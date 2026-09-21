# 后续细化素材

本目录不是当前首轮配置。以下保留旧六配方及当时的角色设计，当前权威见 [presets.md](../presets.md) 和 [technical.md](../technical.md)。

## 上一版：后续细化素材，非首轮清单

下面保留六组具体配置及来源，方便首轮之后有依据地选用。它们不再代表当前推荐的批次。

### 原六组配置

| Preset | Braid profiles 与模型 | 相对 k3-code 的变量 | 要验证的方向 |
| --- | --- | --- | --- |
| [k3-code](k3-code.json) | coordinator K3；app-engineer K2.7 Code | 参照组合 | 协调与完整功能实施分工。 |
| [k3-full](k3-full.json) | coordinator K3；app-engineer K3 | 实施 profile 及所有 executor 改为 K3 | 更强模型用于实施是否改善业务正确性；不假定它一定最好。 |
| [k3-glm](k3-glm.json) | coordinator K3；app-engineer GLM 5.3 | 实施 profile 及所有 executor 改为 GLM 5.3 | 比较另一模型家族的完整功能交付。 |
| [k3-specialists](k3-specialists.json) | coordinator K3；ui-engineer GLM 5.3 Flash；service-engineer K2.7 Code | 可选专长分工及其模型组合 | 多 profile 是否有助于交互与服务集成；不强制前后端拆分。 |
| [k3-impeccable](k3-impeccable.json) | coordinator K3；app-engineer K2.7 Code | frontend-design 换为 Impeccable | 复刻界面与交互状态的设计、自检能力是否改善；先完成其无人值守适配复核。 |
| [k3-domain](k3-domain.json) | coordinator K3；app-engineer K2.7 Code；domain-engineer K3 | 增加可选领域功能 profile | 复杂规则是否需要更集中的领域理解与交付责任，而不是只按 UI/服务分工。 |

每个 variant ID 为 `factory-<preset>`。K3、K2.7 Code、GLM 5.3、GLM 5.3 Flash 的实际 ID 分别为 kimi-k3、kimi-k2.7-code、glm-5.3、glm-5.3-flash。固定一个 preset 的同一份代码和技能版本完成整套任务，不因中间分数修改它；这些是效果假设，不是已验证的模型专长或排名。

默认根 Issue 直接指派 coordinator，其他 work-item 按明确 profile ID 指派，不经过 label。任何 profile 都可承接 Issue 或 PR，对象职责由共同 Braid 协议定义。profile ID 在所选 preset/run 中解析，有效配置摘要区别同名 profile 的不同配置。

| Braid profile | Model | Reasoning | Skills | MCP | 原生 sub-agents（explorer / executor / reviewer） |
| --- | --- | --- | --- | --- | --- |
| coordinator | kimi-k3 | high* | frontend-design、agent-browser；Impeccable 组替换前者 | 无 | K3 / 本 preset 实施模型 / K3 |
| app-engineer | k3-full 为 kimi-k3，k3-glm 为 glm-5.3，其余为 kimi-k2.7-code | high* | frontend-design、ponytail、agent-browser；Impeccable 组替换前者 | 无 | K3 / 自己的 model / K3 |
| ui-engineer | glm-5.3-flash | high* | frontend-design、ponytail、agent-browser | 无 | K3 / GLM 5.3 Flash / K3 |
| service-engineer | kimi-k2.7-code | high* | ponytail、agent-browser | 无 | K3 / K2.7 Code / K3 |
| domain-engineer | kimi-k3 | high* | ponytail、agent-browser | 无 | K3 / K2.7 Code / K3 |

*high 是目标配置，不是网关已经接受且实际生效的事实。逐模型 reasoning 参数映射仍待核验，不能静默忽略后把运行标成 high。全部使用 Pi RPC + [pi-subagents](https://github.com/nicobailon/pi-subagents)。这六份历史草案未包含 Codex；当前首轮方向已在上表单独提出 Codex 完整组合。coordinator 的 executor 在 k3-full 中为 K3、k3-glm 中为 GLM 5.3、其他组为 K2.7 Code。

coordinator 维护需求、当前产品/系统理解、最终验收目标和整体交付，可自行完成小任务或按需要创建工作项。app-engineer 承接跨前后端完整功能。ui/service 提供可选实现专长。domain-engineer 承接领域规则密集的完整功能，关注身份、权限、业务状态与持久化一致性；不是为一次调查单独创建的 Issue，也不是必须经过的评审节点。

这些分工来自正式初赛功能复刻的能力需求，不把赛事介绍里的几个词硬编码为题目答案。所有组都以实际需求、参考素材与可观察行为为准；视觉 skill 不能为了独特而扩大需求或重新设计给定界面。尚未取得正式初赛完整需求，因此当前只能称为面向该方向的候选设计。

## 单个 profile 内部的原生子代理

下表是物理 Pi 会话内部配置，不是另一组 Braid profiles。它们不自动拥有独立 Issue/PR，也不默认获得完整主会话上下文。

| 原生角色 | Model | Reasoning | Skills | MCP | 返回内容 |
| --- | --- | --- | --- | --- | --- |
| explorer | kimi-k3 | high* | 不额外装领域 skill；保留 SVC 导航 | 无 | 当前问题所需的结论、依据、未知；不做无边界资料汇编。 |
| executor | 按上表配置；domain-engineer 下为 kimi-k2.7-code | high* | coordinator 的 executor：frontend-design、ponytail、agent-browser；其他 executor 与所属 profile 一致；Impeccable 组替换 frontend-design | 无 | 授权局部实现及验证证据；遵守文件责任范围。 |
| reviewer | kimi-k3 | high* | coordinator/app/ui 下为 frontend-design、agent-browser（Impeccable 组替换前者）；service/domain 下为 agent-browser | 无 | 独立检查需求、设计、实现或验收证据；将结论交回父 Agent。 |

技能是可加载能力，按实际任务使用；不要求每次加载全部 skill 或调用全部子代理。SVC 两行 user-scope 导航是全部 Braid profile 与子会话的共同方法入口，不能只在表中写“继承”而不验证隔离环境实际加载。工作项与贡献子会话要能在 run 中关联，但这不改变子代理所属层级。
