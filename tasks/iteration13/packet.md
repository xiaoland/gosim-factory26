# I13：Braid、子Agent与协作方法改进

2026-09-30。当前阶段：[CLI C01—C04](repair-design.md)与[上下文重建核心机制](context-implementation.md)分别获准开工，源码及技术文档已完成，整合编译和归档只读操作通过；真实运行行为尚未验收。[正文折叠与根提醒整理](materials-plan.md)源码与文档已完成，编译和已有归档只读反馈通过，新增折叠/提醒行为仍待实际验收；用户最新清单已与原问题树核对，角色、SVC、协作方法、需求树及提示词方案已同步；子Agent简化批次已在独立I13完成并提交7f8ad6e，编译和实际材料生成通过，真实委派未验；[SVC批次](svc-skills-implementation.md)已完成并提交（SVC a0af6e1、Factory 1a377c9），源码及实际材料已独立核对，executor原生说明修正已提交84344b4并通过补丁/编译/材料核对，真实并发与收益仍待验，实验未启动。冻结I12材料未变；用户确认手动恢复后已再次暂停，现场状态见下方接续记录。Console已移交独立[实验设施任务](../braid-console-control/packet.md)，已部署，不计入I13问题或完成条件。
用户原话：“那么将G01/G04/G05纳入I13的范围内”。这条指示确定本轮范围；实施及实验仍按仓库约定在具体影响呈现后取得开工依据。

## 本会话接续（2026-09-30）

用户要求从[原会话](codex://threads/01a0bcc1-62fe-79b1-87d4-5d8a9d1199ed)今天10:00开始的消息及相关tasks资料接续任务，handoff到[本会话](codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2)。已回读该时间范围32个turn中的44条用户消息及最终回复，并核对本packet、修复方案、各实施记录、上游调查和独立Console任务。主线职责从本会话接续；原会话历史保留，不向其发送续做消息，不移动共享checkout。

消息摘取在 `runs/iteration13/thread-handoff-20260930/source-messages.json`。原会话显示缺陷的根因未定位；本次解决工作接续，不把旧会话的completed状态当成用户确实收到回复的证明。

| 已取得的具体指示 | 当前效果与接续边界 |
| --- | --- |
| “先别急着修复……最后我们再来一起（分批）核对方案并修复” | 沿用分批复核。方案认可与具体开工授权分开；本次handoff不自动批准剩余源码、实验或提交。 |
| “其根本是要有‘元理论’……按照该方案进行修正；你整理一下工作区、提交还有task packet” | V&V与相关整理已完成，SVC `31906a5`、Factory `b8b4915`/`27612ba`保留；不是后续所有dirty改动的提交授权。 |
| CLI“可以开始应用了（交给sub-agent；我们还要继续讨论）” | C01—C04源码、文档及只读反馈已完成，实际写操作未验；不重复实施或切换I12 binary。 |
| “仅有description……comment、relationship、title等都不重建”；“我同意你对上下文重建的这套判断，可以应用修改了” | CR01—CR12已整合，原生恢复连续性边界已记录；真实重建、休眠resume、unknown恢复及并发投递仍未验。 |
| “executor……应该自动继续排查”；“可能是SVC task-packet没有发挥作用” | 入口成本来源与实际未读证据已形成；修稿设计归executor/task-packet各cell，净收益与行为采用不能凭材料修订宣布通过。 |
| “braid console的修改方案不需要我复核，可以直接应用” | Console独立维护。已在本次接续完成此前待部署的讨论根入口；不修改Braid或冻结运行材料。 |
| “I13实验时做多一个variant，使用glm5.3作为root issue agent” | 保留基线和仅根Braid session改模型的对照；未创建或启动I13实验。 |

接续起点校准：20:18 CST的实际Console API显示GitHub Running=true/Paused=false、PID 5217，Sheet Running=true/Paused=true、PID 5181。原journal记录GitHub在19:25:33 CST通过 `runtime_resume` 完成恢复，容器身份和StartedAt未变。当时不能沿用旧“两个I12均暂停”判断；之后用户确认手动操作并再次暂停，核验见下文。本次未执行pause/resume、业务写入或I12热部署；后续物理控制由用户明确操作，状态归[I12 packet](../iteration12/packet.md)。

工作区起点仍是Factory `27612ba`，已有大量历史dirty修改，Braid/SVC又是独立仓库；不得全仓暂存或凭HEAD冒充当前材料。接续起点的开发Braid binary SHA-256为 `e2f58d6342f5c74be91dbbbf2c45511148e00fb5d76d1cb05ec6510956279d81`，与核心实施记录一致；本批材料实现后的身份已更新到[材料实施记录](materials-plan.md)。未提交、未推送。三个Factory旧heartbeat均为PAUSED，不恢复旧正式实验；pi-minimal现有自费支线及其侧会话保持独立，不重复启动。

接续后先复核[材料整理具体范围](materials-plan.md)：模型投影details只保留summary，References先折叠再截短，根进度提醒精确替换且保留回复。计划与独立预演已完成；用户现已明确授权“‘正文折叠与根提醒整理’可以开工”，本批源码、文档及编译/已有归档读取已完成，实际新增行为反馈尚缺。之后收敛角色/原生工具、责任承接与task-packet方法；最后再确定I13载体、冻结与自费实验。沿用不编写或运行Factory/Braid/Corpus测试的要求，以编译、真实操作和获授权实验取得反馈；以后派生开发子Agent使用GPT-6.1 Sol替代GPT-6 Sol，遵守有界委派。

用户补充：此前19:25恢复I12是其通过Console手动操作，现在已再次暂停；由用户控制运行状态。20:52 CST实际Console API已确认两题Running=true、Paused=true、PID/StartedAt保持原身份（原文见 `runs/braid-console-control/20260930-session-navigation/http.before.json`）。本批不恢复运行。用户正在整理WSL磁盘（主要factory26），认为这可能解释远端证据目录不可读；该解释记录为用户提供的可能原因，未独立证实。Console新需求（工作项对应agent session及全部provider sessions历史）已明确授权GPT-6.1 Sol / xhigh子Agent独立实现，不阻塞本批；用户进一步明确要求可阅读原生对话及工具调用内容，纳入Console支线完成条件。

Console部署回执最初已写到WSL，但20:29 CST复制时该目录返回ENOENT，随后整个 `runs/braid-console-control/` 也不可见，原因未定。部署产物及实际HTTP再次确认仍正确；本会话将已返回的原始回执另存Mac `runs/iteration13/thread-handoff-20260930/console/` 并记录来源和缺口，不宣称远端回执已成功复制或旧index备份仍可读取。控制journal仍在原I12目录，已实际读取保存；此证据缺口不等同前端部署失败。

## 目标与范围

让原始产品义务穿过分工、实现与验收，让工具操作可预见，让维护和协作减少实际工作负担。最终完成判断须回到实际状态及对应执行证据。

```text
I13
├─ Braid CLI体验 → R03［源码完成；实际写操作待验］
│  └─ C01—C04：短回执、字段读取、显式根resolve、对称unresolve
├─ 上下文与材料 → R04/R09［源码完成；新增运行行为待验］
│  ├─ 仅description重建，其余增量；自操作不自通知；保留原生连续性
│  └─ details投影保留summary；精确替换自有根提醒，保留回复和原件
├─ sub-agent简化与改进 → R07/R08［已提交7f8ad6e；真实行为待验；executor原生说明已修正］
│  ├─ 独立任务输入，不带profile instruction；全部工具开放
│  ├─ explorer承担复杂调查/根因诊断/探索，可请求caller补信息；advisor不规定输入输出或思考方式
│  ├─ 禁句不超过一句或5%；vision去额外环境约束，改glm-5.3-flash
│  └─ 全部角色可再委派，子层最大3；核对原生能力与深度配置
├─ SVC Agent Skills → R02［四技能方法与分发已完成；真实采用待验］
│  ├─ implementation/investigation/design不打包、不引用，源码保留
│  ├─ documentation恢复完整项目知识方法；sub-agents恢复一般委派方法，自包含且不含具体角色内容
│  └─ task-packet恢复工作记忆循环，去growth；复用已改V&V
├─ Braid软件协作及ARC requirements tree → R01/R05/R06/R09［已按泛化边界修订具体范围，源码未开工］
│  ├─ 当前义务、候选、独立讨论、增量、承接及终态，不止命令用法
│  ├─ 父节点自身要求、内聚子树及跨枝完整操作；区分来源、依赖、责任与证据
│  └─ 未接手义务、初态、消费者变化、证明范围及同次结果归属
├─ Factory/Braid提示词分层与入口 → R09［已提交；原生装配/编译通过，动态会话待验］
│  ├─ 简化Issue/PR system prompt、Factory追加要求及profile，去除层间重复
│  └─ documentation/task-packet强制应用及首次读取入口；技能正文独立提供
├─ 工具接线［已提交09a32c4；Linux/材料/Context7/FFF通过，Exa待有效key］
│  └─ Context7/Exa打包自有key并脱离mcporter；增加pi-fff
├─ 合入feat/experiment-storage-lifecycle［2026-10-01新增；分支成果已定位，待合入］
│  └─ decision归档、预算、稳定Python资产、只读GC计划及Braid OTLP摘要
└─ I13载体、冻结与实验［开发载体已建立；冻结/实验未启动；I12由用户控制］
   ├─ I13基线：采用共同的新角色、方法和vision模型
   └─ GLM-5.3-root对照：只额外改变根Issue对应Braid session模型
```

保留历史编号 `I12-G01`、`I12-G04`、`I12-G05` 及其证据入口，修复由本packet负责，不另造一组重复问题。
`I13-R01`～`R09`继续作为[问题账](findings.md)中的上游原因与调查入口；本页按用户最新清单展示交付范围，避免把一项原因误当作一个实现批次。G/C/E/A及I12-M保留为观察和传导链索引，尚未定位的原因仍明确保留。
“机制已证”说明问题怎样发生，不等于已经知道为何当前模型、提示词、上下文和工具使它反复发生。
用户补充的[R01/R05/R06/R07追因报告](upstream-root-cause-investigation/report.md)已逐项消费：R05/06/07先前已部分入账，本轮补全R01分支和修复判断。报告的历史阶段描述不覆盖当前CLI/核心已实施状态，也不作为材料整理或其它批次的开工授权。
多条表现共享一个调查入口，不表示它们已证实同源；根因状态、排除项与下一步区分证据见 [统一问题账的因果分层](findings.md#因果分层与上游问题)。
G01/G04与I12-G02共享同一里程碑遗漏的部分证据链，解释不同决定环节，不算作三个独立功能缺陷。
G05是记录错配，不能据此否定已核实的最终194/152通过或解释全部官方失分。

## 方案与边界

G01/G04/G05的因果证据和原方案见 [方法修正](quality-methods.md)。
用户随后要求重新审查V&V技能的使用时机和方法完整性；[V&V技能复审](vv-skill-review.md) 已对照原知识框架及四个分支，确认入口偏窄、理由和执行内容压缩、反馈与演进导航缺失。
修订方案恢复日常工作入口和四层知识结构，将G04/G05融入方法正文；原先只补几段的方案不再代表完整V&V范围。
用户开工原话：“没错，其根本是要有‘元理论’；你可以安排 astra-light sub-agent 按照该方案进行修正；你整理一下工作区、提交还有task packet 等。”
授权范围是V&V元理论、内容及导航改写，委派实施，以及相关工作区整理和提交；不由此启动I13实验或恢复I12。
子Agent负责技能正文及必要交叉导航，主Agent负责整合、内容复核、任务包和提交。当前接口无独立astra-light标识，采用gpt-6-astra / low并已向用户说明。
方法归SVC；Braid提供协作及上下文能力，不解析业务需求、不判断业务验收。Variant负责技能和角色接线，不生成应用检查或预制本题内容。
复用现有执行记录及技能工具，不新增验收状态机、执行框架或内容测试。

I12-G02/G03、E01/E02的历史状态保留在 [I12问题账](../iteration12/i11-github-score/findings.md)；本次全面分析后的剩余处理由 [I13统一问题账](findings.md) 承接，保留旧编号，区分已部署与实际采用。
I12曾按用户要求暂停，冻结材料和运行身份不变；当前物理状态见 [I12 packet](../iteration12/packet.md)。独立I13已由子Agent批次创建；本轮仍未启动实验。

## 当前下一步

用户最新要求继续当前主线，并明确“比赛本意想要的是泛化的coding agent harness……将arc特定的适配限定在agent skill、root issue description”。该边界已进入[实施方案](collaboration-requirements-plan.md)：通用协作技能与ARC适配分离，后者由原拟 `arc-requirements` 改名为 `arc-bench`，承载需求阅读和交付reference；迁出当前profile中的ARC平台契约，root description提供本次材料入口；移除运行时对 `requirements.yaml` 的硬门槛，只传输入目录。Braid/Pi不增加节点、依赖或覆盖语义，现有外围调用/交付协议保留。独立advisor已只读核对上述范围与验收方式，主线采纳；本轮仅修订任务资料，未据“继续”扩大为源码开工。Exa由用户明天修正，等待其通知后复核，不阻塞本组。

用户最新认可协作与需求树方案，要求进一步查看I12人工复审、I11过程、人类协作/GitHub/LLM上下文研究如何支持方案，并新增参考 `code-philia/agentic-requirement-compiler`。主线已整理[证据与推导](collaboration-requirements-rationale.md)，将人工原稿I12-2补入M12—M17；独立只读子Agent核对官方提交a119f22，区分可借鉴的共享合同、真实执行与追溯，以及父义务、消费者变化和覆盖终态尚未得到保证的边界。方案补清来源、依赖、责任与证据的区别，落点仍为两项独立技能；源码尚未开工。下一段保留前次两条实现线的开工原话。

当前主线进入[Braid协作方法与Requirements树方案讨论](collaboration-requirements-plan.md)，源码尚未开工。用户最新明确：“我已经配置好了 .env.i13key。我复核了这份 tools-prompts-audit.md，没问题。你可以开工工具接线和Factory/Braid 提示词了。然后我们来讨论Braid 协作方法与 Requirements 树。”据此，[工具与提示词两组方案](tools-prompts-plan.md)及审计已复核，两条实现线均获得明确授权：现有i13_prompt_dedup继续，新增i13_tools_implementation负责工具，均为GPT-6.1-Sol / extra-high。工具按已审建议给主Agent/explorer/executor加载Context7/Exa，其余角色不默认加载；fff覆盖主/子。共享run.py与runtime.py按常量/装配和补丁/依赖分工，提交index串行协调。

阶段纠正保留：此前用户说明仍等待审计、尚未进入下一组，主线已回到审计并交付tools-prompts-audit.md；提示词提前开工按用户“不要停，接着补充”继续。现有新授权替代了此前待确认状态，不将早先的方案认可追溯解释为当时已取得开工许可。

工具组复用Context7官方Pi扩展和FFF官方包，并以薄原生adapter提供Exa检索/正文；按角色选择加载、锁定构建、自有key制品接线和旧mcporter入口一并收敛。提示词组按Braid产品协议、Factory配方和运行条件分层去重，明确documentation/task-packet义务及读取入口，保留现有协作与交付要求。技能正文仍独立提供；实际安装、材料生成和服务反馈归两条实施记录，不将先前发布包阅读视为运行验收。

提示词线已完成Factory `3b987e1`与Braid `49d5d5f`，未push；[实施记录](prompt-dedup-implementation.md)保存具体输入来源、十角色原生装配、编译和prepare-only。主线已独立读取报告及profile/root task的提交差分：发现入口保留、重复方法退出，下一组尚未迁移的协作段落仍明确存在。额外修正Braid clone读取到祖先Factory开发AGENTS的生产者边界。完整动态Braid/前后台/恢复未运行，旧会话副本不迁移。

工具线已完成`09a32c4`，既有model-exclusion构建前提及GNU补丁格式另提交`a08070c`，未push。最终Linux runtime、私有ZIP及Linux包内prepare-only完成；Context7真实查询和macOS/Linux原生FFF检索成功。主线独立核对十二消费者工具材料、Linux原生注册/检索原件及角色选择、私有env装配源码，结果与已审分配一致。完整模型会话仍未运行。Exa search/contents均返回HTTP 401 / INVALID_API_KEY，已请用户在现有env修正后再核，不重试旧key、不阻塞其它工作。实际制品身份和边界归[工具实施记录](tools-implementation.md)。

用户随后提供较完整的ARC分析，特别声明“分析不是我的态度和建议”。该内容作为研究输入，不记录成用户偏好、方案决定或开工授权。已补查接口卡片优先级、初态/认证合同、跨层证据时效、视觉缓存、技能选择和工具middleware，并与现有SVC V&V、I13 vision和工具开放政策对照。主线判断及事实/政策/实际采用的区别写入[推导说明](collaboration-requirements-rationale.md)：共享契约按真实跨成员需要形成；GIVEN初态需辨明产品供应、正常流程和检查准备；复用适用证据；当前不引入compiler运行时、工具硬限制或重复repair技能。完整源码实施仍待本组开工指示。

审计快照及当时未闭合范围归[工具与提示词审计](tools-prompts-audit.md)。已确认重复覆盖Braid/profile、Factory根任务与运行约定、原生工具metadata/description、child output的system/task双注入；后者不能仅改Markdown解决。补审同时更正fff默认只有两个工具，确认其guidelines含额外流程限制；工具方案据此更新并已获开工授权。

凭据路径核对：用户口述的 `.env.i13key` 不存在，实际已填的是此前创建的 `.env.i13-tools`，两项变量非空且文件被Git忽略，已向用户说明。工具实现直接采用该文件，不复制或改名，不输出key；服务可用性由本组获准的真实公开文档查询核实。I13尚未冻结或启动模型实验。

用户本轮还新增“将 feat/experiment-storage-lifecycle 的成果合入”。已只读核对同名Factory分支的六个提交（57cd761、e222296、cfc7aa2、956de0b、e6e1a5c、4e1bb08；分支头4e1bb08）及独立Braid分支提交e87b82b，实施真相以该分支 `tasks/experiment-storage-lifecycle/packet.md` 为准，主工作区同路径仍是旧设计阶段副本。成果包含decision归档回执、运行前/运行中存储预算、稳定宿主Python资产、只读GC plan和默认有界OTLP摘要。尚未合并或部署；分支的variant收尾接在pi-braid-i12，后续合入须核对I13接续与现有dirty修改，保留I12暂停现场。合入源码不代替历史清理、GC apply、宿主runtime实际建立或新实验的单独范围确认。

用户明确后续会持续补充新发现，默认登记到已有问题账并归入相应批次，不终止或阻塞主线；只有明确改变当前优先级/范围的指示才调整主线。最新M11为Braid system prompt与profile instruction疑似重复，已归R09及后续提示词整理，当前sub-agent批次保持原范围。

CLI、上下文核心与[正文投影/根提醒整理](materials-plan.md)已落实源码；新增行为的真实运行验收边界各自保留。最新清单与源码接线的差异、方法归属和两组研究的适用边界已写入[修复方案](repair-design.md#最新范围核对2026-09-30)。
用户已审查[本批具体方案](subagents-plan.md)并表示“基本没问题”；其explorer修订已同步：扩大为有明确用途的复杂调查、根因诊断与探索，允许提前向caller补信息，删除Pi已覆盖的基础工具说明。方案及独立只读预演已完成，随后用户授权实施；当前本批已提交7f8ad6e，完整材料反馈及未验边界见[实施记录](subagents-implementation.md)。executor已按[收敛方案](executor-followup.md)删除原生过宽指引并提交84344b4；保留共享cwd/worktree自主选择。之后处理SVC选择/方法、Braid协作、需求树和整体提示词入口；task-packet草案已移除growth。
用户随后指出executor description有同类问题；已对照原始契约改为具备必要调查、局部设计与反馈修正能力的独立工程任务，强调可整合的实际成果及提前请求caller补充信息。文案修订与并发写策略分开，不作为I12采用问题已闭合的证据。
advisor按用户要求参考当前Codex角色定位，description明确在问题定义、方案形成及重要取舍时参与，新证据或反复失败时重新判断；正文保持简短，不恢复固定输入输出或思考步骤。

新增Context7/Exa自有key打包及脱离mcporter、pi-fff插件归“其它”组，不阻塞当前批次。用户明确永远禁止内联Agent Skill（包括sub-agent），已持久化到AGENTS.md并成为各批材料接线约束；当前已知child内联路径在本批清除，技能正文保持独立文件与按需读取。
Console的讨论根入口及Agent/provider历史会话、原生对话和工具调用浏览已独立部署；只读HTTP确认两个I12仍暂停。页面交互、缺失的3份原生文件及Codex格式的未验边界归[Console packet](../braid-console-control/packet.md)。I13实验未启动；不主动改变现存I12运行状态。

## 最新清单的核对与取舍

用户以“主要的几个改进点”重列I13，并要求与现有树核对。该清单确定新的设计方向：移除三项技能的分发和引用；补足documentation/sub-agents的方法理由；task-packet去growth；child输入和工具简化并开放深度3再委派；vision替换模型；引入Braid协作与ARC需求树研究；简化Factory追加要求和Braid系统提示。executor明确继续讨论。已获准实施的三个Braid批次不重复开工，新增材料与配置仍按既有分批流程形成具体实施说明。

与旧树相比，新增或需要改写的并非只有角色Markdown。run.py目前给非vision child追加运行约定并内联三类workflow；原生pi-subagents需显式subagent能力才能再委派，默认最大深度为2。新方案必须核对最终生成指令、实际工具和深度配置。原拟放在svc-design中的责任/初态/消费者案例也需按新的知识归属承接，不保留对已退出技能的间接链接。

旧树中已有且仍保留的范围是details/根提醒、V&V元理论与证据归属、根模型对照；未闭合的G03/G06/G07前因、重复核查及executor净收益继续以问题账记录，不能因改写材料宣称解决。两组研究的旧运行语义只作历史证据，当前策略以已实现的description-only及显式根resolve为准。

## 当前复核、授权及实施准备

用户本轮原话：“executor 未使用……我同意，但你应该自动继续排查”；“可能是SVC task-packet没有发挥作用”；“console 问题不纳入iteration问题；console修正可以立即应用……console属于实验基础设施的一部分”；“其它的我同意”。
据此，四组Harness方案已复核，通过后进入既有实施准备阶段，尚不将其解释为I13实验开工；executor和task-packet继续调查，不搁置为可选跟进。
[executor继续调查](executor-followup.md)已从入口走到工具指引约束，[task-packet复审](task-packet-review.md)已从材料走到两根的实际选择；新增改稿范围进入具体开工说明。
用户随后明确：“仅有description，description之外的comment、relationship、title等都不重建。”其行为表、作用对象及落点归[上下文更新策略](context-update-policy.md)。

CLI已按用户“可以开始应用了（交给sub-agent；我们还要继续讨论）”授权交给GPT-6.1 Sol / high独立实施，范围仅C01—C04及实际受影响文档，不改核心事件语义、Console或运行。执行状态归 `cli-implementation.md`，其它准备见[实施准备](implementation.md)。独立GPT-6.1 Sol / medium已完成描述重建、增量通知及休眠连续性的技术预演；用户已复核[完整筛选清单](context-reset-catalog.md)并明确“我同意你对上下文重建的这套判断，可以应用修改了”。核心已独立开工，主线负责对象事件、GPT-6.1 Sol / high 负责恢复连续性，实际状态归[核心实施](context-implementation.md)。休眠方案复用按指派归属的既有description失效事件，不因全投影hash不同重建，也不迁移I12旧状态。
本阶段不恢复I12，不修改其对象或冻结材料，不启动模型验证，不提交。

Console由原GPT-6.1 Sol / xhigh支线接续，实现、部署与未验边界归[Console控制任务](../braid-console-control/packet.md)。此前已修的暂停后读取证据仍保留在[历史记录](console-paused-access.md)，不是I13待办。Braid通用对象接口与Console/运行适配层保持独立责任。

## 实验对照增量

用户要求：“I13 实验时做多一个 variant，使用 glm5.3 作为 root issue agent。”
将其登记为 I13 实验矩阵中的额外 variant，基线仍保留；这条对照只改变根模型；用户随后提出的vision改用glm-5.3-flash属于两组共同的I13改进。不提前创建实现或启动运行。

| 对照 | 根 Issue Agent | 其它配置 |
| --- | --- | --- |
| I13 基线 | 沿用最终确认的基线配方；当前 I12 为 `glm-5.3-flash` | I13 已复核并冻结的实现与方法 |
| GLM-5.3-root | `glm-5.3` | 与 I13 基线一致，子 Issue、PR 及原生 sub-agent 配方不随根模型改变 |

要回答的是：在相同工具和方法下，更强的根模型是否改善整体需求理解、分工承接和最终覆盖判断，以及增加多少耗时和 token 消耗。
两组使用相同题目、起点和评估方式；人工介入若不同，单独记录其影响，不将结果直接解释为模型差异。
GLM-5.3 仅供根 Issue 对应的 Braid session 使用，遵守每次运行昂贵模型合计最多一个 Braid session 的既有约束；不是按 Pi 原生会话数计限额。
子 Issue 和 PR 的可选成员、模型仍由 Agent 在既有配方边界内决定，Braid 不因根模型选择自动指定或传播模型。
具体目录、材料冻结及实验启动在后续对应阶段确认；当前问题登记和分批复核流程不变。

## 本次范围增量与接续顺序

用户提供 I11 完整 lineage、五类需求因果链和 Braid CLI 审查，并要求“这些都纳入 I13 要修复的问题”。
已将全部结论、八个 CLI 案例及 D1–D6 草案逐项对应到 [统一问题账](findings.md)。已有修复保留实际身份及未验证边界，新增问题保留根因强度和待决方案。
用户随后明确收敛当前阶段：“先别急着修复，先登记并理解这些问题，然后整理 I13 的问题；最后我们再来一起（分批）核对方案并修复这些问题。”
此前登记阶段仅更新packet、核对实现及缺口，报告草案保留为候选；当前已完成方案复核的范围与新增项以上方“当前复核、授权及实施准备”为准。
用户进一步指出 G01/G03/G06/G07/G02/G04 仍是表层表现，要求树中记录根本问题，未定位到的明确标注。
据此按上游问题重组；不再从一个表现直接推出一个提示词补丁。原方法草案仅保留为候选，先说明它针对哪项可改变因素、为何有望改变决定及尚缺什么证据。
新收到[I11根因深化](../iteration11/braid-context-methodology/root-causes-deepening.md)与[I12人工复审登记](i12-manual-review.md)，已更新R01/R04的因果解释、修正packet权威顺序的因果位置，并增加R07使用线索及R08/R09。
工具开放、材料折叠、讨论组织与提醒管理已获得方案认可；其中CLI、上下文核心与正文投影/根提醒整理后来分别获准并完成源码，剩余角色和工作方法继续准备。当前不恢复运行。V&V此前独立获准并完成的改写保留实际状态，不与待开工范围混淆。

1. 完成问题登记与理解：从结果、表现和直接机制追到可改变的上游因素；未定位根因的明确列出候选解释及能区分它们的观察，不以“未遵循方法”结案。
2. 用户此前认可四组方案，CLI、description-only核心及正文材料已分别实施；[当前修复方案](repair-design.md)已按最新清单修订剩余范围。Console独立，executor原生说明修正已完成，真实效果待验。
3. 对通过复核的批次细化实施及验收说明，取得对应开工依据后再修改；I13载体与实验另行确定。

实施前工作树差异、Git起点和SVC原文已保存在 `runs/iteration13/vv-rework-20260930/`。
仓库已有大量历史修改，提交以本次归属明确的内容为边界；其余状态及整理决定见 [工作区整理](workspace.md)。

实现状态由本packet维护；全部问题及证据见[统一问题账](findings.md)，当前方案以[修复方案收敛](repair-design.md)为准；[方法修正](quality-methods.md)保留质量方法的原提案和因果证据，不与新方案并列作为实施要求。V&V新的内容结构、入口及改写深度见[技能复审](vv-skill-review.md)。
历史原生依据留在 [I11 PR23过程](../iteration11/braid-context-methodology/final-pr23-flow.md)、[根最终审阅](../iteration11/braid-context-methodology/final-root-flow.md) 与 [跨模块承接分析](../pi-minimal/github-score-analysis/i11-mechanisms-forward.md)，不复制或改写原始证据。

## 子Agent批次实施结果（2026-09-30）

本段更新本批当前状态，前文未开工描述属于其对应历史复核时点。用户明确授权：“你可以按这个方案开工『I13-sub-agent简化与改进』了；注意你一直都可以自由git commit。”已从当前I12形成独立pi-braid-i13，完成五角色简化、开放原生工具和再委派、子层最大3、移除child自动运行/方法正文，以及两视觉角色换用glm-5.3-flash；共享补丁安装、runtime身份记录与I13 OTLP材料接线已同步。实施范围和观察归[子Agent实施记录](subagents-implementation.md)，方案归[已复核方案](subagents-plan.md)。

Python编译、两处原生补丁的实际适用及语法编译通过；真实requirements目录分别走共用endpoint与独立visual endpoint的prepare-only，两次均生成十份角色，正文与源码仅经路径替换后的内容一致，技能/扩展路径完整，模板和共享native home无SYSTEM.md。原生启动和技能发现按实际源码核对；未运行模型、测试、包smoke或实验，真实三层委派、联络往返、结果回送及视觉API仍未验。I12的25份文件身份未变，冻结runtime和现存运行未修改；提交只纳入本批增量，未push。

本批源码及材料核对已完成，主Agent持有整合责任。随后executor已按[收敛方案](executor-followup.md)完成原生说明修正，SVC批次也已获准完成源码和材料生成；当前MAIN_SKILLS/build清单已退出三旧技能。I13尚未冻结实验制品，不由本批实现或commit启动模型运行。

## SVC批次开工（2026-09-30）

用户原话：“我阅读了方案，没问题，你可以安排subagent开工。btw，可以考虑裁剪掉‘跨仓共同依据’的内容，因为我们的赛题不存在多repo。”授权范围为[更新后的SVC方案](svc-skills-plan.md)：documentation完整方法、通用sub-agents、task-packet去growth、保留技能引用清理及I13退出三技能的接线；Multi-repo不恢复到分发材料。已委派 `/root/i13_svc_skills`（GPT-6.1-Sol / extra-high）实现、取得实际材料反馈并作范围内提交，主Agent持有整合责任。文档/task-packet强制应用与profile整体去重留待后续批次；本次不启动模型或实验。

## Executor原生说明修正开工（2026-09-30）

用户原话：“好的，开工，应用该修正”。按[最新收敛方案](executor-followup.md)删除Pi扩展的cwd级单writer、普通写入强制隔离和父方应用全部修正等说明，同步包内重复入口；不另加父方执行设计要求、writer锁或协调协议。原生派生与worktree能力保留，SVC委派方法由并行批次处理。本批反馈来自实际依赖补丁应用、编译和工具说明材料生成，不启动模型、实验或修改I12冻结运行。起点与快照在 `runs/iteration13/executor-guidance-20260930/`。


## Executor原生说明修正结果（2026-09-30）

已按用户“好的，开工，应用该修正”删除工具及包内帮助的cwd级单writer、普通写入强制隔离和父方应用全部修正要求；worktree只说明参数效果，条件性单writer示例保留。调用方无需先设计局部执行细节，现有executor与SVC委派方法承担独立收敛。本批扩展已有acceptance-off补丁及runtime目标hash清单，未新增调度或权限机制，既有Linux接线直接消费该补丁。

从原始npm归档实际应用完整四份补丁成功；Python与TypeScript语法/emit编译通过；两个真实I13配置生成的description/metadata及full/compact/custom附加说明均已核对。相对旧补丁链只改变七份原生说明文件，I12的25份文件身份未变。详见[executor实施与证据](executor-followup.md#实施与反馈2026-09-30)及 `runs/iteration13/executor-guidance-20260930/`；未运行模型、测试、包smoke或实验，实际并发效果与委派净收益保留待验。


## SVC与Executor批次整合完成（2026-09-30）

SVC `a0af6e14a9f6cd2b19e1565e5d08d82fe3672139`、Factory `1a377c9446618270218476d6df354b2fd2cb419c`完成本批SVC方案；executor原生说明修正在Factory `84344b4b913cd5e036cd8e99fa9f5cd301da55c5`。三项均未push，其它工作区改动保留。当前状态以本段和对应实施记录为准，前文历史开工状态不再代表待办。

主线独立读取技能方法正文及实际launcher/角色材料，并核对prepare-only最终work/skills的32份文件与SVC源码一致：仅分发documentation、sub-agents、task-packet、verification；三项退出技能源码仍在；documentation五分支完整；sub-agents自包含且无具体角色内容；task-packet去growth。原始构建缺pip错误及半成品保留，隔离补齐pip后标准build和真实GitHub requirements的prepare-only完成。详情归[实施记录](svc-skills-implementation.md)，主线文件身份核对在 `runs/iteration13/svc-skills-20260930/primary-material-review.json`。

SVC材料构建复用上批runtime并保留其旧补丁身份；executor修正另从原始npm包组装完整补丁链、编译并生成实际说明，两者没有混报为新Linux实验制品。I12现存材料/运行未改动，也未运行模型或实验；实际方法采用、并发行为与净收益仍待后续授权观察。documentation/task-packet强制应用、profile整体去重及Braid协作/requirements tree仍属后续待复核范围。


## 提示词扩围开工与工具分配修正（2026-09-30）

用户原话：“Context7和Exa的自有key你准备一个env文件给我，我到时候会放进去。并不是所有sub-agent都需要context7和exa。同意‘Factory/Braid提示词’的方案，不过扩大其审计范围，核心目的是审查有无重复提示词（至少不可以让agent的上下文内重复）。”

已创建Git忽略的 `.env.i13-tools`，两个变量留空供用户填写。Context7/Exa全角色加载方案撤回；当前建议主Agent/explorer/executor加载，其余角色不默认加载，待本轮反馈。提示词组获准从实际组合输入审查全部来源，保留每项指令的明确归属，在必要生产者处去重；不会通过删掉必要义务或加自动语义去重框架完成目标。工具服务鉴权和模型实验不由本次空env创建认定完成。
