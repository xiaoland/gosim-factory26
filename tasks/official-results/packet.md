# 官网实验结果整理

状态：已盘点现有终态，持续接收双比赛矩阵的后续评分。当前只整理证据和提出下一轮方向，不改变冻结 ZIP、运行中的矩阵或评分流程。

目标：按远端 run ID 去重，把 Competition 的正式评分、仍在运行的任务和 Playground 诊断探针分开。用同一张可视化总览进入各 run 的原始现场，再根据逐例首阻断点提出可证伪的改进方向。完整结果另见 [报告](../../reports/2026-09-23-official-results.md)；逐例诊断沿用 [已有 cell](../iteration-throughput/cells/score-diagnosis.md)。

验收：每个已完成的官网 run 都能追溯到平台 `status.json` 与唯一远端 ID；未完成任务不计分；Playground 探针不进入 Competition 排名；分数只在同 benchmark、同任务口径下比较。新评分到达时更新报告，先汇报本次实验结果，再决定是否改 variant。运行控制由 [双比赛矩阵](../dual-bench-hosted/packet.md) 持有。

进度：2026-09-23 13:20（北京时间）确认 5 个 Competition/Lite 终态评分、2 个 Competition 运行中任务、3 个 Playground 诊断终态。`python3 -m unittest tests.test_run_viewer` 4 项通过，`python3 scripts/run_viewer.py` 生成 `runs/viewer/index.html`（24 个本地归档 run、0 条发现警告）。现有 viewer 的 Competition 分类只收入 Lite 六条记录，Web/12306 运行中记录在本报告单列；不把 viewer 总数当官方评分数。

当前分析 cell：用户要求从 Agent 运行过程追根因。五个已评分 Competition run 各由独立分析 Agent 阅读其运行轨迹、Braid 协作记录与产物，再以官网首阻断点反查需求理解、分工、实现和自验链。正向满分 run 用来寻找可迁移行为；失败 run 要区分真实生成缺陷、oracle 漏检、平台现场不足和测试合同争议。主 Agent 只做跨 run 综合，不将模型配方与分数相关性当因果；每项改进须写明其针对的运行机制和最小验证。运行中与准备中的任务不推测根因。

停止点：2026-09-23 用户要求证据不足时停止并列出缺口。已确认官网归档缺原生 Agent/Braid 会话，多数 run 缺评测时 DOM；网站只读 API 当前返回 HTTP 500。三条失败 run 和一条满分 run 的独立分析停在此边界，未再扩展到 GLM。可证的交付产物机制与必须补采的证据见 [process-evidence.md](process-evidence.md)。官网双比赛运行控制不受本分析停止影响。
