# 本地实验：Agent 工作过程与失分机制

本报告分析 WSL `/home/yyh/Development/factory26` 已冻结并完成本地公开测试的运行。它们与官网 Competition 的 Runner、公开测试版本和生成轨迹不能合并成同一实验。证据盘点与分析范围记录在[任务包](../../tasks/local-run-analysis/packet.md)；官网已评分产物的过程缺口另见[官网证据说明](../../tasks/official-results/process-evidence.md)。

## 证据是否够用

够用于分析已完成**本地 run** 的具体决策和首阻断点。两个主批次的八个已评分且完成交付的 run 均有冻结应用及哈希、`native/manifest.json` 和 5–7 个原生 JSONL、Braid Issue/PR/comment 与合并结果、评分 `summary.json`/`results.json`、失败项的 DOM `error-context.md`、trace 和截图。多数还保存了 Agent 自验命令和输出；上一轮 codex-generalist/Keep 未检出同类自验命令。本轮三个已评分 run 的应用 SHA 与重评输入完全一致。生成失败的尝试有独立身份、没有评分，不能合并到 DNS 重试或恢复成功的 run。

| 主批次 | Keep | BookStack |
| --- | ---: | ---: |
| 上轮 pi-generalist | 3/32 | 18/34 |
| 上轮 pi-team | 16/32 | 15/34 |
| 上轮 codex-generalist | 5/32 | 无该批次的完成评分 |
| 本轮 pi-team-glm | 6/32（DNS 重试生成新 run） | 8/34 |
| 本轮 pi-team-vv | 无完成评分 | 15/34（第二次 DNS 重试生成新 run） |

这些分数只帮助选择诊断对象。跨轮包、模型、候选代码和测试输入未形成单变量对照；尤其同为 15/34 的两条 BookStack run 有不同的失败集合。

另有两份**事后评测了部分产物、但 Braid 未完成交付**的历史 run：`runs/20260922-144234-2b52c95d` 的 codex-generalist/BookStack 为 8/34，`runs/20260922-144234-cd7850f8` 的 pi-verification/Keep 为 8/32。两份的评测哈希和该 run 的应用哈希匹配，原生会话、Braid DB、失败 DOM/trace 完整；但 `submission_eligible=false`、`delivery=null`、Issue/PR 仍 OPEN，因此不能当作“完成一次 harness 后得分”与上表并列。按已评分产物数是 10，按完成交付且已评分数是 8。

## 从原生会话连到评测失败

| Run | 运行过程中的决定或自验 | 交付与失败现场 | 可以确认的机制 |
| --- | --- | --- | --- |
| 上轮 pi-generalist/BookStack，18/34 | 独立复审从提交克隆、构建、启动、HTTP/API 自验 60/60；原生会话无浏览器调用。 | 16 项失败中 13 项先受 logo、删除确认、Tags、页面标题 placeholder 或建书入口的角色/名称差异阻断；另有两条指定 seed 未写入、一条草稿被匿名 owner 过滤。 | API 与静态验证无法证明匿名用户看到的种子和可访问入口。与 team 的 15/34 相比，两者各有独有通过项：generalist 的命名 Login form 和新建章节路径更好，team 的 Page title placeholder 更好，不能由净三分断言方案优劣。 |
| 上轮 pi-generalist/Keep，3/32 | PR packet 主动把创建入口写成 `Take a note…`，并允许用静态文案与 API 代替浏览器；实现 Agent 称缺无头浏览器，API 28/28，独立验收 API 36/36 后合并。 | 12 项因 div 卡片与测试优先查 article、随后错误退到标题子树而停；4 项入口精确名称不符；7 项因 nav 与 complementary 假设不符，helper 反而折叠已打开侧栏；其余是弹窗、listbox、menu 与视图状态。 | 入口层差异被测试 helper 放大，大多数场景没到业务结果。与同批 team/Keep 的 16/32 对照，team 有 article 卡片、aside 侧栏和精确创建名；这是可证的产物差异，不是模型/协作的单变量效果。 |
| 上轮 codex-generalist/Keep，5/32 | Agent 确实使用 agent-browser 的快照引用完成创建、删除、归档、标签、搜索和设置，并在 PR ready 评论称这些场景通过；复审核对了 18 条种子，但漏掉需求明列的 `Meeting agenda 2.8.1`。 | 创建入口多省略号，卡片按钮叫 More 而非 More options，标题节点与操作按钮为兄弟；编辑器缺 dialog，侧栏为 navigation，视图按钮改名且无稳定 pressed 状态。 | 快照点击能证明部分交互，却没有按最终评分的角色/名称/作用域合同验收。它比 pi-generalist/Keep 多过两项，但不能把净两分归因于 Codex 或 browser 工具。 |
| 上轮 pi-team/BookStack，15/34 | Braid PR packet 明确写“不预置 Shelf 4.3.1/4.3.2”；输入 YAML 的两处 `Seed data` 明确要求预置。Issue Agent 以 API 断言、构建文案及静态属性抽查验收较早提交，PR Agent 后续又改了卡片结构。 | 两项用例的 DOM 没有对应书架；`/books/:id/create-chapter` 被表单里的 `Boolean(id)` 误判为编辑，失败页显示 `Edit Chapter / Not found`。 | 一项是可追到 PR 设计的需求改写，一项是 UI 路由状态归属错误；API 冒烟和旧提交验收都没覆盖最终用户旅程。 |
| 上轮 pi-team/Keep，16/32 | PR packet 选择内联创建器和单个视图切换键；实现 Agent 与 Issue 验收 Agent 只做构建、API 和静态 ARIA 字符串检查，未做浏览器角色定位。 | 7 项先停在 `Note editor` dialog：实际创建器内联、编辑器叫 `Edit note`、标签复选框在 `Label note`。置顶一项的 DOM 已显示 PINNED 区和 Unpin 状态，测试仍找不到子节点 `title=Pinned`。 | 容器形状差异被公共 locator 放大，自验没有判断用户路径/角色；置顶至少有一项是测试附加 DOM 结构假设，不能称功能失效。 |
| 本轮 pi-team-vv/BookStack，15/34 | 原生会话执行 API、SPA 200、构建文案检查，批量脚本先报 `PASS=73 FAIL=3`，补查后 Issue 评论称“API/UI 冒烟 76 项通过”；未见真实浏览器角色定位与点击。 | 六项登录依赖用例停在 `form "Login form"`；DOM 有 Login 按钮，但 form 未命名。访客的 Favorite 被 `user &&` 隐藏。 | 自验把 API/静态证据上升为 UI 通过结论；未覆盖可访问结构与独立访客场景。Logo、Tags 等另有测试是否过度固定 DOM 形状的疑点，不能一律归为应用缺陷。 |
| 本轮 pi-team-glm/BookStack，8/34 | 主 Agent 和 PR Agent 都跑了构建、HTTP/API 检查；PR 批量脚本先为 77/78，补查单个 API 后报告 78 项通过。原生工具调用只有 bash/read/write/edit，未调用包内可用的浏览器能力。 | 同样缺名为 Login form 的表单，六项先卡登录；未登录后编辑、删除、收藏入口被隐藏或保存返回 `You need to be logged in.`。`ShelfForm.jsx` 未声明 `id`，trace 有 `ReferenceError`；种子缺 `Shelf 4.3.1`。 | API 自验没有触及登录 UI、浏览器路由渲染和冷启动种子；此外存在可独立确认的运行时错误。不是单一“角色问题”导致全部 26 项失败。 |
| 本轮 pi-team-glm/Keep，6/32 | 原生会话里有 73 条 `agent-browser` 命令，主要看 snapshot、按快照引用点击与 curl；它修复了 `Backdrop` 浏览器报错。未检出针对评分合同的角色、名称、嵌套作用域、`aria-pressed` 或 `aria-expanded` 断言；PR 评论声称 UI 50/50，但没有对应测试报告。 | 12 项在卡片标题节点内找兄弟分支的操作按钮；5 项找 `Note editor` dialog，实际名为 Create/Edit note；3 项找 `complementary` 侧栏，实际为 nav；其余涉及 group、option、菜单文案和状态属性。 | 浏览器被使用，却主要验证可见性和操作片段；它没有把需求/测试合同转为判别性 UI oracle。卡片层级一类还需区分测试结构假设与产品义务。 |

这些链条的原始材料在对应 WSL run 目录：上一轮 `runs/batch-multi-agent-20260922-01/<variant>-<task>/`，本轮 `runs/local/iteration-throughput-boundary/<case>/work/output/.factory26/<生成 run id>/`，以及各自的 `evaluation/` 或 `evidence/evaluation-input/evaluation/`。每条结论都同时用原生会话或 Braid 对象、交付产物和失败现场核对；“Agent 为什么选择该角色/文案”等无直接会话证据的动机不作推断。

八个完成交付的 run 中，六个只见构建/API/静态检查，没有浏览器自验；另两个确实用了 agent-browser，却主要按快照引用点击，未留下覆盖上述角色、名称、作用域和状态合同的可执行断言。因此“加上浏览器工具”不是充分修正。另一方面，现有 run 只保存 SVC 源码身份或 revision，没有按 run 归属的 Corpus 查阅/使用记录；不能断言某次结果由 SVC 指引造成。

未交付但已离线评分的 pi-verification/Keep 有不同性质的过程证据：它在 PR 工作树提交了代码，随后原生会话连续遭遇 provider `Connection error`，恢复尝试又遇到 materialization collision、缺 key 等故障。根 Issue/PR 没有 ready 或合并，`delivery=null`。冻结该提交后独立评分为 8/32，24 项失败的公共入口包括 div 卡片作用域、非 button 的 `Take a note...`、dialog/listbox/menu 与状态属性；实施会话只留下 build/curl/API 检查，没有完成其 PR packet 中承诺的 UI 验收。这个分数描述部分产物，不能代替一次完成的 V&V harness run。

未交付的 codex-generalist/BookStack 也从 PR 工作树确定性导出了部分应用，离线评分 8/34；`delivery=null`，Issue/PR 均 OPEN，PR 未 ready。原生会话里构建成功且 curl 得到 BookStack 数据，但同一端口的 agent-browser 却显示 Keep 页面，随后 provider 多次 `Connection error`/HTTP 500，turn 被中断；现有记录不能判定是谁发起 SIGTERM，也不能把浏览器错位单独定为交付中断根因。冻结产物的 26 项失败则另有 UI 证据：六项卡未命名的 Login form，多项 link 与测试要求的 button/精确名称不同，草稿直接进入编辑页使测试后续找不到 Edit。该离线分数同样不是完整交付成绩。

## 对下一轮的含义

当前最有力的共同机制是**验证观察面与最终用户合同脱节**，而且它有两种形式：只做 API/构建检查；或者用了浏览器，却只看快照/点击成功，没有对需求承诺的角色、名称、状态和完整旅程作断言。解决办法不是机械增加测试数量，而是先从具体需求选少量能区分正确与错误的完整旅程，并把自验绑定到最终交付提交；同时对测试的额外 DOM 假设做等价实现反例，避免为错误 oracle 改应用。

另一条独立机制是**设计时改变了题目明列的输入状态**：pi-team/BookStack 主动排除了 seed。它应由设计和验收阶段的“需求实体/初始状态清单”在实现前发现，而不是靠事后 API 冒烟。路由中的 `Boolean(id)` 和未声明 `id` 则适合用最小真实浏览器探针在交付前暴露。建议先用这些机制构成下一轮 V&V 方案和可运行验收，复核后再修改 SVC Corpus 或 harness；本报告本身没有改实验配置。

对 SVC Corpus 的候选改稿，这些证据提供了更具体的消费场景：[Design](../../tasks/svc-corpus-review/design.md) 应能阻止 seed 这类已写明的初始状态在 PR 方案中被无声改写；Implementation 的最小真实探针应尽早暴露创建路由和浏览器工作区错位；Test Design/V&V 需要同时防止 API 成功被误称 UI 成功，以及把需求未约定的 DOM 结构误作唯一正确实现。这些是待验证的改稿目标，不是“Corpus 导致低分”的因果结论。
