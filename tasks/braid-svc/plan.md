# 协作顺序与当前实施计划

本页是任务的工作控制入口。当前全局路径仍按明确门槛线性推进；预演与局部工作可以并行，但不能绕过设计、验收和集成门槛。若实施中出现可独立交付的长期分支，再按实际责任拆出局部计划，不预建空 Track/Phase/Cell。

## 用户约定与门槛

| 顺序 | 必须完成的动作 | 当前状态 |
| --- | --- | --- |
| 1 | 用户提出问题，Agent 诊断、分析、探索或必要隔离实验，建立证据和因果链。 | 已完成第一轮，后续发现继续更新 inquiry。 |
| 2 | 提出解决方案，交用户复核和讨论。 | 用户已确认修订方案；旧阶段循环不再采用。 |
| 3 | 设计验收方案，再交用户复核。 | 详细矩阵已确认，并作为后续默认基线；无实质变化不重复复核。 |
| 4 | 规划实现顺序，由独立 Agent 预演、排障，提前消除可预见阻塞。 | 两份静态预演已完成，关键接点经主 Agent 源码复核并整合；只修改本 packet。 |
| 5 | 实现开始前提交基线。 | 已完成：Factory26 `93a9eb3`、braid `36a644d`、SVC `9592494`，均保存未验收草稿。 |
| 6 | 按计划实现，过程中可以自主提交。 | 实施中；与方案相符的工程选择自主处理，产品行为变更需重新复核。 |
| 7 | Agent 执行自己能完成的验收；只有必须用户亲自执行的部分才留给用户。 | 局部检查和历史样本的独立评测链验证已完成；真实核心探针与四组新 bench 由 Agent 执行。 |

本任务前轮留下的修改不回滚。基线提交应清楚标识这些未验收草稿，不能把它们写成已完成成果。Factory26、sources/svc、sources/braid 分别记录可恢复的 Git 基线；父仓库忽略 sources 不代表子仓库没有改动。不得包含凭据、runs、构建产物或无关相邻工作树改动。用户已授权这些实施前和实施中提交，未授权 push/release。

只在真正缺少用户信息、无法作出工程判断或涉及高危决策时请求补充；常规不确定性先用证据和独立判断解决。当前验收已获用户确认；无实质变化不再触发复核门槛。

## 已完成的独立预演

| 独立责任 | 输入 | 输出与停止条件 |
| --- | --- | --- |
| braid 产品链路预演 | design、verification；braid HEAD 的存储/投影/queue/group/worktree/CLI | [braid 预演](rehearsal/braid.md)：具体切面、依赖顺序、故障和区分性检查；不得写源码或跑模型。 |
| Factory/SVC/诊断集成预演 | design、verification；Factory runner、原生配置、官方 SDK、历史样本 | [集成预演](rehearsal/integration.md)：完成/归档/证据映射接点、缓存和诊断缺口；不得写源码或跑模型。 |

主 Agent 已独立核对预演关键结论，交付条件整合进 design，真实核心重建、交付树一致性和诊断关联负例整合进 verification。报告保留调查时的建议，当前选择以这两个语义归属文件为准；不采用扩展为八组完整 Keep 或固定三次查询阈值的建议。预演是调查输出，不因独立 Agent 的身份自动获得验收效力。

## 拟定实现顺序

验收复核与预演已结束，先为三个仓库建立基线，再按以下顺序推进；具体文件范围以预演结果收束，不在此抢先冻结未知接口。

1. 固定本地启动、对象、CLI、事件和 writer 前置条件。Factory 初始化隔离 Git 基线；Braid 显式建立根 Issue activation 与首个 Wake。用一个 Issue/comment/PR 路径贯穿持久化、读取与事件处理。
2. 将配置、正文 materialization 和 worktree 接到本地来源，再接已有 queue/group/session；验证自动重建、精确回声抑制、旧 turn 拒绝、N:M 关联与恢复。移除本分支不再需要的 GitHub 平台路径和旧阶段循环。
3. 实现 ready/merge/root completed/finalization 及 Git/对象状态恢复，再接 Factory 交付 commit 导出、跨 worktree 会话清单、计量和归档。统一两核心的 CLI 入口并精简 SVC 注入；使用现有 source 构建校验，复用 WSL runner/浏览器缓存。
4. 实现独立诊断入口对 ARC-bench 现成证据和 braid/SVC 映射的定向消费，先通过历史真实失败验证推理链。
5. 执行局部故障检查和两个真实核心的受控场景，随后四组真实模型生成、冻结和 bench；分析有效成绩与基础设施失败，完成能由 Agent 执行的验收。
6. 将已验收事实整合进长期文档，保留脱敏报告和原始证据，检查残余事项后按项目规则删除 packet。

第 4 步中的历史 case 定向证据、官方事件消费、analysis 缓存校验和明确评测 ID 可在第 1—3 步期间独立实现；Factory 的 freeze/usage/archive/show 新对象映射须等第 3 步的完成契约稳定。只有源码所有权无冲突时才分配并行工作，不让尚未确认的接口成为两个 Agent 的共同猜测。

## 当前责任与集成返回

| 责任 | 所有权与返回 |
| --- | --- |
| Braid 本地化 worker | 独占 sources/braid；局部进度见 [Braid 实施](implementation/braid.md)，稳定接口与测试结果返回主 Agent。 |
| Factory 集成主 Agent | scripts/factory.py、core.py、braid_runtime.py、check_braid.py、harness 与对应检查；[集成进度](implementation/factory.md)。 |
| 诊断 worker | inspect_runs.py、playground.py 与对应检查；局部进度见 [诊断实施](implementation/diagnostics.md)。 |

源码接口由主 Agent 集成；真实模型与 bench 统一调度，worker 不私自运行。当前两个 worker 可以独立提交进度，不以局部通过替代整体验收。

Factory 独立审查见 [审查报告](implementation/factory-review.md)；报告记录调查时状态，后续修正与通过证据归 [集成进度](implementation/factory.md)。诊断另安排未参与实现的 Agent 从命令入口盲验，不提前提供答案。

执行调度调整：Pi 真实探针已完整通过；Codex 已交付并完成根 finalization，最后一个 PR finalization 模型请求仍在进行。两组无 Braid 的 Keep 与该收尾检查没有依赖，先并行启动它们以复用等待时间；两组 Braid Keep 仍以两个探针全部通过为门槛。验收范围和判据不变。
