# GitHub 组件成本假设：两条原始链的有界量化

2026-09-28，只读取 continuation-03 GitHub 的 Braid SQLite、原生 Pi JSONL 和 `origin.git`，没有操作冻结应用。问题是“没有组件/icon 库是否消耗实现时间，进而造成公开需求遗漏”。[因果复核](harness-causality.md) 已把此项列为间接成本假设；本页只量化共享基础 `039dbd5` 和前端 PR #12 的 `752a084`，不重查产品需求链。选择 PR #12 是因为其实现者 Issue #9 有完整原生会话；PR #2 本身没有独立 assignment，会混淆 Issue 作者与 PR 复核者。

原始根目录 `R` 为 WSL：

```text
/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--github-88884da4b94a0f/workspace/official-generation/template/.factory26/20260928-030347-78b10c07
```

Git 读取 `R/braid-state/origin.git`；SQLite 为 `R/braid-state/braid.sqlite3` 的 `assignments → agent_instances → provider_sessions → turns` 及 `local_comments`。下述 JSONL 均在 `R/work/native-homes/` 下。行数是 `git show --numstat` 或提交内文件 `splitlines()`，不是活跃编写时间；工具调用时间是原生记录的 UTC 时间，不把两个 commit 间隔当工作时长。

|链|提交中留存的前端规模|原生操作与返工|
|---|---|---|
|共享基础 Issue #2，`039dbd5`（05:05:38Z）|`frontend/src/components/` 有 7 个 TSX 组件、合计 252 行；6 个 CSS 文件（`App.css`、`index.css`、`HomePage.css` 与 3 个组件 CSS）合计 370 行。`StatusBadge.tsx` 内联 1 个 `<svg>`、8 个 `<path>`。它是早期共享 UI 的实际产出，不能把 44 个提交文件或依赖锁文件当组件成本。|初始会话 `pi-glm-fast-01a0e5fc-2562-7340-a006-4fae8b0168d6/2026-09-28T03-08-23-503Z_01a0e5fc-2a4f-77d5-9148-2e697493bbb7.jsonl` 在 03:23:14–03:27:55Z 批量 `write` 这些组件/CSS（如 `StatusBadge` call `call_ee5e70c7752742d1ab5d5446`、`App.css` call `call_3001df7579564b5aa25090c9`）。下一会话 `pi-glm-fast-01a0e658-fd50-7900-97e8-ff8124569ea6/2026-09-28T04-49-47-690Z_01a0e659-00aa-772c-878e-56bf31b49b8e.jsonl` 中，构建先于 04:51:10Z 报 `StatusBadge.tsx:8:92 Expected "}" but found "d"`；04:51:53Z `call_a62f7b525572435ea870732d` 把相邻 SVG paths 包进 fragment。04:52:01Z 再报缺失 `StatusBadge.css`；04:52:19Z `call_dda453e174d44b57a9a5f3a3` 删掉错误 import；04:52:31Z 构建通过。两次是可证的同一自制图标组件返工，但没有重写整套 UI。|
|REQ-6b Issue #9 作者交 PR #12，`752a084`（07:48:38Z）|相对父提交，`PullPages.css` 新增 217 行、`App.css` 新增 40 行，CSS 共 257 行；`PullPages.tsx` 与 `SettingsPages.tsx` 新增 893 行、删 34 行。该 PR 未改 `frontend/src/components/`，上述两个页文件无新增 `<svg>`。`frontend/package.json` 只有 React/React Router/Vite/TypeScript 等，无组件或图标包。|作者会话 `pi-deepseek-fast-01a0e6ec-e8f9-7c42-b57d-a0a4321a0b9d/2026-09-28T07-31-21-739Z_01a0e6ec-ec0b-70b4-8246-90832011ceaa.jsonl`：首个前端 `edit` 07:36:31Z（`call_00_wI2zNnQ0svdCLaPtlxrT3266`）；07:37:53/55Z 两个 `cat >>` 分别写入 217/40 行 CSS（`call_00_mWZOxsnOkRqYNGGBAakL9404`、`call_00_ET_pk9HyFg4CY0ltaAXPEbM4925`）；07:44:03Z `call_00_ET_E2DbeiN8cwXL3IjTJXU33871` 给 `.merge-reason` 加一行 `margin-left: 6px`；07:44:46Z `call_00_lVJjyROCRAp3zTHy3TFx3750` 改 `Review summary` 的可访问名为 `Reviews`；最后前端编辑 07:47:26Z。PR #12 的后来复核会话未见前端文件修改；复核与合并不构成 CSS 重做。|

对可计量成本，**下界**是两条链留下 370+257=627 行自写 CSS，以及共享基础 252 行 TSX 组件；这些是产出规模，不等于使用现成库本可省去的行数或时间。直接可见的 UI 修正至少包括 `StatusBadge` 两次编辑和 PR #12 的 CSS 一行微调、可访问名修正；其中 `StatusBadge` 从 04:51:10Z 的明确构建报错到 04:52:31Z 成功，观察到的故障解决窗口约 81 秒墙钟。这个窗口含模型思考、工具等待和两次构建；不能把它当 81 秒活跃编写，也不能将 03:23→05:05 或 07:36→07:48 的跨度当工时。原生轨迹可界定所选会话里的修改调用数量，却不能给全项目 UI 活跃时间、没有库的增量代价或可节省时间的上界。

反证也重要：共享基础的自制 SVG 只出现一处，两次修正后没有可证的大规模组件重写；PR #12 主要扩展已有 PR 页面，未重做共享组件，也没有新增 SVG。所选 Issue #2/#9、PR #12 的正文和评论，以及归属它们的 14 个原生会话的可见普通文本，均未出现“因组件/icon 工作耗时而省略某条需求”的明确取舍或省略记录。单凭 627 行 CSS 不能推断权限越权、PR Milestone 缺失或 reviewer `role option` 错误的原因；后两者与 [公开需求报告](public-requirements-followup.md) 中的任务范围和验收口径链更直接。未检查团队每一个会话，因此“未见明确语言”仅限这两条链。

决策结论：**能证明手写 UI/CSS 存在，并有一个很小的自制 SVG 构建返工；不能证明该成本挤掉了需求、导致 16/100，或证明换库会改善分数。** 若下一轮要优化视觉，先从实际截图和页面一致性缺口决定是否引库；当前修复优先级仍是需求交接与独立验收的已证问题。
