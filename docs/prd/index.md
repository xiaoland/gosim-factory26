# Factory26 产品说明

Factory26 用于开发和比较参加 GOSIM Agentic Factory / ARC-bench 的 Agent Harness。使用者是开发 Harness 的工程师；运行时 Agent 接收需求包并生成应用。开发仓库的 Coding Agent 与被评测的运行时 Agent 是不同角色。

项目要让每次实验能够回答：输入了什么需求、使用了什么模型与 Harness、产生了什么应用、评测如何结束，以及证据在哪里。具体运行方式由[运行文档](../deployment/index.md)维护，单次结果由[四组实验报告](../../reports/2026-09-20-harness-matrix.md)维护。

## 当前能力与范围

当前开发一个 Braid + SVC harness；Pi 和 Codex app-server 是同一配置下的 backend，每次 run 选一种核心，默认 Pi。旧六份组合配置退出活动入口，后续消融另用显式自定义配置。内部 backend、workflow 与 svc 保持独立，受控检查仍可关闭 SVC；配置收敛不建立 Braid 与 SVC 的直接依赖。比赛模型、需求和外部评测版本由配置声明，实际使用的组件源码随每次运行归档。

Codex 通过 app-server v2 接口驱动，使用固定版本 LiteLLM 将 Responses 请求转换为比赛网关的 Chat Completions 请求。适配器是实验条件的一部分。Pi 直接使用比赛网关。运行时保留核心默认系统提示和原生工具；尚未添加额外技能或 MCP server。

SVC 是当前 harness 启用的 Corpus 工作方法，通过核心的 user-scope AGENTS.md 注入。文档归属、任务包组织、verification 和工作姿势由 Agent 按实际需要采用；运行器不把 SVC 任务包作为调度协议，也不复制开发者个人指南。已有设计或实施事实的权威正文应被引用，避免任务包产生第二份权威副本。

braid 的本地模式由 `sources/braid` 维护。Issue、PR 和 comment 的完整当前对象存于本地数据库；Agent 用 braid CLI 修改 description、创建或 hide/unhide/delete comment、关联和交付 PR。对象写入与语义事件同事务完成，现有投影、队列、Agent Group 和会话链负责传播变化。description 变化和 comment 可见性依其来源与关联关系自动失效；自身写入不自打断或制造额外唤醒，但下一次正当执行前必须获得最新上下文。重建保留逻辑 group 与 worktree，替换物理会话并拒绝旧 turn 的控制写入。

根 Issue Agent 维护需求设计并判断交付，PR Agent 在各自 worktree 实现和自检。一个 Issue 可对应多个 PR，一个 PR 可关联多个 Issue；不固定角色往返次数。PR ready 不是自动合并或完成；根 Issue 接受 PR，将指定提交合入本次 delivery branch，并在交付自检与未完成事项处置后关闭为 completed。Braid 等待生命周期收尾和执行收敛后返回固定 commit，Factory 据此导出冻结应用。GitHub 平台接入被裁减，保留本地产品对象与 Git 工作树。

Braid 对 SVC 没有运行时依赖，SVC 也不调用 Braid。user-scope 只注入两行 Corpus 导航；无人值守授权、允许本次临时仓库内 commit/merge 及比赛隔离规则归 Factory 任务契约。CLI/config 收敛只经过本地无模型检查，不以此推导真实核心和 bench 通过。父子 Issue、同类 Agent 并行及共享 packet 的完整协作链仍在设计中；当前每种角色只运行一个活动 turn。

获授权的实验先确定 backend 和实际源码，再根据需求生成应用，冻结后运行官方 Keep 全部 32 项测试。所有设计、实现、上下文重建会话都属于同一次生成，usage 共同计入。SVC 与 braid 在项目内独立 Git 仓库共同开发；变更后重建，以源码哈希和运行归档区分实验变量。首轮四组分数属于旧的 tasks/generation 补丁，不能用来证明当前 braid 本地模式正确。

当前增加可打包的 Linux 参赛入口，接受平台需求和模型配置，交付 frontend/backend 应用；它复用现有生成与冻结链，具体边界见运行文档。活动配置采用平台部署契约，历史 run 按归档配置保留原契约。当前质量验证仍为本地单任务流程；已有 Playground 无模型探针不能代替新包的真实平台兼容性和完整评分验证。Keep 单任务分数不能表述为完整 ARC-bench 或线上 Lite 总分。各次结论记录在 reports/，未完成的实验不能计为零分或成功结果。

## 实验规则

每次实验无论成功或失败，都先汇报已观察结果、原因判断与限制，由用户确定下一轮方向。持续沿用的验收方案不等于自动补跑或连续迭代授权；用户要求停止时，应中断活动实验并保留证据。

独立生成基线只根据允许的需求与资源实现应用，不能读取外部验收测试、参考应用或先前失败报告。Agent 可以编写自己的检查并据此修改应用；外部评测必须在生成结束、应用冻结后执行。

如果后续实验主动使用公开评测反馈修复应用，必须创建新的 run 并标明 `oracle/dev-only`，不能与独立生成基线混淆。线上提交资格需要单独验证，不能由本地流程跑通推导。

固定并记录 benchmark 版本，不修改评测器来适配生成应用。完整评测中的失败用例是有效实验结果；安装、构建、启动或评测中断不能当作有效零分。上游需求或评测缺陷需要记录证据及影响。

每次实验保留输入和应用哈希、模型参数、原始 rollout、usage、退出状态及评测结果。缺失指标按未知处理，客户端费用估算不等于比赛账单。原始产物保存在被 Git 忽略的 `runs/`，可长期分享的脱敏结论保存在 `reports/`。

## 持续采用的验收基线

一次获授权实验选择一个 backend，独立生成一次 Keep，冻结后执行官方全部 32 项测试；不要求应用零失败，但漏例、跳过、生成或评测基础设施失败不能作为完成验收。固定模型、需求、benchmark、核心和实际组件来源。不再默认展开旧四组矩阵，也不因 variant 名相同而混合不同 backend 的实验条件；单次结果不足以作统计排名或完整 ARC-bench 总分。

两个真实核心另有关闭 SVC 的受控 Braid 场景，验证对象 CLI、上下文替换、旧 turn 拒绝及本地 PR 交付。诊断独立验收要求通过真实页面/源码和官方事件区分失败原因、心跳、有效进展与观测过期，并能核对会话、交付源码和评测身份；不以日志数量或输出行数代替可用性。用户已确认这套基线，范围和判据无实质变化时持续沿用。
