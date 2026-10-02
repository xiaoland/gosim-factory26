# Issue 设计与 PR 实施的会话边界

## 结论

官网两题的多数 PR 确实没有独立 PR 成员，并非网页漏显示负责人。GitHub 归档 9 个 PR 中只有 #8/#9 有 PR assignment；Sheet 归档 11 个 PR 中只有 #1 有。未指派 PR 仍是有效的关联与 Git 合并对象，但不会触发 PR driver 建立成员、上下文和独立工作区。当前 Braid 提供“可指派”的机制；Factory 产品目标要求 Issue 承载需求/技术/验收设计、PR 承载实施和验收，但运行指引没有明确要求进入实施前把 PR 指派给独立成员，所以实际执行容易沿 Issue 会话直接做完。

具体链条（只读 `runs/official-collaboration-review/{github,sheet}.sqlite3`）：

| 归档对象 | 创建与合并活动 | 执行身份/物理会话 | PR 会话 |
| --- | --- | --- | --- |
| GitHub PR #7，Issue #6 的 PR 基础 | `local_activity` 11:10:38.531 `deepseek-11` 创建，11:10:47.717 同成员合并至 `f52ade5e`；`local_merges.head_commit=8cc8657d`、`writer_node=issue:6` | `writer_group=01a0e27e-40d2-7af3-9a08-33676c7e55e3` 对应 `issue_agent`、`pi-deepseek-fast`，merge turn `01a0e27e-51a7-7b51-a3a2-e0ca745e18cc`；Issue 工作区已登记 | `assignments` 与 PR worktrees 均无 `pr:7` |
| Sheet PR #2，Issue #3 公式引擎 | 08:57:29.320 `glm-3` 创建，08:57:54.460 同成员合并至 `44f245f1`；`local_merges.head_commit=214affd4`、`writer_node=issue:3` | `writer_group=01a0e1ff-f39b-7fd3-9ad0-78862990dcaf` 对应 `issue_agent`、`pi-glm-fast`，merge turn `01a0e1ff-f9cd-7d41-a26d-be3b32b2e979`；Issue 工作区已登记 | `assignments` 与 PR worktrees 均无 `pr:2` |

这些记录证明创建和合并发生在 Issue 成员会话，PR 没有独立会话。SQLite 不记录每个源码编辑动作；PR head 指向 Issue 的发布分支，但不应仅凭活动行推断全部代码由同一物理会话写成。官网归档日期为 2026-09-27；不能倒推它当时收到 2026-09-28 的当前指令原文。当前指令仍保留了使这条路径可重复出现的含混边界。

## 机制与方法的责任

`objects.rs::create_pr_with_options` 接受可选 assignee；为空时不会发 Assign 事件。`store::assignment_candidates` 只对显式指派的目标建立责任/成员；`group/pr_agent.rs` 仅在 PR assignment 后按 PR head ref 建立独立工作区。Issue 则由 `group/issue_agent.rs` 持有自己的 clone，可以普通 Git commit/push 发布分支。`group/provider.rs::issue_system_prompt` 明确告诉 Issue 成员可创建、关联并合并 ready PR；`merge_with_match` 验证当前 writer 有效但不要求其是该 PR 的负责人。这允许 Issue 或整合者在需要时合并，属于有意保留的协作能力，不宜变成禁止跨工作项 merge 的权限规则。

当前 `variants/pi-braid/agents/pi-{glm,deepseek}-fast/instructions.md` 首段说 Issue 做需求/方案、PR 做实施，但没有说明“实施前创建并指派 PR，交由 PR 成员实施”；第二段只说按工作内容选择负责人。一个模型可以创建一个未指派关联 PR，在自己的 Issue clone 实施并合并，同时在字面上满足“使用关联 PR 完成实现”。这是 Factory 方法没有把设计/实施的会话交接说清楚，不是 GitHub 式 PR 对象本身允许未指派的产品错误。Braid 的 `pr create` 原输出只列 ID、head/base，也没有提醒未指派意味着没有独立会话。

## 最小修复与验收边界

本次已在 `sources/braid/src/cli/mod.rs::print_pr_created` 增加创建回执：从实际保存的 PR 再读 `assignees`，文本和 JSON 都以协作者语言说明工作已交给具体负责人独立处理；未指派时说明尚未交给独立负责人，并给出 `braid pr edit ID --add-assignee NAME` 入口。回执不提 runtime、物理会话，也不承诺负责人已经开始执行。再读保存状态是必要的，因为 `request_id` 幂等重试可能返回已有 PR，其 assignee 已改变；不能由本次命令参数猜测。JSON 原有 ID/head/base 字段保留，新增 `assignees` 与 `assignment_note`。`cargo check --bin braid -q` 通过；没有新建 Factory 测试或运行实验。

Factory 指令应说明：Issue 成员先在 Issue 形成需求、技术与验收依据；进入实施工作前，创建并指派 PR，把方案与初始条件交给 PR 成员；PR 成员在自己的工作区实施、验证、留下证据，Issue 成员负责协调、审阅和整合结论。已有可发布代码可作为 PR head 交接，PR 成员应承接/核验而非重做。这个规则不应自动选模型，也不取消 Issue 或根整合者的 merge 能力。Braid 允许未指派 PR 是对象能力；本轮 Factory 方法没有据此新增“轻量 PR 可跳过独立交接”的例外。主线负责当前五份指令与 provider 的文案，本 cell 只记录边界和已落地 CLI 反馈。

09 验收应从一个真实新 PR 的链条观察：创建时 `--assignee` 及回执、`assignments` 登记、PR driver 的独立 provider session/worktree、PR 成员在相应 head 上的行为与 Issue 成员消费交接；仅看 PR 数量或模型数量不能证明设计/实施分离。官网快照只说明旧运行的缺陷，不证明 09 指令已生效。

## 主线集成

两 variant 共五份主成员 instructions 已实际更新，不再只是建议：实施前创建并指派关联 PR，由独立 PR 成员承接计划、排障、实现、验收；Issue 保留设计依据与协作决定。Braid provider 增加创建工作项与指派独立成员的区别，CLI 文本与 JSON 给真实 assignee 和交接入口。Factory 技术说明同步此责任边界。五份指令已同步至 WSL09/code，经恢复包 refresh-native-materials 装入；旧普通 base 保留原始哈希并由增量记录说明替换。最终编译/运行身份以09恢复记录为准，源码落地不能替代真实独立PR会话证据。
