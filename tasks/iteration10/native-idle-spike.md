# Pi 后台工作与空闲边界：原生接口核实

本记录针对锁定的 Pi 0.85.1、pi-background-bash（PBB）1.0.5、pi-subagents 0.56.0。结论来自这三个已安装包的源码；还没有用模型回合验证端到端时序。

## 真实接口与失联路径

`pi-subagents/src/api/background-work.ts` 已提供进程内 `registerBackgroundWorkProvider({ name, listActiveWork })`。每个工作项只需 `{ id, sessionId }`。其 `agent_end` 处理器在无 UI 模式调用 `drainOutstandingWork`，把当前 Pi session 的 provider 项纳入 `subagent_wait({ all: true })`，最长等待 30 分钟。session identity 是 `sessionManager.getSessionFile() ?? getSessionId()`，通常为 session 文件路径，不能用 PBB 自己的 UUID。`subagent_wait({ id })` 只匹配原生子任务，不匹配 provider 项。

PBB 的 `activeJobs` 是模块私有 Map，两个进入后台的分支都会调用 `pendingJobs.start`，完成时先删除作业，再 `pendingJobs.finish` 并发送 `background_bash_result` follow-up。PBB 当前没有注册 provider，且 `bash` 工具只有 `command`、`timeout`、`background` 参数；文案把有限任务和 dev server/watchers 混为同一类。Pi RPC `get_state` 只有模型活动、压缩、待处理消息数等字段，没有扩展作业列表。Pi 的 `agent_settled` 在 agent prompt 与其队列续轮结束后发送；若 PBB 未注册，Pi 可以在后台进程仍活跃时 settled，随后关闭会触发 PBB `session_shutdown` 的 `abortAllJobs`。

Pi `tool_call` 可在执行前原地修改参数，但不拥有 PBB 私有作业的完成状态。覆盖 `bash` 工具需要接管其执行。独立适配扩展可以读 `pi-pending.list()`，但 PBB 仍须在两个 `pendingJobs.start` 写入归属与作业类型；这样还要维护第二处状态解释代码。最小方案是由 PBB 自身持有注册，直接从已有 `activeJobs` 列举当前活跃且需要结果的后台作业，无需 Braid 新接口。

## 已授权实施路径

给 PBB 的 `bash` 增加 `service?: boolean`，默认 `false`，用于明确声明无需等待完成的常驻服务。`service: true` 本身立即后台化，不要求再传 `background: true`。后台化时记录准确 Pi session identity 和 `service`，并在现有 `pendingJobs.start.details` 保留同样元数据。PBB 加载时向已安装的 `pi-subagents/background-work` 注册 provider，只列举非 service 的可见后台作业；在 session shutdown 解除注册。同步 PBB 工具描述，dev server/watchers 应显式 `service: true`。无须修改 Braid 的 busy/idle 或 RPC 协议。

PBB 与 pi-subagents 已同在 `harness/npm` 锁定依赖内。补丁应保留为可审阅的统一 diff，通过 `scripts/runtime.py` 本机准备和 `submission/Dockerfile` Linux `npm ci` 后同样应用，不能只改现有 `node_modules`。`scripts/runtime.py` 的缓存键仅基于 lock，故补丁校验值也必须参与准备状态检查。没有新包版本。

主 Pi 的 `run.py` 加载 pi-subagents、PBB、observer；pi-subagents 启动 executor/explorer/advisor child 时，以 `--mode json -p` 执行并按角色 `extensions` 传入 PBB，未加载 pi-subagents 本身。因此仅注册 provider 不能保护 child。PBB 在所有无 UI 会话的 `agent_end` await 自己非 service 作业已经持有的 `runPbbBash` 完成 Promise，再排入完成 follow-up。主 Pi 的 pi-subagents handler 先 drain，正常完成时 PBB 没有剩余作业；若它达到 30 分钟上限，PBB 仍等自己剩余的有限作业。child 也由 PBB 自己等待。这里没有定时轮询和 Braid 内部状态。

还需解决一个既有时序：PBB 在 agent 正忙时把完成 follow-up 暂存，到 `agent_end` 后用 `setImmediate` 发送。provider auto-drain 在 `agent_end` 中等到作业结束后，该延时发送可能落在 Pi `agent_settled` 之后。Pi 0.85.1 的 `sendCustomMessage(..., { deliverAs: "followUp", triggerTurn: true })` 在 agent run 期间把消息加入原生 follow-up 队列，而 `_handlePostAgentRun()` 会在 settled 前检查该队列。因此 PBB 应在自己的 `agent_end` handler 内直接冲刷暂存消息，使有限作业完成结果进入同一原生续轮，再发 settled；不另开队列或改 Braid。`service:true` 退出后不应自行触发新回合，仍以 `triggerTurn:false` 将回执写入 Pi 原生历史；运行中则在当前回合末写入，空闲时立即写入，供后续合法输入消费。

超时边界仍在：pi-subagents 的主会话 auto-drain 最长 30 分钟，到期抛出错误；Pi `ExtensionRunner.emit` 捕获 handler 错误并发 `extension_error`，不会自动把超时转成模型可处理的消息。它随后继续执行 PBB 的 `agent_end` handler，后者仍等自己剩余的有限作业完成，避免这类 PBB 作业因 `agent_settled` 后会话关闭而被提前中止。其他原生子任务的 30 分钟边界未改变；不能把这个保障扩大为所有 provider 工作必定完成。取消时沿 PBB 既有 `abortAllJobs` 停止进程。

## 实施与验证

原始 PBB 1.0.5 `extensions/background-bash.ts` SHA-256 为 `e786934d50d5e05cee5ed43548ded060f240ae2697040f126a2c8db996136489`；当前补丁在 `harness/npm/patches/pi-background-bash-1.0.5.patch`，SHA-256 为 `ff7631410d121043d382eaf3671bc31922172cbad67242a5908ab3f298320b38`；应用后文件 SHA-256 为 `79c3a3f33840af02fef47d66ec745394e16d0c18665e008315f826af3ed6178b`。当前补丁对原始锁定包的 `patch --fuzz=0 --dry-run` 与 `git apply --check` 均通过。`scripts/runtime.py prepare` 用补丁与结果文件摘要判定缓存有效性，错版时重新 `npm ci` 后应用；`submission/Dockerfile` 在 Linux runtime 复制 npm 包后应用同一补丁。`runtime-source.json` 记录补丁摘要，打包时随 runtime 一同进入制品。

先前 SHA `c58d66c3e…` 版本曾用锁定的 Pi 0.85.1 RPC 原生进程分别加载「仅 PBB 的 child 形态」和「pi-subagents + PBB 的主 Pi 形态」，两者 `get_state` 成功、退出码零、无 `extension_error` 和 stderr。一次临时原生扩展还在 `session_start` 中用 `listBackgroundWorkProviders()` 和 `pi.getAllTools()` 核实 PBB provider 已注册、bash schema 有 `service` 字段，结果同样无扩展错误。当前补丁只把服务回执改为不触发新回合，已核对 Pi 0.85.1 `sendCustomMessage` 的原生存储分支及补丁可应用性，未重跑原生加载；先前检查也未证明 bash 作业完成时序、实际模型 follow-up 或新 Linux 包，后者须在获授权的新运行中观察。未做 Factory、设施或 Corpus 测试，未启动模型实验。常驻服务的分类不能从 command 字符串或 timeout 推断，调用者须显式设置 `service: true`。
