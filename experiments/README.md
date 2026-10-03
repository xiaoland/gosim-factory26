# 实验定义与配方

variant 是独立维护的 Harness；实验是一项问题及其冻结比较条件；run 是一次实际执行。名称供人查找，源码、包、应用摘要和实际 ID 负责身份。实现选择见 [Variant 索引](../variants/README.md)，执行合同见 [Lab](../lab/README.md)。本页不维护“正在运行”或“待启动”清单。

## 定义、执行与历史

`experiments/<实验>/` 保存 intent、recipe 和冻结 compilation bundle；实际 build/start 使用独立的 `runs/<实验>/<执行>/`。运行保存定义消费快照、冻结执行计划、attempt、artifact、telemetry 和回执，不向定义目录写状态。多个执行可引用同一定义；重试和恢复沿运行关系接续，改变定义则建立新运行。大包、runtime 和私有 deployment 由定义引用，不复制到本目录。

Mac 的项目产物按 [存储规则](../AGENTS.md#工作知识与反馈) 位于 WorkSSD；远端数据保存其实际宿主、路径和来源，不为统一路径复制大型证据。旧 runs、ZIP 和平台名称保留原身份。

| 入口 | 适用范围 |
| --- | --- |
| [I14 intent 接入](i14-0/README.md) | 显式目标、模型政策与逐应用评价的公共 compiler；具体矩阵由本轮 intent 声明。 |
| [Hackathon 公开需求回放](hackathon-local/README.md) | 将已冻结应用按场景交给官方本地 Runner，不生成应用、不预测官网分数。 |
| [pi-braid Lite 配方](pi-braid-lite/README.md) | 固定 I10 `pi-braid` 身份的 Keep/BookStack 配方；不是当前 I13/I14 基线的通用启动器。 |
| [历史登记与旧定义](archive/README.md) | 查前序实验的问题、编号和来源；不从这里取得当前运行授权。 |

## 登记下一项实验

在所属任务的实验记录中声明问题、授权、case、冻结输入、计划次数和完成条件。编号采用 `eYYYYMMDD-NN`，日期取首次登记的 Asia/Shanghai 日期，同日序号查重后分配，不复用；它不替换 Lab 的 `exp-...` ID。编号或目录存在不证明已获授权。

case 是实验内的配置行，可使用同一 variant 的不同冻结包。每次执行显式关联可读名、venue、run ID/路径、包、重放来源和结果入口；名称不供机器解析。

| 执行 | 可读名称 | 来源要求 |
| --- | --- | --- |
| 新生成 | `<实验>--<case>--<task>--gNN` | 本次冻结生成包与允许需求。 |
| 固定应用复评 | `<实验>--<case>--<task>--rNN` | 来源 run、应用摘要及算法，不重新生成。 |
| 本地逐场景复评 | `<实验>--<case>--<task>--<scenario>--rNN` | 同上，另保留冻结 suite 与稳定场景 ID。 |

每次新生成或复评分配新编号，包括未进入评分的执行；在实验/case/task 内跨场所分配，不直接取 attempt 编号。恢复同一 run、重新查询或采集沿用原名。多个 benchmark 有同名题时，task 简称加比赛前缀。官网 display name 属于 submission，可能包含多题，不能代替每题执行身份；无法确定的来源保持未知。
