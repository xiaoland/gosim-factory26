# Run 过程可视化

- **Objective**：现有静态 run 页面要能沿归档证据回看执行过程，定位某次工作项、工具动作或平台阶段的异常，支持针对 Harness 与生成应用的优化。
- **Guardrails**：只读已归档 run；不运行模型或评测，不改动冻结应用及原始证据。过程记录必须标明来源、时间与覆盖缺口；并发 Issue/PR 保留各自会话边界，不制造单线因果。展示文字须转义并保持有界，不默认公开原始提示词、推理或完整工具输出。用户已明确允许实现前基线提交；其余提交需另行授权。
- **Verification**：在真实 Factory 的 Pi/Braid、历史 Codex、Competition hosted 与 Playground 样本上核验事件数、顺序、工作项映射、日志分页去重和来源链接；缺失或损坏归档要明确提示。浏览器检查可读性与跳转，运行针对性测试、`make test`、本地链接检查和 `.venv/bin/svc status --json`。不启动新实验。
- **Current Truth**：当前 `scripts/run_viewer.py` 只呈现生成/评测终态、阶段日志末 12 行及用例结果。Factory 样本 `20260921-142645-6eeb4f7b` 有 5 段通过 SHA256 校验的 Pi 会话，记录 Issue/PR、turn 和 164/164 对可定位行号的工具调用与结果；历史 Codex 的 native rollout 也有独立的 `function_call`/`function_call_output` 格式。现有 19 份 native JSONL 合计 46.6 MiB，另有无原生证据的旧 run。平台 `logs/*.json` 含带 event ID 的 `runner_events`，心跳不代表 Agent 内部进展；已有归档没有跨快照重复事件，须用隔离样例验收去重。首版已批准的任务包明确排除原生全文解析与大段日志内嵌，因此过程展开展示属于实质读取及呈现边界变化。
- **Next Step**：按已确认的影响范围，先提交仅含 viewer 任务的实现前基线，再实现过程视图并验收。用户在本任务回复“确认”，允许本次改动及基线提交。

## 拟议方案

保留现有静态 HTML 生成入口。Factory 过程按工作项和物理会话分组，显示会话状态、turn 类型、起止时间，以及可由归档直接证明的消息、工具调用与结果摘要；每项标出原生文件与行号。只有通过 manifest 哈希验证的会话才宣称工作项映射可信；旧归档无 manifest 时显式标记未核实。正文折叠、截断且不展示模型推理。生成、冻结、评测阶段仍与 Agent 过程分开。

Competition hosted 和 Playground 共用 `runner_events` 时间线，按 event ID 去重，保留平台原始时间字符串及来源归档；心跳只计数，不作为阶段进展。若平台仅归档了阶段或心跳，页面明确说明无法还原 Agent 内部动作。所有来源均显示取证覆盖范围，原始文件仍可通过现有只读链接打开。

计划只修改 `scripts/run_viewer.py`、针对性的 `tests/test_run_viewer.py` 和运行文档；不改生成、评测、平台采集或 SVC。原生解析限定在各 run 的 `native/*.jsonl`，不扫 12 GiB 的其它原始归档。页面展示工具名称、可确认的目标和调用结果摘要，完整参数及输出仍只留在原始文件；每条摘要显示截断状态。若独立预演表明这些来源无法可靠支持过程视图，先重新判断设计，不追加推测层。

## 独立预演与验收

独立 QA 对样本中的 5/5 段 Pi 会话验证了 manifest 哈希，164/164 对调用与结果由 ID 配对。`PR #1` 的 session `001` 中，第 5 行 assistant 含工具调用，第 6 行 `toolResult` 用 `toolCallId` 回指；Codex native rollout 的第 9 行 `function_call` 与第 14 行 `function_call_output` 由 `call_id` 配对。现有平台日志样本的 event ID 均唯一；`scripts/playground.py` 的归档汇总已用 event ID 去重，可沿用规则。已有 viewer 与 Playground 针对性测试 11 项通过，但尚无过程投影测试。

实施后的重点验收：当前 Factory run 的 `PR #1` 工具调用可回到上述原生行号，Pi 与 Codex 分别按各自格式呈现；跨两个平台日志文件的同 ID 事件只显示一次；仅有心跳的运行中样本注明内部 Agent 过程未归档；缺少或哈希不符的原生会话不得冒充可信工作项过程。静态页面打开后再核对折叠、筛选、来源链接和长文本边界。
