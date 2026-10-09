# 实验过程与基础设施 DX 复核

## 原 lab.exp 交付状态（2026-10-03）

本 packet 只持有原 lab.exp 阶段的交付与证据，不作为当前 run 的启动或模型授权入口。当前重构与未验边界归[决赛设施任务](../finals-experiment-loop/packet.md)。

本任务的 hard-cutoff controller/独立 runner 基线已实施并整合到原 main 工作区。接续负责人为[开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)。交付时三个 owner 分别负责材料语义、域存储/保留/输运和执行效果/准入，主 Agent 负责公共入口、环境、冻结代码与 Console 接缝整合。

已交付：

- 新写入切换到 lab.exp，旧 writer 退役；旧 recipe 不自动进入新 writer，旧控制委派原冻结 executor。
- controller/runner、compile/build/doctor/recover、按 kind 切换、冻结代码复用、产物关系投影及 Console writer 接缝已接通。
- 定义、生产选择、实际环境解析和运行事实分别保存；artifact、runtime、telemetry 身份未合并或重写。
- 该旧协议的查询由对应冻结执行器提供，工作区兼容入口是 `python3 -m lab.exp status EXPERIMENT --json` 及 `lab.exp monitor`；按所属记录的冻结版本解释，不修改旧程序或旧冻结记录。
- 交付时原件和离线反馈记录在 `runs/infrastructure-dx/`，合入与三方核对在其 `merge-20261002/` 子目录。这些原件当前不在本 checkout 中；下表是交付记录，不是本次重新执行的结果。

## 用户授权与安全边界

用户先认可调查和方案，随后明确支持 hard-cutoff、建立干净基线，并授权：“开工；你可以自由提交。”之后又授权继续推进和整合到 Development/factory26 的 main。授权覆盖本任务源码、文档、非模型离线材料操作和当前提交，不包含远端 push、模型/官网运行、旧来源停止、共享 daemon 接管、Console 部署、GC apply、历史清理或迁移旧 run。

本任务不把编译、离线读回、消息送达或局部计时当作真实生命周期验收。没有实际 Docker 故障、controller 断开、child budget/cgroup、材料变更后的完整热恢复、官网写入/评分或非空遥测冲突/去重现场时，保持未验。

## 真实离线反馈（截至交付时）

| 操作 | 观察 | 证据 |
| --- | --- | --- |
| 1.4 GiB reviewer 材料首次生产/无变化复用 | 29.28s / 14.55s，同 material identity 与 manifest | ../../runs/infrastructure-dx/material-production-20261003/current-contract-production.json |
| prepared 接收、同请求重入、独立 workspace 装配 | 50.03s / 18.04s / 44.34s | ../../runs/infrastructure-dx/domain-store-20261003/receipt.json |
| 公共 build：缺 runtime / 已有环境新 run / 重入 | 2.57s / 0.55s / 0.28s | ../../runs/infrastructure-dx/public-build-20261003/receipt.json |
| 最终整合源码公共 build A / B / A 重入 | 0.64s / 0.40s / 0.31s | ../../runs/infrastructure-dx/public-build-20261003/final-public-feedback.json |
| 新恢复 prepared 生产/语义读回 | 148.94s / 46.90s，partial | ../../runs/infrastructure-dx/material-production-20261003/final-validation.json |
| 阶段 application 冻结 | 指定 develop commit 的 195 文件应用 | ../../runs/infrastructure-dx/material-production-20261003/application-production.json |

这些是单次顺序操作，未控制 OS cache；离线 build 耗时不是启动入口耗时。新恢复 prepared 因八个 Git 目录历史重建、获取窗口未知而保持 partial；不宣称热修复 hook 或完整恢复已验收。

## 当前未完成与下一步

交付时，实际 Docker 装配/ready/入口、controller 断开、child 预算/cgroup、材料变更后的完整热恢复尚未完成验收。后续材料与运行进展归各实验 owner；I14 当时的实验入口为[夜间 packet](../iteration14/overnight-plan/packet.md)，其当前后续工作沿该 packet 的接续说明确认。接续本任务时先采用其可用反馈，再按实际授权补齐完整打包、启动入口和热恢复三个区间；不能因本页记录了历史限制而要求已取得许可的实验重新申请。

## 稳定证据入口

- [完整历史 packet（截至 2026-10-03）](history-20261003.md)
- [设计](design.md)、[实施准备](preparation.md)、[技术说明](technical.md)
- [运行说明](../../docs/deployment/index.md)、[恢复手册](../../docs/deployment/recovery.md)

历史 packet 保留原授权、调查、方案、实施和验收原文；本页只维护当前结果、owner 和未验边界。
