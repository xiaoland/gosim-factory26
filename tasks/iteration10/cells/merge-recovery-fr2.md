# FR2：已发布合并后的目标快进恢复

## 原因与修复

`apply_merge` 原先只把目标 ref 恰好指向冻结 merge commit M 视为已发布。若 Git 已发布 M、SQLite 尚未结算时中断，随后目标合法快进到包含 M 的 D，恢复会把 intent 错标为 conflict，PR 和冻结的 `closing_issues` 无法结算。

现在恢复读取冻结 intent 的 M，并用已有 `git2::Repository::graph_descendant_of` 判断当前目标是否包含 M；目标等于 M 或后代 D 时保留当前 ref，按原 intent 在同一 SQLite 事务中完成 PR、Issue 与事件。CAS 发布失败后的目标重读也使用同一判定；目标历史不包含 M 时仍拒绝并保存冲突。`merge_with_match` 发现 prepared intent 时先交给 `apply_merge`，避免重试依据后来变化的正文、head 或 base 重新准备。技术约定已更新到 `sources/braid/docs/20-product-tdd/local.md`。

独立复审发现 prepared 重试还需保留显式 `--match-head-commit` 条件：目标仍在原 base、因此重试将实际写 ref 时，所给 SHA 必须匹配 intent 冻结的 head；不匹配则原 intent 保持 prepared，Git 不写入。目标已包含 M 时仅结算，后来 head 的变化不阻止恢复。启动恢复不传显式条件，仍由冻结 source/head CAS 保护发布。

## 边界与证据

本次仅改 `sources/braid/src/objects.rs` 及对应技术说明，没有修改其它 Agent 的文件、提交或运行实验。`cargo check` 成功，只有现有 unused 警告；`git diff --check` 成功。静态核对了 `apply_merge` 的直接调用者 `merge_with_match`、`recover_merges`，及启动恢复入口 `local.rs`。Braid/Factory 测试和探针按仓库约束未编写、未运行。

实际 M→D 中断恢复、冻结 Issue 关闭和非祖先拒绝尚未通过获授权真实操作观察；编译与静态核对不能替代该运行证据。
