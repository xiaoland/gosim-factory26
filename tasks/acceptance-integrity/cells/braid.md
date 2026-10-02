# Braid 实施准备：成员通信与 PR Git 语义

状态：2026-09-26，方案与独立场景预演已形成；用户随后明确授权开工，本文末尾记录实际实施。预演和编译均不等于运行验收。依据为上层 [packet](../packet.md)、[主设计](../design.md)、[协作审查](../braid-github-audit.md) 以及当前 `sources/braid` 工作树；没有运行测试、probe、模型或实验。

## 决定与边界

Braid 负责持久的成员身份、工作项、显式消息、运行状态和 bare origin 上的 Git 事实。它不为 Issue/PR 选模型，不解释评论中的业务完成语义，不管理 Pi 原生子 Agent，也不把 quiescent 当作应用验收通过。保留每工作项独立 clone、现有事件队列和精确 Git ref 更新；不要扩成全站订阅、review 审批或自制 Git 命令集。

当前源码中的关键事实：`assignments.member_login` 已有唯一索引，`local_items.desired_member_login` 保存当前具体成员；`discussion_changed` 只把评论送到工作项及关联/同串参与者的工作项，尚不读取正文；wake batch 和 `claim_runnable_turn` 按工作项而非成员选人；CLOSED assignment 在 finalization 后 sleeping，MERGED PR 的 assignment retired；`consume_closed_activation` 消耗终态激活。PR `head_ref` 固定写成新建的 `braid/pr-N`，base 从 `local_run.delivery_ref` 读取；`ready_commit` 同时表示非 draft 和 merge 的 SHA 锁；`apply_merge` 恢复时又写死 `refs/heads/braid/pr-N` 与 delivery ref。这些位置必须成组修改。

B Sheet 新增修正见 [指派生命周期 cell](assignment-lifecycle.md)：完成保留负责人、取消事件不依赖已消失的执行身份，不让局部收尾阻塞无关工作。该补充正在实施准备，不能从本文主体已实现推断已覆盖。

## 成员寻址和终态对话

`--assignee` 接受的是配置别名，每次指派生成新的具体 `@别名-序号`；评论中的 `@具体成员` 只接受这个完整身份，不把 `@glm` 等配置别名当成某位成员。`assignee_directory`、`profile_for_login` 和 `group/provider.rs::local_instructions` 应调用同一可指派目录规则，保留 root-only 的既有禁止新指派语义；上下文另显示当前/历史具体成员，不能把联系人列表误称可指派配置。

创建可见评论时，在同一 SQLite 事务内保存评论正文，再解析并记录每个明确 `@具体成员` 的投递尝试；未知、配置别名和已改派的名字只使**对应投递**不可达，不回滚普通评论。CLI 文本和 `--json` 都返回 comment id 及逐收件人的 `queued`/`unreachable`（含原因和当前负责人）；后续改派竞态还须把该条投递更新为可查的 `undeliverable`，不能只靠“评论已创建”的成功退出码。解析优先复用已安装的 `comrak`：仅从普通可见文本节点识别边界完整的成员名，跳过 inline/fenced code、HTML 注释和链接目标；`a@b.com` 不能成为 `@b`。不为此加入新通用消息系统或正则依赖。

按 `desired_member_login` 与历史 `assignments.member_login` 精确解析、去重，把每个明确收件人的具体身份写在投递事件上。已有关系/同串广播继续表示“这个工作项有更新”；明确收件人事件表示“交给此人”，不能只写 `work_item_node_id`，否则改派后 wake batch 会送到替代者。尚未物化但仍是该项 `desired_member_login` 的成员可接收，事件在物化后进入队列。写者自提及显示 `self`/无额外 turn；对同一收件人只投一条，保留 `Issue/PR #`、thread root、comment id 与 `comment view ID --thread` 入口。队列竞争时再核对事件中的具体身份与当前 assignment revision：改派后旧消息记录未投递原因，绝不转给新成员。

编辑评论仅对**新增加**的明确地址产生新投递结果；原有名字不重发，新增的未知/失效地址也回显不可达。隐藏、删除、resolve、reaction 不创造新点名；已投递的引用仍指向原评论入口，收件人查看时看到当前隐藏/删除状态。当前 `discussion_changed` 为这些动作产生的普通关系事件可沿用，但不能意外唤醒已结束成员。历史同串参与者的普通关系通知仍按工作项当前负责人投递，界面不要把它写成“通知了原作者”。这与直接 `@旧成员` 的身份规则不同。

关闭本身不删除现任成员地址。显式点名 CLOSED Issue 或 MERGED PR 的现任成员时，恢复同一逻辑成员；原生 user message 只给出对象当前状态和原评论引用，后续行动由 LLM 判断。Braid 不自动重开、不自动发起新的合并。MERGED 后不要把同一逻辑成员直接退休到不可联系：完成既有 finalization 后保留 sleeping 的 assignment、agent/session 和必要 clone 记录。复用 reopen 的原生会话恢复与上下文物化路径，但触发源须是带持久收件身份的显式消息；普通关联评论、写者自己的评论及 finish 回声不触发。内部接触完成后可睡眠，产品界面不引入“单次 turn”概念。`writer()` 仍只允许实际 running 的会话写入，不能让 sleeping 会话持有写权限。已封存 run 不建立常驻通信服务；只承诺运行仍可接续期间的对话。

避免 finalization 吞并发消息的最小改动：当前 `prepare_work_item_finalization` 先消费该项所有 open batch，`mark_turn_terminal` 在 finalization 后再次消费该项所有 open batch；这两处范围过宽。关闭前已排队的更新应与关闭事件进入同一最后输入，领取 turn 时现有 `claim_runnable_turn` 已原子消费其 batch，无须在收尾再清空整项。关闭**之后**的具体点名记录为带收件身份的 pending mention；在 finalization 仍运行时先留待处理，睡眠后沿恢复路径唤醒。只允许这类直接投递激活终态，普通 wake 不激活。`status`/quiescent 的 pending 口径须计入该 mention，避免进程在恢复前退出；如果消息先于 close 进入同一 batch，则 finalization 输入包含它。改动落在关闭准备、finalization 收尾和终态激活选择，不需要重建 wake batch 调度器。若出现 claim 已消费旧 batch、其后新点名到达，收尾只结算已领取的 batch，新的事件和 batch 保持 pending。

改派的旧成员与新负责人是两个身份。本轮已定旧工作会话停止后不可再激活；`@旧名` 的评论仍保存，但该地址回显“已改派，不可达；当前负责人 @新名”，绝不转投。开工影响须披露这个边界。未改派的 CLOSED/MERGED 现任成员仍可联系。

## PR 创建、ready、查看和合并

新 migration 在 `local_items` 为 PR 保存不可变 `base_ref` 和独立 `draft` 布尔值；旧行的 base 回填原 `delivery_ref`，draft 由 `ready_commit IS NULL` 回填，之后 `ready_commit` 不再充当合并版本锁。`head_ref` 保留原字段；旧 `braid/pr-N` 行仍引用其原分支。`local_merges` 的 prepared intent 应保存本次实际 `base_ref/head_ref` 与精确 base/head/result SHA，恢复不猜全局默认分支。migration 前向追加，不改已发布 migration。

`braid pr create --base BRANCH --head BRANCH [--draft]`：两者都只能是 origin 中已发布的 `refs/heads/*` 分支，可接受短名并规范化为完整 ref；不存在、非分支、相同 base/head 明确报错。显式 `--head` 持续引用那条分支，绝不复制提交；commit SHA 或 tag 不再作为 `--head` 的伪分支输入，要从 commit 起步可先用普通 Git 建分支并 push。省略 `--base` 取当前 `delivery_ref`；省略 `--head` 时保留便捷行为，在选定 base 当前提交新建 `braid/pr-N` 并保存为 head。默认 **非 draft**，只有 `--draft` 创建草稿；缺省 head 的新分支暂时与 base 同提交并不需要特殊 draft 默认，尚无可合并的新提交时 merge 应明确拒绝。创建回执和 request-id 重试须返回 PR **保存的** base/head 与查询时的发布 SHA，而非重新用全局 delivery ref 解释旧 PR；同一 request-id 若带互相矛盾的分支参数，明确失败。PR assignee 的 clone 从已保存的 head 分支检出；持续指令用真实 head 名称说明 push 目标，不能写死 `braid/pr-N`。普通 Git push/fetch 仍是发布手段。

`braid pr ready ID` 可由有权写入的任一活动成员或显式宿主调用，要求 PR OPEN 且 origin 上 head ref 可解析，把 `draft` 改为 false；不读取 PR 私人 clone 的 index、HEAD 或干净程度。`braid pr ready ID --undo` 将它改回 true。两者幂等，返回当前远端 head SHA 供使用者记录，但不将其默认为验收通过的版本。CLI 沿用 `gh pr ready --undo`，不另建 `pr draft` 近义命令。

`braid pr merge ID [--match-head-commit SHA]` 在 origin 读取该 PR 保存的 base/head 当前 SHA。draft/非 OPEN、或 head 已包含于 base 而没有新提交时不合并；给出 `--match-head-commit` 时先比较调用者预期与实际 head，不相等则无副作用失败。没有该选项时合并当前已发布 head，不读旧 `ready_commit`。保留 Git object 中的双亲合并提交、prepared intent 和 `git update-ref --stdin` 的原子 `verify head + CAS base`；冲突记录 base/head 与明确错误，源/目标 ref 变动则候选失效、可重新准备，不更新错误分支。`apply_merge` 与 `recover_merges` 只从该 PR/intention 读取 refs：若 base 仍为预备 SHA，核对 head 后更新；若 base 已是 result SHA，仅补 SQLite MERGED 收据；若 base 为第三个 SHA，保留冲突/待人工判断，不能声称成功。合并 develop 的 PR 只推进 develop；合并 main 的根 PR 只推进 main。Factory 导出仍读取 `delivery_ref`，不会把 develop 的推进冒充最终交付。

`issue view` 从 `issue_in` 的权威关系显示父项、直接子项、关联 PR，每条仅编号/标题/状态/具体负责人；`pr view` 显示关联 Issue、保存的 base/head、查询时 origin 上当前 base/head SHA、draft、已合并的 merge SHA。文本和 `--json` 采用同一明确字段契约；`list` 保持简洁，避免为每行反复读 Git。ref 缺失要显示缺失或明确失败，不能回退到 `ready_commit` 冒充当前版本。当前 `Item` 与 `ITEM_FIELDS` 只支撑精简 view，优先扩对应 view 投影，不复制第二份关系表。现有 canonical context 的 `base_ref` 也应改为持久的 PR base。

Factory 的最小只读集成接口是 `result.json.root_issue.state`：在写每次 result 时，Braid 从自己的对象库读取 Issue #1 当前 `OPEN`/`CLOSED`，连同既有 kind/id 写出；即使本次 `blocked`/`failed` 也尽量保留已知状态。确实读不到时写 `null` 并保留具体读取错误，不把未知状态推断成 CLOSED。Factory 只在 `status == quiescent && root_issue.state == CLOSED` 时从 `delivery_ref` 导出 main；其余保持未完成和诊断，不直接读内部 SQLite、评论或测试结果。此接口只报告对象事实，不作应用质量裁决，也不建立新的 Braid 状态机。

develop 的起点无需 Braid 新命令：Factory 将本次 delivery ref 初始化为 `refs/heads/main` 后，根成员在 clone 中用普通 Git 从已发布的 `origin/main` 建立、推送 `develop`；子 PR 指向 develop，根 PR 再用 `--base main --head develop`。前提是 origin/main 已由运行初始化发布，`--head develop` 前必须 push。Braid 的 PR 分支语义与交付 ref 据此各司其职。

## 顺序、调用者和独立场景预演

建议先做 migration 与对象接口，再做具体成员事件/终态调度，再接 CLI、提示词和查看投影，最后改 merge intent/recovery 并由主 Agent 整合 Factory 状态判断与 variant 流程。实现时既有调用者 `create_pr_with_profile[_and_head]`、`ready`、`merge`、`pull_request`、`group/pr_agent.rs`、`group/dispatch.rs`、`local::status`/`result` 都需按新契约调整；Braid 只报告 quiescent/blocked/failed、根 Issue 状态和 `delivery_commit` 事实，Factory 依上面的明确双条件判断能否导出。最终自动化 V&V 属于 variant/SVC 方法与生成应用，不写进 Braid ready/merge 判断。

以下是按已查明接口逐步推演的**反例场景**，用于决定接口是否闭合；尚无真实执行结果，不能写作 PASS：

| 操作与状态 | 方案应产生的可见结果；若未出现则暴露的缺口 |
| --- | --- |
| Issue #1 的 `@glm-1` 在 Issue #2 评论 `@kimi-2 请回报`，两项无关联 | Issue #2 留原评论；`kimi-2` 的下一 turn 收到 `Issue #2`、thread/comment 引用并可 `comment view`；`glm-1` 不因自写收到回声。若只有评论记录而无收件身份/turn，B 的失联重现。 |
| `kimi-2` 的 Issue #2 CLOSED 后，根在别处明确 `@kimi-2` 追问；随后 `kimi-2` 回复 | 同一具体成员看到仍 CLOSED 的对象状态与原评论引用，行动由其判断；回复入库后不因自己写入而循环唤醒。若消息在 close finalization 批次中被吞，需改终态 batch 消费。 |
| PR #3 已 MERGED，关联 Issue 的根明确 `@deepseek-4` 询问合并依据 | 原 PR 成员能回答，PR 仍 MERGED、原 merge SHA 不变；若 retired 会话无法恢复，则终态生命周期没有闭合。 |
| Issue #2 从 `@kimi-2` 改派 `@glm-5`，旧名被点名；或改派恰在投递入队后发生 | 评论保留、逐地址回显旧名不可达和当前负责人；已入队事件可见未投递，不能改送 `glm-5`。重新点名 `glm-5` 才投递。 |
| 评论已有 `@kimi-2`，编辑正文添 `@glm-5` 和无效地址，随后 hide | 只新投 `glm-5`，无效地址回显不可达；旧成员不重收；已收到引用查看时显示 hidden 与理由，不把隐藏正文当新命令。 |
| 先 push `develop`，创建 `--base main --head develop`，后续 develop 再 push | `pr view` 的 head SHA 随 origin/develop 变化；ready 只改变 draft；根可用 `--match-head-commit` 锁定自己验过的 SHA，旧 SHA 匹配失败可见。若显示第一次快照，head 仍被复制。 |
| 在另一个 clone 合并上述 PR，之后再创建 `--base develop --head feature/x` 的子 PR | 第一 PR 只推进 main，第二只推进 develop；两次合并不看原 PR clone 的未提交文件，也不让全局 delivery_ref 替换第二 PR base。 |
| prepared 已落库，Git ref 已更新但 SQLite 未记 MERGED；另一次是 base 被其他 push 推进 | 第一种重启后按 intent/result SHA 补收据，不做第二个 merge；第二种报告冲突/需重新准备，不暗改新的 base。两 PR 指向不同 base 时恢复仍各用自己的 ref。 |
| 根 Issue 仍 OPEN、部分子项未指派，所有当前 Agent 暂时静止 | Braid 如实 quiescent 且 `result.root_issue.state=OPEN`；Factory 保留未完成及原因，不导出 main。即使根 CLOSED，只要 status 为 blocked/failed 也不导出；状态读不到时保持未知。 |

## 尚待主 Agent 处理的决定与证据缺口

已定的产品边界：改派后旧成员不可再激活，明确回显不可达和新负责人，不转投；开工影响说明须包含这一点。已结束 run 不维持即时聊天服务，只在可接续的运行期间交谈。无新增的用户产品决策；真正待证实的是终态消息调度、CLI 回执和不同 base 的恢复能否按上述场景工作。

证据缺口：CLOSED/MERGED 后的接触、编辑时新增点名、改派竞态和不同 base 的 prepared merge 恢复都还是接口预演；源码追踪证明当前无法满足，不能证明拟议实现已满足。开工后的真实操作应串起评论对象、投递事件、原生 turn 输入、origin refs/merge SHA 与 Factory 最终状态；按根仓库约定不新增或运行 Factory/Braid 测试、probe、自检，也不以 reviewer 读代码代替操作证据。

## 实施记录（2026-09-26）

源码已按上述决策修改，权威运行契约更新在 `sources/braid/docs/20-product-tdd/local.md` 和 `lifecycle.md`。新 migration `0010_pr_refs_draft.sql` 保存 PR 的 base ref、draft 和合并 intent 的 base/head ref；`0011_local_direct_messages.sql` 保存事件具体收件身份与逐评论地址投递回执。创建 PR 现在接受已发布的 `--base`/`--head` 分支及 `--draft`，缺省 head 从所选 base 建立分支，缺省为非 draft；ready/ready --undo 只读取 bare origin 的 head。merge 可选 `--match-head-commit`，按每个 PR 保存的 base/head 做冲突判断、CAS 和恢复。view 增加 Issue 关系及 PR 的当前 Git ref/commit、draft、merge 事实。`result.root_issue.state` 读取对象库，blocked/failed 也尽量带回已知值，供 Factory 使用双条件导出门槛。

评论正文保存与点名投递分开。新建可见评论和编辑时新加的地址按具体成员记录 queued/self/unreachable；未知与已改派地址不阻止正文创建。队列事件保留 recipient_login，实际开始原生 turn 后才记 delivered；改派使仍待投递的旧地址不可达。CLOSED/MERGED 的当前成员保留可接触的休眠身份；终态定向消息沿既有物化、队列及恢复路径，给出状态和原评论引用。没有已物化休眠身份但仍是当前负责人时，沿原指派路径建立身份；旧成员不会借新负责人的会话。收尾不再整项清空并行 wake batch，终态普通广播不再替代显式点名。

已执行 `cargo check --locked`，结果成功，仅有既存未使用项警告。按任务边界未编写或运行测试、probe、自检、模型实验，也未在真实 Braid 运行中观察消息投递、Git 合并恢复或 Factory 导出；表中场景保持待实操验证。特别应观察终态点名恰好与关闭收尾并行、改派恰好与消息领取并行、provider 失败重放，以及不同 base 的 prepared merge 中断恢复。编译结果只证明接口与类型可构建，不将这些场景标为 PASS。
