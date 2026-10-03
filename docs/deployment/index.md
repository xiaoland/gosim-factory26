# 运行、证据与恢复

新执行只使用 `python3 -m lab build/start/status/control` 的 experiment schema 3（显式选择 job/request），独立 runner、制品和分析入口见 [Lab](../../lab/README.md)。旧 plan/run/operation writer 已退役；手册历史章节只用于原件追溯和登记中的旧执行退役通道。新模型/费用/目标集由本轮配方显式冻结，没有通用 ARC-only 或 self_funded 默认值。源码切换不授权运行或迁移。

运行时先确认自己要做的是准备制品、新生成、查询既有记录、恢复工作区，还是对冻结应用重新评分。这些操作消耗的资源、需要的授权和结果身份不同；不能用一次构建成功或页面可打开替代生成、评分或证据完整性结论。

本文是操作入口。产品规则归 [PRD](../prd/index.md)，跨组件职责和终态语义归[技术说明](../product-tdd/index.md)，工具安装和源码修改归 [CONTRIBUTING](../../CONTRIBUTING.md)。参数及版本从实际源码、冻结清单和命令帮助读取；历史观测不代表此刻的机器或平台状态。

位置边界按执行方式区分：开发控制可以在 Mac 上进行；使用官方 ARC 本地 Runner 的生成按 recipe 显式声明并核对 Docker endpoint、镜像、容量和执行环境；其它 Lab local backend 以其 recipe/backend 合同为准；Hosted 生成使用平台身份、提交和监控合同。Mac 上的控制进程不能推断本地 runner 的存在或可用授权，WSL/sfp7 等具体宿主以当前冻结配置和只读读回为准。

| 当前要完成的操作 | 操作说明 | 先确认什么 |
| --- | --- | --- |
| 选择模型通道、比较价格或查看接入验证状态 | [模型提供商目录](model-providers.md) | 精确请求 ID、币种、缓存价格、套餐条件、核对日期及账户额度。 |
| 确认练习/正式模式、冻结 Harness，向官网提交或收集结果 | [平台与制品](competition.md) | [赛事须知与模式](competition.md#赛事规则与提交模式)、variant、ZIP SHA256、模型通道和本次授权。 |
| 用官方本地 Runner 独立生成，再对应用评分 | [本地实验](local-experiments.md) | 本次 Docker endpoint、冻结需求/测试/镜像、workspace 回收及两阶段边界。 |
| 判断哪一层失败，定位原始记录 | [证据查询](evidence.md) | 外层 lab run、内层 `.factory26` 或官网 journal 的生产者。 |
| 接续中断工作区，或重新评分已完成应用 | [恢复与重放](recovery.md) | 源执行已停止、完整检查点、具体恢复改动和新运行身份。 |
| 读取 Braid 遥测、原生会话及 token/耗时 | [Braid 诊断](braid-diagnostics.md) | Backend 与内层 Braid run ID、源端错误、归档或实时材料范围。 |
| 查看或人工介入真实协作现场 | [Console 接入](console.md) | state/binary、对象写权限与物理运行控制分别明确。 |
| 追溯已归档的原生四配置对照 | [Hackathon 历史运行](hackathon.md) | 原配置、网关与冻结材料，不能把旧对照当作当前入口。 |

当前开发实现与历史副本见 [Variant 索引](../../variants/README.md)。输入矩阵、命名与运行次数在[实验导航](../../experiments/README.md)及对应 packet 登记，不在本页维护另一份运行状态。新实验显式声明费用模式和凭据来源；正式额度须针对具体冻结产物取得新授权，历史 journal 的存在不授予接续权限。

原始证据保留具体错误、HTTP 状态和可诊断响应。生成完成、应用交付、官方评分、原生归档和遥测完整性分别判断，辅助证据缺失不自动判为应用失败。模型账户费用、客户端 usage 和回放耗时也分别记录，不从一个维度推导另一个。

存储生命周期的默认摘要、decision 归档回执、预算门禁、稳定 Python 资产入口及只读 GC 已整合到当前开发主线和 I13。来源与实际反馈见[所属任务](../../tasks/experiment-storage-lifecycle/packet.md)；容量操作见[本地实验](local-experiments.md)，回收候选边界见[证据说明](evidence.md#存储回收候选)。源码合入不授权历史清理或 I12 暂停现场处置。Braid/SVC 源码随本仓库 clone 取得；原始运行材料、外部开发 SVC 和未提交改动仍需按实际范围交接。

以下保留既有任务和报告使用的锚点，具体操作已归到对应手册。

## 参赛包与平台边界

打包载荷、模型环境、标准应用布局、Competition 与 ARC 追溯见[平台与制品](competition.md#参赛包与平台边界)。

## 按记录生产者查询

lab、Factory、raw 和官网 journal 的查询入口及状态限制见[证据查询](evidence.md#按记录生产者查询)。

## 等待、反馈与交接

程序等待、观察间隔、原生完成消息和旧记录兼容入口见[证据查询](evidence.md#等待反馈与交接)。

## 实验恢复与反馈循环

工作区接续、材料刷新、检查点选择和官网监控见[恢复与重放](history/recovery.md#实验恢复与反馈循环)。冻结应用或阶段提交的评分方法见 [冻结应用与阶段回放](history/recovery.md#冻结应用与阶段提交回放)。
