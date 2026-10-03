# ARC 本地生成的启动边界

2026-10-03 接续说明：以下 ARC 接缝方案已作为 `c2274d86` 局部实现，不能代表整体架构完成。用户要求以长期、根本正确重新审视后，采用本文末尾的架构修正；既有 [实验设施 HLD](../experiment-dx-review/design.md) 继续是整体职责依据。

## 问题与采用的判断

本轮轨迹显示，存在且内容冻结的 SDK、runtime 或镜像没有自动取得正确用途。调用者反复手工组装通用 argv，把宿主解释器当 SDK、镜像内入口当宿主 SDK，漏掉 resource limits、完整 endpoint 或模型环境；这些错误在真实传包和新 attempt 后才暴露。Hosted 的同题并发约束又被扩展成全部生成场所的约束，既有 WSL/sfp7 执行设施未被正确采用。具体原错归 [调查](findings.md)，对话摘录归 [轨迹](trajectory.json)，不能把某一早期 running 回执当当前模型已启动。

用户已经授权总结、设计及本轮设施改进。Advisor 独立复核后认为应先补公共领域编译边界，再修只读检查的实际协议缺陷；只新增 doctor 显示项目不能消除手工 argv。设施提供已声明的执行类型，实验负责人继续决定生成场所、模型、费用、矩阵、恢复损失和运行控制。不从本次调查推导任何新模型或域操作授权。

## 操作、选择与实际执行

高层 intent 的 `variants.<name>.generate` 可声明单一 `operation: "arc-local-generate"`，使用现有 inputs、limits、case 和模型选择。不再为同一 operation 接受手填 command/backend/external_docker 的第二套权威。现有 environment 增加 ARC 的物理选择：宿主 SDK 源码及执行 target；Python 仍是宿主解释器，Harness runtime 仍是材料生产输入。Darwin 控制宿主驱动远端 Linux Docker 是合法关系，不能据其 Python 平台否认 Linux 执行材料。

领域 job 构造从 `arc_matrix` 现有实现复用，与 intent compiler 采用同一函数。它生成当前 `local + external_docker` recipe、adapter argv、资源 limits、运行环境和 application 输出合同；不增加 backend、常驻注册服务或新的 attempt 身份。生成与官网评分仍是独立 job，不能把评分槽等待当本地生成不可启动。

`from_production` 在 compile 时保持引用，只核对生产者用途及必要组合事实，不要求材料先安装。Build 取得实际材料后，SDK 角色检查与材料能力核对使用公共 ARC 输入解释；doctor 复用这些事实，待生产与已兼容分别展示。新操作的宿主解释器由实际已冻结 runner runtime 消费，不以 `{runner}` 同时充当解释器及 SDK。公开编译计划保留生产依赖与展开依据，旧冻结 executor 继续原合同。

## 校验与服务的职责

SDK 的检查只针对现有 adapter 实际调用的 `local_submit.py`、`run_container` 和 `main` 接缝。错误使用镜像内 `local_runner.py` 应在实际输入绑定时解释为 SDK 角色不兼容；不制造 stub，不以文件存在代替可消费事实，不建设另一套版本别名或缓存。静态角色检查不能证明容器运行或模型受理。

只读 readiness 的 admission labels 必须与现行协议2权威规则一致，删除旧 helper/slots 判断，而不再叠加另一道校验。Doctor 不升级旧域、不创建 helper、不自动填 handoff 或授予启动许可。历史权威确需迁移时仍归当前域负责人及其具体授权。

公开模型选择归 compiler；ARC adapter 对 SDK 子容器提供相应绑定和明确声明的凭据变量。公开回执只保存变量名、配置摘要和实际传播事实，不保存凭据值。父进程环境存在、包装器存活或 copy-helper 创建都不能证明子容器已接收模型环境。

ResourceEvidence 同样属于实际执行域。外层 Local runner ready 不代表 SDK 子容器 ready，不能把父 sample_path 直接透传来冒充采集。ARC 的组合入口应在进入 Harness 前提供材料声明需要的服务。当前实验的 collector 修复与派发继续由原负责人完成；本轮隔离开发采用确认的修复，不接管其运行。

## 验收与整合

实现需要在同一操作中覆盖未生产输入的计划、真实 SDK 和材料的生产/解析，以及实际模型环境和子容器服务组合。编译及现存材料离线操作按项目约定执行，不增加设施测试、模拟容器或 smoke。实际 Docker 与模型活动只采用来源负责人保存的真实原件；没有明确的对应执行版本或观察时保持未验，不能把新源码编译成功称为重现了真实启动。

代码在 WorkSSD 分支 `feat/experiment-startup-dx` 隔离开发。主工作区的实验救火与文档改动保留原样；整合时只采用本任务增量。必要入口及操作方法更新其当前权威文档，不复制整个实验设计或把公共操作藏在一次性启动脚本。关键完成依据仍是减少原轨迹里的手工接线与传包后才发现的错误；完整打包、启动和热恢复耗时若未取得对照，不宣称已经验收提速。

## 当前采用的架构修正

独立 [证据调查](architecture-evidence.md) 和 [advisor 判决](architecture-judgment.md) 确认，问题不是原 HLD 缺少 controller/runner/资产/域职责，而是这些职责没有成为共同的实际入口。Fresh 的 `_assemble` 直接返回 workspace，prepared 才具备装配；variant 和 SDK wrapper 分别解释路径与服务。新轨迹中的服务透传、旧样本及父域路径问题均不能靠另一轮 wrapper 补字段收敛。

本轮采用四项贯通合同：生产者输出独立定义组合，后端完成目标域装配，该 namespace 的公共 bootstrap 提供执行上下文，域权威完成 state 与唯一 writer 的交接。它们是现有组件的责任，不是四个新中心服务。具体字段及 caller 迁移在实施准备中收敛，不能先加 JSON 再保留原消费者旁路。

定义组合直接引用 runtime、技能、variant 与设施支持资产；ZIP 和 SDK 自包含目录是交付投影，不再是所有场所内部的材料单位。组合改变只使实际依赖失效。装配记录 `reference + member + local_root`，保留原成员并组合其后缀；foreign root 是来源信息，不能拿来解析本域路径，也不能按 basename 猜成员。Store/retention 仍由控制面拥有，不要求容器访问控制宿主路径。

Fresh 与 prepared 消费同一执行上下文：冻结定义、独立 state、派生输入、真实本域解释器/入口、服务 ready 及相应 receiver/sample binding。必要服务由本域 bootstrap 持续拥有和关闭，旧环境变量仅由同一上下文派生；variant 继续负责 Braid/Pi 配置、应用、native 状态和恢复兼容性，不自行猜另一套设施服务。Local 的读隔离与 Docker 的真实 RO 挂载不混称同一保证，Hosted 只暴露其实际交付/观测能力。

同域热修复保留受管 state，关闭原入口及已登记 writer，取得一致切点与快照，替换变化定义，按恢复兼容性把写入权交给新 incarnation。Snapshot 和旧执行证据保持不可变，active state 不因新 attempt 必然完整复制成 prepared；跨域才执行必要输运。Hosted 不支持完整 checkpoint/hot resume 时明确 unsupported，应用 replay 不能填补该能力。ARC 子容器的关闭必须由实际 SDK 容器负责人确认，不能用外层 Local PID 替代。

完整 workspace 只做一次权威封口，named output 使用同一 artifact 或成员关系；应用继续按独立交付合同发布。校验归可变源码冻结、跨域接收、状态 capture/repair 和入口装配边界，一次解析窗口复用同引用读回，删除下游重复全扫；保留需求身份、Git/SQLite 语义、传输完整性和唯一 writer，不增加永久信任缓存。

上一轮保留 ARC 领域 compiler、角色区分、延迟生产、公开模型政策及实际传播核对、protocol2 只读检查；独立 child 服务代码由共同 bootstrap 替代。完成条件是生产、fresh、捕获和同域恢复的完整纵向闭环，并按打包/启动/热修复三条路径记录时间、哈希读取、复制/输运、峰值空间及人工接线。实施准备必须明确全部迁移和删除点，不以某一最新异常修复或编译成功结案。

最新来源报告 exp23 仍消费冻结 Lab runtime 内的旧 adapter，宿主源码修复未生效，随后下沉到包内 layout fallback 并重新上传 exp25。这也属于组合及变更传播责任：设施代码与 SDK、runtime 的真实源码闭包必须进入生产依赖，修改只重产变化资产，目标装配记录实际消费版本。跳过父路径后回退 package identity 不能被解释为取得可恢复的 retained artifact relation；缺失仍明确暴露，不能借入口越过替代恢复证据。
