# I14 cleaner 与 PR review 方案

2026-10-02用户已复核同意cleaner/reviewer方案，已进一步明确授权实现、基础验收及I14-0实验；本文描述认可的产品机制，实际能力以实施反馈和运行证据为准。tester.army/e2e工具对照是同日新增范围，接入前提独立核对。I14把协作整理与独立验收作为不同实验因素；Braid拥有对象、责任、提交和会话生命周期，provider取得原生输入并运行模型，variant选择材料、模型及实验策略。PR创建默认draft已单独实施，旧PR与I13冻结包保持原身份。

## cleaner 的职责与提交边界

cleaner是工作项负责人使用的一次维护执行，每次只整理当前Issue或PR，不是可指派成员，也不是原生sub-agent。它继承当前原生会话实际生效分支的输入、后续消息、已可见的工具结果与压缩后的工作记忆，以及本次对象/讨论快照；不让负责人重新写一份交接摘要。自己的职责指令替换实施职责，历史中的实施命令只作为材料，共同要求继续适用。技能正文仍是独立文件；对象投影不冒充继承了原生历史。

建议首版采用按需的一次调用，由原生入口取得准确消息边界、运行独立cleaner，再回到负责人。清理推理由cleaner承担，不要求负责人逐条制定hide/resolve或正文改写。先不增加定时清理、后台重试或自动触发政策；是否值得并行由实际等待与费用判断。归属分成明确两层：原生扩展负责继承/独立执行，Braid负责维护身份、对象提交与记录；Factory wrapper配置该能力，避免外部轮询后以--external伪装负责人的整理。

用户提出“这些修改在turn结束后才正式提交”。建议把它作为首版提交边界：cleaner turn中的全部维护操作形成待应用结果，这次cleaner调用正常completed、工具结果已结清后核对来源前提，再用一次短SQLite事务提交。不能把Pi单个assistant/tool batch的turn_end误作整个维护调用完成；当前Braid的agent_settled语义可作为接缝依据，仍需保存实际来源leaf与完成身份。description净变化按现有契约产生一次失效事件，hide/resolve及对象变化按现有投递规则通知；事件与对象一起持久化，提交后才能被派发。模型推理期间不占有数据库事务或锁。提交本身不额外调用模型。

失败、取消、中断或Unknown保留未提交结果与原因，不自动应用半份结果。提交结果不明时读回该维护操作身份，不重新执行一批修改。description或实际涉及的讨论在来源快照后发生变化时，拒绝过时的一批并保留当前对象；首版不做自动文本合并或循环重试。仅比较local_items.revision不够，评论有自己的变化；resolve必须防止把cleaner未读的新回复算作已解决。hide根讨论继续保持隐藏后代的现有产品语义，包括未来后代，所以它适合明确排除的讨论，不能当作普通已读归档。

记录发起成员、维护操作、来源消息边界/对象快照和实际效果，保持负责人责任；cleaner没有新的公开assignee或代码实施责任。description统一提交只减少一次整理的重复reset，不能免除最终正文变化导致的重建；hide/resolve也不会擦除主会话已经读过的文字。这两部分代价要计入实验收益。

当前Braid SessionFactory/AgentProvider只有start/resume等接口，没有继承/fork能力。Pi 0.85.1的原生fork/clone会替换当前runtime；SessionManager.open/forkFrom还可能补写来源文件尾行或迁移，不能直接对主会话使用。实际安装源码的ReadonlySessionManager.getBranch与parseSessionEntries/buildSessionContext可以在内存中取得生效消息；按明确leaf使用当前有效分支及最近压缩，需选完整工具结果边界并保存截点。JSONL不包含完整system/profile，原生扩展可以取得当前system；共用要求与cleaner职责应分开装配。历史不必然等于经过扩展改写的最终模型payload，这个证明范围保持明确。不得双写主session或将全历史所有分支当继承结果。首版可以只支持实际选用的Pi，不先为所有provider建设通用fork框架。

## review 请求与责任

Braid Local当前没有request-review/review实体。ready只观察已发布head、切换draft并通知PR显式关注者；它不是请求review、验收通过或合并批准。现有改派会停止实施者并接管其clone，不能用来制造额外reviewer。

建议增加绑定具体候选的review请求，保存PR、请求者、负责验收的关联Issue、固定base/head提交、需求依据版本、审阅者、请求状态与结论/证据入口。只有一个适用关联Issue时请求默认到该Issue现有负责人；多个时显式选择验收Issue，不取第一个、不默认根Issue、不广播所有负责人。请求review与ready保留为不同动作。

Issue负责人可以自行完成review，也可以把这个review请求的执行责任交给专门的reviewer profile。独立reviewer拥有自己的责任身份、可寻址会话、队列和checkout，PR实施者继续持有原assignment与工作树。复用原生session管理，不把PR改成两个实施负责人，也不把review伪装成额外Issue。一个review请求同一时刻一个审阅者即可。具体assignment与wake键的扩展在产品边界复核后细化。

reviewer检查固定候选：代码review侧重类型检查/静态分析未覆盖的行为、逻辑与边界，消费属于该候选的既有检查结果；缺少必要反馈时运行应用现有命令，不先建设通用checks平台。浏览器验收使用独立checkout/服务/临时数据，记录实际运行的commit/tree、操作与观察，不能将实施者仍变化的目录或服务当作冻结候选。review结束不自动等于批准，由审阅者明确提出结论。

后续push不删除旧结论；旧review只能证明旧候选，新候选另发请求。读取及按review合并时比较当前origin base/head与请求版本，目标分支变化同样会使旧结论不再代表当前集成候选；可沿用现有match-head并补充base保护，不需先做Git push监听。首版不额外引入强制审批门禁、多人投票或仲裁政策。

## 实验顺序与判据

四个独立variant共用同一冻结基线、模型和输入，分别改变维护执行、审阅身份或主要浏览器工具；目录与实验次数按具体实施和运行范围确定。

| variant方向 | cleaner | review执行者 | 回答的问题 |
| --- | --- | --- | --- |
| 共同基线 | 无 | 关联Issue现有负责人 | 显式请求、候选绑定及实现/验收分离是否成立 |
| cleaner对照 | 有 | 同基线 | 负责人整理成本与总成本是否净下降 |
| 专门reviewer对照 | 无 | 独立reviewer会话 | 独立上下文及专用材料是否提高真实发现和验收质量 |
| tester.army/e2e工具对照 | 无 | 同基线，优先e2e、保留agent-browser | 主要浏览器/E2E工具变化是否改善交互可靠性、证据与成本 |

三项因素分别核对实际作用后再考虑组合variant。e2e对照保留agent-browser的可用性，但优先入口与指引切换到实际核对的e2e能力；记录主用与回退工具，避免把仅装了包视作采用。官方测试与应用已有确定性检查继续保留，不用AI工具自报通过替代最终验收。历史I13与I14存在其它差异，不能当作严格受控基线。cleaner看整理耗时/模型费用、遗失决定、误hide/resolve、reset与重新理解总成本；reviewer看独立发现并促成修复的问题、浏览器证据对应候选、最终应用表现与新增费用，调用次数和completed不代替收益。先用编译与独立真实操作确认提交竞争、旧review不覆盖新候选、reviewer不替换实施者，再按packet中已获授权的I14-0矩阵取得实际行为。现有I13继续运行，不注入隐藏评分反馈。
