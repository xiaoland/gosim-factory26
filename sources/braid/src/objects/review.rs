//! Reviews bind responsibility and conclusions to one published candidate.
use super::*;
use crate::worktree;
use sha2::{Digest, Sha256};

macro_rules! review_enum {
    ($name:ident { $($variant:ident => $value:literal),+ $(,)? }) => {
        #[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
        #[serde(rename_all = "snake_case")]
        pub enum $name { $($variant),+ }
        impl $name {
            pub fn as_str(self) -> &'static str { match self { $(Self::$variant => $value),+ } }
        }
        impl FromStr for $name {
            type Err = anyhow::Error;
            fn from_str(value: &str) -> Result<Self> {
                match value { $($value => Ok(Self::$variant)),+, _ => bail!("invalid {} {value:?}", stringify!($name)) }
            }
        }
    };
}
review_enum!(ReviewStatus { Pending => "pending", Completed => "completed", Cancelled => "cancelled" });
review_enum!(ReviewResponsibility { IssueOwner => "issue_owner", AssignedReviewer => "assigned_reviewer" });
review_enum!(ReviewVerdict { Approved => "approved", ChangesRequested => "changes_requested", Inconclusive => "inconclusive" });

#[derive(Debug, Clone, Serialize)]
pub struct ReviewConclusion {
    pub verdict: ReviewVerdict,
    pub body: String,
    pub evidence: Vec<String>,
    pub member: String,
    pub agent: Option<String>,
    pub turn: Option<String>,
    pub checkout_commit: String,
    pub checkout_tree: String,
    pub checkout_dirty: String,
    pub at: String,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewRequest {
    pub id: i64,
    pub node_id: String,
    pub pr: i64,
    pub issue: i64,
    pub request_key: String,
    pub requester_member: String,
    pub requester_agent: Option<String>,
    pub requester_turn: Option<String>,
    pub base_ref: String,
    pub head_ref: String,
    pub base_commit: String,
    pub head_commit: String,
    pub head_tree: String,
    pub requirements_revision: i64,
    pub requirements_body: String,
    pub requirements_digest: String,
    pub responsibility: ReviewResponsibility,
    pub responsibility_revision: i64,
    pub status: ReviewStatus,
    pub conclusion: Option<ReviewConclusion>,
    pub cancelled_reason: Option<String>,
    pub created_at: String,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewCheckout {
    pub request_id: i64,
    pub responsibility_revision: i64,
    pub issue_assignment_revision: i64,
    pub path: PathBuf,
    pub origin: PathBuf,
    pub commit: String,
    pub tree: String,
    pub member: String,
    pub agent: Option<String>,
    pub created_at: String,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewView {
    pub request: ReviewRequest,
    pub current_member: Option<String>,
    pub execution: Option<ExecutionFact>,
    pub checkout: Option<ReviewCheckout>,
    pub applicable: bool,
    pub freshness_errors: Vec<String>,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewList {
    pub items: Vec<ReviewView>,
    pub limit: usize,
    pub has_more: bool,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewSummary {
    pub id: i64,
    pub pr: i64,
    pub issue: i64,
    pub status: ReviewStatus,
    pub responsibility: ReviewResponsibility,
    pub member: Option<String>,
    pub verdict: Option<ReviewVerdict>,
    pub head_commit: String,
}
#[derive(Debug, Clone, Serialize)]
pub struct ReviewRequestContext {
    pub node_id: String,
    pub review: ReviewView,
    pub comments: Vec<CommentSnapshot>,
}

fn db_enum<T: FromStr<Err = anyhow::Error>>(
    row: &rusqlite::Row<'_>,
    index: usize,
) -> rusqlite::Result<T> {
    let value: String = row.get(index)?;
    value.parse::<T>().map_err(|error| {
        rusqlite::Error::FromSqlConversionFailure(index, rusqlite::types::Type::Text, error.into())
    })
}
pub(crate) fn requirements_digest(body: &str) -> String {
    let mut digest = Sha256::new();
    digest.update(b"braid-review-requirements-v1\0");
    digest.update(body.as_bytes());
    hex::encode(digest.finalize())
}
fn request_in(c: &Connection, id: i64) -> Result<ReviewRequest> {
    Ok(c.query_row("SELECT request_id,node_id,pr_node_id,issue_node_id,request_key,requester_member,requester_agent,requester_turn,
        base_ref,head_ref,base_commit,head_commit,head_tree,requirements_revision,requirements_body,requirements_digest,
        responsibility,responsibility_revision,status,verdict,conclusion_body,evidence,conclusion_member,conclusion_agent,
        conclusion_turn,checkout_commit,checkout_tree,checkout_dirty,cancelled_reason,created_at,concluded_at
        FROM review_requests WHERE request_id=?1", [id], |r| {
        let verdict: Option<String> = r.get(19)?;
        let conclusion = if verdict.is_some() {
            Some(ReviewConclusion { verdict: db_enum(r,19)?, body:r.get(20)?,
                evidence: serde_json::from_str(&r.get::<_,String>(21)?).map_err(|error| rusqlite::Error::FromSqlConversionFailure(21,rusqlite::types::Type::Text,Box::new(error)))?,
                member:r.get(22)?,agent:r.get(23)?,turn:r.get(24)?,checkout_commit:r.get(25)?,checkout_tree:r.get(26)?,checkout_dirty:r.get(27)?,at:r.get(30)? })
        } else { None };
        let pr: String = r.get(2)?;
        let issue: String = r.get(3)?;
        let number = |value: &str| -> rusqlite::Result<i64> {
            value.split(':').nth(1).unwrap_or("").parse().map_err(|error| rusqlite::Error::FromSqlConversionFailure(2,rusqlite::types::Type::Text,Box::new(error)))
        };
        Ok(ReviewRequest { id:r.get(0)?,node_id:r.get(1)?,pr:number(&pr)?,issue:number(&issue)?,request_key:r.get(4)?,
            requester_member:r.get(5)?,requester_agent:r.get(6)?,requester_turn:r.get(7)?,base_ref:r.get(8)?,head_ref:r.get(9)?,
            base_commit:r.get(10)?,head_commit:r.get(11)?,head_tree:r.get(12)?,requirements_revision:r.get(13)?,requirements_body:r.get(14)?,
            requirements_digest:r.get(15)?,responsibility:db_enum(r,16)?,responsibility_revision:r.get(17)?,status:db_enum(r,18)?,
            conclusion,cancelled_reason:r.get(28)?,created_at:r.get(29)? })
    }).with_context(|| format!("unknown review request {id}"))?)
}
fn responsibility_in(
    c: &Connection,
    request: &ReviewRequest,
) -> Result<(String, Option<String>, i64)> {
    let target = match request.responsibility {
        ReviewResponsibility::IssueOwner => node("issue", request.issue),
        ReviewResponsibility::AssignedReviewer => request.node_id.clone(),
    };
    let (member, revision): (Option<String>, i64) = c.query_row(
        "SELECT desired_member_login,assignment_revision FROM local_items WHERE node_id=?1",
        [&target],
        |r| Ok((r.get(0)?, r.get(1)?)),
    )?;
    Ok((
        target,
        member,
        if request.responsibility == ReviewResponsibility::IssueOwner { revision } else { 0 },
    ))
}
fn checkout_in(
    c: &Connection,
    request: &ReviewRequest,
    issue_revision: i64,
) -> Result<Option<ReviewCheckout>> {
    Ok(c.query_row("SELECT path,origin,commit_sha,tree_sha,member_login,agent_id,created_at FROM review_checkouts
        WHERE request_id=?1 AND responsibility_revision=?2 AND issue_assignment_revision=?3",
        params![request.id,request.responsibility_revision,issue_revision], |r| Ok(ReviewCheckout {
            request_id:request.id,responsibility_revision:request.responsibility_revision,issue_assignment_revision:issue_revision,
            path:PathBuf::from(r.get::<_,String>(0)?),origin:PathBuf::from(r.get::<_,String>(1)?),commit:r.get(2)?,tree:r.get(3)?,member:r.get(4)?,agent:r.get(5)?,created_at:r.get(6)?,
        })).optional()?)
}
pub(crate) fn summaries_in(c: &Connection, kind: &str, id: i64) -> Result<Vec<ReviewSummary>> {
    ensure!(matches!(kind, "issue" | "pr"), "review summaries require Issue or PR");
    let column = if kind == "issue" { "issue_node_id" } else { "pr_node_id" };
    let ids = c.prepare(&format!("SELECT request_id FROM review_requests WHERE {column}=?1 ORDER BY request_id DESC LIMIT 30"))?
        .query_map([node(kind,id)],|r|r.get::<_,i64>(0))?.collect::<rusqlite::Result<Vec<_>>>()?;
    ids.into_iter()
        .map(|id| {
            let request = request_in(c, id)?;
            let (_, member, _) = responsibility_in(c, &request)?;
            Ok(ReviewSummary {
                id,
                pr: request.pr,
                issue: request.issue,
                status: request.status,
                responsibility: request.responsibility,
                member,
                verdict: request.conclusion.map(|conclusion| conclusion.verdict),
                head_commit: request.head_commit,
            })
        })
        .collect()
}

impl LocalObjects {
    pub fn reviewer_directory(&self) -> Result<Vec<serde_json::Value>> {
        let c = self.connect()?;
        self.current_profiles()?.into_iter().filter(|profile| profile.has_tag("reviewer-only") && !profile.has_tag("root-only")).map(|profile| {
            Ok(serde_json::json!({"login":Self::next_member_for_profile(&c,&profile)?,"description":profile.assignee_description}))
        }).collect()
    }
    fn review_owner(
        &self,
        tx: &Transaction<'_>,
        request: &ReviewRequest,
        writer: Option<&Writer>,
    ) -> Result<()> {
        self.review_writer_for(tx, &node("issue", request.issue), writer)
    }
    fn review_writer_for(
        &self,
        tx: &Transaction<'_>,
        target: &str,
        writer: Option<&Writer>,
    ) -> Result<()> {
        if let Some(writer) = writer {
            ensure!(
                writer.node == target,
                "only the current responsible member of {target} can perform this review action"
            );
            let current:bool=tx.query_row("SELECT EXISTS(SELECT 1 FROM assignments a JOIN agent_instances ai ON ai.assignment_id=a.assignment_id JOIN local_items l ON l.node_id=a.work_item_node_id
                WHERE ai.agent_id=?1 AND a.work_item_node_id=?2 AND a.member_login=l.desired_member_login AND a.assignment_revision=l.assignment_revision AND a.lifecycle IN ('active','finalizing'))",
                params![writer.group,target],|r|r.get(0))?;
            ensure!(current, "review responsibility changed; this writer is no longer current");
        }
        Ok(())
    }
    pub fn request_review(
        &self,
        turn: Option<&str>,
        pr: i64,
        issue: Option<i64>,
        key: &str,
    ) -> Result<ReviewView> {
        ensure!(!key.trim().is_empty(), "review request-id is empty");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        self.review_writer_for(&tx, &node("pr", pr), writer.as_ref())?;
        if let Some(id) = tx
            .query_row("SELECT request_id FROM review_requests WHERE request_key=?1", [key], |r| {
                r.get::<_, i64>(0)
            })
            .optional()?
        {
            let saved = request_in(&tx, id)?;
            ensure!(
                saved.pr == pr && issue.is_none_or(|issue| saved.issue == issue),
                "request-id belongs to a different PR or acceptance Issue"
            );
            drop(tx);
            return self.review_view(pr, id);
        }
        let item = Self::item(&tx, "pr", pr)?;
        ensure!(item.state == "OPEN", "review requires an open PR");
        let issues:Vec<i64>=tx.prepare("SELECT w.number FROM associations a JOIN work_items w ON w.node_id=a.issue_node_id WHERE a.pr_node_id=?1 AND a.active=1 ORDER BY w.number")?
            .query_map([node("pr",pr)],|r|r.get(0))?.collect::<rusqlite::Result<_>>()?;
        let issue = match issue {
            Some(issue) => {
                ensure!(issues.contains(&issue), "Issue #{issue} is not associated with PR #{pr}");
                issue
            }
            None => {
                ensure!(
                    issues.len() == 1,
                    "PR #{pr} has {} acceptance Issues; use --issue to select one associated Issue",
                    issues.len()
                );
                issues[0]
            }
        };
        let requirements = Self::item(&tx, "issue", issue)?;
        let owner = requirements
            .assignees
            .first()
            .context("acceptance Issue has no current responsible member")?;
        let available:bool=tx.query_row("SELECT NOT EXISTS(SELECT 1 FROM assignments a JOIN local_items l ON l.node_id=a.work_item_node_id WHERE a.work_item_node_id=?1 AND a.member_login=l.desired_member_login AND a.assignment_revision=l.assignment_revision AND a.lifecycle IN ('blocked','retired'))",[node("issue",issue)],|r|r.get(0))?;
        ensure!(
            available,
            "acceptance Issue current member @{} has no usable execution responsibility",
            owner.login
        );
        let id: i64 =
            tx.query_row("SELECT coalesce(max(request_id),0)+1 FROM review_requests", [], |r| {
                r.get(0)
            })?;
        let base_ref = normalize_branch(item.base_ref.as_deref().context("PR has no base ref")?)?;
        let head_ref = normalize_branch(item.head_ref.as_deref().context("PR has no head ref")?)?;
        let origin = self.repository()?;
        let base_commit =
            git(&origin, &["rev-parse", "--verify", &format!("{base_ref}^{{commit}}")])?;
        let head_commit =
            git(&origin, &["rev-parse", "--verify", &format!("{head_ref}^{{commit}}")])?;
        let head_tree =
            git(&origin, &["rev-parse", "--verify", &format!("{head_commit}^{{tree}}")])?;
        preserve_candidate(&origin, id, &base_ref, &base_commit, &head_ref, &head_commit)?;
        let review_node = node("review", id);
        tx.execute("INSERT INTO work_items(node_id,repository_node_id,kind,number,state,observed_at) VALUES(?1,'local','review',?2,'OPEN',?3)",params![review_node,id,now()])?;
        tx.execute(
            "INSERT INTO local_items(node_id,title,body) VALUES(?1,?2,?3)",
            params![
                review_node,
                format!("PR #{pr} review #{id}"),
                format!("固定候选验收；完整请求：braid pr review view {pr} {id}")
            ],
        )?;
        tx.execute("INSERT INTO review_requests(request_id,node_id,pr_node_id,issue_node_id,request_key,requester_member,requester_agent,requester_turn,
            base_ref,head_ref,base_commit,head_commit,head_tree,requirements_revision,requirements_body,requirements_digest,responsibility,created_at)
            VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,?12,?13,?14,?15,?16,'issue_owner',?17)",
            params![id,review_node,node("pr",pr),node("issue",issue),key,Self::member_login(&tx,writer.as_ref())?.unwrap_or_else(||"external".into()),writer.as_ref().map(|w|&w.group),writer.as_ref().map(|w|&w.turn),
                base_ref,head_ref,base_commit,head_commit,head_tree,requirements.revision,requirements.body,requirements_digest(&requirements.body),now()])?;
        let reference = format!(
            "PR #{pr} 请求 review #{id}，验收 Issue #{issue}；固定候选 {head_commit}；读取 braid pr review view {pr} {id}"
        );
        for target in [node("pr", pr), node("issue", issue)] {
            Self::activity_in(&tx, &target, writer.as_ref(), "review_requested", None, &reference)?;
        }
        self.notify_member(&tx, &review_node, &owner.login, writer.as_ref(), &reference)?;
        tx.commit().with_context(|| format!("review #{id} commit is unconfirmed; retained candidate refs: refs/braid/reviews/{id}; retry request-id {key}"))?;
        self.review_view(pr, id)
    }
    pub fn review_request(&self, id: i64) -> Result<ReviewRequest> {
        request_in(&self.connect()?, id)
    }
    pub fn review_view(&self, pr: i64, id: i64) -> Result<ReviewView> {
        let c = self.connect()?;
        let request = request_in(&c, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}, not PR #{pr}", request.pr);
        let (target, current_member, issue_revision) = responsibility_in(&c, &request)?;
        let freshness_errors = self.review_freshness_in(&c, &request)?;
        Ok(ReviewView {
            checkout: checkout_in(&c, &request, issue_revision)?,
            execution: Self::execution_fact(&c, &target)?,
            request,
            current_member,
            applicable: freshness_errors.is_empty(),
            freshness_errors,
        })
    }
    pub fn review_list(&self, pr: i64) -> Result<ReviewList> {
        let c = self.connect()?;
        Self::item(&c, "pr", pr)?;
        let mut ids:Vec<i64>=c.prepare("SELECT request_id FROM review_requests WHERE pr_node_id=?1 ORDER BY request_id DESC LIMIT 31")?.query_map([node("pr",pr)],|r|r.get(0))?.collect::<rusqlite::Result<_>>()?;
        let has_more = ids.len() > 30;
        ids.truncate(30);
        Ok(ReviewList {
            items: ids.into_iter().map(|id| self.review_view(pr, id)).collect::<Result<_>>()?,
            limit: 30,
            has_more,
        })
    }
    pub fn review_status(&self) -> Result<Vec<ReviewSummary>> {
        let c = self.connect()?;
        let ids = c
            .prepare("SELECT request_id FROM review_requests ORDER BY request_id DESC LIMIT 30")?
            .query_map([], |r| r.get::<_, i64>(0))?
            .collect::<rusqlite::Result<Vec<_>>>()?;
        ids.into_iter()
            .map(|id| {
                let request = request_in(&c, id)?;
                let (_, member, _) = responsibility_in(&c, &request)?;
                Ok(ReviewSummary {
                    id,
                    pr: request.pr,
                    issue: request.issue,
                    status: request.status,
                    responsibility: request.responsibility,
                    member,
                    verdict: request.conclusion.map(|conclusion| conclusion.verdict),
                    head_commit: request.head_commit,
                })
            })
            .collect()
    }
    pub fn review_context(&self, id: i64) -> Result<ReviewRequestContext> {
        let request = self.review_request(id)?;
        Ok(ReviewRequestContext {
            node_id: request.node_id.clone(),
            review: self.review_view(request.pr, id)?,
            comments: Self::comments(&self.connect()?, &request.node_id)?,
        })
    }
    fn review_freshness_in(&self, c: &Connection, request: &ReviewRequest) -> Result<Vec<String>> {
        let mut errors = Vec::new();
        let pr = Self::item(c, "pr", request.pr)?;
        let origin = self.repository()?;
        for (label, current_ref, frozen_ref, frozen_commit) in [
            (
                "base",
                pr.base_ref.as_deref(),
                request.base_ref.as_str(),
                request.base_commit.as_str(),
            ),
            (
                "head",
                pr.head_ref.as_deref(),
                request.head_ref.as_str(),
                request.head_commit.as_str(),
            ),
        ] {
            if current_ref != Some(frozen_ref) {
                errors.push(format!(
                    "{label} ref changed: frozen {frozen_ref}, current {current_ref:?}"
                ));
            }
            if let Some(current_ref) = current_ref {
                match git(&origin, &["rev-parse", "--verify", &format!("{current_ref}^{{commit}}")])
                {
                    Ok(commit) if commit != frozen_commit => errors.push(format!(
                        "{label} commit changed: frozen {frozen_commit}, current {commit}"
                    )),
                    Err(error) => errors.push(format!("{label}: {error:#}")),
                    _ => {}
                }
            }
        }
        let body: String = c.query_row(
            "SELECT body FROM local_items WHERE node_id=?1",
            [node("issue", request.issue)],
            |r| r.get(0),
        )?;
        let current = requirements_digest(&body);
        if current != request.requirements_digest {
            errors.push(format!(
                "requirements changed: frozen {}, current {current}",
                request.requirements_digest
            ));
        }
        Ok(errors)
    }
    pub(crate) fn validate_review_merge_in(&self, c: &Connection, pr: i64, id: i64) -> Result<()> {
        let request = request_in(c, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}", request.pr);
        ensure!(
            request.status == ReviewStatus::Completed
                && request
                    .conclusion
                    .as_ref()
                    .is_some_and(|conclusion| conclusion.verdict == ReviewVerdict::Approved),
            "review #{id} has no Approved conclusion"
        );
        let errors = self.review_freshness_in(c, &request)?;
        ensure!(errors.is_empty(), "review #{id} does not apply: {}", errors.join("; "));
        Ok(())
    }
    pub fn assign_review(
        &self,
        turn: Option<&str>,
        pr: i64,
        id: i64,
        login: &str,
    ) -> Result<ReviewView> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let request = request_in(&tx, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}", request.pr);
        ensure!(
            request.status == ReviewStatus::Pending,
            "review #{id} is already {}",
            request.status.as_str()
        );
        self.review_owner(&tx, &request, writer.as_ref())?;
        let login = Self::normalize_login(login)?;
        let (existing, revision): (Option<String>, i64) = tx.query_row(
            "SELECT desired_member_login,assignment_revision FROM local_items WHERE node_id=?1",
            [&request.node_id],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )?;
        if existing.as_deref() != Some(&login) {
            let profiles = self.current_profiles()?;
            let mut candidate = None;
            for profile in profiles
                .into_iter()
                .filter(|profile| profile.has_tag("reviewer-only") && !profile.has_tag("root-only"))
            {
                if Self::next_member_for_profile(&tx, &profile)? == login {
                    candidate = Some(profile.id);
                    break;
                }
            }
            let profile = candidate.context(
                "member is not an available reviewer; choose braid assignee list --reviewer",
            )?;
            let item = Item {
                id,
                kind: "review".into(),
                title: format!("PR #{pr} review #{id}"),
                body: String::new(),
                state: "OPEN".into(),
                reason: None,
                head_ref: None,
                base_ref: None,
                draft: false,
                ready_commit: None,
                revision: 1,
                parent: None,
                assignees: existing
                    .into_iter()
                    .map(|login| Actor { node_id: format!("member:{login}"), login })
                    .collect(),
                execution: None,
                desired_profile: None,
                assignment_revision: revision,
            };
            tx.execute("UPDATE review_requests SET responsibility='assigned_reviewer',responsibility_revision=responsibility_revision+1 WHERE request_id=?1",[id])?;
            self.replace_assignee_in(
                &tx,
                "review",
                id,
                &profile,
                &login,
                &item,
                writer.as_ref(),
                false,
            )?;
        }
        tx.commit()?;
        self.review_view(pr, id)
    }
    pub fn checkout_review(&self, turn: Option<&str>, pr: i64, id: i64) -> Result<ReviewCheckout> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let request = request_in(&tx, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}", request.pr);
        ensure!(
            request.status == ReviewStatus::Pending,
            "review #{id} is already {}",
            request.status.as_str()
        );
        let (target, member, issue_revision) = responsibility_in(&tx, &request)?;
        self.review_writer_for(&tx, &target, writer.as_ref())?;
        let member = member.context("review has no current responsible member")?;
        let result = self.provision_review_checkout_in(
            &tx,
            &request,
            issue_revision,
            &member,
            writer.as_ref().map(|w| w.group.as_str()),
            Path::new("git"),
        )?;
        tx.commit()?;
        Ok(result)
    }
    fn provision_review_checkout_in(
        &self,
        tx: &Transaction<'_>,
        request: &ReviewRequest,
        issue_revision: i64,
        member: &str,
        agent: Option<&str>,
        git_path: &Path,
    ) -> Result<ReviewCheckout> {
        if let Some(existing) = checkout_in(tx, request, issue_revision)? {
            ensure!(
                existing.member == member,
                "checkout member differs from current responsibility"
            );
            worktree::verify_review(
                &existing.path,
                &existing.origin,
                &request.head_commit,
                member,
                git_path,
            )?;
            return Ok(existing);
        }
        let origin = self.repository()?;
        let target = self
            .state
            .join("worktrees")
            .join(format!("review-{}", request.id))
            .join(format!("r{}-i{issue_revision}", request.responsibility_revision));
        let branch = format!(
            "braid-review-{}-r{}-i{issue_revision}",
            request.id, request.responsibility_revision
        );
        let provisioned = worktree::provision_review(&worktree::ReviewWorktreeRequest {
            source: &origin,
            target: &target,
            git: git_path,
            commit: &request.head_commit,
            retained_ref: &format!("refs/braid/reviews/{}/head", request.id),
            local_branch: &branch,
            member_login: member,
        })?;
        let checkout = ReviewCheckout {
            request_id: request.id,
            responsibility_revision: request.responsibility_revision,
            issue_assignment_revision: issue_revision,
            path: provisioned.path,
            origin: provisioned.source,
            commit: request.head_commit.clone(),
            tree: request.head_tree.clone(),
            member: member.into(),
            agent: agent.map(str::to_owned),
            created_at: now(),
        };
        tx.execute("INSERT INTO review_checkouts(request_id,responsibility_revision,issue_assignment_revision,path,origin,commit_sha,tree_sha,member_login,agent_id,created_at) VALUES(?1,?2,?3,?4,?5,?6,?7,?8,?9,?10)",
            params![checkout.request_id,checkout.responsibility_revision,issue_revision,checkout.path.to_string_lossy(),checkout.origin.to_string_lossy(),checkout.commit,checkout.tree,member,agent,checkout.created_at])?;
        Ok(checkout)
    }
    pub(crate) fn provision_reviewer_checkout(
        &self,
        id: i64,
        materialization: &crate::store::AgentMaterialization,
        git_path: &Path,
    ) -> Result<ReviewCheckout> {
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let request = request_in(&tx, id)?;
        ensure!(
            request.responsibility == ReviewResponsibility::AssignedReviewer,
            "review has not been delegated"
        );
        let (target, member, issue_revision) = responsibility_in(&tx, &request)?;
        let revision: i64 = tx.query_row(
            "SELECT assignment_revision FROM local_items WHERE node_id=?1",
            [&target],
            |r| r.get(0),
        )?;
        ensure!(
            member.as_deref() == Some(&materialization.member_login)
                && revision == materialization.assignment_revision as i64,
            "review responsibility changed during materialization"
        );
        let checkout = self.provision_review_checkout_in(
            &tx,
            &request,
            issue_revision,
            &materialization.member_login,
            Some(&materialization.agent_id),
            git_path,
        )?;
        tx.commit()?;
        Ok(checkout)
    }
    pub(crate) fn verify_reviewer_checkout(
        &self,
        id: i64,
        path: &Path,
        member: &str,
        git_path: &Path,
    ) -> Result<()> {
        let c = self.connect()?;
        let request = request_in(&c, id)?;
        let (_, current, revision) = responsibility_in(&c, &request)?;
        ensure!(current.as_deref() == Some(member), "review member changed");
        let checkout = checkout_in(&c, &request, revision)?
            .context("review has no registered frozen checkout")?;
        ensure!(checkout.path == path, "review workspace differs from its registered checkout");
        worktree::verify_review(path, &checkout.origin, &request.head_commit, member, git_path)?;
        Ok(())
    }
    pub fn conclude_review(
        &self,
        turn: Option<&str>,
        pr: i64,
        id: i64,
        verdict: ReviewVerdict,
        body: &str,
        evidence: &[String],
    ) -> Result<ReviewView> {
        ensure!(!body.trim().is_empty(), "review conclusion body is empty");
        ensure!(
            evidence.iter().all(|entry| !entry.trim().is_empty()),
            "review evidence entry is empty"
        );
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let request = request_in(&tx, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}", request.pr);
        ensure!(
            request.status == ReviewStatus::Pending,
            "review #{id} is already {}; conclusions are immutable",
            request.status.as_str()
        );
        let (target, member, issue_revision) = responsibility_in(&tx, &request)?;
        self.review_writer_for(&tx, &target, writer.as_ref())?;
        let member = member.context("review has no current responsible member")?;
        let checkout = checkout_in(&tx, &request, issue_revision)?.context(
            "obtain the registered frozen candidate with pr review checkout before concluding",
        )?;
        ensure!(checkout.member == member, "checkout belongs to a previous review responsibility");
        worktree::verify_review(
            &checkout.path,
            &checkout.origin,
            &request.head_commit,
            &member,
            Path::new("git"),
        )?;
        let commit = git(&checkout.path, &["rev-parse", "HEAD"])?;
        let tree = git(&checkout.path, &["rev-parse", "HEAD^{tree}"])?;
        let dirty = git(&checkout.path, &["status", "--porcelain=v1", "--untracked-files=all"])?;
        ensure!(
            commit == request.head_commit && tree == request.head_tree,
            "checkout differs from the frozen candidate"
        );
        let actor = Self::member_login(&tx, writer.as_ref())?.unwrap_or_else(|| "external".into());
        tx.execute("UPDATE review_requests SET status='completed',verdict=?2,conclusion_body=?3,evidence=?4,conclusion_member=?5,conclusion_agent=?6,conclusion_turn=?7,checkout_commit=?8,checkout_tree=?9,checkout_dirty=?10,concluded_at=?11 WHERE request_id=?1 AND status='pending'",
            params![id,verdict.as_str(),body,serde_json::to_string(evidence)?,actor,writer.as_ref().map(|w|&w.group),writer.as_ref().map(|w|&w.turn),commit,tree,dirty,now()])?;
        self.close_review_in(&tx, &request, "review completed", writer.as_ref())?;
        self.review_result_notifications(
            &tx,
            &request,
            writer.as_ref(),
            &format!("review #{id} {}；读取 braid pr review view {pr} {id}", verdict.as_str()),
        )?;
        tx.commit().with_context(|| {
            format!("review #{id} conclusion commit unconfirmed; read pr review view {pr} {id}")
        })?;
        self.review_view(pr, id)
    }
    pub fn cancel_review(
        &self,
        turn: Option<&str>,
        pr: i64,
        id: i64,
        reason: &str,
    ) -> Result<ReviewView> {
        ensure!(!reason.trim().is_empty(), "review cancellation reason is empty");
        let mut c = self.connect()?;
        let tx = c.transaction_with_behavior(TransactionBehavior::Immediate)?;
        let writer = self.writer(&tx, turn)?;
        let request = request_in(&tx, id)?;
        ensure!(request.pr == pr, "review #{id} belongs to PR #{}", request.pr);
        self.review_owner(&tx, &request, writer.as_ref())?;
        ensure!(
            request.status == ReviewStatus::Pending,
            "review #{id} is already {}",
            request.status.as_str()
        );
        tx.execute("UPDATE review_requests SET status='cancelled',cancelled_reason=?2,concluded_at=?3 WHERE request_id=?1",params![id,reason,now()])?;
        self.close_review_in(&tx, &request, reason, writer.as_ref())?;
        self.review_result_notifications(
            &tx,
            &request,
            writer.as_ref(),
            &format!("review #{id} cancelled: {reason}；读取 braid pr review view {pr} {id}"),
        )?;
        tx.commit()?;
        self.review_view(pr, id)
    }
    fn close_review_in(
        &self,
        tx: &Transaction<'_>,
        request: &ReviewRequest,
        reason: &str,
        writer: Option<&Writer>,
    ) -> Result<()> {
        if request.responsibility == ReviewResponsibility::AssignedReviewer {
            self.transition_in(tx, "review", request.id, false, Some(reason), writer)?;
        } else {
            // IssueOwner has no independent driver to consume review-node lifecycle events.
            tx.execute(
                "UPDATE work_items SET state='CLOSED',observed_at=?2 WHERE node_id=?1",
                params![request.node_id, now()],
            )?;
            tx.execute(
                "UPDATE local_items SET state_reason=?2,revision=revision+1 WHERE node_id=?1",
                params![request.node_id, reason],
            )?;
            Self::activity_in(tx, &request.node_id, writer, "closed", None, reason)?;
        }
        Ok(())
    }
    fn review_result_notifications(
        &self,
        tx: &Transaction<'_>,
        request: &ReviewRequest,
        writer: Option<&Writer>,
        reference: &str,
    ) -> Result<()> {
        let author = Self::member_login(tx, writer)?;
        let mut notified = BTreeSet::new();
        for target in [node("pr", request.pr), node("issue", request.issue)] {
            Self::activity_in(tx, &target, writer, "review_concluded", None, reference)?;
            let member: Option<String> = tx.query_row(
                "SELECT desired_member_login FROM local_items WHERE node_id=?1",
                [&target],
                |r| r.get(0),
            )?;
            if let Some(member) = member
                && author.as_deref() != Some(&member)
                && notified.insert(member.clone())
            {
                self.notify_member(tx, &request.node_id, &member, writer, reference)?;
            }
        }
        Ok(())
    }
}
fn preserve_candidate(
    origin: &Path,
    id: i64,
    base_ref: &str,
    base: &str,
    head_ref: &str,
    head: &str,
) -> Result<()> {
    use std::io::Write as _;
    use std::process::Stdio;
    let mut child = std::process::Command::new("git")
        .arg("-C")
        .arg(origin)
        .args(["update-ref", "--stdin"])
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()?;
    let input = format!(
        "start\nverify {base_ref} {base}\nverify {head_ref} {head}\ncreate refs/braid/reviews/{id}/base {base}\ncreate refs/braid/reviews/{id}/head {head}\nprepare\ncommit\n"
    );
    child
        .stdin
        .take()
        .context("candidate retention stdin unavailable")?
        .write_all(input.as_bytes())?;
    let output = child.wait_with_output()?;
    ensure!(
        output.status.success(),
        "review candidate could not be frozen (no request created): {}",
        String::from_utf8_lossy(&output.stderr).trim()
    );
    Ok(())
}
