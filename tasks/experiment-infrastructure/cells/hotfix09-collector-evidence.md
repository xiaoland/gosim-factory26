# attempt-08 Collector 阶段计时的真实窗口

2026-09-28 只读核对 WSL attempt-08 GitHub、Sheet 的 `telemetry-collector.log`、`braid-state/telemetry-errors.jsonl`、`telemetry.sqlite`。截面止于约 07:24 UTC，运行仍在变化。按各题最新 `sessions.opened_at` 选本轮 collector session，仅计该 session 开始后的 producer 错误；数据库查询只读，重复性检查仅在指定错误附近解码 OTLP 日志并提取 `record_id`/`event_kind` 聚合，不输出原始 payload。没有改源码、运行或容器，也没有执行 Factory 测试/模拟负载。

## 阶段分布与错误

| case / 本轮 session 开始 UTC | 已记录 POST | HTTP 200 / receive_errors | 总量与最大 wire batch | total p50 / p95 / max | persist p50 / p95 / max | read p95 / decode p95 / response p95 | 本轮 `Timeout(5s)` |
| --- | ---: | --- | --- | --- | --- | --- | ---: |
| GitHub `7b503b7e63e2c646043374f0` / 06:43:33.855 | 161 | 161 / 0 | 81.0 MB / 7.44 MB | 883 / 3277 / 8028 ms | 882 / 3268 / 8027 ms | 0.65 / 4.57 / 0.25 ms | 3 |
| Sheet `41f7d88b13783b9d3b3b1f27` / 06:44:22.007 | 400 | 400 / 0 | 362.8 MB / 7.71 MB | 937 / 3497 / 8299 ms | 918 / 3393 / 8297 ms | 3.11 / 82.75 / 5.07 ms | 6 |

时间为本轮每个 POST 的 nearest-rank 分位；阶段耗时来自新 `otlp_request_timing` stderr JSON，不是 `batches.received_at` 推算。所有计时行都为 HTTP 200、`failure_stage=null`，`batch_id` 对应最新 session 的 `batch_meta`：GitHub 161 批、Sheet 400 批。它证明这些请求最终完成，**不证明 producer 的所有记录无损**。`receive_errors=0` 只说明 Collector 未记录拒绝/持久化错误；九次 producer `force_flush` 等待超时仍发生，且 SDK 超时不必取消后台导出。

在这两个真实窗口中，常规请求主要耗在 `persist_ms`：GitHub 161 笔仅 2 笔、Sheet 400 笔有 7 笔 `total_ms>=5000`；请求大小不是充分解释，GitHub 4,045 B metrics 曾耗 4,931 ms（persist 4,929 ms），Sheet 3,159 B metrics 耗 5,890 ms（persist 5,888 ms），Sheet 481 B logs 耗 4,267 ms。也不能将所有慢请求直接归为 SQLite 写入：Sheet 07:13:23 的 4,498 B metrics 解码耗 5,525 ms、persist 1,274 ms、总计 6,800 ms。`persist` 当前还合并连接/锁等待、SHA-256、两次 INSERT、commit 与 close；日志没有拆分这些分量，不能据此断言是 fsync、锁或文件大小中的哪一个。

producer 错误均为非终态 `evidence flush`，pending 记录数不是 HTTP 批量大小。GitHub 分别在 07:10:48（5 条）、07:11:26（64 条）、07:19:35（14 条）报错；Sheet 在 06:50:04（33）、06:55:25（29）、07:11:14（39）、07:12:29（64）、07:13:29（64）、07:14:55（64）报错。九次回执等待均约 5 秒，但 capture 总耗时从 5.2 秒到 56.4 秒，说明超时之前也可能在采集或此前批次花费时间。几个可区分的时间重合：

- GitHub 07:10:48 超时窗口覆盖 07:10:43.268–07:10:51.295 的 logs POST，153,547 B，`persist_ms=8027`；07:11:26 又覆盖 07:11:21.575–07:11:27.322 的 304,641 B logs POST，`persist_ms=5743`。长持久化请求足以参与回执延迟，是明确的相关性；没有 producer request ID，不能把它们认作唯一对应批次。
- GitHub 07:19:35 超时时，邻近两笔 logs POST 各耗 3443/1620 ms，且第一笔在错误前完成；Sheet 06:50:04 的相邻两笔各约 3914/2094 ms。单笔 HTTP 超过 5 秒并非每次超时的必要条件，后台队列、多个请求串行和 SDK 回执等待仍未被排除。
- Sheet 07:13:29 错误附近的 4,498 B metrics POST 总计 6800 ms，其中 decode 5525 ms。这提示该时段可能有解释器调度/CPU 争用或解码暂停，但缺少 CPU 与请求排队证据，不能将它写成已证根因。

## 失败重置后的重复发送

现有 `sources/braid/src/telemetry.rs` 在 capture/flush 失败后重建 `EvidenceCollector`；`sources/braid/src/evidence.rs` 中 `emitted` 去重集合随之清空，下一轮会再次发送旧来源。真实数据提供了有界的正例：只比较同一最新 session、错误前后指定窗口的 `record_id`，不比较全库 payload。

| case / 错误 | 错误前窗口 logs | 错误后窗口 logs | 前后相同 `record_id` |
| --- | --- | --- | --- |
| GitHub 07:10:48 与 07:11:26 | 首次错误前 120 秒：4 批、0.95 MB、23 个唯一记录 | 第二次错误后 30–120 秒：10 批、20.65 MB、408 个唯一记录 | 3 个 `evidence_chunk` |
| Sheet 06:55:25 | 错误前 90 秒：8 批、7.09 MB、102 个唯一记录 | 错误后 30–120 秒：30 批、50.74 MB、1250 个唯一记录 | 3 个 `evidence_chunk`、2 个 `evidence_artifact` |

单个 collector 正常运行时 `emitted` 会压住同一 ID 再发，因此前后相同 ID 是重置/重发的直接证据；错误后流量尖峰与源码机制相符。**不能**把 20.65/50.74 MB 全算成重复：部分是错误后新增或变化的来源。整批 `batch_meta.sha256` 在两题全库均未出现重复，也不能据此否定记录级重发，因为同一个 OTLP 批次可混入新记录、换时间戳和边界。是否有未送达记录、重复字节的总量和最终完整率，在当前材料下仍未知。

## 现有设施下一步能回答什么

新阶段计时已经把常规瓶颈缩到 `persist` 的大范围，并定位一次异常 `decode`；它没有把 producer 的 `force_flush`、SDK 队列、HTTP 请求和 Collector 的 `batch_id` 连成一条可核对链。现有日志可凭 wall time 做窗口相关性，不能证明某次回执等了哪笔请求；Collector `total_ms` 从进入 handler 算起，不包括 producer 队列/网络前段，也不证明客户端收到 200。若需判定修复位置，最小补证据应在既有日志边界拆开 `persist` 的连接/等待、hash、commit，并给 producer 导出批次一个可贯穿的关联标识或等价回执；在此之前不依据 `receive_errors=0`、批次 SHA 或单次慢请求断言无损/唯一根因。阶段计时目前只在单独 stderr 日志，现有数据库/分析页没有直接并列 producer 超时、每阶段分位与重置后的记录级重复，复核必须人工跨文件对时；这也是当前设施最具体的观察缺口。

本次原始路径根为 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/`；GitHub 子目录为 `pi-braid--hackathon--github-97914b9e3158cf/workspace/official-generation/template/.factory26/20260928-030347-78b10c07/`，Sheet 为 `pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`。每个子目录内读取上述三份 telemetry 材料。

## 09 的 Braid 侧最小修复与边界

本地锁定的 `opentelemetry_sdk 0.32.1` 的 `BatchLogProcessor::force_flush` 控制回执固定等待 5 秒；超时不会取消 worker 已开始的导出。SDK `emit` 使用有界队列 `try_send`，满队列时可丢弃日志；自动 batch 导出也可能先于后续 flush 发生。它不提供逐条可靠交付回执，因此本修复只按**上一次成功 flush**划重试窗口，不把 flush 成功描述成逐记录已持久化。

已在 `sources/braid/src/evidence.rs` 为 `EvidenceCollector` 记录自上次成功 flush 以来新发的 ID；`sources/braid/src/telemetry.rs` 的每 64 条自动 flush 和每轮 capture 末尾 flush 成功时清空此集合。任一 capture/flush 失败时，仅从已发去重集合移除这段窗口内的 ID，下轮重新计算源并重发这些记录，不再重建 collector 丢掉整个历史。`native_artifacts`、`artifacts`、`session_usage` 都是单轮局部变量，没有另一增量游标需要回退；原有结束时最终 capture 保持。64 条阈值未改：现有数据不足以判定改成更小批能降低总负载，改阈值还会增加 flush 次数。

针对性 Rust 测试模拟中间一次成功 flush、随后失败、重试与再次成功：先前成功段不再发，失败段会重发，之后也不重复。`rustfmt --check` 和 `cargo test -q failed_flush_retries_only_records_since_last_success` 已通过；没有执行 Factory/设施测试，也未将本地源码部署到正在运行的 attempt-08。SDK 队列满时静默丢弃、传输失败与 5 秒回执超时仍是底层限制；这项修复减少失败后重复放大，不提供此前不存在的端到端无损保证。
