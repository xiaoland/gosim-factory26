# PR14 生命周期定向核查

## 范围与证据身份

本记录只核查冻结 `snapshot-01` 中 PR14 native 会话 `2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9` 的 lifecycle 现象，重点读取该会话 Records 32–106，并补看 107–125 中 07:13:04 重新打开后的成功写入。未抓取远端、未改源码、未运行测试。

- Native view：`views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt`。
- 候选版本：PR14 head `9bedf84`，base `develop` `53532a0`。
- Braid DB：`snapshot-01/braid.sqlite3`。PR14 对应 provider session 的 `cli_binding_id` 是 `01a0ebf5-b4c7-7cd3-9369-291fd2002e2a`；它与 native 运行时打印的环境绑定一致。
- runtime-evidence 5c 源：`runtime-evidence/5c957436-src-group-worker.rs`，SHA-256 `7e0c955f9f7e49a2fa4e897ea27f11270df04490651d02a30f43dcdc5cfc5ef6`。

## 观察

1. 初始 PR14 Braid turn `01a0ebf5-b86b-7a61-b7d5-5b4c49069da0` 在 DB 中是 `wake_batch`，开始于 `06:59:04.592Z`，结束于 `07:00:40.286Z`，状态 `completed`。Native 在该 turn 结束前启动后台复验：`views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Record 33 的 `bg001` 实际开始于 `06:59:54.752Z`；同一 view Record 47 在 `07:01:13.498Z` 返回，耗时 `78745ms`，即后台完成晚于 DB turn 结束约 33 秒。该段显示 `TEST_EXIT=0`、`E2E_EXIT=0`；同一 view Record 49 显示 Playwright `34 passed`。
2. 这项后台复验完成时没有对应的新的 PR14 `wake_batch` turn。Native 在 `views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Record 47 只收到 background job `bg001` 的完成结果；DB 在初始 turn 之后直到 07:13:04 没有新的 PR14 running turn。这里可以确认“Pi 背景任务完成结果到达时未登记成新的 Braid turn”，不能把它解释成第二个 Braid 回合已完成。
3. 07:01:30 起，native 尝试把复验结果写回 PR 时连续收到 `error: 当前调用已失效，本次修改未写入`：首次失败见 `views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Records 54–57；`braid pr ready` 也失败见同一 view Records 71–72。读操作仍正常，PR 状态、head 和 base 没变。
4. 同一 view Records 80–105 对宿主状态的只读排查显示：env binding 与 provider session 绑定值一致；宿主视图中的该物理会话已经是 `idle`，初始 Braid turn 已 `completed`，当前续接消息没有创建 running turn。冻结 DB 的最终快照随后把原始 provider session 标成 `replaced`，并保留同一个 `cli_binding_id`；这反映后续重开/替换已经发生，不是初始失败时的绑定错配。
5. 07:13:04 的新 notice 明确要求“当前会话结束后用最新内容重新打开工作会话”，见 `views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Record 107。随后同一 view Record 109 返回 `comment #101`，Record 111 明确记录写入成功；Record 115 可见 #101 已在 PR14 thread 86 发布。DB 对应的是两个 `context_reset_notice` turn：`01a0ec02-87a1-7a10-a14f-193afc607d0f`（07:13:04.199Z–07:13:29.806Z）和 `01a0ec02-ee0d-74d1-a749-66f57bd57432`（07:13:30.507Z–07:13:37.410Z），两者均 `completed`。

## 因果判断

**最符合证据的解释：已完成的 Pi 背景复验结果落在初始 Braid turn 结束之后，宿主先把 provider session 视为 idle/随后替换，续接消息没有同步生成可写的 running Braid turn；因此写 CLI 按生命周期校验拒绝。新的 context-reset notice 触发会话重新打开后，新的 turn 成功登记，#101 才能写入。**

这不是错误绑定的主要证据链：native 在 `views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Records 62–64 看到的 `BRAID_CLI_BINDING_ID` 与 DB provider session 的 `cli_binding_id` 一致；失败同时表现为 session/turn 不在 running 状态，而不是 repository、work item、profile 或 binding mismatch。DB 的 provider session 归属于 PR14 的同一 assignment，未见错误 work item 绑定。

这也没有证据支持“reset kill”是原因。冻结 turns 中，初始 turn 和后续两个 `context_reset_notice` 都是 `completed`，没有 `unknown`、error 或 deferred reason。native 日志没有 signal、进程树、kill 记录或 provider stream closed 记录。后台 job 的完成结果是正常 `TEST_EXIT=0`/`E2E_EXIT=0`，不能从它推出 native 进程被杀。

## 与 5c runtime-evidence 源的对应关系

5c 源把 Braid 终态归因到 provider event，而不是任意 `message_end`：

- `poll_running` 只有收到匹配 `provider_turn_id` 的 `SessionEvent::TurnTerminal` 才交给 `finish_running`（约第 413–439 行）。event stream 关闭或 lagged 才映射为 `unknown`，并附带具体原因（约第 425–434 行）。
- 普通 turn 会调用 `mark_turn_terminal`（约第 380–382 行）；shutdown drain 明确以 `unknown` 和 “provider session disconnected before terminal receipt” 结束（约第 473–490 行）。本证据点没有观察到这些路径。
- context reset 有单独门控：只有确认 reset notice 已被 native session 处理，才移除旧 session 并把 reset turn 标为 terminal（约第 328–346 行）；未观察到 notice 或证据不匹配时会 defer/fail（约第 347–370 行），代码没有把“背景完成消息”直接当作 reset 已完成。
- 因而，`message_end`、Pi background job result 或宿主显示 idle 都不能单独作为 Braid turn 的终态证明；本案的终态证据是 DB turn lifecycle、provider lifecycle 以及 07:13:04 notice 后的成功新写入共同构成的链。

## 已修复与仍在证据范围内

- **已恢复：** 新 notice 后 Braid 写入恢复，#101 成功发布；随后 #102 冻结 head 声明也成功编辑，见 `views/2026-09-29T06-59-04-172Z_01a0ebf5-b76c-715b-978b-ee07e02b9ed9.txt` Records 114–123。head 仍为 `9bedf84`，base 仍为 `53532a0`。
- **仍需保留的边界：** 本证据只能判定本次是“背景结果晚于已完成 Braid turn，续接未登记 running turn”的生命周期/交接缺口；不能推广成所有 Pi background completion 都会丢失，也不能证明宿主绝不会在其它路径错误绑定或 kill reset。
- **下一轮判别证据：** 对每个 background job 记录 `(provider_session_id, provider_turn_id, Braid turn_id, lifecycle, terminal event)`；若 job 完成时没有对应 running turn，应在宿主侧生成显式 continuation/reset turn；若出现 `unknown`，再以 provider stream close、signal、stop failure 和 reset 状态区分 kill、断流与正常完成。
