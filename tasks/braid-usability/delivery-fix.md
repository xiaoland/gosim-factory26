# 根 Issue 关闭理由导致的交付失败

## 原始观察

冻结 ZIP SHA-256 为 `8b7c37b7d3097a0d12e14bb4c66170743d7f9d41e3bd443f227b3726073f6b9d`。Keep run `pi-team-mixed-arc-bench-lite-keep-23563f65f4` 的 `run.json` 为 `failed`、`stage=generation`；适配器错误为 `Agent generation did not produce a complete application`。Braid 原始日志更具体：根 Issue 已 CLOSED、PR #1 已 MERGED，所有执行已收敛，仍返回 `local run incomplete`，因为根 Issue 的 `reason` 是 Agent 写出的自然语言验收说明，而不是精确字面值 `completed`。原始 run 留在 WSL `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924/runs/<run-id>/`；逐 run 过程分析归 [Keep 报告](results/keep.md)。BookStack 的原冻结 run 仍在独立运行，另有自己的分析者。

## 临时修正与其局限

临时修正将根 Issue 的 `close` 当作 Agent 接受交付的动作，`--reason` 保存说明，不再承担隐藏状态码。用户随后指出更根本的边界错误：Braid 不应根据 Issue/PR 状态决定 Factory 应用能否进入 benchmark。新的产品边界见 [run-boundary.md](run-boundary.md)；本修正和已启动的 ZIP 只保留为诊断证据。Braid 仍在关闭时要求根 Issue owner、至少一个已合入 PR、无开放工作项或未处置合并、干净交付树；封存时再要求所有 finalization、执行、reset 和事件收敛。因此自然语言理由不会绕过交付条件。原先仅对 `reason=completed` 启用前置条件，却允许其他理由关闭根 Issue，制造了无法继续的终态。

改动集中在 Braid 的 `objects.rs`、`local.rs`、Issue 指引及本地运行契约。原始 ZIP 和失败证据不修改；新源码单独导出到 `runs/braid-usability-implementation/braid-source-delivery-fix/`，WSL 独占目录为旧实验目录下的 `delivery-fix/`。新制品将重新运行同一 Lite 两题；其完整得分后先报告。

本修复仍只由构建、真实生成与官方本地 Runner 评分验收，不添加 Factory 或基础设施测试。

## 修正后的冻结与运行

本机 `cargo build --locked` 成功，WSL Docker release 构建与独立打包完成。新 ZIP 为 `delivery-fix/pi-team-mixed.zip`，391073007 bytes，SHA-256 `3151d805166ea2e18a6e7a8cd4f947693e7547ab4f9449b8e0afbd3a00f7d9e5`。同一 ZIP 用于修正版完整 Lite 矩阵，两个新 run 分别为 `pi-team-mixed-arc-bench-lite-keep-9cacc02bdd` 和 `pi-team-mixed-arc-bench-lite-bookstack-58b12caa6b`。控制器与原始结果均在 WSL `delivery-fix/runs/`。此时两题已启动，尚无评分；旧 BookStack 独立运行，旧 Keep 失败记录保持不变。
