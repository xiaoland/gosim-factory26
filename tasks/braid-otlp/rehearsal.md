# Braid OTLP 独立只读预演

2026-09-23。本次只检查既有真实运行产物、SQLite 的只读查询、当前 CLI 帮助和只读对象输出；没有阅读 Rust/Python 实现，没有启动模型、benchmark、Factory 测试或 smoke，也没有实现遥测导出。结论支持方案中的“原生已记录内容与最终对象状态”合同，不能支持“所有历史编辑、所有 system 请求及子代理均已完整捕获”的更强主张。

## 证据范围与版本

只检查以下三个运行目录。表中路径均相对于仓库；每个目录的证据入口是 `native/manifest.json`、`braid-state/sessions.json`、`braid-state/braid.sqlite3` 与 `sources/braid.json`。

| 运行目录（`runs/integration/` 下） | Braid 源码 revision | 数据库 migration 终版 | 原生会话 / Braid turn | 对象与事件 |
| --- | --- | --- | --- | --- |
| `20260921-235700-pi-braid-ca880d` | `e9b347117a1aee3eb06f9dd01689173ad975825a` | 6 `profiles_assignment` | 0 / 0 | 1 Issue，0 评论，2 events |
| `20260921-185322-pi-plain-2887cf` | `63459fc3ef3c16377c22282d04a21fa3307183a8` | 5 `local_collaboration` | 9 / 10 | 1 Issue、1 PR、6 评论、1 reaction、31 events |
| `20260920-230846-pi-plain-c01cd3` | `bd0cfcce01dead92e19fc58f34805aa231624927` | 3 `local_objects` | 6 / 6 | 1 Issue、1 PR、5 评论、28 events；无 `local_comment_reactions` 表 |

首选样本的 `result.json` 为 incomplete，`status.json` 有 1 blocked group；两个 sessions 清单均为空。它可说明失败前对象状态，不能证明会话导出。后两个是现有受控接入运行，不是本次重新执行的产品 benchmark。

当前 `sources/braid/target/debug/braid --version` 为 0.3.2；全局 `/opt/homebrew/bin/braid` 是没有 local 命令的旧入口，未用其读取对象。当前 `comment view --help` 明确说明 `--include-hidden` 展开 hidden/resolved 历史，已删除正文不可恢复。

为了不让 CLI 意外改动历史原件，曾把第二个样本的真实数据库字节复制到临时目录，执行 `status --json`、`issue list --json`、`pr view 1 --comments --json` 和 `comment view 1/2 --include-hidden --json`，随后删除临时副本。原件与副本数据库 SHA-256 均未变化。status/comment 成功；issue list/pr view 失败，原始错误为 `no such column: l.desired_profile_id`。这是真实历史 schema 与当前对象读取接口的不兼容；本预演没有迁移或修复它。

## 原生会话可恢复范围

| 检查项 | 185322 样本 | 230846 样本 |
| --- | --- | --- |
| JSONL 行数 | 168 | 99 |
| 原生 entry 类型 | session 9、model_change 9、thinking_level_change 9、message 141 | session 6、model_change 6、thinking_level_change 6、message 81 |
| 消息角色 | user 10、assistant 63、toolResult 68 | user 6、assistant 37、toolResult 38 |
| 工具调用 / 结果 | 68 / 68，调用 ID 双向匹配 | 38 / 38，调用 ID 双向匹配 |
| `parentId` 找不到对应 entry | 0 | 0 |
| 同 parent 多分支 / compaction entry | 0 / 0 | 0 / 0 |
| manifest 原生 SHA-256 一致 | 9/9 | 6/6 |
| context / instructions 文件存在 | 9/9、9/9 | 6/6、6/6 |
| turn input 文件存在且包含于原生 user 消息 | 10/10 | 6/6 |
| context 全文包含于原生 user 消息 | 9/9 | 6/6 |
| instructions SHA-256 与 DB `instruction_revision` 相同 | 9/9 | 6/6 |
| Braid `context_resets` | 7，全部 applied | 4，全部 applied |

每条 message entry 保留 `id`、`parentId`、timestamp、role 与 content。工具调用 content 有 toolCall ID、名称与 arguments；结果有 `toolCallId`、`toolName`、`isError`、content，部分有 details。assistant 保留 provider/model/api、responseId、stopReason/rawStopReason、errorMessage，以及 usage。全部 100 条 assistant 消息都有 input/output/cacheRead/cacheWrite/totalTokens/cost；reasoning 只在 95 条中存在，不能把缺失值当作零。

原生文件没有 system 角色消息。`instructions.md` 能证明 Braid 保存的指令内容，不能单凭这些产物证明 provider 最终拼出的完整模型 system 请求。user 消息是 context 与轮次输入的组合，不与单独 input 文件逐字相等；本次验证的是完整子串包含关系。

每个样本的 worktree 原始副本与 `native/` 归档各保留一份 JSONL，因此分别发现 18/12 个文件，但唯一 header session ID 只有 9/6 个，全部出现在 manifest。没有额外 child session ID，实际工具仅 bash/write。不能把“无未列出的文件”解释为子代理捕获已通过，也不能从这些没有 compaction/branch 的样本证明对应重放行为。Braid reset 则有 old/new session ID 和前后 context revision，可恢复物理会话替换关系。

最大原生单行是第二个样本的 `native/008-2026-09-21T10-55-11-873Z_01a0c39b-0601-761f-ad0f-08c8c9b3198a.jsonl:6`，19,976 字节（含换行；不含为 19,975）。第三个样本最大行为 `native/005-2026-09-20T15-21-28-090Z_01a0bf68-711a-7379-8578-c1f54c3e5f23.jsonl:6`，11,911 字节（含换行）。这只是样本最大值，不是原生格式上限或 protobuf batch 上限。

## 对象、历史与关联

第二个样本最终 Issue 为 CLOSED/completed，PR 为 MERGED。`local_items` 的 Issue/PR revision 分别为 4/3，但各自只剩一行当前 title/body。`associations` 保留一条 active 的 issue:1 → pr:1 关联；`assignments` 与 `agent_instances` 保留两个逻辑 Agent 的 assignment、profile、role 和生命周期。旧 schema 没有当前的 desired_profile_id/assignee_login 合同，Context 中的 `Assignees: @braid` 不能替代当前指派字段的验收。

六条评论中，一条 hidden（revision 2、正文 39 字节、一条 eyes reaction、hide_reason 有值），一条 deleted（revision 2、body 为 NULL），其余四条 visible。当前 CLI 的 include-hidden 输出独立确认 hidden 正文与 reaction 可读取、deleted 正文仍为 null。reply_to、thread_root、resolved_through 字段存在，但本样本没有回复与解决实例：reply_to/resolved_through 全为 null，因此只能确认字段边界，不能确认复杂线程或解决行为。

`local_merges` 保留 base `bf88f759dfbb2f789440e3191335c4c7b6bcc7e6`、head `b820eb9d93cd322a18ad4d54fce8cc7dc4662996`、merge `b67355df623ca5f38f7cfc2cf05c0908eca00dfa`，状态 applied，以及 writer_group/writer_turn/writer_node。第三个样本也有一条 merge 记录。

第二/三个样本的 31/28 条 event 均有 object_version，但分别只有 4/4 条 detail 非空，body_digest 全为空；全部 deliveries 的 raw_payload 都是零字节。event reference 能说明 create/edit/hide/delete/link/ready/merge 等事件，不能提供每个版本的完整正文。第三个样本评论 #1 已到 revision 4，表内仍只有一个当前正文，更直接显示最终状态与修改历史不是同一份证据。原生工具输出和 context 偶尔保留旧值，可辅助解释，但不构成覆盖所有修改的版本日志。

现有可连接的链条是：run_id → work item（kind 与 ID 必须同时保留）→ assignment → agent/group → DB provider_session → 原生 provider_session_id/path → manifest native_id；turn 通过 DB session_id 关联，manifest 同时提供 braid_turn_id/provider_turn_id/input_path。`sessions.json.session_id` 在这两个 Pi 样本中是原生绝对路径，并非数据库 `provider_sessions.session_id` 的 UUID，不能直接等值连接。comment/event writer_group 与 writer_turn 提供作者归属；第二/三个样本各有 26/22 条 event 带这些 writer 字段，其余事件不能臆造作者。

所有 15 个原始绝对 native_session_path 都已经不存在；归档后的相对 `native`、context、instructions、input 路径有效。离线导出必须使用 manifest 的归档路径，不能沿用 sessions.json 或数据库里的临时绝对路径。

## 对实施方案的独立预演结论

1. **最终对象方案有证据支撑，完整历史没有。** 直接导出一致数据库快照与原生输入可恢复样本末态、隐藏正文、删除墓碑、关联和合并 commit。方案明确不承诺全部历史版本是必要边界；若用户所说“完整”包含每次修改前正文，需要另行改变源端记录合同，单纯 OTLP 接线无法补回。
2. **离线历史验收存在真实接口门槛。** 当前 CLI 对 schema 5 的 Issue/PR 查询失败，schema 3 还缺 reaction 表。实施前应明确历史导出支持哪些 schema；选择兼容、受控副本迁移或明确 unsupported 均需给出具体行为，不能把这些历史样本直接当作当前接口可用的前提。首选 schema 6 样本虽然较新，却没有会话。
3. **子代理、压缩和分支仍是证据缺口。** 当前两个有效样本不能独立验证 design.md 所述 child manifest 转换。计划应把“取得已有含 child header/parent 关系或 compaction/branch 的真实源文件并验证公开输出”列为独立验收前提；拿不到时保持未验证/partial，不能用父会话摘要或没有孤儿文件代替。无需为本次预演造数据或运行模型。
4. **记录身份、源顺序与摘要需先固定。** 文件行号可恢复该文件顺序，entry parentId 和 toolCallId 可恢复结构；并发会话不能按 collector 到达顺序排成一条因果链。15 个源绝对路径全失效，且 DB session UUID 与 manifest session_id 不是同一身份，转换层必须显式映射。若要求重建后的字节摘要等于原文件，应保存原始行字节或明确约定规范化摘要；只传解析后 JSON 对象再序列化，不能假定空白、转义和键顺序不变。原生改写后的文件版本也应与旧 offset/旧记录身份区分。
5. **批次与终态完整性尚未验收。** 样本单行最大约 20 KB，无法验证超大 toolResult、图片或 16 MiB protobuf 限制。分片后应按实际编码字节计量；终态清单应覆盖每个源文件和关系，不仅统计 SDK 送出的日志条数。实时读取到最终归档之间、源文件半行/改写、进程强杀前以及 child 归档前都是计划必须显式标 partial 的窗口。此次只有最终产物，无法测定窗口持续时间或证明 flush/重试/错误正文合同。

可继续据此完成 impact handshake；本预演不代表三类信号已经接通，也不代表新实现或实时链路通过验收。
