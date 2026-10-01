# I13-2 启动资源暂缓修复

2026-10-01，用户对 I13-2 实施及设施故障热恢复的授权覆盖本次有界修复。主线负责冻结 Linux 源码与 binary、重新部署及真实接续；本次仅修改 `sources/braid/src/` 中恢复资源暂缓的传播和聚合，完成编译，并保留首次部署证据。不修改资源阈值、SQLite schema、调度器或原生会话身份，不控制现有容器，不调用模型。

## 已观察到的问题

首次本地接续的 GitHub 与 Sheet 容器均完成恢复包准备，随后在 Braid 恢复入口退出。两项 Docker `ExitCode=1`、`OOMKilled=false`；原始恢复日志记录 `session deferred input: resource pressure`，其后 `local run blocked: provider recovery returned an error`。资源准入尚未允许启动 Pi，这次执行没有证明原生 resume/握手、技能采用或旧 packet 补齐。

完整原件与边界见 [首次接续验收](first-continuation.md)，原始日志分别位于 `runs/iteration13/i13-2-20261001/first-continuation/github/recovery-braid.log` 与 `sheet/recovery-braid.log`。原容器、volume 与暂停 source 保留；后续归档因快照外 symlink 失败属于独立问题。

根因是资源拒绝与其它 `SessionError::Deferred` 共用类型，随后恢复管理器和 worker 提前转为字符串；local 在全体无法推进时将这类恢复错误聚合为终态。一般 Deferred 还表示 Unknown 恢复额度耗尽、transport timeout/断连和 Pi streaming 等，不能整体改成资源等待。

## 修复后的行为

有效资源采样的准入拒绝，以及 Pi 结构化启动 receipt 的 `resource_deferred`，使用 `ProviderError::ResourceDeferred`，映射为 `SessionError::ResourceDeferred`。工具调用失败、transport 错误和其它 Deferred 保留原语义；分类不匹配错误字符串。

SessionManager、dispatch 和 worker 将类型保留到 health 聚合。资源暂缓仍走已有延期路径，保留队列、claim、pending reset 和 native identity；没有输入被准入时不会计为成功。资源拒绝本身不经过成功 resume 后的 `note_uncertain_recovery`，因此不消耗 Unknown 恢复预算。已有成功恢复 SQL 才清理 `last_resume_error` 与失败时间，本次没有改变这些存储操作。

worker health 增加 `waiting_for_resources`。在没有其它活动时，资源等待的 `can_progress` 仍为 false。local 将各组完整 health 写入 `status.json` 的 `provider_health`，并使用已有两秒循环重新尝试；纯资源等待不会触发 provider recovery 的终态或 root idle stall。真实错误和 blocked group 的判定仍先于等待分支。

同一组中，已发现的缺失 worktree、缺失 PR head ref、incompatible 或真实 resume failure 优先于资源暂缓；跨组也不会因为另一个组等待资源而隐藏真实恢复错误。stopproof unknown/failed 的阻断路径保持原行为。

## 文件范围与验证

源码差异为 12 个文件，105 行增加、41 行删除：

| 文件 | 改动职责 |
| --- | --- |
| `agent_session.rs`、`provider/mod.rs`、`provider/session.rs` | 独立资源暂缓类型与映射；延期判定保留两类语义。 |
| `provider/factory.rs`、`provider/pi.rs` | 在已结构化的资源拒绝边界产生资源暂缓。 |
| `group/session_manager.rs`、`group/dispatch.rs` | 延期值保留类型，沿用队列、claim、reset 的延期路径。 |
| `group/issue_agent.rs`、`group/pr_agent.rs` | 两种延期均保留 assignment。 |
| `group/worker.rs`、`health.rs` | 真正恢复错误优先，health 显式标记资源等待。 |
| `local.rs` | 聚合完整 health、等待资源时继续恢复循环，并将延期记录为 deferred。 |

`git diff --check` 通过。最终 Mac 编译 `cargo check --locked --bin braid` 于 2026-10-01 22:17:36–22:17:40 CST 完成，exit code 0；只有现存 unused/dead-code 警告。未运行或新增 Factory/Braid 测试、模拟、探针、自检，也没有发起模型请求。

编译原件：`runs/iteration13/i13-2-20261001/first-continuation/startup-fix-compile.json` 与 `startup-fix-cargo-check-final.log`。源码 patch 保存在同目录 `startup-fix.patch`。主线另行同步 `sources/braid/docs/20-product-tdd/lifecycle.md` 的权威描述。

## 交接边界

上述结果证明源码编译通过，不证明 Linux 实际接续成功。主线将冻结新版本并从保全 source 重新进入恢复入口，验收资源等待后能在同一运行中重试、原 native identity 与历史 prefix 延续、pending reset/claim 未丢，以及真实 Pi resume/握手。首次执行尚未发生的新维护输入消费、独立技能采用和旧 packet 补齐，仍须依据新行为定向确认。
