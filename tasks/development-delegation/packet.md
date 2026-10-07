# 开发侧委派流程与角色修订

2026-10-02，用户要求总结一般工作流程，覆盖 sub-agent 与 session delegation，更新至少 repo AGENTS.md，并改写用户侧 Explorer、Browser/Computer Operator。本任务只修改开发侧指引与角色配置；侧会话不参与原实验执行、不调用或联系子 Agent，不改运行状态或 Git 索引。

初稿过早把初步判断写成规则。用户随后要求“先定位出来当前的 sub-agent session delegation 存在怎样的缺陷，特别是 session delegation，从你过去的对话里面去找到这些缺陷”，并指出过度、频繁交接。停止编辑后，已复核双方历史消息并汇报诊断。用户回复“是的，我同意。继续推进。”，授权按该诊断修订现有草案。

## 历史证据与判断

只读复核 [factory26 main](codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2) 和 [I13 Flash/GitHub：内存修复后官网热恢复](codex://threads/01a0fa57-5cd1-7f20-9a18-5360ca8b21f4) 的消息与工具记录，并对照较早 cleaner 方法线的委派。核心主会话 turn 为 `01a0fb3b-7c61-7e21-acb4-48a38269eb1d`，2026-10-02 14:09:34–15:07:55（Asia/Shanghai）；cleaner 片段为 `01a0fab4-4a10-7aa0-905c-61669fc90979`。

核心 turn 有 29 次跨会话发送尝试（28 次工具调用完成、1 次失败），其中 19 次发往恢复会话；另有 29 次等待查询，含 8 次即时查询、1 次一秒等待、20 次四十五秒等待。这是调用次数，不是负责人变更次数，也不能据此把整段耗时归因于协调。凭据注入、缺失 Git 元数据、可选 Pi home、Runner 监督等均存在真实设施问题。

| 可观察的缺陷 | 因果判断与修订落点 |
| --- | --- |
| 委派恢复操作时同时要求“主线负责共享源码/运行设施集成”“你只读共享文件，等 ready 再冻结包”。恢复者定位 Pi home 缺陷后仍须请 shared owner 修复。 | 责任比权限宽，使局部修复变成主线阻塞；必要共享修复纳入同一执行责任，并协调真实并发冲突。 |
| 恢复者已直接通知 DX owner 处理 Runner 故障，又报主线；主线再次通知 DX，再转回结果。 | 主线成为重复中转者；获准的技术依赖由相关负责人直接闭环。 |
| 反复发送“立即推进”“无需再等一般许可”，同时仍要求等接口、hash 和最终交接；旧 run 取消也重复确认已有授权。 | 消息未解决实际依赖却增加指令往返；后续消息以改变执行的新信息为依据，合并相关更新。 |
| 主线通知共享入口 ready、可以冻结后，又交付不同 checkpoint hash，要求重新冻结。 | 尚未完成的组件被当作可消费结果；交付说明实际版本和剩余依赖，消费方再冻结。真实缺陷修复后的换包仍有必要。 |
| cleaner 方法线先被限定只读，主线发现用户在该会话已直接授权后才撤回限制。 | 独立会话拥有持续上下文和直接人类决定；重定向前核对其当前状态，避免旧指令覆盖新授权。 |
| 多次以可消费 handoff、接口 ready 等中间结果组织下一次委派，最后才取消恢复者 shared 只读限制。 | 结果责任在阶段间被拆散；普通步骤和失败由原 owner 持续推进，真正更换负责人时才完整移交。 |

原角色配置另有缺陷：Explorer description 为空、正文范围过窄；Browser Operator 写死 agent-browser/browser-use；Computer Operator 尚不存在；Executor 要求调用方先给齐文件、验证器和重试预算等信息。它们需要改进，但没有证据证明 Explorer/Operator 配置造成了上述恢复拖延，session 问题的直接依据是实际委派消息。

方法参考为已有 [委派来源整理](../factory-subagents/cells/subagent-paradox-source.md) 和 [SVC delegation 方法](../../sources/svc/skills/svc-sub-agents/SKILL.md)。本次提炼开发协作约定，不内联技能正文，不修改参赛侧技能或 Harness。

## 修订与归属

用户追加要求“这样的 AGENTS.md 太长了，我们需要 progressive closure”。按此要求，[用户级 AGENTS.md](/Users/lanzhijiang/.codex/AGENTS.md) 与 [repo AGENTS.md](../../AGENTS.md) 仅保留核心责任与按需入口。通用方法移到 [Delegation](/Users/lanzhijiang/.codex/guides/delegation.md)，按分配工作、会话协调、责任移交和独立判断组织；项目具体方法移到 当时的委派说明（已删除）。复杂委派、跨会话协调或负责人替换时阅读相关部分，普通任务无需预读全套。历史证据仍留在本 packet。未新增协调框架、固定交接模板或消息数量门槛。

重写 [Explorer](/Users/lanzhijiang/.codex/agents/explorer.toml) 与 [Browser Operator](/Users/lanzhijiang/.codex/agents/browser_operator.toml)，新增 [Computer Operator](/Users/lanzhijiang/.codex/agents/computer_operator.toml)。Explorer 覆盖复杂调查、原因诊断和反例，必要时向 caller 补充会改变调查的问题；两个 Operator 负责完整操作与实际结果验证，在原授权内处理局部失败。正文不重复通用工具手册，不绑定特定浏览器工具，不要求固定输入输出表格。

[Executor](/Users/lanzhijiang/.codex/agents/executor.toml) 同步消除调用方必须先给齐执行细节的硬要求和例行升级。既有模型、推理档位和 sandbox_mode 保持原值，新 Computer Operator 沿用 Browser Operator 配置；Advisor 不变。

## 验证与状态

2026-10-02 完成本次指引与角色修订。五份角色 TOML 均解析成功，名称与文件对应，既有模型、推理档位和沙箱字段未变，Advisor 全文未变；用户级与 repo AGENTS.md 的委派章节之外内容与本轮修改前逐字一致。`git diff --check` 通过，原有阶段快照条款及其它会话修改保留。

本次没有启动子 Agent、重载服务、提交 Git 或操作实验。配置文件有效不等于当前会话已热加载新角色。行为收益仍需后续实际委派观察，重点看普通失败能否由原负责人完成、跨会话消息是否包含会改变执行的信息，以及调用方是否能低成本采用结果；不把减少消息数量本身当作完成任务的替代指标。

Progressive closure 修订完成：用户级委派章节从 4506 字符缩至 770，repo 从 950 缩至约 218。原通用方法完整保留，两份 AGENTS 的其它章节不变。用户随后明确 CONTRIBUTING 是开源项目共享协作规范，不承担 Agent 行为指南；据此撤出本任务新增章节，将项目方法移到 当时的委派说明（已删除），并更新 AGENTS 的按需入口。
