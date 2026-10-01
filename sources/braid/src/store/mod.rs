use std::{
    collections::BTreeSet,
    ffi::OsString,
    fs::{self, File, OpenOptions},
    path::{Path, PathBuf},
    sync::mpsc::{self, Receiver, Sender},
    thread,
    time::Duration,
};

use rusqlite::{Connection, OpenFlags, OptionalExtension, backup::Backup, params};
use serde::Serialize;
use sha2::{Digest, Sha256};
use thiserror::Error;
use time::{Duration as TimeDuration, OffsetDateTime, format_description::well_known::Rfc3339};
use uuid::Uuid;

pub const DATABASE_SCHEMA_VERSION: u32 = MIGRATIONS[MIGRATIONS.len() - 1].version;

const INITIAL_SQL: &str = include_str!("../../migrations/0001_initial.sql");
const EVENT_KINDS_SQL: &str = include_str!("../../migrations/0002_event_kinds.sql");
const FAILED_REPLAY_DEDUPE_PREFIX: &str = "braid-failed-turn-replay-v1:";
const UNKNOWN_REPLAY_DEDUPE_PREFIX: &str = "braid-unknown-turn-replay-v1:";
const MIGRATIONS: &[Migration] = &[
    Migration { version: 1, name: "initial", sql: INITIAL_SQL },
    Migration { version: 2, name: "event_kinds", sql: EVENT_KINDS_SQL },
    Migration {
        version: 3,
        name: "local_objects",
        sql: include_str!("../../migrations/0003_local_objects.sql"),
    },
    Migration {
        version: 4,
        name: "pr_request_id",
        sql: include_str!("../../migrations/0004_pr_request_id.sql"),
    },
    Migration {
        version: 5,
        name: "local_collaboration",
        sql: include_str!("../../migrations/0005_local_collaboration.sql"),
    },
    Migration {
        version: 6,
        name: "profiles_assignment",
        sql: include_str!("../../migrations/0006_profiles_assignment.sql"),
    },
    Migration {
        version: 7,
        name: "assignee_projection",
        sql: include_str!("../../migrations/0007_assignee_projection.sql"),
    },
    Migration {
        version: 8,
        name: "cli_binding",
        sql: include_str!("../../migrations/0008_cli_binding.sql"),
    },
    Migration {
        version: 9,
        name: "member_identity",
        sql: include_str!("../../migrations/0009_member_identity.sql"),
    },
    Migration {
        version: 10,
        name: "pr_refs_draft",
        sql: include_str!("../../migrations/0010_pr_refs_draft.sql"),
    },
    Migration {
        version: 11,
        name: "local_direct_messages",
        sql: include_str!("../../migrations/0011_local_direct_messages.sql"),
    },
    Migration {
        version: 12,
        name: "local_cooperation",
        sql: include_str!("../../migrations/0012_local_cooperation.sql"),
    },
    Migration {
        version: 13,
        name: "pr_created_base",
        sql: include_str!("../../migrations/0013_pr_created_base.sql"),
    },
    Migration {
        version: 14,
        name: "pr_closing_intent",
        sql: include_str!("../../migrations/0014_pr_closing_intent.sql"),
    },
    Migration {
        version: 15,
        name: "execution_failure",
        sql: include_str!("../../migrations/0015_execution_failure.sql"),
    },
    Migration {
        version: 16,
        name: "deferred_input",
        sql: include_str!("../../migrations/0016_deferred_input.sql"),
    },
    Migration { version: 17, name: "pr_reviews", sql: include_str!("../../migrations/0017_pr_reviews.sql") },
    Migration { version: 18, name: "work_item_maintenance", sql: include_str!("../../migrations/0018_work_item_maintenance.sql") },
];

#[derive(Debug, Error)]
pub enum StoreError {
    #[error("database actor is unavailable")]
    ActorUnavailable,
    #[error("database actor stopped unexpectedly")]
    ActorStopped,
    #[error("database I/O failed for {path}: {source}")]
    Io { path: PathBuf, source: std::io::Error },
    #[error("SQLite operation failed: {0}")]
    Sqlite(#[from] rusqlite::Error),
    #[error("database {path} is not an empty or Braid Rust database; move it aside explicitly")]
    ForeignDatabase { path: PathBuf },
    #[error("database schema {found} is newer than this binary's supported schema {supported}")]
    NewerSchema { found: u32, supported: u32 },
    #[error("migration {version} checksum differs from the embedded immutable migration")]
    ChecksumMismatch { version: u32 },
    #[error("migration ledger is not contiguous at version {version}")]
    NonContiguous { version: u32 },
    #[error("migration {version} failed: {message}")]
    Migration { version: u32, message: String },
    #[error("backup target {0} already exists")]
    BackupExists(PathBuf),
    #[error("another process holds the migration lease {0}")]
    MigrationBusy(PathBuf),
    #[error("database schema {found} is not ready; apply migrations through schema {required}")]
    SchemaNotReady { found: u32, required: u32 },
    #[error("invalid durable state: {0}")]
    InvalidData(String),
}

#[derive(Debug, Clone, Serialize)]
pub struct MigrationPlan {
    pub database: PathBuf,
    pub current_schema: u32,
    pub supported_schema: u32,
    pub pending: Vec<PendingMigration>,
}

#[derive(Debug, Clone, Serialize)]
pub struct PendingMigration {
    pub version: u32,
    pub name: &'static str,
    pub checksum: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct MigrationResult {
    pub previous_schema: u32,
    pub current_schema: u32,
    pub applied: Vec<u32>,
    pub backup: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize)]
pub struct StoreStatus {
    pub database: PathBuf,
    pub exists: bool,
    pub bytes: u64,
    pub schema_version: u32,
    pub supported_schema: u32,
    pub pending_migrations: usize,
    pub journal_mode: Option<String>,
}

/// Platform-neutral internal event semantics. Producers translate platform
/// deliveries into `EventKind` at ingress; queue and group consumers branch on
/// these kinds (and the semantic `detail`) only, never on platform event names
/// or actions. Adding a platform means adding a producer mapping.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum EventKind {
    /// Activate the dormant Agent Group (native platform assignment, or an
    /// internal activation such as local `braid pr create`).
    Assign,
    /// Native platform unassignment; retires the group after debounce.
    Unassign,
    /// A trusted Human addressed the Agent (permission resolved at delivery).
    /// Urgent wake; on a dormant open Work Item it is consumed as `Assign`.
    Mention,
    /// Ordinary wake signal (new comment, head sync, review request, ...).
    Wake,
    /// Content became stale: edit/delete/dismiss/resolve, including a
    /// cross-surface Associated Issue description change (`detail =
    /// "cross_surface"`). Replaces the group Agent Context.
    Invalidate,
    /// Work Item lifecycle transition; `detail` is `closed`, `reopened`, or
    /// `merged`.
    Lifecycle,
    /// Correlated Agent-origin write. Evidence only; never wakes or
    /// invalidates the same Agent and is consumed at ingest.
    OriginEcho,
    /// Ping, first observation, or unknown variant. Evidence only; consumed
    /// at ingest.
    Noop,
}

impl EventKind {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Assign => "assign",
            Self::Unassign => "unassign",
            Self::Mention => "mention",
            Self::Wake => "wake",
            Self::Invalidate => "invalidate",
            Self::Lifecycle => "lifecycle",
            Self::OriginEcho => "origin_echo",
            Self::Noop => "noop",
        }
    }

    pub fn from_str(value: &str) -> Option<Self> {
        Some(match value {
            "assign" => Self::Assign,
            "unassign" => Self::Unassign,
            "mention" => Self::Mention,
            "wake" => Self::Wake,
            "invalidate" => Self::Invalidate,
            "lifecycle" => Self::Lifecycle,
            "origin_echo" => Self::OriginEcho,
            "noop" => Self::Noop,
            _ => return None,
        })
    }

    /// Evidence-only kinds never wait in the pending ledger.
    pub fn consumed_at_ingest(self) -> bool {
        matches!(self, Self::OriginEcho | Self::Noop)
    }
}

impl std::fmt::Display for EventKind {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(self.as_str())
    }
}

#[derive(Debug, Clone)]
pub struct IngressEvent {
    pub delivery_guid: String,
    pub event_name: String,
    pub action: Option<String>,
    pub repository_node_id: String,
    pub repository: String,
    pub work_item_node_id: Option<String>,
    pub work_item_kind: Option<&'static str>,
    pub work_item_number: Option<u64>,
    pub work_item_state: Option<String>,
    pub object_node_id: Option<String>,
    pub object_version: Option<String>,
    pub object_digest: Option<String>,
    pub visible_body: Option<String>,
    pub actor_node_id: Option<String>,
    pub actor_login: Option<String>,
    pub kind: EventKind,
    pub detail: Option<&'static str>,
    pub cross_surface_invalidation: bool,
    pub origin: &'static str,
    pub reference: String,
    pub mention_candidate: bool,
    pub reaction_target: Option<ReactionTarget>,
    pub known: bool,
    pub raw_payload: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct ReactionTarget {
    pub kind: &'static str,
    pub database_id: String,
}

#[derive(Debug, Clone, Copy)]
pub struct SchedulerPolicy {
    pub quiet_seconds: u64,
    pub event_threshold: u32,
}

#[derive(Debug, Clone, Serialize)]
pub struct IngestResult {
    pub duplicate: bool,
    pub delivery_guid: String,
    pub event_id: Option<String>,
    pub event_lifecycle: Option<String>,
    pub batch_id: Option<String>,
    pub batch_lifecycle: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct RuntimeStoreStatus {
    pub deliveries: u64,
    pub duplicate_deliveries: u64,
    pub unknown_deliveries: u64,
    pub pending_batches: u64,
    pub runnable_batches: u64,
    pub pending_mentions: u64,
    pub pending_writes: u64,
    pub uncertain_writes: u64,
    pub last_reconciliation: Option<String>,
    pub batches: Vec<WakeBatchSummary>,
    pub agent_groups: Vec<AgentGroupSummary>,
    pub context_resets: Vec<ContextResetSummary>,
}

#[derive(Debug, Clone, Serialize)]
pub struct WakeBatchSummary {
    pub batch_id: String,
    pub repository: String,
    pub work_item_kind: String,
    pub work_item_number: u64,
    pub work_item_node_id: String,
    pub event_count: u64,
    pub quiet_deadline: String,
    pub urgent: bool,
    pub lifecycle: String,
}

#[derive(Debug, Clone)]
pub struct TrackedWorkItem {
    pub node_id: String,
    pub repository: String,
    pub kind: String,
    pub number: u64,
    pub state: String,
}

#[derive(Debug, Clone)]
pub struct CanonicalObjectState {
    pub node_id: String,
    pub database_id: Option<String>,
    pub object_kind: String,
    pub version: String,
    pub digest: String,
    pub lifecycle: String,
    pub author_node_id: Option<String>,
    pub author_login: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ProfileRecord {
    pub profile_id: String,
    pub revision: u64,
    pub effective_digest: String,
    pub provider_kind: String,
    pub tags: String,
    pub assignee_login: String,
    pub assignee_description: String,
}

/// Outcome of a settled (or not yet settled) native unassignment.
#[derive(Debug, Clone)]
pub struct UnassignmentOutcome {
    /// false while the debounce window is still open; the event stays pending.
    pub settled: bool,
    /// The provider session whose in-flight turn was fenced by the
    /// retirement; the caller best-effort interrupts it.
    pub provider_sessions: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct AssignmentCandidate {
    pub event_id: String,
    pub action: String,
    pub repository: String,
    pub work_item_kind: String,
    pub number: u64,
    pub unassigned: bool,
    pub target_profile_id: Option<String>,
    pub member_login: Option<String>,
}

#[derive(Debug, Clone)]
pub struct WorkItemLifecycleCandidate {
    pub event_id: String,
    pub action: String,
    pub repository: String,
    pub work_item_kind: String,
    pub number: u64,
}

#[derive(Debug, Clone)]
pub struct AgentMaterialization {
    pub assignment_id: String,
    pub agent_id: String,
    pub work_item_node_id: String,
    pub generation: u64,
    pub assignment_revision: u64,
    pub profile_id: String,
    pub profile_revision: u64,
    pub member_login: String,
    pub worktree_path: Option<PathBuf>,
    pub worktree_head_ref: Option<String>,
    pub sleeping_session: Option<SleepingProviderSession>,
    pub description_event_ids: Vec<String>,
}

#[derive(Debug, Clone)]
pub struct SleepingProviderSession {
    pub id: String,
    pub provider_kind: String,
    pub context_revision: String,
    pub instruction_revision: String,
}

#[derive(Debug, Clone)]
pub struct TurnClaim {
    pub turn_id: String,
    pub batch_id: String,
    pub provider_session_id: String,
    pub repository: String,
    pub work_item_kind: String,
    pub number: u64,
    pub profile_id: String,
    pub references: Vec<String>,
    pub steer_event_ids: Vec<String>,
    pub trusted_mention: bool,
    pub trigger_kind: String,
    pub reset_id: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ContextResetClaim {
    pub old_provider_session_id: String,
    pub reset_id: String,
    pub assignment_id: String,
    pub repository: String,
    pub work_item_kind: String,
    pub number: u64,
    pub profile_id: String,
    pub member_login: Option<String>,
    pub active_turn_id: Option<String>,
    pub provider_turn_id: Option<String>,
    pub changes: Vec<ContextResetChange>,
    pub worktree_path: Option<PathBuf>,
    pub worktree_head_ref: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ContextResetChange {
    pub reference: String,
    pub author: Option<String>,
    pub own_edit: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct AgentGroupSummary {
    pub work_item_kind: String,
    pub work_item_number: u64,
    pub profile_id: String,
    pub assignment_generation: u64,
    pub assignment_lifecycle: String,
    pub provider_session_id: Option<String>,
    pub session_lifecycle: Option<String>,
    pub active_turn_id: Option<String>,
    pub turn_lifecycle: Option<String>,
    pub turn_count: u64,
    pub finalization_turns: u64,
    pub last_finalization_lifecycle: Option<String>,
    pub provider_resume_count: u64,
    pub last_provider_resume: Option<String>,
    pub context_pressure: String,
    pub context_bytes: Option<u64>,
    pub context_error: Option<String>,
    pub worktree_path: Option<PathBuf>,
    pub worktree_lifecycle: Option<String>,
    pub worktree_head_ref: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ProviderResumeCandidate {
    pub provider_kind: String,
    pub assignment_id: String,
    pub provider_session_id: String,
    pub repository: String,
    pub work_item_kind: String,
    pub number: u64,
    pub profile_id: String,
    pub profile_revision: u64,
    pub member_login: Option<String>,
    pub instruction_revision: String,
    pub session_lifecycle: String,
    pub active_turn_id: Option<String>,
    pub active_turn_lifecycle: Option<String>,
    pub worktree_path: Option<PathBuf>,
    pub worktree_head_ref: Option<String>,
    pub needs_resume: bool,
    pub new_input_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ContextResetSummary {
    pub reset_id: String,
    pub repository: String,
    pub work_item_kind: String,
    pub work_item_number: u64,
    pub profile_id: String,
    pub lifecycle: String,
    pub continuation: bool,
    pub old_provider_session_id: String,
    pub new_provider_session_id: Option<String>,
    pub context_revision_before: String,
    pub context_revision_after: Option<String>,
}

#[derive(Debug, Clone)]
pub struct ReconciliationRun {
    pub run_id: String,
    pub repository_node_id: String,
}

#[derive(Debug, Clone)]
pub struct CanonicalComment {
    pub node_id: String,
    pub database_id: String,
    pub object_kind: &'static str,
    pub version: String,
    pub digest: String,
    pub lifecycle: &'static str,
    pub author_node_id: Option<String>,
    pub author_login: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub pinned: bool,
}

#[derive(Debug, Clone)]
pub struct CanonicalCommentSet {
    pub repository_node_id: String,
    pub repository: String,
    pub work_item_node_id: String,
    pub work_item_kind: &'static str,
    pub work_item_number: u64,
    pub work_item_state: String,
    pub work_item_version: String,
    pub work_item_digest: String,
    pub object_kind: &'static str,
    pub comments: Vec<CanonicalComment>,
}

#[derive(Debug, Clone)]
pub struct AssociatedWorkItem {
    pub node_id: String,
    pub repository_node_id: String,
    pub repository: String,
    pub kind: &'static str,
    pub number: u64,
    pub state: String,
    pub visible_description: Option<String>,
}

#[derive(Debug, Clone)]
pub struct AssociationSet {
    pub anchor_node_id: String,
    pub anchor_kind: &'static str,
    pub observed_version: String,
    pub anchor_visible_description: Option<String>,
    pub related: Vec<AssociatedWorkItem>,
}

#[derive(Debug, Clone)]
pub struct DeletedComment {
    pub node_id: String,
    pub database_id: String,
    pub author_node_id: Option<String>,
    pub author_login: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub pinned: bool,
}

pub struct StoreActor {
    sender: Sender<Command>,
    join: Option<thread::JoinHandle<()>>,
}

impl StoreActor {
    pub fn start(database: PathBuf, backups: PathBuf) -> Result<Self, StoreError> {
        let (sender, receiver) = mpsc::channel();
        let join = thread::Builder::new()
            .name("braid-sqlite".into())
            .spawn(move || actor_loop(&database, &backups, receiver))
            .map_err(|source| StoreError::Io { path: PathBuf::from("<database-actor>"), source })?;
        Ok(Self { sender, join: Some(join) })
    }

    pub fn plan(&self) -> Result<MigrationPlan, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::Plan(reply)).map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn apply(&self) -> Result<MigrationResult, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::Apply(reply)).map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn status(&self) -> Result<StoreStatus, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::Status(reply)).map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn reconcile_comments(
        &self,
        update: CanonicalCommentSet,
    ) -> Result<Vec<DeletedComment>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ReconcileComments(update, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn set_context_revision(
        &self,
        work_item_node_id: String,
        revision: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::SetContextRevision(work_item_node_id, revision, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn operational_status_comment_ids(
        &self,
        work_item_node_id: String,
    ) -> Result<BTreeSet<String>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::OperationalStatusCommentIds(work_item_node_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn reconcile_associations(&self, update: AssociationSet) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ReconcileAssociations(update, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn ingest_event(
        &self,
        event: IngressEvent,
        policy: SchedulerPolicy,
    ) -> Result<IngestResult, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::IngestEvent(Box::new(event), policy, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn advance_scheduler(&self) -> Result<u64, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::AdvanceScheduler(reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn runtime_status(&self) -> Result<RuntimeStoreStatus, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RuntimeStatus(reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn tracked_work_items(&self) -> Result<Vec<TrackedWorkItem>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::TrackedWorkItems(reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn canonical_objects(
        &self,
        work_item_node_id: String,
    ) -> Result<Vec<CanonicalObjectState>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::CanonicalObjects(work_item_node_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn begin_reconciliation(
        &self,
        repository_node_id: String,
    ) -> Result<ReconciliationRun, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BeginReconciliation(repository_node_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn finish_reconciliation(
        &self,
        run: ReconciliationRun,
        lifecycle: &'static str,
        work_item_count: usize,
        change_count: usize,
        error: Option<String>,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::FinishReconciliation(
                run,
                lifecycle,
                work_item_count,
                change_count,
                error,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn register_profile(&self, profile: ProfileRecord) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RegisterProfile(profile, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn provider_resume_candidates(
        &self,
        profile_id: String,
        work_item_kind: String,
    ) -> Result<Vec<ProviderResumeCandidate>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ProviderResumeCandidates(profile_id, work_item_kind, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn begin_provider_replacement(
        &self,
        provider_session_id: String,
        profile: ProfileRecord,
    ) -> Result<Option<ContextResetClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BeginProviderReplacement(provider_session_id, profile, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn prepare_offline_resume(&self) -> Result<Vec<String>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::PrepareOfflineResume(reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn clear_provider_binding(&self, provider_session_id: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ClearProviderBinding(provider_session_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn fence_idle_provider(&self, provider_session_id: String) -> Result<bool, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::FenceIdleProvider(provider_session_id, reply)).map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn record_provider_resume(&self, provider_session_id: String, binding_id: String, profile: ProfileRecord, instruction_revision: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RecordProviderResume(provider_session_id, binding_id, profile, instruction_revision, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn record_provider_resume_error(&self, provider_session_id: String, error: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::RecordProviderResumeError(provider_session_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn block_provider_session(
        &self,
        provider_session_id: String,
        error: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BlockProviderSession(provider_session_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn stopping_provider_sessions(
        &self,
        profile_id: String,
        work_item_kind: String,
    ) -> Result<Vec<String>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::StoppingProviderSessions(profile_id, work_item_kind, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn retire_stopping_provider_session(
        &self,
        provider_session_id: String,
    ) -> Result<bool, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RetireStoppingProviderSession(provider_session_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn assignment_candidates(
        &self,
        work_item_kind: String,
        profile_id: String,
    ) -> Result<Vec<AssignmentCandidate>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::AssignmentCandidates(work_item_kind, profile_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn work_item_lifecycle_candidates(
        &self,
        work_item_kind: String,
        limit: usize,
    ) -> Result<Vec<WorkItemLifecycleCandidate>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::WorkItemLifecycleCandidates(work_item_kind, limit, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn prepare_work_item_closure(&self, event_id: String) -> Result<bool, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::PrepareWorkItemClosure(event_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn begin_work_item_reactivation(
        &self,
        event_id: String,
        profile_id: String,
    ) -> Result<Option<AgentMaterialization>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BeginWorkItemReactivation(event_id, profile_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    #[allow(clippy::too_many_arguments)]
    pub fn complete_work_item_reactivation(
        &self,
        event_id: String,
        materialization: AgentMaterialization,
        provider_session_id: String,
        binding_id: String,
        context_revision: String,
        instruction_revision: String,
        policy: SchedulerPolicy,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::CompleteWorkItemReactivation(
                event_id,
                materialization,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                policy,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn fail_work_item_reactivation(
        &self,
        event_id: String,
        assignment_id: String,
        error: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::FailWorkItemReactivation(event_id, assignment_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn defer_work_item_reactivation(
        &self,
        event_id: String,
        assignment_id: String,
        error: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::DeferWorkItemReactivation(event_id, assignment_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn has_lifecycle_observation(
        &self,
        work_item_node_id: String,
        action: String,
        object_version: String,
    ) -> Result<bool, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::HasLifecycleObservation(
                work_item_node_id,
                action,
                object_version,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn begin_agent_assignment(
        &self,
        event_id: String,
        profile: ProfileRecord,
        context_revision: Option<String>,
        preserve_wake_batch: bool,
    ) -> Result<Option<AgentMaterialization>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BeginAgentAssignment(
                event_id,
                profile,
                context_revision,
                preserve_wake_batch,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn ignore_assignment_event(&self, event_id: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::IgnoreAssignmentEvent(event_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn retire_unassigned_work_item(
        &self,
        event_id: String,
        debounce_seconds: u64,
    ) -> Result<UnassignmentOutcome, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RetireUnassignedWorkItem(event_id, debounce_seconds, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn finish_unassigned_work_item(&self, event_id: String) -> Result<bool, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::FinishUnassignedWorkItem(event_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn complete_agent_assignment(
        &self,
        materialization: AgentMaterialization,
        provider_session_id: String,
        binding_id: String,
        context_revision: String,
        instruction_revision: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::CompleteAgentAssignment(
                materialization,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn fail_agent_assignment(
        &self,
        assignment_id: String,
        error: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::FailAgentAssignment(assignment_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn defer_agent_assignment(&self, assignment: String, event: String, error: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::DeferAgentAssignment(assignment, event, error, reply)).map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn set_assignment_context_pressure(
        &self,
        assignment_id: String,
        pressure: String,
        bytes: Option<u64>,
        error: Option<String>,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::SetAssignmentContextPressure(
                assignment_id,
                pressure,
                bytes,
                error,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn claim_runnable_turn(
        &self,
        work_item_kind: String,
        profile_id: String,
        available_sessions: Vec<String>,
    ) -> Result<Option<TurnClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ClaimRunnableTurn(work_item_kind, profile_id, available_sessions, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    #[allow(clippy::too_many_arguments)]
    pub fn record_agent_worktree(
        &self,
        materialization: AgentMaterialization,
        repository_node_id: String,
        path: PathBuf,
        source_path: PathBuf,
        head_ref: String,
        local_branch: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RecordAgentWorktree(
                materialization,
                repository_node_id,
                path,
                source_path,
                head_ref,
                local_branch,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn mark_turn_started(
        &self,
        turn_id: String,
        provider_turn_id: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::MarkTurnStarted(turn_id, provider_turn_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn defer_unstarted_turn(&self, turn_id: String, reason: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::DeferUnstartedTurn(turn_id, reason, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn mark_turn_terminal(&self, turn_id: String, lifecycle: String, error: Option<String>) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::MarkTurnTerminal(turn_id, lifecycle, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn claim_running_input(&self, turn_id: String) -> Result<Option<TurnClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ClaimRunningInput(turn_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn consume_steer_batch(&self, turn_id: String, batch_id: String, event_ids: Vec<String>) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ConsumeSteerBatch(turn_id, batch_id, event_ids, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn enqueue_turn_reaction(
        &self,
        turn_id: String,
        content: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::EnqueueTurnReaction(turn_id, content, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn enqueue_operational_status(
        &self,
        turn_id: String,
        body: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::EnqueueOperationalStatus(turn_id, body, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn begin_context_reset(
        &self,
        active_turn_id: Option<String>,
        work_item_kind: String,
        profile_id: String,
    ) -> Result<Option<ContextResetClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::BeginContextReset(active_turn_id, work_item_kind, profile_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    /// Called once before this role owns any physical execution handles.
    pub fn recover_context_resets(&self, kind: String, profile: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::RecoverContextResets(kind, profile, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn ready_context_reset(
        &self,
        work_item_kind: String,
        profile_id: String,
    ) -> Result<Option<ContextResetClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::ReadyContextReset(work_item_kind, profile_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn refresh_context_reset(&self, reset_id: String) -> Result<ContextResetClaim, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::RefreshContextReset(reset_id, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn claim_context_reset_notice(
        &self, kind: String, profile: String, available_sessions: Vec<String>,
    ) -> Result<Option<TurnClaim>, StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::ClaimContextResetNotice(kind, profile, available_sessions, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn defer_context_reset_notice(
        &self, reset_id: String, turn_id: String, lifecycle: String, reason: Option<String>,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender.send(Command::DeferContextResetNotice(reset_id, turn_id, lifecycle, reason, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn mark_context_reset_turn_terminal(
        &self,
        reset_id: String,
        turn_id: String,
        lifecycle: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::MarkContextResetTurnTerminal(reset_id, turn_id, lifecycle, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn complete_context_reset(
        &self,
        reset_id: String,
        provider_session_id: String,
        binding_id: String,
        context_revision: String,
        instruction_revision: String,
    ) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::CompleteContextReset(
                reset_id,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                reply,
            ))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }

    pub fn fail_context_reset(&self, reset_id: String, error: String) -> Result<(), StoreError> {
        let (reply, receiver) = mpsc::channel();
        self.sender
            .send(Command::FailContextReset(reset_id, error, reply))
            .map_err(|_| StoreError::ActorUnavailable)?;
        receiver.recv().map_err(|_| StoreError::ActorStopped)?
    }
}

impl Drop for StoreActor {
    fn drop(&mut self) {
        let _ = self.sender.send(Command::Shutdown);
        if let Some(join) = self.join.take() {
            let _ = join.join();
        }
    }
}

enum Command {
    Plan(Sender<Result<MigrationPlan, StoreError>>),
    Apply(Sender<Result<MigrationResult, StoreError>>),
    Status(Sender<Result<StoreStatus, StoreError>>),
    ReconcileComments(CanonicalCommentSet, Sender<Result<Vec<DeletedComment>, StoreError>>),
    SetContextRevision(String, String, Sender<Result<(), StoreError>>),
    OperationalStatusCommentIds(String, Sender<Result<BTreeSet<String>, StoreError>>),
    ReconcileAssociations(AssociationSet, Sender<Result<(), StoreError>>),
    IngestEvent(Box<IngressEvent>, SchedulerPolicy, Sender<Result<IngestResult, StoreError>>),
    AdvanceScheduler(Sender<Result<u64, StoreError>>),
    RuntimeStatus(Sender<Result<RuntimeStoreStatus, StoreError>>),
    TrackedWorkItems(Sender<Result<Vec<TrackedWorkItem>, StoreError>>),
    CanonicalObjects(String, Sender<Result<Vec<CanonicalObjectState>, StoreError>>),
    BeginReconciliation(String, Sender<Result<ReconciliationRun, StoreError>>),
    FinishReconciliation(
        ReconciliationRun,
        &'static str,
        usize,
        usize,
        Option<String>,
        Sender<Result<(), StoreError>>,
    ),
    RegisterProfile(ProfileRecord, Sender<Result<(), StoreError>>),
    ProviderResumeCandidates(
        String,
        String,
        Sender<Result<Vec<ProviderResumeCandidate>, StoreError>>,
    ),
    BeginProviderReplacement(String, ProfileRecord, Sender<Result<Option<ContextResetClaim>, StoreError>>),
    PrepareOfflineResume(Sender<Result<Vec<String>, StoreError>>),
    ClearProviderBinding(String, Sender<Result<(), StoreError>>),
    FenceIdleProvider(String, Sender<Result<bool, StoreError>>),
    DeferAgentAssignment(String, String, String, Sender<Result<(), StoreError>>),
    RecordProviderResume(String, String, ProfileRecord, String, Sender<Result<(), StoreError>>),
    RecordProviderResumeError(String, String, Sender<Result<(), StoreError>>),
    BlockProviderSession(String, String, Sender<Result<(), StoreError>>),
    StoppingProviderSessions(String, String, Sender<Result<Vec<String>, StoreError>>),
    RetireStoppingProviderSession(String, Sender<Result<bool, StoreError>>),
    AssignmentCandidates(String, String, Sender<Result<Vec<AssignmentCandidate>, StoreError>>),
    WorkItemLifecycleCandidates(
        String,
        usize,
        Sender<Result<Vec<WorkItemLifecycleCandidate>, StoreError>>,
    ),
    PrepareWorkItemClosure(String, Sender<Result<bool, StoreError>>),
    BeginWorkItemReactivation(String, String, Sender<Result<Option<AgentMaterialization>, StoreError>>),
    CompleteWorkItemReactivation(
        String,
        AgentMaterialization,
        String,
        String,
        String,
        String,
        SchedulerPolicy,
        Sender<Result<(), StoreError>>,
    ),
    FailWorkItemReactivation(String, String, String, Sender<Result<(), StoreError>>),
    DeferWorkItemReactivation(String, String, String, Sender<Result<(), StoreError>>),
    HasLifecycleObservation(String, String, String, Sender<Result<bool, StoreError>>),
    BeginAgentAssignment(
        String,
        ProfileRecord,
        Option<String>,
        bool,
        Sender<Result<Option<AgentMaterialization>, StoreError>>,
    ),
    IgnoreAssignmentEvent(String, Sender<Result<(), StoreError>>),
    RetireUnassignedWorkItem(String, u64, Sender<Result<UnassignmentOutcome, StoreError>>),
    FinishUnassignedWorkItem(String, Sender<Result<bool, StoreError>>),
    CompleteAgentAssignment(
        AgentMaterialization,
        String,
        String,
        String,
        String,
        Sender<Result<(), StoreError>>,
    ),
    FailAgentAssignment(String, String, Sender<Result<(), StoreError>>),
    SetAssignmentContextPressure(
        String,
        String,
        Option<u64>,
        Option<String>,
        Sender<Result<(), StoreError>>,
    ),
    ClaimRunnableTurn(String, String, Vec<String>, Sender<Result<Option<TurnClaim>, StoreError>>),
    RecordAgentWorktree(
        AgentMaterialization,
        String,
        PathBuf,
        PathBuf,
        String,
        String,
        Sender<Result<(), StoreError>>,
    ),
    MarkTurnStarted(String, String, Sender<Result<(), StoreError>>),
    MarkTurnTerminal(String, String, Option<String>, Sender<Result<(), StoreError>>),
    DeferUnstartedTurn(String, String, Sender<Result<(), StoreError>>),
    ClaimRunningInput(String, Sender<Result<Option<TurnClaim>, StoreError>>),
    ConsumeSteerBatch(String, String, Vec<String>, Sender<Result<(), StoreError>>),
    EnqueueTurnReaction(String, String, Sender<Result<(), StoreError>>),
    EnqueueOperationalStatus(String, String, Sender<Result<(), StoreError>>),
    BeginContextReset(
        Option<String>,
        String,
        String,
        Sender<Result<Option<ContextResetClaim>, StoreError>>,
    ),
    RecoverContextResets(String, String, Sender<Result<(), StoreError>>),
    ReadyContextReset(String, String, Sender<Result<Option<ContextResetClaim>, StoreError>>),
    RefreshContextReset(String, Sender<Result<ContextResetClaim, StoreError>>),
    ClaimContextResetNotice(String, String, Vec<String>, Sender<Result<Option<TurnClaim>, StoreError>>),
    DeferContextResetNotice(String, String, String, Option<String>, Sender<Result<(), StoreError>>),
    MarkContextResetTurnTerminal(String, String, String, Sender<Result<(), StoreError>>),
    CompleteContextReset(String, String, String, String, String, Sender<Result<(), StoreError>>),
    FailContextReset(String, String, Sender<Result<(), StoreError>>),
    Shutdown,
}

#[derive(Debug)]
struct Migration {
    version: u32,
    name: &'static str,
    sql: &'static str,
}

#[derive(Debug)]
struct LedgerEntry {
    version: u32,
    checksum: String,
}

#[allow(clippy::too_many_lines)]
fn actor_loop(database: &Path, backups: &Path, receiver: Receiver<Command>) {
    for command in receiver {
        match command {
            Command::Plan(reply) => {
                let _ = reply.send(plan(database));
            }
            Command::Apply(reply) => {
                let _ = reply.send(apply(database, backups));
            }
            Command::Status(reply) => {
                let _ = reply.send(status(database));
            }
            Command::ReconcileComments(update, reply) => {
                let _ = reply.send(reconcile_comments(database, &update));
            }
            Command::SetContextRevision(work_item_node_id, revision, reply) => {
                let _ = reply.send(set_context_revision(database, &work_item_node_id, &revision));
            }
            Command::OperationalStatusCommentIds(work_item_node_id, reply) => {
                let _ = reply.send(operational_status_comment_ids(database, &work_item_node_id));
            }
            Command::ReconcileAssociations(update, reply) => {
                let _ = reply.send(reconcile_associations(database, &update));
            }
            Command::IngestEvent(event, policy, reply) => {
                let _ = reply.send(ingest_event(database, &event, policy));
            }
            Command::AdvanceScheduler(reply) => {
                let _ = reply.send(advance_scheduler(database));
            }
            Command::RuntimeStatus(reply) => {
                let _ = reply.send(runtime_status(database));
            }
            Command::TrackedWorkItems(reply) => {
                let _ = reply.send(tracked_work_items(database));
            }
            Command::CanonicalObjects(work_item_node_id, reply) => {
                let _ = reply.send(canonical_objects(database, &work_item_node_id));
            }
            Command::BeginReconciliation(repository_node_id, reply) => {
                let _ = reply.send(begin_reconciliation(database, &repository_node_id));
            }
            Command::FinishReconciliation(
                run,
                lifecycle,
                work_item_count,
                change_count,
                error,
                reply,
            ) => {
                let _ = reply.send(finish_reconciliation(
                    database,
                    &run,
                    lifecycle,
                    work_item_count,
                    change_count,
                    error.as_deref(),
                ));
            }
            Command::RegisterProfile(profile, reply) => {
                let _ = reply.send(register_profile(database, &profile));
            }
            Command::ProviderResumeCandidates(profile_id, work_item_kind, reply) => {
                let _ =
                    reply.send(provider_resume_candidates(database, &profile_id, &work_item_kind));
            }
            Command::BeginProviderReplacement(provider_session_id, profile, reply) => {
                let _ = reply.send(begin_provider_replacement(database, &provider_session_id, &profile));
            }
            Command::PrepareOfflineResume(reply) => {
                let _ = reply.send(prepare_offline_resume(database));
            }
            Command::ClearProviderBinding(provider_session_id, reply) => {
                let _ = reply.send(clear_provider_binding(database, &provider_session_id));
            }
            Command::FenceIdleProvider(provider_session_id, reply) => {
                let _ = reply.send(fence_idle_provider(database, &provider_session_id));
            }
            Command::DeferAgentAssignment(assignment, event, error, reply) => {
                let _ = reply.send(defer_agent_assignment(database, &assignment, &event, &error));
            }
            Command::RecordProviderResume(provider_session_id, binding_id, profile, instruction_revision, reply) => {
                let _ = reply.send(record_provider_resume(database, &provider_session_id, &binding_id, &profile, &instruction_revision));
            }
            Command::RecordProviderResumeError(provider_session_id, error, reply) => {
                let result = (|| {
                    let connection = open_read_write(database)?;
                    configure_connection(&connection)?;
                    connection.execute("UPDATE provider_sessions SET last_resume_error=?2,last_resume_failed_at=?3 WHERE provider_session_id=?1",
                        params![provider_session_id,error,now_rfc3339()])?;
                    Ok(())
                })();
                let _ = reply.send(result);
            }
            Command::BlockProviderSession(provider_session_id, error, reply) => {
                let _ = reply.send(block_provider_session(database, &provider_session_id, &error));
            }
            Command::StoppingProviderSessions(profile_id, work_item_kind, reply) => {
                let _ =
                    reply.send(stopping_provider_sessions(database, &profile_id, &work_item_kind));
            }
            Command::RetireStoppingProviderSession(provider_session_id, reply) => {
                let _ =
                    reply.send(retire_stopping_provider_session(database, &provider_session_id));
            }
            Command::AssignmentCandidates(work_item_kind, profile_id, reply) => {
                let _ = reply.send(assignment_candidates(database, &work_item_kind, &profile_id));
            }
            Command::WorkItemLifecycleCandidates(work_item_kind, limit, reply) => {
                let _ =
                    reply.send(work_item_lifecycle_candidates(database, &work_item_kind, limit));
            }
            Command::PrepareWorkItemClosure(event_id, reply) => {
                let _ = reply.send(prepare_work_item_closure(database, &event_id));
            }
            Command::BeginWorkItemReactivation(event_id, profile_id, reply) => {
                let _ = reply.send(begin_work_item_reactivation(database, &event_id, &profile_id));
            }
            Command::CompleteWorkItemReactivation(
                event_id,
                materialization,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                policy,
                reply,
            ) => {
                let _ = reply.send(complete_work_item_reactivation(
                    database,
                    &event_id,
                    &materialization,
                    &provider_session_id,
                    &binding_id,
                    &context_revision,
                    &instruction_revision,
                    policy,
                ));
            }
            Command::FailWorkItemReactivation(event_id, assignment_id, error, reply) => {
                let _ = reply.send(fail_work_item_reactivation(
                    database,
                    &event_id,
                    &assignment_id,
                    &error,
                ));
            }
            Command::DeferWorkItemReactivation(event_id, assignment_id, error, reply) => {
                let _ = reply.send(defer_work_item_reactivation(database, &event_id, &assignment_id, &error));
            }
            Command::HasLifecycleObservation(work_item_node_id, action, object_version, reply) => {
                let _ = reply.send(has_lifecycle_observation(
                    database,
                    &work_item_node_id,
                    &action,
                    &object_version,
                ));
            }
            Command::BeginAgentAssignment(
                event_id,
                profile,
                context_revision,
                preserve_wake_batch,
                reply,
            ) => {
                let _ = reply.send(begin_agent_assignment(
                    database,
                    &event_id,
                    &profile,
                    context_revision.as_deref(),
                    preserve_wake_batch,
                ));
            }
            Command::IgnoreAssignmentEvent(event_id, reply) => {
                let _ = reply.send(ignore_assignment_event(database, &event_id));
            }
            Command::RetireUnassignedWorkItem(event_id, debounce_seconds, reply) => {
                let _ =
                    reply.send(retire_unassigned_work_item(database, &event_id, debounce_seconds));
            }
            Command::FinishUnassignedWorkItem(event_id, reply) => {
                let _ = reply.send(finish_unassigned_work_item(database, &event_id));
            }
            Command::CompleteAgentAssignment(
                materialization,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                reply,
            ) => {
                let _ = reply.send(complete_agent_assignment(
                    database,
                    &materialization,
                    &provider_session_id,
                    &binding_id,
                    &context_revision,
                    &instruction_revision,
                ));
            }
            Command::FailAgentAssignment(assignment_id, error, reply) => {
                let _ = reply.send(fail_agent_assignment(database, &assignment_id, &error));
            }
            Command::SetAssignmentContextPressure(assignment_id, pressure, bytes, error, reply) => {
                let _ = reply.send(set_assignment_context_pressure(
                    database,
                    &assignment_id,
                    &pressure,
                    bytes,
                    error.as_deref(),
                ));
            }
            Command::ClaimRunnableTurn(work_item_kind, profile_id, available_sessions, reply) => {
                let _ = reply.send(claim_runnable_turn(
                    database,
                    &work_item_kind,
                    &profile_id,
                    &available_sessions,
                ));
            }
            Command::RecordAgentWorktree(
                materialization,
                repository_node_id,
                path,
                source_path,
                head_ref,
                local_branch,
                reply,
            ) => {
                let _ = reply.send(record_agent_worktree(
                    database,
                    &materialization,
                    &repository_node_id,
                    &path,
                    &source_path,
                    &head_ref,
                    &local_branch,
                ));
            }
            Command::MarkTurnStarted(turn_id, provider_turn_id, reply) => {
                let _ = reply.send(mark_turn_started(database, &turn_id, &provider_turn_id));
            }
            Command::DeferUnstartedTurn(turn_id, reason, reply) => {
                let _ = reply.send(defer_unstarted_turn(database, &turn_id, &reason));
            }
            Command::MarkTurnTerminal(turn_id, lifecycle, error, reply) => {
                let _ = reply.send(mark_turn_terminal(database, &turn_id, &lifecycle, error.as_deref()));
            }
            Command::ClaimRunningInput(turn_id, reply) => {
                let _ = reply.send(claim_running_input(database, &turn_id));
            }
            Command::ConsumeSteerBatch(turn_id, batch_id, event_ids, reply) => {
                let _ = reply.send(consume_steer_batch(database, &turn_id, &batch_id, &event_ids));
            }
            Command::EnqueueTurnReaction(turn_id, content, reply) => {
                let _ = reply.send(enqueue_turn_reaction(database, &turn_id, &content));
            }
            Command::EnqueueOperationalStatus(turn_id, body, reply) => {
                let _ = reply.send(enqueue_operational_status(database, &turn_id, &body));
            }
            Command::BeginContextReset(active_turn_id, work_item_kind, profile_id, reply) => {
                let _ = reply.send(begin_context_reset(
                    database,
                    active_turn_id.as_deref(),
                    &work_item_kind,
                    &profile_id,
                ));
            }
            Command::RecoverContextResets(kind, profile, reply) => {
                let _ = reply.send(recover_context_resets(database, &kind, &profile));
            }
            Command::ReadyContextReset(work_item_kind, profile_id, reply) => {
                let _ = reply.send(ready_context_reset(database, &work_item_kind, &profile_id));
            }
            Command::RefreshContextReset(reset_id, reply) => {
                let _ = reply.send(refresh_context_reset(database, &reset_id));
            }
            Command::ClaimContextResetNotice(kind, profile, available_sessions, reply) => {
                let _ = reply.send(claim_context_reset_notice(database, &kind, &profile, &available_sessions));
            }
            Command::DeferContextResetNotice(reset_id, turn_id, lifecycle, reason, reply) => {
                let _ = reply.send(defer_context_reset_notice(database, &reset_id, &turn_id, &lifecycle, reason.as_deref()));
            }
            Command::MarkContextResetTurnTerminal(reset_id, turn_id, lifecycle, reply) => {
                let _ = reply.send(mark_context_reset_turn_terminal(
                    database, &reset_id, &turn_id, &lifecycle,
                ));
            }
            Command::CompleteContextReset(
                reset_id,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                reply,
            ) => {
                let _ = reply.send(complete_context_reset(
                    database,
                    &reset_id,
                    &provider_session_id,
                    &binding_id,
                    &context_revision,
                    &instruction_revision,
                ));
            }
            Command::FailContextReset(reset_id, error, reply) => {
                let _ = reply.send(fail_context_reset(database, &reset_id, &error));
            }
            Command::Shutdown => break,
        }
    }
}

fn plan(database: &Path) -> Result<MigrationPlan, StoreError> {
    let ledger = read_ledger(database)?;
    validate_ledger(&ledger)?;
    let current_schema = ledger.last().map_or(0, |entry| entry.version);
    Ok(MigrationPlan {
        database: database.to_path_buf(),
        current_schema,
        supported_schema: DATABASE_SCHEMA_VERSION,
        pending: MIGRATIONS
            .iter()
            .filter(|migration| migration.version > current_schema)
            .map(|migration| PendingMigration {
                version: migration.version,
                name: migration.name,
                checksum: migration_checksum(migration),
            })
            .collect(),
    })
}

fn apply(database: &Path, backups: &Path) -> Result<MigrationResult, StoreError> {
    if let Some(parent) = database.parent() {
        create_dir_all(parent)?;
    }
    create_dir_all(backups)?;
    let _lease = MigrationLease::acquire(database)?;

    let before = plan(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    // Journal mode is a database-level setting. Set it before workers and CLI
    // clients start, rather than contending for it on every store operation.
    connection.execute_batch("PRAGMA journal_mode=WAL;")?;
    if before.pending.is_empty() {
        return Ok(MigrationResult {
            previous_schema: before.current_schema,
            current_schema: before.current_schema,
            applied: Vec::new(),
            backup: None,
        });
    }

    let existed_with_bytes = fs::metadata(database).is_ok_and(|metadata| metadata.len() > 0);
    let backup = if existed_with_bytes {
        Some(create_backup(&connection, backups, before.pending[0].version)?)
    } else {
        None
    };

    let mut applied = Vec::new();
    for migration in MIGRATIONS.iter().filter(|migration| migration.version > before.current_schema)
    {
        apply_one(&mut connection, migration)?;
        applied.push(migration.version);
    }
    let after = plan(database)?;
    Ok(MigrationResult {
        previous_schema: before.current_schema,
        current_schema: after.current_schema,
        applied,
        backup,
    })
}

fn status(database: &Path) -> Result<StoreStatus, StoreError> {
    let exists = database.is_file();
    let bytes = fs::metadata(database).map_or(0, |metadata| metadata.len());
    let migration_plan = plan(database)?;
    let journal_mode = if exists && bytes > 0 {
        let connection = open_read_only(database)?;
        connection.query_row("PRAGMA journal_mode", [], |row| row.get::<_, String>(0)).optional()?
    } else {
        None
    };
    Ok(StoreStatus {
        database: database.to_path_buf(),
        exists,
        bytes,
        schema_version: migration_plan.current_schema,
        supported_schema: DATABASE_SCHEMA_VERSION,
        pending_migrations: migration_plan.pending.len(),
        journal_mode,
    })
}

#[derive(Debug)]
struct ExistingComment {
    node_id: String,
}

#[allow(clippy::too_many_lines)]
fn reconcile_comments(
    database: &Path,
    update: &CanonicalCommentSet,
) -> Result<Vec<DeletedComment>, StoreError> {
    require_current_schema(database)?;
    let number = i64::try_from(update.work_item_number).map_err(|_| {
        StoreError::InvalidData("GitHub work-item number exceeds SQLite INTEGER".into())
    })?;
    let observed_at = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction()?;
    transaction.execute(
        "INSERT INTO repositories(node_id, name_with_owner, observed_at)
         VALUES (?1, ?2, ?3)
         ON CONFLICT(node_id) DO UPDATE SET
           name_with_owner=excluded.name_with_owner,
           observed_at=excluded.observed_at",
        params![update.repository_node_id, update.repository, observed_at],
    )?;
    transaction.execute(
        "INSERT INTO work_items(node_id, repository_node_id, kind, number, state, observed_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6)
         ON CONFLICT(node_id) DO UPDATE SET
           repository_node_id=excluded.repository_node_id,
           kind=excluded.kind,
           number=excluded.number,
           state=CASE
             WHEN lower(work_items.state)='merged' AND lower(excluded.state)='closed' THEN work_items.state
             ELSE excluded.state
           END,
           observed_at=excluded.observed_at",
        params![
            update.work_item_node_id,
            update.repository_node_id,
            update.work_item_kind,
            number,
            update.work_item_state,
            observed_at,
        ],
    )?;
    transaction.execute(
        "INSERT INTO canonical_objects(
           node_id, work_item_node_id, object_kind, version, digest, lifecycle,
           observed_at, reference_repository, reference_number
         ) VALUES (?1,?1,?2,?3,?4,'active',?5,?6,?7)
         ON CONFLICT(node_id) DO UPDATE SET
           work_item_node_id=excluded.work_item_node_id,
           object_kind=excluded.object_kind,
           version=excluded.version,
           digest=excluded.digest,
           lifecycle='active',
           observed_at=excluded.observed_at,
           reference_repository=excluded.reference_repository,
           reference_number=excluded.reference_number",
        params![
            update.work_item_node_id,
            update.work_item_kind,
            update.work_item_version,
            update.work_item_digest,
            observed_at,
            update.repository,
            number,
        ],
    )?;

    let previous = {
        let mut statement = transaction.prepare(
            "SELECT node_id
             FROM canonical_objects
             WHERE work_item_node_id=?1 AND object_kind=?2 AND lifecycle != 'deleted'",
        )?;
        let rows = statement
            .query_map(params![update.work_item_node_id, update.object_kind], |row| {
                Ok(ExistingComment { node_id: row.get(0)? })
            })?;
        rows.collect::<Result<Vec<_>, _>>()?
    };
    let current_ids =
        update.comments.iter().map(|comment| comment.node_id.as_str()).collect::<BTreeSet<_>>();
    for comment in &update.comments {
        transaction.execute(
            "INSERT INTO canonical_objects(
               node_id, work_item_node_id, object_kind, version, digest, lifecycle,
               author_node_id, created_at, updated_at, observed_at,
               database_id, author_login, reference_repository, reference_number, pinned
             ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15)
             ON CONFLICT(node_id) DO UPDATE SET
               work_item_node_id=excluded.work_item_node_id,
               object_kind=excluded.object_kind,
               version=excluded.version,
               digest=excluded.digest,
               lifecycle=excluded.lifecycle,
               author_node_id=excluded.author_node_id,
               created_at=excluded.created_at,
               updated_at=excluded.updated_at,
               observed_at=excluded.observed_at,
               database_id=excluded.database_id,
               author_login=excluded.author_login,
               reference_repository=excluded.reference_repository,
               reference_number=excluded.reference_number,
               pinned=excluded.pinned",
            params![
                comment.node_id,
                update.work_item_node_id,
                comment.object_kind,
                comment.version,
                comment.digest,
                comment.lifecycle,
                comment.author_node_id,
                comment.created_at,
                comment.updated_at,
                observed_at,
                comment.database_id,
                comment.author_login,
                update.repository,
                number,
                i64::from(comment.pinned),
            ],
        )?;
    }
    for comment in previous {
        if !current_ids.contains(comment.node_id.as_str()) {
            transaction.execute(
                "UPDATE canonical_objects
                 SET lifecycle='deleted', version=?2, observed_at=?2
                 WHERE node_id=?1",
                params![comment.node_id, observed_at],
            )?;
        }
    }
    let deleted = {
        let mut statement = transaction.prepare(
            "SELECT node_id, database_id, author_node_id, author_login, created_at, updated_at, pinned
             FROM canonical_objects
             WHERE work_item_node_id=?1 AND object_kind=?2 AND lifecycle='deleted'
             ORDER BY created_at, node_id",
        )?;
        let rows =
            statement.query_map(params![update.work_item_node_id, update.object_kind], |row| {
                Ok(DeletedComment {
                    node_id: row.get(0)?,
                    database_id: row.get::<_, Option<String>>(1)?.unwrap_or_default(),
                    author_node_id: row.get(2)?,
                    author_login: row.get(3)?,
                    created_at: row.get::<_, Option<String>>(4)?.unwrap_or_default(),
                    updated_at: row.get::<_, Option<String>>(5)?.unwrap_or_default(),
                    pinned: row.get::<_, i64>(6)? != 0,
                })
            })?;
        rows.collect::<Result<Vec<_>, _>>()?
    };
    transaction.commit()?;
    Ok(deleted)
}

fn set_context_revision(
    database: &Path,
    work_item_node_id: &str,
    revision: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let updated = connection.execute(
        "UPDATE work_items SET context_revision=?2, observed_at=?3 WHERE node_id=?1",
        params![work_item_node_id, revision, now_rfc3339()],
    )?;
    if updated == 1 {
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!(
            "cannot record Context Revision for unknown Work Item {work_item_node_id}"
        )))
    }
}

fn operational_status_comment_ids(
    database: &Path,
    work_item_node_id: &str,
) -> Result<BTreeSet<String>, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "SELECT remote_comment_node_id
         FROM status_comments
         WHERE work_item_node_id=?1 AND remote_comment_node_id IS NOT NULL AND lifecycle != 'deleted'",
    )?;
    let rows = statement.query_map([work_item_node_id], |row| row.get::<_, String>(0))?;
    rows.collect::<Result<BTreeSet<_>, _>>().map_err(StoreError::from)
}

#[allow(clippy::too_many_lines)]
fn reconcile_associations(database: &Path, update: &AssociationSet) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let observed_at = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction()?;
    let mut active_pairs = BTreeSet::new();
    for related in &update.related {
        let number = i64::try_from(related.number).map_err(|_| {
            StoreError::InvalidData(
                "GitHub associated Work Item number exceeds SQLite INTEGER".into(),
            )
        })?;
        transaction.execute(
            "INSERT INTO repositories(node_id, name_with_owner, observed_at)
             VALUES (?1,?2,?3)
             ON CONFLICT(node_id) DO UPDATE SET
               name_with_owner=excluded.name_with_owner,
               observed_at=excluded.observed_at",
            params![related.repository_node_id, related.repository, observed_at],
        )?;
        transaction.execute(
            "INSERT INTO work_items(node_id, repository_node_id, kind, number, state, observed_at)
             VALUES (?1,?2,?3,?4,?5,?6)
             ON CONFLICT(node_id) DO UPDATE SET
               repository_node_id=excluded.repository_node_id,
               kind=excluded.kind,
               number=excluded.number,
               state=CASE
                 WHEN lower(work_items.state)='merged' AND lower(excluded.state)='closed' THEN work_items.state
                 ELSE excluded.state
               END,
               observed_at=excluded.observed_at",
            params![
                related.node_id,
                related.repository_node_id,
                related.kind,
                number,
                related.state,
                observed_at,
            ],
        )?;
        let (issue_node_id, pr_node_id) = if update.anchor_kind == "issue" {
            (update.anchor_node_id.as_str(), related.node_id.as_str())
        } else {
            (related.node_id.as_str(), update.anchor_node_id.as_str())
        };
        active_pairs.insert((issue_node_id.to_owned(), pr_node_id.to_owned()));
        let issue_visible_description = if update.anchor_kind == "issue" {
            update.anchor_visible_description.as_deref()
        } else {
            related.visible_description.as_deref()
        };
        transaction.execute(
            "INSERT INTO associations(issue_node_id,pr_node_id,source,observed_version,active)
             VALUES (?1,?2,'native',?3,1)
             ON CONFLICT(issue_node_id,pr_node_id) DO UPDATE SET
               source='native',
               observed_version=excluded.observed_version,
               active=1",
            params![issue_node_id, pr_node_id, update.observed_version],
        )?;
        if let Some(visible_description) = issue_visible_description {
            transaction.execute(
                "INSERT OR IGNORE INTO issue_context_sources(
                   issue_node_id,visible_description,observed_at
                 ) VALUES (?1,?2,?3)",
                params![issue_node_id, visible_description, observed_at],
            )?;
        }
    }
    let anchor_column = if update.anchor_kind == "issue" { "issue_node_id" } else { "pr_node_id" };
    let query = format!(
        "SELECT issue_node_id, pr_node_id FROM associations WHERE {anchor_column}=?1 AND active=1"
    );
    let prior = {
        let mut statement = transaction.prepare(&query)?;
        let rows = statement.query_map([&update.anchor_node_id], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?))
        })?;
        rows.collect::<Result<Vec<_>, _>>()?
    };
    for pair in prior {
        if !active_pairs.contains(&pair) {
            transaction.execute(
                "UPDATE associations
                 SET active=0, observed_version=?3
                 WHERE issue_node_id=?1 AND pr_node_id=?2",
                params![pair.0, pair.1, update.observed_version],
            )?;
        }
    }
    transaction.commit()?;
    Ok(())
}

#[allow(clippy::too_many_lines)]
fn ingest_event(
    database: &Path,
    event: &IngressEvent,
    policy: SchedulerPolicy,
) -> Result<IngestResult, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction()?;
    let result = ingest_event_transaction(&transaction, event, policy)?;
    transaction.commit()?;
    Ok(result)
}

pub(crate) fn ingest_event_transaction(
    transaction: &rusqlite::Transaction<'_>,
    event: &IngressEvent,
    policy: SchedulerPolicy,
) -> Result<IngestResult, StoreError> {
    let now = now_rfc3339();
    let duplicate = transaction
        .query_row(
            "SELECT 1 FROM deliveries WHERE delivery_guid=?1",
            [&event.delivery_guid],
            |_| Ok(()),
        )
        .optional()?
        .is_some();
    if duplicate {
        transaction.execute(
            "UPDATE deliveries SET duplicate_count=duplicate_count+1 WHERE delivery_guid=?1",
            [&event.delivery_guid],
        )?;
        return Ok(IngestResult {
            duplicate: true,
            delivery_guid: event.delivery_guid.clone(),
            event_id: None,
            event_lifecycle: None,
            batch_id: None,
            batch_lifecycle: None,
        });
    }

    transaction.execute(
        "INSERT INTO repositories(node_id,name_with_owner,observed_at)
         VALUES (?1,?2,?3)
         ON CONFLICT(node_id) DO UPDATE SET
           name_with_owner=excluded.name_with_owner,
           observed_at=excluded.observed_at",
        params![event.repository_node_id, event.repository, now],
    )?;
    if let (Some(node_id), Some(kind), Some(number), Some(state)) = (
        event.work_item_node_id.as_deref(),
        event.work_item_kind,
        event.work_item_number,
        event.work_item_state.as_deref(),
    ) {
        let number = sqlite_u64(number, "GitHub work-item number")?;
        transaction.execute(
            "INSERT INTO work_items(node_id,repository_node_id,kind,number,state,observed_at)
             VALUES (?1,?2,?3,?4,?5,?6)
             ON CONFLICT(node_id) DO UPDATE SET
               repository_node_id=excluded.repository_node_id,
               kind=excluded.kind,
               number=excluded.number,
               state=CASE
                 WHEN lower(work_items.state)='merged' AND lower(excluded.state)='closed' THEN work_items.state
                 ELSE excluded.state
               END,
               observed_at=excluded.observed_at",
            params![node_id, event.repository_node_id, kind, number, state, now],
        )?;
    }
    transaction.execute(
        "INSERT INTO deliveries(
           delivery_guid,repository_node_id,event_name,action,received_at,admitted_at,
           repository_name,object_node_id,actor_node_id,actor_login,raw_payload,known
         ) VALUES (?1,?2,?3,?4,?5,?5,?6,?7,?8,?9,?10,?11)",
        params![
            event.delivery_guid,
            event.repository_node_id,
            event.event_name,
            event.action,
            now,
            event.repository,
            event.object_node_id,
            event.actor_node_id,
            event.actor_login,
            event.raw_payload,
            i64::from(event.known),
        ],
    )?;

    let event_id = Uuid::now_v7().to_string();
    let dedupe_key = event_dedupe_key(event);
    let object_kind = event_object_kind(event);
    let stale = match (
        object_kind,
        event.object_node_id.as_deref(),
        event.object_version.as_deref(),
        event.object_digest.as_deref(),
    ) {
        (Some(object_kind), Some(node_id), Some(version), Some(digest)) => transaction
            .query_row(
                "SELECT version,digest FROM canonical_objects WHERE node_id=?1",
                [node_id],
                |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
            )
            .optional()?
            .is_some_and(|(canonical_version, canonical_digest)| {
                let duplicate = canonical_version == version && canonical_digest == digest;
                if object_kind == "review_thread" {
                    duplicate
                } else {
                    canonical_version.as_str() > version || duplicate
                }
            }),
        _ => false,
    };
    let lifecycle = if stale {
        "superseded"
    } else if event.kind.consumed_at_ingest() {
        "consumed"
    } else {
        "pending"
    };
    let inserted = transaction.execute(
        "INSERT OR IGNORE INTO events(
           event_id,delivery_guid,work_item_node_id,object_node_id,object_version,
           kind,detail,origin,reference,lifecycle,observed_at,dedupe_key,
           mention_candidate,trusted_mention,body_digest
         ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,NULL,?14)",
        params![
            event_id,
            event.delivery_guid,
            event.work_item_node_id,
            event.object_node_id,
            event.object_version,
            event.kind.as_str(),
            event.detail,
            event.origin,
            event.reference,
            lifecycle,
            now,
            dedupe_key,
            i64::from(event.mention_candidate),
            event.object_digest,
        ],
    )?;
    if inserted == 0 {
        return Ok(IngestResult {
            duplicate: false,
            delivery_guid: event.delivery_guid.clone(),
            event_id: None,
            event_lifecycle: Some("superseded".into()),
            batch_id: None,
            batch_lifecycle: None,
        });
    }

    if !stale
        && let (
            Some(object_kind),
            Some(node_id),
            Some(work_item_node_id),
            Some(version),
            Some(digest),
        ) = (
            object_kind,
            event.object_node_id.as_deref(),
            event.work_item_node_id.as_deref(),
            event.object_version.as_deref(),
            event.object_digest.as_deref(),
        )
    {
        let lifecycle = match event.action.as_deref() {
            Some("deleted") => "deleted",
            Some("minimized") => "minimized",
            Some("dismissed") => "dismissed",
            Some("resolved") => "resolved",
            _ => "active",
        };
        transaction.execute(
            "INSERT INTO canonical_objects(
               node_id,work_item_node_id,object_kind,version,digest,lifecycle,observed_at
             ) VALUES (?1,?2,?3,?4,?5,?6,?7)
             ON CONFLICT(node_id) DO UPDATE SET
               work_item_node_id=excluded.work_item_node_id,
               object_kind=excluded.object_kind,
               version=excluded.version,
               digest=CASE
                 WHEN excluded.object_kind IN ('issue','pr') AND ?8=0
                   THEN canonical_objects.digest
                 ELSE excluded.digest
               END,
               lifecycle=excluded.lifecycle,
               observed_at=excluded.observed_at",
            params![
                node_id,
                work_item_node_id,
                object_kind,
                version,
                digest,
                lifecycle,
                now,
                i64::from(event.delivery_guid.starts_with("reconcile-")),
            ],
        )?;
    }

    let mut batch = None;
    if lifecycle == "pending"
        && let Some(work_item_node_id) = event.work_item_node_id.as_deref()
    {
        // PR activation (`braid pr create`) wakes the new group urgently;
        // native Issue assignment creates an idle session and no turn.
        let activation = event.kind == EventKind::Assign;
        let active_contact = event.kind == EventKind::Mention
            && event.detail.as_deref() == Some("direct_contact")
            && transaction.query_row(
                "SELECT EXISTS(SELECT 1 FROM assignments
                 WHERE work_item_node_id=?1 AND lifecycle IN ('active','finalizing'))",
                [work_item_node_id],
                |row| row.get::<_, bool>(0),
            )?;
        if event.kind == EventKind::Wake || activation || active_contact {
            batch = Some(schedule_event(
                &transaction,
                work_item_node_id,
                &event_id,
                policy,
                activation,
                &now,
            )?);
        }
    }
    if lifecycle == "pending"
        && let Some(target) = &event.reaction_target
    {
        enqueue_reaction(&transaction, event, &event_id, target, &now)?;
    }
    if lifecycle == "pending" && event.cross_surface_invalidation && event.origin != "agent" {
        schedule_cross_surface_invalidations(&transaction, event, &event_id, policy, &now)?;
    }
    Ok(IngestResult {
        duplicate: false,
        delivery_guid: event.delivery_guid.clone(),
        event_id: Some(event_id),
        event_lifecycle: Some(lifecycle.into()),
        batch_id: batch.as_ref().map(|value| value.0.clone()),
        batch_lifecycle: batch.map(|value| value.1),
    })
}

fn schedule_cross_surface_invalidations(
    transaction: &rusqlite::Transaction<'_>,
    source: &IngressEvent,
    source_event_id: &str,
    policy: SchedulerPolicy,
    now: &str,
) -> Result<(), StoreError> {
    if source.event_name != "issues"
        || source.action.as_deref() != Some("edited")
        || source.work_item_kind != Some("issue")
        || !source
            .work_item_state
            .as_deref()
            .is_some_and(|state| state.eq_ignore_ascii_case("open"))
    {
        return Ok(());
    }
    let Some(issue_node_id) = source.work_item_node_id.as_deref() else {
        return Ok(());
    };
    let Some(visible_description) = source.visible_body.as_deref() else {
        return Ok(());
    };
    let previous = transaction
        .query_row(
            "SELECT visible_description FROM issue_context_sources WHERE issue_node_id=?1",
            [issue_node_id],
            |row| row.get::<_, String>(0),
        )
        .optional()?;
    let changed =
        previous.as_deref().map_or(source.origin == "external", |body| body != visible_description);
    let targets = {
        let mut statement = transaction.prepare(
            "SELECT pr.node_id,r.name_with_owner,pr.number
             FROM associations edge
             JOIN work_items pr ON pr.node_id=edge.pr_node_id AND pr.kind='pr'
             JOIN repositories r ON r.node_id=pr.repository_node_id
             JOIN assignments a ON a.work_item_node_id=pr.node_id AND a.lifecycle='active'
             WHERE edge.issue_node_id=?1 AND edge.active=1 AND lower(pr.state)='open'
             ORDER BY r.name_with_owner,pr.number",
        )?;
        statement
            .query_map([issue_node_id], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, i64>(2)?))
            })?
            .collect::<Result<Vec<_>, _>>()?
    };
    for (pr_node_id, repository, number) in targets.into_iter().filter(|_| changed) {
        let event_id = Uuid::now_v7().to_string();
        let dedupe_key = hex::encode(Sha256::digest(
            format!("braid-cross-surface-v1\0{source_event_id}\0{pr_node_id}").as_bytes(),
        ));
        let reference = format!(
            "Associated Issue description changed for GitHub PR {repository}#{number}: {}",
            source.reference
        );
        let inserted = transaction.execute(
            "INSERT OR IGNORE INTO events(
               event_id,delivery_guid,work_item_node_id,object_node_id,object_version,
               kind,detail,origin,reference,lifecycle,observed_at,dedupe_key,
               mention_candidate,trusted_mention,body_digest
             ) VALUES (?1,?2,?3,?4,?5,'invalidate','cross_surface',?6,?7,'pending',?8,?9,0,0,?10)",
            params![
                event_id,
                source.delivery_guid,
                pr_node_id,
                source.object_node_id,
                source.object_version,
                source.origin,
                reference,
                now,
                dedupe_key,
                source.object_digest,
            ],
        )?;
        if inserted == 1 {
            schedule_event(transaction, &pr_node_id, &event_id, policy, false, now)?;
        }
    }
    transaction.execute(
        "INSERT INTO issue_context_sources(issue_node_id,visible_description,observed_at)
         VALUES (?1,?2,?3)
         ON CONFLICT(issue_node_id) DO UPDATE SET
           visible_description=excluded.visible_description,
           observed_at=excluded.observed_at",
        params![issue_node_id, visible_description, now],
    )?;
    Ok(())
}

fn event_object_kind(event: &IngressEvent) -> Option<&'static str> {
    match event.event_name.as_str() {
        "issues" => Some("issue"),
        "pull_request" => Some("pr"),
        "issue_comment" if event.work_item_kind == Some("pr") => Some("pr_comment"),
        "issue_comment" => Some("issue_comment"),
        "pull_request_review" => Some("review"),
        "pull_request_review_comment" => Some("review_comment"),
        "pull_request_review_thread" => Some("review_thread"),
        _ => None,
    }
}

fn event_dedupe_key(event: &IngressEvent) -> String {
    let mut digest = Sha256::new();
    for value in [
        event.repository_node_id.as_str(),
        event.object_node_id.as_deref().unwrap_or(""),
        event.object_version.as_deref().unwrap_or(""),
        event.object_digest.as_deref().unwrap_or(""),
        event.action.as_deref().unwrap_or(""),
        event.kind.as_str(),
    ] {
        digest.update(value.as_bytes());
        digest.update([0]);
    }
    hex::encode(digest.finalize())
}

fn enqueue_reaction(
    transaction: &rusqlite::Transaction<'_>,
    event: &IngressEvent,
    event_id: &str,
    target: &ReactionTarget,
    now: &str,
) -> Result<(), StoreError> {
    let operation = "reaction_add";
    let content = "eyes";
    let request_digest = hex::encode(Sha256::digest(
        format!("{}\0{}\0{}\0{content}", event.repository, target.kind, target.database_id)
            .as_bytes(),
    ));
    transaction.execute(
        "INSERT OR IGNORE INTO github_write_outbox(
           intent_id,event_id,repository,target_kind,target_database_id,operation,content,
           request_digest,lifecycle,next_attempt_at,created_at,updated_at
         ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,'pending',?9,?9,?9)",
        params![
            Uuid::now_v7().to_string(),
            event_id,
            event.repository,
            target.kind,
            target.database_id,
            operation,
            content,
            request_digest,
            now,
        ],
    )?;
    Ok(())
}

pub(crate) fn schedule_event(
    transaction: &rusqlite::Transaction<'_>,
    work_item_node_id: &str,
    event_id: &str,
    policy: SchedulerPolicy,
    urgent: bool,
    now: &str,
) -> Result<(String, String), StoreError> {
    let open = transaction
        .query_row(
            "SELECT batch_id,event_count,lifecycle
             FROM wake_batches
             WHERE work_item_node_id=?1 AND lifecycle IN ('pending','runnable')",
            [work_item_node_id],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?, row.get::<_, String>(2)?)),
        )
        .optional()?;
    let created = open.is_none();
    let deadline = deadline_rfc3339(policy.quiet_seconds)?;
    let (batch_id, old_count, old_lifecycle) = if let Some(open) = open {
        open
    } else {
        let batch_id = Uuid::now_v7().to_string();
        transaction.execute(
            "INSERT INTO wake_batches(
               batch_id,work_item_node_id,event_count,quiet_deadline,urgent,lifecycle,created_at,updated_at
             ) VALUES (?1,?2,0,?3,0,'pending',?4,?4)",
            params![batch_id, work_item_node_id, deadline, now],
        )?;
        (batch_id, 0, "pending".into())
    };
    let inserted = transaction.execute(
        "INSERT OR IGNORE INTO wake_batch_events(batch_id,event_id,ordinal)
         VALUES (?1,?2,(SELECT COUNT(*) FROM wake_batch_events WHERE batch_id=?1))",
        params![batch_id, event_id],
    )?;
    let count = old_count + i64::try_from(inserted).expect("SQLite change count fits i64");
    if count == 0 {
        if created {
            transaction.execute("DELETE FROM wake_batches WHERE batch_id=?1", [&batch_id])?;
        }
        return Err(StoreError::InvalidData(format!(
            "event {event_id} is already bound to another wake batch"
        )));
    }
    let threshold = i64::from(policy.event_threshold);
    let lifecycle = if old_lifecycle == "runnable" || urgent || count >= threshold {
        "runnable"
    } else {
        "pending"
    };
    transaction.execute(
        "UPDATE wake_batches SET
           event_count=?2,
           quiet_deadline=CASE WHEN lifecycle='runnable' THEN quiet_deadline ELSE ?3 END,
           urgent=CASE WHEN ?4=1 THEN 1 ELSE urgent END,
           lifecycle=?5,
           updated_at=?6
         WHERE batch_id=?1",
        params![batch_id, count, deadline, i64::from(urgent), lifecycle, now],
    )?;
    Ok((batch_id, lifecycle.into()))
}

fn replay_event(
    transaction: &rusqlite::Transaction<'_>,
    event_id: &str,
    work_item_node_id: &str,
    dedupe_prefix: &str,
    reason: &str,
    policy: SchedulerPolicy,
    now: &str,
) -> Result<(), StoreError> {
    let dedupe_key = format!("{dedupe_prefix}{event_id}");
    let existing: Option<String> = transaction
        .query_row("SELECT event_id FROM events WHERE dedupe_key=?1", [&dedupe_key], |row| row.get(0))
        .optional()?;
    if existing.is_some() {
        return Ok(());
    }
    let replay_event_id = Uuid::now_v7().to_string();
    let inserted = transaction.execute(
        "INSERT INTO events(
           event_id,delivery_guid,work_item_node_id,object_node_id,object_version,
           kind,detail,origin,reference,lifecycle,observed_at,dedupe_key,
           mention_candidate,trusted_mention,body_digest,writer_group,writer_turn,recipient_login,recipient_revision
         )
         SELECT ?1,delivery_guid,work_item_node_id,object_node_id,object_version,
                kind,detail,origin,reference,'pending',observed_at,?3,
                mention_candidate,trusted_mention,body_digest,writer_group,writer_turn,recipient_login,recipient_revision
         FROM events WHERE event_id=?2",
        params![replay_event_id, event_id, dedupe_key],
    )?;
    if inserted != 1 {
        return Err(StoreError::InvalidData(format!("replay source event {event_id} is missing")));
    }
    schedule_event(transaction, work_item_node_id, &replay_event_id, policy, false, now)?;
    transaction.execute(
        "UPDATE local_comment_delivery SET event_id=?2,reason=?3 WHERE event_id=?1 AND status='queued'",
        params![event_id, replay_event_id, reason],
    )?;
    Ok(())
}

// Historical queued contact cannot create a second logical member with the
// same address. Settle receipts even when no profile worker can recover.
fn settle_unreachable_contacts(transaction: &rusqlite::Transaction<'_>) -> Result<(), StoreError> {
    transaction.execute(
        "UPDATE events SET lifecycle='blocked'
         WHERE lifecycle='pending' AND kind='mention' AND detail='direct_contact'
           AND EXISTS(SELECT 1 FROM assignments a WHERE a.member_login=events.recipient_login
                      AND a.lifecycle IN ('blocked','retired'))",
        [],
    )?;
    transaction.execute(
        "UPDATE local_comment_delivery SET status='unreachable',reason=(
           SELECT '@' || a.member_login || ' has no resumable session (' || a.lifecycle || ')'
           FROM assignments a JOIN events e ON e.recipient_login=a.member_login
           WHERE e.event_id=local_comment_delivery.event_id AND a.lifecycle IN ('blocked','retired'))
         WHERE status='queued' AND event_id IN (
           SELECT e.event_id FROM events e JOIN assignments a ON a.member_login=e.recipient_login
           WHERE e.lifecycle='blocked' AND e.kind='mention' AND e.detail='direct_contact'
             AND a.lifecycle IN ('blocked','retired'))",
        [],
    )?;
    Ok(())
}

fn advance_scheduler(database: &Path) -> Result<u64, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let now = now_rfc3339();
    // A description addressed before reassignment cannot invalidate the new
    // member or hold its ordinary inputs behind a permanent reset gate.
    transaction.execute(
        "UPDATE events SET lifecycle='superseded' WHERE lifecycle='pending' AND kind='invalidate'
         AND EXISTS(SELECT 1 FROM local_items l WHERE l.node_id=events.work_item_node_id
                    AND ((events.recipient_revision IS NOT NULL AND events.recipient_revision!=l.assignment_revision)
                         OR (events.recipient_login IS NOT NULL AND events.recipient_login IS NOT l.desired_member_login)))", [],
    )?;
    settle_unreachable_contacts(&transaction)?;
    recover_stale_wake_batches(&transaction, &now)?;
    let changed = transaction.execute(
        "UPDATE wake_batches SET lifecycle='runnable',updated_at=?1
         WHERE lifecycle='pending' AND quiet_deadline<=?1 AND EXISTS (
           SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
           WHERE be.batch_id=wake_batches.batch_id AND e.lifecycle='pending'
         )",
        [&now],
    )?;
    transaction.commit()?;
    Ok(u64::try_from(changed).expect("SQLite change count fits u64"))
}

fn recover_stale_wake_batches(
    transaction: &rusqlite::Transaction<'_>, now: &str,
) -> Result<(), StoreError> {
    // Earlier unknown-turn recovery left these inputs attached to consumed batches.
    let stale = {
        let mut statement = transaction.prepare(
            "SELECT e.event_id,e.work_item_node_id FROM events e
             JOIN wake_batch_events be ON be.event_id=e.event_id
             JOIN wake_batches b ON b.batch_id=be.batch_id
             WHERE e.lifecycle='pending' AND b.lifecycle='consumed'
             ORDER BY e.observed_at,e.event_id",
        )?;
        statement.query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))?
            .collect::<Result<Vec<_>, _>>()?
    };
    for (event_id, work_item_node_id) in stale {
        replay_event(
            &transaction, &event_id, &work_item_node_id, UNKNOWN_REPLAY_DEDUPE_PREFIX,
            "retrying after uncertain provider outcome",
            SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, &now,
        )?;
        transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'", [&event_id])?;
    }
    transaction.execute(
        "UPDATE wake_batches SET lifecycle='consumed',updated_at=?1
         WHERE lifecycle IN ('pending','runnable') AND NOT EXISTS (
           SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
           WHERE be.batch_id=wake_batches.batch_id AND e.lifecycle IN ('pending','resetting')
         )",
        [&now],
    )?;
    Ok(())
}

fn runtime_status(database: &Path) -> Result<RuntimeStoreStatus, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    let batches = load_wake_batches(&connection)?;
    let agent_groups = load_agent_groups(&connection)?;
    let context_resets = load_context_resets(&connection)?;
    Ok(RuntimeStoreStatus {
        deliveries: scalar_u64(&connection, "SELECT COUNT(*) FROM deliveries")?,
        duplicate_deliveries: scalar_u64(
            &connection,
            "SELECT COALESCE(SUM(duplicate_count),0) FROM deliveries",
        )?,
        unknown_deliveries: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM deliveries WHERE known=0",
        )?,
        pending_batches: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM wake_batches WHERE lifecycle='pending'",
        )?,
        runnable_batches: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM wake_batches WHERE lifecycle='runnable'",
        )?,
        pending_mentions: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM events WHERE mention_candidate=1 AND trusted_mention IS NULL AND lifecycle='pending'",
        )?,
        pending_writes: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM github_write_outbox WHERE lifecycle IN ('pending','sending')",
        )?,
        uncertain_writes: scalar_u64(
            &connection,
            "SELECT COUNT(*) FROM github_write_outbox WHERE lifecycle='uncertain'",
        )?,
        last_reconciliation: connection
            .query_row(
                "SELECT completed_at FROM reconciliation_runs
                 WHERE lifecycle='completed' ORDER BY completed_at DESC LIMIT 1",
                [],
                |row| row.get(0),
            )
            .optional()?,
        batches,
        agent_groups,
        context_resets,
    })
}

fn load_wake_batches(
    connection: &rusqlite::Connection,
) -> Result<Vec<WakeBatchSummary>, StoreError> {
    let mut statement = connection.prepare(
        "SELECT b.batch_id,r.name_with_owner,w.kind,w.number,w.node_id,b.event_count,
                b.quiet_deadline,b.urgent,b.lifecycle
         FROM wake_batches b
         JOIN work_items w ON w.node_id=b.work_item_node_id
         JOIN repositories r ON r.node_id=w.repository_node_id
         WHERE b.lifecycle IN ('pending','runnable')
         ORDER BY b.created_at,b.batch_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok(WakeBatchSummary {
            batch_id: row.get(0)?,
            repository: row.get(1)?,
            work_item_kind: row.get(2)?,
            work_item_number: sqlite_i64_to_u64(row.get(3)?, "work-item number")?,
            work_item_node_id: row.get(4)?,
            event_count: sqlite_i64_to_u64(row.get(5)?, "batch event count")?,
            quiet_deadline: row.get(6)?,
            urgent: row.get::<_, i64>(7)? != 0,
            lifecycle: row.get(8)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn load_agent_groups(
    connection: &rusqlite::Connection,
) -> Result<Vec<AgentGroupSummary>, StoreError> {
    let mut statement = connection.prepare(
        "SELECT w.kind,w.number,ai.profile_id,a.generation,a.lifecycle,
                ps.provider_session_id,ps.lifecycle,t.provider_turn_id,t.lifecycle,
                (SELECT COUNT(*) FROM turns at
                 JOIN provider_sessions aps ON aps.session_id=at.session_id
                 WHERE aps.agent_id=ai.agent_id),
                (SELECT COUNT(*) FROM turns ft
                 JOIN provider_sessions fps ON fps.session_id=ft.session_id
                 WHERE fps.agent_id=ai.agent_id AND ft.trigger_kind='finalization'),
                (SELECT ft.lifecycle FROM turns ft
                 JOIN provider_sessions fps ON fps.session_id=ft.session_id
                 WHERE fps.agent_id=ai.agent_id AND ft.trigger_kind='finalization'
                 ORDER BY ft.rowid DESC LIMIT 1),
                COALESCE(ps.resume_count,0),ps.last_resumed_at,
                ai.context_pressure,ai.context_bytes,ai.context_error,
                wt.path,wt.lifecycle,wt.head_ref
         FROM assignments a
         JOIN work_items w ON w.node_id=a.work_item_node_id
         JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         LEFT JOIN worktrees wt ON wt.agent_id=ai.agent_id
         LEFT JOIN provider_sessions ps ON ps.agent_id=ai.agent_id
         LEFT JOIN turns t ON t.session_id=ps.session_id
           AND t.lifecycle IN ('starting','running','unknown')
         ORDER BY a.assigned_at,a.assignment_id,ps.started_at",
    )?;
    let rows = statement.query_map([], |row| {
        Ok(AgentGroupSummary {
            work_item_kind: row.get(0)?,
            work_item_number: sqlite_i64_to_u64(row.get(1)?, "agent Work Item number")?,
            profile_id: row.get(2)?,
            assignment_generation: sqlite_i64_to_u64(row.get(3)?, "assignment generation")?,
            assignment_lifecycle: row.get(4)?,
            provider_session_id: row.get(5)?,
            session_lifecycle: row.get(6)?,
            active_turn_id: row.get(7)?,
            turn_lifecycle: row.get(8)?,
            turn_count: sqlite_i64_to_u64(row.get(9)?, "turn count")?,
            finalization_turns: sqlite_i64_to_u64(row.get(10)?, "finalization turn count")?,
            last_finalization_lifecycle: row.get(11)?,
            provider_resume_count: sqlite_i64_to_u64(row.get(12)?, "provider resume count")?,
            last_provider_resume: row.get(13)?,
            context_pressure: row.get(14)?,
            context_bytes: row
                .get::<_, Option<i64>>(15)?
                .map(|value| sqlite_i64_to_u64(value, "Context bytes"))
                .transpose()?,
            context_error: row.get(16)?,
            worktree_path: row.get::<_, Option<String>>(17)?.map(PathBuf::from),
            worktree_lifecycle: row.get(18)?,
            worktree_head_ref: row.get(19)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn load_context_resets(connection: &Connection) -> Result<Vec<ContextResetSummary>, StoreError> {
    let mut statement = connection.prepare(
        "SELECT cr.reset_id,r.name_with_owner,w.kind,w.number,ai.profile_id,cr.lifecycle,
                cr.continuation,old.provider_session_id,new.provider_session_id,
                cr.context_revision_before,cr.context_revision_after
         FROM context_resets cr
         JOIN agent_instances ai ON ai.agent_id=cr.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id
         JOIN repositories r ON r.node_id=w.repository_node_id
         JOIN provider_sessions old ON old.session_id=cr.old_session_id
         LEFT JOIN provider_sessions new ON new.session_id=cr.new_session_id
         ORDER BY cr.created_at,cr.reset_id",
    )?;
    let rows = statement.query_map([], |row| {
        Ok(ContextResetSummary {
            reset_id: row.get(0)?,
            repository: row.get(1)?,
            work_item_kind: row.get(2)?,
            work_item_number: sqlite_i64_to_u64(row.get(3)?, "context reset Work Item number")?,
            profile_id: row.get(4)?,
            lifecycle: row.get(5)?,
            continuation: row.get::<_, i64>(6)? != 0,
            old_provider_session_id: row.get(7)?,
            new_provider_session_id: row.get(8)?,
            context_revision_before: row.get(9)?,
            context_revision_after: row.get(10)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn tracked_work_items(database: &Path) -> Result<Vec<TrackedWorkItem>, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "SELECT w.node_id,r.name_with_owner,w.kind,w.number,w.state
         FROM work_items w JOIN repositories r ON r.node_id=w.repository_node_id
         WHERE w.kind IN ('issue','pr')
         ORDER BY r.name_with_owner,w.kind,w.number",
    )?;
    let rows = statement.query_map([], |row| {
        Ok(TrackedWorkItem {
            node_id: row.get(0)?,
            repository: row.get(1)?,
            kind: row.get(2)?,
            number: sqlite_i64_to_u64(row.get(3)?, "work-item number")?,
            state: row.get(4)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn canonical_objects(
    database: &Path,
    work_item_node_id: &str,
) -> Result<Vec<CanonicalObjectState>, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "SELECT node_id,database_id,object_kind,version,digest,lifecycle,
                author_node_id,author_login
         FROM canonical_objects WHERE work_item_node_id=?1
         ORDER BY object_kind,node_id",
    )?;
    let rows = statement.query_map([work_item_node_id], |row| {
        Ok(CanonicalObjectState {
            node_id: row.get(0)?,
            database_id: row.get(1)?,
            object_kind: row.get(2)?,
            version: row.get(3)?,
            digest: row.get(4)?,
            lifecycle: row.get(5)?,
            author_node_id: row.get(6)?,
            author_login: row.get(7)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn begin_reconciliation(
    database: &Path,
    repository_node_id: &str,
) -> Result<ReconciliationRun, StoreError> {
    require_current_schema(database)?;
    let run = ReconciliationRun {
        run_id: Uuid::now_v7().to_string(),
        repository_node_id: repository_node_id.into(),
    };
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    connection.execute(
        "INSERT INTO reconciliation_runs(run_id,repository_node_id,lifecycle,started_at)
         VALUES (?1,?2,'running',?3)",
        params![run.run_id, run.repository_node_id, now_rfc3339()],
    )?;
    Ok(run)
}

fn finish_reconciliation(
    database: &Path,
    run: &ReconciliationRun,
    lifecycle: &str,
    work_item_count: usize,
    change_count: usize,
    error: Option<&str>,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(lifecycle, "completed" | "failed") {
        return Err(StoreError::InvalidData(format!(
            "invalid reconciliation terminal {lifecycle}"
        )));
    }
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let updated = connection.execute(
        "UPDATE reconciliation_runs SET lifecycle=?2,completed_at=?3,work_item_count=?4,
           change_count=?5,error=?6 WHERE run_id=?1 AND lifecycle='running'",
        params![
            run.run_id,
            lifecycle,
            now_rfc3339(),
            sqlite_usize(work_item_count, "reconciliation work-item count")?,
            sqlite_usize(change_count, "reconciliation change count")?,
            error,
        ],
    )?;
    if updated == 1 {
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!("reconciliation run {} is not active", run.run_id)))
    }
}

fn register_profile(database: &Path, profile: &ProfileRecord) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if profile.effective_digest.len() != 64 {
        return Err(StoreError::InvalidData("Profile digest is not SHA-256".into()));
    }
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    connection.execute(
        "INSERT INTO profiles(profile_id,revision,effective_digest,provider_kind,tags,assignee_login,assignee_description)
         VALUES (?1,?2,?3,?4,?5,?6,?7)
         ON CONFLICT(profile_id,revision) DO UPDATE SET
           effective_digest=excluded.effective_digest,
           provider_kind=excluded.provider_kind,
           tags=excluded.tags,
           assignee_login=excluded.assignee_login,
           assignee_description=excluded.assignee_description",
        params![
            profile.profile_id,
            sqlite_u64(profile.revision, "Profile revision")?,
            profile.effective_digest,
            profile.provider_kind,
            profile.tags,
            profile.assignee_login,
            profile.assignee_description,
        ],
    )?;
    Ok(())
}

fn provider_resume_candidates(
    database: &Path,
    profile_id: &str,
    work_item_kind: &str,
) -> Result<Vec<ProviderResumeCandidate>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "SELECT a.assignment_id,ps.provider_session_id,r.name_with_owner,w.number,
                ai.profile_id,ai.profile_revision,a.member_login,ps.instruction_revision,ps.lifecycle,
                t.turn_id,t.lifecycle,wt.path,wt.head_ref,w.kind,ps.provider_kind,
                (ps.lifecycle IN ('running','unknown','blocked') OR
                 EXISTS(SELECT 1 FROM wake_batches b JOIN wake_batch_events be ON be.batch_id=b.batch_id
                        JOIN events e ON e.event_id=be.event_id WHERE b.work_item_node_id=w.node_id
                        AND b.lifecycle IN ('pending','runnable') AND e.lifecycle='pending'
                        AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
                        AND (e.recipient_revision IS NULL OR e.recipient_revision=a.assignment_revision)) OR
                 EXISTS(SELECT 1 FROM events e WHERE e.work_item_node_id=w.node_id AND e.kind='invalidate'
                        AND e.lifecycle='pending' AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
                        AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))) OR
                 EXISTS(SELECT 1 FROM context_resets cr WHERE cr.old_session_id=ps.session_id AND cr.lifecycle='interrupting')) AS needs_resume,
                (SELECT json_group_array(e.event_id) FROM events e WHERE e.work_item_node_id=w.node_id AND e.lifecycle='pending'
                 AND e.kind IN ('wake','mention','invalidate','lifecycle')
                 AND coalesce(e.detail,'') NOT IN ('uncertain_continuation','reset_continuation')
                 AND coalesce(e.dedupe_key,'') NOT LIKE 'braid-failed-turn-replay-v1:%'
                 AND coalesce(e.dedupe_key,'') NOT LIKE 'deferred-input:%'
                 AND NOT EXISTS(SELECT 1 FROM local_comment_delivery d JOIN local_comments c ON c.comment_id=d.comment_id
                                WHERE d.event_id=e.event_id AND c.system_author='Braid')
                 AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
                 AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))
                ) AS new_input_ids
         FROM assignments a
         JOIN work_items w ON w.node_id=a.work_item_node_id AND w.kind=?2
         JOIN repositories r ON r.node_id=w.repository_node_id
         JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         JOIN local_items l ON l.node_id=w.node_id AND l.desired_profile_id=ai.profile_id AND l.desired_member_login=a.member_login AND l.assignment_revision=a.assignment_revision
         JOIN provider_sessions ps ON ps.agent_id=ai.agent_id
           AND (ps.lifecycle IN ('idle','running','unknown') OR
                (ps.lifecycle='blocked' AND (ps.last_resume_error='persisted provider session is incompatible with its Profile/worktree'
                 OR ps.last_resume_error LIKE 'session deferred input:%' OR ps.last_resume_error='session is unavailable')))
         LEFT JOIN worktrees wt ON wt.agent_id=ai.agent_id AND wt.lifecycle='active'
         LEFT JOIN turns t ON t.session_id=ps.session_id
           AND t.turn_id=(SELECT latest.turn_id FROM turns latest WHERE latest.session_id=ps.session_id AND latest.lifecycle IN ('starting','running','unknown') ORDER BY latest.turn_id DESC LIMIT 1)
         WHERE a.lifecycle IN ('active','finalizing','blocked') AND ai.profile_id=?1
           AND (a.lifecycle!='blocked' OR ps.lifecycle='blocked')
         ORDER BY a.assigned_at,a.assignment_id,ps.started_at",
    )?;
    let rows = statement.query_map(params![profile_id, work_item_kind], |row| {
        Ok(ProviderResumeCandidate {
            provider_kind: row.get(14)?,
            assignment_id: row.get(0)?,
            provider_session_id: row.get(1)?,
            repository: row.get(2)?,
            number: sqlite_i64_to_u64(row.get(3)?, "resume Issue number")?,
            profile_id: row.get(4)?,
            profile_revision: sqlite_i64_to_u64(row.get(5)?, "resume Profile revision")?,
            member_login: row.get(6)?,
            instruction_revision: row.get(7)?,
            session_lifecycle: row.get(8)?,
            active_turn_id: row.get(9)?,
            active_turn_lifecycle: row.get(10)?,
            worktree_path: row.get::<_, Option<String>>(11)?.map(PathBuf::from),
            worktree_head_ref: row.get(12)?,
            work_item_kind: row.get(13)?,
            needs_resume: row.get(15)?,
            new_input_ids: serde_json::from_str(&row.get::<_,String>(16)?).map_err(|error|
                rusqlite::Error::FromSqlConversionFailure(16, rusqlite::types::Type::Text, Box::new(error)))?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

/// Replace only the physical session after the adapter confirmed missing native history. The assignment, member, agent, and worktree stay.
fn begin_provider_replacement(
    database: &Path,
    provider_session_id: &str,
    profile: &ProfileRecord,
) -> Result<Option<ContextResetClaim>, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let old = transaction.query_row(
        "SELECT ai.agent_id,ps.session_id,ps.context_revision,
                EXISTS(SELECT 1 FROM turns t WHERE t.session_id=ps.session_id AND t.lifecycle='unknown')
         FROM provider_sessions ps
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN local_items l ON l.node_id=a.work_item_node_id
         WHERE ps.provider_session_id=?1 AND ps.lifecycle IN ('idle','unknown','blocked')
           AND ai.profile_id=?2 AND a.lifecycle IN ('active','finalizing','blocked')
           AND l.desired_profile_id=ai.profile_id AND l.desired_member_login=a.member_login
           AND l.assignment_revision=a.assignment_revision
           AND NOT EXISTS(SELECT 1 FROM turns t WHERE t.session_id=ps.session_id AND t.lifecycle IN ('starting','running'))
           AND NOT EXISTS(SELECT 1 FROM context_resets cr WHERE cr.agent_id=ai.agent_id AND cr.lifecycle IN ('interrupting','materializing'))",
        params![provider_session_id, profile.profile_id],
        |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?,
                  row.get::<_, String>(2)?, row.get::<_, bool>(3)?)),
    ).optional()?;
    let Some((agent_id, old_session_id, context_revision, continuation)) = old else {
        transaction.commit()?;
        return Ok(None);
    };
    upsert_profile_record(&transaction, profile)?;
    let reset_id = Uuid::now_v7().to_string();
    transaction.execute(
        "INSERT INTO context_resets(reset_id,agent_id,old_session_id,context_revision_before,
                continuation,lifecycle,created_at,updated_at)
         VALUES(?1,?2,?3,?4,?5,'materializing',?6,?6)",
        params![reset_id,agent_id,old_session_id,context_revision,i64::from(continuation),now],
    )?;
    transaction.execute(
        "UPDATE assignments SET lifecycle=CASE
           WHEN (SELECT state FROM work_items WHERE node_id=assignments.work_item_node_id)='OPEN'
           THEN 'active' ELSE 'finalizing' END,retired_at=NULL
         WHERE assignment_id=(SELECT assignment_id FROM agent_instances WHERE agent_id=?1)
           AND lifecycle='blocked'",
        [&agent_id],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='reset_pending',profile_revision=?2,context_error=NULL
         WHERE agent_id=?1",
        params![agent_id,sqlite_u64(profile.revision,"Profile revision")?],
    )?;
    transaction.execute("UPDATE provider_sessions SET lifecycle='reset_pending' WHERE session_id=?1", [&old_session_id])?;
    let claim = load_context_reset_claim(&transaction, &reset_id)?;
    transaction.commit()?;
    Ok(Some(claim))
}

/// The host calls this only after proving the previous execution environment
/// has stopped and obtaining the runtime lock. The returned native IDs carry
/// that stop evidence into this process's SessionManager.
#[derive(serde::Deserialize)]
struct PhysicalSessionAttempt {
    group_id: Option<String>,
    provider: String,
    status: String,
    error: Option<String>,
    session_id: Option<String>,
    native_session_path: Option<String>,
    native_session_id: Option<String>,
}

fn identityless_pi_reset_attempt(database: &Path, reset_id: &str, agent_id: &str) -> bool {
    let Some(state) = database.parent() else { return false };
    let Ok(entries) = fs::read_dir(state.join("physical")) else { return false };
    let mut failed_attempt = false;
    for entry in entries {
        let Ok(entry) = entry else { return false };
        let name = entry.file_name();
        let Some(name) = name.to_str() else { return false };
        // Both names are runtime-generated UUIDv7 values; their lexical order is time order.
        if name <= reset_id { continue }
        let Ok(bytes) = fs::read(entry.path().join("session.json")) else { return false };
        let Ok(attempt) = serde_json::from_slice::<PhysicalSessionAttempt>(&bytes) else { return false };
        if attempt.group_id.as_deref() != Some(agent_id) { continue }
        if attempt.provider != "pi"
            || attempt.status != "failed"
            || attempt.error.is_none()
            || attempt.session_id.is_some()
            || attempt.native_session_path.is_some()
            || attempt.native_session_id.is_some()
        {
            return false;
        }
        failed_attempt = true;
    }
    failed_attempt
}

fn prepare_offline_resume(database: &Path) -> Result<Vec<String>, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let provider_ids = {
        let mut statement = transaction.prepare(
            "SELECT provider_session_id FROM provider_sessions ORDER BY started_at,session_id",
        )?;
        statement.query_map([], |row| row.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?
    };
    transaction.execute("UPDATE provider_sessions SET cli_binding_id=NULL WHERE cli_binding_id IS NOT NULL", [])?;
    let now = now_rfc3339();
    // A prior process can stop after claiming a sleeping member but before
    // the native resume returns. No input was accepted, so keep that contact.
    let interrupted_reactivations = {
        let mut statement = transaction.prepare(
            "SELECT e.event_id,a.assignment_id FROM assignments a
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
             JOIN provider_sessions ps ON ps.agent_id=ai.agent_id AND ps.lifecycle='sleeping'
             JOIN events e ON e.work_item_node_id=a.work_item_node_id
               AND e.lifecycle='materializing' AND e.detail IN ('reopened','direct_contact')
             WHERE a.lifecycle='materializing' AND ai.lifecycle='materializing'",
        )?;
        statement.query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))?
            .collect::<Result<Vec<_>, _>>()?
    };
    for (event_id, assignment_id) in interrupted_reactivations {
        defer_work_item_reactivation_transaction(
            &transaction, &event_id, &assignment_id,
            "native resume interrupted before input acceptance",
        )?;
    }
    // A stopped runtime may have persisted an assignment and worktree before
    // its native session was registered. Finish that attempt before dispatch.
    let interrupted = {
        let mut statement = transaction.prepare(
            "SELECT a.assignment_id,ai.agent_id,a.work_item_node_id,w.state,
                    a.member_login,ai.profile_id,a.assignment_revision,ai.lifecycle,a.assigned_at,
                    l.desired_member_login,l.desired_profile_id,l.assignment_revision
             FROM assignments a
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             JOIN local_items l ON l.node_id=w.node_id
             WHERE a.lifecycle='materializing'
               AND NOT EXISTS(SELECT 1 FROM provider_sessions ps WHERE ps.agent_id=ai.agent_id)
             ORDER BY a.assigned_at,a.assignment_id",
        )?;
        statement.query_map([], |row| {
            Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, String>(2)?,
                row.get::<_, String>(3)?, row.get::<_, String>(4)?, row.get::<_, String>(5)?,
                row.get::<_, i64>(6)?, row.get::<_, String>(7)?, row.get::<_, String>(8)?,
                row.get::<_, Option<String>>(9)?, row.get::<_, Option<String>>(10)?, row.get::<_, i64>(11)?))
        })?.collect::<Result<Vec<_>, _>>()?
    };
    for (assignment, agent, node, state, member, profile, revision, agent_state, assigned_at,
         desired_member, desired_profile, desired_revision) in interrupted {
        if agent_state != "materializing" {
            return Err(StoreError::InvalidData(format!(
                "interrupted assignment {assignment} has agent lifecycle {agent_state}"
            )));
        }
        if state == "OPEN" && (desired_member.as_deref() != Some(member.as_str())
            || desired_profile.as_deref() != Some(profile.as_str()) || desired_revision != revision)
        {
            return Err(StoreError::InvalidData(format!(
                "interrupted assignment {assignment} no longer matches its member"
            )));
        }
        if !matches!(state.as_str(), "OPEN" | "CLOSED" | "MERGED") {
            return Err(StoreError::InvalidData(format!(
                "interrupted assignment {assignment} has work item state {state}"
            )));
        }
        // A member login is unique across every generation. Release it only
        // when the same open Work Item will activate that member again.
        transaction.execute(
            "UPDATE assignments SET lifecycle='retired',retired_at=?2,
               member_login=CASE WHEN ?3='OPEN' THEN NULL ELSE member_login END
             WHERE assignment_id=?1",
            params![assignment, now, state],
        )?;
        transaction.execute(
            "UPDATE agent_instances SET lifecycle='retired',context_error=?2 WHERE agent_id=?1",
            params![agent, format!("native materialization interrupted before provider registration; member @{member}")],
        )?;
        transaction.execute(
            "UPDATE worktrees SET lifecycle='retired',observed_at=?2 WHERE agent_id=?1 AND lifecycle='active'",
            params![agent, now],
        )?;
        if state == "OPEN" {
            let event = Uuid::now_v7().to_string();
            transaction.execute(
                "INSERT INTO events(event_id,work_item_node_id,kind,detail,origin,reference,lifecycle,dedupe_key,observed_at)
                 VALUES(?1,?2,'assign','activate','local',?3,'pending',?4,?5)",
                params![event, node, "旧执行停止后重试中断的成员物化", format!("offline-materialization:{assignment}"), assigned_at],
            )?;
            schedule_event(&transaction, &node, &event,
                SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, true, &now)?;
        } else {
            transaction.execute(
                "UPDATE events SET lifecycle='consumed'
                 WHERE work_item_node_id=?1 AND kind='lifecycle' AND detail='closed' AND lifecycle='pending'",
                [&node],
            )?;
        }
    }
    // A failed Pi start with no native identity can be retried only after the
    // previous execution has stopped. Retain the same reset and event ownership.
    let identityless_resets = {
        let mut statement = transaction.prepare(
            "SELECT cr.reset_id,cr.agent_id FROM context_resets cr
             JOIN agent_instances ai ON ai.agent_id=cr.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             JOIN local_items l ON l.node_id=w.node_id
             JOIN provider_sessions old ON old.session_id=cr.old_session_id
             WHERE cr.lifecycle='blocked' AND cr.error IS NOT NULL
               AND cr.new_session_id IS NULL
               AND (cr.active_turn_id IS NULL OR EXISTS(
                   SELECT 1 FROM turns t WHERE t.turn_id=cr.active_turn_id
                     AND t.session_id=cr.old_session_id AND t.lifecycle='completed'))
               AND old.provider_kind='pi' AND old.lifecycle='blocked'
               AND ai.lifecycle='blocked' AND ai.context_error=cr.error
               AND a.lifecycle='active' AND w.state='OPEN'
               AND l.desired_member_login=a.member_login
               AND l.desired_profile_id=ai.profile_id
               AND l.assignment_revision=a.assignment_revision
               AND EXISTS(SELECT 1 FROM worktrees wt WHERE wt.agent_id=ai.agent_id AND wt.lifecycle='active')
               AND NOT EXISTS(SELECT 1 FROM provider_sessions newer
                   WHERE newer.agent_id=ai.agent_id AND newer.session_id!=old.session_id
                     AND newer.started_at>=old.started_at)
               AND NOT EXISTS(SELECT 1 FROM context_resets later
                   WHERE later.agent_id=ai.agent_id AND later.reset_id!=cr.reset_id
                     AND (later.created_at>cr.created_at
                          OR (later.created_at=cr.created_at AND later.reset_id>cr.reset_id)))
               AND NOT EXISTS(SELECT 1 FROM context_reset_events cre
                   JOIN events e ON e.event_id=cre.event_id
                   WHERE cre.reset_id=cr.reset_id AND e.lifecycle!='blocked')
             ORDER BY cr.created_at,cr.reset_id",
        )?;
        statement.query_map([], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)))?
            .collect::<Result<Vec<_>, _>>()?
    };
    for (reset_id, agent_id) in identityless_resets {
        if !identityless_pi_reset_attempt(database, &reset_id, &agent_id) { continue }
        transaction.execute(
            "UPDATE context_resets SET lifecycle='materializing',error=NULL,updated_at=?2 WHERE reset_id=?1",
            params![reset_id, now],
        )?;
        transaction.execute(
            "UPDATE agent_instances SET lifecycle='reset_pending',context_error=NULL WHERE agent_id=?1",
            [&agent_id],
        )?;
        transaction.execute(
            "UPDATE provider_sessions SET lifecycle='reset_pending'
             WHERE session_id=(SELECT old_session_id FROM context_resets WHERE reset_id=?1)",
            [&reset_id],
        )?;
        transaction.execute(
            "UPDATE events SET lifecycle='resetting' WHERE lifecycle='blocked'
               AND event_id IN (SELECT event_id FROM context_reset_events WHERE reset_id=?1)",
            [&reset_id],
        )?;
        tracing::info!(reset = %reset_id, "recovering identityless Pi Context reset after offline stop");
    }
    // Earlier recovery could apply a physical reset while leaving the old
    // assignment blocked. The new idle session and current member prove that
    // this group is ready to resume under its existing responsibility.
    transaction.execute(
        "UPDATE assignments SET lifecycle=CASE
           WHEN (SELECT state FROM work_items WHERE node_id=assignments.work_item_node_id)='OPEN'
           THEN 'active' ELSE 'finalizing' END,retired_at=NULL
         WHERE lifecycle='blocked' AND EXISTS(
           SELECT 1 FROM agent_instances ai
           JOIN provider_sessions ps ON ps.agent_id=ai.agent_id AND ps.lifecycle='idle'
           JOIN context_resets cr ON cr.new_session_id=ps.session_id AND cr.lifecycle='applied'
           JOIN local_items l ON l.node_id=assignments.work_item_node_id
           WHERE ai.assignment_id=assignments.assignment_id AND ai.lifecycle='idle'
             AND ai.context_error IS NULL AND l.desired_profile_id=ai.profile_id
             AND l.desired_member_login=assignments.member_login
             AND l.assignment_revision=assignments.assignment_revision)",
        [],
    )?;
    transaction.execute(
        "UPDATE context_resets SET lifecycle='materializing',active_turn_id=NULL,error=NULL,updated_at=?1
         WHERE lifecycle='interrupting' AND EXISTS (
           SELECT 1 FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id
           WHERE ai.agent_id=context_resets.agent_id AND a.lifecycle IN ('active','finalizing')
         )",
        [&now],
    )?;
    let active_turns = {
        let mut statement = transaction.prepare(
            "SELECT t.turn_id FROM turns t
             JOIN provider_sessions ps ON ps.session_id=t.session_id
             JOIN agent_instances ai ON ai.agent_id=ps.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             WHERE t.lifecycle IN ('starting','running')
               AND ps.lifecycle IN ('idle','running','unknown')
               AND a.lifecycle IN ('active','finalizing')
             ORDER BY t.turn_id",
        )?;
        statement.query_map([], |row| row.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?
    };
    for turn_id in active_turns {
        mark_turn_terminal_transaction(&transaction, &turn_id, "unknown", &now, true)?;
    }
    recover_stale_wake_batches(&transaction, &now)?;
    transaction.commit()?;
    Ok(provider_ids)
}

fn clear_provider_binding(database: &Path, provider_session_id: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let updated = connection.execute(
        "UPDATE provider_sessions SET cli_binding_id=NULL WHERE provider_session_id=?1 AND lifecycle IN ('idle','unknown','blocked')",
        [provider_session_id],
    )?;
    if updated == 1 { Ok(()) } else { Err(StoreError::InvalidData(format!("provider session {provider_session_id} is not resumable"))) }
}

fn fence_idle_provider(database: &Path, id: &str) -> Result<bool, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let updated = transaction.execute(
        "UPDATE provider_sessions SET cli_binding_id=NULL WHERE provider_session_id=?1 AND lifecycle='idle'
         AND cli_binding_id IS NOT NULL AND EXISTS(
           SELECT 1 FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id
           JOIN work_items w ON w.node_id=a.work_item_node_id
           JOIN local_items l ON l.node_id=w.node_id
           WHERE ai.agent_id=provider_sessions.agent_id AND ai.lifecycle='idle' AND a.lifecycle='active' AND w.state='OPEN'
             AND l.desired_profile_id=ai.profile_id AND l.desired_member_login=a.member_login
             AND l.assignment_revision=a.assignment_revision
             AND NOT EXISTS(SELECT 1 FROM turns t WHERE t.session_id=provider_sessions.session_id AND t.lifecycle IN ('starting','running'))
             AND NOT EXISTS(SELECT 1 FROM wake_batches b WHERE b.work_item_node_id=w.node_id AND b.lifecycle IN ('pending','runnable'))
             AND NOT EXISTS(SELECT 1 FROM events e WHERE e.work_item_node_id=w.node_id AND e.lifecycle IN ('pending','resetting','materializing'))
             AND NOT EXISTS(SELECT 1 FROM context_resets cr WHERE cr.agent_id=ai.agent_id AND cr.lifecycle IN ('interrupting','materializing')))",
        [id],
    )?;
    transaction.commit()?;
    Ok(updated == 1)
}

fn record_provider_resume(database: &Path, provider_session_id: &str, binding_id: &str, profile: &ProfileRecord, instruction_revision: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let now = now_rfc3339();
    let (agent_id, work_item_node_id, was_unknown): (String,String,bool) = transaction.query_row(
        "SELECT ps.agent_id,a.work_item_node_id,ps.lifecycle='unknown'
         FROM provider_sessions ps JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE ps.provider_session_id=?1 AND ps.lifecycle IN ('idle','running','unknown','blocked')",
        [provider_session_id], |row| Ok((row.get(0)?,row.get(1)?,row.get(2)?)),
    )?;
    upsert_profile_record(&transaction, profile)?;
    transaction.execute(
        "UPDATE provider_sessions SET resume_count=resume_count+1,last_resumed_at=?2,
           last_resume_error=NULL,last_resume_failed_at=NULL,cli_binding_id=?3,
           instruction_revision=?4,lifecycle='idle' WHERE provider_session_id=?1",
        params![provider_session_id,now,binding_id,instruction_revision],
    )?;
    transaction.execute("UPDATE agent_instances SET profile_revision=?2 WHERE agent_id=?1",
        params![agent_id,sqlite_u64(profile.revision,"Profile revision")?])?;
    transaction.execute(
        "UPDATE assignments SET lifecycle=CASE WHEN (SELECT state FROM work_items WHERE node_id=assignments.work_item_node_id)='OPEN' THEN 'active' ELSE 'finalizing' END,retired_at=NULL
         WHERE assignment_id=(SELECT assignment_id FROM agent_instances WHERE agent_id=?1) AND lifecycle='blocked'",[&agent_id],
    )?;
    transaction.execute("UPDATE agent_instances SET lifecycle=CASE WHEN (SELECT lifecycle FROM assignments WHERE assignment_id=agent_instances.assignment_id)='finalizing' THEN 'finalizing' ELSE 'idle' END,context_error=NULL WHERE agent_id=?1",[&agent_id])?;
    if was_unknown {
        let prior: Option<String> = transaction.query_row(
            "SELECT t.turn_id FROM turns t JOIN provider_sessions ps ON ps.session_id=t.session_id
             WHERE ps.provider_session_id=?1 AND t.lifecycle='unknown' ORDER BY t.turn_id DESC LIMIT 1",
            [provider_session_id], |row| row.get(0),
        ).optional()?;
        if let Some(turn_id) = prior {
            enqueue_uncertain_continuation(&transaction, &turn_id, &work_item_node_id, &now)?;
        }
    }
    transaction.commit()?;
    Ok(())
}

// A new recovery fact is not a replay of the input whose acceptance/outcome
// was uncertain. Native history and the preserved clone remain the evidence.
fn enqueue_uncertain_continuation(transaction: &rusqlite::Transaction<'_>, turn_id: &str, work_item_node_id: &str, now: &str) -> Result<(), StoreError> {
    let event_id = Uuid::now_v7().to_string();
    let reference = "上次执行的终态未收到，执行结果仍未知；旧执行已确认停止，会话现已恢复。请根据保留的原生历史、当前工作区和 Issue/PR 核对已完成与未完成的工作后接续，避免重复已执行的操作。";
    let inserted = transaction.execute(
        "INSERT OR IGNORE INTO events(event_id,work_item_node_id,kind,detail,origin,reference,lifecycle,observed_at,dedupe_key,mention_candidate,trusted_mention,recipient_login,recipient_revision)
         SELECT ?1,?2,'wake','uncertain_continuation','local',?3,'pending',?4,?5,0,0,a.member_login,a.assignment_revision
         FROM turns t JOIN provider_sessions ps ON ps.session_id=t.session_id
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE t.turn_id=?6",
        params![event_id,work_item_node_id,reference,now,format!("uncertain-continuation:{turn_id}"),turn_id],
    )?;
    if inserted == 1 {
        schedule_event(transaction, work_item_node_id, &event_id, SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, false, now)?;
    }
    Ok(())
}

fn block_provider_session(
    database: &Path,
    provider_session_id: &str,
    error: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let agent_id = transaction
        .query_row(
            "SELECT agent_id FROM provider_sessions
             WHERE provider_session_id=?1 AND lifecycle IN ('idle','running','unknown','blocked')",
            [provider_session_id],
            |row| row.get::<_, String>(0),
        )
        .optional()?
        .ok_or_else(|| {
            StoreError::InvalidData(format!(
                "provider session {provider_session_id} is not resumable"
            ))
        })?;
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='blocked',last_resume_error=?2,last_resume_failed_at=?3
         WHERE provider_session_id=?1",
        params![provider_session_id, error, now],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='blocked',context_error=?2
         WHERE agent_id=?1",
        params![agent_id, error],
    )?;
    transaction.execute(
        "UPDATE assignments SET lifecycle='blocked',retired_at=?2
         WHERE assignment_id=(SELECT assignment_id FROM agent_instances WHERE agent_id=?1)
           AND lifecycle IN ('active','finalizing')",
        params![agent_id, now],
    )?;
    transaction.commit()?;
    Ok(())
}

fn stopping_provider_sessions(
    database: &Path,
    profile_id: &str,
    work_item_kind: &str,
) -> Result<Vec<String>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "SELECT ps.provider_session_id
         FROM provider_sessions ps
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id AND ai.profile_id=?1
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id AND w.kind=?2
         WHERE a.lifecycle='stopping' AND ps.lifecycle='stopping'
         ORDER BY a.assigned_at,ps.started_at,ps.provider_session_id",
    )?;
    let rows = statement.query_map(params![profile_id, work_item_kind], |row| row.get(0))?;
    rows.collect::<Result<Vec<String>, _>>().map_err(StoreError::from)
}

/// Retire a reassigned physical writer only after its adapter has confirmed
/// native teardown. The assignment's worktree remains active, preserving dirty
/// files for the replacement Profile.
fn retire_stopping_provider_session(
    database: &Path,
    provider_session_id: &str,
) -> Result<bool, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let identity = transaction
        .query_row(
            "SELECT ps.agent_id,a.assignment_id
             FROM provider_sessions ps
             JOIN agent_instances ai ON ai.agent_id=ps.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             WHERE ps.provider_session_id=?1 AND a.lifecycle='stopping'",
            [provider_session_id],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
        )
        .optional()?;
    let Some((agent_id, assignment_id)) = identity else {
        transaction.commit()?;
        return Ok(false);
    };
    transaction.execute(
        "UPDATE turns SET lifecycle='interrupted',ended_at=?2
         WHERE session_id IN (SELECT session_id FROM provider_sessions WHERE agent_id=?1)
           AND lifecycle IN ('starting','running')",
        params![agent_id, now],
    )?;
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='retired'
         WHERE agent_id=?1 AND lifecycle NOT IN ('retired','replaced','blocked')",
        [&agent_id],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='retired' WHERE agent_id=?1 AND lifecycle='stopping'",
        [&agent_id],
    )?;
    transaction.execute(
        "UPDATE assignments SET lifecycle='retired',retired_at=?2
         WHERE assignment_id=?1 AND lifecycle='stopping'",
        params![assignment_id, now],
    )?;
    transaction.commit()?;
    Ok(true)
}

fn assignment_candidates(
    database: &Path,
    work_item_kind: &str,
    profile_id: &str,
) -> Result<Vec<AssignmentCandidate>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let connection = open_read_only(database)?;
    let mut statement = connection.prepare(
        "WITH pending AS (
           SELECT e.event_id,e.work_item_node_id,e.kind,e.detail,e.observed_at,
                  ROW_NUMBER() OVER (PARTITION BY e.work_item_node_id ORDER BY e.observed_at,e.event_id) AS ordinal
           FROM events e JOIN work_items w ON w.node_id=e.work_item_node_id
           WHERE e.lifecycle='pending' AND w.kind=?1
             AND e.kind IN ('assign','unassign','mention')
             AND (e.detail IS NOT 'direct_contact' OR NOT EXISTS(
               SELECT 1 FROM assignments a WHERE a.work_item_node_id=w.node_id
                 AND a.lifecycle IN ('materializing','active','finalizing','stopping','sleeping')))
         ), candidates AS (
           SELECT e.event_id,CASE WHEN e.kind='assign' AND e.detail='activate' THEN 'activate' ELSE e.kind END AS action,
                  r.name_with_owner,w.kind,w.number,l.desired_profile_id IS NULL AS unassigned,
                  COALESCE(l.desired_profile_id,(SELECT ai.profile_id FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id WHERE a.work_item_node_id=w.node_id AND a.lifecycle IN ('stopping','retired') ORDER BY a.generation DESC LIMIT 1)) AS target_profile_id,
                  COALESCE(l.desired_member_login,(SELECT a.member_login FROM assignments a WHERE a.work_item_node_id=w.node_id AND a.lifecycle IN ('stopping','retired') ORDER BY a.generation DESC LIMIT 1)) AS member_login,
                  e.observed_at
           FROM pending e JOIN work_items w ON w.node_id=e.work_item_node_id
           LEFT JOIN local_items l ON l.node_id=w.node_id
           JOIN repositories r ON r.node_id=w.repository_node_id
           WHERE e.ordinal=1
         )
         SELECT event_id,action,name_with_owner,kind,number,unassigned,target_profile_id,member_login
         FROM candidates WHERE target_profile_id=?2 OR target_profile_id IS NULL
         ORDER BY observed_at,event_id",
    )?;
    let rows = statement.query_map(params![work_item_kind, profile_id], |row| {
        Ok(AssignmentCandidate {
            event_id: row.get(0)?,
            action: row.get(1)?,
            repository: row.get(2)?,
            work_item_kind: row.get(3)?,
            number: sqlite_i64_to_u64(row.get(4)?, "assignment Work Item number")?,
            unassigned: row.get(5)?,
            target_profile_id: row.get(6)?,
            member_login: row.get(7)?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn work_item_lifecycle_candidates(
    database: &Path,
    work_item_kind: &str,
    limit: usize,
) -> Result<Vec<WorkItemLifecycleCandidate>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let connection = open_read_only(database)?;
    let limit = i64::try_from(limit)
        .map_err(|_| StoreError::InvalidData("Work Item lifecycle limit exceeds i64".into()))?;
    let mut statement = connection.prepare(
        "SELECT e.event_id,e.detail,r.name_with_owner,w.kind,w.number
         FROM events e
         JOIN work_items w ON w.node_id=e.work_item_node_id
         JOIN repositories r ON r.node_id=w.repository_node_id
         WHERE e.lifecycle='pending' AND (e.kind='lifecycle' OR (e.kind='mention' AND e.detail='direct_contact'))
           AND w.kind=?1 AND e.detail IN ('closed','reopened','direct_contact')
           AND (e.detail!='direct_contact' OR (EXISTS(SELECT 1 FROM assignments a WHERE a.work_item_node_id=w.node_id AND a.lifecycle='sleeping')
             AND NOT EXISTS(SELECT 1 FROM assignments a WHERE a.work_item_node_id=w.node_id AND a.lifecycle IN ('materializing','active','finalizing','stopping'))))
         ORDER BY e.observed_at,e.event_id LIMIT ?2",
    )?;
    let rows = statement.query_map(params![work_item_kind, limit], |row| {
        Ok(WorkItemLifecycleCandidate {
            event_id: row.get(0)?,
            action: row.get(1)?,
            repository: row.get(2)?,
            work_item_kind: row.get(3)?,
            number: sqlite_i64_to_u64(row.get(4)?, "lifecycle Work Item number")?,
        })
    })?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn prepare_work_item_closure(database: &Path, event_id: &str) -> Result<bool, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let candidate = transaction.query_row(
        "SELECT e.work_item_node_id,w.state,e.writer_group FROM events e
         JOIN work_items w ON w.node_id=e.work_item_node_id
         WHERE e.event_id=?1 AND e.lifecycle='pending' AND e.detail='closed'",
        [event_id], |row| Ok((row.get::<_,String>(0)?,row.get::<_,String>(1)?,row.get::<_,Option<String>>(2)?)),
    ).optional()?;
    let Some((node, state, writer)) = candidate else { return Ok(false) };
    if !matches!(state.as_str(), "CLOSED" | "MERGED") {
        transaction.execute("UPDATE events SET lifecycle='superseded' WHERE event_id=?1", [event_id])?;
        transaction.commit()?;
        return Ok(false);
    }
    let owner = transaction.query_row(
        "SELECT ai.agent_id,a.lifecycle,a.member_login,a.assignment_revision
         FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         JOIN local_items l ON l.node_id=a.work_item_node_id AND l.assignment_revision=a.assignment_revision
         WHERE a.work_item_node_id=?1 AND a.lifecycle IN ('active','finalizing','materializing','sleeping')
         ORDER BY a.generation DESC LIMIT 1",
        [&node], |row| Ok((row.get::<_,String>(0)?,row.get::<_,String>(1)?,row.get::<_,Option<String>>(2)?,row.get::<_,i64>(3)?)),
    ).optional()?;
    let Some((agent, lifecycle, login, revision)) = owner else {
        transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1", [event_id])?;
        transaction.commit()?;
        return Ok(false);
    };
    if writer.as_deref() == Some(&agent) {
        // The author already observed its own close. Preserve its current
        // execution and actual incoming messages; closing does not add a turn.
        transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1", [event_id])?;
        sleep_closed_idle_agent(&transaction, &agent)?;
        transaction.commit()?;
        return Ok(false);
    }
    if lifecycle == "materializing" { return Ok(false) }
    // External close is ordinary input. Reuse the existing address/reactivation
    // path for a sleeping member rather than introducing a finalization phase.
    transaction.execute(
        "UPDATE events SET kind=?2,detail=?3,recipient_login=?4,recipient_revision=?5 WHERE event_id=?1",
        params![event_id,if lifecycle == "sleeping" {"mention"} else {"wake"},
            if lifecycle == "sleeping" {Some("direct_contact")} else {None},login,revision],
    )?;
    if lifecycle != "sleeping" {
        schedule_event(&transaction, &node, event_id,
            SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, false, &now)?;
    }
    transaction.commit()?;
    Ok(true)
}

/// Responsibility survives object closure. Only an idle member with no real
/// input sleeps; late addressed messages use the existing reactivation path.
fn sleep_closed_idle_agent(transaction: &rusqlite::Transaction<'_>, agent: &str) -> Result<(), StoreError> {
    let can_sleep: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id
         WHERE ai.agent_id=?1 AND a.lifecycle IN ('active','finalizing') AND w.state IN ('CLOSED','MERGED')
           AND ai.lifecycle IN ('idle','finalizing')
           AND NOT EXISTS(SELECT 1 FROM provider_sessions ps JOIN turns t ON t.session_id=ps.session_id
                          WHERE ps.agent_id=ai.agent_id AND t.lifecycle IN ('starting','running'))
           AND NOT EXISTS(SELECT 1 FROM context_resets cr WHERE cr.agent_id=ai.agent_id AND cr.lifecycle IN ('interrupting','materializing'))
           AND NOT EXISTS(SELECT 1 FROM events e WHERE e.work_item_node_id=w.node_id AND e.lifecycle='pending'
                          AND NOT (e.kind='lifecycle' AND e.detail='closed' AND e.writer_group IS ai.agent_id)
                          AND NOT (e.kind='mention' AND e.detail='direct_contact'
                            AND NOT EXISTS(SELECT 1 FROM wake_batch_events be WHERE be.event_id=e.event_id))))",
        [agent], |row| row.get(0),
    )?;
    if can_sleep {
        transaction.execute("UPDATE provider_sessions SET lifecycle='sleeping' WHERE agent_id=?1 AND lifecycle='idle'", [agent])?;
        transaction.execute("UPDATE assignments SET lifecycle='sleeping' WHERE assignment_id=(SELECT assignment_id FROM agent_instances WHERE agent_id=?1)", [agent])?;
        transaction.execute("UPDATE agent_instances SET lifecycle='sleeping' WHERE agent_id=?1", [agent])?;
        transaction.execute("UPDATE worktrees SET lifecycle='sleeping' WHERE agent_id=?1 AND lifecycle='active'", [agent])?;
    }
    Ok(())
}

#[allow(clippy::too_many_lines)]
fn begin_work_item_reactivation(
    database: &Path,
    event_id: &str,
    profile_id: &str,
) -> Result<Option<AgentMaterialization>, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    if local_delivery_closed(&transaction)? { return Ok(None) }
    let candidate = transaction
        .query_row(
            "SELECT e.work_item_node_id,w.state,e.detail,l.desired_profile_id,e.recipient_revision,l.assignment_revision
             FROM events e
             JOIN work_items w ON w.node_id=e.work_item_node_id
             JOIN local_items l ON l.node_id=w.node_id
             WHERE e.event_id=?1 AND e.lifecycle='pending' AND w.kind IN ('issue','pr','review')",
            [event_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, Option<String>>(2)?,
                    row.get::<_, Option<String>>(3)?,
                    row.get::<_, Option<i64>>(4)?,
                    row.get::<_, i64>(5)?,
                ))
            },
        )
        .optional()?;
    let Some((work_item_node_id, state, detail, desired_profile, recipient_revision, current_revision)) = candidate else {
        transaction.commit()?;
        return Ok(None);
    };
    if desired_profile.as_deref() != Some(profile_id) {
        transaction.commit()?;
        return Ok(None);
    }
    let reopening = detail.as_deref() == Some("reopened") && state.eq_ignore_ascii_case("open");
    let contact = detail.as_deref() == Some("direct_contact");
    if contact && recipient_revision.is_some_and(|revision| revision != current_revision) {
        transaction.execute("UPDATE events SET lifecycle='superseded' WHERE event_id=?1 AND lifecycle='pending'", [event_id])?;
        transaction.execute("UPDATE local_comment_delivery SET status='unreachable',reason='recipient assignment changed' WHERE event_id=?1 AND status='queued'", [event_id])?;
        transaction.commit()?;
        return Ok(None);
    }
    if !reopening && !contact {
        transaction.execute(
            "UPDATE events SET lifecycle='superseded' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
        transaction.commit()?;
        return Ok(None);
    }
    // Reactivation is idempotent: a group that is already materializing,
    // active, or finalizing (for example after a trusted mention activated a
    // fresh generation before the reopen arrived) needs no revival. Consuming
    // the event here prevents a stale sleeping generation from colliding with
    // the unique active-assignment index.
    let busy = transaction
        .query_row(
            "SELECT 1 FROM assignments
             WHERE work_item_node_id=?1
               AND lifecycle IN ('materializing','active','finalizing') LIMIT 1",
            [&work_item_node_id],
            |_| Ok(()),
        )
        .optional()?
        .is_some();
    if busy {
        if reopening {
            transaction.execute(
                "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
                [event_id],
            )?;
        }
        transaction.commit()?;
        return Ok(None);
    }
    let selected = transaction
        .query_row(
            "SELECT a.assignment_id,ai.agent_id,a.generation,a.assignment_revision,ai.profile_id,ai.profile_revision,
                    COALESCE(a.member_login,'历史成员'),wt.path,wt.head_ref,
                    ps.provider_session_id,ps.context_revision,ps.instruction_revision,ps.provider_kind
             FROM assignments a
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
             JOIN local_items l ON l.node_id=a.work_item_node_id
             LEFT JOIN worktrees wt ON wt.agent_id=ai.agent_id
               AND wt.lifecycle IN ('active','sleeping')
             LEFT JOIN provider_sessions ps ON ps.agent_id=ai.agent_id AND ps.lifecycle='sleeping'
             WHERE a.work_item_node_id=?1 AND a.lifecycle='sleeping' AND ai.lifecycle='sleeping'
               AND l.desired_profile_id=ai.profile_id AND l.assignment_revision=a.assignment_revision
               AND (?2=0 OR a.member_login=(SELECT recipient_login FROM events WHERE event_id=?3))
             ORDER BY a.generation DESC LIMIT 1",
            params![work_item_node_id, i64::from(contact), event_id],
            |row| {
                Ok(AgentMaterialization {
                    assignment_id: row.get(0)?,
                    agent_id: row.get(1)?,
                    work_item_node_id: work_item_node_id.clone(),
                    generation: sqlite_i64_to_u64(row.get(2)?, "reactivation generation")?,
                    assignment_revision: sqlite_i64_to_u64(row.get(3)?, "assignment revision")?,
                    profile_id: row.get(4)?,
                    profile_revision: sqlite_i64_to_u64(
                        row.get(5)?,
                        "reactivation Profile revision",
                    )?,
                    member_login: row.get(6)?,
                    worktree_path: row.get::<_, Option<String>>(7)?.map(PathBuf::from),
                    worktree_head_ref: row.get(8)?,
                    description_event_ids: Vec::new(),
                    sleeping_session: row.get::<_, Option<String>>(9)?.map(|id| {
                        Ok::<_, rusqlite::Error>(SleepingProviderSession {
                            id,
                            context_revision: row.get(10)?,
                            instruction_revision: row.get(11)?,
                            provider_kind: row.get(12)?,
                        })
                    }).transpose()?,
                })
            },
        )
        .optional()?;
    let Some(mut materialization) = selected else {
        // No revivable generation: either there is no group, the group is
        // busy (handled above) or active, or every generation is in a
        // terminal/unselectable state (blocked, retired, or diverged through
        // operator surgery — the finalization transaction transitions
        // assignment and agent atomically, so real data cannot diverge).
        // Selection is deterministic on durable state, so retrying would
        // wedge the event as pending forever; consume it as a no-op. A later
        // trusted mention can still activate a fresh generation (the unique
        // active-assignment index only excludes materializing/active).
        transaction.execute(
            "UPDATE events SET lifecycle=?2 WHERE event_id=?1 AND lifecycle='pending'",
            params![event_id,if contact {"blocked"} else {"consumed"}],
        )?;
        if contact {
            transaction.execute("UPDATE local_comment_delivery SET status='unreachable',reason='recipient session cannot be resumed' WHERE event_id=?1 AND status='queued'", [event_id])?;
        }
        transaction.commit()?;
        return Ok(None);
    };
    // Capture only this assignment's unapplied description changes. Other
    // pending inputs, including contacts in the same batch, retain their obligations.
    materialization.description_event_ids = {
        let mut statement = transaction.prepare(
            "SELECT e.event_id FROM events e JOIN assignments a ON a.assignment_id=?2
             WHERE e.work_item_node_id=?1 AND e.kind='invalidate' AND e.lifecycle='pending'
               AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
               AND (e.recipient_revision=a.assignment_revision OR
                    (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))
             ORDER BY e.observed_at,e.event_id",
        )?;
        statement.query_map(params![work_item_node_id,materialization.assignment_id],
            |row| row.get::<_, String>(0))?.collect::<Result<Vec<_>, _>>()?
    };
    transaction.execute(
        "UPDATE events SET lifecycle='materializing' WHERE event_id=?1 AND lifecycle='pending'",
        [event_id],
    )?;
    transaction.execute(
        "UPDATE assignments SET lifecycle='materializing' WHERE assignment_id=?1",
        [&materialization.assignment_id],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='materializing' WHERE agent_id=?1",
        [&materialization.agent_id],
    )?;
    transaction.commit()?;
    Ok(Some(materialization))
}

#[allow(clippy::too_many_arguments)]
fn complete_work_item_reactivation(
    database: &Path,
    event_id: &str,
    materialization: &AgentMaterialization,
    provider_session_id: &str,
    binding_id: &str,
    context_revision: &str,
    instruction_revision: &str,
    policy: SchedulerPolicy,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let event_state = transaction
        .query_row("SELECT lifecycle FROM events WHERE event_id=?1", [event_id], |row| {
            row.get::<_, String>(0)
        })
        .optional()?;
    if event_state.as_deref() != Some("materializing") {
        return Err(StoreError::InvalidData(format!(
            "Work Item reopen event {event_id} is not materializing"
        )));
    }
    let resumed = materialization.sleeping_session.as_ref()
        .is_some_and(|session| session.id == provider_session_id);
    let current_assignment: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM assignments a JOIN local_items l ON l.node_id=a.work_item_node_id
         WHERE a.assignment_id=?1 AND a.assignment_revision=?2 AND l.assignment_revision=a.assignment_revision
           AND l.desired_member_login=a.member_login AND l.desired_profile_id=?3)",
        params![materialization.assignment_id,sqlite_u64(materialization.assignment_revision,"assignment revision")?,materialization.profile_id],
        |row| row.get(0),
    )?;
    if !current_assignment { return Err(StoreError::InvalidData("reactivation assignment changed".into())) }
    transaction.execute("UPDATE agent_instances SET profile_revision=(SELECT revision FROM profiles WHERE profile_id=?2) WHERE agent_id=?1",
        params![materialization.agent_id,materialization.profile_id])?;
    if resumed {
        let updated = transaction.execute(
            "UPDATE provider_sessions SET lifecycle='idle',cli_binding_id=?2,
                    resume_count=resume_count+1,last_resumed_at=?3,last_resume_error=NULL,last_resume_failed_at=NULL,
                    instruction_revision=?7
             WHERE agent_id=?1 AND provider_session_id=?4 AND lifecycle='sleeping'
               AND context_revision=?5 AND instruction_revision=?6",
            params![materialization.agent_id,binding_id,now,provider_session_id,
                materialization.sleeping_session.as_ref().unwrap().context_revision,
                materialization.sleeping_session.as_ref().unwrap().instruction_revision,instruction_revision],
        )?;
        if updated != 1 {
            return Err(StoreError::InvalidData("sleeping provider session changed during resume".into()));
        }
    } else {
        let session_id = Uuid::now_v7().to_string();
        transaction.execute(
            "UPDATE provider_sessions SET lifecycle='replaced'
             WHERE agent_id=?1 AND lifecycle IN ('sleeping','idle','unknown')",
            [&materialization.agent_id],
        )?;
        transaction.execute(
            "INSERT INTO provider_sessions(
           session_id,agent_id,provider_kind,provider_session_id,cli_binding_id,context_revision,
           instruction_revision,lifecycle,started_at
         ) VALUES (?1,?2,(SELECT p.provider_kind FROM agent_instances ai
             JOIN profiles p ON p.profile_id=ai.profile_id AND p.revision=ai.profile_revision
             WHERE ai.agent_id=?2),?3,?4,?5,?6,'idle',?7)",
            params![
                session_id,
                materialization.agent_id,
                provider_session_id,
                binding_id,
                context_revision,
                instruction_revision,
                now,
            ],
        )?;
    }
    if !resumed {
        for description in &materialization.description_event_ids {
            transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND kind='invalidate' AND lifecycle='pending'", [description])?;
        }
    }
    transaction.execute(
        "UPDATE assignments SET lifecycle='active',retired_at=NULL
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        [&materialization.assignment_id],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='idle',context_error=NULL
         WHERE agent_id=?1 AND lifecycle='materializing'",
        [&materialization.agent_id],
    )?;
    transaction.execute(
        "UPDATE worktrees SET lifecycle='active'
         WHERE agent_id=?1 AND lifecycle='sleeping'",
        [&materialization.agent_id],
    )?;
    transaction.execute(
        "UPDATE work_items SET context_revision=?2,observed_at=?3 WHERE node_id=?1",
        params![materialization.work_item_node_id, context_revision, now],
    )?;
    transaction.execute(
        "UPDATE events SET lifecycle='pending' WHERE event_id=?1 AND lifecycle='materializing'",
        [event_id],
    )?;
    let assignment_revision = sqlite_u64(materialization.assignment_revision, "assignment revision")?;
    transaction.execute(
        "UPDATE events SET lifecycle='superseded'
         WHERE work_item_node_id=?1 AND lifecycle='pending'
           AND kind='mention' AND detail='direct_contact'
           AND (recipient_login IS NOT ?2 OR
                (recipient_revision IS NOT NULL AND recipient_revision!=?3))",
        params![materialization.work_item_node_id, materialization.member_login, assignment_revision],
    )?;
    transaction.execute(
        "UPDATE local_comment_delivery SET status='unreachable',reason='recipient assignment changed'
         WHERE status='queued' AND event_id IN (
           SELECT event_id FROM events WHERE work_item_node_id=?1
             AND kind='mention' AND detail='direct_contact' AND lifecycle='superseded')",
        [&materialization.work_item_node_id],
    )?;
    schedule_event(&transaction, &materialization.work_item_node_id, event_id, policy, false, &now)?;
    // Contacts queued while the member slept or while Context materialized
    // share this wake. Keep every event/receipt distinct until input is accepted.
    let contacts = {
        let mut statement = transaction.prepare(
            "SELECT e.event_id FROM events e
             WHERE e.work_item_node_id=?1 AND e.lifecycle='pending'
               AND e.kind='mention' AND e.detail='direct_contact'
               AND e.recipient_login=?2
               AND (e.recipient_revision IS NULL OR e.recipient_revision=?3)
               AND NOT EXISTS(SELECT 1 FROM wake_batch_events be WHERE be.event_id=e.event_id)
             ORDER BY e.observed_at,e.event_id",
        )?;
        statement.query_map(
            params![materialization.work_item_node_id, materialization.member_login,
                assignment_revision],
            |row| row.get::<_, String>(0),
        )?.collect::<Result<Vec<_>, _>>()?
    };
    for contact in contacts {
        schedule_event(&transaction, &materialization.work_item_node_id, &contact, policy, false, &now)?;
    }
    transaction.commit()?;
    Ok(())
}

fn fail_work_item_reactivation(
    database: &Path,
    event_id: &str,
    assignment_id: &str,
    error: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    transaction.execute(
        "UPDATE events SET lifecycle='blocked' WHERE event_id=?1 AND lifecycle='materializing'",
        [event_id],
    )?;
    transaction.execute("UPDATE local_comment_delivery SET status='unreachable',reason=?2 WHERE event_id=?1 AND status='queued'", params![event_id,error])?;
    transaction.execute(
        "UPDATE assignments SET lifecycle='blocked',retired_at=?2
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        params![assignment_id, now],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='blocked',context_error=?2
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        params![assignment_id, error],
    )?;
    transaction.commit()?;
    Ok(())
}

fn defer_work_item_reactivation_transaction(
    transaction: &rusqlite::Transaction<'_>,
    event_id: &str,
    assignment_id: &str,
    error: &str,
) -> Result<(), StoreError> {
    let agent_id: String = transaction.query_row(
        "SELECT ai.agent_id FROM assignments a
         JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         JOIN events e ON e.work_item_node_id=a.work_item_node_id
         WHERE a.assignment_id=?1 AND e.event_id=?2
           AND a.lifecycle='materializing' AND ai.lifecycle='materializing'
           AND e.lifecycle='materializing'",
        params![assignment_id, event_id], |row| row.get(0),
    ).optional()?.ok_or_else(|| StoreError::InvalidData(format!(
        "sleeping reactivation {event_id} changed before retry"
    )))?;
    transaction.execute("UPDATE events SET lifecycle='pending' WHERE event_id=?1", [event_id])?;
    transaction.execute("UPDATE assignments SET lifecycle='sleeping' WHERE assignment_id=?1", [assignment_id])?;
    transaction.execute("UPDATE agent_instances SET lifecycle='sleeping' WHERE agent_id=?1", [&agent_id])?;
    transaction.execute("UPDATE agent_instances SET context_error=?2 WHERE agent_id=?1", params![agent_id,error])?;
    transaction.execute(
        "UPDATE provider_sessions SET last_resume_error=?2,last_resume_failed_at=?3 WHERE agent_id=?1 AND lifecycle='sleeping'",
        params![agent_id, error, now_rfc3339()],
    )?;
    Ok(())
}

fn defer_work_item_reactivation(
    database: &Path,
    event_id: &str,
    assignment_id: &str,
    error: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    defer_work_item_reactivation_transaction(&transaction, event_id, assignment_id, error)?;
    transaction.commit()?;
    Ok(())
}

fn has_lifecycle_observation(
    database: &Path,
    work_item_node_id: &str,
    action: &str,
    object_version: &str,
) -> Result<bool, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    Ok(connection
        .query_row(
            "SELECT 1
             FROM events e JOIN deliveries d ON d.delivery_guid=e.delivery_guid
             WHERE e.work_item_node_id=?1 AND e.object_version=?2
               AND e.kind='lifecycle' AND e.detail=?3 LIMIT 1",
            params![work_item_node_id, object_version, action],
            |_| Ok(()),
        )
        .optional()?
        .is_some())
}

/// Idempotently record the effective Profile revision an assignment binds.
fn upsert_profile_record(
    transaction: &rusqlite::Transaction<'_>,
    profile: &ProfileRecord,
) -> Result<(), StoreError> {
    transaction.execute(
        "INSERT INTO profiles(profile_id,revision,effective_digest,provider_kind,tags,assignee_login,assignee_description)
         VALUES (?1,?2,?3,?4,?5,?6,?7)
         ON CONFLICT(profile_id,revision) DO UPDATE SET
           effective_digest=excluded.effective_digest,
           provider_kind=excluded.provider_kind,
           tags=excluded.tags,
           assignee_login=excluded.assignee_login,
           assignee_description=excluded.assignee_description",
        params![
            profile.profile_id,
            sqlite_u64(profile.revision, "Profile revision")?,
            profile.effective_digest,
            profile.provider_kind,
            profile.tags,
            profile.assignee_login,
            profile.assignee_description,
        ],
    )?;
    Ok(())
}

/// Consume an activation event (`assign`/`mention`) that targets a non-open
/// Work Item: closed groups sleep until reopen; the event remains as consumed
/// evidence. Returns true when the event was consumed as a no-op.
fn consume_closed_activation(
    transaction: &rusqlite::Transaction<'_>,
    event_id: &str,
    work_item_state: &str,
    event_kind: &str,
) -> Result<bool, StoreError> {
    let activation =
        matches!(EventKind::from_str(event_kind), Some(EventKind::Assign | EventKind::Mention));
    if !activation || work_item_state.eq_ignore_ascii_case("open") {
        return Ok(false);
    }
    transaction.execute(
        "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
        [event_id],
    )?;
    Ok(true)
}

fn begin_agent_assignment(
    database: &Path,
    event_id: &str,
    profile: &ProfileRecord,
    context_revision: Option<&str>,
    preserve_wake_batch: bool,
) -> Result<Option<AgentMaterialization>, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    settle_unreachable_contacts(&transaction)?;
    if local_delivery_closed(&transaction)? {
        transaction.commit()?;
        return Ok(None);
    }
    let candidate = transaction
        .query_row(
            "SELECT e.work_item_node_id,w.kind,w.state,e.kind,e.detail,e.recipient_login,l.desired_profile_id,l.desired_member_login,l.assignment_revision,e.recipient_revision FROM events e
             JOIN work_items w ON w.node_id=e.work_item_node_id
             LEFT JOIN local_items l ON l.node_id=w.node_id
             WHERE e.event_id=?1 AND e.lifecycle='pending'",
            [event_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, Option<String>>(4)?,
                    row.get::<_, Option<String>>(5)?,
                    row.get::<_, Option<String>>(6)?,
                    row.get::<_, Option<String>>(7)?,
                    sqlite_i64_to_u64(row.get(8)?, "assignment revision")?,
                    row.get::<_, Option<i64>>(9)?,
                ))
            },
        )
        .optional()?;
    // Every profile driver may have observed the same pending event before the
    // selected driver consumed it. Losing that transaction race is a no-op.
    let Some((
        work_item_node_id,
        work_item_kind,
        work_item_state,
        event_kind,
        event_detail,
        recipient_login,
        desired_profile,
        desired_member_login,
        assignment_revision,
        recipient_revision,
    )) = candidate
    else {
        transaction.commit()?;
        return Ok(None);
    };
    if desired_profile.is_none() {
        transaction.execute(
            "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
        transaction.commit()?;
        return Ok(None);
    }
    if desired_profile.as_deref() != Some(profile.profile_id.as_str()) {
        transaction.commit()?;
        return Ok(None);
    }
    let direct_contact = event_kind == "mention" && event_detail.as_deref() == Some("direct_contact");
    if recipient_login.is_some() && (recipient_login != desired_member_login || recipient_revision.is_some_and(|revision| revision != assignment_revision as i64)) {
        transaction.execute(
            "UPDATE events SET lifecycle='superseded' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
        transaction.execute(
            "UPDATE local_comment_delivery SET status='unreachable',reason='recipient is no longer the assigned member' WHERE event_id=?1 AND status='queued'",
            [event_id],
        )?;
        transaction.commit()?;
        return Ok(None);
    }
    // Activation (assign/mention) applies only to open Work Items: a closed
    // Work Item's group sleeps and stays asleep until reopen. The event is
    // still consumed so the ledger carries the evidence.
    if !direct_contact && consume_closed_activation(&transaction, event_id, &work_item_state, &event_kind)? {
        transaction.commit()?;
        return Ok(None);
    }
    let stopping: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM assignments WHERE work_item_node_id=?1 AND lifecycle='stopping')",
        [&work_item_node_id], |row| row.get(0),
    )?;
    if stopping {
        // The replacement must remain queued until native teardown is proven.
        transaction.commit()?;
        return Ok(None);
    }
    let blocked_same_member: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM assignments
         WHERE work_item_node_id=?1 AND member_login=?2 AND lifecycle='blocked')",
        params![work_item_node_id, desired_member_login],
        |row| row.get(0),
    )?;
    if blocked_same_member {
        // A failed physical resume does not create a new responsibility.
        transaction.commit()?;
        return Ok(None);
    }
    let role = agent_role_for_kind(&work_item_kind)?;
    upsert_profile_record(&transaction, profile)?;
    let deferred = transaction.query_row(
        "SELECT a.assignment_id,ai.agent_id,a.generation,a.assignment_revision,ai.profile_revision,a.member_login,wt.path,wt.head_ref
         FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         LEFT JOIN worktrees wt ON wt.agent_id=ai.agent_id AND wt.lifecycle='active'
         WHERE a.work_item_node_id=?1 AND a.lifecycle='materializing' AND ai.lifecycle='materializing'
           AND a.assignment_revision=?2 AND a.member_login=?3 AND ai.profile_id=?4",
        params![work_item_node_id,sqlite_u64(assignment_revision,"assignment revision")?,desired_member_login,profile.profile_id],
        |row| Ok(AgentMaterialization {
            assignment_id: row.get(0)?, agent_id: row.get(1)?, work_item_node_id: work_item_node_id.clone(),
            generation: sqlite_i64_to_u64(row.get(2)?,"generation")?,
            assignment_revision: sqlite_i64_to_u64(row.get(3)?,"assignment revision")?,
            profile_id: profile.profile_id.clone(), profile_revision: sqlite_i64_to_u64(row.get(4)?,"profile revision")?,
            member_login: row.get(5)?, worktree_path: row.get::<_,Option<String>>(6)?.map(PathBuf::from),
            worktree_head_ref: row.get(7)?, sleeping_session: None, description_event_ids: Vec::new(),
        }),
    ).optional()?;
    if let Some(materialization) = deferred {
        transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1", [event_id])?;
        transaction.commit()?;
        return Ok(Some(materialization));
    }
    if !preserve_wake_batch {
        transaction.execute(
            "UPDATE wake_batches SET lifecycle='consumed',updated_at=?2
             WHERE work_item_node_id=?1 AND lifecycle IN ('pending','runnable')",
            params![work_item_node_id, now],
        )?;
    }
    transaction.execute("UPDATE events SET lifecycle='consumed' WHERE event_id=?1", [event_id])?;
    let active = transaction
        .query_row(
            "SELECT 1 FROM assignments
             WHERE work_item_node_id=?1 AND lifecycle IN ('materializing','active','stopping')",
            [&work_item_node_id],
            |_| Ok(()),
        )
        .optional()?
        .is_some();
    if active {
        transaction.commit()?;
        return Ok(None);
    }
    let generation = transaction.query_row(
        "SELECT COALESCE(MAX(generation),0)+1 FROM assignments WHERE work_item_node_id=?1",
        [&work_item_node_id],
        |row| sqlite_i64_to_u64(row.get(0)?, "assignment generation"),
    )?;
    let preserved: Option<(String, PathBuf, Option<String>)> = transaction
        .query_row(
            "SELECT wt.worktree_id,wt.path,wt.head_ref FROM worktrees wt
         JOIN agent_instances ai ON ai.agent_id=wt.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE a.work_item_node_id=?1 AND a.lifecycle IN ('retired','blocked')
           AND (?2!='review' OR a.assignment_revision=?3)
         ORDER BY a.generation DESC LIMIT 1",
            params![work_item_node_id,work_item_kind,sqlite_u64(assignment_revision,"assignment revision")?],
            |row| Ok((row.get(0)?, PathBuf::from(row.get::<_, String>(1)?), row.get(2)?)),
        )
        .optional()?;
    let materialization = AgentMaterialization {
        assignment_id: Uuid::now_v7().to_string(),
        agent_id: Uuid::now_v7().to_string(),
        work_item_node_id: work_item_node_id.clone(),
        generation,
        assignment_revision,
        profile_id: profile.profile_id.clone(),
        profile_revision: profile.revision,
        member_login: desired_member_login.ok_or_else(|| StoreError::InvalidData(format!("work item {work_item_node_id} has no concrete member identity")))?,
        worktree_path: preserved.as_ref().map(|(_, path, _)| path.clone()),
        worktree_head_ref: preserved.as_ref().and_then(|(_, _, head)| head.clone()),
        sleeping_session: None,
        description_event_ids: Vec::new(),
    };
    transaction.execute(
        "INSERT INTO assignments(
           assignment_id,work_item_node_id,generation,assignment_revision,member_login,lifecycle,assigned_at
         ) VALUES (?1,?2,?3,?4,?5,'materializing',?6)",
        params![
            materialization.assignment_id,
            materialization.work_item_node_id,
            sqlite_u64(materialization.generation, "assignment generation")?,
            sqlite_u64(assignment_revision, "assignment revision")?,
            materialization.member_login,
            now,
        ],
    )?;
    transaction.execute(
        "INSERT INTO agent_instances(
           agent_id,assignment_id,profile_id,profile_revision,role,lifecycle
         ) VALUES (?1,?2,?3,?4,?5,'materializing')",
        params![
            materialization.agent_id,
            materialization.assignment_id,
            materialization.profile_id,
            sqlite_u64(materialization.profile_revision, "Profile revision")?,
            role,
        ],
    )?;
    if let Some((worktree_id, _, _)) = preserved {
        transaction.execute(
            "UPDATE worktrees SET agent_id=?2,lifecycle='active',observed_at=?3 WHERE worktree_id=?1",
            params![worktree_id,materialization.agent_id,now],
        )?;
    }
    if let Some(context_revision) = context_revision {
        transaction.execute(
            "UPDATE work_items SET context_revision=?2,observed_at=?3 WHERE node_id=?1",
            params![work_item_node_id, context_revision, now],
        )?;
    }
    transaction.commit()?;
    Ok(Some(materialization))
}

/// Settle a native unassignment after its debounce window: retire the active
/// Agent Group. An in-flight turn is fenced `interrupted`; the caller
/// best-effort interrupts it through the session. The event is consumed once
/// settled; while the debounce window is open the event stays pending.
fn retire_unassigned_work_item(
    database: &Path,
    event_id: &str,
    debounce_seconds: u64,
) -> Result<UnassignmentOutcome, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let event = transaction
        .query_row(
            "SELECT work_item_node_id,observed_at FROM events
             WHERE event_id=?1 AND lifecycle='pending' AND kind='unassign'",
            [event_id],
            |row| Ok((row.get::<_, Option<String>>(0)?, row.get::<_, String>(1)?)),
        )
        .optional()?;
    let Some((work_item_node_id, observed_at)) = event else {
        transaction.commit()?;
        return Ok(UnassignmentOutcome { settled: true, provider_sessions: Vec::new() });
    };
    let observed = OffsetDateTime::parse(&observed_at, &Rfc3339)
        .map_err(|error| StoreError::InvalidData(format!("event observed_at: {error}")))?;
    let settled = (OffsetDateTime::now_utc() - observed)
        >= time::Duration::seconds(i64::try_from(debounce_seconds).unwrap_or(i64::MAX));
    if !settled {
        transaction.commit()?;
        return Ok(UnassignmentOutcome { settled: false, provider_sessions: Vec::new() });
    }
    let reassigned = if let Some(node_id) = work_item_node_id.as_deref() {
        transaction.query_row(
            "SELECT desired_profile_id IS NOT NULL OR desired_member_login IS NOT NULL FROM local_items WHERE node_id=?1",
            [node_id],
            |row| row.get::<_, bool>(0),
        )?
    } else {
        false
    };
    if reassigned {
        transaction.execute(
            "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
        transaction.commit()?;
        return Ok(UnassignmentOutcome { settled: true, provider_sessions: Vec::new() });
    }
    let active = work_item_node_id
        .as_deref()
        .map(|node_id| {
            transaction
                .query_row(
                    "SELECT a.assignment_id,ai.agent_id,a.lifecycle FROM assignments a
                     JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
                     WHERE a.work_item_node_id=?1
                       AND a.lifecycle IN ('materializing','active','finalizing','sleeping','stopping','retired')
                     ORDER BY a.generation DESC LIMIT 1",
                    [node_id],
                    |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, String>(2)?)),
                )
                .optional()
        })
        .transpose()?;
    let Some((assignment_id, agent_id, lifecycle)) = active.flatten() else {
        transaction.commit()?;
        return Ok(UnassignmentOutcome { settled: true, provider_sessions: Vec::new() });
    };
    let provider_sessions = {
        let mut statement = transaction.prepare(
            "SELECT provider_session_id FROM provider_sessions
             WHERE agent_id=?1 AND lifecycle NOT IN ('retired','replaced','blocked')",
        )?;
        statement
            .query_map([&agent_id], |row| row.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?
    };
    if !provider_sessions.is_empty() {
        transaction.execute(
            "UPDATE turns SET lifecycle='interrupted',ended_at=?2
             WHERE lifecycle IN ('starting','running')
               AND session_id IN (SELECT session_id FROM provider_sessions WHERE agent_id=?1)",
            params![agent_id, now],
        )?;
    }
    if lifecycle != "retired" || !provider_sessions.is_empty() {
        transaction.execute(
            "UPDATE provider_sessions SET lifecycle='stopping'
             WHERE agent_id=?1 AND lifecycle NOT IN ('retired','replaced','blocked')",
            [&agent_id],
        )?;
        transaction.execute(
            "UPDATE agent_instances SET lifecycle='stopping' WHERE agent_id=?1",
            [&agent_id],
        )?;
        transaction.execute(
            "UPDATE assignments SET lifecycle='stopping' WHERE assignment_id=?1",
            [&assignment_id],
        )?;
    }
    transaction.commit()?;
    Ok(UnassignmentOutcome { settled: true, provider_sessions })
}

fn finish_unassigned_work_item(database: &Path, event_id: &str) -> Result<bool, StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let work_item_node_id: Option<String> = transaction
        .query_row(
            "SELECT work_item_node_id FROM events WHERE event_id=?1 AND lifecycle='pending' AND kind='unassign'",
            [event_id],
            |row| row.get(0),
        )
        .optional()?
        .flatten();
    let Some(work_item_node_id) = work_item_node_id else {
        transaction.commit()?;
        return Ok(false);
    };
    let reassigned: bool = transaction.query_row(
        "SELECT desired_profile_id IS NOT NULL OR desired_member_login IS NOT NULL FROM local_items WHERE node_id=?1",
        [&work_item_node_id],
        |row| row.get(0),
    )?;
    if reassigned {
        transaction.execute(
            "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
        transaction.commit()?;
        return Ok(true);
    }
    let remaining: i64 = transaction.query_row(
        "SELECT count(*) FROM provider_sessions ps
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE a.work_item_node_id=?1 AND ps.lifecycle NOT IN ('retired','replaced','blocked')",
        [&work_item_node_id],
        |row| row.get(0),
    )?;
    if remaining > 0 {
        transaction.commit()?;
        return Ok(false);
    }
    let identity = transaction
        .query_row(
            "SELECT a.assignment_id,ai.agent_id
             FROM assignments a
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
             WHERE a.work_item_node_id=?1 AND a.lifecycle IN ('stopping','retired')
             ORDER BY a.generation DESC LIMIT 1",
            [&work_item_node_id],
            |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?)),
        )
        .optional()?;
    if let Some((assignment_id, agent_id)) = identity {
        transaction.execute(
            "UPDATE worktrees SET lifecycle='retired',observed_at=?2 WHERE agent_id=?1 AND lifecycle IN ('active','sleeping')",
            params![agent_id, now],
        )?;
        transaction.execute("UPDATE agent_instances SET lifecycle='retired' WHERE agent_id=?1", [&agent_id])?;
        transaction.execute(
            "UPDATE assignments SET lifecycle='retired',retired_at=?2 WHERE assignment_id=?1",
            params![assignment_id, now],
        )?;
    }
    transaction.execute(
        "UPDATE wake_batches SET lifecycle='consumed',updated_at=?2 WHERE work_item_node_id=?1 AND lifecycle IN ('pending','runnable')",
        params![work_item_node_id, now],
    )?;
    transaction.execute(
        "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
        [event_id],
    )?;
    transaction.commit()?;
    Ok(true)
}

fn ignore_assignment_event(database: &Path, event_id: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    connection.execute(
        "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'",
        [event_id],
    )?;
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn record_agent_worktree(
    database: &Path,
    materialization: &AgentMaterialization,
    repository_node_id: &str,
    path: &Path,
    source_path: &Path,
    head_ref: &str,
    local_branch: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let path = path
        .to_str()
        .ok_or_else(|| StoreError::InvalidData("worktree path is not valid UTF-8".into()))?;
    let source_path = source_path
        .to_str()
        .ok_or_else(|| StoreError::InvalidData("worktree source is not valid UTF-8".into()))?;
    if head_ref.is_empty() || local_branch.is_empty() {
        return Err(StoreError::InvalidData("worktree branch identity is empty".into()));
    }
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let inserted = connection.execute(
        "INSERT INTO worktrees(
           worktree_id,agent_id,path,repository_node_id,lifecycle,observed_at,
           source_path,head_ref,local_branch
         )
         SELECT ?1,ai.agent_id,?3,?4,'active',?5,?6,?7,?8
         FROM agent_instances ai
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id
         WHERE ai.agent_id=?2 AND ai.lifecycle='materializing'
           AND a.assignment_id=?9 AND a.lifecycle='materializing'
           AND w.repository_node_id=?4",
        params![
            Uuid::now_v7().to_string(),
            materialization.agent_id,
            path,
            repository_node_id,
            now_rfc3339(),
            source_path,
            head_ref,
            local_branch,
            materialization.assignment_id,
        ],
    )?;
    if inserted == 1 {
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!(
            "Agent {} is not awaiting a worktree",
            materialization.agent_id
        )))
    }
}

fn complete_agent_assignment(
    database: &Path,
    materialization: &AgentMaterialization,
    provider_session_id: &str,
    binding_id: &str,
    context_revision: &str,
    instruction_revision: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let role = transaction.query_row(
        "SELECT role FROM agent_instances WHERE agent_id=?1 AND lifecycle='materializing'",
        [&materialization.agent_id],
        |row| row.get::<_, String>(0),
    )?;
    if matches!(role.as_str(), "pr_implementation_agent" | "pr_reviewer_agent")
        && transaction
            .query_row(
                "SELECT 1 FROM worktrees WHERE agent_id=?1 AND lifecycle='active'",
                [&materialization.agent_id],
                |_| Ok(()),
            )
            .optional()?
            .is_none()
    {
        return Err(StoreError::InvalidData(format!(
            "PR Agent {} has no active worktree",
            materialization.agent_id
        )));
    }
    let session_id = Uuid::now_v7().to_string();
    transaction.execute(
        "INSERT INTO provider_sessions(
           session_id,agent_id,provider_kind,provider_session_id,cli_binding_id,context_revision,
           instruction_revision,lifecycle,started_at
         ) VALUES (?1,?2,(SELECT p.provider_kind FROM agent_instances ai
             JOIN profiles p ON p.profile_id=ai.profile_id AND p.revision=ai.profile_revision
             WHERE ai.agent_id=?2),?3,?4,?5,?6,'idle',?7)",
        params![
            session_id,
            materialization.agent_id,
            provider_session_id,
            binding_id,
            context_revision,
            instruction_revision,
            now,
        ],
    )?;
    let assignment = transaction.execute(
        "UPDATE assignments SET lifecycle='active'
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        [&materialization.assignment_id],
    )?;
    let agent = transaction.execute(
        "UPDATE agent_instances SET lifecycle='idle',context_error=NULL
         WHERE agent_id=?1 AND lifecycle='materializing'",
        [&materialization.agent_id],
    )?;
    if assignment != 1 || agent != 1 {
        return Err(StoreError::InvalidData(format!(
            "assignment {} is no longer materializing",
            materialization.assignment_id
        )));
    }
    transaction.commit()?;
    Ok(())
}

fn fail_agent_assignment(
    database: &Path,
    assignment_id: &str,
    error: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    transaction.execute(
        "UPDATE assignments SET lifecycle='blocked',retired_at=?2
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        params![assignment_id, now],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='blocked',context_error=?2
         WHERE assignment_id=?1 AND lifecycle='materializing'",
        params![assignment_id, error],
    )?;
    transaction.execute(
        "UPDATE worktrees SET lifecycle='blocked',observed_at=?2
         WHERE agent_id IN (SELECT agent_id FROM agent_instances WHERE assignment_id=?1)
           AND lifecycle='active'",
        params![assignment_id, now],
    )?;
    transaction.commit()?;
    Ok(())
}

fn defer_agent_assignment(database: &Path, assignment: &str, event: &str, error: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let updated = transaction.execute(
        "UPDATE events SET lifecycle='pending' WHERE event_id=?1 AND lifecycle='consumed'
         AND work_item_node_id=(SELECT work_item_node_id FROM assignments WHERE assignment_id=?2 AND lifecycle='materializing')
         AND NOT EXISTS(SELECT 1 FROM provider_sessions ps JOIN agent_instances ai ON ai.agent_id=ps.agent_id WHERE ai.assignment_id=?2)",
        params![event,assignment],
    )?;
    if updated != 1 { return Err(StoreError::InvalidData(format!("deferred assignment {assignment} changed before retry"))); }
    transaction.execute("UPDATE agent_instances SET context_error=?2 WHERE assignment_id=?1 AND lifecycle='materializing'", params![assignment,error])?;
    transaction.commit()?;
    Ok(())
}

fn set_assignment_context_pressure(
    database: &Path,
    assignment_id: &str,
    pressure: &str,
    bytes: Option<u64>,
    error: Option<&str>,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(pressure, "normal" | "soft" | "hard" | "unavailable") {
        return Err(StoreError::InvalidData(format!("invalid Context pressure {pressure}")));
    }
    let bytes = bytes.map(|value| sqlite_u64(value, "Context bytes")).transpose()?;
    let connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let updated = connection.execute(
        "UPDATE agent_instances SET context_pressure=?2,context_bytes=?3,context_error=?4
         WHERE assignment_id=?1",
        params![assignment_id, pressure, bytes, error],
    )?;
    if updated == 1 {
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!("assignment {assignment_id} has no Agent instance")))
    }
}

fn begin_context_reset(
    database: &Path,
    active_turn_id: Option<&str>,
    work_item_kind: &str,
    profile_id: &str,
) -> Result<Option<ContextResetClaim>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let claim = begin_context_reset_transaction(
        &transaction,
        active_turn_id,
        work_item_kind,
        profile_id,
        &now,
    )?;
    transaction.commit()?;
    Ok(claim)
}

fn begin_context_reset_transaction(
    transaction: &rusqlite::Transaction<'_>,
    active_turn_id: Option<&str>,
    work_item_kind: &str,
    profile_id: &str,
    now: &str,
) -> Result<Option<ContextResetClaim>, StoreError> {
    let work_item_node_id =
        context_reset_work_item(transaction, active_turn_id, work_item_kind, profile_id)?;
    let Some(work_item_node_id) = work_item_node_id else {
        return Ok(None);
    };
    let (agent_id, old_session_id, prior_revision, selected_turn_id) = transaction.query_row(
        "SELECT ai.agent_id,ps.session_id,ps.context_revision,t.turn_id
         FROM assignments a
         JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
         JOIN provider_sessions ps ON ps.agent_id=ai.agent_id
         LEFT JOIN turns t ON t.session_id=ps.session_id AND t.lifecycle='running'
         WHERE a.work_item_node_id=?1 AND a.lifecycle IN ('active','finalizing') AND ai.profile_id=?2
           AND ps.lifecycle IN ('idle','running')
         ORDER BY ps.started_at DESC LIMIT 1",
        params![work_item_node_id, profile_id],
        |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, Option<String>>(3)?,
            ))
        },
    )?;
    if active_turn_id != selected_turn_id.as_deref() {
        return Err(StoreError::InvalidData(
            "context reset active-turn precondition changed".into(),
        ));
    }
    let events = context_reset_events(transaction, &work_item_node_id)?;
    if events.is_empty() {
        return Ok(None);
    }
    let reset_id = Uuid::now_v7().to_string();
    let continuation = selected_turn_id.is_some();
    let reset_lifecycle = "interrupting";
    transaction.execute(
        "INSERT INTO context_resets(
           reset_id,agent_id,old_session_id,active_turn_id,context_revision_before,
           continuation,lifecycle,created_at,updated_at
         ) VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?8)",
        params![
            reset_id,
            agent_id,
            old_session_id,
            selected_turn_id,
            prior_revision,
            i64::from(continuation),
            reset_lifecycle,
            now,
        ],
    )?;
    for (ordinal, event_id) in events.iter().enumerate() {
        transaction.execute(
            "INSERT INTO context_reset_events(reset_id,event_id,ordinal) VALUES (?1,?2,?3)",
            params![reset_id, event_id, sqlite_usize(ordinal, "context reset event ordinal")?],
        )?;
        transaction.execute(
            "UPDATE events SET lifecycle='resetting' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
    }
    let claim = load_context_reset_claim(transaction, &reset_id)?;
    Ok(Some(claim))
}

fn context_reset_work_item(
    transaction: &rusqlite::Transaction<'_>,
    active_turn_id: Option<&str>,
    work_item_kind: &str,
    profile_id: &str,
) -> Result<Option<String>, StoreError> {
    if let Some(turn_id) = active_turn_id {
        return transaction
            .query_row(
                "SELECT w.node_id
                 FROM turns t
                 JOIN provider_sessions ps ON ps.session_id=t.session_id
                 JOIN agent_instances ai ON ai.agent_id=ps.agent_id
                 JOIN assignments a ON a.assignment_id=ai.assignment_id
                 JOIN work_items w ON w.node_id=a.work_item_node_id
                 WHERE t.turn_id=?1 AND t.lifecycle='running' AND ps.lifecycle='running'
                   AND a.lifecycle IN ('active','finalizing') AND w.kind=?2 AND ai.profile_id=?3
                   AND NOT EXISTS (
                     SELECT 1 FROM context_resets cr
                     WHERE cr.agent_id=ai.agent_id
                       AND cr.lifecycle IN ('interrupting','materializing')
                   )
                   AND EXISTS (
                     SELECT 1 FROM events e
                     WHERE e.work_item_node_id=w.node_id AND e.lifecycle='pending'
                       AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
                       AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))
                       AND e.origin!='agent'
                       AND (e.mention_candidate=0 OR e.trusted_mention=0)
                       AND (e.kind='invalidate' AND (
                         e.detail IS NOT 'cross_surface' OR EXISTS (
                           SELECT 1 FROM wake_batches wb
                           JOIN wake_batch_events be ON be.batch_id=wb.batch_id
                           WHERE be.event_id=e.event_id AND wb.lifecycle='runnable'
                         )
                       ))
                   )",
                params![turn_id, work_item_kind, profile_id],
                |row| row.get::<_, String>(0),
            )
            .optional()
            .map_err(StoreError::from);
    }
    transaction
        .query_row(
            "SELECT w.node_id
             FROM events e
             JOIN work_items w ON w.node_id=e.work_item_node_id
             JOIN assignments a ON a.work_item_node_id=w.node_id AND a.lifecycle IN ('active','finalizing')
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
             JOIN provider_sessions ps ON ps.agent_id=ai.agent_id AND ps.lifecycle='idle'
             WHERE e.lifecycle='pending' AND e.origin!='agent'
               AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
               AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))
               AND w.kind=?1 AND ai.profile_id=?2
               AND (e.mention_candidate=0 OR e.trusted_mention=0)
               AND (e.kind='invalidate' AND (
                 e.detail IS NOT 'cross_surface' OR EXISTS (
                   SELECT 1 FROM wake_batches wb
                   JOIN wake_batch_events be ON be.batch_id=wb.batch_id
                   WHERE be.event_id=e.event_id AND wb.lifecycle='runnable'
                 )
               ))
               AND NOT EXISTS (
                 SELECT 1 FROM context_resets cr
                 WHERE cr.agent_id=ai.agent_id
                   AND cr.lifecycle IN ('interrupting','materializing')
               )
             ORDER BY e.observed_at,e.event_id LIMIT 1",
            params![work_item_kind, profile_id],
            |row| row.get::<_, String>(0),
        )
        .optional()
        .map_err(StoreError::from)
}

fn context_reset_events(
    transaction: &rusqlite::Transaction<'_>, work_item_node_id: &str,
) -> Result<Vec<String>, StoreError> {
    let mut statement = transaction.prepare(
        "SELECT e.event_id FROM events e
         JOIN assignments a ON a.work_item_node_id=e.work_item_node_id AND a.lifecycle IN ('active','finalizing')
         JOIN local_items l ON l.node_id=a.work_item_node_id AND l.assignment_revision=a.assignment_revision
         WHERE e.work_item_node_id=?1 AND e.lifecycle='pending' AND e.origin!='agent'
           AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login)
           AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at))
           AND (e.mention_candidate=0 OR e.trusted_mention=0) AND e.kind='invalidate'
           AND (e.detail IS NOT 'cross_surface' OR EXISTS (
               SELECT 1 FROM wake_batches wb JOIN wake_batch_events be ON be.batch_id=wb.batch_id
               WHERE be.event_id=e.event_id AND wb.lifecycle='runnable'))
         ORDER BY e.observed_at,e.event_id",
    )?;
    let rows = statement.query_map([work_item_node_id], |row| row.get::<_, String>(0))?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn refresh_context_reset(database: &Path, reset_id: &str) -> Result<ContextResetClaim, StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let work_item: String = transaction.query_row(
        "SELECT a.work_item_node_id FROM context_resets cr
         JOIN agent_instances ai ON ai.agent_id=cr.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE cr.reset_id=?1 AND cr.lifecycle='interrupting'",
        [reset_id], |row| row.get(0),
    )?;
    let next_ordinal: i64 = transaction.query_row(
        "SELECT count(*) FROM context_reset_events WHERE reset_id=?1", [reset_id], |row| row.get(0),
    )?;
    for (index, event_id) in context_reset_events(&transaction, &work_item)?.iter().enumerate() {
        transaction.execute(
            "INSERT INTO context_reset_events(reset_id,event_id,ordinal) VALUES (?1,?2,?3)",
            params![reset_id, event_id, next_ordinal + sqlite_usize(index, "reset event ordinal")?],
        )?;
        transaction.execute(
            "UPDATE events SET lifecycle='resetting' WHERE event_id=?1 AND lifecycle='pending'",
            [event_id],
        )?;
    }
    let claim = load_context_reset_claim(&transaction, reset_id)?;
    transaction.commit()?;
    Ok(claim)
}

fn claim_context_reset_notice(
    database: &Path, kind: &str, profile: &str, available_sessions: &[String],
) -> Result<Option<TurnClaim>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(kind)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let selected: Option<(String, Option<String>)> = transaction.query_row(
        "SELECT cr.reset_id,cr.active_turn_id FROM context_resets cr
         JOIN provider_sessions ps ON ps.session_id=cr.old_session_id
         JOIN agent_instances ai ON ai.agent_id=cr.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id
         LEFT JOIN turns t ON t.turn_id=cr.active_turn_id
         WHERE cr.lifecycle='interrupting'
           AND (cr.active_turn_id IS NULL OR t.lifecycle='deferred')
           AND ps.lifecycle='idle' AND ai.profile_id=?2 AND w.kind=?1
           AND ps.provider_session_id IN (SELECT value FROM json_each(?3))
           AND a.lifecycle IN ('active','finalizing')
         ORDER BY cr.created_at,cr.reset_id LIMIT 1",
        params![kind, profile, serde_json::to_string(available_sessions).expect("session IDs serialize")],
        |row| Ok((row.get(0)?, row.get(1)?)),
    ).optional()?;
    let Some((reset_id, pending_turn_id)) = selected else { return Ok(None) };
    let reset = load_context_reset_claim(&transaction, &reset_id)?;
    let session_id: String = transaction.query_row(
        "SELECT old_session_id FROM context_resets WHERE reset_id=?1", [&reset_id], |row| row.get(0),
    )?;
    let revision: String = transaction.query_row(
        "SELECT context_revision FROM provider_sessions WHERE session_id=?1", [&session_id], |row| row.get(0),
    )?;
    let turn_id = if let Some(turn_id) = pending_turn_id {
        transaction.execute("UPDATE turns SET lifecycle='starting' WHERE turn_id=?1 AND lifecycle='deferred'", [&turn_id])?;
        turn_id
    } else {
        let turn_id = Uuid::now_v7().to_string();
        transaction.execute(
            "INSERT INTO turns(turn_id,session_id,context_revision,trigger_kind,lifecycle)
             VALUES (?1,?2,?3,'context_reset_notice','starting')",
            params![turn_id, session_id, revision],
        )?;
        transaction.execute(
            "UPDATE context_resets SET active_turn_id=?2,updated_at=?3 WHERE reset_id=?1",
            params![reset_id, turn_id, now_rfc3339()],
        )?;
        turn_id
    };
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='running' WHERE session_id=?1",
        [&session_id],
    )?;
    transaction.commit()?;
    Ok(Some(TurnClaim {
        turn_id,
        batch_id: String::new(),
        provider_session_id: reset.old_provider_session_id,
        repository: reset.repository,
        work_item_kind: reset.work_item_kind,
        number: reset.number,
        profile_id: reset.profile_id,
        references: reset.changes.into_iter().map(|change| change.reference).collect(),
        steer_event_ids: Vec::new(),
        trusted_mention: false,
        trigger_kind: "context_reset_notice".into(),
        reset_id: Some(reset_id),
    }))
}

fn defer_context_reset_notice(
    database: &Path, reset_id: &str, turn_id: &str, lifecycle: &str, reason: Option<&str>,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(lifecycle, "completed" | "retry") {
        return Err(StoreError::InvalidData("invalid reset notice disposition".into()));
    }
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let session_id: String = transaction.query_row(
        "SELECT cr.old_session_id FROM context_resets cr WHERE cr.reset_id=?1
         AND cr.active_turn_id=?2 AND cr.lifecycle='interrupting'",
        params![reset_id, turn_id], |row| row.get(0),
    )?;
    let changed = if lifecycle == "retry" {
        let reason = reason.ok_or_else(|| StoreError::InvalidData("missing deferred input reason".into()))?;
        let now = now_rfc3339();
        transaction.execute(
            "UPDATE turns SET lifecycle='deferred',deferred_reason=?2,
               first_deferred_at=COALESCE(first_deferred_at,?3),last_deferred_at=?3,
               deferred_count=deferred_count+1
             WHERE turn_id=?1 AND lifecycle='starting' AND provider_turn_id IS NULL",
            params![turn_id, reason, now],
        )?
    } else {
        transaction.execute(
            "UPDATE turns SET lifecycle='completed',ended_at=?2 WHERE turn_id=?1 AND lifecycle='running'",
            params![turn_id, now_rfc3339()],
        )?
    };
    if changed != 1 { return Err(StoreError::InvalidData(format!("turn {turn_id} cannot be deferred"))) }
    remove_turn_rocket(&transaction, turn_id, &now_rfc3339())?;
    transaction.execute("UPDATE provider_sessions SET lifecycle='idle' WHERE session_id=?1", [&session_id])?;
    if lifecycle == "completed" {
        transaction.execute(
            "UPDATE context_resets SET active_turn_id=NULL,updated_at=?2 WHERE reset_id=?1",
            params![reset_id, now_rfc3339()],
        )?;
    }
    transaction.commit()?;
    Ok(())
}

fn recover_context_resets(database: &Path, kind: &str, profile: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(kind)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let resets = {
        let mut statement = transaction.prepare(
            "SELECT cr.reset_id,cr.active_turn_id,cr.old_session_id,cr.agent_id FROM context_resets cr
             JOIN agent_instances ai ON ai.agent_id=cr.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             LEFT JOIN turns pending ON pending.turn_id=cr.active_turn_id
             WHERE cr.lifecycle='interrupting' AND w.kind=?1 AND ai.profile_id=?2
               AND (cr.active_turn_id IS NULL OR pending.lifecycle!='deferred')",
        )?;
        statement
            .query_map(params![kind, profile], |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, Option<String>>(1)?,
                    row.get::<_, String>(2)?, row.get::<_, String>(3)?))
            })?
            .collect::<Result<Vec<_>, _>>()?
    };
    for (reset, turn, session, agent) in resets {
        if let Some(turn) = turn {
            transaction.execute(
                "UPDATE turns SET lifecycle='unknown',ended_at=?2 WHERE turn_id=?1 AND lifecycle IN ('starting','running')",
                params![turn, now_rfc3339()],
            )?;
        }
        transaction.execute(
            "UPDATE context_resets SET lifecycle='blocked',error='old session ended before reset notice was verified',updated_at=?2 WHERE reset_id=?1",
            params![reset, now_rfc3339()],
        )?;
        transaction.execute(
            "UPDATE agent_instances SET lifecycle='blocked',context_error='old session ended before reset notice was verified' WHERE agent_id=?1",
            [&agent],
        )?;
        transaction.execute("UPDATE provider_sessions SET lifecycle='blocked' WHERE session_id=?1", [&session])?;
    }
    transaction.commit()?;
    Ok(())
}

fn ready_context_reset(
    database: &Path,
    work_item_kind: &str,
    profile_id: &str,
) -> Result<Option<ContextResetClaim>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let connection = open_read_only(database)?;
    let reset_id = connection
        .query_row(
            "SELECT cr.reset_id FROM context_resets cr
             JOIN agent_instances ai ON ai.agent_id=cr.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             WHERE cr.lifecycle='materializing' AND w.kind=?1 AND ai.profile_id=?2
             ORDER BY cr.created_at,cr.reset_id LIMIT 1",
            params![work_item_kind, profile_id],
            |row| row.get::<_, String>(0),
        )
        .optional()?;
    reset_id.map(|reset_id| load_context_reset_claim(&connection, &reset_id)).transpose()
}

fn load_context_reset_claim(
    connection: &Connection,
    reset_id: &str,
) -> Result<ContextResetClaim, StoreError> {
    let mut claim = connection.query_row(
        "SELECT cr.reset_id,a.assignment_id,r.name_with_owner,w.kind,w.number,ai.profile_id,a.member_login,
                cr.active_turn_id,t.provider_turn_id,
                wt.path,wt.head_ref,ps.provider_session_id
         FROM context_resets cr
         JOIN provider_sessions ps ON ps.session_id=cr.old_session_id
         JOIN agent_instances ai ON ai.agent_id=cr.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN work_items w ON w.node_id=a.work_item_node_id
         JOIN repositories r ON r.node_id=w.repository_node_id
         LEFT JOIN worktrees wt ON wt.agent_id=ai.agent_id AND wt.lifecycle='active'
         LEFT JOIN turns t ON t.turn_id=cr.active_turn_id
         WHERE cr.reset_id=?1",
        [reset_id],
        |row| {
            Ok(ContextResetClaim {
                old_provider_session_id: row.get(11)?,
                reset_id: row.get(0)?,
                assignment_id: row.get(1)?,
                repository: row.get(2)?,
                work_item_kind: row.get(3)?,
                number: sqlite_i64_to_u64(row.get(4)?, "context reset Work Item number")?,
                profile_id: row.get(5)?,
                member_login: row.get(6)?,
                active_turn_id: row.get(7)?,
                provider_turn_id: row.get(8)?,
                changes: Vec::new(),
                worktree_path: row.get::<_, Option<String>>(9)?.map(PathBuf::from),
                worktree_head_ref: row.get(10)?,
            })
        },
    )?;
    let mut statement = connection.prepare(
        "SELECT e.reference,a.member_login,coalesce(e.writer_group=cr.agent_id,0)
         FROM context_reset_events cre
         JOIN context_resets cr ON cr.reset_id=cre.reset_id
         JOIN events e ON e.event_id=cre.event_id
         LEFT JOIN agent_instances ai ON ai.agent_id=e.writer_group
         LEFT JOIN assignments a ON a.assignment_id=ai.assignment_id
         WHERE cre.reset_id=?1 ORDER BY cre.ordinal",
    )?;
    claim.changes = statement
        .query_map([reset_id], |row| Ok(ContextResetChange {
            reference: row.get(0)?,
            author: row.get(1)?,
            own_edit: row.get::<_, i64>(2)? != 0,
        }))?
        .collect::<Result<Vec<_>, _>>()?;
    Ok(claim)
}

fn mark_context_reset_turn_terminal(
    database: &Path,
    reset_id: &str,
    turn_id: &str,
    lifecycle: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(lifecycle, "completed" | "interrupted" | "failed" | "unknown") {
        return Err(StoreError::InvalidData(format!("invalid reset turn terminal {lifecycle}")));
    }
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    settle_context_reset_terminal(&transaction, reset_id, turn_id, lifecycle, &now)?;
    transaction.commit()?;
    Ok(())
}

fn settle_context_reset_terminal(
    transaction: &rusqlite::Transaction<'_>,
    reset_id: &str,
    turn_id: &str,
    lifecycle: &str,
    now: &str,
) -> Result<(), StoreError> {
    let reset_matches = transaction
        .query_row(
            "SELECT 1 FROM context_resets
             WHERE reset_id=?1 AND active_turn_id=?2 AND lifecycle='interrupting'",
            params![reset_id, turn_id],
            |_| Ok(()),
        )
        .optional()?
        .is_some();
    if !reset_matches {
        return Err(StoreError::InvalidData(format!(
            "context reset {reset_id} is not interrupting turn {turn_id}"
        )));
    }
    let updated = transaction.execute(
        "UPDATE turns SET lifecycle=?2,ended_at=?3
         WHERE turn_id=?1 AND lifecycle IN ('starting','running')",
        params![turn_id, lifecycle, now],
    )?;
    if updated != 1 {
        return Err(StoreError::InvalidData(format!("turn {turn_id} is not active")));
    }
    remove_turn_rocket(transaction, turn_id, now)?;
    transaction.execute(
        "UPDATE context_resets SET lifecycle='materializing',updated_at=?2
         WHERE reset_id=?1 AND lifecycle='interrupting'",
        params![reset_id, now],
    )?;
    let (session_id, agent_id): (String, String) = transaction.query_row(
        "SELECT old_session_id,agent_id FROM context_resets WHERE reset_id=?1",
        [reset_id], |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    transaction.execute("UPDATE provider_sessions SET lifecycle='reset_pending' WHERE session_id=?1", [&session_id])?;
    transaction.execute("UPDATE agent_instances SET lifecycle='reset_pending' WHERE agent_id=?1", [&agent_id])?;
    Ok(())
}

fn complete_context_reset(
    database: &Path,
    reset_id: &str,
    provider_session_id: &str,
    binding_id: &str,
    context_revision: &str,
    instruction_revision: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let (agent_id, old_session_id, work_item_node_id) = transaction
        .query_row(
            "SELECT cr.agent_id,cr.old_session_id,a.work_item_node_id
             FROM context_resets cr
             JOIN agent_instances ai ON ai.agent_id=cr.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN local_items l ON l.node_id=a.work_item_node_id
             WHERE cr.reset_id=?1 AND cr.lifecycle='materializing'
               AND a.lifecycle IN ('active','finalizing','blocked')
               AND l.desired_profile_id=ai.profile_id
               AND l.desired_member_login=a.member_login
               AND l.assignment_revision=a.assignment_revision",
            [reset_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                ))
            },
        )
        .optional()?
        .ok_or_else(|| {
            StoreError::InvalidData(format!("context reset {reset_id} is not materializing"))
        })?;
    // The original turn may have finished before the reset notice. Its durable
    // terminal, rather than the reset's begin-time guess, decides whether work
    // still needs a continuation after the Context has been replaced.
    let prior_turn: Option<String> = transaction.query_row(
        "SELECT lifecycle FROM turns WHERE session_id=?1 AND trigger_kind!='context_reset_notice'
         ORDER BY turn_id DESC LIMIT 1",
        [&old_session_id],
        |row| row.get(0),
    ).optional()?;
    let continuation = matches!(prior_turn.as_deref(), Some("interrupted" | "failed" | "unknown"));
    let new_session_id = Uuid::now_v7().to_string();
    transaction.execute(
        "INSERT INTO provider_sessions(
           session_id,agent_id,provider_kind,provider_session_id,cli_binding_id,context_revision,
           instruction_revision,lifecycle,started_at
         ) VALUES (?1,?2,(SELECT p.provider_kind FROM agent_instances ai
             JOIN profiles p ON p.profile_id=ai.profile_id AND p.revision=ai.profile_revision
             WHERE ai.agent_id=?2),?3,?4,?5,?6,'idle',?7)",
        params![
            new_session_id,
            agent_id,
            provider_session_id,
            binding_id,
            context_revision,
            instruction_revision,
            now,
        ],
    )?;
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='replaced' WHERE session_id=?1",
        [&old_session_id],
    )?;
    transaction.execute(
        "UPDATE assignments SET lifecycle=CASE
           WHEN (SELECT state FROM work_items WHERE node_id=assignments.work_item_node_id)='OPEN'
           THEN 'active' ELSE 'finalizing' END,retired_at=NULL
         WHERE assignment_id=(SELECT assignment_id FROM agent_instances WHERE agent_id=?1)
           AND lifecycle='blocked'",
        [&agent_id],
    )?;
    transaction
        .execute("UPDATE agent_instances SET lifecycle=CASE WHEN (SELECT lifecycle FROM assignments WHERE assignment_id=agent_instances.assignment_id)='finalizing' THEN 'finalizing' ELSE 'idle' END WHERE agent_id=?1", [&agent_id])?;
    transaction.execute(
        "UPDATE work_items SET context_revision=?2,observed_at=?3 WHERE node_id=?1",
        params![work_item_node_id, context_revision, now],
    )?;
    transaction.execute(
        "UPDATE context_resets SET new_session_id=?2,context_revision_after=?3,
           continuation=?4,lifecycle='applied',updated_at=?5 WHERE reset_id=?1",
        params![reset_id, new_session_id, context_revision, i64::from(continuation), now],
    )?;
    let event_ids = {
        let mut statement = transaction.prepare(
            "SELECT event_id FROM context_reset_events WHERE reset_id=?1 ORDER BY ordinal",
        )?;
        statement
            .query_map([reset_id], |row| row.get::<_, String>(0))?
            .collect::<Result<Vec<_>, _>>()?
    };
    if continuation {
        // Invalidation has been applied, so its events stay historical. A new
        // Wake continues the accepted work without re-invalidating the session
        // or trying to rebind an event that already belongs to an old batch.
        let references = event_ids.iter().map(|id| transaction.query_row(
            "SELECT reference FROM events WHERE event_id=?1", [id], |row| row.get::<_,String>(0),
        )).collect::<Result<Vec<_>,_>>()?;
        let reference = references.join("\n");
        let continuation_id = Uuid::now_v7().to_string();
        transaction.execute(
            "INSERT INTO events(event_id,work_item_node_id,kind,detail,origin,reference,lifecycle,dedupe_key,observed_at)
             VALUES(?1,?2,'wake','reset_continuation','local',?3,'pending',?4,?5)",
            params![continuation_id,work_item_node_id,reference,format!("reset-continuation:{reset_id}"),now],
        )?;
        schedule_event(&transaction, &work_item_node_id, &continuation_id,
            SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, true, &now)?;
    } else {
        transaction.execute(
            "UPDATE wake_batches SET lifecycle='consumed',updated_at=?2
             WHERE lifecycle IN ('pending','runnable')
               AND EXISTS (
                 SELECT 1 FROM wake_batch_events be
                 JOIN context_reset_events cre ON cre.event_id=be.event_id
                 WHERE be.batch_id=wake_batches.batch_id AND cre.reset_id=?1
               )
               AND NOT EXISTS (
                 SELECT 1 FROM wake_batch_events be
                 JOIN events e ON e.event_id=be.event_id
                 WHERE be.batch_id=wake_batches.batch_id AND e.lifecycle='pending'
               )",
            params![reset_id, now],
        )?;
    }
    for event_id in event_ids {
        transaction.execute(
            "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='resetting'",
            [event_id],
        )?;
    }
    transaction.commit()?;
    Ok(())
}

fn fail_context_reset(database: &Path, reset_id: &str, error: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let agent_id = transaction
        .query_row(
            "SELECT agent_id FROM context_resets
             WHERE reset_id=?1 AND lifecycle IN ('interrupting','materializing')",
            [reset_id],
            |row| row.get::<_, String>(0),
        )
        .optional()?
        .ok_or_else(|| {
            StoreError::InvalidData(format!("context reset {reset_id} is not active"))
        })?;
    transaction.execute(
        "UPDATE context_resets SET lifecycle='blocked',error=?2,updated_at=?3 WHERE reset_id=?1",
        params![reset_id, error, now],
    )?;
    transaction.execute(
        "UPDATE agent_instances SET lifecycle='blocked',context_error=?2 WHERE agent_id=?1",
        params![agent_id, error],
    )?;
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='blocked'
         WHERE session_id=(SELECT old_session_id FROM context_resets WHERE reset_id=?1)",
        [reset_id],
    )?;
    transaction.execute(
        "UPDATE events SET lifecycle='blocked' WHERE event_id IN (
           SELECT event_id FROM context_reset_events WHERE reset_id=?1
         ) AND lifecycle='resetting'",
        [reset_id],
    )?;
    transaction.commit()?;
    Ok(())
}

fn remove_turn_rocket(
    transaction: &rusqlite::Transaction<'_>,
    turn_id: &str,
    now: &str,
) -> Result<(), StoreError> {
    let target = transaction
        .query_row(
            "SELECT o.repository,o.target_kind,o.target_database_id
             FROM turns t
             JOIN wake_batch_events be ON be.batch_id=t.batch_id
             JOIN events e ON e.event_id=be.event_id AND e.trusted_mention=1
             JOIN github_write_outbox o ON o.event_id=e.event_id
             WHERE t.turn_id=?1 LIMIT 1",
            [turn_id],
            |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, String>(2)?))
            },
        )
        .optional()?;
    if let Some((repository, target_kind, target_database_id)) = target {
        enqueue_rocket_removal(transaction, &repository, &target_kind, &target_database_id, now)?;
    }
    Ok(())
}

/// A finite Local invocation stops taking new discussion work once its existing
/// delivery scope is closed. This does not classify application completeness.
pub(crate) fn local_delivery_closed(connection: &Connection) -> Result<bool, StoreError> {
    Ok(connection.query_row(
        "SELECT EXISTS(SELECT 1 FROM work_items WHERE node_id='issue:1' AND state='CLOSED')
         AND NOT EXISTS(SELECT 1 FROM work_items WHERE kind IN ('issue','pr') AND state NOT IN ('CLOSED','MERGED'))
         AND NOT EXISTS(SELECT 1 FROM review_requests WHERE status='pending')
         AND NOT EXISTS(SELECT 1 FROM local_merges m JOIN work_items w ON w.node_id=m.pr_node_id
                        WHERE m.lifecycle='prepared' OR (m.lifecycle='conflict' AND w.state='OPEN'))",
        [], |row| row.get(0),
    )?)
}

fn claim_runnable_turn(
    database: &Path,
    work_item_kind: &str,
    profile_id: &str,
    available_sessions: &[String],
) -> Result<Option<TurnClaim>, StoreError> {
    require_current_schema(database)?;
    validate_work_item_kind(work_item_kind)?;
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let selected = transaction
        .query_row(
            "SELECT b.batch_id,ps.session_id,ps.provider_session_id,
                    r.name_with_owner,w.kind,w.number,
                    ps.context_revision,ai.profile_id,a.lifecycle,w.state
             FROM wake_batches b
             JOIN work_items w ON w.node_id=b.work_item_node_id
             LEFT JOIN local_items l ON l.node_id=w.node_id
             JOIN repositories r ON r.node_id=w.repository_node_id
             JOIN assignments a ON a.work_item_node_id=w.node_id
               AND (l.assignment_revision IS NULL OR a.assignment_revision=l.assignment_revision)
               AND a.lifecycle IN ('active','finalizing')
             JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
               AND ((a.lifecycle='active' AND ai.lifecycle='idle')
                    OR (a.lifecycle='finalizing' AND ai.lifecycle='finalizing'))
             JOIN provider_sessions ps ON ps.agent_id=ai.agent_id AND ps.lifecycle='idle'
             WHERE b.lifecycle='runnable' AND w.kind=?1
               AND (?4=0 OR EXISTS(
                 SELECT 1 FROM context_resets cr
                 JOIN events e ON e.dedupe_key='reset-continuation:' || cr.reset_id
                 JOIN wake_batch_events be ON be.event_id=e.event_id
                 WHERE cr.new_session_id=ps.session_id AND cr.continuation=1
                   AND cr.lifecycle='applied' AND e.lifecycle='pending' AND be.batch_id=b.batch_id
               ) OR EXISTS (
                 SELECT 1 FROM turns prior JOIN events e ON e.dedupe_key='uncertain-continuation:' || prior.turn_id
                 JOIN wake_batch_events be ON be.event_id=e.event_id
                 WHERE prior.session_id=ps.session_id AND prior.lifecycle='unknown'
                   AND e.lifecycle='pending' AND be.batch_id=b.batch_id
               ))
               AND EXISTS (
                 SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
                 WHERE be.batch_id=b.batch_id AND e.lifecycle='pending'
               )
               AND l.desired_profile_id=ai.profile_id
               AND ai.profile_id=?2
               AND ps.provider_session_id IN (SELECT value FROM json_each(?3)) AND NOT EXISTS(SELECT 1 FROM events e WHERE e.work_item_node_id=w.node_id AND e.lifecycle='pending' AND e.kind='invalidate' AND (e.recipient_login IS NULL OR e.recipient_login=a.member_login) AND (e.recipient_revision=a.assignment_revision OR (e.recipient_revision IS NULL AND e.observed_at>=a.assigned_at)) AND (e.detail IS NOT 'cross_surface' OR EXISTS(SELECT 1 FROM wake_batch_events be JOIN wake_batches wb ON wb.batch_id=be.batch_id WHERE be.event_id=e.event_id AND wb.lifecycle='runnable')))
             ORDER BY b.created_at,b.batch_id LIMIT 1",
            params![
                work_item_kind,
                profile_id,
                serde_json::to_string(available_sessions).expect("session IDs serialize"),
                i64::from(local_delivery_closed(&transaction)?)
            ],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    sqlite_i64_to_u64(row.get(5)?, "turn Work Item number")?,
                    row.get::<_, String>(6)?,
                    row.get::<_, String>(7)?,
                    row.get::<_, String>(8)?,
                    row.get::<_, String>(9)?,
                ))
            },
        )
        .optional()?;
    let Some((
        batch_id,
        session_id,
        provider_session_id,
        repository,
        selected_work_item_kind,
        number,
        context_revision,
        profile_id,
        _assignment_lifecycle,
        work_item_state,
    )) = selected
    else {
        transaction.commit()?;
        return Ok(None);
    };
    let (references, trusted_mention) = batch_references(&transaction, &batch_id)?;
    let (assignment, reset_continuation): (bool, bool) = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
                       WHERE be.batch_id=?1 AND e.lifecycle='pending' AND e.kind='assign'),
                EXISTS(SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
                       WHERE be.batch_id=?1 AND e.lifecycle='pending' AND e.detail='reset_continuation')",
        [&batch_id],
        |row| Ok((row.get(0)?, row.get(1)?)),
    )?;
    let trigger_kind = if assignment {
        "initial_assignment"
    } else if reset_continuation {
        "reset_continuation"
    } else if work_item_state != "OPEN" {
        "terminal_contact"
    } else if trusted_mention {
        "trusted_mention"
    } else {
        "wake_batch"
    };
    let turn_id = Uuid::now_v7().to_string();
    transaction.execute(
        "UPDATE wake_batches SET lifecycle='consumed',updated_at=?2
         WHERE batch_id=?1 AND lifecycle='runnable'",
        params![batch_id, now],
    )?;
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle='running'
         WHERE session_id=?1 AND lifecycle='idle'",
        [&session_id],
    )?;
    transaction.execute(
        "INSERT INTO turns(
           turn_id,session_id,context_revision,trigger_kind,lifecycle,batch_id
         ) VALUES (?1,?2,?3,?4,'starting',?5)",
        params![turn_id, session_id, context_revision, trigger_kind, batch_id,],
    )?;
    transaction.execute("UPDATE events SET lifecycle='consumed' WHERE lifecycle='pending' AND event_id IN (SELECT event_id FROM wake_batch_events WHERE batch_id=?1)", [&batch_id])?;
    transaction.commit()?;
    Ok(Some(TurnClaim {
        turn_id,
        batch_id,
        provider_session_id,
        repository,
        work_item_kind: selected_work_item_kind,
        number,
        profile_id,
        references,
        steer_event_ids: Vec::new(),
        trusted_mention,
        trigger_kind: trigger_kind.into(),
        reset_id: None,
    }))
}

/// Keep the rejected attempt and original batch as evidence; retry through the
/// existing durable replay path without claiming the input was delivered.
fn defer_unstarted_turn(database: &Path, turn_id: &str, reason: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let (session, batch, work_item): (String, String, String) = transaction.query_row(
        "SELECT t.session_id,t.batch_id,b.work_item_node_id FROM turns t
         JOIN wake_batches b ON b.batch_id=t.batch_id
         WHERE t.turn_id=?1 AND t.lifecycle='starting' AND t.provider_turn_id IS NULL
           AND b.lifecycle='consumed'",
        [turn_id], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?)),
    ).optional()?.ok_or_else(|| StoreError::InvalidData(format!("turn {turn_id} cannot be deferred before acceptance")))?;
    let now = now_rfc3339();
    let events = {
        let mut statement = transaction.prepare("SELECT event_id FROM wake_batch_events WHERE batch_id=?1 ORDER BY ordinal")?;
        statement.query_map([&batch], |r| r.get::<_,String>(0))?.collect::<Result<Vec<_>,_>>()?
    };
    for event in events {
        replay_event(&transaction, &event, &work_item, "deferred-input:",
            "native input was not accepted; retrying",
            SchedulerPolicy { quiet_seconds: 1, event_threshold: 8 }, &now)?;
    }
    // Also delay an already-runnable concurrent batch, so a busy native endpoint
    // is not retried on every worker tick. Reuse Local's one-second quiet period.
    transaction.execute(
        "UPDATE wake_batches SET lifecycle='pending',quiet_deadline=?2,updated_at=?3
         WHERE work_item_node_id=?1 AND lifecycle IN ('pending','runnable')",
        params![work_item,deadline_rfc3339(1)?,now],
    )?;
    transaction.execute(
        "UPDATE turns SET lifecycle='interrupted',ended_at=?2,deferred_reason=?3,
           first_deferred_at=?2,last_deferred_at=?2,deferred_count=1 WHERE turn_id=?1",
        params![turn_id,now,reason],
    )?;
    transaction.execute("UPDATE provider_sessions SET lifecycle='idle' WHERE session_id=?1 AND lifecycle='running'", [&session])?;
    remove_turn_rocket(&transaction, turn_id, &now)?;
    transaction.commit()?;
    Ok(())
}

fn mark_turn_started(
    database: &Path,
    turn_id: &str,
    provider_turn_id: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction()?;
    let updated = transaction.execute(
        "UPDATE turns SET provider_turn_id=?2,lifecycle='running',started_at=?3
         WHERE turn_id=?1 AND lifecycle='starting'",
        params![turn_id, provider_turn_id, now_rfc3339()],
    )?;
    if updated == 1 {
        transaction.execute("UPDATE local_comment_delivery SET status='delivered' WHERE status='queued' AND event_id IN (SELECT be.event_id FROM turns t JOIN wake_batch_events be ON be.batch_id=t.batch_id WHERE t.turn_id=?1)", [turn_id])?;
        transaction.commit()?;
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!("turn {turn_id} is not starting")))
    }
}

#[allow(clippy::too_many_lines)]
fn mark_turn_terminal(database: &Path, turn_id: &str, lifecycle: &str, error: Option<&str>) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(lifecycle, "completed" | "interrupted" | "failed" | "unknown") {
        return Err(StoreError::InvalidData(format!("invalid turn terminal {lifecycle}")));
    }
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    mark_turn_terminal_transaction(&transaction, turn_id, lifecycle, &now, false)?;
    transaction.execute("UPDATE turns SET error=?2 WHERE turn_id=?1", params![turn_id, error])?;
    transaction.commit()?;
    Ok(())
}

#[allow(clippy::too_many_lines)]
fn mark_turn_terminal_transaction(
    transaction: &rusqlite::Transaction<'_>,
    turn_id: &str,
    lifecycle: &str,
    now: &str,
    offline_resume: bool,
) -> Result<(), StoreError> {
    let (
        session_id,
        _trigger_kind,
        agent_id,
        _assignment_id,
        work_item_node_id,
        work_item_kind,
        work_item_state,
        turn_batch_id,
        profile_id,
    ) = transaction
        .query_row(
            "SELECT t.session_id,t.trigger_kind,ps.agent_id,ai.assignment_id,
                    a.work_item_node_id,w.kind,w.state,t.batch_id,ai.profile_id
             FROM turns t
             JOIN provider_sessions ps ON ps.session_id=t.session_id
             JOIN agent_instances ai ON ai.agent_id=ps.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             WHERE t.turn_id=?1 AND t.lifecycle IN ('starting','running')",
            [turn_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, String>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, String>(6)?,
                    row.get::<_, Option<String>>(7)?,
                    row.get::<_, String>(8)?,
                ))
            },
        )
        .optional()?
        .ok_or_else(|| StoreError::InvalidData(format!("turn {turn_id} is not active")))?;
    // A committed invalidation wins over terminal arrival order, including
    // finalization. Keep the logical group alive until fresh input is handled.
    if let Some(reset) = begin_context_reset_transaction(
        transaction,
        Some(turn_id),
        &work_item_kind,
        &profile_id,
        now,
    )? {
        if lifecycle == "completed" {
            transaction.execute(
                "UPDATE turns SET lifecycle='completed',ended_at=?2 WHERE turn_id=?1",
                params![turn_id, now],
            )?;
            remove_turn_rocket(transaction, turn_id, now)?;
            transaction.execute("UPDATE provider_sessions SET lifecycle='idle' WHERE session_id=?1", [&session_id])?;
            transaction.execute(
                "UPDATE context_resets SET active_turn_id=NULL,updated_at=?2 WHERE reset_id=?1",
                params![reset.reset_id, now],
            )?;
        } else {
            settle_context_reset_terminal(transaction, &reset.reset_id, turn_id, lifecycle, now)?;
            if offline_resume && lifecycle == "unknown" {
                transaction.execute(
                    "UPDATE context_resets SET active_turn_id=NULL WHERE reset_id=?1",
                    [&reset.reset_id],
                )?;
            } else {
                transaction.execute(
                    "UPDATE context_resets SET lifecycle='blocked',error='turn ended without verified reset notice' WHERE reset_id=?1",
                    [&reset.reset_id],
                )?;
                transaction.execute("UPDATE agent_instances SET lifecycle='blocked' WHERE agent_id=?1", [&agent_id])?;
            }
        }
        return Ok(());
    }
    transaction.execute(
        "UPDATE turns SET lifecycle=?2,ended_at=?3 WHERE turn_id=?1",
        params![turn_id, lifecycle, now],
    )?;
    let session_lifecycle = if lifecycle == "unknown" { "unknown" } else { "idle" };
    transaction.execute(
        "UPDATE provider_sessions SET lifecycle=?2 WHERE session_id=?1",
        params![session_id, session_lifecycle],
    )?;
    // Unknown retains the native identity and original turn evidence. Only a
    // successful native resume, after proven teardown, makes input runnable.
    if lifecycle == "failed" && work_item_state.eq_ignore_ascii_case("open") {
        let already_replayed = turn_batch_id
            .as_deref()
            .map(|batch_id| {
                transaction.query_row(
                    "SELECT EXISTS(
                       SELECT 1 FROM wake_batch_events be
                       JOIN events e ON e.event_id=be.event_id
                       WHERE be.batch_id=?1 AND e.dedupe_key LIKE ?2 || '%'
                     )",
                    params![batch_id, FAILED_REPLAY_DEDUPE_PREFIX],
                    |row| row.get::<_, i64>(0),
                )
            })
            .transpose()?
            .unwrap_or(0)
            != 0;
        if !already_replayed {
            if let Some(batch_id) = turn_batch_id.as_deref() {
                let mut statement = transaction.prepare(
                    "SELECT event_id FROM wake_batch_events WHERE batch_id=?1 ORDER BY ordinal",
                )?;
                let replayed = statement
                    .query_map([&batch_id], |row| row.get::<_, String>(0))?
                    .collect::<Result<Vec<_>, _>>()?;
                drop(statement);
                for event_id in replayed {
                    replay_event(
                        transaction, &event_id, &work_item_node_id, FAILED_REPLAY_DEDUPE_PREFIX,
                        "retrying after provider failure",
                        SchedulerPolicy { quiet_seconds: 0, event_threshold: 1 }, now,
                    )?;
                }
            }
        }
    }
    if lifecycle != "unknown" {
        sleep_closed_idle_agent(transaction, &agent_id)?;
    }
    if lifecycle == "failed" {
        transaction.execute("UPDATE local_comment_delivery SET status='unreachable',reason='provider did not start this message' WHERE status='queued' AND event_id IN (SELECT be.event_id FROM turns t JOIN wake_batch_events be ON be.batch_id=t.batch_id WHERE t.turn_id=?1)", [turn_id])?;
    }
    Ok(())
}

fn claim_running_input(database: &Path, turn_id: &str) -> Result<Option<TurnClaim>, StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    if local_delivery_closed(&connection)? { return Ok(None); }
    let selected = connection
        .query_row(
            "SELECT b.batch_id,ps.provider_session_id,
                    r.name_with_owner,w.kind,w.number,ai.profile_id
             FROM turns t
             JOIN provider_sessions ps ON ps.session_id=t.session_id
             JOIN agent_instances ai ON ai.agent_id=ps.agent_id
             JOIN assignments a ON a.assignment_id=ai.assignment_id
             JOIN work_items w ON w.node_id=a.work_item_node_id
             JOIN local_items l ON l.node_id=w.node_id
             JOIN repositories r ON r.node_id=w.repository_node_id
             JOIN wake_batches b ON b.work_item_node_id=w.node_id
             WHERE t.turn_id=?1 AND t.lifecycle='running' AND ps.lifecycle='running'
               AND b.lifecycle='runnable'
               AND a.lifecycle IN ('active','finalizing')
               AND ai.lifecycle IN ('idle','running','finalizing')
               AND l.desired_member_login=a.member_login
               AND l.assignment_revision=a.assignment_revision
               AND l.desired_profile_id=ai.profile_id
               AND EXISTS(SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
                          JOIN local_items li ON li.node_id=e.work_item_node_id
                          WHERE be.batch_id=b.batch_id AND e.lifecycle='pending' AND e.kind!='invalidate'
                          AND (e.recipient_login IS NULL OR
                               (e.recipient_login=li.desired_member_login AND
                                (e.recipient_revision IS NULL OR e.recipient_revision=li.assignment_revision))))
             ORDER BY b.created_at,b.batch_id LIMIT 1",
            [turn_id],
            |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    sqlite_i64_to_u64(row.get(4)?, "steer Work Item number")?,
                    row.get::<_, String>(5)?,
                ))
            },
        )
        .optional()?;
    let Some((batch_id, provider_session_id, repository, work_item_kind, number, profile_id)) =
        selected
    else {
        return Ok(None);
    };
    let (references, trusted_mention, steer_event_ids) = batch_references_connection(&connection, &batch_id)?;
    Ok(Some(TurnClaim {
        turn_id: turn_id.into(),
        batch_id,
        provider_session_id,
        repository,
        work_item_kind,
        number,
        profile_id,
        references,
        steer_event_ids,
        trusted_mention,
        trigger_kind: "running_input".into(),
        reset_id: None,
    }))
}

fn consume_steer_batch(database: &Path, turn_id: &str, batch_id: &str, event_ids: &[String]) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if event_ids.is_empty() {
        return Err(StoreError::InvalidData("running input has no events to acknowledge".into()));
    }
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let current: bool = transaction.query_row(
        "SELECT EXISTS(SELECT 1 FROM turns t
         JOIN provider_sessions ps ON ps.session_id=t.session_id
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id
         JOIN wake_batches b ON b.work_item_node_id=a.work_item_node_id
         WHERE t.turn_id=?1 AND t.lifecycle='running' AND b.batch_id=?2 AND b.lifecycle='runnable')",
        params![turn_id, batch_id], |row| row.get(0),
    )?;
    if !current {
        return Err(StoreError::InvalidData(format!("input batch {batch_id} no longer belongs to running turn {turn_id}")));
    }
    for event_id in event_ids {
        let changed = transaction.execute(
            "UPDATE events SET lifecycle='consumed' WHERE event_id=?1 AND lifecycle='pending'
             AND EXISTS(SELECT 1 FROM wake_batch_events WHERE batch_id=?2 AND event_id=?1)",
            params![event_id, batch_id],
        )?;
        if changed != 1 {
            return Err(StoreError::InvalidData(format!("running input event {event_id} is no longer pending in batch {batch_id}")));
        }
        transaction.execute(
            "UPDATE local_comment_delivery SET status='delivered' WHERE status='queued' AND event_id=?1",
            [event_id],
        )?;
    }
    // Events added while native input was in flight stay pending in this batch.
    // Retired recipients among those unsent events were not in this input.
    transaction.execute(
        "UPDATE events SET lifecycle='superseded' WHERE lifecycle='pending' AND event_id IN
           (SELECT e.event_id FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
            JOIN local_items l ON l.node_id=e.work_item_node_id WHERE be.batch_id=?1
            AND e.recipient_login IS NOT NULL
            AND (e.recipient_login IS NOT l.desired_member_login OR
                 (e.recipient_revision IS NOT NULL AND e.recipient_revision != l.assignment_revision)))",
        [batch_id],
    )?;
    transaction.execute(
        "UPDATE local_comment_delivery SET status='unreachable',reason='recipient assignment changed'
         WHERE status='queued' AND event_id IN
           (SELECT e.event_id FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
            WHERE be.batch_id=?1 AND e.lifecycle='superseded')", [batch_id],
    )?;
    transaction.execute(
        "UPDATE wake_batches SET lifecycle='consumed',updated_at=?2 WHERE batch_id=?1
         AND NOT EXISTS(SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
                        WHERE be.batch_id=?1 AND e.lifecycle='pending')",
        params![batch_id, now_rfc3339()],
    )?;
    transaction.commit()?;
    Ok(())
}

fn batch_references(
    transaction: &rusqlite::Transaction<'_>,
    batch_id: &str,
) -> Result<(Vec<String>, bool), StoreError> {
    let mut statement = transaction.prepare(
        "SELECT e.reference,COALESCE(e.trusted_mention,0)
         FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
         JOIN local_items l ON l.node_id=e.work_item_node_id
         WHERE be.batch_id=?1 AND e.lifecycle='pending'
           AND (e.recipient_login IS NULL OR (e.recipient_login=l.desired_member_login AND (e.recipient_revision IS NULL OR e.recipient_revision=l.assignment_revision)))
         ORDER BY be.ordinal",
    )?;
    let rows = statement
        .query_map([batch_id], |row| Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)? != 0)))?;
    let values = rows.collect::<Result<Vec<_>, _>>()?;
    let trusted = values.iter().any(|value| value.1);
    Ok((values.into_iter().map(|value| value.0).collect(), trusted))
}

fn batch_references_connection(
    connection: &Connection,
    batch_id: &str,
) -> Result<(Vec<String>, bool, Vec<String>), StoreError> {
    let mut statement = connection.prepare(
        "SELECT e.event_id,e.reference,COALESCE(e.trusted_mention,0)
         FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id
         JOIN local_items l ON l.node_id=e.work_item_node_id
         WHERE be.batch_id=?1 AND e.lifecycle='pending' AND e.kind!='invalidate'
           AND (e.recipient_login IS NULL OR (e.recipient_login=l.desired_member_login AND (e.recipient_revision IS NULL OR e.recipient_revision=l.assignment_revision)))
         ORDER BY be.ordinal",
    )?;
    let rows = statement
        .query_map([batch_id], |row| Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, i64>(2)? != 0)))?;
    let values = rows.collect::<Result<Vec<_>, _>>()?;
    let trusted = values.iter().any(|value| value.2);
    let (event_ids, references): (Vec<_>, Vec<_>) = values.into_iter().map(|(id, reference, _)| (id, reference)).unzip();
    Ok((references, trusted, event_ids))
}

fn enqueue_turn_reaction(database: &Path, turn_id: &str, content: &str) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if !matches!(content, "rocket" | "+1" | "confused") {
        return Err(StoreError::InvalidData(format!("invalid turn reaction {content}")));
    }
    let now = now_rfc3339();
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction = connection.transaction()?;
    let target = transaction
        .query_row(
            "SELECT o.repository,o.target_kind,o.target_database_id
             FROM turns t
             JOIN wake_batch_events be ON be.batch_id=t.batch_id
             JOIN events e ON e.event_id=be.event_id AND e.trusted_mention=1
             JOIN github_write_outbox o ON o.event_id=e.event_id
             WHERE t.turn_id=?1 LIMIT 1",
            [turn_id],
            |row| {
                Ok((row.get::<_, String>(0)?, row.get::<_, String>(1)?, row.get::<_, String>(2)?))
            },
        )
        .optional()?;
    if let Some((repository, target_kind, target_database_id)) = target {
        if content != "rocket" {
            enqueue_rocket_removal(
                &transaction,
                &repository,
                &target_kind,
                &target_database_id,
                &now,
            )?;
        }
        let request_digest = hex::encode(Sha256::digest(
            format!("{repository}\0{target_kind}\0{target_database_id}\0{content}").as_bytes(),
        ));
        transaction.execute(
            "INSERT OR IGNORE INTO github_write_outbox(
               intent_id,repository,target_kind,target_database_id,operation,content,
               request_digest,lifecycle,next_attempt_at,created_at,updated_at
             ) VALUES (?1,?2,?3,?4,'reaction_add',?5,?6,'pending',?7,?7,?7)",
            params![
                Uuid::now_v7().to_string(),
                repository,
                target_kind,
                target_database_id,
                content,
                request_digest,
                now,
            ],
        )?;
    }
    transaction.commit()?;
    Ok(())
}

fn enqueue_operational_status(
    database: &Path,
    turn_id: &str,
    body: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    let connection = open_read_only(database)?;
    let assignment_id = connection.query_row(
        "SELECT ai.assignment_id FROM turns t
         JOIN provider_sessions ps ON ps.session_id=t.session_id
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         WHERE t.turn_id=?1",
        [turn_id],
        |row| row.get::<_, String>(0),
    )?;
    enqueue_assignment_operational_status(database, &assignment_id, body)
}

fn enqueue_assignment_operational_status(
    database: &Path,
    assignment_id: &str,
    body: &str,
) -> Result<(), StoreError> {
    require_current_schema(database)?;
    if body.trim().is_empty() {
        return Err(StoreError::InvalidData("Operational Status body is empty".into()));
    }
    let mut connection = open_read_write(database)?;
    configure_connection(&connection)?;
    let transaction =
        connection.transaction_with_behavior(rusqlite::TransactionBehavior::Immediate)?;
    let work_item_node_id: String = transaction.query_row(
        "SELECT work_item_node_id FROM assignments WHERE assignment_id=?1",
        [assignment_id],
        |row| row.get(0),
    )?;
    let latest: Option<String> = transaction
        .query_row(
            "SELECT body FROM local_comments
         WHERE work_item_node_id=?1 AND system_author='Braid' AND lifecycle='visible'
         ORDER BY comment_id DESC LIMIT 1",
            [&work_item_node_id],
            |row| row.get(0),
        )
        .optional()?;
    if latest.as_deref() != Some(body) {
        let now = now_rfc3339();
        transaction.execute(
            "INSERT INTO local_comments(work_item_node_id,body,lifecycle,system_author,created_at,updated_at)
             VALUES(?1,?2,'visible','Braid',?3,?3)",
            params![work_item_node_id, body, now],
        )?;
        let comment_id = transaction.last_insert_rowid();
        transaction.execute(
            "UPDATE local_comments SET thread_root=comment_id WHERE comment_id=?1",
            [comment_id],
        )?;
        transaction.execute(
            "INSERT INTO local_activity(work_item_node_id,occurred_at,actor_login,action,source_comment,detail)
             VALUES(?1,?2,'Braid','commented',?3,'operational status')",
            params![work_item_node_id, now, comment_id],
        )?;
    }
    transaction.commit()?;
    Ok(())
}

fn enqueue_rocket_removal(
    transaction: &rusqlite::Transaction<'_>,
    repository: &str,
    target_kind: &str,
    target_database_id: &str,
    now: &str,
) -> Result<(), StoreError> {
    transaction.execute(
        "UPDATE github_write_outbox SET lifecycle='superseded',updated_at=?4
         WHERE repository=?1 AND target_kind=?2 AND target_database_id=?3
           AND operation='reaction_add' AND content='rocket' AND lifecycle='pending'",
        params![repository, target_kind, target_database_id, now],
    )?;
    let remote = transaction
        .query_row(
            "SELECT remote_database_id FROM github_write_outbox
             WHERE repository=?1 AND target_kind=?2 AND target_database_id=?3
               AND operation='reaction_add' AND content='rocket' AND lifecycle='applied'
               AND remote_database_id IS NOT NULL
             ORDER BY updated_at DESC LIMIT 1",
            params![repository, target_kind, target_database_id],
            |row| row.get::<_, String>(0),
        )
        .optional()?;
    let Some(remote_database_id) = remote else { return Ok(()) };
    let request_digest = hex::encode(Sha256::digest(
        format!(
            "{repository}\0{target_kind}\0{target_database_id}\0reaction_delete\0{remote_database_id}"
        )
        .as_bytes(),
    ));
    transaction.execute(
        "INSERT OR IGNORE INTO github_write_outbox(
           intent_id,repository,target_kind,target_database_id,operation,content,
           request_digest,remote_database_id,lifecycle,next_attempt_at,created_at,updated_at
         ) VALUES (?1,?2,?3,?4,'reaction_delete','rocket',?5,?6,'pending',?7,?7,?7)",
        params![
            Uuid::now_v7().to_string(),
            repository,
            target_kind,
            target_database_id,
            request_digest,
            remote_database_id,
            now,
        ],
    )?;
    Ok(())
}

fn scalar_u64(connection: &Connection, query: &str) -> Result<u64, StoreError> {
    let value = connection.query_row(query, [], |row| row.get::<_, i64>(0))?;
    Ok(sqlite_i64_to_u64(value, "SQLite count")?)
}

fn validate_work_item_kind(kind: &str) -> Result<(), StoreError> {
    if matches!(kind, "issue" | "pr" | "review") {
        Ok(())
    } else {
        Err(StoreError::InvalidData(format!("unknown Work Item kind {kind}")))
    }
}

fn agent_role_for_kind(kind: &str) -> Result<&'static str, StoreError> {
    match kind {
        "issue" => Ok("issue_agent"),
        "pr" => Ok("pr_implementation_agent"),
        "review" => Ok("pr_reviewer_agent"),
        other => Err(StoreError::InvalidData(format!("unknown Work Item kind {other}"))),
    }
}

fn sqlite_u64(value: u64, name: &str) -> Result<i64, StoreError> {
    i64::try_from(value)
        .map_err(|_| StoreError::InvalidData(format!("{name} exceeds SQLite INTEGER")))
}

fn sqlite_usize(value: usize, name: &str) -> Result<i64, StoreError> {
    i64::try_from(value)
        .map_err(|_| StoreError::InvalidData(format!("{name} exceeds SQLite INTEGER")))
}

fn sqlite_i64_to_u64(value: i64, name: &str) -> Result<u64, rusqlite::Error> {
    u64::try_from(value).map_err(|error| {
        rusqlite::Error::FromSqlConversionFailure(
            0,
            rusqlite::types::Type::Integer,
            Box::new(StoreConversionError(format!("{name} is negative: {error}"))),
        )
    })
}

#[derive(Debug)]
struct StoreConversionError(String);

impl std::fmt::Display for StoreConversionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(&self.0)
    }
}

impl std::error::Error for StoreConversionError {}

fn deadline_rfc3339(seconds: u64) -> Result<String, StoreError> {
    let seconds = i64::try_from(seconds)
        .map_err(|_| StoreError::InvalidData("duration exceeds i64 seconds".into()))?;
    (OffsetDateTime::now_utc() + TimeDuration::seconds(seconds))
        .format(&Rfc3339)
        .map_err(|error| StoreError::InvalidData(format!("cannot format deadline: {error}")))
}

fn require_current_schema(database: &Path) -> Result<(), StoreError> {
    let migration_plan = plan(database)?;
    if migration_plan.current_schema == DATABASE_SCHEMA_VERSION {
        Ok(())
    } else {
        Err(StoreError::SchemaNotReady {
            found: migration_plan.current_schema,
            required: DATABASE_SCHEMA_VERSION,
        })
    }
}

struct MigrationLease {
    _file: File,
}

impl MigrationLease {
    fn acquire(database: &Path) -> Result<Self, StoreError> {
        let mut lock_name = OsString::from(database.as_os_str());
        lock_name.push(".migrate.lock");
        let path = PathBuf::from(lock_name);
        let file = OpenOptions::new()
            .create(true)
            .read(true)
            .truncate(false)
            .write(true)
            .open(&path)
            .map_err(|source| StoreError::Io { path: path.clone(), source })?;
        fs2::FileExt::try_lock_exclusive(&file).map_err(|source| {
            if source.kind() == std::io::ErrorKind::WouldBlock {
                StoreError::MigrationBusy(path.clone())
            } else {
                StoreError::Io { path: path.clone(), source }
            }
        })?;
        Ok(Self { _file: file })
    }
}

fn read_ledger(database: &Path) -> Result<Vec<LedgerEntry>, StoreError> {
    if !database.is_file() || fs::metadata(database).map_or(0, |metadata| metadata.len()) == 0 {
        return Ok(Vec::new());
    }
    let connection = open_read_only(database)?;
    let table_names = user_table_names(&connection)?;
    if !table_names.iter().any(|name| name == "schema_migrations") {
        if table_names.is_empty() {
            return Ok(Vec::new());
        }
        return Err(StoreError::ForeignDatabase { path: database.to_path_buf() });
    }
    let mut statement = connection
        .prepare("SELECT version, checksum FROM schema_migrations ORDER BY version ASC")?;
    let rows = statement
        .query_map([], |row| Ok(LedgerEntry { version: row.get(0)?, checksum: row.get(1)? }))?;
    rows.collect::<Result<Vec<_>, _>>().map_err(StoreError::from)
}

fn validate_ledger(ledger: &[LedgerEntry]) -> Result<(), StoreError> {
    if let Some(found) = ledger.last().map(|entry| entry.version)
        && found > DATABASE_SCHEMA_VERSION
    {
        return Err(StoreError::NewerSchema { found, supported: DATABASE_SCHEMA_VERSION });
    }
    for (index, entry) in ledger.iter().enumerate() {
        let expected_version = u32::try_from(index + 1).expect("migration count fits u32");
        if entry.version != expected_version {
            return Err(StoreError::NonContiguous { version: entry.version });
        }
        let migration = MIGRATIONS
            .iter()
            .find(|migration| migration.version == entry.version)
            .ok_or(StoreError::NewerSchema {
                found: entry.version,
                supported: DATABASE_SCHEMA_VERSION,
            })?;
        if entry.checksum != migration_checksum(migration) {
            return Err(StoreError::ChecksumMismatch { version: entry.version });
        }
    }
    Ok(())
}

fn apply_one(connection: &mut Connection, migration: &Migration) -> Result<(), StoreError> {
    let rebuild_parent = migration.version == 17;
    let failure = |message: String| StoreError::Migration { version: migration.version, message };
    if rebuild_parent && !connection.is_autocommit() {
        return Err(failure("work_items rebuild requires an autocommit connection".into()));
    }
    let result = (|| -> Result<(), StoreError> {
        if rebuild_parent {
            connection.execute_batch("PRAGMA foreign_keys=OFF")?;
            if connection.query_row("PRAGMA foreign_keys", [], |r| r.get::<_, i64>(0))? != 0 {
                return Err(failure("cannot disable foreign_keys before work_items rebuild".into()));
            }
        }
        connection.execute_batch("BEGIN EXCLUSIVE")?;
        connection.execute_batch(migration.sql)?;
        if rebuild_parent {
            let mut check = connection.prepare("PRAGMA foreign_key_check")?;
            let mut rows = check.query([])?;
            if let Some(row) = rows.next()? {
                return Err(failure(format!("foreign_key_check: table={}, rowid={:?}, parent={}, fk={}",
                    row.get::<_, String>(0)?, row.get::<_, Option<i64>>(1)?, row.get::<_, String>(2)?, row.get::<_, i64>(3)?)));
            }
        }
        connection.execute(
            "INSERT INTO schema_migrations(version, name, checksum, applied_at) VALUES (?1, ?2, ?3, ?4)",
            (migration.version, migration.name, migration_checksum(migration), now_rfc3339()),
        )?;
        connection.execute_batch("COMMIT")?;
        Ok(())
    })();
    if result.is_err() && !connection.is_autocommit() { let _ = connection.execute_batch("ROLLBACK"); }
    if rebuild_parent {
        connection.execute_batch("PRAGMA foreign_keys=ON").map_err(|error| failure(format!("foreign_keys restoration failed: {error}; migration result: {result:?}")))?;
        if connection.query_row("PRAGMA foreign_keys", [], |r| r.get::<_, i64>(0))? != 1 {
            return Err(failure(format!("foreign_keys restoration not confirmed; migration result: {result:?}")));
        }
    }
    result.map_err(|error| failure(error.to_string()))
}

fn create_backup(
    source: &Connection,
    backups: &Path,
    next_version: u32,
) -> Result<PathBuf, StoreError> {
    let timestamp = OffsetDateTime::now_utc().unix_timestamp_nanos();
    let target = backups.join(format!("braid.before-v{next_version}.{timestamp}.sqlite3"));
    if target.exists() {
        return Err(StoreError::BackupExists(target));
    }
    let mut destination = Connection::open(&target)?;
    let backup = Backup::new(source, &mut destination)?;
    backup.run_to_completion(16, Duration::from_millis(10), None)?;
    drop(backup);
    destination.close().map_err(|(_, error)| StoreError::Sqlite(error))?;
    Ok(target)
}

fn open_read_only(path: &Path) -> Result<Connection, StoreError> {
    Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(StoreError::from)
}

fn open_read_write(path: &Path) -> Result<Connection, StoreError> {
    Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_WRITE
            | OpenFlags::SQLITE_OPEN_CREATE
            | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .map_err(StoreError::from)
}

fn configure_connection(connection: &Connection) -> Result<(), StoreError> {
    connection.busy_timeout(Duration::from_secs(30))?;
    connection.execute_batch("PRAGMA foreign_keys=ON; PRAGMA synchronous=FULL;")?;
    Ok(())
}

fn user_table_names(connection: &Connection) -> Result<Vec<String>, StoreError> {
    let mut statement = connection.prepare(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name",
    )?;
    statement
        .query_map([], |row| row.get(0))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(StoreError::from)
}

fn migration_checksum(migration: &Migration) -> String {
    hex::encode(Sha256::digest(migration.sql.as_bytes()))
}

fn create_dir_all(path: &Path) -> Result<(), StoreError> {
    fs::create_dir_all(path).map_err(|source| StoreError::Io { path: path.to_path_buf(), source })
}

fn now_rfc3339() -> String {
    OffsetDateTime::now_utc().format(&Rfc3339).expect("UTC timestamp formats as RFC 3339")
}
