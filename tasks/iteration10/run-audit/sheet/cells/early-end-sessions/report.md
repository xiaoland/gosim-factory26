# Sheet 原生会话 52–62 审查

范围为主 manifest 索引 52–62，11 会话、1,587 条原生记录，现已全部按原生顺序完成语义阅读。`coverage.json` 逐 SID 记录来源和阅读状态。索引 55、56、58 的长渲染曾有显示截断，已以小段补读；机械写入和精确重复在各 `session-XXX-omissions.json` 与 compact 渲染中登记原始行及长度。

## 已确定的因果链

- **F3 浏览器证据从缺口到补齐。** #6 的静态审查在 develop `266f0e4` 发现已有浏览器检查未覆盖越界 `=#REF!` 与移动源不变，只能证明引擎单测而不能证明 UI 行为（`continuation02-root-native/099-2026-09-28T07-00-20-094Z_01a0e6d0-83fe-74c2-91f8-7e3ec07b3e54.jsonl:L1–20`）。索引 56 的 #6 分支 `a845770` 补两条浏览器检查；首轮 `BASE_URL` 缺失与管道接 `tail` 造成假 `PLAYWRIGHT_EXIT=0`，再遇 Chromium `Socket path too long` 全 7 失败（`continuation02-root-native/105-2026-09-28T07-04-31-430Z_01a0e6d4-59c6-722e-9f5c-45a296e259d6.jsonl:L69–85`）；短 TMPDIR 后定向 7 passed / 1 skipped（L102–103）。索引 62 在 rebase 到 `ab5dc1b` 后再次得到 7 passed / 1 skipped，但原生终止前尚未见 PR 或证据评论（`continuation02-root-native/117-2026-09-28T07-32-57-580Z_01a0e6ee-626c-75de-b585-5d546b014fe0.jsonl:L85–86`）。主审后段已证实 PR #22、最终 33/33 与 51 全绿，故这是历史验证缺口及过程误报，**不列最终未修**。
- **PR #9 与 CSV 的不确定测试被后续有效实验分离。** 索引 58 第一轮 CSV 浏览器项目 2 pass / 1 fail，服务器后台作业约 180 秒被回收；用 detached `setsid` 与独立端口重跑 3/3、退出码 0，回贴 Issue #3 comment #158（索引 58 原生记录中段至尾段）。索引 61 又有公式导出用例失败、`PATCH /cells` 500，但服务端日志明确 `Cannot find module .../@app/formula-engine/dist/index.js`，是临时 worktree 复用 symlink `node_modules` 且 rebase 后 dist 消失；重建 dist 后同用例通过（`continuation02-root-native/115-2026-09-28T07-26-18-406Z_01a0e6e8-4b25-7261-bf2d-b3c138da259f.jsonl:L108–112,L159`）。随后的普通后台长跑被回收，日志停在首测，不能当产品失败；整段 detached 重新跑 4/4、`PW_EXIT=0`（同文件 L146–159）。
- **CSV 筛选隐藏行检查最终有审查链。** 索引 55 的 #9 旧 head `65b4f57` 预合并定向通过，head 变为 `01ee744` 后又定向通过，检查分支只改 `checks/csv.spec.ts` 52 行；这不是合并后验收。索引 61 对新的 #9 head `8099339` 加该检查做 4/4（同文件 L159–160）；#9 以 `83f9e38` 合入，`8099339` 与 merge commit 的 tree 相同（L185–195）；检查分支 rebase 为 `08b1062` 并创建 PR #18（L186–195）；在此合并后候选 head 构建双端成功，CSV 4/4、`PW_EXIT=0`（L198–204），整套第二次 30 passed / 1 skipped、`RUN_EXIT=0`、`.last-run.json` passed（L247–277），PR #18 comment #186 与 Issue #3 thread #87 comment #187 回贴（L286–291）。唯一 skip 是既有行列结构 undo fixme。索引 61 截至原生 L333 的 PR #18 仍 OPEN；主审已在后段确认 PR #18 以 `c3058923` 合入，故它也不是最终未修项。
- **move 后 raw/value 分裂曾使 CSV 导出旧值，随后已修。** 索引 59 的独立复核否定空 move 额外 undo 的猜测（`History.push` 有空操作守卫，`continuation02-root-native/111-2026-09-28T07-15-48-645Z_01a0e6de-af25-74f5-86e7-3810e07f1044.jsonl:L45–46`），但发现 A1=`newval` 移到 D1=`oldval` 后 D1.raw=`newval`、D1.value=`oldval`，网格读 raw，`frontend/src/domain/csv.ts` 导出读 value，浏览器 CSV 得 `,,,oldval`（L152–174,L237,L443）。PR #15 comment #161 报告，后续提交 `423181f`/`783ff7e` 修复，API 9/9、函数 3/3，浏览器 CSV 改为 `,,,newval`（L373,L387–418）。历史确定缺陷，**不列最终未修**。这与父主审指出的 pivot 跨表公式缓存旧值是不同路径。
- **32 次 429 造成短时失能，无有效推进。** 索引 62 的 SID `01a0e6ee-626c-75de-b585-5d546b014fe0` 在 07:41:37–07:46:18 连续 32 条 glm 余额/资源包 429；期间只夹杂旧通知，没有新实质动作（`continuation02-root-native/117-2026-09-28T07-32-57-580Z_01a0e6ee-626c-75de-b585-5d546b014fe0.jsonl:L87–125`）。前置的 F3 rebase 及定向验证已经完成，但交付评论/PR 未见于本段；后段 PR #22 补齐。不能把 429 本身归成产品缺陷。

## 其他会话结果与判断边界

- 52、54 是 #6 对已合入 PR #12 / 旧评论的同步复核，没有新的源码变更。57 记录 PR #13 合入 `3e55813` 并发协调评论。60 确认公式栏修复及旧回归在 develop `1d7eca7`，Issue #5 comment #152；没有新代码。
- 索引 61 的 run 脚本第一次全套 30 passed / 1 skipped，但包装命令没有保存 shell 退出码（L247–252）；代理再跑一次并显式记录 `RUN_EXIT=0`（L253–277）。这是后者才可支持退出码断言。该会话还发现自己的直跑辅助脚本通过 `ss` 判端口会误判“无残留”，而 `/proc` 查到两个自己启动的 node 服务，随后精确 PID kill；官方 `run.sh` 留存 RUN_DIR 日志是设计行为（L278–284）。这说明仅凭 `ss` 的空结果不可证明无遗留服务；最终服务清理有 `ps -C node` 复核。
- PR #17 空白下拉校验在索引 59 从 `070168a` rebase 为 `450b0dc`、定向及全套绿，相关通知/comment 有到达和不可达区分（L315–417）。主审已知后续最终状态，审查此段不另断终态。

## 对迭代 10 修复的关系

本单元支持保留作业登记、完成投递、空闲 drain 及验证语义收敛：同一会话多次普通后台长跑被回收又重复唤醒（索引 61 L146–159,L302–333），早期 `tail` 掩盖原命令退出码（索引 56），而真正完成证据来自明确 commit、单份 `.last-run.json`、明确退出码和评论回读。已有迭代 10 PBB 作业登记/空闲 drain/工具完成投递改动与评论合批退订；**具体去重效果仍需新运行验证**。本单元没有独立证据要求再加硬调度规则。
