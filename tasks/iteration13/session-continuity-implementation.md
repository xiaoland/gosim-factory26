# I13 原生会话连续性实施

2026-09-30。CR08–CR11 源码与生命周期文档已完成，最终整合编译通过，文件已交回主线。用户开工原话：“我同意你对上下文重建的这套判断，可以应用修改了”。授权覆盖 description-only 下的原生连续性、配置摘要收窄、unknown 安全恢复及确切历史丢失；不覆盖新模型/原生专用运行、部署或 I12 恢复。主线负责 CR01–CR07，CLI 子 Agent 负责 C01–C04。

计划是先核实实际 adapter 接口，再修改恢复事务与调度边界，最后编译并记录真实只读反馈。没有改变数据库 schema，没有新增测试、fixture、mock、probe 或模型运行，不提交。既有 dirty 修改均保留。

## 已完成实现与接口

CR08：AgentMaterialization 携带 description_event_ids，SleepingProviderSession 携带 provider_kind。恢复按真实 assignment 的 member/revision 捕获 pending description Invalidate，直接联系和 reopened 共用。取消重新开放时全批消费；start 只结算捕获的描述事件，混批其它输入保留。没有描述变化时 resume 发生在 render/Hard 检查之前，实际 context_revision 沿用旧 session；新投影只在实际 start 成功后由完成事务记录。当前指派改变会拒绝完成；旧 recipient_revision 的描述事件 superseded，reset 和普通输入门禁同样检查归属。

CR09：worker 不再以 Profile revision 或 instruction revision 失配生成替换。Pi spawn 的 --model/--thinking/--append-system-prompt，Codex thread/resume 的 model/developerInstructions 和 turn/start effort，是采用当前参数的实际接口证据。当前 native adapter、repository、成员及 worktree 仍须匹配。恢复完成事务更新采用的 instruction revision 与当前 profile revision，保留旧 context_revision。主线明确接受旧 native home 材料保留；native_template 仅在新 home 创建时复制，活动进程不宣称即时应用所有配置。旧版本因通用兼容错误被 blocked 且实际不变量仍成立的 session 可沿恢复重试，不因旧摘要错误永久锁死。

CR10：删除 unknown 直接创建 reset 和 replay 原输入的路径；旧 turn 保持 unknown。SessionManager.resume 必须取得 managed teardown 或 offline stop 证据；成功原生恢复后 record_provider_resume 原子置 idle 并按旧 turn 生成一次 uncertain_continuation Wake。输入只说明上次终态未知、已恢复及应核对历史/现场，没有内部 UUID，也不追认成功。即使全部对象已关闭，该已接受工作的一次恢复联系仍可接续。真正 description reset 的离线恢复保持独立条件，不把未恢复会话提前宣称为已经恢复。

CR11：SessionError::HistoryUnavailable 只用于完成 Pi 原生路径查找后的确切缺失；权限/读目录/歧义错误保留具体原因。仅 Codex 当前配置根未找到 home 不能证明历史消失，明确阻断。resume 的启动/超时/断连沿原 Deferred，不把暂时不可用永久锁死。新启动恢复进程失败后 factory 负责退出证明，失败保留 ownership，不能留下隐形 writer。record_provider_resume_error 保留原始错误于旧 provider session，fresh start 后仍可追溯缺失原因。

改动归属是 Braid src/store/mod.rs、group/{dispatch,worker,provider,session_manager}.rs、agent_session.rs、provider/factory.rs 与 docs/20-product-tdd/lifecycle.md。provider/pi.rs 的既有 dirty 修订保留，本轮无需额外状态框架。角色指引同步 comment resolve ROOT，仅允许讨论根；局部整理使用 hide。

## 反馈与未验边界

cargo check --locked、cargo build --locked 与 git diff --check 均通过，只有 13 条既有/移除使用后的 dead_code 警告。主线已独立完成 check/build，构建日志为 runs/iteration13/context-core-20260930/build.log；后续实际归档只读入口由主线核查。本 worker 未执行 SQL schema 准备核对。本轮没有真实模型 resume、unknown 后接续、缺失文件后的 start、混批消费、并发改派、失败 teardown 或配置变更实操，编译及源码核对不能证明这些路径已经端到端验收。

可重复的最小编译命令是 cd sources/braid 后 cargo check --locked 和 cargo build --locked。实际运行验收只从已授权运行中取得，不为补矩阵创建专用 run：description 未变时原生身份与实际 context_revision 保持；description start 只消费当前指派捕获事件；unknown 原记录不变且一次恢复输入独立于旧 batch；超时/权限问题不 fresh start；确认停止失败无第二 writer。I12 全程暂停冻结，未读写其现场。
