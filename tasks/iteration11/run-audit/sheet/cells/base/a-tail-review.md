# A 侧视图尾段复核：S41、S44、S45

## 阅读范围与证据边界

本次只读了 `cells/a/views_unique/` 的三个尾段视图，没有修改 `cells/a`、源码或运行任何测试。视图中出现的 `[DUPLICATES: ...]` 只表示精确重复材料按 `duplicate-lines.json` 指向前源；本报告引用前源已有审计，不把重复标记或索引当作新事实。

| 视图 | 原生会话 ID | 原生源 | 视图物理行 | 原生事件段 |
|---|---|---|---:|---:|
| S41 | `01a0ebf3-874b-77d8-96af-0dfa7c289724` | `work/native-homes/pi-deepseek-fast-01a0ebf2-17bc-7491-8e1b-ca54f0fd9ba9/2026-09-29T06-55-07-355Z_01a0ebf2-1a5b-723d-a39f-49fb8a42d849.jsonl` | 1–2596 | L1–L199 |
| S44 | `01a0ec0e-5e87-7692-b269-ff14128c005b` | `work/native-homes/pi-deepseek-fast-01a0ec0e-54da-7713-b39b-621d17719ddd/2026-09-29T07-25-59-815Z_01a0ec0e-5e87-7692-b269-ff14128c005b.jsonl` | 1–733 | L1–L66 |
| S45 | `01a0ec0e-ed93-75a7-926a-751dadb16aa6` | `work/native-homes/pi-deepseek-fast-01a0ec0e-e4da-72e1-b9ba-45209330529f/2026-09-29T07-26-36-435Z_01a0ec0e-ed93-75a7-926a-751dadb16aa6.jsonl` | 1–584 | L1–L65 |

三个视图均无本次阅读造成的未读或工具输出截断。视图本身保留了大量重复材料的省略标记；这些省略内容按前源处理，不重复计入新的独立阅读量。

## 按过程复核

### 1. S41：Issue #3 / PR #8 收口与 C-1 契约交接

**原文位置 → 决定/动作 → 后果。**

- S41:L12–L34 处理 PR #8 合入后的两处正文修订：`used range` 改为 `max(非空包围盒, 静态足迹)`，权威列表补入 v1.3 的 A-1/A-2/A-3/A-4 入口。随后 `S41.txt` 视图物理行 257–315 记录了对合入树 `origin/develop=e63efc6` 的只读核对：`csvExport.ts` 的足迹下界和空文件判据成立，A 分支树与 develop 字节一致，`PRE-C TRANSITION` 仍是过渡断言。动作是文档窄改和 owner 侧核实，未改提交；后果是 A 的已交付边界与整合门禁仍可追溯，Issue #3 继续 CLOSED。
- `S41.txt` 视图物理行 361–380 发布 C-1 的共享契约：`evaluate`、`rewriteRefsOnCopy(..., bounds)`、`rewriteRefsOnInsertDelete`、`isNumericCellValue`；`bounds` 必须来自目标表的 `row_count/col_count`，不能使用 A 的 `min_rows/min_cols` 足迹。复制越界要求公式栏整式变成 `=#REF!`，结构删除则按引用替换；绝对引用随结构变更平移；`backend/src/ranges.js` 迁移到共享实现并保留兼容再导出。这里明确 B 的端点回归随 C/PR #10，B 不新增实现。
- `S41.txt` 视图物理行 386–413 先做 A-3/A-4 的接口兼容性判断，随后视图物理行 518–531 形成 owner 侧确认：C 的 `evaluate` 返回 `row:col → 显示文本` 与 A 的 `cellKey`/显示接缝兼容，错误值也走网格和 CSV 的显示路径，FormulaBar/内联编辑继续用 `raw`。这是一项契约核对与交接动作，不是 A 侧新代码；责任边界落在 C 的 PR #10 和最终整合 PR。
- `S41.txt` 视图物理行 1967–1990 观察到 C 分支已把公式导出过渡断言翻到 `2`/`2,plain`，但当时仍把 develop 的过渡状态和整合复跑作为后续条件。视图物理行 2020–2128 记录 v1.4/D-C14：独立 shared 静态门归 PR #10，浏览器内真实 e2e 仍必须执行；A、B 不再开并行基础层窄 PR。视图物理行 2158–2195 再次把 `bounds=结构`、共享静态门和浏览器 e2e 双门写入交接。
- `S41.txt` 视图物理行 2352–2405 的 A-3 复核把具体结果写入 Issue #3 comment #131，并随后更新 Issue 正文：C 分支接缝已改为 `evaluate(...,{rowCount,colCount})`，网格/导出消费者保持不变，FormulaBar/内联编辑保留 `raw`，过渡用例已变为 `2`/`2,plain`；develop 尚未合入，整合 PR 的动作收窄为最终候选上的浏览器复跑。视图物理行 2453–2593 显示正文核对和窄改已落地，保留 C 尚未合入这一未决事实。

**原因与竞争解释。** 原先“整合 PR 翻转断言”的文字是 A 交付时的时序描述；C 分支先完成翻转后，若继续按“整合 PR 再翻转”理解，会把已经完成的实现动作重复分配给整合者。因此 S41 的修订把职责改为“C 实现并翻转，整合 PR 在最终候选浏览器内复跑”，同时保留 develop 尚未改变的事实。shared 静态门是 Node-only 方向的补充检查，不能替代浏览器运行时门。

**下一轮证据。** 验收应在 C 合入后的最终候选上复跑同一用例，观察网格 `2` 和导出 `2,plain`，并同时取得 v1.4 §5 的 shared 静态门结果。A 侧不再承担实现或另开基础层门禁。

### 2. S44：A 侧复核 C 接缝、PR 正文和 moving-head 锚点

- S44:L4 直接呈现 Issue #3 comment #131 的代码级复核：C 的 `cellDisplay.ts` 调用 `evaluate(worksheet.cells,{rowCount,colCount})`，错误值走同一显示路径；`WorkbookEditor → Grid` 与 `WorkbookToolbar → worksheetToCsv` 接线未变；FormulaBar/内联编辑仍读 `raw`；C 分支 e2e 断言已为 `2`/`2,plain`。同一段明确 PR #10 仍 OPEN，develop `e63efc6` 仍为过渡实现，所以 A 的最终前提在 develop 上没有消失。
- S44:L12–L14 的实际树核对与上项一致：develop 仍是恒等接缝，C 分支已调用 `evaluate`，C 的 e2e 翻转在 L382/L384 可见。S44:L40–L53 随 C head 从 `c340e2e` 前进到 `d42be13`，再次核对 `cellDisplay.ts` 和 `2,plain`；`S44.txt` 视图物理行 566–614 因此把 PR #8 正文锚点改成“翻转首见于 `c340e2e`，后续 `d42be13` 复核仍成立”，并在 comment #136 的回复中留下更正。
- `S44.txt` 视图物理行 635–731 处理通知和时间线混淆：PR #8 的正文编辑、Issue #3 的正文更新、comment #136/#137 都能在有限分页的时间线中对应；A 分支仍 `a23af5a`、无新提交，Issue #3 CLOSED。这里的实际动作是窄改文档并校正 moving-head 证据锚点，不是重新实现或重新翻转 e2e。

### 3. S45：v1.4 合约确认、正文窄改与 gate 归属

- S45:L35–L39 核对负责人和当前树：Issue #5 负责人为 `@deepseek-7`，实现 PR #10 为 `@deepseek-8`，develop `e63efc6`，C head `d42be13`。`S45.txt` 视图物理行 331–344 读取 v1.4 comment #135 的约束：生产消费者必须传结构 `{rowCount,colCount}`；shared 静态门的 `include` 必须同时覆盖 `*.js` 和 `*.d.ts`；正向/负向探针都应有明确错误和清零退出；浏览器 e2e 仍是运行时证据。
- `S45.txt` 视图物理行 343–387 的实际核对再次得到 develop 过渡断言和 C 分支翻转断言。视图物理行 398–419 判断 A 侧没有新的实现动作；视图物理行 423–471 只修正 Issue #3 正文中绑定旧 head 的句子；视图物理行 518–582 留下窄改依据和最终未决项：C 合入后整合 PR 复跑该 e2e，用例名是稳定锚点，A 侧其他边界保持不变。

## 关键判断：A 是否亲自执行了门拦截实验

结论：**S44/S45 没有 A 亲自执行 shared 静态门/Node 全局拦截探针的证据。**

- S44:L4 的“代码级复核”是对 C 分支文件、diff 和 e2e 断言的只读检查；不是 `tsc` 探针或浏览器门拦截实验。
- `S45.txt` 视图物理行 331–344 只是读取并采用 v1.4 comment #135 的契约；视图物理行 343–387 的命令只核对分支、文件和断言；没有 A 发起的 probe 命令或 probe tool result。
- S41:L154 的 `“我侧独立复现”` 属于 comment #125 的作者 `@deepseek-7`，其内容引用 `/tmp/ds7-shared-gate-probe.log`；这是 C owner 的实测结果在 A 会话中被读取，不应改写为 A 的实验。S41 中 A 说“my #121 proposal”表示提出/转交建议，不等于本尾段有 A 的执行证据。

因此，对“门放置、include 双项、正/负向探针、运行时 e2e 互补”的结论，责任链应写成：`#121/#122 的实测与 #125 的独立复现 → v1.4/#135 裁定 → PR #10 承担 shared 门；整合 PR 承担最终浏览器复跑`。A 的贡献是契约接缝核对、迁移边界和最终 gate 入口确认。

## 影响、归属与下一轮证据

1. **共享契约**：`bounds` 是结构事实，足迹只服务导出下界；`evaluate` 显示值接缝只供网格/CSV，raw 仍归 FormulaBar/内联编辑。归属为 C/PR #10 实现，B/D 按各自消费端回归，A 只保留边界与门禁入口。
2. **验收初始条件/候选一致性**：develop=`e63efc6` 仍代表 A 交付的过渡候选；C head=`d42be13` 只证明分支上的翻转。最终结论不能用 C 分支结果替代合入候选结果，必须在最终候选浏览器内复跑，并附 shared 静态门结果。
3. **重复检查与注意力成本**：S44/S45 多次因 C head 前进、正文通知和时间线默认分页再次核对同一事实。moving-head 锚点的窄改有实际交接价值；重复读取同一翻转、重复通知和无待办回执没有新增产品证据，应由稳定 commit 首见点 + 当前复核点 + 用例名收敛。
4. **修复边界**：没有证据要求 A 改源码或再开基础层窄 PR。若最终候选缺 shared 门，PR #10 负责；若浏览器用例在合入候选失败，整合 PR 负责定位/修复或回退 C 合入；若仅是 A 文档锚点过时，A owner 负责窄改并留更正依据。
