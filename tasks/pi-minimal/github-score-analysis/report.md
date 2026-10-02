# Pi Minimal：GitHub 2 分增量诊断

> 后续原生根因追溯已完成，见 [两条决策链与候选修订](causality.md)。下文保留首轮判断；最早错误点及 advisor 的作用以后续原文证据为准。I11 新增结果另见 [e68661975b53 独立报告](i11-e68661975b53.md)。

结论：本次是应用完成生成、部署和评测后的低分，不能归于旧 npm 安装失败、旧控制器中断或 Kimi 未接通。交付确有公开需求违约；生成侧的主要可控问题是把局部成功、绕过入口的检查和代码自审扩大成完整验收。修改提示词有明确着力点，但现有提示词已经要求保真验收和读取相关 Skill，单纯再加泛化要求没有充分依据。没有逐例官方错误，不能声称已解释全部 98 个失败，更不能承诺改动后的分数。

## 身份与原始材料

|项目|GitHub|Sheet（有限对照）|
|---|---|---|
|官方 task|hackathon--github / TASK-011|hackathon--sheet / TASK-012|
|run|c3fea0c3488c|6dc68bef2081|
|submission|f12fdf5540a1|同左|
|评分|2/100；2 通过、98 失败；0/47 功能完成|40/100；40 通过、60 失败；5/24 功能完成|
|终态|FAILED，三个执行阶段均 completed|同左|
|UTC 起止|2026-09-30 01:18:33.575107—03:08:27.782642|01:18:39.650300—02:57:23.919651|
|variant / 模型|pi-minimal；bigmodel/glm-5.3-flash；advisor arc/kimi-k2.7-code|同左|
|模式|self_funded|self_funded|

冻结 ZIP SHA256：`b4196fd387909a21a39a34e8c10f2a69c621057c7ed4f0647b60db3eeaf66e6a`，已对原 journal 的 agent.zip 计算核实，并用新鲜官网响应核对 run、task、submission。分析时主仓库 HEAD 为 `8e6ea7f`，大量已有未提交工作保持原样；它不是本次冻结 ZIP 的充分版本标识。

独立原始资料目录：[20260930T031746Z](../../../runs/analysis/pi-minimal-github-20260930/20260930T031746Z/)。下文称此目录为 E。GitHub [原始工作区 ZIP](../../../runs/analysis/pi-minimal-github-20260930/20260930T031746Z/c3fea0c3488c/workspace.zip) 来自既有授权会话的只读 `/runs/c3fea0c3488c/workspace/template-bundle` 下载。大小 88,716,489 字节，1465 项，SHA256 `02fb0e2abefea3fa7a42557792747008bc9c4a57005b7c6fec383a5410f6c88e`；ZIP CRC 全部通过，无路径/符号链接跳过。文件仅作为数据解压，未执行下载代码。完整清单及收据在 `E/c3fea0c3488c/{archive-index,download-receipt,application-files}.json`。

GitHub 解压根为 `E/c3fea0c3488c/extracted/template/`，下文文件位置相对该根。包内有前后端源码、公开需求、数据库及原生轨迹；没有 `.git`、`.arc`、node_modules、frontend/dist。因此不能宣称取得整个容器、官网逐例报告或交付 Git commit；以 ZIP 和逐文件哈希固定本次证据。归档内含运行认证材料，原始证据留在受限本地目录，不把这些内容复制到报告。

官网两题新鲜 `status.json`、`logs.json` 已保存到 E 的各 run 目录。两者 `tests=[]`、`node_states={}`；只有汇总计数，没有失败场景身份。GitHub 日志证实前后端 npm 安装、Vite build 成功，02:52:02 输出 `gitlite listening on http://0.0.0.0:3000`。Sheet 同样正常启动。`failure_reason` 的原文是 `Runner exited with test failures or runtime errors`，不能脱离已完成的阶段与日志，把它一概解释为设施失败。

Sheet 不重复下载：复用、复制了费用采集器已留存的终态 ZIP，源为 `runs/pi-minimal/20260930/arc-advisor/official/usage-snapshots/6dc68bef2081.zip`，SHA256 `76947a054d731e2de0e63fdd65159f2b68fa60c6263094ecbfd39ac3`，保存为 `E/6dc68bef2081/workspace-retained-terminal.zip`。只定向读身份、终态、Skill 调用及末尾验收声明。

## 已证问题与因果链

**1. 非累积权限被改写成角色等级。** 公开需求 `requirements/requirements.yaml:2653`、`:2663`、`:2702`、`:2741` 明确：标签、里程碑、关闭/重开等动作允许 Triage/Maintain/Admin，Write 和 Read 不得操作。交付 `backend/src/perms.js:9–12` 采用 Read=1、Triage=2、Write=3 并用数值比较；`routes/issues.js:205–211` 的统一守卫被标签 `:331`、里程碑 `:357`、状态 `:381` 调用，均以 Triage 为下限。故已登录且拥有 Write 的用户可以通过这些服务端检查；前端 `role-utils.ts:2–6`、`IssueDetail.tsx:41` 同样放行。这是静态调用链可确定的公开需求违约，本轮没有执行应用复现。

根因不是没提供规则：主会话分块读取覆盖完整需求，ROOT 也明确禁止累积阶梯；原生 `.factory26/pi-minimal/session.jsonl:73` 已把这些动作压成 `Triage+`，`:630` 又将 canTriage 当作正确性理由；最终 `:699` 声称“严格按需求逐条列出”。14 项应用单测验证了角色取最大值与 Read 私有访问等，却没有验证 Write 对这些操作的拒绝边界。**规则在设计和验收中同向失真**。

**2. 并列对象范围收窄：里程碑只有 Issue 侧。** 公开 REQ-5-3-3（YAML `:2696–2702`）覆盖 Issue 或 PR。`backend/src/db.js` 的 issues 表有 milestone_id，pulls 表（`:132–149`）没有；`backend/src/routes/pulls.js` 和 `frontend/src/pages/repo/PullDetail.tsx` 无里程碑处理，后者侧栏 `:76–80` 只有 reviewers、review summary、merge。不是控件名字稍有偏差，而是 PR 侧数据与入口均未承接。主会话 `:46` 的初始 schema 规划已仅在 issues 中列 milestone_id，后续自审没有纠正。最终声称全部“约 30 条”原子需求完成，而实际是 47 条，说明覆盖声明没有精确来源支撑；不能据这句计数断言具体漏了其余多少需求。

**3. 浏览器失败后绕过入口，却把结果页可用写成路径通过。** 原生主会话 `:502–503` 尝试在仓库页输入 Search 并按 Enter，因提取元素编号错误返回 `Unknown ref: e` 和退出码 1。`:504–505` 改成直接打开 `/alice-dev/acme-docs/search?q=search%20flow`，看到结果；`:508` 随即宣布 “Code search works”。这只证明结果页可读，没有验证 REQ-4-2-3 的“仓库顶端搜索框 → Enter → Code 结果”链。

对应交付代码也存在入口缺陷：`App.tsx:22–24` 把 Header 放在 Routes 外，`Header.tsx:13,21–25` 却用当前匹配路由的 useParams 判断仓库范围；按这一组件结构，Header 不能取得子 Route 的 owner/name，将走全局搜索分支。这是源码层面的确定性推断，未做新运行。直接 URL 的验证正好绕开了这条分支。另一个已有真实快照（主会话 `:206`）显示首页两个同名 link “Sign in”，`:207` 直接点击 @e6；两个入口分别来自 Header 和 Home。它可能让未限定范围的严格名称定位失败，是**高影响的共同入口候选**；需求未明确要求唯一 Sign in，官网也未给选择器，因此不能把它写成已证的 98 例共同根因。

**4. 初始状态生命周期建立在未核实的评分器假设上。** 主会话 `:36` 告诉 advisor “Grader likely restarts app per scenario”，方案是每次启动删库。advisor 输出明确表示只有实际逐场景重启时才成立，但主会话 `:63` 继续采纳。交付 `backend/src/server.js:11–24` 无条件删除各表并重播种，README `:24–29` 将它写成保证。这会丢弃跨服务重启的数据，不能等同于正常持久化；DB_PATH 只换位置，不消除删除。它还不能保证一个长驻进程里的每个场景都得到预期种子。**生命周期风险成立，其本次扣分贡献未知**；当前没有服务器逐场景重启或场景污染的证据，不把它列为已证首要失分原因。

上述原文节选保存在 `E/c3fea0c3488c/selected-trajectory.json`；`trajectory-index.txt` 仅供定位，含截短摘要，不能代替原始 session.jsonl。这里是结果导向的定向审查，不声称覆盖了 711 行轨迹的全部行为或全部 47 项业务。

## 复用历史分析，排除错误归因

复用了 [旧 GitHub 4 分结论](../../github-score-diagnosis/results.md)、[16 分实用复现](../../github-score-diagnosis/continuation03/functional-diagnosis.md)、[16 分 Harness 因果分析](../../github-score-diagnosis/continuation03/harness-causality.md)。这次公开需求 SHA256 为 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f`，与 16 分诊断记录相同。Write 越权、PR 里程碑遗漏在新产物中独立查证再次出现；它们不是 Braid 协作专属故障。历史的组织菜单 menuitem 错误这次不能沿用：新 Header 的 MenuLink 是普通 Link；历史注册邮箱原生校验阻断也不能沿用：这次邮箱 input 为 text。

冻结 instructions.md 已明确“验收判据来自原需求”“不要让现有实现反过来决定判据”“局部检查不代表整体完成”，并要求实现前读取相关 Skill、最终留下可重复完整路径检查。材料不是没有提供。主会话可见的 Skill 正文读取只有 agent-browser；fixing-accessibility、认证和组织指南未见主会话主动读取，也未见 Context7/Exa 调用。这不是绝对证明指南从未通过其他方式影响模型。Ponytail 则有原生扩展注入，不能按普通 read 调用缺失判未使用。

Kimi advisor **成功**：`subagent-artifacts/*_advisor_meta.json` 为 `arc/kimi-k2.7-code:high`、exitCode=0、success=true；其 transcript 第 3 行实际读取了 ponytail、better-auth-best-practices、organization-best-practices，后续还定向读公开需求。因此“再装一个认证 Skill”不是有力修复。advisor 给过精确控件断言和种子前提的提醒，但没有被转化为交付验收；部分建议还依赖假设。单次成功咨询不构成独立验收。

环境/工具方面，生成途中确有 Node ABI 115/137 不匹配（主会话 `:98`），后来改用目标 app-env；最终官方安装启动成功，不再作为终态原因。生成中 UNIQUE constraint 的编号问题也已修复并留下后续成功证据，不能沿用旧错误。主会话 14 条工具返回包含 `Unknown ref: e`，其中至少搜索一条引发了错误的验收替代；应区分工具调用构造错误与产品缺陷。旧 controller 的 offset 回退只阻断了本地采集，这次官网已完成；未修改或重启它。

Sheet 只作为有限反证：相同 frozen variant 和模型路由能生成并部署另一个应用，且主会话确实读了 hyperformula 和 fixing-accessibility（其 session `:30`）。末尾声明 31 单测和 64 项端到端检查通过，官网仍只有 40/100。这不能证明这些检查无用，也不能证明读 Skill 会提升到 40 分。两题有 47/24 功能项、不同交互和状态空间，不能用分数比推断模型强弱或提示词收益。既有 [Sheet 诊断](../../sheet-score-diagnosis/packet.md) 的“自建验收通过不等于公开需求覆盖”仍是适用方法提醒，不把旧 Sheet 种子缺陷移植成这次结论。

## 最多三个候选调整（均未实施）

|优先级与位置|具体机制与证据|风险与不花评测额度的验证|
|---|---|---|
|1：`variants/pi-minimal/instructions.md` 的验收段；需要专门操作示例时，仅在该 variant 的浏览器 Skill 打包副本补充，接线位于 `build.py:59`|把现有泛化要求改为可观察规则：探索可用 @ref；验收从需求规定的入口走到结果，核对 role/name/作用域及需求明确的唯一性。定位失败须修复调用再重走；直接 URL/API 只能验证子段，原路径保持未验证。依据是搜索 `:502–508` 和首页快照。|避免禁止所有直达 URL，避免给整个项目强加“所有同名控件唯一”。本次已有原始快照和轨迹即可人工回放验收判定：新规则必须把 Code search 标未完成，而不是 PASS；不运行代码、不调用模型。它检验规则能否识别历史误判，不证明模型下一次会遵循。|
|2：`variants/pi-minimal/instructions.md` 的设计/最终核对段|在第一次实现前只记录会改变边界的原子需求引用：显式允许/拒绝关系、并列对象、状态生命周期；完工核对这些项的 UI、服务端和持久化路径。不能把排除式规则压成等级。覆盖数来自真实原子 ID，未验证项保留。依据是 Write、PR 里程碑与 47→“约30”。|别把 GitHub 固定角色/对象硬编码进 Harness，也不增加庞大模板。本次以相同公开 YAML 和现有源文件做手工对照，规则应识别上述两处缺口及 seed 假设；不建立或运行 Factory 内容测试。|
|3（次级，可先不做）：`variants/pi-minimal/agents/advisor.md` 与主 instructions 的咨询交接|将既有咨询聚焦于能推翻方案的原文和反例：遇到未证的运行前提，明确标注未知及其设计后果；建议落实与否由主线保留证据。优先重定向现有咨询，不自动增加咨询次数。|advisor 已读相关 Skill 仍未消除问题，新增更多 Skill 或更长 prompt 未必有效。用已保存的 advisor 输出与主线 `:63` 人工检查条件是否被保留即可；是否调整模型/增加调用需要另行设计费用受控实验。|

最有价值的是前两项，不建议此时新增通用流程框架、盲目扩大测试数量、直接换模型或恢复 Braid。当前有证据支持改进验收和需求保真方法，没有证据可以量化提分。若要验证“修改后是否改变 Agent 行为或分数”，仍需要用户另行授权具体生成/评测和预计费用；本轮没有发起任何生成、评分、模型试调用，也未消耗比赛评测额度。

分析已完成。剩余限制是官网逐例失败不可得，以及本次按授权未运行下载应用；不存在下载/登录/审批阻塞。实际只新增本分析 task 材料及独立 runs 原始证据，未改 variant、Skill、应用、控制器或其他现有工作，未提交、推送或部署。
