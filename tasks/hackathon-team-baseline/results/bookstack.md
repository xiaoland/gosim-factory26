# BookStack Lite run：27/34 的证据边界

只读对象：WSL `/home/yyh/Development/factory26/runs/hackathon-team-baseline/20260925/lite-runs/pi-team-mixed-arc-bench-lite-bookstack-ba27587982/`，下文记作 `R/`。没有修改生成应用、评测输入或重新运行。分析按 [本轮设计](../design.md) 区分最终行为、Agent 过程和可归因性。

## 结果与主要判断

`R/workspace/experiment-result.json` 显示生成完成、官方本地评测完整执行 **34 项，27 通过、7 失败（79.4%）**；`score=null` 是本地结果没有综合分，评测容器 exit 1 对应 Playwright 失败。冻结与受评应用源摘要同为 `0b7664cc79c71d971296c3fa7f8c3bbd503957d5823a78fd82df8ce863fcab8f`。输入 ZIP 与应用身份见 `R/run.json`、`R/workspace/experiment-result.json`。与历史 30/34 的差异不能当单项改造效果，因为不是同一冻结输入与单变量对照。

七项均为 10 秒超时。其中六项的失败快照**已经显示期望对象以另一种角色出现**：评测 helper 在异步页面或状态更新前即时探测多个 locator；当时都不可见时固定返回列表首项（button 或 heading），随后只等这个错误角色。代码见 `R/inputs/tests/helpers.ts` 的 `firstVisible`、`clickNamed`、`expectTextsVisible`、`expectVisible`，每项的直接错误见 `R/workspace/official-evaluation/template/.arc/playwright-report.json`，DOM 见 `R/workspace/official-evaluation/tests/test-results/REQ-*/error-context.md`。这支持**评分 helper 时序竞态的推断**，不能据最终快照断言其后未执行的点击跳转也会成功。剩余 REQ-6.1.3 是导航契约差异。官方隐藏测试按实验约束在应用冻结后才运行，不能要求生成 Agent 预知其 helper 或用评分后的无修复推断生成期反馈失效。

| 官方失败 | 直接观察与可支持的结论 | 证据等级 |
| --- | --- | --- |
| REQ-6.1.1 保存页面 | helper 等 `heading Page Created 6.1.1`；失败快照停在书详情，已有 `link Page Created 6.1.1`。需求要求保存后返回书详情并添加条目，快照支持这个结果；helper 很可能在导航完成前锁定 heading。 | 结果可见；时序原因推断 |
| REQ-6.1.2 保存草稿 | helper 等 `button Book 6.1.2`，快照在书列表显示 `link Book 6.1.2`。超时发生在进入编辑器前，**没有官方保存草稿的观察**。 | 错误角色与书存在确定；后续未知 |
| REQ-6.1.3 删除草稿 | helper 从书详情点击 `Draft 6.1.3` 后再等 `Edit`；快照已经在带 `Delete Draft` 的草稿编辑器。生成应用的 `frontend/src/pages/BookPages.jsx` 将草稿直接链接到 `/pages/:id/edit`。需求 `R/inputs/requirements/requirements.md` 的 GIVEN 是“已在页面编辑页”；官方 helper 额外要求中间 `Edit`。**导航路径不一致**，不能说删除功能本身失败。 | 确定 |
| REQ-6.3.1 进入阅读页 | helper 等 `button Page 6.3.1`；书详情快照已有 `link Page 6.3.1`。点击与阅读页未被官方观察。 | 错误角色确定；后续未知 |
| REQ-8.1 收藏 | helper 等 `heading Unfavorite`；快照已有 `button Unfavorite` 且 `[pressed]`。这直接证明当前页面的收藏切换发生了；helper 的后续 aria-pressed 断言因先前超时未执行。 | 切换确定；竞态推断 |
| REQ-8.2 从收藏跳转 | helper 等 `button Book 8.2`；首页快照在 `My Most Viewed Favorites` 内已有 `link Book 8.2`。收藏列表有目标，跳转未被官方观察。 | 列表结果确定；后续未知 |
| REQ-9.1 从最近更新跳转 | helper 等 `button Page Updated 9.1`；首页快照在 `Recently Updated Pages` 内已有 `link Page Updated 9.1`。更新列表有目标，跳转未被官方观察。 | 列表结果确定；后续未知 |

## 改进是否在本 run 体现

原始执行材料在 `R/workspace/official-generation/template/.factory26/20260924-163415-c848b68c/`，下文记作 `G/`；三个原生会话在 `G/native/`，Braid 对象库为 `G/braid-state/braid.sqlite3`。验收判据参照 `tasks/factory-subagents/verification.md`、`tasks/braid-usability/verification.md` 与 `tasks/braid-usability/factory-workflow.md`。表中“未观察”不等于配置失效。

| 改进或假设 | 实际行为与产出采用 | 证据等级 |
| --- | --- | --- |
| SVC skill 按需导航、task packet、V&V、shift-left | 冻结提交包确有 `agent/skills/svc/SKILL.md`；Braid 有效角色指令要求按问题查阅 SVC 并保存 packet。三个原生会话的实际工具调用没有读 SVC、没有 `svc` 调用，交付树没有 task packet。Agent 直接读需求与参考图、检查 Node/npm/Playwright，独立写应用后建立自编浏览器检查；尚无证据表明 SVC 方法影响了判据或路线。 | 配置确定；运行采用未观察 |
| 需求与生成期反馈循环 | 原生主会话先读取需求 Markdown、YAML 和参考图，再写应用；之后自编 Playwright 驱动浏览器，观察到页面与操作失败，修改应用并重走检查。源代码提交后，一次清理误删前端构建物导致自检失败；Agent 识别并重新构建，最终在新启动服务上得到 **33 passed, 0 failed**。这证明生成期存在“需求→真实浏览器观察→修复→复验”的局部循环。检查脚本自身也曾改写等待和导航，因此仅凭最终计数，不能逐项证明每次失败都在**同一原路径与判据**下由应用修复；需要对具体轨迹逐一核对才可扩大结论。33 项自编检查与 34 项隐藏评分是不同观察，不把数量差当成缺陷或反馈失败。 | 循环及最终自检确定；逐项原路径复验边界有限 |
| Braid 简化身份与工作项 | 初始根 Issue #1 已指派 `@glm`；Agent 使用 `braid issue view`、`braid issue close`、`braid comment resolve/view`，调用没有手工传 state 或 writer-turn，写入作者/对象由 Braid 关联。只有一名 GLM issue agent、一个 Issue、一个自写交付评论；无 PR、子 Issue、merge 或跨成员消息。Agent 在根 Issue worktree 独自完成并提交，评论在实现后形成，没有被另一成员用于决定或接入。 | 调用与对象确定；协作收益未观察 |
| comment/reply/hide/resolve 的上下文整理 | 交付评论 #1 后被同一成员 `resolve`，Braid 因事件重建了后续 Context；重建会话读到 CLOSED Issue 和已解决评论。没有 reply、hide、跨成员消费者或因评论改变的代码/决定。 | resolve 与重建确定；信息增益未观察 |
| 主动 assign / Issue→PR 分工 | 工作项初始就由 Factory 指派 `@glm`；Agent 没有新建或编辑指派，没开 PR。`G/braid-state/result.json` 仍记录 `quiescent` 与交付 ref/commit，说明此场景无 PR 仍交付；不能据此证明设计/实施职责分离。 | 确定；主动选人未观察 |
| fresh 子会话、角色 SOP 与模型 | 三个 `G/native/*session-tree.json` 均 `children: []`；主会话没有 spawn 或局部子 Agent 调用，因此 fresh 参数、子角色收到 SOP、子产出被父采用均未观察。`G/braid-state/physical/*/instructions.md` 是实际 Braid 角色上下文，含 SOP 和 `context:"fresh"` 指引；不是子角色运行证据。三段原生会话的 `model_change` 与 assistant message 均记录 `factory26/glm-5.3-flash`，没有 DeepSeek 调用；这是客户端原生记录，缺服务端路由审计。 | GLM 调用确定到客户端；子 Agent 未观察 |
| 探索工具与浏览器 | 实际工具为 `bash/read/write/edit`；没有 MCP/`mcporter`、Context7、Exa、ast-grep、`rg`、agent-browser 或 browser-operator 调用。Agent 用安装的 Playwright 从 Node 脚本驱动 Chromium，浏览器反馈确促成局部改动。可用工具配置或 npm 成功不能外推 MCP 查询成功。 | 浏览器执行确定；其他工具未观察 |

`G/native/manifest.json` 报三段原生会话归档 complete、gaps 为空；可据此描述可见 Pi 工具与消息。归档没有网关服务端请求明细，也没有完整系统提示逐字副本，故不把模型路由或 skill 自动发现的实际提示内容说成已被独立审计。Braid 本地对象只有一名 assignee 和一次自写评论；没有“子 Agent 产出被采用”的路径。

## 与前一 BookStack 分析的可比边界

先前 [boundary-fix 分析](../../braid-usability/results/bookstack-boundary-fix.md) 是另一冻结 run 的 **30/34**。本次种子数据包括旧 run 缺失的 `Shelf 4.3.2`，本次 REQ-8.1 的失败快照也已见 `Unfavorite` pressed；这说明两个旧缺口在此受评应用中有相应行为。REQ-6.1.3 的直接进编辑器与官方多余 Edit 仍相冲突；旧 run 的 REQ-7.2 类 helper 竞态在本次六项中呈现类似形态。不能由两个分数的差值归因于 Braid、SVC、模型或浏览器路线。

本 run 的决策意义是：完整 34 项评分已取得，生成与交付有效；当前 7 个红项需要按**实际应用缺陷、官方 helper 时序/路径、未观察的后续旅程**分开判断。六个快照只能确认目标元素最终出现，其中 8.1 确认状态已切换；不把未执行的跳转或草稿保存自动补记为通过，也不把 27/34 简化成七个应用缺陷。生成期可见反馈已推动局部修复与最终自检；隐藏评分是冻结产物的独立结果，不属于可回流的生成期反馈。
