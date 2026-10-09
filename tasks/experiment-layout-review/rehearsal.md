# 实施计划预演与排障

## 方法与结论范围

2026-09-25 按用户授权开展计划预演；未实施源码迁移。主 Agent 追踪查询依赖、当前文档、WSL 资产和真实记录元数据；独立 explorer 追踪冻结脚本、打包和官网调用；独立 QA 复核具体 plan.md。只读预演不运行项目模块、测试、探针、模型或 benchmark，不证明迁移后的代码已经可执行。

下列路径行号对应预演时工作树，其他任务仍有未提交改动。实施前按符号和调用重新定位。

## 已识别并纳入计划的断点

| 场景 | 静态证据或现场观察 | 计划修正 |
| --- | --- | --- |
| 将所有源码改成包内 import | arc_matrix.py:40–63 只冻结 adapter/noop 单文件；local_experiment.py:87、199 从独立 workspace 执行。 | 仓库 CLI 用 -m；冻结 adapter/noop 继续 stdlib 自包含脚本，同迁并保留 basename。 |
| 只移动 raw/Hackathon 文件 | package_raw_core.py:19、57–61，package_hackathon.py:30、38–43 读取旧 submission 路径；hackathon_main 导入 raw_main，后者导入时读 raw-config.json。 | 两个专用打包器改取材路径，包内文件名及一份 raw 共享实现不变。 |
| 将 raw/Hackathon 当普通团队 variant 打包 | package_agent.py:90 要求 build.py，第 102 行要求 Braid runtime，第 109 行为 Pi 元数据。 | 保留各自打包协议，不为目录归位顺手统一 manifest 或增加 Braid。 |
| 调整官网模块层级 | playground.py:20 的 parents[1] 原指仓库根，移动后会变成 lab；practice_record/output_dir/saved_summary 依赖同一 ROOT。 | ROOT 保持仓库根，journal/cookie/锁/计费模式不随源码迁移。 |
| 拆 status 但仍间接读取 Harness | local_experiment.py:292 → inspect_runs；后者读取 .factory26/.arc/raw 和官方事件。run_feedback.py:343、run_viewer.py:15、factory.py:99 共用其增强结构。 | 核心 status 读原始状态；增强结构由分析消费者提供，ARC 结果与 Harness 过程目录拆分。 |
| 只修通用 status 的 import | inspect_runs.py:161 只识别 .arc/raw；submission/hackathon_main.py 实际记录在 .arc/hackathon。 | 增强分析加入原生 Hackathon 入口发现；缺少记录继续明确缺口，不影响核心终态。 |
| 分析输出按旧根推导 | run_viewer.py:726–737 固定 ROOT/runs/viewer；factory.analyze 在输入目录下建 analysis，inspect_runs 的发现/会话关联依赖后者。 | 仅 Viewer 增显式输出；Factory 私有缓存及其读取契约保留，不建立外置索引。 |
| 改模块名遗漏展示和监控入口 | Makefile:21、旧监控说明（已删除）、run_viewer.py:589、braid_telemetry_viewer.py:198 与运行文档包含旧 CLI。 | 更新当前操作命令与模板示例；不替换历史已执行命令或 frozen inputs。 |
| 迁走 submission 中的模型代码 | hackathon_gateway.py:78 仍把 submission 放入 PYTHONPATH，callback 当前只依赖 scripts/responses_compat。 | 独立复核确认不是迁移断点：submission 目录仍保留，网关源码/PYTHONPATH 均不动。 |
| 把远端当作本机工作树镜像 | WSL 若干脚本缺失、若干版本不同，见下节。 | 范围化部署到独立源码快照，显式依赖路径；不整仓覆盖或删除。 |
| 认为旧 running 字段代表活动生成 | 旧 raw 记录保留 queued/running；本次进程快照匹配到两个网关，没有从字段推断控制器存活。 | 不改写旧终态或自动恢复/清理；源码部署前确认实际路径持有者。 |

源码调查没有发现 official_matrix 通过子进程硬编码旧 competition.py 路径：其控制路径是 Python import，统一调整包导入即可。回放入口中的 __file__.parent 指包根，保留；打包器中的仓库寻根可改为同目录取材。公共 Docker 上下文和 pi-team 的 support 复制无需改动。

## 两端部署差异

| 模块 | Mac | WSL |
| --- | --- | --- |
| local_experiment.py | e4c4ab09de6d… | 相同 |
| arc_matrix.py | 293e64383e66… | 相同 |
| arc_bench_adapter.py | 0966d87b0d02… | 相同 |
| inspect_runs.py | 3e6a88992e5f… | 843533631dce… |
| playground.py | 6fa8c39cc26e… | 3ca7da4e7e92… |
| competition.py | 存在 | 缺失 |
| run_viewer.py、braid_telemetry_viewer.py、agent_support.py | 存在 | 缺失 |

第一次清单读取在远端 competition.py 缺失处抛出 FileNotFoundError，没有写入。随后按存在性单独读取所需文件，确认上述差异。该错误是预演的读取假设不成立，不是实验执行失败。

WSL 已有 sources/braid/target/debug/braid 和本轮 runtime-pi-braid/bin/braid；这里只确认文件存在，没有运行或判定版本兼容。后续 Braid 网站操作应显式选择对应版本并记录身份，不能依赖新部署目录下恰好存在默认路径。

两个根目录机器矩阵 hackathon-generation-matrix.json（8 jobs）和 hackathon-pi-native-browser-matrix.json（1 job）的具名输入路径目前均存在，且仍指向旧 scripts/arc_bench_adapter.py。它们是历史执行清单，不是待自动恢复队列；即使目录搬迁令旧来源路径失效，也不改写这些记录。

## 后续实际查询可用的真实证据

以下事实来自只读 JSON 和以 SQLite mode=ro 读取的批次计数，没有加载项目代码或展开 Agent 文本。

| 样本 | 保存结果 | OTLP |
| --- | --- | --- |
| WSL repo runs/hackathon-team-baseline/20260925/lite-runs/pi-team-mixed-arc-bench-lite-keep-54196efa62 | completed，27 passed / 5 failed / 32 total | 214 批：8 traces、146 logs、60 metrics |
| 同目录 pi-team-mixed-arc-bench-lite-bookstack-ba27587982 | completed，27 passed / 7 failed / 34 total | 301 批：8 traces、184 logs、109 metrics |
| WSL assets runs/hackathon-generation-20260924/codex-base-hackathon-sheet-67ac86e938 | completed，mode=requirements-only，score=null，evaluation_status=skipped | 982 logs 批 |
| Mac runs/playground/a11ce90b4611/status.json | FAILED，self_funded，test_pass_rate=1.0，tests 长度 100 | 不适用 |
| Mac runs/playground/963db7dca6c2/status.json | FAILED，self_funded，test_pass_rate=1.0，tests 长度 0 | 不适用；不能凭总分补出逐例错误 |

两个 Lite 样本的顶层 result 没有 mode 或 score 字段，评分事实位于 evaluation/summary。因此迁移不能只按 result.mode 识别 ARC，不能把缺少顶层 score 当成未评分。Sheet 则有显式 score=null，其生成完成也不代表通过测试。

本次读取的 run.json SHA256：Keep c2b58973fc1809c0e62b22a1937ec65cc0b845e49af646b2f2c4fad43f51ca77；BookStack 875e3e3b11bf661d418d02c04d210df10f9bd77e50b7ee778787b677647a3646；Sheet 80cfacdc5ba74e624b65feb1d2c28c3bd2aca95d6c0f9e29236f868b94fc736d。这些用于描述读到的版本，不建立自动内容测试或冻结未来采集。

旧 raw 目录另有 50 个 queued、10 个 running、6 个 completed 和 27 个 failed 文件记录。这里只在有限目录深度内枚举外层 run.json，遇到 run 后不进入 inputs/workspace，未读原生 rollout。这些数值是保存状态的清单，不是当前活动任务数。

## 独立计划复核

独立 QA 按实际消费者检查计划，提出两项收窄，主 Agent 均已采纳并改写 plan 正文。

第一项是撤销网关 PYTHONPATH 清理。目录迁移不破坏现有 callback，服务还在运行，本轮不为移除一个无影响的搜索目录改变服务代码。

第二项是撤销 Factory analyze 的 --output 改造。初版计划只考虑写入位置，遗漏 inspect_runs.py:91–104、402–445 对 run/analysis 的发现和会话关联。迁到外层后结果会从 show/viewer 中消失。保持这一完整私有契约，只让独立 Viewer 支持显式输出，避免顺势增加索引协议。

QA 还指出官网 save 的实现归属必须写具体、旧矩阵链接必须修正。计划现在列明从 agent_support 迁出同等 save 实现到 playground，official_matrix 相对导入，并列出当前文档及历史链接更新范围。

独立 QA 最终建议接受修订后的计划，进入待开工；未发现剩余静态计划阻断。主 Agent 采纳这一判断，仍保留实际模块导入、部署快照、ZIP 构建、真实查询和网站生成、完整生成部署的运行证据缺口。

独立预演只能消除当前可见的计划断点；没有导入新模块、打新包、调用官网或运行完整实验。单文件冻结、ZIP 实际构建和新版 CLI 的运行证据仍按 plan 的授权及验收边界取得。
