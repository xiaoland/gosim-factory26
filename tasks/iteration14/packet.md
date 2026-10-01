# I14：协作职责与独立验收实验

2026-10-01开始，2026-10-02更新。I14处于机制调查与实验设计；PR创建默认draft已按直接授权完成源码、编译与隔离真实操作反馈。cleaner/reviewer的产品与技术方案待用户复核。I13-2四项接续保持原冻结输入与纯脚本监控，本轮不热改其运行包、不创建I14收费运行。正式成果由既有监控/终态流程取得，等待完成后逐项对照I13目标，将未达成或仍有优化空间的事项转入I14。

## 用户目标与授权

用户原话：“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”；“等待 I13 的正式运行成果，与 I13 的目标、改进项核对，未完成的、还有优化空间的，交给 I14”。draft范围包括创建契约、CLI、必要文档和真实无模型操作反馈，不改旧PR或旧冻结包。用户已授权自主git commit，提交限当前范围。

I14主要采用不同variant做实验。cleaner帮助Issue/PR负责人hide/resolve comment和维护description，以减少协作整理对工作思考的占用；上下文从对应work-item agent继承，它不是Braid可指派成员或原生sub-agent，归属与生命周期尚未决定。reviewer则是通过profile配置的Braid成员，PR负责人请求review后由Issue负责人验收，或由Issue负责人另行指派专门reviewer，在PR上生成独立reviewer session，承担代码审查与浏览器手动验收。当前授权为调查和设计；产品/技术方案先交用户复核，再按仓库阶段约定推进实施。用户随后提出cleaner的修改与通知应到一次turn结束才正式提交，主线与advisor建议采用该提交边界，具体失败/竞争语义归方案。

用户还要求在root issue提示使用现代TypeScript、避免JavaScript，但若I13应用本已自然使用TS则忽略。已检查保全工作树与发布origin：GLM/Sheet的backend/src仍有六个JavaScript业务源文件，因此I14保留TypeScript偏好；GitHub已有TS，官网Sheet当前导出的src缺失不作语言事实。只在未来I14根Issue约定落地，不改当前I13。

## 当前事实与下一步

新PR创建默认draft已完成并提交e7d88e7，保留--draft兼容，继续用pr ready/--undo；不改旧PR、迁移或request-id重试状态。主线独立读取前后SQLite、具体merge错误、实际Git效果和编译原件；原生session数量为零，准备阶段真实blocked不当成功运行。[draft记录](draft.md)保存命令、错误和覆盖边界。

review接缝已查明：ready不是请求验收，PR单负责人改派会停止实施者；需要独立的review请求与执行责任。cleaner的原生继承能力已核对Pi0.85.1实际源码，不能直接用会切换主runtime的fork/clone。advisor已独立建议按需维护操作、结束后一次提交、固定候选review和三个独立variant方向。产品边界、提交竞争与实验判据归[机制方案](mechanisms.md)；I13承接与语言依据归[证据对账](evidence.md)。原始观察归runs/iteration14；确定的Braid产品契约回归其PRD/TDD，Factory实验安排回归对应variant/配方。

下一步先复核cleaner的按需调用/提交边界及review请求/验收归属，再细化实施计划；不在本阶段创建I14运行包或收费实验。I13正式成果继续由原脚本收集，完成后逐项移交未达成与优化机会。

I13目标与当前过程验收分别归 tasks/iteration13/packet.md、tasks/iteration13/i13-2/process-acceptance.md；正式身份与进展归 tasks/iteration13/experiments.md。当前本地GLM两项为a94a67b4b3d85b/8046cfb0695023，官网Flash/Sheet为f16834f58674，官网Flash/GitHub为e1aa595f6995。创建完成、过程采用、最终评分分别保留证据，未触发机制不自动标为失败。

## 独立实验设施会话

用户明确要求“安排另一个独立的会话去改进实验基础设施”，范围为热恢复、本地/官网启动与持续监控，也允许改造必要的Braid/Factory接口。已创建并确认[Factory26 实验启动、热恢复与监控自动化](codex://threads/01a0f82f-23db-74d3-85b4-901b3b23fff0)正在开展调查。它拥有设施自动化线，当前会话拥有I14机制/variant线；创建prompt已给出I13真实journal/回执、费用模式与在途源码边界。不再把重复手拼启动/恢复流程混进I14机制方案，不建立第二Console或并行采集。具体方案与后续实施由该会话独立向用户复核。
