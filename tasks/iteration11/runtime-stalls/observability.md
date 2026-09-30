# I11 本地生成停滞信号

2026-09-30。用户直接要求修复过去两次 I11 长时间停滞的观测缺口；本文件记录开发侧只读监控改动。没有改参赛应用、Pi/Braid 生命周期、模型、凭据、活跃 run 或评分。

## 事实与缺口

GitHub 最新接续 `pi-braid-i11--hackathon--github-5c52a331ef0d5c` 的外层 `run.json.phase=running`，Braid `local_run.lifecycle=running`，因此容器与 controller 存活被显示为仍在运行。当前 WSL 的 Braid SQLite 只读快照却有 0 个 starting/running turn、11 个 pending event；三个 OPEN 工作项 root #1、Issue #10、PR #22 的现行 active assignment agent 全为 blocked，`context_error` 和最新 reset error 均为 `session is unavailable`。该 run 的 `recovery-braid.log` 保存原错 `Pi new_session RPC failed: provider request pi_rpc timed out`；三个新 physical 都没有 native identity。`blocked_groups=5` 包含历史 CLOSED 工作项，不能据此称五个现行负责人失败。旧 GitHub `f402061b5bc88f` 与 Sheet `db75cf2c3b82be` 的七小时停滞及同类超时见 [本地恢复观察](../recovery-curation/local-observation.md) 和本目录 [GitHub](github.md)、[Sheet](sheet.md) 审查。Sheet 一致停止现场 `source/template.tar` 的 DB 另证：OPEN root #1 与 PR #13 blocked，Issue #4 idle，0 active turn、49 pending event；所以不能只在所有 OPEN 负责人均 blocked 时报警。

观测消费链是 `lab.analysis.factory show` → `lab.analysis.inspect_runs` → `lab.arc_bench.results`。此前只消费 Runner/外层终态；`lab.status` 有意保持实验格式中立，不能从 `running` 推导 Braid 进展。另一个独立接线缺口是当前 WSL `github/prepared/launch.py` 仅调用 `lab run ... --background`，没有启动 monitor；本次 attempt 没有 `monitor-generation.py` 或 `generation-monitor.jsonl`，进程表也没有该监控。旧 `runs/e20260928-01-flash-team/monitor-generation.py` 和 I10 专属脚本不监视此 run。容器继续存活七小时不会触发 lab 的终态通知。

## 改动与判据

在已有 ARC 本地结果摘要加入 `runtime_blocker`，并由 `factory show` 展示。外层 phase 为 running、当前 Braid DB 唯一且 `local_run.lifecycle=running` 时，从 SQLite `mode=ro` 同一事务列出现行 OPEN 工作项的 active assignment。只要其中有人 blocked 且有 Context 错误，就显示其工作项与原错；若仍有 active turn，标为 `partial`，不停止观察。没有 active turn 且根负责人 blocked，或所有 OPEN 负责人均 blocked，才升为 `blocked`，让 watch 退出报告。根身份采用 Braid 自身的 `issue:1` node ID 契约（`sources/braid/src/store/mod.rs` 的根关闭检查），不猜标题。pending event 数一并展示，**不作为报警前提**，以免所有事件已被阻断时漏报。输出 Context/reset 原错、DB 证据路径，并从本轮更新过的 `recovery-braid.log` 或 `braid.log` 的有界末尾附上原始 Pi provider 错误。日志原错用于诊断，不是触发判据；兼容 `Pi startup handshake failed`、`Pi get_state failed while resuming` 等新文案。信号独立于生成、部署、评测状态，不写 `run.json`，不取消、不重建、不重试、不把基础设施故障计零分。

同一个 `factory` CLI 增加 `watch --run <run目录>`：立即输出一次 JSONL 快照；按该 run 启动后前十分钟每 180 秒、之后每 480 秒再读。出现 `blocked` 时输出原始证据并以退出码 2 结束；`partial` 继续观察，外层终态以 0 结束。它只读摘要、SQLite 与最多 64 KiB provider 日志，不打包或复制完整工作区。运行部署方需要在 `lab run --background` 后启动此入口并接收其退出和 stdout；启动动作不属于此次源码变更，实际部署回执见本文件末尾。可以复用以下命令，将路径换成同次新 run；运行环境须含这次更新的 `lab` 源码：

```sh
PYTHONPATH=/home/yyh/Development/factory26/runs/iteration11/runtime-stalls/observer \
python3 -m lab.analysis.factory watch --run /home/yyh/Development/factory26/runs/iteration11/runtime-stalls/github/generation/runs/pi-braid-i11--hackathon--github-0d0cb6e9982fc1
```

## 验收与限制

`python3 -m py_compile` 三个改动模块和 `git diff --check` 通过。将改动源码放在 WSL `/tmp/f26-i11-observer` 隔离目录后，针对**真实、运行中的**上述 GitHub run 执行只读 `factory show --json`：返回外层 `running`、生成 `generating`，同时明确 `runtime_blocker.status=blocked`、0 active turn、11 pending event，列出三个 OPEN 负责人及原始 `pi_rpc timed out`。同一 run 的 `factory watch` 首次采样输出同一阻断并退出 2。当前 Sheet 新接续 run `396538bc0dda96` 有 5 active turn、无 blocked 负责人，`factory show` 未发阻断；旧 Sheet 一致停止 DB 的 root/PR #13/Issue #4 组合经只读 SQL 核对，满足新根受阻判据。没有运行 Factory/Braid/设施测试、模拟探针或新模型。该只读核验阶段未启动新 run 的 watch；随后部署阶段已接线，回执见末尾。只凭旧 run 的 `running` 或历史 blocked 数不能宣称生成恢复。

### 原位接续的证据路径修正

后续 GitHub 原位接续 `pi-braid-i11--hackathon--github-0d0cb6e9982fc1` 的新 `workspace/` 不含 `official-generation/`；`generation.resource.json.workspace` 明确指向旧 `5c52a331ef0d5c` 的保留工作区。初版 observer 因只查新 workspace 而返回空信号。现在只在本地生成目录缺失时读取该资源记录，并交叉核对 resource 的 `source_run_id`、新 run labels 的 `source_run_id`/`retained_generation` 及来源 run.json 的身份；不扫描任意旧目录。DB/WAL 须在**本次** `started_at` 后写过，才解释受阻状态，避免把继承的旧 blocked 快照误报成新尝试失败。外部证据使用绝对路径作为 evidence key。provider 原错从本次时间戳的 `continuation-*-braid.log`，或本次更新的 `recovery-braid.log`/`braid.log` 读取，旧 `phase_log=braid.log` 不冒充本轮日志。

更新后的完整 observer 已同步到 WSL `runs/iteration11/runtime-stalls/observer/`。对真实新 run 只读 `factory show --json` 返回 `runtime_blocker.status=clear`、3 active turn、7 pending event、无受阻负责人；DB source 指向 resource 宣告的保留工作区，resource evidence 指向新 run，warnings 为空。这证实本轮工作正在推进，不能因保留路径上存在上一轮失败而提前报警。恢复负责人已收到仅重启 watch 的通知；未操作模型或活跃 run。

主线已将完整 observer 源码持久化到上述 PYTHONPATH，并在实际恢复部署中接续该 watch；具体 PID/终态以 runtime-stalls 的部署回执为准。

2026-09-30 10:03 CST 实际部署：GitHub watcher PID1698832，Sheet PID1698834，首条分别2/1 active turn、6/21 pending event，无blocked owner。输出保存到 WSL `runs/iteration11/runtime-stalls/watches/{github,sheet}/watch.jsonl`，退出码另存。监控已挂到实际保留DB，不再以返回空信号当成健康。跨会话自动唤醒仍未验证。
