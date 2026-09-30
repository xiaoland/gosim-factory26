# 实验存储、制品与生命周期治理

状态：产品方案已于 2026-09-30 获用户确认；2026-10-01 分支成果已合入开发主线并适配 I13。当前执行仅支持 `decision`。来源分支设计保留，下文其它归档级、GC apply、历史迁移及物理压缩仍为后续方案，不表示已实现或获本次操作授权。

## 职责边界

```text
稳定宿主资产                         活跃运行现场
runtime / Runner / package / input ─ref─► manifest / run / journal
shared rebuildable caches                  workspace / Braid / native / OTLP
          ▲                                      │
          │                                      │ finalizer
          │                                      ▼
          └──────── provenance ─────── 持久归档 + archive.json
                                                │
                                  引用扫描 + 所有权核验
                                                ▼
                                      GC plan → apply receipt
```

不建设中央制品数据库、常驻 GC 服务或通用对象存储。复用现有 manifest、journal、资源记录和生产者原生 ID；每个逻辑 run 只新增一份归档回执，反向引用索引按需从消费记录生成。

## 数据决策

| 对象 | 权威副本 | 默认长期策略 |
| --- | --- | --- |
| runtime、Runner、Agent ZIP、冻结输入 | 稳定宿主资产目录中的不可变内容身份 | 同一宿主每个内容身份一份；run 记录 execution/recovery 引用 |
| Braid state | `braid.sqlite3` 与必要 state | `decision` 保留；生命周期小，不优先裁剪 |
| native 会话 | `native/manifest.json` 指向的原文 | `decision` 保留关联原文，不保留整个 native home |
| OTLP | traces/metrics/操作 logs 与有界 evidence summary | 普通运行不再复制完整 native/对象；`--portable` 仅供 forensic 或无本地原件的跨边界重建 |
| 应用和评分 | application/replay 身份、journal、原始 status/result | 长期保留；绝对来源路径仅是 provenance |
| decoded/viewer/cache/core dump | 可重建投影或故障附件 | 默认候选；只有明确问题引用才 pin |

归档状态拆分为 execution、delivery、evaluation、diagnostic coverage、原文保存、recovery capability 和 reclaim state。I13 归档复制/读取失败、已声明原文缺失会阻止删除 work；关联/observer 覆盖不完整本身不覆盖交付状态。辅助诊断失败不改写有效应用或评分，但没有满足声明的归档义务时不得删除对应来源。

## 归档级别

当前 CLI/schema v3 仅接受已经实现的 `decision`，防止未实现的 `resumable` 承诺下仍删除 workspace。其余级别保留为产品方案，落实其保存与释放合同后再开放。

- `score-only`：包/应用/需求身份、journal、平台原始结果和错误。
- `decision`：默认级；在 score-only 上增加 replay、必要 Braid state、关联 native 原文、错误、usage/timing、telemetry 摘要和 gaps。
- `resumable`：增加同一停止时点的 workspace、在线数据库备份、Git bundle/patch、未提交内容和执行依赖。
- `forensic`：增加完整原始 OTLP、平台 workspace 或其它指定原件；必须单独预算。

## 回收与预算

GC 先生成包含 identity、大小、引用者和理由的只读 plan；apply 必须在同一宿主锁下重核 owner/path/digest，优先同文件系统隔离并写回执。active、paused、cleanup 和显式 recovery 引用受保护；过期时间、失联、目录名和 `completed` 都不能单独授权删除。

实验启动前声明并发数、run workspace cap、telemetry cap、构建峰值、archive level、归档目标和 finalization scratch。preflight 必须满足：

```text
free >= host reserve + 新制品/解包峰值 + 并发 run 剩余 cap + finalization scratch
```

预算配方应将 host reserve 设为文件系统容量 10% 与最大 finalization scratch 的较大值；当前执行器消费冻结的绝对 host_reserve_bytes，CLI 示例默认 50 GiB，不会自行推导容量 10%。inode 默认保留 10%。达到 80% 软阈值时暂停控制器新派发；已经启动的 job 内部构建、解包及宿主手工导出没有独立门禁，不将设计目标冒称当前实现。达到 100% 或 host reserve 时停止 controller 管理的进程组并保留原始错误，不在活动现场临时删 evidence 续跑。容器等外部资源不能从进程组退出推断为已停止，必须保持 `unconfirmed`，随后复用冻结的 `reconcile`/`cleanup` 边界核实。

## 实施和验收顺序

1. Braid 将 operational summary 与 portable evidence 分流；Factory 默认只请求 summary。
2. 当前 I13 生成 finalizer 写 `archive.json`，只有 reclaim eligible 才删除 `work/`。
3. 实验 manifest 显式记录解释器、Runner、runtime、镜像、gateway/service、cleanup/recovery 依赖及空间预算。
4. 建立稳定资产目录和共享缓存，切断 attempt-local runtime/venv 依赖。
5. 上线只读 GC report；首版只把有效 archive 回执的精确 `work` 目标列为候选，稳定资产无引用只作观察。核对 I12 保护清单后才决定是否实现 plan-bound apply。
6. I12 完成后分批迁移历史；WSL 停机后再分别处理 Docker、fstrim 和 VHDX 物理压缩。

遵守仓库约定，不新增或运行 Factory/Braid 测试。验收使用编译、静态依赖核对、实际归档/重放/恢复操作、磁盘与制品观测，以及后续单独获授权的实验。
