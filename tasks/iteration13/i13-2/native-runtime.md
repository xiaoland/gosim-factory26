# I13-2 原生执行接口与停止范围

2026-10-01。原生实现是 `harness/npm/native-managed.mjs` 与三份 `*-i13-2-managed.patch`。增量补丁必须在完整既有 Pi、PBB、subagents patch 之后应用；既有三份 dirty patch 未被重写。装配目标与 SHA 原件保存于 `runs/iteration13/i13-2-20261001/native-runtime/assembly.json`，语法及顺序装配反馈归 `syntax-and-assembly.json`。

Pi RPC 的 `get_state.data.managed_state` 返回 `status: quiescent|busy|unknown`、有界 `reason` 和 `execution_id`。原生 turn、待投递消息、仍在运行的自有进程、PBB service、尚未消费的 PBB/subagent 结果都会阻止 quiescent。Braid 使用这个字段决定物理卸载；service 存活仍允许 Agent 接收普通输入并决定是否停止服务，不能把 managed busy 当成普通输入的统一拒绝条件。

`stop_owned_execution` RPC 返回 `status: stopped|unknown`、`reason`、`receipt_path` 和成功时的 `coverage`。活 Pi 调用先以共享 helper 的 `fence` 封住该执行的新 spawn，再清理子作业，并跳过自己的父进程。Braid 关闭 stdin、取得父 wait 后，必须再次调用离线入口验证父进程及 detached 作业。父 wait 的非零结果、EOF 与作业树停止是不同事实。离线入口为：

```sh
node "$FACTORY_NATIVE_RUNTIME_MODULE" cleanup \
  --execution-dir "$FACTORY_NATIVE_EXECUTION_DIR" \
  --execution-id "$FACTORY_NATIVE_EXECUTION_ID"
```

离线入口也需要 `FACTORY_RESOURCE_HELPER`、`FACTORY_RESOURCE_PYTHON` 和 `FACTORY_RESOURCE_DIR`，以同一 flock 写 fence。Fence 与准入登记在同一短锁内完成；TERM、KILL、等待及验证不持有准入锁。每次物理恢复使用新的 execution UUID 和目录，旧 fence 及原件保留。嵌套 RPC Pi 没有独立子树 fence 时返回 unknown；整个 execution 的控制归顶层 provider。

停止回执的准确范围是 `registered-process-groups-and-inherited-execution-markers`。Helper 在 payload exec 之前登记不可变 birth identity、独立 PGID、parent_start_id 和 execution identity。原生清理核对 Linux boot_id 与 `/proc/<pid>/stat` 的 starttime，登记 leader 仍匹配时覆盖同一组的成员；脱组后代须保留 execution/start marker，或由后续原生入口继续登记。只提取 ownership marker，回执不输出完整环境或凭据。

这个范围覆盖普通进程组，以及保持 marker 的 setsid/doublefork 后代。任意 shell 主动清除身份环境并脱组，历史归属无法仅由当前 `/proc` 恢复；本实现不声称对这种行为有无条件的全 writer 证明。2026-10-01 主线明确接受这项 managed ownership 边界，不将普通 bash 全部判 unknown，也不增加新的监督器。已检测到的 PID 冲突、不能核实的存活组、信号失败、枚举失败及身份缺失仍返回 unknown；旧暂停现场的旧机制缺口由整来源容器停止事实补足，不能用新原生回执替代旧现场证据。

`relieve_pressure` RPC 不调用模型，只选择一个确切自有的有限作业，并沿 parent_start_id 纳入其原生子作业。包含自有 service 的子树不会被这个默认压力动作选中。压力原因和“部分副作用可能存在”写入 execution 的 `pressure/<start-id>.json`；原始 exit/signal 和停止结果分别写入 `terminals/<start-id>.json`，既有 PBB/subagents 输出与 manifest 继续保留。没有可选有限作业时返回 deferred，归属或停止不能确认时返回 unknown。服务原有 shutdown 寿命不变。

所有 PBB bash、Pi 内建 shell、foreground child Pi、async runner 与其 detached child Pi 都调用统一 helper launch。Helper 自身 exec 成 payload，所以没有登记前执行应用写入的时隙。原生调用同步读取 `starts/<start-id>.json`，resource_deferred 立即返回工具错误，不等父进程占用的资源；它也中止既有自动启动重试及模型 fallback。Async runner 只有在真实 child 获准物理启动后才报告成功；拒绝或准备失败会返回明确失败并保留 status。已经 proceed 后的超时不伪称 startupDidNotProceed，也不把仅 runner 组停止当成所有 detached child 已停止。

同一个模块同时是 Pi extension。它在 `before_agent_start` 读取共享 helper status，将实际 memory charge、headroom、pressure 或 unavailable 原因追加到本轮 systemPrompt，并建议工具原生 worker 从 1 开始、根据余量提高或分步完成。它不解析或改写 shell 参数，不改工具权限，也不内联技能正文。工具本身仍受 helper 准入与原生压力控制。

Mac 已通过真实 Pi RPC get_state/relieve_pressure 操作，没有发送 prompt。真实 Pi SDK 加载 PBB 后执行有限 printf、持久 service，再调用其原生 session_shutdown；加载错误为空，既有 jobs/events/logs/session 原件位于 `native-runtime/operations/`。Mac 没有 Linux `/proc`，停止证明返回 unknown 是预期行为，不能代替 Linux 验收。

Linux 实际操作使用主线建立的 `factory26-i13-2-native-operations` 容器，内存上限 4GiB、2CPU、network none；容器身份保存于 `native-runtime/linux-container.json`。装配 runtime 为 `/runtime`，实际 helper 为 `/ops/runtime_resources.py`。`operations/operate-linux.py` 复用真实 ResourceEvidence，并通过 helper launch 运行安装后的 Pi RPC 与真实 Pi SDK/PBB 工具，没有发送 prompt，也没有人为制造 OOM。原件已复制到 `native-runtime/linux-operations/`。

PBB 的 bg001 正常退出 0；bg003 保留 partial log 后被 relieve_pressure 以 SIGTERM 停止，原始 exitCode 为 null。bg002 service 在压力动作后继续存活，使 managed_state 保持 busy；随后原生 session_shutdown 才终止该服务。RPC 的状态依次是 quiescent、有限 shell 运行时 busy、relieved、结果进入原生 history 后 quiescent。stop_owned_execution 写 fence 后，新的 bash 明确返回 resource_deferred: execution_stopping，原始 receipt 与错误保留，payload 没有输出。RPC 关闭 stdin 后离线 cleanup 返回 stopped。实际压力采样全程 normal，memory.events 的 oom/oom_kill 均为 0；这些操作验证控制行为，不声称已经复现资源压力阈值。

`operations/operate-proxy-and-sigkill.py` 另行复用了主线的 start_shared_proxy/stop_shared_proxy。真实 foreground proxy PID118 不带 execution/start 身份；有限工具清理及另一个 Pi SIGKILL 后的离线清理都保留这个代理，HEAD 返回 404 和 X-Portless:1。其 run owner 最后 TERM/wait 为 0，代理 PID 不存在。第二个 Pi 的原始 root wait 为 -9，wait 后 `/proc` 仍直接观察到子 PID161、相同 starttime 1216108、state S；离线 cleanup 返回 stopped 后该子为 Z、RSS 0，不能再写。原始退出码、partial 输出和停止事实分别保存在 `linux-operations/proxy-and-sigkill/operation.json`、RPC JSONL、原生 session 及 execution receipt 中。父 wait 与 writer 停止的区别由独立 `/proc` 观察支持。

Foreground subagents 与 async runner→detached child 的接线已通过顺序补丁装配和语法编译；本轮没有允许它们发送模型 prompt，因此没有以启动真实模型的方式验收这两个流程。其准入拒绝、child-startup 回执及停止边界仍按上述接口保留，后续已授权恢复会取得真实生成反馈。
