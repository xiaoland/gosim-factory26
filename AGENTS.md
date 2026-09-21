# Factory26 开发入口

本仓库开发需求到应用生成的 Agent Harness。开发仓库的 Coding Agent 与被评测的运行时 Agent 是不同角色。

## 文档归属

- [文档索引](docs/index.md)：长期文档、历史输入和实验记录的导航。
- [产品说明](docs/prd/index.md)：目的、当前范围、角色和实验规则。
- [运行文档](docs/deployment/index.md)：环境、凭据、执行、恢复和证据查询。
- `variants/`、`scripts/`、`tests/`：可执行参数、行为和边界检查的事实来源。
- `reports/`：单次实验的脱敏结论；`runs/`：被 Git 忽略的原始产物。
- `docs/handoff-original.md`：保留的原始设计输入，不是当前规范。

## 工作约定

先更新发生变化的语义归属文档，再更新入口链接；不要在 README、任务包和长期文档之间复制同一份规范。机械可验证的事实优先由源码、配置和测试维护。项目共享说明不导入个人指南。

非简单任务使用 `tasks/<task>/packet.md` 保存目标、当前状态和验证结果。任务结束时，将长期有效的变化整合进对应文档，再删除任务包；有保留价值的实验结论与原始证据分别留在 `reports/` 和 `runs/`。

修改生成或评测流程前阅读产品说明中的实验规则。外部评测只能在生成结束并冻结应用后运行，不能把失败详情回灌到同一次基线，也不能修改 `third_party/` 的评测器来适配应用。

诊断实验先使用 `python3 scripts/run_feedback.py brief runs/<run-id>`；具体用例使用 `factory.py show <run-id> --case <REQ-ID>`，再按入口查询 SVC evidence。原生 rollout 只用于明确问题的定向取证，不默认铺进主会话。可用 `analyze --svc-source ../svc` 采用相邻 SVC 工作树，操作说明归属运行文档。

## 实验协作

一次实验的目标、输入和完成条件先记入 task packet。无论成功或失败，先给用户结果、证据和限制，由用户决定下一轮；沿用验收方案不等于授权自动补跑。改设施与跑模型是不同授权范围。

Harness 与开发设施的非简单改动按以下顺序推进：诊断与方案复核、验收方案复核、实施计划与独立 Agent 预演、向用户呈现具体影响及预演结果并取得明确开工同意（impact handshake）、实现前提交、实现与验收、结果汇报。设计、验收或推进顺序获批不替代开工同意；不能从“继续规划”或“按顺序推进”推定授权实现。task packet 记录每个门槛及其证据，未完成开工确认时明确暂停源码实施和新实验。开工后在已同意的边界内持续完成实现与验收，只有实质范围、设计或风险改变才重新握手，不逐项重复请示。

调查、只读诊断、隔离预演和 task packet 整理可以在开工确认前进行；预演默认不修改产品源码，不发起正式实验。实现前提交属于开工后的第一项操作，不能用提交本身替代 impact handshake。已有明确批准且未发生实质变化的验收方案继续沿用。task packet 将控制状态、设计和实施计划按需要拆开，不堆成单文件。能由 Agent 完成的验收由 Agent 执行，只把必须由用户操作的部分留给用户。

技术方案先在 HLD 明确语义权威、资源所有权、生命周期和跨组件不变量，再在 LLD 核实实际 API、状态形状和失败合同。实现计划要把未知前移为最小 spike；能用公开接口输出验证时，不等完整 E2E 才发现接口假设错误。若时序、并发或边界补丁开始累积，暂停局部修补，回到更高层检查所有权、顺序和状态模型；优先让正确架构消除状态组合，再保留边界必须的防御。

确定性程序负责采集、去重和判断执行终态。较低成本子 Agent 用于边界明确的事实采集、黑盒场景执行、等待和证据降噪；不要把阅读同一份实现的 sub-agent/reviewer 当作发现问题或独立验收的机制。主 Agent负责源码推理、跨组件设计和最终判断，并用不共享实现假设的可复现输入与外部输出核验结果。

长实验由一个获授权的子 Agent 持有运行与等待，利用进程退出和子 Agent 完成消息回传。主 Agent 不定时轮询运行，也不每三分钟唤醒模型读无变化状态。只有远端缺少事件接口时，后台程序才从三分钟间隔起采集；错误和重试由设施提前暴露，心跳和 token 增长不算语义进展。通知边界与恢复命令见[运行文档](docs/deployment/index.md)。

项目检查入口为 `make test`；文档变更检查本地链接和 `.venv/bin/svc status --json`。本项目使用 `.venv/bin/svc`，以下 SVC 生成导航中的命令也用该路径执行，避免误用全局旧版本。

<!-- svc:begin -->
## SVC

Use `svc --help` or `svc <command> --help`.

- `svc status`: inspect project state
- `svc lookup`: read SVC guidance
- `svc task init`: create a task packet
- `svc task grow`: inspect packet shape without changing files
- `svc dev`: manage declared development targets

If `AGENTS.local.md` exists, read it after this file. It is ignored local guidance; shared rules belong here.
<!-- svc:end -->
