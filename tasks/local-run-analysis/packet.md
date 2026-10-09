# 本地实验的 Agent 过程分析

状态：十个已离线评分产物的身份与证据盘点完成，其中八个已交付 run 和两个未交付但可评分产物均经逐 run 诊断；结论见[本地过程报告](../../runs/reports/2026-09-23-local-agent-process.md)。不改 harness、SVC Corpus 或实验配置。

目标：利用本地 run 保存的原生会话、Braid 对象、生成产物与 Playwright 失败现场，解释已评分实验中的 Agent 工作机制和具体失分。先验证证据完整性，再给每个完整 run 一名独立分析者；跨 run 综合只使用可追溯的观察，不能从分数或最终源码倒推 Agent 决策。

范围：上一轮 `runs/batch-multi-agent-20260922-01` 与本轮 WSL `runs/local/iteration-throughput-boundary`。同名 variant 的重试分别列出 run 身份；本地公开测试与官网 Competition 分开，不用分差当环境或模型的单变量因果。

盘点另发现两份单独归档的旧应用虽有 8/34、8/32 离线分数，Braid 却未完成交付。报告按“10 个已评分产物、其中 8 个完成交付”列账，避免把 `run.json` 的 `generated/frozen` 当作交付成功。

验收：每条原因链能定位到需求输入、Agent 会话或 Braid 记录、自验行为、交付代码和失败现场中必要的节点；缺节点就标明假设。报告优先回答是否读到要求、如何分工、为何验收漏检、何时停止，以及相应的最小可检验改进。用户要求证据不足时停下，不为凑结论继续推测。

完成情况：独立分析者逐一审阅八个完整交付 run，以及 pi-verification/Keep、codex-generalist/BookStack 两份未交付产物。每个 run 都把原生会话、Braid 状态、生成身份和失败现场按同一身份核对；跨 run 只综合有实际共性的机制，不把同分或分差当单变量因果。历史评分证据与文档链接已核对。
