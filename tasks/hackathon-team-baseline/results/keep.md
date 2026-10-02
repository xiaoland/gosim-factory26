# Lite Keep：pi-team-mixed 基线运行分析

本报告只分析 WSL 上的 `pi-team-mixed-arc-bench-lite-keep-54196efa62`，不修改生成应用、评测器或 Harness，也未重跑。原始 run 根目录为 `/home/yyh/Development/factory26/runs/hackathon-team-baseline/20260925/lite-runs/pi-team-mixed-arc-bench-lite-keep-54196efa62/`（下文记为 `$RUN`）。结论针对这一冻结应用；不把单次分差归因于某项 Harness 改造。

## 结果与五项失败

`$RUN/workspace/experiment-result.json` 记录生成 `completed / exit 0`、评测 `completed`，32 项执行完毕，**27 passed、5 failed，84.4%**；`score` 为 null。`frozen_source_sha256` 与 `evaluated_source_sha256` 均为 `e83ea20d41febcd58db3533b2ae9b4e7ea23f8d222e90a23b59bf7e8d7853731`。评测容器退出 1 对应五个 Playwright 失败，不是生成或部署未完成。直接报错见 `$RUN/workspace/official-evaluation/template/.arc/playwright-report.json`，逐项日志见同目录 `.arc/stdout.log`。

| 用例 | 官方观察 | 生成应用与自检事实 | 判断 |
| --- | --- | --- | --- |
| REQ-2.7.1 指派 `Work` | `setLabel` 在 `Note editor` dialog 内等待 `Work` checkbox，10 秒超时。 | `App.jsx` 在标签面板打开时卸载 `NoteEditor`，独立渲染 `LabelsDialog`；`selfcheck.py` 在 `Change labels` dialog 内查找同一 checkbox 并通过。 | 官方 locator 的容器范围与交付 DOM 不同；该超时本身不能证明 checkbox 或指派行为不存在。 |
| REQ-2.7.2 移除 `Work` | 同一 `Note editor` 范围内的 `uncheck` 超时。 | 与上一项共用标签面板结构；自检在 `Change labels` dialog 内移除并检查卡片结果通过。 | 同一结构差异。 |
| REQ-2.7.4 创建时指派 `Reminders` | 同一 `Note editor` 范围内的 `check` 超时，未走到填标题、关闭和保存断言。 | 创建流程也切换到独立 `LabelsDialog`，关闭后返回编辑器；自检按此流程通过。 | 同一结构差异；官方失败无法单独判断最终保存行为。 |
| REQ-2.8.1 置顶已有笔记 | `Pinned` 区域断言已通过；随后 `card.getByTitle('Pinned')` 在卡片**后代**中找不到标记，10 秒超时。 | `NoteCard.jsx` 把 `title="Pinned"` 放在 `article` 自身；自检直接断言 article 属性与区域，均通过。 | 置顶区域已出现，失败是标记所在 DOM 层级与官方 locator 不一致。需求正文也明确写“article has title `Pinned`”，所以不能据此认定置顶功能坏了。 |
| REQ-2.8.3 创建时置顶 | 创建后同一 `card.getByTitle('Pinned')` 超时。 | `NoteCard.jsx` 同样把 `title` 放在 article 自身；自检检查 article 属性与 `Pinned` 区域通过。 | 与上一项共用的定位差异；该官方用例未继续检查区域。 |

上述判断由 `$RUN/inputs/tests/{helpers.ts,REQ-2.7.1.spec.ts,REQ-2.7.2.spec.ts,REQ-2.7.4.spec.ts,REQ-2.8.1.spec.ts,REQ-2.8.3.spec.ts}`、`$RUN/inputs/requirements/requirements.md` 和冻结生成应用 `$RUN/workspace/official-generation/template/frontend/src/{App.jsx,components/LabelsDialog.jsx,components/NoteCard.jsx}` 交叉支持。需求要求标签编辑器有 checkbox，却没有规定它必须嵌在 `Note editor`；置顶需求明确要求 article 自身暴露 `Pinned` title。因此**五个官方断言未通过，集中在评测 locator 与需求允许的 DOM 结构不一致**，不能直接列为五项产品缺陷或 Factory V&V 失败。自检支持其实际检查过的需求路径；现有证据不足以判断整个产品的需求验证是否充分，亦不足以保证所有用户路径正常。

## 反馈循环与前轮改进的实际表现

原生归档入口是 `$RUN/workspace/official-generation/template/.factory26/20260924-163414-e4fa7b12/native/manifest.json`；四段 JSONL 均在其 `native/` 下，分别对应根 Issue 两段、PR 两段。Braid 本地对象保存在同层 `braid-state/braid.sqlite3` 的 `local_items`、`local_comments`、`local_merges` 等表。以下“直接”指原始工具/对象/产物与评测可交叉核实；“有限”指行为发生但收益或完整链条无法证明；“未观察”不等于能力不可用。

| 改进目标 | 实际行为与产出是否被采用 | 判断与证据等级 |
| --- | --- | --- |
| SVC Skill 按需导航、task packet、V&V 与提前消除关键未知 | 根 Issue 会话实际读取 `work/skills/svc/SKILL.md` 和 `references/task-packet/index.md`（首段 JSONL 第 26、28 行），先读需求、YAML 片段及六张参考图，并在编码前向 Issue 写一条技术栈、可访问性名称、种子数据和假设的设计评论（第 40 行）。未见读取 test-design/verification/implementation 等方法正文，交付树未见 task packet；没有在实现前明确“何种观察会推翻方案”的验收判据。 | Skill 入口与设计评论**直接生效**；task packet 与 V&V 方法采用**未观察**。自检到实现之后才建立，未证明 shift-left 有效。 |
| SVC 反馈解释与修复 | 根 Issue 编写并多次运行 Playwright `selfcheck.py`。早期 6/30、24/30、15/30 等失败促成服务启动、菜单定位、标签即时状态和自检路径的修改；最终 31/31。PR 会话复核构建和启动。 | 局部“失败→修改→自检通过”**直接**。自检按需求允许的独立标签 dialog 和 article 自身 `Pinned` 属性验证，因官方 locator 选了不同 DOM 范围而未取得这五项得分；这不构成要求生成 Agent 预知评测内部 locator 的理由。自检能支持其覆盖的行为，完整产品验证是否充分仍**证据不足**。 |
| Braid 简化身份与主动指派 | 根 Issue 用 `braid pr create --issue 1 ... --assignee glm` 创建 PR；对象库有 Issue/PR、单一 `pi-glm-fast` assignee、ready commit 与 applied merge。正常对象命令未携带 `state` 或 `writer-turn` 身份参数。根 Issue 先在自己的 worktree 尝试 PR ready/merge，随后 PR 实例在自己的 worktree 完成复核与整合。 | 创建、指派、身份归属和合并**直接**；少量 worktree/CLI 探索仍有操作负担，不能仅由成功交付推断全部易用性问题已消除。 |
| Issue/PR 分工、评论与上下文协作 | Issue 设计评论在 PR 新会话重建的工作记忆中出现；PR 能据此找到已有实现，并构建、启动、合入。根 Issue 在创建 PR 之前已写完并提交主要应用（`bbcb44c`）；PR 的 ready commit 仍是此提交，未见根据评论改变应用。对象库只有这一条设计评论，未见 reply/hide/resolve 的实际场景。 | 对象承载与跨会话传递**直接**；评论影响实施选择或“设计/实现”真实分工的收益**未证实**。reply/hide/resolve **未观察**，不强求人工制造争议。 |
| fresh 子会话、角色/模型/SOP | 原生 manifest 中四段均为 `pi-glm-fast`，每段 `model_change` 与有效 assistant message 均记 `factory26 / glm-5.3-flash` 并有 usage；四份 `*-session-tree.json` 的 `children` 均为空。PR 的 Braid 独立会话从当前 Issue/PR 对象重建工作记忆。冻结包内有 Pi subagents 运行包、角色文件及要求 fresh 的根成员指令。 | Braid 新会话与 GLM 客户端调用**直接**；子代理材料**已打包**，但 Pi 内部子代理调用、fresh 参数、子角色 SOP 实际生效及其成果采用均**未观察**。原生会话不提供未调用工具的完整暴露清单，不能从未调用推断不可用。未见 DeepSeek 请求；客户端记录也不是网关服务端路由审计。 |
| 探索与外部工具：rg/ast-grep、Context7、Exa、浏览器 | 四段会话的工具调用只有 `bash/read/write/edit`；`bash` 未见 `mcporter`、Context7、Exa、SVC CLI 或 ast-grep 查询。根 Issue 用 `read` 看参考图、用 shell `grep`/文件读取查需求，用 `bash` 启动 Playwright/Chromium 做真实页面自检；无原生 browser operator 会话。 | 图片与页面操作**直接**；外部 MCP 查询、专用检索和浏览器子角色收益**未观察**。不能把 npm 安装或模型成功请求当外部 MCP 可达证据。 |

与[上轮 Keep boundary-fix 分析](../../braid-usability/results/keep-boundary-fix.md)对照，两次均为 27/32，但上轮还有三个种子状态与测试前置操作冲突、两个标签容器冲突；本轮旧种子状态失败未再出现，新增三个标签容器和两个置顶 locator 失败。制品、过程和失败构成均不同，**同分不是“无改进”或“改造无效”的因果证据**。本轮能确认自检促成局部修复，PR 复核了启动路径；五项失分反映官方 locator 与需求允许的结构分歧，不能据此要求把评测细节当产品要求。没有其它独立用户路径观察，也没有服务端模型/MCP 审计，故不判断整套产品验证已充分或不足。
