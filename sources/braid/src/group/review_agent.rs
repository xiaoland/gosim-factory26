//! Materialize a review responsibility without taking over the source PR.
use super::worker::GroupDriver;
use crate::{
    context::{self, ContextPressure},
    group::provider::review_system_prompt,
    queue::scheduler::record_context_pressure,
    store::AssignmentCandidate,
};
use anyhow::{Result, ensure};

impl GroupDriver<'_> {
    pub(super) async fn materialize_next_review_assignment(&self) {
        let candidates =
            match self.store.assignment_candidates("review".into(), self.spec.profile.id.clone()) {
                Ok(candidates) => candidates,
                Err(error) => {
                    tracing::error!(%error,"cannot inspect review activation events");
                    return;
                }
            };
        for candidate in candidates {
            let result = if candidate.action == "unassign" {
                self.settle_unassignment(candidate).await
            } else if candidate.unassigned {
                self.store.ignore_assignment_event(candidate.event_id).map_err(Into::into)
            } else {
                self.materialize_review_assignment(candidate).await
            };
            if let Err(error) = result {
                tracing::error!(%error,"cannot materialize review responsibility");
            }
        }
    }
    pub(super) async fn materialize_review_assignment(
        &self,
        candidate: AssignmentCandidate,
    ) -> Result<()> {
        if candidate.work_item_kind != "review"
            || !matches!(candidate.action.as_str(), "assign" | "mention" | "activate")
        {
            self.store.ignore_assignment_event(candidate.event_id)?;
            return Ok(());
        }
        ensure!(
            self.spec.profile.has_tag("reviewer-only"),
            "review driver requires reviewer-only profile"
        );
        let canonical = self.github.canonical("review", candidate.number as i64)?;
        let rendered = context::render_budgeted(
            &canonical,
            self.spec.profile.context_soft_ratio,
            self.spec.profile.context_hard_bytes,
            self.spec.profile.context_window_tokens,
        );
        context::record_context_revision(&canonical, &rendered, self.store)?;
        let Some(materialization) = self.store.begin_agent_assignment(
            candidate.event_id.clone(),
            self.spec.profile_record.clone(),
            Some(rendered.revision.clone()),
            true,
        )?
        else {
            return Ok(());
        };
        record_context_pressure(self.store, &materialization.assignment_id, &rendered, None)?;
        if rendered.pressure == ContextPressure::Hard {
            self.store.fail_agent_assignment(
                materialization.assignment_id,
                format!("review context exceeds hard limit: {} bytes", rendered.bytes),
            )?;
            return Ok(());
        }
        let checkout = match self.github.provision_reviewer_checkout(
            candidate.number as i64,
            &materialization,
            &self.config.tools.git,
        ) {
            Ok(checkout) => checkout,
            Err(error) => {
                self.store
                    .fail_agent_assignment(materialization.assignment_id, error.to_string())?;
                return Err(error);
            }
        };
        if let Some(preserved) = &materialization.worktree_path {
            ensure!(
                preserved == &checkout.path,
                "preserved review worktree differs from frozen responsibility checkout"
            );
        } else {
            self.store.record_agent_worktree(
                materialization.clone(),
                "local".into(),
                checkout.path.clone(),
                checkout.origin,
                format!("refs/braid/reviews/{}/head", candidate.number),
                format!(
                    "braid-review-{}-r{}-i{}",
                    candidate.number,
                    checkout.responsibility_revision,
                    checkout.issue_assignment_revision
                ),
            )?;
        }
        let mut profile = self.spec.profile.clone();
        profile.workspace = Some(checkout.path);
        let instructions = review_system_prompt(
            self.config,
            &self.spec.profile,
            candidate.number,
            Some(&materialization.member_login),
        );
        self.start_materialized_assignment(
            &candidate,
            materialization,
            profile,
            instructions,
            rendered,
        )
        .await
    }
}
