## Collaboration Workflow

### Discuss

Issue Activation creates the Issue session. A native assignment and the first
trusted visible `@braid` on a dormant Issue are the same internal `assign`
event; neither invents a turn by itself. On installations without the special
Agent App assignment capability, that first mention both activates the dormant
Issue and supplies the first Wake Event. Later Human comments, newly populated
included metadata, and unfolded content are Wake Events. They accumulate until
the Quiet Window expires or the count threshold is reached. The Issue Agent
receives one current Context plus coalesced Event References and decides
whether to discuss, update the design description, wait, or request
implementation.

### Implement

An Issue Agent or Human may request implementation through a concise Issue
comment. `braid gh pr ensure` uses that comment's GitHub ID as the
Implementation Request key, so concurrent calls for the same request converge
on one Draft PR. It establishes native Issue association and PR Activation. If
the selected remote head has no difference from base, Braid creates an
App-authored empty bootstrap commit with the same tree, so GitHub can open the
Draft PR before implementation changes exist. This public commit changes no
file and records the Implementation Request; the PR Agent then implements in
the resulting branch/worktree.

PR Profile selection is deterministic: use the sole eligible `pr` Profile, or
the configured default when several exist; otherwise leave activation visibly
blocked. The PR session receives all directly Associated Issue Contexts and the
current PR Context. Local Git facts such as head SHA, commits, changed-file
summaries, checks, and normally reviewers stay out of Context because the Agent
can discover them without harm; GitHub changes to those facts arrive as Event
References when available.

### Review and Memory Maintenance

PR comments, reviews, diff comments, and unresolved review threads form the PR
discussion memory. A PR Agent may update a directly Associated Issue when
implementation reveals a design correction. Its own write is included in
future Context but does not wake or reset the same Agent.

Only open Associated Issues contribute full Context. Every closed Issue,
including completed, not-planned, and duplicate Issues, contributes only its
reference, state/reason, and relationship metadata. Reopening restores full
Context on the next materialization.

### 本地固定候选验收

本地ready与request-review是分开的动作：实现者发布候选并ready后，请求所关联Issue的当前负责人验收。恰好一个关联Issue才可默认选择，多个时明确指出验收Issue。Issue负责人在保持自身工作区的同时取得独立候选checkout，或把请求交给专门reviewer成员；后者只承接验收执行，PR实施者继续修复和发布。

验收者检查固定候选的代码行为、逻辑与边界，并独立运行应用取得浏览器观察；有缺口时说明，不将“已执行”自动解释成Approved。结论保存候选Git身份、需求依据、观察和证据。继续修改后的候选发新请求；旧请求的结果保留，但引用、提交或需求变化会使其不适用。明确依某次Approved整合时用merge --review守住这些条件。

请求Completed或有原因地Cancelled才结束该责任，PR关闭不替代它。有限本地运行在公开交付范围完成之外，还等待所有明确请求结束及已经接受的执行结清；这些状态仍不证明应用质量。CLI与恢复细节归[本地契约](../20-product-tdd/local.md)。

### Close, Merge, Reopen, and Unassign

Issue unassignment is debounced; once settled it retires the active Issue Agent
Group. Closing an Issue, closing a PR, or merging a PR does not interrupt a
current turn. It grants at most one Finalization Turn, then a closed Issue or
closed-unmerged PR sleeps and a merged PR retires. A mention on a closed Work
Item does not wake the sleeping group; Reopen is the designed re-entry. Reopen
rematerializes Context and starts one ordinary debounced turn. Duplicate
deliveries never grant extra finalization turns.
