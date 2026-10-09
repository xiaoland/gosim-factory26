# 截至 2026-10-02 的结果对账与 I14 采用证据

本页是只读调查结果，服务于今晚实验设计；没有启动模型、prepare、恢复、评分或 Factory/Braid 测试。状态以最新回执为准，旧 packet 中较早的动态截面不覆盖后续终态。

## 先回答“过去一天只有一个完整评分”

在“本轮已登记实验”的过去 24 小时口径下成立；这不是对平台全球结果的断言。唯一可作为完整官方结果的是 I13-2 Flash/Sheet：官网 run `f16834f58674`、submission `e69e9764310c`，生成和评测均 `completed`，74/100（74 通过、26 失败）。本地保存的官方 `status.json` 还给出 `run_duration_seconds=10115`、`feature_implemented_count=11`、`feature_total_count=24`、`evaluation_started_at=null`、`tests=[]`、`node_states={}`；`feature=11/24` 是另一统计口径，不能把 26 个失败直接对应到下面的五个缺陷。证据入口是 `runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T174303.462955Z/f16834f58674/status.json`、`collection.json` 及 `tasks/iteration13/i13-2/flash-sheet-score-analysis/{packet,findings}.md`。

| 运行 | 观察到的终态 | 能否算完整评分 | 不能混入评分的原因 |
| --- | --- | --- | --- |
| I13 Flash/Sheet `f16834f58674` | 官网生成+评测完成，74/100 | 是 | 唯一完整结果 |
| I13 Flash/GitHub `7e8ec62670df` | 后续因 ARC 余额耗尽取得 72 条 HTTP 402 `insufficient_balance`，运行被取消并保全 | 否 | 没有评测终态；前期 RUNNING 只是阶段状态 |
| I13 GLM/GitHub `a94a67b4b3d85b` | 真实 GLM 请求成功，随后源容器停止，Git/Braid/native 选择性保全 | 否 | 生成/评分未完成，保全不是交付 |
| I13 GLM/Sheet `8046cfb0695023` | 真实 GLM/Flash 请求成功，随后源容器停止并保全 | 否 | 生成/评分未完成 |
| I13 官网 GitHub 首轮 `346bc3b51b09` | 生成阶段 `FAILED`，score=0、passed=failed=0、未进入评测；Pi SIGKILL 与同 cgroup OOM 计数增加强相关 | 否 | 设施/生成失败，0 不是有效应用零分 |
| I14 baseline/cleaner/reviewer/e2e | 有的只有 prepare，有的取得模型响应；全局随后暂停 | 否 | 没有完整应用交付和评分；`completed`/模型响应不等于评分 |

I14 的 e2e 确有正向运行证据：`runs/iteration14/dx-resume-20261002/` 关联的系统盘回执记录了 10 条成功 assistant、工具活动、`ZHIPU/GLM-5.3-Flash`、2 GiB cgroup 和 Pi `Max address space unlimited`。这只证明运行与资源边界已接通；不证明工具被正确采用、应用完成或评分。GLM baseline 也有成功 assistant 回执，但同样不是评分。

## fresh baseline 的暂停历史

两组 fresh baseline 曾使用同一新版 GitHub 需求 SHA `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8`，暂停前分别留下 5 次和 1 次成功模型调用；这些调用都只读技能/Issue，没有应用成果证据。它们在 20:48 CST 全局暂停时的 attempt、容器和原生现场随后按清理流程删除，相关记录仅作为历史事实保留，不能称为可恢复来源、未删除现场或后续评分候选。

## 74 分目前最可行动的根因

`findings.md` 的五项结论有代码/合同证据，但不是 26 个失败的逐项解释：

1. 第二列筛选覆盖第一列条件。
2. 前端插行/列操作漏传 undo session，后端局部调用正确不能抵消前端接线缺口。
3. 插删列只迁移筛选范围，没有同步迁移条件列。
4. 透视源删除被拒绝后没有关闭确认对话框。
5. 明确单格选择被扩大为已用区域；这是 PR #5 主动写入并在后续交接中保留的错误行为约定，区别于 F1–F4 的实现遗漏。

F1–F4 属于已进入需求/设计但没有完成完整用户操作链的遗漏；F5 是需要重新对照原文裁决的错误决定。真实 Issue/PR 追踪还表明：延后义务没有以完整结果交给消费者 PR，已有的局部测试集合和 ARIA/文案矩阵被当成完整验收。因而当前最强的质量解释是“需求裁决与端到端收口不足”，不是单纯模型等级、cleaner、reset 或 OOM；没有证据量化任何一个因素对 74 分的独立贡献。

## Flash/Sheet 轨迹是否已经分析，以及哪些改进真正进入 I14

已分析，但分析边界是有限的：正向应用集 `runs/iteration13/i13-2-20261001/hosted-sheet-r2/agent.zip` 的 SHA256 为 `7de33f7d23a910ec61e4b639275305cdd05222416ff01f2e757d55e58c1ff316`；唯一 final 批次 `f16834f58674` 的 `workspace.zip`、`status.json`、`collection.json`、`provider-observation.json`、`liveness.json` 和 `archive-index.json` 均保留。已有报告读取了应用源码/合同、有限模块/API观察、Issue/PR 正文与定向 provider session；没有重扫完整 rollout、重跑 UI、读取 hidden evaluator 或修改应用。它足以支持缺陷分类和 I14 方案输入，不足以证明 26 个失败逐项归因或修复后得分。

| 事项 | I14 已落实的通用变化 | 当前判定与剩余边界 |
| --- | --- | --- |
| 明显上下文冗余：关联事件已经投影 PR description，仍机械要求 `pr view` | `828a3da` 将共享事件改为中性详情/正文入口，允许复用已有上下文、按需补缺或核对变化；离线编译和副本 CLI 操作通过。 | **机械修复已落实，运行效果未证实。** 原始 I13 轨迹证明重复读取，但不能据此说技能导致；未来只能比较实际重复查询/上下文成本。 |
| 根/成员固定读技能、固定重读对象的开场 | `a31eb888` 重写 `arc-bench`/`braid-collaboration` 及 references 为 What/Why 与成立条件；`ed9a97bb` 把方法绑定到接手、裁决、采用/完成判断；`b13f4290` 删除 I14 cleaner fast/root 成员的固定技能和对象重读开场。 | **材料/入口已落实，采用未证实。** I13 根读取过部分方法但最终未稳定兑现；I14 冻结包有材料身份和真实技能读取记录，但没有质量收益证据。 |
| 重复同理由评论制造 context 噪声 | `33b9e382` 在通用 context 层聚合同理由隐藏评论，保留一条可追溯事实；相关 packet 记录了 77 条同理由根评论候选。 | **通用实现已落实，收益未证实。** 没有把评论数量下降或 cleaner completed 当成质量改善；仍需真实运行观察是否遗漏必要事实。 |
| 延后义务、错误行为约定和局部 PASS 被当作整体完成 | I14 技能材料与 reviewer/协作方案明确要求交接完整结果、把新语义与原文裁决分开、局部证据不支持整体完成；`a31eb888`、`ed9a97bb` 已把这些成立条件写入通用材料。 | **方案已落实，独立验收未落实。** reviewer 仍是待真实运行的检测机制；不能说它已经发现或修复了 Flash/Sheet 缺陷。 |
| cleaner 负责整理而不替实施/验收者制造正确性结论 | cleaner 职责、快照前提、一次提交和冲突保留已形成方案与准备材料。 | **职责方案已落实，variant 集成/实际 turn 提交未完成。** 不能把 cleaner 设计当作 F1–F5 的修复。 |

四项应用缺陷 F1–F4 都有明确的机械失效点：保留既有筛选条件、结构操作传 `session`、列移动同步条件字段、失败分支清理确认框。这些是应用自身代码/合同问题；I14 没有把它们改成通用 Harness 修复，也不应把它们作为 GitHub 题目的预置答案。F5 是单格选择回退到已用区域的明确语义冲突，虽有源码支持，但必须先由产品原文裁决，不能自动改。当前五项均应视为 **Sheet 应用候选缺陷**：机械项可在用户授权应用修复后定向处理，语义项保留决定；本次没有做任何应用修改。

I14 能采用的通用清单只有：中性事件入口/按需读取、减少机械重复开场、协作方法的成立条件表达、延后义务和局部证据边界、同理由评论聚合，以及 reviewer/e2e 作为公开需求驱动的独立观察机制。它们改变的是输入来源、责任交接和验收判断条件，不直接修复 Sheet 的业务逻辑。实际采用、发现数、修复数和最终残留仍须独立记录，不能用材料 SHA、skill read、编译或 `completed` 状态代替。

## I14 四分支实际在验证的独立假设

| 分支 | 独立假设 | 当前已有证据 | 尚未具备的证据 |
| --- | --- | --- | --- |
| baseline | 干净根成员按原流程能产生可比较的应用质量基线 | I14 曾取得真实模型响应；早期 baseline 另有 GLM 成功回执 | 同一输入下的完整生成、交付、缺陷清单和评分 |
| cleaner | 将 Issue/PR 描述维护、隐藏/解决评论等整理责任移出工作成员，可减少整理成本并保留决定 | cleaner 方案、材料冻结、只读写身份拒绝与恢复准备已验证 | 实际 turn 结束提交、整理耗时/费用、决定遗失或误 hide/resolve 是否下降；不等于直接修复 F1–F4 |
| reviewer | 独立负责人按 GitHub 公开需求和实际候选审查，可能在交付前发现并促成修复 | reviewer 角色/合同和准备包已完成；I13 暴露过局部验收不足 | 一次独立 review 的实际发现、证据对应关系、修复闭环及相对 baseline 的新增成本/收益 |
| e2e | 以真实浏览器操作链和失败后状态核对，可能发现静态验收遗漏的连续状态缺陷 | e2e 已有真实模型/工具活动和资源采样正反馈 | 工具是否被 Agent 实际采用、实际候选覆盖情况、应用完成与独立评分 |

“协作材料/arc-bench 方法”是跨分支的共同条件，不是已经证明有效的第五个对照。I13 中根读取方法、部分平台交付采用，但后续接手和合并判断没有稳定兑现；不能以技能读取次数代替效果证据。

当前优先级、设施边界和后续实验决策统一归 [overnight-plan/design.md](../design.md)；本结果 cell 只保留评分证据、已进入 I14 的通用变化和待验证机制，不重复执行方案。

e2e→reviewer 的 seed gate、A→B 身份和三次机会机器触发事实见[实施接缝](experiment-entry.md)。

### 证据入口

- I13 当前矩阵：`tasks/iteration13/experiments.md`、`tasks/iteration13/i13-2/packet.md`
- Flash/Sheet 正式结果：`tasks/iteration13/i13-2/flash-sheet-score-analysis/{packet,findings}.md`
- I14 方法与结果对账：`tasks/iteration14/evidence.md`
- 当前优先级与实验方案：`tasks/iteration14/overnight-plan/design.md`
- e2e/reviewer 实施接缝：`tasks/iteration14/overnight-plan/cells/experiment-entry.md`
