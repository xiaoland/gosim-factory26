# I14 夜间实验：当前入口

更新于2026-10-03 21:24 CST。主线v7已由sfp7官方SDK接受，本次外层attempt为33f6eff9…；日志显示官方run_submission.py启动，内层恢复和新native活动仍待读回，不能据outer running宣告成功。用户最新将官网生成收敛为仅GitHub主任务的e2e，direct及其它候选在本地完成后冻结应用并官网重放；pi-minimal-vv的Sheet/stage1–3保底线由用户另管。两direct v7材料已齐，等待主线实际验证；9b未知snapshot仍不重复POST/create/start。WSL reviewer31约七小时停滞已保全并冻结停止，释放约993MiB；稳定owner继续核对legacy恢复来源。监控max(last_event_at)选择最新Issue、遮蔽PR停滞的明确错误已修，15分钟/仅异常报警不变。[资源恢复](../resource-recovery/packet.md)归实际修复，[场地决定](../../../runs/iteration14/overnight-20261003/venue-allocation-20261003.json)归当前派发范围；[今晚草案](design.md)的新迭代/启动采集策略尚未部署。

用户纠正“五次上限是本地，不适用于官网”，授权停止run5182并用新版接续旧进度。5182已独立确认16:54:38取消；稳定runtime owner现持公共legacy恢复接入、主线实际官方runner验证及后续同源官网接续，root持总体判断与结果采用。用户随后新增9b4 cleaner-stage2、8ca reviewer-sheet同样保全取消和各一次新版接续，direct_oom_continuations唯一负责两run。原Git/Braid/native保持为目标，由公共checkpoint/prepare核验，不默认fresh；不控制stage3 db6，不恢复已退役的自动评分queue。主线持有全局判断、授权、monitor绑定和结果采用。基础设施已合入main 5e96bdd6，恢复owner可继续必要机械修复。WSL reviewer/cleaner31保持原运行与只读采集，4GiB本地结果不补证官网2GiB结论。

## 当前授权与决定

用户最新决定：“可以上传一个运行到 github task，其余的本地运行，运行完成后上传官网重放”，原因是已安排pi-minimal-vv参加Sheet及GitHub stage1–3保底。当前唯一官网生成采用主线5182 e2e，在sfp7实际验证后同源转官网GitHub主任务；direct两项及旧reviewer恢复只在本地生成，完成即冻结应用再独立官网重放评分。此决定替代此前direct官网生成安排，不控制用户另行管理的pi-minimal-vv。场地、负责人及未知9b snapshot边界已[冻结](../../../runs/iteration14/overnight-20261003/venue-allocation-20261003.json)。

用户最新授权：“我要睡觉了，你整理好工作区，确保实验基础设施的改造已经完成，就可以自动开工，不需要我的审核。”并要求fallback按价格从低到高，明确智谱原厂无余额。此指示取代此前“暂不启动”，授权完成本夜必要源码、材料生产、真实接线及官网实验；不恢复已删历史运行、不做正式比赛提交。[设计](design.md)与[实施准备](preparation.md)按最新账户事实收口后直接实施，不再等待审核。

用户确认清理“按此范围清理，包括不完整 I14”：仅保留I13-2完整评分、应用及必要复现材料，删除更早和不完整运行。最新存储澄清原话：“是‘允许远端执行数据；Mac 侧产物全部放 WorkSSD’。继续。”WSL/sfp7执行数据可在远端盘，Mac产物、临时文件、专属cache及回收全部在WorkSSD；已更新[AGENTS.md](../../../AGENTS.md)，远端按实际容量与权威冻结，不从Mac余量推导。

用户具体要求Braid通知只列对象与变化，去掉正文读取指导。此窄改已单独获准并完成，编译及真实无模型CLI读回通过；示例为`Issue #1：评论 #2 created`，见[通知回执](cells/brief-notifications.md)。用户进一步限定独立审阅只修明确机械缺陷，语义或证据不完整项保留；明显上下文冗余、重复、频繁打断可以直接修正。

用户早晨指示：“现在已经是7:40了，既然如此，我们将e2e、cleaner、reviewer都启动起来。”授权新增cleaner与reviewer各一次从公开GitHub需求完整生成，历史台账limit=4，不自动新增audit或重跑。用户随后明确“是WSL/sfp7”，主线撤回macOS/Darwin方向；当前存储范围已获上述明确答复，无新增开工审核。旧seed串行程序及新Hosted等待程序均已精确退役，无新队列start-intent，A2未受控制。之前reviewer官网start返回409、started_at为空，不计模型生成或零分；拒绝及队列原件保留。

## 采用的事实与方案

唯一完整登记结果为I13 Flash/Sheet **74/100**，已做代码、Issue/PR和定向轨迹分析。[结果证据](cells/results-evidence.md)列出F1–F4机械应用缺陷、F5语义争议及已进入I14的通用修正；不能映射26项官方失败，也不能把Sheet答案注入GitHub。GitHub对Sheet迁移性是选题假设。

A2停止后，第5次主线官网run `5182d1d25e9d`曾确认原生活动与实际2GiB cgroup；其13:22启动回执归 `runs/.../stage-oom-release-narrow/first-runtime-acceptance.json`。后来停滞并按本次授权取消，尚无完整结果。reviewer、cleaner31继续在WSL生成；reviewer不含seed，独立审阅仅修闭合机械项。4GiB本地结果与官网2GiB生成OOM结论分开。

ARC与智谱原厂额度均不可用。候选先满足同模型版本、实际账户与启用能力，再按价格升序冻结；已购套餐及按量价格/抵扣分别记录，千帆GLM低价不改变e2e优先级。当前接续显式采用Rust模型代理，保留每个来源的冻结路由顺序；受控.private模型凭据只装配当前激活链。精确选择与实际验收归[供应商调查](cells/provider-fallback.md)。材料从保留Linux runtime派生，新Braid、e2e及代理生产当前身份，不先建设远端域。

## 负责人、依赖与下一步

2026-10-03 21:03 CST：既有WSL采集确认reviewer31的PR3原生会话自14:00后约七小时无新活动，最后turn为Pi subagent auto-drain失败；Issue重复状态检查不算有效推进。root将该旧运行的有界核对、必要机械修复和原进度热恢复正式交给wsl_reviewer_recovery，已无root在途控制；cleaner31不受控制，新增主线/两direct仍放sfp7。具体根因和child现状待读回，[证据入口](../../../runs/iteration14/overnight-20261003/parallel-reviewer/recovery31-20261003)由负责人持有，不先归因resource gate。

| 负责人 | 当前结果与入口 |
| --- | --- |
| recovery_boundary | 清理已完成；[清理回执](cells/storage-cleanup.md)。仅保留完整Sheet提交包、最终应用/评分与必要小回执，GLM/GitHub及重复展开副本、旧gateway、外置Factory专属数据与资源已删。WorkSSD约658 GiB可用。 |
| overnight_judgment | [独立判断](cells/advisor-decision.md)：采用Linux来源派生与Hosted seed audit，列出动态库、秘密装配及无应用报告回收边界。 |
| brief_notifications / provider_fallback | 通知与Router接线完成；真实host gateway的stream/tool/image均200，包内凭据只覆盖选定链。 |
| resource_gate_implementation / direct_oom_continuations | 稳定runtime owner负责主线v7实际官方runner操作及必要公共入口修复，direct owner负责9b4/8ca，root持总体和结果采用；[资源恢复](../resource-recovery/packet.md)。 |
| 主Agent / provider_fallback | 主线持有reviewer、cleaner两项WSL/sfp7本地生成的冻结、必要修复与实际启动，以及A2控制、机会台账和评分；provider_fallback持有只读连续采集，监控仅报告。 |

[开发-实验基建改进](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)已交付main的`302878bc`（有界监控证据）和`83e723d0`（四I14定义/state及checkpoint v3）。版本与20源码编译/真实材料离线回执已核对；本夜Linux runtime/material已生产，首轮已在官网生成；完整评分和OOM端到端仍待终态。当前依赖归[存储/布局任务](../../experiment-storage-lifecycle/packet.md)，不接管其源码或把局部离线计时当作完整启动/热恢复验收。消费交付时重新核对版本及本夜实际调用链。

原首轮`66e2c515dc3d`及A2 `8a282da5502e`均已保全并退役，不作为完整checkpoint或有效零分。旧Hosted队列及入口16–29的模型前失败保留原件，当前运行、预期退役与恢复准备以monitor-contract为准；历史控制、修复和授权归[执行](execution.md)。本次已授权三项Hosted保留进度接续，各owner保留其它任务修改。

监控采用独立5.6-Luna medium会话、15分钟heartbeat，主动比较连续活动/有界原生事件与阶段证据。用户最新明确“让监控仅在出现异常的时候汇报，监控只报警，不报告进度”：普通进展、正常完成、恢复正常及预期退役只保存记录，不发送消息。新疑似停滞、采集失联、具体故障及非预期失败才报警；修复、热恢复ROI、运行控制及最终实验结果交付均由主线负责。告警先持久保存再通知本主会话，并由root写处置回执；未处理告警不被去重删除。具体身份归execution及运行monitor-contract。

早晨复盘已落实控制纪律：沿冻结执行器，不绕过Hosted暂停/恢复限制；平台can_resume不证明保留进度，疑似停滞先只读核对并记录未知及处置损失。监控实际消费六条有界原生事件并保留真实通知回执；后续心跳反馈仍待观察。另修正无时区官网日期被按Mac本地时区解释的八小时偏差，当前A2不换冻结代码。持久约定归[恢复手册](../../../docs/deployment/recovery.md)。本地机会台账limit=5；Hosted按同task一个活动run门控，本次三个接续各仅一次，不自动增加其它模型轮次。
