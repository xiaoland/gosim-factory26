# 实验启动、恢复与持续执行

2026-10-02，方案已批准并获准开工，设施实现与本轮无模型验收已完成，结果待用户复核。目标是让已授权实验从冻结输入、恢复准备、本地或官网启动一直进入脚本持续执行，操作被中断后能从原记录接续，并明确返回失败发生在哪一步、已产生哪些外部效果及下一步需要什么。用户于本轮明确授权：“同意，开工，可以自有提交”。范围对应 design.md 的五项设施改动、共享操作入口及实际无模型验收；本次指示同时满足方案认可和该范围开工依据，不再重复征求开工许可。新增收费实验和远端 push 不在此授权中。

## 授权与边界

独立会话的任务是改进热恢复、本地启动、官网启动与监控；按本仓阶段复核，先提供调查结果、产品/技术与验收方案，用户认可后进入实施准备，再对具体范围复核开工。调查、隔离实验和本 packet 可直接推进。已授权且根因、范围清楚的设施故障可在原实验范围内必要修复，不能据此批准新矩阵或新的收费尝试。

本轮不启动、取消、恢复或更换现有四项执行，不替换现行采集脚本。I13-2 本地两项为 `glm-root--hackathon--github-a94a67b4b3d85b` 和 `glm-root--hackathon--sheet-8046cfb0695023`；官网 Sheet 为 `f16834f58674`，GitHub 为 `e1aa595f6995`。这些是交接身份，不是当前健康结论。官网均为 self_funded、自有 ARC key、比赛额度关闭。费用 key 仅从私有文件注入，pending 写请求不自动重发。Console 继续使用唯一的 `http://127.0.0.1:8765/`；远端默认为 Debian-Rebuild，旧环境不自动成为恢复目标。

恢复保留来源 Git、未提交文件、Braid DB/WAL、原生历史和版本身份；检查点不全必须说明限制，不用重新生成替代热恢复。监控完全由脚本执行，不调用模型或 heartbeat。不编写或运行 Factory/Braid/SVC 测试、smoke 或改名探针。设施改动与费用实验各自授权。

工作区由多任务共享。现有 `lab/arc_bench/competition.py`、`package_arc_replay.py` 等已有未提交修改，集成前必须核对归属。另一任务持有 I14 机制、variants、`sources/braid/src/cli/mod.rs`、objects 默认 draft 边界和相关 Braid 文档；当前仅列接口交接点。提交只纳入本任务获授权改动，远端 push 不在范围。

## 当前事实与调查分工

已有 `competition.Controller` 的持久 journal/锁/pending 核对、恢复包和 prepare-only、纯脚本 provider 监控及 Docker workspace 传输。三条调查确认，I13-2 仍靠每轮脚本完成组件交接，并且存在不能靠包装消除的接口缺陷：

- 恢复打包将来源 journal/旧包与目标 base 绑定，更新材料只能退回 caller-confirmed；Linux 准备、独立保留性读回和逐 clone Git 重建又由临时脚本承担。
- 官网没有释放比赛锁后交接监控的有限启动接口。collector 的 journal 集合在启动时固定，增加一条 run 就需要人工停启，并核对 scheduler 连续性。
- 本地终态跟随用内存去重、遇已有目录即失败，无法从同一目录接续；没有证据表明它已重复收费，风险在人工绕开原 journal。
- Mac 的进程出生依据为空，`owner_state` 将空值相等判为 alive。真实旧 PID 98966/15711 已不存在仍返回 alive；同根因还影响 retry/reconcile/cleanup 的直接比较。
- 输出回收复用严格输入快照规则，被合法容器绝对链接和原本悬空的外链阻断；三个退出路径可重复回收，生成失败与归档失败需要跨文件拼接。

建议在 `lab.arc_bench` 增加薄的操作入口，提供 prepare、run（再次调用接续同一操作）和 status，修正上述真实接口；原 lab run、官网 journal 和 scheduler 继续各自拥有事实，不引入通用工作流平台。独立 advisor 支持这个边界，并要求进程未知身份不得放行清理/重试、部分启动成功不得转换为新执行、检查点缺失不被校验和掩盖。详情见[方案](design.md)。

| 调查责任 | 返回与当前边界 |
| --- | --- |
| 主线：本地启动、终态跟随、Docker 回收及整合设计 | 已完成[本地调查](local-findings.md)及[方案](design.md)，原始系统读回在 `runs/experiment-operations/20261002/investigation.json`。 |
| `recovery_flow`：热恢复链路 | 已完成[恢复调查](recovery-findings.md)，无源码或运行变更。 |
| `hosted_lifecycle`：官网启动与监控交接 | 已完成[官网调查](hosted-findings.md)，区分已发生故障与未验证源码候选。 |
| `operations_advisor`：组件边界及失败语义 | 已完成独立判断、身份缺陷与整合方案复核；方案已补齐 prepare 冻结实际内容、收费重放跟随者独立接收两项约束，不套用紧急修复例外。 |

以上是一次调查中的有界返回，不建立新的通用编排框架。权威入口是 [I13-2 packet](../iteration13/i13-2/packet.md)、[纯脚本监控](../iteration13/i13-2/script-monitor.md)、[已有设施任务](../experiment-infrastructure/packet.md) 和 [运行说明](../../docs/deployment/index.md)。真实原件位于 `runs/iteration13/i13-2-20261001/`。

## 完成证据与下一步

用户在实施中补充：“我有注意到你发现了很多问题，注意避免打补丁，而是选择长期正确的架构、治理来解决问题；不要盲目遵循 ponytail”。当前收敛重点改为统一授权运行集合、明确 preparation 消费绑定、分开准备/停止/启动/观察事实，以及由组件所有者记录失败与接续。独立预演指出共享 runs_root 越界重放、恢复执行缺停止门控和 collector 故障重启循环，正在按这些边界整合，不能在验收前称已解决。

I14 主任务提出设施消费需求：同一 WSL daemon 共享五个执行槽，新配方每项 2GiB/2CPU，已有两个 I13 的 4GiB 配置保留并计入容量。此任务提供冻结矩阵参数和同宿主共享准入接口，不启动 I14、不改 I14 variant 或 Braid，也不替主任务决定模型、费用或自动化。真实容量和消费方法归 shared-admission.md；多 controller 的准入责任不再依赖单一矩阵 workers 值。

本阶段已形成由真实操作支持的重复劳动/根因表、现有能力与缺口、产品/技术方案和验收边界。后续实现的完成标准是明确哪些原手工步骤由稳定入口持续完成；同一操作重入不重发未确认收费写入、覆盖源现场或丢失监控历史；准确保留原始错误和外部执行身份。具体真实操作验收与尚未覆盖的收费/长期情形必须分开陈述。现有原件足以证明缺口，尚未实现的新入口不能据此宣称验收通过，也没有可报告的实际节省比例。

已按用户“同意，开工，可以自有提交”进入实施。实施准备与预演在获批范围内收敛接口，随后持续实现和验收。进程身份、监控/Controller、恢复准备分别由有界 worker 持有，主线负责 operation、终态重放、输出回收及集成；具体接口与顺序见 plan.md。当前四项执行的任何监控应用须先给出具体影响；设施授权不创建 I14 或新增收费矩阵。

## 本轮实现与验收结果

已实现 operation prepare/run/status、恢复准备及来源执行门控、有限官网启动、动态观察接收、统一进程身份、输出保全和同宿主共享Docker准入。架构收敛为冻结experiment/job/run或首次attempt范围共同约束启动、重放、观察和完成；组件原记录仍拥有事实，公开accepted观察回执避免操作猜内部scheduler或等待无关任务。来源journal的完整观察冻结进恢复包，原活动路径只追溯；来源停止证明可用精确source/stop identity链，不能由caller-confirmed提升。

实际证据分开报告：恢复Linuxprepare成功且独立比对21764文件和SQLite七表一致；两份原始tar的68057/77898项与冻结远端entries完全一致；真实终态operation按本scope完成，重入仍completed；旧失联PID判lost、缺出生依据判unknown；真实WSL容量占二余三。主要原件分别在20261002/recovery-prepare、output-recovery、process-identity、shared-admission及terminal-scope-operation-20261002。恢复旧成功包仍缺启动证明链而明确Blocked；新证明链/冻结journal接口以真实原件关联和编译覆盖，未再次创建收费执行。各项精确事实及限制见对应implementation说明。

所有受影响Python模块编译及diff检查通过，没有运行Factory/Braid/SVC测试或构造自检。没有启动模型、官网写入、迁移活跃I13采集或改Console。新的provider恢复、实际收费重放、满格并发和崩溃接续仍需在后续获授权真实实验取得反馈；本次不以静态路径复核冒充这些验收。I14消费说明已写i14-interface.md，主任务可分批独立冻结；逐pending项条件撤销尚不存在，不通过改manifest或手工TERM绕过。

提交边界已逐项核对：competition原有锁范围差异是有限launch必须依赖且与本次批准职责一致的前提，连同launch/原始写入回执纳入当前任务。package_arc_replay、package_agent和TDD的既有assignee改动不属于本任务，保留在工作区；TDD只提交本次组件责任增量。无远端push。
