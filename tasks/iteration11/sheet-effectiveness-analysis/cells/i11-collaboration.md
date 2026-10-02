# I11 Sheet 接续协作：撤销修正、最终交接与无动作通知

## 范围与证据口径

本 cell 只分析 I11 接续阶段，不重述 `inherited-process.md` 中的 I10 早期需求理解与分工。观察起点是 `db75cf2c3b82be` 的恢复现场，重点时段为 2026-09-29 17:15 UTC 之后；最终成功接续从 2026-09-30 01:48 UTC 的 root/PR #13 新原生会话开始，终点是 `396538bc0dda96` 的交付收口。早先 root/PR #13 的 Pi 握手失败是待恢复状态，不能当作最终阻塞结论。所有 Issue/PR 号均为 Braid 协作对象；官方 `fe617f4f8526` 的 59 分只作末端状态核对，不反推协作过程。

直接证据来自最终原始 SQLite 的评论与对应 native JSONL，整理索引见 `evidence/comments.md`、`evidence/subagent-calls.json`、`evidence/svc-calls.json`。评论 ID 是 Braid 原文身份，`comments.md` 行号是本地保留定位；native 行号用于核对模型当时如何消费通知。解释性判断和证据缺口单独标注。

## 链 1：撤销检查的失败观察 → 机制定位 → PR #14 的窄修正

**直接事实。** PR #11 的 #553 先把整合门禁中 `range-undo.spec.ts:482` 的 Ctrl+Z 失败作为待定位问题转给 deepseek-11。deepseek-11 随后在 PR #11 #570 给出机制：`WorkbookEditor.commitCell` 先做乐观渲染，`recordHistory` 要等 `PUT /cells` 返回后才入撤销栈；用例在画面变成 A1=4 后立即按 Ctrl+Z，按键时栈为空，因而 no-op，工具栏 Undo 同刻也 disabled。将提交窗口放宽到 1.5 秒时，旧序列稳定失败约 20.3 秒，等待撤销步骤入栈后的序列通过；因此提出 `waitForRecordedUndoStep`，只改 `e2e/range-undo.spec.ts`，判据与应用语义不变（`comments.md:13636-13648,13655-13660`）。

这是一条正向链：可见失败状态 → 读取实现时序 → 有界 probe 区分检查时序与应用语义 → spec-only 修正。替代解释是实际后端延迟或应用提交竞争在其他操作中仍有影响；现有证据只覆盖该用例及其放宽窗口，不能推广为“所有并发问题已消失”。证据也支持不改产品：`18cfeab` 的应用树零改动，68 个 E2E、typecheck、backend 171 和 frontend 196 均通过（`comments.md:13636-13640`）。

**提出与消费。** deepseek-11 将实现/证据交给 glm-15（PR #14 #572）；glm-15 在 #574 核对候选、SHA256、干净树和 `--match-head-commit` 后决定合入，并明确 packet 不随 PR #14 追加，避免仅文档移动 head 又迫使整套 E2E 重取（`comments.md:13663-13672`）。合入后 deepseek-11 在 #576 只读确认 develop=`2dc4b9f`，相对 `d07dd62` 只有该 spec +16 行、应用树未变，且 B 回归点②判据不变（`comments.md:13690-13704`）。这是“提出者解释机制、PR owner 决定合并、提出者收口”的职责闭环，#577 又独立复核了应用树与 B 宿主 spec 未变。

## 链 2：套件改变 → 证据适用性重判 → PR #13 负责人交付与 root 验收

**当时已知状态与决定。** PR #13 原生会话在 root #578 之前已经开始取四门；root 在 PR #13 #578（01:51:58）更正 B 证据清单为 12/12，并确认 PR #14 已把 develop 推到 `2dc4b9f`。相对 `d07dd62`，E2E 套件确实多了 PR #14 的 +16 行，因此旧 `d07dd62` 的 68 passed 不能直接代表新套件；但这不能推出 `18cfeab` 的已有证据失效：#574 已记录 `18cfeab` 的非跳过 E2E 68 passed、单测/typecheck，独立比较也显示 `18cfeab` 与 `2dc4b9f` 整树相同（`runtime-stalls/sheet.md:19,35-45`）。root #578 强化并记录了当前 head 的适用性口径、同步修改 Issue #1 正文；它不是四门启动的触发点（`comments.md:13722-13732`；PR13 native message `170be1db`，`work/native-homes/pi-deepseek-fast-01a0efff-7173-7ff0-967a-9e619f01d259/2026-09-30T01-48-34-507Z_01a0efff-cf4b-7018-9b07-4dae29085d1b.jsonl:54`）。证据明确的新缺口是 `SKIP_FRONTEND_BUILD=1` 与平台路径；对非跳过 E2E、单测/typecheck，未见记录说明 `18cfeab` 的环境或结果为何失效。

**分工和交接。** deepseek-14 作为 PR #13 owner 在 #582 以 `5926059` 为最终候选，串行完成四门：unit/typecheck（backend 171、frontend 196）、非跳过 E2E 68、`SKIP_FRONTEND_BUILD=1` E2E 68、Node 20.19.3 平台路径；每门均记录候选 head、dirty/untracked、退出码和 SHA256（`comments.md:13755-13779`）。他明确写出应用树仍逐字节不变、e2e 已变化，且按 #574 把 PR #14 packet 补节带入 PR #13（`comments.md:13761-13765`）。随后用 `--match-head-commit 5926059` 合入，#583 记录 merge `10cba2a`、三树相等和 main 启动/深链接/API/种子核对（`comments.md:13791-13811`），#584/#585 将交付事实交给 root 与 Issue #4 owner。

职责边界清晰：deepseek-14 对候选门禁、精确合并、合并后启动和下游通知负责；glm-4 依据同一回执关闭 B Issue（#587，`comments.md:13869-13886`）；root 在 #588 独立核对候选树、四门目录、post-merge 目录和 12/12 B 证据，再关闭根 Issue（`comments.md:13888-13907`）。#580 只能作为“未擅自关闭、仍等待 PR13 owner 交接”的局部职责例：它确实 fetch 并重新呈现了 develop/main/OPEN 状态，且发布了无变化的 packet 核查回执，不能把它当作完全停止重复确认的正例（`comments.md:13741-13745`）。

## 链 3：无动作通知 → 责任判断 → 适度停止复查

I11 继承的 R3 修改把入口规则写成：先判断通知是否改变职责、未决项或所需动作；没有相关变化时结束，不复查相同代码、哈希或检查，也不发布“无动作”回执；实质纠正、交接和行动仍须回复，且不改变 Braid 收件人、@ 投递或订阅状态（`tasks/iteration11/cells/r3-notification-work.md:7-16`）。这不是新的 SVC 原则，也没有引入自然语言去重状态机。

最终接续有可核对的正例。deepseek-6 在 native message `41baf8ae`（`work/native-homes/pi-deepseek-fast-01a0f010-42ed-71f1-b6f9-721c004a88c0/2026-09-30T02-06-34-025Z_01a0f010-4829-7560-ab6c-c541e4e448a7.jsonl:27`）读到 PR #13 #582 后判断：评论只是信息，没有问题、事实更正、交接或本职行动；#553 链已由 #576 收口，root Issue #1 归 glm-9，因此“不需回复”。这说明模型把“已完成且非本职责”的通知消费为停止，而不是再次核同一 hash。deepseek-14 在收到 #587 后也只为过时的 PR 正文做一次有意义的状态修正，没有再发重复收口评论（native `...pi-deepseek-fast-01a0f011-fa89-...jsonl:8-24`）。

同时，不能把所有重复读取都算作失败。root #588 的独立树/证据完整性核对有明确验收职责；PR #13 确实在当前候选上补取了 skip-build、平台路径并绑定最终 head。可是，虽然 #582 实际重新执行了非跳过 E2E、单测/typecheck，原文没有说明 `18cfeab` 上已有结果因何失效；不能事后替 Agent 补充“新环境”或把这两项自动称为必要新覆盖。I11 仍保留迟到轮询回执和同值状态被再次呈现的样本，且没有足够证据证明它们是同一事件重复投递；因此只能说 R3 的“无动作即停止”有局部正例，不能声称调度层已证明去重或所有成员均采用。

## SVC、packet、方法和文档是否改变了决定

直接观察到的改变集中在交接载体和证据纪律，而非产品代码。PR #14 #574 明确不改 packet，避免文档提交移动候选 head；PR #13 #582 按决定携带 packet 补节，并在正文记录候选差异。root #578 将适用性口径写进 Issue #1。独立 Git 比较显示 `18cfeab..5926059` 只有两份 packet 文档，而 `18cfeab` 与 `2dc4b9f` 整树相同；相对 `d07dd62` 的应用差异是 `e2e/range-undo.spec.ts` +16 与两份 packet 文档，应用树零改动（`comments.md:13761-13765,13896-13898`）。因此可以确认新的 skip-build、平台路径、最终候选绑定和合并后树核对；`18cfeab` 已有的非跳过 E2E 与单测/typecheck，未见记录说明其失效原因，不能把 #582 对它们的重复取数解释成已证明的必要新覆盖。因此 packet/方法改变了证据的归属、指针和停止条件，没有改变撤销产品语义或验收判据。

文档同步并不完全闭合：最终树中的 README 与 `tasks/issue-4-b/packet.md` 仍可见部分早期“C/E 未交付/待验收”措辞；这些是持久载体中的历史/当前状态混存，不能覆盖 #582–#588 的最终 Braid 收口事实。它构成 durable-doc 维护缺口，但没有证据表明它改变了 PR13 的实际门禁或合并决定。

`svc-calls.json` 与 `subagent-calls.json` 是按 message id+timestamp 去重后的索引，不代表已读结论。17:00 UTC 之后可见的新原文中只有一次 subagent status（17:19:28 查询旧 `524072e5`），没有新的 spawn/subagent_wait，也没有参数含 `svc-` 的 read/bash。这个事实支持“I11 晚期协作主要由 Braid Issue/PR owner 完成”，但不能据无显式调用断言 SVC 方法没有作用：冻结配置仍含 advisor/design、explorer/investigation、executor/implementation 的 inline workflow，既有角色指令、packet 和证据适用性纪律仍可能被模型消费。也不能把没有新 subagent 当作缺陷，因为本阶段 root、PR13、PR14 和 Issue4 的职责已在 Braid 内明确闭环。

## 覆盖边界与结论

本 cell 覆盖 I11 晚期从撤销检查修正提出、PR #14 合入、PR #13 新候选四门、main 合并、Issue #4 与根 Issue #1 收口的正向链；不覆盖 I10 全部 176 个早期文件，也不把官方 59 分解释成过程证据。直接事实支持三点：#14 修正是确定性用例时序修正且不改应用；#13 由 owner 负责补取明确缺失的 skip-build/platform 门并精确合并，root 负责独立对应性验收；无动作通知在至少一个最终成员 session 中被正确消费，而 #580 等例显示“有职责的状态回看”与“无动作即停止”仍须区分。

剩余缺口是：没有跨所有通知样本的事件级重复投递证明；没有显式 SVC 调用可证明晚期模型实际执行了哪条 SVC 命令；没有证据把 R3 的正例推广到整个 I11。故本报告不提出新的调度去重器、SVC 规则或产品改动，只保留这些边界供主分析整合。
