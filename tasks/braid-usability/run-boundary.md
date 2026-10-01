# Braid、SVC 与 Factory 的职责边界（已获开工授权）

用户指出：Keep 已生成并合入应用，但 Braid 判“交付未完成”，导致 benchmark 无法评分。`reason` 的字面值失配只是触发点；真正的问题是 Braid 把工作项状态解释为 Factory 应用交付条件。

用户进一步要求审查其它同类耦合，并把既定工作流程应用到 Factory。
本页持有边界方案；Braid 的具体审计证据见 [boundary-audit-braid.md](boundary-audit-braid.md)，Braid Factory 的自主流程和成员指令见 [factory-workflow.md](factory-workflow.md)。
用户已明确“你可以应用这些修正了”，并限定工作流程仅适用于 Braid Factory、“像人类一样协作”不展开。当前进入源码实现，SVC 保持通用且不改动。

## 已核实的因果链

1. Braid `local.rs` 只在根 Issue 关闭、所有工作项关闭且 PR 合并等条件同时成立时调用 `seal_delivery()`；`objects.rs` 还要求根 Issue 关闭前至少有一个已合入 PR，并把 `local_run` 封存为 completed。任一语义条件缺失，`braid local` 返回非零。
2. 四个 variant 的 `run.py` 在该非零退出处抛错；`braid_runtime.load_delivery()` 又只接受 `result.status=completed` 和 `delivery_commit`。因此即使 Git 集成分支已有应用代码，Factory 也不会导出它。
3. ARC 适配器要求入口成功且 `frontend/package.json`、`backend/package.json` 存在，才进入独立评分。Keep 被挡在应用导出之前；其 `generation failed` 是接入层结果，不是应用评分。

旧 Keep run 的集成提交 `146ce2cac430d0e8e84ce9d4865d875c2edfa804` 已包含前后端两个 package.json。已将该确切提交单独归档为只读评分输入，原始 run 保持不变；评分证据位于 WSL `.../20260924/keep-salvage/`。官方本地 Runner 对该冻结应用完成了 32 项评测：19 passed、13 failed，test_pass_rate=59.4%；空 Agent 评测阶段的综合 `score` 为 null。这证明原应用可评测，不改变原入口因 Braid 状态而失败的事实。

## 建议的产品边界

| 所有者 | 正向职责 |
| --- | --- |
| LLM | 判断需求是否满足、是否讨论/拆分/合并/关闭工作项、选择交付候选提交。 |
| Braid | 持有 Issue/PR/comment/assignee、上下文、原生会话、工作树和 Git 集成分支；执行可运行的工作并报告 `quiescent`、`blocked` 或执行错误及当前 Git ref。Issue 的 close/reason 是对象事实，不是应用完成判定。 |
| SVC | 提供需求探索、设计、实现准备、V&V、任务包与有界委派方法，按当前问题装载；不依赖比赛、Braid 的对象模型或固定协作流程。 |
| Factory variant | 根据自己的产物契约从已选 Git ref 冻结应用，记录 Braid 运行状态和确切提交，提供前后端标准布局。 |
| ARC Runner | 对冻结的应用部署和评分；评分结果决定 benchmark 成绩。 |

Braid `local` 在可运行工作收敛后返回可恢复的状态和当前集成 ref，即使根 Issue 仍开放；它不要求根 Issue 关闭或至少合入一项 PR，亦不把没有任务完成的判断写成执行失败。真实 provider、调度或 Git 错误继续单独报告。Factory 只导出确切 Git 提交，不从任意未提交工作树或最近 PR 猜测候选；应用布局缺失由 Factory/Runner 如实记录，应用质量由 Runner 评分。Braid 的评论、分工和工作项历史仍保留供诊断，不会变成隐含评分门槛。

## SVC 的实际分发边界

审查对象是当前 `sources/svc/SKILL.md`、`references/` 和 `assets/templates/`，包括方法、V&V、原生子 Agent、任务包及模板正文。
这些材料没有直接引用 Factory、ARC-Bench、Braid、比赛评分、前后端平台布局或指定模型；其方法也没有要求截图、平台测试或固定的 Issue/PR 阶段。
`SKILL.md:31` 明确方法不添加产品需求或工具授权，`references/sub-agents/index.md` 把局部委派和独立任务负责人的协作区分开。
`scripts/agent_support.py:7` 仅复制技能入口与标准资源目录，`variants/pi-team-mixed/run.py:55` 使用原生 `--skill` 装载。
维护仓库中的历史 docs/tasks/CLI 不在这条实际分发路径内；这份结论不宣称整个历史仓库不存在旧语义。

当前无需为了采用工作流程再向 SVC 写一份 Factory SOP。
Factory 用任务指令选择并连接通用方法；Braid 提供对象和操作，使用者决定如何组织工作。
真实运行是否读到了合适方法、是否因此改善结果，仍由轨迹与运行证据回答，不能以静态目录审查代替。

## 同类问题的处理取舍

补充审查确认了下列行为；完整位置与调用关系保留在 [Braid 审计](boundary-audit-braid.md)。

| 当前行为 | 问题与建议 |
| --- | --- |
| PR ready 通知关联 Issue，merge 却只允许根 Issue #1 | 通知对象和实际可作决定的人不一致，子 Issue 被迫转交根成员。移除根成员独占合并权，保留当前 writer 身份与 Git 局部正确性；负责该范围的成员按任务授权决定整合。 |
| 通用提示固定隔离仓库、禁止 push、无人中途介入 | 这些是 Factory 作为宿主提供的环境与授权，已有 Factory 任务正文承接；从 Braid 默认提示删去，不再加另一层配置。 |
| 创建并指派 PR 的通知宣称“已授权实现、自检和本地提交” | 通知应报告已创建、已指派以及关联对象，具体授权来自任务上下文；对象事件不自行授予权限。 |
| 初始化根 Issue 时要求“通过 PR 交付” | 保留 Braid 的设计/实现分离，实际实施使用 PR；去掉把 PR 当成所有任务必须具备的交付凭据的要求。 |
| Braid 维护文档直接以 Factory bench 表述验收 | Braid 文档描述自身产品与接口；比赛接入和实验规则留在 Factory 文档。历史材料与当前规范分开。 |

保留的机制包括显式 assignee、关联工作项、评论通知、description/context 重建、有效写入身份、PR ready 的提交事实、Git 集成及错误报告。
它们提供操作与事实，不因存在状态或事件就等于替 LLM 作任务语义判断。
设计/实现分离也是 Braid 已确认的产品职责，不在此次边界清理中删除。

## 技术与实施边界

- 在 Braid 的 `local` 收敛路径移除根 Issue/PR 的交付判定，保留现有活动执行、事件、reset、阻塞与原生 teardown 的操作性判断。正常收敛报告 `quiescent`，保留状态以供后续恢复；删除只服务于“任务完成”判定的封存路径。
- 根 Issue 使用和其它 Issue 相同的 close/reopen 对象语义；理由保存说明。PR 的 ready/merge 仍保证 Git 操作的局部正确性。
- Factory 的四个独立 variant 读取 Braid 的操作结果并导出请求中指定 ref 的确切提交；把过程错误和产物是否具备评分布局分别记录。`braid_runtime.py` 从本次指定仓库和 ref 取得 commit，不解释 Issue 状态；运行结果作为独立诊断记录。
- ARC 适配器继续以标准入口结果和应用布局进入评分，不解析 Braid 内部状态。旧冻结 ZIP 与运行记录保持原样。

这跨越 Braid 产品契约和 Factory 接入边界，用户已明确授权本次修正。实施先处理 Braid 终态和 Factory 导出，再构建新的完整 Lite 制品；现有 `delivery-fix` ZIP 仅是旧边界下的临时诊断，不能充当本方案的验收。

## 验收方案

选一条已结束但 Braid 认为 incomplete、集成 ref 已有完整应用的原始 run（当前 Keep）冻结并独立评分，证明模型输出能越过协作状态被评测。新制品需在真实任务中分别记录 Braid 的操作状态、导出 commit、标准布局以及官方本地 Runner 的完整分数；工作项是否关闭不决定能否进入评分。若运行出现 provider/调度错误，保留原始错误及应用候选，报告操作故障与可评测产物两个事实。应用得分和 Braid 协作收益仍分开分析，一 run 一分析者。

## 实施与当前证据

已删除 `seal_delivery` 和根 Issue close 的全局完成门槛；merge 保留有效 writer、ready commit 与 Git 集成检查，去掉根 Issue 独占。
`local` 正常收敛报告 quiescent 并返回零，受阻报告 blocked，执行错误报告 failed；运行状态保留供恢复。
新旧操作终态均可作遥测最终取证，历史 completed/incomplete 仅供旧记录读取。
初始化、Assign 和 ready 通知使用对象事实，不授予任务权限或指令根成员执行验收。

Factory 四个 variant 分别记录进程退出码及 `metadata.braid`，从自身请求指定的 ref 取得确切 commit，再导出和检查平台布局。
Braid 结果文件不可读时留下具体诊断错误；其状态不阻止应用导出。
操作故障与交付失败均保留工作区；正常收敛且交付成功才使用既有清理行为。
六份成员指令只在 Braid Factory 中加入自主工作路线和一句“像人类一样协作、使用 Issue/PR”；SVC、模型、工具配置保持原样。

本机 Rust 构建、Python 语法编译及差异检查通过；未运行或添加 Factory/Corpus 测试。
新的源码交接为本机 `runs/braid-usability-implementation/braid-source-boundary-fix/`，远端独占目录为 `.../20260924/boundary-fix/`。
Linux release 构建与打包已完成，新 ZIP SHA-256 为 `4f581ac51e485a767954976abc17764ff799bd2a64eadf707b671b65a4a47d6d`。
同一 ZIP 的完整 Lite 两题已完成，原 Controller PID 为 895749，状态和日志位于上述 boundary-fix 目录。
gpt-6-luna/medium 监控已在终态返回；两题随后各由一个独立分析 Agent 完成证据分析。

| Task | 新边界 Run ID | 官方完整结果 |
| --- | --- | --- |
| Keep | `pi-team-mixed-arc-bench-lite-keep-bfdf6b8f51` | 27/32，84.4%，score=null；[独立分析](results/keep-boundary-fix.md)。 |
| BookStack | `pi-team-mixed-arc-bench-lite-bookstack-f065388906` | 30/34，88.2%，score=null；[独立分析](results/bookstack-boundary-fix.md)。 |

两题生成、导出和独立评测均完成；Braid 均返回 quiescent，Factory 对确切提交评分。
BookStack 没有 PR 仍成功导出，直接观察到 PR 不再成为交付门槛；两题根 Issue 都已关闭，因此开放 Issue 导出的运行场景尚无直接证据。
五项 Keep 失败主要涉及初始状态和操作入口；四项 BookStack 失败涉及漏 seed、草稿入口、登录条件以及一项尚未确定的评分 helper 时序问题。
自测通过没有覆盖这些不同条件，不能把自测次数或另一 Agent 重跑同一脚本当作独立验收证据。
Braid 协作收益仍未证实：Keep 根成员在创建 PR 前已完成主要实现，BookStack 无评论或 PR；不据接口修正和分数提升声称持续协作已经成立。
详细因果与证据限制以逐 run 报告为准，完成此次既定矩阵后未启动下一轮。

旧首轮 BookStack 已完成 29/34（85.3%），其独立分析另存 results/bookstack.md；临时修复版 BookStack 已完成 23/34（67.6%），见 results/bookstack-delivery-fix.md。
它们与新的边界制品独立，均不能充当本次修正验收。
本次没有提交，SVC skill 源码没有修改。
