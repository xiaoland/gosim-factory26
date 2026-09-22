# 诊断与实验反馈 × 接入就绪

Track：feedback。Phase：ready。状态：active。01 消费链调查和独立预演复核完成，见 [feedback.md](../rehearsal/feedback.md)；主 Agent 持有诊断与批次集成，实施起点提交后进入 02。

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

## 02 当前返回（2026-09-21）

原生归档已沿 Pi session-tree 与 Codex rollout parent metadata 建树，保留 profile/工作项与 native role 身份，并检查路径、UUID、冲突和缺失；代码检查还不证明实际运行必然提供完整证据。brief 增加观测模型、原生会话数/子会话数及证据状态；show 可按 profile/session 定向查询。Codex 父会话 usage 是否已包含子调用尚未验明，暂分组报告，拒绝盲加总。

固定批次控制器已落地 `scripts/batch.py`，复用现有生成/评测/analysis；模型生成与评测容量分离，使用 future 完成事件推进，后台采集仍至少 180 秒。冻结输入包括源码构建、材料、需求与 runner；终态失败不重跑，失去 controller 的在途状态保留 unknown，不新建竞争 writer。独立 worker 已修正容量与恢复边界；Factory 94 项 Python 检查通过（1 项平台跳过），包括八项去重、设施失败暂停和 analysis 异常不抹掉结果；Node lifecycle 检查也通过。尚未启动八项真实实验。

## Playground 备选执行位置（2026-09-21）

用户正在排查 WSL 网络，建议考虑在线 Playground；暂停新增 WSL 模型运行，已有受控检查保留终态。现有 HTTP 客户端已重新验证登录与 `/requirements` 读取，线上 benchmark catalog 显示 Keep32、BookStack34。原始响应保存在 `runs/integration/playground-availability-20260921/`。数量一致不能证明 runner revision 或用例身份等价，目前不更换八项清单的评测权威。

阻碍不在浏览器操作：上传/启动/等待/收集已有脚本。`package_agent.py` 仍只打包旧单 profile 配置与少量 scripts，Dockerfile 没有 pi-subagents/agent-browser/技能材料；submission 的平台模型配置也还只作用于单模型。直接提交会测错 harness。若改在线完整生成，必须先让既定 effective profiles 和锁定能力进入 Linux 制品，处理多模型映射与原生证据回收，再验证平台隔离/工具可用性；这是有实质范围的适配，尚未实施或上传。当前继续本机可完成的就绪检查，避免网络排障与工具链迁移相互遮蔽。

## 03 联合证据与批次状态（2026-09-22）

原生归档对真实 Pi 终态 receipt 的重放得到 21 个会话、0 个错误；Codex 场景的 rollout parent metadata 也能关联根线程与 executor 子线程。Factory 当前 99 项 Python 检查通过（1 项真实 Landlock 平台跳过），Pi lifecycle Node 检查通过。旧失败 run 保持失败状态，确定性的归档修复在独立 replay 输出验证，没有改写历史记录。

固定批次位于 `runs/batch-multi-agent-20260922-01`。启动时两项 pi-generalist 生成占满 2 个 generation workers，其余六项排队；evaluation workers 上限为 4。该路径只把 ARC-Bench report 的实际用例结果作为实验评分，可修复的生成、协议或设施故障返回本 Cell 继续处理，不作为“分数好坏”的停点。
