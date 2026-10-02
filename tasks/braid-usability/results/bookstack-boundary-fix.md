# BookStack boundary-fix run 独立分析

本报告只分析 `pi-team-mixed-arc-bench-lite-bookstack-f065388906`。原始 run 位于 WSL `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/boundary-fix/runs/pi-team-mixed-arc-bench-lite-bookstack-f065388906/`；下文的 `R/` 指该目录。取证只读取此 run 的冻结输入、生成应用、官方结果、Braid 对象和原生会话，没有启动新实验或修改应用。关键原件另存于 [boundary-bookstack 证据目录](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/)。

## 正式结果与边界状态

| 层次 | 观察到的结果 |
| --- | --- |
| 外层 run | `run.json` 的 `phase=completed`、外层命令 `runner_exit_code=0`，表示适配器成功产出结果文件。 |
| 生成 | `experiment-result.json` 的 `generation.status=completed`、`generation_exit_code=0`；生成容器 exit 0。Braid `status=quiescent`、`reason=当前没有可执行工作`，Factory `process_exit_code=0`、`status=generated`、`phase=frozen`。 |
| 交付 | Factory 选取 `refs/heads/braid-delivery` 的确切提交 `7d35564476eefff2ef0073d86aeef41aee1018e3`，`delivery.json` 记录 `delivered`；导出物具备 `frontend/package.json`、`backend/package.json`。冻结应用与受评应用的源身份摘要均为 `014d3a363b9c7064c00b9e3655b52a1bd7bdee773ecb38715a14a2b16f296263`。 |
| 官方评分 | `evaluation_status=completed`，**34 项中 30 通过、4 失败，test_pass_rate=88.2%**；`feature_implemented_count=30/34`。`score=null`，因为本地空 Agent 评分阶段没有综合分数。评测容器 exit 1、结果内 `runner_exit_code=1` 对应四项 Playwright 失败，不是生成或交付故障。 |

分母是官方 34 个 Playwright test，不是 Agent 自检的 58 条断言。以上数据见 [experiment-result.json](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/experiment-result.json)、[Playwright 报告](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/template/.arc/playwright-report.json) 和 [官方 stdout](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/template/.arc/stdout.log)。输入 ZIP 的**实际字节** SHA-256 已对 `R/inputs/agent/pi-team-mixed.zip` 执行 `sha256sum` 核实为 `4f581ac51e485a767954976abc17764ff799bd2a64eadf707b671b65a4a47d6d`。外层 [run.json](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/run.json) 记录的 agent 输入 `sha256=d6643306…` 是输入身份的复合摘要，不能拿它当 ZIP 文件字节哈希；`014d3a…` 又是应用源身份摘要，也不是 ZIP 哈希。

## 四项失败及其可支持的原因

| 官方项目 | 直接失败证据 | 生成应用与 Agent 行为；因果判断 |
| --- | --- | --- |
| REQ-4.3.2 取消创建书架 | 在 `openShelfDetails` 的起始步骤等待 `Shelf 4.3.2`，超时；[页面快照](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/test-results/REQ-4.3.2-REQ-4-3-2-Cancel-Creation/error-context.md)中的书架列表没有该名称。 | 需求明确指定此初始书架；[seed.js](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-generation/template/backend/src/seed.js)没有创建它，生成时的数据也没有它。原生自检改用 `Shelf 4.4.2` 进入取消流程，故“取消不保存”自检通过未覆盖官方起点。**确定的初始数据遗漏**。 |
| REQ-6.1.3 删除草稿 | 官方 helper 从 `Book 6.1.3` 点 `Draft 6.1.3` 后再找 `Edit`，在此等待超时；[快照](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/test-results/REQ-6.1.3-REQ-6-1-3-Delete-Draft/error-context.md)已经显示编辑器及 `Delete Draft`。 | [BookDetails.jsx](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-generation/template/frontend/src/pages/BookDetails.jsx)把草稿直接链接到 `/pages/:id/edit`，没有中间阅读页的 `Edit`。Agent 自检从主页草稿列表直接进入编辑器并删除成功。**官方导航路径与实现不一致**；现有证据不能说删除操作本身失败。需求写的是“已在编辑页”，官方 helper 额外假设了中间 `Edit`，此差异须作为验收契约问题单独判断。 |
| REQ-7.2 从最近浏览跳转 | 官方 `clickNamed` 最终等待的是 `button Shelf 7.2`，10 秒超时；[失败时快照](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/test-results/REQ-7.2-REQ-7-2-Quick-Navigation-from-Recently-Viewed/error-context.md)却在 `My Recently Viewed` 内显示 `link Shelf 7.2`。 | [helpers.ts](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/helpers.ts)的 `firstVisible` 先即时探测 button、再探测 link；都暂时不可见便固定返回 button 定位器。主页数据由异步 `/api/home` 加载，[Home.jsx](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-generation/template/frontend/src/pages/Home.jsx)先显示 Loading。**推断**：调用发生在链接渲染前，helper 选中永不存在的 button；失败快照证明后来链接已出现。没有点击后的官方轨迹，不能据此断言实际跳转成功；Agent 自检用明确的 region/link 定位器通过了相近路径。 |
| REQ-8.1 收藏项目 | 官方点 `Favorite` 后等 `Unfavorite` 超时；[快照](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/test-results/REQ-8.1-REQ-8-1-Favorite-Items/error-context.md)停在登录页。 | 官方 [测试](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-evaluation/tests/REQ-8.1.spec.ts)未登录；[FavoriteButton.jsx](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/workspace/official-generation/template/frontend/src/components/FavoriteButton.jsx)对未登录用户直接导航 `/login`，因此不切换。需求 REQ-8.1 未规定登录前提。Agent 自检从 REQ-2.2 起一直使用同一个已登录浏览器会话，所以没有覆盖此状态。**确定的未认证路径不满足官方场景**。 |

四个失败都发生在评分应用的可操作界面；没有“入口失败使测试无法运行”的迹象。官方的第 7.2 项存在评分 helper 竞态的证据，但没有复跑或逐帧 DOM 时间线，故不把推断写成已证实的应用缺陷或评测器缺陷。

## Braid、SVC 与原生执行轨迹

Braid 对象库 `R/workspace/official-generation/template/.factory26/20260924-101125-e7d39675/braid-state/braid.sqlite3` 的[只读查询摘录](../../../runs/braid-usability-implementation/evidence/boundary-bookstack/braid-objects-query.json)显示，`local_items` 只有根 Issue #1，`local_comments=0`、`local_merges=0`；`assignments` 只有最初的 `@glm` 一次指派，`worktrees` 指向 `braid-delivery` 分支。根 Issue 结尾被 Agent 关闭，body 仍是初始需求，close reason 宣称 58 条自检覆盖全部场景。没有子 Issue、PR、讨论、评论 resolve/hide、工作项正文编辑或成员间反馈。`revision=2` 与 close 状态同在，不能据此推断需求正文被编辑。

第一段原生会话 `R/.../native/000-2026-09-24T10-11-45-329Z_01a0d2e6-5431-7670-9633-79e8f7b57680.jsonl` 记录了 Agent 读取 `braid context issue 1`，阅读 SVC skill 与 task-packet 指南，创建 `NOTES.md`，独自在根 Issue worktree 完成代码、自写 Playwright 检查、提交 `7d35564`、随后运行 `braid issue close 1`。其自检脚本只在一个 browser context 内连续执行：先登录；REQ-4.3.2 改从 `Shelf 4.4.2` 起步；REQ-6.1.3 从主页草稿链接直接进编辑器；REQ-7.2 明确等待 region 内 link；REQ-8.1 延续已登录状态。原生工具结果确实报告 `58 passed`，但这些与官方逐项独立情境不同，不能支持“REQ-1～9 全部官方场景通过”的关闭理由。

关闭后，Braid 因对象事件执行了一次 `context_resets`（`continuation=0`、`lifecycle=applied`）；第二段原生会话 `R/.../native/002-2026-09-24T12-28-50-992Z_01a0d363-d7b0-7416-b529-b774ea1b1583.jsonl` 从当前 Issue Context 读取 CLOSED 状态、检查提交和工作树，然后重述完成结论。这里体现了**上下文重建**，没有信息被整理后传给不同成员并改变决策或代码的证据；不能算有效讨论反馈。

新边界在此 run 中产生了可观察效果：没有任何 PR/merge，Factory 仍从请求指定的 `refs/heads/braid-delivery` 取得确切提交并导出、进入完整官方评分，Braid 的操作终态独立记录为 `quiescent`。但根 Issue 实际已关闭，因此本 run 只能证明“无 PR 不阻止导出”；不能单凭它验证“根 Issue 保持开放时也能导出”。单一成员完成任务，也无法据本 run 衡量多成员协作收益或分工成本。

## 下一轮应据此判断的少量事项

1. 边界修正已让这个无 PR 的应用进入 34 项正式评分；后续若要验证“开放 Issue 不阻断”，需有真实开放 Issue 且可交付的 run，不能从本 run 外推。
2. Agent 的自检覆盖声明高于实测覆盖：固定 fixture、逐项隔离登录状态和导航入口是三个具体缺口；当前工作流程指令没有自然形成讨论、上下文编辑或跨成员复核。是否要求这些协作步骤，应先基于产品价值决定，避免为展示机制而人为制造工作项。
3. 对四项失败，REQ-4.3.2 与 REQ-8.1 有明确应用/数据缺口；REQ-6.1.3 是官方路径与直接编辑实现的契约差异；REQ-7.2 需要时序证据才可归因。此次只读分析不修改生成应用或官方测试。
