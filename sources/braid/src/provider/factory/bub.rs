use super::{AgentProvider, ProviderAgentSession, created, materialize_native_home};
use crate::{
    agent_session::{CliContext, CreatedSession, SessionError, SessionFactory},
    config::{BubConfig, Profile, RuntimeBinding},
    provider::{BubProvider, bub::BubSessionRecord, session::map_provider_error},
};
use std::{collections::BTreeMap, fs, path::PathBuf, sync::Arc};
use tokio::sync::Mutex;

pub(super) struct BubSessions {
    config: BubConfig,
    bindings: BTreeMap<String, RuntimeBinding>,
    providers: Mutex<BTreeMap<String, Arc<BubProvider>>>,
}

impl BubSessions {
    pub(super) fn new(config: BubConfig, bindings: BTreeMap<String, RuntimeBinding>) -> Self {
        Self { config, bindings, providers: Mutex::new(BTreeMap::new()) }
    }

    fn config_for(
        &self,
        profile: &Profile,
        home: Option<PathBuf>,
    ) -> Result<BubConfig, SessionError> {
        let binding = self.bindings.get(&profile.id).ok_or_else(|| {
            SessionError::Failed(format!("missing runtime binding for profile {}", profile.id))
        })?;
        let mut config = self.config.clone();
        config.executable = binding.executable.clone();
        config.api_key_environment =
            binding.api_key_environment.clone().or(config.api_key_environment);
        config.api_key_file = binding.api_key_file.clone().or(config.api_key_file);
        config.home = match home {
            Some(home) => home,
            None => materialize_native_home(
                profile,
                &binding.native_home,
                binding.native_template.as_ref(),
                Some(&config.home),
            )?,
        };
        config.home =
            config.home.canonicalize().map_err(|error| SessionError::Failed(error.to_string()))?;
        Ok(config)
    }

    fn resume_home(&self, profile: &Profile, id: &str) -> Result<PathBuf, SessionError> {
        let root = self
            .bindings
            .get(&profile.id)
            .and_then(|binding| binding.native_home.root.clone())
            .unwrap_or_else(|| self.config.home.clone());
        let mut candidates = vec![root.clone()];
        for entry in fs::read_dir(&root).map_err(|error| {
            SessionError::Failed(format!("Bub native home {}: {error}", root.display()))
        })? {
            let path = entry.map_err(|error| SessionError::Failed(error.to_string()))?.path();
            if path.is_dir() {
                candidates.push(path);
            }
        }
        let mut homes = Vec::new();
        for home in candidates {
            if !home.join("braid-session.json").try_exists().map_err(|error| {
                SessionError::Failed(format!("Bub native binding {}: {error}", home.display()))
            })? {
                continue;
            }
            let record = BubSessionRecord::read(&home).map_err(map_provider_error)?;
            if record.session_id == id {
                record.validate(&home, id, profile.workspace()).map_err(map_provider_error)?;
                if record.history_is_missing().map_err(map_provider_error)? {
                    return Err(SessionError::HistoryUnavailable(format!(
                        "Bub native tape is unavailable for session {id}: {}",
                        record.tape.display()
                    )));
                }
                homes.push(home);
            }
        }
        match homes.len() {
            1 => Ok(homes.remove(0)),
            0 => Err(SessionError::Failed(format!(
                "cannot locate durable Bub binding {id} under {}; this does not prove native history loss",
                root.display()
            ))),
            _ => Err(SessionError::Failed(format!("Bub session {id} has multiple native homes"))),
        }
    }

    async fn retain_result(
        &self,
        provider: Arc<BubProvider>,
        session: Arc<ProviderAgentSession>,
        home: PathBuf,
    ) -> Result<CreatedSession, SessionError> {
        let record = provider.native_record().await.ok_or_else(|| {
            SessionError::Failed("Bub adapter returned no durable binding".into())
        })?;
        let mut result = created(session, Some(home)).await?;
        result.native_session_path = Some(record.tape.clone());
        result.native_session_id =
            record.tape.file_stem().map(|stem| stem.to_string_lossy().into_owned());
        self.providers.lock().await.insert(result.id.clone(), provider);
        Ok(result)
    }

    async fn settle_error(
        &self,
        id: &str,
        provider: Arc<BubProvider>,
        error: SessionError,
    ) -> SessionError {
        let native_id = provider.native_record().await.map(|record| record.session_id);
        let id = native_id.as_deref().unwrap_or(id);
        let error = if native_id.is_some() && !matches!(error, SessionError::Materialization { .. })
        {
            SessionError::Materialization {
                session_id: native_id.clone(),
                reason: error.to_string(),
            }
        } else {
            error
        };
        match provider.close_native().await {
            Ok(()) => error,
            Err(stop) => {
                self.providers.lock().await.insert(id.into(), provider);
                SessionError::Failed(format!("{error}; Bub native teardown failed: {stop}"))
            }
        }
    }
}

#[async_trait::async_trait]
impl SessionFactory for BubSessions {
    async fn check(&self) -> Result<(), SessionError> {
        let executable = self
            .bindings
            .values()
            .next()
            .map_or(&self.config.executable, |binding| &binding.executable);
        which::which(executable).map(|_| ()).map_err(|_| SessionError::Unavailable)
    }

    async fn start(
        &self,
        profile: Profile,
        instructions: String,
        context: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        let config = self.config_for(&profile, None)?;
        let provider = Arc::new(
            BubProvider::connect(&config, &profile, &cli).await.map_err(map_provider_error)?,
        );
        match ProviderAgentSession::start(
            Arc::clone(&provider) as Arc<dyn AgentProvider>,
            profile,
            instructions,
            Some(context),
        )
        .await
        {
            Ok(session) => self.retain_result(provider, session, config.home).await,
            Err(error) => Err(self.settle_error("unidentified-bub-create", provider, error).await),
        }
    }

    async fn resume(
        &self,
        id: &str,
        profile: Profile,
        instructions: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        if self.providers.lock().await.contains_key(id) {
            self.teardown(id).await?;
        }
        let home = self.resume_home(&profile, id)?;
        let config = self.config_for(&profile, Some(home))?;
        let provider = Arc::new(
            BubProvider::connect(&config, &profile, &cli).await.map_err(map_provider_error)?,
        );
        match ProviderAgentSession::resume(
            Arc::clone(&provider) as Arc<dyn AgentProvider>,
            profile,
            instructions,
            id,
        )
        .await
        {
            Ok(session) => self.retain_result(provider, session, config.home).await,
            Err(error) => Err(self.settle_error(id, provider, error).await),
        }
    }

    async fn teardown(&self, id: &str) -> Result<(), SessionError> {
        let provider = self.providers.lock().await.get(id).cloned().ok_or_else(|| {
            SessionError::Failed(format!("Bub provider session {id} is not registered"))
        })?;
        provider.close_native().await.map_err(map_provider_error)?;
        self.providers.lock().await.remove(id);
        Ok(())
    }
}
