# 具体成员身份与指派

2026-09-25 用户明确：不同工作会话是不同的 Agent／assignee，profile 只是派生配置。
当前处于调查与方案讨论；没有本项源码修改、提交或新实验授权。
本页保留证据与产品方向；当前技术选择和复核状态见[协作技术方案](../braid-collaboration/design.md)与其 packet。

## 证据与问题

`sources/braid/src/objects.rs::item` 从 `desired_profile_id` 查询 profile 的 `assignee_login`，`assignee_directory` 也直接列出 profiles；`profile_for_login` 又将公开 login 解析回 profile。
因此同一 profile 下独立创建的工作项 Agent 在 Issue/PR 中显示成同一个人。
`read_comments` 则将实际 `agent_id`（存于 writer_group）直接作为作者 login，评论和负责人不采用同一身份。
`src/group/provider.rs::local_instructions` 注入静态 profile 成员目录，但没有当前具体 Agent 的公开身份。
Issue driver 还用 profile.assignee_login 判断指派归属，因此不能只给输出加后缀而保持解析、调度不变。

[GitHub 1/100 的原始分析](../issue-decomposition/results/7207a7fe0845.md)记录根会话将 Issue #2 assign 给 glm，同时宣称由自己实现；实际独立会话也在实现。
这支持身份歧义是重复工作的一个解释，不能证明修正身份就能消除所有冲突或解释全部失败。
过去 [assignee 投影方案](../iteration-throughput/assignee-projection.md)将一个 profile 投影成一个人，这项产品前提现已被用户修正。

## 用户修正后的产品方向

用户明确只保留“指派工作”，不增加创建成员的操作。
assign 选择 agent profile，并在操作完成时返回派生的具体 Agent 名字；提示文本应明确配置与具体成员的区别。
用户认可工具结果、当前身份和协作对象统一表达实际成员，并明确避免向 LLM 暴露 UUID。
这次回复是产品方向修正，不是源码开工授权。

配置目录列出配置名及能力说明，不把配置名写成 @成员。
当前成员目录和 Issue/PR 的 assignee 则使用派生后具体 Agent 的名字。
例如根 Issue 的负责人为 @glm-1，新建 Issue #2 时使用 `--assignee glm`，返回“已使用配置 glm 为 Issue #2 指派独立 Agent @glm-2”。
指引简短说明：“指派时选择能力配置；每个独立工作会话有自己的成员名，指派结果返回该名字，后续用它识别负责人和发言者。”
该文案及名字格式为方案示例，技术设计需覆盖根 Issue 初始化、Issue/PR 创建和重新指派的同一入口。

负责人、当前会话身份、评论作者、reaction 和通知中的成员引用采用同一公开名字。
各 Agent 的稳定指引包含“你是 @glm-2，当前处理 Issue #2”，工具返回实际指派结果，不让模型从配置名推测自己或同事的身份。
对同一工作项重复选择当前配置时建议保持现有指派并返回同一个名字；新工作项使用同一配置则产生不同成员，不能暗中共用身份。
上下文重建与原生进程恢复建议沿用逻辑 Agent 身份；真正重新指派而创建独立协作者时产生新身份。
上述生命周期细节仍需在技术设计中与既有 agent_instances → provider_sessions、assignment 关系一起核实。
assign 返回不应等待模型执行结束，也不应将“已指派”描述为“已开始运行”或“工作已完成”。

Braid 交给 Agent 的身份字段、文本/JSON、上下文、通知和错误使用可读成员名及 Issue/PR/comment 编号，不暴露内部 UUID，也不以截短 UUID 充当名字。
底层诊断保留真实 ID 与公开名字的映射，避免损害原始证据；这不是对应用内容或工具原始输出执行全局脱敏。

验收应观察实际运行中的配置选择、返回成员、独立会话、评论署名与根会话判断是否一致，而不以 Issue 数量或命令是否成功代替行为证据。
当前不启动实验，后续实施准备仍需计划、适用的独立预演和明确开工复核。
