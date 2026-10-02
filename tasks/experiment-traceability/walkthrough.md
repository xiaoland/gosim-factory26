# 实验入口与复评流程走查

2026-09-25，依据既有 WSL 记录和当前源码进行只读走查。没有启动模型、应用、评测或基础设施测试。交互建议归 [设计](design.md)，本文件保存发现依据，不代表建议已实现。

## 从结果进入 Agent 过程

在 WSL 使用已有 `/tmp/factory26-identity-check` 源码快照中的 `show_run` 与 `render_show`，读取原始记录。快照是前次身份修正验收留下的副本；这里没有覆盖正在使用的源码。以下路径均相对于 `/home/yyh/Development/factory26-official-local/`。

| 查询对象 | 实际返回 | 使用者仍要完成的工作 |
| --- | --- | --- |
| `experiments/hackathon-local-eval-20260925/full/runs/codex-base-artifact-replay-hackathon-local-sheet-req-1-2-1-1327f9d013` | 1667 个字符。显示 failed、生成 unknown、部署 incomplete、评分 failed；包含外层错误、缺少 Playwright 报告及应用/证据路径。 | 判断此次其实在回放已有应用，找到应用来源，定位原生成的过程与更早的具体错误。 |
| `runs/hackathon-generation-20260924/codex-base-hackathon-sheet-67ac86e938` | 3472 个字符。显示生成和部署 completed、评分 skipped，并列出 8 条原生会话路径及应用/原始证据路径。 | 选择能够解释这些会话的工具，确认所读过程与前次被测应用的关系。路径条数不代表 Agent 数量。 |

首个记录的 `workspace/official/template/.arc/replay.json` 已声明来源为第二个记录，variant 为 codex-base，应用摘要为 `61a4c56c23c2215a04ae3d41e09289d85a003d48634e2d7aa0ce09d8f3b3dc71`。这些信息没有连接到当前默认摘要。此前已核对回放 ZIP 的应用文件清单；本次没有把声明文件当作新的消费哈希核验。

因此，“此评测没有启动 Agent”和“产生此应用的 Agent 过程可在原生成执行找到”应同时表达。不能将复评的无 OTLP 显示为原生成过程缺失，也不能将原生成事件混入本次复评时间线。基础设施负责连接证据，用户选择的分析器负责解释内容。

## 失败并不总是同一种后续工作

上述场景 `sheet-req-1-2-1` 有三份记录：

| 执行后缀 | 保存状态 | 本次读取能确认的事实 |
| --- | --- | --- |
| `1327f9d013` | failed | `workspace/official/execution.debug.log` 第 23 行为 `npm error Exit handler never called!`，来源为 frontend-npm-install.stderr；第 24 行为 npm 自报内部错误。Runner 结果没有 Playwright 报告。不能仅据此断言网络是根因。 |
| `bd440dbe1a` | running，无结束时间 | 历史状态未收口，本次未核对其进程归属，不当作当前仍在运行。 |
| `04c425b2fa` | completed | 已保存的代理报告记录 outcome=failed，失败步骤为 `create and enter a blank Sheet1`，Playwright status=failed。执行完成与应用通过不同。 |

代理报告来自 `/tmp/factory26-identity-check-analysis/result.json`。报告使用 3 份测试源码快照，早期记录的覆盖映射快照不全。以上可展示为同一场景的已知执行记录；不能据此自动证明它们条件完全相同，或补写缺失的 retry_of。

默认任务视图应呈现最新尝试及当前可用结果，旧错误留在历史中。打开确切旧 run 引用时仍显示原记录，并链接后续同场景记录及条件差异；对历史未显式建立的关系标明推断依据。已有后续完成记录时，重评旧失败是另一次主动实验，不能默认推荐为仍未完成的补救。

## 复评操作的现有障碍

现有 Hackathon 配方已能只选择一个场景，也确实只回放冻结应用。使用者仍需从文档拼接回放 ZIP、平台输入、Runner、镜像、输出清单与运行根，再执行清单和报告脚本。这些选择包含“新脚本还是旧快照”“沿用哪个应用”等实验含义，不能交给目录猜测。

`lab/arc_bench/package_arc_replay.py:package` 先要求整个 run 的 phase=completed，再从固定生成目录读取应用。对于已交付应用但后续评测失败的执行，这个入口会拒绝复用；这是源码确认的边界，未为验证它启动新实验。复评应依据实际可用的应用及其来源，不由外层总状态单独决定。

建议从任务或指定应用发起“对已有应用重新评测”：自动携带来源，默认使用原评测冻结条件，展示选择范围、条件差异与模型调用范围，再按已有授权执行。不增加强制预览确认。若仅存在可疑的工作目录，先说明应用身份未核实；不得默默换成当前目录里的最新文件。

## 本轮收敛

实验概览以计划任务为单位，尝试历史在任务下展开。71 个场景和 122 次执行分开计数；历史非终态不直接加入当前运行数。过程入口区分本次执行过程和输入应用的生成过程。具体错误、测试结论和可执行操作放在同一上下文中，让用户能够选择排障、分析应用或发起新的复评。

本轮确认的是路径与语义障碍，未测得端到端耗时，也未验证运行中实时过程展示。后者只能承诺展示已到达的事实及其时间；其体验需在后续另行授权的真实运行中验收。

## 全方案收敛时的补充核对

用户要求持续设计至整个方案收敛后，又核对了以下具体接口和成本。仍然只读，没有运行模型、Collector、网关或评测。

- 八次历史生成的 `inputs/agent/*.zip` 合计 4,369,711,702 bytes，只有四份不同的保存身份。每个配置在两题中使用同一份 ZIP。输入共享冻结有直接存储收益；尚未测准备耗时，不据字节数声称加速比例。
- 当前 `lab/otlp.py` 固定 16 MiB，拒绝 gzip，错误为文本，SQLite 异常返回 500；`lab/run.py` 只覆盖通用 OTEL 参数，宿主信号专用 endpoint/headers 仍可能优先。查阅 [OTLP 协议](https://opentelemetry.io/docs/specs/otlp/)和 [exporter 配置](https://opentelemetry.io/docs/specs/otel/protocol/exporter/)后，方案明确协议接入范围、可配置接收边界、可重试持久化失败及信号专用参数处理，避免把配置不兼容误判成 Agent 未上报。
- WSL `hackathon-runtime-codex/python/litellm-1.102.0.dist-info/METADATA` 确认版本。该版本 `proxy/auth/user_api_key_auth.py:1346` 的基本 custom_auth 分支直接调用用户方法并验证 UserAPIKeyAuth；`integrations/custom_logger.py` 已有 pre/failure hooks；`proxy/common_request_processing.py` 提供 call ID 和流处理。此证据支持每 run 网关凭据及请求日志关联方案，不意味着实际接线已完成。
- 固定 Runner `raw-baseline-20260923-wsl/runner/local_submit.py:554` 在启动 Docker 前 flush 输出 workspace 和容器名；docker 使用 `--rm`、`--name` 与明确 bind。适配器可及时登记并核实资源，恢复时无需依赖全机容器名称扫描。

桌面推演覆盖了不完整评测后复评、旧成功后新失败、同时存在的尝试、Collector 关闭后补采、控制器失联、共享网关请求和更新测试后读旧报告。结果已合入技术方案：确切引用不漂移、执行/评分/证据分离、分析固定截止点、未知状态不自动重跑、来源不明不伪造。该推演只收敛设计冲突，不代替将来的实际运行验收。
