# I10 GitHub 接续整理包

日期：2026-09-29。范围是暂停后的只读整理；不恢复、不启动、不修改原始 DB、运行代码、Issue/PR 或 Git。原始容器保持 Docker `Paused=true`：`f26-continue-db0f28e3288046`（GitHub）与 `f26-continue-a2ce3ac2d41459`（Sheet）。

## 来源与证据

- 取样定义：[delivery-estimate/report.md](../../observations/delivery-estimate/report.md)、[capture.py](../../observations/delivery-estimate/capture.py)、[latest.jsonl](../../observations/delivery-estimate/latest.jsonl)。报告取样时间为 2026-09-29 19:42–19:44 CST；本次远端只读核对基于 WSL 原 workspace：`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--github-7fe42a1248f9d8/workspace/official-generation/template/.factory26/20260929-042409-1202e245`。
- 已有全量审查：[run-audit/github/report.md](../../run-audit/github/report.md)；本包不重复做全量分析。
- 原始 Braid：`<workspace>/.factory26/20260929-042409-1202e245/braid-state/braid.sqlite3`、`status.json`、`origin.git/`、`worktrees/`。

## 暂停时状态

GitHub Braid status 读数为 `active_turns=7`、`blocked_groups=0`、`delivery_closed=false`。远端/运行状态不得解释为失败；当前是用户要求保留现场的暂停态。根 Issue #1 OPEN；Issue #3/#4/#5/#6/#8 CLOSED；Issue #7/#9/#10 OPEN。PR #2/#11/#12/#13/#14/#15/#16/#17/#18 MERGED；PR #19/#20 OPEN。

## 已合入交付

以下以 `origin.git` refs 和 Issue/PR 状态为准，已合入 `develop`：

| 范围 | 事实 | 证据 |
|---|---|---|
| 基础 | PR #2 merged；基础脚手架与共享契约 | `refs/heads/braid/pr-2=abb6f6b` |
| M1 | Issue #3、PR #12 merged；head `af2d06d` | Issue #3 reason、PR #12 |
| M2 | Issue #4、PR #13 merged；PR #14 的 Access denied 修复也 merged | `d62907d`、`9bedf84` |
| M3 | Issue #5、PR #11 merged | `15c79a4` |
| M4a | Issue #6、PR #16 merged | `c33e8ee` |
| M5 | Issue #8、PR #15/#17 merged | `2a51605`、`425b97c` |
| 工具修复 | PR #18 merged；e2e shell 引号修复 | `1ef02cd` |

`origin/develop=5b6c7d4`，`origin/main=2914d2d`。因此“已合入 develop”不等于最终 main 交付；尚无 develop→main 整合 PR。

## 未合入与未提交进度

### PR #19 / Issue #7：M4b

- 最新已提交候选 `0aa49d2`，此前 `e3c147d` 已落地 D12：`commit_files.status` 统一为 `added|modified|deleted`，移除 `deleted→removed` 写入映射；评论称 D1–D12、Vitest 12/151、e2e 113、platform-path exit 0，但这些是 Agent 交接证据，必须在恢复后按最终 head 重核。
- 当前 worktree `worktrees/pr-19/pi-deepseek-fast-g1` 有未提交修改：`e2e/code-search.spec.ts`、`frontend/src/components/AppShell.tsx`、`frontend/src/features/search/SearchPage.tsx`。这是最重要的可保留生成进度，不能丢弃或直接当作 PR head。
- 评论 #264/#265 抓到“结果页内再次搜索”丢失仓库范围/过滤值；#268–#273 记录 D12 更正及交接。恢复时先读取 worktree diff，再决定是否提交。

可应用的精简正文：

> M4b covers branch selection, branch-scoped code search, commit/file browsing, and web editing. Preserve the D1–D12 contract in the Issue body, especially `commit_files.status=added|modified|deleted` and the result-page repeat-search scope/filter invariant. The candidate head is `0aa49d2`; after any uncommitted changes are resolved, run the listed Vitest, Playwright, platform-path, and migration checks on the final head, then merge to `develop` with `--match-head-commit`.

### PR #20 / Issue #9：M6a

- 当前 PR #20 OPEN，worktree 最近提交 `f3a97eb`；根已采纳 seed 方案 C，Issue #9 评论 #249 列出实施顺序和与 M4a 的 5 处断言联动。
- `origin/develop=5b6c7d4` 尚未包含 PR #20。已有报告中出现 95 passed/1 failed e2e、133/4 Vitest 的候选证据；失败在已登记清单内，不能写成全绿。
- worktree 未显示未提交文件，但仍需恢复后确认最终 branch head 与完整测试输出是否存在。

可应用的精简正文：

> M6a covers branch protection, Checks, and the PR lifecycle. Implement the root decision in #242 and the ordered checklist in #249 as one coherent candidate, including the five known M4a assertion updates. Record exact command, Node version, exit code, and the complete failure list on the final head before merge; do not report the current candidate as all-green.

### Issue #10：M6b

Issue #10 OPEN，当前 `desired_member_login=null`，尚未指派，依赖 PR #20。范围包括 review validity, stale review behavior, inline comments, transactional merge and permission matrix。它是实质功能路径，不是收尾签字。

可应用的精简正文：

> M6b depends on the merged M6a contract and covers review validity, stale reviews, inline comments, transactional merge, and the permission matrix. Before assignment, define the observable states and the smallest repeatable browser/API checks. Do not close the Issue on design or comments alone; require a candidate PR, final-head checks, and integration evidence.

### 根 Issue #1

根仍 OPEN，尚无整合 PR。最终关键路径是：PR #19 与 #20 完成并合入 develop → 指派并完成 Issue #10 → 建立 develop→main 整合 PR → 在最终候选上做完整验收 → 再关闭根并交付 main。根评论中已存在大量重复的哈希、合入树和“无动作”确认，接续时应以最新事实和触发条件为主。

可应用的精简正文：

> Current delivery state: M1–M5 and shared fixes are merged to develop; M4b and M6a remain open, M6b is unassigned, and no develop→main integration PR exists. Continue only from the preserved worktrees and final-head evidence. Delivery requires M4b/M6a merge, M6b completion, a clean integration PR, full final-head validation, and main merge; CLOSED status alone is insufficient.

## 建议隐藏的评论（不在本次整理中执行）

只建议隐藏明显重复、过期或已被后续事实替代的正文，保留原始数据库和可追溯性：

- 根 Issue 的旧“当前进度/仍待合入”评论：被后续 merge 事实替代的 M1–M5 状态，理由是会把已合入事项重新呈现为未完成。
- 根 Issue 评论 #256/#257：#257 已被标为 hidden；若外部镜像仍显示其正文，应继续按 hidden 处理，避免把清单内失败误读成无范围失败。
- 根/PR 中对同一 README 哈希口径的重复交叉确认（#496–#500 类评论）：保留一条最终更正（blob 与内容 sha256 分开），其余 hide，理由是重复确认不新增判据。
- PR #19 在 `cf2762e`、`e3c147d` 之前的已过期交接评论：若正文仍显示为当前候选，hide 或标注 superseded；保留 #269–#273 的 D12 最终链。

不隐藏失败证据、验收输出、责任更正或会改变触发条件的评论。实际 hide 必须由有权限的接续 Agent 在恢复后按当前评论树核对，不依据本包直接批量操作。

## 有效验收与未决

- 有效：最终 head 上真实 Node/依赖环境的完整 Vitest、Playwright、typecheck、build、platform-path；PR #19 的迁移/搜索/编辑边界；PR #20 的 branch protection/Checks/PR lifecycle；Issue #10 的 review/stale/inline/merge 权限矩阵；最终 develop→main 合入树与应用启动。
- 无效替代：只看 Issue CLOSED、只看 PR merged、只看历史 head 的 PASS、只看评论中的计数、把当前未提交 worktree 当作 PR head、把 paused 当作失败。
- 未决：PR #19 未提交 diff 是否完整可用；PR #20 最终候选及失败清单；Issue #10 的负责人/方案/实现；M4b 与 M6a 的联动回归；最终整合 PR 尚不存在。

## 接续顺序

1. 维持两个 I10 容器 paused，复制原 workspace 与 Git/worktree 到独立整理副本；原始现场只读保留。
2. 在副本先审阅 PR #19 未提交 diff，再核对 PR #20 最终 head；不把未提交内容自动提交。
3. 依据现有 Issue/PR 正文精简正文，隐藏已确认重复或过期评论；保留失败、判据和责任边界。
4. 只有恢复运行获得新的最终 head/验证证据后，才继续 M4b→M6a→M6b→整合 PR；本 packet 不授权任何启动、恢复、提交、部署或评分。
