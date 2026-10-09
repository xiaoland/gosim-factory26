# I14 组合版接入 FrontierHarness v1：可行性调查

2026-10-05。用户原话：“看看可不可以拿 i14 组合版参加一下 frontier harness v1 ?” 本次授权为可行性调查和方案整理；没有修改源码、安装工具、创建远端运行、调用模型或提交结果。

结论：可以基于 `pi-braid-i14-reviewer-cleaner-e2e` 接入第三方评测，当前 Web 生成包不能原样运行。FrontierHarness v1 公开 30 题，由 21 道 Terminal-Bench 和 9 道 DeepSWE 组成，分别经 Harbor/Pier 执行，支持注册自定义 agent。公开材料提供复现和报告流程；本次未确认官方收录新候选的审核或提交机制。

## 必须适配的行为

`variants/pi-braid-i14-reviewer-cleaner-e2e/run.py:201` 新建空应用目录，`:226` 仅复制需求，`:445` 初始化新 Git 仓库；profile workspace 固定为这个应用目录（`:84-86`）。根任务限定 ARC/Web（`:251-254`），CLI 只接受 web（`:568-578`）。最终提交从 main 导出到独立输出目录（`:480-487`），而 `scripts/agent_support.py:702-726` 强制 frontend build/backend start 并复制应用。这些行为无法满足既有仓库修复或原任务文件系统交付。

建议增加评测入口，复用 Braid/Pi、reviewer、cleaner、e2e 和现有 session 预算保护，接收允许的任务指令与任务环境；按两套执行器的真实接口分别完成工作目录接入、集成结果回写、终态和证据交付，不复用 Web 包校验。非 Git 终端题的文件系统与 Braid worktree 关系仍须在实施准备核实。所有子角色和 cleaner/e2e 调用计入 token、缓存与费用；单一根 session 的 usage 不代表组合总消耗。评测器和隐藏答案不进入生成 Agent 的上下文。

## 建议实验与比较口径

第一轮保留当前混合模型配方，冻结确切代码、材料和角色路由，串行执行一题 Terminal-Bench 和一题 DeepSWE。接入验收要求实际执行、官方 verifier 的有效结果、完整来源及消耗证据；题目失败可以是有效结果，设施故障不能记成能力失败。两题不用于估计总体通过率。接入结果汇报后再由用户决定 30 题范围与预算。

公开基线统一 Kimi K3。混合模型评测回答 I14 系统实际效果，不能将与公开基线的差异单独归因于 Harness。若目标为同模型比较，所有成员、reviewer、cleaner/e2e 和原生子角色都需明确绑定 K3；`MODEL=` 不足以完成替换。当前仓库限制 K3 等列举模型合计每次 Factory run 只供一个 Braid session 使用，而 root 与 reviewer 各开 session，全 K3 路线需要用户明确调整本轮限制，不能私自缩掉 reviewer 或移除预算保护。

最新官方流程因历史基线网络 allowlist 未记录，令新结果默认不可比且不参与排名，即使同模型覆盖全部 30 题也不自动获得排行资格。比较 Harness 时应在相同模型供应商、资源、网络、任务与冷启动合同下另做原生 Pi 对照，并保留环境差异声明。官方支持 custom provider；现有国内通道是否满足 Runta/Pier 代理与网络合同尚未验证。

## 运行前提与下一步

本机 PATH 未找到 `runta`；jq 和 Node 可用。Runta 账户认证、额度、实际远端资源及模型受理能力未核实。本仓当前 HEAD 为 `5e96bdd6e43bfdcd80abcb2d8ca7c303ce5fe108`，大量 I14/设施修改尚在工作区，不能把该 SHA 当作组合最终冻结版本。WorkSSD 实际文件系统为 `/Volumes/WorkSSD`，本次观察约 335 GiB 可用；远端容量独立核实，Mac 全部材料、缓存、控制与证据留在 WorkSSD。

下一步需用户决定是否授权接入实施及两题实验，并冻结模型配方、任务集合和费用/资源上限。正式收录机制、全 K3 预算例外不从本次调查推导授权。

主 Agent 持总体、外部合同和 packet；`i14_compatibility` 持本地入口只读调查并完成，`evaluation_judgment` advisor 持首轮实验判断并完成。没有在途运行和源码改动。

证据入口：[组合版说明](../../../../variants/pi-braid-i14-reviewer-cleaner-e2e/README.md)、[官方仓库](https://github.com/frontier-harness-eval/eval)、[官方评测合同](https://github.com/frontier-harness-eval/eval/blob/main/skills/frontierharness-eval/SKILL.md)、[执行器和计费说明](https://github.com/frontier-harness-eval/eval/blob/main/skills/frontierharness-eval/reference.md)。官方材料读取于 2026-10-05，执行时应冻结版本而非依赖 main。
