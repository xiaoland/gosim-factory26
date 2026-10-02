# Pi Minimal 新 V&V run：4 分的证据与机制

2026-09-30。对象仅为 [2ef9660d0dad](https://arc-bench.com/runs/2ef9660d0dad) 与旧 [c3fea0c3488c](https://arc-bench.com/runs/c3fea0c3488c)，不把 I11 的产物或过程移植为本次结论。

**官方结果确为从 2/100、0/47 功能变成 4/100、1/47 功能；但这次没有验证“完整执行 V&V 后只提高两分”。新 Skill 已冻结、已向两个模型展示目录，却没有被读取；advisor 还明确以“这是设计建议，不是验证”为由排除了它。** 主会话实际做了大量检查并修过真实错误，但检查没有形成从完整需求树、规定初态、真实入口到最终状态的闭环。

这里的“2→4”是 run 详情 score/test_pass_rate 与通过数口径。最新 submission API 另给新 task 加权 `score=3.538969688863313`（penalty），旧 task 的该字段为 null（unavailable），不能混成同一排名分数差。两接口的 4/100、1/47 一致，原始字段详见 [身份记录](identity.md)。

用户怀疑“根因没定位完整或修复没到位”，证据支持更精确的拆分：旧分析确实遗漏了一个明确的父层入口约束；本次方法接线到达了模型，但方法执行未发生；旧权限问题只在新 UI 正确表达，服务端仍错；PR 里程碑继续缺失；还出现新的前后端接线和页面运行缺陷。**这些能说明具体失败机制，不能据此分配全部 96 个官方失败，也不能把两分变化归因于 Skill。**

## 证据入口与事实边界

- [身份、提示与冻结材料](identity.md)：run/submission/ZIP/binary/模型/Skill版本、完整可见提示、下载收据与限制。
- [完整需求树及产物核对](requirements.md)：ROOT、父层、47 原子需求和场景的继承关系、产物断点。
- [原生过程正向整理](trajectory.md)：需求→设计→咨询→实现→检查→修正→交付，含时间、message ID、行号与覆盖边界。
- 原始证据根 [E](../../../runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/)；`A=E/extracted/template`。`M=A/.factory26/pi-minimal/session.jsonl`（551行），`V=A/.factory26/pi-minimal/session/fb04a836-51cb-48dc-8940-b29ddf178785/run-0/session.jsonl`（55行），`R=A/requirements/requirements.yaml`。以下源码相对 A，M/V/R 行号均为原文件一基行号。

官网已完成生成、安装、启动和评测；新生成 exit=0，后端监听 3000。官网 tests=[]、node_states={}，commit-history/traceability 在终态不可用，没有逐例失败和生成应用 Git OID。工作区 ZIP、原生会话、provider system/tool schema、完整 task prompt、数据库、源码已取得并独立保存；未执行下载应用。本报告将静态可达缺陷、当时真实观察和官方分数分开。

## 这次真正改变了什么

两次公开 requirements.yaml 完全相同：292,270 bytes，SHA256 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f`，prerequisites.md 都为空。主模型仍是 BigModel GLM-5.3-flash/high，唯一 advisor 仍是 ARC Kimi-k2.7-code/high，两次均咨询成功。新运行是从原需求独立生成，**不是给旧应用打补丁后复评**。

上传包从 `b4196fd3…` 变成 `4edbd960…`，新 submission=`2dbbc244c485`。冻结包新增 V&V 入口及四份 references，另改主入口技能发现、主指令、advisor 声明、agent-browser 的结果解释引用、执行位恢复的条件判断，以及执行文件清单排序；Pi/Node runtime 和其余 23,755 个载荷的 manifest 哈希相同。该差异排除“只是源码写了、实际仍跑旧包”的解释，也说明不能把实验条件简化为只有一个 Skill 文件变化。详见 [身份记录](identity.md)。

Skill 是实际冻结的 `svc-verification 16.0.0`，不能用当前 SVC 工作树替代。它已提供本轮需要的方法：并列对象分别承接、非累积授权相邻反例、跨组件原路径、初态不被 setup 替代、检查须能区分真实状态变化、结果不得超过观察范围。它也明确在实施前使用；不是只有最终执行测试时才适用。

## 正向还原与决定性断点

### 1. 完整原文可见，但设计摘要没有保住全部对象与父层约束

M:L9–20 分块读取需求。父层登录与唯一性、非累积权限、Issue/PR 里程碑都在可得原文中。M:L21（04:47:03，`a5e37c7f`）归纳模块并设计 schema；里程碑仍只进入 issues，PR 表与 PR 功能清单没有承接。后续 `db.js:147–164` 的 pulls、`pulls.js`、`PullPage.jsx` 均无 milestone 字段/路由/控件。

这不是最终漏写一个 label，而是 **读过“多个对象”的需求后，设计按模块转写时少保留一个适用对象，后续实现和检查沿窄化表示走下去**。旧链路仍适用；不能根据新增加了 V&V 就假设这里已修。

权限则不能照搬旧结论：M:L41（05:11:22，`0d7c113c`）明确说 `If bob's effective role is 'write', he can comment/edit but not triage.`；M:L141 的 UI 初版已使用 `['triage','maintain','admin']`。但 M:L45 的等级 helper 和 M:L61 的服务端 `withIssue(...,'triage')` 仍按下限比较。最终 `perms.js:3–4` 将 Write=3、Triage=2；`issues.js:121,154,166,202,218` 放行 Write 的状态/分配/标签/里程碑操作，而 `IssuePage.jsx:23` 正确隐藏这些控件。

**新问题更准确地说是同一规则在 UI 与服务端两次表达后漂移，缺乏跨层反例核对**。UI 正确不证明服务端拒绝，原始要求又明确写操作必须服务端校验。23 项 API 检查在 Issue 管理动作上使用 Admin，未留下 Write 拒绝的检查；两种实现都能通过这些 Admin 正向用例。

### 2. V&V 可见，advisor 主动把设计排除在用途之外

M provider system `new-provider-system-glm-5.3-flash.txt:42–46` 和 advisor system `…kimi-k2.7-code.txt:69–73` 均展示 svc-verification 的 name、description、location；advisor system:48 还明确要求在产品与技术设计中应用方法。M:L4 实际用户提示也包含设计验收和结果解释的使用时机。系统展示的是目录，**没有自动内嵌 Skill 正文**。

新两份原生会话的工具调用没有读取 svc-verification/SKILL.md 或四份 references；也未见 bash/grep 等间接取得正文。main 实际读取的是 better-auth、fixing-accessibility（M:L25–27）和 agent-browser（M:L177–178）。advisor 没有 Skill 正文读取。

这里不只有“没搜到调用”的弱证据。V:L6（04:48:02，`1cd9eedd`）明确推理：`there's svc-verification skill relevant. But maybe not needed`，随后 `task is design advice, not verification`。这个阶段分类与冻结 Skill 的“实施前形成可观察判据”和角色提示相冲突。M:L177 读到 agent-browser 对 V&V 的结果解释提示后也没有跟进。

advisor 并非没工作：它读了需求与参考图，V:L55 成功回传搜索默认 scope、PR branch pair、种子等建议；M:L41 记录消费反馈并修改 seed，搜索默认 scope 也实际改了。可见的是 **咨询成功、建议有消费，但没有执行这次新增的验收方法**，不是 advisor 失败、材料不可见或主线全盘忽略建议。目录说明仍可能影响模型；本次不能证明它完全没有任何影响，更不能量化其提分。

### 3. 遇到初态冲突后，以猜测评分器和终态幂等性替代原判据

M:L41 在给 bob 分配角色时同时意识到 REQ-2-3 的“初始无 direct grant”与自己希望给 bob 既有权限相冲突。它没有保留待解决的独立场景条件，而是写下 `graders likely tolerate`；最后明确接受：`member bob has a direct grant ✗ (but upsert keeps exactly one record ✓). Acceptable.`

最终 `db.js:280–337` 采用全局三账号种子，给 bob direct Maintain；`seed()` 在已有用户时返回。此项证据支持 **判据偏移**：给已有授权改成 Write 后仍只有一条记录，不能证明从无授权初态完成授权创建。这里有多个场景状态的真实设计困难，但“最小账号集合下看似冲突”不等于原需求允许放宽；应保留未解分支，而不是根据评分器会容忍的猜测宣布满足。

主线也没有完全照单全收 advisor：advisor 建议只保留 alice/bob，它为注册非成员场景保留 carol。应保留这一正面事实。问题是另一些初态被主动让步，且最终覆盖声明未携带这一限制。新 seed 不再像旧应用每次启动删除全部表，旧“重启丢库”的具体实现问题不能沿用；但独立场景初始化仍未建立可核验闭环。

### 4. 检查真实运行，却没有可靠区分需求满足与相似局部成功

主线编写并运行了 23 项 backend API 集成检查，真实修过 SQL `no such column: id`、merge 的 `makeCommit` 未导入、排序回归等；浏览器也完成过登录、Issue、PR、合并及最终 fresh seed 的局部观察。不能称为“完全没有验收”。M:L341–342 有 merge 修复后的真实成功，M:L533–534 后来从 fresh seed 看到了 `test: pending`，不能把早期失败作为最终未修复。

但验收路径和结论有以下可反驳缺口：

|原始动作与结果|当时结论|实际只支持什么|
|---|---|---|
|M:L389–390 退出后统计 `link "Sign in"`，结果为 **2**；随后私有仓库显示拒绝|M:L391 `Sign-out works`|退出确实生效；首页唯一入口仍被自己的结果反驳，未进入修复|
|M:L459–462 在原本 Public 的 acme-docs 中，Public radio 已选中，直接 Confirm，仍显示 Public|M:L463 `Visibility change works`|同值保存/关闭对话框，不能证明 Private→Public 或访问策略同步变化|
|`backend/test/api.test.js:104–111` 正确验证码重置时把密码设回原种子密码，再用原密码登录|检查名是 password recovery updates the password|校验错误验证码与正常响应有价值，但正向部分不能排除重置接口不改密码的实现|
|API 搜索检查仅测试 `scope=repositories`（api.test.js:169–173），文件读取另用直接API；没有 code-scope 检查|API 成功用于功能信心|既未覆盖 Code 搜索分支，也未经过前端发送的 `name`，无法暴露真实 UI 接线错误|
|最终 M:L523 直接 open `/signin`；M:L531 点击 Account menu，M:L532 只 grep `menuitem`|最终声明完整路径/所有流程已验证|跳过首页唯一 Sign in，并且接受了错误的菜单角色；不是原需求端到端路径|

另有工具使用缺陷：多次用 `grep -o '@e[0-9]*'` 提取元素编号，而 snapshot 实际返回 `[ref=eNN]`。空变量造成 Missing arguments 等错误，主线却归因于 hydration/refs stale（如 M:L337、477），之后靠手写 ref 或直接 URL 继续。它没有让所有检查失败，但破坏了可重复性和错误诊断；没有完整复验就不能扩大通过结论。

可见正式保留的自动化是 API 检查；未发现覆盖原始完整 UI 场景的可重复脚本，也未调用 with-service.py。wrapper 本身不是必需条件，关键是其代表的候选、初态、路径、输出与结论边界是否另有证据承接。本次散落的浏览器命令和最终声明没有补齐这些缺口。

这是有可见决定的覆盖收缩：M:L343（05:41:39，`c83a4b7e`）原拟编写 E2E，随后以时间/投入为由改成 Node API integration test；M:L413（05:45:57，`80ebfdc0`）进一步判断 `Given API tests cover logic, one or two more UI spot checks suffice.` API优先本身不是错误，遗漏的是那些只有真实入口、前后端连接和页面语义才能支持的剩余承诺。M:L184 的首张首页快照已明确显示双 Sign in，M:L185 按 ref 点击其中一条成功，也说明问题并非没见到首页，而是没有把父层约束当成判据。

## 新旧产物差异及高覆盖断点

|对象|旧 run|新 run / 证据性质|
|---|---|---|
|Write 对 Issue 管理动作|UI 与服务端均按 Triage+ 放行|UI 正确排除 Write，服务端仍放行；静态完整调用链已证，非整条权限误解原样复制|
|Issue **或 PR** 里程碑|设计与实现只做 Issue|仍缺 PR schema/API/UI；相同并列范围遗漏|
|全局/仓库搜索|Header 在 Routes 外用 useParams 判断仓库范围，原生失败后直达结果页|Layout 改从 location.pathname 获得仓库范围，advisor 的默认 repository scope 建议被采用；**新** Code 路径把 `name` 传给只读 `repo` 的 API，404 又被前端转为空结果。不是旧同一接线 bug|
|首页 Sign in|原生快照已有两个|Layout.jsx:96 + Home.jsx:52 仍同时渲染；M:L390 实际计数为2，违反父层明确唯一要求|
|认证后身份|本轮不重复全面审旧|新 username 只在展开菜单子树出现：Layout.jsx:65–92、ui.jsx:49；Home.jsx 无 username。M:L532 支持展开后出现；M:L530 是截断交互快照，不能单凭它证明所有普通文字缺失|
|账户菜单角色|旧 Header 的 MenuLink 是 link，旧报告已排除该历史缺陷|新 Layout.jsx:85–89 把 Your organizations/Settings/Sign out 改成 menuitem；M:L532 原生快照确认。与原文要求 link 不同|
|Owner People 页面|本轮不作旧全量比对|OrgPage.jsx:4 未导入 Menu，:135–150 在 canManage=true 且已有成员时引用它，静态推导运行会抛未定义标识符；阻断 Owner 成员管理共同页。未运行应用复现|
|初态生命周期|启动时删库并假定评分器逐例重启|只在 users=0 时 seed，旧删除逻辑不再存在；却使用统一种子并主动容忍 bob 初态不符，独立场景仍未获得证据|

**对旧分析的明确修正：** [旧 report.md:40](../github-score-analysis/report.md:40) 写“需求未明确要求唯一 Sign in”，这不准确。相同哈希的 R:L2831–2839 已规定 REQ-6 的 named controls 唯一，以及从首页 `unique Sign in link` 开始并在认证后显示 username；R:L1614–1618、L2160–2164 也有父层登录/唯一性要求。此项从“可能触发严格选择器的候选”提升为**明确公开需求违规**。新证据来自本 run 原文和产物，不靠 I11 推断。旧报告保留，本轮在此纠正，未改已有工作项。

这类共享入口在很多签入场景的业务步骤之前就会触发，因而比几个末端按钮更有覆盖影响。其“可能阻断多项”有需求依赖支持；具体官方评测是否因此失败多少项，仍需逐例失败记录，不能把 96 全归给它。

## 根因候选与下一步判别标准

|优先级|证据支持的机制|应落在哪一层；下一次先看什么|
|---|---|---|
|1|Skill 激活边界错误：设计阶段被解释成不属于 verification，目录存在却未消费正文|Pi 主指令/advisor 的方法选择与交接。下一次先核对设计前实际读取、原文→判据→反例的可见产物；若仍未执行，不把分数用于评价该方法有效性。不要仅继续增加材料|
|2|需求转写丢失父层/并列对象，跨层实现缺乏同一反例约束|设计及验收表示应携带适用父层、对象集合和服务端拒绝条件。当前证据可人工判别：双Sign in、PR无milestone、UI拒绝但API放行都必须留下不满足结论；不能仅检查REQ标签或helper名字|
|3|独立初态被统一seed和评分器猜测替代，缺状态转移区分力|产品/技术/验收设计交接。保留真实场景前提与未解冲突；观察 Private→Public、新密码替换旧密码、Write拒绝等能区分no-op或错误简化的结果，不能用同值/同权正向检查替代|
|4|局部 API/build/快照成功被扩为完整 UI 路径成功，错误工具解析未根治|真实原入口到结果的应用验收与结果解释。先修复ref解析，再重走所欠路径；Code前端参数、Owner People渲染和菜单link角色须在其实际边界被观察。现有后台/浏览器工具足以承接，不需要先新增编排框架|

这些是候选改进方向，未修改 variant、Skill 或应用，也没有新模型/评测。装入 Skill 与将它执行到位是不同问题；即使下一次确实读取了全部材料，也要检查其判据和动作，不能以 read 调用本身当验收。**当前证据不承诺 Skill 能提分，也不能证明同模型换提示必然消除全部缺陷。**

本轮由两个有界 Agent 分别整理完整需求/产物与原生过程，主线独立回读了 provider system、M:L21/30/41、V:L6/55、首页/菜单和同值验证的原始动作结果，以及最终源码的相关调用链。旧研究仅复用已验证链路。下载内容未运行，Factory/Braid/SVC 测试未编写或运行；未提交、部署、生成或消耗比赛额度。剩余限制为官网逐例错误与应用 Git OID 不可得，静态缺陷未追加运行复现。
