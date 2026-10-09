# 运行证据查询与分析

查询先按记录生产者选择入口：当前 run 使用 Lab 保存的 status，旧 experiment 使用原冻结执行器，旧 Factory 使用保存的 `.factory26`/legacy reader，Hosted 使用 journal 原件；Braid OTLP 使用 [Braid 诊断](braid-diagnostics.md)。本页后半保留旧格式的只读查询，不把历史命令当作新运行入口。

本文帮助接续者从已有记录定位状态、原始错误和过程事实。它不启动模型或重建实验。外部命令及控制 CLI 契约归 [Lab](../../lab/README.md)，Braid 三信号与会话重建归[诊断手册](braid-diagnostics.md)。

定向查询冻结检查点中的 SQLite 时，在任务目录复制数据库及其已登记的 WAL/SHM 后打开副本；`mode=ro` 连接原件仍可能创建辅助文件，改变冻结 inventory。原件意外出现读者派生文件时，先核对原登记成员字节与模式，再由输入负责人隔离保全，不改 manifest 或删除原登记 WAL。

## 按记录生产者查询

先确认拿到的是外层实验目录、Harness 内层目录还是平台 journal；它们的状态描述不同过程。
`lab.analysis.factory show`、`lab.analysis.run_feedback brief` 接受 Factory 生成目录或 lab 外层目录；平台 journal 继续由官网工具解释。

| 记录类型 | 从哪里开始 | 下一层证据与限制 |
| --- | --- | --- |
| 当前 ARC run | `python3 -m lab status RUN --json` | 本 run 的 manifest、records/status.json、日志、资源、费用和平台原件；使用实际 run ID/目录，completed 不推断评分。 |
| 旧 experiment/attempt | 对应冻结执行器的 status/history；工作区兼容读入口为 `python3 -m lab.exp history <run目录>` | 旧 producer 原件，只读且不补新执行保证，不把目录传给当前 run CLI。 |
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

新 Lab 公共包由容器内 `ResourceSupervisor` 的既有循环调用同一 `ResourceEvidence`，Local 和 Hosted 都采执行容器的 namespace；宿主或外部 OTLP receiver 只负责传输，不能代替容器资源采样。Hosted 内部 receiver 使用 `--no-resource-sampling` 避免重复写入。独立 `lab_otlp.py --serve-run` 保留自己的采样默认。资源采样启动或读取失败保存具体错误，不阻止生成。旧冻结运行不自动采用这项接线修复。

新版 collector 优先记录存活进程，避免大量 zombie 用尽详细进程名额。它另外汇总全部可见进程各 scope 的存活/死亡数和 RSS，并在原有循环内每十秒读取最大十二个存活内存使用者的 `smaps_rollup`、I/O 和文件描述符类别计数，保留读取后 birth identity 核对。`status` 同时记录 RssAnon、RssFile、RssShmem、VmSwap。RSS 汇总可能重复计算共享页，不能当作 cgroup charge；PSS 和匿名/文件/共享内存细分用于进一步归因。读取失败或 PID 已消失保持具体错误，不推断内存为零；不读取 argv、环境变量或文件内容，也没有新增权限要求和内核追踪能力。

资源数据由两个各 31 MiB 的段轮转，基线另有 2 MiB 上限，持续保留末端样本。轮转记录明确保存上一段及被丢弃旧段的字节数；`resource-status.json` 保存最后采样状态、当前/上一段开始时点及轮转次数。基线和低频操作 JSONL 分别限制为 2 MiB、8 MiB，达到上限写同名 `.capped.json` marker。单个样本最多记录 256 个进程，优先 collector 父进程的后代树并按层级保留上层进程，其次为 run 内 cwd、当前 cgroup、其它可见进程；各范围计数和遗漏数均保留。这些采样范围不等同工作项归属。首先核对基线、cgroup inode/路径、可见 namespace、读取错误、遗漏数及轮转覆盖，再解释计数变化。`memory.events` 与 `.local` 的范围不同；`oom_kill` 增量证明对应范围内发生 OOM 杀进程，不能单独证明哪一个 Pi 是 victim，`memory.max=max` 也不证明被 namespace 隐藏的祖先没有限制。

成功信号 API 返回只记录请求结果，死亡原因另看 wait。Pi Child owner 释放记录不证明 Tokio 实际发送信号。容器内没有平台宿主信号审计，不能确定外部 sender；collector 若同遭 SIGKILL，最后样本也不是终止原因。官网能下载的仍是平台保留的 workspace/template，宿主 kernel、Docker 和祖先 cgroup 的因果证据需要平台提供。当前实施与实际覆盖见 [进程终止证据 packet](../../tasks/experiment-signal-diagnostics/packet.md)。

历史远程评测以 `remote-evaluations/<evaluation-id>.json` 保存每次请求的完整观测，`remote-evaluation.json` 仅作为最近观测的兼容入口。
请求在启动前分配明确 ID，区分连接、传输、远端运行和下载，每 180 秒获取该 ID 的 summary；SSH 进程退出立即返回，不额外等一个观察周期。
下载后核对 run、benchmark 和冻结应用哈希，不按目录差集猜测执行。
观测时间与观测失败单独保存，下载后用终态 summary 收口；断线不能被当成远程零分或停止成功。
`show` 同时保留最新本地评测与远端状态，不把暂存远端状态当作已下载成绩。

## 等待、反馈与交接

当前 run 由自身执行与观察程序保存状态和终态；查询消费保存事实，不另起采集循环。程序等待使用 `python3 -m lab wait RUN --json`，流式日志使用 `python3 -m lab logs RUN --follow`。当前 CLI 不提供 monitor 或 wait --timeout；停止等待不停止执行。

采集身份、观察截止点和缺项跟随实际 producer。旧 experiment monitor、schema3 observer 与 operation ZIP 采集协议见[历史采集说明](history/evidence.md#旧-experiment-monitor-与-schema3-observer)，仅解释对应冻结运行。

查询先核对实际 producer、观察时间和来源身份，不能用 token 增长、活动进程或 stale 标记推断语义进展。每次实验结束先汇报，由用户决定下一轮。旧 collector 的取证窗口、完整 ZIP 保存条件、Factory watch 和 run_feedback wait 见 [历史采集协议](history/evidence.md#等待反馈与交接)，它们不升级已在运行的冻结执行器。

## 证据与分析

证据按上表的生产者保存。
旧 Factory `runs/<run-id>/` 与新团队输出 `.factory26/<id>` 均可包含配置、提示、哈希、原生 session 和生成日志；外部评测的 JSON、HTML、截图、视频与 trace 位于对应评测目录，不保证与生成记录同层。
新入口的材料哈希也不等于旧入口保存的完整源码快照。
`native/manifest.json` 将每个物理 session 与 provider、逻辑 group、工作项、turn、归档输入及内容哈希对应；被替换会话的用量仍计入。
缺失证据保留身份及错误，不能用最新文件代替。
退出时清理 Agent 与应用进程组；报告中的相对产物链接依赖本机保留的 run，不会随源码自动分发。

历史分析中的 `application/`、解压副本或网站目录可能在归档后清理。引用不存在时，先沿所属 run 的 archive/artifact manifest、冻结 ZIP 和来源身份找仍保留的原件，区分派生副本缺失与原件丢失。确需恢复应用时，只从已核实来源提取到新的 WorkSSD 目录，保留来源与成员路径；它只是只读分析副本，不取得完整 checkpoint 或继续生成的身份。维护证据索引时链接保留的原件和提取方法，不把临时副本继续列为当前入口。

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

当前 Lab CLI 不暴露 gc-plan 或 GC apply。制品保留与完整性边界见 [Lab 制品说明](../../lab/exp/artifacts.md)；历史冻结 CLI 的只读候选规则和未接入 Console 的限制见 [历史回收协议](history/evidence.md#存储回收候选)。completed、目录名或扫描范围内未见消费者均不构成删除许可；本页不授权历史清理。

## 实验模型、连接与配置漂移

当前模型事实由 `python3 -m lab status EXPERIMENT --json` 展示 desired/bindings、runtime_selected 和 observed 及其缺口。声明配置、已安装配置、实际调用和收费是不同来源；provider alias 或 endpoint 不证明底层模型与费用模式。输入和凭据关系见 [定义合同](../../lab/exp/experiments.md)，旧 operation models 的字段与单次 live 查询见 [历史模型事实协议](history/evidence.md#实验模型连接与配置漂移)。
