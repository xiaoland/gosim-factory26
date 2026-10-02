//! Dispatch and materialization: the group layer's execution half.
//!
//! The queue (scheduler + store) decides *what* should happen next; these
//! functions are the group-side orchestration that claims the decision and
//! executes it against physical sessions. They are called only from the group
//! workers' drive loops.
#![allow(clippy::all, clippy::pedantic)]
use super::worker::{GroupDriver, RunningAgentTurn};

use anyhow::{Context as _, Result, bail};
use sha2::{Digest, Sha256};

use crate::{
    agent_session::SendResult,
    context::{self, CanonicalContext, ContextError, ContextPressure},
    group::issue_agent::{provision_issue_agent_worktree, resolve_issue_worktree_ref},
    group::provider::{issue_system_prompt, pr_system_prompt, review_system_prompt, render_context_reset_notice, render_context_reset_source, render_event_references},
    objects::{RepositoryName, WorkItemLocator},
    queue::scheduler::record_context_pressure,
    store::{ContextResetClaim, StoreActor, TurnClaim, WorkItemLifecycleCandidate},
};

fn fail_claimed_turn(store: &StoreActor, claim: &TurnClaim, lifecycle: &str, reason: String) {
    if let Err(error) = store.mark_turn_terminal(claim.turn_id.clone(), lifecycle.into(), Some(reason)) {
        tracing::error!(%error, turn = %claim.turn_id, "cannot close failed turn claim");
    }
    if let Some(reset_id) = &claim.reset_id {
        if let Err(error) = store.fail_context_reset(
            reset_id.clone(), format!("reset notice turn ended {lifecycle} before delivery"),
        ) {
            tracing::error!(%error, "cannot block failed reset notice");
        }
    }
}

pub(crate) fn is_context_too_large(error: &anyhow::Error) -> bool {
    matches!(error.downcast_ref::<ContextError>(), Some(ContextError::TooLarge { .. }))
}

pub(crate) fn record_context_unavailable(
    store: &StoreActor,
    assignment_id: &str,
    error: &anyhow::Error,
) -> Result<()> {
    store.set_assignment_context_pressure(
        assignment_id.into(),
        "unavailable".into(),
        None,
        Some(error.to_string()),
    )?;
    Ok(())
}

impl GroupDriver<'_> {
    pub(super) async fn handle_next_work_item_lifecycle(&self) -> (bool, Option<RunningAgentTurn>, Option<anyhow::Error>) {
        let store = self.store;
        let work_item_kind = self.spec.kind.as_str();
        let candidate = match store.work_item_lifecycle_candidates(work_item_kind.into(), 1) {
            Ok(candidates) => candidates.into_iter().next(),
            Err(error) => {
                tracing::error!(%error, work_item_kind, "cannot inspect Work Item lifecycle events");
                return (false, None, None);
            }
        };
        let Some(candidate) = candidate else {
            return (false, None, None);
        };
        match candidate.action.as_str() {
            "closed" => match store.prepare_work_item_closure(candidate.event_id) {
                Ok(true) => {
                    tracing::info!(
                        work_item_kind,
                        number = candidate.number,
                        "external close queued for its assignee"
                    );
                    (true, self.start_next_agent_turn().await, None)
                }
                Ok(false) => (true, None, None),
                Err(error) => {
                    tracing::error!(%error, work_item_kind, number = candidate.number, "cannot process Work Item closure");
                    (true, None, None)
                }
            },
            "reopened" | "direct_contact" => {
                let mut retryable_error = None;
                if let Err(error) = Box::pin(self.reactivate_work_item_agent(candidate)).await {
                    tracing::error!(%error, work_item_kind, "cannot reactivate reopened Agent Group");
                    if matches!(error.downcast_ref::<crate::agent_session::SessionError>(),
                        Some(crate::agent_session::SessionError::Deferred(_)
                            | crate::agent_session::SessionError::ResourceDeferred(_)
                            | crate::agent_session::SessionError::Unavailable)) {
                        retryable_error = Some(error);
                    }
                }
                (true, None, retryable_error)
            }
            _ => {
                if let Err(error) = store.ignore_assignment_event(candidate.event_id) {
                    tracing::error!(%error, "cannot consume unsupported Work Item lifecycle event");
                }
                (true, None, None)
            }
        }
    }

    pub(super) async fn reactivate_work_item_agent(
        &self,
        candidate: WorkItemLifecycleCandidate,
    ) -> Result<()> {
        let store = self.store;
        let github = self.github;
        let config = self.config;
        let sessions = &self.sessions;
        let profile = &self.spec.profile;
        let policy = crate::queue::scheduler::policy_from_config(self.config);
        let Some(materialization) =
            store.begin_work_item_reactivation(candidate.event_id.clone(), profile.id.clone())?
        else {
            return Ok(());
        };
        if materialization.profile_id != profile.id {
            let message = format!(
                "reopened {} Profile {} does not match active Profile {}",
                candidate.work_item_kind, materialization.profile_id, profile.id
            );
            store.fail_work_item_reactivation(
                candidate.event_id,
                materialization.assignment_id,
                message.clone(),
            )?;
            bail!(message);
        }
        let mut retryable_resume = false;
        let result = Box::pin(async {
            let repository = candidate.repository.parse::<RepositoryName>()?;
            let locator = WorkItemLocator { repository, number: candidate.number };
            let (canonical, instructions, effective_profile) = if candidate.work_item_kind == "pr" {
                let pull_request = context::materialize_pull_request(github, &locator, 100).await?;
                if pull_request.head_repository.as_deref() != Some(config.repository.as_str()) {
                    bail!(
                        "reopened PR #{} head repository is not the configured repository",
                        candidate.number
                    );
                }
                let head_ref = materialization
                    .worktree_head_ref
                    .clone()
                    .unwrap_or_else(|| pull_request.head_ref.clone());
                let mut effective_profile = profile.clone();
                effective_profile.workspace = Some(
                    materialization
                        .worktree_path
                        .clone()
                        .context("reopened PR Agent has no preserved worktree")?,
                );
                (
                    CanonicalContext::PullRequest(pull_request),
                    pr_system_prompt(config, profile, candidate.number, &head_ref, Some(&materialization.member_login)),
                    effective_profile,
                )
            } else if candidate.work_item_kind=="review" {
                let path=materialization.worktree_path.clone().context("review reactivation has no frozen checkout")?;
                github.verify_reviewer_checkout(candidate.number as i64,&path,&materialization.member_login,&config.tools.git)?;
                let mut effective_profile=profile.clone();
                effective_profile.workspace=Some(path);
                (github.canonical("review",candidate.number as i64)?,review_system_prompt(config,profile,candidate.number,Some(&materialization.member_login)),effective_profile)
            } else if candidate.work_item_kind=="issue" {
                let issue = context::materialize_issue(github, &locator, 100).await?;
                let repository_node_id = issue.repository_node_id.clone();
                let canonical = CanonicalContext::Issue(issue);
                let effective_profile = if let Some(preserved) =
                    materialization.worktree_path.clone()
                {
                    let mut effective_profile = profile.clone();
                    effective_profile.workspace = Some(preserved);
                    effective_profile
                } else {
                    // Pre-worktree generations (v0.3.0 data) preserved no
                    // worktree; provision a fresh one on the current head ref
                    // instead of parking the group blocked.
                    let head_ref =
                        resolve_issue_worktree_ref(&canonical, &config.repository, github).await?;
                    provision_issue_agent_worktree(
                        store,
                        config,
                        profile,
                        candidate.number,
                        &materialization,
                        &head_ref,
                        repository_node_id,
                    )?
                };
                (
                    canonical,
                    issue_system_prompt(config, profile, candidate.number, Some(&materialization.member_login)),
                    effective_profile,
                )
            } else {bail!("unsupported reactivation kind {}",candidate.work_item_kind)};
            let instruction_revision = hex::encode(Sha256::digest(instructions.as_bytes()));
            let sleeping = materialization.sleeping_session.as_ref();
            if let Some(session) = sleeping {
                if session.provider_kind != profile.adapter_type {
                    bail!("sleeping native adapter {} cannot resume with {}",session.provider_kind,profile.adapter_type);
                }
                let worktree = materialization.worktree_path.as_ref().context("sleeping Agent has no preserved worktree")?;
                crate::worktree::resume(worktree, profile.workspace(), &materialization.member_login, &config.tools.git)
                    .with_context(|| format!("cannot verify sleeping member worktree {}",worktree.display()))?;
                // Also required for a description replacement: never let a new
                // writer start before the previous native writer has stopped.
                sessions.remove(&session.id).await?;
                if materialization.description_event_ids.is_empty() {
                    let result = sessions.resume(session.id.clone(), effective_profile.clone(), instructions.clone()).await;
                    if let Err(error) = &result { store.record_provider_resume_error(session.id.clone(), error.to_string())?; }
                    match result {
                        Ok(Some(binding_id)) => return Ok((session.id.clone(), binding_id, session.context_revision.clone(), instruction_revision)),
                        Ok(None) => bail!("sleeping provider session stayed live during resume"),
                        Err(crate::agent_session::SessionError::HistoryUnavailable(reason)) => {
                            tracing::warn!(provider_session = %session.id, %reason, "native history missing; starting with current Context");
                        }
                        Err(error @ (crate::agent_session::SessionError::Deferred(_) | crate::agent_session::SessionError::ResourceDeferred(_) | crate::agent_session::SessionError::Unavailable)) => {
                            retryable_resume = true;
                            return Err(error.into());
                        }
                        Err(error) => return Err(error.into()),
                    }
                }
            }
            let rendered = context::render_budgeted(
                &canonical, profile.context_soft_ratio, profile.context_hard_bytes, profile.context_window_tokens,
            );
            record_context_pressure(store, &materialization.assignment_id, &rendered, None)?;
            if rendered.pressure == ContextPressure::Hard {
                return Err(ContextError::TooLarge { bytes: rendered.bytes, hard_bytes: profile.context_hard_bytes }.into());
            }
            let (thread_id, binding_id) = sessions.start(effective_profile, instructions, rendered.text).await?;
            Ok::<_, anyhow::Error>((thread_id, binding_id, rendered.revision, instruction_revision))
        })
        .await;
        match result {
            Ok((thread_id, binding_id, context_revision, instruction_revision)) => {
                if let Err(error) = store.complete_work_item_reactivation(
                    candidate.event_id,
                    materialization.clone(),
                    thread_id.clone(),
                    binding_id,
                    context_revision,
                    instruction_revision,
                    policy,
                ) {
                    sessions.remove(&thread_id).await?;
                    return Err(error.into());
                }
                tracing::info!(
                    work_item_kind = candidate.work_item_kind,
                    number = candidate.number,
                    "reopened Agent has current Context and a debounced Wake"
                );
                Ok(())
            }
            Err(error) => {
                if retryable_resume || error.downcast_ref::<crate::agent_session::SessionError>().is_some_and(crate::agent_session::SessionError::is_deferred) {
                    store.defer_work_item_reactivation(
                        candidate.event_id,
                        materialization.assignment_id,
                        error.to_string(),
                    )?;
                    return Err(error);
                }
                if !is_context_too_large(&error) {
                    record_context_unavailable(
                        store,
                        &materialization.assignment_id,
                        &error,
                    )?;
                }
                store.fail_work_item_reactivation(
                    candidate.event_id,
                    materialization.assignment_id,
                    error.to_string(),
                )?;
                Err(error)
            }
        }
    }

    pub(super) async fn materialize_next_context_reset(&self) -> Result<bool> {
        let store = self.store;
        let profile = &self.spec.profile;
        let work_item_kind = self.spec.kind.as_str();
        let reset = match store.ready_context_reset(work_item_kind.into(), profile.id.clone()) {
            Ok(Some(reset)) => Some(reset),
            Ok(None) => {
                match store.begin_context_reset(None, work_item_kind.into(), profile.id.clone()) {
                    Ok(Some(_)) => return Ok(true),
                    Ok(None) => None,
                    Err(error) => {
                        tracing::error!(%error, "cannot begin idle Context reset");
                        return Ok(false);
                    }
                }
            }
            Err(error) => {
                tracing::error!(%error, "cannot inspect ready Context resets");
                return Ok(false);
            }
        };
        let Some(reset) = reset else { return Ok(false) };
        self.sessions.remove(&reset.old_provider_session_id).await?;
        let reset_id = reset.reset_id.clone();
        let assignment_id = reset.assignment_id.clone();
        if let Err(error) = Box::pin(self.materialize_context_reset(reset)).await {
            if error.downcast_ref::<crate::agent_session::SessionError>().is_some_and(crate::agent_session::SessionError::is_deferred) {
                tracing::info!(%error, reset = %reset_id, "Context materialization deferred; reset retained");
                return Ok(false);
            }
            if !is_context_too_large(&error)
                && let Err(status_error) =
                    record_context_unavailable(store, &assignment_id, &error)
            {
                tracing::error!(%status_error, reset = %reset_id, "cannot record unavailable Context status");
            }
            if let Err(store_error) = store.fail_context_reset(reset_id.clone(), error.to_string())
            {
                tracing::error!(%store_error, reset = %reset_id, "cannot block failed Context reset");
            }
            tracing::error!(%error, reset = %reset_id, work_item_kind, "cannot replace Agent Context");
        }
        Ok(true)
    }

    pub(super) async fn materialize_context_reset(&self, reset: ContextResetClaim) -> Result<()> {
        let store = self.store;
        let github = self.github;
        let config = self.config;
        let sessions = &self.sessions;
        let profile = &self.spec.profile;
        if reset.profile_id != profile.id {
            bail!(
                "Context reset Profile {} does not match active Profile {}",
                reset.profile_id,
                profile.id
            );
        }
        let repository = reset.repository.parse::<RepositoryName>()?;
        let locator = WorkItemLocator { repository, number: reset.number };
        let canonical = if reset.work_item_kind == "pr" {
            CanonicalContext::PullRequest(
                context::materialize_pull_request(github, &locator, 100).await?,
            )
        } else if reset.work_item_kind == "issue" {
            CanonicalContext::Issue(context::materialize_issue(github, &locator, 100).await?)
        } else if reset.work_item_kind=="review" {
            github.canonical("review",reset.number as i64)?
        } else {
            bail!("unsupported Context reset Work Item kind {}", reset.work_item_kind);
        };
        let rendered = context::render_budgeted(
            &canonical,
            profile.context_soft_ratio,
            profile.context_hard_bytes,
            profile.context_window_tokens,
        );
        record_context_pressure(store, &reset.assignment_id, &rendered, None)?;
        let context = format!("{}{}", render_context_reset_source(&reset), rendered.text);
        if rendered.pressure == ContextPressure::Hard || context.len() > profile.context_hard_bytes {
            return Err(ContextError::TooLarge {
                bytes: context.len(),
                hard_bytes: profile.context_hard_bytes,
            }
            .into());
        }
        let mut effective_profile = profile.clone();
        let instructions = if reset.work_item_kind == "pr" {
            let worktree =
                reset.worktree_path.as_ref().context("PR Context reset has no active worktree")?;
            let head_ref = reset
                .worktree_head_ref
                .as_deref()
                .context("PR Context reset has no local branch reference")?;
            effective_profile.workspace = Some(worktree.clone());
            pr_system_prompt(config, profile, reset.number, head_ref, reset.member_login.as_deref())
        } else if reset.work_item_kind=="review" {
            let worktree=reset.worktree_path.as_ref().context("review reset has no frozen checkout")?;
            github.verify_reviewer_checkout(reset.number as i64,worktree,reset.member_login.as_deref().context("review reset has no member")?,&config.tools.git)?;
            effective_profile.workspace=Some(worktree.clone());
            review_system_prompt(config,profile,reset.number,reset.member_login.as_deref())
        } else {
            let worktree = reset
                .worktree_path
                .as_ref()
                .context("Issue Context reset has no active worktree")?;
            effective_profile.workspace = Some(worktree.clone());
            issue_system_prompt(config, profile, reset.number, reset.member_login.as_deref())
        };
        let instruction_revision = hex::encode(Sha256::digest(instructions.as_bytes()));
        let (thread_id, binding_id) =
            sessions.start(effective_profile.clone(), instructions.clone(), context).await?;
        if let Err(error) = store.complete_context_reset(
            reset.reset_id.clone(),
            thread_id.clone(),
            binding_id,
            rendered.revision.clone(),
            instruction_revision,
        ) {
            sessions.remove(&thread_id).await?;
            return Err(error.into());
        }
        tracing::info!(
            reset = %reset.reset_id,
            work_item_kind = %reset.work_item_kind,
            work_item = reset.number,
            provider_session = %thread_id,
            "Agent Context was replaced"
        );
        Ok(())
    }

    pub(super) async fn forward_running_input(&self, active: &RunningAgentTurn) {
        let store = self.store;
        let sessions = &self.sessions;
        let steer = match store.claim_running_input(active.claim.turn_id.clone()) {
            Ok(steer) => steer,
            Err(error) => {
                tracing::error!(%error, "cannot inspect running input batch");
                return;
            }
        };
        let Some(steer) = steer else { return };
        let reference = render_event_references(&steer);
        let Some(session) = sessions.get(&active.claim.provider_session_id).await else {
            tracing::warn!(
                provider_session = %active.claim.provider_session_id,
                "no AgentSession for steer; batch remains runnable"
            );
            return;
        };
        match session.send_user_msg(reference, true).await {
            Ok(SendResult::Acknowledged) => {}
            Ok(SendResult::Started) => {
                tracing::error!("running input unexpectedly started a new turn; batch remains runnable");
                return;
            }
            Err(error) if error.is_deferred() => return,
            Err(error) => {
                tracing::warn!(%error, "active turn did not accept input; batch remains runnable");
                return;
            }
        }
        if let Err(error) = store.consume_steer_batch(active.claim.turn_id.clone(), steer.batch_id, steer.steer_event_ids) {
            tracing::error!(%error, "cannot acknowledge running input batch");
        }
    }

    pub(super) async fn start_next_agent_turn(&self) -> Option<RunningAgentTurn> {
        let store = self.store;
        let sessions = &self.sessions;
        let profile = &self.spec.profile;
        let work_item_kind = self.spec.kind.as_str();
        // Unrelated idle members must not create a resource wait that prevents
        // the run from finishing. Only inspect sessions with durable input.
        let candidates = match store.provider_resume_candidates(profile.id.clone(), work_item_kind.into()) {
            Ok(candidates) => candidates.into_iter().filter(|candidate| candidate.needs_resume)
                .map(|candidate| candidate.provider_session_id).collect(),
            Err(error) => {
                tracing::error!(%error, "cannot inspect runnable input candidates");
                return None;
            }
        };
        let ready = sessions.input_ready_ids(&candidates).await;
        let reset_notice = match store.claim_context_reset_notice(work_item_kind.into(), profile.id.clone(), ready.clone()) {
            Ok(claim) => claim,
            Err(error) => {
                tracing::error!(%error, "cannot claim Context reset notice");
                return None;
            }
        };
        let next = if let Some(claim) = reset_notice {
            Ok(Some(claim))
        } else {
            store.claim_runnable_turn(
                work_item_kind.into(), profile.id.clone(), ready,
            )
        };
        let claim = match next {
            Ok(claim) => claim,
            Err(error) => {
                tracing::error!(%error, work_item_kind, "cannot claim runnable Agent turn");
                return None;
            }
        }?;
        let mut telemetry = crate::telemetry::Operation::new(
            "braid.turn",
            vec![
                opentelemetry::KeyValue::new("braid.turn.id", claim.turn_id.clone()),
                opentelemetry::KeyValue::new(
                    "braid.provider_session.id",
                    claim.provider_session_id.clone(),
                ),
                opentelemetry::KeyValue::new("braid.work_item.kind", claim.work_item_kind.clone()),
                opentelemetry::KeyValue::new("braid.profile.id", claim.profile_id.clone()),
                opentelemetry::KeyValue::new("braid.work_item.id", claim.number.to_string()),
            ],
        );
        let reference = if let Some(reset_id) = &claim.reset_id {
            match store.refresh_context_reset(reset_id.clone()) {
                Ok(reset) => render_context_reset_notice(&reset),
                Err(error) => {
                    tracing::error!(%error, "cannot refresh Context reset notice");
                    fail_claimed_turn(store, &claim, "failed", error.to_string());
                    return None;
                }
            }
        } else {
            render_event_references(&claim)
        };
        if let Err(error) =
            crate::local::archive_turn_input(self.config.runtime.root(), &claim, &reference)
        {
            tracing::error!(%error,"cannot archive turn input");
            fail_claimed_turn(store, &claim, "failed", error.to_string());
            return None;
        }

        // Every assignment materialization and resume path now populates the
        // SessionManager, so a missing session is a genuine error.
        let Some(session) = sessions.get(&claim.provider_session_id).await else {
            tracing::error!(
                turn = %claim.turn_id,
                provider_session = %claim.provider_session_id,
                "no AgentSession found for claimed turn"
            );
            fail_claimed_turn(store, &claim, "failed", "no AgentSession found for claimed turn".into());
            return None;
        };
        // Subscribe before sending so the `TurnStarted` event — the single
        // authority for provider turn identity — cannot be missed.
        let mut events = session.events();
        match session.send_user_msg(reference.clone(), false).await {
            Ok(SendResult::Started) => { sessions.clear_session_deferred(&claim.provider_session_id).await; }
            Ok(SendResult::Acknowledged) => {
                tracing::error!(turn = %claim.turn_id, "AgentSession did not start a turn");
                fail_claimed_turn(store, &claim, "failed", "AgentSession did not start a turn".into());
                return None;
            }
            Err(error) => {
                if error.is_deferred() {
                    sessions.record_session_deferred(&claim.provider_session_id, error.clone()).await;
                    let deferred = if let Some(reset_id) = &claim.reset_id {
                        store.defer_context_reset_notice(
                            reset_id.clone(), claim.turn_id.clone(), "retry".into(), Some(error.to_string()),
                        )
                    } else {
                        store.defer_unstarted_turn(claim.turn_id.clone(), error.to_string())
                    };
                    if let Err(release) = deferred {
                        tracing::error!(%release, "cannot retain rejected input for retry");
                    }
                    tracing::debug!(%error, "native input was not accepted; retained for retry");
                    return None;
                }
                let lifecycle: String = match error {
                    crate::agent_session::SessionError::Unavailable => "unknown".into(),
                    crate::agent_session::SessionError::Deferred(_)
                    | crate::agent_session::SessionError::ResourceDeferred(_)
                    | crate::agent_session::SessionError::HistoryUnavailable(_)
                    | crate::agent_session::SessionError::Failed(_)
                    | crate::agent_session::SessionError::StopUnproved(_)
                    | crate::agent_session::SessionError::Materialization { .. } => "failed".into(),
                };
                fail_claimed_turn(store, &claim, &lifecycle, error.to_string());
                if lifecycle == "unknown" {
                    let _ = store.enqueue_operational_status(
                        claim.turn_id.clone(),
                        super::provider::operational_status_unknown_profile(&claim.profile_id),
                    );
                    let _ = sessions.remove(&claim.provider_session_id).await;
                }
                if claim.trusted_mention && lifecycle == "failed" {
                    let _ = store.enqueue_turn_reaction(claim.turn_id, "confused".into());
                }
                tracing::error!(%error, "cannot send user message through AgentSession");
                return None;
            }
        }
        // The adapter emits exactly one `TurnStarted` before `Started` returns, so
        // this receive cannot hang on a healthy adapter.
        let provider_turn_id = match events.recv().await {
            Ok(crate::agent_session::SessionEvent::TurnStarted { provider_turn_id }) => {
                provider_turn_id
            }
            other => {
                tracing::error!(?other, turn = %claim.turn_id, "AgentSession stream did not begin with TurnStarted");
                fail_claimed_turn(store, &claim, "failed", format!("AgentSession stream did not begin with TurnStarted: {other:?}"));
                return None;
            }
        };
        if let Err(error) = store.mark_turn_started(claim.turn_id.clone(), provider_turn_id.clone())
        {
            tracing::error!(%error, "cannot record provider turn start");
            if let Some(reset_id) = &claim.reset_id {
                let _ = store.fail_context_reset(reset_id.clone(), error.to_string());
            }
            // The provider turn is running but unrecorded; the contract has no
            // interrupt-only message, so the orphan turn is left to the provider's
            // own lifecycle rather than fencing it here.
            return None;
        }
        if claim.trusted_mention
            && let Err(error) = store.enqueue_turn_reaction(claim.turn_id.clone(), "rocket".into())
        {
            tracing::error!(%error, "cannot enqueue trusted-mention start reaction");
        }
        telemetry.attribute("braid.provider_turn.id", provider_turn_id.clone());
        let reset_id = claim.reset_id.clone();
        let notice_text = reset_id.as_ref().map(|_| reference);
        Some(RunningAgentTurn {
            telemetry, claim, provider_turn_id, reset_id, notice_text,
            last_notice_poll: None, events,
        })
    }

    /// Queue an update in the old Pi session; the terminal path verifies
    /// native delivery before it tears down this session.
    pub(super) async fn begin_active_context_reset(&self, active: &mut RunningAgentTurn) {
        let store = self.store;
        let sessions = &self.sessions;
        if active.reset_id.is_none() {
            let reset = match store.begin_context_reset(
                Some(active.claim.turn_id.clone()),
                active.claim.work_item_kind.clone(),
                active.claim.profile_id.clone(),
            ) {
                Ok(reset) => reset,
                Err(error) => {
                    tracing::error!(%error, "cannot begin active Context reset");
                    return;
                }
            };
            let Some(reset) = reset else { return };
            if reset.active_turn_id.as_deref() != Some(active.claim.turn_id.as_str())
                || reset.provider_turn_id.as_deref() != Some(active.provider_turn_id.as_str())
            {
                let message = "Context reset returned a different active provider turn";
                let _ = store.fail_context_reset(reset.reset_id, message.into());
                tracing::error!(message);
                return;
            }
            active.reset_id = Some(reset.reset_id);
        }
        if active.claim.trigger_kind == "context_reset_notice" { return }
        if active.last_notice_poll.is_some_and(|at| at.elapsed() < tokio::time::Duration::from_secs(3)) {
            return;
        }
        active.last_notice_poll = Some(tokio::time::Instant::now());
        let reset_id = active.reset_id.as_ref().expect("reset assigned");
        let reset = match store.refresh_context_reset(reset_id.clone()) {
            Ok(reset) => reset,
            Err(error) => {
                tracing::error!(%error, "cannot refresh active Context reset");
                return;
            }
        };
        let notice = render_context_reset_notice(&reset);
        if active.notice_text.as_deref() == Some(notice.as_str()) { return }
        let Some(session) = sessions.get(&active.claim.provider_session_id).await else { return };
        match session.send_user_msg(notice.clone(), true).await {
            Ok(SendResult::Acknowledged) => active.notice_text = Some(notice),
            Ok(SendResult::Started) => tracing::error!("active reset steer unexpectedly started a turn"),
            Err(error) => tracing::warn!(%error, "Context reset notice was not queued; will retry"),
        }
    }
}
