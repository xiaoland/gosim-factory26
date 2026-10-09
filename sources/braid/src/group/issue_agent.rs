#![allow(clippy::large_futures)]
use super::worker::GroupDriver;

use anyhow::Result;
use sha2::{Digest, Sha256};

use crate::{
    config::{Config, Profile},
    context::{self, CanonicalContext, ContextPressure},
    group::dispatch::record_context_unavailable,
    group::provider::issue_system_prompt,
    objects::{LocalObjects, RepositoryName, WorkItemLocator},
    queue::scheduler::record_context_pressure,
    store::{AssignmentCandidate, StoreActor},
    worktree::{self, WorktreeRequest},
};

/// Provision a clone from the work item's published start branch. The
/// effective Profile carries this independent local repository as its cwd.
pub(crate) fn provision_issue_agent_worktree(
    store: &StoreActor,
    config: &Config,
    profile: &Profile,
    issue_number: u64,
    materialization: &crate::store::AgentMaterialization,
    head_ref: &str,
    repository_node_id: String,
) -> Result<Profile> {
    if let Some(path) = &materialization.worktree_path {
        anyhow::ensure!(path.is_dir(), "preserved Issue worktree is missing");
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
        .join(format!("issue-{issue_number}"))
        .join(format!("{}-g{}", profile.id, materialization.generation));
    let local_branch = if issue_number == 1 {
        head_ref.trim_start_matches("refs/heads/").to_owned()
    } else {
        format!("braid-agent/issue-{issue_number}/{}-g{}", profile.id, materialization.generation)
    };
    let provisioned = worktree::provision(&WorktreeRequest {
        source: profile.workspace(),
        target: &target,
        git: &config.tools.git,
        head_ref,
        local_branch: &local_branch,
        member_login: &materialization.member_login,
    })?;
    store.record_agent_worktree(
        materialization.clone(),
        repository_node_id,
        provisioned.path.clone(),
        provisioned.source,
        provisioned.head_ref,
        provisioned.local_branch,
    )?;
    let mut effective_profile = profile.clone();
    effective_profile.workspace = Some(provisioned.path);
    Ok(effective_profile)
}

/// The Issue Agent worktree binds the issue's sole same-repository
/// Development linked branch; with zero or several Development branches it
/// starts on the repository default branch and the Agent may switch or create
/// branches in its worktree itself.
pub(super) async fn resolve_issue_worktree_ref(
    canonical: &CanonicalContext,
    repository: &str,
    github: &LocalObjects,
) -> Result<String> {
    let prefix = format!("{repository}:");
    let same_repository: Vec<&str> = match canonical {
        CanonicalContext::Issue(issue) => issue
            .linked_branches
            .iter()
            .filter_map(|branch| branch.strip_prefix(prefix.as_str()))
            .collect(),
        CanonicalContext::PullRequest(_) | CanonicalContext::ReviewRequest(_) => Vec::new(),
    };
    if same_repository.len() == 1 {
        return Ok(same_repository[0].to_owned());
    }
    Ok(github.delivery_ref()?.trim_start_matches("refs/heads/").to_owned())
}

impl GroupDriver<'_> {
    /// Settle a native Issue unassignment after its debounce window and
    /// confirm teardown of any provider session owned by this driver.
    pub(super) async fn settle_unassignment(&self, candidate: AssignmentCandidate) -> Result<()> {
        let store = self.store;
        let config = self.config;
        let sessions = &self.sessions;
        if candidate.target_profile_id.as_deref().is_some_and(|owner| owner != self.spec.profile.id)
        {
            return Ok(());
        }
        let event_id = candidate.event_id.clone();
        let outcome =
            store.retire_unassigned_work_item(event_id.clone(), config.scheduler.quiet_seconds)?;
        if !outcome.settled {
            return Ok(());
        }
        let owned: std::collections::HashSet<_> = store
            .stopping_provider_sessions(
                self.spec.profile.id.clone(),
                candidate.work_item_kind.clone(),
            )
            .map_err(anyhow::Error::from)?
            .into_iter()
            .collect();
        if !outcome.provider_sessions.iter().all(|id| owned.contains(id)) {
            return Ok(());
        }
        let first_session = outcome.provider_sessions.first().cloned();
        for provider_session_id in outcome.provider_sessions {
            if owned.contains(&provider_session_id)
                && sessions.is_managed(&provider_session_id).await
            {
                sessions.remove(&provider_session_id).await?;
            }
        }
        if let Some(provider_session_id) = first_session {
            store.retire_stopping_provider_session(provider_session_id)?;
        }
        store.finish_unassigned_work_item(event_id)?;
        tracing::info!(
            kind = candidate.work_item_kind,
            number = candidate.number,
            "retired unassigned Agent Group"
        );
        Ok(())
    }

    pub(super) async fn materialize_next_issue_assignment(&self) {
        let store = self.store;
        let candidates =
            match store.assignment_candidates("issue".into(), self.spec.profile.id.clone()) {
                Ok(candidates) => candidates,
                Err(error) => {
                    tracing::error!(%error, "cannot inspect assignment events");
                    return;
                }
            };
        for candidate in candidates {
            if candidate.action == "unassign" {
                if let Err(error) = self.settle_unassignment(candidate).await {
                    tracing::error!(%error, "cannot settle Issue unassignment");
                }
                continue;
            }
            if candidate.unassigned {
                if let Err(error) = store.ignore_assignment_event(candidate.event_id) {
                    tracing::error!(%error, "cannot consume unassigned Issue activation");
                }
                continue;
            }
            if candidate.work_item_kind != "issue"
                || !matches!(candidate.action.as_str(), "assign" | "mention" | "activate")
            {
                if let Err(error) = store.ignore_assignment_event(candidate.event_id) {
                    tracing::error!(%error, "cannot consume invalid activation");
                }
                continue;
            }
            if let Err(error) = self.materialize_issue_assignment(candidate).await {
                tracing::error!(%error, "cannot materialize Issue Agent assignment");
            }
            // Dispatch before starting another native process from this batch.
            return;
        }
    }

    #[allow(clippy::too_many_lines)]
    pub(super) async fn materialize_issue_assignment(
        &self,
        candidate: AssignmentCandidate,
    ) -> Result<()> {
        let store = self.store;
        let github = self.github;
        let config = self.config;
        let sessions = &self.sessions;
        let profile = &self.spec.profile;
        let profile_record = &self.spec.profile_record;
        let mention_activation = matches!(candidate.action.as_str(), "mention" | "activate");
        if candidate.action != "assign" && !mention_activation {
            store.ignore_assignment_event(candidate.event_id)?;
            return Ok(());
        }
        let Some(canonical) = self.materialize_assignment_context(&candidate).await? else {
            return Ok(());
        };
        if !mention_activation
            && candidate.target_profile_id.as_deref() != Some(self.spec.profile.id.as_str())
        {
            return Ok(());
        }
        let rendered = context::render_budgeted(
            &canonical,
            profile.context_soft_ratio,
            profile.context_hard_bytes,
            profile.context_window_tokens,
        );
        context::record_context_revision(&canonical, &rendered, store)?;
        let preserve_wake = rendered.pressure != ContextPressure::Hard;
        let slot = self.sessions.reserve().await?;
        let Some(materialization) = store.begin_agent_assignment(
            candidate.event_id.clone(),
            profile_record.clone(),
            Some(rendered.revision.clone()),
            preserve_wake,
        )?
        else {
            return Ok(());
        };
        record_context_pressure(store, &materialization.assignment_id, &rendered, None)?;
        if rendered.pressure == ContextPressure::Hard {
            let message = format!(
                "local Context is {} bytes, above the configured hard limit of {} bytes",
                rendered.bytes, profile.context_hard_bytes
            );
            store.fail_agent_assignment(materialization.assignment_id.clone(), message)?;

            return Ok(());
        }
        if !profile.workspace().is_dir() {
            let message =
                format!("assigned workspace does not exist: {}", profile.workspace().display());
            store.fail_agent_assignment(materialization.assignment_id, message.clone())?;
            anyhow::bail!(message);
        }
        let head_ref =
            match resolve_issue_worktree_ref(&canonical, &config.repository, github).await {
                Ok(head_ref) => head_ref,
                Err(error) => {
                    let message = format!("cannot resolve the Issue worktree ref: {error:#}");
                    store.fail_agent_assignment(
                        materialization.assignment_id.clone(),
                        message.clone(),
                    )?;
                    anyhow::bail!(message);
                }
            };
        let CanonicalContext::Issue(issue) = &canonical else {
            anyhow::bail!("Issue assignment materialized non-Issue canonical Context");
        };
        let effective_profile = match provision_issue_agent_worktree(
            store,
            config,
            profile,
            candidate.number,
            &materialization,
            &head_ref,
            issue.repository_node_id.clone(),
        ) {
            Ok(effective_profile) => effective_profile,
            Err(error) => {
                let message = format!("cannot provision the Issue Agent worktree: {error:#}");
                store.fail_agent_assignment(
                    materialization.assignment_id.clone(),
                    message.clone(),
                )?;
                anyhow::bail!(message);
            }
        };
        let instructions = issue_system_prompt(
            config,
            profile,
            candidate.number,
            Some(&materialization.member_login),
        );
        let instruction_revision = hex::encode(Sha256::digest(instructions.as_bytes()));
        let context = rendered.text.clone();
        let result =
            sessions.start(effective_profile.clone(), instructions.clone(), context, slot).await;
        match result {
            Ok((thread_id, binding_id)) => {
                if let Err(error) = store.complete_agent_assignment(
                    materialization.clone(),
                    thread_id.clone(),
                    binding_id,
                    rendered.revision.clone(),
                    instruction_revision,
                ) {
                    sessions.remove(&thread_id).await?;
                    return Err(error.into());
                }
                tracing::info!(
                    issue = candidate.number,
                    model = ?profile.model,
                    "Issue Agent session is idle"
                );
                Ok(())
            }
            Err(error) => {
                if error.is_deferred() {
                    store.defer_agent_assignment(
                        materialization.assignment_id,
                        candidate.event_id,
                        error.to_string(),
                    )?;
                    return Err(error.into());
                }
                store.fail_agent_assignment(materialization.assignment_id, error.to_string())?;
                Err(error.into())
            }
        }
    }

    pub(super) async fn materialize_assignment_context(
        &self,
        candidate: &AssignmentCandidate,
    ) -> Result<Option<CanonicalContext>> {
        let store = self.store;
        let github = self.github;
        let profile_record = &self.spec.profile_record;
        let repository = candidate.repository.parse::<RepositoryName>()?;
        let locator = WorkItemLocator { repository, number: candidate.number };
        match context::materialize_issue(github, &locator, 100).await {
            Ok(issue) => Ok(Some(CanonicalContext::Issue(issue))),
            Err(context_error) => {
                let Some(materialization) = store.begin_agent_assignment(
                    candidate.event_id.clone(),
                    profile_record.clone(),
                    None,
                    false,
                )?
                else {
                    return Ok(None);
                };
                let error = anyhow::Error::from(context_error);
                record_context_unavailable(store, &materialization.assignment_id, &error)?;
                store.fail_agent_assignment(materialization.assignment_id, error.to_string())?;
                Err(error)
            }
        }
    }
}
