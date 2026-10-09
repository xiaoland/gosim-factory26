# I15 单一当前 Reviewer、Cleaner、E2E 组合

本variant从当前I14组合派生，保留其角色、模型、cleaner、e2e和接续能力，并以reviewer profile的`single-reviewer-per-pr` tag禁止同PR两个reviewer Session同时验收。每次候选的request、checkout和reviewer Session独立；conclude/cancel终止本次责任，后续请求重新选择具体assignee，不继承旧Session。改派同样停止旧执行后为新assignee创建新Session，同profile不代表同reviewer。不同PR可并行；原生验收子角色数量不受此策略限制。独立 reviewer 只接固定候选的验收请求；普通成员通过 `braid assignee list --reviewer` 与 `braid pr review assign` 指派它。每个 Braid 成员的 Pi launcher 均加载 `braid_cleaner`，完整正常响应经 Braid 来源校验后原子维护当前工作项。成员与原生浏览器角色读取独立 e2e 技能，通过 e2e MCP 操作真实浏览器，并保留 agent-browser 的诊断能力。

默认根成员与 reviewer 使用 GLM-5.3-Flash / high；cleaner 与 e2e 使用相同模型。原生 advisor 使用 Kimi-K3 / high，executor、explorer 使用 DeepSeek-V4-Flash-0731 / high，vision、browser-operator 使用 GLM-5.3-Flash / high。私有多供应商 failover、Rust proxy、Braid session 预算保护、模型预算配方继承底包；Pi与pi-subagents修复由当前protocol输入叠加。

新 Lab 使用 `build.py --runtime <当前公共完整runtime> --skills <共享技能库> --variant-only --directory <独立目录>`，沿公共 `package_agent.produce` 的 agent/support 组件装配，并叠加当前完整共享技能发布资源和显式variant覆盖。公共 `public_package` 负责网关、模型代理与Lab运行合同；本地完整runtime通过target的`prebuilt_runtime`和`remote_runtime`只读挂载，包含已冻结e2e addon。角色启用清单不随库目录扩展。模型路由由本variant的`model-recipe.json`引用公共自费链，运行保存实际选择，不从catalog默认挑选。

Lab 通过 `observe.py` 读取共享 Pi/Braid 状态与当前执行的原生 token 记录。宿主遇到 SDK 创建的私有原生目录时，由既有宿主 sudo 权限只读运行同一 reader，保留原 PermissionError 和恢复身份，不修改在途会话权限。此记录包含缓存 token，不能当作供应商账单；未保存或在途用量仍未知。

Evolution 种子复制排除 SDK 的根级 `requirements/` 输入。恢复旧现场时，只有能确认该平台输入从原 seed 到交付 commit 未变，才对两份派生应用采用同一显式平台路径投影；manifest 保留完整 commit 与 `excluded_platform_paths`。原 Git、需求输入与业务内容保留，应用路径校验仍严格执行。包内公共发布 helper 从同目录加载 `exp_checkpoint.py`。

旧底包overlay入口仅保留历史复现用途：`build.py --base-zip <完整自费baseline.zip> --braid-binary <Linux Braid> --braid-build-receipt <JSON> --protocol-runtime <Pi runtime目录> --output <目录>`。新Lab不消费该底包或overlay。

执行负责人先将完整底包解压到本次独立的 Linux x86_64、CPython 3.12 包目录，再将 `overlay.tar` 解压到相同目录，保留全部继承成员与私有凭据。入口为 `python3 <包目录>/main.py <允许需求目录> --output-dir <本次输出目录> --type web`。如需只准备真实原生材料，在同一命令末尾加入 `--prepare-only`。本 variant 不预置应用，不自行提交官网；4 GiB 容器及运行启动由本轮执行负责人设置。

本地阶段接续通过 `--initial-application <上一阶段冻结应用目录>` 传入只读应用，`--output-dir` 使用本阶段独立空输出目录。入口将输入复制到隔离仓库，并在 Braid 启动前将完整业务输入强制加入初始 Git 快照，包括应用自身 ignore 规则忽略的数据库、上传文件等业务资源。Braid 各成员从该快照创建独立 clone，验收也取得同一业务状态；工作文件不共享可变原件。原 ignore 规则保留，后续新增临时文件仍按它处理。源应用保留，最终交付只发布到本阶段输出。Stage 1 不传初始应用。每阶段绑定确切上阶段产物，不能用独立生成的同名阶段应用代替。

Evolution 运行添加 `--evolution`。平台已经向 output 注入基线时，入口默认从该目录复制业务应用到本次独立工作仓库；本地也可通过 `--initial-application` 指定同源完整官方基线。旧 `.factory26`、`process-evidence`、`.factory-e2e`、`.e2e-evidence` 和 `.arc` 留在基线，不进入新成员工作树，原生会话、浏览器与工具状态重新建立。最终导出逐项更新应用成员，保留 output 中的历史证据及已有业务文件，不清空输出目录。初始文件哈希、初始 Git commit 和最终交付 commit 分别记录；增量任务要求保留既有功能、技术栈、业务数据和未知字段。

运行设施可通过 `TASK_CONTEXT_FILE` 传入独立补充任务文件。入口在模型调用前核对可读性，复制到本次 run，记录来源和 SHA256，并在任务提示中引用该文件；未配置时保持原任务入口。赛事特定的数据准备与增量约定归任务设施，该 variant 不维护 EVO 数据或赛事提示正文。

reviewer默认技能发现只列7项：braid-collaboration、arc-bench、svc-verification、e2e、agent-browser、svc-sub-agents、context7-docs。原领域技能仍保留包内文件，必要时按独立路径读取；root和实施成员保持原16项目录及指令。reviewer只收到验收环境约束，不收到框架、组件库、数据库或样式实现选型要求。在为冻结候选建立原始需求对应的验收判据前明确触发svc-verification，已读上下文可复用、references按问题读取，不再要求统一先读documentation/task-packet。技能正文不内联，也没有改共享技能本体。

业务验收直接读取run/input原始requirements和允许参考附件，引用路径、版本与条款；PR说明、设计和自验不得降低标准，增量任务保留未取消的基线要求及业务数据。审阅期间冻结base/head，包括packet-only提交。每个验收进程独立使用数据库、缓存、uploads、端口、浏览器会话和证据；conclude前保存证据并关闭自己的验收进程和工具会话，以conclude作为本候选处理及当前turn的最后动作，Braid沿Unassign终止本次reviewer Session；下一候选须等旧Session实际停止后重新指派。

机制接线在 `run.py:native_files()`、`agents/pi-glm-reviewer/`、`materials/pi-extensions/pi-braid-i15-reviewer-cleaner-e2e/factory-cleaner.ts` 与 `tools/mcporter.json`。Linux 短路径别名沿用 e2e 的原生清理流程；Mac 的实际写入位于本次 WorkSSD 输出目录。生成结束保留 maintenance 回执与 e2e daemon 清理结果。

同一未完成运行的机械恢复使用 `--resume-run-dir <output/.factory26/确切run> --resume-stopped-receipt <停止收据.json>`，同时沿用原 `--output-dir`、完整需求目录、`MODEL`、`TASK_CONTEXT_FILE` 和 `--evolution` 模式。可以通过 `--braid <独立修复的binary>` 选择已冻结身份的新二进制。入口复用原 application、input、worktrees、native homes、Braid state、预算和 request，保留原 run_id 与 started_at；不再次复制基线、初始化 Git 或创建另一 run。执行实际调用 `braid local <原request> --offline-resume`，Braid 自己完成受支持的状态恢复；入口不写其 SQLite。该参数不保证任意 blocked 状态已可恢复，具体 Braid 缺陷仍须由相应修复二进制处理。

停止收据由执行宿主核实后提供，必须含 `run_id`、64位十六进制旧 `container_id`、`stopped:true`、`owned_execution_stopped:true`、数值 UNIX 秒 `stopped_at`，以及 `container_state:{Running:false,Pid:0,ExitCode:<整数>}`。停止时间必须晚于原启动或上一恢复启动；同一收据不能用于第二次恢复。口头 flag 或仅一个 stopped 字段不足以启动模型。入口在模型调用前核对停止身份、保留官方输入和 context 字节、原根 Profile/model、冻结连接与 deployment/wire、原 seed commit 和 Braid 请求，缺失或改变明确报错。

每次恢复先将会被覆盖的 run 根控制文件与派生证据保存到 `recovery/<attempt>/`，旧 model-gateway 完整目录（含请求、HTTP错误与原私有权限）、native 归档、native-config 与 maintenance 移入该恢复归档，实际原生 home 和 Braid 原状态仍留在原位置；不复制大 worktrees。恢复收据记录停止来源、原 seed、模型、修复 binary 与入口字节哈希。旧失败 turn 和会话不能改写为成功，恢复耗时属于该 attempt，不用于宣称两模型严格同条件比较。没有新增运行停止阈值。

替换恢复二进制时，需要同时冻结它实际消费的资源协议版本。仅提供 `configure/fence/launch` 的 `support/runtime_resources.py` 不能与仍调用 `status/reclaim` 的旧 Braid 配合。已移除资源门控的版本还须配套 `runtime/native-managed.mjs`、`runtime/bin/pi` 及其真正加载的 Pi `dist/bundle/cli.js` 和同版 `dist/`；只替换未被加载的源码无法生效。可以将这些确定成员作为只读 overlay 挂载到原 runtime，并逐文件记录哈希，保留其它扩展、fd、模型路由和会话预算材料。恢复属于同一原运行，协议修复不能重新准备业务或重置原会话预算。

用户明确调整在途模型有序路由时，同 run 恢复额外传入 `--resume-routing-change-receipt <JSON>`。收据必须含原 `run_id`、`authorized_by:"user"`、非空 `reason`、原 `routing-snapshot.json` 的 `old_routing_snapshot_sha256`、新冻结 `support/model-gateway.json` 的 `new_catalog_sha256`、新 `support/gateway-routes.json` 的 `new_routes_sha256`，以及列明本次授权变化模型的 `changed_aliases` 数组（旧单模型 `changed_alias` 仍可读取）。入口要求模型集合不变、实际变化的链恰好等于列明集合，并核对这些实际字节与所有未列明模型的有序链及 deployment/wire 身份；未带收据仍要求原配方完全一致。变更身份归本次 `recovery/<attempt>/routing-change.json`，旧配置、请求和错误保留在恢复归档。该入口沿既有停止收据恢复原会话与应用，不会热重载一个正在处理请求的网关；运行宿主须先在可追溯执行边界停止旧 owned execution，再启动与新链长度及协议配套的冻结 proxy。生效以新 gateway ready/config hash 和实际请求回执为准。

此前I15以独立`skills/e2e/`覆盖同名技能；该历史材料及已冻结运行保留。当前业务状态转移reference已归共用e2e，主技能随共享源装配。业务状态转移方法要求有期限的可见成功/失败终态，再执行依赖动作，HTTP200不替代页面验收；首次失败与复测条件变化保留。完整示例采用冻结e2e指南API，示例局部预算不改变工具默认timeout/retry。新材料身份与读取证据见`tasks/e2e-acceptance-state-transitions/packet.md`。

2026-10-07的PBB与自验隔离更新交付在`runs/iteration15/materials/pbb-e2e-isolation-20261007/`。其中`protocol-inputs/`是从上述同版runtime复制的窄构建输入，不是完整执行runtime；仅PBB CLI增加了与status/tail一致的跨会话停止修复。重产此版本时，`--protocol-runtime`使用该目录，builder将其`node_modules/pi-background-bash/bin/pbb.js`明确叠加到旧底包，来源及成员哈希记录在`protocol_overlay`，不能继续用未修复的旧protocol输入。专属e2e技能同时保留业务状态转换说明与用例数据隔离说明；独立数据库不等于用例隔离，不默认逐例重置整个数据库。该更新只用于新交付，未热改已有运行。

I15原生settings启用`compaction.thresholdTokens=245000`，由Pi现有自动压缩路径消费；真实模型contextWindow、reserveTokens默认16384和keepRecentTokens默认20000保持。实际触发取245000与真实容量减reserve的较小值，较小模型不会超出本身容量；threshold不扩大摘要输出预算。Braid的协作上下文reset继续按既有生命周期执行，profile的hard bytes不是原生token阈值。此配置形成及材料读回不等于已经取得摘要质量或费用改善的运行反馈。

2026-10-08起，builder默认从当前`materials/skills/`中的有效技能目录装配完整共享库，复用`copy_skill`发布边界：SKILL.md、references、assets、scripts和许可文件；不复制目录维护用AGENTS.md或README.md。再按`variant/skills/`中实际存在的文件覆盖。共享技能不再由七项刷新名单或冻结底包决定；源码链接装配为普通文件，`context7-docs`继续来自公共npm生产入口。MAIN_SKILLS、REVIEWER_SKILLS及原生角色启用声明保持独立，库中新技能存在不代表会话自动发现或采用。I15不再保存整份e2e主正文，业务状态转移方法归共享reference。Pi/Braid继续使用公共源码与producer；新Lab沿公共网关交付，历史standalone入口保留。共享默认变化只供以后新装配消费，历史冻结包和在途运行不变；本轮未制overlay或部署。

I15 launcher显式启用`FACTORY26_SUBAGENT_CATALOG=1`。Pi的`before_agent_start`沿pi-subagents已有角色发现、disabled与capability ceiling语义，将当前可用角色的name和description追加到当次system prompt；技能正文和角色正文仍为独立文件，不内联。调用条件由角色description表达，不在root/fast另列一套条件。空目录不注入；普通原生子角色未加载parent subagent扩展，不因此取得委派能力。公共catalog hook补丁按现有runtime安装顺序应用，其目标模块属于I15 builder统一补丁目标集；新构建须消费包含该补丁身份的runtime，旧冻结runtime不能凭launcher开关自动获得hook。本轮完成无模型ExtensionRunner加载、system目录读回及native_files材料生成，未制包、部署或启动模型。


Lab同variant、同task原生恢复保留`native_scope_id`、原需求与补充context、业务应用、Braid状态和工作树、Pi会话/home/template、原request及模型逻辑名额。Lab先停止来源执行并保存完整data，再在固定`/workspace/submission`和`/workspace/template`路径调用Braid `--offline-resume`。默认继承来源冻结模型路由/catalog；显式实际不同配方在停止来源之前拒绝。旧日志和进程控制归档到recovery attempt，新producer重新记录执行，不把旧PID当新控制依据。该入口不支持任意历史绝对路径迁移，也不承诺恢复浏览器、PBB在途工具或进程内存；失败不会降级成新原生会话。manual恢复继续要求它原有的Docker停止收据。

正式 Hosted 由公共 Lab `--competition` 入口消费 `submission-models.json` 的主/视觉模型声明，使用平台注入端点与凭据。I15 的 `prebuilt_runtime` 配置使 Hosted 包携当前完整离线 runtime 和独立 E2E addon；安装入口依据生产者可执行成员清单恢复官网解压丢失的权限。本地挂载运行材料仍由原正常执行器持有，正式包不包含本地生成应用或原生状态。

E2E launcher保留执行器明确提供的非空 `PLAYWRIGHT_BROWSERS_PATH`（含特殊值 `0`，不会创建名为 `0` 的目录），不尝试 mkdir 显式的预装或只读缓存路径；未提供时使用运行所属的 `FACTORY26_BROWSER_CACHE_DIR`、`XDG_CACHE_HOME` 或 `HOME/.cache`，不会强制在只读addon内寻找或安装浏览器。修改launcher只影响之后启动的E2E服务，不改变已有MCP服务进程的环境。


自实现 Pi 扩展的维护源归 [materials/pi-extensions](../../materials/pi-extensions/README.md)，variant 不保留源码副本。装配器将所选 canonical 文件复制到交付 extensions/ 并记录源字节身份；原生入口与相对工具引用仍使用交付路径。当前历史冻结包保持原样，新的公共组件缓存与冻结 overlay 均纳入所选扩展及选择器身份。

I15 的本轮顶层执行容量由 Lab target 的 `max_active_agents` 冻结进 run manifest 和 lab-run 合同，再写入 Braid 请求。Hosted 默认 2，Local 默认 4；根、Issue、PR、reviewer 采用同一池，不按模型请求数计槽。原生接续只更新这次执行的调度配置，原任务、模型、assignment 和 Pi 历史继续保留。有限后台作业和未消费结果仍占责任，只有显式登记的 owned service 可在原生空闲、有限义务为空时经 stop proof 交接后释放；MCP daemon 在其专用启动入口登记 service，而非按命令名字推断。

验收模板仍采用 e2e `workers: 1`；I15 Braid 进程环境冻结 `VITEST_MAX_WORKERS=1`，由 Vitest v4 的真实配置解析入口消费。其它版本/runner 根据独立技能使用其实际单 worker 设置。源和新生产材料不等于旧原生会话已重新读技能；采用反馈须依据实际 runner 环境、命令、进程和结果。

生成入口的正常退出与业务完成分别记录。内部准备、生成、验证、发布或诊断失败保存具体错误，入口仍返回 0，供执行器继续保存并评测已有应用；`run.json.generation_result` 保留 completed、incomplete、failed 或 interrupted，不能从 entry exit 0 推导需求已完成。Braid 非 quiescent 或根未关闭不阻断既定 delivery ref 的导出。发布失败仅尝试同 run 的既定 ref 和初始 seed commit，经应用结构与路径校验后交付为 partial；否则保留已注入基线，记录 baseline_retained 或 unavailable，不把空或无效产物标记为成功。准备阶段诊断归 `output/.factory26/entry-result.json`。外部 SIGTERM/SIGINT 保留 143/130，SIGKILL 保留内核退出事实。

共享 workspace 清理尽力发送信号和等待，`workspace-cleanup.json` 记录原始检查/信号错误、观测 PID 与残留身份。清理不再抛普通异常阻断交付；列表返回只表示观测到哪些 PID，不能证明它们已停止。工作区、短路径别名及归档回收仅采用明确 stopped 回执，缺失或 unreadable 回执按 unknown 保留现场。本源码修复不改变已冻结的在途执行。

用户显式授权的本地临时模型替换由 Lab 新 run 的 `native_model_substitution` 合同控制，不修改本 variant 正式角色源。恢复旧会话时，文本逻辑 alias 保留、模型能力元数据采用实际 GLM-5.3；视觉 provider/角色与 E2E 使用独立 Flash alias。入口同时更新 capabilities template 和既有 native home 的真实 models/角色文件，记录 producer、实际生效时间、logical/actual 模型及修改材料。原输入和旧配置保留在来源及 recovery 归档；该记录不承诺旧浏览器或工具进程继续存活。费用按实际模型的执行切片，不按历史逻辑 alias 覆盖整个 scope。
