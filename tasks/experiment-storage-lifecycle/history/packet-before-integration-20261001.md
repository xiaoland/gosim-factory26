<!-- Create one packet for every non-trivial Consumer Task. `svc task init` creates only this shape. Do not create family children until their topology or information owner is admitted; keep this as a compact Human collaboration surface, not a completed-work log. -->
# experiment-storage-lifecycle

- **Objective**: 为 Factory26 的实验运行时、缓存、工作区、会话、Braid 状态、telemetry、应用制品和评分证据建立可复核的所有权、引用、保留、预算、归档与安全回收方案；先完成设计复核，获用户开工授权后才实施。
- **Guardrails**: 本阶段只调查和编辑本 task packet；不修改源码、不启动实验、不移动或清理 I12 及其依赖路径、不提交。方案优先复用现有 manifest、journal、OTLP 与运行目录，不能用自动删除掩盖重复生成的数据模型缺陷。验收不得新增或运行 Factory/Braid/实验基础设施测试，只能使用静态核对、实际操作、磁盘/制品观测与获授权实验。
- **Verification**: 方案须以实际生产/消费路径为依据，明确每类数据的权威副本、引用与删除条件、保留等级和预算；给出 HLD、与现有 LLD/失败语义的对照、迁移顺序及分阶段验收，并区分立即可做、I12 完成后和 WSL 停机期。
- **Current Truth**: WSL 曾使用约 475/503 GiB，其中 `runs` 约 301.8 GiB、`factory26-official-local` 约 97.5 GiB、独立 acceptance checkout 约 19.7 GiB、`/var` 约 32.7 GiB。应急治理后 WSL 已用约 59 GiB、`/var` 约 6 GiB，但精简快照仍约 45 GiB，历史 evidence 约 37 GiB。本轮核实精简快照内 `telemetry.sqlite*` 约 18.7 GiB、JSONL 约 2.6 GiB、Braid SQLite 仅约 0.12 GiB；大 telemetry 样本超过 99.8% payload 是 logs，且 Braid 源码确认完整 native/对象 evidence 通过 logs 传输。另有逐字节相同的 telemetry/core dump、数百 MiB decoded 投影及 run-local cache。当前 I12 最新记录为两题 paused；restart workspace、shared submission、Braid/Console、容器和 watcher 依赖在远端现场核验前全部受保护。真正根因是执行依赖未建模和完成归档缺少独立释放判据，不是单纯缺少自动删除。
- **Next Step**: 请用户复核[存储、制品与生命周期治理方案](../design.md)，重点确认普通 Factory 实验默认采用 `decision` 归档级、`resumable`/`forensic` 需逐轮显式选择并给预算。认可后进入实施准备和独立预演；当前没有源码实施、迁移、清理或实验授权。

## Supporting Material

- Evidence: [`runs/wsl-retained-20260930/README.md`](../../../runs/wsl-retained-20260930/README.md)、[`docs/deployment/index.md`](../../../docs/deployment/index.md)、[`docs/product-tdd/index.md`](../../../docs/product-tdd/index.md)、[`lab/README.md`](../../../lab/README.md)、[`tasks/iteration12/restart.md`](../../iteration12/restart.md)及方案中的源码入口。
- Decisions: [待复核方案](../design.md)建议稳定资产目录、消费方显式引用、完成归档回执和两阶段安全 GC；不建设中央制品数据库、常驻 GC/TTL 服务或自动分层存储。
