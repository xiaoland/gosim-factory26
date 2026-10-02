# K3 根 Issue Agent 对照

## 当前调查：干净重放 14/100（2026-09-26）

用户要求重新分析 [`e45e4ae7110d`](https://arc-bench.com/runs/e45e4ae7110d) 的低分；随后要求由 `5.6-luna / medium` 操作浏览器、随验收记录，并优先复用或改进已有 GitHub 应用验收。当前范围是结果调查与生成应用验收，不启动新的生成或官方评测，不修改参赛 Harness。

当前状态：调查与 10 项定向自动复验已完成，结果为 3 passed、7 failed、0 blocked，已归档原始证据并清理本次运行资源。完整结论见 [14/100 重放报告](results/e45e4ae7110d.md)。下文保留随调查更新的发现和阶段记录；应用验收代码未提交。

已确认：重放源码与 `4c17843` 冻结应用的 73 个文件逐一相同；无生成模型调用，正式后端正常监听 `0.0.0.0:3000`，没有旧 run 的端口冲突。官方结果 14 通过、86 失败、功能项 4/47。因而旧服务污染不能继续作为严重低分的主要解释；11→14 的净差也不等于恰好有 3 个测试由端口修复。

隔离复现使用 WSL Docker 中的原样应用、新数据库，映射到本机 `127.0.0.1:43017`。已由浏览器观察确认：

| 需求/边界 | 当前观察 |
| --- | --- |
| REQ-3-3、REQ-2-1-1 仓库标题 | `acme-demo / acme-docs Public`，不包含连续的 `acme-demo/acme-docs`；这是共享入口的契约偏差，是否导致官方场景连锁失败仍属推断。 |
| REQ-3-2-2 Fork | `button` 精确匹配为 0，实际为 `link`。 |
| REQ-2-1-1 组织筛选 | `Find a repository` 实际为 `searchbox`，需求指定 `textbox`。 |
| REQ-5-3-1 指派 | `Search assignees` 实际为 `searchbox`；选中后 option 名称带 `✓ `，精确用户名定位失败。实际点击 carol 后保存成功，刷新仍在，但选项名称变成 `✓ carol-maintainer`。 |
| REQ-4-2-1 历史入口 | 概览链接名为 `Commits 3`，精确 `Commits` 链接匹配为 0。 |
| REQ-6-1 Checks | PR 默认页没有 Checks region 或 `test status` combobox；点击 Checks 进入子页才出现 `test: pending` 和状态控件。 |

原生 PR #4 自编 E2E 确实产生 156 PASS，但其文件明确仅覆盖 REQ-5/6；`hasctl` 只查名称字符串，主要流程直接打开内部路径。行 199 把选项定位从 `option` 放宽为 `button|option`，移除了角色约束；匹配用户名尾部也接受 `✓ username`。Checks 检查直接打开 `/checks`，跳过默认页要求。应区分工具快照角色转换的适配与需求验证，不能由脚本通过推导完整契约通过。

源码另发现团队种子将 bob-reviewer 预先加入 frontend-team，与 REQ-2-2-2 的待添加前提冲突；这一项尚无独立 UI 复现。Luna 因子会话看不到主会话 tab、且没有可用 IAB provider 而未能继续；Reviewers 控件后来由自动套件确认。

证据目录：[`replay/analysis`](../../runs/competition-budget/20260926/replay/analysis/)，含官网 status/logs、公开需求、逐文件比较、PR #4 自编脚本及定向原生片段。下一步：定位并复用已有 GitHub 应用验收套件，将上述已知偏差对照其覆盖范围；必要的改进限于生成应用的验收，不引入 Factory 自身测试。收尾须停止本次临时应用及 SSH tunnel，并形成结果报告。

已定位 `benchmarks/hackathon/github.spec.ts`、`support.ts` 及 `experiments/hackathon-local/matrix.py`。现有套件的共享导航直接要求首页存在 acme-docs 链接，公开需求允许通过全局 Search 进入，当前应用首页也没有该链接；因此原样运行会把大量功能挡在测试自身假设上。另有组织入口、Fork 未登录、Reviewers 未检查 textbox、Checks 只看设置文本等覆盖不足。先冻结现有套件，对登录、搜索、组织浏览、Issue 读取运行 4 个独立本地 Runner 场景，保留原结果；随后仅修正本次发现的导航假设，并加强已获得独立观察的契约检查，重跑相关场景。每场景从同一冻结应用独立启动，源应用不变，不推算官方分数。

Luna 所在子会话没有可用 IAB provider，已保存阻碍记录；后续 UI 取证由用户指定复用的 Playwright 套件完成，不再扩大主模型手工操作。

原套件的 4 场景已完成：登录通过；搜索因 `/acme-docs/i` 同时匹配源仓库和 fork 而发生 strict-mode 异常；组织浏览停在未规定必须有的首页 Acme Demo 链接；Issue 读取停在首页仓库快捷链接。后三项均不能作为应用业务失败。原始 Playwright phase 附件和错误保存在 WSL `/tmp/factory26-replay-e45-analysis/baseline/runs/`。同时发现当前工作树的 ARC adapter 将退出码 1 的已完成失败评测概括为设施失败，尽管 `evaluation_status=completed` 且完整 Playwright 结果存在；本次直接读取原始附件归因，不修改另一任务正在变动的设施。

已在现有 `support.ts` 修正共享仓库导航，`github.spec.ts` 修正模糊搜索、组织入口及 Fork 身份前提，并加强仓库标题、精确 Commits、指派选项、默认页 Checks、Reviewers 搜索与刷新保持。后续定向运行 10 项：登录、搜索、组织浏览、Fork、仓库概览、历史、Issue 读取、指派、Checks、Reviewers。未选的 37 项不计为通过，未将整套套件称为已完整校准。

定向复验已完成的前 6 项：登录、仓库搜索通过；组织筛选缺 `textbox Find a repository`、Fork 缺 `button Fork`、仓库概览缺连续 owner/name heading、历史缺精确 `link Commits`。四个失败均到达目标验证阶段，错误与此前独立浏览器观察一致，没有再停在首页假设。原始记录位于 WSL `/tmp/factory26-replay-e45-analysis/targeted/runs/`；其余 4 项仍在执行。结果解释草稿已写入 [重放报告](results/e45e4ae7110d.md)。

**本次调查已完成。** 10 项定向复验最终为 3 passed、7 failed、0 blocked；通过的是登录、仓库搜索、Issue 读取。后三个失败分别为指派 textbox、PR 默认页 `test: pending`、Reviewers textbox 不存在。完整错误、前后 suite 哈希和逐例身份已保存至 [`local-suite-results.json`](../../runs/competition-budget/20260926/replay/analysis/local-suite-results.json)，14 次运行的原始 JSON、trace、截图与清理记录已同步本机。全部所属 Runner 容器均为 absent；手工取证应用已停止，SSH tunnel 和临时页面已关闭。最终结论与证据边界见 [重放报告](results/e45e4ae7110d.md)。已知 adapter 摘要口径矛盾留作设施任务后续处理；未选 37 项和失败后的步骤均不宣称通过。本轮应用验收改动尚未提交，未修改冻结应用或参赛 Harness，也未启动新生成或官网评测。

## 原实验与历史记录

用户授权原话：“同意，加一个k3做根issue agent的variant然后重跑试题看看。”

目标是检验更强的根 Agent 在完整 Hackathon GitHub 任务中，能否更好地组织工作、判断最终产物的验收证据，并改善官方得分。此项是模型对照实验，不视为验收失真的通用修复；[通用方案](../braid-collaboration/acceptance-design.md)另待复核。

## 对照与冻结

- 控制组：2026-09-26 已完成的 `pi-team-mixed` 官方 GitHub run [`b77e4357a4e1`](https://arc-bench.com/runs/b77e4357a4e1)，冻结包 SHA256 `3440b95605ba7b5a3df606438becff3d2b2f0741673d6f32f5b5d4d29b527609`，4/100。
- 实验组：独立 `pi-team-k3-root` variant，以控制组的冻结源码、技能、支持模块、Linux runtime 为基底，只新增 K3 根 profile，并将 `root_profile_id` 指向它。原 GLM、DeepSeek profile 和内部角色保留。Braid 的可指派列表将多一个 K3 profile；实际子工作项的模型分配必须记录，不能把此实验误称为严格的根模型单变量对照。
- 不引入专门针对 GitHub/Web 的完成规则，不混入待复核的独立验收 Agent 提案，也不修改原冻结包。

## 实验与判断

先比对新包与控制组的运行文件、技能和支持模块，再使用官方比赛入口、`official_evaluation`、同一 GitHub 需求重跑。保留 submission、run、最终提交、Braid 工作项和 Pi 原生会话证据。完整评分后先向用户报告并停止；Sheet 仍受旧暂停 run 占用，不把 GitHub 结果冒充完整双题 bench。

报告同时回答：最终应用是否生成并被评分，官方通过数/总数及耗时，根 Agent 是否在最终集成提交上实际进行足以支持完成声明的结果验收；具体用了哪些工具、覆盖了哪些用户可见行为，有无把局部分支或 API 检查当作整体交付证据。模型并非唯一可能影响因素，单次运行不证明稳定因果收益。

当前状态：独立 variant `variants/pi-team-k3-root/` 已建立，使用控制组冻结 `run.py`、Agent 材料、技能和 Linux runtime；与控制组包清单的 22,524 个原有文件逐项比对，只有 `run.py` 改变，另增 K3 profile。新包位于 `runs/k3-root-experiment/20260926/pi-team-k3-root.zip`，SHA256 `dbed5665e92948c5d3fe4147a8313e42c12c7a92592021250438f662474eb5bf`。
官方 journal 是 `runs/k3-root-experiment/20260926/official`，`official_evaluation` submission `4318424173a5`，GitHub run [`7b533d7bd71b`](https://arc-bench.com/runs/7b533d7bd71b) 已于北京时间 12:39 完成，官网为 11/100。最新状态与完整工作区包保存在 `runs/k3-root-experiment/20260926/analysis/`，详见[结果分析](results/7b533d7bd71b.md)。正式后端启动出现 3000 端口冲突，生成期间的旧 PR 服务不在 Factory 清理范围内，因此分数不能直接代表最终交付在干净环境中的质量。根 Issue 仍 OPEN 且没有最终验收回合；Issue #5 的实现未进入 PR #4 分支，后者重新实现并验收，造成显著重复工作。本轮冻结包未包含 `pi-background-bash`。`billing_mode=self_funded` 与请求模式不一致，原样保留而不猜测计费。用户本次授权仅为结果分析，尚未修改源码或运行复评。

2026-09-26 11:10 的只读观察：官网仍为 `RUNNING`，评分尚未启动；[工作区快照](../../runs/k3-root-experiment/20260926/official/tasks/hackathon--github/template-bundle-live.zip)中的原生会话显示 10:57 仍在修改代码。Braid 已关闭子 Issue #2/#3/#4，合并 PR #1/#2/#3，PR #4 仍在执行。根 K3 Agent 明确将 Issue #5 指派给 `kimi`，Issue #5 的 K3 Agent又以 `braid pr create ... --assignee kimi` 指派 PR #4。因此本次 K3 不限于根 Issue，不能解释为严格的根模型单变量对照；截至快照，K3 还承担了共享基础实现、Issue #5 设计实现和 PR #4 复核/继续实现。原生记录证明 K3、DeepSeek V4 Flash、GLM 5.3 Flash 在同一官网 run 中有真实模型响应；没有观察到 Context7/Exa 查询，不能判断这两项外网工具可达性。`official_evaluation` 提交与 `self_funded` run 字段不一致，实际计费路径尚未核清。

2026-09-26 12:14 的只读观察：官网仍为 `RUNNING` 且评分未开始，但官网 `/source` 返回的 [Pi 原生会话](/Volumes/WorkSSD/Development/factory26/runs/k3-root-experiment/20260926/official/tasks/hackathon--github/observations/pi-live/20260926T041405Z-pr4-k3.jsonl) 比旧工作区快照更新。PR #4 的 K3 Agent 在 12:06 完成一轮自编浏览器 E2E，输出 `PASS count: 150` 和 13 条 `FAIL`；其中若干为脚本按 `option` 寻找实际是 `button` 的选项。它随后检查 Reviewers 控件、修正脚本，并于 12:09 发起使用新数据库的完整 E2E 重跑，命令超时为 1500 秒。截至 12:14，Pi 会话尚未写入该命令的结果。这些数字仅是 Agent 自编验收脚本的断言，不是官网评分，也不能由此断言应用全部通过。

12:17 官网完成打包的 [完整工作区快照](../../runs/k3-root-experiment/20260926/official/tasks/hackathon--github/template-bundle-1217.zip) 已保存，SHA256 `46ee0dde0ba2affb5d0bd11623d868f42cb9f067795983816522339d25b8eeb5`。其中 Braid 数据库确认 3 个 PR 已合并、PR #4 与 Issue #5 仍开放；包内 PR #4 的 Pi 会话只到 12:01，晚于此的进展应读官网 `/source` 的实时原生会话。后续下载工作区包应允许官网 2–3 分钟打包，不因短暂无响应判失败。
