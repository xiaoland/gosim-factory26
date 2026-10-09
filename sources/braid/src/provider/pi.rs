#![allow(clippy::wildcard_imports)]
use super::*;
use std::io::BufRead as _;
use std::path::PathBuf;
use std::sync::atomic::AtomicBool;

struct PiProcess {
    writer: Option<ChildStdin>,
    child: PiChild,
    execution: Option<(PathBuf, String)>,
    started_at: std::time::Instant,
    #[allow(dead_code)]
    stdout_handle: tokio::task::JoinHandle<()>,
    #[allow(dead_code)]
    stderr_handle: tokio::task::JoinHandle<()>,
}

struct PiChild(Child);

impl std::ops::Deref for PiChild {
    type Target = Child;

    fn deref(&self) -> &Self::Target {
        &self.0
    }
}

impl std::ops::DerefMut for PiChild {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut self.0
    }
}

impl Drop for PiChild {
    fn drop(&mut self) {
        // Tokio retains its existing cleanup. Release is not proof that it sent a signal.
        tracing::info!(
            pid = self.0.id(),
            sender_pid = std::process::id(),
            kill_on_drop_at_creation = true,
            signal_outcome = "unobserved",
            "Pi child owner released"
        );
    }
}

struct PiRequest {
    response: oneshot::Sender<Result<Value, ProviderError>>,
    turn_id: Option<String>,
}

type PiRequests = BTreeMap<i64, PiRequest>;

struct PiState {
    config: PiConfig,
    resume_path: Option<PathBuf>,
    cli: crate::agent_session::CliContext,
    pending: Arc<Mutex<PiRequests>>,
    next_request_id: Arc<AtomicI64>,
    process: Option<PiProcess>,
    session: Option<String>,
    developer_instructions: String,
    context: String,
}

#[derive(Clone)]
pub struct PiProvider {
    state: Arc<Mutex<PiState>>,
    notifications: broadcast::Sender<ProviderNotification>,
    closed: watch::Sender<bool>,
    thread_id: Arc<Mutex<String>>,
    turn_id: Arc<Mutex<Option<String>>>,
    native_session_id: Arc<Mutex<Option<String>>>,
    teardown_failed: Arc<AtomicBool>,
}

impl PiProvider {
    pub fn connect(
        config: &PiConfig,
        cli: crate::agent_session::CliContext,
        resume_path: Option<PathBuf>,
    ) -> Self {
        let (notifications, _) = broadcast::channel(512);
        let (closed, _) = watch::channel(false);
        let state = PiState {
            config: config.clone(),
            resume_path,
            cli,
            pending: Arc::new(Mutex::new(BTreeMap::new())),
            next_request_id: Arc::new(AtomicI64::new(1)),
            process: None,
            session: None,
            developer_instructions: String::new(),
            context: String::new(),
        };
        Self {
            state: Arc::new(Mutex::new(state)),
            notifications,
            closed,
            thread_id: Arc::new(Mutex::new(String::new())),
            turn_id: Arc::new(Mutex::new(None)),
            native_session_id: Arc::new(Mutex::new(None)),
            teardown_failed: Arc::new(AtomicBool::new(false)),
        }
    }

    pub(crate) async fn close_native(&self) -> Result<(), ProviderError> {
        if self.teardown_failed.load(Ordering::Acquire) {
            return Err(ProviderError::Protocol("Pi shutdown previously failed".into()));
        }
        let mut state = self.state.lock().await;
        if state.process.is_none() {
            return Ok(());
        }
        if state.process.as_ref().is_some_and(|process| process.execution.is_some()) {
            match Self::request(&mut state, json!({"type":"stop_owned_execution"})).await {
                Ok(receipt) => {
                    tracing::info!(receipt = %receipt, "Pi owned execution shutdown receipt")
                }
                Err(error) => {
                    tracing::warn!(%error, "Pi shutdown RPC unavailable; offline cleanup required")
                }
            }
        }
        let mut process = state.process.take().expect("checked Pi process");
        // EOF invokes Pi's own runtime disposal and extension shutdown hooks.
        // Internal subagents belong to Pi, not to Braid's process supervisor.
        process.writer.take();
        let pid = process.child.id();
        tracing::info!(
            pid,
            phase = "request",
            reason = "stdin-eof-shutdown",
            timeout_seconds = 180,
            "Pi child wait"
        );
        let waited = match timeout(Duration::from_secs(180), process.child.wait()).await {
            Ok(Ok(status)) => {
                #[cfg(unix)]
                let signal = std::os::unix::process::ExitStatusExt::signal(&status);
                #[cfg(not(unix))]
                let signal: Option<i32> = None;
                tracing::info!(pid, phase = "result", exit_code = status.code(), signal,
                    status = %status, "Pi child wait");
                if let Some((directory, identity)) = &process.execution {
                    if let Err(error) = crate::local::write_json(
                        &directory.join("parent-wait.json"),
                        &json!({"execution_id":identity,"pid":pid,"exit_code":status.code(),"signal":signal,"status":status.to_string()}),
                    ) {
                        tracing::warn!(%error, "cannot persist Pi parent wait receipt");
                    }
                }
                Ok(status)
            }
            Ok(Err(error)) => {
                tracing::warn!(pid, phase = "result", errno = error.raw_os_error(), %error,
                    "Pi child wait failed");
                Err(ProviderError::Protocol(error.to_string()))
            }
            Err(_) => {
                tracing::warn!(pid, phase = "result", reason = "timeout", "Pi child wait failed");
                tracing::warn!(
                    pid,
                    sender_pid = std::process::id(),
                    phase = "request",
                    signal = 9,
                    reason = "shutdown-timeout",
                    "Pi child kill and wait"
                );
                match timeout(Duration::from_secs(5), process.child.kill()).await {
                    Ok(Ok(())) => {
                        tracing::warn!(
                            pid,
                            phase = "result",
                            result = "returned",
                            "Pi child kill and wait"
                        );
                        process
                            .child
                            .wait()
                            .await
                            .map_err(|error| ProviderError::Protocol(error.to_string()))
                    }
                    Ok(Err(error)) => {
                        tracing::warn!(pid, phase = "result", errno = error.raw_os_error(), %error, "Pi child kill and wait failed");
                        Err(ProviderError::Protocol(error.to_string()))
                    }
                    Err(_) => Err(ProviderError::Timeout { method: "Pi shutdown kill".into() }),
                }
            }
        };
        // A failed turn or a SIGKILL is an execution outcome, not a cleanup
        // verdict. Detached work must be settled from persisted ownership.
        let result = if let Some((directory, identity)) = &process.execution {
            if let Err(error) = &waited {
                if let Err(write_error) = crate::local::write_json(
                    &directory.join("parent-wait.json"),
                    &json!({"execution_id":identity,"pid":pid,"wait_error":error.to_string()}),
                ) {
                    tracing::warn!(%write_error, "cannot persist Pi parent wait error");
                }
            }
            stop_owned_execution_offline(directory, identity).await
        } else {
            waited.and_then(|status| {
                if status.success() {
                    Ok(())
                } else {
                    Err(ProviderError::Protocol(format!(
                        "Pi exited with {status}; owned execution stop proof unavailable"
                    )))
                }
            })
        };
        if let Err(error) = &result {
            self.teardown_failed.store(true, Ordering::Release);
            state.process = Some(process);
            tracing::error!(%error, "Pi owned execution stop unproved");
        }
        self.closed.send_replace(true);
        result
    }

    pub(crate) async fn native_session_id(&self) -> Option<String> {
        self.native_session_id.lock().await.clone()
    }

    async fn refresh_session_identity(
        &self,
        state: &mut PiState,
    ) -> Result<(String, String), ProviderError> {
        let startup_timeout = Duration::from_secs(state.config.startup_timeout_seconds);
        let started = std::time::Instant::now();
        let state_resp = match Self::request_with_turn(
            state,
            json!({"type": "get_state"}),
            None,
            startup_timeout,
        )
        .await
        {
            Ok(response) => response,
            Err(error) => {
                return Err(error);
            }
        };
        observe_native_state(state, "startup", &state_resp);
        let data = state_resp.get("data").and_then(Value::as_object).ok_or_else(|| {
            ProviderError::CreatedWithoutIdentity("get_state missing data".into())
        })?;
        let session_file = data
            .get("sessionFile")
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| {
                ProviderError::CreatedWithoutIdentity("get_state missing sessionFile".into())
            })?;
        let session_id = data
            .get("sessionId")
            .or_else(|| data.get("session_id"))
            .and_then(Value::as_str)
            .filter(|value| !value.is_empty())
            .ok_or_else(|| {
                ProviderError::CreatedWithoutIdentity("get_state missing sessionId".into())
            })?;
        *self.native_session_id.lock().await = Some(session_id.to_owned());
        tracing::info!(
            native_session = session_id,
            elapsed_ms = started.elapsed().as_millis(),
            "Pi startup handshake completed"
        );
        Ok((session_file.to_owned(), session_id.to_owned()))
    }

    fn spawn(
        &self,
        state: &mut PiState,
        profile: &Profile,
        workspace: &Path,
        session: Option<&str>,
    ) -> Result<(), ProviderError> {
        let start_id = uuid::Uuid::now_v7().to_string();
        let execution = std::env::var_os("FACTORY_NATIVE_RUNTIME_MODULE").map(|_| {
            let home = state.config.home.as_deref().unwrap_or(workspace);
            (home.join("managed-executions").join(&start_id), start_id.clone())
        });
        let mut startup_receipt = None;
        let mut cmd = if let Some(helper) = std::env::var_os("FACTORY_RESOURCE_HELPER") {
            let python = std::env::var_os("FACTORY_RESOURCE_PYTHON").ok_or_else(|| {
                ProviderError::Protocol("FACTORY_RESOURCE_PYTHON is missing".into())
            })?;
            let directory = std::env::var_os("FACTORY_RESOURCE_DIR")
                .ok_or_else(|| ProviderError::Protocol("FACTORY_RESOURCE_DIR is missing".into()))?;
            startup_receipt =
                Some(PathBuf::from(directory).join("starts").join(format!("{start_id}.json")));
            let mut command = Command::new(python);
            command
                .arg(helper)
                .args(["launch", "--start-id", &start_id, "--kind", "native", "--"])
                .arg(&state.config.executable);
            command
        } else {
            Command::new(&state.config.executable)
        };
        if let Some((directory, identity)) = &execution {
            std::fs::create_dir_all(directory).map_err(ProviderError::Start)?;
            cmd.env("FACTORY_NATIVE_EXECUTION_DIR", directory)
                .env("FACTORY_NATIVE_EXECUTION_ID", identity);
        }
        if startup_receipt.is_some() && execution.is_none() {
            return Err(ProviderError::Protocol(
                "managed process registration requires FACTORY_NATIVE_RUNTIME_MODULE".into(),
            ));
        }
        cmd.env_remove("FACTORY_NATIVE_START_ID");
        cmd.args(["--mode", "rpc"])
            .env("BRAID_AGENT_RUNTIME", "1")
            .env("PI_TIMING", "1")
            .env("BRAID_STATE", &state.cli.state)
            .env("BRAID_CLI_BINDING_ID", &state.cli.binding_id);
        // Pi 启动迁移会搬走配置根顶层的 JSONL；活动会话必须写入独立子目录。
        let session_dir = state
            .config
            .home
            .as_ref()
            .map(|home| home.join("sessions"))
            .unwrap_or_else(|| workspace.join(".braid").join("pi-sessions"));
        std::fs::create_dir_all(&session_dir).map_err(|error| {
            ProviderError::Protocol(format!(
                "cannot create pi session dir {}: {error}",
                session_dir.display()
            ))
        })?;
        cmd.args(["--session-dir", &session_dir.to_string_lossy()]);
        if !profile.provider.is_empty() {
            cmd.args(["--provider", &profile.provider]);
        }
        if let Some(model) = &profile.model {
            cmd.args(["--model", model]);
        }
        if let Some(thinking) = &profile.reasoning {
            cmd.args(["--thinking", thinking]);
        }
        if let Some(home) = &state.config.home {
            cmd.env("PI_CODING_AGENT_DIR", home);
        }
        if let Ok(api_key) = state.config.api_key()
            && let Some(api_key_env) = &state.config.api_key_environment
        {
            cmd.env(api_key_env, api_key);
        }
        // Agent shell commands must resolve the same local `braid` binary.
        if let Ok(current_exe) = std::env::current_exe()
            && let Some(exe_dir) = current_exe.parent()
        {
            let mut path_parts: Vec<String> =
                std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default())
                    .map(|p| p.to_string_lossy().into_owned())
                    .collect();
            let exe_dir_str = exe_dir.to_string_lossy().into_owned();
            if !path_parts.iter().any(|p| p == &exe_dir_str) {
                path_parts.insert(0, exe_dir_str);
            }
            cmd.env("PATH", std::env::join_paths(path_parts).unwrap_or_default());
        }
        if let Ok(braid_config) = std::env::var("BRAID_CONFIG") {
            cmd.env("BRAID_CONFIG", braid_config);
        }
        if let Some(session_path) = session {
            cmd.args(["--session", session_path]);
        }
        if !state.developer_instructions.is_empty() {
            cmd.args(["--append-system-prompt", &state.developer_instructions]);
        }
        cmd.current_dir(workspace);
        cmd.stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).kill_on_drop(true);
        #[cfg(unix)]
        cmd.process_group(0);

        let started_at = std::time::Instant::now();
        let mut child = PiChild(cmd.spawn()?);
        tracing::info!(pid = child.id(), profile = %profile.id, workspace = %workspace.display(), native_home = ?state.config.home, session_dir = %session_dir.display(), resume = session.is_some(), "Pi process started");
        #[cfg(target_os = "linux")]
        if let Some(pid) = child.id() {
            for name in ["stat", "cgroup"] {
                let path = format!("/proc/{pid}/{name}");
                match std::fs::read_to_string(&path) {
                    Ok(raw) => tracing::info!(pid, %path, raw = %raw.trim(), "Pi process identity"),
                    Err(error) => tracing::warn!(pid, %path, errno = error.raw_os_error(), %error,
                        "Pi process identity unavailable"),
                }
            }
        }
        let writer = child
            .stdin
            .take()
            .ok_or_else(|| ProviderError::Protocol("pi stdin was not piped".into()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| ProviderError::Protocol("pi stdout was not piped".into()))?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| ProviderError::Protocol("pi stderr was not piped".into()))?;
        let stdout_handle = spawn_pi_stdout(
            stdout,
            started_at,
            Arc::clone(&state.pending),
            self.notifications.clone(),
            self.closed.clone(),
            Arc::clone(&self.thread_id),
            Arc::clone(&self.turn_id),
        );
        let stderr_handle = spawn_pi_stderr(stderr, state.config.home.clone());
        state.process = Some(PiProcess {
            writer: Some(writer),
            child,
            execution,
            started_at,
            stdout_handle,
            stderr_handle,
        });
        Ok(())
    }

    async fn request(state: &mut PiState, frame: Value) -> Result<Value, ProviderError> {
        Self::request_with_turn(state, frame, None, REQUEST_TIMEOUT).await
    }

    async fn request_with_turn(
        state: &mut PiState,
        frame: Value,
        turn_id: Option<String>,
        deadline: Duration,
    ) -> Result<Value, ProviderError> {
        let id = state.next_request_id.fetch_add(1, Ordering::Relaxed);
        let method = frame.get("type").and_then(Value::as_str).unwrap_or("unknown").to_owned();
        let started = std::time::Instant::now();
        tracing::info!(request_id = id, %method, deadline_ms = deadline.as_millis(),
            "Pi RPC request started");
        let mut frame = frame;
        if let Some(obj) = frame.as_object_mut() {
            obj.insert("id".to_string(), json!(id));
        }

        let (sender, receiver) = oneshot::channel();
        state.pending.lock().await.insert(id, PiRequest { response: sender, turn_id });

        let process = state.process.as_mut().ok_or(ProviderError::Disconnected)?;
        let bytes = {
            let mut bytes = serde_json::to_vec(&frame)
                .map_err(|error| ProviderError::Protocol(error.to_string()))?;
            bytes.push(b'\n');
            bytes
        };
        let writer = process.writer.as_mut().ok_or(ProviderError::Disconnected)?;
        if let Err(error) = writer.write_all(&bytes).await {
            state.pending.lock().await.remove(&id);
            tracing::warn!(request_id = id, %method, phase = "write", %error,
                elapsed_ms = started.elapsed().as_millis(), "Pi RPC request failed");
            return Err(ProviderError::Start(error));
        }
        if let Err(error) = writer.flush().await {
            state.pending.lock().await.remove(&id);
            tracing::warn!(request_id = id, %method, phase = "flush", %error,
                elapsed_ms = started.elapsed().as_millis(), "Pi RPC request failed");
            return Err(ProviderError::Start(error));
        }
        tracing::info!(request_id = id, %method, pid = process.child.id(),
            process_elapsed_ms = process.started_at.elapsed().as_millis(),
            elapsed_ms = started.elapsed().as_millis(), "Pi RPC request submitted");
        let result = match timeout(deadline, receiver).await {
            Ok(Ok(response)) => response,
            Ok(Err(_)) => Err(ProviderError::Disconnected),
            Err(_) => {
                state.pending.lock().await.remove(&id);
                Err(ProviderError::Timeout {
                    method: format!("Pi {method} ({}s)", deadline.as_secs()),
                })
            }
        };
        match &result {
            Ok(_) => tracing::info!(request_id = id, %method,
                elapsed_ms = started.elapsed().as_millis(), "Pi RPC request completed"),
            Err(error) => tracing::warn!(request_id = id, %method, %error,
                elapsed_ms = started.elapsed().as_millis(), "Pi RPC request failed"),
        }
        result
    }

    fn success_or_protocol(result: &Value, context: &str) -> Result<(), ProviderError> {
        if result.get("success").and_then(Value::as_bool).unwrap_or(false) {
            return Ok(());
        }
        let message = if let Some(error) = result.get("error").and_then(Value::as_str) {
            error.to_owned()
        } else if let Some(message) =
            result.get("data").and_then(|data| data.get("message")).and_then(Value::as_str)
        {
            message.to_owned()
        } else {
            format!("{context} failed")
        };
        Err(ProviderError::Protocol(message))
    }
}

#[async_trait::async_trait]
impl AgentProvider for PiProvider {
    async fn can_accept_input(&self, _thread_id: &str) -> Result<bool, ProviderError> {
        let mut state = self.state.lock().await;
        let native = Self::request(&mut state, json!({"type": "get_state"})).await?;
        observe_native_state(&state, "input_readiness", &native);
        if native_is_busy(&native) {
            return Ok(false);
        }
        Ok(true)
    }
    async fn managed_state(
        &self,
        _thread_id: &str,
    ) -> Result<crate::agent_session::ManagedState, ProviderError> {
        let mut state = self.state.lock().await;
        let native = Self::request(&mut state, json!({"type":"get_state"})).await?;
        observe_native_state(&state, "idle_unload", &native);
        if let Some((_, identity)) =
            state.process.as_ref().and_then(|process| process.execution.as_ref())
        {
            if native["data"]["managed_state"]["execution_id"].as_str() != Some(identity.as_str()) {
                tracing::warn!(response = %native, execution = identity, "native managed state identity mismatch");
                return Ok(crate::agent_session::ManagedState::Unknown);
            }
        }
        Ok(match native["data"]["managed_state"]["status"].as_str() {
            Some("quiescent") => crate::agent_session::ManagedState::Quiescent,
            Some("busy") => crate::agent_session::ManagedState::Busy,
            _ => crate::agent_session::ManagedState::Unknown,
        })
    }
    async fn yield_stoppable_services(
        &self,
        _thread_id: &str,
    ) -> Result<crate::agent_session::ManagedState, ProviderError> {
        {
            let mut state = self.state.lock().await;
            let receipt =
                Self::request(&mut state, json!({"type":"yield_stoppable_services"})).await?;
            observe_native_state(&state, "service_handoff", &receipt);
            let identity = state
                .process
                .as_ref()
                .and_then(|process| process.execution.as_ref())
                .map(|(_, identity)| identity.as_str());
            if identity.is_none()
                || receipt["data"]["managed_state"]["execution_id"].as_str() != identity
            {
                return Err(ProviderError::Protocol(format!(
                    "service handoff execution identity mismatch: {receipt}"
                )));
            }
        }
        // The stop receipt is not an idle oracle: independently observe the
        // native turn, pending results, providers and exact process ownership.
        self.managed_state(_thread_id).await
    }

    fn subscribe(&self) -> broadcast::Receiver<ProviderNotification> {
        self.notifications.subscribe()
    }

    async fn closed(&self) {
        let mut closed = self.closed.subscribe();
        while !*closed.borrow() && closed.changed().await.is_ok() {}
    }

    async fn start_session(
        &self,
        profile: &Profile,
        developer_instructions: &str,
    ) -> Result<ProviderSession, ProviderError> {
        let mut state = self.state.lock().await;
        developer_instructions.clone_into(&mut state.developer_instructions);
        state.context.clear();
        state.session = None;
        state.process = None;
        *self.turn_id.lock().await = None;
        *self.native_session_id.lock().await = None;

        self.spawn(&mut state, profile, profile.workspace(), None).inspect_err(
            |error| tracing::error!(%error, profile = %profile.id, "Pi process start failed"),
        )?;

        // Pi without --session/--continue already creates a fresh session.
        // Calling new_session here tears it down and reloads every extension.
        let (session_file, _session_id) = self.refresh_session_identity(&mut state).await
            .inspect_err(|error| tracing::error!(%error, profile = %profile.id, "Pi startup handshake failed"))
            .map_err(
            |error| match error {
                ProviderError::CreatedWithoutIdentity(_) => error,
                ProviderError::Deferred(_) | ProviderError::ResourceDeferred(_) => error,
                other => ProviderError::CreatedWithoutIdentity(other.to_string()),
            },
        )?;
        state.session = Some(session_file.to_owned());

        Ok(ProviderSession { thread_id: session_file.to_owned() })
    }

    async fn inject_context(&self, _thread_id: &str, context: &str) -> Result<(), ProviderError> {
        let mut state = self.state.lock().await;
        context.clone_into(&mut state.context);
        Ok(())
    }

    async fn resume_session(
        &self,
        thread_id: &str,
        profile: &Profile,
        developer_instructions: &str,
    ) -> Result<ProviderSession, ProviderError> {
        let mut state = self.state.lock().await;
        developer_instructions.clone_into(&mut state.developer_instructions);
        state.context.clear();
        state.session = Some(thread_id.to_owned());
        state.process = None;
        *self.turn_id.lock().await = None;
        *self.native_session_id.lock().await = None;

        let native_path = state
            .resume_path
            .as_ref()
            .ok_or_else(|| ProviderError::Protocol("Pi native session path is missing".into()))?
            .clone();
        if !native_path.is_file() {
            return Err(ProviderError::Protocol("Pi native session file is missing".into()));
        }
        let native_path_str = native_path
            .to_str()
            .ok_or_else(|| ProviderError::Protocol("Pi native session path is not UTF-8".into()))?;
        self.spawn(&mut state, profile, profile.workspace(), Some(native_path_str))?;

        let (session_file, _session_id) =
            self.refresh_session_identity(&mut state).await.inspect_err(
                |error| tracing::warn!(%error, "Pi get_state failed while resuming session"),
            )?;
        if Path::new(&session_file) != native_path {
            return Err(ProviderError::Protocol("Pi resumed a different session file".into()));
        }
        // The persisted Braid id still identifies this Agent and its notifications.
        state.session = Some(thread_id.to_owned());

        Ok(ProviderSession { thread_id: thread_id.to_owned() })
    }

    async fn start_turn(
        &self,
        _thread_id: &str,
        _profile: &Profile,
        event_references: &str,
    ) -> Result<ProviderTurn, ProviderError> {
        let mut state = self.state.lock().await;
        if state.process.is_none() {
            return Err(ProviderError::Disconnected);
        }

        let mut message = String::new();
        if !state.context.is_empty() {
            message.push_str(&state.context);
            message.push_str("\n\n");
        }
        message.push_str(event_references);

        let native = Self::request(&mut state, json!({"type": "get_state"})).await?;
        observe_native_state(&state, "prompt_preflight", &native);
        if native_is_busy(&native) {
            return Err(ProviderError::Deferred("Pi is streaming or compacting".into()));
        }

        let turn_id = uuid::Uuid::now_v7().to_string();
        *self.thread_id.lock().await = state.session.clone().unwrap_or_default();
        let result = Self::request_with_turn(
            &mut state,
            json!({"type": "prompt", "message": message}),
            Some(turn_id.clone()),
            REQUEST_TIMEOUT,
        )
        .await;
        match result {
            Ok(result) => Self::success_or_protocol(&result, "prompt")?,
            Err(ProviderError::Protocol(message)) => {
                // Pi has no typed busy response. Confirm native state instead of
                // recognizing error strings; a rejected prompt never owns a turn.
                let native = Self::request(&mut state, json!({"type": "get_state"})).await?;
                observe_native_state(&state, "prompt_rejection", &native);
                if native_is_busy(&native) {
                    return Err(ProviderError::Deferred(message));
                }
                return Err(ProviderError::Protocol(message));
            }
            Err(error) => return Err(error),
        }

        // The accepted prompt now owns this Context in native history. Retain it
        // on every rejection/Deferred path so retrying cannot lose initial input.
        state.context.clear();
        Ok(ProviderTurn { turn_id })
    }

    async fn steer(
        &self,
        _thread_id: &str,
        expected_turn_id: &str,
        event_references: &str,
    ) -> Result<(), ProviderError> {
        let mut state = self.state.lock().await;
        if self.turn_id.lock().await.as_deref() != Some(expected_turn_id) {
            return Err(ProviderError::Deferred("the observed Pi turn has ended".into()));
        }
        let result =
            Self::request(&mut state, json!({"type": "steer", "message": event_references}))
                .await?;
        Self::success_or_protocol(&result, "steer")?;
        Ok(())
    }

    async fn interrupt(&self, _thread_id: &str, _turn_id: &str) -> Result<(), ProviderError> {
        let mut state = self.state.lock().await;
        let result = Self::request(&mut state, json!({"type": "abort"})).await?;
        Self::success_or_protocol(&result, "abort")?;
        Ok(())
    }

    async fn message_was_processed(
        &self,
        thread_id: &str,
        message: &str,
    ) -> Result<bool, ProviderError> {
        let file = std::fs::File::open(thread_id).map_err(|error| {
            ProviderError::Protocol(format!("cannot read Pi native session {thread_id}: {error}"))
        })?;
        let mut notice_seen = false;
        for line in std::io::BufReader::new(file).lines() {
            let line = line.map_err(|error| {
                ProviderError::Protocol(format!(
                    "cannot read Pi native session {thread_id}: {error}"
                ))
            })?;
            let entry: Value = serde_json::from_str(&line).map_err(|error| {
                ProviderError::Protocol(format!("invalid Pi session entry: {error}"))
            })?;
            if entry["type"] != "message" {
                continue;
            }
            let role = entry["message"]["role"].as_str();
            if role == Some("user") {
                notice_seen |= entry["message"]["content"].as_array().is_some_and(|parts| {
                    parts.iter().any(|part| {
                        if part["type"] != "text" {
                            return false;
                        }
                        part["text"].as_str().is_some_and(|text| {
                            text == message
                                || text
                                    .strip_suffix(message)
                                    .is_some_and(|prefix| prefix.ends_with("\n\n"))
                        })
                    })
                });
            } else if role == Some("assistant") && notice_seen {
                return Ok(true);
            }
        }
        Ok(false)
    }
}

fn native_is_busy(response: &Value) -> bool {
    response["data"]["isStreaming"] == true || response["data"]["isCompacting"] == true
}

fn observe_native_state(state: &PiState, reason: &str, response: &Value) {
    let Some(process) = &state.process else {
        return;
    };
    let Some((directory, execution)) = &process.execution else {
        return;
    };
    let data = &response["data"];
    let receipt = json!({
        "observed_at_unix_nanos":std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)
            .map(|duration| duration.as_nanos().to_string()).unwrap_or_default(), "reason":reason,
        "expected_execution_id":execution, "pid":process.child.id(),
        "provider_session_id":state.session, "native_session_id":data["sessionId"],
        "managed_state":data["managed_state"], "isStreaming":data["isStreaming"],
        "isCompacting":data["isCompacting"], "pendingMessageCount":data["pendingMessageCount"],
    });
    if let Err(error) =
        crate::local::write_json(&directory.join("native-state-latest.json"), &receipt)
    {
        tracing::warn!(%error, execution, "cannot persist native state observation");
    }
}

async fn stop_owned_execution_offline(
    directory: &Path,
    identity: &str,
) -> Result<(), ProviderError> {
    let module = std::env::var_os("FACTORY_NATIVE_RUNTIME_MODULE").ok_or_else(|| {
        ProviderError::Protocol("native runtime cleanup module is missing".into())
    })?;
    let output = timeout(
        Duration::from_secs(30),
        Command::new("node")
            .arg(module)
            .args(["cleanup", "--execution-dir"])
            .arg(directory)
            .arg("--execution-id")
            .arg(identity)
            .output(),
    )
    .await
    .map_err(|_| ProviderError::Timeout { method: "owned execution cleanup".into() })??;
    let raw = String::from_utf8_lossy(&output.stdout);
    let receipt: Value = serde_json::from_slice(&output.stdout).map_err(|error| {
        ProviderError::Protocol(format!(
            "invalid owned execution cleanup receipt: {error}; status={}; stdout={raw}; stderr={}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        ))
    })?;
    tracing::info!(execution = identity, directory = %directory.display(), receipt = %receipt, status = %output.status,
        stderr = %String::from_utf8_lossy(&output.stderr), "Pi offline owned execution cleanup");
    if output.status.success() && receipt["status"] == "stopped" {
        Ok(())
    } else {
        Err(ProviderError::Protocol(format!(
            "owned execution stop unproved: {receipt}; status={}; stderr={}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        )))
    }
}

#[allow(clippy::too_many_arguments)]
fn spawn_pi_stdout(
    stdout: tokio::process::ChildStdout,
    started_at: std::time::Instant,
    pending: Arc<Mutex<PiRequests>>,
    notifications: broadcast::Sender<ProviderNotification>,
    closed: watch::Sender<bool>,
    thread_id: Arc<Mutex<String>>,
    turn_id: Arc<Mutex<Option<String>>>,
) -> tokio::task::JoinHandle<()> {
    tokio::spawn(
        async move {
            let mut lines = BufReader::new(stdout).lines();
            let mut last_stop = None;
            let mut last_extension_error = None;
            let mut first_line = true;
            while let Ok(Some(line)) = lines.next_line().await {
                if first_line {
                    tracing::info!(process_elapsed_ms = started_at.elapsed().as_millis(),
                        "Pi first stdout received");
                    first_line = false;
                }
                let Ok(frame) = serde_json::from_str::<Value>(&line) else {
                    tracing::warn!(output = %line, "pi emitted non-JSON stdout");
                    continue;
                };
                if let Some(id) = frame.get("id").and_then(Value::as_i64) {
                    tracing::info!(request_id = id, method = ?frame.get("command"),
                        success = ?frame.get("success"),
                        process_elapsed_ms = started_at.elapsed().as_millis(),
                        "Pi RPC response received");
                    if let Some(request) = pending.lock().await.remove(&id) {
                        let response =
                            if frame.get("success").and_then(Value::as_bool) != Some(true) {
                                let message = frame
                                    .get("error")
                                    .and_then(Value::as_str)
                                    .unwrap_or("pi rpc returned success=false")
                                    .to_owned();
                                Err(ProviderError::Protocol(message))
                            } else {
                                if let Some(accepted_turn) = request.turn_id {
                                    *turn_id.lock().await = Some(accepted_turn.clone());
                                    last_stop = None;
                                    last_extension_error = None;
                                    let _ = notifications.send(ProviderNotification::TurnStarted {
                                        thread_id: thread_id.lock().await.clone(),
                                        turn_id: accepted_turn,
                                    });
                                }
                                Ok(frame)
                            };
                        let _ = request.response.send(response);
                    } else {
                        tracing::warn!(request_id = id,
                            "Pi RPC response has no pending request (late or unmatched)");
                    }
                    continue;
                }
                let current_thread = thread_id.lock().await.clone();
                let current_turn = turn_id.lock().await.clone();
                let Some(current_turn) = current_turn else {
                    tracing::trace!(method = ?frame.get("type"), thread_id = %current_thread, "Pi idle activity");
                    continue;
                };
                if let Some(notification) =
                    parse_pi_event(&frame, &current_thread, &current_turn, &mut last_stop, &mut last_extension_error)
                {
                    if matches!(notification, ProviderNotification::TurnCompleted { .. }) {
                        *turn_id.lock().await = None;
                    }
                    let _ = notifications.send(notification);
                }
            }
            let drained = std::mem::take(&mut *pending.lock().await);
            for request in drained.into_values() {
                let _ = request.response.send(Err(ProviderError::Disconnected));
            }
            let _ = notifications.send(ProviderNotification::Disconnected);
            closed.send_replace(true);
        }
        .in_current_span(),
    )
}

fn spawn_pi_stderr(
    stderr: tokio::process::ChildStderr,
    native_home: Option<std::path::PathBuf>,
) -> tokio::task::JoinHandle<()> {
    tokio::spawn(
        async move {
            let mut lines = BufReader::new(stderr).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                tracing::warn!(provider = "pi", native.home = ?native_home, output = %line, "provider diagnostic");
            }
        }
        .in_current_span(),
    )
}

fn parse_pi_event(
    frame: &Value,
    thread_id: &str,
    turn_id: &str,
    last_stop: &mut Option<(String, Option<String>)>,
    last_extension_error: &mut Option<String>,
) -> Option<ProviderNotification> {
    let event_type = frame.get("type")?.as_str()?;
    if event_type == "agent_start" {
        *last_stop = None;
    }
    if event_type == "message_end" {
        let message = &frame["message"];
        if message["role"] == "assistant" {
            *last_stop = message["stopReason"].as_str().map(|reason| {
                (
                    reason.to_owned(),
                    message["errorMessage"]
                        .as_str()
                        .filter(|error| !error.is_empty())
                        .map(str::to_owned),
                )
            });
        }
    }
    if event_type == "extension_error" && frame["event"] == "agent_end" {
        let path = frame["extensionPath"].as_str().unwrap_or("unknown extension");
        let detail = frame["error"].as_str().unwrap_or("unknown error");
        *last_extension_error = Some(format!("Pi {path} agent_end failed: {detail}"));
    }
    match event_type {
        // Pi may persist, compact, or retry after message_end. Only settled
        // closes this physical run; a transient error must not abort recovery.
        "agent_settled" => {
            let cancelled = frame["cancelled"] == true;
            let completed = !cancelled
                && last_extension_error.is_none()
                && last_stop.as_ref().is_some_and(|(reason, _)| reason == "stop");
            let stop_error =
                last_stop.as_ref().and_then(|(_, error)| error.clone()).unwrap_or_else(|| {
                    format!(
                        "Pi settled with stop reason {:?}",
                        last_stop.as_ref().map(|(reason, _)| reason)
                    )
                });
            Some(ProviderNotification::TurnCompleted {
                thread_id: thread_id.to_owned(),
                turn_id: turn_id.to_owned(),
                status: if completed {
                    "completed"
                } else if cancelled && last_extension_error.is_none() {
                    "interrupted"
                } else {
                    "failed"
                }
                .into(),
                error: if completed || cancelled && last_extension_error.is_none() {
                    None
                } else {
                    Some(match last_extension_error {
                        Some(extension_error)
                            if last_stop.as_ref().is_some_and(|(reason, _)| reason != "stop") =>
                        {
                            format!("{stop_error}; {extension_error}")
                        }
                        Some(extension_error) => extension_error.clone(),
                        None => stop_error,
                    })
                },
            })
        }
        _ => {
            tracing::trace!(method = event_type, %thread_id, %turn_id, "Pi activity");
            None
        }
    }
}
