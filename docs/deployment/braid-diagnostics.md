# Braid 诊断

Braid 通过 OTLP traces、logs 和 metrics 保存运行与协作证据。Factory 包内 Collector 通常将三信号写入 `.factory26/<run>/telemetry.sqlite`；旧运行可能使用外层数据库。采集错误位于 `telemetry-collector.log`、`telemetry-export.log` 和 `braid-state/telemetry-errors.jsonl`，具体覆盖以实际包和原件为准。

## 生成诊断网站

在仓库根目录构建本机 Braid，然后从已有 Backend 生成新网站。Mac 的 Cargo 缓存、target 和临时目录先按[开发工具说明](../../tooling/scripts/README.md)设置到 WorkSSD。

```sh
cargo build --locked --manifest-path sources/braid/Cargo.toml
make braid-report RUN=runs/EXPERIMENT OUTPUT=runs/EXPERIMENT/analysis/SITE
```

`OUTPUT` 必须不存在；打开其 `index.html`，或交给静态服务器。网站保存批次截止点和解释器身份，不轮询平台，也不会启动模型或补发遥测。多个 Braid run 时用 `BRAID_RUN_ID` 选择内层 ID。完整脚本入口为：

```sh
python3 -m lab.analysis.braid_telemetry_viewer RUN \
  --output OUTPUT --braid /absolute/path/to/braid
python3 -m lab.analysis.native_profile GENERATION_RUN \
  --output runs/analysis/profile.json
```

主 CLI 当前不提供 `lab telemetry` 子命令；数据库导出与选择参数从上述分析模块和 [Braid CLI](../../sources/braid/README.md)查询。Linux 打包二进制不能直接作为 macOS 诊断工具。

## 原始材料与排障

| 材料 | 用途 |
| --- | --- |
| `batches.json`、`otlp/` | Backend 实际返回的批次、信号与字节数 |
| `decoded.json`、`decoded.stderr.log` | protobuf 解码、resource 与内层 Braid 身份 |
| `reconstruction.json`、`evidence/manifest.json` | 快照选择、摘要校验、缺分片与关联缺口 |
| `evidence/messages.jsonl`、`native-*.jsonl` | 保存且通过核对的原生记录 |
| `profile.json` | 模型 usage、会话时间与缺失字段 |
| `source-errors/` | 当前生成目录中的 exporter、Braid 和 runner 原始错误 |

没有 Braid resource 时，先检查批次、解码错误和源端传输；variant 名不能证明有遥测。partial 需要逐项读取 manifest 的 gaps，不能用网页生成成功推断源材料完整。摘要批次不含原文，只有 portable evidence 可以重建完整内容；导出时不能丢掉 logs 或分片时段。解码器按 `-logs.pb`、`-traces.pb`、`-metrics.pb` 后缀区分 schema。

源端 HTTP 403、超时或归档失败保留具体状态与响应。只有原 state/native 仍在，且有正确 Collector endpoint 和有效鉴权环境时，才可补采：

```sh
braid telemetry export --state /absolute/generation/braid-state \
  --native-manifest /absolute/generation/telemetry-native.json
```

命令消费标准 `OTEL_EXPORTER_OTLP_*` 环境变量，不在参数中传凭据；它不会重启 Collector 或绑定另一个 run。补采不会补造历史实时 span，也不改变应用终态。

## 解读限制

Pi token 数来自 assistant usage，按原生消息身份去重；请求未结束、usage 缺失或账单未知时保留未知。累计工具、模型和并行任务耗时不能相加当总墙钟，首增量延迟也不是服务端推理时间。恢复后分析需明确当前 producer 与完整原生会话的范围，不能把旧运行费用计入新 run。

资源样本是执行容器可见的 cgroup/proc 事实。OOM 计数增量不能单独确定被杀进程，成功发送信号也不证明死亡原因；平台宿主和隐藏祖先的证据仍需平台提供。遥测完整性、应用完成与官方评分分别判断。

网站可能包含会话与工具原文，分享前检查批次和下载文件。整站数据嵌入 HTML，会受浏览器内存限制。修改展示可用已有真实归档生成新目录核对；早期源码或报告中的局部反馈不代表每个版本和环境均已完成验收。
