# 会话 A：InKCre 核心能力升级

## 覆盖与边界

读取 `codex://threads/019fad3c-57eb-7160-ae35-b04cf79f6dcd` 的 4 个分页窗口（每窗最近 10 turns 的摘要），并在本地原始记录中定向读取 2026-07-31 至 2026-08-06 的 5 个用户消息及邻近回应；主 Agent 另核验了 2026-07-29 起点 `019fad3c-5c82-7f63-8483-10e3dc193bd3`。所读最近 turn 为 2026-09-20 `01a0be97-507c-7bc2-9cb4-75f41f4eeaa5`。重点仍是 2026-09 的 Agent Query Sink；它不能代表整个“大任务”的所有 unit。本文是分段证据分析，不是全会话逐 turn 审计；较早 CLI unit 只用于识别工作模式，未逐项审计其代码变更。命令执行与文件变更是会话记录，本文没有复跑外部 CI 或生产环境。

## 关键发现

### 1. 用户授权被拆成阶段性、可撤回的设计授权，而非一次性“实现许可”

**观察。** 用户在 `01a0bcc6-1e33-75b3-ac92-e2990a8a24f2` 指定 Agent Query Sink 为由 AI 组合原子查询的检索能力；主 Agent 明说“当前只进入调查与讨论，不开始实现”。在 `01a0bcc7-0c7e-7510-9c22-87432e6b7da8`，用户确认按既定流程，Agent 建 packet、提出交付定义。后续“接受/同意”分别确认独立 Job、Sink 实例、结果合同等；`01a0bd78-7c96-72f2-aea9-4db76bf7996f` 仍声明只做 preflight/packet，不开始源码实施。最终用户在 `01a0be97-507c-7bc2-9cb4-75f41f4eeaa5` 明确授权合并、验证、关闭 unit。

**推断。** 这条会话把“方案被接受”和“可改变外部状态”分开，能让用户在成本较低的阶段纠正架构，同时在最后才授权合并。它依赖可辨认的授权载体（packet/decision、PR draft 与最后的明确指令），不只是 Agent 口头承诺。

**限制。** 摘要未展示每个“接受”对应的完整上下文；不能据此推断所有历史 unit 都严格遵守同一粒度。

### 2. task packet/decision 是有效的跨轮外部工作记忆，但其价值取决于把纠正写回到实施前资料

**观察。** 早期用户已在原始记录 turn `019fb91f-2c27-7301-a7ca-5a2fdec67c45`（2026-07-31）直接询问 packet 是否支撑“产品/技术设计→实现计划+最后探索→实现”；并在 `019fd143…`（2026-08-05）指出数千行 `decisions.md` monolith 要拆、`019fd5fc…`（2026-08-06）指出 packet 停更且要求子 Agent 回溯遗漏。Agent Query 起点 `01a0bcc7…` 创建 unit packet、product-design、research 与 D611-D620；每个设计结论都伴随 `fileChange` 和 `git diff --check`。用户纠正 route 后，`01a0bd42-06d5-70e0-a094-1f3c2c32ea7e` 明确“撤回 packet 中的固定 route 建议”，写回 D-623、packet、research、technical-design。工具归属纠正后，`01a0bdae-3c43-76a0-b5ea-a7eb3914a450` 把 D-629、impact handshake、implementation plan、common pattern、roster 等同步更新，再开始源码改动。实现后，`01a0be02-62da-72c2-894a-488195d0c111` 又把 Preview 事实写进 packet/implementation evidence。

**推断。** packet 在此不是日记：它把“当前决定、待验收项、跨 owner 依赖”变为后续实现、PR 描述和合并检查可以读取的对象，降低了上下文压缩后重述约束的负担。但早期的 monolith 和停更纠正也说明它必须有拆分/回溯维护接口，不能仅凭“更多记录”保持可靠。

**反例/限制。** 文件更新很多且分散，摘要不能证明每一项都在实施时被实际消费；维护量本身可能成为噪声。需要进一步比较 packet 中的决策是否被自动或人工地与 PR/验收条目逐项对照。

### 3. 两次用户纠正暴露的不是“未听从”，而是相邻基础设施概念被错误外推；正确性需由领域语义裁决

**观察链 A（生命周期）。** Agent 在 `01a0bd33-d6ab-7962-9070-612a243e7e37` 提出 route 固定存在，因为受理和执行分离；用户于 `01a0bd42…` 指出 endpoint 应跟 Sink 挂载走。Agent 随即承认把“共享 Job 受理机制”外推为“两种入口同样可用”，改为 `on_start` 挂载、`on_close` 撤下，而 Job 继续独立（D-623）。preflight 后还验证动态 route/OpenAPI 与实际注册对象（`01a0bd78…`）。

**观察链 B（能力归属）。** `01a0bd49-0da9-7970-bcd0-d9a2eb50fd2d` 初始建议新增 `app/agent_tools` 适配模块以集中读取工具；用户在 `01a0bdae…` 指出应分别回到 InfoBase、Resolver、GraphNavigation 和 AgentQuerySink owner。Agent 承认把“供 Agent 调用”误作业务归属，撤回方案并把原则写为“不新增 `app/agent_tools`”。之后最终 PR 汇报称独立启动遗漏的工具注册已修复，且未抽取不必要 helper（`01a0be02…`）。

**推断。** 两个错误都不是缺少更多“遵守规则”的提示，而是方案需给足因果链与相反语义的反例：为何该 owner/生命周期/复用边界成立，什么观察会推翻它。可采用轻量的 proposal 记录，不应把某种强制表格误当结论。

**限制。** 用户是该架构的权威，摘要不能判断 Agent 仅凭代码是否本可推出相同结论；这属于语义/产品 ownership 判断，不能完全自动化。

### 4. sub-agent 调查被用于有界问题，主 Agent 保留综合、决策沟通和落盘责任

**观察。** `01a0bcc7…`、`01a0bcce…` 至 `01a0bd78…` 多次出现 `agent_query_framing` 与 `sink_lifecycle_review` 子 Agent 活动，随后主 Agent 自己读取相关源码、在面向用户的结论中给出取舍、更新 packet/decision。例如 lifecycle proposal 由 `sink_lifecycle_review` 后写入 D-622；preflight 的动态 route 验证则由主线程完成。早期 `019fd5fc…` 的 packet 停更纠正也显示 sub-agent 产物需要主线程回溯核对。没有证据显示子 Agent 直接获得用户授权或直接合并。

**推断。** 这种“窄调查→主线程对照源码与用户目标→主线程登记决定”的分工减少主线程检索负荷，同时没有把架构接受权委托出去。

**限制。** 摘要只显示 sub-agent 活动而未包含其完整回报，不能评估其独立结论质量，也不能量化节省的时间。

### 5. 验收跨越静态检查、Preview、真实模型/CLI 行为与发布依赖；最终合并仍重新确认外部状态

**观察。** 实现验收汇报 `01a0be02…` 列出真实模型查询、媒体文字子图、bounded wait/abort/timeout、双 Sink lifecycle、Organization 回归、CLI wheel、Preview readiness；命令记录显示修复后 read-only smoke 通过，而初次因可执行文件名错误失败后被更正。review 采纳/不采纳的区分（修复独立启动遗漏的工具注册、暂不抽 helper）见 `01a0be82…`。最后合并 turn `01a0be97…` 先查 Hub #29 与 core #111、submodule SHA、检查门禁；Hub squash 后更新 submodule 并重新跑 Core 门禁，等待所有 Preview 后才合并 #111。首次合并受保护检查阻止时，Agent 说明等待而不绕过。

**推断。** 可迁移的正例是把验收材料与发布前条件分层：实现的行为证据不等于最终可合并性；跨仓库 squash/submodule 依赖须在 merge 时再重新读取真源。

**限制。** thread 摘要中“全部通过”主要是 Agent 声明和命令状态，本文不独立验证 GH/生产结果；真实模型偶发未提交结果被记录为已知残余，不能由这一轮判定为已解决。

## 高价值候选改进（最多三项）

1. **在 proposal/impact-handshake 加一张 owner–lifecycle–reuse–counterexample 表。** 证据是 D-623 与 D-629 均由“相近机制”误推为错误抽象；表应强迫 route、schema、工具、状态各自写明领域 owner、生命周期 owner、已有可复用接口，以及一个会否定该方案的反例。反例限制：最终 owner 仍需用户/架构权威裁定，表不能代替评审。

2. **让 packet 的决定与验收条目具可追溯链接，而非增加更多过程文字。** 证据是 route/工具纠正确实传播到 decision、plan、handshake 和最终验证；可将每项决定链接到实现证据和最终 PR/merge 检查。限制：本会话已大量更新文件，若强制为每个细节建条目会增加维护成本，只应覆盖改变接口、owner、生命周期或可见合同的决定。

3. **将跨仓库交付的“merge-time revalidation”做成明确的检查清单/接口。** 证据是 Hub squash 改变 SHA，必须先合 Hub、更新 Core submodule、重跑 Core 检查；这不是实现阶段能一次性固定的事实。限制：只有存在可变的跨 repo 引用、保护规则或发布控制器时才值得启用，单仓库小改动不应套用。
