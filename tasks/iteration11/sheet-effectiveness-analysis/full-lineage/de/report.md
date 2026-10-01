# D/E full lineage: I10 → I11

本报告重建指定 run 中 D（Issue #6 / PR #11，及 PR #14 稳定性修正）与 E（Issue #7 / PR #12）从需求输入、上下文获取、设计和交接、实现反馈、跨域修正到最终关闭的信息流。阅读对象是 final-source run：

`tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4`

阅读分成两层，不能等同：程序对原生 JSONL 全量逐行解析，并按真实 source path、session id、cwd、msg id 记账；模型只对下文列明的语义批次做定向阅读（assistant 的决策/命令/结果、交接、Pi subagent 返回和协作评论）。完全重复的快照、重复轮询通知、大段代码回包和图片二进制没有全部进入模型，只在 coverage 中计数并保留原始定位。没有按 basename 合并 canonical 与 continuation，也没有把 `comments.md`、`work-items.md` 或 `subagent-calls.json` 当作原生全文来源。

## 1. 身份、范围和终态

DB 只读核对到：14 个 work item、589 条 local comment、3,494 条 event、15 个 agent instance、444 个 provider session、8 条 association。D/E 原生记录分别为 2,394 / 3,710 行；对应原生文件 29 / 53 个。另读 PR #13 4 个文件 415 行，PR #14 3 个文件 52 行，用于主线交接和 D 稳定性收口。原始文件、行数、cwd、阶段和 read status 详见同目录 `coverage.md`。

DB `associations` 当前八条关系为：`issue:1→pr:2`、`issue:3→pr:8`、`issue:4→pr:9`、`issue:5→pr:10`、`issue:6→pr:11`、`issue:7→pr:12`、`issue:1→pr:13`、`issue:6→pr:14`。因此 D/E 的直接关系是 `Issue #6→PR #11/#14`、`Issue #7→PR #12`；PR #13 直接关联根 Issue #1，不能把 PR #11/#12 说成直接关联根 Issue。DB 当前状态显示 Issue #6/#7 CLOSED、PR #11/#12/#13/#14 MERGED。最终应用链为 PR #11 merge `4e1a7bc`，PR #12 merge `ca69b7b`，PR #14 merge `2dc4b9f`，PR #13 最终候选 `5926059` → main merge `10cba2ad`；这些是运行记录的状态事实，不是从分数倒推。

### Pi 原生角色

- D Issue 负责人使用 `pi-glm-fast`，provider identity `01a0ec7d-7062-7913-82da-2f5f9fa60d71`；其 advisor transcript `.../subagent-artifacts/b06382e6-058c-41d4-b47b-792e9c028955_advisor_transcript.jsonl` 核实 `PUT .../state` 已支持 validations/filters/pivots 全表恢复，遂把 D 的后端范围收敛到客户端快照和 paste 事务。
- D PR 负责人使用 `pi-deepseek-fast`，identity `01a0ec8e-37ae-7b63-9278-6357cf71c4a9`；三个 vision transcript（`028ec617...`、`7db5161f...`、`88719c66...`）把参考图与实现图的网格线、选区/复制源差异反馈给 PR #11。视觉结果只作为 UI 判据输入，未被夸大为持久化事实。
- E Issue 负责人使用 `pi-deepseek-fast`，identity `01a0ecbb-ccb6-77e1-b369-df370111d350`；advisor `45923385...` 评审数字验证、filter、pivot、sort，vision `e0982353...` 先纠正参考图文件错配。E continuation identity `01a0ecca-0119-7532-a2c3-6b0a196170ed` 的三个 advisor（`744ec1d7...`、`94df6b1c...`、`9ba8b682...`）分别复核空 range 哨兵、排序 R0/RT/RD 解释、显示值接缝。Pi 输出并非全部被采纳：#375 明确拒绝 advisor 建议的新错误文案，保留需求已有字段文案；这里仅把被评论/契约明确消费的判断列入信息流，没有把隐藏思维当成决策证据。
- PR #12 仍由 `pi-deepseek-fast` 实施，PR #13 同 profile，PR #14 由 `pi-glm-fast` 实施。所有对应 provider path 与 continuation 均在 `coverage.md` 中列出。

## 2. 需求输入 → 可见上下文

### D / Issue #6

Issue #6 初始范围是 REQ-3-1-2、REQ-3-1-3、REQ-3-2-1、REQ-3-2-2：二维粘贴、矩形选择、copy/cut/paste、撤销/重做。D 与 E 都在 **04:41 创建**并挂到 Issue #1；“批次分配”是后续上下文。Issue #6 在 09:27 才指派 `@glm-10`，正文随后更新，并在 comment #220（物理文件 `evidence/comments.md:4783`）交接 PR #11。

D 在可见上下文中先吸收了 C 的 formula probe 和根契约：

- copy 计算使用**粘贴后扩张的 bounds**；`C1 → C7` 得 `=A7+B7` / 网格 `0`，`C1 → B1` 才得到逐字 `=#REF!`（Issue #6 #221/#227）。
- cut/move 采用根裁定的读法②：移动块 raw 原样写入目标、同事务清空源、仅重算；不调用 copy 重写、不引入切换开关。
- paste 不能先提交结构扩张再做校验。D→根的新契约 v1.5（Issue #1 #232/#242）允许新增 paste 端点，在同一事务中尾扩张、验证、写入和 touch；`PUT .../cells` 的越界 400 仍不变。

Issue #6 负责人 Pi advisor 的关键输入是：state 端点已经原生支持 `validations`/`filters`/`pivots` 和 `lastResult/stale` 恢复，因此 D 不重复发明后端 state 契约。D 负责人将这项事实传播到 D-D2（客户端整表快照、PUT state、100 项软上限、刷新后恢复）。

### E / Issue #7

Issue #7 初始范围是 REQ-5-1-1、REQ-5-1-2、REQ-5-2-1、REQ-5-3-1：sort/filter/validation/pivot。它与 D 一样在 **04:41 创建**；直到 **10:35:23.236040197Z**（`local_activity` ordinal 553）才指派 `@deepseek-12`，10:48 创建并关联 PR #12。可见状态没有把 `@deepseek-11` 作为 E owner；该身份出现在 D PR #11 / 后续 D 稳定性链。其入口正文和 D→E 接缝在 Issue #7 #314（物理文件 `evidence/comments.md:6975`）可见：paste 必须从 mock gate 换成真实 0–100 gate 并保持 409 原子性，undo 要恢复 pivot 的 config/stale/last_result 三元组，结果 worksheet cells 的一致性由 E Refresh 接管。B 的结构/pivot 源约束则由 #323 交给 E 回归。

E 设计定稿 #331（约 `comments.md:7359`）列出 E-D1…E-D10；#336/ #355/ #359 暴露原有空 range DELETE 语义的可达性和别名风险；#362 暂停实现并重新裁定。这里发生了实质的跨域信息流：B 原实现“折叠到空就删除 pivot 行”，但删除后结果表与 pivot 关联消失，REQ-5-3-1 要求的可见错误/保留两表/Refresh 入口不可达。

顺序应以 B 的 probe 为起点：#355/#356 先实测 `A2:A3` 删除两次后残留合法且 in-bounds 的 `A2`，并发现它与普通位移 `stale=1` 不可区分，会让 Refresh 静默按错位数据重算；#362 因此冻结实现等待裁定。`744ec1d7...` 的 advisor 输入已包含这组 probe 事实，advisor 做的是独立重核、比较选项并提出哨兵的最强反论据，不是首次发现该别名风险。随后 #375 将方向固定为不删 pivot 行、写 `source_range=''`、`stale=1`，并明确拒绝 advisor 建议的新文案；Refresh/Apply 使用需求已有 `Pivot field is no longer available. Select a new field.`，保持 `last_result` 和结果 worksheet。#377 将该形态写入 E-D8。该链保留 E 的产品目标，同时避免静默错位重算。

排序也经过跨域裁定：#365/C 发现“raw 不变”会使排序后的公式展示错误；#396 冻结 RT（row permutation）规则，排序和 pivot 均经 display-value seam，`$` 行引用按 rowMap 移动，矩形外和表头引用不改。E #427 把 `valueFor`、`resolvePivotField` 单点和假设列入实现接口。

## 3. D 设计、实现反馈和交接

### 3.1 设计决定

Issue #6 #220/#221 将 D-D1…D-D4 固定下来：paste 单事务、state 快照恢复、UI 选区/复制源显示、move 读法②；D 还登记 README “三条路径”改为四条。PR #11 原生正文在 `.../pr-11...09-45-39-523Z...jsonl:218` 复述交付范围和 base `develop @ a592c3e`。

### 3.2 首轮失败如何改变实现

PR #11 原生记录保留了首轮 `6 failed / 4 passed`，并将两类根因分开：FormulaBar blur 把旧 draft 写入新选中单元格；UnoCSS preflight 缺失造成 content-box 尺寸和不可见网格边框。该反馈来自实际运行日志和截图，不是事后猜测。修复后首次候选 `bdb457a`/应用树 `a9f775f`，再补齐 #247 §1 的尾扩张公式用例，得到 `5b3a514`/应用树 `517384b`，46 项 e2e 通过（原生实现交接 `...pr-11...01a0ecaa...jsonl:177`）。

独立验证者关注两条 C 接缝：copy bounds 与 move dangling formula；D 将其写成可复现 e2e，并把“首轮 44/45 的过期结果”明确标为 superseded，保留日志但不混入最终结论。Issue #6 #289/#294 将候选、证据和未决接缝交给根/C/E；#302/#304 收到根侧验收，PR #11 以 `4e1a7bc` 合入，Issue #6 随之关闭。

### 3.3 D → E 的实际交接

Issue #7 #314 收到 paste 真 gate、state replay 和 pivot 接缝；D 负责人 #304 明确把剩余的 paste 0–100 409 回归和撤销-透视接缝转移给 E，不把它们伪装成 D 已完成项。E #331/#348 接收 gate 调用位置、mock wrapper 三参数风险、pivot collapse 需要自有回归；E #521 后以 PR #12 验收候选承接这些交接。

## 4. E 设计、实现反馈和跨域纠正

### 4.1 E 设计到实现

E #331 先登记数字文案双模板、筛选条件、验证 gate、pivot 三态、结果物化、撤销边界和 RT。#377 改判空 range 为 sentinel；#396 将排序从 raw 读法改为 RT/display seam。PR #12 原生实现阶段记录了 C 的 rowMap 缺陷：初版原语 `7ba7916` 对负/越界映射产生非法公式；C/根裁定该缺陷属于契约内修复，发布 `ed72f89`，PR #12 接入 `9ab0559`。这不是 E 自己发明的新语义，E 通过 #455/#473/#486 接缝复核消费。

PR #12 实现候选 `42f9c5b` 的原生交接位于 `.../pr-12...10-48-42-721Z...jsonl:697`；随后只改 packet 的 `422f718`（同应用树）。E 端证据交接包含 backend 171、frontend 196、typecheck/static gate、64 e2e 和 platform path；报告仅记录这些原运行结果，不重新运行。Issue #7 #521/#522/#523 接收候选、真实 paste gate、sentinel、B regression 和 C canonical consumption。

### 4.2 E 实际吸收的反馈

- **B → E**：#323/#355 先指出删空 pivot 会改变源 worksheet 删除约束和结果回链；#345 接受改判；#377 以 sentinel 收敛为可判别状态。B 后续 regression 证明：源行删除后 pivot 仍在、source range 是不可解析哨兵、stale=1、last_result/两张 worksheet 保留；删除结果 worksheet 仍是唯一逃生路径。
- **D → E**：#350 明确 gate mock 若只收一参数会在真规则签名下失败；E 改为真实 gate，paste 409 不落库。撤销快照只恢复 config/stale/last_result，不把物化结果 worksheet cells 当作 D 的逆向快照；Refresh 重新建立一致性。
- **C → E**：#365、#391、#396 把排序值层从 raw 改为 display value，并冻结 rowMap；#451 发现负 rowMap 生成 `=B-1` / `=$B$-1`，#459/ #470/ #480 追踪修订后原语和 canonical 8/8 消费。
- **A/README → E**：#366、#529、#540 确认 A-3 display seam 文案由 PR #12 一并进入 develop，PR #13 只需在最终候选复跑；E 没有回退 A 的契约。

PR #12 在原生记录中反复标出“旧轮询/旧 C3 失败通知”并明确 superseded；最终结论只取 `42f9c5b` 的验证和 `422f718` 的同树 packet 修订。PR #12 merge `ca69b7b` 后，Issue #7 在 11:50 左右关闭；#562/#564/#567 把 B regression、numeric double-template 和 E domain zero-diff 交回 PR #13。

E 的上下文管理还留下一个可复核的正/负例：Issue #7 continuation `work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_...jsonl:53–69`（native msg `bd1f3d9d`、`1a02d6be`、`01f7b9ae` 等）处理 #362/#370 的折叠请求时，先错误地把多个 ID 一次传给 `unresolve`（CLI 明确报 unexpected argument），随后分别 unresolve 成功，并编辑 #470 把“已折叠”更正为“已取代但保持可见”。这说明 thread 状态纠正是有实际负例和恢复动作的；不能从当前 resolved/open 状态倒推历史一直正确。

## 5. 晚期稳定性、整合和关闭

PR #11 #553 暴露了撤销快捷键 flake：`commitCell` 先乐观渲染，`recordHistory` 要等 `PUT .../cells` 返回才入栈；检查在入栈前按 Ctrl+Z 只是 no-op。D 将它归为 spec 时序，不擅自增加“提交在途立即撤销”产品语义。PR #14 #572 用 `waitForRecordedUndoStep` 修正 e2e，应用树零改动；原生 PR #14 provider `.../2026-09-29T17-25-54-187Z...jsonl:26` 核实候选 `18cfeab` 的证据，按 `--match-head-commit` 合入 `2dc4b9f`。D #576 解决 thread，保留两个 D→E 接缝入口在 Issue #7，不因 thread 折叠丢交接。

PR #13 原生 `.../2026-09-30T01-48-34-507Z...jsonl:156` 记录最终候选 `5926059`（含 PR #14 spec 修正）四门完成并合并到 main `10cba2a`；`.../2026-09-30T02-08-26-581Z...jsonl:24` 核对 main/develop 树一致。根 Issue #1 #588/#589 关闭全部主线。关于边界，只能报告可见裁定：根 Issue #1 comment #588（`evidence/comments.md:13904`）明确把“排序混合 `$` 退化构型”和“paste/state 无应用层尺寸上限”等列为“已记录的已知边界”，不构成当时的未决阻塞。这个可见声明不能推出不存在隐藏未决项；DB 也没有完整的隐藏历史表，因此报告不作“无隐藏未决”的强结论。

## 6. 状态、关系和可见性影响

DB `local_activity` 给出可复算时序：Issue #6 与 #7 均 04:41 创建→D 09:27 指派、E **10:35:23.236040197Z** 指派→各自 PR 创建/双向 link→PR #11 10:30 merge、Issue #6 10:34 close→PR #12 11:50 merge、Issue #7 11:50 close；PR #13 随后创建/link root，PR #14 在 late D flake 后创建/link Issue #6，PR #14 merge 后 PR #13 重取最终候选并 merge。当前 association/merge 表只有最终状态，因此历史关系变化仍以 native JSONL 和 activity 为准。

评论状态不能只看当前 export：589 条评论中 D/E 相关可见评论仍保留交接正文；#220、#366、#455、#473 等讨论经历 resolve/折叠；PR #11 #576 明确“D→E 两条入口已在 Issue #7 正文登记”，所以折叠并不表示信息删除。当前 `comments.md` 是最新 lifecycle，native JSONL 保留了 resolve/hide 前后的上下文。隐藏/过时内容的处理遵循：保留首轮失败与 superseded 说明作为错误学习证据，避免用旧候选替代最终候选；不把 score 或应用 bug 作为 D/E 因果证据。

## 7. 有效实践、错误和信息缺口

有效实践：

1. 先锁定跨域契约和消费方，再实现；D 的 paste 原子性、E 的 sentinel/RT 都有根 Issue comment 作为可追溯裁定。
2. 为设计错误保留可复现 probe 和失败日志，同时明确 superseded 候选，避免轮询回包污染结论。
3. 将 Pi advisor/vision 作为独立复核来源；B probe 先发现空 range 别名风险，advisor 在已给定事实下重核选项并强化哨兵论证，随后 E 形成“probe→独立复核→契约→回归”闭环。
4. 用具体 commit/tree、cwd、candidate 和 `--match-head-commit` 绑定证据；PR #14 的“应用树不变、只改 spec”使最终候选重取逻辑清晰。

错误与修正：D 首轮 FormulaBar draft/CSS preflight 缺陷；D e2e 曾有误报的旧绝对引用断言；E 初始 pivot 保留原 range 方案存在合法别名和源表永久锁定风险；C 旧 rowMap 对负映射生成非法公式；D 撤销快捷键检查抢在 history 入栈之前。每项都有对应修复或改判，且修复范围没有被扩大成未经授权的产品语义。

缺口：两条早期独有原件在 final-source 目录索引与本地 increment 中的路径/覆盖账存在差异；原件仍在本地 increment，且旧的全读账已覆盖，因此不能写成全库缺失或证据不可得。DB 没有 description history、relationship history 或 comment lifecycle history，故这些演变必须以 native JSONL/activity 重建。部分旧 cwd 会继续引用运行外的 `/workspace/template/...` 路径，报告将它视为原始身份字段，不假设当前工作区可复现。代码/工具巨大回包和图片数据没有逐字复制，也没有全部进入模型；coverage 只说明其存在、数量和原始定位，不能把程序解析写成模型语义阅读。
