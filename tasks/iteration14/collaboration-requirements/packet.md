# I14 协作与 ARC 需求方法改进

2026-10-02。两项独立技能的改进及随后 What／Why 重构已由本会话实施；cleaner 职责调查和入口方案已就绪，主会话持有 variant 集成、冻结与实际热恢复。任务保持一个紧凑计划；独立 advisor 只返回方法判断，不另建实施分支。

## 目标与授权

让组织、接手、新产品行为裁决、PR 采用/合并和完成判断消费原承诺与适用结果，避免把发布、局部检查或错误共同约定视为完整兑现。委派消息确认用户已复核树并授权继续两技能改进、热修到 I14 系列；主 packet 记录用户明确要求集中于 braid-collaboration 与 ARC 需求方法。本会话允许当前任务 commit，不 push，不启动模型实验或操作现场。

源码权限限于 `harness/skills/braid-collaboration/`、`harness/skills/arc-bench/`，及本 packet。cleaner 诊断初始限定只读；用户随后直接认可 What／Why 下一步，主线确认该人类授权优先，已在两技能范围实施。cleaner role、成员 instructions、variant、core 与现场仍仅提供方案，由主线整合，不在本会话编辑。四个 I14 root/run 入口只给主会话建议，不编辑。共享仓库其它修改不覆盖、不纳入提交。技能正文保留独立文件，不内联进 prompt。禁止 Factory/Braid/SVC 测试、smoke、probe；不向生成材料注入历史应用缺陷答案、分数、隐藏反馈或 rollout。

## 当前事实与方案

证据为 [官网 Flash/Sheet 分析](../../iteration13/i13-2/flash-sheet-score-analysis/findings.md)及 [I14 对账](../evidence.md)。对象和 packet 实际被使用，错误约定也成功接续；首次遗漏与最后放行应分开。ARC 主技能与部分 reference 已读且早期有采用，覆盖 reference 无读取记录；补读不是充分修复。

现有技能已有正确原则，缺的是把原则绑定到下一项决定：接手时找回尚欠完整消费者结果，公开新增语义时对照原承诺，接口条件改变时检查真实调用方，PR 采用/合并及最终关闭时按声明范围消费证据。拟在现有文件重写相应动作及按问题加载 reference 的入口，保留合理局部接受与证据复用，不增加模板、固定三层检查或全节点同步表。通用协作与 ARC 格式保持分离。

先核对现有分发/发现与各 reference，再独立 advisor 审视最小路径，完成材料并按真实调用路径读回。旧源码路径显示四 I14 build 均选择两技能，run 的 MAIN_SKILLS 明确启用；根 issue 当前只提示 ARC 主文件及泛泛适用 reference。实际材料目录由 run 显式复制，完整参考目录随技能取得。

## 验收与效果边界

材料验收核对独立文件及相对链接可达、四 variant 的分发/发现入口、旧规则不矛盾、相关决定能从主文件到达问题 reference。独立方法复核从中性场景判断下一动作，不用阅读次数或角色身份冒充效果。不运行设施测试或模型实验。

能判别的方法采用是：接手任务含原延期承诺的完整结果，新增语义冲突被裁决，真实请求与新接口条件一致，局部证据只支持其范围，未证实义务保持开放。错误首次产生、交付前检出和最终残留分开记录；本次材料改进不能证明这些效果已在 I14 运行发生，也不能给成功率增益。

上一批材料实现与独立方法复核已完成，提交为 `ed9a97bb`；root 入口复核为 `60ba2e01`，历史身份保留。What／Why 接续改写及独立复核已完成，最新材料身份如下。主会话须先将 cleaner variant 的入口与恢复通知按角色判断收敛，再冻结/热恢复；不将上一批统一复读建议机械应用到所有成员。主会话需为每个新/恢复 run 保留旧新技能身份及采用时点；暂停的 baseline 不由本会话恢复。

## 实现与独立复核

改动仅为两个 SKILL 的 description/问题入口及现有 references，共 8 个材料文件；平台 reference 不改。协作方法在组织时保留完整消费者结果、接手时恢复前序延期、传播新约定前比较原承诺、接口改变时核对真实调用、采用/合并时限制结论范围。ARC 方法从原树与适用父层找回义务，在接手、行为变化、审阅采用和完成决定时进入覆盖回查。中性编辑器/导入器例子说明不同判断；没有写入历史题目的具体业务修复。

独立 advisor 先基于指定原证据提出三项决定动作，再对改后材料作中性反例复核：仅错误提示的接手范围须恢复状态保持与重开持久化；后端含版本的请求通过不能证明遗漏版本的 UI 调用正确；检查输入修正与违背原承诺的新保存语义须分别判断。它同时指出有效编辑器结果可先合并，整体不能因此关闭；若漏接线的正是编辑器，旧结果也不可继续视为有效。这是方法决策自洽性复核，不是实际运行采用或收益验证。

逐文件阅读及 `git diff --check` 未发现冲突或格式问题。沿用 SVC 对原要求/派生设计、判据/结果适用性、文档归属与 packet 的现有方法，不复制通用教程。两主文件按问题进入已有 reference；reference 之间的相对地址及所引用四 SVC SKILL 均实际存在。

四 variant 的 `build.py` 明确选择这两技能，`run.py:MAIN_SKILLS` 将主文件加入全部 Braid 成员的 Pi `--skill` 发现入口，并通过 `scripts/agent_support.py:copy_skill` 复制整个 references。`scripts/package_agent.py:assemble` 使用同一复制入口。成员 instructions 已要求开始/接续时读取 braid-collaboration。原生内部角色的自动 skills 选择未包括这两项，局部委派需按本次问题传独立文件入口；不据文件存在宣称自动读取。本次没有运行打包、prepare、测试、smoke 或模型；上述分发事实是源码路径与文件读取的验收，不代表新冻结包或现场已取得它们。

## 主会话的最小接口与热部署前提

2026-10-02 追加接口复核后，决定保留四个 `run.py` 的 root prompt 源码，不添加重复 description。现有 root Issue 已提供本次需求路径、arc-bench 独立文件入口与交付约定；Pi `MAIN_SKILLS` 的发现入口已负责名称、description 和路径。先前建议在 root 再复制 frontmatter 元数据已撤回；两主文件现在会把相关决定引向适用 reference，无需扩角色方法正文、提示模板、工具接口或通用 Harness 的 ARC 耦合。

本次读取 I14 已冻结的 `runs/iteration14/i14-0/linux-runtime/node_modules/@earendil-works/pi-coding-agent/dist/core/skills.js:275`，确认 `formatSkillsForPrompt` 只产生 name、description、location 发现信息；`system-prompt.js:111` 将它加入系统输入，`resource-loader.js:332` 在 `--no-skills` 下仍装载显式 skills。四个 run 的 launcher 已显式传两主文件。`sources/braid/src/provider/pi.rs:505` 的恢复路径保留 native 会话并重新启动 Pi；`submission/recover_completed.py:558` 的显式材料刷新备份旧目录、重建 launcher/技能并记录新哈希。`scripts/package_completed_recovery.py:391` 从完整冻结 base 取得材料，不能仅靠开发目录更新。这些是本地源码及冻结 runtime 的读取证据，尚未读回本次恢复实际发送的系统输入。

恢复现场不能靠源码更新自动获得材料，也不能假定旧会话因技能换版就已采用。主会话须在实际恢复输入中交付完整技能目录，读回逐文件 SHA256；保留旧材料、原需求、Git/Braid/native 身份与恢复来源。恢复后在受影响成员既有的本次工作输入中传一次材料换版事实，列两技能名称、实际独立文件路径与新 SKILL SHA256，不重复 description；同时说明当前材料已换版；由承担相关组织、接手、需求解释、采用或验收决定的成员取得新主文件及适用 reference。此次恢复本身不构成让所有成员统一读两技能的理由，职责选择见下节。这是材料缓存失效与读取动作，不是内联方法正文，也不新增固定提示模板。仅列哈希而没有读取动作可能仍让成员沿用旧历史里的正文；系统发现更新也不证明新正文已读。两主文件新 hash 在下表，完整目录的逐文件身份由部署读回负责，不让每个成员重复做完整性审计。不要把本报告、隐藏反馈或历史具体修复送入生成会话。各 run 保留部署与实际采用时点，未取得采用证据时如实记未观察；暂停 baseline 不因此自动接续。这里不要求额外 ACK 或全部工作重读历史。

缺的观察有三个层次：恢复后的实际系统发现是否绑定新路径与 description；版本变化输入是否到达当前真正实施、集成和检查的消费者；这些消费者是否读取新主文件并在本次相关决定中采用适用 reference。只通知 root 不能证明其它保留会话已更新理解，文件和系统发现更新也不能代表后三者。读回可在原生记录里核对路径、返回的新正文及随后决定；已经有证据的成员不反复通知，不用读取计数或全员 ACK 代替效果。暂无证据要求修改 root prompt 源码；若发现实际系统发现缺失或路径错误，先修部署/launcher 的具体接线，仍不复制 description 作为补丁。

四个 variant 的机制差异保持原样；实际容器、Console、冻结/新启动与恢复一致性由主会话负责，本会话不操作。不新增实验矩阵，效果取证仍消费已授权运行。

## 最新材料身份

下面比较首轮改进提交 `ed9a97bbb8415633dcf1628738ab37e9a035ca7f` 与本次 What／Why 新材料；首轮旧新身份表仍在该提交的 packet 中保留。`60ba2e01` 只修改入口判断，不修改技能。实际冻结/恢复以本表的新值读回，platform 行未变。

| 文件（相对 harness/skills） | 首轮 SHA256 | 当前 SHA256 |
| --- | --- | --- |
| `arc-bench/SKILL.md` | `b92b281913728c54234baed1ceb64518b603a44f246cda58846966eb0a52f2dc` | `f68e56dc12d7b4093ed76a0a8dcb1db73b73142c1287e2fc0494b71966553f4b` |
| `arc-bench/references/platform-delivery.md` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` | `d042032f153e5346dee6913e972c02c322ade51231c6a32aafa172d26423a1dc` |
| `arc-bench/references/reading-requirements.md` | `363686fcf65f95ec0855b92c2cdf6e009f5731e2cfc6fffd65124c51c3537d54` | `d63e2d01b39e78471ac1fcb3c39175bc9000ada612d71c14b649ead904cf272c` |
| `arc-bench/references/tracing-and-reviewing-coverage.md` | `73844a8858351d62036d9b51bac0bedd9ed6f8efdc8e8275eaac6a7580ac3fc5` | `31dc1e18d9705ddad7fed5c3341e796f657beda6e7409ebae9cbf0c033c66a2d` |
| `braid-collaboration/SKILL.md` | `a30cfb7128690b1ef66653bb7e53cd315b4e32845d5c62dd15663b6620dea08a` | `b5008d92d6aa9b687597d21fb7db0ad2fac07fe59880559e7150dc4f6e1da5c4` |
| `braid-collaboration/references/accepting-and-closing.md` | `33043321cc8a971f27ca2dcb780eee62aeee72e5a2337d8a910a5d5194d2bc1a` | `ce894fc7c513cff1f98a75c8855402a4eb07a096d9a393ec6a8de1f584470112` |
| `braid-collaboration/references/handoffs-and-changes.md` | `c2e2d2d1071687c8310fa8597f3ed21d29d9e5e339ec788b47cf2bf9d16991a2` | `4ff3e297ac5c9ce0944cf486d15fab559a3d4a161b656dfe97110e4f5fd6e348` |
| `braid-collaboration/references/organizing-work.md` | `7f785f4e29837ec43457692f3140c7e33f8e78ebded997c3527518090b024a8b` | `6608a81d8a3ba1089020f44e49da7cf48addc015257edad649a0868272312c28` |
| `braid-collaboration/references/worked-example.md` | `f6f30f293f1f3eaa4e923bd9036a56fa3f84b3594aa516d0872f2bc25ddf4aa9` | `7f943770117622391ff6831e1df98e74a47d5b5eb83a36f7e2ecf740d91e74f1` |


## cleaner 职责接续方案：当前结论与待集成范围

用户新增目标是让 work-item 不必以 “Let me start by reading the braid-collaboration skill and viewing the PR.” 开场。用户又确认 What／Why 应具体到能区分选择，并原话认可：“我同意你的职责分配，不过根据分析，可以暂缓引入 Hook；也同意你的下一步。”此为本轮两技能 What／Why 改写的直接用户授权，范围是概念、因果理由、判断依据与中性反例；具体命令与外部接口约束保留必要 reference，不把绑定决定等同固定操作流程。主线随后明确授权该范围继续实施，cleaner 其它源码仍由主线整合。Hook 暂缓，没有新增 hook 或运行机制。

### 已核对的原因与反证

cleaner variant 的 `agents/pi-glm-fast/instructions.md:1` 和 `agents/pi-glm-root/instructions.md:1` 无条件要求开始/接续读 braid-collaboration，后段仍将发布与采用归给共同技能。工具段只免去逐条整理计划。因此有 cleaner 不会自然消除固定技能开场；`MAIN_SKILLS` 是发现信息，与强制读取是不同入口，不应为取消开场而删掉发现能力。

定向原生取证仅检查保全目录 `runs/iteration14/cleaner-hidden-context-20261002/cleaner/workspace/template/.factory26/20261001-175111-a7c5faa8/work/native-homes/` 下两份有关 session：`pi-glm-fast-01a0f89d-f04f-7fa1-9821-52df69019506/sessions/2026-10-01T17-58-17-892Z_01a0f89d-fa23-7195-89c4-3992fd4e77f1.jsonl` 第4行已有 PR2 目标、范围、判据及状态，第5行实际先读技能并 `pr view 2`，第8行又查评论。`pi-glm-fast-01a0f922-57f9-7bc1-9e7f-25fa7594a20f/sessions/2026-10-01T20-23-01-380Z_01a0f922-7a03-7601-9d68-7c1e074b7337.jsonl` 第4行已投影 PR3 的 OPEN ready、glm-3 assignee、base/head branch、正文及部分讨论，第5–7行查询的 PR 字段重复这些已有事实；同时定向读取了评论29。该评论完整交接正文不在当时投影的讨论21/22中，后者仍说原负责人持有 head 推进权，因此评论29查询有具体接手价值，不能一并归为无效重读。第8行还明确“按指令”读技能。这里只定位了两次开场，不推断其它会话的重复读取比例。

`context.rs:433` 已渲染 PR 正文、状态、分支及讨论；`project_body` 折叠 details 并过滤注释，预算路径还可能截短正文或只留评论索引。因此投影足够时可直接消费，折叠细节、相关新评论、冲突或候选身份未知时仍需定向查询。避免重复 view 的根据是当前决定所需信息已经足够，不能以 cleaner 已存在推导信息完整。

`factory-cleaner.ts:118–165` 只投影触发前有效分支，再从 maintenance snapshot 取得完整当前对象、评论及需求背景；`factory-cleaner.md` 已限定一次维护。独立 complete 不提供工具，cleaner 自身不能读取独立技能或核实应用/文件/真实结果。maintenance 快照中的 description 与评论较新，只证明对象事实较新，不证明其中产品主张正确。由无工具 cleaner 自动承担原承诺裁决或验证，会超出现有能力与已批准职责。

### 职责与最小范围

| 消费者 | 应承担的结果 | 未知或缺证据时的边界 |
| --- | --- | --- |
| cleaner | 整理当前 description，合并重复陈述，保留已明确采用的决定、未决义务及证据入口；按已有成立事实整理讨论。 | 不产生新的完成/采用结论，不替人改变范围或责任；缺少依据或存在分歧则保留，不能因某条评论声称通过就认定问题解决。 |
| 实施/接手成员 | 从当前已提供的任务与结果继续做事；决定当前范围是否承接前序完整义务，核实必要接口与真实调用，发布自身成果和文件。 | 对具体缺口补读原要求、评论、代码、文档或结果；不替 cleaner 写改写/hide/resolve 计划，也不为例行整理预先阅读全部协作方法。 |
| 原承诺与验收责任人 | 解释新增用户行为、采用候选、判断结果覆盖与整体完成。 | 保留原文权威、真实调用与完整消费者结果闭环；方法按本次判断取得，不能交给只见文本的 cleaner 裁决。 |

最小源码范围建议首先限于 cleaner 两份成员 `instructions.md`：取消会话开始/接续即读协作技能的首段义务；职责入口说明既有投影可直接消费，例行正文/讨论整理由 cleaner 承担，工作方法随当前实际判断取得。它描述角色与能力边界，不内联任何 Skill 正文。原 SVC 文件发布与 packet 维护仍由有文件工具的成员负责，不因 cleaner 整理了 description 而删除。

`factory-cleaner.md` 的现有范围基本足够，若主线确认需澄清，仅补职责边界以区分“整理已成立事实”与“制造新的正确/完成判断”。不需改 `factory-cleaner.ts`、增加工具、改 Braid core 或新增 hook。两技能保留在 `MAIN_SKILLS`；共享技能的判断闭环不因 cleaner 存在而删除。其主体 What／Why 已按最新直接授权改写，也不是取消固定开场所需的运行机制前提；不能为一个 variant 全局免除其它责任人的判断。

共享方法按职责消费：work-item 在组织结果、接手延期、改变共同约定、采用成果或判断完成时取得相应概念与判别依据；普通已明确的局部实施不需要为了整理重读整套方法。ARC 原文与覆盖判断仍归应用实施/验收责任人。当前 cleaner 从所供历史和快照消费已成立事实及保留义务，不要求它执行独立 Skill 阅读；若未来要让它独立学习新方法，则需要另议材料取得能力，不能复制技能正文进其 system 作为捷径。

恢复通知建议继续交付两技能的换版身份与路径，但取消“root glm-1 / PR3 glm-3 统一立即读两主文件”。root 正在组织、解释或采用结果时与两技能直接相关，需取得适用新方法；PR3 的 glm-3 按实际接手/剩余实施/交付决定选择材料，不因恢复一律复读，也不因 cleaner 存在免去完整承诺判断。generic 通知接口仍由 shared owner 持有，只传版本变化事实与材料入口，不塞 role 方法或操作模板。是否实际采用按后续决定取证。

### 实际验收判别与移交

下一条获授权真实 cleaner 接续中，分别观察：已有投影足够且无新协作决定时，负责人直接推进局部工作，无机械技能开场、重复 view 或无必要 cleaner 调用；存在评论索引/折叠缺口、责任冲突或候选未知时，按具体问题查询并继续接手/验收；延期完整结果、新语义与真实调用的原判断闭环仍成立；cleaner 不把冲突或无依据的完成主张变成已解决事实。衡量减少的重复获取与整理成本及总成本，同时检查义务与有效知识是否保留。少一句开场、少一次 view、cleaner 正常返回都不足以证明收益。

独立 advisor 已只读核对职责、输入、投影路径与技能，支持先改 cleaner variant 的入口，保留按需查询和产品判断，并明确无工具 cleaner 的能力边界。该判断由源码与定向原生证据支撑，不用 reviewer 身份当实际采用证据。cleaner 职责调查没有运行测试、smoke 或新模型请求，未改 cleaner role、variant、core 或现场。主线负责整合成员入口与通知正文；cleaner 最终 launch 待该职责方案集成，Flash/GitHub 已在运行不受此调查阻塞。本会话另按直接用户授权完成下述两技能改写，没有留下待本会话自行修改的源码工作。


## What／Why 接续实现与完成边界

本轮仅重写两 SKILL、各方法 references，并微调现有中性例子，共 8 个材料文件；路径与目录结构不变，平台外部合同原件不动。主文件以目的、概念差异、因果关系及成立条件说明方法用途，references 展开会改变选择的条件。移除了会话生命周期驱动的阅读顺序、Git 工作树定位命令、提交/push 教程及重复维护动作；消费者可发现、可取得且与适用候选相符的材料条件仍保留，详细文档/packet 方法仍指向 SVC 独立入口。

关键判断没有以抽象口号替代：接手安置责任、适用结果支持兑现；新产品约定与原承诺/授权范围有不同地位；真实用户入口须进入接口所需条件才能把局部能力连接到结果；旧证据的适用性由行为与条件的影响决定；有效局部成果、局部工作结束与整体完成有不同依据。当前信息足够时可以直接消费，定向取材由具体未知驱动。整理者组织已成立事实和开放义务，较新快照未使主张自动正确。

ARC 原树/父层的语义适用性、跨枝完整操作、GIVEN 的产品启动/正常用户状态/检查条件区分、图片真实观察与允许输入边界仍保留。generic 协作技能没有 ARC 格式或历史题目答案。例子展示判断分叉而非要求复制固定步骤；平台安装/构建/启动命令是实际外部条件，仍在原 reference。

独立 advisor 先审视 What／Why 容易丢失的条件，再对改后材料以新的三选择复核：私有 packet 只有实际可发现、可取得且适用，才能支持另一 clone 接续；同格式的新消费者可能因读取时机/失效关系不同而尚未正确采用；有效局部成果且后续责任明确时可先合并，整体仍需剩余依据或有权目标变更。结果支持判断条件自洽，不能当实际 Agent 采用证明。

逐文件阅读与 `git diff --check` 完成，独立地址与交叉引用沿原路径保持。没有运行设施测试、smoke、prepare、打包或模型；后续冻结与恢复应以最新材料 hash 读回。本次只完成材料与可消费的入口职责方案，未热部署、未据此宣布运行采用或质量收益；新通知旧 candidate 保留，最终版本由主线按本次职责方案选择。
