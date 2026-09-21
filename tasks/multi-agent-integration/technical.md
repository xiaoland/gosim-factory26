# Multi-agent 接入技术方案

状态：主体技术方案已认可；本轮按用户纠正修订配置归属、浏览器委派和 SVC 范围。variant/preset 仅属于 Factory，Braid 不认识这两个概念。SVC 仅 V&V 纳入本轮，其余 Corpus 冻结。以下仍是方案，不表示已实现。验收见 [verification.md](verification.md)，运行原理证据见 [profiles.md](profiles.md)、[Codex 调查](research-codex.md)、[Pi 调查](research-pi.md)。沿用现有 Braid、原生核心、SVC 和评测入口。

## 配置按语义归属组合

一个 variant 对应一个 preset；preset 是 Factory 选择的一组 agent profiles。Braid 仅有普通 profile 注册、查询、指派和执行能力，不读取 Factory 的 variant/preset 文件，不接收其 ID 或整组摘要，不负责选择、展开、冻结或比较 preset。

```text
variants/<variant>/preset.json     # profile 引用集合、本组默认指派
harness/
├─ profiles/<profile>.json         # 一种 Braid Agent 的核心/模型/能力选择
├─ subagents/<role>.json           # 原生子角色的配置与工作合同引用
├─ instructions/                  # 共同与专长指引正文
├─ skills/                        # 选定的技能正文/必要依赖
├─ models.json                    # 比赛 provider、模型能力和参数映射
└─ dependencies.lock.json          # 工具、扩展、技能的来源及固定版本
experiments/<batch>.json           # variant × task、runner、主机、并行条件
runs/<run>/effective-config.json   # Factory 生成的完整展开证据，不手工维护
```

这是实施目标结构，当前不创建空目录。独立文件对应独立配置责任，不按每个字段拆文件。preset 仅选择 profile，不嵌入角色正文、模型元数据、技能安装细节或实验参数。profile 引用子角色与材料，Factory 一次校验显式引用、展开并归档；没有 extends、多级继承、隐式覆盖或深度 merge。共用文件只有一处权威，有实质差异的 profile 使用不同定义。

```text
Factory：variant → preset → 选定 profiles + 材料 → 原生运行绑定
                                      ↓ 普通 profiles / bindings / 明确指派
Braid：profile registry → work-item assignment → 原生 session tree
                                      ↓ work-item/profile/session 证据
Factory：附加 variant/task 关联 → 分析、冻结应用、外部评测与批次比较
```

Braid 请求里的 profile 列表是本次可用普通配置，绝不是一个 preset 对象；不以数量为一或多改变语义。默认指派使用普通 profile ID，root Issue 的指派由 Factory 启动时明确指定。Braid 的 CLI、对象、数据库和日志均不需要 preset/variant 字段。

| 配置责任 | 唯一权威与消费者 |
| --- | --- |
| variant/preset 的组合选择 | Factory 的 preset 文件引用 profiles；Factory 解析成 Braid 可用的普通 profile IDs 和启动默认值。 |
| 单个 Braid profile | core/provider/model/reasoning、指令与 skills/CLI/extensions/native_subagents/MCP 引用。Factory 装配能力；Braid 只按该 profile 及运行绑定执行。 |
| 原生子角色 | 独立 role 定义拥有模型/推理、技能、工具和窄工作合同；不是 Braid profiles，也没有独立 Braid assignment。 |
| 服务能力与安装来源 | models.json 和依赖锁定记录。参数映射与精确来源共享，不混入 variant 选择。当前 MCP 为空，不构建无消费者的 MCP 管理器。 |
| 题目和执行条件 | batch manifest 拥有任务、输入/runner版本、主机和容量，不放入 Agent profile。 |
| HOME、端口、会话与密钥 | 运行时绑定；密钥只由环境注入，证据只保存引用名称。 |

Factory 冻结本次组合及全部展开材料，并拒绝用变化后的组合恢复同一次实验。Braid 仅检查单 profile 的有效修订及对应会话兼容性：其摘要包含该 profile 实际消费的模型、指令、能力材料和核心版本，不包含其他 profiles 或整组 preset 摘要。因此改变一个未被该会话使用的 profile，不会因为“整组变了”使它的 Braid 上下文失效。临时目录/端口不进入语义摘要。历史 run 仍按原归档读取。

## Braid 的直接指派与恢复

CLI 增加 `braid profile list/view`；创建 Issue/PR 使用 `--assignee PROFILE_ID`。修改指派使用 `issue/pr edit ID --assignee PROFILE_ID`：这是本地单一执行 profile 的替换操作，不模拟 GitHub 多个人类 assignee；同 ID 为无操作。list/view 的默认简报和 JSON 都显示当前 profile。未知 ID 在数据库写入前报错。根 Issue 使用 Factory 显式传入的 profile ID；新工作项未指定时使用该 Braid 实例的普通默认指派配置，不从标题、label 或模型判断专长。

默认映射：通才两组的 Issue/PR 都为 generalist；两团队组默认 Issue 为 coordinator、PR 为 app-engineer。所有 profile 可承接两种对象；默认映射不规定协调者必须派发任务或 UI 必须单独拆成 Issue。

`local.rs` 接收 profiles 与默认值，注册每个 profile。沿现有 group worker 建立 kind × profile 的驱动实例，assignment candidate 和 claim 同时按工作项的显式 profile 筛选；SQL 事务再次校验指派，避免多个 worker 抢走或忽略另一 profile 的事件。健康汇总按实际实例集合计算，移除固定“两类 worker 就绪”的假设。kind 决定 Issue/PR 协议，profile 决定能力，两者正交。

工作项保存 desired profile 和指派修订；现有 assignment/agent/session 记录保存实际执行身份。重新指派是一项可恢复的运行转换：先撤销旧 writer、停止旧 session tree，确认不再写入后，再由新 profile 从当前 canonical context 启动。保留工作项、讨论、Git 分支、现有工作树与未提交文件，保留旧会话证据；新的 assignment generation/执行身份不复用旧 provider messages。再次指派时以最新 desired profile 为准，旧请求不能覆盖它。关闭项可修改期望 profile，但只在 reopen 后激活。

这与原 profile 下的 description/hide 引发的上下文重建不同：后者保留逻辑 Agent，仅替换物理上下文。实现复用已有 fencing、context reset 和恢复机制；不会用“关闭再创建 Issue”模拟指派。无法确认旧进程及其原生子树已停止时保留 blocked 证据，不在同一工作树启动竞争写者。Braid 按单 profile 修订检查恢复兼容性；整个实验配置的冻结与新 run 判定归 Factory。

## 原生装配与子代理

Factory 为每份 profile 生成只读配置模板，为每个 Braid 物理会话树建立隔离 HOME/native home。原生子代理由核心创建，其配置继承和进程树由核心/扩展处理；Factory 提供必要配置与证据收集。Braid 本地请求增加按 profile ID 索引的运行绑定，包含原生配置模板、可执行程序及能力摘要；它与 catalog 必须一一对应。SessionFactory 根据 profile ID 选择绑定，在既有 physical 会话目录中物化独立 home，开始与恢复统一走这个边界。PiConfig 只保留进程/认证/目录参数，模型与推理从 Profile 传给 spawn；不建立另一套子代理调度器。

Pi 使用固定版本 pi-subagents，显式加载选定扩展和 skills，保持个人扩展、主题与提示文件隔离。模型、thinking 使用 Profile 的实际值，provider 统一注册为比赛网关的描述，而不是把所有新模型冒充内置 DeepSeek。原生 role 定义由同一有效配置展开，包含工具和技能；网关 API key 只从运行环境读取。

Codex 固定当前 0.155.0，使用隔离 CODEX_HOME 下的原生 role TOML 和技能配置，通过 app-server 驱动；继续使用已有 LiteLLM Responses→Chat 转换器，保留核心默认 system prompt。Braid/profile 指引使用 developer instructions。原生父子关系来自 thread source 的 thread_spawn 元数据；不把宿主 Codex App 的可用角色当成实验核心已有配置。[本机 schema 与固定版本来源](research-codex.md)已核对，真实 K3 兼容性仍是预演/验收项。

原生子代理不是新的 Braid Agent，不独立获得 work-item assignment。其委派输入包含任务 delta、必要上下文入口、授权写入范围与返回合同；SVC 导航在隔离环境中真实可读。若代父使用 Braid writer，仍受父 dispatch 的有效性约束，不得把旧 writer 或 external 入口当成长期凭据。父会话重建、重新指派和 run 终止都必须覆盖在途子树的处理，不能仅停止父进程后遗漏继续写工作树的子代理。

原生核心的并发/深度行为记录为实验条件；不另加推测性的低 token/时长限制，也不以“等待子代理”为理由强制结束父 Agent。是否委派、怎样组织任务及何时验收由 LLM 判断。

## 浏览器委派与能力材料

重新读取 SVC sub-agents/index.md、explorer.md、executor.md 后，角色设计按工作边界与反馈闭环调整，而不是给每个工具造一个必须经过的角色。主会话保留需求、方案、协作与整体判断；连续页面操作、DOM/截图筛选和复现通常交给原生子代理，避免逐步工具输出占据主上下文。简单单步检查允许主会话直接完成，不由 harness 硬禁用浏览器。

| 原生角色 | 合适的委派边界 | 返回与反馈责任 |
| --- | --- | --- |
| explorer | 一个证据路径嘈杂的事实/约束问题，默认只读 | 给直接消费者返回问题所需结论、出处和未知，避免资料堆积。 |
| executor | 已授权的局部实现/修复，明确文件或效果边界、约束和反馈机制 | 自行完成实现→浏览器/API/测试反馈→局部修复，交付实际 patch/产物与验证入口；不把每步日志交给主会话中转。 |
| browser-operator | 一个明确页面旅程、复现或观察问题；默认可操作隔离应用数据，不改源码 | 接收 URL/启动入口、需求/现有判据、账号数据、状态与允许效果；返回相关观察、最短复现、证据路径和未知。判据缺失时报告探索发现，不擅自定义需求。 |
| reviewer（仅 pi-verification） | 一个已有证据尚不能回答的需求理解、设计或验收依据问题 | 返回有依据的偏差、反例或证据缺口；不重复执行已有确定性检查来提供“二次批准”，不因另一个 Agent 看过就宣称独立可靠。 |

默认将浏览器操作 skill 放在 browser-operator 和需要浏览器快反馈的 executor，主会话只有简短委派导航。已有 executor 能自己闭合浏览器反馈时，无需再套一层 operator。browser-operator 是原生工具操作专长，不是新 Braid profile；所有组都可用 K3/high 的该角色，实际图像兼容须验明。pi-verification 原 browser-reviewer 与 operator 合并：独立验收通过具体 assignment/证据来源表达，不再维护另一份几乎相同的工具角色。

role 委派遵循现有 SVC：明确问题或期望效果、范围/权限、必要上下文与 freshness、可用反馈、消费者/返回合同、局部恢复和实质升级条件。不给子代理完整主会话作为默认上下文，也不强制固定重试数或统一表单。主 Agent 保留语义判断和最终责任；运行时不能把 reviewer 标签当作自动批准条件。

仅 pi-verification 配置一个可选 reviewer（K3/high），删除 contract-reviewer 定义；其它三组不注册或注入专职审查角色，也不换名为 explorer 来强制复现同一审查流程。所有组仍共享 V&V，主 Agent 和 executor 仍负责选择、执行和解释必要检查。这里控制的是预置角色，不是禁止 LLM 检查自己的工作或按实际问题委派调查。

Contract 是要满足的语义约束，不对应一种固定验证工具：类型、schema 和可静态判定的规则交给静态检查；状态转移、持久化或跨组件行为按最低成本的有效边界用 property/integration/E2E 等取得证据。reviewer 只作为检查需求→性质→Oracle 转换和证据缺口的候选手段，例如检查现有断言是否把“显示已保存”误当成数据已持久化。发现可可靠自动判定的问题时，优先补充或修正可执行检查；reviewer 的意见不替代检查结果，不是必经阶段或批准门槛。主 Agent 可判断无需调用；价值是否成立须看新增发现及其证据，不能从角色存在推断。

浏览器候选为 agent-browser、dev-browser、Playwright CLI/脚本。当前建议四组先共享 agent-browser 作为固定工具条件；替代方案的主要差异和预演标准见 [skill-candidates.md](skill-candidates.md)。先验证选定工具能完成题目需要的富文本/弹窗/暂态反馈/多会话/截图和必要网络诊断；存在具体缺口时试替代工具，不在每个 Agent 中同时塞三套工具，也不自动把四组扩大为浏览器交叉矩阵。外部官方评测器继续使用其原版 Playwright。

每个物理主/子会话独立 browser session/state，wrapper 按 run + 原生 session ID 自动命名并清理。Codex 使用 CODEX_THREAD_ID，Pi 使用 PI_SESSION_ID，不能按 role/worktree 或全树共享 ID 命名。二进制可缓存复用，应用账号/数据和浏览器状态独立。API/脚本可以辅助诊断和建立非 UI 前置条件；判定 UI 交互时必须通过界面操作，不能以 eval 直接改应用状态冒充功能成立。

### 本批实际能力分配

high 均为目标且必须记录实际映射，MCP 均为空；下表是设计配方，真实效果仍待实验。所有主子会话保留固定 SVC 导航。

| Variant / Braid profile | 主模型 | 主会话 skills | 原生角色与技能差异 |
| --- | --- | --- | --- |
| 两个 generalist | K3 | 不叠加专项方法 skill；提供浏览器委派导航 | explorer/executor/browser-operator 均 K3；浏览器 skill 在 executor/operator。 |
| pi-team / coordinator | K3 | 浏览器委派导航 | explorer/operator K3；executor K2.7 Code + ponytail、浏览器。 |
| pi-team / ui-engineer | GLM 5.3 Flash | Impeccable | explorer/operator K3；executor GLM Flash + Impeccable、浏览器。 |
| pi-team / app-engineer | K2.7 Code | ponytail | explorer/operator K3；executor K2.7 Code + ponytail、浏览器。 |
| pi-verification / coordinator | K3 | 按需 diagnosing-bugs | explorer/operator/reviewer K3；executor K2.7 Code + frontend-design、diagnosing-bugs、浏览器。 |
| pi-verification / app-engineer | K2.7 Code | frontend-design、按需 diagnosing-bugs | 与本组 coordinator 同样的原生角色；reviewer 以共同 V&V 为入口。 |

前端技能服务于给定界面与交互复刻，不覆盖状态、数据、业务约束或整体通过率。profile/skill 是可能有用的配置假设，题目并未规定必须用它们。需求→能力→配置的具体依据见 [requirements-fit.md](requirements-fit.md)；该文属于开发分析，不能把题目答案或逐项固定测试配方写入通用 harness。

## SVC 冻结边界与 V&V

按用户最新明确：本轮允许 V&V 调整；SVC 的其它 Corpus 冻结。Design 总入口与 Implementation 等清理移交 [后续独立任务](../svc-corpus-review/packet.md)，不是本批前置，也不借 Factory 的大提示词复制一套替代方法论。

V&V 以 [用户方法原文](../verification-system.md) 为依据，改动归 methods/design/test.md 和 verification/ 的实际语义 owner：从产品意图导出行为性质和判据；区分 Oracle 与输入/状态选择；检查需求破坏应失败、等价实现不误失败；区分验收与诊断证据；以保留目标语义的最低成本观察边界建立快慢反馈，并允许有理由修订判据。删除重复/无助于判断的文字，不新增强制模板、角色批准链或每需求永久测试的规则。

这份 V&V 在批次前完成并固定，四组使用同一快照；冻结其余 Corpus 的来源与 hashes，确认实际安装/消费一致。对旧实验比较必须注明 V&V 版本变化，不能把差异归因于新 profile。范围之外发现的方法问题写入后续 packet，不边跑八项边修改共同基础。

外部 skill 适配保留：Impeccable 只接本次需要的界面判断内容；frontend-design 尊重给定需求/参考图；ponytail 不削减明确要求；diagnosing-bugs 保留针对症状和区分假设的反馈，移除固定假设数等冲突。来源、版本和适配差异均归档。

## 诊断与批次

复用 native/manifest.json，加上 profile_id、effective_profile_digest、parent_native_session_id、native_role、身份来源及缺失说明。Braid 主会话与原生子会话分层表示；单独标识重建前后关系。子会话文件按明确身份归档，不靠修改时间猜测。逐会话调用现有 SVC 分析，摘要聚合 usage 时按原生唯一身份去重；不能确认是否包含子调用时分别报告，不盲加总。

brief 默认显示 variant/task、当前或失败阶段、实际模型集合、会话/子会话数、证据完整性及最相关入口；show 可按 profile/session/case 下钻。配置声明、实际加载、观察到的使用是三种事实；没有观测不算没有发生。分析失败不抹掉真实 benchmark 分数，benchmark 失败与生成/启动/设施失败分开。

批次由一份固定 manifest 描述四个 variant × 两个 task、输入/runner/配置摘要、执行主机和 run ID。为现有阶段函数增加薄的批次调度，不新建工作流框架。生成和评测各有独立容量；最多两项生成、四项独立单-worker评测，analysis 不占生成容量。原生/Braid 内部请求会叠加，记录 API 限流和资源错误；先不声称外层两项等于 API 两并发。

批次运行在 WSL，提前一次完成 bootstrap 与缓存准备。不同应用的依赖目录分开，工具和 runner 固定共享；不在每个 job 内重复安装评测器/Chromium。生成只读取需求素材，完成后冻结，外部评测结果不反馈到同次生成。

恢复批次只重连已知在途任务或继续尚未启动的任务；已终态的失败不重跑。不确定进程是否仍活着时标 unknown，不重复生成。阶段进程退出触发状态聚合；主 Agent 不定时 polling。系统性配置/隔离/协议错误停止排队任务并保留在途证据，普通应用低分继续预定清单。完整结果给逐题分数、总 passed/66 与逐题宏平均；缺题不输出完整分数。

## 实施范围和仍需预演的接缝

Braid 改 config/local/objects、相关 store 迁移与 group/provider 消费者；Factory 改配置/装配、原生证据收集、brief/show 与批次入口；SVC 仅上述 V&V 范围；四配方及冻结材料归 variants/harness。既有检查沿实际行为边界扩展。历史 run 不改写，当前默认入口应明确解析为所选新配方，不保留同名配置却仍运行旧单模型的隐式路径。

后续实施责任与局部计划归 [task-map.md](task-map.md)中的三个 ready Cell。独立预演重点是：重新指派和重建时原生子树收尾；Pi 扩展的隔离配置/异步子会话证据；Codex 自定义网关模型的原生子代理；浏览器主子隔离；三个网关模型实际能力与 WSL 可用环境。接口不符先做有界修正；改变产品语义、模型或验收范围时才回到复核。安装、模型调用和实际源码实施均未在本次设计调查中开始。
