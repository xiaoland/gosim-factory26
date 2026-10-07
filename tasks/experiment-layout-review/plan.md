# 实验设施目录整理实施计划

## 状态、范围与不变量

本计划对应用户已认可的 lab / experiments / variants / submission 职责划分。计划和预演阶段曾限定“别开始落地”；用户随后明确说“好的，开始落地”，因此目录迁移与已授权验收已执行。这里保留实施时的约束与步骤，实际结果以 [任务包](packet.md) 为准。

实现目标是让源码位置表达所有者，使通用执行和 OTLP 与具体 Harness 分析分离，并让实验定义、机器执行清单和历史产物各有明确位置。沿用当前 CLI 参数、运行结果和 ZIP 协议的有效部分，不引入安装服务、插件框架、配置 DSL 或统一 Agent 事件模型。

必须保持的边界如下：

- 唯一活动 variant 仍是 pi-team-mixed。raw/Hackathon 迁移源码归属，不改模型、角色、输出预算、重试策略、打包协议或启用状态。
- 执行器通过 argv 和结果文件接入任意 Runner；OTLP backend 保留原始批次。两者不导入 ARC 适配器、Factory、Braid、raw 或分析模块。
- 完整低分、执行中断和没有测试三者继续区分。核心状态不重新解释 bench 分数，分析输出不回写实验终态。
- 单 run 的 inputs/workspace/artifacts、run.json、日志、telemetry.sqlite 及官方 workspace 内部结构不迁移。旧 ZIP、输入快照、原始会话、官方 journal 和机器执行清单不重写。
- 在 WSL 构建和执行实际工具；macOS 只编辑、传输和查看。实施授权不隐含模型调用、benchmark、官网 POST、服务终止或提交授权。

## 源码去向

模块模式统一为在仓库根运行 `python3 -m lab.<模块>`。增加无副作用的包初始化文件，采用显式包导入；不在新 CLI 中层层修改 sys.path，也不为所有旧路径留转发壳。可独立分发的 adapter/noop/replay 入口继续是自包含脚本。

| 当前文件 | 目标 | 处理 |
| --- | --- | --- |
| scripts/local_experiment.py | lab/run.py | 保留 run/status/telemetry 子命令；status 转到通用记录读取。 |
| scripts/otlp_store.py | lab/otlp.py | 原始批次接收、存储、查询和导出 API 不变。 |
| scripts/wait_local_runs.py | lab/wait.py | 保留显式 run 路径、终态和 controller PID 检查；不新增恢复或心跳功能。 |
| local_experiment 的 status 分支 | lab/status.py | 读取通用 run.json；保留 result 原值和声明的路径，不扫描私有工作目录。 |
| scripts/arc_matrix.py | lab/arc_bench/arc_matrix.py | 保留单文件输入冻结和 argv 占位符。 |
| scripts/arc_bench_adapter.py | lab/arc_bench/arc_bench_adapter.py | 保持 stdlib 自包含，不从 lab 导入运行依赖。 |
| scripts/arc_bench_noop.py | lab/arc_bench/arc_bench_noop.py | 保持单文件写入评测 ZIP 根 main.py 的行为。 |
| scripts/package_arc_replay.py | lab/arc_bench/package_arc_replay.py | 导入同包 adapter 的排除项，按同目录取回放入口。 |
| submission/arc_replay.py | lab/arc_bench/arc_replay.py | 源码位置改变，制品内仍名为 main.py。 |
| scripts/playground.py、competition.py、official_matrix.py | lab/arc_bench/ 同名模块 | 修正包导入与仓库根；保留 HTTP/journal/计费模式及旧数据路径。 |
| scripts/inspect_runs.py、factory.py、run_feedback.py、run_viewer.py | lab/analysis/ 同名模块 | 保留专用消费者和历史读法，调整依赖方向、导入与输出位置。 |
| scripts/braid_telemetry_viewer.py 及同名 HTML | lab/analysis/ 同名文件 | 两者一起移动；继续从 OTLP 调用 Braid CLI 解码。 |
| inspect_runs 内 ARC 结果解释 | lab/arc_bench/results.py | 负责官方结果、阶段事件、评分计数和 bench 证据路径；不识别 Harness 会话。 |
| inspect_runs 内私有过程目录发现 | lab/analysis/native_evidence.py | 负责 Factory、raw、原生 Hackathon 的过程证据入口；只作分析补充。 |
| submission/raw_main.py、raw_models.json、raw_otlp.py、raw_responses_compat.py | variants/raw/ 同名文件 | 同一份源码仍供历史 raw 和 Hackathon 包取材；保留归档状态。 |
| submission/hackathon_main.py、hackathon_models.json、agents/ | variants/native-hackathon/ 同名文件 | 保留原生四配置的历史实现和角色材料。 |
| experiments/multi-agent-lite.json | experiments/archive/multi-agent-lite.json | 标明旧格式及退役入口，当前文档不再推荐执行。 |

`scripts/runtime.py`、`package_agent.py`、`package_raw_core.py`、`package_hackathon.py`、`agent_support.py`、`braid_runtime.py`、`core.py`、`sources.py` 继续原位。后两种专用打包器仅修改取材路径。公共 Dockerfile/build.py 仍在 submission；团队 variant 的 support 复制布局和构建接口保持原样。raw/Hackathon 不强塞进当前要求 Braid 的 package_agent 协议。

模型网关及 Responses 兼容层仍在 scripts，源码和 PYTHONPATH 均不改。网关只是实验的外部服务；本次不改供应商路由、secret 格式或模型参数。PYTHONPATH 中虽有当前 callback 不使用的 submission 分量，但迁移不会移除 submission 目录，这不构成断点，无需为路径整洁扩大到服务代码。已有服务不因目录整理重启。

`scripts/playground_probe.py` 是旧环境探针，没有当前源码消费者；实施时退役该脚本并移除当前操作入口，历史报告保留。不会迁到 lab 后作为设施验收重新启用。

## 查询与 CLI 接口

通用 `python3 -m lab.run status RUN` 直接呈现 run.json 的执行状态、原始 result、输入身份和记录路径，不把未知 Harness 套成 ARC 的生成/部署/评分模型。原来增强的 Factory/ARC 摘要继续由 `python3 -m lab.analysis.factory show --run RUN` 提供，文档明确两者用途和输出区别。核心 status 的旧增强 JSON 不是兼容接口；已知调用方必须改到明确的消费者，不通过通用层再次 import inspect_runs。

`lab.arc_bench.results` 从外层结果和官方 Runner 证据中解释 ARC；`lab.analysis.inspect_runs` 组合它与 `native_evidence` 的会话入口。Factory 原生清单、Pi 终止原因和历史报告读取继续由分析侧维护。Hackathon 的 `.arc/hackathon` 由其分析消费者识别，加入主事件、stderr、原生会话路径；没有记录时说明缺口，不把其他会话当补齐，也不据此修改分数。

结果来源保留：单阶段官方结果、两阶段 generation/evaluation、requirements-only 和旧 Factory evaluation 格式分别读取。实际 Lite 两阶段结果没有顶层 mode/score，必须结合明确的 ARC 结果字段或 workspace 来源识别，不能只按 mode 分派。requirements-only 的部署事件在 official-generation，不能因没有 official-evaluation 就丢掉已经保存的部署事实；该模式的评分仍为 skipped/null。缺少 adapter 标准入口记录时，只有分析侧可展示历史 raw/Factory 的替代线索，必须指出来源；它不成为核心执行成功条件。新 producer 或未知 workspace 仍可通过通用 status 查看完整保存的 result。

官网模块的 ROOT 继续指向仓库根，`runs/playground`、既有 Competition journal、登录 cookie、锁和计费模式保持原位置。当前 playground 和 official_matrix 都从 agent_support 导入 save；实施时将同等的临时文件加 replace 写入实现放在 playground，official_matrix 改为从同包 playground 导入 save，不保留裸 agent_support import，也不改变持久化行为。专用 Factory analysis 可以继续复用 `scripts.agent_support` 的文件函数，作为明确的 Harness 消费者；采用该 import 时 scripts 增加无副作用 __init__.py，不移动或改动已打包的团队 support。

官网离线验收使用分析 Viewer 读取显式 root 下的已有 journal，以及 playground 的 --saved 路径或纯摘要函数。Competition status/recover 会联网，不能作为本轮只读本地验收入口；--offline 是历史无模型提交选项，也不等于离线读取。跨机器 journal 副本放到新的分析输入目录，沿 Viewer 已支持的 runs/playground 或 Competition 布局读取，无需改变官方原始目录。

`run_viewer --root EXPERIMENT` 仍读取该目录下 runs，旧仓库根也可作为 root；本次不设计跨机器自动发现或多根索引。补充显式 `--output EXPERIMENT/analysis/viewer`，输出目录从输入根解耦；旧默认行为保留。Braid viewer 已有 --output，无需新增层。

Factory analyze 的私有缓存继续写入其输入 run/analysis，inspect_runs 的发现和会话关联都依赖该位置；本轮不修改这项成套契约，不增加外置分析索引。实验根的 analysis 保存独立 Viewer、Braid 网站和诊断报告，不要求所有 Harness 内部派生产物都迁出 workspace。

当前文档、Makefile 的 braid-report、当时的监控说明（已删除）、活动 task 的待执行操作统一更新为模块入口。历史报告、已执行命令和冻结清单不批量替换路径；涉及旧方案的 task 只增加退役/后继入口，不改写当时事实。未启动的旧机器清单属于当时实验记录，不直接重新派发；后续获授权运行使用新实验目录重新生成清单。

必须检查的文档映射包括 AGENTS.md 仓库地图、CONTRIBUTING 的修改位置/角色/诊断段、docs/product-tdd 的组件边界、docs/deployment/{index,hackathon,braid-diagnostics}.md、docs/index.md、variants/README.md、Makefile 和 当时的监控说明（已删除）。旧 multi-agent-lite 文件搬入 archive 后，tasks/developer-experience/{inquiry,boundaries}.md 等仍有效的 Markdown 链接只修目标，不改历史措辞。README 与新 experiments 导航指向当前入口，raw/native-hackathon 的新目录明确归档状态和专用打包方法。

## 源码位置与分发位置分离

ARC matrix 只冻结 adapter/noop 单文件。它们搬迁后仍保持当前 basename、argv 参数、stdlib 依赖和结果协议。`with_name` 随三者一起迁移仍有效，不能把 adapter 的执行命令改成依赖仓库 PYTHONPATH 的模块命令。源码侧 ARC CLI 使用 -m，冻结执行侧继续使用绝对脚本路径。

raw/Hackathon 源码归入 variants 后，打包器继续写出原有 ZIP 布局。raw 包仍含 main.py、raw_otlp.py、raw-config.json、runtime-executables.json、requirements.txt 和 runtime；Codex 附带两份 Responses callback。Hackathon 仍含 main.py、raw_main.py、raw_otlp.py、hackathon_models.json、raw-config.json、agents、skills、runtime 及其现有清单。raw_main 导入时读取包内 raw-config.json，因此不能拿归位后的源码当作已配置的可执行应用。

回放包仍按 requirements.yaml 哈希选应用，保留 main.py、replay-manifest.json、applications/<run-id> 和 requirements.txt。源码迁移不改变生成应用或 seed 数据，不修改包等待时间。各类包现有 manifest 并不相同；本轮不统一它们，也不把 replay/raw/Hackathon 接入只接受团队清单的 Competition 打包校验。

## 实验定义与 WSL 数据

新源码实验入口为 `experiments/pi-team-mixed-lite/matrix.sh` 与相邻 README。脚本只声明 pi-team-mixed、Lite 两题和两阶段模式，调用现有 arc_matrix；Agent ZIP 由调用者提供，其余 Runner、输入、镜像、env 文件、并发及输出路径沿用现有 CLI 参数，不另造参数解析器。配方只产生 manifest，不自动构建、启动模型或提交官网。它不固定某位开发者的绝对路径，不收录 secret 内容，也不建立新配置语言。历史 raw/Hackathon 定义作为归档说明链接到现有冻结清单，不重新启用。

机器输出采用以下布局。数据根由调用者选择，WSL 当前默认建议仍为仓库同级 factory26-official-local；未启动新实验前不创建空资源目录。

```text
platform-inputs/<competition>/<task>/
runners/<source-revision>/
runtimes/<build-id>/
packages/<variant>/<build-id>.zip
services/<instance>/
experiments/<id>/
  manifest.json
  controller.log
  runs/<run-id>/
  analysis/
```

Runner、runtime、package 按真实来源身份引用，目录名不替代哈希。网关实例可被多场实验引用，独立于某个 Harness 的 home；环境凭据继续来自项目 .secrets，服务生成的 env 留在受限服务实例目录，不复制进仓库实验定义。

首次落地仅让新写入遵循布局，并更新 WSL 根 README 的当前入口与历史位置表。不批量移动历史大文件、旧 run 或正在使用的服务。已观察到两个网关进程仍在，旧 raw run 还有 queued/running 元数据；这不是进程仍在生成的证据，也不是可以清理的依据。旧原始现场继续显式寻址，单独列出历史资产根。

复制固定 Runner 到新资源目录若成为下一次实验的必要准备，先核实已有 Git revision/工作树差异，复制或固定已有内容，不拉取上游最新版来替换实验环境。runtime/ZIP 可以直接复用旧路径；整齐的新目录不成为重复构建或复制大资源的强制前置条件。

## 实施顺序与冲突处理

1. 开工授权后重新确认当前工作树、活动 task 和外部引用。源码和文档已有大量他人改动，以实际内容建立迁移映射；不能从 HEAD 恢复文件或丢弃他人改动。不要在有活动依赖时同步删除远端旧入口。
2. 先分离通用 status 与 ARC/Harness 消费者，再迁移通用设施。更新所有受影响 import 和内部调用，维持单 run 协议。
3. 迁移 ARC、官网和分析模块，修正 __file__ 根计算、模板邻接路径、callback/module 名和 CLI 文档。官网本次只保留静态行为，不调用 API。
4. 归位 raw/Hackathon 源码，改专用打包器取材路径，保留分发布局与归档状态。团队 Harness 的执行、材料和包内 support 不变。
5. 补充新实验配方和实际运行目录用法，归档旧矩阵/探针入口；更新有冲突的当前导航。历史说明和当前操作页分开。
6. 在 WSL 用已有真实记录执行正常的查询、OTLP 导出和报告生成，输出到新的 analysis 目录；审阅原始事实与展示结果。必要构建仅验证实际制品交付，不增加包 smoke 或自检脚本。

不使用旧入口转发壳作为完成标准。若发现尚在执行且没有冻结副本的控制器/网关动态依赖某条旧源码路径，先保留该文件所在部署快照；确认持有者结束或取得协调授权后再切换部署。需要服务停止或超出目录迁移的行为修改时，在独立工作完成后说明具体阻塞。

Mac 工作树与 WSL 当前部署不完全相同：三个执行/ARC 模块的哈希相等，inspect_runs 不同；WSL 没有 competition、run_viewer、braid_telemetry_viewer、agent_support，且 playground 的哈希不同。因此实施时先列明本次源码部署集合及内容身份，再传输到 WSL 的独立源码快照，不能整仓 rsync --delete 或以远端文件缺失推断可删除本机实现。依赖的现有 Braid 二进制、开发 SVC、真实记录和输出位置用显式参数指定；验证报告写清实际使用的源码快照及二进制身份。通过后再按具体调用方切换部署入口，不覆盖已有服务现场。只读官网 journal 可把已经脱敏的归档副本传至 WSL 的新分析输入目录，不传 cookie 或 key；原始记录继续保留 Mac 原位置。

## 验收安排与停止条件

当前预演只读源码、目录和真实记录元数据，不运行准备中的实现。后续验收采用实际操作与既有原始证据，不编写或运行 Factory/基础设施测试、fixture、observer 测试、包 smoke、探针或改名后的自检。

| 验收对象 | 实施后的实际操作 | 判定依据 |
| --- | --- | --- |
| 通用执行与查询边界 | 检查依赖和真实 run 的 status 输出 | 核心只呈现保存状态/result，未知或没有评分不被改写为零分。 |
| Lite 两阶段结果 | 读取现有 WSL mixed Keep/BookStack 外层记录及官方 local-result | 通过/失败计数与原始结果相同，生成/部署/评分边界保留。 |
| 原生 Hackathon | 读取 codex-base Sheet 原始 requirements-only 记录 | score 仍为 null；.arc/hackathon 的过程入口可定位，不能被当成满分。 |
| 历史中断/排队记录 | 读取旧 raw 记录 | 如实保留保存的 phase，并区分观测与实时进程状态；不自动继续、归零或清理。 |
| OTLP 与 Braid 网站 | 对已有真实 telemetry.sqlite 导出、重建到新分析目录 | 原始批次/来源身份不变，Braid 网站继续使用 Braid 解码，不靠本地会话补齐 backend。 |
| 历史官网 journal | 对已有本地保存状态执行离线读取 | 原始 run/submission/billing_mode/测试计数不变；不发 HTTP 请求。 |
| 目录和分发 | 实际打包时检查构建输出清单、来源与包内入口 | 源码位置改变不改变分发路径；官方 adapter/noop 仍单文件自包含。 |

上述已有记录的使用属于后续实现范围内的证据查询，不授权新模型调用或重新评测。完整生成/部署运行是否仍然成立，必须在下一次单独获授权的真实实验中确认；没有该证据时明确写为未运行，不以静态预演或构建成功代替。

实施准备时的完成条件是：文件去向和调用方列全；预演阻断项纳入计划；历史数据与服务边界说明；目录实施与真实新实验分开授权。这些条件已满足，随后获用户开工授权。实际完成情况与未做的新实验见 [任务包](packet.md)。
