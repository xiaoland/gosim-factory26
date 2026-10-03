# 执行、恢复与状态投影

本页对应 controller.py、runner.py、backends.py、hosted.py、projection.py、admission.py 及 CLI 的 start/recover/status/monitor。

controller 按冻结 recipe 管理 build、attempt、预算、阶段和公开操作建议；Local/Docker runner 负责单次入口、资源限额、collector 和归档；hosted adapter 负责平台身份、pending 请求和平台回执。controller 退出不撤销已受理执行，重入同一请求不能重跑入口。

status 与 monitor 使用同一 experiment projection，读取保存的 producer 原件并展示目标、阶段、当前 attempt、输入输出、历史关系、阻塞和下一操作。入口退出、执行终态、archive、telemetry、transport 和平台 verdict 分别判断；局部成功不提升整体成功。unknown、身份冲突、pending 和原始错误必须保留，不自动 retry。

start 重新核对授权、预算、凭据、物理准入、冻结 runtime、来源 instance、OS、架构和 logical root。recover 只派生新的运行目录和明确的恢复关系，不停止来源、不把停止证明改名为新 attempt，也不把旧运行翻译成新执行。

Docker 的域 authority、容量和网络模式必须有保存的准入与物理读回；旧 dispatcher、预约或在途启动未明确交接时不能接管。新执行、来源停止、控制、导出和评分都需要各自授权，保存状态本身不授予执行许可。

## 查询一项或多项实验

`python3 -m lab status EXPERIMENT` 查询单个运行目录，默认呈现状态、阻塞、观察来源和下一动作的文本摘要。需要完整身份字段或程序消费时加 `--json`；也可传入 `factory26.exp.index` schema 1 文件。index 只声明需要投影的位置，路径相对 index 文件解析：

```json
{"kind":"factory26.exp.index","schema_version":1,
 "experiments":["experiment-a","experiment-b"]}
```

`python3 -m lab status INDEX.json --json` 返回 `factory26.exp.status-index`；其中一项缺失或不可读时保留该项路径和具体错误，其余项继续展示。index 不产生新执行身份，不授予接续许可。单项 `targets[].stages` 分别呈现 entry、execution、archive、telemetry、transport 和 verdict 的 producer、事实时间、来源路径与缺口；不要把某一阶段的 completed 提升为整体成功。

从所属 packet 或 index 取得实验目录后，先读 projection，再沿返回的 `evidence.path` 和 attempt `source` 定向读取原件。不要为寻找状态递归扫描整个运行树：工具资源、应用依赖和连续监控快照会把同名文件大量展开。

controller 的保存 `phase=running` 与当前 `physical_state` 分开解释。`unknown` 表示本次查询未确认同一 host、boot 和进程出生身份；宿主不同、身份字段缺失或本机读取受权限限制均可能造成它，不能据此认定 controller 已死或重新派发。需要进一步核实时保留具体读取错误；沙箱拒绝只读进程查询时，保留未知并继续消费已保存的运行事实，不绕过审批。

可用动作由冻结 controller 的 `available_actions` 决定，`next_actions` 是技术建议，仍须按当前授权选择。控制语法是 `python3 -m lab control EXPERIMENT ATTEMPT COMMAND --request-id REQUEST`；同一请求保留回执，效果未知先只读核对，不能把同一动作换 request ID 后重发。具体处置和 Hosted 支持边界见 [恢复门控](../../docs/deployment/recovery.md#当前-checkpointprepare-与停止门控)。

## 来源停止、托管和 Console

`import-source-stop` 有两种明确输入合同。未传 `--experiment/--attempt` 时，它核对同一出生身份的 birth/status GET，生成 `factory26.exp.legacy-source`（`legacy-hosted` backend identity），用于历史来源；传入两者时，必须同时传且核对现行 experiment、attempt、execution、request、prepared package 和 dispatch identity，输出绑定该 attempt 的 hosted source，不生成 legacy-source。两种模式都要求终态是 PASSED/FAILED/CANCELLED 且有 `finished_at`；可选 `--cancel-evidence` 只保存请求原件，受理本身不算停止。它不执行 cancel/start/resume；launch 仍用当前 private deployment 观察同一出生身份并验证 stopped。缺身份、凭据、当前物理状态或跨平台条件时阻塞。

`stop-evidence` 消费实际 attempt 的停止观察并形成新执行的来源停止证明；`observe_source` 会分别处理 legacy-docker、legacy-hosted、绑定 attempt 的 hosted source 和 runner source。不要把历史 legacy-source 记录改写成新 attempt，也不要把 `recover_completed.py --execute-prepared` 当作 lab.exp 的 CLI：它是已装配交付包的独立入口，要求当前 assembly、manifest、workspace 和 definition logical root 一致。

首次使用的 authority-handoff 必须明确 daemon、writer、registry、旧派发者、启动窗口和真实宿主 readback；空 docker ps 或默认路径不存在不能证明没有未知旧域。Docker job 显式 network=none 时，create 和 inspect 都要核对网络模式；未声明则保留默认网络。

托管 adapter 是新 run 的唯一平台采集和终态导出 owner，保存 pending、原始响应和唯一远端身份；不接入旧 collector，不伪造 legacy journal，不重复 POST。Luna 只消费保存的 lab monitor JSON。平台状态以保存的 /runs/RUN_ID GET 为准，read_at 或 token 增长不能替代新鲜度。

Console accessor 需要域内 access_resource_id；创建、启动和 checkpoint 捕获由同一权威排序。新登记不能追认旧未覆盖的活动 accessor；停止后不能重启同一出生实例，必须重新创建和登记。当前服务部署仍由其 owner 负责。
