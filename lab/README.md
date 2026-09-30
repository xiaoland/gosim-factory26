# 本地实验设施

`lab` 运行外部 argv、冻结输入、收集原始 OTLP，并保存运行事实。它不导入或解释任何 Agent Harness。新实验使用 JSON v3 清单，包含 `max_parallel`、`storage`、稳定宿主 `controller_runtime` 和非空 `jobs`；每个 job 提供 `command` argv、命名 `inputs`，可选 `result_path`、`artifact_paths`、标签和显式 execution/cleanup/recovery 依赖。命令中的 `{workspace}`、`{run_dir}`、`{run_id}`、`{artifacts}` 与 `{输入名}` 在尝试分配时替换。外部命令以 workspace 为工作目录运行；没有 `result_path` 时只报告进程退出，不推断业务成功。历史 v1/v2 清单继续可读，并在启动收据中明确标为 `legacy-unbudgeted`。

ARC 官网追溯材料的导出、运行证据采集与查询归 [ARC 平台运行说明](../docs/deployment/competition.md)中的 ARC 适配层；通用 Collector 不要求任何 ARC 字段。

在 WSL 的独立 Python 环境安装 [requirements.txt](requirements.txt)。`python3 -m lab plan <recipe> --experiment-root <新目录>` 只冻结输入；`python3 -m lab run <recipe> --experiment-root <新目录>` 冻结后执行。`run <已冻结实验目录>` 只安排从未分配尝试的 job；`retry <run目录>` 明确增加一次尝试。输入在一个实验内按来源共享冻结，命令和控制器源码也保存在实验内；改变配方或源码应建立新实验。

v3 `storage` 必须声明 `host_reserve_bytes`、每 run 的 `workspace_bytes_per_run`、`telemetry_bytes_per_run`、`finalization_scratch_bytes_per_run`、一次性 `build_bytes` 和 `archive_level`。当前只支持已实现的 `decision`，其它级别在冻结边界拒绝。控制器在分配 attempt 之前用目标文件系统的实际 available bytes/inodes 计算并发峰值，保存 `storage-preflights/<id>.json` 和最新 `storage-preflight.json`；不足时不创建 attempt。`parallel` 增加槽位前重新预检。预检只证明启动时有预算，不代替运行中限额或终态归档回执。

v3 的 `controller_runtime` 必须引用 `scripts/runtime.py host-lab` 生成的 `factory26.host-runtime` 回执。计划时冻结其根目录、launcher 和环境树身份；controller 启动前再次核对。ARC 矩阵把同一引用写进每个 job 的 `execution_cleanup` dependency，因此执行和资源核对不会暗中依赖创建配方时所在的 venv。回执缺失、环境被原地修改或 launcher 不可执行都会失败关闭。

运行中控制器按自身启动时间在前十分钟每三分钟、此后每八分钟异步扫描，向 `storage-observations.jsonl` 追加去重后的实际占块、telemetry 占用和文件系统余量。单 run 达到 workspace/telemetry cap 的 80%，或余量进入 finalization floor 时停止派发新 attempt；扫描不完整同样暂停派发，不把缺失数据当作 ready。单 run 达到 100% 时停止对应 controller 进程组，host reserve/inode 底线被突破时停止全部受控进程组并取消未启动 attempt；同批目标共享最早的 30 秒 TERM 宽限期，随后 KILL。run 记录 `storage_budget_exceeded` 及原始观测；外部容器和其它已登记资源仍标为 `unconfirmed`，必须用 `reconcile` 核实并按需显式 `cleanup`。控制器不删除活动 cache、workspace 或 evidence 来续跑。

运行时环境提供 `EXPERIMENT_RUN_ID`、`EXPERIMENT_RUN_DIR`、`EXPERIMENT_ARTIFACT_DIR`、`EXPERIMENT_EVENT_DIR`，以及三信号的 OTLP/HTTP protobuf endpoint、header 和协议变量。Collector 支持 traces、logs、metrics，保留原始 protobuf；采集缺失不代替外部命令的终态。生产者可自行向事件目录写 JSONL，Agent 过程语义由生产者和后续分析工具决定。用户分析放在 `<实验目录>/analysis/<新名称>/analysis.json` 时会由 `show <run>` 列出；声明引用具体 run、输入批次截止点、分析器版本及结果入口。

常用查询为 `show <实验或run>`、`status <run>`、`events <实验> [--after <游标>]`、`wait <实验> [--after <游标>]`、`evidence <run> [相对路径]` 和 `telemetry <run> [--signal logs] [--after-id N] [--limit N] [--export <新目录>]`。遥测列表默认返回最多 100 批并给出下一批 ID；显式导出默认包含全部选定批次。`stop <实验>` 与 `parallel <实验> N` 通过拥有者的控制 socket 受理；返回操作 ID 可用 `operation <实验> <ID>` 查询。`reconcile <run>` 只观察进程和配方声明的资源；`cleanup <run>` 是显式清理，检查命令来自冻结配方，不能从事后事件获得执行权限。失联不会自动重启模型调用。

`gc-plan --root <记录域> [--asset-root <稳定资产目录>] [--protect <路径>]` 只向 stdout 输出 `factory26.gc-plan`，不调用 cleanup、不移动或删除对象，也不写回既有记录。首版只把有效 `factory26.archive` v1 回执中精确声明的 `work` 目标列为候选，并重验回执、持久归档对象、原文保存状态、恢复承诺、路径边界、I12/I13 活动记录和显式保护；扫描不完整会阻塞候选。稳定资产只报告 `referenced`、`unreferenced_in_scope` 或 `unknown`，任何状态的 `reclaim_authorized` 都是 false；未找到引用不是删除授权。候选的 `allocated_bytes_observed` 按 inode 去重，但外部硬链接意味着实际可释放字节仍是 unknown。`complete` 只表示已支持记录格式的扫描完整。Console 的 `console-runs.json` 不在当前扫描格式内，其 binary/state、访问容器 mount 和原生原路径依赖必须用 `--protect` 显式保护；server 退出不表示访问容器或这些引用消失。gateway 等其它域外依赖同样须显式保护，不能仅加 `--root` 就假定未知格式已解释。

读原生会话可用 `evidence <生成run> --session <native_id> --bytes 4096`，从该 run 的 `native/manifest.json` 精确选择归档文件。结果保留原始路径、字节 `offset`、所在 `line` 和 `next_offset`/`next_line`；继续读取时传 `--offset <next_offset>`，直至 `truncated` 为 false。输出按字节限制，可能停在一行中间；行号是定位信息，不能把分页完成当作语义已读。

跨链只读导航使用 `trace`。`--work-item issue:6` 从清单列出该工作项的全部成员、原生会话、context/instructions/turn 原文入口、session-tree 父子记录、时间与工具事件；`--session <native_id>` 可反向定位工作项。`--pid`、`--commit`、`--tree` 只做已有 timing/sqlite 字段的精确检索，结果状态会明确标记 `missing`/`ambiguous`，不会用时间邻近推断因果。例：

```sh
python3 -m lab trace <生成run> --work-item issue:6
python3 -m lab trace <生成run> --session <native_id> --tool-call <tool_call_id> --bytes 4096
python3 -m lab trace <生成run> --session <native_id> --text "关键词"
```

`--text` 只返回有界 preview 与原始 `source`/`line`/`offset`，标为 `text_candidate`，不构成身份关联。`--record <record_id>` 或 `--tool-call <tool_call_id>` 才会读取原始 JSONL 记录；工具调用返回 call/result 两个定位和各自 `next_record_offset`，可在同一命令用 `--offset` 续读，或用现有 `evidence` 的绝对 `next_offset`。缺少 PID、commit、tree 或父子归档时保留缺失状态，不补造字段。

补采使用 `telemetry serve <run>` 创建新接收会话，向现有数据库追加批次。导出与查询只读旧数据库，不升级原始文件；新的分析结果应固定自己消费的 batch ID 截止点。ARC 入口、容器资源和冻结应用复评属于 [ARC 适配器](arc_bench/)，其操作说明见 [本地运行](../docs/deployment/local-experiments.md)。

## 实验标签与每次执行的名称

配方 job 可用 `labels` 保存任意字符串标签；旧顶层 `competition/variant/task/venue` 继续兼容。两处同时声明一个标签时必须同值，冻结后不允许用执行标签改写它。lab 不解释模型、ARC 或命名编号，调用者约定见 [实验导航](../experiments/README.md)。

例如 ARC 配方的一行稳定标签为：

```json
{"experiment_key": "e20260926-01", "case": "coordinator", "operation": "generate"}
```

编号仅为示例。`run_name` 不写入冻结 job，因为同一 job 可能重试；本次执行单独准备一个 JSON 文件，以冻结 manifest 中的 job ID 为键：

```json
{
  "coordinator--arc-bench-lite--keep": {
    "run_name": "e20260926-01--coordinator--keep--g01"
  }
}
```

```sh
python3 -m lab run <实验目录> --run-labels <本次标签.json>
python3 -m lab retry <来源run目录> --run-labels <新一次标签.json>
```

执行标签经整体验证后附加到本次 `run.json.labels`，消费的映射内容也进入现有 operation request；不在后台重新读取一个可能变化的标签文件。映射只能补充标签或重复相同值。重试保留原 `retry_of`，不继承上次执行的 run_name；省略映射时保持无可读名。名称与机器 run ID 一起由 `show --json` 保存展示，`show --all` 的文字视图列出有名称的各次尝试。

这些参数适用于新控制器冻结的实验。旧实验继续使用其 `controller-source`，不能用当前 CLI 参数冒充升级；旧运行的人类名称在所属任务的对应表记录。编号分配由实验登记负责，不用 attempt 推算跨 local/hosted 的 g/r 编号，不建立全局编号服务。
