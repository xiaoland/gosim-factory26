# 在途提交号维护循环：可核查活动时间线

2026-09-30。有界追加调查，属于 GitHub run `e68661975b53` 的 I10→I11 同一 lineage；本段发生于 2026-09-29 的 I10 阶段。只读归档，没有执行记录中的命令。本报告引文来自历史参赛 Agent 的任务记录和工具结果，不是本次分析 Agent 的内部推理。

**结论先行：两次 hash-only 编辑是 Agent 自选的交接准确性维护；Braid 确实把其自身编辑变成持续输入和一次接续。** “必须每次同步在途 hash”并不是当时的明确指令。Agent 很快认出通知来自自己，仍以准确、便宜为理由继续。因此，来源不明只能解释最初的一次核对，不能解释后面的两次编辑。

**对旧报告的精确化**：不能把这段描述成“每次编辑立即新开 Pi 会话”。五次编辑绑定同一个 pending context reset；五次累计提醒先进入**同一 native session、同一 Braid turn**，原 turn 完成后才重建一次会话。后继收到五条修改的合并唤醒。以下用实际事件关联证明，不只凭先后时间推断。

## 原件与定位方法

共同前缀 `F`（相对项目根）为：

`runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`

- **P**：`F/work/native-homes/pi-glm-fast-01a0ecff-7bc8-75f3-ae03-c4d92e8e6561/2026-09-29T11-49-25-679Z_01a0ecff-8c2f-7379-8857-a3ff01afd017.jsonl`。全文 69 个 JSONL 记录；表中 L 指物理行。Braid session `01a0ecff-8d51-7222-a7f9-c4e5be750fe2`；turn `01a0ecff-907d-7752-8171-bcfe4491ec73`，11:49:28.271→12:01:48.856 UTC，completed。
- **P2**：`F/work/native-homes/pi-glm-fast-01a0ed0a-f546-7880-88cc-4124f66b22c1/2026-09-29T12-01-56-959Z_01a0ed0b-02de-77cc-a5ba-ff5e4f0f86a5.jsonl`，接续 session `01a0ed0b-04be-7170-9c69-2ff847bafa46`。
- **DB**：`F/braid-state/braid.sqlite3`，只读查询。`local_activity.ordinal` 是下表 activity 号；`local_comments.comment_id` 是 comment 号；reset/event 关联见下一节。
- 本次便于复核的摘录：[evidence/deepening-maintenance-records.json](evidence/deepening-maintenance-records.json)。含 P:L25–69、P2 的 5 条选定记录及对应 DB 记录；P2:L4 仅保留末 850 字通知，完整上下文仍在原件。本报告另回读 P:L4 的初始入口、P:L6–24 的触发和核对过程。

## 当时实际工作，而非事后套因

P:L4 `187e8672` 把根职责规定为“根统筹与最终整合”，当前明确有 PR19/20 两位实施负责人，两项均“候选开出后根核实…后合并”；没有证据、裁决请求时不是合并时点。该正文同时自己维护两 PR 的**实施中 checkpoint hash**，又声明正文为 task packet、“随时更新”；同一入口还有稳定的责任、合并条件、未决项。原始问题由此不是要不要维护 packet，而是哪些变化应当进入根正文。

此时 PR19/20 的版本本来能从 PR/Git 查得，且尚不是根待批准的冻结候选。P:L36、53 明确知道两 owner 正在执行、无事可裁。两次维护没有改变责任、范围、依赖、核销条件或下一步，只改变易变的 hash 副本。

实际加载指令为 `F/braid-state/physical/01a0ecff-7bc4-7a00-8822-5f4ecfd3cf03/instructions.md`（instruction revision `7935b9e44a7280b15cd5b35bfff20492968cbdd4067122e54790b9733159f8e8`）。L3 已写“交接前核对当前说明，无需把日常进度反复复制到正文”；L13 要求相关决定变化时更新；L21 说无新事实/决定无需重复总结。故不能将工作资料中的“随时更新”当成固定指令强制实时镜像。历史源码 `1fabd11` 与 physical、DB 的版本边界及具体行号见 [deepening-maintenance-mechanism-notes.md](deepening-maintenance-mechanism-notes.md)；主分析另回读了其中 `store/mod.rs:4617–4653,5142–5157` 和 provider/dispatch 的通知代码。

## 时间线（UTC）

| 时间 / provider 来源 | 触发输入与实际动作 | Braid 对应 / 后续 |
|---|---|---|
| 11:49:28–11:54:27；P:L4、9、14、25–29 | 初始批次含 #256/257/258 与较早正文修改；随后收到 #261/#263。实际查看 PR19/20、D12 修复和新文档问题。L25 `9e00bfba` 增加 D12 具体待办、责任与出处，同时同步两个 checkpoint；L27 `aa5973ae` 真正提交 `issue edit 1 --body-file`。这是**有新合并核对信息的编辑**。 | activity **489**，11:54:27.611。L30 `7a0f9673` 11:54:50.052 注入：“你正在处理的 Issue #1 有更新…当前会话结束后会用最新内容重新打开工作会话”，1 条 `title/body 已修改`。 |
| 11:55:13–11:55:25；P:L31–35 | L31 `9e62ac12` 尚不确定是自己还是他人编辑，查询正文、fetch。L33 返回 PR20 `32826b6→dc566cf`。L34 `aec3c922` 已确认“正文更新即我上一轮的 packet 编辑，内容完好”，仍查看 PR20 评论；结果没有新证据。 | 首次通知确实引出核对；此后已不能说 Agent 一直误认成别人的修改。 |
| **11:56:04–11:56:23；P:L36–39** | **`9c3a4129:L36`**：“Both owners executing; nothing for me to adjudicate or merge right now.” 同时写“repeated head updates each round create churn”，最终选“accuracy matters for handover. A one-line sed edit is trivial. Do it.” 工具仅替换根正文 PR20 `32826b6→dc566cf`。L37 工具确认 updated。L38 `b47c8a1b` 对外说明“本轮仅把…head…同步…（保持入口准确）”。 | activity **495**，11:56:05.751。L39 `cca563e4` 11:56:23.552 再注入提醒，列**累计 2 条**正文修改；不是一个新 Pi session。 |
| 11:56:37–11:57:25；P:L40–48 | 再核正文/fetch；L43 `81dce8dd` 认出都是自己、无新 push，仍查询评论。此次确实找到 **#264**（11:54:40.169，@deepseek-15，PR19 thread241）：从原 REQ-4-2-3 场景 2 重建“结果页内再次搜索”，发现既有 spec 只从仓库页发起，遗漏保留 repo/path/language。L47 `3553c1b7` 把该修复加入根合并核销清单。 | activity **497**，11:57:25.255。L50 `f2bc9202` 11:57:37.670 累计 **3 条**修改。此处有真实新事实，是重要反例；不能把五次编辑全部叫无效维护。 |
| **11:58:21–12:00:06；P:L51–56** | fetch 返回 PR20 `dc566cf→f3a97eb`，评论未变。**`d93a62f9:L53`**：“Body modifications are mine again…No new comments anywhere. Nothing to adjudicate.” 又说“Heads keep moving; frequent churn is low-value. But keeping the entry roughly accurate is my duty; a single sed is cheap.” 实际仅替换 `dc566cf→f3a97eb`；L54 确认 updated。L55 `37e8bd91` 对外：“两 PR 均无新评论…packet 已同步该 hash”。 | activity **498**，11:58:34.547。L56 `8f60eec6` 12:00:06.169 累计 **4 条**修改。这里直接排除“只因为没看出是自己编辑”的单因解释。 |
| 12:00:40–12:01:29；P:L57–64 | 又查询。发现 **#265**（12:00:10.663，@deepseek-15，PR19 thread241，reply264）：加入原需求“全页恰一个 Search searchbox”断言，确认264已采纳。L61 `d0ebf2af` 加该验收增量，并更新 PR19 head `eef31e7→e3c147d`。 | activity **502**，12:00:59.067。L64 `c68345a0` 12:01:29.718 累计 **5 条**修改。含实际验收信息，不能算纯 hash 维护。 |
| 12:01:34–12:01:48；P:L65–69 | fetch/comments 无变化；L67 `8a246dac` 再读正文两行确认。**L69 `2a22f1a7` 停止编辑**：“正文五次修改通知均为我历轮的 packet 编辑…无任何需要根介入的事项；不重复发布进度总结、不空转检查已有效结果。” | 五次编辑到此停止，原 Braid turn 12:01:48.856 completed。这个停止反例表明编辑并非硬指令强制；但此前自操作已安排接续。 |
| 12:01:57–12:02:57；DB，P2:L4、6–8 | DB 12:01:57.355 applied reset。P2:L4 `1b0b7d07` 12:02:02.484 重新得到完整对象投影，末尾“请处理 Issue #1”，列累计五次 `title/body 已修改`，并要求 `view 1 --comments`。P2:L6 `d6a6c322` 实际 fetch + view PR19/20。 | 新 turn `01a0ed0b-0d6f-7f33-9599-8e026b9191a2` 由 wake_batch 开始。只确认它已执行这些动作；终态归档 lifecycle=unknown，不宣称这一长 turn 最后正常完成。查询也发现 PR19 又有新 push，不能把后继整个会话算空转。 |

## 因果关联的 DB 凭据

五次编辑都由 root writer group `01a0eb68-0ed9-7ff0-a22a-52f93596e102`、**同一个 writer_turn** `01a0ecff-907d-7752-8171-bcfe4491ec73` 发出。每个事件 kind=`invalidate`、origin=`local`、reference=`issue #1 title/body 已修改`，依 ordinal 0–4 绑定到 reset **`01a0ed04-2bb9-77a0-a7be-49267dbcedb8`**：

| activity | event_id | observed_at | reset 内 ordinal |
|---|---|---|---|
| 489 | `01a0ed04-279b-7d73-9702-d751f8aae6a2` | 11:54:27.611262982 | 0 |
| 495（9c3a4129） | `01a0ed05-a6f7-7573-8722-afb04f40d12f` | 11:56:05.751105025 | 1 |
| 497 | `01a0ed06-dd87-7bb0-9894-cdc52ed3a53b` | 11:57:25.255047291 | 2 |
| 498（d93a62f9） | `01a0ed07-ec33-7941-b643-05296c247d5a` | 11:58:34.546844038 | 3 |
| 502 | `01a0ed0a-20bc-7ec1-8c28-8c11a9bdad0f` | 12:00:59.067654849 | 4 |

reset 于 11:54:28.664 创建，12:01:57.355 applied；`active_turn_id`、old/new session 与上文完全对应，`continuation=1`。后继 batch `01a0ed0b-04be-7170-9c69-3010998c86e0` 对应新 turn。归档中同 reset-continuation 的重复保留事件**不当作两次实际模型执行**。

这组 writer_turn→invalidate→context_reset_events→reset→wake_batch→新 provider 输入的连接，证明了 runtime 的反馈路径。**它不证明没有这些维护就会得到更高评分，也不提供节省 token/时间的反事实数值。**

## 根因辨别，及不能下的结论

1. **“系统命令强迫改正文”不成立。** notice 要求继续当前工作，并说有未保存进展“可写”；后继要求处理/查看，没有要求同步所有在途提交号。L36、53 是自选编辑，L69 能不再编辑。
2. **“机械通知被误读”只解释一部分。** L31/40 起初不知道修改来源；但 L34/36/53 明知来源是自己。更强机制是：根正文已同时承担稳定决策入口与 volatile checkpoint 副本，“准确交接”的一般目标被落实为每个副本尽量最新。决策中只计算一次 sed 便宜，没有显示把 downstream notice/reset 纳入该次选择的成本。这是可观察的选择框架；不能再推断其不可见心理动机或训练奖励。
3. **“长 description 本身导致失败”没有被证明。** 本段67k左右的初始对象投影包含很多历史内容，但两次关键选择明说知道无根任务、知道低价值，仍选择同步，不能简单归为没看见、截断或遗忘。没有这里发生上下文截断的证据。
4. **维护与有用协作交错。** #264 正是独立回原场景语义、拒绝被既有 spec 通过蒙蔽的成功例；#265补具体原判据。根消费这些增量是合理行为。有效通知策略应保留它们，不能一律消音所有更新。
5. **边界建议**：根正文保持责任、冻结候选/验收边界、待裁决项与 PR 引用；未 ready 的 head 由 PR/Git 查询，不为每次变化编辑根正文。自身编辑确认与“新的外部工作”应有独立 runtime 语义；是否需刷新上下文与是否需继续执行应分开。前者可用提示/Skill约束，后者要修改运行机制才可保证。更完整的上游指令与三条根因综合另见 `root-causes-deepening.md`。

## 覆盖限制

本报告完整排列这一个69记录 native session 的相关编辑/通知链，并读接续的首次输入和动作；精读关键工具、正文段落与 #261/263/264/265。DB查询只取对应活动、事件、reset、turn、session，未重扫全部归档、未逐字审阅每个既有业务评论。分析没有量化维护总开销，也没有把此12分钟片段代表所有运行阶段。原完整 lineage 覆盖口径仍见 [coverage.md](coverage.md)。
