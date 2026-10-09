# 运行与诊断

Factory26 使用 Lab 管理一次生成或评测。每个 run 保存程序、冻结输入、工作区、原生状态、日志及平台回执；完整命令和数据布局见 [Lab](../../lab/README.md)。具体 target、runtime、凭据和任务配置需要在执行环境准备，仓库中的配置不表示相应服务当前可用。

| 操作 | 说明 |
| --- | --- |
| 本地生成与独立评测 | [本地运行](local-experiments.md) |
| 停止、重跑与保留进度接续 | [恢复](recovery.md) |
| 查询状态、错误和归档 | [证据查询](evidence.md) |
| 阅读 Braid 会话与遥测 | [Braid 诊断](braid-diagnostics.md) |
| 部署只读运行界面 | [Console](console.md) |
| 配置模型与供应商路由 | [模型配置](model-providers.md) |
| ARC 包装、生成与评分身份 | [ARC 平台](competition.md) |
| 读取已结束赛事的规则和输入 | [Hackathon Evolution 归档](hackathon-evolution.md) |

生成完成、应用交付、官方评分和证据完整性分别记录。源码发布不等于完整运行验收；使用模型或收费评测前确认本轮执行范围和费用模式。

旧 `lab.exp` 记录由[历史执行器](../../lab/exp/README.md)解释，不传给当前 run 控制接口。仍有独立使用价值的旧服务与恢复说明见[历史入口](history/README.md)。
