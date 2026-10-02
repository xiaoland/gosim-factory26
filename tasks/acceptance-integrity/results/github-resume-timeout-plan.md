# GitHub 已有会话恢复超时：待讨论方案

目标是接续已付费产生的代码与会话，完成集成、验收和官网应用重放。
用户已批准超时分类、定向状态修复和接续，也批准追加原生路径修复。旧 GitHub 容器已归档并结束；原数据库中的 #1/#4 已按审计事务恢复一次。V5 接续暴露 Pi 配置目录错误，V6 接续暴露 Pi 会话路径仍被重新拼接；两次均未让 #1/#4 开始模型工作。V6 中 #5 正在继续原工作，须等其结束后再切换二进制和恢复 #1/#4。详见末节。

## 确定事实与因果边界

运行源码以 `runs/e20260927-01-handoff/build/src/` 为准，不用正在开发的源码冒充冻结版本。

| 位置 | 实际行为 |
| --- | --- |
| `provider/mod.rs:24`、`provider/pi.rs:241` | Pi RPC 共用 30 秒响应期限。 |
| `provider/pi.rs:311–330` | 恢复时已有原生 session 路径；启动 Pi 后通过 `get_state` 读取身份。 |
| `provider/pi.rs:93–99` | 共用身份读取函数把请求失败统一包装成 `CreatedWithoutIdentity`，包含 timeout。 |
| `provider/session.rs:303–310` | 原始 timeout 本可成为 `Unavailable`，包装后却成为 `Materialization`。 |
| `group/issue_agent.rs:185–193` | Materialization 进入 `block_provider_session`，Unavailable 不走这个分支。 |
| `store/mod.rs:3244–3284` | provider、agent、assignment 都被标为 blocked，assignment 写入 retired_at。 |
| `store/mod.rs:3168–3200` | 恢复候选只包含 idle/running/unknown 会话和 active/finalizing assignment，因此这两项不能靠普通重启恢复。 |
| `group/worker.rs:324–349` | 周期恢复约每两秒发生；仅改成 Unavailable 仍可能反复启动，不能作为完整修复。 |

10:01:25/28 的原日志显示根 Issue #1 与 Issue #4 在恢复会话时出现 `physical session materialization failed: provider request pi_rpc timed out`。
以上调用链可将失败定位到已有会话恢复的身份读取，不是模型推理请求超时。
同期机械硬盘高 I/O 等待有实测证据，但缺少 Pi 启动完成/对应 RPC 响应时间，尚不能证明它就是该 30 秒超时的唯一原因。
当前没有晚到响应的可靠证据，不声称 Pi 已经成功恢复却被 Braid 丢弃。

| 工作项与负责人 | 当前持久状态 | 责任退休时间（UTC） |
| --- | --- | --- |
| 根 #1，@glm-1 | assignment、agent、provider 全部 blocked | 02:01:26.657455414 |
| #4，@deepseek-5 | assignment、agent、provider 全部 blocked | 02:01:23.744461459 |
| #5，@glm-6 | assignment active、provider running；容器已冻结 | 无 |

精确内部 ID、原生文件路径和错误保存在 [状态取证](../../../runs/e20260927-01-handoff/network/github-persisted-state.json)，不放入 Agent 提示词。
WSL `runs/e20260927-01-handoff/github-rpc-timeout/workspace-paused.tar.gz` 为暂停后完整代码、Git、DB、原生会话归档，25,112,317 字节，排除可恢复依赖缓存。
暂停动作见 [操作记录](../../../runs/e20260927-01-handoff/network/github-pause.json)。

## 建议的最小修复

已知会话恢复的连接、超时错误保留暂时不可用语义；新建会话成功后确实无法取得身份，继续单独处理。
响应结构损坏或身份不匹配不能伪装为暂时超时。
恢复失败不撤销工作项责任关系，也不新建另一个负责人或重新实现应用。

为防止两秒周期反复启动，在本次进程内记录每个失败的恢复尝试，报告为“待显式接续”的执行阻塞；同一进程不自动再启动它。
其它已活动会话可继续，整次执行结束时明确指出哪些工作项尚待恢复。
操作员明确重新启动一次接续，才允许新的尝试；不用无限重试、数据库轮询或延长所有 RPC 的全局期限来掩盖问题。
这是拟议行为，实施准备需要核对该记录应放在既有 session manager 还是 worker 的恢复状态中，避免重复状态源。

## 两条旧错误状态如何恢复

现有 `issue assign` 接受配置别名；再次指定相同 profile 是 no-op（`objects.rs:303–305`）。
`unassign` 后重新指派会产生新负责人、新 assignment，而不是恢复原生会话，因此不推荐把它当作本次修复。
当前没有查到现成的保留原身份 unblock CLI。

建议在批准后执行一次受审查的修复事务，只修正这两个已证实被误分类的当前状态投影。
事务先核对具体工作项、原 assignee/profile/revision、原生 session 文件、错误字符串和三层 blocked 状态完全匹配；无匹配即停止。
恢复原责任关系和可恢复的会话状态，原 Git 分支、工作树、会话文件、已完成 turn、历史评论和事件保持原样。
原错误、retired_at 和前后值完整保存到新增操作记录；另通过现有 CLI 写一条明确的恢复说明，不伪造旧通知或把失败 turn 改为成功。
这里需要用户确认是否接受这项有审计记录的当前状态修复；未经确认不执行 SQL。

## 最小验证与解冻顺序

协调复核补充了一项必要的缺陷分支回归，待开工后执行：在已有 Pi RPC 边界仅令恢复既有 session 的 `get_state` 返回 Timeout（优先现有可注入边界；否则用单次响应延迟，不模拟整个 Pi）。
使用隔离的原状态副本，验证错误归类为 Unavailable、原 assignment/provider 未被 blocked 或 retired、原 assignee/session 身份保留；跨过两个既有恢复周期后，启动/请求计数没有增加，证明同进程没有两秒循环。
这项回归只覆盖本次真实缺陷，不扩展 Factory 测试体系；真实 Pi 的成功调用不能替代它。

1. 保持暂停及归档；批准后先在暂停现场的副本中，用真实 Pi、原模型配置和原会话文件执行一次 `get_state`，记录启动到响应的时间，不发任务 prompt、不产生实现工作。
2. 若仍超过期限或不可用，保留 RPC 阶段和 I/O 证据并停下，不启动付费恢复循环；由证据决定是否需要独立的启动等待期限或降低恢复时的 I/O 竞争。
3. 仅在用户认可具体实现与状态修复后构建新恢复二进制；暂停中的旧进程不换二进制。
4. 对 GitHub 旧 Braid 进程安排正常退出再解冻以完成收尾，不恢复它的自动调度来碰运气；保留 #5 已写的文件、原生记录以及中断工具信息，不强迫新增 WIP commit。
5. 在停止后的完整副本上执行获批状态修复，新增一次接续记录；沿原 #1/#4/#5 身份与工作区启动，不重新拆题或重写已完成模块。
6. 验证根与 #4 收到输入并实际工作，#5 接续已有文件；暂时失败时不退休 assignment、不两秒循环。最终仍以完整交付及官网 self_funded 应用重放评分验收，不以 get_state 成功、局部测试或 quiescent 代替。

不增加大规模 Factory 测试套件或模拟时序系统。
缺陷分支回归、真实 Pi 成功路径、完整应用交付与评分分别记录，三者不能互相替代。

## 实施中发现：传给 Pi 的路径并非原生文件

冻结 DB 的 `provider_session_id` 为 native-home 根下的 JSONL 路径，实际原生文件却在该 home 的 `sessions/<项目目录>/` 下。
`PiSessions::resume_home` 已按文件名在子目录找到文件并返回其父目录，但 `PiProvider::resume_session` 继续把旧 DB 路径作为 `--session` 参数。
在只读原件的隔离副本里，用旧路径启动 Pi 时 `get_state` 虽成功且回显旧路径，`sessionId` 与保存的 JSONL 头部 ID 不同；改用真实文件路径后两条会话的 ID 均与原文件一致。
因此此前“get_state 成功”只证明了 RPC 可用，不能证明原上下文恢复。未据此更改真实 DB、原生文件或用户应用。

获批的局部修复：用定位到的唯一原生文件作为 Pi 的 `--session` 实参；仍以旧 DB ID 作为 Braid 内部稳定会话键与通知键。核对 `get_state.sessionFile` 为实际文件路径，避免把新空会话认作恢复；若 basename 匹配多份文件则报错。
这需要同时核对 `PiProvider::start_turn` 设置的通知 thread ID，防止物理路径变化后丢失 TurnStarted/TurnCompleted。恢复后记录真实 native 文件路径供诊断，但不改历史 DB 会话 ID，不把路径或内部 ID 传给 Agent。
先在隔离副本验证两条原生会话 ID 与消息历史，再重复单次超时分支检查；通过后才运行已经准备的定向 DB 修复与新接续记录。

受控超时检查结果：隔离副本运行 48 秒，三条原生会话各启动一次；#1/#4 的 `get_state` 各超时一次，此后九次 `session recovery unavailable` 报告没有再次启动 Pi；两条 assignment 保持 active，agent/provider 保持 idle，retired_at 为空。该检查未发模型请求。当前 Braid `cargo test --no-run` 被仓库已有的测试代码接口漂移阻断（33 个编译错误）；本轮没有扩建测试体系。

## 接续实况与下一步

V5 先修复 `--session` 物理路径，却把 `PI_CODING_AGENT_DIR` 指向 `sessions/<workspace>`，Pi 报 `Unknown provider "factory26"`。V5 在读取原会话前失败；#1/#4 保持 active/idle，没有再次错误退休。
V6 将配置目录改回 native-home 根，但 `PiProvider::resume_session` 仍按配置目录拼接文件名，导致 `Pi native session file is missing`，#1/#4 被当成永久失败再次 blocked。#5 同时成功启动，正在编写 REQ-4 的可重复检查；其原生 JSONL 持续增长，不能在执行中覆盖二进制或修改运行数据库。
最终局部实现把实际文件路径作为 `PiProvider` 独立的 `resume_path` 传入，配置目录继续指向 native-home 根；Mac `cargo check` 已通过，WSL Linux release 已构建。待 #5 当前执行结束，保存 V6 现场，核对 #1/#4 的精确错误与身份，用 `repair-github-state-v7.py` 作一次可审计的定向恢复，再从同一工作区启动 V7。首先验证 `get_state` 的原生 ID 对应旧 JSONL 且有后续消息；随后继续整合与最终评分。
V6 正常工作期间不再由主 Agent 高频查看。WSL 上只读脚本每三分钟查看 V6 `run.json`，终态输出才唤醒主 Agent；脚本不做数据库修复、二进制替换或新 run 启动。
