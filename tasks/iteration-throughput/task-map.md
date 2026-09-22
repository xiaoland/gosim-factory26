# 实施前 Spike 与预演

设计与验收已获Human批准。当前共同出口是可线性执行的实施计划和impact handshake；各Cell只做接口核验、无模型或最小模型spike、代码路径预演与计划材料，不修改产品源码或活动配置。

| Cell | owner与局部路线 | 返回及消费关系 |
| --- | --- | --- |
| Assignee与Braid公开面 | 完成 | `cells/assignee.md`；已返回精确文件顺序、兼容风险和最小行为检查。 |
| Variant、能力与SVC装配 | 完成 | `cells/capabilities.md`；已返回 effective schema、四 variant 差异和网关 429 证据。 |
| 官方包与混合Controller | 完成 | `cells/runner.md`；已返回 adapter 状态、恢复点、缓存与并发计划。 |
| Pi lifecycle与整合顺序 | 完成 | `cells/integration.md`与[plan.md](plan.md)；unknown terminal false-ready 已复现，impact handshake 已形成。 |

子Agent仅拥有各自报告文件和隔离调查材料；无源码、活动配置、Corpus、模型实验、平台提交或Git提交权限。恢复局部取证失败由各owner自行处理，只有改变方案的问题进入主上下文。源码审阅不作为独立验收；可读接口查合同，但不凭角色身份或同一实现自洽宣称正确。

每个Cell只返回消费者需要的事实、拟修改面、次序、检查与残余，不以阅读代码后的同意充当验收。主Agent按实际接口和可运行spike核验返回；预演分工不是未来实施拓扑的自动承诺。
