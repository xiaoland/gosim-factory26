# Pi + SVC / Keep 恢复后实验

本次实验由用户在 ARC-bench 服务恢复后授权，只运行一次 `pi-svc / Keep`，没有自动重试或启动其他 variant。

## 结果

Run `20260921-083151-b978c271` 自然完成，整体 `outcome.json` 为 completed。Pi 生成耗时 609.9 秒，完成冻结且没有结构化错误或重试；应用 SHA-256 为 `541a501805e16e46b0def7cfe4d9be6ad33a9e5e23fab45a17ae7061711da6ba`。

WSL 评测 `20260921-084202-543910fb` 核对了同一应用哈希和固定 benchmark revision `1eb018367bedd618d3b9ced406ce07fb423d4956`。32 项均有终态，9 项通过、23 项失败、0 flaky、0 skipped，得分 `9/32`，pass rate 0.28125。runner exit 1 来自测试失败；评测阶段本身完整结束，不是基础设施失败。

失败中 19 项为 60 秒 UI locator timeout，4 项为断言不匹配。后者包括 Help & feedback 菜单项缺失、list/grid 切换按钮缺少预期 `aria-pressed`，以及 sidebar 按钮缺少预期 `aria-expanded`。这些证据表明当前应用覆盖了部分静态界面，但核心交互和可访问状态契约尚未形成完整实现；本轮不据此自动修改 harness 或补跑。

SVC analysis 导出完成，content、tool linkage、relation mapping、descendant closure、history branch、usage 和 timestamps 七个域完整。单个 Pi 会话的 overview 为 partial，因为原生记录没有可用的显式 terminal state；这不改变 Factory 已验证的生成退出、冻结和评测终态。

总流程约 1866.7 秒，其中生成约 609.9 秒、远端评测约 1252.3 秒。模型用量记录为 34,457 input、91,199 output、48,306 reasoning、3,932,160 cache read tokens；比赛账单未知，不作客户端费用估算。

## 结论与限制

本次证明比赛模型网关当前可用：Pi 单次生成自然完成，没有结构化网关错误或 retry；新的 outcome、低噪反馈、WSL 评测和 analysis 闭环也首次在真实完整实验中贯通。一次成功不能证明网关持续稳定。

这是当前 `pi-svc` 接入的第一份有效 32 项成绩。历史 `14/32` 来自旧 adapter，不能作为当前 harness 的同条件回归基线。下一轮实验或修正仍由用户复核本结果后决定。

原始证据位于本机忽略目录 `runs/20260921-083151-b978c271/`；关键入口为 `outcome.json`、`evaluation/20260921-084202-543910fb/summary.json`、`results.json`、`test.log`、`remote-evaluations/20260921-084202-543910fb.json` 和 `analysis/000-08d6003bbdedfec292b2/evidence-v4.zip`。
