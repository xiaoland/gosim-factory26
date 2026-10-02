#![allow(clippy::needless_raw_string_hashes)]
#![allow(clippy::large_futures)]
use std::{collections::BTreeSet, fmt::Write as _};

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
        format!("Local {noun}: {}#{}", self.repository, self.number)
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

#[derive(Debug, Clone, Serialize)]
pub struct RenderedContext {
    pub text: String,
    pub revision: String,
    pub bytes: usize,
    pub pressure: ContextPressure,
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
    let mut text = String::new();
    match context {
        CanonicalContext::Issue(issue) => render_issue(&mut text, issue),
        CanonicalContext::PullRequest(pull_request) => render_pull_request(&mut text, pull_request),
    }
    let bytes = text.len();
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
    RenderedContext { text, revision: hex::encode(digest.finalize()), bytes, pressure }
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

fn render_issue(output: &mut String, issue: &IssueSnapshot) {
    push_line(output, &format!("# Local Issue: {}#{}", issue.repository, issue.number));
    push_line(output, &issue.title);
    output.push('\n');
    push_state(output, &issue.state, issue.state_reason.as_deref());
    push_actor(output, "Author", issue.author.as_ref());
    if let Some(issue_type) = &issue.issue_type {
        push_line(output, &format!("Type: {issue_type}"));
    }
    push_actor_set(output, "Assignees", &issue.assignees);
    push_string_set(output, "Labels", &issue.labels);
    if let Some(milestone) = &issue.milestone {
        push_line(output, &format!("Milestone: {milestone}"));
    }
    render_projects(output, &issue.projects);
    push_string_set(output, "Development branches", &issue.linked_branches);
    render_issue_relationships(output, issue);
    if !issue.body.is_empty() {
        push_section(output, "Description");
        push_body(output, &filter_html_comments(&issue.body));
    }
    if !issue.comments.is_empty() {
        push_section(output, "Comments");
        for comment in &issue.comments {
            render_comment(output, comment, "Comment");
        }
    }
}

fn render_pull_request(output: &mut String, pull_request: &PullRequestSnapshot) {
    for issue in &pull_request.associated_issues {
        render_issue(output, issue);
        output.push_str("\n---\n\n");
    }
    push_line(output, &format!("# Local PR: {}#{}", pull_request.repository, pull_request.number));
    push_line(output, &pull_request.title);
    output.push('\n');
    push_line(output, &format!("State: {}", pull_request.state.to_ascii_lowercase()));
    let readiness = if pull_request.merged {
        "merged"
    } else if pull_request.draft {
        "draft"
    } else {
        "ready"
    };
    push_line(output, &format!("Lifecycle: {readiness}"));
    push_actor(output, "Author", pull_request.author.as_ref());
    push_line(output, &format!("Base: {}", pull_request.base_ref));
    let head = pull_request.head_repository.as_ref().map_or_else(
        || pull_request.head_ref.clone(),
        |repository| format!("{repository}:{}", pull_request.head_ref),
    );
    push_line(output, &format!("Head: {head}"));
    push_actor_set(output, "Assignees", &pull_request.assignees);
    push_string_set(output, "Labels", &pull_request.labels);
    if let Some(milestone) = &pull_request.milestone {
        push_line(output, &format!("Milestone: {milestone}"));
    }
    render_projects(output, &pull_request.projects);
    if !pull_request.body.is_empty() {
        push_section(output, "Description");
        push_body(output, &filter_html_comments(&pull_request.body));
    }
    if !pull_request.conversation.is_empty() {
        push_section(output, "Conversation");
        for comment in &pull_request.conversation {
            render_comment(output, comment, "Comment");
        }
    }
    if !pull_request.reviews.is_empty() {
        push_section(output, "Reviews");
        for review in &pull_request.reviews {
            let author = review.author.as_ref().map_or("@ghost", |actor| actor.login.as_str());
            push_line(output, &format!("### Review: {} by @{author}", review.database_id));
            push_line(output, &format!("State: {}", review.state.to_ascii_lowercase()));
            push_line(output, &format!("Posted: {}", review.created_at));
            if review.updated_at != review.created_at {
                push_line(output, &format!("Updated: {}", review.updated_at));
            }
            if review.minimized {
                let reason = review.minimized_reason.as_deref().unwrap_or("unspecified");
                push_line(output, &format!("State: minimized ({reason})"));
            } else if !review.body.is_empty() {
                output.push('\n');
                push_body(output, &filter_html_comments(&review.body));
            }
        }
    }
    if !pull_request.review_threads.is_empty() {
        push_section(output, "Review Threads");
        for thread in &pull_request.review_threads {
            let mut location = thread.path.clone();
            if let Some(line) = thread.line {
                let _ = write!(location, ":{line}");
            }
            push_line(output, &format!("### Review thread at {location}"));
            push_line(output, &format!("Location: {location}"));
            let mut states = Vec::new();
            if thread.resolved {
                states.push("resolved");
            }
            if thread.collapsed {
                states.push("collapsed");
            }
            if thread.outdated {
                states.push("outdated");
            }
            if states.is_empty() {
                states.push("open");
            }
            push_line(output, &format!("State: {}", states.join(", ")));
            if thread.resolved {
                push_actor(output, "Resolved by", thread.resolved_by.as_ref());
            }
            if thread.resolved || thread.collapsed {
                render_thread_metadata(output, &thread.comments);
            } else {
                for comment in &thread.comments {
                    render_comment(output, comment, "Review comment");
                }
            }
        }
    }
}

fn render_issue_relationships(output: &mut String, issue: &IssueSnapshot) {
    if let Some(parent) = &issue.parent {
        push_line(output, &format!("Parent: {}", parent.identity()));
    }
    push_references(output, "Sub-issues", &issue.sub_issues);
    push_references(output, "Blocked by", &issue.blocked_by);
    push_references(output, "Blocking", &issue.blocking);
    push_references(output, "Associated PRs", &issue.associated_prs);
    if !issue.duplicate_pairs.is_empty() {
        let values = issue
            .duplicate_pairs
            .iter()
            .map(|(duplicate, canonical)| {
                format!("{} → {}", duplicate.identity(), canonical.identity())
            })
            .collect::<Vec<_>>();
        push_line(output, &format!("Duplicates: {}", values.join(", ")));
    }
}

fn render_projects(output: &mut String, projects: &[ProjectEntry]) {
    for project in projects {
        let fields = project
            .fields
            .iter()
            .map(|field| format!("{}={}", field.name, field.value))
            .collect::<Vec<_>>();
        if fields.is_empty() {
            push_line(output, &format!("Project: {}", project.title));
        } else {
            push_line(output, &format!("Project: {} ({})", project.title, fields.join(", ")));
        }
    }
}

fn render_comment(output: &mut String, comment: &CommentSnapshot, noun: &str) {
    let author = comment.author.as_ref().map_or("ghost", |actor| actor.login.as_str());
    let reference_kind =
        if noun == "Review comment" { "pullrequestreviewcomment" } else { "issuecomment" };
    push_line(
        output,
        &format!(
            "### {noun}: {}#{reference_kind}-{} by @{author}",
            comment.repository, comment.database_id,
        ),
    );
    push_line(output, &format!("Posted: {}", comment.created_at));
    push_line(
        output,
        &format!(
            "Thread: {} ({})",
            comment.thread_root,
            if comment.resolved { "resolved" } else { "open" }
        ),
    );
    if let Some(parent) = comment.reply_to {
        push_line(output, &format!("Reply to: comment {parent}"));
    }
    for reaction in &comment.reactions {
        push_line(output, &format!("Reaction: {} by {}", reaction.expression, reaction.actor));
    }
    if comment.updated_at != comment.created_at {
        push_line(output, &format!("Updated: {}", comment.updated_at));
    }
    if comment.deleted {
        push_line(output, "State: deleted");
        output.push('\n');
        return;
    }
    if comment.minimized {
        let reason = comment.minimized_reason.as_deref().unwrap_or("unspecified");
        push_line(output, &format!("State: minimized ({reason})"));
        output.push('\n');
        return;
    }
    if comment.folded {
        push_line(
            output,
            "State: folded by thread resolution; use comment view --include-hidden to read",
        );
        output.push('\n');
        return;
    }
    if comment.pinned {
        push_line(output, "Pinned: yes");
    }
    if let Some(body) = &comment.body {
        output.push('\n');
        push_body(output, &filter_html_comments(body));
    }
}

fn render_thread_metadata(output: &mut String, comments: &[CommentSnapshot]) {
    let authors = comments
        .iter()
        .filter_map(|comment| comment.author.as_ref().map(|actor| format!("@{}", actor.login)))
        .collect::<BTreeSet<_>>();
    if !authors.is_empty() {
        push_line(
            output,
            &format!("Authors: {}", authors.into_iter().collect::<Vec<_>>().join(", ")),
        );
    }
    if let Some(first) = comments.first() {
        push_line(output, &format!("Posted: {}", first.created_at));
    }
    if let Some(last) = comments.last() {
        push_line(output, &format!("Updated: {}", last.updated_at));
    }
    output.push('\n');
}

fn push_state(output: &mut String, state: &str, reason: Option<&str>) {
    let state = state.to_ascii_lowercase();
    match reason {
        Some(reason) => {
            push_line(output, &format!("State: {state} ({})", reason.to_ascii_lowercase()));
        }
        None => push_line(output, &format!("State: {state}")),
    }
}

fn push_actor(output: &mut String, label: &str, actor: Option<&Actor>) {
    if let Some(actor) = actor {
        push_line(output, &format!("{label}: @{}", actor.login));
    }
}

fn push_actor_set(output: &mut String, label: &str, actors: &[Actor]) {
    let values = actors.iter().map(|actor| format!("@{}", actor.login)).collect::<Vec<_>>();
    push_line(output, &format!("{label}: {}", if values.is_empty() { "未指派".into() } else { values.join(", ") }));
}

fn push_string_set(output: &mut String, label: &str, values: &[String]) {
    if !values.is_empty() {
        push_line(output, &format!("{label}: {}", values.join(", ")));
    }
}

fn push_references(output: &mut String, label: &str, references: &[WorkItemReference]) {
    if !references.is_empty() {
        push_line(
            output,
            &format!(
                "{label}: {}",
                references.iter().map(WorkItemReference::identity).collect::<Vec<_>>().join(", ")
            ),
        );
    }
}

fn push_section(output: &mut String, title: &str) {
    output.push('\n');
    push_line(output, &format!("## {title}"));
    output.push('\n');
}

fn push_body(output: &mut String, body: &str) {
    output.push_str(body.trim_matches('\n'));
    output.push_str("\n\n");
}

fn push_line(output: &mut String, line: &str) {
    output.push_str(line);
    output.push('\n');
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
