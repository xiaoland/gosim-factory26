# Factory 集成进度

用户确认的验收沿用 verification.md。基线提交已完成，源代码实施中。

## 已实现，待集成验收

- SVC user-scope 仅保留两行 Corpus 导航；无人值守授权归生成任务契约。
- 评测请求携带明确 ID、run/benchmark/应用哈希。官方发现清单与实际测试身份、终态核对，跳过或漏例不再算完成。
- analysis 缓存包含实际原生内容、provider 和 exporter 来源；修改输入必须产生新分析代次。
- Braid 从 result.json 指定的交付 commit 导出应用；native/manifest.json 保存跨工作树的物理会话身份、归档路径和哈希。失效会话的已消耗 usage 保留，整体终态由工作项收敛判断。

## 接口与待办

Braid request 保留 profile/prompt/state/codex/pi，增加 run_id、delivery_ref。result.json 与 sessions.json 由 Braid 负责。Factory 验证仓库归属、分支/commit 一致性及原生会话首行身份；缺失证据不能宣布成功。

下一步：Braid 已提交稳定检查点，替换后的真实上下文探针即将运行，随后执行四组 Keep。WSL runner/浏览器继续复用，先同步确切脚本版本，不修改评测器。

## 当前证据

2026-09-20：Factory 15 项边界检查、交付/会话归档 2 项通过。官方用例发现返回 Keep 32 项；两核心各自 SVC 开/关的隔离入口检查通过，开启时为两行指南，关闭时为零行。WSL 已在独立副本上验证新评测链；尚无新真实 Braid 或四组 bench 成绩。


2026-09-20 集成前检查：父仓库 `make test` 共 43 项通过，文档本地链接和 SVC status 通过。独立 Factory 审查发现的错误交付身份与探针标记冲突已修复；探针已补自身写入前后 active turn、物理会话及 pending wake/reset/event 检查。

WSL 新评测链已在 `runs/validation/evaluator-20260920-215843-6cc3c4` 的历史应用独立副本完成，evaluation 为 `20260920-215843-6f2bc1b7`：全部 32 项有终态，14/32，与原冻结参考逐项身份和结果一致。它只验证评测链，不计入新四组成绩。

Braid 失败生成工作区现在保留 Git common repo 与各 worktree，并写 recovery-workspace.json；这避免销毁恢复依据，但不声称 Factory 已提供一键 resume。
