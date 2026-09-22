# 官方参赛闭环与 Pi multi-agent 实验

- **Objective**：交付符合官方打包与运行契约的 Pi + Braid + SVC harness，结合官方 Competition 与本地官方 runner 自动完成既定实验，比较快速模型配方及 SVC V&V 的效果，并同时取得通过率、成本、得分和阶段耗时。
- **Guardrails**：评分仍以完整官方 benchmark 为准；设施失败不能冒充实验结果；不能为了提速把失败详情回灌同一次生成。基础设施修复与正式 score 使用不同阶段，score 开始后冻结 revision。
- **Verification**：批次自动记录 qualification、排队、生成、artifact-ready、冻结、评测与恢复时间；下一轮可从终态数据计算墙钟、worker 利用率、重复采样次数和主 Agent 介入次数。
- **Current Truth**：实现阶段已完成主要接线，三模型接口、真实vision/executor与修复后的实际包双浏览器/隔离边界通过。proc与NSS缺陷已修复。真实Braid首次context replacement暴露包缺少ps/kill；新候选5bee93dd已通过无overlay工具、双浏览器与Linux边界；实际Braid复验在首次reset发现共享进程终态判定错误：已退出Z态writer被kill-0误判为存活，该Braid兜底修复已撤回，转为删除越界生命周期接线。官方本地镜像仍缺失。进度与责任见 [task-map](task-map.md)，资格证据见 [integration cell](cells/integration.md)。此前一轮 08:54–17:13 共 8h19m。健康的两路前四项只用了约 80 分钟；官方评测每项约 3–5 分钟。主要损耗来自资格验证过晚、application artifact 与 finalization 失败耦合、失败后重复模型采样，以及主 Agent 同时承担 scheduler、日志压缩和恢复。详见 [profile](profile-2026-09-22.md)。产品边界已收敛为一个Factory task对应一个根Issue；运行时Agent只使用GitHub式assignee，内部agent-profile与variant均由Harness隐藏。粗筛组合见[能力装配设计](recipes.md)。
- **Next Step**：新方向获准推进到具体方案与预演；[Pi边界修正cell](cells/pi-boundary.md)记录删除面、正常Pi关闭、最快真实验证与实施分工。用户进一步明确删除全部自建沙箱（含开发机），已纳入同一cell；用户已确认调整后的范围并授权实施；先提交任务基线，然后删除越界接线和所有自建沙箱，直接真实验证。三层无模型spike不再作为必经关卡，模型额度不是主要约束。

## Proposed loop

1. **Qualify**：沿实际变更验证 Pi 协作、模型/视觉接口与官方 ZIP 入口；复用已有恢复检查。Codex 退出活动 variant 后不作为本轮资格门槛，不每轮重跑无关矩阵。
2. **Freeze**：资格通过后冻结 Braid、SVC、runner、profiles 和 benchmark revision。正式 score 期间不滚动换源码。
3. **Score**：官方 Competition 与本地官方 runner 混合调度；脚本负责提交、任务启动、队列、终态与产物获取。官网容量不足时在本地运行独立实验，保留运行环境标签，不把本地评分称作正式线上成绩；两处使用同一冻结 ZIP，模型总并发仍受 Meter 约束。
4. **Recover**：保留 work-item、会话和应用检查点；已完成的生成不因辅助分析或导出失败而从头采样。普通 commit 不等于应用完成，人工导出的评分也不能冒充正常平台交付成功。具体恢复能力须符合官方入口契约。
5. **Report**：设施只在终态或系统性故障唤醒主 Agent，并输出 `{item, phase, since, error-class, artifact}`。原始日志按需交低成本子 Agent 压缩。既定评分齐全后汇总并停止。

矩阵大小由实验问题决定，不以缩小矩阵作为主要提速手段。本轮改善 user-scope AGENTS.md/user instructions 的 SVC 导航和关键行为；现有 canonical V&V 已覆盖批准的方法，本轮不改 Corpus 正文。现有 preset 只是一对一转抄 profiles/defaults 的空壳，本轮设计删除该层，由 variant 直接组合内部配置和方法。先前 2.5–3.5h 是基于本地健康段的粗估，不能作为官网排队条件下的承诺；profiling 中“60%/约5h”也不是精确测得的可消除时间。
