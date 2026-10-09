//! Bounded evidence summaries, with explicit portable snapshots when raw recovery is required.
use anyhow::{Context as _, Result, bail, ensure};
use opentelemetry_proto::tonic::{
    collector::logs::v1::ExportLogsServiceRequest, common::v1::any_value,
};
use prost::Message as _;
use rusqlite::{Connection, OpenFlags, types::ValueRef};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    io::{BufRead as _, Write as _},
    path::{Path, PathBuf},
    time::{SystemTime, UNIX_EPOCH},
};

const CHUNK_BYTES: usize = 64 * 1024;
const RECORD_BYTES: usize = 192 * 1024;
const TABLES: &[&str] = &[
    "schema_migrations",
    "local_run",
    "work_items",
    "local_items",
    "local_comments",
    "local_subscriptions",
    "local_activity",
    "local_comment_reactions",
    "associations",
    "local_merges",
    "review_requests",
    "review_checkouts",
    "pr_review_sessions",
    "assignments",
    "agent_instances",
    "provider_sessions",
    "turns",
    "events",
    "context_resets",
    "profiles",
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CaptureMode {
    Summary,
    Portable,
}

impl CaptureMode {
    fn label(self) -> &'static str {
        match self {
            Self::Summary => "summary",
            Self::Portable => "portable",
        }
    }
}

fn digest(bytes: &[u8]) -> String {
    hex::encode(Sha256::digest(bytes))
}

fn record_digest(record: &Value) -> Result<String> {
    let mut content = record.clone();
    let fields = content.as_object_mut().context("evidence record must be an object")?;
    fields.remove("record_id");
    fields.remove("captured_at_unix_nanos");
    Ok(digest(&serde_json::to_vec(&content)?))
}

fn inventory_entry(bytes: &[u8], source: &str, kind: &str) -> Value {
    json!({"source":source,"logical_type":kind,"sha256":digest(bytes),"bytes":bytes.len()})
}

fn inventory_summary(mut entries: Vec<Value>) -> Result<Value> {
    entries.sort_by_cached_key(Value::to_string);
    let mut types: BTreeMap<String, Value> = BTreeMap::new();
    let mut bytes = 0_u64;
    for entry in &entries {
        let size = entry["bytes"].as_u64().unwrap_or(0);
        bytes = bytes.saturating_add(size);
        let kind = entry["logical_type"].as_str().unwrap_or("unknown");
        let row = types.entry(kind.to_owned()).or_insert_with(|| json!({"artifacts":0,"bytes":0}));
        row["artifacts"] = json!(row["artifacts"].as_u64().unwrap_or(0) + 1);
        row["bytes"] = json!(row["bytes"].as_u64().unwrap_or(0).saturating_add(size));
    }
    Ok(json!({"artifacts":entries.len(),"bytes":bytes,
        "content_set_sha256":digest(&serde_json::to_vec(&entries)?),"types":types}))
}

pub struct EvidenceCollector {
    run_id: String,
    emitted: BTreeSet<String>,
    since_flush: BTreeSet<String>,
    omissions: Vec<String>,
}

impl EvidenceCollector {
    pub fn new(run_id: String) -> Self {
        Self {
            run_id,
            emitted: BTreeSet::new(),
            since_flush: BTreeSet::new(),
            omissions: Vec::new(),
        }
    }

    pub fn flush_succeeded(&mut self) {
        self.since_flush.clear();
    }

    pub fn retry_since_flush(&mut self) {
        for id in std::mem::take(&mut self.since_flush) {
            self.emitted.remove(&id);
        }
    }

    fn record(
        &mut self,
        kind: &str,
        mut record: Value,
        emit: &mut impl FnMut(&Value) -> Result<bool>,
    ) -> Result<String> {
        record["schema_version"] = json!(1);
        record["run_id"] = json!(self.run_id);
        record["event_kind"] = json!(kind);
        let bytes = serde_json::to_vec(&record)?.len();
        // ponytail: manifests stay within one record; paginate references if large runs hit this ceiling.
        if bytes + 256 > RECORD_BYTES {
            let gap = format!(
                "{kind} manifest/metadata omitted: {bytes} bytes exceeds the {RECORD_BYTES}-byte record budget; raw artifact chunks already submitted remain partial"
            );
            self.omissions.push(gap.clone());
            record = if kind == "evidence_snapshot" || kind == "evidence_summary" {
                json!({"schema_version":1,"run_id":self.run_id,"event_kind":kind,
                    "final":record["final"],"native_archive":record["native_archive"],
                    "mode":record["mode"],"inventory":record["inventory"],
                    "artifacts":record["artifacts"].as_array().map(|ids| ids.iter().take(256).cloned().collect::<Vec<_>>()),
                    "coverage":{"status":"partial"},"gaps":[gap]})
            } else {
                json!({"schema_version":1,"run_id":self.run_id,"event_kind":"evidence_gap","gap":gap})
            };
        }
        let id = record_digest(&record)?;
        record["record_id"] = json!(id);
        record["captured_at_unix_nanos"] =
            json!(SystemTime::now().duration_since(UNIX_EPOCH)?.as_nanos().to_string());
        if !self.emitted.contains(&id) {
            self.emitted.insert(id.clone());
            self.since_flush.insert(id.clone());
            if emit(&record)? {
                self.flush_succeeded();
            }
        }
        Ok(id)
    }

    fn artifact(
        &mut self,
        bytes: &[u8],
        source: &str,
        kind: &str,
        metadata: &Value,
        emit: &mut impl FnMut(&Value) -> Result<bool>,
    ) -> Result<String> {
        let mut chunks = Vec::new();
        for chunk in bytes.chunks(CHUNK_BYTES) {
            chunks.push(self.record(
                "evidence_chunk",
                json!({"sha256":digest(chunk),"data_hex":hex::encode(chunk)}),
                emit,
            )?);
        }
        self.record(
            "evidence_artifact",
            json!({
                "source":source,"logical_type":kind,"metadata":metadata,
                "sha256":digest(bytes),"bytes":bytes.len(),"chunks":chunks,
            }),
            emit,
        )
    }

    fn capture_artifact(
        &mut self,
        bytes: &[u8],
        source: &str,
        kind: &str,
        metadata: &Value,
        mode: CaptureMode,
        emit: &mut impl FnMut(&Value) -> Result<bool>,
    ) -> Result<(Option<String>, Value)> {
        let id = if mode == CaptureMode::Portable {
            Some(self.artifact(bytes, source, kind, metadata, emit)?)
        } else {
            None
        };
        Ok((id, inventory_entry(bytes, source, kind)))
    }

    fn file(
        &mut self,
        path: &Path,
        source: &str,
        kind: &str,
        metadata: &Value,
        mode: CaptureMode,
        gaps: &mut Vec<String>,
        emit: &mut impl FnMut(&Value) -> Result<bool>,
    ) -> Result<Option<(Option<String>, Value)>> {
        match fs::read(path) {
            Ok(bytes) => {
                self.capture_artifact(&bytes, source, kind, metadata, mode, emit).map(Some)
            }
            Err(error) => {
                gaps.push(format!("{}: {error}", path.display()));
                Ok(None)
            }
        }
    }

    /// Capture durable inputs and a consistent object snapshot. The callback returns true
    /// when a flush succeeds; it is not a per-record delivery acknowledgment.
    #[allow(clippy::too_many_lines)] // Keep the ordered capture and its shared gap inventory together.
    pub fn capture(
        &mut self,
        state: &Path,
        native_manifest: Option<&Path>,
        final_capture: bool,
        mode: CaptureMode,
        emit: &mut impl FnMut(&Value) -> Result<bool>,
    ) -> Result<Value> {
        self.omissions.clear();
        if mode == CaptureMode::Summary {
            let current = snapshot_cooperation(&state.join("braid.sqlite3"))?;
            let native_count = current["sessions"].as_array().map_or(0, Vec::len);
            let coverage = json!({"status":"partial", "objects":true,
                "native_sessions":native_count, "native_bodies":false});
            let id = self.record("evidence_summary", json!({"mode":"summary",
                "final":final_capture, "current":current, "coverage":coverage,
                "gaps":["Complete native bodies and history are available after portable recovery."]}), emit)?;
            return Ok(json!({"run_id":self.run_id, "snapshot_id":id,
                "mode":"summary", "coverage":coverage, "native_sessions":native_count,
                "usage":[], "gaps":self.omissions}));
        }
        let mut gaps = Vec::new();
        let mut artifacts = Vec::new();
        let mut inventory = Vec::new();
        let objects = match snapshot_objects(&state.join("braid.sqlite3"), &mut gaps) {
            Ok(objects) => {
                if let Some(rows) = objects["tables"]["local_run"]["rows"].as_array() {
                    for row in rows {
                        if row["run_id"].as_str() != Some(&self.run_id) {
                            gaps.push("object store run_id differs from evidence run_id".into());
                        }
                    }
                }
                let bytes = serde_json::to_vec(&objects)?;
                let (id, entry) = self.capture_artifact(
                    &bytes,
                    "objects.json",
                    "objects",
                    &Value::Null,
                    mode,
                    emit,
                )?;
                if let Some(id) = id {
                    artifacts.push(id);
                }
                inventory.push(entry);
                Some(objects)
            }
            Err(error) => {
                gaps.push(format!("object snapshot: {error:#}"));
                None
            }
        };
        let mut state_files = vec![
            PathBuf::from("sessions.json"),
            PathBuf::from("status.json"),
            PathBuf::from("result.json"),
        ];
        for directory in ["physical", "turns"] {
            match sorted_directory(&state.join(directory)) {
                Ok(paths) => {
                    for path in paths {
                        if directory == "physical" && path.is_dir() {
                            for name in ["session.json", "instructions.md", "context.md"] {
                                state_files.push(path.join(name).strip_prefix(state)?.to_owned());
                            }
                        } else if directory == "turns"
                            && path.extension().is_some_and(|x| x == "md")
                        {
                            state_files.push(path.strip_prefix(state)?.to_owned());
                        }
                    }
                }
                Err(error) => gaps.push(format!("{directory}: {error:#}")),
            }
        }
        for relative in state_files {
            if let Some((id, entry)) = self.file(
                &state.join(&relative),
                &relative.to_string_lossy(),
                "state_input",
                &Value::Null,
                mode,
                &mut gaps,
                emit,
            )? {
                if let Some(id) = id {
                    artifacts.push(id);
                }
                inventory.push(entry);
            }
        }
        let (sessions, archive_root) = if let Some(path) = native_manifest {
            let manifest: Value = serde_json::from_slice(
                &fs::read(path).with_context(|| format!("read {}", path.display()))?,
            )?;
            ensure!(manifest["schema_version"] == 1, "unsupported native manifest schema_version");
            ensure!(
                manifest["run_id"].as_str() == Some(&self.run_id),
                "native manifest run_id mismatch"
            );
            let sessions = manifest["sessions"]
                .as_array()
                .context("native manifest sessions must be an array")?
                .clone();
            if let Some(items) = manifest["gaps"].as_array() {
                gaps.extend(items.iter().map(|v| {
                    format!("native archive: {}", v.as_str().unwrap_or("invalid gap entry"))
                }));
            }
            let bytes = serde_json::to_vec(&manifest)?;
            let (id, entry) = self.capture_artifact(
                &bytes,
                "native-manifest.json",
                "native_manifest",
                &Value::Null,
                mode,
                emit,
            )?;
            if let Some(id) = id {
                artifacts.push(id);
            }
            inventory.push(entry);
            (sessions, Some(path.parent().unwrap_or(Path::new(".")).canonicalize()?))
        } else {
            gaps.push(
                "native child-session inventory is unknown without an archive manifest".into(),
            );
            let sessions = match fs::read(state.join("sessions.json")) {
                Ok(bytes) => match serde_json::from_slice::<Vec<Value>>(&bytes) {
                    Ok(sessions) => sessions,
                    Err(error) => {
                        gaps.push(format!("sessions.json: {error}"));
                        Vec::new()
                    }
                },
                Err(_) => Vec::new(), // The state input reader already reported the error.
            };
            (sessions, None)
        };
        if let Some(objects) = &objects {
            check_sources(state, objects, &sessions, &mut gaps);
        }
        let native_ids: BTreeSet<&str> =
            sessions.iter().filter_map(|s| s["native_session_id"].as_str()).collect();
        for session in &sessions {
            if let Some(parent) = session["parent_native_session_id"].as_str()
                && !native_ids.contains(parent)
            {
                gaps.push(format!("native parent session {parent} is absent from the inventory"));
            }
        }
        let mut session_usage = BTreeMap::new();
        let mut native_artifacts = BTreeMap::new();
        for session in sessions {
            let native = match native_source(&session, archive_root.as_deref()) {
                Ok(path) => path,
                Err(error) => {
                    gaps.push(format!("native session source: {error:#}"));
                    continue;
                }
            };
            let mut bytes = match fs::read(&native) {
                Ok(bytes) => bytes,
                Err(error) => {
                    gaps.push(format!("{}: {error}", native.display()));
                    continue;
                }
            };
            // Live providers may be in the middle of a JSONL write. Only publish whole lines.
            if !final_capture && !bytes.ends_with(b"\n") {
                let length = bytes.iter().rposition(|b| *b == b'\n').map_or(0, |n| n + 1);
                bytes.truncate(length);
                gaps.push(format!("{}: live trailing line deferred", native.display()));
            }
            let mut metadata = session.clone();
            let provider = session["provider"].as_str().unwrap_or("unknown");
            // Bub tapes have no identity header. Correlate their exact derived
            // filename with the factory-persisted native identity, and keep the
            // weaker path-based evidence visible in parse_status.
            let bub_path_identity = (provider == "bub")
                .then(|| native.file_stem().and_then(|stem| stem.to_str()).map(str::to_owned))
                .flatten();
            let header = bub_path_identity.or_else(|| native_header(&bytes, provider));
            let expected = session["native_session_id"].as_str();
            match header {
                Some(id) if expected.is_none_or(|expected| expected == id) => {
                    metadata["native_session_id"] = json!(id);
                    metadata["parse_status"] =
                        json!(if provider == "bub" { "recognized-path" } else { "recognized" });
                }
                _ => {
                    metadata["parse_status"] = json!("unparsed");
                    gaps.push(format!(
                        "{}: missing, unsupported or mismatched {provider} session header",
                        native.display()
                    ));
                }
            }
            if archive_root.is_some() && expected.is_none() {
                gaps.push(format!("{}: manifest has no native_session_id", native.display()));
            }
            for (line, bytes) in bytes.split(|b| *b == b'\n').enumerate() {
                if !bytes.is_empty() && serde_json::from_slice::<Value>(bytes).is_err() {
                    gaps.push(format!(
                        "{}:{}: invalid native JSON entry",
                        native.display(),
                        line + 1
                    ));
                }
            }
            let source = format!(
                "native/{provider}/{}",
                metadata["native_session_id"]
                    .as_str()
                    .unwrap_or_else(|| native.to_str().unwrap_or("unparsed"))
            );
            session_usage.insert(source.clone(), native_usage(&bytes, provider));
            let (id, entry) =
                self.capture_artifact(&bytes, &source, "native_session", &metadata, mode, emit)?;
            inventory.push(entry);
            if native_artifacts.insert(source.clone(), id).is_some() {
                gaps.push(format!(
                    "multiple native versions for {source}; final inventory selects its last entry"
                ));
            }
        }
        let native_count = native_artifacts.len();
        let usage = combine_usage(session_usage.into_values().flatten());
        artifacts.extend(native_artifacts.into_values().flatten());
        artifacts.sort();
        artifacts.dedup();
        let database_lifecycle = objects
            .as_ref()
            .and_then(|v| v["tables"]["local_run"]["rows"].as_array())
            .and_then(|rows| rows.first())
            .and_then(|row| row["lifecycle"].as_str())
            .unwrap_or("unknown");
        let result = fs::read(state.join("result.json"))
            .ok()
            .and_then(|bytes| serde_json::from_slice::<Value>(&bytes).ok());
        let terminal =
            result.as_ref().and_then(|value| value["status"].as_str()).unwrap_or("unknown");
        if final_capture
            && !matches!(terminal, "quiescent" | "blocked" | "failed" | "completed" | "incomplete")
        {
            gaps.push(format!("run terminal state is {terminal}"));
        }
        gaps.extend(self.omissions.iter().cloned());
        gaps.sort();
        gaps.dedup();
        let status = if final_capture && gaps.is_empty() { "complete" } else { "partial" };
        let source_inventory = inventory_summary(inventory)?;
        let manifest = json!({
            "mode":mode.label(),"artifacts":artifacts,"inventory":source_inventory,
            "final":final_capture,"native_archive":native_manifest.is_some(),
            "coverage":{"status":status,"native_sessions":native_count,"objects":objects.is_some(),"run_terminal":terminal,"database_lifecycle":database_lifecycle},"gaps":gaps,
        });
        let event_kind =
            if mode == CaptureMode::Portable { "evidence_snapshot" } else { "evidence_summary" };
        let id = self.record(event_kind, manifest.clone(), emit)?;
        let mut summary_gaps = manifest["gaps"].as_array().cloned().unwrap_or_default();
        summary_gaps.extend(self.omissions.iter().map(|gap| json!(gap)));
        let mut coverage = manifest["coverage"].clone();
        if !self.omissions.is_empty() {
            coverage["status"] = json!("partial");
        }
        Ok(json!({"run_id":self.run_id,"snapshot_id":id,"mode":mode.label(),
                "coverage":coverage,"inventory":manifest["inventory"],
                "native_sessions":native_count,"usage":usage,"gaps":summary_gaps}))
    }
}

fn capture_time(record: &Value) -> u128 {
    record["captured_at_unix_nanos"].as_str().and_then(|s| s.parse().ok()).unwrap_or(0)
}

// Sum native Pi assistant usage and Bub model-step run events. ACP usage_update
// is a changing context snapshot and must never be added as token consumption.
fn native_usage(bytes: &[u8], provider: &str) -> Vec<Value> {
    if provider == "bub" {
        return bub_native_usage(bytes);
    }
    if provider != "pi" {
        return Vec::new();
    }
    let mut seen = BTreeSet::new();
    let mut messages = Vec::new();
    for line in bytes.split(|byte| *byte == b'\n') {
        let Ok(entry) = serde_json::from_slice::<Value>(line) else {
            continue;
        };
        if entry["message"]["role"] != "assistant" {
            continue;
        }
        let id = entry["id"].as_str().map_or_else(|| digest(line), str::to_owned);
        if !seen.insert(id) {
            continue;
        }
        messages.push(json!({"provider":provider,"model":entry["message"]["model"].as_str().unwrap_or("unknown"),"usage":entry["message"]["usage"]}));
    }
    messages
}

fn bub_native_usage(bytes: &[u8]) -> Vec<Value> {
    let mut seen = BTreeSet::new();
    let mut messages = Vec::new();
    for line in bytes.split(|byte| *byte == b'\n') {
        let Ok(entry) = serde_json::from_slice::<Value>(line) else { continue };
        if entry["kind"] != "event" || entry["payload"]["name"] != "run" {
            continue;
        }
        let data = &entry["payload"]["data"];
        let Some(usage) = data["usage"].as_object() else { continue };
        let id = entry["meta"]["run_id"].as_str().map_or_else(|| digest(line), str::to_owned);
        if !seen.insert(id) {
            continue;
        }
        let mut tokens = json!({});
        for (target, primary, alternate) in [
            ("input", "prompt_tokens", "input_tokens"),
            ("output", "completion_tokens", "output_tokens"),
        ] {
            if let Some(value) =
                usage.get(primary).or_else(|| usage.get(alternate)).and_then(Value::as_u64)
            {
                tokens[target] = json!(value);
            }
        }
        if let Some(value) = usage
            .get("completion_tokens_details")
            .and_then(|detail| detail.get("reasoning_tokens"))
            .and_then(Value::as_u64)
        {
            tokens["reasoning"] = json!(value);
        }
        messages.push(json!({"provider":"bub","model":data["model"].as_str().unwrap_or("unknown"),"usage":tokens}));
    }
    messages
}

fn combine_usage(messages: impl Iterator<Item = Value>) -> Vec<Value> {
    let mut totals: BTreeMap<(String, String), Value> = BTreeMap::new();
    for message in messages {
        let provider = message["provider"].as_str().unwrap_or("unknown");
        let model = message["model"].as_str().unwrap_or("unknown");
        let total = totals.entry((provider.to_owned(), model.to_owned())).or_insert_with(|| json!({"provider":provider,"model":model,"assistant_messages":0,"tokens":{},"known_messages":{}}));
        total["assistant_messages"] = json!(total["assistant_messages"].as_u64().unwrap_or(0) + 1);
        for field in ["input", "output", "cacheRead", "cacheWrite", "reasoning"] {
            if let Some(value) = message["usage"][field].as_u64() {
                total["tokens"][field] =
                    json!(total["tokens"][field].as_u64().unwrap_or(0).saturating_add(value));
                total["known_messages"][field] =
                    json!(total["known_messages"][field].as_u64().unwrap_or(0) + 1);
            }
        }
    }
    totals.into_values().collect()
}

fn check_sources(state: &Path, objects: &Value, sessions: &[Value], gaps: &mut Vec<String>) {
    if let Some(turns) = objects["tables"]["turns"]["rows"].as_array() {
        for turn in turns {
            if let Some(id) = turn["turn_id"].as_str()
                && !state.join("turns").join(format!("{id}.md")).is_file()
            {
                gaps.push(format!("turn {id}: persisted input is absent"));
            }
        }
    }
    let state_sessions = match fs::read(state.join("sessions.json")) {
        Ok(bytes) => match serde_json::from_slice::<Vec<Value>>(&bytes) {
            Ok(sessions) => sessions,
            Err(error) => {
                gaps.push(format!("sessions.json: {error}"));
                return;
            }
        },
        Err(_) => return,
    };
    for root in &state_sessions {
        let matched = sessions.iter().any(|candidate| {
            root["provider"] == candidate["provider"]
                && [
                    (root["native_session_id"].as_str(), candidate["native_session_id"].as_str()),
                    (root["session_id"].as_str(), candidate["provider_session_id"].as_str()),
                    (root["session_id"].as_str(), candidate["session_id"].as_str()),
                    (
                        root["native_session_path"].as_str(),
                        candidate["native_session_path"].as_str(),
                    ),
                ]
                .into_iter()
                .any(|(left, right)| left.is_some() && left == right)
        });
        if !matched {
            gaps.push(format!(
                "root provider session {} is absent from native inventory",
                root["session_id"]
            ));
        }
    }
    if let Some(providers) = objects["tables"]["provider_sessions"]["rows"].as_array() {
        for provider in providers {
            if !state_sessions
                .iter()
                .any(|session| session["session_id"] == provider["provider_session_id"])
            {
                gaps.push(format!(
                    "database provider session {} is absent from sessions.json",
                    provider["provider_session_id"]
                ));
            }
        }
    }
}

fn sorted_directory(path: &Path) -> Result<Vec<PathBuf>> {
    let mut paths = fs::read_dir(path)?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<std::io::Result<Vec<_>>>()?;
    paths.sort();
    Ok(paths)
}

fn native_source(session: &Value, archive_root: Option<&Path>) -> Result<PathBuf> {
    if let Some(root) = archive_root {
        let relative =
            Path::new(session["path"].as_str().context("native manifest session has no path")?);
        ensure!(!relative.is_absolute(), "native archive path must be relative");
        let path = root.join(relative).canonicalize()?;
        ensure!(path.starts_with(root), "native archive path escapes archive root");
        return Ok(path);
    }
    if let Some(path) = session["native_session_path"]
        .as_str()
        .or_else(|| (session["provider"] == "pi").then(|| session["session_id"].as_str()).flatten())
    {
        return Ok(PathBuf::from(path));
    }
    if session["provider"] == "codex" {
        let home = session["native_home"].as_str().context("Codex session has no native_home")?;
        let id = session["native_session_id"]
            .as_str()
            .or_else(|| session["session_id"].as_str())
            .context("Codex session has no native identity")?;
        let root = Path::new(home).join("sessions").canonicalize()?;
        let mut directories = vec![root.clone()];
        let mut matches = Vec::new();
        while let Some(directory) = directories.pop() {
            for path in sorted_directory(&directory)? {
                if path.is_symlink() {
                    continue;
                }
                if path.is_dir() {
                    directories.push(path);
                    continue;
                }
                if path.extension().is_none_or(|extension| extension != "jsonl") {
                    continue;
                }
                let mut first_line = Vec::new();
                std::io::BufReader::new(fs::File::open(&path)?)
                    .read_until(b'\n', &mut first_line)?;
                if native_header(&first_line, "codex").as_deref() == Some(id) {
                    matches.push(path);
                }
            }
        }
        ensure!(
            matches.len() == 1,
            "Codex native identity {id} matched {} files in {}",
            matches.len(),
            root.display()
        );
        return Ok(matches.remove(0));
    }
    bail!("session has no exact native_session_path")
}

fn native_header(bytes: &[u8], provider: &str) -> Option<String> {
    let header: Value = serde_json::from_slice(bytes.split(|b| *b == b'\n').next()?).ok()?;
    let id = match provider {
        "pi" if header["type"] == "session" => header["id"].as_str(),
        "codex" if header["type"] == "session_meta" => header["payload"]["id"].as_str(),
        _ => None,
    }?;
    Some(id.to_owned())
}

fn snapshot_cooperation(path: &Path) -> Result<Value> {
    let mut connection = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    let transaction = connection.transaction()?;
    let mut current = serde_json::Map::new();
    // Current relations and short labels only; never read native JSONL or long bodies here.
    for (name, query) in [
        ("objects", "SELECT w.node_id AS id,w.number,w.kind,w.state,w.observed_at,
            substr(l.title,1,160) AS title,a.assignment_id,a.member_login,
            a.lifecycle AS assignment_state FROM work_items w
            LEFT JOIN local_items l ON l.node_id=w.node_id
            LEFT JOIN assignments a ON a.work_item_node_id=w.node_id
              AND a.generation=(SELECT max(n.generation) FROM assignments n
                WHERE n.work_item_node_id=w.node_id)
            ORDER BY w.node_id LIMIT 5000"),
        ("sessions", "SELECT ps.session_id,ps.agent_id,ps.provider_kind,
            ai.profile_id,a.work_item_node_id,a.member_login,ps.lifecycle AS state,
            coalesce((SELECT max(coalesce(t.ended_at,t.started_at)) FROM turns t
              WHERE t.session_id=ps.session_id),ps.last_resumed_at,ps.started_at) AS last_activity_at
            FROM provider_sessions ps JOIN agent_instances ai ON ai.agent_id=ps.agent_id
            JOIN assignments a ON a.assignment_id=ai.assignment_id
            WHERE ai.lifecycle<>'retired' AND ps.lifecycle<>'replaced'
            ORDER BY ps.session_id LIMIT 5000"),
        ("turns", "SELECT turn_id,session_id,provider_turn_id,lifecycle AS state,
            trigger_kind,started_at AS at,ended_at,substr(error,1,256) AS error
            FROM turns ORDER BY turn_id DESC LIMIT 200"),
        ("events", "SELECT event_id,work_item_node_id,kind,detail,lifecycle,
            observed_at FROM events ORDER BY observed_at DESC,event_id DESC LIMIT 200"),
    ] {
        current.insert(name.into(), json!(snapshot_rows(&transaction, query)?));
    }
    transaction.commit()?;
    Ok(Value::Object(current))
}

fn snapshot_rows(transaction: &rusqlite::Transaction<'_>, query: &str) -> Result<Vec<Value>> {
    let mut statement = transaction.prepare(query)?;
    let columns: Vec<String> = statement.column_names().into_iter().map(str::to_owned).collect();
    let mut cursor = statement.query([])?;
    let mut rows = Vec::new();
    while let Some(row) = cursor.next()? {
        let mut fields = serde_json::Map::new();
        for (index, column) in columns.iter().enumerate() {
            let value = match row.get_ref(index)? {
                ValueRef::Null => Value::Null,
                ValueRef::Integer(value) => json!(value),
                ValueRef::Real(value) if value.is_finite() => json!(value),
                ValueRef::Real(value) => json!({"sqlite_real_bits":hex::encode(value.to_bits().to_be_bytes())}),
                ValueRef::Text(value) => match std::str::from_utf8(value) {
                    Ok(value) => json!(value),
                    Err(_) => json!({"sqlite_text_hex":hex::encode(value)}),
                },
                ValueRef::Blob(value) => json!({"sqlite_blob_hex":hex::encode(value)}),
            };
            fields.insert(column.clone(), value);
        }
        rows.push(Value::Object(fields));
    }
    Ok(rows)
}

fn snapshot_objects(path: &Path, gaps: &mut Vec<String>) -> Result<Value> {
    let mut connection = Connection::open_with_flags(path, OpenFlags::SQLITE_OPEN_READ_ONLY)?;
    let transaction = connection.transaction()?;
    let mut tables = serde_json::Map::new();
    for table in TABLES {
        let exists: bool = transaction.query_row(
            "SELECT EXISTS(SELECT 1 FROM sqlite_master WHERE type='table' AND name=?1)",
            [table],
            |row| row.get(0),
        )?;
        if !exists {
            gaps.push(format!("object snapshot: optional/legacy table {table} is absent"));
            continue;
        }
        let statement = transaction.prepare(&format!("SELECT * FROM \"{table}\""))?;
        let columns: Vec<String> =
            statement.column_names().into_iter().map(str::to_owned).collect();
        // SQLite orders the source rows deterministically. Cached JSON sort
        // keys otherwise duplicate every historical row in memory at capture.
        drop(statement);
        let ordering =
            (1..=columns.len()).map(|index| index.to_string()).collect::<Vec<_>>().join(",");
        let rows = snapshot_rows(&transaction, &format!("SELECT * FROM \"{table}\" ORDER BY {ordering}"))?;
        tables.insert((*table).to_owned(), json!({"columns":columns,"rows":rows}));
    }
    transaction.commit()?;
    Ok(json!({"schema_version":1,"tables":tables}))
}

fn protobuf_files(input: &Path) -> Result<Vec<PathBuf>> {
    if input.is_file() {
        return Ok(vec![input.to_owned()]);
    }
    let mut files = Vec::new();
    for path in sorted_directory(input)? {
        if path.is_symlink() {
            continue;
        }
        if path.is_dir() {
            files.extend(protobuf_files(&path)?);
        } else if path.extension().is_some_and(|x| x == "pb") {
            files.push(path);
        }
    }
    Ok(files)
}

/// Decode backend batch exports with official OTLP types. Filenames identify the signal;
/// protobuf messages alone cannot reliably distinguish the three wire schemas.
pub fn decode(input: &Path) -> Result<Value> {
    use opentelemetry_proto::tonic::collector::{
        metrics::v1::ExportMetricsServiceRequest, trace::v1::ExportTraceServiceRequest,
    };
    let mut batches = Vec::new();
    let mut errors = Vec::new();
    for path in protobuf_files(input)? {
        let name = path.file_name().context("batch has no filename")?.to_string_lossy();
        let result = (|| -> Result<(&str, Value)> {
            let bytes = fs::read(&path)?;
            if name.ends_with("-logs.pb") {
                Ok((
                    "logs",
                    serde_json::to_value(ExportLogsServiceRequest::decode(bytes.as_slice())?)?,
                ))
            } else if name.ends_with("-traces.pb") {
                Ok((
                    "traces",
                    serde_json::to_value(ExportTraceServiceRequest::decode(bytes.as_slice())?)?,
                ))
            } else if name.ends_with("-metrics.pb") {
                Ok((
                    "metrics",
                    serde_json::to_value(ExportMetricsServiceRequest::decode(bytes.as_slice())?)?,
                ))
            } else {
                bail!("batch filename must end in -logs.pb, -traces.pb or -metrics.pb")
            }
        })();
        match result {
            Ok((signal, data)) => batches.push(json!({"file":name,"signal":signal,"data":data})),
            Err(error) => errors.push(json!({"file":name,"error":format!("{error:#}")})),
        }
    }
    Ok(json!({"schema_version":1,"batches":batches,"errors":errors}))
}

/// Render diagnostic prose with GFM extensions; raw HTML is escaped, never executed.
pub fn render_markdown(texts: &[String]) -> Value {
    let mut options = comrak::Options::default();
    options.extension.table = true;
    options.extension.strikethrough = true;
    options.extension.tasklist = true;
    options.extension.autolink = true;
    options.render.escape = true;
    json!(texts.iter().map(|text| comrak::markdown_to_html(text, &options)).collect::<Vec<_>>())
}

fn decode_artifact(artifact: &Value, records: &BTreeMap<String, Value>) -> Result<Vec<u8>> {
    let mut bytes = Vec::new();
    for id in artifact["chunks"].as_array().context("artifact chunks must be an array")? {
        let id = id.as_str().context("chunk reference must be a string")?;
        let chunk = records.get(id).with_context(|| format!("missing chunk {id}"))?;
        ensure!(chunk["event_kind"] == "evidence_chunk", "reference {id} is not a chunk");
        let decoded = hex::decode(chunk["data_hex"].as_str().context("chunk has no data_hex")?)?;
        ensure!(decoded.len() <= CHUNK_BYTES, "chunk {id} exceeds {CHUNK_BYTES} bytes");
        ensure!(chunk["sha256"].as_str() == Some(&digest(&decoded)), "chunk {id} sha256 mismatch");
        bytes.extend(decoded);
    }
    ensure!(
        artifact["bytes"].as_u64() == Some(bytes.len() as u64),
        "artifact byte length mismatch"
    );
    ensure!(artifact["sha256"].as_str() == Some(&digest(&bytes)), "artifact sha256 mismatch");
    Ok(bytes)
}

/// Rebuild only into a new directory. Source paths are descriptions, never output paths.
#[allow(clippy::too_many_lines)] // Decode, verify and write in one ordered pass with one gap inventory.
pub fn reconstruct(input: &Path, output: &Path, run_id: Option<&str>) -> Result<Value> {
    ensure!(!output.exists(), "output already exists: {}", output.display());
    let mut decoded = Vec::new();
    let mut decode_gaps = Vec::new();
    for path in protobuf_files(input)? {
        if path.file_name().and_then(|name| name.to_str()).is_some_and(|name| name.ends_with("-traces.pb") || name.ends_with("-metrics.pb")) {
            continue;
        }
        match ExportLogsServiceRequest::decode(fs::read(&path)?.as_slice()) {
            Ok(request) => decoded.push(json!({"file": path.display().to_string(), "signal": "logs", "data": serde_json::to_value(request)?})),
            Err(error) => decode_gaps.push(format!("{}: protobuf decode: {error}", path.display())),
        }
    }
    reconstruct_from_decoded(&decoded, output, run_id, decode_gaps)
}

/// Reconstruct from decoded OTLP batches. The Python viewer uses this entry point
/// after retaining decoded batches across polling cutoffs, so protobuf decoding
/// is not repeated for every published projection.
pub fn reconstruct_from_decoded(
    decoded: &[Value],
    output: &Path,
    run_id: Option<&str>,
    mut gaps: Vec<String>,
) -> Result<Value> {
    ensure!(!output.exists(), "output already exists: {}", output.display());
    let mut runs: BTreeMap<String, BTreeMap<String, Value>> = BTreeMap::new();
    for batch in decoded {
        if batch["signal"] != "logs" {
            continue;
        }
        let request: ExportLogsServiceRequest = serde_json::from_value(batch["data"].clone())
            .with_context(|| format!("decoded OTLP batch {} is invalid", batch["file"]))?;
        for resource in request.resource_logs {
            for scope in resource.scope_logs {
                for record in scope.log_records {
                    let Some(any_value::Value::StringValue(body)) =
                        record.body.and_then(|body| body.value)
                    else {
                        continue;
                    };
                    if body.len() > RECORD_BYTES {
                        gaps.push("oversized evidence/log body".into());
                        continue;
                    }
                    let Ok(record) = serde_json::from_str::<Value>(&body) else { continue };
                    if !record["event_kind"]
                        .as_str()
                        .is_some_and(|kind| kind.starts_with("evidence_"))
                    {
                        continue;
                    }
                    let Some(run) = record["run_id"].as_str() else {
                        gaps.push("evidence record has no run_id".into());
                        continue;
                    };
                    let entries = runs.entry(run.to_owned()).or_default();
                    if record["schema_version"] != 1
                        || record["record_id"].as_str() != Some(&record_digest(&record)?)
                    {
                        gaps.push(format!("run {run}: invalid schema or record digest"));
                        continue;
                    }
                    let id = record["record_id"].as_str().context("record has no id")?.to_owned();
                    if entries
                        .get(&id)
                        .is_none_or(|prior| capture_time(prior) <= capture_time(&record))
                    {
                        entries.insert(id, record);
                    }
                }
            }
        }
    }
    let run = match run_id {
        Some(run) => run.to_owned(),
        None if runs.len() == 1 => runs.keys().next().context("no run")?.clone(),
        None if runs.is_empty() => bail!("no Braid evidence records found"),
        None => bail!(
            "multiple Braid runs found; select --run-id: {}",
            runs.keys().cloned().collect::<Vec<_>>().join(", ")
        ),
    };
    let records = runs.get(&run).with_context(|| format!("no evidence for run {run}"))?;
    let snapshot =
        records.values().filter(|v| v["event_kind"] == "evidence_snapshot").max_by_key(|v| {
            (
                capture_time(v),
                v["final"].as_bool().unwrap_or(false),
                v["native_archive"].as_bool().unwrap_or(false),
            )
        });
    let selected = if let Some(snapshot) = snapshot {
        if snapshot["final"] != true {
            gaps.push("final snapshot is missing".into());
        }
        if snapshot["coverage"]["status"] != "complete" {
            gaps.push("source coverage is partial".into());
        }
        if let Some(source_gaps) = snapshot["gaps"].as_array() {
            gaps.extend(
                source_gaps.iter().map(|v| v.as_str().unwrap_or("invalid source gap").to_owned()),
            );
        }
        snapshot["artifacts"].as_array().context("snapshot artifacts must be an array")?.clone()
    } else {
        gaps.push(
            "snapshot manifest is missing; recovered artifacts may include superseded versions"
                .into(),
        );
        records
            .values()
            .filter(|v| v["event_kind"] == "evidence_artifact")
            .map(|v| v["record_id"].clone())
            .collect()
    };
    fs::create_dir(output).with_context(|| format!("create new output {}", output.display()))?;
    let mut messages = fs::File::create(output.join("messages.jsonl"))?;
    let mut index = Vec::new();
    let mut object_written = false;
    for (number, id) in selected.iter().enumerate() {
        let Some(artifact) = id.as_str().and_then(|id| records.get(id)) else {
            gaps.push(format!("missing artifact {id}"));
            continue;
        };
        if artifact["event_kind"] != "evidence_artifact" {
            gaps.push(format!("invalid artifact reference {id}"));
            continue;
        }
        let bytes = match decode_artifact(artifact, records) {
            Ok(bytes) => bytes,
            Err(error) => {
                gaps.push(format!("artifact {id}: {error:#}"));
                continue;
            }
        };
        let filename = match artifact["logical_type"].as_str() {
            Some("objects") if !object_written => {
                object_written = true;
                "objects.json".to_owned()
            }
            Some("native_session") => format!("native-{number:06}.jsonl"),
            _ => format!("artifact-{number:06}.bin"),
        };
        fs::write(output.join(&filename), &bytes)?;
        if artifact["logical_type"] == "native_session" {
            for (sequence, line) in bytes.split(|b| *b == b'\n').enumerate() {
                if line.is_empty() {
                    continue;
                }
                let entry = match serde_json::from_slice::<Value>(line) {
                    Ok(entry) => entry,
                    Err(error) => {
                        gaps.push(format!("{filename}:{}: native JSON: {error}", sequence + 1));
                        json!({"unparsed_hex":hex::encode(line)})
                    }
                };
                serde_json::to_writer(
                    &mut messages,
                    &json!({"artifact":filename,"sequence":sequence,"session":artifact["metadata"],"entry":entry}),
                )?;
                messages.write_all(b"\n")?;
            }
        }
        if artifact["logical_type"] == "objects" {
            let objects: Value = serde_json::from_slice(&bytes)?;
            let mut timeline =
                fs::File::create(output.join(format!("timeline-{number:06}.jsonl")))?;
            if let Some(events) = objects["tables"]["events"]["rows"].as_array() {
                let mut ordered: Vec<_> = events.iter().collect();
                ordered.sort_by_key(|event| {
                    (event["observed_at"].as_str(), event["event_id"].as_str())
                });
                for event in ordered {
                    serde_json::to_writer(&mut timeline, event)?;
                    timeline.write_all(b"\n")?;
                }
            }
        }
        index.push(json!({"file":filename,"record_id":id,"source":artifact["source"],"logical_type":artifact["logical_type"],"metadata":artifact["metadata"],"sha256":artifact["sha256"],"bytes":artifact["bytes"]}));
    }
    gaps.sort();
    gaps.dedup();
    let summary = json!({"schema_version":1,"run_id":run,"snapshot_id":snapshot.map(|v| &v["record_id"]),"status":if gaps.is_empty(){"complete"}else{"partial"},"artifacts":index,"gaps":gaps});
    fs::write(output.join("manifest.json"), serde_json::to_vec_pretty(&summary)?)?;
    Ok(summary)
}
