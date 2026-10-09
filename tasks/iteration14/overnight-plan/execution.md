# I14 夜间执行与接续

当前决定（2026-10-03 17:17 CST）：官网2GiB OOM资源释放是最高优先级。typed idle卸载及新共享gate已完成源码/编译/完整runtime，先主动释放，最多三轮/30秒恢复及重复压力预算耗尽后明确失败；源码完成不代表实际资源问题解决。原始诊断、材料、授权与真实验收入口归[资源恢复packet](../resource-recovery/packet.md)。

用户纠正“五次上限是本地，不适用于官网”，批准停止旧5182并用新版本保留进度接续。5182已16:54:38独立GET确认CANCELLED，未评分；新版尚未启动。experiment_evidence唯一负责公共legacy manifest/runtime兼容、prepared入口短TMPDIR及该run的保全、prepare、启动和实际验收。当前新producer对旧schema的拒绝由该owner修复，不能据此认定源进度不可恢复。Hosted缺少原位resume不妨碍导出→公共checkpoint→prepare→新实例接续，完整性由实际来源读回证明，不将普通ZIP补成完整checkpoint。

用户另授权9b4cc578b462 cleaner-stage2与8ca071551fd4 reviewer-sheet保全取消并各一次新版接续，唯一执行owner为direct_oom_continuations。原同题、角色、模型、无gateway及self_funded配方保持；db6 stage3不受控制。相关源观察、授权及处置归runs/iteration14/resource-recovery-20261003/direct-continuations。resource_gate_implementation已交付合并后public support依赖闭包，恢复producer采用实际support/helper路径，不盲拷缺state_writer依赖的根runtime文件。main合并5e96bdd6已完成，原工作区修改保留。

reviewer/cleaner31继续WSL development-1，只读采集按实际出生身份保持。官网应用评分有限queue已精确退役，不自动恢复，不用4GiB本地结果补证官网2GiB。monitor-contract登记当前run、owner、预期退役及collector；15分钟5.6-Luna medium监控只报警，普通进展/正常完成/恢复/预期取消仅保存。实际修复及控制由执行owner完成，root持有判断和结果采用。本地limit=5；Hosted各task至多一个活动run，新增接续只在当前明确授权内。

## 执行历史

以下保留历史原件和决定，当前状态以本页开头、monitor-contract最新身份及相应处置回执为准。旧“保持原run等待”“评分queue已绑定”等表述已由上面的OOM优先级决定取代。

2026-10-03。用户授权原话：“我要睡觉了，你整理好工作区，确保实验基础设施的改造已经完成，就可以自动开工，不需要我的审核。”并明确“千帆coding plan就支持glm-5.3-flash，而且应当优先使用coding plan”。智谱原厂无余额。此指示授权本夜必要源码、材料及串行官网实验，取代暂不启动；不做正式比赛提交。

早晨新指示要求e2e、cleaner、reviewer全部启动。原serial PID80659已按出生身份退役。reviewer独立派发run `df82f1a527f6`（submission `09f4303786d8`），start实际HTTP409要求先停止同题前一run；独立GET为FAILED、started_at为空，A2仍RUNNING。该次不是模型验证或应用零分。cleaner未重复此失败请求。

两条新包已就绪，`runs/iteration14/overnight-20261003/queued-generations/experiment`已compile/build，冻结reviewer→cleaner两job、max_parallel=1/max_attempts=2。有限等待程序PID24202消费A2保存状态，终态独立GET后仅启动一次该实验；按平台限制串行执行，无seed-B、自动重试或额外模型轮次。来源/拒绝/队列原件均归上述run根。

主Agent是唯一模型阶段派发、机会余额及终态消费负责人，采用83e723d0基建交付，保留其它任务改动。provider_fallback拥有供应商后台、集中路由及包内gateway/support；linux_materials拥有Linux资产及package producer；experiment_evidence拥有独立seed审阅入口与报告门控。旧串行seed树已撤销；当前历史模型机会limit=4（原A/A2/新reviewer/cleaner），平台活动limit=1。

当前Linux runtime/e2e/Braid与LiteLLM材料已生产；Host gateway真实stream/tool/image均200。冻结包已排除旧模型Scope拒绝DS重命名的机械缺陷。只做完整GitHub，Hosted self_funded单次运行生成和评分，max_parallel=1；下一轮仅消费v2 published A及允许需求。首轮已中断退役，当前执行以文末A2为准。

监控会话[ I14 夜间监控](codex://threads/01a0fdaf-9994-74e1-9a46-d2520f093e6d)使用gpt-5.6-luna medium、15分钟heartbeat；只读采集消费与报告，禁止修复和运行控制。root负责停滞诊断、热修复ROI、控制及唯一模型阶段派发。运行契约、机会台账、告警及处置回执均在runs/iteration14/overnight-20261003。

首轮实际冻结：agent.zip SHA256 `c54822b3821e661d8712e10e5978f117399e80689cd92e02e34f72e809fcfa1b`，883,254,528 bytes，material-591f24ea；全条目/权限/路由/ELF/预算及modelScope读回已通过。Lab intent→compiled/recipe→experiment已冻结。2026-10-03 02:04 CST控制器启动（controller-ab7b7412086e66396ec9aff2，pid51809），attempt-74c8f17f9e412c026a88c1d6，submission `4d03459b0c7b`，官网run `66e2c515dc3d`，启动时active、现已退役。物理进展与完整评分以保存的execution/monitor原件为准，active不等于已取得生成结果。

首个真实Linux反馈：gateway pid90；Harness run `20261002-180804-e6adda75` 处于braid/generating；当前原生主会话available，连续assistant toolUse与成功toolResult，原生子Agent已启动。复用现有collect_workspace/assess消费一次实际10.3MB workspace反馈，classification active、errors为空。原件归runs/.../first-runtime-feedback；没有把它当最终e2e或OOM验收。

串行程序只消费保存状态：完整评分及published final A→冻结同需求的独立reviewer包→单次Hosted审阅/合格B评分；report-only no-change合法；缺证据或源码基线变化则保留blocked交root。controller/runtime/source、serial program birth、监控线程及处置回执归monitor-contract。

2026-10-03 05:05 CST接续：监控报告PR会话疑似停滞，root暂停后官方Resume返回HTTP404 `Submission workspace is not available`，独立GET确认仍PAUSED。旧ZIP保全；重复导出不能独自证明缓存或真实进程停滞，不以旧资源样本断言OOM或curl根因。现有恢复包缺本轮gateway/E2E接线及完整Git/停止合同，不能冒充完整checkpoint。旧run已由真实Lab stop退役，独立GET确认CANCELLED、finished_at为21:05:01Z；停止入口的冻结source链接校验缺陷已修复并由此次操作验证。定向原件与限制归[停滞记录](cells/run-stall-20261003.md)。

第二次机会A2沿用原ZIP、Flash/GitHub和self_funded，新experiment为runs/iteration14/overnight-20261003/stage-a2/experiment，controller `80211`、attempt `attempt-07031e32569a13d9886ca629`，实际官网run `8a282da5502e`、submission `3c086cc0c8f1`，平台RUNNING。新Harness为`20261002-210813-f7ceb8fe`；定向/source读回39条原生assistant/toolResult事件，最后工具结果21:12:58Z成功，无provider error或资源等待。证据归runs/.../stage-a2/first-start/first-start-verification.json；这仅证明真实启动与原生活动，不是完整e2e/OOM结果。它是新生成，非保留进度热恢复。串行程序已改为等待A2，pid80659、SHA `a665a2d38ec70c04e5f7779fbb6c0163c28a19dce78adc319a43b6ba561c4cc5`；保留原B材料基线，完整A2成立后audit-B按台账计第三次机会，不再新增第四次。
