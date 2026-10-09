use crate::objects::{LocalObjects, review::ReviewVerdict};
use anyhow::{Context as _, Result};
use clap::{Subcommand, ValueEnum};
use serde::Serialize;
use std::path::PathBuf;

#[derive(Subcommand)]
pub(super) enum ReviewCommand {
    /// 最近30个请求；结论保留冻结候选身份及当前适用性。
    List {
        pr: i64,
        #[arg(long)]
        json: bool,
    },
    View {
        pr: i64,
        request: i64,
        #[arg(long)]
        json: bool,
    },
    /// 只改变review执行责任，不改派PR实施者。
    /// 指派当前候选；已认领同职责旧名可自动保留有效现负责人，回执明确说明。新候选才改派。
    Assign {
        pr: i64,
        request: i64,
        #[arg(long)]
        assignee: String,
        #[arg(long)]
        json: bool,
    },
    /// 取得独立固定候选checkout，不切换当前工作区。
    Checkout {
        pr: i64,
        request: i64,
        #[arg(long)]
        json: bool,
    },
    /// 结论正文须说明代码判断、浏览器观察或不适用理由、证据入口及缺口。
    Conclude {
        pr: i64,
        request: i64,
        #[arg(long, value_enum)]
        verdict: Verdict,
        #[arg(long)]
        body_file: PathBuf,
        #[arg(long)]
        evidence: Vec<String>,
        #[arg(long)]
        json: bool,
    },
    Cancel {
        pr: i64,
        request: i64,
        #[arg(long)]
        reason: String,
        #[arg(long)]
        json: bool,
    },
}
#[derive(Clone, Copy, ValueEnum)]
pub(super) enum Verdict {
    Approved,
    ChangesRequested,
    Inconclusive,
}
impl From<Verdict> for ReviewVerdict {
    fn from(value: Verdict) -> Self {
        match value {
            Verdict::Approved => Self::Approved,
            Verdict::ChangesRequested => Self::ChangesRequested,
            Verdict::Inconclusive => Self::Inconclusive,
        }
    }
}
impl ReviewCommand {
    pub(super) fn is_read_only(&self) -> bool {
        matches!(self, Self::List { .. } | Self::View { .. })
    }
}
pub(super) fn print<T: Serialize>(result: &T, json: bool) -> Result<()> {
    let value = serde_json::to_value(result)?;
    if json {
        println!("{}", serde_json::to_string(&value)?);
    } else {
        println!("{}", serde_json::to_string_pretty(&value)?);
    }
    Ok(())
}
pub(super) fn execute(
    objects: &LocalObjects,
    turn: Option<&str>,
    command: ReviewCommand,
) -> Result<()> {
    match command {
        ReviewCommand::List { pr, json } => print(&objects.review_list(pr)?, json),
        ReviewCommand::View { pr, request, json } => {
            print(&objects.review_view(pr, request)?, json)
        }
        ReviewCommand::Assign { pr, request, assignee, json } => {
            print(&objects.assign_review(turn, pr, request, &assignee)?, json)
        }
        ReviewCommand::Checkout { pr, request, json } => {
            print(&objects.checkout_review(turn, pr, request)?, json)
        }
        ReviewCommand::Conclude { pr, request, verdict, body_file, evidence, json } => {
            let body = std::fs::read_to_string(&body_file)
                .with_context(|| format!("cannot read review body {}", body_file.display()))?;
            print(
                &objects.conclude_review(turn, pr, request, verdict.into(), &body, &evidence)?,
                json,
            )
        }
        ReviewCommand::Cancel { pr, request, reason, json } => {
            print(&objects.cancel_review(turn, pr, request, &reason)?, json)
        }
    }
}
