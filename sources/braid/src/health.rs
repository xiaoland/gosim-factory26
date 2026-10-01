//! Provider health observations sent from group workers to the local runtime.

/// Per-driver observations are aggregated before publishing provider health.
#[derive(Debug, serde::Serialize)]
pub(crate) struct ProviderHealthUpdate {
    pub(crate) group: String,
    pub(crate) error: Option<String>,
    pub(crate) can_progress: bool,
    pub(crate) waiting_for_resources: bool,
}
