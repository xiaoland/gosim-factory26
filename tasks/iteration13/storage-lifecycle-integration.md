# I13 存储生命周期成果合入

2026-10-01。用户开工原话：“好的，也可以委派开工 合入 experiment-storage-lifecycle”。本批完成 Factory/Braid 源码、当前 I13 接线、长期文档与限定提交；不包含模型实验、远端部署、建立宿主 runtime、历史/I12 GC plan、GC apply、现场清理或 pause/resume。

## 来源与合入方式

Factory 来源为 `feat/experiment-storage-lifecycle`，基线 `27612ba`、HEAD `4e1bb08`，工作树在 `/Volumes/WorkSSD/Development/.worktrees/experiment-storage-lifecycle/factory26`。独立 Braid 来源为该树 `sources/braid` 的 `e87b82b`。来源任务和设计先行核对；主线同路径原先未跟踪的早期方案保存在 [历史起点](../experiment-storage-lifecycle/history/)。

目标 Factory 起点 `b8f8cd9`，目标独立 Braid 起点 `49d5d5f`；两者已有大量未提交修改。采用逐文件来源 delta 三方合入，保留目标新功能及 dirty；源码交集为 runtime 新补丁、Braid CLI 和既有 telemetry 参数修正。来源 I12 的收尾只映射到当前 I13，不修改冻结 I12。来源旧 Deployment index 的操作增量写回现有拆页，不恢复旧组织。

| 来源提交 | 本次落点 |
| --- | --- |
| `57cd761` | Factory 默认摘要、core decision 回执及 I13 回执授权后才删 work。 |
| `e222296` | lab schema v3、冻结 storage policy/解释器依赖和启动容量预检。 |
| `cfc7aa2` | 异步占块观察、软阈值派发门禁、硬阈值受控停止与外部资源 unconfirmed。 |
| `956de0b` | 稳定宿主 Python 资产回执、同一 launcher 的 controller/job/inspect/cleanup。 |
| `e6e1a5c` | 失败关闭的只读 GC plan，精确 work 候选与引用/保护核验。 |
| `4e1bb08` | 来源授权和恢复点历史，继续保留于本任务。 |
| Braid `e87b82b` | 默认 summary/显式 portable、源材料 bytes/artifacts 指标及操作说明；目标提交 `8325ed6`。 |

Factory 合入提交通过本文件的 Git history 查得；限定增量与实际提交身份另保存在证据根 `factory-integration-commit.txt`。不通过 cherry-pick 把 I12 修改或无关 dirty 一起带入提交。

## 集成时收敛的边界

独立 advisor 发现来源回执只检查目录存在，native-config 半复制及未保存原文仍可能授权删除 work。本批将原文保存独立于关联覆盖：实际归档复制/读取错误、manifest 声明的原文缺失/摘要不符、observer 原件读取失败阻塞回收；已经保存 native/unparsed 原文、仅身份或观察关联不全时保留诊断缺口。归档辅助错误不改写已交付应用结果，失败回执保留 work 和 recovery-workspace。

来源接受四级 archive_level，但执行只实现 decision。本批 CLI/schema v3 只接受 decision，避免声明 resumable 却删除其 workspace。score-only/resumable/forensic 继续作为设计方案，显式 portable 手工导出仍可用。历史 v1/v2 冻结控制器、旧 ZIP 与恢复材料不迁移，旧兼容启动仍标 legacy-unbudgeted；没有原文保存确认的旧回执不能成为 GC 候选。

GC 保留 I12 识别并加入 I13 活跃/终态保护，所有输出仍为 reclaim_authorized=false。Console console-runs.json 尚未被解释；host binary、shared submission、state/native 原路径和访问容器 mounts 必须显式 protect，停止 server 不解除引用。此处没有 Console 生命周期实现或历史清理授权。

端到端核对还发现新应用复评入口 evaluate.py 仍用 sys.executable/schema2 绕过保护。经同一 advisor 核对，本批必要适配为显式 host-runtime 和复评自身预算、同一 launcher 的执行/资源 handler、schema v3；不继承来源生成 run 的现场解释器或预算。通用配方/稳定资产框架未扩建。

## 实际反馈与未验范围

证据根为 `runs/iteration13/storage-lifecycle-integration-20261001/`。starting-state.json 保存两个目标仓库及两个来源仓库的起点，before/ 与 handoff-before/ 保存涉及文件的 dirty 和共享写权交接；validation.json、check-*.log 保存编译及 CLI 结果。

Python 3.13.15 编译本批 11 份 Python 文件通过。`cargo build --locked --manifest-path sources/braid/Cargo.toml` 通过，保留 13 个当前工作树 dead-code 警告。lab、gc-plan、arc_matrix、evaluate、runtime host-lab 与 Braid portable CLI 帮助实际读取通过。

标准 prepare-only 使用既有允许输入与 runtime，明确传当前 sources/braid binary，写出真实 I13 请求、profiles、launchers 和 15 项技能；没有调用 Braid/模型。结果为 `prepared/.factory26/20261001-074056-94828e68`，prepare-operation.json 保存命令/身份，prepare.log 保存原始输出。另一个技能实现者独立读回共同材料，回执在其 `prepared-material-review-final.json`。

sources/braid 源码树与 third_party/braid 不同，但既有 sources/braid/target 链接指向 third_party 的 target；本次 Cargo 明确使用 sources/braid/Cargo.toml，material 中 resolved binary 路径因此位于共享构建目录。编译源码哈希与该链接均在 validation.json。binary SHA-256 为 `1f67dcea1b6309b4b505187debc8a18c168460bd5043273709735209b369b130`，不能仅用产物路径或 Git HEAD 冒充完整源码身份。

prepare-only 提前返回，未运行 finalizer。真实归档成功/半复制失败/删除行为、预算观测和 TERM/KILL、资产创建/消费、GC 候选扫描、summary/portable 传输及重建、新复评实际执行仍未验。编译、源码核对和材料生成不作为这些运行行为的保证。后续须按具体输入、预算和完成条件另行取得实验或现场操作授权。
