# 验收与实施顺序

## 当前阶段与复核门槛

用户要求推进第 1 项 Braid 产品与执行能力，随后明确这只是初步产品设计，技术方案、验收方案和实施计划必须先复核。新增 agent-profile 属于另一个项目，归第 3 项 Factory 装配；本轮保持现有 profile，不开始 Corpus 清理或新的 provider 扩展装配。

| 门槛 | 当前事实 |
| --- | --- |
| 产品方向与本轮范围 | 用户于 2026-09-21 同意；本轮仅第 1 项。 |
| 技术方案 | [technical.md](technical.md) 已获用户同意。 |
| 新增验收方案 | [verification.md](verification.md) 已获同意；既有 bench 基线沿用。 |
| 实施计划与独立预演 | 已完成，结果见下文；对象层也由独立 Agent 预演并复核实现。 |
| 实现前提交、源码实现、验收执行 | 基线 `08f177a` 已提交，源码和本地检查完成；真实验收见 [execution.md](execution.md)。 |

## 实施计划

1. **收敛接口和风险。** 复核技术与验收方案，明确 thread 回复/折叠及投递范围、自编辑替换的可见行为。独立 Agent 随后按真实调用路径预演迁移、CLI 消费者、并发收尾/恢复和 provider 输入，给出具体修订。准备各检查入口与所需样例；不能把当前阅读源码等同完成这一门槛。
2. **提交实施基线。** 仅提交本任务的已复核 packet 和实施起点，Factory 与 Braid 各自仓库分开处理，不带入参赛 P0 等并行任务改动。
3. **实现对象与消息的完整使用路径。** 新迁移、对象关系、CLI、Context 投影和持久投递一起完成。按实际使用验证 thread、hide 理由、resolve 后新回复、reaction 和可选父子 Issue，不只交付数据库字段。
4. **实现上下文替换与独立执行。** 分离自身普通消息回声和真正失效，修正 continuation/terminal 竞态；再将 role driver 改为活动会话集合，同时修正 finalization 与 resume retain 的隐含串行假设。每步运行相关判别检查，保持 writer fencing、worktree 和 merge journal 边界。共享 store 代码由单一实施 owner 整合，不让并行 worker 猜接口。
5. **整合协议、文档与验收。** 更新 Issue/PR 指导和现有 owner 文档，核对 Factory CLI 消费者，构建并刷新来源记录；按验收方案完成本地检查，再进入已复核的真实 adapter 场景与单次完整生成/bench。每次实验结束即汇报，不自行补跑。

各步输出分别是可复核方案、干净实施起点、可用对象/通信、正确并发/上下文和实际验收证据。具体 worker 文件所有权在正式预演后确定；保持新 profile、SVC 清理和第 3 项装配的独立范围。

## 实施预演与所有权

2026-09-21 独立 runtime 预演确认方案可沿现有接口实施，并补出两项必须处理的细节：runtime 在 reset 已持久化为 interrupting、终态尚未收据时重启，必须在独占启动阶段接管并沿 reset-specific unknown 收据推进；现有 ProductSession 测试在同一 writer 上连续 edit/hide/delete 的脚本必须改为基于 canonical state 的可恢复步骤，不能放宽 writer fencing。先修复 store 的两种 terminal 顺序与重启恢复，再启用自身 Invalidate 并解除 worker 的全局 idle 门。

runtime 实施 owner 负责 `sources/braid/src/store/mod.rs`（含迁移注册）、`src/group/worker.rs`、`dispatch.rs`、两个 role resume 路径、SessionManager 及 `src/local.rs` 的 runtime 判别检查；主 Agent 负责 objects/context/CLI、新 SQL 迁移、CLI 集成测试、角色协议与文档整合。共享 store 不并行编辑。基线为 Braid `e0c3ca2`；Factory 基线提交仅包含本 packet 与其用户方法输入，排除 `tasks/competition-p0/packet.md`。

判别入口为 `cargo test session_recovery_tests`、`cargo test local::tests::`、`cargo test --test cli_writer_boundary`。检查须证明真实重叠、单 session reset 不影响同伴、运行中 close 恰一次收尾，以及 v4 升级保留旧对象；不能用执行时长猜测并行。

## 已完成的范围

CLI 对齐、直接 PR 创建和单一 variant/config 已按“预演→实现前提交→实现→本地核验”的顺序完成，该轮明确不跑模型或 bench。实现细节、检查与既有 Clippy 限制归 [实施核验](implementation.md)，不再在本计划重复。参赛包与部署适配另由 [P0 packet](../competition-p0/packet.md) 维护，其进展和授权不扩展本轮多 Agent 范围。

## 沿用的实验边界

既有完整 Keep 32 项、冻结后评测、官方 runner 不改、原生会话和应用哈希关联、每次实验后先汇报的标准继续沿用。技术、验收、实施方案已经用户同意；具体单次实验的输入与完成条件见执行记录，终态后汇报而不自动追加下一轮。

新增行为、场景、Oracle 与执行证据统一维护在 [验收方案](verification.md)，本计划不复制第二份清单。原先强制研究子 Issue、父 turn 结束让位及围绕这条流程的容量 1 验收已撤回；provider sub-agent 当前只核查能力边界，不以未接通的扩展作为本轮完成条件。

## 后续项目与责任边界

顺序：方案与新增验收边界复核 → 具体实施计划和独立 Agent 预演 → 实现前提交 → 实现及必要检查 → 单次获授权实验 → 结果汇报。

SVC 的现有结构和内容不预设保留，后续以实际消费问题审查删除、合并、重写；新增 profile、provider 扩展和 Factory 方法/材料装配在第 3 项处理。这些工作不在本轮偷偷纳入，也不作为本轮 Braid 实现的先决条件。相互依赖的运行边界不分给多个 worker 猜同一接口。

当前产品复核已由独立 advisor 审视“能力与编排”的边界，主 Agent 核对 worker、会话契约和 SVC 范式。后续预演围绕原生 sub-agent 能力、当前同类 worker 串行化、上下文替换及会话树生命周期开展；本轮讨论不冒充已完成的实现预演。
