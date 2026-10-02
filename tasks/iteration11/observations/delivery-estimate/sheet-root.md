- 权威决定与当前判断：本正文（D1–D3、种子方案、技术方案、未决问题）；变化时在原处更新，不另建副本。
- 负责人与协调结构：comment #2（thread 2）；进展核查回复：comment #5（thread 4）。
- 共享契约：v1 正文见 comment #1；v1.1（索引 0 基、updatedAt 语义、定位纪律、粘贴扩张归 D、better-sqlite3 锁 12.6.2）见 thread 1 comment #12；v1.2（默认结构 9×26 → 6×26）见 comment #15；**v1.3（A-1 导入端点+解析语义四条、A-2 尺寸三路径、A-3 显示值接缝不变式、A-4 Y-min 导入足迹下限+空文件优先级、B-1/B-2/B-3 结构端点与选区两道门、尺寸上限非全局、state 端点不纳入快照集合）见 comment #51 + #54 + #57 + #60 + #65（末换行）+ #69（helper 定稿）+ #73（多缺陷优先级微差记录）**；**v1.4（C-1：公式引擎四接口 + `bounds`=目标表结构、C-1a 复制越界整式塌缩 `=#REF!` vs 结构删除按引用替换的不对称义务、C-1b 绝对引用随结构平移+三条边界语义、`ranges.js`→`shared/a1.js` 再导出契约与事务内接缝、构建形态 (E) allowJs + 独立 shared program 双向静态门（门放置在 SKIP_FRONTEND_BUILD 块外、include 双项防假绿，#129 + #135）、evaluate 可选 bounds 窄化（#124/#126/#135）、场景文本损坏复议条款）见 comment #109 + #110/#111/#115（消费方确认）+ #114/#118/#121/#122（构建实测）+ #128（裁定）+ #135（增量确认）+ #150（D-C14 门落地独立复核）**，以 thread 1 时序最末裁定为最新增量权威；**v1.4 补充增量（REQ-3-2-1 cut/move 语义）：被移动块内公式 raw 文本不变、仅重算，引用偏移重写与塌缩仅适用 copy 路径，悬空引用按空单元格规则求值（显示 0，不引入新错误值语义）**见 thread 2 comment #212/#214/#216（根侧 advisor 咨询后裁定）；引擎实测期望值与复现脚本（D 的 e2e 判据来源，`run.sh <worktree>` 可重跑）：#213 interface-probe-a592c3e（copy/结构重写各期望串，含 `=#REF!` 塌缩与 `$` 平移）、#217 move-dangling-probe-a592c3e（move 悬空引用求值表），留档 braid-state/evidence/issue-5-c/。；**v1.5（D-1 paste 端点：`POST .../worksheets/:wid/paste`，单事务内 尾扩张→validation gate→整批写入→touchWorkbook、返回整快照；结构语义两分=位移型归 B 端点唯一入口、增长型归 paste 事务内且必须裸 UPDATE 行列数；copy 路径 bounds 取扩张后结构+区分用例；paste 不设应用层尺寸上限=② 显式裁定）**见 comment #218（提案）+ #222/#224/#225/#229（A/B/C/基础层对账）+ #232（裁定）+ #231（上限口径更正）+ #238（增补）+ #235（尾扩张“空转”前提更正→禁调为硬约束，判据绑定 `shared/formula.js` sha256 `d445f268…` 与 braid-state/evidence/issue-5-c/ 的四个 probe 目录） + #242（硬约束定稿：尾扩张必须是裸 `UPDATE row_count/col_count`，成功路径同样会改写无关 raw） + #243（B 侧 helper+端点两层复算，evidence/issue-4-b/tail-append-ref-rewrite-a592c3e/） + #247（尾追加 raw 保持回归归 PR #11 e2e；develop 既有 `=A7` 用例为相关但**非等价覆盖**，未覆盖前随 E 批次回归点 ② 兜底，更正见 #259 及 evidence/issue-4-b/delete-shrink-rollback-ref-rewrite-a592c3e/） + #248（基础层平台入口嵌套事务+裸扩张探针，evidence/pr-2-base/nested-tx-and-bare-expansion-probe-a592c3e/；README 锚点精确为 `:56-57` 与 `:88-90`，#246/#252/#254，给 PR #11 的可执行改写点见 Issue #3 #252）**；**v1.6（E 段：9 个新端点 sort / filter PUT+DELETE / validations POST+PUT+DELETE / pivots POST+PUT+refresh，写路径单事务+返回整快照；`findValidationViolation(db, ws, changes)` 唯一 gate，`PUT .../cells` 与 paste 事务内共用；数字文案双模板=0–100 用具体句 `Please enter a number from 0 to 100`、其余用通用句 `Please enter a number between <min> and <max>`（未决 ① 关闭）；pivot 空 `source_range` 改判=不删 pivot 行、**写哨兵空串 `''`**+`stale=1`、判据 `parseA1Range(source_range)===null` 单调无别名、失效路径 409+`Pivot field is no longer available. Select a new field.`、撤销经 state 逐字往返自愈（方向 #363 批准、写法按 #375 修订；别名分支反例 #369/#355/#356，B #385 接受，基础层 schema 实测 `NOT NULL` 禁 `null`），develop 无该分支既有覆盖 → **PR #12 必须自带新用例**；配套 `paste.test.js` mock 包装器改全参转发；改动点全部归 PR #12）见 comment #332（提案）+ #334/#341（基础层核对）+ #339（更正）+ #345（B 接受）+ #350（D 包装器事实）+ **#363（根侧 v1.6 裁定）** + #369/#374/#375/#376（§3 哨兵修订链）+ #378（冻结解除）+ #385（B 终态接受）+ #386（基础层 schema 核实）+ **#397（根侧 §3 终裁：哨兵形态）**；**v1.6 补充（E-D3 排序公式语义改判 RT）**：排序按行置换改写矩形内引用（改写充要条件=被引格行列都在矩形内、`$` 随行平移、矩形外不动、无塌缩分支），共享原语 `rewriteRefsOnRowPermutation` 由 C 方在 PR #12 提供、排序管线单函数接缝为硬性义务、canonical 场景用例必做——见 Issue #7 #365/#368/#391（反例+独立咨询）+ #396（E 裁定）+ **#406（根侧批准）**；取值层终裁（排序键/透视汇总=**显示值**，后端 `valueFor` 单点访问器，更正 #406 §3① 的 raw 登记）与 README A-3 段（`README.md:98-101`）归属 PR #12 同批（兜底 A 窄 PR）见 **#428**。
- 环境证据：comment #3 —— better-sqlite3 在平台 Node 20.19.3 入口下兼容，留档 /tmp/sqlite-probe；13.x 不兼容证据见 PR #2（负责人实测）；渲染预算实测（≈0.10ms/单元格）见 comment #53，/tmp/pr2-render-probe.log（"尺寸上限非全局"裁定的依据）。
- 进度快照（随核查更新，历史核查不在此堆积）：**develop 消费基线 = `4e1a7bc`**（批次 3 合入后的共享实现状态，含 A 导入导出、B 结构端点、C 公式引擎、D paste 端点与撤销/重做）。各批次验收与合并记录：
  - 基础 PR #2：合入 `698afd2`（应用代码 `0a08fdd`），验收记录 PR #2 thread 10 comment #22，合入完整性 comment #23；PR 冻结于 `c344b3b`（负责人复核 comment #72）。证据：平台路径 /tmp/pr2-platform-path-fresh2.log（EXIT=0）、pnpm 全新副本 /tmp/pr2-pnpm-fresh.log + /tmp/pr2-pnpm-fresh-tests.log、Playwright 冒烟 3 passed（/tmp/f26-asqug4b2/service-check-ikzuhmb1）。契约 v1.2 随合入成为消费基线。
  - #4（B，PR #9 → @glm-4/@deepseek-6）：合入 `15abbf6`（候选 app 代码 `014d7ed`），验收记录 Issue #4 thread 41，偏离项 1–5 全部接受（合入回执 thread 1 comment #79）。共享校验 helper `assertWorksheetStateValid` 进入 develop。遗留回归：公式引用重写随 C、pivot 约束/Refresh 回归随 E；pivot source_range 收缩至空删除 pivot 行为 E 合入时核对点。
  - #3（A，PR #8 → @deepseek-3/@deepseek-5）：合入 `e63efc6`（候选 `a23af5a` = v1.3 Y-min 补齐 `559a0bd` + rebase/helper 切换 055fdaa + 漂移接入 16b94d8），根侧独立复核合并树与候选逐字节一致（`a3ae41bf`）；验收记录 Issue #3 thread 27 comment #81/#88、PR 侧 thread 63 comment #90。**#3 已关闭**（含 #60 helper 切换关闭前提：develop 为共享 helper 单一实现）。已知边界随契约保持可见：A-5 宽松解析、足迹静态、导入无应用层尺寸上限（#54）。
- **批次 2（C 公式引擎）完成**：#5 → Issue 侧 @deepseek-7（设计定稿 Issue #5 comment #107），实现 **PR #10**（负责人 @deepseek-8，head `c-issue-5-formula-engine` @ `05b7446`）。收尾项 ①（D-C14 静态门：SKIP_FRONTEND_BUILD 块外、include 双项、正反探针）②（深嵌套防护，≈127 层已记录边界）③（e2e 越界单格/依赖更新两条）④（绝对引用插/删行回归）全部落地并经 Issue 侧独立复核（PR #10 comment #158/#159：vitest frontend 116 / backend 105、完整 e2e 35 passed 含 A-3 接缝翻转与结构位移全套）；cold 平台路径 PASS/EXIT=0（Node 20.19.3 逐目录 install/build/start，日志 /tmp/f26-lzle9d69/platform-path-cold-05b7446-rerun.log）。@deepseek-7 按 Issue #5 正文 + 契约 v1.4 验收合并（`--match-head-commit 05b7446` → merge `a592c3e`）；根侧（@glm-9）复核 `origin/develop^{tree}` = `05b7446^{tree}` 逐字节一致。B 回归点 ① 由 @deepseek-6 首手浏览器内 e2e 复跑 35 passed 结案（Issue #4 thread 41 comment #187，证据 braid-state/evidence/issue-4-regress-01/）。未决 ① 已随批次 3 收口：REQ-4-1-2 / REQ-4-2-1 两条在合入树 `4e1a7bc` 首手成立（comment #306，证据 braid-state/evidence/issue-5-c/develop-4e1a7bc/，46 passed），**#5 已关闭**（关闭记录含残余假设 A-C1…A-C6 保持可见）。
- **批次 3（D 范围编辑与撤销重做）完成**：#6 → Issue 侧 @glm-10（设计定稿 D-D1..D-D4；cut/move 语义裁定 #216，D-D4 无切换分支），实现 **PR #11**（负责人 @deepseek-11）。交付：paste 端点（契约 v1.5 全套：单事务裸 UPDATE 尾扩张→gate→写入→整快照）、README 两处窄改、前端 TSV/范围编辑/撤销重做、#247 §1 尾扩张 raw 保持 e2e。验收链：D 两轮全量检查（46 passed）、@glm-10 独立复跑 + 缺口把关（#291/#294）、C 侧两条首手复核（#293/#296）、接口实现方确认（#298）；根侧（@glm-9）树完整性核对 `origin/develop` 应用树 = 被验候选 `517384b` 逐字节一致（根侧核对 Issue #6 comment #304）。merge `--match-head-commit 5b3a514` → `4e1a7bc`。D/E 接缝裁定（undo 恢复 pivot-result validity、不恢复结果表物化格）见 Issue #6 comment #303。**#6 已关闭**。
- **批次 4 进行中**：#7（E 排序/筛选/验证/透视）Issue 侧 @deepseek-12 设计定稿（Issue #7 comment #331，E-D1…E-D10 + 验收方案），实现 **PR #12**（负责人 @deepseek-13，head `e-issue-7-data-tools` @ `42f9c5b`（已承接原语修订 `ed72f89`，`shared/formula.js` = `9ab0559a…`；负责人在该 head 上跑全量检查中，#488）：sort/filter/validation/pivot 端点与纯函数、前端 Data 菜单/对话框/隐藏行控件、`resolvePivotField`+`valueFor` 取值单点、README API 表 9 行 + A-3 段替换均已落地；packet 回填随实现提交进行）。契约 v1.6 已裁定（#363，§3 写法经 #397 终裁修订为哨兵形态）：端点面、gate 扩签名 + 文案双模板、pivot 空 range 改判（哨兵 `''`+`stale=1`）全部批准，改动点（store.js 空 range 两行→写哨兵、validate.js gate + 两处调用点、paste.test.js 包装器全参转发、README API 表、新用例）归 PR #12。E-D3 已改判为 RT（排序按行置换改写矩形内引用，#396 + 根侧批准 #406；推翻 #331 原读法）。C 已交付共享原语 `rewriteRefsOnRowPermutation`（`origin/c-issue-5-row-permutation @ 7ba7916`，#408/#410；基础层门覆盖探针 9/9 + GATE_EXIT=0 #412，接缝复核 PASS #456）。**该 sha 的已确认缺陷已修订（阻塞项已关闭）**：负/越界 `rowMap` 值产出不可词法化文本（`=B-1`、`=$B$-1`，#445/#447 双方独立复现；根侧裁定修复语义 = 负值/缺项同读作「不映射→不改写」，#406 §2 契约不变，锁定测试须含相对/`$`/算术/区间端点四形态）。修订提交 **`origin/c-issue-5-row-permutation @ ed72f89`** 已发布（`shared/formula.js` sha256 `9ab0559a…`，#463），根侧 #462 的验收候选阻塞项就此关闭；基础层第二来源复核通过（#461/#469：冻结门 GATE_EXIT=0、环境中立无命中、语义探针 17/17 含负/非整数/缺失 `rowMap` 7/7），C 侧差分复核通过（#472，唯一分歧仍为已记录的混合 `$` 退化构型）。PR #12 已按旧 sha cherry-pick（`e64ca87`，不回退），**`ed72f89` 已再落到 PR #12**（head `42f9c5b`，#476 §3 在途项就此关闭；C 侧 #496 预核：合入树逐字节 = e 树，`merge-tree` 无冲突）。合入 develop 后 C 侧 7 目录探针按新 `shared/formula.js` sha `9ab0559a…` 重取（#410 §3.2、#436，写者 @deepseek-8）。取值层终裁 = 显示值 + 后端 `valueFor` 单点（#428）；README A-3 段归属 PR #12 同批（#428）——**已在 `525cd20` 落地替换**（按 Issue #3 #351 §3 文本），兜底 A 窄 PR 预期不触发；A-3 段监测链已收口（#478/#481/#483/#485/#492/#493/#495）：订阅持有人与合并树只读复核 = @deepseek-3（PR #12 合入 develop 时由 E @ 通知，复核后退订），此后最后一道检查归整合 PR 门禁（#428 §3 已登记），@deepseek-5 仅作者侧兜底。E 承接转移义务：① 真 0–100 规则交付后把 D 的 mock-gate 409 原子性用例切到真规则并回归 paste 409；② D/E 接缝用例（undo → 结果表保留旧结果 → Refresh 重算或报错，裁定 #303）；③ B 回归点 ②（pivot 源约束 409 / Refresh / 空 range 哨兵形态，E 合入后由 B 复核，#385 §3）。PR #12 新增义务：`rewriteRefsOnRowPermutation` 共享原语（C 方提供+单测）、排序管线单函数接缝、canonical 排序公式场景用例（#406 §3）。#5/#6 已关闭；仅 #4 保持 OPEN（回归点 ② 随 E）。最终整合 PR（develop → main）在 #7 合入后组织，其判据须含 REQ-5-3-1 三类失败路径与隐藏行对导出/透视不可见性的 e2e 断言（#363 §4）。

## 需求入口

- 完整需求包：`/workspace/template/.factory26/20260929-042409-811f18d4/input/`
  - `requirements.yaml`：权威需求树（ROOT → 5 个域 → 24 个 ATOMIC 需求），每个 ATOMIC 描述精确规定了控件可访问名称、错误文案、持久化与刷新行为。
  - `reference/`：9 张参考图（Google Sheets/云端硬盘截图，中文界面），仅作布局与交互风格参考。
  - `prerequisites.md`：空文件，无额外前提。
- 范围外：分享协作、版本历史、高级样式、图表、宏、协作光标、外部 office 集成。

## 需求格式问题与处置（已核实）

- 全部场景 WHEN/THEN 的动词短语被占位符 "the requested workflow" 替换（308 处），仅 GIVEN 与场景名中的零散 token 存活。
- 机械化交叉核对：所有场景名/GIVEN 幸存 token 均能映射到对应 ATOMIC 描述的内容或为场景数据值（坐标、常量），未发现场景独有行为。
- **决定 D1**：ATOMIC 描述为验收权威；场景仅用于提取种子数据与具体值；"with concrete values `East/1200/North/800`" 是模板填充物，不作为输入要求。场景步骤时序不可恢复，按合理顺序实现并保证各失败路径幂等。

## 种子与初始状态（决定 D2）

- 场景 GIVEN 存在互斥变体（REQ-1/2/5 族、REQ-3 族 A1:B2=Item/Qty、REQ-4 族 A1=2/B1=3），单一静态种子无法同时满足。交付**最大一致子集**：
  - 工作簿 `Q3 Sales`；Sheet1 = `A1:C4`：表头 `Region/Sales/Status`，行 `East/1200/Open`、`North/800/Closed`、`South/700/Open`；`A5:C6` 属于场景可引用范围但内容为空。
  - Sheet2 = 空白工作表（满足 REQ-2 族 "with Sheet1 and Sheet2"）。
- 种子在应用正常启动时幂等准备：只补缺失、不覆盖已有用户数据；不提供重置端点。REQ-3/4 场景数据由验收脚本经可见控件录入。
- 交付环境：Node 20.19.3（平台入口 `/usr/local/bin/node`）；平台在 frontend 执行 npm install/build，再在 backend 执行 npm install 与 `HOST=0.0.0.0 PORT=3000 npm run start`；后端同端口服务前端构建产物与 API，120 秒内启动。

## 技术方案（决定 D3）

- 前端：Vite + React + TypeScript + UnoCSS；后端：Node.js + Express + better-sqlite3（SQLite，事务写入，可重复迁移）。pnpm 开发、提交 pnpm-lock.yaml，保持平台逐目录 npm 兼容。
- **公式引擎与网格自研**，不使用 Handsontable/HyperFormula：商业/双许可不适合交付物，且 Handsontable 虚拟化渲染与"区域外每个 gridcell 暴露 aria-selected=false"的精确断言冲突。
- 引擎范围：算术、括号、一元负号、A1 相对/绝对引用、连续区间、SUM/AVERAGE/COUNT/MIN/MAX（大小写不敏感、空单元格不计为零）、依赖图拓扑重算、直接/间接循环引用 → `#REF!`、错误值 `#DIV/0!`/`#REF!`/`#NAME?`/`#ERROR!`、复制偏移与行列插入删除的引用重写（越界 → `#REF!`）。公式存原文串，加载时重算。规模按 800–1500 行 + 单测排期，引用重写为最大技术风险项，先行单测。
- 编辑器 URL：`/workbook/:id`（"stable workbook state" 入口）；首页 `/`。
- 撤销/重做仅会话内有效：按"工作表状态快照"（客户端内存）实现，不落库、不要求重开后保留历史。

## 共享契约

数据模型、API 面、ARIA/可访问名称约定、持久化清单见本 Issue 契约评论（v1 → v1.6 全部增量见顶部「共享契约」指针条；thread 1 时序最末增量 #406 为最新权威（v1.6 §3 写法链 #375/#397），取值层终裁（排序键/透视=显示值、后端 `valueFor` 单点）见 #428）。develop 当前状态（`4e1a7bc`，批次 3 合入后）即为各业务子 Issue 的消费基线；消费者按契约继续，不以旧分支自检推翻。

## 子 Issue 拆分与依赖

- #3 A 工作簿生命周期与 CSV（REQ-1-2-1、1-2-2、1-3-1、1-3-2）— 依赖基础【已指派 @deepseek-3】
- #4 B 工作表与行列结构（REQ-2-1-1…2-1-4、2-2-1、2-2-2）— 依赖基础【已指派 @glm-4】
- #5 C 公式引擎与计算（REQ-4-1-1、4-1-2、4-2-1、4-2-2）— 依赖基础【已关闭：PR #10 合入 `a592c3e`，未决 ① 随批次 3 收口（见进度快照）】
- #6 D 范围编辑与撤销重做（REQ-3-1-2、3-1-3、3-2-1、3-2-2）— 依赖 C、B【已关闭：PR #11 合入 `4e1a7bc`，D/E 接缝裁定见 Issue #6 comment #303】
- #7 E 排序/筛选/验证/透视（REQ-5-1-1、5-1-2、5-2-1、5-3-1）— 依赖 C、B、D【Issue 侧 @deepseek-12 设计定稿（comment #331）；实现 PR #12 @deepseek-13 进行中；契约 v1.6 已批准（#363）】
- 最终整合 PR（develop → main）：在最终候选上执行覆盖全部需求范围的 Playwright 自动化验收，修复失败并复验后合并交付。

## 重要假设与未决问题

- 验收 harness 的种子重置机制未知；按"不依赖任何重置端点、种子幂等"实现（已记录为风险）。
- 筛选 range 内部插入行时 range 是否扩张：按 Sheets 惯例裁定"内部插入扩张、边界外插入不扩"，已写入契约。
- 参考图与需求文本不一致处（如首页无 "New blank workbook" 按钮、界面为中文）：以需求文本的英文可访问名称为权威，参考图仅决定布局与视觉风格。
- 允许同名工作簿 + "失败时无该名链接"断言在同名先成功后失败的跨用例下会误挂（v1.3 A-1 残余风险，整合 PR 用例用不同文件名规避）。


sub-issue: #3 [CLOSED] 子 Issue A：工作簿生命周期与 CSV 交换（REQ-1-2-1/1-2-2/1-3-1/1-3-2）
sub-issue: #4 [OPEN] 子 Issue B：工作表与行列结构（REQ-2-*）
sub-issue: #5 [OPEN] 子 Issue C：公式引擎与计算（REQ-4-*）
sub-issue: #6 [OPEN] 子 Issue D：范围编辑与撤销重做（REQ-3-1-2/3-1-3/3-2-1/3-2-2）
sub-issue: #7 [OPEN] 子 Issue E：数据组织与分析（REQ-5-*）
PR: #2 [MERGED] 基础 PR：共享架构、脚手架与开发反馈设施

sub-issue: #3 [CLOSED] 子 Issue A：工作簿生命周期与 CSV 交换（REQ-1-2-1/1-2-2/1-3-1/1-3-2）
sub-issue: #4 [OPEN] 子 Issue B：工作表与行列结构（REQ-2-*）
sub-issue: #5 [OPEN] 子 Issue C：公式引擎与计算（REQ-4-*）
sub-issue: #6 [OPEN] 子 Issue D：范围编辑与撤销重做（REQ-3-1-2/3-1-3/3-2-1/3-2-2）
sub-issue: #7 [OPEN] 子 Issue E：数据组织与分析（REQ-5-*）
PR: #2 [MERGED] 基础 PR：共享架构、脚手架与开发反馈设施



