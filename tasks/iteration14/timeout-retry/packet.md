# Pi超时退避与组合Harness后续实验

2026-10-04用户指示：“好，现在对 405 问题设计一个长期修复的方案（先确认为什么 pi 的退避重试没能发挥作用；定位到根本原因，再制定修复方案）。然后用修正后的版本跑 github stage 1 ~ 3、 arc-bench web 题吧（web可以本地取得评分；github stages 可以到 https://arcbench-selftest-web.vercel.app/tasks 取得评分）。”上下文已观察错误为504 upstream_headers_timeout，当前按504调查并同时核对405，未将笔误当作已证事实。

本任务先完成诊断与修复方案，再冻结实施与实验范围。用户要求修正版后运行指定benchmark，授权目标已有，但具体web题目录、stage起始材料、运行矩阵和验收条件仍需核实；不从旧配方恢复队列、不读取隐藏测试来适配生成。当前仅调查、隔离实验、方案与准备；源码修复与收费运行尚未开始。

根因诊断由既有执行负责人 `combined_sfp7_owner` 持有，追踪原两次504代理请求、Pi退避分类/终态、后台作业auto-drain与Braid调度收尾的实际版本和因果关系。实验和评分准备由 `evaluation_preparation` 持有，独立核公开需求、官方runner、web任务清单与selftest现有合同；它不提交评分、不启动模型、不接管诊断源码。主线持有方案采用、授权解释、矩阵与结果交付。开发子会话不使用advisor，按此前用户限制执行。

证据来源为已完成组合run `20261004-023236-a69535b2`，两次504及reviewer局部移交保存在 `runs/deadline-20261003/combo-restart-20261004/`。最终生成已21:22:29正常退出，应用冻结，诊断不控制旧run或改其身份。新证据与准备放 `runs/iteration14/timeout-retry-20261004/`；旧原件保留。Mac所有产物WorkSSD、远端sfp7执行数据可留远端。不运行Factory/Braid/SVC测试、探针或smoke；编译、真实操作和获授权benchmark提供反馈。模型/供应商、内存/预算与高价模型Braid session合计限制须冻结，不借诊断任意换模型或无限重试。

待解决的不确定性：Pi实际是否识别代理504为可重试；重试是否开始或被agent_end钩子阻断；为何原生error已持久而Braid仍running；代理未知上游执行的请求重放边界；web具体题目范围及每个stage的公开起点。下一步以真实事件和运行版本定位根因，形成跨组件约束、窄修方案及实际验收，再采用实验准备的矩阵。


## 已采用诊断与实施范围

诊断见[根因与证据](../../../runs/deadline-20261003/combo-restart-20261004/timeout-retry-diagnosis/diagnosis.md)。两次504均为代理90秒无headers后本地产生；未发现405。实际Pi支持504、默认3次2/4/8秒退避，阻塞来自准备退避前等待agent_end扩展。subagents/PBB缺少willRetry信息并等待后台工作。实际bin/pi加载bundle，既有core补丁未进入实际bundle，修正版必须统一入口字节。供应商是否生成/计费及30分钟后精确await仍未知，不借未知自动重放代理请求。

主线已采用方案并根据用户“然后用修正后的版本跑”的完整指示进入实施，无新增审批要求。修复owner负责唯一retry判定传播给extension与RPC，subagents/PBB重试期间不阻塞drain；耗尽/error保存原错、完成结果和active refs，不自动触发第四次推理，可靠settled/error；成功收尾及cleaner提交不变。统一实际Pi入口与patch生产身份。代理timeout、模型/供应商/fallback不变。编译与实际授权benchmark验收，不执行本地固定错误响应模拟重演、设施测试/探针/smoke；没有自然瞬态故障时明示故障路径未实证。

实验owner `evaluation_preparation` 持5题的生成与评分：GitHub stage1/2/3各确切公开输入各一次，Web为12306与携程（ctrip）各一次。制品ready前只准备；修复owner直接交可消费制品。生成仅公开需求，冻结应用后逐题评分，web官方本地runner，stage用户指定selftest；评分不注入其它在途生成。sfp7实际容量/daemon/runtime/input与wall/token/storage/并发由owner核实冻结后登记；当前4GiB/无swap和模型配方作为沿用基线，不任意扩展。新实验不恢复其它run、官网正式提交或heartbeat。


实验准备中的三阶段输入与资源合同已采用[矩阵与输入证据](../../../runs/iteration14/timeout-retry-20261004/preparation/evaluation-matrix.md)。GitHub三份确切公开requirements来自历史同题workspace归档，仅提取公开requirements成员；不传历史应用或评测结果给新生成。Web消费本地六题的公开requirements，tests由独立评价阶段读取。每run4GiB无swap、sfp7与WSL两机合计5题全部并发、12小时生成wall上限，实际sfp7容量/运行身份由启动owner读回并冻结。每题一次生成，设施故障必要修复保留失败identity，不以失败当有效零分、不自动增加模型轮次。


## 当前实验范围纠正

用户明确纠正：“9题？不是应该只有4题吗？”主线此前误把Web解释为本地六题全集，现收回该解释。当前仅GitHub stage1–3三题加一题Web；Web具体题目已询问用户，尚未确认前禁止Web派发。GitHub三阶段可独立准备与运行。此前六Web哈希仅作准备证据，不授予其生成/评分。执行owner立即核在途队列并关闭Web派发，保留已受理身份与原件；实际回执待owner返回。

修复制品已ready：`runs/iteration14/timeout-retry-20261004/implementation/agent.zip`，722242070bytes，SHA256`8a926096eac2aa0df6365e67e9e1093a1b37a842a51192581bb0dc88b5d9e50b`。实际入口/core/插件字节归同目录artifact-identity.json，编译范围和限制归implementation-receipt.json。修复实现授权不因实验范围纠正而改变。


用户已回复：“哦天哪，抱歉我没有意识到 web 有这么多题目，我们仅选择 web 的 12306, 携程吧。”当前最终范围改为5题：GitHub stage1/2/3与Web12306、ctrip。仅这两Web解除派发暂停，另外四Web不启动，旧9题和暂时4题理解均被此明确选择替代。执行owner已收到队列更新，可消费修复制品直接继续，不需再审核。


用户新增：“哦对了，上一个 github 的运行成果别忘了保存下来哦”。旧run稳定owner `combined_sfp7_owner`负责将已完成的`20261004-023236-a69535b2`、最终main `c15d9858`的应用、Git与验收/终态/必要运行证据回收WorkSSD并生成封存清单，保留远端原件，不混入新实验或重跑生成。

首批执行反馈：GitHub Stage1与Web12306已在sfp7进入Pi/Braid进程，4GiB/no extra swap，消费已冻结SHA8a926096。首轮Stage1因解包Rustproxy为0644在模型前失败，原件`execution/failed-initial/github-stage-1`保留，执行owner恢复权限后重启。修复owner继续核实ZIP可执行位与消费安装边界，当前不声称仅有进程即完整模型成功。执行owner持五题逐题生成/冻结/评分闭环，剩余题按并发安排，不增加其它题。


用户最新：“有sfp7+WSL两个设备，并发全部题目是没问题的”。当前5题全部并发，覆盖此前初始2/最多3的临时资源安排。保留sfp7已运行Stage1与12306，不重启；owner先核两机实际daemon/image/capacity及旧队列在途，再启动剩余Stage2/Stage3/ctrip，停止旧队列重复新派发可能性。每run4GiB/no extra swap、同修复制品身份、12小时wall和评分隔离保持。建议sfp7三题/WSL两题，具体按实际宿主余量由owner决定并记录。


五题实际运行身份已交[handoff](../../../runs/iteration14/timeout-retry-20261004/execution/handoff.json)：sfp7 Stage1 `20261004-142939-bc8d926a`、Stage3 `20261004-143747-395482a7`、12306 `20261004-142926-43d7aecc`；WSL Stage2 `20261004-143923-63c2f90d`、ctrip `20261004-144059-9c31b6d6`。均已真实Pi模型活动。当前交接中旧orchestrate.sh仍含串行补发及hardcode宿主，主线采用时发现具体重复派发/采集风险，已交执行owner立即核旧controller身份、退役旧补发而不控制5个run，并发布只消费准确跨宿主终态及评分的新consumer回执；尚不把score-plan等同评分已运行。

旧GitHub成果保存已完成：final-delivery/final-application.zip SHA`4ef2f52a950bd8b271bc01a77746a8890169afe4e1e4a0ef0e2cb04c3b7e7661`，112个应用源文件核验；final-run.tar.gz 580001621bytes，25,943条文件/链接核验；17个Git工作树与7个dirty工作树、Braid/native/gateway/验收和原harness已封存，git fsck exit0保留dangling历史对象。13项约1.49GB，远端原件保留，不声称live完整checkpoint。清单与完整性限制归[封存清单](../../../runs/deadline-20261003/combo-restart-20261004/archive/final-delivery/manifest.json)。


旧controller风险已解除：原session17972停止、PID52574不存在；orchestrate.sh改为collector-only，无create/rm/restart路径，新session68240按各job实际development1/2采集，handoff保留旧身份退役和新绑定。五题仍generating，无可评分终态。`evaluation_preparation`继续持有本轮完整生成/冻结/实际评分，主线明确要求等待终态逐题评分，不以score-plan或采集器running冒称评测完成；普通进展只保存，第一题真实评分、必要异常和完整结果用完成消息交主线采用。当前root已完成根因、方案采用、修复制品/真实启动及旧成果封存的交付；本轮最终分数待该稳定owner结果，不增加新轮次或恢复heartbeat。


## 2026-10-05 Stage2场地决定

用户问：“那么将stage2放到wsl运行？还是现在就尝试再启动到sfp7？”当前有界读回：sfp7约16GB、Stage1/3/12306三题各4GiB，WSL约16GB只有ctrip有效生成，失败Stage2仍有约728MiB残留；两机当前PSI为0。原Stage2失败观测不能证明WSL两题必然容量不足。主线选择WSL唯一新尝试，不在sfp7叠第4个4GiB上限，也不继续静候sfp7空槽。此为已有5题全并发与必要设施恢复范围内的常规调度。

执行owner先核退役旧等待恢复controller62994及在途窗口，保全失败源，精确识别并停止旧Stage2残留（不把728MiB解释为仅sleep），ctrip不受控制；然后同artifact/input/model/gate/4GiB/no swap启动Stage2-r2，独立身份，更新collector/评分绑定。再次同类失败不循环重跑，保留事实交回判断。停止可能损失仅该已失败来源的后台服务活动，源进度/错误/原件保留，当前不追认完整checkpoint或改变门控阈值。实际新模型活动待owner回执。


WSL新Stage2实际启动已采用：旧恢复controller62994已退役、无r2 start-intent；旧失败容器只存sleep且job.exit1，约955MiB源output已保全，残留容器精确移除，ctrip未受控制。新容器c2269569、Braid run`20261004-161257-31991cf1`、Pi session`01a107b0-f2fc-74b0-b6c7-2acd1bff50b5`，startup handshake及新语义活动已确认，同artifact/input/model/budget/95%gate/4GiB/no extra swap。collector74620已绑定r2实际development1，负责其余4题和本次r2终态与评分。具体边界归execution/recovery-stage2.json；不将源955MiB备份追认为完整checkpoint，也不把新run身份合并旧失败。

## 2026-10-05 删除资源压力门控的实施授权

用户明确“删除资源门控，保留既有运行数据，接续运行”，并追加“同时也用移除资源门控的版本去恢复 github stage1,2；使 github stage3 重新运行”。本次授权覆盖共享Python启动准入、Pi claim/send压力检查和Braid压力恢复/fail-closed路径的删除，不是仅调阈值。`combined_sfp7_owner`持源码、权威文档、编译和正式新制品；`evaluation_preparation`持携程与Stage1/2来源保全及接续、Stage3 fresh与评分。原运行和容器不清理，费用/session预算、Docker4GiB/no-extra-swap及进程登记、停止fence、birth identity、清理证明保持。编译与真实授权运行提供反馈，不运行Factory/Braid测试、模拟或探针，不用advisor、不commit/push。

实施证据归 `runs/iteration14/timeout-retry-20261004/remove-resource-gate/`。旧resource-failed/pressure/recovery预算仅为历史证据，不在新运行中重新关闭准入；旧execution stopping/ownership记录仍属于写者隔离和生命周期约束，不能为了接续绕过停止证明。正式SHA交执行owner消费，临时agent-nogate.zip不作为共同制品。

2026-10-05 资源门控删除正式制品已生产：`runs/iteration14/timeout-retry-20261004/remove-resource-gate/agent.zip`，SHA256 `70f134fef768d03b4c6339ac9f6b5837fec7be936cd071f88cf1c80227fd809c`，722305773 bytes。当前 Linux Braid release、Pi 与插件编译通过；Python launcher/claim/send/shared recovery 压力门控删除，保留 ownership 登记、stop fence、真实 Docker 内存限额和模型费用/session 预算。正式包保留 `runtime_resource_environment` 调用，其语义已改为纯登记，不能沿临时方案删调用而关闭停止证明。旧失败/压力记录保留但不参与准入。权威行为归 `docs/product-tdd/runtime-resources.md`；实际字节身份、编译限制与安装执行权限合同归同证据目录的 `artifact-identity.json` / `production-receipt.json`。已经直接交 evaluation_preparation 执行 Stage1/2 offline-resume，Stage3+携程 fresh；本条记录生产完成，实际部署/运行反馈由执行 owner 补充，不把编译通过当作已运行。

## 2026-10-06 00:13 CST 终态与评分核实

携程 `20261005-035205-08c0ba7f` 的容器 `f26-i14-nogate-web-ctrip` 于 2026-10-05 23:49:40 CST 达到冻结的 12 小时 wall 后退出，`oom=false`；已保存 `execution/results/current-web-ctrip` 及完整 Git/Braid/native/失败 turn 证据，未删除来源。PR2 仍为 OPEN，ready commit `bbc0458f8f43b695b56f27c686d1465382f9a0be`，对应 worktree clean；Issue OPEN、`delivery_closed=false`。因此本轮没有携程最终交付分数。该 clean PR 快照可作为另行授权的阶段应用评估来源，当前只标阶段快照，不冒充完整交付结果，也不自动扩大 wall 或 fresh 重跑。

GitHub Stage3 官方提交 `65aecd15-98d0-4c9b-99b4-dda018c28f2e` 已通过独立官方页面核实为 2/41（5%），不是用户报告值；package SHA `9523b0baaa0c2d6a34fac4c5efda476081ab502806305d15bcb5cdb5943f783e`，核实结果已写入 `execution/github-score-receipts.json` 的 `stage3_verified`。Stage1 官方结果为 15/30，Stage2 为 5/29，12306 为 91/135，均按各自 receipt 保留。

## 2026-10-06 携程接续

用户明确要求“接续携程”，授权沿现存数据继续本题，不从头生成。原停止容器和归档保留。新 WSL 容器为 `f26-i14-nogate-web-ctrip-resume-20261006-r2`，沿用 source/run `20261005-035205-08c0ba7f`、无压力门控 Braid SHA `56e9d1007abec0e18065ff37c3680c48debca47c5b88f560cbd7eea9f5c40766`、4GiB/no extra swap 和原模型、费用、session 预算；新容器仍使用有界 12 小时窗口。

恢复负责人此前未能完成启动，主线暂停其 turn 后接管启动控制。消费端恢复材料缺少原 `budgeted-pi`，运行时目录、模型环境和网关启动接线也有缺口；原请求与预算启动器均从停止的源容器取回，没有伪造替代请求或关闭预算保护。失败目录与日志全部保留。派生 workspace SHA 为 `c9428462ad744c241f2b98ab45e2981f2efc1ab433634809e8e38b1f75733388`；运行时回到合同要求的 `/job/agent`。独立接续控制脚本调用冻结包内的 standalone Rust gateway、原模型绑定与恢复入口，并保留无压力门控 helper 的 ownership、Portless 和停止生命周期。

01:19 CST 已确认实际接续：`--offline-resume` 正在运行，新的 wake batch 已产生两个 running turn，原生会话已有工具调用及结果；Issue1、PR2、review1 仍 OPEN。当前唯一控制脚本为 `/job/continue_root_r15.py`，当前日志/退出绑定 `/job/job-root-r15.{stdout,stderr,exit}`，不得读取此前失败尝试的旧退出文件。源 run 身份沿用，恢复 attempt 独立记录。启动证据归 `execution/root-ctrip-resume-20261006/startup-receipt.json`，操作来源和失败保留归同目录 `operator-record.md`；后续继续生成、冻结并执行官方本地评分，不将历史 GitHub 评分注入生成。

## 2026-10-06 01:20 CST 携程 r15 接续交接

用户明确授权“接续携程”。主线启动唯一 live controller `/job/continue_root_r15.py` 于容器 `f26-i14-nogate-web-ctrip-resume-20261006-r2` 内，沿 source/run `20261005-035205-08c0ba7f`、正式 no-gate artifact SHA `70f134fef768d03b4c6339ac9f6b5837fec7be936cd071f88cf1c80227fd809c` 与 Braid SHA `56e9d1007abec0e18065ff37c3680c48debca47c5b88f560cbd7eea9f5c40766`。已观察到 `--offline-resume`、3 个 Pi startup handshake、两个新 running turn 及原生工具调用/结果；费用、模型、4GiB/no extra swap、12h wall 和压力门控删除边界保持。

执行 owner 已启动 collector-only `execution/collect-ctrip-r15.sh`（PID 记录于 `execution/collect-ctrip-r15.pid`）。collector 以唯一 `job-root-r15.exit` 或 Docker stopped 状态判断终态，并从容器回收新输出，不读取旧 attempt exit；终态后冻结应用并运行官方本地 Web ctrip runner。旧容器、旧 run、失败尝试和新 r15 现场均保留。

## 2026-10-06 11:00 CST 携程 r15 终态回收与交付校验失败

r15 已达到 Braid 终态而非继续生成：回收的 `braid-state/result.json` 显示 delivery commit `6ded27d9265c39e763206f47bd52cca8b92f9505`、root Issue `CLOSED`、`scope_closed=true`、status `quiescent`。控制器 `/job/continue_root_r15.py` 以 exit `1` 结束，原始 stderr 保存在 `execution/results/current-web-ctrip-r15/job-root-r15.stderr`。

失败发生在 `recover_completed.py -> deliver -> validate_application`，具体错误为缺少 `/job/output/.factory26/20261005-035205-08c0ba7f/recovered-application/frontend/package.json`。已回收完整结果至 `execution/results/current-web-ctrip-r15`；应用实际包含根 `package.json`、`apps/web/package.json`、`apps/api/package.json` 和 `packages/shared/package.json`，提交树同样没有 `frontend/package.json`。因此这是交付布局/验证契约不匹配，当前没有可合法冻结的 Ctrip 评测包，也没有分数；不记为有效零分。旧容器、原 run、Braid/native、失败日志和 r15 回收件均保留。`execution/ctrip-r15-collector-receipt.json` 已登记 exit、commit、错误和 `blocked_invalid_delivery` 状态。

## 2026-10-06 11:00 CST 携程 r15 终态回收与交付校验失败

r15 已达到 Braid 终态而非继续生成：回收的 `braid-state/result.json` 显示 delivery commit `6ded27d9265c39e763206f47bd52cca8b92f9505`、root Issue `CLOSED`、`scope_closed=true`、status `quiescent`。控制器 `/job/continue_root_r15.py` 以 exit `1` 结束，原始 stderr 保存在 `execution/results/current-web-ctrip-r15/job-root-r15.stderr`。

失败发生在 `recover_completed.py -> deliver -> validate_application`，具体错误为缺少 `/job/output/.factory26/20261005-035205-08c0ba7f/recovered-application/frontend/package.json`。已回收完整结果至 `execution/results/current-web-ctrip-r15`；应用实际包含根 `package.json`、`apps/web/package.json`、`apps/api/package.json` 和 `packages/shared/package.json`，提交树同样没有 `frontend/package.json`。因此这是交付布局/验证契约不匹配，当前没有可合法冻结的 Ctrip 评测包，也没有分数；不记为有效零分。旧容器、原 run、Braid/native、失败日志和 r15 回收件均保留。`execution/ctrip-r15-collector-receipt.json` 已登记 exit、commit、错误和 `blocked_invalid_delivery` 状态。

## 2026-10-06 11:35 CST 携程交付包装修复与官方本地评分完成

用户明确授权“帮忙修复一下携程交付的包，然后运行评分”。沿原冻结 source/run `20261005-035205-08c0ba7f` 与 delivery commit `6ded27d9265c39e763206f47bd52cca8b92f9505`，未改生成源码。修复包装 `ctrip-r15-layout-fix-6ded27d-r8`：将 `apps/web`、`apps/api` 适配为官方要求的 `frontend`、`backend`；将 `shared` 改为本地依赖；backend 托管 frontend/dist；为官方 Node 20.19.3 增加 `node:sqlite` 的 `better-sqlite3` 兼容层；保留已验证 Linux ELF，并把 native loader/dependencies 放在官方 baseline 会保留的路径。原失败包、r1/r6/r7错误和源 run 全部保留。

本地前端构建通过；WSL 官方 runner `factory26-arcbench-runner-i14-wsl:20261003` 实际启动 backend（`0.0.0.0:3000`）并完成 125 个 Ctrip Playwright 用例。结果：16 通过、109 失败、通过率 12.8%，runner 测试退出码 1；runner 因 meter 未提供费用无法计算其加权 score 字段，因此记录为 score=null，12.8% 是实际测试通过率，不冒充加权分数。原始 report、stdout、preflight、runner events 已回收至 `execution/scores/web-ctrip-r15-layout-fix-r8/ctrip-r8-evidence.tar.gz`，receipt 已登记包 SHA、根因、结果和限制。
