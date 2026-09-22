# Assignee Cell：实施结果

状态：Braid 实现与验证完成；未提交。sources/braid 已停止写入，等待主线快照与 Linux 构建。Factory 侧能力物化和 src/provider/factory.rs 由其他 owner 负责，不计入本 Cell 的源码归属。

## 已实现合同

- Profile 配置与持久化新增 assignee_login、assignee_description。login 采用 GitHub 风格的 1–39 位小写字母、数字和单连字符，禁止首尾或连续连字符；CLI 接受可选 @ 并转为小写。description 必须是单行且不超过 240 UTF-8 bytes。当前请求中的公开 login 必须唯一。
- 新增 forward-only 0007_assignee_projection.sql。旧数据库可迁移并读取，旧 profile 行的公开字段保持 NULL；不会从内部 profile、model 或 provider 猜测公开身份。缺少公开投影的旧活动请求不能作为兼容身份继续运行。
- Issue 与 PR 的 canonical、CLI JSON/text 统一输出最多一个公开 assignees actor。desired_profile、assignment_revision、provider/session 信息不再进入 Agent 可见对象；运行时隐藏并拒绝 profile 命令，运行时 status 不输出 physical sessions。Agent context 注入公开 login 与 description 的成员目录。
- create --assignee LOGIN 在任何对象写入前完成 login→内部 profile 的唯一映射。edit --add-assignee LOGIN 与 --remove-assignee LOGIN 实现严格单 owner 合同：已有 owner 时第二次 add 失败；remove 必须匹配当前 owner；同一命令 remove 旧 owner + add 新 owner 在一个 SQLite immediate transaction 内原子完成；remove-only 进入未指派并停止旧 owner。
- 重指派复用既有 desired_profile_id、assignment revision、writer fence、native teardown、worktree reuse 与 scheduler。事务先写目标与 fence，事务外异步取得旧 writer teardown 证明，再激活新 generation。成功 A→B→C 时每次只唤醒新 owner 一轮；teardown 失败时 assignment 保持 stopping、事件保持 pending，不会并行启动新 writer。
- 修复了重指派事件竞争：非目标 Issue driver 不再消费 pending Assign，只有选中的 profile 能取得事件并开始目标轮次。

## 变更范围

Braid owner 修改：

- migrations/0007_assignee_projection.sql
- config.example.toml
- docs/20-product-tdd/local.md
- src/config.rs
- src/store/mod.rs
- src/objects.rs
- src/cli/mod.rs
- src/local.rs
- src/group/provider.rs
- src/group/issue_agent.rs
- src/group/pr_agent.rs
- tests/cli_writer_boundary.rs

src/provider/factory.rs 的同工作树变更属于主线 Pi receipt owner；本 Cell 未修改或回退它。

## 可观察验证

新增和扩展的行为测试覆盖：公开 login 的 @/大小写归一化；非法 login、description 换行和 UTF-8 字节上限；Issue/PR assignee 对称；未知 assignee 的 create/edit 零写入；严格 add/remove 与原子替换；运行时 profile 隐藏及 status 字段隐藏；A→B→C 的旧 writer teardown、脏 worktree 复用和每次恰一轮唤醒；native teardown 失败时 fence 与 pending 状态保持。

最终在包含主线 src/provider/factory.rs 当前改动的工作树执行：

- cargo fmt --check：通过。
- git diff --check：通过。
- cargo test --all-targets：32 个单元测试与 1 个 CLI 集成测试全部通过，0 失败；单元测试 17.90 秒，集成测试 0.72 秒。输出只有既有 dead-code warnings。

## 剩余集成边界

Braid 范围内没有已知阻塞。主线仍需把 Factory 物化的 assignee_login / assignee_description 与内部 defaults.issue / defaults.pr 请求合同一并快照，并完成 Linux 构建或更高层联合验收。当前工作树未提交，避免与主线集成顺序冲突。
