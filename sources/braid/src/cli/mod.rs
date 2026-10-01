use crate::{
    context::CommentSnapshot,
    objects::{CommentResolution, IssueCreateResult, Item, ItemEditResult, LocalObjects, PrCreateResult},
};
use anyhow::{Context as _, Result, ensure};
use clap::{Args, Parser, Subcommand, ValueEnum};
use serde_json::{Map, Value, json};
use std::{fs, io::Read, path::PathBuf};

#[derive(Parser)]
#[command(name = "braid", version, about = "本地 Issue / PR 操作与 Agent 协作")]
struct Cli {
    /// 宿主运行目录；放在 issue/pr/comment 等子命令之前。Agent 环境自动绑定。
    #[arg(long = "state")]
    run_state: Option<PathBuf>,
    /// 宿主诊断用；Agent 身份由启动环境绑定。
    #[arg(long, global = true, conflicts_with = "external", hide = true)]
    writer_turn: Option<String>,
    #[arg(long, global = true, hide = true)]
    external: bool,
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// 宿主诊断：导出原始证据或从 OTLP 重建。
    Telemetry {
        #[command(subcommand)]
        command: TelemetryCommand,
    },
    Local {
        request: PathBuf,
        /// Host confirms the previous execution environment has stopped.
        #[arg(long)]
        offline_resume: bool,
    },
    Status {
        #[arg(long)]
        json: bool,
    },
    #[command(hide = true)]
    Profile {
        #[command(subcommand)]
        command: ProfileCommand,
    },
    /// 查询可指派对象（对应 GitHub 的 repository assignees 查询）。
    Assignee {
        #[command(subcommand)]
        command: AssigneeCommand,
    },
    Context {
        kind: String,
        id: i64,
        /// 按模型 token 窗口的 20% 预算展示实际分档投影；省略则完整读取。
        #[arg(long, value_parser = clap::value_parser!(u64).range(1024..))]
        window_tokens: Option<u64>,
    },
    Issue {
        #[command(subcommand)]
        command: IssueCommand,
    },
    Pr {
        #[command(subcommand)]
        command: PrCommand,
    },
    Comment {
        #[command(subcommand)]
        command: CommentCommand,
    },
}

#[derive(Subcommand)]
enum TelemetryCommand {
    RenderMarkdown,
    Decode {
        #[arg(long)]
        input: PathBuf,
    },
    Export {
        #[arg(long)]
        native_manifest: Option<PathBuf>,
        /// Include complete source bytes for offline reconstruction. Summary-only by default.
        #[arg(long)]
        portable: bool,
    },
    Reconstruct {
        #[arg(long)]
        input: PathBuf,
        #[arg(long)]
        output: PathBuf,
        #[arg(long)]
        run_id: Option<String>,
    },
}

#[derive(Subcommand)]
enum AssigneeCommand {
    /// 列出可用于指派工作的名称与职责。每次新指派产生独立负责人。
    List {
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand)]
enum ProfileCommand {
    List {
        #[command(flatten)]
        json: JsonFields,
    },
    View {
        id: String,
        #[command(flatten)]
        json: JsonFields,
    },
}

#[derive(Args)]
struct BodyArgs {
    /// 内联正文；编辑时替换完整正文，不是追加。多行正文优先使用 --body-file。
    #[arg(short = 'b', long, conflicts_with = "body_file")]
    body: Option<String>,
    /// 从文件读取完整正文；- 表示标准输入。编辑时替换原正文，空内容会清空正文。
    ///
    /// 先用 view ID --json body 读取正文，保存并编辑本地文件，检查内容后再单独写入。
    /// 例：braid issue edit 1 --body-file issue-1.md，然后 braid issue view 1 --json body。
    /// 写入时不使用临时生成正文的进程替换；CLI 无法获知上游 shell 命令是否失败。
    #[arg(short = 'F', long, value_name = "FILE", conflicts_with = "body")]
    body_file: Option<PathBuf>,
}

impl BodyArgs {
    fn read(self) -> Result<Option<String>> {
        if let Some(body) = self.body {
            return Ok(Some(body));
        }
        let Some(path) = self.body_file else { return Ok(None) };
        if path.as_os_str() == "-" {
            let mut body = String::new();
            std::io::stdin().read_to_string(&mut body)?;
            Ok(Some(body))
        } else {
            Ok(Some(fs::read_to_string(path)?))
        }
    }

    fn required(self) -> Result<String> {
        self.read()?.ok_or_else(|| anyhow::anyhow!("body is required; use --body or --body-file"))
    }
}

#[derive(Args)]
struct JsonFields {
    /// 输出全部字段，或用逗号选择本命令支持的字段；保存完整 JSON 后解析，不截行。
    #[arg(long, value_name = "FIELDS", num_args = 0..=1, default_missing_value = "all")]
    json: Option<String>,
}

#[derive(Clone, Copy, ValueEnum)]
enum IssueListState { Open, Closed, All }

#[derive(Clone, Copy, ValueEnum)]
enum PrListState { Open, Closed, Merged, All }

#[derive(Clone, Copy, ValueEnum)]
enum IssueCloseReason { Completed, #[value(name = "not planned")] NotPlanned, Duplicate }

impl IssueCloseReason {
    fn value(self) -> &'static str {
        match self { Self::Completed => "completed", Self::NotPlanned => "not planned", Self::Duplicate => "duplicate" }
    }
}

#[derive(Args)]
struct CommentArgs {
    #[command(flatten)]
    body: BodyArgs,
    /// 编辑当前成员在此工作项最后一条未隐藏、未删除的评论；已解决线程仍计入。
    #[arg(long, conflicts_with = "delete_last")]
    edit_last: bool,
    /// 删除当前成员在此工作项最后一条未隐藏、未删除的评论；已解决线程仍计入，必须同时提供 --yes。
    #[arg(long, conflicts_with = "edit_last")]
    delete_last: bool,
    /// 确认删除最后一条评论。
    #[arg(long, requires = "delete_last")]
    yes: bool,
}

#[derive(Subcommand)]
enum IssueCommand {
    /// 默认最多 30 项，按编号倒序；输出说明 has_more，JSON 数组的截断提示写入 stderr。
    List {
        #[arg(short = 's', long = "state", value_name = "STATE", value_enum, default_value = "open")]
        filter_state: IssueListState,
        #[arg(short = 'L', long, default_value_t = 30)]
        limit: usize,
        /// 当前具体成员名，例如从 view 的 assignees 读取。
        #[arg(short = 'a', long)]
        assignee: Option<String>,
        #[command(flatten)]
        json: JsonFields,
    },
    /// 读取完整正文；--json FIELDS 按字段取值。--timeline 仅支持裸 --json，不能同时 --comments。
    /// 核心字段：number,title,body,state,assignees,execution；comments 显式读取讨论。
    View {
        id: i64,
        #[arg(short = 'c', long)]
        comments: bool,
        #[arg(long, conflicts_with = "comments")]
        timeline: bool,
        /// 读取此全局序号之后的活动；从 0 开始，下一页使用输出的 next_after。
        #[arg(long, requires = "timeline", default_value_t = 0)]
        after: i64,
        /// 每页最多 100 条；输出会说明是否还有下一页。
        #[arg(long, requires = "timeline", default_value_t = 30)]
        limit: i64,
        #[command(flatten)]
        json: JsonFields,
    },
    /// 主动恢复此工作项的自动讨论通知。
    Subscribe { id: i64 },
    /// 退出自动讨论通知，直到主动 subscribe；单次 @ 仍送达但不会恢复关注。负责人不能退订。
    Unsubscribe { id: i64 },
    Create {
        #[arg(short = 't', long)]
        title: String,
        #[arg(long)]
        parent: Option<i64>,
        /// 从 braid assignee list 选择具体成员名；指派与联系使用同一个名字。
        #[arg(short = 'a', long, value_name = "MEMBER")]
        assignee: Option<String>,
        #[command(flatten)]
        body: BodyArgs,
        #[arg(long)]
        json: bool,
    },
    Edit {
        id: i64,
        #[arg(short = 't', long)]
        title: Option<String>,
        #[arg(long, conflicts_with = "remove_parent")]
        parent: Option<i64>,
        #[arg(long)]
        remove_parent: bool,
        /// 从 braid assignee list 选择具体成员名；改派时同时移除当前成员。
        #[arg(long, value_name = "MEMBER")]
        add_assignee: Option<String>,
        /// 移除当前具体成员的责任；空闲本身不需要取消指派。
        #[arg(long, value_name = "MEMBER")]
        remove_assignee: Option<String>,
        #[command(flatten)]
        body: BodyArgs,
        #[arg(long)]
        json: bool,
    },
    Comment {
        id: i64,
        #[arg(long)]
        reply_to: Option<i64>,
        #[command(flatten)]
        comment: CommentArgs,
        #[arg(long)]
        json: bool,
    },
    Close {
        id: i64,
        #[arg(long, value_enum)]
        reason: Option<IssueCloseReason>,
        /// 关闭时一并发表解释，与对象状态同事务；成功后再宣告关闭。不证明收件人已处理。
        #[arg(long)]
        comment: Option<String>,
        #[arg(long)]
        json: bool,
    },
    Reopen {
        id: i64,
        #[arg(long)]
        comment: Option<String>,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand)]
enum PrCommand {
    /// 默认最多 30 项，按编号倒序；输出说明 has_more，JSON 数组的截断提示写入 stderr。
    List {
        #[arg(short = 's', long = "state", value_name = "STATE", value_enum, default_value = "open")]
        filter_state: PrListState,
        #[arg(short = 'L', long, default_value_t = 30)]
        limit: usize,
        /// 当前具体成员名，例如从 view 的 assignees 读取。
        #[arg(short = 'a', long)]
        assignee: Option<String>,
        #[arg(short = 'B', long)]
        base: Option<String>,
        #[arg(short = 'H', long)]
        head: Option<String>,
        #[command(flatten)]
        json: JsonFields,
    },
    /// 读取完整正文；--json FIELDS 按字段取值。--timeline 仅支持裸 --json，不能同时 --comments。
    /// 核心字段：number,title,body,state,assignees,execution；comments 显式读取讨论。
    View {
        id: i64,
        #[arg(short = 'c', long)]
        comments: bool,
        #[arg(long, conflicts_with = "comments")]
        timeline: bool,
        /// 读取此全局序号之后的活动；从 0 开始，下一页使用输出的 next_after。
        #[arg(long, requires = "timeline", default_value_t = 0)]
        after: i64,
        /// 每页最多 100 条；输出会说明是否还有下一页。
        #[arg(long, requires = "timeline", default_value_t = 30)]
        limit: i64,
        #[command(flatten)]
        json: JsonFields,
    },
    /// 主动恢复此工作项的自动讨论通知。
    Subscribe { id: i64 },
    /// 退出自动讨论通知，直到主动 subscribe；单次 @ 仍送达但不会恢复关注。负责人不能退订。
    Unsubscribe { id: i64 },
    /// 创建 PR；采用已发布的 head，或从 base 新建实施分支。
    /// 正文 Closes #N（或 Fixes/Resolves）在合入 origin 默认分支后关闭该 Issue。
    /// 仅解析本仓库正文文字，不解析代码示例、commit message 或跨仓库引用。
    Create {
        /// 提供需求与讨论背景的 Issue，可用逗号指定多个；关联本身不声明合并后关闭。
        #[arg(long, value_delimiter = ',', required = true)]
        issue: Vec<i64>,
        #[arg(short = 't', long)]
        title: String,
        #[command(flatten)]
        body: BodyArgs,
        /// 可选重试键；同键只返回首次创建的 PR。
        #[arg(long)]
        request_id: Option<String>,
        /// 从 braid assignee list 选择具体成员名；指派与联系使用同一个名字。
        #[arg(short = 'a', long, value_name = "MEMBER")]
        assignee: Option<String>,
        /// 已发布在本次 origin 中的目标分支；省略时使用 delivery ref。
        #[arg(long, value_name = "BRANCH")]
        base: Option<String>,
        /// 已发布在本次 origin 中的源分支；省略时新建 PR 分支。
        #[arg(long, value_name = "BRANCH")]
        head: Option<String>,
        #[arg(long)]
        draft: bool,
        #[arg(long)]
        json: bool,
    },
    Edit {
        id: i64,
        #[arg(short = 't', long)]
        title: Option<String>,
        #[command(flatten)]
        body: BodyArgs,
        /// 从 braid assignee list 选择具体成员名；改派时同时移除当前成员。
        #[arg(long, value_name = "MEMBER")]
        add_assignee: Option<String>,
        /// 移除当前具体成员的责任；空闲本身不需要取消指派。
        #[arg(long, value_name = "MEMBER")]
        remove_assignee: Option<String>,
        #[arg(long)]
        json: bool,
    },
    Comment {
        id: i64,
        #[arg(long)]
        reply_to: Option<i64>,
        #[command(flatten)]
        comment: CommentArgs,
        #[arg(long)]
        json: bool,
    },
    /// 关联背景 Issue，不建立关闭意图；自动关闭须在 PR 正文声明 Closes #N 并合入默认分支。
    Link {
        id: i64,
        #[arg(long)]
        issue: i64,
        #[arg(long)]
        json: bool,
    },
    /// 移除背景关联；关闭意图由 PR 正文的 Closes/Fixes/Resolves 声明决定。
    Unlink {
        id: i64,
        #[arg(long)]
        issue: i64,
        #[arg(long)]
        json: bool,
    },
    /// 观察已发布 head 并切换 draft；不证明实现完成或他人已处理。
    Ready {
        id: i64,
        #[arg(long)]
        undo: bool,
    },
    /// 合并已发布的 head；回执区分引用更新、登记既有整合和无变化，不替代应用验收。
    /// 失败可已保存合并意图或更新 Git；保留具体错误，先 view 核对，不自动重试。
    Merge {
        id: i64,
        #[arg(long)]
        match_head_commit: Option<String>,
        /// 使用当前支持的本地 merge commit 策略；省略时保持原有行为。
        #[arg(long, conflicts_with_all = ["squash", "rebase"])]
        merge: bool,
        /// 尚未实现。
        #[arg(long, conflicts_with = "rebase")]
        squash: bool,
        /// 尚未实现。
        #[arg(long)]
        rebase: bool,
        /// 尚未实现。
        #[arg(long)]
        auto: bool,
        /// 尚未实现。
        #[arg(long)]
        disable_auto: bool,
    },
    Close {
        id: i64,
        #[arg(long)]
        comment: Option<String>,
        #[arg(long)]
        json: bool,
    },
    Reopen {
        id: i64,
        #[arg(long)]
        comment: Option<String>,
        #[arg(long)]
        json: bool,
    },
}

#[derive(Subcommand)]
enum CommentCommand {
    /// 精准读取一条评论；--thread 显式展开所属讨论。JSON 为数组，单条含一项。
    /// 常用字段：database_id,body,thread_root,reply_to,hidden_by,resolved,folded,reactions,deliveries。
    View {
        id: i64,
        #[arg(long)]
        thread: bool,
        /// 追溯自身或祖先隐藏及 resolved 历史；直接读取不会绕过祖先隐藏。
        #[arg(long)]
        include_hidden: bool,
        #[command(flatten)]
        json: JsonFields,
    },
    Edit {
        id: i64,
        #[command(flatten)]
        body: BodyArgs,
        #[arg(long)]
        json: bool,
    },
    /// 隐藏本条及其现有、未来后代正文；保留每条自身的隐藏选择。
    Hide {
        /// 评论 ID；可一次提供多个，例如 hide 8 9 --reason '已整理'。
        #[arg(required = true, num_args = 1..)]
        ids: Vec<i64>,
        #[arg(long)]
        reason: Option<String>,
        #[arg(long)]
        json: bool,
    },
    /// 取消本条自身隐藏；后代自身或其它祖先的隐藏仍生效。
    Unhide {
        id: i64,
        #[arg(long)]
        json: bool,
    },
    /// 删除指定正文，保留墓碑和回复；正文不可恢复。
    Delete {
        id: i64,
        #[arg(long)]
        json: bool,
    },
    /// 整理已结束的整段讨论；先读取 comment view ROOT --thread 了解范围。
    Resolve {
        /// 仅接受讨论根 ID；折叠整串当前前缀，新回复可见。回复 ID 整批拒绝；局部整理用 hide。
        #[arg(required = true, num_args = 1..)]
        ids: Vec<i64>,
        #[arg(long)]
        json: bool,
    },
    Unresolve {
        /// 仅接受讨论根 ID；展开整串前缀，仍保留独立 hide/delete。
        #[arg(required = true, num_args = 1..)]
        ids: Vec<i64>,
        #[arg(long)]
        json: bool,
    },
    Reaction {
        #[command(subcommand)]
        command: ReactionCommand,
    },
}

#[derive(Subcommand)]
enum ReactionCommand {
    Add { id: i64, expression: String, #[arg(long)] json: bool },
    Remove { id: i64, expression: String, #[arg(long)] json: bool },
}

fn output(value: impl serde::Serialize) -> Result<()> {
    println!("{}", serde_json::to_string_pretty(&value)?);
    Ok(())
}

const ITEM_FIELDS: &[&str] = &[
    "id",
    "number",
    "kind",
    "title",
    "body",
    "state",
    "reason",
    "stateReason",
    "head_ref",
    "headRefName",
    "base_ref",
    "baseRefName",
    "draft",
    "isDraft",
    "ready_commit",
    "revision",
    "parent",
    "assignees",
    "execution",
];

fn public_item_fields(map: &mut Map<String, Value>) {
    for (public, legacy) in [("number", "id"), ("stateReason", "reason"), ("isDraft", "draft")] {
        map.insert(public.into(), map[legacy].clone());
    }
    for (public, legacy) in [("headRefName", "head_ref"), ("baseRefName", "base_ref")] {
        let value = map[legacy].as_str().map(|name| name.strip_prefix("refs/heads/").unwrap_or(name));
        map.insert(public.into(), value.into());
    }
}

fn selected_fields(fields: &str, comments: bool) -> Result<Vec<&str>> {
    if fields == "all" {
        let mut fields = ITEM_FIELDS.to_vec();
        if comments {
            fields.push("comments");
        }
        return Ok(fields);
    }
    let fields = fields.split(',').map(str::trim).collect::<Vec<_>>();
    for field in &fields {
        ensure!(!field.is_empty(), "JSON field list contains an empty field");
        ensure!(
            ITEM_FIELDS.contains(field) || (comments && *field == "comments"),
            "unknown JSON field `{field}`; available fields: {}",
            ITEM_FIELDS
                .iter()
                .copied()
                .chain(comments.then_some("comments"))
                .collect::<Vec<_>>()
                .join(",")
        );
    }
    Ok(fields)
}

fn comment_json(comment: &CommentSnapshot) -> Result<Value> {
    let Value::Object(mut value) = serde_json::to_value(comment)? else { unreachable!() };
    let lifecycle = if comment.deleted {
        "deleted"
    } else if comment.minimized {
        "hidden"
    } else {
        "visible"
    };
    value.insert("lifecycle".into(), lifecycle.into());
    if comment.body.is_none() && !comment.deleted {
        value.insert("read_body_with".into(), format!("braid comment view {} --include-hidden", comment.database_id).into());
    }
    Ok(Value::Object(value))
}

fn json_item(item: &Item, fields: &str, comments: Option<&[CommentSnapshot]>) -> Result<Value> {
    let Value::Object(mut all) = serde_json::to_value(item)? else { unreachable!() };
    public_item_fields(&mut all);
    let mut selected = Map::new();
    for field in selected_fields(fields, comments.is_some())? {
        let value = if field == "comments" {
            Value::Array(
                comments
                    .unwrap_or_default()
                    .iter()
                    .map(comment_json)
                    .collect::<Result<Vec<_>>>()?,
            )
        } else {
            all[field].clone()
        };
        selected.insert(field.into(), value);
    }
    Ok(Value::Object(selected))
}

fn print_item(
    item: &Item,
    fields: Option<&str>,
    comments: Option<&[CommentSnapshot]>,
) -> Result<()> {
    if let Some(fields) = fields {
        return output(json_item(item, fields, comments)?);
    }
    let label = if item.kind == "pr" { "PR" } else { "Issue" };
    let draft = if item.kind == "pr" && item.draft { " - draft" } else { "" };
    let assignee = item.assignees.first().map(|actor| format!("@{}", actor.login)).unwrap_or_else(|| "未指派".into());
    println!("# {label} {} - {} - {}{draft} - {assignee}", item.id, item.title, item.state);
    if let Some(reason) = &item.reason {
        println!("reason: {reason}");
    }
    if let Some(head) = &item.head_ref {
        println!("head: {head}");
    }
    if let Some(commit) = &item.ready_commit {
        println!("last ready observation: {commit}");
    }
    if let Some(fact) = &item.execution {
        println!("最近执行尝试：{} 于 {}；{}（错误详情：braid {} view {} --json execution_error）", fact.outcome, fact.at, fact.summary, item.kind, item.id);
    }
    if !item.body.is_empty() {
        let mut text = String::from("\n## Description\n");
        crate::context::fenced_body(&mut text, &item.body);
        print!("{text}");
    }
    print_comments(comments.unwrap_or_default());
    Ok(())
}

const ISSUE_VIEW_FIELDS: &[&str] = &["parent_issue", "sub_issues", "associated_prs", "subscriptions", "execution_error"];
const PR_VIEW_FIELDS: &[&str] = &["associated_issues", "closing_issues", "base_commit", "head_commit", "base_error", "head_error", "merge_commit", "subscriptions", "execution_error", "assignee_activity", "assignee_deliveries", "headRefOid", "baseRefOid"];
const COMMENT_FIELDS: &[&str] = &["node_id", "database_id", "repository", "work_item_number", "author", "created_at", "updated_at", "body", "minimized", "minimized_reason", "hidden_by", "hidden_by_reason", "pinned", "deleted", "reply_to", "thread_root", "resolved", "folded", "reactions", "lifecycle", "read_body_with", "deliveries"];

fn view_fields<'a>(kind: &str, fields: &'a str) -> Result<Vec<&'a str>> {
    let extra = if kind == "pr" { PR_VIEW_FIELDS } else { ISSUE_VIEW_FIELDS };
    if fields == "all" { return Ok(ITEM_FIELDS.iter().copied().chain(extra.iter().copied()).chain(["comments"]).collect()); }
    let fields = fields.split(',').map(str::trim).collect::<Vec<_>>();
    for field in &fields {
        ensure!(ITEM_FIELDS.contains(field) || extra.contains(field) || *field == "comments", "unknown {kind} view field {field:?}; available fields: {}", ITEM_FIELDS.iter().chain(extra).copied().chain(["comments"]).collect::<Vec<_>>().join(","));
    }
    Ok(fields)
}

fn read_view(objects: &LocalObjects, kind: &str, id: i64, fields: Option<&str>, comments: bool, timeline: bool, after: i64, limit: i64) -> Result<()> {
    if timeline {
        ensure!(!comments, "--timeline conflicts with --comments");
        ensure!(fields.is_none_or(|fields| fields == "all"), "--timeline supports bare --json only; field selection applies to object view");
        return print_timeline(objects, kind, id, after, limit, fields.is_some());
    }
    let selected = fields.map(|fields| view_fields(kind, fields)).transpose()?;
    if comments && let Some(selected) = &selected {
        ensure!(selected.contains(&"comments"), "--comments requires comments in the JSON field selection; use --json comments or omit --comments");
    }
    let wants = |field| selected.as_ref().is_none_or(|fields| fields.contains(&field));
    let include_comments = if selected.is_some() { wants("comments") } else { comments };
    let item = objects.read_for_cli(kind, id, wants("body"), wants("execution"))?;
    let comments = include_comments.then(|| objects.comments_for(kind, id)).transpose()?;
    print_view(objects, &item, selected.as_deref(), comments.as_deref())
}

fn print_view(objects: &LocalObjects, item: &Item, fields: Option<&[&str]>, comments: Option<&[CommentSnapshot]>) -> Result<()> {
    let detail_fields = fields.map(|fields| fields.iter().map(|field| match *field { "headRefOid" => "head_commit", "baseRefOid" => "base_commit", field => field }).collect::<Vec<_>>());
    let details = if fields.is_none() { objects.view_details(&item.kind, item.id)? } else { objects.view_details_for_fields(&item.kind, item.id, detail_fields.as_deref())? };
    if let Some(fields) = fields {
        let mut all = serde_json::to_value(item)?;
        let map = all.as_object_mut().expect("item is an object");
        map.extend(details.as_object().expect("details are an object").clone());
        public_item_fields(map);
        if item.kind == "pr" {
            map.insert("headRefOid".into(), map.get("head_commit").cloned().unwrap_or(Value::Null));
            map.insert("baseRefOid".into(), map.get("base_commit").cloned().unwrap_or(Value::Null));
        }
        if let Some(comments) = comments { map.insert("comments".into(), Value::Array(comments.iter().map(comment_json).collect::<Result<Vec<_>>>()?)); }
        let selected = fields.iter().map(|field| ((*field).to_owned(), map[*field].clone())).collect::<Map<_, _>>();
        return output(selected);
    }
    print_item(item, None, comments)?;
    if item.kind == "pr" {
        for prefix in ["base", "head"] {
            let reference = details[format!("{prefix}_ref")].as_str().unwrap_or("missing");
            let commit = details[format!("{prefix}_commit")].as_str().unwrap_or("unavailable");
            println!("{prefix}: {reference} ({commit})");
        }
        if let Some(activity) = details["assignee_activity"].as_object() {
            let assignment = activity["assignment"].as_str().unwrap_or("unknown");
            let agent = activity["agent"].as_str().unwrap_or("unknown");
            let session = activity["session"].as_str().unwrap_or("none");
            let turn = activity["turn"].as_str().unwrap_or("none");
            let status = if turn == "running" { "正在执行" }
                else if turn == "starting" { "正在投递" }
                else if assignment == "blocked" || agent == "blocked" || session == "blocked" { "执行受阻" }
                else if matches!(session, "idle" | "sleeping") { "等待调度" }
                else if session == "none" && matches!(assignment, "materializing" | "active") { "尚未启动" }
                else { "状态待确认" };
            if let Some(started) = activity["turn_started_at"].as_str() {
                println!("Braid 观察到的负责人执行状态：{status}（本轮开始于 {started}）");
            } else {
                println!("Braid 观察到的负责人执行状态：{status}");
            }
        }
        if let Some(deliveries) = details["assignee_deliveries"].as_array() {
            for receipt in deliveries {
                let status = match receipt["status"].as_str() {
                    Some("delivered") => "已送达（不代表已处理）",
                    Some("queued") => "待投递",
                    Some("unreachable") => "未送达",
                    _ => "状态待确认",
                };
                println!("负责人评论投递：#{} {status}", receipt["comment"]);
            }
        }
        println!("head 仅是已发布提交；Braid 未观测未提交或未推送的工作。");
        if let Some(commit) = details["merge_commit"].as_str() { println!("merged: {commit}"); }
        if let Some(issues) = details["closing_issues"].as_array() {
            for issue in issues { println!("closing issue: #{issue}"); }
        }
    }
    for (field,label) in [("parent_issue","parent"),("sub_issues","sub-issue"),("associated_prs","PR"),("associated_issues","issue")] {
        let values = if details[field].is_array() { details[field].as_array().cloned().unwrap_or_default() } else if details[field].is_object() { vec![details[field].clone()] } else { Vec::new() };
        for value in values {
            println!("{label}: #{} [{}] {}", value["number"].as_u64().unwrap_or_default(), value["state"].as_str().unwrap_or("unknown"), value["title"].as_str().unwrap_or(""));
        }
    }
    if let Some(activity) = details["activity"].as_array() {
        for entry in activity { println!("{} {}", entry["at"].as_str().unwrap_or(""), entry["message"].as_str().unwrap_or("")); }
    }
    Ok(())
}
fn print_timeline(objects: &LocalObjects, kind: &str, id: i64, after: i64, limit: i64, as_json: bool) -> Result<()> {
    let (rows, has_more) = objects.timeline(kind, id, after, limit)?;
    let next_after = rows.last().and_then(|row| row["ordinal"].as_i64());
    if as_json { return output(json!({"items":rows,"after":after,"limit":limit,"has_more":has_more,"next_after":has_more.then_some(next_after).flatten()})); }
    println!("协作历史：{} 条；{}。", rows.len(), if has_more { "后面还有记录" } else { "已到末尾" });
    for row in rows {
        let author = row["author"].as_str().filter(|value| !value.is_empty())
            .map(|value| format!("@{value}")).unwrap_or_else(|| "未记录成员".to_owned());
        let action = row["action"].as_str().unwrap_or("");
        let detail = row["detail"].as_str().unwrap_or("");
        if let Some(comment) = row["comment"].as_i64() {
            println!("Comment {comment} · {author} · {action}");
            if !detail.is_empty() && detail != format!("comment #{comment}") {
                println!("  {detail}");
            }
            println!("  braid comment view {comment}");
        } else {
            println!("{author} {action} {detail}");
        }
    }
    if has_more && let Some(next_after) = next_after {
        println!("下一页：braid {kind} view {id} --timeline --after {next_after} --limit {limit}（每页最多 100 条）");
    }
    Ok(())
}

fn print_comments(comments: &[CommentSnapshot]) {
    let mut text = String::new();
    crate::context::render_comments(&mut text, comments, 3, false);
    print!("{text}");
}

fn mutation_json(id: i64, mut value: Value) -> Result<()> {
    let map = value.as_object_mut().expect("receipt is an object");
    map.remove("id");
    map.remove("number");
    let remaining = serde_json::to_string(map)?;
    println!("{{\"id\":{id},\"number\":{id},{}", &remaining[1..]);
    Ok(())
}

fn print_change(kind: &str, id: i64, action: &str, changed: bool, as_json: bool) -> Result<()> {
    let effect = match action {
        "hidden" => "本条及现有、未来后代正文隐藏，各条自身状态保留",
        "unhidden" => "仅取消本条自身隐藏，后代自身或其它祖先隐藏及讨论折叠保留",
        "deleted" => "正文不可恢复，回复保留",
        _ => "",
    };
    if as_json { return mutation_json(id, json!({"kind":kind,"action":action,"changed":changed,"effect":effect})); }
    println!("{kind} #{id}：{action}；{}{}", if changed { "已改变" } else { "无变化" }, if effect.is_empty() { String::new() } else { format!("；{effect}") });
    Ok(())
}

fn print_comment_resolution(results: &[CommentResolution], resolved: bool, as_json: bool) -> Result<()> {
    if as_json { return output(results); }
    for result in results {
        let cutoff = result.resolved_through.map_or_else(|| "无（已展开）".to_owned(), |id| format!("评论 #{id}"));
        let previous = result.previous_resolved_through.map_or_else(|| "无".to_owned(), |id| format!("评论 #{id}"));
        println!("讨论根 #{}：{}；折叠截至 {cutoff}（此前 {previous}）；本次前缀范围改变 {} 条记录；{}；新回复可见，独立 hide/delete 保留", result.thread_root, if resolved { "resolve" } else { "unresolve" }, result.affected_comments, if result.changed { "已改变" } else { "无变化" });
    }
    Ok(())
}

fn print_list(items: &[Item], has_more: bool, limit: usize, fields: Option<&str>) -> Result<()> {
    if let Some(fields) = fields {
        selected_fields(fields, false)?;
        output(items.iter().map(|item| json_item(item, fields, None)).collect::<Result<Vec<_>>>()?)?;
        eprintln!("list：返回 {} 项，limit={limit}，has_more={has_more}{}", items.len(), if has_more { "；增大 --limit 读取更多" } else { "" });
    } else {
        for item in items { println!("#{}\t{}\t{}\t{}", item.id, item.state, item.assignees.first().map_or("未指派".into(), |actor| format!("@{}", actor.login)), item.title); }
        println!("list：返回 {} 项，limit={limit}，has_more={has_more}{}", items.len(), if has_more { "；增大 --limit 读取更多" } else { "" });
    }
    Ok(())
}

fn print_issue_created(result: &IssueCreateResult, as_json: bool) -> Result<()> {
    if as_json { return mutation_json(result.id, json!({"kind":"issue","action":"created","changed":true,"assignees":result.assignees})); }
    println!("issue #{}：已创建；负责人 {}", result.id, result.assignees.first().map_or("未指派".into(), |actor| format!("@{}", actor.login)));
    Ok(())
}

fn print_edit(kind: &str, id: i64, result: &ItemEditResult, as_json: bool) -> Result<()> {
    if as_json { return mutation_json(id, json!({"kind":kind,"action":"edited","changed":!result.changed_fields.is_empty(),"changed_fields":result.changed_fields,"assignees":result.assignees})); }
    println!("{kind} #{id}：{}；负责人 {}", if result.changed_fields.is_empty() { "无变化".into() } else { format!("已修改 {}", result.changed_fields.join(",")) }, result.assignees.first().map_or("未指派".into(), |actor| format!("@{}", actor.login)));
    Ok(())
}

fn write_comment(objects: &LocalObjects, turn: Option<&str>, kind: &str, id: i64, reply_to: Option<i64>, comment: CommentArgs, as_json: bool) -> Result<()> {
    let CommentArgs { body, edit_last, delete_last, yes } = comment;
    if edit_last || delete_last {
        ensure!(reply_to.is_none(), "--reply-to cannot be combined with last-comment operations");
        if delete_last {
            ensure!(yes, "--delete-last requires --yes");
            ensure!(body.body.is_none() && body.body_file.is_none(), "--delete-last does not accept a body");
        }
        let last = objects.last_comment_by_current_member(turn, kind, id)?;
        let (action, changed) = if delete_last { ("deleted", objects.comment_lifecycle(turn, last, "delete")?) } else { ("edited", objects.edit_comment(turn, last, &body.required()?)?) };
        print_change("comment", last, action, changed, as_json)
    } else {
        let comment = objects.comment_reply(turn, kind, id, &body.required()?, reply_to)?;
        if as_json { return mutation_json(comment, json!({"kind":"comment","action":"created","changed":true,"work_item_kind":kind,"work_item_number":id,"reply_to":reply_to})); }
        println!("comment #{comment}：已创建于 {kind} #{id}；不代表收件人已处理。投递详情：braid comment view {comment} --json deliveries");
        Ok(())
    }
}

fn print_lifecycle_result(kind: &str, id: i64, reopen: bool, changed: bool, comment: Option<i64>, as_json: bool) -> Result<()> {
    let state = if reopen { "OPEN" } else { "CLOSED" };
    if as_json { return mutation_json(id, json!({"kind":kind,"action":if reopen { "reopened" } else { "closed" },"state":state,"changed":changed,"comment":comment})); }
    println!("{kind} #{id}：{state}；{}（仅记录对象状态）", if changed { "已改变" } else { "无变化" });
    if let Some(comment) = comment { println!("comment #{comment}：已创建；不代表收件人已处理"); }
    Ok(())
}

fn print_message_receipts(comment_id: i64, deliveries: &[Value]) {
    if deliveries.is_empty() { return }
    // Keep transport acknowledgements outside authored text and task outcomes.
    println!("\n消息投递回执 — 评论 #{comment_id}（仅表示评论输入的接收状态）");
    for delivery in deliveries {
        let status = match delivery["status"].as_str().unwrap_or("") {
            "delivered" => "会话已接受评论输入 (delivered)",
            "queued" => "评论等待投递 (queued)",
            "unreachable" => "评论无法送达 (unreachable)",
            other => other,
        };
        println!("收件人 @{}: {status}{}", delivery["recipient"].as_str().unwrap_or(""), delivery["reason"].as_str().map_or(String::new(), |reason| format!(" ({reason})")));
    }
}

fn print_pr_created(result: &PrCreateResult, as_json: bool) -> Result<()> {
    if as_json {
        let mut value = serde_json::to_value(result)?;
        value["kind"] = "pr".into();
        value["action"] = if result.created { "created" } else { "reused" }.into();
        value["changed"] = result.created.into();
        return mutation_json(result.id, value);
    }
    println!("pr #{}：{}；head {} ({})；base {} ({})；负责人 {}", result.id, if result.created { "已创建" } else { "复用已有 request-id，无变化" }, result.head_ref, result.head_commit, result.base_ref, result.base_commit, result.assignees.first().map_or("未指派".into(), |actor| format!("@{}", actor.login)));
    Ok(())
}

#[allow(clippy::too_many_lines)]
pub async fn run() -> Result<()> {
    let Cli { run_state: state, writer_turn, external, command } = Cli::parse();
    if let Command::Local { request, offline_resume } = &command {
        return crate::local::run(request, *offline_resume).await;
    }
    if let Command::Telemetry { command } = command {
        ensure!(
            std::env::var("BRAID_AGENT_RUNTIME").as_deref() != Ok("1"),
            "遥测导出与重建只供宿主诊断使用"
        );
        return match command {
            TelemetryCommand::RenderMarkdown => {
                let texts: Vec<String> = serde_json::from_reader(std::io::stdin().lock())?;
                output(crate::evidence::render_markdown(&texts))
            }
            TelemetryCommand::Decode { input } => output(crate::evidence::decode(&input)?),
            TelemetryCommand::Export { native_manifest, portable } => {
                let state = state.context("--state is required for telemetry export")?;
                output(crate::telemetry::export(state, native_manifest, portable).await?)
            }
            TelemetryCommand::Reconstruct { input, output: destination, run_id } => {
                crate::telemetry::local_logging();
                output(crate::evidence::reconstruct(&input, &destination, run_id.as_deref())?)
            }
        };
    }
    crate::telemetry::local_logging();
    let agent_runtime = std::env::var("BRAID_AGENT_RUNTIME").is_ok_and(|value| value == "1");
    ensure!(
        !agent_runtime || (state.is_none() && writer_turn.is_none() && !external),
        "当前 Agent 环境已自动绑定执行身份，不接受 --state、--writer-turn 或 --external"
    );
    let (state, binding_id) = if agent_runtime {
        (std::env::var_os("BRAID_STATE").map(PathBuf::from).context("BRAID_STATE is missing")?,
         Some(std::env::var("BRAID_CLI_BINDING_ID").context("BRAID_CLI_BINDING_ID is missing")?))
    } else {
        (state.context("--state is required")?, None)
    };
    let objects = if let Some(binding_id) = binding_id {
        LocalObjects::new(state).with_cli_binding(binding_id)
    } else {
        LocalObjects::new(state)
    };
    let reading = matches!(
        &command,
        Command::Status { .. }
            | Command::Context { .. }
            | Command::Assignee { .. }
            | Command::Issue { command: IssueCommand::List { .. } | IssueCommand::View { .. } }
            | Command::Pr { command: PrCommand::List { .. } | PrCommand::View { .. } }
            | Command::Comment { command: CommentCommand::View { .. } }
    );
    ensure!(
        reading || writer_turn.is_some() || external || agent_runtime,
        "此操作需要当前 Agent 的有效执行身份，或由宿主使用 --external"
    );
    let turn = writer_turn.as_deref();
    match command {
        Command::Local { .. } | Command::Telemetry { .. } => unreachable!(),
        Command::Status { json: as_json } => {
            if agent_runtime {
                let items = objects
                    .list("issue")?
                    .into_iter()
                    .chain(objects.list("pr")?)
                    .collect::<Vec<_>>();
                if as_json {
                    let items = items
                        .iter()
                        .map(|item| json_item(item, "kind,id,number,title,state,assignees,execution", None))
                        .collect::<Result<Vec<_>>>()?;
                    output(json!({"items": items}))
                } else {
                    for item in items {
                        let assignee = item
                            .assignees
                            .first()
                            .map_or_else(|| "未指派".into(), |actor| format!("@{}", actor.login));
                        println!(
                            "{} #{}\t{}\t{}\t{}",
                            if item.kind == "pr" { "PR" } else { "Issue" },
                            item.id,
                            item.state,
                            assignee,
                            item.title
                        );
                        if let Some(fact) = &item.execution {
                            println!("  最近执行尝试：{} 于 {}；{}", fact.outcome, fact.at, fact.summary);
                        }
                    }
                    Ok(())
                }
            } else {
                let status = crate::local::status(&objects)?;
                if as_json {
                    output(status)
                } else {
                    let items = status["items"].as_array().map_or(0, Vec::len);
                    println!("items: {items}");
                    for key in
                        ["active_turns", "pending_batches", "pending_events", "pending_resets"]
                    {
                        println!("{key}: {}", status[key]);
                    }
                    Ok(())
                }
            }
        }
        Command::Profile { command } => {
            ensure!(!agent_runtime, "Agent 运行环境不提供内部配置诊断");
            match command {
                ProfileCommand::List { json } => {
                    let profiles = objects.profiles()?;
                    if json.json.is_some() {
                        output(profiles)
                    } else {
                        for profile in profiles {
                            println!("{}\t{}", profile["id"], profile["adapter_type"]);
                        }
                        Ok(())
                    }
                }
                ProfileCommand::View { id, json } => {
                    let profile = objects.profile(&id)?;
                    if json.json.is_some() { output(profile) } else { output(profile) }
                }
            }
        }
        Command::Assignee { command: AssigneeCommand::List { json } } => {
            let directory = objects.assignee_directory()?;
            if json { return output(directory); }
            for member in directory {
                println!("{}：{}", member["login"].as_str().expect("login"), member["description"].as_str().expect("description"));
            }
            Ok(())
        }
        Command::Context { kind, id, window_tokens } => {
            let context = objects.canonical(&kind, id)?;
            let rendered = if let Some(window) = window_tokens {
                crate::context::render_budgeted(&context, 0.8, usize::MAX, usize::try_from(window)?)
            } else {
                crate::context::render_complete(&context, 0.8, usize::MAX)
            };
            eprintln!("context: {:?}, estimated_tokens={}", rendered.tier, rendered.estimated_tokens);
            println!("{}", rendered.text);
            Ok(())
        }
        Command::Issue { command } => match command {
            IssueCommand::List { filter_state, limit, assignee, json } => {
                let state = match filter_state { IssueListState::Open => "open", IssueListState::Closed => "closed", IssueListState::All => "all" };
                let fields = json.json.as_deref().map(|fields| selected_fields(fields, false)).transpose()?;
                let wants = |field| fields.as_ref().is_some_and(|fields| fields.contains(&field));
                let (items, has_more) = objects.list_for_cli("issue", state, limit, assignee.as_deref(), None, None, wants("body"), wants("execution"))?;
                print_list(&items, has_more, limit, json.json.as_deref())
            }
            IssueCommand::View { id, comments, timeline, after, limit, json } => {
                read_view(&objects, "issue", id, json.json.as_deref(), comments, timeline, after, limit)
            }
            IssueCommand::Subscribe { id } => {
                objects.set_subscription(turn, "issue", id, true)?;
                println!("issue #{id}：已恢复自动讨论通知");
                Ok(())
            },
            IssueCommand::Unsubscribe { id } => {
                objects.set_subscription(turn, "issue", id, false)?;
                println!("issue #{id}：已退出自动讨论通知；单次 @ 仍送达，主动 subscribe 才恢复关注");
                Ok(())
            },
            IssueCommand::Create { title, body, parent, assignee, json } => {
                let result = objects.create_issue_with_parent_and_profile(
                    turn,
                    &title,
                    &body.required()?,
                    parent,
                    assignee.as_deref(),
                )?;
                print_issue_created(&result, json)
            }
            IssueCommand::Edit {
                id,
                title,
                body,
                parent,
                remove_parent,
                add_assignee,
                remove_assignee,
                json,
            } => {
                let body = body.read()?;
                let result = objects.edit_with_parent_and_assignees(
                    turn,
                    "issue",
                    id,
                    title.as_deref(),
                    body.as_deref(),
                    if remove_parent { Some(None) } else { parent.map(Some) },
                    add_assignee.as_deref(),
                    remove_assignee.as_deref(),
                )?;
                print_edit("issue", id, &result, json)
            }
            IssueCommand::Comment { id, comment, reply_to, json } => {
                write_comment(&objects, turn, "issue", id, reply_to, comment, json)
            }
            IssueCommand::Close { id, reason, comment, json } => {
                let (changed, posted) = objects.lifecycle_with_comment(turn, "issue", id, false, reason.map(IssueCloseReason::value), comment.as_deref())?;
                print_lifecycle_result("issue", id, false, changed, posted, json)
            }
            IssueCommand::Reopen { id, comment, json } => {
                let (changed, posted) = objects.lifecycle_with_comment(turn, "issue", id, true, None, comment.as_deref())?;
                print_lifecycle_result("issue", id, true, changed, posted, json)
            },
        },
        Command::Pr { command } => match command {
            PrCommand::List { filter_state, limit, assignee, base, head, json } => {
                let state = match filter_state { PrListState::Open => "open", PrListState::Closed => "closed", PrListState::Merged => "merged", PrListState::All => "all" };
                let fields = json.json.as_deref().map(|fields| selected_fields(fields, false)).transpose()?;
                let wants = |field| fields.as_ref().is_some_and(|fields| fields.contains(&field));
                let (items, has_more) = objects.list_for_cli("pr", state, limit, assignee.as_deref(), base.as_deref(), head.as_deref(), wants("body"), wants("execution"))?;
                print_list(&items, has_more, limit, json.json.as_deref())
            },
            PrCommand::View { id, comments, timeline, after, limit, json } => {
                read_view(&objects, "pr", id, json.json.as_deref(), comments, timeline, after, limit)
            }
            PrCommand::Subscribe { id } => {
                objects.set_subscription(turn, "pr", id, true)?;
                println!("pr #{id}：已恢复自动讨论通知");
                Ok(())
            },
            PrCommand::Unsubscribe { id } => {
                objects.set_subscription(turn, "pr", id, false)?;
                println!("pr #{id}：已退出自动讨论通知；单次 @ 仍送达，主动 subscribe 才恢复关注");
                Ok(())
            },
            PrCommand::Create { issue, title, body, request_id, assignee, base, head, draft, json } => {
                let result = objects.create_pr_with_options(
                    turn,
                    &issue,
                    &title,
                    &body.required()?,
                    request_id.as_deref(),
                    assignee.as_deref(),
                    base.as_deref(),
                    head.as_deref(),
                    draft,
                )?;
                print_pr_created(&result, json)
            }
            PrCommand::Edit { id, title, body, add_assignee, remove_assignee, json } => {
                let body = body.read()?;
                let result = objects.edit_with_parent_and_assignees(
                    turn,
                    "pr",
                    id,
                    title.as_deref(),
                    body.as_deref(),
                    None,
                    add_assignee.as_deref(),
                    remove_assignee.as_deref(),
                )?;
                print_edit("pr", id, &result, json)
            }
            PrCommand::Comment { id, comment, reply_to, json } => {
                write_comment(&objects, turn, "pr", id, reply_to, comment, json)
            }
            PrCommand::Link { id, issue, json } => {
                let changed = objects.link(turn, id, issue, true)?;
                if json { mutation_json(id, json!({"kind":"pr","action":"linked","issue":issue,"changed":changed})) }
                else { println!("pr #{id}：Issue #{issue} 背景关联；{}；关联不声明合并后关闭", if changed { "已改变" } else { "无变化" }); Ok(()) }
            },
            PrCommand::Unlink { id, issue, json } => {
                let changed = objects.link(turn, id, issue, false)?;
                if json { mutation_json(id, json!({"kind":"pr","action":"unlinked","issue":issue,"changed":changed})) }
                else { println!("pr #{id}：Issue #{issue} 背景关联；{}；正文关闭意图仍由 Closes/Fixes/Resolves 决定", if changed { "已移除" } else { "无变化" }); Ok(()) }
            },
            PrCommand::Ready { id, undo } => {
                let result = objects.ready_with_undo(turn, id, undo)?;
                let mut value = serde_json::to_value(result)?;
                value["kind"] = "pr".into();
                value["state"] = "OPEN".into();
                value["effect"] = "仅观察已发布 head；不证明实现完成或收件人已处理".into();
                mutation_json(id, value)
            },
            PrCommand::Merge { id, match_head_commit, merge: _, squash, rebase, auto, disable_auto } => {
                ensure!(!squash && !rebase && !auto && !disable_auto, "当前只支持即时本地 merge；--squash、--rebase、--auto 和 --disable-auto 尚未实现");
                let result = objects.merge_with_match(turn, id, match_head_commit.as_deref())?;
                let mut value = serde_json::to_value(result)?;
                value["kind"] = "pr".into();
                value["state"] = "MERGED".into();
                value["effect"] = "已记录整合；应用验收由调用者判断".into();
                mutation_json(id, value)
            }
            PrCommand::Close { id, comment, json } => {
                let (changed, posted) = objects.lifecycle_with_comment(turn, "pr", id, false, None, comment.as_deref())?;
                print_lifecycle_result("pr", id, false, changed, posted, json)
            }
            PrCommand::Reopen { id, comment, json } => {
                let (changed, posted) = objects.lifecycle_with_comment(turn, "pr", id, true, None, comment.as_deref())?;
                print_lifecycle_result("pr", id, true, changed, posted, json)
            },
        },
        Command::Comment { command } => match command {
            CommentCommand::View { id, thread, include_hidden, json } => {
                let selected = json.json.as_deref().map(|fields| {
                    if fields == "all" { return Ok(COMMENT_FIELDS.to_vec()); }
                    let selected = fields.split(',').map(str::trim).collect::<Vec<_>>();
                    for field in &selected { ensure!(COMMENT_FIELDS.contains(field), "unknown comment view field {field:?}; available fields: {}", COMMENT_FIELDS.join(",")); }
                    Ok(selected)
                }).transpose()?;
                let wants = |field| selected.as_ref().is_none_or(|fields| fields.contains(&field));
                let comments = objects.view_comment_for_fields(id, thread, include_hidden, wants("body") || wants("read_body_with"), wants("reactions"))?;
                if let Some(selected) = selected {
                    output(comments.iter().map(|comment| {
                        let mut value = comment_json(comment)?;
                        let id: i64 = comment.database_id.parse()?;
                        if selected.contains(&"deliveries") { value["deliveries"] = serde_json::to_value(objects.comment_deliveries(id)?)?; }
                        let map = selected.iter().map(|field| ((*field).to_owned(), value.get(*field).cloned().unwrap_or(Value::Null))).collect::<Map<_, _>>();
                        Ok(map)
                    }).collect::<Result<Vec<_>>>()?)
                } else {
                    print_comments(&comments);
                    for comment in &comments {
                        let id: i64 = comment.database_id.parse()?;
                        print_message_receipts(id, &objects.comment_deliveries(id)?);
                    }
                    Ok(())
                }
            }
            CommentCommand::Edit { id, body, json } => {
                let changed = objects.edit_comment(turn, id, &body.required()?)?;
                print_change("comment", id, "edited", changed, json)
            },
            CommentCommand::Hide { ids, reason, json } => {
                let results = objects.hide_comments(turn, &ids, reason.as_deref())?;
                if json {
                    #[derive(serde::Serialize)]
                    struct HiddenComment { id: i64, changed: bool, action: &'static str, effect: &'static str }
                    output(results.iter().map(|(id, changed)| HiddenComment { id: *id, changed: *changed, action: "hidden", effect: "本条及现有、未来后代正文隐藏，各条自身状态保留" }).collect::<Vec<_>>())
                }
                else {
                    for (id, changed) in results { print_change("comment", id, "hidden", changed, false)?; }
                    Ok(())
                }
            }
            CommentCommand::Unhide { id, json } => {
                let changed = objects.comment_lifecycle(turn, id, "unhide")?;
                print_change("comment", id, "unhidden", changed, json)
            },
            CommentCommand::Delete { id, json } => {
                let changed = objects.comment_lifecycle(turn, id, "delete")?;
                print_change("comment", id, "deleted", changed, json)
            },
            CommentCommand::Resolve { ids, json } => print_comment_resolution(&objects.resolve_comments(turn, &ids, true)?, true, json),
            CommentCommand::Unresolve { ids, json } => print_comment_resolution(&objects.resolve_comments(turn, &ids, false)?, false, json),
            CommentCommand::Reaction { command } => match command {
                ReactionCommand::Add { id, expression, json } => {
                    let changed = objects.react(turn, id, &expression, false)?;
                    print_change("comment", id, "reaction added", changed, json)
                }
                ReactionCommand::Remove { id, expression, json } => {
                    let changed = objects.react(turn, id, &expression, true)?;
                    print_change("comment", id, "reaction removed", changed, json)
                }
            },
        },
    }
}
