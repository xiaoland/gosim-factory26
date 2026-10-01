# Braid/SVC 源码纳入 Factory26

2026-10-01。用户明确要求：“将它们纳入本仓库中，不需要把它们再作为独立的仓库了。”本次仅迁移源码归属、收敛对应构建与交接说明，不改变 Harness、运行中服务或实验状态。

当前 `sources/braid`、`sources/svc` 保持原目录、组件文档和技能入口，当前源码及未提交修改作为父仓库的一次源码快照纳入。Braid 的运行时对象、成员 clone 和共同 origin 仍是其产品职责，与开发源码是否使用独立仓库无关。开发侧完整 SVC `/Volumes/WorkSSD/Development/svc` 保持外部来源。

## 来源与恢复

迁移前 Braid HEAD 为 `76747f2db174237501d948c36b5321ad3ffd75ae`，96 份实际源码文件；SVC HEAD 为 `a0af6e14a9f6cd2b19e1565e5d08d82fe3672139`，574 份实际源码文件。迁移前还有未提交修改和 SVC 未跟踪文件，均按当前工作区内容纳入，不用旧 HEAD 覆盖。

原始来源、refs、暂存与未暂存 patch、文件内容/权限身份和父仓库起点在 `runs/source-repository-integration-20261001/`。原 `.git` 移到该目录的 `git-metadata/<component>/`，作为本地恢复备份，独立历史不重新拼入 Factory26 的提交图。该备份不随父仓库 clone 分发；当前完整源码快照随本次父仓库提交分发。

Braid 另有一个 `feat/experiment-storage-lifecycle` 历史 worktree。迁移同步其 `.git` 指针到保留的元数据位置，不改变其源码、HEAD、分支或 index，不注销工作树。原指针和迁移回执留在证据目录。

构建输出、虚拟环境、缓存和本地配置仍由 ignore 排除。既有 `sources/braid/target` 链接及 `harness/skills/svc-*` 链接不移动；两者构建和材料消费路径保持一致。

## 验证与收尾

两目录的 `git rev-parse --show-toplevel` 均归 Factory26，独立 `.git` 已移出源码目录。父仓库待纳入 670 份普通文件；逐项读回未发现缺失、意外内容修改或可执行权限变化，仅 Braid 的 ignore、组件说明和 SVC 的缓存 ignore 按本次范围修改。历史 Braid worktree 的 HEAD 和状态保持原身份，原始读回回执保存在证据目录。

受影响的 Python 入口编译通过；`cargo build --locked --manifest-path sources/braid/Cargo.toml` 成功，保留 13 条已有编译警告及完整日志。实际执行本仓源码交接入口时，旧的子目录导出方式被拒绝，且未创建输出目录。只取得编译、Git、文件及命令反馈，不编写或运行 Factory/Braid/SVC 测试，不启动模型或实验。提交仅包含迁入源码和本批相关增量，保留其它工作区修改，不 push。
