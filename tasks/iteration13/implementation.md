# I13 实施准备

2026-09-30。CLI C01—C04、上下文核心与正文投影/根提醒整理已分别获准并完成源码。用户最新清单已同步到[修复方案](repair-design.md)，下列剩余批次取代旧的角色/技能承载假设；executor写入方案继续讨论，实验未启动。
Console归[独立设施任务](../braid-console-control/packet.md)，不等待本页开工，也不改变Braid对象或调度语义。

## 当前接续

CLI、上下文核心和正文投影/根提醒整理源码已完成，编译及归档只读反馈见各实施cell；I12已由用户再次暂停。
Braid材料投影/自有提醒按GPT-6.1 Sol / medium[独立预演](materials-rehearsal.md)与本轮明确开工授权完成，具体实现和未验边界归[材料实施](materials-plan.md)。实际归档没有details，根提醒未经历自然运行周期，不能将编译/普通读取视为新增行为验收。
task-packet结构草案已去掉growth；documentation/sub-agents的方法理由、三项技能退出、Braid协作和requirements tree一并进入材料批次。尚未修改这批SVC、variant或启动实验。
用户已基本认可[子Agent具体方案](subagents-plan.md)，其explorer复杂调查/诊断边界、caller信息补全和基础工具去重意见已同步；五角色草案、输入来源、完整工具/深度配置和两处原生窄补丁已完成独立只读预演。方案复核已完成，尚未修改该批源码。
Console的CLI讨论根入口及agent/provider历史会话、原生对话与工具调用浏览已独立部署，实际反馈与页面验收限制归独立Console packet。

## 顺序、范围与反馈

| 状态 / 顺序 | 实施单元和归属 | 关键不变量 / 开工前需收敛 |
| --- | --- | --- |
| 已完成源码 | Braid对象CLI：短回执、显式根resolve、对称unresolve、字段读取与错误 | 真实写操作待验；不扩大为幂等/CAS/分页框架，不替换冻结I12的binary。 |
| 已完成源码 | Braid对象更新及原生连续性：仅description触发Invalidate，其余增量通知，操作者不自回送 | 真实恢复、重建及并发投递待验；作用归属和失效来源见核心实施记录。 |
| 已完成源码 | Braid投影及自有提醒：details折叠投影，原文完整；隐藏旧系统提醒，保留回复 | 归档没有details，未观察自然到期替换；不能以编译/普通读取宣布新增行为已验。 |
| 方案已复核并修订 | I13角色与原生配置：独立child输入、完整工具、简化角色、再次委派及视觉模型 | 具体范围见subagents-plan；新建独立pi-braid-i13，移除role/run.py过量注入及全部skill内联，修正原生fanout接线及文案，子层最大3；不改冻结I12。executor写入策略另行讨论。 |
| 剩余第二批 | SVC选择/方法与协作入口：退出三项技能；补documentation/sub-agents理由；task-packet去growth；复用V&V | 同时处理build.py、MAIN_SKILLS、角色引用、workflow内联和保留技能交叉链接；源码保留。svc-sub-agents自包含，通用SVC不承载比赛/Braid制度，不把退出的SOP整体搬入剩余技能。 |
| 与第二批联合收敛 | Braid协作方法、ARC requirements tree、Factory追加要求与Issue/PR系统提示 | 方法解释义务、候选、交接、证明范围；树读取保留父要求、来源与跨枝行为，映射不代替语义覆盖。Braid系统提示保留职责和实际操作协议，方法按需读取；Factory保留真实运行合同，去掉重复方法灌入。 |
| 其它组，独立准备 | Context7/Exa自有key打包及直接调用，增加pi-fff | 不经mcporter使用这两个服务；具体接口、版本与装载在该组核对。禁止内联skill，不以本组未完成阻塞sub-agent文案与能力改造。 |
| 材料完成后 | I13冻结、统一材料及行为反馈 | 两组共同使用新vision模型，额外对照只改变根Braid session模型。编译、真实操作及获授权实验分别报告；实验矩阵、起点、人工介入和费用单独确认。 |

以上按依赖和确定性排序，不是同时派多人改共同入口的计划。
公共Braid/SVC源码变化不会自动改动已冻结运行；材料选择、构建身份和部署行为分别记录。
角色指令只保留职责与必要入口。通用方法在SVC、Braid成员协作在其独立方法材料中各有一个归属，不在root prompt、共同指令、各角色中重复。

角色批次的材料复核对象是最终生成输入，而不只是角色Markdown：不含profile instruction和重复workflow；explorer的工作步骤仅元调查、规划、task packet；advisor不规定输入输出和思考方式；禁句不超过一句或5%；vision没有额外环境约束。能力检查须同时覆盖原生基本工具和subagent入口，删除tools配置本身不能证明工具完整。

第二批的协作案例分别承接R01/G03/G06/G07及R05/R06：原义务排除后由谁承接，父层约束和初态适用于什么场景，新增消费者为何改变状态更新与证明范围，接收方采用哪次执行及哪些仍适用的证据。案例服务这些决定，不形成每项工作必填的表格或步骤。

## 独立预演

`i13_context_policy_rehearsal`（GPT-6.1 Sol / medium，fresh）首轮已完成[上下文策略预演](context-policy-rehearsal.md)：入口落在对象更新事务，活动会话没有hash自动reset旁路；直接把Invalidate改成Wake会造成漏通知/重复通知。
主线要求补查的休眠恢复问题已收敛：provider的resume不接收替换context，不需要完整投影hash相同；dispatch与store须一起区分旧会话resume和新会话start。先保证Invalidate只表示description变化，再复用既有pending事件及assignment revision携带未应用的description变化事实。没有这类变化时保留原生连续性与旧实际context revision；真实不可恢复、新指派等仍保留。不新增数据库字段，不迁移I12混合事件。报告末尾的补充取代首轮对休眠hash校验的判断。
预演只读源码，不改实现/运行或执行测试。其操作矩阵是观察覆盖候选，不授权创建专用模拟或模型测试run；实际反馈使用获授权运行与操作，I12现场不变。
这是实施前排障，不将阅读实现当独立验收；其它确定性材料编辑不另造泛化review任务。

## 具体开工说明的组成

在预演完成后，一次呈现所选目录/文件面、description-only带来的会话历史取舍、角色/工具及SVC新增变化、实际验收范围与未授权实验边界。
记录用户针对该范围的开工原话后实施；必要修复在获准范围内持续完成，不因普通问题反复请求确认。
剩余缺少反事实证据的净收益问题不伪造成已闭合，也不阻塞已定位的接口/材料修正。
