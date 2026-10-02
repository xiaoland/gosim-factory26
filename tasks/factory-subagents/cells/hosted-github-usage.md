# 官网 GitHub 原生子代理使用：来源生成与续跑链

本页只统计官网 GitHub 的**原生 Pi 子代理**。Braid Issue assignee 是协作成员，不是 Pi 子代理；同一 Braid run 在官网恢复后出现的新 Pi 主会话也不是新协作成员。时间均为 2026-09-27 UTC。主证据为 `runs/e20260928-completed-replay/github/source-workspace.zip` 中 Braid `20260927-080209-0b57147a` 的 `work/native-homes/` 原生会话和 `subagent-artifacts/`。该终态 ZIP 随 `435b79927a47` 生成后保存，包含从初始 `38dc20e99fa5` 起沿同一 Braid 状态继承的历史，**不能把所有调用归算为 g05 新窗口**。

## 来源生成链及覆盖

| 官网 run | 性质与原始材料 | 本页口径 |
|---|---|---|
| `38dc20e99fa5` | 初始 GitHub 生成，终态 `runs/acceptance-integrity/20260927/cooperation-hackathon-self-funded/github-terminal-workspace.zip`；g01 从此快照继续。 | 已在 g05 继承历史中核实 11:24、11:27 两次 executor；旧 ZIP 未单独核对是否还有其他调用，不能称仅此两次。 |
| `e4e7f35f55eb` (g01) | 11:56:47 启动，从初始工作区恢复；`runs/e20260927-03-github-resume/g01/` 有 11:58 快照及 13:38 保存现场。 | 本页第三次 executor 于 12:05 启动，归属 g01；前两次是继承历史。 |
| `64e0bebcf6f3` (g02) | 从 g01 保存现场继续；14:46 取消；`runs/e20260927-03-github-resume/g02/terminal/` 有终态 ZIP。 | 有原始资料，独立增量索引待查；不能把继承的三次再次计数。 |
| `6b45225a668c` (g03) | 恢复 SQL 约束错误，尚未启动 Braid 生成。 | 无新 Pi 执行。 |
| g04 | 与 g03 同来源再试；见 `tasks/acceptance-integrity/experiments.md`。 | 需以官网 journal 确认 run ID 和是否有增量，不在现有三次中推算。 |
| `435b79927a47` (g05) | 成功恢复并交付的来源生成；终态 ZIP 是本页总索引。 | 三次 executor 是继承历史，不归为 g05 新调用；g05 新窗口需要按会话时间单独筛。 |
| `595ab74c90a9` | 对 g05 完成应用的官网部署与评分重放，4/100；不重新生成。 | 不计为 Pi 子代理生成 run。 |

更早 `d593b9eae490` 是 2026-09-26 四题官网初步验收中的 GitHub run，见 `tasks/acceptance-integrity/experiments.md` 与 `runs/e20260926-01-acceptance-github/`；它和上表不是同一恢复链，原生索引尚未核对，不能以本页三次覆盖。其他早期运行若有原始 ZIP，亦需逐 run 查证。

## 已核实调用 ledger（初始 run 与 g01 新窗口，均见于 g05 继承终态 ZIP）

三个异步执行各有**独立 UUID**，不是一个子会话的重试片段。父均为 Braid 根成员 `@glm-1` 的不同物理 Pi 会话，模型父配方为 GLM，调用的 `executor` 子角色实际模型为 `factory26/deepseek-v4-flash:high`；这是当时的角色模型配置，不等于错误混模。每次先调用 `agent:"deepseek"` 得到 `Unknown agent: deepseek`，再 `subagent({action:"list"})` 得五个可用角色（advisor/browser-operator/executor/explorer/vision，均 `context:fresh`），然后改用 `executor`。这是**把模型/Braid 成员名误当原生角色名**的实证，不是三次 DeepSeek 子代理成功启动。三次错误调用与三次有效启动分开计数。

| 原生 run ID／父 Pi session | 委派输入、状态与时段 | 可观测投入、返回与父消费 |
|---|---|---|
| `7befc0b1-e0d9-48a9-ba62-49a7be07756a`；初始 run，父 `01a0e299-90fd-7652-8f9c-ac54e0f5e402` | 11:24:54 启动 `executor`，要求在根 Issue #1 worktree 把 Issue #7 PR #8 快照 rebase 到已含 #6 的 `develop`、解五处冲突并自检；明确该 cwd 为唯一写入区。子 transcript 有 11:24:58–11:34:18 记录。 | 40 条有 usage 的 assistant 消息合计 input 134,029／output 46,898／cacheRead 2,010,112／cacheWrite 0；父 11:26:02 对该 UUID arm `subagent_wait(nonBlocking:true)`。快照仅有 input/transcript，无 meta/output 或可证父消费；**终态未证**。 |
| `76d53282-1604-439f-9e94-ae8a1bf8ad97`；初始 run，父重建后 session `01a0e29d-9511-719a-9662-a40b1351d755` | 11:27:55 再次把相同 rebase/冲突任务交 `executor`，任务文本也称该同一 cwd “唯一写入者”。子 transcript 11:27:56–11:33:59。 | 25 条 assistant usage：input 111,738／output 29,476／cacheRead 1,256,704／cacheWrite 0；父 11:28:16 查询**此新 UUID** status 为 running，11:28:22 arm wait。快照仅 input/transcript，无 meta/output 或可证父消费；**终态未证**。 |
| `56af2cee-145a-4048-883d-d98d91a176d8`；g01，父另一 session `01a0e2ba-6e7a-7719-929d-7923f8e4cca7` | 12:05:45 第三次交同一 Issue #7 rebase/集成任务；子 transcript 12:05:48–12:24:43。 | 77 条 assistant usage：input 178,994／output 66,588／cacheRead 7,010,816／cacheWrite 0。artifact meta 明确 `exitCode:1`、`error:"Subagent process terminated by signal SIGKILL."`；output 只有 “Now resolve styles.css. Let me view the conflict:”，没有完成交接。父 12:09:36 arm wait；是否收到失败通知待查。 |

这些 usage 数字是各子 transcript 中 assistant message 的累加，不能等同独立付费量；第三次 meta 的 usage 与 transcript 加总一致。前三次至少有 11:24–12:24 的可见子任务工作，其中前两次的 transcript **时间范围重叠**（11:27:56–11:33:59），两者在相同根 worktree 上于重叠期均发出 bash/read 工具调用。现有证据仅能证明并行工具活动和重复任务；已见临时 `/tmp` 写入，但**未证明同一工作树文件发生并发写入或冲突**。第三次 meta 证明失败，前两次缺少终态文件，不能把三次说成成功完成。

`context:fresh` 有直接工具输出支持；三个子 transcript 的首条 user 任务是独立的、有 cwd/HEAD/冲突范围的委派文本，没有父历史消息。`subagent-artifacts/*_input.md` 中 system prompt 被 `[prompt redacted]` 替代，因此不能逐字验证完整系统提示；这不使可见的任务正文和消息历史也变成未知。

## 因果与限制

最明确的投入浪费是初始 run 根 Issue 在 11:24 和重建后 11:27 两次把**同一个正在进行的 rebase**重新派给不同 `executor`。第一次子 transcript 一直写到 11:34，第二次也持续到 11:33；父第二次只查询了新 UUID `76d...` 的 status，没有查旧 UUID `7bef...`。两次 `list` 只列角色，没有列在途任务；父新会话的首条 Braid Issue 消息未显式携带旧子 run UUID。结合再次委派，说明子任务身份/结果在重建交接中未有效进入模型决策。它**尚不能证明**旧 UUID 在底层 `status` API 不可查询，也不要求 Braid 管理 Pi 子进程。最小修正位置是 Pi 会话恢复提示或原生子代理状态/完成通知，使父知道在途 UUID 和结果；先通过实际 `status(old UUID)` 能否跨 Pi home 解析来判定是发现性还是存储隔离。

按 g05 终态 ZIP 的原生 JSONL 定向索引，已见成功启动的原生角色只有上述三个 `executor`；advisor、explorer、browser-operator、vision 在本次索引未见启动。此结论限于已扫描的 `work/native-homes` 父 Pi 工具调用，并需再按早期各独立 ZIP、新窗口对比；不能改写为“全部官网 GitHub 零使用其他角色”。三个 executor 都用于根 Issue 已由 Braid 成员负责的集成 rebase，未观察到清晰的增量代码/检查成果被父消费；第三次明确 SIGKILL。最终应用虽完成并重放评分，不能把结果归功于这些子任务，亦不能仅凭未消费证明它们无代码影响。需要对照父后续 git 命令与最终 commit 才能确认代码贡献。

证据定位：来源 ZIP 中三个父 session 的 `sessions/--workspace-template-.../2026-09-27T11-21-50...jsonl`、`11-26-13...jsonl`、`11-57-43...jsonl`；相应 `subagent-artifacts/<UUID>_executor_{input,transcript,meta,output}`。`native/` 下的编号 JSONL 与 `work/native-homes` 可复制同一会话，计数时以子 UUID 和父 toolCall ID 去重，不把它们当额外调用。官网运行身份与来源见 `tasks/acceptance-integrity/experiments.md`、`tasks/github-score-diagnosis/packet.md`。
