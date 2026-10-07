# Agent Skills 实现审查与改进

## 目标与当前状态

依据 [技能编写指引](../../materials/skills/AGENTS.md)，修复本包发现的示例、依赖与分发问题，并按实际读取场景整理技能正文和 references。保留原则型、why/what 型技能，不以行数或统一步骤模板判断质量。

2026-10-08 本包六项材料修复已完成，相关 builder 已改动并通过 Python 源码编译；已复制实际选择的技能材料并人工核对。未构建完整 Linux runtime 包，未调用 MCP 或运行网格应用、模型生成及官方评测；不宣称技能采用率、token、耗时或评分改善。变化只对后续新装配生效，旧冻结包与在途运行未改动。

本包独立承接跨技能审查与修复。I15 的需求拆分、reviewer 生命周期及执行可见性仍归 [I15 packet](../iteration15/packet.md)，旧 [SVC Corpus 审查](../svc-corpus-review/packet.md) 保留历史适配。未接管这些任务的运行或其它工作区改动。

## 授权与边界

用户先要求“基于此，审查其它技能的实现，是否存在优化/缺陷”，随后要求“好的，创建相应 task packet”。接续时提出“我们来处理 factory26/tasks/agent-skills-review/packet.md”，在收到首批范围建议后明确授权：“开始全部项目的修复。”本次实施覆盖本包全部六项，而非只修第 1–4 项。

负责人仍为本侧会话，沿用本任务不使用或联系子 Agent 的边界。未获模型、评分或生成实验授权；后续已获 commit 授权，未获 push 授权。未创建或运行 Factory/Braid/技能内容测试、包 smoke 或换名自检；反馈采用源码编译、材料复制操作、文本和 API 合同核对。Mac 原件、候选材料及证据均保存在已核实解析路径与实际文件系统的 WorkSSD。

实施前已保存当前文件副本，因此能够区分本任务差异与此前工作区修改。共享 e2e、task-packet 和 I15 builder 的既有改动已保留；本轮未更改执行器、模型配方、费用或运行控制。

## 六项修复及实际消费者

| 原问题 | 当前修改及理由 |
| --- | --- |
| 1. minimal e2e 全文替换生成错误路径 | [共享 e2e 正文](../../materials/skills/e2e/SKILL.md) 使用绝对 `E2E_CONFIG`，通过 JSON 序列化构造 MCP 参数，并在 shell 中展开配置路径。两个 minimal builder 删除全文替换和正文切片，只复制 [minimal 接线 reference](../../variants/pi-minimal-vv/skills/e2e/references/runtime-setup.md)。路径直接来自 `E2E_PROJECT_DIR`，不拼 checkout；vv 与 tailwindcss 共用同一接线来源。 |
| 2. task-packet 引用包内缺失的技能 | [task-packet](../../sources/svc/skills/svc-task-packet/SKILL.md) 和 [planning](../../sources/svc/skills/svc-task-packet/references/planning.md) 将跨技能路线明确为可选，优先使用已安装的 `svc-specs` 或 documentation，并给出两者及委派技能缺失时的继续方式。未补装整套 SVC，也未将 specs 当作 documentation 的别名。 |
| 3. 网格同步混用视觉行与物理行 | [data-workflows](../../materials/skills/handsontable/references/data-workflows.md) 先转换主表视觉行，再按稳定业务 ID 找从表物理行；源写入覆盖从表排序、移动和裁剪。明确源写入钩子、验证与持久化责任，以及缺失业务对象的处理边界。 |
| 4. 自动保存未说明并发与重试 | 同一 reference 改为按稳定 ID 保存不可变快照，并由本地队列串行发送。失败批次重新保留且不覆盖较新编辑；明确后续编辑或 Retry 调用 `scheduleSave()`，不暗示已有自动重试。跨客户端和不确定提交须有后端版本控制或同时防重复、保顺序的协议；UI 计数器不能保证持久化顺序。 |
| 5. 浏览器技能混入局部运行接线和排障 | agent-browser 的检查、服务、日志和进程清理细节移至 [application-checks](../../materials/skills/agent-browser/references/application-checks.md)，正文保留会话责任、观察与证据原则。e2e 的环境接线和冻结版本排障分别归 [runtime-setup](../../materials/skills/e2e/references/runtime-setup.md) 与 [runner-results](../../materials/skills/e2e/references/runner-results.md)；模型值从实际 config/执行器取得。I15 的独立正文同样分层，保留其业务状态转移方法。 |
| 6. 原则技能完整案例按问题取用 | documentation 的多消费者案例移至 [shared-rule-adoption](../../sources/svc/skills/svc-documentation/references/shared-rule-adoption.md)；sub-agents 的数据查询与交互选择案例分别移至 [missing-parent-records](../../sources/svc/skills/svc-sub-agents/references/missing-parent-records.md) 和 [interaction-choice](../../sources/svc/skills/svc-sub-agents/references/interaction-choice.md)。正文保留定义、因果、边界和直接读取条件，完整案例仍可取得，未改成统一步骤模板。 |

I15 overlay 继承旧底包，仅修改共享源码不会自动刷新全部技能。因此 [I15 builder](../../variants/pi-braid-i15-reviewer-cleaner-e2e/build.py) 除原有 arc-bench、braid-collaboration 外，显式刷新当前 agent-browser、handsontable、svc-task-packet、svc-documentation 和 svc-sub-agents 的资源。I15 的 runtime/result reference 以源码链接复用共享文件，装配时读取为普通文件载荷；自己的 business-state-transitions reference 保留。其它使用 `copy_skill` 的消费者在后续装配时取得新增 references，不需要复制方法正文。

持久分发说明已整合到 [材料索引](../../materials/skills/README.md)；运行接线归 variant reference，当前结果和证据归本 packet。无需新增技术设计文档或检查框架。

## 核对结果与证据

证据目录：[repair-20261008-04e28ab3](../../runs/agent-skills-review/repair-20261008-04e28ab3/)。`before/` 保存修改前的当前文件与原始审查 packet；[materialization.json](../../runs/agent-skills-review/repair-20261008-04e28ab3/materialization.json) 保存复制操作、三个 builder 的编译结果及材料文件哈希；[task-changes.patch](../../runs/agent-skills-review/repair-20261008-04e28ab3/task-changes.patch) 仅比较本轮开始时的副本与交付文件，不把先前工作区差异混入本次修复。

已操作两个 minimal variant 声明的技能复制，并复制相应接线文件；I15 的本地 skill 文件载荷与共享 overlay 材料，以及独立 documentation/sub-agents 的材料，也已复制到 `materials/` 供人工读取。这里是技能材料装配，不是完整 runtime 包构建或包运行验收。已核对正文、读取条件、相对文件入口、源码链接解析及复制后普通文件，完整案例保留；task-packet 中未分发的跨技能路线有明确可选继续方式。三个 builder 编译成功，相关 Git diff 无空白错误。

Handsontable 的行号、源写入及变化钩子合同核对了官方 [18.0 Core API](https://handsontable.com/docs/18.0/javascript-data-grid/api/core/) 与 [18.0 Hooks](https://handsontable.com/docs/18.0/javascript-data-grid/api/hooks/)。自动保存逻辑只作边界与控制流核对，未在网格应用中运行，因此不宣称已观察到排序同步、网络失败重试或数据持久化结果。

## 完成边界

本轮已完成六项源码材料修复和上述材料核对，无待修项。用户随后明确“可以提交”，授权提交本任务改动，未授权 push。完整 Linux 包、真实 MCP/网格操作及技能发现、读取、采用与收益不在本轮证据范围；这些缺口不能用文本变短或编译通过替代。若后续另行授权行为实验，使用新候选、独立数据与进程责任，分别记录采用和效果，不回写旧冻结材料或将隐藏评测反馈注入生成中的 Agent。

提交核对发现，两个 minimal builder 和 I15 的本地 e2e 正文在本轮开始前已是未跟踪文件；I15 builder 的共享技能 overlay 机制也来自此前尚未提交的修改。用户明确“可以一起纳入”，授权必要的 variant 前置内容进入本次提交。已纳入两套 minimal variant 的完整源码、所需的独立 svc-specs 资源与发现链接、task-context 支持、I15 本地 e2e 材料及共享技能 overlay 机制，并保留本包引用的技能维护指引。

提交通过独立索引内容分离共享文件的既有修改；I15 的无关 runtime 补丁、SVC task-packet 的既有 description 修改、共享 e2e 的既有验收合同段落和 README 的其它材料改写仍留在工作区。没有把授权理解为提交全部工作区。三个新案例 reference 的末尾空行已在提交准备时清理，未改变内容。暂存候选的源码编译与 diff 空白检查完成后创建本任务 commit；结果与路径清单保存到证据目录的 `commit-preparation/`。不 push。
