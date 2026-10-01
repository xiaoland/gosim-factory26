# I13-2 Braid 生命周期实施

2026-10-01。范围来自主线授权的 A+B，以及资源启动与压力反馈的消费边界。未操作两项暂停来源、未发送模型输入、未部署 Console，未 commit/push。

Pi 每次物理启动使用 UUID execution/start identity 和独立 PGID。启动通过共享 Python launcher 登记后 exec；顶层清除继承的 `FACTORY_NATIVE_START_ID`，避免错误归入旧父代次。`FACTORY_NATIVE_EXECUTION_DIR` 位于 native home 的 `managed-executions/<UUID>`，身份和路径随该句柄保留。资源拒绝读取共享目录 `starts/<start-id>.json` 的明确收据，保留真实错误内容，不按退出码猜测。

停止分开保存父 wait 与原生 stopped 收据。先使用 `stop_owned_execution` RPC，再 stdin EOF 与父 wait；即使父 wait 为非零或具体错误，仍调用 `node $FACTORY_NATIVE_RUNTIME_MODULE cleanup --execution-dir DIR --execution-id UUID`，由原生 ownership 核实包括 detached 工作在内的停止。收据不为 stopped 时不释放 writer；初始化和恢复失败也走这一边界。现有共享 PGID 不进入信号目标。

OPEN idle 卸载要求当前原生 identity 对应 quiescent，并在 Store immediate transaction 内核对 assignment/member/version、无 turn、输入、reset，再清除 binding。释放后保留同 provider/native/session/clone 身份，不新建 Unknown。既有候选查询同时服务有效句柄保留和恢复决定，新增 `needs_resume` 只为真实输入、必要 reset 或 Unknown 恢复进程；没有输入的 idle 不再周期复活。首批没有新增持久 residency 字段。

新 assignment 的资源拒绝保留同一 materializing assignment、member、clone 和激活事件；再次物化重用该代次。sleeping activation 返回待投递，Context reset 保持 materializing。普通 turn 只读压力；未接受输入沿现有 deferred receipts 留队。共享 factory 在既有两秒循环内按 sample 至多串行降载一次，再读取压力；无独立 scheduler。连续 Unknown 每成员自动恢复一次，真正 completed 或未见过的真实工作事件才重置；系统评论、恢复通知和自身 replay 不计入。全部待真实输入 ID 一并记录，避免旧 pending 事件从队列头部回落时被误认为新授权。

`ProviderHealthUpdate.can_progress` 由 driver 的实际 running、原生 streaming、可接续候选、待物化/reset/lifecycle 义务提供；local 等所有 group 已观察且全都不能推进、存在错误时才返回可恢复 blocked。同 group 的另一健康成员不会因一个 Unknown 门控被立即停掉。服务只驻留、没有原生 streaming 或真实待输入时，不被计为进展。

上述局部化适用于资源 Deferred、恢复限次和已取得完整停止回执的异常 wait。真正 stop-proof 为 unknown 时，仍保留原有 `fatal_stops` 的全局 blocked 边界及 factory ownership；本轮没有建立任意未证明停止 writer 的独立权限撤销或执行隔离，不能声称其它成员可在这一安全缺口下继续运行。主线已明确保留此边界。

代码面为 provider Pi/factory 与内部 session 接口、SessionManager、worker、dispatch、Issue/PR 的 deferred 分支、Store lifecycle 函数、RecordingFactory 转发和 local health 归并。未修改其他 worker 所拥有的 objects/comment/context/prompt 投影及 npm/Python 制品。

反馈原件位于 `runs/iteration13/i13-2-20261001/braid-cargo-check.log` 和 `braid-operation/store-readonly-operation.json`。Sheet 保全 SQLite 另复制到 `braid-operation/sheet-readonly-copy.sqlite3` 并以只读连接运行实际候选查询：Issue 1 的普通 idle 无待输入，`needs_resume=0`；PR 3 仍为 running，`needs_resume=1`。同时对本次 lifecycle SQL 执行 SQLite EXPLAIN，未修改原保全副本或副本业务记录。

cargo check 已通过；完整 Linux 编译、原生装配后的实际 get_state/TERM/KILL/cleanup 由主线集成与 native owner 提供独立原件。完整 Braid idle→新联系→同 native resume、Unknown 恢复事实消费、资源拒绝后的应用进展仍须通过后续获授权的实际实验确认，不以只读 SQL 或编译充当端到端验收。不增加 Factory/Braid 测试、mock 或改名探针。
