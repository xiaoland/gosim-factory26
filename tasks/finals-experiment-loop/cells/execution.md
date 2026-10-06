# ARC 实验执行、环境装配与归档调查

本 cell 回答一个具体问题：把 ARC 本地生成和 Hosted 运行收敛为“给 variant、run target、task 就能启动”的旅程时，现有设施哪些职责应复用，哪些门控应删除，哪些事实不能删除。结论是面向决赛支持环境的设计输入，不是源码改动授权。

## 调查范围与当前调用关系

一次本地 ARC 生成的实际链路如下：

```text
run request (variant / target / task)
  -> current experiment compiler or future ARC assembler
     解析 variant、model/gateway、task、environment
  -> lab.exp.controller build
     冻结 runner/controller source、runtime、输入 artifact 和 recipe
  -> lab.arc_bench.local_job.job
     组装宿主 SDK 参数、agent/requirements/workspace、competition/task
  -> lab.exp.runner dispatch
     建立 attempt/binding，调用 lab.exp.backends.local_launch
  -> lab.arc_bench.arc_bench_adapter
     复制或解包 agent，装配 collector/resource evidence，调用 ARC host SDK
  -> ARC SDK local_submit.py/run_container
     在选定 Docker daemon 创建 ARC child
  -> ARC child runtime
     记录 child resource birth、进程/容器关系和 workspace 回收
  -> child agent / Braid
     写 workspace、result、OTLP、application receipt
  -> local_monitor / runner observer
     读取终态、资源、Braid/provider evidence
  -> runner seal/export + workspace_archive
     固化输出、结果、运行日志和恢复材料
```

Hosted 不是这条链的另一个 Docker backend，而是另一条物理执行链：

```text
lab.exp.hosted.dispatch
  -> snapshot/create/start API 写入
  -> hosted observer / collect_progress
     GET run、steps、workspace/template-bundle、provider evidence
  -> hosted_monitor
     liveness、stale、workspace.zip、runtime-evidence、评分/费用原件
  -> hosted.seal + arc traceability/results
     terminal archive、application seed、evaluation evidence
```

这个区别必须进入用户模型：`run target=local` 表示选择本地 ARC SDK + 外部 Docker 域；`run target=hosted` 表示选择 ARC 平台提交/观察域。两者可以共享 run、stage、archive 和 report 语义，不能假装共享暂停、资源和评分能力。核心调度与控制单位是 run；experiment 只用于把多个 run 分组比较，不是另一个隐藏控制器。一次确定 variant、target、task 且可独立停止的执行就是一个 run；stage 接续和独立评测可以产生来源明确的新 run，restart 不允许换 variant。

当前入口分散在 `lab.exp` 的 compile/build/start/dispatch/control/observe/seal、`lab.arc_bench.__main__` 的 runtime export、`arc_matrix`/`official_matrix` 和 Hosted monitor。`local_job.job()` 仍要求调用者先提供完整旧 target：endpoint、image、slots、admission_volume、authority_handoff；`lab.exp.hosted` 又要求 private cookie、competition/template 历史和可回读的远端 identity。这些是旧实现的现状证据，不是新产品必须继续携带的输入；新 target 只需解析执行宿主、实际 CPU/内存约束、路径、gateway、collector 和运行句柄。

## 当前职责和应保留的事实

| 现有组件 | 实际职责 | 建议处理 |
| --- | --- | --- |
| `compiler` / `controller` | 当前把定义和环境冻结成 recipe，并建立执行源码闭包 | 只提取材料装配、版本记录和错误保存；删除把 recipe/编译成功当作启动许可的职责 |
| `local_job` | 当前把 variant、requirements、ARC SDK、Docker child 参数和 task 组装为 job | 提取 ARC SDK argv 与目录映射；删除面向旧 authority/receipt/job schema 的公共入口，是否保留内部函数待判定 |
| `runner` | 当前拥有 attempt dispatch、observer、control、seal/export | 提取进程/child 生命周期和终态采集；不预设保留其 attempt/receipt/owner 模型，需与 ARC 运行负责人合并后判定 |
| `backends` / `docker_admission` / `state` | 当前管理资源 birth、slot/reservation、workspace holder、release | 删除 capacity/slot/admission/reservation/lease 调度职责；只提取能证明“创建了谁、现在是谁、如何关闭进程/容器和回收 workspace”的直接机制，不能藏进 profile |
| `arc_bench_adapter` | 把交付材料装进 ARC child namespace，当前也内嵌 collector/resource evidence 和 host SDK 调用 | 提取 variant/requirements/workspace 装配和 SDK 边界；本地改接共享 Collector/Backend，Hosted 不携带这套设施 |
| `local_monitor` / `hosted_monitor` | 当前读取进展、采集资源/工作区/平台证据并形成 liveness | 提取观测字段与平台回收；控制策略直接在执行侧运行，不通过远端 Backend 再止损，也不把 read-only monitor 变成新调度器 |
| `hosted` | 当前负责 ARC 平台 snapshot/create/start/stop、远端身份绑定和 workspace 归档 | 提取平台 API 适配、写入幂等和可得原件；Hosted stop/finalizer 语义必须独立保留 |
| `workspace_archive` / `arc_artifacts` / `results` | 当前提供输出清单、安全解包、应用/结果/评分证据 | 提取真实需要的归档和安全边界；是否保留全量 hash/receipt 链由具体风险判定 |
| `evaluate.py` / `arc_bench_adapter` evaluation mode | 当前以显式 application、requirements、tests 和 runner/image 运行独立评测，保存 `experiment-result.json` | 复用 ARC 评测调用和结果解释；删除让生成 attempt 隐式携带评分的路径 |
| `package_arc_replay.py` / `arc_replay.py` | 当前按 requirements SHA、application manifest 和来源 run 打包/投递冻结应用，不重新生成模型 | 复用为官网重放；应用 snapshot 必须显式绑定，不能读取 latest |
| `traceability.py` / Braid export | 当前从保存 workspace/native materials 提取 traceability 与 session 关联 | 只消费 Braid 自有导出或原生 store；不在 Factory 侧重建 issue/session 恢复协议 |
| Exp Console | 目标是 OTLP Collector/Backend 上的实验、资源、费用、日志和结果视图 | Console 以 OTLP 为主；Braid 自己实现 Braid 视图。Pi-only 没有 Braid 仍显示自己的运行/会话，不显示“未进入 Braid” |

至少以下事实必须进入 run archive：variant、run target、task/competition、实际采用的 gateway route（凭据只保存引用）、运行句柄、外部 Docker 或 Hosted identity、阶段时间、原始 stdout/stderr、OTLP/资源证据位置、完整可回收 workspace、application/result/score、费用和 native session 的原始记录、每个自动动作及其依据。source digest 和 receipt 链是否保留要按材料大小、恢复用途和直接风险决定；`exit 1` 只能是一个字段，不能替代真实错误。

## “移除所有 gate”的可执行解释

用户要求不能被实现成把旧 authority 系统藏到 `launch` 里继续逐层审批。建议从公共执行路径删除以下机制：

| 当前门控/负担 | 具体机制 | 替代行为 |
| --- | --- | --- |
| 手工选择 job、request、facility、deployment | `compile/build/start` 的多次人工交接及各类 receipt 路径 | environment profile 一次解析；run owner 生成内部 ID 和目录 |
| 以完整组合白名单阻止阶段 | compiler 对 purpose、输入来源和 job 组合的限制 | stage1 发布应用后直接接 stage2；只检查 stage2 所需应用是否可用 |
| 重复全量身份/来源证明 | compiler、runner、adapter、export 各自重验同一材料 | 删除无直接风险收益的重复扫描；保留由具体路径、秘密、控制目标或收费写入风险要求的检查 |
| `preflight` 作为启动许可 | runner 先要求全部能力满足再 launch | 删除统一启动 gate；由实际执行记录缺失能力和原始错误 |
| 手工 authority handoff / repair-ready | `authority_handoff`、`repair-ready`、额外 repair request 变成普通旅程的前提 | 删除操作者证明链；运行负责人持有实际控制句柄，是否需要旧 authority 由实现判定 |
| monitor 只能读、不能自动处置 | `local_monitor`/`hosted_monitor` 当前明确“read-only”，Hosted 的 cancel-on-lite-failure 已移除 | Python policy script 读取规范化 observation，按费用/turn/stale 条件向同一 owner 发 stop/restart；动作写入 action log |
| “旧运行未知就一律阻塞” | unknown platform write、旧 controller active 状态或外部资源状态 | 不重发未知写入；显示 unknown 原因，并由普通 Python 代码显式选择 stop/reconcile/等待；不能把未知伪装成成功 |
| 通过校验猜测环境是否可运行 | doctor/readiness 读取 SDK/runtime 但不能证明 child 环境 | profile 发布已解析路径和能力；执行中记录实际失败及其原始响应 |

删除旧 gate 后，只直接保留四类风险检查；它们仍然是检查，不用改名隐藏：

1. 路径写入不能越界。
2. 秘密不能进入公开 workspace/归档。
3. 停止/pause 必须绑定当前运行句柄，不能命中其它运行。
4. 收费或创建请求超时/未知时不能盲目重发；保留原请求和可查询身份。

这些检查仍可能拒绝一个具体危险动作，但不再要求操作者手工提供证明文件。`image_id`、Docker daemon、Hosted cookie/competition 和 task 是 profile/平台装配输入；缺失时记录原始 `environment_unavailable`，不制造已启动的假象。

## 一次 environment profile 覆盖 Mac、WSL、sfp7 和 Hosted

建议维护一个位于 WorkSSD 的 profile registry，每个 profile 只描述物理域和装配约定，不描述某次模型运行：

```json
{
  "id": "arc-local-sfp7",
  "target": "local",
  "control_root": "/Volumes/WorkSSD/.../runs",
  "execution_host": "sfp7",
  "sdk_source": ".../local_submit.py",
  "docker": {"endpoint": "...", "daemon_id": "...", "image_id": "sha256:...", "workspace": "..."},
  "runtime": {"python": "...", "runner": "...", "collector": "..."},
  "paths": {"run_root": "...", "cache_root": "...", "archive_root": "..."},
  "gateway": {"route_config": "...", "network_from_child": "..."},
  "otlp": {"collector_mode": "local-shared", "endpoint_from_child": "..."}
}
```

Mac 侧全部专属产物（包括控制记录、profile、run archive、evidence index 和临时文件）都必须位于 WorkSSD；实际 Linux runner、Docker workspace、gateway/cache 按 profile 的远端路径保存。证据范围要精确：`lab/control.py:122` 的 `Control.__init__` 把本地 controller 的 Unix socket runtime 写到 `Path("/tmp") / f"lab-{token}"`；这证明当前 Mac controller 若走该实现会把其临时控制目录放到系统盘，不证明所有 Linux runner 的 `/tmp` 都违反 WorkSSD 约定。远端 Linux 的临时目录是否允许由其执行合同和是否为需保留产物分别判定。

WSL 与 sfp7 都是可选的本地执行域；主域选择属于部署次序和环境证据的候选，不预先收窄为只支持一个，也不能让两个域无记录地接管同一执行。Hosted profile 单独声明 API、cookie 引用、competition/template contract、workspace download 和评分入口；它无需 Docker 装配，也不承诺 pause/resume。旧 image/slot/admission 机制不属于任何新 target；实际平台所需的应用包或镜像仍由对应 adapter 按真实契约提供。Mac/WSL/sfp7 的路径差异由 profile 的 remote executor 和 artifact transport 处理，variant 只看到稳定的 `agent/requirements/workspace/.factory26` 布局。profile 不承载旧 authority handoff、slot reservation 或 receipt 审批链。

一次启动应等价于：

```text
launch <variant> <target> <task> [--route-config ROUTES] [--competition]
  -> resolve profile + variant delivery + task requirements
  -> allocate one run controller and archive root
  -> materialize gateway/collector/harness paths
  -> call local ARC SDK or Hosted adapter
  -> persist resolved run inputs before first model request
```

缺少环境材料时，owner 可以先创建 run 并进入 `environment_unavailable`，这样失败仍可追踪；不会把“预检查通过”当成实验结果。

## stages 与自动控制

当前需求主要是 stage1 生成应用后接 stage2；评分是独立动作，不把评分反馈注入仍在进行的生成。不需要通用 workflow/DAG 平台。以下只是现有材料的归属示意，不预设新增强制 schema：

```text
stage1 generate -> output application
stage2 generate -> input stage1.application
independent score -> input selected application
```

每个确定的 variant、target、task 组合都是一个独立 run；实验只是把多个 run 分组比较。stage2 只在 stage1 的 application 实际可用后由普通 Python 代码启动新 run。接续统一命名为 `restart`：只能使用同一 variant，创建新 run，迁移完整 `data/`，并记录 `source_run`；不换 variant、不选择多个来源路径、不提供独立 `extract`。评分独立保存，不向生成阶段注入隐藏结果；Hosted 的评分仍由 Hosted adapter 产生自己的平台 evidence。

一次阶段接续的最小映射如下：

```text
run R1 / stage1 / variant A
  outputs: application-A, workspace-A, optional native-state-A
restart R1 -> run R2 / stage2 / variant A
  inputs: application-A
  migrated: data/ (only the standardized run data directory)
  relation: source_run=R1, source_application=application-A
  outputs: application-A2, workspace-A2, native-state-A2
```

运行数据不再通过多个 path 或独立 `extract` 组装。每个 run 固定为 `program/`、`inputs/`、`data/{workspace/,harness/}`、`records/`、`snapshots/`、`evaluations/` 和根 `manifest.json`。`program/` 是只读 variant 安装包；`inputs/` 保存 task/route/application 输入；`data/` 是 restart 必须迁移的完整工作区与 Harness/native 数据；`records/` 保存 status、日志、telemetry、cost 和平台控制记录；`snapshots/` 保存显式选择的快照；`evaluations/` 保存应用评测与官网重放材料。restart 只迁移完整 `data/`，不从任意路径猜测或执行 extract。

Braid issues 不是可任意复制的“恢复上下文”。Braid 自有 SQLite/native session、worktree 和会话关系仍是原生事实；可携带的数据只能来自 Braid 自己的 traceability/export snapshot 或归档的只读 native store。只保存 issue JSON 不足以恢复会话，不能把它交给 Pi-only variant 假装完成 Braid 恢复。Pi-only 没有 Braid 时提取自己的运行、会话和应用材料即可；缺少 Braid 不构成异常。

评测必须是独立的自动步骤，并强耦合 ARC 交付和结果保存。当前仓库已有三条可提取路径：

| 评测入口 | 实际调用 | 成功结果 | 失败/边界 |
| --- | --- | --- | --- |
| 自实现模拟测试 | 以冻结 application 作为输入，在本地评测 runner 中运行自实现测试；对应 `lab.arc_bench.evaluate`/`arc_bench_adapter` 的 `purpose=evaluate` | 保存 `evaluation-status`、passed/failed/total、score 和测试日志 | 测试进程失败、计数不完整或应用身份改变时只保存失败/unknown；这是应用评测，不是 Factory/Braid 设施测试 |
| 官网重放 | `package_arc_replay` 依据 requirements、application manifest 和 source application 生成 replay ZIP；`arc_replay.py` 只投递冻结应用，不重新生成模型 | Hosted run 的平台终态、score、workspace、traceability 和费用原件 | 上传/创建/终态/下载任一阶段失败都保留原始 HTTP/API 响应；重放是新 run、新费用，不能冒充原生成结果 |
| 试题自带评测 | ARC Runner 以题目提供的 tests/requirements 执行 application evaluation；adapter 读取 `experiment-result.json` 与 runner events | `evaluation_status=completed` 且 passed+failed=total 时才有完整 score | `requirements-only` 的 score 必须是 null；缺浏览器、测试目录、部署或 finalizer 时分别保存具体错误，不降级成业务 0 分 |

三条入口都引用同一个 application snapshot 身份，评测过程不修改生成 application。生成尚未终态或 application 快照不完整时，评测不会读取“latest”目录；报告区分 generation、evaluation、official replay 三种来源。隐藏评分只进入 score archive，不进入仍在运行的生成或接续 prompt。

现有 ARC SDK 的 stage 边界也有明确限制：`arc_bench_adapter.py:653-718` 能在一次 adapter invocation 内先运行 generation、发布 `.lab-artifacts/application`，再用 noop agent 对同一 application 做 evaluation；`arc_matrix.py:122-125` 则明确新 generation job 只消费 requirements，独立 application evaluation 才能消费冻结 application，`arc_matrix.py:173-187` 的跨 job 关系目前只生成 evaluation job。因而“同一 native 执行内的 generation→evaluation”已有实现证据；stage1→stage2 建成来源新 run，restart 按同 task/需求版本恢复原生入口，task 变化创建新 native state。题目自带一键 pipeline 若由 ARC SDK 提供，可以作为单 run adapter 能力；不能从现有 evaluation job 白名单推导通用多 stage。

自动控制脚本不是第二个调度器。owner 持续写规范化 observation：

```json
{
  "phase": "running",
  "stage": "generate",
  "native_sessions": [{"session_id": "...", "turns": "observed", "source": "native session record", "as_of": "..."}],
  "cost": {"value": "observed-or-unknown", "currency": "USD", "source": "gateway/provider/platform", "as_of": "..."},
  "last_progress_at": 1790000000,
  "resource": {"phase": "open", "identity": "..."},
  "platform": {"status": "...", "run_id": "..."}
}
```

策略是普通 Python callable/script，在执行侧读取带来源和时点的 gateway/provider/platform cost、每个 native session 的 turn 记录、执行状态和资源事实，直接调用 `start`、`wait`、`stop`、`pause`、`snapshot`、`restart` 或 `evaluate`，并记录已发出的请求与实际结果；不返回 action 交给另一层解释。它不经远端 Backend 做二次止损，不管理独立自动化程序生命周期或未来代码，也不提供任意脚本自动断点恢复。默认阶段脚本只在当前 run `completed` 后进入下一 stage；显式 `stop → snapshot → restart` 仍按原语执行。`stop` 只作用于指定 run，不递归取消来源 run、restart run 或独立评测 run，也不等于停止自动化程序；费用范围和是否联动必须由策略显式声明。未知 POST 只查询结果，不重发。Hosted 的 stop 可能只停止生成请求而绕过平台 finalizer；外部回收记录必须标明取得时点和覆盖范围。`pause` 仅在 local variant/runtime 声明支持时可用；Hosted 当前 pause/resume=false。

`status` 是无参数的 Docker-ps 式 brief：查询已保存 run 索引，只列“未归档且非正常结束”的 run，字段为 `run_id variant target task lifecycle activity last_activity age reason`。supervisor 将 facts 经 stdin 交给 program 内固定副本的 variant-bound 状态脚本；i14 脚本消费最近 native provider turn（超过 10 分钟显示 stale），pi-minimal 脚本消费最新 session message，stdout 返回 activity/brief/last_activity_at/依据，supervisor 原子写 `records/status.json`。没有状态生产者时显示 `unknown` 及具体错误，不伪造 running/finished；正常 `completed`/archived 不出 brief。CLI 不扫描远端 root 或自行创建采集循环。

## 归档、恢复和失败边界

归档目标是“以后能解释、比较、导出和在支持的边界恢复”，不是承诺所有运行都可原地续跑。一次 run archive 最小包含：

历史 `attempt`、`receipt`、container birth 等字段继续作为旧运行的事实入口，便于解释和回收；新产品不把它们提升为 run 之上的调度层，也不要求新 run 继承旧 attempt/receipt。新的 stage、restart 和评测都创建自己的 run 记录，并用 `source_run`、`source_application` 或显式 native-state 关系连接；variant 只由新 run 自己明确选择，restart 不允许更换。

```text
manifest.json                 冻结输入、profile、route、阶段来源和版本
program/                      variant 安装包及版本（只读）
inputs/                       task、route、application 输入
data/workspace/               完整工作区或 Hosted workspace 原件
data/harness/                 native session 与 Harness 状态
records/                      status、日志、telemetry、cost、平台控制记录
snapshots/                    显式选择的快照
evaluations/                  application/result/score 与评测日志
archive-index.json            成员、覆盖范围、缺失项和恢复能力
```

Local 先确保完整 workspace 已写入 `data/workspace`，再关闭采集、关闭 child/helper 进程并回收临时运行资源；`data/workspace` 本身不因 archive 而搬迁或删除。

Local 在 child 终态后由 run controller 先确保完整 workspace 已持久可得，再关闭采集、关闭 child/helper 进程并回收 workspace，最后 seal/export；关闭或回收失败保存具体的原始错误和受影响路径，不造统一释放状态。已有处置证据显示 ca315 的两条旧占用均为 terminal/pending=null，262e 经 writer-close+release applied 后 e3107 才获 reserve 并进入 sending；19:12 读回仍有旧 I14 占一个旧 execution slot。这是旧 capacity 机制造成的历史成本链，支持移除旧调度接缝，但不单独证明全栈必须重写。Hosted stop 可能绕过平台 finalizer；远端终态和 workspace 回收必须记录取得时点与覆盖范围，不能保证是最新完整。下载失败时归档仍可为 `terminal-observed`，但标记 `workspace_missing`，不能把 0 分解释成应用失败。

恢复分三种明确能力：

| 恢复类型 | 当前真实能力 | 语义 |
| --- | --- | --- |
| 观察恢复 | Local/Hosted 都可 | 新 observer 读取 archive/平台 identity，不重复创建或收费；这是默认恢复 |
| 控制恢复 | Local 按实际句柄支持 stop/pause；Hosted 当前 API 仅暴露 stop，且可能绕过 finalizer | 只操作指定 run；pause 不伪造为 Hosted 能力 |
| 应用重放 | 以已保存 application/data 重新开始新的原生会话；Local/Hosted 的材料和平台能力分别决定可行性 | 新 run、新费用和新 platform identity；绝不把新 run 伪装成原 run |
| 原生执行接续 | 同 task 使用同 variant 的既有入口：Pi 使用迁移后的 session 文件；Braid `local --offline-resume` 保留原 run identity；Lab 总是新 run_id。task/需求版本变化则在 `data/harness/<new Lab run_id>/` 创建新 native state，完整 data/app 仍迁移 | 同 task 复制完整数据但不改写 DB 来假装新会话；task 变化不把旧 native root 当本阶段目标。原生恢复后若已完成而立即结束是正常终态，不自动 reopen。 |

当前 `workspace_archive.extract_output` 的路径、链接和成员检查值得提取为安全边界。当前 `hosted_monitor` 的 `workspace.zip`、`collection.json`、`liveness.json`、`required_reads` 可作为统一 archive index 的输入，不强制沿用其状态 schema。恢复失败必须保留具体错误（缺少浏览器、远端身份不唯一、route 漂移、workspace 缺失、资源未释放），不能退回工作区/容器并声称已恢复。

## 可直接采用的实施映射

以下是实现计划，不把信息收集、模型运行或设施测试列为前置条件：

| 目标 | 现有入口 | 具体变更 |
| --- | --- | --- |
| run 生命周期 | 新 `lab/__main__.py` CLI、`lab/run.py` supervisor，复用 `scripts/execution_bootstrap.py:launch_delivery/launch_source` 与 `lab/exp/runner.py:dispatch/control/observe` | CLI 提供 `start/stop/pause/resume/restart/status/wait/logs/evaluate/archive/serve`，`snapshot` 为内部 API，evaluate 同时供 CLI 与普通 Python 程序调用；新的 run owner 只保存句柄、终态和目录，不继承旧 attempt/slot/admission/receipt 调度。适配 `pi-minimal`、`pi-minimal-vv` 与现活跃 I14 家族：`pi-braid-i14`、`pi-braid-i14-cleaner`、`pi-braid-i14-cleaner-direct`、`pi-braid-i14-e2e`、`pi-braid-i14-reviewer`、`pi-braid-i14-reviewer-cleaner-e2e`、`pi-braid-i14-reviewer-direct`；材料独立，共用入口合同。 |
| 规范目录 | `scripts/execution_bootstrap.py:delivery_assembly/prepared_delivery_assembly`、`lab/arc_bench/local_job.py:job`、`lab/exp/hosted.py` | 新增确定的 `lab/arc_bench/run_layout.py`：写入 `program/inputs/data/{workspace,harness}/records/snapshots/evaluations` 和根 manifest；Local 与 Hosted 都写 manifest，Hosted 只登记实际可下载的部分。 |
| restart | 新 `lab/run.py:restart`，各 variant 的 `main.py/run.py` 原生入口，复用 `scripts/package_agent.py:assemble/produce` 与 `lab/exp/hosted.py` | 源 run active/paused 时先 stop、确认 writer 停止、保存全部 `data/`，再以当前 program version 装配新 Lab run 并 start。同 task/需求版本调用 Pi 原 `--session <data/harness/.../session.jsonl>`，Braid 调用既有 `local --offline-resume`，保留原 Braid run identity；Lab 使用新 run_id，`data/harness/<首次创建该 native 执行的 Lab run_id>/` 保留 native_state_path。task/需求版本变化时完整 data/app 仍迁移，但在新 Lab run_id 子目录创建新 Pi session 或 Braid root/request；旧 native DB 只作历史。默认继承来源保存的 task 版本，不重读同名最新需求；旧 native 读取失败保存原错，禁止 fresh fallback。 |
| pause/stop | `lab/exp/runner.py`、`lab/exp/hosted.py` | 保留 local 的 SIGSTOP/SIGCONT 能力并公开为 `pause`；Hosted 明确返回 unsupported pause，只实现真实 stop。关闭 child/container 和 workspace 回收是具体动作，不再有 reservation/lease/release 状态机。 |
| status | 现有 `lab/arc_bench/local_monitor.py:collect/collect_attempt`、`lab/arc_bench/hosted_monitor.py:collector_session`；各 variant 与评测器的 `status.py` | supervisor 将 JSON facts（lifecycle、native/spend/resources 来源及时点、`data/workspace`、`data/harness` 路径）stdin 传给 program 内固定副本的 `status.py`；脚本 stdout 只输出 `activity/brief/last_activity_at/依据`，stderr 保存原错，不写 lifecycle、不启动控制、不访问 live checkout。supervisor 原子写 `records/status.json` 并输出 OTLP；CLI 只读该 facts。无参数列未归档且 `lifecycle != completed`，`--all`/RUN 显式查看。 |
| 归档 | `lab/arc_bench/workspace_archive.py`、`arc_artifacts.py`、`results.py` | run owner 先确保 `data/workspace` 持久可得，再写固定目录与 manifest；archive 只是隐藏标记列表，不自动搬迁、删除或另存。private credentials 留在受限存储。Hosted 缺失下载只标记 `workspace_missing`。 |
| ARC 评测 | `lab/arc_bench/evaluate.py`、`package_arc_replay.py`、`arc_replay.py`、`arc_matrix.py` | 三个入口统一消费同一 application snapshot：模拟测试、官网重放、题目自带 tests；每次评测独立 run，生成 run 绑定 variant 脚本，评测 run 绑定评测器脚本。普通 Python 程序是唯一跨 run 启动自动评测/下一 stage 的 owner；包内脚本只控制当前 run，隐藏反馈只进入 evaluation archive。 |

### 目录合同

```text
<profile.run_root>/runs/<run_id>/
  program/       # variant 安装与版本，运行期间只读
  inputs/        # task、route、application 输入
  data/          # workspace/、harness/，restart 迁移整体 data
  records/       # status、stdout/stderr、telemetry、cost、平台控制记录
  snapshots/     # 显式选择的快照
  evaluations/   # 本地测试、官网重放、题目测试及结果
  manifest.json  # variant、target、task、版本、句柄、来源关系
```

Mac 控制记录和归档根目录固定在 WorkSSD；WSL/sfp7 的 run root 由 profile 指定，Hosted 只保存平台实际可回读材料。源代码修复后的 restart 使用新的 `program.version`，保留 `source_run` 和旧版本，绝不覆盖旧 run。默认继承原 task/route/target，但调用者可显式覆盖这些字段；variant、迁移来源和 `extract` 不可覆盖。

### 状态与 restart 的最小合同

```json
{"lifecycle":"starting|running|paused|completed|failed|stopped|unknown",
 "activity":"variant script brief; evidence_as_of=..."}
```

正常评测 0 分仍是 `completed`；variant 状态脚本失败则写 `unknown` 和原始错误。`status` 不另开远端轮询，而读取状态脚本由现有观察循环定期保存的 facts。restart 对 active/paused 源严格执行“stop → 确认 writer 已停止 → 保存全部本次 data → 新 program 装配并迁移 data → start”；任何保存失败都不回退到空目录或旧 snapshot，只有调用者明确指定旧 snapshot 才可使用。`archive`/`--undo` 只改变归档隐藏标记。

状态入口合同固定为 program 内 `status.py`：supervisor 以 stdin JSON 传入 lifecycle、native/spend/resources facts 及 `data/workspace`、`data/harness` 路径；脚本 stdout 输出 activity、brief、last_activity_at 和依据，stderr 保存原错，既不写 lifecycle 也不控制 run，supervisor 原子写 `records/status.json` 并输出 OTLP。restart 入口合同固定为 `lab/run.py:restart(source_run, overrides)`，仅允许 task/route/target 覆盖；variant、source data 和评测来源不可覆盖。

### 已定实施项与平台能力限制

- 共享 Collector/Backend 固定部署在 sfp7；WSL 与 sfp7 都是执行 target。WSL profile 使用 sfp7 的共享 endpoint，不把 WSL loopback Console 当共享 Backend。
- Hosted 使用低内存自包含采集；平台能力限制（pause 不支持、stop 可能绕过 finalizer、导出可能缺 workspace/最终费用）单独记录，不作为本地部署待决。
- 费用来源分别保存 gateway/provider/platform 的原始记录；native session turn 是独立的策略指标，不作为费用权威源。
- “参与比赛”先作为 target/competition metadata 进入运行上下文；不预设额外提交 gate，具体平台语义由 Hosted adapter 的实际契约决定。
- Console 以 OTLP Collector/Backend 为实验主视图；Braid 视图和接入由 Braid 自己负责，Factory 只保留运行上下文关联，不再把 Braid source binding 作为普通 run 的前提。
- ARC template 当前已能表达 application/template、generation/evaluation 等已知路径；新产品只实现这些固定入口，不再引入任意多路径提取配置。
- `pi-minimal` 及 `pi-minimal-vv` 的 restart entry 在各自 `main.py` 使用迁移后的 session 文件并调用既有 `--session` 入口；现 I14 的源码用 run.name 设置 Braid run identity，新接线须在同 task restart 时从 retained request 沿用原身份，并通过 `local --offline-resume` 恢复，不能改成新 Lab run_id。task/需求版本变化时由同一入口在新 Lab run_id 子目录创建新 Pi session 或 Braid root/request，旧 native 数据保留历史。
- Hosted stop 绕过 finalizer 时，平台最终费用和完整 workspace 的取得时点仍受 API 限制；report 必须保留这一能力缺口。

## 证据入口

- `lab/arc_bench/local_job.py`：ARC job 仍要求完整 target、authority handoff、limits，并生成 adapter argv。
- `lab/arc_bench/arc_bench_adapter.py`：child namespace、collector、resource evidence、标准入口和结果路径。
- `lab/arc_bench/docker_admission.py`、`lab/exp/state.py`、`lab/exp/backends.py`：当前 capacity/authority/释放实现；新产品删除其调度职责，只提取可证明创建者、控制目标、进程/容器关闭和 workspace 回收的部分。
- `lab/exp/runner.py`、`lab/exp/controller.py`：attempt owner、dispatch、control、seal/export 和冻结执行器。
- `lab/exp/hosted.py`、`lab/arc_bench/hosted_monitor.py`：Hosted 写入幂等、平台身份、workspace/终态采集和 liveness。
- `lab/arc_bench/workspace_archive.py`、`lab/arc_bench/arc_artifacts.py`、`lab/arc_bench/results.py`：输出安全、制品身份和评分证据。
- `lab/control.py`：当前 controller 临时 runtime 使用 `/tmp`，需要纳入 WorkSSD profile 设计。
- 定向运行证据：`tasks/pi-minimal/sequential-stage2-stage3-20261006/packet.md`，以及其中记录的 `ca315` capacity snapshot、`262e` 的 `workspace/user-stopped-capacity-release.json`、`e3107` 的 `workspace/all-runs-status-snapshot.json`；它们支持终态到释放再到下一次启动的因果链，但不能单独推出全栈重写。

## 只读环境拓扑与部署建议（2026-10-06）

本次只读 SSH 使用 `BatchMode`、短连接超时、禁用 ControlMaster，未写入远端文件、服务或运行控制。Mac 证据仍只写本 cell；远端实际执行数据不从 Mac 空间推断。

| 域 | 读回事实 | 对 target 的含义 |
| --- | --- | --- |
| WSL `wsl.win-ws.localhost` | `yyh-ws`，Linux WSL2；Docker `0c1d4a2e-b921-49be-a075-1e30571f0995`，12 CPU、约 15.6 GiB、Docker root `/var/lib/docker`；根盘 124.9G/25.1G 可用；已有 loopback `127.0.0.1:8765` Console 进程和多批历史/当前容器 | 适合保留为现有 Console 兼容域和可选 ARC target；不适合作为共享 Backend 的默认耐久存储，除非先清理/迁移已批准材料并设磁盘预算。当前实际运行目录是 `/home/yyh/factory26-*` 一类根目录，文档中的 `/home/yyh/Development/...` 在本次读回不存在，不能写死。 |
| sfp7 `sfp7-ws.localhost` | `surface-yyh`，Fedora 43；Docker `e316f857-fe3d-4e7b-8236-9376f063fedc`，8 CPU、约 15.2 GiB、Docker root `/var/lib/docker`；根/home 236.9G/110.8G 可用；未读到 Console/OTLP listener；当前 stage2 明确使用 `/home/yyh/factory26-manual-sequential-20261006/stage2/{control,output,requirements}` bind mounts | 推荐作为共享 Collector/Backend 的首选宿主和一个本地执行 target：持久空间余量明显更大，运行路径已是可配置的远端持久目录。部署前必须单独核对服务端口从 WSL/执行容器可达；本次只证明 SSH `22`（WSL→sfp7）和 `122`（sfp7→WSL）双向可达，不证明任意 HTTP/OTLP 端口可达。 |

部署固定为 sfp7 承担共享 Collector/Backend 的耐久存储和服务，WSL 作为 `arc-local-wsl` 执行 profile；现有 WSL Console 的 `8765` 只作兼容入口，不能当跨宿主共享 Backend。WSL 与 sfp7 都保留为执行 target；sfp7 endpoint 不可达时是该 target 的运行失败，不触发另一套隐式部署拓扑。

建议冻结两个 target profile 的边界：

```text
arc-local-wsl:
  executor: wsl.win-ws.localhost
  docker_daemon: 0c1d4a2e-b921-49be-a075-1e30571f0995
  run_root: /home/yyh/<run-owned-root>
  collector: shared profile endpoint (not 127.0.0.1:8765)

arc-local-sfp7:
  executor: sfp7-ws.localhost
  docker_daemon: e316f857-fe3d-4e7b-8236-9376f063fedc
  run_root: /home/yyh/<run-owned-root>
  collector: local shared Collector/Backend on sfp7
```

profile 只保存宿主、Docker endpoint/daemon、run root、gateway/OTLP 地址和可用能力；不携带旧 authority handoff、reservation 或 Console SSH 控制 socket。Mac 控制/归档仍落 WorkSSD，远端 run/workspace/Backend 数据留在对应宿主；性能上限、Hosted 最终导出完整性和平台回收时点属于能力限制，不能被 profile 或 status 推断为成功。
