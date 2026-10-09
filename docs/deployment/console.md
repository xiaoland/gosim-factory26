# Console 服务与运行接入

新运行的 Lab Console 由 `python3 -m lab serve --config FILE` 提供，共享 Collector、Backend 与静态前端在一个 Python 进程中。服务数据库使用实际服务宿主本地磁盘；首选 sfp7，Mac 控制及回收仍在 WorkSSD。配置、部署身份与当前验收状态见[决赛设施 packet](../../tasks/finals-experiment-loop/packet.md)，组件用法见 [Lab](../../lab/README.md) 和 [Lab Console](../../consoles/lab/README.md)。Braid 协作页面与旧冻结服务归 [Braid Console](../../consoles/braid/README.md)。

以下是新 run 的接入合同；当前真实执行、传输和投影链路仍在设施任务中验收，单独 HTTP 200 不证明闭环。按该合同，运行启动时自动建立观测归属，不要求使用者停 HTTP、人工 register 或创建 accessor。CLI 与 Console 读取同一份保存 status；Pi-only、Braid 和独立评测均有通用页面。Braid 自己维护只读投影与正文路由，页面展示 cutoff、as_of 和缺口，不进入原生成容器、查询 live DB 或执行实时 Braid CLI。模型与物理执行控制使用 Lab run API，Console 不承担人工工作项写入。

Hosted 使用轻量接收与落盘，不携带 UI/query 服务；回收后导入共享 Backend。观测缺口不等同生成失败，服务断连不成为启动门禁。任何低内存、丢失范围和端到端延迟结论均依实际验收，而非配置存在。

## 旧冻结服务

旧服务的 prepare/register、live/archive、accessor 及解除接入操作归[历史 Console 合同](history/console.md#旧冻结-console-服务合同)，仅用于其对应冻结服务。不要以停止 HTTP 或人工登记作为新 run 观测接入前置步骤。旧服务、旧数据及其恢复关系保持原身份，本次说明迁移不控制或退役实际服务。
