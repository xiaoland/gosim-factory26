# continuation-03：Sheet 运行成本与 Braid 协作链补查

只读取证截面截至 2026-09-28 11:10 UTC。03 的新运行在 `attempt-09/continuation-03/generation/runs/`；Sheet 实际工作区、Braid 数据库和原生会话继续复用 `attempt-09/generation/runs/` 中的父运行。本文不重复 [token 分析](token-deep-03.md) 的 usage 统计，也不把并行验证的时长相加当作墙钟成本。

为缩短下文路径，`S` 指 WSL 上的 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation/template/.factory26/20260928-025746-66feadac`；`C` 指同一 `attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a`。评论编号和时间来自只读 `S/braid-state/braid.sqlite3:local_comments`，投递状态来自 `local_comment_delivery`。这些是本地 Braid 对象，不是外部 GitHub 评论。

## 两次服务消失：已定位到跨工作项的全局清理

| UTC | 直接动作与独立观察 | 归因边界 |
| --- | --- | --- |
| 09:33:01 | Issue #4 的 GLM 会话执行 `pkill -f 'dist/server.js'`，想清理自己的 API 检查残留；工具结果为 `Command aborted`。Issue #6 的检查日志随后记录六台 per-spec server（CREATE、EDITOR、HOME、CSV、REQ3_CORE、REQ3_INTEGRATION）在 09:33:02–08 逐台 `disappeared`，watchdog 在原 DATA_DIR 重启。| 命令按进程命令行匹配，未限定 Issue #4 的 PID 或工作树；时序和匹配范围支持它杀死 Issue #6 服务。`Command aborted` 也说明这条清理命令自身未正常收尾，不能据此推断每个子命令都执行。 |
| 09:42:07–13 | PR #8 的 DeepSeek 会话先收到 `pbb kill bg002 --stale` 的结果 `bg002 is not running; no kill requested`，接着同一 bash 命令运行 `pkill -f "backend/dist/server.js"`。09:42:10 的工具输出列出 Issue #6 正在跑的 `checks/run.sh` 和六个 `issue-6/.../backend/dist/server.js` PID；09:42:13 下一次 `pgrep` 仅见一台新启动的 Issue #6 server。PR #22 描述记载第二轮 watchdog 在 09:42:12–17 再次重启六台。| 这次有杀前/杀后的原生进程列表，证据强于单纯 watchdog 自报。PR #8 的 `pbb` job 本已停止，后续全局 `pkill` 波及其它 lane。仍没有内核审计记录逐一列出信号发送者和六个退出码，不声称精确 PID 级因果链。 |

原生证据：`S/work/native-homes/pi-glm-fast-01a0e751-0825-7df3-b100-b41d5619f714/2026-09-28T09-20-45-676Z_01a0e751-146c-7111-8394-c1592615f521.jsonl:100-101`；`S/work/native-homes/pi-glm-fast-01a0e759-cdfa-7489-8194-a7aefb3ffb28/2026-09-28T09-30-17-466Z_01a0e759-cdfa-7489-8194-a7aefb3ffb28.jsonl:74`；`S/work/native-homes/pi-deepseek-fast-01a0e75f-95dc-7f00-a80e-035d33f4e0c7/2026-09-28T09-36-39-049Z_01a0e75f-a089-7593-a867-60e4c60e8c7c.jsonl:111-116`；`S/braid-state/braid.sqlite3:local_items(pr:22).body`。

这纠正了 [前次截面](continuation03-progress.md) 的“外部清理尚未定位”：清理者是**同一 Sheet 运行中的其它 Braid 工作项 Agent**，不是已证的 Braid 守护进程行为，也没有证据指向 CPU/OOM。Braid 为各工作项提供独立 Git worktree，但此运行中的 shell 进程共享可被上述 `pkill -f` 命中的进程空间，形成跨 lane 干扰。最小修复方向是让 Agent 及检查脚本只结束自己启动时记录的 PID/进程组，避免全局按 `dist/server.js` 名称清理；是否需要进程级隔离属于后续设计决定。本轮不改运行材料。

## 复验、环境准备与关键路径

- PR #22 只新增 `checks/req3-integration.spec.ts` 的 89 行检查。它的两轮全量结果各为 35 passed / 1 failed / 1 skipped，不同 spec 分别失败；上述服务重启提供了非产品干扰的具体来源，随后单项目 9 passed / 1 skipped。失败造成额外排查与复验，但原生记录不足以把两轮全部用时或每个失败都精确归到 `pkill`。来源：`local_items(pr:22).body`。
- PR #20 的重验有真实收益：#279 报出 CSS 少一个 `}`、使下拉等样式失效，#280/#282 独立确认并阻止旧 head 合并；#301 与最终 head `779c560` 的检查验证修复。#293/#294 又把旧浏览器红例中的错误期望与共享种子污染单独纠正。不能把这些复验一概视为冗余。来源：评论 #279–#295、#301–#305；[前次进展](continuation03-progress.md)。
- PR #23 首轮全量 `run.sh` 在同一内容树上给出 **49 passed、18.7 分钟**和 `.last-run.json=passed`，但没有保存可复核的 shell 退出码（#328）。根在 #330 将退出码列为合并门槛，作者于 10:49:37 启动 `--skip-build` 再跑，#346 回贴 **49 passed、17.2 分钟、`RUN_SH_EXIT=0`**；这是同一 tree 的第二次整套检查，其增量证据主要是退出码。独立复核者 #345 采用 tree 等价和受影响的 `req3-integration` 11/11，没有第三次跑全量；平台 PR owner #344 也明确不重复整套。来源：评论 #328、#330、#334、#344–#346。17.2 分钟是该检查自身运行时间，不等于全部可省墙钟：它与复核及另一个收尾分支并行，但合并明确等待其结果。
- REQ-5 负责人在已验过的 `779c560`（#309/#310）与合并树 `db23b1f` **逐字节相同**的前提下，又在后者执行 `req5-all.sh` 10/10 和全量 `run.sh` 47 passed / 1 skipped、19.0 分钟（#354）。其中新增的 #4↔#7 结构联动 16/16 探针有新覆盖价值；重复的整套检查不因“合并提交”自动新增覆盖。它与 PR #23 收尾并行，不能直接把 19 分钟加在关键路径上。#344 明言多 lane 并行时浏览器单例变慢，但没有资源监测可量化 Braid 并发造成的延长。
- npm 安装、独立 worktree、临时 DATA_DIR 和建服在不同 head 或互相污染的测试之间有实际隔离理由。现有记录能证明部分重复 `run.sh`，不能把所有安装/建服判成无效准备；也没有完整的环境准备分段计时。#344 的错误 Chromium 路径导致一次 11 例即时启动失败并纠正，属于工具参数失误，而非产品红例或 Braid 调度失败。

## 交接、共享契约与通知

09:24–09:27，根 #217 把结构 undo 的端点与 History 侧分给不同负责人，#220/#223 冻结 `relatedSheets`，#225 提供用例片段；后续 #285–#287、#322/#324 逐项核对实现机制，说明 Issue 评论确实传递了跨组件契约。10:02 的 #266 对收件人说“由你”与既定归属冲突，#268 指出，#269/#270 在约一分钟内澄清唯一写者仍是 @deepseek-5。这里的成本来自评论措辞和多负责人边界，Braid 的持久评论与投递帮助及时发现并纠正；未见由此产生第二份实现。来源：上述评论行，特别是 #217、#220、#223、#266–#270。

10:24 的 #297 指出原定 PR #23 复核者 @deepseek-10 无可恢复会话；投递表对 #269/#270/#297/#299/#300 均记 `unreachable`，原因包括 `no resumable session`/`blocked`。#298–#300 随即改定 @deepseek-17。10:53 创建 PR #23 时平台实际指派 @deepseek-21（#328/#329），#330 再确定 @deepseek-17 做唯一实质复核，@deepseek-21 做形式核对。这多了一轮负责人澄清，但投递状态也让不可达问题在创建 PR 前暴露。10:39 的 #307 解锁通知给 @deepseek-5 曾显示 `native input was not accepted; retrying` 后最终 `delivered`；#308 中几位已改派或不可达成员收到 `unreachable`，而 @deepseek-7 为 `queued`。不能仅凭发评论的时间视所有收件者已同步取得上下文。来源：`local_comments` 与 `local_comment_delivery` 上述编号。

PR #20 最终 head 于 10:29 的 #302 交接，#305 10:38:29 判 ready，根于 10:38:58 合入 `db23b1f`；交接尾段约 9 分钟，其中 #305 明载独立 `worksheet-lifecycle` 10/10 复跑，不能全算通知等待。PR owner 10:42 的 #311 按原始需求发现 Ready 清单遗漏“重开透视编辑器需可见报错”，比合并晚约四分钟；#313/#315 明确合并与暂缓评论竞速并重开 Issue #4。Braid 的 `--match-head-commit` 固定了已验提交，无法替代对需求清单完整性的判断；现有证据是**语义验收遗漏与异步交接竞速**，不是 head 校验失效。#323 随后又把“Apply 必须禁用”加成额外条件，#325 在实现定稿前撤回为可选，避免了额外误约束。来源：评论 #302–#316、#323/#325。

截至 11:10 UTC，PR #23 于 11:08 合入 `b4a4b0c`，Issue #5 已关闭；Sheet 的 `C/run.json` 仍无 `finished_at/result`，Braid 中根 Issue #1 与重开的 Issue #4 仍 OPEN，尚无跟进 PR。当前剩余关键路径是 Issue #4 的透视编辑器缺口修复及复核 → 最终整合与交付；不能把此前 10:38 的“REQ-2 已完成”截面当终态。此次只读分析未改源码、应用、运行状态、评论或实验。
