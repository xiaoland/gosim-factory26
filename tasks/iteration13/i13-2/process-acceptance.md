# I13 已有过程的验收

本次验收回答 I13 的改进是否在真实工作中被采用、是否达成原来的机制目标。它先于最终应用评分，不能代替应用验收，也不需要为补齐观察启动专门模型任务。来源为本地 `exp-20261001-184401-7c84dd` 和已保全的官网当前 attempt；用户暂停后的完整检查点由本轮保全回执确定。

## 当前判断

| I13 目标 | 已观察行为与判断 | 尚不能据此证明的内容 |
| --- | --- | --- |
| 会话接续保留工作记忆 | GLM/GitHub 在 Debian-Rebuild 接回原根 native `01a0f66b-8bef-77c7-883a-8adb41c2532a`，8 份历史文件前缀摘要保持，真实后续请求完成。此恢复场景成立。 | 不证明所有 description 重建、并发输入、空闲卸载与 Unknown 恢复分支都成立。 |
| 原生故障局部化 | 官网 GitHub 当前 attempt 发生 cgroup OOM，Pi wait 返回 SIGKILL，非零退出被当成 teardown 失败并扩大为整轮 blocked。 | 尚无内核 victim/sender 原件；不能把历次 SIGKILL 全归为 OOM。当前恢复目标未达成，纳入 I13-2。 |
| 协作知识各归其位 | Sheet 根成员确实读取三项有关技能，先建共同文档，随后 PR 2 又复制平台、种子、API、文案和验收要求。材料已经触达，避免重复镜像的目标仍未达成。 | PR 的责任边界和本次取舍可以合理保留，篇幅本身不是失败判据。精确区分归协作调查。 |
| packet 参与判断并可被接续 | Sheet 根与 PR 2 的 packet 写在 clone 外；PR 2 又在实现结束后才建立它。GitHub 根的 `packet/` 留在未提交状态并自行注明“勿提交”。两项 develop 均无 AGENTS/tasks，当前共享交接要求未达成。 | 文件存在或技能已读均不足以证明采用；Sheet PR 3 的在途 packet 已位于正确 clone，须按候选发布阶段判断，不能笼统判为从未创建。 |
| 过时讨论不持续占据正常视图 | 当前 hide 仅作用于单条评论，根评论隐藏后后代仍可见，与用户明确的讨论树语义不符。 | 是否有具体未处理的旧评论、resolve 和 hide 各自发生过什么，仍以冻结 DB 及事件为准。 |
| 工具与子 Agent 改进 | 当前采集可见原生 vision/advisor 委派和技能读取；仅按工具名与次数汇总可找到证据入口。 | 调用成功、结果采用、executor 的委派收益、三层再委派和工具配置正确性都不能由次数推断。未出现的工具不自动判失败。 |

## 证据入口与范围

恢复身份、容器 binary 及历史前缀：`runs/iteration13/local-rebuild-20261001/{launch-summary,primary-readback,primary-first-generation-readback,append-system-readback}.json`。官网故障的具体时间线和关联限制见 [失败分析](../hosted-github-recovery-failure.md)。

本地过程的第一轮窄检索来自 `runs/iteration13/local-rebuild-20261001/monitor/20261001T114033.094510Z/`。工具/技能索引保留在 `runs/iteration13/i13-2-20261001/process-acceptance/*-tool-summary.json`，包含原始路径和本次 attempt 时间过滤。GitHub 的 native 文件还带导入历史，只有本次时间范围的条目可以声称来自本次执行；旧历史仍可作为有明确来源的 I13 早期观察。

Sheet PR 2、根 Issue 1、共同文档和实际技能读取的因果调查归 [协作调查](collaboration-findings.md)。该调查负责将预期、指令、实际采用和后续结果连起来；这里不另建一份对 PR 内容的解释。完整快照取得后继续补足对象关系、当前文档与上下文变化，修正完成后用恢复后的同一工作继续观察。

## 用于本轮决定

现有过程已经足以启动 OOM 与协作修正。尚未观察的其它 I13 分支保留为未覆盖，避免为了形式上的全通过花费 API 额度。新代码编译、实际 CLI 与冻结材料读取建立实现事实；恢复后的真实行为建立采用和效果事实，两者分别报告。I13-2 不通过手工改写旧 rollout、删除原始 PR 或注入隐藏评测结果制造改进证据。
