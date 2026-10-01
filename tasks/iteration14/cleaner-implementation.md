# I14 cleaner 实现与反馈

2026-10-02。用户已明确授权“可以实现、基础验收、启动实验”。本实施只修改 I14 cleaner 对照和 Braid 对象维护模块，不修改 I13，不自行启动 benchmark、Console 或监控。费用通道以主线最新冻结决定为准：用户已撤销自有 API 选择，I14 继续 ARC API；cleaner 消费当前注册的 `factory26/glm-5.3-flash`，不自己选择供应商或读取凭据。

当前完成了源码、variant 接线、联合编译和真实旧身份/外部维护拒绝反馈，尚未取得真实模型正向提交反馈。实现依据为 [cleaner 准备预演](cleaner-preparation.md) 和 [已认可机制](mechanisms.md)。基础验收用编译和实际读取、拒绝反馈，不编写或运行 Braid/Factory 测试、smoke 或探针。

## 当前接口与边界

Pi 主会话加载 `factory-cleaner.ts` 后提供无参数的 `braid_cleaner`，串行执行。两个负责人 profile 都只有按需触发指引，不要求负责人写维护计划。`run.py` 为每个原生材料目录装配独立 cleaner 职责、共享要求和冻结模型配置；共享要求来自现有 `RUN_CONDITIONS` 与中文表达约束，SVC 技能正文不被内联。

扩展沿本次 toolCallId 找到产生工具调用的 assistant entry，截到其 parent leaf，在内存调用生产 `buildSessionContext` 和 `convertToLlm`。完整历史工具调用必须配对；找不到准确边界或存在悬空调用会拒绝。它不打开、fork 或改写主 SessionManager，也不声称该历史就是经过全部扩展变换的最终父模型 payload。来源记录 leaf、发起 entry/toolCall、分支摘要和源文件摘要。

`braid maintenance snapshot --operation-id UUID --native-source FILE` 必须取得有效当前 writer，由 writer 的工作项决定目标。快照包含原始完整正文、该项全部评论的原文与作者、线程关系、可见性、截止、版本，以及实际供给的 OPEN 关联 Issue 与祖先需求背景。`braid maintenance apply --input FILE` 严格接收 snapshot、声明式 result 和独立响应的模型/usage事实；其短 immediate transaction 先查同操作回执，再检查当前 writer/指派、完整来源摘要和整批合法性，最后写入对象、原有事件/投递、维护活动及持久回执。没有 external 维护写入旁路。

结果仅支持可选最终 description、带理由的 hide 评论数组和 resolve 讨论根数组。正文使用现有 HTML 注释过滤规则判断是否产生 context 失效；一次净正文变化只调用一次现有 `description_changed`，Issue 变化继续传播到现有关联 PR。hide 保持隐藏当前及未来后代的现有语义。resolve 截止取自已核对未变化的完整快照，不把提交期间未读的新回复折叠。维护不创建额外完成评论。

同 operation ID、完全相同请求直接返回已有回执，不重复效果；同 ID 的不同内容拒绝。`braid maintenance receipt UUID` 是只读恢复入口。模型仅执行一次 `ctx.modelRegistry.complete`，不提供工具，禁止重试；只有 stop、无工具调用、结构合法且未观察到取消时才启动 apply。启动短提交进程后不再用 AbortSignal 杀它，已提交事实通过 receipt 返回；回执读取也失败时标为 commit_unknown，不报告未修改。

预算通过现有 `model_budget.mjs` 的 `claimModelSession`，owner 为快照捕获的 Braid agent ID，不建第二 Pi runtime 或 sub-agent。原生输入、响应、待应用结果、usage、回执与错误在 native home 的 `.factory/maintenance/<operation-id>/` 保全。cleaner variant 在回收工作区前把这些目录归档到 run 的 `maintenance/<native-home>/`；复制失败单独记录诊断并保留工作区，不改变应用生成状态。诊断材料脱敏已知 API 环境凭据，实际 apply 输入保留准确字节并以 0600 私有文件提供给 Braid，避免脱敏改变来源前提或应用正文。SDK 返回的全零 token 初始化不被当作 usage 事实；没有提供可辨认用量时 receipt 记 null。SDK cost 仅是模型注册信息的估计，不能当作实际账单费用。

## 已取得反馈

`esbuild` 已完成生产 cleaner 扩展的 ESM 编译；Python `py_compile` 已完成 cleaner variant 的 `run.py` 编译，产物归 `runs/iteration14/cleaner/static/`。联合 Rust 首轮 `cargo check` 在 reviewer 共享接线过程中失败；接口收敛后 `cargo build` 完整通过，仅保留 11 项既有 dead_code 警告，最终日志在 `runs/iteration14/cleaner/static/braid-build.log`。

对保全的真实 I13 Pi 会话，使用已安装 Pi 0.85.1 的生产 parse/projection/消息转换函数读取了一个发起工具调用之前的有效分支：154 条消息，79 个历史工具调用，悬空调用与无对应结果均为零，发起 assistant 被排除。源文件前后 SHA256 都是 `a724d960c21e13be7d5a6b1008b465e8d63adaad66ac426d30ff208e37683d1b`。该样本不存在 compaction，压缩继承没有真实样本验收；没有为此造压缩历史。事实与投影原件在 `runs/iteration14/cleaner/native-prefix/`。

对保全的真实历史 Braid 数据库作只读 backup 后，用新 binary 独立运行了三个生产 CLI 操作：读取 Issue 1 的 number/state/body 成功；以实际 completed turn 和 replaced provider session 发起 maintenance snapshot，退出 1 并返回“当前调用已失效，本次修改未写入”；宿主用 --external 发起 snapshot，退出 1 并返回 `maintenance requires a current owner execution; external writes are not supported`。所有对象、评论和 events 行前后完全一致。原数据库文件摘要也没有变化。原件、完整退出值及身份来源在 `runs/iteration14/cleaner/cli-rejection/`；这证明写身份被前置拒绝，不宣称已验证正常提交或来源竞争。

## 待取得反馈与主线集成

主线已注册 objects 和 CLI 维护模块；reviewer worker 已注册 store 中 17/18 迁移。0018 的正式路径为 `sources/braid/migrations/0018_work_item_maintenance.sql`。还需主线安排的一次有限真实 Pi owner → cleaner → Braid apply 调用。该正路径不能用伪造 running turn、assignment 或 provider 身份代替。

持久 Braid 约定已整合到 `sources/braid/docs/20-product-tdd/local.md` 的“工作项维护批次”；variant 触发与运行材料留在 cleaner 对照中。2026-10-02 主线明确源码、基础拒绝反馈和历史继承证据已足够交接，第一条正式 cleaner 运行的正向模型操作由主线接续；本子任务未发起付费模型调用，不持有模型费用结果。

有限真实调用需保留父工具调用/返回、独立 stop、来源 leaf、维护回执、对象/事件顺序和费用归属，至少发生一次有效正文或讨论净变化。源变化、取消和旧身份的拒绝仍需实际运行身份反馈；通过编译或正常完成本身不证明这些竞争边界，也不证明 cleaner 有净收益。长期对照和具体输入矩阵由主线冻结配方持有。
