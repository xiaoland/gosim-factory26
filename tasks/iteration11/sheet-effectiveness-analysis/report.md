# I11 Sheet：从需求到交付的过程与能力实效

本次能证实 SVC、advisor、vision、explorer 和 Braid 协作中存在具体有效消费，也能证实部分信息维护与验收决定没有收敛。不能把这些能力笼统判成“没用”，也不能把文件齐全、调用成功或本地 PASS 当作完整需求已满足。最强的改进依据来自运行当时的选择及后续动作，而非最终 59 分。

本文中的 Issue、PR、评论均为 **Braid 的 Agent 协作对象**，不是生成应用里的业务功能。时间均为 UTC。

## 1. 对象已唯一确定，旧调查的时间边界已修正

| 身份层 | 已核实事实 | 原始入口 |
| --- | --- | --- |
| 继承起点 | I10 Sheet，Braid run `20260929-042409-811f18d4`；并非 I11 从空白生成 | [恢复来源](../recovery-curation/sheet/packet.md) |
| I11 首次接续 | `pi-braid-i11--hackathon--sheet-db75cf2c3b82be`；PR14 已合入，但 root/PR13 启动失败 | [当时审查](../runtime-stalls/sheet.md) |
| 最终成功接续 | `pi-braid-i11--hackathon--sheet-396538bc0dda96`；source package SHA256 `4a048cc4041dab1621f6a233954a9c0e0954b57f8774bb39b4efe7bd1d160fdb` | [身份摘录](evidence/identity.json)、最终现场 `run.json` |
| 实际恢复 binary | `3056feb7a599addeb82e0250d6a0cc1e055d9e8e78f0151ca12ea75582605bf4`，`refresh_native_materials=false`；没有把 GitHub 后来的 `d76d65…` 启动修复部署到本题 | 最终 `recovery-provenance.json`；[封包回执](../../../runs/iteration11/20260930-completed-turn-resume/sheet/prepared/package-identity.json) |
| 最终交付 | PR13 merge/main `10cba2ad888fd60f283382158c1bfb00b0fad240`；被验 develop `5926059835b8ff0de1256957c4205f75a8861e35`；两者 tree=`1a18466bd63e2702b91663033a3e5d62d228de65`；root CLOSED，Braid quiescent | 最终 `braid-state/result.json`、本地只读 Git 对照、评论 #583/#588 |
| 官网末端核对 | submission `87acf1919de7`，run **[fe617f4f8526](https://arc-bench.com/runs/fe617f4f8526)**，`self_funded`，59 通过/41 失败、功能 8/24；平台三阶段完成，`tests=[]`，无逐例错误 | [原始 status](../../../runs/iteration11/final-replay-20260930/official/tasks/hackathon--sheet/status.json)、[重放 manifest](../../../runs/iteration11/final-replay-20260930/replay-manifest.json) |

因此，约 02:27 前后“部分 Sheet 使用旧 binary”的说法必须拆开理解：本题最后确实继续使用上述 binary，但 **已完成恢复和交付**；不能再沿用旧快照的“root/PR13 blocked、main 空树”，也不能把恢复成功归给后来未部署的启动修复。Pi Minimal `run6dc68bef2081` 的 40 分完全排除。

## 2. 正向过程：需求如何成为决定、分工和检查

原始需求是在线表格工作区：24 条 ATOMIC、100 个 scenarios，涉及工作簿/工作表持久化、行列结构、编辑与范围操作、公式、排序筛选验证透视；跨功能反复要求可见控件、精确名称/错误、成功后刷新保留、失败时原子回滚。原文的许多 WHEN/THEN 被占位短语破坏，308 是重复文本处数，不能当作 308 个场景。主分析已通读 [ATOMIC 原文摘取](evidence/atomic-requirements.txt)，未借隐藏评分还原它们。

| 阶段 | 当时可见问题 → 决定与动作 | 后果及能力消费 |
| --- | --- | --- |
| I10，09-29 04:24 起，理解与规划 | 根先读需求、`svc-design`/`svc-task-packet`，把九张图交 vision，把损坏场景、种子、技术选择和持久化交 advisor。advisor 发现 Region/Item/数字种子的冲突，区分可读 ATOMIC 与场景残骸。根形成 D1–D3：ATOMIC 为权威，最大一致种子，其余通过 UI 布置；自研网格/公式，稳定 workbook URL。 | advisor 增加了父输入未覆盖的种子冲突与持久化面；vision 未被当成功能证明。种子重置方式仍是假设。直接原文 `18163b83`、advisor `d40ffc1a` L25；根/基础消费链见 [继承 cell](cells/inherited-process.md)。 |
| 04:39–05:49，基础 PR2 | 发布 SQLite/事务、raw 与显示值、ARIA、API、快照、平台 Node 20 等共同约束；README 与 shared/types 承接一部分。通过实际安装/运行发现驱动版本及 ABI 差异，再锁定兼容版本。 | 共享基础可供 A/B/C 消费，环境反馈改变了依赖选择。与此同时，依据未知验收可能用模糊 A1 定位，把默认行数收敛到 6；这是**被猜测的评测行为影响产品默认值**的直接样本，不能由自建定位失败推出隐藏评测要求，也未证明 6 行损害产品。原请求 `5cd87956` L296、`3da2b2d4` L34，评论 #15，最终 README L45–56。 |
| 05:50–08:10，A/B/C 分工、实现和审阅 | A 工作簿/CSV，B 工作表/结构，C 公式。Issue owner 定设计/验收，独立 PR owner 实现；packet 保存接口、候选及待回归点。v1.3 发布到 Issue owner，却没有直接到 PR8 活动实现 owner；PR8 仍按旧版交接，之后主动读取、修订并随 helper 合入 rebase。 | packet/评论提供恢复入口，但“发布→投递→当前实现采用”不是同一件事。B 的原地 SQLite 位移预演暴露主键冲突后改两阶段位移；C 的 explorer 从逐格错误隔离要求出发，实测深嵌套抛出整表，再经 #147/#149 落到 `d6ca6d4`。这是独立反馈改变实现的正例。 |
| 09:34–11:50，D/E 与跨域回归（仍是 I10 继承） | D 承接范围/撤销，E 承接数据工具；C/E 在排序后公式引用语义上产生分歧，通过原需求、advisor、根裁决和共享原语发布收敛。B 的 C/E 合入后回归由明确 owner 承接。 | 接口及回归依赖是真实存在的，不能把这段顺序全部解释为“只有两个 agent”的错误容量模型。D/E 已实现并合入后，I11 不再重新开发这些功能。晚期补读见继承 cell。 |
| 11:51–12:05，PR13 设计最终验收（I10 继承） | 整合者把 24 条需求按域映射到已有用例，再补首页/编辑器 updatedAt 同值、通用数字错误文案、pivot 源删除与释放等跨域缺口，提交 `d07dd62`。B 二次回归已结案，撤销快捷键偶发失败被记录并交 D 核查。 | 验收不只是累计 PASS：出现了从需求补接缝用例的实际动作。但本地用例通过仍只证明这些判据及条件，不能凭“24 条均有映射”证明全部场景行为。 |
| I11，17:15–17:33，接续与 PR14 | root/PR13 未获得 Pi 身份；旧模块 owner 能行动。D 对 #553 的失败观察做延迟窗口对照：乐观显示早于撤销栈入账。以可见 Undo enabled 为同步条件，只改 spec，PR14 合入 `2dc4b9f`。 | 将问题归于检查时序有行为证据，并未为通过检查增加未要求的产品行为；同时旧 C/B/E owner 继续镜像候选与“无待办”状态。关键整合责任有人负责但**设施阻塞**，不能说模型不愿接手。 |
| 09-30 01:48–02:10，恢复、交接和交付 | PR13 恢复后读 #571/#574 和 packet，补两份文档形成 `5926059`，串行执行四门；按 match-head 合并，核对 main 树及启动；Issue4 和根分别显式关闭。 | 有精确候选、原始日志、退出值、树对应与后续消费者，交付链闭合。另一方面已有 PR14 同套件证据未被完整接纳，产生下节所述复验；根最终复核证据后没有再跑整套，是停止条件的正例。 |

## 3. SVC 是否真正发挥作用

**配置确实存在，加载路径不只有显式 read。** 最终材料包含七个 SVC 技能；advisor 原生模板直接内联 design workflow，explorer 内联 investigation，executor 内联 implementation。主角色指令要求 packet、共享定义、结果解释和证据适用性。实际 `materials.json` 的源文件哈希与已保存材料吻合；rendered role 因路径替换、扩展和方法追加而字节不同，不能误报为版本漂移。[材料核对](evidence/material-check.json)同时保存源哈希及渲染前缀核对。

| 对象 | 实际消费与贡献 | 没有做到的部分 / 归因界限 |
| --- | --- | --- |
| task-packet | B/C/D/E 将设计、owner、接口、候选、检查及未决点写入；PR13 恢复第一分钟直接 `cat tasks/pr-13-integration/packet.md`（`b8b333b0` L12），随后按其中缺失门继续，补记 PR14 决定（`f5731270` L42）。这证明 packet 被接续执行消费，而非仅存在。 | final main 的 B packet 仍自称“待 Issue 负责人验收”，依赖段仍写 C/E 未交付（L7、L41–44）；实际已合入并结案。PR13 packet 的最终结果仍主要导向讨论。有效历史证据与“当前状态”未充分分开。 |
| design / implementation / investigation 方法 | 根、B、C、E 显式读技能，局部实现前有数据库/环境预演；advisor 和 explorer 的返回改变共享决定或实现。 | 方法、角色指令和模型常识叠加，不能识别某个 skill 的独立净收益。大部分工作属于 I10，不能说是 I11 新增方法造成。 |
| verification / interpreting-results | PR14 保留旧序列失败与修正序列通过、候选及运行条件；最终四门结果/退出码齐全；根接受最终有效证据而停止重跑。 | 新文档已明确“新 commit 身份本身不使证据失效”，但 #571/#574 的旧纪律仍被后续继承；方法可用不等于冲突指令已消退。 |
| durable project docs | README 保存驱动/ABI、API、raw/显示值接缝，shared/types 及共享函数形成可消费权威；确实支撑实现分工。 | README L5 把全部设计指回根正文+comment1；PR13 packet L5 又要求回溯 thread1 v1–v1.6 全部增量。版本化项目知识只落地了一部分，读者仍须重建讨论时序。B final packet 的旧状态进一步增加解释成本。 |

对完整采集的 native JSONL 建立消息身份索引后，I11 阶段未见新增 `svc-*` 路径读取；这仅限制“本阶段新调用技能”的声明，**不**否定内联方法、主角色指令及旧知识的作用。[调用导航](evidence/svc-calls.json)是搜索索引，不是全文阅读账。

## 4. Pi 子角色：配置、实际输入输出与影响

Braid 的 `glm/deepseek` 工作项负责人，与 Pi 内部 advisor/vision/explorer/executor 是不同层。最终主角色仍为 GLM-5.3-flash / DeepSeek-v4-flash；以下均是 Pi 原生角色。

| 角色 | 冻结配置与实用情况 | 可确认贡献 | 局限 |
| --- | --- | --- | --- |
| advisor | kimi-k3 / high，fresh，只读工具，内联 design workflow。继承子会话首条 model_change 实际为 factory26/kimi-k3。输入含原需求、歧义、约束、候选及待决点。 | 初始种子冲突、显式行列/规则迁移/透视三态；B 结构与 selection；C 错误/复制引用语义；后期排序分歧。决定发布、共享接口和实现消费形成链。 | 有建议未变成已证事实，例如未知种子重置方式、隐藏定位器假设、库方案冲突未实测。认同不能代替行为验收。没有把另一个 GitHub run 的 advisor 路由故障套到 Sheet。 |
| vision | deepseek-v4-flash-vision-exp / high，read only，无 skills；继承记录实际匹配。输入给定截图、需求背景和具体疑问。 | 带图片来源的布局、菜单、字段与无法确认项被写入 packet；明确中文参考布局不替代英文 ARIA/错误文案。 | 截图无交互结果的地方保留未知，不能用 vision 证明持久化、公式或范围操作。I11 没有新调用，不能验证本轮 vision 截断修复。 |
| explorer | deepseek-v4-flash / high，fresh/read only，内联 investigation。C 将 `c340e2e`、#107 判据、限定文件和返回格式交给它。 | 原生 `622e40fd` L74 保留具体行为反例和“不曾执行 e2e”的边界；#147/#149 消费后，`d6ca6d4` 加递归预算、逐格防护与回归。 | 独立执行机制增加证据，泛读同一代码或同意同一判据本身不增加独立性。极端输入发现不能自动解释最终失分。 |
| executor | deepseek-v4-flash / high，读写工具、implementation workflow 均已配置。 | 完整已采集调用索引未见 executor 委派；实际应用编辑由 Braid PR owner 完成。 | 不能将 PR owner 写代码算作 executor 成功，也不能从未调用推断模型能力差或必须增加调用。 |

**I11 新阶段没有新 spawn。** 唯一 subagent 工具行为是 `e3504f2b`（09-29 17:19:28，L13）查询旧 advisor run `524072e5…`。因此能评估的是继承角色输出如何影响 I11 所接成果，不能宣称 I11 新编排、等待或 advisor 修复已经获得行为验收。[全量调用索引](evidence/subagent-calls.json)保留 workflowScript，已检查其中角色，避免只数 `agent` 字段漏掉 fanout。

## 5. 三条直接可复核的因果判断

### 5.1 正确诊断被交接纪律削弱：修好检查后又丢掉可用证据

#553 从具体撤销失败提出“可能时序竞争”；D 实际拉长提交窗口，旧序列失败、新序列成功；PR14 在 `18cfeab` 留下 non-skip 68 passed 与 unit/typecheck。PR14 owner #574 正确接受这些证据而没有自己重跑，随后却要求整合者在新 head 再取数。

主分析只读 Git 确认：`18cfeab^{tree}=2dc4b9f^{tree}=0c61a1c…`；`18cfeab..5926059` 仅两份 packet。PR13 原生 L9 先读 #571/#574，L54 于 **01:50:32** 启动四门；根 #578 于 **01:51:58** 才发出。因此 #578 是强化已有要求，不能说它单独触发复验。#582 最终用旧 `d07dd62` 作比较，指出套件变了，于是全部重跑；没有给出已有 `18cfeab` non-skip 结果失效的具体条件。

**可确认**：交接看到了 PR14 证据，却未完成对最新已验产物的适用性判断；把分支/提交变化和检查有效性部分混为一体。**不能确认**：所有复跑都多余。skipbuild 和完整平台路径此前确有缺口；新的工作区/环境可能构成理由，但本轮没有明确提出这样的区别性需求。优化应补“原观察→当前候选→剩余义务”的决定，不能简单禁止复验。最终根 #588 仅复核对应关系即关闭，是有效停止的反例。

### 5.2 已完成 owner 镜像全局状态，使维护本身继续产生工作

I11 #567/#568/#569 明言“无剩余动作”，却继续核当前 develop、复算证据、修改旧 PR 正文再发回执。#569 直接记录触发是“本 PR 正文更新（我自己的编辑）”。B #575/#577 也反复更正已经完成 PR9 的当前全局候选指针。SVC要求当前事实可恢复，但这里落成了多处对象都追逐同一个集成状态。

**可确认**：注意力用于维持没有本域变化的投影，且 self-edit→新上下文/通知→再核对链仍可见。**解释**：根任务的当前集成状态与历史模块交付记录职责混在一起，通知呈现又使“已经包含的变化”看起来像处理请求。**替代解释**：部分更新确为修正引用错误或履行承诺，不能全部删除；本轮也有读完不回复的正例。新 binary 未应用到 Sheet，不能把所有现象归为它的回归。

### 5.3 有独立 reviewer，但独立性取决于它提出了什么可区分观察

从 REQ-4-2-2 的“错误格不阻断其它格”出发，C 交 explorer 的不是任意找 bug，而是既定候选与逐项语义；explorer 保留实测异常、没有运行 e2e 的边界，PR owner 之后修复并取得正式反馈。这是真正改变实现的贡献。与此相对，旧版本契约的互相确认、同树哈希复算、advisor 对隐藏评测的猜测，即使多人赞同，也不能增加对需求满足的证据。

**缺口**：无法从这些案例识别 SVC 或某个模型对分数的独立效应；没有对照实验，也没有官方逐例反馈。更合理的分析单位是“某个问题的返回是否改变下一步及其证据”，而不是角色调用次数。

## 6. 少量优化候选（未实施，不承诺提分）

| 归属 | 基于现有证据的候选 | 下次有授权运行时的判别证据 |
| --- | --- | --- |
| 提示词 / 当前协作交接 | 在接续时清退对象正文中“head 变就重取”等与现行方法冲突的纪律；交接明确**原始已验候选、当前候选差异、环境变化、仍缺的需求观察**。保留旧观察原身份。 | PR13 类消费者能明确接纳/拒绝最近有效证据并说明原因；skip/platform等真实缺口仍完成，不仅少跑一次。 |
| Skill 应用 / 文档职责 | 复用已有 documentation/task-packet 方法，明确集成 owner 维护当前全局状态；完成模块保留自身交付、约束和证据，不持续镜像 develop。最终 packet 退役旧“待办”并指向交接。 | 新 owner 可从一个当前入口恢复；C/E 已完成不再在 main 的 B packet 被标成未交付；一次候选变化不再引出多份无本域变化的回执。无需新模板体系。 |
| 运行机制 | 沿现有 reset/通知改进范围检查“更新投影、接续未完工作、投递真实新输入”的区别；呈现作者、已包含状态和变化，避免自行整理制造新的泛化处理请求。 | 同类 self-edit 后没有重复实算/回执；外部新的实质缺陷仍可联系旧 owner。不能以屏蔽已关闭成员所有通知替代。 |
| Skill / 判据应用（较低优先级） | 对未指定产品默认值，记录需求/用户体验依据；模糊 locator 首先修观察方法，不将未知 evaluator 假设升级成产品规范。I11 interpreting-results 已写此原则，应验证消费而非再加同义句。 | 类似 A1 歧义能在保留合理产品数据规模时取得精确观察；必要的未决假设保持可见。未证本例默认6行导致官方失败。 |

## 7. 证据边界与交接

官方 59/100 与功能 8/24 是这份冻结交付的末端事实；三阶段完成排除了“尚未启动评分”，但没有逐例错误，不能据此把 41 个失败归给上述某项流程、接口或应用行为。原始/派生 application hash 使用不同算法字段，本报告以明确的 commit/tree、source package 及 replay 来源链绑定身份，不把哈希字符串跨算法比较。

本次先由两名有界子 Agent 整理 [继承链](cells/inherited-process.md) 与 [I11 链](cells/i11-collaboration.md)，主分析再回读关键原文、需求、Git 差异、真实结果文件和最终状态。详细主审范围见 [reading-map.md](evidence/reading-map.md)；所有评论的编号/行号在 [comment-anchors.json](evidence/comment-anchors.json)，关键消息的完整文件路径、消息ID和行号在 [message-anchors.json](evidence/message-anchors.json)。旧全过程报告只作为其既定截点内的复用证据；本报告不声称重新全文审完所有 native。

最终必要现场已下载到独立目录，采集清单含 5596 文件、302177761 bytes，逐文件SHA核对一致；集合是已结束运行的只读采集，不宣称可恢复的原子检查点。已采集材料满足本次判断，无访问阻塞；未回读的其余原生内容不能算作已验证结论。没有运行应用、Factory/Braid测试、评测或模型，没有修改 variant、原运行、其他报告或推送/提交。
