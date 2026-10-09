# I14：协作职责与独立验收实验

截至2026-10-03，用户授权基建完成后自动开工，无需审核，并要求e2e、cleaner、reviewer全部启动。e2e A2继续官网生成；两项新增候选使用既有WSL/sfp7远端runner本地生成、逐应用官网self_funded评分，正在核实实际运行与存储合同。主线误建的官网等待队列及macOS方向已撤回，两项尚未启动模型。当前只做GitHub、Flash优先；OOM须官网完整生成验证，独立审阅只自动修明确机械缺陷与已证上下文噪声，语义/证据不完整项保留。当前范围与执行身份以[夜间packet](overnight-plan/packet.md)为准，不从下文历史恢复队列或seed audit。已按授权清理更早及不完整运行，仅保留I13-2完整Sheet成果必要材料。

用户新增的 Braid 简短通知作为 I14 共同基线实施：消息列出对象及发生的变化，去掉“查阅正文请用……”操作教学，保留事件与队列语义。此具体源码改动和数据清理已单独完成；本夜新模型实验授权以夜间packet记录的最新用户指示为准。下文与 [前次接续 packet](dx-resume/packet.md)保留历史决定，不从它们恢复已暂停或已清理的队列。

用户最新澄清存储范围：“允许远端执行数据；Mac 侧产物全部放 WorkSSD”。WSL/sfp7执行数据可以保存于远端盘；Mac上的运行回收、控制数据、构建、专属缓存及临时产物全部必须在WorkSSD。前次将I14迁到 `~/.codex/factory26-i14-runs/20261002` 是错误，该外置根已删除；历史系统盘路径不能作为恢复或新启动依据。当前执行身份归夜间packet。

## 用户目标与授权

用户原话：“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”；“等待 I13 的正式运行成果，与 I13 的目标、改进项核对，未完成的、还有优化空间的，交给 I14”。draft范围包括创建契约、CLI、必要文档和真实无模型操作反馈，不改旧PR或旧冻结包。用户已授权自主git commit，提交限当前范围。

I14主要采用不同variant做实验。cleaner帮助Issue/PR负责人hide/resolve comment和维护description，以减少协作整理对工作思考的占用；上下文从对应work-item agent继承，它不是Braid可指派成员或原生sub-agent，按认可方案采用Pi扩展独立推理与Braid结束后原子提交。reviewer则是通过profile配置的Braid成员，PR负责人请求review后由Issue负责人验收，或由Issue负责人另行指派专门reviewer，在PR上生成独立reviewer session，承担代码审查与浏览器手动验收。用户随后提出cleaner的修改与通知应到一次turn结束才正式提交，主线与advisor已将该提交边界及失败/竞争语义纳入方案。2026-10-02用户复核原话：“好的，这个方案没问题。”此为方案复核依据；后续明确开工原话与范围见下节。

用户还要求在root issue提示使用现代TypeScript、避免JavaScript，但若I13应用本已自然使用TS则忽略。已检查保全工作树与发布origin：GLM/Sheet的backend/src仍有六个JavaScript业务源文件，因此I14保留TypeScript偏好；GitHub已有TS，官网Sheet当前导出的src缺失不作语言事实。只在未来I14根Issue约定落地，不改当前I13。

## 历史暂停边界（已由上文清理与新设计覆盖）

当前用户决定为暂停所有实验；实际物理状态以对应原执行回执为准。未经用户新指示，不恢复 I14 任一 variant、Sheet/GitHub 生成、prepare、输运、模型请求或评价；现场、配方草稿和历史回执继续由 [接续 packet](dx-resume/packet.md) 持有。

当前最终配方只作为未来恢复时的输入记录：`glm-5.3-flash`、`glm-5.3` 与 `kimi-k3` 使用普通 Qwen，内部 `deepseek-v4-flash-0731` 使用 Qwen Token Plan。I13 当前 K2.7-Code advisor 的原厂路由保持。实际 endpoint、凭据装配和恢复身份仍须等待 owner 回执。

供应商凭据未输出；未来冻结只注入实际需要的三组凭据，不回退 ARC 或 BigModel。开发侧 Codex 与既定 Luna 监控不属于 I14 生成配方。

| I14模型 | 渠道 | endpoint / key变量 |
| --- | --- | --- |
| glm-5.3-flash（成员、视觉、cleaner及实际采用它的e2e） | 普通Qwen API | QWEN_BASE_URL / QWEN_API_KEY |
| kimi-k3（advisor） | 普通 Qwen API，wire ID `kimi-k3` | QWEN_BASE_URL / QWEN_API_KEY |
| glm-5.3（采用时的根模型） | 普通Qwen API，wire ID `glm-5.3` | QWEN_BASE_URL / QWEN_API_KEY |
| 内部DeepSeek，wire ID `deepseek-v4-flash-0731` | Qwen Token Plan | QWEN_TOKEN_PLAN_BASE_URL / QWEN_TOKEN_PLAN_API_KEY |

`.secrets/models.env`保持权限0600、Git忽略，未输出或更换凭据值；Token Plan endpoint为用户指定的独立地址。未来冻结只注入实际需要的三组凭据，不回退ARC或BigModel。当前暂停后的新配方未发模型请求；此前 e2e 等历史运行事实另按回执记录，非空检查不等于服务端可用性验收。模型ID按本套餐真实能力核对，DeepSeek版本ID不默认视为别名；不采用先前提出的替换模型选项。

生产端的多供应商绑定已由 DX 交付显式 `FACTORY26_MODEL_BINDINGS` 接口；每个角色/模型的实际 endpoint 与 credential 仍须由 [接续 packet](dx-resume/packet.md) 的离线准备和读回证据确认。纸面配方、包内配置和原生实际采用分别记录。

供应商耦合、停止回执契约及 owner/资源生命周期的实现边界归实验 DX；旧包中的强制逻辑保持历史身份，只有重新冻结的新包可以纳入已交付修复。实际准备、恢复和运行是否通过仍以接续 packet 的回执为准。

2026-10-02，本次整理覆盖用户最新三项修正：“‘强制 ARC’听起来像是过度处置”；“让 GLM-5.3 用 qwen AI”；“实验基础设施即将进行较大的重构和改进；我们整理一下情况”。随后 canonical 接续 packet 记录“所有实验暂停”，新增冻结、prepare、launch、模型请求和评价均停止；GLM、cleaner、reviewer、e2e 与 baseline 的现场和回执保留，以下日期段落不构成自动启动依据。

## 历史决定与范围（保全原文）

2026-10-01开始，2026-10-02更新。I14-0机制源码与基础反馈已完成，实际采用和收益待运行对账；后续问题改进移至I14-1。本轮收窄为GitHub-only，所有生成模型改用Qwen Token Plan。当前新增冻结与启动等待设施干净基线完成及模型配方就绪，见下方当前树。既有采集与独立GPT-5.6-Luna / low十分钟监控继续消费已保存摘要与告警。

DX交付后接续（2026-10-02）：用户明确“实验DX改进完成了。现在我们继续推进”，新增准备阶段的暂挂已解除，按最新GitHub-only与三渠道配方接续。DX提交eef231b1完成新controller/runner、逐模型供应商绑定及旧writer退役；实际Docker/Harness恢复、供应商请求仍需本轮取得反馈。主线与两个有界worker已并行处理恢复接线和host交接，当前入口归[接续packet](dx-resume/packet.md)。baseline既有用户暂停保持，先保全/准备；Sheet不派发。

最新范围修正（2026-10-02）：用户要求“I14暂停运行sheet题目，只运行github”，并指定所有I14生成模型使用Qwen Token Plan，Base URL为 `https://token-plan.maas.qianwenaiapi.com/compatible-mode/v1`，配套独立key；等待实验DX收尾后配置供应商。本轮待执行范围收窄为四variant各GitHub，四Sheet保留历史记录但不派发。只更新未来实验配方，不原地修改既有冻结输入、历史运行或I13。模型请求、恢复与新启动继续等待DX完成和实际配方就绪。

```text
暂停前保存的实验与改进快照（2026-10-02 15:12 CST）
├─ I13：四个逻辑运行
│  ├─ Flash/GitHub【第一优先级】
│  │  ├─ 7e8ec62670df：ARC额度耗尽，已取消并保全最终工作区/18份native
│  │  ├─ 原恢复会话：端到端负责修复、准备、官网提交/启动与监控交接
│  │  ├─ 离线准备已派发；替代官网run尚未启动，未取得最终评分
│  │  └─ 配方：Flash普通Qwen；保留K2.7-Code/自有Kimi；DS0731/Token Plan
│  ├─ Flash/Sheet：正式74/100，通过74/失败26；过程分析完成
│  ├─ GLM/GitHub：源已停止、完整选择性保全；待恢复与最终评分
│  └─ GLM/Sheet：源已停止、完整选择性保全；待恢复与最终评分
├─ I14-0：仅GitHub，新生成让位于I13官网恢复
│  ├─ baseline：用户暂停保持
│  ├─ reviewer：旧现场paused，待保全/恢复；Console reviewer适配已部署
│  ├─ cleaner：旧现场stopped且完整保全；热修候选已完成，待准备/恢复
│  ├─ e2e：未派发
│  └─ 四项Sheet：暂停，不派发
├─ I14方法与机制
│  ├─ draft、cleaner、reviewer、e2e：源码与基础操作反馈完成，收益待实验
│  ├─ 隐藏评论聚合：77个同理由根评论压为一行，候选读回通过
│  │  └─ 运行部署效果与隐藏thread后代实景覆盖仍待验证
│  ├─ braid-collaboration＋arc-bench：What/Why改写完成，采用与收益待运行
│  └─ cleaner成员入口简化：完成并进入候选，实际效果待恢复
├─ I14-1：I13结果/目标对账，未达项与后续优化在此收敛
└─ 共同设施
   ├─ DX新controller/runner与旧writer退役：已交付，实际恢复验证正在进行
   ├─ 多供应商接线：旧native身份保留、wire ID和私有凭据装配已完成
   ├─ 恢复实战缺陷：空Pi home与进程监督竞态已修复，等待完整准备反馈
   ├─ development-2：首次域准入已交接，承担断网准备；WSL旧现场保持
   ├─ Console：沿用唯一实例，不增设服务
   └─ 监控：程序负责采集；Luna/low每十分钟消费，新run启动后绑定新身份
```

I13正式结果、费用字段与来源归[实验记录](../iteration13/experiments.md)。两GLM当前恢复边界归[只读交接](../iteration13/i13-2/glm-final-recovery.md)，canonical全保全回执为 `runs/iteration13/i13-2-20261001/arc-hot-recovery-20261002/handoff-state.json`。GitHub 7906项、Sheet 10398项选定进度材料均已逐项核验，含应用/Git、Braid DB/WAL及native历史；这是有明确排除依据的完整选择性保全，不是全volume字节备份。此前Sheet超时的partial与原错误独立保留，不能替代后来成功归档。

cleaner的[恢复packet](cleaner-hidden-context/packet.md)及 `runs/iteration14/cleaner-hidden-context-20261002/stopped-handoff.json` 记录最终ZIP `41d5ddb40887464ed5323f0ba26226e6f6c305c2d34bafe35dd8848a4d27d4ab`。它包含新版binary、两技能与两成员入口，并携带仅名称/路径/hash的一次换版通知计划；没有operation、offline prepare、通知发送或模型请求。保存的prepare脚本并未执行。原现场、helper、volume和旧候选均保留；不将候选组装成功记成部署。

两技能独立会话 [I14：协作与 ARC 需求方法改进](codex://threads/01a0fa92-eb8e-7143-81fa-21eb002790f7) 已完成材料、职责方案与交接，详情归[方法packet](collaboration-requirements/packet.md)。技能保持独立文件，Pi发现入口保留名称、description和路径；四root prompt不重复description。换版通知不统一强制复读，实际职责决定取材。PR2/PR3开场确有对已投影字段的重复读取，但PR3评论29的交接正文未投影，有具体查询价值，因此成员入口改为从已有材料推进、围绕未知定向补充。SVC知识/packet、语义裁决与验收仍由负责人承担，例行description和讨论维护交cleaner。

历史供应商修正记录（最新Token Plan决定见本节开头）：供应商选择收回到实验配方。历史“全部切回ARC，包括GLM-5.3”和“I14继续ARC”解释现有冻结身份；最新Qwen指示作为GLM-5.3下一次配方修正，尚未改运行现场。此前四个I14 run.py及共享恢复入口存在ARC-only拒绝或覆盖；本次DX工作树已移除，实际收尾及新包部署仍待完成。这不是通用Harness的产品规则。其他模型路由、凭据来源和官网费用模式分别冻结，不能把模型渠道变化解释成启用比赛额度。DeepSeek不可成为Braid可指派成员、每run高价模型合计仅一个Braid session、技能不得内联仍是独立约束。下一次启动需冻结修正后的完整模型配方。

WSL本次独立读回仍为 daemon `0c1d4a2e-b921-49be-a075-1e30571f0995`、boot `0569f94d-32fc-4b45-8a89-ba4df70f94c3`，资源与镜像归 `runs/iteration14/wsl-capacity-return-20261002.json`。五槽registry实际保留三个alive owner reservation：baseline/reviewer容器paused、cleaner容器stopped但owner alive；未释放或接管。另一个已编译Runner的development-2候选只作保留资产，不能修改旧operation endpoint或并行重复准备。Console唯一WSL服务 `8cc80cad-d873-49ed-ab49-e958ba8852a3` / port8765，最新GET /api/runs为HTTP200；旧cleaner accessor停止导致具体runtime读取400，新physical run不存在。当前Console Docker接线只支持unix endpoint，不能宣称已支持development-2的SSH context。

本次没有重启daemon/WSL、解除baseline暂停、cleanup源、创建第二Console或collector。下一步先完成设施新基线的方案/实施范围复核，再以原件和明确配方接续，不能让已结束的恢复worker继续无任务等待。新Flash/GitHub的OTLP flush HTTP503仍作为辅助采集缺陷保留，生成继续且本地原件存在；根因未知，不据此认定生成终态或OOM。

## 独立实验设施会话

原 [Factory26 实验启动、热恢复与监控自动化](codex://threads/01a0f82f-23db-74d3-85b4-901b3b23fff0) 已完成并提交897f307，提供已有operation/admission/采集等能力；其上一轮实现已结束，不是当前大重构的活跃执行者。当前大重构的方案owner为 [实验 DX：模型路由与运行配置可见性](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)，权威任务为 [设施DX复核](../experiment-dx-review/packet.md)。用户在该会话明确支持hard-cutoff、干净基线、长期正确优先，随后授权“开工；你可以自由提交”；owner已进入完整controller/独立runner实现及真实离线验收，尚未交完整收尾。旧P0兼容准备已撤回。本轮不启动模型、不停止/迁移活动实验、不部署或重启Console。

主线已将最新Qwen/ARC边界、两源完整保全、停止回执schema不匹配、三个保留reservation、cleaner未启动候选及唯一采集/Console事实交给该owner，不另建竞争的重构线。新基线需要区分controller意图与runner执行效果、检查点语义与输运、原件身份与portable引用、独立执行/采集生命周期，并覆盖新旧切换与活动旧run交接。已有功能不冒充新基线完成；本次整理不自动授权停止或迁移活动官网run。

## tester.army/e2e 工具对照

用户新增原话：“还增加一个 variant，引入 tester.army/e2e（替代 agent-browser 生态位，但也不会移除 agent-brwoser）”。保留agent-browser可用，新增variant以e2e承担主要浏览器交互/端到端反馈职责；如何覆盖这个生态位以官方真实能力核对，不提前假定它只是另一个浏览器CLI。独立资料负责人核对官方页面、发布来源、版本、模型/API与浏览器/证据接口，结论归 tester-e2e.md。

该项与cleaner、专门reviewer分开作为工具因素。建议同共同基线配对，只改变优先浏览器/E2E能力，cleaner关闭、review仍由Issue现有负责人执行，保留agent-browser后记录实际使用哪条工具路径。已有Playwright确定性验收与官方benchmark仍保留；不因引入工具就删除原验收判据。是否另设专门reviewer搭配e2e的组合，等独立效果成立后决定。


## I14-0 开工与实验冻结（历史阶段记录）

当时用户原话：“本地（WSL）运行现在应该有两个槽位，我们扩充到5个，并且将内存缩小到 2GiB 来贴近官网runner的配置；I14-0 实验不必等待I13的运行完成和问题改进了，这些留到 I14-1；I14 不使用 ARC API，而是我们自有的 bigmodel, kimi, ds, qwen。我已经相当于授权你开工，你可以实现、基础验收、启动实验。”用户同时恢复“gpt-5.6-luna low 继续监控（每10分钟）各运行”，要求复用脚本能力。该指示是本轮源码、基础真实反馈和具体实验的开工依据。

本轮 experiment_key 为 e20261002-01、batch 为 i14-0。四个独立variant为 pi-braid-i14、pi-braid-i14-cleaner、pi-braid-i14-reviewer、pi-braid-i14-e2e，各自从干净起点运行 GitHub 与 Sheet 一次，共八项。允许需求沿用 I13 已冻结的官方题目需求包，不读取外部测试或旧应用。共同模型配方按最新修正使用自有ARC额度：根与普通Braid成员GLM-5.3-Flash / high，原生advisor Kimi K3，内部DeepSeek Flash可用于sub-agent，不能成为Braid可指派成员。备用GLM-5.3根profile带root-only，任何run的高价模型Braid session总量只允许一个，保留现有预算保护。视觉模型GLM-5.3-Flash。各组仅机制/工具因素不同，不增加根模型因素或重复次数。

所有新增生成run使用 Debian-Rebuild / development-1 的远程Docker，2GiB/2CPU，共享并发上限5，包含仍在运行的I13两项。已有I13两个4GiB运行保持当前资源；因此初期最多三个新run，旧run结束后可填到五个新run。启动前核对实际容器与宿主身份/容量，不把每个controller的max_parallel=5当全宿主约束。主线从既有私有ARC模型env注入本轮自有ARC key，不启用比赛额度，不修改本地I13两项的自有供应商路由。

完成条件为完整生成、冻结准确最终应用，然后按既有非参赛self_funded应用重放取得官网分数；重放不调用生成模型，不以生成失败或设施故障充当有效零分。每题独立完成即重放，原生成和重放的耗时/费用分别保存，不等同批其它题。隐藏评分不送给仍在生成的Agent。首批基础验收包括Braid编译、真实独立Git/对象操作/旧数据库迁移与e2e实际MCP，原生cleaner与reviewer的实际采用在授权实验中保存provider身份和候选证据。禁止基础设施测试、伪造turn或包smoke。

唯一I14索引为 runs/iteration14/i14-0/active-matrix.json，输入/包/运行/监控回执分别保存在同目录；未生成字段不能冒充已启动。独立设施会话负责shared admission与启动/监控程序接口，主线负责具体输入冻结和首次读回。只复用既有Console，不能新建实例。

原监控会话 I13 实验监控已解除归档并设置 gpt-5.6-luna / low。旧 i13-wsl automation 的更新返回“does not exist”，故在同会话创建唯一 i13-i14 heartbeat，ACTIVE、每十分钟；不另开采集器。其通知仅限明确新故障、终态或用户决策，普通进展保持安静。


用户随后覆盖供应商决定：“我们继续使用 ARC API 就好”，I14-0据此使用ARC通道，本地I13仍保留自己的已冻结路由。用户还授权：I13正式结果若GLM-5.3根更好，仅调整尚未开始生成的I14项；其明确判据为“两题平均分至少高10个百分点”。比较必须有GitHub/Sheet两题、Flash/GLM两组的正式最终分数，不用过程/阶段分数推断。默认Flash先启动，已经开始生成的项不改；pending项切换时保存新的冻结输入和原队列关系，禁止改写旧包、manifest或已发生请求。该切换会使不同root模型分层解释结果，不能合并成严格同模型对照。

2026-10-02，cleaner/reviewer已完成源码、联合编译、真实对象/Git拒绝与恢复反馈。reviewer已有81条操作、v16数据库完整图迁移及两类保存intent真实中断恢复；正常原生reviewer权限与浏览器候选对应关系留给正式运行。cleaner真实有效历史继承及旧身份/外部调用拒绝已证，正常模型提交与竞争限界留给第一条正式cleaner运行。e2e实际双checkout MCP交互、图像与有reaper的关闭反馈已完成；一次ARC Flash explore实际点击成功，但结构化extract存在两次MODEL_OUTPUT_INVALID后修复及一次规划不确定回退，不将它宣称为无异常判断链。证据分别归 cleaner-implementation.md、reviewer-implementation.md、tester-e2e.md。

四份Linux ZIP已冻结在 runs/iteration14/i14-0/packages，共同Braid二进制SHA256为 e002edb848395698ab83d2221ec40a13bcfa8c2e379bf7ca26f90389d02260e8，源码清单和包身份归同目录 linux-braid/source-identity.json、packages.json。根目录.env.i13key已不存在，工具key复用I13-2冻结私有tool-env.json，不在聊天或仓库正文中记录值。

已采用 [有限实验dispatcher](../../experiments/i14-0/README.md)，复用独立设施会话的operation prepare/run、shared admission、采集和自动应用重放。每目标稳定一个operation目录；逐项选择root、保存selection、冻结私有MODELenv及recipe，再等实际admission事实才放出下一项。snapshot不能预约槽，真正五槽限制由admit实现。模型承诺点是该项派发冻结，未来未派发目标可采用新结果；冻结到实际准入存在短暂窗口，不能宣称所有尚未实际执行项都可原地切换。发生失联或明确失败时安全停止队列并保留原operation，身份核查后恢复同一记录，不新增尝试。唯一active-matrix是聚合引用，各operation保留自己的采集目录，Luna每十分钟消费已有证据。

## 2026-10-02 ARC-only 与共用 Braid 修复（历史实施记录）

用户要求后续 I14 不在任何地方使用自有模型 API；Context7/Exa 工具凭据不属于模型供应商切换。本次 canonical 四入口、子 Agent 原生 modelScope、e2e 和 dispatcher 已拒绝非 ARC endpoint/分离 key，并移除继承的供应商认证。实际四次 prepare-only 完成，九模板均 ARC，同一 FACTORY26_API_KEY；四个非 ARC URL 在创建输出目录前被拒绝。详细边界和证据归 [arc-only.md](arc-only.md)。运行/排队的旧冻结制品没有现场修改，不能声称已经部署新保护。

用户要求明确 OOM 缺陷的修复覆盖全部 Braid variant。共用 sources/braid 已实施 claim 前的资源就绪保护、对象快照排序内存改进以及原生状态/capture 内存证据；公共 collector 补充存活进程内存归因。新制品和热恢复须绑定修复编译身份，旧冻结原件保留。当前三个 I14 运行不因开发源码更新自动改变；I13 正在优先停写保全并使用修复包恢复。I14 dispatcher 为保护本地 I13 两个替换槽位已暂挂；各生成容器的实际状态见下方读回，恢复调度以对应 operation/admission 回执为准。

用户已授权独立 GPT-6.1-Sol/medium 会话 01a0fa4f-471a-7963-a4e5-bc4a6071113e 改进实验 DX，直接暴露 desired/frozen/actual 模型、endpoint 与配置来源，避免依赖专门审计才能核对正常运行事实。该会话不启动或改动实际实验。后续 GPT-6.1-Sol 统一 medium。

## 2026-10-02 隐藏评论与 reviewer 展示

用户明确授权将同一隐藏理由的评论压成一行，例如 `# Comments 759,756,892 hidden (reason)`，隐藏 thread 仅保留 hidden 的根评论参与新上下文，并立即至少热修复 I14 cleaner。独立 GPT-6.1-Sol/medium 会话 `01a0fa5d-2c5e-7963-b2a5-3a29bb5e74df` 拥有 context renderer 与 cleaner-hidden-context 的私有恢复操作；它编译的新 source 应包含已完成的共用 Braid 资源修复。旧原生历史不会因 hide 自动删除，新投影与恢复后实际发送需分别核验。

用户另要求调查已合并 reviewer run 的 PR2 为何在 Exp Console 看不到 reviewer。独立同模型/effort 会话 `01a0fa5e-eb26-7f23-bca6-2949d9d3416a` 负责核对真实 review/session 记录及修复 Console 展示，沿用唯一现有服务；不据 UI 缺失宣称底层 reviewer 未运行，也不伪造历史。两会话不恢复 I14 dispatcher、不占 I13 替换槽、不停止其它生成。

主线 Braid/collector 源码已完成，可冻结共同修复；具体编译身份与共享 recovery 接线就绪见 I13-2 packet 的 `linux-fix/handoff.json`。新 cleaner 自身代码必须另行编译及绑定新身份。

截至10:48 CST独立读取实际Docker Unix API，baseline 容器9a780621…为 paused，用户已确认这是其主动暂停；cleaner72d333b8…已为本任务物理停止，Pid0/Exit137，属于主动切换；reviewer b32fc9ef…仍running，三者均OOMKilled=false。不能笼统称三个都在生成。cleaner独立会话已提交聚合修复 `33b9e382`，同一真实root投影从10696减至4833 bytes，77个同reason隐藏根聚合一行；该现场没有隐藏thread实例，thread规则尚缺真实运行实例验收。新Linux binary `63fdabce…` 含共用内存修复；当前完整保全/热恢复仍在继续，未据编译声称已热部署。

Console 展示修复已完成并提交 `226449f8`，部署到唯一现有 service `8cc80cad-d873-49ed-ab49-e958ba8852a3`，沿用 http://127.0.0.1:8765。真实 PR2 存在 reviewer-1 的 review #1、Approved 结论及对应 agent/provider/native session；已通过实际浏览器操作核对 PR 到 review、会话、原生对话和工具内容的导航。证据与历史离线展示限制归 [Console reviewer packet](../console-reviewer/packet.md)。这证明 reviewer 的执行及展示关系，不单独证明应用验收结论正确。

cleaner 切换还须处理 Console 访问入口。独立恢复会话已停止仅属于旧 cleaner 的 accessor，避免切换期间发生外部 CLI 写入；共享 HTTP 服务及其它运行入口保留。原 run 登记不能改指向另一个现场。恢复会话负责提供新 physical run、volume/container、Braid namespace 与 binary SHA；主会话负责通过原唯一服务登记接续运行并保留旧运行与恢复来源关系。新 accessor 须使用 `63fdabce…` binary，不能使用仍带旧 context renderer 的 CLI。不因等待 Console 登记阻塞恢复操作自身的保全、准备及生成。

## 2026-10-02 比赛规则变化与待核实边界

用户本次转达主办方公告，以下为公告事实，尚未独立核对平台实际行为。最终成绩仅采用最后一次保存的提交；新提交不继承旧提交成绩。同一提交下每项任务可以多次运行，采用得分最高一次运行对应的通过数与开销，不能分别拼接最佳通过数和最低开销。公告建议在最终提交下分别运行 Sheet 和 GitHub；若最新提交全部任务为零分或未运行，可以删除该提交。前端任务绿点表示已有运行成绩。截止仅限制提交，不中断已经开始运行的任务；公告未给出新的具体截止时间。

GitHub 原题保留，并新增三个渐进阶段；两条路线均按最后一次提交的结果计算并取较高得分。公告称 Stage 1 已开放，规模约为原题三分之一，Stage 2、Stage 3 将于公告所称“今天”陆续开放；不能据此认定现在已经开放。后续阶段以“上一阶段最新提交中得分最高运行对应的应用”为起点，没有可用应用则从空模板开始。只完成 Stage 1 也可获得累计成绩并上榜。阶段累计公式、阶段费用合并方式及跨提交接续的实际接口尚未核实。

公告提供 https://arcbench-selftest-web.vercel.app 的 GitHub Stage 快速评测入口，允许上传已生成应用并跳过智能体运行。本次网页读取工具无法访问该入口，未取得其页面或接口事实；是否进入正式榜单、费用模式、上传布局及阶段选择仍待核实。快速评测可用不自动授权在正式 Harness 中预置赛题应用，也不改变本轮冻结的 self_funded 重放身份。

现行 docs/deployment/competition.md 中“最终取历史有效正式提交的最高分”已经被本公告覆盖，“每次同时运行两题、两题结束后形成提交成绩”的表述也需按新任务运行方式重新核实。原计分公式保留其历史来源；公告没有完整说明阶段累计如何代入公式，不能自行推导。此处先保存当前调查与决策依据，未修改长期规则正文或源码。

本次授权边界：用户提供比赛变化，未要求新建提交、删除提交、启动阶段路线、切换现有输入或消耗额外额度。I13/I14 已授权恢复与实验保留原冻结输入、应用身份和对照范围；Stage 1/2/3 应分别登记需求、来源应用、提交与运行身份，不能混入原题结果。下一步先核对阶段需求、接续契约、快评计分身份与截止时间，再向用户呈现具体阶段实验范围。
