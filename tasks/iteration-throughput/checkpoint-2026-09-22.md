# 开工后暂停盘点（2026-09-22 23:43 CST）

用户明确要求停下盘点。已中断process_terminal_fix；两个Braid资格进程均已失败退出，没有新的模型运行或Competition提交。原现场不删除、不回退。Braid源码干净，最后发现的僵尸终态误判尚未修改。

从实现前提交7d3b1e6的20:01到23:43约3小时42分。本轮0个完整benchmark评分，0次Competition上传；此前17:12记录的上轮成绩不属于本轮。

| 出口 | 实际状态 |
| --- | --- |
| 公开assignee、四variant、明确native role模型、SVC接线 | 实现提交32f1e3c；静态/行为检查通过，未证明完整bench |
| Competition自动化、冻结和恢复 | fake transport检查通过；真实首个POST尚未发生 |
| Linux离线提交包 | 5bee93dd候选389830022 bytes；工具、双浏览器与Landlock实际检查通过 |
| 模型与native能力 | 文本/视觉工具接口、真实vision/executor通过；浏览器修复后沿实际wrapper无模型验证，未重新采样整场 |
| Braid协作 | 两场均失败在首次foreground reset，未完成background reset、双Issue/PR交付 |
| 官方本地runner | prepare-only通过，所需官方镜像缺失，未跑本地正式评测 |

墙钟阶段粗分（不是CPU时间，也不是独占工时）：20:01–20:37主要实现约36分钟；20:37–21:28离线运行时/浏览器打包约51分钟；21:28–22:56原生资格、环境迁移、浏览器/proc/NSS排障约88分钟；22:56–23:43重新打包与Braid两场资格、procps和僵尸问题诊断约47分钟。依据git提交时间及scene check/process记录，不能把其中所有时间归因模型。

最后阻塞的因果链：foreground writer PID10718在reset后成为Z态，PPID1；Braid共享helper使用kill -0判定存活，故把已退出但未reap视为仍在运行，并在SIGKILL后报错。证据runs/qualification/live-linux/braid-procps/writer-terminal.json与foreground.jsonl绑定同PID。修复范围已分配但尚未实施；应区分执行终止与PID槽位释放，并对检测未知fail closed，background原有lease/processTerminal证明仍保留。

本轮效率问题：平台依赖与完整进程生命周期没有在最初实际Linux包上集中验证，缺陷被逐个串行发现；native场景为设施排障消耗模型采样，首场还出现恢复消息与停止指令交错；procps加入较早Docker层触发Chrome重下载；已有fake/空子树检查与真实有子进程的生命周期之间仍有空隙。后半程无模型浏览器/工具probe确实减少重采，但没有改变本轮尚未取得评分的结果。

恢复前应先与用户盘点，不自动推进。建议后续第一出口是一个无模型真实进程树reset回归（live/zombie/unknown），再恢复现有Braid场景；不新增泛化框架或扩展资格矩阵。

## 暂停后的架构判断（讨论稿，未授权新实施）

已核对design.md、verification.md、Braid teardown与参赛须知。判断：本轮把过多产品能力与部署机制放进一个串行成功条件，缺少最薄的真实官方纵向路径；Pi原生、pi-subagents、自有extension与Braid之间的完整会话树终止责任也仍分散。证据足以要求重审接缝，不足以断言应放弃Pi或Braid。

既有设计本来要求无模型的原生→扩展→Braid、同writer三层spike，但实际先得到空子树RPC与mock证明，完整有子进程的reset问题仍由付费协作场景揭示。这是未落实已识别的关键验证，不是再加一份规则能解决。

官方输入/输出、指定模型、运行部署与评分是端到端最小路径；Issue/PR、comment上下文、设计实施分离、multi-agent是用户的实验对象，应保留。detach子进程、跨层receipt/lease消费、自带Chrome系统库、自建Landlock ABI要求是实现选择，需要逐项证明必要性。参赛须知允许npm/pip/Cargo软件源下载，没有规定必须自带这些底层机制；实际runner隔离与可用工具仍需事实确认，不能未经验证删除保护。

建议讨论的方向：先在一份候选上闭合官方完整链，再展开既定矩阵；Braid依赖provider对完整session tree的生命周期合同，详细进程/lease协议收敛在一个适配边界；原生子代理无需在父会话销毁后存活，不应为不需要的独立生命周期支付管理成本。具体Pi接口与可实现边界需小spike验证，尚不能把某一种OS隔离方案当已选技术方案。

## 用户纠正：生命周期边界与验证成本

Braid不管理Pi内部sub-agent生命周期。Pi/pi-subagents的僵尸、清理或停止缺陷应在所属组件处理；不得为此在Braid消费原生child process/lease证明或增加兜底。上一节将共享进程终态补丁和三层无模型spike作为恢复前提的建议撤回；process_terminal_fix仍中断，未修改Braid源码。

模型额度几乎无限，墙钟时间稀缺。验证按“取得足够证据所需时间”选择，不把无模型当优先目标。已有低成本确定性检查可保留；不为替代短真实运行而新造复杂模拟系统。后续讨论优先直接复用Linux开发环境运行实际Pi能力，只对已观察故障做最短定向复现，到可交付检查点再打包冻结。上述为方案修正记录，不表示源码实施恢复。

## 用户纠正：删除自建沙箱

用户明确所有自建沙箱均不需要，包括开发机；撤回“本地必须保留保护”的建议。删除面包含Factory的macOS sandbox-exec/Linux bwrap、提交包Landlock及关联preflight/资格要求。不新增替代沙箱，不以配置开关保留。具体方案归cells/pi-boundary.md。
