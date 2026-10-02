# FF1 observer 增量独立复核

结论：本次增量**无新增阻断项**。FF1所指的确定因果链已在源码上消除：正常startup父A的空清单不再阻止同home的new_session父B初始化；同父恢复仍保留自己的子任务索引。此结论是静态边界复核，不是Pi行为验收，也不升级旧任务结果实际送达/父消费的证据。

本轮仅复核两个活动variant的 `extensions/factory-subagent-observer.ts` 及其对应Pi生命周期，未重审44项目录。两文件逐字一致，读取时SHA-256均为 `c0168d377385d1366980e6cee95d72cf05435a5c804f739a27728ec7a2242afb`。主线报告的esbuild转换通过属于已有反馈，本轮未执行转换、测试、探针、应用或实验；仅写本文，未提交。

## 身份、归属与覆盖

| 路径 | 当前机制与静态判断 |
|---|---|
| 新home startup A → RPC new_session B | A的有效空清单在父ID变化时被放下，不存空历史；B不存在自己的历史则从空集合开始。原先父ID不等即抛错的分支已消失，FF1发生条件被直接消除。 |
| 同父A恢复/再次session_start | 活动清单父ID仍是A，按现有merge加载已有条目，首次observe不会清空。 |
| A有子任务 → 同home切到B | 在覆盖活动清单之前，先把A清单按A的编码ID保存；B只从自己的历史读取，不把A的children合并成B的子任务。旧条目的父ID、产物路径、cwd和时间戳原样保留。 |
| B → 恢复A → 再切走A | 先保存B，再加载A历史。A的新事件合并到活动清单；下次切走时该较新清单覆盖A自己的旧历史，保留同一父的连续观察。没有跨父覆盖。 |
| 活动清单与历史同时含同父 | previousRuns先按父ID选一个较新清单，再展开run，避免将同一父当前与历史两个版本重复展开。同时间戳时活动清单先进入并保留；正常写入顺序下它不比存档缺子项。 |
| 同home旧父的handoff | previousRuns不再跳过当前home；仍按cwd过滤，并按当前父ID排除自己。旧父是handoff来源，不变成新父的所有权。 |
| 数据损坏 | schema/children结构仍校验；有children却无父身份及载入错误父历史仍报错。没有用吞异常或将未知旧任务自动当失败来换取启动成功。 |

存档在活动清单覆写之前完成。若在这两步之间中断，原活动清单和归档可同时存在，但读取会按父选一个版本；不是先删后存造成归属丢失。父ID经过encodeURIComponent，正常Pi UUID映射稳定。以上以当前单个原生父进程按Pi会话替换顺序使用其home为边界；本轮没有依据要求同一home被多个无关进程并发写的新增协调机制。

## 与真实Pi生命周期的对应

本轮重新读取本机锁定Pi 0.85.1的 `dist/core/agent-session-runtime.js:98–173`：替换前先abort当前回应、发session_shutdown并dispose，随后用原agentDir创建新runtime；newSession创建新的SessionManager，switchSession打开指定SessionManager。替换后重新bind；RPC自身还可能再次bind同一个新session。新增实现既允许不同父切换，也允许同父重复session_start，所以不依赖“每个home只能有一个父ID”或“session_start只发生一次”的旧假设。

原FF1涉及的Braid `spawn → new_session` 协议无需再假设不存在；本次修复已直接兼容它。同身份resume、切到旧身份以及reload重复初始化均沿相同身份分支处理。关闭时watcher释放、活跃期间转送的原边界未变，本次没有adopt、重新绑定旧任务或为历史任务保活。

未发现本次正常切换/恢复链会把历史错挂、静默覆盖其它父索引，或因活动/历史双副本重复展开同一父。既有多子项合并语义没有在本次扩大为一次新的通用重写，也不以本轮审查声称所有可能原生事件负载均已验证。

## 交付限制

可以将FF1标为“源码因果已修、增量独立静态复核无新增阻断”。真实生成中的startup/new、自然resume、历史入口展示和结果消费仍须按既有授权观察；没有自然恢复时保留未触发。此前PBB取消/settled和正式Node20观察条件保持不变，本次不重新开展其审查或新增验收流程。
