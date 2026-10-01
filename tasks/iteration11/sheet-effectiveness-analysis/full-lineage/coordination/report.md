# Sheet I10→I11 完整协作 lineage：协作对象、上下文与决策可见性

## 范围与结论

本报告以完整只读 DB 状态、04:24–08:24 的既有全读账，以及 08:24 后 ABC/base/根的有限语义抽查为基础；D/E、PR13/14 的后段原生材料只引用已登记的跨链 comment/event，不宣称本报告已全文阅读。报告分析协作对象如何组织可见信息，以及 description、关系、评论、hide/resolve、订阅、指派、关闭和 context rebuild 怎样改变下一步决策。它不是评分归因；末端四门和交付只作为 lineage 的终点身份核对。

最重要的结论有三点。第一，Sheet 的对象图在 DB 中可完整辨认：根 `issue:1` 下有五个子 Issue，8 条 issue→PR 关联，最终 PR13 合并到 main；但“当前正文”是压缩后的快照，不能替代事件顺序。第二，既有全读账和本轮抽查显示，契约增量、独立复核、状态通知和上下文重建在链路中都改变了可见入口；D/E 的具体后段消费仍以主线补读为准。第三，DB 能明确指出“当前权威版本 + 受影响消费者 + 事件原因”没有总是落在同一可见对象上；这构成后续补读和改进检查边界，不能直接推出所有消费者都失败。

## 需求到对象图

04:24:17 创建根 Issue，04:41:40–41 创建 A–E 五个 child，并以 `parent_added/child_added` 成对动作写入 `local_activity` ordinals 8/9、11/12、14/15、17/18、20/21。根最初的共享契约和协调批次是 comment #1/#2（`evidence/comments.md:2,55`）：基础 PR2 先行，A/B 并行，之后 C→D→E，最终整合 PR。根把损坏的场景动作视为不可恢复、以 24 条 ATOMIC 描述为权威（comment #1 正文中 D1 段；当前 Issue 正文由后续 revision 50 保留）。这一步有效地把不完整需求转换为可执行接口与验收清单；但它也把“共享契约评论 + 各 Issue 正文 + packet”分散成多个事实载体。

05:50 基础 PR2 合入 `698afd2`，A/B 被指派；local activity 记录 `assigned`、`linked_pr/linked_issue`、`merged/associated_pr_merged` 的严格时间顺序。A 先创建 PR8（06:01），B 创建 PR9（06:05）；A 的设计交接 comment #29（`evidence/comments.md:569`）把需求、分工、验收和分支绑定在同一交接点，B 的对应 comment #41（`:842`）也这样做。这个交接格式有效，因为实现负责人能从关联 Issue/PR 找到判据和基线；失效处在于交接后契约仍继续变化，旧的交接文本不会自动变成“已读最新版本”。

## 时序信息/动作流

| 时间（UTC） | 对象与原始动作 | 对谁改变了什么 | 证据 |
| --- | --- | --- | --- |
| 04:24–05:50 | 根契约、协调入口、平台依赖核实；PR2 实现与合入 | 所有消费者获得 v1；基础合入成为 A/B 前置 | `local_activity` ord 1–45；comments #1/#2/#3/#22（`comments.md:2,55,73,387`）；PR2 merge event `01a0eb9f…` |
| 05:50–06:17 | 指派 A/B；A/B 设计、跨域请求；A 候选 d536aa2 | A 收到三条变更路径；B 将 helper/尺寸边界交给基础层裁定；实现者开始按旧/局部契约工作 | comments #27/#35/#38/#54/#57/#60/#62（`:460,703,873,1142,1198,1251,1275`）；activity ord 46–111 |
| 06:34–06:53 | 根核查 A 候选缺 Y-min；契约 v1.3（A-4 导出末换行）；补交后 PR8 合入 `e63efc6`，Issue3 关闭；C 指派 | 独立检查阻止带缺项候选进入合入；A 的显示值接缝、导出和 README 义务交给 C/整合 | comments #64/#65/#90/#96/#98（`:1331,1356,1941,2071,2124`）；merge/close activity ord 119–157 |
| 06:53–08:10 | C 设计与 PR10；基础、A/B/C 多轮只读复核；PR10 合入 `a592c3e` | C 把显示值、公式引用重写、tail expansion、错误串等契约落到共享 helper；A/B 被通知“无动作”但仍需更新载体 | comments #96/#100/#112；events kind `mention/invalidate/wake`；PR10 merge event `01a0ec…` |
| 08:09–08:24 | 根 progress/reset 与系统断连窗口 | comment #172/#176、invalidate blocked、wake superseded；根旧 session 未完成 reset，不能从后继状态推断其当时判断 | comment #172 `comments.md:3851`、#176 `:3929`；blocked reset `01a0ec37-80e9…`、blocked event `01a0ec37-7b44…` |
| 08:24–10:35 | 基础/A/B/C 旧 owner 续段；D 设计、PR11 创建；B/C 对 tail paste 和接口边界做反例复核 | 抽查到的续段显示部分 owner 读取新正文并作出“无动作/交接”判断；D 侧具体交接只以已登记 comment/event 作为跨链线索 | 本轮索引范围见 `coverage.md`，语义抽查见 `semantic-excerpts.md`；comments #220/#228/#230/#237/#245/#262/#286/#289（`:4783,4991,5053,5266,5469,5863,6284,6332`） |
| 10:30–10:35 | PR11 合入 `4e1a7bc`；Issue6 关闭；C 隐藏误发 probe2、Issue5 关闭 | D 的“tail expansion 不改 raw / paste 409 原子性 / undo”进入 develop；隐藏 probe 不再干扰讨论，但其存在仍是历史事实 | activity ord 537–558；comments #304 `:6730`、#307 `:6808`、#309 `:6840` |
| 10:35–11:50 | E 指派，PR12 创建；pivot sentinel、RT 排序引用、显示值单点反复裁定；PR12 合入 `ca69b7b` | 已登记的跨链 comments/events 记录了裁定、责任转交和后续状态；E 后段原生消费链不在本报告语义抽查范围 | comments #331/#338/#366/#375/#396/#399/#406/#411/#413/#421/#423/#424/#428/#429（`:7359,7572,8211,8407,8911,9027,9176,9309,9382,9555,9603,9616,9742,9775`）；PR12 merge event `01a0ed00-405b-7d32-92c5-d27cddc6ea86` |
| 11:51–12:05 | A/C 旧 owner 出现 blocked reset/pending mention；C 载体重取与收口；外部 offline packet edits | 最新通知存在但不一定到达旧 owner；正文和证据目录继续收窄，C 的验证范围落到 PR12 合入树 | blocked reset `01a0ed01-af48…`、`01a0ed0d-dcfb…`；comments #503/#516/#524/#536（`:11698,12026,12260,12619`） |
| 17:25–17:31 | PR14 创建/合入 `2dc4b9f`，D 侧记录 undo test timing 修正；B/C 只读复核 | comment/event 链记录了“套件变化后重跑”的责任决定；本报告不把该决定升级为独立必要性结论 | comments #553/#570/#571/#572/#574/#575/#577（`:13152,13590,13618,13630,13663`）；PR14 merge event `01a0ee35-d4f0-7781-a69b-6950df67432a` |
| 01:48–02:10 | PR13 最终候选 `5926059` 四门通过，merge `10cba2a`；B、根显式关闭 | PR13 交接把候选、退出码、四门与证据入口绑定；随后 root/Issue4 关闭 | comments #578/#582/#583/#584/#585/#586/#587/#588/#589（`:13722,13753,13791,13815,13846,13859,13869,13888,13910`）；PR13 merge event `01a0f…` |

## 描述、关系和评论怎样改变可见性

`local_items` 是当前快照，`local_activity` 才是可用的追加历史。最终 14 个对象均为 Issue CLOSED / PR MERGED，revision 从 2 到 68 不等；根 revision 50、A 48、B 28、C 68、D 7、E 33、PR13 5。编辑活动 374 次，但活动明细只为 `title/body changed`，因此“某版本何时存在”可以确定，“旧版本正文逐字内容”只有 native JSONL 的相应工具回包能恢复。不能用最终正文解释早期 owner 当时看到的内容。

关系表中 8 条 issue→PR 关联均 active：根→PR2/13，A→PR8，B→PR9，C→PR10，D→PR11/14，E→PR12。关系在 `local_activity` 中成对写入 `linked_pr/linked_issue`，随后另有 `associated_pr_merged`；这使负责人能从 Issue 找实现候选，但 merge 后关联不会自动消除旧的“待交接”文字。实际反例是 A/B/C 的正文在后期仍保留“待裁/待复跑”段，直到 owner 读到新评论手工窄改。

589 条评论中 586 visible、3 hidden、0 deleted；所有评论当前 body 均非空。28 条评论挂有 `resolved_through`，其中代表性链是 PR11 comment #220 最终由 #304 resolve、PR9 #286 最终由 #559 resolve、根 progress #579 被自身收口 resolve。生命周期管理的原生实证还包括 #470 所在文件 `work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl:53–69`：`1a02d6be` 识别 resolve 目标，`f2bd639a` 的多参数 unresolve 失败，`01f7b9ae` 分别成功，`f227e4f2` 编辑 #470 纠正，实际折叠了 #314/#331。该链说明 resolve/unresolve 的参数和替代关系会改变当前可见线程；它不支持推导下游丢失信息。三条 hidden 是：Issue5 #307 的误发 probe2（`:6808`，隐藏理由明确写出）、根 #338 的 shell 反引号损坏正文（`:7572`，由 #339 替代）、根 #414 的 A/C 重复答复（`:9399`）。hide 的理由和 replacement anchor 足够解释“谁看见什么”，但默认 UI 仍需显式显示 hidden/替代关系才能避免读者以为评论缺失。

投递上，2,041 delivered、12 queued、174 unreachable。169 条 unreachable 的 reason 是 `@glm-1 was reassigned; current assignee: @glm-9`，说明根从 glm-1 迁移到 glm-9 后，旧订阅/旧 mention 产生了失败投递记录；这不等于内容消失，也不能仅凭 unreachable 推导下游没有消费。18 个 mention event 在最终 DB 仍 pending，主要来自 11:51 后 A/C 旧 owner 的通知和最终关闭时对已结束成员的 mention；它们只证明当前未完成投递/消费闭环。`events` 另有 28 个 superseded wake、3 个 blocked invalidate；因此“评论已写入”“已投递”“已消费”必须分开核对。

订阅表保留 23 行，21 active、2 inactive：A 负责人 deepseek-5 与根 issue 的 deepseek-3 在 A-3 文档落地/监测结束后退订；其余订阅多为 assignment 或 explicit。这个机制在 A-3 监测中有效：Issue #1 的契约裁定、A-3 文档替换和 PR12 合入树复核可以指定 deepseek-3 作为单一监测方，最终由 #503/#522 路径退订（comment anchors `:11698` 与 `:12193`）。但 subscription 变更不是评论正文的一部分，后继者必须同时读表和 comment，才能知道通知责任是否仍在。

## context reset 与“谁看见什么”

DB 共 359 次 context reset：356 applied、3 blocked；338 continuation、21 fresh；672 条 reset-event 绑定。后 08:24 仅基础/A/B/C/根就有 17、17、28/25、13/44、35/44 次 reset（Issue/PR 顺序如覆盖账），说明“旧 owner 续段”不是单一新工作项，而是高频 session 重建后的连续观察者。

重建会保留当前可见正文和部分事件，但不天然保留“为何触发”。于是相同机制出现两类结果：

- 有效线索：已抽查的 A 刷新片段显示 C 合入后 A owner 收窄任务；#228、#423/#424、#582 则由 DB/跨链登记提供后续版本线索。由于后两组后段原生材料未在本报告全文语义复核，它们只作为可追溯线索，不升级为完整消费证明。
- 需保留的异常：根 #338 的正文因 shell 反引号损坏后由 #339 替代；A #414 与 #413 语义重复并隐藏；C Issue5 #307 是探针写错对象后隐藏。blocked reset `01a0ec37-80e9…`（旧 session unknown）、`01a0ed01-af90…`（Issue3 session unavailable）、`01a0ed0d-dcfb…`（Issue5 session unavailable）在 DB 中没有对应的后续消费记录；这不能证明旧 session 断点前没有作出决定。

context revision/hash 在 reset 表中前后成对保存，能证明新 session 是否接续同一上下文；`writer_group/writer_turn/recipient_revision` 在 event 中能追到生成者与接收 revision。但当前工具呈现若只给泛化“当前调用已失效/对象已更新”，就会让 owner 再次猜测变更来源。应把 reset 快照中“作者、变更 comment/event、是否已包含在当前正文、下一步 owner”作为一组元数据展示。

## 写作、通信与责任分工的有效/失效样本

有效样本线索是契约增量与独立验证形成“决定→消费者→证据”闭环。早期全读账和本轮已抽查片段支持基础层、A/B/C 的部分链路；#237/#245、#286、#289、#396/#406 等后段内容主要来自已登记 comment anchors，D/E 的原生消费仍需主线补读确认。角色责任是否改变候选或验收范围，应以各原生片段与 DB event 对齐后再升级证据等级。

需补读验证的风险样本是责任存在但载体可能不同步。已抽查的 A-3 刷新片段显示 C 合入后 A owner 收窄任务；#228、#286、#338 及 progress comments #164/#166/#172/#288/#579 的 DB/评论状态则显示正文、评论和事件在不同对象上演变。它们支持“需要同时核对载体”的判断，不足以单独证明某个下游消费者丢失信息。通信问题的可检验边界是评论、正文 revision、delivery 和 reset 原因是否能在一个交接对象上绑定。

在“无动作”责任上，已抽查的 B 片段和 #230/#262 登记内容给出“读到当前事实、PR 侧无动作”的样本；不能把它推广为所有 owner 的消费证明。DB 同时存在不同新事件、superseded wake、queued/unreachable delivery，不能把它们都归为同一消息重复唤醒。合理的完成条件应允许负责人写出“我读到版本 X；受影响面为空；不再回复”，并让系统把该消费状态与事件关闭绑定。

## 可检验的改进边界

1. 把每次 description 编辑、评论编辑、resolve/hide 的“当前版本、替代版本、受影响对象、是否已被负责人消费”写入一个可引用事件；保留正文历史或至少保留前后 digest。验收：随机抽取 #338/#414/#228，后继 session 不需猜测即可找到替代关系。
2. 将 assignment/subscription/delivery 状态放入交接快照，区分 queued、delivered、unreachable、superseded、consumed。验收：根 glm-1→glm-9 后，旧事件不会被计为“未读任务”，新负责人能看见当前 revision。
3. context rebuild 通知带作者、变更范围、已包含标记和下一步责任；timeline 分页明确“当前页/仍有后续”。验收：自编辑后同一 owner 能直接识别已完成写入，外部实质编辑仍产生一次动作。
4. 继续使用 Issue→PR 关联和独立复核，但把“契约增量”单点化为可版本化正文；评论只引用增量 ID 和消费者清单。验收：A/B/C 旧 owner 续段能按版本读到同一判据，重复确认下降而跨域反例仍能改变实现/门禁。

## 最终状态与证据边界

最终 DB 显示 Issue1/3/4/5/6/7 `CLOSED`、PR2/8–14 `MERGED`，PR13 merge `10cba2ad…`，对象和关系与最终源码身份一致；PR13 #582/#583/#588/#589 的证据入口位于 `comments.md:13753,13791,13888,13910`。这只证明 lineage 的收口身份及证据对应，不把四门结果外推为协作机制的净评分因果。`local_run` 仍为 `running`、18 mention pending 和 3 blocked reset 也应在后续报告中保留，不能被“根 Issue closed”覆盖。后段原生语义覆盖等级和未读范围见 `semantic-excerpts.md`。
