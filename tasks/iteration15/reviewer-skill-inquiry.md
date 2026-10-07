# Reviewer 技能读取定向抽样

观察时间：2026-10-07T14:14:51.708714+08:00。本次只读四个指定专门reviewer的原生记录，不运行模型、控制运行、修改提示词或业务代码。样本来自原Stage3 `20261006-155638-60f0ce5d` 的reviewer-1/2和pre403应用接续 `20261007-042557-61978851` 的reviewer-1/2，不用于估计所有reviewer的采用率。

用户所说的技能发现/加载性能，指触发、内容摄取和方法采用的可靠性，而非文件读取速度。85毫秒和2毫秒对此没有判别力：它们只能排除这两次调用的具体文件I/O失败，不能回答技能是否可靠触发、正文是否进入有效判断、方法是否落实。原两位成功读取，接续两位没有尝试，是同类非简单验收任务中触发不稳定的迹象。它们仍读取其它技能并开展独立验收，所以不能把未读直接当作验收完全失效；具体遗漏机制及缩短指令后的收益仍未验证。

| 运行 / 成员 | 原生session ID | svc-verification读取 | 其它成功技能读取 |
| --- | --- | --- | --- |
| original / reviewer-1 | 01a1127c-9ab3-71e0-b32c-e471c7730484 | 成功；4102字符；0.085秒 | braid-collaboration, arc-bench, e2e |
| original / reviewer-2 | 01a1143d-8b6f-7433-af5f-dc9e30565cc4 | 成功；4102字符；0.002秒 | braid-collaboration, arc-bench, e2e |
| continuation / reviewer-1 | 01a114ae-3ded-709b-b2bf-4312ef216b6b | 没有读取调用；无读取错误可归因 | braid-collaboration, arc-bench, e2e |
| continuation / reviewer-2 | 01a114b6-1767-7693-9428-3edcc2bac5f3 | 没有读取调用；无读取错误可归因 | braid-collaboration, arc-bench, e2e, agent-browser |

父任务静态核对当前共同MAIN_SKILLS实际16项；启动先`--no-skills`再显式`--skill`，Pi0.85.1保留CLI指定技能，不能把`--no-skills`解释成禁用全部。发现入口只提供name/description/path，正文按需read。上述是静态接线事实，并非四份原生session保存了完整system发现列表。四份session中的具体读取路径和成功内容已直接证明相应技能可用；没有尝试的两份不能单独证明svc-verification当次出现在system列表。本次没有专门回收Pi资源加载warning通道，不能声称loader warning为零。

原Stage3 reviewer-1在原生行22、2026-10-06T18:32:35.867Z读取svc-verification（以samples.json实际timestamp为准），随后行25/31分别提出静态差异、现有检查、真实浏览器验收与候选记录计划，行141还核对e2e用例是否使用需求的精确locator。原Stage3 reviewer-2行58明确把非简单验收与阅读verification联系起来，行61/65记录验收计划与合并事务、权限、seed及可访问名称判据；行95独立对照REQ-6-6发现命名账号pr-viewer缺失，而不是把已有issue-viewer测试通过视为充分覆盖。这些是方法使用迹象，但计划与指令本来就要求同类行为，不能据此证明技能阅读是唯一原因或整体验收可靠。

接续reviewer-1行16在读取verification之前（本样本随后亦无此read）已明确计划：读原requirements、静态审阅、Vitest/e2e子集、真实浏览器；行21/23直接读input/requirements.yaml。reviewer-2行18/20直接读原requirements，行22计划合并、权限、编号、stale、seed与可访问名称等检查，之后加载e2e与agent-browser。此前保存的`manual-stage3-pre403-2a951d4/reviewer-activity-20261007T1333+0800.json`又记录两位实际API权限/状态核查与浏览器导航脚本排障。存在验收活动不等于采用svc-verification；相反，没读取该技能也不等于没有验收。

具体错误属于模型供应商路径：原reviewer-1保存两次403 `AccessDenied.Unpurchased`；接续样本保存504 `upstream_headers_timeout`。没有SKILL读取调用对应这些错误，不能把它们归因于技能加载。这里列出的读取墙钟只测本地工具返回，不能代表技能发现注入、模型消化4.1KB正文或整个验收耗时，也未建立提示长度对model latency的对照。

按父任务查阅的mattpocock/skills `writing-for-agents/SKILL.md` 与 `SKILL-MECHANICS`，应先检查上下文指针的措辞和信息层级，而不是以read次数衡量效果：必需方法藏在触发不明确的指针之后，会引入执行差异；所有验收分支都需要的原则应在入口明确，细节再按需读取。这里的同类任务读取差异与这一可靠性风险一致，但不是单独证明某一句指针造成遗漏的实验。

可采用的方向是把reviewer入口组织成一个明确动作链：“在制定或解释任何非简单验收前，读取svc-verification；从原始requirements建立每项预期行为对应的可观察判据（observable oracle），记录实际输入、期望结果、观测结果、证据及未覆盖边界；既有测试通过不能替代该映射。”保留原始需求权威、固定候选、独立状态与结论证据这些所有分支必需的约束；方法细节保留在独立技能，不内联正文。效果应以验收过程和判据产出是否可预测衡量，不能以技能是否被read一次替代。

16项共同技能目录造成候选指针竞争、svc-verification泛化description难以优先匹配具体审阅时刻、以及特别instruction重复方法提醒可能使模型认为已经取得足够指引，都是可解释当前差异的候选机制。四份rollout没有直接对照证明这些机制各自的因果权重。可以收窄reviewer的职责技能列表并合并重复提示，但应先锐化必要技能的触发及产出要求，不能据未读就断言删除skill有益。此次只更新解释和建议，未修改源码或新增实验。

原始定向证据保存于`runs/iteration15/reviewer-skill-inquiry/samples.json`（读取调用/返回/错误）、`method-excerpts.json`（原reviewer计划及判据）、`continuation-behavior.json`（接续初始计划）。每条含远端原session绝对路径、原始行号、UTC时间。没有复制完整rollout到主报告。
