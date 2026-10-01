# I14：协作职责与独立验收实验

2026-10-01开始，2026-10-02更新。用户已明确授权 I14-0 实现、基础验收和实验启动，不等待 I13 正式成果；I13 完成后的问题改进与目标对账移至 I14-1。PR 创建默认 draft 已提交 e7d88e7。cleaner、reviewer 和 e2e 接线已委派实施，主线负责共同 variant、基础集成、冻结矩阵及启动。现有 I13 不热改本轮包；采集继续复用原脚本，独立 GPT-5.6-Luna / low 监控恢复为每十分钟消费已保存摘要与告警。

## 用户目标与授权

用户原话：“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”；“等待 I13 的正式运行成果，与 I13 的目标、改进项核对，未完成的、还有优化空间的，交给 I14”。draft范围包括创建契约、CLI、必要文档和真实无模型操作反馈，不改旧PR或旧冻结包。用户已授权自主git commit，提交限当前范围。

I14主要采用不同variant做实验。cleaner帮助Issue/PR负责人hide/resolve comment和维护description，以减少协作整理对工作思考的占用；上下文从对应work-item agent继承，它不是Braid可指派成员或原生sub-agent，按认可方案采用Pi扩展独立推理与Braid结束后原子提交。reviewer则是通过profile配置的Braid成员，PR负责人请求review后由Issue负责人验收，或由Issue负责人另行指派专门reviewer，在PR上生成独立reviewer session，承担代码审查与浏览器手动验收。用户随后提出cleaner的修改与通知应到一次turn结束才正式提交，主线与advisor已将该提交边界及失败/竞争语义纳入方案。2026-10-02用户复核原话：“好的，这个方案没问题。”此为方案复核依据；后续明确开工原话与范围见下节。

用户还要求在root issue提示使用现代TypeScript、避免JavaScript，但若I13应用本已自然使用TS则忽略。已检查保全工作树与发布origin：GLM/Sheet的backend/src仍有六个JavaScript业务源文件，因此I14保留TypeScript偏好；GitHub已有TS，官网Sheet当前导出的src缺失不作语言事实。只在未来I14根Issue约定落地，不改当前I13。

## 当前事实与下一步

新PR创建默认draft已完成并提交e7d88e7，保留--draft兼容，继续用pr ready/--undo；不改旧PR、迁移或request-id重试状态。主线独立读取前后SQLite、具体merge错误、实际Git效果和编译原件；原生session数量为零，准备阶段真实blocked不当成功运行。[draft记录](draft.md)保存命令、错误和覆盖边界。

review接缝已查明：ready不是请求验收，PR单负责人改派会停止实施者；需要独立的review请求与执行责任。cleaner的原生继承能力已核对Pi0.85.1实际源码，不能直接用会切换主runtime的fork/clone。advisor已独立建议按需维护操作、结束后一次提交、固定候选review和三个独立variant方向。产品边界、提交竞争与实验判据归[机制方案](mechanisms.md)；I13承接与语言依据归[证据对账](evidence.md)。原始观察归runs/iteration14；确定的Braid产品契约回归其PRD/TDD，Factory实验安排回归对应variant/配方。

cleaner/reviewer实施准备已经完成，详见 cleaner-preparation.md、reviewer-preparation.md。开源e2e实际发布及MCP接缝已核对，见 tester-e2e.md。按最新开工授权完成代码、真实操作反馈和I14-0实验；I13正式成果继续由原采集脚本收集，之后逐项移交I14-1。

I13目标与当前过程验收分别归 tasks/iteration13/packet.md、tasks/iteration13/i13-2/process-acceptance.md；正式身份与进展归 tasks/iteration13/experiments.md。当前本地GLM两项为a94a67b4b3d85b/8046cfb0695023，官网Flash/Sheet为f16834f58674，官网Flash/GitHub为e1aa595f6995。创建完成、过程采用、最终评分分别保留证据，未触发机制不自动标为失败。

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
