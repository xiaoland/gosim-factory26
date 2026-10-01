# I11 GitHub：原生子 Agent 的正向过程链（增量）

仅针对最终 replay **e68661975b53** 所对应源生成 `pi-braid-i11--hackathon--github-0d0cb6e9982fc1`；最终 4/100、1/47 的身份/制品证据沿用 [I11 运行报告](i11-e68661975b53.md)，不以评分反推过程。本文先从当时需求、委派与行动重建，最后核对交付。没有新增评测、模型调用、应用运行或测试；下述测试均是历史日志中的生成应用验证。本次不扩展 Pi Minimal 或 Sheet。

## 资料边界与定位

复用 `tasks/iteration11/run-audit/github/cells/m4-m5/report.md` 作为导航后，回读下列原生 JSONL 的关键消息。不是全运行所有会话通读。08:04 snapshot 只能证明早期历史，后续 M6b 来自最终源 archive 已保留的会话；不把某一截点材料当终态。

路径前缀 **S** = `/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github/snapshot-01/work/native-homes/`；**N** = `/Volumes/WorkSSD/Development/factory26/runs/analysis/i11-github-e68661975b53/20260930T033923Z/native-preserved/`。以下标签均为原始文件，`L` 是该 JSONL 物理行号，不是展平 view 的 Record：

| 标签 | S/N 后的路径 |
|---|---|
| I8-start | S + `pi-glm-fast-01a0ebee-ce8f-7730-9269-3864fbb38de2/sessions/--workspace-template-.factory26-20260929-042409-1202e245-braid-state-worktrees-issue-8-pi-glm-fast-g1--/2026-09-29T06-51-32-373Z_01a0ebee-d295-71da-bcb3-f758d6d5f668.jsonl` |
| I8-next | S + `pi-glm-fast-01a0ebee-ce8f-7730-9269-3864fbb38de2/2026-09-29T06-51-32-373Z_01a0ebee-d295-71da-bcb3-f758d6d5f668.jsonl` |
| V5 | S + `pi-glm-fast-01a0ebee-ce8f-7730-9269-3864fbb38de2/2026-09-29T06-51-32-373Z_01a0ebee-d295-71da-bcb3-f758d6d5f668/d9c2373b-dae9-4c09-8eaa-7d1a7d898e5a/run-0/session.jsonl` |
| A5-design | S + `pi-glm-fast-01a0ebee-ce8f-7730-9269-3864fbb38de2/2026-09-29T06-51-32-373Z_01a0ebee-d295-71da-bcb3-f758d6d5f668/ec4d81d6-77cf-45a2-af84-dd3484f6b662/run-0/session.jsonl` |
| P15-start | S + `pi-deepseek-fast-01a0ebf8-5cf2-73a1-ade8-6d82357844a5/sessions/--workspace-template-.factory26-20260929-042409-1202e245-braid-state-worktrees-pr-15-pi-deepseek-fast-g1--/2026-09-29T07-01-58-325Z_01a0ebf8-5fb5-70da-a773-18a0d10a7f4d.jsonl` |
| P15-next | S + `pi-deepseek-fast-01a0ebf8-5cf2-73a1-ade8-6d82357844a5/2026-09-29T07-01-58-325Z_01a0ebf8-5fb5-70da-a773-18a0d10a7f4d.jsonl` |
| A5-impl | S + `pi-deepseek-fast-01a0ebf8-5cf2-73a1-ade8-6d82357844a5/2026-09-29T07-01-58-325Z_01a0ebf8-5fb5-70da-a773-18a0d10a7f4d/088d04b0-1a9c-43b6-9254-fd043e6d7623/run-0/session.jsonl` |
| E5 | S + `pi-deepseek-fast-01a0ebf8-5cf2-73a1-ade8-6d82357844a5/2026-09-29T07-01-58-325Z_01a0ebf8-5fb5-70da-a773-18a0d10a7f4d/38367068-3731-4e48-b580-b31de57cfbf4/run-0/session.jsonl` |
| I10-start | N + `065faa32-2026-09-29T16-09-22-776Z_01a0eded-8a58-762d-bc11-f3200d8a7401.jsonl` |
| I10-next | N + `f7e62c05-2026-09-29T16-09-22-776Z_01a0eded-8a58-762d-bc11-f3200d8a7401.jsonl` |

同名主文件与 `sessions/` 文件是原始会话的前后片段，不能选一个当全记录；本表已分开。archive 成员与哈希映射见 `N/../selected-native-index-v2.json`。

## 1. 当时有哪些角色，而非当前源码有哪些角色

历史运行内 **I10-next L22 `60be4431` 16:12:54** 读取实际 native advisor 配置：`factory26/kimi-k3`、fresh context、`inheritProjectContext:false`、`inheritSkills:false`，只读工具；显式技能为 svc-documentation/design/investigation/verification 等。其正文要求“先理解原始问题…当前方案只是候选”，要求反例和缺失事实；并实际附带 SVC Design Workflow 文本。配置不是当前 `variants/` 的推断。

**I10-next L30 `c13e63d9` 16:13:30** 读取本次 `/workspace/submission/agent/agents/pi-deepseek-fast/agents/` 文件，显示：advisor=kimi-k3；explorer/executor=deepseek-v4-flash；vision/browser-operator=deepseek-v4-flash-vision-exp。executor 有 write/edit，explorer 只读；vision 仅 read。这些角色存在不等于都被调用。

早期实际子会话 model_change 是另一层证据：A5-design L2 / A5-impl L2 为 factory26/kimi-k3；V5 L2 为 visual/deepseek-v4-flash-vision-exp；E5 L2 为 factory26/deepseek-v4-flash，均 high。后期 advisor 的实际失败却报告 gpt-5.5（见第5节），说明“配置模型”不能直接当“实际模型”。

**executor：**早期审计 `coverage.json` 的 transcript 索引及本次定向读取的 M5/M6b 原始链没有发现原生 executor 调用；实际写代码的是被分配 PR 的 Braid 成员。不得把 Braid PR implementer 称为原生 executor，也不能据此断言全运行从未使用 executor、或 executor 失效。没有效果证据，就不提出“多用 executor 必然改善”。

## 2. 需求→视觉观察→设计：Vision 有用但不是功能验收

M5 需求包括 Issue 列表、创建、元数据与状态交互。**I8-start L40 `57f688a1` 06:55:32** 将四个明确图片路径、列表排布/选择器/详情问题交给 vision，要求“区分图中可见事实与推断”。第四张 `github-issue-detail.png` 是未核实路径，还让仅有 read 的 vision 用 ls 找替代，输入与工具能力不完全匹配。

**V5 L29 `33142fc6` 06:56:26** 返回可归因结果：三张真实存在图片已读；详情图 ENOENT，目录 read 为 EISDIR、无 ls；列表参考是 No results 空态，“没有任何 issue 行”；选择器未展开。明确报告缺失证据，而没有假造行布局。它也提供可见侧栏、按钮、表单位置；截图中文案 Create 与需求指定 Submit new issue 不一致，不能覆盖需求。

**I8-next L7 `58a9d136` 06:58:32** 明确消费：“list rows layout not verifiable…issue detail page has no image reference…design follows requirement text”。随后 Issue #8 的设计按文本确定数据态/交互。可确认效果是约束了事实边界、避免把空态当数据态证据。没有本链证据证明主 Agent 做过实际页面与参考图的独立视觉终验，故不能将 vision 调用算作视觉符合性验收。

最小改进是委派前由有 ls 的主 Agent 提供实际文件清单，vision 对指定文件解释，返回已知/未知；不是无限扩大 vision 权限或多发图。收益限于少走不存在路径和更清楚的观察边界，不能预测评分增长。

## 3. 需求→设计→实现负向断言→Advisor共享化：确实纠正了权限选择

### 先形成局部设计，Advisor并未一开始做全面需求审计

**I8-next L4 `0ed5597d` 06:56:44** 的 advisor brief 同时写“权限非隐式阶梯”和“元数据/关闭 Triage+”，具体问题是 New issue 对低权限的可见性、空白评论允许两种交互、Issue/PR 编号是否共用。**A5-design L23 `0e5f87f4` 06:59:30** 独立核对文档后逐题给建议，并要求登记前检索是否有 New issue 隐藏条款。

**I8-next L10 `6e97075b` 06:59:39 → L11 `2d37ddd3` → L12 `24676441` 07:01:35** 先实际检索权威需求，再采纳“低权限仍见入口，服务端拒绝显示原因”、启用空白评论按钮、各表编号，发布 #89 并交 PR #15。这个 advisor 有真实决策影响；但没有复核整套权限表示。不能说它审过一切而完全无效，也不能把“含 advisor 复核”的 #89 当全量批准证明。

### 首次纠错来自应用验证，Advisor随后加强共享边界

PR implementer 消费 #89 和架构 `triage+` 后实现。**P15-start L126 `72e82f11` 07:06:46** 原始历史测试明确：bob(write) POST close 得200，期望403（4 failed /21 passed）。**L127 `6b7ca587` 07:07:03** 推理：“roleAtLeast('write','triage') = true…requirement text is authoritative”，并区分“可被指派 ≥Triage”与“执行指派的角色集合”；L128/L130 工具结果确认写入修正，L132 `4b2dd386` 07:07:18 为25通过。

因此最早可见机制是**按需求写的反向断言推翻实现**，不是 advisor 首先发现权限问题。**P15-start L213 `79b083f0` 07:13:14** 才把已发现冲突、原文、当前实现、可替代解释和共享化问题交给独立 advisor，说明其目的为“before I formalize it as a shared premise”。

**A5-impl L5 `817c176c` 07:13:32** 证实子 Agent 收到上述 fresh brief；**L21 `c7fe7e4a` 07:17:26** 回读 REQ-6-6 等后说明 PR close 与 Issue close 是不同集合，建议显式集合移入共享 permissions、纠正架构速记、Write 五端点拒绝与 Triage 正向对照。

**P15-next L65 `1e5a40f5` 07:17:42** 逐条采纳，明确移动到 shared permissions；L77 `a0ef73f6` 07:18:03 设计 Write五端点403/Triage正向验证；L105 `0cc209e7` 07:20:10 草拟根契约修正，L151 `ba5116e7` 07:23:58 发起 #112。后续 **L247 `80860ecf` 07:33:51** 读到 #89 已由owner更正、#112由根负责架构。既有 M4/M5 审计和最终 workspace 仍有 explicit set，对应实现与共享文档消费链成立。

**直接证据结论：**原生 advisor 的增量价值是解释验证、跨模块区别、共享实现与验证建议；“加一条先问 advisor”不足，因为这条要求本来存在且确实执行。应改的是每次审查的覆盖边界：结果须说明已回答的问题/未覆盖内容，不能把局部问题答复升级为整个设计已审。

## 4. 实现→需求审计→修正：Explorer改变了行为，但本身有边界

**P15-next L212 `ac4fa168` 07:27:53** 在平台安装等待期间主动委派只读 explorer：提供 REQ-5 各ID、权威原文路径、实现/测试文件、已接受#89，并要求 description 和 WHEN/THEN 逐步判别、关注刷新持久化与accessible names；没有只让它复述自有测试通过。

**E5 L80 `8e2925ee` 07:33:43** 给出真正行为反例：输入关键词后200ms才写URL，若立即刷新丢q；现有e2e先等待URL变化会掩盖窗口。另列断言缺口和编号/默认状态歧义，并区分“实现正确但未断言”。它没有运行测试，结论是静态需求审计，不是另一次独立行为通过证据。

**P15-next L247** 发现手头tail从中间开始，主动重新读完整输出；**L250 `338df551` 07:34:19** 明确“real behavioral risk”，采用URL立即replace、仅请求防抖。**L256 `5ed9f844` 07:34:28** 实际edit IssueListPage；随后补断言、对编号/默认两态另作设计取舍。原审计的 #120/#121 与 `bab2b11` 交接记录支持结果进入候选，不仅留在摘要。

**作用与限制：**同一个实现者没有把全绿当终点，这个 explorer 有有效纠错。它的输出同时把许多“仅浏览器层未断言、实现已有/API已有”的项目列“必须修”，优先级混入覆盖声明与真实行为缺陷；主 Agent有再次分类。审计brief围绕 M5 文件和已接受#89，所以不能自动获得全应用端到端范围的独立性。REQ-5-3-3虽在输入ID内，本次输出未追踪PR端消费；这只能证明此审查范围未产出该跨模块责任问题，不能从最终遗漏推断它的隐藏心理。

## 5. 后期设计→Advisor故障→Explorer替代→主Agent复核：独立判断并未停止

M6b Issue #10 当时范围是行内评论、评审、请求reviewer、合并、关闭重开。**I10-start L53 `2226934f` 16:10:21、L59 `61dd8ea1` 16:10:31** 先从原文与M6a实现辨认作者是否可评论、compare commit权威、seed初态/断言等待决点；**L75 `fe5a9900` 16:11:54** 带具体候选和原文咨询advisor。

**I10-next L6 `38a1d89f` 16:12:03** 报实际advisor失败：gpt-5.5，HTTP401 invalid_api_key。**L9 `69b94572` 16:12:21** 显式指定factory26/kimi-k3重试，**L17 `e91ca6b8` 16:12:35** 仍报告gpt-5.5/401。**L22/L24** 回读配置看到kimi-k3；**L28 `a13b7086` 16:13:24** 读取model-exclusions，kimi-k3已有429记录（credit balance low，非此刻新请求回包）。

所以只能确证：配置/请求模型与实际失败模型不一致，已有不可用模型排除信息；不能仅凭主Agent推测断言哪段fallback代码错误，也不能写成本次kimi直接限流两次。原始错误含脱敏凭据片段，本报告不复印任何凭据或账号标识。

**L31 `93989e6a` 16:13:40** 改用 fresh只读explorer，并提供真实需求、当前契约、实现入口及D1–D6候选，要求反例/缺失事实。**L92 `3cc81675` 16:18:09** 成功状态确认deepseek-v4-flash；**L93 `35768ae1` 同时** 是原始custom_message `subagent-notify`，正文保留完整输出。这里即使未提取其子会话，输入、结果、消费均在父原始会话可核对。

输出给出old/new行号同号的具体反例，支持side字段；发现protection-lab没有合适非作者Write评审者和必要seed，提示预置check会冲突既有全库计数。**L94 `e86b182c` 16:18:15** 主Agent逐项消费；**L98 `5ef8c3ca` 16:18:55** 又实际核对断言并重新权衡原文明确seed要求，没有盲从explorer用运行时setup替代全部seed。它选择新增merge-lab + 窄改全库计数，向根提出裁决；**L142 `ad9592f3` 16:20:01** 交接#308/#309/#310与PR#22，明确记录替代审查和A/B/C待裁决。

**直接证据结论：**advisor工具路径有可诊断故障，但本链通过另一新上下文角色恢复了独立判断；“advisor不可用”不能等同“没有审查”。模型独立性弱于原来的不同模型advisor，但主Agent实际补证据与有理由不采纳建议可见，不能从同模型直接判无效。

**同一正向链的范围边界：**I10-start L65/L68已把PR里程碑认定不在M6b范围，之后explorer brief只包含REQ-6，原始REQ-5-3-3跨PR约束未作为“排除后需找承接者”的问题。这里能观察到输入约束了替代审查范围；不能要求一个被明确限定REQ-6的explorer自动负责全项目漏项。是否由根登记并重新分配，属于Braid跨Issue责任闭环，应与本报告的子Agent有效性分开核对。

## 6. 可以改什么，不能据此许诺什么

| 候选 | 层次/具体位置 | 证据与机制 | 风险与零额度核对 |
|---|---|---|---|
| 审查输入带“原需求范围、拟排除项及承接依据”，输出明确已审/未审，主调用方记录采纳/拒绝理由 | 原生advisor/explorer委派指引与I11成员instructions；SVC方法应沿现有来源维护，避免两套正文 | M5早期只审三题却被#89标“含advisor复核”；M6b排除在brief外；M5后期反例式输入实际有效 | 不能变成每次全量审计或复制全部需求；仅跨对象、角色、生命周期边界。用已存brief/输出人工重建范围表，确认上述两例能显露缺口；不跑模型 |
| 保留按原文形成的可区分反例，再请advisor解释共享影响 | 验收Skill/成员验收指引 | 真正先抓Write错误的是403负向断言；advisor随后共享化；explorer刷新时序反例改了行为 | 单纯多测试/多advisor不等价。静态逐条将历史断言对回需求，而不是重跑Factory/Braid测试 |
| 记录requested/configured/effective model及原始失败，提供已授权的角色替代路径 | subagent运行机制和错误呈现；不是只改自然语言 | M6b两次配置kimi但实际gpt401，依赖读exclusions才解释；替代explorer确有产出 | 本报告未定位选择器源码，不能直接断言bug所在或推荐自动无限fallback。零额度先只读比对现成事件/role配置/exclusions；不发模型请求 |

优先前两项；第三项先确认实际fallback契约。Vision输入清单是低成本局部整理；executor暂无足够证据支持新增并行或扩大角色。所有候选只支持“减少已见过程盲区”的判断，不能预测4分能提升多少。最终官方无逐用例失败明细，无法把96项失败分摊给这些机制。
