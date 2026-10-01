//! Local Issue/PR authority. Object and event writes share one SQLite transaction.
use crate::{
    config::Profile,
    context::{
        self, Actor, CanonicalContext, CommentReaction, CommentSnapshot, IssueSnapshot,
        PullRequestSnapshot, WorkItemKind, WorkItemReference,
    },
    store::{self, EventKind, IngressEvent, SchedulerPolicy},
};
use anyhow::{Context as _, Result, bail, ensure};
use comrak::{Arena, Options, nodes::NodeValue, parse_document};
use rusqlite::{Connection, OptionalExtension, Transaction, TransactionBehavior, params};
use serde::{Deserialize, Serialize};
use std::{
    collections::{BTreeMap, BTreeSet},
    fmt,
    path::{Path, PathBuf},
    str::FromStr,
};

#[derive(Clone, Debug)]
pub struct RepositoryName(String);
impl FromStr for RepositoryName {
    type Err = anyhow::Error;
    fn from_str(s: &str) -> Result<Self> {
        ensure!(!s.is_empty(), "repository identity is empty");
        Ok(Self(s.into()))
    }

}
impl fmt::Display for RepositoryName {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}
pub struct WorkItemLocator {
    pub repository: RepositoryName,
    pub number: u64,
}
impl fmt::Display for WorkItemLocator {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}#{}", self.repository, self.number)
    }
}
#[derive(Clone)]
pub struct LocalObjects {
    pub state: PathBuf,
    pub policy: SchedulerPolicy,
    cli_binding_id: Option<String>,
}
#[derive(Debug, Clone)]
struct Writer {
    group: String,
    turn: String,
    node: String,
}
#[derive(Debug, Clone, Serialize)]
pub struct Item {
    pub id: i64,
    pub kind: String,
    pub title: String,
    pub body: String,
    pub state: String,
    pub reason: Option<String>,
    pub head_ref: Option<String>,
    pub base_ref: Option<String>,
    pub draft: bool,
    pub ready_commit: Option<String>,
    pub revision: i64,
    pub parent: Option<i64>,
    pub assignees: Vec<Actor>,
    pub execution: Option<ExecutionFact>,
    #[serde(skip_serializing)]
    pub desired_profile: Option<String>,
    #[serde(skip_serializing)]
    pub assignment_revision: i64,
}
#[derive(Debug, Clone, Serialize)]
pub struct ExecutionFact {
    pub outcome: String,
    pub at: String,
    pub summary: String,
    #[serde(skip_serializing)]
    pub error: Option<String>,
}
#[derive(Debug, Clone, Serialize)]
pub struct IssueCreateResult {
    pub id: i64,
    pub assignees: Vec<Actor>,
}
#[derive(Debug, Clone, Serialize)]
pub struct ItemEditResult {
    pub changed_fields: Vec<&'static str>,
    pub assignees: Vec<Actor>,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReadyResult {
    pub id: i64,
    pub changed: bool,
    pub head_commit: String,
    pub ready_commit: Option<String>,
    pub draft: bool,
}
#[derive(Debug, Clone, Serialize)]
pub struct MergeResult {
    pub id: i64,
    pub changed: bool,
    pub outcome: &'static str,
    pub merge_commit: String,
    pub base_ref: String,
    pub head_commit: String,
    pub target_commit: Option<String>,
    pub git_ref_updated: bool,
    pub closed_issues: Vec<i64>,
}
#[derive(Debug, Clone, Serialize)]
pub struct PrCreateResult {
    pub id: i64,
    pub created: bool,
    pub assignees: Vec<Actor>,
    pub head_ref: String,
    pub head_commit: String,
    pub base_ref: String,
    pub base_commit: String,
}
#[derive(Serialize)]
struct AssigneeCandidate {
    #[serde(skip_serializing)]
    profile: String,
    login: String,
    description: String,
}
#[derive(Deserialize)]
struct FrozenProfiles {
    profiles: Vec<Profile>,
}
#[derive(Serialize)]
pub struct CommentResolution {
    pub thread_root: i64,
    pub previous_resolved_through: Option<i64>,
    pub resolved_through: Option<i64>,
    pub affected_comments: i64,
    pub changed: bool,
}
pub enum RootIdle {
    Closed,
    Waiting,
    Blocked(String),
}
fn now() -> String {
    time::OffsetDateTime::now_utc()
        .format(&time::format_description::well_known::Rfc3339)
        .expect("time")
}
fn node(kind: &str, id: i64) -> String {
    format!("{kind}:{id}")
}
fn public_error(error: &str) -> String {
    let mut visible = String::with_capacity(error.len());
    let mut last = 0;
    for (start, _) in error.char_indices() {
        if start < last { continue }
        if let Some(candidate) = error.get(start..start + 36)
            && uuid::Uuid::parse_str(candidate).is_ok()
        {
            visible.push_str(&error[last..start]);
            visible.push_str("[id]");
            last = start + 36;
        }
    }
    visible.push_str(&error[last..]);
    visible
}
fn normalize_branch(name: &str) -> Result<String> {
    let branch = name.strip_prefix("refs/heads/").unwrap_or(name);
    ensure!(!branch.is_empty() && !branch.starts_with("refs/") && !branch.contains(".."), "expected a published branch, got {name:?}");
    let full = format!("refs/heads/{branch}");
    ensure!(git2::Reference::is_valid_name(&full), "invalid branch {name:?}");
    Ok(full)
}
fn mentioned_members(markdown: &str) -> BTreeSet<String> {
    let arena = Arena::new();
    let root = parse_document(&arena, markdown, &Options::default());
    let mut members = BTreeSet::new();
    for node in root.descendants() {
        if node.ancestors().skip(1).any(|parent| matches!(parent.data.borrow().value, NodeValue::Link(_) | NodeValue::Image(_))) {
            continue;
        }
        let data = node.data.borrow();
        let NodeValue::Text(value) = &data.value else { continue };
        let bytes = value.as_bytes();
        for (start, byte) in bytes.iter().enumerate() {
            if *byte != b'@' || (start > 0 && (bytes[start-1].is_ascii_alphanumeric() || matches!(bytes[start-1], b'_' | b'-' | b'.' | b'/'))) {
                continue;
            }
            let mut end = start + 1;
            while end < bytes.len() && (bytes[end].is_ascii_alphanumeric() || matches!(bytes[end], b'_' | b'-')) {
                end += 1;
            }
            if end > start + 1 {
                members.insert(value[start+1..end].to_ascii_lowercase());
            }
        }
    }
    members
}
fn kind_static(kind: &str) -> Result<&'static str> {
    match kind {
        "issue" => Ok("issue"),
        "pr" => Ok("pr"),
        _ => bail!("kind must be issue or pr"),
    }
}
impl LocalObjects {
    pub fn new(state: PathBuf) -> Self {
        Self { state, policy: SchedulerPolicy { quiet_seconds: 1, event_threshold: 8 }, cli_binding_id: None }
    }
    pub fn with_cli_binding(mut self, binding_id: String) -> Self {
        self.cli_binding_id = Some(binding_id);
        self
    }
    pub fn database(&self) -> PathBuf {
        self.state.join("braid.sqlite3")
    }
    pub fn connect(&self) -> Result<Connection> {
        let c = Connection::open(self.database())?;
        c.busy_timeout(std::time::Duration::from_secs(30))?;
        c.execute_batch("PRAGMA foreign_keys=ON;")?;
        Ok(c)
    }
    pub fn delivery_ref(&self) -> Result<String> {
        Ok(self.connect()?.query_row("SELECT delivery_ref FROM local_run", [], |r| r.get(0))?)
    }
    pub fn repository(&self) -> Result<PathBuf> {
        Ok(PathBuf::from(self.connect()?.query_row(
            "SELECT repository FROM local_run",
            [],
            |r| r.get::<_, String>(0),
        )?))
    }
    pub fn initialize(
        &self,
        repo: &Path,
        run_id: &str,
        delivery_ref: &str,
        prompt: &str,
        root_profile_id: &str,
    ) -> Result<()> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute(
            "INSERT INTO local_run(singleton,run_id,repository,delivery_ref) VALUES(1,?1,?2,?3)",
            params![run_id, repo.to_string_lossy(), delivery_ref],
        )?;
        let profile_id = root_profile_id.to_owned();
        let root_profile = self.current_profiles()?.into_iter()
            .find(|profile| profile.id == root_profile_id)
            .with_context(|| format!("当前 request 未配置根 Profile {root_profile_id}"))?;
        let member_login = Self::next_member_for_profile(&tx, &root_profile)?;
        self.create_item(&tx, "issue", "任务", prompt, None, None, None)?;
        tx.execute("UPDATE local_items SET desired_profile_id=?1,desired_member_login=?2 WHERE node_id='issue:1'", params![profile_id,member_login])?;
        Self::subscribe_in(&tx, "issue:1", &member_login, "assignment")?;
        Self::activity_in(&tx, "issue:1", None, "created", None, "root issue created")?;
        self.emit(&tx, "issue:1", EventKind::Assign, Some("activate"), "activate", None, None)?;
        self.emit(
            &tx,
            "issue:1",
            EventKind::Wake,
            None,
            "任务已建立。",
            None,
            None,
        )?;
        tx.commit()?;
        Ok(())
    }
    fn writer(&self, tx: &Transaction<'_>, turn: Option<&str>) -> Result<Option<Writer>> {
        ensure!(
            tx.query_row("SELECT lifecycle='running' FROM local_run", [], |r| r.get::<_, bool>(0))?,
            "run is sealed; control writes are disabled"
        );
        if turn.is_none() && self.cli_binding_id.is_none() { return Ok(None) }
        let writer=tx.query_row("SELECT ai.agent_id,a.work_item_node_id,t.turn_id FROM turns t JOIN provider_sessions ps ON ps.session_id=t.session_id JOIN agent_instances ai ON ai.agent_id=ps.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE ((?1 IS NOT NULL AND t.turn_id=?1) OR (?2 IS NOT NULL AND ps.cli_binding_id=?2)) AND t.lifecycle IN ('starting','running') AND ps.lifecycle='running' AND a.lifecycle IN ('active','finalizing') AND ai.lifecycle IN ('idle','running','finalizing') AND NOT EXISTS(SELECT 1 FROM context_resets cr WHERE cr.agent_id=ai.agent_id AND cr.lifecycle='materializing') AND (SELECT count(*) FROM turns current WHERE current.session_id=ps.session_id AND current.lifecycle IN ('starting','running'))=1", params![turn,self.cli_binding_id.as_deref()], |r|Ok(Writer {group:r.get(0)?,node:r.get(1)?,turn:r.get(2)?})).optional()?;
        Ok(Some(writer.context("当前调用已失效，本次修改未写入")?))
    }
    fn member_login(tx: &Transaction<'_>, writer: Option<&Writer>) -> Result<Option<String>> {
        writer.map(|writer| tx.query_row(
            "SELECT a.member_login FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id WHERE ai.agent_id=?1",
            [&writer.group], |r| r.get(0),
        )).transpose().map_err(Into::into)
    }
    fn subscribe_in(tx: &Transaction<'_>, target: &str, login: &str, source: &str) -> Result<()> {
        tx.execute("INSERT INTO local_subscriptions(work_item_node_id,member_login,active,source,changed_at) VALUES(?1,?2,1,?3,?4) ON CONFLICT(work_item_node_id,member_login) DO UPDATE SET active=1,source=excluded.source,changed_at=excluded.changed_at WHERE local_subscriptions.source!='explicit'",
            params![target,login,source,now()])?;
        Ok(())
    }
    fn activity_in(tx: &Transaction<'_>, target: &str, writer: Option<&Writer>, action: &str, comment: Option<i64>, detail: &str) -> Result<()> {
        let actor = Self::member_login(tx, writer)?.unwrap_or_else(|| "external".into());
        tx.execute("INSERT INTO local_activity(work_item_node_id,occurred_at,actor_login,action,source_comment,detail) VALUES(?1,?2,?3,?4,?5,?6)",
            params![target,now(),actor,action,comment,detail])?;
        Ok(())
    }
    fn notify_followers(&self, tx: &Transaction<'_>, source: &str, writer: Option<&Writer>, reference: &str) -> Result<()> {
        let author = Self::member_login(tx, writer)?;
        let owner: Option<String> = tx.query_row("SELECT desired_member_login FROM local_items WHERE node_id=?1", [source], |r| r.get(0))?;
        let followers: Vec<String> = tx.prepare("SELECT member_login FROM local_subscriptions WHERE work_item_node_id=?1 AND active=1 AND source='explicit'")?
            .query_map([source], |r| r.get(0))?.collect::<Result<_,_>>()?;
        for login in followers {
            if author.as_deref() == Some(&login) || owner.as_deref() == Some(&login) { continue; }
            self.notify_member(tx, source, &login, writer, reference)?;
        }
        Ok(())
    }
    fn notify_member(&self, tx: &Transaction<'_>, source: &str, login: &str, writer: Option<&Writer>, reference: &str) -> Result<()> {
        let destination: Option<(String,String,i64)> = tx.query_row("SELECT l.node_id,w.state,l.assignment_revision FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.desired_member_login=?1", [login], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional()?;
        let Some((target,state,revision)) = destination else { return Ok(()) };
        let kind = if state == "OPEN" { EventKind::Wake } else { EventKind::Mention };
        if let Some(event) = self.emit_with_id(tx, &target, kind, (state != "OPEN").then_some("direct_contact"), reference, writer, Some(source.into()))? {
            tx.execute("UPDATE events SET recipient_login=?2,recipient_revision=?3 WHERE event_id=?1", params![event,login,revision])?;
        }
        Ok(())
    }
    // Metadata updates address people, including sleeping owners, without
    // replacing their native history or echoing the actor's own operation.
    fn metadata_changed(&self, tx: &Transaction<'_>, sources: &[String], writer: Option<&Writer>, reference: &str) -> Result<()> {
        let actor = Self::member_login(tx, writer)?;
        let mut notified = BTreeSet::new();
        for source in sources {
            let recipients: Vec<String> = tx.prepare(
                "SELECT desired_member_login FROM local_items WHERE node_id=?1 AND desired_member_login IS NOT NULL
                 UNION SELECT member_login FROM local_subscriptions WHERE work_item_node_id=?1 AND active=1 AND source='explicit'"
            )?.query_map([source], |r| r.get(0))?.collect::<Result<_,_>>()?;
            for login in recipients {
                if actor.as_deref() != Some(&login) && notified.insert(login.clone()) {
                    self.notify_member(tx, source, &login, writer, reference)?;
                }
            }
        }
        Ok(())
    }
    pub fn set_subscription(&self, turn: Option<&str>, kind: &str, id: i64, active: bool) -> Result<()> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?.context("subscribe requires a current member")?;
        let target = node(kind_static(kind)?, id);
        Self::item(&tx, kind, id)?;
        let login = Self::member_login(&tx, Some(&writer))?.context("current member has no login")?;
        if !active {
            let assignee: Option<String> = tx.query_row("SELECT desired_member_login FROM local_items WHERE node_id=?1", [&target], |r| r.get(0))?;
            ensure!(assignee.as_deref() != Some(&login), "the current assignee cannot unsubscribe");
        }
        tx.execute("INSERT INTO local_subscriptions(work_item_node_id,member_login,active,source,changed_at) VALUES(?1,?2,?3,'explicit',?4) ON CONFLICT(work_item_node_id,member_login) DO UPDATE SET active=excluded.active,source='explicit',changed_at=excluded.changed_at",
            params![target,login,active,now()])?;
        tx.commit()?;
        Ok(())
    }
    pub fn subscriptions(&self, kind: &str, id: i64) -> Result<Vec<serde_json::Value>> {
        let c = self.connect()?;
        Self::item_for_read(&c, kind, id, false, false)?;
        Ok(c.prepare("SELECT s.member_login,s.active,s.source,EXISTS(SELECT 1 FROM local_items l WHERE l.desired_member_login=s.member_login AND NOT EXISTS(SELECT 1 FROM assignments a WHERE a.member_login=s.member_login AND a.lifecycle IN ('retired','blocked'))) FROM local_subscriptions s WHERE s.work_item_node_id=?1 ORDER BY s.member_login")?
            .query_map([node(kind,id)], |r| Ok(serde_json::json!({"login":r.get::<_,String>(0)?,"active":r.get::<_,bool>(1)?,"source":r.get::<_,String>(2)?,"reachable":r.get::<_,bool>(3)?})))?
            .collect::<rusqlite::Result<Vec<_>>>()?)
    }
    pub fn timeline(&self, kind: &str, id: i64, after: i64, limit: i64) -> Result<(Vec<serde_json::Value>, bool)> {
        ensure!(after >= 0, "timeline after must be nonnegative");
        ensure!((1..=100).contains(&limit), "timeline limit must be 1..100");
        let c = self.connect()?;
        Self::item(&c, kind, id)?;
        let mut rows = c.prepare("SELECT ordinal,occurred_at,actor_login,action,source_comment,detail FROM local_activity WHERE work_item_node_id=?1 AND ordinal>?2 ORDER BY ordinal LIMIT ?3")?
            .query_map(params![node(kind,id),after,limit + 1], |r| Ok(serde_json::json!({"ordinal":r.get::<_,i64>(0)?,"at":r.get::<_,String>(1)?,"author":r.get::<_,String>(2)?,"action":r.get::<_,String>(3)?,"comment":r.get::<_,Option<i64>>(4)?,"detail":r.get::<_,String>(5)?})))?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        let has_more = rows.len() > limit as usize;
        rows.truncate(limit as usize);
        Ok((rows, has_more))
    }
    pub fn root_idle_tick(&self, messages: &[String]) -> Result<RootIdle> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let (state, login, since): (String,Option<String>,Option<String>) = tx.query_row(
            "SELECT w.state,l.desired_member_login,r.root_idle_since FROM work_items w JOIN local_items l ON l.node_id=w.node_id CROSS JOIN local_run r WHERE w.node_id='issue:1'",
            [], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?)),
        )?;
        if state != "OPEN" {
            tx.execute("UPDATE local_run SET root_idle_since=NULL", [])?;
            tx.commit()?;
            return Ok(RootIdle::Closed);
        }
        let pending: bool = tx.query_row("SELECT EXISTS(
            SELECT 1 FROM events WHERE work_item_node_id='issue:1' AND lifecycle IN ('pending','resetting','materializing')
            UNION SELECT 1 FROM wake_batches WHERE work_item_node_id='issue:1' AND lifecycle IN ('pending','runnable')
            UNION SELECT 1 FROM assignments WHERE work_item_node_id='issue:1' AND lifecycle IN ('materializing','finalizing','stopping')
            UNION SELECT 1 FROM turns t JOIN provider_sessions ps ON ps.session_id=t.session_id JOIN agent_instances ai ON ai.agent_id=ps.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE a.work_item_node_id='issue:1' AND t.lifecycle IN ('starting','running')
            UNION SELECT 1 FROM context_resets cr JOIN agent_instances ai ON ai.agent_id=cr.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE a.work_item_node_id='issue:1' AND cr.lifecycle IN ('interrupting','materializing')
        )", [], |r| r.get(0))?;
        let executable: bool = tx.query_row("SELECT EXISTS(SELECT 1 FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id JOIN provider_sessions ps ON ps.agent_id=ai.agent_id WHERE a.work_item_node_id='issue:1' AND a.member_login=?1 AND a.lifecycle IN ('active','sleeping') AND ai.lifecycle IN ('idle','sleeping') AND ps.lifecycle IN ('idle','sleeping'))", [login.as_deref()], |r| r.get(0))?;
        if pending {
            tx.execute("UPDATE local_run SET root_idle_since=NULL", [])?;
            tx.commit()?;
            return Ok(RootIdle::Waiting);
        }
        if !executable {
            return Ok(RootIdle::Blocked(format!("root Issue #1 member {} has no resumable session", login.as_deref().unwrap_or("unassigned"))));
        }
        let current = time::OffsetDateTime::now_utc();
        match since {
            None => { tx.execute("UPDATE local_run SET root_idle_since=?1", [now()])?; }
            Some(since) => {
                let started = time::OffsetDateTime::parse(&since, &time::format_description::well_known::Rfc3339)?;
                if current - started >= time::Duration::minutes(5) {
                    let at = now();
                    // Count committed reminders, not ticks or visible comments: resume and
                    // hiding a comment must not restart the caller's message cycle.
                    let sent: i64 = tx.query_row(
                        "SELECT count(*) FROM local_activity WHERE work_item_node_id='issue:1' AND actor_login='Braid' AND action='commented' AND detail='root progress check'",
                        [], |r| r.get(0),
                    )?;
                    let body = if messages.is_empty() {
                        "请检查当前工作进展。"
                    } else {
                        messages[(sent % messages.len() as i64) as usize].as_str()
                    };
                    // Creation activity distinguishes these reminders from other Braid
                    // comments. Preserve replies' own state; ancestor visibility hides
                    // their bodies together with the superseded reminder.
                    let previous = tx.prepare("SELECT c.comment_id FROM local_comments c
                        WHERE c.work_item_node_id='issue:1' AND c.system_author='Braid' AND c.lifecycle='visible'
                        AND EXISTS(SELECT 1 FROM local_activity a WHERE a.work_item_node_id=c.work_item_node_id
                            AND a.source_comment=c.comment_id AND a.actor_login='Braid'
                            AND a.action='commented' AND a.detail='root progress check')
                        ORDER BY c.comment_id")?
                        .query_map([], |row| row.get::<_, i64>(0))?
                        .collect::<rusqlite::Result<Vec<_>>>()?;
                    for previous in previous {
                        let reason = "superseded by the next root progress check";
                        tx.execute("UPDATE local_comments SET lifecycle='hidden',hide_reason=?2,revision=revision+1,updated_at=?3 WHERE comment_id=?1", params![previous,reason,at])?;
                        // This housekeeping shares the new reminder's transaction and
                        // creates no additional discussion notification.
                        tx.execute("INSERT INTO local_activity(work_item_node_id,occurred_at,actor_login,action,source_comment,detail) VALUES('issue:1',?1,'Braid','hide',?2,?3)", params![at,previous,reason])?;
                    }
                    tx.execute("INSERT INTO local_comments(work_item_node_id,body,lifecycle,system_author,created_at,updated_at) VALUES('issue:1',?1,'visible','Braid',?2,?2)", params![body,at])?;
                    let comment = tx.last_insert_rowid();
                    tx.execute("UPDATE local_comments SET thread_root=comment_id WHERE comment_id=?1", [comment])?;
                    tx.execute("UPDATE local_run SET root_idle_since=NULL,root_check_comment=?1", [comment])?;
                    tx.execute("INSERT INTO local_activity(work_item_node_id,occurred_at,actor_login,action,source_comment,detail) VALUES('issue:1',?1,'Braid','commented',?2,'root progress check')", params![at,comment])?;
                    // The reminder is visible to everyone, but only asks the root owner to act.
                    let root_member = login.as_deref().context("root has no assigned member")?;
                    self.deliver_comment_to(&tx, comment, root_member, None, "created")?;
                }
            }
        }
        tx.commit()?;
        Ok(RootIdle::Waiting)
    }
    fn item(c: &Connection, kind: &str, id: i64) -> Result<Item> {
        Self::item_for_read(c, kind, id, true, true)
    }
    fn item_for_read(c: &Connection, kind: &str, id: i64, body: bool, execution: bool) -> Result<Item> {
        kind_static(kind)?;
        let mut item = c.query_row("SELECT w.number,w.kind,l.title,CASE WHEN ?2 THEN l.body ELSE '' END,w.state,l.state_reason,l.head_ref,l.ready_commit,l.revision,(SELECT number FROM work_items WHERE node_id=l.parent_issue),l.desired_profile_id,l.assignment_revision,l.desired_member_login,l.base_ref,l.draft FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.node_id=?1",params![node(kind,id),body],|r|{
            let login: Option<String> = r.get(12)?;
            Ok(Item{id:r.get(0)?,kind:r.get(1)?,title:r.get(2)?,body:r.get(3)?,state:r.get(4)?,reason:r.get(5)?,head_ref:r.get(6)?,ready_commit:r.get(7)?,revision:r.get(8)?,parent:r.get(9)?,desired_profile:r.get(10)?,assignment_revision:r.get(11)?,base_ref:r.get(13)?,draft:r.get(14)?,assignees:login.into_iter().map(|login| Actor { node_id: format!("member:{login}"), login }).collect(),execution:None})
        })?;
        if execution { item.execution = Self::execution_fact(c, &node(kind,id))?; }
        Ok(item)
    }
    fn execution_fact(c: &Connection, work_item: &str) -> Result<Option<ExecutionFact>> {
        let latest: Option<(String, String, Option<String>)> = c.query_row(
            "WITH current AS (SELECT assignment_id FROM assignments WHERE work_item_node_id=?1 ORDER BY generation DESC LIMIT 1),
             facts AS (
               SELECT t.lifecycle outcome,t.ended_at at,t.error error FROM turns t
               JOIN provider_sessions ps ON ps.session_id=t.session_id
               JOIN agent_instances ai ON ai.agent_id=ps.agent_id
               WHERE ai.assignment_id=(SELECT assignment_id FROM current) AND t.ended_at IS NOT NULL
               UNION ALL
               SELECT 'resumed',ps.last_resumed_at,NULL FROM provider_sessions ps
               JOIN agent_instances ai ON ai.agent_id=ps.agent_id
               WHERE ai.assignment_id=(SELECT assignment_id FROM current) AND ps.last_resumed_at IS NOT NULL
               UNION ALL
               SELECT 'resumed',ps.started_at,NULL FROM provider_sessions ps
               JOIN agent_instances ai ON ai.agent_id=ps.agent_id
               WHERE ai.assignment_id=(SELECT assignment_id FROM current) AND ps.lifecycle IN ('idle','running','sleeping')
               UNION ALL
               SELECT 'recovery_unavailable',ps.last_resume_failed_at,ps.last_resume_error FROM provider_sessions ps
               JOIN agent_instances ai ON ai.agent_id=ps.agent_id
               WHERE ai.assignment_id=(SELECT assignment_id FROM current) AND ps.last_resume_error IS NOT NULL AND ps.last_resume_failed_at IS NOT NULL
               UNION ALL
               SELECT 'recovery_unavailable',a.retired_at,ai.context_error FROM assignments a
               JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
               WHERE a.assignment_id=(SELECT assignment_id FROM current) AND a.lifecycle='blocked' AND a.retired_at IS NOT NULL AND ai.context_error IS NOT NULL
               UNION ALL
               SELECT 'recovery_unavailable',cr.updated_at,cr.error FROM context_resets cr
               JOIN agent_instances ai ON ai.agent_id=cr.agent_id
               WHERE ai.assignment_id=(SELECT assignment_id FROM current) AND cr.lifecycle='blocked' AND cr.error IS NOT NULL
             ) SELECT outcome,at,error FROM facts WHERE at IS NOT NULL ORDER BY at DESC LIMIT 1",
            [work_item], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?)),
        ).optional()?;
        let Some((outcome, at, error)) = latest else { return Ok(None) };
        if !matches!(outcome.as_str(), "failed" | "unknown" | "recovery_unavailable") { return Ok(None) }
        let error = error.map(|value| public_error(&value));
        let summary = error.as_deref().unwrap_or(match outcome.as_str() {
            "failed" => "执行失败，提供方未返回具体错误",
            "unknown" => "执行结果未知，未收到可靠终态",
            _ => "恢复暂不可用",
        }).split_whitespace().collect::<Vec<_>>().join(" ").chars().take(200).collect();
        Ok(Some(ExecutionFact { outcome, at, summary, error }))
    }
    pub fn read(&self, kind: &str, id: i64) -> Result<Item> {
        Self::item(&self.connect()?, kind, id)
    }
    pub fn read_for_cli(&self, kind: &str, id: i64, body: bool, execution: bool) -> Result<Item> {
        Self::item_for_read(&self.connect()?, kind, id, body, execution)
    }
    pub fn list(&self, kind: &str) -> Result<Vec<Item>> {
        kind_static(kind)?;
        let c = self.connect()?;
        c.prepare("SELECT number FROM work_items WHERE kind=?1 ORDER BY number")?
            .query_map([kind], |row| row.get(0))?
            .map(|id| Self::item(&c, kind, id?))
            .collect::<Result<Vec<_>>>()
    }
    pub fn list_for_cli(&self, kind: &str, state: &str, limit: usize, assignee: Option<&str>, base: Option<&str>, head: Option<&str>, body: bool, execution: bool) -> Result<(Vec<Item>, bool)> {
        kind_static(kind)?;
        ensure!(limit > 0, "list limit must be at least 1");
        let limit = i64::try_from(limit).context("list limit is too large")?;
        if let Some(assignee) = assignee {
            ensure!(!assignee.eq_ignore_ascii_case("@me") && !assignee.contains(','), "按当前具体成员名筛选；不支持 @me 或多个负责人");
        }
        let assignee = assignee.map(Self::normalize_login).transpose()?;
        let base = base.map(normalize_branch).transpose()?;
        let head = head.map(normalize_branch).transpose()?;
        let c = self.connect()?;
        let mut ids: Vec<i64> = c.prepare("SELECT w.number FROM work_items w JOIN local_items l ON l.node_id=w.node_id
            WHERE w.kind=?1 AND (?2='all' OR w.state=upper(?2) OR (?1='pr' AND ?2='closed' AND w.state='MERGED'))
              AND (?3 IS NULL OR l.desired_member_login=?3)
              AND (?4 IS NULL OR l.base_ref=?4) AND (?5 IS NULL OR l.head_ref=?5)
            ORDER BY w.number DESC LIMIT ?6")?
            .query_map(params![kind,state,assignee,base,head,limit.checked_add(1).context("list limit is too large")?], |row| row.get(0))?
            .collect::<rusqlite::Result<_>>()?;
        let has_more = ids.len() > limit as usize;
        ids.truncate(limit as usize);
        let items = ids.into_iter().map(|id| Self::item_for_read(&c, kind, id, body, execution)).collect::<Result<_>>()?;
        Ok((items, has_more))
    }

    pub fn profiles(&self) -> Result<Vec<serde_json::Value>> {
        let c = self.connect()?;
        Ok(c.prepare("SELECT profile_id,revision,effective_digest,provider_kind,tags FROM profiles p WHERE revision=(SELECT max(revision) FROM profiles n WHERE n.profile_id=p.profile_id) ORDER BY profile_id")?
            .query_map([], |r| Ok(serde_json::json!({"source":"profile-history","id":r.get::<_,String>(0)?,"revision":r.get::<_,i64>(1)?,"effective_profile_digest":r.get::<_,String>(2)?,"adapter_type":r.get::<_,String>(3)?,"tags":serde_json::from_str::<serde_json::Value>(&r.get::<_,String>(4)?).unwrap_or_else(|_| serde_json::json!([]))})))?
            .collect::<rusqlite::Result<Vec<_>>>()?)
    }

    pub fn assignee_directory(&self) -> Result<Vec<serde_json::Value>> {
        let mut c = self.connect()?;
        let tx = c.transaction()?;
        self.assignee_candidates(&tx)?.into_iter()
            .map(|candidate| serde_json::to_value(candidate).map_err(Into::into))
            .collect()
    }
    fn current_profiles(&self) -> Result<Vec<Profile>> {
        let path = self.state.join("request.json");
        let bytes = std::fs::read(&path).with_context(|| format!("无法读取当前成员配置 {}", path.display()))?;
        let frozen: FrozenProfiles = serde_json::from_slice(&bytes)
            .with_context(|| format!("当前成员配置无效 {}", path.display()))?;
        ensure!(!frozen.profiles.is_empty(), "当前 request 的 profiles 不能为空");
        let mut ids = BTreeSet::new();
        let mut logins = BTreeSet::new();
        for profile in &frozen.profiles {
            profile.validate().with_context(|| format!("当前 Profile {} 无效", profile.id))?;
            ensure!(!profile.id.is_empty() && ids.insert(profile.id.as_str()), "当前 request 的 Profile ID 为空或重复：{}", profile.id);
            ensure!(logins.insert(profile.assignee_login.as_str()), "当前 request 的成员前缀重复：{}", profile.assignee_login);
        }
        Ok(frozen.profiles)
    }
    fn assignee_candidates(&self, c: &Connection) -> Result<Vec<AssigneeCandidate>> {
        let mut profiles = self.current_profiles()?;
        profiles.sort_by(|a, b| a.assignee_login.cmp(&b.assignee_login));
        profiles.into_iter().filter(|profile| !profile.has_tag("root-only")).map(|profile| {
            let login = Self::next_member_for_profile(c, &profile)?;
            Ok(AssigneeCandidate { profile: profile.id, login, description: profile.assignee_description })
        }).collect()
    }

    pub fn profile(&self, id: &str) -> Result<serde_json::Value> {
        self.profiles()?
            .into_iter()
            .find(|profile| profile["id"] == id)
            .ok_or_else(|| anyhow::anyhow!("unknown profile {id}"))
    }

    pub fn set_assignee(&self, turn: Option<&str>, kind: &str, id: i64, login: &str) -> Result<()> {
        kind_static(kind)?;
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let item = Self::item(&tx, kind, id)?;
        ensure!(writer.as_ref().is_none_or(|w| w.node == node(kind, id)),
            "only this work item group can change its assignee");
        let login = Self::normalize_login(login)?;
        if item.assignees.first().is_none_or(|actor| actor.login != login) {
            let (profile, login) = self.profile_for_login(&tx, &login)?;
            self.replace_assignee_in(&tx, kind, id, &profile, &login, &item, writer.as_ref(), true)?;
        }
        tx.commit()?;
        Ok(())
    }
    fn normalize_login(login: &str) -> Result<String> {
        let login = login.strip_prefix('@').unwrap_or(login);
        ensure!(!login.is_empty() && !login.starts_with('@'), "invalid assignee login {login:?}");
        Ok(login.to_ascii_lowercase())
    }
    fn profile_for_login(&self, tx: &Transaction<'_>, login: &str) -> Result<(String, String)> {
        let login = Self::normalize_login(login)?;
        let candidates = self.assignee_candidates(tx)?;
        let mut matching = candidates.iter().filter(|candidate| candidate.login == login);
        let Some(candidate) = matching.next() else {
            let options = candidates.iter().map(|candidate| candidate.login.as_str()).collect::<Vec<_>>();
            bail!("成员 {login} 不可指派（未知、已占用或目录已更新）；请从 braid assignee list 选择当前具体成员：{}", options.join("、"));
        };
        ensure!(matching.next().is_none(), "成员 {login} 对应多个配置");
        Ok((candidate.profile.clone(), candidate.login.clone()))
    }
    fn next_member_for_profile(c: &Connection, profile: &Profile) -> Result<String> {
        let prefix = format!("{}-", profile.assignee_login);
        // 订阅历史保留在会话物化前已取消的成员名；查询候选不认领名字。
        let history = c.prepare("SELECT desired_member_login FROM local_items WHERE desired_member_login IS NOT NULL UNION SELECT member_login FROM assignments WHERE member_login IS NOT NULL UNION SELECT member_login FROM local_subscriptions")?
            .query_map([], |r| r.get::<_, String>(0))?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        let mut sequence = 0_u64;
        for login in history {
            let Some(suffix) = login.strip_prefix(&prefix) else { continue };
            if suffix.is_empty() || !suffix.bytes().all(|byte| byte.is_ascii_digit()) { continue }
            let value: u64 = suffix.parse().context("成员名称序号超出支持范围")?;
            sequence = sequence.max(value);
        }
        let next = sequence.checked_add(1).context("成员名称序号已耗尽")?;
        Ok(format!("{prefix}{next}"))
    }
    fn retire_direct_messages(tx: &Transaction<'_>, login: Option<&str>, replacement: Option<&str>) -> Result<()> {
        let Some(login) = login else { return Ok(()) };
        tx.execute("UPDATE events SET lifecycle='superseded' WHERE lifecycle='pending' AND recipient_login=?1", [login])?;
        tx.execute("UPDATE local_comment_delivery SET status='unreachable',reason=?2 WHERE recipient_login=?1 AND status='queued' AND event_id IN (SELECT event_id FROM events WHERE lifecycle='superseded')",
            params![login,format!("@{login} was reassigned; current assignee: {}",replacement.map_or("unassigned".into(), |name| format!("@{name}")))])?;
        tx.execute("UPDATE wake_batches SET lifecycle='consumed' WHERE lifecycle IN ('pending','runnable') AND NOT EXISTS(SELECT 1 FROM wake_batch_events be JOIN events e ON e.event_id=be.event_id WHERE be.batch_id=wake_batches.batch_id AND e.lifecycle='pending')", [])?;
        Ok(())
    }
    fn replace_assignee_in(
        &self,
        tx: &Transaction<'_>,
        kind: &str,
        id: i64,
        profile: &str,
        login: &str,
        item: &Item,
        writer: Option<&Writer>,
        require_own_writer: bool,
    ) -> Result<()> {
        if require_own_writer {
            ensure!(
                writer.is_none_or(|w| w.node == node(kind, id)),
                "only this work item group can change its assignee"
            );
        }
        if item.assignees.first().is_some_and(|actor| actor.login == login) {
            return Ok(());
        }
        let member_login = login;
        Self::retire_direct_messages(tx, item.assignees.first().map(|actor| actor.login.as_str()), Some(member_login))?;
        tx.execute("UPDATE local_items SET desired_profile_id=?2,desired_member_login=?3,assignment_revision=assignment_revision+1,revision=revision+1 WHERE node_id=?1", params![node(kind,id), profile, member_login])?;
        Self::subscribe_in(tx, &node(kind,id), member_login, "assignment")?;
        Self::activity_in(tx, &node(kind,id), writer, "assigned", None, &format!("@{member_login}"))?;
        tx.execute("UPDATE assignments SET lifecycle='stopping' WHERE work_item_node_id=?1 AND lifecycle IN ('materializing','active','finalizing','sleeping')", [node(kind,id)])?;
        // An explicitly replaced blocked writer still needs the normal stop
        // fence; otherwise no stopping session exists to retire its assignment.
        tx.execute("UPDATE agent_instances SET lifecycle='stopping' WHERE assignment_id IN (SELECT assignment_id FROM assignments WHERE work_item_node_id=?1 AND lifecycle='stopping') AND lifecycle!='retired'", [node(kind,id)])?;
        tx.execute("UPDATE provider_sessions SET lifecycle='stopping' WHERE agent_id IN (SELECT agent_id FROM agent_instances WHERE assignment_id IN (SELECT assignment_id FROM assignments WHERE work_item_node_id=?1 AND lifecycle='stopping')) AND lifecycle NOT IN ('retired','replaced')", [node(kind,id)])?;
        self.emit(
            tx,
            &node(kind, id),
            EventKind::Assign,
            None,
            &format!("{kind} #{id} assigned to @{member_login}"),
            writer,
            None,
        )?;
        // Assign materializes the replacement's idle session; a separate wake
        // carries the work to that session after the old writer is retired.
        self.emit(tx, &node(kind, id), EventKind::Wake, None, "负责人已变更。", None, None)?;
        self.notify_followers(tx, &node(kind,id), writer, &format!("{kind} #{id} assigned to @{member_login}"))?;
        Ok(())
    }
    fn create_item(
        &self,
        tx: &Transaction<'_>,
        kind: &str,
        title: &str,
        body: &str,
        head: Option<&str>,
        request_id: Option<&str>,
        desired_profile: Option<&str>,
    ) -> Result<i64> {
        kind_static(kind)?;
        ensure!(!title.trim().is_empty(), "title is empty");
        let desired_assignment = desired_profile
            .map(|login| self.profile_for_login(tx, login))
            .transpose()?;
        let id: i64 = tx.query_row(
            "SELECT coalesce(max(number),0)+1 FROM work_items WHERE repository_node_id='local'",
            [],
            |r| r.get::<_, i64>(0),
        )?;
        tx.execute("INSERT OR IGNORE INTO repositories(node_id,name_with_owner,observed_at) VALUES('local','local/run',?1)",[now()])?;
        tx.execute("INSERT INTO work_items(node_id,repository_node_id,kind,number,state,observed_at) VALUES(?1,'local',?2,?3,'OPEN',?4)",params![node(kind,id),kind,id,now()])?;
        tx.execute("INSERT INTO local_items(node_id,title,body,head_ref,request_id,desired_profile_id,desired_member_login) VALUES(?1,?2,?3,?4,?5,?6,?7)",params![node(kind,id),title,body,head,request_id,desired_assignment.as_ref().map(|(profile, _)| profile),desired_assignment.as_ref().map(|(_, member)| member)])?;
        Ok(id)
    }
    fn emit(
        &self,
        tx: &Transaction<'_>,
        target: &str,
        kind: EventKind,
        detail: Option<&'static str>,
        reference: &str,
        writer: Option<&Writer>,
        object: Option<String>,
    ) -> Result<()> {
        self.emit_with_id(tx, target, kind, detail, reference, writer, object).map(|_| ())
    }
    fn emit_with_id(
        &self,
        tx: &Transaction<'_>,
        target: &str,
        kind: EventKind,
        detail: Option<&'static str>,
        reference: &str,
        writer: Option<&Writer>,
        object: Option<String>,
    ) -> Result<Option<String>> {
        let (target_kind, id, state): (String, i64, String) = tx.query_row(
            "SELECT kind,number,state FROM work_items WHERE node_id=?1",
            [target],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )?;
        let kind = if writer.is_some_and(|w| w.node == target) && kind == EventKind::Wake {
            EventKind::OriginEcho
        } else {
            kind
        };
        let assignment_lifecycle: Option<String> = if kind == EventKind::Invalidate {
            tx.query_row(
                "SELECT a.lifecycle FROM assignments a JOIN local_items l ON l.node_id=a.work_item_node_id
                 WHERE a.work_item_node_id=?1 AND a.member_login=l.desired_member_login
                   AND a.assignment_revision=l.assignment_revision
                   AND a.lifecycle IN ('active','materializing','finalizing','sleeping')",
                [target], |r| r.get(0),
            ).optional()?
        } else { None };
        let kind = if kind == EventKind::Invalidate && assignment_lifecycle.is_none() { EventKind::Noop } else { kind };
        let event = IngressEvent {
            delivery_guid: uuid::Uuid::now_v7().to_string(),
            event_name: if target_kind == "issue" { "issues" } else { "pull_request" }.into(),
            action: detail.map(str::to_owned),
            repository_node_id: "local".into(),
            repository: "local/run".into(),
            work_item_node_id: Some(target.into()),
            work_item_kind: Some(kind_static(&target_kind)?),
            work_item_number: Some(id as u64),
            work_item_state: Some(state),
            object_node_id: Some(object.unwrap_or_else(|| target.into())),
            object_version: Some(uuid::Uuid::now_v7().to_string()),
            object_digest: None,
            visible_body: None,
            actor_node_id: writer.map(|w| w.group.clone()),
            actor_login: None,
            kind,
            detail,
            cross_surface_invalidation: false,
            origin: "local",
            reference: reference.into(),
            mention_candidate: false,
            reaction_target: None,
            known: true,
            raw_payload: vec![],
        };
        let result = store::ingest_event_transaction(tx, &event, self.policy)?;
        if let Some(id) = result.event_id.as_deref() {
            tx.execute(
                "UPDATE events SET writer_group=?2,writer_turn=?3 WHERE event_id=?1",
                params![id, writer.map(|w| &w.group), writer.map(|w| &w.turn)],
            )?;
            // A sleeping member records the description change, but only an
            // actual contact/reopen resumes work. Resume consumes this revision.
            if detail == Some("cross_surface") && kind == EventKind::Invalidate && assignment_lifecycle.as_deref() != Some("sleeping") {
                self.schedule(tx, target, &id)?;
            }
            if matches!(kind, EventKind::Assign | EventKind::Invalidate) {
                tx.execute("UPDATE events SET recipient_login=(SELECT desired_member_login FROM local_items WHERE node_id=?2),recipient_revision=(SELECT assignment_revision FROM local_items WHERE node_id=?2) WHERE event_id=?1", params![id,target])?;
            }
        }
        Ok(result.event_id)
    }
    fn schedule(&self, tx: &Transaction<'_>, target: &str, event: &str) -> Result<()> {
        store::schedule_event(tx, target, event, self.policy, false, &now())?;
        Ok(())
    }
    fn description_changed(
        &self,
        tx: &Transaction<'_>,
        target: &str,
        writer: Option<&Writer>,
        reference: &str,
    ) -> Result<()> {
        self.emit(tx, target, EventKind::Invalidate, None, reference, writer, None)?;
        let (target_kind,state): (String,String) = tx.query_row("SELECT kind,state FROM work_items WHERE node_id=?1", [target], |r| Ok((r.get(0)?,r.get(1)?)))?;
        // PR projections include only their OPEN associated Issues' descriptions.
        let related: Vec<String> = if target_kind == "issue" && state == "OPEN" {
            tx.prepare("SELECT pr_node_id FROM associations WHERE issue_node_id=?1 AND active=1")?
                .query_map([target], |r| r.get(0))?
                .collect::<Result<_, _>>()?
        } else {
            vec![]
        };
        for related in related {
            self.emit(tx, &related, EventKind::Invalidate, Some("cross_surface"), reference, writer, None)?;
        }
        Ok(())
    }
    pub fn create_issue(&self, turn: Option<&str>, title: &str, body: &str) -> Result<i64> {
        self.create_issue_with_parent(turn, title, body, None)
    }
    pub fn create_issue_with_parent(
        &self,
        turn: Option<&str>,
        title: &str,
        body: &str,
        parent: Option<i64>,
    ) -> Result<i64> {
        self.create_issue_with_parent_and_profile(turn, title, body, parent, None).map(|result| result.id)
    }
    pub fn create_issue_with_parent_and_profile(
        &self,
        turn: Option<&str>,
        title: &str,
        body: &str,
        parent: Option<i64>,
        profile: Option<&str>,
    ) -> Result<IssueCreateResult> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let id = self.create_item(&tx, "issue", title, body, None, None, profile)?;
        if let Some(login) = Self::item(&tx,"issue",id)?.assignees.first() {
            Self::subscribe_in(&tx, &node("issue",id), &login.login, "assignment")?;
        }
        Self::activity_in(&tx, &node("issue",id), writer.as_ref(), "created", None, title)?;
        if let Some(parent) = parent {
            Self::set_parent_in(&tx, id, Some(parent))?;
            Self::activity_in(&tx, &node("issue",id), writer.as_ref(), "parent_added", None, &format!("Issue #{parent}"))?;
            Self::activity_in(&tx, &node("issue",parent), writer.as_ref(), "child_added", None, &format!("Issue #{id}"))?;
        }
        if profile.is_some() {
            self.emit(
                &tx,
                &node("issue", id),
                EventKind::Assign,
                Some("activate"),
                &format!("Issue #{id} 已创建并指派。"),
                writer.as_ref(),
                None,
            )?;
        }
        self.emit(
            &tx,
            &node("issue", id),
            EventKind::Wake,
            None,
            "新 Issue 需求",
            writer.as_ref(),
            None,
        )?;
        let result = IssueCreateResult { id, assignees: Self::item_for_read(&tx, "issue", id, false, false)?.assignees };
        tx.commit().with_context(|| format!("issue #{id} 创建提交未能确认；先用 braid issue view {id} --json number,state 读取结果，不要为了取得编号重复创建"))?;
        Ok(result)
    }
    pub fn edit(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        title: Option<&str>,
        body: Option<&str>,
    ) -> Result<()> {
        self.edit_with_parent(turn, kind, id, title, body, None)
    }
    // A patch distinguishes unchanged, removed, and a new parent.
    #[allow(clippy::option_option)]
    pub fn edit_with_parent(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        title: Option<&str>,
        body: Option<&str>,
        parent: Option<Option<i64>>,
    ) -> Result<()> {
        self.edit_with_parent_and_assignees(turn, kind, id, title, body, parent, None, None).map(|_| ())
    }
    #[allow(clippy::option_option)]
    pub fn edit_with_parent_and_assignees(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        title: Option<&str>,
        body: Option<&str>,
        parent: Option<Option<i64>>,
        add_assignee: Option<&str>,
        remove_assignee: Option<&str>,
    ) -> Result<ItemEditResult> {
        ensure!(
            title.is_some()
                || body.is_some()
                || parent.is_some()
                || add_assignee.is_some()
                || remove_assignee.is_some(),
            "edit requires title, body, parent, or assignee change"
        );
        if let Some(title) = title {
            ensure!(!title.trim().is_empty(), "title is empty");
        }
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let item = Self::item(&tx, kind, id)?;
        let mut changed_fields = Vec::new();
        let current_login = item.assignees.first().map(|actor| actor.login.as_str());
        let remove_login = remove_assignee.map(Self::normalize_login).transpose()?;
        let add_login = add_assignee.map(Self::normalize_login).transpose()?;
        if let Some(ref remove_login) = remove_login {
            ensure!(
                current_login == Some(remove_login.as_str()),
                "cannot remove @{remove_login}; current assignee is {}",
                current_login.map_or("unassigned".into(), |login| format!("@{login}"))
            );
        }
        // 重复选择当前成员（包括 remove 后再 add 同名）不改变责任或物理会话。
        let same_assignee = add_login.as_deref().is_some_and(|login| Some(login) == current_login);
        let remove_login = if same_assignee { None } else { remove_login };
        let add = if same_assignee { None } else {
            add_login.as_deref().map(|login| self.profile_for_login(&tx, login)).transpose()?
        };
        if add.is_some() && remove_login.is_none() {
            ensure!(current_login.is_none(), "work item already has an active assignee; remove the current member when replacing it");
        }
        if let Some(parent) = parent {
            ensure!(kind == "issue", "only issues have a parent");
            if item.parent != parent {
                changed_fields.push("parent");
                Self::set_parent_in(&tx, id, parent)?;
                Self::activity_in(&tx, &node(kind,id), writer.as_ref(), "parent_changed", None, &format!("{:?} -> {:?}",item.parent,parent))?;
                for related in [item.parent,parent].into_iter().flatten().collect::<BTreeSet<_>>() {
                    Self::activity_in(&tx, &node("issue",related), writer.as_ref(), "child_changed", None, &format!("Issue #{id}"))?;
                }
                let mut affected = vec![node(kind,id)];
                affected.extend([item.parent,parent].into_iter().flatten().map(|parent| node("issue",parent)));
                self.metadata_changed(&tx, &affected, writer.as_ref(), &format!("Issue #{id} parent changed；详情入口：`braid issue view {id}`"))?;
            }
        }
        let title = title.unwrap_or(&item.title);
        let body = body.unwrap_or(&item.body);
        if item.title != title { changed_fields.push("title"); }
        if item.body != body { changed_fields.push("body"); }
        if item.title != title || item.body != body {
            tx.execute(
                "UPDATE local_items SET title=?2,body=?3,revision=revision+1 WHERE node_id=?1",
                params![node(kind, id), title, body],
            )?;
            let description_changed = context::filter_html_comments(&item.body) != context::filter_html_comments(body);
            if item.title != title || description_changed {
                Self::activity_in(&tx, &node(kind,id), writer.as_ref(), "edited", None, "title/body changed")?;
                if description_changed {
                    self.notify_followers(&tx, &node(kind,id), writer.as_ref(), &format!("{kind} #{id} description changed"))?;
                    self.description_changed(&tx, &node(kind,id), writer.as_ref(), &format!("{kind} #{id} description 已修改"))?;
                } else {
                    self.metadata_changed(&tx, &[node(kind,id)], writer.as_ref(), &format!("{kind} #{id} title 已修改；详情入口：`braid {kind} view {id}`"))?;
                }
            }
        }
        if let Some((profile, login)) = add {
            changed_fields.push("assignees");
            self.replace_assignee_in(
                &tx,
                kind,
                id,
                &profile,
                &login,
                &item,
                writer.as_ref(),
                false,
            )?;
        } else if remove_login.is_some() {
            changed_fields.push("assignees");
            Self::retire_direct_messages(&tx, current_login, None)?;
            tx.execute("UPDATE local_items SET desired_profile_id=NULL,desired_member_login=NULL,assignment_revision=assignment_revision+1,revision=revision+1 WHERE node_id=?1", [node(kind,id)])?;
            Self::activity_in(&tx, &node(kind,id), writer.as_ref(), "unassigned", None, "assignee removed")?;
            tx.execute("UPDATE assignments SET lifecycle='stopping' WHERE work_item_node_id=?1 AND lifecycle IN ('materializing','active','finalizing','sleeping')", [node(kind,id)])?;
            tx.execute("UPDATE agent_instances SET lifecycle='stopping' WHERE assignment_id IN (SELECT assignment_id FROM assignments WHERE work_item_node_id=?1 AND lifecycle='stopping') AND lifecycle NOT IN ('retired','blocked')", [node(kind,id)])?;
            tx.execute("UPDATE provider_sessions SET lifecycle='stopping' WHERE agent_id IN (SELECT agent_id FROM agent_instances WHERE assignment_id IN (SELECT assignment_id FROM assignments WHERE work_item_node_id=?1 AND lifecycle='stopping')) AND lifecycle NOT IN ('retired','blocked')", [node(kind,id)])?;
            self.emit(
                &tx,
                &node(kind, id),
                EventKind::Unassign,
                Some("unassign"),
                &format!("{kind} #{id} unassigned"),
                writer.as_ref(),
                None,
            )?;
        }
        let result = ItemEditResult { changed_fields, assignees: Self::item_for_read(&tx, kind, id, false, false)?.assignees };
        tx.commit().with_context(|| format!("{kind} #{id} 编辑提交未能确认；读取 braid {kind} view {id} 核对结果"))?;
        Ok(result)
    }
    fn set_parent_in(tx: &Transaction<'_>, id: i64, parent: Option<i64>) -> Result<()> {
        if let Some(parent) = parent {
            Self::item(tx, "issue", parent)?;
            let cycle: bool = tx.query_row(
                "WITH RECURSIVE ancestors(node_id) AS (SELECT ?1 UNION SELECT l.parent_issue FROM local_items l JOIN ancestors a ON a.node_id=l.node_id WHERE l.parent_issue IS NOT NULL) SELECT EXISTS(SELECT 1 FROM ancestors WHERE node_id=?2)",
                params![node("issue", parent), node("issue", id)], |r| r.get(0))?;
            ensure!(!cycle, "issue parent would create a cycle");
        }
        tx.execute(
            "UPDATE local_items SET parent_issue=?2 WHERE node_id=?1",
            params![node("issue", id), parent.map(|id| node("issue", id))],
        )?;
        Ok(())
    }
    pub fn comment(&self, turn: Option<&str>, kind: &str, id: i64, body: &str) -> Result<i64> {
        self.comment_reply(turn, kind, id, body, None)
    }
    pub fn comment_reply(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        body: &str,
        reply_to: Option<i64>,
    ) -> Result<i64> {
        ensure!(!body.trim().is_empty(), "comment body is empty");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let comment = self.comment_reply_in(&tx, writer.as_ref(), kind, id, body, reply_to)?;
        tx.commit().with_context(|| format!("comment #{comment} 在 {kind} #{id} 的创建提交未能确认；先用 braid comment view {comment} 读取结果，不要重复创建"))?;
        Ok(comment)
    }
    fn comment_reply_in(&self, tx: &Transaction<'_>, writer: Option<&Writer>, kind: &str, id: i64, body: &str, reply_to: Option<i64>) -> Result<i64> {
        ensure!(!body.trim().is_empty(), "comment body is empty");
        Self::item(&tx, kind, id)?;
        let root = reply_to
            .map(|parent| {
                let (target, root): (String, i64) = tx.query_row(
                    "SELECT work_item_node_id,thread_root FROM local_comments WHERE comment_id=?1",
                    [parent],
                    |r| Ok((r.get(0)?, r.get(1)?)),
                )?;
                ensure!(target == node(kind, id), "comment #{parent} belongs to {} #{}, not {kind} #{id}; read it with braid comment view {parent}", target.split_once(':').map_or("unknown", |(kind, _)| kind), target.split_once(':').map_or("unknown", |(_, id)| id));
                Ok::<_, anyhow::Error>(root)
            })
            .transpose()?;
        tx.execute("INSERT INTO local_comments(work_item_node_id,body,lifecycle,writer_group,writer_turn,created_at,updated_at,reply_to,thread_root) VALUES(?1,?2,'visible',?3,?4,?5,?5,?6,?7)",params![node(kind,id),body,writer.as_ref().map(|w|&w.group),writer.as_ref().map(|w|&w.turn),now(),reply_to,root])?;
        let comment = tx.last_insert_rowid();
        if root.is_none() {
            tx.execute(
                "UPDATE local_comments SET thread_root=comment_id WHERE comment_id=?1",
                [comment],
            )?;
        }
        Self::activity_in(&tx, &node(kind,id), writer, if reply_to.is_some() { "replied" } else { "commented" }, Some(comment), &format!("comment #{comment}"))?;
        let deliveries = self.discussion_changed(&tx, comment, writer, "created")?;
        self.direct_mentions(&tx, comment, body, &BTreeSet::new(), writer, &deliveries)?;
        Ok(comment)
    }
    pub fn last_comment_by_current_member(&self, turn: Option<&str>, kind: &str, id: i64) -> Result<i64> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?.context("last comment requires a current member")?;
        Self::item(&tx, kind, id)?;
        let login = Self::member_login(&tx, Some(&writer))?.context("current member has no login")?;
        let candidates = tx.prepare("SELECT c.comment_id FROM local_comments c
            JOIN agent_instances ai ON ai.agent_id=c.writer_group
            JOIN assignments a ON a.assignment_id=ai.assignment_id
            WHERE c.work_item_node_id=?1 AND a.member_login=?2 AND c.lifecycle='visible'
            ORDER BY c.comment_id DESC")?
            .query_map(params![node(kind,id),login], |row| row.get::<_, i64>(0))?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        for id in candidates {
            if Self::comment_hidden_by(&tx, id)?.is_none() { return Ok(id); }
        }
        bail!("当前成员在此工作项没有可编辑或删除的可见评论")
    }

    fn deliver_comment_to(&self, tx: &Transaction<'_>, comment: i64, login: &str, writer: Option<&Writer>, action: &str) -> Result<Option<String>> {
        if matches!(action, "created" | "edited" | "mentioned") && Self::comment_effectively_hidden(tx, comment)? {
            return Ok(None);
        }
        let source: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [comment], |r| r.get(0))?;
        let current: Option<(String,String,i64)> = tx.query_row("SELECT l.node_id,w.state,l.assignment_revision FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.desired_member_login=?1", [login], |r| Ok((r.get(0)?,r.get(1)?,r.get(2)?))).optional()?;
        let (status, reason, event_id) = if let Some((target,state,revision)) = current {
            let blocked: bool = tx.query_row("SELECT EXISTS(SELECT 1 FROM assignments WHERE member_login=?1 AND lifecycle IN ('blocked','retired'))", [login], |r| r.get(0))?;
            if blocked {
                ("unreachable", Some(format!("@{login} has no resumable session")), None)
            } else {
            let kind = if state == "OPEN" { EventKind::Wake } else { EventKind::Mention };
            let label = if source.starts_with("issue:") { "Issue" } else { "PR" };
            let number = source.split(':').nth(1).unwrap_or(&source);
            let author = Self::member_login(tx, writer)?.map(|login| format!("（@{login}）")).unwrap_or_default();
            let reference = format!("{label} #{number}：评论 #{comment} {action}{author}；正文入口：`braid comment view {comment}`");
            let event = self.emit_with_id(tx, &target, kind, (state != "OPEN").then_some("direct_contact"), &reference, writer, Some(format!("comment:{comment}")))?;
            if let Some(ref event) = event {
                tx.execute("UPDATE events SET recipient_login=?2,recipient_revision=?3 WHERE event_id=?1", params![event,login,revision])?;
            }
            if event.is_some() { ("queued", None, event) } else { ("unreachable", Some("message event was not queued".to_owned()), None) }
            }
        } else {
            let old: Option<Option<String>> = tx.query_row("SELECT l.desired_member_login FROM assignments a JOIN local_items l ON l.node_id=a.work_item_node_id WHERE a.member_login=?1", [login], |r| r.get(0)).optional()?;
            let reason = match old {
                Some(current) => format!("@{login} was reassigned; current assignee: {}", current.map_or("unassigned".into(), |name| format!("@{name}"))),
                None => format!("@{login} is not a concrete member in this run"),
            };
            ("unreachable", Some(reason), None)
        };
        tx.execute("INSERT INTO local_comment_delivery(comment_id,recipient_login,status,reason,event_id) VALUES(?1,?2,?3,?4,?5) ON CONFLICT(comment_id,recipient_login) DO UPDATE SET status=excluded.status,reason=excluded.reason,event_id=excluded.event_id", params![comment,login,status,reason,event_id])?;
        Ok(event_id)
    }
    fn direct_mentions(&self, tx: &Transaction<'_>, comment: i64, body: &str, previous: &BTreeSet<String>, writer: Option<&Writer>, deliveries: &BTreeSet<String>) -> Result<()> {
        let self_login = Self::member_login(tx, writer)?;
        for login in mentioned_members(body).difference(previous) {
            if self_login.as_deref() == Some(login) { continue; }
            if !deliveries.contains(login) { self.deliver_comment_to(tx, comment, login, writer, "mentioned")?; }
        }
        Ok(())
    }
    pub fn comment_deliveries(&self, comment: i64) -> Result<Vec<serde_json::Value>> {
        let c = self.connect()?;
        Ok(c.prepare("SELECT recipient_login,status,reason FROM local_comment_delivery WHERE comment_id=?1 ORDER BY recipient_login")?
            .query_map([comment], |r| Ok(serde_json::json!({"recipient":r.get::<_,String>(0)?,"status":r.get::<_,String>(1)?,"reason":r.get::<_,Option<String>>(2)?})))?
            .collect::<rusqlite::Result<Vec<_>>>()?)
    }

    // Participants are identified by durable logical agents, never replaceable provider sessions.
    fn discussion_changed(
        &self,
        tx: &Transaction<'_>,
        id: i64,
        writer: Option<&Writer>,
        action: &str,
    ) -> Result<BTreeSet<String>> {
        let (target, root): (String, i64) = tx.query_row(
            "SELECT work_item_node_id,thread_root FROM local_comments WHERE comment_id=?1",
            [id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
        let recipients: BTreeSet<String> = tx.prepare(
            "SELECT s.member_login FROM local_subscriptions s WHERE s.work_item_node_id=?1 AND s.active=1 AND s.source='explicit'
             UNION SELECT desired_member_login FROM local_items WHERE node_id=?1 AND desired_member_login IS NOT NULL
             UNION SELECT a.member_login FROM local_comments c JOIN agent_instances ai ON ai.agent_id=c.writer_group
               JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE c.work_item_node_id=?1 AND c.thread_root=?2 AND a.member_login IS NOT NULL AND NOT EXISTS(SELECT 1 FROM local_subscriptions s WHERE s.work_item_node_id=?1 AND s.member_login=a.member_login AND s.source='explicit' AND s.active=0)"
        )?.query_map(params![target,root], |r| r.get(0))?.collect::<Result<_,_>>()?;
        let mut deliveries = BTreeSet::new();
        let author = Self::member_login(tx, writer)?;
        for login in recipients {
            if author.as_deref() == Some(&login) { continue; }
            self.deliver_comment_to(tx, id, &login, writer, action)?;
            deliveries.insert(login);
        }
        Ok(deliveries)
    }

    pub fn edit_comment(&self, turn: Option<&str>, id: i64, body: &str) -> Result<bool> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let (previous, life, folded): (Option<String>, String, bool) = tx.query_row(
            "SELECT c.body,c.lifecycle,coalesce(c.comment_id<=root.resolved_through,0) FROM local_comments c JOIN local_comments root ON root.comment_id=c.thread_root WHERE c.comment_id=?1",
            [id],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?)),
        )?;
        ensure!(life != "deleted", "deleted comment cannot be edited");
        let changed = previous.as_deref() != Some(body);
        if changed {
            let visible_change = context::filter_html_comments(previous.as_deref().unwrap_or(""))
                != context::filter_html_comments(body);
            tx.execute("UPDATE local_comments SET body=?2,revision=revision+1,updated_at=CASE WHEN ?4 THEN ?3 ELSE updated_at END WHERE comment_id=?1",params![id,body,now(),visible_change])?;
            if visible_change {
                let target: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [id], |r| r.get(0))?;
                Self::activity_in(&tx, &target, writer.as_ref(), "comment_edited", Some(id), &format!("comment #{id}"))?;
                let deliveries = self.discussion_changed(
                    &tx,
                    id,
                    writer.as_ref(),
                    "edited",
                )?;
                if life == "visible" && !folded {
                    self.direct_mentions(&tx, id, body, &mentioned_members(previous.as_deref().unwrap_or("")), writer.as_ref(), &deliveries)?;
                }
            }
        }
        tx.commit().with_context(|| format!("comment #{id} 编辑提交未能确认；读取 braid comment view {id} 核对结果"))?;
        Ok(changed)
    }
    pub fn comment_lifecycle(&self, turn: Option<&str>, id: i64, action: &str) -> Result<bool> {
        self.comment_visibility(turn, id, action, None)
    }
    pub fn comment_visibility(
        &self,
        turn: Option<&str>,
        id: i64,
        action: &str,
        reason: Option<&str>,
    ) -> Result<bool> {
        if action == "hide" {
            return self.hide_comments(turn, &[id], reason).map(|results| results[0].1);
        }
        let lifecycle = match action {
            "hide" => "hidden",
            "unhide" => "visible",
            "delete" => "deleted",
            _ => bail!("invalid comment action"),
        };
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let (prior, old_reason): (String, Option<String>) = tx.query_row(
            "SELECT lifecycle,hide_reason FROM local_comments WHERE comment_id=?1",
            [id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
        ensure!(prior != "deleted" || lifecycle == "deleted", "deleted comment cannot be restored");
        let reason = if lifecycle == "hidden" { reason.or(old_reason.as_deref()) } else { None };
        let changed = prior != lifecycle || old_reason.as_deref() != reason;
        if changed {
            tx.execute("UPDATE local_comments SET lifecycle=?2,body=CASE WHEN ?2='deleted' THEN NULL ELSE body END,hide_reason=?4,revision=revision+1,updated_at=?3 WHERE comment_id=?1",params![id,lifecycle,now(),reason])?;
            let target: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [id], |r| r.get(0))?;
            Self::activity_in(&tx, &target, writer.as_ref(), action, Some(id), reason.unwrap_or(""))?;
            self.discussion_changed(&tx, id, writer.as_ref(), action)?;
        }
        tx.commit().with_context(|| format!("comment #{id} 的 {action} 提交未能确认；读取 braid comment view {id} --json lifecycle 核对结果"))?;
        Ok(changed)
    }
    pub fn hide_comments(&self, turn: Option<&str>, ids: &[i64], reason: Option<&str>) -> Result<Vec<(i64, bool)>> {
        ensure!(!ids.is_empty(), "hide requires at least one comment ID");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let mut comments = Vec::new();
        for id in ids.iter().copied().collect::<BTreeSet<_>>() {
            let (prior, old_reason): (String, Option<String>) = tx.query_row(
                "SELECT lifecycle,hide_reason FROM local_comments WHERE comment_id=?1",
                [id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )?;
            ensure!(prior != "deleted", "deleted comment cannot be restored");
            comments.push((id, prior, old_reason));
        }
        let mut results = Vec::new();
        for (id, prior, old_reason) in comments {
            let next_reason = reason.or(old_reason.as_deref());
            let changed = prior != "hidden" || old_reason.as_deref() != next_reason;
            results.push((id, changed));
            if changed {
                tx.execute(
                    "UPDATE local_comments SET lifecycle='hidden',hide_reason=?2,revision=revision+1,updated_at=?3 WHERE comment_id=?1",
                    params![id, next_reason, now()],
                )?;
                let target: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [id], |r| r.get(0))?;
                Self::activity_in(&tx, &target, writer.as_ref(), "hide", Some(id), next_reason.unwrap_or(""))?;
                self.discussion_changed(&tx, id, writer.as_ref(), "hide")?;
            }
        }
        tx.commit().with_context(|| format!("评论 {ids:?} 的 hide 提交未能确认；用 braid comment view ID --json lifecycle 逐条读取结果"))?;
        Ok(results)
    }
    pub fn resolve_comment(&self, turn: Option<&str>, id: i64, resolved: bool) -> Result<Vec<CommentResolution>> {
        self.resolve_comments(turn, &[id], resolved)
    }
    pub fn resolve_comments(&self, turn: Option<&str>, ids: &[i64], resolved: bool) -> Result<Vec<CommentResolution>> {
        ensure!(!ids.is_empty(), "resolve requires at least one comment ID");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let mut threads = BTreeMap::new();
        for id in ids.iter().copied().collect::<BTreeSet<_>>() {
            let (root, cutoff): (i64, Option<i64>) = tx.query_row("SELECT root.comment_id,root.resolved_through FROM local_comments c JOIN local_comments root ON root.comment_id=c.thread_root WHERE c.comment_id=?1", [id], |r| Ok((r.get(0)?, r.get(1)?)))?;
            ensure!(id == root, "comment #{id} is a reply in discussion root #{root}; no comments changed; use braid comment {} {root} for the whole discussion, or braid comment hide {id} --reason TEXT for this reply branch", if resolved { "resolve" } else { "unresolve" });
            let next = if resolved {
                Some(tx.query_row(
                    "SELECT max(comment_id) FROM local_comments WHERE thread_root=?1",
                    [root],
                    |r| r.get::<_, i64>(0),
                )?)
            } else {
                None
            };
            threads.entry(root).or_insert((id, cutoff, next));
        }
        let mut results = Vec::new();
        for (root, (id, cutoff, next)) in threads {
            let changed = next != cutoff;
            let affected_comments = if changed {
                tx.query_row(
                    "SELECT count(*) FROM local_comments WHERE thread_root=?1
                       AND comment_id > ?2 AND comment_id <= ?3",
                    params![root, if resolved { cutoff.unwrap_or(0) } else { 0 },
                            if resolved { next.unwrap_or(0) } else { cutoff.unwrap_or(0) }],
                    |r| r.get(0),
                )?
            } else { 0 };
            if changed {
                tx.execute(
                    "UPDATE local_comments SET resolved_through=?2 WHERE comment_id=?1",
                    params![root, next],
                )?;
                let target: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [id], |r| r.get(0))?;
                Self::activity_in(&tx, &target, writer.as_ref(), if resolved { "resolved" } else { "unresolved" }, Some(id), &format!("thread #{root}"))?;
                self.discussion_changed(
                    &tx,
                    id,
                    writer.as_ref(),
                    if resolved { "resolved" } else { "unresolved" },
                )?;
            }
            results.push(CommentResolution {
                previous_resolved_through: cutoff,
                thread_root: root,
                resolved_through: next,
                affected_comments,
                changed,
            });
        }
        tx.commit().with_context(|| format!("讨论根 {ids:?} 的折叠提交未能确认；用 braid comment view ROOT --json resolved,folded 逐条读取结果"))?;
        Ok(results)
    }
    pub fn react(&self, turn: Option<&str>, id: i64, expression: &str, remove: bool) -> Result<bool> {
        ensure!(!expression.trim().is_empty(), "reaction expression is empty");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let life: String =
            tx.query_row("SELECT lifecycle FROM local_comments WHERE comment_id=?1", [id], |r| {
                r.get(0)
            })?;
        ensure!(life != "deleted" || remove, "deleted comment cannot receive reactions");
        let actor = writer.as_ref().map_or("external", |w| w.group.as_str());
        let sql = if remove {
            "DELETE FROM local_comment_reactions WHERE comment_id=?1 AND actor=?2 AND expression=?3"
        } else {
            "INSERT OR IGNORE INTO local_comment_reactions(comment_id,actor,expression) VALUES(?1,?2,?3)"
        };
        let changed = tx.execute(sql, params![id, actor, expression])? > 0;
        if changed {
            let target: String = tx.query_row("SELECT work_item_node_id FROM local_comments WHERE comment_id=?1", [id], |r| r.get(0))?;
            Self::activity_in(&tx, &target, writer.as_ref(), if remove { "reaction_removed" } else { "reaction_added" }, Some(id), expression)?;
        }
        tx.commit().with_context(|| format!("comment #{id} 表情提交未能确认；读取 braid comment view {id} --json reactions 核对结果"))?;
        Ok(changed)
    }
    fn comments(c: &Connection, target: &str) -> Result<Vec<CommentSnapshot>> {
        Self::read_comments(c, target, None, None, false, false, true, true)
    }
    // Read from the complete ancestry, including for a single-comment view.
    // Reply IDs always follow their parents, so the chain cannot cycle.
    fn comment_hidden_by(c: &Connection, id: i64) -> rusqlite::Result<Option<(i64, Option<String>)>> {
        c.query_row(
            "WITH RECURSIVE ancestors(comment_id,reply_to,lifecycle,hide_reason,depth) AS (
                SELECT p.comment_id,p.reply_to,p.lifecycle,p.hide_reason,1
                FROM local_comments c JOIN local_comments p ON p.comment_id=c.reply_to WHERE c.comment_id=?1
                UNION ALL SELECT p.comment_id,p.reply_to,p.lifecycle,p.hide_reason,a.depth+1
                FROM ancestors a JOIN local_comments p ON p.comment_id=a.reply_to
             ) SELECT comment_id,hide_reason FROM ancestors WHERE lifecycle='hidden' ORDER BY depth LIMIT 1",
            [id], |row| Ok((row.get(0)?, row.get(1)?)),
        ).optional()
    }
    fn comment_effectively_hidden(c: &Connection, id: i64) -> rusqlite::Result<bool> {
        let own: bool = c.query_row("SELECT lifecycle!='visible' FROM local_comments WHERE comment_id=?1", [id], |row| row.get(0))?;
        Ok(own || Self::comment_hidden_by(c, id)?.is_some())
    }
    fn display_member(c: &Connection, raw: Option<String>) -> rusqlite::Result<String> {
        let Some(raw) = raw else { return Ok("external".into()) };
        if matches!(raw.as_str(), "external" | "Braid") { return Ok(raw); }
        c.query_row(
            "SELECT COALESCE(a.member_login, '') FROM agent_instances ai JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE ai.agent_id=?1 ORDER BY a.generation DESC LIMIT 1",
            [&raw], |r| r.get::<_, String>(0),
        ).optional()?.filter(|value| !value.is_empty()).map_or(Ok("历史成员".into()), Ok)
    }
    fn read_comments(
        c: &Connection,
        target: &str,
        thread: Option<i64>,
        comment: Option<i64>,
        include_hidden: bool,
        expand_resolved: bool,
        body: bool,
        reactions: bool,
    ) -> Result<Vec<CommentSnapshot>> {
        let mut comments = c.prepare("SELECT c.comment_id,w.number,c.lifecycle,CASE WHEN ?4 THEN c.body ELSE NULL END,c.created_at,c.updated_at,coalesce(c.system_author,c.writer_group),c.reply_to,c.thread_root,root.resolved_through,c.hide_reason FROM local_comments c JOIN work_items w ON w.node_id=c.work_item_node_id JOIN local_comments root ON root.comment_id=c.thread_root WHERE c.work_item_node_id=?1 AND (?2 IS NULL OR c.thread_root=?2) AND (?3 IS NULL OR c.comment_id=?3) ORDER BY c.comment_id")?.query_map(params![target,thread,comment,body],|r| {
            let id:i64=r.get(0)?;
            let life:String=r.get(2)?;
            let author:Option<String>=r.get(6)?;
            let author_login = Self::display_member(c, author)?;
            let cutoff:Option<i64>=r.get(9)?;
            let folded=cutoff.is_some_and(|cutoff| id<=cutoff);
            let hidden_by = Self::comment_hidden_by(c, id)?;
            let visible=life=="visible" && hidden_by.is_none() && (!folded || expand_resolved);
            Ok(CommentSnapshot {
                node_id:format!("comment:{id}"),database_id:id.to_string(),repository:"local/run".into(),work_item_number:r.get::<_,i64>(1)? as u64,
                author:Some(Actor {node_id:format!("member:{author_login}"),login:author_login}),
                created_at:r.get(4)?, updated_at:if visible || include_hidden {r.get(5)?} else {r.get(4)?},
                body:if life!="deleted" && (visible || include_hidden) {r.get(3)?} else {None},
                minimized:life=="hidden",minimized_reason:r.get(10)?,pinned:false,deleted:life=="deleted",
                hidden_by:hidden_by.as_ref().map(|(id, _)| *id),hidden_by_reason:hidden_by.and_then(|(_, reason)| reason),
                reply_to:r.get(7)?,thread_root:r.get(8)?,resolved:cutoff.is_some(),folded,reactions:vec![],
            })
        })?.collect::<Result<Vec<_>,_>>()?;
        for comment in comments.iter_mut().filter(|_| reactions) {
            let raw_reactions: Vec<(String, String)> = c
                .prepare("SELECT actor,expression FROM local_comment_reactions WHERE comment_id=?1 ORDER BY expression,actor")?
                .query_map([&comment.database_id], |r| Ok((r.get(0)?, r.get(1)?)))?
                .collect::<Result<_, _>>()?;
            comment.reactions = raw_reactions
                .into_iter()
                .map(|(raw, expression)| Ok(CommentReaction { actor: Self::display_member(c, Some(raw))?, expression }))
                .collect::<Result<_, anyhow::Error>>()?;
        }
        Ok(comments)
    }
    pub fn view_comment(
        &self,
        id: i64,
        thread: bool,
        include_hidden: bool,
    ) -> Result<Vec<CommentSnapshot>> {
        self.view_comment_for_fields(id, thread, include_hidden, true, true)
    }
    pub fn view_comment_for_fields(&self, id: i64, thread: bool, include_hidden: bool, body: bool, reactions: bool) -> Result<Vec<CommentSnapshot>> {
        let mut c = self.connect()?;
        let tx = c.transaction()?;
        let (target, root): (String, i64) = tx.query_row(
            "SELECT work_item_node_id,thread_root FROM local_comments WHERE comment_id=?1",
            [id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
        Self::read_comments(&tx, &target, Some(root), (!thread).then_some(id), include_hidden, !thread, body, reactions)
    }
    pub fn comments_for(&self, kind: &str, id: i64) -> Result<Vec<CommentSnapshot>> {
        let c = self.connect()?;
        Self::item_for_read(&c, kind, id, false, false)?;
        Self::comments(&c, &node(kind, id))
    }
    fn reference(item: &Item) -> WorkItemReference {
        WorkItemReference {
            node_id: node(&item.kind, item.id),
            repository_node_id: "local".into(),
            repository: "local/run".into(),
            number: item.id as u64,
            kind: if item.kind == "issue" {
                WorkItemKind::Issue
            } else {
                WorkItemKind::PullRequest
            },
            title: item.title.clone(),
            state: item.state.clone(),
            state_reason: item.reason.clone(),
        }
    }
    fn issue_in(c: &Connection, id: i64) -> Result<IssueSnapshot> {
        let item = Self::item(c, "issue", id)?;
        let assignees = item.assignees.clone();
        let prs:Vec<i64>=c.prepare("SELECT w.number FROM associations a JOIN work_items w ON w.node_id=a.pr_node_id WHERE a.issue_node_id=?1 AND a.active=1 ORDER BY w.number")?.query_map([node("issue",id)],|r|r.get(0))?.collect::<Result<_,_>>()?;
        let children: Vec<i64> = c.prepare("SELECT w.number FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.parent_issue=?1 ORDER BY w.number")?.query_map([node("issue",id)], |r| r.get(0))?.collect::<Result<_,_>>()?;
        let parent = item
            .parent
            .map(|id| Self::item(c, "issue", id).map(|item| Self::reference(&item)))
            .transpose()?;
        Ok(IssueSnapshot {
            node_id: node("issue", id),
            database_id: id.to_string(),
            repository_node_id: "local".into(),
            repository: "local/run".into(),
            number: id as u64,
            title: item.title,
            body: item.body,
            state: item.state,
            state_reason: item.reason,
            updated_at: format!("{:020}", item.revision),
            assignees,
            associated_prs: prs
                .into_iter()
                .map(|id| Self::item(c, "pr", id).map(|i| Self::reference(&i)))
                .collect::<Result<_>>()?,
            comments: Self::comments(c, &node("issue", id))?,
            parent,
            sub_issues: children
                .into_iter()
                .map(|id| Self::item(c, "issue", id).map(|item| Self::reference(&item)))
                .collect::<Result<_>>()?,
            ..Default::default()
        })
    }
    pub fn issue(&self, id: i64) -> Result<IssueSnapshot> {
        let mut c = self.connect()?;
        let tx = c.transaction()?;
        Self::issue_in(&tx, id)
    }
    pub fn pull_request(&self, id: i64) -> Result<PullRequestSnapshot> {
        let mut c = self.connect()?;
        let tx = c.transaction()?;
        let item = Self::item(&tx, "pr", id)?;
        let assignees = item.assignees.clone();
        let issues:Vec<i64>=tx.prepare("SELECT w.number FROM associations a JOIN work_items w ON w.node_id=a.issue_node_id WHERE a.pr_node_id=?1 AND a.active=1 ORDER BY w.number")?.query_map([node("pr",id)],|r|r.get(0))?.collect::<Result<_,_>>()?;
        Ok(PullRequestSnapshot {
            node_id: node("pr", id),
            database_id: id.to_string(),
            repository_node_id: "local".into(),
            repository: "local/run".into(),
            number: id as u64,
            title: item.title,
            body: item.body,
            state: item.state.clone(),
            draft: item.draft,
            merged: item.state == "MERGED",
            updated_at: format!("{:020}", item.revision),
            base_ref: item.base_ref.context("PR has no base ref")?,
            head_repository: Some("local/run".into()),
            head_ref: item.head_ref.context("PR has no branch")?,
            assignees,
            associated_issues: issues
                .into_iter()
                .map(|id| Self::issue_in(&tx, id))
                .collect::<Result<_>>()?,
            conversation: Self::comments(&tx, &node("pr", id))?,
            ..Default::default()
        })
    }
    pub fn canonical(&self, kind: &str, id: i64) -> Result<CanonicalContext> {
        match kind {
            "issue" => Ok(CanonicalContext::Issue(self.issue(id)?)),
            "pr" => Ok(CanonicalContext::PullRequest(self.pull_request(id)?)),
            _ => bail!("kind must be issue or pr"),
        }
    }
    pub fn view_details(&self, kind: &str, id: i64) -> Result<serde_json::Value> {
        self.view_details_for_fields(kind, id, None)
    }
    pub fn view_details_for_fields(&self, kind: &str, id: i64, fields: Option<&[&str]>) -> Result<serde_json::Value> {
        let wants = |field: &str| fields.is_none_or(|fields| fields.contains(&field));
        let mut connection = self.connect()?;
        let connection = connection.transaction()?;
        let item = Self::item_for_read(&connection, kind, id, kind == "pr" && wants("closing_issues"), wants("execution_error"))?;
        let mut details = serde_json::Map::new();
        if wants("execution_error") { details.insert("execution_error".into(), serde_json::to_value(item.execution.and_then(|fact| fact.error))?); }
        if wants("subscriptions") { details.insert("subscriptions".into(), serde_json::to_value(self.subscriptions(kind, id)?)?); }
        if kind == "issue" {
            if wants("parent_issue") {
                let parent = item.parent.map(|id| Self::item_for_read(&connection, "issue", id, false, false).map(|item| Self::reference(&item))).transpose()?;
                details.insert("parent_issue".into(), serde_json::to_value(parent)?);
            }
            for (field, query, related_kind) in [
                ("sub_issues", "SELECT w.number FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.parent_issue=?1 ORDER BY w.number", "issue"),
                ("associated_prs", "SELECT w.number FROM associations a JOIN work_items w ON w.node_id=a.pr_node_id WHERE a.issue_node_id=?1 AND a.active=1 ORDER BY w.number", "pr"),
            ] {
                if wants(field) {
                    let ids = connection.prepare(query)?.query_map([node(kind, id)], |r| r.get(0))?.collect::<rusqlite::Result<Vec<i64>>>()?;
                    let references = ids.into_iter().map(|id| Self::item_for_read(&connection, related_kind, id, false, false).map(|item| Self::reference(&item))).collect::<Result<Vec<_>>>()?;
                    details.insert(field.into(), serde_json::to_value(references)?);
                }
            }
        } else if kind == "pr" {
            if wants("associated_issues") {
                let ids = connection.prepare("SELECT w.number FROM associations a JOIN work_items w ON w.node_id=a.issue_node_id WHERE a.pr_node_id=?1 AND a.active=1 ORDER BY w.number")?.query_map([node(kind,id)], |r| r.get(0))?.collect::<rusqlite::Result<Vec<i64>>>()?;
                let issues = ids.into_iter().map(|id| {
                    let item = Self::item_for_read(&connection, "issue", id, false, false)?;
                    Ok(serde_json::json!({"number":item.id,"title":item.title,"state":item.state,"assignees":item.assignees}))
                }).collect::<Result<Vec<_>>>()?;
                details.insert("associated_issues".into(), serde_json::to_value(issues)?);
            }
            for (prefix, reference) in [("base", &item.base_ref), ("head", &item.head_ref)] {
                let reference = reference.as_deref().context("PR has no branch ref")?;
                if wants(&format!("{prefix}_ref")) { details.insert(format!("{prefix}_ref"), reference.into()); }
                if wants(&format!("{prefix}_commit")) || wants(&format!("{prefix}_error")) {
                    let commit = git(&self.repository()?, &["rev-parse", "--verify", reference]);
                    details.insert(format!("{prefix}_commit"), serde_json::to_value(commit.as_ref().ok())?);
                    details.insert(format!("{prefix}_error"), serde_json::to_value(commit.as_ref().err().map(ToString::to_string))?);
                }
            }
            if wants("draft") { details.insert("draft".into(), item.draft.into()); }
            if wants("merge_commit") {
                let merged: Option<String> = connection.query_row("SELECT merge_commit FROM local_merges WHERE pr_node_id=?1 AND lifecycle='applied'", [node(kind,id)], |r| r.get(0)).optional()?;
                details.insert("merge_commit".into(), serde_json::to_value(merged)?);
            }
            if wants("closing_issues") {
                let closing = if item.state == "MERGED" {
                    let frozen: String = connection.query_row("SELECT closing_issues FROM local_merges WHERE pr_node_id=?1", [node(kind,id)], |r| r.get(0))?;
                    serde_json::from_str::<Vec<i64>>(&frozen)?
                } else { self.closing_issues_in(&connection, &item.body, item.base_ref.as_deref().context("PR has no base ref")?)? };
                details.insert("closing_issues".into(), serde_json::to_value(closing)?);
            }
            if wants("assignee_activity") {
                let assignee_activity = connection.query_row(
                    "SELECT a.lifecycle,ai.lifecycle,ps.lifecycle,t.lifecycle,t.started_at,t.trigger_kind
                     FROM local_items l
                     JOIN assignments a ON a.work_item_node_id=l.node_id
                       AND a.assignment_revision=l.assignment_revision
                       AND a.member_login=l.desired_member_login
                     JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
                     LEFT JOIN provider_sessions ps ON ps.agent_id=ai.agent_id
                       AND ps.lifecycle NOT IN ('replaced','retired')
                     LEFT JOIN turns t ON t.session_id=ps.session_id
                       AND t.lifecycle IN ('starting','running')
                     WHERE l.node_id=?1
                     ORDER BY a.generation DESC,ps.started_at DESC,t.started_at DESC LIMIT 1",
                    [node("pr", id)],
                    |r| Ok(serde_json::json!({
                        "assignment":r.get::<_,String>(0)?,
                        "agent":r.get::<_,String>(1)?,
                        "session":r.get::<_,Option<String>>(2)?,
                        "turn":r.get::<_,Option<String>>(3)?,
                        "turn_started_at":r.get::<_,Option<String>>(4)?,
                        "turn_trigger":r.get::<_,Option<String>>(5)?,
                        "unpublished_work":"unknown"
                    })),
                ).optional()?;
                details.insert("assignee_activity".into(), serde_json::to_value(assignee_activity)?);
            }
            if wants("assignee_deliveries") {
                let assignee_deliveries = if let Some(assignee) = item.assignees.first() {
                    connection.prepare(
                        "SELECT c.comment_id,d.status FROM local_comment_delivery d
                         JOIN local_comments c ON c.comment_id=d.comment_id
                         WHERE c.work_item_node_id=?1 AND d.recipient_login=?2
                         ORDER BY c.comment_id DESC LIMIT 3"
                    )?.query_map(params![node("pr", id), assignee.login], |r| {
                        Ok(serde_json::json!({"comment":r.get::<_,i64>(0)?,"status":r.get::<_,String>(1)?}))
                    })?.collect::<rusqlite::Result<Vec<_>>>()?
                } else { Vec::new() };
                details.insert("assignee_deliveries".into(), serde_json::to_value(assignee_deliveries)?);
            }
        }
        Ok(serde_json::Value::Object(details))
    }
}

impl LocalObjects {
    pub fn create_pr(
        &self,
        turn: Option<&str>,
        issue_ids: &[i64],
        title: &str,
        body: &str,
        request_id: Option<&str>,
    ) -> Result<i64> {
        self.create_pr_with_profile(turn, issue_ids, title, body, request_id, None)
    }
    pub fn create_pr_with_profile(
        &self,
        turn: Option<&str>,
        issue_ids: &[i64],
        title: &str,
        body: &str,
        request_id: Option<&str>,
        profile: Option<&str>,
    ) -> Result<i64> {
        Ok(self
            .create_pr_with_profile_and_head(
                turn, issue_ids, title, body, request_id, profile, None,
            )?
            .id)
    }
    pub fn create_pr_with_profile_and_head(
        &self,
        turn: Option<&str>,
        issue_ids: &[i64],
        title: &str,
        body: &str,
        request_id: Option<&str>,
        profile: Option<&str>,
        requested_head: Option<&str>,
    ) -> Result<PrCreateResult> {
        self.create_pr_with_options(turn, issue_ids, title, body, request_id, profile, None, requested_head, true)
    }
    #[allow(clippy::too_many_arguments)]
    pub fn create_pr_with_options(
        &self,
        turn: Option<&str>,
        issue_ids: &[i64],
        title: &str,
        body: &str,
        request_id: Option<&str>,
        profile: Option<&str>,
        requested_base: Option<&str>,
        requested_head: Option<&str>,
        draft: bool,
    ) -> Result<PrCreateResult> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let (repository, delivery_ref): (String, String) =
            tx.query_row("SELECT repository,delivery_ref FROM local_run", [], |row| {
                Ok((row.get(0)?, row.get(1)?))
            })?;
        if let Some(request_id) = request_id {
            ensure!(!request_id.is_empty(), "request id is empty");
            if let Some(id) = tx
                .query_row(
                    "SELECT w.number FROM local_items l JOIN work_items w ON w.node_id=l.node_id WHERE l.request_id=?1",
                    [request_id],
                    |row| row.get(0),
                )
                .optional()?
            {
                let result = Self::pr_create_result(&tx, &repository, id)?;
                if let Some(base) = requested_base {
                    ensure!(normalize_branch(base)? == result.base_ref, "request id belongs to PR with a different base");
                }
                if let Some(head) = requested_head {
                    ensure!(normalize_branch(head)? == result.head_ref, "request id belongs to PR with a different head");
                }
                return Ok(result);
            }
        }
        if let Some(login) = profile {
            self.profile_for_login(&tx, login)?;
        }
        ensure!(!issue_ids.is_empty(), "PR requires at least one --issue");
        ensure!(!title.trim().is_empty(), "title is empty");
        for issue in issue_ids {
            Self::item(&tx, "issue", *issue)?;
        }
        let repo = git2::Repository::open(repository)?;
        let base_ref = requested_base.map(normalize_branch).transpose()?.unwrap_or(delivery_ref);
        let base = repo.find_reference(&base_ref)
            .with_context(|| format!("published base {base_ref:?} is not present in origin"))?
            .peel_to_commit()?;
        let explicit_head = requested_head.map(normalize_branch).transpose()?;
        ensure!(explicit_head.as_deref() != Some(base_ref.as_str()), "PR base and head must differ");
        let head = requested_head
            .map(|_| {
                let reference = explicit_head.as_deref().expect("normalized head");
                repo.find_reference(reference)
                    .with_context(|| format!("published head {reference:?} is not present in origin"))?
                    .peel_to_commit()
                    .with_context(|| format!("published head {reference:?} is not a commit"))
            })
            .transpose()?
            .unwrap_or_else(|| base.clone());
        let observed_unique_head = if head.id() != base.id() && !repo.graph_descendant_of(base.id(), head.id())? {
            Some(head.id().to_string())
        } else {
            None
        };
        let id = self.create_item(&tx, "pr", title, body, None, request_id, profile)?;
        if let Some(login) = Self::item(&tx,"pr",id)?.assignees.first() {
            Self::subscribe_in(&tx, &node("pr",id), &login.login, "assignment")?;
        }
        Self::activity_in(&tx, &node("pr",id), writer.as_ref(), "created", None, title)?;
        let branch = explicit_head.unwrap_or_else(|| format!("refs/heads/braid/pr-{id}"));
        tx.execute(
            "UPDATE local_items SET head_ref=?2,base_ref=?3,draft=?4,created_base_commit=?5,observed_unique_head_commit=?6 WHERE node_id=?1",
            params![node("pr", id), branch, base_ref, draft, base.id().to_string(), observed_unique_head],
        )?;
        for issue in issue_ids {
            self.link_in(&tx, id, *issue, true, writer.as_ref())?;
        }
        if profile.is_some() {
            self.emit(
                &tx,
                &node("pr", id),
                EventKind::Assign,
                Some("activate"),
                &format!("PR #{id} 已创建并指派。"),
                writer.as_ref(),
                None,
            )?;
            self.emit(&tx, &node("pr", id), EventKind::Wake, None, "新 PR 工作", None, None)?;
        }
        if requested_head.is_none() {
            match repo.find_reference(&branch) {
                Ok(existing) => ensure!(existing.target() == Some(head.id()), "existing PR branch differs from base"),
                Err(error) if error.code() == git2::ErrorCode::NotFound => {
                    repo.branch(&format!("braid/pr-{id}"), &head, false)?;
                }
                Err(error) => return Err(error.into()),
            }
        }
        let assignees = Self::item_for_read(&tx, "pr", id, false, false)?.assignees;
        tx.commit().with_context(|| format!("pr #{id} 创建提交未能确认；origin 中的分支 {branch} 可能已创建；先用 braid pr view {id} --json number,state 核对结果"))?;
        Ok(PrCreateResult {
            id,
            created: true,
            assignees,
            head_ref: branch,
            head_commit: head.id().to_string(),
            base_ref,
            base_commit: base.id().to_string(),
        })
    }
    fn pr_create_result(
        tx: &Transaction<'_>,
        repository: &str,
        id: i64,
    ) -> Result<PrCreateResult> {
        let (head_ref, base_ref): (String, String) = tx
            .query_row("SELECT head_ref,base_ref FROM local_items WHERE node_id=?1", [node("pr", id)], |r| Ok((r.get(0)?,r.get(1)?)))?;
        let repo = git2::Repository::open(repository)?;
        let head_commit = repo.revparse_single(&head_ref)?.peel_to_commit()?;
        let base_commit = repo.revparse_single(&base_ref)?.peel_to_commit()?;
        Ok(PrCreateResult {
            id,
            created: false,
            assignees: Self::item_for_read(tx, "pr", id, false, false)?.assignees,
            head_ref,
            head_commit: head_commit.id().to_string(),
            base_ref,
            base_commit: base_commit.id().to_string(),
        })
    }
    fn link_in(
        &self,
        tx: &Transaction<'_>,
        pr: i64,
        issue: i64,
        active: bool,
        writer: Option<&Writer>,
    ) -> Result<bool> {
        Self::item(tx, "pr", pr)?;
        Self::item(tx, "issue", issue)?;
        let prior: Option<bool> = tx
            .query_row(
                "SELECT active FROM associations WHERE issue_node_id=?1 AND pr_node_id=?2",
                params![node("issue", issue), node("pr", pr)],
                |r| r.get(0),
            )
            .optional()?;
        if prior == Some(active) || (prior.is_none() && !active) {
            return Ok(false);
        }
        tx.execute("INSERT INTO associations(issue_node_id,pr_node_id,source,observed_version,active) VALUES(?1,?2,'local',?3,?4) ON CONFLICT(issue_node_id,pr_node_id) DO UPDATE SET active=excluded.active,observed_version=excluded.observed_version",params![node("issue",issue),node("pr",pr),now(),active])?;
        Self::activity_in(tx, &node("issue",issue), writer, if active { "linked_pr" } else { "unlinked_pr" }, None, &format!("PR #{pr}"))?;
        Self::activity_in(tx, &node("pr",pr), writer, if active { "linked_issue" } else { "unlinked_issue" }, None, &format!("Issue #{issue}"))?;
        self.metadata_changed(tx, &[node("pr",pr),node("issue",issue)], writer,
            &format!("PR #{pr} 与 Issue #{issue} 关联变为 {active}；详情入口：`braid pr view {pr}`"))?;
        Ok(true)
    }
    pub fn link(&self, turn: Option<&str>, pr: i64, issue: i64, active: bool) -> Result<bool> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let changed = self.link_in(&tx, pr, issue, active, writer.as_ref())?;
        tx.commit().with_context(|| format!("pr #{pr} 与 issue #{issue} 的关联提交未能确认；读取 braid pr view {pr} --json associated_issues 核对结果"))?;
        Ok(changed)
    }
    pub fn worktree(&self, kind: &str, id: i64) -> Result<PathBuf> {
        Ok(PathBuf::from(self.connect()?.query_row("SELECT wt.path FROM worktrees wt JOIN agent_instances ai ON ai.agent_id=wt.agent_id JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE a.work_item_node_id=?1 ORDER BY a.generation DESC LIMIT 1",[node(kind,id)],|r|r.get::<_,String>(0))?))
    }
    pub fn ready(&self, turn: Option<&str>, id: i64) -> Result<String> {
        self.ready_with_undo(turn, id, false).map(|result| result.head_commit)
    }
    pub fn ready_with_undo(&self, turn: Option<&str>, id: i64, undo: bool) -> Result<ReadyResult> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let item = Self::item(&tx, "pr", id)?;
        ensure!(item.state == "OPEN", "PR is not open");
        let repo = self.repository()?;
        let expected_branch = item.head_ref.as_deref().context("missing head ref")?;
        let head = git(&repo, &["rev-parse", "--verify", expected_branch])?;
        let mut changed = item.draft != undo;
        if !undo {
            let base_ref = item.base_ref.as_deref().context("missing base ref")?;
            let base = git(&repo, &["rev-parse", "--verify", base_ref])?;
            let origin = git2::Repository::open(&repo)?;
            let base_oid = git2::Oid::from_str(&base)?;
            let head_oid = git2::Oid::from_str(&head)?;
            if base != head && !origin.graph_descendant_of(base_oid, head_oid)? {
                changed |= tx.execute(
                    "UPDATE local_items SET observed_unique_head_commit=?2 WHERE node_id=?1 AND observed_unique_head_commit IS NOT ?2",
                    params![node("pr", id), head],
                )? > 0;
            }
        }
        if item.draft != undo {
            tx.execute(
                "UPDATE local_items SET draft=?2,ready_commit=CASE WHEN ?2=0 THEN ?3 ELSE ready_commit END,revision=revision+1 WHERE node_id=?1",
                params![node("pr", id), undo, head],
            )?;
            Self::activity_in(&tx, &node("pr",id), writer.as_ref(), if undo { "draft" } else { "ready" }, None, &head)?;
            self.notify_followers(&tx, &node("pr",id), writer.as_ref(), &format!("PR #{id} {} at {head}", if undo { "draft" } else { "ready" }))?;
            self.emit(
                &tx,
                &node("pr", id),
                EventKind::Wake,
                None,
                &format!("PR #{id} {} at {head}", if undo { "draft" } else { "ready" }),
                writer.as_ref(),
                None,
            )?;
        }
        let ready_commit = if item.draft != undo && !undo { Some(head.clone()) } else { item.ready_commit };
        tx.commit().with_context(|| format!("pr #{id} ready 提交未能确认；读取 braid pr view {id} --json draft,ready_commit 核对结果"))?;
        Ok(ReadyResult { id, changed, head_commit: head, ready_commit, draft: undo })
    }
    pub fn lifecycle(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        reopen: bool,
        reason: Option<&str>,
    ) -> Result<()> {
        self.lifecycle_with_comment(turn, kind, id, reopen, reason, None).map(|_| ())
    }
    pub fn lifecycle_with_comment(
        &self,
        turn: Option<&str>,
        kind: &str,
        id: i64,
        reopen: bool,
        reason: Option<&str>,
        comment: Option<&str>,
    ) -> Result<(bool, Option<i64>)> {
        if let Some(comment) = comment {
            ensure!(!comment.trim().is_empty(), "comment body is empty");
        }
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let item = Self::item(&tx, kind, id)?;
        ensure!(item.state != "MERGED", "merged PR cannot close or reopen");
        let next = if reopen { "OPEN" } else { "CLOSED" };
        if item.state == next {
            return Ok((false, None));
        }
        let closing_comment = if reopen { None } else { comment };
        let mut comment_id = closing_comment.map(|body| self.comment_reply_in(&tx, writer.as_ref(), kind, id, body, None)).transpose()?;
        self.transition_in(&tx, kind, id, reopen, reason, writer.as_ref())?;
        if reopen && item.desired_profile.is_some() {
            let revivable: bool = tx.query_row(
                "SELECT EXISTS(SELECT 1 FROM assignments a
                 JOIN agent_instances ai ON ai.assignment_id=a.assignment_id
                 JOIN local_items l ON l.node_id=a.work_item_node_id
                 WHERE a.work_item_node_id=?1 AND a.lifecycle IN ('sleeping','materializing','active','finalizing')
                   AND ai.profile_id=l.desired_profile_id AND a.assignment_revision=l.assignment_revision)",
                [node(kind, id)],
                |row| row.get(0),
            )?;
            if !revivable {
                self.emit(
                    &tx,
                    &node(kind, id),
                    EventKind::Assign,
                    Some("activate"),
                    &format!("{kind} #{id} reopened for its assignee"),
                    writer.as_ref(),
                    None,
                )?;
                self.emit(&tx, &node(kind, id), EventKind::Wake, None, "工作项已重新开放。", None, None)?;
            }
        }
        if reopen {
            comment_id = comment.map(|body| self.comment_reply_in(&tx, writer.as_ref(), kind, id, body, None)).transpose()?;
        }
        // Related objects expose the new state on their next legitimate dispatch.
        tx.commit().with_context(|| format!("{kind} #{id} 状态提交未能确认；读取 braid {kind} view {id} --json state 核对结果"))?;
        Ok((true, comment_id))
    }
    fn transition_in(&self, tx: &Transaction<'_>, kind: &str, id: i64,
        reopen: bool, reason: Option<&str>, writer: Option<&Writer>) -> Result<()> {
        let next = if reopen { "OPEN" } else { "CLOSED" };
        tx.execute(
            "UPDATE work_items SET state=?2,observed_at=?3 WHERE node_id=?1",
            params![node(kind, id), next, now()],
        )?;
        tx.execute("UPDATE local_items SET state_reason=?2,revision=revision+1,ready_commit=CASE WHEN ?3 THEN NULL ELSE ready_commit END WHERE node_id=?1",params![node(kind,id),if reopen {None} else {reason},reopen])?;
        Self::activity_in(tx, &node(kind,id), writer, if reopen { "reopened" } else { "closed" }, None, reason.unwrap_or(""))?;
        self.emit(
            tx,
            &node(kind, id),
            EventKind::Lifecycle,
            Some(if reopen { "reopened" } else { "closed" }),
            &format!("{kind} #{id} {next}: {}", reason.unwrap_or("")),
            writer,
            None,
        )?;
        self.notify_followers(tx, &node(kind,id), writer, &format!("{kind} #{id} {next}"))?;
        Ok(())
    }

    fn closing_issues_in(&self, tx: &Connection, body: &str, base: &str) -> Result<Vec<i64>> {
        let repo = self.repository()?;
        if git(&repo, &["symbolic-ref", "HEAD"])? != normalize_branch(base)? {
            return Ok(Vec::new());
        }
        let mut result = Vec::new();
        for id in closing_references(body) {
            if tx.query_row("SELECT EXISTS(SELECT 1 FROM work_items WHERE kind='issue' AND number=?1)",
                [id], |r| r.get::<_, bool>(0))? { result.push(id); }
        }
        Ok(result)
    }

    fn close_merge_issues_in(&self, tx: &Transaction<'_>, pr: i64, writer: Option<&Writer>) -> Result<Vec<i64>> {
        let frozen: String = tx.query_row("SELECT closing_issues FROM local_merges WHERE pr_node_id=?1",
            [node("pr", pr)], |r| r.get(0))?;
        let issues: Vec<i64> = serde_json::from_str(&frozen)?;
        let mut closed = Vec::new();
        for issue in issues {
            if Self::item(tx, "issue", issue)?.state == "OPEN" {
                closed.push(issue);
                self.transition_in(tx, "issue", issue, false, Some(&format!("Completed by PR #{pr}")), writer)?;
            }
        }
        Ok(closed)
    }

    pub fn merge(&self, turn: Option<&str>, id: i64) -> Result<String> {
        self.merge_with_match(turn, id, None).map(|result| result.merge_commit)
    }
    pub fn merge_with_match(&self, turn: Option<&str>, id: i64, expected_head: Option<&str>) -> Result<MergeResult> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let item = Self::item(&tx, "pr", id)?;
        if item.state == "MERGED" {
            return tx.query_row(
                "SELECT merge_commit,base_ref,head_commit FROM local_merges WHERE pr_node_id=?1",
                [node("pr", id)],
                |r| Ok(MergeResult { id, changed: false, outcome: "already_merged", merge_commit: r.get(0)?, base_ref: r.get(1)?, head_commit: r.get(2)?, target_commit: None, git_ref_updated: false, closed_issues: Vec::new() }),
            ).map_err(Into::into);
        }
        ensure!(item.state == "OPEN", "PR is closed");
        let prepared: Option<String> = tx.query_row(
            "SELECT merge_commit FROM local_merges WHERE pr_node_id=?1 AND lifecycle='prepared'",
            [node("pr", id)],
            |r| r.get(0),
        ).optional()?;
        if let Some(merged) = prepared {
            drop(tx);
            return self.apply_merge(id, expected_head).with_context(|| format!("PR #{id} has saved merge intent {merged}; application result is not confirmed; inspect braid pr view {id} --json state,merge_commit"));
        }
        ensure!(!item.draft, "PR is draft");
        let source = self.repository()?;
        let branch = item.head_ref.context("PR has no branch")?;
        let head = git(&source, &["rev-parse", "--verify", &branch])?;
        if let Some(expected) = expected_head {
            ensure!(expected == head, "PR #{id} head changed: expected {expected}, current {head}");
        }
        let reference = item.base_ref.context("PR has no base")?;
        let base = git(&source, &["rev-parse", &reference])?;
        let repo = git2::Repository::open(&source)?;
        let base_object = repo.find_commit(git2::Oid::from_str(&base)?)?;
        let head_object = repo.find_commit(git2::Oid::from_str(&head)?)?;
        if base == head || repo.graph_descendant_of(base_object.id(), head_object.id())? {
            let (created_base, observed_head): (Option<String>, Option<String>) = tx.query_row(
                "SELECT created_base_commit,observed_unique_head_commit FROM local_items WHERE node_id=?1",
                [node("pr", id)],
                |r| Ok((r.get(0)?, r.get(1)?)),
            )?;
            let created_base = created_base.context(format!(
                "PR #{id} target {reference} at {base} already contains head {head}, but this PR has no recorded creation base; its integration cannot be confirmed"
            ))?;
            let observed_head = observed_head.context(format!(
                "PR #{id} target {reference} at {base} already contains head {head}, but Braid never observed this PR head outside its target base; its integration cannot be confirmed"
            ))?;
            let observed_oid = git2::Oid::from_str(&observed_head)?;
            ensure!(head == observed_head || repo.graph_descendant_of(head_object.id(), observed_oid)?,
                "PR #{id} head {head} no longer contains the previously observed unique head {observed_head}; its integration cannot be confirmed");
            tx.execute(
                "INSERT INTO local_merges(pr_node_id,base_commit,head_commit,merge_commit,base_ref,head_ref,lifecycle,writer_group,writer_turn,writer_node) VALUES(?1,?2,?3,?4,?5,?6,'applied',?7,?8,?9) ON CONFLICT(pr_node_id) DO UPDATE SET base_commit=excluded.base_commit,head_commit=excluded.head_commit,merge_commit=excluded.merge_commit,base_ref=excluded.base_ref,head_ref=excluded.head_ref,lifecycle='applied',error=NULL,writer_group=excluded.writer_group,writer_turn=excluded.writer_turn,writer_node=excluded.writer_node",
                params![node("pr",id),created_base,head,base,reference,branch,writer.as_ref().map(|w|&w.group),writer.as_ref().map(|w|&w.turn),writer.as_ref().map(|w|&w.node)],
            )?;
            let closing = self.closing_issues_in(&tx, &item.body, &reference)?;
            tx.execute("UPDATE local_merges SET closing_issues=?2 WHERE pr_node_id=?1",
                params![node("pr", id), serde_json::to_string(&closing)?])?;
            let closed_issues = self.close_merge_issues_in(&tx, id, writer.as_ref())?;
            tx.execute("UPDATE work_items SET state='MERGED' WHERE node_id=?1", [node("pr", id)])?;
            tx.execute("UPDATE local_items SET revision=revision+1 WHERE node_id=?1", [node("pr", id)])?;
            Self::activity_in(&tx, &node("pr", id), writer.as_ref(), "merged", None,
                &format!("observed {reference} at {base} already contains head {head}; no Git ref was updated"))?;
            self.notify_followers(&tx, &node("pr", id), writer.as_ref(),
                &format!("PR #{id} 的当前 head {head} 已包含于 {reference}（观测提交 {base}）；已记录整合状态，Braid 未更新 Git 引用。"))?;
            self.emit(&tx, &node("pr", id), EventKind::Lifecycle, Some("closed"),
                &format!("PR #{id} 的当前 head {head} 已包含于 {reference}（观测提交 {base}）；已记录整合状态，Braid 未更新 Git 引用。"),
                writer.as_ref(), None)?;
            let issues: Vec<String> = tx.prepare("SELECT issue_node_id FROM associations WHERE pr_node_id=?1 AND active=1")?
                .query_map([node("pr",id)], |r| r.get(0))?.collect::<Result<_,_>>()?;
            for target in issues {
                Self::activity_in(&tx, &target, writer.as_ref(), "associated_pr_merged", None,
                    &format!("PR #{id} current head {head} was observed in {reference} at {base}"))?;
            }
            tx.commit()?;
            return Ok(MergeResult { id, changed: true, outcome: "recorded_existing_integration", merge_commit: base.clone(), base_ref: reference, head_commit: head, target_commit: Some(base), git_ref_updated: false, closed_issues });
        }
        let mut index = repo.merge_commits(&base_object, &head_object, None)?;
        if index.has_conflicts() {
            tx.execute("INSERT INTO local_merges(pr_node_id,base_commit,head_commit,base_ref,head_ref,lifecycle,error) VALUES(?1,?2,?3,?4,?5,'conflict','merge conflict') ON CONFLICT(pr_node_id) DO UPDATE SET base_commit=excluded.base_commit,head_commit=excluded.head_commit,base_ref=excluded.base_ref,head_ref=excluded.head_ref,merge_commit=NULL,lifecycle='conflict',error='merge conflict'",params![node("pr",id),base,head,reference,branch])?;
            self.emit(
                &tx,
                &node("pr", id),
                EventKind::Wake,
                None,
                &format!(
                    "PR #{id} 合并未发生：源分支 {branch} 与目标分支 {reference} 存在冲突。"
                ),
                writer.as_ref(),
                None,
            )?;
            tx.commit()?;
            bail!(
                "PR #{id} 合并未发生：源分支 {branch} 与目标分支 {reference} 存在冲突"
            )
        }
        let tree_id = index.write_tree_to(&repo)?;
        let signature = git2::Signature::now("Braid", "braid@local.invalid")?;
        let merged = repo
            .commit(
                None,
                &signature,
                &signature,
                &format!("Merge local PR #{id}"),
                &repo.find_tree(tree_id)?,
                &[&base_object, &head_object],
            )?
            .to_string();
        tx.execute("INSERT INTO local_merges(pr_node_id,base_commit,head_commit,merge_commit,base_ref,head_ref,lifecycle) VALUES(?1,?2,?3,?4,?5,?6,'prepared') ON CONFLICT(pr_node_id) DO UPDATE SET base_commit=excluded.base_commit,head_commit=excluded.head_commit,merge_commit=excluded.merge_commit,base_ref=excluded.base_ref,head_ref=excluded.head_ref,lifecycle='prepared',error=NULL",params![node("pr",id),base,head,merged,reference,branch])?;
        let closing = self.closing_issues_in(&tx, &item.body, &reference)?;
        tx.execute("UPDATE local_merges SET closing_issues=?2 WHERE pr_node_id=?1",
            params![node("pr", id), serde_json::to_string(&closing)?])?;
        tx.execute("UPDATE local_merges SET writer_group=?2,writer_turn=?3,writer_node=?4 WHERE pr_node_id=?1",params![node("pr",id),writer.as_ref().map(|w|&w.group),writer.as_ref().map(|w|&w.turn),writer.as_ref().map(|w|&w.node)])?;
        tx.commit()?;
        self.apply_merge(id, expected_head).with_context(|| format!("PR #{id} saved merge intent {merged}; application result is not confirmed; inspect braid pr view {id} --json state,merge_commit"))
    }
    fn apply_merge(&self, id: i64, expected_head: Option<&str>) -> Result<MergeResult> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let (base, head, merged, life, reference, branch): (String, String, String, String, String, String) = tx.query_row(
            "SELECT base_commit,head_commit,merge_commit,lifecycle,base_ref,head_ref FROM local_merges WHERE pr_node_id=?1",
            [node("pr", id)],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?,r.get(4)?,r.get(5)?)),
        )?;
        let writer = tx.query_row(
            "SELECT writer_group,writer_turn,writer_node FROM local_merges WHERE pr_node_id=?1",
            [node("pr", id)],
            |r| {
                Ok((
                    r.get::<_, Option<String>>(0)?,
                    r.get::<_, Option<String>>(1)?,
                    r.get::<_, Option<String>>(2)?,
                ))
            },
        )?;
        let writer = match writer {
            (Some(group), Some(turn), Some(node)) => Some(Writer { group, turn, node }),
            _ => None,
        };
        if life == "applied" {
            return Ok(MergeResult { id, changed: false, outcome: "already_merged", merge_commit: merged, base_ref: reference, head_commit: head, target_commit: None, git_ref_updated: false, closed_issues: Vec::new() });
        }
        ensure!(life == "prepared", "merge is not prepared");
        let source = self.repository()?;
        let current = git(&source, &["rev-parse", &reference])?;
        let publish_error = if current == base {
            if let Some(expected) = expected_head {
                ensure!(expected == head, "PR #{id} prepared head {head} differs from expected {expected}");
            }
            update_merge_refs(
                &source, &normalize_branch(&branch)?, &head, &reference, &base, &merged,
            ).err()
        } else {
            None
        };
        let git_ref_updated = current == base && publish_error.is_none();
        let current = if current == base { git(&source, &["rev-parse", &reference])? } else { current };
        let origin = git2::Repository::open(&source)?;
        if current != merged && !origin.graph_descendant_of(git2::Oid::from_str(&current)?, git2::Oid::from_str(&merged)?)? {
            let error = publish_error.map_or_else(
                || format!("delivery ref moved from {base} to {current}; prepared merge {merged} is absent from the target history"),
                |error| error.to_string(),
            );
            tx.execute(
                "UPDATE local_merges SET lifecycle='conflict',error=?2 WHERE pr_node_id=?1",
                params![node("pr", id), error],
            )?;
            tx.commit()?;
            bail!("{error}");
        }
        let observed_effect = format!("PR #{id} 已观察 origin {reference} 包含合并 {merged}（当前 {current}，本次 Git 引用更新={git_ref_updated}）；对象完成尚未确认；读取 braid pr view {id} --json state,merge_commit");
        (|| -> Result<MergeResult> {
            tx.execute(
                "UPDATE local_merges SET lifecycle='applied' WHERE pr_node_id=?1",
                [node("pr", id)],
            )?;
            tx.execute("UPDATE work_items SET state='MERGED' WHERE node_id=?1", [node("pr", id)])?;
            tx.execute(
                "UPDATE local_items SET revision=revision+1 WHERE node_id=?1",
                [node("pr", id)],
            )?;
            Self::activity_in(&tx, &node("pr",id), writer.as_ref(), "merged", None, &format!("{reference} at {current} contains prepared merge {merged}"))?;
            self.notify_followers(&tx, &node("pr",id), writer.as_ref(), &format!("PR #{id} merged at {merged}; {reference} at {current} contains it"))?;
            self.emit(
                &tx,
                &node("pr", id),
                EventKind::Lifecycle,
                Some("closed"),
                &format!("PR #{id} merged at {merged}; origin {reference} at {current} contains it. Local clones can fetch origin to receive it."),
                writer.as_ref(),
                None,
            )?;
            let issues: Vec<String> = tx.prepare("SELECT issue_node_id FROM associations WHERE pr_node_id=?1 AND active=1")?
                .query_map([node("pr",id)], |r| r.get(0))?.collect::<Result<_,_>>()?;
            for target in issues {
                Self::activity_in(&tx, &target, writer.as_ref(), "associated_pr_merged", None, &format!("PR #{id} merged at {merged}"))?;
            }
            let closed_issues = self.close_merge_issues_in(&tx, id, writer.as_ref())?;
            tx.commit()?;
            Ok(MergeResult { id, changed: true, outcome: "applied_prepared_merge", merge_commit: merged, base_ref: reference, head_commit: head, target_commit: Some(current), git_ref_updated, closed_issues })
        })().context(observed_effect)
    }
    #[tracing::instrument(name = "braid.merge.recover", skip_all, err)]
    pub fn recover_merges(&self) -> Result<()> {
        let c = self.connect()?;
        let ids:Vec<i64>=c.prepare("SELECT w.number FROM local_merges m JOIN work_items w ON w.node_id=m.pr_node_id WHERE m.lifecycle='prepared'")?.query_map([],|r|r.get(0))?.collect::<Result<_,_>>()?;
        for id in ids {
            self.apply_merge(id, None)?;
        }
        Ok(())
    }
}
fn closing_references(body: &str) -> BTreeSet<i64> {
    use comrak::{Arena, Options, nodes::NodeValue, parse_document};
    let arena = Arena::new();
    let visible = context::filter_html_comments(body);
    let document = parse_document(&arena, &visible, &Options::default());
    let mut ids = BTreeSet::new();
    for paragraph in document.descendants().filter(|n| matches!(n.data.borrow().value, NodeValue::Paragraph | NodeValue::Heading(_))) {
        let mut text = String::new();
        for node in paragraph.descendants() {
            match &node.data.borrow().value {
                NodeValue::Text(value) => text.push_str(value),
                NodeValue::SoftBreak | NodeValue::LineBreak => text.push(' '),
                NodeValue::Code(_) | NodeValue::HtmlInline(_) => text.push_str(" <code> "),
                _ => {}
            }
        }
        let words: Vec<_> = text.split_whitespace().collect();
        for pair in words.windows(2) {
            let keyword = pair[0].trim_matches(|c: char| c.is_ascii_punctuation()).to_ascii_lowercase();
            if !matches!(keyword.as_str(), "close" | "closes" | "closed" | "fix" | "fixes" | "fixed" | "resolve" | "resolves" | "resolved") { continue; }
            let Some(reference) = pair[1].strip_prefix('#') else { continue };
            let digits = reference.trim_end_matches(|c: char| matches!(c, '.' | ',' | ';' | ':' | '!' | '?' | ')' ));
            if let Ok(id) = digits.parse::<i64>() { if id > 0 { ids.insert(id); } }
        }
    }
    ids
}

fn update_merge_refs(repo: &Path, source_ref: &str, head: &str, delivery_ref: &str, base: &str, merged: &str) -> Result<()> {
    use std::io::Write;
    use std::process::Stdio;

    let mut child = std::process::Command::new("git")
        .arg("-C").arg(repo).args(["update-ref", "--stdin"])
        .stdin(Stdio::piped()).stdout(Stdio::piped()).stderr(Stdio::piped()).spawn()?;
    let input = format!(
        "start\nverify {source_ref} {head}\nupdate {delivery_ref} {merged} {base}\nprepare\ncommit\n"
    );
    child.stdin.take().context("git update-ref stdin is unavailable")?.write_all(input.as_bytes())?;
    let output = child.wait_with_output()?;
    ensure!(
        output.status.success(),
        "PR source or delivery changed; merge did not occur: {}",
        String::from_utf8_lossy(&output.stderr).trim()
    );
    Ok(())
}

pub fn git(repo: &Path, args: &[&str]) -> Result<String> {
    let output = std::process::Command::new("git").arg("-C").arg(repo).args(args).output()?;
    ensure!(
        output.status.success(),
        "git {}: {}",
        args.join(" "),
        String::from_utf8_lossy(&output.stderr).trim()
    );
    Ok(String::from_utf8(output.stdout)?.trim().into())
}
