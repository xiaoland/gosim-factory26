# 官网 run 的 Agent 过程证据缺口

2026-09-23 只读调查的边界：我们已能确认某些交付产物为何在评分时卡住，却不能从现有官网归档回答 Agent 当时如何阅读需求、如何派发 Issue/PR、子代理做了什么、自验采用什么 oracle、为何接受并停止。若把后者写成根因，就是用最终代码倒推决策。用户要求在此停下，等待实验基础设施补齐证据。

| Run | 已经证实 | 不能据此推断 |
| --- | --- | --- |
| deepseek/Keep `bd3c2e50b511` | 交付后独立评测 32/32；官网 stdout 只记录生成开始、约一小时后冻结和测试。 | Issue/PR 是否拆分、是否调用子代理、为何满分；同配置 WSL 本地另一次生成失败，不能代替该 run。 |
| deepseek/BookStack `d853830ddb0a` | 同一交付源码和重评 DOM 复现 7 个入口阻断：共用 Tags `<details><summary>` 导致 5 项 button 不可定位；草稿直接进编辑页导致 1 项找不到 Edit；Book 8.2 初始已收藏导致 1 项只有 Unfavorite。详见[成绩报告](../../reports/2026-09-23-official-results.md)。 | Agent 是否有意选择这些 UI/初始状态、内部是否测试相关场景、谁负责相关实现。 |
| mixed/Keep `007b8fc9d38b` | 官网日志证实 6 项找不到 Delete Note/Change labels button、2 项找不到 Pinned 子节点、1 项找不到 Save。需求文本明确要求前两者为 button。 | 当前归档无失败 DOM/源码，无法独立确认实际角色为 menuitem；也没有该 run 的 76/76 自验原始记录，不能解释漏检链。 |
| mixed/BookStack `6e786f33bc1b` | 同一交付源码里书架/图书列表项是 Link、登录昵称是 span；官网测试多处等待 button/heading。21 项失败中 17 项卡入口、4 项卡操作后标题。 | 没有失败 DOM 和 helper 全文，不能把 21 项统一归因为角色差异；Braid 会话索引不能替代对话正文。 |

缺少的**最小原始记录**，按恢复因果链的顺序排列：

1. **生成过程**：每个官网 run 的 `.factory26/<run>/native/manifest.json`、对应 `native/*.jsonl`、Braid Issue/PR/comment 对象与修订、`braid.log`。它们需能把工作项、profile、物理会话、工具调用和最终交付 commit 串起来。mixed/BookStack 的 [远端目录清单](../../runs/competition/iteration-throughput-boundary-20260923/hosted/pi-team-mixed/tasks/arc-bench-lite--bookstack/workspace-files.json) 已列出 `native/000…010*.jsonl`、manifest 和 `braid.log`，但本地仅下载了 `braid-state/sessions.json` 索引，里面指向的临时 `/tmp/factory26-.../native-homes/` 已消失。
2. **Agent 自验**：运行时实际执行的检查命令、断言/脚本、stdout/stderr、退出码及其针对的需求或控件合同。mixed/Keep 的“76/76”目前只有二手叙述，缺该 run 的原始测试定义与结果；没有它便无法诊断 oracle 是漏测、错测还是运行了旧版本。
3. **失败现场**：至少每个不同首阻断类别的一份 Playwright `error-context.md`/DOM、截图或 trace，连同实际 `helpers.ts`、用例和冻结应用哈希。官网日志只有 locator 超时，不能说明元素不存在、角色不同、状态不同或 helper 回退造成误判。

当前 `traceability.json` 在所查 run 中为 `interfaces: [], tests: []`，`commit-history.json` 报 `workspace_unavailable`；平台 stdout 只给生成/冻结/评分阶段边界。网站维护期间，已试的 `/runs/{id}`、`/artifacts`、`/traceability`、`/commit-history` 和 source 请求返回 HTTP 500，因此现在不能补采。最小设施改进是**在工作区销毁前保存同一 run 的原生记录和少量代表性评测现场**，沿现有 `runs/competition/.../tasks/<task>/` 归档并记录文件取得状态；无需另造一套追踪语义。官网恢复后可先尝试按已有文件清单下载，若工作区已不可用，再将采集提前到 Runner 生命周期内。
