# 迭代 10：成员唤醒、休眠会话与后台完成边界

状态（2026-09-29）：按用户新要求，Braid 已删除测试代码、夹具、测试脚本及 CI 测试调用，今后不维护或运行 Braid 测试。本次只运行 `cargo check --bin braid`，**exit 0**，有 11 条现存 dead-code 警告；输出保存在 `/tmp/factory26-braid-no-tests-check.log`。未打包、部署或启动新实验。

历史验证（2026-09-28）：删除前的 `cargo test --bin braid --quiet` 为 **63 passed、0 failed，cargo exit 0**，输出在 `/tmp/factory26-braid-resume-retry-tests.log`；当时 `git -C sources/braid diff --check` 通过。此历史结果不代表 Pi/PBB 原生包或比赛题目已验收。

## 测试清理

删除了 `src/config.rs`、`src/local.rs`、`src/objects.rs`、`src/store/mod.rs`、`src/evidence.rs`、`src/health.rs` 和 provider 的 `codex.rs`、`factory.rs`、`pi.rs`、`session.rs` 中全部内嵌测试模块，`tests/cli_writer_boundary.rs`，以及 `scripts/tests/` 下全部十个脚本、接收器和说明。只供旧测试调用的 `queue_worker`、`HealthSnapshot`/`provider_health_worker`、`GroupSpec::new/profile_id` 也已移除；保留产品运行代码、迁移和真实行为契约。CI 不再运行安装测试脚本；Braid `AGENTS.md`、当前 README/PRD/部署说明及仓库内 Rust 技能已改为编译、静态检查和获授权的真实产品观察。

源码和当前维护入口已无 `#[cfg(test)]`、`cargo test`、`scripts/tests` 或失效的测试指引。`CHANGELOG.md` 与旧 `tasks/rust-mvp-implementation.md` 中仍有过去测试活动和脚本路径，作为历史证据保留；Factory 侧历史报告同样未改。此次没有运行或新增测试，也未提交。

## 已确认问题与当前修复

`objects.rs::replace_assignee_in` 曾只发 `Assign`。新 member 的 assignment/session 被物化后，store 会消费该事件；没有独立 Wake，故新 session 保持 idle、没有 turn。保留的测试数据库直接记录旧成员 `local-agent-1` retired、新成员 `alternate-2` active、assign batch consumed、无新 turn。现在在同一事务发给目标的 Wake，不使用旧 writer 标记以免被归类为 OriginEcho。`set_assignee` 与 `edit_with_parent_and_assignees` 共用此入口；测试 `chained_reassignment_tears_down_each_writer_and_wakes_each_owner_once` 已通过，证实旧会话 teardown 后新负责人只收到一轮工作，连续改派没有重复唤醒。`failed_native_teardown_keeps_reassignment_fenced_and_pending` 也通过，证实 stop 失败仍挡住新负责人。

相同的 assign 被消费后不再构成 turn 的情况也存在于带指派的 `create_pr_with_options`，以及没有可复活 assignment 时 `lifecycle(reopen)` 的重新指派。两处同事务补目标 Wake；PR 首轮已由完整 local 工作流验证，reopen 有独立 Braid 行为断言。Issue 创建本来就有独立 Wake，因此未新增。未指派对象仍不自动运行。

八项 local 测试原夹具还沿用旧产品协议：直接使用非 bare repo、未先注册 Profile、固定 `#1/#2` 编号与 `local-agent` 成员名、从 Agent 文本解析已移除的 `--writer-turn`、假定 steer 被禁止和 close 必然产生 finalization turn。已将夹具改为现行 bare origin、动态 turn/成员记录，并按实际 `steer → 可核对处理回执 → close/sleeping` 验证；native stop 失败仍挡住替换。完整产品脚本现在遵守 draft PR→push 已发布 head→ready、由 PR 作者在父 Issue 明确评论交接，之后 root 合并两个 PR 并关闭 Issue；结果为 `quiescent`，交付 commit 包含两份 artifact。PR 关联本身只提供背景，不等同订阅或自动通知；我曾短暂尝试给所有关联 Issue 发 ready Wake，复核契约后已撤销，产品源码中没有保留该块。

## 已实现的严格休眠复用

原调用链中 `store/mod.rs::provider_resume_candidates` 排除 sleeping，`group/dispatch.rs::reactivate_work_item_agent` 总调用 `sessions.start`，导致同一成员的后续普通联系重建原生会话。既有 Pi `resume_session` 可恢复持久原生历史，但不能以向旧历史追加新的完整 Context 代替重建：隐藏评论、编辑描述等会使旧历史保留应删除的内容。

`begin_work_item_reactivation` 现在在原有 materialization 中携带旧 sleeping provider id、Context revision、instruction revision。dispatch 仅当同一 assignment/member 的 Profile revision（含 binding 身份）、instruction digest、**当前 canonical Context revision** 与旧记录相同，且 `worktree::resume` 验证原路径属于当前 origin/成员时，才调用现成 `SessionManager::resume`。成功后 `complete_work_item_reactivation` 原地更新旧 provider row 与新 CLI binding，不新建 provider session；新的 store 检查断言同一 session row、`resume_count=1`、contact 仍进入原 session 的 turn。Context 或身份不一致继续原有 fresh 路径。绝对路径的 Pi 原生 session 文件确定已消失时可 fresh；resume 的 timeout/断连/start 错误在 `ProviderAgentSession::resume` 保留具体错误，不再压成 `Unavailable` 而误触发 fresh。工作树验证失败也带具体原因，不静默忽略。

这仍是保守优化：有新评论而 canonical Context 改变时会 fresh；跨项 direct contact 在 Context 不变时才受益。没有新 Context 注入协议或新状态机，也不凭静态检查宣称实际 token 节省。原生 resume 的真实运行收据仍待主 Agent 的新本地实验。

暂时性原生 `Start`、`Timeout`、`Disconnected` 和 resume 时的 `Unavailable` 现在走可接续失败：保留原始错误，事务性将当前 event 从 materializing 退回 pending，将 assignment/agent 退回 sleeping，联系收据保持 queued，旧 provider id 和工作树不变；错误记在 provider `last_resume_error`，成功后清除。worker 将错误交给现有 health 报告，按已有两秒 recovery 时点节流重试；其它执行仍在途时可继续恢复，静止时 local 依既有条件返回 blocked，供同请求重启接续。进程恰好在 materializing 阶段退出时，`prepare_offline_resume` 也把有 sleeping provider 的重新激活退回同一状态。store 检查证实超时和中断后 queued 联系及同一原生 id 留存，成功只投递一次、`resume_count=1`；worker/local 行为检查分别证实第一次失败、下一恢复时点成功，以及无活动时 blocked 且联系仍 queued。确定 Pi 原生文件缺失仍 fresh；身份、Profile、指令或 canonical Context 改变仍 fresh。真实原生断连/恢复效果仍待新本地实验。

## Pi 后台完成边界

现有 `store/mod.rs::sleep_closed_idle_agent` 仅看 Braid turn/pending event；Pi `agent_settled` 可早于 `pi-background-bash` job 完成，而扩展 `session_shutdown` 会取消仍在运行的 job。因此此处是源码证明的机制风险，非某个已抓到的 job 遗失收据。主 Agent 已决定 Pi 原生已有 `registerBackgroundWorkProvider`/`agent_end` drain 为唯一最小接线；另一单元负责 PBB 将非 service 活跃 job 注册到该原生通用工作契约，常驻 service 显式标注。这一工作不在本单元文件归属内；Braid 不读 PBB job JSON，不管 Pi 内部 subagent，也不加专属 RPC 或等待时间。需待 Pi 包与实际运行验证结果，不能用 Braid store 的 idle 状态独自宣称后台已完成。

验证仅使用 Braid 自身检查；未运行 Factory/设施/Corpus 测试，未改冻结运行、未提交或部署。本单元涉及 `src/objects.rs`、`src/local.rs`、`src/store/mod.rs`、`src/group/dispatch.rs`、`src/provider/session.rs` 与本 cell；其它共享脏文件均保留。原始检查输出为 `/tmp/factory26-braid-all-tests.log`，另有定位阶段的 `/tmp/factory26-braid-local-*.log`。最终包、Pi/PBB 原生运行、两题结果由主 Agent 继续验收。
