# Playground API 与并发实验（2026-09-20）

本次在既有四组实验基础上补齐脚本化 Playground 操作，并实测比赛模型 API 与 WSL 独立评测的并发能力。没有重新生成应用、修改官方评测器或提交榜单。操作入口归属[运行文档](../../docs/deployment/index.md)，首轮模型成绩仍见[矩阵报告](2026-09-20-harness-matrix.md)。

## Playground 的实际执行

网站 `POST /api/auth/login` 接收 email/password，通过 Cookie 调用 `GET /api/auth/me` 验证登录。客户端使用 curl 保持系统 TLS 验证；凭据通过 stdin 或临时私有文件传入，不进入 argv。会话保存在仓库外的权限 600 文件，后续命令无需浏览器。

2026-09-20 通过 API 上传已授权的无模型探针，创建 submission `2e93a2fffe45` 和 run `23a11724c9f4`，需求为 playground catalog 的 `__demo__`。包 SHA256 为 `bb00c66fb97d4206daeedaebc49dcf24f17df334b446a2a50ce097019c5f3213`，与此前探针相同；没有传比赛模型密钥。实际验证了上传、创建、启动、状态、增量日志、traceability 和 commit history 接口。随后使用同一 submission 创建 run `eb84b5a05b52`，未重复上传，仍为 PASSED 1/1；复用运行也已通过 API 实测。

平台状态为 PASSED，首页测试 1/1 通过。started_at 至 finished_at 为 34.522 秒；API 的 run_duration_seconds 字段却返回 0，因此客户端终态摘要改用开始、结束时间计算 elapsed_seconds，并保留原始响应。日志有明确的 `FACTORY26_PROBE` 输出、Agent 成功退出、应用安装和构建、Playwright 执行与报告解析，证明不是只创建了一条成功记录。

| 云端观测 | 结果 |
| --- | --- |
| Python / 系统 | 3.12.3 / Linux x86_64 |
| os.cpu_count() | 16；未测容器 CPU 配额，不能据此声称独享 16 核 |
| 已有工具 | node、npm、git |
| 探针未发现的工具 | codex、pi、uv、cargo、bwrap |
| 缓存 | 使用已有 runner 镜像及镜像内 Playwright |
| 仍执行的准备工作 | Agent Python 依赖、应用前后端依赖安装和前端构建 |
| 评测 | 单 Playwright worker，首页测试 326 ms |
| 模型 | 0 次调用；占位符 Meter 认证 401 不构成模型计费验证 |

Demo 仅用于基础设施验证，不能当成 ARC-bench 分数或云端长任务吞吐依据。原始 12306 空白模板探针 `2041e4b58701` 自然结束，未调用 cancel；总历时 1526.067 秒（约 25.4 分钟），135 项均为 timedOut，每项约 10 秒。Agent 成功完成，失败发生在空白应用的评测阶段；这是探针结果，不是模型质量分数。两次 stdout 报告相同工具环境。四组本地 harness 还需要适配平台 Python main.py 入口、工具供应和 frontend/backend 部署契约；当前没有声称可直接上传开发仓库。

证据：`runs/playground/upload-20260920-162052-a95e63/submission.json`，`runs/playground/23a11724c9f4/{status.json,logs/,traceability.json,commit-history.json}`。平台响应的完整日志在 run 结束后才出现探针 stdout；运行时依赖 steps 和 runner_events 判断阶段，0/N 不足以判断测试停滞。

## 比赛模型 API 并发

从 WSL 向 `https://api.arc-bench.com/v1/chat/completions` 调用 `deepseek-v4-flash-vision-exp`，依次发送 2 路、4 路短请求。凭据经 SSH stdin 传入，没有写入 WSL 配置；请求无输出 token 上限、无重试。180 秒是本次短 HTTP 探针的传输超时，不是 Agent 生成上限。

| 同时请求数 | 成功 | 整批耗时 | 单请求耗时 | HTTP 429 |
| --- | --- | --- | --- | --- |
| 2 | 2/2 | 2.639 秒 | 2.194–2.638 秒 | 0 |
| 4 | 4/4 | 2.622 秒 | 2.116–2.621 秒 | 0 |

同组请求在约 3 ms 内开始，所有开始时间早于任一完成时间，确认客户端请求实际重叠。六次都是 HTTP 200、非空正文、finish_reason=stop；其中两次正文未精确匹配 OK，已单独记录，未用输出格式评价并发。总 usage 为 426 tokens。结果支持继续试用四路请求，不能据此推断主办方配额或长时间生成不会限流。

证据：`runs/concurrency/20260920-162142-probe-cd537313/probe.json`。只保留指标，不保留模型正文或推理内容。

## WSL 独立评测

官方固定评测器在 scripts/run-playwright.js 末尾追加 `--workers 1`，配置禁用 fullyParallel，静态审计也要求单 worker。测试会共享应用状态；直接提高同一服务的 workers 会改变实验条件。因此并发单位为独立评测任务，各有应用副本、服务端口、报告目录，评测器保持不变。Keep 冻结后评测不调用 LLM，其吞吐与模型并发分别测量。

主机为 wsl.win-ws.localhost，12 个逻辑 CPU、约 16 GB 内存。使用 Pi + SVC + braid 冻结应用 `20260920-141339-6138c072`，参考原始评测 `20260920-143117-15f133`：14/32，通过状态按 file/title/project 逐项比较；原始应用与参考报告不覆盖。批次开始前固定参考哈希，避免把后来的评测自动选作对照。复用既有 runner、node_modules 和 Chromium，应用自身在独立目录准备。

两路批次 `20260920-162142-eval-02da6657` 已完整结束：两份均为 14/32，64 项用例状态全部匹配参考，端口分别为 56985、35911，整批 882.695 秒。相对原始单份 874.612 秒，吞吐约 1.982 倍。独立解析原始 Playwright JSON 再次核验一致性，同时确认参考 summary/results 哈希、冻结应用和评测器工作树未变。

四路批次 `20260920-163747-eval-9cb10a4b` 也完整结束：四份均为 14/32，128 项状态全部匹配原始参考；各任务历时 891.035–894.448 秒，整批 894.520 秒。端口分别为 51205、47891、46681、42335，结束后均已释放。独立核验再次确认参考、应用快照及评测器未变，四份实际评测源码快照一致。两批全部报告、截图、trace 和日志已下载，本机 `status` 路径重定位通过。

| 并发任务数 | 整批耗时 | 每份结果 | 与参考逐项一致 | 相对参考的吞吐 |
| --- | --- | --- | --- | --- |
| 1（原始参考） | 874.612 秒 | 14/32 | 参考 | 1.00× |
| 2 | 882.695 秒 | 均为 14/32 | 64/64 项一致 | 1.98× |
| 4 | 894.520 秒 | 均为 14/32 | 128/128 项一致 | 3.91× |

吞吐比按“并发数 × 原始单份耗时 ÷ 整批耗时”计算；每种并发只跑一批，没有统计置信区间。四路单批比两路慢约 1.3%，但一次完成的份数翻倍。运行中一次主机采样显示约 12.2 GiB 可用内存，1 分钟负载约 1.16；这是瞬时全机采样，不是每个任务的峰值资源统计。

后续在该 WSL 主机上进行类似的冻结 Keep 应用评测，建议采用 4 个独立任务，每个保持官方单 worker。此次是同一快照的重复对照，没有验证四种核心同时生成；生成主机的共享临时路径和端口风险仍需单独处理。结果也不能推导其他 CPU 密集任务、长期模型请求或云端 runner 的并发上限。

## 交付检查

Factory26 的 25 项检查在 Mac 全部通过；WSL 通过 24 项、跳过 1 项 macOS 沙箱检查。覆盖了凭据传输、HTTP 失败、已上传 ID 恢复、日志游标持久化、真实 PASSED 终态、429 不重试、并行任务隔离、逐项对照以及远端批次下载后的只读路径重定位、原生日志进度与终态实际耗时。项目 SVC status 为 healthy，文档本地链接有效。本次没有 Git 提交或重新安装 runner/Playwright。
