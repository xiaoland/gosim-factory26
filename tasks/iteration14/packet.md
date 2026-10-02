# I14：协作职责与独立验收实验

2026-10-01开始，2026-10-02更新。用户已明确授权 I14-0 实现、基础验收和实验启动，不等待 I13 正式成果；I13 完成后的问题改进与目标对账移至 I14-1。PR 创建默认 draft 已提交 e7d88e7。cleaner、reviewer 和 e2e 接线已委派实施，主线负责共同 variant、基础集成、冻结矩阵及启动。现有 I13 不热改本轮包；采集继续复用原脚本，独立 GPT-5.6-Luna / low 监控恢复为每十分钟消费已保存摘要与告警。

## 用户目标与授权

用户原话：“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”；“等待 I13 的正式运行成果，与 I13 的目标、改进项核对，未完成的、还有优化空间的，交给 I14”。draft范围包括创建契约、CLI、必要文档和真实无模型操作反馈，不改旧PR或旧冻结包。用户已授权自主git commit，提交限当前范围。

I14主要采用不同variant做实验。cleaner帮助Issue/PR负责人hide/resolve comment和维护description，以减少协作整理对工作思考的占用；上下文从对应work-item agent继承，它不是Braid可指派成员或原生sub-agent，按认可方案采用Pi扩展独立推理与Braid结束后原子提交。reviewer则是通过profile配置的Braid成员，PR负责人请求review后由Issue负责人验收，或由Issue负责人另行指派专门reviewer，在PR上生成独立reviewer session，承担代码审查与浏览器手动验收。用户随后提出cleaner的修改与通知应到一次turn结束才正式提交，主线与advisor已将该提交边界及失败/竞争语义纳入方案。2026-10-02用户复核原话：“好的，这个方案没问题。”此为方案复核依据；后续明确开工原话与范围见下节。

用户还要求在root issue提示使用现代TypeScript、避免JavaScript，但若I13应用本已自然使用TS则忽略。已检查保全工作树与发布origin：GLM/Sheet的backend/src仍有六个JavaScript业务源文件，因此I14保留TypeScript偏好；GitHub已有TS，官网Sheet当前导出的src缺失不作语言事实。只在未来I14根Issue约定落地，不改当前I13。

## 当前事实与下一步

2026-10-02 10:48 CST，用户要求先停下来用树整理，主线暂停新的技能改造和额外启动；在途保全继续。用户明确说明 baseline 是其主动暂停，并授权将下一项改进集中在 braid-collaboration 与 ARC 需求方法，热修复到 I14 系列。当前独立分析报告实际对应官网 Flash/Sheet，arc-requirements 的现行技能名称是 arc-bench；不把它记作尚未取得正式结果的本地 GLM/Sheet。

```text
当前实验与改进
├─ I13
│  ├─ Flash/Sheet：正式74分，独立过程分析完成
│  ├─ Flash/GitHub：官网7e8ec62670df已RUNNING；原native历史完整接续，新工具调用已观察
│  ├─ GLM/GitHub：7906项完整选择性保全；源此前仅paused，实际stop仍待确认，接续未启动
│  └─ GLM/Sheet：唯一输运1800秒超时；partial保留，不作为完整恢复快照，接续未启动
├─ I14-0：四variant×两题；dispatcher暂挂，不新增实验矩阵
│  ├─ baseline/GitHub：用户主动暂停，保持暂停
│  ├─ cleaner/GitHub：旧source已物理停止，聚合修复读回通过，保全/热恢复继续
│  ├─ reviewer/GitHub：此前running、Console修复已部署；WSL不可用后当前状态未确认
│  ├─ e2e/GitHub及四项Sheet：五项仍待派发
│  └─ 各组共有技能改进：首轮材料已提交；What/Why及cleaner职责入口再迭代，待最终冻结/热部署
└─ 共同设施
   ├─ Braid资源等待/快照内存与新增证据：共用源码已编译，旧运行不自动更新
   ├─ ARC-only与模型DX：源码已完成，具体部署以各恢复/新冻结回执为准
   ├─ prepared-workspace输运：共享reentry已提交，实际完整读回与唯一官网接续通过
   └─ WSL/SSH/Docker/存储：homelab独立会话诊断，主线不重启daemon或WSL
```

用户指定的 homelab / GPT-5.6-Sol / medium 会话已创建并实际开始：[WSL 实验基础设施：恢复传输阻塞排查与修复](codex://threads/01a0fa82-8883-7cc0-942b-8cf8cb1a16c3)。它负责宿主设施，Factory26 lab/arc_bench/recovery.py 仍由 i14_arc_only_implementation 单独负责，官网恢复会话只读该共享文件。主线保留整体协调及启动门控。修复只针对有证据的原因，不由Docker CLI超时认定daemon全挂、OOM或磁盘损坏。

用户随后明确“好的，继续推进”，并授权尝试 sfp7 的 development-2，之后将“恢复 I13 flash/github”设为第一优先级。主线已实读新 endpoint `ssh://sfp7-ws.localhost`、daemon `e316f857-fe3d-4e7b-8236-9376f063fedc`：Linux x86_64、8CPU、约15.2GiB内存、可用约13.3GiB、磁盘剩余约174GiB、PSI接近零，只有现有Redis服务，没有Factory实验。旧operation的冻结endpoint不改；准备或迁移到新host须登记新操作身份，保全和停止门控仍保留。旧WSL当前不可用，下方此前的容器读回保留其观察时点，不冒充现在仍可控制。

两项技能工作已并行交给 [I14：协作与 ARC 需求方法改进](codex://threads/01a0fa92-eb8e-7143-81fa-21eb002790f7)，GPT-6.1-Sol/medium。它独占 harness/skills/braid-collaboration/ 与 harness/skills/arc-bench/ 及[任务包](collaboration-requirements/packet.md)，已提交材料 ed9a97bb、部署接口复核 60ba2e01；主线负责新材料冻结和实际热恢复。该会话不操作run/Console，不修改Braid、shared recovery或packager，不阻塞Flash/GitHub。完成材料不等于现场已部署或产生改进效果。

保留四个root prompt源码：Pi原生技能发现已提供名称、description和路径，根Issue不再重复description。恢复输入须携带完整新技能目录，并向实际接续消费者传一次技能名称、实际文件路径、新主文件hash及继续当前工作前重新读取的通知；不内联正文、不要求全员ACK。部署读回、通知送达及相关决定中的实际采用分别取证。完整旧新hash和方法复核归独立任务包。

development-2所需Runner已编译并交cleaner独立恢复owner：镜像 `sha256:3d51899c61e6464242a7545a1badb6445f368f4757828fd36f040c6954b56681`，daemon身份仍为 `e316f857-fe3d-4e7b-8236-9376f063fedc`。冻结Runner来自I13已使用的control/runner，官方base固定为 `gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de`；断网、501:20直接读取运行metadata为CPython3.12.3、glibc2.39、Linux/x86_64，退出0，无模型或原source重启。构建与读回原件归 `runs/iteration14/development2-runner-20261002/`。新image只能进入新操作冻结输入，不能改写旧endpoint或冒充旧image；同一宿主原Redis服务未修改。

cleaner已保存 `cleaner-hidden-context-20261002/skills-refresh-recovery-plan.json`，明确Issue1/root glm-1与仍实施PR3的glm-3是实际消费者，不唤醒完成的glm-2。共享owner正在补显式恢复通知输入：prepare-only只核对/冻结计划，runtime在材料刷新与ARC保护之后、首次launch前，通过现有normal comment与request-id发送一次并留回执；不临时修改DB或native历史。旧3ce599fb保留其材料刷新/ARC身份，新接口需新hash/最终ZIP后方可实际prepare/恢复。

用户随后补充cleaner目标：“让 work-item agent 不必 'Let me start by reading the braid-collaboration skill and viewing the PR.'”。两成员instructions首段确实无条件要求开始/接续时读取该技能；具体原生句与PR投影内容仍由方法会话定向核对。改进要区分例行对象整理与实施、交接、需求裁决和验收的判断责任；同时确认初始PR快照覆盖了什么，不能仅把必要查询一律关闭。方法会话还收到用户直接授权：Skill主体应围绕足以区分选择的What/Why，暂缓Hook，同意其下一步。这些新决定纳入同一材料线，首轮ed9a97bb/60ba2e01保留历史身份；当前候选冻结和强制重读两主文件的通知不当最终部署，cleaner首次launch待职责方案与最终新材料收敛。

恢复通知接口首轮已ready，packager `7ea9f02f…`、main `a12ae58d…`，仅增加显式 `--material-notice-plan`，lab unchanged。CLI的comment实际没有request-id；计划request_id只是本次冻结输入身份，不是CLI原生幂等键。发送前保存pending，成功或重入以正常comment id、目标、external作者、bodySHA及实际delivery唯一核对；pending后零/多条或结果不明不重发并阻断launch。prepare-only不发送通知，不写DB/native。接口及旧候选保留供最终材料接续，尚未实际prepare/launch，不据源码就绪宣称通知或材料采用已经发生。

技能改进的判断依据是分析报告已经区分的义务交接、原文与新增约定冲突、真实跨层调用及合并证据充分性；不是单纯增加读取次数、篇幅或模板。改进保持通用Harness边界，ARC特定方法仍归独立技能与根Issue入口。热修复须记录各run的旧/新技能身份与实际采用时点，避免把混合版本的过程视为从启动起统一使用新方法；不将隐藏评分或具体失分答案送入仍生成的Agent。

新PR创建默认draft已完成并提交e7d88e7，保留--draft兼容，继续用pr ready/--undo；不改旧PR、迁移或request-id重试状态。主线独立读取前后SQLite、具体merge错误、实际Git效果和编译原件；原生session数量为零，准备阶段真实blocked不当成功运行。[draft记录](draft.md)保存命令、错误和覆盖边界。

review接缝已查明：ready不是请求验收，PR单负责人改派会停止实施者；需要独立的review请求与执行责任。cleaner的原生继承能力已核对Pi0.85.1实际源码，不能直接用会切换主runtime的fork/clone。advisor已独立建议按需维护操作、结束后一次提交、固定候选review和三个独立variant方向。产品边界、提交竞争与实验判据归[机制方案](mechanisms.md)；I13承接与语言依据归[证据对账](evidence.md)。原始观察归runs/iteration14；确定的Braid产品契约回归其PRD/TDD，Factory实验安排回归对应variant/配方。

cleaner/reviewer实施准备已经完成，详见 cleaner-preparation.md、reviewer-preparation.md。开源e2e实际发布及MCP接缝已核对，见 tester-e2e.md。按最新开工授权完成代码、真实操作反馈和I14-0实验；I13正式成果继续由原采集脚本收集，之后逐项移交I14-1。

I13目标与当前过程验收分别归 tasks/iteration13/packet.md、tasks/iteration13/i13-2/process-acceptance.md；正式身份与进展归 tasks/iteration13/experiments.md。当前本地GLM两项为a94a67b4b3d85b/8046cfb0695023，官网Flash/Sheet为f16834f58674，官网Flash/GitHub为7e8ec62670df，旧e1aa595f6995已取消保全。创建完成、过程采用、最终评分分别保留证据，未触发机制不自动标为失败。

## 独立实验设施会话

用户明确要求“安排另一个独立的会话去改进实验基础设施”，范围为热恢复、本地/官网启动与持续监控，也允许改造必要的Braid/Factory接口。已创建并确认[Factory26 实验启动、热恢复与监控自动化](codex://threads/01a0f82f-23db-74d3-85b4-901b3b23fff0)正在开展调查。它拥有设施自动化线，当前会话拥有I14机制/variant线；创建prompt已给出I13真实journal/回执、费用模式与在途源码边界。不再把重复手拼启动/恢复流程混进I14机制方案，不建立第二Console或并行采集。具体方案与后续实施由该会话独立向用户复核。

## tester.army/e2e 工具对照

用户新增原话：“还增加一个 variant，引入 tester.army/e2e（替代 agent-browser 生态位，但也不会移除 agent-brwoser）”。保留agent-browser可用，新增variant以e2e承担主要浏览器交互/端到端反馈职责；如何覆盖这个生态位以官方真实能力核对，不提前假定它只是另一个浏览器CLI。独立资料负责人核对官方页面、发布来源、版本、模型/API与浏览器/证据接口，结论归 tester-e2e.md。

该项与cleaner、专门reviewer分开作为工具因素。建议同共同基线配对，只改变优先浏览器/E2E能力，cleaner关闭、review仍由Issue现有负责人执行，保留agent-browser后记录实际使用哪条工具路径。已有Playwright确定性验收与官方benchmark仍保留；不因引入工具就删除原验收判据。是否另设专门reviewer搭配e2e的组合，等独立效果成立后决定。


## I14-0 开工与实验冻结

用户最新原话：“本地（WSL）运行现在应该有两个槽位，我们扩充到5个，并且将内存缩小到 2GiB 来贴近官网runner的配置；I14-0 实验不必等待I13的运行完成和问题改进了，这些留到 I14-1；I14 不使用 ARC API，而是我们自有的 bigmodel, kimi, ds, qwen。我已经相当于授权你开工，你可以实现、基础验收、启动实验。”用户同时恢复“gpt-5.6-luna low 继续监控（每10分钟）各运行”，要求复用脚本能力。该指示是本轮源码、基础真实反馈和具体实验的开工依据。

本轮 experiment_key 为 e20261002-01、batch 为 i14-0。四个独立variant为 pi-braid-i14、pi-braid-i14-cleaner、pi-braid-i14-reviewer、pi-braid-i14-e2e，各自从干净起点运行 GitHub 与 Sheet 一次，共八项。允许需求沿用 I13 已冻结的官方题目需求包，不读取外部测试或旧应用。共同模型配方按最新修正使用自有ARC额度：根与普通Braid成员GLM-5.3-Flash / high，原生advisor Kimi K3，内部DeepSeek Flash可用于sub-agent，不能成为Braid可指派成员。备用GLM-5.3根profile带root-only，任何run的高价模型Braid session总量只允许一个，保留现有预算保护。视觉模型GLM-5.3-Flash。各组仅机制/工具因素不同，不增加根模型因素或重复次数。

所有新增生成run使用 Debian-Rebuild / development-1 的远程Docker，2GiB/2CPU，共享并发上限5，包含仍在运行的I13两项。已有I13两个4GiB运行保持当前资源；因此初期最多三个新run，旧run结束后可填到五个新run。启动前核对实际容器与宿主身份/容量，不把每个controller的max_parallel=5当全宿主约束。主线从既有私有ARC模型env注入本轮自有ARC key，不启用比赛额度，不修改本地I13两项的自有供应商路由。

完成条件为完整生成、冻结准确最终应用，然后按既有非参赛self_funded应用重放取得官网分数；重放不调用生成模型，不以生成失败或设施故障充当有效零分。每题独立完成即重放，原生成和重放的耗时/费用分别保存，不等同批其它题。隐藏评分不送给仍在生成的Agent。首批基础验收包括Braid编译、真实独立Git/对象操作/旧数据库迁移与e2e实际MCP，原生cleaner与reviewer的实际采用在授权实验中保存provider身份和候选证据。禁止基础设施测试、伪造turn或包smoke。

唯一I14索引为 runs/iteration14/i14-0/active-matrix.json，输入/包/运行/监控回执分别保存在同目录；未生成字段不能冒充已启动。独立设施会话负责shared admission与启动/监控程序接口，主线负责具体输入冻结和首次读回。只复用既有Console，不能新建实例。

原监控会话 I13 实验监控已解除归档并设置 gpt-5.6-luna / low。旧 i13-wsl automation 的更新返回“does not exist”，故在同会话创建唯一 i13-i14 heartbeat，ACTIVE、每十分钟；不另开采集器。其通知仅限明确新故障、终态或用户决策，普通进展保持安静。


用户随后覆盖供应商决定：“我们继续使用 ARC API 就好”，I14-0据此使用ARC通道，本地I13仍保留自己的已冻结路由。用户还授权：I13正式结果若GLM-5.3根更好，仅调整尚未开始生成的I14项；其明确判据为“两题平均分至少高10个百分点”。比较必须有GitHub/Sheet两题、Flash/GLM两组的正式最终分数，不用过程/阶段分数推断。默认Flash先启动，已经开始生成的项不改；pending项切换时保存新的冻结输入和原队列关系，禁止改写旧包、manifest或已发生请求。该切换会使不同root模型分层解释结果，不能合并成严格同模型对照。

2026-10-02，cleaner/reviewer已完成源码、联合编译、真实对象/Git拒绝与恢复反馈。reviewer已有81条操作、v16数据库完整图迁移及两类保存intent真实中断恢复；正常原生reviewer权限与浏览器候选对应关系留给正式运行。cleaner真实有效历史继承及旧身份/外部调用拒绝已证，正常模型提交与竞争限界留给第一条正式cleaner运行。e2e实际双checkout MCP交互、图像与有reaper的关闭反馈已完成；一次ARC Flash explore实际点击成功，但结构化extract存在两次MODEL_OUTPUT_INVALID后修复及一次规划不确定回退，不将它宣称为无异常判断链。证据分别归 cleaner-implementation.md、reviewer-implementation.md、tester-e2e.md。

四份Linux ZIP已冻结在 runs/iteration14/i14-0/packages，共同Braid二进制SHA256为 e002edb848395698ab83d2221ec40a13bcfa8c2e379bf7ca26f90389d02260e8，源码清单和包身份归同目录 linux-braid/source-identity.json、packages.json。根目录.env.i13key已不存在，工具key复用I13-2冻结私有tool-env.json，不在聊天或仓库正文中记录值。

已采用 [有限实验dispatcher](../../experiments/i14-0/README.md)，复用独立设施会话的operation prepare/run、shared admission、采集和自动应用重放。每目标稳定一个operation目录；逐项选择root、保存selection、冻结私有MODELenv及recipe，再等实际admission事实才放出下一项。snapshot不能预约槽，真正五槽限制由admit实现。模型承诺点是该项派发冻结，未来未派发目标可采用新结果；冻结到实际准入存在短暂窗口，不能宣称所有尚未实际执行项都可原地切换。发生失联或明确失败时安全停止队列并保留原operation，身份核查后恢复同一记录，不新增尝试。唯一active-matrix是聚合引用，各operation保留自己的采集目录，Luna每十分钟消费已有证据。

## 2026-10-02 ARC-only 与共用 Braid 修复

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
