# e20261001-01：I13 首轮实验

当前状态：GitHub单题已在生成阶段异常终止，尚未评测；用户已授权子Agent保全工作区并排查证据，正在执行。此前用户因 WSL 问题改为官网参赛，明确授权“上传到官网运行，参加比赛，使用比赛额度，跑github先，继续按3+8监控实际运行状态（glm-5.3-flash variant）”。本次仅启动 `pi-braid-i13` 的 GitHub 一次；WSL、本地矩阵、Sheet 与 GLM 根组继续暂停。以下旧本地安排保留为历史方案，不作为本次官网启动前提。

2026-10-01 用户在审阅最终检查结果后明确：“好的，可以启动 I13 了。”本轮承接两组根配方各生成 GitHub、Sheet 一次，共四次新生成的建议，授权必要的根对照实现、最终材料冻结、独立干净宿主建立、本地生成、Console 人工介入与逐题官网应用重放。I12 已结束，仅保留其归档；当时无法挂载的旧 Debian VHDX 和冷备不进入恢复范围。

## 当前官网启动范围

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

官网 failure_reason 只有外层命令 `python3 /workspace/submission/main.py ...` 返回非零，没有 traceback。终止前 Braid 仍有 PR #3/#4/#5 的实际编辑与测试活动，`active_turns=3`、`blocked_groups=0`、`delivery_closed=false`；PR #5 同时出现 Node 24 不满足项目 `>=20 <21` 的依赖错误，但现有证据不足以证明它就是外层退出根因。因此本次结论为“生成阶段未归因终止”，不是已确认的 Harness、应用或 provider 故障。

完整终态证据入口：`runs/iteration13/hosted-20261001/completion.json` 与 `runs/iteration13/hosted-20261001/monitor/20261001T065751.899359Z/346bc3b51b09/`；独立监控已完成采集，未重发请求、未启动第二次收费尝试。用户随后明确要求“安排sub-agent保留工作区并且排查证据”。已委派 `/root/i13_hosted_failure_evidence`（GPT-6.1-Sol / extra-high）下载并核验官网可得工作区与日志、保留Git/未提交worktree/Braid数据库和会话、核对终止因果与恢复一致性。独立输出归 `failure-investigation/` 与 `tasks/iteration13/hosted-github-failure.md`；当前无重跑或源码修复动作。

Mac 后台协调进程46943、3+8采集进程46944已经启动，使用 `lab.arc_bench.hosted_monitor --review` 与独立 `agents/run-monitor.md`（GPT-5.6-Luna/low）。首批实际状态与归档读取成功，归档当时仅含需求，尚无原生会话，因此只能证明平台启动阶段，不能证明模型已开始有效开发。第一次内容审查已结束；主线已消费其引用并保留此证据缺口。终态由 `follow-hosted.py` 收集 status、logs、traceability 与 Git history。heartbeat `i13-github` 每8分钟消费已有监控结果，仅在故障、完成或需要决定时通知；现已按用户要求迁入独立[GPT-5.6-Luna监控会话](codex://threads/01a0f613-082a-7251-a25f-e99acbc37706)（low），主开发会话不再定时唤醒。

第二批13:24:58 CST已取得Braid与原生会话，主线直接读取确认：根Issue #1开放且有1个活跃turn，根Agent已检查应用仓库与Node环境，启动应用依赖安装（30秒后自动进入bg001），并于13:24:42调用vision子Agent分析12张需求参考图。这证明模型和实际工具链已开始工作；应用实现、最终覆盖、advisor调用与评分仍待后续证据。

13:34批次的原生证据确认：根Agent提交设计资料、创建基础PR #2并指派DeepSeek；DeepSeek已读取需求与设计。根曾误用comment --message，随后读help改用body-file并成功发布评论，属于已自行恢复的调用错误。监控旧逻辑按文件名字典序选中advisor/vision旧子会话，审查因此错误关联到Issue/PR；主线已直接读取两条当前Braid原生会话纠正。监控现按physical_sessions的原生路径生成带工作项/profile身份的session_evidence，当前两条会话均进入必读列表；实际归档读回及Python编译通过。仅重启Mac监控（协调PID53789，当前采集PID53790），保留同一run与下一次采集时点，官网生成未中断。回执为 `monitor-session-selection-readback.json`、`monitor-restart-session-mapping.json`；13:44既定采集已实际返回正确的session_evidence映射，关联文件均存在。

监控会话移交：用户明确要求创建GPT-5.6-Luna独立会话并将automation迁入。已创建 `01a0f613-082a-7251-a25f-e99acbc37706`，将现有 `i13-github` 的target_thread_id从主开发会话改到该会话，保持原8分钟频率；现有3+8后台采集及官网run均未重启。原始配置读回在 `monitor-thread-handoff.json`。后续日常监控与终态通知由该会话负责。

回执入口为 `runs/iteration13/hosted-20261001/launch-summary.json`、`submission-history-after.json`、`monitor-launch.json` 与 `monitor/`。本地WSL无新增操作，Sheet和GLM根组未启动。

## 配方与判断目标

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
