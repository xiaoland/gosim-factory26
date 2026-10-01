# I13 官网 GitHub 生成中断：保全与诊断

2026-10-01 本次受用户“官网异常结束，请安排 sub-agent 保留工作区并排查证据”指示，仅做该 run 的只读取证及本地证据写入。没有恢复或继续官网执行，没有新 run、模型调用、源码修复、WSL 操作或远端 push。

## 结论与身份

官网 run [346bc3b51b09](https://arc-bench.com/runs/346bc3b51b09) 在生成阶段失败，未开始官方测试。直接原因已定位：PR #5 的 `pi-deepseek-fast` 原生 Pi 进程 PID **19590** 收到 **SIGKILL 9**，RPC 断开后，Braid 的原生关闭检查将全局执行置为 `blocked`、返回 1，Harness `run.py:321` 将此失败向外传播。**信号发送方和底层资源原因尚未证实**；不能把此结果归为有效零分，也不能仅凭 SIGKILL 判定 OOM。

| 字段 | 身份或结果 |
| --- | --- |
| Competition / task | `hackathon` / `hackathon--github` |
| Submission / variant | `d0692dd35545` / `pi-braid-i13` |
| Braid run | `20261001-052115-e45f4278` |
| 官方 requirements.yaml SHA256 | `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f` |
| Harness ZIP SHA256 | `afca9654b10544851885c748060d7d283b2d40b0890363f6acfb9a2dfe677877` |
| 平台终态 | `FAILED`，`deploy_agent=completed`、`start_agent=failed`、`run_tests=pending` |
| 官方评测 | `evaluation_started_at=null`；passed=0、failed=0 |
| 已保存费用字段 | run `billing_mode=self_funded`；submission `credential_mode=official_evaluation`，两者差异继续保留 |

冻结包 `run.py` 及全部 `implementation-hashes.json` 项均与现场一致。运行中的 `work/bin/braid` SHA256 为 `a78128da72e64fc604d7cd0ccde68ebc69e61d7db48af165e7b53c858e6e83dd`，与包内二进制一致。Braid 当前源码按构建器同一文件集合计算的摘要仍为冻结的 `105e42ad20018531b7e47ce739a8df4f107b457bd1e1bb9f462b817111b8a260`，因此本次对关闭与错误传播接口的阅读有版本依据；相关源码另存为只读证据，不以当前 Git HEAD 代替包内身份。身份核对见下方 `analysis/frozen-identity.json`、`frozen-runtime-identity.json`、`braid-source-identity.json`。

## 保全清单与边界

本次独立证据根目录为 [`failure-investigation/20261001T070702.797343Z/`](../../runs/iteration13/hosted-20261001/failure-investigation/20261001T070702.797343Z/)，以下“本次目录”均指此处。原监控批次和 journal 未修改。

| 材料 | 本次目录内入口 | 核实结果 |
| --- | --- | --- |
| 官方工作区原件 | `workspace.zip` | GET `/runs/346bc3b51b09/workspace/template-bundle`，15:07:02–15:07:58 CST，HTTP 200，277814542 bytes；SHA256 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd` |
| 下载身份、HTTP、时间 | `download-receipts.json`、各 `*.headers` | 保留每次 GET 的路径、时间、curl 退出码、HTTP 状态、原始响应与摘要，不含 cookie 内容 |
| ZIP 索引与完整性 | `archive-index.json`、`archive-file-hashes.json`、`zip-integrity.json` | 27768 项、958068635 未压缩字节；逐项读取 CRC 无错误，每个文件另存 SHA256 |
| 独立解包副本 | `inert-workspace/template/`、`inert-extraction.json` | 只生成不可执行的普通文件；没有执行包内程序。原 ZIP 保留归档元数据 |
| 与上批终态对照 | `previous-terminal-comparison.json` | 与 `monitor/20261001T065751.899359Z/346bc3b51b09/workspace.zip` 每个成员内容完全一致；ZIP 容器摘要不同，不表示现场变化 |
| 当前官方文件树 | `workspace-files.json`、对应回执 | GET `/workspace/files`，15:15:13–15:15:23 CST，HTTP 200，27816 个文件；比 ZIP 多列 48 个文件 |
| 单文件补充保全 | `supplemental-source/receipts.json`、`summary.json`、`inert-content/` | 按当前官网客户端实际 `/source?file_path=…&kind=file` 接口补取上述 48 项，43 项 HTTP 200。原响应与返回的 UTF-8 原文分开保留；不宣称 binary 字节身份 |
| 补取失败原件 | `supplemental-source/summary.json` 及对应 `*.response.json` | PR #2 `backend/test-results/.last-run.json` 返回 404 `{"detail":"Not found"}`；一个 vision route-index 与三个 nested route.json 返回 500 `Internal Server Error`，不伪造缺件 |
| 已成功保存的官方终态与 traceback | `prior-official/status.json`、`03436d68fef7e8d8.json`、`sources.json` | 从原 journal 原样复制并记录来源；日志含 14:50:04 的 Harness traceback |
| 本次刷新错误 | `status.json`、`status-retry.json`、`logs-offset-0.json`、`traceability.json` 及回执 | 本次 GET 返回 HTTP 500，具体原文 `Internal Server Error` 保留；没有以错误响应覆盖 journal 的既有成功记录 |
| 官网提交历史刷新 | `commit-history.json` | HTTP 200，`{"availability":"workspace_unavailable","commits":[]}`；不据此宣称内部 Git 成果为空 |
| 冻结实现副本 | `frozen-implementation/` | 从冻结 ZIP 保存 main/run/support；确认 Braid 源码摘要一致后保存关闭与错误传播相关源码 |

ZIP 实含官方需求 29 项、五个工作树 303 项、`origin.git` 136 项、六个 Braid 物理会话的 native home、Braid SQLite/WAL/SHM，以及 `native/` 归档。三个 Pi 内部子 Agent 的 `session.jsonl`、transcript、output 和 meta 也在完整 ZIP 内；补取的 `work/tmp` 侧记录进一步保全它们的终态与恢复关联。

这里的“完整工作区”指官网实际提供的 **workspace/template bundle**。当前官网客户端仅暴露此工作区 ZIP 和上传 submission 的 archive 下载；它没有暴露完整 `/workspace` 容器文件系统、宿主 cgroup/kernel 日志或任意 `/tmp` 目录归档。官网会省略各 clone 的 `.git`，ZIP 还未包含上表列出的 48 项；本次用文件树与只读 source 补取明确标出这些界限。上传 Harness 的原 ZIP 已在 `github/agent.zip` 和 `start-20261001/artifacts/pi-braid-i13-k27.zip` 原样保留，两者均为 393332574 bytes、上述冻结 SHA256，故未重复下载同一个 submission archive。接口依据及成员差异见 `analysis/official-download-scope.json`，当前官网客户端原件为 `site.js`。

## 事件时间线

下面日期均为 2026-10-01；CST 为 UTC+8。原始 Braid 日志为解包副本 `.factory26/20261001-052115-e45f4278/braid.log`，末尾定向副本为 `analysis/braid-final-lines.txt`。最后工具事实见 `analysis/final-tool-events.json`，会话与 turn 状态见 `analysis/braid-state-tables.json`。

| UTC / CST | 观察 | 对判断的意义 |
| --- | --- | --- |
| 05:20:59 / 13:20:59 | 平台启动；05:21:15 Harness 创建 Braid run | 正式执行身份已冻结 |
| 06:31:20 / 14:31:20 | 基础分支提交 `ddfbe6a` | 基础实现进入 Git common repo |
| 06:35:33 / 14:35:33 | PR #2 合入 develop，commit `6c102f0` | 该成果在终态原件中仍存在 |
| 06:36:22 / 14:36:22 | PR #5 Pi 启动 PID 19590，随后原生 session `01a0f62d-abb6-7628-8972-4e88ec4a2ae1` | 精确定位收到 SIGKILL 的执行身份 |
| 06:46 批次 / 14:46 批次 | 最新正常采集显示 PR #3/#4/#5 三个 active turn、blocked_groups=0；各原生记录末尾在 06:45–06:46 | 故障之前已有真实编辑，非启动即失败 |
| 06:48:17–30 / 14:48:17–30 | PR #3 定向应用测试返回 28 passed | 仅是生成 Agent 的应用自验反馈，不是官方评分 |
| 06:48:56 / 14:48:56 | PR #3 启动全套 vitest；30 秒后 bg001 仍 running | 后台任务并未取得终态 |
| 06:49:39 / 14:49:39 | PR #3 再次启动全套 vitest；PR #4 同秒启动 orgs vitest | 同一时段存在重复和跨 PR 的测试进程，构成资源压力线索 |
| 06:49:41–48 / 14:49:41–48 | PR #5 `pnpm install` 返回 Node `v24.10.0` 不满足 `>=20.0.0 <21` 的具体错误 | 这是已返回的工具结果；Pi 未在此工具结果里报告退出 |
| 06:49:53.728 / 14:49:53.728 | PR #5 provider turn `01a0f62d-ae0a-7dc3-a3b4-84d5b281ac58` 报 `provider disconnected` | 本次首次终止链证据 |
| 06:49:53.816 / 14:49:53.816 | 同一个 PR #5 原生会话关闭返回 `session failed: Pi exited with signal: 9 (SIGKILL)` | 直接进程退出原因已确定 |
| 06:49:53.818 / 14:49:53.818 | PR #4 turn 变为 unknown，错误 `provider session disconnected before terminal receipt` | 发生在 PR #5 故障后的全局收尾边界 |
| 06:49:54.319 / 14:49:54.319 | Braid 输出 `local run blocked: native teardown could not be proven: … SIGKILL`，exit 1 | 单个原生关闭失败进入全局失败路径 |
| 06:49:55.962 / 14:49:55.962 | Harness 保存 generation_failed 与恢复工作区声明 | 原始进度未按成功路径回收 |
| 06:50:04 / 14:50:04 | 归档回执保存；官方日志打印 `run.py:321` RuntimeError，经 :385 重新抛出 | 归档与 traceback 晚于首个失败，未产生最初 SIGKILL |
| 06:50:48.440 / 14:50:48.440 | 平台 FAILED，测试仍 pending | 这是生成中断，不是已完成的隐藏评测结果 |

## 原因、排除项与未知

直接退出链置信度高。Braid `provider/pi.rs` 的 stdout 读取在 EOF 后报告 `Disconnected`；关闭路径等待原生 child，非零状态成为 `Pi exited with …`；session manager 把关闭失败送入 fatal stop；local driver 收到后返回 `blocked`。这与原始日志、SQLite turn 终态和 Harness traceback 相符。原生 `close_native` 的超时分支为 180 秒并返回 `Pi shutdown` timeout；本次断开至 SIGKILL 关闭错误仅约 88 毫秒，**不符合该超时分支主动杀进程的行为**。`run.py` 的 `cleanup_workspace` 在 Braid 退出之后才执行，也不能解释最初的 PR #5 断开。

当前最值得判别的底层假设是宿主或容器资源压力。PR #3 留下一份仍 running 的全套 vitest，又因把 bg001 误交 `subagent_wait` 得到 “No active run matched” 后启动第二份；同时 PR #4 启动应用测试。保存的 vitest 配置没有显式 worker 限制。这些事实与 SIGKILL 时间相邻，**只提供线索，尚无 cgroup `memory.events`、OOM victim、RSS、内存上限或平台 kill 审计，不能确证 OOM，也不能据此作容量修复决定**。

| 解释 | 证据与当前判断 |
| --- | --- |
| Node engines 错误直接杀死 Pi | 已返回常规工具结果，没有证据表明版本校验发出 SIGKILL；属于实际应用工具环境问题，因果未建立 |
| Factory 模型预算保护 | 冻结保护器拒绝时打印 `Factory model budget: …` 并 exit 78；故障现场没有此错误，退出信号为 9；该路径不匹配 |
| ARC/provider HTTP 错误 | 定向原生与 Braid 日志没有在故障时间给出 429/5xx 或 provider 账余额错误；信号来源仍可能在外部，不能用无匹配日志完全排除 |
| 应用自验失败 | 历史自验有成功与失败，两者均保存；首次全局终止记录为原生 SIGKILL，没有官方应用评测执行 |
| 归档失败 | `archive.json` 在原生退出之后生成；诊断覆盖 partial 与原始 SIGKILL 分开记录，非最初终止来源 |
| Agent 显式 kill 命令 | 全部六条 Braid 原生 bash 调用仅见 06:28 与 06:34 对应用服务器的 pkill；未见 06:49 时杀 PID 19590 的命令。记录在 `analysis/explicit-process-commands.json` |
| 平台超时、管理员终止或 OOM | 缺宿主级事实，仍为未知；平台端只有外层 exit 1，不能从约 89 分钟耗时推断硬限额 |
| 存储容量或数据库损坏 | 定向日志无 `No space left`、storage budget、disk quota 错误；现场 SQLite+WAL integrity=ok、foreign_key_check 无违例。没有远端余量采样，无法宣称容量充足 |

本次刷新 status/logs/traceability 的 HTTP 500 出现在生成已终止后，只说明取证时 API 的失败行为，不反推为 14:49:53 的终止根因。

## 可恢复成果与限制

内部 Git common repo 包含五个提交。`main` 仍为初始化提交 `e9e24e029c1603aa9394e3fbad701c5cd9245527`，`develop` 为基础合并 `6c102f0928a9a58a5986f27a73cceca5ea4f415e`；三个功能 PR 的已发布 ref 尚未前进。`delivery.json` 为 failed，根 Issue #1 OPEN，PR #3/#4/#5 OPEN；没有最终应用交付到模板根目录。

| 恢复对象 | 已保留的成果 | 具体边界 |
| --- | --- | --- |
| Git 已发布历史 | 初始化、设计资料、ignore、基础实现、PR #2 merge；common repo refs/objects 完整可读取 | `main` 的 delivery_commit 仅为 seed，不是最终成品；官网 commit-history 不可用不影响这些内部原件 |
| PR #3 工作树 | 相对已发布 ref 保留 7 项文件差异，含 repos/orgs 路由、权限操作与 repos 自验 | 最后两个测试调用没有完整工具终态；不能按 native 仍 running 判断进程仍活着 |
| PR #4 工作树 | 保留 6 项差异，含 orgs、repoGrants、db 接线及 orgs 自验 | turn 已 unknown，最后测试未回传终态 |
| PR #5 工作树 | 保留 8 项差异，含 issues 路由、schema、seed 与任务笔记 | 会话被 SIGKILL，依赖安装尚未成功，不是可交付成品 |
| Braid 协作状态 | SQLite、WAL、SHM、request、sessions、turn 输入、物理上下文与对象记录 | `status.json` 仍显示 3 active turn，而终态 sessions/数据库已将 PR #4/#5 标 unknown；DB `local_run` 仍 running、PR #3 turn 仍 running。这是持久执行身份未收敛，不代表远端继续运行，接续必须经过 offline-resume 边界 |
| 原生会话 | 六条 Braid 物理 JSONL 与 `native/` 副本逐字/hash一致；三条 Pi 子 Agent 原生 JSONL及产物也保留 | `native/manifest.json` 三个子 Agent 条目没有关联到 child ID/path，归档回执因此 partial；不能把回执不足改写为工作区原文丢失，也不修改历史回执 |
| 工具与输入 | 官方需求与图片、native materials、work/skills/capabilities、原 `braid-request.json`、完整冻结 Harness runtime | 官方 ZIP 不提供所有系统 `/tmp` 内容；重建执行环境必须记录来源，不把新产物当历史原件 |
| 私有 clone Git 元数据 | 工作树文件可保留为修复接续输入，现有恢复入口可从已发布 ref 重建 Git index | 各 clone `.git` 未进入官方 ZIP/文件树，原索引、私有 HEAD/refs、未 push 历史不可恢复；不能声称已取得精确全运行检查点 |

文件差异表只是“保留文件与 common repo 已发布分支”的比较；因私有 `.git` 缺失，不区分 staging、私有已提交但未推送和未提交。详细清单为 `analysis/worktree-file-differences.json`，Git 原始 refs/log 为 `analysis/git-state.json`，数据完整性为 `analysis/database-integrity.json`，原生原文核对为 `analysis/native-integrity.json`、`child-native-inventory.json`。

较早候选是 `monitor/20261001T064642.322438Z/346bc3b51b09/workspace.zip`，SHA256 `daf975da0c042c60aa723f17b069b50777be448ba050e690a1d59ab48aaae022`。它有同一 run、相同物理会话、SQLite 完整性 ok 和故障前实际进度，但在三个 turn 活跃时取得，缺各 clone `.git`，也没有证明应用文件、SQLite 与 native 是同一原子停止点。其所有 ZIP 成员时间在 06:47:00–06:47:20，原生记录末尾在 06:45–06:46；不得把批次名当单一恢复时点。它是**故障前采集副本**，尚不是已证实的完整可恢复检查点。

对较早副本与终态文件逐项比对，三个 PR 和根 packet 共 10 个源文件/笔记有后续变化；退回该副本将放弃已保全的这些实际进度。两批原件均保留。比较见 `analysis/previous-live-checkpoint.json`、`previous-live-database.json`、`last-live-vs-terminal-files.json`。本次没有选择或执行恢复。

## 接续来源建议与设施判别证据

主线随后传入用户新增决定：WSL 已恢复，四项矩阵由主线启动，其中 Flash/GitHub 可接续；改进实验设施以捕捉反复发生的 Pi SIGKILL 来源。本调查 Agent 仍只读保全诊断，不自行恢复或实现设施。

**主线已接受建议：Flash/GitHub 从本次终态 ZIP 的副本重建接续。** 它保留最晚的实际源文件、common repo、可读的 SQLite+WAL 与同一组原生身份；原件内容与上批终态 ZIP 完全一致，说明目前下载的是稳定终态材料。现有证据显示一次突发原生 SIGKILL，没有源文件损坏、持续扩散错误或上下文污染的证据。回到上一批会具体放弃十个后来变化的文件及成功自验记录，且仍不能得到原子完整检查点。因此接续身份应明确写为“终态文件快照，经 clone Git 重建与 Braid offline-resume 接续”，不能称原版本独立完成或精确原生断点续进。

若主线必须使用错误首次发生前的材料，最近候选仅为上节 14:46 批次；它的 Git、DB、六条会话身份互相对应，SQLite 可读，但三个 active turn 与非原子打包限制保持。来源选择需要同时保留终态原件、列明上述十个文件的进度损失。无论选哪批，平台省略私有 `.git` 的约束相同；原索引与未推送历史不能以新 `git read-tree` 重建结果冒充。接续前由执行方核实旧官网已停止，恢复组件在离线边界撤销旧身份、处理 running/unknown turn，并保留两个来源的原生记录和失败链。

对于下一次 WSL 执行，最小有判别价值的采集不是更频繁读取模型 heartbeat，而是进程退出与宿主资源事实：

| 需要捕捉 | 最小采集与解释 |
| --- | --- |
| 哪个原生进程因什么终态退出 | 将 run、Braid agent/provider/native session、PID、`/proc/PID/stat` starttime、PGID、容器与 cgroup 身份在启动时绑定；持有 child wait 的运行器保存原始 exit/signal 和观测时间，避免只留 `provider disconnected` |
| 是否是 OOM | 运行前记录 cgroup `memory.events` 基线与 `memory.max`，退出时立即保存其 delta、`memory.current`/`memory.peak`、`pids.events`。保留同一时窗的 kernel OOM victim 行；`oom_kill` 增量与 victim PID 相互印证。Docker `State.OOMKilled=false` 不能排除只杀了容器内 child |
| 资源压力从哪里上升 | 宿主程序在运行期保存有界低频资源序列，例如每秒 cgroup memory/current/pids 与 Pi/应用测试进程 RSS、线程数、父子关系；终态追加一份进程树。这是程序内采集，不唤醒模型；3+8 语义监控不足以覆盖几秒内的压力峰值 |
| 哪个程序发送 SIGKILL | 所有 Factory/Braid 主动 TERM/KILL、timeout/drop/cleanup 路径先记录 sender、target PID/starttime、signal 与原因，随后保存真实调用结果，区分信号意图与成功发送。宿主具备权限和 kernel tracepoint 时，再以原生 PID/cgroup 过滤 `signal_generate` 与 OOM victim 事件，取得外部 sender 或内核 OOM 的事实。仅 child waitstatus 无法给出 sender，SIGKILL 也不能在被杀进程里用 handler 捕捉 |

这四类记录应由宿主与 wait-owning 运行器落盘，在故障时冻结相同运行身份与时间窗；保存完整错误与数值，再生成摘要。重点字段即可，不需要原生 rollout 全量铺进主会话。对于本次官网故障，现有权限无法补采已过去的宿主 signal/OOM 事件，仍需要平台侧材料；后续新增设施不能把当前未知根因追认为已确证。

下一条真正能区分本次根因的证据是平台宿主在 **06:49:39–06:49:54 UTC**、容器内 **PID 19590** 的终止记录：cgroup `memory.events`/内存上限、内核 OOM victim，或平台 timeout/admin kill 审计，以及同一时点的进程树/RSS。现有公开只读接口没有这些材料，应先取得这组证据，再决定资源约束或生命周期改动；不自动重跑来猜测。

主线执行已新增授权的接续时，应在运行配方中冻结所选 ZIP SHA256、来源 run、费用模式及上述重建限制；使用副本重建 clone Git、核对六条原生会话及持久 turn，经过 Braid 离线接续接口。已存在的恢复声明和单独 Git commit 不替代完整检查点核实。本调查本身未启动任何恢复或新运行。
