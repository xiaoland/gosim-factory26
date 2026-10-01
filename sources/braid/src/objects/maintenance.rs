//! One completed cleaner response becomes one object/event/receipt transaction.
use super::*;
use sha2::{Digest, Sha256};

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct NativeMaintenanceSource {
    pub session_id: String,
    pub session_file: String,
    pub leaf_id: String,
    pub invoking_entry_id: String,
    pub tool_call_id: String,
    pub branch_digest: String,
    pub source_file_digest: String,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceWriter {
    pub agent_id: String,
    pub turn_id: String,
    pub session_id: String,
    pub assignment_id: String,
    pub member_login: String,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceItem {
    pub node_id: String,
    pub kind: String,
    pub number: i64,
    pub title: String,
    pub description: String,
    pub state: String,
    pub revision: i64,
    pub parent: Option<i64>,
    pub assignment_revision: i64,
    pub assignee: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceComment {
    pub id: i64,
    pub body: Option<String>,
    pub lifecycle: String,
    pub author: String,
    pub writer_group: Option<String>,
    pub writer_turn: Option<String>,
    pub system_author: Option<String>,
    pub revision: i64,
    pub reply_to: Option<i64>,
    pub thread_root: i64,
    pub resolved_through: Option<i64>,
    pub hide_reason: Option<String>,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceMaterial {
    pub item: MaintenanceItem,
    pub comments: Vec<MaintenanceComment>,
    pub requirements: Vec<MaintenanceItem>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceSnapshot {
    pub operation_id: String,
    pub native_source: NativeMaintenanceSource,
    pub writer: MaintenanceWriter,
    pub material: MaintenanceMaterial,
    pub source_digest: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceHide {
    pub id: i64,
    pub reason: String,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceResult {
    #[serde(
        default,
        deserialize_with = "provided_description",
        skip_serializing_if = "Option::is_none"
    )]
    pub description: Option<String>,
    pub hide: Vec<MaintenanceHide>,
    pub resolve: Vec<i64>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceModel {
    pub provider: String,
    pub model: String,
    pub response_model: Option<String>,
    pub response_id: Option<String>,
    pub stop_reason: String,
    pub usage: Option<MaintenanceUsage>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct MaintenanceUsage {
    pub input: f64,
    pub output: f64,
    pub cache_read: f64,
    pub cache_write: f64,
    pub cache_write1h: Option<f64>,
    pub reasoning: Option<f64>,
    pub total_tokens: f64,
    pub cost: MaintenanceCost,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields, rename_all = "camelCase")]
pub struct MaintenanceCost {
    pub input: f64,
    pub output: f64,
    pub cache_read: f64,
    pub cache_write: f64,
    pub total: f64,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct MaintenanceApply {
    pub snapshot: MaintenanceSnapshot,
    pub result: MaintenanceResult,
    pub model: MaintenanceModel,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct MaintenanceEffect {
    pub action: String,
    pub comment_id: i64,
    pub thread_root: i64,
    pub changed: bool,
    pub affected_comments: Option<i64>,
    pub previous_resolved_through: Option<i64>,
    pub resolved_through: Option<i64>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct MaintenanceReceipt {
    pub operation_id: String,
    pub work_item: String,
    pub writer: MaintenanceWriter,
    pub native_source: NativeMaintenanceSource,
    pub source_digest: String,
    pub result_digest: String,
    pub model: MaintenanceModel,
    pub changed: bool,
    pub description_changed: bool,
    pub context_changed: bool,
    pub discussions: Vec<MaintenanceEffect>,
    pub event_ids: Vec<String>,
    pub committed_at: String,
}

fn digest<T: Serialize>(value: &T) -> Result<String> {
    Ok(hex::encode(Sha256::digest(serde_json::to_vec(value)?)))
}

fn provided_description<'de, D: serde::Deserializer<'de>>(
    deserializer: D,
) -> std::result::Result<Option<String>, D::Error> {
    String::deserialize(deserializer).map(Some)
}

fn maintenance_item(c: &Connection, target: &str) -> Result<MaintenanceItem> {
    let (kind, number): (String, i64) =
        c.query_row("SELECT kind,number FROM work_items WHERE node_id=?1", [target], |r| {
            Ok((r.get(0)?, r.get(1)?))
        })?;
    let item = LocalObjects::item_for_read(c, &kind, number, true, false)?;
    Ok(MaintenanceItem {
        node_id: target.into(),
        kind,
        number,
        title: item.title,
        description: item.body,
        state: item.state,
        revision: item.revision,
        parent: item.parent,
        assignment_revision: item.assignment_revision,
        assignee: item.assignees.first().map(|actor| actor.login.clone()),
    })
}

fn maintenance_material(c: &Connection, target: &str) -> Result<MaintenanceMaterial> {
    let item = maintenance_item(c, target)?;
    let comments = c.prepare(
        "SELECT c.comment_id,c.body,c.lifecycle,c.writer_group,c.writer_turn,c.system_author,
                c.revision,c.reply_to,c.thread_root,root.resolved_through,c.hide_reason,c.created_at,c.updated_at
         FROM local_comments c JOIN local_comments root ON root.comment_id=c.thread_root
         WHERE c.work_item_node_id=?1 ORDER BY c.comment_id"
    )?.query_map([target], |r| {
        let writer_group: Option<String> = r.get(3)?;
        let system_author: Option<String> = r.get(5)?;
        Ok(MaintenanceComment {
            id: r.get(0)?, body: r.get(1)?, lifecycle: r.get(2)?,
            author: LocalObjects::display_member(c, system_author.clone().or_else(|| writer_group.clone()))?,
            writer_group, writer_turn: r.get(4)?, system_author, revision: r.get(6)?,
            reply_to: r.get(7)?, thread_root: r.get(8)?, resolved_through: r.get(9)?,
            hide_reason: r.get(10)?, created_at: r.get(11)?, updated_at: r.get(12)?,
        })
    })?.collect::<rusqlite::Result<Vec<_>>>()?;
    let mut requirement_nodes = BTreeSet::new();
    if item.kind == "pr" {
        requirement_nodes.extend(c.prepare(
            "SELECT a.issue_node_id FROM associations a JOIN work_items w ON w.node_id=a.issue_node_id
             WHERE a.pr_node_id=?1 AND a.active=1 AND w.state='OPEN' ORDER BY a.issue_node_id"
        )?.query_map([target], |r| r.get::<_, String>(0))?.collect::<rusqlite::Result<Vec<_>>>()?);
    } else if let Some(parent) = item.parent {
        requirement_nodes.insert(node("issue", parent));
    }
    let mut pending = requirement_nodes.iter().cloned().collect::<Vec<_>>();
    while let Some(requirement) = pending.pop() {
        let parent: Option<String> = c.query_row(
            "SELECT parent_issue FROM local_items WHERE node_id=?1",
            [&requirement],
            |r| r.get(0),
        )?;
        if let Some(parent) = parent
            && parent != target
            && requirement_nodes.insert(parent.clone())
        {
            pending.push(parent);
        }
    }
    let requirements = requirement_nodes
        .into_iter()
        .map(|target| maintenance_item(c, &target))
        .collect::<Result<_>>()?;
    Ok(MaintenanceMaterial { item, comments, requirements })
}

fn maintenance_writer(tx: &Transaction<'_>, writer: &Writer) -> Result<MaintenanceWriter> {
    Ok(tx.query_row(
        "SELECT ps.session_id,a.assignment_id,a.member_login FROM turns t
         JOIN provider_sessions ps ON ps.session_id=t.session_id
         JOIN agent_instances ai ON ai.agent_id=ps.agent_id
         JOIN assignments a ON a.assignment_id=ai.assignment_id WHERE t.turn_id=?1 AND ai.agent_id=?2",
        params![writer.turn, writer.group], |r| Ok(MaintenanceWriter {
            agent_id: writer.group.clone(), turn_id: writer.turn.clone(), session_id: r.get(0)?,
            assignment_id: r.get(1)?, member_login: r.get(2)?,
        }),
    )?)
}

impl LocalObjects {
    pub fn maintenance_snapshot(
        &self,
        turn: Option<&str>,
        operation_id: &str,
        native_source: NativeMaintenanceSource,
    ) -> Result<MaintenanceSnapshot> {
        uuid::Uuid::parse_str(operation_id).context("maintenance operation ID must be a UUID")?;
        ensure!(
            !native_source.session_id.is_empty()
                && !native_source.session_file.is_empty()
                && !native_source.leaf_id.is_empty()
                && !native_source.invoking_entry_id.is_empty()
                && !native_source.tool_call_id.is_empty(),
            "native maintenance source is incomplete"
        );
        ensure!(
            Path::new(&native_source.session_file).is_absolute(),
            "native maintenance source file must be absolute"
        );
        for checksum in [&native_source.branch_digest, &native_source.source_file_digest] {
            ensure!(
                checksum.len() == 64 && checksum.bytes().all(|byte| byte.is_ascii_hexdigit()),
                "native maintenance source digest must be SHA256 hex"
            );
        }
        let mut c = self.connect()?;
        let tx = c.transaction()?;
        let writer = self.writer(&tx, turn)?.context(
            "maintenance requires a current owner execution; external writes are not supported",
        )?;
        let material = maintenance_material(&tx, &writer.node)?;
        Ok(MaintenanceSnapshot {
            operation_id: operation_id.into(),
            native_source,
            writer: maintenance_writer(&tx, &writer)?,
            source_digest: digest(&material)?,
            material,
        })
    }

    pub fn maintenance_receipt(&self, operation_id: &str) -> Result<Option<MaintenanceReceipt>> {
        Self::maintenance_receipt_in(&self.connect()?, operation_id)
            .map(|row| row.map(|(_, receipt)| receipt))
    }

    fn maintenance_receipt_in(
        c: &Connection,
        operation_id: &str,
    ) -> Result<Option<(String, MaintenanceReceipt)>> {
        c.query_row("SELECT request_digest,receipt_json FROM local_maintenance_receipts WHERE operation_id=?1", [operation_id],
            |r| Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?)))
            .optional()?.map(|(request_digest, receipt)| Ok((request_digest, serde_json::from_str(&receipt)?))).transpose()
    }

    #[allow(clippy::too_many_lines)]
    pub fn maintenance_apply(
        &self,
        turn: Option<&str>,
        request: MaintenanceApply,
    ) -> Result<MaintenanceReceipt> {
        let snapshot = &request.snapshot;
        uuid::Uuid::parse_str(&snapshot.operation_id)
            .context("maintenance operation ID must be a UUID")?;
        let request_digest = digest(&request)?;
        let result_digest = digest(&request.result)?;
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        if let Some((previous_digest, receipt)) =
            Self::maintenance_receipt_in(&tx, &snapshot.operation_id)?
        {
            ensure!(
                previous_digest == request_digest,
                "maintenance operation ID already committed with different content"
            );
            return Ok(receipt);
        }
        ensure!(
            request.model.stop_reason == "stop",
            "cleaner did not complete normally; no maintenance changes committed"
        );
        let writer = self.writer(&tx, turn)?.context(
            "maintenance requires a current owner execution; external writes are not supported",
        )?;
        ensure!(
            writer.node == snapshot.material.item.node_id
                && maintenance_writer(&tx, &writer)? == snapshot.writer,
            "maintenance source execution or assignment has changed; no maintenance changes committed"
        );
        let current = maintenance_material(&tx, &writer.node)?;
        ensure!(
            digest(&snapshot.material)? == snapshot.source_digest,
            "maintenance source snapshot digest does not match its content"
        );
        // ponytail: whole supplied snapshot conflicts on any change; narrow only if real rejection rates justify it.
        ensure!(
            digest(&current)? == snapshot.source_digest,
            "maintenance source is stale: description, discussion, assignment, or supplied requirement changed; no maintenance changes committed"
        );
        let mut hide_ids = BTreeSet::new();
        for hide in &request.result.hide {
            ensure!(
                hide.id > 0 && hide_ids.insert(hide.id),
                "duplicate or invalid hide comment ID"
            );
            ensure!(!hide.reason.trim().is_empty(), "hide reason is empty");
            let comment = current
                .comments
                .iter()
                .find(|comment| comment.id == hide.id)
                .context("hide comment is outside the current work item")?;
            ensure!(comment.lifecycle != "deleted", "deleted comment cannot be hidden");
        }
        let mut resolve_ids = BTreeSet::new();
        for id in &request.result.resolve {
            ensure!(
                *id > 0 && resolve_ids.insert(*id),
                "duplicate or invalid resolve discussion ID"
            );
            ensure!(
                !hide_ids.contains(id),
                "the same discussion root cannot be hidden and resolved in one batch"
            );
            let comment = current
                .comments
                .iter()
                .find(|comment| comment.id == *id)
                .context("resolve discussion is outside the current work item")?;
            ensure!(comment.thread_root == *id, "resolve only accepts discussion roots");
        }
        let before_event: i64 =
            tx.query_row("SELECT coalesce(max(rowid),0) FROM events", [], |r| r.get(0))?;
        let body = request.result.description.as_deref().unwrap_or(&current.item.description);
        let description_changed = body != current.item.description;
        let context_changed = context::filter_html_comments(body)
            != context::filter_html_comments(&current.item.description);
        if description_changed {
            tx.execute(
                "UPDATE local_items SET body=?2,revision=revision+1 WHERE node_id=?1",
                params![writer.node, body],
            )?;
            if context_changed {
                Self::activity_in(
                    &tx,
                    &writer.node,
                    Some(&writer),
                    "edited",
                    None,
                    "title/body changed",
                )?;
                self.notify_followers(
                    &tx,
                    &writer.node,
                    Some(&writer),
                    &format!("{} #{} description changed", current.item.kind, current.item.number),
                )?;
                self.description_changed(
                    &tx,
                    &writer.node,
                    Some(&writer),
                    &format!("{} #{} description 已修改", current.item.kind, current.item.number),
                )?;
            }
        }
        let mut discussions = Vec::new();
        for hide in &request.result.hide {
            let comment = current
                .comments
                .iter()
                .find(|comment| comment.id == hide.id)
                .expect("validated comment");
            let changed = comment.lifecycle != "hidden"
                || comment.hide_reason.as_deref() != Some(&hide.reason);
            if changed {
                tx.execute("UPDATE local_comments SET lifecycle='hidden',hide_reason=?2,revision=revision+1,updated_at=?3 WHERE comment_id=?1", params![hide.id, hide.reason, now()])?;
                Self::activity_in(
                    &tx,
                    &writer.node,
                    Some(&writer),
                    "hide",
                    Some(hide.id),
                    &hide.reason,
                )?;
                self.discussion_changed(&tx, hide.id, Some(&writer), "hide")?;
            }
            discussions.push(MaintenanceEffect {
                action: "hide".into(),
                comment_id: hide.id,
                thread_root: comment.thread_root,
                changed,
                affected_comments: None,
                previous_resolved_through: None,
                resolved_through: None,
            });
        }
        for id in &request.result.resolve {
            let comment = current
                .comments
                .iter()
                .find(|comment| comment.id == *id)
                .expect("validated discussion");
            // Snapshot equality makes this maximum exactly the observed cutoff, never a later reply.
            let cutoff = current
                .comments
                .iter()
                .filter(|comment| comment.thread_root == *id)
                .map(|comment| comment.id)
                .max();
            let changed = comment.resolved_through != cutoff;
            if changed {
                tx.execute(
                    "UPDATE local_comments SET resolved_through=?2 WHERE comment_id=?1",
                    params![id, cutoff],
                )?;
                Self::activity_in(
                    &tx,
                    &writer.node,
                    Some(&writer),
                    "resolved",
                    Some(*id),
                    &format!("thread #{id}"),
                )?;
                self.discussion_changed(&tx, *id, Some(&writer), "resolved")?;
            }
            let affected_comments = current
                .comments
                .iter()
                .filter(|comment| {
                    comment.thread_root == *id && comment.id > comment.resolved_through.unwrap_or(0)
                })
                .count() as i64;
            discussions.push(MaintenanceEffect {
                action: "resolve".into(),
                comment_id: *id,
                thread_root: *id,
                changed,
                affected_comments: Some(if changed { affected_comments } else { 0 }),
                previous_resolved_through: comment.resolved_through,
                resolved_through: cutoff,
            });
        }
        let event_ids = tx
            .prepare("SELECT event_id FROM events WHERE rowid>?1 ORDER BY rowid")?
            .query_map([before_event], |r| r.get(0))?
            .collect::<rusqlite::Result<Vec<String>>>()?;
        let receipt = MaintenanceReceipt {
            operation_id: snapshot.operation_id.clone(),
            work_item: writer.node.clone(),
            writer: snapshot.writer.clone(),
            native_source: snapshot.native_source.clone(),
            source_digest: snapshot.source_digest.clone(),
            result_digest,
            model: request.model.clone(),
            changed: description_changed || discussions.iter().any(|effect| effect.changed),
            description_changed,
            context_changed,
            discussions,
            event_ids,
            committed_at: now(),
        };
        Self::activity_in(
            &tx,
            &writer.node,
            Some(&writer),
            "maintenance",
            None,
            &format!(
                "operation {}; changed={}; result={}",
                snapshot.operation_id, receipt.changed, receipt.result_digest
            ),
        )?;
        tx.execute("INSERT INTO local_maintenance_receipts(operation_id,work_item_node_id,writer_agent,writer_turn,source_digest,result_digest,request_digest,source_json,receipt_json,committed_at) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
            params![snapshot.operation_id,writer.node,writer.group,writer.turn,snapshot.source_digest,receipt.result_digest,request_digest,serde_json::to_string(snapshot)?,serde_json::to_string(&receipt)?,receipt.committed_at])?;
        tx.commit().with_context(|| format!("maintenance {} 提交结果未能确认；用 braid maintenance receipt {} 读取持久回执，不要重跑模型", snapshot.operation_id, snapshot.operation_id))?;
        Ok(receipt)
    }
}
