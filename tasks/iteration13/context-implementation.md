# 上下文重建策略实施

2026-09-30。用户开工原话：“我同意你对上下文重建的这套判断，可以应用修改了”。范围为 [CR01—CR12 清单](context-reset-catalog.md)已给出的取舍：日常只有有效description变化触发重建，且跨项传播必须存在真实描述依赖；恢复不因非description变化、全配置摘要或执行结果未知就丢弃原生历史。
I12保持暂停，不部署到冻结运行，不启动新模型实验；CLI的独立开工授权及结果见 [cli-implementation](cli-implementation.md)。

## 分工与顺序

1. CLI worker完成并释放 `objects.rs` 的回执/范围修改，主线接续其结果修改对象事件分类，不同时写同一文件。
2. 主线负责 `objects.rs` 与 context/local 技术说明：description比较；comment/title/relationship增量；自操作排除；description依赖传播；休眠描述事件的指派归属。不顺带改SVC、variant、提醒频率或正文折叠策略。
3. GPT-6.1 Sol / high worker负责 store/group/provider 恢复路径，单独维护 [恢复实施记录](session-continuity-implementation.md)。依据已完成的恢复预演，先核实原生配置/恢复接口，再修正CR08—CR11；保留旧执行停止确认与具体失败依据。
4. 汇合后编译、核对实际CLI/help和可读取的既有材料，保留可重复的真实操作检查入口。模型运行、写入现存工作项、暂停解除及热部署均未包含在本次实施中，行为尚未实际观察的地方明确留为未验。

## 跨组件约束

对象事务只为description有效变化产生Invalidate。事件指向当前具体指派的成员/revision，休眠成员的描述失效保留但不独立唤醒；恢复事务判断该指派是否有未应用描述变化。
新的title/comment/关系仅作增量，当前操作者不接收自己的操作；其它实际参与者/关注者仍能获知，不能把消除reset变成丢消息。
resume保留旧原生历史与实际context revision；真正start才登记新投影，不把未发送内容记作已送达。
未知执行需要先确认旧执行已停及原生可恢复性，不通过盲重放或宣布完成解决。确切历史丢失和新负责人有显式的新建理由；原生 adapter 类型等不兼容配置明确报错，不据此自动抹去历史。
description与指派变更、评论输入同批时各自保留归属，不让旧指派的失效事件卡住新成员或消费其它输入。

## 落地状态

CR01—CR12 已落实到源码，对象侧与恢复侧已整合完成。
`objects.rs` 只在 `description_changed` 产生 Invalidate；有效比较沿用当前可见正文规则。
comment 变更汇入同一个参与者通知入口，保留动作、评论编号与读取入口，排除执行该操作的具体成员。
标题更新、父关系及 PR 关联变更按受影响对象负责人/显式关注者发增量，同次关系动作按成员去重。
仅 OPEN 关联 Issue description 向 PR 传播；休眠 Invalidate 保存当前指派成员与 revision，不排用于刷新上下文的唤醒批次。
CLI 子 Agent 已释放同文件接口；其实际事务回执和根评论校验保持不变。

恢复侧的原生配置核实表明，Pi/Codex 的 resume 接口支持当前模型和系统指令，同时保持原生历史。
旧 native home 原样保留，模板文件更新不自动覆盖其中材料；新模板在真正创建新 home 时采用。
当前进程也不因配置摘要改变立即重启。此边界避免把“配置摘要变了”误称为“历史已失效”。

## 反馈

最终 `cargo check --locked`、`cargo build --locked`、`git diff --check` 均通过；13 条 dead_code 警告保留，没有为消除警告扩大清理范围。
主线使用整合 binary `e2f58d6342f5c74be91dbbbf2c45511148e00fb5d76d1cb05ec6510956279d81` 复核 I11 既有归档：comment 347 单条精确读取；显式 thread 返回7项；body 与数据库原文完全相同；list 截断明确提示；冲突字段返回非零退出及具体原因。
完整编译日志与原始 CLI 回包在 `runs/iteration13/context-core-20260930/{build.log,cli-readonly.json}`。
编译及真实只读操作不等同模型行为验收；本次未创建测试、mock、fixture或专用模型运行，未提交或部署。
可重复的源码检查入口：在 `sources/braid` 执行 `cargo check --locked`；实际 CLI/只读对象反馈及命令归 [CLI实施](cli-implementation.md)。
尚未观察的行为包括活动会话 description 重建、休眠后的真实 resume、unknown 故障接续和并发修改送达；不能据此宣称已在 I12 生效。
后续获准运行时，同时对照对象动作、对应事件、assignment revision 与原生 session 身份，而不只看模型是否采样。
