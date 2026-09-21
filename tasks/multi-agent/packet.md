# 单一 Harness 的多 Agent 协作

目标：把后续开发收敛为一个 Braid + SVC harness，Codex app-server / Pi 是可选 backend；让需求通过父子 Issue、PR、comment 和任务材料完成有边界的委派、并行执行、验证与汇总。

用户已确定上述方向，并接受根 Issue description 保存 Factory prompt、引用完整 requirements 包，子 Issue 按需要内联局部需求。Braid 与 SVC 继续独立：前者管理对象、关系、执行和上下文，后者提供协作方法，Factory harness 负责装配。2026-09-21 用户授权实施 CLI 对齐和 variant/config 收敛，明确本轮不用跑实验验收；完整多 Agent 协作链继续设计，尚未授权实施。

实施前核实：本地 CLI 沿用了部分 gh 动词，但对象层级、view/comment 和正文输入方式仍有差异。Braid 已有多个逻辑 group 和独立 worktree，但每种角色仅有一个活动 turn，多个 PR 仍串行；本轮不改变这一调度现状，也不引入父子 Issue 关系。SVC user scope 仍是两行查询导航，单独注入这些导航不能证明多 Agent 协作已接通。

本页保留控制状态和授权；[方案与证据](design.md)承接职责边界和共享材料判断；[验收与实施顺序](plan.md)维护授权门槛；[实施核验](implementation.md)记录当前 CLI/config 的检查与限制。调查、预演和实现证据各归其位，不将后续协作方案写成已完成事实。

本轮 CLI/config 已完成并通过本地核验：顶层 issue/pr CLI、直接创建本地 PR、单一 factory 配置与 backend 选择，以及受影响的测试、协议和文档。实现前已提交 packet；Braid 独立 worker 与 Factory 主 Agent 分别完成各自仓库，主 Agent 另以真实 CLI 验证 Factory 消费者。未启动 core probe、模型、Playground 或 bench。下一步由用户继续讨论完整协作链，未经复核不实现该部分。上一轮 `pi-svc` 的 [9/32 实验](../../reports/2026-09-21-pi-svc-keep.md)保持历史事实；[旧接入 packet](../braid-svc/packet.md)不因方向收敛而虚报完成。
