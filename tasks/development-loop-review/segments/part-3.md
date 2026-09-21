# 分段 3（2026-08-06 至 2026-08-09）：把已讨论的边界变成 Agent、peer 与 mail unit 的可实施设计

## 覆盖声明

覆盖 `part-3.index.txt` 所列全部用户 turn，并针对 Agent rumination、peer delegation、mail source、长讨论节奏及 pattern 回收做关键往返深读。证据采用 `raw L…`；本段截至技术设计与实现启动前后，不以历史命令或后来结果替代当时的协作事实。

## 工作模式

### 1. 已确认的 common pattern 必须能在下一次设计中阻止同类边界回退

**触发→材料→互动→继续。** 用户反复校正 Agent draft/submit 的验证边界：`draft_graph` 需要 runtime schema 验证，`Resolver.create_graph` 接收普通 input（`019fd632…`, L22301）；GraphForm 中不填 database-managed 字段、负 ID 表示本次待创建实体已是既有模式（`019fd657…`, L22526）。当 Agent 又混入错误验证责任，用户明确质疑 common pattern/task packet 没整理好（`019fd63f…`, L22344）。Agent 随后回到 runtime/Pydantic 验证、领域层只做本职责的拓扑。

**结论。** 稳定原则不是“多记一个 pattern”，而是每次新设计要先检索相同边界的既有决定，并说明此次如何套用或为何不适用。反例是把已定边界重新作为开放问题。

### 2. 从业务的持久配置与调度关系出发，HTTP/UI 只是可选承载

**触发→材料→互动→继续。** Agent 先从 HTTP API 讨论 rumination，用户指出 peer 平等、数据库协同，关键是 agent_definition 如何被 organization 配置引用（`019fd6b9…`, L22644）。在厘清触发与 acceptance corpus 后（`019fd6fe…`, L22798），用户才同意“为此提供 HTTP API”，并寻找 client-web 的 UI 承载点（`019fd70f…`, L22825）。peer runtime config 也被压缩为 deployment 提供的本地配置，而非复杂服务发现路径（`019fd747…`, L23007）。

**结论。** 稳定原则是先定位业务 owner、持久化关系和调度语义，再决定 REST/peer/UI 是否需要出现；接口不是讨论的默认主轴。项目特例是 peer delegation 让同一能力可在多个 peer 运行，因而 HTTP 成为第二个落地点。

### 3. 验收材料应逼近真实使用语境，但不能反向塑造产品和实现

**触发→材料→互动→继续。** 用户要求专业相关、可收藏的真实文章作为 acceptance corpus，并追问 entity reference 会不会污染实现（`019fd75a…`, L23071）。Agent 以 corpus 作为行为证据而非领域模型来源；用户又拒绝在已有 RFC/MDN 强证据后再做“真实反向代理 smoke test”（`019fd76d…`, L23213）。

**结论。** 稳定原则是测试/验收应检查用户关心的真实旅程，且只补足仍不确定的边界；既不能让 fixture 倒逼产品，也不为已被高质量外部证据覆盖的低价值疑问制造测试。

### 4. 对破坏性或不可逆猜测保持保守；best-effort 可接受并不等于制造通用重复处理机制

**触发→材料→互动→继续。** 邮件 identity 讨论中，用户拒绝“metadata 明显不符”的猜测：低概率错误仍可能严重且无恢复路径（`019fe4f2…`, L34478；`019fe4f8…`, L34588）。另在附件内容重复问题上，用户拒绝稳定选择/全局 duplicate util，因为这会把 best-effort 妥协暗示成受鼓励行为；要求 InfoBaseManager 只返回一个即可（`019fe714…`, L35756）。

**结论。** 稳定原则是区分安全的 best-effort 缺口和会把错误对象静默绑定的猜测；前者可局部容忍，后者必须拒绝或留可恢复路径。可变 SOP 是风险判断依赖错误是否可见、可逆和实际损害。

### 5. source、resolver、adapter 的边界由“谁拥有行为”决定，不由协议名称或函数名决定

**触发→材料→互动→继续。** 用户纠正“attachment 下载属于 Organization enrichment”：enrichment 可描述结果，但下载/持久化的操作由 mail resolver 或 source 拥有（`019fdc12…`, L29601）。在 IMAP/POP3 设计中，用户持续追问 adapter 的 `collect` 是否误拿了 source 语义（`019fe60c…`, L35065），并把拓扑收敛为 Mail Source 与 Mail Resolvers 共同依赖 IMAP/POP3 adapter（`019fe556…`, L34747）。配置则要求 sources.storage 指向可写 type，并由边界 registry/DB constraint 维护，而非运行时 helper 猜测（`019fe652…`, L35205；`019fe660…`, L35248）。

**结论。** 稳定原则是用操作 owner 判定模块方向：adapter 提供协议事实，resolver 解释/物化内容，source 编排 collect，organization 不因“增加”就接管外部读取。反例是从函数名 `collect` 或产品词“enrichment”反推 ownership。

### 6. “最小”是按真实扩展压力裁剪，不是拒绝所有抽象或把协议内部名版本化

**触发→材料→互动→继续。** 用户一方面拒绝让 MailProtocol 变成 InKCre internal `extensions.mail.protocol.imap.v1`，要求 `Literal["imap"]`（`019fe5c6…`, L34895；`019fe5cd…`, L34948）；另一方面保留小的 `create_mail_adapter`，因为未来 POP3 只需在该函数接入、成本低收益明确（`019fe5d1…`, L34975）。类似地，用户要求 adapter 的 protocol/parameters 分离，复用先前 inbound interface pattern（L34895）。

**结论。** 稳定原则是抽象需有具体第二路径、边界隔离或资源管理收益；标准协议名称不应伪装为内部 capability/version。项目特例是已明确 IMAP→POP3 的短期扩展方向，使小 factory 合理。

### 7. 讨论批次应随信息密度自适应；过长时先回顾，过大或信息不足时立即缩小

**触发→材料→互动→继续。** 用户要求回顾 mail unit 已讨论的位置与剩余项（`019fe66d…`, L35322），一度建议稍扩大 adaptive batch、略过自然推出项以加速（`019fe67e…`, L35400），随即强调仅是本 unit 特例、不可推广为任务 SOP（`019fe6cf…`, L35423）。当下一批信息不足又太大，用户要求缩小（`019fe6e1…`, L35582）。

**结论。** 稳定原则是让用户随时能审查前提和选择；可变 SOP 是批次大小，依据当前概念耦合、剩余未知和用户所需解释量动态调整，绝非“一次一个问题”的僵硬替代。

## 正反案例与可迁移指导

正例：用户用“HTTP 不是主轴”“猜错不可恢复”“adapter 不拥有 collect”这类归属/后果反例，迫使 Agent 将名词提案还原为行动与责任。反例：把已确认的 GraphForm 验证责任再次混入 resolver，或将 unit 临时的批次策略升级为全局规则。

1. harness 可在每次方案中要求标注：本次复用的既有决定、owner、以及违反它会出现的具体错误；不能只检索到 pattern 名称。
2. 支持把验收证据分为“仍需真实执行”和“已有强证据无需重复”，并要求说明哪种不确定性被消除。
3. 支持用户调节讨论批次并把该调节的作用域标成 unit-local 或 task-wide，防止节奏偏好误变全局流程。
