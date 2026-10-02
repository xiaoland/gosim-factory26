# I14：协作职责与独立验收实验

2026-10-01开始，2026-10-02更新。I14-0机制源码与基础反馈已完成，实际采用和收益待运行对账；后续问题改进移至I14-1。本轮收窄为GitHub-only，所有生成模型改用Qwen Token Plan。当前新增冻结与启动等待设施干净基线完成及模型配方就绪，见下方当前树。既有采集与独立GPT-5.6-Luna / low十分钟监控继续消费已保存摘要与告警。

## 用户目标与授权

用户原话：“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”；“等待 I13 的正式运行成果，与 I13 的目标、改进项核对，未完成的、还有优化空间的，交给 I14”。draft范围包括创建契约、CLI、必要文档和真实无模型操作反馈，不改旧PR或旧冻结包。用户已授权自主git commit，提交限当前范围。

I14主要采用不同variant做实验。cleaner帮助Issue/PR负责人hide/resolve comment和维护description，以减少协作整理对工作思考的占用；上下文从对应work-item agent继承，它不是Braid可指派成员或原生sub-agent，按认可方案采用Pi扩展独立推理与Braid结束后原子提交。reviewer则是通过profile配置的Braid成员，PR负责人请求review后由Issue负责人验收，或由Issue负责人另行指派专门reviewer，在PR上生成独立reviewer session，承担代码审查与浏览器手动验收。用户随后提出cleaner的修改与通知应到一次turn结束才正式提交，主线与advisor已将该提交边界及失败/竞争语义纳入方案。2026-10-02用户复核原话：“好的，这个方案没问题。”此为方案复核依据；后续明确开工原话与范围见下节。

用户还要求在root issue提示使用现代TypeScript、避免JavaScript，但若I13应用本已自然使用TS则忽略。已检查保全工作树与发布origin：GLM/Sheet的backend/src仍有六个JavaScript业务源文件，因此I14保留TypeScript偏好；GitHub已有TS，官网Sheet当前导出的src缺失不作语言事实。只在未来I14根Issue约定落地，不改当前I13。

## 当前事实与下一步

最新范围修正（2026-10-02）：用户要求“I14暂停运行sheet题目，只运行github”，并指定所有I14生成模型使用Qwen Token Plan，Base URL为 `https://token-plan.maas.qianwenaiapi.com/compatible-mode/v1`，配套独立key；等待实验DX收尾后配置供应商。本轮待执行范围收窄为四variant各GitHub，四Sheet保留历史记录但不派发。只更新未来实验配方，不原地修改既有冻结输入、历史运行或I13。模型请求、恢复与新启动继续等待DX完成和实际配方就绪。

供应商最终修正（用户原话：“已经配置。好的，那么glm-5.3-flash就使用普通qwen API；而kimi-k3继续使用自有kimi api”）：Token Plan key、普通Qwen key和自有Kimi key均已只读确认非空。沿用模型职责，`glm-5.3-flash`的所有角色走普通Qwen、`kimi-k3`走自有Kimi，其余I14模型继续Token Plan。此指示覆盖上一条“所有模型Token Plan”的两项例外，没有授权静默替换模型。开发侧Codex与既定Luna监控不属于I14生成配方。

| I14模型 | 渠道 | endpoint / key变量 |
| --- | --- | --- |
| glm-5.3-flash（成员、视觉、cleaner及实际采用它的e2e） | 普通Qwen API | QWEN_BASE_URL / QWEN_API_KEY |
| kimi-k3（advisor） | 自有Kimi API | KIMI_BASE_URL / KIMI_API_KEY |
| 其它模型（包括采用时的glm-5.3、内部DeepSeek） | Qwen Token Plan | QWEN_TOKEN_PLAN_BASE_URL / QWEN_TOKEN_PLAN_API_KEY |

`.secrets/models.env`保持权限0600、Git忽略，未输出或更换凭据值；Token Plan endpoint为用户指定的独立地址。未来冻结只注入实际需要的三组凭据，不回退ARC或BigModel。当前未发模型请求，非空检查不等于服务端可用性验收；模型ID按本套餐真实能力核对，DeepSeek版本ID不默认视为别名。官方支持表缺少Flash/K3的问题通过明确供应商例外解决；不采用先前提出的替换模型选项。

生产端尚有一个实际接线边界需DX确认：原native的 `factory26` provider同时容纳GLM-Flash/K3/DeepSeek，而当前 `bind_native_models` 按provider统一改URL/key。这不能仅凭一条factory26绑定落实三个不同供应商。已将用户最终配方及此代码事实交给DX owner收敛有效绑定合同；主线不并行改其源码。供应商配方先保存为未冻结草稿，待DX交付入口后装配并实际读回每个角色/模型的endpoint与credential变量。纸面路由、包内配置和原生实际采用分别记录。

供应商耦合、停止回执契约及owner/资源生命周期归实验DX改进，不另立修补任务。当前工作树四I14入口与共享恢复已移除ARC-only，采用 `scripts/agent_support.py` 的显式 `FACTORY26_MODEL_BINDINGS`（provider/base_url/credential_env），不选择供应商；DX正在真实离线验收，尚未以源码阅读宣称完整收尾。实验入口仍有固定八目标和GLM `qwen-ai`标签校验，运行说明也仍写固定ARC恢复，已交DX owner收敛为显式目标/模型配方并同步文档；未与其并行编辑。同一旧包包含的强制逻辑保持历史身份，只有重新冻结的新包可以纳入已修源码。

2026-10-02，本次整理覆盖用户最新三项修正：“‘强制 ARC’听起来像是过度处置”；“让 GLM-5.3 用 qwen AI”；“实验基础设施即将进行较大的重构和改进；我们整理一下情况”。据此，新增冻结、prepare、launch 和模型请求已暂挂，GLM 与 cleaner 执行者完成交接并结束活跃等待。原官网 Flash/GitHub 及唯一采集器继续；baseline 的用户暂停、旧 dispatcher 和源适配器的 SIGSTOP 保持。以下是当前事实，后续日期段落保留当时操作记录，不构成自动启动依据。

```text
当前实验与改进
├─ I13：四个逻辑运行
│  ├─ Flash/Sheet：正式74/100，通过74/失败26；独立过程分析完成
│  ├─ Flash/GitHub：官网7e8ec62670df继续，12:30 CST原采集器读回RUNNING
│  │  └─ 原native历史完整接续及新工具调用已直接观察；尚无最终评分
│  └─ GLM/GitHub、GLM/Sheet：两源实际stopped，完整选择性保全已核验
│     └─ 未完成生成或上传评分；本次未新冻结、prepare或恢复模型
├─ I14-0：当前仅四variant各GitHub；原八项作为历史矩阵保留
│  ├─ baseline/GitHub：用户暂停，当前物理容器paused
│  ├─ reviewer/GitHub：当前物理容器paused；此前Console适配已部署
│  ├─ cleaner/GitHub：旧源实际stopped；最终恢复包完成，未prepare/launch
│  ├─ e2e/GitHub：未派发，等待DX和新配方
│  └─ 四项Sheet：本轮暂停，不派发
├─ I14材料与机制
│  ├─ draft、cleaner、reviewer、e2e：源码及既有实际操作反馈完成，收益待实验
│  ├─ 隐藏评论聚合：77个同理由隐藏根压为一行，实际投影读回通过
│  │  └─ 新binary进入cleaner候选；该现场没有隐藏thread后代实例，未覆盖此实景
│  ├─ 协作/需求技能：What/Why改写a31eb888完成；Hook暂缓
│  └─ cleaner成员入口：b13f4290完成，已有快照起步、按具体信息缺口查询
│     └─ 最终材料已进入cleaner候选；部署、通知送达、方法采用与收益尚未验证
└─ 实验设施
   ├─ 已有能力：共用Braid内存修复、实际资源采集、输运reentry、模型事实查询
   ├─ DX收尾：ARC约束源码已移除；回执契约与资源生命周期由DX负责
   ├─ 宿主：WSL已恢复；development-2仅备用，未发生迁移或新生成
   ├─ Console：唯一WSL/8765服务可访问；旧cleaner访问器停，未登记新physical run
   └─ 新基线：独立controller/runner与hard-cutoff已开工，真实离线验收中
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
