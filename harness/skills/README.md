# 固定技能材料

这些文件是实验运行时材料，不是本仓库开发 Agent 的额外工作指令。来源版本归 `../dependencies.lock.json`；上游许可随技能保存。适配内容由 Factory 固定，四组不在运行期间更新。

| 技能 | 取用内容与适配 |
| --- | --- |
| frontend-design | Anthropic 的视觉选择、层级、文字与自检原则；去除虚构客户背景、等待客户确认、强制新颖性和固定设计轮次，给定需求与参考图优先。 |
| impeccable | pbakaus 的 craft-floor：层级、间距、真实内容、状态、可读性和界面反馈；不接入 launcher、hooks、菜单、强制产物或脱离 brief 的样式禁令。 |
| diagnosing-bugs | Matt Pocock 的症状反馈循环、最小复现、可区分假设与根因修复；移除硬性红测前置、固定假设数量、人工确认和每次永久回归测试要求。 |
| ponytail | 4.10.0 的复用顺序与复杂度判断；仅作用于技术实施，不削减授权要求，不替代 SVC 工作流程，也不强制回答格式。 |
| agent-browser | Factory 的薄操作导航；完整指令由固定版本 CLI 的 `skills get core` 提供，避免复制另一份过时操作手册。 |
