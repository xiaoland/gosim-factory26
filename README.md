# Factory26

Factory26 是面向软件开发任务的 Coding Agent Harness 与实验平台，开发于 GOSIM Agentic Factory 2026 / ARC-Bench 赛事。它把需求交给 Agent，通过工具和多 Agent 协作生成应用，再对冻结应用独立评测，保存执行、模型用量和评分来源。

2026 年 Hackathon Evolution 决赛已结束。本仓库公开参赛实现和开发成果；部分实验设施与实现仍有未完成的实际验收，相关限制保留在组件说明和任务记录中。

## 项目组成

| 目录 | 用途 |
| --- | --- |
| [variants/](variants/README.md) | 独立 Harness 实现：Pi 原生执行、Pi + Braid 团队协作及职责对照。 |
| [lab/](lab/README.md) | 启动、观察、控制和保存运行；接入 ARC-Bench 与独立应用评测。 |
| [consoles/](consoles/README.md) | 运行状态与 Braid 协作界面。 |
| [materials/](materials/README.md) | 共享技能、工具依赖、原生补丁与模型配方。 |
| [tooling/](tooling/scripts/README.md) | 开发工具准备、Linux 资源构建和 Harness 打包。 |
| [sources/](sources/) | 随仓库维护的 Braid、SVC 与公共执行设施源码。 |
| [experiments/](experiments/README.md) | 实验配方与历史定义。 |

团队 Harness 使用 Braid 管理 Issue、PR、成员与讨论，Pi 负责原生工具和会话，SVC 提供按需读取的工作方法。不同 variant 独立维护生成流程；源码用途和差异见 [Variant 索引](variants/README.md)。

## 开始使用

先阅读 [开发说明](CONTRIBUTING.md)，按[工具准备方法](tooling/scripts/README.md#准备原生工具)安装所需依赖，再选择 variant、执行 target 和需求输入。target、模型通道与凭据需要按自己的环境配置；仓库不提供公共 API key 或正在运行的服务。

查看命令入口与已有运行：

```sh
python3 -m lab --help
python3 -m lab status
```

实际生成会调用模型。启动、保存、接续和独立评测的方法见 [运行手册](docs/deployment/index.md)与 [Lab 说明](lab/README.md)；Linux 制品构建见[打包方法](tooling/scripts/README.md#构建独立运行资源与制品)。

## 文档与结果

[文档导航](docs/index.md)提供产品、架构和操作入口。[历史报告](runs/reports/README.md)记录带来源与条件的实验结论，[工作记录](docs/work-index.md)用于追溯实现决定和未完成事项。原始运行、下载快照、依赖和凭据不随 Git clone 提供。

相关项目：[GOSIM Factory26](https://create.gosim.org/factory26/)、[ARC-Bench](https://github.com/code-philia/arc-bench)、[Braid](https://github.com/xiaoland/braid)、[SVC](https://github.com/xiaoland/svc)。
