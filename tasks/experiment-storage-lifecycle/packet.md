# experiment-storage-lifecycle

- **Objective**: 为 Factory26 的运行时、缓存、workspace、Braid/native/OTLP、应用和评分证据建立可验证的归档、预算、引用与安全回收边界。
- **Guardrails**: 不触碰 I12 暂停现场及其 restart、shared submission、Braid/Console、容器和 watcher 依赖；不运行模型实验；不新增或运行 Factory/Braid 测试。实现使用编译、静态核对、实际制品操作及后续单独获授权实验验收。
- **Authorization**: 用户于 2026-09-30 确认普通实验默认采用 `decision` 归档级，并授权“直接改进 braid 的 OTLP 导出内容、内部采集/埋点等”，要求创建独立分支和 worktree 开始；随后明确“可以自由提交”。授权范围包括本方案需要的 Factory、Braid、文档和任务包改动及当前任务提交，不包括模型实验、历史清理、I12 现场迁移或 VHDX 停机操作。
- **Workspace**: Factory 分支 `feat/experiment-storage-lifecycle`，worktree `/Volumes/WorkSSD/Development/.worktrees/experiment-storage-lifecycle/factory26`。独立 Braid 源位于该 worktree 的 `sources/braid`，使用同名分支。
- **Current Truth**: 历史快照中 `telemetry.sqlite*` 约 18.7 GiB，Braid SQLite 约 0.12 GiB；大 telemetry 样本超过 99.8% payload 是 logs。源码确认完整 native/对象 evidence 被周期性分片写入 OTLP。隐藏的 attempt-local interpreter/runtime 和完成后缺少独立 reclaim 判据，使目录名或 `completed` 都不能安全授权删除。
- **Decision**: 普通 Factory 实验使用 `decision`：长期保留应用/replay、必要 Braid state、关联 native 原文、评分和错误；完整 OTLP、整棵 workspace 仅在逐轮明确的 `resumable`/`forensic` 级保留。执行/cleanup/recovery 引用可以 pin 物理对象，provenance 只保留身份和位置事实。
- **Implementation Status**: Braid 提交 `e87b82b` 将运行期和默认手工 export 改为有界摘要；只有 `--portable` 发送完整原文，增加源材料 bytes/artifacts 指标，并保留既有离线重建格式。Factory 提交 `57cd761` 已接入默认摘要、`archive.json` 回执及“回执授权后才删除 work”的门禁，提交 `e222296` 已增加 lab schema v3、冻结的 storage policy/解释器依赖及启动 preflight，提交 `cfc7aa2` 已增加异步实际占块观测、80% 派发门禁、100%/host reserve/inode 的受控进程组 TERM/KILL，以及外部资源 `unconfirmed` 边界，提交 `956de0b` 已将 controller、job、inspect/cleanup 绑定到同一份稳定宿主 Python 资产回执，提交 `e6e1a5c` 已增加失败关闭的只读 GC plan；只有完整 v1 archive 回执的精确 `work` 能成为非授权候选。
- **Integration Authorization**: 用户于 2026-10-01 明确：“好的，也可以委派开工 合入 experiment-storage-lifecycle”。授权 Factory/Braid 源码与文档合入及必要 I13 适配、非模型编译/CLI/prepare-only 和当前任务限定提交；不含资产建立、历史/I12 GC plan、apply、真实清理、迁移或物理运行控制。
- **Current Integration**: 六个 Factory 来源提交已按 delta 合入开发主线，I12 收尾改动仅映射到 I13；Braid e87b82b 已整合为目标 8325ed6。集成收紧真实原文保存门禁、decision-only 支持边界，加入 I13 GC 保护，并将新应用复评配方适配至稳定 Python/预算 schema v3。Python/Rust 编译、CLI 帮助及真实 prepare-only 通过，运行期归档/预算/GC/传输行为未实测。
- **Next Step**: 将完整合入结果交主线复核。实际建立宿主 runtime、对 I12/历史记录域运行 GC plan、任何 GC apply、模型运行和 WSL/VHDX 停机操作仍在应用前集中复核。冻结 I12 与既有现场保持原样，Console registry 的域外依赖必须显式 protect。

## Supporting Material

- [治理设计](design.md)
- [I13 合入回执](../iteration13/storage-lifecycle-integration.md)
- [合入前历史](history/)
- [WSL 应急治理记录](../../runs/wsl-retained-20260930/README.md)
- [运行说明](../../docs/deployment/index.md)
- [产品技术说明](../../docs/product-tdd/index.md)
