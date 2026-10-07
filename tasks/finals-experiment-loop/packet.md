# 决赛实验基础设施重设计

2026-10-07 用户告知“钥匙串我刚刚授权好了”。此前等待系统授权的前提解除，evaluation_implementation 恢复原 self-test 认证与实际评分闭环，优先复用已有登录材料；已通知原独立验收会话在 Stage1 完成冻结后按原计划独立评分、接续 Stage2。授权完成不等于认证或评分已取得，下面的 pending_auth 记录是当时事实。默认维护基座同步为已正式发布的 p，不再指向旧 o。

2026-10-07 用户明确“是，你不必停下，继续”，继续原优化和验收闭环。runtime 集成已提交 `e7a3cb7d`，公共回执及 self-test 接入提交 `d7c4605b`。正式默认已切到直出 p：约 495 MiB，经维护入口首次发布 42.84 秒、再次调用复用；真实 ARC 容器在只读 runtime 下通过 `agent-browser open https://example.com` 与 snapshot，缓存后操作 2.78 秒，`--help` 不下载浏览器。构建与基座精简共用一个浏览器入口实现，不新增工具分层。原件见 evaluation；这些不是空缓存完整构建或生成 Agent 使用通过的证明。

独立 Stage1 run `610daf8655bc4f178cf6b0b35e94cfc7` 仍消费完整 c，已实际写入认证、数据库及前端文件，保持同一执行继续生成；不为默认材料更新打断它。完成后由原独立负责人冻结应用、执行模拟与 self-test 评测，再接续 Stage2。尚无阶段完成或评分。历史 j/m/o 的体积、发布及失败事实保留在下文，当前默认以 p 为准。

2026-10-07 用户再次提醒“避免过度的校验、安全、隐私设计”。后续修复必须对应已发生错误或具体的凭据泄露、误操作、产物损失风险，不扩展通用校验层、隐私框架或启动门禁；不把辅助证据缺失判成运行失败，不为填齐验收字段追加无关实验。继续优先原运行接续、构建部署耗时及正常使用负担。

2026-10-07 用户回复“那么继续推进优化”，继续授权既有优化闭环。当前优先解决原 Stage1 的原生接续故障，再以真实源码修改取得精简 runtime 的构建/部署/消费证据。execution_owner 持续持有构建部署，与独立验收的原恢复负责人协调在途版本，不重复构建或接管运行；主修正公共 dispatch 异常的状态与原错投影。self-test 钥匙串授权仍等待用户，不触发新查询。

当前 runtime 原始 `du -sk` 为 1,106,552 KiB，正式默认 j 为 551,760 KiB，最新直出 m 为 507,260 KiB（约 495 MiB）。m 的 37.07 秒是缓存命中的构建/导出，不是空缓存或 Braid 源码改动耗时；j 默认发布及同版本复用有正式部署回执。Stage1 最新 de22 已实际恢复同一 root native identity 后断连，原实施输入在旧 reset 中丢失可执行唤醒的问题正由原负责人修复；没有新的生成完成、冻结应用或评分证据。

随后恢复负责人已产出新 Braid c，execution_owner 复用其字节组装 o（518,416 KiB，约 506 MiB，实际组装 5.18 秒），通过维护入口正式发布并切换默认 target；原件为 `runs/arc-default-deploy-20261007/runs/default-runtime-recovery-c/records/runtime-deployment.json`。该发布仍为 full-rsync，同版本复用已有证据，新版本自动兼容基座选择/增量仍由同一 owner 完成。主已采用 advisor 的副作用边界判断修复公共 start 异常投影，并保留 subprocess stdout/stderr 到 start-error 原件；Local 派发受理显示 starting，而非尚无实际观察就报 running。以上只做编译和实际旧记录查询，后续资格由原独立接续取得。

最新维护 target 已内置正式 o 基座，普通用户不提供额外基座参数；维护增量路径实际取得 `reflink-base-plus-braid`、3.29 秒（`runs/arc-default-deploy-20261007/runtime-delta-staging2.{json,time}`）。发布已改为同父目录 staging 内完成复制/delta/新回执后 rename，避免 clone 携带旧回执被中断后误认。该样本 Braid hash 与 o 相同，只证明路径；c 原编译耗时日志缺失，不补造。原独立 run `610daf8655bc4f178cf6b0b35e94cfc7` 已实际消费完整 c，root 原身份 wake turn completed、fast 实施 wake turn running，应用完成仍未证明；不能称本次运行消费精简 o。I14 具体错误 brief 修复提交为 `fcc1a6bc`，其它当前任务集成仍待完成。

2026-10-07 用户补充官网费用回执的已知平台缺陷：创建为 `official_evaluation`、启动显示 `self_funded` 时，实际已经使用比赛费用。已核对新 run 的 Hosted start：当前没有比较这两个费用字段的拒绝校验，冻结模式不被启动响应覆盖，原始 upload/create/start 回执分别保存。因此不新增兼容层或平台写请求，只在启动边界及运行说明记录该例外；后续验收不能把这一差异判成自费或启动失败。此次为代码路径核对，未新发官网请求或消费比赛费用。

2026-10-07 11:00 当前恢复事实：第二版 Linux runtime 已部署，新 run `d38fa85756f24f13bb5fbb262b3fdf80` 在约 10:58 启动，保留原 native scope。恢复负责人读回两个中断 reset 均 `applied`、旧 provider session 均 `replaced`，并取得新的 completed `reset_continuation`；应用第一阶段完成及后续评分仍未取得证据。主此前只读上层验收会话，漏掉其子负责人已执行的进展，两次“还在准备 Linux”报告过时，不代表实际执行一直等待。

本次恢复发布从约 10:26 到 10:58：首次完整 Linux runtime 构建 705.7 秒，首次 restart（含约 1.1 GiB runtime 同步）156.0 秒；首版因 assignment 已恢复 active 而恢复 SQL 只接受 blocked，实际未触发 reset，修正一条条件后再次构建。第二版构建/导出存在失败重试，其中 Docker identity GET 10 秒超时使 runtime-source.json 未生成，包构建原错为该文件缺失；最终 restart 161.2 秒返回。这是完整 release 重建/输运、实现返工及导出边界错误的叠加，不是单纯交叉编译耗时。

用户指出 Helium 已登录 self-test，并明确允许逆向其登录接入。主实地确认已有 xiaoland 登录会话；撤回将“cookie 未部署”当作需要用户解决的外部前提。evaluation_implementation 持续完成现有登录态到维护客户端的安全接线及真实认证核验，凭据不进入公开记录或迁移 data，未取得该接线成功证据前不宣称 self-test 完整可用。

实际接入现已自动发现 Helium 目标域 cookie 并走 macOS Keychain 的既有 ACL；系统需要用户允许一次读取，不能由开发 Agent 绕过。用户对该系统授权回复“稍后再确认”，因此不再触发查询/弹窗，认证成功及新评分仍未取得。私密材料准备、复用、评测映射和 child 回收由设施负责，不把接线交给使用者；runtime 与其它独立工作继续。

认证模块已去除派生密钥出现在 openssl argv 的边界，使用系统 CommonCrypto 的内存接口；主实地确认当前 Python 可加载 CCCrypt 符号，仅核对原生接口可用，没有解密或外部请求。后续 HTTP 认证成功仍待用户授权，不以静态编译或符号发现代替。已准备的私有 cookie 材料会复用，避免每次查询重复钥匙串读取；必要准备发生在耗时打包前。

2026-10-07 用户新增明确授权：“runtime 的大小也是个值得关注的问题……尽可能精简，避免预打包开发环境比如 chromium、better-sqlite……完整构建、部署等的耗时也需要优化，请你推进。验收不要只是能用，而是用得好（使用者不绕弯子、消耗 token 少、消耗时间少）”。execution_owner 已接续 runtime、依赖材料、DX builders 与增量部署，evaluation_implementation 持续负责 self-test/auth/映射/回收；共享 local_run 按函数边界直接协调。advisor 建议冻结基座派生新 Braid 字节、远端宿主内独立复制后只传变化，并修复导出完成被清理网络错误否定的边界。体积、冷/热构建、实际传输与独立使用成本纳入 [evaluation](evaluation.md)，具体实施归 [implementation](implementation.md)。这些是正在实施的目标，尚无精简或提速通过声明。

## 当前纠正：模型配方实际消费

主采用 advisor 对普通 CLI 输出的判断：默认 brief 加必要回执，完整 JSON 显式 `--json`，Python API 与保存原件不变；控制受理、实际终态及保存完成分别表达。初版实际只读查询 d38 显示 running/active，表格输出 258 字节、同次完整 JSON 146,510 字节；这是输出规模事实，不是 token 节省测量。随后根据独立会话反馈，为单 run 补配方、来源、记录路径和保存回执，无参数列表仍是 brief；P2 读回 saved=true、d38 明示 unknown。start/restart/control/evaluate 的新默认输出仍待独立真实操作验收。

2026-10-07 用户指出，验收错误使用已明确耗尽的 ARC API，而非当前自费配方。主 Agent 承担这次冻结配置错误；历史 ARC 授权不代表本轮应选 ARC。P1 `e1ce4d6f6a174bb995c74f22e3db3a0d` 实际首次请求为 HTTP 402 `insufficient_balance`，没有应用生成进展，不能算有效零分或验收通过。原始 run、请求错误与保存材料保留；不要求用户补充 ARC 额度。

后续本轮验收改用集中维护的当前自费配方 `harness/model-recipes/self-funded.json`。生成装配与 Hosted 评测共用 `freeze_model_channel`，本地无模型评测不读取供应商凭据；运行入口已实际消费冻结路由和 selected catalog，不再只复制 `--route` 文件。per-provider 模型描述与私有凭据一并装配，不把官网 `billing_mode=self_funded` 当作模型配方切换。验收会话不负责寻找凭据或拼供应商配置。此节覆盖下文和 evaluation 中旧 ARC 冻结及“尚未收费运行”的过时状态；旧段落保留为实施沿革。

advisor `recipe_source_decision` 核对了文档审计中用户指定的 GLM/Flash/K2.7-code 链，以及 10 月 6 日 I14 实际冻结路由与千帆成功、Flash 千帆限额后 Ark 接管的记录。公共配方补齐同一来源的 K3 与 DeepSeek0731；两 variant 按实际角色闭包筛选，不从 catalog 的默认项选供应商。主已修改 execution/targets 的公共配方选择、所需 alias 冻结、selected catalog 与私有凭据材料；self-funded 路径移除 ARC Meter。provider_model_config 完成 builder/shared services 的网关消费链及 per-provider 参数，Linux binary 为 `runs/provider-model-config-20261007/delivery/model-proxy-linux-x86_64`，SHA256 `388b29d3002dbbf6add9051ad986cb6de46021736eace1d02b3ee4bf0a98d38f`。主接通原生模型描述，保留会话身份与兼容配置，并通过 Python 编译。已向原独立会话发送短消息继续 BookStack；尚无修复后实际调用或控制验收结果，不把源码编译当作通过。

修复后实际接续 run 为 `bf51263913f7414d9d50207deaa417c8`，保留 P1 native scope。保存的 `data/harness/e1ce4d6f6a174bb995c74f22e3db3a0d/producers/bf51263913f7414d9d50207deaa417c8/gateway.log` 中六次 `upstream_headers` 均为 `qianfan-token-plan-glm-5.3-flash`、HTTP 200，证明本次确实消费自费配方而非 ARC。独立会话确认真实工具活动及 pause/resume，实际暂停约 50 秒（等待 30 秒另加操作往返）。之后出现代理 413 `body_limit_or_read_error`，终态 failed；费用未采集不记零。SDK 回收又遇到程序 `.private/model-proxy` 的权限边界，现场通过保留私有原件及移出 SDK 回收范围恢复 saved=true，不代表自动保存已通过。provider_model_config 继续负责 413 根因/修复与新 binary；cold_local_profile 继续负责 saved-facts 同步、私有状态/SDK 回收边界。详见 evaluation 的实际记录，应用完成与后续矩阵仍未通过。

- **Objective**: 面向 2026-10-08 18:00 决赛截止，重设计开展、观察、控制、接续和分析 ARC 实验的完整设施。让 Agent 主要处理实验问题，不再负担环境接线、身份拼接和机械排错；simplicity、agent-friendly、traceability/observability 都以真实使用成本判断。
- **Guardrails**: 2026-10-06 用户已明确批准实施计划开工、自由提交及真实模型独立会话验收，费用不是问题；原话见下文。不控制其它任务运行、不清理历史数据、不 push。Mac 产物只在 WorkSSD。保留他人工作区改动；不编写或运行 Factory/Braid 的测试、smoke 或换名自检。用户新增的自实现模拟测试指生成应用的评测，不扩大为设施测试。
- **Verification**: 先定义代表需求与可观察结果，再以独立 Agent 的实际使用 profiling 取得反馈。覆盖三参数启动、status、pause/resume、同 variant restart、本地与 Hosted、Pi-only 与 Braid、OTLP/Console、资源、费用/turn 策略、顺序 stages、失败/取消及完整结果保存。查阅历史材料的耗时只作为诊断基线，不能充当真实启动或改造收益证明，方法见 [evaluation](evaluation.md)；不把这些活动塞进实现计划的调查阶段。
- **Current Truth**: 用户已批准 [design](design.md) 与六段 [implementation](implementation.md) 开工。自费配方已由真实请求 HTTP 200 证明实际消费，pause/resume 保持同一容器；最新 BookStack 接续 `a0d8fdab6eea4fe295c1bbcff65bca41` 约一分钟返回，status 正确显示 running/failed、资源与原生错误，失败现场自动保存成功。该次后续连接超时，没有完成应用或取得随题评分；费用未采集，完整验收仍未通过。
- **Next Step**: evaluation_implementation 接通 self-test 及四个测评后端的公共接口、配置、原件保存和实际操作；独立会话继续本地 GitHub Stage1/2 的生成与控制，冻结后独立评分。官网生成明确拒绝的路径不再重复上传；BookStack 保存现场及网络故障证据保留，按可消费的修复条件接续。主更新设计、矩阵及 packet 并集成返回，不重复启动 observer、不接管其它任务。

2026-10-07 最新 Linux proxy 去除任意请求体字节上限，仍保留读取超时、JSON 边界和具体 `body_read_error`；交付 binary SHA256 为 `eeacf0fb751b53499941e01ac49b061e497eac3212b0debd8c1a521087e77388`。旧 `388b29…` 是上一接续的冻结身份，不覆盖旧 run 材料。P2 接续已不再返回 413，但发生 `502 upstream_transport_error`，原始诊断为 `Connection timed out (os error 110)`，处于 SendRequest，不能证明供应商未收到请求，因此不扩大模糊错误自动 fallback。普通 `lab logs` 仍缺 SDK 捕获的过程内容，该问题由本地负责人持续处理。

主已修复生成装配未回写 Hosted frozen target_config 的共享边界，以及 Mac relay 在自动评测子 run 派发回执到达前退出的问题。原执行宿主仍是唯一 observer；Mac 仅登记已经派发的同身份 task-evaluation child 并启动 saved-facts relay。freeze application 失败保存具体派发错误，不留下无回执等待。上述最新接线仅完成静态编译，实际评测与 Hosted 仍待独立操作反馈。

最新 proxy 为请求保留实际序列化 `request_bytes` 和 attempt 的 `elapsed_ms`，不复制或记录 prompt；交付 SHA256 `19562690787bf2e0a51aefb71e1d99e35e6f70054fe6f57e050344ac8de83fd8`。P2 网络事后核对只证明宿主当时可达，不能替代容器失败时证据，故不擅自改供应商或 timeout。SDK 确认普通过程与 stderr 合并到 `.arc/stdout.log`，新增 observer 回收为 records/agent.stdout.log；新运行以启动前字节 offset 分隔，旧无 baseline 的记录明确包含迁移历史，不默认展开完整 rollout。

实际浏览器 Console 初次连接拒绝，原因是 Mac→sfp7 隧道退出；共享服务仍 HTTP 200，恢复 ssh -fNT 转发后页面因列表 manifest 字段缺失崩溃。cold_console_profile 持续负责 API/UI 契约、重新编译部署及实际页面反馈。Pi/Hosted Stage1 `7868abfa67fa4ce096126ccc768e4bde` 已由独立会话启动，当前在上传自包含包，没有平台 run ID，不重复提交不明写请求；BookStack 完成及评测仍待恢复。

当前提交 `a0305e4b` 保存公共自费配方、冻结入口、DX 消费链、观测回收与日志边界；已有网关/catalog 的其它工作区变化按归属保留，不宣称整个工作区已清洁交付。Console 当前已实际浏览器验证 Pi 详情的 lifecycle/activity、资源/native 与费用 unknown 可见；完整 JSON 不作为默认界面，进一步可读性部署由同一 owner 持续完成。

Hosted 的独立操作取得明确 HTTP 400，而非模型失败。cold_hosted_profile 当前 GET 核实 `hackathon` 已 ended，Stage1/2 需求仍可读但无新建生成提交入口。2026-10-07 用户纠正：self-test 是原先明确要求的测评后端，官网生成入口关闭不能扩大为测评不可用。撤回以 Evolution 替换本轮题目的提议及待确认事项，不启动新题或复用其它任务提交。原 Hosted 生成两阶段覆盖仍有缺口；本地 Stage1/2 生成、独立 self-test 评分继续沿用原授权。

独立会话继续持有已授权本地 I14/sfp7 Stage1→Stage2 验收，已收到短自然请求；BookStack 原网络故障现场保留。明确上传拒绝后的保存边界已由独立会话修复并用本次真实原件得到 saved=true（scope program/inputs/records，无远端执行 workspace），不是生成成功或完整远端回收。

后续提交为 `bd1e2cfe`（所需 catalog deployment、provider 描述消费、Console 与明确官网拒绝的保存）和 `27bd09e7`（费用缺口具体来源与原因）。catalog 只采用当前自费链依赖的新增项，其它已有工作区配置保持原样。当前 Pi 详情已实际浏览器核对：最新 502 原错、retained session、终态资源与费用 not_collected 原因可以直接查看；旧 P2 过程 stdout 已通过已有读取路径补入 records，并明确其启动边界未知，不改原始 workspace。

本地 Braid 首次 `26cd033f71ef4ee6bc5c3cd599b8e73d` 约四秒退出，原错为旧代码读取 `routes['factory26']` 的 KeyError，无模型调用；独立会话修复为按实际模型解析集中绑定，继续持有实际运行和 native idle 证据。该次失败未计为生成或接续通过。共用 Braid 状态读取与当前 scope/native 路径映射还在同一会话的修复闭环中，主不抢占控制或另建 observer。

原 Stage1 官方 self-test 页面当前可读，任务为 `github-stage-1-req-test`（另有 Stage2/3），上传应用 ZIP 最大 50 MB、根含 Dockerfile，页面说明结果仅本人可见、不计正式成绩。该入口与已关闭 Hosted submissions 不是同一路径；没有公开的精确需求/评测器版本时保留该限制，不将其变成新增许可门禁。evaluation_implementation 持续负责官网、self-test、本地随题、本地模拟四个测评后端的实现与真实反馈；主负责公共接口和文档集成。独立验收会话继续持有本地生成与控制，应用冻结后独立测评，隐藏反馈不进入生成。当前 self-test 仅取得只读入口证据，尚未上传评分，不能宣称接入或验收完成。

## 开工授权与责任

2026-10-06 用户原话：“好的，没问题，你可以开工了；你可以自由提交；基于 I14, pi-minimal 派生出 I14-dx-test, pi-minimal-vv-dx-test 两个 variants （派生新的 variant 是因为本次实验基础设施改进必定会涉及到 variant 的改进），按你说的用独立会话验收，你可以使用真实模型，不需要 mock，费用不是问题。”这条指示批准当前 design/implementation 的源码实施、必要部署、当前任务提交和真实模型验收。比赛提交与既有运行仍不在接管范围。

主 Agent 负责公共 run API、CLI、自动化、ARC 执行、restart、target 配置、整体集成和提交；cold_console_profile 持续负责 OTLP/Backend/Console/Braid view。前两位执行负责人的交付尚未接通真实控制、数据回收和原生接续，主没有采用其完成声明。evaluation_implementation 已确认没有构建、SDK 或收费运行在途，并转交执行责任；它继续持有 evaluate/package_arc_replay 的独立评测结果。2026-10-07 execution_owner 明确没有在途运行后，主接管两个 variant 的 main.py、I14 run.py 与共用 harness_services；execution_owner 仅维护两个 build.py 并从最新源码重建材料。原草稿和构建原件保留，不回退其他工作区。

2026-10-07 已移除 I14 dispatcher 对旧 execution context 的启动门禁，入口直接运行 variant。接续应用迁移到真实 template 根，native 数据独立迁移；当前平台输入与私有评测上下文不被旧输入覆盖。Hosted 共用轻量 raw receiver，按当前 Lab run ID 单独保存 producer 数据；本地使用共享 Collector。执行端 supervisor/Python 自动化通过 remote spawn 接入，Mac relay 只消费保存的记录并回收数据，不成为第二套运行观察器。以上是源码接线状态，尚未进行本轮真实模型验收。

已经向独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 发送首个自然请求：“现在帮我用 pi-minimal-vv-dx-test 在 WSL 跑一次 BookStack。跑起来后暂停半分钟再恢复；看一下状态、日志和费用，确认有真实进展后停止并保存现场。顺便记录一下使用中哪里费劲。”不提供 CLI 操作清单或内部技术导航。请求开始实际 P1 使用，但发送成功不证明已经运行。费用目前可采集共享 account-key-window delta，不能冒称 per-run，因此 P1 的精确费用自动停止仍未覆盖；这次手动停止属于原验收矩阵明确允许的接续准备。WSL 固定实际 loaded image ID cfb919…，源/目标 17 层一致与默认配置差异的证据保存在 `runs/arc-bench-image-comparison-20261007.json`。

首个实际 P1 run 为 `e1ce4d6f6a174bb995c74f22e3db3a0d`。独立会话已观察到完整 ZIP 构建及输入重复传输，`starting` 未区分阶段会增加查日志成本；尚未收到其模型活动、pause/resume 或保存验收结果。advisor 因官方 SDK agent 目录会解引用 symlink，建议本地小程序目录＋固定只读 runtime、Hosted 完整 ZIP；已采用，P1 保持原冻结材料不打断，后续 P2 记录各段耗时与传输事实，不凭源码宣称收益。当前任务源码提交 `f01e5fa1`，后续 runtime/运输及 provider 配置修正仍进行中。

2026-10-07 用户追加：“llm gateway / model proxy 注意引入 per provider 的模型配置，比如 ARK 的 kimi-k2.7 的 max_tokens 和其它提供商的配置就不太一样。”已交 advisor 决定 catalog deployment 归属及 cap/default 语义，再交 provider_model_config 负责 catalog、Rust proxy、LiteLLM 发送边界及说明；主接 native 模型描述和统一装配。该责任不控制当前实验，也不擅自增加其它供应商的付费调用。具体数值必须核对对应 provider/套餐的来源，不能以一个模型名推导共同上限。

已安排 local_execution_decision advisor 判断官方 SDK prepare 后直接 Docker create/start 与继续捕获 SDK stdout 容器身份的取舍。判断依据是实际 SDK `docker run --rm`、随机容器名和只在结束后保存的 local-run.json；尚无本轮收费运行，不能把 SDK prepare 成功当作运行控制通过。

已采用 advisor 的直接 create→保存 CID→start 建议；cold_local_profile 接续其边界调查，持有新增 local_run.py 的真实执行、远端部署与控制回收结果，主负责把它接入公共 API。SDK Meter 是共享 access-key 累计差值，不保证单 run 归属，不因此增加串行 gate。默认 target registry 已改用实际 Mac 材料构建路径与远端执行路径，不再返回缺 SDK/runtime 的假 profile；任务 registry 提供 BookStack 和已冻结 GitHub Stage1/2 的需求入口。主只读 GET 确认 `/competitions/hackathon` 的实际 id 为 hackathon；官网凭据使用现存 ARC dotenv，而非不含 ARC key 的 models.env。以上仍是接线与事实核对，不是付费验收结果。

实际材料检查尚未通过：第一份 I14 ZIP 根 main.py 仍是旧 facility dispatcher；第一份 Pi ZIP 仅 28 项，缺 node/pi runtime。原包保留在 runs/finals-experiment-loop/materials，不发给独立验收者，variant owner 正修复直接 builder 与入口。新版执行装配已改为调用这两个 builder，不再进入 package_agent 的定义/制品门控包装。原生状态观察只采用真实 header/session_id；没有 provider turn ID 时保留缺失，不用行号补造。状态脚本错误保留 stdout/stderr，查询本身不制造活动时间。

历史 Hosted 原始 template-bundle ZIP 的实际根为 template/，已按这条证据修正下载映射到 data/workspace 与 data/harness。完整 native 历史仍迁移；新 raw collector 使用 native_scope/producers/当前 Lab run ID 独立目录，不把旧 batch 重新计作新 run 的消费。以上代码尚待真实包和平台运行验证。WSL SDK 已部署，镜像仍需执行 owner 完成传输；共享 Console 的 sfp7 宿主/容器 bridge 和 WSL 宿主反向隧道已有 HTTP 200，WSL 容器入口、实际原生生产、费用以及 Hosted raw 回收尚不能算验收通过。

独立验收会话 `01a1118d-d790-7df1-93b5-df1801813158` 负责真实首次使用与 profiling，不以阅读实现代替实际反馈。evaluation 已冻结最多八次生成与三项独立评测，覆盖 BookStack、GitHub Stage1/2 及策略/平台停止；费用来源未知不当作零，非正式参赛 self_funded。当前尚未开始收费验收，等待真实可消费执行与服务版本。旧段落中的“待开工”描述是历史授权沿革，不代表当前阶段。

用户随后要求验收派单尽量接近平日的自然消息，不发长串明确边界或操作导航。已告知独立会话：前述长说明属于准备，不作为冷启动顺畅证据；真正交付后的派单只描述实验目标与关心的结果，入口查找与排错都计入真实使用负担。

Console owner 已报告 sfp7 的实际部署：独立目录 `/home/yyh/factory26-exp-console-20261006`，loopback `127.0.0.1:18765`，服务 PID `3337058`，`/api/runs` 返回 200；Linux Braid binary 已编译并具备 `telemetry reconstruct --decoded`。这证明服务可启动，不证明真实 run 的生产、传输和投影已通过验收。执行 owner 的最新交付仍缺真实 ARC target/Hosted 接线，restart 仍有创建目录与旧 handle 继承问题，主未采用其“闭环完成”声明，已要求同一 owner 持续修复到实际可启动。当前仍没有本任务收费运行。

公共 observer 已接入 Console saved-facts 发布，终态只有 `save` 明确返回 `saved: true` 才结束；发布失败独立记录，不改变运行生命周期。共享字段为 `observability.service_url`、`registration_token_file` 和 `collector_token_file`，秘密不进入迁移 data。此接线仍需真实生产者验证。

主已实地只读确认 sfp7 HTTP 200；服务部署期间重启，PID 不作为永久身份。初次列表包含本任务构造的登记，不能证明真实生产链路，已要求 owner 删除；owner 已报告清除并明确旧 facility4 缺少 status/native turn/cost。约 27 MiB 的单次 RSS 只属于空载服务，不作为低内存验收结论。当前源码中的旧 `lab.control.Control`、exclusive/send 写入链没有调用方，已删除，保留进程出生身份与历史只读等待；这不等于整套 lab.exp 已退役。

主分担 `lab/arc_bench/hosted_run.py` 的真实官网 API 适配，执行 owner 继续负责打包、数据映射与实际 dispatch 接线。新模块保存 upload/create/start/cancel 请求及响应、真实 submission/run ID、日志 cursor、平台费用和全 workspace ZIP；未知写请求不自动重发，5xx/传输不明不冒充确定失败。当前只通过编译，未调用收费 API；规范 data 在平台导出中的映射和原生接续尚须与实际包完成闭环。

旧入口退役的调用核对确认：新评测仍可经 ARC adapter 导入旧 artifacts/core/telemetry，I14 的 experiment_entry/bootstrap 仍带 state_writer，package_agent/runtime 也被其他当前材料构建调用。整目录删除 lab.exp 会破坏这些维护调用方；已经冻结的 runner.pyz 不读当前源码，但重新构建仍受影响。新 run 必须提取实际 ARC/材料功能并切断门控，而非依赖 gate 在某些环境 no-op；旧源码中他人的未提交变化不得覆盖。该核对由 cold_local_profile 完成，只读，没有控制旧运行。新增 advisor 委派被平台 thread limit 拒绝，当前没有取得新的重大退役取舍意见，不把只读依赖核对冒充 advisor 建议。

## 历史需求与决定沿革

用户要求先定义“怎样算好的实验设施”，依据实验需求、工程知识、Agent 使用 profiling 建立完整因果链，不为找问题而找问题。Mac、WSL、sfp7 和官网差异属于设计对象，环境触发、集成耦合与设施内部缺陷分别归因。Exp Console 属于实验基础设施，不留作无期限的外围改进。

用户随后明确要求：Exp Console 不再承担实时介入；数据走 OTLP，Braid 自己实现 Braid 视图；本地共享包含 Collector/Backend 的观测服务，官网执行仍轻量自包含。还需资源采集，耦合 ARC-Bench 并统一 variant/gateway/collector 装配与路径，Python 条件自动取消/接续，自动保存完整工作区、日志、评测和费用，移除所有 gate/校验，三参数启动与停止/挂起，以及 stages。最后提醒“这个任务不小哦”。以上全部属于本轮设计范围，不按截止日期偷换成少数入口修补。

2026-10-06 用户补充了自动且强耦合的自实现模拟测试、官网重放、试题自带三类评测，统一各 variant 共用的 gateway/collector 装配，以及来自采集的 spend、native session turn idle 等 Python 变量。同期提出的跨 variant、多路径接续后来被用户撤回，当前同 variant 整体 data 迁移的决定见下文。

早期方案阶段的授权原话：“我同意你定下的这个推进方案，在开始实现之前和我确认方案，你可以自由继续推进。”当时只认可设计推进方法，尚未批准开工。该阶段已被顶部记录的明确开工授权替代；本段保留沿革，不要求当前执行重新申请许可。

用户随后明确：“核心调度对象/控制单位是run，而不是实验。（我后续还会不断补充，你不必停下）；你总是可以有不同的看法”。已撤掉把 run 定义为整条实验链再用 attempt 控制的候选；每次实际可独立派发/停止执行是 run，内部阶段服从平台真实粒度。来源、接续、重试和独立评测通过 run 关系连接，experiment 仅标签。stop 只操作指定 run，跨 run 操作与费用范围由普通 Python 程序明确表达。

用户质疑“撤销尚未派发的自动后续”是否仍保留 capacity/queue。复核确认这是设计越界：把尚未执行的 Python 代码想象成了设施待办任务，执行调查稿也残留 reservation/slot 的目标措辞。主 Agent 与 advisor 已撤回建议，目标设计删除内部 capacity、admission、slot、reservation、运行队列及未来任务撤销机制；历史故障证据保留。启动直接尝试执行，资源不足返回实际错误。Python 直接调用运行 API，不增加 action 解释层或任意脚本断点恢复；默认 stages 只在 completed 后继续，显式 restart 仍可处理 failed/stopped。stop RUN 不停止独立自动化程序，两者不混称。

用户最新修正要求：suspend 改 pause；接续不能用 continue；程序与数据路径规范后，只迁移数据且不允许切换 variant，extract 无意义；新增 status，无参数列未归档、非正常结束的 run brief，由绑定 variant 的脚本解释活动；继续收敛到可列实现计划，计划不含信息收集、调查或实验。当前采用 restart 表达同 variant 新执行，覆盖 stop→保存确定数据→迁移→启动的顺序；status 默认条件为未归档 AND lifecycle != completed。状态脚本固定在本次 program 版本，只读采集事实，脚本错误显示 unknown；正常执行得到零分仍为 completed。archive 仅列表标记，自动保存结果另行完成。此段覆盖前述历史 cross-variant、多路径接口及命名建议，设计正文以最新决定为准。

第二轮独立文档预演已经能推导启动/status、pause/resume、restart、归档后查回与独立评测；唯一操作缺口是自动三类评测的实际启用和官网费用来源。已补 task.json 的 evaluations 清单、同一应用快照绑定及 official billing_mode，不加许可字符串/审批门禁。另经 advisor 核对 Braid retained request 的实际约束，明确同 task 用原 native 状态、下一 task 建新状态，避免旧 root 已结束就跳过新需求。预演仍是文档反馈，不是运行验收。

主 Agent 与 advisor 的建议是删除重复证明、准入和人工写入协调，但保留路径边界、秘密处理、准确控制目标、未知收费写入防重复这四类直接风险约束。这是明确提出的保留建议，不声称已获用户认可，也不改名藏回“全部移除”之后。具体理由见 design。

Collector/Backend 推荐来自现有接收能力、所需领域查询和部署总成本，而不是只因赶期限或最小代码行数。没有“新架构已经验证”结论。最小可用交付必须纵向包含执行、观测、控制和归档；分批决定交付顺序，不取消完整目标。

## 负责人及可采用结果

| 负责人 | 范围 | 当前交付 |
| --- | --- | --- |
| 主 Agent | 产品要求、评价标准、跨组件 HLD、方案复核及 packet | 本 packet、design、evaluation、assessment |
| execution_owner | 两个派生 variant 的程序/数据分离及原生接续 | 材料构建不能替代实际同 task/new task 验收 |
| evaluation_implementation | evaluate/package_arc_replay 独立评测 | 尚待真实应用快照 |
| cold_console_profile（承接原 observability_owner） | OTLP、资源/费用/turn、Collector/Backend、Console 与 Braid 边界 | [观测专项](cells/observability.md)，原 owner 已不在活跃树，主 Agent 在本轮明确转交收敛责任 |
| finals_infra_advisor | 重大工程判断，不担任实现 reviewer | 明确 restart/native task 分支、status/archive、Python 自动化及 Braid 自有低频物化视图，已整合到 design |
| continuation_journey_rehearsal | 首次使用者的独立文档预演 | 两轮桌面使用反馈；最新补齐评测清单与费用模式入口，旧多路径意见已随用户修正失效；不是运行验收 |

只读实施准备得到两项具体采用结果：sfp7/WSL 可用空间约 110.8/25.1 GiB，WSL 已有本地 Console，跨域 HTTP 未验证；Pi 历史主会话 274 条 usage 的原生 cost 全零而平台有实际费用，raw OTLP 省略 message_update、timing 仅 first_update，不能直接作为精确 idle。原件与限制分别记录在执行、观测 cell，主线未控制这些运行。

第一轮 facility_journey_profile、environment_causality 和三个 cold-profile Agent 的结论保留在 assessment。后续相关工作保持原 owner；profile Agent 的原始意见不自动等于已采纳事实。

## 证据与更正

2026-10-06 的三次只读冷启动调查墙钟分别为本地 95 秒、Console 164 秒、Hosted **214 秒**。这是 Agent 执行整个调查的墙钟，不是独立测得的主动劳动。Hosted 原返回写成 114 秒，已按 epoch 差更正。Console 样本为纯 Pi variant，不产生 Braid 是预期行为；其 creation 快照也不能证明从未运行，历史读回实际已有 Pi 请求和工具活动。不能用这个样本证明 Braid 接入失败。

历史 capacity 拒绝原件有价值，但不能仅凭报错断言 admission 正确或存在泄漏。另一任务后续保存了 terminal 仍占槽、writer-close/release 及下一次 reserve 的证据，应据其解释生命周期接缝，不能把旧失败快照当当前运行状态。

- [当前设施证据与因果判断](assessment.md)
- [质量标准及 profiling 方法](evaluation.md)
- [完整需求与 HLD 草案](design.md)
- 历史基线：[实验 DX 复核](../experiment-dx-review/packet.md)、[实验操作](../experiment-operations/packet.md)、[实验追溯](../experiment-traceability/packet.md)
- 顺序阶段历史：[Pi Stage2/3 packet](../pi-minimal/sequential-stage2-stage3-20261006/packet.md)
- 本任务只读分析快照：runs/finals-experiment-loop/readback-20261006-analysis.json
