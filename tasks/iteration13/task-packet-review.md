# Task Packet：材料、入口与实际采用复审

2026-09-30。用户提出“可能是SVC task-packet没有发挥作用，甚至可能和V&V skill存在类似的问题”，随后明确“svc-task-packet不要growth”。本页已据此修订结构方案，尚未修改SVC或I12。

## 当前判断

问题不能简化成“没有要求建packet”。当前角色已要求根与子Issue建立文件任务包，技能入口也明确非简单任务直接创建 `tasks/<task-id>/packet.md`。
材料缺口和使用缺口同时存在：正文重组织名词、轻外置工作记忆的工作循环；已观察到根Agent口头打算使用技能，随后没有读取，并将Issue评论当成任务包入口或本身。
这比单独改description更具体，也不能由此断言所有成员均未使用文件任务包。

## 证据与边界

已通读 `sources/svc/skills/svc-task-packet/SKILL.md`、三个references、入口模板及模板导航，比较旧设计 `sources/svc/tasks/core-mechanism-evolution/design/32-integrated-task-packet-shape.md` 和13/14号材料。
旧资料中的人类汇报契约不回灌无人值守技能；它们只能帮助识别原方法在精简时保留了什么、丢失了什么。

WSL只读核对的I12运行位于 `/home/yyh/Development/factory26/runs/iteration12/restart-20260930/<case>/workspace/official-generation/template/.factory26/<inner>/`。
以下时间/行号取各原生JSONL，未启动模型或运行应用；查看原state使用SQLite `mode=ro`。

| 观察 | 依据 | 能支持的判断 |
| --- | --- | --- |
| GitHub根说要读task-packet，实际该会话只读取svc-design | inner `20260930-071413-6b4bf7a8`；native home `pi-glm-fast-01a0f12a-3011-7a31-89cb-096e86c680e3`；session `2026-09-30T07-14-30-518Z_01a0f12a-35f5-71fb-beec-01e5d161fa25.jsonl` L26。共56个toolCall，仅一次工具参数包含技能路径，指向svc-design；没有packet.md/tasks路径调用。 | 知道名字、计划阅读和实际采用不同；并非技能完全不可发现。限该保留会话，不扩大为所有原生会话。 |
| Sheet根明确把设计评论当packet | inner `20260930-071413-6fe73efc`；native home `pi-glm-fast-01a0f12a-31c2-7080-924f-1bdc40a1b679`；session `2026-09-30T07-14-30-534Z_01a0f12a-3604-73d2-9371-b0960a5da750.jsonl` L79：“Save task packet entry in Issue #1 comment (the design comment covers it).”该会话45个toolCall，读取了svc-design和hyperformula，未见task-packet读取。 | 不是仅少整理一次，而是把通讯载体当成任务材料的承载位置；没有证据说明它已经读过技能正文后仍作此选择。 |
| GitHub评论#3自称task packet入口，却只有汇报和Issue/PR编号，没有文件入口 | 原state根Issue评论#3；root worktree只有.git。 | 评论可以协调，但这里没形成所声称的外置材料入口。 |
| Sheet根有docs三文件，未有tasks目录 | `braid-state/worktrees/issue-1/pi-glm-fast-g1/` 当前有 `docs/acceptance.md`、`product-rules.md`、`architecture.md`。 | 它能够写工作文件，不能归因于通用文件权限缺失。不是完整全分支历史审计。 |

## 材料审计

| 层次 | 现有有效内容 | 缺口及影响 |
| --- | --- | --- |
| 使用入口 | description覆盖非简单任务、上下文、负责人及依赖；正文也要求直接建包。 | 相比旧V&V并非同等程度的场景收窄，但主要以恢复/协调/记录识别需求，未鲜明表达正在推理时减轻注意力负担的日常用途。 |
| 元理论 | current truth、来源、下一步、过期投影及唯一知识归属都有。 | 原因基本压成条款；没有充分说明有限上下文如何导致重复搜索、已排除方案复活、材料错配，以及为什么“当前综合+按需证据”能改善它。 |
| 工作循环 | 找到影响路线的发现时更新packet；事实/判断分开。 | 没有连贯展示“遇到问题→保存材料与当前解释→采用结果→修改当前路线→移出旧解释”的全过程，读者容易理解成阶段结束后整理报告。 |
| 结构与导航 | 有渐进扩展、语义归属、Cell和Track/Phase方法。 | 首层较早列出Plan/Inquiry/Design/Decision/Verification等名词；大量深度用于分类和准入，简单任务何时、如何实际落笔反而弱。 |
| 与协作载体的关系 | 项目文档与packet边界明确。 | 通用方法未充分区分通讯与可寻址材料；variant“在Issue中形成设计”容易被理解为把全部设计和状态常驻正文。此项是提示组合的候选诱因，不是已定唯一原因。 |

## 提交复核的修订方向

入口先教“外置工作记忆”：在多步工作中保存会影响下一步的判断、材料、脚本入口、未决问题和进行中工作，使当前会话与接续者按需取用，不必重新推导整个过程。
使用场景覆盖首次分析、边做边试、并行协作、切换关注点和上下文恢复，而非等到需要汇报或恢复才建包。
先说明一个短入口加就近材料如何工作，再把信息模块及Track/Phase/Cell留到真实导航、所有权或依赖压力下深入读取。去掉growth入口和专门材料，不将其整章改名迁入其它文件；必要的组织能力按实际用途保留，也不恢复旧的人类审批框架。

用同一个任务从简单到分叉的例子串起：原始材料→当前问题/解释→区分性观察→结果被采用→旧解释退出当前入口；随后才出现并行负责人和共享依赖。
说明“保存”与“消费”不同：保存原始返回不等于更新当前判断；更新packet也不等于把每个远端值同步为最新。
历史证据、可复用脚本和原件可在包中按需定位，当前入口只承载仍影响行动的综合与链接；成熟共享规则交给项目文档。

variant的既有工作流入口应与之相容：Issue/PR承载任务和协作，设计、计划、证据材料可通过文件入口承接；不把“在Issue开展设计”解释成“全部放在description/comment”。
只替换有歧义的入口，不再加第二套SOP；SVC保持与Braid无直接依赖。

## 下一步与采用判断

以上材料方向已纳入用户最新I13清单；具体改稿及接线仍随剩余材料批次给出开工说明。正文折叠/根提醒整理的源码授权不扩展为本技能的改稿授权。
观察正常工作中是否实际建立并利用材料入口、是否采用返回后更新当前判断、能否从短入口找到证据并避免重复工作。
有文件、读过技能或写了“task packet”字样都不单独算有效；未实际发生的恢复/协作路径标未验。

## 具体结构与入口草案（待复核）

本轮接续通读三份references；当前源码中`references/information.md`的investigation指向仍存在的svc-investigation，I12 build.py和角色技能列表也包含它。先前把它判断为已移除入口是误判，保留这项纠正。
用户随后明确I13不打包、不引用svc-investigation、svc-implementation和svc-design，这是新的材料选择。三者源码保留，task-packet中指向它们的链接随I13接入一起处理；通用任务材料方法也不改为依赖某个provider的explorer角色。
本节只细化方案，没有修改技能源码。

```text
svc-task-packet
├─ SKILL.md：日常多步工作的外置工作记忆
│  ├─ 为什么：注意力有限；聊天顺序不等于当前问题结构
│  ├─ 最小起点：短入口 + 已有材料的可达链接
│  └─ 工作循环：取得材料 → 形成当前判断 → 据此行动 → 用结果修订判断
├─ references/information.md：保存、解释与采用不是同一件事
│  ├─ 同一个共享格式任务，从未知到决定、实现与反馈
│  ├─ 当前综合与原始证据各自的用途
│  └─ 必要时才独立 Inquiry/Design/Decision/Verification 文件
├─ references/planning.md：跨负责人和依赖的工作组织
│  └─ 保留 Task/Track/Phase/Cell 能力，按实际协调需要使用
└─ assets/templates/：可选的起步材料，不能代替方法
```

元理论先说明问题：对话按时间追加，但当前决定依赖的是少量仍有效的事实、解释和未决问题。
把每次返回继续追加在聊天或入口会同时增加检索成本与旧判断复活的机会；只留下结论又会失去重新判断所需的依据。
因此入口保存当前综合和下一步，原件、脚本、分线工作保留为可寻址材料；新的结果改变当前综合，旧解释退出当前路线但不伪造历史。
这不是让每项远端状态保持逐值最新，也不是阶段结束后补写报告。

入口 description 草案：

> Use for multi-step work to keep current reasoning, decisions, evidence, and work in progress usable outside the conversation, during investigation, implementation, coordination, and recovery.

SKILL.md 首次使用先给一个可直接落笔的起点：目标与边界、当前判断及依据、尚未回答的问题、下一步与进行中工作的入口。
不要求这五项变成固定标题；已有短文件能承载时直接接续。
后面用自然段解释何时更新：结果改变解释或路线、工作被交接或完成、旧判断退出当前依据时同步；没有相关变化时不为“维护最新”另造工作。

连贯案例沿用共享配置格式：编辑器与导入器共享格式、调查某个兼容行为、记录区分性观察、采用结果修订共同定义、分别推进消费者、把反馈交回。
示例体现 packet 保存当前解释和进行中工作，项目文档保存共享格式，协作消息只携带问题/决定和材料入口；不把 Braid 或比赛概念写进通用技能。
最后才说明材料量与并行更新压力如何触发拆文件或 Cell，保留能力但降低首次使用门槛。

variant 的接线只需消除“在 Issue 形成设计 = 全部写在 Issue 正文/评论”的歧义，提供文件入口与技能导航；不复制上述方法或再次建立固定目录制度。
验收仍观察实际采用：能否从入口找到当前问题、依据和进行中工作；新结果是否改变当前判断；能否避免重复取得已有材料。存在文件或读过技能本身不能证明这些收益。

## 与 profile instruction 优化共同核对

用户本轮明确 documentation、task-packet 是强制应用的机制。技能负责解释理由与操作方法；后续 profile 批须明确负责人开始承担任务时读取入口并建立或接续相关材料，深入 references 按问题选择，已有有效工作可复用。当前 profile 的文档/packet 义务与“技能提供可选方法”概括需共同消除歧义；强制应用不等于内联正文、每轮全读或每个短子任务另建全套文件。完整关联见[SVC 方案](svc-skills-plan.md#强制应用与-profile-instruction-联查)。本次仅修订方案，未修改技能或 profile 源码。
