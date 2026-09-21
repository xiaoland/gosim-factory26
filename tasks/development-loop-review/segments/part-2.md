# 分段 2（2026-08-03 至 2026-08-05）：以实际场景压测深模块，收敛到 Agent/organization 设计

## 覆盖声明

覆盖 `part-2.index.txt` 所列全部用户 turn，并深读 RSS unit 收尾、semantic retrieval/peer/organization/Agent 的关键往返。本段主要是设计与工作模式，不覆盖后续实现结果；证据定位使用 `raw L…`。

## 工作模式

### 1. unit 关闭前先回到验收旅程，再决定是否抽取基础能力

**触发→材料→互动→继续。** 用户发现 RSS 验收尚未确认（`019fc548…`, L15502）；Agent 给出实际验收链，用户认可主体方案但只在确有可抽离价值时讨论测试基建（`019fc55d…`, L15551），再允许关闭/提交（`019fc59c…`, L15679）。用户还明确 unit 是实现单元而非发布单元，偏好真实 Atom/RSS 黑盒验收而非 helper fixture tests（`019fbe15…`, L9242，前段交界材料）。

**结论。** 稳定原则是先以用户可见旅程验证，再问是否值得抽取；发布是否为完成门槛是项目/用户可变条件。

### 2. 从实际使用场景倒推深模块，而非先由存储结构或索引术语驱动

**触发→材料→互动→继续。** 用户接受 semantic-retrieval 重整，但要求从实际应用倒推深模块，并追问检索结果为何不应是 blocks/relations（`019fc675…`, L15878）。用户进而把 chunk 问题关联到 organization/breakdown，却仍把 organization 限在 blocks/relations、检索留在 use/interface（`019fc67f…`, L15933；`019fc69a…`, L15994）。Agent 随后提出 embedding/profile/record 分层，用户只要求把 profile/record 的持久化和语义审清（`019fc759…`, L16033）。

**结论。** 稳定原则是模块的“深”由调用者需要的语义和责任边界衡量；技术对象可作为实现材料，不能先决定产品输入输出。

### 3. 表、配置和 registry 的引入需由生命周期/复用/作用域证明，而非名称相似

**触发→材料→互动→继续。** 用户以“没有独立 identity、生命周期或足够复用价值”概括是否建表的判据（`019fc7f2…`, L16373），拒绝为低损害并发风险加 version 字段。对于 semantic retrieval config，用户否决单独表：一个 deployment 仅一条记录，改用简单 deployment-scope config；但区分它与通用配置模块（`019fca60…`, L17417；`019fca7d…`, L17564）。AI dialect 也由 registry 命名讨论收敛为 AIManager 的路由职责（`019fc87e…`, L16590）。

**结论。** 稳定原则是先问独立 identity、生命周期、复用和作用域；名称/未来可能性不足以新增表或 manager。可变 SOP 是何时提升公共模块，取决于第二个真实 consumer 是否出现。

### 4. 人类通过反例校正拓扑，Agent 需带着可运行的调用链讨论而不是目录树

**触发→材料→互动→继续。** 用户拒绝把 semantic retrieval 业务塞入数据库，并以“不对等 peer”与 collect job 为反例，逼出服务发现与 delegation 的产品问题（`019fcb1c…`, L18100）。讨论由 “PeerConnection 是否耦合 capability” 逐步改为 `SemanticRetrieval → PeerManager.delegate(capabilityID) → failover → HTTPOutbound`（`019fcb5e…`, L18451；`019fcbbc…`, L18599），再明确 peer 只理解 delegation、不理解业务（`019fcd97…`, L18773）。

**结论。** 稳定原则是用 caller→领域入口→基础设施→provider 的端到端链展示模块职责，并让用户以反例检验耦合。目录命名和抽象名可在链路正确后再定。

### 5. 先定义产品行为的可接受 no-op/失败语义，再决定 LLM/Agent 是否需要更强的主动性

**触发→材料→互动→继续。** 用户把 breakdown 从 command 改为 organization solution/approach，拒绝默认删除原 block，并反驳“无 useful anchor 即 no-op”过严（`019fd012…`, L19454；`019fd022…`, L19491）。对 resolver 不能理解内容，用户要求深模块对外给浅完成语义，避免过早引入内部重试、回滚或降级（`019fd063…`, L19687；`019fd069…`, L19728）。当 Agent 将主动图探索放到未来，用户依据现有 tool-call/JSON 能力要求现在就考虑 Agent 模式（`019fd07a…`, L19764；`019fd085…`, L19796）。

**结论。** 稳定原则是 LLM 只在有意义的内容理解/图生成处保留判断空间；领域层负责可提交的 GraphForm、ID、storage 等持久化边界。后来撤回的做法是把 no-op 定义为“没有单一 useful anchor”，以及把 Agent 过早排除在 MVP 外。

### 6. 技术设计在长讨论后必须停下来整理，再以最小持久模型和并发语义继续

**触发→材料→互动→继续。** 用户在 decisions.md 数千行时主动暂停并要求拆分 monolith（`019fd143…`, L20049），再回到 Agent definition/thread。用户将 tool schema 校验归 runtime/Pydantic，避免 info-base 重复验证（`019fd17e…`, L20271；`019fd185…`, L20307）；又要求 tool calls 可并行、消息闭合语义准确（`019fd1f2…`, L20581；`019fd235…`, L20799）。最后用户要求停止继续展开、回顾并整理 unit（`019fd2c1…`, L21179）。

**结论。** 可变 SOP 是当决策量或概念耦合超过当前可审查性时，暂停而非强行“完成设计”；整理后的最小模型需保留尚未验证的并发/持久化选择，不能假装都已落地。

## 正反案例与可迁移指导

正例：用户用不对等 peer、单 deployment config、无 anchor 但 subgraph 有价值等反例，使 Agent 从抽象名词回到可观察职责。反例：先以 HNSW、候选角色、独立 config/table 等技术形状驱动，会引入无生命周期对象或错误边界。

1. harness 可要求架构提案先给一个 caller→provider 调用链和一个会推翻该提案的反例。
2. 对长设计会话，提供可见的“整理后继续”断点，保留确定结论、开放问题和未验证假设。
3. Agent/LLM 设计应区分：开放的内容判断与工具选择；不可开放的 schema、持久字段、提交边界和协议闭合。
