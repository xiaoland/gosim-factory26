# 表现—问题定位—修复目录

本目录先于独立复审建立，覆盖 closure.md 已登记的29项与后续新增项。定位是待复审的主张，不是审查必须接受的事实。
原运行分数不是本轮修复效果；源码落地、编译/实际操作、模型采用、评分收益分开判断。
本目录链接是相对仓库根路径；源码范围含 pi-braid 与独立 Flash 对照。源文档提及的旧 Braid 测试仅是历史证据，现已全部清退，禁止复跑或重建。

## 原账本中的缺陷与工作流程调整

每项“表现/定位”当前合并记录于原账本，审查应拆开检验：具体观测是什么、原因是事实还是解释、哪个产品要求支撑修复。不存在直接因果证据时降级，不补造它。

### R01 根把comment view末尾delivered回执误读成子任务已交付

- 表现（需回到原证据核对）：根把comment view末尾delivered回执误读成子任务已交付，实际正文只是检查进展。
- 当前问题定位（可被推翻）：正文与消息传输回执混排，业务完成和输入接收语义未分清。
- 已应用修复主张：Braid CLI创建/编辑/查看评论共用消息回执展示，与正文分区；delivered明确为“会话已接受评论输入”，保留JSON和原始reason。
- 源码/材料入口：`sources/braid/src/cli/mod.rs`。
- 证据与当前验证限制：GitHub根session04 L25–32给出直接误读链；已编译，在原GitHub最终DB副本实际执行comment view 4 --thread，确认检查评论、催交接回复与消息回执分区；不把全部接管损失武断量化。

### R02 环境共同约束只在根Issue

- 表现（需回到原证据核对）：环境共同约束只在根Issue，独立子项及fresh原生角色未稳定收到。
- 当前问题定位（可被推翻）：共同条件仅依赖根任务继承，fresh成员/原生角色不自动持有。
- 已应用修复主张：pi-braid与Flash的run.py将运行条件移为单一正文，由native_files直接追加给每个profile及四个有bash的原生角色；保留原有fresh、只读/委派边界，vision仍只读给定材料。
- 源码/材料入口：`variants/pi-braid/run.py；variants/pi-braid-flash-team/run.py`。
- 证据与当前验证限制：输入审计确认旧/当前缺口；源码接线已改并静态核对，未打包运行；不把缺输入直接等同已发生环境污染。

### R03 整合PR负责人和根负责人都被指示关闭根Issue

- 表现（需回到原证据核对）：整合PR负责人和根负责人都被指示关闭根Issue。
- 当前问题定位（可被推翻）：指令将PR交付与根整体关闭两位负责人的动作混在一起。
- 已应用修复主张：五份当前profile正文删除PR负责人关闭根项动作，保留整合验收、合并、交接，再由根判断整体关闭；并收敛重复PBB service说明。
- 源码/材料入口：`variants/pi-braid/agents/*/instructions.md；variants/pi-braid-flash-team/agents/*/instructions.md`。
- 证据与当前验证限制：当前正文已核对；不修改Braid显式Closes对象语义，不宣称旧关闭错误全由此造成。

### R04 原需求在根→共享契约→子项→oracle间收窄

- 表现（需回到原证据核对）：原需求在根→共享契约→子项→oracle间收窄，初始状态被自建数据绕过。
- 当前问题定位（可被推翻）：派生说明和oracle没有持续保留原始约束/初始前提。
- 已应用修复主张：根prompt先形成跨项方案，子项保留原始需求/场景/状态入口；SVC product/check-design补并列范围、非单调规则、setup绕过范围和冲突解释的证据限制。
- 源码/材料入口：`variants/pi-braid/run.py；sources/svc/skills/svc-design/references/product.md；sources/svc/skills/svc-verification/references/check-design.md`。
- 证据与当前验证限制：源码已写，下一运行观察交接和真实判据；不硬编码赛题答案。

### R05 已看到原始需求与派生任务冲突

- 表现（需回到原证据核对）：已看到原始需求与派生任务冲突，却将派生任务当新权威并传播。
- 当前问题定位（可被推翻）：成员把派生描述当原始需求的新权威，冲突未交负责者显式裁决。
- 已应用修复主张：SVC product把原有原则落实为原句对照、交负责决策者处理、显式变更后更新受影响材料；区分原输入内部矛盾和派生改写，保留有据裁决。
- 源码/材料入口：`sources/svc/skills/svc-design/references/product.md`。
- 证据与当前验证限制：GitHub原生证据确认有意识选择派生版本；部分错误后期改回，不能直接归因最终失分；方法和skill导航已改。

### R06 接口的实际用途迁移

- 表现（需回到原证据核对）：接口的实际用途迁移，另一任务仍按旧用途保留校验豁免；重复规则只做窄parity检查。
- 当前问题定位（可被推翻）：调用用途改变未被视为契约变更，旧豁免前提未复核。
- 已应用修复主张：SVC technical明确用途变化也是契约变化，追踪调用者到判定/写入及旧豁免前提；implementation要求受影响消费者随改动更新；check-design补相关规则的可达交叠/状态变化及跨组件实际交接观察。
- 源码/材料入口：`sources/svc/skills/svc-design/references/technical.md；sources/svc/skills/svc-implementation/references/workflow.md；sources/svc/skills/svc-verification/references/check-design.md`。
- 证据与当前验证限制：Sheet PR15/19、双规则实现和公开路径构成证据链；已补通用方法，不替生成应用修业务逻辑，不推断隐藏42项归因。

### R07 vision发现截图不支持其标题

- 表现（需回到原证据核对）：vision发现截图不支持其标题，父用另一边界的PASS排除疑点并在终报弱化披露。
- 当前问题定位（可被推翻）：父会话把其它属性的PASS作为排除图像反证的依据。
- 已应用修复主张：SVC interpreting-results补同一待证属性的反证处理：解释测量错误、取得缺失观察或缩小声明，不能用其它层的PASS补证据。
- 源码/材料入口：`sources/svc/skills/svc-verification/references/interpreting-results.md`。
- 证据与当前验证限制：Sheet原生父确实读并逐项处理vision反馈，并非漏投递/完全忽略；已修解释方法，截图缺证不等同公式功能失败。

### R08 根将共享基础整体转为子Issue；Issue自行实现后补PR

- 表现（需回到原证据核对）：根将共享基础整体转为子Issue；Issue自行实现后补PR。
- 当前问题定位（可被推翻）：共享基础责任和Issue/PR实施边界在当前variant指引中不清。
- 已应用修复主张：根直接负责基础设计/交付，经关联独立PR实施；Braid职责明确Issue设计与PR计划/预演/实现/验收，Pi主指令按需路由SVC。
- 源码/材料入口：`variants/pi-braid/run.py；sources/braid/src/group/provider.rs`。
- 证据与当前验证限制：当前源码与说明已写，模型实际执行待验。

### R09 advisor只在实现后被当作重复检查

- 表现（需回到原证据核对）：advisor只在实现后被当作重复检查，重要假设先传播。
- 当前问题定位（可被推翻）：独立判断的触发时机和普通委派ROI混淆；零调用本身不能证明阻断。
- 已应用修复主张：父指令/角色description前移咨询，SVC设计归独立判断，排除普通委派ROI门槛。
- 源码/材料入口：`variants/pi-braid/agents/*/agents/advisor.md；sources/svc/skills/svc-sub-agents/`。
- 证据与当前验证限制：六组历史0调用；K3目录可用，真实工具往返/返回/父消费须新运行观察。

### R10 把已指派Braid工作再交原生executor启动；错误角色名修正仍重复整个Issue

- 表现（需回到原证据核对）：把已指派Braid工作再交原生executor启动；错误角色名修正仍重复整个Issue。
- 当前问题定位（可被推翻）：Braid成员所有权与原生角色名字混淆，改对名字后仍可能重复工作。
- 已应用修复主张：Braid指派回执说明已交给成员推进；Pi主指令区分当前成员内部工作与其它成员责任；executor核对重叠；Unknown agent在调用处保留错误并提示目录与所有权。
- 源码/材料入口：`variants/pi-braid/extensions/factory-subagent-observer.ts；variants/pi-braid/agents/*/agents/executor.md；sources/braid/src/cli/mod.rs`。
- 证据与当前验证限制：[三角色审计](../factory-subagents/cells/iteration10-role-audit.md)，源码已写。

### R11 父重建后旧子任务身份与结果未承接

- 表现（需回到原证据核对）：父重建后旧子任务身份与结果未承接，重复派同一写任务。
- 当前问题定位（可被推翻）：父原生重建未携带旧子任务身份和结果入口。
- 已应用修复主张：原生observer按同工作区登记旧run/artifact/status，首轮注入并监听终态转送。
- 源码/材料入口：`variants/pi-braid/extensions/factory-subagent-observer.ts`。
- 证据与当前验证限制：08已有注入正例，真实在途终态→新父消费未证；不让Braid接管子代理生命周期。

### R12 vision纯读角色被修改意图guard误拒；PBB等待误用subagent_wait

- 表现（需回到原证据核对）：vision纯读角色被修改意图guard误拒；PBB等待误用subagent_wait。
- 当前问题定位（可被推翻）：修改意图guard误套读图；后台job与sub-agent等待接口混淆。
- 已应用修复主张：非实施角色completionGuard关闭；observer在原生空结果保留错误、提示PBB入口。
- 源码/材料入口：`variants/pi-braid/agents/*/agents/vision.md；variants/pi-braid/extensions/factory-subagent-observer.ts`。
- 证据与当前验证限制：已有vision成功链，等待纠偏待新运行；后台完成机制另列下节。

### R13 explorer工具知识分散在额外skill

- 表现（需回到原证据核对）：explorer工具知识分散在额外skill，角色缺具体方法。
- 当前问题定位（可被推翻）：探索工具/SOP藏在额外skill而不在角色就绪指引。
- 已应用修复主张：explorer直接含rg/ast-grep/Context7/Exa路由，领域知识留对应skill，MCP配置归variant/tools。
- 源码/材料入口：`variants/pi-braid/agents/*/agents/explorer.md；variants/pi-braid/tools/mcporter.json`。
- 证据与当前验证限制：已落地；explorer零调用无阻断证据，不加配额、不重复装旧exploration-tools。

### R14 同一Pi会话每次prompt重复完整Context

- 表现（需回到原证据核对）：同一Pi会话每次prompt重复完整Context。
- 当前问题定位（可被推翻）：待注入Context在成功接受后未清除。
- 已应用修复主张：prompt接受后清待注入副本，失败/Deferred保留。
- 源码/材料入口：`sources/braid/src/provider/session.rs；sources/braid/src/provider/pi.rs`。
- 证据与当前验证限制：Braid3项协议验证通过；已有v2包，真实净token节省待测。

### R15 sleeping恢复暂时失败

- 表现（需回到原证据核对）：sleeping恢复暂时失败，把未送达联系标blocked/unreachable。
- 当前问题定位（可被推翻）：暂时恢复故障被处理成永久身份/投递失败。
- 已应用修复主张：原生resume暂时错误用既有Deferred；事务退回sleeping/pending/queued并保留原生ID及last_resume_error；worker沿已有2秒恢复节流重试，静止故障沿原health边界退出保现场。
- 源码/材料入口：`sources/braid/src/provider/session.rs；sources/braid/src/group/dispatch.rs；sources/braid/src/group/worker.rs；sources/braid/src/store/mod.rs；sources/braid/src/local.rs`。
- 证据与当前验证限制：当前Braid63/63，包括worker失败一次后同会话恢复/恰好消费一次，以及静止失败保留同请求接续状态；不永久暂停整组，真实Pi恢复仍待实验。

### R16 终态联系逐条启动造成大量无行动会话

- 表现（需回到原证据核对）：终态联系逐条启动造成大量无行动会话。
- 当前问题定位（可被推翻）：联系逐条消费且新建会话，缺少技术层合批与有效复用。
- 已应用修复主张：同工作项/成员/revision批量接收，逐条保留收据，新联系不误休眠。
- 源码/材料入口：`sources/braid/src/group/dispatch.rs；sources/braid/src/store/mod.rs`。
- 证据与当前验证限制：8项生命周期验证通过；sleeping原生复用另列下节。

### R17 短期进度反复改description、失效决定留在工作记忆

- 表现（需回到原证据核对）：短期进度反复改description、失效决定留在工作记忆。
- 当前问题定位（可被推翻）：对象用途和整理动作未被清晰介绍；是否工具缺陷仍需审查。
- 已应用修复主张：Braid介绍稳定description、增量comment/thread；更正、hide理由、resolve及生效时机。
- 源码/材料入口：`sources/braid/src/group/provider.rs`。
- 证据与当前验证限制：当前指引已写，自然整理效果待验，不自动判消息语义。

### R18 PR正文Closes无效；背景关联和关闭意图混淆

- 表现（需回到原证据核对）：PR正文Closes无效；背景关联和关闭意图混淆。
- 当前问题定位（可被推翻）：关闭意图与背景关联混淆，合并发布与恢复没有统一结算。
- 已应用修复主张：默认分支、冻结merge intent和发布恢复统一结算；CLI/create/link帮助明确背景关联不自动关闭。
- 源码/材料入口：`sources/braid/src/objects.rs；sources/braid/src/worktree.rs；sources/braid/migrations/0014_pr_closing_intent.sql`。
- 证据与当前验证限制：定向验证通过，当前objects集合14/14；不追溯develop子PR，不关闭全部背景Issue。

### R19 显式退订仍因历史参与被唤醒

- 表现（需回到原证据核对）：显式退订仍因历史参与被唤醒。
- 当前问题定位（可被推翻）：历史参与者推导覆盖了明确退订状态。
- 已应用修复主张：排除显式退出的自动参与者，保留负责人责任和当次@；help/回执明确主动subscribe才恢复。
- 源码/材料入口：`sources/braid/src/objects.rs；sources/braid/src/store/mod.rs；sources/braid/src/cli/mod.rs`。
- 证据与当前验证限制：行为验证通过，自然采用待验。

### R20 指派配置与具体成员含义不清

- 表现（需回到原证据核对）：指派配置与具体成员含义不清，Issue创建不返负责人。
- 当前问题定位（可被推翻）：CLI没有把能力选择和具体执行成员身份说清。
- 已应用修复主张：create/edit帮助与回执区分所选名称和具体成员，Issue create JSON返回assignees/assignment_note。
- 源码/材料入口：`sources/braid/src/cli/mod.rs；sources/braid/src/objects.rs`。
- 证据与当前验证限制：当前编译与issue create --help已核，objects14/14。

### R21 Git手工整合后PR状态无法准确说明；Issue/PR编号分开

- 表现（需回到原证据核对）：Git手工整合后PR状态无法准确说明；Issue/PR编号分开。
- 当前问题定位（可被推翻）：两个编号分配器与已发布Git事实没有对应统一对象行为。
- 已应用修复主张：正证识别已整合候选，不改Git、不捏造merge commit；新建工作项共用序列，旧数据保留原编号。
- 源码/材料入口：`sources/braid/src/objects.rs；sources/braid/migrations/`。
- 证据与当前验证限制：当前objects/迁移0013已修，Braid边界检查回归中。

### R22 同head/base PR接管竞态；更新head后未消费承诺的检查便合并

- 表现（需回到原证据核对）：同head/base PR接管竞态；更新head后未消费承诺的检查便合并。
- 当前问题定位（可被推翻）：把没有发布进展等同停工、把当前head匹配等同检查前提解除。
- 已应用修复主张：接管先联系当前负责人或核实失败；合并前消费当前候选结果与尚未解除前提。
- 源码/材料入口：`variants/pi-braid/agents/*/instructions.md`。
- 证据与当前验证限制：指令已落地；不增加自动锁/审批门，head匹配不证明语义前提满足。

### R23 已退役地址反复物化产生2.1万唯一键错误；根关闭绕过开放工作

- 表现（需回到原证据核对）：已退役地址反复物化产生2.1万唯一键错误；根关闭绕过开放工作。
- 当前问题定位（可被推翻）：旧身份输入未在共同技术边界收尾；终态判断范围不全。
- 已应用修复主张：历史输入在共同边界结清；保持同一成员恢复与显式改派区别；全范围终态统一。
- 源码/材料入口：`sources/braid/src/store/mod.rs；sources/braid/src/group/worker.rs；sources/braid/src/local.rs`。
- 证据与当前验证限制：[既有实现与实证](../braid-product-reaudit/cells/termination-contact.md)，当前全套回归中。

### R24 无provider的materializing孤儿阻止交付

- 表现（需回到原证据核对）：无provider的materializing孤儿阻止交付。
- 当前问题定位（可被推翻）：离线中间态未区分仍执行与已无provider的孤儿。
- 已应用修复主张：离线确认停止后，开放项保留身份/工作区并重排，结束项收尾，重复执行幂等。
- 源码/材料入口：`sources/braid/src/local.rs；sources/braid/src/store/mod.rs`。
- 证据与当前验证限制：旧Sheet实恢复、无模型调用、应用树不变并评分；不是迭代10新生成。

### R25 原生余额/429失败被泛化

- 表现（需回到原证据核对）：原生余额/429失败被泛化，运行中误当有进展。
- 当前问题定位（可被推翻）：原生供应商错误被泛化，监控未区分最近成功和连续失败。
- 已应用修复主张：Pi保存stopReason/errorMessage；新监控按恢复边界看连续failed与最近成功。
- 源码/材料入口：`sources/braid/src/provider/pi.rs；tasks/iteration10/scripts/monitor-generation.py`。
- 证据与当前验证限制：Pi原始错误已保留；监控已用真实fresh/recovery记录核对，能识别同当前会话连续未恢复错误，旧Sheet22条429作为明确故障证据；不自动取消/换模型。

### R26 长检查首轮缺exit导致重跑

- 表现（需回到原证据核对）：长检查首轮缺exit导致重跑，同候选结果被重复验证。
- 当前问题定位（可被推翻）：首轮结果与后续消费路径分离；已有证据复用条件不清。
- 已应用修复主张：agent-browser with-service支持check-only及首轮exit/候选/条件/日志；SVC按内容/检查/数据/环境复用。
- 源码/材料入口：`harness/skills/agent-browser/scripts/with-service.py；sources/svc/skills/svc-verification/references/interpreting-results.md`。
- 证据与当前验证限制：实际生成应用副本正常/失败/中断/邻居服务验证完成，未进统一新包。

### R27 全局pkill破坏别人检查

- 表现（需回到原证据核对）：全局pkill破坏别人检查。
- 当前问题定位（可被推翻）：进程清理没有限定实际所有者。
- 已应用修复主张：按job/PID/process group只收尾自有资源；helper管理自己启动的进程组。
- 源码/材料入口：`harness/skills/agent-browser/SKILL.md；harness/skills/agent-browser/scripts/with-service.py`。
- 证据与当前验证限制：实际应用验证完成；SIGKILL等不保证最终回执。

### R28 跨设备硬链接、错误Chromium路径、长socket路径造成排障

- 表现（需回到原证据核对）：跨设备硬链接、错误Chromium路径、长socket路径造成排障。
- 当前问题定位（可被推翻）：未使用已提供运行路径且复制/socket假设与环境不符。
- 已应用修复主张：现有agent-browser指引使用运行时浏览器路径、普通copy/install与短TMPDIR。
- 源码/材料入口：`harness/skills/agent-browser/SKILL.md；variants/pi-braid/run.py`。
- 证据与当前验证限制：当前工具/指令已修，收益待新运行，不建新应用脚本框架。

### R29 巨大status输出；Collector错误重建导致全量重发

- 表现（需回到原证据核对）：巨大status输出；Collector错误重建导致全量重发。
- 当前问题定位（可被推翻）：面向Agent输出包含物理全集；Collector发送进度随实例丢失。
- 已应用修复主张：Agent status只投影工作项；Collector保留已确认集合，只重试上次成功flush之后。
- 源码/材料入口：`sources/braid/src/cli/mod.rs；tasks/braid-github-minimal-review/cells/iteration10-tools.md（Collector源入口）`。
- 证据与当前验证限制：[工具核对](../braid-github-minimal-review/cells/iteration10-tools.md)，当前源码已修；SDK回执≠逐条持久化保证。

## 原账本之外的已应用改动

| ID | 表现/依据 | 问题定位或选择性质 | 已应用修复与源码入口 | 必须核查的边界 |
| --- | --- | --- | --- | --- |
| A01 | Pi先settled但后台有限检查未完成 | 原生pending-work/完成消息时序，尚未新运行验证 | harness/npm/patches/pi-background-bash-1.0.5.patch；依赖锁；Mac/Linux构建接线；native-idle-spike.md | 由原生扩展管理，不让Braid管理内部job；service显式排除；等待/退出是否反而增加卡死 |
| A02 | 改派、带assignee创建PR、重开后无首条工作输入 | Assign物化与Wake缺口 | sources/braid/src/objects.rs、store/mod.rs、group/dispatch.rs；iteration10-lifecycle.md | 同事务首条工作输入；旧执行退出顺序；不替Agent发明业务工作 |
| A03 | 监控错选旧/后续共享工作区证据，fresh漏native | 来源与执行时间边界错误 | tasks/iteration10/scripts/monitor-generation.py；monitor.md | 不能把历史错误当本次故障，不自动用参赛额度/换模型/取消 |
| A04 | vision没有按图片类型/用途组织提取 | 用户批准的角色方法增强，不等于已证全部读图失败根因 | 两个活动variant五份agents/vision.md | 独立只读原生角色、fresh；事实/推断/未知分开，无业务判据注入 |
| A05 | 用户要求删除全部Braid测试 | 明确范围决策，不包装成运行得分根因 | sources/braid/src测试模块、tests、scripts/tests已删除，CI/AGENTS/维护入口清理 | 不把产品代码误删；历史记录保留；禁止重建/运行测试 |
| A06 | 用户要求pnpm/portless/Vitest/组件库/图标/UnoCSS及共用工程指引 | 技术选择与工作方法默认值，不是已证全部环境/完成度根因 | variants/*/run.py；harness/npm/package*.json；submission/build.py；scripts/runtime.py；toolchain-proposal.md | 不指定TS/Vue、不加两题专属建议、不预写应用；平台Node20/npm入口兼容，工具Node24独立 |
| A07 | 浏览器/依赖重复取得与路径猜测 | 预打包环境接线和使用提示 | run.py缓存/工具路径环境；submission/Dockerfile、build.py；docs/deployment/index.md | 包缓存按运行复用、不强制离线、不污染初始数据；实际制品尚未更新 |
| A08 | 安装仍运行就测试，同目录install/rebuild重叠；reset与观察并行 | 依赖顺序违反，预打包不独自解决 | svc-implementation/references/workflow.md | LLM控制工作顺序，避免新增语义调度器；不能用禁止一切并行代替 |
| A09 | 格式过滤无匹配被当无评论，管道掩盖首错 | 观察结果被投影丢失/误读 | svc-investigation/references/debugging.md | 要保留原动作状态，不能靠额外大日志淹没上下文；CLI接口本身是否仍有歧义 |
| A10 | 同名/tmp正文污染、全局close/pkill影响其它成员 | 共享环境资源所有权；部分损害仅相关性 | svc-implementation/workflow.md；agent-browser/SKILL.md named close | 不新增用户否决的沙箱；声明不应代替本可由工具消除的缺陷 |
| A11 | queued后没匹配预想输出而继续写出重复评论 | 把已受理消息当失败；未证失效错误撒谎 | svc-implementation/workflow.md 先读回再重试 | 无自动语义去重；同时检查Braid写入回执是否足够明确，不只教育LLM |
| A12 | HyperFormula getCellValue示例instanceof CellError失败 | 输入示例与公开返回类型不同 | harness/skills/hyperformula/references/error-handling.md改DetailedCellError | 对照官方3.4.0 src/CellValue.ts/index.ts；自定义函数仍CellError；非最终失分归因 |

## 证据入口

- tasks/iteration10/run-audit/github/report.md、coverage.md、evidence/：GitHub完整原生决策/控制流审查，保留省略与缺失。
- tasks/iteration10/run-audit/sheet/report.md、coverage.md、cells/：Sheet仍在追加，完成度以覆盖账本为准，不能把当前局部归因当全审。
- tasks/iteration10/instruction-audit/：实际装配输入审计。
- tasks/factory-subagents/cells/iteration10-role-audit.md：原生角色使用审计。
- tasks/braid-github-minimal-review/cells/iteration10-lifecycle.md、iteration10-tools.md、svc-cli-integration.md：源码与历史核实。
- tasks/iteration10/implementation.md、closure.md、review.md、build.md：实现过程和制品边界；旧时态可能落后，审查不得默认为现状。

代码定位按名字而非稳定行号提供；source-snapshot.json记录开始复审时的内容摘要，变化须回报，不能将不同版本结果混用。

## 最后复审增量

- Z01：F1同home resume索引覆写 → 当前父身份/schema核对后加载原清单，复用merge继续记录；两variant observer已改，真实采用未验。检查错误处理是否反而阻断正常生命周期。
- Z02：F2关闭后无法转送 → 明确产品能力为持久索引/恢复重读＋存活期间通知，不自动接管历史工作或保活。检查是否满足原问题，若只是削弱承诺而遗漏必要能力请指出。
- Z03：Sheet内联Markdown被shell展开毁正文 → BodyArgs两字段补已有文件/stdin用法帮助；不改执行语义。
- Sheet最终审查report/coverage均已完成：263可得会话。新增pivot写入→跨表缓存/CSV不同源是静态推导，不修冻结应用、不加题目提示。检验R06等通用改动是否真正针对原因，勿以方法已写视为收益已证。
