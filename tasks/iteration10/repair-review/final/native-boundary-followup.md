# 原生完成边界增量复核

最终静态复核结论：本次审查提出的两处确定边界问题已被实现者修正；在下述范围内，未发现新增阻断。此结论是源码及锁定依赖接口复核，不是运行验收，也不证明现有缓存、已冻结 ZIP 或运行中的 Pi 已升级。审查者未修改源码，未运行测试、探针、构建或实验。

## 审查中发现并收口的问题

| 问题 | 原因与最终修正 | 静态复核结论 |
| --- | --- | --- |
| 取消可被 completion 续轮覆盖 | Pi 原有 `_handlePostAgentRun` 只检查原生队列；`agent.continue()` 会建立新的 core AbortController。排空期间取消后，新增结果仍可能触发续采并产生最终 stop。coding-agent 补丁现在在本次调用记住 abort，在异步后处理前后检查取消，并通过 `agent_settled.cancelled` 传递终态。 | 取消不再依赖最后 assistant 是否仍保留 aborted。Braid 在无屏障异常时投影 interrupted；同时有屏障异常则保留错误并 failed，与实施记录一致。 |
| 把残留文件误判为通知未接受 | watcher 在 notifier 接受后仍可能因标记、observer 或清理失败保留文件；原有 `removeResultIndex` 明确吞掉清理错误以免影响交付。仅用文件非空判失败会阻止已经排队的正常后续处理。最终补丁按持久 `notificationDeliveredAt` 或已接受原 payload 的 state/timestamp 排除已接受结果。 | 接受事实与清理状态已区分。记录绑定送入 notifier 的 payload，而不是 await 后磁盘上可能被替换的内容；沿用上游既有 state/timestamp 替换语义，没有新增任务身份体系。 |

定位：`harness/npm/patches/pi-coding-agent-0.85.1-braid-boundary.patch:12–50`；`harness/npm/patches/pi-subagents-0.56.0-completion-boundary.patch:85–148`；`sources/braid/src/provider/pi.rs:585–614`。两项均已即时反馈主线及实现者，最终补丁重新阅读确认。

## 最终完成链与范围

正常路径是 headless `agent_end` 先令 batcher 即时交付并冲刷已有 batch，等待有限执行排空，再从当前 session 的候选结果中选出当前 completion owner 尚未接受的结果，冲刷文件 coalescer 并等待同文件正在处理的 Promise。随后重新检查未接受结果，仍有剩余则抛出屏障异常。其它已知 owner 的残留不会被归入本次交付，也没有把历史任务所有权转给当前调用。

锁定 Pi 的 `isStreaming` 读取 `_isAgentRunActive`，它覆盖 `agent_end` handler 的整个等待阶段。因此 notifier 的 `sendMessage` 在这条正常路径进入现有 steer/follow-up 队列；该队列入队分支没有 await，不是只创建了未来会启动的 Promise。Pi 随后的 `_handlePostAgentRun` 检查队列并继续父模型处理；只有这一过程退出才执行 settled。锁定 subagent runner 的最终结果写入在最终 `writeStatusPayload` 前，支持屏障结束后从结果索引直接消费的顺序。这里证明的是对应实现路径，不能由此宣称模型已正确理解或完成业务。

屏障错误经 Pi runner 的 `extension_error(event=agent_end)` 发给 RPC。coding-agent 补丁会阻止本次调用继续自动采样；Braid 保留扩展路径和具体错误，在 settled 投影 failed，不因后来一条 stop 抹掉屏障失败。结果排空与通知排空同时出错时，扩展汇合两条错误。新 prompt 接受时重置当前调用错误，不污染下一次合法输入。

调用关闭后，Braid 模式的 `sendCustomMessage(triggerTurn:true)` 不再进入 `_runAgentPrompt`，而是追加会话消息。关闭前已排入队列的结果仍属于当前调用；关闭后到达的历史结果或 service 通知只保存，下一次合法 prompt 才可能消费。Braid 只接收已有执行终态及取消字段，没有管理 Pi 子任务、增加子任务表或自行推断业务完成。

依赖接口核对来源是 `/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed/node_modules/`：Pi `dist/core/agent-session.js` 的 `_runAgentPrompt`、`_handlePostAgentRun`、`sendCustomMessage`、`abort`、`bindCore`；`dist/modes/json-event.js` 对非 message_update 事件原样传递；嵌套 pi-agent-core `dist/agent.js` 的 continue/runWithLifecycle；pi-subagents 的 auto-drain、notify、result-watcher、result-files 与 subagent-runner。缓存原件用于核对补丁上下文及既有语义，不视为已应用补丁。

## 安装接线与证据限度

`scripts/runtime.py:24–52` 将两份补丁列入本地 prepare，比较补丁哈希和所有修改目标的哈希；补丁变化、目标漂移或缺失会触发 npm ci 后重新应用，失败不会写出成功 stamp。缓存目录名虽仍由 lock 决定，但 prepare 的内容判定覆盖本次补丁失效需求。

Linux 构建复制完整 npm 材料和 patches；`submission/Dockerfile:16–19` 在复制 node_modules 后应用补丁，Docker 的 COPY 输入变化会使相应层失效。`runtime.py:91–97` 记录补丁哈希。`scripts/package_agent.py:122–125` 的默认路径新建 Linux runtime，显式传入 runtime 时则复用已有目录。后者及直接使用旧缓存路径不会自动升级，这是冻结/复用入口的现有语义；后续运行必须使用重新 prepare 或重建的材料，不能把源码审查当作安装生效证据。

实现记录报告补丁干跑、临时副本应用及 JS/TS/Python/Rust 语法检查通过；本审查没有重跑这些操作，也没有把它们认作完整类型检查、编译或运行验收。实际效果仍需后续已授权生成中的自然证据对齐：结果 terminal、通知入队、父后续处理、settled；异常及取消需保留对应终态，没有自然覆盖时继续标未证。

最终读取的 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| pi-coding-agent boundary patch | `fe4ea179a6f29f57f2a79b882e3f455582800882a9289c7ffad9907ab3a3fa2a` |
| pi-subagents completion patch | `faaf1cd5f7260bd02861abd8523153fc159d455599420471dd67664d16930e49` |
| scripts/runtime.py | `a0b9d0d6eb16f7968a0649f8f927f4e833d28d3d359491d7add4c6f88bfc4a56` |
| submission/Dockerfile | `da4d160ed183b4e784744a1737a1abab3d86714352e7a203cd35d8abfe3b6626` |
| sources/braid/src/provider/pi.rs | `c9b45b4932fa71f2c40cfa612bfb7d0447c6c0b2af345fde995d133277e16096` |

更省事的产品替代仍是所有结果被动保存并由模型显式 wait；它会改变已批准的有限任务自动收尾行为，本次没有据此缩减范围。复核没有扩展到其它原生执行入口或重新审计历史两题。
