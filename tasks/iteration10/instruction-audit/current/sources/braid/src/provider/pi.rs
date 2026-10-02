#![allow(clippy::wildcard_imports)]
use super::*;
use std::path::PathBuf;
use std::sync::atomic::AtomicBool;
use std::io::BufRead as _;

struct PiProcess {
    writer: ChildStdin,
    child: Child,
    #[allow(dead_code)]
    stdout_handle: tokio::task::JoinHandle<()>,
    #[allow(dead_code)]
    stderr_handle: tokio::task::JoinHandle<()>,
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
        let Some(process) = state.process.take() else { return Ok(()) };
        let PiProcess { writer, mut child, .. } = process;
        // EOF invokes Pi's own runtime disposal and extension shutdown hooks.
        // Internal subagents belong to Pi, not to Braid's process supervisor.
        drop(writer);
        let result = match timeout(Duration::from_secs(180), child.wait()).await {
            Ok(Ok(status)) if status.success() => Ok(()),
            Ok(Ok(status)) => Err(ProviderError::Protocol(format!("Pi exited with {status}"))),
            Ok(Err(error)) => Err(ProviderError::Protocol(error.to_string())),
            Err(_) => {
                let _ = child.kill().await;
                Err(ProviderError::Timeout { method: "Pi shutdown".into() })
            }
        };
        if result.is_err() {
            self.teardown_failed.store(true, Ordering::Release);
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
        let state_resp = Self::request(state, json!({"type": "get_state"}))
            .await?;
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
        Ok((session_file.to_owned(), session_id.to_owned()))
    }

    fn spawn(
        &self,
        state: &mut PiState,
        profile: &Profile,
        workspace: &Path,
        session: Option<&str>,
    ) -> Result<(), ProviderError> {
        let mut cmd = Command::new(&state.config.executable);
        cmd.args(["--mode", "rpc"])
            .env("BRAID_AGENT_RUNTIME", "1")
            .env("BRAID_STATE", &state.cli.state)
            .env("BRAID_CLI_BINDING_ID", &state.cli.binding_id);
        let session_dir = state
            .config
            .home
            .clone()
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

        let mut child = cmd.spawn()?;
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
            Arc::clone(&state.pending),
            self.notifications.clone(),
            self.closed.clone(),
            Arc::clone(&self.thread_id),
            Arc::clone(&self.turn_id),
        );
        let stderr_handle = spawn_pi_stderr(stderr, state.config.home.clone());
        state.process = Some(PiProcess { writer, child, stdout_handle, stderr_handle });
        Ok(())
    }

    async fn request(state: &mut PiState, frame: Value) -> Result<Value, ProviderError> {
        Self::request_with_turn(state, frame, None).await
    }

    async fn request_with_turn(state: &mut PiState, frame: Value, turn_id: Option<String>) -> Result<Value, ProviderError> {
        let id = state.next_request_id.fetch_add(1, Ordering::Relaxed);
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
        if let Err(error) = process.writer.write_all(&bytes).await {
            state.pending.lock().await.remove(&id);
            return Err(ProviderError::Start(error));
        }
        if let Err(error) = process.writer.flush().await {
            state.pending.lock().await.remove(&id);
            return Err(ProviderError::Start(error));
        }

        match timeout(REQUEST_TIMEOUT, receiver).await {
            Ok(Ok(response)) => response,
            Ok(Err(_)) => Err(ProviderError::Disconnected),
            Err(_) => {
                state.pending.lock().await.remove(&id);
                Err(ProviderError::Timeout { method: "pi_rpc".into() })
            }
        }
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

        self.spawn(&mut state, profile, profile.workspace(), None)?;

        let result =
            Self::request(&mut state, json!({"type": "new_session", "name": "braid-session"}))
                .await?;
        Self::success_or_protocol(&result, "new_session")?;

        let (session_file, _session_id) = self.refresh_session_identity(&mut state).await.map_err(
            |error| match error {
                ProviderError::CreatedWithoutIdentity(_) => error,
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

        let (session_file, _session_id) = self
            .refresh_session_identity(&mut state)
            .await
            .inspect_err(|error| tracing::warn!(%error, "Pi get_state failed while resuming session"))?;
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
        if native_is_busy(&native) {
            return Err(ProviderError::Deferred("Pi is streaming or compacting".into()));
        }
        let turn_id = uuid::Uuid::now_v7().to_string();
        *self.thread_id.lock().await = state.session.clone().unwrap_or_default();
        let result = Self::request_with_turn(
            &mut state, json!({"type": "prompt", "message": message}), Some(turn_id.clone()),
        ).await;
        match result {
            Ok(result) => Self::success_or_protocol(&result, "prompt")?,
            Err(ProviderError::Protocol(message)) => {
                // Pi has no typed busy response. Confirm native state instead of
                // recognizing error strings; a rejected prompt never owns a turn.
                let native = Self::request(&mut state, json!({"type": "get_state"})).await?;
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

    async fn message_was_processed(&self, thread_id: &str, message: &str) -> Result<bool, ProviderError> {
        let file = std::fs::File::open(thread_id).map_err(|error| {
            ProviderError::Protocol(format!("cannot read Pi native session {thread_id}: {error}"))
        })?;
        let mut notice_seen = false;
        for line in std::io::BufReader::new(file).lines() {
            let line = line.map_err(|error| {
                ProviderError::Protocol(format!("cannot read Pi native session {thread_id}: {error}"))
            })?;
            let entry: Value = serde_json::from_str(&line)
                .map_err(|error| ProviderError::Protocol(format!("invalid Pi session entry: {error}")))?;
            if entry["type"] != "message" { continue }
            let role = entry["message"]["role"].as_str();
            if role == Some("user") {
                notice_seen |= entry["message"]["content"].as_array().is_some_and(|parts| {
                    parts.iter().any(|part| {
                        if part["type"] != "text" { return false }
                        part["text"].as_str().is_some_and(|text| {
                            text == message || text.strip_suffix(message).is_some_and(|prefix| prefix.ends_with("\n\n"))
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

#[allow(clippy::too_many_arguments)]
fn spawn_pi_stdout(
    stdout: tokio::process::ChildStdout,
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
            while let Ok(Some(line)) = lines.next_line().await {
                let Ok(frame) = serde_json::from_str::<Value>(&line) else {
                    tracing::warn!(output = %line, "pi emitted non-JSON stdout");
                    continue;
                };
                if let Some(id) = frame.get("id").and_then(Value::as_i64) {
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
                                    let _ = notifications.send(ProviderNotification::TurnStarted {
                                        thread_id: thread_id.lock().await.clone(),
                                        turn_id: accepted_turn,
                                    });
                                }
                                Ok(frame)
                            };
                        let _ = request.response.send(response);
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
                    parse_pi_event(&frame, &current_thread, &current_turn, &mut last_stop)
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
                    message["errorMessage"].as_str().filter(|error| !error.is_empty()).map(str::to_owned),
                )
            });
        }
    }
    match event_type {
        // Pi may persist, compact, or retry after message_end. Only settled
        // closes this physical run; a transient error must not abort recovery.
        "agent_settled" => {
            let completed = last_stop.as_ref().is_some_and(|(reason, _)| reason == "stop");
            Some(ProviderNotification::TurnCompleted {
                thread_id: thread_id.to_owned(),
                turn_id: turn_id.to_owned(),
                status: if completed { "completed" } else { "failed" }.into(),
                error: if completed {
                    None
                } else {
                    Some(
                        last_stop.as_ref().and_then(|(_, error)| error.clone()).unwrap_or_else(|| {
                            format!("Pi settled with stop reason {:?}", last_stop.as_ref().map(|(reason, _)| reason))
                        }),
                    )
                },
            })
        }
        _ => {
            tracing::trace!(method = event_type, %thread_id, %turn_id, "Pi activity");
            None
        },
    }
}

#[cfg(test)]
mod terminal_tests {
    use super::*;
    #[tokio::test]
    async fn context_is_consumed_only_by_an_accepted_prompt() {
        let provider = PiProvider::connect(
            &PiConfig { executable: "cat".into(), api_key_environment: None,
                api_key_file: None, home: None },
            crate::agent_session::CliContext { state: "unused".into(), binding_id: "test".into() },
            None,
        );
        let profile: Profile = serde_json::from_value(json!({
            "id":"test", "display_name":"test", "assignee_login":"test",
            "assignee_description":"test", "tags":[], "adapter_type":"pi",
            "adapter_version":"1", "provider":"", "model":null, "reasoning":null,
            "user_instructions":"", "context_soft_ratio":0.8, "context_hard_bytes":10000
        })).unwrap();
        // Inspect the actual RPC messages sent by start_turn, then acknowledge
        // them through its existing request channel. No model process is needed.
        let mut child = Command::new("cat").stdin(Stdio::piped()).stdout(Stdio::piped()).spawn().unwrap();
        let writer = child.stdin.take().unwrap();
        let stdout = child.stdout.take().unwrap();
        let pending = provider.state.lock().await.pending.clone();
        let observed = Arc::new(Mutex::new(Vec::<String>::new()));
        let captured = observed.clone();
        let reader = tokio::spawn(async move {
            let mut lines = BufReader::new(stdout).lines();
            let mut first_state = true;
            let mut reject_prompt = true;
            while let Some(line) = lines.next_line().await.unwrap() {
                let frame: Value = serde_json::from_str(&line).unwrap();
                let reply = if frame["type"] == "get_state" {
                    let busy = first_state;
                    first_state = false;
                    Ok(json!({"success":true,"data":{"isStreaming":busy}}))
                } else {
                    captured.lock().await.push(frame["message"].as_str().unwrap().to_owned());
                    if reject_prompt {
                        reject_prompt = false;
                        Err(ProviderError::Protocol("not accepted".into()))
                    } else {
                        Ok(json!({"success":true}))
                    }
                };
                pending.lock().await.remove(&frame["id"].as_i64().unwrap()).unwrap()
                    .response.send(reply).unwrap();
            }
        });
        provider.state.lock().await.process = Some(PiProcess {
            writer, child, stdout_handle: reader, stderr_handle: tokio::spawn(async {}),
        });
        provider.inject_context("s", "initial context").await.unwrap();
        assert!(matches!(provider.start_turn("s", &profile, "first").await, Err(ProviderError::Deferred(_))));
        assert!(matches!(provider.start_turn("s", &profile, "retry").await, Err(ProviderError::Protocol(_))));
        provider.start_turn("s", &profile, "accepted").await.unwrap();
        provider.start_turn("s", &profile, "next notification").await.unwrap();
        provider.inject_context("s", "rebuilt context").await.unwrap();
        provider.start_turn("s", &profile, "replacement").await.unwrap();
        assert_eq!(*observed.lock().await, vec![
            "initial context\n\nretry", "initial context\n\naccepted",
            "next notification", "rebuilt context\n\nreplacement",
        ]);
        let process = provider.state.lock().await.process.take().unwrap();
        drop(process.writer);
        process.stdout_handle.await.unwrap();
        let mut child = process.child;
        child.wait().await.unwrap();
    }

    #[tokio::test]
    async fn prompt_receipt_owns_identity_and_activity_cannot_evict_terminal() {
        // Pipe actual JSON lines through the production reader; no model or network.
        let mut child = Command::new("cat").stdin(Stdio::piped()).stdout(Stdio::piped()).spawn().unwrap();
        let mut input = child.stdin.take().unwrap();
        let (rejected_tx, rejected_rx) = oneshot::channel();
        let (accepted_tx, accepted_rx) = oneshot::channel();
        let pending = Arc::new(Mutex::new(BTreeMap::from([
            (1, PiRequest { response: rejected_tx, turn_id: Some("rejected".into()) }),
            (2, PiRequest { response: accepted_tx, turn_id: Some("new".into()) }),
        ])));
        let (notifications, mut events) = broadcast::channel(8);
        let (closed, _) = watch::channel(false);
        let reader = spawn_pi_stdout(child.stdout.take().unwrap(), pending, notifications, closed,
            Arc::new(Mutex::new("session".into())), Arc::new(Mutex::new(Some("old".into()))));
        let mut frames = vec![json!({"id":1,"success":false,"error":"rejected preflight"})];
        frames.extend((0..2048).map(|_| json!({"type":"message_update"})));
        frames.extend([
            json!({"type":"message_end","message":{"role":"assistant","stopReason":"stop"}}),
            json!({"type":"agent_settled"}),
            json!({"id":2,"success":true}),
            json!({"type":"turn_start"}),
            json!({"type":"message_end","message":{"role":"assistant","stopReason":"stop"}}),
            json!({"type":"agent_settled"}),
        ]);
        for frame in frames {
            input.write_all(format!("{frame}\n").as_bytes()).await.unwrap();
        }
        drop(input);
        reader.await.unwrap();
        child.wait().await.unwrap();
        assert!(matches!(rejected_rx.await.unwrap(), Err(ProviderError::Protocol(_))));
        accepted_rx.await.unwrap().unwrap();
        assert!(matches!(events.recv().await.unwrap(), ProviderNotification::TurnCompleted { turn_id, .. } if turn_id == "old"));
        assert!(matches!(events.recv().await.unwrap(), ProviderNotification::TurnStarted { turn_id, .. } if turn_id == "new"));
        assert!(matches!(events.recv().await.unwrap(), ProviderNotification::TurnCompleted { turn_id, .. } if turn_id == "new"));
        assert!(matches!(events.recv().await.unwrap(), ProviderNotification::Disconnected));
    }

    #[test]
    fn pi_terminal_waits_for_recovery_and_rejects_length() {
        let mut stop = None;
        for reason in ["error", "stop"] {
            let frame = json!({"type":"message_end","message":{
                "role":"assistant","stopReason":reason,"errorMessage":"provider quota exhausted"
            }});
            assert!(matches!(
                parse_pi_event(&frame, "s", "t", &mut stop),
                None
            ));
        }
        let settled = json!({"type":"agent_settled"});
        assert!(
            matches!(parse_pi_event(&settled,"s","t",&mut stop), Some(ProviderNotification::TurnCompleted { status, error, .. }) if status == "completed" && error.is_none())
        );
        let frame =
            json!({"type":"message_end","message":{"role":"assistant","stopReason":"length"}});
        parse_pi_event(&frame, "s", "t", &mut stop);
        assert!(
            matches!(parse_pi_event(&settled,"s","t",&mut stop), Some(ProviderNotification::TurnCompleted { status, .. }) if status == "failed")
        );
        let frame = json!({"type":"message_end","message":{
            "role":"assistant","stopReason":"error","errorMessage":"provider quota exhausted"
        }});
        parse_pi_event(&frame, "s", "t", &mut stop);
        assert!(matches!(
            parse_pi_event(&settled, "s", "t", &mut stop),
            Some(ProviderNotification::TurnCompleted { status, error: Some(error), .. })
                if status == "failed" && error == "provider quota exhausted"
        ));
    }
}
