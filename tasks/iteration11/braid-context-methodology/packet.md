# Braid上下文与协作内容方法：GitHub lineage / 两题综合

2026-09-30。当前阶段：诊断与一般方法草案完成，交父会话与独立规划会话。用户从I11局部方法分析扩大到完整I10→I11 lineage；接续/版本节点只作待检验因素。GitHub由本会话负责，Sheet由父会话的独立会话负责，综合只消费其同维度报告，未重读其全部记录。

授权原话：“从头分析两题完整I10→I11 lineage，不受迭代编号边界限制，包含所有相关Pi sessions、Issue、PR、description/relationship/comment及hide/resolve/状态演变，重建信息与决策流。”另要求对照人类写作、沟通、项目协作、软件工程及少量一手研究，不以术语包装推断。仅分析和本目录报告，不改源码或原work items，不跑模型、测试或评测。

分工：braid_content_lifecycle建立GitHub时间/对象/来源覆盖与缺口，braid_context_semantics核实历史指令与运行上下文真实语义，braid_method_research整理少量权威一手参照；主线负责补原始末段、独立回读、因果串联和协议草案。已有局部报告 tasks/pi-minimal/github-score-analysis/i11-mechanisms-forward.md 保留为已读证据入口，不代替完整历史。

身份：直接lineage为 inner 20260929-042409-1202e245，起点 e20260928-03-check-receipts / pi-braid--hackathon--github-7fe42a1248f9d8，后来刷新I11材料继续到 pi-braid-i11--hackathon--github-0d0cb6e9982fc1，最终官网重放e68661975b53。iteration10/run-audit/github另属更早inner 20260928-030347-78b10c07，作为比较前史，不混成同一次运行。

末段来源核实并已下载：replay-manifest中 final run_path 在远端 runtime-stalls/github/generation，标签 retained_generation 指 completed-turn-resume/github/...5c52a331ef0d5c/workspace/official-generation。保留目录的native/context与终态braid-state/braid.sqlite3已选择性归档至 runs/analysis/braid-context-methodology/github-final-20260930/；2324文件manifest hash均匹配，result=quiescent、全部work items完成，delivery commit 442dc1cf776f144688d8ad667a76dd026f553e27。未覆盖既有原件或执行下载内容。最终run自己仅留published应用，不把它误当原生资料丢失。

交付入口：[report.md](report.md)；完整时间/来源/跳过类别：[coverage.md](coverage.md)；分线报告 middle-content-evidence.md、continuation-flow.md、final-pr23-flow.md、主线final-root-flow.md；历史语义 runtime-semantics.md、一手研究 research.md。原生22152条唯一记录为结构索引，绝不声称所有字段全读；按用户认可口径复用早期审查、回读全部相关状态信息流和关键长段。

最新范围分工：requirements树→Issue具体映射由thread 01a0f102-bc06-76b7-8cd2-8f75d952704a、tasks/iteration11/requirements-tree-collaboration-plan/负责。本报告的一般内容/生命周期协议仅作该规划输入，不重复展开实现设计。所有候选未实施，不授权评测/模型试跑/源码改动。

2026-09-30追加授权：用户要求对范围排除未承接、最终覆盖代理、在途hash维护循环进一步向上游找原因，并先交可核查的维护活动记录。当前阶段重新进入有界增量取证；新增 `maintenance-activity-timeline.md` 与 `root-causes-deepening.md`，旧结论不无标记覆盖。三条有界分线分别核责任输入、验收输入和维护运行语义，主线独立重读关键原文并串联工具动作/DB活动/触发输入。仍只读原件，仅保存报告/摘录；不测试、评测、模型试跑或修改runtime/variant/workitems。

追加任务已完成：[维护活动时间线](maintenance-activity-timeline.md)已先回父会话；[三条根因深化](root-causes-deepening.md)为本轮主交付，配套 `deepening-responsibility-notes.md`、`deepening-acceptance-notes.md`、`deepening-maintenance-mechanism-notes.md`。具体修正：11:54–12:01五次edit在同一native session/Braid turn内累计notice，随后一次reset续接，不是每次edit立即新开session；PR23 packet排序晚于L48放弃重推mapping，属于固化因素。责任链向前补到初始M5交付/设计的对象收窄，再到M6已知缺口的排除与咨询输入筛选。已保存有界provider/DB摘录 `evidence/deepening-maintenance-records.json`，无新取证阻塞。下一步由用户/父会话复核并转独立规划，不实施候选。
