# 开发闭环与 Playground 调查（2026-09-20）

本次没有重新生成四组应用。工作集中在实验导航、失败状态、上游共同开发，以及 Playground 执行能力探测。首轮成绩与条件仍以[矩阵报告](2026-09-20-harness-matrix.md)为准，当前操作方式归属[运行文档](../../docs/deployment/index.md)。

## 诊断和目录调整

原始证据较完整，但查找入口缺失，运行中阶段不落盘，容易迫使 Agent 阅读大量无关的 session 元数据。本次新增 `list/show/--case`，将生成、评测和 analysis coverage 分开；阶段状态与错误写入已有元数据文件，不增加数据库或 UI。真实四组读取结果仍为 7/32、9/32、14/32、8/32，REQ-2.2 能直接定位 Note editor / Title 等待超时及本地附件。

组合配置迁至 `variants/<id>/config.json`；公共 SVC user-scope 指令继续由 `harness/AGENTS.md` 维护，确有差异时才增加 variant 的覆盖文件。旧 `configs/` 是符号链接，历史 run 不重命名、不补写阶段；新 run 保存 variant 源码快照和实际注入文件。

analysis 按 CLI 来源指纹保存不可变结果，避免“改了 exporter，却因旧 ZIP 存在而没实际重导出”。查询中断不会覆盖历史结果。SVC `partial` 说明证据覆盖，不是生成失败；外部评测错误与原生工具事件之间没有自动因果关联。

## Python Responses 协议桥

需要的是对 Codex 提供 Responses、对比赛网关调用 Chat Completions 的桥。Codex 本身支持 Responses；此前接入问题是比赛网关直接调用 `/responses` 返回缺少 messages 的 422。两个 Codex 实验已使用 LiteLLM 完成，因此不是仍未解决的 blocker。

| 候选 | 核查事实 | 本次决定 |
| --- | --- | --- |
| [LiteLLM](https://docs.litellm.ai/docs/response_api) | Python；支持 Responses 与 Chat Completions 桥接。当前固定 1.102.0，使用 `use_chat_completions_api: true`；真实 app-server 已完成带工具、图片的生成 | 继续使用现有安装，不引入新桥 |
| [talkcozy/api2codex](https://github.com/talkcozy/api2codex/tree/1a18533889922654665134421557d287d24c0cf6) | Python，FastAPI/httpx 单文件。源码 `input_to_messages` 将 `input_image` 替换为 `[image]`，与 README 宣称支持图片有实质差别；流结束无条件生成 completed | 当前不适合本项目的视觉需求与终态判断 |
| [uugxm/codex-proxy](https://github.com/uugxm/codex-proxy/tree/3ba60b794047dd2ca641038d5e75cc0c026fd603) | Python；源码 `_finish` 无论 stop 或其他 finish_reason 都生成 completed，不能可靠区分 length 截断 | 保留为候选，不切换实验条件 |

候选只做了源码核查，没有对比赛网关运行替代桥。当前 LiteLLM 已验证正常完成路径；不能由两次成功推导所有异常、流中断与 usage 字段都完全等价。若替换桥，必须独立核验图片、工具调用往返、流中断/length、usage 缺失，而不是仅凭一次文本应答。

## 本地上游修改

`~/Development/svc` 基于 HEAD `80996c1`，修正 analysis help 中仍要求先读取大量原生记录的旧导航，改为 match → trace，read 留给精确恢复或审计。附 CLI patch release fragment 和帮助回归；完整 `pdm run check` 通过（259 项测试，含格式、类型、schema 与依赖边界检查）；没有调整 Corpus 权限或任务语义。Factory26 可以通过 `analyze --svc-source ../svc` 直接使用 PDM 环境，并记录未提交源码哈希。真实 Pi 会话的隔离副本已完成导出与查询，历史实验分析未覆盖。

`~/Development/braid` 基于 HEAD `08c1c10`，同步实验已经发现的通用 Pi provider 修复：保留默认系统提示、等待 agent_settled、拒绝最终 length；同步契约和现有隔离测试 fixture。requirement 适配继续属于 Factory26。通过 2 项 provider 测试、格式检查和 diff 检查；没有宣称完成真实 GitHub 产品验收，也未提交或推送。

后续已完成独立 HTTP 客户端认证、API 上传运行及证据收集，当前进展见[API 与并发实测](2026-09-20-playground-concurrency.md)。下文保留本轮早期调查时的验证范围。

## Playground 的执行接口

来源是[官方 Playground](https://arc-bench.com/playground/arc-bench/web/12306)、[API/SDK 文档](https://arc-bench.com/api-doc)、公开前端 `assets/index-pw0ZS5Jw.js` 与官方下载的 Python blank template。下表中的 HTTP 路由是前端协议调查结果，不是主办方承诺的稳定外部 API。请求使用网站 Cookie 会话；未导出浏览器 Cookie 或平台 Access Key。

| 用途 | 当前前端调用 |
| --- | --- |
| 需求 | `GET /api/requirements/{id}?catalog=benchmark` |
| 下载 Python 起点 | `GET /api/requirements/{id}/starter-agent?catalog=benchmark&language=python&template=blank` |
| 上传 Agent | `POST /api/submissions`，multipart：runtime、catalog、agent_source、display_name、base_url、api_key、model、visual_model、file；可含 requirement_id、competition_id、task_type、template_selections |
| 创建一次运行 | `POST /api/runs`，multipart：submission_id、requirement_id |
| 启动运行 | `POST /api/runs/{run-id}/start` |
| 状态与增量日志 | `GET /api/runs/{run-id}`；`GET /api/runs/{run-id}/logs?log_offset=…&after_event_id=…` |
| 状态流 | `GET /api/runs/{run-id}/events?since_version=…`，SSE |
| 需求关联 | `GET /api/runs/{run-id}/traceability?node_id=…`，`__all__` 查询全部 |
| 源码和提交 | `GET /api/runs/{run-id}/source?file_path=…&kind=file&first_line=…&commit_oid=…`；`GET /api/runs/{run-id}/commit-history` |
| 预览 | `GET /api/runs/{run-id}/preview/status` |

公开需求与模板下载实际返回 200；未登录 auth/me 返回 401。上传、创建、启动已通过用户登录的 Helium 页面实际执行。直接在浏览器打开 JSON 日志接口被客户端阻止，因此没有把所有读取路由写成已验证可用于独立 CLI 的接口。对本次 run 的无凭据日志请求也返回 401。没有绕过认证，也未构建依赖私有 Cookie 的自动化客户端。

Python 包要求根目录有 main.py、requirements.txt，可另外有 package.json 安装 Node 依赖。执行契约为：

```sh
python3 main.py /path/to/requirements --output-dir /path/to/output --type web
```

runner 注入 OPENAI_API_KEY、OPENAI_BASE_URL、MODEL；官方 SDK 提供 `.arc/runner-events.jsonl` 和 `.arc/traceability/` 的事件/关联写入。模板使用 frontend/ 与 backend/，平台安装依赖、构建前端并部署。当前本地 harness 读取仓库外密钥、采用根目录 npm start，不能把开发仓库直接压缩就认为可运行；需要独立的入口和部署契约适配。

## 云端探针

[2041e4b58701](https://arc-bench.com/playground/arc-bench/web/12306/submissions/2041e4b58701) 名称为 factory26-environment-probe-no-llm。用户授权上传并运行。ZIP 由 [playground_probe.py](../../scripts/playground_probe.py) 基于官方 blank template 创建，仅包含模板、SDK 和工具/CPU 可用性检查；表单使用非凭据占位符，未传比赛密钥，探针不调用模型。

本地入口和模板复制验证通过。平台已确认环境 preflight、安装 Agent 依赖、执行 Agent 成功，随后安装前后端依赖、构建、启动 localhost:3000 并进入 135 场景评测。日志明确使用已有 runner 镜像及镜像内 Playwright，测试 worker 为 1。Meter 以占位符认证返回 401，符合本次无密钥探针的设置，不构成模型计费验证。

平台并未跳过应用自身依赖安装。运行至 10 分 50 秒时仍显示 0/135，因此尚无证据说明平台整体反馈比 WSL 更快。这个空白模板不产生可比较的模型分数；四种真实 harness 的云端兼容性、CPU 配额和完整评分耗时仍未验证。

## 交付检查

Factory26 的 `make test` 在 macOS 通过 16 项；WSL 同步当前脚本后执行同一入口，平台专属 macOS 沙箱检查在 Linux 跳过。原始实验元数据和快照未改写，文档本地链接有效，项目 SVC status 为 healthy。当前配置仍使用已有 runner/node_modules/Chromium 缓存，本次未重新安装评测依赖。
