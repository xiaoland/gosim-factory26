# 子 Agent 配置与内聚性调查

2026-09-24 读取当前工作树与锁定的 pi-subagents 0.56.0 源码。
以下是配置事实及产品方案，未进行新的模型实验，也不声称每次实际调用均使用默认值。

## 当前配置

用户所列四角色对应 `submission/hackathon_main.py:ROLES/write_roles`，供 codex-base、codex-svc、pi-base、pi-svc 使用。
这些角色属于原生 Coding Agent 内部，不是 Braid 成员。

| 角色 | 模型 | 已装配知识 |
| --- | --- | --- |
| explorer | glm-5.3-flash | SVC 组可用 SVC；正文只有需求/应用只读调查与返回事实。 |
| executor | glm-5.3-flash | SVC 组可用 SVC；正文只有有界实现、协调文件与验证。 |
| browser_operator | deepseek-v4-flash-vision-exp | agent-browser；正文要求图片与页面检查、截图/console/复现。 |
| advisor | kimi-k3 | SVC 组可用 SVC；正文要求独立判断、关键证据与风险。 |

Codex 写入每个角色 TOML 的 model 和 model_reasoning_effort="none"。
Pi 写入 gateway/model，未设置角色 thinking；父启动参数为 --thinking off，模型 descriptor 为 reasoning:false。
这些客户端值不能直接证明供应商关闭了推理；既有网关调查表明采用供应商默认推理，见 `tasks/hackathon-variants/packet.md`。

Codex 角色配置与主指令未制定 fork_turns/fork_context 策略。
补查锁定版本 rust-v0.155.0：V1 spawn 使用 fork_context 布尔值，false 或省略只带初始委派；V2 使用 fork_turns，省略默认 all，none 才不带父历史。
不能用其中一个接口的默认值概括全部调用；本次未核实冻结 Codex 每次 spawn 的实参。
官方文档确认自定义角色配置可指定 model、model_reasoning_effort、developer_instructions，省略的其他会话设置从父会话继承：<https://developers.openai.com/codex/multi-agent>。

Pi 四角色设置 inheritProjectContext:false，控制 AGENTS.md/CLAUDE.md 等项目指令，不等于父会话历史继承开关。
未显式设置 defaultContext、inheritSkills、systemPromptMode。
补查发现新 Hackathon 也没有设置 subagents.disableBuiltins:true；自定义同名角色覆盖内建同名项，不会自动移除其他内建角色。
所以“四个角色”准确指四个自定义角色，不能当作 Pi 运行中只有四个可选角色。
锁定扩展的自定义角色默认 systemPromptMode=replace、inheritSkills=false；不存在隐式继承同名内建角色正文的方法。
若调用及扩展配置也未覆盖 context，未声明 defaultContext 的角色从 fresh 开始；调用可显式选 fork。
Pi 接口为 fresh/fork，而非按最近 N turn 截取；fork 从父会话当前叶子分支。

Braid Factory 的四个 pi-team-* variant 下六个成员目录则都配置五个内部角色：explorer/executor 使用 deepseek-v4-flash，specialist 使用 kimi-k3，browser-operator/vision 使用 deepseek-v4-flash-vision-exp。
五角色都显式 thinking:high、defaultContext:fresh、inheritProjectContext:false、inheritSkills:false、systemPromptMode:append。
executor 选用 svc、ponytail、impeccable、agent-browser；explorer/specialist 选用 svc；browser-operator 选用 agent-browser；vision 无 skill。
这套已经有少量工作方法，不能与 Hackathon 的一两句角色正文混称。

## 因果判断与候选改进

职责边界只回答要解决哪类问题和返回什么，未必给出获得可信结果的路径。
新 Pi 四角色的 replace 默认还意味着不能假设基础 Coding Agent 方法自动保留。
已有 SVC Explore、Implementation、Engineering Judgment、V&V 含相关通用方法。
用户指出前一版本将专业知识扩展成接口、持久化等领域职责，过度解释了输入；当前设计按角色的 SOP 与实际工具选择知识修正，见 [设计](design.md)。
这些角色明确不继承父会话历史，不再保留“必要时 fork”的建议。
SOP 在相应角色的实际上下文中可用，不能仅依赖一句泛化的“SVC 可用”；SVC 正文继续由 skill 提供单一来源，不建立第二份维护副本，也不放进 base 对照组。

## 接口证据入口

- `submission/hackathon_main.py` 的 ROLES、write_roles 与主指令。
- `variants/pi-team-mixed/agents/pi-glm-fast/agents/`，已对照其他五个成员目录的 model/thinking/context/skills 字段。
- 本机锁定包：`~/.cache/factory26/runtime-faf60473273ddeed/node_modules/pi-subagents`。
- 该包 `src/agents/agents.ts` 的 defaultSystemPromptMode 与 frontmatter 解析；`src/shared/fork-context.ts` 的 resolveSubagentLaunchContext；`docs/agents.md` 的 Prompt assembly；`docs/observability.md` 的 session fork。
- `sources/svc/references/sub-agents/`、`references/methods/explore/`、`references/methods/implementation/`。
- Codex 固定版本工具协议：<https://github.com/openai/codex/blob/rust-v0.155.0/codex-rs/core/src/tools/handlers/multi_agents_spec.rs>；V1 handler：<https://github.com/openai/codex/blob/rust-v0.155.0/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs>。
- Pi 实际角色发现还查阅了 agents.ts 的 discoverAgents、applyBuiltinOverrides 及合并优先级；Context7/Exa 真实 tools/list 保存于 runs/factory-subagents-research/，具体接口与限制归 technical.md。
