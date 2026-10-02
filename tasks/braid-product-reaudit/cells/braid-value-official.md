# 官网两题的 Braid 价值：工作记忆、协作、设计交接

本审查只看 2026-09-27 官网生成归档：GitHub `435b79927a47`、Sheet `bd7ac1b232ba`。对象历史取自 [`github.sqlite3`](../../../runs/official-collaboration-review/github.sqlite3)、[`sheet.sqlite3`](../../../runs/official-collaboration-review/sheet.sqlite3) 的 `local_activity`，当前可见状态取自 `local_items` / `local_comments`，物理上下文取自 [`github/source-workspace.zip`](../../../runs/e20260928-completed-replay/github/source-workspace.zip)、[`sheet/source-workspace.zip`](../../../runs/e20260928-completed-replay/sheet/source-workspace.zip)。后续本地 08/09 热修复不倒写成官网行为；历史官网评分也不是 Braid 单项效果实验。

## 工作记忆：判断留住了，纠错没有替换旧输入

**期望。** Issue 保存当前需求、契约与验收依据，评论线程保留讨论轨迹；过时内容经编辑、hide 或 resolve 后，不继续与当前决定以同等权重进入接续上下文。

**实际收益与代价。** 两题根 Issue #1 都形成可追溯协作记录，GitHub 有 31 个顶层评论和 68 条回复，Sheet 有 21 个顶层评论和 39 条回复；各自均无工作项正文编辑、hide、resolve 或删除。归档晚期根 Issue 物理 `context.md` 分别约 108KB、78KB，仍含早期评论。可复核的 ZIP 成员分别是 `template/.factory26/20260927-080209-0b57147a/braid-state/physical/01a0e39b-cafe-7a61-9171-cff6b03ae638/context.md` 和 `template/.factory26/20260927-082825-d9c4f6ea/braid-state/physical/01a0e3c1-0164-7562-a054-e04c237b1c17/context.md`。GitHub 根评论 #51 错称 Issue #6 的 PR 基础已合入；#55 在 72 秒后明确纠正，但 #51 仍可见，并出现在晚期上下文。Sheet 根评论 #44 指向“由 #6 的 `validateWrites` 供 #5 复用”；#80 改判以 #5 的 `validateEntries`/整表端点为契约源，#6 应删除重复实现，两条都留在根上下文。这说明 Braid 留住了纠错证据，同时也继续携带被推翻的指示。`context.rs::render_complete` 全量投影可见评论、PR 还投影关联 Issue；`ContextPressure` 只标压力，不截断。这是上下文负担和混淆机会，不等于证明每次 provider 请求都完整吞入这些字节，更不能单凭旧评论断言后续错误由其造成。

**有效采用的反例。** Sheet Issue #2 的评论 #29 因 bash 反引号损坏标识符，被以“正确版本见同线程 #30”为理由 hide；#30 给出完整函数/调用约定。Sheet Issue #3 的 11 次、Issue #5 的 4 次及 PR #1/#9 的 1/3 次 resolve 把已处理线程折叠，Issue #3 线程 #127 在 resolve 截止 #135 后仍有新回复 #141 可见。机制真实可用，且局部把坏输入从默认投影移走。因此根 Issue 的问题是**未采用/不易发现**，不是全局缺 hide/resolve 能力，也不能要求为了指标隐藏所有历史。#51/#44 各含其他有效信息，整条隐藏可能丢证据；更合适的是编辑具体错误句、保留指向更正的理由，或把当前契约升入工作项正文再折叠已结论线程。

**机制与强度。** 归档 42 个 GitHub、67 个 Sheet 根 Issue 物理 `instructions.md` 均未提到 hide/resolve；只提示 view、comment/reply、timeline 等。CLI 能力并非不可发现：Sheet 子项实际调用。当前 `sources/braid/src/group/provider.rs` 已新增“description 当前说明、comment 增量、hide/resolve”的引导，但官网旧物理输入没有这段，尚无真实 09 采用效果。观察强度：对象历史和上下文投影为高；旧信息是否改变某次模型决策为未证。尤其 Sheet #6 后来读到新契约却因旧 `develop` 可测而选择旧形状，另两条后续纠偏未送入仍运行会话；见[共享契约因果](../../experiment-infrastructure/cells/shared-contract-braid-causality.md)。不能把它简化成“hide 少导致错误”。

**决定。** 当前新引导须用一次真实接续验收：先识别已被推翻的决定，再看是否修正原位置/当前正文，以及新成员是否按新口径行动。Braid 应提供可见投影与可靠投递，业务上哪句过时由成员判断。若仍反复错读，应比对“原样历史 / 编辑后带纠错链接”两种输入的决策与上下文成本；不以压缩率或 hide 次数作为成功标准。

## 多 Agent 协作：并行产出存在，依赖与通知成本也存在

**期望。** 子项独立推进，共享基线和契约及时送达；主负责人能在真实提交上整合成果，避免等待、重做与冲突扩大。

**实际收益。** GitHub 根 Issue 在基础 PR #1 合并后，于 08:56:57–59 UTC 指派 Issue #3/#4/#5 给三个成员；三条子任务执行窗口重叠，随后有 PR #4、#7 等合入。Sheet 根 Issue 于 08:34:02 同时指派 Issue #2/#3；公式引擎 PR #2 于 08:57:54 合入，共享基础 PR #3 于 09:36:26 合入，之后再整合。Sheet PR #1 的独立整合者 @glm-7 不只“挂名”：收到根 Issue #48 的职责与验收触发条件，在 #56、#97、#105、#137、#170 对连续候选提交复验并记录证据；根负责人在 #62、#108、#175 等处消费/裁决，最终由 `pr:1` 合并。这是并行、依赖对齐、成果整合都被实际使用的正例。

**代价与失效。** GitHub 首批子任务的状态信号不足，根在 #18/#23 等处反复检查并重新指派；不能从重派次数单独推断子成员无效。Sheet #5/#6 的校验契约并行分叉：新裁决 #71/#78 在旧 #6 会话运行中发出；恢复后被读到，但 #6 为复用可测试旧实现仍选择旧形状；#109/#118 后续纠偏又未进入仍运行的会话。这里同时有人的/模型的取舍问题、分支发布时序与历史 Braid 运行中输入投递缺口，详见[因果核查](../../experiment-infrastructure/cells/shared-contract-braid-causality.md)。Root 中大量“收到、无行动项”回执增加可见历史，但没有逐请求 token 和受控对照，不能分摊耗时或称全部通知为浪费。

**机制与强度。** `assignments`、`turns`、`local_merges` 能证明并行窗口、成员归属与合并；PR #1 具体评论证明根和整合者双向消费。它们不能给出“若不使用 Braid 的净墙钟/质量差”，也不能把公式引擎先于共享基础合入自动判为错误，必须看最终集成。现有运行中 steer、通知收件、Context 修正针对已确认缺口，但此官网快照不验收新版本。

**决定。** 优先用真实新任务验证“关键裁决送达 → 被引用 → 对应分支/验收改变”，并记录从依赖发布到合并的等待及重复检查。可消融的是窄通知/运行中投递或结构化交接，相同需求、角色、模型与工作区条件下比较；不能用单轨迹宣称去掉 Braid 更快。

## 设计与实施分离：有整合复验交接，功能实施前分离未建立

**期望。** Issue 先形成需求、技术和验收依据；独立 PR 负责人在自己的上下文中消费依据、实施/验证、回传证据，由 Issue/根负责人审阅整合。PR 数量或指派本身不算实现分离。

**实际。** GitHub 9 个 PR 中只有 #8/#9 曾指派 PR 成员；Sheet 11 个 PR 中只有 #1。GitHub PR #7 由 Issue #6 成员 `deepseek-11` 在 11:10:38 创建、11:10:47 由同一 Issue 会话合并，没有 PR assignment/worktree；Sheet PR #2 由 Issue #3 `glm-3` 在 08:57:29 创建、08:57:54 合并，亦无 PR 成员。[会话边界核查](issue-pr-session-boundary.md)给出 writer group/turn。**GitHub PR #8 也不是“实施前交接”的正例**：Issue #7 成员 @deepseek-10 在 10:57 起已写后端、前端和检查，11:16:06 的 WIP `d00c0ba` 已含 13 文件约 2471 行新增；PR 于 11:16:20 才创建/指派 @deepseek-12。后者确有实质集成和修复、在最终 head `3e61a4a` 自检并以 `pr:8` 合并，故可证明事后接手与 PR 阶段验收，而非最初实现由独立 PR 成员承担。根还在 Issue #7 评论 #166 接管集成。Sheet PR #1 则是从定义上负责 develop→main 的独立整合与最终复验，不能当 feature 实施分离证据。详见[PR 交接时序](pr-handoff-timing.md)。另一个反例 GitHub PR #9 虽指派 @glm-13，却在其首次回帖 #284 前，由根 Issue 会话于创建后约 23 秒合并。故“有指派”甚至“有 PR 阶段检查”都不能替代按时间核对谁先写了功能、谁消费设计和最终候选。

**机制与强度。** Braid 的 `pr create` 可不指派，Issue clone 能 commit/push，merge 允许有效 writer 处理关联 PR。这是灵活 Git 协作能力，不是缺 PR 对象；官网 Factory 指引与创建回执没有清楚说明“创建 PR ≠ 已交给独立负责人”。PR 关联 Issue 的上下文投影提供设计材料，但未指派时不会自动产生独立 PR 会话；指派后还需观察真实阅读、修改、验收与回传。PR #8 的原生 `write`/`edit` 时间和 WIP Git 提交足以确定 Issue 先实施，最终集成提交的每行作者则无法由 SQLite/Git 作者栏准确分摊。09 已在 Factory 五份指令、provider 与 CLI 回执上明确交接，见[边界报告](issue-pr-session-boundary.md)；这只是修复装载，旧官网数据不证明其有效。

**决定。** 下次真实新 PR 逐链验收：Issue 的设计/初始条件 → 创建且指派的 PR → 独立 PR context/worktree → 负责人引用设计、实施及对 head 验收 → Issue/根负责人消费结果。保留未指派 PR 作为 Braid 通用能力，不强制自动选模型或禁止根负责人合并；Factory 本轮也未决定“轻量 PR 可跳过独立交接”的新例外。

## 全对象覆盖与口径

表内 `C/R` 是历史顶层评论/回复动作；`E` 是工作项 title/body 编辑，`CE` 是评论编辑，`H` 是 hide，`V` 是 resolve。`local_activity` 与快照 `local_comments` 交叉检查；所有对象删除动作均为 0。`E` 不能细分标题还是正文；没有编辑动作的根 Issue 可以确证未改正文。仅有动作不证明后续模型采纳；仅有当前可见状态也不能反推从未编辑。

| 官网 | 对象 | C/R | E/CE/H/V | 当前说明 |
| --- | --- | ---: | ---: | --- |
| GitHub | Issue #1, #2, #3, #4 | 31/68, 10/3, 32/14, 25/10 | #3 CE1，其余 0 | 全部评论可见；根 #1 无整理 |
| GitHub | Issue #5, #6, #7 | 7/1, 45/4, 9/21 | 全 0 | 全部评论可见 |
| GitHub | PR #1–#4 | 0/0, 1/0, 0/0, 0/0 | 全 0 | #2 有 1 评论 |
| GitHub | PR #5–#9 | 0/0, 0/0, 0/0, 2/0, 1/0 | #8 E1，其余 0 | #8/#9 有独立指派记录 |
| Sheet | Issue #1, #2, #3 | 21/39, 8/2, 11/17 | #2 H1；#3 CE1/V11 | #2 一条 hidden；#3 十一串折叠 |
| Sheet | Issue #4, #5, #6 | 18/19, 4/4, 14/17 | #5 V4，其余 0 | 根 #1 无整理 |
| Sheet | PR #1–#4 | 12/17, 0/0, 0/0, 0/0 | #1 V1；#3 E1 | #1 有独立指派记录 |
| Sheet | PR #5–#8 | 0/0, 0/0, 0/0, 0/0 | 全 0 | 无评论 |
| Sheet | PR #9–#11 | 4/1, 5/2, 1/0 | #9 V3；#10 E1 | #9 三串折叠 |

覆盖全部 GitHub 7 Issue/9 PR、Sheet 6 Issue/11 PR；细读仅限上文决定性链条，并非逐条语义审判全部评论。零 hide/resolve 在某些短 PR 或纯历史记录中可完全合理；本报告只对明确被纠正而仍持续投影的内容提出整理机会。没有“无 Braid”对照、逐次 provider payload/注意力证据，也没有把官网结果按 Braid 单项归因的可信比例。下一轮要区分的是：机制不能表达、说明不足、Agent 不采用、采用后无效果，以及该工作项本不需要该机制。
