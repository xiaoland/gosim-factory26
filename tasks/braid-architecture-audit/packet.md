# Braid 架构与协作审查

状态：技术审查与第二轮产品需求审查均已交付。只读检查 Braid 实现与已有运行证据；本任务只编辑本目录，不修改实现，不提交，不启动模型或官网实验。

目标是判断 Braid 是否让 LLM 通过 Issue、PR 和 comment 自主分工并维护工作项 Context，以及哪些运行缺陷、职责越界或重复机制妨碍这一目标。语义与完成决定属于 LLM；assignee 表示责任，执行容量独立；Pi 原生子代理归 Pi；Braid 不直接依赖 benchmark 或 SVC。

授权依据为本次独立审查委派。当前源码包含未提交的 Context reset 与 Local 完成判定改动；这些改动作为待审查事实，不回撤，也不默认认可。

本包分为 [审查路径与证据](evidence.md)、[系统拓扑与时序](architecture.md) 和 [排序结论](findings.md)。运行权威输入为 `runs/e20260928-completed-replay/{github,sheet}/source-workspace.zip`，规范入口为 `sources/braid/docs/20-product-tdd/local.md`。已有调查参考 `tasks/acceptance-integrity/cells/terminal-contact-loop.md` 与 `context-reset-handoff.md`。

已完成正常投递、关闭后唤醒、Context reset、Git 合并与恢复边界的控制流核对，并直接读取两份来源 ZIP 的 SQLite、实际 turn 输入与 Pi JSONL。

按影响排序的主要结论：unknown 重放使同一事件仍绑定已消费批次，产生 236/441 个没有输入事件的 terminal_contact；当前冷恢复要求新进程持有旧句柄而必然阻塞；Pi 专属通知收据成为共享 reset 门槛，Codex 无对应实现。前一项有真实运行证据，后二项为当前源码确定路径，未冒称完成真实恢复验收。

前一轮收尾时主线暂未改生命周期；后续用户已授权前三项技术缺陷与三类精简另行实施，主线现已报告完成 cargo check 与 Linux build，WSL 验收等待产品复核后再启动。本任务未重跑这些检查。旧报告按其指明的基线阅读，不能把它当作当前源码缺陷清单。

本轮新增 [产品需求审查](product-review.md)、[产品拓扑与时序](product-model.md) 及 [产品运行证据](product-evidence.json)，检查需求→机制→成本/故障的因果链。两份归档分别有 40/39 次已应用 reset 的 Context 仅严格追加；普通回复实际形成 9/6 个投递目标，但包含 queued/unreachable，不能等同于已执行轮次。报告分别列出实现纠偏、需要选择的通知范围/finalization/交付范围，以及后续真实验收的证据。用户明确要求的根五分钟检查、方法层的需求设计与实现分离、PR 交付均保留。

读取时间与源码哈希独立保存在 [产品审查基线](product-baseline.json)。本轮已停止扩展调查，其余低优先级风险保留证据边界；只整理需求判断，不扩展或回退其它工作者的实施。
