use std::{
    collections::BTreeMap,
    path::Path,
    process::Stdio,
    sync::{
        Arc, Mutex as StdMutex,
        atomic::{AtomicI64, Ordering},
    },
};

pub use serde_json::{Value, json};
use thiserror::Error;
use tracing::Instrument as _;

pub use tokio::{
    io::{AsyncBufReadExt as _, AsyncWriteExt as _, BufReader},
    process::{Child, ChildStdin, Command},
    sync::{Mutex, broadcast, oneshot, watch},
    time::{Duration, timeout},
};

pub(crate) use crate::config::{BubConfig, CodexConfig, PiConfig, Profile};

const REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
type PendingRequests = BTreeMap<i64, oneshot::Sender<Result<Value, ProviderError>>>;

#[derive(Debug, Error)]
pub enum ProviderError {
    #[error("provider deferred input: {0}")]
    Deferred(String),
    #[error("cannot start provider process: {0}")]
    Start(#[from] std::io::Error),
    #[error("provider request {method} timed out")]
    Timeout { method: String },
    #[error("provider disconnected")]
    Disconnected,
    #[error("provider protocol error: {0}")]
    Protocol(String),
    #[error("provider created a session without a recoverable identity: {0}")]
    CreatedWithoutIdentity(String),
}

#[derive(Debug, Clone)]
pub enum ProviderNotification {
    TurnStarted { thread_id: String, turn_id: String },
    TurnCompleted { thread_id: String, turn_id: String, status: String, error: Option<String> },
    Activity { method: String, thread_id: Option<String>, turn_id: Option<String> },
    Disconnected,
}

#[derive(Debug, Clone)]
pub struct ProviderSession {
    pub thread_id: String,
}

#[derive(Debug, Clone)]
pub struct ProviderTurn {
    pub turn_id: String,
}

/// Trait abstracting over native agent providers.
#[async_trait::async_trait]
pub trait AgentProvider: Send + Sync {
    fn subscribe(&self) -> broadcast::Receiver<ProviderNotification>;

    async fn can_accept_input(&self, _thread_id: &str) -> Result<bool, ProviderError> {
        Ok(true)
    }

    async fn managed_state(&self, _thread_id: &str) -> Result<crate::agent_session::ManagedState, ProviderError> {
        Ok(crate::agent_session::ManagedState::Unknown)
    }

    /// Resolves when the provider connection is permanently closed (process
    /// exit, stdio EOF, fatal protocol error). Connection death is a
    /// connection-scoped fact observed inside the adapter. Adapter session
    /// handles expose their own latched availability to core consumers.
    async fn closed(&self);

    async fn start_session(
        &self,
        profile: &Profile,
        developer_instructions: &str,
    ) -> Result<ProviderSession, ProviderError>;

    async fn inject_context(&self, thread_id: &str, context: &str) -> Result<(), ProviderError>;

    async fn resume_session(
        &self,
        thread_id: &str,
        profile: &Profile,
        developer_instructions: &str,
    ) -> Result<ProviderSession, ProviderError>;

    async fn start_turn(
        &self,
        thread_id: &str,
        profile: &Profile,
        event_references: &str,
    ) -> Result<ProviderTurn, ProviderError>;

    async fn steer(
        &self,
        thread_id: &str,
        expected_turn_id: &str,
        event_references: &str,
    ) -> Result<(), ProviderError>;

    /// Best-effort termination of the observed active turn. Idempotent at the
    /// Braid state-machine boundary: the provider may report "no active turn"
    /// after convergence, and the terminal still arrives via notifications.
    async fn interrupt(&self, thread_id: &str, turn_id: &str) -> Result<(), ProviderError>;

    /// Pi's steer acknowledgement means queued, not sampled. The native
    /// session must contain this exact user message followed by assistant work.
    async fn message_was_processed(&self, _thread_id: &str, _message: &str) -> Result<bool, ProviderError> {
        Err(ProviderError::Protocol("native message receipt is unavailable for this adapter".into()))
    }
}

mod bub;
mod codex;
mod process;
mod pi;
mod session;
mod util;

pub use bub::BubProvider;
pub use codex::CodexProvider;
pub(crate) use factory::session_factory;
pub use pi::PiProvider;
pub use session::ProviderAgentSession;
mod factory;
pub(crate) use util::{path_text, required_string};
