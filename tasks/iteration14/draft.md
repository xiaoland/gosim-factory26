# Braid PR 创建默认草稿

用户明确要求“PR 创建默认为 draft（如果 braid PR 还没实现 draft，请实现）”。本项只修改 Braid Local 创建默认值，主线负责实施授权与整体 packet；改动由主线统一提交，未修改 Factory variant、Console、运行包或 I13 现场。

`sources/braid/src/cli/mod.rs` 的 `pr create --draft` 默认值改为 true，保留旧旗标。`sources/braid/src/objects.rs` 中未接收 draft 参数的创建入口也统一传 true；显式接收 draft 的底层入口、既有对象、迁移、request-id 重试早返以及 ready/merge 实现保持原样。不增加创建即 ready 的选项，调用方用现有 `pr ready ID` 明确切换状态。

`sources/braid/docs/20-product-tdd/local.md` 更新创建契约，并按主线指出的事实差异，将 ready 的通知对象改为该 PR 的显式关注者。该文档修正没有增加关联 Issue 通知功能。

原件集中在 [runs/iteration14/pr-draft/20261001](../../runs/iteration14/pr-draft/20261001/)。目录按开始准备日期命名；实际 CLI 操作跨至北京时间 2026-10-02。`git-head.txt`、`source-before.sha256`、`source-after.sha256`、`change.diff` 和修改前后两个独立二进制保留实现身份。`build-before.log`、`build-after.log` 保存两次 `cargo build --locked --bin braid --manifest-path sources/braid/Cargo.toml` 的编译原始输出，均正常退出，均含现存 12 项 dead_code 警告。`git diff --check` 正常通过；未运行或新增测试、smoke、探针及断言框架。

隔离输入仓库、裸 origin、独立 PR clone 与 SQLite 库均在该原件目录。修改前二进制通过正常 `braid local request.json` 初始化状态；请求指向不存在的 provider executable，原生 preflight 返回 `session is unavailable`，local 的真实终态为 blocked、退出码 1，不能称为成功运行。`local-before.stderr`、`state/result.json`、`state/sessions.json` 保留这条边界。修改前后数据库均没有 provider session，也未启动模型。其后使用宿主 `--external` 执行真实对象命令与 Git 操作。

| 实际操作 | 观察与原件 |
| --- | --- |
| 修改前创建默认 PR #2 和显式草稿 PR #3，新二进制读回并重试 #2。 | #2 始终非草稿，#3 始终草稿；旧标题、ready_commit、创建及关联活动未变。见 `legacy-*-before.json`、`legacy-*-final.json`、`legacy-ready-retry.json` 与 `database-observations.json`。 |
| 新二进制省略 draft 创建 PR #4，沿用 `--draft` 创建 #5；发布真实分支后以显式 base/head 创建 #8。 | #4、#5、#8 均为草稿。见 `default-created-view.json`、`explicit-draft-view.json`、`explicit-head-view.json`。 |
| 同标题、同正文、无 request-id 连续创建。 | 分配不同编号 #6 和 #7，均为草稿；不按内容去重。见 `no-key-first.json`、`no-key-second.json` 与数据库原件。 |
| #4 清除草稿、重试创建、撤回 ready 后再重试；合并后再重试创建。 | 每次重试都复用 #4，`created=false`、`changed=false`；保留当时的 ready/draft/MERGED 状态、原标题和原正文。见 `ready-after-retry.json`、`undo-after-retry.json`、`merged-after-retry.json` 及对应 `*-retry.json`。 |
| 草稿 #4 请求 merge；转 ready 后，在尚无新提交时请求 merge。 | 草稿退出码 1，具体错误为 `PR is draft`。无新提交时退出码 1，完整错误说明 Braid 未观察到该 head 位于目标 base 之外，不能确认整合。见 `draft-merge-corrected.*`、`no-new-commit-merge.*`。 |
| 独立 clone 在 #4 head commit 并 push，草稿请求 merge，再 ready 和按准确 head merge。 | 已发布新提交时仍拒绝草稿；ready 保存准确 head；merge 返回 `applied_prepared_merge`、`git_ref_updated=true`、状态 MERGED；裸 origin 的 delivery ref 包含 `change.txt`。见 `published-draft-merge.*`、`published-ready.json`、`published-merge.json`、`merged-change.txt`、`git-history.txt`。 |
| 以同 request-id 指定不同 head 重试创建。 | 退出码 1，具体错误为 `request id belongs to PR with a different head`。见 `retry-head-conflict.*`。 |

准确命令及原始执行回显分别在 `operations-before.log`、`operations-after.log`、`operations-after-ready.log`、`operations-published-head.log`。首次 ready/merge 操作错误地附加了现有 CLI 不支持的 `--json`，返回参数错误、退出码 2；这些原件保留在 `operations-after.log` 与 `draft-merge.*`，后续去掉该参数并完成实际行为验证，不把参数错误作为 draft merge 的证据。

`objects-before.sqlite3` 与 `objects-after.sqlite3` 是操作前后独立 SQLite 原件，`database-observations.json` 提供只读查询结果。前后 schema_migrations 仍为 v1–v16；本次未修改历史迁移的 draft 缺省或重算旧状态。这证明修改前二进制创建的既有库和 PR 能保留状态，不声称已重放更早 schema 的升级。

尚未覆盖的是原生执行身份、模型指派启动及实际状态通知送达；这些实现路径未变。本次没有直接调用已无生产调用者的内部兼容包装函数，覆盖来自完整调用链核对和编译。没有扩大到模型实验或产品验收。
