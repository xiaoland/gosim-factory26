# I13-2 协作材料与评论隐藏调查

2026-10-01。范围为 `glm-root--hackathon--sheet-a45a22ec644204` 的 PR #2、Issue #1 与 Braid 评论可见性链路。本文是只读调查和实施交接，未修改源码、运行状态或 Console，未运行测试、探针、模型或实验。事实、判断和未核实事项分别标明。

## 结论与证据入口

**事实：PR #2 创建前已经有四份发布到 develop 的共同文档，根负责人也已经读过相关技能。** PR #2 随后再次写入平台合同、技术栈、精确种子、API、UI 文案和通用验收规定。不能把整个 PR 正文判为无效：本 PR 的壳页范围、与后续编辑器的界面、阶段验收及暂缓项确实需要作为当前责任交给负责人。应保留这些差异，引用共同定义，停止维护共同规则的另一份副本。

**事实：Issue #1 的旧提醒根已被隐藏，其子回复仍进入普通模型 Context。** 因而这不是仅仅“还没有 hide”，也不是仅 Console 展示差异。当前产品契约就是单条 hide；用户期待的祖先隐藏向后代生效需要改变 Braid 的共同读取语义，并同步 Console 的归档读取与隐藏展示。

本次定向材料以以下入口定位，不广泛导入完整 rollout：

- 启动身份：[launch-summary.json](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/launch-summary.json)。Sheet 为干净启动，Braid run 为 `20261001-104900-3b994a70`；实际 Braid binary SHA256 为 `5e98b9374d20870fc6dd45406b4b2d4efc41bf9e6fbb9f3edd4ff64ae8f50a73`，纳入 `828a3da`。
- E1，根设计会话：[2026-10-01T10-49-09-600Z_01a0f715-16df-753d-be50-c785cddcdc83.jsonl](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/monitor/20261001T114033.094510Z/glm-root--hackathon--sheet-a45a22ec644204/evidence/20261001-104900-3b994a70/work/native-homes/pi-glm-root-01a0f715-1323-7af0-bf9b-602b9c9ce904/sessions/2026-10-01T10-49-09-600Z_01a0f715-16df-753d-be50-c785cddcdc83.jsonl:90)。第 90 行是 PR #2 创建正文的完整 write；第 92–93 行是实际 create 及回包。
- E2，PR #2 实施会话：[2026-10-01T11-04-29-608Z_01a0f723-20a8-76ed-ac7f-2a1de58f276e.jsonl](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/monitor/20261001T114033.094510Z/glm-root--hackathon--sheet-a45a22ec644204/evidence/20261001-104900-3b994a70/work/native-homes/pi-glm-fast-01a0f723-1d23-7f12-8665-181546a3afcf/sessions/2026-10-01T11-04-29-608Z_01a0f723-20a8-76ed-ac7f-2a1de58f276e.jsonl:5)。仅核对技能、共同文档读取及 packet 的建立时机。
- E3，根进展会话：[2026-10-01T11-05-57-313Z_01a0f724-7740-7151-bc37-b2c127fe090b.jsonl](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/monitor/20261001T114033.094510Z/glm-root--hackathon--sheet-a45a22ec644204/evidence/20261001-104900-3b994a70/work/native-homes/pi-glm-root-01a0f724-73f1-76b3-a89d-5640ed50f9c9/sessions/2026-10-01T11-05-57-313Z_01a0f724-7740-7151-bc37-b2c127fe090b.jsonl:44)。第 11、30、44、60 行分别创建旧进展回复 #3、#5、#7、#9。
- E4，重建后的真实普通 Context：[2026-10-01T11-35-01-542Z_01a0f73f-14a5-70cc-acca-84f2b4446f63.jsonl](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/monitor/20261001T114033.094510Z/glm-root--hackathon--sheet-a45a22ec644204/evidence/20261001-104900-3b994a70/work/native-homes/pi-glm-root-01a0f73f-1165-7a00-bc9b-dc83252826c1/sessions/2026-10-01T11-35-01-542Z_01a0f73f-14a5-70cc-acca-84f2b4446f63.jsonl:4)。第 4 行、11:40:04.724Z，是正常首条用户输入，直接证明隐藏根下的旧回复正文仍被注入。
- E5，暂停后保全的独立只读 SQLite 副本：[braid-forensics.sqlite3](/Volumes/WorkSSD/Development/factory26/runs/iteration13/i13-2-20261001/preservation/sheet/early-sqlite/braid-forensics.sqlite3)，独立重算 SHA256 为 `6f9e3bbe81cc32b6f505757348afecca74a3cb07e2155f8ab480cf534b12af29`。以 `mode=ro&immutable=1` 仅查询 `local_comments`、`local_activity` 和 PR #2 的 `local_items`；依据以表名、Comment ID 和 activity ordinal 定位，不为二进制 DB 虚构文本行号。
- 原冻结输入：[glm-root-sheet-clean.zip](/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/glm-root-sheet-clean.zip)。仅读取三项技能及两份 `agents/*/instructions.md`，未读取凭据。包内三项技能与当前仓库文件逐字相同，排除了本次看到的新技能尚未进入这只运行的解释。

## PR #2 的材料归属

**事实与时序。** E1 第 5 行读取 braid-collaboration，42 行读取 svc-documentation，52 行读取 svc-task-packet，54 行建立根 packet。76、78、80、82 行分别写 `docs/product.md`、`docs/technical-design.md`、`docs/api-contract.md`、`docs/acceptance-plan.md`；86–87 行发布设计提交 `eab1a21`。90 行于 11:04:23.602Z 写 PR 正文，92–93 行创建 PR #2，94 行又写 Issue #1 正文。正文自称“本文不重复其内容，冲突时以 docs 为准”，实际仍包含下表规则。

E5 的 `local_items.node_id='pr:2'` 正文为 2872 字符、revision=2；与 E1 第 90 行创建正文逐字相同。因而下述重复在暂停现场仍存在，不只是创建时的历史写法。

这里“重复”按知识责任及变更原因判断，不按正文长度判断。文档内行号指 E1 对应 write 的 content 内行号，尚未将 monitor 的定向材料冒充完整工作树。

| PR #2 内容 | 已有共同定义 | 实施时应保留的 PR 差异 |
| --- | --- | --- |
| 仓库目录、技术栈、独立安装、静态服务、HOST/PORT、Node、启动条件 | `technical-design.md` 23–45、125–129 行；E1 78 行 | 本 PR 交付脚手架和正式服务路径；指向发布提交及共同合同。开发命令和稳定环境要求归项目入口/操作说明，不逐个 PR 重列。 |
| `Q3 Sales`、两张表和六个逐字单元格值 | `product.md` 68–76 行；E1 76 行 | 本 PR 实现迁移与幂等种子；引用种子定义及幂等性验收，不复制字面量表。 |
| API 路径、统一错误、验证模板和原子性 | `api-contract.md` 11–77 行；E1 80 行 | 哪些接口由本 PR 交付、透视源约束哪些义务留待后续。不能因为局部暂缓就缩减整体合同；留出当前责任入口。 |
| 首页、创建、重命名、导入的精确控件名及文案 | `product.md` 17–54 行；E1 76 行 | 本 PR 只把编辑器做到壳页，网格/HF/标签栏留给后续；URL 和刷新需要达到什么阶段结果。 |
| 平台命令、首轮失败保存、Vitest 和冒烟流程 | `acceptance-plan.md` 5–13、45 起；E1 82 行；技术说明 125–129 行 | PR #2 阶段仅验首页→壳页→刷新，不能照搬共同冒烟里的 A1 网格门槛；本 PR 的选择范围及对应原始证据入口需要保留。 |
| better-sqlite3 已验证安装、React Router 选择、开发代理与正式验收区别 | 技术说明技术栈/平台/反馈章节；E1 78 行 | 当已有环境结果适用于本候选时引用其条件；需要本候选正式安装观察则说明原因与证据，不重复全局操作教程。 |

E1 94 行的 Issue 正文还复制了角色/流程、develop→main 分支规则、关键技术决定和 PR 路线。前两项已经由冻结 `agents/pi-glm-root/instructions.md` 与 `agents/pi-glm-fast/instructions.md` 提供；技术决定归 docs；仍在推进的 PR 路线归根 packet 与责任入口。Issue 可以解释整体目标、当前剩余义务和消费者入口，但不宜成为这些共同规则的第二权威。

**技能实际采用的事实。** E2 第 5–6 行读取 braid-collaboration；11、18、24 行读取四份共同文档。该保全会话未出现 svc-documentation、svc-task-packet 的读取，也未见上述 Braid reference 的读取。首个 PR packet write 在 116 行，11:17:59.756Z；内容已经说“代码已全部写完，未提交”，且是因会话将结束而保存恢复状态。212、234 行继续维护最终状态。它证明 packet 的确被使用，不能说完全没有任务包；但它没有在实施起点承担当前推理与路线的作用。未据此推断全部子 Agent 都未读取技能。

**判断与诱因。** 技能不是缺失：冻结与当前版本一致，且根负责人实际读过。现有 [braid-collaboration 主文](../../../materials/skills/braid-collaboration/SKILL.md:11) 已说共同定义、packet、description 与讨论不能互相镜像；[svc-documentation](/Volumes/WorkSSD/Development/factory26/sources/svc/skills/svc-documentation/SKILL.md:60) 已要求链接共同定义。但 [provider::local_instructions](/Volumes/WorkSSD/Development/factory26/sources/braid/src/group/provider.rs:64) 仍把 description 定义为“当前要求与稳定决定”；[organizing-work](../../../materials/skills/braid-collaboration/references/organizing-work.md:17) 让 Issue description 保存决定，[accepting-and-closing](../../../materials/skills/braid-collaboration/references/accepting-and-closing.md:21) 仍把“义务、合同和理由”并列允许放入 description、文档或 packet。它们没有给出消费者需要的区分条件，容易被执行成再次浓缩共同合同。不能证明任何一条是模型行为的唯一原因。

**可执行修正。** 只调整上述共同说明的知识责任：共享产品/技术/操作规则归已有版本化文档或配置；当前解释、实施路线、进度、恢复点归 packet；Issue/PR description 解释本工作项的目标、交付差异、依赖、仍欠义务及适用共同定义入口，验收返回保存实际候选和证据证明范围。保留足以让消费者知道为什么读该入口的关键结论，不用机械字段模板、字数上限或纯链接清单。不再次铺开 SVC 技能正文，也不新增“读了技能”的 ACK。

项目根 AGENTS/CONTRIBUTING 若缺少当前文档和开发入口，应按 [svc-documentation 的贡献者入口](/Volumes/WorkSSD/Development/factory26/sources/svc/skills/svc-documentation/references/internal-and-local.md:27) 补足发现入口；不要把整个架构和流程搬成 AGENTS 的另一份正文。包内 Harness 角色已说明的配方政策仍由角色持有，应用 AGENTS 不复制模型、ARC 或本次实验政策。完整冻结应用内 AGENTS 的存在性尚待保全工作树核实。

## Issue #1 的过时回复与 hide 实际语义

**运行事实。** E4 第 4 行同时出现以下内容：

| 评论 | 正常 Context 中的状态 | 仍注入的正文含义 |
| --- | --- | --- |
| #2、#4、#6 | 三个 Braid 提醒根均显示 `hidden (superseded by the next root progress check)` | 根本身正文隐藏。 |
| #3，回复 #2 | 正文可见 | 11:05 的设计已交付、PR #2 尚无候选、我方无待办。 |
| #5，回复 #4 | 正文可见 | 11:17 的 PR #2 尚无已发布提交，加上未变的材料入口。 |
| #7，回复 #6 | 正文可见 | 11:22 自称“与评论 #5 相比无变化”“我方无待办”。 |
| #8、#9 | 新提醒根及其进展回复 | #9 有真实新候选 `428ea08`，但仍重列“当前入口（无变化）”。 |

E3 中未观察到根负责人对这些回复执行 hide/resolve；三个旧提醒根的隐藏是 Braid 自动维护。源码 [objects.rs 根提醒事务](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:422) 只把旧提醒单条 lifecycle 改为 hidden，并明说保留回复。这与 E4 独立运行输入一致。

E5 补齐暂停现场：旧提醒 #2/#4/#6/**#8** 均自身 hidden，回复 #3/#5/#7/**#9** 均自身 visible、没有 hide_reason；Issue #1 所有根的 resolved_through 均为 null。`local_activity` ordinal 9、13、16、28 分别记录 Braid 对 #2、#4、#6、#8 的自动 hide，最后一项发生于 11:40:03.00479778Z；没有成员 hide 或 resolve。最新提醒 #12 与回复 #13 自身 visible。因此实际情况是“系统已 hide 旧根，但产品只处理根自身，旧子评论仍可见”；不是用户或模型已隐藏全部子项而 Console 忽略了状态。E4 的物化快照中 #8 仍可见，与稍后的自动 hide 时点分别保留，不把输入接受时间当成所有快照内容的读取时间。

I13 的 [ROOT_CHECK_MESSAGES](/Volumes/WorkSSD/Development/factory26/variants/pi-braid-i13/run.py:27) 交替使用“检查进展”和“检查进展并整理 task packet 及 Issue/PR 当前入口”。**判断：** 根负责人把后者解释成公开汇报，即使无新事实也重新公布当前入口；已有 provider 与技能要求无待办不回执，并未实际约束该行为。最小补充应解释“检查/整理是核对和维护发生变化的现有材料；无变化无需公开回复”，放在通用协作说明与本轮提醒含义中，不在通用 Harness 写 ARC 特例。新提醒仍可触发真正的纠偏、交接或剩余义务，不能机械禁止所有根回复。

精确修正边界包括 `variants/pi-braid-i13/run.py::ROOT_CHECK_MESSAGES` 的第二句：将无条件“整理当前入口”的信号改为按实际变化维护既有材料，并按协作技能判断下一动作。对齐 [accepting-and-closing 的停止条件](../../../materials/skills/braid-collaboration/references/accepting-and-closing.md:25)，不增加另一层否定清单或公开检查模板。源码重新冻结进 I13-2；当前运行已存的提醒正文作为历史保留。

### CLI → 对象存储 → 投影 → Console

| 环节与精确入口 | 当前事实 | 隐藏继承的实施责任 |
| --- | --- | --- |
| `cli/mod.rs::CommentCommand::Hide`、`print_change`、`CommentCommand::Hide` dispatch（[438 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:438)、[776 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:776)、[1209 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:1209)） | 多 ID 是逐条操作；文本明确“仅此正文，回复保留”。 | 更新 help、回执的可见性解释；不把继承效果误报为对子项的独立 hide 写入。 |
| `objects.rs::hide_comments` / `comment_lifecycle`（[1241 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1241)） | 只改选中 ID 的自身 lifecycle；unhide 也只改一个。 | 继续保留自身 hide 状态。根 unhide 不能抹去孩子自身 hide；不需批量永久改写所有后代或新建 migration。 |
| `objects.rs::read_comments`、`view_comment_for_fields`、`comments`、`issue_in`、`pull_request`（[1358 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1358)） | 正文只看本条 life 和根 resolved cutoff；精准单条读取先限制本条 ID。Issue/PR CLI 与 CanonicalContext 共用这里。 | 用自身或任一 reply_to 祖先 hidden 计算实际可见性；精准单条也必须独立追祖先，不能因 WHERE 只选本条漏掉继承。分支级祖先隐藏只影响其后代。 |
| `context.rs::CommentSnapshot`、`render_context_comments`、`render_comment`（[86](/Volumes/WorkSSD/Development/factory26/sources/braid/src/context.rs:86)、[454 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/context.rs:454)、[491 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/context.rs:491)）；`cli::comment_json`（[566 起](/Volumes/WorkSSD/Development/factory26/sources/braid/src/cli/mod.rs:566)） | `minimized` 是自身 hidden；JSON 又用它反推 lifecycle。renderer 遍历孩子，不按隐藏祖先跳过。 | 保留自身 lifecycle/minimized，另表达可诊断的隐藏祖先（例如 `hidden_by`）；普通正文及 renderer 使用有效可见性。不能只把 minimized 改为继承结果，伪装孩子自身状态。 |
| `objects.rs::comment_reply_in`、`edit_comment`、`deliver_comment_to` / `discussion_changed`（[1054](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1054)、[1170](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1170)、[1096](/Volumes/WorkSSD/Development/factory26/sources/braid/src/objects.rs:1096)）；`store::batch_references*`（[5963](/Volumes/WorkSSD/Development/factory26/sources/braid/src/store/mod.rs:5963)）；`provider::render_event_references`（[101](/Volumes/WorkSSD/Development/factory26/sources/braid/src/group/provider.rs:101)） | 评论通知保存/读取静态引用与普通 `comment view` 命令，没有注入正文，事件不是重新从 snapshot 渲染。新增回复自身总为 visible；edit 的新 @ 条件只看本条 life/folded。 | 新回复用同一祖先规则立即继承；审阅直接联系/读取义务时也区分实际隐藏。无需改写旧事件字符串或原生历史；普通事件入口不得自动加 include-hidden，读取后的隐藏状态不能当作应消费的正文。 |
| Console live [server.py::item_view](../../../consoles/braid/server.py:128)、`/api/comment`（[287](../../../consoles/braid/server.py:287)） | 正常 `/api/item` 使用 CLI view JSON，不带 include-hidden；`/api/comment` 固定带 include-hidden，供用户展开正文/历史，不存在正常 API 默认 `show_hidden` 开关。 | live 正常对象读取继承 Braid 结果。追溯接口保留明确展开用途，不把其全文回填普通 item/context。 |
| Console archive [archives.py::comments](../../../consoles/braid/archives.py:155) 与 `comment` | 独立 SQL 复制自身 lifecycle/folded 判断；item 默认 include_hidden=false，指定 comment 追溯用 true。 | 同步计算隐藏祖先，并保持单条自身状态。Braid 和 archive 两个维护边界需对同一保存 DB 取得一致结果。 |
| Console [Discussion.tsx::CommentCard](../../../consoles/lab/web/src/Discussion.tsx:23) / `Thread`（[70](../../../consoles/lab/web/src/Discussion.tsx:70)） | hidden 仅看本条 minimized/lifecycle；Thread 仅过滤 folded，没有祖先隐藏过滤；用户显式展开后读取追溯 API。 | 默认对子回复按有效隐藏呈现/收起正文，显示可诊断的祖先入口。`expandedBody` 从整串 include-hidden 返回时也不能绕过有效隐藏；显示历史的用户动作不得改变 store 或普通模型投影。 |

**推荐语义。** 持久态仍是每条自身 visible/hidden/deleted。正常可见性由本条和任一隐藏祖先共同决定；根 hide 因而覆盖现有全部子回复及未来新回复，中间回复 hide 只覆盖其分支。根 unhide 后自身未隐藏的后代重新可见，仍被其它隐藏祖先或自身 hide 约束的正文继续隐藏。resolve 仍是当前前缀折叠，新回复不自动 folded；delete 仍保留墓碑和回复关系，不借此改变删除合同。include-hidden 是显式追溯入口，无法恢复 deleted 正文，也不能使普通 Context/事件重新展开历史。

**精确所有权建议。** 一个 Braid worker 独占 `objects.rs` 的上述评论创建/编辑/生命周期/读取函数、`context.rs` 的 CommentSnapshot 与评论 renderer、`cli/mod.rs` 的评论帮助/JSON/回执，以及 `group/provider.rs::local_instructions` 的材料归属/hide 文案。此范围不需碰 `provider/pi.rs`、group worker 或 store 会话生命周期；事件 batch 读取仅作为已核查边界，若实现判断要修改则先交主线协调。共用 `objects.rs` / `provider.rs` 的函数区开工前再次与 OOM worker 锁定。

Console 的 `archives.py::comments` 和 `web/src/Discussion.tsx::{CommentCard,Thread}` 应归同一个隐藏兼容 owner；`server.py` 的正常/追溯 API 已有分离，只有发现字段或读取透传缺失时才改对应函数。只处理隐藏可见性兼容，不接手 UI 改版、文件浏览、部署架构或新实例。通用技能修改归主线统一材料 owner，避免另一个 worker 同改同段落。

## 行为验收与未核实事项

使用已保存 DB 的隔离副本和真实 CLI/Console 操作获取反馈，不新增 Factory/Braid 测试或换名探针。编译只证明源码完整性；原始状态与实际操作回包分别保存。以下是消费者行为维度，不是要求另造测试框架：

1. 根 hide 后，普通 `issue/pr view --comments`、精准 `comment view CHILD`、`--thread`、各 Context 档位、Console live/archive 的默认视图都不显示后代正文；能看出自身状态和导致隐藏的祖先。单条精准读取不能漏算祖先。
2. 多层回复中间节点 hide 不影响兄弟分支；父根 unhide 不清除子节点自身 hide；隐藏祖先下新增回复立即继承。多 ID 失败维持现有整批原子性；delete 不可恢复、resolve 的新回复语义维持原合同。
3. 明确 include-hidden 或 Console 展开可追溯所需正文及隐藏来源；随后关闭展开、正常重新读取或新建 Context 不泄漏追溯正文。整串展开的 `expandedBody` 不能穿透仍隐藏的节点。
4. hide/unhide 的状态通知仍可纠正受影响成员；隐藏分支的新增/编辑及 @ 不得通过普通正文入口恢复正文。既已送达的原生历史不改写；在途成员依据更正联系处理旧认识，而不是声称 hide 追回历史。
5. 用同一保存 DB 比较 Braid 与 Console archive；E4 的旧根 #2/#4/#6 与子 #3/#5/#7 是本次真实回归材料。操作前后的自身 lifecycle 保持可追溯，不能用级联 UPDATE 获得表面一致后丢失独立 hide。
6. 本地 GLM 接续时观察新的实际协作：描述承载本工作项差异与义务，引用共同定义和适用提交；当前 packet 在多步实施前可用并随决定/路线维护；提醒无新变化时不发布无动作回执。已有有效的壳页边界和阶段验收不因“去重”而丢失。此项需要真实获授权运行反馈，不能仅凭文案或字数下降宣称成功。

**未核实：** 完整暂停工作树仍在导出，位于 `runs/iteration13/i13-2-20261001/preservation/`。本调查没有拿 monitor 或单 DB 当完整 checkpoint；各应用 clone 的 AGENTS 是否存在、完整 Git/原生会话一致性仍待保全负责人核实。评论终态与 PR #2 正文已由 E5 补齐。用户所见 Console 的当时实例版本与页面展开状态未直接取证，因此不声称已复现其当时每个像素，但读取缺口由源码、冻结 DB 和模型实际输入共同确证。


## 完整暂停工作树补证：SVC 发布缺口

完整 Sheet 保全副本已完成，来源与身份见 `preservation/handoff.json` 的 `sheet.git_locations`。此次只读 Git、原生会话与文件核对的原始回包归[发布事实](../../../runs/iteration13/i13-2-20261001/collaboration-validation/svc-publishing-facts.json)。这里纠正的是“文档与 packet 已经可供接续”的完成判断，不否定已经发生的设计交付和技能读取。

`origin.git` 的 `refs/heads/develop` 为 `577d64b0c11dffad5ae7f188b95f17867f5e8f33`，包含四份 `docs/{product,technical-design,api-contract,acceptance-plan}.md`，没有 `AGENTS.md` 或任何 `tasks/`。设计提交为 `eab1a21`，PR #2 已发布 head 为 `428ea08815550808c0d9acddce3d0119f58c25cd`，合入 develop 的提交为 `577d64b`。根 clone HEAD 与 PR #2 clone HEAD 的树也没有上述入口/packet，普通 `git status --short --untracked-files=all` 均为空。应用导出 clone 尚为初始 `b9cf795`，不能据其树断言 develop 没有四份文档。

packet 确实写过且仍在暂停副本中。E1 第 54 行，2026-10-01T10:53:45.837Z，明确写入 `/workspace/template/.factory26/20261001-104900-3b994a70/work/tasks/issue-1/packet.md`；E2 第 116 行，11:17:59.756Z，明确写入同一运行根下 `/work/tasks/pr-2/packet.md`，212、234 行继续维护。两文件当前分别为 7565 与 1646 bytes。它们位于独立 clone 外，因此不可能由这些 clone 的普通 commit/push 带给消费者。`git check-ignore -v tasks/issue-1/packet.md tasks/pr-2/packet.md` 在两 clone 中均返回 1，无排除规则；HEAD `.gitignore` 只排除依赖、dist、log 和 sqlite。没有证据表明 packet 曾在 clone 内创建后又被清理，不把未发布推成未创建。

原生 cwd 并未指错。E1 session header 为 `/workspace/template/.factory26/20261001-104900-3b994a70/braid-state/worktrees/issue-1/pi-glm-root-g1`；E2 为同一运行下 `/braid-state/worktrees/pr-2/pi-glm-fast-g1`。Braid 的 Issue/PR provisioning 将 effective profile 的 workspace 设为各自独立 clone，Pi 用该 workspace 设置 `cmd.current_dir`。保全 `physical/*/instructions.md` 未出现 `work/tasks` 指示。SVC task-packet 当前只约定相对 `tasks/<task-id>/packet.md`，不强制产品目录结构；观察到的是 Agent 显式选择 clone 外绝对路径，不支持 runtime cwd 注入缺陷的解释。本轮由 I13 profile 强制触发独立方法读取，在协作技能明确从 `git rev-parse --show-toplevel` 返回的实际 clone 根建立材料，而不修改 cwd 链路。

PR #2 的四份文档实际读取分别见 E2 第 11、18、24 行，来源是当前 clone 的相对 docs 或其绝对路径；共同定义至少已经被取得，不能声称“完全没有文档系统”。PR #3 的原生会话 `2026-10-01T11-33-13-155Z_01a0f73d-6d42-72be-97e9-ed55eed7aeda.jsonl` 第 11、17 行也读过四份 docs，第 30 行读 svc-task-packet，第 36 行使用相对 `tasks/pr-3/packet.md` 写入；完整副本确实在 PR #3 clone 内保留这份 3164-byte packet。它尚属未提交实施态，与已经交接/合入的 PR #2 不能混为同一发布缺口。

因此强制要求尚欠的是可发现的阅读入口、在实施中使用并随阶段发布的根/PR packet，以及 consumers 取得适用版本后的实际采用证据。具体修正、隔离验证与恢复建议见[协作实施](collaboration-implementation.md)。源码和提示词修正不等于暂停模型已经遵循，也不以目录、模板或技能读取 ACK 作为验收。


## GitHub 完整暂停工作树：另一种 packet 发布缺口

GitHub 的完整现场保全后追加有界只读核对，未为此读取 rollout 或恢复运行。原始 Git/DB/路径记录见[GitHub 发布事实](../../../runs/iteration13/i13-2-20261001/collaboration-validation/github-publishing-facts.json)。其 origin/develop 与 braid/pr-2 均为 `726e21f4ea42ff9a5dbedd572a86fd1bf0bb2ed1`，发布了 `docs/{architecture,permission-matrix,seed-data,verification,reading-map,ui-inventory}.md`，没有 AGENTS.md 和 tasks。六份文档包括需求阅读图，不能将 Sheet 的“四份文档且 clone 外 work/tasks”事实套给 GitHub。

当前根 clone 内确有未跟踪 `packet/state.md`、`design-summary.md`、需求摘录、视觉结果、PR 正文草稿等九份材料。state.md 自称根 task packet，保存当前设计交付、PR 路线及接续动作，开头明确“勿提交 packet/ 目录到共享仓库”。这是现存私有材料的指示，不是已核实的 Harness 配方要求；恢复时应保留其作为来源并撤销这项当前交接判断，不能凭没有 tasks 目录就认定没有工作记忆。运行的 work/tasks 未发现 packet，tasks 无 Git ignore 匹配。

保全负责人生成的合并 WAL forensics 副本显示 Issue #1 OPEN、负责人 glm-root-1；PR #2 OPEN、负责人 glm-1，base develop、head braid/pr-2。PR #2 clone 已有大量未提交基础实现，已发布分支仍只有设计提交，必须保留其在途文件。首次 immutable 读取原 base DB 因忽略非空 2422592-byte WAL 只见根 Issue；该首轮结果及原因保留在原始事实 JSON，当前状态以完整 forensics 副本为准，不把 base DB 当完整恢复点。

GitHub 的必要维护是从现有 clone 内 packet 来源整理为可共享、可接续的 tasks/issue-1/packet.md，补齐导航并先发布共同材料；当前 PR #2 成员在继续实施前恢复本项 packet，随候选发布。它无需复活 Sheet 已完成 PR #2 或沿用 Sheet 的 PR #3/577d64b 进度。


## SVC 分发补证：总入口的 growth 未进入本轮 I13

用户指出 `harness/skills/svc/` 总入口仍保留 growth 路由。该观察对这份文件成立，但不能直接推为本轮 Agent 读取了它。沿 canonical、选材函数、冻结 ZIP 和两个完整暂停工作区核对后，未发现本轮 I13 的 SVC 分发错路由；原始文件清单、SHA、链接目标和 launcher 内容归[分发事实](../../../runs/iteration13/i13-2-20261001/collaboration-validation/svc-distribution-facts.json)。

`harness/skills/svc-task-packet` 是跟踪的 symlink，指向 `../../sources/svc/skills/svc-task-packet`。其 canonical `SKILL.md` SHA256 为 `a7380c7b8150a5838529324ae61e367e4e6c4a064ae56f890de0dea6f1af3ebe`；整个发布树为 13 文件，只含 SKILL、information/planning reference 与可选模板，未有 growth 文件或路由。当前 `copy_skill` 复制明确选中的 SKILL、references、assets、scripts，不按目录全量发现，也不把独立技能重定向到总入口。

I13 和实际 GLM 根对照的 build/run 都明确选择 `svc-sub-agents`、`svc-task-packet`、`svc-documentation`、`svc-verification`。base `glm-root-sheet-clean.zip` 的 skills 根只有这四项 SVC，没有 `skills/svc/`；四项全部文件及其 SHA 与 canonical 一致，不是仅首文件相同。Sheet 和 GitHub 完整暂停工作区的 work/skills 也只含这四项，完整树与 canonical 一致。其 launcher 关闭默认技能发现，并通过 15 个明确的 `--skill .../SKILL.md` 路径加载；其中 task packet 的路径就是独立 skill 文件。实际原生读取入口已由此前 E1/E2/E3 证据记录，不是从总入口猜测。

选材表同时检查当前与保留的入口：pi-minimal 只选独立 svc-verification；pi-braid、I11、I12、flash-team、kimi-root、coordinator、review 均以独立 svc-* 选择所需材料，无总入口。`harness/skills/svc/` 是未跟踪的遗留目录；真正引用它的代码入口是 `variants/pi-team-{glm,deepseek,vv}` 与 native-hackathon 专用旧打包器，均在 Variant 索引列为停用历史实现。本次没有启动这些路径，不修改其历史冻结制品。

为本轮 I13-2，用当前真实 copy_skill 从同一 harness symlink 物化四项至 `collaboration-validation/i13-2-svc-material/skills`，得到 1/13/12/6 个文件，无 symlink 和 growth 路由，全部 SHA 与 canonical 一致；65 个 Markdown 相对链接均可解析到实际文件。它证明本轮已选择材料的物化路径，尚不冒充主线最终新 ZIP。结论是保留正确 canonical 和现行分发，不因遗留未选材目录中的字符串增加转换层或删除他人未跟踪材料；最终新包形成后按实际包清单继续核对。


## task-packet 起点与载体职责审计

用户进一步指出：载体边界偏晚可能输给工作项契约；handoff 句没有明确实施前建 packet；“more than one obvious action”判据含混；existing owners/ongoing work 可能诱发 PR 复制。按当前 SVC Skills AGENTS、svc-documentation 的 task-state 边界、task-packet 及现有 information/planning reference 审计，原方法已经要求当前答案、指向详细材料及不维持第二定义；修正澄清入口、时点与依赖范围，不新增管理方法或固定模板。继承的历史 Corpus/CLI 文档不覆盖当前独立 Skills 契约。

已证实的 Sheet 行为仍是：根读过 skill、实施 PR #2 读过 braid 与共享文档但未见 task-packet/doc skill 读取、首个 PR packet 在代码写完后建立、root/PR #2 packet 位于 clone 外、共同提交没有 packet/AGENTS、PR 描述重复共同合同。它们不能证明第 46–49 行的位置或“existing owners”文字是唯一原因，也不能证明提前正文即可改变 instruction 优先级。旧 Braid 把 description 称为稳定决定、允许私有材料与不明确发布路径，是已见的竞争说明；本轮已在其所属层修正。

最小增量已冻结：通用 task-packet SKILL 开头先说明当前工作记忆、项目知识与交接摘要的不同职责，指向 documentation 的知识归属；用需要调查/决定/多步路线/协作/恢复的具体条件替代“obvious action”计数，明确工作前建立/接续、实施前形成当前依据、接收方在依赖工作前恢复它。owners/ongoing work 限于影响本任务下一步的依赖与责任，其合同、计划和进度仍留在自身入口。通用正文不含 Braid、Issue、PR 或 comment 产品名。

两个 I13 variant 的三个 profile instructions 同步缩回强制采用、开始/接续触发和独立读取入口；去掉重复的 clone 根、共享发布和 PR 发布 SOP。Braid 的具体规则继续只在 braid-collaboration，由现有入口持有，不增加另一层。information/planning reference 原语义与此一致，无需修改；没有改 native/runtime、Braid 或 Console，也没有运行内容测试或模型。变更文件 SHA 见[冻结材料](../../../runs/iteration13/i13-2-20261001/collaboration-validation/task-packet-audit-frozen-material.json)。

此前 package-stage 只读比较已确认四项 SVC、braid-collaboration 和 root/fast profile 与当时源码一致，独立 SKILL/references、无 growth 或 legacy svc 总入口，见[stage 事实](../../../runs/iteration13/i13-2-20261001/collaboration-validation/i13-2-stage-material-facts.json)。本次起点审计随后改变了 task-packet SKILL 和 profile instructions，主线须刷新这四份材料并在最终 ZIP 核对；旧 stage 一致性不能冒充本次最终冻结。真实采用效果仍由恢复后的行为判断。
