#![allow(clippy::large_futures)]
use super::worker::GroupDriver;

use anyhow::{Result, bail};
use sha2::{Digest, Sha256};

use crate::{
    config::{Config, Profile},
    context::{self, CanonicalContext, ContextPressure, RenderedContext},
    group::provider::pr_system_prompt,
    objects::{LocalObjects, RepositoryName, WorkItemLocator},
    queue::scheduler::record_context_pressure,
    store::{AssignmentCandidate, StoreActor},
    worktree::{self, WorktreeRequest},
};

pub(crate) struct PreparedPrContext {
    rendered: RenderedContext,
    repository_node_id: String,
    head_ref: String,
}

pub(crate) async fn prepare_pr_context(
    store: &StoreActor,
    github: &LocalObjects,
    config: &Config,
    profile: &Profile,
    candidate: &AssignmentCandidate,
) -> Result<PreparedPrContext> {
    let repository = candidate.repository.parse::<RepositoryName>()?;
    let locator = WorkItemLocator { repository, number: candidate.number };
    let canonical = CanonicalContext::PullRequest(
        context::materialize_pull_request(github, &locator, 100).await?,
    );
    let rendered = context::render_budgeted(
        &canonical,
        profile.context_soft_ratio,
        profile.context_hard_bytes,
        profile.context_window_tokens,
    );
    context::record_context_revision(&canonical, &rendered, store)?;
    let CanonicalContext::PullRequest(pull_request) = canonical else {
        unreachable!("PR materializer returned Issue Context");
    };
    if pull_request.head_repository.as_deref() != Some(config.repository.as_str()) {
        bail!("PR #{} head repository is not the configured repository", candidate.number);
    }
    Ok(PreparedPrContext {
        rendered,
        repository_node_id: pull_request.repository_node_id,
        head_ref: pull_request.head_ref,
    })
}

pub(crate) fn provision_pr_agent_worktree(
    store: &StoreActor,
    config: &Config,
    profile: &Profile,
    candidate: &AssignmentCandidate,
    materialization: &crate::store::AgentMaterialization,
    prepared: &PreparedPrContext,
) -> Result<Profile> {
    if let Some(path) = &materialization.worktree_path {
        anyhow::ensure!(path.is_dir(), "preserved PR worktree is missing");
        worktree::resume(
            path,
            profile.workspace(),
            &materialization.member_login,
            &config.tools.git,
        )?;
        let mut effective = profile.clone();
        effective.workspace = Some(path.clone());
        return Ok(effective);
    }
    let target = config
        .runtime
        .worktrees()
        .join(format!("pr-{}", candidate.number))
        .join(format!("{}-g{}", profile.id, materialization.generation));
    let local_branch = prepared.head_ref.trim_start_matches("refs/heads/").to_owned();
    let provisioned = worktree::provision(&WorktreeRequest {
        source: profile.workspace(),
        target: &target,
        git: &config.tools.git,
        head_ref: &prepared.head_ref,
        local_branch: &local_branch,
        member_login: &materialization.member_login,
    })?;
    store.record_agent_worktree(
        materialization.clone(),
        prepared.repository_node_id.clone(),
        provisioned.path.clone(),
        provisioned.source,
        provisioned.head_ref,
        provisioned.local_branch,
    )?;
    let mut effective_profile = profile.clone();
    effective_profile.workspace = Some(provisioned.path);
    Ok(effective_profile)
}

impl GroupDriver<'_> {
    pub(super) async fn materialize_next_pr_assignment(&self) {
        let store = self.store;
        let candidates = match store.assignment_candidates("pr".into(), self.spec.profile.id.clone()) {
            Ok(candidates) => candidates,
            Err(error) => {
                tracing::error!(%error, "cannot inspect PR activation events");
                return;
            }
        };
        for candidate in candidates {
            if candidate.action == "unassign" {
                if let Err(error) = self.settle_pr_unassignment(candidate).await {
                    tracing::error!(%error, "cannot settle PR unassignment");
                }
                continue;
            }
            if candidate.unassigned {
                if let Err(error) = store.ignore_assignment_event(candidate.event_id) {
                    tracing::error!(%error, "cannot consume unassigned PR activation");
                }
                continue;
            }
            if let Err(error) = Box::pin(self.materialize_pr_assignment(candidate)).await {
                tracing::error!(%error, "cannot materialize PR Implementation Agent assignment");
            }
        }
    }

    async fn settle_pr_unassignment(&self, candidate: AssignmentCandidate) -> Result<()> {
        if candidate.target_profile_id.as_deref().is_some_and(|owner| owner != self.spec.profile.id) {
            return Ok(());
        }
        let event_id = candidate.event_id;
        let outcome = self.store.retire_unassigned_work_item(
            event_id.clone(),
            self.config.scheduler.quiet_seconds,
        )?;
        if !outcome.settled {
            return Ok(());
        }
        let owned: std::collections::HashSet<_> = self.store
            .stopping_provider_sessions(
                self.spec.profile.id.clone(),
                candidate.work_item_kind,
            )?
            .into_iter()
            .collect();
        if !outcome.provider_sessions.iter().all(|id| owned.contains(id)) {
            return Ok(());
        }
        let first_session = outcome.provider_sessions.first().cloned();
        for id in outcome.provider_sessions {
            if self.sessions.is_managed(&id).await {
                self.sessions.remove(&id).await?;
            }
        }
        if let Some(id) = first_session {
            self.store.retire_stopping_provider_session(id)?;
        }
        self.store.finish_unassigned_work_item(event_id)?;
        Ok(())
    }

    pub(super) async fn materialize_pr_assignment(
        &self,
        candidate: AssignmentCandidate,
    ) -> Result<()> {
        let store = self.store;
        let github = self.github;
        let config = self.config;
        let sessions = &self.sessions;
        let profile = &self.spec.profile;
        let profile_record = &self.spec.profile_record;
        if candidate.work_item_kind != "pr"
            || !matches!(candidate.action.as_str(), "assign" | "mention" | "activate")
        {
            store.ignore_assignment_event(candidate.event_id)?;
            return Ok(());
        }
        let prepared = prepare_pr_context(store, github, config, profile, &candidate).await?;
        let Some(materialization) = store.begin_agent_assignment(
            candidate.event_id.clone(),
            profile_record.clone(),
            Some(prepared.rendered.revision.clone()),
            true,
        )?
        else {
            return Ok(());
        };
        record_context_pressure(store, &materialization.assignment_id, &prepared.rendered, None)?;
        if prepared.rendered.pressure == ContextPressure::Hard {
            let message = format!(
                "local Context is {} bytes, above the configured hard limit of {} bytes",
                prepared.rendered.bytes, profile.context_hard_bytes
            );
            store.fail_agent_assignment(materialization.assignment_id.clone(), message)?;

            return Ok(());
        }
        let effective_profile = match provision_pr_agent_worktree(
            store,
            config,
            profile,
            &candidate,
            &materialization,
            &prepared,
        ) {
            Ok(profile) => profile,
            Err(error) => {
                store.fail_agent_assignment(
                    materialization.assignment_id.clone(),
                    error.to_string(),
                )?;
                return Err(error);
            }
        };
        let instructions = pr_system_prompt(config, profile, candidate.number, &prepared.head_ref, Some(&materialization.member_login));
        let instruction_revision = hex::encode(Sha256::digest(instructions.as_bytes()));
        let memory = prepared.rendered.text.clone();
        let result = sessions.start(effective_profile.clone(), instructions.clone(), memory).await;
        match result {
            Ok((thread_id, binding_id)) => {
                if let Err(error) = store.complete_agent_assignment(
                    materialization.clone(),
                    thread_id.clone(),
                    binding_id,
                    prepared.rendered.revision.clone(),
                    instruction_revision,
                ) {
                    sessions.remove(&thread_id).await?;
                    return Err(error.into());
                }
                if prepared.rendered.pressure == ContextPressure::Soft {
                }
                tracing::info!(
                    pr = candidate.number,
                    worktree = %effective_profile.workspace().display(),
                    model = ?profile.model,
                    "PR Implementation Agent session has current Context"
                );
                Ok(())
            }
            Err(error) => {
                store.fail_agent_assignment(materialization.assignment_id, error.to_string())?;
                Err(error.into())
            }
        }
    }
}
