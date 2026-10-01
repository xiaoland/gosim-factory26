# 实施计划

1. [完成] 盘点 v15 历史兼容面：配置、Corpus、analysis、integration、机器输出与运行中进程合同；区分应删除的成功路径和必须保留的拒绝/安全边界。
2. [完成] 分离发布说明、Corpus 发布索引和 CLI 合同，重做当前草稿中混入 Corpus 指南的 CLI 迁移内容。
3. [完成] 用 Towncrier 替换 Changie，保留 release PR 合并触发发布，并让 CI/CD 复用同一构建与验收入口。
4. [完成] 收敛静态检查与测试入口；补齐 mypy 实际源码覆盖，改善子进程超时、stderr 和失败现场的可诊断性。
5. [完成] 验证当前合同、旧输入拒绝、wheel 安装、analysis、double 与 Agent-thread 黑盒行为，并以 Towncrier draft 演练 release PR 准备；Python 3.11/3.14 由 CI 矩阵执行。

当前状态：设计已由 Human 确认并通过 advisor 复审。实现、生成物、wheel
黑盒验收和本地全套检查均已完成；等待代码审阅与是否提交的指示。

## CLI 架构复查

1. [完成] 由 advisor 在方案形成前调查 monolith 候选与真实切缝。
2. [进行中] 按命令所有权从根 `cli.py` 迁移纵向切片；analysis 与 telemetry 已迁移。
3. [待处理] 迁移 double、dev、run 与 project 命令，保持根入口、退出码和延迟可选依赖合同。
4. [进行中] 已抽出 double compiler 的资源所有者；待分离 provider source/capture 与 normalization。

## 仓库与发布边界

1. [完成] 将 Corpus 权威源从 `src/` 迁移到 `corpus/`，将 PDM member 从
   `svc_cli/` 迁移到 `cli/`，保留 `cli/src/svc_cli/`。
2. [完成] 分离 CLI/Corpus Towncrier 配置、fragment 队列、changelog 触发和
   `cli-v…`/`corpus-v…` tag，同时保留旧 `CHANGELOG.md` 作为共同历史。
3. [完成] 让 Corpus release 检查按相对内容跨旧 `src/` 基线比较，避免纯目录
   改名被误判为语义发布。
4. [完成] 验证 PDM workspace、全量检查、Towncrier 双 draft 与旧布局基线。
