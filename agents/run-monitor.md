# 消费已保存的运行监控

这是开发侧监控消费者的入口，不注入参赛 Agent，也不启动新的运行或采集器。当前采集由冻结的 Lab controller/runner/Hosted adapter 保存状态、原始错误、告警和终态；旧 operation 的 `hosted_monitor.py`、`local_monitor.py` 只按原冻结协议解释，不作为所有 run 的统一入口。

从所属 packet 确定实际实验及已授权监控范围，再消费 `python3 -m lab monitor EXPERIMENT --json` 或已保存摘要、告警和终态回执。普通进展或状态未变不重复通知；不要重复浏览官网、下载包、另起 collector，或自动暂停、恢复、重试和修改源码。

默认消费者模型与间隔以 [AGENTS.md 的实验边界](../AGENTS.md#实验边界)为准；本轮明确的覆盖决定仍查所属 packet，不沿用 2026-10-01 的“禁用所有模型监控”旧结论。采集者和摘要消费者是不同责任，脚本采集不等于无需处理告警。

告警先核对 producer 身份、来源时点、实际 provider 生命周期及连续观测，区分停滞、观察失联和未知；token 增长不证明语义进展。确定终态或需要决定的故障返回完成/注意消息，保留具体错误和证据入口。停止及恢复判断见 [运行门控](../docs/deployment/recovery.md#当前-checkpointprepare-与停止门控)。
