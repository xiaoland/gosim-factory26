# 运行中诊断入口改进

状态：2026-09-28 获用户授权实施设施改进；运行中 viewer 改进已用真实 DeepSeek Sheet 生成目录验证。改动在 `lab/analysis`、恢复入口和设施文档，不改 Braid、variant、冻结运行输入或生成应用。当前真实证据见 [四条 run 截面](../../braid-product-hardening/cells/live-run-evidence.md)，停止前后的模型/进展比较见 [对照](flash-deepseek-process-comparison.md)。

## 需要解决的缺口与最小改动

现有 `native_profile.profile()` 强制读取终态 `native/manifest.json`，viewer 也只在归档存在时接入。因此 DeepSeek Sheet 的运行中页面虽从包内 OTLP 数据库生成，却没有 `profile.json`。改为在 manifest 尚无时读取同一 `.factory26/<run>` 的 `braid-state/sessions.json`、原生 Pi JSONL 和 `pi-timing.jsonl`；映射容器绝对路径时限制在该 run 内。保留归档 manifest 作为终态权威，运行中状态显式标记 partial，未结束请求不填用量或耗时。按实际 model/provider、根 Braid provider 会话与 Pi 内部子会话分层展示；usage 按原生 assistant 消息 ID 去重，已知字段数和请求数分开，不把 Pi 占位 cost=0 当价格。

Viewer 从已识别的生成目录拷贝原始 `braid-state/telemetry-errors.jsonl` 和 `braid.log` 到输出目录，展示带原始文件链接的有界错误摘要。发生 capture timeout 时标记批次完整性未知；`receive_errors=0` 与重建成功均不能抹掉源端超时。沿用现有页面和 Backend，不增设采集协议或数据层。

WSL 两条 attempt 已有 `monitor-generation.py` 按 run 开始时间以 180/480 秒采样。现有脚本已覆盖计划间隔；在[运行说明](../../../docs/deployment/index.md)明确了同时核对最后采样行和同一路径进程、确认不存在旧进程后用原脚本接续的入口。未改正在执行的进程，也未新增调度框架。

## Flash 模型费用判别材料

2026-09-28 03:29:10 UTC 的 WSL `attempt-02` 截面。来源：每例 `.factory26/<run>/work/native-homes/*/*.jsonl` 的 assistant usage（按 session/message ID 去重）、`pi-timing.jsonl` 的不同 `request_id`、`braid-state/sessions.json` 的根会话身份。表中 tokens 为已结束消息报告的字段；MiniMax Sheet 有 1 个开始但尚未结束请求，其用量未知。Pi 的 `input` 与 `cacheRead` 为独立字段，不能把价格或 `cost=0` 占位推成实际收费。

| 题 | 实际模型/provider | 根 Braid provider 会话 / 已见 Pi 子会话 | 请求开始 / 已结束 | input | output | cacheRead | cacheWrite |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GitHub | qwen3.6-flash / factory26 | 2 / 0 | 284 / 284 | 20,343,865 | 137,468 | 0 | 0 |
| Sheet | qwen3.6-flash / factory26 | 2 / 0 | 299 / 299 | 21,781,738 | 139,767 | 0 | 0 |
| 合计 | qwen3.6-flash / factory26 | 4 / 0 | 583 / 583 | 42,125,603 | 277,235 | 0 | 0 |
| GitHub | minimax-m3 / factory26 | 2 / 0 | 220 / 220 | 277,084 | 44,727 | 5,618,865 | 0 |
| Sheet | minimax-m3 / factory26 | 2 / 0 | 299 / 298 | 262,752 | 91,739 | 13,958,421 | 0 |
| 合计 | minimax-m3 / factory26 | 4 / 0 | 519 / 518 | 539,836 | 136,466 | 19,577,286 | 0 |

MiniMax 的 GitHub/Sheet 原生 assistant 分别有 67/74 条 error 消息，四项 Pi usage 均报告 0；成功消息分别为 153/224 条，承载了表中全部 token。Qwen 两题的 284/299 条消息均为成功，未见 error。这里的成功只指 Pi assistant 未以 error 结束，不等于产出的工作有效。已结束消息的四项 usage 均有数值，但这些数值不等于收费账单，429 失败请求是否收费需平台账单佐证。`cacheRead=0` 仅是 Pi JSONL 与同源回调的标准化返回；本批未取得 ARC 网关原始 response usage，不能断言供应商确实没有 cache hit。已见子会话数为当前记录中的事实，不保证未来不会启动内部子代理。

## 验收

已把本地修改的 viewer 三个文件放入 DeepSeek `attempt-02/analysis/live-diagnostics-code/` 作一次性分析执行（未改冻结 `code/`）；从仍运行的 Sheet 生成目录实际生成 `generation/analysis/live-viewer-profile/index.html`、`profile.json`。该次页面查询包内 SQLite 固定至第 364 批，Braid 重建 8 会话、状态 partial；`profile.json` 为 `live-unarchived`、有 Pi 时间事件，显示 4 个 GLM 根、4 个 DeepSeek 根、DeepSeek 与视觉模型各 1 个 Pi 子会话，未结束请求保留空用量/时间。`source-errors/` 保留并在页面索引原始 `telemetry-errors.jsonl`、`braid.log`、runner stderr；页面含 Timeout(5s) 与原文件链接。生成结束后数值仍会增长，以上是 03:36 UTC 的一次快照，不是终态或网页视觉交互验收。

随后将修正过 Pi 根会话轮换文件与子会话源文件读取的最终分析代码，在同一真实 Sheet 运行材料上生成 `generation/analysis/live-viewer-profile-v3/index.html`。固定至第 469 批、Braid 重建 8 会话、状态 partial；剖面为 `live-unarchived` 且 gaps 空，含 4 个 DeepSeek 根、2 个 DeepSeek 子会话（两个会话均使用过 DeepSeek）、1 个视觉子会话及 4 个 GLM 根。页面模型表已从 `profile.json` 核对；`analysis.json` 记 50 条源错误摘要，`source-errors/` 包含三份原文件。该静态页面仍是生成时刻快照；不能据此声称全部源端 OTLP 批次无丢失。后续主线依用户指示停止 DeepSeek attempt-02 并冻结半成品，观察窗不再增长。

恢复入口 `submission/recover_completed.py` 原本直接启动 Braid，未装配包内 OTLP 接收器与 Pi timing，也未在恢复后新归档 native；本次复用 `support/agent_support.py`、`support/core.py` 的已有 helper 接线。ZIP 解压恢复 Unix symlink 和 mode，旧 native 目录重命名保留；诊断失败写 `recovery-diagnostics.json`，清理失败仍阻断交付。仅做 Python 编译验证，实际新恢复包由主线后续冻结和执行，不能把上面的 attempt-02 viewer 验收冒称恢复入口验收。

没有编写或运行 Factory/devinfra 测试、模拟探针、benchmark；本 agent 没有停止或重启任何 run。Flash 两题及后续 DeepSeek 两题均由主线按用户指示取消；Flash 外层 wrapper 将取消误记 failed 的来源与新 attempt 用法已写入运行说明，旧执行记录未改写。

## attempt-03 恢复启动延迟与采集核对（只读取证）

DeepSeek 恢复包在 WSL 的 GitHub/Sheet 主进程分别约 03:52:52/03:53:13 UTC 启动。GitHub 的 `recovery-braid.log` 首条为 03:57:45，Sheet 为 03:58:44；进入 Braid 前约 4 分 53 秒和 5 分 31 秒。主线先前看到 GitHub PID 189608 在 `folio_wait_bit_common` 且 fd 3 指向 `runtime/node_modules/typebox/.../compile.d.mts`；本次看到 Sheet PID 189884 在同一等待点、fd 3 指向 `support/otlp-deps/google/type/month_pb2.pyi`。它们都符合 `verify_package(ROOT)` 逐文件读取及校验阶段；Github 当时进程累计 `read_bytes` 约 1.205 GB、Sheet 约 637 MB，但这些计数覆盖进程此前所有读取，不能全部归算为校验。两包 ZIP 分别约 516 MB 和 740 MB；校验后还需读工作区 ZIP 与解压。03:57–03:59 WSL `io` PSI `full avg10` 约 61%–64%，内存可用约 11 GiB、磁盘余约 194 GiB。这个窗口的显著压力是磁盘 IO 等待，未见内存或容量耗尽；不能从一次截面分解出校验、解压各自的精确耗时。

`verify_package` 先遍历全包检查符号链接与文件清单，再对 manifest 每个文件以 `path.read_bytes()` 算 SHA256。最小可改进点是在恢复入口利用它已经验证过的 `recovery-workspace.zip` manifest SHA，与 `recovery-source.json` 的 `workspace_sha256` 比较，省掉紧接着对同一个 80/304 MB ZIP 的第二次全量哈希；这是同一受校验 manifest 中的哈希与已验证来源记录相互核对，不需降低载荷校验。将逐文件哈希换为流式 `hashlib.file_digest` 还可避免大文件一次读入 Python 堆，但磁盘总读量不变，不能承诺消除上述启动延迟。两个大包并行校验和解压是否值得错峰，需要另测单包与并行吞吐，不从本次 IO PSI 猜定收益。

GitHub 03:57:42 新建包内 `telemetry.sqlite` generation session；恢复窗口截至终态收到 logs 8、traces 4、metrics 2 批。Sheet 包内同样收到 logs 17、traces 4、metrics 2 批；两份 `recovery-diagnostics.json` 均为 `{}`。GitHub 源端 `braid-state/telemetry-errors.jsonl` 共 37 行，36 行来自原运行，只有 03:58:01 的 `capture_error: Operation failed: errs: [Err(Timeout(5s))]` 属恢复窗；原运行的 `/v1/logs` reqwest timeout 不能误归因到新 collector。Braid `EvidenceWorker` 的错误分支会重建 collector 状态、下轮重发，但已收批次不能证明该超时前所有材料无丢失。恢复窗之后仍收到三信号批次，证明 collector 接线工作；该 5 秒超时发生于采集/force-flush 路径，不能据此断言模型请求或主执行受阻。无新增的 OTLP HTTP transport 错误记录。

两题后来都以 `generation_exit_code=1` 终止。`recovery-braid.log` 的直接原因是恢复后 Issue Agent assignment 物化触发 `UNIQUE constraint failed: assignments.member_login`，随后 Braid `local run blocked`；不是包校验或 OTLP 接线失败，也不应把启动后的几条 Pi/OTLP 记录当完成进度。旧 session 的 instruction revision mismatch 与新 session 创建已由主线确认是本次内置指令变更的预期行为。Braid assignment 修复由主线处理，本 cell 未修改该源码或运行现场。

## 来源 `.arc` 与新 runner 身份

两份 attempt-02 工作区 ZIP 各含 13 个 `template/.arc/` 条目，包括 preflight、`runner-events.jsonl`、`runtime-reporting/operations.jsonl` 和空 traceability 列表，没有 `adapter-agent-result` 等来源终态结果。现恢复入口把这些条目直接解到新 runner 的 `template/.arc`。attempt-03 GitHub 的新 `runner-events.jsonl` 前 590 行与来源 ZIP 原文件逐行相同，新 runner 只追加到 592 行；Sheet 前 654 行相同，新 runner 追加到 657 行。来源记录末尾时间分别为 03:44:26/03:44:28，新 `start_agent` 失败记录时间为 03:58:13/03:58:55。旧事件确实混入新运行的监控材料，即使本批没有旧终态 result。建议把来源 `template/.arc/` 保留在生成 run 下的 `recovery-source-arc/`，不覆盖新 runner 的 `.arc`；保留审计线索且不更改 Braid 工作状态或模型输入。本 cell 仅核对，未改恢复入口。

## attempt-04 普通 base 包

浏览器指引删除落地后，将当前本地 `pi-braid` variant、技能、scripts、lab 和 SVC 技能符号链接目标复制到 WSL `attempt-04/code/`，复用 attempt-03 已解出的 Linux runtime，由标准 `scripts/package_agent.py --variant pi-braid --runtime ... --output ...` 生成普通 base 包。未重新构建 Docker/npm/Chromium，也没有启动实验；标准 packager 仍会将轻量 OTLP Python 依赖安装进临时 stage。首次构建因独立源码快照缺少 `harness/skills/svc-*` 的目标目录失败，补入原始目标目录后按同一标准命令成功；没有修改打包器源码。

产物为 WSL `runs/e20260928-02-deepseek-direct/attempt-04/pi-braid-base.zip`，434,905,269 bytes，SHA256 `cd0f8e8ea93f21025af51caa16546d02dce22afe95cd4c9796e6cfce0fb3d058`。ZIP 中 22,943 个条目，含 `support/otlp.py`、`extensions/factory-pi-timing.ts`、`skills/agent-browser/SKILL.md`、旧 Linux Braid 等必需材料，没有 `browser-checks` 条目；`run.py` 选择 agent-browser。`attempt-04/base-provenance.json` 保存源码 HEAD、复用 runtime 来源和关键 payload 的 manifest SHA。此包只是后续 recovery 包的基础，尚未换入主线新 Braid，也未作为新实验运行。

后续 attempt-04 真实恢复在刷新 native 材料前发现旧 base ZIP 的 AppleDouble 污染：独立 code 经 macOS `tar` 传输带入 233 个 `._*` 等元数据路径，普通 base ZIP 中有 71 个，`agents/._pi-deepseek-fast` 被当作成员目录导致 `NotADirectoryError`。用户授权后，在 `package_agent.py` 增加同一 metadata 路径判定，生成 stage 和 ZIP 时过滤；`package_completed_recovery.py` 复用该判定，从已有 base 复制时跳过污染条目并从 manifest 删除。attempt-04/code 已删去 233 个传输杂项，余数 0；旧 base 与失败现场保持原样。macOS 后续传输使用 `COPYFILE_DISABLE=1 tar --no-xattrs`。新恢复包由主线使用修正后的打包器生成；本单元没有启动实验或跑 Factory 测试。

主线已复制 v3 页面到本机 runs/e20260928-02-live-observability-v3/index.html，便于人工复审；它仍是 attempt-02 已停止现场的静态剖面，不冒称实时刷新。
修复后的恢复入口已打进 DeepSeek attempt-03 两份恢复包并启动，具体身份与后续真实收据归 tasks/braid-product-reaudit/packet.md。
