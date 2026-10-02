# Hackathon 本地模拟测试集

## 当前目标与阶段

2026-09-25 用户提出：“好的，接下来我们来‘建立 hackthon bench 的本地模拟测试集’。”用户随后以“是的，认可”确认第一轮定位：覆盖全部公开需求，独立编写 Playwright 用例，不强求复刻官方 200 项划分，不把本地通过率当官方得分预测。第二轮用户以“同意”确认独立场景状态、公开 UI 准备数据、单独检查交付种子，以及准备失败明确标为未测到的取舍。第三轮用户再次以“同意”认可结果口径、目录归属和已有冻结应用验收设计，并进入实施计划与预演。[实施计划](plan.md)、[Runner 预演](runner-preplay.md) 和 [覆盖预演](coverage-preplay.md) 已完成。用户现以“同意开工；验收就是将先前上传到官网的生成好的软件交给我们写的模拟eval进行评估，不需要重新生成。”授权实现与验收。目录整理已由 b32be1e 提交；本任务不接管工作树中其他任务的改动。

目标是针对 Hackathon GitHub、Sheet 的生成应用建立可重复、可诊断的本地功能评测。用例必须独立于具体 Harness、生成软件实现和通用实验核心，能够对冻结应用重复执行。生成应用自身的验收属于仓库允许范围；这不改变禁止 Factory/开发基础设施测试的约定。实际构建与评测在 WSL 执行。

## 已核对的材料

官方需求快照位于 WSL `/home/yyh/Development/factory26-official-local/platform-inputs/hackathon/{github,sheet}/requirements/`，包含 requirements.yaml 与参考图。来源 ZIP、哈希和取得过程见 [历史 Hackathon 实验](../hackathon-variants/packet.md)。本轮只读取现有快照，没有更新输入或启动模型。

对两份 YAML 的实际统计：GitHub 有 47 条 ATOMIC、100 个 scenarios；Sheet 有 24 条 ATOMIC、100 个 scenarios。Sheet 的 100 个场景都包含 `the requested workflow` 泛化措辞；GitHub 抽查的注册场景也有重复且缺少明确动作的描述。ATOMIC description 提供更具体的控件名称、role、scope、状态、错误消息与持久化规则。因此不能仅靠场景数量或标题恢复官方测试。

2026-09-25 读取 [公开 ARC-Bench README](https://github.com/code-philia/arc-bench)：它规定从应用入口通过 Playwright 操作，应用自行初始化需求种子，不依赖私有 reset/seed API；同一应用的测试单 worker 顺序执行。此为公开 benchmark 的约定，尚不能证明 Hackathon 隐藏测试逐项采用相同实现。本轮未取得 Hackathon 官方测试。

已有 `lab/arc_bench/arc_bench_adapter.py` 支持通过官方 Runner 对冻结应用评分，生成与评测可分离。`arc_matrix.py` 当前有来源清单和输入哈希约束；接入自建用例时需要明确记录本地 suite 身份，不能用官方需求身份冒充官方测试身份。通用 `lab/run.py` 和 OTLP backend 无需了解业务用例。

既有真实失败及原始证据入口保存在历史 Hackathon packet：GitHub 登录后会话状态未更新、两个同名 Sign in 控件；Sheet 新建/导入不进入编辑器、跨工作簿 Undo 错位。它们可以验证新用例是否发现公开需求中的实际违约，但不能作为调整预期结果或增加需求外契约的依据。官方 Sheet 重试只返回 1/100、没有逐例结果；不能用这个总数校准本地用例的正确性。

## 已认可的定位与待细化设计

目标已确定为覆盖公开需求的本地代理评测。保持官方 Runner 的部署方式和浏览器交互边界，以原子需求正文为主要依据，把具体场景转成确定的操作与断言；逐项保存需求对应关系与本地解释。结果明确标记为自建测试通过率，不预测官方得分，不为了凑齐 200 项重复或臆造场景。

完整范围包含全部 71 条原子需求，先完成需求到用例的覆盖清单，再逐步实现。操作覆盖正常流程、拒绝与状态不变、刷新后的持久化，以及需求明确要求的账户/工作簿隔离。选择器遵守需求规定的可访问名称、角色和范围；不得根据既有生成应用增加 CSS、私有 API 或直接 URL 的补救路径。

已确定每个独立场景使用独立应用状态，可并行评测不同实例；同一场景内采用确定的连续操作。浏览器 context 隔离不等于数据隔离，实施准备时须核实服务端状态也从冻结副本独立建立。缺失种子、前置流程失败、业务断言失败和 Runner 故障保留具体证据与区别，不能简单跳过缺失功能后提高通过率。

已认可测试源码归 benchmarks/hackathon，实验清单归 experiments/hackathon-local，Runner 接入归 lab/arc_bench，原始报告留在实验产物目录。不新增通用测试框架。

## 第二轮：种子与状态隔离

本轮定向读取原需求，确认 Sheet 对同名 Q3 Sales 存在分组初始状态：REQ-1 要求 A1=Region，REQ-3 的 A1:B2 为 Item/Qty、Pen/4，REQ-4 要求 A1=2、B1=3，REQ-5 为 Region/Sales/Status 销售数据。需求没有公开切换这些状态的接口。仅重启同一个冻结应用不会自动满足这些不同前提，不能凭空要求应用实现评测专用 seed/reset API。

GitHub REQ-1-3 明确要求每个改密场景拥有独立账户状态，REQ-2-2-4 要求每个移除成员场景开始时成员仍然存在，REQ-6-5 要求合并场景的种子状态独立恢复。因此串行执行本身不能防止前例改密、删成员或合并 PR 污染后例。

已认可采用场景独立的运行状态：各场景从同一冻结交付副本启动，使用独立的可写目录与应用实例；场景内保留连续用户操作、刷新和多会话观察。不同场景可以并行，不依赖测试后通过业务操作恢复数据；不让一个场景的清理失败污染另一个。实例创建与构建资源复用属于后续实施细节，需要核实官方 Runner 能提供的边界，不能仅隔离浏览器就声称数据库已隔离。

已认可的数据准备分为两种明确目的：直接检查公开要求的交付种子；对需要特定状态的功能用例，通过公开 UI 执行预先写明的准备步骤。准备方式在用例设计时确定，不根据被测实现是否失败临时切换。Sheet 的分组初始状态由这种可见准备建立并记录为本地解释；不修改被冻结源码、直接写数据库或假设私有 API。GitHub 无公开 UI 可建立的状态只能依赖交付种子，缺失时明确报告。

交付种子缺失不能因为功能用例准备成功而被抹去；准备阶段失败标记对应功能未测到并关联具体阻断步骤，不宣称后续业务断言已失败或已经通过。统计保留全部计划用例及阻断数，不通过只计算已执行断言提高通过率。具体计分单位与展示在后续设计中收敛。

用户已接受公开 UI 的确定性场景准备：它能解决已观察到的 Sheet 初始状态冲突，但会让下游功能评测依赖基本编辑等准备能力，并且属于本地测试语义，不能声称已复刻官方 seed 机制。

## 第三轮：结果、归属与验收设计

已认可主要按原子需求展示本地检查全部通过的数量，GitHub 分母 47、Sheet 分母 24；下钻后显示场景通过、目标断言失败、前置阻断和未执行的数量。每条需求的已定义必需检查全部通过才计入通过数；未实现用例、阻断和未执行不能从分母移除。开发中的不完整 suite 明确标记覆盖未完成，不能与完整 suite 直接比较。保留场景级细节以反映局部进展，不新增任意权重或模拟官方总分。

每次结果绑定需求、测试集、冻结应用及 Runner/镜像身份。场景保存准备/操作/断言步骤、原始异常、失败截图与 Playwright trace，报告可按共同失败步骤聚合；同一登录步骤的多次失败只能称共同阻断，不能没有额外证据就推定其他功能均有缺陷。部署/测试枚举/报告收集故障会使评测不完整；已完成的场景证据保留，但不将设施错误转为业务零分。

本轮读取 WSL 现有官方 local_submit.py：walk_playwright_report 把 failed、timedOut、interrupted 和 skipped 都归为未通过；完整原始报告位于 template/.arc/playwright-report.json，local-result.json 只是其摘要。因此本地诊断应读取完整报告及场景阶段记录，保留官方原始结果，不修改官方解析器或把准备失败写成通过。通用 lab 状态继续透传结果，不导入 Hackathon 的解释规则。

已认可目录为 benchmarks/hackathon/：github/、sheet/ 分别保存业务用例，必要的共享 Playwright 操作、覆盖映射和结果解释靠近用例。experiments/hackathon-local/ 保存实验配方；lab/arc_bench/ 只维护官方 Runner、冻结应用及实验协议的接入。逐次结果继续在 WSL experiments/<id>/runs 和 analysis 中。具体文件数量由实施所需确定，不预建一套插件/注册框架。

已认可首轮以已有冻结应用的独立副本验收，无须再次生成：核对已确认的登录、创建/导入跳转、跨工作簿 Undo 缺陷，以及已观察成功的打开工作簿、公式计算和刷新持久化。失败定位须与独立浏览器观察相符；只能在真实正/反例上确认相应测试路径，不能以全套能够枚举或旧应用大量失败宣称所有断言正确。其余路径的实证缺口随覆盖映射记录，必要时再讨论补充应用来源。

## 实施准备的新增证据

独立 Runner 预演核实指定镜像存在；官方配置没有单例 grep 接口，会覆盖 tests/playwright.config.ts，并默认关闭 trace/screenshot。测试级 test.use 可覆盖，完整附件写在 workspace/tests/test-results，官方 JSON 在 workspace/template/.arc/playwright-report.json。因此选择文件与测试侧配置足以接入，无需改通用执行器或官方源码；容器生命周期与取消边界继续预演。

主 Agent 只读核实已有回放 ZIP 的 SHA256 仍为 `3f78afcaa8e79029bc00734b46044f08d8ea77cdf22ef93d87624e717805e6d6`，GitHub 12 个、Sheet 21 个应用文件与包内 manifest 的哈希全部匹配。原始生成记录均 completed/requirements-only；归档事件显示 GitHub 部署阶段约 2 秒、Sheet 约 8 秒。这些历史耗时只用于评估逐场景重新部署的可行性，不作为新并发实验的性能保证。

两项独立预演均建议进入开工复核。已采纳 ROOT/FOLDER 继承合同、分场景种子解释、多角色共享本场景应用但隔离 BrowserContext、需求 dependencies 不作为运行 DAG、完整报告校对实际场景 ID、正例验证边界等约定。官方入口的 stdout 在容器启动前记录精确名称，ARC 适配层可据此核实本次 workspace 挂载并处理取消；不需要扫描停止其他容器。此必要源码补口已经加入实施范围。

已有完整 suite 及报告尚未实现；本轮未运行模型、应用或测试。读取镜像使用的临时容器均未启动且已删除。实施后计划先以 4 并发在已有两款冻结应用上完成有独立证据的场景验收，再执行完整本地 suite，记录缺定义或尚未得到正例验证的路径。运行只消费冻结回放包，不启动生成模型或官网提交。

当前进入实现与验收。源码改动范围是测试集、实验配方/报告、ARC 取消补口及对应文档；不修改通用 OTLP 或任何 Harness 实现。验收只消费先前上传到官网的冻结软件回放包，不重新生成。

## 实现与验收进度

本地源码已实现 71 条原子需求的 Playwright 场景、固定分母报告、逐场景矩阵和 ARC 容器终态补偿。静态覆盖核对为 GitHub 47、Sheet 24，场景 ID 无缺失、重复或多余；Python 文件可编译，任务范围 `git diff --check` 通过。使用仓库已有 Playwright 做了不启动浏览器的真实枚举：完整材料注册 71 项，选择 `sheet-req-3-2-2` 时只注册该 1 项。枚举显示场景声明归属 `support.ts`，因此 trace/screenshot 配置保留在同一 Playwright 文件作用域。跨工作簿 Undo 场景已补为通过公开 UI 创建第二工作簿、在 Q3 Sales 执行 undo/redo、再核对第二工作簿不被历史污染。

用户授权中断 WSL 后，实跑已完成。启动故障的根因是 Windows C 盘耗尽，Debian ext4 随后只读；已把 Debian VHD 迁移到 `D:\WSLDebian` 并修正注册表 BasePath，恢复后的根文件系统可写且有约 55 GiB 空间。WSL 重启还暴露出自动生成 DNS 指向不可用地址；本轮使用 Windows 当前 DNS `172.18.0.2`、`192.168.252.11` 恢复容器内 npm 访问。首次完整运行中受这两项主机故障影响的 Sheet 尝试没有计入业务结论，修复后重新执行全部 24 项。

最终验收使用回放 ZIP `3f78afcaa8e79029bc00734b46044f08d8ea77cdf22ef93d87624e717805e6d6`、`arcbench-local-submit:latest`（image ID `sha256:840105914e…19d`）、4 并发，在每场景独立的官方 Runner 实例中完成。汇总为 GitHub `0/47 passed, 4 failed, 43 blocked`，Sheet `11/24 passed, 11 failed, 2 blocked`；`incomplete=0`、`unexecuted=0`。GitHub 的主要共同阻断是冻结应用不能用公开凭据建立登录会话，因此 43 项不能解释为各自业务能力失败。Sheet 通过项为打开工作簿、导出 CSV、增加/切换/重命名工作表、编辑/选择单元格，以及四项公式计算与持久化能力。

收口校验从最终报告选出的 71 个 run 逐一读取原始 Playwright JSON：场景 ID 71 个且无重复，每个 run 恰好一个测试、一个 trace 和 `status=absent` 的容器清理终态，共 60 张失败截图；不存在遗留的 ARC 容器。注册、仓库搜索和工作表重命名初跑暴露了同名或前缀匹配导致的测试选择器歧义；分别收窄到 `main`、精确名称或对应 dialog 后单独重跑，其中工作表重命名得到通过，另外两项留下真实业务失败。结果位于 WSL `/home/yyh/Development/factory26-official-local/experiments/hackathon-local-eval-20260925/full/analysis/`，原始 runs 位于同级 `full/runs/`。本轮没有调用模型、重新生成软件或访问官网。

## 结果身份与局部说明修正

用户指出矩阵写死 `codex-base-artifact-replay` 会让替换 `--replay` ZIP 后的 run 仍带旧标签，形成第二份身份来源。现改为读取 ZIP 内 `replay-manifest.json`，按需求哈希取对应 case 的原始 `variant`；本次冻结包解析出的值是 `codex-base`。每个新 job 同时冻结测试脚本和 `coverage.json`，selection 保存其联合哈希。配方 README 说明了回放身份、重试选择与报告身份口径。

报告现在逐条核对选中 run 的场景、原子需求、需求文件哈希和冻结测试源码，拒绝把不同回放输入的结果混为一个报告。顶层 `suite_sha256` 只在选中 run 具有相同的完整测试集快照时给出；旧 run 缺少覆盖映射快照时保留逐条源码哈希并将顶层值置空。用既有 71 条真实 run 重算，结果数未变，识别出 3 个历史测试源码快照且 `coverage_snapshots_complete=false`。在 WSL 仅生成一条新清单，确认其 variant 来自 ZIP 且新测试包含覆盖映射；未重新运行应用、模型或评测。
