//! Bub's native stdio ACP boundary. Queue policy stays in Braid.
use super::process::NativeProcess;
use super::{
    AgentProvider, BubConfig, PendingRequests, Profile, ProviderError, ProviderNotification,
    ProviderSession, ProviderTurn, REQUEST_TIMEOUT, path_text, required_string,
};
use crate::agent_session::CliContext;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    process::Stdio,
    sync::{
        Arc,
        atomic::{AtomicI64, Ordering},
    },
};
use tokio::{
    io::{AsyncBufReadExt, AsyncWriteExt, BufReader},
    process::{ChildStdin, Command},
    sync::{Mutex, broadcast, oneshot, watch},
    time::{Duration, timeout},
};
use tracing::Instrument as _;

const CHANNEL: &str = "acp-server";
const MANIFEST: &str = "braid-session.json";

#[derive(Debug, Deserialize)]
struct NativeSession {
    session_id: String,
    cwd: PathBuf,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub(super) struct BubSessionRecord {
    pub session_id: String,
    pub cwd: PathBuf,
    pub tape: PathBuf,
    context: Option<String>,
    submitted: Vec<SubmittedMessage>,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
struct SubmittedMessage {
    message: String,
    native_text: String,
    after_entry_id: u64,
}

impl BubSessionRecord {
    pub(super) fn read(home: &Path) -> Result<Self, ProviderError> {
        let path = home.join(MANIFEST);
        let bytes = fs::read(&path).map_err(|error| file_error(&path, error))?;
        serde_json::from_slice(&bytes).map_err(|error| {
            ProviderError::Protocol(format!("{}: {error}", home.join(MANIFEST).display()))
        })
    }

    pub(super) fn history_is_missing(&self) -> Result<bool, ProviderError> {
        if self.submitted.is_empty() {
            return Ok(false);
        }
        match fs::metadata(&self.tape) {
            Ok(metadata) if metadata.is_file() => Ok(false),
            Ok(_) => Err(ProviderError::Protocol(format!(
                "Bub tape path is not a file: {}",
                self.tape.display()
            ))),
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(true),
            Err(error) => Err(file_error(&self.tape, error)),
        }
    }

    fn save(&self, home: &Path) -> Result<(), ProviderError> {
        let temporary = home.join("braid-session.json.tmp");
        fs::write(
            &temporary,
            serde_json::to_vec_pretty(self)
                .map_err(|error| ProviderError::Protocol(error.to_string()))?,
        )
        .map_err(|error| file_error(&temporary, error))?;
        fs::rename(&temporary, home.join(MANIFEST))
            .map_err(|error| file_error(&temporary, error))?;
        Ok(())
    }

    pub(super) fn validate(&self, home: &Path, id: &str, cwd: &Path) -> Result<(), ProviderError> {
        if id.len() != 32 || !id.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(ProviderError::Protocol(format!("invalid Bub session identity {id:?}")));
        }
        if self.session_id != id
            || self.cwd != cwd.canonicalize().map_err(|error| file_error(cwd, error))?
        {
            return Err(ProviderError::Protocol(
                "Bub session identity or cwd does not match the persisted binding".into(),
            ));
        }
        let metadata_path = home.join("acp-sessions.json");
        let bytes = fs::read(&metadata_path).map_err(|error| file_error(&metadata_path, error))?;
        let metadata: Vec<NativeSession> = serde_json::from_slice(&bytes)
            .map_err(|error| ProviderError::Protocol(format!("Bub acp-sessions.json: {error}")))?;
        let mut matches = metadata.iter().filter(|entry| entry.session_id == id);
        let unique =
            matches.next().is_some_and(|entry| entry.cwd == self.cwd) && matches.next().is_none();
        if !unique {
            return Err(ProviderError::Protocol(format!(
                "Bub metadata does not prove a unique session {id} at {}",
                self.cwd.display()
            )));
        }
        if self.tape != tape_path(home, &self.cwd, id) {
            return Err(ProviderError::Protocol(
                "Bub tape path does not match the persisted identity".into(),
            ));
        }
        Ok(())
    }
}

fn tape_path(home: &Path, cwd: &Path, id: &str) -> PathBuf {
    let workspace = format!("{:x}", md5::compute(cwd.to_string_lossy().as_bytes()));
    let session = format!("{:x}", md5::compute(format!("{CHANNEL}:{id}")));
    home.join("tapes").join(format!("{}__{}.jsonl", &workspace[..16], &session[..16]))
}

#[derive(Clone)]
pub struct BubProvider {
    home: PathBuf,
    writer: Arc<Mutex<Option<ChildStdin>>>,
    pending: Arc<Mutex<PendingRequests>>,
    next_id: Arc<AtomicI64>,
    notifications: broadcast::Sender<ProviderNotification>,
    closed: watch::Sender<bool>,
    process: Arc<NativeProcess>,
    active: Arc<Mutex<Option<(String, String)>>>,
    record: Arc<Mutex<Option<BubSessionRecord>>>,
    // Serialize control-plane mutation, not the long-running prompt response.
    control: Arc<Mutex<()>>,
}

impl BubProvider {
    pub(super) async fn connect(
        config: &BubConfig,
        profile: &Profile,
        cli: &CliContext,
    ) -> Result<Self, ProviderError> {
        let mut hooks = configured_command(config, profile, cli)?;
        let report = timeout(
            Duration::from_secs(config.startup_timeout_seconds),
            hooks.arg("hooks").output(),
        )
        .await
        .map_err(|_| ProviderError::Timeout { method: "Bub hooks".into() })??;
        let stdout = String::from_utf8_lossy(&report.stdout);
        let has_session_prompt = stdout.lines().any(|line| {
            line.strip_prefix("system_prompt: ")
                .is_some_and(|names| names.split(", ").any(|name| name == "session-prompt"))
        });
        let has_file_store = stdout.lines().any(|line| line == "provide_tape_store: builtin");
        if !report.status.success() || !has_session_prompt || !has_file_store {
            return Err(ProviderError::Protocol(format!(
                "Bub requires the official session-prompt plugin and builtin FileTapeStore; hooks status {}: {}{}",
                report.status,
                stdout,
                String::from_utf8_lossy(&report.stderr)
            )));
        }
        let mut command = configured_command(config, profile, cli)?;
        command.args(["acp", "--transport", "stdio"]);
        let mut child = command.spawn()?;
        let writer = child
            .stdin
            .take()
            .ok_or_else(|| ProviderError::Protocol("Bub stdin was not piped".into()))?;
        let stdout = child
            .stdout
            .take()
            .ok_or_else(|| ProviderError::Protocol("Bub stdout was not piped".into()))?;
        let stderr = child
            .stderr
            .take()
            .ok_or_else(|| ProviderError::Protocol("Bub stderr was not piped".into()))?;
        let (notifications, _) = broadcast::channel(512);
        let (closed, _) = watch::channel(false);
        let provider = Self {
            home: config.home.clone(),
            writer: Arc::new(Mutex::new(Some(writer))),
            pending: Arc::new(Mutex::new(BTreeMap::new())),
            next_id: Arc::new(AtomicI64::new(1)),
            notifications,
            closed,
            process: Arc::new(NativeProcess::new(child)),
            active: Arc::new(Mutex::new(None)),
            record: Arc::new(Mutex::new(None)),
            control: Arc::new(Mutex::new(())),
        };
        provider.read_stdout(stdout);
        let home = provider.home.clone();
        tokio::spawn(async move {
            let mut lines = BufReader::new(stderr).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                tracing::info!(native_home = %home.display(), output = %line, "Bub native stderr");
            }
        }.in_current_span());
        let initialized = provider.request("initialize", json!({"protocolVersion":1,"clientCapabilities":{},"clientInfo":{"name":"braid","version":env!("CARGO_PKG_VERSION")}}), Duration::from_secs(config.startup_timeout_seconds)).await;
        match initialized {
            Ok(result)
                if result["protocolVersion"] == 1
                    && result["agentCapabilities"]["loadSession"] == true =>
            {
                Ok(provider)
            }
            result => {
                let reason = match result {
                    Ok(value) => {
                        format!("Bub ACP initialization lacks protocol 1/loadSession: {value}")
                    }
                    Err(error) => error.to_string(),
                };
                provider.close_native().await?;
                Err(ProviderError::Protocol(reason))
            }
        }
    }

    pub(super) async fn close_native(&self) -> Result<(), ProviderError> {
        // EOF enters Bub's native shutdown path. Process teardown still proves
        // the complete owned execution stopped, including a broken ACP peer.
        self.writer.lock().await.take();
        self.process.stop(true).await?;
        self.closed.send_replace(true);
        Ok(())
    }

    pub(super) async fn native_record(&self) -> Option<BubSessionRecord> {
        self.record.lock().await.clone()
    }

    async fn write(&self, frame: &Value) -> Result<(), ProviderError> {
        let mut writer = self.writer.lock().await;
        let writer = writer.as_mut().ok_or(ProviderError::Disconnected)?;
        let mut bytes = serde_json::to_vec(frame)
            .map_err(|error| ProviderError::Protocol(error.to_string()))?;
        bytes.push(b'\n');
        writer.write_all(&bytes).await?;
        writer.flush().await?;
        Ok(())
    }

    async fn begin_request(
        &self,
        method: &str,
        params: Value,
    ) -> Result<(i64, oneshot::Receiver<Result<Value, ProviderError>>), ProviderError> {
        if *self.closed.borrow() {
            return Err(ProviderError::Disconnected);
        }
        let id = self.next_id.fetch_add(1, Ordering::Relaxed);
        let (sender, receiver) = oneshot::channel();
        self.pending.lock().await.insert(id, sender);
        if let Err(error) =
            self.write(&json!({"jsonrpc":"2.0","id":id,"method":method,"params":params})).await
        {
            self.pending.lock().await.remove(&id);
            return Err(error);
        }
        Ok((id, receiver))
    }

    async fn request(
        &self,
        method: &str,
        params: Value,
        deadline: Duration,
    ) -> Result<Value, ProviderError> {
        let (id, receiver) = self.begin_request(method, params).await?;
        match timeout(deadline, receiver).await {
            Ok(result) => result.map_err(|_| ProviderError::Disconnected)?,
            Err(_) => {
                self.pending.lock().await.remove(&id);
                Err(ProviderError::Timeout { method: method.into() })
            }
        }
    }

    fn read_stdout(&self, stdout: tokio::process::ChildStdout) {
        let provider = self.clone();
        tokio::spawn(async move {
            let mut lines = BufReader::new(stdout).lines();
            while let Ok(Some(line)) = lines.next_line().await {
                let Ok(frame) = serde_json::from_str::<Value>(&line) else { tracing::error!(output = %line, "Bub emitted invalid ACP stdout"); break };
                if frame.get("method").is_some() {
                    if let Some(id) = frame.get("id") {
                        // No filesystem, terminal or elicitation capabilities
                        // are advertised: Bub retains its own native tools.
                        if provider.write(&json!({"jsonrpc":"2.0","id":id,"error":{"code":-32601,"message":"Braid does not provide this ACP client method","data":{"method":frame["method"]}}})).await.is_err() { break; }
                    } else {
                        let active = provider.active.lock().await.clone();
                        tracing::info!(frame = %frame, "Bub ACP activity");
                        let _ = provider.notifications.send(ProviderNotification::Activity { method: frame["method"].as_str().unwrap_or("unknown").into(), thread_id: frame["params"]["sessionId"].as_str().map(str::to_owned), turn_id: active.map(|(_, turn)| turn) });
                    }
                } else if let Some(id) = frame["id"].as_i64() {
                    if let Some(sender) = provider.pending.lock().await.remove(&id) {
                        let result = if let Some(error) = frame.get("error") { Err(ProviderError::Protocol(format!("Bub ACP response error: {error}"))) } else if let Some(result) = frame.get("result") { Ok(result.clone()) } else { Err(ProviderError::Protocol(format!("Bub ACP response lacks result/error: {frame}"))) };
                        let _ = sender.send(result);
                    }
                }
            }
            provider.closed.send_replace(true);
            for sender in std::mem::take(&mut *provider.pending.lock().await).into_values() { let _ = sender.send(Err(ProviderError::Disconnected)); }
            let _ = provider.notifications.send(ProviderNotification::Disconnected);
        }.in_current_span());
    }

    fn write_instructions(&self, id: &str, instructions: &str) -> Result<(), ProviderError> {
        let path = self.home.join("sessions").join(format!("{CHANNEL}:{id}")).join("AGENTS.md");
        fs::create_dir_all(path.parent().expect("session prompt parent"))
            .map_err(|error| file_error(&path, error))?;
        fs::write(&path, instructions).map_err(|error| file_error(&path, error))?;
        Ok(())
    }

    async fn select_reasoning(&self, id: &str, profile: &Profile) -> Result<(), ProviderError> {
        if let Some(reasoning) = &profile.reasoning {
            self.request(
                "session/set_config_option",
                json!({"sessionId":id,"configId":"reasoning_effort","value":reasoning}),
                REQUEST_TIMEOUT,
            )
            .await?;
        }
        Ok(())
    }
}

#[async_trait::async_trait]
impl AgentProvider for BubProvider {
    fn subscribe(&self) -> broadcast::Receiver<ProviderNotification> {
        self.notifications.subscribe()
    }
    async fn closed(&self) {
        let mut receiver = self.closed.subscribe();
        while !*receiver.borrow() && receiver.changed().await.is_ok() {}
    }

    async fn start_session(
        &self,
        profile: &Profile,
        instructions: &str,
    ) -> Result<ProviderSession, ProviderError> {
        let _control = self.control.lock().await;
        let cwd = profile
            .workspace()
            .canonicalize()
            .map_err(|error| file_error(profile.workspace(), error))?;
        let result = self
            .request(
                "session/new",
                json!({"cwd":path_text(profile.workspace())?,"mcpServers":[]}),
                REQUEST_TIMEOUT,
            )
            .await?;
        let id = required_string(&result, "sessionId", "Bub session/new")
            .map_err(|error| ProviderError::CreatedWithoutIdentity(error.to_string()))?;
        if id.len() != 32 || !id.bytes().all(|byte| byte.is_ascii_hexdigit()) {
            return Err(ProviderError::CreatedWithoutIdentity(format!(
                "Bub returned unexpected session ID {id:?}"
            )));
        }
        let record = BubSessionRecord {
            session_id: id.clone(),
            tape: tape_path(&self.home, &cwd, &id),
            cwd,
            context: None,
            submitted: Vec::new(),
        };
        *self.record.lock().await = Some(record.clone());
        record.save(&self.home)?;
        self.write_instructions(&id, instructions)?;
        self.select_reasoning(&id, profile).await?;
        *self.record.lock().await = Some(record);
        Ok(ProviderSession { thread_id: id })
    }

    async fn inject_context(&self, id: &str, context: &str) -> Result<(), ProviderError> {
        let _control = self.control.lock().await;
        let mut record = self.record.lock().await;
        let record = record
            .as_mut()
            .ok_or_else(|| ProviderError::Protocol("Bub session has no durable binding".into()))?;
        if record.session_id != id || !record.submitted.is_empty() {
            return Err(ProviderError::Protocol(
                "Bub context can only be staged before its first prompt".into(),
            ));
        }
        record.context = Some(context.into());
        record.save(&self.home)
    }

    async fn resume_session(
        &self,
        id: &str,
        profile: &Profile,
        instructions: &str,
    ) -> Result<ProviderSession, ProviderError> {
        let _control = self.control.lock().await;
        let record = BubSessionRecord::read(&self.home)?;
        record.validate(&self.home, id, profile.workspace())?;
        if record.history_is_missing()? {
            return Err(ProviderError::Protocol(format!(
                "Bub native tape is unavailable: {}",
                record.tape.display()
            )));
        }
        self.request(
            "session/load",
            json!({"sessionId":id,"cwd":path_text(&record.cwd)?,"mcpServers":[]}),
            REQUEST_TIMEOUT,
        )
        .await?;
        self.write_instructions(id, instructions)?;
        self.select_reasoning(id, profile).await?;
        *self.record.lock().await = Some(record);
        Ok(ProviderSession { thread_id: id.into() })
    }

    async fn start_turn(
        &self,
        id: &str,
        _profile: &Profile,
        message: &str,
    ) -> Result<ProviderTurn, ProviderError> {
        let _control = self.control.lock().await;
        let mut active = self.active.lock().await;
        if active.is_some() {
            return Err(ProviderError::Deferred("Bub already has an active prompt".into()));
        }
        let mut record = self.record.lock().await;
        let record = record
            .as_mut()
            .ok_or_else(|| ProviderError::Protocol("Bub session has no durable binding".into()))?;
        if record.session_id != id {
            return Err(ProviderError::Protocol("Bub turn targets another session".into()));
        }
        let entries = native_entries(&record.tape)?;
        let context_present = record.submitted.first().is_some_and(|first| {
            entries.iter().any(|entry| {
                entry["kind"] == "message"
                    && entry["payload"]["role"] == "user"
                    && entry["payload"]["content"]
                        .as_str()
                        .is_some_and(|text| clean_native_user(text, id) == first.native_text)
            })
        });
        let native_text = if !context_present {
            record
                .context
                .as_ref()
                .map_or_else(|| message.to_owned(), |context| format!("{context}\n\n{message}"))
        } else {
            message.to_owned()
        };
        // Persist the exact body before submission; an ambiguous disconnect
        // retains both the candidate body and the native tape for recovery.
        let after_entry_id =
            entries.iter().filter_map(|entry| entry["id"].as_u64()).max().unwrap_or(0);
        record.submitted.push(SubmittedMessage {
            message: message.into(),
            native_text: native_text.clone(),
            after_entry_id,
        });
        record.save(&self.home)?;
        let (request, receiver) = self
            .begin_request(
                "session/prompt",
                json!({"sessionId":id,"prompt":[{"type":"text","text":native_text}]}),
            )
            .await?;
        let turn = format!("bub-{request}-{}", uuid::Uuid::now_v7());
        *active = Some((id.into(), turn.clone()));
        let _ = self.notifications.send(ProviderNotification::TurnStarted {
            thread_id: id.into(),
            turn_id: turn.clone(),
        });
        let provider = self.clone();
        let thread_id = id.to_owned();
        let turn_id = turn.clone();
        tokio::spawn(
            async move {
                // session/prompt resolves at the terminal, not at admission.
                let result = receiver.await.unwrap_or(Err(ProviderError::Disconnected));
                let mut active = provider.active.lock().await;
                if active.as_ref() != Some(&(thread_id.clone(), turn_id.clone())) {
                    return;
                }
                *active = None;
                let (status, error) = match result {
                    Ok(value) => match value["stopReason"].as_str() {
                        Some("end_turn") => ("completed", None),
                        Some("cancelled") => ("interrupted", None),
                        _ => ("failed", Some(format!("Bub prompt stop result: {value}"))),
                    },
                    Err(ProviderError::Disconnected) => {
                        ("unknown", Some("Bub ACP disconnected before prompt terminal".into()))
                    }
                    Err(error) => ("failed", Some(error.to_string())),
                };
                let _ = provider.notifications.send(ProviderNotification::TurnCompleted {
                    thread_id,
                    turn_id,
                    status: status.into(),
                    error,
                });
            }
            .in_current_span(),
        );
        Ok(ProviderTurn { turn_id: turn })
    }

    async fn steer(&self, _id: &str, _turn: &str, _message: &str) -> Result<(), ProviderError> {
        // Bub's private extension may start an uncorrelated background turn.
        // Deferred leaves ownership of this input in Braid's durable queue.
        Err(ProviderError::Deferred("Bub ACP cannot guarantee steering into the observed turn; retained for the next idle turn".into()))
    }

    async fn interrupt(&self, id: &str, turn: &str) -> Result<(), ProviderError> {
        if self.active.lock().await.as_ref() != Some(&(id.into(), turn.into())) {
            return Ok(());
        }
        if let Err(error) = self
            .write(&json!({"jsonrpc":"2.0","method":"session/cancel","params":{"sessionId":id}}))
            .await
        {
            tracing::warn!(%error, session_id = id, turn_id = turn, "Bub cancel notification failed; stopping owned process");
        }
        // The pinned plugin's cancel routes to a no-op. Stop the owned process;
        // EOF is Unknown unless an actual prompt terminal was already observed.
        self.close_native().await
    }

    async fn message_was_processed(&self, id: &str, message: &str) -> Result<bool, ProviderError> {
        let record =
            self.record.lock().await.clone().ok_or_else(|| {
                ProviderError::Protocol("Bub session has no durable binding".into())
            })?;
        if record.session_id != id {
            return Err(ProviderError::Protocol("Bub receipt targets another session".into()));
        }
        let Some(submitted) = record.submitted.iter().rev().find(|entry| entry.message == message)
        else {
            return Ok(false);
        };
        if !record.tape.is_file() {
            return Err(ProviderError::Protocol(format!(
                "Bub native tape is unavailable: {}",
                record.tape.display()
            )));
        }
        let mut matched = false;
        let mut matched_run: Option<String> = None;
        for entry in native_entries(&record.tape)? {
            if entry["id"].as_u64().is_none_or(|entry_id| entry_id <= submitted.after_entry_id) {
                continue;
            }
            if matched
                && entry["kind"] == "tool_call"
                && matched_run
                    .as_ref()
                    .is_some_and(|run| entry["meta"]["run_id"].as_str() == Some(run.as_str()))
                && entry["payload"]["calls"].as_array().is_some_and(|calls| !calls.is_empty())
            {
                return Ok(true);
            }
            if entry["kind"] != "message" {
                continue;
            }
            if entry["payload"]["role"] == "user" {
                let text = entry["payload"]["content"].as_str().ok_or_else(|| {
                    ProviderError::Protocol("Bub user tape content is not text".into())
                })?;
                let text = clean_native_user(text, id);
                if text == submitted.native_text {
                    matched = true;
                    matched_run = entry["meta"]["run_id"].as_str().map(str::to_owned);
                }
            } else if matched && entry["payload"]["role"] == "assistant" {
                return Ok(true);
            }
        }
        Ok(false)
    }
}

fn clean_native_user<'a>(text: &'a str, id: &str) -> &'a str {
    let Some((header, rest)) = text.split_once('\n') else { return text };
    if header != format!("channel=${CHANNEL}|chat_id={id}") {
        return text;
    }
    let Some((date, body)) = rest.split_once('\n') else { return text };
    if date.starts_with("---Date: ") && date.ends_with("---") { body } else { text }
}

fn native_entries(path: &Path) -> Result<Vec<Value>, ProviderError> {
    let bytes = match fs::read(path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(Vec::new()),
        Err(error) => return Err(file_error(path, error)),
    };
    let mut entries = Vec::new();
    for line in bytes.split_inclusive(|byte| *byte == b'\n') {
        // Native writes can still be in progress. A partial line is no receipt.
        if line.last() != Some(&b'\n') {
            break;
        }
        if line.len() == 1 {
            continue;
        }
        entries.push(serde_json::from_slice(line).map_err(|error| {
            ProviderError::Protocol(format!("Bub native tape {}: {error}", path.display()))
        })?);
    }
    Ok(entries)
}

fn configured_command(
    config: &BubConfig,
    profile: &Profile,
    cli: &CliContext,
) -> Result<Command, ProviderError> {
    let mut command = Command::new(&config.executable);
    #[cfg(unix)]
    command.process_group(0);
    if let Some(exe_dir) = std::env::current_exe()?.parent() {
        let mut paths: Vec<_> =
            std::env::split_paths(&std::env::var_os("PATH").unwrap_or_default()).collect();
        paths.insert(0, exe_dir.to_path_buf());
        command.env(
            "PATH",
            std::env::join_paths(paths)
                .map_err(|error| ProviderError::Protocol(error.to_string()))?,
        );
    }
    command
        .current_dir(profile.workspace())
        .env("BUB_HOME", &config.home)
        .env("BUB_ACP_SERVER_CHANNEL_NAME", CHANNEL)
        .env("BUB_ACP_SERVER_CONTEXT_WINDOW_SIZE", profile.context_window_tokens.to_string())
        .env("BRAID_AGENT_RUNTIME", "1")
        .env("BRAID_STATE", &cli.state)
        .env("BRAID_CLI_BINDING_ID", &cli.binding_id)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .kill_on_drop(true);
    if let Some(model) = &profile.model {
        let model = if profile.provider.is_empty() {
            model.clone()
        } else {
            format!("{}:{model}", profile.provider)
        };
        command.env("BUB_MODEL", model);
    } else if !profile.provider.is_empty() {
        return Err(ProviderError::Protocol(
            "Bub profile.provider requires a profile.model".into(),
        ));
    }
    if let Some(key) =
        config.api_key().map_err(|error| ProviderError::Protocol(error.to_string()))?
    {
        command.env("BUB_API_KEY", key);
    }
    Ok(command)
}

fn file_error(path: &Path, error: std::io::Error) -> ProviderError {
    ProviderError::Protocol(format!("Bub native material {}: {error}", path.display()))
}
