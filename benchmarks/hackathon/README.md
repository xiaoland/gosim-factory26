# Hackathon 本地公开需求代理测试集

本目录将公开的 Hackathon GitHub 与 Sheet 需求转换为本地 Playwright 检查。它不是官方隐藏测试的副本，也不预测官方分数。主指标固定为通过检查的公开原子需求数：GitHub `/47`、Sheet `/24`。

每个场景由官方本地 Runner 在独立的冻结应用副本中执行。测试仅使用页面入口、可访问名称、浏览器会话和公开 UI；不调用私有 API、修改数据库或读取应用源码。Sheet 中互相冲突的 `Q3 Sales` 初始状态按场景分别检查，并通过 UI 建立目标功能所需的数据。GitHub 缺少公开凭据或构造路径的交付状态会报告为 `blocked`。

场景有五种结果：`passed`、目标断言 `failed`、前置条件 `blocked`、评测设施 `incomplete`、尚未运行 `unexecuted`。后四种都不会从固定分母中移除。UI 检查只能证明可观察行为，不能证明服务端事务或内部存储实现。

运行入口与参数见 [`experiments/hackathon-local`](../../experiments/hackathon-local/README.md)。`coverage.json` 绑定官方需求内容哈希、71 条原子需求、稳定场景 ID、祖先合同和种子来源。失败 trace、截图、官方 Playwright JSON、Runner 日志和容器清理记录保存在对应实验 run 中。
