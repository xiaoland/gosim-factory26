# SVC 方法与原生委派的运行接缝审查

本页从已发生的委派反查当前材料接线，不通读或重写全部 Corpus。依据为 [使用视图](usage-map.md)、[官网 GitHub](hosted-github-usage.md)、[官网 Sheet](hosted-sheet-usage.md)、[原生连续性](native-continuity.md)，以及当前 `variants/pi-braid/agents/pi-glm-fast/` 和 `run.py::native_files`。只读调查后写本报告；没有改源码、Corpus、运行，没有模型实验或测试。以下可验证预期留给获授权的真实运行观察，不是要求新增设施测试。

## 实际组合方式

必须分开“已安装”“提示里可发现”“正文直接进入上下文”“本次确实读取/采用”。当前源码能证明前三者的接线，历史子 transcript 的 system prompt 被 redacted，不能由当前配方倒推每次历史调用都采用了当前正文。

父代理通过 `run.py` 的 `MAIN_SKILLS`/`--skill` 获得五项 SVC 及领域、设计、浏览器技能目录；`instructions.md` 另作为 profile 的 `user_instructions`。Pi 0.85.1 `core/skills.js::formatSkillsForPrompt` 提供名称、描述、路径，**不直接注入各 SVC 正文**。因此父知道有 task-packet，不等于它读过 `references/delegation.md`。父收到的当前明确委派说明来自 variant instructions 第 17 行；强制 vision 分工来自第 15 行，并非 SVC 通则。

子角色都配置 `systemPromptMode:append`、`defaultContext:fresh`、`inheritProjectContext:false`、`inheritSkills:false`。显式 `skills` 仍会被加载成该子角色自己的技能目录：pi-subagents 0.56.0 `agents/skills.ts::buildSkillInjection` 明确要求匹配任务时用 read 读取，而非注入全文。禁止继承不等于没有方法，也不等于父任务的需求和授权会自动传入。

| 角色 | 直接追加正文（除角色自身文本） | SVC 可发现入口 | 权限、输入与返回边界 |
| --- | --- | --- | --- |
| advisor / Kimi | design `references/workflow.md`；后台命令收尾规则 | design、investigation、verification | read/搜索/bash；正文约束只读。输入是目标、约束、证据与待决问题，返回推荐、理由、反例和不确定性，不接管决定 |
| explorer / DeepSeek | investigation workflow；后台收尾规则 | investigation、verification、task-packet | read/搜索/bash；正文约束只读，另有 rg/ast-grep/Context7/Exa 工具知识。返回来源支持的事实及下一步影响，不回传全检索过程 |
| executor / DeepSeek | implementation workflow；后台收尾规则 | implementation、investigation、verification、task-packet | read/bash/edit/write/搜索；局部授权、保留他人改动、取得反馈。返回实际修改、观察与未决项，父负责整合 |
| browser-operator / 视觉 DeepSeek | agent-browser SKILL；后台收尾规则 | verification | read/bash；限定应用效果，不改源码。输入 URL、判据、账号、初态；返回旅程观察和证据，不替代可重复最终验收 |
| vision / 视觉 DeepSeek | 无 SVC 或后台扩展正文 | 无 | 仅 read；给定图片/材料到带路径的视觉事实、布局、疑点和未知，不推断未显示交互 |

四个非 executor 角色已有 `completionGuard:false`。advisor/explorer/browser-operator 的“只读”是工作约束，bash 并不是只读沙箱；vision 的工具集合才形成更窄的能力边界。领域技能是知识入口，角色正文规定工作责任，SVC 提供方法，工具配置限定能力，父委派提供本次目标与允许效果；这几层不能相互代替。

## 五项高价值发现

### 1. 委派方法主要在父的可选入口，不能用子已注入 workflow 证明委派质量已受约束

**事实与判断：** SVC task-packet 的 delegation 已要求比较直接工作/确定性工具、计算上下文转移和整合成本、提供消费者与效果范围、一目标优先单写者。executor 直接追加的是“怎样实施”，不是父的“值不值得派、派给谁”。官网根重复交相同 rebase、本地 Flash 又把已有成员负责的共享基础交给 executor，说明实际输入/所有权判定出了问题，不证明 Corpus 缺少完整角色体系。

**正反场景：** 独立的参考图事实提取、噪声检索可减少父注意力成本；把正在由另一成员整合的同一工作树再交 executor，任务文字即便写“唯一写入者”也不成立。

**建议与预期：** 保留当前轻量父指引及可选方法入口，不把全部 delegation 正文强塞所有角色。若需要方法级收敛，只在现有 delegation 的单写者句附近表达“先核对现有所有者/在途产物，再选择新增委派”，避免另造流程。预期新委派能指出与现有工作不重叠的产物/责任；简单已知查找直接完成也算合格，不以委派次数验收。

### 2. Fresh 是上下文传递责任，不是独立判断或权限正确性的保证

**事实与判断：** 五角色不继承父历史/项目上下文，但都有明确方法或工具入口。SVC 已要求传目标、相关来源、效果边界、返回和场景前提。已有三个 vision 任务之所以可被消费，是给了实际参考图和问题；官网 rebase 的两个任务虽各自有 cwd/冲突范围，却各自宣称唯一写入者，说明遗漏的是活跃所有权这一当前事实。角色名称、fresh 和模型档位都不能补上它。

**正反场景：** 将一个有争议的 API 契约及版本交给 explorer，可返回独立事实；只说“review 一下”或把父方案当事实交 advisor，容易让它复述方案。允许 bash 的调查角色不能被称为硬只读。

**建议与预期：** 不新增统一任务模板或额外权限系统。通用方法继续要求最小充分上下文，并把“已有相关工作/不能触碰的表面”视为效果边界的具体内容。预期子返回能追溯输入来源和观察边界；遇到超出授权或关键缺失时返回明确未知，而不是继承一份未提供的产品决定。

### 3. 结果消费的缺口应落在交接和证据判断，不应用“再派一个 reviewer”补偿

**事实与判断：** GitHub 三个 executor 中两个终态未证，一个 SIGKILL；没有可靠父消费链。Sheet 38 次无匹配 wait 也没有产生可消费成果。反例是本地 GitHub 两个 vision 的完整通知与父随后的需求比对。SVC delegation 已要求 consequential result 的验证，verification 已要求结论绑定产物、输入、条件和原始证据，故不是缺少“验证”口号。

**正反场景：** 视觉报告可支持“图上显示了什么”，父再结合文字需求决定实现；executor 启动回执或一条“已合并”不能支持依赖实现已进入当前候选，更不能支持整体验收。已有有效证据无需父逐步重做，也无需固定增加 reviewer。

**建议与预期：** 可在现有通用交接语义中明确区分启动/进行中/完成结果，并要求消费者判断结果对当前决定的适用性；具体 run ID 和 Issue/PR 命令仍属于 harness 指引。预期父的结论引用实际返回/产物及适用范围；失败、部分、未知保持对应状态，不能由角色身份自动升级为完成。当前 variant 第 5、17 行已补这些具体接缝，不应再叠一份同义 SOP。

### 4. 跨会话身份/通知和语义 guard 属于工具问题，Corpus 无法修复

**事实与判断：** 原生无 id status 只列当前父 session；完成通知和 wait 绑定原 session/owner。新父无法自动发现/收到旧子返回，正是重建后重复 rebase 的重要机制。只读 vision 因任务中 UI 文案触发“实施意图”而启动失败，则是 guard 与角色工具契约冲突。Unknown agent、bg* 被传给 subagent_wait 是工具命名空间使用错误，靠准确接口说明处理。

**正反场景：** 当旧 UUID 和 status/result 可用时，父可以查询和消费；若冷恢复已丢失临时状态，Corpus 中再写十次“先查状态”也不会恢复证据。避免误用需要告诉父真实入口，不能发明跨 session resume/adopt。

**建议与预期：** Corpus 最多保留恢复前核对既有事实、未知不等于失败、失败不等于可安全重派的通则。工具连续性由当前 observer 被动交接及原生正确接口处理，guard 用结构化角色契约处理，不往 Corpus 加 UI 动词黑名单、轮询策略或子进程管理。预期真实重建时旧 UUID/已知终态或 unknown 可见且被消费；若不可见，这是设施缺口，不归咎于模型没遵守 SVC。被动交接实现尚待真实重建验证，不能以提示更新宣称已验收。

### 5. 强制 vision 是当前 harness 的专门分工，不宜推广为 SVC 的普遍委派规则

**事实与判断：** 当前 variant 明确所有需求参考图视觉解读交 vision，即使父支持图像也一样；vision 无 SVC，只有 read 和短角色指引。官网 Sheet 曾有 13 次父直接读图；本地有三次 vision 完成且被父消费，但没有控制变量证明质量或成本净收益。因此这是已选运行策略，不是由现有样本证明的通用最优规则。

**正反场景：** 多图跨状态比较、视觉模型与主模型能力不同、需要带来源的事实压缩时，独立 vision 有清晰价值；单个已取得有效观察的参考图重复派、图片根本未提供、视觉服务不可用或报告延迟时，强制交接会增加等待和恢复成本。截图事实还可能与文字需求冲突，本地父以需求文字判断正体现消费者责任。不能让 vision 从图猜产品需求，也不能因子报告尚未返回而宣称需求已完整审阅。

**建议与预期：** 不在本轮擅自取消此明确分工，也不把它写入通用 SVC。方法侧只保留按能力/证据/转移成本选择工具或角色、复用有效观察、把未知留给消费者的原则。harness 后续若审此策略，应明确材料缺失/能力失败时的处理和何时复用既有观察，而非重试到有报告为止。预期同一相关图组形成可追溯且可复用的一份观察，父显式处理图文差异；成功标准是减少决策不确定性和返工，不是调用了 vision 或独立报告数量。

## 收敛结论

当前 SVC 的委派、权限边界、返回与验证方法大体具备；最值得通用化的窄增量是“已有在途工作属于委派输入事实”和“消费者按实际返回判断当前适用性”。其余高确定性问题分别属于父工具指引、跨会话证据交接、启动 guard 与本项目视觉分工，不应反向膨胀成 Corpus 生命周期框架。这里只提出审查建议，是否修改及其范围由主线汇总当前 Corpus 审查后决定。
