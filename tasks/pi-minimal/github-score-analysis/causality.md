# 两条 Pi 原生决策链：2026-09-30 增量结论

本轮接续 [首轮报告](report.md)，只解释权限误解和 PR 里程碑范围丢失。两个有界 Agent 分别整理，主线回读关键原文后裁决；另行纳入的 I11 结果见 [独立报告](i11-e68661975b53.md)。不修改 variant、Skill 或应用，不执行下载内容，不运行模型或评测。

**主要修正：问题在原始需求转成设计表示时就已经发生；独立 advisor 又确认了其中的错误。** 因而“再提醒读全需求”“多装一个 Skill”“换 fresh 上下文咨询”不是这两条链的充分修复。可以改进的环节是：要求设计保留可反驳的对象集合和操作条件，并用原文导出的反例检查实际实现。

## 来源和上下文边界

证据根 `runs/analysis/pi-minimal-github-20260930/20260930T031746Z/c3fea0c3488c/`。

- **M**：`extracted/template/.factory26/pi-minimal/session.jsonl`，主 session `01a0efe4-7d83-7106-aa8f-3ee6679cb85c`，711行。行号均从1开始。
- **A**：`extracted/template/.factory26/pi-minimal/session/dc12f443-1021-4428-9573-e360a0e6112f/run-0/session.jsonl`，advisor session `01a0efea-1822-77f0-94ca-1fafda39f0ed`，52行。不要把衍生 transcript 的行号与这里混用。
- provider-facing 原文：`extracted/template/.factory26/pi-minimal/capabilities/{4d1d23e608c09e507ac5a875ac0518b5ae3799be2ec28297c063b2ff1f6aa99a,5e44ddb8d01cdbc4c3ef73bcda5eb74a37b6c8bd0d1e00aa5d2c25e63a5c9adc}.json`，分别对应 main 与 advisor。可读副本为证据根下 `provider-system-glm-5.3-flash.txt`、`provider-system-kimi-k2.7-code.txt`。

两份原生记录没有 compaction、branch-summary 或 session replacement 事件，parentId 链没有指向已取得文件外的缺口。主会话分块 read 的截断有明确后续 offset；相关权限与里程碑原文在 toolResult 中实际存在。这只排除**可见的读取缺口或本地压缩事件**，不证明供应商内部永远不截断。但最早错误在01:23:59就出现，晚期上下文过长无法解释它的起源。advisor 为 fresh 独立会话，输入是主线给出的5966字符简报及明确路径，不自动拥有主线历史。

## 权限：把“有效角色取最大”错误推广为“所有操作按等级放行”

|顺序（UTC）|原生位置|短原文与可观察含义|
|---|---|---|
|01:19:05.574|M:L10，`b0f41d25`|ROOT 已可见：`these roles are not an automatic cumulative ladder`。|
|01:19:29.422 / 01:19:34.063|M:L18 `a8a06e90`、L20 `c0eaa9e7`|Issue模块及具体操作原文已返回：Write可创建/编辑/评论，Triage/Maintain/Admin可分配/标签/里程碑/状态；Write不得执行后一组。|
|01:23:59.084|M:L30，`af8a7b56`|首次错误设计：`Role ordering: Read < Triage < Write < Maintain < Admin`，随即 `assign/label/milestone/close: Triage+`。有效角色计算和操作授权被用同一个序关系表达。|
|01:25:13.067|A:L21，`5a9ac217`|advisor 实际读取到：`Write can create, edit, and comment but cannot assign, label, set milestones, or change status`。不是只看了主线摘要。|
|01:26:11.604 / 01:27:46.488|A:L32 `24bfa834`、L42 `c1fa1843`|却判断 `The plan says "issue close needs Triage+" which matches. Good.`；之后又重复 `issue close Triage+. Good.`。这是可见的语义误判，不是工具失败或需求没送达。|
|01:26:59.783|M:L52，`c1bcc65d`|write perms.js 同时写下“不累积、应使用 explicit role sets”的正确注释和数值 hasAtLeast。说明保存了原则文字，却没有把它落实为这些动作的条件。|
|01:29:22.166 / 01:30:22.166|M:L62 `6967ec7e`、L63 `7480c445`|advisor 最终回传 `The plan is basically sound`，未提出该权限矛盾；主线记录采纳反馈。不能把 A 内部错误句当作原封不动回传，但实际反馈确实没形成纠偏。|
|01:34:15.777|M:L73，`140a5de1`|写 issues 路由，用 `requireIssuePerm(..., 'Triage')`调用等级守卫；标签、里程碑、状态处理都受影响。|
|02:41:58.907|M:L630，`7df791ac`|自审将“metadata pickers…gated by canTriage — good”当作依据。变量名字又替代了一次规则核对。|
|02:50:57.999|M:L699，`8588a1d1`|最终宣称按操作列出而“不做隐式阶梯”，与实际代码不符。|

该链支持的根因是**操作级授权条件被错误抽象，后续审查继续使用同一抽象作判据**。原需求允许对多个来源的有效权限作比较，不等于允许把每项操作的允许集合替换成等级下限；两个概念在这次设计中被混用。不能从记录进一步断定这必然来自模型训练中的GitHub常识或能力上限，也不能证明是有意降低要求。

后续可见验证覆盖过 Read、访客、正常 Write 评论/审阅等路径，却没有在这几项管理动作上留下 Write 拒绝的有效检查。主线另行回读M:L638–642：02:42:51 Read控件计数为0；02:43:00使用carol-maintainer成功关闭/重开，却把命令标作“as triage”；02:44:10便宣称“All permission gates verified”（`f738942f`）。这是真实但不具区分力的通过结果，不是假定所有检查都没做。Read拒绝不能区分正确集合与错误的Triage下限，两种实现都能通过它。这个解释比“测试少”更准确：缺的是有区分力的相邻反例。具体过程及已读边界见 [权限整理](permission-trace.md)。

## 里程碑：跨对象约束在模块化设计中被收窄

|顺序（UTC）|原生位置|短原文与可观察含义|
|---|---|---|
|01:19:29.422|M:L18，`a8a06e90`|模块说明明确 `may be associated with multiple issues or PRs`。|
|01:19:34.063|M:L20，`c0eaa9e7`|REQ-5-3-3 标题 `Assign Issues and Pull Requests to a Milestone`及正文 `issue or pull request`实际返回，未被50KB截断丢失。|
|01:23:59.084|M:L30，`af8a7b56`|初始schema只给issues列milestone_id；功能/路由规划把milestones置于issues组。同期明确把comments、activities设计为共享target_type，说明不是完全没识别Issue/PR共有能力；里程碑被选择性漏掉。|
|01:24:49.095|M:L36，`adf80123`|给advisor的简报在issues能力中列milestones，在PR能力清单中不列，范围收缩进入了对外设计交接。|
|01:25:01.958 / 01:25:13.067|A:L11 `cb501b13`、L21 `5a9ac217`|advisor grep虽有限幅，返回开头仍含 `issue or pull request`；随后read完整出现 `multiple issues or PRs`。不能解释为advisor完全不知道交叉范围。|
|01:26:04.421|M:L46，`219a38f0`|实际write db.js：issues有milestone_id，pulls无。第一次落地即未承接PR侧。|
|01:34:15.777 / 01:36:44.252|M:L73 `140a5de1`、L85 `b6b8b406`|issues路由有里程碑处理，完整pulls路由write参数无milestone。|
|01:51:12.752 / 01:53:32.948|M:L157 `ff222dc5`、L164 `87cc07cf`|IssueDetail有Milestone，PullDetail侧栏只有ReviewersBox、ReviewSummary、MergeBox。代码沿窄化设计一致推进。|
|最终审查/交付|A:L52；M:L699|advisor最终重点是控件语义、合并和环境等，没有里程碑范围纠正；最终声称全部“约30条”完成，而实际47条，未给可核验的原子覆盖依据。|

这条链支持**读到了跨对象需求，但转写成模块设计时漏保留，后续沿设计实现，最终检查也没有回到该并列范围**。没有记录明确说“PR里程碑太难所以删除”，也没有看到压缩删掉这一行；不能把遗漏动机编成时间压力、Ponytail删功能或上下文遗忘。原生L30有“大项目/尽快开工”的措辞，只能作为背景，不能当因果证明。可见的元数据检查主要落在Issue侧；一侧成功无法证实另一侧存在。具体证据与未读边界见 [里程碑整理](milestone-trace.md)。

## 系统提示、Skill 与 advisor 的实际作用

main 的 provider-facing system 明确给出了组织、认证、可访问性 Skill 目录，并要求匹配时读取正文（可读副本L38–40）。M:L4的实际任务提示已经要求原需求决定判据、实现前读相关Skill、重要方案咨询advisor。主线没有主动读取认证/组织正文，但advisor实际读取了这些指南；它还重新查阅了包含反例的公开需求。因此“缺Skill安装/缺路径/无advisor”已被反证；main少读Skill是执行偏离，却不能据此证明读后就能消除这两个错误。

Ponytail full 已注入两者的system；其原文同时要求不得简化掉安全、可访问性和明确需求（main可读副本L152–154；advisor L166–168）。没有证据表明它指示采用累积权限或只做Issue里程碑，不把它列为直接原因。组织Skill偏框架知识也不能替代此题操作集合；在记录中没有发现足以把这两处错误归因于某条Skill建议的链路。

advisor 的角色提示本来就要求挑战假设、找反例；fresh上下文也实际生效，但独立上下文本身没有产生独立判据。权限线上它看到精确规则仍对错误缩写作肯定判断；里程碑线上它看到了原文却没有检查schema两侧对应。这比首轮“建议没被落实”更强：至少权限部分，**建议产生之前的审查判断本身也错了**。

## 对首轮候选的修订

1. **保留并具体化需求保真要求。** 不再建议只追加“读全需求/不要遗漏”。在权限、并列对象这类会改变实现边界的决定上，留下一个从原文导出的可反驳例子或对象清单，再对应实际守卫/数据关系/入口。权限检查需要能区分集合与下限的拒绝例；并列对象各自至少有承接位置。通用指引不能硬编码GitHub角色和Issue/PR。
2. **改advisor的交付判据，而非增加泛化提醒或咨询次数。** 对这类决定让review返回“原文允许/禁止 → 一个具体反例 → 方案/代码会怎样处理”；只说“matches/Good/基本合理”不构成核验。里程碑则核对每个并列对象在schema和入口的落点。advisor已经看过原文仍误判，故仅补更多上下文不是充分方案。
3. 首轮“完整用户入口不能被直达URL代替”仍有独立搜索轨迹支持，但它解释的是发现缺陷失败，**不能当作这两条早期误设计的起源**。本轮不再扩展搜索调查。

这些调整应优先放在 `variants/pi-minimal/instructions.md` 的设计与验收交接、`agents/advisor.md` 的审查产物约束；不是增加通用Skill库或重写Harness。全部仅为候选，未修改文件。可以用本次已保存的原文和代码静态推演，检验新判据能否识别已证反例，不需评测额度或运行下载应用；要证明Agent今后会采用、是否提分，仍需另行授权受控实验。本轮也不能从2分推断换模型必然有效。


## I11 对照后的综合裁决

I11 `e68661975b53` 已独立核实为最终应用回放，4/100、1/47功能；其公开需求哈希与 Pi Minimal `c3fea0c3488c` 完全相同。详细身份、原始 ZIP、7份定向原生会话及来源索引见 [I11报告](i11-e68661975b53.md)。主线另外回读官网 status、184文件清单比对、M6a/M6b和根的原生关键消息，而非仅合并分支摘要。

|问题|Pi Minimal|I11|证据支持的改进方向|
|---|---|---|---|
|非累积权限|完整原文可见，主设计错写Triage+，advisor同向误判，验收未区分Write例外|最终显式允许集合排除Write，该处已正确；不能沿用Pi的归因|以原文导出的拒绝例检查实际条件；不能只审helper名字或“原则正确”的文字|
|PR里程碑|初设计缩到Issue，schema/路由/UI沿用遗漏|成员明确知道跨到PR，也知道M5只做了Issue，却按REQ编号反复排除；根看到排除后未形成承接闭环|前者要保留适用对象集合；后者要使范围排除对应一个确实接手的工作项，否则仍是根持有的未完成需求|
|版本与交付|冻结包身份已核，生成/部署完成|新binary确实启动和消费交接；最终184/184文件与冻结清单一致|没有证据把这里的已证功能遗漏归于旧binary或上传漏文件|

I11 主线回读的关键原文为 `native-preserved/3890f307-…jsonl:L55`（09-29 11:10:59.223Z，`9bf622c6`）的“Let me not overreach…issue #9 scope doesn't include”；`065faa32-…jsonl:L65/L68`（16:10:36.409Z `07cae554` / 16:10:55.282Z `a3ff1bd7`）明确“M5 didn't implement PR label/milestone UI”，仍称“it's M5's REQ-5 scope”；根 `b5c8efb3-…jsonl:L27`（16:19:35.716Z，`10a5036c`）收到正式排除声明。完整文件名及原tar成员见I11报告索引，不能拿回放ZIP当生成会话。

因此对 I11 的候选应再加一个窄约束：**成员发现需求跨出自己范围时，不必擅自实现，但“交给别人”必须有明确接手证据；没有接手者就保留为根的开放交付项。** 使用现有Issue/评论即可，不需新调度平台或模板库。最终核对对象能力，不能以47个REQ标签曾出现在验收文件中当作47项均完成。

关于binary，主线核验 `runtime-stalls/github/first-response/runtime-snapshot.json` 的实际哈希 `d76d65f1…`、三次握手完成日志，以及根原生 `…01a0f008-fd9b…jsonl:L6`（09-30 01:59:44.216Z，`5ee31ebe`）调用 `braid comment view 331/332`。故“仅新源码写好而未运行”与这些证据不符。最终main 442dc1仍只引用既有packet，未另核远端Git receipt；独立核实的是最终应用文件与官网一致。

共同可改进点是公开需求到最终交付的覆盖闭环；已证形成机制并不相同。2分和4分不能用来比较Harness优劣，以上缺口也不能在缺少官网逐例结果时解释全部98/96例失败。所有候选仍未实施，本轮没有新增评测或模型试跑。
