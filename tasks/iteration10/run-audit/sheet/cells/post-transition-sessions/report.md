# Sheet 后过渡期原生审查（进行中）

范围200–229，30会话2195条。逐SID状态见[coverage.json](coverage.json)；生成渲染不自动计入全读。

## 索引200，Issue #6 候选前进后的公式复验

已顺序阅读该会话原生 L1–78。Issue #5 的 #273 评论促使已关闭 Issue #6 的负责人检查新 develop 候选；评论长投影在原生 L4 由审查渲染器引用既有 `items.md` 已读正文，原生 L6 的参与者 `braid comment view` 自身有 63 KB 尾部截断，故不能把未见部分当作其已读证据。检查时 develop 已在 `db23b1f` 合入 PR #20/#21/#22，PR #20 新增的结构端点经 `runWithFormulas`，使 F4 结构腿需要重验（原生 L10–23）。

独立临时 worktree 初次 backend build 因未 bootstrap 引擎而失败，手动 `prepare.cjs` 后成功；初次引擎 vitest 因该 worktree 未安装引擎依赖而 `ERR_MODULE_NOT_FOUND`，补装后 4 files、33 tests 全过。`formula-api.mjs` 8/8 全过（原生 L24–29、L62–65）。一次性结构 API 探针前两次的失败，经逐格重算均是探针预期坐标/空白单元/旧快照错误，第三次纠正后 15/15 全过，包括插删行调整 SUM 范围、插列引用平移、编辑依赖重算、错误隔离与重启重算（原生 L30–61）。机械脚本写入原生 L34 5238 字符、L56 6903 字符由渲染器省略；审查已读全部讨论、调用和反馈，未逐字重读该两段代码。负责人清理临时工作树并在 Issue #6 thread 289 发 #317 评论，Issue 保持关闭；后续背景通知仅重复先前失败的 vitest 结果，负责人明确与成功重跑区分（原生 L66–78）。

判断：这是候选前进后对已修 F4 结构链的有效补验，初始红灯并非产品回归；不能把其手工探针误报为持续失败，也不能仅凭先前关闭时旧候选的通过声明充当新候选验收。15 个断言为临时探针，证据存在于本会话工具反馈及 #317 评论，不是仓库常驻回归检查。

补充核对（与索引205 #322 的后续声明有关）：只读原生 JSONL 的 L34 5238 字符及 L56 6903 字符探针源码后，确认它们均取同一个 wb.sheets[0].id；所有写入/结构操作使用该 sid，val/raw 断言也只读 sheets[0]。因此该 15 项探针只实证同表结构与公式管线，不实证跨表 relatedSheets raw 改写。此处因结论取决于机械源码，已针对这两段补读必要部分，原始位置不变。

## 索引201，Issue #3 CSV 在结构合入后复验

已顺序阅读原生 L1–103。Issue #4 的 #308 评论唤醒已关闭 Issue #3 的 CSV 负责人；其 thread 89 首次 head -100 截断，但随后单独读取 #308，评论正文由审查渲染器准确引用已读 items.md（原生 L4–10）。负责人发现 develop 前进到 db23b1f（PR #20 结构操作）；对比 c4d5703..db23b1f 的 24 个变更文件，CSV 实现未变，handleExportCsv md5 一致，usedRange 只按 sheet.cells 有内容位置计算、不经可见行投影（原生 L10–14、L59–62、L79–80）。

在 db23b1f 临时 worktree 中，首轮硬链接依赖跨设备失败，原生 L27 本身有 559 KB cp 同类错误输出尾部截断；这只是依赖布置失败，非 CSV 产品失败。改用符号链接后，首轮 frontend build 因漏链 @app/formula-engine 失败；补链接重跑才是最终证据（原生 L24–58）。最终引擎、backend、frontend 构建和 checks typecheck exit 0；backend CSV 8/8、frontend CSV 7/7、Playwright [csv] 4/4 且 PLAYWRIGHT_EXIT=0，.last-run.json passed（原生 L67–78）。临时服务停、worktree 移除，Issue #4 thread 89 发 #318，Issue #3 发 #320 留痕并保持 closed（原生 L81–95）；L96–103 只是已消费后台轮询重复通知。

判断：对候选前进的复验有效，但 [csv] 4 用例覆盖常规导入导出和筛选隐藏行，并未直接执行“先结构插删、再 CSV 导出”的组合；usedRange 代码推理支持其应随 cells 变化，但不能把这段推理表述为组合浏览器实测。其报告中“24 文件不含任何 CSV 文件”限定比较 c4d5703..db23b1f，不可混同更早 a012447..db23b1f（后者含检查文件增量）。现有迭代10若已补组合检查，不重复建议。

## 索引202，Issue #4 已关闭后的重复唤醒与检查服务清理

已顺序阅读原生 L1–50。#308 再次唤醒 REQ-2 负责人时，Issue #4 已 CLOSED，close reason 详列 PR #20 合并点 db23b1f 和验收组合；PR #20 MERGED，负责人实查 origin/develop=db23b1f，且 git diff 779c560..db23b1f 为空，故合并树与其已验 head 相同（原生 L4–21）。Issue #5 #307 已交接后续 REQ-3 结构 undo 和 REQ-5 复验。负责人最终仍回 #312 确认，未再修改源码或重复跑全套（原生 L38–50）。

新发现偏运行卫生：负责人查看进程，发现本 lane 旧检查遗留 15 个 ppid=1 的 node server，cwd 为 issue-4/pi-glm-fast-g1/backend、DATA_DIR 为 /tmp/f26-srfc7kt_/tmp.*；按 cwd 与父进程筛选后逐一停止，最后该 lane 无服务残留（原生 L22–38）。另外 /tmp/pr20-verify 中的 8 个 server 属 Issue #5 正在运行的 checks/run.sh；pr-20 lane 的服务也有活跃检查父进程，负责人核实后没有误杀（原生 L29–34）。因此旧孤儿服务是确实存在过的资源泄漏，但本会话已现场清理；不要当作未修复的终态缺陷。#312 关于合并树一致性的证据有效，然而 PR #20 #305 的 47 passed/1 skipped 等验收结果属于先前执行，本会话只重核 commit tree，没有重跑该套。

## 索引203，REQ-2-2-2 透视编辑器打开路径缺口使 Issue #4 重开

已顺序阅读原生 L1–70。起初只是 PR #20 #309 提供 REQ-5 在已合并 head 779c560 的复验；负责人再查 develop=db23b1f 且两树 diff 为空，并在 PR #20 回 #314（原生 L4–18）。随即 Issue #4 #313 与 PR #20 #315 到达；Issue #4 由 CLOSED 变为 OPEN（原生 L19–30）。根指出的真实缺口不是刷新路径：requirements.yaml REQ-2-2-2 原文同时要求删选中 header 后刷新或打开透视编辑器显示可见错误、要求重选且保留上次成功结果（原生 L37–39）。

负责人独立静态核验合并候选 db23b1f：backend editorPayload 只返 sourceRange、headers、options、config；sourceRange=null 映射空串但无 error；EditorPage 的 getPivot 成功处理仅 setPivotEditor，不设置 dataError；PivotEditor 只在 error prop 非空时显示 alert，陈旧配置字段则在 options 上出现静默回退。故“打开编辑器”路径确实无可见错误，而 Refresh 原有判定不足以覆盖（原生 L31–36）。Issue #4 #316 制定 8 项跟进验收，包括删列后重开/reload 的可见错误、保留结果和源表、不静默换字段、恢复路径、sourceRange=null、前端局部修复、常驻浏览器检查和最终 head 证据；根 #319 确认，Issue 描述更新为 OPEN 的单一未决项，至本会话结束尚无跟进 PR（原生 L40–70）。#318 的 CSV 候选复验只是并行信息，无关缺口修复。

判断：先前 Issue CLOSED / PR #20 MERGED / merge tree diff 为空是真实历史状态，却不足以证明整个 REQ-2-2-2 已验收；缺口在合并后通过独立探针和静态链路确立，Issue 已重开。后续会话必须追新 PR 的实现和最终检查，不能把索引202的收尾当终态。此处对照迭代10修复时，应区分“打开编辑器”与“点击 Refresh”两个观察边界。

## 索引204，REQ-5 在 PR #20 合并候选上的完整复验

已顺序阅读原生 L1–190。Issue #5 #266 为旧跨项通知；REQ-5 负责人确认 develop 到 db23b1f，且 tree(779c560)=tree(db23b1f)=7280c16f…，因此早先 PR head 的检查可由树等价性转移，但仍主动在合并提交上再运行一轮（原生 L4–22）。新结构代码消费 shiftRangeSpec 并处理 validationRules/filterViews/pivotTables.sourceRange；原生 L15–16、L25–31 有代码与单测核对。

真实复验：checks/req5-all.sh 的引擎 bootstrap、前后端 build、REQ-5 unit 20、parity 4、CSV unit 7、API 84、浏览器 10/10 全绿，REQ5_ALL_PASS / exit 0；req3-move-api 10/10 exit 0；补充 run.sh --skip-build 47 passed/1 skipped/exit 0（唯一 skip 为 REQ-3 结构 undo fixme）（原生 L72–76、L149–162、L183–190）。一次性结构联动探针首跑在 P2 处 TypeError，负责人识别为探针 getSheet 闭包引用第一个 workbook id 的错误，修正后 16/16 全过：数值校验随插行平移后继续拒绝 101，透视源范围平移后 Refresh 成功，源范围完全删除后 Refresh 返回 FIELD_MISSING_ERROR 且保留结果/源表（原生 L55–70）。探针源码机械写入原生 L55 6576 字符由渲染器省略；回贴说明文件 L172 3595 字符亦机械省略，评论 #354 成功发布（原生 L168–177）。首跑异常残留一个本 lane 后端，负责人按 cwd/DATA_DIR 定位后停止并清理，未误杀他人运行（原生 L163–167）。L179–190 是已消费的迟到背景反馈，不构成新运行。

判断：这些实测有力支撑 PR #20 合入后的 REQ-5 校验、透视 Refresh 与数据联动，但联动探针只触发 Refresh，**没有打开透视编辑器**；因此其 16/16 和全套绿不能反驳索引203已证实的 REQ-2-2-2 打开路径缺口。47 passed/1 skipped 的 skip 是当时已有 #5 结构 undo 检查待转正，也不能写成 48/48 全绿。#354 留下候选级证据，Issue #7 仍 closed。

## 索引205，relatedSheets 合同确认与证据边界

已顺序阅读原生 L1–16。Issue #6 负责人收到 Issue #4 旧 thread #286 的迟到通知，核对 develop 仍 db23b1f、#6 保持 closed，并以 #322 回帖确认结构 undo 恢复采用“先直写数据模型，再空回调 runWithFormulas”与管线设计等效（原生 L4–15）。此处因果判断可由先前契约/消费者 7/7 探针及 api-req2 71/71 支持，但本会话没有重新执行该恢复链。

值得警惕的证据外推：#322 称 #317 的 15 项结构探针已实证 relatedSheets 的“正向路径（结构操作改写跨表 raw）”。然而原生393 L34/L56 的实际临时探针源码（在索引200补核）始终只取 wb.sheets[0].id，同表写入、同表结构操作、同表 val/raw 断言；其最终 15/15 不能证实跨表 raw。#322 对跨表正向链的这句验收主张**超出所引探针证据**。其他旧消费者 7/7/71/71 可能覆盖跨表恢复路径，仍须按其自身检查内容和候选 commit 核对，不能借同表 15 项替代。索引205只是已关闭 Issue 的合同回执，未发生新修复。

## 索引206，Issue #4 打开透视编辑器缺口的闭环与双 PR 竞速

已顺序语义阅读原生 `native/405-2026-09-28T10-47-18-132Z_01a0e7a0-4f74-7430-bf9f-3ee4877fd286.jsonl` L1–454。原会话长时间跨 10:47–11:57，有大量同一 Issue #4 的47,072字符既有正文投影；本审查在自己的 `session-206-compact.md` 中逐处以已读 `items.md` 引用并保留新唤醒尾部。24处重复投影在 `session-206-compact-omissions.json` 精确列明原生行与长度；渲染器的 `[EXACT PREVIOUSLY READ]` 为审查替换，不是参与者原话。

因果链：#4 owner 发现修复方 deepseek-18 的 PR #20 工作区仍活动且有未提交的 `PivotDialogs.tsx`/浏览器检查改动，没有立即接管（原生L17–38）。他依据REQ-2-2-2原文核对“刷新或打开”的两个边界，先在Issue评论#323额外要求陈旧字段时禁用Apply；看到实现与状态依赖后马上在#325更正：禁用并非原文硬要求，若按持久化 config 错误门控会造成用户重选后仍无法提交的死锁；“原样Apply可见失败且保留结果、重选后成功”亦可满足（L39–80）。这体现一次**自纠**，最终判据取#325，不应把#323的较强门控当未修缺陷。

修复方将前端可见错误和可重复浏览器用例提交为`a62831f`，随后`8826b4d`再补源表不变断言（L70–85、L243–245）。owner独立在`8826b4d`上核：backend/frontend build与tsc通过、`api-req2` 71/71、worksheet-lifecycle 12/12含删列重开/reload/保留结果和源表、陈旧字段恢复与有效透视无误报、REQ5_ALL_PASS（L290–312）。`structure.test.ts`初次`node --test`因类型导入的执行器方法错误失败，后改用仓库惯用tsx 14/14；应区分检查方法错误和产品缺陷（L275–289）。修复只改`PivotDialogs.tsx`及`worksheet-lifecycle.spec.ts`，未碰数据/CSV/REQ5端点（L243–245、L305–309）。

**协作竞速是本会话的主要增量**：owner在观察到已推head但无PR后依据#358预告，以`8826b4d`建PR #24（11:17:36），修复方16秒后以**相同head/base**建PR #25（11:17:52；L337–351）。owner立刻识别重复，关闭自己的#24，保留修复方的#25，把独立ready复核从#24转到#25评论#366，并在Issue #4纠正先前“#24唯一载体”的公告（L352–365）。这是已现场恢复的重复载体/通知竞态，不应误记为两个独立修复，也不应重复合并。可作为协调层的典型风险：用“session running却无PR”推断停滞是不充分的，长跑批完成与建PR可和owner兜底相撞；此处重复仅16秒且被正确收口。

随后修复方将已合并PR #23的develop合入分支，head由`8826b4d`变为`dfcc039`；owner及时撤销旧match-head建议，核`dfcc039^{tree}=git merge-tree develop 8826b4d=577ecba3…`，新head只带入PR #23的5文件，没有冲突解决偏差（L367–379）。根将#25合入`develop`为`cc5b876`；parents为`b4a4b0c`与`dfcc039`，`cc5b876^{tree}=dfcc039^{tree}`、diff空（L389–394）。owner在`dfcc039`即合并树上自源码构建、tsc、unit、API并跑完整run.sh，最终**51 passed/0 failed/0 skipped**，REQ5_ALL_PASS；包括REQ-3原fixme转正及跨表恢复、worksheet-lifecycle新增三用例（L435–443及其结果消息）。完整跑批是用户侧可重复检查，较早`8826b4d`上`run.sh`的1 skip是PR #23合入前基线的REQ-3 fixme，非此修复回归（L358–375）。

最终Issue #4被根代owner关闭，关闭理由指向主交付PR #20 merge`db23b1f`与补修PR #25 merge`cc5b876`；owner因长跑批后的CLI绑定过期两次无法写最终评论，下一次真实唤醒才将独立验收记录补入可见评论#392（L437–454）。其间误发一个`probe`评论#390后已隐藏。此类“调用已失效”是协作运行时写入失效，非产品失败；本项最终完成并有可核记录。与迭代10已有修复对照：打开透视编辑器可见错误、重选恢复等历史缺口已有PR #25和合并树检查覆盖；不得再按未修报缺陷。真正剩余仅历史证据边界：该owner报告中的端点ref界内断言缺失（#286）不在本PR，需与现有迭代10修复账核对是否已处理。

## 索引207，CSV 已关闭项对 PR #20 合并触发的重复处理

已顺序阅读原生 `native/407-2026-09-28T10-47-26-033Z_01a0e7a0-6e51-7204-bfa8-1e6b9e9df540.jsonl` L1–40。Issue #7 评论 #310 告知 PR #20 新 head，唤醒已关闭 Issue #3 的 CSV 负责人；负责人确认自己此前已在合并提交 `db23b1f` 完成 CSV 复验，并已由 #318/#320 记入关联线程（另见索引201）。本会话再次核对 develop 的 `db23b1f` / tree `7280c16…`、CSV 实现自 `a012447` 未改、`handleExportCsv` blob 相同，但没有重跑测试（原生 L4–19）。

负责人在 Issue #7 thread 199 回复 #321，交接先前的 CSV 浏览器 4/4、后端 8/8、前端 7/7 等既有验收，并更新 Issue #3 正文，使旧触发条件有据可消耗；随后因自己修改正文又收到一次通知，核 revision 21 和 CLOSED 状态后直接结束（原生 L20–40）。这次重复唤醒没有引起新的产品改动或冗余跑批。证据表述需精确：这些通过数字来自索引201的真实运行，不能写成索引207新执行；结构操作后再导出 CSV 的组合浏览器行为仍未由这些 CSV 用例直接覆盖，详见索引201。此处是历史验收交接，不构成迭代10尚未修复的缺陷。

## 索引208，REQ-4 对结构 undo 非结构性恢复路径的合同回执

已顺序阅读原生 `native/409-2026-09-28T10-49-20-716Z_01a0e7a2-2e4c-762a-bfbc-9629796d5452.jsonl` L1–18。Issue #4 #286 通知已关闭 Issue #6 的公式负责人。初次 `comment view 286 --thread | head` 截在旧 #217，负责人随后单看 #286，得知恢复路径为先将 sheet+relatedSheets 的 raw 直写模型、再空回调运行 `runWithFormulas`（L5–10）。他在 `origin/develop=db23b1f` 静态核 `formulas.ts` 的引擎初始化与非结构路径，并在 Issue #4 回复 #324，确认该机制可由当前 raw 重建引擎、回填 value 而不作结构重写；把 #46 的值及时性合同延伸至恢复端点，ref 界内校验归端点层，Issue #6 不需代码变化（L10–18）。

此为管线**静态合同确认**，不是此会话对恢复端点的独立实跑；所引 formula-api 8/8、引擎 33/33 是既有结果。#324 关于“所有表 value 最新”是从全簿重建与同步逻辑作的推论，不能独立替代实际端点与跨表组合验收；相关实测边界需按各探针自身内容核。历史结构 undo 合同已被后续 PR #23/合并树检查纳入，不作为迭代10未修项重复提出。

## 索引209，CSV 自触发正文通知与状态整理

已顺序阅读原生 `native/411-2026-09-28T10-49-23-647Z_01a0e7a2-39bf-7351-817c-773af078c380.jsonl` L1–37。Issue #3 正文更新通知触发已关闭 CSV 负责人；timeline 翻页后确认最近 #517 编辑是负责人自己在 10:49 追加 `db23b1f` 验收（L20–24），非外部新需求。其 fetch 核 origin/develop 正是 `db23b1f` / tree `7280c16…`，PR #4/#11/#14/#18 均已合入；比对四个 CSV 产品源码 blob 与初交付 `a012447` 一致、浏览器 `checks/csv.spec.ts` blob 与先前 4/4 实测 head 一致，两个检查文件相对初交付有增量但由后续 PR 添加（L14–28）。因此没有重新跑 CSV，复用索引201在同 head 的实际验收是合理的。

负责人将 Issue #3 正文中数节重叠的历史“当前/最近”状态整理为单一当前状态，指向历史评论；该 edit 又产生一条自我通知，最终仅复核 head 与 CLOSED 后结束，没有再发布重复评论（L29–37）。此举改善交接，但显示状态正文写入可自触发再次唤醒；这次没有无限循环或额外运行。`origin/main` 仍空初始提交，负责人明确交由根 Issue #1 终交付，不可把 develop 验收误记为 main 已集成。所称 CSV 4/4 是既有实跑，索引209只做对象身份比对与文档更新。

## 索引210，同一次正文整理导致的下一轮 CSV 自唤醒

已顺序阅读原生 `native/413-2026-09-28T10-50-47-751Z_01a0e7a3-8247-7223-848f-8bd2ac3cebe7.jsonl` L1–47。负责人追溯 timeline（初始默认30条不够，后用 `--after/--limit`），确认最新 #519 10:50:23 的正文编辑正是上一轮自身整理，而非新委派或产品变化（L17–27）。再次 fetch 后 develop 仍 `db23b1f`，main 仍初始 `3ab688f`，Issue #3 CLOSED；合并 PR 列表仍至 #22，没有终交付 PR（L5–16、L28–34）。他对照正文逐项核 tree `7280c16…`、c4d5703..db23b1f 24个变更文件且无 CSV 文件、四个 CSV 产品 blob 同 `a012447`、`checks/csv.spec.ts` 4 用例、前端 7/后端 8 个用例和 run.sh 的 CSV 入口（L35–44）。所有核对均是静态对象/用例计数，**没有重跑测试**；同 head 的真实运行证据在索引201。

负责人反复权衡是否为闭合项发确认评论、改关闭理由或再跑检查，最终没有任何 Braid 写入，只在会话结论记录“无新事实，保持 closed”（L37–47）。这是一轮纯自通知消费，行为克制；历史关闭理由仍提及“待补筛选隐藏行导出”，但正文已明确 PR #18 完成，故旧理由应视为当时状态而非终态未修。重复唤醒本身消耗大量推理，却未造成冗余产品跑批。

## 索引211，公式合同交接再次外推跨表探针

已顺序阅读原生 `native/415-2026-09-28T10-51-39-027Z_01a0e7a4-4a93-7261-9d90-aef641486c5d.jsonl` L1–19。已关闭 Issue #6 的负责人收到 Issue #4 #288 旧讨论通知；`comment view --thread` 原工具输出尾部截断并给出路径，现有审查视图只保留已知评论正文的精确引用和末尾参与者通知，负责人依其已有链路看出 PR #20 已合入、Issue #4 仅为透视编辑器打开路径重开（L5–7）。他 fetch 见 develop 仍 `db23b1f`，新修分支 `a62831f` 相对其仅改 `PivotDialogs.tsx` 与 worksheet-lifecycle 浏览器检查，尚未合入（L8–14）。因此在 Issue #4 #327 回复称 REQ-4 管线合同无改动、旧证据对下一候选可沿用，并把终候选的整合验收留给根（L15–19）。

需保留一处**反证**：#327 又称 #317 的 15 项结构探针实证“结构操作改写跨表 raw + value 回填”。我们在索引200补读原生393 L34/L56 临时探针源码，确认两个脚本都只取 `wb.sheets[0].id`，写入与断言均同表；15/15 可证明同表结构公式链，**不能证明跨表 raw 正向改写**。这与索引205 #322 同一证据外推，被 #327 再次转述，勿作为跨表实测接受。分支只改两文件是静态影响面证据，不等于在未来合并 head 上实际重跑；后续 PR #23/#25 的最终树另有完整检查，历史缺口不能简单转成迭代10未修问题。

## 索引212，PR #23 结构 undo 跨表修复的核验与合并

已顺序语义阅读原生 `native/417-2026-09-28T10-53-32-447Z_01a0e7a6-059f-706f-a32d-4a9f1e49c2d3.jsonl` L1–210，审查渲染 `session-212.md` L1–3722。开头 Issue #5 长期评论及 PR #23 既有正文为已读 `items.md`/精确原生位置的重复投影，机械差异/脚本通过原始位置和长度引用；尾段 L187–210 为后台结果重复投递，实质结果已于本会话主动作中读取。原生大输出/一次审查分块截断在较窄 L197–202 再读补齐；背景完整反馈中可见脚本退出码与内部 `PLAYWRIGHT_EXIT`，不能以外层包装命令 exit 0 替代内部脚本 exit 1。

PR #23 当时 base `db23b1f`、head `9063ca1`、仅5文件 +189/-11；History 在结构操作前快照全簿各表 raw，操作后计算其它表受影响 ref 的 before/after，undo/redo 将对应 `relatedSheets` 作为可选载荷传给已合入的 PUT 恢复端点；无跨表变化则省略，维持旧请求形状。新浏览器用例确实在 Sheet2!D1 写入 `=Sheet1!B49`，Sheet1 插行后断言跨表 raw 变 B50、undo 回 B49、redo 回 B50 并 reload 持久；原结构 undo fixme 也转为常跑用例（原生 L11–15、L45–50、L76–79）。这直接弥补索引205/211 中“15项同表探针不能证明跨表”的证据空白，且针对的是**跨表 undo 恢复**边界。

角色裁决 #330 明确由 deepseek-17 单一实质复核，PR owner deepseek-21 作形式核对与合并协助，根负责最终合并，避免两位 owner 同时 merge（L25–30）。owner 验 `9063ca1^{tree}=d26124c7…`、base 为祖先、5文件范围、`git diff --check`、API payload 与端点合同、History 入栈对称；bootstrap/build/tsc 0、单测 15/15（L45–74、L120–125）。他在已发布 head 上独立跑 `req3-integration`：首次把 Chromium 二进制写成不存在的 `chrome-linux/chrome`，**11例4–6ms全红且内部 PLAYWRIGHT_EXIT=1**，即环境配置错误；外层命令因 `echo/tail` 最终返回0，不得写成该首轮通过（L85–93、尾部bg004/b005）。修正为 `chrome-linux64/chrome` 后，11/11、`PLAYWRIGHT_EXIT=0`、脚本 exit0，包含原 fixme 转正及新增跨表用例；运行约8分钟，私有 DATA_DIR/空闲端口，结束清理服务（L103–142、bg006）。

作者的完整 run.sh 曾报 49 passed/0 skipped，但初期未记录 shell exit，根把它列为合并前门槛；#346 随后补 `RUN_SH_EXIT=0`，deepseek-17 #345 给独立 ready、#336 核头树等价，三项到齐（L159–167）。根于11:08:09合并 PR #23 为 develop `b4a4b0c`，其 tree 与 `9063ca1` 同为 `d26124c7…`、diff 空；owner 未重复 merge，只在 #352 记录收口与移交（L171–186）。因此该跨表恢复缺口在历史运行内已修，相关测试不再 skip；后续最终候选仍须按其实际树取验收，迭代10不应把此历史缺口重报为未修。

## 索引213，CSV 对未合入透视编辑器分支的影响判断

已顺序阅读原生 `native/419-2026-09-28T10-53-36-300Z_01a0e7a6-14ab-7792-b508-e6eb374a3567.jsonl` L1–23。已关闭 Issue #3 的 CSV 负责人因 Issue #4 #319 被唤醒；初次 `comment view --thread | head` 只到早期评论，后单独抽 #319 及关联判据，确认新缺口为透视编辑器打开时可见报错，不是 CSV（L5–11）。fetch 后 develop 仍 `db23b1f`，待合入 `a62831f` 分支仅改 `PivotDialogs.tsx` 和 `worksheet-lifecycle.spec.ts`，不触及 CSV 实现/检查、EditorPage 导出路径或前端 domain（L12–14）。负责人在 Issue #4 #332 交接“REQ-1-3影响面零”，Issue #3 保持关闭，没有新测试或源码改动（L15–23）。

这是一项基于**分支静态差异与当前 develop 未变**的证据连续性判断；#332 引用的 `[csv]` 4/4、后端 8/8、前端 7/7 是索引201在 `db23b1f` 的既有运行，不能当成索引213或未来合并头的新实测。后续若 final candidate 吸收其他 PR，应按实际合并树核影响面，不能仅凭 `a62831f` 两文件 diff 外推整合终态。

## 索引214，公式负责人消费早于其回应的旧通知

已顺序阅读原生 `native/421-2026-09-28T10-53-54-314Z_01a0e7a6-5b0a-7591-9049-5390a31e2083.jsonl` L1–9。已关闭 Issue #6 负责人收到 Issue #4 #290 的旧状态评论；该评论仅说明当时 PR #20 owner 正活跃、不需接管，而他此刻看到同串更晚 #322/#324/#327 已由自己完成管线确认（L5–7）。fetch 后 develop 仍 `db23b1f`、Issue #6 CLOSED，此前 #317 的检查候选未变化（L8–9）。因此没有新回复、源码修改或测试，属迟到通知消费。其结论再次引用“15项结构探针”作为当前同 head 的已有证据；该探针跨表 raw 外推限制见索引200/205/211，不能因多次重复而增强证明力。

## 索引215，CSV 对待合入 PR #23 的提前影响核对

已顺序阅读原生 `native/423-2026-09-28T10-54-32-697Z_01a0e7a6-f0f9-70f3-a962-1458f13fc378.jsonl` L1–32。已关闭 Issue #3 的负责人收到 Issue #4 #322 的 REQ-4 合同通知；先取长 thread 头部截断，后单看 #322，确认没有直接 CSV 要求（L5–10）。fetch 后 develop 仍为自身先前实测的 `db23b1f` / tree `7280c16…`，CSV 产品四文件相对 `a012447` 无差；[csv] 4 用例与前端 7 用例仍存在（L11–16）。他进一步预检**尚未合入**的 PR #23 `9063ca1`：虽改 `EditorPage.tsx`，diff hunks只在结构操作和 restoreStructure，`handleExportCsv` 段在 base/head 的 md5 均为 `da4d1aa8…`，domain/csv 不变；因此在 Issue #3 #335 记录“该分支合入本身不触发 CSV 专项重新取证”（L17–32）。

这是提前静态影响分析，不是 PR #23 合并后的 CSV 实跑；其结论应限于已检的五文件分支，不含其它后来并入 develop 的 PR。#335 引用的 CSV 4/4、后端8/8、前端7/7仍为索引201在 `db23b1f` 上的真实旧运行。负责人没有跑测试或更改产品，Issue #3 保持 closed；最终组合由根在最新候选跑全套。

## 索引216，公式负责人对 PR #23 的静态管线影响核对

已顺序阅读原生 `native/425-2026-09-28T10-55-21-299Z_01a0e7a7-aed3-731f-93ff-bd1fd4eaed58.jsonl` L1–29。已关闭 Issue #6 负责人因 Issue #5 #291 旧通知被唤醒；他读取的 #291 讨论串已推进到 PR #23 提交 #329，原参与者工具输出自身在 68KB 后尾截断，但当前关键评论及后续其推理可见（L4–7）。他 fetch 确认 develop 仍 `db23b1f`、PR #23 head `9063ca1`，diff 仅五个 frontend/checks 文件，`backend/` 与 `shared/formula-engine` 无差（L8–10）；随后在 Issue #5 #338 回复既有 PUT 恢复端点合同依旧、跨表 undo 新用例会给公式恢复腿 UI 证据，提醒 req3-integration 增至 11 例（L11–29）。

这是静态代码范围核对与既有 #304 端点审查的推论，**本会话未跑公式测试或浏览器检查**。#338 将 `req3-integration.spec.ts:457` 称“实跑断言”，其独立运行证据来自索引212修正 Chromium 路径后的 11/11，不应归给本会话；发评论时 PR #23 仍 OPEN（L12、L28），后在索引212所见另一会话最终合并。旧通知导致闭项再次消耗推理并发布重复管线总结；没有新产品缺陷。

## 索引217，CSV 负责人对透视判据通知的重复交接

已顺序阅读原生 `native/427-2026-09-28T10-56-10-746Z_01a0e7a8-6ffa-72fd-888d-5ebdd84436fb.jsonl` L1–32。已关闭 Issue #3 负责人收到 Issue #4 #323 通知，直接 JSON 查看得其内容只是透视编辑器缺失字段时禁用 Apply、恢复选择路径与前端失效表示判据，不含 CSV 要求（L8–11）。fetch 后 develop 仍 `db23b1f`，待合入透视修复 `a62831f` 相对它只改 `PivotDialogs.tsx` 和 `worksheet-lifecycle.spec.ts`（L12–17）；其 CSV 产品文件比较为空（L21）。因此本项没有新实现或需要重跑的 CSV 专项测试。

其远程分支大扫掠使用 `git diff origin/develop..branch`，把许多已落后或分叉的旧分支列为“触及 CSV/EditorPage”；负责人随后认识到该列举对旧分支不具决策意义，真正有用的是指定待合入分支的双文件差异（L21–22）。他在是否回复无关通知上反复推理，最终仍往 Issue #4 #337 发较长“CSV 无新待办”评论（L18–31），引起多人 queued 通知。该会话展示通知扩散与无动作说明的额外协作成本，但没有产品缺陷；#337 提及未来 `run.sh` 会覆盖 CSV 是计划，不是本会话实跑。

## 索引218，PR #25 透视编辑器修复、合并与晚到的同树全量证据

已顺序语义阅读原生 `native/429-2026-09-28T10-56-19-009Z_01a0e7a8-9041-731a-8e2b-b08892696814.jsonl` L1–381（审查视图 `session-218.md` L1–6111）；机械大段为已有 `items.md` 投影、重用的 run.sh/代码/评论、临时 PR 文本写入（原生 L92 3601 字符、L335 2855 字符、L351 1980 字符），均保留精确来源与长度。

PR #20 已合并但 Issue #4 重开，因为删去透视配置引用的表头后，**打开编辑器**没有可见错误；已存结果要保留。负责人在 `db23b1f` 基础的 `a62831f` 增添 `PivotDialogs.tsx` 派生错误，源范围空或已保存字段不在 `options` 时显示与 Refresh 同文案，不改服务端/共享包；浏览器用例覆盖删列后重开、reload、Refresh、陈旧字段不被静默换成首选项、重选后恢复以及有效透视反例（原生 L5–10、L27–31、L59–64）。他发现源表在操作后是否被 Refresh 意外修改缺显式断言，主动中止首轮浏览器运行并加断言，形成 `8826b4d`；断言校验删 B 列后 `B1=Status/B2=Open`，避免把旧 B2=1200 写错（L64–75）。首轮 run.sh 因其主动中止不能计通过。

`8826b4d` 上 bootstrap/build/tsc 0、结构单测14/14、API71/71（新 DATA_DIR）、run.sh **49 passed/1 skipped/0 failed、exit0**，12个 worksheet 用例全绿，REQ-5 all `REQ5_ALL_PASS`（L32–47、L155–178）。其中 skip 是当时 PR #23 尚未合入的 `req3-integration.spec.ts:427` 旧 fixme；这轮不能被写成 0 skip。作者创建 PR #25 时 develop 已由 PR #23 前进到 `b4a4b0c`，而新 PR 先登记旧 head `8826b4d`（L179–184）；意识到 base 漂移后 merge-tree clean，将 develop 合入为 **`dfcc039`**、重建并在11:18:30开始该 head 的全量重跑（L185–202）。差异中 PR #23 修改 EditorPage 的结构 undo 载荷，但透视编辑器读取路径未变（L199–201）。

**时序要严格写明**：#4 owner 在 PR #25 #366 对旧 head 表示 ready，#370 于11:19:26表示新 head `dfcc039` 正重取证；根在11:19:41已合并 PR #25 → develop `cc5b876`（PR timeline 原生 L222–235）。作者独立 `dfcc039` 上 run.sh 至11:40:06才报 **51 passed/0 skipped/exit0**，新增 #23 的结构 undo 原 fixme `:427` 与跨表 `:457` 皆绿，透视 `worksheet-lifecycle` 12/12；REQ-5 all 至11:45:18报 `REQ5_ALL_PASS`、exit0；单测14/14、API71/71、新构建/tsc也绿（L189–196、L278–332）。`dfcc039^{tree}` 与 merge `cc5b876^{tree}` 同为 `577ecba3…`、diff 空（L229–230），因此**终态已有合并树上的完整补验证**，且 #385/#386 回贴。合并时已有独立验证过的 PR #23 部分、旧 head 修复检查和 clean merge-tree，可支持较窄的代码影响判断；本会话内确切组合全量实跑仍在进行。不能倒置时间把旧 head 49 passed/1 skipped 称为新 head 的完整实跑，也不能据此说终态仍未修。此会话最终 Issue #4 尚 OPEN，负责人将关闭任务留给 owner（L339–381），后续状态需看别的会话。

操作噪声：PR #25 形式指派机制不能给已分配成员名 `deepseek-17`，改以 `deepseek` 得新成员 `deepseek-23`（L179–182），故实际 #4 owner 仍以评论审阅；同一分支曾产生关闭的重复 PR #24（L345–350）。后台轮询/延迟完成通知生成大量重复无动作回执（L103–153、L360–381）；这是协作成本而非产品缺陷。自动背景第一次 API 服务器会话曾 abort、但作者随后用新脚本取 71/71 并确认自身服务无残留（L39–46、L191–194、L355–358）。

## 索引219，CSV 对公式恢复旧通知再发无动作回复

已顺序阅读原生 `native/431-2026-09-28T10-57-36-106Z_01a0e7a9-bd6a-763c-95ef-88c1039771a0.jsonl` L1–27。CSV 闭项负责人收到 Issue #4 #324 的 `relatedSheets` / 公式恢复路径通知；多次取长 thread 再定位 #324，确认讨论不涉及 CSV（L5–16）。fetch 后 develop 仍 `db23b1f` / tree `7280c16…`，与其索引201的 CSV 专项运行 head 相同；CSV **产品**文件自 `a012447` 未变，但检查文件 `checks/csv.spec.ts`、`frontend/tests/csv.test.ts` 已增强，负责人在 L17 明确看见该差异（不可写成所有 CSV 文件无差）。无新测试，仅静态 `grep -c test` 4 例、run.sh 含 CSV 项目（L19–20）。最后仍在 Issue #4 #339 发较长“本项无需动作”回帖（L25–27），属于旧通知引发的重复协作成本。#339 所称 `[csv]` 4 passed 是索引201既有实跑，不能计为本会话新验；它把恢复路径最新 `value` 与 CSV 导出语义关联是合同推论，不是导出新实测。

## 索引220，CSV 对透视 Apply 判据更正第三次回复

已顺序阅读原生 `native/435-2026-09-28T10-59-01-085Z_01a0e7ab-095d-7457-8be9-5a20784948f5.jsonl` L1–32。Issue #4 #325 更正 #323 的判据：陈旧透视字段时 Apply 不一定强制禁用，只要提交失败可见且保留结果；这是 #4 owner 的范围，CSV 未受影响。闭项 CSV 负责人 fetch 见 develop 仍 `db23b1f`，待合入透视分支仍仅 `PivotDialogs.tsx` 与 `worksheet-lifecycle.spec.ts` 两文件，PR #23 仍 OPEN head `9063ca1`；`handleExportCsv` 在 develop/两分支 MD5 一致，导出路径未变（L14–23）。本轮未跑测试。

尽管他在 L13/L19/L22 多次认真指出“收到评论不必回执”且 #337/#339 已报告相同无影响结论，最终又向 Issue #4 #340 发较长说明（L24–32），通知多人 queued。该回复新增的信息主要是 #325 判据更正和重复确认导出函数哈希，对产品验收并无新实跑；后续团队不应将三次 no-op 回帖视为三份独立 CSV 证据。

## 索引221，公式负责人收到已解决的旧审阅提醒

已顺序阅读原生 `native/433-2026-09-28T10-59-01-088Z_01a0e7ab-0960-76a0-944f-48bb158b5fe1.jsonl` L1–9。关闭的 Issue #6 公式负责人收到旧 Issue #5 #297 中有关 reviewer 不可达的提醒；同一长线程已有 #298–300 解答与后续可用 reviewer，PR #23 仍 OPEN head `9063ca1`（L4–6）。他复核 req3 集成数口径：原先 10 总项含一项 `fixme` skip，PR #23 激活并加一个用例，故为 11 active；最终只作无动作说明，没有修改、测试或 Braid 回帖（L7–9）。末尾工具输出自身有长度截断，关键评论正文依既读 `items.md` 投影核对；不能将本次静态解释当新一次公式测试。

## 索引222，旧 #327 通知推动 CSV 闭项再写重复结论

已顺序阅读原生 `native/437-2026-09-28T11-01-14-073Z_01a0e7ad-10d9-7207-a258-ceebe373e674.jsonl` L1–25。通知来自 Issue #4 #327（10:53:33，REQ-4 管线侧证据沿用声明），本次才在 11:01 唤醒已关闭 Issue #3；原生 thread 命令尾保留且头截断（L6），但 L12 JSON 完整给出 #327 正文。#327 把 #317 的 15 项结构探针称为跨表正向 raw/value 证据，这是既有证据越界：#317 探针仅 `wb.sheets[0]`，后续 #23 浏览器检查才覆盖跨表 undo。CSV owner 在 L8–21 长时间判断是否应回复，自己承认 #332/#337/#339/#340 已足够且没有 CSV 新事实；仍重新 fetch，证实 develop `db23b1f`、修复分支只涉及 `PivotDialogs.tsx` 和 worksheet lifecycle 检查，CSV 实现自 `a012447` 未变（L18–20）。随后在 Issue #3 发独立顶层 #341（L21–24），重复宣布 4/4 旧证据沿用，未跑新测试，Issue #3 保持 CLOSED。这里的额外回复不构成第四份独立 CSV 验证，反而说明旧通知队列持续消耗闭项人员。

## 索引223，PR #23 合入后 REQ-5 真正复验与探针纠错

已顺序阅读原生 `native/439-2026-09-28T11-10-48-991Z_01a0e7b5-d69f-7638-b456-08673a49ee86.jsonl` L1–103。Issue #7 关闭负责人收到一条 10:02 的旧 Issue #5 #268 归属冲突通知；此时 develop 已从 `db23b1f` 前进到 PR #23 merge `b4a4b0c`（L4–16），#268 争议的 History 实现已落地。PR #23 只改 5 文件，虽未动 REQ-5 专项 checks/backend 规则，却改 `EditorPage.tsx`、`editing.ts`、`api.ts` 这些共用 UI 宿主，故重新取证有因果根据。负责人在新 head 运行 `checks/req5-all.sh`，构建、unit 20/20、parity 4/4、CSV 7/7、API 84、浏览器 10/10 全部 exit 0；另跑 req3-move API M1–M8 10/10（L24–28、L63–75、L100）。

他还核对结构快照含 `validationRules/filterViews/pivotTables`，restore PUT 会持久化这些字段（L19–25），写临时 9,221 字 API 探针（L44；机械代码省略）验证行插入后规则范围与 pivot 源范围平移，再按 undo 的 PUT 方式恢复并试写/刷新。首版探针 14 pass/1 fail 是**探针自身期望错误**：原始 B3=200 超出新设 0–100 规则，试图改回 200 被正确拒绝，pivot 仍计 50（L65–67）；修正 seed B3=90 并检查回写 90 后，16/16 pass（L67–71）。因此不可将首轮 FAIL 报为产品回归。该探针只直接覆盖 API 级快照 PUT + 元数据行为，浏览器 10 例覆盖的是 REQ-5 UI；不能把它称为新浏览器级“结构 undo × pivot”端到端。负责人把结果贴 #7 #355 与 #5 #356（L80–87）。后台 bg002 轮询 exit1 仅因尚不存在 move 日志，正式 bg001 exit0，所有后台 job 均终止（L94–103）。

## 索引224，REQ-3 对 #355 的重复交接回复

已顺序阅读原生 `native/441-2026-09-28T11-15-35-780Z_01a0e7ba-36e4-7569-bcc2-63e372115e30.jsonl` L1–18。Issue #5 已 CLOSED，收到刚发的 #7 #355；owner 先判断该 16/16 API 元数据探针是对 REQ-3-2-2 判据的补充且无需动作（L8–14），但后又决定跨项回执。第一次误将属于 Issue #7 的 #355 用 `issue comment 5 --reply-to` 回复，被 Braid 拒绝 `reply belongs to a different work item`；随后改为 Issue #7 #357 成功（L15–17）。该回复接受 #355 判据并复述既有 run.sh 49 pass / 0 skip 与 editing unit 15/15，**无本会话新测试**。本次未触及源码或重新打开 #5；主要观察仍是消息/回执联动。

## 索引225，旧归属通知唤醒 #7，登记在途 pivot 修复

已顺序阅读原生 `native/443-2026-09-28T11-16-01-338Z_01a0e7ba-9aba-7336-9857-d31a88d31c86.jsonl` L1–38。#7 owner 收到更早的 Issue #5 #269（撤销 History 归属措辞），develop 仍 `b4a4b0c`，索引223新实跑已经覆盖；他在 L17–23 认定本通知无 #7 任务且先前 #356 已补判据。后来发现另一个在途分支 `fix/req2-pivot-editor-missing-field` @ `8826b4d`：直接双点 diff `origin/develop` 对旧基分支会出现 PR #23 的反向差异（L27–28），不能据此说待合入变更会撤销 PR #23；merge-tree 语义 clean，分支相对 merge base 的独有变更为 `PivotDialogs.tsx` 与 `worksheet-lifecycle.spec.ts`。他在 #7 #360 登记合并后再验证计划与既有另一负责人在 `8826b4d` 的 REQ5_ALL_PASS 对照（L36–38），没有新测试。#360 用“实际触及两文件”描述分支增量时应明确是 merge-base/合并净变更口径，避免误读为双点 diff；本审查报告已限定。

## 索引226，REQ-3 接受元数据探针，但 skip 清点命令无效

已顺序阅读原生 `native/445-2026-09-28T11-16-07-042Z_01a0e7ba-b101-7499-98b4-322453f47f44.jsonl` L1–18。Issue #5 已关闭，收到 #7 #356 后静态核对 develop 仍 `b4a4b0c`、`git diff 9063ca1 origin/develop` 为空，`snapshotSheetStructure` 与恢复 PUT 确含三项 metadata（L9–11），随后在 #5 #359 接受索引223的 16/16 API 探针为规则范围/透视结果有效性判据（L12–17），没有新测试。需注意 L10 的 `git grep -n "test\.fixme\|test\.skip" ... | wc -l` 是否为有效 grep 取决于实际转义；此处原始动作为 `git grep -n "test\.fixme\|test\.skip"`，shell 双引号保留反斜杠供 BRE `\|` 交替，可能有效；但 #359 回帖中写的 `git grep -c "test\.fixme|test\.skip"`（无 BRE 交替反斜杠）与实际动作不一致，不能将该回帖的零条命令视为复现性清单。已有 49 passed/0 skipped 日志仍是更直接的全套结果。

## 索引227，合并树核实 #23 结构 undo 不被旧基分支回退

已顺序阅读原生 `native/447-2026-09-28T11-16-32-239Z_01a0e7bb-136f-7343-8ac7-2167e3d9bfd9.jsonl` L1–28。Issue #5 已关闭负责人被 #4 #358 唤醒；#358 是 `8826b4d` 的透视编辑器修复预验证，其判据含结构 undo 恢复正常。直接 `git diff origin/develop 8826b4d` 展现多个 PR #23 文件“删除”，但该分支 merge-base 是旧 `db23b1f`，作者进一步用 `git merge-tree --write-tree` 得 clean tree `577ecba`，该树相对 develop 只增加 `PivotDialogs.tsx` 和 worksheet lifecycle 检查（L15–21），这是避免误判 PR #23 被回退的关键因果区别。他直接读取 merge tree 中 `editing.ts` 的 relatedStructureDiff 与 `req3-integration` :423/:457，确认跨表 undo 实现/测试保持（L21），并在 #4 thread 回复（L24–25）。这里仅静态合并树/既有 branch 测试复用，没有在确切合并树上新跑 REQ-3 全套；不能把 clean merge-tree 单独当测试。最终 PR #25 的 dfcc039/cc5b876 同 tree `577ecba`，后续索引218已实跑全绿。

## 索引228，10:03 的旧归属定稿在 11:17 唤醒已关闭 #7

已顺序阅读原生 `native/449-2026-09-28T11-17-07-003Z_01a0e7bb-9b3b-730f-a755-957a4beb3ef9.jsonl` L1–34。触发 #5 #270 由 glm-1 于 10:03:30 定稿 History 单写者 deepseek-5，计划待 PR #20 合入后 rebase/提 PR；当前 11:17 已有 PR #20 `db23b1f` 与 PR #23 `b4a4b0c`，#7 owner 因旧通知再次唤醒并在 #5 #365 说明计划已完成（L14–29）。他查出旧 `491f6ba` 非 develop 祖先、原分支现 `9063ca1` 已合并，是 rebase/后续提交替代旧 SHA，不能误称旧承诺未执行（L22–24）。develop 仍 `b4a4b0c`，此次无新测试或产品变化。与此同时，他观察到 PR #24 已以 `8826b4d` head 建立并 ready，但尚未合入（L31–34）；后续会话/索引218的 PR #25 才是最终实际合并载体，不应把 #24 的 ready 当 merge 事实。此轮额外 #365 回帖继续呈现旧消息唤醒造成的协作回声，但补充了旧 SHA 与实际合入之间的准确映射。

## 索引229，#360 口径纠偏：旧基分支不能双点 diff 当净合入范围

已顺序阅读原生 `native/451-2026-09-28T11-17-18-036Z_01a0e7bb-c654-736b-9b12-c80ad17c4717.jsonl` L1–25。已关闭 #5 owner 收到 #7 #360，发现 `origin/develop b4a4b0c` 对在途旧基 `8826b4d` 的双点 diff 列出 PR #23 五个文件（L12–13），又查 merge-base 为 `db23b1f`，merge-tree clean `577ecba`（L14），进而证明最终合并树相对 develop 仅动 `PivotDialogs.tsx` 与 worksheet lifecycle 检查（L16）。他在 #7 #363 纠正 #360 的“实际触及两文件”须加基线限定（L17–24）。这是有效的静态合并影响面证据；仍不是合并 head 上的新全套实跑，终态实际运行见索引218。
