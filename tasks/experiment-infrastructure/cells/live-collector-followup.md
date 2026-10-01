# attempt-07 Collector 的有界取证

2026-09-28，先只读核对 WSL 两题已有的 `telemetry.sqlite`、`braid-state/telemetry-errors.jsonl`、run-local monitor 源码，以及本地现有 Collector/SDK 源码；随后仅在本地 [lab/otlp.py](../../../lab/otlp.py) 实施请求计时。没有改动运行或容器，没有读取凭据、原生长轨迹，没有运行 Factory/设施测试、探针或负载。本页的运行观测仍来自实施前的 attempt-07，不能用来验证新计时。

结论：**30 秒 capture、4 GiB / 2 CPU 环境下，SDK flush 超时仍复现；当前证据不足以确定是接收、纯 Python 解码、SQLite 提交还是 SDK 导出队列等待。** 应先给现有 Collector 日志增加请求阶段耗时，不继续凭单批条数或内存额度调阈值。

## 恢复后的实际窗口

两题 DB 都带有旧恢复来源的多个 collector session。下表严格选 `sessions.opened_at` 最新 session，再按 `batch_meta.session_id` 统计批次；producer 错误只计该 session 开始之后的记录。没有把历史累计 74/102 条错误算成本轮结果。

| case | 新 session / 开始 UTC | 本次观察 UTC | logs 批次 / 原始字节 / 单批最大 | metrics / traces 批次 | 新 producer capture 错误 | receive_errors |
| --- | --- | --- | --- | --- | ---: | ---: |
| GitHub | `581ab6669077263aef7f95dd` / 05:32:35.806 | 05:53:56.050 | 63 / 51,324,607 / 5,987,587 | 21 / 15 | 1 | 0 |
| Sheet | `9c9863a4ba1c0d90933a57fe` / 05:33:16.893 | 05:54:01.682 | 111 / 156,788,056 / 7,352,871 | 20 / 127 | 3 | 0 |

最新会话已接收日志均为 `encoding=identity`，wire bytes 与 payload bytes 相等，因此 gzip 解压不是这些批次的耗时来源。两题 `telemetry-collector.log` 在该截面均为 0 字节。此前相邻截面的 batch SHA-256 重复计数为 0；这不证明记录级无重发，因为重发的 OTLP 时间戳、组合与批次边界可以变化。

本轮四次错误均为 `final_capture=false`，也没有本轮 `DiagnosticClient` 的 HTTP/reqwest 错误记录：

| case / UTC | pending records | force_flush 等待 | capture 总耗时 |
| --- | ---: | ---: | ---: |
| Sheet 05:37:33.833 | 13 | 5000 ms | 5194 ms |
| Sheet 05:50:37.107 | 53 | 5000 ms | 5241 ms |
| GitHub 05:51:45.787 | 21 | 5000 ms | 5104 ms |
| Sheet 05:51:54.783 | 53 | 5000 ms | 5443 ms |

所以原先“Sheet 只有一次”的 05:43 截面已被后续事实更新。这里的 pending 是 EvidenceWriter 自己在上次 flush 后 emit 的计数，不是当前 HTTP 请求内记录数，也不等于 SDK 队列深度。

## 现有时间戳能说明什么

围绕错误时刻，仅按批次元数据查看 ±8 秒窗口，没有解码 payload：

- Sheet 首次错误前有 logs batch #896，`received_at=05:37:28.833`、528,505 B；后续 traces #897 在 05:37:38.055 记录。
- Sheet 第二次错误前有 logs #1065（05:50:32.066、1,452,585 B）和 #1066（05:50:36.885、734,233 B）。
- GitHub 错误前有 logs #567（05:51:40.789、1,072,368 B）。
- Sheet 第三次错误前有 logs #1093（05:51:49.388、1,944,400 B）和 #1094（05:51:53.076、799,497 B）。

这些批次最终可从 DB 读到，且接收后仍有其它信号继续入库。但 [lab/otlp.py](../../../lab/otlp.py) 在完整读取 body、解压/解码验证之后，才在 `INSERT batches` 参数中取 `time.time()`；该字段既不是 HTTP 请求到达时间，也不是 commit 完成或响应发出时间。没有 producer request ID 与 flush 的精确关联，不能把上述相邻 batch 宣称为某次 flush 唯一对应的请求，更不能由“超时前五秒有 received_at”反推 SQLite 花了五秒。

## 源码中的可证机制与未证瓶颈

本地实际 `opentelemetry_sdk-0.32.1/src/logs/batch_log_processor.rs` 的 `force_flush()` 向后台线程发送 ForceFlush，然后 `recv_timeout(self.forceflush_timeout)`；构造器将该回执等待固定为 5 秒。它的 Timeout 不等于 HTTP 请求报错或取消正在进行的后台导出。[Braid telemetry.rs](../../../sources/braid/src/telemetry.rs) 已分别记录 transport 原因与 capture/flush 时间：本轮只见后者，不能把旧 run 的 reqwest timeout 混入本轮。

同一文件的 EvidenceWorker 每 30 秒采集，任何 capture/flush 失败会新建 EvidenceCollector，丢弃其增量记忆；下一次 capture 因而重发此前来源。这是潜在流量放大机制，不是由本次 batch hash 就能量化出的重复比例。

Collector 使用 ThreadingHTTPServer；随包 `otlp-deps` 存在时强制 `PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`。每个 POST 完整读取 wire，验证完整 protobuf envelope，然后连接 SQLite、计算 payload SHA-256、写入 batches/batch_meta、提交，最后响应 200。SQLite 写事务及 Python 解码都是需要判别的候选；pure-Python/GIL 与数 MB 批次能形成解释，但本轮没有 CPU、阶段时间或请求并发证据，不能将候选写成已确认瓶颈。64 条 flush 阈值、13 条 pending、4 GiB / 2 CPU 都不足以单独解释五秒等待。

## 已实施的最小计时（待后续包实际运行）

现有 Handler 的每个 POST 在结束时向 stderr 写一条 `event=otlp_request_timing` JSON，沿用 [start_local_telemetry](../../../scripts/agent_support.py) 收集的 `telemetry-collector.log`。`started_at`、`finished_at` 是 Unix wall time 秒，供与 producer 错误窗口对齐；`read_ms`、`decode_ms`、`persist_ms`、`response_write_ms`、`total_ms` 使用 monotonic 时钟。`persist_ms` 覆盖当前 SHA-256、两次 INSERT 和 `connect` 退出时的 commit；`response_write_ms` 覆盖本地响应构造与写出，不代表客户端已收 ACK。

每条还含已匹配的 `session_id`、`signal`、实际 `wire_bytes`/`payload_bytes`、HTTP 状态，以及成功提交后才填的 `batch_id`；`failure_stage` 指明拒绝或异常所在阶段。未走阶段为 `null`，已进入但失败的阶段仍有耗时。原有 `receive_errors` 写入与错误响应保持原样；计时输出失败不会改变接收结果。不另建表或日志框架，不通过第二次 SQLite 写入测量 commit，不记录 token、headers、payload 或错误正文。当前只完成本地 Python 编译检查，未在 attempt-07 部署或用负载验证。后续以自然运行取得数据：decode 占主导才讨论解析成本；persist 占主导才拆分 hash/锁等待/commit；Collector 很快完成而 SDK 仍超时，才继续检查生产者导出排队/回执。当前不调整阈值，不取消正确性验证。

## monitor-generation 的取消退出

已直接读取 attempt-07 的 `monitor-generation.py`。当前代码将逐题 `cancelled/finished/interrupted` 视作终态，外层 `execution.phase=cancelled` 也使循环退出；因此主线所做的本地修正已在文件中。此次没有动 PID 243060 或已停止的 attempt-06 PID 199628，也没有重启监控。

在当前仓库 `lab/`、`scripts/`、`agents/` 中没有找到生成或共享维护 `monitor-generation.py` 的源码入口；它是 attempt-local 文件，部署文档只是接续说明。现有 [lab/wait.py](../../../lab/wait.py) 已识别 `completed/failed/interrupted/finished/cancelled/lost` 并结束等待，可复用做终态等待；它不等价于当前 monitor 附加的 Braid 计数与 native mtime 采样。[lab 的 wait 子命令](../../../lab/__main__.py) 另有 controller 事件等待，不应与上述模块混称为一个入口。当前没有必要再造监控框架。run-local monitor 仍把逐题取消映射成 `state=failed` 并可能返回 1，属于摘要语义，已经退出不代表摘要准确；后续若收敛脚本，应保留原 phase，复用既有终态契约。

## 原始位置

WSL 根为 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/`：

- GitHub：`pi-braid--hackathon--github-116b6cbc63dc5c/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/`
- Sheet：`pi-braid--hackathon--sheet-28ca9afab308e8/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`

各内层根读取 `telemetry.sqlite`、`braid-state/telemetry-errors.jsonl` 和 `telemetry-collector.log` 文件大小；数据库以 `mode=ro` 打开，最终统计在单次只读事务内固定。monitor 文件位于同一 attempt-07 根。恢复前错误按最新 collector session 开始时间排除；运行仍在变化，本页不代表终态完整性或应用验收结果。
