# CLI 裁减审查

Factory 运行时的 `harness/AGENTS.md` 已引导 Agent 按需建立 Task Packet。CLI 的主要裁减判据是 Agent 是否必须学习一个额外命令及其规则才能完成本可直接完成的工作；包体和执行时间不是这个判断的主因。运行代码通过 `sources/svc` 安装 CLI，开发诊断的 `telemetry`、`analysis` 使用独立的 `.venv/bin/svc`。

| 命令或机制 | 当前消费者与判断 | 处理 |
| --- | --- | --- |
| `lookup` | 参赛 Agent 按需读取指引的入口 | 保留 |
| `task init` | 仅复制内置模板到 `tasks/<task-id>/packet.md` 并拒绝覆盖；Agent 可以直接创建或续写该文件 | 已删除命令、专用模块与测试；模板只作为可选参考 |
| `task grow` | 只扫描文件名并复述形状问题；Agent 直接读 packet 与增长指引即可做语义判断 | 已删除命令及其独占扫描代码 |
| `check-corpus-release` 与 Corpus 内容测试 | 把文本篇目、版本和历史差异变成测试门槛 | 已从默认检查链及测试套件移除；构建时仍须能读取、打包有效资源 |
| `init`、`status`、`upgrade`、`dev`、`run`、`double`、`telemetry`、`analysis` | Factory 参赛 Agent 的常规路径不使用；部分属于通用 SVC 开发或项目集成能力 | 本次不删。下一步可以只让参赛运行时暴露 `lookup`，开发 CLI 保持完整；优先核实是否还有 Agent 需要上述命令，避免把可用能力与认知噪声混为一谈 |

未把 `cli/tests/test_lookup.py` 等基于合成资源的 CLI 行为测试当作 Corpus 内容测试；它们检验命令协议和选择行为，不断言已撰写 Corpus 的篇目或措辞。
