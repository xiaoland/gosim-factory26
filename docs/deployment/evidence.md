# 运行证据查询与分析

本文帮助接续者从已有记录定位状态、原始错误和过程事实。它不启动模型或重建实验。外部命令及控制 CLI 契约归 [Lab](../../lab/README.md)，Braid 三信号与会话重建归[诊断手册](braid-diagnostics.md)，语义分析步骤归 [运行分析 SOP](../../agents/run-analysis.md)。

## 按记录生产者查询

先确认拿到的是外层实验目录、Harness 内层目录还是平台 journal；它们的状态描述不同过程。
`lab.analysis.factory show`、`lab.analysis.run_feedback brief` 接受 Factory 生成目录或 lab 外层目录；平台 journal 继续由官网工具解释。

| 记录类型 | 从哪里开始 | 下一层证据与限制 |
| --- | --- | --- |
| 新实验/attempt | `python3 -m lab status <experiment目录> --json` | saved execution、archive、telemetry、平台观察及原错；completed 不推断评分。 |
| 旧实验外层 run | `python3 -m lab history <run目录>` | 旧 producer 原件，只读且不补新执行保证。 |
| ARC/Factory 分析 | `python3 -m lab.analysis.factory show --run <run目录>` | 分别解释生成、部署、评分及已归档过程证据。 |
| Factory 团队生成 | `python3 -m lab.analysis.factory show --run <输出/.factory26/id>` | braid.log、delivery.json、braid-state、native/manifest.json；使用显式路径，不依赖根 runs 的自动发现。 |
| raw 生成 | 官方 workspace 的 `template/.arc/raw/` | 原生事件、stderr、身份与入口结果；外部评分在外层 Runner 结果中。 |
| 历史 Factory run | `python3 -m lab.analysis.run_feedback brief <旧run目录>` 或 factory show | 旧 status/outcome 格式与归档评测仍可读取，原始记录不迁移、不改写。 |
| Competition / Playground | 对应 journal、已保存 status 和平台原始结果 | 记录观察时间、远端 ID、完整评分与采集缺口；历史文件不证明远端当前状态。 |

Factory show 可以按原归档支持的评测和用例继续定位：

```sh
python3 -m lab.analysis.factory show --run /path/to/factory-run --case REQ-2.2
python3 -m lab.analysis.factory show --run /path/to/factory-run --eval <evaluation-id> --json
```

`list/show` 只读已有运行。
生成失败时，show 从哈希核实的 Pi 归档提取末条 assistant 的终止原因与记录位置；不展示完整正文，不回溯已恢复或已替代会话的旧错误，损坏或关联不唯一时明确未知。
默认 show 先呈现状态、失败和相关入口；指定 --case 时优先展示该用例。
全部元数据、路径、会话和 SVC evidence 映射保留在 --json，避免默认输出铺满文件列表。
生成状态、所选评测和 SVC coverage 分别展示；最新本地评测失败时不回退到旧分数。
用例入口展开有长度标记的错误、从官方 error-context 定向提取的页面片段及行号，以及重定位后的本地截图、视频和 trace。
页面事实不自动等于因果结论。
历史数据缺少阶段或退出码时显示未知；旧 variant 根据配置推导并显式标记。

浏览多个归档时，可以生成本机静态诊断页：

```sh
python3 -m lab.analysis.run_viewer
open runs/viewer/index.html
```

页面发现 runs 下嵌套的 Factory/lab 外层记录，以及 Competition hosted 控制器和 Playground 的归档。
进入实验目录后不扫描其 inputs、工具资源和应用依赖；外层详情直接链接嵌套 .factory26、raw 会话、生成应用与评分报告。
例如 `python3 -m lab.analysis.run_viewer --root ../factory26-official-local --output ../factory26-official-local/experiments/<id>/analysis/viewer` 可将相邻实验的页面放在本次分析目录。默认输出仍为输入根的 `runs/viewer`。
矩阵、批次、派生 `analysis/run.json` 不算独立 run。
列表可搜索 run ID、组合和状态；详情分开展示生成/平台状态、完整评分、逐用例错误、执行过程和可打开的归档证据。
Competition 的 `FAILED` 可以带有效低分，运行中、生成失败和评测中断则显示评分未知。

Factory 过程按物理会话展示 Agent 的可见说明、工具调用与返回状态，标出 Issue/PR、turn、原生文件及行号；只有 manifest 哈希核实后才将工作项归属标为可信。
旧 run 没有 manifest 时可查看未核实的原生过程，缺少会话或格式不可读时显示证据缺口。
多个工作项可能并发，页面顺序不代表单一因果链。
Competition 和 Playground 展示已归档的 `runner_events`，按事件 ID 去重并把心跳单独计数；平台未归档 Agent 内部工具调用时，不能从阶段事件推断其操作。
两类平台事件时间保留原值，不能据页面推断跨来源的精确时差。

网页是生成时的快照，不轮询平台；run 更新后重跑上述命令。
页面只展示有界摘要，不内嵌原始提示词、推理和完整工具输出；摘要与原始日志仍可能包含敏感内容，分享前应检查。
生成文件位于被 Git 忽略的 `runs/viewer/`，源归档保持不变。

各生产者的阶段字段以其实际记录为准。
团队入口记录 prepared、braid 及结束阶段，旧生成和评测入口还有 setup、cleanup、install、build、health、tests 等记录，不能用一套阶段列表套用所有 run。
失败保留 `failed_phase`，中断明确标记。
Braid 生成失败时另存 `recovery-workspace.json` 并保留原始工作目录及 Git common repo，以免销毁恢复依据。I13 收尾写 `archive.json`，只有 `reclaim_state.status=eligible` 才删除 `work/`；真实归档复制/读取失败、声明原文未保存或仍有恢复承诺都会阻塞回收。原文完整而关联或 observer 覆盖不全时仍保留诊断缺口，不用其一概改写应用结果。冻结 I12 不随此改动升级。
应用终态先持久化；原生会话缺少规范 header 时另存 `unparsed_native` 原始文件，标记归档错误，不伪造会话身份或覆盖应用结果。
阶段更新时间表示最后一次阶段变化，不代表进程仍存活；服务不健康时可由阶段日志定位。

使用 `start_local_telemetry` 的新冻结团队包，其本地 OTLP collector 同时每两秒将容器可见的 cgroup/proc 事实保存到生成 run 的 `process-evidence/`。`resources-baseline.jsonl` 保留 namespace、mount/cgroup 原件和启动基线；`resources.jsonl` 与 `resources.previous.jsonl` 保存资源限制和后续计数、PID/starttime/PGID/RSS，不可读字段保存具体 errno。`operations.jsonl` 保存共享支持模块自身的信号请求、API 返回和 wait；Braid 的 `braid.log` 保存 Pi 原有的 wait、shutdown 及 Child owner 释放事实。这些文件进入原有归档对象，辅助采集失败不改变生成结果。历史冻结包与工作区没有这些材料时，不能补推历史资源事实。

新版 collector 优先记录存活进程，避免大量 zombie 用尽详细进程名额。它另外汇总全部可见进程各 scope 的存活/死亡数和 RSS，并在原有循环内每十秒读取最大十二个存活内存使用者的 `smaps_rollup`、I/O 和文件描述符类别计数，保留读取后 birth identity 核对。`status` 同时记录 RssAnon、RssFile、RssShmem、VmSwap。RSS 汇总可能重复计算共享页，不能当作 cgroup charge；PSS 和匿名/文件/共享内存细分用于进一步归因。读取失败或 PID 已消失保持具体错误，不推断内存为零；不读取 argv、环境变量或文件内容，也没有新增权限要求和内核追踪能力。

资源数据由两个各 31 MiB 的段轮转，基线另有 2 MiB 上限，持续保留末端样本。轮转记录明确保存上一段及被丢弃旧段的字节数；`resource-status.json` 保存最后采样状态、当前/上一段开始时点及轮转次数。基线和低频操作 JSONL 分别限制为 2 MiB、8 MiB，达到上限写同名 `.capped.json` marker。单个样本最多记录 256 个进程，优先 collector 父进程的后代树并按层级保留上层进程，其次为 run 内 cwd、当前 cgroup、其它可见进程；各范围计数和遗漏数均保留。这些采样范围不等同工作项归属。首先核对基线、cgroup inode/路径、可见 namespace、读取错误、遗漏数及轮转覆盖，再解释计数变化。`memory.events` 与 `.local` 的范围不同；`oom_kill` 增量证明对应范围内发生 OOM 杀进程，不能单独证明哪一个 Pi 是 victim，`memory.max=max` 也不证明被 namespace 隐藏的祖先没有限制。

成功信号 API 返回只记录请求结果，死亡原因另看 wait。Pi Child owner 释放记录不证明 Tokio 实际发送信号。容器内没有平台宿主信号审计，不能确定外部 sender；collector 若同遭 SIGKILL，最后样本也不是终止原因。官网能下载的仍是平台保留的 workspace/template，宿主 kernel、Docker 和祖先 cgroup 的因果证据需要平台提供。当前实施与实际覆盖见 [进程终止证据 packet](../../tasks/experiment-signal-diagnostics/packet.md)。

历史远程评测以 `remote-evaluations/<evaluation-id>.json` 保存每次请求的完整观测，`remote-evaluation.json` 仅作为最近观测的兼容入口。
请求在启动前分配明确 ID，区分连接、传输、远端运行和下载，每 180 秒获取该 ID 的 summary；SSH 进程退出立即返回，不额外等一个观察周期。
下载后核对 run、benchmark 和冻结应用哈希，不按目录差集猜测执行。
观测时间与观测失败单独保存，下载后用终态 summary 收口；断线不能被当成远程零分或停止成功。
`show` 同时保留最新本地评测与远端状态，不把暂存远端状态当作已下载成绩。

## 等待、反馈与交接

长实验由程序持有运行命令、采集证据并保存终态；运行监控不再唤醒模型。官网与本地共享 provider 活动判断，保存来源身份、生命周期、恢复边界与 native 元数据；疑似 stale 仅表示长时间没有可观测活动，不判断语义进度。
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

## 证据与分析

证据按上表的生产者保存。
旧 Factory `runs/<run-id>/` 与新团队输出 `.factory26/<id>` 均可包含配置、提示、哈希、原生 session 和生成日志；外部评测的 JSON、HTML、截图、视频与 trace 位于对应评测目录，不保证与生成记录同层。
新入口的材料哈希也不等于旧入口保存的完整源码快照。
`native/manifest.json` 将每个物理 session 与 provider、逻辑 group、工作项、turn、归档输入及内容哈希对应；被替换会话的用量仍计入。
缺失证据保留身份及错误，不能用最新文件代替。
退出时清理 Agent 与应用进程组；报告中的相对产物链接依赖本机保留的 run，不会随源码自动分发。

`python3 -m lab.analysis.factory analyze --run <Factory生成目录>` 为每个原生会话分别导出 `analysis/<序号>-<来源指纹>/evidence-v4.zip`，保存 overview、模型 usage 和 provenance。
来源指纹包含原生内容、实际 provider 和 exporter；缓存使用前核对原生清单与产物哈希。
相同来源复用已完成分析；来源变化重新导出，全部查询成功后才发布目录，失败不覆盖已有分析。
历史目录保持原样。
用量是否汇总及覆盖哪些会话应以该生产者的实际记录为准，缺项不能当作零；不要从入口名称推断统计完整。
进一步检查可使用 `query`、`read`；请求格式通过命令帮助与 `--schema` 查询：

```sh
.venv/bin/svc analysis query --help
.venv/bin/svc analysis read --help
.venv/bin/svc status --json
.venv/bin/svc lookup --path specs/
```

svc 负责证据导航，不自动判定应用质量。
标准 Pi session 缺少执行终态，可能使 overview 显示 `partial`；应结合覆盖声明、运行器退出码与最终模型停止原因判断，不能把 `partial` 一概解释成内容丢失。
实际费用未知时保持 null，不用客户端估算替代比赛账单。

## 用开发 SVC 定向取证

`factory analyze` 默认调用开发 `.venv/bin/svc`，分析没有 SVC 注入的原始 core run 也有效。已有 `--svc-source <path>` 可使用具备 PDM 环境的完整源码作独立诊断，记录实际 HEAD 与 CLI 源码哈希，不替换参赛 Corpus 或改写旧分析；安装与交接见 [CONTRIBUTING](../../CONTRIBUTING.md)。

生成期间的工具错误先用稳定短语 match，再用返回的 ref trace：

```sh
printf '%s\n' '{"version":3,"intent":"match","predicates":{"kinds":["tool_result"],"text_terms":["稳定错误短语"]}}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
printf '%s\n' '{"version":3,"intent":"trace","event":<match返回的ref对象>}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
```

trace 返回关联调用的标准化上下文；只有需要精确原文或原生审计时才用 read。外部评测发生于生成之后，错误未必存在于生成 transcript；先判断用例暴露的应用缺口，再定向回看当时实现和自验，不能把用例编号强行关联到工具调用。

历史冻结执行器的只读跨链查询使用 `lab trace <生成run> --work-item issue:6` 或 `--session <native_id>`。它依据保存的身份字段列出来源，不按时间邻近推断因果；缺失和多义结果保留。原文分页和参数以 [Lab](../../lab/README.md)为准。

## 存储回收候选

当前 Lab CLI 不暴露 gc-plan，也没有 GC apply。历史冻结 CLI 的 `python3 -m lab gc-plan --root <记录域> --asset-root <稳定资产父目录> --protect <活动现场>` 只读已有记录并输出计划；须使用保存该接口的原冻结程序，不在当前工作树执行。先选择其支持的消费记录域和明确保护路径；该命令不扫描运行进程来补造所有权，不应仅因旧目录或 `completed` 判定可删。

首版只将有效 v1 `archive.json` 精确声明的 `work` 列为候选，核对 archive ID、持久对象身份、原文保存状态及恢复/保护引用。I12/I13 活跃或未确认状态受保护；缺件、摘要变化、旧回执缺少原文保存确认、扫描错误和恢复承诺都会阻塞。报告区分 `candidate`、`blocked` 和 `already_absent`，所有条目的 `reclaim_authorized` 都是 false。稳定资产的 `unreferenced_in_scope` 仅表示扫描范围内未见消费者，不构成删除权限。当前没有 GC apply；历史迁移、I12 现场处置和 WSL/VHDX 停机须另行授权。

该历史扫描未接入 Console registry（如旧 I12 的 `console-runs.json`）；当前 Console 的 manifest 引用也不能由旧格式扫描推导。它们可能引用 run 内 host binary、shared submission、state/native 原路径及长期访问容器的 mounts；停止 server 不解除这些依赖。扫描 `complete` 只覆盖支持的记录格式，查询前须按实际配置、原 owner 回执和容器事实保护这些路径。Console 生命周期整理归独立设施任务，本入口不迁移其原文读取或 I12 现场。

## 实验模型、连接与配置漂移

新实验模型事实使用 `python3 -m lab status EXPERIMENT --json`，分别保留 desired/bindings、runtime_selected 与 observed 的未知范围。以下 operation models 是历史冻结执行器的只读合同；工作树 operation 入口已经退役，只能从 `lab history` 读取保存原件或使用明确的旧冻结程序，不能作为当前 CLI 执行。

```sh
python3 -B -m lab.arc_bench operation models /absolute/operation
python3 -B -m lab.arc_bench operation models /absolute/active-matrix.json --live
python3 -B -m lab.arc_bench operation models /absolute/lab-run --live --json
```

默认只读已保存的 `monitor/<batch>/<run>/model-facts.json` 或已回收工作区，`operation status` 同时包含 `model_facts`。`--live` 复用 local_monitor 的容器身份校验，做一次 Docker inspect/exec 只读查询，不创建采集循环、启动模型或读取原生 rollout 正文。它仅读取模型配置、连接回执、timing 的公开字段及活动进程连接变量；整个 env、模型 apiKey 和提示词都不越过采集边界。URL 不输出 userinfo、query、fragment 或非标准路径。

`desired` 取明确的 selection 回执；`frozen` 沿 manifest/run 的实际 input 绑定读取 ZIP 与 model_env，并显示实际/期望 SHA256。env 未绑定为 input 时不把当前私有文件冒充冻结输入。`actual` 的 `runtime_selected` 来自 Braid 当前 request、Pi template 与已物化 native home；`process_environment` 来自与本次 timing 路径匹配的活动进程。恢复回执与实现哈希独立列入来源，当前仓库 HEAD 不作为运行版本。`observed_usage` 只投影 timing 已记录的 provider/model/session，未使用的配置仍只是可选材料；服务端底层模型不能由客户端记录独立证明。e2e 配置以静态 model/baseURL 投影，未运行时不会制造调用事实。

provider 别名 `factory26` 不证明供应商；公开 endpoint 为 ARC 时只证明客户端连接 ARC。认证变量存在只证明认证输入已配置，不证明账单是自费或比赛额度。Competition journal 的明确 credential_mode 与独立评分 replay_policy 分开显示；没有生成费用回执时保持 unknown。`drift` 比较已有的模型、endpoint 和冻结输入字节，发现差异列出具体来源；缺材料则 unknown，`no_observed_drift` 仅表示已覆盖字段未见差异。

新冻结采集器在原采样周期保存上述投影，不增加轮询。已经启动的冻结 collector-source 不自动升级，旧运行可用 `--live` 查询；没有模型事实归档的终态运行只能报告现存材料及缺口。当前实现与实际读回边界见[模型事实任务](../../tasks/experiment-model-facts/packet.md)。
