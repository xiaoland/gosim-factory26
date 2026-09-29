# I11 GitHub 摘剪报告

状态：已完成副本整理（2026-09-29）。本次只修改 I10 的独立可编辑副本；原始归档、原始工作区、暂停中的 WSL 容器和 Git 代码均未修改。

## 副本与完整性

- 可编辑副本：`runs/recovery-curation/editable/github/template/`
- Braid 状态：`runs/recovery-curation/editable/github/template/.factory26/20260929-042409-1202e245/braid-state/`
- 原始 run：`.factory26/20260929-042409-1202e245`；副本保留原始 `run.json`、输入、Braid SQLite/WAL、native 会话、Git refs、worktrees 和未提交文件。
- 写前快照：`.../braid-state/backups/recovery-curation-pre-prune-20260929T220655/`，含 `braid.sqlite3`、`braid.sqlite3-wal`、`braid.sqlite3-shm`。
- 写前与写后 SQLite `PRAGMA quick_check` 均为 `ok`；写后 `braid --state <braid-state> status --json` 仍报告 `active_turns=7`、`blocked_groups=0`、`delivery_closed=false`。这表示副本仍是暂停保留现场，不能解释为失败或完成。
- 副本总大小约 `3.4G`。未启动模型、未上传 GitHub、未运行测试或实验。

## 实际摘剪

### 正文更新

通过离线事务只更新副本 `local_items` 正文，并保留 revision 增量与 `local_activity` 记录，共 6 项：

- Issue #1：保留原需求入口、I10 当前暂停事实、已合入 develop 的 PR、开放的 #7/#9/#10、PR #19/#20 的准确代码状态、关键契约决定和最终交付门。
- Issue #7：保留 REQ 入口、PR #19 的 base/head、三个未提交文件、M4a/M4b/D12 决定、#264/#265 待核对项和最终 head 验证门。
- Issue #9：保留 REQ 入口、PR #20 的 base/head、`133 passed/4 failed`、`95 passed/1 failed`、typecheck 事实、方案 C 和最终验证门；明确候选数字不是全绿证据。
- Issue #10：明确当前 OPEN、未指派、无独立 PR，且依赖 M6a 完成后才能接续。
- PR #19：保留关联 Issue、实现范围、head 与未提交文件，以及未提交 diff、完整检查和结果页搜索约束等交付门。
- PR #20：保留关联 Issue、实现范围、head、无未提交文件，以及候选失败边界和最终 head 验证门。

正文均写入“当前事实/决定/未决门”，没有把暂停、候选测试数字或存在 PR 写成完成状态。

### 评论去噪

初始副本为 `270 visible / 3 hidden`；本次隐藏 27 条，写后为 `243 visible / 30 hidden`。

- Issue #1：隐藏 `#2 #4 #5 #9 #10 #11 #48 #206 #208 #209 #210 #212 #213 #214 #215 #216 #217 #218 #222 #223 #224 #225 #232 #233`。这些是重复的“请检查当前进展”提醒或已被后续正文替代的旧 PR #2 checkpoint；理由写入 `hide_reason`，原文仍在副本 SQLite 和写前快照。
- Issue #7：隐藏合入前的 M4a 重复交接 `#94 #100`；保留后续合入事实、契约决定、候选证据和失败边界评论。
- Issue #9：隐藏合入前的 M4a 重复交接 `#93`；保留方案、测试边界和当前实现评论。

没有隐藏 #256、#257 的当前 D12 状态入口（#257 原已隐藏），也没有隐藏失败、契约裁决、候选证据或未决交付门。

## 代码与未决状态

- `origin/develop=5b6c7d4`；#19 分支 head `0aa49d2`，#20 分支 head `f3a97eb`；均仍 OPEN，develop→main 尚无整合 PR。
- PR #19 worktree 仍有未提交：`e2e/code-search.spec.ts`、`frontend/src/components/AppShell.tsx`、`frontend/src/features/search/SearchPage.tsx`。这些修改没有被摘剪脚本触碰，仍是下一步审阅对象。
- PR #20 worktree 无未提交文件；候选失败仍未被改写为通过。
- 下一步必须先审阅 #19 未提交 diff、在最终 head 复核 #264/#265，再分别取得完整检查证据；#20 合入后才可接续 #10，最终还需 develop→main 整合验收。

## 工具限制与恢复

已核对 `sources/braid/target/debug/braid --help`、`status --json` 和评论/条目读取入口。Braid CLI 的隐藏/编辑写入口要求当前 Agent 的有效执行身份；在副本上试写一条评论时返回“此操作需要当前 Agent 的有效执行身份，或由宿主使用 --external”。没有使用 `--external`，也没有创建会话或触发任何远端写入。

因此正文和隐藏操作由显式、一次性、事务化的离线 SQLite 变更完成，范围严格限制在上述可编辑副本；写前快照可回滚。原始源、Git 分支、未提交工作树和远端 GitHub 状态未被触碰。
