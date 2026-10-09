# I14 启动卡点

本页保留历史错误及当时操作，旧运行原件已按用户清理授权删除。下文将产物迁到系统盘的处理违反用户最新的 WorkSSD 绝对规则，已撤回，不能再次采用；应清理已获准数据或报告存储阻塞。当前决定归 [夜间 packet](../overnight-plan/packet.md)。

2026-10-02。用户要求：“启动实验的过程中，遇到的卡点，请记录下来。”本记录覆盖 cleaner、reviewer、e2e 三个 GitHub 的本轮启动；baseline 保持暂停，I13 由用户另行推进。授权、执行负责人和当前状态归 [packet](packet.md)。历史启动原件保留在 `runs/iteration14/dx-launch-20261002/`；表中未标绝对路径的历史日志相对此目录。迁移后的执行原件在 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/`，稳定交接和监控索引在 `runs/iteration14/dx-resume-20261002/`。

这里区分配置核对发现、真实执行失败和已取得的修复反馈。离线准备成功不等于模型请求成功，也不等于最终应用交付。启动过程中继续追加具体错误，不将设施故障记为应用零分。

最新范围：用户要求“暂停目前现有的所有实验，因为 API 额度即将耗尽”，已核对原会话真实userMessage，全部实验/热恢复/评价停止推进，不自动恢复。此前用户要求“暂停继续推进cleaner和reviewer；专注e2e”已被覆盖。两项现场和以下卡点保留，暂停后续修复、输运、生成和评分，e2e原生成在新指示前已停止以保全共用修复恢复点；后续恢复现也暂停。实际两项用户暂停已闭合：cleaner无模型入口、专属本机操作关闭、原容器Paused=true；reviewer完整检查点/原archive保留，未开始新transfer/generate。回执归packet、稳定handoff及系统盘cleaner-reviewer-user-pause-local.json。

暂停前状态：e2e 已有真实 Flash 模型成功响应；cleaner 的 prepared 已 complete、输运及公共 verify 成功，generate 已完成输入上传/完整读回并Docker start成功，资源绑定参数冲突使worker等待marker，正修复只确认启动的绑定边界；reviewer 的 reserve 前查询超时已通过显式公共接续门控，同 attempt 的准备入口已 exit0，完整检查点已complete/gaps空，7仓Git检查和3个native profile保全已核验；整域export至少缺15.06GiB，本机输运暂停、远端归档保留，尚无模型响应。原暂停 baseline 未恢复；另一会话获新授权的两 fresh baseline 已有各自模型成功回执。后文旧错误记录保留发生时状态，当前结论以本段及最新回执为准。

| 卡点与触发 | 原始错误或实际缺口 | 根因与处理 | 已有反馈与证据 |
| --- | --- | --- | --- |
| Controller runtime 首次使用本机默认 Python | Python 3.9.6 不满足 `opentelemetry-proto==1.44.0` 的 Python >=3.10 要求，依赖解析退出 1。 | 系统默认解释器过旧；显式选择 Python 3.12，不降低依赖版本或绕过解析。 | `controller-runtime.log:5` 保留原错；`controller-runtime-py312.log` 保存重新装配。新 runtime 已用于实际准备。 |
| e2e 工具供应商与逻辑模型混用 | 配置原先读 `FACTORY26_API_KEY` 和逻辑模型 ID，不能保证实际请求使用普通 Qwen 的 `ZHIPU/GLM-5.3-Flash`。这是装配核对发现，不是本轮已发生的供应商 HTTP 拒绝。 | 工具独立读取 `E2E_MODEL / E2E_BASE_URL / E2E_API_KEY`，必须显式提供 wire ID；不改 Braid 的逻辑模型及预算身份。 | canonical `variants/pi-braid-i14-e2e/tools/e2e.config.ts` 与 `run.py` 已修改；最终包与实际运行的供应商读回仍须分别保存。 |
| e2e 首次真实断网 prepare 的包校验 | 报“参赛包包含缺失或未登记载荷”，发生在模型调用前。 | 打包器登记了 tools 下的 `__pycache__`，校验器按既有合同忽略它；在打包器原有过滤处统一排除，保留失败 ZIP。 | 原 attempt 为 `e2e-prepare-experiment/attempts/attempt-9b889d4e4cda2c1a95dff0b4/`；修正后的 `e2e-prepare-experiment-r3` / `attempt-7a891ac90b533206b3ddb10b` 实际入口退出 0。 |
| reviewer 暂停现场不能直接当停止检查点 | 首次保全脚本报 `RuntimeError: reviewer exact paused identity changed`，随后停止与导出重新核对实际身份。 | 不凭本地旧记录操作容器；按 daemon、完整容器 ID、labels 与暂停状态核实来源后，仅停止 reviewer 容器。 | `reviewer-preserve.log:5` 保留原错；`reviewer-source/source-identity.json`、`source-stop.json` 与 `template.tar` 保存实际来源、停止及完整归档。baseline 没有解除暂停。 |
| reviewer 完整归档抽取遇到外部符号链接 | `tarfile.AbsoluteLinkError`：node-gyp 的 `python3` 链接指向绝对路径。 | 生成应用的 node_modules 含外部工具链接，默认安全抽取拒绝；保留原 tar 和链接目标文本，核对没有通过链接写入的后续子成员，再按明确边界抽取。 | `reviewer-preserve-r2.log:21` 保留原错；`reviewer-snapshot-finalize.log` 与 `reviewer-source/workspace` 保存后续处理。不能据抽取目录存在声称原 Git/native 已核验，核验由恢复证据另行给出。 |
| 旧 Docker 来源无法进入新 Lab 门控 | 旧来源没有新 `attempt_id`；旧来源分支只覆盖官网，不能合法消费 WSL 的 cleaner/reviewer。 | 在现有 legacy-source 合同增加 Docker 的只读导入与当前观察，固定真实 source_run_id、daemon、容器出生、StartedAt、image 和 labels。启动前回读原 WSL，不给旧来源伪造 attempt。 | `cleaner-legacy-source.json` / `cleaner-legacy-stop.json`、`reviewer-legacy-source.json` / `reviewer-legacy-stop.json` 已实际生产；导入不授予独立启动许可。 |
| 停止生成容器仍未关闭全部写入入口 | reviewer 专属 accessor 仍 paused 且挂载源卷可写；cleaner 导入曾报 `legacy Docker source volume users changed after writer closure`。 | 仅关闭这两个来源的专属 accessor 和 writer/restart 入口，并重新核对卷使用者；不停止共享 HTTP 服务、不清退 WSL 全域。 | `reviewer-source/accessor-stop.json` 保存退出/Pid0；`reviewer-volume-closure.json` 和 cleaner 对应 closure 保存卷用户；`cleaner-legacy-import.log:15` 保留拒绝，`cleaner-legacy-import-r2.log` 保存成功导入。 |
| 杀掉旧 worker 后身份查询仍为 unknown | Darwin 对僵尸进程不给出生信息；旧 worker PID 54127/54504 的通用 process_state 为 unknown。 | 新 `ps` 读回为 Z，不能执行；保留原 unknown 和新观察，不为回收它们 CONT 共享暂停 dispatcher。旧来源门控实时核验，活进程或身份不明时拒绝。 | `reviewer-writer-retirement.json`、`writer-retirement.log` 及后续 restart closure 保存依据；不是把所有 unknown 统一当作停止。 |
| prepared 已装配却只能走重新解压入口 | 新 runner 装配 prepared 后，旧 `recover_completed.py` 再解压会因 run 已存在而拒绝；私有 generate driver 也会重复创建 submission。 | 增加 canonical 显式 `--execute-prepared`，复用原环境、通知锁、执行和最终导出段；不重新解压、重建 Git、刷新材料或迁移需求。当前绑定与 prepared transport 不一致则重新 prepare。 | 新入口已编译；`cleaner-resume-final.zip`、`reviewer-resume-final.zip` 重新冻结。真实 Linux prepared 执行结果尚待本轮取得，不能将编译当作接续成功。 |
| 私有 driver 与公共合同的字段/输出不一致 | prepare driver 最初记录 `runtime_identity.image`，runner 要求 `image_id / python_sha256`；工作区需落到持久卷而非容器层；恢复最终产物为 `run/recovered-application`，不是 `run/application`。 | 按实际 runtime 身份与持久工作区装配，生成直接消费已装配入口，按 canonical 恢复输出发布应用。 | `recovery-prepare-entry.py` 与 `generate-entry.py` 保存当前接线；最终输出与模型执行的实际验证继续登记，不作为已完成交付。 |
| e2e 生成与自动重放意图首次编译冲突 | `ValueError: conflicting evaluation case inputs: ['requirements']`；后续 build 的 recipe 缺失是该失败的下游结果。 | 生成/评价模板重复声明的 case inputs 不一致，需统一冻结的需求输入；不在缺失 recipe 上继续 build。 | `e2e-generate-compile-final.log:15`、`e2e-generate-build-final.log:18` 保留原错；后续 `e2e-generate-experiment-final2` 已实际派发。 |
| 新 runner 接管 OTLP 后资源采样没有生产 | e2e 生成已进入 Braid，但 Issue Agent assignment 持续报 `session waiting for resources`，原因是 `resource-latest.json` 的 FileNotFoundError。没有取得供应商成功。 | 外部 runner OTLP 接收器使 Harness 跳过旧 serve_run，而旧 serve_run 同时生产 ResourceEvidence；新 Collector 未承接该采样。独立 advisor 已确认根因；在现有 runner 监管循环复用已有 ResourceEvidence，显式传样本路径，不开第二采集器或循环。采样独立于 telemetry 开关，入口前即须存在，且样本须通过新鲜度、cgroup inode 和有限 memory.max 核验。 | `e2e-live-braid.log:1` 保存 18:37:43 CST 原错；源 run 为 `20261002-103153-5ff2cceb`。旧等待现场已保全。系统盘新 e2e 的 e2e-native-activity.json 实际读回 sample age约0.93秒、memory.max2147483648、Pi AS unlimited，并保存10条成功 assistant。本项已有真实正反馈，不外推其他尚未运行组。 |
| cleaner/reviewer 实际 prepare 的链接缺口 | 入口退出 1、checkpoint partial；readback.gaps 包含恢复代码生成的绝对 materials 别名，以及旧 HOME 的 pulse runtime 临时链接。 | 材料别名指向同一个 submission，但独立副本核验时被视为外部；旧 pulse daemon 已停止，短命目标不属于恢复内容。拟将生成别名改相对路径，严格匹配格式/目标后仅移除旧 pulse symlink，保存 sanitation 回执，不修改来源完整归档或放宽外部链接门控。 | cleaner 原 attempt `attempt-51dfdaada9946607d08d295c` 的 export/artifact-store 输出 `stdout.log` 保存具体 gaps；reviewer 对应实际准备原件保留。相对材料别名与旧pulse链接处理已在cleaner的新prepare实际验收：entry0、complete、gaps空；reviewer后续仍因独立node-gyp外链partial，见对应记录。 |
| Docker 内存约束被同时用于虚拟地址上限 | 源码核对发现 internal_entry 对 Docker 同样设置 RLIMIT_AS=2GiB；本轮尚无具体 V8 失败原件。 | Docker 已用 --memory 执行 cgroup 限额，额外每进程虚拟地址约束含义不同。独立 advisor 建议将 RLIMIT_AS 条件限定为 local 后端，Docker 继续保持原 2GiB cgroup，不增加 V8 专用参数。 | 修复由 runner 稳定 owner 完成；实际启动核对 memory.max=2147483648 和 Pi 进程 limits。此项是启动前源码核对发现，不记作已发生 OOM 或 V8 错误。e2e实际回执已核对2GiB cgroup、Pi AS unlimited。 |
| prepared 入口重复应用原始包的无链接合同 | 独立 advisor 核对发现 --execute-prepared 仍先执行 verify_package(ROOT)，它拒绝任何 symlink，会拒绝合法派生的相对材料别名。 | 原始 ZIP 与已装配 prepared 是不同阶段。新模式应核对 runner 装配身份、prepared 引用和路径映射，原始包验证仍严格；不全局允许 symlink，也不临时删别名绕过。 | 源码复核发现的必达冲突，不额外运行测试或故意制造失败；启动 owner 正修复并以实际 prepared 执行验收。 |
| WorkSSD 低于实际启动存储预留 | `attempt storage reserve unavailable`；WorkSSD 约 11GiB 可用，当前 recipe 要求 12GiB。在 Docker reserve/launch 前拒绝。 | 历史包、完整归档与重复冻结占用空间，不能删除原始失败现场来伪造充足容量。新实验与新恢复包改放系统盘 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002`，当时约 51GiB 可用。 | `e2e-generate-experiment-resource/controller.json` 保存拒绝；约定 monitor/handoff 保留在原位置并引用新绝对路径。真实系统盘迁移后 e2e已启动并取得native成功响应；其他恢复组仍按各自回执验证。 |
| 存储迁移候选路径实际仍落在 WorkSSD | `/Users/lanzhijiang/Development` 是指向 WorkSSD 的链接，候选新路径 resolve 后仍在 SSD，第二次同一 reserve 拒绝发生在 Docker reserve 前。 | 不能根据 /Users 前缀推断物理文件系统；按 resolve/df 核对后，将实际新根改为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002`，确认 `/dev/disk3s5`、当时约 51GiB 可用。 | 原第二次 reserve 错误保留，launch-handoff 将发布真实根与容量；前一“迁到系统盘”的计划未实际成立，不算成功迁移。 |
| cleaner 恢复包选取了错误层级的来源目录 | 原 workspace/readback 位于 cleaner-hidden-context 父目录，打包候选指向 cleaner 子目录。 | 按真实 handoff/readback 选择完整来源，保留错误候选并重新打包；不凭目录名或半成品骨架制作检查点。 | 启动 owner 已定位并重新打包；后续cleaner完整来源的新prepare已entry0/complete/gaps空，五仓Git及完整native读回见系统盘cleaner-checkpoint-partial.json；不据此推断generate已成功。 |
| 新 prepared 仍包含 node-gyp 的镜像工具外链 | 前两项链接修复后，reviewer partial 仍报告 better-sqlite3/build/node_gyp_bins/python3 指向 /usr/bin/python3。 | 目标是构建工具，不是失踪 native 状态。独立 advisor认可仅在恢复副本中物化目标冻结镜像的真实解释器字节、保留执行权限，记录原literal link、resolved目标、实际SHA及image_id；不误用sys.executable SHA，不扩外链能力。 | 系统盘 `reviewer-checkpoint-partial.json` 保留缺口。原source snapshot、Git/native/DB不动；原partial在外链处提前返回。后续node-gyp新prepare已entry0、complete/gaps空，7仓Git检查和3个native profile完整读回见reviewer-nodegyp-checkpoint-readback.json；generate仍待实际反馈。 |

历史首次派发的 e2e 实验 `i14-e2e-github-qwen-20261002` / `attempt-c5de9727fc767ba1bae52eed` 已进入 Braid，但资源采样缺失导致成员等待，没有取得供应商成功；该现场已保全，后续新 attempt 已取得真实成功，见下文。cleaner 已完成恢复准备，reviewer 正按实际链接缺口重新准备。后续记录应补充每项实际入口结果、供应商原始响应、原生会话继续、监控绑定和最终应用身份；具体请求错误保存原文、HTTP 状态及可诊断内容，公开记录不包含凭据。

## 并行新 baseline 的反馈入口

用户另行授权的两根模型干净起点 baseline 由原 I13 会话 owner 执行，原件归 `runs/iteration14/baseline-roots-20261002/`。它与本会话共用 development-2，其卡点也纳入启动复盘，但不由本会话重复修复。两组使用新版允许需求，本会话三组使用原 I14 冻结需求，不能直接当作相同输入的模型对照。

GLM attempt `attempt-2522d62badad14158771bc66` 在 admission 的 reserve mutation 前，批量读取全部 11 个容器的 physical inspection 超时 30 秒；没有 create-intent/launch，runner 保留 launch_pending/unknown，不能当作已启动或允许直接重跑。原错为 `experiment/attempts/attempt-2522d62badad14158771bc66/launch-error.json`，无启动证据为 `glm-unlaunched-physical-evidence.json`。窄修复与有界重入归该会话执行 owner，本三项 owner 不重复修改同一派发窗口。

该 owner 另发现 `scripts/model_budget.mjs` 对 `PI_SUBAGENT_CHILD==='1'` 的跳过路径，正在核实是否会绕过按 Braid session 的唯一昂贵 owner 保护；该 owner 随后实查 foreground/execution.ts 继承 BRAID_STATE/CLI_BINDING_ID、pi-spawn 使用预算包装器，确认跳过路径会绕过父 Braid owner保护，已删除整体 return。多个同父孩子仍以同一 agent_id 计入同一个 Braid session；源码语法通过，不据此认定所有旧包已有保护。两线后续包重新冻结采用；没有将该缺陷推断成已发生的具体超额账单。

并行两组新 baseline 的 experiment-final 同样被 storage reserve 拒绝（观察1790938224.3007958），原 controller/error保留，沿相同物理文件系统核对与新根交接处理，不重复删除现场或重新压缩未变化ZIP。

准入 inspect 超时后续定位：baseline owner逐对象只读检查，其余11对象约0.2–0.4秒返回，唯一容器 `516628a2b2087a3de67e8cd50632a1bd9636f6f8779b838ab4b45384b5a37952` 连续30/60秒超时。该对象归本会话 reviewer prepare 的 `attempt-e77cba903ba6029d7969d2eb`，launch/resource和export原件一致；`export-1790938012406728000/transport-error.json`保留输运错误。由 reviewer原owner收敛在途export及实际容器可读性，不跳过未知对象或假释放reservation。该观察把“全域inspect超时”缩小为具体对象/输运窗口，不自动认定daemon整体故障。

上述具体容器后续由原owner独立inspect约0.4秒返回 exited/Pid0，Running/Paused/Restarting均false；Mac无该cid在途cp/exec。证据为 `runs/iteration14/dx-launch-20261002/reviewer-inspect-after-export.json`。原错误明确为同attempt全 `/attempt/.` Docker cp300秒超时，不是新的模型失败；入口退出1/checkpoint partial仍保留。输运修复沿同attempt接续，不重跑旧入口；canonical变化所需的新prepare是另一个有来源的新执行。

## e2e 修复后的实际正反馈

2026-10-02 18:57 CST 保存的成功观察为 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002/e2e-native-activity.json`。实际 attempt 为 `attempt-482e5780ca417e6ebb63e28b`，容器为 `aecd15534ef849c80bb1d8d20e22fbea2e4dba1f155db921ce008c12bf4eee12`，Braid run为 `20261002-105607-3c89d659`。原生路由 `factory26-route-57e81eb4b2da`、发送模型 `ZHIPU/GLM-5.3-Flash`；10条 assistant中保存的成功消息为 toolUse/errorMessage=null，有具体tool活动和usage，不只是容器RUNNING。usage里的cost0不是已查询账单，不据此认定实际费用为0。

同一观察保存sample age926969065ns、memory.max2147483648及Pi进程 `Max address space unlimited`，支持资源采样、Docker物理限额和AS修复已在这条真实执行采用。该结果不证明e2e工具已被Agent调用，也不证明应用完成；cleaner/reviewer及最终评测仍需独立结果。

准入超时重现的耦合：旧516对象恢复后，e2e/cleaner/reviewer新材料复制窗口又使全量physical batch inspect30/60秒超时，另baseline experiment-live在reserve前失败、没有创建新对象。不是已确认的五槽耗尽；单对象copy/export期间暂不可读会阻塞全域新reserve。两线按稳定owner分工：本三项顺序处理大复制并在launch-handoff保存精确attempt/container/held及窗口；另一 owner 评审后保留 held/physical 合同，仅增加物理只读查询的有界重试；未知身份仍阻塞，不假释放 lease。原提议的占位捷径没有采用，当前以顺序复制和实际读回协调启动窗口。

主线已使用每项冻结launcher/source执行公开 `lab monitor --json`，没有请求平台或live采样。`runs/iteration14/dx-resume-20261002/monitor-primary-readback.json` 实际显示e2e generate running、cleaner/reviewer prepare running；e2e评价正确等待生成终态及应用产物。稳定monitor/index和binding现已发布，绑定存在不等于两项恢复已开始模型调用。

并行新 baseline GLM 已取得真实正反馈：`runs/iteration14/baseline-roots-20261002/glm-live-readback.json` 保存Braid `20261002-110120-f5e81834`、11:01:36.627Z的glm-5.3成功assistant、12677 total tokens、error0，当前样本memory.max2147483648、oom/oom_kill0以及Pi AS unlimited。昂贵owner绑定实际root session。本会话不重复派发GLM；Flash另owner按同域容量单独补派。

容量口径纠正：此前沿旧host说明把Redis计入foreign并推定四Factory槽，不准确。主线独立读取canonical、本轮e2e以及reviewer frozen admission.py，三者SHA均为 `22e3a519a57f7d5742d1c5b4e9eff51558a7c4042bc548a6af599ba175118d42`；physical的ps显式过滤 `label=io.factory26.exp.attempt`，无此标签的Redis不进入helper计数。因此本轮是五个Factory执行槽，未改slot配置或停止Redis。排队仍按真正held与在途窗口判断，不以旧文字反向改设施。

cleaner后续真实准备已退出0，系统盘 `cleaner-checkpoint-partial.json` 文件名沿诊断命名，但内容status=complete/readback.gaps=[]，五仓Git检查均退出0并列出完整native历史。公共prepared输出artifact-c4131e0cce48851c97ac06e8已独立published，terminal大archive尚pending；启动owner从同exact volume输运已sealed named产物，经公开artifact verify/transfer和正常prepared门控继续，不重跑旧prepare、不修改immutable prepared。此路径将语义完整性、具体产物输运与整域终态保全分别记录，不能把pending大archive直接当成生成不可启动或交付失败。

两freshbaseline Flash也已取得成功，真实绑定 `runs/iteration14/baseline-roots-20261002/active-bindings.json`（GLM experiment-live / Flash experiment-flash）已接入既有十分钟heartbeat。失败blocked实验仍保留但不作为当前有效生成矩阵。

reviewer 精确 node-gyp 修复后的新准备首次在 Docker info 确认 daemon 时触发 10 秒 `TimeoutExpired`。当时 execution/binding/resource/create-intent 均不存在，尚未 reserve 或启动 entry；原件保存在 controller 历史及系统盘 `reviewer-nodegyp-preflight-readback.json`。原 owner 随后成功确认同一 daemon，通过公共 `lab start` 重入同 attempt `attempt-ef630a2f3aa6a6608a020bec`，没有重复已执行的 prepare；最终入口结果仍待回执。

cleaner sealed prepared 输运已采用 1800 秒总界限并绑定 extractor/helper 的精确出生身份；进展、截止与退出回执归系统盘 `cleaner-prepared-transport.json`。当前已有约 3.0GiB 部分提取，尚不等于完整 artifact。到期仅终止这次精确 extractor，保留 immutable source 与 partial；通过公共 artifact verify 后才可进入 compile，不重跑 prepare。

cleaner 输运随后完成，`cleaner-prepared-transport.json` 保存 source_exit_code=0、extract_exit_code=0 和 finished_at。它证明来源读取及本地提取成功，尚须公共 artifact 完整核验、compile/doctor/build/start 和原生模型响应，不能提前标记生成已运行。

cleaner named prepared 输运耗时 660.924 秒、两端退出 0，随后公共 artifact verify 成功；生成实验已完成 compile/build 并发出公共 start，仍待实际 entry/native 响应。

reviewer 新 prepare 的同 attempt `attempt-ef630a2f3aa6a6608a020bec` 在 admission reserve 前，对 17 个容器的批量 physical inspect 再次触发 60 秒 `TimeoutExpired`。原错为系统盘 `reviewer-nodegyp-prepare-experiment/attempts/attempt-ef630a2f3aa6a6608a020bec/launch-error.json`。runner 已写 accepted/effectunknown，但 resource/create-intent 尚不存在；canonical 重入仅 observe，不能直接重入 docker_launch。恢复须核对真实 authority 中没有 reserve/启动副作用，独立 advisor 正复核窄公共恢复条件；不凭文件缺失跳过 physical 门控、不假释放未知持有对象。

独立 advisor 对上述 reviewer 阻塞的裁决：增加显式 reserve 前接续管理入口，保持同 attempt/request/incarnation 和参数；持原 dispatch.lock，核验原派发窗口已闭合、无 create/resource/start/launch 记录，同 daemon 当前 authority 无任何该 attempt reservation，并完整查询确定性名称及 attempt 标签，确认执行容器和执行卷不存在。查询失败或任一 reservation phase 均拒绝。physical 查询在预约 HELPER 前失败支持本次窄路径，但 authority 卷本身可能已创建，不能称零副作用。保留 unknown/错误及独立接续回执，沿既有 docker_launch 的 CAS 和预约门控；不修改 HELPER/held 合同。公共恢复工具记录自己的源码版本，容器仍使用原冻结 runtime.source，不篡改旧 manifest/source。修复由原启动 owner 完成并实际验证。

系统盘迁移后容量继续下降：当前 `/System/Volumes/Data` 约 13GiB 可用，cleaner generate 已分配 `attempt-521bc2eaaaf45445b2075f6c`、仍在 prepared 装配且尚无 execution receipt。默认本机 reserve=12GiB 可能在装配结束再次拒绝，此时尚不是已发生拒绝。远端单 attempt 产物上限仍为 12GiB。其他 baseline owner 曾单独冻结本机 reserve=1GiB；本三项不据此篡改既有 attempt，正独立核对剩余复制/归档预算与可保全的可重建重复副本，不为通过门控虚减实际空间需要。

reviewer 的公共 `continue-pre-reserve` 已在同 attempt 完成完整 authority/physical/name/volume 门控，原 unknown/error 与新增 `pre-reserve-continuations` 原件保留。实际容器 `d2d9811d1847ab9500c7de70a0d5161d514dfde92bbabad85cb37e9c0b050b46` 于 11:38:59Z 创建并进入输入复制，尚无模型调用。cleaner 原 12GiB 本机存储门控也实际通过，现为 launch_pending，无需为本次虚降 reserve；稳定 handoff/monitor 已补实际身份。

cleaner 生成容器 `a3e6ab0f5887541aa3a380283bb403b2e900b2dae8235f449b62052651aec821` 于11:40:46Z创建，输入复制在途；reviewer prepare 容器于11:40:41Z进入 entry running。显式接续另补一次性保护：任何历史 continuation/continuation-error 均拒绝沿用最初 inspect 错二次放行，避免后续 HELPER 超时的未知副作用被旧错误掩盖。编译通过，实际新容器创建反馈保留，未运行测试。

存储复核纠正：storage_reserve_bytes 并非纯本机门槛，远端归档还按 reserve+证据/输出体积预检；docker_export 会先整份复制 /attempt，再复制新增 artifacts，本机没有对应回传峰值预检。因此不采用1GiB来证明空间充足。cleaner prepared 有三份各约5.5GiB，分别为来源store、冻结artifact和在途输入；旧失败export约5.2/3GiB仍须保留。后续按实际导出T+新增artifact A+余量串行回传；复制闭合、相同内容完整核验后可用原生APFS clone/COW替换重复immutable payload，保持原路径/manifest身份，不用hardlink、不删除冻结引用。当前系统盘又降至约9.7GiB，必要时先报告具体缺量，不盲目回传至写满。

cleaner 实际 input 上传触发固定300秒超时：`docker cp tempupload/. a3e6...:/attempt` 的 `TimeoutExpired`，原件为系统盘 `cleaner-experiment/attempts/attempt-521bc2eaaaf45445b2075f6c/launch-error.json`。派发 PID24804已退出，无 launch/start/entry，只有绑定 Created 的实际 resource。原 owner 正核对严格同 attempt/sameCID 未启动 input-upload 接续，不重复 create 或模型入口；同时处理共享复制窗口与实际大材料输运耗时不匹配的根因，不仅逐项补重入。原上传暂存已清理，冻结artifact和失败证据保留；空间释放以实际df读回为准。

cleaner 上传接续的独立裁决：从既有 docker_launch 抽出共用“组装冻结输入→上传→完整读回→启动→绑定StartedAt”尾段，正常派发与恢复共用，不再reserve/create。接续前核验原输运闭合、同一resource出生身份、authority同一materialized记录，容器严格created/StartedAt为零/Pid0且无start/entry。完整读回后重新执行来源当前停止门控，不能沿用旧launch-gate；start结果不确定时仅观察，禁止再上传。只把input upload和terminal export两条大复制改为1800秒：当前300秒TimeoutExpired与同级660.9236秒成功输运为直接依据；小JSON/control查询不扩大。旧冻结runtime不篡改，公共恢复工具记录新版本。读回采用archive流核验，避免本机再落5.5GiB副本。

cleaner 公共接续已开始，先核验全部冻结artifact再重组staging；采用1800秒upload及完整archive流SHA/link/exec读回，实时来源停止门控后才start。reviewer stdout已出现checkpoint/native历史列表且无stderr，但尚未输出sealed artifact，不提前记prepare成功。旧冻结controller的自动export仍固定300秒、无本机T+A预检，不能热改冻结source；owner会在终态前量具体T/A，空间不足时仅关闭本源本机输运owner，远端entry/archive继续保全，再用有空间的公共管理export接续，不暂停模型或删除原件。

reviewer 新prepare实际 entry exit0，remote-final原件与系统盘 `reviewer-nodegyp-checkpoint.json` 已保存；完整Git/native还须核对。整域export的确切空间阻塞：活源T下限8,961,201,274bytes、新artifact A下限3,929,595,165bytes，加原reserve12,884,901,888bytes，共需至少25,775,698,327bytes；本机free9,609,064,448bytes，至少缺16,166,633,879bytes（约15.06GiB），源归档继续增长故均为下限。已核出生身份，仅SIGTERM本源本机controller PID485并保留lost回执；远端entry/archive继续、不停容器、不删证据。证据归 `reviewer-nodegyp-storage-hold.json`。sealed named prepared 发布后可独立取回，不等待整域export；cleaner同CID1800秒上传在途，完成后再核验APFS COW可回收空间并评估reviewer生成，不降低reserve。

主线采用 reviewer-nodegyp-checkpoint-readback.json：status=complete/gaps=[]，7个Git成员head/object检查均exit0，native保留pi-glm-fast 19、pi-glm-reviewer 2、pi-glm-root 0条历史；0是该profile实际读回，不误称存在root历史。原33MB checkpoint保留，不能将此准备成功外推模型请求或最终应用完成。

并行 baseline owner报告用户指出 Exp Console 当前实验显示错误且不能加载，实际检查将其定位为旧8765仍接WSL历史注册、新development2 baseline未接。其原owner正在实现固定原container身份的只读接入并保持模型运行；本三项仅交真实handoff/state/Braidrun/binary，不将prepare/failed或未产生状态登记为生成running。本项为另一owner报告，最终Console反馈归其实际操作原件，不由本会话重复启动服务。

cleaner 同CID的1800秒upload及完整archive流读回均成功，Docker start成功；管理尾段随后调用 `record("resource", **binding)`，binding带record envelope的kind/schema_version，触发 `TypeError: duplicate kind`（backends.py436）。原错归 `input-upload-continuation-error.json`及stderr。真实worker等待resource-start marker，尚无模型入口。必要修复是共享尾段剥离record envelope，并严格公共confirm-start-binding仅inspect/bind/marker：核同StartedAt/authority/noentry、完整读回及当前来源已停止，不再start、不再上传、不重prepare、不换CID。这是明确参数边界缺陷，不把Docker start成功外推模型成功。

e2e Console只读身份门控拒绝登记：console_sources指向 `/workspace/submission/runtime/bin/braid`、期望63fdabce...，另owner的实际docker cp SHA为e002edb848...。原件为 `runs/braid-console-control/20261002-current-runs/e2e-binary-mismatch.json`。需核对实际运行进程exe、原冻结manifest和work/runtime真实binary，不能直接将期望改成读回值冒充来源匹配。调查属于当前e2e范围；cleaner/reviewer暂停保持。

e2e二进制来源矛盾已核实：实际 `/proc/134/exe` 为 `/workspace/template/.factory26/20261002-105607-3c89d659/work/bin/braid`、SHAe002edb848...，冻结 `e2e-resource-final.zip` 的runtime/bin/braid及package-manifest.files也为同SHA；但manifest.sources.braid声称adopted63fdab...，来源元数据错误。原ZIP不修改，原件为系统盘 `e2e-actual-braid-exe.json`。handoff须绑定实际冻结file身份及work/bin路径，明确63版OOM/context修复未被此二进制采用；不能把旧期望直接换值并伪称修复已部署。当前仍生成，未有本条具体OOM/context失败原件；独立advisor正复核必要热部署判据和来源记录根因。

来源身份完整闭合：`e2e-binary-binding-readback.json` 核本地冻结ZIP完整SHA等于实际agent artifact manifest.contents SHA；ZIP runtime/bin/braid字节=package-manifest.files SHA=实际/proc134/exe SHA，均e002...。来源claim63元数据错误以source_claim_matches_file=false明确披露；Console改指实际work/bin且期望取原冻结file证据，旧记录保留。先前交接漏核文件身份已纠正。

独立版本裁决进一步确认，I14总packet已有用户要求OOM修复覆盖所有Braid variant、新制品/热恢复必须绑定修复编译身份，未撤销。因此本条还需必要e2e热部署，不能因当前无OOM只纠正元数据后视作合格。先保全当前进度和原版本、核完整同点恢复，沿公共门控重新冻结修复binary及实际进程读回；两暂停项保持。

版本根因的独立证据：真实linux-fix/braid-linux-x86_64为63fd，build-receipt exit0/source_sha ee2024.../binary_sha63fd一致，但两个adopted来源stage实际仍e002。旧冻结源码can_accept_input仅检查native_is_busy，修复源码新增claim前resource_status/native-state保护，确缺用户要求共用修复，并非只差context显示。最小根因处理是选取真实linux-fix字节，并在packager最终bundle file SHA与声明binary_sha256不一致时拒绝冻结，不静默改写source声明；再新包和/proc真实闭环。

独立完整冻结包读回覆盖32,636个manifest文件的stream SHA与执行位，extra/missing/duplicates/mismatches全部为空。文件合同本身完整且实际就是e002；来源声明错误不可称作包损坏，也不以修正标签掩盖未部署共用修复。

e2e公共pause已applied，原attempt/cid保留，Paused=true、原StartedAt10:55:35Z，回执e2e-oom-source-pause.json。当前为必要共用修复的同点现场保全，暂不是模型继续生成；后续须新冻结修复来源/prepare/实际进程身份完整闭环，原源先不stop。

e2e同点template快照完成：`e2e-oom-source/template.tar.gz` 412,992,296bytes、exit0、74.004秒；snapshot-receipt保存精确来源身份/SHA。定向现有日志的modelScope审计0匹配，原件e2e-modelscope-log-audit.json，不扩张为全局无错、不预改路由。公共stop随后派发，后续新恢复用真实linux-fix63+sourceidentity/buildreceipt。packager write_zip已加入最终runtime/bin/braid与声明binary_sha256不一致拒绝门控，原旧包矛盾仍保留；实际新冻结/prepare/运行待回执。

e2e旧源stop实际确认exited/Pid0、Pausedfalse/Restartingfalse，FinishedAt12:42:18.2636Z，原CID/volume/attempt保留。暂停同cgroup writer时快照封workspace.zip共84,819项、491,412,908bytes/SHA04a7dc...，恢复点为停止前最近完整现场，无主动弃置有效进度；Git/native完整性尚须公共checkpoint验收。新修复base正冻结actual linux-fix63，build/source/binary核验待新执行闭环。

暂停时最后卡点：真实63修复base已冻，新e2e恢复package退出1，`KeyError: template/requirements/requirements.yaml`，fresh driver把需求置template之外。原件为系统盘 `e2e-oom-package.stderr`及对应半成品。全实验暂停后不补输入、不prepare、不新增恢复/评价attempt；本会话11个controller精确身份均lost、在途本机操作闭合，回执all-experiments-user-pause-20261002.json。后续仅在用户新指示后接续此点。
