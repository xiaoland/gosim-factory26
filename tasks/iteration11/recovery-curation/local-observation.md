# I11 本地 GitHub 恢复：前 20 分钟观察

本次运行是从 I10 GitHub 工作区摘剪副本继续，不是空白启动。实验 ID 为 `pi-braid-i11--hackathon--github-65b879cdc68a1f`；恢复来源为 `pi-braid--hackathon--github-7fe42a1248f9d8`。新容器中的 Braid 于 **2026-09-29 14:45:02 UTC** 执行 `local ... --offline-resume`，以此作为 T0。容器创建和长达约 17 分钟的恢复包逐文件扫描均未计入模型运行时间。20 分钟归档时 `run.json` 仍为 `running`。

四个包保存在 [observations](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations)。定时器在 T0+5/10/15/20 分钟触发；下表时间是远端归档、传输、本地校验全部完成的时间，不冒充瞬时快照时间。每包均已用 Python tarfile 完整遍历，并保存 SHA-256 与成员清单元数据。

| 批次 | 触发目标 UTC | 完成 UTC | 归档 | 字节 | SHA-256 |
| --- | --- | --- | --- | ---: | --- |
| 5m | 14:50:02 | 14:53:59 | [05m.tar.gz](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/05m.tar.gz) | 464,056,554 | `f6c303c6ff24cb6686ba8d4cdf5c09e7eda3f1a84fd0703c9babcd6cd3a62f3b` |
| 10m | 14:55:02 | 14:56:39 | [10m.tar.gz](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/10m.tar.gz) | 199,745,608 | `0baf640ecd9237827f6d5cea6d68fa6363c215063740d9e0475f63fd3ac9d3ed` |
| 15m | 15:00:02 | 15:01:26 | [15m.tar.gz](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/15m.tar.gz) | 190,019,892 | `7a91f999d7cee9028af42a1557fffb5b13069550aeaa01b3622b4ceb0ec0e805` |
| 20m | 15:05:02 | 15:05:55 | [20m.tar.gz](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/20m.tar.gz) | 202,011,938 | `1be32247eca1cd8fa19d76b3edbb261dbd1cbf77619997993b4a6d2d01c` |

归档使用 WSL 上的 `tar`、SSH 和 `scp`，未使用 `rsync`。每批在远端对非空 `braid.sqlite3` 做 SQLite 在线备份，备份位于包内 `db-backups/`，分析采用该备份而非正在写入的原文件。包保留 `.factory26`、应用源码、Git 对象与工作树、Braid DB、原生会话、配置和运行日志。再生依赖 `node_modules`、runtime、缓存、Playwright/npm 缓存、输入中的 runner/agent 压缩包、恢复源压缩包、`.private` 和 `*.env` 被排除；10m 起又排除已在首包保留的 `telemetry.sqlite` 与历史 `core.*` 转储。15m 首次 tar 因瞬时消失的 `braid.sqlite3-shm` 失败，立即排除该类 sidecar 重取；20m 首次 tar 又遇到 `telemetry.sqlite-{shm,wal}`，扩大到所有 `*.sqlite*-{shm,wal}` 后立即重取。两次均为取证归档竞态，不是 Braid 运行错误；四个最终包都校验通过。每包的 [JSON 元数据](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/20m.json) 记录具体成员路径。

恢复确实换用了 I11 运行材料。[05m 恢复证明](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/05m-recovery-provenance.json) 记录 `mode=workspace-resume`、`refresh_native_materials=true`、旧运行身份及新 Braid/指引文件散列；[05m 请求](/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260929-feasibility/observations/05m-braid-request.json) 配置 `pi-glm-fast` 根 Profile、`glm-5.3-flash` 与 `deepseek-v4-flash` 两个 Pi Profile，窗口均为 1,000,000 tokens。PR #19 新会话中的首条重建上下文包含 I10 摘剪后的 M4b 接续摘要、原候选 head `0aa49d2`、未提交文件和复核顺序；它不是只创建了空会话。根 Issue #1 的新会话未建立，不能据配置文件证明根实际接收了这些指引。

| 观察点 | 实际证据与边界 |
| --- | --- |
| 5m | Braid 创建了 PR #19、Issue #7、Issue #9 的新 Pi 会话，另有 Issue #7 一次后续重建。PR #19 的归档原生 JSONL 已有 39 条 assistant、48 条工具结果；模型读取保留的未提交 diff，指出自己把 URL 空格编码从 `%20` 变为 `+`，触发既有断言失败。归档 Git 工作树仍含 8 个未提交文件，包含原 `AppShell.tsx`、`SearchPage.tsx` 和 `code-search.spec.ts`。 |
| 10m | PR #19 会话达 50 条 assistant、59 条工具结果。第一次 Playwright E2E 实为 117 通过、1 失败；外层 shell 因管道误印 `E2E_EXIT=0`，不能据此判绿。模型修正后第二轮工具输出 `118 passed` 和测试进程 `exit code 0`，随后继续 platform-path 检查。 |
| 15m | PR #19 会话达 60 条 assistant、70 条工具结果，完成检查后把保留的未提交代码与新增测试、文档分别写成本地 commit：`ef71100`、`36344be`、`56f53ae`。归档 Git head 为 `56f53ae`，按内容比较工作树干净。唯一 `toolResult.isError` 是诊断命令读取不存在的临时 `h-*` 日志后退出 1，未见模型 API 参数错误。 |
| 20m | PR #19 会话达 83 条 assistant、89 条工具结果，并消费 Issue #7 后续更新；Issue #7 的另一个 DeepSeek 会话开始独立核查 `56f53ae`，文本称 `pnpm test` 为 12 文件、151 测试通过，仍在继续。在线 DB 的本轮 turn 为 5 completed、1 running；本地评论从 273 增至 275、事件从 1023 增至 1028。PR #19 归档 head 仍为 `56f53ae`，原三文件改动已经入 commit，工作树内容干净。 |

PR #19 新会话确实使用 Pi 的后台作业：`bash` 启动 `bg001`/`bg003`/`bg004` 等，`pbb tail` 取得构建、E2E 和平台检查输出。`subagent_wait` 返回的是 **0 async run、1 provider item**，不能当作新原生子代理启动证据。Playwright E2E 确实运行 Chromium，但新会话中未见 `agent-browser` 专用工具、技能文件调用、Context7/Exa 或 MCP 调用；这些能力在此 20 分钟窗口内仍属未验证。已观察的 DeepSeek 与 GLM assistant 消息 stopReason 只有 `toolUse`/`stop`，无 `errorMessage`；这只证明这些已建立会话的 provider 应答，不能覆盖下述失败成员。

## 未恢复的四个成员

20m 归档的 Braid 日志在 14:45:43–49 UTC 记录四次 `cannot replace Agent Context: session is unavailable`。SQLite 在线备份把失败明确对应到以下工作项；四个 assignment 仍标 `active`，但 Agent、旧 provider session 和 reset 均为 `blocked`。因此本次并非全员恢复，尤其根 Issue #1 未恢复。

| 工作项 / 成员 | reset ID | 恢复时新建物理会话的记录 |
| --- | --- | --- |
| Issue #1 / `glm-1` | `01a0eda0-5776-71d1-8d08-6fb9420cf057` | `braid-state/physical/01a0eda0-7032-7703-a2ec-b935c71d531f/session.json`：`failed`、`session is unavailable` |
| Issue #6 / `deepseek-9` | `01a0ed0d-5d0e-7201-85a6-b4309db4b66b` | `braid-state/physical/01a0eda0-60eb-7313-879e-128ab7dd356f/session.json`：同上 |
| PR #16 / `glm-12` | `01a0ed0d-6845-7f10-b921-55f399e867ae` | `braid-state/physical/01a0eda0-6eed-71b2-9379-11e5d7b544eb/session.json`：同上 |
| PR #20 / `deepseek-18` | `01a0ecee-62a4-7d61-b598-a6e4baca3d87` | `braid-state/physical/01a0eda0-67d1-70f0-b88c-efdde5126fa1/session.json`：同上 |

四条旧 Pi JSONL 会话文件均在 20m 包中，故不是“恢复包缺少旧会话文件”。失败物理记录是**新建**会话 `failed`，而不是只缺旧进程；其他相同 Pi Profile 随后成功创建会话，也排除了全局缺少 Pi 可执行文件的解释。三条 reset 从 I10 副本带入待处理状态，根 Issue #1 的 reset 在 T0 建立；四条在本轮物理启动时失败。当前源码中的 `PiSessions::start` 调用 `ProviderAgentSession::start`，其 Pi `new_session` 启动/传输错误会映射成笼统的 `SessionError::Unavailable`；`materialize_next_context_reset` 随后调用 `fail_context_reset` 将 reset、Agent、旧 session 一并置为 `blocked`。已查看的 Braid 日志与 `physical/session.json` 未留下更细的原始启动错误，不能断言是并发峰值、RPC 超时还是子进程退出；“启动突发导致瞬时失败”仅是可能原因。旧 provider 进程不在新容器本属预期，现有旧文件并不能代替新物理启动。

修复首先要在**新物理会话身份尚未产生**的错误边界保留原始 Pi 启动原因，并给受影响成员明确可操作的恢复入口。`start_session` 在取得 `sessionFile` 前失败与已经产生身份后的失败必须区分，避免双投或丢上下文。当前活动 I11 未因取证被修改或重启；没有安全的现成 CLI 操作可据这些证据直接解封四个成员，尤其不能编辑 live SQLite 或从 PR #19 局部成功推断根可工作。后续恢复应先保存当前状态，再针对四个 blocked reset 走下述受限路径，不碰暂停的 I10 容器。

## 四次物理启动故障的后续定位（只读取证）

继续检查当前容器和四个 `braid-state/physical/<id>/` 目录：每个目录只有已渲染的 `context.md`、`instructions.md` 与 `session.json`，没有单独的 stderr；按创建时间对应的四个新 Pi native home 均没有本次 `*.jsonl` 会话文件。当前 `recovery-braid.log` 中 `provider diagnostic` 为 0 条，仅有四条上表的上层 `session is unavailable` 错误。旧会话文件都存在，故可以把失败范围缩到**新 Pi 会话拿到可恢复身份之前**，仍无法由现存证据区分子进程 `spawn` 失败和本地 `new_session` RPC 写入、断连或超时。`new_session` 是 Pi 本地 RPC，尚未向模型发出工作提示，不能称为模型 API 参数错误。容器内存限制为 4 GiB；只读 cgroup 计数显示触及 `memory.max`，`oom=0`、`oom_kill=0`，这不是四次失败的因果证明。

丢失细节的位置已定位：`PiProvider::start_session` 的 `spawn` 与 `new_session` RPC 原样产生 `ProviderError`，接着 `ProviderAgentSession::start` 调用 `map_provider_error`，把 `Start(io::Error)`、`Timeout`、`Disconnected` 都变为无详情的 `SessionError::Unavailable`；记录器最终只能把这串概括性文字写进 `physical/session.json`，`fail_context_reset` 也只能持久化相同文字。已在 [Pi provider](/Volumes/WorkSSD/Development/factory26/sources/braid/src/provider/pi.rs:313) 两个原始错误仍存在的位置分别补上阶段和 `%error` 的 tracing。它只改善下次运行的诊断，不改变返回类型、数据库状态或当前活动容器；`cargo check -q` 通过，未运行测试或模拟探针，也未部署该源码。

原有恢复机制不会重试这种 blocked 状态：`ready_context_reset` 只选 `materializing`，`begin_context_reset` 需要旧 provider `idle`，而原有 `prepare_offline_resume` 不会重新入队。因此仅再次执行未改动的 `--offline-resume` 无法解封。受限恢复必须先停止并保存**本次 I11**状态，再核当前责任关系与物理身份，把仍合格的 reset 及其事件交给现有 `ready_context_reset`/`materialize_context_reset`；不能机械重放观察时的四条，也不应直接操作运行中的 DB。

## 冷接续源码修复

获授权后，已在 [StoreActor 的 offline-resume 准备事务](/Volumes/WorkSSD/Development/factory26/sources/braid/src/store/mod.rs:3071) 实施上述受限恢复，而非手工修改 live DB。持久化选择同时要求：`blocked` reset 的错误**精确**为 `session is unavailable`，`new_session_id` 和活动 turn 均为空；旧 provider 是 Pi 且仍 blocked；Agent 同因封锁；工作项仍 OPEN、assignment 活动、当前成员/Profile/指派版本与 desired 状态一致，原工作树仍活动；同 Agent 没有后续 reset 或更新的 provider session；reset 持有的事件仍全部 blocked。另读取旧运行的 `braid-state/physical/<UUIDv7>/session.json`，只有 reset 之后同 Agent 的物理尝试均记录 `failed`、同一错误且 `session_id`/`native_session_path`/`native_session_id` 为空，并确有至少一条这种失败记录，才恢复原 reset 与其事件。缺文件、记录不可读、已创建或身份不明一律保持 blocked。

重新入队只在一次已获停机证明的 `--offline-resume` 事务中发生：原 reset 改回 `materializing`、Agent/旧 provider 改为 `reset_pending`、其事件改回 `resetting`，之后仍由既有物化和 continuation 路径接手。没有运行中定时重试；再次失败仍封锁。最新运行中只读状态已经不同于 20m 观察：PR #20 旧 assignment 已 retired 且新 session 在执行，Issue #6 已 CLOSED、PR #16 已 MERGED，故这三项不会被该选择条件重放；若冷包时根 Issue #1 仍 OPEN 且未被改派，才可能成为候选。主线负责停机、备份和实际冷接续；本段只说明源码逻辑，不声称新 binary 已运行或恢复已经成功。

根 Issue #1 的 reset 若 `continuation=false`，应用时会消费 description invalidation，不会立即注入新的 work prompt。现有主循环在 root OPEN 且其新 session 可执行、没有待处理输入时调用 `root_idle_tick`，从该时点重计约五分钟后产生并定向发送 root progress check 评论；这条既有路径负责唤醒 root。冷接续验证需分别确认 reset applied、新物理 Pi 身份、该评论送达，以及其后真实模型响应，不能只凭新 session 文件宣称恢复成功。

已冻结当前含未提交改动的 Braid 源码并在 WSL 的缓存 Rust 1.93.1 容器中执行 `cargo build --release --locked --offline`，编译成功，未执行测试、模型或官网任务。交付物位于 `runs/iteration11/20260929-cold-resume/build/`（WSL 仓库）：`braid-source.tar.gz` SHA256 为 `24957f29608de36b00ce59a92a66dfd29503d8e52e18aab75132d7dccfcc9e9a`，Linux `braid` SHA256 为 `5c802c32e452ebe8c0de9182bfa4a5298c7cabcf1097d1dccf95ae6a031f17eb`；`build-identity.json` 记录 git HEAD、dirty diff 与构建身份。此处仅证明新 binary 来自该源码快照，实际恢复成效仍待冷接续日志和 DB 核验。

## 冷接续实际核验

新单题 run `pi-braid-i11--hackathon--github-f402061b5bc88f` 由已核 SHA256 为 `4b54da87d1b7f29b297a0bd23db5a1a72c3ddc43831b2c0e8c99067e1d19131b` 的包启动。Braid 于 2026-09-29 16:02:43 UTC 开始 `--offline-resume`。同一根 Issue #1 的原 blocked reset `01a0eda0-5776-71d1-8d08-6fb9420cf057` 在 16:03:02 UTC 成为 `applied`，错误清空、新 provider session `01a0ede7-baa2-7ca3-bc2b-090b54f118bd` 建立；16:04 UTC 只读 SQLite 显示其为 `running`，对应新 Pi JSONL 有 8 条 assistant 消息、最近为 toolUse、无 `errorMessage`。根成员已经有真实模型响应，不只是进程或文件存在。

这次 root 的直接触发是 14:45 已保留的 wake batch `01a0eda0-578b-7372-9539-12315d09e23a`，包含既有 reset continuation 与评论 #276–#290；新 turn 于 16:03:03 UTC 以 `wake_batch` 开始。16:04:38 UTC root 自编辑又产生 continuation=true 的 Context reset。当前没有新 root progress check 评论，故本次只能证明已有 wake 正常续接；五分钟 idle check 的回退代码路径仍未在这次运行中实际触发。

PR #20 旧 Pi session 在恢复时报告 `Session file is not a valid pi session` 和 `provider disconnected`。该旧 JSONL 文件存在（208115 bytes），但第一行是 `type=message` 而非 Pi session header；这是文件格式原始证据，尚未证明缺 header 发生在哪个归档步骤。Braid 随后于 16:03:01 UTC 为 PR #20 应用另一条 Context reset 并建立新 session；不能把旧文件恢复报错误记为该新 session 的模型执行成功，也没有改写运行中的旧文件。

16:05:30 UTC，root 的自编辑 reset `01a0ede9-34f5-79e1-a6ee-2e4773af6b5d` 也成为 `applied`（`continuation=true`），16:05:31 UTC 新 `wake_batch` turn 开始。第二个新 Pi JSONL 在随后的只读观察中已有 6 条 assistant，最近为 toolUse；首个冷接续 turn 已记为 `completed`。因此不只是最初身份less reset 被解封，后续自编辑重建与实际续接也走通；本观察仍不代表整个应用或所有成员完成。

四条原失败 reset 的只读对照显示：仅 Issue #1 的原 reset 由 blocked 变为 applied；Issue #6 仍 blocked 且工作项 CLOSED，PR #16 仍 blocked 且 MERGED，PR #20 的原 reset 仍 blocked、旧 assignment 已 retired、工作项现为 MERGED。后面三条未被此次 offline-resume 误重放。


## 当前只读快照：2026-09-30 08:43–08:46 CST

本段来自当时 WSL 的 run.json、SQLite `mode=ro` 查询、最新原生 JSONL 和 Git refs，替代把上面的首次恢复观察当作当前状态。未重启、改 DB、修改应用或执行验收。

`github-f402061b5bc88f` / 容器 `arcbench-local-f495d20d0a75` 仍为 running / Up，但 **没有 running turn**。最新原生 assistant 响应为 2026-09-29 17:09:53.980 UTC（北京时间 9 月 30 日 01:09:53），DeepSeek 正常 stop、无 errorMessage；此后逾七小时未见新的模型响应。因此当前是容器存活而生成停滞，不能称为继续推进。

实际进展已超过首次冷恢复：PR #19/#20/#21 均 MERGED，Issue #3–#9 均 CLOSED。当前只剩 root Issue #1、M6b Issue #10 和 PR #22 OPEN。M6b 分支候选已到 `42b2f64a2389a4d80f70c9cbded6096e766c9ce4`；Issue #10 评论 #332（17:08:57Z）记录独立核对后交根合并，列出 194 单测、152 E2E 与平台路径通过，并保留负载相关失败和重跑。这里记录的是运行成员的持久验收报告，本次没有重跑验证。Git refs 确认候选尚未合入：develop 仍为 `e5110cbba3560412b5a81163aee3e100c1803c7c`。

三个 OPEN 工作项的当前 active agent 全部 blocked，context_error 均为 `session is unavailable`：root 的 reset `01a0ee12-480e-7273-a8a2-2adac39001c9` 于 16:50:56Z blocked；PR #22 的 `01a0edf7-0a3b-7731-be53-2eaefd2a3798` 于 16:52:14Z blocked；Issue #10 的 `01a0ee24-4c3d-7151-92be-1c60fdb88c78` 于 17:10:26Z blocked。恢复日志保留 `Pi new_session RPC failed: provider request pi_rpc timed out`，最新一条为 17:10:25Z。root 早先成功恢复的事实仍成立，但后续 Context 重建再次失败，当前不能工作。

**尚未生成交付**：`local_run.lifecycle=running`、`delivery_commit=null`，main 仍 `2914d2ddf2a9cc5723619fd2cef53f5b21b8c3ac`，未见恢复完成或 runner 生成结果。下一决策是有界恢复这些现行 OPEN assignment 的 Pi 身份创建故障；本次只读任务未实施恢复。


## 当前 Pi 超时与最小恢复边界（2026-09-30 08:50 CST，只读）

本次五个现行失败（GitHub root/Issue #10/PR #22，Sheet root/PR #13）原始日志均为 `Pi new_session RPC failed: provider request pi_rpc timed out`。冻结构建源码 `20260929-cold-resume/build/source/braid/src/provider/mod.rs` 的 `REQUEST_TIMEOUT` 是 30 秒；`provider/pi.rs` 在 spawn 子进程后立刻发送 `new_session`，等待响应后才 `get_state` 取得 native identity，之后才注入工作提示。故这是同一 **Pi 本地启动握手边界**，不是模型 API 超时，也不是已知的旧 JSONL header 格式错误。五个最新 `physical/session.json` 均 failed，session/native ID/path 全为空。stderr 没有对应故障细节；不能把 I/O/CPU 压力推断为已证根因，也不能断言延长等待必然修复。

此前 GitHub root 冷恢复成功说明同一现有身份less恢复路径可重建 Pi 并收到模型响应，但不保证后续重建不再超时。当前故障发生在该成功之后，不能沿用首次成功结论。最小方案应先修正恢复选择的具体遗漏，再在完整保留现场、确认旧进程停止后做一次冷接续；不刷新全体指令，不重新安装 runtime，不全量重跑任务，也不改 live DB 或建立无限自动重试。


恢复选择的具体遗漏已证：对冻结源码 `prepare_offline_resume` 中原 SELECT 以 SQLite `mode=ro` 查询，GitHub 返回 0 候选。三个 reset 的 `active_turn_id` 非 NULL，但对应旧 turn **全部 completed，且在新物理尝试失败前已经结束**。现有筛选 `cr.active_turn_id IS NULL` 误把“保存过去已完成 turn 的关联”当成“仍有在途 turn”。只读把这一条改为 NULL **或该 turn 属于 cr.old_session_id 且 lifecycle=completed**，其余原守卫不变，恰好选中现行 root/Issue #10/PR #22；三个候选的后续 physical 也都满足 failed + session is unavailable + 无任何 native identity，未发现更晚成功身份。

建议最小源码改动仅放在这条 offline-resume 候选条件：接受上述已完成旧 turn，保留原字段和 continuation，不伪造 NULL；仍排除 starting/running/unknown/failed，保留 OPEN、active assignment、owner/Profile/revision 一致、无更新 session/reset、所有 reset event blocked、失败物理记录等现有条件。这是恢复范围补齐，尚未实施。30 秒握手超时的底层成因仍待真实接续反馈；不把扩大全局 RPC 超时混入此修复。


## 已授权最小筛选修复与离线构建（2026-09-30）

主线依据用户已有 I11 恢复缺陷修复授权，要求落地上述已证筛选修复并准备 Linux binary，暂不动 live DB、停止容器或启动接续。已在 `sources/braid/src/store/mod.rs` 的 identityless reset 查询中，将 `active_turn_id IS NULL` 扩为 NULL 或存在属于 `old_session_id` 且 lifecycle 为 completed 的 turn。其余条件与任何历史字段均未改；没有扩展到 unknown/failed/running turn，没有更改全局 RPC 超时，没有新增测试。

为了不把其它工作树脏改动带入制品，构建基于此前运行过的 WSL `20260929-cold-resume/build/braid-source.tar.gz`（SHA256 `24957f29608de36b00ce59a92a66dfd29503d8e52e18aab75132d7dccfcc9e9a`），只加入相同 SQL 增量。新输出目录为 WSL `runs/iteration11/20260930-completed-turn-resume/build/`，含 `completed-turn.patch`、完整源码 tar、构建日志和身份材料。复用 `rust:1.93-bookworm` 镜像、`factory26-cargo-registry` / `factory26-braid-target` 缓存卷；网络关闭，2 CPU / 3 GiB，`RUSTUP_TOOLCHAIN=1.93.1 cargo build --release --locked --offline`。首轮未指定工具链覆盖，源码指定 1.93.0 导致离线下载失败，已原样保存为 `build-initial-toolchain.log`；随后显式使用前次成功构建的已安装 1.93.1，不改源码工具链文件。


构建已完成：release exit 0，耗时 2m31s，13 条 warning；未运行测试或模型。WSL 新 binary 为 `/home/yyh/Development/factory26/runs/iteration11/20260930-completed-turn-resume/build/braid`，SHA256 `3056feb7a599addeb82e0250d6a0cc1e055d9e8e78f0151ca12ea75582605bf4`。同目录完整源码 tar SHA256 `fa7e91a01c8a6b09ecdb3b2730babebc271cc9f5a4ab3afdbf09b2278675fc28`；增量 patch SHA256 `87485f575db41e7f559eb3594f39ef70f15198336337dd86726a691817d53a7e`，详见 `build-identity.json`。运行中的旧 binary 和两容器均未改。

下一步接续仍使用现有 `scripts/package_completed_recovery.py`：先停相应旧执行并保存包含 Git/未提交/native/SQLite/physical 的一致现场，再用该现场 ZIP、现有 `20260929-cold-resume/prepared/base-agent.zip`、新 binary/source tar 打包，传 `--continue-generation`，**不传** `--refresh-native-materials`。`--source-run-id` 分别使用当前 `github-f402061b5bc88f` 或 `sheet-db75cf2c3b82be` 的完整 run ID，不能回退到更早 I10 快照。复用对应已记录 launch.py 的单题、自有 API、4GiB/2CPU参数，新实验目录与新 agent.zip 必须匹配。

恢复入口最终调用的容器内命令为：

```sh
/workspace/template/.factory26/20260929-042409-1202e245/work/bin/braid local /workspace/template/.factory26/20260929-042409-1202e245/braid-request.json --offline-resume
/workspace/template/.factory26/20260929-042409-811f18d4/work/bin/braid local /workspace/template/.factory26/20260929-042409-811f18d4/braid-request.json --offline-resume
```

以上分别属 GitHub/Sheet，须由现有 recovery 入口在保留环境与已替换新 binary 的新执行环境运行；不是授权在仍存活旧容器内并发执行。当前只完成编译材料交付，尚未冻结新的停止现场或启动这些命令。


## 本轮实际恢复部署已开始（2026-09-30 08:57 CST）

主线已明确授权对当前 GitHub `f402061b5bc88f` 与 Sheet `db75cf2c3b82be` 做一次受控冷接续，并要求新版 `3056feb7…` binary、单题自有 API / 4GiB / 2CPU、不刷新原生材料、不改应用或模型。已核 Docker `/workspace` 挂载与两个 run 路径一致，记录 pre-stop identity 后，只停止 `arcbench-local-f495d20d0a75`、`arcbench-local-cd5c76728316`。原两暂停 I10 和官网任务均未触碰。

完整 template 直接流式归档至 Mac `runs/iteration11/20260930-completed-turn-resume/{github,sheet}/source/template.tar`；保留未提交代码、Git、SQLite/WAL、native、physical、权限与链接。停止前/后的 run 和容器身份另存于同名 WSL 新目录的 source。当前 WSL 仅余约 5GiB；主线已授权在归档可读取并确认含 template/DB/native/Git 后，仅删除两个停止 run 的 `workspace/observed-agent` 与 `workspace/official-generation/submission` 这两类可重建载荷，以及已封包 workspace.zip 中间材料；原位 template/DB/native/Git 保留。不把人工停止后的 failed 状态当应用交付失败或评分。


### 停止现场迁离 WSL（已追加授权）

两份完整归档已可读并核对 DB/native/Git；新双 run 空间不足，主线允许将**这两份停止现场**从 WSL 迁离，Mac 唯一归档永久保留，原暂停 I10 不动。逐项映射、完整 SHA 和恢复命令保存在 `runs/iteration11/20260930-completed-turn-resume/migration-record.json`。恢复用 `tar -xpf <archive> -C <new-workspace-parent>`，保留 template 根路径。

- github：`/home/yyh/Development/factory26/runs/iteration11/20260929-cold-resume/generation/runs/pi-braid-i11--hackathon--github-f402061b5bc88f/workspace/official-generation/template` → `/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260930-completed-turn-resume/github/source/template.tar`；SHA256 `7754fff84824fc9b27bb3f2180de8a36ce98135f0f3db6351dd264e0f085cd92`。

- sheet：`/home/yyh/Development/factory26/runs/iteration11/20260930-sheet/generation/runs/pi-braid-i11--hackathon--sheet-db75cf2c3b82be/workspace/official-generation/template` → `/Volumes/WorkSSD/Development/factory26/runs/iteration11/20260930-completed-turn-resume/sheet/source/template.tar`；SHA256 `ed9165029deeade35822b231b65e2ebd2a0d005ff5e2025c01e35786b2897e92`。


### 本次 GitHub 接续结果：失败，未重试

新 run `pi-braid-i11--hackathon--github-5c52a331ef0d5c`，容器 `arcbench-local-4811f5cd77f2`；恢复包 SHA256 `0b16156fdfc751dc359786dc76c742c372cd290bf65498ea9f72b3b903162c43`，workspace ZIP SHA256 `e435778486b78612e0fd8a54c44485cbff39c8f1a66588475739c52b97aba8a1`，binary `3056feb7…`，refresh=false。01:31:37 UTC 开始 Braid。

01:32:15–20 UTC 原三个 reset 均产生新 physical 后再次 blocked：root `01a0eff0-68b2-7483-9573-6ac04329241f`，PR #22 `01a0eff0-5c87-7403-a003-0720f558a73a`，Issue #10 `01a0eff0-5a4c-77b0-a7a3-b398dc082731`，全部 failed、无 native identity；原错仍为 `Pi new_session RPC failed: provider request pi_rpc timed out`。筛选遗漏已在真实调用中补齐，但本地 Pi 初始化超时并未解决，不能宣布恢复成功。没有新 assistant 响应，也没有交付。

原始 recovery-braid.log、只读 SQLite online backup 和三个 physical 的 session/context/instructions 已保存于 Mac 与 WSL `runs/iteration11/20260930-completed-turn-resume/github/evidence/first-resume-failure/`。按本次每题一次边界，不重启、不调大超时、不改 live DB。仅删除已完成复制用途的此新 run `workspace/observed-agent` 重复载荷以为 Sheet 留空间，运行中 `official-generation/submission` 和 `template` 保留。


## 2026-09-30 10:03 CST 原位修复实际验证

新 attempt `pi-braid-i11--hackathon--github-0d0cb6e9982fc1` 经既有lab continuation入口启动，run.json=running，container=`f26-continue-0d0cb6e9982fc1`，4GiB/2CPU、自有供应商不变。generation.resource.json明确关联保留的 `github-5c52a331ef0d5c/workspace/official-generation`。只换Braid binary与启动诊断，不refresh材料/应用/模型，不覆盖旧失败结论。容器内SHA256实测为 `d76d65f133979a9f310b39e73fc254f727b564734ee1513c4febe6fbecb083be`。

三项握手成功：PR22 122763ms、root 124012ms、Issue10 129190ms，reset均applied。新native ID依次为 `01a0f008-fda5-715f-89bb-205f06b895ae`、`01a0f008-fd9b-72c4-8a04-2d2d5a4e7033`、`01a0f008-fda6-704a-886c-255bfc94913f`。首次assistant分别09:59:43.022、09:59:44.216、09:59:44.629 CST；root首个bash实际读取评论331和332，工具结果包含原评论正文，DB中332对glm-1/deepseek-22均delivered。不是仅凭running状态判恢复。

原始证据在Mac和WSL同一repo相对目录 `runs/iteration11/runtime-stalls/github/evidence/first-response/`：SQLite backup、三个原生JSONL、完整continuation日志、runtime-snapshot.json。10:02:57样本：cgroup oom/oom_kill=0；容器IO full avg60=11.09%，host24.73%，磁盘余10GiB。说明真实首启在资源压力下耗时较长；不将main分段timing相加，也不声称冗余new_session单独解释所有旧失败。

后台watch已用持久observer代码启动，PID1698832；首条已通过resource契约找到retained DB，2 active turns/6 pending/无blocked owners，stderr为空。输出 `runs/iteration11/runtime-stalls/watches/github/watch.jsonl`，退出码另存exit-code。Sheet watcher PID1698834，首条1 active/21 pending/无blocked owner。运行继续，不再重启。Sheet保持3056旧binary，避免打断有效生成。
