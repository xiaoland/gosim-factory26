# 增强前的内容审查

2026-09-24，只读审查加 task packet 整理。
本页是发现与推断，不是已经应用的 Corpus，也不是对模型能力的实测报告。

## 依据与实际消费

- 用户本轮六组观察，以及此前关于 shift-left、语义权威、真实验收和避免规则堆叠的纠正。
- `~/.codex/AGENTS.md`：当前个人指南，作为方法来源，不复制其语言偏好、审批/提交规则或 Advisor 约定。
- [V&V 原始方法](../../verification-system.md)：产品意图、行为性质、观察、oracle；证据边界和全生命周期成本。
- [既有会话分析](../../development-loop-review/analysis.md)：已有分段调查结果；本轮没有重读完整历史 trace，也不将其推断当作新的实测。
- 实际参赛内容 `sources/svc/corpus/`，入口 `harness/skills/svc/SKILL.md`。
  variant 的 run.py 和 build.py 显式复制/选择这份 Corpus，开发树 `~/Development/svc` 不会自动同步进去。

## 已有能力、实际缺口与建议归属

| 观察 | 现有正文 | 缺口及判断 | 建议归属 |
| --- | --- | --- | --- |
| V&V 应保护产品意图与实现自由 | design/test.md:4–36 已有性质、oracle、输入选择、双向辨别、成本和真实依赖；verification/index.md:9–30 已区分无证据和失败、验收与诊断 | 这些原则不能再追加一遍。缺少从当前待决问题选择证据、依据结果决定下一步的连贯使用路径。 | design/test.md 负责证据方案；verification/index.md 负责执行后的判断与继续条件 |
| 实现前投入注意力 | Factory implementation/index.md:7 只有按当前证据做线性计划；开发树同文件已有真实协议等高代价未知的提前核实段落 | 先前通用改稿没有出现在当前参赛文本。应恢复其判断依据，并防止“每项改动都先做模拟预演”。 | implementation/index.md；Technical Design 仅说明会改变方案的接口事实 |
| 识别打转、循环、原地踏步 | Explore 的 sufficiency/economics 已论述足够与成本，Implementation 只泛称不符合方案时回到 owner | 抽象原则没有描述实际信号：同一假设、同一失败、同一检索被重复，却没有支持/排除解释或改变路线。 | methods/index.md 的工作转向，Explore 的判别性调查 |
| 低 ROI 委派 | sub-agents/index.md:3 已要求收益覆盖委派、验证、集成成本 | 不缺一句“考虑 ROI”，缺与直接工作/确定性工具的比较，以及下游如何真正用到返回结果。 | sub-agents/index.md，角色页仅保留角色差异 |
| 不靠 reviewer 阅读实现找问题 | verification/index.md:23 已说另一个 Agent 同意不是独立证据；sub-agents/index.md:11 再说一次 | “不是证据”尚不能防止默认派人泛读代码来猎错。应明确：基于真实差异调查，代码阅读用于解释机制；验收依赖适合该性质的机制。 | verification/index.md 为唯一原则归属，委派入口引用 |
| 并发/时序边界不断增多 | engineering-judgment.md:最后一句要求反复矛盾时回看 model，前面有 authority/lifecycle 原则 | 先审问题是否必要，再审职责与状态归属，最后才选实现结构；现有措辞容易被理解为继续增加抽象。 | engineering-judgment.md，Technical Design 引用 |
| 没有固定答案时仍能推进 | product.md:11 允许选择一致方案并记录假设；test.md:6 禁止用缺失意图编造验收规则 | 两者本来可兼容，但没有讲清：提出有依据的产品选择不是捏造用户要求；开放选择需要判断，不能伪装成客观 oracle。 | Product Design；Test Design 区分需求、设计假设和质性判断 |
| 不同模型的能力结构不同 | Explorer/Executor 按信息与执行工作分工，没有绑定模型 | 不应加入未经验证的模型排名。“范围有界”也不等于“有标准答案、认知难度低”。型号配置在 Harness；Corpus 只讲能力与任务匹配。 | sub-agents/index.md 的执行者选择，Product Design 的自主判断 |
| Task packet 对打转的帮助 | task-packet/index.md 已要求更新路线/证据，information.md 有 hypothesis 和 residual | 无需再造进展账本；让当前解释、被排除的方向与下一项判别进入已有 inquiry/plan，替换过期答案。 | task-packet/information.md 小幅明确；不增加模板 |

## 行文问题

Design 中 forces/commitments/projections、Explore 中 Frame/keyness/residual、Implementation 中 Slice/qualification 等术语连用，使读者先学方法本体再判断任务。
这些区分有的有用，但定义职责占据了本可解释“当前该怎么判断”的位置。
应以真实问题、判断依据、动作与返回结果组织正文；需要的精确术语放在所属深层页，不在每个入口重复边界声明。

verification.template.md 仍写“packet's terminal Verification”，与 information.md 的“not a final Task phase”冲突。
corpus/AGENTS.md 仍要求 Catalog/wheel 检查，已不符合 skill 直接装载方式；它是维护者材料，不是参赛 Agent 提示词。
以上是可直接定位的文档事实；本轮没有证据证明某一个措辞导致了之前某个 run 的失败或低分。

## 原则的适用限制

新信息可以是排除一个解释或确认等待外部条件，不要求每一步都产出代码。
同一操作的重试也可能合理，前提是条件变化、暂态故障或取得新证据的机制使它值得。
复杂设计不必然错误；先判断复杂性来自真实要求，还是我们自行引入的承诺。
能力不足、工具缺陷、反馈不可见和不合理任务拆分都可能造成打转，不能全部归咎于模型注意力或提示词。
“模型不善开放探索”目前是选人与分工的待核实假设，不能按品牌或角色名称固化。
