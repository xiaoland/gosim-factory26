# Hackathon 本地测试集实施计划

## 状态与实施边界

三轮设计已经获得用户认可，实施计划和两项独立预演已完成。用户已经授权开工，当前处于实现与验收阶段；授权原话与进度见 [packet](packet.md)。

交付范围是 GitHub 47 条、Sheet 24 条原子需求的公开可观察行为评测，包含正常流程、拒绝/状态不变、持久化与隔离。每条检查引用原子需求及其 ROOT/FOLDER 继承合同。无法从公开 UI 证实的内部机制、未定义输入和材料矛盾需显式记录边界，不通过私有 API、数据库操作或读取被测应用实现来补足。

初次验收使用两款已有 codex-base 冻结应用，无需修改 Harness、运行生成模型或调用官网。仍使用归档 variant 的既有产物，不改变 pi-team-mixed 是唯一活动 variant 的约定。不提交 Git，不覆盖其他任务工作区、远端服务或历史实验。

## 最小运行路径

复用已有 `package_arc_replay.py` 和冻结回放 ZIP，将每个独立场景展开为一个通用 lab job。现有 `arc_bench_adapter.py` 的单阶段模式已经能够运行回放入口及指定 tests-dir；入口只交付冻结软件，未涉及模型。第一版无需为此给适配器添加另一个生成/评测分支。

每个 job 使用独立的 tests bundle、官方 workspace 和容器，回放相同应用后进行确定的 UI 准备和目标检查。不同场景可以并行；一个场景的连续操作和多浏览器角色检查在同一应用实例内完成，多角色使用同一应用下的不同 BrowserContext。场景 ID 放在作业 task 标签中，调用官方 Runner 时仍显式传真实任务 slug github 或 sheet；具体归并依据选择文件的 task/scenario_id，不从目录名称猜测。

WSL Runner 固定路径为 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner`，已有镜像 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`。实施时保存实际 Runner 文件身份和镜像 ID，不拉取最新版替换。测试使用镜像实际预装的 Playwright 1.57.0，不能从另一份公开 benchmark 的 1.61.1 package 文件推定运行版本。原始官方 local-result 与完整 Playwright 报告保留，自建报告解释其阶段证据，不改写官方结果。

不另建调度器：场景并发直接使用 lab.run 的 max_parallel。不从需求 dependencies 自动生成运行 DAG或跳过用例：这些字段表达产品语义依赖，所有独立场景均从新状态开始，其准备步骤自行验证前提。

## 源码归属与接口

| 位置 | 内容与边界 |
| --- | --- |
| `benchmarks/hackathon/README.md` | 当前测试合同、材料版本、解释边界、运行及结果阅读入口。 |
| `benchmarks/hackathon/coverage.json` | 全部 71 条需求及稳定场景 ID 的映射；每场景写出目标行为、固定准备方式、需求依据及已知解释边界。它是覆盖清单，不是可执行步骤 DSL。 |
| `benchmarks/hackathon/github/*.spec.ts` | 按身份、组织、仓库、代码/分支、Issue、PR 业务领域聚合原生 Playwright 用例。 |
| `benchmarks/hackathon/sheet/*.spec.ts` | 按工作簿、工作表/结构、编辑、公式、数据分析聚合用例。 |
| `benchmarks/hackathon/support.ts` | 必要的场景选择、Playwright fixture、带阶段的 test.step 与失败证据保存。只复用真实重复操作，不引入 page-object 类层次或插件系统。 |
| `benchmarks/hackathon/report.py` | 从冻结覆盖清单、run 状态及完整 Playwright/阶段记录输出 JSON 与可阅读报告。与业务断言一起版本化。 |
| `experiments/hackathon-local/matrix.py` 与 README | 按任务/场景选择生成 tests bundle 和现有 lab manifest，声明外部 Runner、镜像、需求和回放制品。只准备清单，不隐式开跑。 |
| `lab/arc_bench/arc_bench_adapter.py` | 保持现有单阶段接口，补齐本次调用的容器取消/终态核对；原始产物复用现有 artifact_paths 采集，不引入业务分类。 |

不在通用 lab.run、OTLP、variants 或 Harness 中添加 Hackathon 业务依赖。当前文档只补充专用测试集入口和目录归属，旧四配置运行说明仍明确历史用途。测试集正文的完整说明由 benchmarks/hackathon/README 持有，不复制到多份任务文档。

## 测试装配与场景选择

镜像中的生产 Runner 每次重写 tests/playwright.config.ts，testDir 为当前 tests 目录，worker=1，默认 timeout=10 秒且 trace/screenshot 关闭；没有现成单场景 grep 参数。因此不能把自带配置文件作为生效依据。

采用按领域组织 spec，加一个有明确范围的场景声明 helper：同步读取 bundle 内的 selection.json，仅向原生 Playwright 注册对应场景，不将其他场景注册为 skipped。未指定场景时允许官方 Playwright 枚举完整测试集，用于与 coverage.json 对照；实际矩阵必须指定场景，并检查官方报告恰好包含该 ID。selection 同时保存 suite 内容身份、真实 task 与需求哈希，完整可执行测试材料由 lab 冻结。所有 spec 的模块顶层只声明用例，不执行应用操作；枚举与运行使用相同的选择输入。未知或重复 ID、实际注册数量不为一均为评测材料错误。

选择 helper 不执行步骤、不解释操作 DSL；业务控制流继续写成普通 TypeScript 与 Playwright 调用。每次场景只有一个原生 test，可包含多个有名的 test.step。这一结构既保留场景级数据隔离，又避免为每个细小用例建立一个源码文件。

通过实际 spec/suite 上的原生 test.use 配置 trace=on、screenshot=only-on-failure，不能只声明一个会被官方配置覆盖的 fixture 默认值；超时使用显式场景策略并写入运行材料，不能无意继承 Runner 的 10 秒总超时。初始流程预算按真实 UI 步骤设置，选择器等候有界，不自动重试或刷新绕过失败。无需自带 package.json/node_modules：官方会重写测试 package 并链接镜像内的 Playwright，附加库不会被安装。仅使用 Playwright 和 Node 标准库。

配方声明采集 `workspace/official/tests/test-results/`、`workspace/official/template/.arc/`、`workspace/official/execution.debug.log` 及官方根结果/装配元数据。报告中的 `/workspace/` 附件路径映射到本次 `workspace/official/` 展示，保留原 JSON。不要递归复制 tests/node_modules 的镜像内符号链接，也不重复归档整个部署目录。具体依据见 [Runner 预演](runner-preplay.md)。

## 场景语义与覆盖顺序

覆盖清单先从官方 ROOT/FOLDER/ATOMIC 文本推导，再编写用例，最后对冻结应用运行。来自历史诊断的已知缺陷只帮助验收用例的诊断能力，不改变其预期结果、选择器或准备路线。

Sheet 的祖先合同已经明确 Worksheet grid 的 grid role、gridcell 的坐标名称及 aria-selected、Formula bar、Edit A1 内联编辑器、行列 header 和菜单角色。按这些公开合同实现共享操作，不猜测 CSS/data-testid。GitHub 必须保留不同操作的显式角色集合，不能把 Read/Triage/Write/Maintain/Admin 当作单调累加权限。

| 领域 | 原子需求数 | 首要可观察检查 |
| --- | ---: | --- |
| GitHub 身份 | 5 | 注册及逐字段错误、登录/失败统一提示、恢复、退出、改密与后续会话。 |
| GitHub 组织 | 7 | 公开仓库可见性、创建组织/团队、层级、成员增删、用户及团队授权。 |
| GitHub 仓库 | 6 | 搜索、创建、fork、clone 展示/复制、公开概览、visibility。 |
| GitHub 代码与分支 | 8 | 文件/历史/diff/搜索、分支切换创建与默认分支、Web 文件变更。 |
| GitHub Issue | 9 | 列表过滤、详情、创建编辑评论、assignee/label/milestone、关闭重开。 |
| GitHub PR | 12 | 分支保护、列表比较、普通及 draft 创建、详情/diff/inline review、审查人、合并与关闭重开。 |
| Sheet 工作簿 | 5 | 打开、新建、重命名、CSV 导入/导出及失败后无部分数据。 |
| Sheet 工作表与结构 | 6 | 增删改名切换、插入删除行列及关联状态变化。 |
| Sheet 编辑 | 5 | 单元格/公式栏、二维粘贴、范围选择、复制剪切、撤销重做与隔离。 |
| Sheet 公式 | 4 | 运算与聚合、相对/绝对引用、依赖重算、错误值及恢复。 |
| Sheet 数据分析 | 4 | 排序、过滤、验证规则、透视表与刷新。 |

先实现入口与共享操作，再实现各领域；这只是源码依赖顺序，不让低层场景失败阻止其他独立场景派发。每条需求可以对应多个场景，不预设总数 200，不把不相关行为塞进一个超长场景。需要连续操作才能观察的撤销、权限撤回、会话隔离等保留在同一场景。

数据准备是明确的用例步骤。Sheet 以 UI 建立所在场景的固定数据，记录对不完整/冲突种子文字的解释；交付种子检查按场景前提分别报告，不要求同一个初始 A1 同时满足 Region、Item 和数字 2。互斥种子未定义切换机制的地方记录合同歧义，不汇成多个互相矛盾的必过断言；UI 准备后的功能结果继续独立呈现。

GitHub 对没有公开创建入口的 labels、milestones 等只使用合同要求的交付数据；角色凭据或具体名称缺失时记录材料缺口，不能从生成应用源码提取后冒充官方既定合同。有公开 UI 构造路径的角色和对象可以作为事先定义的准备步骤，其中 REQ-6-1 已提供 Admin 设置 test status 的控件，不能把所有 check 状态都视为只能预置。但准备步骤不得抹掉独立交付种子检查。不可用账户等既未给出可登录身份、又无公开构造路径的条件标注不可测/阻断依据，不臆造账户。相关需求证据见 [覆盖预演](coverage-preplay.md)。

UI 准备使用浏览器原生剪贴板权限、读写和按键；权限/浏览器能力失败要与应用拒绝粘贴或复制分开。直接重开页面只使用先前由真实 UI 获得的可见地址，在需求指定持久化检查时执行，不猜测内部路由或用整页跳转绕过登录状态缺陷。

## 原始证据与结果口径

场景结果关联 requirement IDs、场景 ID、准备/目标步骤、原始 Playwright outcome、错误全文和附件。目标动作之前的准备失败记 blocked；正在被检查的入口/登录行为本身失败仍是 failed，不能统一包装成 blocked。可判定的缺少控件/数据属于应用观测；缺少测试定义、错误选择器或浏览器进程故障属于评测问题，不把所有异常兜底为应用失败。

实验执行完成与业务通过分开。Runner 有完整该场景结果及应用身份时，底层 run 可以 completed，即使业务断言失败。适配器使用现有 expected-tests=1；报告仍须核对实际场景 ID，计数为一不证明选对了用例。报告结合覆盖清单把其他未派发/未实现场景列为未执行；设施失败标记评测不完整并保留已得结果。准备阻断不写成 skipped/pass 来改变官方计数。

需求级主指标是本地必需检查全部通过的需求数，分母固定 GitHub 47、Sheet 24；同时显示场景级进展。只执行选定子集时明确是局部诊断，未执行需求不被删去。不将 UI 可观察测试通过声称为内部事务/存储实现得到证明，不把不完整覆盖标为全需求通过。

报告按共同失败步骤归类，保留每条独立失败事实与证据，不自动推断根因因果关系。应用、需求、测试集、Runner/镜像身份都保存，只有相同检查集合的结果才能直接比较。不同套件版本继续展示原计数而不回算历史成绩。

## 实施顺序与验收实验

1. 将全部原子需求及祖先合同对应到覆盖清单，明确每场景准备和断言、无法观测内容与歧义解释。通过独立需求预演修正，避免在看到软件行为后调整预期。
2. 实现最小原生 Playwright 共用操作、选择和证据记录，再完成 GitHub/Sheet 各业务领域的真实用例。
3. 实现实验配方和报告，接入现有回放 ZIP、官方 Runner 和通用 lab。核实源码冻结与容器生命周期边界；范围内必要的 ARC 接入修复同期完成。
4. 在 WSL 独立源码快照物化场景清单、核对实际 Playwright 枚举及有效配置。该操作针对 benchmark 用例，不引入基础设施自检或模拟测试。
5. 在已有 codex-base 两题冻结应用的独立副本上先执行有独立观察依据的场景，核对已知成功行为和缺陷。核实场景间数据不互相影响以及 trace/截图确实能打开。具体选择包括 GitHub 登录后状态、Sheet 打开/编辑公式/刷新、新建/导入跳转、跨工作簿 Undo。
6. 核心操作能正确报告后，完成这两款应用的全套独立场景评测。共享测试错误修复后只重跑受影响场景，保留旧错误；应用缺陷不修、不刷新绕过。全套结果按 47/24 要求汇总并报告测试路径的正例证据缺口。
7. 更新运行与目录文档，保存最终输入/套件身份、结果和预演问题处理记录，再交用户复核。新的生成、官网评分、更多 variant 矩阵或 commit 另按用户指令进行。

验收输入使用既有 `codex-base-artifact-replay.zip`（SHA256 `3f78afcaa8e79029bc00734b46044f08d8ea77cdf22ef93d87624e717805e6d6`），本轮已只读核实字节身份及包内 12/21 个应用文件。源 run 分别为 `codex-base-hackathon-github-97ad8b8eec` 与 `codex-base-hackathon-sheet-67ac86e938`，均位于 WSL `factory26-official-local/runs/hackathon-generation-20260924/`。初始真实场景采用 4 并发并记录资源/部署耗时，随后使用同一可配置并发参数运行完整矩阵，不给场景或 variant 加独占锁。

本轮只读资源观测为 WSL 12 CPU、约 10 GiB available memory、65 GiB 可用磁盘，官方每个容器默认 1 CPU/2 GiB。历史两题安装构建到可达分别约 2 秒与 8 秒；不以此保证冷缓存或新并发时的耗时。逐场景复制原始小型回放包和测试材料，保留现场；不要重复复制几百 MiB 的完整 Harness runtime。

没有实现新 runtime、缓存服务或黄金参考应用的计划。生产 Runner 会为本次两款应用每场景重新安装构建，第一版如实接受并测量成本；保留应用状态隔离的前提下才讨论后续构建复用，不提前共享可写构建目录。

## 已定位的 ARC 生命周期补口

现有 lab.run 在取消时只终止宿主 job 进程组，官方 local_submit 的 docker run --rm 没有单独保存容器 ID 或 finally 补偿。Docker daemon 中的容器可能继续运行。因此需要在 ARC adapter 的调用边界识别当前独占 workspace 的容器，在正常/异常退出和可处理的取消信号后核实终态并清理自己拥有的残留。

官方入口会在 docker run 前 flush 打印精确的 `Container: arcbench-local-<12位hex>`，优先读取这次 invoke 日志中的名字，无需广扫 Docker 容器。adapter 主线程为 SIGTERM 提供可展开栈的退出处理，在共享 invoke 的 finally 中 inspect 该名字，并核对 Type=bind、Source=该次命令的 --workspace 绝对路径、Destination=/workspace。匹配才定向清理；单阶段的真正源路径是 adapter workspace/official，生成与评测分支分别为 official-generation、official-evaluation。正常运行结束同样核实所持有的容器终态，不按镜像或名称前缀批量停止。

清理过程及失败写入当前 workspace 日志。宿主 SIGKILL、容器创建交错或 daemon 不可达时无法保证 finally 完成，必须保留精确名字、挂载及末次核实状态供恢复，不新增后台守护服务或声称绝对无残留。

只在 ARC 边界补这一条实际取消缺口，不修改上游 Runner 或通用执行器，不新增基础设施模拟测试。开工后通过当前真实应用场景的取消操作核实正常取消路径；若无法在既有 5 秒终止窗口完成可靠处理，先保留可诊断状态并报告证据，再判断最小调整，不堆叠重试和 watcher。

## 开工前检查点

独立 Runner 预演已确认场景选择、附件持久化路径、应用状态隔离和取消缺口；独立需求预演确认公开交互合同、覆盖/阻断口径与材料歧义的处理。两者均建议进入开工复核，必要约定已纳入本计划，未发现剩余静态方案阻断。实际单场景注册、trace 采集、UI 准备和取消处理仍须在源码实施后用上述真实应用验证，不能把预演结论当作运行验收。

向用户提供改动范围、验收输入与已知限制的简短说明，再按当前阶段约定进入源码实现。
