# Multi-agent ARC-Bench-Lite 首轮结果

本轮使用 ARC-Bench-Lite revision `1eb018367bedd618d3b9ced406ce07fb423d4956`，官方单 worker 评测八个应用。分数是通过用例数/总用例数；测试失败属于应用质量结果，评测设施均完整结束。

| Variant | Keep | BookStack | 合计 |
| --- | ---: | ---: | ---: |
| pi-generalist | 3/32（9.38%） | 18/34（52.94%） | 21/66（31.82%） |
| pi-team | 16/32（50.00%） | 15/34（44.12%） | **31/66（46.97%）** |
| codex-generalist | 5/32（15.63%） | 8/34（23.53%） | 13/66（19.70%） |
| pi-verification | 8/32（25.00%） | 9/34（26.47%） | 17/66（25.76%） |

原固定批次在 `runs/batch-multi-agent-20260922-01/`；其中五个评分来自 Braid `0c68c75`。补跑证据如下：

| 项目 | Run | Evaluation | 生成/恢复边界 |
| --- | --- | --- | --- |
| pi-verification Keep | `20260922-144234-cd7850f8` | `20260922-153455-63155f43` | Braid `690522e` 下生成；provider/teardown 失败后从干净 PR commit `19d96f6` 确定性导出并冻结。 |
| pi-verification BookStack | `20260922-154050-5ee2ae35` | `20260922-165811-3a5efd02` | Braid `673c119` 正常交付并自动评测。 |
| codex-generalist BookStack | `20260922-144234-2b52c95d` | `20260922-170531-cd743f12` | Braid `690522e` 下生成；provider 长时 500 后从保留工作树提交 `3fe521c`，确定性导出并冻结。 |

因此八个分数都是真实官方测试结果，但这不是严格同 revision、无恢复干预的干净对照矩阵。两次确定性恢复没有修改应用内容，只完成提交、导出与冻结；它们仍证明应用质量，不证明对应 Braid 交付链正常。variant 间的初步排序以 `pi-team` 最好，但下一轮收窄前应先决定是否用统一修复版重跑候选组合。

本轮同时修复了两个运行时根因：Braid `690522e` 对开放 work-item 的明确 Failed turn 有界重放一次；`673c119` 让 blocked assignment 的新 generation 复用原工作树。WSL `/tmp` 满载通过把已退出 workspace 迁到 `runs/_retained-workspaces/` 并保留原路径符号链接解决，模型、runner、浏览器缓存和运行证据均未删除。
