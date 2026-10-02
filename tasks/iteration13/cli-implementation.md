# I13 Braid CLI C01–C04 实施

2026-09-30。CLI 源码及文档已完成，主线整合 check/build 与归档只读实操通过；真实写操作尚未验收。用户开工授权原话：“braid cli 的改进是相对独立的，我觉得这个方案没问题，可以开始应用了（交给sub-agent；我们还要继续讨论）”。范围以 [repair-design 第三组](repair-design.md) 为准。

仅修改 Braid `src/cli/mod.rs`、`src/objects.rs` 的回执、读取与 resolve 选择校验，以及对应 CLI 文档。不改 event/reset/delivery/scheduler 语义、Console、SVC、variant、冻结材料或 I12 运行；不提交或部署。

实施顺序：先让既有事务返回本次改变与结果；再收窄 resolve/unresolve 到根 ID 并对称批量；随后使单条/字段读取按请求加载并拒绝冲突组合；最后同步 help、正文往返与异步语义说明。

## 反馈与验收边界

允许 Rust 编译、实际 CLI help 和只读既有材料核对。不运行模型、不写入或恢复 I12、不创建测试/fixture/mock/probe 或专用 run。回执写入、批量误选无写入、新回复可见及 merge 恢复必须等待获授权实际操作，阅读实现不能冒充验收。

最小可重复检查命令及判据见下文；它们仅检查 help/参数契约与既有对象的只读读取。

## 实际改动与因果覆盖

CLI 源码已完成，`src/objects.rs` 与 CLI 文档段落已交回主线；不再占用共同文件。改动保持在既有路径：

- C01：创建与编辑在原事务内取得负责人和本次改变；comment 创建不再提交后查询投递列表。短写 JSON 先输出 id/number，详细投递独立查询。编辑返回 changed_fields；hide/unhide/delete/reaction/link 返回实际改变，无变化不冒充新写。提交未确认的错误带可操作编号及只读核对入口，保留原始错误链。
- C02：resolve/unresolve 在共享 resolve_comments 中只接受根 ID，批量目标全部校验后才写；回复错误给出所属根、整串命令及局部 hide 入口。unresolve 参数与 resolve 对称。回执列前后 cutoff、改变记录数；可见性与新回复规则沿用原实现。
- C03：单条 Comment ID 在 SQL 中限定，不先读整 thread。对象字段请求决定是否读取 body/execution/comments；详情不再通过完整 Issue/PR 快照加载关联讨论。comment 字段决定 body/reactions/deliveries 加载。timeline/comments 和不支持字段组合显式拒绝；list 多取一个编号确认 has_more，同时保留旧 JSON 数组形状。
- C04：close/reopen 沿用已有状态与评论同事务，报告真实状态与 changed；ready 区分本次 published head 和实际保存的 ready_commit；merge 区分已经合并、登记既有整合、应用已准备合并，返回本次 Git 更新及确实关闭的 Issue。已保存 intent、已观察 Git 效果及对象完成未知分别报告，未修改合并、事件或调度控制语义。

没有实施 preview/through、通用 CAS、Issue/comment 创建幂等、全套分页或错误 envelope。CLI 实际消费者核对：Console server 保持读取 list/comment 数组、裸 view 对象，写结果只作为 stdout 字符串记录，未依赖已移除的默认投递详情。Console 当前每条评论的 resolve 按钮仍发送该条 ID；未来绑定新 binary 时，必须只让根讨论入口发送根 ID并同步范围提示，不能把回复 ID 自动隐式升格。当前 registry/旧冻结 binary 没有修改。

## 编译、实际只读反馈与版本边界

CLI 批次独立完成时 `cargo check --locked`、`cargo build --locked` 通过，只有既有 dead_code 警告；最后一次 objects.rs 收尾之后 `cargo check --locked` 也通过。`git diff --check` 通过。

随后主线与恢复 worker 在同一工作树实施已获新授权的核心变化，最后整合 build 当时未完成：先遇 HistoryUnavailable 分支与 record_provider_resume 参数未接齐，后遇 store/mod.rs 的 now/context_reset_events 暂未收敛；均在其它 worker 正在编辑的文件。没有替它们补实现。最新 CLI help 文案、稳定 action 值及 hide JSON 身份字段排序已改源码，须随主线最终整合 build 确认，不能把前一 binary 当成最终冻结产物。

本次实际操作使用前一成功构建的 `sources/braid/target/debug/braid`，SHA-256 `df0f959bd5f891a5b4553af299f91490e9d4152f98a8c25c6194e0b27f417d64`。它包含 C03 查询、参数规则及根 ID/batch help；后续变化只涉及 help 文案和写回执 action/排序。CLI 开工前 mod.rs hash `0c3f1e75cbef4dafdc79c223473830eec42381bdb6c68ee7bc39aa85bc187ac9`，objects.rs hash `773bcb68ec5ba2a4e68c63a451f07550cf10508a437cb700299642813cfb676c`；未以 HEAD 代替 dirty 源码身份。

只读来源是已有 I11 GitHub 归档 `runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/braid-state/braid.sqlite3`，没有启动或写入实验。源数据库本体读取前后 SHA-256 同为 `98a503029161ce12a6a4d9f6c2be5193b3f2fab0a3ed41871a9a498e32b3399d`。

| 实际操作 | 观察与判据 |
| --- | --- |
| comment resolve/unresolve --help | 两者 Usage 均为 `<IDS>...`，明确只接受根 ID；resolve 提示局部 hide。 |
| comment view 347 --json database_id,thread_root | 退出 0；数组仅一项，只有两个所选字段，ID 347/root 341。 |
| comment view 347 --thread --json database_id,thread_root | 退出 0；明确数组展开同根 341 的 7 项：341,343,344,345,347,348,352。 |
| comment view 347 --json body | 退出 0；数组一项仅 body，解码得到 1137 字符，与归档数据库原文完全一致；未写回评论。 |
| issue view 1 --json number,state | 退出 0，仅返回 number=1、state=CLOSED。 |
| issue list --state all --limit 1 --json number,state | 退出 0，stdout 仍为一项数组；stderr 明确返回1项、limit=1、has_more=true。 |
| issue view 1 --timeline --json body | 退出 1，明确 timeline 不支持对象字段选择。 |
| issue view 1 --comments --json body | 退出 1，明确 comments 必须包含在所选 JSON 字段中。 |
| comment view 347 --json imaginary | 退出 1，具体指出未知字段并列合法字段。 |
| issue view 1 --timeline --comments | clap 退出 2，明确两个选项冲突。 |

可重复命令（只读既有归档，不建立专用 run）：

```sh
cli_evidence_state=/Volumes/WorkSSD/Development/factory26/runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/braid-state
cli_binary=/Volumes/WorkSSD/Development/factory26/sources/braid/target/debug/braid
"$cli_binary" comment resolve --help
"$cli_binary" comment unresolve --help
"$cli_binary" --state "$cli_evidence_state" comment view 347 --json database_id,thread_root
"$cli_binary" --state "$cli_evidence_state" comment view 347 --thread --json database_id,thread_root
"$cli_binary" --state "$cli_evidence_state" comment view 347 --json body
"$cli_binary" --state "$cli_evidence_state" issue list --state all --limit 1 --json number,state
"$cli_binary" --state "$cli_evidence_state" issue view 1 --timeline --json body
```

未验项仍包括真实创建/编辑/no-op短回执、回复 ID 整批无写入、批量 unresolve 恢复及新增回复可见、close+comment 与 merge 已知部分/恢复、写正文往返。这些路径没有获准可写实际对象，本批不制造现场或把代码阅读/编译当作验收。未运行模型、测试、fixture、mock、probe、专用 run；未提交、冻结或部署。

源码已完成整合；实际可写操作与模型运行按后续授权进行，已有 I12 原 binary 和暂停状态保持原样。

## 主线整合结果

CLI与核心恢复修改汇合后的 check/build/diff check 已通过。主线以最终 binary 重新执行上述 resolve/unresolve help、comment 347 单条/整串/完整正文、list 截断与 timeline 字段冲突操作，结果与表中相同。
最终源码反馈与 binary 身份以[核心实施记录](context-implementation.md)和 `runs/iteration13/context-core-20260930/cli-readonly.json` 为准；前文构建中间态保留为过程记录，不再代表当前阻塞。实际写操作及模型运行仍未验，冻结 I12 未改。
