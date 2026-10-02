# I11 Sheet 继承过程：需求、SVC 与 Pi 角色

## 身份与阅读边界

本 cell 只解释 I10 Sheet 运行的早期需求理解、规划、分工和局部验证；这些行为属于 run `20260929-042409-811f18d4` 的 I10 继承来源。I11 的工作是暂停副本的恢复/语义整理，不把最终生成 `396538bc0dda96`、官网 `fe617f4f8526` 或 59 分倒推为早期过程缺陷。主要证据是 `tasks/iteration11/run-audit/sheet/report.md`、`coverage.json`、`cells/{base, a, b, c, root, root-late}`，以及 `evidence/input/requirements.yaml`、选定的 native JSONL 和子代理 artifact；不重复阅读 176 个源。原始覆盖截止 `2026-09-29T08:04:43.268468Z`，没有把未采集的晚期 D/E 原生过程或最终评测当作本 cell 已读证据（`cells/base/report.md:5-7,77-79`；`report.md:106-117`）。

## 需求理解、规划与持久化方法

1. **需求先被分层，而不是从应用结果反推。** `requirements.yaml` 的 ROOT 明确要求在线表格工作区、持久 workbook/worksheet 状态、ARIA 语义和精确错误文案（`evidence/input/requirements.yaml:1-36,48-103`）；但约 100 个场景中的 WHEN/THEN 共 308 处被同一占位短语破坏。根会话先读 `svc-design` 和 `svc-task-packet`（native `000-...01a0eb68...jsonl:1-3`，消息 `18163b83`、`75f285c0`），再让 advisor 独立核对幸存 token、种子和替代技术路线（`cells/base/initial-advisor.md:7-33`，artifact `afffce3b...advisor_transcript.jsonl:42`）。因此 D1 将 ATOMIC description 作为验收权威，场景只取种子/具体值；D2 采用最大一致种子 `Q3 Sales`、Sheet1 `A1:C4` 加空的 `A5:C6`、空 Sheet2；D3 选择自研 ARIA 网格/公式引擎、React/Vite、Express/better-sqlite3、SQLite 和 `/workbook/:id`（根正文消息 `606aec3a`，native `002-...01a0eb79...jsonl:4`）。这条链的有效性来自需求文本、advisor 的互斥 GIVEN 分析和随后实现消费，而不是来自最终分数。

2. **SVC 方法实际改变了工作交接形态。** `svc-design` 要求在共享边界/不确定验收前取得独立判断；`svc-task-packet` 要求把当前真相、约束、证据、未决项、owner 和下一步留在可恢复 packet，且不取代需求、源码或验收证据。原生 advisor 配置还内联加载了 `svc-design/references/workflow.md`（session `01a0eb6b…`，消息 `d40ffc1a`），所以以下行为是 SVC 文档与 Pi 角色指令叠加后的实际效果，不能归为某一 skill 的独立净效应。其实际结果是：根把 D1–D3 和契约 v1 放进 Issue #1；基础 PR #2 将表结构、事务、raw、snapshot、ARIA、错误体写入 README；B 的 `tasks/issue-4-b/packet.md` 链到 comment #35/#38/#39，注明设计 owner 与 PR #9 实现 owner；C 的 packet/Issue 正文链到 comment #107、A-3 接缝、D-C1…D-C14 和 PR #10（`cells/b/report.md:11-15,54-57`；`cells/c/report.md:21-25,44-61`）。这使后续成员能消费 `0` 基索引、`updatedAt`、6×26、结构端点、公式 raw/显示值单一接缝等具体接口；同时也暴露了 README、packet、PR body 和根评论分持当前版本的维护成本（`cells/a/report.md:9-11,26-30`）。

## 2–4 条正向因果链

### 链 1：需求损坏 → 共享契约 → 基础与业务消费

根/advisor 发现 ATOMIC 可读、约 100 个场景中的 WHEN/THEN 共 308 处被同一占位短语破坏，并记录种子冲突；根据此写 D1/D2/D3 和契约 v1。PR #2 实际消费 0 基坐标、整批拒绝、`updatedAt`、显式 row/col、raw 原文、选区矩形、稳定 URL 和平台 Node/SQLite 基线；A/B/C/D 又从 README/packet 取得这些入口（`cells/base/report.md:17-21,69-75`）。这是有效的需求到实现链。替代解释是“场景 GIVEN 可能由 harness 按族重置”；证据没有证明存在重置机制，所以最大一致种子和 UI 覆盖被保留为假设，而不是伪装成需求事实（`cells/base/initial-advisor.md:17-21`）。

### 链 2：版本传播缺口 → 旧候选交接 → 主动读取和独立验收修正

根 #51/#57/#60（v1.3）在 06:12–06:15 直接投给 Issue owner 等，未直接投 PR #8 实现 owner；PR8 06:17 仍以旧契约交 `d536aa2`。这证明的是“投递范围 + 交接前未强制刷新”的断点，不是消息丢失：PR8 06:31 主动读取 Issue #1 与相关评论，提交 `559a0bd`，在 B helper 合入后 rebase 为 `a23af5a`，Issue3 #88 独立验收并合入 `e63efc6`（`cells/a/report.md:9-21`）。有效消费例是 #47 对 README 两条尺寸路径的 diff 反馈；无效例是旧候选交接仍写“待根裁定”，以及后续旧 `used range` 文句与新 `max(包围盒,足迹)`冲突（#100，`cells/a/report.md:11,27`）。

### 链 3：advisor 反例 → B 设计/packet → 预演修复真实数据库边界

Issue #4 先读需求、契约、`svc-task-packet`/`svc-design`，advisor 给出 `{index,count,side}`、selection 四角+anchor、服务端同事务位移、`r2 -= 1`、pivot 源先查后删和结构上限等反例；这些被写入 comment #35、packet 和 PR #9 交接，vision 仅补充中文参考图的菜单布局及其缺口（`cells/b/report.md:11-15,47-57`；advisor `99522beb...:76`，vision `5dc65496...:13`）。随后 PR9 预演直接按 `row=row+1` 更新触发 SQLite 复合主键冲突，改用两阶段 `SHIFT_OFFSET`，并保留失败日志和独立浏览器证据（`cells/b/report.md:19-24,28-31`）。这里的因果来自原始 probe → 代码修复 → 后续验收；不能把最终 B 回归状态扩大成所有结构路径均已验收。

### 链 4：C advisor/explorer → 公式契约 → 深嵌套修复与新增回归

Issue #5 以 ATOMIC + 根 v1–v1.3 为权威，advisor 将复制越界定为精确 `=#REF!` 整式塌缩、区间/标量越界分开、严格数值语法、错误优先级和逐格隔离；设计 comment #107 将其落为 `shared/formula.js`、`shared/a1.js`、`evaluate(cells,bounds?)` 和两侧共用 rewrite API（`cells/c/report.md:21-36`；advisor `1c5d1c7c...:88`）。vision 只确认截图没有种子、公式结果或公式栏验收证据，因此被正确降级为布局背景。explorer 读取候选 commit 并实跑只读探针，发现 2,000/5,000 层括号会把 `RangeError` 抛出整表，且缺 `=A7` 与错误修复依赖 e2e；Issue #5 写入 #147/#149，PR #10 在 `d6ca6d4` 加深度预算、逐格保护和回归（`cells/c/report.md:38-42,50-61,67-75`）。这是有效独立反馈。无效边界是：explorer probe 不是正式 e2e，vision 不能证明计算语义；复制/粘贴端到端仍交给 D/整合阶段。

## Pi 角色输入/输出与缺口

| 角色 | 实际输入与输出 | 被消费的有效/无效例 |
|---|---|---|
| advisor | 根：损坏需求、种子/技术/URL/持久化；B：结构和 selection 反例；C：公式歧义与错误优先级。 | 根的 D1–D3、B #35、C #107 具体改变契约。未证明 6 行必需、库方案必然失败或 seed reset 存在。 |
| vision | 9 张中文 Drive/Sheets/Excel 风格图，输出布局、菜单、选区和“无对话框/无粘贴结果”等事实。 | 只作为视觉背景；英文 ARIA、错误文案和粘贴结果回到 ATOMIC/实际操作。把截图当功能验收会是无效消费。 |
| explorer | C 候选 commit、只读 probe，输出深嵌套整表抛错及 e2e 缺口。 | 转成 #147/#149、`d6ca6d4` 和 35 条回归；probe 本身不算最终验收。 |
| executor | 旧审查截点内未发现独立 `executor` transcript/artifact；PR owner 承担实现与浏览器/平台执行。C 主会话读取 `agent-browser` 并启动包装检查（`cells/c/report.md:50-59`），不能改称为独立 executor 结论。完整源的 181 次 subagent 索引中也未见 `executor` 调用，但这只是索引事实，不能替代实现 transcript。 | 旧截点判断应限定为资料边界，不据此断言“未执行”或“执行失败”；应保留 owner、候选 head、命令输出和终态来补证。 |

## 继承结论与剩余缺口

早期过程的有效机制是：ATOMIC/假设/替代解释分层，advisor 在承诺前介入，packet 保存跨重建入口，B/C 的独立 probe 能改变实现，合入前后以 commit/tree 身份核对。可改进处是根评论与消费者投递未绑定“当前版本”，旧候选可在未刷新时交接；无关回执、上下文重建后重复确认和 timeline 无分页提示放大了成本，但不能据此把全部等待或后续 59 分倒归某一角色（`cells/root-late/report.md:15-31,35-63`）。晚期 D/E 的完整原生过程、最终整合门禁和官方评分不在本 cell 的继承证据范围；恢复 packet 只保留其当前可复核状态与未决门（`tasks/iteration11/recovery-curation/sheet/packet.md:12-20`）。

## 晚期继承补充：D/E 的排序、公式引用与取值层

这是对旧截点之后完整源的有界增量回读，不把晚期实现倒推为早期缺陷。正向链是：REQ-5-1-1 要求“entire records move together by row”，且排序后 formula bar 的 references/results 要与 new positions 一致；C 在 #365 给出可复跑反例：`=B2*2/=B3*2/=B4*2` 随 `A2:D4` 排序若只搬 raw，South 行显示 East 的 2400，故提出 RT（按 `oldRow→newRow` 改写）。独立 advisor（索引 `evidence/subagent-calls.json:1621`，产物 `work/native-homes/pi-deepseek-fast-01a0ecca-0119-7532-a2c3-6b0a196170ed/subagent-artifacts/94df6b1c-a492-4405-8a90-41533676e1c0_advisor_output.md:5-20`）按需求内部措辞裁定 RT，否定 R0 与整体位移 RD；随后 E #396 正式把 RT 写成当前权威（`work/native-homes/pi-deepseek-fast-01a0ecc7-f2f1-7dc3-a204-8742c8e202ac/2026-09-29T10-48-42-721Z_01a0ecc7-f5e1-731b-a08b-49ba1031c6ef.jsonl:287`），并明确仅矩形内被引格改写、`$` 保留、矩形外/跨界区间不动、无 `#REF!` 塌缩，同时把排序键与透视读取统一到显示值。

该判断被 C/根侧继续消费，而非停留在 advisor 意见：#408 报告 `rewriteRefsOnRowPermutation` 位于 `7ba7916`，72 tests、类型门通过且可无冲突 cherry-pick（`work/native-homes/pi-deepseek-fast-01a0ecc7-f2f1-7dc3-a204-8742c8e202ac/2026-09-29T10-48-42-721Z_01a0ecc7-f5e1-731b-a08b-49ba1031c6ef.jsonl:374`）；#410 将其登记进 PR #10 正文，要求 PR #12 单函数接缝（`work/native-homes/pi-deepseek-fast-01a0ecda-3772-78d0-bfd3-48785316ff99/2026-09-29T11-08-40-924Z_01a0ecda-3e5c-7616-9cfc-5d38f38077fa.jsonl:24`）。#427 又把消费清单写入 E packet：先 cherry-pick 原语、排序管线使用单访问接缝、补 RT canonical 与公式值 SUM/排序用例，并以列索引解析重复/非单射显示表头（`work/native-homes/pi-deepseek-fast-01a0ece2-ac13-7e81-9cbd-ac6d16395091/2026-09-29T11-17-55-541Z_01a0ece2-b4d5-723f-81cc-5cd1923d24e2.jsonl:34`）。提交链在 #516 被明确记录为 `d89a0db`（#396 RT/#377 哨兵与显示值）→ `e64ca87`（承接原语）→ `525cd20`（#427 packet/实现落地），说明 advisor→裁决→实现消费可追踪；后续原语修订 `ed72f89` 不改变这条继承关系。

晚期第二次 advisor（索引 `evidence/subagent-calls.json:1798`，产物 `work/native-homes/pi-deepseek-fast-01a0ecd6-7bde-7c80-879e-90ac9854be86/subagent-artifacts/8edc714c-725d-43a5-bd41-15c23b2c783a_advisor_output.md:5-20`）审查已落地原语，确认与 #396 一致，并指出负数 rowMap、混合 `$` 区间属于实现加固/未规定边界；第三次 advisor（索引 `:1819`，产物 `work/native-homes/pi-deepseek-fast-01a0ecda-3772-78d0-bfd3-48785316ff99/subagent-artifacts/e18461ab-b661-4459-beb9-437e7d3fe23a_advisor_output.md:26-44,71-75`）从 REQ-5-1-1/5-3-1 的可观测值出发，支持显示值 + `valueFor` 单点访问器和字面量结果表，但保留“harness 是否主动造公式”与 `parseable numbers` 的替代解释。完整 181 次索引只见 1 次 explorer（`2026-09-29T07:25:19Z`，索引项 79）且无 executor；因此旧报告的“无 executor transcript”必须理解为旧截点资料判断，晚期也没有索引可指向独立 executor，而不是把 PR owner 的实际实现/验收抹去。
