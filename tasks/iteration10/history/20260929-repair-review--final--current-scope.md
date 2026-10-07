# 历史入口快照

2026-09-29重整前的材料，仅供追溯；其中的当前状态和授权不再生效。接续请读[主packet](../packet.md)。原始文件：`repair-review/final/current-scope.md`。

# 最终独立修复复审：当前补充范围

用户要求独立审查已发现的问题和应用的修复是否针对根本问题、是否长期正确。
接续同一个最终独立修复复审，核对当前实现及其证据链，不重新全读两题、不重做已完成的终态归因，也不预设早期复审结论正确。
实验保持暂停；审查只读源码、运行证据与已有报告，只写本目录；不提交、不修改实现、不运行测试/探针/模型实验。

## 范围和分工

- methods：SVC七技能、角色/variant装配、工作方法及任务/项目文档边界。消费旧目录R/A相关项及下面M项。
- runtime：Braid协作/生命周期、Pi原生与PBB/observer边界、工具与analytics。消费旧目录R/A/Z相关项及下面L项。
- 主线：复核两份独立判断，整合问题优先级及修复决定，向用户报告；审查者不能代主线宣布效果验收通过。

前置目录：../catalog.md；约束：../boundaries.md；原生证据与审查来源：../../run-audit/{github,sheet}/report.md及coverage.md。
先前结论 findings.md 和 observer-followup.md 可作定位线索，不能代替证据。

## 新增表现—问题—修复目录

| ID | 表现／需求 | 待审根因主张 | 已改内容与入口 |
| --- | --- | --- | --- |
| L01 | 同父恢复曾清空子任务索引，补丁又阻断正常startup→new_session | 同home不等于同父；旧成果可见性与执行所有权需区分 | variants/pi-braid*/extensions/factory-subagent-observer.ts：按父历史保留/恢复、同工作区发现，未接管历史任务 |
| L02 | Sheet349 PBB返回后评论writer失效，Agent改DB绕过 | 有限后台任务未计入终态边界，结果迟到触发原生续轮 | harness/npm/patches/pi-background-bash-1.0.5.patch：有限job等待/完成消息；service退出只留消息不独立触发续轮。证据../../cells/writer-followup.md |
| L03 | 跨会话取原文手工找路径、分页截断补读成本 | 原生身份与原文定位、续读不顺手；不能推论跨链分析已自动完成 | lab/__main__.py evidence --session、原行号/UTF-8连续分页；../../cells/audit-analytics.md |
| M01 | 前后端重叠规则分歧，只有孤立检查；用户要求恢复文档系统 | 共享语义缺稳定发现/传播方式只是候选因素，不能假定有文档就正确 | sources/svc/skills/svc-documentation独立skill；task-packet互链；两活动variant打包/主会话/角色技能启用 |
| M02 | 检查边界原则缺直观组织 | 快反馈与产品证据需互补，层数和比例不应变成义务 | svc-verification/references/evidence-design.md检查金字塔，沿用保存设置案例 |
| M03 | 调查、设计、委派、packet原则抽象 | 缺可消费案例是表达问题，不自动等于旧运行根因 | ../../cells/svc-method-views.md列七技能取舍；正文案例、流程图和表格 |
| M04 | packet有计划结构，但制定计划方法分散偏薄 | 制定执行路线与保存计划是不同职责 | svc-implementation/references/planning.md；旧workflow迁移，skill元数据/入口；task-packet导航/模板提示 |
| M05 | 审查成本高、终态回溯可能漏掉过程损耗 | 覆盖与因果不同，重复渲染/读回与层次分工可改 | 当时的运行分析说明（已删除）：结果与全过程两路径，局部Luna、跨链Sol/Astra；单一覆盖账本与来源 |

## 判断与交付

每项重要结论给出具体表现、上游原因、竞争解释/反证、修复为何覆盖或不覆盖原因、可行的更简单方案、对应源码/原文位置、下一步最小判别证据。
区分确证缺陷、合理但未验假设、用户明确选择、根因尚不明；不把全部改动硬说成已证失分根因。
从产品义务出发检查修复归属及依赖方向；注意是否只是更多提示词、过度状态机/兼容路径、或把不必要要求实现得更复杂。
不以代码阅读宣称运行缺陷或收益已验证，阅读用于审查已提出机制与边界。
报告仅列决策所需内容及证据入口，覆盖表简短标明哪些项实核、哪些复用以及局限。
高影响确定发现即时回传；完成时必须通知主线。无需为认真而逐字重读已经覆盖的所有原生会话。

## 全范围补审后的修复消费

用户已授权继续修复。FR1已改为被动消息；FR2按冻结merge祖先正证结算、C1根定位/归档共享历史父读取均进入实现。原生架构审计进一步要求有限执行与必要通知同属一次调用完成边界，异常不能伪装成功；详见../../cells/lifecycle-architecture/report.md及其implementation.md。
这些是同一迭代的后续消费，不能用此前快照“无漂移”覆盖新改动。新增材料需编译/接口核对及有界独立复核，真实效果仍由后续授权生成观察。实验暂停。

## 本批增量已消费

FR2、C1、原生边界实现已完成，分别见 fr2-followup.md、c1-followup.md、native-boundary-followup.md。独立复核新增的未发布head条件、取消续采、已接受结果残留误判均已修正。Braid cargo check --locked通过；补丁应用/语法检查通过。上述结论限于本批源码和接线，真实行为未验；冻结包未更新，实验仍暂停。
