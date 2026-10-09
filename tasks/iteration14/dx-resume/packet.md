# I14 GitHub：DX 新基线接续

本 packet 已退役为历史记录。用户随后授权删除所有不完整 I14，要求先复核新实验设计、暂不启动，并规定项目产物绝对只能位于 WorkSSD。下文将 I14 迁到系统盘是错误；外置根及旧运行现场已按授权删除。当前决定、清理终态及未来启动条件归 [夜间 packet](../overnight-plan/packet.md)，不得采用本 packet 的旧路径或接续指令。

2026-10-02。用户在实验DX交付后明确：“实验DX改进完成了。现在我们继续推进。”结合已授权I14实现、实验启动与热恢复，本阶段继续配置、实际准备并接续GitHub；Sheet暂停。源码及恢复采用DX提交eef231b1的新lab.exp入口，不使用已退役旧writer，不静默覆盖原冻结记录。

## 当前状态：所有实验暂停（2026-10-02）

用户在原 I13 会话最新原话：“暂停目前现有的所有实验，因为 API 额度即将耗尽。”主线已只读核对真实userMessage（turn01a0fca6-cb94-7af3-abba-320deae7fdda），该指示覆盖此前仅e2e及必要热恢复安排。所有后续prepare、输运、生成、重放评价、收费派发和源码修复推进停止；原owner仅执行暂停与必要保全，冻结专属controller/dispatcher后续调度。共享heartbeat已由全局owner设为PAUSED，不另建或自动恢复。

旧e2e在本指示前已因必要热恢复停止，保留实际exited来源，不重启来伪造pause；修复包/快照及原错误保留，新恢复尚未取得模型运行成功。cleaner已paused、reviewer已exited，均保持。实际进程/尝试完整清单及暂停回执由原owner补齐；两freshbaseline由另一稳定owner暂停。未经用户新指示不得恢复任何实验或评价。

## 前次范围：仅推进 e2e（已被全实验暂停覆盖）


用户最新原话：“暂停继续推进cleaner和reviewer；专注e2e。”该指示立即覆盖此前三项启动范围。cleaner/reviewer停止后续源码修复、prepare、输运、marker绑定、生成及评分，保留当前检查点、原件和失败半成品；由原owner核实并关闭仅两项专属在途本机操作，若已有模型入口则按精确身份受控暂停。reviewer既有远端归档允许保全，不推进新执行。实际暂停回执待原owner给出，不能仅据本条指令称容器已暂停。

e2e继续现有实际run `20261002-105607-3c89d659`、生成和已冻结独立self_funded评价闭环；仍使用原collector与十分钟heartbeat，已更新消费范围以排除用户暂停项的自动恢复。旧baseline暂停不解除；另一会话独立获授权的两freshbaseline不受本条范围调整影响。

执行owner仍为 `i14_launch`，持必要e2e修复、实际操作及终态/评测证据；主线维护范围和记录。启动卡点归[记录](startup-blockers.md)。

## 前次启动授权（历史，2026-10-02）


用户最新原话：“I13 我会另外去推进。现在的重点是让 I14 运行起来。”此指示将本会话优先级切到 I14 实际运行，撤销此前等待 I13 恢复闭环后才启动 I14 的主线安排。I13 原恢复会话由用户另行推进，本会话及子 Agent 不操作 I13。

本会话继续已授权四 variant 的 GitHub 范围、最新普通 Qwen / Token Plan 配方和每项 2GiB/2CPU、共享五槽约束。执行 owner 为本会话子 Agent `i14_launch`，负责必要调查、有界修复、保全/准备、冻结、实际启动、运行读回和监控证据；主线负责暂停边界、整体配方与结果采用。用户已明确回答：“baseline 继续暂停，只运行另外三个”。因此仅启动 cleaner/reviewer/e2e 的 GitHub，baseline 的旧容器、owner 和暂停状态保持。Sheet 不运行。

新执行复用公共 Lab compile/doctor/build/start，旧历史身份和失败原件保留；不另建 launcher、Console 或采集循环。独立 DX 会话仍持有设施在途修改，启动 owner 采用其现行公开合同，必要依赖集中交接。可恢复设施缺陷直接完成修复和真实反馈，不以准备成功代替实际生成。

## 接续初始快照（历史，已被当前启动授权覆盖）

用户原话：“本任务继续推进 factory26 的迭代。”本会话接续整体优先级、实验配方和结果采用；原官网恢复与实验 DX 会话继续持有各自执行责任，不重新拆分或接管在途操作。当前第一优先级仍是 I13 Flash/GitHub，I14 仅 GitHub，baseline 用户暂停保持，新增生成继续等待该优先事项与设施准备就绪。

接续时只读核对原恢复会话、DX 会话和已有采集摘要。新版需求接续已有官网 run `c5a3674c42c4` / submission `9cdbe3e15239`；采集批次 `20261002T094141.544700Z`（17:41 CST）记录 RUNNING，当前根会话最近 turn 已 completed、error=null，生命周期 idle。此事实不证明完整交付，也不能据静止归因为 OOM。原恢复负责人正在响应用户关于 OOM 停滞的核查；其当前结论与后续实际操作归原恢复 packet，不以早期 HTTP400 或旧需求失败概括当前状态。

下一步采用原负责人关于实际运行、内存与供应商请求的最新结论，再推进已授权恢复闭环；I14 配方沿本文最新普通 Qwen 免费额度修正。DX 会话正在收敛 compile/build/doctor 与内容验证边界，主线不并行修改其共享源码或重复派发。源码、旧原件、唯一采集器与 Console 均保持各自现有 owner。

## 范围与决定

四variant为baseline、cleaner、reviewer、e2e。baseline此前用户暂停，先保全与准备，不自动解除其暂停；cleaner已有完整停止快照，优先保留原进度；reviewer当前paused，须同样保全与核对；e2e尚未开始，可独立准备。原GitHub需求沿旧冻结输入，不混入新增Stage或隐藏评分反馈。每生成2GiB/2CPU，共享五槽；需要新的Docker准入权交接，不能从无running容器推导旧owner已退役。

模型配方沿最新决定：GLM-5.3-Flash的成员、cleaner、视觉及e2e走普通Qwen，GLM-5.3与Kimi K3同样走普通Qwen，内部DeepSeek走Qwen Token Plan。三组凭据由.secrets/models.env取得，不输出key、不回落ARC；默认根Flash，I13两组两题正式均分领先10pp条件尚未具备，不擅自切根或替换模型ID。新生成逐模型拆分native provider；旧retained恢复能否保持会话/profile身份需真实材料核对。

应用完成后每题独立冻结并按原self_funded/比赛额度关闭取得官网重放成绩；生成与评分费用分别保存。原Flash/GitHub运行、唯一Console与既有采集不改，新的实际接入交给原监控消费者，不另建第二服务。Factory/Braid不写或跑tests/smoke/probe，反馈来自编译、实际准备与获授权运行。

## DX 交付时的责任与事实（历史）

主线拥有配方、最终装配、实验启动、状态与监控接入。i14_recovery_routes拥有逐模型恢复接线及其有证据的必要修复；i14_host_handoff只读盘点旧writer、reservations及源保全/交接。主线保持整体集成责任，子Agent不得启动模型、停止无关旧资源或修改Console。

DX源码及离线制品发布已完成，不等于Docker接续、完整Harness恢复或供应商请求已经验收。当前正在消费公开合同和实际旧回执；真实模型catalog查询只读GET，不发生成prompt。原件归runs/iteration14/dx-resume-20261002，错误原文、版本、源停止与实际采用分别保留。

下一步是确认逐模型恢复合法路径与宿主准入，冻结新配置/私有凭据，完成实际无模型准备及逐角色读回，然后沿已授权GitHub范围启动并记录身份。若恢复需要丢进度、变更会话历史或同daemon退役无关任务，返回具体影响和最小决定，不据继续推进扩大范围。


## I13 优先阶段（历史，已解除 I14 等待）

用户新要求官网I13 Flash/GitHub 7e8ec62670df因ARC额度耗尽切换到自有API，采用I14配方。该项为当前最高优先级，独立原owner负责受控停止/完整保全和接续；I14当前仅推进无模型材料与接口准备，不启动新生成。实际catalog只读GET已取得HTTP200：普通Qwen提供ZHIPU/GLM-5.3-Flash而非裸glm-5.3-flash；Kimi包含kimi-k3/K2.7；TokenPlan提供deepseek-v4-flash-0731/4.1而非裸DS。供应商wireID与旧原生model.id不同，需要显式映射或合法迁移，不能只更换URL宣称完成。

宿主读回确认WSL旧执行权不满足新authority接管；development-2可用于独立准备，只有用户Redis，但新authority缺首次使用域消费不存在legacy registry的公开合同。已将具体原件交DXowner修接口，未编造空registry或停止无关WSL旧现场。

用户已确认本次I13 advisor“保留K2.7-Code，只切供应商”，内部DeepSeek采用Token Plan的deepseek-v4-flash-0731。这两个决定仅覆盖本次I13接续；I14 advisor仍为K3。旧官网源7e8ec62670df已单次取消并独立GET确认CANCELLED，最终ZIP为326459735字节，SHA256 de0f9bfe1af401b49756bf6abfd314fc75641b208f37afa1f70f4d41e826d43c；72条原生HTTP402错误明确为insufficient_balance，不能当作OOM。取消前ZIP、取消意图、原始响应、最终ZIP与18份native均在hosted-github-self-funded-r4保留。

最终ZIP缺clone私有.git，原来源保持partial。接续先以每个clone最后成功Git操作核实commit/branch，再用现有明确重建路径生成新Git元数据，保留全部非.git工作文件、DB/WAL和native；新index不是原index，原reflog与暂存独有状态不可声称恢复。若基准歧义或未发布对象缺失，呈现具体影响再决定。派生完整状态只属于真实离线修复后的新执行，并沿provenance保留原缺损。

实际官网表单只注入一个模型key，三路绑定不能仅靠模型配置生效。共享恢复包增加显式私有model-environment输入，只接受FACTORY26_MODEL_BINDINGS及其声明的凭据变量，入口在绑定前消费；不会全量复制models.env或建立模型网关。当前已完成源保全及共享接线的离线反馈，尚未启动替代官网运行或产生新模型请求。


## 执行归属调整（2026-10-02 15:12 CST）

用户指出主线陷入协调与细节、要求尽快官网恢复。现由原Flash/GitHub恢复会话统一持有必要共享源码有界修复、实际准备、官网提交/启动和监控交接权，取消此前共享源码只读及逐项向主线等待确认的限制。主线只持有整体优先级与结果验收，不继续拆分恢复执行。新DX监督器竞态已由900da591修复，offline-ready离线准备已派发；尚未取得替代官网run身份，不把准备派发当作官网恢复成功。


## 官网需求版本迁移（2026-10-02）

替代run 925e6ef9eaf9已提交并启动，但模型调用前因平台需求实质变化被原SHA门控拒绝，原错误、公开需求差异和终态保留，不记为有效零分。用户明确选择“保留进度，迁移新版需求继续（推荐）”，授权原恢复owner保留应用、Braid/native历史，显式迁移公开新版需求并接续官网。新旧需求身份、差异与采用边界须保留；结果单列，不与旧版I13分数直接比较。此次选择解除需求版本阻塞，不授权读取隐藏评测反馈或简单删除需求一致性校验。

## 2026-10-02 16:36 模型与供应商重新核对

用户指出普通 Qwen 已开通 Flash，精确请求 ID 为 `ZHIPU/GLM-5.3-Flash`，并指出 Qwen 也有 Kimi K3。重新使用当前 models.env 的三组凭据只读获取 /models，全部 HTTP200。普通 Qwen 同时列出 Flash、glm-5.3、kimi-k3、kimi/kimi-k3、kimi-k2.7-code、kimi/kimi-k2.7-code、deepseek-v4-flash 和 deepseek-v4-flash-0731；Token Plan 列出 glm-5.3、deepseek-v4-flash-0731，未列出 Flash 或 K3；Kimi 原厂列出 kimi-k3、kimi-k2.7-code。因此“Qwen 没有 K3”不成立，普通 API 与 Token Plan 必须分开表述。原件在 runs/iteration14/dx-resume-20261002/model-matrix-recheck/readback.json 和各供应商目录响应。

本次核对时的配方为 Flash→普通 Qwen、GLM-5.3/内部 DeepSeek0731→Token Plan、advisor→Kimi 原厂；I13 Flash/GitHub advisor 保留 K2.7-Code，I14 advisor 为 K3。此次是矩阵核对，不能据目录可用性自动修改运行供应商。普通 Qwen Flash 已由恢复 owner 以冻结 key 和精确 ID 直接 POST 得到 HTTP200，23 tokens；官网 Pi 装配路径的 HTTP400 继续由该 owner 修复，不能再归因为产品未开通。

## 普通 Qwen 免费额度路由修正

用户明确：“GLM-5.3、K3 也用普通 Qwen，因为各自有 1M 的免费额度”。这是未来冻结与热恢复配方的开工授权。GLM-5.3 使用普通 Qwen 的 `glm-5.3`，K3 使用普通 Qwen 的 `kimi-k3`，与 Flash 的 `ZHIPU/GLM-5.3-Flash` 共同使用 QWEN_BASE_URL / QWEN_API_KEY。内部 DeepSeek 仍用 Token Plan 的 `deepseek-v4-flash-0731`。各模型 1M 免费额度为用户提供的账户事实，尚未独立查询余额。

I13 Flash/GitHub 当前 advisor 是 K2.7-Code，继续 Kimi 原厂；不因本条涉及 K3 而修改 K2.7 或重复启动官网运行。增量已交原恢复 owner，当前 Pi 请求修复继续由它负责。I14 尚未冻结的新配方采用本节决定，历史冻结包与目录证据保持原件。

## 新运行监控消费接线

沿用既有 `i13-i14` heartbeat / 原 Luna 会话，已追加 I14 新入口与配方覆盖：只消费 `runs/iteration14/dx-resume-20261002/monitor-index.json` 及 `monitor-binding.json` 声明的冻结 Lab monitor 接口；文件尚不存在时明确未绑定，不扫描或沿旧 dispatcher 推断新运行。自动化当前 ACTIVE，按本轮用户 AGENTS 每十分钟运行，保留 I13 原范围，未创建第二自动化或采集器。三项和两 fresh baseline 的精确 monitor 绑定已发布；具体运行成功仍以回执为准。此前保留二十分钟的配置已被本轮决定覆盖。

## 本轮实际准备反馈

启动 owner 的独立原件归 `runs/iteration14/dx-launch-20261002/`。旧 reviewer 已受控停止并完整复制；仅其专属 accessor 停止，唯一 HTTP 服务和 baseline 保持。cleaner/reviewer writer 退役原件中的 unknown 经新 `ps` 观察确认为僵尸 Z，保留两种观察，不唤醒共享 dispatcher回收。旧 Docker 来源已通过新公开导入，固定原 source_run_id、daemon、完整容器 ID、Created/StartedAt、image 与 labels，并在新 launch 回读原 WSL 身份和退出状态，不伪造 attempt_id。

e2e 首次断网准备在模型调用前因包清单/校验器对 `__pycache__` 的规则不一致被拒绝，原 ZIP 与错误保留，打包过滤已修正。canonical e2e 配置改为独立 E2E_MODEL/E2E_BASE_URL/E2E_API_KEY，wire ID 显式使用普通 Qwen Flash；重新冻结和实际 runner 读回由启动 owner完成。

当前正补齐 canonical `--execute-prepared` 执行边界：同一 prepared 工作区不重复解压/刷新，复用原环境、通知锁及执行收尾；当前冻结凭据/路由、runtime image_id/python_sha256 和 `recovered-application` 输出须一致。独立 advisor 已只读复核此方案并给出真实 driver 缺口，worker继续拥有必要修复与 Linux 实际反馈。以上不代表三项生成已经运行或供应商响应成功，实际结果以新执行身份与回执为准。

用户进一步要求记录启动卡点，逐项原错、根因、修复与真实反馈归[启动卡点](startup-blockers.md)。记录由主线维护，启动 owner 持续回报重要新错误及证据入口，不为记录另开采集或停止执行。

## 并行新 baseline 范围（已核对人类指示）

只读核对 `I13 Flash/GitHub：内存修复后官网热恢复` 会话最新用户原话：“所以请你直接使用I14-baseline运行GitHub题，有两个variant：glm-5.3-flash和glm-5.3（因为之前I13的glm-5.3 variant没有结果）”。该会话持有两组干净起点 baseline 的唯一执行责任，权威入口为 `tasks/iteration14/baseline-roots/packet.md`，两组采用新版允许需求9480921。它不恢复或清理旧 baseline 暂停现场，也不替代本会话三项执行。

本会话继续 cleaner/reviewer/e2e，沿本轮原冻结需求及保留进度；两线需求版本不同，结果不能不加条件地合并成同需求对照。共同 development-2 的五槽准入保持唯一权威，launch_pending/上传中的派发窗口也必须计入实际协调；不能据当前空 ps 宣称无在途。本会话 worker将发布 `runs/iteration14/dx-resume-20261002/launch-handoff.json`，包含当前在途身份和已冻结可复用 runtime/Braid 证据，供另一个 owner读取，不重复派发 baseline。

监控间隔按本轮用户 AGENTS 的明确每十分钟要求已修正为十分钟，覆盖此前保留历史二十分钟的接续记录。仍仅更新既有 i13-i14 heartbeat，保留唯一监控会话；追加了由另一 owner 发布的两组 fresh baseline 的真实 index/binding 消费合同，不据合同存在声称已绑定。

新生成的存储根改为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002`。原因是 WorkSSD 约 11GiB 不满足实际 attempt 12GiB reserve，新 e2e 在 Docker准入前被拒绝；系统盘当时约51GiB可用。原始错误与所有已有现场保留，稳定 monitor/index、binding、launch-handoff 仍在 runs/iteration14/dx-resume-20261002 引用实际绝对路径，不改写旧实验目录身份。

存储路径纠正：此前候选 `/Users/lanzhijiang/Development/factory26-i14-runs/20261002` 经 resolve发现仍经链接落到WorkSSD，第二次reserve拒绝原件保留。实际新根为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002`，df确认/dev/disk3s5约51GiB；不能据/Users路径名宣称迁移成功。

e2e已取得实际native成功，入口为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/e2e-native-activity.json`：attempt-482e5780ca417e6ebb63e28b / Braid20261002-105607-3c89d659，普通Qwen Flash精确wireID，10条assistant及后续toolUse无error，sample新鲜约0.93秒、2GiB cgroup、Pi AS unlimited。仅此项已证明模型运行；cleaner/reviewer的新恢复准备与启动继续由原owner完成，未把它们标成成功。

监控已绑定并经主线公开只读查询：约定monitor-index.json/monitor-binding.json记录三项精确冻结launcher/source/controller/attempt，主线monitor-primary-readback.json显示e2e生成running，cleaner/reviewer为prepare running；无新的采集器或live请求。正式模型成功目前只确认e2e。

本轮槽位口径已按实际冻结代码纠正：Factory过滤标签下slots=5为五Factory执行槽，Redis不计入；此前四槽说明撤回，见host.md与启动卡点中的源码SHA。保持原五槽配置与Redis原状态。

两freshbaseline真实绑定已按active-bindings.json接入唯一heartbeat，只消费其targets的frozen monitor接口和attempt_scope，排除旧blocked源作为当前matrix。cleaner公共prepared产物已published且entry0/gaps空；其大terminal archive尚pending，原owner输运sealed named产物后正常启动，不重prepare。reviewer精确构建工具修复需其独立新prepare回执。

cleaner named prepared 已完成两端输运（660.924秒、exit0）并通过公共 verify，生成已 compile/build/start accepted；尚待模型实际响应。reviewer node-gyp 新 prepare 同 attempt ef630a2f 在 reserve 前 physical inspect60秒超时，需显式公共 pre-reserve 接续入口；独立 advisor 已裁决其锁、完整身份/authority 无reservation与无执行对象证明、保留unknown/错误和冻结runtime边界。原owner继续必要修复与实际启动，详细错误与拒绝条件归启动卡点记录。

reviewer node-gyp prepare entry已exit0、完整checkpoint读回，Git/native核验由原owner完成；整域export本机至少缺15.06GiB（T/A均增长下限）。仅停止出生已核本源controller PID485的本机输运，远端entry/archive与原件继续保全；sealed named prepared独立输运可继续。cleaner同CID1800秒input上传在途。具体量值/原错和后续空间计划归启动卡点及reviewer-nodegyp-storage-hold.json，不降低reserve。

并行baseline owner报告用户新要求修复Exp Console显示及加载。该owner持8765只读接入：Mac稳定Console，绑定原development2 container的daemon/fullID/birth/labels/binary，不暂停重启生成或新采集。三项owner仅在共享handoff补实际state/Braidrun/binary入口，prepare/failed/未产生state不得登记生成running；本会话不改8765或另起Console，没有Console源在途writer。

Console交接已发布于稳定launch-handoff.json及monitor-binding.json的console_sources。当前可接e2e实际run20261002-105607-3c89d659，state `/workspace/template/.factory26/20261002-105607-3c89d659/braid-state`，binary `/workspace/submission/runtime/bin/braid`（SHA63fdabce78498bf6164df846308d05c11f640cd844c544f561507d1df82f7e8d），有完整daemon/cid/Created/StartedAt/image/labels。cleaner/reviewer当前available=false，仅planned_state。本owner无Console writer/在途操作；8765仍归另一owner，直接读取共享文件接续。

Console owner可直接采用的绝对交接文件：`/Volumes/WorkSSD/Development/factory26/runs/iteration14/dx-resume-20261002/launch-handoff.json` 与 `/Volumes/WorkSSD/Development/factory26/runs/iteration14/dx-resume-20261002/monitor-binding.json` 的 `console_sources`。e2e可接；cleaner/reviewer未有实际Braid状态不登记。另owner报告Mac稳定Console及两baselineHTTP已可读，最终界面证据归其原件。

e2e范围收窄后主线执行一次冻结公共monitor只读查询（e2e-scope-monitor-readback.json）：controller alive/running，generate attempt-482e5780ca417e6ebb63e28b execution running/errors[]；评价正确等待生成终态和application/application-receipt，尚无成绩。该接口为已保存runner事实，不据errors[]排除native层未汇总错误。原owner沿现有摘要定向核另一baseline报告的modelScope问题，不预先重启或篡改e2e冻结输入。

两项暂停已闭合，集中原件 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/cleaner-reviewer-user-pause-local.json`。cleaner confirm工具PID66617及controller17020已关闭，未进入绑定，resource-start/confirmation/launch均不存在；同CID a3e6... StartedAt12:12:54.911579424Z但无entry/Braid，公共pause applied、Paused=true，未补marker。reviewer entry0/complete检查点、7仓Git与3native读回及sealedartifact保留，controller此前已closed，新transfer/generate未开始，原远端archive不动。COW去重尚未执行，失败半成品及原错保留。stable index现仅e2e，两暂停项binding为userpaused/advance_authorized=false。

e2e版本身份纠正：实际work/bin/braid与e2e-resource-final.zip冻结file均e002edb848...；旧manifest.sources采用63fdab声明矛盾，原件和错误声明保留，不声称63版已部署。Console交接按实际冻结file+work/bin路径修正并显式披露；是否热部署由实际行为/必要约束证据裁决，当前不预先重启。详细原件归e2e-actual-braid-exe.json及启动卡点。

版本裁决：独立advisor核对I14总packet既有用户要求“明确OOM缺陷修复覆盖全部Braid variant，新制品和热恢复绑定修复编译身份”。该约束未撤销，当前e2e旧e002文件身份不能凭无OOM视作满足要求。原owner继续必要e2e热部署：先保全原attempt和版本，核Git/Braid/native同一恢复时点的最近完整检查点，沿公共门控重新冻结修复binary并读回真实进程采用；不得改旧manifest或仅替换文件伪称升级。兼容/完整恢复前提不满足时保留现场明确阻塞，两暂停项不动。

e2e必要共用修复热恢复已进入受控保全：公共pause applied于原attempt482e/cidaecd，Paused=true/Pid1483835、原StartedAt10:55:35Z；回执e2e-oom-source-pause.json。先保持原源paused完成Git/Braid/native一致现场保全，再经公共门控恢复63fd修复版本；当前不把旧原源stop或视作结果。稳定handoff/Console来源应显示paused/待热恢复，cleaner/reviewer用户暂停保持。

e2e旧源公共stop已confirmed：exited/Pid0、Paused=false/Restarting=false、FinishedAt12:42:18.2636Z；原attempt/CID/volume保留，原件e2e-oom-stop-evidence.json。同cgroup所有writer暂停时完整快照封装workspace.zip，84,819 entries/491,412,908bytes/SHA04a7dc...，选择停止前最近同点现场，无主动弃置有效进度；完整Git/native须公共checkpoint核验。新包正在冻结actual linux-fix63，build/source/binary三份SHA核验，不据冻结过程称新运行成功。

全实验暂停回执已采用：系统盘all-experiments-user-pause-20261002.json核本会话N/P共11个controller精确出生身份均lost（原e2e30186亦blocked/lost），无活owner/dispatcher/评价，无新e2e prepare/恢复/评价attempt，无在途本机操作。cleaner实时Paused=true，旧e2e及reviewer实时exited/Pid0；原源、检查点、半成品全部保留。真实63base已冻结，新恢复package因 `KeyError: template/requirements/requirements.yaml` 退出1（fresh driver需求置template外），原stderr与半成品保留，暂停后未补输入、未prepare。待用户明确新恢复指令后再处理此具体卡点，不自动接续。
