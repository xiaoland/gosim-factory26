# Run 可视化诊断

- **Objective**：从本机已归档的 Factory、Competition hosted 和 Playground run 生成可在浏览器打开的诊断页面。使用者能从 run 列表进入状态、阶段、评分完整性、失败用例、错误与原始证据，定位应进一步查询的现场。
- **Guardrails**：只读已有 run，不联网、不运行评测、不修改源归档；页面是可重建的派生快照，源 JSON 和现有 `factory show` 仍是事实权威。区分平台终态、评分是否完整与采集时间，缺失显示未知。原始日志可能含敏感内容，页面不内嵌整段原始日志或凭据。源码实施与新实验须待影响评估及独立预演呈现给用户后取得明确开工同意；本任务当前仅授权调查、隔离预演和任务包整理。不得提交。
- **Verification**：独立预演已核对真实归档和四条静态相对证据路径；实施后须在浏览器实际点击页面与截图，并用生成成功但评测失败、生成失败、评测中断、完整低分、运行中、缺失证据样本核对列表及逐项结果，再运行 `make test`、本地链接检查和 `.venv/bin/svc status --json`。不启动模型或正式实验。
- **Current Truth**：根 `runs/*/run.json` 有 15 个 Factory run，`scripts/inspect_runs.py` 已提供 `list_runs/show_run` 与身份、评测完整性、会话证据校验。当前 Competition hosted 的 `state.json` 关联任务 run；任务 `status.json` 是 `{observed_at, source, value}`，其中完整的 `FAILED` 也有有效分数，而运行中计数不能视为成绩。Playground 的 `status.json` 直接存平台响应。递归搜索 `run.json` 会把官网 analysis 快照、验证 fixture 等误列为独立 run。已有工作树改动属于其它任务，不纳入本任务。
- **Next Step**：向用户呈现下面的源码影响和独立预演结果，取得明确开工同意；未取得同意前不编辑产品源码。

## 方案与权威

首版用 Python 标准库生成 `runs/viewer/index.html` 及逐 run 页面，浏览器直接打开，不部署常驻服务。目录和页面均是忽略的派生产物；新增 run 或已有 run 更新后重新执行生成命令。列表明确显示生成时间和源观测时间，不假装自动刷新。

发现规则按生产者划定：Factory 只读根 `runs/*/run.json`，复用 `inspect_runs.list_runs/show_run`；Competition hosted 只读 `runs/competition/*/hosted/*/inputs.json` 与同目录 `state.json` 声明的任务，再核对归档 `status.json` 的平台 ID；Playground 只读 `runs/playground/<id>/status.json` 并核对 ID。批次和矩阵只用于分组或导航，不能计作独立 run。派生的 `analysis/run.json` 不加入列表。

页面层只负责呈现，不重算事实权威。Factory 评分沿用 `inspect_runs` 的完整计数判断；用例根据所选评测 `results.json` 展开，并复用已有定向证据提取。Competition/Playground 按明确终态、正整数 total、`passed+failed=total` 和平台数值分数判断评分完整性，保留 `FAILED` 与有效低分的区别。网页仅展示有界错误、阶段、原始文件的相对链接；所有来自归档的文字需 HTML 转义，附件链接必须落在 `runs/` 且文件存在。

## 实施顺序与验收

1. 先以独立小样确认 `file://` 页面可打开相对证据链接，并验证三个来源的解析假设；不修改产品源码。
2. 开工确认后新增一个生成入口和必要的页面模板/样式，复用现有诊断函数。限制文件读取在已知元数据和所选用例证据，不遍历 12 GiB 原始归档或对原生日志做全文索引。
3. 用现存 run 构建页面，核对 Factory 本地完整分数与生成失败，Competition mixed/BookStack 完整低分和运行中未知分数，Playground 终态与观测时间；点击至少一个失败用例及现场证据。对缺失或身份不符显示不可用和警告，不猜测补齐。
4. 更新 `docs/deployment/index.md` 的使用入口及快照语义，执行项目检查。实施完成后把长期有效的说明留在运行文档并删除任务包。

**预期源码影响**：新增只读页面生成脚本及必要的针对性检查，更新运行文档；不修改 Factory 生成、评测、Competition 控制器、Playground 采集器或已有 run。若预演发现浏览器不能访问必要本机附件，再复核是否改为仅绑定 `127.0.0.1` 的只读服务，不在未复核时扩大范围。

## 独立预演回报

QA 独立核对了六类真实样本。本地 `20260921-083151-b978c271` 生成成功、评测完整结束但只有 9/32；`factory.py show --case REQ-2.2 --json` 能返回错误、截图、视频、trace 和页面片段。本地 `20260920-225624-82074f1f` 生成失败且反馈定位到 `pi-events.jsonl:8589`；`20260920-110533-521c8f13` 的评测中断没有可用分数。官网 mixed/BookStack 的 `FAILED` 是完整 13/34、平台分数 38.2；官网 GLM/Keep 的 `RUNNING` 尚无分数。Playground 已归档样本分别有通过和失败终态。

隔离样例位于忽略目录 `runs/validation/viewer-preflight/index.html`，四个相对的截图/日志路径在本机 `file://` 解析下均可读取；浏览器自动化的 URL 安全策略拒绝打开 `file://`，因此真实点击和渲染仍列为实施后验收门槛，不冒称已验证。预演未修改产品源码、原始 run 或评测器，未启动模型或实验。
