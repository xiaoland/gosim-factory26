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
