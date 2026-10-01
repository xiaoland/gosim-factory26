# PR11 生命周期旁证

## 证据身份与范围

本记录只核查 PR #11 owner 的 U8 native 会话及冻结 DB 生命周期，不重读实现，不抓远端，不修改源码，不运行测试。U8 的 assignment 身份为 `pr:11`，native 会话为：

`views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt`

候选版本是 PR11 head `15c79a4`、tree `5319a2b8`，owner 的独立干净副本结果为 platform-path 33/33、Vitest 76/76、typecheck 0。以下 DB 均来自冻结 `snapshot-01/braid.sqlite3`。

## 时序与因果证据

1. **后台复跑跨过了初始 Braid turn 的边界。** DB 中 PR11 的 provider session 是 `01a0ebe1-a34a-7db1-a1e1-13b13f3fc8c0`，初始 `wake_batch` turn `01a0ebe1-a476-75f3-978f-4ba02b5d47ab` 于 `06:37:08.744Z–06:40:30.890Z` 完成，`error` 与 `deferred_reason` 均为空。Native 在该 turn 内启动 `bg001`（`06:37:31.891Z`）；独立副本复跑最终在 `06:42:45.600Z` 报 `PLATFORM_PATH_EXIT=0`、`VITEST_EXIT=0`、`TSC_EXIT=0`、`ALL-DONE`，Playwright 33/33 也在同一批结果中出现。来源：native view `views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt` Records 69–73；DB `turns` 查询。
2. **后台结果到达后，写操作确实落在已结束 turn 之外。** 复跑结果之后，`braid pr comment 11 --reply-to 71` 在 `06:42:58.873Z` 以及 `06:43:01.818Z` 仍返回 `error: 当前调用已失效，本次修改未写入`；同一会话后续的绑定/状态探查也得到 turn `completed`、provider session `idle`。来源：native view `views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt` Records 76、80、86、101–108。
3. **不是 binding 错配。** 冻结 DB 的 provider `cli_binding_id` 是 `01a0ebe1-9e5b-7c93-bc41-8afc1a1f7ef9`；native 环境探查打印的 `BRAID_CLI_BINDING_ID` 与该值相同。native 自己的 guard 查询还显示写入要求同时满足 running turn、running provider session、有效 assignment 且没有 materializing reset；当时只有 completed turn 与 idle session，所以失败条件成立。来源：native view `views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt` Records 83、101–108、145–155；DB `provider_sessions` 查询。
4. **写入在新的普通 wake 中恢复。** `comment #74` 对 owner 先处于 queued；`06:47:19.979Z` 新的 `wake_batch` turn `01a0ebea-f828-7561-a0e7-a3e955bf73b2` 开始后，`06:47:21.758Z` 的同一 CLI 写入成功创建 `comment #75`。随后 PR body 编辑成功，最终 thread 可见 #75 与更新后的正文。来源：native view `views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt` Records 150–163、170、175–178；DB `turns` 查询显示该 `wake_batch` 于 `06:47:19.979Z–06:47:53.267Z` 完成且无 error/deferred reason。
5. **这次恢复不是 reset kill。** 对应 context reset 是在新 wake 已能写入之后才创建/应用：冻结 DB 记录 reset `01a0ebeb-439a-7b10-a74e-1ea4730c9cdb` 于 `06:47:39.161Z` 创建，`06:47:54.471Z` 应用；随后新 provider session 获得新的 binding `01a0ebeb-7c52-71f2-bd77-08694aceed94`。没有 `unknown`、error、deferred、signal、stop failure 或 provider stream close 证据。来源：native view `views/2026-09-29T06-37-08-214Z_01a0ebe1-a2f6-70c2-8b4c-fd64ffccea92.txt` Records 161–183；DB `context_resets`、`provider_sessions`、`turns` 查询。

## 与 PR14 的关系

PR11 与 PR14 可以作为同一生命周期模式的两条旁证，但不应拆成两个独立的 binding 锁故障：两者都显示后台工作在初始 Braid turn 结束后才完成，续接写入没有处于可写的 running turn，随后新交接恢复写入。

恢复路径有差别：PR11 在 `06:47:19` 的普通 `wake_batch` 中恢复，且在 `06:47:39` reset 应用前就成功写入 #75；PR14 则在 `07:13:04` 新 notice 后由 `context_reset_notice` turns 恢复并写入 #101。这个差别说明 PR11 不能被表述成“reset kill”，也不能把 PR14 的 notice 机制反推为 PR11 的实际恢复动作。

## 5c 源与版本边界

5c runtime-evidence 源（`5c957436-src-group-worker.rs`，SHA-256 `7e0c955f9f7e49a2fa4e897ea27f11270df04490651d02a30f43dcdc5cfc5ef6`）规定：普通 provider terminal 走 `mark_turn_terminal`（约 380–382 行）；context reset 只有在 native session 确认处理了 notice 后才终结（约 328–370 行）；shutdown/断流才走 `unknown`（约 445–490 行）。这与本案“普通新 wake 恢复、无 unknown/reset kill 证据”的观察相容。

hotfix02 的部署身份为 `5c957436`（主会话 06:31 续跑日志）；因此本案应归类为**hotfix02 恢复之后的现场旁证**，不能暗示它发生在 5c 之前。逐进程 native 会话到 binary revision 的独立绑定证明没有随 U8 保留，所以 5c 源码与观察到的行为相容，但不等于已证明每个事件都实际走过该源码路径；本案仍不应另立为一个新的 reset 锁故障。

## 结论与判别边界

- **已证：** PR11 的失败由旧 turn 已完成、provider session 已 idle，导致 CLI guard 找不到唯一 running invocation；binding 值一致，后台复跑本身成功。
- **已证恢复：** queued comment 触发新的 `wake_batch` 后 #75、后续 #78 与 PR body 写入成功；不是永久丢失。
- **未证：** U8 所服务的确切 runtime build 是否就是 5c；也不能推广为所有后台任务都必然丢失续接。
- **综合用途：** 将 PR11 作为 PR14 生命周期根链的独立旁证，统一归因到“后台/续接结果未登记为可写 Braid turn”的交接缺口，避免重复登记 binding 锁故障。
