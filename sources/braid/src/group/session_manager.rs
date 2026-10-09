use crate::{
    agent_session::{AgentSession, CliContext, CreatedSession, SessionError, SessionFactory},
    config::Profile,
};
use std::{
    collections::{HashMap, HashSet},
    future::Future,
    path::PathBuf,
    pin::Pin,
    sync::Arc,
    task::{Context, Poll, Waker},
};
use tokio::sync::{Mutex, OwnedSemaphorePermit, Semaphore};

pub(crate) type ExecutionPool = Option<Arc<Semaphore>>;
pub(super) struct ExecutionSlot {
    _permit: Option<OwnedSemaphorePermit>,
}
type Admission =
    Pin<Box<dyn Future<Output = Result<OwnedSemaphorePermit, tokio::sync::AcquireError>> + Send>>;

/// Ephemeral handles indexed by the store's opaque session identity. Physical
/// resource ownership and sharing stay in the injected adapter factory.
pub(super) struct SessionManager {
    factory: Arc<dyn SessionFactory>,
    pool: ExecutionPool,
    admission: Mutex<Option<Admission>>,
    admission_requested: std::sync::atomic::AtomicBool,
    uncertain_slots: Mutex<Vec<Arc<ExecutionSlot>>>,
    state: PathBuf,
    sessions: Mutex<HashMap<String, ManagedSession>>,
    stopped: Mutex<HashSet<String>>,
    stop_failure: Mutex<Option<String>>,
    uncertain_recoveries: Mutex<HashSet<String>>,
    recovery_inputs: Mutex<HashMap<String, HashSet<String>>>,
    deferred: Mutex<Option<SessionError>>,
    deferred_sessions: Mutex<HashMap<String, DeferredKind>>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum DeferredKind {
    Input,
    Resource,
}

struct ManagedSession {
    session: Arc<dyn AgentSession>,
    telemetry: crate::telemetry::Operation,
    _slot: Arc<ExecutionSlot>,
}

fn observed_session(
    id: &str,
    session: Arc<dyn AgentSession>,
    slot: Arc<ExecutionSlot>,
) -> ManagedSession {
    ManagedSession {
        session,
        _slot: slot,
        telemetry: crate::telemetry::Operation::new(
            "braid.session",
            vec![opentelemetry::KeyValue::new("braid.provider_session.id", id.to_owned())],
        ),
    }
}

impl SessionManager {
    pub(super) fn new(
        factory: Arc<dyn SessionFactory>,
        state: PathBuf,
        stopped: Vec<String>,
        pool: ExecutionPool,
    ) -> Self {
        Self {
            factory,
            pool,
            admission: Mutex::new(None),
            admission_requested: std::sync::atomic::AtomicBool::new(false),
            uncertain_slots: Mutex::new(Vec::new()),
            state,
            sessions: Mutex::new(HashMap::new()),
            stopped: Mutex::new(stopped.into_iter().collect()),
            stop_failure: Mutex::new(None),
            uncertain_recoveries: Mutex::new(HashSet::new()),
            recovery_inputs: Mutex::new(HashMap::new()),
            deferred: Mutex::new(None),
            deferred_sessions: Mutex::new(HashMap::new()),
        }
    }

    pub(super) fn begin_admission_cycle(&self) {
        self.admission_requested.store(false, std::sync::atomic::Ordering::Relaxed);
    }
    pub(super) async fn end_admission_cycle(&self) {
        if !self.admission_requested.load(std::sync::atomic::Ordering::Relaxed) {
            // The durable candidate disappeared; do not retain a semaphore grant.
            self.admission.lock().await.take();
        }
    }
    pub(super) async fn admission_waiting(&self) -> bool {
        self.admission.lock().await.is_some()
    }
    pub(super) fn pool_waiting(&self) -> bool {
        self.pool.as_ref().is_some_and(|pool| pool.available_permits() == 0)
    }
    pub(super) async fn reserve(&self) -> Result<Arc<ExecutionSlot>, SessionError> {
        self.admission_requested.store(true, std::sync::atomic::Ordering::Relaxed);
        let Some(pool) = &self.pool else {
            return Ok(Arc::new(ExecutionSlot { _permit: None }));
        };
        let mut admission = self.admission.lock().await;
        let future = admission.get_or_insert_with(|| Box::pin(pool.clone().acquire_owned()));
        // Keep the semaphore's FIFO waiter, but never block a worker that must
        // observe and stop its existing sessions before another can run.
        match future.as_mut().poll(&mut Context::from_waker(Waker::noop())) {
            Poll::Ready(Ok(permit)) => {
                admission.take();
                Ok(Arc::new(ExecutionSlot { _permit: Some(permit) }))
            }
            Poll::Ready(Err(error)) => {
                admission.take();
                Err(SessionError::Failed(format!("execution pool closed: {error}")))
            }
            Poll::Pending => {
                Err(SessionError::Deferred("queued for a top-level Agent execution slot".into()))
            }
        }
    }

    pub(super) async fn check(&self) -> Result<(), SessionError> {
        self.factory.check().await
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
    pub(super) async fn record_deferred(&self, error: SessionError) {
        let mut deferred = self.deferred.lock().await;
        if error.is_resource_deferred()
            && deferred.as_ref().is_some_and(|prior| !prior.is_resource_deferred())
        {
            return;
        }
        *deferred = Some(error);
    }
    pub(super) async fn take_deferred(&self) -> Option<SessionError> {
        self.deferred.lock().await.take()
    }
    pub(super) async fn record_session_deferred(&self, id: &str, error: SessionError) {
        let kind =
            if error.is_resource_deferred() { DeferredKind::Resource } else { DeferredKind::Input };
        self.deferred_sessions.lock().await.insert(id.to_owned(), kind);
        self.record_deferred(error).await;
    }
    pub(super) async fn session_deferred(&self, id: &str) -> bool {
        self.deferred_sessions.lock().await.contains_key(id)
    }
    pub(super) async fn session_resource_deferred(&self, id: &str) -> bool {
        self.deferred_sessions.lock().await.get(id) == Some(&DeferredKind::Resource)
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

    pub(super) async fn input_ready_ids(&self, candidates: &HashSet<String>) -> Vec<String> {
        let sessions: Vec<_> = self
            .sessions
            .lock()
            .await
            .iter()
            .filter(|(id, managed)| candidates.contains(*id) && !managed.session.is_unavailable())
            .map(|(id, managed)| (id.clone(), Arc::clone(&managed.session)))
            .collect();
        let mut ready = Vec::new();
        for (id, session) in sessions {
            match session.can_accept_input().await {
                Ok(true) => {
                    self.clear_session_deferred(&id).await;
                    ready.push(id);
                }
                Ok(false) => {}
                Err(error) if error.is_deferred() => self.record_session_deferred(&id, error).await,
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
        slot: Arc<ExecutionSlot>,
    ) -> Result<(String, String), SessionError> {
        let binding_id = uuid::Uuid::now_v7().to_string();
        let cli = CliContext { state: self.state.clone(), binding_id: binding_id.clone() };
        let created = self.factory.start(profile, instructions, context, cli).await;
        if let Err(error) = &created
            && error.is_deferred()
        {
            self.record_deferred(error.clone()).await;
        }
        if let Err(error @ SessionError::StopUnproved(_)) = &created {
            self.record_stop_failure(error).await;
            self.uncertain_slots.lock().await.push(slot.clone());
        }
        let CreatedSession { id, session, .. } = created?;
        self.stopped.lock().await.remove(&id);
        self.sessions.lock().await.insert(id.clone(), observed_session(&id, session, slot));
        Ok((id, binding_id))
    }

    pub(super) async fn resume(
        &self,
        id: String,
        profile: Profile,
        instructions: String,
        slot: Arc<ExecutionSlot>,
    ) -> Result<Option<String>, SessionError> {
        if self.is_live(&id).await {
            return Ok(None);
        }
        // An offline stop certificate or managed teardown must precede resume.
        self.remove(&id).await?;
        let binding_id = uuid::Uuid::now_v7().to_string();
        let cli = CliContext { state: self.state.clone(), binding_id: binding_id.clone() };
        let created = self.factory.resume(&id, profile, instructions, cli).await;
        if let Err(error) = &created
            && error.is_deferred()
        {
            self.record_session_deferred(&id, error.clone()).await;
        }
        if let Err(error @ SessionError::StopUnproved(_)) = &created {
            self.record_stop_failure(error).await;
            self.uncertain_slots.lock().await.push(slot.clone());
        }
        let created = created?;
        self.clear_session_deferred(&id).await;
        if created.id != id {
            let stopped = match self.factory.teardown(&created.id).await {
                Ok(()) => created.session.close().await,
                Err(error) => Err(error),
            };
            if let Err(error) = stopped {
                self.uncertain_slots.lock().await.push(slot);
                let error = SessionError::StopUnproved(format!(
                    "resume changed durable identity; replacement teardown failed: {error}"
                ));
                self.record_stop_failure(&error).await;
                return Err(error);
            }
            return Err(SessionError::Failed("resume changed the durable session identity".into()));
        }
        self.stopped.lock().await.remove(&id);
        self.sessions.lock().await.insert(id.clone(), observed_session(&id, created.session, slot));
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
