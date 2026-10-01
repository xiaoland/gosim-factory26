# Braid Local

此 Factory26 工作树将 Issue、PR 和 comment 保存在本地 SQLite，让它们成为 Coding Agent 的当前工作记忆。Issue Agent 维护需求与验收判断；PR Agent 在独立 Git worktree 实现和自检；根 Issue 接受 PR，最终交付来自明确的 delivery commit。逻辑 group 与 worktree 在物理会话替换后继续保留。

```sh
cargo build --release
braid local /absolute/path/request.json
braid --state /absolute/path/state status --json
braid --state /absolute/path/state issue view 1 --comments
```

请求、CLI、交付结果及归档契约见 [本地运行契约](docs/20-product-tdd/local.md)。构建需要 Rust 1.93+ 和 Git。连接 Codex app-server 或 Pi 的参数由请求显式提供，不需要 GitHub App、remote、webhook 或 tunnel；SVC 可由调用者独立配置。

源码检查使用 `cargo check --bin braid`；真实 native 核心与 Factory26 bench 的行为由独立接入验收证明。

此目录是从上游 `08c1c10d3b61b24119580ba8af14e2a393f7ea33` 派生的本地实现，现由 Factory26 父仓库统一跟踪。原独立仓库的 Git 历史保留为迁移恢复材料，入口见[源码纳入记录](../../tasks/source-repository-integration/packet.md)；相邻历史工作树继续保留。本目录不再提供旧 `braid gh` 或双 Markdown/handoff/refresh 流程。
