# I13成果对账与I14承接依据

2026-10-03。唯一完整登记结果为官网Flash/Sheet `f16834f58674`，74/100（74通过、26失败）；其余不完整运行已按用户授权清理，历史running/pending不是当前现场。完整提交包、最终workspace和评分原件保留在WorkSSD。本文保存I13成果与I14承接依据，当前实验设计和授权归[夜间packet](overnight-plan/packet.md)。

分析对应的通用改进已进入当前I14源码/材料：`828a3da`按需读取事件入口、`a31eb888`与`ed9a97bb`需求/协作方法的成立条件、`b13f4290`移除固定技能与对象重读开场、`33b9e382`聚合同理由评论，以及本次简短通知窄改。实现、采用和质量收益分别判断，不能称这些变化已经修复旧Sheet业务逻辑。最新验证优先级为e2e→reviewer/cleaner→GLM-5.3，OOM须官网完整运行；独立审阅只自动修明确机械缺陷和已证上下文噪声，语义/证据不完整项保留。逐项落实与限制归[结果对账](overnight-plan/cells/results-evidence.md)。

I13的目标与过程验收归原packet和i13-2/process-acceptance.md。完成后对每个目标分别核对源码/分发、实际触发、结果采用和最终作用，将有证据的未达成或优化机会交给I14；未触发记未覆盖，不预设失败。当前承接候选包括协作载体归属、packet在过程中采用与发布、过时讨论整理、原生连续性/资源等待、工具与子代理委派收益、需求树的跨枝合同及最终应用验收。I13-2首批已经证明两项原Pi接续、九份历史prefix保持、Sheet资源等待后继续、AGENTS与共享packet发布；这不证明其它目标已全部成立。

| 当前已观察的问题/边界 | I14如何承接 | 仍需等正式运行核对的内容 |
| --- | --- | --- |
| Sheet PR曾复制稳定规格，packet事后补写/未发布；I13-2已修材料并补发布。 | cleaner实验检验整理是否确实减少负责人分心，而不重新镜像项目文档。 | 之后是否继续正确归属、采用/更新packet、是否有返工。 |
| 根hide后代语义已在I13-2实现；旧native文字不会被擦除。 | cleaner使用当前hide/resolve语义，衡量后续投影与reset成本。 | 自然整理采用与误隐藏/遗失决定；实现存在不代表收益。 |
| PR默认非draft，ready不是请求review；Local无独立review责任。 | 新创建默认draft已直接修；review方案绑定具体候选与验收责任。 | 独立审阅能发现何种问题及最终质量增量。 |
| 官网OOM、热恢复与启动存在大量设施人工劳动。 | 实验设施独立会话负责自动化；I14只承接必要harness接口/配方变化。 | 原故障、恢复与新运行效果分别读回，不把设施失败当应用零分。 |

## TypeScript选择的实际依据

用户要求若I13已自然采用TypeScript则忽略新增提示。只读检查本地完整暂停副本与官网保全clone后，该条件并未对全部应用成立：GLM/Sheet的已发布develop@577d64b0c11dffad5ae7f188b95f17867f5e8f33仍有backend/src/app.js、db.js、errors.js、repository.js、server.js、validation.js六个业务源文件；前端为TS/TSX。GLM/GitHub PR2与Flash/GitHub各PR的应用source为TS/TSX，但前者当时develop尚只有六份入口文档，不能把未发布PR当最终交付。此前Flash/Sheet只读的是采集器的部分提取目录，不能凭其中缺src证明语言选择。本次终态Git导出已确认Flash/Sheet前后端业务源码均为TypeScript/TSX；这修正该题的证据缺口，不改变本地GLM/Sheet仍有JavaScript业务源码的既有事实。

因此保留I14 root issue中的偏好：使用JavaScript生态实现应用时，前后端业务源码采用现代TypeScript，复用所选框架的类型支持；正常构建产物与必要的工具配置不因此要求迁移。该规则只放未来I14根Issue的交付约定，当前I13冻结包与工作区不改，不在各profile/skill重复。I14 variant建立时同步移除其继承条件中“不为此预先指定TypeScript”的冲突表述。完整路径、源码计数、package与published-ref读取归 runs/iteration14/language-choice.json；它们是阶段观察，不是最终应用判断。


## 官网Flash/Sheet正式结果与I14-1承接

终态来源为 `runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T174303.462955Z/f16834f58674/`，交付 `main@4812a40400b55f593c061ae180c6a609e9a72400`。官网74/100与feature 11/24为不同统计口径；tests/node_states为空，不能逐项解释26失败。费用字段为token_cost_usd=49.087573、currency=CNY，不称美元。

[独立分析报告](../iteration13/i13-2/flash-sheet-score-analysis/findings.md)定位了五个最终代码/合同缺陷：第二列筛选覆盖第一列条件、前端行列操作遗漏undo session、插删列只迁移筛选范围未迁移条件列、透视依赖拒绝未关闭删除确认框，以及明确单格选择被扩大到已用区域。前两项有无网络的现有模块观察，后三项为明确静态数据流或原文合同冲突；尚未完整UI复现，也不能对应官网失败编号。定向native与Git证明最终业务代码未在验收后漂移；新验收负责人主要复跑实现者已有用例，阶段延后义务未补为完整用户旅程。

第二轮直接回查provider sessions、Issue与PR后，[报告](../iteration13/i13-2/flash-sheet-score-analysis/findings.md)已纠正归因：F5是PR #5主动写入设计packet的错误单格回退约定，后续接续成功保留，并在范围外D2被搬移的反馈出现后只修测试选择动作；F1–F4属于已可见要求未完整落实，尚无明确缩减语义的决定证据。F2后端/session测试与漏接的前端均由同一会话完成，不能统一归因跨Agent交接。decision-trace.json保留具体时点、公开操作与来源。

I14-1应分别处理错误约定与实现遗漏：前者核对新增产品语义与原文的冲突，后者观察完整UI操作链、连续状态保留、字段迁移与失败后界面。专门reviewer可检测这些缺陷，但不等于消除生成原因；其独立判据与实际发现能力仍待获授权比较。延后事项继续留在现有packet，直到消费者场景取得证据。没有证据支持把cleaner、reset、资源阈值或模型等级当这些缺陷的已证根因；同样不能把74分整体解释为LLM单纯遗漏。报告用于开发侧决策，不向仍运行的生成Agent传递隐藏反馈。

第三轮Issue/PR使用调查补充：并非载体缺席，具体不足是延后事项在消费者PR中被缩成局部错误路径、已披露的单格新语义未按原文裁决、共享API合同改变未核对所有调用方，以及关键ARIA/文案矩阵和已有集合通过被用作完整需求完成证据。种子分歧#79→#80→#108/#109的真实闭环证明相同载体能发挥作用。优先改善现有PR的结果交接、行为分歧裁决与合并判定，不先增加Issue/模板。对减少缺陷漏出有具体机制支持，对减少首次生成遗漏及收益幅度尚无比较证据；不能把验收发现更多等同LLM产生更少。具体评论、provider操作与PR4历史合同见分析目录issue-pr-use-trace.json。

第四轮技能作用核对：arc-requirements在I13已改名arc-bench。本run确实冻结分发；根读主技能、reading与platform，基础读主技能/platform，advisor读platform。根公开援引方法处理图文差异，正式平台路径验证有采用。功能与最终验收native未找到arc技能读取，tracing reference无人读；这不证明完全没接触方法，也不能解释首次编码遗漏。主技能已有原文权威、完整操作、延期收口及局部PASS非完整覆盖要求，但后续决定未兑现。I14检验应从“方法是否改变责任/合并判断”取证，入口和读取只算前置条件，不先加篇幅/模板，也不将一次补读当充分修复。详见报告及arc-skill-use-trace.json。
