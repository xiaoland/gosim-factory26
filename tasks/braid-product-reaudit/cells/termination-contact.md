# 全范围结束与历史成员投递修复

本单元由主 Agent 委派，用户本轮已授权应用复审修复。所有权为 Braid `src/local.rs`、`src/store/mod.rs` 及其中针对性测试；不改 provider、session 或 group。保留既有未提交修改，不提交，不运行 Factory/devinfra 测试或 benchmark。

实际调用链确认：`drive` 在全对象终态检查之外还有 `RootIdle::Closed` 的 quiescent 返回；Store 派发采用独立 SQL 判据。统一由 Store 的全范围判据同时提供运行状态与派发判断，根关闭但仍有开放项/未决合并且静止时返回既有 blocked，保留状态。已开始 turn 与 reset continuation 继续自然结束。

历史 direct_contact 由 assignment_candidates 进入 begin_agent_assignment，blocked/retired 地址会重复尝试唯一名字。最小修复是在调度推进及物化事务边界复用确定性收尾：仅将指向终态成员的 pending direct_contact 置 blocked，并将对应 queued 回执置 unreachable，记录成员与生命周期原因；不改地址或创建新人。调度入口保证不依赖特定 profile 成功启动，物化入口阻止竞态。正常 sleeping 沿已有 reactivation 路径，显式改派保留新名字。

验证覆盖根关闭且开放未指派项返回 blocked、全范围关闭后的普通输入保留/重开可取、历史 blocked/retired 输入多次推进幂等且不新增 assignment、sleeping 身份不受影响。只执行 Braid 针对性 Rust 测试；历史保留快照可获得时在隔离副本验证，不改原始归档。

状态：计划完成，正在实施。

## 实施与验证

实现已完成。`Store::local_delivery_closed` 同时提供派发与 Local 退出判据；根关闭而全范围未收敛的静止状态返回 blocked。result 的 `retained_input` 汇总 queued 评论投递数量、范围是否关闭、SQLite 回执表和 comment view 定位命令；计数读取失败保留具体错误，不阻止结果落盘。全范围关闭仍等待既有执行和 reset continuation 完成。

`settle_unreachable_contacts` 在 scheduler 和 assignment 事务入口处理历史终态成员地址，消息事件 blocked、queued 回执 unreachable 并注明原地址/成员状态。真实 ZIP 中数据库仅复制到临时目录，通过当前 Rust `StoreActor::advance_scheduler` 连续推进两次：glm-3 的 27 条 pending direct_contact 全部成为 blocked，queued 回执从 25 降到 0；全部 12 条 assignment 的 ID、地址及状态逐项一致。原始归档未改写，前后查询保存于 [验证证据](termination-contact-evidence.json)。临时历史快照测试执行后移除，稳定的身份回归测试保留在 Braid。

主线追加委派了原生明确拒收的持久恢复：`defer_unstarted_turn(String)` 仅接受 starting 且没有 provider turn ID 的普通批次，旧 turn 标 interrupted 并保留原 batch。复用 `replay_event` 的 dedupe 因果链，queued 回执改指派生事件且保持 queued，原 session 回 idle；已有 open batch 统一进入一秒 quiet，避免每 worker tick 重试。主线选择了保留因果的已有重放机制，未采用清空旧 turn.batch_id 或搬迁原事件的方案。reset notice 沿已有接口。

已通过的 Braid 定向验证：

- `cargo test store::closure_tests -- --nocapture`：7 项通过，包含关闭自然收尾、关闭后真实输入、已接受 reset continuation、重开后消息恢复、blocked/retired 历史输入身份保持、明确未接受的重放及并发新输入、运行中 ordinary 非 urgent 批次与关闭/失效/旧地址/旧 revision 边界。
- `cargo test closed_root_with_open_unassigned_item_returns_blocked -- --nocapture`：完整 Local execute 返回 blocked，开放未指派项保留。
- `cargo test closed_scope_result_explains_retained_queued_comments -- --nocapture`：完整 Local execute 返回 quiescent，迟到评论仍 queued，result 数量为 1。
- 临时隔离真实保留快照 Rust 测试：1 项通过，前后值见 JSON。

未提交、未跑 Factory/devinfra 测试或 benchmark。现存 dead_code 编译警告未扩大处理。主线继续负责 Provider 端 native ACK/terminal 配对、mixed batch 收据以及权威文档整合，本单元的 Store 确定性结果不代替原生模型验收。
