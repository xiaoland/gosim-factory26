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

## 显式调度职责复核（2026-10-03）

用户怀疑 controller 自动创建/派发 attempt 及两秒轮询属于功能过度设计，要求 attempt/run 由使用者主动调度。本轮进入只读调查与设计，未扩大前轮实现授权。主 Agent 调查并保存 scheduling-review.md、scheduling-review-readback.json，稳定 advisor storage_judgment 独立判断。主工作区并行改动与源实验不受本轮控制；尚未修改源码或运行实验。上一轮实现也保留这一职责混合，不能视为已解决。

Advisor 已完成独立复核并采用：删除隐式调度职责，保留单次执行闭环；补充控制不应先等待完整 workspace 下载、执行容量不应与归档耦合的边界。结论为设计建议，未实施。

## 后续独立验收反馈（用户要求在当前职责复核之后处理）

用户提供主区 runs/developer-experience/post-infrastructure-acceptance-20261003/report.md，并要求“你处理完手上这件事情还要处理这个”。已读取；报告针对 d4ac01dd，结论为部分通过，不能宣称打包、启动或恢复提速已验收。后续应处理：合入前保留 main 3074b476 的缺少 harness-manifest.json 错误说明；资源等待结构化详情在文本中被截断、重复长证据路径及证据入口区分不足；多实验比较入口缺口。完整打包、实际首次入口/模型受理、合法 checkpoint 同域恢复与三类耗时对照仍未关闭，按具体实验既有授权采纳真实反馈，不从该报告推导新模型运行授权。当前先收敛显式调度职责，随后逐项处理报告；报告列出的未验项不是已证明源码缺陷。

## 全范围职责复核（2026-10-03）

用户明确“不仅如此，所有的职责混合问题都要处理”，随后要求“推进”。沿上一条回复约定，本轮先整体只读调查、设计和advisor复核，不擅自进入新的源码实施。复核覆盖定义/编译/生产/装配、显式调度、单次执行、控制/观察、准入/state、capture/repair/recovery、传输/归档、projection/analysis/Console与相关variant接缝。原owner继续负责：storage_producers负责production报告，exp_platform负责execution报告，storage_judgment负责HLD取舍，主Agent负责projection、验收反馈及整体整合。各owner只能写本task对应review文档；不改主区，不接管源实验，不测试/运行/网络/控制。复核将以整体职责与公共操作合同收敛，不新增自动开关或workflow engine。

整体方案 responsibilities-design.md 已完成，production/execution/projection 与 advisor review 提供证据和采用依据；主区与交付源码身份见 responsibilities-review-readback.json。已纳入验收报告的诊断回归、呈现缺口与未验界限。选择是按三批贯通唯一新写入合同，不保留隐式scheduler模式、不扩大为通用控制平台。下一阶段收敛CLI/request、目标依赖、场所装配、恢复事务及所有公共caller删除迁移；本轮未改源码、未提交、未编译/运行/控制资源。

## 全范围实施授权与在途状态

用户针对已交付的整体方案明确指示“开始。”，授权 responsibilities-design.md 范围内的源码、文档与必要验证；不是新的模型/Docker/官网运行许可。本轮在feat/experiment-startup-dx隔离区实施。root持显式start/retry/request与CLI/projection/artifact成员运输、整体文档；storage_producers持compile/build/生产/装配/SDK/variant及controller限定材料函数；exp_platform持执行/控制/恢复/准入/Console及controller限定操作函数；storage_judgment持重大判断。所有owner保留主区并行改动，按函数责任避免互相覆盖。

新写入recipe为schema3，旧schema1/2只保留状态读取与原attempt控制，不重启旧scheduler。显式调度与角色代码部署、成员运输接口已协调；完整生产、恢复、资源关闭与投影集成仍在实施。不会以编译成功宣称三类实际耗时已验收。

本轮已完成整体源码迁移和实际材料反馈，采用依据见 [实施记录](responsibilities-implementation.md)。Production、execution 的原 owner 已分别完成生产/装配、单次执行/恢复及调用迁移；advisor 最终定点确认未知效果、成员接收/GC、容量释放与显式 retry 的采用缺口关闭。主负责人完成显式 CLI、按 owner 组合的 projection、多目录入口、成员解析/运输及权威文档整合。源码最终身份归 responsibilities-source-readback.json；执行 owner 的阶段内嵌脚本编译归 responsibilities-execution-compile.json。

实际现有 intent 离线编译约 0.50 秒，12 个真实 I14 目录一次文本查询约 0.37 秒，真实冻结 executor 的 4477 字节成员接收保留原引用/hash且没有完整 payload。这些不是设施测试或 Docker/模型启动验收。独立验收报告的 add_note 回归及状态呈现缺口已处理；完整打包、首次启动、热恢复的端到端耗时仍未获得实测。提交留在本隔离分支，不推送、不合入主区，不处理源实验运行资源。


## 噪声反馈后的诊断与设计（2026-10-03）

用户要求继续分析主区 `runs/developer-experience/noise-analysis-20261003/advisor-decision.md`，允许独立判断。本轮先完成诊断和改动范围设计；没有修改源码、合入主区、控制实验或发起模型运行。交付仍是 `15a1a2a2`，主区 `9e5eeeac` 及其在途改动保留。用户另已明确 advisor 不充当 reviewer；此前 advisor 的定点采用判断不计作独立实现审查或验收，后续职责据此纠正。

认可成本报告的归因边界：927 MB 是本地递归扫描产物，不是模型实际收到的输入；累计缓存输入不是常驻指令成本的分项计量。既有任务条件不同，不能以两次耗时差宣称设施独立收益。当前不建立检索服务、状态数据库、计量框架或新的文档体系。

文档问题是两侧成果未整合。主区 Lab 与恢复入口已经简化，但实验 schema 和 build/start/recover 示例仍沿旧合同；交付分支的新协议集中在大入口，尚未采用主区的组件导航。下一步沿用主区短入口和分主题组件正文，按交付 CLI 的真实 schema 3、单 job、请求重入、输入显式绑定、recover 默认准备与 `--execute`、seal/export 分责更新。定义与生产归 `lab/exp/experiments.md`，执行和请求归 `execution.md`，成员运输与恢复证据归 `artifacts.md`；旧执行器合同仍按原身份保留。组件本地 README 必须以交付源码核对函数和行为，不能直接复制主区运行中修改。合并文档不等于合并主工作区或接管运行。

Query_scope owner 使用已有真实 `stage-a2/experiment` 读取默认 status 和 monitor：分别约 0.081/0.065 秒、均 3396 B，输出相同。该历史实验只有一个 job 和一个 attempt；已终态 CANCELLED，但仍展开两个 session/native 窗口、整组资源等待诊断及多个证据路径。因此有证据支持考虑默认摘要与显式详情，没有证据优先增加 job/attempt 筛选器。原始输出在本 worktree `runs/experiment-startup-dx/query-scope-20261003/`；实际 CLI 帮助已确认 start 必需 `--job/--request-id`，recover 另支持 `--action/--execute`。这些只读操作不是新实现验收。

拟采用同一 projection 的默认可行动文本及 `--details` 完整文本，JSON 保持完整合同。首层保留 experiment/job/attempt 身份、实际执行与平台状态、阻塞或具体原错、partial/unknown、影响动作判断的证据缺口、事实生产者和观察时间、下一操作及原件入口。诊断层保留所有资源数值、session/native 证据、各 facet 的完整来源和历史。尤其不同 producer 的观察不能合并成一个新鲜时间；终态运行中的旧 resource_wait 不能冒充当前启动阻塞，unknown 也不能因收起诊断而消失。不得以固定字符数裁掉错误，也不新增第二份状态事实或查询时重新采集平台。

主负责人持有文档归属与总体设计，query_scope 持有单问题真实观察，query_design_advisor 仅解决默认呈现与选择器的取舍，不读实现、不充当审查或验收。改动范围确认后再实施；反馈沿现有真实原件及公开 CLI 获取，不重复冷任务、多轮模型或设施测试。验收需确认摘要未隐藏影响下一动作的错误、身份、新鲜度和恢复拒绝条件，而非仅追求字节减少；完整打包、首次启动和热恢复耗时仍是上一轮未关闭项。


用户进一步明确“对于 agent 来说，应该将它对待为人类，JSON 不总是 agent-friendly 的，而且经常不是”，并指向相邻 `svc` 与 `InKCre/core-py` 的资料。主负责人只读核对 SVC 的权威 PRD 与 renderer，query_scope 原 owner 只读核对 InKCre 的 CLI 呈现、错误/退出码设计及实际输出源码；没有修改参考仓、运行服务或测试。已将显式格式、不依赖 TTY、按动作语义组织、渐进续查、有限呈现不丢边界、命令结果与领域终态分离等约束整合到既有 responsibilities-design.md，而非新增 CLI 框架或竞争文档。InKCre 当前默认对象仍多为 pretty JSON，HTTP 默认错误和临时目录策略也不能直接照搬；设计与实际能力分开采用。本轮仍处诊断与设计，没有修改源码。


## Agent-friendly CLI 优化实施授权

用户于 2026-10-03 明确指示“开始修改”，授权前述短导航与新协议整合、同一 projection 的默认行动文本及显式完整诊断。主负责人持有 CLI/renderer、实际保存记录反馈及采用；storage_producers 接续持有组件文档、短入口和历史合同迁移；cli_review 是独立源码 reviewer，不是 advisor，也不承担实际运行验收。本轮保留主工作区及参考仓原样，不扩大到 runtime/cache 默认落点、模型或远端执行。

默认摘要使用已保存事实，详情只改变呈现，不请求平台；JSON 生成结构不改。错误文本不再按固定字符数剪头尾。源码审查发现的辅助事实时间遗漏、资源原错过滤和独立观察/执行身份遗漏已修正，终态资源诊断依执行与平台终态归为历史，详情仍完整展开。所有 Python 修改内存编译，真实 stage-a/stage-a2 只读单项及批量 CLI 输出保存在本 worktree `runs/experiment-startup-dx/agent-friendly-cli-20261003/`。这些不是完整运行或性能验收；完整打包、首次启动、热恢复仍未关闭。


CLI 已完成默认摘要与 `--details`，同一保存 projection 的 JSON 路径保留；两种文本均显示 job/attempt/incarnation/run/submission，具体原错不剪裁，独立错误观察在首层可见。正常 session/native 窗口与完整资源数值放入详情，异常会话分类仍保留定向依据。实际旧 stage-a2 单项默认 2177 B（原 3396 B）、详情 4449 B；两项批量默认 4351 B、详情 8036 B，均成功读取。当前查询 0.08–0.14 秒，不将字节变化推导为总体 token 或运行性能收益。cli_review 提出的三项遗漏及历史诊断判定均已处理；审查属于源码反馈，不替代真实运行验收。源身份和操作原件见上述 `source-receipt.json` 与 `final-operations.json`。


本轮文档整合已完成：25 页的 339 个本地链接及片段由文档 owner 实际读取确认。四个入口共 15669 B，原 101528 B；详细协议归回组件与历史正文，未删身份或恢复证明。默认辅助遥测同时保留 producer flush，最终单项摘要 2203 B、详情 4461 B、两项批量 4522 B，最终原件为 final-revised-operations.json。三个修改 Python 源码最终内存编译及 diff 检查完成。按已有自主提交授权在隔离分支提交当前任务；不推送或合入主区。本轮仅交付查询呈现和文档入口优化，不宣称所有 CLI 已自然语言化，也未关闭完整打包、首次启动和热恢复的性能验收。
