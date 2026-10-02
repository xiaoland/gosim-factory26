# 临时修复版 Keep：已交付，独立评分 23/32

本报告只分析 `pi-team-mixed-arc-bench-lite-keep-9cacc02bdd`。`workspace/experiment-result.json` 记录生成 `completed`、冻结源码与评测源码 SHA-256 同为 `b206d6a0fa93af65a0e3668f9faf6db1c5172666ecbaeabf96f087d612c2d8cc`；Braid 的 `braid-state/result.json` 记录交付提交 `6aa1d14e42263deba788763e6e4f3eefa398ffcc`。官方本地 Runner 的 noop 评分阶段完成，Playwright **23 passed / 9 failed / 32 total，71.9%**；`score=null` 是 noop 阶段没有 Meter，评分容器 exit 1 对应失败断言，不能把 71.9% 称为平台总分。没有重跑、改应用或打开外部测试源码。

它是重新生成的应用。旧 Keep 从另一合入提交提取的源码 SHA-256 为 `8862dd932265487277367bf849c8a2a7c50db41d9a7f52e145d613bb443e6bd6`，其补评测为 19/32；两个数字**不是对同一应用只改 Braid 交付门槛的受控对照**，不能把 4 项差额归因于交付语义修复。

## 九项失败的定位

| 项目 | 评测结果、页面快照与冻结应用形成的因果链 |
| --- | --- |
| REQ-2.3.3、REQ-2.5.3、REQ-2.5.4：3 项 | 定位器从首页笔记 article 内寻找标题按钮以继续删除/归档，10 秒后仍找不到；失败时首页快照不含相应笔记。冻结 `backend/store.js` 将 `Delete me 2.3.3` 初始设为 `trashed: true`，将两条 `Travel plans` 初始设为 `archived: true`。根 Issue 的验收契约与 PR 评论也明确采用这些预置终态。因而这些失败发生在预期的首页交互之前，不能判定 Trash/Archive 后续功能本身失效。 |
| REQ-2.4：1 项 | 点击编辑目标后，定位器等待 `Note editor` 内的 `Note content` 文本框超时；失败快照有 `Project ideas` article，却没有 `Note editor`。冻结 `NoteCard.tsx` 表面上将 article 点击接到 `onOpen`，`App.tsx` 也有 editor 渲染路径；现有报告没有记录先前点击实际命中的元素或浏览器错误，**不能唯一确定对话框未出现的原因**。 |
| REQ-2.7.1、REQ-2.7.2：2 项 | `Work` 复选框在失败快照中存在（第二项为已勾选），但在卡片下的独立 `Note labels` dialog 内；Runner 在 `Note editor` dialog 内寻找该复选框，故超时。冻结 `NoteCard.tsx` 在卡片中挂载 `LabelPickerDialog`，与该层级一致。结果止于定位，不能断言标签数据操作失败。 |
| REQ-2.7.4：1 项 | 创建笔记时标签已勾选 `Reminders`，随后关闭编辑器遇到严格定位错误：`Note editor` 下有两个名为 `Close` 的按钮，一个是编辑器本身，另一个是嵌套 `Note labels` dialog。失败快照与 `NoteEditorDialog.tsx`、`LabelPickerDialog.tsx` 一致。 |
| REQ-2.8.1、REQ-2.8.3：2 项 | 目标笔记在失败快照中已位于 `Pinned` 区，按钮为 `Unpin note`；定位器要求目标 article 的**后代**带 `title="Pinned"`，而冻结 `NoteCard.tsx` 把该 title 放在 article 自身。置顶状态已改变，失败发生在标记位置检查。 |

以上九项有五类直接失败点，主要是种子初始状态、对话框层级和 DOM 标记契约不匹配。REQ-2.4 保留未定因，不用推测补齐。无证据表明模型连接或 Runner 设施使这九项断言失败；也不能由未触达的后续断言推断那些功能的好坏。

## Braid 工作流程与信息作用

这次有可核的设计/实施分离。根 Issue 由 `@glm` 负责，09:11:06 UTC 先在交付分支提交 `2d8d2e2`，只新增 67 行 `docs/acceptance-contract.md`，列出可访问性与种子数据决策；09:11:43 创建 PR #1 并**显式指派** `@deepseek`。PR 成员读取该文档，在独立 PR 工作树实现前后端，09:36 提交 `f7a732f`，完成本地构建、自检后在 09:37:22 留下唯一一条 PR 评论，说明验证结果及三处与根契约不一致的选择：标签管理行名称、Trash/Archive 种子状态、笔记菜单按钮角色。根成员 09:39 查看 ready PR 与评论，在独立临时工作树构建、运行测试、启动应用、核验持久化并抽查标签命名；09:43:50 合并为 `6aa1d14`，09:44:09 以自然语言验收理由关闭根 Issue。`braid-state/result.json` 为 `completed`，交付提交与评测的冻结源码摘要相对应。

这条评论承载了实质信息：PR 成员没有机械照抄根契约中的 `Label <名> editable` 等字面假设，根成员随后抽查标签命名，最终关闭理由明确写出“标签行命名以需求文本为准，契约差异已在 PR 讨论记录”。与此同时只有一次评论、没有回复或多轮协商；种子状态取舍虽被记录并接受，却导致了上述三项评分失败。故可说工作项促进了差异显化和有依据的接受决定，不能说持续讨论充分消除了误判。`local_comments` 无 hide、resolve、reply；上下文整理能力在本 run 未观察。没有未指派对象或重新分派场景。

## 证据定位

本机只读副本在 `/Volumes/WorkSSD/Development/factory26/runs/braid-usability-implementation/evidence/keep-delivery-fix/`，对应 WSL 原 run 为 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/delivery-fix/runs/pi-team-mixed-arc-bench-lite-keep-9cacc02bdd/`。副本含 `run.json`、`workspace/experiment-result.json`、生成 Braid 的 `braid-state/{result,status}.json` 与 `braid.sqlite3`、原生会话 `native/000,002,004`、`native/manifest.json`、评测 `playwright-report.json` 与九项失败的 `error-context.md`、相关冻结应用文件；不含评测测试源码。定位时间：根契约提交 09:11:06、PR 创建 09:11:43、PR 评论 09:37:22、根验收 09:39–09:44，见原生会话；评分细节见 `workspace/official-evaluation/template/.arc/playwright-report.json` 及同级 `tests/test-results/*/error-context.md`。
