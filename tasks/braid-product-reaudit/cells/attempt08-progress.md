# attempt-08 GitHub 根会话后台检查的定向核对

2026-09-28 06:57 UTC 截面。只读核对正在运行的 GitHub 工作区；没有操作作业、容器、应用或 PR，也没有调查 Sheet。来源是 WSL `runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--github-97914b9e3158cf/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/`。以下相对路径均基于这个内层目录：

- 根原生会话：`work/native-homes/pi-glm-fast-01a0e6c1-4bf4-7812-9c3a-7a3dab051187/2026-09-28T06-43-44-290Z_01a0e6c1-5222-75b2-89e0-1ed3d84c2bad.jsonl`。
- PBB 作业和日志：`work/home/.pi/pbb/sessions/b5a39c1f67e440ce4f623610/instances/pbb_116_4f53c2eb/{jobs,logs}/bgNNN.{json,log}`。这三个作业的 `sessionFile` 均精确指向上述根会话；其它 PBB session 中同名的 `bg015` 等属于不同会话，不能混用。

**结论：根会话未被失效作业卡住。** `bg015` 是真实的依赖安装检查，在查询到“无日志输出”后约五秒完成；`bg016`、`bg017` 更早完成。低效点是用多个 `sleep 60/90/120/180` 后重复 `pbb tail`，且最初测试命令只保留 `tail -4`，导致退出码和测试摘要的证据不充分。根会话随后重新取得明确测试结果，并在 06:55–06:57 UTC 执行 REQ-4 E2E 与集成操作。

| 作业 | 原始命令与 PID（容器内） | 实际状态、耗时与日志 |
| --- | --- | --- |
| `bg015` | PID/PGID `1644`；`cd /tmp/verify-pr5/backend && npm install --no-audit --no-fund 2>&1 \| tail -2 && node -e "require('better-sqlite3');console.log('bs3 OK pr5')" 2>&1 \| tail -1` | 06:51:52–06:53:25 UTC，`exited`、exit code 0、93,822 ms。`bg015.log` 60 B，最终为 `added 103 packages, and changed 1 package in 2m`、`bs3 OK pr5`。06:53:20 的 `pbb tail` 显示 `running` 和 `No log output recorded yet`，因为输出经 `tail` 汇总到命令结束才出现，不是失活证据。 |
| `bg016` | PID/PGID `1686`；`cd /tmp/verify-pr6/backend && npm test 2>&1 \| tail -4` | 06:51:56–06:52:13 UTC，`exited`、PBB exit code 0、17,487 ms。日志只有测试输出最后四行（70 B），没有总数或失败数；管道的 0 也只是末端 `tail` 的状态，单凭本作业不能判定 `npm test` 通过。 |
| `bg017` | PID/PGID `1696`；`cd /tmp/verify-pr7/backend && npm test 2>&1 \| tail -4` | 同在 06:51:56–06:52:13 UTC 完成，`exited`、PBB exit code 0、17,488 ms。日志同样只有最后四行（70 B），证据限制与 `bg016` 相同。 |

根会话原生行 77–81 是三个作业的启动与后台确认；行 90–91 记录了 `bg016`/`bg017` 已 `exited`、`bg015` 尚无输出。行 96–100 显示它改为把 PR6/PR7 测试完整输出写到 `/tmp` 再取摘要：PR6 结果 `exit=0`，36 tests、36 pass、0 fail；PR7 命令也打印 `exit=0`，随后的 grep 因输出格式不匹配返回 1，但下一条 `tail` 明示 36 tests、36 pass、0 fail，不能把 grep 失败冒称测试失败。行 107–108 取得 PR5 后端 `exit=0`、38 tests、38 pass、0 fail。

原生行 109–114 与 PBB `bg021.json`/`bg021.log` 显示根会话随后在 `/tmp/verify-pr5` 跑 `node e2e/req4.spec.mjs`，06:55:08–06:55:50 UTC、PID `2719`、exit code 0、42,038 ms，日志总结 `REQ-4 e2e: 24/24 PASS`。行 115–131 已转向集成 worktree 和 PR #5 合并操作；这证明它没有停在 `bg015`–`bg017` 的轮询上，但不代表整体应用或余下需求完成。

轮询代价可以从同一 PBB 实例核对：`bg018` 是 `sleep 90` 后查三作业，`bg019` 是 `sleep 120` 后再查，`bg020` 是 `sleep 60` 后查已完成的 `bg015`；`bg022` 又 `sleep 120` 查 42 秒已完成的 `bg021`。这些后台睡眠与其它工作有重叠，不能将其时长直接相加为根会话停工时间；但重复查询已结束作业和过早截断测试输出，确实增加了无信息的工具调用。

最小处理建议是**不干预当前运行**。后续检查可等待 PBB 已提供的完成消息，必要时对同一 job 查询一次状态与完整结果；测试命令应保留测试进程的退出码和摘要（例如写完整日志后显式输出 `exit=$?` 与摘要），避免 `npm test | tail` 把真正失败掩盖或迫使重复运行。此建议只针对根会话的检查方式；本页没有复核 PR 总树、REQ-6 或 Sheet，也不能据此判断最终评分。

## 追加：07:02 UTC 的 GitHub 集成与 REQ-6 关键路径

本节继续只读同一运行的 `braid-state/braid.sqlite3`、`braid-state/origin.git` 和上述根原生会话。前节“没有复核 PR 总树、REQ-6”的范围说明仅适用于其 06:57 UTC 截面；以下是新增核对结果，不是运行终态。

**PR #5 的代码已经合入，但 Braid 条目为 `CLOSED`，不是 `MERGED`。** `origin/develop` 指向 `2d29c4de644ac3900edbf10dbcea1010278f396e`，该 merge commit 的双亲是原 develop `354b198fb2d0d10b46f75e81a6cf38b0fb5786db` 与 PR #5 head `33258736ea85a857ae1f8305f23585348115c0ba`；后者也是当前 develop 的祖先。根会话原生行 123–126 显示在干净 worktree 先完成 `git merge --no-ff` 并推送。随后行 129–136 的 `braid pr merge 5` 因 head 已在 base 内而拒绝，行 139–140 才以说明性 reason 把 PR 置为 `CLOSED`，Issue #6 于行 145 后关闭。数据库 `local_merges` 仅有 PR #1–4 的 applied 记录，故 Braid 状态不能用来否定 Git 实际合入，也不能把 PR #5 误称为 Braid 已标记 `MERGED`。

根在行 115–120 曾遇到 `SettingsPages.tsx` add/add 冲突，但那次命令先执行 `git checkout develop 2>&1 | tail -1`，checkout 实际输出 `Aborting`，管道末端 `tail` 的成功状态使后续 merge 仍在既有 `integration/req4` 分支运行；该分支 HEAD `5d7cb16` 本就含 REQ-4 的整合。根随即 `git merge --abort`，新建 `/tmp/integ`、快进到真正的 origin/develop，再合 PR #5，未见冲突。因此这次暂态冲突是错误分支上的重复合并，不是共享 API 契约漂移。

| 项目 | 07:02 UTC 的可证状态 | 当前下一步 |
| --- | --- | --- |
| PR #6 / REQ-2 | Braid `OPEN`，未见 `local_merges`；交付 head `a118113` 基于旧 develop `354b198`。根在 06:59 将其 rebase 到已含 PR #5 的 develop，冲突文件为 `backend/src/server.js`、`frontend/src/App.tsx`、`frontend/src/pages/RepoSettingsPage.tsx`、`frontend/src/pages/RepositoryPage.tsx`；07:00:29 形成 rebased commit `3014fa2`，随后在复验 build/依赖。 | 复验、发布 rebased head，再合入。尚未有已合入证据。 |
| PR #7 / REQ-5 | Braid `OPEN`，无 merge 记录；交付 head `a9b09c3` 同样基于 `354b198`。根已查看并复验原 head，尚未见针对新 develop 的合入。 | 等根完成集成/复验；与 PR #5 共同改了 `server.js`、`App.tsx`，与 PR #6 还共同改了 7 个文件，后续可能需要同类集成，但不能预判具体冲突或结果。 |
| Issue #8 / REQ-6a | `OPEN`、`desired_member_login=NULL`，`assignments` 无该 Issue；故无 PR 是**尚未派发**，不是已派发后 agent 或旧状态堵塞。Issue 正文只要求共享基础 #2 已合入；根在 Issue #1 评论 17/31 中进一步决定等 #6 的 diff 能力。#6 已于约 06:58:39 关闭，PR #5 的代码已在 develop，所设派发条件现已满足。 | 可与 PR #6/#7 集成并行指派；当前根仍在处理 PR #6。 |
| Issue #9 / REQ-6b | `OPEN`、`desired_member_login=NULL`，无 assignment/PR；正文明确依赖 #8 的 PR 详情框架与种子。 | 等 #8 成果合入后派发，当前等待符合依赖。 |

PR #6 的四处冲突来自并行功能同时修改共享入口和页面：根原生行 157–170 可见 `server.js` 是 `codeRouter` 与 `orgsRouter` 的挂载并置、`App.tsx` 是路由/导入并置、设置页是 Branches 与 Manage access 链接并置；`RepositoryPage` 同时承载代码页与组织授权入口。这是基于同一旧 develop 的普通重叠，且路由挂载顺序确需保留行为；当前没有证据表明 Issue #2 约定的 API/数据契约在无人知晓时漂移。PR #5/#6 相交 4 个文件，PR #5/#7 相交 2 个，PR #6/#7 相交 7 个（由三个 head 相对共同 base `354b198` 的文件集合计算）；文件交集只说明集成风险，不等于已经发生语义冲突。

**未见终态交接消息丢失。** REQ-2 成员在 Issue #4 comment 40（06:09:23 UTC）报告 PR #6/head/自检，REQ-5 成员在 Issue #7 comment 44（06:24:01 UTC）报告 PR #7/head/自检；`local_comment_delivery` 对根 `glm-1` 均为 `delivered`，对应 `events` 的 root wake 均为 `consumed`。根恢复会话行 8 于 06:44 `braid pr view 6/7`，随后实际复验两份交付。`consumed` 本身只表示调度事件已消费，不能证明逐字读完评论；根的后续动作证明至少 PR 入口及实现成果已被使用。07:02 截面无指向 `glm-1` 的 pending completion/wake 事件，故没有证据支持“通知在队列里未被消费”解释 #8 未派发。

当前关键路径是根整合 PR #6/#7 与尚未开工的 REQ-6a/#8；REQ-6b/#9 要等 #8。可改进的 Harness/工作方式有三个具体点：一是子项依赖达到后及时派发 #8，让根的 PR 集成与可独立的 PR 功能开发并行；二是检查命令避免 `git checkout ... | tail` 或 `npm test | tail` 掩盖真正退出码，尤其不能在 checkout 失败后继续 merge；三是手工先 push 合并再调用 `braid pr merge` 会使工具无法记录为 `MERGED`，应在选择合并路径时保持 Git 与 Braid 状态可解释。以上是当前运行的诊断，不要求修改正在执行的应用或 Braid 状态；评分与最终完成仍未知。
