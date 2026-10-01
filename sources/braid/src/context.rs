#![allow(clippy::needless_raw_string_hashes)]
#![allow(clippy::large_futures)]
use std::collections::HashMap;

use comrak::{Arena, Options, nodes::NodeValue, parse_document};
use serde::Serialize;
use sha2::{Digest, Sha256};
use thiserror::Error;

use crate::{
    objects::{LocalObjects, WorkItemLocator},
    store::{StoreActor, StoreError},
};

const CONTEXT_REVISION_DOMAIN: &[u8] = b"braid-context-v1\0";

#[derive(Debug, Error)]
pub enum ContextError {
    #[error(transparent)]
    Local(#[from] anyhow::Error),
    #[error(transparent)]
    Store(#[from] StoreError),
    #[error("Local Context is {bytes} bytes, above the Profile hard limit of {hard_bytes} bytes")]
    TooLarge { bytes: usize, hard_bytes: usize },
}

#[derive(Debug, Clone, Serialize)]
pub struct Actor {
    pub node_id: String,
    pub login: String,
}

#[derive(Debug, Clone, Serialize)]
pub struct WorkItemReference {
    pub node_id: String,
    pub repository_node_id: String,
    pub repository: String,
    pub number: u64,
    pub kind: WorkItemKind,
    pub title: String,
    pub state: String,
    pub state_reason: Option<String>,
}

impl WorkItemReference {
    fn identity(&self) -> String {
        let noun = match self.kind {
            WorkItemKind::Issue => "Issue",
            WorkItemKind::PullRequest => "PR",
        };
        format!("{noun} {}", self.number)
    }
}

#[derive(Debug, Clone, Copy, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum WorkItemKind {
    Issue,
    PullRequest,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProjectEntry {
    pub title: String,
    pub fields: Vec<ProjectField>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProjectField {
    pub name: String,
    pub value: String,
}

// Visibility, deletion, and thread resolution are independent object facts.
#[allow(clippy::struct_excessive_bools)]
#[derive(Debug, Clone, Serialize)]
pub struct CommentSnapshot {
    pub node_id: String,
    pub database_id: String,
    pub repository: String,
    pub work_item_number: u64,
    pub author: Option<Actor>,
    pub created_at: String,
    pub updated_at: String,
    pub body: Option<String>,
    pub minimized: bool,
    pub minimized_reason: Option<String>,
    pub hidden_by: Option<i64>,
    pub hidden_by_reason: Option<String>,
    pub pinned: bool,
    pub deleted: bool,
    pub reply_to: Option<i64>,
    pub thread_root: i64,
    pub resolved: bool,
    pub folded: bool,
    pub reactions: Vec<CommentReaction>,
}

#[derive(Debug, Clone, Serialize)]
pub struct CommentReaction {
    pub actor: String,
    pub expression: String,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct IssueSnapshot {
    pub node_id: String,
    pub database_id: String,
    pub repository_node_id: String,
    pub repository: String,
    pub number: u64,
    pub title: String,
    pub body: String,
    pub state: String,
    pub state_reason: Option<String>,
    pub updated_at: String,
    pub author: Option<Actor>,
    pub issue_type: Option<String>,
    pub assignees: Vec<Actor>,
    pub labels: Vec<String>,
    pub milestone: Option<String>,
    pub projects: Vec<ProjectEntry>,
    pub linked_branches: Vec<String>,
    pub parent: Option<WorkItemReference>,
    pub sub_issues: Vec<WorkItemReference>,
    pub blocked_by: Vec<WorkItemReference>,
    pub blocking: Vec<WorkItemReference>,
    pub duplicate_pairs: Vec<(WorkItemReference, WorkItemReference)>,
    pub associated_prs: Vec<WorkItemReference>,
    pub comments: Vec<CommentSnapshot>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ReviewSnapshot {
    pub node_id: String,
    pub database_id: String,
    pub author: Option<Actor>,
    pub state: String,
    pub created_at: String,
    pub updated_at: String,
    pub body: String,
    pub minimized: bool,
    pub minimized_reason: Option<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ReviewThreadSnapshot {
    pub node_id: String,
    pub path: String,
    pub line: Option<u64>,
    pub start_line: Option<u64>,
    pub resolved: bool,
    pub resolved_by: Option<Actor>,
    pub collapsed: bool,
    pub outdated: bool,
    pub comments: Vec<CommentSnapshot>,
}

#[derive(Debug, Clone, Serialize, Default)]
pub struct PullRequestSnapshot {
    pub node_id: String,
    pub database_id: String,
    pub repository_node_id: String,
    pub repository: String,
    pub number: u64,
    pub title: String,
    pub body: String,
    pub state: String,
    pub draft: bool,
    pub merged: bool,
    pub updated_at: String,
    pub author: Option<Actor>,
    pub base_ref: String,
    pub head_repository: Option<String>,
    pub head_ref: String,
    pub assignees: Vec<Actor>,
    pub labels: Vec<String>,
    pub milestone: Option<String>,
    pub projects: Vec<ProjectEntry>,
    pub associated_issues: Vec<IssueSnapshot>,
    pub conversation: Vec<CommentSnapshot>,
    pub reviews: Vec<ReviewSnapshot>,
    pub review_threads: Vec<ReviewThreadSnapshot>,
}

#[derive(Debug, Clone, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum CanonicalContext {
    Issue(IssueSnapshot),
    PullRequest(PullRequestSnapshot),
}

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContextPressure {
    Normal,
    Soft,
    Hard,
}

#[derive(Debug, Clone, Copy, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum ContextTier {
    Full,
    CommentIndex,
    References,
}

#[derive(Debug, Clone, Serialize)]
pub struct RenderedContext {
    pub text: String,
    pub revision: String,
    pub bytes: usize,
    pub pressure: ContextPressure,
    pub tier: ContextTier,
    pub estimated_tokens: usize,
}

pub async fn materialize_issue(
    client: &LocalObjects,
    locator: &WorkItemLocator,
    _page_size: usize,
) -> Result<IssueSnapshot, ContextError> {
    Ok(client.issue(i64::try_from(locator.number).map_err(anyhow::Error::from)?)?)
}
pub async fn materialize_pull_request(
    client: &LocalObjects,
    locator: &WorkItemLocator,
    _page_size: usize,
) -> Result<PullRequestSnapshot, ContextError> {
    Ok(client.pull_request(i64::try_from(locator.number).map_err(anyhow::Error::from)?)?)
}

#[allow(clippy::cast_precision_loss)]
pub fn render_complete(
    context: &CanonicalContext,
    soft_ratio: f64,
    hard_bytes: usize,
) -> RenderedContext {
    render_projected(context, soft_ratio, hard_bytes, ContextTier::Full)
}

/// Select the richest deterministic projection strictly below one fifth of
/// the model window. If even the minimum locator cannot fit, return Hard.
pub fn render_budgeted(
    context: &CanonicalContext,
    soft_ratio: f64,
    hard_bytes: usize,
    context_window_tokens: usize,
) -> RenderedContext {
    let full = render_complete(context, soft_ratio, hard_bytes);
    if within_budget(&full, hard_bytes, context_window_tokens) { return full; }

    let mut indexed = context.clone();
    index_comments(&mut indexed);
    let index = render_projected(&indexed, soft_ratio, hard_bytes, ContextTier::CommentIndex);
    if within_budget(&index, hard_bytes, context_window_tokens) { return index; }

    let mut limit = 1200usize;
    loop {
        let mut references = context.clone();
        reference_projection(&mut references, limit);
        let rendered = render_projected(&references, soft_ratio, hard_bytes, ContextTier::References);
        if within_budget(&rendered, hard_bytes, context_window_tokens) { return rendered; }
        if limit == 0 { break; }
        limit /= 2;
    }

    let mut minimal = finish_rendered(minimum_locator(context), soft_ratio, hard_bytes, ContextTier::References);
    if !within_budget(&minimal, hard_bytes, context_window_tokens) {
        minimal.pressure = ContextPressure::Hard;
    }
    minimal
}

fn render_projected(context: &CanonicalContext, soft_ratio: f64, hard_bytes: usize, tier: ContextTier) -> RenderedContext {
    let mut text = String::new();
    match context {
        CanonicalContext::Issue(issue) => render_issue(&mut text, issue, tier),
        CanonicalContext::PullRequest(pull_request) => render_pull_request(&mut text, pull_request, tier),
    }
    if tier == ContextTier::References { append_read_paths(&mut text, context); }
    finish_rendered(text, soft_ratio, hard_bytes, tier)
}

#[allow(clippy::cast_precision_loss)]
fn finish_rendered(text: String, soft_ratio: f64, hard_bytes: usize, tier: ContextTier) -> RenderedContext {
    let bytes = text.len();
    let estimated_tokens = estimate_tokens(&text);
    let pressure = if bytes > hard_bytes {
        ContextPressure::Hard
    } else if bytes as f64 > hard_bytes as f64 * soft_ratio {
        ContextPressure::Soft
    } else {
        ContextPressure::Normal
    };
    let mut digest = Sha256::new();
    digest.update(CONTEXT_REVISION_DOMAIN);
    digest.update(text.as_bytes());
    RenderedContext { text, revision: hex::encode(digest.finalize()), bytes, pressure, tier, estimated_tokens }
}

fn estimate_tokens(text: &str) -> usize {
    let (ascii, non_ascii) = text.chars().fold((0usize, 0usize), |(ascii, non_ascii), ch| {
        if ch.is_ascii() { (ascii + 1, non_ascii) } else { (ascii, non_ascii + 1) }
    });
    ascii.div_ceil(4) + non_ascii
}

fn within_budget(rendered: &RenderedContext, hard_bytes: usize, context_window_tokens: usize) -> bool {
    rendered.bytes <= hard_bytes && rendered.estimated_tokens.saturating_mul(5) < context_window_tokens
}

fn index_comments(context: &mut CanonicalContext) {
    let comments = match context {
        CanonicalContext::Issue(issue) => &mut issue.comments,
        CanonicalContext::PullRequest(pr) => &mut pr.conversation,
    };
    for comment in comments { comment.body = None; }
}

fn reference_projection(context: &mut CanonicalContext, limit: usize) {
    match context {
        CanonicalContext::Issue(issue) => {
            issue.comments.clear();
            issue.body = truncate_chars(&project_body(&issue.body), limit);
            issue.state_reason = issue.state_reason.take().map(|reason| truncate_chars(&reason, limit.min(200))).filter(|reason| !reason.is_empty());
        }
        CanonicalContext::PullRequest(pr) => {
            pr.conversation.clear();
            pr.body = truncate_chars(&project_body(&pr.body), limit);
            for issue in &mut pr.associated_issues {
                issue.comments.clear();
                issue.body = truncate_chars(&project_body(&issue.body), limit / 2);
            }
        }
    }
}

fn truncate_chars(text: &str, limit: usize) -> String {
    if text.chars().count() <= limit { return text.to_owned(); }
    if limit == 0 { return String::new(); }
    format!("{}\n…", text.chars().take(limit).collect::<String>())
}

fn append_read_paths(output: &mut String, context: &CanonicalContext) {
    let (kind, number) = match context {
        CanonicalContext::Issue(issue) => ("issue", issue.number),
        CanonicalContext::PullRequest(pr) => ("pr", pr.number),
    };
    heading(output, 2, "Read more");
    push_line(output, &format!("工作项投影：braid context {kind} {number}"));
    push_line(output, &format!("完整正文：braid {kind} view {number} --json body"));
    push_line(output, &format!("当前讨论：braid {kind} view {number} --comments"));
    if matches!(context, CanonicalContext::PullRequest(_)) {
        push_line(output, "关联 Issue 的完整正文：braid issue view ID --json body（ID 见上方 Issues）");
    }
}

fn minimum_locator(context: &CanonicalContext) -> String {
    match context {
        CanonicalContext::Issue(issue) => format!("# Issue {} - {}\n工作项投影：braid context issue {}\n完整正文：braid issue view {} --json body\n", issue.number, issue.state, issue.number, issue.number),
        CanonicalContext::PullRequest(pr) => format!("# PR {} - {}\n工作项投影：braid context pr {}\n完整正文：braid pr view {} --json body\n", pr.number, pr.state, pr.number, pr.number),
    }
}

pub fn record_context_revision(
    context: &CanonicalContext,
    rendered: &RenderedContext,
    store: &StoreActor,
) -> Result<(), ContextError> {
    let node_id = match context {
        CanonicalContext::Issue(issue) => &issue.node_id,
        CanonicalContext::PullRequest(pull_request) => &pull_request.node_id,
    };
    store.set_context_revision(node_id.clone(), rendered.revision.clone())?;
    Ok(())
}

fn render_issue(output: &mut String, issue: &IssueSnapshot, tier: ContextTier) {
    render_issue_at(output, issue, 1, false, tier);
}

fn render_issue_at(output: &mut String, issue: &IssueSnapshot, level: usize, associated: bool, tier: ContextTier) {
    heading(output, level, &format!(
        "Issue {} - {} - {} - {}",
        issue.number, one_line(&issue.title), issue.state, assignees(&issue.assignees),
    ));
    if !associated {
        if let Some(reason) = issue.state_reason.as_deref() {
            push_line(output, "Close reason:");
            fenced_body(output, reason);
        }
        if let Some(parent) = &issue.parent {
            push_line(output, &format!("Parent: {}", parent.identity()));
        }
        references(output, "Sub-issues", &issue.sub_issues);
        references(output, "PRs", &issue.associated_prs);
    }
    if !issue.body.is_empty() {
        heading(output, level + 1, "Description");
        if tier == ContextTier::References {
            // References already projects before truncation. Re-parsing the
            // shortened Markdown could reinterpret an incomplete code span.
            fenced_body(output, &issue.body);
        } else {
            fenced_body(output, &project_body(&issue.body));
        }
    }
    if !associated && !issue.comments.is_empty() {
        heading(output, level + 1, "Discussion");
        render_context_comments(output, &issue.comments, level + 2, tier == ContextTier::CommentIndex);
    }
}

fn render_pull_request(output: &mut String, pull_request: &PullRequestSnapshot, tier: ContextTier) {
    let state = if pull_request.state == "OPEN" {
        if pull_request.draft { "OPEN draft" } else { "OPEN ready" }
    } else {
        pull_request.state.as_str()
    };
    heading(output, 1, &format!(
        "PR {} - {} - {} - {}",
        pull_request.number, one_line(&pull_request.title), state, assignees(&pull_request.assignees),
    ));
    push_line(output, &format!(
        "Branch: {} → {}",
        short_branch(&pull_request.head_ref), short_branch(&pull_request.base_ref),
    ));
    if !pull_request.associated_issues.is_empty() {
        push_line(output, &format!(
            "Issues: {}",
            pull_request.associated_issues.iter().map(|issue| format!("Issue {}", issue.number)).collect::<Vec<_>>().join(", "),
        ));
    }
    if !pull_request.body.is_empty() {
        heading(output, 2, "Description");
        if tier == ContextTier::References {
            fenced_body(output, &pull_request.body);
        } else {
            fenced_body(output, &project_body(&pull_request.body));
        }
    }
    if !pull_request.conversation.is_empty() {
        heading(output, 2, "Discussion");
        render_context_comments(output, &pull_request.conversation, 3, tier == ContextTier::CommentIndex);
    }
    if pull_request.associated_issues.iter().any(|issue| issue.state == "OPEN") {
        heading(output, 2, "Associated Issues");
        for issue in pull_request.associated_issues.iter().filter(|issue| issue.state == "OPEN") {
            render_issue_at(output, issue, 3, true, tier);
        }
    }
}

fn render_context_comments(output: &mut String, comments: &[CommentSnapshot], heading_level: usize, comment_index: bool) {
    let visible = comments.iter().filter(|comment| {
        !comment.folded || comment.database_id.parse::<i64>().ok() == Some(comment.thread_root)
    }).cloned().collect::<Vec<_>>();
    if comment_index { push_line(output, "讨论仅列标题；按编号使用 braid comment view ID 读取正文。"); }
    render_comments(output, &visible, heading_level, true);
}

/// Render a comment slice as a reply tree. Missing parents become roots, so a
/// direct `comment view ID` retains its own comment when the parent is absent.
pub(crate) fn render_comments(output: &mut String, comments: &[CommentSnapshot], heading_level: usize, filter_html: bool) {
    let ids = comments.iter().enumerate().filter_map(|(index, comment)| {
        comment.database_id.parse::<i64>().ok().map(|id| (id, index))
    }).collect::<HashMap<_, _>>();
    let mut roots = Vec::new();
    let mut children = vec![Vec::new(); comments.len()];
    for (index, comment) in comments.iter().enumerate() {
        let parent = comment.reply_to.and_then(|id| ids.get(&id).copied().or_else(|| ids.get(&comment.thread_root).copied()));
        let own_id = comment.database_id.parse::<i64>().ok();
        if let Some(parent) = parent.filter(|_| comment.reply_to.zip(own_id).is_some_and(|(parent, own)| parent < own)) {
            children[parent].push(index);
        } else {
            roots.push(index);
        }
    }
    let by_creation = |a: &usize, b: &usize| comments[*a].created_at.cmp(&comments[*b].created_at)
        .then_with(|| comments[*a].database_id.cmp(&comments[*b].database_id));
    roots.sort_by(by_creation);
    for branch in &mut children { branch.sort_by(by_creation); }
    let mut pending = roots.into_iter().rev().map(|index| (index, 0usize)).collect::<Vec<_>>();
    while let Some((index, depth)) = pending.pop() {
        let parent_missing = comments[index].reply_to.is_some_and(|parent| !ids.contains_key(&parent));
        render_comment(output, &comments[index], heading_level + depth, filter_html, parent_missing);
        for &child in children[index].iter().rev() { pending.push((child, depth + 1)); }
    }
}

fn render_comment(output: &mut String, comment: &CommentSnapshot, level: usize, filter_html: bool, parent_missing: bool) {
    let mut title = format!("Comment {}", comment.database_id);
    if let Some(author) = &comment.author {
        title.push_str(&format!(" - @{}", one_line(&author.login)));
    }
    if let Some(parent) = comment.reply_to.filter(|_| parent_missing) {
        title.push_str(&format!(" - reply to #{parent}"));
    }
    if comment.deleted {
        title.push_str(" - deleted");
    } else if comment.minimized {
        title.push_str(" - hidden");
        if let Some(reason) = &comment.minimized_reason {
            title.push_str(&format!(" ({})", one_line(reason)));
        }
    }
    if !comment.deleted {
        if let Some(ancestor) = comment.hidden_by {
            title.push_str(&format!(" - hidden by ancestor #{ancestor}"));
            if let Some(reason) = &comment.hidden_by_reason {
                title.push_str(&format!(" ({})", one_line(reason)));
            }
        } else if !comment.minimized && (comment.folded || comment.resolved) {
            title.push_str(" - resolved");
        }
    }
    if comment.pinned { title.push_str(" - pinned"); }
    if level <= 6 {
        heading(output, level, &title);
    } else {
        let indent = (level - 7) * 2;
        push_line(output, &format!("{}- {title}", " ".repeat(indent)));
    }
    let content_indent = if level <= 6 { 0 } else { (level - 7) * 2 + 2 };
    let padding = " ".repeat(content_indent);
    if comment.deleted { return; }
    if (comment.minimized || comment.hidden_by.is_some()) && (filter_html || comment.body.is_none()) {
        output.push('\n');
        return;
    }
    if comment.folded && (filter_html || comment.body.is_none()) {
        output.push('\n');
        return;
    }
    if !comment.reactions.is_empty() {
        push_line(output, &format!("{padding}Reactions: {}", comment.reactions.iter()
            .map(|reaction| format!("{} by {}", reaction.expression, reaction.actor))
            .collect::<Vec<_>>().join(", ")));
    }
    if let Some(body) = &comment.body {
        let visible = if filter_html { project_body(body) } else { body.clone() };
        fenced_body_indented(output, &visible, content_indent);
    } else if !filter_html {
        push_line(output, &format!("{padding}Read: braid comment view {}", comment.database_id));
        output.push('\n');
    }
}

fn assignees(actors: &[Actor]) -> String {
    if actors.is_empty() { "未指派".to_owned() }
    else { actors.iter().map(|actor| format!("@{}", one_line(&actor.login))).collect::<Vec<_>>().join(", ") }
}

fn one_line(value: &str) -> String {
    value.lines().collect::<Vec<_>>().join(" ")
}

fn short_branch(reference: &str) -> &str {
    reference.strip_prefix("refs/heads/").unwrap_or(reference)
}

fn references(output: &mut String, label: &str, values: &[WorkItemReference]) {
    if !values.is_empty() {
        push_line(output, &format!("{label}: {}", values.iter().map(WorkItemReference::identity).collect::<Vec<_>>().join(", ")));
    }
}

fn heading(output: &mut String, level: usize, title: &str) {
    if !output.is_empty() && !output.ends_with("\n\n") { output.push('\n'); }
    push_line(output, &format!("{} {title}", "#".repeat(level)));
    output.push('\n');
}

pub(crate) fn fenced_body(output: &mut String, body: &str) {
    fenced_body_indented(output, body, 0);
}

fn fenced_body_indented(output: &mut String, body: &str, indent: usize) {
    let mut run = 0usize;
    let mut longest = 0usize;
    for byte in body.bytes() {
        if byte == b'`' { run += 1; longest = longest.max(run); }
        else { run = 0; }
    }
    let pad = " ".repeat(indent);
    let fence = "`".repeat(longest.max(2) + 1);
    push_line(output, &format!("{pad}{fence}"));
    for line in body.split_inclusive('\n') {
        output.push_str(&pad);
        output.push_str(line);
    }
    if !body.ends_with('\n') { output.push('\n'); }
    push_line(output, &format!("{pad}{fence}"));
    output.push('\n');
}

fn push_line(output: &mut String, line: &str) {
    output.push_str(line);
    output.push('\n');
}

/// Project author-folded material without changing stored text or the separate
/// description-change comparison. Only explicit, balanced HTML is folded; this
/// is not a browser's HTML repair algorithm. Markdown code nodes are excluded.
fn project_body(markdown: &str) -> String {
    let markdown = filter_html_comments(markdown);
    if !markdown.as_bytes().windows(8).any(|text| text.eq_ignore_ascii_case(b"<details")) {
        return markdown;
    }
    let arena = Arena::new();
    let root = parse_document(&arena, &markdown, &Options::default());
    let offsets = line_offsets(&markdown);
    let mut html = root.descendants().filter_map(|node| {
        let data = node.data.borrow();
        match &data.value {
            NodeValue::HtmlInline(_) | NodeValue::HtmlBlock(_) => source_range(&markdown, &offsets, data.sourcepos),
            _ => None,
        }
    }).collect::<Vec<_>>();
    html.sort_unstable();

    struct Element<'a> {
        name: &'a str,
        start: usize,
        content_start: usize,
        summary: Option<(usize, usize)>,
        valid: bool,
    }
    let mut stack: Vec<Element<'_>> = Vec::new();
    let mut raw: Option<&str> = None;
    let mut omitted = Vec::new();
    let mut cursor = 0;
    for (start, end) in html {
        cursor = cursor.max(start);
        while let Some(tag) = next_html_tag(&markdown, &mut cursor, end, raw) {
            if raw.is_some() { raw = None; }
            if !tag.valid {
                for element in &mut stack { element.valid = false; }
                continue;
            }
            if tag.closing {
                let Some(index) = stack.iter().rposition(|element| element.name.eq_ignore_ascii_case(tag.name)) else {
                    for element in &mut stack { element.valid = false; }
                    continue;
                };
                if index + 1 != stack.len() {
                    // Consume crossed closures now; a later valid container must
                    // never supply the missing close for this broken candidate.
                    stack.truncate(index);
                    for element in &mut stack { element.valid = false; }
                    continue;
                }
                let element = stack.pop().expect("matching element exists");
                if !element.valid { continue; }
                if element.name.eq_ignore_ascii_case("summary") {
                    if let Some(parent) = stack.last_mut()
                        && parent.name.eq_ignore_ascii_case("details") && parent.summary.is_none()
                    {
                        parent.summary = Some((element.content_start, tag.start));
                    }
                } else if element.name.eq_ignore_ascii_case("details")
                    && let Some((summary_start, summary_end)) = element.summary
                {
                    omitted.push((element.start, summary_start));
                    omitted.push((summary_end, tag.end));
                }
            } else if !is_html_void(tag.name) {
                if tag.self_closing {
                    // HTML non-void elements require a real closing tag.
                    for element in &mut stack { element.valid = false; }
                    continue;
                }
                stack.push(Element { name: tag.name, start: tag.start, content_start: tag.end, summary: None, valid: true });
                if ["script", "style", "pre", "textarea", "title", "xmp", "iframe", "noembed", "noframes", "plaintext"]
                    .iter().any(|name| tag.name.eq_ignore_ascii_case(name))
                {
                    raw = Some(tag.name);
                }
            }
        }
    }
    // Unioning omissions also handles nested details: hidden descendants stay
    // hidden, while a details inside the retained summary folds in the same pass.
    omitted.sort_unstable();
    let mut merged: Vec<(usize, usize)> = Vec::new();
    for (start, end) in omitted {
        if let Some(last) = merged.last_mut() && start <= last.1 {
            last.1 = last.1.max(end);
        } else {
            merged.push((start, end));
        }
    }
    let mut visible = String::with_capacity(markdown.len());
    let mut cursor = 0;
    for (start, end) in merged {
        visible.push_str(&markdown[cursor..start]);
        visible.push('\n');
        cursor = end;
    }
    visible.push_str(&markdown[cursor..]);
    visible
}

struct HtmlTag<'a> {
    name: &'a str,
    start: usize,
    end: usize,
    closing: bool,
    self_closing: bool,
    valid: bool,
}

fn is_html_void(name: &str) -> bool {
    ["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]
        .iter().any(|void| name.eq_ignore_ascii_case(void))
}

// Scan only comrak's HTML source ranges, consuming entire attributes/comments.
// Inside raw text, only its own closing tag has structural meaning.
fn next_html_tag<'a>(markdown: &'a str, cursor: &mut usize, end: usize, raw: Option<&str>) -> Option<HtmlTag<'a>> {
    let bytes = markdown.as_bytes();
    // A raw element or comment may cross comrak nodes and blank lines. Its
    // literal span also excludes tags in intervening Markdown/code nodes.
    let end = if raw.is_some() { markdown.len() } else { end };
    while *cursor < end {
        let Some(relative) = markdown[*cursor..end].find('<') else {
            *cursor = end;
            return None;
        };
        let start = *cursor + relative;
        *cursor = start + 1;
        let closing = *cursor < end && bytes[*cursor] == b'/';
        let name_start = *cursor + usize::from(closing);
        let mut name_end = name_start;
        while name_end < end && (bytes[name_end].is_ascii_alphanumeric() || matches!(bytes[name_end], b'-' | b':')) {
            name_end += 1;
        }
        let name = &markdown[name_start..name_end];
        if let Some(raw) = raw {
            if raw.eq_ignore_ascii_case("plaintext") || !closing || !name.eq_ignore_ascii_case(raw) { continue; }
        } else {
            let tail = &markdown[start..];
            let terminator = if tail.starts_with("<!--") { Some("-->") }
                else if tail.starts_with("<![CDATA[") { Some("]]>") }
                else if tail.starts_with("<?") { Some("?>") } else { None };
            if let Some(terminator) = terminator {
                *cursor = start + tail.find(terminator).map_or(tail.len(), |offset| offset + terminator.len());
                continue;
            }
            if tail.starts_with("<!") {
                let mut quote = None;
                while *cursor < markdown.len() {
                    let byte = bytes[*cursor];
                    *cursor += 1;
                    if let Some(delimiter) = quote {
                        if byte == delimiter { quote = None; }
                    } else if matches!(byte, b'\'' | b'"') {
                        quote = Some(byte);
                    } else if byte == b'>' { break; }
                }
                continue;
            }
        }
        if name.is_empty() || !bytes[name_start].is_ascii_alphabetic()
            || name_end == end || !(bytes[name_end].is_ascii_whitespace() || matches!(bytes[name_end], b'/' | b'>'))
        {
            continue;
        }
        let mut quote = None;
        let mut valid = true;
        let mut position = name_end;
        while position < markdown.len() {
            let byte = bytes[position];
            if let Some(delimiter) = quote {
                if byte == delimiter { quote = None; }
            } else if matches!(byte, b'\'' | b'"') {
                quote = Some(byte);
            } else if byte == b'<' {
                valid = false;
            } else if byte == b'>' {
                *cursor = position + 1;
                let attributes = markdown[name_end..position].trim();
                valid &= !closing || attributes.is_empty();
                if raw.is_some() && !valid { break; }
                return Some(HtmlTag { name, start, end: *cursor, closing, self_closing: attributes.ends_with('/'), valid });
            }
            position += 1;
        }
        *cursor = position.saturating_add(1).min(markdown.len());
    }
    None
}

pub fn filter_html_comments(markdown: &str) -> String {
    let arena = Arena::new();
    let root = parse_document(&arena, markdown, &Options::default());
    let line_offsets = line_offsets(markdown);
    let mut ranges = Vec::new();
    for node in root.descendants() {
        let data = node.data.borrow();
        let is_comment = match &data.value {
            NodeValue::HtmlInline(literal) => literal.trim_start().starts_with("<!--"),
            NodeValue::HtmlBlock(block) => block.literal.trim_start().starts_with("<!--"),
            _ => false,
        };
        if is_comment && let Some(range) = source_range(markdown, &line_offsets, data.sourcepos) {
            ranges.push(range);
        }
    }
    if ranges.is_empty() {
        return markdown.to_owned();
    }
    ranges.sort_unstable();
    let mut merged: Vec<(usize, usize)> = Vec::new();
    for (start, end) in ranges {
        if let Some(last) = merged.last_mut()
            && start <= last.1
        {
            last.1 = last.1.max(end);
        } else {
            merged.push((start, end));
        }
    }
    let mut visible = String::with_capacity(markdown.len());
    let mut cursor = 0;
    for (start, end) in merged {
        visible.push_str(&markdown[cursor..start]);
        cursor = end;
    }
    visible.push_str(&markdown[cursor..]);
    visible
}

fn line_offsets(markdown: &str) -> Vec<usize> {
    let mut offsets = vec![0];
    for (offset, byte) in markdown.bytes().enumerate() {
        if byte == b'\n' {
            offsets.push(offset + 1);
        }
    }
    offsets
}

fn source_range(
    markdown: &str,
    line_offsets: &[usize],
    source: comrak::nodes::Sourcepos,
) -> Option<(usize, usize)> {
    let start_line = *line_offsets.get(source.start.line.checked_sub(1)?)?;
    let end_line = *line_offsets.get(source.end.line.checked_sub(1)?)?;
    let start = start_line.checked_add(source.start.column.checked_sub(1)?)?;
    let end = end_line.checked_add(source.end.column)?;
    (start <= end && end <= markdown.len()).then_some((start, end))
}

// Local materialization queries and response adapters follow. They are kept in
// this module because partial canonical data must never escape into projection.
