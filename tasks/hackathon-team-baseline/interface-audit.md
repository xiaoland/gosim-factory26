# Agent 使用入口审查与实施准备

状态：已获用户开工及自购 API 完整 Lite 验收授权，正在实现。
用户要求将“从使用者已有的经验介绍能力，而不是把实现者的系统划分教给使用者”应用到同类问题。
产品依据为 [工作项入口方案](workflow-design.md)，本页保存具体落点、取舍与执行顺序。

## 发现与取舍

| 入口 | 当前证据 | 修正 |
| --- | --- | --- |
| Braid 稳定指令 | `src/group/provider.rs:60–94` 把 Issue/PR 解释为问题、设计、验收和实施阶段，并直接规定局部委派用原生 sub-agent。 | 介绍 braid CLI、Issue/PR 的查看、评论和指派；保留成员目录、当前对象和分支这些操作事实；删除阶段指令及原生子代理介绍。 |
| 当前 variant 的两个成员指令 | `agents/*/instructions.md:1–5` 重复阶段流程、原生角色路由、fresh 参数及 SVC 内部方法名。 | 删除 Braid 与原生接入已经拥有的介绍；用普通软件工作问题介绍 SVC，保留任务实际的无人值守条件。角色模型、SOP 和 fresh 配置继续由原生角色文件承载。 |
| 初始与重建上下文 | `issue_agent.rs:410`、`pr_agent.rs:352`、`dispatch.rs:362` 解释 working memory、canonical、provider history；所有内容又被笼统称为非指令。 | 直接使用现有 Issue/PR 内容投影；去掉内部过程的包装。目标仍由 Issue description 提供，不改变正文、评论、隐藏理由及关联对象的可见性。 |
| 唤起与变更通知 | `provider.rs:96–108` 使用“事件引用”“不是阶段命令”“先读取再决定”；`objects.rs` 有“根需求”“Issue activation”“下一合法 turn 前读取完整当前 Context”。 | 唤起为“请处理 Issue #N。”或“请处理 PR #N。”；附带更新只陈述对象与评论发生了什么，并给出可用查看命令。根对象标题改为“任务”，不把通用 task 预先解释成 requirement。 |
| 操作反馈 | `objects.rs:1117` 用 group 解释 ready 限制；`:1250,1269` 要求 PR 自检后 ready，并把合并分支称作 delivery。 | 用正在处理的 Issue/PR、分支、提交解释同一事实与操作条件；移除自检方法命令。保留实际错误和分支信息，不改变权限、合并条件或错误分支。 |
| CLI 帮助 | `cli/mod.rs:11,205` 使用“工作记忆”“激活 work item”；同一 CLI 也服务宿主。 | 帮助围绕 Issue/PR 操作描述；宿主专用选项说明其使用者，不改参数及全局可见性，不为同一帮助另造生成器。 |
| Agent 的 status | `cli/mod.rs:535–551` 仅移除 physical_sessions，仍打印 active_turns/pending_batches 等；`local.rs:242–248` 的内部摘要供运行调度使用。技术说明声称内部计数已对 Agent 隐藏，与实现不符。 | 在既有 agent_runtime 分支中复用对象读取，显示 Issue/PR 的编号、标题、状态与负责人；JSON 保留 items 外壳，内部运行摘要及宿主输出保持原样。 |
| SVC skill 入口 | `SKILL.md:3,21,27` 的 description、acceptance observations、planning topology 需要读者先理解方法分类。 | 按当前问题及预期帮助表达；方法正文与已选定方法后的专业术语保留。 |
| 探索工具 skill | `harness/skills/exploration-tools/SKILL.md:15` 从“main entry 设置 MCPORTER_CONFIG”介绍接线。 | 直接说明 Context7/Exa 已配置、怎样调用及查看实际 schema；准确命令和环境变量名仍可用于排障，不以入口实现作为使用前提。 |

SVC 取证由独立 Agent 定向阅读入口及方法，主 Agent 作以上取舍。
其余候选如“state lifetimes”属于工程师已熟悉的概念，单凭专业词汇不认定为问题。
角色正文中的工具选择、返回内容、文件权限和专业 SOP 是完成任务所需知识，不因出现约束而删除。
宿主的 `status --json`、telemetry、数据库字段、会话日志和技术文档面向维护者，保留其精确信息，不执行全仓术语替换。
当前 profile 命令已明确限制为宿主诊断，Agent 的 Issue/PR list/view 已使用 assignee；这些已经合适的路径保持现状。

## 具体输入形式

Braid 稳定入口以如下语义为准，再用实际支持的例子提供操作帮助：

> 使用 `braid` CLI 操作 Issue / PR，常用操作沿用 GitHub CLI 的形式。Issue 和 PR 可以 assign 给其他 Agent。像人类一样在 Issue / PR 中开展协作。

已按当前 clap 参数核对的例子：

```sh
braid issue view 1 --comments
braid issue comment 1 --body-file note.md
braid issue comment 1 --reply-to 8 --body '补充信息'
braid pr create --issue 1 --title '完成搜索功能' --body-file change.md --assignee teammate
braid issue edit 2 --add-assignee teammate
braid comment hide 8 --reason '已由后续信息替代'
braid comment resolve 8
```

入口不必列出全部示例，选择查看、指派、回复等少量例子，其余由对应 `--help` 承担。
`teammate` 代表从成员目录选出的实际 login；Issue #2 的 add 示例仅适用于未指派状态，更换已有负责人须在同一 edit 中 remove 原负责人并 add 新负责人。
不声称所有 GitHub CLI 参数兼容；`--issue`、普通评论 thread/hide/resolve 等扩展能力按真实行为说明。
hide 的理由与 resolved 历史仍可查看；删除不可恢复正文、description 编辑会重新接续工作等会影响使用决定的效果，要用直接语言告知，不解释内部队列与会话实现。

操作反馈示例：

- `only this PR group can mark ready` → “当前正在处理 Issue/PR #M；此操作需由处理 PR #N 的 Agent 执行。”
- `ready head changed; PR must self-check and mark ready again` → “PR #N 的提交已改变，当前提交尚未标为 ready。”
- 合并冲突通知报告 PR 编号、源分支与目标分支，合并未发生；如何整合与验证由 Agent 判断。
- 旧调用写入失效报告“当前调用已失效，本次修改未写入”，不把多个潜在原因猜成唯一诊断；底层日志保留原有身份事实。

这些表述描述现有操作条件；本轮不改变谁可以改派、ready 或 merge。
不将 ready 限制表述为 login 权限：同一登录名可被指派多个对象，实际检查的是调用正在处理的对象，宿主显式操作另有既有路径。

## 已核实的接线与实施顺序

1. 修改 Braid 的共同稳定指令和 CLI 帮助/操作反馈。
   Issue/PR 启动、resume 和 reset 共用 `issue_system_prompt` / `pr_system_prompt`，在共同位置修正即可覆盖两类工作项。
   `render_event_references` 同时服务空闲唤起与运行中的 steer；只改呈现及 reference 文字，不改事件类型、收件者或调度。
   Agent status 复用 `LocalObjects.list` 与现有公开字段选择，不新增状态模型；`local.status` 的计数仍由 runtime 与宿主读取，不能改这个共同生产者。
2. 移除 Issue 初建、PR 初建及 reset 三处上下文包装，继续传递同一个 `rendered.text`。
   `SessionManager.start → SessionFactory.start → inject_context` 已提供上下文入口。
   Pi `provider/pi.rs:305–359` 暂存对象内容，并在 prompt 中与请求拼接；Codex `provider/codex.rs:344–358` 单独注入对象消息。
   因此“简短请求”指其命令内容；不能声称 Pi 整条原始 user message 只有这一句话。
   本轮不为物理消息布局增加协议、system prompt 中的任务数据或原生 Adapter 分支。
3. 收敛 `pi-team-mixed` 两个成员的 `instructions.md`，更新 SVC description、两处导航及探索工具 skill 的接线叙述。
   SVC 文本采用已认可的 [候选](workflow-design.md#svc-导航候选)；不复制方法正文。
   `run.py:native_files` 已将角色配置交给 Pi，无需新增“Factory 能力指引”。
   本轮冻结运行所用 pi-subagents 0.56.0 的 `extension/index.ts:671–716` 注册原生工具，`tool-description.ts` 已提供 list、调用与 guide，`schemas.ts:321` 说明 context 参数；`api/preflight.ts:195–205` 消费角色 defaultContext。
   当前两个成员的原生角色均设为 fresh，model、thinking、tools、skills 和 SOP 不变；不改或复制第三方工具说明。
4. 同步受影响的 `docs/product-tdd/index.md` 与 Braid `docs/20-product-tdd/local.md`，区分维护者理解的结构与 Agent 的使用入口。
   实施前核对脏工作区，只修改上述范围；冻结 ZIP、历史 run、归档 variants 均保留。

## 检查与验收

独立预演已完成，只核对上述入口、调用方与参数是否支持计划，不用读代码声称行为验收成功。
预演纠正了 shell 占位符、add-assignee 的未指派前提，以及 ready 不能仅按 login 解释的条件；上文已吸收。
主 Agent 追查所有调用方后，还排除了一个 grep 假阳性：`only this work item group can change its assignee` 仅由旧 set_assignee 路径触发，当前 CLI edit 传入 require_own_writer=false，因此不能将它写成当前 CLI 的限制或本轮待修入口。
三处上下文包装不含额外对象事实，直接保留 rendered.text 无需新 API；status 必须只改 CLI Agent 分支，内部计数生产者保留。
实施后直接审阅最终指令与对象文本，核对修改涉及的所有消费者及原始诊断信息；Rust 编译可用于检查接线。
不新增或运行 Factory/设施/Corpus 测试、替身或探针。
用户已授权重新运行完整 Lite，改用自购 Kimi/DeepSeek/GLM API；具体执行与差异见 interface-lite.md。
行为判断以材料对后续决定与产出的作用为准，不以工具调用数、Issue 数或 PR 数代替收益。
