# I13-2：OOM 防范与执行接续的实施准备

2026-10-01，主线转达用户已同意 [OOM 方案](../../experiment-signal-diagnostics/packet.md)，将本轮改进作为 I13-2，并热恢复到 I13；本地两项运行已由用户暂停。本文件收敛可分派的实现边界，不重新申请这些范围的授权。此准备轮只写本文档，没有改源码、部署、调用模型或恢复运行。热恢复的具体来源、停止事实、费用模式和冻结制品仍由 I13 主 packet 记录；本文件不启用收费新 run 自动恢复。

目标是在有限资源下继续完成既有任务：启动前保留执行余量，工具收到可诊断的压力事实，静止成员释放驻留进程，异常成员在旧执行确认停止后接续原历史。沿用当前职责：Braid 管理工作项、逻辑成员、输入及 provider-neutral 会话；Pi provider/native 接入管理工作项内子 Agent、bash 和后台作业。Braid 不解释 PBB/subagent 私有作业种类、命令语法或结果协议。不得把原生作业表整体搬进 Braid store。

本文保留实施准备时的接口调查。最终选定共享 Python helper 与短期 `flock`，不向 Braid store 增加资源表；原生接入拥有作业结果。当前实现契约见[运行资源约定](../../../docs/product-tdd/runtime-resources.md)，源码和实际操作状态见本组 [packet](packet.md)。下文候选不是并行保留的现行方案。

## 已有接口与需要补齐的边界

`SessionManager::remove/resume` 已提供停止证明先于同身份 resume 的入口。worker 每两秒检查可恢复 provider session；Unknown 保留旧 turn、provider ID、clone 和 native 文件，成功后由 `record_provider_resume` 排入一次按旧 turn 去重的核对接续事实。`PiProvider::close_native` 现在只关闭 stdin 并 wait 父进程，而且把非零退出当作停止证明失败；该错误通过 `stop_failure`、`fatal_stops` 扩大为全 run blocked。父进程 wait 已结束与作业树停止须分别记录，不能仅将 nonzero 分支改成 `Ok(())`。

OPEN idle session 仍在 `provider_resume_candidates` 中，`retain` 会保留它；直接关闭后还会被两秒恢复循环拉起。当前 sleeping 只覆盖 CLOSED/MERGED 且无真实输入的成员。每 kind/profile worker 每 tick 可以再启动一个 turn，`running` 集合无容量限制；`SchedulerConfig` 只有 quiet window 与 event threshold。

原生材料已有可复用基础。当前三份 dirty patch 在非 TUI `agent_end` 排空有限 background bash、subagent 和完成结果，再让 Pi 发 `agent_settled`。PBB 的 `service:true` 不参与有限作业 drain，但仍在 shutdown 中停止。`pi-subagents` 0.56.0 的 background runner 已有 `owned-process-tree.ts` 和 `process-terminal.ts`；async runner、其 child Pi 以及 PBB bash 使用 detached 进程，foreground child Pi 则沿父组运行。因此给顶层 Pi 单独 PGID 仍不足以覆盖已有 detached 作业，必须由原生接入保留这些作业的 owner/终止收据。

本次核对的安装入口是 `harness/npm/package-lock.json` SHA `9b7aa8110d9b2b2befeab075b0c11019a02445d900091e41044dad427d352e4a` 对应缓存。实现者以 lock 和完整现有 patch 组装出的制品为准，不将其它 runtime 缓存的同名源码当基线。

## 四块分派与文件 ownership

| 工作块 | 实现者负责的文件 | 交付接口与边界 |
| --- | --- | --- |
| A：Pi owned execution 停止及 Unknown 恢复 | `sources/braid/src/provider/pi.rs`、`sources/braid/src/provider/process.rs`、`sources/braid/src/provider/factory.rs`、`sources/braid/src/agent_session.rs`；必要的 `group/session_manager.rs` 停止结果消费由 A 持有 | Pi provider 消费原生停止收据，分别保留父 wait 结果与 owned execution 停止结果；通用 session 层只接收停止成功/失败。已异常退出且 owned execution 已停，允许既有 Unknown→同身份 resume；停止不明继续保留现场及 ownership，不启动第二写者。 |
| B：OPEN idle 卸载及按需恢复 | `sources/braid/src/group/worker.rs`、`sources/braid/src/group/dispatch.rs`、`sources/braid/src/store/mod.rs` 的候选/claim/lifecycle 部分；需要新持久字段时新增后续 migration，不改旧 migration | 区分逻辑 idle 与物理已卸载，不改变 assignment、member、clone 或 native 身份。只在原生确认静止且没有待投递输入/reset 时释放；真实输入或必要恢复才启动，不再遍历恢复所有 OPEN idle。原生进程不可恢复仍沿既有明确错误与 HistoryUnavailable 边界。 |
| C：采样、共享资源准入及压力反馈 | `scripts/agent_support.py`、`lab/otlp.py`；Braid 侧新增一个聚合资源模块，接线 `sources/braid/src/config.rs`、`local.rs`，如选择 CLI 候选再接 `cli/mod.rs`；`variants/pi-braid-i13/run.py` 的 policy/路径接线由集成者持有 | 现有 collector 产同 attempt 最新原始样本与有界压力事实；所有 Braid 物理 start/resume/reset/reactivation 及正常 turn 启动共享同一个 run 资源判断。Braid 保留待执行输入；压力判断/上限不按角色或模型权限分类。工具收到同来源资源事实。C 不管理工具私有生命周期。 |
| D：原生工具并发预算与作业停止/静止收据 | `harness/npm/patches/` 下 Pi、PBB、subagents 的本次原生增量；upstream targets 见下文。`scripts/runtime.py` patch target/顺序及 I13 原生材料接线由集成者串行完成 | 覆盖 foreground/async runner/child Pi/PBB bash 的实际 spawn、完成、abort 和 shutdown。原生接入提供 provider 可消费的聚合静止/停止收据；工具 spawn 前短路拒绝资源不足，返回资源事实和部分已执行情况，不等待父进程占用的槽位。保留工具原有并行参数，提供预算建议，不改写任意 shell。 |

A 与 B 的 `session_manager.rs`/worker 调用接口先约定，再串行接线。B 持有 `store/mod.rs` 工作项状态；C 若选共享 SQLite 准入，仅提交独立资源 accounting 部分，由 store 文件 owner 合入，不能同时编辑整个 store。D 是全部原生 patch 的唯一写者；A 只定义 provider 需要的聚合契约，由 D 交付。四块可以分派调查与独立文件实现，重叠文件由单 owner 整合。

D 的上游实际入口为：Pi `dist/core/agent-session.js`、`dist/modes/rpc/rpc-mode.js` 与既有 bundle 入口；PBB `extensions/background-bash.ts`、`bin/pbb.js`；subagents `src/runs/foreground/execution.ts`、`src/runs/background/async-execution.ts`、`subagent-runner.ts`、`owned-process-tree.ts`、`process-terminal.ts`，以及已有 `src/api/background-work.ts`、`background/auto-drain.ts`、完成 result watcher。无需新写一套 subagent 调度器。尽量新增按现有 patch 完成后的源码生成的顺序增量，不重写 dirty patch；若必须编辑同一 patch，D 保留其完整现有内容并说明实际增量。

## 首批契约

### Provider 的执行所有权与静止

顶层 Pi 新执行具有独立 process group，记录 PID 的 birth identity 与执行代次；不向目前与 Braid 共享的历史 PGID 发组信号。Pi 原生接入负责登记自己启动的 detached runner/child/bash 的既有 owner 身份与终态，并将全部 owned groups 纳入该 provider execution 的停止闭环。已有作业 manifest、PBB instance/job 记录和 process terminal 是事实源；优先补缺字段，不能再创建竞争的全量账本。

原生静止结果须能区分：正在执行 turn；有限作业未结束；结果尚待入原生历史；服务仍在运行；已经静止；信息无法取得。Braid 只消费 `quiescent/busy/unknown` 与有界理由，不读取这些私有条目。建议在现有 `get_state` 的 managed runtime 信息中提供聚合结果，最终字段形式由 A/D 收敛；它不是通用工具协议。仅 `agent_settled` 不足以代替此结果，尤其要处理 `service:true`。

首批默认保留仍有 owned service 的 Pi 驻留，不改变现有服务寿命，也不误停仍被其它成员使用的共享 portless proxy。Agent 或压力处置明确停止自己拥有的服务并取得收据后，才进入 idle 卸载。若后续要让服务在 owner 卸载后继续存在，需要另行定义独立 service owner 与结果交接，不在此次最小实现中默默转移所有权。

停止流程先关闭原生输入，执行原生 shutdown/drain；父 wait 与原生 owned groups 的清理/核实分别保存。非零 wait 记录为异常执行结果，不能自动使停止证明失败，也不能覆盖真实清理失败。stdout EOF、未知 turn 的事实和同 native 身份恢复沿既有链路；成功停止后才撤旧 binding、恢复新句柄。timeout、权限拒绝、身份冲突、未知作业归属保留具体错误并阻断该恢复，禁止循环 OOM 重启。

SIGKILL 绕过 Pi shutdown，必须从该执行已持久化的原生 ownership 找回 detached 作业，而非只沿当前 PPid 枚举。任意 shell 内进一步 `setsid`、双 fork 或清除身份环境的进程不能仅靠已登记外层 PGID证明停止。D 必须在实现时核对实际工具运行/持久服务中可取得的 owner 标识；无法证明的范围明确返回 unknown，由 A 保持现有停机安全边界。此次不以“ps 暂时没看见”声称完整 stop。

### 逻辑成员与驻留进程

B 使用原 session 身份与当前 clone，新增的只是物理 residency 状态。未知执行接续与正常 idle 卸载必须区分：前者需要一次去重的恢复事实，后者不制造“上次结果未知”，也不重放旧输入。

卸载在检查原生静止后，必须在 store 同一事务核对 assignment/version、无活动 turn、无输入、无 reset，再 fence 旧 binding；并发新输入留队，由下次按需恢复消费。释放前后原生信息变化仍须通过关闭/停止收据确认，不能凭一次 readiness snapshot 直接删句柄。恢复需覆盖正常 wake、description reset、新 assignment、closed member 重新激活及 Unknown 接续，避免仅改 `start_next_agent_turn` 后其它入口仍无条件 spawn。

可优先沿用 provider session 的 idle 状态保存逻辑责任，在旁边记录物理 unloaded 状态或依赖明确的运行内句柄集合；不把 OPEN assignment 伪装成 closed sleeping。是否需要一个持久 residency 字段，由 B 核对重启查询能否仅靠 existing provider lifecycle 与 offline stop certificate正确推导后决定。若可推导则省字段；若不能，字段只用于防止无输入的卸载成员在重启时被全部拉起。

### 资源样本、准入与反馈

C 复用两秒 collector；补读 `memory.stat`、可读的 `memory.pressure`，保留 errno、cgroup identity、采样起止与 attempt 身份。`memory.current` 是内核计入该 cgroup 的内存用量；PID RSS 仅帮助定位，不相加作为余量。缓存相关字段只作解释与工作集估计，不能把 file charge 全部扣除当作肯定可回收内存。PSI/reclaim 与 charge 的变化帮助区分瞬时缓存和持续压力。

对消费者提供一个原子替换的最新快照，包含来源身份、时间、原始计数和简单 `normal/pressured/critical/unavailable` 状态。有滞回和连续样本确认；OOM increment/逼近 hard limit的实际危险不等待长确认。阈值及执行数量上限集中在本轮 policy，保持很少的可调项，随实际操作校准；不能依据末端 RSS 合计宣布某个精确容量安全。只读 cgroup 无法写 `memory.high`、新建子 cgroup 或强制回收，首批不依赖这些能力。

Braid 准入使用全 run 共享状态，既控制驻留 physical sessions 的新增，也控制活动执行的新增；计入启动中和恢复中的资源，不能只计已 running。普通待执行输入留 queue，恢复也受相同准入；已经接受的 turn/子作业不被回溯拒绝。压力持续上升时，原生工具层中止归属明确的作业，先保存原退出/信号/输出、资源原因与副作用可能性，再交给 Agent 决定缩小并发或继续；不把此事归为应用验收失败。

工具层要及时获得采样或准入事实，Braid/OOM控制不能只依赖 Agent 自愿遵守提示。但是 shell 内一个命令的 worker 数不能被外层槽位精确控制，首次工具结果和当轮上下文须明确当前预算与工具原生并行建议；实际 worker 数由工具参数控制，不解析命令并偷偷追加参数。

### 全 run 原子准入的最小候选，尚未冻结承载

候选一是复用 Braid CLI 与 SQLite 的 immediate transaction，仅提供 provider-neutral 的短期资源 reservation（claim/bind/release），由 Braid start 与原生工具调用共同使用。它记录 opaque owner execution、reservation、实际 OS birth identity和释放事实，不储存 PBB/subagent种类、业务状态、结果或工具命令。原生 owner 保留自己的私有作业记录与停止职责；Braid runtime 只消费聚合资源占用。该候选可避免新常驻服务，但增加跨进程调用、数据库写入和少量 CLI contract，应由 advisor 对照收益确认。

候选二是在原生接入复用既有作业 owner/instance 文件，增加很小的共享 admission helper，在同一 run 目录用既有 Python/OS 文件锁原子申请与释放；Braid 通过 provider 调用或通用 launcher参与。它避免 Braid store了解工具，但必须证明不会形成第二份 lifecycle事实源、spawn 时隙和不同语言锁规则，且仍要覆盖 Braid start/resume/reset；仅各自读取同一个资源 JSON 不具备原子准入。

最低持久字段的理由如下；如果既有原生材料已提供，复用，不复制。

| 信息 | 不能省略时的具体失败 |
| --- | --- |
| 同一 attempt/execution 代次和 opaque owner | 旧恢复来源的作业或计数会被误认为本轮资源；一个成员退出会清理另一个成员的执行。 |
| 唯一 reservation/job identity及既有 manifest位置 | 同一 spawned作业重复注册/释放，或者 owner死后无法找到其 detached作业。它不是新的业务任务ID。 |
| PID/birth identity和自有 PGID（确切可取得时） | PID重用误杀；共享PGID误杀 Braid；只保存PID无法发现父退出后仍活的组。 |
| 启动 intent或等价的既有 startup handoff | spawn完成但登记前owner被杀，出现不可归属的新writer。未登记的child不能开始应用写入；已有startup ack/proceed可复用。 |
| 已确认停止/未确认及原wait/cleanup证据位置 | 将leader close误认整组停止，释放配额并启动第二writer。临时失败不能永久吞掉slot，也不能靠超时删除活跃owner。 |

不新增角色优先级、工作流图、公平调度平台、每工具估算模型或完整持久job表。模型按 Braid session 的预算保护继续沿既有独立规则，不将本次进程预算写成新的模型权限限制。

## 父等子与后台工作不能制造准入死锁

原生子调用的 admission 必须是一次非等待决定。父正在执行/等子时占据的资源是真实内存，不能假装释放；如果子进程无法启动，立刻返回 `resource_deferred` 一类明确结果及压力事实，不创建永远 queued 的原生run，也不在 `agent_end` drain等待一个尚无slot的child。上层Agent可以缩小本次并行、直接完成或在父安全结束后重新发起；Braid自身输入则继续留队。

并行批次先按当前预算确定能启动的规模。已有工作必须按原有语义逐项保留收据；若原生API要求批次原子启动，整批明确拒绝，不能静默丢失未启动条目。对于已启动的async runner，其后 child Pi也要同预算接线：不能将runner登记为“启动成功”后无限等待真正writer名额。优先使用现有 startup handoff在实际child可启动时确认，或者失败终结runner并返回资源事实。嵌套child与PBB继承同一run政策和owner根，不能每个父都重新获得完整预算。

压力处理/取消不得在等待本作业terminal的同一锁内等待该terminal。admission锁只覆盖状态变更，立即释放；drain/TERM/KILL/wait及模型工具结果交付均在锁外。正常关闭的有限作业完成结果应先入native历史，再发 `agent_settled`；`service:true`虽不参加有限drain，仍计内存和停止证明。不得借关闭通知触发新的无预算后台结果turn。

## 实施顺序、冲突与反馈

1. 主线先冻结 A/D 的通用 stopped/quiescent契约，以及 C/D 资源快照和原子准入承载。这是内部工程复核，不是重新问用户开工。native owner先确认已有manifest/startup handoff能覆盖哪些脱组进程，未覆盖的明确升级；不得先改nonzero wait放行恢复。
2. C独立补采样与最新快照；D串行完善native spawn/close/drain/资源拒绝及owner收据；A完善Pi专属execution与聚合stop消费。采集器只读、2秒周期不变，不能引入新监督服务。
3. A停止闭环完成后，B接OPEN idle卸载和按需恢复；C接所有start/resume/reset/reactivation/turn的全run准入。拒绝start保留原任务与输入，不误变永久blocked；停止未知仍保留安全边界。
4. 集成者接 `variants/pi-braid-i13/run.py`、`scripts/runtime.py` 与相应打包/恢复入口，冻结policy、patch顺序、目标文件SHA、实际Linux Braid SHA及版本I13-2。既有恢复identity/过程证据继续保留，不替换旧attempt。本文准备轮不做此步、不启动任何run。
5. 编译及无模型实际操作通过后，主线按已批准I13实验/恢复范围热应用；模型/费用/来源不因源码准备自动变化。首次实际运行观察准入拒绝、资源降载、idle释放、native历史接续和应用继续进展；若最低工具并行仍无法完成则保留事实交回资源/执行方式决策，不能无限重启。

当前dirty冲突面：三份 `harness/npm/patches/pi-background-bash-1.0.5.patch`、`pi-coding-agent-0.85.1-braid-boundary.patch`、`pi-subagents-0.56.0-completion-boundary.patch` 与 `scripts/runtime.py` 已有未提交改变；它们包含结果drain、Pi bundle改走shipped module、长度截断结果等，不属于可丢弃的旧试验。D和集成者先保留基线diff/SHA，增量施工；`model-exclusion-boundary`、`open-tools`、`acceptance-off`后续patch也可能触同一上游文件，所有stamp必须记录完整装配后的文件。`harness/skills/agent-browser`、benchmark、lab ARC及其它task packet的dirty改动不由本任务接管。`sources/braid`当前无此任务前的dirty源码，但并行worker仍须按上述ownership互相协调。

反馈不增加Factory/Braid测试、模拟集成或改名探针。编译包括Braid `cargo check`、Python `py_compile`、已安装原生package的构建/类型或语法完整性检查及顺序patch装配回执。实际操作用隔离副本启动真实Pi RPC并读取get_state，不发送prompt；实际运行PBB有限命令与service并完成其真实shutdown、读取subagents既有终态原件、对自有进程作TERM/KILL并保存wait/组停止结果。只对隔离自有组操作，不碰暂停来源或共享PGID。

OPEN idle→卸载→原session恢复可先用既有native历史副本、真实RPC启动/关闭确认身份与文件保存；完整Braid wake/Unknown后模型接续、worker参数改变后的内存改善只能由后续授权实际实验取得证据，本准备轮不编造无模型端到端验收。资源与准入反馈保留memory原件、采样身份、拒绝原因、实际spawn/wait和未启动条目；RSS定位图不能充当容器容量证明。Console、远程Docker源码、隐藏评测器与push均不在本实施面。
