开始或接续 Braid 工作时，读取独立技能 braid-collaboration；按当前问题读取适用 reference。同一会话中已读取的方法按需回看。技能与 SVC 方法保持独立文件，不内联到工作项或原生委派提示词。

当前工作项的 description 或讨论需要整理时，按需调用 braid_cleaner。它自行继承当前有效历史并读取完整对象快照；你只触发，不先写逐条改写、hide 或 resolve 计划。检查回执；过时、失败或取消的结果没有自动应用，不自动重试。它只维护当前负责项，不承担代码实施或验收责任。

SVC 文档系统与 task packet 是本配方的强制要求。非简单工作开始或接续时，先读取独立技能 svc-documentation、svc-task-packet，取得并启用适用的项目知识与当前 task packet，再推进工作。材料归属、发布与采用按 braid-collaboration 和两项 SVC 技能处理；技能方法保持独立文件。

实施前核实会改变路线的版本、API、共享接口和环境前提，用小规模真实操作消除关键未知；根据反馈修订方案。

将有歧义的需求解释发布为共同前提、确定影响多个任务的共享契约，或确定仍有关键假设的验收判据之前，先向原生 advisor 咨询；反复失败或新证据动摇方案时再次咨询。这些时机已由本配方选定，不以委派是否比自己省时或是否已通过自检来决定使用；日常明确的局部决定直接推进。

本配方由根 Issue 直接负责共享架构、脚手架与开发反馈设施的设计和交付，创建直接关联根 Issue 的基础 PR 并指派独立负责人实施；不把整套基础责任转为子 Issue，也不在 Issue 工作区先完成应用实现。

共享成果持续整合到 develop，最终交付分支为 main。根负责人开始协作时，fetch origin，若还没有 develop，从 origin/main 创建并发布它，不覆盖已有分支。Issue 的初始个人工作区不一定包含最新共享实现，按需要 fetch 并查看 origin/develop。子任务 PR 使用 --base develop；需要承接已有代码时先发布相应分支，再用 --head 指定它，而不是从空白重复实现。

根 Issue 最后组织关联的 develop → main 整合 PR（braid pr create --base main --head develop ...），由其负责人在最终候选上执行覆盖完整需求范围的自动化测试或脚本，修复失败并复验，再合并交付并交接结果。合并时用 --match-head-commit 保护确认的已发布候选。

检查设计、首次执行与结果解释时读取 svc-verification。执行工具未完整保存原始输出和真实退出值时，读取 agent-browser 技能并使用其检查命令包装，API、构建和自带服务的检查同样适用。浏览器探索默认使用 e2e MCP，先读取独立 e2e 技能，也可委派 browser-operator；agent-browser 保留用于诊断或已确认的 e2e 能力缺口。

需求参考图的视觉解读交给原生 vision sub-agent；相关图可在同一项委派中提供，主模型是否支持图像不改变这项分工。

需要原生委派时读取 svc-sub-agents，按原生目录中的职责选择角色。braid 指派列表中的成员名不是 subagent 的角色名。保留原生任务 ID；恢复后先查询对应状态和已保存产物。

本reviewer实验采用专门验收成员。验收Issue收到pr request-review后，从braid assignee list --reviewer选择当前具体成员并用pr review assign委派请求。Issue负责人组织验收范围、处理讨论和整合决定；代码与浏览器结论由该请求的独立reviewer提交。源PR实施者持续推进修复，不以Issue自行验收替代此实验因素。
