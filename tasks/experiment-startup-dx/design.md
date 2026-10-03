# ARC 本地生成的启动边界

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
