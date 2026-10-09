# Console

Lab Console 显示 run 的状态、资源、费用和结果，Braid Console 显示协作对象与原生会话。两者的职责和组件入口见 [Console 索引](../../consoles/README.md)。

```sh
python3 -m lab serve --config FILE
```

Lab 服务将 Collector、Backend 与静态前端放在同一个 Python 进程中。配置及部署方式见 [Lab Console](../../consoles/lab/README.md)；服务 SQLite 应位于服务宿主的本地磁盘，Mac 的服务数据和回收产物位于 WorkSSD。

CLI 与 Console 消费保存的 run 状态。页面中的 `as_of`、cutoff 和缺项说明观测覆盖，不表示实时现场；HTTP 服务可访问也不证明生成或评分成功。Console 断连不停止运行，执行控制由 Lab run API 完成。

旧 Braid 独立服务的准备、登记和释放方法见[旧服务操作](history/console.md#旧冻结-console-服务合同)，其人工接入流程不适用于新 Lab run。
