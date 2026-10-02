# GitHub lineage：Braid 内容投影与操作语义

只读增量，2026-09-30。跟踪同一 GitHub 工作流从 09-29 04:24 开始到 I11 接续的内容边界；迭代名称不当作行为模式。未运行 Braid、编译、测试或模型。下述“来源行”均指保存的原文；新提取文件的原归档成员、hash 在相邻 extraction.json。外部 GitHub 应用自己的 Issue/PR 功能不属于这里的 Braid 协作对象。

**关键结论：从最早会话起已存在明确内容规则，不能将问题归为“完全没有方法”。可确认的缺口是规则与实际读取/折叠单元不完全对齐；尚不能证明 description 长度导致低分。**

## 语义、版本与运行证据

| 内容维度 | 最早及旧投影 | 后续实际材料/冻结实现 | 证据边界 |
|---|---|---|---|
| 内容归属 | 04:24 根指令已要求 description 保存当前任务与稳定决定；comment 放讨论/证据/增量，相关回复接 thread；更正先联系受影响者；hide 失效整条；resolve 前保存结论/证据入口，未决/风险/验收前提保持可见 | 16:30:36 创建成功的 Issue #10 会话仍保留该规则，并加“先读本条，必要时展开 thread” | [早期指令](evidence/earliest-root-instructions.md:3)、[后期指令](evidence/01a0ee00-f654-7ce3-8d32-7e427b9a30c9-instructions.md:3)；session.json 证实 native 身份，指令存在不等于每条规则均被执行 |
| Issue 分层 | 根初始 context 明确“父 Issue 正文不会自动成为子项上下文”，要求子项自包含需求/场景入口、结果、前置状态、共享决定和依赖 | 冻结 renderer 的普通 Issue 注入自身标题/状态/负责人、parent/sub-issue/PR 引用、自身 description 与当前可见评论；父项、子项与关联 PR 不递归展开 | [初始需求](evidence/earliest-root-context.md:14)、[冻结 renderer](evidence/frozen-src-context.rs.txt:382)；因此关系链接本身不能承担完整交接 |
| PR 背景 | 04:32:05 PR #2 实际 context 先放关联 Issue #1，再放自身 PR；旧 renderer 对关联 Issue 调用完整 render_issue，包括其讨论 | 后续先放 PR 自身 description/讨论；关联编号仍全列，只展开 OPEN Issue 的 description，**不带其讨论** | [早期 PR 投影](evidence/earliest-pr2-context.md:1)、[旧源码快照](../context-templates/evidence/context-renderer.rs.txt:289)、[冻结 renderer](evidence/frozen-src-context.rs.txt:407)。09-30 PR22 失败启动的 context 171行起也符合新投影，但该次无 native 身份，不能据此算消费成功 |
| 自动注入与按需读取 | 新评论产生更新引用，不自动要求每次全板刷新；旧事件模板末尾却要求 `view --comments` | 新模板只给精确评论入口；20%模型窗口内依次选 full→评论标题索引→截短 description/关系引用，CLI 无窗口参数仍完整读取 | [旧模板](../context-templates/evidence/instructions-events.rs.txt:116)、[新事件模板](evidence/frozen-src-group-provider.rs.txt:94)、[预算](evidence/frozen-src-context.rs.txt:243)。预算是粗估 ASCII/非ASCII，不是 tokenizer；只管工作项投影，不含固定指令/后续会话。没有运行降档触发证据 |
| 关系与通知 | parent 是层级引用；PR link/--issue 是背景关联，不是自动完成声明 | 指派者、thread参与者及显式关注者接收评论；@定向联系；Issue description 更新及评论 edit/hide/resolve 会使关联 PR 上下文失效。新评论通常为 wake，只给来源引用 | [指令](evidence/earliest-root-instructions.md:3)、[变更传播](evidence/frozen-src-objects.rs.txt:665)、[评论传播](evidence/frozen-src-objects.rs.txt:1014)。关联不是消费者已采用的证明；关闭意图还须正文 Closes 等且合入默认分支 |

冻结源码来自 `runs/iteration11/20260930-completed-turn-resume/build/braid-source.tar.gz`，SHA256 `fa7e91…675fc28`；build identity 对应旧启动 binary `3056fe…05bf4`。之后实际成功启动 binary `d76d65…83be` 的保存 patch 只改启动 timeout/诊断，并未改这些内容投影文件：来源为 `runs/iteration11/runtime-stalls/build/{build-identity.json,startup.patch}`。本报告不拿当前 `sources/braid` 代替历史；当前源码已经有新的 resolve 回执结构，不能倒填为当时已提供。

## hide/resolve 的真实边界与一次可观察误用

- **hide** 只改指定评论可见性，保存正文/理由；不自动隐藏其可见后续回复。**delete** 清空正文不可恢复。二者均不同于关闭工作项。[冻结 objects 1090–1151](evidence/frozen-src-objects.rs.txt:1090)
- **resolve 任意回复 ID** 先找到 `thread_root`，将该 thread 当时的最大 comment ID 写成 `resolved_through`；折叠整条历史前缀，不是只折叠该回复，也不是只折叠其后代。新回复高于 cutoff 仍可见；unresolve 清空整个 thread cutoff。[1154–1194](evidence/frozen-src-objects.rs.txt:1154)
- 普通投影对 resolved 历史只留根身份；直接 `comment view ID` 展开该条仍可见的 resolved 正文；`--thread` 默认仍折叠；`--include-hidden` 可展开 hidden/resolved，deleted 无法恢复。[renderer 443](evidence/frozen-src-context.rs.txt:443)、[读取 1230、1279](evidence/frozen-src-objects.rs.txt:1230)
- edit/hide/resolve 影响后续重建，不会撤销在途 Agent 已读内容；重建提醒要求本轮结束前保存进展。因此不能把 hide 当成已向所有消费者撤回决定。[reset消息](evidence/frozen-src-group-provider.rs.txt:108)

实际轨迹见 [#324–327 原始数据库摘录](evidence/comments-324-327.json)：16:29:16，Issue10 #324 宣布按惯例 `resolve 318`，以为仅闭环 #318→#322 转呈；16:29:41 #325 发现连同 #308/#313/#317 等仍使用的决定被折叠，执行 unresolve，却又误称留下几条局部折叠；16:31:48 根 #326 逐条查状态纠正“实际全部可见”；16:32:13 #327 回读 thread 结构，承认无法单独折叠此组回执、保持全可见并窄改正文。这是**语义误解→有效共同复核→安全恢复**，无证据显示它造成产品缺失或最终评分损失。

当时 CLI `resolve` 帮助只写“评论 ID；可一次提供多个”，未解释整 thread cutoff；操作返回 `Result<()>`，没有 root/cutoff/影响数量回执。[旧CLI](evidence/frozen-src-cli-mod.rs.txt:438)、[旧对象函数](evidence/frozen-src-objects.rs.txt:1157)。指令虽教“相关回复留同thread”，却没教如何分开有独立闭环条件的议题；不同裁决、转呈和验收义务绑到一棵树，会使安全局部收束困难。此解释由结构和自述支持，不是长度推断。

## 候选与不可归因项

现有机制可由提示/Skill改善：按**独立待决问题与关闭条件**建立 thread；description 保留当前目标/范围、当前决定与权威入口、仍未决的责任和验收门，评论保留差异/证据；稳定共同定义上移项目文档，消费者确认采用或明确阻塞；跨 Issue 排除范围须点名接手项/负责人并取得承接。resolve 前按真实 root/cutoff 核对整串是否都可结束；仍使用的结论先保存入口，但不能以“有文档”替代消费证据。历史运行已教其中不少原则，应补案例和决策条件，勿再堆一份泛化长提示。

若要求工具**保证**不会误折叠混合未决 thread，或提供局部子树 resolve，则必须改运行语义；前者可考虑操作前范围显示及返回 root/cutoff/影响条数，后者是产品行为变更，不能由提示实现。若要求所有工作项默认只注入决策摘要/引用，也需改 renderer；现有 full 档仍会注入本项全部可见讨论。不能将硬截短视作语义整理，更不能保证预算低于阈值就不会误判。

未证：长 description 导致失误；全部历史都被注入每次模型请求；20%降档实际触发；hide 后仍未纠正的损害；新运行规则普遍改善评分。范围控制和错误结论仍需主线正向决策链证据；这里仅确定自动内容边界、真实操作单元、已存在方法与可观察纠错。
