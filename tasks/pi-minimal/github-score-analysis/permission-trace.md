# GitHub c3fea0c3488c：非累积操作权限失真的原文链

本次仅本地只读取证并整理本文；未执行下载应用、未运行测试、未调用网络或模型 API、未改源码、未生成或评分。结论限定于 issue 权限这一条链，不据此解释全部 2/100 或全部功能失分。

**最有力的链：原始需求明确排除 Write，并已进入主会话 → 首次架构摘要把允许集合压成 `Triage+` → fresh advisor 读到同一排除规则，仍把 `Triage+` 判断为匹配 → 后端和前端共同实现等级阈值 → 验收只用 Read 拒绝、Maintain 放行等不能区分两种模型的例子 → 以“全部权限已验证”和“严格按需求”交付。** 已记录的错误不是单纯忘记鉴权，而是把“有效角色取最高授权”和“每项操作的允许角色集合”混在一起。后者是归纳解释；记录没有直接陈述主模型产生该混淆的心理原因。

## 证据命名与时间

所有时间均为 2026-09-30 UTC；所有行号为文件物理行号，从 1 开始。下列简称均可从仓库根定位：

- `E` = `runs/analysis/pi-minimal-github-20260930/20260930T031746Z`
- `T` = `E/c3fea0c3488c/extracted/template`
- `M` = `T/.factory26/pi-minimal/session.jsonl`（711 行，主 Agent）
- `A` = `T/.factory26/pi-minimal/session/dc12f443-1021-4428-9573-e360a0e6112f/run-0/session.jsonl`（52 行，advisor）
- `R` = `T/requirements/requirements.yaml`（3820 行公开需求）

### 1. 原需求何时可见，首次错在哪里

| 原文位置 | 消息 id / UTC | 观察及短引文 |
| --- | --- | --- |
| `M:4` | `a6c91f6d` / 01:18:50.405 | 运行输入要求“验收判据来自原需求与初始条件……不要让现有实现反过来决定判据”；也要求咨询 fresh advisor，主 Agent 保留判断责任。 |
| `M:9–10`；对应 `R:18–20` | 返回 `b0f41d25` / 01:19:05.574 | `read` 参数是完整 YAML 路径；首块返回 ROOT：“these roles are not an automatic cumulative ladder”。返回尾部明确为第 1–618 行及继续读取 offset，非只有标题或摘要。 |
| `M:17–18`；对应 `R:2142–2151` | 返回 `a8a06e90` / 01:19:29.422 | `read` 参数 `offset:1797, limit:560`。完整返回 issue 模块规则：“Write can create, edit, and comment but cannot assign, label, set milestones, or change status.” 在原子细则之前已给出明确 Write 负例。 |
| `M:19–20`；对应 `R:2653–2664,2702,2733,2741–2742` | 返回 `c0eaa9e7` / 01:19:34.063 | `read` 参数 `offset:2357, limit:560`。标签允许 Triage/Maintain/Admin，“Read and Write users may only view … the server rejects their submissions”；里程碑及关闭/重开也明确排除 Write。 |
| `M:23–24` | 返回 `5f7d6e2a` / 01:19:43.298 | 最后一块 `offset:3619, limit:210` 到文件末尾。此前返回依次覆盖 1–618、619–1158、1159–1796、1797–2356、2357–2916、2917–3618；至此原需求全文已按块返回。这里证明可见性，不等于证明逐句理解。 |
| **`M:30`** | **`af8a7b56` / 01:23:59.084** | **最早定位到的错误操作权限转述**：先写“Role ordering: Read < Triage < Write < Maintain < Admin”，随后把 issue 权限写为“create/edit/comment: Write+; assign/label/milestone/close: Triage+”。错误的决定性部分是后半句允许集合变阈值，而不是角色聚合使用排序本身。 |

`R:1071–1075` 确实要求有效仓库角色是 Owner 的 Admin、直接授权和团队授权中的最高者，随后仍按 ROOT 操作规则鉴权。因此保留角色排序用于“哪一个角色生效”有需求依据；不能从排序推出 Write 自动获得 Triage 的 issue 操作。主会话在收到显式负例约四分半后就出现错误摘要，不能归因于后期才丢失了这条信息。

### 2. advisor 并非没看到，也并非调用失败

| 原文位置 | 消息 id / UTC | 观察及短引文 |
| --- | --- | --- |
| `M:36–37` | 请求 `adf80123` / 01:24:49.095；返回 `9b85bb5d` / 01:24:49.129 | `subagent` 参数 `agent:"advisor", context:"fresh"`；给出原 YAML 路径，但摘要自身写“Order Read<Triage<Write<Maintain<Admin”及“issue close needs Triage+”。五个具体问题集中于重建种子、组件库、commit 存储、运行版本和可访问名称；没有单列这条排除规则。工具确认 async 任务成功启动。 |
| `A:6–9` | 读请求 `52239938` / 01:24:58.110；组织技能返回 `5a188290` / 01:24:58.116 | advisor 实际读取 Ponytail、认证和组织技能正文。组织技能要求先写出产品允许操作及有效权限规则，插件“does not define the application's repository, issue, or review permissions”。 |
| `A:13–14` | 返回 `34020f7c` / 01:25:05.245 | `read offset:1, limit:60`；再次看到 ROOT 的“not an automatic cumulative ladder”。 |
| **`A:20–21`** | 返回 **`5a9ac217` / 01:25:13.067** | `read offset:2136, limit:28`；读到 `R:2149–2151` 原文，含“Write … cannot assign, label, set milestones, or change status”。故不能解释为 fresh 委派只给了摘要、advisor 没机会看排除项。 |
| **`A:32`** | **`24bfa834` / 01:26:11.604** | 已记录的直接错误判断：“Permission for issues: Write can create/edit/comment; Triage can assign/label/milestone/close/reopen. The plan says ‘issue close needs Triage+’ which matches. Good.” |
| `A:42` | `c1fa1843` / 01:27:46.488 | 再次并列正确集合与错误结论：“Write, Maintain, and Admin may create …; Triage, Maintain, and Admin may assign…”；接着“The plan says issue close Triage+. Good.” |
| `A:52` → `M:62` | advisor `c2f56d72` / 01:29:01.845；主线通知 `6967ec7e` / 01:29:22.166 | 实际最终回复为“The plan is basically sound”；列出的主要风险为可访问名称、ARIA 和合并逻辑，没有纠正操作权限。内部 `A:32/42` 的错误判断不等于逐字回传主线；主线实际得到的是无权限纠正的总体背书。 |
| `M:63` | `7480c445` / 01:30:22.166 | 主 Agent 称“Advisor confirmed the approach with key fixes”，落实三方合并等意见，随后继续实现。 |

解释上，委派摘要把错误阈值设为候选方案，可能造成锚定；但 advisor 主动获取了足以推翻它的独立原文，还明确判断“matches”。因此更强的证据是**复核也发生了集合到阈值的语义误判**，而不只是材料路由不足。记录无法证明锚定的实际心理权重。

### 3. 从摘要到实际写入，正确注释没有约束调用

| 原文位置 | 消息 id / UTC | 实际 toolCall 参数与反馈 |
| --- | --- | --- |
| `M:46` | `219a38f0` / 01:26:04.421 | “While installs run and advisor reviews, let me start writing the backend.” 开始数据库等实现；权限失真此前已出现在 `M:30`，不是这条开始动作才发生。 |
| **`M:52–53`** | 请求 **`c1bcc65d` / 01:26:59.783**；反馈 `d0dd1932` / 01:26:59.785 | `write` / `call_d6a4b5c46a214be6a8fb8803` 写 `backend/src/perms.js`。内容同时保留“Roles are not a cumulative ladder for per-operation gates … explicit role sets otherwise”注释，并定义 `Read:1,Triage:2,Write:3,Maintain:4,Admin:5` 及 `ROLE_ORDER[role] >= ROLE_ORDER[min]`。反馈“Successfully wrote”。单独存在 helper 尚不等于错误；错误在不允许用阈值的调用处。 |
| **`M:73–74`** | 请求 **`140a5de1` / 01:34:15.777**；反馈 `55d499e5` / 01:34:15.778 | 思考再次写 `PUT labels (Triage+)`、`PUT milestone (Triage+)`、`POST close/reopen (Triage+)`。`write` / `call_d3bccbd636d046ffb544f85e` 参数为 `backend/src/routes/issues.js`，定义 `requireIssuePerm → hasAtLeast(role,min)`；标签、里程碑、状态传入 `'Triage'`。反馈成功。注意实际状态路由写入的是 PUT；这里按思考原文保留 POST。 |
| `M:157–160` | UI 请求 `ff222dc5` / 01:51:12.752，反馈 `16b58e40` / 01:51:12.754；helper 请求 `0479e8f4` / 01:51:24.079，反馈 `b1717feb` / 01:51:24.082 | `IssueDetail.tsx` 写入 `canTriage = hasAtLeast(role,'Triage')`；`role-utils.ts` 写入同样的数值角色表和 `>=`，两次均成功。 |

交付源码仍对应这条写入链：`T/backend/src/perms.js:9–12`；`T/backend/src/routes/issues.js:205–211` 的统一检查及标签 `:331`、里程碑 `:357`、状态 `:381`；`T/frontend/src/role-utils.ts:2–6` 和 `T/frontend/src/pages/repo/IssueDetail.tsx:41`。Write 的 3 大于 Triage 的 2，所以前后端都会放行。这是静态代码推导，本轮没有执行应用验证请求。

异步时序是事实，但不能单独解释漏纠正：helper 在 advisor 完成前写入，issue 守卫则是在主线收到 advisor 结果之后才写入；advisor 本身也未建议修正。

### 4. 为什么后续验收没推翻错误模型

| 原文位置 | 消息 id / UTC | 观察及证据边界 |
| --- | --- | --- |
| `M:616` | `4f2c3845` / 02:40:10.640 | 验收列表写“issue close/reopen as Triage (dave-reader Read should see no buttons)”。这里挑出的负角色是 Read，未列明 Write。 |
| `M:620–621` | 请求 `5255b569` / 02:40:33.403；反馈 `4f58515f` / 02:40:33.525 | 明确准备检查 dave 的 issue 状态和 metadata 控件；API 反馈 `viewerRole:"Read"`。 |
| `M:624–637` | 首次失败反馈 `b45ec15b` / 02:40:57.932；识别失败 `8432eb90` / 02:41:43.557；最终反馈 `1c352623` / 02:42:38.116 | 首次登录为 `Unknown ref: e`；主 Agent 认识到访客状态和 PR inline 按钮缺陷，修复后重新登录。最后反馈 Account menu 计数 1、PR Add comment 计数 0。因此不能笼统说 Read 走查从头到尾都是假登录，早期失败已处理。 |
| **`M:630`** | **`7df791ac` / 02:41:58.907** | **自审直接拿已有 helper 当正确性依据**：“metadata pickers … are gated by canTriage — good. Close/reopen gated by canTriage — good.” 同条又说 bob 有 Write、非 PR 作者，应有 PR Add comment；这是另一个操作的允许例，不能替代 issue Write 拒绝例。 |
| `M:638–639` | 请求 `59d430a6` / 02:42:50.040；反馈 `ab11d0cd` / 02:42:51.116 | dave 会话打开 issue 1，分别计数 Close/Reopen 和 Assignees/Labels/Milestone，返回 `0`、`0`。这证明该次 Read UI 边界符合预期，不能区分集合模型和错误阈值模型。 |
| `M:640–641` | 请求 `7ea1a267` / 02:43:00.581；反馈 `a84e7e87` / 02:43:00.693 | 命令注释“close/reopen as triage: carol has Maintain”，实际使用 Maintain 账号 PUT issue 3 status，返回 `{"ok":true,"status":"closed"}` 和 open。Maintain 在两种模型都允许，也不能区分它们。不是一次真实 Triage 专项检查。 |
| `M:642` | `f738942f` / 02:44:10.196 | 随即声称“All permission gates verified” / “Permission gating fully verified”，开始写应用测试。原始 Write 禁止例没有出现在这条完成判据中。 |
| `M:642,665` | 写入同上；运行结果 `a6a8e3f9` / 02:46:19.979 | 已交付 `backend/test/core.test.js:9,22–65` 的权限相关覆盖是有效角色、私库读取、团队直接成员和最高授权；14 项记录通过，但没有 issue 操作的 Write 拒绝断言。本轮只读已有内容及历史结果，没有执行这些测试。 |
| `M:699` | `8588a1d1` / 02:50:57.999 | 最终说明仍称“各操作门禁严格按需求逐条列出（如 issue 评论需 Write+、关闭需 Triage+），不做隐式阶梯”，并泛称各角色控件边界已验收。错误摘要和完成声明在同句并存。 |

主会话 toolCall 参数的定向搜索没有定位到以 Write 身份对 issue 标签、里程碑、状态提交并要求拒绝的检查。不能将这表述为所有未记录行为都不存在；可以确定的是，上述可回溯验收证据没有形成这一关键反例，而静态交付代码仍会接受它。

## 技能、指引与上下文边界

认证/组织指南是可用的。主会话 provider-facing 系统文本 `E/c3fea0c3488c/provider-system-glm-5.3-flash.txt:59–66` 有两项技能目录，`M:4` 又明确要求匹配后读正文。主原生 toolCall 中只定位到 `M:201`（`819582b6`，01:56:48.897）读取 agent-browser 技能，未定位到主 Agent 读取这两项正文。**不能因此写“技能整体未采用”**：advisor 已在 `A:6–9` 实际读到正文；组织技能本身要求明确操作与有效权限，未要求使用累积角色，也未替应用定义 issue 权限（冻结正文 `E/frozen-materials/skills/organization-best-practices/SKILL.md:8–10`）。

Ponytail 的效率倾向实际注入，但同一主系统文本 `provider-system-glm-5.3-flash.txt:152–161` 明确要求不得删掉显式需求和安全措施、先读懂问题。advisor 的 `provider-system-kimi-k2.7-code.txt:166–175` 也保留这些约束。没有直接证据说模型是受某一技能句子驱动而改成阈值；把“懒惰/简单化指引导致错误”作为确定归因不成立。较窄且已证的是：通用保真提醒、正确代码注释和一次 fresh 咨询都存在，却没有产出能识别 Write 例外的具体判据。

主原生仅一条 session、一次初始模型设置，记录类型为 700 条 message 和 8 条 custom_message；custom_message 是 advisor 完成及后台 bash 结果，没有 compaction 或 branch-summary 事件。advisor 为独立 fresh 会话，52 行也无此类事件；不能假定它继承主上下文。记录不足以排除服务端另行截断，但已证错误在早期全文分块返回后出现，advisor 的更短独立上下文也同向误判，所以“只因主会话后期 compaction 遗失规则”与现有证据不符。

## 竞争解释、覆盖与具体调整

- **没提供/没返回需求**：由 `M:10/18/20` 和 `A:14/21` 反证。返回不等于理解；能支持的是语义转述及复核错误。
- **只是一处手误或忘记调用鉴权**：早期计划、advisor 判断、前后端 guard、自审和最终声明多次一致，反证“仅局部代码笔误”。
- **advisor 失败或返回太晚**：工具成功、结果已读；issue 实现在返回之后。咨询未能纠正是明确事实，而非传输故障。
- **只因缺组织技能**：主线未定位到正文读取，确属流程缺口；但 advisor 实际读过却仍误判，单纯强制多读一遍不保证识别本例。
- **独立覆盖限制**：本次定向读取需求返回、权限设计/写入、advisor、后期边界检查及交付声明；没有逐条复核其他 47 项功能，没有官方逐例失败日志，不能计算本缺陷造成多少分损失，也不能证明任何提示词调整必然提分。

仅提出两项与本链直接对应的候选方法，未实施：

1. **在架构摘要中分开记“有效角色来源”与“操作允许/拒绝集合”**；凡需求有显式排除项，原样保留为一句反例，不用 `Triage+` 等缩写替换。此题应直接写：issue 标签/里程碑/状态允许 `{Triage, Maintain, Admin}`，拒绝 `{Read, Write}`。advisor 应先把候选方案代入这个反例，再作整体判定；它已持有足够原文，无需再扩大阅读范围。
2. **把能区别错误模型的例子作为验收门槛**：本题固定一个确认为 Write 的隔离会话，检查相关控件不可用，再验证服务端提交被拒且对象未改变；与允许的 Triage 或 Maintain 操作配对。Read 拒绝、Maintain 通过和 helper 存在只能作为局部证据，不能据此声明全部权限通过。该建议面向生成应用自身验收，不新增 Factory/Braid 测试。
