# Corpus 场景耦合审查

范围是参赛包实际装入的 27 篇 SVC 文档；`corpus/AGENTS.md` 是未打包的维护者指引。
判断标准：SVC Corpus 讲可复用的软件工作方法；本场比赛的任务形态、素材格式、无人值守约束和运行机制由 Factory 指引、任务输入和 Harness 承担。

| 发现 | 处理 | 原因 |
| --- | --- | --- |
| Product Design 为命中 `screenshot` 检索而增加截图与参考图片枚举。 | 撤回，保留原型、渲染替代、交互回放和直接观察等通用方法。 | 检索词缺口不足以让一次赛题的素材形态成为方法指导。Factory 生成 prompt 已要求阅读参考图片。 |
| Corpus 总入口限定为单个 Web 应用需求和无人值守 Factory run。 | 改为软件任务入口，并按任务请求、权威需求和当前观察路由。 | 这些运行条件由 Harness 与任务输入提供。 |
| Task Packet 和 Sub-agent 入口使用 Factory task、application、issue 协作措辞。 | 改为普通任务、任务产物和当前 Agent 内的子代理边界。 | 工作方法不应预设 Braid 的 Issue 分配模型或固定产物类型。 |
| `svc task init/grow` 与 `tasks/<task-id>/packet.md`。 | 保留。 | 它们是 SVC 自身的可执行入口和产物路径，不是 ARC-Bench 的协议。 |
| Test Design 中的 DOM、持久化等例子及对 requirement 的引用。 | 保留。 | 这些例子存在于通用 SVC 原文，用来说明不要把实现细节误当需求；没有绑定赛题或 Runner。 |

检查打包文档中的 Factory、ARC-Bench、Web application、screenshot、reference image、Braid、runner 等标记，不再出现赛题或运行机制名词。
这项检查只证明本次可见过拟合已移除，不能代替后续真实任务对方法有效性的验证。
