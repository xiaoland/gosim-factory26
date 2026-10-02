# DeepSeek 两题：09 是否应退到更早恢复点

结论截至 **2026-09-28 08:19 UTC 的 09 恢复包冻结截面**：现有证据不支持因“半成品旧内容过多”改从 06/07 恢复。08 留下两条需要纠正的协作状态与仍未完成的产品路径，但 Git 提交、PR head、工作区及 Braid 对象都有可定位的接续入口；更早快照也包含相同或更早的需求误读，且会丢失大量已合入成果。应先解决当前模型路由的 429 余额不足这一外部阻断，再在 09 的保留工作区按 **真实 Git/需求/受检提交** 校正责任与验收；429 对早快照同样成立，不能当作当前上下文不可恢复的证据。本页不查询 09 实时活跃性，该支线由另一调查者负责，也不预言 09 后续能否交付。

## 来源与候选点

WSL `runs/e20260928-02-deepseek-direct/attempt-09/restore-point-facts.json` 列出 06→07、07→08、08→09 的冻结工作区；`{github,sheet}-workspace-provenance.json` 明确 09 源于 08 各自的 `workspace/official-generation/template`，`recovery-package-verification.json` 有两个 `mode=workspace-resume`、冻结 DB SHA 与 `problems=[]`。这证明 09 的**起点**包含 08 对象/工作区，不证明 09 运行后状态未再改变。07/08 停止是获授权热修中断，不是生成自身失败；09 尚无可用最终评分。

| 可选来源 | GitHub 冻结事实 | Sheet 冻结事实 | 退回的实际代价 |
| --- | --- | --- | --- |
| 06→07 包 | 9 Issue OPEN、1 PR MERGED；大量功能未派发 | 7 Issue OPEN、3 PR MERGED、1 OPEN | 回到共享基础早期，几乎整个后续交付须再做；并不消除 Sheet 初始状态/需求判据的早期偏差 |
| 07→08 包 | 6 Issue OPEN/3 CLOSED，4 PR MERGED/3 OPEN；`develop=354b198` | 4 Issue OPEN/3 CLOSED，11 PR MERGED/2 OPEN；`develop=3e55813` | 相比 08 丢失 GitHub 22 个后续 Git commit、Sheet 39 个；两个旧 develop 均是 08 develop 的祖先，后续成果不是无法接上的平行历史 |
| 08→09 包，当前选用 | 2 Issue OPEN/7 CLOSED，10 PR MERGED、PR #5 CLOSED、PR #12 OPEN；`develop=afee849`、`main` 仍初始 | 3 Issue OPEN/4 CLOSED，18 PR MERGED、PR #19 OPEN；`develop=7f4216e`、`main` 仍初始 | 保留 PR #11/REQ-6a、Sheet PR #15/#17/#18 等已合入成果及尚未合入的分支；需主动处理下述不一致与最终验收 |

Git ancestry 在 08 冻结 `origin.git` 上只读核对：GitHub `354b198` 是 `afee849` 祖先，差 22 commit；Sheet `3e55813` 是 `7f4216e` 祖先，差 39 commit。commit 数只描述会丢的历史，不等于有效需求数或质量分。归档路径：08 冻结运行在 `attempt-08/generation/runs/pi-braid--hackathon--github-97914b9e3158cf/` 与 `...sheet-d478f7dc8ff84f/`；相应 Braid run id 仍是 `20260928-030347-78b10c07`、`20260928-025746-66feadac`。

## 真正需要纠正的状态，而非仅“旧内容多”

**GitHub PR #5 对象状态落后于 Git。** 08 根先在真实 Git 上以 merge commit `2d29c4d` 纳入 PR head `3325873`，随后 `braid pr merge 5` 因 head 已在 base 内拒绝，根把 PR 标为 CLOSED，说明写在 close reason。08 冻结 `develop=afee849` 的祖先图仍包含 `3325873`；不能把对象 CLOSED 当“代码没合入”，也不能把它伪装成 Braid `MERGED`。09 新外部合并语义只对有创建基线的新 PR 精确识别，旧 PR #5 不能倒推原始整合事件；接续时应保留“代码已入 develop / 历史对象为 CLOSED”的事实说明，并从 Git 树审查 REQ-4，不需回退到尚未包含该代码的 07。[08 Git 集成证据](attempt08-progress.md)有具体双亲与原生工具链。

**Sheet 已关闭 Issue #7 的全覆盖声明被后续缺口推翻。** 08 的 #7 评论 #199 在 `develop=6bb8192` 上报告 `REQ5_ALL_PASS` 并称四种写路径含范围移动均有校验拒绝断言，于 08:09 UTC 关闭 Issue。08:12 又由相关成员创建 OPEN 的 PR #19，题目明确是“REQ-5-2-1：范围移动端点也走写校验（补齐 range move 的整单拒绝）”；其 head `b89df03` 仍未合入冻结 `develop=7f4216e`，且基于较早 `6bb8192`。这不是评论多的问题，而是**完成口径/覆盖范围失真**。应在 09 将 #19 指回 #7 的关闭声明与原需求，复核 API 层非法移动的整单拒绝、重基到最终 develop 并再次验收；若 #7 的关闭语义要求所有 REQ-5 路径完成，则先重开或在原位置显式标“待 #19”，不可沿用 #199 作为整套产品已完的证据。无需抹去 #7 其他已合入的排序/筛选/透视工作。对应冻结对象和评论来自 08 Braid SQLite；[Sheet 08 截面](attempt08-sheet-progress.md)记录更早的局部通过与环境判据。

**独立 PR 责任尚未闭环。** GitHub Issue #9 的 PR #12 在 07:49:10 留有 head `752a084`、基于 `afee849` 的实现与自检交接；PR 于 07:49:20 曾指派 @glm-11，四秒后移除，08 冻结为 OPEN 且无负责人。不能把 PR head 自检当独立复核，也不能凭短时指派说 09 的新方法已经有效。保留现成分支，在路由可用后为 PR 找可执行的独立负责人，复核原 Issue 设计、受检 head 和最终候选后再整合。历史多数 PR 由 Issue 会话直接实现，是过程承诺没有建立的缺陷，但重跑整个应用也无法追溯改变过去作者；有针对性的独立代码/行为审阅可以补当前交付可信度。[Issue/PR 边界](issue-pr-session-boundary.md)另有官网背景与 09 方法修正。

**Sheet 剩余 REQ-2/REQ-3 的依赖是真实工作，不是脏快照。** 08 冻结 Issue #4 仍 OPEN，其 `issue-4` 分支 `2d9d92f` 有结构端点、undo 快照、共享引擎接线及检查等已提交工作，相对分叉点约 22 文件、2202 行新增；尚未合入 develop。08 07:01 的真实 seeded server 检查为 52 pass/2 fail（Region 删除、恢复快照），不能称全通过；其后是否修好须以 09 新证据判断。Issue #5 的评论 #196 已准确留下“结构 undo 要等 #4 合入，当前检查 1 skip”的门槛；因此 Sheet `main` 尚初始、根 Issue OPEN 是合理未完状态。退到 07 不会自动得到正确 REQ-2/3，只会丢失后续实现和真实失败线索。

## 保留与继续的判据

当前快照的可靠资产是可追溯 Git history、已合入 develop 的具体 PR、仍在分支上的候选及相应局部检查；并非所有“PASS”评论。GitHub Issue #8/PR #11 的 head `e0d6908` 已由根在评论 #55 记录独立复验、以 `afee849` 合入；受检项目含 build、backend 62/62、REQ-6a 89/89 与 REQ-3 回归 19/19，属**有具体提交和动作的证据**，但本审查未重跑，也未证明 46 项最终候选。Sheet PR #15/#17/#18 在冻结 develop 中有对应 merge commits；#18 仅加 CSV 回归，不替代产品全验收。历史错误与通过片段都应按候选提交、运行条件、需求初态分类，不直接拷成最终完成声明。

继续 09 的可操作顺序是：先使模型请求恢复可用，随后以 Braid 对象和 Git 图建立简短当前事实索引；纠正 PR #5 的对象/Git差异、#7/#19 的验收边界、PR #12 的独立负责人；再让现有未完工作线处理 GitHub #9、Sheet #4/#5/#19 并对整合后 develop→main 候选验证。这里是接续判据，不代替参赛 Agent 写应用或直接修改冻结 DB。当前 429 余额不足是独立 P0，换 06/07 源并不能使模型调用成功；若路由恢复后真实发现**无法定位的工作区损坏、关键 Git 历史丢失、同一需求无法从任何原始输入重建正确判据**，才重新比较更早恢复点与局部回滚。现有归档没有这样的证据，不能因沉没成本盲目继续，也不能因陈旧上下文长度盲目清零。

本页没有读取全部 native transcript、没有独立执行应用检查，也没有追踪 09 启动后的活跃消息。08 冻结 PR/Issue 活动与 Git 图为高可信状态证据；测试结果来自此前定向原生核查和附提交的成员报告，最终质量仍待同一整合候选的实际检查或评分。09 的最新增量须另列，不能塞进 08 冻结结论。
