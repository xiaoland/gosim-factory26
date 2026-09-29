# 此前 sub-agent 返回的消费核对

2026-09-29，用户要求重点核对此前委派者，而非仅检查最终两份汇总报告。
本次从当前代理返回、GitHub/Sheet主审最终报告、输入审计独立发现及其最终降级判断、原生架构与后续报告回查关键建议；没有重读全部原生运行，也不把早期独立快照当最终结论。

| 返回来源 | 具体要求／结论 | 当前消费 |
| --- | --- | --- |
| GitHub全链主审 report.md | 前置执行成功后再启动依赖；保留首轮真实退出结果；临时资源归属；写入受理/不明先读回 | svc-implementation/workflow与检查工具已落实四项；原/派生权威等纳入最终方法取舍 |
| Sheet全链主审 report.md | 用途迁移、重叠规则、跨表缓存不变量；同条件复用；BodyArgs文件/stdin帮助；HF示例纠正 | R06/SVC方法、helper与CLI已有对应改动；pivot静态缺口作下轮方法效果观察，不改冻结应用 |
| 输入审计 report.md/packet.md | fresh角色共同条件缺失、两位根关闭主语、重复后台说明 | RUN_CONDITIONS及成员指令已修；保持fresh，不加多余继承 |
| 输入审计独立发现2/3，最终报告第2节 | completionGuard关闭后，原生acceptance仍可能把只读返回套成实现/reviewer要求 | 原审计已证明review-required不阻断完成，明确暂不改原生分类；此前最终取舍漏记。补入非阻断观察，检查真实返回是否诱发父追加无意义工作，不新建reviewer |
| 原生生命周期架构与增量复核 | 执行排空不等于通知排空；agent_end异常、取消被续轮覆盖、残留文件假失败、队列退出前丢失 | 锁定原生补丁及Braid投影已修；保留历史/service被动边界，真实时序仍待证 |
| analytics_executor及native_boundary_review | 记录补读越界、工具调用配对、负offset及UTF-8尾边界 | 已实现与回读；缺失链保持missing，不重做全量分析 |
| final_product_methods与假阳性报告 | 修正过宽归因；packet单一权威；保留必要契约修复、降级观察项 | decisions.md及五份成员指令已消费 |
| native_boundary_review | 协作者失败事实、Node入口；检查并清理无效status_surfaces路径 | 查询式事实与Node入口已修；status_surfaces字段、三处不可达通知函数/分支及调用已删除，保留压力/错误记录及仍有消费者的通用运行状态函数；Braid 1fabd11，cargo check通过 |
| collaborator_failure_facts | 完成查询投影、原错保存、恢复后旧故障消除 | 已纳入Braid 034372a；cargo check通过，真实SQL/CLI恢复链未动态验证 |

## 剩余项目

1. status_surfaces清理已完成，调用者核对及cargo check通过；未新增广播、未改变查询式失败事实，无测试或实验。
2. acceptance/review-required保留观察：只读结果是否被父当成未实现、是否凭空要求不存在的reviewer。已有guard修复不等于该语义已消失；现无阻断或额外工作证据，不为ledger字段新增机制。
3. 完成后的实际采用、时序与收益仍待新包和授权运行。旧监控代理的2026-09-27状态仅是历史快照，不作为当前待监控任务。
