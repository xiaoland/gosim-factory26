# Pi minimal：能力采用与原生依赖诊断

2026-09-29。用户要求停下调查；GitHub run `59aaf58e7462bc` 已通过停止其adapter及所属容器终止，原始workspace保留。I11不受影响。本页是诊断与修复建议，尚未修改variant或重跑。

## 观察与证据限度

原生会话只有GLM主模型实际调用；未见subagent/list、advisor、mcporter或SKILL.md读取。两次图片read返回image。模型在阅读需求后识别任务复杂，随后自行选择Express/SQLite/React、自建认证和组件并进入大块实现，未咨询advisor或读取版本文档。未使用不自动等于能力失效，也不能由配置存在推导可成功调用。

包入口明确传入subagents/PBB扩展和七个--skill；advisor落在PI_CODING_AGENT_DIR/agents，原生发现逻辑使用同一路径；Pi技能加载不受--no-context-files禁用，默认系统提示词会生成name/description/location并要求匹配时读取。stderr为空，未见扩展加载错误。但本轮没有保存发送给模型的最终system/tools，因此“实际请求中工具可见”仍缺直接证据。

## 问题、原因与最小修正建议

| 问题 | 证据支持的原因/边界 | 建议 |
|---|---|---|
| 大型任务未咨询advisor | 指令只说可以调用、不是必经步骤；描述未把独立判断连到具体决策时机。扩展默认full工具说明还包含多种当前用不到的编排能力，但其因果贡献未证实。 | 在重要技术选择和大块实现前，带原需求/候选方案/不确定性咨询advisor；不加explorer/executor角色或SVC流程。用扩展现成compact工具说明，降低无关编排说明。 |
| 技能没有读取 | 身份接线无明显缺口；auth/organization描述以已选Better Auth为中心，自建认证路径绕过技能。Ponytail原则已内联，没读正文不等于原则没生效；Sheet专用技能不应在GitHub强制使用。 | 在能力入口按问题介绍技能（认证、会话、组织权限、可访问交互），说明选库/自建决策前先读取匹配技能；不强制使用Better Auth或遍历所有技能。 |
| Context7/Exa没用 | 仅提供工具用途与schema查询法；模型对依赖兼容行为直接作出判断。无请求所以不能断言网络故障。 | 把查证触发绑定具体不确定性：依赖版本/API/构建/兼容不确定先查官方文档，Context7优先匹配库；需外部资料时Exa。没有外部问题时不强制检索。 |
| 原生依赖首次不可用 | sqlite专项报告：首次pnpm安装后缺binding，显式onlyBuiltDependencies后构建成功；未确认首轮prebuilt下载细节。 | 指引依赖安装后先验证实际load，原生依赖明确构建脚本与目标Node ABI；避免直到主体代码完成再发现。Node24成功不能替代Node20验证。 |

下一轮真实接续时保留最终发送的system prompt和tool名称/描述及skill诊断，用运行证据区分“未暴露”和“模型没用”，不写模拟测试。不要通过临时模型探针或强制所有工具各调用一次冒充真实工作采纳。

当前不恢复：用户要求是诊断和讨论如何修复，先给出方案。保留半成品，后续获授权修正后可以接续，不必重新生成。
