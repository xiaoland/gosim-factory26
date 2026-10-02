## 当前任务说明（task packet，随时更新）

需求来源：`/workspace/template/.factory26/20260929-042409-1202e245/input/`（requirements.yaml 34 条原子需求 + reference/ 27 张截图）。
交付：满足全部需求的 Web 应用（frontend/ + backend/，平台 npm 安装/构建/启动兼容），经 develop → main 整合 PR 交付。

## 权威入口
- 方案与契约（develop 分支 docs/）：product-plan、architecture（§9 修订记录随裁决增长，与实现一致）、seed-data、acceptance-plan、ui-reference-notes
- 决定记录与依赖图：本 Issue 评论 #1（现行有效）；契约增量裁决（6 项采纳）thread 1（#7/#8）；M3 期契约裁决 thread 43；Access denied 裁决 issue #4 评论 #73（PR #14 落地）；M4a branches 归属 issue #6 thread 92（#96）；Issue 元数据/关闭重开角色集合 thread 112（#112/#118，docs §4/§9.15 已落地 `f6e326c`）；PR #16 合并归属 PR #16 thread 91（#127/#128）；M5 前提闭合裁决 PR #15 thread 115（#141/#142、#162，**合并动作归根**，PR #17 #178 澄清）；grep 修复处置 thread 188（#189 裁决、#228 证据、#229 根核实）；**M6a seed 塑形裁决 thread 234（#242 + 边界补充 #245/#246）**；**M4b 契约裁决 thread 237（#244：五项）**
- 已解决问题清单（历史归档，含证据链接）：本 Issue **评论 #207**，正文不再维护
- 任务包：PR #2 分支 docs/task-packets/foundation-pr-2.md（"Next action" 一节已被合入事实取代，其余有效）；各子 Issue 正文即其任务入口；各 PR packet 见对应分支 docs/task-packets/
- 共享仓库：origin develop（工作基线）、main（最终交付）

## 当前状态（2026-09-29T12:0xZ 核实；develop head `5b6c7d4`；#3/#4/#5/#6/#8 已关闭）
- **已合入 develop**（merge commit）：PR #2 基础 `c338578`；#3 M1 → PR #12 `a619edd`；#5 M3 → PR #11 `53532a0`；PR #14 Access denied `d70e6ac`；#4 M2 → PR #13 `e9390cc`；#8 M5 → PR #15 `2eed74e`；PR #17 M5 前提 `41bf131`；#6 M4a → PR #16 `4a8f3c9`；grep 修复 → PR #18 `5b6c7d4`。
- **活跃项 — 批次 3 全部开出 PR，实施中**：
  - **#7（M4b）→ PR #19**（head `braid/issue-7-m4b` @ `5cdc7a6`；设计 @deepseek-15 #236/D1–D11，实施 @deepseek-17）；5 项契约变更已根裁决（#244）。
  - **#9（M6a）→ PR #20**（head `braid/issue-9-m6a`，packet `2d03591`；设计 @glm-16 #235，实施 @deepseek-18 #238/#239）；seed 塑形方案 C 已根裁决（#242，边界终版 #246），实施无剩余未决项。
  - 两人按惯例：实施 + 全量证据（Vitest/typecheck/e2e/platform-path，含首轮失败原文）登记 PR → 根核实（对照 #242/#244 清单 + 平台证据 + `--match-head-commit`）后合并。
- **批次 4**：#10（M6b，← #9 合入后指派）。

## 负责人
- 根统筹与最终整合：@glm-1。已闭环：基础 PR @deepseek-2；#3 @deepseek-3（PR #12）；#5 @glm-4（PR #11）；PR #14 @deepseek-8；#4 @glm-7（PR #13）；#6 @deepseek-9（设计+验收/合并）+ @glm-12（PR #16 实施）；#8 @glm-10（设计+收尾）+ @deepseek-11（PR #15）+ @deepseek-13（PR #17）；grep 修复 @deepseek-11（PR #18，线索 @deepseek-13）。
- 在办：#7 → @deepseek-15（设计）+ @deepseek-17（PR #19 实施）；#9 → @glm-16（设计）+ @deepseek-18（PR #20 实施）；#10 待指派（批次 4）。

## 跨模块前提（下游任务包发布时对齐）
1. **D3 编号序列**（issue #8 评论 #89）：issues 与 PR 编号**不共享序列**（各表内 MAX+1）；已随 #9 交接（#231）对齐，若发现必须共享序列的需求依据先回 issue #8 thread 85 裁决。
2. **branches 端点唯一**（issue #6 thread 92 #96，M4a 已生效）：`GET /branches` + 最小 combobox `Branch` 归 M4a；#7 扩展 REQ-4-3-1 在其上扩展/替换（替换为 button `Branch <当前分支>` + `Find branch`，属已登记演进，断言变更按 #244 第 1 项记 §9 新条目）；保持 REQ-4-1 THEN2 可观察，`main-only.md` 不移除。
3. **seed 证人钉住 + M6a 塑形（#242 终版）**：`main-only.md` 是 REQ-4-1 THEN2 唯一种子证人（issue #6 评论 #92）；`Improve onboarding` 挂 M6 自有分支（pr-onboarding 类，= main + 1 自有 commit，diff={src/search.ts modified, 1 added}，3+/1−）；feature-search 追加 1 个自有 commit（只改 src/search.ts、只增行）；`Fix search`/Closed/Draft 用自有分支；`test` check 不预置行（缺省 pending）；`/pulls/compare` 路由批准（M4a `/compare` 保留）。REQ-6-2-2 GIVEN "one commit ahead / modifies one file" 与证人钉住不可同时成立 → **验收以 THEN 为准**，偏差须在 seed-data/architecture §9/acceptance-plan 三处登记（链接 #242）。
4. **copy 键不重复定义**：`errors.accessDenied` 由 PR #14 引入；既有键直接消费，新文案进 copy.ts。
5. **Issue 元数据谓词**（thread 112/#118，docs §4/§9.15）：指派/标签/里程碑/关闭重开 Issue 用显式集合 `{triage, maintain, admin}`（`permissions.canManageIssueMetadata`/`requireRoleIn`，禁止 roleAtLeast）；PR 标签/里程碑复用同一谓词，PR 关闭/重开按 REQ-6-6 另立集合 `{PR author ∪ maintain ∪ admin ∪ 组织 Owner}`；D9 不变（已随 #9 交接 #231）。
6. **M2/M5 seed 权限档证人**（PR #15 thread 115 #153/#165）：`pw-triage`、`pw-maintain`（maintain/triage @ acme-docs）可复用（勿改授权）；组织仓库权限断言消费既有 M2/M3 seed，不新增行。
7. **M4b seed 与页面契约（#244）**：acme-docs 新增 `release` 分支（head=main 头，零新 commit）；`docs/guide.md`→`docs/overview.md`（仅文件名，commit 内容/增删数不变）；`alice-dev/protected-sandbox`（public，main+规则）归 M4b REQ-4-4 证人，**M6a REQ-6-1 用 `alice-dev/protection-lab`**（#239 已批准）；分支元数据 migration v3 显式列（`branches.created_by/at`、`repos.default_branch_changed_by/at`）；Settings→Branches 页 M4b 建页拥有 Default branch 区、M6a 同页追加保护规则区（先合入者建页）；AppShell 搜索框复用（URL `q` 回填、Path 过滤用普通 textbox）。
8. **共享断言与树前提（#240/#245/#246）**：M6a 不得改 `ACME_DOCS_TREES.searching` 的 `README.md`/`src/search.ts` 内容、不得给 acme-docs `main` 追加 commit；M4b 写隔离只写 `pw-branch-*`、不推进 main 头；M6a 自有 commit 经共享行 diff 助手写 `commit_files`、新 commit `created_at` 晚于 `Add main-only notes`；`backend/test/content.test.js` 分支穷举行由**后合入者按对方结果补齐**；M4a 断言更新以 #246 清单为终版，超出须回报根。

## 未决问题
1. Read/Triage 的 UI 可见性个别裁决点 —— 由模块负责人在子 Issue 评论登记后实现（#5 已闭环 3 条；#3 的 D1/D2/D3 条件性裁定保留；#8 的 D1–D9 已含 advisor 复核）。
2. 契约变更纪律：实施中发现 docs/ 契约需变更 → 先在对应 PR/子 Issue 提出，根 Issue 决定后更新文档再合入。

## 下一步
1. **跟进 PR #19（@deepseek-17）/#20（@deepseek-18）实施与证据**：候选开出后根核实（#242/#244/#246 清单对照 + 平台/测试证据 + `--match-head-commit`）后合并；两 PR 共改 `content.test.js` 穷举行等处，后合入者补齐，必要时按顺序合并。
2. **批次 4**：#9 合入后指派 #10（M6b，← #9；分支场景受益于 #7）。
3. 全部业务模块合入后：创建 develop → main 整合 PR，在最终候选上执行全量 E2E 与平台启动验收（含 Triage/Maintain 与组织仓库断言；留意 PR #16 #175 登记的 M1 重启用例高负载抖动），交付并用中文说明结果。
