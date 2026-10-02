# 原生调用结束边界

状态：独立架构审计与已授权实现均已返回；不是运行验收。当前整体取舍由[最终修复审查](../../repair-review/final/packet.md)消费，实验与提交授权以[主packet](../../packet.md)为准。

## 问题、方案与证据

- [原故障链](../writer-followup.md)：有限后台工作未完成而调用先结束，迟到结果触发失效身份续轮。
- [产品与架构审计](report.md)：区分进程/会话存活、一次调用和业务完成；保持Braid/Pi分层。
- [当前实施记录](implementation.md)：Pi/子任务结果交付屏障、异常与取消、退出前队列持久化以及打包接线。
- [完整运行时产品审查](../../repair-review/final/product-runtime.md)、[假阳性核查](../../repair-review/final/review-false-positives.md)：判断方案及新增条件是否合理，不用旧局部通过背书整体。

实现者已完成锁定补丁应用核对、语法检查和Braid编译；没有新运行时序证据，冻结包未更新。本cell不再自发扩展修复链。
恢复实验后要观察有限结果接受、父后续处理与settled的顺序；没有自然覆盖的取消/异常继续标未证。历史/service只保存事实不承诺空闲时立即采样，Braid不管理原生子任务。

过去的审计/实施授权经过见[历史入口](../../history/20260929-lifecycle-packet.md)。
