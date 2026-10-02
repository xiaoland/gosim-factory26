# SVC CLI 裁减：已转交 skill 接线

当前后继是 [SVC skill 接线](../svc-skill-integration/packet.md)。
不再按此阶段计划保留或恢复参赛 CLI；待完成的真实读取与实验验收归后继任务，开发侧 SVC 不受该裁减影响。

## 历史阶段记录

目标：从 Factory 运行时 SVC CLI 删除 `task grow` 与 `task init`，移除针对已撰写 SVC Corpus 的测试，并审查其余 CLI 的认知负担。

范围：`sources/svc` 是参赛运行时源码；开发用的独立 SVC checkout 不在本次改动内。Agent 直接创建或续写 packet，仍可按需读取 Task Packet 指引和可选模板。其余 CLI 命令先审查用途，不直接删除。

验收判据：运行时 CLI 不再列出或接受 `task` 命令；SVC 指引仍能让 Agent 直接建立 packet；测试不再对 SVC Corpus 的篇目、文本、版本推进或目录作断言；CLI 检查和 Factory 测试通过。实验评分等基础设施准备后再做。

状态：`task` 命令及整个专用实现模块已删除；`lookup` 保留。针对已撰写 Corpus 的 catalog/release 测试及默认 release 检查已删除。CLI 其余命令的用途与下一步边界见[裁减审查](audit.md)。

验收结果：`sources/svc` 的 `pdm run check` 为 241 项通过，sdist 与 wheel 构建通过；参赛安装已重建，黑盒确认 `task` 命令不可用、`lookup` 可用；Factory `make test` 为 139 项 Python 测试与 Pi observer 检查通过。没有新增或保留针对已撰写 SVC Corpus 的测试；未运行评分实验。

后续：先前 `runs/packages/svc-corpus-review/pi-team-vv-generic-corpus-candidate.zip` 是 CLI 删除前的包，已失效，不能作为本轮源码提交；实验基础设施就绪时需重新打包并冻结。

后续按用户决定移除整个参赛运行时 CLI，改由 skill 装载 Corpus；实施与验收见 [接线任务](../svc-skill-integration/packet.md)。
