# Pi 输入投递修复 LLD

本次只修复 Braid 对原生输入、收据和生命周期的适配，不管理 Pi 内部子 Agent。依据为本机固定 `@earendil-works/pi-coding-agent@0.85.1` 的 `dist/modes/rpc/rpc-mode.js` 与 `dist/core/agent-session.js`：prompt 仅在 preflight 成功后回复 success，然后进入 `_runAgentPrompt`；busy/compacting 拒绝没有结构化错误码，`get_state` 则提供 `isStreaming`/`isCompacting`。`steer` 直接排队，即使 idle 也不会自行开新 turn，因此 ACK 只支持已排入原生队列，不能证明模型读到。

ProviderAgentSession 以独立发送锁串行化发送，状态锁只覆盖读取与变更，不跨 RPC 等待；通知能在请求期间推进状态。运行中非 steer、idle 时 steer 返回类型化 Deferred，不丢弃消息后 ACK，也不偷偷开 turn。上层将 Deferred 的已 claim 普通输入恢复为可投递，steer 输入保持 runnable。

Pi start_turn 先读取结构化原生状态；busy 返回 Deferred。成功 prompt response 是分配当前 turn ID 的边界：stdout reader 在该 response 上安装待定 ID 并先发送 TurnStarted，随后才唤醒请求方；拒绝不改变当前 ID。状态查询与提交之间仍可能变化，prompt 失败后再次读取结构化状态，只有可证 busy 才 Deferred，否则保留具体协议错误。RPC 超时/断连仍是不可确认，不当作拒收重试。

Pi Activity 不参与生命周期 broadcast，只记录 trace；agent_start/turn_start 不重新分配 ID，agent_settled 结束 response 已接受的物理运行。不会扩大缓冲区或把 lag 伪装成功。原生 steer 保持原生排队语义；idle 的 wrapper 不调用它，同一运行的迟到排队收据仍不能替代采样证据，context reset 沿用 message_was_processed。

可判别验证：请求尚未回复时 terminal 仍能被消费；非 steer 忙时、idle steer 均 Deferred 且无新增 provider 请求；失败 prompt 不重贴旧 turn；成功 response 后快速 terminal 保持 Started→Terminal；大量 Activity 不制造 lag；断连仍产生 Unknown。采用针对性的 Braid 适配测试，不运行 Factory 测试或模型 benchmark。

## 实施与验证

已修改 `sources/braid/src/agent_session.rs`、`provider/mod.rs`、`provider/session.rs` 和 `provider/pi.rs`。只对 Pi 生命周期广播移除 Activity：活动仍以 trace 记录，stderr 继续逐行 warning，非 JSON stdout 仍 warning；没有扩大 buffer。成功 prompt response 在 reader 中发送 Started 后才唤醒请求方，wrapper 继续去重；失败 response 不变更当前 ID。新 session/resume 清除旧的物理 turn 映射。

2026-09-28 执行 `cargo test --bin braid provider:: --no-default-features`，8 passed、0 failed。新增测试分别验证 pending steer RPC 期间终态能被消费、两种发送模式不匹配返回 Deferred，以及生产 stdout reader 面对 2,048 条 Activity 时保留旧 turn 的拒收后终态和新 turn 的 Started→Terminal 顺序。原有测试还覆盖断连的 Unknown 与独立会话清理。初次 provider 测试发现旧 Pi fixture 的 resume `get_state` 总返回进程号，和既有生产会话路径校验冲突；已获主 Agent 授权，仅将 fixture 改为返回 `--session` 实际请求路径，保留生产校验，复跑后全通过。未运行 Factory 测试或模型 benchmark。

本次直接读取的原生文件位于 `~/.cache/factory26/runtime-faf60473273ddeed/node_modules/@earendil-works/pi-coding-agent/`，package.json 为 0.85.1。`agent-session.js::_runAgentPrompt` 先等待 agent.prompt，再循环 `_handlePostAgentRun`；后者检查重试、压缩和 `agent.hasQueuedMessages()`，正常执行期间收到的 steer 会在原生边界消费，队列未空则继续运行。`_emitAgentSettled` 在该循环结束后调用，并在发 settled 事件前 await 扩展 handler。

窄竞态仍须明确：最后一次队列检查已经结束 → Braid 尚未读取 settled（或 steer 已写入 stdin 但 Pi 尚未读取）→ 原生收到迟到 steer 并排队 → ACK。这条消息已被原生接受，但可能留待后续 prompt 消费；本次不声称恰好一次或已采样。wrapper 明确 idle 时不会自行开 turn，Pi reader 已观察 settled 时也会拒绝该旧 turn 的 steer；没有新增队列轮询、清队列、子 Agent 生命周期管理或阻止自然退出的兜底。Context reset 仍使用已有的实际消息处理证据；普通投递的 durable ACK 语义由上层保持为 accepted。

类型化 Deferred 的证据也有边界：Pi 0.85.1 的错误 response 只有文本，所以本次仅在结构化 `get_state` 可证 streaming/compacting 时分类为暂不可接收。若拒收后原生恰好已经 idle，会保留原具体 Protocol 错误，不以文本猜测忙碌，也不将所有认证或配置错误笼统重试。最终源码再次运行上述 provider 命令仍为 8/8 通过，`git diff --check` 无报错。独立命令锁同样覆盖 interrupt，发送返回后会重新检查 handle 是否已关闭。
