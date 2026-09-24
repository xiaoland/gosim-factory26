# 实施预演：多评论整理与指令归属

本记录只读核对当前源码与已批准的 [设计](design.md)、[技术方案](technical.md)、[验收方案](verification.md)。没有改源码、运行测试或实验；以下是实施位置与失败边界，不能当作验收结果。

## 多 ID resolve / hide

现有 [CLI](../../sources/braid/src/cli/mod.rs) 的 `CommentCommand::{Hide,Resolve}` 都只收一个 `id: i64`；`Hide` 另收 `--reason`。分派分别调用 [objects.rs](../../sources/braid/src/objects.rs) 的 `comment_visibility(turn,id,"hide",reason)` 与 `resolve_comment(turn,id,true)`。`Unhide`、`Delete`、`Unresolve` 目前也为单 ID，本轮需求只扩大 hide、resolve；单 ID 调用格式应继续可用。

现有两个对象方法各自执行 `connect → BEGIN IMMEDIATE → writer → 读取对象 → 更新 → discussion_changed → commit`。`writer` 会因目标工作项已有 pending invalidate 而拒绝旧 turn，所以在 shell 中依次运行单 ID 命令，第一条成功后第二条可能被 fenced。`discussion_changed` 用同一事务给评论所在工作项发 `Invalidate`，给关联工作项与讨论参与者发 `Wake`；`emit`/`store::ingest_event_transaction` 还在该事务中写 delivery、event 和调度记录。不能在一个循环里调用现有 public 方法，也不应在 CLI 里自行提交后重建。

最小改动顺序：

1. 在 [CLI](../../sources/braid/src/cli/mod.rs) 把 `Hide`、`Resolve` 的位置参数改为一个或多个 ID，并将整组交给对象层；保留 `comment hide 8 --reason …`、`comment resolve 4` 的原用法。帮助只说明 `comment hide 8 9 --reason '…'`、`comment resolve 4 7` 是同一操作。
2. 在 [objects.rs](../../sources/braid/src/objects.rs) 为 hide/resolve 增加接收 `&[i64]` 的事务入口，单 ID public 方法委托它以维持旧调用语义。每次只创建一个 `Immediate` 事务、取得一次 writer；在该事务内先读并验证所有 ID，再更新及调用原 `discussion_changed`，最后一次 `commit`。hide 沿用现有 `deleted` 不可恢复、旧理由继承、状态/理由未变则不发事件的规则；resolve 沿用 `thread_root`、`resolved_through=max(comment_id)` 和无变化不发事件的规则。重复 ID 去重；同一 thread 的多个 resolve ID 按 root 去重，避免重复事件。
3. `commit` 成功后直接返回。调度器沿既有 [store/mod.rs](../../sources/braid/src/store/mod.rs) `context_reset_events` / `begin_context_reset_transaction` 和 [group/dispatch.rs](../../sources/braid/src/group/dispatch.rs) `materialize_context_reset` 路径消费整组 pending invalidation，重建完整当前投影并替换旧 session。`objects.rs::read_comments` 已将 hidden 正文从普通视图移除、按 `resolved_through` 折叠评论；`comment view --include-hidden` 仍可查历史。无需新事件类型、手动 refresh、批量脚本或另一份上下文 schema。

任何 ID 不存在、hide 对已删除评论非法、写入或事件入库出错时，事务不提交，所有已准备或已执行的 SQL 随事务回滚；不会出现前几个 ID 已提交、后几个失败的半成品。验证必须先覆盖整组，不能先改一条再校验下一条。风险是同一命令跨多个工作项会产生多条既有 invalidation/wake，但一次提交后只触发既有调度；同一 thread 的重复 resolve 应压成一次。上下文重建是提交后的异步行为，重建本身失败仍按已有 reset 错误路径处理，批量 SQL 原子性不等于原生会话替换绝不失败。

## 提示词与四个 variant

工作项协议的主归属是 [group/provider.rs](../../sources/braid/src/group/provider.rs) 的 `local_instructions`、`issue_system_prompt`、`pr_system_prompt`：这里当前重复说明 writer-turn/state 前缀、会话替换操作、整页 CLI 清单，以及 Issue/PR 固定交接。按设计改为简短的工作项语义、成员目录和常用 `--help` 入口；不要求更多讨论或阶段文件。

四个现有 variant 为 `pi-team-glm`、`pi-team-deepseek`、`pi-team-mixed`、`pi-team-vv`。它们的六份 `agents/*/instructions.md` 前两段完全相同，重复说明 Issue/PR、assignee 与强制完成评论；这些 Braid 协议应从六份文件移到上述 Braid 归属并精简，而非继续复制。后两段是原生 sub-agent 的有界委派方法与无人值守决策边界，应保留。仅 `pi-team-vv` 两份文件末尾另有 SVC 测试设计/Verification 指引，应原样保留；不复制或修改 SVC Corpus。各 variant 的 `run.py::native_files` 读取对应 `instructions.md` 作为 `profile.user_instructions`，因此改这六份源文件即覆盖四 variant，无需改生成材料模板来删除重复文字。四份 `run.py` 的 `DEFAULTS={issue,pr}` 和 request 接线属于另一个已批准的分派变更，不能以提示词精简代替。

实施时先处理对象层事务，再接 CLI 参数及帮助，随后精简 Braid 共用提示和六份 variant 指令；身份绑定和默认指派由各自方案路径集成。最需防的回归是把多 ID 循环落在独立事务外、使第一条 invalidate 先封住后续 ID，或删除 variant 里的原生委派/VV 的 SVC 方法指引。是否在真实任务中改善上下文使用，按已批准的真实运行验收观察；本预演不新增 Factory/Braid/SVC 测试或探针。
