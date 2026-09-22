# 本轮主线与待收敛问题

目标是可正式打包、可无人值守取得官方评分的 Pi multi-agent 实验闭环。模型、角色与 V&V 为实验能力；自动化与恢复负责及时可靠地产生证据。本文是产品范围整理，不是已经获批的 LLD 或实施计划。

```text
官方参赛闭环与 Pi multi-agent 实验
├── 1. 官方运行契约与可复现 ZIP
│   ├── 核对 Competition 入口、官方 runner、模型注入、网络与部署
│   ├── 每个 variant 冻结模型、profiles、SVC 材料并产出 Agent ZIP
│   └── Lite 完整评分作为本轮起点；Web 为同一入口适配的扩展范围
├── 2. 清晰的 Agent 能力与模型装配
│   ├── Braid：从 work-item 的目标、验收和上下文边界推导分工；不先定岗位
│   ├── Pi sub-agents：explorer / executor；browser-operator 与 vision 均用 DS V4 Vision
│   ├── 深度专项建议可选 Kimi K3；常规路径采用快速模型
│   └── 每个角色显式 model / reasoning / skills / tools / MCP / context
├── 3. 可解释的实验组合
│   ├── 两个 generalist 从活动配置删除；保存历史基线与复现身份
│   ├── pi-team：共享的 multi-agent 团队
│   ├── pi-verification：同一团队与模型配方 + 明确的 V&V 增量
│   └── 快速模型配方 × team / team+V&V；具体数量按假设决定
├── 4. SVC 方法与接线
│   ├── V&V 方法归 SVC Corpus，Factory 只选择与接入
│   ├── 有使用时机的能力索引，按需加载；突出 task packet 与 V&V
│   └── 处理无人中途介入的授权边界，不复制相互竞争的方法正文
└── 5. 自动实验与诊断
    ├── 官方 API 驱动上传、启动、排队、终态、日志/应用下载
    ├── 官网与本地官方 runner 混合调度，复用镜像与依赖
    ├── Pi Adapter/扩展/RPC 故障分层定位，先复现再决定修改归属
    ├── 保留检查点、避免整轮重复生成；辅助诊断不阻断交付
    └── 汇总通过率 / 官方得分 / 成本 / 阶段耗时 / 设施失败
```

V&V 方法归 SVC Corpus；核对当前 main 后，没有发现需要本轮修改 canonical 正文的具体缺口。本轮只改善 SVC 接线：user-scope AGENTS.md/user instructions 应说明主要内容、使用时机和最短读取入口，突出 task packet 与 V&V，避免两行空导航和强制全量预读两个极端。Braid 不感知 variant/preset；Issue/PR、comment 协作和 Agent 对任务拆分的决策权保持不变。

## 2026-09-22 核对结果

参赛资料是事实来源，不授予提交、联系主办方或修改源码的权限。

- PDF `/Users/lanzhijiang/Downloads/参赛须.pdf` 共四页。初赛 9.24–9.30，每次正式提交运行两个任务；正式测试细节不公开，使用平台 key，单任务最多 48 小时。同队只能运行一份正式评测，个人 key 的练习提交也占用队伍资源。允许下载应用与 Agent 日志。参考图用于布局理解，文字需求/场景为功能依据。排名同时计算综合通过率与费用：b0=1.2，奖励指数0.1，惩罚指数0.2。
- [官方 Lite 页面](https://arc-bench.com/competitions/arc-bench-lite) 实际显示 Keep32/BookStack34，同一 submission 完成两题才有综合分；保存快照后选择任务运行；页面提供 Base URL、API Key、Model、Visual Model。默认视觉 ID 为 `deepseek-v4-flash-vision-exp`。公开 Lite/Web 与九月初赛不是同一赛事身份，不能混称成绩；它们的并发规则仍须分别核实。
- [官方模拟环境](https://github.com/code-philia/hackathon-local-simulation) 要求 ZIP 根目录 `main.py`、`requirements.txt`；入口 `python3 main.py <requirements_dir> --output-dir <output_dir>`。提供 OPENAI 与 VISUAL 两组模型环境变量。其 runner 可复现安装、生成、部署、评测，但不模拟网站队列。README 的镜像下载示例含占位地址，镜像可取得性仍需核验。
- [Meter 模型目录](https://meter.arc-bench.com/user) 显示：GLM5.3 Flash 输入/输出0.8/2.8元每百万token；DeepSeek V4 Flash为3/9；视觉实验模型1/4；Kimi K3为20/100。未见 `qwen-3.8-flash`，可见 `qwen3.6-flash`、`qwen3.8-max` 等，不能静默替换。DeepSeek的1M窗口及网关实际协议/速度留给定向spike验证，不能用名称或静态声明证明。
- Braid `src/config.rs` 的 Profile 有 display_name/tags/user_instructions，没有 description。Factory 配置也没有 description。计划补齐注册、CLI发现及协调者可见的职责说明，赋予 LLM 指派依据，不增加自动路由规则。
- 当前 `harness/subagents/*.json` 已配置模型：explorer/browser-operator/reviewer 为 Kimi K3，executor-code/verification 为 Kimi K2.7 Code，executor-ui 为 GLM5.3 Flash，reasoning均为high；`scripts/native_profiles.py` 会生成原生角色配置。此前缺少完整的人类复核表，静态配置也不证明实际使用。

## 设计建议与依赖

撤回 application-engineer 作为既定边界。agent-profile是Harness内部可复用能力配置，work-item才持有一次具体工作的目标、验收和协作上下文；同一配置可以支持多个独立work-item，从而形成多个Braid Agent。运行时Agent不知道profile，只看到GitHub式assignee，并结合投影出的成员能力说明决定指派。下一步从完整用户能力的设计、实现、验收和整合场景推导是否需要专门内部配置，避免把coordinator/engineer强制设成长期岗位。Issue/PR的设计与实现分离也不自动要求不同配置。

preset目前只是一对一转抄profiles/defaults的空壳，本轮不再保留这一层。variant直接引用内部profiles、默认assignee与方法装配；实验差异以实际模型、方法和能力为准，Braid仍不接收variant语义。

vision 是接收需求参考图或浏览器截图的原生 sub-agent，返回附带源路径的观察和疑点；browser-operator 同样使用 deepseek-v4-flash-vision-exp，直接结合截图与 DOM 完成页面旅程，避免每次观察再转发给另一个 vision Agent。两者是否使用不同权限/指令由实际场景决定。不能假设只写 model 字段就传递了图像。文字模型不应被动接收不支持的 image block。视觉结果为事实材料，不承担需求语义权威。

快速配方先考虑 GLM与DeepSeek组合，以及DeepSeek为主；Qwen只考虑用户指定的3.8 Flash（若确实可调用），不以Max替代。Kimi专项咨询可选，是否调用由Agent决定而非harness启发式升级。V&V方法统一归SVC，基础组仍有必要自检；增强组差异须落到所选SVC材料及其实际行为，不再另写一份Factory V&V方法论。

SVC导航可按当前权威入口组织：非简单任务建立/恢复状态时读取 task-packet/；探索、设计与实施方法读取 methods/；有界委派读取 sub-agents/；设计验收依据、选择证据及判断完成读取 verification/；维护长期项目事实读取 specs/；设计取舍需要进一步判断时读取 taste/。导航给出关键行为和触发条件，具体方法正文由Corpus持有。无人比赛环境不自动等待人类，但保留原始需求与授权边界。

Pi可靠性调查先复用已保存失败trace。区分Pi原生RPC、pi-subagents扩展、自有lifecycle扩展及Braid Adapter。用相同最小输入分别在原生RPC、加扩展、经Braid三层观察，针对可疑停止/重建/失败行为验证资源与状态由谁持有。上一轮修复数量并不能证明RPC有缺陷，也不能证明当前Adapter已正确。若原生层可完成而经Braid失败，先修接缝；若原生最小场景也失败，才形成上游协议/实现问题证据。此为调查路线，尚未作技术方案裁决。

自动化按官网实际容量安排队列，本地使用官方runner承接独立实验；两处使用同一冻结ZIP并记录运行环境与资源。线上评分和本地练习评分保留来源，不能合成为一份正式提交成绩。在线实验要求同一ZIP完成正常入口交付；人工导出仅是诊断证据。并发费用归因要特别验证：官方本地脚本使用key前后差值，如果多个任务共用key并行会互相污染，不能把该差值当逐variant成本。正式结果按平台提供的聚合粒度返回，不依赖隐藏测试细节构建调试流程。

推进顺序：核实官方/模型边界 → 复核团队、配方与V&V差异 → HLD/LLD和验收方案 → 分Cell实施计划及独立接口spike/预演 → 明确impact handshake → 实现前提交 → 纵向接通一个实际ZIP → 自动完成已批准矩阵 → 汇报停止。不会把所有新能力攒到正式大批次才第一次验证。
