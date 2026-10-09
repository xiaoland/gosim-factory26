use crate::objects::LocalObjects;
use anyhow::Result;
use clap::Subcommand;

#[derive(Subcommand)]
pub(super) enum ExecutionCommand {
    /// 当前Issue责任的执行事实；工作区和证据路径可用于定向检查。
    Issue {
        id: i64,
        #[arg(long)]
        json: bool,
    },
    /// 当前PR实施者的执行事实；reviewer另用execution review查询。
    Pr {
        id: i64,
        #[arg(long)]
        json: bool,
    },
    /// 请求的候选、review责任及执行；不会创建checkout或启动验收。
    Review {
        pr: i64,
        request: i64,
        #[arg(long)]
        json: bool,
    },
}

pub(super) fn execute(objects: &LocalObjects, command: ExecutionCommand) -> Result<()> {
    let (value, json) = match command {
        ExecutionCommand::Issue { id, json } => (objects.execution_view("issue", id)?, json),
        ExecutionCommand::Pr { id, json } => (objects.execution_view("pr", id)?, json),
        ExecutionCommand::Review { pr, request, json } => {
            (objects.review_execution_view(pr, request)?, json)
        }
    };
    super::review::print(&value, json)
}
