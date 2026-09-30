# I12 Braid 连续性与讨论折叠

## 问题、根因与处理

description 和可见讨论的编辑需要完整重建 Context，但旧实现把 reset 开始时有运行 turn 或同会话自编辑，直接记为 `continuation`。旧 turn 后来正常结束，或自编辑事件在会话空闲后才被处理，仍会生成新的 `reset_continuation` Wake；所有普通事件又被渲染为“请处理”，使已完成工作重新审计。resolve/unresolve 已按讨论根保存 `resolved_through`，但 CLI 只回空成功，操作者难以看出影响范围。

重建链和原生通知证明保持原状。在新物理 session 完成物化的事务中，读取旧 session 最后一条非 reset notice 工作 turn 的持久终态：`completed` 或无工作 turn 时只更新 Context；`interrupted`、`failed`、`unknown` 才生成续接 Wake。begin 时的运行状态不再决定最终续接。首次指派、上下文续接和后续输入用既有 batch 事件 kind/detail 区分；事件引用只呈现来源和入口，后续输入由负责人判断动作。重建预告要求保存仍需接续的进展与材料入口，不预设必须再执行。

resolve/unresolve 仍通过任意评论 ID 选整条 thread；resolve 折叠到执行时该 thread 最大评论 ID，后续回复保持可见。命令回显实际根、折叠边界、此次改变折叠状态的评论记录数和是否改变。hide 继续按单条评论及可选理由处理。

## 边界与核验

- 旧 turn 自然 `completed`，包括 reset 已开始后结束和先结束再进入 idle reset：只重建，不造新 Wake。
- 自编辑 idle：即使已有 invalidate，旧工作 `completed` 后也不续派；完整 description 仍重建。
- 真实 `interrupted`、`failed`、`unknown`：终态保留续接义务，旧会话通知、停止证明、fencing 或失败封锁仍由既有链处理，不能绕过证明创建第二写者。
- 新评论与 invalidate 混批：reset 只消费绑定的失效事件；独立评论保留在 wake batch，继续投递。仅因 Context 更新不制造工作结论。
- Issue/PR 正文只维护本项当前任务、交付与证据入口；当前集成状态由整合任务维护并链接历史成果。

`cargo check` 与 `cargo build` 成功；实际编译后的 `braid comment resolve --help` 和 `unresolve --help` 显示讨论级参数说明；`git diff --check` 通过。仓库现有代码整体不符合 rustfmt，`cargo fmt --check` 会对多处未触及文件提出大量格式变更，本次没有批量格式化。依据仓库约束未编写或运行 Braid 测试；尚无获授权的模型实验与真实运行数据，因此端到端 reset/讨论操作效果仍待后续正式运行观察。

## I12 Linux 构建材料

当前 Braid 工作树（HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，包含已授权 I11/I12 未提交源码）冻结为 Mac 与 WSL 各自 `runs/iteration12/build/source.tar.gz`，SHA256 `ea427e6ca0d6e0d1fdcb89e498a58973503c97a5401a4288bd9413ca53d237bf`。同目录 `source-head.txt`、`source-status.txt`、`source-dirty.patch` 保存 Git 身份与脏差异；diff SHA256 `008a7ccfbd2003d61fd5039fa190181f4e5be6afa3d417fd6f9d34a5ced08471`。源码包不含 `.git` 或 `target`。

WSL `/home/yyh/Development/factory26/runs/iteration12/build/source` 从该包解出。在已有 `rust:1.93-bookworm` 镜像中复用 `factory26-cargo-registry`、`factory26-braid-target` 缓存卷，以关闭网络、2 CPU、3 GiB 和 `RUSTUP_TOOLCHAIN=1.93.1 cargo build --release --locked --offline` 构建成功，耗时 135 秒。第一次尝试仅因宿主缺少 `/usr/bin/time` 而未进入编译，错误保存在 `build-initial-missing-time.log`。最终编译日志为 `build.log`，身份和各哈希见 `build-identity.json`。

Linux binary 位于 WSL `/home/yyh/Development/factory26/runs/iteration12/build/braid`，已同步至 Mac `/Volumes/WorkSSD/Development/factory26/runs/iteration12/build/braid`，两端 SHA256 均为 `190c74bd24db7e969ae25b41ef541e322ec1775c7b445949c439f9c2e4a7398c`。WSL 该路径可供后续 console 以 `--external` 操作实际数据库；本次只执行 binary 的顶层及 resolve/unresolve `--help`，记录于 `cli-*.txt`，没有启动模型、运行测试或写入运行数据库。I11 原 binary 两端哈希仍为 `d76d65f133979a9f310b39e73fc254f727b564734ee1513c4febe6fbecb083be`。
