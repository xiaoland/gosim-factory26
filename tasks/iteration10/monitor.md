# 迭代 10 本地生成监控

监控脚本为 [scripts/monitor-generation.py](scripts/monitor-generation.py)。它只读 `generation/runs/*/run.json`、lab 控制器通知、内层 Braid `run.json` / SQLite / `sessions.json` 索引的原生 JSONL，以及 gateway `request-metadata.jsonl`。全新生成以内层 Braid 启动时间属于本次 lab run 为证，读取 `braid.log`；恢复则要求当前 lab 尝试自己的 stdout 或 execution.debug.log 指向确切恢复日志，并验证日志起点落在本次启动与结束之间。旧快照只有继承状态时不读 native。共享状态在本次结束后又被写入时标记 `later_shared_state`，native 只统计本次起止之间的消息。

每次将完整错误与增量原文、文件路径、行号或字节偏移写入独立 JSONL。外层失败/终态输出一次摘要并退出（失败码 1）；当前可执行原生会话连续至少两条 assistant 错误且未在该会话恢复时，输出一次 `attention` 摘要并退出码 2，保留 run 的原始 `running`，不取消或判 benchmark 失败。两题尚未建立时继续等待，静止本身不判失败。任一题启动后的前 600 秒间隔 180 秒，其后间隔 480 秒。

实际 WSL 旧运行只读采样（没有启动控制器、模型或设施测试）：

| 原始记录 | 判别结果 |
| --- | --- |
| `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-02/iteration10-monitor-fresh-generation.jsonl` | 两题均识别 `fresh_generation`，从各自 `braid.log` 与 native 索引取证；无恢复日志。 |
| `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-03/iteration10-monitor-inherited-snapshot.jsonl` | 两题均识别 `inherited_snapshot`，不把快照里的旧 native 错误算作本轮。 |
| `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/iteration10-monitor-cold-recovery.jsonl` | 两题均从本次 `execution.debug.log` 确认 `recovery-braid.log`；旧 Sheet 实录 22 条连续 429/余额错误。此 run 已取消，故输出失败终态，不另发 attention。 |
| `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/iteration10-monitor-boundary.jsonl` | 两题从本次 stdout 确认各自 `continuation-<本次启动时间>-braid.log`。GitHub `finished/completed`；Sheet `cancelled`，native `Connection error.` 与 gateway `CancelledError` 后都有成功。Sheet 的共享库又被后续接续写入，统计来源标记 `later_shared_state`，本次 native 截止取消时间。 |

旧运行的连续错误来自已保存的真实原生 JSONL；历史终态无法替代新运行中 `attention` 的现场触发验收。旧运行状态不代表迭代 10 结果。

新实验启动后，在已同步本脚本的 WSL 仓库运行：

```sh
python3 /home/yyh/Development/factory26/tasks/iteration10/scripts/monitor-generation.py \
  --root /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation \
  --gateway-log /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/gateway/request-metadata.jsonl \
  --out /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation-monitor.jsonl
```

截至准备时，WSL 中 `e20260928-03-check-receipts/generation/runs` 尚不存在，本脚本也尚未同步至 WSL 工作副本；因此新实验监控未启动。监控不取消运行、不换模型、不修改生成应用。
