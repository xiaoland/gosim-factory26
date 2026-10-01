# Keep：原入口未交付；同一合入应用补评测通过 19/32

冻结 run：`pi-team-mixed-arc-bench-lite-keep-23563f65f4`，Agent ZIP 原始 SHA-256 为 `8b7c37b7d3097a0d12e14bb4c66170743d7f9d41e3bd443f227b3726073f6b9d`。`run.json` 的输入摘要 `7028ac…` 使用本地实验器的“文件名 + NUL + 文件内容”算法，不是普通 `sha256sum`，两者不矛盾。本报告判断该冻结 run 及后来从其已合入提交提取应用做的独立补评测；没有读取评分测试源码、修改应用或重跑生成。

## 失败链与处置依据

生成阶段运行约 3,838 秒。Runner 正常组装环境，安装 Agent 依赖成功，密钥与 base URL 均被识别；`generation-agent` 最终 exit 1。其原始异常是 `RuntimeError: braid local 退出 1；见 braid.log`。Braid 在 08:54:22 UTC 报 `local run incomplete: 无后续可执行工作；根 Issue state=CLOSED reason=Some("Keep … 已通过 PR #1 …")`。当时 PR #1 已 MERGED、根 Issue #1 已 CLOSED，`active_turns/pending_batches/blocked_groups/unresolved_merges` 均为 0，但 `braid-state/result.json` 的 `status=incomplete`、`delivery_commit=null`，`local_run.lifecycle=running`。适配器因此记录 `stage=generation`、`Agent generation did not produce a complete application`；分离评测没有启动，分数为 **无**，不能当作低分。

直接触发是根 Issue Agent 在 08:53:06 调用 `braid issue close 1 --reason "Keep …已通过 PR #1 …"`，没有使用旧契约的字面值 `completed`。冻结版本的 `src/local.rs` 和 `src/objects.rs::seal_delivery` 只在 `reason == "completed"` 时认定交付；`objects.rs::lifecycle` 却接受其它非空关闭理由，只对 `completed` 执行交付前置检查。旧产品文档和 Agent 指引确实明确要求 `--reason completed`，所以这是 Agent 未遵守既有协议与 CLI 允许进入无后续工作的状态共同造成的失败。**主 Agent 随后提出的新产品决定**是以根 Issue 的 close 动作作为交付决定，让 `--reason` 保存自然语言验收依据，同时仍检查 root owner、至少一个已接受 PR、无开放工作项/未解决合并、干净交付树和 finalization 收敛；该决定不是本冻结 run 的行为，也没有在这里验收新版本。修复应同时覆盖关闭路径与最终 seal 判断，不能只放宽其中一个。

另有 08:49:29 的 `provider disconnected`，Braid 随后替换 PR 会话并继续到 ready、merge 与双组 finalization；它不是最终 exit 1 的近因。Runner 没有记录超时终止；原入口不是应用断言失败，因为原入口评测被跳过。Agent 自称的 Playwright 自检结果只能说明它做过本地验证，不能替代 Runner 结果。

## 已合入应用的独立补评测

补取证没有使原入口变为成功。它从该 run 的 `refs/heads/braid-delivery` 合入提交 `146ce2cac430d0e8e84ce9d4865d875c2edfa804` 用 `git archive` 冻结应用，`source.json` 记录源码 SHA-256 `8862dd932265487277367bf849c8a2a7c50db41d9a7f52e145d613bb443e6bd6`；官方本地 Runner 以 noop Agent **只运行评测**。`local-result.json` 的 `evaluation_status=completed`，Playwright 报告为 **19 passed、13 failed、32 total，test_pass_rate=59.4%**。`score=null` 是 noop 评测阶段没有 Meter，Runner exit 1 是确有失败测试。此结果只适用于已合入的同一应用源码，不是原生成入口产出的成功交付或平台总分。

13 个失败可由评测报告的失败定位与失败时页面快照分成四组；以下观察没有读取测试源码：

| 失败项 | 直接证据与原因边界 |
| --- | --- |
| REQ-2.3.1/.2/.3（删除），REQ-2.6.1/.2（颜色），REQ-2.7.1/.2/.4（标签操作）：8 项 | 定位器等待名为 `Delete Note`、`Light green`、`Change labels` 的 `button` 到 10 秒超时。失败快照中同名控件已经出现，但角色是 `menuitem`；冻结应用的菜单 JSX 对这些 `<button>` 显式设置 `role="menuitem"`。失败发生在激活菜单项之前，不能由这些结果断言后续删除、改色或标签数据逻辑本身错误。 |
| REQ-2.7.5（编辑标签）：1 项 | 快照显示重命名已发生，侧栏和输入值均为 `Projects`，但输入框可访问名是 `Label Projects editable`；Runner 等待精确名 `Label Projects`，因此找不到。冻结 JSX 用 ``aria-label={`Label ${l.name} editable`}``。 |
| REQ-2.7.6.1/.2（按标签过滤、查看全部）：2 项 | 两项等待侧栏 `Work` 按钮超时；其失败快照里同一侧栏已是 `Projects`。它们紧随 2.7.5，而应用后端在进程内共享状态；之前的重命名虽使 2.7.5 因名称断言失败，实际已修改 `Work`。这是已观察到的状态级联；这两项并未走到过滤结果断言，不能判定过滤逻辑本身坏。 |
| REQ-2.8.1/.3（置顶）：2 项 | 快照中目标笔记已经位于 `Pinned` 区，按钮变成 `Unpin note`，说明操作已改变状态；定位器却在笔记 article 的**后代**寻找 `title="Pinned"`，而冻结 JSX 将该 `title` 放在 article 自身。失败是标记位置不符合检查方式，不能写成置顶动作未执行。 |

这 13 项不是连接、容器或计分基础设施错误；它们主要暴露可访问角色/名称/DOM 位置与期望不一致，以及共享服务状态导致的后续级联。补评测不证明剩余未触达的用户路径都正确。

## 对象、身份与协作

该 run 只有根 Issue #1 和 PR #1，`local_comments` 为空。根 Issue 预设给 `@glm`，根成员在 08:39:22 用 `braid pr create --issue 1 --assignee glm` 自主给 PR 选了同一成员；这证明能显式选择和一人承担两个工作项，未指派路径在此 run 未观察。实际 CLI 调用无需 `--state` 或 `--writer-turn`；数据库中 PR 创建、正文编辑、ready、merge、Issue close 事件的 `writer_group/writer_turn` 分别指向执行它们的根组或 PR 组。根组即使切换 cwd 到 PR worktree，`braid pr ready 1` 仍被拒绝为 `only this PR group can mark ready`；PR 组后来成功 ready。这支持隐式执行身份与工作项权限生效，旧实例在替换后能否冒用新身份未观察。

实际分工仍有明显退化。08:39:15 根 Issue 工作树提交 `dbc8818`，一次加入 11 个文件、4,343 行，已经实现 React/Vite 前端和 Express 后端；**之后**才在 08:39:22 创建 PR #1。PR 分支的独有提交 `de2bbb3` 只改 `frontend/src/styles.css` 3 行，修复 snackbar 遮挡。PR Agent 将结构、需求覆盖、取舍与自检写进 PR 正文并标记 ready；根 Agent 查看该 CSS diff，又在 PR head 上构建并跑自己的本地验证，随后合并为 `146ce2c`。因此 PR 的这次具体修复和 ready 信息确实改变了根 Agent 的验收行动，但 PR 并未承载主体实现，不能把两个工作项算作实质设计/实施分离。对象正文 revision 可见，原生 CLI 明确记录了 `pr edit`；本报告只据此说这次 PR 正文更新，不由 revision 数推断其它历史演化。

没有评论、回复、hide、resolve，也没有多 ID 整理及后续 context 对比；上下文整理能力在 Keep 未观察。最终被检查的 PR head `de2bbb3` 与合并提交 `146ce2c` 有记录；Braid 未 seal 交付，后来仅对合入应用做了独立 Runner 补评测，不能把补评测改写成原入口成功。

## 证据定位

只读原始证据副本在 `/Volumes/WorkSSD/Development/factory26/runs/braid-usability-implementation/evidence/keep/`，保留了 run/result、Runner 日志、Braid 状态/数据库和五段必要原生会话。补评测的 `source.json`、`local-result.json`、Playwright JSON、失败时页面快照及冻结应用源码在该目录 `salvage/` 下，不含评测测试源码。对应的 WSL 原始目录分别是 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/runs/pi-team-mixed-arc-bench-lite-keep-23563f65f4/` 和同级 `keep-salvage/`。

| 结论 | 原始证据定位 |
| --- | --- |
| 生成失败且评测跳过 | `run.json` 的 `result`；`workspace/experiment-result.json`；`workspace/generation.stdout.log`；`workspace/official-generation/execution.debug.log` 与 `template/.arc/stdout.log` 的 08:54:22 段 |
| 交付判定缺口 | `template/.factory26/20260924-075038-1c70d73a/braid.log` 的 08:54:22 ERROR；同目录 `braid-state/result.json`、`status.json`、`braid.sqlite3` 中 `local_run/local_items/local_merges`；冻结源码 `src/local.rs:451-467`、`src/objects.rs:1171,1424` |
| 主体先于 PR、PR 小修及最终验收 | 同目录 `native/000-…jsonl` 的 08:39:22、08:50:45–08:53:06，`native/002-…jsonl` 的 08:49:28，`native/004-…jsonl` 的 08:50:28；应用仓库 `git show --stat dbc8818/de2bbb3` 与 `git show 146ce2c` |
| 身份与对象 | `braid.sqlite3` 的 `events.writer_group/writer_turn`、`provider_sessions.cli_binding_id`、`assignments`、`local_comments`；`native/000-…jsonl` 的 08:40:15 和 08:41:46 `only this PR group can mark ready`，`native/004-…jsonl` 的 08:50:28 ready 成功 |
| 同一源码与补评测计数 | `salvage/source.json` 的 commit 与源码摘要；`salvage/official-evaluation/local-result.json`；`salvage/official-evaluation/template/.arc/playwright-report.json` 的 32 项结果 |
| 13 项失败的实际页面状态 | `salvage/official-evaluation/tests/test-results/REQ-…/error-context.md`，尤其 2.3.1、2.6.1、2.7.1 的 `menuitem`，2.7.5–2.7.6.2 的 `Projects`，2.8.1/.3 的 `Pinned` 区；对应冻结 `salvage/app/frontend/src/App.jsx` 与 `salvage/app/backend/server.js` |
