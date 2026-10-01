# Lite/Web 本地实验设施验收

2026-09-23 使用主办方发布的 [本地模拟 Runner `4e62690`](https://github.com/code-philia/hackathon-local-simulation/tree/4e62690ef0af48601150f248e1f993a300533357) 验证了独立实验设施。基础镜像固定为 `gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de`（`linux/amd64`），本地包装镜像 ID 为 `sha256:e0107fd248d0d810f0deb453787195af417046e16eccb714bcb6723e9a5e0f2c`。镜像内 `/opt/arcbench/run_submission.py` 的 SHA256 为 `025ede6378697205fdc380655a36c3d44b7062292242b154a23ac4914c63fa46`。这些是本地环境标识；包装层及本地测试不能等同于已关闭官网的评分。

黑盒检查让同一 Lite/Keep 的两个 variant 与 Web/Keep 同时执行，证实 run 目录、冻结输入、OTLP 批次和产物彼此隔离。公开的八组 Lite/Web 输入均通过来源身份与哈希核对。Lite/Keep 和 Web/Keep 的并行准备阶段均成功，且两者使用不同的需求与测试哈希。

无模型静态应用的完整运行保存在仓库同级 `factory26-official-local/runs/infra-smoke-20260923/results/`。Lite/Keep 与 Web/Keep 各完成 32 项评测，均为预期的 0/32；每场在原始 Runner workspace 中保存了 32 份 `error-context.md`。Runner 的测试命令返回非零，但结果文件明确记载 `evaluation_status=completed` 和完整用例计数，设施正确将其记为有效低分。另一个短命 Agent 从生产 Runner 容器发出一条 OTLP trace 批次后主动退出；`factory26-official-local/runs/infra-otlp-probe-20260923/results/` 中该 run 标记为失败，遥测仍独立保存并可导出。

`make test` 的 135 项 Python 检查及 Pi observer 检查通过；文档本地链接、`git diff --check` 和 `.venv/bin/svc status --json` 通过。此次验收证明 Lite/Web 本地装配、并发、结果归档与容器到 Collector 的 OTLP 链路；未运行带真实模型的 Harness，也未验证其实际会话上报内容。运行方法与结果字段以[运行文档](../docs/deployment/index.md)为准。
