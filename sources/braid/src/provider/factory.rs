use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};
use tokio::sync::Mutex;

use super::{AgentProvider, CodexProvider, PiProvider, ProviderAgentSession};
use crate::{
    agent_session::{CliContext, CreatedSession, SessionError, SessionFactory},
    config::{CodexConfig, NativeHomeBinding, PiConfig, Profile, ProviderConfig, RuntimeBinding},
};

/// Compose the one configured native adapter.
pub(crate) fn session_factory(config: ProviderConfig) -> anyhow::Result<Arc<dyn SessionFactory>> {
    let bindings = config.bindings;
    match (config.codex, config.pi, config.bub) {
        (Some(config), None, None) => Ok(Arc::new(CodexSessions {
            config,
            bindings,
            homes: Mutex::new(BTreeMap::new()),
            providers: Mutex::new(BTreeMap::new()),
        })),
        (None, Some(config), None) => {
            Ok(Arc::new(PiSessions { config, bindings, providers: Mutex::new(BTreeMap::new()), pressure_sample: Mutex::new(None) }))
        }
        (None, None, Some(config)) => Ok(Arc::new(bub::BubSessions::new(config, bindings))),
        _ => anyhow::bail!("必须配置且仅配置一个会话 adapter"),
    }
}

struct CodexSessions {
    config: CodexConfig,
    bindings: BTreeMap<String, RuntimeBinding>,
    homes: Mutex<BTreeMap<String, PathBuf>>,
    providers: Mutex<BTreeMap<String, Arc<CodexProvider>>>,
}

impl CodexSessions {
    async fn connection(
        &self,
        profile: &Profile,
        existing_home: Option<PathBuf>,
        cli: &CliContext,
    ) -> Result<(Arc<CodexProvider>, PathBuf), SessionError> {
        let binding = self.bindings.get(&profile.id).ok_or_else(|| {
            SessionError::Failed(format!("missing runtime binding for profile {}", profile.id))
        })?;
        let home = if let Some(home) = existing_home {
            home
        } else {
            materialize_native_home(
                profile,
                &binding.native_home,
                binding.native_template.as_ref(),
                Some(self.config.home.as_path()),
            )?
        };
        let mut config = self.config.clone();
        config.executable = binding.executable.clone();
        config.home = home.clone();
        let provider = Arc::new(
            CodexProvider::connect(&config, cli).await.map_err(super::session::map_provider_error)?,
        );
        Ok((provider, home))
    }

    fn native_home_root(&self, profile: &Profile) -> PathBuf {
        self.bindings
            .get(&profile.id)
            .and_then(|binding| binding.native_home.root.clone())
            .unwrap_or_else(|| self.config.home.clone())
    }
}

#[async_trait::async_trait]
impl SessionFactory for CodexSessions {
    async fn check(&self) -> Result<(), SessionError> {
        let profile = self.bindings.keys().next().and_then(|id| self.bindings.get(id));
        let executable = profile
            .map_or_else(|| self.config.executable.clone(), |binding| binding.executable.clone());
        which::which(executable).map(|_| ()).map_err(|_| SessionError::Unavailable)
    }

    async fn start(
        &self,
        profile: Profile,
        instructions: String,
        context: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        let (provider, native_home) = self.connection(&profile, None, &cli).await?;
        let session = ProviderAgentSession::start(
            Arc::clone(&provider) as Arc<dyn AgentProvider>,
            profile,
            instructions,
            Some(context),
        )
        .await?;
        let result = created(session, Some(native_home.clone())).await?;
        self.homes.lock().await.insert(result.id.clone(), native_home);
        self.providers.lock().await.insert(result.id.clone(), provider);
        Ok(result)
    }

    async fn resume(
        &self,
        id: &str,
        profile: Profile,
        instructions: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        if self.providers.lock().await.contains_key(id) { self.teardown(id).await?; }
        let native_home = self.homes.lock().await.get(id).cloned();
        let native_home = match native_home {
            Some(home) => Some(home),
            None => find_native_home(&self.native_home_root(&profile), id)?,
        };
        let native_home = native_home.ok_or_else(|| {
            SessionError::Failed(format!("cannot locate Codex native home for thread {id} under {}; the configured root does not prove native history loss",self.native_home_root(&profile).display()))
        })?;
        let (provider, native_home) = self.connection(&profile, Some(native_home), &cli).await?;
        let session = match ProviderAgentSession::resume(
            Arc::clone(&provider) as Arc<dyn AgentProvider>, profile, instructions, id,
        ).await {
            Ok(session) => session,
            Err(error) => {
                if let Err(stop_error) = provider.close_native().await {
                    // Keep ownership so the next attempt must settle this writer.
                    self.providers.lock().await.insert(id.to_owned(), provider);
                    return Err(SessionError::Failed(format!("{error}; failed resume teardown: {stop_error}")));
                }
                return Err(error);
            }
        };
        let result = created(session, Some(native_home.clone())).await?;
        self.homes.lock().await.insert(result.id.clone(), native_home);
        self.providers.lock().await.insert(result.id.clone(), provider);
        Ok(result)
    }

    async fn teardown(&self, id: &str) -> Result<(), SessionError> {
        let provider = self.providers.lock().await.remove(id).ok_or_else(|| {
            SessionError::Failed(format!("cannot prove Codex native teardown for thread {id}"))
        })?;
        match provider.close_native().await {
            Ok(()) => Ok(()),
            Err(error) => {
                self.providers.lock().await.insert(id.to_owned(), provider);
                Err(SessionError::Failed(error.to_string()))
            }
        }
    }
}

struct PiSessions {
    config: PiConfig,
    bindings: BTreeMap<String, RuntimeBinding>,
    providers: Mutex<BTreeMap<String, Arc<PiProvider>>>,
    pressure_sample: Mutex<Option<String>>,
}

impl PiSessions {
    async fn check_start_resources(&self) -> Result<(), SessionError> {
        let resource = super::pi::resource_status().await.map_err(|error| SessionError::Deferred(error.to_string()))?;
        if let Some(resource) = resource {
            if resource["status"] != "normal" { return Err(SessionError::Deferred(format!("resource pressure: {resource}"))); }
        }
        Ok(())
    }
    fn config_for(
        &self,
        profile: &Profile,
        existing_home: Option<PathBuf>,
    ) -> Result<PiConfig, SessionError> {
        let binding = self.bindings.get(&profile.id).ok_or_else(|| {
            SessionError::Failed(format!("missing runtime binding for profile {}", profile.id))
        })?;
        let mut config = self.config.clone();
        config.executable = binding.executable.clone();
        config.api_key_environment =
            binding.api_key_environment.clone().or(config.api_key_environment);
        config.api_key_file = binding.api_key_file.clone().or(config.api_key_file);
        let home = if let Some(home) = existing_home {
            home
        } else {
            materialize_native_home(
                profile,
                &binding.native_home,
                binding.native_template.as_ref(),
                config.home.as_deref(),
            )?
        };
        config.home = Some(home);
        Ok(config)
    }

    fn resume_path(&self, profile: &Profile, session_path: &str) -> Result<(PathBuf, PathBuf), SessionError> {
        let path = Path::new(session_path);
        let binding = self.bindings.get(&profile.id).ok_or_else(|| {
            SessionError::Failed(format!("missing runtime binding for profile {}", profile.id))
        })?;
        let root = binding
            .native_home
            .root
            .clone()
            .or_else(|| self.config.home.clone())
            .unwrap_or_else(|| profile.workspace().join(".braid/native-home"));
        let candidate = root.join(session_path);
        let exact_exists = path.is_absolute() && path.try_exists().map_err(|error| SessionError::Failed(format!("cannot inspect Pi native session {session_path}: {error}")))?;
        let native_path = if exact_exists && path.is_file() {
            path.to_path_buf()
        } else if candidate.try_exists().map_err(|error| SessionError::Failed(format!("cannot inspect Pi native session {}: {error}",candidate.display())))? && candidate.is_file() {
            candidate
        } else {
            let basename = path.file_name().ok_or_else(|| {
                SessionError::Failed(format!("cannot locate Pi native session {session_path}"))
            })?;
            let mut stack = vec![root.clone()];
            let mut found = None;
            while let Some(directory) = stack.pop() {
                for entry in
                    fs::read_dir(&directory).map_err(|error| SessionError::Failed(error.to_string()))?
                {
                    let entry = entry.map_err(|error| SessionError::Failed(error.to_string()))?;
                    let entry_path = entry.path();
                    if entry_path.is_dir() {
                        stack.push(entry_path);
                    } else if entry_path.file_name() == Some(basename) {
                        if found.replace(entry_path).is_some() {
                            return Err(SessionError::Failed(format!(
                                "multiple Pi native sessions match {session_path}"
                            )));
                        }
                    }
                }
            }
            found.ok_or_else(|| SessionError::HistoryUnavailable(format!("cannot locate Pi native session {session_path} under {}",root.display())))?
        };
        // 配置根位于 sessions 之上；旧平铺绝对路径仍以文件父目录为根。
        let home = native_path
            .strip_prefix(&root)
            .ok()
            .and_then(|relative| relative.components().next())
            .map(|component| root.join(component))
            .or_else(|| native_path.ancestors()
                .find(|directory| directory.file_name().is_some_and(|name| name == "sessions"))
                .and_then(Path::parent).map(Path::to_path_buf))
            .or_else(|| native_path.parent().map(Path::to_path_buf))
            .ok_or_else(|| SessionError::Failed("Pi session path has no native home".into()))?;
        Ok((native_path, home))
    }
}

fn materialize_native_home(
    profile: &Profile,
    binding: &NativeHomeBinding,
    template: Option<&PathBuf>,
    fallback: Option<&Path>,
) -> Result<PathBuf, SessionError> {
    let root = binding
        .root
        .clone()
        .or_else(|| fallback.map(Path::to_path_buf))
        .unwrap_or_else(|| profile.workspace().join(".braid/native-home"));
    let home = root.join(format!("{}-{}", profile.id, uuid::Uuid::now_v7()));
    fs::create_dir_all(&home).map_err(|e| SessionError::Failed(e.to_string()))?;
    if let Some(template) = template {
        copy_template(template, &home).map_err(|e| SessionError::Failed(e.to_string()))?;
    }
    Ok(home)
}

#[async_trait::async_trait]
impl SessionFactory for PiSessions {
    async fn maintain_resources(&self) -> Result<(), SessionError> {
        // The same factory is shared by every group; keep one relief operation
        // in flight and consume each collector sample at most once.
        let mut last_sample = self.pressure_sample.lock().await;
        let Some(status) = super::pi::resource_status().await.map_err(super::session::map_provider_error)? else { return Ok(()); };
        let sample = status["sample_id"].to_string();
        if last_sample.as_ref() == Some(&sample) { return Ok(()); }
        *last_sample = Some(sample);
        if !matches!(status["status"].as_str(), Some("pressured" | "critical")) { return Ok(()); }
        let providers: Vec<_> = self.providers.lock().await.values().cloned().collect();
        for provider in providers {
            match provider.relieve_pressure().await {
                Ok(receipt) => {
                    tracing::warn!(pressure = %status, receipt = %receipt, "native pressure relief");
                    if receipt["data"]["status"] == "relieved" { break; }
                }
                Err(error) => tracing::warn!(%error, "native pressure relief unavailable"),
            }
        }
        let after = super::pi::resource_status().await.map_err(super::session::map_provider_error)?;
        tracing::info!(before = %status, after = ?after, "resource pressure after relief");
        Ok(())
    }
    async fn check(&self) -> Result<(), SessionError> {
        // Pi has no global process: processes belong to physical sessions.
        let executable = self
            .bindings
            .values()
            .next()
            .map_or_else(|| self.config.executable.clone(), |binding| binding.executable.clone());
        which::which(executable).map(|_| ()).map_err(|_| SessionError::Unavailable)
    }

    async fn start(
        &self,
        profile: Profile,
        instructions: String,
        context: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        self.check_start_resources().await?;
        let config = self.config_for(&profile, None)?;
        let provider = Arc::new(PiProvider::connect(&config, cli, None));
        let session = match ProviderAgentSession::start(
            Arc::clone(&provider) as Arc<dyn AgentProvider>,
            profile,
            instructions,
            Some(context),
        )
        .await {
            Ok(session) => session,
            Err(error) => {
                if let Err(stop) = provider.close_native().await {
                    let identity = provider.native_session_id().await.unwrap_or_else(|| uuid::Uuid::now_v7().to_string());
                    self.providers.lock().await.insert(identity, provider);
                    return Err(SessionError::StopUnproved(format!("{error}; failed start teardown: {stop}")));
                }
                return Err(error);
            }
        };
        let native_home = config.home.clone();
        let mut result = created(session, native_home.clone()).await?;
        result.native_session_path = Some(PathBuf::from(&result.id));
        result.native_session_id = provider.native_session_id().await;
        self.providers.lock().await.insert(result.id.clone(), provider);
        Ok(result)
    }

    async fn resume(
        &self,
        id: &str,
        profile: Profile,
        instructions: String,
        cli: CliContext,
    ) -> Result<CreatedSession, SessionError> {
        self.check_start_resources().await?;
        if self.providers.lock().await.contains_key(id) { self.teardown(id).await?; }
        let (native_path, home) = self.resume_path(&profile, id)?;
        let config = self.config_for(&profile, Some(home))?;
        let provider = Arc::new(PiProvider::connect(&config, cli, Some(native_path.clone())));
        let session = match ProviderAgentSession::resume(
            Arc::clone(&provider) as Arc<dyn AgentProvider>, profile, instructions, id,
        ).await {
            Ok(session) => session,
            Err(error) => {
                if let Err(stop_error) = provider.close_native().await {
                    // Keep ownership so the next attempt must settle this writer.
                    self.providers.lock().await.insert(id.to_owned(), provider);
                    return Err(SessionError::StopUnproved(format!("{error}; failed resume teardown: {stop_error}")));
                }
                return Err(error);
            }
        };
        let native_home = config.home.clone();
        let mut result = created(session, native_home.clone()).await?;
        result.native_session_path = Some(native_path);
        result.native_session_id = provider.native_session_id().await;
        self.providers.lock().await.insert(result.id.clone(), provider);
        Ok(result)
    }

    async fn teardown(&self, id: &str) -> Result<(), SessionError> {
        let provider = self.providers.lock().await.get(id).cloned().ok_or_else(|| {
            SessionError::Failed(format!("Pi provider session {id} is not registered"))
        })?;
        provider.close_native().await.map_err(super::session::map_provider_error)?;
        self.providers.lock().await.remove(id);
        Ok(())
    }
}

fn copy_template(source: &PathBuf, destination: &PathBuf) -> std::io::Result<()> {
    if source.is_dir() {
        for entry in fs::read_dir(source)? {
            let entry = entry?;
            let target = destination.join(entry.file_name());
            if entry.path().is_dir() {
                fs::create_dir_all(&target)?;
                copy_template(&entry.path(), &target)?;
            } else {
                fs::copy(entry.path(), target)?;
            }
        }
    } else if source.is_file() {
        fs::copy(source, destination.join(source.file_name().unwrap_or_default()))?;
    }
    Ok(())
}

fn find_native_home(root: &Path, identity: &str) -> Result<Option<PathBuf>, SessionError> {
    let mut candidate_homes = Vec::new();
    let mut roots = Vec::new();
    if root.join("sessions").is_dir() {
        roots.push(root.to_owned());
    }
    for entry in fs::read_dir(root).map_err(|error| SessionError::Failed(error.to_string()))? {
        let entry = entry.map_err(|error| SessionError::Failed(error.to_string()))?;
        if entry.path().is_dir() && entry.path().join("sessions").is_dir() {
            roots.push(entry.path());
        }
    }
    for home in roots {
        let sessions = home.join("sessions");
        let mut stack = vec![sessions];
        while let Some(directory) = stack.pop() {
            for entry in
                fs::read_dir(&directory).map_err(|error| SessionError::Failed(error.to_string()))?
            {
                let entry = entry.map_err(|error| SessionError::Failed(error.to_string()))?;
                let path = entry.path();
                if path.is_dir() {
                    stack.push(path);
                    continue;
                }
                let contents = fs::read_to_string(&path)
                    .map_err(|error| SessionError::Failed(error.to_string()))?;
                let Some(header) = contents.lines().next() else {
                    continue;
                };
                let payload_id = serde_json::from_str::<serde_json::Value>(header)
                    .ok()
                    .and_then(|value| value.get("payload")?.get("id")?.as_str().map(str::to_owned));
                if payload_id.as_deref() == Some(identity) && !candidate_homes.contains(&home) {
                    candidate_homes.push(home.clone());
                }
            }
        }
    }
    match candidate_homes.len() {
        0 => Ok(None),
        1 => Ok(candidate_homes.pop()),
        _ => Err(SessionError::Failed(format!(
            "Codex native session {identity} matches multiple native homes"
        ))),
    }
}

async fn created(
    session: Arc<ProviderAgentSession>,
    native_home: Option<PathBuf>,
) -> Result<CreatedSession, SessionError> {
    let id = session
        .thread_id()
        .await
        .ok_or_else(|| SessionError::Failed("adapter returned no session identity".into()))?;
    Ok(CreatedSession {
        id: id.clone(),
        session,
        native_home,
        native_session_path: None,
        native_session_id: None,
    })
}

mod bub;
