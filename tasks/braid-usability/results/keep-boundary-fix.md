# Keep：boundary-fix 制品的独立运行分析

本报告只分析 `pi-team-mixed-arc-bench-lite-keep-bfdf6b8f51`。远端原始 run 位于 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/boundary-fix/runs/pi-team-mixed-arc-bench-lite-keep-bfdf6b8f51/`；必要原始材料只读复制到 [`boundary-keep`](../../../runs/braid-usability-implementation/evidence/boundary-keep/) 供复核。未修改生成应用或评测器，也未启动另一轮实验。

## 正式结果与交付边界

**事实。** [控制器结果](../../../runs/braid-usability-implementation/evidence/boundary-keep/run-controller.json)的阶段为 `completed`、外层退出码为 0。[实验结果](../../../runs/braid-usability-implementation/evidence/boundary-keep/experiment-result.json)记录生成 `completed / exit 0`，官方本地评测 `completed`，**27 passed、5 failed、32 total，test_pass_rate 84.4%**。这里的分母是明确的 32 个 REQ Playwright 用例，详见[完整报告](../../../runs/braid-usability-implementation/evidence/boundary-keep/playwright-report.json)。`score` 为 null；空 Agent 的独立评测阶段容器退出码和内部 runner 退出码为 1，不能把 null 叙述为另一种数值分数。生成阶段记录 8521.719 秒、33,910,848 token 和 8.850824 CNY；评测阶段 token 指标为 null。

**事实。** [Braid 结果](../../../runs/braid-usability-implementation/evidence/boundary-keep/braid-result.json)为 `quiescent`、理由“当前没有可执行工作”，返回 `refs/heads/braid-delivery` 上的 `5535ccaae80ed797f3ed1abf07ac1b4e932d0f0d`。 [Factory 运行记录](../../../runs/braid-usability-implementation/evidence/boundary-keep/run-factory.json)把 Braid 的操作结果与 `delivery_commit` 单独记录，`process_exit_code=0`、`phase=frozen`。[导出记录](../../../runs/braid-usability-implementation/evidence/boundary-keep/delivery.json)为 `delivered`；生成目录有 `frontend/package.json` 与 `backend/package.json`，官方 Runner 随后实际构建、部署并执行了全部 32 项。这证明该次运行越过了 Braid `completed` 封存门槛并完成应用导出及评分。Braid 数据库的 `local_run.lifecycle` 仍为 `running`；根 Issue 最终为 `CLOSED`、PR 为 `MERGED`，因此**本次没有直接观察到根 Issue 保持开放时仍导出**，不能用它单独证明该反事实。

**输入身份。** 对远端源 ZIP 和本 run `inputs/agent/pi-team-mixed.zip` 执行 `sha256sum`，两者的实际字节 SHA-256 均为 `4f581ac51e485a767954976abc17764ff799bd2a64eadf707b671b65a4a47d6d`。控制器 `run.json` 中 `inputs.agent.sha256=d6643306...` 是输入身份字段，不能拿它当 ZIP 字节 SHA-256 比较；实验结果的 `frozen_source_sha256` 与 `evaluated_source_sha256` 同为 `cc2317f8...`，是冻结/评测应用源摘要，也不是 ZIP 字节 SHA-256。

## 五项失败的直接证据

| 用例 | 官方失败位置 | 生成应用与需求/测试的对应事实 | 判断 |
| --- | --- | --- | --- |
| REQ-2.3.3 Trash list | 测试先在首页对 `Delete me 2.3.3` 卡片执行 `deleteNote`，`hoverNamed` 等待该卡片内匹配标题的目标 10 秒超时。 | `backend/src/seed.js` 将该笔记预置为 `trashed: true`，首页不显示它。需求场景只写“打开 Trash 并显示已删除笔记”，自测也直接打开 Trash；官方测试额外从首页删除。 | 超时的直接原因是首页不存在目标卡片。此题同时存在需求场景与官方测试前置操作的差异；不能据此声称 Trash 页面本身失效。 |
| REQ-2.5.3 Show archived notes | 测试先从首页对 `Travel plans 2.5.3` 执行 `archiveNote`，同样在找标题卡片的悬停步骤超时。 | seed 将其预置为 `archived: true`。需求场景只要求打开 Archive 显示它；生成 Agent 自测也如此。 | 官方测试要求从首页归档，预置状态使目标不在首页。 |
| REQ-2.5.4 Unarchive | 测试先从首页归档 `Travel plans 2.5.4`，在同一悬停步骤超时，尚未执行 Unarchive。 | seed 将其预置为 `archived: true`。需求场景从已打开的 Archive 列表执行 Unarchive；自测按此路线通过。 | 本次失败不证明 Unarchive 按钮自身坏了；失败发生在官方测试新增的首页归档前置步骤。 |
| REQ-2.7.1 Assign label | `setLabel` 在 `Note editor` dialog 内等待名为 `Work` 的 checkbox，10 秒超时。 | 官方测试从卡片的 `More options → Change labels` 打开面板。生成应用把该 `LabelEditorPanel` 渲染在卡片 `article` 的 popover 内，没有打开 `Note editor` dialog；Agent 自测从 `article` 内定位 checkbox。 | 控件实际定位范围与官方测试契约不同。不能把此超时简单归因于没有 `Work` checkbox。 |
| REQ-2.7.2 Remove label | 与上一项同一 dialog 内定位 `Work` checkbox 的 `uncheck` 超时。 | 同一组件位置与自测定位方式；seed 已给目标笔记 `Work` 标签。 | 与 REQ-2.7.1 共用的结构差异。 |

上表中的官方调用与报错来自[评测报告](../../../runs/braid-usability-implementation/evidence/boundary-keep/playwright-report.json)及远端本 run 的 `workspace/official-evaluation/tests/{REQ-*.spec.ts,helpers.ts}`；seed、`NoteCard.jsx`、`NoteEditor.jsx`、`LabelEditorPanel.jsx` 来自该 run 的冻结生成应用。需求对照来自其 `requirements/requirements.md`。这些是静态产物与实际 Playwright 报错的交叉证据，未重跑或改动评分。相邻功能的官方用例 REQ-2.3.1、2.5.1、2.7.3 等通过，但不能替代这五项的分数。

## Agent 行为和 Braid 的实际作用

**事实。** [原生会话定向摘录](../../../runs/braid-usability-implementation/evidence/boundary-keep/native-evidence.md)与 [Braid 对象数据库](../../../runs/braid-usability-implementation/evidence/boundary-keep/braid.sqlite3)显示四段原生会话全部使用 `pi-glm-fast`，分别落在根 Issue 与 PR 的 agent 实例上。根 Issue 会话读取需求和 SVC，创建任务包，在 Issue worktree 编写前后端全部主要代码，编写自己的 `/tmp/e2e.py` 并反复修正后宣称 32/32；11:57 提交应用，12:00 才创建关联 PR。其自测对 REQ-2.3.3、2.5.3、2.5.4 直接访问预置 Trash/Archive 数据，对 2.7.1/2.7.2 从卡片 `article` 内找 checkbox，正好没有覆盖官方测试的不同前置步骤和 dialog 范围。PR 会话随后构建、启动并重跑同一自测，更新任务包，然后 `ready`、`merge`；根 Issue 没有在该复核之后修改应用代码。其“32/32”是生成 Agent 自测结果，不能当正式 benchmark 成绩。

**事实。** 初建 PR 时未指派成员，根 Issue 会话尝试 `braid pr ready` 得到 `only this PR group can mark ready`；带 `--state` 试图绕过身份时 CLI 拒绝。它手工创建的 PR worktree 与 Braid 为新指派的 PR 实例创建 worktree 冲突，数据库保留 `Git operation failed ... 'braid/pr-1' is already used by worktree`，首个 PR assignment 进入 `blocked`。根 Issue 会话移除手工 worktree、取消并重新指派后，第二个 PR 实例正常运行并合入。这是一次可恢复的操作负担，没有使本 run 的生成或评分失败。

**事实及界限。** Braid 确实保存了 Issue、关联 PR、assignee、ready/merge commit 和原生会话，也把当前 Issue/PR 对象重建进 PR 会话上下文；PR 会话据此找到交付物并作复核。可见的 `braid context pr 1` 是读取，原生调用没有 context resolve/hide 或对 Issue/PR 正文作信息更新；数据库只有根 Issue 和一个 PR、两条内容重复且均在 merge 之后写入的验收评论，没有合并前围绕需求争议的讨论反馈。根 Issue 的全部主要实现早于 PR 创建，因此本 run 的“设计/实现分离”主要是对象和会话顺序，不能算多成员在设计反馈后改变实现。PR 会话的独立构建与自测有实际复核价值，但沿用了根 Issue 的同一测试假设，未发现官方测试中的五项差异。未观察到上下文编辑和有效的前置讨论，不能把对象 revision 数解释成它们发生过。

## 供下一轮决定的发现

1. **边界修正的可观察成果是交付与评分通路成功。** Braid 返回 `quiescent`、Factory 记录确切提交并交付应用、Runner 完成 32 项。根 Issue 同时被关闭，所以开放工作项下的同类场景仍需其它真实证据。
2. **本次 5 个失分集中于两类契约偏差。** 三项是官方测试对预置笔记又先执行首页删除/归档，与 Agent 按需求场景选择的初始状态相撞；两项是卡片标签面板与测试要求的 dialog 范围不同。根 Issue 与 PR 成员共用自测路径，故其 32/32 未覆盖这些差异。
3. **Braid 的对象接力未形成有效的实施前反馈。** 唯一执行模型先在 Issue 完成代码、后建 PR；PR 成员复核了构建和自测，也经历了可恢复的身份/worktree 障碍，但没有观察到上下文整理或改变实现的讨论。分数提升或下降不能归因于 Braid 协作收益。
