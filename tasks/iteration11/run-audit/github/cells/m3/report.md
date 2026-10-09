# M3（Issue #5 / PR #11）GitHub iteration11 审查

## 覆盖与边界

本次模型核对目前只能记为部分读取，不能声称已读完 assignment 的全部 28 个源。部分长输出调用出现工具截断，且脚本抽取字段片段不能替代完整正文阅读；2,184 records、6,195,953 characters 是 assignment 统计，不是模型已读量。已直接看到的 record 范围、截断警告和未核对范围见 `read-receipts.json`。`views/issue-5-board.txt`、`views/pr-11-board.txt` 已各自按连续不超过 20,000 字节的片段完整直接阅读，回执记录了每段范围。

早期 broad 去重流只覆盖 text/thinking/command/arguments，未覆盖 toolResult；它曾直接看到 chunks 0–102（偏移 0–2,059,999 / 4,513,852），不能单独当作全文消费。本轮主 native canonical 补流已改按 Record JSON 递归消费所有 JSON string value，完整性以该 canonical 回执为准；其它 source 仍按各自回执保持 partial。

本轮继续保留两条较小 PR 原生会话的有界缺口：`views/2026-09-29T06-50-51-338Z_01a0ebee-324a-720e-b0a9-c844ef815173.txt` 的 Record 8 嵌套正文，以及 `views/2026-09-29T06-50-29-107Z_01a0ebed-db73-7710-a24d-aaca70d257f5.txt` 的 Record 4 嵌套 issue 正文，仍因此前 `Warning: truncated output` 未声明全文完成；它们和其它未转交主 native 的 source 继续按回执保持 `partial`。

本次已完成父任务指定的主 native canonical view 全量补读。`views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 原文 2,084,432 字符、786 个展平 Record，实际来自两份 source JSONL：sessions 行 1–80 与 main 行 1–706。先前已消费的 147 个 leaf body（370,847 个正文字符；带流标题 376,977）不重复读取；本轮 canonical 补流递归解析 Records 1–786 的全部 JSON string value，新增 3,545 个 exact-unique 字符串、999,048 字符，分 70 个连续切片（stream 1,244,883 字符，每片不超过 18,000 字符）完整消费。递归范围包含 `text`、`thinking`、`command`、`arguments`、`details`、`custom_message`、`toolResult` 及其嵌套后代；精确重复只在首次完整出现处消费并引用。该 source 因 raw wrapper 分隔符、空白、Source 标题和重复包装没有逐字符重印，仍不标记 raw `full_text_verified`，但所有 JSON string value 已完成。准确凭据见 `read-receipts.json` 中该 source 的 `canonical_view_json_strings` 与最后一条 direct_read_log。cell 级 status 仍受其它 source 的 partial 范围影响。

本审查只读 snapshot-01 和 views，没有修改源码、没有运行实验或测试；主 native canonical view 已完成全量 JSON string value 消费，其它 source 的未读边界仍按回执保留，因此涉及其它 source 的判断仍以已看到材料为限。没有把独立 archive/副本中相同的 `--head` 误判为共享物理 worktree；PR #11 的复跑明确使用独立 worktree 或 `git archive` 干净副本。

### 主 native canonical 补读后的终态事实

- `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 727 记录最终平台检查的组件数量与 `PLATFORM_EXIT=0`；同一 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Records 729、784–785 进一步确认发布 head 为 `7b35656`、Playwright 21/21、干净 archive 无 core，且最终平台尾部退出 0。该事实支持旧候选已在最终 head 上复验，不改变 F1 对 core 产生者的待证边界。
- `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Records 668–675 记录共享 origin 中不可达 core blob 被 GC 后移除、refs 完整且 `fsck` clean；这是 native 会话报告的仓库维护结果，不是本审查执行的操作，也不等于已证明 core 的产生者。
- `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Records 731–738 记录 PR #11 comment #59 的最终报告和 Issue #5 comment #60 的交接；后续 Records 749–754 仍显示等待 Issue #5 负责人确认，不能把“候选 ready”直接等同于已合入。

## 结论摘要

M3 最终交付已落到 develop：候选 `15c79a4`（tree `5319a2b8`）以 merge `53532a0` 合入，最终两份独立复跑均为 platform-path exit 0、Vitest 76/76、Playwright 33/33、typecheck 通过。权限过滤、服务端私有 fork 强制、`viewerPermission` 控件依据、跨任务 `blob/tree`/contents 路径和 Access denied 后续归属均有明确证据。

过程上有两个最高影响问题：崩溃转储曾进入 PR 历史；初始候选的验收证据曾对应已经过时的 `7b35656`，develop 前进后才重做合并、结构核对和全量验收。另有一个中影响问题：平台检查与 e2e 的后台轮询、并发复跑和 stale notification 反复发生，带来可证的重复工作和恢复摩擦。

## 发现

### F1 — [高] core dump 被纳入提交历史，触发历史重写和强推

**观察与位置。** PR 原生视图 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 的 Record 547 明确记录“core dumps were committed”；该 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 549 发现并删除 `backend/core.9318`、`core.9319`、`core.9337`，并补 `.gitignore`；该 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Records 551/553 使用 `git filter-branch` 从 PR 历史移除；该 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 555 检查 `origin/develop..HEAD` 中 core 对象为 0；该 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 576 强推修复后的 PR。对应 PR board 正文及 Issue #5 board 正文的合并前提段确认这些文件约 363 MB，并在实现方的说明中推测与被杀本地进程有关；snapshot 没有 signal、进程身份或 core 生成者的独立证据。

**决定、动作与后果。** 负责人先在工作树删除文件、补忽略规则，再重写 PR 历史、强推并做对象检查。此前的候选及其平台检查不能直接沿用，平台检查还被终止并在清理后重跑。事故造成大体积对象进入共享 refs 的风险、强推和 GC 的恢复成本；snapshot 中没有证据表明凭据进入 core dump，也没有证据表明最终 develop 保留 core 对象。

**根因与竞争解释。** 已证事实是仓库此前没有覆盖这些名字的忽略规则，随后使用了宽泛 `git add -A`；“被杀进程产生 core”目前只是实现方解释，降为待证。竞争解释包括依赖安装、测试进程或平台 runner 的异常退出；需要 signal、进程树和文件产生时间才能区分。

**修复层与边界。** 立即修复落在 PR 工作流：提交前检查 `git status` 和 `git ls-files`，在任何运行前启用 `core`/`core.*`/`*.core` 忽略；推送前用 `git rev-list --objects base..HEAD` 检查大文件和 core 路径。设施层的清理/自动失败只能作为待验证的后续方向，本次材料没有足够的退出信号、进程身份和产生者证据支持把它写成根因或已授权修复。应用 Agent 侧应先在运行前启用忽略规则并在提交/推送前做对象检查；不要把 `filter-branch` 当常规补救，一旦已发布，应冻结 refs、核对对象、再决定是否强推。

**下一轮判别证据。** 新候选必须同时满足：`git ls-files` 无 core、`git rev-list --objects base..HEAD` 无 core 路径、发布 ref 与被验收 hash 相同；若 runner 被杀，日志应给出退出信号、转储路径和清理结果。当前 `15c79a4` 已观察到 core 匹配 0，说明本轮终态已修复，不证明防回归设施已存在。

### F2 — [高] 验收证据先对应旧 head，develop 前进后发生候选漂移

**观察与位置。** PR #11 在 `7b35656` 上完成第一套四项前提并宣告 ready：platform-path exit 0、Vitest 64/64、Playwright 21/21、typecheck/build 通过（PR 原生视图 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 的 Records 580, 654, 666）。随后 M1 合入使 `develop` 前进到 `a619edd`；根侧产生合并结果 `47c453e`，但 Issue #5 负责人和 PR 负责人发现该对象缺少 packet 自引用的一行，不能作为最终候选。Issue #5 board 正文及 Issue #5 原生视图 `views/2026-09-29T06-11-38-334Z_01a0ebca-4ade-741e-b226-f2b25ab95bf4.txt` 的 Records 288, 305, 322 明确把候选改为 `15c79a4`，并要求以该 hash 重跑。

**决定、动作与后果。** 负责人在 `15c79a4` 上做独立结构核对（routes 顺序、§9 重编号、§7/§7.1、`.gitignore`、无 core），根侧和干净 archive 副本分别重跑，得到 Vitest 76/76、Playwright 33/33、platform-path exit 0，且构建产物 hash 一致（Issue #5 原生视图 `views/2026-09-29T06-31-13-883Z_01a0ebdc-3adb-7187-818e-3c72e0b5b33a.txt` 的 Record 339、以及 `views/2026-09-29T06-35-38-316Z_01a0ebe0-43cc-71de-a0df-39fcffa91b2f.txt` Records 373, 407；board 正文同步）。这避免了用旧 head 证据合并，但重复消耗了安装、构建、e2e 和核对工作，并暴露出原“ready”证据并不适用于后来实际合并的候选。

**根因与竞争解释。** 根因是分支验收与 develop 合并不是一个冻结步骤：先验收 `7b35656`，再等待并合并已前进的 develop。竞争解释是 M1 合入本身引入了真实路由/文档冲突；记录确实显示冲突发生在 `routes.tsx` 与 `architecture.md`，但若早先先做候选合并再验收，仍可避免旧证据失效。

**修复层与边界。** 流程层应固定顺序：先把候选与目标 base 合并（或生成不可变合并候选），再在该最终 hash 上做结构核对和完整验收；使用 `--match-head-commit`、`merge-tree`、tree hash 和运行条件绑定每一份结果。Issue/PR 正文应禁止把“旧 head 已通过”写成当前 ready。当前 `15c79a4` 已按正确顺序复验并以 `53532a0` 合入，develop tree 与候选 tree 一致；这是本轮的有效终态证据。

### F3 — [中高] 初始设计误读需求，跨任务边界和共享契约后置修正

**观察与位置。** Issue #5 comment #20 及 PR packet 初稿把“访客使用 Code 克隆入口”登记成隐藏入口，并把登录态 e2e 暂定为临时直插 session；advisor transcript 视图 `views/7ab36782-c477-4072-a0b9-19e85128e434_advisor_0_transcript.txt` 的 Record 48 指出权威 REQ-3-2-3 明确允许 visitors，REQ-3-3 的 THEN 还要求点击文件进入 file-content page，且 `blob/tree` 路由没有被现有 §7 约束。PR 原生视图 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 的 Record 1；Issue #5 原生后续记录和 board 正文显示随后修正为：访客可见 Code button、Fork 仍仅登录可见、M3 提供最小 blob/tree 内容页、contents API 及 href 断言，并由 Issue #5 comment #42 将其升格为共享契约。

**决定、动作与后果。** 负责人没有直接悄改共享文档，而是先在 Issue #5/Issue #1 登记，得到根裁决后把 §7 双态搜索框、§7.1 五条约定和修订记录纳入 PR；登录 API 已在 develop 的事实也被 comment #29 更正，最终改走真实 `POST /api/auth/sign-in`。这使设计/实现分离最终恢复，且 M4a 有明确消费边界；代价是新增 advisor 循环、契约评论、最小内容页实现、文档提交及多轮回归。

**根因与竞争解释。** 根因是模块方案先固化了一个与权威原文冲突的 UI 假设，并把跨任务路由当成自然约定。竞争解释是需求文本本身存在 REQ-3-4 的确认输入矛盾、概览与 Code 页重叠等歧义；这些确实增加了判断难度，但不能解释访客 Code 入口和 file-content THEN 已明确存在这一事实。

**修复层与边界。** 方案阶段应先逐条提取原子需求的 GIVEN/WHEN/THEN，再登记 assumptions；跨模块路由、接口、权限展示条件应在实现前进入共享契约。实现层继续保留服务端 `canViewRepo`、私有 fork 强制 private、`viewerPermission` 驱动 UI 的约束。§7.1 约定 4/5（最后触碰提交、空分支 200/缺失 404）已明确转交 M4a，不能把 M3 的现有近似当成已修复。

**下一轮判别证据。** 读取 M4a/Issue #6 的实际消费结果，确认它沿用 `blob/tree`、contents 响应和 1–3 约定，并为 4/5 提供对应测试；确认 PR #14 的 Access denied 登录态 e2e 不改变 API 404 防枚举契约。当前 M3 记录只证明接口已登记和自身 16 条 repos e2e 通过。

### F4 — [中] 平台检查、e2e 和环境排障存在大量重复轮询与并发运行

**观察与位置。** PR 原生视图 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 的 Records 385–646 连续读取平台日志、进程状态、npm cache、后台任务状态；脚本统计该源中与 `pr11-platform`/`pr11-e2e`/`sleep` 相关的 tool calls 为 117 次。单次平台检查因 registry latency 从约 05:52 持续到 06:00，后续 final2 又跨多个 200–300 秒 sleep；同时该 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 618 记录 @glm-4 的独立复跑在竞争 registry/CPU。中途多次 kill 平台任务并重新启动，之后才得到 `7b35656` 与 `15c79a4` 的稳定结果。

**决定、动作与后果。** 负责人在安装阶段反复 tail/ps/ls，虽然多次文字上说“等待完成通知”，实际仍继续轮询；一轮平台任务被 stale/旧 head 或 core 清理打断，重跑多次。后果是可证的重复模型响应和墙钟等待，且并发 npm 安装降低环境可诊断性；现有材料没有足够计费语义，不能把这些记录换算成金额。

**根因与竞争解释。** registry 慢和 better-sqlite3 预构建下载是真实环境因素；但重复轮询和独立验证并发仍是编排问题，不能全归因于网络。另一个竞争解释是平台检查本身阶段较长，部分 tail 是必要诊断；因此报告只把重复同一日志状态的调用列为已证冗余，不把所有等待时间都判为浪费。

**修复层与边界。** 应用 Agent 侧审查编排应只保留一个有 owner 的长作业，在会话内保存候选 hash、阶段和最后变更游标，并只在状态变化/完成/失败时读取；禁止主会话并行启动同一候选的重复 platform-path。安装慢时记录阶段和 cache/network 事实，不靠重复 `tail` 轮询。平台设施如何清理或通知超出本次已证边界；开发侧旧监控说明已删除，不注入参赛运行。

**下一轮判别证据。** 新 run 应能从一条作业记录还原启动、阶段迁移、退出码和清理，且同一 `(candidate tree, recipe)` 只对应一个平台作业；若再出现 117 次同类 tail 或多个并发 npm 安装，应视为编排回退。当前最终结果本身通过，不代表等待/并发流程已改进。

### F5 — [中] 交接后的 stale notification 重复唤醒，没有状态去重

**观察与位置。** PR 原生视图 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` 的 Records 674–706 在短时间内反复收到 superseded/stale platform 输出，负责人多次回复“no action needed / state unchanged”，并重复说明旧候选 `7b35656` 已被 `15c79a4` 取代、等待 @glm-4 确认。材料没有给出 job id、revision 或 event id，不能进一步证明这些输出属于同一 job/同一 revision。Issue #5 原生视图 `views/2026-09-29T06-48-49-940Z_01a0ebec-5814-7099-983f-b1e37881e214.txt` 的 Records 8–34 及 `views/2026-09-29T07-00-41-839Z_01a0ebf7-34ef-76e7-83db-63836efb47bd.txt` 的 Records 4–10 随后按 #80/#81/#82 读取并整理终态。

**决定、动作与后果。** 负责人正确地没有在旧分支继续写入，也没有把 stale 输出当成新证据；但会话仍把旧 tail 作为多次需要处理的更新。后果是重复上下文、重复“已完成”判断和交接噪声，增加了错把旧 head 当当前 head 的风险。

**根因与竞争解释。** 当前只能确证存在旧候选输出被反复展示，不能从 snapshot 证明后台作业没有按 job/revision 去重。待证解释包括旧 watcher 事件、多个独立作业的相同 tail，或交接方重复读取同一日志。竞争解释是其中一部分更新确实携带了新的 Issue/PR 评论，不能全部删除；需要 job/revision/event 身份后才能决定去重层。

**修复层与边界。** 这是开发侧审查编排的待补证方向：下一轮若仍需通知，应在记录中携带 `(job_id, candidate, revision, status)`，再判断是否丢弃旧 tail；不把已删除的开发侧监控说明或此类通知设施直接注入参赛运行。交接消息中保留一次精确断点即可，后续用稳定读取入口而不是重复全文重读。

**下一轮判别证据。** 观察同一 run 的终态后是否仍产生 stale 事件；统计每个 job 的唯一 revision 与唤醒次数。当前没有 evidence 表明 stale notification 改变了最终源码或验收结论，影响主要是消费与交接摩擦。

## 主 native 补读确认的过程事实

- 实现方在 `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 64 记录了平台 Node 20 路径下 `better-sqlite3` 可加载（输出版本 3.49.2），同一 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 66 记录基线后端测试为 5 files / 38 tests 通过；这是当时 native 会话的环境排障和基线证据，不是本审查重新运行。
- `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 72 记录 Playwright 剪贴板 probe 成功读回 clone URL；同一 view `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 73 随后把权限配置纳入 e2e 计划。这把 REQ-3-2-3 的 clipboard 风险从未知降为已做过定向验证，但 probe 只证明该浏览器/权限条件下的能力，不替代最终候选的全量验收。
- 同一 view Records 58–59 显示实现方在写代码前先读取 helpers、copy-contract、seed、permissions 和 session e2e；Records 67–69 显示其把 task packet、clipboard probe、事务回滚验证列入顺序计划。它证明了设计和验收意图，不能单独证明计划中的 seed/事务测试后来全部实现。
- `views/2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.txt` Record 19 的规划文本明确发现 “clone 对访客隐藏” 与 REQ-3-2-3 允许访客使用相冲突，并决定回 Issue #5 更正；该补读支持 F3 的“先误读、后登记裁决”归因，但不能把规划决定本身当作共享契约已经生效的证据。

## 权限、契约和验收专项判断

- 服务端搜索、详情、contents 和列表均以共享访问规则过滤；不可见私有仓库返回与不存在相同的 404，私有 fork 的 private 约束在服务端执行。前端控件依 `viewerPermission`，访客 Code button 与登录态 Fork button 的边界在更正后与原文一致。
- 初始方案对访客 Code 的假设错误，但已通过 Issue #5 comment #32/#34/#42 和 e2e 修正；不能把旧 comment #20 当当前契约。
- REQ-3-4 的“无需重输名称”描述与 WHEN/THEN 的确认输入相矛盾，实施按页面要求输入完整名并保留不匹配仍为 Private 的分支；这是已登记的解释，不应在下一轮悄然改变。
- M3 的 API 防枚举与后续 `RepositoryMissing` 会话态呈现已分离：PR #14 负责登录态 Access denied e2e、copy/docs 和 packet 陈旧段刷新，且须先于 PR #13。该后续项不改变 M3 API 404 语义。
- 最终验收证据只采信 `15c79a4`/tree `5319a2b8`：根侧和干净 archive 副本均通过 platform-path exit 0、Vitest 76/76、Playwright 33/33、typecheck；develop `53532a0` 的 tree 与候选一致。早期 `7b35656` 的 64/64、21/21 只能作为历史阶段证据。

## 交接与未读边界

M3 交付主体已完成并合入 develop；本 cell 的材料审查覆盖仍为 `partial`，不能把交付状态误写成全文审查完成。建议主审把 F1/F2 标为最高优先级的设施/流程改进，把 F3 的已修正设计偏差作为需求读取与共享契约登记案例，把 F4/F5 纳入运行监控和通知重建。当前 cell 未审其它 Issue/PR 的实际消费结果，因此不能把 M4a 对 §7.1 约定 4/5 的完成情况推广为已修复；也未重新读取其它 cell 的 coverage.json。
