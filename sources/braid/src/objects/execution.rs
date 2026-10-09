//! Read-only execution facts, separate from product state and review conclusions.
use super::*;
use serde_json::{Value, json};

impl LocalObjects {
    pub fn execution_view(&self, kind: &str, id: i64) -> Result<Value> {
        kind_static(kind)?;
        let item = self.read(kind, id)?;
        Ok(json!({
            "work_item": {"kind":kind,"id":id,"state":item.state,
                "member":item.assignees.first().map(|actor| &actor.login),
                "head_ref":item.head_ref,"base_ref":item.base_ref},
            "execution":self.execution_for_node(&node(kind,id))?,
        }))
    }

    pub fn review_execution_view(&self, pr: i64, request: i64) -> Result<Value> {
        let view = self.review_view(pr, request)?;
        let c = self.connect()?;
        let latest_request: Option<i64> = c.query_row(
            "SELECT max(request_id) FROM review_requests WHERE pr_node_id=?1",
            [node("pr",pr)], |r| r.get(0),
        ).optional()?;
        Ok(json!({
            "review": {"pr":pr,"request":request,"status":view.request.status,
                "responsibility":view.request.responsibility,"member":view.current_member,
                "responsibility_revision":view.request.responsibility_revision,
                "latest_request":latest_request,
                "is_latest_request":latest_request.is_none_or(|id| id==request),
                "execution_node":view.execution_node_id,
                "base_commit":view.request.base_commit,"head_commit":view.request.head_commit,
                "checkout":view.checkout,"applicable":view.applicable,
                "freshness_errors":view.freshness_errors},
            "execution":self.execution_for_node(&view.execution_node_id)?,
        }))
    }

    fn execution_for_node(&self, target: &str) -> Result<Value> {
        let c = self.connect()?;
        // Keep the latest assignment even after retirement: its stopping execution
        // remains relevant, but must never be described as the new owner's session.
        let assignment: Option<Value> = c.query_row(
            "SELECT assignment_id,generation,lifecycle,member_login,assigned_at,retired_at
             FROM assignments WHERE work_item_node_id=?1 ORDER BY generation DESC LIMIT 1",
            [target], |r| Ok(json!({"id":r.get::<_,String>(0)?,"generation":r.get::<_,i64>(1)?,
                "status":r.get::<_,String>(2)?,"member":r.get::<_,Option<String>>(3)?,
                "assigned_at":r.get::<_,String>(4)?,"retired_at":r.get::<_,Option<String>>(5)?})),
        ).optional()?;
        let assignment_id = assignment.as_ref().and_then(|v| v["id"].as_str());
        let agent: Option<Value> = c.query_row(
            "SELECT agent_id,profile_id,lifecycle,context_pressure,context_error
             FROM agent_instances WHERE assignment_id=?1 ORDER BY rowid DESC LIMIT 1",
            [assignment_id], |r| Ok(json!({"id":r.get::<_,String>(0)?,"profile":r.get::<_,String>(1)?,
                "status":r.get::<_,String>(2)?,"context_pressure":r.get::<_,String>(3)?,
                "context_error":r.get::<_,Option<String>>(4)?})),
        ).optional()?;
        let agent_id = agent.as_ref().and_then(|v| v["id"].as_str());
        let worktree: Option<Value> = c.query_row(
            "SELECT path,lifecycle,observed_at,head_ref,local_branch FROM worktrees WHERE agent_id=?1",
            [agent_id], |r| Ok(json!({"path":r.get::<_,String>(0)?,"status":r.get::<_,String>(1)?,
                "observed_at":r.get::<_,String>(2)?,"head_ref":r.get::<_,Option<String>>(3)?,
                "local_branch":r.get::<_,Option<String>>(4)?})),
        ).optional()?;
        let session: Option<Value> = c.query_row(
            "SELECT session_id,provider_kind,provider_session_id,lifecycle,started_at,
                    last_resumed_at,last_resume_failed_at,last_resume_error
             FROM provider_sessions WHERE agent_id=?1 ORDER BY started_at DESC,rowid DESC LIMIT 1",
            [agent_id], |r| Ok(json!({"id":r.get::<_,String>(0)?,"provider":r.get::<_,String>(1)?,
                "provider_session_id":r.get::<_,String>(2)?,"status":r.get::<_,String>(3)?,
                "started_at":r.get::<_,String>(4)?,"last_resumed_at":r.get::<_,Option<String>>(5)?,
                "last_resume_failed_at":r.get::<_,Option<String>>(6)?,
                "last_resume_error":r.get::<_,Option<String>>(7)?})),
        ).optional()?;
        let session_id = session.as_ref().and_then(|v| v["id"].as_str());
        let turn: Option<Value> = c.query_row(
            "SELECT turn_id,provider_turn_id,lifecycle,trigger_kind,started_at,ended_at,error
             FROM turns WHERE session_id=?1 ORDER BY rowid DESC LIMIT 1",
            [session_id], |r| {
                let id:String=r.get(0)?;
                Ok(json!({"id":id,"provider_turn_id":r.get::<_,Option<String>>(1)?,
                    "status":r.get::<_,String>(2)?,"trigger":r.get::<_,String>(3)?,
                    "started_at":r.get::<_,Option<String>>(4)?,"ended_at":r.get::<_,Option<String>>(5)?,
                    "error":r.get::<_,Option<String>>(6)?,
                    "input_path":self.state.join("turns").join(format!("{id}.md"))}))
            },
        ).optional()?;
        let reset: Option<Value> = c.query_row(
            "SELECT lifecycle,created_at,updated_at,error FROM context_resets
             WHERE agent_id=?1 ORDER BY created_at DESC,rowid DESC LIMIT 1",
            [agent_id], |r| Ok(json!({"status":r.get::<_,String>(0)?,"created_at":r.get::<_,String>(1)?,
                "updated_at":r.get::<_,String>(2)?,"error":r.get::<_,Option<String>>(3)?})),
        ).optional()?;
        let pending_batches: i64 = c.query_row(
            "SELECT count(*) FROM wake_batches WHERE work_item_node_id=?1 AND lifecycle IN ('pending','runnable')",
            [target], |r| r.get(0),
        )?;
        let provider_id = session.as_ref().and_then(|v| v["provider_session_id"].as_str());
        let physical = if let Some(provider_id) = provider_id {
            crate::local::sessions(self)?.into_iter().find(|v|
                v["session_id"].as_str()==Some(provider_id) && v["group_id"].as_str()==agent_id)
        } else { None };
        let evidence = physical.map(|v| json!({
            "native_session_path":v["native_session_path"],
            "native_session_id":v["native_session_id"],
            "instructions_path":v["instructions_path"],"context_path":v["context_path"],
        }));
        Ok(json!({"observed_at":now(),"node":target,"assignment":assignment,"agent":agent,
            "session":session,"latest_turn":turn,"latest_reset":reset,
            "pending_batches":pending_batches,"worktree":worktree,"evidence":evidence,
            "fault":Self::execution_fact(&c,target)?,
            "origin":self.state.join("origin.git"),
            "note":"执行状态来自Braid最后记录，不证明进程此刻存活或产品取得进展。工作区和原生记录按明确问题只读核对；退任或停止中的执行不代表后任已启动，review候选以请求登记checkout为准。"}))
    }
}
