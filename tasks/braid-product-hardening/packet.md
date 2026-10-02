# Braid 产品能力与新模型团队
状态：2026-09-28 用户已复核并授权产品、工作方法/工具及实验设施改进，实现与定向验证完成，上下文因果排查完成；新模型端到端实验尚未运行。WSL 在修正整合后再冻结。

## 目标与授权
修复已证实的投递/恢复断点，清除不再服务 Local 协作的旧机制；独立复审产品要求是否把 LLM 的语义判断转移给 Harness。
用户授权应用三个发现和三类清理，扩大产品审查；同时用最新 variant 在 WSL 跑 Hackathon 两题并监控，使用官方 API。
用户进一步明确：模型替换属于 agent-profile，并作为独立 variant。

## 工作单元
- 旧事件重放及显式离线恢复已实现；dd3bda66bcb3 证明冷恢复平稳续进，按用户缩小后的验收范围已完成并取消，冻结证据保留。
- Codex 收据已实现，真实 app-server 普通/steer 消息顺序已验证；[记录](../experiment-infrastructure/cells/codex-receipt.md)。完整 Codex 工作项 reset 尚未端到端验收。
- 三类精简已实现；[记录](../experiment-infrastructure/cells/braid-cleanup.md)。cargo check、Linux release 编译与差异空白检查通过；旧 fixture 接口编译错误已机械修复，相关定向检查已运行；剩余旧对象测试失败与本轮验收界限见下文。
- 产品审查已完成，用户已批准修正。普通追加、讨论收件、关闭自然收尾及关闭关联正文的实现见 cells；根单独关闭作为新结束模式仍未采用。
- 主 Agent 创建 pi-braid-flash-team，保留 GLM，提供 Qwen/MiniMax 两个替代 DeepSeek 的 Braid profile。原生 sub-agent 模型保持原样，先核实官方模型可用性与原生配置。
- 耗时分析及修复方案归 ../experiment-infrastructure/time-cost-proposals.md；已获复核，方法/技能与工具使用修正在 cells/working-methods.md。

## 实验边界
WSL 新生成 GitHub、Sheet 各一次，使用官方 API 的自带 key，不使用参赛额度，不新开官网实验。
冻结最新修复后的 Braid、variant、技能与模型配置。两个任务并行，资源与现有运行先核查。
生成阶段不能访问评测测试。冻结产物之后使用现有本地代理评测；分数不能冒称官网成绩。
监控前十分钟每三分钟、之后每八分钟；程序等待，终态由低成本 Agent 汇报。
不改已运行的冻结包、不提交源码、不写 Factory/基础设施/Corpus 测试，不直接修改生成应用。

## 实验时序修正
用户最新指示：“先做完手上的改进，然后等待审查结果，一并修复之后再重新跑wsl实验”。两题尚未启动；仅已完成官方 API/Pi 模型接线核实、Linux release 编译。已停止尚在复制 runtime 的打包进程，保留本轮源码及运行材料。后续先消费产品审查，明确行为取舍并完成相应修正，再重新打包；不把现有暂存二进制当最终冻结。官网 dd3bda66bcb3 的原冻结恢复实验不受此调整影响。


## 本轮合并范围
用户追加要求：上次官网运行的根因分析与修复方案一并纳入；核实设施验收和使用体验；设计自包含 OTLP Collector/backend，官网与 WSL 的诊断不依赖 ARC traceability，并强化 token/耗时剖析。
统一方案分为 [迭代范围](iteration.md)；独立可观测性盘点归 ../experiment-infrastructure/observability-inventory.md。
先整理产品/方法/工具/设施各自承担的修正，避免把同一根因分别补到多个层。产品行为与设施技术方案已经复核并获本次实施授权；WSL 新实验待改动整合与冻结后推进。

## 本次开工与验收调整
用户原话：“同意，继续改进Braid、工作方法与工具（按你给我的这些，我复核通过）”；“同时/子代理去继续按照你说的这些，改进实验基础设施”。
实施分工：context-notifications 负责失效与收件；主 Agent 负责关闭自然收尾与整合；working-methods 负责已有 SVC/角色/工具指引；observability 负责 Collector、原生采集、存储与查询。各 cell 记录具体接口与验收。
根关闭作为独立结束请求此前仅是候选，本轮保持既有全部对象终态范围，修复正在执行的末轮被截断，不新增产品结束模式。
用户将冷恢复验收缩为“未完成状态的冷恢复能平稳运行”。dd3bda66bcb3 已通过真实续进证据满足此范围，随后按授权取消，远端确认 CANCELLED；本地 controller/monitor 同步停止。证据 runs/e20260928-offline-resume/user-stop.json。
不以取消视为生成失败或评分结果；不为这项验收继续消耗模型。

## 追加：上下文与验收偏移的因果排查
用户提出竞争解释：改判据、丢初始条件可能由 Braid 上下文重置、通知和消息管理混乱诱发，不一定是工作方法漏洞。已委派 GitHub、Sheet 各一个独立取证 Agent，结论由主 Agent 综合。
已观察到的是错误决策与需求传递损失；“方法不足”“关键信息因重建而丢失”“通知噪声干扰决策”目前仍须区分。现有已批准实施不撤回，也不据此宣称它们解决了得分根因。
判别链：原需求 → 当时实际初始 Context/后续消息 → 工具实际读取 → reset 与通知消费 → 关键决策 → 检查/交付。要求以具体成员及物理会话时间窗核对；材料存在不等于读过，时间邻近不等于因果。
结果分别归 cells/github-context-causality.md 与 cells/sheet-context-causality.md；缺失关键输入时指出具体证据，不补造结论，不启动额外收费实验。

## 本轮实施收口
Braid：Context/通知 4 项定向检查、关闭/交付边界 4 项、自编辑恢复 2 项通过，Linux release 编译成功；不把这些替代为完整 benchmark 结果。旧对象测试仍有 6 项与本轮无关的失败，证据保留，不宣称全套测试通过。
工作方法：已在 SVC 权威内容和 browser-checks/活动 variant 短入口落地。方法是否为主要失分原因仍由新增因果调查区分。
实验设施：包内 Collector/SQLite、原生调用计时与模型/成员剖面已实现；真实历史 OTLP 接收→停止→单 DB 读取通过，历史原生 token 剖面和 viewer 已生成。证据 runs/e20260928-product-hardening/observability。新 Pi 回调与新包官网/WSL完整链路仍待真实实验，不补造历史耗时。
未提交；未启动新的模型实验。

## 上下文因果排查结论
[GitHub](cells/github-context-causality.md) 与 [Sheet](cells/sheet-context-causality.md) 已完成独立取证，核对具体成员、物理会话、原生消息祖先链和通知消费。
GitHub 的正确 link 断言被改成 menuitem，发生在该成员首次 Braid reset 前；当时催办仅排队未消费。模型仍提及原需求，却用当前 DOM 与对官方测试的猜测替代它。
Sheet 初次 A1-only 契约来自缺少 GIVEN 的摘要，早于根首次 reset；REQ-5 随后读到完整 GIVEN，仍写出自造数据的检查，也早于其首次 reset。根后续重读完整需求，没有修正共享前提。
这些实例不支持“Braid 重建直接抹掉依据”的解释；也不能据此认定 SVC 文本有漏洞。长上下文和无效排障是否放大注意力问题仍未知。归档缺少每次采样的完整 provider payload，不能把祖先链中的材料等同模型有效关注。
已批准的 Braid 修正按独立产品证据成立；方法修正作为改善实际采用的假设，不宣称已经证明得分收益。不因这次调查再堆叠提示词或启动额外实验。下一次既定实验同时观察协作噪声与判据依据，不单凭得分推断因果。

## 继续过程取证
用户要求继续深入过程，先不扩大提示词。现有 GitHub/Sheet 取证 Agent 分别追加：同一成员正确修复 UI 与错误修改判据的输入对照；根最终全覆盖声明实际依赖的检查、需求和成员回执。仅更新各自 cell，主 Agent 综合判断，不因分析自动开新实验。SVC 仅在既有判据修订段明确禁止让实现反过来决定验收判据。

## 状态补核：重复调度与产品复审
用户追问的“2.1 万条”准确为旧 GitHub 日志 21,206 条 assignments.member_login 唯一键错误；另有 68 条无行动/保持关闭评论，二者不可合并为模型调用数。来源 tasks/acceptance-integrity/results/run-time-profile-20260927.md。
已修的空批次重放、通知范围、普通追加引起重建、强制 finalization 分别对应不同机制。冷恢复快照中新 turn 空批次为零，只验证该机制，不足以证明 member_login 唯一键忙重试已修。该唯一键问题尚缺专项的事件→身份→物化链和修复回执，明确保留未闭环，不能用总的“Braid 实现完成”覆盖它。
产品复审五项：追加/Wake、thread 收件、关闭自然收尾、关闭关联 Issue 正文已实现；有限执行的根关闭模式未采用，仍保持全部对象终态，只修末轮不可被截断。新运行的噪声降幅未验证。

2026-09-28 用户重新授权启动 WSL Flash Team，两条 run 已分配并 running；冻结身份和控制器见 experiments.md，原“尚未启动”是历史暂缓状态。监控 cell 持续记录模型启动、故障与终态。

## 2026-09-28 新运行验收及二次复审
用户要求同批检查运行、设施、噪声与方法效果；追加browser工具细粒度分析、共享契约Braid因果及产品→技术二审。结果归 cells/live-run-evidence.md、../experiment-infrastructure/cells/browser-feedback-audit.md、../experiment-infrastructure/cells/shared-contract-braid-causality.md、../braid-product-reaudit/packet.md。旧官网协作HTML归 ../official-collaboration-review/packet.md。新增发现尚未获本轮源码修正开工确认，不修改在跑的冻结输入。
