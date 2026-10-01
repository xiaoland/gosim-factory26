use crate::{
    agent_session::{AgentSession, CliContext, CreatedSession, SessionError, SessionFactory},
    config::Profile,
};
use std::{
    collections::{HashMap, HashSet},
    sync::Arc,
    path::PathBuf,
};
use tokio::sync::Mutex;

/// Ephemeral handles indexed by the store's opaque session identity. Physical
/// resource ownership and sharing stay in the injected adapter factory.
pub(super) struct SessionManager {
    factory: Arc<dyn SessionFactory>,
    state: PathBuf,
    sessions: Mutex<HashMap<String, ManagedSession>>,
    stopped: Mutex<HashSet<String>>,
    stop_failure: Mutex<Option<String>>,
    uncertain_recoveries: Mutex<HashSet<String>>,
    recovery_inputs: Mutex<HashMap<String, HashSet<String>>>,
    deferred: Mutex<Option<String>>,
    deferred_sessions: Mutex<HashSet<String>>,
}

struct ManagedSession {
    session: Arc<dyn AgentSession>,
    telemetry: crate::telemetry::Operation,
}

fn observed_session(id: &str, session: Arc<dyn AgentSession>) -> ManagedSession {
    ManagedSession {
        session,
        telemetry: crate::telemetry::Operation::new(
            "braid.session",
            vec![opentelemetry::KeyValue::new("braid.provider_session.id", id.to_owned())],
        ),
    }
}

impl SessionManager {
    pub(super) fn new(factory: Arc<dyn SessionFactory>, state: PathBuf, stopped: Vec<String>) -> Self {
        Self {
            factory,
            state,
            sessions: Mutex::new(HashMap::new()),
            stopped: Mutex::new(stopped.into_iter().collect()),
            stop_failure: Mutex::new(None),
            uncertain_recoveries: Mutex::new(HashSet::new()),
            recovery_inputs: Mutex::new(HashMap::new()),
            deferred: Mutex::new(None),
            deferred_sessions: Mutex::new(HashSet::new()),
        }
    }

    pub(super) async fn check(&self) -> Result<(), SessionError> {
        self.factory.check().await
    }
    pub(super) async fn maintain_resources(&self) -> Result<(), SessionError> {
        self.factory.maintain_resources().await
    }
    pub(super) async fn managed_ids(&self) -> Vec<String> {
        self.sessions.lock().await.keys().cloned().collect()
    }
    pub(super) async fn allow_uncertain_recovery(&self, id: &str, new_inputs: &[String]) -> bool {
        let mut inputs = self.recovery_inputs.lock().await;
        let seen = inputs.entry(id.to_owned()).or_default();
        if new_inputs.iter().any(|input| !seen.contains(input)) {
            seen.extend(new_inputs.iter().cloned());
            self.uncertain_recoveries.lock().await.remove(id);
        }
        !self.uncertain_recoveries.lock().await.contains(id)
    }
    pub(super) async fn note_uncertain_recovery(&self, id: &str) {
        self.uncertain_recoveries.lock().await.insert(id.to_owned());
    }
    pub(super) async fn note_completed(&self, id: &str) {
        self.uncertain_recoveries.lock().await.remove(id);
    }
    pub(super) async fn record_deferred(&self, error: String) {
        *self.deferred.lock().await = Some(error);
    }
    pub(super) async fn take_deferred(&self) -> Option<String> {
        self.deferred.lock().await.take()
    }
    pub(super) async fn record_session_deferred(&self, id: &str, error: String) {
        self.deferred_sessions.lock().await.insert(id.to_owned());
        self.record_deferred(error).await;
    }
    pub(super) async fn session_deferred(&self, id: &str) -> bool {
        self.deferred_sessions.lock().await.contains(id)
    }
    pub(super) async fn clear_session_deferred(&self, id: &str) {
        self.deferred_sessions.lock().await.remove(id);
    }

    pub(super) async fn get(&self, id: &str) -> Option<Arc<dyn AgentSession>> {
        self.sessions.lock().await.get(id).map(|managed| Arc::clone(&managed.session))
    }

    pub(super) async fn is_live(&self, id: &str) -> bool {
        self.get(id).await.is_some_and(|session| !session.is_unavailable())
    }

    pub(super) async fn is_managed(&self, id: &str) -> bool {
        self.sessions.lock().await.contains_key(id)
    }

    pub(super) async fn input_ready_ids(&self) -> Vec<String> {
        let sessions: Vec<_> = self.sessions.lock().await.iter()
            .filter(|(_, managed)| !managed.session.is_unavailable())
            .map(|(id, managed)| (id.clone(), Arc::clone(&managed.session)))
            .collect();
        let mut ready = Vec::new();
        for (id, session) in sessions {
            match session.can_accept_input().await {
                Ok(true) => ready.push(id),
                Ok(false) => {},
                Err(error) => {
                    tracing::debug!(%error, provider_session = %id, "native readiness unavailable; send path will resolve failure");
                    ready.push(id);
                }
            }
        }
        ready
    }

    pub(super) async fn start(
        &self,
        profile: Profile,
        instructions: String,
        context: String,
    ) -> Result<(String, String), SessionError> {
        let binding_id = uuid::Uuid::now_v7().to_string();
        let cli = CliContext { state: self.state.clone(), binding_id: binding_id.clone() };
        let created = self.factory.start(profile, instructions, context, cli).await;
        if let Err(error @ SessionError::Deferred(_)) = &created { self.record_deferred(error.to_string()).await; }
        if let Err(error @ SessionError::StopUnproved(_)) = &created { self.record_stop_failure(error).await; }
        let CreatedSession { id, session, .. } = created?;
        self.stopped.lock().await.remove(&id);
        self.sessions.lock().await.insert(id.clone(), observed_session(&id, session));
        Ok((id, binding_id))
    }

    pub(super) async fn resume(
        &self,
        id: String,
        profile: Profile,
        instructions: String,
    ) -> Result<Option<String>, SessionError> {
        if self.is_live(&id).await {
            return Ok(None);
        }
        // An offline stop certificate or managed teardown must precede resume.
        self.remove(&id).await?;
        let binding_id = uuid::Uuid::now_v7().to_string();
        let cli = CliContext { state: self.state.clone(), binding_id: binding_id.clone() };
        let created = self.factory.resume(&id, profile, instructions, cli).await;
        if let Err(error @ SessionError::Deferred(_)) = &created { self.record_session_deferred(&id, error.to_string()).await; }
        if let Err(error @ SessionError::StopUnproved(_)) = &created { self.record_stop_failure(error).await; }
        let created = created?;
        self.clear_session_deferred(&id).await;
        if created.id != id {
            let _ = created.session.close().await;
            return Err(SessionError::Failed("resume changed the durable session identity".into()));
        }
        self.stopped.lock().await.remove(&id);
        self.sessions.lock().await.insert(id.clone(), observed_session(&id, created.session));
        Ok(Some(binding_id))
    }

    async fn record_stop_failure(&self, error: &SessionError) {
        *self.stop_failure.lock().await = Some(error.to_string());
    }

    pub(super) async fn take_stop_failure(&self) -> Option<String> {
        self.stop_failure.lock().await.take()
    }

    pub(super) async fn remove(&self, id: &str) -> Result<(), SessionError> {
        let removed = self.sessions.lock().await.remove(id);
        let Some(mut removed) = removed else {
            if self.stopped.lock().await.contains(id) {
                return Ok(());
            }
            let error = SessionError::Failed(format!(
                "cannot prove native teardown for provider session {id}"
            ));
            self.record_stop_failure(&error).await;
            return Err(error);
        };
        if let Err(error) = self.factory.teardown(id).await {
            self.sessions.lock().await.insert(id.to_owned(), removed);
            tracing::warn!(%error, provider_session = id, "provider session shutdown failed");
            self.record_stop_failure(&error).await;
            return Err(error);
        }
        if let Err(error) = removed.session.close().await
            && !matches!(error, SessionError::Unavailable)
        {
            self.sessions.lock().await.insert(id.to_owned(), removed);
            tracing::warn!(%error, provider_session = id, "session release could not interrupt a turn");
            self.record_stop_failure(&error).await;
            return Err(error);
        }
        removed.telemetry.finish("completed");
        self.stopped.lock().await.insert(id.to_owned());
        Ok(())
    }

    pub(super) async fn retain(&self, ids: &HashSet<String>) -> Result<(), SessionError> {
        let obsolete: Vec<_> =
            self.sessions.lock().await.keys().filter(|id| !ids.contains(*id)).cloned().collect();
        for id in obsolete {
            self.remove(&id).await?;
        }
        Ok(())
    }
}
