# 官方参赛闭环与 Pi multi-agent 实验

- **Objective**：交付符合官方打包与运行契约的 Pi + Braid + SVC harness，结合官方 Competition 与本地官方 runner 自动完成既定实验，比较快速模型配方及 SVC V&V 的效果，并同时取得通过率、成本、得分和阶段耗时。
- **Guardrails**：评分仍以完整官方 benchmark 为准；设施失败不能冒充实验结果；不能为了提速把失败详情回灌同一次生成。基础设施修复与正式 score 使用不同阶段，score 开始后冻结 revision。
- **Verification**：批次自动记录 qualification、排队、生成、artifact-ready、冻结、评测与恢复时间；下一轮可从终态数据计算墙钟、worker 利用率、重复采样次数和主 Agent 介入次数。
- **Current Truth**：Braid 已删除 Pi 内部子代理控制与自造 teardown 协议（`sources/braid`：`fdb5c19`）；Factory 已删除自建沙箱，SVC 接线和四个快速模型 variant 保持本轮范围。官网 mixed 包已完成 Keep 23/32、BookStack 13/34；官网 DeepSeek 包已完成 Keep 32/32、BookStack 27/34；官网 GLM/Keep 已完成 23/32，GLM/BookStack run `23cf3569040f` 截至 13:00 仍为 RUNNING、未交付应用。双比赛矩阵已接管 Lite journal 的所有权；旧 Lite-only 控制器 PID 35711 在移交时停止。我曾因未看到新矩阵而短暂恢复旧控制器，并在确认双比赛屏障后于 13:17 停止其后台 PID 36621；远端 run 未取消，也未新建任务。双比赛矩阵当前因 Web 端 HTTP 500 保留原状态，见[双比赛 packet](../dual-bench-hosted/packet.md)。Codex 线程 heartbeat `factory26-lite` 每小时检查平台恢复与矩阵终态，不启动旧 Lite-only 控制器。平台 `FAILED` 仅表示未全通过，不等于生成/评分中断。旧资格证据在 [integration cell](cells/integration.md)，当前批准边界在 [pi-boundary cell](cells/pi-boundary.md)。
- **Next Step**：四个参赛包仍冻结。官网控制器按矩阵继续 GLM、V&V；官网证据目录为 `runs/competition/iteration-throughput-boundary-20260923/`。WSL 本地 GLM/BookStack 8/34、V&V/BookStack 15/34、GLM/Keep DNS 修复重跑 6/32 均是旧公开 benchmark 的模拟评分；DeepSeek/Keep 和旧 GLM/Keep、V&V/BookStack 的既有本地生成因连续模型连接错误未交付、不计分。WSL DNS 指向无响应的 `172.29.144.1` 已确认并临时改用公共 DNS；GLM/Keep 重跑曾在交付确认处中断，随后沿同一 run 完成交付及 32 项评测，无 DNS/模型错误。证据见[环境 cell](cells/environment.md)及[V&V 中断 cell](cells/vv-local-failure.md)。同一 DeepSeek/BookStack 应用在新版 `ddc7e40` 测试中稳定复现官网 27/34；mixed/BookStack 官网 13/34、本地新版 30/34 仍未对齐，详见[校准 cell](cells/local-parity.md)和[诊断 cell](cells/score-diagnosis.md)。

## Proposed loop

1. **Qualify**：沿实际变更验证 Pi 协作、模型/视觉接口与官方 ZIP 入口；复用已有恢复检查。Codex 退出活动 variant 后不作为本轮资格门槛，不每轮重跑无关矩阵。
2. **Freeze**：资格通过后冻结 Braid、SVC、runner、profiles 和 benchmark revision。正式 score 期间不滚动换源码。
3. **Score**：官方 Competition 与本地官方 runner 混合调度；脚本负责提交、任务启动、队列、终态与产物获取。官网容量不足时在本地运行独立实验，保留运行环境标签，不把本地评分称作正式线上成绩；两处使用同一冻结 ZIP，模型总并发仍受 Meter 约束。
4. **Recover**：保留 work-item、会话和应用检查点；已完成的生成不因辅助分析或导出失败而从头采样。普通 commit 不等于应用完成，人工导出的评分也不能冒充正常平台交付成功。具体恢复能力须符合官方入口契约。
5. **Report**：设施只在终态或系统性故障唤醒主 Agent，并输出 `{item, phase, since, error-class, artifact}`。原始日志按需交低成本子 Agent 压缩。既定评分齐全后汇总并停止。

矩阵大小由实验问题决定，不以缩小矩阵作为主要提速手段。本轮改善 user-scope AGENTS.md/user instructions 的 SVC 导航和关键行为；现有 canonical V&V 已覆盖批准的方法，本轮不改 Corpus 正文。现有 preset 只是一对一转抄 profiles/defaults 的空壳，本轮设计删除该层，由 variant 直接组合内部配置和方法。先前 2.5–3.5h 是基于本地健康段的粗估，不能作为官网排队条件下的承诺；profiling 中“60%/约5h”也不是精确测得的可消除时间。

本轮收尾的[诊断约束清理](cells/diagnostic-friction.md)与[开发过程复盘](cells/retrospective.md)分别记录已修改的设施行为和下一轮可验证的工作方式。[两轮得分诊断](cells/score-diagnosis.md)以每个 task run 的测试现场说明得分原因；[本地与官网评分校准](cells/local-parity.md)追踪同应用、同测试、同运行状态的环境对齐，不把开发耗时或跨 variant 分差当作评分归因。
