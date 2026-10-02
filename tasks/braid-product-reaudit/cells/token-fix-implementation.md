# Token 根因修复实施

2026-09-28：用户通过协调任务明确授权直接推进 token-deep-03 方案实现与必要验证，其他调查继续。无需再次索要本范围实施许可。当前比赛/本地运行仍用冻结材料，部署新热修复时给出具体清单。

主 Agent 独立复核了 Pi start_turn/inject_context/resume 和 ProviderSession 调用路径。修正是成功收到 prompt receipt 后清空待注入 Context；任何此前错误与 Deferred 路径保留，native history 不删除。已写源码与协议说明，正在运行有界 Braid 协议测试（首次busy、prompt拒绝、接受后只发增量、重新inject）。未修改 Factory/设施/Corpus，未新开实验。

6-Sol lite_keep_analysis：先完成耗时证据报告，现持有 dispatch/store 的终态 direct_contact 批量和可行的原生复用。要求保留逐条receipt，Context/profile/instruction不同时继续重建，不按消息语义丢弃；实现前报告最小路径。Astra token_deep_astra 继续独立GitHub体验审查，不承担本次修复。

收益验证边界：Braid协议测试证明消息形状；当前已运行会话中的重复历史不会自动消失，真实token节省要在下一次已授权材料接续/运行观察，不能冒充已经取得实验结果。

Pi验证已完成：`cargo test --bin braid provider::pi::terminal_tests -- --nocapture`，3 passed，0 failed。首次尝试--lib因仓库仅bin target而未执行测试，已改用实际bin。现有dead-code warnings保留。源代码start_session原先清空并由ProviderSession::start inject，resume清空且沿用原生历史，未改变。新测试从实际start_turn发出的RPC消息检查busy Deferred、拒绝后重试、接受后的增量消息、重新装载Context。未增加任何Factory/设施/Corpus测试。

6-Sol 实施：`src/store/mod.rs` 在 reactivation 确定 recipient 后，将同 work item、成员和 assignment revision 的待送达 `direct_contact` 一起编入单个 wake batch；旧 recipient/revision 的待送达联系标为 superseded，并分别结清 receipt。active/finalizing 时新进入的 direct contact 即安排 wake batch；已有排程中的联系会阻止 idle Agent 误休眠，未排程的旧联系不阻塞终态。批次中每条 event 和 receipt 仍独立，turn 开始和未开始回退走现有逐条状态转换。验证：`cargo test sleeping_member_batches_real_comments_and_keeps_each_delivery_receipt -- --nocapture` 通过；`cargo test store::closure_tests --quiet` 8 passed。测试经实际 `LocalObjects.comment` 入口覆盖沉睡、materializing 期间到达、旧身份、逐条 receipt、未开始回退及 active 期间新联系。未运行 Factory/设施/Corpus 测试。首次 `--lib` 命令因仓库无 lib target 未执行测试，改用 bin 后通过。

原生 sleeping session resume 本次未实现，不能将批量送达称为原生复用。当前 `provider_resume_candidates` 排除 sleeping session，`clear_provider_binding`/`record_provider_resume` 只接受 idle/unknown，而 reactivation 会把旧 sleeping session 标为 replaced 并创建新 session。安全复用还需同时确认成员身份、profile、instruction、context 一致，以及原生会话文件和持久化状态的生命周期；此次仅消除一批 close 联系的重复唤醒/启动，不声称实际 token 节省量已观测。
