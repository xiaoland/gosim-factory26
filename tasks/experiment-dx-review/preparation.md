# 干净基线实施准备与切换范围

2026-10-02，完整新基线已获开工授权并实施。用户hard-cutoff取向取代此前P0兼容计划；原derive_prepared_transport/prepared_receipt补丁路线不再作为实施目标。完整职责、生命周期和验收合同见[design](design.md)。源码、文档和真实离线证据发布已完成；未变更已有模型、平台、旧派发者或 Console。

## 新合同与公开入口

新执行领域使用独立kind与schema_version，不能仅增加旧manifest的数字版本继续走normalize兼容分支。拟定experiment kind为factory26.exp.experiment、首版schema_version=1；记录分别标注request、execution、artifact、telemetry和analysis kind，旧lab v1/v2/v3及Competition journal不能进入新写入/控制。

| 合同 | 权威及输入输出 |
| --- | --- |
| Build/freeze | Controller组织producer，输入recipe、明确材料和目标能力；输出experiment、不可变artifact、controller/runner/runtime身份及失败原件。无隐式模型请求。 |
| Dispatch | Controller分配job/attempt及预算，runner或托管后端接收固定请求；返回受理身份，不提前声明物理启动。 |
| Runner lifecycle | 每attempt独立监督者持久保存request效果、真实进程/容器、限额、stdout/stderr、collector绑定和收尾；controller退出后继续，不以runner重启重发main。 |
| Control/reconcile | 动作绑定attempt/request_id/参数；效果明确区分受理、实际停止和unknown。平台POST先记pending，缺唯一身份时只观察。 |
| Artifact/checkpoint/prepare | Producer维护类型、组成、来源和语义覆盖；runner取得一致切点/材料，controller选择来源，消费者核验。引用artifact_id/member/digest，停止证明单独绑定来源执行。 |
| Telemetry/monitor | 执行侧持久接收及有身份的源批次传输，controller按游标摄取/监控。原始重传与分析语义分别处理。 |
| Evaluate/analyze | 冻结应用为独立评分输入，每个评分attempt有费用/平台身份；分析固定制品及遥测截止点，不能影响仍在生成的Agent。 |

拟保留`python -m lab`作为唯一开发侧执行CLI，命令按build/start/control/status/monitor/analyze/artifact/evidence/wait组织；runner另有冻结制品入口。history为旧事实显式只读入口。命令语法随具体LLD收敛，但不保留旧执行命令到新协议的别名或参数翻译。官方SDK agent runtime export不是exp runner，保留其独立角色。

新实现建议放在lab/exp，分离controller、runner、backend、artifact与telemetry责任；这是逻辑源码归属，不要求每项合同一个文件或新服务。Controller不再通过旧operation工作者启动旧lab controller再启动适配器；ARC官方Runner作为真实评测依赖仍由选定执行后端调用，并保留独立事实。

## 迁移与删除面

| 当前实现 | 完整基线中的处理 |
| --- | --- |
| lab/plan.py、assets.py、records.py | Build/freeze、资产及内容身份迁入新合同；删除新执行侧旧schema/default runtime兼容，复用成熟清单/原子发布。 |
| lab/run.py、control.py | 分开实验分配/派发与独立attempt supervision；复用出生身份基础能力，退出旧共享进程worker/receiver生命周期。 |
| lab/otlp.py | 原始receiver归执行侧，持久绑定stream/epoch；补完整批次元数据及游标封装，查询分析消费不可变范围。 |
| lab/arc_bench/operations.py、competition.py | operation多层编排归并为新controller；托管adapter保留平台协议、pending与身份核对，不再拥有第二实验控制器。 |
| arc_bench_adapter.py、docker_workspace.py、docker_endpoint.py、docker_admission.py | ARC本地执行和Docker实际资源归runner/backend；准入落实际daemon资源域，跨控制宿主有共同权威。 |
| recovery.py、workspace_archive.py、arc_artifacts.py | 通用制品完整性/安全输运与Harness恢复语义分离，新checkpoint/prepared/application合同；停止证明移出prepared包。 |
| local_monitor.py、hosted_monitor.py、model_facts.py | 本地原始进程/模型观察移执行侧；controller消费公开事实，托管专有轮询保留；重构成统一monitor视图。 |
| lab/status.py、wait.py、gc.py、analysis | 新身份、制品引用、来源时间、批次截止及保护关系；历史格式隔离只读，不把unknown解释成默认成功/费用。 |
| arc_matrix.py、official_matrix.py、evaluate.py；当前experiments配方与I14派发 | 新recipe与公开controller入口，同步移除对operations内部函数和lab.run的依赖；条件选择政策留配方，generic runner不理解模型比赛阈值。 |
| scripts/runtime.py、package_agent.py、package_completed_recovery.py、agent_support.py；submission/recover_completed.py | 分别发布controller/runner/Harness制品；更新复制OTLP源码和动态loader；Harness检查点/恢复合同留生产端，通用exp层不读Braid私有SQL。 |
| 四个variants/pi-braid-i14*/run.py与恢复生产端 | 移除通用入口的ARC-only限制/强制覆写，显式消费配方provider/credential绑定；不静默切换旧冻结或活动run。 |
| braid-console的登记、访问与物理控制接入 | 消费新执行身份，通过runner/backend控制；Console自有服务、binary和访问容器仍由自身管理。 |
| PRD/TDD、lab与当前实验README、deployment说明 | 整合已切换合同和唯一操作路径；历史报告保留原条件，不批量改历史示例冒充新结果。 |

当前活跃实现/配方消费者、原生材料复制、动态launcher和GC保护均须核对；仅rg imports不足以覆盖迁移。允许复用算法和协议实现，不允许留下双重生命周期owner。不会因长期正确而重写官方SDK或改变Harness内部成员调度。

完整交付可按依赖有界分工：领域合同/制品与构建、独立执行与Docker、平台/monitor/分析、消费者/切换整合。先收敛接口再委派独占代码面，主Agent持有集成责任；内部完成順序不构成旧新两套公开基线长期共存的发布计划。

## 切换过程

1. 建立完整新领域及其生产制品，当前维护的配方、runtime、Console和分析入口完成同一合同的接入。新记录根与旧记录区分，身份/控制端/monitor登记不能混用。
2. 对活动旧实验只读盘点实际派发器、已受理attempt、未派项、pending写入、collector、runtime与源码依赖、资源保护和Console引用。冻结代码与仍依赖工作树的组件分别列明。不能默认所有旧任务已隔离。
3. 确认哪些旧执行按原冻结范围自然完成，哪些未派项转新recipe，哪些需要明确退役动作。迁移有源停止、模型/费用或外部平台影响时单独记录授权与实际效果；不能通过删除源码替代物理交接。
4. 发布前核对新准入权威及相同资源域的旧reservation，明确每个旧dispatcher的停派/允许集合、pending保护和工作树依赖保全。无法共同安全计入时等待退役，或使用明确独立资源域。这些是切换门槛，不能新入口上线后才检查。
5. 门槛成立后新执行入口一次切换，只接受新kind/schema。工作树旧writer和执行兼容退出；旧在途如仍需控制，只使用其实际冻结程序及限定退役通道，不提供工作树旧writer供新实验使用。随后核对没有隐含旧调用、重复collector、被遗漏制品引用或未确认平台写入。
6. 既有历史保留只读、导入产物留来源/缺口；删除旧实现不删除运行证据、保护对象和仍在用的runtime。未授权GC或push。

这是一轮整体切换，不以“先上线P0、以后再独立runner”作为完成。存在活动旧执行时，其限定退役通道是责任保全，不是新基线兼容层。

## 验收与授权边界

现有真实Flash/GitHub原件可验收历史投影、main成功/输运失败区别、完整export/validation核验及显式制品导入。它们不能证明新runner独立、完整活源checkpoint、跨环境native恢复或平台写入恢复。

源码实施阶段包含编译、实际build/freeze、已有原件离线导入与分析、调用方核对。新基线实际验收须冻结真实Harness、题目、模型/费用、目标环境、完成条件和允许的控制动作，至少覆盖：

- 已受理执行期间controller断开、重连，runner继续采集并完成保全，同attempt不重复main。
- 实际停止/收尾的原件与受理回执分别核对；效果unknown阻止重启与回收。
- Local/Docker实际运行及完整制品回收；跨环境恢复核对native路径、历史及允许材料变更，不只比较文件SHA。
- 实际检查点取得/prepare/来源停止门控、应用冻结与独立评分的完整来源关系。
- 原始批次接续和重复传输，controller摄取及分析不重复统计；producer/collector/controller排空分别报告。
- ARC托管保留pending唯一身份及平台能力缺口，评分与生成费用/耗时分别记录。
- 新入口拒绝旧格式执行；旧材料可读但不被追认为新保证；新旧资源及Console保护没有遗漏。

不新增或运行Factory/Braid测试、fixture、probe或smoke，不以模拟元数据验收生命周期。不能为了取得异常样本盲目重发收费请求；不可安全取得的故障样本明确保留证据缺口。完整实际验收涉及模型、平台和在途控制，尚须具体实验范围授权，不能复用历史official_evaluation自动接续许可。

当前独立调查/预演已覆盖迁移消费者、目录广复制遗漏新模块、旧活动隔离、collector绑定与元数据、制品绝对路径和Harness一致性责任。已形成[technical](technical.md)，并完成有界独立LLD预演，修正已整合：attempt受理唯一性及稳定查询、控制预期incarnation、daemon准入资产/物化窗口、准入先于发布、checkpoint到stop的同instance链、resolver链接边界、telemetry冲突及封口回执。Advisor支持真独立runner与完整硬切。接口已实施，离线证据路径已取得实际反馈；切换现场与收费矩阵尚未授权，现场能力不宣称已验收。

## 最新主线边界与真实交接

已只读核对主会话最新人类指示：“强制ARC”过度处置、GLM-5.3用Qwen AI、先整理情况再重构。Provider/credential/官网费用分属配方，不将此前ARC许可升级为通用Harness限制；GLM-5.3新配方按Qwen修正，其它模型另行冻结。

主线交接记录本轮HOLD新freeze/prepare/launch/模型请求；Flash/GitHub 7e8ec62670df继续原唯一collector，不停/不迁移。两GLM源已有stopped及保全记录，旧adapter/dispatcher为SIGSTOP；五槽中有三个alive owner reservation，包含paused负载及已stopped但owner alive的cleaner，不能以容器stopped释放。状态依据`tasks/iteration13/i13-2/glm-final-recovery.md`与`runs/iteration13/i13-2-20261001/arc-hot-recovery-20261002/handoff-state.json`，这里不是新的实时Docker观测。

现有source-stop的container对象/readback.state与packager期待container_id/after不兼容，是原件契约的实际失败样本。历史import保留原件和生产者字段，只有足够身份证据时生成明确派生观察，不能手改原件或通过宽松字段别名伪造新保证。cleaner候选已组装但未prepare/launch/通知，接入口为`runs/iteration14/cleaner-hidden-context-20261002/stopped-handoff.json`；材料完成与部署/效果分别成立。

共享材料通知仍由原owner处理package_completed_recovery.py和recover_completed.py，源码稳定未提交不代表新基线采用；本会话不并行覆盖。WSL已恢复、development-2为备用、唯一Console在WSL/8765；当前Docker Console仅支持Unix endpoint，跨宿主接入尚未实现，不能为新架构另建第二Console。重构切换前重新核对现场，不把此交接快照当启动许可。

## 实施完成后的边界

源码实施与离线反馈见 packet。真实 Docker/Harness/官网实验仍需明确输入、预算、费用与中断范围；旧活动退役和 Console 部署独立授权。新域缺少 authority-handoff 时明确阻塞，不替已有 owner 作退役决定。材料通知的既有增量保留，当前任务提交仅纳入新合同接缝。本文前述主线现场是调查时的快照，下一次真实实验前重新核对。
