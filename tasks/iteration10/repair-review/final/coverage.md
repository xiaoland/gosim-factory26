# 最后复审覆盖表

本表覆盖R01–R29、A01–A12、Z01–Z03共44个目录ID，不将交叠修复重复计作根因。`直接`表示本轮读相关实现与来源并作边界判断；`有限`表示只核关键接线、报告和部分实现；二者都不是行为验收。没有重新全读两题原生轨迹，也没有运行任何测试、探针、应用或实验。

来源：G=`tasks/iteration10/run-audit/github/report.md`；S=`tasks/iteration10/run-audit/sheet/report.md`；O=`tasks/factory-subagents/cells/iteration10-role-audit.md`；前轮结论=`../findings.md`与`../coverage.md`。完整源码基线见source-snapshot.json。前轮的编译/实际操作/历史测试是已有证据，不是本轮独立重验；未直接追取的原生证据不升级。

| ID | 本轮读到的边界/机制及判断 | 深度与剩余限制 |
|---|---|---|
| R01 | CLI print_message_receipts将正文与接收状态分开，delivered不再暗示业务完成；G报告保留后来正确识别的反证。 | 直接读CLI关键输出；未重开旧DB或全读原生。方向成立。 |
| R02 | native_files给主profile及非vision角色追加单一环境正文，并先说明不扩大职责；fresh不依赖父历史。 | 直接读run.py装配；未造新制品。方向成立。 |
| R03 | 主指令将整合PR交接与根整体关闭分开；Closes仍是显式对象能力。 | 直接读当前主profile，其他profile由快照一致性支持；采用待观察。 |
| R04 | 原场景/初始数据/并列对象→派生任务的保真责任留在variant及SVC；不硬编码两题答案。 | 直接读run/product/check-design，G/S报告定向；效果未证。 |
| R05 | product要求原句对照、决策者处理和传播变更，保留原始输入歧义，不将派生任务自动升级成权威。 | 直接；未重读全部冲突原文，依G/S定向报告。 |
| R06 | technical/workflow沿用途、调用者、豁免至写入；check-design覆盖可达交叠及跨组件结果。S的pivot新增路径同属此机制。 | 直接方法，应用静态链依S，未重审冻结应用；方向成立不等于新模型采用。 |
| R07 | interpreting-results要求同属性反证补观察或缩小声明，其它层PASS不能代替图像。 | 直接方法；未重新看原图片，不扩大S视觉结论。 |
| R08 | run.py规定根基础独立PR与业务分批，Braid provider说明对象职责；当前用户流程选择不伪称旧分数唯一原因。 | 直接主指令/provider；真实交接未证。 |
| R09 | profile在共享假设/判据形成前咨询，不套普通委派ROI；零调用不等于工具故障。 | 有限：读父指令与O，未独立全读五份角色或调用。 |
| R10 | observer在Unknown agent保留错误并给目录/所有权，executor检查重复责任。 | 直接；observer正常启动回归影响提示可达性，见FF1。 |
| R11 | 原问题是父重建后的旧写任务不可见；同父保留索引方向正确，正常fresh出现FF1回归。Z02的存活条件收敛可接受。 | 直接完整observer＋Pi真实生命周期源码＋O证据链；需消费FF1，采用未验。 |
| R12 | vision只读且guard关闭；subagent_wait空结果保留并提示PBB命名空间/aggregate区别。 | 直接vision/observer；实际等待时序归A01，不能用提示证明完成。 |
| R13 | 工具方法进入explorer、工具配置归variant方向符合能力发现。 | 有限：本轮只核目录与前轮材料，未重读完整explorer/MCP配置或远端调用；不升级验收。 |
| R14 | Pi start/resume清暂存，prompt成功接受后clear context；不把之后回合失败倒算输入未接受。 | 关键接线有限核查，未复跑协议；净token收益未证。 |
| R15 | dispatch仅在profile/context/instruction匹配时resume，Deferred退回原路径，缺原生文件才fresh；同身份不改责任。 | 直接关键分支；未全读退回事务，前轮验证仅历史；FF1影响fresh回退。 |
| R16 | 批量和恢复按技术身份/版本组织，不由系统判断评论有无业务价值。 | 有限：读取相关dispatch/store边界，未逐条核批量SQL；无可兑现成本数字。 |
| R17 | provider说明description/comment/hide/resolve及在途与重建生效差异，语义整理归成员。 | 直接；尚无自然整理效果证据。 |
| R18 | closing_issues_in只在默认分支解析，冻结关闭意图后共用结算；迁移旧prepared不补造意图。 | 直接函数/迁移，发布与恢复全链未重跑；方向成立。 |
| R19 | discussion_changed历史参与者排除显式inactive，但保留当前负责人和显式联系。 | 直接SQL及help；自然退订使用未验。 |
| R20 | print_issue_created/pr_created回具体成员与无需再次启动，区别选能力与联系成员。 | 直接CLI/provider；未执行CLI。 |
| R21 | 目录和前轮说明手工整合以正证记录、旧编号不改；当前迁移保留created base/observed head。 | 有限：读迁移/关键入口，未重读全部merge与编号分配；不作新的全量正确性保证。 |
| R22 | 接管先联系或明确失败，当前候选需消费未解除前提；head匹配不是验收判定。 | 直接主profile；没有增加语义审批门，行为待观察。 |
| R23 | store共同边界结清旧地址；local_delivery_closed要求全工作项终态并无未决merge，不仅根关闭。 | 直接相关谓词/退役分支；未重开历史DB，终态不是产品完整度判定。 |
| R24 | 既有无provider孤儿与无模型恢复支持离线物化收尾，不需要假造有效零分。 | 有限：调用入口/前轮已读实证，未完整重读prepare_offline_resume；旧执行停止前提仍必要。 |
| R25 | Pi保留原生失败原因，monitor按会话及时间界定连续错，不能把token增长当语义进展。 | 有限：错误/时间接线，未重消耗监控样本。 |
| R26 | with-service首轮exit、候选与条件保存，check-only不重复起服务；dirty标记不等于内容快照。 | 直接全文；未运行helper，历史实操不作本轮验收。 |
| R27 | helper启动自有process group并按组收尾，避免全局pkill；脱离组服务/SIGKILL不在完整保证内。 | 直接；不新增沙箱或全局清理。 |
| R28 | run.py短TMPDIR、运行时browser、工具路径解决已知路径假设；持久Pi temp另存。 | 直接装配，未运行浏览器或检查新Linux制品路径。 |
| R29 | collector在循环外复用，成功flush清since_flush，失败只退回该集合；CLI输出分层由前轮说明。 | 直接collector关键接线，CLI status仅有限核查；不宣称后端逐条exactly-once。 |
| A01 | PBB自己注册pending-work，service排除，child无subagents时自身await并原生follow-up。 | 直接完整补丁与native-idle材料；有限任务完成/取消/settled顺序仍未证，保留F3。 |
| A02 | replace_assignee同事务Assign+无旧writer的Wake，旧owner stopping栅栏保留；create PR/reopen有对应入口。 | 直接replace及store栅栏，另两入口有限；无独立行为运行。 |
| A03 | monitor按执行cutoff/until、来源和每路径错误串区分旧证据与当前错误。 | 有限关键字段/调用，未全读所有路径选择或重跑真实记录；与R25不重复计收益。 |
| A04 | vision按图类型/用途提取，只读给定材料，事实/推断/未知分开，不替父定业务要求。 | 直接完整角色；未看新图像输出，属于用户方法选择。 |
| A05 | Braid git状态含测试删除，src搜索未见cfg(test)/test属性；生产evidence decode的OTLP导入不是测试。 | 有限删除核查；未逐行审全部删差异，不运行测试/编译，不保证每处删除均已独立验收。 |
| A06 | run.py保留框架选择、Node20/npm交付；runtime提供pnpm/portless等工具，不预写应用。 | 直接RUN_CONDITIONS，构建接线有限；工具Node24不能替Node20正式反馈，保留F5。 |
| A07 | runtime补丁摘要参与缓存，Docker应用同补丁；运行级缓存/browser入口复用不强制离线。 | 有限静态接线；未新打包，旧ZIP不代表现源码。 |
| A08 | workflow要求成功前置后才能依赖执行，同时允许独立并行；不是禁所有并行。 | 直接；下一生成看实际退出与调用顺序，预打包不解决控制顺序。 |
| A09 | debugging区分原动作状态与过滤输出，空结果不证对象不存在；CLI已知歧义由R01另修。 | 直接方法，原生链依G；不声称所有CLI歧义已清除。 |
| A10 | workflow将临时文件/浏览器/服务归属及干扰通知连起来，with-service实际约束其自有组。 | 直接方法/helper，技能其它细节有限；与R27同因，不增隔离系统。 |
| A11 | 已受理/结果不明先读回，不能依输出末行重试；CLI queued保持不同于失败。 | 直接方法/回执；不假称技术exactly-once或自动语义去重。 |
| A12 | 本轮读修改后的DetailedCellError示例与custom function CellError区分，窄文档纠错。 | 有限：官方3.4.0源码核对沿用前轮已列来源，未重新联网/执行；不归因最终失分。 |
| Z01 | 同父merge保留索引，但同home正常new父被误判，FF1。 | 直接完整跨层链，确定需修。 |
| Z02 | 持久入口＋恢复重读＋存活期通知满足旧任务可见性核心目标，不转移责任。 | 直接机制与O；未证明真实完成被新父消费，FF1消费是必要前提。 |
| Z03 | BodyArgs已有文件/stdin读取，多操作复用，帮助暴露正确入口。 | 直接完整BodyArgs；不改变解析语义，不假称shell展开可被事后还原。 |

FF1是本轮唯一确定新增缺陷；FF2为产品边界判断，FF3为Sheet消费判断。PBB及正式Node20是已有真实观察条件，不为缺证新增机制。前轮已有报告与本轮源码阅读互补，但不能合并伪装成新运行结果。
