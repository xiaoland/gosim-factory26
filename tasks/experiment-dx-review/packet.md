# 实验过程与基础设施 DX 复核

2026-10-02，用户要求继续分析 `codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2` 及实验相关子 Agent 会话，找出确定性设施应承接的操作及 DX 改进。最初授权为调查与方案；随后用户认可 hard-cutoff 完整基线并明确“开工；你可以自由提交”。当前源码实施和实际离线反馈见文末；历史阶段记录不作为当前待开工状态。

## 调查范围和证据

读取主会话从 2026-10-01 13:12 起至 2026-10-02 本轮读取快照的 26 个 turn，其中 18 个含有效用户/操作/答复记录，共有 551 条 commandExecution。还读取以下 8 个实验相关子 Agent/独立会话的相关 turn。数量只描述取样范围，其中包括必要调查、实现与验收，不能解释为浪费次数或节省空间；未读取整个项目所有历史会话，也未将推理记录用于归因。

| 证据会话 | 本次关注的操作事实 |
| --- | --- |
| [主会话](codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2) | turn `01a0f65a…` 反复组包、权限/路径、唯一 Console；`01a0f847…` 八项派发与模型/费用变化；`01a0fa2f…` ARC切换、两项热修；`01a0fa79…` 回传阻塞及重新画树；`01a0fa90…` 更换可用准备宿主、离线接续、通知及唯一采集器交接。 |
| [I13 本地启动/保全子 Agent](codex://threads/01a0f665-0b69-7fb3-8b0b-9531d87d4e97) | dangling symlink 导出失败、完整保全及来源身份、旧会话前缀、模型成功请求、终态重放与采集的手工接线。 |
| [I13 四项启动准备子 Agent](codex://threads/01a0f65c-297b-7301-8e73-c3a801a795c3) | 在 runs 下写 host-readiness、linux-prepare、prepare-final-matrix、collect-startup 等本次脚本；Flash/GitHub 四条 session unavailable 后保全266MB现场。 |
| [I14 派发复核子 Agent](codex://threads/01a0f886-5dd3-7a91-a7dd-be393d225026) | model.env冻结、accepted→admission、进程回执优先级及崩溃窗口；另查 Console 启动时manifest、登记/短重启及真实state出现条件。 |
| [I14 Console 登记子 Agent](codex://threads/01a0f89b-9607-7a92-a571-98a601ce85aa) | 两份私有register/readback脚本；保持原服务/旧条目，新增访问容器及binary，HTTP停机约53秒；完整inspect曾泄露Env。 |
| [ARC切换/共享恢复子 Agent](codex://threads/01a0fa45-c05d-76f1-bb68-bf4b682c69d9) | pause-old-adapters、select-snapshot、preserve-current、refine-manual-dependency-selection等临时脚本；压缩传输、离线reentry、I14刷新和一次材料换版通知的共享修复。 |
| [Flash/GitHub 恢复会话](codex://threads/01a0fa57-5cd1-7f20-9a18-5360ca8b21f4) | main与974份保留文件核对成功后全量回传超时；停止现场导出/核对，等待共享reentry后才冻结、唯一官网启动；新run原生历史继续及8份内存明细取得。 |
| [cleaner 热修复会话](codex://threads/01a0fa5d-2c5e-7963-b2a5-3a29bb5e74df) | 从I13导出脚本读文本替换为本次流程；完整工作区/Git/native保全；等待I14刷新/ARC、技能材料、Runner镜像、恢复通知接口，尚不把候选包当部署完成。 |
| [I13 实验监控](codex://threads/01a0f613-082a-7251-a25f-e99acbc37706) | heartbeat消费原脚本摘要，普通变化保持安静；新run身份/collector路径仍由主会话长消息交接。 |

核对了实际源码 `lab/arc_bench/{operations,recovery,model_facts,hosted_monitor}.py`、`lab/docker_endpoint.py`、`experiments/i14-0/launch.py`、`braid-console/service.py`，以及现有设施方案、实现说明和恢复文档。只读现场包括 cleaner `handoff.json`、ARC热恢复 `handoff-state.json`、Flash/GitHub operation-r2 的准备回执及 Console 登记回执。它们是对应读取时的事实，不构成持续健康判断。

## 核心判断

瓶颈是组件接缝仍需要 Agent 解释：源码已有冻结、门控、准备、启动、采集和恢复回执，但公开入口没有贯通失败阶段、可消费产物和剩余依赖。主会话必须读多份JSON、找源码函数、重算hash、重写私有脚本、发长handoff，再重新画状态树。增加Agent并发能分担劳动，不能使这些机械事实可靠。

设施应该承接身份核对、材料绑定、阶段接续、订阅接收和确定性状态投影；Agent保留实验策略、语义判断、缺损恢复取舍与有外部影响的决策。不能从“步骤能编程”推出它可自动获授权执行，也不能把所有子Agent操作归为浪费。

| 顺序 | 已观察的缺口与原因 | 应由设施承接的结果 | 已有能力及仍需做的部分 |
| --- | --- | --- | --- |
| P0 | prepare main/readback成功但导出失败，调用者仍另找回执、重新判断是否要跑main；正常prepare只将prepared视为完成，failed会新建attempt。 | 同一恢复入口清楚显示准备、导出、校验、来源停止、可接续阶段；消费原attempt的已验证产物，只继续获授权的缺失阶段，保留旧失败。输出main是否执行过及为什么无需再依赖WSL。 | 压缩流和 `complete_prepared_transport` 已实现，不重做；缺口是它们与正常prepare/public status的阶段消费接缝。不要在不确定错误后盲目重试。 |
| P0 | 用户多次要求重新画树，恢复会话有长依赖消息；prepare失败时operation/status首先读取尚未生成的inputs.json，不能由同一入口解释该失败。 | 状态入口在inputs未就绪时也读spec/prepare receipt，展示每个逻辑目标的当前attempt、来源/替代关系、真正阻塞的组件、已取得事实和下一合法动作；从同一active-matrix聚合，不再手写第二份运行事实树。 | operation/status、冻结作用域和accepted回执已存在；补准备失败和前置依赖的投影、简洁人类视图。packet继续拥有授权与决定，不做运行数据库。 |
| P1 | 多次重建root/private clone Git，保全WAL、native前缀、暂停/停止身份；合法悬空外链和约1GiB core造成输运/打包劳动，临时脚本跨任务复制并str.replace。 | 保全生产端提供完整可恢复的源材料和明确缺损清单，在同一时点绑定应用、Git、Braid及native；统一导出/冻结回执供恢复消费。历史缺损用已有显式重建依据，保留不可恢复项。 | output链接保全、Git reconstruction、prepare独立读回已存在；缺的是统一完整检查点生产/发现与导出反馈。尚未定位平台ZIP遗漏.git的全部生产路径，不能承诺修改平台；不从ignore、DB branch或文件hash推断材料可丢弃/历史完整。 |
| P1 | 生成已开始后另派Agent发现state、准备binary/访问容器、短停同一Console，另发长消息把新run交给唯一采集器。 | operation发布实际身份及接入请求；monitor/Console各自在自己的边界登记并确认接收。显示生成、监控、Console、评分跟随分别是否接通，某一接入失败只补接入。订阅消费稳定索引，减少每次通知会话新路径。 | monitor动态targets/accepted和逐题重放已实现；Console已有register/binary/access命令，却没有发现/接收请求的自动消费。要核对现有服务重启与权限契约再设计，不能让operation直接改registry或新建第二Console。旧冻结collector接线升级与新功能必须分开。 |
| P1 | 模型供应商曾需专门audit、完整Env误输出；材料刷新后旧native历史不会自然知道技能换版，主会话需要传多个hash及通知消费者。 | 常见查询默认白名单公开投影；材料生产端提供从声明、冻结、启动选定到已观察使用的能力证据，保留来源和缺口。明确材料变更时生成本次获授权的一次通知计划与接收回执，避免靠聊天重复粘贴版本。 | operation/models已完成且有实际读回，不再作为待建；后续是Console/monitor消费、官网及e2e证据覆盖。一次换版通知接口正由原共享owner实施，不能平行重写。通知送达不等于已阅读，更不等于方法发挥效果。 |
| P2 | WSL不可用后，主会话逐命令调查development-2的daemon、资源、镜像、架构及Runner来源，又在多目录寻找冻结Dockerfile。 | 单次宿主/运行环境事实入口，分别列连接、daemon、平台、容量、镜像/runtime身份和可承担的阶段，prepare直接消费明确冻结的输入，报告缺少哪项资产。 | Docker endpoint冻结/confirm、共享admission和host runtime asset已有；补readiness聚合及稳定资产发现。不能自动把旧宿主已冻结任务换到新host，也不能用只读snapshot代替预约槽。 |

P0排序依据是错误后果与反复出现的机械判断：先让失败操作可靠接续并能解释自己，再减少订阅/材料接线。完整检查点是长期优先项，但先查清生产边界；Console和宿主DX随后。没有据命令条数估算API/耗时节省。

## 不应转为通用确定性默认值的内容

GLM两题正式平均领先10个百分点的选择、缺分时先选Flash、是否改费用/供应商、哪些variant纳入下一轮属于实验配方。I14 dispatcher及共享五槽已实现，未来项按确定条件分批冻结已解决常规换根问题；只有确需撤下已进controller但尚未启动项时，才补controller/实际启动共同仲裁的条件取消，不能读waiting后TERM。

OOM或停滞的原因判断需要证据和工程决策。采集、活动阈值、具体错误、资源归属和受控限界属于设施；token增加不证明语义进度，缺victim不授权猜信号来源。自动恢复收费运行要消费本轮授权与明确的停止/接续依据，不能由异常类型自动授予。

选择缺损检查点及接受丢失进度、推断最后checkout、公开行为是否满足需求、技能是否真正改变协作都需要负责人判断。设施可列证据和限制，不能从hash一致、消息已送或局部操作成功宣布整体验收。主会话曾把官网SIGKILL与WSL问题混为一谈、误解个人key/比赛模式，这些概念误判也有文档消费问题；设施应投影显式venue/credential mode及原平台回执，不能仅靠多加自动化解决理解问题。

## 下一步与验收方向

建议先将两个P0合成一项有界方案：现有operation/recovery接缝，覆盖inputs尚未就绪、准备成功而导出失败、已有导出可离线完成、来源仍未确认停止四类真实过程状态。无需新runner、状态树或通用工作流平台。再按组件所属分别接Console订阅及完整检查点生产；禁止以新轮询覆盖已有采集。

后续实现须取得对应范围的新授权。真实反馈沿现有失败attempt/导出/校验原件取得：公开状态准确显示哪个阶段成功、哪个未确认、下一步需要何种证据；接续保持package/attempt绑定，不重执行已成功main、不新增付费请求；外部依赖不可用时不错误阻塞已经取得的本地产物。没有Factory/Braid测试、probe或smoke；代码阅读不能冒充真实接续/崩溃/并发验收。全部新付费实验、Console部署、宿主迁移和源停止各自按任务授权推进。

独立advisor复核支持按现有组件职责补交接，指出压缩输运、离线reentry、共享准入、动态观察及模型查询已存在，不能重复建设；Git遗漏生产路径和Console接入生命周期仍有专门调查缺口。本轮没有把原主线正在进行的热恢复或通知实现接管过来。

## 方案阶段

用户随后明确：“好的，基于这些调查，我们思考实验基础设施改进方案。”据此进入产品/技术设计，尚不进入源码实施。当前[方案](design.md)按组件原件拥有事实、operation只聚合交接收敛；第一批覆盖两个P0，并明确分开材料有效与来源停止门控。已完成独立advisor复核，修正complete_prepared_transport与verify_launch耦合、failed重入新attempt及main退出事实覆盖的设计边界。方案待用户复核；认可后进入接口/文件归属/验收的实施准备，再对具体范围开工复核。没有改源码、控制实验或提交本轮文档。

用户进一步提出exp controller(build/control/monitor/analyze)与exp runner(env-agnostic/control harness/telemetry-collect)。方案已纳入此控制面/执行面职责模型，经独立advisor复核：controller拥有实验意图与跨attempt编排，runner拥有单次执行效果；环境无关是契约而非运行事实，官网托管由平台适配器暴露实际能力；检查点取得与Harness语义完整性分工。此前“无需新runner”指当前P0不用新增执行器，不排斥目标职责划分。仍为设计待复核，无源码或运行授权扩展。

## 实施准备与待开工

用户“好，继续推进”认可继续架构方案，按前次呈现的阶段边界进入实施准备。已完成现有执行接口调查、独立恢复预演及新增派生接口的advisor复核，具体结果整合在[preparation](preparation.md)。第一批仍落recovery/operations与实际受影响文档，不拆分通用runner或增加总控服务。

实证修正：历史Flash/GitHub原attempt failed回执与main exit0原件均存在，但canonical已prepared并用于真实run，不能以复制目录或覆盖canonical重演。拟用一个材料派生核心向独立output发布同attempt结果，再以新operation引用prepared_receipt；旧现场只读。来源停止未知真实legacy包存在，但尚无同包完整prepared原件，完整判别场景保留未实测限制。通用collector失联独立性是目标而非已实现事实。

当前为待开工，源码/运行/提交均未发生。开工复核对象为preparation中列明的源码文件、接口和编译/真实离线验收；不含模型启动、平台写入、源停止、Console部署、迁移、清理或push。按仓库阶段约定，在用户对此具体范围明确同意开工后实施，不将本次实施准备自动视为源码授权。

## 用户修正：完整干净基线

用户明确：“我支持 hard-cutoff ，建立干净基线，而且可以一步到位，以长期正确为第一优先级。”据此撤回此前兼容P0实施准备与待开工说明，design/preparation正文已重写为完整controller/独立runner基线。此前阶段记录仅保留过程，不作为当前实施授权。

新方案包含真正独立runner与collector、统一新执行领域/CLI、local/Docker/ARC托管能力、制品/检查点/准备/评分、停止证据外置、portable引用、monitor/analyze/Console，以及新写入硬切和旧活动退役。独立advisor、执行面迁移调查和制品预演已完成并整合；新LLD/schema/传输及完整真实验收矩阵仍需收敛，不能把此前P0预演用于完整架构验收。

已确认风险包括：旧派发器可能依赖工作树而非冻结源码；当前通用receiver与controller共生命周期；远端collector缺持久绑定；OTLP导出缺session元数据；历史prepared绝对路径不能当portable合同。新方案不保留旧执行翻译层，也不自动停止、迁移、删除活动旧记录或扩充收费授权。当前是修订方案待复核，未修改源码/运行/提交。

随后形成technical.md并完成两个独立LLD预演，6项合同修正已进入正文：attempt受理唯一性/稳定查询与控制instance、准入物化窗口、先核对再发布、checkpoint/stop同instance、resolver链接/装配约束、telemetry冲突/封口。按主线交接只读核对其最新人类Qwen/ARC指示和GLM交接资料：四个I14 run.py与恢复入口确有ARC-only约束，新方案包含生产端修正；不切旧包/FlashGitHub、不改其它模型。主线HOLD、paused/stopped但alive reservation、stop格式不兼容、原通知owner及唯一WSL Console边界已加入preparation。未向其它会话发送新指令，也未改变现场。

## 开工授权与实施

用户明确授权：“开工；你可以自由提交。”授权对象为已呈现的完整 hard-cutoff 新基线及 technical/preparation 的实施范围，允许当前任务提交，不包含远端 push。源码、生产端、接入和文档按此范围实施；不启动新的模型或官网运行，不停止或迁移现有实验，不部署或重启 Console。基线工作区和已有修改保存在 `runs/experiment-dx-review/implementation-20261002/baseline.json` 与 `before/`，提交只纳入本任务增量。

独立 runner、平台和 Harness 材料按已划定文件边界实施。主 Agent 负责 controller、制品、公开入口、Console 接缝及集成。独立复核发现 prepared 文件名/观测字段不一致、未受理 attempt 重入缺失、冻结源码依赖遗漏及工作树控制路径，已纳入修复；静态复核不作为实际生命周期验收。


## 实施结果与反馈范围

新写入已切换到 `lab.exp`，旧 plan/run/operation/competition/recovery writer 从工作树退役。旧源码及本轮开始时的相关增量保全于 `runs/experiment-dx-review/implementation-20261002/retirement-source/`，身份清单为 `retirement-preservation.json`；既有冻结运行、暂停的旧派发者、平台记录和唯一 Console 未变更。新 Docker 域必须取得明确 authority-handoff，不能用 container stopped 跳过尚存活 owner 和启动窗口。

Controller 持有冻结实验、请求、预算及证据投影；每个 Local/Docker attempt 的 runner 独立持有入口、collector、限额、控制与归档。工作树控制调用委派给该实验冻结的 controller；制品传输保持 ID 和 manifest 摘要。托管 adapter 保存 pending/原始响应并按唯一远端身份接续，未知副作用不重发 POST。生成应用与评分分成独立 attempt，归档或输运失败不重跑 main。

Harness checkpoint/validate/prepare 是公开、离线、版本化 producer。Prepared 与停止证明分开，启动重新观察来源身份；当前只支持相同 OS、架构及 logical root，外部链接和缺少 Git/native 原件会成为 partial，不重建历史。Console 已接入冻结控制协议和实际 Docker 身份校验，但自动发现/登记尚未实现，且缺少公开静止协调能力时明确拒绝暂停。托管导出只保证平台可获得的部分证据，不宣称恢复检查点。

模型 endpoint、credential_env 与官网费用独立冻结在配方。同一 native provider 的不同模型可使用 `provider/model-id` 绑定，材料生产端分配确定性独立 provider 并改写 profile/角色选择；供应商 model_id 可显式映射。旧会话若需要改变 provider 身份，恢复入口明确拒绝。没有发出模型请求来验证这些供应商支持范围。I14 的 targets/job_id 和模型显式配置，不再固定八项或自动选择 GLM/供应商。

实际反馈原件均在 `runs/experiment-dx-review/implementation-20261002/`。读取真实 GLM 交接原件并发布、核验、导出、跨 store 传输，制品 ID 与 manifest 摘要保持一致。随后使用真实原件进行独立离线归档：早期失败原件保留，修复了 namespace 依赖冻结、zipapp 环境 PYTHONPATH 和 bytecode 源码漂移；最终 `offline-evidence-final2` 的 attempt `attempt-5516368153344987a5182438` 返回 exit 0、archive preserved、telemetry sealed、controller completed。`offline-final2-build-reentry.json` 证明执行后冻结源码仍可核验；`offline-final2-stop.json` 和 `offline-final2-analysis` 分别保存当前物理停止观察和分析范围。collector 为零批次，producer_flush 仍为 unknown，不能解释成实际模型遥测排空保证。

源码编译、daemon helper 字符串编译与差异空白检查通过。按仓库要求没有编写或运行 Factory/Braid 测试、fixture、probe 或 smoke。Docker 准入交接与中断/重连、完整 Harness 检查点恢复、官网写入/评分、非空遥测冲突/去重、供应商实际请求仍未取得现场验收。后续真实实验须冻结具体输入、预算、费用、停止/中断范围；本次设施开工不授予这些行为。当前没有 push、清理、在途迁移或 Console 部署。
