# Sheet 17bffdd4a8b0 长时间运行调查

2026-09-25 23:23（北京时间）按用户要求检查[官网 run](https://arc-bench.com/runs/17bffdd4a8b0)。本次只读采集平台与原生记录，并对生成应用自身的原有自测做一次 10 秒限时隔离复现；未修改远端、源码或应用，未恢复/取消运行、未调用模型。

**长期没有结果的直接原因是：应用自测脚本遗留后端子进程，输出管道无法结束；两名 Agent 先后进入同一阻塞，无默认超时的工具与外层进程等待把它持续放大。** 用户手动暂停是观察到异常耗时后的操作，仅作为调查截止背景，不是耗时原因。根 Agent 和后端 Agent 都在等待这份脚本返回，官方评测尚未开始。

## 暂停前的时间消耗与完整阻塞链

用户进一步明确要分析“为什么这么久还没有结果”，据此补查了原生调用开始/返回时间和本次冻结包中的真实等待实现。

| 北京时间 | 已核实事件 | 时间的含义 |
| --- | --- | --- |
| 19:24–19:28 | 启动后分为公式引擎、后端与前端三个子 Issue。 | 实现与集成开始。 |
| 19:58:52–20:51:19 | 后端 Agent 的一条 `api.smoke.js | tail -6` 调用持续 3147 秒。 | **第一次挂起约 52 分 27 秒**，直到根 Agent 清理进程才返回；返回内容是 `actual: '' / expected: '2000'` 的失败断言。 |
| 此次挂起期间 | 其他工作项仍有活动；根 Agent 在 20:39 修复后端与公式接线，20:42 遇到模型代理 HTTP 400/connection reset 后被恢复。 | 该阶段有实际工作和恢复成本，不能把后端 52 分钟等待全部等同于全团队停工。 |
| 20:51:19 | 根 Agent 杀掉自 19:58 遗留的 shell 与后端进程。后端原先悬挂的调用立即返回。 | 已有远端原生证据直接把残留进程与等待结束关联起来。 |
| 20:53:02 | 根 Agent 修正行插入的双重位移。 | 修复了业务集成错误，但没有修改自测的进程清理逻辑。 |
| 20:53:43 / 20:56:06 | 根 Agent 和后端 Agent 分别再次运行同类自测管道，都没有收到结果。 | **第二次挂起覆盖两个剩余活跃会话**。 |
| 至少到 23:15:32 | 平台仍报告 RUNNING，两份原生轨迹仍停留在上述工具调用。 | 两者共同无新结果至少 **2 小时 19 分钟**；根会话单独等待超过 2 小时 21 分钟。 |

等待没有自行结束的原因分为三层：

1. **应用自测的缺陷**：重启后的后端没有被清理，继承的输出管道不关闭，`tail` 收不到 EOF。失败信息已经产生，也不能返回给调用者。
2. **Agent 工具调用无截止时间**：这三条悬挂调用都没有传 `timeout`。本次 ZIP 内 Pi 的 `bash.js` 明确声明 `optional, no default timeout`，只有实际传入 timeout 才设置终止计时器。因此不能期待它默认几分钟后自动报错。
3. **生成阶段仍等待底层结束**：冻结包的 `agent_support.logged()` 调用没有 timeout 的 `proc.wait()`；variant 在它返回以后才执行 `load_delivery → export_delivery → deliver`。本次底层没有返回，生成无法完成，平台也就没有进入部署和评分。

已有监控读取平台状态和终态，不检查原生工具长时间未返回，所以 RUNNING 没有变成无进展告警。它不是本次运行阻塞的制造者，但也没有识别出这一异常。

可见根 Agent 曾发现并干预第一次挂起，但只清除了残留进程，没有消除重复产生残留进程的脚本缺陷；之后它自己也进入了同一无界等待。这解释了为何已有排障动作，仍会继续耗费两个多小时。

新增证据：[自测调用时间对照](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/smoke-command-timing.json)、[冻结包的 Pi Bash 实现](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/frozen-harness/runtime/node_modules/@earendil-works/pi-coding-agent/dist/core/tools/bash.js)、[冻结包的进程等待实现](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/frozen-harness/support/agent_support.py)、[根 Agent 首个会话](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/01a0d84f-c1c4-7725-bbf3-d215809e2cbf.jsonl)。

## Pi 的执行职责与已有保护

用户追问工具执行既然由 Pi 负责，为何仍会出现这种等待。补查本次冻结包中的 `@earendil-works/pi-coding-agent` 与 `pi-agent-core`，版本均为 **0.85.1**。需要区分生成脚本的错误、Pi 的执行契约，以及无人值守接入的完成保障，不能把现象直接定性为 Pi 的进程回收实现失效。

Pi 已提供以下保护：显式 `timeout` 到期或收到 abort 时调用 `killProcessTree`；本次 Linux 路径通过负 PID 向进程组发送 SIGKILL。`waitForChildProcess` 也专门处理“直接子进程已经退出，后代仍持有 stdout/stderr”的情况：收到直接子进程的 exit 事件后，等待输出空闲 100 毫秒即可返回，不会只依赖 close 事件。

本次 Pi 直接启动的是 shell。生成脚本遗留的后端让 `tail` 等不到 EOF，shell 又在等待前台管道完成，因此 shell 本身尚未退出，达不到上述退出后保护的触发条件。与此同时，bash 工具明确没有默认 timeout，本次调用也未指定它，所以没有启动另一条定时终止路径。Agent 主循环在 `await prepared.tool.execute(...)`，这两个会话不会在同一工具仍未返回时自行再发起一轮模型判断。

因此，当前证据支持“调用落入 Pi 允许的无期限等待，未建立适合无人值守运行的等待策略”，不支持“Pi 的超时已经启动却不起作用”或“Pi 没处理后代持有输出管道”。用户随后要求达到等待阈值时通知 Agent、保留进程，当前处理方向已改为让工具返回仍在运行的执行标识，由 Agent 决定继续等待或停止。Pi 原生 timeout 会终止进程，不能用它直接实现这一软等待行为；修复当前应用自测只解决当前触发点。具体方案与验收已同步到任务包，本次未改实现。

冻结证据：[退出后管道保护](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/frozen-harness/runtime/node_modules/@earendil-works/pi-coding-agent/dist/utils/child-process.js)、[进程组终止实现](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/frozen-harness/runtime/node_modules/@earendil-works/pi-coding-agent/dist/utils/shell.js)。上游当前的 [Bash 工具](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/tools/bash.ts)和[进程等待实现](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/utils/child-process.ts)也保留上述相关行为；对本次运行的判断以冻结包为准。

## 运行环境假设的核查

用户说明日常使用 Pi 从未遇到同类问题，要求判断运行环境的可能性。现有证据不适合换算成概率；需区分“ARC 容器、操作系统或资源故障制造阻塞”和“无人值守调用方式缺少期限，放大生成脚本缺陷”。后者有已知证据，前者目前支持较弱，但缺少暂停前完整资源指标与用户日常 Pi 的同条件对照，不能完全排除。

原隔离复现在 macOS / Node 24.15.0 的普通 shell 中执行，未经过 Pi、Braid、官方容器或模型服务，仍出现测试主进程退出而服务器与 tail 存活的现象。远端是 Linux / Node 24.10.0；远端第一次悬挂也在清理遗留进程后立即返回。因此平台专属故障不是产生该阻塞机制的必要条件。

进一步追查最后的持久化失败，发现生成自测前面已经删除透视源工作表：先新增空白工作表，再删除原工作表，并断言删除成功（原脚本 533–536 行）。最后却读取重启后 `sheets[0].C1`，仍要求它等于已删除工作表里的 `2000`（588 行）。这项断言的前提已被前面的测试破坏。

为区分数据原本已删除与重启后丢失，在临时副本中仅增加重启前 API、磁盘文件及重启后 API 的观察输出，保留全部断言及原进程清理逻辑。原有应用自测在 0.678 秒后退出码 1；三处数据均为同一空白 `Sheet2`、零单元格、无 C1，说明该失败在本地复现中不源于重启或磁盘持久化丢失。命令直接输出到日志文件，未接 tail，因此测试主进程可以立即返回；遗留后端由外部 finally 清理整个隔离进程组。未调用模型、运行官方 benchmark 或测试 Factory/Pi 基础设施。

此外，即使最后断言成功，外层 finally 仍只清理旧 child，重启后的 child2 仍可能保留管道；失败断言不是该进程泄漏成立的必要条件。

原生记录确实出现过更早的环境相关错误：19:44:25 有 `EADDRINUSE 127.0.0.1:3457`；根会话 20:42 有模型代理 HTTP 400/connection reset 后恢复。这些错误应保留，但之后会话继续推进，不能据此解释 20:53/20:56 开始的最终等待。第一次长等待时的 ps 还显示 shell 与服务器处于睡眠状态、CPU 0.0%，与等待管道相符；这一快照不能替代完整容器资源监控。

补充证据：[重启前后及磁盘状态](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/environment-causality/result.json)、[完整观察输出](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/environment-causality/observed-test.log)、[临时副本仅增加观察的差异](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/environment-causality/observation-only.patch)。

## 当前状态与最后进展

| 项目 | 观察 |
| --- | --- |
| 平台状态 | `PAUSED`，`failure_reason=Execution paused by user request`，`can_resume=true` |
| 平台日志 | `[arcbench] Pause requested; stopping runner immediately` |
| 启动时间 | 北京时间 19:24:41；到本次查询相隔约 3 小时 59 分钟，不能把其中暂停时间也算作有效执行 |
| 当前阶段 | 环境准备完成；应用生成未完成；评测 pending；尚无分数 |
| 费用 | 平台当前记录 `18.734651 CNY` |
| 最近一次仍运行观测 | 本地监控于 23:15:32 记录 RUNNING；本次 23:23 查询为 PAUSED，未取得准确暂停时刻 |
| 根 Agent 最后工具调用 | 20:53:43，运行 `node backend/test/api.smoke.js 2>&1 | tail -30`，没有后续工具结果 |
| 后端 Issue #3 最后工具调用 | 20:56:06，先检查单元格变更，再运行 `node backend/test/api.smoke.js 2>&1 | tail -4`，没有后续工具结果 |

从后端 Agent 的最后记录到 23:15 的 RUNNING 观测，至少有 **2 小时 19 分钟没有新的原生结果**。会话清单仍把二者标为 running，这是暂停前保存的内部状态，不能解释为暂停后进程仍然运行。

## 挂起机制与复现

生成应用的 `backend/test/api.smoke.js` 在启动时将后端进程保存为局部常量 `child`，同时赋给 `ctx.child`。最后的持久化测试终止旧后端，启动 `child2`，再将 `ctx.child` 更新为新进程。然而外层 `finally` 仍执行 `child.kill('SIGTERM')`，只处理了旧进程。

新后端使用 `stdio: ['ignore', 'inherit', 'inherit']`，继承测试命令的输出管道。测试主进程调用 `process.exit` 后，新后端继续运行，管道仍有写端；末尾的 `tail` 一直等待 EOF。两条原生 bash 调用都未设置 `timeout`，所以 Agent 收不到最终工具结果。

使用只读下载的当前后端源码及原有自测，在本机 Node 24.15.0 上执行同类管道，并用外部 10 秒期限保护：

- 前 24 个检查输出通过。
- 最后的持久化检查在 `api.smoke.js:588` 失败，实际值 `''`、期望值 `'2000'`。这是本地复现结果，不是官网 benchmark 的评分；后续环境核查已确认该断言依赖的原工作表此前被测试自己删除，详见前文。
- 测试主进程已经退出，进程快照仍有 PPID=1 的 `node server.js`、`tee`、`tail`；管道在 10 秒后仍未结束，`tail_output` 为空。
- 外部限时结束后，已清理此次复现的整个独立进程组，没有修改脚本。

原生记录还显示，根 Agent 在 20:51 已发现并清理过一次相同自测遗留的服务，随后修复了行插入时的双重坐标平移，再次执行自测后又陷入等待。这支持问题出在自测进程生命周期，而非正常的长时间模型推理。

本地复现环境与官网 Linux 环境不同，但管道结构、脚本缺口与两个 Agent 的最后待返回命令一致，足以定位直接阻塞机制。当前暂停状态下未取得远端实时进程表，不能声称已直接看到暂停前远端最后一条断言。

## 处理建议与证据

保持现有证据后，应让自测清理当前的后端子进程，并按用户修正让工具达到等待阈值后返回“仍在运行”与执行标识，通知 Agent 自主判断后续操作；阈值本身不杀进程。最后的持久化检查应依据实际保留的数据断言，不能要求恢复此前已经删除的工作表内容。仅延长等待时间不会消除已经复现的管道等待机制。恢复运行、修改应用或 Harness 属于后续操作，本次没有执行；新增观察仅位于已清理的临时副本，差异作为证据保留。

证据目录为 `runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/`：

- [平台状态](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/status.json)与[平台日志](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/logs.json)。
- [根 Agent 原生记录](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/01a0d896-871e-778a-ad37-ffe5623b8faf.jsonl)与[后端 Agent 原生记录](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/01a0d852-e8de-748c-8419-3698c035c882.jsonl)。
- [原有应用自测源码](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/source/backend/test/api.smoke.js)、[限时复现结果](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/smoke-reproduction.json)、[完整输出](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/smoke-reproduction.log)与[清理前进程快照](../../../runs/issue-decomposition/20260925-hackathon/analysis/17bffdd4a8b0/20260925-152347/smoke-processes.txt)。
