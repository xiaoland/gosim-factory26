# 启动接缝调查

调查只读取主工作区已保存原件与当前源码，没有控制实验、Docker、模型或网络操作，没有读取凭据正文。以下原件均相对主工作区 `/Volumes/WorkSSD/Development/factory26`；它们保留原身份，不能把隔离分支的新实现回写进旧记录。

## 已观察错误与因果链

| 原件入口 | 观察与边界 |
| --- | --- |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/compiled8/recipe.json` | 首个 argv 和 `--runner` 同为 `{runner}`，inputs 却没有 runner。宿主 Python launcher 与宿主 SDK 源码目录被混成一个名称；后续分别绑定才向前推进。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment12/attempts/attempt-51910e364e939f22aa86208a/execution.json` | `NameError: platform is not defined`，真实 entry 尚未成立。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment13/attempts/attempt-4cf142f2b7e81def8076966e/stderr.log` | adapter 读取 job limits 的 `memory_bytes`，配方只声明存储/遥测/时间，触发 KeyError。raw command 的 `--memory` 不构成 runner 合同。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment14/attempts/attempt-c4c62005be47fec174f62518/stderr.log` | adapter 的 endpoint 缺 `remote`，触发 KeyError。完整 Docker endpoint 是设施选择，不能靠每次实验补字段。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment15/attempts/attempt-0eb11d50715a93e421ce27ec/stderr.log` | 实际 admission 拒绝旧卷：`domain volume identity differs; legacy authority is not silently upgraded`。拒绝正确；doctor 仍校验旧 helper/slots labels，与协议2 daemon/protocol/handoff 合同不一致。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment16/attempts/attempt-d2c874cad4a8cdd1cf315f81/stderr.log` | adapter 缺 `read_json` import，触发 NameError。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment17/attempts/attempt-42349a32cfab98022621438c/workspace/generation.stderr.log` | 实际 `AttributeError: module factory26_official_runner has no attribute run_container`。镜像内部 local_runner 被当成宿主 SDK。 |
| `runs/iteration14/overnight-20261003/local-generations/runner-compatibility-evidence.json` | 独立保存镜像内部入口与宿主 `local_submit.py` 的角色区别及实际源码身份；后续使用现存官方宿主 SDK，不伪造 run_container。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment18/attempts/attempt-89e552e8ded1dd28ae279ef3/workspace/experiment-result.json` | 生成 exit1、没有完整应用；execution.md 记录 binding/SDK 透传遗漏及当时修复。不能据父环境存在推断子容器已收到。 |
| `runs/iteration14/overnight-20261003/local-generations/reviewer/experiment19/attempts/attempt-aa5ff3d9cbb3afafcfd8eb71/workspace/experiment-result.json` | 本次截取时已 generation failed、exit1；不是仍传输，也不是有效模型实验结果。本调查没有接管其后续运行诊断。 |

cleaner 的平行原件保留同一生产链，主设计及机会台账仍归 overnight-plan。以上不复制 native rollout 或私有字段。

## 接口判断

启动选择也有认知卡点：会话先把 Hosted 同题并发的 HTTP 409 解释为需要串行等待，之后经用户提醒才采用既有 WSL/sfp7 本地生成设施；控制宿主的 Darwin 平台又一度被当作生成容器的平台。HTTP 409 本身是有效平台约束，应归对应托管 job，不能据此否定其它生成场所。设施需要在 experiment intent/profile 中明确场所和材料角色，而不是让接续 Agent 再从机器名、包名和历史长 handoff 推断。

会话早期的 stale 判断、暂停后 resume 404 和新 A2 启动，属于运行控制与恢复保证的另一个接缝。新启动不能被报告为保留进度的热恢复；本轮保留原始记录，没有为缩短启动而绕过停止或恢复门控，也没有扩大到重新设计控制协议。

当前 environment.python 是 controller/adapter 的宿主解释器；environment.harness.runtime 是参赛 Harness 的 Linux 定义材料。Darwin Python 驱动远端 Linux Docker 是合法接线，错误是混用角色或生产出不符合目标的 Harness 材料。调查时的 profile 尚不维护宿主 SDK 与 ARC 目标域，而通用 intent 允许作者手工填写 argv/backend/input，直到执行后才发现这些角色是否兼容。

现存 arc_matrix 已分别消费宿主 SDK、Python runtime、Runner image、endpoint、slots/admission/handoff 并生成 limits。改进复用该领域 job 构造；recipe 继续 local + external_docker，不另造执行引擎。新的 `arc-local-generate` intent operation 接收输入、limits、case/model 与环境物理选择，禁止 raw command/backend 双权威。`from_production` 在 compile 保持未生产引用；计划完整不等于材料已经装配或模型已启动。

SDK 的真实 local_submit.py/run_container/main 由公共 ARC 输入解释边界读回；环境透传在实际子容器创建边界核对，build 实际绑定后消费，doctor 区分等待生产、角色不符与静态可用。readiness 复用 admission 协议2规范，避免第二套 labels 校验。子容器模型环境和 ResourceEvidence 由 ARC 组合入口承接；父进程的 sample_path 不能冒充子容器 ready。

本轮在独立分支实现这些接缝；正在运行的实验修复仍由 provider_fallback 承担。验收只使用编译、真实已存材料的离线消费和可追溯原件，未授权新模型、Docker或网络动作。

Hosted409本身是正确的平台同题门控。把该限制推广为所有venue禁止并行、未先发现既有WSL/远端runner，是控制平面的发现缺口；不以删除平台约束修复。controller/helper存活、entry已创建、原生模型首次活动及应用完成分别记录，不能互换。
