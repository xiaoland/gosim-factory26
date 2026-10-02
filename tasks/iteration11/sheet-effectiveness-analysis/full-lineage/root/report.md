# Issue 1 root 后段 lineage 分析

## 范围与结论

本报告只分析主 root 在 08:24 之后对 Issue 1 的输入、判断、工具动作、评论和后果，并覆盖 PR #13、PR #14 的 root 侧验收链。早期 04:24→08:24 沿用 `tasks/iteration11/run-audit/sheet/` 的已有全文审计；本报告不把早期摘要重新计作阅读。原始 B 是：

`tasks/iteration11/sheet-effectiveness-analysis/evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4`

按统一索引 `full-lineage/inventory/{inventory.md,inventory.json,records.jsonl}`，Issue 1 共 2,411 条索引记录，其中 inventory 标为 `needs_new_read` 的新增段为 1,083 条；PR #13 为 415 条，PR #14 为 52 条。这个计数是覆盖账，不把程序解析等同人工全文阅读。此次语义 pass 逐记录按 user/assistant/tool/comment 生命周期导航，关键决定和结果回到原行核读；长上下文、重复工具回包和重复代码没有重新展开，而是以原始 path、line、msgID、时间和载荷指纹保留。精确阅读/省略边界见 `coverage.md`。

阶段切点复核补充了一条重要边界：final-source 并非所有 08:24 前载体都能直接由旧 audit 继承。Issue 1 的 `2026-09-29T08-01-37-411Z_01a0ec2e-...jsonl` 在旧 early 载体 17 行之后追加 11 行（最终 28 行），新增了 #171/#172/#174、D-C14、resolve 和后续重开提示；这 11 行已在本次 root 语义链中补读。另一个 07:37 文件属于 Issue 4/B，不属于本报告的 root Issue 1 主线；它在 final-source 为 78 行、旧 early 为 36 行，且 lineage comparison 标为 `content_diff`、前缀不相等，因此不能被早期全文账当作可继承证据。本报告仅把它作为跨工作项背景边界，不用它替代 Issue 1 证据。

主线的有效机制是：root 将跨 ABC/DE 的共享语义先收敛成可执行契约，再把缺口绑定到具体 owner、测试和候选 commit；候选移动时按适用性重新判断证据；最终只在当前树、候选指纹和门禁证据一致后停止。它确实减少了跨 agent 的语义漂移，但长 thread 的逐通知读取和几次正文维护错误产生了可见成本。

## 逐段主线

### 09:26：接手 cut/move 争议，形成根侧裁定

直接证据是 Issue 1 原始 native 文件：

`work/native-homes/pi-glm-fast-01a0ec7c-532c-7cb3-8b89-f580a8ee0c64/2026-09-29T09-26-06-713Z_01a0ec7c-5679-76bb-8f0c-16ee96829f11.jsonl`，以及其中对应的 Issue #212→#217 工具结果和 assistant turns。

root 看到 C 对 cut/move 语义的疑问后，判断这是共享语义而非继续留给某一个实现 agent 的局部决定；它检查正文、发布 #214 收讫并把 advisor 对 raw text unchanged、copy-only `rewriteRefs`、`=#REF!` collapse 和低风险主流表格语义的阅读折入 #216。#214 中误带的字面 `EOF` 随后被发现并编辑移除。#213、#215、#217 只是已覆盖的回执或证据，root 选择不再重复回复。

后果是 cut/move 的不变式、copy/preserve 口径和剩余 harness 不确定性有了单一权威入口；代价是一次正文小错误和等待 advisor 的交接延迟。这里的证据支持“root 作了裁定并发布”，不支持“该裁定本身已由隐藏评测证明正确”。

### 09:45–09:59：把 paste 从讨论变成原子 endpoint 契约

Issue 1 thread 1 的实体评论在 `tasks/iteration11/sheet-effectiveness-analysis/evidence/comments.md`：#232、#238、#242、#247、#259。native 侧主要来自 `.../2026-09-29T09-45-...jsonl`、`.../2026-09-29T09-55-...jsonl`；统一索引保留每个实际文件的精确原行与 msgID。

root 的动作不是简单转发 agent 意见：

- #232 将 requirements 变成一个 transaction：tail expand → gate → write → touch/snapshot；成功路径完成正常 touch，409 路径必须无结构、selection、updatedAt 残留。它区分 displacement/insert/delete 的 B endpoint 与 paste growth endpoint，paste/state 不添加应用层尺寸上限，回滚采用 state replay，不采用会改写无关 raw 的 delete-shrink 回退。
- #238 接受 state 与 paste 同属固化尺寸，并补 outer transaction/SAVEPOINT 及 post-expansion reread；README 锚点也收窄到 `:56` 和 `:89`。
- #242 接受 B/C 的反例：尾扩张不能调用 `rewriteRefsOnInsertDelete`/shift helper；必须 bare `UPDATE`，因为旧尾端的 `=A7` 等 raw 可能被持久改变。成功路径和 409 路径都绑定 probe。
- #247 把 `A1='=A7'` 的尾扩张保持 raw 交给 PR #11 E2E，缺失时以 E②作为回归阻断点。
- #259 更正了一个关键证据边界：已有 `e2e/formula-engine.spec.ts:276` 只是无结构操作的基线，不能替代尾扩张测试；真实删除回退损坏证据应引用 B 自己的 `delete-shrink-rollback...` 目录。

后果是 D 的实现约束、PR #11 的测试义务和 B 的反例证据形成可追踪闭环。#218–#268 中大量编号只是 A/B/C 回执、正文账或重复维护；#232、#238、#242、#247、#259 才实质推进了语义或验收。root 仍逐条读取了若干已经在输入中的无动作评论（包括 #250、#252、#254、#255、#257、#258），这说明活跃长 thread 同时承载契约历史和当前证据，能够避免漏掉 #259 这类更正，但读取策略还有压缩空间。

### 10:02–10:45：从独立门禁发现真正缺口，并让 D 补测试

主 native 文件：

`work/native-homes/pi-glm-fast-01a0ec9d-9f09-7e02-a3c7-839bcd784e30/2026-09-29T10-02-28-840Z_01a0ec9d-a268-771a-8193-b6a47af56470.jsonl`。

root 读到 PR #11 的应用改动、README、frontend wiring 和首轮 E2E 根因修复后，以 `b3ced6be` 对应 turn 发布进度；看到 #291 的独立重跑全部通过时，又没有把“全绿”当作完结，而是对照 #247 找出 `=A7` 尾扩张成功路径仍未覆盖（native msg `1b14462a` 附近）。它在 #291 回复中明确要求 D 补 case。D 随后以 #294 加入 `range-undo.spec.ts:221` 的 case，候选 `517384b` 的 46 项检查通过；root 又检查 app-tree diff，确认除 README/E2E/tasks 外无未授权应用差异。

root 在 #304 作了 D/E seam 裁定：undo 只恢复四类编辑、pivot validity/config/stale/last_result；结果 worksheet 的 materialized cells 不由 undo 恢复，由 E Refresh 负责，并要求 seam case。随后 #319 以 develop `4e1a7bc` 为基线分配 batch 4 给 E，明确 0–100 paste 409、undo→pivot stale→Refresh、B 回归②等义务。

这是跨团队组织最清楚的一次因果链：独立通过 → 对照契约发现缺口 → owner 补测试 → 树完整性核对 → seam 责任转移。root 没有自己改应用代码，也没有以重复运行代替缺口定义。

### 10:47–11:18：v1.6 的快速交错更正，以及 E 的共享取值语义

主 native 文件：

`work/native-homes/pi-glm-fast-01a0ecc6-e48e-77f2-835c-5d0d25dea18a/2026-09-29T10-47-33-486Z_01a0ecc6-e76e-7774-8701-b0cc8b4a9fa7.jsonl`；后续 `...2026-09-29T11-10-...jsonl`。

root 对 E 的设计另作了 requirements 核查，发布 #363：9 个 endpoint shape、transaction/snapshot、validation 双模板、mock 完整参数，以及 pivot 空 source 的测试义务。随后交错事件暴露了两次“刚发布即过时”的问题：

- B counterexample 和 E #362 到达后，#363 中“B accepted/no counterexample”已不再成立。root 在 #397 公开更正为 sentinel：pivot 行保留、`source_range=''`、`stale=1`、last_result 与两张 worksheet 保留，Refresh 失败返回 409 field error；这是 TEXT NOT NULL 下可落地的状态，也保留 undo 对旧 range 的恢复。
- root 在 #406 先登记 sort/pivot 读取 persisted raw 的假设；对照 E-D8-2 的 display-value 约定后，在 #428 纠正为显示值，要求统一 `valueFor(row,col)` 接缝，并保留单一 `rewriteRefsOnRowPermutation` primitive 和 canonical test。

这两次更正不是无关编辑：前者避免 Refresh 对可解析但错误范围静默重算，后者避免 sort/pivot 与显示层出现不同值语义。它们也暴露 root 的过程风险：在快速交错下，正文刚形成时的“当前事实”可能已旧。root 选择显式改正而非掩盖，保留了可审计性。

### 11:20–11:55：阻断旧 primitive，收敛 PR #12，并建立最后整合门

相关 native 文件按时段分为 `...2026-09-29T11-20-52-...jsonl`、`...11-28-48-...jsonl`、`...11-32-14-...jsonl`、`...11-44-28-...jsonl`。root 读到旧 primitive 被 cherry-pick 后，识别 `=B-1`、`=$B$-1` 负/越界映射未词法化且可能持久化的缺陷，发布 #462，把它定义为“无映射目标则不改写”，要求四种锁定形式。

在修复 `ed72f89` 的环境中立门禁、语义 probe 17/17 和 9ab0559 证据到达后，root 以 #476 接受修复，不重复运行已有适用门禁，而要求 PR #12 owner 将固定 sha 合入。随后 #509 收讫 A3 README 监测链、blob/content hash 更正和“deepseek-3 最后一次 merge-tree review 后退订；最终检查归整合门”的责任链。PR #12 的最终候选通过检查后，root 核对 merge-tree，合并 `422f718`→develop `ca69b7b`，关闭 Issue 7，再用 #539 分配 PR #13。

这里 root 的停止判断有两个层次：已有适用的修复证据不机械重跑；候选树发生改变时再恢复严格门禁。这避免了把 token 增长当语义进展，同时保留缺陷修复后的新 sha 身份。

### PR #14：把 Ctrl+Z flake 限定为测试时序，并重新要求当前树重跑

PR #14 的三份 native 文件为：

`work/native-homes/pi-glm-fast-01a0ee33-33cc-71c3-930e-8fcabdb592ec/2026-09-29T17-25-54-187Z_01a0ee33-998b-7726-bab5-046059220625.jsonl`，以及同一 session 的两个 final-source 载体（具体完整路径、行段和 msgID 见 `coverage.md`）。

PR #11 彩排中的 #553 记录首个 Ctrl+Z 并发失败；串行通过、实现无改动，根因是 optimistic render 后 `recordHistory` 尚未入栈。PR #14 owner 以 #570/#571 提议 `waitForRecordedUndoStep`，#572 只改 E2E spec，应用树保持不变；#574 以 `18cfeab`、68 passed、SHA256 和 match-head 交回。

PR #13 的当前 head 纪律来自 #571/#574：PR #14 只改 E2E spec，#574 已交回 `18cfeab`、68 passed、SHA256 和 match-head；PR #13 的四道门按当前候选交回。root 后来的 #578 比较了旧 `d07dd62` 与已变化的 suite，并更正 11/11→12/12；它强化了当前候选树、checksum 和适用性核对，但不是四道门整体启动的直接原因，也没有否定当时已经存在的 #574 non-skip 68/unit 证据。

### PR #13：从 gap integration 到当前候选的四道门和停止

PR #13 的四份 native 文件由统一索引列出（首份 `2026-09-29T11-55-07-417Z`，恢复/收尾份 `2026-09-30T01-48-34-507Z`、`02-08-26-581Z`、`02-09-24-375Z`）；415 条记录均在语义导航范围内，但长重复 payload 没有逐字重展开，关键 owner 决策、门禁、merge 结果回到原行核读。owner 先以 develop `ca69b7b` 为基线，识别真正缺口是“last updated home 与 editor 同值”的 integration 语义，而旧 E2E 只证明 smoke visibility；这不是把已有 E2E 计数换名。

root 的 #578 还更正了自己从 #552 沿用的错误计数 11/11→12/12，并记录旧 `d07dd62` 与 PR #14 后 tree 之间的核对边界。PR #13 owner 的 #582 给出串行当前候选 `5926059` 的完整证据：typecheck 0、backend 171、frontend 196、nonskip E2E 68、skipbuild E2E 68、Node 20.19.3，dirty/untracked 均 false；随后 #583 将 `5926059` 合入 main `10cba2a`。root 的 #588 核对 main/develop/candidate tree 均为 `1a18466b`、checksums、#566 的 12/12、post-merge smoke 和 24 atomics，确认 A–E 与 #4 均关闭；#589 是短完成收讫。

root 在最终点选择证据映射和树核对，没有另行重跑已经在同一候选上交回的四道门。这一停止是有条件的：树、候选、dirty 状态、门禁读数和 post-merge smoke 相符；不是“评论已结束”就自动停止。

## 根侧机制评价

### 直接证据支持的有效做法

1. **共享契约先于实现。** #232/#238/#242 将 B 的实测反例转换为 transaction 顺序、bare UPDATE、409 residue、state replay 和 README 锚点；#304 又将 D/E seam 转成四类 undo 与 Refresh 责任。这样跨 ABC/DE 的“谁负责”有明确终点。
2. **独立检查用来找缺口，不用来替代需求。** #291 全绿仍被 #247 对照出 A1 尾扩张缺 case；#294 补完后才进入 batch4。root 检查 app-tree diff，保证测试补丁未偷带应用行为。
3. **head 纪律约束证据适用性。** #571/#574 形成 PR #14 的 spec-only 修复、当前 head、68 passed 和 checksum 证据；#578 后来比较旧 `d07dd62`，补充当前树与计数核对。它不能单独被当作 PR #13 四道门启动的原因，但帮助最终验收保留了候选身份边界。
4. **停止条件可复核。** #588 以 tree equality、hash、dirty/untracked、gate counts、post-merge smoke 和 issue closure 共同构成终点，并保留同名 workbook、mixed-$、paste/state 无 app size limit 等已知边界。

### 直接证据支持的成本和风险

1. 长 thread 的每条更新都会携带大量历史契约。root 的 09:45/10:02 输入分别约 125KB/167,672 字符；#250 等无动作回执被重复读取。部分重读确实抓住了 #259、#291、#375 之类的真实更正，不能全部归为噪声，但机械读取和正文重建可以更依赖统一索引。
2. #214 的 `EOF`、正文中的 #313→#319 指针错误，以及 #561 的 11/11 计数，都是低级维护错误；均有后续更正，未改变最终树，但增加了可审计成本。
3. #363 和 #406 的假设在发布时分别已被新 counterexample、display-value 语义追上。root 的公开更正是好的恢复行为；更好的做法是发布前对“刚到达事件”和当前正文做一次短一致性检查。

## 证据边界

本报告可以证明 root 的输入、判断、工具动作、评论演变、commit/tree 验收和停止条件；不能由 native/SQLite 评论记录单独证明隐藏评测分数、用户体验改善幅度或所有 agent 内部未公开思考。SQLite 只读索引保存当前 item/comment 状态，hide/resolve 历史仍以 native JSONL 为准；因此 lifecycle 的历史结论只引用有原生事件或评论证据的部分。所有源文件、记录状态、重复载荷和缺读边界见 `coverage.md`。
