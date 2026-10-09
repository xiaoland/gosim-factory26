# Braid Factory 正式比赛基线

当前阶段：入口修正版官方 API Lite 已完成并汇报，Keep 23/32、BookStack 26/34，合计 49/66；本 packet 保存该轮及此前 54/66 的证据。
后继正式 Hackathon 实验已转入 [Issue 拆分实验](../issue-decomposition/packet.md)；当前状态由其 packet 与官网原始记录维护。
授权原话：“可以”，对应上一轮呈现的冻结 ZIP、两题两并发、官方 API 与完整评分后报告的范围。
用户本轮要求提交上一轮子代理改造，并将新基线作为独立 task：先在 WSL 使用官方 LLM API 完整运行 Lite，通过实际结果确认 Harness 可用和表现，再在官网运行正式 Hackathon，记录评分、多模型和联网能力。
子代理改造提交为 `b15570f`；其余 Braid 边界等既有工作区改动仍须随实际制品冻结，不能声称该 commit 独自复现本轮。

## 实验对象与顺序

用户已确认唯一实验对象为 `pi-team-mixed`，含 Braid + SVC、GLM 根成员、DeepSeek 成员及各自原生子代理。
用户认可 Lite → Hackathon 顺序和补充后的设计，并确认官网使用 official_evaluation。
本轮直接授权用户级 AGENTS.md 的搭档职责更新与提交脚本两模式支持；已按这个范围实施。
核实分成两条：正式比赛的实际条件，以及当前 variant 的迭代假设。Lite 分数过低即为暂缓正式题的警讯，诊断重点包含反馈循环是否真正闭合。
其他 variants 已按授权标记归档／停用，历史实现与结果保持原路径。
另一会话的 `codex-base/codex-svc/pi-base/pi-svc` 不含 Braid，不自动作为本次实验对象。
同一套冻结 Harness 先运行 Lite 的 Keep、BookStack，再用于官网 Hackathon 的 GitHub、Sheet。
本地两题可并行；官网以其实际并发能力和正式任务顺序执行，不使用 Playground 或产物回放替代生成基线。
完整 Lite 结果先报告；“表现尚可”包含性能下限预检查；不自行发明硬门槛，也不因设施正常就忽略低分。

[实验设计](design.md)记录要解决的具体判断、凭据差异和结果如何改变下一步。
[执行计划](plan.md)保存原生资源、输入、模型、证据和待确认条件。
[准备记录](preparation.md)保存本轮实际平台与 WSL 观测。

## 完成判据

Lite 两题均有完整官方评分，生成/部署故障与有效低分分别呈现。
官网两题使用同一冻结 Harness 真实生成并评分；没有公开测试不能用本地生成完成替代官网得分。
多模型及联网结论来自实际请求和返回证据，区分宿主、WSL 容器、官网容器；未使用的能力记为未观察。
每个完成的 run 由独立分析 Agent 分析原生过程，主 Agent 综合；不以阅读 Harness 源码代替验收。
不新增 Factory/设施/Corpus 测试，不调整模型配方或 SVC 来改善本轮分数。

## 本轮实施与待验收

用户级 `~/.codex/AGENTS.md` 已加入 Collaborative Judgment，保持个人指南在用户范围，不复制进本项目或 Factory 材料。
competition.prepare 的凭据模式进入冻结身份，snapshot 显式提交该字段；official_evaluation 不读取或上传个人模型 key，self_funded 保留原路径。
旧 journal 缺字段按历史 self_funded 解释，模式变化要求新状态目录；摘要区分请求模式与运行返回的 billing_mode。
本轮未提交新改动、未运行 Factory 测试；competition.py 语法编译通过，平台实际效果仍待真实提交确认。
独占 WSL 构建及打包已完成，Lite 两题清单已就绪，恢复点见 plan.md；未调用模型或官网写接口。

## 最新结果

本轮 Keep run 为 `pi-team-mixed-arc-bench-lite-keep-54196efa62`，BookStack 为 `pi-team-mixed-arc-bench-lite-bookstack-ba27587982`。
两题均 completed，全部 66 个用例已执行，score 字段均为 null；以上百分比为测试通过率。
证据位于 WSL `runs/hackathon-team-baseline/20260925/lite-runs/`。
逐题分析分别委派给独立 gpt-6-sol/high Agent，报告写入 results/keep.md 与 results/bookstack.md；尚未开展官网实验。

## 监控交接与过程验收

本次监控遗漏的触发是新 Agent 创建返回 `agent thread limit reached`；其上限是否偶发尚无证据。
直接原因是先 interrupt 原监控，再创建接替者；创建失败后既未恢复监控，也未检查当时实验终态便结束回复。
这是交接顺序缺口，不是实验控制器故障或三分钟采样间隔问题。
只在当时的监控说明（现已删除）补充先确认接管再结束原职责的顺序，不增加 watcher、轮询、测试或新平台。

用户要求逐 run 分析覆盖此前改进的实际体现。
两个分析 Agent 已分别收到 SVC skill/导航/task packet/V&V/shift-left、Braid 指派/身份简化/评论与上下文协作、子 Agent fresh/SOP/工具/模型的观察任务。
报告区分配置存在、轨迹实际生效和局部产出被采用；未观察到的角色/工具不算失败，跨版本分差不单独证明因果。

## 过程分析结论

独立分析已完成：[Keep](results/keep.md)、[BookStack](results/bookstack.md)。
两题都有真实浏览器反馈、修正与自检通过，不能将冻结后的隐藏评分未回流视为反馈循环失败。
Keep 五项失败集中在需求允许结构与评分 locator 的差异；BookStack 六项有 helper 角色选择竞态的证据，一项为草稿入口差异。
这些证据不能把失败项自动补记通过，也不支持将分差归因于本轮改造。

Braid 免传内部身份参数的操作已观察到；Keep 有主动创建并指派 PR，但主要实现已经完成，BookStack 没有 PR。
BookStack 实际 resolve 评论并重建上下文，Keep 评论传入 PR；尚无这些上下文操作带来协作收益的完整证据。
SVC 入口及 task-packet 导航在 Keep 被读取，BookStack 未观察到读取；两题均未形成 packet，未证实 V&V 正文采用。
两题都只有 GLM 客户端模型记录，没有 Pi 内部子 Agent、DeepSeek 或 MCP 查询。
因此 fresh/SOP/子成果采用、多模型和工具运行能力仍未验收，不能用现有通过率关闭 factory-subagents 或 SVC 的行为验收。
冻结包内角色材料存在不证明运行时工具完整暴露；当前原生归档不记录全部未调用工具清单，这是区分未暴露与未选用的具体证据缺口。
这一区别已继续追查，结论与具体证据边界见 [主 Agent 综合分析](analysis.md)：消费者链成立，尚未定位到接线缺陷；BookStack 有明确考虑委派/SVC 后选择直接实施的轨迹。当前更明确的问题是根 Issue 未维持设计/实施职责，而非子角色内容已证实无效。

## 用户复核后的方案修正

[工作项入口、协作层次与 SVC 导航](workflow-design.md)及其实施准备已获批准，正在实现。
明确区分 Braid 工作项负责人和 Pi/Codex 原生 sub-agent；修正“定义明确可抵消规模成本”的不充分判断。
入口目标是简短工作项请求、GitHub 式操作与协作说明、可编辑对象上下文各司其职，并审查同类消息路径；不把设计/实现阶段映射或会话隔离的内部解释作为使用者的入门指令。
Factory 只是参赛 Agent 的称呼；原生 sub-agent 的介绍归 Codex/Pi 及其扩展，不新增“Factory 能力指引”层。
用户认可 SVC description 的修改方向；SVC 短导航和 description 从实际问题介绍用途，内部方法名称留在 skill 中。
用户开工授权原话：“确认，开始。验收就是重新跑lite（但是用我另外提供的kimi,deepseek,glm的key，而不是官方的llm api）。”
用户进一步要求基于使用者视角排查并修正同类问题；已完成对稳定指令、三处上下文包装、通知、CLI 帮助/错误、原生工具介绍及技能入口的定向调查。
具体结果与实施准备见 [入口审查](interface-audit.md)，不扩展为运行时架构或 Corpus 正文重写。
独立 Agent 已完成接口预演，主 Agent 已吸收 shell 示例、指派前提及 ready 身份表达修正，并排除当前 CLI 不可达的旧改派限制；已进入实现与完整 Lite 验收。


## 自购 API 的入口修正验收

执行记录见 [本轮 Lite](interface-lite.md)。实现由主 Agent 负责成员/SVC/工具入口与实验接入，独立 Agent 负责 Braid 源码及其技术文档。
Lite 使用 WSL 官方 Runner，Keep、BookStack 两题并发，完整评分后报告；不启动官网或其它 variant。


## 入口修正版官方 API Lite

用户在确认官方 Meter 可用余额为 ¥277.228206 后明确要求：“那么我们用官方API去运行lite吧”。
复用 20260925-interface/pi-team-mixed.zip，WSL 官方 Runner 对 Lite Keep 和 BookStack 并行两 worker，生成与评分分离。
本次记录在 WSL runs/hackathon-team-baseline/20260925-interface-official-api；私有环境沿用前次成功跑分的 20260925/official-api.env，不使用自购网关。
控制器 PID 20873；两条 run be4dde8d43 与 743b6187f7 已进入 running。完整两题结束后报告分数及可观察到的行为。

运行继续由本地程序持有，不因聊天结束而中断；线程 heartbeat `factory26-api-lite` 每 15 分钟只读检查终态，完成后汇报并停用。旧的自购 API 监控 Agent 与曾尝试接管的新 Agent 已中断，避免重复观察。

完整官方 API Lite 已结束：Keep 23/32（71.9%，run be4dde8d43），BookStack 26/34（76.5%，run 743b6187f7），合计 49/66（74.2%）；旧 ZIP 54/66（81.8%）。两题生成 exit 0、评分完成，冻结源码与评分源码哈希各自相同。
本轮与旧轮 Runner、adapter、requirements、tests、noop 输入哈希分别相同，Agent ZIP 不同；同一官方 API 环境文件，但随机生成不能单次归因。Keep 耗时 36.4 分钟（旧 61.4），BookStack 99.2 分钟（旧 110.7）。
原始 run 证据在 WSL runs/hackathon-team-baseline/20260925-interface-official-api/lite-runs。两题原始 Braid 对象均只有根 Issue，Keep 无评论，BookStack 有一条评论，均无 PR、子 Issue、merge；实际协作收益待与原生轨迹交叉核对。两名独立 Agent 各分析一题的失败项与行为证据。heartbeat `factory26-api-lite` 已暂停，避免终态后继续轮询。

逐项差分与运行行为结论见 [入口修正版官方 API Lite 结果](results/interface-official-lite.md)。本轮实验完成，按约定先向用户汇报，由用户决定下一轮，不启动正式比赛。

用户提出下一轮在根 Issue description 明确要求拆分需求；新一轮方案与复核状态转入 [Issue 拆分实验](../issue-decomposition/packet.md)。上一轮运行与评分保持原始记录。
