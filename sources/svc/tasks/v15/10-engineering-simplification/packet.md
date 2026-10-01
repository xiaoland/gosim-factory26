# v15 工程化简化

目标：让 SVC 的实现、静态检查、测试、CI 与发布只保留能证明当前
Python 包和 Corpus 合同的最小路径。

完成条件：

- 发布说明改用 Python 生态工具，不再依赖 Changie 或专用 workflow linter。
- Corpus 迁移只由 `corpus/migrations/` 与 `corpus/version.json` 表达；CLI 不再生成或执行历史配置迁移。
- v15 同时切断 CLI 与 Corpus 历史链，只接受当前配置、Corpus 基线和机器输出合同。
- 本地 `pdm run check` 与 CI 使用同一入口，pytest 失败能直接显示完整断言和跳过/失败摘要。
- release PR 合并后发布的体验保持不变；锁文件、全套检查、构建和安装后黑盒验收通过。

已确认决策：

- 使用 Towncrier 替换 Changie，但不改成人工推 tag 发布。
- v15 的 hard cut-off 包含 Corpus 历史链；旧输入保留明确拒绝，不保留成功兼容路径。
- Corpus 指南不承载 CLI 配置或机器输出迁移；后者属于 CLI 发布说明和用户文档。

当前事实：工作位于 `ref/v15-engineering-simplification`，从 `main` 的
`b642d04` 创建。分支携带一批讨论前产生的未完成草稿；它们不是已接受设计，
必须按 [plan.md](plan.md) 逐项审查。advisor 已指出草稿遗漏 analysis/integration
兼容路径并过度削弱 wheel 黑盒验收。

当前前沿：[design.md](design.md) 已通过 advisor 复审；实现正在按该边界收敛，
当前测试已切断旧 analysis/evidence 成功路径，CI/CD 与发布工具正在验证。

目录与发布边界已追加确认：仓库 Corpus 权威源改为 `corpus/`，CLI PDM
member 改为 `cli/`，但保留标准导入隔离布局 `cli/src/svc_cli/` 和公开包名
`svc_cli`。CLI 与 Corpus 分别拥有 Towncrier fragments、changelog、版本和 tag；
wheel 仍内嵌一个 Corpus 快照，因此 Corpus 的 PyPI 交付随下一次 CLI 发布发生。
