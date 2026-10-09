# 长会话复盘与开发体验优化

2026-10-03。本轮结论是：接续成本的主要来源是当前决定、实现能力、实际运行事实和历史限制没有稳定地对应起来。目录和文档确有漂移，但这不足以解释所有损失；指定会话的暂停事故还涉及绕过控制边界的判断。继续增加状态表、交接协议或重排全仓目录，没有当前证据支持。

## 复盘覆盖

| 会话 | 证据覆盖 | 对本轮的用途 |
| --- | --- | --- |
| [重设计 I13 今晚无人值守实验](codex://threads/01a0fd22-fe3b-7430-9707-4534e7758565) | 完整分页至起点；9 个 turn、485 次命令、7 次压缩，截止 10-03 08:43:50，末 turn 在途。 | 准备耗时、暂停损失、同题并发及“本地 runner”误解。详见[时间线与原件](target-session.md)。 |
| [开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e) | 5 页、52 个 turn 的可见消息；2026-10-02 至 10-03。 | 状态投影、定义/运行数据分离、反复准备和局部反馈的边界。 |
| [整理项目数据、代码与文档](codex://threads/01a0fcde-a99d-7930-878c-6e3284c3ef36) | 3 个 turn；作为直接相关的整理对照，不宣称是最长会话。 | 文档漂移、多任务工作区，以及自行收窄完成范围造成返工。 |
| [factory26 main](codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2) | 沿用既有 26 turn／551 命令／8 个相关会话的复盘，另读末段原始窗口。 | 多负责人协调、I13/I14 交接串线。 |

这是有目的的样本，不是全项目会话排名。后三项的关键用户纠正、turn ID 和限制见[对照复盘](other-sessions.md)。工具数量与压缩次数不等于无效工作量，未对私有推理归因。

## 证据支持的判断

| 反复出现的成本 | 已观察事实 | 当前处理 |
| --- | --- | --- |
| 接手后重新裁决“哪份说明有效” | Deployment 写 experiment schema 1，实际为 2；开发指南 cache 路径落后于实现；实验 DX packet 顶部待开工、文末已实施合并。 | 改正权威正文，把当前答案从完整历史中分离。 |
| 重做已经完成的设施调查 | 较早会话缺统一状态投影；当前 `controller.status` 已聚合 index，并使用 `projection` 与 `available_actions`。 | 复用已有 status/monitor，按问题给源码导航；不新造摘要 CLI 或运行数据库。 |
| 把局部反馈当可直接运行的交付 | 有编译、1.4 GiB 材料复用、partial 恢复读回，但完整启动和热恢复没有在相同条件下验收。 | packet 明确交付时的证明范围与后续运行 owner；不把当时缺材料写成永远缺材料。 |
| 场所、职责和授权在长消息中丢失 | 官网 409 后误建串行队列，再把本地 runner 理解成 Mac；另有 I14 配方混入 I13 owner 的纠正。 | 明确控制宿主、执行 backend、评分场所；接续先读当前授权，随后读运行事实。 |
| 告警后的错误控制 | 04:50 暂停后恢复 404，首轮约 2 小时 43 分钟进度未接续；真实停滞原因未知。 | 接续导航直接指向现有恢复门控。目录整理不能被宣称为已修复这类决策失误。 |

目录核对没有证明独立 variant、历史证据和共享设施应合并。它们有不同消费者与版本身份；按文件数量去重会丢失这些边界。已跟踪文档与未跟踪构建/验证材料也必须分开计数，具体口径见[仓库核对](repository-findings.md)。本轮保留这些实现及原始运行材料。

## 已落地改进

1. [文档入口](../../../docs/index.md)增加接续顺序：主题入口 → 当前 packet → 所属运行的保存事实；控制或选检查点时进入恢复手册。它只提供导航，不复制动态实验状态。
2. [运行入口](../../../docs/deployment/index.md)纠正 experiment schema，并明确 Mac 控制端、官方 ARC 本地 Runner 和 Hosted 的位置关系。其它 Lab backend 仍按各自合同解释。
3. [开发指南](../../../CONTRIBUTING.md)修正 runtime 安装、构建缓存和 SVC 交接路径；将实验设施按“编译、readiness、状态、控制、制品”映射到实际源码，避免猜不存在的 `intent.py`、`schema.py` 或 `cli.py`。
4. [实验 DX packet](../../experiment-dx-review/packet.md)与[存储 packet](../../experiment-storage-lifecycle/packet.md)改为当前交付、授权、未验事项及证据入口。两份原文分别留在同目录 `history-20261003.md`，旧授权与失败事实不删除，也不把两项任务的成果合并成一个身份。
5. 本任务沿用既有 [developer-experience packet](../packet.md)，只保存本轮结果与入口。I14 运行 owner 继续维护自己的现场，本轮没有复制其队列或接管操作。

这些改进使用现有 Markdown、CLI 和状态投影，没有引入运行逻辑、依赖或新的管理服务。

## 实际接续核对

从 `docs/index.md → I14 packet → 夜间 packet / execution` 可以取得负责人、当前指示及 experiment 路径，再读取其 `experiment.json` 的 controller runtime 和 `source/` 中的冻结代码。本轮只执行三次已有 `lab status ... --json`，没有请求平台、安装材料或操作运行。原始输出、argv、cwd 与查询时点见[查询回执](../../../runs/developer-experience/session-recovery-20261003/status-query-receipts.json)和[有界摘要](../../../runs/developer-experience/session-recovery-20261003/status-summary.json)。

| 场景 | 保存事实给出的答案 | 必须结合的决定或限制 |
| --- | --- | --- |
| 已退役首轮 A | stage exited；平台 CANCELLED；archive partial；run `66e2c515dc3d`。 | 读取原始暂停/恢复 404 回执。不能把 controller completed、无 blockers 或 consume 动作当作可恢复检查点。 |
| A2 在途截面 | stage active；保存平台状态 RUNNING；下一动作 wait；run `8a282da5502e`。 | 查询时间为 08:54:14，平台原件观察时间约 08:52:53，二者分别保留；不当作实时完成或 OOM 结论。 |
| 已撤回官网等待队列 | 两项 waiting、没有 attempt；技术上可显示 start，并附授权条件。 | packet 和 dispatcher 原件已将该队列退役，不能因为 CLI 能列 start 而重新派发。 |

这三次单次只读查询各耗时约 0.11–0.13 秒，证明保存事实可以直接取得，不是整个 session 恢复时间或稳定性能基准。它们也说明 packet 的人类决定与 Lab 的执行事实各有职责，合并为新状态数据库并不能自动解决问题。

另一条接续路径为 `docs/index.md → 实验 DX packet → 交付结果 / 未验事项`：现在无需通读完整历史即可判断“源码已交付、main 已整合、完整生命周期未由该离线记录证明”。历史引用的 `runs/infrastructure-dx/` 原件当前不在本 checkout，packet 已明确这一点；不能把缺文件变成重新开工或已通过验收的理由。后续实际反馈归现有实验 owner。

## 验证和剩余边界

本轮用真实保存记录核对了接续答案，核对新增链接、历史原文保留及限定文件差异；没有编写或运行 Factory/Braid 测试，也没有模型实验、控制、部署、数据删除或 push。其它任务的并行修改保留。

两份任务入口正文合计由 75,863 字节降至 8,180 字节；实验 DX 为 309 → 44 行，存储任务为 61 → 39 行。两份历史页均与整理前已提交 packet 字节一致。此处只衡量当前入口的阅读量，完整历史仍可查，不推算 token 或工作耗时收益。[核对回执](../../../runs/developer-experience/session-recovery-20261003/verification.json)记录文件身份和链接检查范围。

尚未测量这些改进在未来长会话中能节省多少时间或 token。完整打包、启动、热恢复及生成收益仍归已有实验验收，不以本轮文档整理宣布完成。没有证据支持本轮进一步移动仓库目录、合并独立 variant 或建立强制交接 schema；如出现现有入口无法回答的具体问题，应先修该入口，而不是重开全局设计。
