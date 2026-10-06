# 观测、资源采集与 Exp Console 实施边界

本 cell 将观测方案收敛到主 design 的目录、入口和职责。只记录源码证据、实现文件映射和生命周期边界；执行控制由 execution owner 负责，Braid 语义由 `sources/braid` 负责。

## 已核实的现状

| 能力 | 事实来源 | 采用决定 |
| --- | --- | --- |
| OTLP 接收 | `lab/otlp.py` 的 `initialize`、`list_batches`、`read_batch`、`list_receive_errors`、`export_batches`、`serve_run`；已有三信号 protobuf/gzip、批次分页和错误表 | 保留原始 batch/error 语义，在 `lab/backend.py` 增加 manifest 身份、查询和幂等导入 |
| 资源采集 | `scripts/agent_support.py:ResourceEvidence`；`scripts/execution_bootstrap.py:resource` 建立并采样；`lab/exp/runner.py` 调用 bootstrap 的 resource/collector | 资源采集归 bootstrap/runner，不归 `lab/otlp.py`；保存到 `records/telemetry`，缺失保持 unknown |
| Braid evidence | `sources/braid/src/evidence.rs` 已有 `decode`、`reconstruct`、`render_markdown`；`lab/analysis/braid_telemetry_viewer.py` 当前只是 Python 离线整站编排 | Braid 的 view/projection 编排移入 `sources/braid`；Factory 只调用固定处理入口、读取已物化投影和通用摘要 |
| 当前 Lab CLI | `lab/__main__.py` 仅转发历史 `lab.exp.__main__`；后者是旧 experiment/attempt reader 与控制入口 | 新 `start/stop/pause/resume/restart/status/logs/evaluate/archive/serve` 注册在 `lab/__main__.py`；不向旧 `lab.exp.__main__` 增命令 |
| 当前 Console | `braid-console/server.py` 的 API 依赖 registry、Braid CLI、live/archive reader | 新 Console 只读共享 Backend；旧 CLI/live/control 路径不接入新链路 |

纯 Pi-only 没有 Braid 对象是合法变体；只有 manifest 明确存在 Braid binding 且收到 `service.name=braid`、`braid.run.id` 时才挂载 Braid 页面。

## 规范目录与归属

每个 run 固定为：

```text
run/
  manifest.json
  program/                 variant、状态脚本、角色技能和依赖入口（只读）
  inputs/                  task 需求与显式公开反馈（只读）
  data/
    workspace/             完整生成工作区与 Git
    harness/               native home、Braid DB/worktree 等可写状态
  records/
    status.json            lifecycle 执行事实 + variant activity brief
    logs/                  入口、工具、gateway、平台原始日志
    telemetry/             OTLP batch/error、ResourceEvidence、coverage
    cost/                  provider/ARC/platform receipt 或 estimate
    evaluations/           本 run 的评测关系和摘要
    platform/              平台状态与控制响应
  snapshots/               data 快照和独立 application 快照
  evaluations/             评测 run 引用与报告
```

共享 Backend 的 SQLite 位于独立 service root，不属于任何 run；Hosted 的 SQLite 位于该 run 的 `records/telemetry/`，只负责接收和落盘，终态再导入 Backend。`restart` 只迁移 `data/`，不复制 `records/`、进程句柄、服务地址、凭据、费用或遥测；因此遥测不会被当成新 run 的新费用。新 run 的 manifest 记录 `source_run` 与选用 snapshot，原始 Docker/Hosted/native/provider 身份及已发生请求仍只作为 manifest/records 事实保存，不再建立额外 bindings/receipt/sha 目录层。

## `lab serve`、Backend 和 Hosted 接收

### 唯一入口

在 `lab/__main__.py` 注册：

```text
python3 -m lab serve --config CONFIG
```

`CONFIG` 只声明 service root、监听地址、静态 UI 构建目录、Backend SQLite、访问凭据和导入目录。`lab/serve.py` 是唯一常驻进程，提供静态 UI、Collector HTTP 接收和 Backend API；不再分别启动 `braid-console/server.py`、`lab/otlp.py --serve-run` 或第二个查询服务。旧 `lab.exp.__main__` 只保留历史 reader/兼容入口。

Hosted 不获得新的用户 CLI：Hosted 装配器直接调用 `lab/backend.py` 的接收落盘核心，写入 `records/telemetry/`，由外层回收后使用 Backend 的导入 API/函数导入。Hosted 不挂 UI、查询 API 或完整服务生命周期。

### 固定模块职责

- `lab/backend.py`：共享 SQLite schema、manifest 身份注册、OTLP 三信号写入、`receive_errors`、bounded 查询、Hosted batch/artifact 幂等导入、coverage/cutoff。每个写入事务短；冲突原件保留并返回具体错误。
- `lab/serve.py`：读取 config，启动一个 HTTP 进程，挂载静态包、`/v1/traces|logs|metrics` 接收端点和 `/api` 查询端点；不解析 Braid 私有 DB，不执行 live CLI。
- `lab/otlp.py`：保留 protobuf/gzip 解码和现有 batch 低层读写，作为 `lab/backend.py` 的协议/存储基础，不再承担资源采样或完整服务入口。
- `scripts/execution_bootstrap.py`、`scripts/agent_support.py`、`lab/exp/runner.py`：继续负责执行域资源采样、collector 生命周期和运行侧落盘；输出迁移到规范 `records/` 路径。
- `braid-console/web/`：编译静态 UI；不再依赖旧 Python Console 的 live CLI/runtime/control 路由。

Collector 按 manifest 的 run token/原始身份写入 Backend；服务不扫描目录猜 run，也不把 Backend 可达当作生成 gate。断连时运行侧继续保存 `records/telemetry/` 原件，导入按 manifest 和 batch identity 幂等。

### 通用 API

| 路径 | 返回 |
| --- | --- |
| `GET /api/runs` | 默认列 `not archived AND lifecycle != completed` 的 brief；`all=1` 包含完成和归档项 |
| `GET /api/runs/:run` | manifest、lifecycle/execution、`records/status.json`、资源/日志/费用/评测摘要、as_of、coverage/gaps、原件链接 |
| `GET /api/runs/:run/resources?after=&until=&limit=` | bounded ResourceEvidence 和 latest/status，不读取 live cgroup/proc |
| `GET /api/runs/:run/logs?stream=&cursor=&limit=` | 有界已落盘日志片段/索引，不无限跟随活文件 |
| `GET /api/runs/:run/cost?scope=&cursor=&limit=` | receipt 或带 source/kind/currency/as_of 的 estimate；缺失为 unknown |
| `GET /api/runs/:run/evaluations` | 评测 run、评测器自有 lifecycle/score/cost/result 原件；不套生成 variant 的 idle 规则 |
| `GET /api/runs/:run/artifacts/:id?offset=&bytes=` | manifest 登记的受限原件读取，不接受任意路径 |
| `POST /api/import` | Hosted records/telemetry 导入回执；幂等成功、冲突或具体错误，不启动或控制 run |
| `GET /api/runs/:run/braid/*` | Braid-owned viewer 挂载的 bounded projection、sessions/turns/objects、正文 artifact 分页、coverage/gaps 和原件链接 |

`status`、Console 列表和详情消费同一 `records/status.json`。lifecycle/execution 是执行事实，activity 是 variant 脚本判断；例如 `running/stalled` 分开展示，脚本失败为 `activity=unknown` 并保留原错。正常 score=0 仍是 completed。archive 只影响默认列表，不删除或停止结果。

## Braid-owned view 的生命周期

当前 Python viewer 的调用事实是：`database_for_run` 选 Backend，`list_batches` 固定 cutoff，复制 batch，执行 Braid `telemetry decode`、`telemetry reconstruct` 和 `render-markdown`，再读取 native profile。它不能原样成为页面请求处理器：按页面 limit 截断输入会丢失跨 batch 的 evidence/artifact/native 上下文；每次轮询整库重建也违反 bounded 查询。

采用以下明确边界：

1. 在 `sources/braid/viewer/reader.py` 实现 Braid-owned reader、projection 和查询；`sources/braid/viewer/web/` 持有 Braid view 页面。Factory 不复制 turn、session、object、Portable 或 native 语义，只挂载该处理入口和通用 run 上下文。
2. Backend ingest 的新 batch 触发一次后台 materialize，最多每 30 秒、且有新数据时选择固定 cutoff；同一 run 的重建不重叠。reader 按 run 顺序累计已解 records，保留 Portable chunks、artifact manifest、source gaps 和跨 batch 上下文，原子发布新的 projection/as_of/error。不能按 HTTP page limit 截断 reconstruct，也不建立新的 Rust 增量持久状态系统或独立微服务。
3. `sources/braid/src/evidence.rs` 仅窄调整，拆出接收已解 records 的 `from_records` 重建核心；已有 protobuf 输入路径先 decode，再复用该核心，避免每个新增 batch 重复 protobuf 解码。`sources/braid/src/cli`/`src/main.rs` 增加已解 records 参数入口，供 `viewer/reader.py` 的固定处理入口调用；跨 batch 的状态和投影仍由 Braid Python viewer 管理。
4. 正文按已发布 artifact link + offset/bytes 分页；Markdown 只在用户请求 bounded 正文时渲染。HTTP 只读已发布 projection/as_of/error 和受限原件，不执行 live CLI、不打开 live Braid DB。缺失原件、reconstruct gap、reader/CLI stderr 原样进入 error/coverage，不能变成空列表。
5. `lab/analysis/braid_telemetry_viewer.py` 降为离线导出薄适配器，调用 `sources/braid/viewer/reader.py` 和 `web/` 数据，不一次性嵌入全部正文/Markdown；Console 请求不调用该旧模块。

Factory 的 `/api/runs/:run/braid/*` 只挂载 Braid viewer 的已物化 projection、来源/observed-at、coverage/gaps 和受限原件链接。Braid 拥有协作语义与视图，Factory 只提供 run 上下文、通用列表/资源/日志/费用/评测查询和静态页面入口。Pi-only 不调用 Braid materializer。

## 状态、评测与 restart 边界

- status producer 由 execution owner 放入固定 variant 程序，观察循环写 `records/status.json`；其中包含 lifecycle 执行事实、activity 判断、来源、`as_of` 和具体原错。CLI/Console 不各自远端轮询或另写健康状态机。
- 三类自动评测由唯一普通 Python 程序启动：自管执行宿主直接运行，Hosted 包外程序负责启动/回收。评测 run 使用自己的 evaluator status，不套生成 variant 的 native turn/idle 规则。
- `restart` 是同 variant 新 run：只迁移来源 run 的 `data/` 快照，重新装配当前同名 variant/program，写新 manifest/source snapshot；不迁移 records/telemetry/cost/evaluations。删除 extract/take 及多路径提取接口。
- `pause`/`resume` 作用于同一 run，由 target/variant 声明能力；Hosted 不宣称 pause/resume。跨 variant 接续不进入本方案。

## 明确文件映射

| 文件 | 实施责任 |
| --- | --- |
| `lab/__main__.py` | 注册 `serve` 及新 run 命令；旧 `lab.exp.__main__` 不增新命令 |
| `lab/backend.py` | 新共享 SQLite Backend：接收、bounded 查询、manifest 身份、Hosted 导入、cutoff/coverage、Braid materializer 调度 |
| `lab/serve.py` | 唯一 `--config` 常驻服务：静态 UI、Collector、Backend API；不含 Braid 私有解释 |
| `lab/otlp.py` | 保留/复用低层 protobuf/gzip/batch 读写；删除其作为独立用户服务的角色 |
| `scripts/execution_bootstrap.py`、`scripts/agent_support.py` | 资源采样、运行侧 collector 生命周期和 records 落盘；不把 ResourceEvidence 归属移给 OTLP |
| `sources/braid/viewer/reader.py`、`sources/braid/viewer/web/` | Braid-owned reader、projection、bounded 查询和 Braid 页面；由 Backend 显式装载 |
| `sources/braid/src/evidence.rs`、`sources/braid/src/cli`、`sources/braid/src/main.rs` | 复用已解 records 的窄重建核心及固定处理入口，不新增 Rust 增量状态系统 |
| `lab/analysis/braid_telemetry_viewer.py` | 离线导出薄适配器，消费 Braid viewer 输出，不作为 Console 请求处理器 |
| `braid-console/web/` | Factory 通用 run/resources/logs/cost/evaluations 页面和 Braid 入口，编译为 `lab serve` 静态包 |
| `braid-console/server.py` 及旧 reader | 保留历史兼容读取，不接入新 Backend/live CLI |

实施完成边界：`lab serve --config` 是唯一用户服务入口；run manifest 能定位 `program/inputs/data/records/snapshots/evaluations`；Backend 能 bounded 接收、查询、幂等导入并装载 Braid viewer；Braid viewer 在 ingest 后按固定 cutoff 有序物化跨 batch projection，HTTP 只读原子发布的 projection/as_of/error 和通用事实。生成不依赖 Console 在线，Hosted 不带 UI，restart 不复制遥测制造新费用。

## 依据

- `tasks/finals-experiment-loop/design.md`：规范目录、`lab serve --config`、restart/data-only、status/archive 语义。
- `lab/otlp.py`：现有 OTLP 低层接收、batch/error 表和分页读取。
- `scripts/execution_bootstrap.py:resource`、`scripts/agent_support.py:ResourceEvidence`、`lab/exp/runner.py`：资源与 collector 的真实归属和生命周期。
- `sources/braid/src/evidence.rs`：现有 decode/reconstruct/render 与跨 batch 重建所需 evidence/artifact 语义；窄拆 `from_records` 供 viewer 复用。
- `sources/braid/viewer/reader.py`、`sources/braid/viewer/web/`：Braid-owned reader、projection、查询和页面的目标归属。
- `lab/analysis/braid_telemetry_viewer.py`：当前整站导出链，作为待迁移的编排而非新服务 API。
- `lab/__main__.py`：新入口应落在这里，不扩展旧 `lab.exp.__main__`。
