# attempt-08 Sheet 进展与检查成本

只读截面：2026-09-28 06:59–07:01 UTC（北京时间 14:59–15:01）。增量原生窗口从本轮新父会话约 06:44:29 起；旧 Git 提交与评论仅作基线，不计为 08 新完成。未运行应用检查、探针或模型，未改运行、源码或应用，未提交。下文检查均为参赛 Agent 已实际执行的原生记录。

证据根 `R`：WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/generation/runs/pi-braid--hackathon--sheet-d478f7dc8ff84f/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`。状态来自只读 `braid-state/braid.sqlite3`、`status.json`；提交由 `git --git-dir R/braid-state/origin.git log` 与 worktree 的 `git status/log` 独立核对。原生定位以下列 session UUID 在 `work/native-homes/*/2026*.jsonl` 查找，并按时间定位 toolCall/toolResult；不以评论的 PASS 作为唯一依据。

## 当前判断

有真实进展，但尚未收敛成完整候选：13/14 个 PR 已合并，只有 PR #9 开放；Issue #1/#4/#5/#7 仍开放，#2/#3/#6 已关闭。**合并数量掩盖三条功能链仍未汇合**：REQ-2 结构恢复、REQ-3 moveCells、REQ-5 数据组织。`develop=266f0e4`（06:51:53，Merge PR #14），`main=3ab688f`（02:58:01，初始仓库），还没有最终 main 交付。

检查/环境工作占据显著活动，但本截面不能量化为总投入占比，也不能说功能工作停了。REQ-5 的失败检查已修正并继续推进，moveCells 已通过一轮检查又因共享基线改变进入干净克隆复验，REQ-2 仍在调查实际失败。现有证据支持“关键路径逐渐明确、检查成本仍高”，不支持“设施已经完全修好”或“所有检查工作都是过度工程”。

## 三条产品关键路径

| 工作 | 可核实增量 | 当前未完成项及判断 |
| --- | --- | --- |
| Issue #4：REQ-2 生命周期/行列与结构 undo | 父 `01a0e6c2-02f3-7691-b2eb-6e9ba9b726f0`；06:56:37 构建退出 0、unit 13/13。最新工作树 `c348970`，前两提交 `1816e28` 补结构恢复检查、`164707c` 将结构快照接入共享 History | 06:57:23 执行 `node checks/api-req2.mjs http://127.0.0.1:3501`，06:57:32 实际结果 **52 passed, 2 failed**：删除第 1 行后 Region 应消失、恢复后 cells 应等于快照。前面连接拒绝已改用新 seeded server 再现，故不能继续归咎环境。06:58:17 调试显示恢复 200、删除 200 且坐标发生移动；尚不足判定实现还是用例前提错误。未有最终 PR/通过证据 |
| Issue #5：REQ-3 moveCells | 父 `01a0e6c2-187b-710b-bf5b-71187eb36207`；06:57:56 读取真实 checks 日志：**31 passed / 1 skipped，10.0m**，PBB 原 job exitCode 0。其中 numeric validation 拒绝非法目标移动的用例通过；skip 是等待 REQ-2 的结构 undo | 通过之后 06:57:59 合入最新 develop，远端新 head `issue-5-range-move=21b627b`，修改 9 文件、481+/89−。先前 PASS 不自动覆盖合并后候选；06:59:31 干净 clone backend install 成功，06:59:59 checks install 成功，随后在 `/tmp/issue5-clean` 重跑套件，本截面无最终结果。尚待发布 PR、合入与取消结构依赖 skip |
| Issue #7 / PR #9：REQ-5 排序/筛选/验证/透视 | 父 `01a0e6c2-2695-7043-b45f-3f741f770ccc`；06:56–06:57 下拉验证经粘贴/移动拒绝的用例失败；随后 `7ca55a7` 修正检查读取 `.gridcell-value` 与初始值 North→East。06:58:18 定向 **1 passed / PLAYWRIGHT_EXIT=0**。06:59:35 全量日志：前后端 build exit 0、core unit 20/20、contract parity 3 pass/1 skip、CSV filtered-out rows unit 7/7、API **84 checks ALL PASS** | 06:59:35 开始 10 项浏览器检查，本截面无总结果；contract parity 的 skip 原因未在本次展开，不当完整覆盖。工作树已有 `7ca55a7`，origin 的 PR head 仍 `65b4f57`（06:00:26旧提交）。需发布 rebase 后候选、实际回归证据与合并；不能把本地通过当远端已交付 |

REQ-2 父怀疑 PR #12 移除陈旧 dist 后从源码构建引擎导致差异，目前只有猜测与 diff 调查，不能写成已确认引擎回归。真实新 server 上复现两项失败足以说明有待解决的问题，但还不够确定产品根因。

三条链共享 `EditorPage`、结构元数据与 validation。根评论 #120–123 指出消费唯一 validation/bootstrap 实现、去掉已合入 undo cherry-pick 和重复自举，属于具体整合协调。评论 #125 列出的关键路径与 Git/native 相符：PR #9 及 #4/#5 收尾 → develop→main 整合 → 最终候选的完整行为验收。F3 复制偏移、筛选隐藏行仍导出、结构 undo 等跨模块行为目前仍需要最终集成证据。

## 检查设施与环境：哪些工作有根据

| 事项 | 非评论证据 | 分类与边界 |
| --- | --- | --- |
| 干净构建自举 | PR #12 merge `0b18726`，head `6043193` 于06:45:35仅补共享脚本 executable bit；历史 `b17ca0f/5159262/33b51b9` 已加入前后端共享 bootstrap、依赖安装及移除入库 dist。Git 可确认实际进入 develop | 是交付/平台顺序风险，不是单纯测试美化。评论 #119/#126 称干净 clone 构建启动及公式 API 成功；本次未完整抽取该两个后台原始检查日志，保留“提交已整合，全部通过细节依评论待深核”的边界 |
| watchdog/cleanup 竞态 | PR #10 的 `fcbb114`（05:54，属旧窗）改 run.sh 30+/6−；08 新 `6b34914`（06:50:24）只加 115行 cleanup-race-check.sh + README。Issue #3 父 `01a0e6c2-0361-7254-b391-9b84cfe2a710` 的06:50:18直接读取PBB日志，两轮都有 `RACE_CHECK_PASS`、`RUN1/2 EXIT=0` | 可重复清理竞态检查有实际场景。首轮 victim 单次采样失败是检查自身竞态，后来短重试修复。当前已合入；无需仅因理论上还可增加 `/proc` fallback 就扩大。评论 #127主动拒绝无证据扩展，体现一次收敛 |
| 全套 passed 但退出1 | PR #8父 `01a0e6c2-0361-74a9-b028-1555086e918d`；06:59:02读取本次 `checks/results/20260928T064924/.last-run.json` 为 passed，而日志有 EXIT=1。06:58:47现成Playwright最小检查1 pass+1 fixme得到退出0，排除了“skip必然退出1”。06:59:38真实shell语义复现：`set -euo pipefail` 中以 lsof 无listener结果赋值会退出1，06:59:48复制 cleanup 模式仍 PROBE_EXIT=1 | 是生成应用 `checks/run.sh` 的具体假失败，不应靠忽略退出码处理。日志证明调查在收敛到窄根因，不能把它与产品失败混算。是否已有最终修补，本截面未证；不需 Factory 接管生成应用脚本 |
| CSV Chromium 启动失败 | 同 Issue #3父06:54:49读取真实日志，06:54:09 Chromium FATAL：`Socket path too long: /workspace/template/.factory26/.../work/tmp/org.chromium.Chromium.../SingletonSocket`。短TMPDIR后06:56:12结果 **3 passed (52.5s)、CSV_PROJECT_EXIT=0** | 环境故障；不能视为CSV产品失败。该问题对绕开应用 run.sh 直接调用浏览器的工具链仍可复现，是本轮最具体的 harness 可改候选 |
| REQ-5 拒绝检查 | 失败断言期待 A2=North，实际需求种子为East；`7ca55a7`同时改成读取值span，定向重跑通过 | 有判据/DOM目标证据支持的检查修正，不是为了当前实现随意改需求。仍须等10项UI全量及集成结果 |
| 公式栏重复undo | `b06d22f` 在 FormulaBar 加10行、检查加27行；PR #13已merge `3e55813`（早于08的基线） | 真实产品行为修正已存在，不应在moveCells新分支再次 cherry-pick同一改动；08的去重提醒合理 |

`.last-run.json=passed` 只描述 Playwright 部分，wrapper 失败仍要解释。反过来，cleanup 返回1也不能把已经观察的产品用例全部说成失败。应保存这两个层次直到窄缺陷修好。

## 重复与过度工作信号

确认有重复风险，但没有证据支持一刀切停掉验证：

- PR #14 评论 #116承认另一个成员一度准备相同检查脚本分支，发现已有PR后删除；Git最终只合入一个脚本。这是已识别并收敛的协调成本，不是两份持久重复实现。
- root要求 #4去掉自带 bootstrap、#5去掉已合入 undo提交、#9消费唯一validation，说明共享契约跨分支漂移正在消耗 rebase/复验成本。需以合入后的唯一实现为完成条件，而非继续各自维护替代版本。
- moveCells的10分钟局部套件刚通过即因合并新baseline复验，成本高但有代码变化依据；不宜称无意义重跑。对于未受影响的旧结论，保留提交/条件可降低无差别重做，最终集成仍有必要。
- #6已关闭后多个新父会话在06:56–06:59继续读取旧bootstrap请求并说明已交付，显示滞后评论消费成本；只据此不能判Braid投递bug或“空转”。通知/接续专项由另一审查负责，本页不重复归因。
- 多条lane同时运行浏览器套件，加上4GiB/2CPU既定环境约束，使等待/启动/竞态暴露增多；本页没有采集资源利用率，也不能从并行事实直接证明每次失败由资源竞争造成。不能只增超时或加watchdog作为默认答案。

## 可修 harness 根因与下一步判断

本轮最明确的 harness 候选是**全局 TMPDIR 过长与 Chromium Unix socket 路径限制不兼容**。当前本地 `variants/pi-braid/run.py:178` 将 TMPDIR 指向 `work/tmp`，原生Chrome FATAL指向同一路径。应用 run.sh的短路径绕过帮助了它自己的调用，但直接Playwright等其他入口仍踩坑。可在设施侧评估一个稳定、按运行隔离且足够短的临时根，并保留恢复时Pi子任务临时状态的归属；不能粗暴共享 `/tmp` 或单为浏览器更改已恢复子任务的查找根。本页仅提出边界，不实施，也不要求新探针。

wrapper 的 lsof/set-e、共享引擎源码与dist、具体检查初态属于生成应用自身闭环。没有必要把这些题目级细节写成新的 Harness SOP，也不能由开发代理直接替参赛Agent修应用。当前最有价值的观察条件是：REQ-2两项失败获得明确归因并收敛；moveCells/REQ-5发布验过的新head并合入；新develop候选取消未满足依赖的skip，完成对应跨模块路径；main从初始提交前进。只要这些在推进，检查数量多本身不足以宣布停滞。

本报告最后事实截面为07:01:05 UTC；之后的完成/失败不在此结论范围。没有最终得分、全需求PASS或交付完成证据。

## 07:18 UTC 追加：退出码假失败已由 Agent 修复

用户新增授权允许在本地热修时替 Agent 修生成工作区；本次先只读核对，结果是**无需另写补丁**，也未动运行中的工作区。

确切修复提交 `1be21ec1f9dbf8fe8306203e8e6911a37453f7f7`，作者 `@deepseek-10`，07:01:36 UTC，分支 `fix/check-run-exit-status`。PR #16 已 MERGED，07:14:22 合并提交 `1d7eca71b94fb963801df53064fde78016046896` 的父分别为旧 develop `266f0e4` 与修复 `1be21ec`。只读 `git branch --contains 1be21ec` 确认 develop、REQ-5远端分支和moveCells分支都已包含该修复；main仍是初始 `3ab688f`。

修复落在公共 helper `checks/run.sh:73` 的 `listener_pid()`：`lsof ... | head -1` 后加 `|| true`，并解释调用方以打印的 PID（无监听时为空）判断，不以 lsof 的无监听退出1判断检查失败。调用点覆盖 cleanup 第125行、`start_owned_server` 启动等待第154行和 watchdog 第210行；无需分别修三个位置。EXIT trap仍在第132行，套件仍由第269行 `exit "$EXIT"` 返回检查状态，未改业务断言或expected。该提交同时新增72行 `checks/run-exit-status-check.sh` 和README入口；这是运行中Agent已有改动，本次没有添加或运行测试。

两个原生非评论证据支持修复：

- 父 `01a0e6c2-0361-74a9-b028-1555086e918d`，07:01:06 toolResult：用旧 `origin/develop:checks/run.sh` 得 `RUN_EXIT_CHECK_FAIL: listener_pid() failed the script for a port with no listener`、`EXIT=1`；当前修复文件得 `RUN_EXIT_CHECK_PASS`、`EXIT=0`。
- 父 `01a0e6c2-312c-736d-9ed2-308d3cbdcd96`，07:14:57 toolResult：工作树切到合并commit `1d7eca7` 后运行已有短回归，得 `RUN_EXIT_CHECK_PASS`、`EXIT_CHECK_EXIT=0`。这证明窄退出码行为已验证，不冒称新最终候选的整个浏览器套件已通过。

07:18截面的实际工作树并不都在新基线：`issue-2/pi-glm-fast-g1=1d7eca7`、`issue-5/pi-deepseek-fast-g1=8e0b036`、`issue-7/pi-deepseek-fast-g1=8099339` 的 helper已修；`issue-4/pi-glm-fast-g1=a19e005`、`pr-15/pi-deepseek-fast-g1=21b627b` 仍旧版本。原发现者 `pr-8/pi-deepseek-fast-g1` 当前回到 `2ecf101`，也不含修复，但修复提交已在独立分支/共享develop发布，不能据此说改动丢失。

调用方还包括README所列整体检查入口，以及 `checks/cleanup-race-check.sh:52` 启动 `checks/run.sh --skip-build`；新 `run-exit-status-check.sh:23` 默认读同仓run.sh。在旧工作树或已经开始的旧检查进程中继续观察到EXIT1，不足以推翻新helper的修复，先核对所跑候选。09热停后应保存既有历史，按正常集成关系消费含PR #16的新基线；不要把同一补丁再次套入各工作树，也不要在运行中替换脚本。若09另有生成工作区热补丁，应单列为允许的本地例外，不包装成纯Harness效果；本项目前没有开发代理新增应用修改。
