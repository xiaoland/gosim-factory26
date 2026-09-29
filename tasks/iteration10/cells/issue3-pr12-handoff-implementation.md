# Issue #3 / PR #12 接手误判热修复

取证见 [Issue #3 / PR #12 接手与双写](../observations/issue3-pr12-handoff.md)。PR #12 的评论 #39/#41 已送达，原负责人 glm-6 正在执行且有未提交编辑。Issue 负责人仅依据 origin PR head 未变化判断其未行动，未取得交接确认便写入同一分支。

Braid 的 `pr view` 现在从现有 SQLite 状态展示当前负责人的 assignment/session/turn 事实、执行轮次开始时间及最近三条针对该负责人的评论投递回执。JSON 字段为 `assignee_activity` 与 `assignee_deliveries`。JSON 保留诊断字段；正文只概括 Braid 观察到的执行状态，并注明“已送达”不代表要求已完成。视图明确声明 head 仅代表已发布提交，未提交或未推送的工作未知。无需数据迁移。

共用指令改为：先核对 PR 视图并联系当前负责人，确认交接点以及在途成果的保存或发布；只有明确交接确认，或可核实其执行失败且不能继续，才通过 `pr edit ID --remove-assignee CURRENT_MEMBER --add-assignee AGENT` 转移 PR 责任。PR 实现修改与 head 发布由当前 PR 负责人承接；即使显式 `--head` 使用 Issue 负责人先前发布的设计分支，后续变更也应在讨论中交接，再由 PR 负责人实施。此修复不自动接管，也不强制中断现有会话。

源码提交 `5c957436f5aead2c2f4d49a6a5030d8e22d9863d`。`cargo check` 通过；按本次热修复要求未新增或运行测试。热恢复使用新 binary 和原请求材料即可：`worker.rs` 在 `--offline-resume` 时重算指令摘要，摘要不同会替换旧 provider session，使现有 Issue/PR 负责人收到新共用指令；无需修改 Profile 的 `user_instructions`。运行部署由主线负责。

进一步核实了“共享 Git 工作区/必须另建 `braid/pr-12` 分支”的报告：这不是本案根因。Braid `worktree.rs` 使用 `git clone --no-local`；SQLite 记录 Issue #3 与 PR #12 位于不同 clone，分别使用本地 `braid-agent/issue-3/pi-deepseek-fast-g1` 与 `braid/issue-3-m1`。Issue 负责人 05:33:00Z 推送设计提交 `07980ef`，05:33:13Z 用显式 `--head braid/issue-3-m1` 创建 PR；PR 负责人 05:47:19Z 推送实现提交 `9d30be4`。Issue 负责人之后在自己的 clone 于 05:53:43Z 提交 `a194fee`，05:58:41Z 推到同一个远程 PR head，这才是未交接越界。PR 负责人 05:59:02Z 提交 `d262e52`，05:59:44Z 推到独立 WIP ref，未覆盖 PR head。显式 head 承接已发布设计提交符合当前 `pr create --head` 语义；无须禁用同名远程 ref。

## 实际部署

2026-09-29 06:31 UTC在WSL hotfix-02/generation接续两题：GitHub `pi-braid--hackathon--github-db0f28e3288046`，Sheet `pi-braid--hackathon--sheet-d105b86431cdc7`。Linux binary SHA256 `eae8333a8b6d789f440c4d3d337ab06ee84e056279660255f9fbc3ae763d591b`。新physical instructions已出现交接段，日志确认因指令变化替换上下文；真实`pr view 12 --json assignee_activity,assignee_deliveries`返回sleeping及评论#56/#52/#46 delivered，说明查询接线有效，不意味着行为缺陷已经通过长期观察排除。保留原模型、应用与分支，未强制重命名PR head。恢复点仍是本次暂停时的完整现场；没有确认到双写前完整checkpoint。异常与行为采集在hotfix-02继续3+8周期，监控Agent已接续。
