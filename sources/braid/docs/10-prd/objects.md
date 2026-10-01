## Product Objects

### Work Items and Context

- A **GitHub Issue** becomes an Issue Work Item through an Issue Activation.
  A provisioned GitHub Agent App assignment is the preferred native signal;
  an ordinary GitHub App is not a standard assignable user, so the PoC also
  accepts the first Trusted Braid Mention on a dormant Issue. Native assignment
  creates a session and remains idle; mention fallback carries the comment as
  a Wake Event and starts the first turn after materialization.
- A **GitHub PR** becomes a PR Work Item through a trusted `@braid` PR comment
  or the ActivationIntent produced by `braid gh pr ensure`.
- **Issue Context** contains the repository-qualified Issue identity, current
  title and description, material metadata and relationships, and its comment
  lifecycle projection.
- **PR Context** first contains the current projections of every directly
  Associated Issue, then the PR's own minimal implementation context. It is
  rebuilt from current state before every PR turn; it is never a creation-time
  snapshot.
- Full Context is Markdown or plain text for the Agent, never a JSON protocol
  dump. Event user messages are short references; the Agent can use `gh` to
  inspect the changed object.

The exact projection is the [Context contract](../20-product-tdd/context.md).

本地入口以SQLite中的Issue、PR、正文和讨论为协作权威，每个被指派工作项拥有独立成员和clone，不再维护设计/实施Markdown镜像。当前Context与生命周期契约见[本地工作项](../20-product-tdd/local.md)。

本地PR还可拥有明确的ReviewRequest。请求绑定具体PR、验收Issue、固定base/head和需求依据；请求是否完成、原候选结论和结论是否仍适用于当前候选是不同事实。默认由验收Issue现有负责人处理，也可委派reviewer-only成员。委派建立独立执行身份与冻结checkout，源PR实施者保持原责任。一次请求保存不可覆写的Approved、ChangesRequested或Inconclusive，或有原因的Cancelled；候选修复后使用新请求，PR关闭不代替验收。

Review是内部执行节点，不是额外Issue，也不进入普通Issue/PR目录。代码判断与浏览器验收由当前review责任承担，实际服务、数据和观察必须对应冻结候选；Braid提供独立路径和证据记录，不把原生执行结束或工作项状态当作产品通过。显式依结论合并时使用--review核验候选与依据，历史结论持续可读。

### 本地评论可见性

评论的自身隐藏、删除与讨论解决分别保存。隐藏一条评论时，该条及其现有、未来后代的正文从普通对象读取、模型 Context 和 Console 展示中隐藏；中间回复只影响自己的分支。取消祖先隐藏不会清除后代自身的隐藏选择。精准读取也遵守祖先隐藏，显式追溯可读仍保存的正文；删除正文不可恢复。解决仍折叠当时的讨论前缀，新回复不会自动折叠。接口与通知行为见[本地工作项](../20-product-tdd/local.md)。

### Agent Profiles and Groups

An Agent Profile is a versioned Braid configuration containing a provider,
model, reasoning setting, Profile User Instructions, cwd/workspace policy,
sandbox/approval settings, and optional tools, skills, MCP, or other
provider-specific resources. Tags declare whether it can serve `issue`, `pr`,
or both. The Profile `workspace` names a clean source checkout, never the
Agent's cwd: every Agent Group session runs in a dedicated generation-scoped
Braid worktree (the Issue's sole Development branch when unambiguous,
otherwise the default branch; the PR head for a PR Agent).

Braid adds its own versioned System Prompt when materializing a Provider
Session. It explains GitHub Working Memory, Braid and `braid gh`, concise public
comments, and the Issue- or PR-specific role. GitHub Context remains delimited
working data rather than a system instruction.

The architecture can represent multiple parallel Agents without primary or
sub-agent roles. MVP acceptance deliberately uses:

- one active Issue Agent per Issue Agent Group;
- one Implementation Agent per PR Agent Group;
- one dedicated generation-scoped worktree per Agent Group session.

Multi-Agent fan-out is not rejected, but cross-peer ordering, semantic merge,
arbitration, and convergence are outside the MVP correctness claim.
