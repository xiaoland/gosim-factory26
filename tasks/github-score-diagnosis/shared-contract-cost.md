# Sheet 共享验证契约合并后的冲突成本

这份附录分析的是 **Sheet** 官网续跑 `3445926a1142` 的 Issue #5/#6、PR #9/#10，不是 GitHub 低分重评 `595ab74c90a9`。原先“共享契约合并后约 28 分钟排障”出自 [2026-09-27 耗时剖面](../acceptance-integrity/results/run-time-profile-20260927.md) 中 Sheet 的 13:07–13:35 窗口。精确口径为：PR #9 于 **13:07:04.751 UTC** 合入 `develop`，#6 于 **13:07:19.048** 发起 rebase，至 **13:35:41.842** 才提交最后一轮本地契约改动并启动浏览器回归；从 rebase 到启动回归是 **28 分 23 秒**的墙钟观察窗。快照截止 13:38:09 时回归未有终态、PR #10 远端仍是旧 head，故这不是“冲突已解决并交付”的耗时。

证据底座：`runs/e20260927-02-sheet-resume/g03/stop-preservation/20260927T133809Z/3445926a1142/workspace.zip` 内 `template/.factory26/20260927-082825-d9c4f6ea/braid-state/braid.sqlite3` 的 `local_comments`/`local_activity`、同包 `braid-state/origin.git` 的提交，以及 #6 原生会话 `work/native-homes/pi-glm-fast-01a0e2b1-5237-72a1-91b6-47e31e3fc19b/2026-09-27T11-47-49-663Z_01a0e2b1-5d1f-7137-a5a4-c4cf0a0ee5d7.jsonl`（下称 **#6 Pi**，行号指 ZIP 内 JSONL 行）。前驱实现会话是 `native/030-2026-09-27T10-01-17-464Z_01a0e24f-d398-73ea-9cdf-0bdef55f18c4.jsonl`。Pi 的消息间隔既不等于模型推理，也不等于进程运行；下表只在有调用/结果或进程自报时给执行时长。

## 契约如何分叉，以及合并前已有什么证据

| 时间 UTC | 事实与证据 | 因果含义 |
| --- | --- | --- |
| 10:13:47 | Braid `comment #40`（Issue #4）让 #4 负责验证规则形状和结构位移，#6 提供 `validateWrites` 钩子。 | 这是早期协作接口，尚非后来裁决。 |
| 10:26:01–10:30:12 | #5 `comment #71` 提出 `dropdown/numberRange + anchor/focus + allowedValues`、`validateEntries`、`PUT validation-rules` `{rules}` **整表替换**；根在 #6 `comment #78`、根 Issue `comment #80` 核对需求文案并明确以 #5 为契约源，撤回先前的 #6 钩子方案。 | 最迟 10:29 契约文字已经完整且有明确优先级；#5 源代码尚未发布到 origin，是后续可见性缺口，但不是需求语义缺口。 |
| 10:29:22–10:33:23 | #6 前驱 Pi 会话仍在写旧实现和 `dataops.spec.ts`（原生 `:126,140`）。#4 的 PR #6 于 10:32:21 合入 `develop@56a9324`；该提交 `backend/store.js:586,589,629` 仍为 `number-range/list + range + addValidationRule/validationViolation`。 | 旧形状先进入共享 develop，距新裁决约 3 分钟；后续 Agent 若以“当前 develop 已测试”为权威，容易把过渡实现误作最终契约。合入本身没有发现/阻断语义冲突。 |
| 11:48:03–11:55:35 | #6 Pi `:5-7` 执行 `braid issue view 6 --comments`，**实际读到** #71/#78；`:37,39` 正确指出新旧规则形状和整表替换差异。到 `:49,51`，因 #5 分支未 push、当前 develop 旧形状已有测试，改决定复用旧 `validationViolation`、`number-range/list + range`，把与 #5 的冲突留待集成。 | 不能归因于“指令未提供/未读”。这是读后在局部绿测压力下偏向已合入旧实现；#5 不可见加剧选择，但已公开的契约足以先对齐形状。 |
| 12:24:52、12:36:25、12:50:32 | #6 提交 `0e49dd5`（父 `46ff084`）固化旧形状。根直查后在 #6 `comment #109` 明列形状、校验函数、端点三项差异；`comment #118` 再说明**不必等 #5 合入即可对齐**。#6 Pi 在本续跑只在 11:48/11:50 读过 Braid Issue，12:36 与 12:50 后未见再次读取这些评论。 | 这是合并前两次明确预警。评论已发出不等于 #6 已消费；但 #6 早在 11:48 已消费原裁决，不能靠“后来通知未达”解释整个分叉。 |
| 12:58:08–13:07:05 | `6244148` 继续以旧形状补测；#6 Pi 在 13:03:37 读到旧分支全套 **27 passed (4.0m)**，13:06:19 push，13:07:05 建 PR #10。PR #9 仅 **0.617 秒前**在 13:07:04.751 合入 `develop@7ad4be2`；PR #10 当时 head `6244148`、base 已是 `7ad4be2`。 | 自检绿色只说明旧分支对自己的 oracle 一致；`checks/dataops.spec.ts` 当时仍用 `{rule}` 旧请求形状，未验证裁决契约。新旧 PR 到达顺序几乎同时，合入前强制比较目标分支契约是最后一道可左移的门。 |

这里的冲突有四层，不能统称 Git rebase 文本冲突：**文本层**是 `backend/store.js`、`docs/design.md`、`frontend/src/Editor.tsx`、`frontend/src/api.ts`、`frontend/src/styles.css`、`frontend/src/utils.ts` 六个 unmerged 文件（#6 Pi `:397-400`，共 10 处 conflict marker）；**API 层**是同一 `PUT .../validation-rules` 的 `{rule}` 单项 upsert 对 `{rules}` 整表替换；**数据层**是持久化 `validationRules` 的 `list/number-range + range + allowed` 对 `dropdown/numberRange + anchor/focus + allowedValues`；**语义层**是旧 `validationViolation` 与新 `validateEntries` 对所有写入路径的统一拒绝、undo 顺序和错误文案。CSS、utils、Editor 工具栏冲突还有相邻功能同时编辑的正常集成成本，不能全归验证契约。快照没有既有用户数据迁移试验，不能据此判断迁移影响。

## 13:07 后的逐动作关键路径

| 时间 UTC | #6 可见动作与结果 | 耗时性质 |
| --- | --- | --- |
| 13:07:11–13:07:34 | `git fetch` 首见 #5 merge，13:07:19 `git rebase origin/develop` 失败；13:07:23 列出六个冲突文件，13:07:34 数出 markers 并确认 `validation.js` 已在 develop（#6 Pi `:393-400`）。 | 从发起 rebase 到冲突清单 **15 秒**；这是纯 Git 文本冲突的首次诊断，不是 28 分钟。 |
| 13:07:47–13:16:55 | 读 `server.js`、`store.js` 冲突段和 #5 `validation.js`；13:16:55 第一次改 `store.js` import（`:401-412`）。 | 约 9 分 8 秒的**阅读/决策/工具消息观察窗**，其中 13:08:28→13:12:13 和 13:12:13→13:15:10 存在数分钟消息间隔，无后台进程记录，不能记为纯模型推理或空闲。 |
| 13:17:06–13:19:16 | 发现旧验证块仍残留、重复 `deleteValidationRule`；删除旧块并保留新契约，13:19:15 执行 `node` 加载与 `structure`/`formula-engine` 单测，13:19:16 返回 **17/17、42/42**（`:413-434`）。 | 约 2 分 10 秒混合代码修正与多次即时命令；后端测试调用到返回约 1 秒。59 项绿测只覆盖当时被调用的后端测试，不证明前端和 #6 数据验证 UI 已对齐。 |
| 13:19:27–13:27:55 | 逐文件消除 `utils.ts`、`api.ts`、`Editor.tsx`、`styles.css`、`docs/design.md` 的文本冲突，同时改前端保存规则为新形状；13:27:55 `git rebase --continue` 因 `EDITOR unset` 失败（`:435-474`）。 | 约 8 分 28 秒包含正常功能合并和契约迁移，非单纯 Git marker 清理；`EDITOR` 错误是工具环境小故障，下一条修正即可。中间 13:19:47→13:21:09、13:21:14→13:22:48 有无调用间隔，未归因。 |
| 13:28:02–13:28:46 | 用 `GIT_EDITOR=true git rebase --continue` 越过编辑器问题，随即第二个提交 `4eae331` 在 `Editor.tsx` 再冲突；13:28:46 合并状态同步逻辑后显示 `Successfully rebased`，本地 head `eca0ba7`（`:475-484`）。 | 编辑器修正到本地 rebase 成功 **44 秒**；13:07:19→13:28:46 的整个 rebase 墙钟为 **21 分 27 秒**，其中实际 `git rebase` 命令均几乎立即返回，时间主要是人工/Agent 的冲突判断与编辑，纯推理时间未知。 |
| 13:29:28–13:31:35 | 后端 17/17、42/42 再过；前端构建在 13:29:38 报旧字段 `allowed` 和旧 `number` 联合类型错误。13:30:16 读出 `Editor.tsx` 仍按 `rule.range`/`list`；13:31:25 修 hooks 与 dialog，13:31:35 构建通过（Vite 自报 **2.65s**，`:485-492`）。 | rebase 绿不等于契约绿。13:28:46→13:31:35 为 **2 分 49 秒**的后置静态验证/修正窗；首次构建调用约 10 秒，第二轮的整体命令约 10 秒，其余消息间隔不可归因。 |
| 13:32:45–13:35:41 | 读 `checks/dataops.spec.ts` 发现仍发送 `{rule}`；13:35:00 改为 `{rules:[...]}` 和新字段，13:35:41 本地提交 3 文件、17 增 6 删，并以 `CHECK_PORT=4381 nohup bash checks/run-checks.sh > /tmp/checks-run8.log` 启回归（`:493-500`）。 | 约 **2 分 56 秒**，混合测试 oracle 修正、读文案与提交。13:32:45→13:35:00 的 2 分 15 秒没有可见工具执行，不能称测试耗时。 |
| 13:36:28–13:38:09 | 13:36:28 首次读到第 3–6 项通过，13:37:47 读到第 5–8 项；快照截止时无最终退出码、PR #10 未推新 head。根 `comment #145` 在 13:35:07 已看见本地 rebase，但确认远端还是 `6244148`。 | 回归与结果读取和其它 Agent 评审并行；`/tmp/checks-run8.log`、`nohup` 进程最终结束时间不在快照中。**不能**把 13:35:41 当作完成验收或可合并时刻。 |

PR #10 的阻塞评审（`comment #136` 13:21:25、`#138` 13:26:52）发生在 #6 解决本地冲突**同时**，基于远端旧 head `6244148`；不应把两条评审各自再加作顺序成本。PR #11 的旧 API 声明清理 13:24–13:26 合入 develop 也与 #6 rebase 并行，改变了后续基线，但非这 28 分钟的额外可加时间。ZIP 的 #6 PBB session `612cd009e565c23747b5ba1b` 有 `bg001`–`bg014` 元数据，最晚 job 从 12:56:01 开始；**13:07–13:38 没有对应 PBB job**。Pi 中 13:35:59/13:37:18 的 `sleep 29` 是等待后台浏览器检查，不能相加；这次回归由普通 shell `nohup` 启动，ZIP 未包含 `/tmp/checks-run8.log`，只可用两次 `grep` 输出夹定进度，不能造出进程结束时间。

## 对 Harness 与协作流程的决策

最可改变的触发点在 **11:55**，不是 13:07：#6 已读裁决并能准确复述，却因为 #5 实现未公开、旧 develop 已合并且可测试，主动选择旧契约并把冲突推迟。应由 Harness 的**外部协作规则/工具**为跨 Issue 契约记录“裁决版本、权威来源、被废弃形状、依赖 PR”，在子 PR 创建和合入前自动比对目标 branch 与该决策；目标分支上若仍是过渡形状，明确禁止用该形状的绿测替代契约验收。#5 可被要求尽早发布可读的契约提交或文档，不必等完整功能 PR；#6 则应在拿不到实现时按已公开的请求/数据形状构造验收，或标明依赖、暂缓 PR，而非提交旧形状。这些是提示词和 Braid/Harness 外部工作流建议，**不是**预制或改写生成应用源码。

最小区分检查可只读重放冻结证据：在 11:55 的 `origin/develop@56a9324` 与 `comment #78` 上跑一份外部契约差异报告，应同时检出 `number-range/list`、`range`、`addValidationRule` 与 `{rule}`；若检不出，工具方案不足。然后在 `PR #10@6244148 → develop@7ad4be2` 上比较文本冲突清单与契约差异，验证门槛能在创建 PR 前报出**语义**风险而非仅事后 `git rebase` 报 marker。现有单次运行不能量化该工具能省满 28 分钟，也不能推断模型能力差异；即使契约提前对齐，Editor/CSS/utils 的相邻功能合并仍有成本。
