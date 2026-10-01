#![allow(clippy::large_futures)]
use std::{
    collections::{HashMap, HashSet},
    sync::Arc,
};

use anyhow::Result;
use sha2::{Digest, Sha256};
use tokio::{
    sync::watch,
    time::{Duration, Instant, MissedTickBehavior},
};

use super::{
    SessionManager,
    provider::{
        issue_system_prompt, materialized_profile_with_binding,
        operational_status_unknown_profile, pr_system_prompt,
    },
};
use crate::{
    agent_session::SessionFactory,
    config::{Config, Profile},
    objects::LocalObjects,
    store::{ProfileRecord, StoreActor, TurnClaim},
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum GroupKind {
    Issue,
    Pr,
}

impl GroupKind {
    pub(super) fn as_str(self) -> &'static str {
        match self {
            Self::Issue => "issue",
            Self::Pr => "pr",
        }
    }
}

pub(crate) struct GroupSpec {
    pub(super) kind: GroupKind,
    pub(super) profile: Profile,
    pub(super) profile_record: ProfileRecord,
}

impl GroupSpec {
    pub(crate) fn new_with_binding(
        kind: GroupKind,
        profile: Profile,
        binding: &crate::config::RuntimeBinding,
        store: &StoreActor,
    ) -> Result<Self> {
        let profile_record = materialized_profile_with_binding(&profile, binding)?;
        store.register_profile(profile_record.clone())?;
        Ok(Self { kind, profile, profile_record })
    }

    pub(crate) fn group_id(&self) -> String {
        format!("{}:{}", self.kind.as_str(), self.profile.id)
    }
}

/// Shared logical driver; adapters own physical resources and the store owns durable identities.
pub(super) struct GroupDriver<'a> {
    pub(super) store: &'a StoreActor,
    pub(super) github: &'a LocalObjects,
    pub(super) config: &'a Config,
    pub(super) spec: &'a GroupSpec,
    pub(super) sessions: SessionManager,
}

impl GroupDriver<'_> {
    async fn retire_reassigned_sessions(&self) -> Result<(), crate::agent_session::SessionError> {
        let ids = match self.store.stopping_provider_sessions(
            self.spec.profile.id.clone(),
            self.spec.kind.as_str().into(),
        ) {
            Ok(ids) => ids,
            Err(error) => {
                tracing::error!(%error, "cannot inspect reassigned provider sessions");
                return Err(crate::agent_session::SessionError::Failed(error.to_string()));
            }
        };
        for id in &ids {
            // A sleeping session may already have been released by resume's
            // retain pass. Only a handle owned by this worker needs teardown.
            if self.sessions.is_managed(id).await {
                self.sessions.remove(id).await?;
            }
        }
        for id in ids {
            match self.store.retire_stopping_provider_session(id.clone()) {
                Ok(true) => {
                    tracing::info!(provider_session = %id, "retired fenced provider session after reassignment")
                }
                Ok(false) => {}
                Err(error) => {
                    tracing::error!(%error, provider_session = %id, "cannot retire reassigned provider session");
                    return Err(crate::agent_session::SessionError::Failed(error.to_string()));
                }
            }
        }
        Ok(())
    }

    async fn resume(&self, active_sessions: &HashSet<String>) -> Result<()> {
        let store = self.store;
        let profile = &self.spec.profile;
        let candidates =
            store.provider_resume_candidates(profile.id.clone(), self.spec.kind.as_str().into())?;
        let retained = candidates
            .iter()
            .map(|candidate| candidate.provider_session_id.clone())
            .chain(active_sessions.iter().cloned())
            .collect();
        self.sessions.retain(&retained).await?;
        let mut unavailable = None;
        for candidate in candidates {
            if active_sessions.contains(&candidate.provider_session_id)
                || self.sessions.is_live(&candidate.provider_session_id).await
            {
                continue;
            }
            if self.sessions.is_managed(&candidate.provider_session_id).await {
                self.sessions.remove(&candidate.provider_session_id).await?;
            }
            // Fence a lost handle before checking compatibility, so a blocked
            // session cannot leave a running turn behind.
            if candidate
                .active_turn_lifecycle
                .as_deref()
                .is_some_and(|state| matches!(state, "starting" | "running"))
                && let Some(turn_id) = &candidate.active_turn_id
            {
                store.mark_turn_terminal(turn_id.clone(), "unknown".into(), None)?;
                store.enqueue_operational_status(
                    turn_id.clone(),
                    operational_status_unknown_profile(&profile.id),
                )?;
                continue;
            }
            let Some(worktree_path) = candidate.worktree_path.clone() else {
                let message = "persisted provider session has no active worktree";
                tracing::warn!(kind = self.spec.kind.as_str(), number = candidate.number, provider_session = %candidate.provider_session_id, "{message}");
                store.block_provider_session(
                    candidate.provider_session_id.clone(),
                    message.into(),
                )?;
                continue;
            };
            let head_ref = if self.spec.kind == GroupKind::Pr {
                let Some(head_ref) = candidate.worktree_head_ref.as_deref() else {
                    let message = "persisted PR provider session has no local branch reference";
                    tracing::warn!(pr = candidate.number, provider_session = %candidate.provider_session_id, "{message}");
                    store.block_provider_session(
                        candidate.provider_session_id.clone(),
                        message.into(),
                    )?;
                    continue;
                };
                Some(head_ref)
            } else {
                None
            };
            let instructions = match head_ref {
                Some(head_ref) => pr_system_prompt(
                    self.config,
                    profile,
                    candidate.number,
                    head_ref,
                    candidate.member_login.as_deref(),
                ),
                None => issue_system_prompt(
                    self.config,
                    profile,
                    candidate.number,
                    candidate.member_login.as_deref(),
                ),
            };
            let instruction_revision = hex::encode(Sha256::digest(instructions.as_bytes()));
            let incompatible_reason = if candidate.repository != self.config.repository {
                Some("repository mismatch")
            } else if candidate.work_item_kind != self.spec.kind.as_str() {
                Some("Work Item kind mismatch")
            } else if candidate.profile_id != profile.id {
                Some("Profile id mismatch")
            } else if candidate.provider_kind != profile.adapter_type {
                Some("native adapter mismatch")
            } else if self.spec.kind == GroupKind::Issue && !profile.workspace().is_dir() {
                Some("Profile workspace is not a directory")
            } else if !worktree_path.is_dir() {
                Some("worktree is not a directory")
            } else {
                None
            };
            if let Some(reason) = incompatible_reason {
                let message =
                    "persisted provider session is incompatible with its Profile/worktree";
                tracing::warn!(
                    kind = self.spec.kind.as_str(), number = candidate.number,
                    provider_session = %candidate.provider_session_id, reason,
                    stored_profile_revision = candidate.profile_revision,
                    current_profile_revision = self.spec.profile_record.revision,
                    "{message}"
                );
                store.block_provider_session(
                    candidate.provider_session_id.clone(),
                    message.into(),
                )?;
                continue;
            }
            let mut effective_profile = profile.clone();
            effective_profile.workspace = Some(worktree_path);
            store.clear_provider_binding(candidate.provider_session_id.clone())?;
            let result = self.sessions.resume(candidate.provider_session_id.clone(), effective_profile, instructions).await;
            if let Err(error) = &result {
                store.record_provider_resume_error(candidate.provider_session_id.clone(), error.to_string())?;
            }
            match result {
                Ok(binding_id) => {
                    if let Some(binding_id) = binding_id {
                        store.record_provider_resume(
                            candidate.provider_session_id.clone(),
                            binding_id,
                            self.spec.profile_record.clone(),
                            instruction_revision.clone(),
                        )?;
                    }
                    tracing::info!(
                        kind = self.spec.kind.as_str(), number = candidate.number,
                        provider_session = %candidate.provider_session_id,
                        prior_lifecycle = %candidate.session_lifecycle,
                        "resumed compatible provider session"
                    );
                }
                Err(crate::agent_session::SessionError::HistoryUnavailable(reason)) => {
                    // This path is allowed only after resume's stop proof and
                    // the adapter's positive evidence of missing native history.
                    store.begin_provider_replacement(candidate.provider_session_id.clone(), self.spec.profile_record.clone())?;
                    tracing::warn!(provider_session = %candidate.provider_session_id, %reason, "native history missing; requesting fresh Context");
                }
                Err(error @ (crate::agent_session::SessionError::Unavailable | crate::agent_session::SessionError::Deferred(_))) => {
                    unavailable = Some(error)
                }
                Err(error) => {
                    store.block_provider_session(
                        candidate.provider_session_id.clone(),
                        error.to_string(),
                    )?;
                    tracing::error!(%error, kind = self.spec.kind.as_str(), number = candidate.number, provider_session = %candidate.provider_session_id, "cannot resume provider session");
                }
            }
        }
        if let Some(error) = unavailable {
            return Err(error.into());
        }
        Ok(())
    }

    async fn materialize_next_assignment(&self) {
        match self.spec.kind {
            GroupKind::Issue => self.materialize_next_issue_assignment().await,
            GroupKind::Pr => Box::pin(self.materialize_next_pr_assignment()).await,
        }
    }
}

pub(crate) async fn agent_group_worker(
    store: Arc<StoreActor>,
    github: Arc<LocalObjects>,
    config: Config,
    spec: GroupSpec,
    factory: Arc<dyn SessionFactory>,
    reports: tokio::sync::mpsc::Sender<crate::health::ProviderHealthUpdate>,
    fatal_stops: tokio::sync::mpsc::Sender<String>,
    mut shutdown: watch::Receiver<bool>,
) -> Option<String> {
    let driver = GroupDriver {
        store: &store,
        github: &github,
        config: &config,
        spec: &spec,
        sessions: SessionManager::new(factory, config.runtime.root().to_path_buf(), config.runtime.offline_stopped_sessions.clone()),
    };
    let drive_error = driver.drive(&reports, &fatal_stops, &mut shutdown).await;
    let retain_error = if drive_error.is_none() {
        driver
            .sessions
            .retain(&std::collections::HashSet::new())
            .await
            .err()
            .map(|error| error.to_string())
    } else {
        None
    };
    if retain_error.is_some()
        && let Some(error) = driver.sessions.take_stop_failure().await
    {
        let _ = fatal_stops.send(error).await;
    }
    drive_error.or(retain_error)
}

impl GroupDriver<'_> {
    async fn finish_running(
        &self,
        mut active: RunningAgentTurn,
        lifecycle: &str,
        error: Option<String>,
    ) -> Result<(), crate::agent_session::SessionError> {
        active.telemetry.finish(lifecycle);
        let result = if let Some(reset_id) = &active.reset_id {
            let reset = self.store.refresh_context_reset(reset_id.clone());
            let expected = reset.as_ref().map(super::provider::render_context_reset_notice);
            let observed = if lifecycle == "completed" {
                match (self.sessions.get(&active.claim.provider_session_id).await, &expected) {
                    (Some(session), Ok(message)) => session.message_was_processed(message).await,
                    (None, _) => Err(crate::agent_session::SessionError::Unavailable),
                    (_, Err(error)) => Err(crate::agent_session::SessionError::Failed(error.to_string())),
                }
            } else { Ok(false) };
            match (lifecycle, observed) {
                ("completed", Ok(true)) => {
                    // The durable reset stays interrupting until native teardown
                    // is proved; a failed stop cannot enable a replacement.
                    self.sessions.remove(&active.claim.provider_session_id).await?;
                    self.store.mark_context_reset_turn_terminal(
                        reset_id.clone(), active.claim.turn_id.clone(), lifecycle.into(),
                    )
                }
                ("completed", _) if active.claim.trigger_kind != "context_reset_notice" => {
                    self.store.defer_context_reset_notice(
                        reset_id.clone(), active.claim.turn_id.clone(), lifecycle.into(), None,
                    )
                }
                ("completed", Ok(false)) if active.notice_text.as_deref()
                    != expected.as_ref().ok().map(String::as_str) => {
                    self.store.defer_context_reset_notice(
                        reset_id.clone(), active.claim.turn_id.clone(), lifecycle.into(), None,
                    )
                }
                ("completed", evidence) => {
                    let reason = match evidence {
                        Ok(false) => "Pi did not record the reset notice followed by assistant work".to_string(),
                        Err(error) => error.to_string(),
                        Ok(true) => unreachable!(),
                    };
                    let result = self.store.defer_context_reset_notice(
                        reset_id.clone(), active.claim.turn_id.clone(), lifecycle.into(), None,
                    );
                    if result.is_ok() {
                        let _ = self.store.fail_context_reset(reset_id.clone(), reason);
                    }
                    result
                }
                (_, _) => {
                    let result = self.store.mark_turn_terminal(active.claim.turn_id.clone(), lifecycle.into(), error.clone());
                    let _ = self.store.fail_context_reset(
                        reset_id.clone(), format!("old session ended {lifecycle} before reset notice was processed"),
                    );
                    result
                }
            }
        } else {
            self.store.mark_turn_terminal(active.claim.turn_id.clone(), lifecycle.into(), error)
        };
        if let Err(error) = result {
            tracing::error!(%error, turn = %active.claim.turn_id, "cannot record session terminal");
            if active.reset_id.is_some() {
                return Err(crate::agent_session::SessionError::Failed(error.to_string()));
            }
        }
        if active.reset_id.is_none() && active.claim.trusted_mention && lifecycle != "unknown" {
            let reaction = if lifecycle == "completed" { "+1" } else { "confused" };
            let _ = self.store.enqueue_turn_reaction(active.claim.turn_id.clone(), reaction.into());
        }
        if lifecycle == "unknown" {
            let _ = self.store.enqueue_operational_status(
                active.claim.turn_id,
                operational_status_unknown_profile(&active.claim.profile_id),
            );
            self.sessions.remove(&active.claim.provider_session_id).await?;
        }
        Ok(())
    }

    /// Drain buffered terminals before checking disconnection: closing a sender
    /// does not erase its already-delivered terminal receipt.
    async fn poll_running(
        &self,
        running: &mut HashMap<String, RunningAgentTurn>,
    ) -> Result<(), crate::agent_session::SessionError> {
        use crate::agent_session::SessionEvent;
        use tokio::sync::broadcast::error::TryRecvError;
        for id in running.keys().cloned().collect::<Vec<_>>() {
            let active = running.get_mut(&id).expect("owned active session");
            let terminal = loop {
                match active.events.try_recv() {
                    Ok(SessionEvent::TurnStarted { .. }) => {}
                    Ok(SessionEvent::TurnTerminal { provider_turn_id, outcome, error }) => {
                        if provider_turn_id != active.provider_turn_id {
                            continue;
                        }
                        if let Some(error) = &error {
                            tracing::warn!(%provider_turn_id, %error, "session terminal with error");
                        }
                        break Some((outcome.lifecycle(), error));
                    }
                    Err(TryRecvError::Empty) => break None,
                    Err(TryRecvError::Closed) => break Some(("unknown", Some("provider event stream closed before terminal receipt".into()))),
                    Err(TryRecvError::Lagged(skipped)) => {
                        tracing::warn!(
                            skipped,
                            provider_session = id,
                            "session event consumer lagged"
                        );
                        break Some(("unknown", Some(format!("provider event stream lagged by {skipped} events"))));
                    }
                }
            };
            if let Some((lifecycle, error)) = terminal {
                self.finish_running(running.remove(&id).expect("owned active session"), lifecycle, error)
                    .await?;
            }
        }
        Ok(())
    }

    async fn drive(
        &self,
        reports: &tokio::sync::mpsc::Sender<crate::health::ProviderHealthUpdate>,
        fatal_stops: &tokio::sync::mpsc::Sender<String>,
        shutdown: &mut watch::Receiver<bool>,
    ) -> Option<String> {
        // The runtime holds the exclusive state lock; no execution handles
        // exist here yet, so any interrupting reset belongs to the prior run.
        if let Err(error) = self
            .store
            .recover_context_resets(self.spec.kind.as_str().into(), self.spec.profile.id.clone())
        {
            let _ = reports
                .send(crate::health::ProviderHealthUpdate {
                    group: self.spec.group_id(),
                    error: Some(error.to_string()),
                })
                .await;
            return None;
        }
        let mut running = HashMap::new();
        let mut tick = tokio::time::interval(Duration::from_millis(250));
        tick.set_missed_tick_behavior(MissedTickBehavior::Delay);
        let mut recovery = tokio::time::Instant::now();
        let mut reactivation_retry = tokio::time::Instant::now();
        let mut reactivation_error = None;
        let mut available = false;
        loop {
            tokio::select! {
                biased;
                _ = shutdown.changed() => {
                    for (_, active) in running.drain() {
                        if let Err(error) = self.finish_running(active, "unknown", Some("provider session disconnected before terminal receipt".into())).await {
                            let stop_failure = self.sessions.take_stop_failure().await;
                            let message = error.to_string();
                            if let Some(error) = stop_failure {
                                let _ = fatal_stops.send(error).await;
                            }
                            let _ = reports.send(crate::health::ProviderHealthUpdate {
                                group: self.spec.group_id(),
                                error: Some(message.clone()),
                            }).await;
                            return Some(message);
                        }
                    }
                    return None;
                }
                _ = tick.tick() => {}
            }
            if let Err(error) = self.poll_running(&mut running).await {
                let stop_failure = self.sessions.take_stop_failure().await;
                let message = error.to_string();
                if let Some(error) = stop_failure {
                    let _ = fatal_stops.send(error).await;
                }
                let _ = reports
                    .send(crate::health::ProviderHealthUpdate {
                        group: self.spec.group_id(),
                        error: Some(message.clone()),
                    })
                    .await;
                return Some(message);
            }
            if let Err(error) = self.retire_reassigned_sessions().await {
                let stop_failure = self.sessions.take_stop_failure().await;
                let message = error.to_string();
                if let Some(error) = stop_failure {
                    let _ = fatal_stops.send(error).await;
                }
                let _ = reports
                    .send(crate::health::ProviderHealthUpdate {
                        group: self.spec.group_id(),
                        error: Some(message.clone()),
                    })
                    .await;
                return Some(message);
            }
            for active in running.values_mut() {
                self.begin_active_context_reset(active).await;
                self.forward_running_input(active).await;
            }
            if tokio::time::Instant::now() >= recovery {
                let readiness = self.sessions.check().await;
                available = readiness.is_ok();
                let result = match readiness {
                    Ok(()) => self.resume(&running.keys().cloned().collect()).await,
                    Err(error) => Err(error.into()),
                };
                let error = result.err().map(|error| error.to_string()).or_else(|| reactivation_error.clone());
                if let Some(error) = &error {
                    tracing::warn!(%error, kind = self.spec.kind.as_str(), "session recovery unavailable");
                }
                if reports
                    .send(crate::health::ProviderHealthUpdate {
                        group: self.spec.group_id(),
                        error,
                    })
                    .await
                    .is_err()
                {
                    return None;
                }
                if let Some(error) = self.sessions.take_stop_failure().await {
                    let _ = fatal_stops.send(error.clone()).await;
                    return Some(error);
                }
                recovery = tokio::time::Instant::now() + Duration::from_secs(2);
            }
            if available {
                if tokio::time::Instant::now() >= reactivation_retry {
                    let (_, lifecycle_turn, retryable_error) = Box::pin(self.handle_next_work_item_lifecycle()).await;
                    if let Some(active) = lifecycle_turn {
                        running.insert(active.claim.provider_session_id.clone(), active);
                    }
                    if let Some(error) = retryable_error {
                        reactivation_retry = recovery;
                        reactivation_error = Some(error.clone());
                        let _ = reports.send(crate::health::ProviderHealthUpdate {
                            group: self.spec.group_id(),
                            error: Some(error),
                        }).await;
                    } else if reactivation_error.take().is_some() {
                        let _ = reports.send(crate::health::ProviderHealthUpdate {
                            group: self.spec.group_id(),
                            error: None,
                        }).await;
                    }
                }
                match Box::pin(self.materialize_next_context_reset()).await {
                    Ok(_) => {}
                    Err(error) => {
                        let stop_failure = self.sessions.take_stop_failure().await;
                        let message = error.to_string();
                        if let Some(error) = stop_failure {
                            let _ = fatal_stops.send(error).await;
                        }
                        let _ = reports
                            .send(crate::health::ProviderHealthUpdate {
                                group: self.spec.group_id(),
                                error: Some(message.clone()),
                            })
                            .await;
                        return Some(message);
                    }
                }
                self.materialize_next_assignment().await;
            }
            if let Some(active) = self.start_next_agent_turn().await {
                running.insert(active.claim.provider_session_id.clone(), active);
            }
            if let Some(error) = self.sessions.take_stop_failure().await {
                let _ = fatal_stops.send(error.clone()).await;
                let _ = reports
                    .send(crate::health::ProviderHealthUpdate {
                        group: self.spec.group_id(),
                        error: Some(error.clone()),
                    })
                    .await;
                return Some(error);
            }
        }
    }
}

/// In-memory projection of the in-flight turn claim: the store is the
/// authority; this cache attributes the terminal event and remembers the
/// last reset notice accepted by the native session.
pub(crate) struct RunningAgentTurn {
    pub(crate) telemetry: crate::telemetry::Operation,
    pub(crate) claim: TurnClaim,
    pub(crate) provider_turn_id: String,
    pub(crate) reset_id: Option<String>,
    pub(crate) notice_text: Option<String>,
    pub(crate) last_notice_poll: Option<Instant>,
    /// The receiver that observed this turn's `TurnStarted`, created before
    /// the send and handed off with the turn, so the drive loop consumes the
    /// terminal with no subscription-timing gap.
    pub(crate) events: tokio::sync::broadcast::Receiver<crate::agent_session::SessionEvent>,
}
