# 原生执行结束边界实施记录

已确认本机锁定接口：Pi 0.85.1 的 RPC 会输出 `extension_error`（含扩展路径、事件名和错误正文），但 `agent_end` handler 抛错由 Pi 捕获，随后仍会发 `agent_settled`。`pi-subagents` 0.56.0 的 `drainOutstandingWork` 只排空执行；结果 watcher 和通知 batcher 的接受流程仍可在其后。Pi 空闲时收到扩展 `triggerTurn:true` 会直接启动采样。Braid 为 Pi 进程设置 `BRAID_AGENT_RUNTIME=1`，可作为仅针对该接入的原生边界。

实施链：headless `agent_end` 将通知 batcher 切到即时交付，先排空本 session 的有限执行，再直接处理当前 completion owner 已持久化的结果文件，等待 watcher 正在处理的同批文件。以 Pi `sendMessage` 进入原生队列作为通知接受点；仍未接受的结果保留持久文件，作为屏障异常，不报告成功。已接受但因 observer 或文件清理失败而保留的结果，依当前通知接受记录及持久 `notificationDeliveredAt` 识别，不误判为投递失败。Pi 接入模式下，已关闭调用到达的 `triggerTurn:true` 消息只写入会话，不自行启动采样；当前活跃调用内的 follow-up 继续进入原生队列。`agent_end` handler 报错后，Pi 停止本次调用的自动续采，并在 `agent_settled` 前把已入队消息写入 Pi 会话，避免 Pi 关闭时丢失已接受结果；Braid 在当前 turn 接到 `agent_end` 的 `extension_error` 后保存具体错误，到 `agent_settled` 投影为 failed。下一次合法 Braid `prompt` 正常打开新调用并可读取被动积累的消息；历史任务和 service 的迟到通知也只积累事实。Pi 在 Braid 调用中记住 `abort`，即使取消发生在屏障等待期间也不再自动续采，队列同样写入会话；`agent_settled.cancelled` 使 Braid 投影 interrupted。若屏障同时异常，保留具体异常并标 failed。

不改 Braid 对 Pi 子任务的管理职责，不增加任意宽限期或新的跨层消息框架。此记录是源码实施设计；尚未通过实际运行验收。本次未获授权启动实验，当前实验暂停；仓库规则禁止 Factory/Braid 自身测试及改名探针。两份依赖补丁在锁定缓存原件上干跑通过；临时副本应用通过，修改过的 JS/TS、`runtime.py` 与 Rust adapter 语法检查通过，Braid `cargo check --locked` 通过（仅有原有 dead-code 警告）。没有运行完整 runtime 构建、测试或实验。
