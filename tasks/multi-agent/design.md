# 方案与证据

CLI 与单一配置已经实施。下述方案依据 2026-09-21 用户对拆分、会话树和自主协作的纠正重新整理，已获用户批准并完成本地实现，真实验收进展见 [execution.md](execution.md)；此前的调查子 Issue、派发后强制结束父 turn、按任务结果事件推进协作均已撤回。

## CLI 的熟悉度与实际语义

实施前 [cli/mod.rs](../../sources/braid/src/cli/mod.rs) 的入口为 `braid object --state … --writer-turn …`，读取使用 read，comment 创建使用 `comment create issue|pr ID`，正文只支持 `--body-file`，其 `-` 会被当作文件名。Issue/PR edit 只修改正文，没有 gh edit 的 title 等可选项。这些差异是本轮 CLI 调整的原因。

这些调整已实施，当前操作契约归属 [Braid 本地协议](../../sources/braid/docs/20-product-tdd/local.md)：顶层 issue/pr、view --comments、正文/stdin、title edit 和 JSON 输出。writer turn 仍由每轮提供并核验，不以多个 session 共享的可变环境变量替代当前身份。

对齐依据：[gh issue comment](https://cli.github.com/manual/gh_issue_comment)、[gh issue view](https://cli.github.com/manual/gh_issue_view)、[gh pr create](https://cli.github.com/manual/gh_pr_create)。重新核对本地产品后，移除 pr ensure 强制依赖请求 comment 的约束，改为 pr create --issue ID --title TITLE --body/--body-file …，直接创建本地实施工作项并激活 PR Agent；无需 GitHub 发布或预先存在的实施分支。可选 --request-id 同键返回已有 PR，不更新内容、关系或重复激活；无键每次新建。该本地激活语义在 help 和运行协议中明确说明。保留按稳定 comment ID hide/unhide/delete 和 Context 查询，不以“最后一条 comment”推断多 Agent 写入目标。父子 Issue 关联和委派仍属后续方案。

## 产品边界：语义和决策归属

Braid 的核心是 Agent 会话的上下文管理、多 Agent 协作、设计与实现分离。用户进一步明确：任务含义、工作组织和下一步决策的权威属于 LLM；Braid、SVC、Codex/Pi 都是围绕 LLM 的 harness，连接环境并赋予感知和改变环境的能力。LLM 在用户授权和环境约束内判断是否拆分、如何分工、何时交流和采用结果。SVC 提供供 LLM 理解和选用的方法，不能把某一种协作模式固化为 Braid 的必经流程。可靠投递、上下文一致性和写入隔离是设施责任；“调查结束所以进入设计”“子任务返回所以父任务收尾”属于 LLM 的语义判断。

Issue 表达需要独立维护的问题、需求及其讨论；sub-agent 是某个 Agent 安排工作的手段。创建和关联子 Issue 是能力，不是 requirement 的默认转换步骤；调查通常不足以成为独立 Issue。拆分指南可以讨论功能、问题边界等不同选择，不能规定唯一树形分解模式或固定角色流水线。多个 Issue Agent 可以协作，也可以直接与兄弟 Issue、关联 PR 交流，不要求消息或决定逐层通过父 Issue。

用户进一步明确的一般分工是：Issue 负责需求理解、技术方案和最终验收方案，PR 负责实施预演与计划、执行及最终验收。方法依据与 SVC/Braid 归属见 [设计、实施与验收](working-methods.md)。N:M 关联不变，不强制“一次设计后一次实现”。根 Issue description 可以保存 Factory prompt 与 requirements 引用，子 Issue 可以直接内联局部 requirement。

## Braid Agent 与 provider sub-agent

| 层面 | 本轮设计采用的边界 |
| --- | --- |
| Braid multi-agent | Braid 级别的 Agent 围绕 work-item 组织会话上下文，通过 comment 异步交流。Group 是工作项上的逻辑组织，不是全局角色队列；父子 Issue 关系不是执行调用栈。 |
| Provider sub-agent | Codex/Pi 内部由某个 Agent 使用的 explorer、executor、reviewer 等子会话。它们不自动成为 Braid Agent、Issue 或 Group；其内部消息不自动发布为公共 comment。 |

本项目后续使用 multi-agent 专指前者，sub-agent 专指后者。Braid Agent 的持续身份和工作记忆不依赖某个物理 provider session 永不更换；更换物理会话也不等于新建工作项或要求其它 Agent 重新协作。provider 内的会话树仍需核实其能力和生命周期，不能因 Braid 支持多个工作项就声称原生 sub-agent 已接通。

LLM 的推理调用本身不保存应用会话状态；harness 管理 messages/context、执行 tool calls，并将新输入和工具结果提供给后续采样。Turn 不再作为 Braid 的产品语义或协作单位。现有 provider 的 turn/start、turn/completed 及运行中的请求标识是执行协议事实，需要适配、记录和保护旧输入的写入边界，但不能决定任务阶段、交接或完成。新输入可以在适配器可接受的边界进入下一次推理；合并或暂存输入是执行机制，不能据此要求 LLM 先宣告任务阶段结束。

上游术语见 [glossary.md](../../sources/braid/docs/10-prd/glossary.md)，其中 GitHub 操作部分是历史材料；当前本地实现以 [local.md](../../sources/braid/docs/20-product-tdd/local.md) 为准。设计调查时（Braid 基线 `e0c3ca2`）核实：[local.rs](../../sources/braid/src/local.rs) 为 Issue/PR 各启动一个 worker；[group/worker.rs](../../sources/braid/src/group/worker.rs) 每 worker 仅保存一个活动 turn，活动期间不会物化或启动另一个同类 group。这是当时执行串行化的限制，不能转化为“父 Agent 派发后必须结束 turn”的产品要求。

同一个 Braid Agent 可以使用 provider sub-agent、继续工作或等待新的信息；其它 Braid Agent 应能独立运行。资源管理需要支持这种行为，不能要求 Agent 通过人为结束 provider 执行来绕开 worker 瓶颈。工作项关系与 provider sub-agent 树不建立一棵统一的调度或审批树。

当前 [agent_session.rs](../../sources/braid/src/agent_session.rs) 区分异步消息接受和 provider turn terminal，但尚无证据证明两个 backend 的 sub-agent 树已完整接通。后续预演需要核对原生能力及根会话重建/关闭对子会话的影响，优先复用现有能力；本轮不先设计新的通用 sub-agent 调度器。

## 协作机制：comment 消息与 work-item 上下文

用户提出的核心机制是围绕 comment 组织的异步消息系统，加上围绕 work-item 组织的 session context。Comment 既是 Agent 间交流的持久载体，也可以作为当前工作记忆的一部分；description 保存当前理解，metadata 和关联提供对象事实。LLM 通过 Braid CLI 读取、评论、修订和整理这些内容，Braid 负责让所需输入进入相应会话，并使上下文重建真实生效。

消息到达不等于必须回复，不等于产生新任务，也不自动表达阻塞或完成。LLM 根据内容决定是否追问、修改设计、创建 PR 或继续其它工作。hide/delete 改变后续上下文中的可见内容，不能追溯撤销已发生的环境操作。无需把完整私人推理或每次 provider sub-agent 返回写成公共 comment，也不把所有相关 Issue 的全文递归塞入每个会话。

交流的产品行为是 Agent 能在相关对象上提出问题、补充信息、回应和修订理解。Braid 保证对象变化被正确送达、当前上下文一致；Agent 决定内容意味着什么以及下一步做什么。现有对象变化、失效和 provider 终态具有机械用途，保留这些机制不等于新增任务级事件协议。撤回“委派→结束父 turn→结果事件→唤醒父”的固定链路，也不换成“消息”名称保留同一套编排。

一个判别场景：Braid 的 Issue A Agent 使用 provider 内的 explorer，同时通过 Issue B 的 comment 提问；explorer 结果通过 provider 内部机制返回，B 的回应通过 Braid comment 交流进入相关会话。A 对后续工作作出判断，无需创建调查 Issue，也无需报告“调查完成”才能继续。消息如何寻址和进入会话需要在实现预演中核对，不用任务状态分类代替；这只是能力组合的例子，不是规定流程。

## 可回复和可整理的讨论

用户要求 Issue 和 PR 的普通 comment 都支持回复形成 thread，以及 resolve/hide；不沿用 GitHub 仅给 PR review 提供 thread 的限制。这些能力让 LLM 能围绕一个问题持续讨论，并把暂时无须继续占据上下文的讨论收起。

设计调查时的源码现状：[local_comments](../../sources/braid/migrations/0003_local_objects.sql) 只有 visible/hidden/deleted，没有回复关系；[CLI](../../sources/braid/src/cli/mod.rs) 只有 comment edit/hide/unhide/delete。[context.rs](../../sources/braid/src/context.rs) 仍有旧 PR review thread 的 resolved/collapsed 投影，但 [objects.rs](../../sources/braid/src/objects.rs) 本地读取只填充扁平 conversation，review_threads 保持默认空。因此当时尚未支持本地 reply/thread/resolve，不能以旧 renderer 的存在宣称能力已接通。

建议的产品行为是：comment 可针对稳定 ID 回复并保留讨论关系；resolve 表达 LLM 对该段讨论暂告结束的判断，并可在默认上下文中折叠已解决讨论；hide 控制单条内容是否参与默认上下文，不等于解决问题。折叠保留可定位的身份和状态，允许显式回看和恢复。LLM 按需要把仍有效的结论、约束或证据引用整理到 description 或共享材料；harness 不自动总结和采纳意见。

hide 应允许附加理由，并在正文隐藏后的简短元数据中保留该理由。例如“结论已并入 description”或“已被后续实验推翻”能帮助新会话理解为何不再携带原文，判断是否需要回看。理由由 LLM 提供，harness 不猜测，也不强制每次填写。当时本地 objects.rs 把 minimized_reason 固定为 hidden，CLI 没有理由输入，虽然 renderer 可以呈现理由，仍不能算完整支持。

resolve、hide 不构成产品验收，也不自动令 Issue completed、PR ready 或 merge。已 resolved 的讨论收到新回复时，建议仍正常投递新内容并提供原讨论入口，是否重新打开由 LLM 判断，避免沿用“resolved 全文省略”而吞掉新信息。该行为已通过复核并实现；CLI 与数据模型以 Braid 本地协议为准。

用户另提出 reaction 可用于轻消息/轻通知。将其作为候选协作能力：Agent 可针对 comment 添加或撤回 reaction，相关会话能知道谁对哪条消息表达了什么，无需把简短回应都写成新 comment。具体含义由 LLM 结合语境解释，不预设 emoji 对应审批或任务阶段，也不把 reaction 数量作为验收证据。现有源码仍有历史 turn 状态 reaction 出站逻辑，但本地 emit 的 reaction_target 为空，comment 投影和 CLI 均无 Agent 可用的 reaction 能力；不能照搬该旧机制来代替新的产品行为。

## SVC、材料与诊断

SVC `sub-agents/index.md` 的 Primary/Child 是一次会话内委派的责任边界，不能直接套成父子 Issue 的强制管理关系。`task-packet/index.md` 明确 packet 保存任务局部信息，不拥有 runtime 工作图。材料用于减少重复传递、保留共同理解；按实际需要共享和拆分，不强制每个 Issue 一个 packet，也不先建立发布/采用协议。

Braid 与 SVC 不直接依赖。Factory 负责让 Agent 能访问所引用的材料，并向每个 Agent 提供适用的运行授权、隔离和交付约束；SVC user-scope 继续保持简单查询导航。文件归属、稳定引用和证据记录应解决真实交接问题，具体装配在实施预演中核对，不能先成为新的协作门槛。

诊断独立作为产品需求：默认展示工作项与会话树、实际运行状态及需要处理的问题，能沿相关对象追到实际输入、原生会话、代码与验收证据。运行事实由设施记录；需要理解语义的“在等什么、为何卡住”由 Agent 说明或按问题分析，未知就显示未知，不为仪表盘另建任务事件分类和等待图。复用 svc analysis 与 ARC-bench 的用例报告、trace、截图和日志，开发侧低成本 Agent 做按需语义筛选，原始材料不默认铺进主会话。

## 单一 Variant 与后端

历史方案曾把活动配置收敛到一个 shared-config，固定 Braid + SVC，并用 backend 参数选择核心；该方案已退出活动入口。当前每个团队 variant 自持有 prompt、原生接入和生成流程；backend 差异不再伪装成一个名为 `factory` 的 variant。

历史 run 和报告保留原 variant 名称及实际来源。旧配置退出活动 variant 入口，但迁移前核对旧命令和分析读取的使用者，不删除历史证据。后续消融作为新的显式实验配置加入；成绩比较仍要区分 backend、并发和实际源码，不能因 variant 名相同就混为同条件。
