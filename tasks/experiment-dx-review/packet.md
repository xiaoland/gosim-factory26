# 实验过程与基础设施 DX 复核

2026-10-02，用户要求继续分析 `codex://threads/01a0f23c-a2bc-7800-a5b0-847d29845cd2` 及实验相关子 Agent 会话，找出确定性设施应承接的操作及 DX 改进。最初授权为调查与方案；随后用户认可 hard-cutoff 完整基线并明确“开工；你可以自由提交”。当前源码实施和实际离线反馈见文末；历史阶段记录不作为当前待开工状态。

当前工作区为独立 feat/infrastructure-dx；第一批去除语义链接遍历哈希与开发入口修正已提交。本轮用户“好的，推进改进”后继续制品复制边界、doctor 的当次核验复用、定义与运行数据分离和打包双读优化。主验收改为打包、启动、热恢复的端到端耗时；当前局部反馈不代表三条路径已完成验收，范围及证据归文末。原工作区其它 owner 的在途 producer/hosted 源码没有带入本分支，不在这里启动恢复生成或写官网。

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


## 真实接续中的两个接口补齐

主线委派本会话处理 development-2 首次域和旧官网来源停止导入，范围只到 lab.exp 共享接口，不运行模型、停止旧 owner、写平台或部署 Console。development-2 的真实 readback 指向 daemon `e316f857-fe3d-4e7b-8236-9376f063fedc`；列明的远端默认 registry 不存在，仅有用户 Redis，有限本地扫描的 prune/大小/路径范围明确保存于 `runs/iteration14/dx-resume-20261002/host/`。这些观察不单独证明不存在未知自定义域，因此 first-use 必须另消费获授权负责人的新域及 writer/registry 覆盖声明。旧 WSL 三个 alive owner 和暂停派发者不受此次修复影响。

新增 `authority-handoff --mode first-use --scope`，真实缺失原件与有限物理扫描和明确覆盖声明分别保留，输出 reservations=absent，不编造空旧 registry。旧 retirement 仍要求真实 registry 和物理退役。新增 `import-source-stop`，消费旧官网出生与独立终态 GET，来源为 legacy-source/source_id，绝不伪装 new attempt。Launch 对此来源重新 GET 核对相同出生与终态；原请求、原件身份和源码合同详见 lab/README.md。

当前只完成共享消费者与 CLI。Harness producer 对 source_id/attempt_id 联合类型的消费由主线独占 worker 处理，本会话不改 submission/exp_checkpoint.py、submission/recover_completed.py 或 scripts/agent_support.py。此前已冻结 controller 不自动获得新门控，消费者须在源码及 Harness 接口稳定后重新 build。首次域授权/覆盖输入和 Flash 原平台终态保全由实际 owner 提供；本会话没有伪造这些输入或重复执行取消。实际首用 handoff 与 legacy source launch 尚未运行，编译和 CLI 合同读取不作为效果验收。


用户追加的 DX 判断已纳入 design 的后续提案：保留底层身份和显式 relation，人的控制面以实验投影统一查询；承认 intent → compile → frozen recipe 两级，将 I14 的策略编译从逐实验 launch script 收敛为公共层。入口发现、runtime 复用和 Console 订阅是配套体验，不能靠增加 Makefile 别名或万能 trace ID 替代。此追加消息按方案讨论处理，没有直接实施新 compiler 或投影框架。


主线进一步确认原 hosted 最终 ZIP 缺各 clone 私有 .git，当前仍 partial；由原恢复 owner 从原 native 成功 Git 工具证据确认 commit/branch，再在独立离线 repair 中重建明确缺件。本合同不放宽 partial prepare：legacy-source 可作为 repair 的输入/停止来源关系；repair attempt 身份只描述派生动作，不能追认原 ZIP 完整或伪装原生成执行。修复输出的 lineage 应保留原 ZIP、legacy-source、逐 clone 重建依据及独立 repair attempt。原 source-stop 与新派生执行停止证明各自绑定自己的身份，不能互相替换；完整 prepared 的发布须由 Harness producer 对修复后实际状态独立读回并说明允许变更。主线独占 worker 负责此 producer 接缝及私有 model-environment 接线，本会话不改这几个文件。


实际交接已发布于 `runs/experiment-dx-review/real-handoff-20261002/consumer-handoff.json`：development2-endpoint.json、development2-first-use-scope.json 和 development2-authority-handoff.json 已经由真实 Docker 只读命令产出，reservations=absent，实时物理对象仅1个用户Redis及其卷；没有创建准入 helper/负载、释放或控制任何旧资源。来源声明与有限扫描覆盖分别保留，不追认未知自定义域为空。r4恢复owner已实际调用 import-source-stop 成功，source-identity.json/source-stop-evidence.json位于其r4根；本会话核对原件摘要和出生绑定，并独立GET保存legacy-source-current-observation.json（成功时有文件），launch仍需自身当前观察。

随后发现实际 Docker backend 未消费断网要求，已补齐显式 backend.network=none，冻结参数校验、create --network none、docker-create-intent.json 和物理 inspect 网络门控，未声明network的生成行为不变。编译及差异检查通过，实际离线job由原恢复owner独占派发并产生物理回执；本会话没有以编译冒充真实断网验收，没有改其producer/凭据/packager源码。DX方案扩展延后，优先接续官网任务。


托管监控最小交接（2026-10-02）：复用已有 lab monitor/status 只读接口，无须为即将启动的 hosted 再建采集器或状态数据库。controller 的 hosted adapter 是唯一新 run API采集与终态导出 owner，原PID77062保留旧 cancelled source 范围；不伪造journal，不迁移旧monitor目录。Luna每十分钟消费保存的身份/状态/原错/archive/终态，禁止live observe/Client/第二collector；绑定实际experiment→controller出生→attempt→submission/run后才声称订阅具体新run。未接收订阅不阻塞hosted启动。consumer合同与实际离线readback位于 real-handoff-20261002/monitor-consumer-contract.json 和 monitor-readback-offline-repair.json，真实repair-final已completed，读回没有平台请求、模型调用或collector创建。新hosted run尚未作为实际观察对象，接收身份和告警效果不能凭合同存在宣布验收。本会话未更改旧collector、Luna自动化或原恢复owner。


实际离线prepare监督故障修复：home-fix attempt-e2c989263d851bb93a0454dd报process group member birth identity unavailable，旧异常没有成员PID/原process_error，无法追认哪一子进程消失。独立exact-resource inspect确认原container5ac55bac…exited、Pid0、OOMKilled=false、networknone；监督器exit0不等于入口exit0。owner导出没有harness manifest/readback，不能提升为prepared，旧unknown与半成品保持。

runner定向修正ps快照到birth读取之间的竞态：仅在新ps查询无成员且出生观察process_state=lost，或明确已非同组/僵尸时跳过；仍活动且无法识别的成员保持Blocked并保存PID、身份缺项及当前ps原错。入口wait/poll实际退出码在组和外部资源收尾之前独立持久化，不因辅助监督失败丢失。Docker backend_identity的kind在resource原件展开之后显式赋docker，修复两个生产路径的metadata覆盖；旧冻结source不宽松别名或原件改写。源码编译与差异检查通过，可由原owner重新冻结修正runner执行一次明确获授权的纯断网prepare；本会话不自行重派发，下一实际结果用于效果反馈。实物及源码摘要位于real-handoff-20261002/runner-birth-failure/repair-readiness.json。


## 统一 experiment projection 开工（2026-10-02）

用户在审阅 projection → compiler → readiness 的建议及本会话判断后明确“你可以开工”。本轮实施统一公开读模型及 Lab status/monitor 的人类视图：显式目标/阶段、未派发依赖、当前 attempt 与历史关系、入口/执行/归档/输运/可消费产物、证据时点和缺口、controller 提供的下一操作及执行前重验条件。优先消费真实 r4 恢复原件，不通过合并 identity、推断命名或重写旧冻结记录制造完整状态。recipe 只增加必要的显式目标元数据，compiler/readiness/Console 自动登记仍留在后续。

实施由本会话负责 lab.exp 及相关文档，不接管原恢复 owner，不启动模型、写官网、控制旧来源、部署 Console 或新增采集器。沿用自主提交授权，只提交本轮增量。验证采用编译及对真实现存记录的只读操作，保存输出与事实差异；不编写或运行设施测试、自检、探针及 synthetic fixture。


本轮 projection 已实现，入口为当前工作树的 `python -m lab status EXPERIMENT [--json]` 与同义只读 monitor；它们可以消费已冻结的新协议目录，不修改目录内的旧程序。新 build 会冻结 projection 及显式 target；旧冻结程序自己的查询呈现不自动升级。Compiler/readiness/Console 自动接入尚未实施。跨目录读取复用显式 index，不推断跨实验语义关系。

真实只读反馈保存于 `runs/experiment-dx-review/projection-20261002/`：existing-experiments.json、status.txt/status.json、monitor.json 和 readback.json。六个实际目录包括 r4 offline-ready、r2、final、home-fix、hosted-own 及本任务 offline-evidence-final2。实际 offline-ready 的 entry exit 0 与 archive preserved 保持，同时 Docker cp 的 300 秒原超时和缺少本地输出导致阶段 blocked，下一操作是同 attempt export，附 incarnation/物理终态/输运条件重验要求；没有执行该命令。r2/final 的 entry exit 1 不被 controller completed 提升成功，home-fix 仍 unknown；实际成功归档则可读取发布产物。平台状态沿绑定 run 的成功 GET 原件呈现；没有新的平台采集。

所有 lab.exp 源码内存编译及差异检查通过；查询前后列明的冻结 experiment.json 摘要未变。真实现存配方没有 case/variant 元数据或 from_job 评价关系，这两条路径尚无真实运行反馈，不能宣称生命周期验收完成。状态解释覆盖与实际物理执行效果分开；本轮未启动模型、控制旧现场、改原件、运行设施测试/探针或部署 Console。原恢复 owner 的 hosted latest 修复与 requirements 迁移独立进行，本提交不包含其源码。


## Compiler 与 readiness 接续开工（2026-10-02）

用户在第一阶段提交后明确“继续推进，你可以自由提交”。本轮接续公共 intent compiler，随后实现只读 readiness：编译显式 targets/cases/variants/models、命名选择政策和逐应用评价政策到严格 recipe，保留不可变输入及决定来源；取消 I14 的策略 launcher。Readiness 聚合声明资产、runtime、Docker endpoint/image 与容量证据，不隐式安装/创建资源或取得派发许可。原恢复 owner 的 hosted adapter 与恢复生产者仍独占，本任务不改这些文件或运行模型/官网/Console。

已读取个人 delegation 指引并尝试独立 advisor，当前 agent thread limit reached，无可用 advisor；没有以另一执行 owner 代替独立判断。沿用前轮已审阅的两层设计，实施边界由本会话持有：不自动展开 targets，不做通用表达式/DAG，不猜模型或费用，缺失选择证据只有显式政策才可降为 baseline。反馈继续来自现有真实配方/材料/平台原件的离线编译和只读宿主观察，不建立设施测试或 synthetic fixture。


Compiler/readiness 已实施。公共 compile 输出 intent/recipe/compilation，模型选择支持显式配置与 final-score-margin，评价支持 none/per-application；目标不自动展开，费用和凭据变量独立声明。源字节身份、runtime/handoff 描述及评分原件快照冻结；build 核对后发布 compilation_evidence。I14 launch.py 已退役，原件保全。Doctor 读取原配方或已构建实验，报告 runtime、资产、保存的来源门控、私有变量覆盖及 Docker 白名单事实，不调用准入 helper、不安装、不查询官网。当前 slots、工具缓存及镜像内 interpreter 缺少独立证明时保持 unknown。

实际操作原件位于 `runs/experiment-dx-review/compiler-20261002/`。最终现存 r4 配方的离线重表达为 existing-r4-intent.json，compile-final3/build-final3 及各自 reentry 均成功且回执完全相同；existing-r4-experiment-final3 未创建 attempt。Doctor 在新实验上显示已发布输入/完整来源绑定与缺少明确私有 deployment 的阻塞，status 呈现显式 github/pi-braid-i13 目标和未派发 generate。原先拆分校验导致 budget 变量引用遗漏的真实 build 失败已保全并修复；早期 bundle 与半成品保留，不改原件。最终 readback.json 保存代码摘要、操作及回执一致性。

对实际 r4 offline-ready 的 doctor-docker.stdout 成功确认 development-2 daemon、不可变镜像、准入卷标签和声明五槽，保存容器原件；可用 slots 仍 unknown，没有创建 helper 或调和预约。读取真实 I14 config 的历史 I13 评分：Flash 两题缺少完整终态评分条件，GLM 两份 journal 路径不存在；具体错误及原件摘要保存于 i13-score-readback.json，不补造 run ID 或运行政策选择。条件选择的完整评分路径、逐应用评价尚无完整真实材料反馈，不能宣称效果验收。所有 lab.exp 源码编译与本任务差异检查通过，未运行设施测试/fixture/probe、模型、官网写入或 Console 部署。

## 流程成本与重复证明（用户追加，2026-10-02）

用户指出热恢复的主要 DX 摩擦是重复全量校验、完整复制和上传，要求保留来源停止、需求身份、进度保全与传输边界，复用未变化内容的证明并减少往返。该判断调整后续优先级：compiler/readiness 只能收敛意图与发现，不能宣称已解决执行路径成本。当前 compiler 的输入 pinning/build 发布验证也有额外全量读取，本轮没有将这些成本隐藏成免费的安全保证。

源码定向核对确认：exp_checkpoint.validate 对 content 做完整 inventory，semantic_readback 两次逐 mount 调用 inventory 主要用于链接判断，仍读取普通文件 SHA；同一次 semantic readback 还复制 SQLite/WAL 到临时位置后 integrity_check，并对各 Git 仓库 fsck --full。Checkpoint 先完整 copy、semantic readback、manifest inventory，再 validate；prepare 验源后 copy 全量内容再 validate。Controller.verify 对冻结制品全量核验，code 制品还重复 verify；分配时 materialize 再验证和复制，launch gate 经 artifact.resolve 再完整 validate；runner._assemble 再 validate，随后逐 mount inventory/source copy/inventory target。Artifact resolve 每次自身 verify，materialize 另 verify 源并核验复制目标，未复用上层刚取得的核验结果；transfer 在源与目标边界均核验。具体源码版本归本轮 readback.json，当前恢复 owner 仍独占 Harness/recovery producer 修改。

这些是静态确认的调用链，不是各项耗时或累计字节的实测。真实本轮输入 ZIP 为720307829字节，prepared manifest 有82086个目录/文件/链接条目；未为汇报重新遍历内容统计总字节。用户报告的769个文件逐字节比较和上传566MB进度尚未独立核对，不据此生成比例或性能结论。没有再次启动原恢复或访问官网来做计时。

后续改动应围绕“同一内容、同一 validator、同一 policy 的证明只生产一次，变化或跨真实传输边界才新增工作”。先移除同一操作内部的重复哈希：链接遍历不读取文件内容，semantic readback 可消费刚取得的 inventory；共享 artifact 操作复用本次已核验 manifest，避免 resolve/materialize/verify 层叠。跨阶段语义回执绑定完整内容摘要、validator 版本和所检政策，不把 mtime 当内容证明；在发布 store 尚无实际不可变保障时，不能凭历史 receipt 跳过目标字节核验。来源当前停止与需求授权仍每次 launch 重验，语义证明不能替代现场效果。

减少复制需先明确哪一副本是保存原件、哪一副本供运行写入：不对会写 Git/SQLite 的恢复 workspace 使用共享 hardlink。同宿主具备实际 reflink/COW 能力可用其保持独立写入，跨宿主继续校验接收字节；公开凭据边界不扩大。包的实际必需内容与平台增量上传能力先核实，不猜可跳过重传。下一真实恢复应由原 owner 在正常操作中记录阶段耗时、哈希读取与复制/发送字节，区分必要边界和重复证明；不建立 synthetic benchmark 或另一个 collector。本节为调查和拟议改动，尚未修改恢复 producer、运输或校验复用接口。


## 独立 DX 分支接续（2026-10-02）

用户明确“创建独立的分支和 worktree 去继续推进实验基础设施、开发基础设施的 DX 改进”。已从61e0f5f6建立 feat/infrastructure-dx，managed worktree 位于 `/Users/lanzhijiang/Development/.worktrees/infrastructure-dx/factory26`，后续源码与提交只在这里进行。原工作区其它 owner 的未提交修改没有复制或覆盖。沿用自由提交授权；创建独立 worktree 不改变模型/官网/旧来源/Console 的效果权限。

本轮先消除同一操作内有明确证据的浪费：Harness 语义链接检查只需目录/类型/链接信息，不应重算普通文件 SHA；Controller 对同一 code 制品的重复 verify 可以复用本次结果。完整内容、Git/SQLite 语义及传输目标验证暂时保留，不新增跨阶段缓存或凭 mtime 跳过校验。开发入口同时修正裸 make 默认触发 tools 安装的问题，默认帮助明确呈现已有工作流，并更新 CONTRIBUTING 中已退役源码导航。新分支的 Harness 基线不含原恢复 owner 的在途 legacy-source producer 增量；不自动吸收其未提交文件，验证限制必须明确保留。

反馈使用现存 r4 prepared 的真实离线 semantic_readback、冻结实验的只读校验及实际 make 帮助输出，不生成 synthetic fixture/设施测试。原件归新 worktree 的 runs/infrastructure-dx/first-cut；语义调用前后比较 producer 结果与原件摘要，耗时只解释同一宿主单次实际操作，不当作稳定 benchmark。


第一批改动已取得实际反馈：semantic_readback 的两次链接 inventory 采用 hash_files=false，仍检查类型/链接并拒绝不支持的对象；默认 inventory 保留全文件 SHA，完整 validate、Git fsck、SQLite/WAL 和外链门控未删除。Controller.verify 复用当次 code_manifest，安装目录仍独立核对。裸 make 实际只打印帮助，不进入 tools；CONTRIBUTING 的实验源码导航已更新。

真实 r4 prepared 的 semantic-before/after 原件完全匹配 producer，manifest 摘要未变；单次顺序调用约56.84秒→15.41秒，文件缓存未控制，不能解释成稳定性能倍率。当前分支对已有 final3 冻结实验实际 build reentry 返回成功，约31.27秒，experiment.json 前后摘要相同，没有新 artifact/attempt。证据归 runs/infrastructure-dx/first-cut/receipt.json、semantic-before.json、semantic-after.json、build-reentry.json 和 make-help.txt。修改模块编译及差异检查通过；未运行设施测试、合成材料或模型。由于该分支未带入其它 owner 在途的 legacy-source producer 变更，本轮反馈为真实内容的 semantic_readback，不宣称新分支完整 legacy 恢复启动已验收。

当前已完成这批局部优化；跨阶段语义回执复用、发布存储的真实不可变性、减少全量复制与包传输仍待实施。后续沿本分支/本 worktree 接续，先按实际边界定义证明失效条件与目标装配生命周期，不能增加更多层校验回执后反而扩大流程。


## 复制边界与当次证明复用（2026-10-02）

用户明确“好的，推进改进”，本轮沿 feat/infrastructure-dx 改进 artifacts 的 export/transfer 以及 readiness。独立 advisor 派发仍因 agent thread limit reached 未受理；改动保持已同意的传输目标完整性边界，不引入跨阶段长期缓存或新的产品权限。Manifest 认证与 payload 核验分开，前者不能声称后者成立。复制前认证 manifest/ID/根路径，复制后的 staging 完整核验，匹配才发布；独立 verify/resolve 保留全量检查。已有 transfer 目标重入先完整核验目的 store，取消对源仍存在的依赖。Doctor 同一次 asset 核验后的路径供 producer 元数据读取，避免 source gate 再哈希 prepared/stop；失败资产不进入该读取。

实际反馈采用原现存 final3 实验、720307829字节 agent ZIP 与真实 prepared，原件保存于本 worktree 的 runs/infrastructure-dx/transport。对源只读、对新证据目录导出/传输；没有触发 controller/runner main、源停止、模型、官网或 Console。验证仍不用设施测试、合成损坏 fixture 或 probe。实际物理复制和目标全量核验仍保留；没有把这批提交宣称为跨阶段语义回执、COW 装配或增量上传已经完成。


本轮已取得实际反馈：doctor 前后 jobs/runtimes/blockers 完全一致，仍明确缺少 deployment 的阻塞；单次顺序读取约52.30秒→38.70秒。720MB ZIP 两次新导出均通过目标内容核验，重入没有再次复制；本次原实现约1.25秒、新实现约2.55秒，未观察到新复制的墙钟提速，不能将减少一次源预读等同稳定性能收益。真实 prepared transfer 约103.45秒，目的 store 重入约27.03秒；artifact_id、返回引用和源/目标 manifest 摘要均一致，原 experiment.json 摘要未变。新独立 verify 与有界 evidence 读取成功，仍通过全量源/目标字节验证。具体操作、原错/输出及结论归 transport/receipt.json。

所有 lab.exp 模块编译及本轮差异检查通过；没有设施测试、合成损坏/缺源场景或 native runner 装配启动。因此缺源重入与目标损坏失败窗口的结论来自明确控制流及保留的校验，未取得这些错误场景的真实现场反馈。实际复制总字节没有重新遍历来计数，上传没有进入本轮。另收到原恢复 owner 的协调消息，声明其主工作区 worker 正持有 backends.py/__main__.py 的新官网停止来源接缝；本分支本轮只改 artifacts/readiness，不合入其未提交修改，主线效果以其原 packet 为准。

## 最新验收标准与定义边界（2026-10-02）

用户补充“提示：运行数据和运行定义分离”，随后明确“关键验收标准：缩小打包、启动运行、热修复恢复运行的耗时”。这取代以命令收敛或减少哈希次数作为主验收的口径；主指标是三条路径的端到端时间，阶段反馈用于定位瓶颈。目前 doctor 与 transfer 重入的实测不构成整体验收，首次 export 未观察到提速。

已落实定义消费关系与路径边界，文档明确 experiments 保存定义、runs 保存运行数据。真实旧离线交接 recipe 原字节另存独立定义位置，build 与重入成功，status 展示 source/SHA/artifact，原定义身份未改变；证据 `runs/infrastructure-dx/separation/receipt.json`。本次未启动该 job，离线小材料 build 不作为代表性启动耗时。

沿真实打包路径发现通用打包器双读文件且再次压缩内嵌 ZIP，改为边写边哈希，正在用现有真实恢复包重新打包取得反馈。曾比较内嵌 ZIP 直接存储：62.45s→49.22s，但包增大20.5MB；上传低于约1.55MB/s会抵消节省，已撤回该编码变化，保持原压缩策略。未新增校验缓存或另一套恢复编排，未启动模型、写平台、停止来源或覆盖其它会话的恢复改动。

真实恢复包已有 stage 的打包反馈已完成：保留原压缩策略的流式版本62.45s→57.49s，约减少7.9%；两版manifest、实际文件字节和权限完整读回一致。单次顺序操作、OS缓存未控制，不能当稳定基准或覆盖runtime/stage构建。直接存储ZIP候选已撤回，保留原件与取舍依据；最终证据 `runs/infrastructure-dx/packaging/receipt.json`。源码编译和diff检查通过，未添加或运行设施测试。

下一步主路径仍为runtime/stage装配、启动前重复材料扫描以及热修复的包重建/上传/prepare/入口确认。启动与完整热恢复尚未取得本分支的可比端到端反馈；原主线执行owner报告转为新的I14干净起点实验，该报告不授予本分支接管或恢复旧运行。这里只保留其文件归属和实际原件入口，不将旧热恢复当成本轮验收对象。
