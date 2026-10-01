# I11 来源报告消费核对

当前运行核验已转入 [恢复根治与行为验证](runtime-stalls/packet.md)。本文保留问题与实施账本；源码完成/旧“未部署”截点不代表当前效果。两题实证矩阵见 [GitHub](runtime-stalls/github.md)、[Sheet](runtime-stalls/sheet.md)。

2026-09-29。对照用户共享契约/进度保留等报告、GitHub与Sheet两份run-audit/report.md、01–10实施cell、CLI实施记录及当前源码。不是新一轮全量运行分析，不将源码完成写成行为通过。

## 已有明确源码落点

| 来源/问题 | 落点 | 状态 |
| --- | --- | --- |
| 用户共享契约变更，Sheet §1 | I11-01；svc-documentation + implementation planning/workflow | 已改，未部署；纠正“无Git契约”，实际为权威分散/消费滞后 |
| Sheet §2 profile误当两个人 | I11-02；指派目录/help/回执 | 已改，未证明排期改善；真实依赖等待不删除 |
| GitHub §2 重建挡评论 | I11-03；worker/store领取及精确ack | 已改，未运行验证 |
| Sheet §3 重建原因不清/分页 | I11-04；重建来源与timeline分页 | 已改，未证明减少重复推理 |
| GitHub §1 有限后台工作与turn脱节 | I11-05；RPC等待、终态落盘、旧globalJobId读取、Pi真实入口、runtime缓存目标 | 已改且接线完成，未真实时序验证；一次subagent_wait无登记的唯一原因仍缺证 |
| Sheet §4 指定评论折叠 | I11-06；直接读取resolved正文 | 已改；thread历史仍折叠 |
| GitHub §3/Sheet §6.4 失败丢失与过强解释 | I11-07；完整日志/退出值入口、with-service结果、SVC解释 | 已改，未证明采用 |
| Sheet §6.1 猜评测改变默认值 | I11-08；产品/检查/环境/猜测的修复对象判断 | 已改；不硬编码Sheet尺寸 |
| GitHub §4/Sheet §6.2 无必要复验 | I11-09及06方法部分；diff/运行条件/证据适用性/停止条件 | 已改，未证明停止循环 |
| Sheet §6.3 长正文误覆盖 | I11-10；文件准备与全量替换帮助 | 已改；-F本身有效，不编造参数缺陷 |
| 用户CLI复核 | CLI-01～05；实现、help、宿主telemetry调用 | 已改、编译和只读操作通过；未部署 |

## 补充项及处理结果

### R1 时间线序号与评论编号仍混淆：明确剩余界面缺口

GitHub报告“其他观察”6记载将timeline #89误当comment ID，实际目标comment #32。
当前objects.timeline返回独立ordinal和comment字段；cli.print_timeline文本仍打印“#ordinal”，未呈现comment字段/直接读取入口。
已修分页不等于已修这处身份歧义。归I11-04/CLI可读性补项，不另扩展协作机制。
已应用：文本明确“活动序号”，有来源评论时另列comment编号及读取命令；JSON保留两个独立字段。编译与真实归档副本只读查询通过，见cells/r1-timeline-identity.md。

### R2 vision结果length截断：已定位并修复

冻结父会话报告Background task completed: vision，子会话最后assistant实际stopReason=length。原生pi-subagents共享detectSubagentError只查toolResult错误，前后台共同漏报。
已修原生共享utils.ts：最后assistant为length时保留部分文本、明确不完整，并沿既有错误返回；不自动重跑、不更换模型。仅看最后assistant，历史截断后成功续完不误报。runtime目标指纹接线完成，完整补丁顺序应用与语法编译通过。
observer的partial是关联证据完整性，不是任务结果状态，因此不挪用、不新增状态。见cells/r2-truncated-result.md。源码闭合，未部署/行为验收。

### R3 重复无动作确认：方法已有改动，通知/决策覆盖仍不充分

Sheet §4及19:42增量存在已完成成员反复哈希确认。现有06/09改动主要在“证据已满足后停止复验/交接”，没有独立证据证明覆盖“收到与职责无关通知后反复读取、回复”的完整路径。
不据此关闭所有已合入成员订阅，也不把有价值的shared静态门反馈删除。
已核通知收件人与显式退订：没有把样本定性为同事件重复投递的依据，不增去重状态机。两处通知入口改为先读单条、按需展开thread；两份I11角色替换原回执句，明确无相关变化/待办即可结束，不复核相同哈希。见cells/r3-notification-work.md，源码与编译闭合，行为收益待未来运行。整理I10副本不冒充未来行为修复。

## 不是默认追加源码的观察

- Node20/24与浏览器版本：I11 run.py已有明确应用Node入口、工具/应用版本区分，agent-browser已有BROWSER_EXECUTABLE_PATH指引。保留采用效果待验，不再仅加同义提示。
- GitHub34/47需求计数：47个ID有归属，不能据根计数错误宣告漏13项；接续整理纠正摘要，最终按ID核对。
- core文件：历史已清理，产生原因缺证；不能让Harness自动改应用或拒交付。
- Sheet旧DB/tsc问题：归07记录条件/原始错误与09证据适用性，不单开环境框架。
- SQLite锁/结果权限/根恢复属于I10已部署热修复；不混入两份报告的覆盖声明。
- 有效advisor/explorer反馈、SQLite位移预演和真实基线变化后的复验保留，不当作浪费删除。

## 操作性剩余

I10完整归档和独立整理副本正在准备；无已确认的错误扩散前一致历史checkpoint，现采用最新有效代码+人工整理上下文的接续起点，明确不是从零对照。
I11构建、冻结身份、部署及真实行为验收尚未执行；用户明确暂不启动。
