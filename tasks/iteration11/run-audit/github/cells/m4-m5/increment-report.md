# M4/M5 固定尾段增量审查（snapshot-02）

审查截点为 **2026-09-29 08:26:07.983932 UTC**。仅将 snapshot-02 中归属 Issue #6 / PR #16、Issue #8 / PR #15 的十份原生记录与 snapshot-01 作前缀比对，并逐条读完新增 **738 条记录**。旧前缀十份均逐字节相同；根 Issue #1 的两份增量由主审负责。此截点各会话仍在运行，以下是当时可见状态，不代表后续终态。精确文件与范围见 `increment-read-receipts.json`。记录引用 `I<increment-index>:r<record>`，路径由该回执映射到 snapshot-02 原生 JSONL。

## 1. M5：同 head 证据补齐，但失败原因不能被确证排除

**原文→动作→后果。** PR #15 worker 在 `6f272e7` 的干净副本上完成平台路径检查，`EXIT=0 / 58 passed`，PR #15 评论 #135；Issue #8 负责人先核实 `bab2b11..6f272e7` 只有 packet 文档 17+/10-，于 #137 接受 docs-only 等价证据。随后根 #134 要求严格锚点，worker 在同一 `6f272e7` 跑工作区 Vitest/typecheck/build/e2e（I5:r385–406，I9:r4、r8），PR 评论 #138 说明第一次 Vitest **5 failed / 98 passed**，机器 load≈33；其输出被 worker 自己的 `grep` 过滤，**失败栈和错误全文无法回放**。后两次在 load≈25/22 下均 103/103 exit0，typecheck/build 与 e2e 58 passed。Issue 负责人 #140 08:15:43 将证据改为“同提交实测”，并断言“无并发条件下连续两次”足以排除代码问题（I9:r4，I1:r4）。这个“无并发”与记录里的 load≈25/22 不一致；两次通过支持该候选可通过，但不能证明首轮 5 失败都只是负载噪音。高负载、真实 HTTP server 定时断言是合理竞争解释，代码与设施的间歇性失败仍未被原始错误排除。修复层是**结果解释与原始诊断保留**：保留首次完整 Vitest 日志或在等负载条件下复现，比较五条失败的具体错误，再决定归因。无需因此否认 `6f272e7` 上的两次成功。

**重锚成本。** worker #129/#131 对 `bab2b11` 作“不再提交”承诺后仍做 packet 更新到 `6f272e7`；Issue 负责人 #132 因 head 变化要求重跑，随后才接收 #135/#138（I9:r4、r8，I1:r4）。根因是“最终 packet 文案”晚于“最终证据 head”落地，验收门禁按提交精确匹配自然失效。把 packet 当前态在验证前写齐、验证后才发布最终 head 承诺，可减少重锚；但本次补跑确实把证据落在 `6f272e7`。

## 2. M5：浏览器层角色前提被细分，独立小 PR 已预备但未发布

PR #15 评论 #141：worker 临时为个人仓库加入 `pw-triage`/`pw-maintain` seed 与 `repo_grants`，临时 scratch Playwright 两条 2 passed、16.6s，并恢复工作区，`6f272e7` head 未变（I9:r43–70）。Triage 可看元数据与关闭按钮、不能编辑/评论，服务端评论 403；Maintain 可编辑并保存标题。这是一次真实操作，支持两档实现路径，却因临时测试未纳入仓库而不能提供可重复验收。Issue 负责人 #142 接收后把原“等 M2 才能复验两档”的前提改为：PR #15 合入 develop 后由同 worker 基于新 develop 发独立小 PR，补两个账户、授权、正式 e2e 与 seed 文档；M2 仍是 `acme-demo/*` 组织仓库权限场景的前提（I9:r72–81，I1:r4）。这是**依赖拆分的有效纠正**：个人仓库角色档只需要直接 seed 授权，组织仓库场景才需要 M2。

worker 随即在 PR #15 物理工作区做了五文件未提交增量与补丁保存（I9:r91–119，I2:r6–23）。预备 spec 首次 API 创建返回 401，两条失败，因为使用 `signIn` 后没有等会话稳定（I2:r24–35）；改用 `signInAndWait` 后针对两档的 2/2 通过、后端 103/103（I2:r38–42）。因此不是 M5 产品实现缺陷，是**新验收代码的等待条件缺失**，由正式场景反向揭示；旧一次性 scratch spec 没有调用需会话已建立的 `createIssue`，故未触发。全量 e2e 在 I2:r47 开始，I2:r48 仍未产出终态；不能说小 PR 已通过全套。直到截点 PR #15 仍 open、`6f272e7`，小 PR 未创建，worker 的增量仍是工作区未提交状态，顺序由 #142 明示。

## 3. M5：M2 合入使“可合并”再次变成有冲突候选

Issue #8 后续会话看到 PR #13 已并入 `origin/develop @ e9390cc`，而 PR #15 head 仍 `6f272e7`（I1:r10–13）。对当前 develop 与 PR #15 的 `git merge-tree` 退出 1，内容冲突在 `backend/src/app.js`、`backend/src/seed/all.js`、`backend/test/helpers.js`、`frontend/src/contracts/copy.ts`（I1:r12–15）。先前 #137/#140 的“可继续合并”只针对 `f6e326c` base；M2 上线后必须重新整合并核对这些共享接线/契约文件。证据表明的是**预期并行开发整合冲突**，不是 PR #15 实现失败。下一轮判别证据是以 `e9390cc` 为 base 的冲突解决 diff、四处模块接线语义、以及最终合并 head 上的检查；特别防止为了合并而丢失 M2 与 M5 任一侧的路由、seed、权限和 copy 键。

## 4. M4a：旧候选通过后，短 hash 直开缺口与文档同步被发现

PR #16 worker 在 `e10ebb5` 合并 develop 到 `f6e326c` 后，报告 `5228a3e` 上 Vitest 91/91、typecheck、e2e 47/47（I11:r402–555，Issue #6 评论 #144）。一次失败是合并后 `frontend/dist` 未重建，旧 `RepositoryMissing` 仍渲染 `Not found`，重建后通过；另一次高负载导致多例超时并被终止，随后 load≈5.6 时复跑通过。旧 `24a6ed7` 平台路径 PASS 没有在 `5228a3e` 上重跑，不能把它写成同 head 的平台证据。Issue #6 负责人核对 `e2e/content.spec.ts` 后指出，当前 47/47 里的新增一条来自 PR #14，并未覆盖验收原文要求的“私有仓库短 hash 直接打开 `/commit/:rev` 无内容泄露”（I7:r4、r10–13；PR #16 评论 #145）。worker 在 `9012550` 只改该 spec，新增该路由防泄露与 README 全文本两条断言；负责人核对 diff 为一文件 +22/-1（I7:r15–21）。这补了**覆盖形态**，还没有在该 head 上得到最终全套结果。

Issue 负责人另指出两项已约定回填未完成：`docs/acceptance-plan.md` 缺 M4a 的 `Commits`/`Changed files`/`Compare changes`/`Branch`/视觉隐藏增删行 token，packet “最小分支端点待根确认”仍未改为 #96 的已确认；PR 正文 §9.14 过期引用已改成 §9.16（I7:r17–24、r29、r55）。这是**共享决定已经发布、消费文档未同步**的问题：下游 #7/#9 可能从旧 packet 读到“未决”，最终整合验收也可能漏 M4a 名称抽查。应在最终候选一次补齐，而不是只在评论中留修正。

## 5. M4a：新 develop 又前进，独立 clone 与验收边界清楚

PR #13 合入后 develop 前进到 `e9390cc`，PR #16 `9012550` 的 merge-base 仍是 `f6e326c`；Issue #6 负责人在自己的 issue 工作区用 merge-tree 发现实际内容冲突两处：`backend/src/app.js` 的 org router 与 content router 相邻插入，`frontend/src/contracts/copy.ts` 的 org 与 content 文案块相邻插入；`docs/seed-data.md` 与 `routes.tsx` 自动合并但需语义核对（I7:r15–28）。PR #16 评论 #149 要 worker 合并新 develop、补两项文档、在新 head 重跑 Vitest/e2e/platform，再由 Issue 负责人验收后合并（I7:r29、r37–38、r55）。截点 head 仍 `9012550`、PR open、Issue open，**后续结果未知**。同名 PR head 在不同独立 clone 中出现是正常读取/交接，不能视为共享同一物理 worktree；I7:r6 的 Issue 工作区与 I11 的 PR 工作区路径不同。负责人没有改 worker 工作区，而是发布核对与任务，符合已裁决的合并归属（PR #16 #128）。

**需纠正的文字。** Issue #6 正文和 PR #16 worker 曾把 `f6e326c` 写成包含“PR #15”；提交日志显示它是根的 §4/§9.15 文档裁决，PR #15 此时仍 open（I7:r4、r15–16，I9:r10–14）。`f6e326c` 的确携带 M5 权限契约，**不包含 M5 PR 实现**。这一点会影响跨链验收是否误以为 M5 已进入 develop；下一轮应以 merge commit 列表而非文字标签确定实际基线。

## 6. 通知/交接边界

snapshot-02 中 PR #16 评论 #145/#147/#148 在 `braid pr view` 输出显示“待投递”，但 worker 后续实际用 `braid pr view 16 --comments` / `braid comment view 125 --thread` 主动读取过 #145 与相关线程并补了用例（I11:r556–580）。PR #15 的 #132 也由 worker 主动查询/回应（I9:r4、r8）。因此 **queued 只表示原生自动评论输入当时还未送达，不等于 worker 没有通过 CLI 消费评论**；也不能用 #145 的队列状态解释其补用例前的遗漏。相反，snapshot-01 的 #110 在旧候选 PASS 前是否消费，须依先前报告的原文时序判定，不可用这里的后续 CLI 查询倒推。I7:r55 的 #149 截点仍 queued，尚无 worker 消费证据。

## 给下一轮的最小判别点

1. **PR #15**：以 `e9390cc` 后的新 head 核对四处冲突解决、同 head 的验收；小 PR 必须在 #15 合并后从新版 develop 发布，当前五文件只是准备稿。
2. **PR #16**：以含 `e9390cc` 的新 head 核对两处冲突、两项文档回填与 `9012550` 两条新增 e2e；收全量与平台路径结果，最后由 Issue #6 负责人按 #128 验收/合并。
3. **失败归因**：M5 的首次 5 失败缺堆栈，M4a 的旧 dist 有明确重建判据；不要将所有失败统一归于高负载，也不要让旧 head 的 PASS 代替新候选。
