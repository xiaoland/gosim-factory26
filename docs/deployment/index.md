# 运行、证据与恢复

新入口使用 `python3 -m lab start VARIANT TARGET TASK` 与 run 级 stop/pause/resume/restart/status，公共 Python API 和数据合同见 [Lab](../../lab/README.md)。旧 experiment/job/attempt、compile/doctor/build 和容量治理不进入新链路；原冻结执行仍沿原 executor，不批量接管或重写身份。新模型、费用和任务范围由本轮 packet 明确授权，源码切换本身不授权运行。新路径仍在集成，实际部署与未验边界见[设施任务](../../tasks/finals-experiment-loop/packet.md)，操作示例不是验收回执。

运行时先确认自己要做的是准备制品、新生成、查询既有记录、恢复工作区，还是对冻结应用重新评分。这些操作消耗的资源、需要的授权和结果身份不同；不能用一次构建成功或页面可打开替代生成、评分或证据完整性结论。

本文是操作入口。产品规则归 [PRD](../prd/index.md)，跨组件职责和终态语义归[技术说明](../product-tdd/index.md)，工具安装和源码修改归 [CONTRIBUTING](../../CONTRIBUTING.md)。参数及版本从实际源码、冻结清单和命令帮助读取；历史观测不代表此刻的机器或平台状态。

位置边界按实际执行合同区分：当前 run 从 target 配置及冻结输入核对 Docker endpoint、镜像、宿主和模型通道；Hosted 使用其平台身份、提交和监控合同。旧 lab.exp 的 recipe/backend 只解释对应冻结执行。Mac 控制进程不能证明 runner 存在或可用，WSL/sfp7 等具体宿主以本次执行身份和只读读回为准。

| 当前要完成的操作 | 操作说明 | 先确认什么 |
| --- | --- | --- |
| 使用已选模型配方 | [跨 variant 模型配方](../../materials/model-recipes/README.md) | 角色模型与有序路由、实际 catalog 和凭据来源；不能由供应商目录或 catalog 默认推断。 |
| 比较候选通道、价格或接入事实 | [模型提供商目录](model-providers.md) | 精确请求 ID、币种、缓存价格、套餐条件与核对日期；账户事实不能代替本次选路。 |
| 确认练习/正式模式、冻结 Harness，向官网提交或收集结果 | [平台与制品](competition.md) | [赛事须知与模式](competition.md#赛事规则与提交模式)、variant、ZIP SHA256、模型通道和本次授权。 |
| 用官方本地 Runner 独立生成，再对应用评分 | [本地实验](local-experiments.md) | 本次 Docker endpoint、冻结需求/测试/镜像、workspace 回收及两阶段边界。 |
| 判断哪一层失败，定位原始记录 | [证据查询](evidence.md) | 外层 lab run、内层 `.factory26` 或官网 journal 的生产者。 |
| 接续中断 run，或重新评分已完成应用 | [恢复与重放](recovery.md) | 来源执行器、停止与 data 保存范围、同 variant 接续及独立评分身份；旧检查点按原合同解释。 |
| 读取 Braid 遥测、原生会话及 token/耗时 | [Braid 诊断](braid-diagnostics.md) | Backend 与内层 Braid run ID、源端错误、归档或实时材料范围。 |
| 查看 run 资源、费用、结果与 Braid 协作 | [Console 接入](console.md) | OTLP 来源、保存状态及投影 cutoff；新 Console 不访问现场或执行写命令。 |
| 追溯已归档的原生四配置对照 | [Hackathon 历史运行](hackathon.md) | 原配置、网关与冻结材料，不能把旧对照当作当前入口。 |

当前开发实现与历史副本见 [Variant 索引](../../variants/README.md)。输入矩阵、命名与运行次数在[实验导航](../../experiments/README.md)及对应 packet 登记，不在本页维护另一份运行状态。新实验显式声明费用模式和凭据来源；正式额度须针对具体冻结产物取得新授权，历史 journal 的存在不授予接续权限。

原始证据保留具体错误、HTTP 状态和可诊断响应。生成完成、应用交付、官方评分、原生归档和遥测完整性分别判断，辅助证据缺失不自动判为应用失败。模型账户费用、客户端 usage 和回放耗时也分别记录，不从一个维度推导另一个。

旧 I13 与 lab.exp 的存储生命周期曾整合默认摘要、decision 回执、预算门禁、稳定 Python 资产入口及只读 GC；这些属于对应冻结协议，不作为新 run 的启动前提。来源与实际反馈见[所属任务](../../tasks/experiment-storage-lifecycle/packet.md)；容量操作见[本地实验](local-experiments.md)，回收候选边界见[证据说明](evidence.md#存储回收候选)。源码合入不授权历史清理或 I12 暂停现场处置。Braid/SVC 源码随本仓库 clone 取得；原始运行材料、外部开发 SVC 和未提交改动仍需按实际范围交接。

以下保留既有任务和报告使用的锚点，具体操作已归到对应手册。

## 参赛包与平台边界

打包载荷、模型环境、标准应用布局、Competition 与 ARC 追溯见[平台与制品](competition.md#参赛包与平台边界)。

## 按记录生产者查询

lab、Factory、raw 和官网 journal 的查询入口及状态限制见[证据查询](evidence.md#按记录生产者查询)。

## 等待、反馈与交接

程序等待、观察间隔、原生完成消息和旧记录兼容入口见[证据查询](evidence.md#等待反馈与交接)。

## 实验恢复与反馈循环

工作区接续、材料刷新、检查点选择和官网监控见[恢复与重放](history/recovery.md#实验恢复与反馈循环)。冻结应用或阶段提交的评分方法见 [冻结应用与阶段回放](history/recovery.md#冻结应用与阶段提交回放)。
