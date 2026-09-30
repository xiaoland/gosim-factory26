# 实验存储、制品与生命周期治理方案

状态：待用户复核。本文只形成产品与技术方案；尚未获得源码实施、历史数据迁移、清理或实验授权。

## 结论

不建设新的制品数据库、常驻 GC 服务或通用对象存储。最小可行方案是：

1. 把可共享的 runtime、Runner、冻结包和缓存移出 run evidence，放入稳定、不可变、带内容身份的宿主资产目录；run 只记录依赖。
2. 让消费方在现有 `manifest.json`、`run.json`、Competition journal 和资源记录中声明执行、清理与恢复所需的真实依赖；历史来源只保留身份，不自动 pin 原 workspace。
3. 在 run 完成时按明确归档级别生成可验证的 `archive.json` 回执；应用结果、诊断完整性、恢复能力和可回收性分别判定。
4. GC 只扫描已有记录，先输出带理由的候选清单，再在同一宿主锁下处理无活动引用、无恢复承诺且已有归档回执的对象。未知旧数据默认不删。
5. 新运行先消除重复生成；压缩和迁移只处理已经收敛的权威副本，不能作为重复数据模型的补救。

这套边界覆盖本轮目标。暂不需要 TTL 续租守护进程、可写引用计数、跨机共享数据库、自动分层存储或后台自愈。

## 已核实的证据

应急治理及容量事实见 [`runs/wsl-retained-20260930/README.md`](../../../runs/wsl-retained-20260930/README.md)。本轮进一步只读核对得到：

- 精简快照的 `main/runs` 约 37 GiB。`telemetry.sqlite*` 共约 18.7 GiB；JSONL 共约 2.6 GiB；Braid SQLite 共约 0.12 GiB。Braid DB 不是主要容量来源。
- I11 完成接续的 Sheet telemetry 中，logs 约 4.106 GB，metrics 约 4.0 MB，traces 约 1.1 MB；GitHub 对应约 2.844 GB、5.0 MB、1.0 MB。两个样本的 logs 均超过原始 OTLP payload 的 99.8%。Braid 源码明确将无损 native/对象 evidence 分片放入 OTLP log body，并周期性采集；因此 telemetry 不只是轻量时序，而包含大块内容副本。
- 同一 Sheet Braid run 在 attempt-03 与 attempt-04 的 315,043,840 字节 telemetry DB SHA256 完全相同；I11 feasibility 与后续 resume 中同一 116,199,424 字节 core dump 的 SHA256 也完全相同。重复不是估算，而是逐字节副本。
- 多个 `decoded.json` 单文件达到约 248–464 MB，属于可由原始 OTLP 和分析器重建的投影。I11 两个完成目录的 `work/cache` 仍分别约 682 MiB 和 734 MiB。
- [`lab/plan.py`](../../../lab/plan.py) 会按实验复制冻结输入；[`arc_bench_adapter.py`](../../../lab/arc_bench/arc_bench_adapter.py) 会把 Agent ZIP 展开到 attempt workspace；[`competition.py`](../../../lab/arc_bench/competition.py) 又复制一份 `agent.zip`。这些动作各自有正确的局部目的，但没有跨实验的共享资产边界。
- [`arc_matrix.py`](../../../lab/arc_bench/arc_matrix.py) 把 `sys.executable` 绝对路径写入命令和 cleanup handler，却没有把解释器列为冻结输入或依赖。I12 的启动与 watcher 记录还引用旧 attempt venv、旧 observer 及既有 runtime；Console registry 直接引用现存 state、binary、容器和容器内绝对路径。目录名看似历史，不代表没有消费者。
- [`variants/pi-braid-i12/run.py`](../../../variants/pi-braid-i12/run.py) 将归档异常记为 `diagnostic_error`，但只要生成/Braid/history 条件成立仍会删除 `work/`；`native/manifest.json` 的 partial/unknown 没有进入删除条件。当前实现正确地不让辅助诊断覆盖应用结果，却尚未建立独立的“可回收”判据。
- 官网 monitor 当前既保留 `workspace.zip`，又提取其中一部分 evidence；`archive-index.json` 只有 path/bytes，没有 ZIP 或逐文件哈希。终态下载失败仍可进入 done，这对“评分已终态”合理，但不能表示“恢复材料已齐”。

当前 I12 的状态和依赖来自仓库最新 packet/receipt，不是本轮远端实时复查。两题暂停现场、restart 工作区、shared submission、Braid state/worktrees/native homes、Console registry、当前 binary、容器与可能仍存活的 watcher 在现场核验前全部视为受保护。

## 问题树与因果链

| 问题 | 根因 | 产品决策 | 技术方案 | 验收结果 |
| --- | --- | --- | --- | --- |
| 历史目录不能删 | 执行解释器、Runner、runtime、observer、Console 和恢复入口使用历史绝对路径；来源记录与运行依赖没有区分 | 新运行不得借用 attempt 目录作为 runtime；消费方拥有依赖声明 | 稳定宿主资产目录；现有 manifest/run/journal 增加执行、cleanup、恢复依赖；历史路径只读兼容 | 下一次获授权运行的 command、handler、shebang、mount、service 均不指向旧 attempt；I12 旧依赖被明确保护 |
| runtime/cache 每 run 重复 | 自包含 ZIP、实验输入冻结、workspace 展开、per-run npm/pnpm store 混在同一目录语义 | 自包含发布包只保留一个冻结 ZIP；宿主 runtime/cache 共享；运行现场只保留可变状态 | runtime/Runner/包按内容身份稳定存放；journal 同文件系统优先 hardlink，跨文件系统才复制；npm/pnpm/Cargo/浏览器缓存归宿主缓存 | 同一 package/runtime/input 在同一宿主只有一个权威物理副本；并发运行仍相互隔离 |
| completed 仍占满磁盘 | completed 只表达某一生产者终态；没有归档级别和删除回执 | 业务完成、评分收齐、诊断覆盖、恢复能力、可回收性是五个独立事实 | 完成 finalizer 写 `archive.json`，逐类确认保留、替代、缺口与释放资格 | 归档失败不改分数，但原件不被误删；归档完成后可说明每个删除对象由什么替代 |
| telemetry 与 native 成本失控 | 无损 native/对象快照进入 OTLP logs；周期/补采/恢复和 workspace 复制会重复保存；派生页面再展开 | native/Braid 是本地内容权威；OTLP 是操作时序与传输通道，不默认再保存完整内容副本 | 新运行分开 operational telemetry 与 portable evidence；本地默认只保留 native、Braid、errors、usage/timing 和必要 OTLP；完整 OTLP 仅 forensic 级 | 普通完成 run 不再同时长期保存 native 原文、完整 evidence logs、workspace ZIP 和 decoded 投影 |
| GC 有误删风险 | 没有可达性模型；按目录名、时间或 completed 猜测 | 只有执行/cleanup 引用和明确恢复承诺能 pin 物理对象；provenance 不 pin | 扫描消费方记录生成反向索引；活动所有权用 PID/start/host、容器 ID/mount、Braid/Console 事实核验；未知保留 | GC 报告能解释每个 protected/candidate；过期或失联只进入核对，不自动释放 |
| 磁盘耗尽后才响应 | 没有启动峰值预算、host reserve、运行中增长与停止策略 | 无预算不启动；空间保护先停止新增写入，再受控暂停/停止生产者，绝不在活动现场靠删除腾空间 | preflight 计算峰值；controller/watch 记录 statvfs、inode、已知大对象和增长；阈值动作写 journal | 在 ENOSPC 前产生可诊断的 budget stop；终态、现场和实际停止动作可追溯 |
| 多机/官网/本地难关联 | ID 已存在但映射分散，绝对路径被误当身份，同一 Braid run 被多次复制 | 保留各生产者原生 ID；只用显式关系和带算法摘要连接；路径只是位置 | 复用 experiment/job/run/retry、Braid run、native ID、package/application digest、submission/platform run；归档记录 host/location | 任取官网结果可追到确切 package、应用、来源 run、Braid/native 证据和观测时间，搬迁不改变逻辑身份 |

## HLD：三类存储面和一个完成边界

```text
稳定宿主资产                         活跃运行现场
runtime / Runner / package ZIP ──ref──► manifest / run / journal
requirements / shared caches             workspace / Braid / native / OTLP
          ▲                                      │
          │                                      │ finalizer
          │                                      ▼
          └──────── provenance ─────── 持久归档 + archive.json
                                                │
                                  引用扫描 + 所有权核验
                                                ▼
                                      GC plan → apply receipt
```

### 稳定宿主资产

延续 `official-local/README.md` 已提出的 `platform-inputs/`、`runners/<revision>/`、`runtimes/<build-id>/`、`packages/<variant>/<build-id>.zip`、`services/<instance>/` 结构。目录名只导航，身份来自 manifest 与摘要。

- runtime 是不可变执行制品，不是 run evidence。`runtime-source.json` 继续记录来源，但需补全 runtime 全树身份；构建使用临时目录，完整核验后原子发布，失败不留下可复用的半成品。
- Runner、Agent ZIP、需求快照各保留一个按内容身份核实的权威副本。run/journal 在同一文件系统可 hardlink 冻结文件；跨文件系统复制并记录新位置，不引入自制 CAS 服务。
- npm/pnpm、Cargo target、浏览器下载和 Docker build cache 是可重建宿主缓存。使用原生并发安全与宿主配额，不进入 evidence；共享缓存不等于共享可变 workspace。
- 自包含官方 ZIP 仍包含 runtime，这是平台交付要求。治理消除的是“同一 ZIP/展开 runtime 在每个 attempt 和 journal 长期重复保留”，不是取消自包含制品。

### 活跃运行现场

active、paused、lost-but-unreconciled 和 explicit-resume 四类现场都受保护。run 的消费记录声明：

- `execution`：解释器、Runner、runtime、package、输入、镜像、gateway/service、命令与挂载。
- `cleanup`：用于 inspect/cleanup 的解释器、handler、service state 和资源 ID；停止主进程不代表这些依赖可删。
- `recovery`：只有明确承诺续接时存在，保护同一检查点的 workspace、Braid DB、Git、native、配置与 runtime 身份。
- `provenance`：来源 run、package/application digest 和原路径；永久保留事实，但不保护来源 workspace。

不使用“lease 超时即删除”。时间只触发重新核对：控制器复用现有 host/boot/PID/start 事实，ARC 资源复用 container ID + `/workspace` mount 所有权，Console/Braid 复用 registry、runtime lock、数据库和容器事实。paused 容器仍是活动引用；未知状态保持 protected。

### 持久归档

每个逻辑 run 生成一个机器可验证的 `archive.json`，只做收口回执，不复制另一套运行状态。最少包含：

- archive level、来源 host/path/capture time；
- experiment/job/attempt、Braid/native、package/application、submission/platform run 等显式身份；
- 每个保留对象的类型、算法、摘要、逻辑字节、实际位置和唯一/共享属性；
- 评分、应用、诊断、恢复各自的状态与 gaps；
- 被省略或可重建对象、替代对象、释放条件；
- 活动 SQLite 使用 online backup 的回执，静态文件使用 manifest/hash；
- 恢复段的 source segment、collector session、batch cutoff 和 `recovery_of`。

归档级别不改变历史结果：

| 级别 | 保留内容 | 适用场景 |
| --- | --- | --- |
| `score-only` | package/application/requirements 身份、journal、原始平台 status、完整评分与错误 | 纯应用重放或只关心外部结果 |
| `decision`（Factory 实验默认） | `score-only` + 冻结应用或 replay 能力、Braid DB/必要 state、`native/manifest.json` 与所引用原生原文、错误、usage/timing、telemetry 摘要和 gaps | 需要判断 Harness 行为、成本与失败原因的普通实验 |
| `resumable` | `decision` + 同一停止写入时点的 workspace、online SQLite backup、Git bundles/patches、未提交内容、runtime/package 身份与路径约束 | 已明确承诺续接的未完成工作 |
| `forensic` | `decision` + 完整原始 OTLP、平台 workspace 或其它指定原件 | 代表性基线、异常根因或方法研究；必须单独给预算 |

默认不把 `resumable` 当作所有失败 run 的永久状态。恢复检查点是有成本的产品承诺；完成、放弃接续或被新检查点取代后，转为 `decision` 或 `score-only`。

### 完成状态拆分

以下字段独立，不再由 `completed` 相互推断：

1. `execution_result`：进程/生成是否终态。
2. `delivery_result`：冻结应用是否交付。
3. `evaluation_result`：本地/官网评分是否完整。
4. `diagnostic_coverage`：native/OTLP/关联 complete、partial、unknown。
5. `recovery_capability`：none、declared、verified、gapped。
6. `reclaim_state`：blocked、eligible、applied、failed。

归档辅助失败不把有效低分或已交付应用改成失败；但没有满足本 run 声明的归档义务时，不得删除对应原件。已明确缺口时只 pin 缺口所需的最小来源，不能因为一个 native 文件失败就永久保留整个 Runner workspace。

## 数据所有权、预算与回收条件

| 数据 | 权威副本 | 预算方式 | 回收条件 |
| --- | --- | --- | --- |
| runtime / Runner | 稳定资产目录的不可变树 + 完整身份 | 宿主级；只计被 execution/recovery 引用的版本与一个当前构建版本 | 无 execution/cleanup/recovery 引用，构建来源和归档替代已核实 |
| Agent ZIP | packages 中一个完整 ZIP SHA256 对象 | 每 digest 一份；journal 只 link/ref | 无 run/journal/replay/recovery 需要精确包；否则永久保留一份而非每 run 一份 |
| requirements/input | platform-inputs 中经 inventory 核实的一份 | 每内容摘要一份 | 没有结果、复评或恢复引用；小型权威输入通常长期保留 |
| npm/pnpm/Cargo/browser cache | 宿主缓存 | 独立软/硬上限；不占 evidence 预算 | 无活动 writer 时可按平台能力回收；删除只影响重建时间 |
| active workspace | run 目录 | 每 run 在 packet/recipe 声明 peak cap | archive 回执完成、无 recovery promise、无 active/cleanup 引用 |
| Braid DB/state | run 的 decision/resumable archive | 纳入 decision cap；DB 体量小，不优先裁剪 | score-only 明确放弃过程归因，或由更强 archive 替代 |
| native sessions | `native/manifest.json` 指向的一个原文集合 | decision cap；按已关联会话计，不保留整个 native home | score-only 或明确裁剪；manifest 单独存在不能替代原文 |
| OTLP | 活动时原始 DB；完成后按 archive level | 普通 run 有独立 telemetry cap；完整 DB 只允许 forensic | decision 归档生成摘要/gaps/必要 errors 后可裁剪；forensic 保留原 DB |
| 应用 | application tree + receipt，或已核实 replay ZIP | 每 application digest 一份 | 明确放弃部署/复评；只留摘要不足以 replay |
| 评分证据 | journal + 原始 status/result/observed_at | 低成本，长期保留 | 不自动回收 |
| viewer/decoded/SVC analysis | 可重建 analysis cache | 独立小配额 | 第一优先级回收；源和工具身份仍可取得即可 |
| core dump、trace/video/screenshot | 明确引用的故障证据 | 默认不保留；异常 run 单独声明 | 未被问题结论引用即可删；不能因扩展名进入永久 evidence |

## telemetry 与原生会话决策

当前大 telemetry 不是“监控本来就贵”，而是内容层和传输层重叠。新设计采用以下边界：

- `native/` + manifest 是本地会话内容权威；Braid DB/state 是协作对象权威。
- OTLP traces/metrics/普通 logs 保留运行时序、用量、操作结果和具体传输错误。Collector 继续只验证协议并保存原始批次，不在接收侧理解或裁剪 Braid 语义。
- Braid producer 不再周期性重发完整、未变化的 native/对象字节。运行中只发有界对象摘要和 operational signals；完成时本地 archive 已存在则发 manifest、摘要和 gaps，不再把同一原文复制进本地 OTLP。只有需要跨边界的 `portable evidence` 才发送完整分片，并把该传输副本本身视为 archive，不再同时搬运 native 原件。
- 在上述 producer 边界实施前，不直接对活动 SQLite 做 SQL 删除。历史普通 run 先按 archive level 选择是否整体保留 OTLP；派生 export/decoded/viewer 可立即列为候选。这样不会用 GC 掩盖重复生成。
- 默认 `decision` 级保留完整关联 native，而非所有工作目录中的 session/cache。被替换会话仍由 manifest 关联，缺失保持 gap。只有基线、异常或方法研究 run 进入 full OTLP forensic。

## 空间预检、观测与停止策略

### 启动前

每个获授权实验在 packet/recipe 声明：并发数、每 run workspace cap、telemetry cap、是否构建 runtime/镜像、archive level、归档目标文件系统和 finalization scratch。未声明上限的首次新配方不启动；先依据同类历史或一次明确授权的小规模运行校准。

preflight 使用实际可用 bytes/inodes，而不是目录配额名称。必须满足：

```text
free >= host_reserve
      + 新增不可变制品/解包峰值
      + 所有并发 run 的剩余 cap
      + 同盘 finalization scratch
```

初始 `host_reserve` 建议取文件系统容量的 10% 与一次最大已授权 finalization scratch 的较大值；inode 同样保留 10%。503 GiB 根分区对应约 50 GiB 的初始空间底线。这个值是保护底线，不是每 run 预算；取得新配方实际峰值后再复核，不从 45 GiB 历史快照反推固定 run cap。

Docker 构建还需单列 build cache/image/container 峰值；Windows 宿主可用空间和 WSL VHDX 逻辑上限都要满足，不能只看 WSL `df`。

### 运行中

复用现有 controller/watch，不启动模型或新守护服务。程序记录：filesystem available bytes/inodes、已知 run 根和 telemetry DB 大小、Docker 当前资源、增长速率及最近阶段。`statvfs` 可高频低成本采样，目录明细只在阶段变化和既有 3/8 分钟监控点采集。

- 达到 run cap 的 80%，或预测在下一个监控窗口触及 host reserve：停止派发新 attempt、构建、解包、workspace 下载和可选 full evidence export；继续收口已完成结果并告警。
- 达到 run cap 的 100% 或 host reserve：按配方预先声明的控制入口暂停或停止实际写入者，记录 `storage_budget_exceeded`、具体路径/字节/动作。没有安全 pause 的外部进程使用现有 process-group stop；远端运行不因本地空间不足被盲目取消，只停止本地下载并保留 journal。
- ENOSPC、inode 耗尽和写入失败保留原始错误；不在活动 run 内临时删除 cache/evidence 来继续消费模型。

## 安全 GC

GC 分两步，启动/发布新引用和 GC apply 使用同一宿主 `flock`，避免扫描后新运行开始引用：

1. `plan` 扫描稳定资产 manifest、lab experiment/run、Competition journal、Harness run、resource records、Console registry 和 recovery/archive receipts，输出每个对象的 identity、逻辑/实际大小、引用者、状态、候选理由和未知。
2. `apply` 只接受同一 plan identity；再次核验 owner、路径和摘要。优先同文件系统 rename 到隔离区并写结果回执，随后按明确保留期删除。无法原子隔离时停止，不退化为宽泛 `rm` 或 `docker system prune`。

引用传播规则：active/paused/cleanup/recovery 保护目标及其必要依赖；provenance/retry/source_application 只保护身份和 archive location。控制器失联、lease 时间到或目录久未修改都不能单独授权删除。

旧数据没有 archive receipt 或记录格式未知时只进入 inventory。第一次治理由人工确认归属和 archive level；纳管后才允许自动生成候选。GC 不递归猜测任意目录用途，也不扫描密钥内容。

## WSL、Docker 与 VHDX 边界

- WSL ext4：Factory 管理 run、assets、cache 和 archive 的逻辑占用；系统层继续维持 1% reserved blocks、journald 上限和 weekly fstrim。`du`、`df`、inode 与打开但已删除文件分别核对。
- Docker：Factory 只通过已记录的 container/image/volume/build identity 管理自己拥有的对象。现有 ARC `container_id + mount` 核验可复用。镜像没有运行容器不等于没有恢复价值；不以全局 prune 代替引用判断。
- VHDX：ext4 释放和 fstrim 只使块可回收，不保证 Windows 文件立即变小。物理压缩必须在 I12 结束、所有 WSL 进程和暂停容器均可终止、WSL 干净 shutdown 后单独执行与验收。VHDX 大小不进入每 run 成功判据。

## 现有 LLD 的最小改动点

| 组件 | 复用 | 需要调整的行为 |
| --- | --- | --- |
| `scripts/runtime.py` | lock/patch 来源、Linux 导出、`runtime-source.json` | 临时构建后原子发布；补全 runtime tree identity；稳定输出不放在 attempt；cache 设宿主预算 |
| `scripts/package_agent.py` | 逐文件 manifest、ZIP 原子失败处理 | package 只生成一次并登记完整 ZIP SHA；stage 是临时构建物；run/journal 不再各存物理副本 |
| `lab.plan` / `lab.run` | experiment/job/attempt/retry、input inventory、controller journal | 管理资产可 ref/link；记录 interpreter、Runner、runtime、image、gateway/service 和 cleanup dependencies；增加 budget/archival facts，不改变 Harness 私有协议 |
| `arc_matrix.py` | recipe 和 resource handler | `sys.executable` 及 handler 依赖显式化；不让旧 attempt venv 成为隐藏依赖 |
| `arc_bench_adapter.py` | exact container ID + mount cleanup、application receipt | workspace 完成后按 archive level 释放展开 Agent/runtime；资源清理状态与 evidence reclaim 分开 |
| variant `run.py` / recovery | application、Braid、native 现有分层结果 | 共享宿主包缓存；归档各步骤独立回执；只有 reclaim eligible 才删 work；恢复写标准 delivery/application receipt 与 segment lineage |
| Braid telemetry | event digest、manifest/gaps、三信号 | operational 与 portable evidence 分流；不重复发送未变化的大 artifact；Collector 保持格式中立 |
| Competition / monitor | package SHA、pending journal、原始 status、source_application | canonical ZIP 用 ref/link；`collected` 与 workspace/recovery archive 状态分开；workspace ZIP 有 SHA/逐文件 inventory，长期只保留 ZIP 或提取证据之一 |
| analysis/viewer | 来源指纹、批次 cutoff、新目录发布 | 输出归 analysis cache，默认可删；不把 decoded/viewer 变成第二权威副本 |

## 旧路径与兼容分支的退役原则

I12 结束并完成归档前，不移动或修改任何 restart、shared-submission、state、runtime、binary、container、Console registry、watcher 或它们引用的旧路径。

I12 后优先停止“新写入”，再删除旧实现：

- 新实验不再从 `runs/<historical-attempt>/venv`、旧 baseline runtime、旧 observer 或根目录遗留 Runner/ZIP 启动；在稳定资产目录重建 venv/runtime，venv 不搬家复用。
- I12 的一次性 freeze/launch/restart 路径在最终 `resumable` 或 `decision` archive 验收并释放恢复承诺后退役，不转成下一轮模板。
- `source_application.run_path`、历史 input source 和旧 nested telemetry 路径只保留为 read compatibility；新 writer 使用内容身份和显式 location，不再把绝对路径当保留引用。
- variant 名 allowlist、开发源码 fallback、旧平铺 native/session 搜索只在确有历史消费者时保留。新包不应依赖这些分支；完成兼容使用量盘点后逐项删除，不再增加符号链接链。
- 第一批实际删除候选是 analysis decoded/viewer/export、`work/cache`、node_modules、浏览器与包缓存、Rust target、无引用 core dump、重复 stage/ZIP/workspace 展开和“workspace ZIP + extracted evidence”双份。完整 OTLP 和 native 的选择必须先有 archive level，不按扩展名批量删。

## 迁移与实施顺序

### 立即可做，但仍需本方案获开工授权

1. 对 I12 做一次只读 dependency closure：核对实际 PID/start、容器 ID/mount、Console registry、watcher、命令、shebang、Braid DB/path、runtime 和 service；写保护清单，不迁移。
2. 给 45 GiB 快照补逻辑大小、实际占块、inode、硬链接/重复摘要、telemetry signal 和派生物统计口径；生成只读 GC plan，apply 为空。
3. 固定 archive level、host reserve、每类预算字段和 `archive.json` 回执语义；同步技术说明、运行说明和当前 task packet。

### I12 完成后

1. 建立稳定资产目录，重建控制器 venv/runtime/Runner/cache；新入口切换后用实际 command、handler、mount 和 manifest 核实不再依赖旧 attempt。
2. 先修输入/package/runtime/cache 的共享与依赖记录，再修完成 finalizer；此时仍不自动删历史数据。
3. 修 telemetry producer 的重复 evidence 模型，限定普通 run 的长期 OTLP；随后才启用 archive level 的裁剪。
4. 实现只读 GC report，使用现有历史样本和 I12 保护清单核对；再启用有 plan identity 的 apply。
5. 按 archive receipt 迁移历史：保留一份 package/application/input、必要 native/Braid/score；派生和逐字节重复优先回收。每批保存释放前后字节/inode和 tombstone，不改写历史运行事实。

### 需要 WSL 停机

1. 确认 I12 与全部容器/WSL 进程已终止且归档可用。
2. Docker daemon 重启以应用日志上限；按记录处理 Factory 自有的残留对象。
3. fstrim 后 shutdown WSL，执行 Windows 侧 VHDX 物理压缩。
4. 分别记录 ext4 可用空间、Docker 占用和 VHDX 物理大小；三者不能合成一个“清理成功”字段。

## 验收方案

遵守仓库规定，不新增或运行 Factory、Braid 或实验基础设施测试，不把测试改名为 probe/self-check。实施后的证据来自静态核对、实际操作、磁盘/制品观测和另行获授权的实验。

1. **静态依赖核对**：枚举新运行的 command、resource handlers、shebang、mount、service state、runtime/package manifest、recovery 请求；不存在 attempt-local runtime/venv/Runner 隐藏引用。
2. **I12 安全**：GC plan 将两题暂停容器、restart workspace、shared submission、Braid/Console/watcher 依赖列为 protected 并指明消费者；provenance-only 的旧 source 不永久 pin workspace。
3. **共享资产实际操作**：连续准备两个相同输入/包的 plan，核对内容身份相同且只有一个权威物理对象；run 的可变 workspace、日志和 state 仍独立。失败构建不发布半成品。
4. **归档实际操作**：对一个已完成历史副本运行 finalizer，应用结果不变；`archive.json` 可重算哈希，明确 archive level/gaps；decision 归档可由现有查询读取，replayable 归档可用既有 packager 生成相同应用摘要。
5. **恢复实际操作**：只有当该 run 声明 resumable 且另获授权时，从隔离目录恢复；核对 online DB backup、Git bundle/patch、未提交文件、native/runtime 身份属于同一检查点。能解压不算恢复验收。
6. **telemetry 成本**：同一内容未变化时不重复发送大 artifact；普通 decision run 的 telemetry 不再随周期性完整 native 快照线性增长。保留 traces/metrics/errors/usage/timing 和 gap；forensic 模式仍可取得完整原始 OTLP。
7. **预算与停止**：在下一次获授权实验中记录 preflight、实际峰值、80%/100% 动作和 host reserve；通过真实受限运行或自然阈值观测核对停止入口，不伪造模型结果。远端仅停止本地下载，不盲目取消平台 run。
8. **GC 实际释放**：plan/apply identity 一致；删除前后核对内容摘要、`df`、inode、Docker 占用和打开但已删除文件。删除对象均有替代或明确放弃；失败保持可恢复隔离状态。
9. **跨机身份**：任取一题，从官网 platform run 追到 submission、package SHA、application 算法+摘要、来源 lab/Braid/native、原始 status 和 archive location；把归档复制到另一主机后逻辑身份不变，绝对路径只作为旧位置记录。

## 待用户复核的产品决定

推荐 Factory 的普通实验默认使用 `decision` 级：长期保留一份冻结应用/replay 能力、Braid DB/必要 state、关联 native 原文、原始评分与错误；不默认保留完整 OTLP、整棵 workspace 和可重建分析投影。`resumable` 与 `forensic` 必须在每轮 packet 中明确选择并给预算。

如果用户认可这一默认值，下一阶段才细化文件级实施计划和独立预演，并在开工复核中列出源码、文档、历史迁移与实际验收范围；本阶段不实施。
