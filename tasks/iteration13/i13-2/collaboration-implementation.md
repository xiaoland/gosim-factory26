# I13-2 协作实施与恢复输入

2026-10-01。接续[本轮 packet](packet.md)与[协作调查](collaboration-findings.md)，用户授权协作修正并热恢复，SVC 文档系统和 task packet 是新增强制验收要求。本线完成评论可见性、材料与最小 Console 兼容；没有恢复暂停容器、调用模型、官网评分或部署 Console，原保全副本保持不动。主线持有冻结、恢复、单实例部署和统一提交。

## 实施范围与当前结果

评论持久态仍属于每条自身。`objects.rs::comment_hidden_by` 从完整祖先链取得最近隐藏祖先，`read_comments` 将其作为共享可见性门；精准单条、thread、工作项和 Context 都不能因读取切片缺少祖先而恢复正文。`minimized` 继续表示自身 hidden，新增 `hidden_by` 与 `hidden_by_reason` 解释祖先影响。root hide 覆盖现有与未来后代，中间 hide 只影响该分支，unhide 不清除子项自身 hide；没有级联 UPDATE 或数据库迁移。delete 的正文不可恢复，resolve 的新回复合同与多 ID 事务校验保持原样。

普通 created/edited/mentioned 投递经同一祖先门拒绝隐藏分支，hide/unhide 等状态通知仍纠正参与者认识。已送达的原生历史和旧 rollout 不重写。在精准 ID 操作之外，`--edit-last`/`--delete-last` 的选择也排除被祖先隐藏的评论。Context 各档位只渲染有效可见正文并保留隐藏来源；显式 include-hidden 用于追溯。CLI help、JSON 可选字段和回执说明对应语义。

Console archive 的正常读取计算相同最近隐藏祖先，live 路径采用 Braid 的字段。Discussion 区分自身隐藏与祖先隐藏，指出隐藏来源；仅当用户明确展开该隐藏评论时取得追溯正文，整串已解决历史的 `expandedBody` 不能穿透隐藏门。取消隐藏操作针对自身状态，后代仍受其它隐藏选择约束。改动只在评论读取和展示，不建立新服务实例或修改其它界面/部署架构。

Braid 通用指令明确 description 承接本项目标、交付差异、依赖、仍欠义务和共同定义入口，长期产品/技术/操作规则归版本化文档或配置，当前判断/路线/恢复点归任务材料；Braid 不认识 SVC 产品。I13 基线及本轮实际 `pi-braid-i13-glm-root` profile 将 SVC 文档与 packet 明确为强制要求，触发独立技能读取。profile 只持有强制采用、开始/接续触发与独立读取入口；clone 根、任务材料与发布的详细方法由 braid-collaboration 持有：先用 `git rev-parse --show-toplevel` 确认当前实际 clone 根，读取/接续该根下的 packet，再实施；共享材料在依赖工作前发布，PR packet 随候选发布，集成后在 develop 可发现。AGENTS 只导航知识入口并记录适用开发规则，不复制 Harness 配方或文档正文。

braid-collaboration 及其 organising/closing reference 持有消费者、采用和发布的具体约定，未内联 SVC skill 正文。两 variant 的 ROOT_CHECK_MESSAGES 改为无新事实、决定或行动时结束；只在变化影响当前判断、下一步或交接时维护已有材料，不诱导固定公开回执。提示词与源码修正仅表示已实现指引，是否被本地模型采用仍须恢复后观察。

## 已有过程的新事实

[发布事实原件](../../../runs/iteration13/i13-2-20261001/collaboration-validation/svc-publishing-facts.json)保存完整 Git 命令回包、原生 cwd、packet write 的路径/时刻/hash，以及保留文件的身份。origin/develop `577d64b` 的四份 docs 真实已提交、已发布，并有 PR #2 和 PR #3 的实际读取证据。共同阅读入口 AGENTS 与已发布 tasks 缺失；根/PR #2 packet 位于运行的 work/tasks 中，仍存在却不属于独立 clone。git check-ignore 不排除 tasks，native cwd 本来就是正确 clone，未发现注入 work/tasks 的 Harness 指令。PR #3 的 packet 在其 clone 内，属于未提交的当前实施态。详见[补证](collaboration-findings.md#完整暂停工作树补证svc-发布缺口)。

这些观察区分了写文件、提交、发布与消费者取得；读取日志不能证明按合同实施，四份文档也不能替代缺失的 packet 与发现入口。本线没有修改已有应用来假装完成此项验收。

## 编译与实际操作

证据归 `runs/iteration13/i13-2-20261001/collaboration-validation/`；[身份与边界](../../../runs/iteration13/i13-2-20261001/collaboration-validation/validation-identity.json)保存原 DB SHA256、实际 CLI binary SHA256、退出值和隔离状态路径。所有写操作只发生在从原保存 DB 复制出的独立目录，未改原快照或暂停现场。没有新增或运行 Factory/Braid/SVC 测试、mock、probe、selfcheck。

| 消费者与边界 | 实际结果与原始入口 |
| --- | --- |
| 源码完整性 | `cargo build --bin braid` 退出 0；[编译日志](../../../runs/iteration13/i13-2-20261001/collaboration-validation/braid-build.stderr.log)保留 12 项既有 dead-code 警告。Console `pnpm build` 的 TypeScript/Vite 退出 0，保留现有 chunk-size 警告，见[回执](../../../runs/iteration13/i13-2-20261001/collaboration-validation/console-build-receipt.json)。 |
| 真实旧提醒回归 | 普通 Issue、精准 #3、thread #2 中 #3/#5/#7/#9 的 body=null、hidden_by=2/4/6/8；include-hidden 仍取得保存正文。[CLI 原始读取](../../../runs/iteration13/i13-2-20261001/collaboration-validation/cli-baseline.json)、[archive 原始读取](../../../runs/iteration13/i13-2-20261001/collaboration-validation/archive-baseline.json)。 |
| Full/CommentIndex/References | CLI 实际渲染三档；Full estimated_tokens=2046，8192 window 得到 CommentIndex/957，4096 得到 References/770。未显示旧隐藏分支正文。最初 1000/100 窗口因现有 1024 下限被拒绝，首次错误保留在 baseline，没有改参数边界。[分档回包](../../../runs/iteration13/i13-2-20261001/collaboration-validation/context-budgeted.json)。 |
| 分支与独立选择 | 实际创建 #14 根、#15 中间、#16 孙回复、#17 兄弟；hide #15 仅消除 #15/#16 正文，#17 可见；hide #14 后新增 #18 立即 hidden_by=14；unhide #14 后 #15 自身 hidden、#16 hidden_by=15，而 #17/#18 可见。[操作回包](../../../runs/iteration13/i13-2-20261001/collaboration-validation/cli-operations.json)。 |
| 通知与 @ | 隐藏根下新增 #18 @glm-2、编辑孙回复 @glm-2，events=35 与 deliveries=21 均未增长；unhide 状态通知仍保留。操作回包记录前后实际计数。 |
| last 选择 | 使用隔离副本中仍有效的当前成员执行身份创建 #20 可见根、#21 隐藏根和 #22 后代；`--edit-last` 实际编辑 #20，#22 保存正文未被改变、hidden_by=21，见[回包](../../../runs/iteration13/i13-2-20261001/collaboration-validation/cli-last-selection.json)。 |
| 原合同 | hide 17 999999 返回原始 Query returned no rows，#17 未部分隐藏；root+reply resolve 整批拒绝，根仍未 resolved。resolve 根后的 #19 body 可见且 folded=false；删除 #17 后 unhide 返回 deleted comment cannot be restored，include-hidden 仍只得 tombstone。含已删除 ID 的批量 hide 失败，#19 未部分隐藏。 |
| Console 正常/追溯读取 | 直接调用现有 server 的 item_view/braid_json 和 Archive 读取同一隔离 DB，未启动服务。live/default 与 archive/default 对原提醒及后代逐条一致；两条 trace 路径都取得 #2/#3 保留正文。见[实际读取回包](../../../runs/iteration13/i13-2-20261001/collaboration-validation/console-read-paths.json)。 |

`git diff --check` 在 owned 源码/材料通过。尚未覆盖部署后的浏览器交互、暂停模型对新指引的采用，以及恢复后真正发布 SVC 材料；这三项不能由编译或隔离 DB 操作宣布完成。

## 派生恢复包的维护输入

保留原 workspace.tar、原 DB、原生会话和源 work/tasks 文件。从完整快照派生副本中注入一条真实新根评论，保存维护正文、实际 created ID、DB/文件前后 hash 和事件来源，再随恢复包冻结。原件不动。使用现有 CLI，不增加消息配置接口，不改 Issue/PR description 触发重建：

```sh
braid --state /ABSOLUTE/DERIVED/braid-state --external issue comment 1 --body-file /ABSOLUTE/i13-2-maintenance.txt --json
```

建议正文如下；它只包含本次事实、材料入口与具体纠正，技能方法保持独立文件：

> I13-2 接续维护：用户要求必须使用 SVC 文档系统和 task packet。暂停副本显示 origin/develop@577d64b 已含四份 docs，但未有 AGENTS.md 与 tasks/。根和 PR #2 packet 已存在于本运行的 work/tasks/issue-1/packet.md、work/tasks/pr-2/packet.md，位于各自 Git clone 外；这两份仅作恢复来源，不代表已发布。请先读取独立 svc-documentation、svc-task-packet 与更新后的 braid-collaboration，核对原要求、当前已发布提交及已有 packet。在当前实际 Git clone 根（git rev-parse --show-toplevel）整理为可接续的 tasks/issue-1/packet.md，保留原文件和证据；补齐 AGENTS 阅读导航，将稳定定义、当前判断和本项交付职责放回各自材料。将共享文档、导航和根 packet 发布到 develop，使消费者取得适用提交；PR #2 已合入，其 packet 按真实完成状态保留可发现的收尾入口，勿改旧 PR description 来触发重建。联系当前 PR #3 成员取得该提交，接续其 clone 内已有 tasks/pr-3/packet.md 并随候选提交和 push 发布。不得以文件存在、已读技能或纯 ACK 代替实际采用；保留未知和原始失败。完成必要维护后继续原工作，没有新变化无需另发公开回执。

根应从现有 work/tasks 源材料恢复当前解释，不能从零创建空 packet。现有根 packet 已记 PR #2 合入、PR #3 指派，但仍把 Issue description 称作稳定决定权威；迁入正确 clone 时按新归属修正这项当前判断和过时入口，保留源文件作为证据。PR #2 的完成 packet 可由根整理为已完成收尾材料并引用既有评论 #10/#11 与原始证据，不复活已完成成员或重跑已取得结果。当前 PR #3 负责人接续原 packet 和在途实现，fetch 根新提交并采用对应材料，候选发布时纳入当前任务 packet；不得覆盖其未提交实现。

这段正文只适用于已核实的 Sheet 进度。GitHub 的[发布事实](../../../runs/iteration13/i13-2-20261001/collaboration-validation/github-publishing-facts.json)确认 origin/develop 与 braid/pr-2 均为 `726e21f`，已发布六份 docs，仍未有 AGENTS 与 tasks。根 clone 内保留九份未跟踪 packet/ 资料，state.md 是当前根任务记忆，开头的“勿提交 packet/”会妨碍共享交接；PR #2 clone 有未提交实现。其当前对象依据合并 WAL 的 forensics 副本，而非忽略 WAL 的原 base DB，Issue #1 和 PR #2 均 OPEN、负责人分别 glm-root-1 与 glm-1。采用同一 CLI 参数形状，正文改为：

> I13-2 接续维护：用户要求必须使用 SVC 文档系统和 task packet。当前 origin/develop@726e21f 已发布六份 docs，但未有 AGENTS.md 或 tasks/。根 clone 的 packet/state.md、packet/design-summary.md 与其它 packet/ 资料仍未提交；state.md 中“勿提交 packet/”不能继续作为共享交接规则。请保留这些原文件作恢复来源，先读取独立 svc-documentation、svc-task-packet 与更新后的 braid-collaboration，以当前实际 Git clone 根为基准，将当前判断和路线整理为 tasks/issue-1/packet.md，补齐 AGENTS 阅读导航，沿用六份文档的现有知识归属并核实缺口。把共享文档、导航与根 packet 发布到 develop，使消费者可取得适用提交。当前 PR #2 @glm-1 尚未发布实现候选，其 clone 有在途未提交代码；联系该成员取得新材料，从当前实现和已保存工作恢复本项 packet，在继续多步实施前于其 clone 根接续 tasks/pr-2/packet.md，并随候选 commit/push 发布。保留未提交实现、原始证据与未知；不要以文件存在、技能读取或纯 ACK 代替实际采用，不改 description 触发无谓重建。维护完成后继续原工作，无新变化无需公开回执。

两条维护输入都经主线采用，注入和冻结由主线在派生副本执行。当材料发布并由当前消费者采用后，主线核对 origin/develop 的可发现性、提交身份和实际后续行动；不以一次 ACK 计完成。Console 最后由主线沿既有单实例部署并作实际页面操作确认。

## Owned 文件与交接

- Braid 源码：`sources/braid/src/objects.rs`、`context.rs`、`cli/mod.rs`、`group/provider.rs` 的指定评论/材料区域。
- Braid 知识：`sources/braid/docs/10-prd/objects.md`、`docs/20-product-tdd/local.md`、`context.md`。
- 协作技能：`harness/skills/braid-collaboration/SKILL.md`、`references/organizing-work.md`、`references/accepting-and-closing.md`。
- Console：`braid-console/archives.py::comments`、`web/src/Discussion.tsx`、`web/src/api.ts` 的评论类型。
- I13：`variants/pi-braid-i13/run.py`、`variants/pi-braid-i13-glm-root/run.py` 仅 ROOT_CHECK_MESSAGES；基线 `agents/pi-glm-fast/instructions.md` 与实际 variant 的 `agents/pi-glm-fast/instructions.md`、`agents/pi-glm-root/instructions.md` 仅必要 SVC 强制触发。
- 当前任务材料仅此文与 findings 新事实。没有 commit/push；主线统一整合，保留其它工作区修改。


## SVC 分发核对增量

用户随后质疑“不要 growth 仅在 canonical 成立，Factory 实际分发总 svc 入口”。[三层证据](../../../runs/iteration13/i13-2-20261001/collaboration-validation/svc-distribution-facts.json)将此说法限定到未被本轮选用的遗留总入口：当前 I13 build/run、base ZIP、Sheet/GitHub 暂停 work/skills 的四项独立 SVC 全树与 canonical 一致，svc-task-packet 的 13 文件没有 growth 路由。选择函数按明确名称复制，主会话 launcher 按独立 SKILL 路径启用，原生子角色的技能目录也只含已分发材料。

本轮已通过真实 copy_skill 物化所选四项，全部文件 SHA 一致、65 个相对 Markdown 入口有效。没有发现需要修正的活动分发错路由，因此此增量不改 canonical、copy_skill、package_agent 或已冻结 Braid；不删除旧 ZIP 与未跟踪 legacy svc 目录。活跃/保留入口的 build/run 选材表、停用总入口消费者与复制产物均在原始 JSON，具体事实见 findings。最终 I13-2 新 ZIP 仍由主线生成，其形成后需要沿同一实际包清单核对；物化目录不等同完成新包冻结或模型采用。


## task-packet 入口审计后的冻结增量

通用 SVC task-packet 的 description 与起始段已明确工作前使用、三类载体职责及材料引用；起点判据不再按“obvious action”数量，交接接收者须在依赖工作前接续当前依据，跨任务 owner 信息仅保留影响当前路线的责任与依赖。本增量只修改其 SKILL，现有 information/planning reference 无需改动。Braid 具体对象与发布规则继续由 braid-collaboration 持有，未注入通用 SVC。

同时将基线 fast 和 GLM 对照 root/fast 的 profile 新增段缩回 mandatory SVC、触发范围和 skill 读取入口，删除先前重复的 clone 根与发布 SOP。事实与因果限制见 findings；并未声称前置文字已战胜工作项说明或模型已经遵循。源码面不动 Braid/native/runtime/Console，未新增方法、测试或技能正文内联。

[冻结文件 SHA](../../../runs/iteration13/i13-2-20261001/collaboration-validation/task-packet-audit-frozen-material.json)给主线用于刷新 package-stage 和最终 ZIP：`skills/svc-task-packet/SKILL.md` 与 GLM 对照 `agents/{pi-glm-root,pi-glm-fast}/instructions.md` 需要替换，另外基线对应 fast source 同步保持一致。stage 先前已确认其余四项 SVC/协作文件的完整身份和独立发布形状，可复用；最终 ZIP 的路径、全量 SHA 与无 legacy/growth 核对由主线执行。模型恢复后观察实施前 packet、当前材料及实际发布/采用，不以文字审核或文件存在计行为验收完成。
