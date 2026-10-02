# Root 维护循环：两次自编辑的指令与运行机制

有界补审，2026-09-30。仅追 `9c3a4129`、`d93a62f9` 所在 11:49 root 原生会话、所属 reset 与直接后继；不重做人工维护时间线、不改源码/工作项、不运行测试或模型。

**结论：这不是“每次 edit 立即重建”。两次 edit 都加入同一 reset，运行中的原会话反复收到累积提醒；该会话完成后才统一重建，并因 continuation 规则再排入一次 wake。历史模板把这次自编辑续接也渲染成“请处理 Issue #1 / 使用 view --comments 查看当前内容”。固定指令已有防止日常重复更新的条款，Agent 却明确选择追逐 head；缺少自写标识不是这两次选择的充分解释，因为它当时知道是自己的修改。**

## 来源与版本边界

原始根 **R**：`runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`。

- **A** = `R/work/native-homes/pi-glm-fast-01a0ecff-7bc8-75f3-ae03-c4d92e8e6561/2026-09-29T11-49-25-679Z_01a0ecff-8c2f-7379-8857-a3ff01afd017.jsonl`。
- **B** = `R/work/native-homes/pi-glm-fast-01a0ed0a-f546-7880-88cc-4124f66b22c1/2026-09-29T12-01-56-959Z_01a0ed0b-02de-77cc-a5ba-ff5e4f0f86a5.jsonl`。
- **P** = `R/braid-state/physical/01a0ecff-7bc4-7a00-8822-5f4ecfd3cf03/`，`session.json` 将 A 与 root agent `01a0eb68-0ed9-7ff0-a22a-52f93596e102`、context revision `d32759ee…` 相连。
- **Q** = `R/braid-state/physical/01a0ed0a-f543-7d01-9138-713c3ff383f8/`，直接后继 B；两份 instructions 的 SHA-256 与 DB instruction revision 均为 `7935b9e44a7280b15cd5b35bfff20492968cbdd4067122e54790b9733159f8e8`。
- DB = `R/braid-state/braid.sqlite3`，本次只读打开，查 `events/context_reset_events/context_resets/provider_sessions/turns/wake_batch_events/wake_batches`。
- 历史源码取 **Braid commit `1fabd11fc8726aea0d17b47878526a47a75c6022`**，由 `runs/iteration10/start-20260929/source-record.json:3` 与 `tasks/iteration10/build.md:3` 指认；通过 `git show 1fabd11:<path>` 只读。以下源码行号均指这个固定版本，**不是当前 checkout 或 I11 后改源码**。构建记录指向与实际通知文案、DB 行为互相吻合；未重新取得 11:49 进程 binary 的字节 hash，故不把 commit 记录宣称为全包逐字节部署证明。

## 1. 当时指令到底要求了什么

| 来源 | 原文与作用 | 不能扩张成的要求 |
|---|---|---|
| P/instructions.md:1、3 | 保留“原始要求、重要决定和未决问题的入口”；description 保存“当前任务说明与稳定决定”；“**交接前核对当前说明，无需把日常进度反复复制到正文**” | 没有要求每次子 PR push 都同步 head 到 root 正文 |
| :13 | 建立/接续 task packet，保存“当前判断、计划、证据与下一步”；“**相关决定变化时**更新原定义及受影响的任务状态” | packet 当前性不等同于对每个活跃分支实时镜像 |
| :9、21 | “收到评论不必回执”；仅需回答、纠正、交接、行动时回复；“没有新事实或新决定时，无需发布重复进度总结” | 明确抑制重复发言，但没有逐字写“无需重新读取未变代码、hash 或检查” |
| :19 | 复用有效局部检查；base 或候选发生“**影响结论的变化**”才重取证据；不重复同一套有效整体验收 | 这是检查证据适用规则，不是每次维护通知都得重验的要求 |
| :45 | 没有独立工作时结束当前回应，由后台完成消息接续，不另启 sleep 轮询 | 不要求通过额外检查填满等待时间 |
| P/context.md:11、23–29、后续“下一步” | root 正文自称“当前任务说明（task packet，**随时更新**）”，保存活跃 PR 的精确 SHA 与跟进候选计划 | “随时更新”在工作资料 description 内，不是上述固定 instruction 或原题验收条款；本补审不追其最早编辑者 |

这给出一组有张力的实际材料：固定方法限制日常回填，工作资料采用瞬时 SHA、随时更新的结构。不能将后者无条件当作更高优先级要求，也不能说模型没有拿到防重复规则。旧模板没有后续版本更明确的“无相关变化即可结束 / 不重核未变 hash”等表述；此处应按 11:49 实际文件说话。

两条目标记录尤其清楚：

- **A:36 `9c3a4129`，11:56:04.850**：先确认两 owner 正在实施、无待裁决/合并事项；写出 “The body edit notice was my own edit” 及 “repeated head updates … create churn”，最后仍认为 “accuracy matters for handover. A one-line sed edit is trivial. Do it.”，执行 `32826b6→dc566cf` 的 `issue edit 1`。
- **A:53 `d93a62f9`，11:58:34.427**：明说 “Body modifications are mine again … No new comments anywhere. Nothing to adjudicate”，又认为 “keeping the entry roughly accurate is my duty; a single sed is cheap”，执行 `dc566cf→f3a97eb`。

**直接观察**是：模型在知道无协作待办、知道自己在制造更新的情况下，把记录即时精确性置于避免日常回填之上。**解释性假设**是它将单次 sed 成本当作总成本，没计入控制面的通知/续接；源码和后继记录支持这个成本外溢，不能据此推断其全部隐藏推理。

## 2. 从工具调用到 DB reset，再到实际 user 输入

这条链不只靠相邻时间：事件有同一 `writer_group`、同一 `writer_turn`，reset 有明确 `context_reset_events` 外键，后继 wake 有 `reset-continuation:<reset_id>` dedupe key，wake batch 又由后继 turn 引用。Pi toolCallId 没有直接写进 DB 外键；两次 edit 的绑定依据是上述归属、动作种类以及各自工具调用开始—返回区间内唯一对应 root edit。

旧 DB session **S0**=`01a0ecff-8d51-7222-a7f9-c4e5be750fe2`；root turn **T0**=`01a0ecff-907d-7752-8171-bcfe4491ec73`；reset **X**=`01a0ed04-2bb9-77a0-a7be-49267dbcedb8`。T0 从 11:49:28.271 到 **12:01:48.856 completed**，全程仍是 A。

| activity / 时间 | invalidate event | X 中 ordinal | A 中实际后续通知 |
|---|---|---:|---|
| 489 / 11:54:27.611 | `01a0ed04-279b-7d73-9702-d751f8aae6a2` | 0 | :30 `7a0f9673`，1 条 title/body 更新 |
| **495 / 11:56:05.751**，A:36 的工具返回为 :37 `bcb902be` “updated” | **`01a0ed05-a6f7-7573-8722-afb04f40d12f`** | 1 | :39 `cca563e4`，累计 2 条 |
| 497 / 11:57:25.255 | `01a0ed06-dd87-7bb0-9894-cdc52ed3a53b` | 2 | :50 `f2bc9202`，累计 3 条 |
| **498 / 11:58:34.547**，A:53 的工具返回为 :54 `c032f846` “updated” | **`01a0ed07-ec33-7941-b643-05296c247d5a`** | 3 | :56 `8f60eec6`，累计 4 条 |
| 502 / 12:00:59.067 | `01a0ed0a-20bc-7ec1-8c28-8c11a9bdad0f` | 4 | :64 `c68345a0`，累计 5 条 |

五个 event 的 `kind=invalidate`、`writer_group=root agent`、`writer_turn=T0` 相同，均由 X 消费。X 在 11:54:28.664 创建，`continuation=1`；直到 **12:01:57.355** 才 applied，`old_session=S0`→`new_session=S1=01a0ed0b-04be-7170-9c69-2ff847bafa46`。因此 2→3→4 条不是同一事件被误当多条重投，也不是 3 次独立 reset，而是同一个 pending reset 收入了新的自编辑事件。

运行中的实际通知统一是：

> 当前会话结束后会用最新内容重新打开工作会话……请继续完成当前工作；如有尚未保存、后续需要接续的进展，可写到相关 Issue 或 PR。

它是**本轮结束后**重建预告，保存建议也有条件“如有尚未保存”；没有要求马上结束、没有命令“再 edit 正文”。其缺陷是只列泛化 reference，没有作者、自写身份、哪个字段变化或“你刚完成该修改”的提示。

真正后继映射为：

`X applied` → 新 wake **`01a0ed0b-04be-7170-9c69-300ef0da48c9`**（`detail=reset_continuation`，dedupe=`reset-continuation:X`）→ batch **`01a0ed0b-04be-7170-9c69-3010998c86e0`**（`urgent=1,event_count=1`）→ S1 的 turn **`01a0ed0b-0d6f-7f33-9599-8e026b9191a2`**，12:02:01.137 开始 → **B:4 `1b0b7d07`**。

B:4 实际包含更新后完整工作项快照，已经有 `f3a97eb`；尾部再次出现五条累计 reference、“**请处理 Issue #1**”及“**使用 braid issue view 1 --comments 查看当前内容**”。这里才是重建快照附带的自动续轮要求。A:69 `2a22f1a7`（12:01:48）刚总结“无新增事项、不空转检查已有效结果”；B:6 `d6a6c322`（12:02:57）又从 packet 的跟进计划出发 fetch origin、查看两 PR 状态。重复进入检查有实际可观察证据，但不是工具强制模型必须执行这些具体命令。

S1 的 turn 最终在 14:45 被记 unknown，另有 `braid-unknown-turn-replay-v1:…300ef0da48c9` 的修复重放事件；它不是上述两次 edit 当场生成的第二个 reset-continuation。本补审止于直接后继，不把后续恢复消息混入 11:56/11:58 的反馈成本。

## 3. 固定版本源码为什么产生此行为

| `1fabd11` 文件/行 | 可确认机制 | 对本例的意义 |
|---|---|---|
| `src/objects.rs:222–229,805–824` | writer 从活动 turn/session 解析；可见 title/body 真变化时记录 edited，并发 `Invalidate` | 哈希更新是实质可见正文变化；不是每次空 edit 都无条件制造事件 |
| `src/objects.rs:588–593,620–625` | 自写 **Wake** 可转 OriginEcho；**Invalidate 不走该自写抑制**，仍存 writer_group/turn | 有自写识别数据，不代表自写 edit 不会 reset |
| `src/store/mod.rs:4617–4653` | `continuation = selected_turn_id.is_some() || self_edit`；绑定 events→reset | 本例正在运行，已足以 `continuation=1`；此外自编辑即使 idle 也可触发续轮，不能把两条件混成仅自编辑才续 |
| `src/store/mod.rs:4750–4777` | refresh 把新 pending invalidate 追加到同 X，按 ordinal 累积 | 对应 1→2→3→4→5 条通知 |
| `src/group/dispatch.rs:605–653` | 每次刷新生成完整 notice，文本与上次不同才 `send_user_msg(notice,true)`；至少 3 秒检查间隔 | 避免完全相同 notice 重发，但新增同文 reference 会改变整个消息，再注入旧会话；不是立即终止重建 |
| `src/group/worker.rs:328–368` 与 `src/store/mod.rs:5030–5049` | 等 native completed 且证实 notice 被处理后 teardown，再将 reset 转 materializing | `interrupting` 这个 DB 名称不能等同于立刻中断模型；本例终态时间实际证明等待了当前 turn |
| `src/group/dispatch.rs:350–394` | 读取 canonical 当前对象，重新渲染，`context=rendered.text`，开启新 session | 当时没有后来新增的重建来源、自写标记前缀 |
| `src/store/mod.rs:5142–5157` | applied 后将旧 references join 成一个新 `wake/reset_continuation`，以 quiet=0/threshold=1/urgent 调度 | 上一轮已说“无事可做”，调度器仍按 continuation 布尔值续轮；它不判定是否还存在语义待办 |
| `src/group/provider.rs:101–134` | wake 一律“请处理”并要求 `view --comments`；reset notice 仅 reference | 外观上把保存自身状态后的恢复也包装成可处理更新，增加重新取数的诱因 |

后来 I11 的 `cells/readable-cli.md` 已明确修复“只提取 reference、不显示写入人”的问题；新源码/新 physical 有 own-edit 标记。**这些后改语义不能倒填 11:49 的实际输入。**旧版本已识别自写用于 continuation，但没将自写身份呈现给模型，是本例最容易混淆的两层。

## 4. 最强解释、反证与候选边界

**最强机制链**：root 把动态 head 镜像当作保持 packet 准确的责任 → 可见正文变化产生 invalidate → 同一运行 turn 收到累积提醒 → 更晚统一重建、丢开当前原生推理历史，保留最新工作资料 → continuation 发“请处理 / 全量读取” → 再进入状态核对。它包含 Agent 的可观察选择和运行机制的真实放大，不能简化为“提示词没教好”或“runtime 强迫反复 edit”。

**反证/限制**：

1. 固定指令已明确无需日常回填；reset 保存建议是有条件的。两条 target thinking 明确认出 own edits，因此仅增加自写作者标签不足以消除这两次错误取舍。
2. DB/runtime 没要求改 head、重跑测试或回复。新的 wake 强制了调度机会，模板要求查看当前内容，但采取多大行动仍由模型决定。
3. 工作资料里的“随时更新”与精确 SHA 易造成维护目标偏移；这是一条有原文支持的解释，不是证明唯一原因。未观察这些几分钟对最终评分的可量化影响。
4. 已有 anti-churn 文句不足以稳定兑现，但不等于再加一句“简洁”就能解决；I11 增强作者提示后是否足以改变行为，应由后段对照判断，不在本补审外推。

**提示/Skill 可收敛**：区分冻结候选/验收版本与正在移动的 head；后者引用 PR 元数据而不复制。明确“已完成的自己修改不是新待办；无未保存进展可直接结束，不用为保存而制造新状态”。把“维护入口”的触发条件写成决定、范围、责任、候选证据变化，而非每次 push。

**运行机制候选**：把“保证快照最新”与“必须再启动一次模型处理”分开；只含已由本 turn 写入且处理过的 invalidate 是否需要 continuation，须定义明确生命周期与未交接进展保证。不能直接删除全部自写 wake（会影响在途交接及外部夹入更新）。改善 notice 应优先给新增变更与自写归属，避免每次重新累积相同 reference；新会话说明快照已含变更、无需再读取或改写已有效内容。这些需要运行语义/模板改变，不能靠 Skill 保证调度停止。

本次仅提出有界候选，不实施。证据已足以区分自写选择、同会话 steering、统一 reset、自动 continuation 四层；无需扩大读取全部日志。
