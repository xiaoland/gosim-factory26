# 实验启动接缝改进

2026-10-03。用户要求查看 [重设计 I13 今晚无人值守实验](codex://threads/01a0fd22-fe3b-7430-9707-4534e7758565) 的运行轨迹，总结卡点、设计修复方案，再开展一轮开发基础设施改进，并明确使用 advisor。本指示授权必要源码、文档、非模型实际材料反馈；自主提交沿已有授权，不包含控制该实验、模型请求、远端 push、旧域迁移或清理。

当前在 WorkSSD 隔离分支 `feat/experiment-startup-dx`。主工作区有实验与文档负责人正在修改的未提交内容，保留原样；不接管 provider_fallback 的派发和运行修复。storage_producers 接续持有启动接口及原错调查，storage_judgment 持有独立方案判断，主 Agent 持有总体设计、入口和最终整合。

当前判断：重复困难集中在环境/SDK 的选择与发现、raw argv 手工组装、私有环境跨容器透传、资源服务能力组合。一次次重新派发才发现静态接缝问题，不能把“helper 存活”“controller running”当模型已启动。初步轨迹见 [会话摘录](trajectory.json)；具体原错与修复、待实施边界将在 [设计](design.md) 收敛。

沿项目约定不增加或运行设施测试，不把编译及局部材料操作称为模型或 Docker 启动成功。所有本任务产物位于 WorkSSD；不从来源会话的远端授权推导本任务的运行授权。

已采用 advisor 判断并实施单一 `arc-local-generate` intent operation，复用 ARC 矩阵的领域 job 构造；environment 承接宿主 SDK 和目标域，compiler 承接模型及输入组合，build/doctor 解释真实材料角色，adapter 承接模型环境与子容器资源服务。具体原错归 [调查](findings.md)，职责和采用理由归 [设计](design.md)。Advisor 复核发现并关闭目录材料误按 ZIP 解读、SDK 私有函数形状门槛、旧入口资源采样及环境合并问题；不新增一套通用执行协议。

真实 SDK 和已有 ZIP 的离线读回见 [包材料读回](actual-material-readback.json)，没有 package-manifest 的真实生产目录读回见 [目录读回](actual-directory-readback.json)。完整延迟生产编译成功，保留 from_production，未生产 runtime/material 或创建 cache；见 [计划读回](actual-plan-readback.json)。首次 endpoint 可选字段误判的原错和修复后编译 bundle 保留在本 worktree 的 `runs/experiment-startup-dx/offline-plan/`。这些只证明静态消费和编译，不证明发布、Docker 或模型执行。

实施范围与反馈归 [实施记录](implementation.md)，源码及两个生成入口内存编译身份归 [编译记录](source-readback.json)。[Intent 示例](example-intent.json)和[环境示例](example-environment.json)使用真实公开身份，但 authorization 仅离线用途。完成本任务的源码、设计和证据提交；不增加或运行设施测试。

本轮提交留在隔离分支，不覆盖主区正在进行的实验及文档修改，不改变旧冻结 executor。后续实际启动必须采用新冻结配方，由有该实验授权的负责人执行；完整打包、启动及热恢复耗时尚无对照，不能宣称已验收提速。
