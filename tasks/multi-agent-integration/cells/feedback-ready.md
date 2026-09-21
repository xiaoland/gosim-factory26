# 诊断与实验反馈 × 接入就绪

Track：feedback。Phase：ready。状态：active，局部计划当前由主 Agent 持有；本轮诊断扩展及八项批次入口尚未实现。

本 Cell 让开发者从短结果回答“哪个 Braid Agent/原生子会话做了什么、哪里失败、依据在哪”，并用既有 runner 执行可恢复的固定实验。信噪比按真实调查所需判断，不以日志量、字段数或摘要字数衡量。

## 出口与依据

brief/show 能从 variant/task 下钻到 work-item/profile/native session 和用例证据，准确区分配置、加载、实际使用；父子 usage 不重复计数，缺失不当零。批次清单、状态隔离、终态唤醒和恢复可验证，不隐式重跑，不反复安装 runner/Chromium。生成冻结后才评测，分析失败不抹掉已有成绩。

诊断/批次方案归 [technical.md](../technical.md#诊断与批次)，跨返回判据归 [verification.md](../verification.md)，题包和资源身份归 [experiment-design.md](../experiment-design.md)。沿用 brief/show、SVC analysis、native manifest 和 ARC-bench report/trace；不新增日志数据库或工作流框架。

## 局部计划

1. **01：返回身份与终态接缝、检查样例。** 独立预演 Braid/原生子会话身份与归档链、usage 含义和终态/失联/恢复路径；准备一个能从短摘要定位原因的失败场景及批次状态样例。定义对 runtime/capabilities 返回值的实际需求。
2. **02：返回可查询的联合执行证据。** 共同实施前门槛通过后，随 runtime/capabilities 第一个闭环接入 manifest、brief/show 与 SVC 分析，保留原始入口；用独立身份/产物核对关联，不靠文件修改时间猜会话，也不将原生子代理注册为 Braid Agent。
3. **03：返回可运行的固定批次。** 复用单任务阶段增加薄调度及结果聚合，用边界替身核验完整、失败、失联、中断恢复和不自动重跑。核对 WSL 缓存/端口/工作区隔离，记录联合真实场景证据；与其他 ready Cell 汇合后，把固定输入和执行入口交给[固定批次 Plan](../experiment-plan.md)。

依赖的身份字段或归档能力缺失时，回到对应 runtime/capabilities owner，不能在诊断层编造确定结论。二者发生影响证据的变动，只重验受影响路径。

本 Cell 的 01/02 consumes runtime/capabilities 各自 01 的身份/材料合同；02/03 随联合执行消费实际会话、能力版本与生命周期返回，不等待两个完整 Cell 先满足 ready 才接诊断。向固定批次 Plan 返回查询/恢复命令、固定清单及环境就绪证据。Factory 的共享源文件由主 Agent 协调整合；日志语义过滤可有界委派，主 Agent 核验关键证据。
