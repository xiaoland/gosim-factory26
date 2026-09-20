# 调查与当前证据

本页维护事实、推断和未决问题，不重复方案或实施状态。方案见 [design.md](design.md)，验证状态见 [verification.md](verification.md)。

## 工作区现状

项目内 `sources/svc`、`sources/braid` 已作为独立 Git 仓库建立，main 基础分别为 4fe4c66、08c1c10，origin 指向各自上游。前轮相邻工作树修正已迁入，原工作树保留。Factory26 父仓库源码仍未做首次提交；两个 sources 仓库有未提交修改。

现有草稿包括 source 构建/归档、可选 SVC runtime、诊断输出精简，以及 braid `src/local.rs`。后者的双正文/handoff/refresh 模型不符合已确认产品行为，需在实施阶段替换；用户明确要求现在不撤回已有修改。

PRD、Deployment 和 sources/braid/docs 的部分文字提前描述了旧草稿。核对当前上游产品时使用 `git show HEAD:<path>` 和原始源码，不能循环引用这些文字证明新设计。

## SVC 注入

`scripts/factory.py` 的 runtime_environment 复制 `harness/AGENTS.md` 到临时 `.codex/AGENTS.md` 或 `.pi/agent/AGENTS.md`；目前没有 variant AGENTS 覆盖。当前文件包含运行授权、工作方法摘要、评测限制和工具/完成指导，超过简短导航的职责。这是需要精简注入的直接原因。

## braid 行为与缺口

以下均核对于 braid HEAD 08c1c10，未采用新增 local 模块作为依据：

| 证据 | 支持的结论 |
| --- | --- |
| `src/context.rs:967` 的 render_comment | hide/delete 保留身份、作者、时间与状态，不输出正文；hide 可恢复，delete 为墓碑。 |
| `src/context.rs:835` 的 PR 投影 | PR 包含直接关联 Issue；关闭 Issue 只保留引用与状态。 |
| `src/cli/gh_cmd.rs` | 当前 CLI 只有 comment create、PR ensure，完整对象操作需要补齐。 |
| `migrations/0001_initial.sql` 的 work_items、canonical_objects | 当前存储主要是身份、版本、生命周期；不能直接充当完整本地正文权威。 |
| `src/store/mod.rs:104` 的 EventKind | 已有平台中立语义入口，可用于本地对象变更，不必重造阶段调度器。 |
| `src/group/provider.rs:68` | PR Agent 可以修订关联 Issue 的设计；不支持强制角色往返的推论。 |
| `src/producer/reconcile.rs:334`、`src/store/mod.rs:2352` | 识别任意 Agent-origin 后整体排除传播，宽于文档的 originating-group 自身回声抑制。 |
| `src/group/dispatch.rs:422` | 向已有会话发送 references，不能据此证明新关联正文已注入；更新 context_revision 也不是物理重建证据。 |

两份静态预演已收束上述接点，证据详见 [braid 预演](rehearsal/braid.md) 和 [集成预演](rehearsal/integration.md)。主 Agent 已独立核对 Factory prompt 禁止 commit、空应用初始化及固定冻结初始目录，与 Braid worktree 强制 GitHub remote/fetch 的冲突；同时核对了 Codex/Pi 的 CLI PATH 差异、Pi 跨工作树会话遗漏和终态计量、analysis 缓存未纳入输入内容哈希、远程评测依赖目录差集选择身份。这些是静态发现，不是新实现验收结果。无人值守交付的推荐条件归 [design.md](design.md)，实施依赖归 plan。

## ARC-bench 与诊断

`third_party/arc-bench/playwright.config.ts:15` 已提供 HTML、失败 trace、截图和视频。官方下载的 `runs/development-loop-research/starter.zip` 包含 SDK：events.py 提供 runner/requirement 状态，traceability.py 提供需求、场景、接口、文件/测试的显式关联。

本项目已收集评测 JSON/附件、平台状态/增量日志、traceability 和 commit-history。但实际无模型探针 `runs/playground/23a11724c9f4/traceability.json` 为空，commit-history.json 为 workspace_unavailable；不能宣称需求到源码的关联已接通。

已定位的诊断样本为 run 20260920-141339-6138c072、eval 20260920-163747-e5039d、REQ-2.2。error-context.md:21 的定位链要求 dialog Note editor 下的 Title；:335-339 的页面实际有 dialog Create note 和 Title；冻结 application/public/app.js:763 设置的正是 Create note。证据支持父对话框名称契约不一致，不支持“输入框或创建能力不存在”。是否属于输入契约缺口仍应核对完整需求，不能直接归咎于模型。
