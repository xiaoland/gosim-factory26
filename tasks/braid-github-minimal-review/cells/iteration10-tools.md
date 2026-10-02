# 迭代 10：工具耗时缺口与本地实验设施

2026-09-28 只读核对既有诊断、当前源码和 WSL 资源；未启动模型实验、Factory/设施/Corpus 测试，未碰冻结 run。新改动仅是 `harness/skills/agent-browser/SKILL.md` 的两句操作指引。工作区有其他任务改动，本页不把它们归为本次交付。

## 已知耗时根因的处置

| 证据和根因 | 当前可执行路径 | 结论 |
| --- | --- | --- |
| Sheet 用 `cp -al` 把依赖从持久工作区搬到 `/tmp`，跨设备产生 4,499 行 `Invalid cross-device link`；见 [token 取证](../../braid-product-reaudit/cells/token-deep-03.md)。 | `agent-browser` 现有检查指引补充：先用运行时给的路径，跨设备依赖复制改普通 copy/install，首个错误留日志、只回传短摘要。 | 操作根因有明确替代；未观察新 Agent 实际采用，不报节省分钟。没有添加缓存或复制框架。 |
| Sheet PR 检查曾猜错 Chromium 路径；GitHub 手动检查漏 `BASE_URL`，两者均在配置/启动阶段失败。 | `variants/pi-braid/run.py` 已把 `BROWSER_EXECUTABLE_PATH` 与 `AGENT_BROWSER_EXECUTABLE_PATH` 设为 `browser_executable(runtime)`；skill 现在要求先验证所给路径可执行。应用自身 runner 仍须提供其声明的 `BASE_URL` 等变量。 | 不再派生另一个浏览器路径发现器；未修改生成应用。 |
| Sheet 为查 blocked，将几乎整个旧 `braid status --json` 打印给模型，含 `physical_sessions`，约 427KB 原输出；见同上。 | 当前 `sources/braid/src/cli/mod.rs` 已按 `BRAID_AGENT_RUNTIME=1` 把 Agent 的 `status --json` 限为 items 的 `kind/id/title/state/assignees`；宿主诊断仍保留全量。宿主需要少数字段时再用 `jq` 投影，WSL 已有该工具。 | 当前源码已修 Agent 的大回显根因，旧运行未采用；待新包自然观察。无需新增字段选择接口。 |
| PR #23 首轮全套 18.7 分钟只留通过摘要，因缺真实 shell exit 在同 tree 重跑 17.2 分钟；见 [成本链](../../braid-product-reaudit/cells/runtime-cost-followup.md)。 | `agent-browser/scripts/with-service.py` 已支持 `--check-only` 包装应用自管 runner，持久保存 `check_exit`、检查命令、候选与环境说明、日志和清理状态；单服务模式仍在。先前 [真实生成应用副本验证](svc-cli-integration.md) 覆盖正常、失败、未启动、中断及邻居服务。 | 工具实现已存在，待打入新 Linux 包和自然运行采用；SIGKILL/宿主崩溃不能保证最终收据。没有重跑这些已完成验证。 |

`SVC dev` 需要应用声明 `svc.json` 和持久服务目标，不能替代一次性检查回执；沿用已实现的 helper。应用自有多服务脚本仍负责就绪、数据和断言，外层只收其进程组。首次收据须连同候选、检查源码、数据和环境交接；同 Git tree 不能单独证明结果等价。

## Collector 与原生取证

[08 真实 Collector 取证](../../experiment-infrastructure/cells/hotfix09-collector-evidence.md) 确认旧 `EvidenceWorker` 在 capture/flush 失败时重建 collector，清空已发 ID 集合，错误前后有相同 `record_id` 再发。当前 `sources/braid/src/telemetry.rs` 已保留同一 collector：自动 64 条和轮末 flush 成功后调用 `flush_succeeded()`，失败调用 `retry_since_flush()`；`sources/braid/src/evidence.rs` 只重试自上次成功 flush 以来的 ID。该 cell 记载的针对性 Rust 检查已通过；本次不再改 telemetry，也未重复测试或部署。SDK 的 5 秒 `force_flush` 回执超时可能发生在后台导出仍完成时，有界队列也可能在满时丢日志；成功 flush 不等于逐条持久化确认。新运行要保留 `telemetry-errors.jsonl` 与 Collector timing/SQLite 原始批次，记录错误窗口的 `record_id` 重复与证据缺口，不能简单吞错误或宣称无损。

下一实验收集子代理真实调用的最小入口是生成 run 的 `native/manifest.json` 与其中列明的原始 Pi JSONL；运行中则在对应 `.factory26/<braid-run>/work/native-homes/`，另看 Pi 的 `sessions/` 子会话文件及 `session-tree.json` 关联。`scripts/core.py::archive_sessions` 按身份复制这些原文件并保留摘要和诊断状态；`variants/pi-braid/run.py` 同时保留 `pi-timing.jsonl`，Braid evidence 向 `telemetry.sqlite` 写原始 OTLP 批次。WSL 冻结 Sheet 原始根目录只做结构计数：11127 条 assistant `toolCall` 含 `name/arguments/id`，11112 条 `toolResult` 含 `toolCallId/toolName/content/details/isError`，11127 条 usage 含 `input/output/cacheRead/reasoning` 等字段；未输出参数或正文。这证明原生文件能直接核对调用参数、结果和用量，不能仅凭 OTLP 聚合或 timing 猜工具行为。子会话是否齐全以 manifest 的 `diagnostic_status`、身份链和原始文件核对；`token-final-review.md` 的 Sheet vision 子会话说明不能只数顶层文件。

## 新本地实验前的 WSL 核对

通过既有 `ssh wsl.win-ws.localhost` 只读检查 `/home/yyh/Development/factory26`。WSL 有 12 个逻辑 CPU、15 GiB RAM（检查时约 12 GiB available）、4 GiB swap（约 2.2 GiB free）、根卷约 102 GiB available；Docker 26.1.5 正常，`arcbench-local-submit:latest` 镜像、原生 Runner `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner`、双题 `platform-inputs/hackathon/{github,sheet}` 和原需求 ZIP 都在。Docker bridge gateway 为 `172.17.0.1`。旧 Pi runtime 有 `bin/chromium`，Codex runtime 有 `bin/litellm`；系统 Python 3.12.14。4018 端口正监听，新网关须另选空闲端口。

WSL `.secrets/models.env` 权限为 `600`，仅确认存在 `DEEPSEEK_API_KEY`/`DEEPSEEK_BASE_URL`、`GLM_API_KEY`/`GLM_BASE_URL`、`KIMI_API_KEY`/`KIMI_BASE_URL`，未输出值或发模型请求。当前 `scripts/hackathon_gateway.py` 为 `deepseek-v4-flash`、vision、`glm-5.3-flash`、`kimi-k3`、`kimi-k2.7-code` 生成各自 `openai/<model>` LiteLLM 路由，从对应供应商环境名取地址和密钥；新实例的 `--preserve-parameters` 可保留现有客户端参数。路由和 key 存在不等于模型推理/额度已验证。运行中旧 4018 网关的实际启动参数不从当前文件推断。

**同步边界：** WSL 仓库的 `harness/npm/package-lock.json` SHA256 为 `e40ef772…`，本工作区为 `960494ef…`；WSL 的旧 runtime 与当前迭代 10 源码并不等价。新包必须从本次已确认的源码、lock 与 Braid revision 在 WSL 重建，不能直接复用旧 ZIP 或旧 runtime 来宣称验收。同步、构建和新运行由主实验工作项在统一冻结时执行；本页只提供入口。

## 现成入口与监控边界

下列命令在**同步后的 WSL 仓库根**使用，每个输出为全新路径；`<...>` 须替换为本次登记的真实冻结路径，运行前先核对端口和配方。这里只列启动入口，未执行：

```sh
python3 scripts/runtime.py linux --backend pi --braid-source sources/braid --output <new-pi-runtime>
python3 scripts/package_agent.py --variant pi-braid --runtime <new-pi-runtime> --output <new-agent.zip>
python3 scripts/hackathon_gateway.py --python /home/yyh/.local/bin/python3.12 --runtime /home/yyh/Development/factory26-official-local/hackathon-runtime-codex --state <new-gateway-state> --port <free-port> --preserve-parameters
python3 -m lab.arc_bench.arc_matrix --candidate iteration10=<new-agent.zip> --case hackathon/github --case hackathon/sheet --requirements-only --inputs-root /home/yyh/Development/factory26-official-local/platform-inputs --runner /home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner --image arcbench-local-submit:latest --gateway-state <new-gateway-state> --container-otlp-host 172.17.0.1 --workers 2 --output <new-manifest.json>
python3 -m lab run <new-manifest.json> --experiment-root <new-experiment-directory> --background
python3 -m lab show <new-experiment-directory>
```

`--requirements-only` 只生成与部署，不给本地官方分数；每题完成后用 `python3 -m lab.arc_bench.package_arc_replay --run <that-run-directory> --output <new-single-task-replay.zip>` 冻结应用，再按既定 `self_funded` 官网路径单题评分，生成和评分耗时分开记录。

旧 `attempt-09/continuation-03/monitor-generation.py` 已按每个 run 的 `started_at` 在前 600 秒每 180 秒、随后每 480 秒采集，并把原始摘要写 `generation-monitor.jsonl`；`agents/run-monitor.md` 定义内容审查与完成条件。这个脚本固定 `ROOT=自身目录/generation/runs` 与两题名，不是可直接指向任意新实验的通用 CLI。新实验应在其独立目录复用该已验证节奏与 `lab show/status/events` 读取，绑定本次 run 身份；不能拿旧 monitor 的 PID、旧结果或只看 token 增长冒充新运行监控。长等待交程序，异常或终态再给审查 Agent 真实证据。新监控接线仍须在主实验工作项冻结前确认。
