# Braid 通用协作边界补充审查

范围：2026-09-24 当前 `sources/braid` 生产代码与 Agent 指引；只读追踪。已知的根 Issue 关闭、`seal_delivery` 与 Factory 导出耦合见 [`run-boundary.md`](run-boundary.md)，这里不重复。下列是代码表达的行为与可能后果，不等同于某次运行中已发生的协作结果。

## 关键发现

1. **所有 PR 的接受权固定在根 Issue #1，关联子 Issue 只能收到消息。** `objects.rs:1110-1149` 的 `ready` 检查 PR 工作树干净、HEAD 与记录分支一致，再经 `changed` 通知关联 Issue；`objects.rs:1047-1097` 的关联和 `:886-918` 的 Issue 上下文让子 Issue 看见 PR。但 `objects.rs:1250-1279` 的 `merge` 只接受 `issue:1` writer，且固定在 `issue:1` 工作树集成；`group/provider.rs:77,91` 同样要求根 Issue 判断合并。故只关联子 Issue 的 PR 可以由子 Issue 讨论和验收，却必须另等根 Issue 实施最终接受，普通子 Issue 不能自治地完成其 PR。单一交付 ref 的原子 Git 集成是合理机械约束；“谁判断接受”是工作流权限，不能由该约束自然推出。建议保留集中集成与 ready HEAD/冲突校验，去掉根 Issue 独占操作权，由获得任务授权的成员发起合并；Factory 指引由负责该范围的 Issue 成员判断接受。继续使用已有写入身份，不另建审批或授权策略系统。集成工作树的位置与操作者身份分开处理，细节在实施准备中确认。

2. **初始唤醒把需要 PR 的工作泛化成所有任务的交付前提。** `local.rs:293-301` 调 `objects.rs:114-140` 初始化根 Issue，并发“通过 PR 交付”；`group/issue_agent.rs:98,408`、`group/pr_agent.rs:159,350` 与 `group/dispatch.rs:150,181,352,359` 将 `group/provider.rs:72-92` 的角色提示送到新建、重开和重置会话。设计与实现分离是用户明确的 Braid 产品目标，Issue 管设计、PR 管实施应保留；它不意味着每个 Issue 都必须创建 PR，也不意味着每个任务只有一次阶段交接。应去掉初始化消息中无条件的 PR 交付命令，让纯分析或讨论可以形成自己的结果；实际需要实施时使用 PR。不能为了比赛无关而把 Braid 退化为没有产品职责的通用对象存储。

3. **创建 PR 的事件文案把对象操作解释成实施授权。** CLI `src/cli/mod.rs:649-658` 调 `objects.rs:975-1045`；显式指定 assignee 时在 `:1023-1032` 发 Assign，引用写“已授权实现、自检和本地提交”。对象创建和指派足以启动执行，但不证明提出该 PR 的人有权扩大任务范围。此消息可能把“已有工作项”误作用户授权，尤其当 Issue 内容发生变化时。最小方向是改为事实性事件（“PR 已创建并指派；请读取关联 Issue 和当前授权范围”）；保留指派唤醒与 writer 约束。`--issue` 至少一个（CLI `:205-206`、objects `:1003`）是明确的可追溯关联约束，单凭本审查不建议删除。

4. **运行宿主约束被固定注入每个 Agent 的通用提示。** `group/provider.rs:60-70` 生成的 `local_instructions` 经上述会话路径送入所有 Issue/PR Agent，直接声明“本次隔离仓库”“禁止 push”“无人中途介入”及本地 commit/merge 的授权。它适合当前 Factory 的隔离、无人值守执行，却不是 Braid 对任意本地项目可推断的事实；若复用该 runtime，可能与用户/宿主的 push 或人工审批政策冲突。最小方向是保留真实 worktree、CLI、成员目录和事件接续说明，将仓库隔离、push 与交互政策由调用方显式提供；不要由 Braid 提示词自行授予 commit/merge 权限。

## 未发现的直接比赛依赖与合理机制

生产路径中未找到 ARC 布局、评分字段或 Factory 路径的判断。`local.rs:24-40,157-204,257-318` 的 `run_id` 是持久运行身份，`state` 在仓库外、所有 profile 共用一个 Git workspace、`delivery_ref` 是合法本地 ref；`objects.rs:125,272,302` 的 `local/run` 是内部仓库显示身份，并非比赛目录。单仓库/单 ref 是当前 Local 产品形状，若要多仓库才需扩展。`objects.rs:615-649` 的讨论通知、`:1047-1097` 的关联失效与唤醒、`:1115-1138` 的 ready 提交校验以及 `:379-427` 的显式指派属于必要机械约束，未发现它们强制评论数、子 Issue 数或设计阶段模板。

Agent 维护文档仍有 Factory 接受语境：`sources/braid/AGENTS.md:3,46` 与 `docs/20-product-tdd/local.md:86`。这不是运行时调用链，却会把 Factory bench 当作 Braid 开发的权威验收；最小文档处理是将比赛接入验收说明归 Factory 文档，Braid 只说明自身 Local 契约。本文不主张据此改动 SVC、Factory 或 Braid 源码。
