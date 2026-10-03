# 状态、判断与呈现的职责复核

本轮只读观察主区及 d4ac01dd，未运行 status、采集或控制。独立验收报告已经覆盖真实保存记录的读取性能，本轮采用它而不重复操作。以下源码行号为 d4ac01dd 工作区的 projection.py。

projection.attempt 在 execution.json、remote-execution.json、observation.json、dispatch-observation.json 中按 `_time` 选择一个整体记录（145–185）。它核对身份，并且不让只有观察错误的记录替代 runner 事实，这些边界正确。但整体选择意味着执行、archive、telemetry 和 observed physical 状态共用一个选中的 producer envelope；长期应让事实的唯一 owner 决定该 facet，并让 observer 仅补充实际观察与新鲜度，不成为执行结果的另一个写入者。不据此声称已发生错误覆盖；这是源码可见的职责混合和后续回归风险。

stages 默认每个 job 展示最新 attempt（323–338），未分配的依赖又由当前最新 producer 推导输入（348–362）。展示默认最新可以保留，但必须表明这是展示选择；执行绑定由显式 request 保存的具体 source attempt/output 或 artifact 决定。选定下游 attempt 后原输入已冻结，不会因后来 generation retry 重绑（342–346）；这条正确合同保留。

stages 将 controller 故障分配为各个非终态阶段的 blocker（369–375），并把终态但存在 artifact/observer/archive 缺口的 stage 改为 blocked（448–450）。因此“后台调度进程不可用”“模型仍执行”“入口已失败”“出口待运输”“缺恢复证明”虽然有分开的 facets，顶层仍混为一个 stage status。改为主运行状态由其执行 owner 提供；每项交付/观察/恢复能力分别显示，阻塞必须指明阻塞的是哪项操作。诊断证据缺失不自动阻止停止或消费已发布应用。

available_actions 和 next_actions 是候选操作提示，不应成为用户权限或未来调度计划。共享真正前置条件供操作和 projection 解释，避免投影复制整套完整验证。建议格式保留 operation/target/request scope、阻塞原因与所需证据，不把一个统一“next legal action”强行作为全阶段唯一入口。普通内容发布与完整 checkpoint 的能力差异继续明确展示。

独立验收发现 resource_wait 对结构化详情用统一300字符摘要，native/source/evidence 的绝对路径重复，用户仍要自选先读哪份JSON。修复应由 renderer 解释已有字段：资源种类及实际身份、当前值/阈值/连续样本、原具体原因和证据入口。未知保持 unknown，无法识别的字段仍保存在JSON并给原件路径，不新建原因分类数据库。显示一次根目录和受限成员；完整原件路径保留在JSON。摘要原件、平台回执、native窗口及人工下一步取证明确区分，不把读时间当 producer 观察时间。

已有 `factory26.exp.index` 只持有路径、不维护新状态库，是合适的多实验查询入口。补比较场景可消费的显式目录列表/小index，不自动递归发现全部runs，也不从索引创建执行。actual 旧I14 index不存在是操作交付缺口，不是需要一个新中心数据库的证据。

analyze.snapshot 读取明确 evidence 文件并固定其摘要、telemetry cutoffs；telemetry.snapshot 用 SQLite mode=ro。这两项没有发现混入执行或隐式采集，应保留。多原件读取窗口不等于完整状态checkpoint；既有analyze也未声称具备该能力。

验收使用真实保存记录及独立原件；不重新造测试、fixture或synthetic probe。本轮问题范围是职责，不以输出变短或代码变少作为完成标准。
