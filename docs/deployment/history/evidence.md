# 历史证据查询与采集协议

本页只解释旧 operation collector、旧 Factory watcher、历史 GC 计划和模型事实投影。使用记录中实际冻结的程序，不能用这些命令启动当前工作树的旧 writer。当前查询和消费者选择见 [证据手册](../evidence.md)。

## 等待、反馈与交接

以下是前序冻结 collector 和 Factory watcher 的生产/消费合同；不作为新 experiment 的采集入口，也不覆盖当前监控消费者约定。长实验由当时的程序持有运行命令、采集证据并保存终态。官网与本地共享 provider 活动判断，保存来源身份、生命周期、恢复边界与 native 元数据；疑似 stale 仅表示长时间没有可观测活动，不判断语义进度。
旧 journal 的 `hosted_monitor` 每轮仍从平台下载完整 `workspace.zip`，采样频率不变；平台没有增量证据接口，此改动只减少本地永久占用。普通成功轮次在临时 `scratch/` 中读取 Braid status、recovery attempt、SQLite DB/WAL 与完整 native 文件，再永久保存判定实际使用的原始 status/recovery、`provider-rows.json` 的选取 provider/turn 行值，以及每个 native 的 `header.jsonl`、`tail.raw` 和 `source.json`。窗口保存原始末 1 MiB，首尾半行、原文件字节数、offset 和 ZIP member 来源均明确记录；窗口不是完整 native，也不提供恢复承诺。provider 活动、原文件 bytes 和 fingerprint 仍来自完整 scratch，不能通过窗口文件大小重新推导。SQLite 摘录只保存本轮所选原始行，不是完整数据库，不能据此独立重跑全表选最新的查询。`required_reads` 只引用本轮永久证据。

已有 `assess/transition` 的终态、进入新故障或故障实质变化会保留本轮完整 ZIP；相同持续故障通过 `prior_full_evidence` 引用先前全现场。原生文件本来缺失时保存 expected source、原错误和 ZIP index 中不存在的依据，仍按原规则表示观察缺口；相同持续缺口不强制重复全 ZIP。解析、其它读取或写入失败保留本轮原下载和具体错误，下载未通过 ZIP 读取时明确标为未核实，不能冒充完整现场。成功轮次先将判定证据、索引、collection、liveness、outcome 及 `retention.json` 回执同步到存储，再清理本轮 scratch；普通轮最后释放本轮 ZIP。回执的 `release_state=authorized` 表示已耐久保存的释放许可，实际是否已经释放以该文件是否仍存在为准；中断时不从许可推断删除完成。此流程不扫描或回收历史轮次，也不升级已运行的冻结 collector。

本地启动 `python3 -m lab.arc_bench.local_monitor --matrix /absolute/active-matrix.json --output /absolute/collector-output`，首轮立即采样，随后沿 3+8 分钟间隔。矩阵明确实际 lab run 路径，输出保留 scheduler、每批 provider-observation/liveness、原始有界材料、通知和终态；阈值可通过 stale-after-seconds 与 minimum-samples 调整。生成容器停止而 lab 仍回传时记 stopped_finalizing，不反复 exec 或把回传阶段当未知采集失败；source 终态及 transport-finalization 原错误分别保留。监控只读，不替代已有成功门控评分跟随。
每次实验结束先向用户汇报，由用户决定下一轮，不自动重跑。

旧 Factory `run` 的后台观察器每 180 秒读取已有事件并保存 `feedback.json`，相同类别错误不重复输出，执行退出时立即刷新终态。
错误类别与重试是观测事实，可能已经恢复；不输出不能指导判断的工具完成计数。
整体状态以 `outcome.json` 为准，错误片段只用于定向取证。
没有完整结果的旧 run 明确标记 `scope=generation`，不能据此声称 bench 已完成。

主会话不定时读取原始流，也不通过每三分钟唤醒一次模型来模拟事件通知。
ARC 本地生成的恢复启动需要同时接续观察器。外层 `running` 只表示执行进程仍在，不能证明 Braid 负责人可执行。

```sh
python3 -m lab.analysis.factory watch --run /path/to/lab-run > watch.jsonl
```

该入口复用 `factory show` 的实时状态解释，只读当前对象/会话状态和有界日志，不复制整个工作区。
首次立即采样，启动后前十分钟每三分钟，此后每八分钟；当前 OPEN 负责人受阻会保留原错，无活动且根受阻或全部负责人受阻时退出2，外层终态退出0。
部署方保存 watcher PID、JSONL及退出值，由既有执行编排接收终态；没有启动该进程不能称为已接线。
停止观察不停止生成，局部负责人受阻而仍有活动时继续观察，不把设施故障换算为评分。

lab.run 应等待执行进程完成并读取持久结果；下面的只读等待命令只适用于旧 Factory 状态格式：

```sh
python3 -m lab.analysis.run_feedback watch runs/<run-id>
python3 -m lab.analysis.run_feedback watch runs/<run-id> --after-event <已处理的event_id>
```

独立 `watch` 没有被观测进程的句柄，因此以至少 180 秒的间隔检查文件；发现终态后立即返回。
已处理的终态身份保持静默，这用于去重，不保证跨进程消息恰好投递一次。
停止等待不等于停止远端实验。

## 存储回收候选

当前 Lab CLI 不暴露 gc-plan，也没有 GC apply。历史冻结 CLI 的 `python3 -m lab gc-plan --root <记录域> --asset-root <稳定资产父目录> --protect <活动现场>` 只读已有记录并输出计划；须使用保存该接口的原冻结程序，不在当前工作树执行。先选择其支持的消费记录域和明确保护路径；该命令不扫描运行进程来补造所有权，不应仅因旧目录或 `completed` 判定可删。

首版只将有效 v1 `archive.json` 精确声明的 `work` 列为候选，核对 archive ID、持久对象身份、原文保存状态及恢复/保护引用。I12/I13 活跃或未确认状态受保护；缺件、摘要变化、旧回执缺少原文保存确认、扫描错误和恢复承诺都会阻塞。报告区分 `candidate`、`blocked` 和 `already_absent`，所有条目的 `reclaim_authorized` 都是 false。稳定资产的 `unreferenced_in_scope` 仅表示扫描范围内未见消费者，不构成删除权限。当前没有 GC apply；历史迁移、I12 现场处置和 WSL/VHDX 停机须另行授权。

该历史扫描未接入 Console registry（如旧 I12 的 `console-runs.json`）；当前 Console 的 manifest 引用也不能由旧格式扫描推导。它们可能引用 run 内 host binary、shared submission、state/native 原路径及长期访问容器的 mounts；停止 server 不解除这些依赖。扫描 `complete` 只覆盖支持的记录格式，查询前须按实际配置、原 owner 回执和容器事实保护这些路径。Console 生命周期整理归独立设施任务，本入口不迁移其原文读取或 I12 现场。

## 实验模型、连接与配置漂移

以下 operation models 是历史冻结执行器的只读合同；工作树 operation 入口已经退役，只能从 `lab history` 读取保存原件或使用明确的旧冻结程序，不能作为当前 CLI 执行。

```sh
python3 -B -m lab.arc_bench operation models /absolute/operation
python3 -B -m lab.arc_bench operation models /absolute/active-matrix.json --live
python3 -B -m lab.arc_bench operation models /absolute/lab-run --live --json
```

默认只读已保存的 `monitor/<batch>/<run>/model-facts.json` 或已回收工作区，`operation status` 同时包含 `model_facts`。`--live` 复用 local_monitor 的容器身份校验，做一次 Docker inspect/exec 只读查询，不创建采集循环、启动模型或读取原生 rollout 正文。它仅读取模型配置、连接回执、timing 的公开字段及活动进程连接变量；整个 env、模型 apiKey 和提示词都不越过采集边界。URL 不输出 userinfo、query、fragment 或非标准路径。

`desired` 取明确的 selection 回执；`frozen` 沿 manifest/run 的实际 input 绑定读取 ZIP 与 model_env，并显示实际/期望 SHA256。env 未绑定为 input 时不把当前私有文件冒充冻结输入。`actual` 的 `runtime_selected` 来自 Braid 当前 request、Pi template 与已物化 native home；`process_environment` 来自与本次 timing 路径匹配的活动进程。恢复回执与实现哈希独立列入来源，当前仓库 HEAD 不作为运行版本。`observed_usage` 只投影 timing 已记录的 provider/model/session，未使用的配置仍只是可选材料；服务端底层模型不能由客户端记录独立证明。e2e 配置以静态 model/baseURL 投影，未运行时不会制造调用事实。

provider 别名 `factory26` 不证明供应商；公开 endpoint 为 ARC 时只证明客户端连接 ARC。认证变量存在只证明认证输入已配置，不证明账单是自费或比赛额度。Competition journal 的明确 credential_mode 与独立评分 replay_policy 分开显示；没有生成费用回执时保持 unknown。`drift` 比较已有的模型、endpoint 和冻结输入字节，发现差异列出具体来源；缺材料则 unknown，`no_observed_drift` 仅表示已覆盖字段未见差异。

新冻结采集器在原采样周期保存上述投影，不增加轮询。已经启动的冻结 collector-source 不自动升级，旧运行可用 `--live` 查询；没有模型事实归档的终态运行只能报告现存材料及缺口。当前实现与实际读回边界见[模型事实任务](../../../tasks/experiment-model-facts/packet.md)。

## 旧 experiment monitor 与 schema3 observer

以下描述原冻结协议，查询不迁移或接管运行。

旧 experiment 由冻结 controller/runner/Hosted adapter 采集并保存终态；监控消费者读取已保存的 `python3 -m lab.exp monitor EXPERIMENT`，不另起采集循环。程序等待使用 `python3 -m lab.exp wait EXPERIMENT ATTEMPT --json --timeout 60`，工具调用的续等留在程序编排中；停止等待不停止执行。恢复门控见[冻结执行合同](../../../lab/exp/execution.md#查询保存事实)。

旧 schema 3 Hosted attempt 在显式 start 已受理同一 run 后，附着一个只读 single-attempt observer。它仅按既定三分钟/八分钟 cadence 保存身份 GET、provider 连续观察及有限终态证据，不提交 snapshot、不创建 run、不 start/retry 或挑选评价对象。`observer.json` 保存所属 attempt/incarnation 与进程出生身份，`observer-launch-error.json` 和 `observer-error.json` 保留辅助失败；这些错误不改变远端执行结果。终态证据最多作三次有界收尾，无法完成时明确保存 incomplete。

控制的身份 readback 不经过 progress/workspace 下载锁。标准 provider 采集保留 main 原有 status、SQLite 所用行及 native 原始窗口；ZIP 只在平台支持的完整下载接口取得，不声称减少网络。`seal` 接续同 attempt 的内容/证据发布，`export` 只向指定 consumer/store 输运明确的 reference/member。部分 member 位置与 full 位置可同时存在，前者不能用于 whole verify 或被解释为完整 workspace。执行额度在实际终态和 writer-close 后释放，封口与输运仍可失败并保存原件，资产 hold 和状态 volume 不随 slot 释放而删除。

长实验由程序持有运行命令、采集证据并保存终态；运行监控不再唤醒模型。官网与本地共享 provider 活动判断，保存来源身份、生命周期、恢复边界与 native 元数据；疑似 stale 仅表示长时间没有可观测活动，不判断语义进度。
旧 journal 的 `hosted_monitor` 每轮仍从平台下载完整 `workspace.zip`，采样频率不变；平台没有增量证据接口，此改动只减少本地永久占用。普通成功轮次在临时 `scratch/` 中读取 Braid status、recovery attempt、SQLite DB/WAL 与完整 native 文件，再永久保存判定实际使用的原始 status/recovery、`provider-rows.json` 的选取 provider/turn 行值，以及每个 native 的 `header.jsonl`、`tail.raw` 和 `source.json`。窗口保存原始末 1 MiB，首尾半行、原文件字节数、offset 和 ZIP member 来源均明确记录；窗口不是完整 native，也不提供恢复承诺。provider 活动、原文件 bytes 和 fingerprint 仍来自完整 scratch，不能通过窗口文件大小重新推导。SQLite 摘录只保存本轮所选原始行，不是完整数据库，不能据此独立重跑全表选最新的查询。`required_reads` 只引用本轮永久证据。
