# I11-03 / I11-05：重建上下文时保持协作与执行连续

状态：2026-09-29用户明确同意03/05存在及方案，并授权应用。03交readable-cli实施；05交GitHub审查负责人定向核实并修复原生层。依据 GitHub 全过程报告及固定部署源码，不把 agent_settled 当作缺失能力。

## 目标与边界

修改正文仍完整重建上下文，包括自行编辑；清理当前工作记忆不应关闭协作收件箱，也不应让一个有限后台检查的结果消失。
Braid 管工作项、消息和 provider 会话交接；Pi 及其扩展管原生后台作业与 sub-agents。
不新增 Braid 作业调度器，不把服务永不退出理解为会话永不完成，不默认强制打断长检查。

## I11-03：重建等待不封锁普通消息

已证：worker 在 active.reset_id 存在时不 forward_running_input；store 又在 pending invalidate 存在时禁止 claim_running_input。
PR16 的基线更新评论因此等待约43分钟，到旧基线报验后才读取。这是门禁导致的排队，不是评论随机丢失。

建议：旧会话仍可接收输入期间，重建通知与普通评论共用既有原生输入通道，普通评论不因“将要重建”而停送。
只有进入实际关闭旧会话的交接点才停止向旧会话发送；此后新消息保留给新会话。
投递对象仍核对当前assignment；取消息时按当前hide/delete/resolve可见性渲染，不把已删除正文通过历史事件再次注入。
新快照标明已包含范围；不得因为文本在快照里出现就声称收件人已经阅读或执行。

实施应同时核 worker 与 store 两个门禁、批次ack/失败重放和重建快照覆盖，不能只删一个if。
接受到原生输入的评论保留送达记录，未接受的消息保持待处理；重建与send串行交接，禁止旧会话退出后把未发成功的评论标已消费。
语义动作与工作优先级仍由Agent决定，Harness不识别“紧急基线更新”等业务事件。

## I11-05：后台执行由原生层提供可交接结果

已证：同一候选多次开始检查；reset后旧job没有可读取的终态，新实例当前scope jobs=0被误当作原任务不存在。
旧会话close会走Pi dispose和PBB abortAllJobs；但未捕获每个旧job的signal/exit，不能声称每次都是Braid杀掉。
已存在 agent_settled、finite-job等待与background-work注册，因此再加一份等待机制不是方案。

建议先修正已有原生完成/关闭契约：有限后台工作结束且结果进入原生消息或持久结果记录后，才报告可正常关闭；常驻service不阻塞，但关闭时应记录停止事实。
检查PBB的ownerSessionId、registerBackgroundWorkProvider、RPC模式ctx.hasUI及agent_end/settled顺序，找到已有等待路径实际失效的一环后修复该环。
现有证据不足以在这些候选中任选一个作最终根因；该定向核实属于本方案实施准备，不重做整次run审查。

确定可修部分：正常取消/关闭必须等待已有作业收尾并保存cancelled/exit/输出路径，不能先清空回包队列再丢弃结果；非正常退出只记unknown，不伪造取消成功。
结果读取复用现有全局job标识和持久元数据，不要求新Pi实例继承旧内存作业对象；当前实例列表为空只表示本实例没有作业。
Braid只消费原生层的可关闭/未完成状态，不枚举或结束Pi内部sub-agent，不接管后台进程PID。

## 顺序与判别

普通消息可达 → 旧会话处理重建通知与当前工作 → 原生层有限工作及结果可交接 → 关闭旧会话 → 当前快照建立新会话。
等待期间仍接收协作消息；明确停止或provider故障另走已有中断路径，保留实际未完成结果。
真实运行验收观察：长检查期间正文更新及新评论同时到达，评论不等整轮检查结束才送达；同一作业结果可消费，正常重建不因current-scope=0重新启动相同检查。
不引入模拟测试或探针；不把一次编译通过当成时序行为成立。

## I11-03 实施记录

`group/worker.rs` 在 active reset 等待期间继续调用既有 `forward_running_input`；`store/mod.rs::claim_running_input` 不再因 pending invalidate 拒绝普通输入，但仍要求原 turn 与 provider session 运行中、当前 assignment/member/profile 一致。claim 只选普通待投递事件，Invalidate 留给 reset 链，不把失效事件伪装成普通评论。`group/dispatch.rs` 同一个 worker 先发重建通知再发普通输入，旧 turn terminal 及 teardown 路径仍由它串行执行；进入 `reset_pending` 后不再满足 running claim。

旧批次可以在原生 steer 等待应答时收到新事件。claim 现在记下实际渲染进输入的事件 ID；原生返回 `Acknowledged` 后，store 仅将这些 ID 标为 consumed、相应评论回执标为 delivered。新追加事件留在 runnable batch，下一轮只渲染仍 pending 的引用。未接受输入时不调用确认，原批次继续可投递。确认事务核原 turn 与批次归属，不因新事件混批而误报已送达。引用只含 comment ID，正文由当前 CLI 对象投影按 hide/delete/resolve 可见性读取；回执不声称 Agent 已阅读或执行。

本次未修改普通评论的业务语义、通知收件规则、PBB 进程/作业生命周期，也未让 Braid 枚举原生子代理。`cargo check -q` 通过，只有既有 dead-code warnings；未运行测试、模拟探针、部署或 I10 运行。静态核对只能证明代码和状态约束一致，长 turn 中评论能否及时被原生 provider 实际处理，仍须新 variant 真实运行观察。若原生 steer 已接受而 SQLite 确认失败，现有协议仍可能重投同一引用；这属于原生接受与本地事务不能原子提交的边界，需以实际故障证据再决定是否增加去重机制。
