use tokio::sync::broadcast;
use std::path::PathBuf;

#[derive(Clone)]
pub(crate) struct CliContext {
    pub(crate) state: PathBuf,
    pub(crate) binding_id: String,
}

/// Terminal outcome of a provider turn.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TurnOutcome {
    Completed,
    Interrupted,
    Failed,
    Unknown,
}

impl TurnOutcome {
    pub fn lifecycle(self) -> &'static str {
        match self {
            Self::Completed => "completed",
            Self::Interrupted => "interrupted",
            Self::Failed => "failed",
            Self::Unknown => "unknown",
        }
    }
}

/// Synchronous scheduling decision returned by `send_user_msg`.
///
/// This carries no lifecycle facts: turn identity, terminal outcomes, and
/// failures are reported solely through the `SessionEvent` stream, which is
/// the single authority for everything the durable store records.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SendResult {
    /// A new turn was accepted; observe `SessionEvent::TurnStarted` next.
    Started,
    /// The message was accepted without creating a new turn (steering).
    Acknowledged,
}

/// Lifecycle events that the core needs to react to.
///
/// Delivery guarantees, enforced by the adapter:
///
/// - Exactly one `TurnStarted` per accepted turn (the provider reports the
///   fact twice — response and notification — and the adapter deduplicates).
/// - Exactly one `TurnTerminal` per started turn, always following its
///   `TurnStarted`. Session death is no exception: the adapter synthesizes
///   `TurnTerminal { outcome: Unknown, .. }` for the in-flight turn before
///   going quiet, so a started turn is never left without a terminal.
/// - No events for messages that only return `Acknowledged`.
/// - Handle availability is observed independently through `is_unavailable`,
///   including while idle. It is latched for the lifetime of the handle;
///   restoring a durable session produces a new handle.
///
/// Delivery reliability is the consumer's side of the contract: the receiver
/// that observed `TurnStarted` (created before the send) is handed to the
/// drive loop inside `RunningAgentTurn`, so no fact can be lost to a
/// subscription-timing gap. Across restarts, resume-time fencing of orphaned
/// `starting`/`running` turns is the second authoritative path.
#[derive(Debug, Clone)]
pub enum SessionEvent {
    /// A provider turn accepted and started; the single authority for the
    /// provider turn id.
    TurnStarted { provider_turn_id: String },
    /// The turn reached a terminal outcome. `error` carries the provider's
    /// reason when the outcome is `Failed` or `Unknown`.
    TurnTerminal { provider_turn_id: String, outcome: TurnOutcome, error: Option<String> },
}

#[derive(Debug, thiserror::Error)]
pub enum SessionError {
    /// No input was accepted; retain the durable message for later delivery.
    #[error("session deferred input: {0}")]
    Deferred(String),
    #[error("session failed: {0}")]
    Failed(String),
    #[error("session is unavailable")]
    Unavailable,
    /// The adapter confirmed that the persisted native history cannot be located.
    #[error("native history is unavailable: {0}")]
    HistoryUnavailable(String),
    /// The provider created a physical session, but materialization did not finish.
    /// Retain even an unknown identity as evidence; it is not an unstarted attempt.
    #[error("physical session materialization failed: {reason}")]
    Materialization { session_id: Option<String>, reason: String },
}

/// The core-facing Agent Session handle.
///
/// `send_user_msg` returns as soon as the adapter has accepted the message;
/// the event stream is the single authority for all lifecycle facts. The
/// adapter owns physical session mechanics (create, steer, interrupt,
/// provider notification translation). The core orchestrates context
/// replacement by starting a fresh session with materialized context through
/// `SessionManager`; there is no in-place reset message.
#[async_trait::async_trait]
pub trait AgentSession: Send + Sync {
    fn events(&self) -> broadcast::Receiver<SessionEvent>;

    /// True once this handle can no longer safely dispatch. This does not
    /// imply that the provider's persisted session has been deleted.
    fn is_unavailable(&self) -> bool;

    /// Whether a new ordinary input can currently be accepted. This is only
    /// a snapshot; `send_user_msg` may still race and return Deferred.
    async fn can_accept_input(&self) -> Result<bool, SessionError>;

    /// Release this handle's execution resources, best-effort interrupting
    /// its active turn. Other sessions must remain usable.
    async fn close(&self) -> Result<(), SessionError>;

    /// Send a user message batch. `steering` selects the provider steer path
    /// for a running turn. A non-steering message while running, or a steer
    /// while idle, returns `Deferred` without accepting the input.
    async fn send_user_msg(&self, msg: String, steering: bool) -> Result<SendResult, SessionError>;

    /// Best-effort termination of the in-flight turn — the control-plane
    /// sibling of steering: both are immediate operations addressed to the
    /// observed active turn, but `interrupt` carries control (terminate)
    /// rather than input.
    ///
    /// Idempotent at the state-machine boundary: no in-flight turn (or a turn
    /// that already completed) is `Ok(())`. The terminal still arrives through
    /// the event stream — `Interrupted` when honored, or the natural outcome
    /// if the turn completed first — so callers never wait on a side channel.
    async fn interrupt(&self) -> Result<(), SessionError>;

    /// Prove that this exact user message appears in native session history
    /// before subsequent assistant activity. Unsupported adapters cannot
    /// authorize a context replacement from an RPC acknowledgement alone.
    async fn message_was_processed(&self, _message: &str) -> Result<bool, SessionError> {
        Ok(false)
    }
}

/// An adapter-created handle and the opaque identity to bind in the durable store.
pub(crate) struct CreatedSession {
    pub(crate) id: String,
    pub(crate) session: std::sync::Arc<dyn AgentSession>,
    pub(crate) native_home: Option<std::path::PathBuf>,
    pub(crate) native_session_path: Option<std::path::PathBuf>,
    pub(crate) native_session_id: Option<String>,
}

/// Core-owned creation contract. Implementations own their physical topology;
/// callers supply already-selected instructions, Context and workspace.
#[async_trait::async_trait]
pub(crate) trait SessionFactory: Send + Sync {
    /// Check runtime availability even before a Work Item has a session.
    async fn check(&self) -> Result<(), SessionError>;
    async fn start(
        &self,
        profile: crate::config::Profile,
        instructions: String,
        context: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError>;
    async fn resume(
        &self,
        id: &str,
        profile: crate::config::Profile,
        instructions: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError>;

    /// Close the provider connection/process owned by this factory.
    /// Provider-internal agents and resources belong to the provider runtime.
    async fn teardown(&self, _id: &str) -> Result<(), SessionError> {
        Ok(())
    }
}
