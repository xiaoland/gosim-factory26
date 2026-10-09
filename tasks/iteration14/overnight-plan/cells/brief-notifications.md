# Braid 简短通知

状态：已完成源码窄改、编译和无模型本地消息读回；未启动实验、未请求模型、未部署远端。

用户授权范围：用户要求“让 Braid 的通知 message 更加简单简短，只需要简单地列出什么对象发生什么变化即可，也不需要有‘查阅正文请用...’”。保留 assignment/task prompt、review 候选身份与必要关联、失败诊断、事件/订阅/失效/队列语义。

实现位置：

- `sources/braid/src/group/provider.rs`：事件引用渲染为短列表；初次指派保留任务提示；内部 `activate` 映射为对象已指派；重建通知保留“上下文将重建”和作者/自编辑事实，删除保存提示。
- `sources/braid/src/objects.rs`：评论、标题/父级修改和 PR/Issue 关联通知删除正文/详情 CLI 入口。
- `sources/braid/src/objects/review.rs`：review 请求保留 PR、Issue 和冻结候选；结论/取消保留 Review 与 PR 关系及状态/原因，删除读取命令。
- `sources/braid/docs/10-prd/glossary.md`、`sources/braid/docs/20-product-tdd/context.md`：更新 Event Reference 的权威说明，明确不复制正文或操作教学。

无模型读回（验证 state 已迁入 WorkSSD，未依赖 runs）：

- 改前事件引用：`Issue #1：评论 #1 created；正文入口：\`braid comment view 1\``。
- 改后实际事件引用：`Issue #1：评论 #2 created`。
- 初次指派的内部 `activate` 由渲染器读回为 `- Issue #1 已指派`；初次任务提示仍保留。

验证：`cargo check --locked` 通过；`cargo build --locked` 通过（既有 11 条 dead-code warning，无新增错误）。使用 `/bin/false` 作为 provider executable 初始化临时本地运行，运行在首次 provider 恢复处 blocked，未发生模型调用；随后用 `braid --state ... --external issue comment` 写入真实 SQLite 事件并读回上述引用。

未验证：没有运行 Braid 测试、自检或模型会话；没有提交或推送。后续若要验证 provider 原生 user message，需要在明确允许模型/原生协议操作时使用独立临时 state。

## WorkSSD 产物收尾

用户新增绝对规则要求本项目产物全部位于 WorkSSD。此前本任务按旧建议创建的任务专属 `/tmp/braid-notify-*` 产物已逐项迁入：

`/Volumes/WorkSSD/Development/factory26/tasks/iteration14/overnight-plan/validation/brief-notifications/`

其中包含 `braid-notify-work/`、`braid-notify-state/`（SQLite、origin、result、status、backup）、`braid-notify-request.json`、`braid-notify-local.out`、`braid-notify-local.err` 和 `braid-notify-cargo-check.out`。迁移前确认没有存活的验证进程；迁移后 `/tmp/braid-notify-*` 均不存在。Cargo target 通过仓库现有 `sources/braid/target` 链接解析到 `/Volumes/WorkSSD/Development/factory26/third_party/braid/target`，未触碰通用缓存或其它项目产物。验证文件中保留了运行时生成的原始 `/tmp` 路径字符串作为历史证据，它们不再对应现存文件；实际配置、fixture、SQLite、origin、日志和编译产物均已在 WorkSSD。迁移仅改变验证产物位置，未重跑模型、测试或实验。
