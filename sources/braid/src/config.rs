use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
};
use thiserror::Error;
#[derive(Debug, Error)]
pub enum ConfigError {
    #[error("cannot read config {path}: {source}")]
    Read { path: PathBuf, source: std::io::Error },
    #[error("invalid config: {0}")]
    Invalid(String),
}
#[derive(Clone)]
pub struct Config {
    pub repository: String,
    pub runtime: RuntimeConfig,
    pub scheduler: SchedulerConfig,
    pub tools: ToolConfig,
    pub profiles: Vec<Profile>,
    pub bindings: BTreeMap<String, RuntimeBinding>,
}
impl Config {
    pub fn profile(&self, id: &str) -> Result<&Profile, ConfigError> {
        self.profiles
            .iter()
            .find(|p| p.id == id)
            .ok_or_else(|| ConfigError::Invalid(format!("unknown profile {id}")))
    }
}
#[derive(Clone)]
pub struct RuntimeConfig {
    pub root: PathBuf,
    pub worktrees: PathBuf,
    pub offline_stopped_sessions: Vec<String>,
}
impl RuntimeConfig {
    pub fn root(&self) -> &Path {
        &self.root
    }
    pub fn worktrees(&self) -> &Path {
        &self.worktrees
    }
}
#[derive(Clone)]
pub struct ToolConfig {
    pub git: PathBuf,
}
#[derive(Clone)]
pub struct SchedulerConfig {
    pub quiet_seconds: u64,
    pub event_threshold: u32,
}
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ProviderConfig {
    pub codex: Option<CodexConfig>,
    pub pi: Option<PiConfig>,
    pub bub: Option<BubConfig>,
    #[serde(default)]
    pub bindings: BTreeMap<String, RuntimeBinding>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CodexConfig {
    pub executable: PathBuf,
    pub home: PathBuf,
    pub version: String,
    pub stable_schema_sha256: String,
    pub experimental_schema_sha256: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct PiConfig {
    pub executable: PathBuf,
    /// Process boot includes extension loading; ordinary RPCs keep their own deadline.
    #[serde(default = "default_pi_startup_timeout")]
    pub startup_timeout_seconds: u64,
    #[serde(default)]
    pub api_key_environment: Option<String>,
    #[serde(default)]
    pub api_key_file: Option<PathBuf>,
    pub home: Option<PathBuf>,
}

/// Bub with the official ACP server and session-prompt plugins installed.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct BubConfig {
    pub executable: PathBuf,
    pub home: PathBuf,
    #[serde(default = "default_pi_startup_timeout")]
    pub startup_timeout_seconds: u64,
    #[serde(default)]
    pub api_key_environment: Option<String>,
    #[serde(default)]
    pub api_key_file: Option<PathBuf>,
}

impl BubConfig {
    pub fn api_key(&self) -> Result<Option<String>, ConfigError> {
        if let Some(path) = &self.api_key_file {
            return load_provider_secret_file(path).map(Some);
        }
        self.api_key_environment.as_ref().map(|name| std::env::var(name).map_err(|_| {
            ConfigError::Invalid(format!("environment variable {name:?} for bub.api_key_environment is not set"))
        })).transpose()
    }
}

fn default_pi_startup_timeout() -> u64 { 180 }

/// The runtime material used by one ordinary Braid profile. Model and
/// reasoning intentionally live on `Profile`; this binding owns process and
/// authentication details only.
#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct RuntimeBinding {
    pub adapter_type: String,
    pub executable: PathBuf,
    #[serde(default)]
    pub api_key_environment: Option<String>,
    #[serde(default)]
    pub api_key_file: Option<PathBuf>,
    #[serde(default)]
    pub native_template: Option<PathBuf>,
    #[serde(default)]
    pub capabilities: serde_json::Value,
    #[serde(default)]
    pub native_home: NativeHomeBinding,
}

#[derive(Debug, Clone, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct NativeHomeBinding {
    #[serde(default)]
    pub root: Option<PathBuf>,
}

impl PiConfig {
    /// Load the provider API key from `api_key_file` if set, otherwise from
    /// `api_key_environment`.
    pub fn api_key(&self) -> Result<String, ConfigError> {
        if let Some(path) = &self.api_key_file {
            return load_provider_secret_file(path);
        }
        if let Some(env) = &self.api_key_environment {
            return std::env::var(env).map_err(|_| {
                ConfigError::Invalid(format!(
                    "environment variable {env:?} for provider.pi.api_key_environment is not set"
                ))
            });
        }
        Err(ConfigError::Invalid(
            "one of provider.pi.api_key_environment or provider.pi.api_key_file must be set".into(),
        ))
    }
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Profile {
    pub id: String,
    pub display_name: String,
    pub assignee_login: String,
    pub assignee_description: String,
    pub tags: Vec<String>,
    /// Locates the runtime entry that implements this profile's adapter.
    pub adapter_type: String,
    /// Contract pin checked against the runtime entry's version.
    pub adapter_version: String,
    /// Selects the native client provider configured in this profile's runtime template.
    /// An empty value keeps the native client default.
    pub provider: String,
    pub model: Option<String>,
    pub reasoning: Option<String>,
    pub user_instructions: String,
    /// Request input checkout, shared by all Profiles. During a local run this
    /// resolves to its bare origin; Agent sessions use separate clones.
    #[serde(default)]
    pub workspace: Option<PathBuf>,
    /// Model window in tokens; legacy profiles use a conservative 128k window.
    #[serde(default = "default_context_window_tokens")]
    pub context_window_tokens: usize,
    pub context_soft_ratio: f64,
    pub context_hard_bytes: usize,
}

fn default_context_window_tokens() -> usize { 128_000 }

impl Profile {
    pub fn workspace(&self) -> &Path {
        self.workspace.as_deref().expect("resolved profile workspace")
    }
    pub fn has_tag(&self, tag: &str) -> bool {
        self.tags.iter().any(|v| v == tag)
    }
    pub fn validate(&self) -> Result<(), ConfigError> {
        if self.context_window_tokens < 1024 {
            return Err(ConfigError::Invalid("context_window_tokens must be at least 1024".into()));
        }
        if !(0.0..1.0).contains(&self.context_soft_ratio) || self.context_hard_bytes == 0 {
            return Err(ConfigError::Invalid(
                "context_soft_ratio must be in (0,1) and context_hard_bytes positive".into(),
            ));
        }
        if !matches!(self.adapter_type.as_str(), "codex" | "pi" | "bub") {
            return Err(ConfigError::Invalid("adapter_type must be codex, pi or bub".into()));
        }
        let login = self.assignee_login.as_bytes();
        if login.is_empty()
            || login.len() > 39
            || !login[0].is_ascii_alphanumeric()
            || !login[login.len() - 1].is_ascii_alphanumeric()
            || login
                .iter()
                .any(|byte| !byte.is_ascii_lowercase() && !byte.is_ascii_digit() && *byte != b'-')
            || login.windows(2).any(|pair| pair == b"--")
        {
            return Err(ConfigError::Invalid(format!(
                "assignee_login {:?} must be 1-39 lowercase ASCII letters, digits, or single hyphens, without leading or trailing hyphens",
                self.assignee_login
            )));
        }
        if self.assignee_description.is_empty()
            || self.assignee_description.len() > 240
            || self.assignee_description.contains(['\n', '\r'])
        {
            return Err(ConfigError::Invalid(
                "assignee_description must be one non-empty line of at most 240 UTF-8 bytes".into(),
            ));
        }
        Ok(())
    }
}
#[derive(Deserialize)]
struct ProviderSecretFile {
    provider_api_key: String,
}
fn load_provider_secret_file(path: &Path) -> Result<String, ConfigError> {
    let text = fs::read_to_string(path)
        .map_err(|source| ConfigError::Read { path: path.to_owned(), source })?;
    let file: ProviderSecretFile =
        toml::from_str(&text).map_err(|e| ConfigError::Invalid(e.to_string()))?;
    Ok(file.provider_api_key)
}
