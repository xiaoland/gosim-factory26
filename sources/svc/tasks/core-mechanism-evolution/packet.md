# SVC 核心协作机制演进

## 目标

演进 SVC，使最常见的一个 Human——以及通常不超过 3～5 人的小团队——能与
Coding Agent(s)：

1. 更高效、精细地协作，并对齐产品与技术品味；
2. 更好地完成范围模糊、复杂交错的长任务；
3. 以更低的长期变更成本驾驭大型、长生命周期软件。

## 边界

- SVC 服务 Sir 的个人开发体验，可以有明确主张，但 Human 的事实、因果、技术和
  方案判断仍可被验证、质疑和修正；最终从事实、逻辑、利益相关者价值和长短期
  ROI 作判断。
- Review、探索、思考和 Task Packet 整理默认自主进行；durable mutation、外部效果、
  commit/release 仍服从适用权限。
- 渐进式披露与 `S-SIMPLE` 是根本约束：没有真实压力，不增加文件、目录、概念、
  schema、Agent surface 或 automation。
- 能力模型已经接受；Source Landing 的 durable mutation 已获 Sir 明确授权并完成。
  未获授权的 commit、release 与外部效果仍不执行。
- 所有 gleanings 都是可反驳输入；本轮设计只是可被真实任务修正的 provisional model。

## 如何判断本阶段完成

P2 完成时要有：符合浏览直觉且无 competing owner 的 source tree、由 `src/` 局部拥有的
Corpus 撰写原则、五个 Track 的 compact source、Task Packet template family、受控的
`task init/grow`、明确的公开路径迁移，以及通过机械验证的 catalog/wheel projection。
这些结果证明 landing 内部连贯；真实任务效果仍须在后续 Consumer Tasks 中检验。

## Task Map

`P1 — Capability Model` 已关闭。`P2 — Source Landing` 已完成真实共享 barrier：
五个 Track 都参与，因为 Working Protocol 只有在其它 semantic owner 有明确落点后才能
安全收缩；五个落点也必须共同遵守同一套 repository layout 与 corpus 撰写原则。

| Track | 当前状态 | 当前 Source Landing 工作 |
| --- | --- | --- |
| Task Packet | `TP × P2` satisfied; reopenable | `task-packet/index.md`、渐进深度、template family 与受控 `task init/grow` |
| Working Protocol | `WP × P2` satisfied; reopenable | `working-protocol/index.md`、对称的 `methods/` 与 `src/AGENTS.md` authoring owner |
| Sub-agents | `SA × P2` satisfied; reopenable | `sub-agents/index.md` 路由两种 consumer-relative contract |
| Verification | `VF × P2` satisfied; reopenable | `verification/index.md`，不集中所有测试和 evidence |
| Tastes & Design | `TD × P2` satisfied; reopenable | `methods/design/index.md` 路由到 `taste/implementation/index.md` |

详细工作状态由 [`task-map.md`](task-map.md) 和五个 Cell 管理；当前 Source Landing
整合见 [`design/84`](design/84-source-content-migration-and-review.md)。

## 当前能力模型

### 1. Task Packet

Task Packet 是服务于 Task completion 和 Human-Agent coordination 的 volatile
filesystem package，不是 monolith 文件。只有用 Human 协作语言写成的短小
`packet.md` 是 universal surface；其它信息/工作模块只按真实压力生长。

- `Track`：任务中横向持续存在的管理义务。
- `Phase`：真实共享语义 barrier；不能为矩阵整齐制造虚假 barrier。
- `Cell`：一个 Track 在一个 Phase 中的工作控制单位。
- `Plan`：Cell 或小任务内的线性、可局部预见路线；允许 TBC。
- `Slice`：能独立产生有用 return 的计划单位；在所属 Plan 内按统一序列递增，后缀表达
  return scope，例如 `03-IQ`、`04-DS`、`05-IM`、`06-VR`。
- `Step`：使 Slice 更易掌控的下一动作；`Assignment` 是 Slice 内的委派单位。

Inquiry、Design、Decision、跨 return 的 Verification 各有 semantic owner；
Task map/Plan 只拥有工作控制状态，不复制它们的完整内容。

### 2. Working Protocol

Working Protocol 是 SVC 的 Agent-facing operational kernel 和导航入口，不是拥有
所有内容的 semantic umbrella。它连接 obligation/return、method/feedback、
action/effect authority、observation/integration/disposition，并按压力导航到其它 owner。

基础 Working Methods 是 Explore、Design、Implementation。它们像桌上的工具，可随时
组合使用，没有 activate/pause/exit lifecycle；仍须诚实返回 residual，不能借“放下方法”
丢掉 Task obligation。Verification 是横切能力，不是第四种 Working Method。

Human fine control 来自 outcome、taste、constraint、effect、evidence、stakeholder、
cost/reversibility 等语义把手，而不是 Working Method telemetry 或持续审批。只有 Human-only
贡献或早期纠偏价值足够大时，才压缩成一个 decision-ready 问题。

### 3. Sub-agents

是否委派同时看三个因果维度：attention partition、trajectory shaping、capacity scaling；
它们不是角色分类，也不能套一个统一公式。必须与 Primary 直接做、渐进加载、确定性机制、
Human-only 判断比较完整成本。

Primary 保留 Task、Human、跨边界与 material residual authority。Child 只接一个适配其
真实 model/context/tools 的 bounded Assignment，自行渐进读取 canonical shared guidance，
Primary 只补 Task delta、material handles 和必要 snapshot/freshness boundary。

结果路径取决于 consumer：

- **Explorer**：处理 bounded、高熵、consumer-relevant 的信息问题；返回 question-shaped
  report 给 semantic consumer。Primary 需要理解报告，所以不放一个通用 validator；抽查
  关键来源属于消费/继续 Inquiry，其成本必须计入委派。
- **Executor**：围绕一个 bounded intended change 做 realization-feedback loop；实际
  candidate + support 进入独立 validator 和 effect/integration gate，局部失败回 Child 修复，
  只有 material design/authority/effect mismatch 才升级给 Primary。

不先引入 Reviewer、validator Agent、doc writer、rule resolver、Task Packet manager、generic
QA、固定团队流水线或通用 Assignment schema。完整提案见 [`D-087..D-088`](decisions/D081-D090.md)。

### 4. Verification

最小链路是：`owned claim → observation surface/oracle → evidence + trusted-base scope +
residual → consumer-owned disposition`。

- Product/Technical Design 拥有 expected claim；Test Design 设计有区分力的 scenario、
  observation、oracle/invariant/Human criterion；Implementation 构造机制；Verification
  执行并解释；consumer/effect authority 决定 accept、waive、integrate 或 reject。
- 选择与损失相称的最小可信机制；compiler/type/schema/constraint、已有 qualified module
  guarantee、runtime/integration/external readback、metamorphic/differential、fuzz/shadow、
  statistical/Human observation 都只是按 claim 选择的手段。确定性不等于有效性。
- AI 同时生成实现、fixture、oracle、test 时，绿色结果只是强相关的候选证据；只有预期
  损失值得时才增加真实输入、独立机制或关系型挑战。
- Verification 分布在工作中；Task 根 `verification.md` 仅在跨 return/Cell 的 claim、证据、
  residual 需要共同综合或 requalification 时生长，不是最终阶段。

完整提案见 [`D-089`](decisions/D081-D090.md)。

### 5. Tastes & Design Ability

Taste 是帮助 Design 在多个可行方案之间判断的 compressed consequence knowledge。
项目 Product/Technical truth、Sir 的个人 preference、可反驳的一般 design judgment、Task-local
hypothesis 具有不同 authority，但不强制做成 metadata schema。

Taste 由 Design 按 Product/Technical/Test projection 和当前 recurring design pressure 渐进加载，
而不是堆成全局格言。高价值条目要能说明：优化的 consequence、适用 pressure、默认选择和
因果理由、成本/counter-pressure/弱化条件，以及合适的 observable example/challenge。

- UI/UX 用 reference、rendered alternative、interaction replay、prototype 和 Human perception。
- Architecture 用 authority/dependency topology、lifecycle/change scenario、migration 和传播义务。
- Implementation 用 code/data/API shape、命名、contracts、tests、assertions、observability 和
  future-change cost。

ECCA 的 semantic locality、ownership/contracts、vertical coherence、explicit propagation 等
思想作为可反驳默认被消费，但不强制 branded architecture、目录、ports/adapters、ADR 或
modular monolith。完整提案见 [`D-090`](decisions/D081-D090.md)。

## 当前 Source Landing 设计

Source Landing 有两个耦合结果：repository layout 负责 semantic owner、入口和渐进深度；
corpus writing 负责用低歧义、低冗余、合适的信息载体表达这些内容。五个 Task Track
不会直接变成五个 source 目录。

落地结果移除了没有信息价值的 `sections/`，也没有引入同样宽泛的 `work/`。每个可导航语义
概念统一使用 `<concept>/index.md`：根层是 `working-protocol/`、`task-packet/`、
`sub-agents/`、`verification/`、`methods/`、`project/`、`taste/`、`extensions/`、
`templates/` 与 `migrations/`；每层 `index.md` 都是 compact semantic interface，
不是链接堆。

结构对称约束节点形状，不要求镜像相同内容。已有独立 consumer/trigger 的 Task Packet
planning/information/growth、Explore Agent Task Analysis、Design Product/Technical/Test、
Sub-agent Explorer/Executor 及部分 project capability 成为 depth；Working Protocol、
Implementation、Verification、Implementation Taste 和 Unit TDD 目前可以只有
`index.md`。以后长出 depth 不改变 canonical entry address。monofile 压力证据见
[`design/86`](design/86-progressive-source-depth.md)，修正后的目录语法和完整树见
[`design/87`](design/87-symmetric-corpus-navigation.md)。

复审进一步确认：这不是单纯移动几个 Markdown。Corpus path 是 catalog/wheel/lookup 的
公开地址，且当前 dirty worktree 已有旧版 `task init/grow`。因此
[`design/88`](design/88-p2-review-and-realization-outline.md) 统一拥有 exact content move、
`src/AGENTS.md` 排除、完整 template family、CLI 行为、major migration 和四段式实现轮廓。
Template family 提供 `packet/plan/task-map/cell` 与
`inquiry/diagnostic-matrix/design/decisions/verification` 积木；只有 `packet` 由 init 自动创建。

Corpus 撰写标准由未打包的 `src/AGENTS.md` 局部拥有；catalog/wheel 必须精确排除它并保留
其它 Markdown 的 fail-closed 规则。`task init` 只安全创建最小入口并立即触发 shape
preflight；`task grow` 从静态 guide dump 改成 packet-specific、read-only growth brief，
不冒充 semantic grow engine。完整修正见
[`design/85`](design/85-browse-first-layout-and-task-cli.md)。

## 下一步

P2 已按 [`design/88`](design/88-p2-review-and-realization-outline.md) 落地：对称目录入口、
九个 opt-in Task Packet templates、compact entry contract、read-only growth brief 与 `13.0.0`
major migration 均已通过文档、projection、完整测试和 fresh-wheel smoke 验证。作为对称
导航的 follow-up，`lookup --path a/b` 与 `a/b/` 现在都解析到 canonical `a/b/index.md`，
但 catalog 和返回身份仍只有 Markdown 路径。当前只需向 Sir
交付精简复审结果；不 commit 或 release。后续真实 Consumer Tasks 继续检验 Human attention、
terminal quality、委派/验证成本、retrieval value、系统变更成本和简单任务 overhead，并可据此
重开相应 Cell。
