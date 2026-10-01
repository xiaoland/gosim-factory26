# e20261001-01：I13 首轮实验

当前状态（2026-10-01 17:15 CST核对）：GLM/Sheet已在WSL真实启动，17:13:14起网关已记录实际GLM-5.3请求完成；另外三项仍在恢复准备。原运行均已停止并保全，尚无有效应用评分。当前为官网Flash两项、自有API本地GLM两项。移除DeepSeek Braid成员，内部DeepSeek sub-agent保留；不建立永久的PR模型限定。

## 启动以来的工作树

```text
I13 / e20261001-01
├─ I13主体改造［源码与材料完成；整体收益待本轮实验］
│  └─ CLI、上下文、sub-agent、SVC、协作/需求树、提示词、工具、存储生命周期
├─ 四个逻辑运行［已启动1项；另3项准备中］
│  ├─ Flash/GitHub → 官网接续［优先；未启动］
│  │  └─ 成员迁移实际反馈、诊断入口独立复核通过；最终包实际验证和启动待完成
│  ├─ Flash/Sheet → 官网接续［未启动］
│  │  └─ 本地一致快照已保全；复用恢复入口，完成反向路径兼容与最终包
│  ├─ GLM/GitHub → WSL接续［未启动］
│  │  └─ 旧原生会话切自有网关的显式接口已写；待稳定版验证/冻结
│  └─ GLM/Sheet → WSL干净启动［17:12:39容器已运行］
│     └─ 实际GLM-5.3模型请求已成功；应用语义进展由后续原生证据判断
├─ 模型与费用［配置确定］
│  ├─ 官网：不勾选使用比赛额度评测、不上榜；官方ARC地址 + 自有key
│  ├─ 本地：自有API；GLM→Bigmodel，K3→Kimi，内部DS Flash→Qwen
│  └─ DeepSeek Braid成员已移除；旧在途工作保留身份、显式迁至GLM
├─ 官网SIGKILL诊断与恢复［官网启动前置］
│  ├─ 资源/cgroup/进程及自身信号记录［完成，真实Linux操作验证］
│  ├─ 统一Linux Braid构建［完成］
│  ├─ 新旧attempt证据隔离、启动/wait接线［源码独立复核通过；最终包实际验证待完成］
│  ├─ ZIP导出/原件保全/权限与路径恢复［基础能力完成］
│  ├─ 自动恢复［方案完成，未实现/未开启收费重试；建议每来源至多1次］
│  └─ 历史SIGKILL来源［未知］；没有WSL同类故障事实
└─ 配套设施与知识
   ├─ Exp Console［唯一实例；新本地两个固定目录已纳入接入范围］
   ├─ 自有API网关［已运行；绑定200、撤销401，未发额外付费探测］
   ├─ Luna独立监控会话 + automation［已建立；新运行证据逐项接入］
   ├─ 参赛须知durable docs［完成，PDF/规则/PRD/索引已提交］
   └─ 原失败/暂停现场［已保全］；本轮尚无有效应用评分
```

本地Sheet真实身份：experiment `exp-20261001-171054-581f65`，run `glm-root--hackathon--sheet-45bf2d21de2ec4`；容器 `arcbench-local-1bcf230cc22d`，4 GiB/2 CPU、bridge、1000:1000，读回running且未暂停。包SHA256为 `a0a42a42955e755179cf9086950de2ad010023154043ab7e5951cd7e0ae5d5b9`，来源见 `runs/iteration13/local-self-funded-20261001/sheet-start-readback.json` 与 `sheet-clean-receipt.json`。运行负责人随后核对实际网关日志：17:13:14 CST首个 `glm-5.3` 请求完成，第二请求也完成；两者归该run的独立binding，参数保持high/thinking配方，未发送额外付费探测。本地两题使用同批下独立冻结的 `sheet/`、`github/` 实验，因为既有lab冻结后不能追加job；共同experiment_key为 `e20261001-01`、batch为 `local-self-funded-20261001`，本地总并行上限2。

不再执行的分支：WSL宿主SIGKILL追踪已撤回；第二个Console HTTP已退役；原两槽位矩阵已停止；单项g03及四项全本地新矩阵均未启动，现由两官网、两本地取代。旧Debian恢复与I12不在范围内。旧官网run保持终态，新官网恢复使用新身份并明确来源。

用户授权原话：“优先处理让 flash/github 恢复，并且是恢复到官网；flash/sheet也放到官网运行；都不参加比赛，使用 ARC API”；“前提是做好了收集/采集更多（关键的）帮助排查 SIGKILL 根本原因的工作”；“glm/* 留在本地运行，并且使用我们自己的 bigmodel, kimi, ds, qwen 等 API”。这覆盖此前“全部ARC、全部本地、官网诊断不阻塞”的安排。官网两项拟采用 self_funded 凭据模式并提供ARC API通道，最终以冻结输入及平台读回核对，不把比赛task名称当参赛模式证据。自有API凭据只从私有文件注入，模型ID与endpoint对应关系先验证。

用户另要求“看看能否加入自动尝试恢复的机制”。当前授权包括调查、设计与实现准备，未冻结自动收费重试次数或费用上限；不据此无限重试。优先复用现有monitor、competition journal和恢复打包，先定义SIGKILL/终态判据、完整保全、同run核查及pending写请求处理，再确定自动启动边界。隐藏评测反馈仍不进入生成Agent。

用户已澄清：“不参加比赛”指提交时不勾选“使用比赛额度评测”，使用官方 ARC API 地址和我们自己的 API key，而不是比赛 key。继续使用原 competition 题库，显式 `credential_mode=self_funded` 并关闭比赛额度许可；用户确认不勾选即不上榜，不要求另换题库。此前主线将费用选择扩大成排行榜排除要求是误解，相关启动等待已撤销。统一 Linux Braid SHA256 为 `a8afac46d2a8268dc3e7e163e673220216caaeee892b6d3af01c743b70144414`，标准源码树 SHA256 为 `088d94e5eb89bf8b1332414088fee621e2cf9879ca21f99151a1569f874e361c`。恢复入口需将导入的 `process-evidence` 与本次 attempt 分离，记录本次 Braid 启动和 wait；旧 SIGKILL 不得触发本次自动恢复。

分工：官网恢复子Agent持有两个包和journal准备；诊断子Agent持有采集就绪与自动恢复方案；目录/本地子Agent持有统一Braid构建、GLM自有通道和本地两项准备。子Agent之间直接交接具体制品，主线整合当前决策、发布前置、实际启动与结果，不逐项代做执行细节。

### 当前配方调整授权

用户原话：“不要再用 DeepSeek 作为 PR 的可分派模型（也就是说可以继续在 sub-agent 中使用，但不能作为 Braid Agent）”；“就在这次 I13，我希望现在的这次实验就可以应用”；“我们应该可以支撑4个并行”。当前迁移暂用剩余的 GLM-5.3-Flash 成员，不将其设为永久PR模型限制；两个 case 的根模型、advisor 和内部角色配方保持不变。四项实际进入新配方的时间、来源与新执行身份需分别记录，先前 DeepSeek 产生的历史进度不改写为 GLM 产出。旧冻结包和原尝试保留。

当前运行的 Braid 将成员配置读入内存，offline-resume 又检查原配方一致性，不能靠修改源码文件就宣称已应用。主线正核对受审计的迁移与一致工作区保全，避免丢弃正在写入的 PR。四并发沿用每容器4 GiB/2 CPU；实际容量检查约12.4 GiB可用内存、451 GiB磁盘，两条生成容器当前分别约1.0 GiB和0.7 GiB。这是此前全本地四槽位准备的容量依据；最新安排只在本地运行GLM两项。

两条live已通过唯一 Console 的写者门闩与 Docker pause 保全。完整 template ZIP 在复制前后均确认同一容器处于暂停状态，包含 clone 私有 Git、未提交文件、Braid SQLite/WAL 和原生历史；Mac副本SHA一致、SQLite quick_check均为ok。Flash/Sheet快照SHA `1158466fe93bada0007be4b5735f8ded2ab344c75731bc9df702886fe8a3eb4d`，GLM/GitHub为 `e207e502f10203e98abff1aa78dc9cb2479ac3358cc0a232e286b8704d4215a4`，回执归 `runs/iteration13/local-20261001/model-cutover/`。旧控制器先降一槽位禁止旧配方队列混启，保全后通过操作 `69a1a4e4aaf227e059ae9329` 停止。独立读回确认controller finished、两个原容器已移除；两条生成为计划内cancelled，GLM/Sheet未开始即取消。这不是新的运行故障。原四槽位新矩阵未启动，现改为官网两项与本地两项。

迁移保留原profile ID、member、assignment、worktree和Pi session，旧DeepSeek执行profile改用GLM并撤出新指派目录；新指派只使用现有pi-glm-fast。旧目录按摘要revision的数值最大项选择，无法可靠表达当前配置；现已修为读取冻结request中的当前目录，并通过真实允许/拒绝指派操作验证，历史profiles不改。旧Pi home在factory26下没有GLM定义，需定向补入同款GLM定义，保留内部角色和DeepSeek sub-agent。两个request的旧原件与变更回执单独保存；不放宽普通offline-resume的一致性检查。此前拟建 `e20261001-01-glm-pr-20261001` 与单项 `recovery-g03` 均未执行，现由两官网、两本地的新journal取代。

## 首轮 WSL 启动范围（已停止）

授权原话：“改进这个实验的基础设施，让这种信号的来源能够被捕捉到”，以及“现在 WSL 已经恢复了，让我们启动4个运行吧（glm-5.3-flash--github的可以接续）”。本批沿用下文两组模型配方、ARC 模型额度及逐题官网 self_funded 应用重放；并发上限2、每容器4 GiB/2 CPU，先启动两项 GitHub，再由空闲槽位启动 Sheet。没有新增官网 Harness 生成。

| 运行名 | 起点 |
| --- | --- |
| `e20261001-01--flash-root--github--g02` | 从官网 `346bc3b51b09` 的稳定终态副本重建接续，Braid run `20261001-052115-e45f4278`。 |
| `e20261001-01--glm-root--github--g01` | 原冻结 GLM/K3 包，干净生成。 |
| `e20261001-01--flash-root--sheet--g01` | 原冻结 Flash/K2.7 Code 包，干净生成。 |
| `e20261001-01--glm-root--sheet--g01` | 原冻结 GLM/K3 包，干净生成。 |

Flash/GitHub 来源 ZIP SHA256 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd`；其需求 SHA256 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f` 与本地 GitHub 输入一致。旧进程已经终止，SQLite/WAL 可一致读取，六个 Braid 物理会话和三个 child 原生文件均已保全。平台遗漏各 clone 私有 `.git`；恢复入口从发布 ref 重建索引并保留文件，再走 Braid offline-resume 撤销失效执行身份。私有 HEAD、未发布历史与原索引无法证明恢复；这是有来源的重建接续，不是完整原子检查点。较早运行中 ZIP 同样不完整且会丢有效文件进度，故采用稳定终态副本。详见[失败调查](hosted-github-failure.md)。

本批证据目录 `runs/iteration13/local-20261001/`。用户已明确 SIGKILL 只出现在官网，WSL 从未发生。此前把宿主取证列为本批启动前置的方案已撤回；没有部署或启用 WSL collector，没有执行信号/OOM验证。官网可得的 cgroup、进程、退出证据与平台接口另行调查，不阻塞本批 WSL 生成。单实例 Console 接入按用户最新要求核对，不启动第二个服务实例。

已恢复宿主 `factory26-i13-wsl`、Docker daemon `a76759eb-0145-45f3-be55-ed98b48ef91f`、稳定 Python 与旧资产身份均重新核验；宿主约15.59 GiB内存、4 GiB swap、465 GiB可用磁盘支持原定两路并发。schema v3保留52 GiB host reserve、每run24 GiB workspace/4 GiB telemetry/8 GiB finalization scratch及12 GiB build，最终以启动时容量预检为准。四项模型、题目、制品与实际 ID 在启动回执中冻结；隐藏评测结果不进入仍在生成的 Agent。

### 本地启动与恢复设施错误

15:42 CST 已一次性启动冻结矩阵 `/home/yyh/factory26/experiments/e20261001-01-local-20261001`，controller `controller-bcfe252ace2f`、PID3563。镜像为 `sha256:c5d3e2765a92d26093257ffa0363094f4aff502e37d5fa4dc59d1435127b3225`；启动容量预检通过，所需136 GiB、当时可用约463 GiB。四项 allocation 如下；准确记录由 `runs/iteration13/local-20261001/active-matrix.json` 关联。

| 配置 / 题目 | lab run 后缀 | 首次启动反馈 |
| --- | --- | --- |
| Flash / GitHub | `4afc8896760859` | 15:44:08 恢复入口退出1，尚未启动 Pi；完整失败现场已封存。 |
| GLM / GitHub | `00bf489759b139` | Braid `20261001-074336-af6f78cd`，15:44:07 Pi 握手完成，实际阅读需求并开展工作。 |
| Flash / Sheet | `f893bdb3298d69` | 前一槽位释放后启动，Braid `20261001-074506-6e7af22b`，实际委派视觉分析。 |
| GLM / Sheet | `2cf88b952f231c` | 已分配，等待原控制器的空闲槽位。 |

Flash/GitHub 首个恢复包 SHA256 `96302a70c4df8fb65472de9b3e156fb2af944dd6eb3f3701e339c55f6b75bf06` 的24214项载荷均核验一致，但实际部署暴露恢复设施缺口：官网 ZIP 将声明的启动器保存为0600，Braid `SessionFactory::check` 的 `which::which` 因不可执行返回 `session is unavailable`；四个 provider 组均未进入 Pi 启动。进一步核对确认，官网旧绝对包路径是 `/workspace/submission/runtime`，本地 adapter 的真实包位置是 `/workspace/submission/agent/runtime`。修复限定于已声明启动器权限和已知包装层的路径别名，不改模型配方、技能或原生历史。该错误不是 SIGKILL，也不是应用有效零分。

原始 `recovery-braid.log` 与入口 traceback 保存在本地 `preparation/flash-github-recovery-{braid,error}.log`；包含 Git/Braid/native 的完整失败现场归档266006235 bytes、SHA256 `eae5dcb74312935f13746b4e64505661808afa20ac650e57d287bc1190b404d8`，远端和Mac一致。Meter baseline 另报宿主 DNS `Errno -3`，仅作为 Meter 证据缺口，不替代实际恢复退出原因。其它干净运行继续，未为恢复问题重启它们。

用户随后要求把反复手工导出、组包与权限处理自动化，纳入实验设施改进。主线正在通过本次真实导出实现和验证一条可重复命令；修复后的接续会登记新包/执行身份并保持总并发不超过2，不覆盖失败尝试。

后台 `monitor-local.py` 以3+8间隔保存定向状态和会话片段，复用 Luna/low 内容审查；`follow-batch.py` 通过 `lab.wait` 取得终态并逐题执行既定应用重放。两者的PID/入口归 `background-launch.json`、`monitor-restart.json`。初始两批审查误把恢复目录里的官网历史当成本次进展，已撤销其结论；采集已补充本次 `experiment-result.json`、退出码和 `recovery-braid.log` 必读，主线以原始错误独立纠正。独立[实验监控会话](codex://threads/01a0f613-082a-7251-a25f-e99acbc37706)及 `i13-wsl` heartbeat 消费已有结果，不另行平行轮询。旧官网监控保持终止。

2026-10-01 用户在审阅最终检查结果后明确：“好的，可以启动 I13 了。”本轮承接两组根配方各生成 GitHub、Sheet 一次，共四次新生成的建议，授权必要的根对照实现、最终材料冻结、独立干净宿主建立、本地生成、Console 人工介入与逐题官网应用重放。I12 已结束，仅保留其归档；当时无法挂载的旧 Debian VHDX 和冷备不进入恢复范围。

## 首次官网启动范围（已结束）

运行名 `e20261001-01--flash-root--github--g01`；Competition 为 `hackathon`，task 为 `hackathon--github`。使用官网本次提供的原始需求，不向 Agent 提供本地或隐藏评测内容。模型仍是根 `glm-5.3-flash/high`、advisor `kimi-k2.7-code`、视觉 `glm-5.3-flash`，全部走 ARC。

复用冻结包 `runs/iteration13/start-20261001/artifacts/pi-braid-i13-k27.zip`（393332574 bytes），SHA256 `afca9654b10544851885c748060d7d283b2d40b0890363f6acfb9a2dfe677877`；新 journal 为 `runs/iteration13/hosted-20261001/github/`，显式冻结 `credential_mode=official_evaluation` 与 `allow_competition_credit=true`。本次不提供个人模型 key；平台实际返回的 billing_mode 另行保存，不能仅凭请求模式宣称已确认计费。

既有 RUN_CONDITIONS 中“人工介入研究运行”标签与新场所不一致，但后文仅允许通过对象评论接收输入，并要求自行处理常规歧义，没有等待人工的条件。独立 advisor 建议复用本包，避免仅因标签改变已冻结制品；保留此解释限制，真实自主运行以本次证据判断。

先冻结新 journal，再依次上传 snapshot、创建单题 run、启动；POST 回执不明时先用同 journal 只读恢复核对。已有3+8程序负责状态、工作区证据采集及 GPT-5.6-Luna/low 定向语义审查；终态收集官方结果后停止轮询。仅运行此一次，不自动增加收费尝试、恢复旧运行或启动其它题目。官网生成、部署和评分属于同一次正式 run，无另行应用重放。


### 官网启动回执

2026-10-01 13:20:59 CST 启动；submission `d0692dd35545`，run [`346bc3b51b09`](https://arc-bench.com/runs/346bc3b51b09)。官网已完成环境部署并进入生成阶段；首批13:21:10的状态为 RUNNING，评测尚未开始。

官网保存的 submission 已核实 `credential_mode=official_evaluation`；本次未提供个人模型 key。run 返回 `billing_mode=self_funded`，两者不一致，与既有平台记录的差异相同。原始 submission history、status 与启动摘要均保留在新证据目录；实际费用归属不能仅凭其中一个字段断言，后续继续核对。

### 官网终态（2026-10-01 15:04 CST）

run `346bc3b51b09` 已终止，状态为 `FAILED`，发生在生成阶段，未进入官方评测：`deploy_agent=completed`、`start_agent=failed`、`run_tests=pending`、`evaluation_started_at=null`。官网记录的分数为 `0.0`，通过/失败测试数均为 `0`，因此这不是一次有效的应用评分。

终态回执记录：开始 `2026-10-01T05:20:59.107371Z`，结束 `2026-10-01T06:50:48.440272Z`，持续 `5335` 秒；token `58165820`，费用 `13.328865 CNY`，`billing_mode=self_funded`。submission 仍为 `credential_mode=official_evaluation`，二者差异保留，不能仅凭字段断言实际费用归属。

官网 failure_reason 仅报告 `main.py` 非零退出；随后子Agent在原始官网日志 `github/tasks/hackathon--github/logs/03436d68fef7e8d8.json` 找到14:50:04 CST的完整traceback，主线已直接核对。`run.py:321` 因Braid exit=1抛错，result.reason为 `native teardown could not be proven: session failed: Pi exited with signal: 9 (SIGKILL)`。直接退出链已确认，SIGKILL来源及被杀会话仍在调查，不能据此断言OOM或平台限制。此前PR中的Node版本错误也不能直接当成本次全局终止原因；未自动恢复或重跑。

现场保全回执：15:07:02—15:07:58 CST新鲜GET工作区成功（HTTP200），原始ZIP277814542 bytes、27768项、CRC逐项通过；SHA256 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd`，主线独立重新计算一致。文件清单确认包含需求、worktrees、origin.git、Braid sqlite/WAL/SHM、native-homes与原生归档；原件及下载/完整性回执在 `runs/iteration13/hosted-20261001/failure-investigation/20261001T070702.797343Z/`。后续status/log/traceability GET返回HTTP500（Internal Server Error），错误原文保留；此前已成功采集的终态原件仍在，不能将本次取证API错误推定为此前运行退出原因。Git/Braid/会话是否形成可直接恢复的完整一致检查点仍在核对。

完整终态证据入口：`runs/iteration13/hosted-20261001/completion.json` 与 `runs/iteration13/hosted-20261001/monitor/20261001T065751.899359Z/346bc3b51b09/`；独立监控已完成采集，未重发请求、未启动第二次收费尝试。用户随后明确要求“安排sub-agent保留工作区并且排查证据”。已委派 `/root/i13_hosted_failure_evidence`（GPT-6.1-Sol / extra-high）下载并核验官网可得工作区与日志、保留Git/未提交worktree/Braid数据库和会话、核对终止因果与恢复一致性。独立输出归 `failure-investigation/` 与 `tasks/iteration13/hosted-github-failure.md`；当前无重跑或源码修复动作。

Mac 后台协调进程46943、3+8采集进程46944已经启动，使用 `lab.arc_bench.hosted_monitor --review` 与独立 `agents/run-monitor.md`（GPT-5.6-Luna/low）。首批实际状态与归档读取成功，归档当时仅含需求，尚无原生会话，因此只能证明平台启动阶段，不能证明模型已开始有效开发。第一次内容审查已结束；主线已消费其引用并保留此证据缺口。终态由 `follow-hosted.py` 收集 status、logs、traceability 与 Git history。heartbeat `i13-github` 每8分钟消费已有监控结果，仅在故障、完成或需要决定时通知；现已按用户要求迁入独立[GPT-5.6-Luna监控会话](codex://threads/01a0f613-082a-7251-a25f-e99acbc37706)（low），主开发会话不再定时唤醒。

第二批13:24:58 CST已取得Braid与原生会话，主线直接读取确认：根Issue #1开放且有1个活跃turn，根Agent已检查应用仓库与Node环境，启动应用依赖安装（30秒后自动进入bg001），并于13:24:42调用vision子Agent分析12张需求参考图。这证明模型和实际工具链已开始工作；应用实现、最终覆盖、advisor调用与评分仍待后续证据。

13:34批次的原生证据确认：根Agent提交设计资料、创建基础PR #2并指派DeepSeek；DeepSeek已读取需求与设计。根曾误用comment --message，随后读help改用body-file并成功发布评论，属于已自行恢复的调用错误。监控旧逻辑按文件名字典序选中advisor/vision旧子会话，审查因此错误关联到Issue/PR；主线已直接读取两条当前Braid原生会话纠正。监控现按physical_sessions的原生路径生成带工作项/profile身份的session_evidence，当前两条会话均进入必读列表；实际归档读回及Python编译通过。仅重启Mac监控（协调PID53789，当前采集PID53790），保留同一run与下一次采集时点，官网生成未中断。回执为 `monitor-session-selection-readback.json`、`monitor-restart-session-mapping.json`；13:44既定采集已实际返回正确的session_evidence映射，关联文件均存在。

监控会话移交：用户明确要求创建GPT-5.6-Luna独立会话并将automation迁入。已创建 `01a0f613-082a-7251-a25f-e99acbc37706`，将现有 `i13-github` 的target_thread_id从主开发会话改到该会话，保持原8分钟频率；现有3+8后台采集及官网run均未重启。原始配置读回在 `monitor-thread-handoff.json`。后续日常监控与终态通知由该会话负责。

回执入口为 `runs/iteration13/hosted-20261001/launch-summary.json`、`submission-history-after.json`、`monitor-launch.json` 与 `monitor/`。本地WSL无新增操作，Sheet和GLM根组未启动。

## 首次冻结配方与判断目标（通道及成员已由顶部当前安排更新）

| case | variant | 根 Issue | 原生 advisor | 子 Issue / PR 与其余原生角色 |
| --- | --- | --- | --- | --- |
| flash-root | pi-braid-i13 | glm-5.3-flash / high | kimi-k2.7-code | 两个 Flash 可指派成员及其余已核定 I13 配方 |
| glm-root | pi-braid-i13-glm-root | glm-5.3 / high，root-only | kimi-k3 | 同上 |

用户最新修正为：“有一个变化，使用 K2.7 code 替代 K3”；“抱歉，GLM-5.3 组继续使用 K3”。ARC 同时提供 kimi-k2.7-code 和 highspeed 变体，本轮采用精确的 kimi-k2.7-code。这一决定同时改变根模型和 advisor，结果不能归因为单一根模型差异。其余工具、技能、共同提示词、Flash 子 Issue/PR 成员与视觉 glm-5.3-flash 保持一致；所有模型走 https://api.arc-bench.com/v1，使用用户已恢复授权的 ARC 额度。

本轮回答整体需求理解、责任交接、最终覆盖、上下文连续性与运行成本是否改善；description 重建、普通评论增量送达、深层委派、executor采用与归档恢复承诺来自真实工作证据。技能读取、对象关闭、token增长不单独证明有效行为。人工介入保留 journal，若两组介入不同，明确分析限制。

## 旧本地输入、次数与运行安排（暂停）

允许输入来自项目已保存的官方需求：`runs/wsl-retained-20260930/official-local/platform-inputs/hackathon/`。GitHub 28 个文件、Sheet 10 个文件，均已与各自 source.json 校验一致。无官方本地 tests-source；生成不接触外部测试、参考应用或历史运行产物，本地采用 requirements-only，不报告本地分数。

四次可读生成名称为 `e20261001-01--<flash-root|glm-root>--<github|sheet>--g01`。每题两组使用独立干净起点，不互相导入代码、Git或会话。并发上限2，先 GitHub 的两组，再 Sheet 的两组；每个容器 4 GiB/2 CPU。若实际容量不支持并发2，则全轮统一串行并记录原因，不扩大资源。无自动增加重复次数。

新宿主采用[独立 Debian 方案](../debian-disk-recovery/packet.md)：Debian-Factory26、独立 Docker Engine 与稳定 host-lab Python资产。只准备实际运行依赖，不安装整套开发环境。先核实新 ext4 与承载它的 Windows 卷空间、真实 bind mount、容器网络和 OTLP，随后冻结 schema v3 的空间/inode预算。当前24 GiB workspace、4 GiB telemetry、8 GiB finalization scratch是待宿主实测校准的准备值，不是已完成容量验收；host reserve至少为文件系统容量10%与最大scratch的较大值。保存所有原始错误，不自动清理历史数据。

本机 `runs/iteration13/start-20261001/` 保存准备和回执；最终 ZIP、源码、Braid、SVC、依赖及补丁身份由 `artifacts/` 的实际材料记录。根对照与Kimi替换实施归[root-comparison.md](root-comparison.md)。当前尚无模型请求；最终包和运行ID在取得后追加。

## 旧本地完成、反馈与后续边界（暂停）

每题生成完成即从准确交付版本发布应用重放包，并独立提交官网，不等待其余任务。本地生成使用 ARC 模型额度；应用重放不调用生成模型，采用既有非榜单 `self_funded` artifact-replay 入口及 no-model 凭据占位，明确记录平台实际 billing_mode。重放不是新的Harness生成，耗时和模型消耗分开记录。评分只用于开发侧结果，隐藏反馈不送给仍在生成的Agent。

lab程序保存终态和容量观测；远端无事件接口时，采集按启动后前10分钟每3分钟、此后每8分钟执行。需要语义审查时使用 agents/run-monitor.md 的 GPT-5.6-Luna / low，读取定向证据而不铺开全量rollout；程序等待不每分钟唤醒主模型。明确设施缺陷在已授权范围内保留现场、修复和接续；预算停止后另用reconcile核对外部容器。新题目、增加重复次数、改模型配方或不可逆宿主变更不由本记录默认授权。

最终每条结果关联实际lab/Braid/原生身份、包/需求/应用摘要、官网run与分数、原始错误和证据缺口。四次完成后无论分数高低先汇报，由用户决定下一轮。

## 暂停时的实际准备结果

两份包已冻结并在新WSL传输校验一致，包内全部载荷与manifest一致，工具凭据非空且私有ZIP为0600；主线读回见 `runs/iteration13/start-20261001/primary-artifact-readback.json`。组间差异仅为run中的根选择、advisor/model descriptor和根新增profile，见 `artifacts/primary-package-comparison.json`。源码提交为0149ff0、5edec2c，授权记录为b6d3ed1，均未push。

新SSH为factory26-i13-wsl；独立Docker daemon为a76759eb-0145-45f3-be55-ed98b48ef91f，29.8.2；Python为3.12.14，稳定lab资产位于 `/home/yyh/factory26/assets/host-lab-i13-20261001/asset.json`。DNS默认gateway resolver曾间歇失败；子Agent在用户暂停指示之前已仅为新发行版设置generateResolvConf=false并使用172.18.0.2，具体事实归Debian packet，后续由用户处理。

本轮实际可用空间约477GiB，承载D卷准备时约679GiB；待用配方为52GiB host reserve、每run24GiB workspace/4GiB telemetry/8GiB scratch及12GiB build，尚未执行最终schema v3容量预检。官方基础镜像已下载，包装构建在用户要求时受控停止，不能称为最终Runner构建成功。`linux-prepare.py`、`prepare-matrix.py` 和 `follow-batch.py` 均仅保留脚本，尚未运行；没有正式矩阵、run ID或模型反馈。

空Console在8766保留（WSL HTTP PID2479，Mac转发PID71228，service c5c21595-811d-4dde-b6b4-83a77cf1bbc8），8765原归档服务未变。后续接入方案归[Console启动记录](console-launch.md)；当前未导入受管理binary、未建访问容器、未登记Braid DB或后台自动接入。
