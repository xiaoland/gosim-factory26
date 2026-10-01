//! Local composition of the existing projector, scheduler, Agent Groups and adapters.
use crate::{
    agent_session::{CliContext, CreatedSession, SessionError, SessionFactory},
    config::{
        BubConfig, CodexConfig, Config, PiConfig, Profile, ProviderConfig, RuntimeBinding,
    },
    group::{GroupKind, GroupSpec, agent_group_worker},
    objects::{LocalObjects, git},
    store::{StoreActor, TurnClaim},
};
use anyhow::{Context as _, Result, ensure};
use rusqlite::OptionalExtension;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap,
    fs,
    path::{Path, PathBuf},
    sync::Arc,
};
use tracing::Instrument as _;

#[derive(Clone, Deserialize)]
#[serde(deny_unknown_fields)]
struct Request {
    profiles: Vec<Profile>,
    root_profile_id: String,
    #[serde(default)]
    root_check_messages: Vec<String>,
    bindings: BTreeMap<String, RuntimeBinding>,
    codex: Option<CodexConfig>,
    pi: Option<PiConfig>,
    bub: Option<BubConfig>,
    prompt: String,
    state: PathBuf,
    #[serde(default)]
    run_id: String,
    #[serde(default = "default_ref")]
    delivery_ref: String,
}
fn default_ref() -> String {
    "refs/heads/braid-delivery".into()
}
pub(crate) fn write_json(path: &Path, value: &impl Serialize) -> Result<()> {
    let temporary = path.with_extension(format!("{}.tmp", uuid::Uuid::now_v7()));
    fs::write(&temporary, serde_json::to_vec_pretty(value)?)?;
    fs::rename(temporary, path)?;
    Ok(())
}
pub(crate) fn archive_turn_input(state: &Path, claim: &TurnClaim, input: &str) -> Result<()> {
    let directory = state.join("turns");
    fs::create_dir_all(&directory)?;
    fs::write(directory.join(format!("{}.md", claim.turn_id)), input)?;
    Ok(())
}

struct RecordingFactory {
    inner: Arc<dyn SessionFactory>,
    state: PathBuf,
    bindings: BTreeMap<String, RuntimeBinding>,
}

fn effective_profile_digest(profile: &Profile, binding: Option<&RuntimeBinding>) -> String {
    if let Some(digest) =
        binding.and_then(|binding| binding.capabilities.get("digest")).and_then(Value::as_str)
    {
        return digest.to_owned();
    }
    let material = serde_json::json!({"profile": profile, "binding": binding});
    hex::encode(Sha256::digest(serde_json::to_vec(&material).expect("profile digest serializes")))
}
#[async_trait::async_trait]
impl SessionFactory for RecordingFactory {
    async fn check(&self) -> std::result::Result<(), SessionError> {
        self.inner.check().await
    }
    async fn start(
        &self,
        profile: Profile,
        instructions: String,
        context: String,
        cli: CliContext,
    ) -> std::result::Result<CreatedSession, SessionError> {
        let mut telemetry = crate::telemetry::Operation::new(
            "braid.session.create",
            vec![
                opentelemetry::KeyValue::new("braid.profile.id", profile.id.clone()),
                opentelemetry::KeyValue::new("provider", profile.adapter_type.clone()),
            ],
        );
        let directory = self.state.join("physical").join(uuid::Uuid::now_v7().to_string());
        let record = (|| -> Result<Value> {
            fs::create_dir_all(&directory)?;
            fs::write(directory.join("instructions.md"), &instructions)?;
            fs::write(directory.join("context.md"), &context)?;
            let digest = effective_profile_digest(&profile, self.bindings.get(&profile.id));
            let mut meta = json!({"session_id":null,"provider":profile.adapter_type,"profile_id":profile.id,"effective_profile_digest":digest,"worktree":profile.workspace(),"native_home":null,"native_session_path":null,"native_session_id":null,"parent_native_session_id":null,"assignment_generation":null,"status":"starting","turns":[]});
            let objects = LocalObjects::new(self.state.clone());
            let c = objects.connect()?;
            let binding: Option<(String, String, i64, Option<String>, i64)> = c.query_row(
                "SELECT ai.agent_id,w.kind,w.number,w.context_revision,a.generation FROM worktrees wt JOIN agent_instances ai ON ai.agent_id=wt.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id JOIN work_items w ON w.node_id=a.work_item_node_id WHERE wt.path=?1",
                [profile.workspace().to_string_lossy().as_ref()],
                |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?, r.get(4)?)),
            ).optional()?;
            if let Some((group, kind, number, revision, generation)) = binding {
                meta["group_id"] = json!(group);
                meta["work_item_kind"] = json!(kind);
                meta["work_item_id"] = json!(number.to_string());
                meta["context_revision"] = json!(revision);
                meta["assignment_generation"] = json!(generation);
            }
            write_json(&directory.join("session.json"), &meta)?;
            Ok(meta)
        })();
        let mut meta = record.map_err(|e| SessionError::Failed(e.to_string()))?;
        let result = self.inner.start(profile.clone(), instructions, context, cli).await;
        let outcome = match &result {
            Ok(created) => {
                json!({"session_id":created.id,"provider":profile.adapter_type,"profile_id":profile.id,"worktree":profile.workspace(),"native_home":created.native_home,"native_session_path":created.native_session_path,"native_session_id":created.native_session_id,"parent_native_session_id":null,"status":"created"})
            }
            Err(SessionError::Materialization { session_id, reason }) => {
                json!({"session_id":session_id,"provider":profile.adapter_type,"profile_id":profile.id,"worktree":profile.workspace(),"native_home":null,"native_session_path":if profile.adapter_type=="pi" {session_id.clone()} else {None},"status":"unknown","error":reason,"turns":[]})
            }
            Err(error) => {
                json!({"session_id":null,"provider":profile.adapter_type,"profile_id":profile.id,"worktree":profile.workspace(),"native_home":null,"native_session_path":null,"status":"failed","error":error.to_string()})
            }
        };
        meta.as_object_mut()
            .expect("session metadata")
            .extend(outcome.as_object().expect("session outcome").clone());
        if let Err(error) = write_json(&directory.join("session.json"), &meta) {
            if let Ok(created) = &result {
                let _ = created.session.close().await;
            }
            return Err(SessionError::Failed(error.to_string()));
        }
        telemetry.finish(if result.is_ok() { "completed" } else { "failed" });
        result
    }
    async fn resume(
        &self,
        id: &str,
        profile: Profile,
        instructions: String,
        cli: CliContext,
    ) -> std::result::Result<CreatedSession, SessionError> {
        let mut telemetry = crate::telemetry::Operation::new(
            "braid.session.resume",
            vec![opentelemetry::KeyValue::new("braid.provider_session.id", id.to_owned())],
        );
        let result = self.inner.resume(id, profile, instructions, cli).await;
        telemetry.finish(if result.is_ok() { "completed" } else { "failed" });
        result
    }
    async fn teardown(&self, id: &str) -> std::result::Result<(), SessionError> {
        self.inner.teardown(id).await
    }
}
fn config(request: &Request) -> Result<Config> {
    ensure!(!request.profiles.is_empty(), "profiles must not be empty");
    let mut ids = std::collections::BTreeSet::new();
    let mut assignee_logins = std::collections::BTreeSet::new();
    for profile in &request.profiles {
        profile.validate()?;
        ensure!(ids.insert(profile.id.clone()), "duplicate profile id {}", profile.id);
        ensure!(
            assignee_logins.insert(profile.assignee_login.clone()),
            "duplicate assignee login {}",
            profile.assignee_login
        );
        let binding = request
            .bindings
            .get(&profile.id)
            .with_context(|| format!("missing runtime binding for profile {}", profile.id))?;
        ensure!(
            binding.adapter_type == profile.adapter_type,
            "binding adapter_type mismatch for profile {}",
            profile.id
        );
    }
    ensure!(
        request.bindings.len() == request.profiles.len(),
        "bindings must match profiles exactly"
    );
    let profile_ids: std::collections::BTreeSet<_> =
        request.profiles.iter().map(|p| p.id.as_str()).collect();
    ensure!(
        request.bindings.keys().all(|id| profile_ids.contains(id.as_str())),
        "binding references unknown profile"
    );
    ensure!(
        profile_ids.contains(request.root_profile_id.as_str()),
        "unknown root profile {}",
        request.root_profile_id
    );
    Ok(Config {
        repository: "local/run".into(),
        runtime: crate::config::RuntimeConfig {
            root: request.state.clone(),
            worktrees: request.state.join("worktrees"),
            offline_stopped_sessions: Vec::new(),
        },
        scheduler: crate::config::SchedulerConfig { quiet_seconds: 1, event_threshold: 8 },
        tools: crate::config::ToolConfig { git: "git".into() },
        profiles: request.profiles.clone(),
        bindings: request.bindings.clone(),
    })
}
pub(crate) fn sessions(objects: &LocalObjects) -> Result<Vec<Value>> {
    let c = objects.connect()?;
    let mut records = vec![];
    let physical = objects.state.join("physical");
    if !physical.exists() {
        return Ok(records);
    }
    for entry in fs::read_dir(physical)? {
        let directory = entry?.path();
        let path = directory.join("session.json");
        if !path.is_file() {
            continue;
        }
        let mut record: Value = serde_json::from_slice(&fs::read(path)?)?;
        if record["session_id"].is_null() && record["status"] != "unknown" {
            continue;
        }
        record["instructions_path"] = json!(directory.join("instructions.md"));
        record["context_path"] = json!(directory.join("context.md"));
        if let Some(id) = record["session_id"].as_str().map(str::to_owned) {
            let bound:Option<(String,String,i64,String,String,String)>=c.query_row("SELECT ai.agent_id,w.kind,w.number,ps.context_revision,ps.lifecycle,ps.session_id FROM provider_sessions ps JOIN agent_instances ai ON ai.agent_id=ps.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id JOIN work_items w ON w.node_id=a.work_item_node_id WHERE ps.provider_session_id=?1",[&id],|r|Ok((r.get(0)?,r.get(1)?,r.get(2)?,r.get(3)?,r.get(4)?,r.get(5)?))).optional()?;
            if let Some((group, kind, number, revision, lifecycle, session)) = bound {
                record["group_id"] = json!(group);
                record["work_item_kind"] = json!(kind);
                record["work_item_id"] = json!(number.to_string());
                record["context_revision"] = json!(revision);
                record["status"] = json!(lifecycle);
                let turns=c.prepare("SELECT turn_id,provider_turn_id,lifecycle,trigger_kind FROM turns WHERE session_id=?1 ORDER BY rowid")?.query_map([session],|r| {let turn:String=r.get(0)?;Ok(json!({"braid_turn_id":turn,"provider_turn_id":r.get::<_,Option<String>>(1)?,"status":r.get::<_,String>(2)?,"trigger_kind":r.get::<_,String>(3)?,"input_path":objects.state.join("turns").join(format!("{turn}.md"))}))})?.collect::<Result<Vec<_>,_>>()?;
                record["turns"] = json!(turns);
            }
        }
        records.push(record);
    }
    records.sort_by(|a, b| a["context_path"].as_str().cmp(&b["context_path"].as_str()));
    Ok(records)
}
pub fn status(objects: &LocalObjects) -> Result<Value> {
    let c = objects.connect()?;
    let count = |sql: &str| -> Result<i64> { Ok(c.query_row(sql, [], |r| r.get(0))?) };
    let items=c.prepare("SELECT w.kind,w.number,w.state,l.state_reason,l.head_ref,l.ready_commit,l.base_ref,l.draft FROM work_items w JOIN local_items l ON l.node_id=w.node_id ORDER BY w.kind,w.number")?.query_map([],|r|Ok(json!({"kind":r.get::<_,String>(0)?,"id":r.get::<_,i64>(1)?,"state":r.get::<_,String>(2)?,"reason":r.get::<_,Option<String>>(3)?,"head_ref":r.get::<_,Option<String>>(4)?,"ready_commit":r.get::<_,Option<String>>(5)?,"base_ref":r.get::<_,Option<String>>(6)?,"draft":r.get::<_,bool>(7)?})))?.collect::<Result<Vec<_>,_>>()?;
    Ok(
        json!({"items":items,"delivery_closed":crate::store::local_delivery_closed(&c)?,"queued_comment_deliveries":count("SELECT count(*) FROM local_comment_delivery WHERE status='queued'")?,"active_turns":count("SELECT count(*) FROM turns WHERE lifecycle IN ('starting','running')")?,"pending_batches":count("SELECT count(*) FROM wake_batches b WHERE lifecycle IN ('pending','runnable') AND EXISTS(SELECT 1 FROM assignments a WHERE a.work_item_node_id=b.work_item_node_id AND a.lifecycle IN ('active','materializing','finalizing'))")?,"pending_events":count("SELECT count(*) FROM events e WHERE lifecycle IN ('pending','resetting') AND (kind IN ('assign','lifecycle','invalidate') OR (kind='mention' AND detail='direct_contact'))")?,"pending_continuations":count("SELECT count(*) FROM wake_batches b JOIN wake_batch_events be ON be.batch_id=b.batch_id JOIN events e ON e.event_id=be.event_id JOIN context_resets cr ON e.dedupe_key='reset-continuation:' || cr.reset_id WHERE b.lifecycle IN ('pending','runnable') AND cr.lifecycle='applied' AND cr.continuation=1 AND e.lifecycle='pending'")?,"pending_resets":count("SELECT count(*) FROM context_resets WHERE lifecycle IN ('interrupting','materializing')")?,"materializing_groups":count("SELECT count(*) FROM assignments WHERE lifecycle='materializing'")?,"blocked_groups":count("SELECT count(*) FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE ai.lifecycle='blocked' AND a.generation=(SELECT max(generation) FROM assignments n WHERE n.work_item_node_id=a.work_item_node_id)")?,"unresolved_merges":count("SELECT count(*) FROM local_merges m JOIN work_items w ON w.node_id=m.pr_node_id WHERE m.lifecycle='prepared' OR (m.lifecycle='conflict' AND w.state='OPEN')")?,"physical_sessions":sessions(objects)?}),
    )
}
fn quiescent(status: &Value) -> bool {
    ["active_turns", "pending_batches", "pending_events", "pending_resets", "materializing_groups"]
        .iter()
        .all(|key| status[key] == 0)
}
fn delivery_complete(status: &Value) -> bool {
    status["delivery_closed"] == true
}
fn execution_settled(status: &Value) -> bool {
    ["active_turns", "pending_resets", "pending_continuations", "materializing_groups"]
        .iter().all(|key| status[key] == 0)
}
// Keep result persistence and telemetry teardown in the same error boundary.
#[allow(clippy::too_many_lines)]
async fn execute(request: Request, factory: Arc<dyn SessionFactory>) -> Result<()> {
    execute_mode(request, factory, false).await
}

async fn execute_mode(mut request: Request, factory: Arc<dyn SessionFactory>, offline_resume: bool) -> Result<()> {
    ensure!(!request.prompt.trim().is_empty(), "prompt is empty");
    ensure!(request.root_check_messages.iter().all(|message| !message.trim().is_empty()),
        "root_check_messages must not contain blank messages");
    ensure!(request.state.is_absolute(), "state must be absolute");
    let first_profile = request.profiles.first().context("profiles must not be empty")?;
    let workspace = fs::canonicalize(
        first_profile.workspace.as_ref().context("profile.workspace is required")?,
    )?;
    ensure!(!request.state.starts_with(&workspace), "state must be outside repository");
    for profile in &mut request.profiles {
        let profile_workspace =
            fs::canonicalize(profile.workspace.as_ref().context("profile.workspace is required")?)?;
        ensure!(profile_workspace == workspace, "all profiles must use the same source workspace");
        profile.workspace = Some(workspace.clone());
    }
    ensure!(request.delivery_ref.starts_with("refs/heads/"), "delivery_ref must be refs/heads/...");
    git(&workspace, &["check-ref-format", &request.delivery_ref])?;
    let seed_commit = git(&workspace, &["rev-parse", "HEAD"])?;
    let input_profiles = request.profiles.clone();
    let _ = config(&request)?;
    fs::create_dir_all(&request.state)?;
    let runtime_lock = fs::OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(request.state.join("runtime.lock"))?;
    fs2::FileExt::try_lock_exclusive(&runtime_lock)
        .context("another local runtime owns this state")?;
    let store = Arc::new(StoreActor::start(
        request.state.join("braid.sqlite3"),
        request.state.join("backups"),
    )?);
    store.apply()?;
    let objects = Arc::new(LocalObjects::new(request.state.clone()));
    let origin = request.state.canonicalize()?.join("origin.git");
    let request_path = request.state.join("request.json");
    let current_request = json!({"run_id":request.run_id,"repository":workspace,"seed_commit":seed_commit,"delivery_ref":request.delivery_ref,"prompt":request.prompt,"profiles":input_profiles,"root_profile_id":request.root_profile_id,"root_check_messages":request.root_check_messages,"bindings":request.bindings});
    let mut refresh_request = false;
    ensure!(!offline_resume || request_path.is_file(), "offline resume requires retained state");
    if !request_path.exists() {
        write_json(&request_path, &current_request)?;
    } else {
        let prior: Value = serde_json::from_slice(&fs::read(&request_path)?)?;
        ensure!(
            prior["run_id"] == request.run_id
                && prior["repository"] == json!(workspace)
                && prior["seed_commit"] == seed_commit
                && prior["prompt"] == request.prompt
                && prior["delivery_ref"] == request.delivery_ref,
            "resume request identity does not match retained run"
        );
        refresh_request = prior["root_check_messages"] != current_request["root_check_messages"];
        let same_material = prior["profiles"] == current_request["profiles"]
            && prior["bindings"] == current_request["bindings"];
        if !same_material && offline_resume {
            let old_profiles = prior["profiles"].as_array().context("retained profiles are invalid")?;
            let new_profiles = current_request["profiles"].as_array().context("resume profiles are invalid")?;
            let same_recipe = old_profiles.len() == new_profiles.len()
                && old_profiles.iter().zip(new_profiles).all(|(old, new)| {
                    let (mut old, mut new) = (old.clone(), new.clone());
                    old.as_object_mut().map(|value| value.remove("user_instructions"));
                    new.as_object_mut().map(|value| value.remove("user_instructions"));
                    old == new
                });
            let old_bindings = prior["bindings"].as_object().context("retained bindings are invalid")?;
            let new_bindings = current_request["bindings"].as_object().context("resume bindings are invalid")?;
            let same_adapters = old_bindings.len() == new_bindings.len()
                && old_bindings.iter().all(|(id, old)| new_bindings.get(id)
                    .is_some_and(|new| old["adapter_type"] == new["adapter_type"]));
            ensure!(same_recipe && same_adapters, "offline resume changes Profile identity or model recipe");
            refresh_request = true;
        } else {
            ensure!(same_material, "resume profile materials differ from the retained run");
        }
        ensure!(prior["root_profile_id"] == request.root_profile_id,
            "resume root Profile differs from the retained run");
    }
    if !origin.join("HEAD").exists() {
        git(&request.state, &["init", "--bare", origin.to_str().context("origin path is not UTF-8")?])?;
    }
    let initialized: Option<String> = objects.connect()?.query_row(
        "SELECT lifecycle FROM local_run", [], |r| r.get(0),
    ).optional()?;
    if initialized.is_none() {
        let published = git(&origin, &["rev-parse", "--verify", &request.delivery_ref]).ok();
        if let Some(published) = published {
            ensure!(published == seed_commit, "uninitialized origin delivery ref differs from input HEAD");
        } else {
            git(&origin, &["fetch", "--no-tags", workspace.to_str().context("input path is not UTF-8")?, &format!("HEAD:{}", request.delivery_ref)])?;
        }
        git(&origin, &["symbolic-ref", "HEAD", &request.delivery_ref])?;
        let root_profile = request.profiles.iter()
            .find(|profile| profile.id == request.root_profile_id)
            .context("root profile is not configured")?;
        let root_binding = request.bindings.get(&root_profile.id)
            .context("root profile has no runtime binding")?;
        let _ = GroupSpec::new_with_binding(
            GroupKind::Issue, root_profile.clone(), root_binding, &store,
        )?;
        objects.initialize(&origin, &request.run_id, &request.delivery_ref, &request.prompt, &request.root_profile_id)?;
    } else {
        ensure!(objects.repository()? == origin, "stored origin differs from retained run");
        git(&origin, &["rev-parse", "--verify", &request.delivery_ref])?;
        let lifecycle: String =
            objects.connect()?.query_row("SELECT lifecycle FROM local_run", [], |r| r.get(0))?;
        ensure!(lifecycle == "running", "run is already sealed");
    }
    if refresh_request {
        let history = request.state.join("request-history");
        fs::create_dir_all(&history)?;
        fs::copy(&request_path, history.join(format!("{}.json", uuid::Uuid::now_v7())))?;
        write_json(&request_path, &current_request)?;
    }
    let offline_stopped = if offline_resume {
        let stopped = store.prepare_offline_resume()?;
        let receipts = request.state.join("offline-resumes");
        fs::create_dir_all(&receipts)?;
        write_json(&receipts.join(format!("{}.json", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH)?.as_millis())),
            &json!({"host_assertion":"previous execution environment stopped", "provider_sessions":stopped}))?;
        stopped
    } else { Vec::new() };
    for profile in &mut request.profiles {
        profile.workspace = Some(origin.clone());
    }
    let telemetry = crate::telemetry::initialize(&request.state, &request.run_id).await;
    let evidence = telemetry.as_ref().map(|guard| {
        crate::telemetry::EvidenceWorker::start(
            request.state.clone(),
            request.run_id.clone(),
            guard.evidence_writer(),
        )
    });
    let root = tracing::info_span!("braid.run", braid.run.id = %request.run_id, result = tracing::field::Empty);
    let started = std::time::Instant::now();
    let outcome = drive(&request, Arc::clone(&store), Arc::clone(&objects), factory, offline_stopped)
        .instrument(root.clone())
        .await;
    let (mut status_name, mut reason) = match outcome {
        Ok(outcome) => outcome,
        Err(error) => ("failed".into(), format!("{error:#}")),
    };
    if let Err(error) = sessions(&objects)
        .and_then(|records| write_json(&request.state.join("sessions.json"), &records))
    {
        status_name = "failed".into();
        reason = format!("{reason}; could not persist sessions manifest: {error:#}");
    }
    let commit = match git(&origin, &["rev-parse", &request.delivery_ref]) {
        Ok(commit) => Some(commit),
        Err(error) => {
            if status_name == "quiescent" {
                status_name = "failed".into();
                reason = format!("cannot resolve delivery ref: {error:#}");
            } else {
                tracing::warn!(%error, "could not record delivery ref after local run failure");
            }
            None
        }
    };
    let root_state = objects.read("issue", 1);
    let retained_input = match status(&objects) {
        Ok(final_status) => json!({
            "queued_comment_deliveries":final_status["queued_comment_deliveries"],
            "scope_closed":final_status["delivery_closed"],
            "receipts_table":"local_comment_delivery",
            "comment_command":"comment view <comment_id> --thread",
            "note":"queued 仅表示已登记，未确认送达；范围关闭后保留的普通输入需重开工作范围才能继续派发"
        }),
        Err(error) => json!({"status_error":format!("{error:#}")}),
    };
    let result: Result<()> = write_json(
        &request.state.join("result.json"),
        &json!({"schema_version":1,"run_id":request.run_id,"status":status_name,"reason":reason,"root_issue":{"kind":"issue","id":"1","state":root_state.as_ref().ok().map(|item| &item.state),"state_error":root_state.as_ref().err().map(ToString::to_string)},"repository":origin,"delivery_ref":request.delivery_ref,"delivery_commit":commit,"objects_database":objects.database(),"retained_input":retained_input,"sessions_manifest":request.state.join("sessions.json")}),
    )
    .with_context(|| format!("local run {status_name}: {reason}; could not persist result.json"))
    .and_then(|()| {
        ensure!(status_name == "quiescent", "local run {status_name}: {reason}");
        Ok(())
    });
    let outcome =
        if result.is_err() && status_name == "quiescent" { "failed" } else { &status_name };
    root.record("result", outcome);
    if let Err(error) = &result {
        tracing::error!(parent: &root, %error, "local run ended with an error");
    }
    crate::telemetry::measurement(
        "braid.run",
        if outcome == "quiescent" { "ok" } else { outcome },
        started.elapsed().as_secs_f64(),
    );
    drop(root);
    if let Some(worker) = evidence {
        let _ = tokio::task::spawn_blocking(move || worker.stop()).await;
    }
    if let Some(guard) = telemetry {
        let _ = tokio::task::spawn_blocking(move || guard.shutdown()).await;
    }
    result
}
async fn drive(
    request: &Request,
    store: Arc<StoreActor>,
    objects: Arc<LocalObjects>,
    factory: Arc<dyn SessionFactory>,
    offline_stopped: Vec<String>,
) -> Result<(String, String)> {
    objects.recover_merges()?;
    store.advance_scheduler()?;
    let initial = status(&objects)?;
    write_json(&request.state.join("status.json"), &initial)?;
    if delivery_complete(&initial) && execution_settled(&initial) {
        return Ok(("quiescent".into(), "根 Issue 与全部工作项已完成".into()));
    }
    let mut config = config(request)?;
    config.runtime.offline_stopped_sessions = offline_stopped;
    let factory: Arc<dyn SessionFactory> = Arc::new(RecordingFactory {
        inner: factory,
        state: request.state.clone(),
        bindings: request.bindings.clone(),
    });
    let (shutdown, signal) = tokio::sync::watch::channel(false);
    let (reports, mut health) = tokio::sync::mpsc::channel(32);
    let (fatal_stops, mut fatal_stop_events) = tokio::sync::mpsc::channel(8);
    let mut workers = vec![];
    for kind in [GroupKind::Issue, GroupKind::Pr] {
        for profile in config.profiles.iter().cloned() {
            let binding = config
                .bindings
                .get(&profile.id)
                .with_context(|| format!("missing runtime binding for profile {}", profile.id))?;
            let spec = GroupSpec::new_with_binding(kind, profile, binding, &store)?;
            workers.push(tokio::spawn(
                agent_group_worker(
                    Arc::clone(&store),
                    Arc::clone(&objects),
                    config.clone(),
                    spec,
                    Arc::clone(&factory),
                    reports.clone(),
                    fatal_stops.clone(),
                    signal.clone(),
                )
                .in_current_span(),
            ));
        }
    }
    drop(reports);
    drop(fatal_stops);
    let mut errors = std::collections::BTreeMap::new();
    let result = async {
        loop {
            tokio::select! {
                _ = tokio::time::sleep(std::time::Duration::from_millis(250)) => {}
                Some(error) = fatal_stop_events.recv() => {
                    return Ok(("blocked".into(), format!("native teardown could not be proven: {error}")));
                }
            }
            store.advance_scheduler()?;
            while let Ok(report) = health.try_recv() {
                errors.insert(report.group, report.error);
            }
            write_json(&request.state.join("sessions.json"), &sessions(&objects)?)?;
            let current = status(&objects)?;
            write_json(&request.state.join("status.json"), &current)?;
            // Closed scope stops ordinary dispatch in the store. Wait for already
            // accepted execution and reset continuations to finish naturally.
            if delivery_complete(&current) && execution_settled(&current) {
                return Ok(("quiescent".into(), "根 Issue 与全部工作项已完成".into()));
            }
            if errors.len() == config.profiles.len() * 2
                && errors.values().any(Option::is_some)
                && current["active_turns"] == 0
                && current["pending_resets"] == 0
            {
                return Ok((
                    "blocked".into(),
                    format!("provider recovery returned an error: {errors:?}; retained state can resume"),
                ));
            }
            if errors.len() == config.profiles.len() * 2
                && current["blocked_groups"].as_i64().unwrap_or(0) > 0
                && current["active_turns"] == 0
                && current["pending_batches"] == 0
                && current["pending_resets"] == 0
                && current["materializing_groups"] == 0
            {
                return Ok((
                    "blocked".into(),
                    "必要 group 物化或恢复已 blocked，状态与输入已保留".into(),
                ));
            }
            if !quiescent(&current) {
                objects.root_idle_tick(&request.root_check_messages)?;
                continue;
            }
            match objects.root_idle_tick(&request.root_check_messages)? {
                crate::objects::RootIdle::Closed => return Ok(("blocked".into(), "根 Issue 已关闭，但工作范围尚未收敛（仍有开放工作项或未决合并）；状态与输入已保留".into())),
                crate::objects::RootIdle::Waiting => continue,
                crate::objects::RootIdle::Blocked(reason) => return Ok(("blocked".into(), reason)),
            }
        }
    }
    .await;
    let _ = shutdown.send(true);
    let mut cleanup_errors = Vec::new();
    for worker in workers {
        if let Some(error) = worker.await? {
            cleanup_errors.push(error);
        }
    }
    if !cleanup_errors.is_empty() && result.as_ref().is_ok_and(|(state, _)| state == "quiescent") {
        return Ok((
            "blocked".into(),
            format!("native teardown could not be proven during shutdown: {cleanup_errors:?}"),
        ));
    }
    result
}
pub async fn run(path: &Path, offline_resume: bool) -> Result<()> {
    let request: Request = serde_json::from_slice(&fs::read(path)?)?;
    let uses_codex = request.profiles.iter().any(|p| p.adapter_type == "codex");
    let uses_bub = request.profiles.iter().any(|p| p.adapter_type == "bub");
    let uses_pi = request.profiles.iter().any(|p| p.adapter_type == "pi");
    ensure!(uses_codex == request.codex.is_some(), "codex config must match codex profiles");
    ensure!(uses_bub == request.bub.is_some(), "bub config must match bub profiles");
    ensure!(uses_pi == request.pi.is_some(), "pi config must match pi profiles");
    let factory = crate::provider::session_factory(ProviderConfig {
        codex: request.codex.clone(),
        pi: request.pi.clone(),
        bub: request.bub.clone(),
        bindings: request.bindings.clone(),
    })?;
    if offline_resume {
        execute_mode(request, factory, true).await
    } else {
        execute(request, factory).await
    }
}
