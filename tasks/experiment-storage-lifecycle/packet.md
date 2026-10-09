# 实验存储生命周期

## 当前状态（2026-10-03）

本任务已完成既有存储预算、归档回执、稳定 Python 资产、监控载体和定义/state 分离改动的集成。接续负责人为[开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)。交付结果是：

- Braid 摘要导出、Factory archive.json 回执、预算门禁、稳定宿主 Python 资产和只读 GC plan 已合入；历史清理、GC apply、迁移和 I12 现场处置仍未授权。
- `302878bc` 完成有界监控证据保留；四个新 I14 入口、checkpoint/prepared v3 和定义/state 分离已接通。
- 既有真实终态 ZIP 的监控读回通过；交付时普通轮次 ZIP 释放、完整 prepare、Docker 启动和热恢复未验收，不据此推断后续实验没有产出新材料。
- 当前不运行模型实验，不删除数据，不控制 Docker/官网，不恢复或迁移旧现场。

## 目标、授权与稳定约束

目标是为 runtime、workspace、Braid/native/OTLP、应用和评分证据建立可验证的归档、预算、引用和安全回收边界。用户于 2026-09-30 授权改进 Factory/Braid 及内部采集，并允许提交；2026-10-01 又授权合入 I13。授权不包含模型实验、历史清理、I12 现场迁移、VHDX 停机或真实运行控制。

2026-10-03 用户进一步授权“是的，这些属于实验基础设施，请进行优化”，随后明确“这个分层没错；我们开始应用吧/开工吧？”。这覆盖监控载体、四个新 I14 variant、公共材料接线、SDK 装配和 checkpoint/prepared 消费边界；仍不扩大到运行控制或历史清理。

普通实验使用 decision 归档级：长期保留应用/replay、必要 Braid state、关联 native 原文、评分和错误；完整 OTLP、整棵 workspace 仅在明确 resumable/forensic 时保留。目录名、completed、文件 hash 或单独 Git 提交都不能证明可回收或恢复完整。

定义资产、派生输入和可写运行状态属于同一执行生命周期的不同材料。variant 声明语义，设施负责真实装配、引用保留和状态捕获；旧冻结记录按原合同解释，不能用新布局改写历史身份。

## 已交付和未验边界

已有提交 e87b82b、57cd761、e222296、cfc7aa2、956de0b、e6e1a5c 及 I13 合入已记录在历史页。当前真实反馈：终态 ZIP 164,995,785 字节保持原样；6,508,663 字节永久判定证据保留，15,236,514 字节提取 scratch 在持久化后释放；资产 COW、sealed handover、同请求重入和 materialize 读回通过。

这些反馈只证明已有材料的局部机制。交付时缺少新 I14 冻结 runtime/material 和 wrapper 终态 namespace 原件，四入口 prepare、Docker 生命周期、SDK 正向组合捕获和热恢复未验收；没有证据证明每次实验节省 10 GiB。后续运行与材料归[夜间 packet](../iteration14/overnight-plan/packet.md)，本任务先采用实际新反馈，再沿其已有授权补齐适用的验证，避免重复生产和重开已完成工作。

## 稳定 owner 与证据入口

存储制品、终态和输运由 storage_producers 负责；监控证据由 exp_platform 负责；公共执行投影和整体整合归实验 DX owner。其它任务的 I13/I14 现场、模型和官网 owner 不因本任务文档而改变。

- [完整历史 packet（截至 2026-10-03）](history-20261003.md)
- [实验 DX 当前入口](../experiment-dx-review/packet.md)
- [空间调查](investigation-20261003/findings.md)
- [监控操作回执](investigation-20261003/monitor-operation.json)
- [资产操作回执](investigation-20261003/asset-operation.json)
- [运行说明](../../docs/deployment/index.md)、[证据说明](../../docs/deployment/evidence.md)

历史 packet 保留原授权、实施过程、事实和限制；本页只维护当前结果和未验边界。
