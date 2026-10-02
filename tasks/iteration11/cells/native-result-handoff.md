# I11-05：原生后台结果交接

2026-09-29。状态：源码补丁已完成，固定版本补丁应用、语法和静态依赖编译已核对；待主任务接入缓存目标清单，真实运行时序尚未验收。未打包、部署、提交或干预 I10。

## 授权与范围

协调任务转达用户“明确同意 I11-03/05 修复方案并授权应用”，本单元负责 05 的 Pi/PBB/subagents 补丁。随后明确允许修复实际 Pi 入口，并要求核实随 runtime 分发的模块依赖。03 的 Braid 消息门禁由另一负责人实施。

本单元只修改 `harness/npm/patches/pi-background-bash-1.0.5.patch`、`pi-subagents-0.56.0-completion-boundary.patch`、`pi-coding-agent-0.85.1-braid-boundary.patch` 和本记录。未修改 Braid、其它成员源码、当前运行或生成应用。

## 已确认的断点

### RPC 的 UI 能力被误当成无需收尾的交互模式

已读 [批准方案](reset-handoff-design.md)、[后台重建审查](../run-audit/github/cells/root/background-reset.md)及冻结部署源码。Pi 0.85.1 的 `ExtensionContext` 明确区分 `mode` 与 `hasUI`：mode 为 tui/rpc/json/print，hasUI 在 TUI 和 RPC 都为真。`rpc-mode.js` 的 rebindSession 安装 createExtensionUIContext；runner.hasUI 判断该对象是否为 noOpUIContext。因此 Braid 的 `--mode rpc` 会使 PBB 和 subagents 原有的 `if (!ctx.hasUI)` 等待分支跳过。

这解释了为什么已有 agent_settled 仍能早于有限后台作业结束：agent_end 没有等待作业，Pi 随后就能报告 settled；后台完成还可能自行开启一次没有对应 Braid active turn 的原生模型调用。无需新增 settled 事件或另一个等待器。

PBB 的 ownerSessionId 与 subagents 的 resolveCurrentSessionId 都使用 `getSessionFile() ?? getSessionId()`，不是已证的 UUID/文件名不一致。background-work 注册表使用同一个 `Symbol.for("pi-subagents.background-work.v1")`，原部署也确有注册代码。审查记录中的一次 subagent_wait 返回“无已登记工作”仍缺少当时注册表快照，不能以此次静态核对伪造其唯一原因；本轮没有据此添加第二套登记机制。

### 正常关闭先丢弃了本应落盘的完成结果

部署 PBB 的 abortAllJobs 先设 shuttingDown、发送 abort/TERM、清空 activeJobs；session_shutdown 随后清空待回包队列，不等待作业的 close 回调。deliverBackgroundResult 又在 shuttingDown 时提前返回，位置在 recordPbbJobCompleted 之前。因此即使子进程随后实际退出，也可能没有终态记录。原现场保留 running/null、Pi 与子进程 PID 均消失、日志只到 12/51，与这条路径相符；仍不能据此追认每个历史 job 的具体信号或退出值。

### 实际 Pi CLI 未加载已有 Braid 边界补丁

本次通过 SSH 只读核对的冻结 runtime：

`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--github-7fe42a1248f9d8/workspace/official-generation/submission/agent/runtime`

其 `bin/pi` 执行 `node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js`；该入口静态导入 `chunks/chunk-JVUZSMYM.js`，其中包含 AgentSession 实现，没有转入 `dist/core/agent-session.js`。现有 `pi-coding-agent-0.85.1-braid-boundary.patch` 只修改后者。因此，**该补丁的 agent_settled.cancelled、agent_end 失败/取消后的队列保留、Braid 下禁止空闲 follow-up 自启 turn、abort 标记**未被这条 bundle CLI 路径采用。不是所有 Pi/PBB 补丁都失效：PBB 和 subagents 是另外装载的 TypeScript 扩展，WSL 文件中确实存在其既有改动。

WSL 读取到的身份：

| 冻结文件 | SHA-256 |
| --- | --- |
| PBB extensions/background-bash.ts | `79c3a3f33840af02fef47d66ec745394e16d0c18665e008315f826af3ed6178b`，与审查归档一致 |
| subagents src/extension/index.ts | `9f2d7398554d65db6733505c8b815b436290235780a7cb7122b356f23f46f3cd` |
| Pi dist/core/agent-session.js | `bd90787a5f7bac651d99a45a2e7cdc508973cfe5302f8a78036b5379ae9840a6`，已有补丁，但不是 bundle CLI 的执行对象 |

## 修复

1. PBB 与 subagents 以 `ctx.mode !== "tui"` 进入已有收尾路径，RPC/json/print 都等待有限工作。PBB 仍排除 service；subagents 仍使用原 drainOutstandingWork 和 result watcher，没有新增轮询器或 Braid 内部任务调度。
2. PBB 的 completion promise 包括完成结果持久化回调；先保存结果，再从 activeJobs 移除。session_shutdown 取消自己拥有的作业，等待现有 completion promises 都收尾后再清空通知与注销 provider。正常取消保存实际 close 的 exitCode、signal 和既有日志路径，沿用原 outcome=abort，不将请求取消当作取消成功。
3. process exit 无法等待子进程 close 时，仅尽力保存 unknown，不编造 exit。SIGKILL 等来不及执行 hook 的情况，由读取端将“owner 已不可用且只有未完成记录”呈现为 unknown，保留 recordedStatus。常驻 service 不阻塞 agent_end，但在 session_shutdown 取消并保存停止结果。
4. PBB status/tail 接受已返回的全局 ID `INSTANCE:bgNNN`，从原有各 session 元数据目录读取旧结果；短 ID、列表和 kill 仍保留原有范围。当前列表为空只描述当前 scope。读取进程状态时，若没有 pi-lane 登记，使用 PBB 自己 identity.json 已记录的 owner PID，避免把未装载 pi-lane 扩展的活动 PBB 一律当成失联。PID 存在只作为当前 liveness 线索，不证明历史完成或取消。
5. 将现有 bundle/cli.js 与 bundle/rpc-entry.js 改为分别导入 `../cli.js`、`../rpc-entry.js`，保持原入口路径与参数。这样正常 CLI 和 RPC entry 都使用随 npm 包分发、已受边界补丁修改的模块。该路径经过 main → modes/rpc → agent-session-runtime / agent-session；Braid 仍只消费原生边界，不管理内部 job/PID。

## 验证与必要接线

三个最终补丁在隔离副本上对固定 0.85.1 / 1.0.5 / 0.56.0 原文以 `patch --fuzz=0` 完整应用；八个目标 JS/TS 文件均通过 Node 语法解析，没有执行模块。对应用后源码的 diff 空白核对没有诊断。直接对 patch 文本执行 diff --check 会把 unified diff 的上下文前缀空格识别为缩进/行尾空白，本轮未改写这些补丁格式必需字符。

对现有完整 Linux runtime 中未打包 cli/rpc-entry 的模块依赖图进行了 esbuild 内存编译（write=false，不产出交付包、不运行模块），两入口共解析 2,080 个输入文件，无编译警告；随后在上述 WSL 冻结 runtime 逐项只读核对，2,080 个文件全部存在。除 Node 内置模块外，编译图留下的外部引用为 supports-color、bufferutil、utf-8-validate，属于依赖中的可选加载路径；本轮没有新增 npm 依赖。此核对建立静态分发可达性，不代表平台原生库、动态加载或会话行为已经实际运行验收。

**主任务集成还需同步 `scripts/runtime.py` 的 patch target_names**：PBB 加入 `bin/pbb.js`；Pi 加入 `dist/bundle/cli.js` 与 `dist/bundle/rpc-entry.js`。现有 Dockerfile 已按同名补丁应用，无须新增补丁入口。由于本单元权限限于 harness/npm/patches，缓存目标清单交由协调任务接入；否则缓存校验不会覆盖新增目标。现有补丁 hash 变化会触发重新准备，但不能代替目标文件完整性记录。

本轮未运行测试、模拟探针、Pi 会话或模型实验，未部署。最新 comment220 的“恢复终止后台”仅作为协调任务提供的定位线索，没有拿模型自述当作杀进程证据，也未改动 setsid 作业。真实验收仍需在获授权的新运行中观察：RPC 有限任务结束及结果进入消息/持久记录之后才 settled；正常关闭记录实际终态；强制退出只报告 unknown；重建后的旧 globalJobId 可读，不因 current-scope=0重复启动检查。03 的并发消息投递与交接还需由主任务共同验收。

## 主线集成完成

2026-09-29已将上述三个新增文件加入scripts/runtime.py的target_names，既有patch hash与逐目标文件hash机制不变；Python compile语法核对通过。补丁hash变化本身已使旧缓存失效，本次补齐的是新增目标的持续校验覆盖。未运行prepare、打包或部署，真实行为仍待实验。
