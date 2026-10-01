# I14 reviewer 实施准备

2026-10-02。本文是已认可 [机制](mechanisms.md) 的有界实施预演，供 I14-0 实施者使用。主线已转达用户对实现、基础验收和实验启动的授权；具体实验配方和授权原话归 [packet](packet.md)。本文只细化 review 接缝，不持有 cleaner、tester.army 或实验矩阵，不修改实现，不运行模型或测试。源码定位基于本次读回；后续并行改动可能移动行号。

## 实施决定与对象边界

新增内部 `work_items.kind='review'` 执行节点，每个 review 请求一个稳定节点，例如 `review:7`。公开操作仍归 PR：`pr request-review` 和 `pr review …`，不把它包装成新 Issue，也不把它放进普通 Issue/PR 列表。节点复用现有以 `work_item_node_id` 为键的 assignment、wake batch、turn、member、provider session 和 clone 记录。一个节点仍只有一个活动负责人。PR 的实施节点、assignment、成员、会话和工作区保持自己的身份。

这项选择已由主线确认。把 review assignment 挂到同一个 PR 节点，会撞到现有唯一索引，并迫使停机、改派、claim、writer、reset 等大量路径再携带角色过滤；本轮不走该路径。新节点只服务 review，不新增通用执行范围、角色协调器、投票或审批框架。

`ReviewRequest` 是权威数据。建议将它与对象事务放在新的 `src/objects/review.rs` 子模块，保留 `objects.rs` 内部 writer、通知和 activity 复用能力；用 Rust struct/enum 穿越内部边界。旧 `context::ReviewSnapshot` 表示没有候选提交的历史 review 展示形状，不直接借其名字或字段充当新请求。

| 数据 | 首版必须保存的内容与理由 |
| --- | --- |
| 请求身份 | 请求 ID、内部 node、源 PR、验收 Issue、请求者具体 member/agent/turn、创建时间、幂等 request key。重试不重复创建责任。 |
| 固定候选 | 请求时 origin 的规范化 base/head ref 与完整 commit，必要的冻结 tree 身份。不可用 ready_commit 或当前 clone HEAD 替代。 |
| 需求依据 | 验收 Issue 的目标正文/依据入口快照及其内容 digest；正文 revision 可作定位，不能单独作版本证明。正文已会被覆写，旧 review 需要保留当时依据。 |
| 执行责任 | `IssueOwner` 或 `AssignedReviewer`，责任 revision。后者使用节点 local_items 的 desired profile/member/assignment revision；前者关联验收 Issue 当前责任，不复制该 Issue 的 assignment。 |
| 终态 | `Pending / Completed / Cancelled`；Completed 还必须有审阅者明确提交的 verdict、正文、证据入口、实际 checkout commit/tree 和脏文件观察。running/blocked/sleeping 从现有执行事实取得，不另建同名状态机。 |
| 结论 | `Approved / ChangesRequested / Inconclusive`，请求一次终结。继续修复后发新请求；评论讨论不覆写原结论。保存历史结论不等于它仍适用于当前候选。 |

`work_items.state` 仅承接责任生命周期：Pending 对应 OPEN，Completed/Cancelled 对应 CLOSED。请求状态、verdict 和 checkout 事实保存在新 typed 表；不要把 verdict 塞进 `state_reason` 或 PR draft。`local_items` 对 review 只提供已有执行路径需要的 title、body、desired assignment 等，不成为另一份候选/结论权威源。

请求时恰好一个适用关联 Issue 才可默认选择；零个、多个或没有可用负责人时返回具体原因，多个要求 `--issue`。不得默认根 Issue。Issue 当前负责人可直接处理，新的 Issue assignment 在其上下文中仍能看到未完成请求。Issue 改派使旧 writer 失效；当前新负责人取得默认处理权。专门 reviewer 的执行权只来自该请求节点当前 assignment，不从“能写任意对象”推导。

## 最小公开动作和职责核验

建议本轮收敛以下具体命令，避免把 request、执行和结论混为一个动作。PR 参数是源 PR；请求 ID 必须显式，不能由“最近 review”猜测候选。

| 命令 | 事务和责任边界 |
| --- | --- |
| `braid pr request-review PR [--issue ISSUE] --request-id KEY` | 检查当前 PR 实施 writer、源 PR 和关联 Issue，解析 origin base/head，冻结依据，创建请求及内部节点；在同一对象事务记录 activity 和向验收 Issue 当前成员投递请求入口。独立于 `pr ready`，不修改 draft。 |
| `braid pr review list PR`、`braid pr review view PR REQUEST` | 返回 typed 请求、结论、执行事实与当前 freshness；按当前 origin base/head 与当前需求 digest 比较，给出具体不匹配原因。保留过时结果。 |
| `braid pr review assign PR REQUEST --assignee MEMBER` | 仅验收 Issue 当前负责人或明确宿主输入可委派；从当前具体成员目录选择 reviewer profile。只改 review 节点的 desired assignment 并产生 Assign/Unassign，不编辑 PR assignee。 |
| `braid pr review checkout PR REQUEST` | 为当前责任 revision 取得独立冻结 checkout，返回 path/commit/tree；不切换 Issue 或 PR 工作区。重复调用同一 revision 不复制新 checkout。 |
| `braid pr review conclude PR REQUEST --verdict … --body-file FILE` | 核验请求和 PR 对应、Pending、当前执行责任以及责任 revision；从登记 checkout 取得实际 commit/tree/脏文件事实，保存明确 code review 与浏览器观察/证据入口、verdict，关闭 review 节点，通知 PR 实施者和验收 Issue 当前负责人。 |
| `braid pr review cancel PR REQUEST --reason TEXT` | 验收 Issue 当前负责人或宿主显式放弃请求并留原因，关闭独立责任。不能以 PR 关闭静默抹掉请求。 |
| `braid pr merge PR --review REQUEST` | 仅在用户/Agent明确依该结论合并时要求 Approved、请求匹配该 PR、当前 origin base/head 与依据均匹配。未传 `--review` 的原有合并策略保持现有语义。 |

命令中证据的具体编码可复用 `--body-file` 与明确的文件入口；不因此建设检查结果平台。需要 typed 的是候选、责任、终态和事实来源，不能让任意 JSON Value 在内部代替这些契约。approve 的产品指引必须要求代码判断和浏览器验收；确实不适用的验收项明确说明原因。原生 turn completed 或没有工具错误都不能自动形成 Approved。

新增窄 tag `reviewer-only`，沿用现有 `root-only` 的目录模式：普通 assignee 目录/Issue/PR driver 排除该 tag，专门 reviewer 目录和 Review driver只选择该 tag，`assignee list --reviewer` 取得可指派的具体成员名。默认 IssueOwner 路径不要求 Issue profile 有该 tag。不引入可配置角色权限系统。Frozen request.json 仍是 profile 来源，不从运行后编辑的 agents 文件重装 profile。

现有 `LocalObjects::writer` 证明活动原生 turn 与 assignment 的绑定，但普通 `edit` 并不等于“只有此对象负责人可写”。新命令必须显式检查 `writer.node`、当前 Issue 责任或 review assignment revision。`--external` 只保留现有明确宿主输入用途，不用它伪造 Agent 身份来验证权限。

## 执行、通知、上下文与 checkout

默认 IssueOwner 路径没有第二个 member/session：请求和未决入口进入验收 Issue 的规范上下文，真实请求通知复用其 wake batch，现有会话执行验收并向同一 `ReviewRequest` 提交结论。委派之后，原 Issue 会话仍能查看/讨论请求，但不再拥有提交该请求终结结论的执行权。改派事务增加责任 revision；旧在途结论提交必须失败，不影响其处理 Issue 自身设计讨论。

AssignedReviewer 路径使用新 `GroupKind::Review`、`pr_reviewer_agent` role 和窄 `group/review_agent.rs` materializer；现有 SessionFactory、GroupDriver、SessionManager、预算与 native 生命周期照常使用。materializer 只负责取得请求投影、冻结 clone、reviewer system prompt，并调用已有 assignment/start/complete 流程。重新委派只停止 review 节点旧负责人，不能停止源 PR 或验收 Issue。完成后使用已有 closed-idle sleep；明确联系可重新唤醒讨论，但 Completed 请求不能被恢复成新候选或再次提交结论。

复用已有 Assign、Unassign、Wake、Mention、Lifecycle 事件种类，不新增 review 专用调度器。请求和结论通知携带 `pr review view` 入口及请求 ID；直接投递 current concrete member 并按已有 recipient_revision 隔离。通知不能依赖 PR 显式 followers：关联 Issue 目前并不会自动获得 ready 通知。结论事实只保存一份；两处 activity/通知只是引用该事实。重复成员去重，自发通知仍按当前既有规则处理。

新增 `CanonicalContext::ReviewRequest` 与专用 snapshot/render/materialize，保留冻结要求、源 PR/Issue 入口、base/head、责任、未决事项和结论。Issue/PR 当前投影只增加相关请求的有界摘要和完整读取入口，避免内联所有证据、Issue 全部评论或原生 rollout。所有 context tier、revision 记录和 reset 路径必须处理新 variant。普通公开 `WorkItemReference` 继续只表达 Issue/PR；内部 review 不走现有 else=>PR 的 reference 帮助方法。

浏览器验收的 checkout 是必须单独落实的接缝。现有 `worktrees.agent_id` UNIQUE，Issue 当前会话已有 clone，所以不能把它的第二个候选 checkout 冒记为另一个 agent worktree。新增窄 `review_checkouts`，按 request + responsibility revision 登记 path、origin、固定 commit/tree、执行者及创建事实。Dedicated reviewer 的 path 同时登记到现有 agent-owned worktrees；IssueOwner 只有请求 checkout 记录，自己的 cwd/工作树不变。

复用 `worktree.rs` 的 clone、origin 核验、member identity 与 `.braid` 排除处理，但补 `provision_review`：从 origin 取得请求完整 SHA，并在独立 review 本地分支固定到该 SHA；克隆后及恢复时核实实际 SHA/remote，不能只核实分支名。请求创建前固定 base/head 的保留引用，例如 `refs/braid/reviews/REQUEST/base|head`，使后续强推/分支删除仍可取到原候选。保留引用只固定对象，不更新 PR/base 发布 ref；Git 失败不得报告请求成功。DB失败留下的独立保留引用可追溯为孤立产物，不伪装成请求或静默复用。

路径按 responsibility revision 分开。现有改派会接管旧负责人的脏 clone，因此 review 必须在 `begin_agent_assignment` 的 preserved-worktree 接缝排除跨 revision 继承，保留旧 checkout/证据，新的 reviewer 从原冻结候选重新取得 clone。同一责任的会话恢复仍用其现有 path，检查候选与污染事实，不静默 reset 掉证据。服务端口、浏览器数据与应用临时数据由该验收路径单独提供并记录；不得把 PR实施服务地址当作固定候选证明。新的 review 本地分支不发布到 PR head；需要改实现时交回 PR 负责人并发新请求。

## Forward migration 的具体边界

截至读回，schema 是 v16，`work_items` 自 v1 以来没有增列，定义仍是七列及 `UNIQUE(repository_node_id,kind,number)`；`kind` CHECK 仅 issue/pr。下一版迁移编号由主线统一占用，不能同时让 cleaner 与 reviewer 各自声明 v17。新 migration 增加 review 请求/checkout 表、必要索引、local_merges 的可空 review request 关联，同时重建 `work_items` CHECK 为 issue/pr/review。旧 migration 原文和 checksum 都保持不变，不回填任何旧 PR 的假 review。

现有 `store::apply` 在迁移前取得 lease、创建 SQLite backup，`configure_connection` 开启 FK；`apply_one` 先 `BEGIN EXCLUSIVE` 后执行 migration SQL。事务内 `PRAGMA foreign_keys=OFF` 无效。因此给本次已知需重建父表的迁移增加窄的事务外 FK 开关，不能全局关闭 FK：

1. 在 `BEGIN EXCLUSIVE` 之前记录并关闭此连接 foreign_keys；断言连接不处于事务内。保留现有 lease、backup 和逐版 checksum。
2. 事务内创建 `work_items_new`，完整复制原七列、主键与 UNIQUE；DROP 原表，再 RENAME 新表为 `work_items`。不能先 rename 旧表，否则 SQLite 会将子表引用改向临时旧名。现存 work_items 的唯一索引由原 UNIQUE 重建，没有额外显式索引需要丢失。
3. 增加新表/列后，在同一事务内运行 `PRAGMA foreign_key_check`，任何返回行带表名、rowid、父表、外键编号报错并 rollback；零行才写 schema_migrations 并 commit。
4. 成功和所有错误返回路径恢复 foreign_keys=ON 并核实。恢复失败必须显式报错，不留下以为受 FK 保护的连接。新连接仍照旧 configure。

直接外键原件包括 assignments、wake_batches、associations 两端、canonical_objects、events、write_intents、status_comments、issue_context_sources，以及 v3 local_items/local_comments、v12 local_subscriptions/local_activity；worktrees 与原生会话另通过 agent链关联。迁移前后独立读回每张现有表的行、主键、schema 外键目标和 FK check；不能只看新CHECK允许插入review。新表不能牵动旧记录ID、active唯一索引、旧PR draft/base/head、CLI binding或原生session身份。此处当前只确认源码条件，尚未执行迁移；实际完整性证据必须由实施后的正常迁移操作取得。

## 文件边界与 kind/收敛清单

以下清单包含必须改的路由和必须保持排除的边界。并行实施者先以当前源码重新定位，不能机械地把所有 `issue/pr` 字符串扩为 review。

| 所有者/定位 | 实施动作或明确排除 |
| --- | --- |
| `migrations/0001_initial.sql:22`，`src/store/mod.rs:24,6425,6490` | 只新增 forward migration 和注册；按上一节补父表重建路径。旧文件不改。 |
| `src/objects/review.rs`（新增）；`objects.rs:207,591,646,701,760` | typed请求事务、当前责任检查和通知。保留普通 public kind验证只接受issue/pr；内部 emit 的 execution kind及event_name显式支持review，不能自动认成pull_request。复用改派只针对review节点。普通对象编号分配只看issue/pr；review单独分配其kind内编号。 |
| `objects.rs:1101,1113,1149,1464,1544` | 成员路由继续按当前node/assignment工作；review通知标签和读取入口显式。reference与public canonical不能else=>PR；新增独立review canonical入口，普通Issue/PR reference不接受review。 |
| `src/cli/mod.rs:52,286,614,644,926,1016,1100附近` | 新PR动作、review子命令及只读识别；专用review文本/JSON输出，不通过现有Issue/PR print_item/字段表兜底。context review读取可提供给内部调度，公开入口仍提示pr review。新增字段按typed结果串行化。 |
| `src/context.rs:56,186,279,316,324,348,362,367` | 新CanonicalContext分支、完整/有界/引用tier、注释缩减、revision记账；Issue/PR增加review摘要。旧ReviewSnapshot不冒充新事实。 |
| `src/group/mod.rs`、`worker.rs:29,164,203,284`；新增 `group/review_agent.rs` | Review driver/materializer，恢复采用review冻结clone；只在本kind执行assignment，不以Issue默认路径恢复。 |
| `group/dispatch.rs:137,340,365` | reactivation、reset canonical和system prompt三处显式match；review不能落到Issue，也不能按PR实施head重新materialize。 |
| `group/provider.rs:74,91,102,121` | Issue负责需求+独立验收，PR负责实现+请求review；reviewer职责聚焦固定候选审阅。event/reset标签显式Review。共用协作规则继续使用，实施push指令不进入reviewer角色。 |
| `store/mod.rs:6287,6295,3767,4713` | kind验证、role映射、closed-contact reactivation的硬编码IN，以及完成assignment需active worktree的角色判断扩展review。closed-idle sleep本已按node通用，可复用；completed请求的对象写权限仍由review域禁止。 |
| `store/mod.rs:2990,3517,3589,3637,4843,5067,5178,5223,5584,5948` | resume/stop、assignment、lifecycle、reset、claim等已用kind参数过滤；在验证新kind后复用，核对SQL不隐含PR/Issue。不要改active assignment/wake/turn唯一键。 |
| `store/mod.rs:4375附近` | 改派的旧worktree继承仅对review跨责任revision关闭；停止/退休仍只按review node，不增加按PR源关系停止其它成员的动作。 |
| `worktree.rs:37,107` | 新冻结候选provision路径和恢复SHA核验；现有verify_existing只检查local branch与remote，不是冻结commit证明。旧Issue/PR路径保持原行为。 |
| `local.rs:260,509` | status的公开items只列issue/pr，review_requests单独有界展示；新增仅reviewer-only profiles的Review driver，Issue/PR driver排除此tag。physical session清单保留全部真实session及kind。 |
| `store/mod.rs:2857,5572` | tracked_work_items如果作为公开Issue/PR库存，必须过滤issue/pr；内部健康诊断另可显式含review。delivery_closed不能把review算成应用交付工作项，也不能因此在显式pending review尚未处理时提前终止调度。 |
| `evidence.rs:20,663` | portable对象快照加入新review表与checkout表；保留现有行事实和缺口语义。不能只有新CLI展示而恢复产物丢掉结论。 |
| `objects.rs:2026,2140`，`migrations`的local_merges扩展 | --review核验、merge intent保存request id；prepare和apply两处的ref/需求保护，见下一节。 |

收敛分两层处理：现有应用交付范围仍是根 Issue closed、所有公开 Issue/PR closed/merged及无未完成merge；review节点不进入这份公开对象判据。有限 Local invocation 的**停止取新工作**还需所有显式请求Completed/Cancelled，且review的在途turn/reset/队列按已有统一pending计数结清。可保持现有 `local_delivery_closed` 名字而在其SQL里显式两类条件，或抽一个窄停止判据，不能仅加 `kind IN ('issue','pr')` 就让pending review被提前关门。请求未委派时review节点OPEN而无assignment，不应成为blocked agent；它由IssueOwner的待办承担。cancel提供有原因的收敛出口，不把PR关闭当review通过。

association、parent_issue、closing_issues、PR默认draft、根Issue启动、delivery ref/app冻结仍只处理Issue/PR，不扩大到review。`objects.rs:815` 的Issue背景向关联PR传播保持其用途，不把内部review当PR；新请求依据变化由read/merge比较，不需要每次Issue编辑广播新的冻结候选。需要reset的只是review当前讨论可见性或责任材料，不覆写请求冻结要求。

## 候选检查与合并重试

view时计算freshness，不在push时改旧结果。head ref变、head commit变、base ref变、base commit变或依据digest变都明确列为不适用；缺ref/缺对象保留具体Git错误。conclude可以保存对原候选的结论，即使已过时，但不能显示成当前candidate获批。独立checkout的实际HEAD不匹配请求则不能提交该候选结论。

`merge --review REQUEST` 在生成新merge intent前检查所有绑定和Approved，沿用当前Git ref事务对head/base作CAS，不只补CLI的match-head。把request id保存在local_merges：prepared重试与自动恢复不能丢掉这是依哪次review准备的事实。首次apply尚未发布时再校验需求digest；当前ref匹配仍由已有Git事务保障。若merge已经真实发布，恢复只记录已发生效果，不能由于合入后base变化把既有成功误判成未发生或逆向回滚。当前already-contained与prepared重试分支也需独立处理，不让它们绕过新merge的review检查，或把历史已合入结果强行重新批准。

## 实施顺序与真实反馈

1. 主线先统一migration编号和worker文件责任。实施者先完成typed请求、内部node、migration及CLI读写；编译后正常执行新建和旧数据库升级，不先接模型。
2. 完成IssueOwner请求/通知/投影、checkout、结论、cancel和freshness。独立host真实操作覆盖一个/多个关联Issue、request重试、新head/新base/需求变化、旧结论保留、cancel及不使用ready触发review。原生身份权限仍需后面的实际运行取证。
3. 完成Review driver、reviewer-only目录、materializer、system/context reset/恢复与生命周期。复用assignment通用路径，在review改派接缝排除脏clone继承；对所有表中kind路由逐项收口。不要复制整个PR materializer再逐步维护两份实现。
4. 完成merge --review及saved intent保护、status/收敛/portable证据。做Git与对象独立读回，取得基础反馈，再进入主线批准的运行矩阵。

无模型基础反馈沿用已有draft任务的真实路径：编译 `cargo build --locked --bin braid --manifest-path sources/braid/Cargo.toml`；在新的隔离目录建立真实bare origin/应用clone，用正常Local初始化取得对象库，配置明确缺失的provider executable使其阻塞在启动前（保留真实blocked结果，确认零原生session），再用正常 `--external` CLI 操作对象与普通Git改变head/base，独立读取SQLite与Git refs。不得改I13运行数据库，不插入假agent/session/turn，不以mock、探针或基础设施测试替代反馈。现有draft原件可作为操作格式参考，不写入其数据库。

迁移反馈使用一份真实v16对象库的独立备份，并保留其原件。正常调用新二进制迁移；保存before/after数据库、schema_migrations、完整现有表/主键/FK目标读回、backup路径、FKcheck和错误stderr。compile通过或新表存在不足以证明历史图未损坏。固定候选checkout同样用普通Git独立读取HEAD/tree、origin和脏文件；推进/强推源head后原候选仍可取得，实施clone不变。

host操作能够证明对象事务、Git候选、迁移、结论历史与收敛条件，不能证明native reviewer已实际启动、权限revision阻断在途提交，或浏览器服务对应候选。后者在用户已授权的I14实验中取得真实native session/assignment/turn和应用浏览器证据：同一源PR实施者持续存在，默认Issue会话处理请求，专门reviewer独立身份开始并提交结论，责任改派后的旧提交被拒绝，源head/base变化让旧批准失效；保留实际路径、provider身份、GitSHA、错误和操作观察。不得用模型自报“独立”代替DB/进程/工作区事实。

I14-0不等待I13最终成果；其后续输入改进归I14-1。WSL共享5槽位、新run 2GiB、自有API且不使用ARC等实验限制由主线配方持有。源码实施无需读取隐藏评测。

## 需由实施反馈关闭的具体不确定性

迁移的SQLite事务/外键保持、private保留ref的克隆获取、review改派后的停止完成与跨revision脏clone隔离，都已经定位到明确源码接缝，尚未通过实际操作。首先取得这些反馈；失败时保留原件和具体错误，窄修边界，不自动换成通用执行框架。

需求依据首版冻结所选Issue正文及其显式材料入口，不能声称已追踪正文链接目标的全部外部内容版本。如果验收实际依据来自其他版本化文件，结论需记录其Git身份/入口；是否进一步自动冻结这些材料应由实际缺口决定，不先建立全依赖版本图。

应用服务和浏览器临时数据的独立性不能仅由worktree记录推出，必须由实际验收命令/目录/端口/进程及观察证明。首版提供独立路径和角色约定、记录使用事实；没有证据时结论应说明缺口，不添加通用服务沙箱或把缺口隐藏成Approved。
