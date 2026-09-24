# 独立 Variant：现状与设计草案

总体边界已获用户认可；本文保留问题与 HLD，不是当前实现说明。
具体迁移见 [技术方案](technical.md)，完成判据见 [验收方案](verification.md)，次序见 [实施计划](plan.md)。

## 问题与证据

实验对象的结构仍在探索，把所有 variant 放进一个共同配置模型，会把实验变成生成器允许的参数组合。
本次优先缩短“理解一个 variant、修改它、运行并解释结果”的路径，接受有意义的重复代码。

| 当前位置 | 已观察行为 | 对迁移的影响 |
| --- | --- | --- |
| `scripts/profiles.py:resolve` | 读取 variant、全局 profiles、subagents、models、skills，展开成 effective；还固定 Pi、CLI 列表和空 MCP 等约束。 | 差异先受统一 schema 限制，再传入执行层；仅移动 JSON 不能解除这一约束。 |
| `scripts/native_profiles.py:materialize` | 把 effective 再转成原生模板、角色文件、技能目录、launcher 和 Braid bindings。 | 理解实际 Agent 环境需要追踪两层投影。 |
| `scripts/factory.py:generate`、`braid_request` | 所有活动 variant 共用生成流程，并保留 single/Braid、Pi/Codex 和本地/参赛分支。 | 行为演化仍会落到公共运行函数。 |
| `scripts/package_agent.py:package` | 复制固定脚本集合、整个 `harness/`，生成 `variants/factory/config.json`。 | 当前包包含其他配置材料；打包器参与 Harness 语义装配。 |
| `scripts/arc_matrix.py:build` | 输入 `NAME=AGENT_ZIP`，把 ZIP 交给发布版 Runner 的 adapter。 | 已有不理解内部 profile 的实验入口，可以继续使用。 |
| `scripts/official_matrix.py:freeze` | 历史官网矩阵读取 ZIP 内部 effective profiles 来推导模型路由。 | 这是格式耦合点；先确认是否仍有新提交消费者，已有 journal 恢复不需要重建旧包。 |

raw-core 基线已有独立 `main.py` 打包路径，但仍通过 raw config 选择 backend/model。
它能提供入口和运行依赖复用的参考，不应直接推广成第二个统一 variant 生成器。

## 所有权建议

一个 variant 是一个普通的可执行目录。
它拥有自己的入口、指令、主 Agent 与 sub-agent 装配、工具和技能选择、Braid 调用及交付行为。
同样的文件可以起初复制为四份，以后各自演化；不要求派生关系、基类、插件注册或公共流程上的回调。

```text
variants/
├── pi-team-deepseek/    完整入口、运行代码、原生配置、指令和选用材料
├── pi-team-glm/         完整入口、运行代码、原生配置、指令和选用材料
├── pi-team-mixed/       完整入口、运行代码、原生配置、指令和选用材料
└── pi-team-vv/          完整入口、运行代码、原生配置、指令和选用材料

共同实验设施
├── 依赖构建与缓存、ZIP 封装
├── 官方 Runner 接入、并行运行、终态与恢复
└── 原始证据采集、结果分析与可视化

依赖来源
└── Pi / Codex、Braid、SVC skills、浏览器工具
```

目录内部只在责任实际需要时拆文件，不规定每个 variant 都必须实现相同类或模块树。
四份主入口不能只调用 `generate(variant_config)`，否则仍是原来的架构。

Pi、Codex 和 Braid 本身仍是可复用依赖，不复制其源码来证明独立。
Braid 保留其现有普通 profile/binding 接口，不感知 variant 或 preset。
角色模型、指令及能力直接由各 variant 表达为实际消费的原生配置；原生 API 必需的 JSON/TOML 和动态路径填充仍可存在。
要删除的是用一套 Factory DSL 生成所有 Harness 的关系，不是禁止配置文件。

SVC Corpus 继续有自己的内容权威，各 variant 决定选用哪些 skills 以及如何接入。
制品包含该次选用的具体材料与依赖身份，运行时不读取可变的外部 checkout。
其他 variant 的代码不随单个 variant 修改而改变；更新共同依赖必须作为显式的重新构建输入，不冒充完全相同的实验。
这不要求把所有技能正文变成四份各自维护的上游，也不在本任务更改 Corpus。

共同打包设施处理文件和运行依赖，不决定模型、角色、skill、工作项协作或生成流程。
共同实验设施消费 ZIP、输入、输出、退出状态和证据，不遍历 profile 推导 Agent 行为。
模型路由若为平台提交所必需，可以作为提交元数据显式提供，不再从内部能力树反推。
具体字段只保留现有消费者实际需要的内容，不在这里发明新 manifest 标准。

## 迁移边界与待核实项

建议先以当前 mixed 行为贯通一份独立实现，再迁移其余三份；每份完成后独立运行，之后才删除失去消费者的公共生成链。
这里仅迁移代码所有权，不同时改实验假设或修正既有模型表现。
官方格式入口、需求读取、应用交付和原始诊断材料需要连续；已有旧结果继续可以读取。

以下调查项已用于形成技术方案；消费者事实与无模型边界分别由独立 Agent 核实，不依据概念图直接开工：

1. 从 `factory.generate` 中划出 Harness 行为、交付边界和诊断导出；确定每个现有调用者如何迁移，开发 analysis 不能跟着误删。
2. 列出 run viewer、analysis、OTLP 和矩阵实际消费的字段；保留有消费者的证据，不重建大而全的配置快照协议。
3. 核实公共 runtime 缓存与单个 variant 的依赖选择如何接合；改变纯指令不应触发重新安装 Pi、浏览器或 Runner。
4. 确认历史官网 freeze 路径是否仍用于新实验，再决定最小适配；不为历史状态增加新的双格式运行分支。

## 拟议验收方向

在普通临时目录中移走其他 variant 和旧共享生成器后，单个目录仍可构建并通过官方包入口执行。
修改其中一个 variant 的指令或执行步骤，其他三个无需修改或重新生成；独立材料清单能说明哪些输入发生变化。
这类检查使用临时样例，不为 SVC Corpus 的篇目或措辞写测试。

固定输入下核对实际原生指令、模型、角色、技能选择和 Braid 协作接口，并保留真实运行的会话证据。
无模型 smoke 只证明入口与交付，不能代替真实协作验收；模型额度不足应报告缺口，不扩建模拟系统。
评分实验继续沿用既定方法，具体运行范围等待设施就绪及已有任务安排对齐，不因本设计自动启动。

当前工作区包含 SVC 接线、实验设施等多个未提交任务的改动。
实施前应明确各任务的基线和文件所有权，不整包提交、不回退他人的修改，也不把新任务完成等同于 SVC 任务关闭。
