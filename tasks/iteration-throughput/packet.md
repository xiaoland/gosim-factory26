# 官方参赛闭环与 Pi multi-agent 实验

- **Objective**：交付符合官方打包与运行契约的 Pi + Braid + SVC harness，结合官方 Competition 与本地官方 runner 自动完成既定实验，比较快速模型配方及 SVC V&V 的效果，并同时取得通过率、成本、得分和阶段耗时。
- **Guardrails**：评分仍以完整官方 benchmark 为准；设施失败不能冒充实验结果；不能为了提速把失败详情回灌同一次生成。基础设施修复与正式 score 使用不同阶段，score 开始后冻结 revision。
- **Verification**：批次自动记录 qualification、排队、生成、artifact-ready、冻结、评测与恢复时间；下一轮可从终态数据计算墙钟、worker 利用率、重复采样次数和主 Agent 介入次数。
- **Current Truth**：按用户批准的新方向，Braid 已删除 Pi 内部子代理控制与自造 teardown 协议，改为关闭所持有的 Pi RPC stdin 并等待主进程退出（`sources/braid`：`fdb5c19`，29 单元与 1 CLI 检查通过）。Factory 已删除全部自建沙箱，扩展仅被动收集会话关联，诊断缺失不阻断有效交付；124 Python 检查与 Node observer 检查通过。SVC 接线和四个快速模型 variant 保持本轮范围。尚未取得本轮完整 benchmark 分数。官方 Competition 已接收 mixed 包（submission `f9d8960d81a5`），Keep run `007b8fc9d38b`已进入平台 Agent 运行阶段。旧资格与失败证据保留在 [integration cell](cells/integration.md)，当前批准边界见 [pi-boundary cell](cells/pi-boundary.md)。
- **Next Step**：短真实模型旅程完成，已有交付复验通过；四个参赛包已冻结，官方 Competition 控制器正在运行，先 mixed 的 Keep/BookStack，再其余既定组合。状态与证据目录为 `runs/competition/iteration-throughput-boundary-20260923/`。官网尚无评分结果。本地 production 镜像仍缺失，但正核查能否用现有官方ARC评测器、相同冻结ZIP与明确环境标签完成并行本地评分，不再默认要求复制整个生产环境。

## Proposed loop

1. **Qualify**：沿实际变更验证 Pi 协作、模型/视觉接口与官方 ZIP 入口；复用已有恢复检查。Codex 退出活动 variant 后不作为本轮资格门槛，不每轮重跑无关矩阵。
2. **Freeze**：资格通过后冻结 Braid、SVC、runner、profiles 和 benchmark revision。正式 score 期间不滚动换源码。
3. **Score**：官方 Competition 与本地官方 runner 混合调度；脚本负责提交、任务启动、队列、终态与产物获取。官网容量不足时在本地运行独立实验，保留运行环境标签，不把本地评分称作正式线上成绩；两处使用同一冻结 ZIP，模型总并发仍受 Meter 约束。
4. **Recover**：保留 work-item、会话和应用检查点；已完成的生成不因辅助分析或导出失败而从头采样。普通 commit 不等于应用完成，人工导出的评分也不能冒充正常平台交付成功。具体恢复能力须符合官方入口契约。
5. **Report**：设施只在终态或系统性故障唤醒主 Agent，并输出 `{item, phase, since, error-class, artifact}`。原始日志按需交低成本子 Agent 压缩。既定评分齐全后汇总并停止。

矩阵大小由实验问题决定，不以缩小矩阵作为主要提速手段。本轮改善 user-scope AGENTS.md/user instructions 的 SVC 导航和关键行为；现有 canonical V&V 已覆盖批准的方法，本轮不改 Corpus 正文。现有 preset 只是一对一转抄 profiles/defaults 的空壳，本轮设计删除该层，由 variant 直接组合内部配置和方法。先前 2.5–3.5h 是基于本地健康段的粗估，不能作为官网排队条件下的承诺；profiling 中“60%/约5h”也不是精确测得的可消除时间。
