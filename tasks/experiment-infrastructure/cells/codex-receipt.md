# Codex Context reset 消息收据

## 决定与实现

`sources/braid/src/provider/codex.rs` 现在实现 `AgentProvider::message_was_processed`：调用原生 `thread/read` 并设置 `includeTurns=true`，只检查最新 `completed` turn。该 turn 的完整有序 items 必须包含与通知全文一致的 `userMessage`，且其后存在 `agentMessage`。缺失历史、非完整 items 或请求失败不会生成肯定收据。已在 `sources/braid/docs/20-product-tdd/app-server.md` 记录这一边界。

这样，`turn/start` 和 `turn/steer` 的 RPC ACK 仍只代表请求接受；较早 turn 中同文通知、当前 turn 中通知前的 assistant 输出都不能解锁 reset。普通 turn 内自编辑和外部编辑触发的 reset 共用同一收据判断；通知未送达时，现有 GroupDriver 延后补发。

## 契约与实测

本机 `codex-cli 0.155.0` 生成的 v2 JSON schema 定义了 `ThreadReadParams.includeTurns`，返回 `thread.turns[]`，每个 turn 有 `status` 和按序排列的 `items[]`；`userMessage.content[]` 的文本项是 `{type:"text",text}`，assistant 项为 `agentMessage`。公开接口见 [Codex app-server README](https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md) 与 [协议结构](https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/src/protocol/v2/thread_data.rs)。

直接连接本机真实 app-server 的隔离探针（工作目录 `/tmp/braid-codex-receipt-probe`）得到：

- 两个连续 turn 都以 `completed` 终结，`thread/read(includeTurns=true)` 依次返回两个 turn，items 均为 `userMessage → agentMessage`。
- 对第三个 turn，`turn/steer` 返回 ACK；终结后最新 turn 的原生 items 为 `userMessage(原始) → agentMessage(开始) → userMessage(通知) → agentMessage(结束)`。因此通知前的 assistant 活动不足以成立收据，通知后的活动可以成立。
- Braid 内的最小收据断言覆盖旧 turn 有同文消息、最新 turn 通知后无 assistant、通知后有 assistant、最新 turn 非 completed 四种状态。

探针读回的关键原始字段（线程 `01a0e585-6018-7fc3-852e-61f3cb35af3c`）：

```text
turn_order [{"id":"01a0e585-60ff-73b2-89e1-405004eaaf6f","status":"completed","item_types":["userMessage","agentMessage"]},{"id":"01a0e587-0130-7600-9e9d-b39d6916d978","status":"completed","item_types":["userMessage","agentMessage"]}]
steer_ack true
terminal completed
latest {"id":"01a0e587-c180-70b0-b5e0-552783e4d461","status":"completed","items":[{"type":"userMessage","content":[{"type":"text","text":"Braid steer receipt 11731846-8756-475c-a686-cc8ce00d050c。请仔细思考，然后回复一词：开始"}]},{"type":"agentMessage","text":"开始"},{"type":"userMessage","content":[{"type":"text","text":"补充通知 Braid steer receipt 11731846-8756-475c-a686-cc8ce00d050c。现在回复一词：结束"}]},{"type":"agentMessage","text":"结束"}]}
```

完整 Braid 工作项的自编辑及外部编辑 reset 链路尚无 Codex 真实 run；当前活动验收环境使用 Pi，不能把上述协议探针说成端到端验收。
`thread/read(includeTurns=true)` 读取整段历史；若长会话触及现有 30 秒请求超时，可改用新版本的分页 turn/items 接口，但要先确认目标 Codex 版本的能力。

## 验证状态

`git diff --check` 与 `cargo check` 通过。`cargo test receipt_tests` 首次尝试被并行修改中的 `src/group/pr_agent.rs` 未闭合 delimiter 阻断；重试时 test 编译又被 `src/local.rs` 等处对已更新接口的 33 个不匹配错误阻断，尚未运行到本断言。共享测试源码收敛后需重跑。
