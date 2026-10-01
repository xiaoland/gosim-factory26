# 需求树协作规划：Braid 上下文与生命周期边界复核

日期：2026-09-30。范围：独立核实需求树映射方案可以依赖的 Braid 原生能力，给出协议约束；不重做 GitHub / Sheet 全量 lineage，不实施方案，不操作工作项，不运行测试、模型或评测。本文是规划依据，不是新增运行契约。

**设计结论：需求树可以成为分配、继承约束和验收追溯的来源，但 Braid 的树边与 PR 关联不会自动实现这些语义。当前最小方案应使用既有 description / comment / subscribe / 明确交接，保留唯一原需求入口；不能把“父子引用、已关联、已送达、ready、merged、closed”提升成需求已继承、责任已承接或验收已完成。**

## 1. 来源与版本边界

- 优先消费既有 [runtime-semantics.md](../braid-context-methodology/runtime-semantics.md)、[content-evidence.md](../braid-context-methodology/content-evidence.md)、[research.md](../braid-context-methodology/research.md)。它们已经区分最早原生输入、I11 冻结实现和当前源码；本分线只定向补核接口。
- 历史源码引用均来自既有 `evidence/frozen-src-*.txt`。来源归档是 `runs/iteration11/20260930-completed-turn-resume/build/braid-source.tar.gz`；版本身份及后续 startup-only patch 的边界见 [历史语义报告](../braid-context-methodology/runtime-semantics.md)。冻结源码证明当时实现边界，不能单独证明某个 Agent 实际读取或消费。
- 当前源码是 `sources/braid` 的**有未提交修改工作区**，基准 HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`。没有把 HEAD 当作当前文件内容，也没有把当前能力倒填进 I11。定向读取时 SHA256：`src/context.rs` = `7d092b54855be71bbd7780a82e93b3e54bb63b7f362ed76e394aa7ffadc0db15`；`src/objects.rs` = `773bcb68ec5ba2a4e68c63a451f07550cf10508a437cb700299642813cfb676c`；`src/group/provider.rs` = `95e905c0ec718e3056f93442d2bc7153756882c2aa68e169eafc01231e56a424`；`src/cli/mod.rs` = `0c3f1e75cbef4dafdc79c223473830eec42381bdb6c68ee7bc39aa85bc187ac9`。后续接续应先核对是否改变。
- 已读 [Braid AGENTS](../../../sources/braid/AGENTS.md)。仓库根未发现 `AGENTS.local.md` 或 `.agents/`。未修改 Braid 文档或其它研究报告。

## 2. 历史已证与当前源码边界

| 能力 | 历史 I11 可确认内容 | 当前源码核实 | 对需求树规划的约束 |
| --- | --- | --- | --- |
| description / comment 职责 | 最早指令已有“description 当前说明与稳定决定，comment 讨论、证据、增量；未决和验收前提保持可见”。不是完全没有方法 | [provider:60](../../../sources/braid/src/group/provider.rs:60) 保留规则，并新增已完成项保留自身交付、集成状态由整合任务维护 | 优先补充决策条件与具体示例；不要再发一份同义长规则。原要求仍是权威，Issue 是当前任务的分配与解释，不能默默覆盖原文 |
| 子 Issue 上下文 | 实际初始要求已提醒父正文不自动成为子项上下文；[冻结 context:382](../braid-context-methodology/evidence/frozen-src-context.rs.txt:382) 只展开本项正文/讨论 | [context:382](../../../sources/braid/src/context.rs:382) 本项显示 parent、sub-issues、PR 引用，关联对象不递归展开 | 每个实施单元需要列明适用父约束的原节点入口及当前有效解释；不能只写 `parent=#X`。父层旅程的整体验收应另有明确责任 |
| PR 背景 | 早期 PR2 投影曾包含关联 Issue 的讨论；后续冻结 renderer 已改为 PR 自身先呈现，只展开 OPEN 的直接关联 Issue description | [context:407](../../../sources/braid/src/context.rs:407) 同样只对 OPEN Issue 调 `render_issue_at(..., associated=true)`；该模式不呈现其父子引用和评论 | PR 只关联叶子/子 Issue 时，看不到祖先正文、祖先关系或该 Issue 的裁决讨论。稳定决定若只在 Issue comment 中，PR 必须按需读取或从当前 Issue description 找到精确入口 |
| 已关闭关联 Issue | [冻结 context:435](../braid-context-methodology/evidence/frozen-src-context.rs.txt:435) 过滤非 OPEN Issue，仅保留关联编号 | 当前同样过滤。关闭不抹去存储；仍可 `issue view ID` 读取 | 已关闭共享契约不能依赖下一次 PR 物化自动展开。不要为了可见性让完成项无限保持 OPEN；应保存明确合同入口和版本并要求消费时读取 |
| 父子关系 | 关系是层级引用；没有自动分解、审批或父子完结联动 | [objects:913](../../../sources/braid/src/objects.rs:913) 拒绝不存在的父项/环；[lifecycle:1810](../../../sources/braid/src/objects.rs:1810) 相关对象在下次合法 dispatch 才显露新状态；[local:81](../../../sources/braid/docs/20-product-tdd/local.md:81) 明说子 close 不唤醒父 | “子项全部 CLOSED”不是上层约束合格的判断，也不是已向父项交回结果。父项需约定交回位置和自身验收责任 |
| Issue–PR 关联 | N:M 背景关联；`--issue` / `pr link` 不建立自动关闭承诺 | [objects:1659](../../../sources/braid/src/objects.rs:1659) 改关联会使 PR 上下文失效；没有 typed `implements` / `depends_on` / `accepts` 等关系字段 | 可以一个 PR 关联多个 Issue，或一个 Issue 关联多个 PR；需求追溯/消费依赖/关闭意图须分开表述，不能把所有跨分支关系塞进 `parent` |
| 关注与定向联系 | [冻结 objects:248](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:248) 已有显式订阅；[冻结 objects:918](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:918) 评论按讨论规则通知 | [objects:1033](../../../sources/braid/src/objects.rs:1033) 收件人为本项负责人、未退出的同 thread 历史参与者、显式关注者，再加有效 `@成员`；跳过作者 | 链接、父子关系和创建对象都不是自动订阅。可用既有 `issue/pr subscribe ID`，不需设计伪 `follow` 命令；但按需订阅，避免所有成员关注所有项 |
| 跨对象回复 | [冻结 objects:928](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:928) 明确拒绝 reply 归属其它工作项 | [objects:949](../../../sources/braid/src/objects.rs:949) 仍要求 `--reply-to` 指向命令目标工作项内的评论 | PR 负责人可以**到 Issue 上**回复该 Issue 的交接 thread；不能在 PR comment 里用 Issue comment ID 建跨对象回复树。另一个对象只保留回链和本项义务 |
| 投递与理解 | 既有历史报告明确关联/投递不等于消费 | [objects:988](../../../sources/braid/src/objects.rs:988) 记录 queued / unreachable 等；原生接受输入后才能记 delivered，见 [local:97](../../../sources/braid/docs/20-product-tdd/local.md:97) | delivered 只证明送交原生会话；承接应由对应回应或实际正确行动证明，不要求每个无关通知多一轮 ACK。旧成员改派后不会自动转投新负责人 |
| ready / merge 返回 | 冻结 [objects:1691](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:1691) 的 ready 只通知 PR 显式 followers 与本项，不由关联表广播 | [objects:1731](../../../sources/braid/src/objects.rs:1731) 只在 draft 状态变化时发 ready 事件；[objects:2053](../../../sources/braid/src/objects.rs:2053) merge 向关联 Issue 写 activity，不直接唤醒所有 Issue 负责人 | ready / merged 是候选/代码状态，不能替代“交回 Issue 的证据与剩余项”。可由消费者显式订阅获得状态信号，但证据和承接内容仍需明确 |
| close / Closes | 关联与正文关闭关键字分离；默认分支合并才处理关闭关键字 | [objects:1836](../../../sources/braid/src/objects.rs:1836) 解析关闭对象并关闭，不检查该 Issue 原需求覆盖或评论待决事实；CLI 也没有 `pr review` 状态机 | 审阅意见以现有 comment 表达；“批准/需修改”须带 head、范围和证据。不得写不存在的 `braid pr review --approve`。父项若仍有集成验收，不让局部 PR 的 `Closes` 提前结束它 |

### 当前文档漂移：不能当作能力承诺

1. [local.md:87](../../../sources/braid/docs/20-product-tdd/local.md:87) 仍称关闭关联 Issue 展开正文及讨论，与该文件之外的 [context.md:3](../../../sources/braid/docs/20-product-tdd/context.md:3)、冻结/当前 renderer 冲突。本文采用源码所示 **仅 OPEN description**，不修改原文。
2. [local.md:109](../../../sources/braid/docs/20-product-tdd/local.md:109) 称 ready “通知关联 Issue”，但冻结/当前 `ready_with_undo` 与 `notify_followers` 没有关联广播；当前 PR 默认非 draft，重复 ready 还可能没有状态变化事件。本文不把这句当作自动交回保证。

这两点是定向静态核实结果，不证明某次实际运行因此失分；应在后续实现准备时对齐文档与预期接口，不能靠规划里的假设消除差异。

### `close --comment` 与最终关闭的派发边界（主规划复核补证）

- **真实 CLI：** `braid issue close ID --reason completed --comment TEXT` 的参数和帮助注释在 [cli:258](../../../sources/braid/src/cli/mod.rs:258)，分派到 `lifecycle_with_comment` 在 [cli:1020](../../../sources/braid/src/cli/mod.rs:1020)。PR 的 `close ID --comment TEXT` 在 [cli:396](../../../sources/braid/src/cli/mod.rs:396)，调用在 [cli:1101](../../../sources/braid/src/cli/mod.rs:1101)。这里 `--comment` 是文本参数，不是 `--body-file`；merge 没有这个参数，不能写成 `pr merge --comment`。
- **原子保存的精确范围：** [objects:1773](../../../sources/braid/src/objects.rs:1773) 开 SQLite immediate transaction；[1782](../../../sources/braid/src/objects.rs:1782) 用同一 `tx` 写解释评论及其通知，随后 `transition_in` 写状态/事件，至 [1811](../../../sources/braid/src/objects.rs:1811) 一并 commit。这保证评论和本次状态变化在数据库中同成同败，不保证跨 Git/文件证据原子性，也不保证接收者已消费。已经是目标状态时 [1778](../../../sources/braid/src/objects.rs:1778) 返回 unchanged，**不会再发评论**；MERGED PR 在 [1776](../../../sources/braid/src/objects.rs:1776) 拒绝 close/reopen。历史冻结 [objects:1728](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:1728) 已有相同事务模式，非本轮新设计。
- **关闭不赠送收尾轮次：** [store:3582](../../../sources/braid/src/store/mod.rs:3582) 对负责人自己 close 消费事件、保留当前执行及已有输入，不新增 turn；外部 close 在 [3591](../../../sources/braid/src/store/mod.rs:3591) 走普通输入/恢复地址，不建立新的 finalization 阶段。合同对应 [lifecycle:15](../../../sources/braid/docs/20-product-tdd/lifecycle.md:15)。结果应在当前获授权执行中保存，不能依赖关闭后还有一次专门执行。
- **全体最终关闭后不派发普通讨论：** [store:5394](../../../sources/braid/src/store/mod.rs:5394) 的判断是根 Issue CLOSED、全部工作项 CLOSED/MERGED、无 prepared 合并及仍开放 PR 的冲突；[claim_runnable_turn:5433](../../../sources/braid/src/store/mod.rs:5433) 此时仅允许已经应用的 reset continuation 例外。[claim_running_input:5807](../../../sources/braid/src/store/mod.rs:5807) 也不再领取普通输入，[begin_agent_assignment:4093](../../../sources/braid/src/store/mod.rs:4093) 不再新物化普通成员。待已接受执行/重建续接收敛后，[local:537](../../../sources/braid/src/local.rs:537) 返回 quiescent；`execution_settled` 的条件在 [local:261](../../../sources/braid/src/local.rs:261)，并不以所有 queued comment 已消费为条件。
- **协议后果：** 需另一成员处理的结果/问题应在最后终态前交回并安置，不能仅靠 close 后发评论期待对方再工作。`close --comment` 适合同时保存本项解释；它在**本项**建立新评论，不自动变成父 Issue 的交回，也不能保障“最后一次关闭”的通知随后得到处理。需要回到父项 thread 的语义结果仍先在该 thread 交回，最后关闭前核无待处理交接。

本次补核新增读取文件 SHA256：`src/local.rs` = `55b475210a22f9b543a332a85c09c94cb9e10f9bb37d08f60a1590579f0f4cfa`；`src/store/mod.rs` = `67118e34cde7912810b7f3bf9c2b5cc48d46fa7d9aed73ef5315c7b9e0125a49`。这是当前有未提交修改的源码边界，没有操作任何 Braid 工作项或执行运行验证。

## 3. 变更传播与未决事实保护

### 3.1 传播矩阵

| 动作 | 自动作用 | 不自动完成的责任 |
| --- | --- | --- |
| 新增 comment | 按负责人、同 thread 参与者、显式订阅和当次 `@` 发引用；作者不自唤醒 | 不因 parent / PR link 广播；不自动更新对方 description；不等于采用新决定 |
| 修改 Issue 标题/description | 本项 Invalidate；所有直接关联 PR 跨面 Invalidate；显式 followers 另得更新引用 | 不递归更新子 Issue/祖先/任意文本中的依赖者；不保证在途 Agent 撤回已采用旧判断 |
| 编辑可见 comment / hide / resolve | 本项 Invalidate；若是 Issue，则直接关联 PR 也 Invalidate | hide / resolve 本身不向每个跨项历史参与者发新的语义更正；没有“所有下游已更新”的完成门 |
| 改 Issue parent | 更新关系/活动，对被改子项发 Wake | 不把父需求复制进子项；不建立消费依赖或跨层验收 |
| close / reopen | 更新本项状态及相关订阅信号，关系状态可在后续读取看到 | 不自动唤醒父成员或普通关联消费者；不传播语义证据失效 |
| 更新共享 Git 文档 | 只改变所在 clone / 发布后的 Git commit | 其它 clone 不自动采用；要明确发布 commit、路径和受影响者，消费者 fetch 后读取指定版本 |

主要实现入口：[changed](../../../sources/braid/src/objects.rs:694)、[description edit](../../../sources/braid/src/objects.rs:860)、[discussion_changed](../../../sources/braid/src/objects.rs:1033)、[parent edit](../../../sources/braid/src/objects.rs:842)、[lifecycle](../../../sources/braid/src/objects.rs:1760)、[Git 使用约定](../../../sources/braid/src/group/provider.rs:60)。历史冻结实现中的前四项对应关系见 [runtime-semantics](../braid-context-methodology/runtime-semantics.md)。

**容易遗漏的代价：** PR 不注入关联 Issue 的评论，但编辑/隐藏/折叠那些评论仍可能触发关联 PR reset。把每个 PR 都关联一个经常整理讨论的全局“合同 Issue”，可能扩大重建范围；现有实现不按“该评论是否实际进入该 PR 投影”过滤这次跨面事件。是否造成无效重建须查事件与实际会话，不能从关联数推定损失。规划应测量这一项，先使用范围合适的合同入口与较少的语义更新；不要把所有共享决定集中到一个高频变化的巨大工作项。

### 3.2 hide / resolve 的真实粒度

- `hide ID` 隐藏**指定单条**评论，保留正文、身份与理由；不自动隐藏后续回复。`delete` 清空正文不可恢复，不是整理历史的默认选择。
- `resolve ID` 通过任意评论 ID 找到 thread root，把该 thread 当时的最大 comment ID 作为 cutoff；折叠整串历史前缀，**不是只折叠该回复或其后代**。新回复高于 cutoff 仍可见；`unresolve` 清空整串 cutoff，不是只恢复单条。
- 普通投影对已解决历史只留根标记；`comment view ID` 可直接读该条仍 visible 的已折叠正文；`comment view ID --thread` 默认仍折叠历史；`--include-hidden` 可展开 hidden / resolved，不能恢复 deleted。证据：[冻结 objects:1154](../braid-context-methodology/evidence/frozen-src-objects.rs.txt:1154)、[当前 objects:1182](../../../sources/braid/src/objects.rs:1182)、[当前读取:1275](../../../sources/braid/src/objects.rs:1275)。
- I11 曾发生 `resolve 318` 连带折叠同 thread 的长期裁决，随后 unresolve 并读回纠正，见 [已有正向案例](../braid-context-methodology/content-evidence.md)。这证明议题/关闭条件和 thread 单元需匹配；没有证据证明此短暂误折叠造成产品缺失。
- **当前已改善：** CLI 帮助明确整条讨论，回执提供 root / cutoff / affected count / changed，[CLI:438](../../../sources/braid/src/cli/mod.rs:438)、[objects:1231](../../../sources/braid/src/objects.rs:1231)。I11 当时没有这些回执。仍无语义校验来保证 thread 内所有未决义务已安置。

候选规则：一个 thread 围绕一个可独立结束的待决问题；长期合同的决定 thread 与短期“已发布/已读/请刷新”回执分开。resolve 前看整串，确认仍使用的决定、例外、未决责任、验收前提在当前入口可取。不同议题已混在同串时，可保留可见，不为减少长度强行折叠；仅隐藏明确失效的单条并留替代入口。任何会纠正消费者的内容，先发具体变更，再处理旧内容可见性。

### 3.3 自动投影预算不是语义保全

[当前 context:243](../../../sources/braid/src/context.rs:243) 与冻结语义都按完整内容 → 评论索引 → 引用/截短正文降档，以粗估 token 严格低于模型窗口 20% 及 byte 上限为条件。引用档从前缀截取本项 description，PR 的关联 Issue description 使用更短前缀；最低档可以只剩工作项读取入口。[截短实现](../../../sources/braid/src/context.rs:320)

因此“把父层约束写入 description”提高默认可得性，但**不是所有档位必见的硬保证**。协议至少要要求实施/审阅前按原节点入口读取适用约束；静态核对应检查完整、索引、引用三种可见边界，而非只看存储正文。没有本次证据证明 I11 实际触发降档，也不能把 20% 当作低于阈值就不会误解的保证。

## 4. 最小可执行内容协议候选

以下都能用既有正文、评论与文件引用表达；字段名是建议写法，不是假称 Braid 已有 schema。只保留一套原需求权威，不把各 Issue 的解释复制成新需求全集。

| 位置 | 当前应保留 | 不应承担 |
| --- | --- | --- |
| 原 requirements 树 | 原节点身份、文本、祖先路径和原始版本；保留父层否定/唯一性/权限例外 | 不直接等同所有节点都分配 Agent 或独立 PR |
| Issue description | 分配的原节点入口；适用祖先约束/共享合同的精确入口与版本；可判定结果；未决问题/责任；依赖输出与满足条件；验收边界 | 不复制全板进度或其它已完成项的动态 head；不把局部排除写成无人承接的“out of scope” |
| Issue comment | 一次提案、裁定、更正、交接请求/回应或证据；声明替代何项、影响谁、是否改变验收结论 | 不把评论中的重要现行裁决仅留在 PR 永远不读的关联讨论里；不把发出 @ 当作完成转交 |
| PR description | 实际候选 head；关联需求/合同版本；实现范围与变化；验收行为/原始证据入口；未完成项与承接者；合入目标 | 不把 `ready`、本地编译或自写验收通过直接等同父层端到端要求成立 |
| PR 审阅 comment | 审阅针对的 head 和需求范围；结论、发现、需要补的证据；每项问题的处理/保留决定 | 不使用不存在的 `pr review` 命令，不把审阅者读同一解释当作独立原要求核查 |
| 稳定共享文档 | 已采纳且需跨分支复用的领域定义/接口/权限合同，来源与适用版本 | 不保存整板动态状态；文件更新不等于各 clone 已采用 |
| 父/整合 Issue | 原上层约束的整体验收责任；子项交回结果与仍待整合义务的入口 | 不要求每一层做同样验收，也不靠子 close 数量推导覆盖率 |

**交接示例仅表示命令形态，不创建真实对象：** PR 负责人要交回 Issue 12 的 thread 40，应调用 `braid issue comment 12 --reply-to 40 --body-file result.md`；不能调用 `braid pr comment 23 --reply-to 40 ...`，除非 40 本来属于 PR 23。消费者需持续关注 PR 23 时用 `braid pr subscribe 23`；只需一次回答时直接在相应 thread 讨论，不额外订阅全项。关注和 reply 都使用已经核实存在的 CLI。

语义交接只要求覆盖重要边界：排除范围、接口变化、候选交付、前提失效等。接收者给出“接手哪些原节点/父约束、依赖什么、下一步或阻塞”，或已有明确正确行动可作证；没有新事实的 `收到` 不需层层传播。接手被拒或 unreachable 时，责任仍留在转交方/原协调项，不能从两边 description 同时删除。

**版本与更正：** description/comment 的稳定 ID 不意味着正文不可变；`edit` 覆写当前正文，普通 CLI 没有每个正文版本的检索协议。[覆写入口](../../../sources/braid/src/objects.rs:860) 与 [comment edit](../../../sources/braid/src/objects.rs:1078)。影响范围或验收的更正应先保留原决定身份和变更原因，再更新当前说明；验收证据绑定实际代码 commit、适用原需求/合同版本与运行条件。内部 `context_revision` 是实际投影的哈希，不能替代需求版本或语义采纳证明。代码不变但需求解释改变时，旧证据可能不充分；仅整理不改变语义的说明时，也不应机械要求重做全部验收。

## 5. Skill 可完成与 runtime 才能保证的界线

| 候选目标 | 先用既有机制 / Skill | 若要求强保证，才需要单独设计的 runtime 能力 |
| --- | --- | --- |
| 保留父层约束和原需求追溯 | 每实施单元记录适用祖先入口，开工/审阅读原文；父项保端到端义务；按需读闭合历史 | 自动计算继承约束、在所有投影档强制保留关键字段、验证分配与覆盖完整性 |
| 表达跨分支依赖与承接 | 正文写生产者、消费者、输出版本、满足条件；现有 @ / thread / subscribe；有条件的接手回应 | typed dependency / request-acceptance 状态、自动受影响者传播、改派后责任转投等硬约束 |
| 保护未决事实 | 独立 thread、当前未决入口、resolve 前读全串、保留混合 thread | 按子树 resolve、阻止折叠未决语义、原子迁移义务；当前 root/cutoff 回执已存在，不应重复列成未实现 |
| 控制无新事实唤醒 | 少发空 ACK、不广播全项；修改真实语义时才更正正文；父/PR 显式交回必要结果 | 改变关联 Issue 评论编辑/resolve 的跨面失效边界、语义去重、自动判断消息无新事实 |
| PR/父项验收关闭门 | comment 写范围/head/证据；Issue 负责人复查上层约束；谨慎使用 Closes | 原生 review / approval 模型、关闭前覆盖门、自动失效证据或阻止陈旧批准合并 |
| 覆盖追溯的机械核查 | 先规划离线人工回放与结构化清单核对：ID 存在、每项有责任、依赖有输出、证据有版本 | 持续执行的内建覆盖检查、原生 requirements registry 或自动树→Issue 生成器；本轮均未实施 |

现在不需要以 runtime 大改为首步：现有能力足以比较直接树映射和按交付单元组织的**语义完整性**。但不能把 Skill 合规期望写成系统保证，也不能用“关联后系统会通知”“关闭会自动收敛”作验收前提。

建议父规划的回放指标增加：① 当时投影/按需读取是否能取得适用父约束和例外；② 交接请求到承接证据之间的未承接义务；③ PR 审阅证据是否针对正确 head 与需求版本；④ 无内容变化的回执是否引出新工作；⑤ 共享 Issue 编辑造成的实际重建范围，及新会话是否得到新事实；⑥ close/merge 后仍未显式交回的上层验收义务。均需标清分母和缺证项，不把 Issue 数、长度、CLOSED 比例当质量。

## 6. 保留的未决选择与结论限制

- 共享合同究竟放在专门 Issue 还是 Git 文档，应由变更频率、消费范围与责任归属决定；不能仅为了自动注入而让所有 PR 关联全局 root。文件有版本/fetch 成本，Issue 有上下文重建与关闭可见性成本。
- 是让需求树的大分支成为父 Issue，还是只保留原节点映射、按交付单元建立 Issue，仍需用两题真实树的片段比较；此报告只裁定能力边界，不替映射研究作结论。
- 当前 source 的语义不等于本次已实际部署或已完成运行验收。两处文档漂移需要在实施准备时收敛；本轮无授权修改 runtime 或文档。
- 没有运行期对照，因此不能据本复核声称新协议会提高分数、节省多少 token 或杜绝遗漏。无运行的新方案可先被历史回放中的反例否证；若要验证模型采纳和官方分数，仍需另获具体输入、预算、完成条件的实验授权。
