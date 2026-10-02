# PR9 增量阅读：PR10 合入后的 B 回归核对

## 源身份与顺序

本增量只读 `increment/coverage.json` 指定的 PR9 两份材料。两份文件共享 UUID `01a0ec30-6737-76f7-b57e-f4263514ce49`，但属于不同原生载体和时段：

1. `sessions/.../2026-09-29T08-03-10-263Z_01a0ec30-6737-76f7-b57e-f4263514ce49.jsonl`：24 行，session 头 08:03:10 UTC，保留旧段；用户事件 08:03:12 是 comment 171 edited 的 PR9 处理。
2. 顶层 `.../2026-09-29T08-03-10-263Z_01a0ec30-6737-76f7-b57e-f4263514ce49.jsonl`：61 行，顶层 session 头被重建为 08:10:00 UTC；用户事件 08:10:14 已变为“PR10 comment 173，PR10 merged at a592c3e”。coverage 明确标为 `prefix_preserved=false`，所以不能把它当作 08:03 段的逐字前缀。

重复材料按第一次原处引用；两段的身份、时间和动作差异均记在 `increment-pr9-read-ranges.json`，未改全局 coverage ledger。

## 08:03 旧段：comment 171 处理及已有回归证据

旧段读取 PR9 正文和 comment #173 所在 PR10 thread，确认：

- PR9 已 MERGED，合入 `15abbf6`；PR9 分支 head 记录为 `3641902`，该提交链只改 `tasks/issue-4-b/packet.md`，不改应用树。
- comment #171 作者元数据是 `deepseek-6`，不是 #158/#159 证据的作者；#158/#159 的 `author.login` 是 `deepseek-7`。packet 将“第二来源证据”的归属修为 @deepseek-7，并把引用改成 `PR #9 comment #171`。
- `comment #159` 的保存日志 `/tmp/ds7-rev5/full-e2e-d6ca6d4.log` 被重新 grep：`e2e/worksheets-structure.spec.ts` 的 10 条 B 用例（编号 26–35）均 PASS，整批 `35 passed`；先出现 `==> shared static gate`，再进入 Playwright。这个证据是 PR10 候选 `d6ca6d4` 上的独立复核，不是本段新跑出来的结果。
- 当时 PR10 仍 OPEN、`origin/develop=e63efc6`，所以 comment 171 中写的回归点 ① 尚未触发。此段正确结论是 B 无动作，不应提前把 C 的回归标成已结案。

## 08:10 重建段：PR10 已合入，回归点 ① 被触发

顶层 61 行完整动作链显示：

1. 用户通知 PR10 以 merge commit `a592c3ebf4e86d0ce1f82c39bea4579b98af4140` 合入 develop。
2. 工具核对 merge parents 为 `e63efc6` 与 `05b7446`；`git diff --stat 05b7446 origin/develop` 为空；`git diff --stat d6ca6d4 origin/develop` 只有 `tasks/issue-5-c/packet.md`。树 hash 为 `origin/develop=05b7446=0836d6465b21ff6a7b5bcd65a65a5c2de0afcf14`，而 `d6ca6d4` 的树为 `ff64d2fb...`，差异限于文档。
3. B 相关文件 hash 逐项复核一致（包含 `e2e/worksheets-structure.spec.ts`、`backend/src/store.js`、`backend/src/ranges.js` 等）。因此按 packet 的快路径，已有 `d6ca6d4` 双来源 35 passed 证据足以覆盖 B 回归；若要本地重跑，必须保留首轮原始输出。
4. 尽管快路径成立，agent 仍启动了 `bash checks/run-e2e.sh` 的本地回归，副本为 `/tmp/b-regr-a592c3e`、`E2E_PORT=37381`。原文给出的理由是想在实际合入候选上取得第一手证据、避免严格读者把“树不完全相等”解释为必须重跑，并认为这样更严谨；但前述验收规则已经明确“差异仅限 `tasks/**` 即可引用既有双来源证据”，所以这不是新增的独立验收义务，而是 agent 自选的额外复核。捕获的最后工具结果（顶层 L61，08:12:25.990 UTC）显示 frontend build 完成、Playwright 启动，35 用例中前 8 条通过，包含公式结果/依赖/循环/越界刷新等；该源没有完整 35 passed、退出码或 cleanup 结果。

### 证据边界

PR10 thread 的 comment #175（在顶层 L57 工具结果中完整读取）随后声称最终 head `05b7446` 上 cold platform path `PASS/EXIT=0`、非跳过完整 e2e 35 passed、vitest 116/105 和 typecheck 0，并再次确认 `origin/develop^{tree}=05b7446^{tree}`。这是 PR10 负责人交回的上游证据，不是 PR9 顶层 08:10 本地回归的完成结果；总账应分开标注来源。

本 PR9 两源在 L61 后没有记录完整回归的终态；本报告不把源外的后续运行信息改写成模型停滞，也不把它当作 PR9 e2e 的 PASS/FAIL 证据。可确认的本地事实仅到 L61 的 8/35。

## 归纳判断

- 回归判据本身正确：先核树；若 develop 与已验候选 app tree 只差 `tasks/**`，引用既有浏览器证据，不必重复消耗一轮完整 e2e。
- 08:10 agent 已证明“无需重跑”的快路径，却基于“第一手候选证据/更严谨”的自选理由启动本地完整回归；这是可预防的注意力/环境成本，不能算 B 或 Harness 缺陷。其后来没有在本源内形成终态，不能补写为通过或失败。
- 08:03 段的 comment 归属更正与 08:10 段的 PR10 合入是两个连续事件；前者不是后者的重复输出。B 侧代码未被增量修改，新增信息主要是回归门状态和证据来源边界。
