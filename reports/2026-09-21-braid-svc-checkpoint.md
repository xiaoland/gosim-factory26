# Braid / SVC 接入实验检查点

2026-09-21，用户要求停止实验并先复核结果。四个仍在运行的生成已中断，工作区相关进程全部退出；没有继续生成或自动评测。各次主动中断另存 `interruption.json`，保留原因和停机核验。当前运行器把 KeyboardInterrupt 归为 generation_failed，不能据此把这四次主动停止误读成自然失败。

本轮结论：Braid 本地对象、上下文与交付链已通过真实核心探针；SVC 独立注入与诊断链有可核查证据。四组新 Keep 尚无有效官方分数，整体验收未完成，也不能比较组合优劣。[旧适配器四组报告](2026-09-20-harness-matrix.md) 的分数不代表本次实现。

## 已经验证的成果

SVC user-scope AGENTS.md 只有两行 `svc lookup` 导航，不含个人指南，也不调用 Braid。两核心真实运行均成功查询 Corpus；关闭 SVC 的 Braid 探针仍完整通过。因此，独立组合已得到验证，SVC 对生成质量的收益尚未验证。

Braid 保留本地 Issue、PR、comment、N:M 关联及 Git worktree。Agent 通过 CLI 操作对象，沿原有 Context、queue、GroupDriver、SessionManager 链执行。探针验证 comment hide/unhide/delete、自身写入不制造唤醒、宿主 description 变化后实际物理上下文重建、旧 turn 写入被拒绝、同一逻辑 group/worktree 保留，以及 PR 合入、根 Issue completed、收尾收敛和固定 commit 导出。

| 真实核心探针，SVC 关闭 | 结果 | 物理会话 | 墙钟时间 | 证据 |
| --- | --- | ---: | ---: | --- |
| Pi + Braid | 通过 | 6 | 16.1 分钟 | [check.json](../runs/integration/20260920-230846-pi-plain-c01cd3/check.json) |
| Codex app-server + Braid | 通过 | 5 | 21.1 分钟 | [check.json](../runs/integration/20260920-230846-codex-plain-ae35a6/check.json) |

第一轮 Codex 探针曾误用宿主 `--external` 创建 comment，原自动断言没有捕获。修正后，两个 provider 子进程带运行环境标记，CLI 拒绝该环境中的 external 写入；宿主仍可调用。上表的新探针通过真实原生 shell 验证拒绝且对象/事件不变、当前 writer 可用、旧 writer 被拒绝。这是防误用措施，不是对抗性 OS 隔离。

父仓库 50 项检查通过；Braid 当前版本 11 项单元检查及 1 项 CLI 集成检查通过。它们覆盖交付身份、评测完整性、会话归档、故障恢复等边界，不替代真实应用评测。

诊断独立验收通过：历史 REQ-2.2 可从官方错误上下文、页面快照和源码定位到控件名称不匹配；证据不足以宣布评测器有缺陷。SVC analysis 与原生会话通过身份和哈希关联，Playground 保存状态中的缺失时效/trace 保持未知。此次 Pi 失败进一步暴露了终态诊断缺口，已修正退出码误判，并让 show 直接给出核实后的原生终止原因及记录位置。

WSL 评测链复用 runner、依赖和 Chromium。在历史冻结应用的独立验证副本中，官方全部 32 项有终态，14 通过、18 失败，与原结果逐项一致。这只证明评测管线工作，不能记为新 harness 的 14/32。[验证证据](../runs/validation/evaluator-20260920-215843-6cc3c4/validation.json)

## Keep 实验实际结果

| 组合 | 原始尝试 | 结果与耗时 | 当前能说明什么 |
| --- | --- | --- | --- |
| Pi + SVC | [82074f1f](../runs/20260920-225624-82074f1f/run.json) | 58.6 分钟后自然失败 | SSE JSON 解析错误，原生重试耗尽；未交付应用 |
| Codex + SVC | [32e98b15](../runs/20260920-225624-32e98b15/run.json) | 87.8 分钟时按用户要求停止 | 多次流错误后仍在尝试；未交付应用 |
| Pi + SVC + Braid | [6aae4ce3](../runs/20260920-233128-6aae4ce3/run.json) | 30.7 分钟后自然失败 | 原生 JSON 解析错误；根 Issue OPEN，Braid 返回 incomplete |
| Codex + SVC + Braid | [1ba8fed8](../runs/20260920-233128-1ba8fed8/run.json) | 52.8 分钟时按用户要求停止 | 已建立 PR 并写出 8 个应用/自检文件，尚未 ready、合并及交付 |

失败后我未经逐次结果复核，又启动了 Pi 两组独立重跑。这超出了用户期望的实验协作节奏。两次重跑均在约 4.7 分钟时按用户要求停止：[Pi + SVC](../runs/20260921-001931-00ded6c4/interruption.json)、[Pi + SVC + Braid](../runs/20260921-001932-fbf5b027/interruption.json)。后者曾发生 Connection error 后继续活动。它们没有分数，也不覆盖原始失败。

两个被停止的 Braid 工作区保留完整 Git common repo、worktree、对象数据库和原生会话；通过对应 run 的 recovery-workspace.json 定位。其他运行保留原生归档和中断时应用副本。所有应用均未满足本轮冻结交付条件，不可拿未完成文件直接评分。

## 失败证据与判断边界

Pi 的原生错误为 `Unterminated string in JSON` 或 `Expected ':' after property name in JSON`。原始日志保存的非法 payload 多次在外层 model、usage 等字段中途结束，尚未到工具参数。对实际已安装 SDK 的离线判别表明：这些错误来自其已派发 SSE event 的外层 JSON 解析；普通工具参数截断或输出长度终止是不同路径。

Codex 的 LiteLLM 适配器也记录同类 MidStreamFallbackError。因此，共享网关或传输层是优先调查方向，不能据此推断 Pi/Braid 产品模型不成立。用户随后提示 ARC-bench 似乎正在重启服务器；尚无服务器侧证据确认与本次错误的因果关系。

三个隔离的原始流诊断均成功：通用请求、用失败会话消息重放、带 Pi 原生 max_tokens=384000 参数重放。后两次仅消费单次模型响应，不执行工具，最终 toolUse；它们不是 bench。没有捕获到新的坏帧，所以不能宣称问题已修复，也没有据此更改模型、裁减上下文或降低输出限制。[诊断一](../runs/diagnostics/pi-stream-20260921/probe.log)、[消息重放](../runs/diagnostics/pi-stream-20260921/replay.log)、[原生参数重放](../runs/diagnostics/pi-stream-native-options-20260921/replay.log)

墙钟时间包含流错误、重试及共享服务竞争。错误响应中的部分 usage 被 SDK 报为 0；归档只保留原生已报告数据，实际消耗与费用并不完整。这些时长和 token 数不能作为组合效率排名。

## 实验与协作结论

接入机制已经比旧适配器更接近用户要求，但“探针通过”与“完整 Keep 交付成功”仍有明确距离。当前没有证据证明四种组合中哪一种更好。诊断入口已缩短从运行失败到原生原因的路径，但仍暴露两项限制：用户主动停止在主元数据中被泛化成失败；流错误需要进一步关联原始响应或服务端状态才能完成归因。本检查点只记录这些限制，不继续修改或启动实验。

后续每次实验无论成功或失败，都先停止追加实验并汇报结果，由用户确定下一轮方向。已确认的验收方案可沿用，但不等于授权自动补跑或连续迭代。我的建议是下一轮先在服务恢复后完成一个组合的端到端 Keep，再决定是否展开四组；此建议尚未执行。

本检查点 Factory 源码为 `77572d7`（之后 `c93d186` 只更新任务状态）；Braid 为 `bd0cfcce01dead92e19fc58f34805aa231624927`，SVC 为 `9592494`。两组原始无 Braid 生成使用 `85db6a2` 时的脚本快照；每个 run 的 runner-source、来源清单和哈希是具体事实来源。源仓库分别位于 sources/braid、sources/svc，独立提交，未 push。
