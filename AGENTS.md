# Factory26 开发入口

本仓库由 Coding Agent 开发 Agent Harness，用户参与需求、方案和授权决策。
开发 Agent 与无人值守的参赛 Agent 是不同角色，项目共享说明不导入个人指南。

## 仓库地图

```text
variants/<name>/          每个团队 Harness 的独立实现
  main.py / run.py        标准入口、原生材料接线与生成流程
  agents/                Braid 成员与 Pi 内部角色的原生配置和指令
  build.py / extensions/ 材料选择与原生扩展
harness/                 共用技能材料与工具依赖声明
submission/              Linux 公共交付和资源构建
scripts/                 打包、运行支持与模型网关
lab/                     通用实验执行与 OTLP；ARC 接入；可选过程分析
sources/                 独立维护的 Braid/SVC 仓库，父仓库 Git 忽略
third_party/             外部评测器和历史依赖，Git 忽略
experiments/             实验配方与归档定义，不是 Harness 的全局配置
tasks/                   当前问题、设计、授权、计划与恢复点
reports/                 带条件和证据入口的历史结论
runs/                    原始运行产物，Git 忽略
```

| 要做什么 | 先读哪里 |
| --- | --- |
| 理解产品目标、协作模型和实验规则 | [PRD](docs/prd/index.md) |
| 修改 Harness、交付或实验接入边界 | [技术说明](docs/product-tdd/index.md)，再按 [CONTRIBUTING](CONTRIBUTING.md) 定位实现 |
| 准备工具、修改角色或技能 | [CONTRIBUTING](CONTRIBUTING.md) |
| 运行、诊断或恢复一次实验 | [运行说明](docs/deployment/index.md)，先辨别记录生产者 |
| 接续任务或找历史证据 | [文档与任务索引](docs/index.md)，状态以对应 packet 为准 |

## 协作与授权

非简单任务主动建立或接续 `tasks/<task>/packet.md`，保存当前问题、方案、授权、下一步与证据入口。
用户纠正改变方案时，更新当前设计及受影响计划，不靠追加声明覆盖仍然矛盾的正文。
调查、只读分析和 task packet 整理可以先行；已有历史授权不自动授权新任务。

推进顺序为：诊断与方案复核 → 验收方案复核 → 实施计划及适用的独立 Agent 预演 → 呈现具体影响、取得明确开工同意 → 实现与验收 → 汇报。
设计获批不替代开工确认；开工后持续完成已授权范围，仅在实质范围或前提变化、无法继续或需要用户决策时暂停。
沿用已批准且未变化的验收方案，不反复请求确认。
提交只按用户明确指令执行；获准实施前提交时，只纳入本任务改动，不把混合工作区整体提交。

先明确 HLD 中的职责、生命周期和跨组件约束，再核实 LLD 的实际接口与失败行为。
反复出现时序或边界补丁时，先重新确认问题和产品要求，再判断是否需要改变设计。
主 Agent 持有整体判断；有界委派给子 Agent 时只传必要增量、材料入口、文件与权限边界、返回要求和升级条件。
不要让 reviewer 单靠阅读同一实现充当独立验收。

## 工作知识与反馈

产品意图归 PRD，跨组件技术约定归技术说明，操作方法归开发/运行文档，当前调查和计划归 packet，局部实现理由靠近代码。
修改只更新实际受影响的内容，不复制字段表或建立空模板。
收尾先将持续有用的知识整合到其归属，报告和原始证据各自保留；确认剩余事项已转交后再整理任务入口。

不编写、维护或运行 Factory 自身及开发基础设施的测试，包括单元测试、模拟集成测试、observer 测试和包 smoke；SVC Corpus 也不设内容测试。
不将已删除测试换名为探针或自检重新引入。
官方 benchmark 与生成应用自身的验收保留，反馈来自实际操作、原始证据及获授权实验。

保留具体错误、HTTP 状态和可诊断的响应内容，再生成有界摘要；不要用泛化分类丢失原因。
脱敏、完整性校验和防重复措施必须针对具体风险，辅助证据缺失不自动等同交付失败；对外展示不暴露实际凭据。
原生 rollout 只用于明确问题的定向取证，不默认铺进主会话。

## 实验边界

改设施与跑模型是不同授权范围；实验的输入、矩阵和完成条件先记入对应 packet。
独立生成只依据允许需求，冻结应用后才执行外部评测，不读取或修改评测器来适配生成应用。
可修复的设施故障属于已授权实验闭环，不是有效零分，也不是已经取得结果。
完成既定 benchmark 后无论分数高低先汇报，由用户决定下一轮；遵守用户的停止要求。

长实验优先由程序记录终态并通过执行完成或获授权子 Agent 的完成消息返回，不频繁唤醒主 Agent 读取心跳。
实验监控使用 [run-monitor](agents/run-monitor.md) 的 `gpt-5.6-luna / low` 配置；工具会话的续等留在程序编排内，不每分钟回到模型调用 wait。
远端没有事件接口时，后台采集从三分钟间隔起步；token 增长不等于语义进展。
恢复、等待和不同记录格式的查询方法见运行说明，不把旧 watcher 当作所有 run 的统一入口。

## 开发侧 SVC

开发和 analysis 使用 `runtime.py dev-svc --svc-source <完整开发SVC源码>` 安装的 `.venv/bin/svc`；参赛 Agent 直接装载 `sources/svc` 提供的完整 skill，两者用途与来源不同。
需要文档归属或任务包方法时按需查询 `specs/`、`task-packet/`，不要预读全部 Corpus。
下面生成导航中的 `svc` 指开发侧 `.venv/bin/svc`，不是参赛 Agent 的工具。

<!-- svc:begin -->
## SVC

Use `svc --help` or `svc <command> --help`.

- `svc status`: inspect project state
- `svc lookup`: read SVC guidance
- `svc task init`: create a task packet
- `svc task grow`: inspect packet shape without changing files
- `svc dev`: manage declared development targets

If `AGENTS.local.md` exists, read it after this file. It is ignored local guidance; shared rules belong here.
<!-- svc:end -->
