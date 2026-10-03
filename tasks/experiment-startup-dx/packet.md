# 实验启动接缝改进

2026-10-03。用户要求查看 [重设计 I13 今晚无人值守实验](codex://threads/01a0fd22-fe3b-7430-9707-4534e7758565) 的运行轨迹，总结卡点、设计修复方案，再开展一轮开发基础设施改进，并明确使用 advisor。本指示授权必要源码、文档、非模型实际材料反馈；自主提交沿已有授权，不包含控制该实验、模型请求、远端 push、旧域迁移或清理。

当前在 WorkSSD 隔离分支 `feat/experiment-startup-dx`。主工作区有实验与文档负责人正在修改的未提交内容，保留原样；不接管 provider_fallback 的派发和运行修复。storage_producers 接续持有启动接口及原错调查，storage_judgment 持有独立方案判断，主 Agent 持有总体设计、入口和最终整合。

当前判断：重复困难集中在环境/SDK 的选择与发现、raw argv 手工组装、私有环境跨容器透传、资源服务能力组合。一次次重新派发才发现静态接缝问题，不能把“helper 存活”“controller running”当模型已启动。初步轨迹见 [会话摘录](trajectory.json)；具体原错与修复、待实施边界将在 [设计](design.md) 收敛。

沿项目约定不增加或运行设施测试，不把编译及局部材料操作称为模型或 Docker 启动成功。所有本任务产物位于 WorkSSD；不从来源会话的远端授权推导本任务的运行授权。

已采用 advisor 判断并实施单一 `arc-local-generate` intent operation，复用 ARC 矩阵的领域 job 构造；environment 承接宿主 SDK 和目标域，compiler 承接模型及输入组合，build/doctor 解释真实材料角色，adapter 承接模型环境与子容器资源服务。具体原错归 [调查](findings.md)，职责和采用理由归 [设计](design.md)。Advisor 复核发现并关闭目录材料误按 ZIP 解读、SDK 私有函数形状门槛、旧入口资源采样及环境合并问题；不新增一套通用执行协议。

真实 SDK 和已有 ZIP 的离线读回见 [包材料读回](actual-material-readback.json)，没有 package-manifest 的真实生产目录读回见 [目录读回](actual-directory-readback.json)。完整延迟生产编译成功，保留 from_production，未生产 runtime/material 或创建 cache；见 [计划读回](actual-plan-readback.json)。首次 endpoint 可选字段误判的原错和修复后编译 bundle 保留在本 worktree 的 `runs/experiment-startup-dx/offline-plan/`。这些只证明静态消费和编译，不证明发布、Docker 或模型执行。

实施范围与反馈归 [实施记录](implementation.md)，源码及两个生成入口内存编译身份归 [编译记录](source-readback.json)。[Intent 示例](example-intent.json)和[环境示例](example-environment.json)使用真实公开身份，但 authorization 仅离线用途。完成本任务的源码、设计和证据提交；不增加或运行设施测试。

本轮提交留在隔离分支，不覆盖主区正在进行的实验及文档修改，不改变旧冻结 executor。后续实际启动必须采用新冻结配方，由有该实验授权的负责人执行；完整打包、启动及热恢复耗时尚无对照，不能宣称已验收提速。

## 架构层复核接续

用户质疑是否因 Ponytail 选择最小修改而没有落实长期、根本正确，随后明确“是的，继续”，并指出来源会话仍持续暴露问题。本轮以长期正确及三类端到端耗时为判断标准，不以最小 diff 作为选型依据；Ponytail 仅提示避免无效复杂度，不能否决必要的职责划分。上一轮提交 `c2274d86` 是局部实现，不作为整体设计完成证明。

继续由 storage_producers 持有全执行场所、variant 和恢复生命周期的实际边界调查，storage_judgment 持有独立 HLD 判决，主 Agent 持有新轨迹及整体设计收敛。先对照已批准的 DX HLD 与实际实现，识别尚未贯通的责任，再细化必要源码调整；不为新错误立即堆补丁，不控制来源实验。

新消息摘录见 [后续轨迹](trajectory-update.json)。来源负责人报告 exp20 复用旧资源样本、exp21 消费宿主输入路径而容器无该路径，已派生 exp23；报告的修复和启动不等于本分支已解决或首次模型活动成立。根因涉及实际执行域中的资产成员映射、服务绑定和服务生命周期，需要共同边界解释。

已采用 [全生命周期调查](architecture-evidence.md) 与 [advisor 判决](architecture-judgment.md)，更新现有 [设计](design.md)：四项共同合同贯通定义组合、域内装配、执行上下文和 state/writer 交接；不推翻已有 HLD，不再以 ARC wrapper 作为独立完成切面。Storage_producers 接续持有具体 LLD、caller 迁移/删除和反馈计划，主 Agent 复核范围与采用依据。该调查已完成并进入下述已授权实施；三类耗时及跨域实际运行仍未取得验收。

[具体实施准备](architecture-plan.md) 已完成，advisor 独立纸上预演通过。闭环项包括设施代码的精确生产/部署失效、capture 持有的原位修复与新 generation、半失败重入、原子写权交接及交接前旧消费者转不可变快照。Hosted 保持真实能力和外部关联；未知平台身份不造字段。复核范围是公共生产组合、fresh/prepared/child 装配与 bootstrap、四 I14 消费、公共 capture/state 交接及单次封口。用户已明确开工，源码实施见下节；纸上推演不作为真实运行验收。

后续轨迹截取已推进到来源 exp25：exp23 的宿主 adapter 修改未进入实际冻结 runtime，负责人转而修改包内 layout fallback，exp25 仍处于 copy-helper/domain channel，未确认模型活动。该现场继续由原 owner 持有，本任务不消息介入或运行控制。

## 架构实施授权与当前责任

用户于 2026-10-03 明确指示“开始改动”，授权实施 architecture-plan.md 已复核的完整范围。工作继续位于独立 feat/experiment-startup-dx worktree；主工作区在途修改保留。Storage_producers 持有定义生产、交付投影、公共装配/bootstrap 及 caller 迁移；Exp_platform 持有受管状态、capture/repair/generation 和 writer handoff；主 Agent 持有单次终态封口、输出 member 关系和集成采用。Advisor 负责重大边界判断与独立复核。

本轮源码实现与 advisor 最终定点复核已完成。SDK terminal child 的公共 checkpoint source 选择已接入 schema4，普通 Local 交付与完整恢复捕获已经分流；反馈边界及实际原件见 implementation.md。尚未取得新的实际 Docker、模型运行或三类耗时验收；采用新分层执行器需要由实验 owner 冻结新制品，不能将工作树变更当作旧运行已部署。


实现期间较早的源会话证据见 trajectory-implementation-update.json：当时实验 29 的外层 reviewer execution 为 running，资源处于 sending，尚未观察到实际生成容器；cleaner 外层已退出，资源为 not-started。此记录保留当时身份，不能覆盖下述更新。源 owner 另补 legacy monitor 的 attempt 接口。本轮 projection 显式分开外层执行与已保存的实际 child_execution；没有 child 出生/状态时显示具体缺口，不以 supervisor running 代替模型开始。此证据仅用于设施设计，不接管或控制源实验。

用户随后报告 reviewer 于北京时间 11:39 进入远端应用，约四秒后因 run.py 与包内哈希清单不一致退出。真实包与原始错误的只读核实见 experiment29-package-readback.json。用户还报告 cleaner 被五个未释放预约阻塞，11:46 仍有三个旧预约及四个辅助容器；本任务修复预约、实际创建及失败关闭的生命周期，不直接释放这些现场资源。

现存 A2 的 provider 保存事实已由新的统一 projection 实际解读并渲染，见 architecture-provider-readback.json 与 architecture-provider-render.txt。会话生命周期、连续观测、资源等待原因及 native 证据覆盖范围来自原生产者；读取时间不充当远端观察时间。两份读回时间不同，monitor-latest 原件持续更新，不把样本数量差异误判为身份变化。未新增采集、分类规则或平台请求。

用户补充存储约束的准确含义：项目产物不能放在 Mac mini 内置磁盘，并非只能使用 WorkSSD 这一卷名；远端执行数据可保留在远端。本任务继续使用既有 WorkSSD，不迁移数据或推导新的实验运行授权。后续存储选择核对真实挂载、文件系统与容量。

最终收口：40 份改动 Python 源码与 11 段静态嵌入 Python 完成内存编译，git diff --check 通过；身份见 architecture-source-readback.json。原 owner 已冻结源码，无在途实验或控制操作。Advisor 的源码接缝审阅只用于实现采用；三类耗时及完整实际恢复仍未验收。提交仅本隔离工作区本任务内容，不覆盖主区并行工作。
