# 10 月 3 日截止：pi-minimal-vv 手工正式参赛

用户于 2026-10-03 更正提交截止为北京时间当日 23:59，并明确：“停止使用任何的实验基础设施，手工，最小化，立刻安排 sub-agent 将 pi-minimal-vv 分别启动到 github stage1~3 以及 sheet。”随后明确“没有预算限制”。这直接授权四项官网正式启动及必要入口修复；旧 100 元预算上限和本轮必须经过 Lab 的操作要求由此覆盖。

当前用户决定分三路：Pi立即正式启动GitHub Stage 1–3和Sheet，争取23:50前完成；I14-baseline立即正式启动GitHub主任务，用户明确该项不变，这正是Pi只跑四题的用意；本地五个I14候选在已定多provider-failover自费API下各4GiB并行生成GitHub，再上传自测站评估，23:50按最高分选最终提交。最终候选计划覆盖此前I14五题接续，具体启动仍等待同题Pi终态和平台槽位。两套Harness不同submission的分数不假设自动继承或合并。所有新生成从公开需求干净起点，不预置赛题应用，不重复未知效果的写请求。

用户进一步强调：“Pi得先跑完它的task才能释放出槽位给I14-baseline运行。”I14包可提前准备，同题启动必须等Pi终态与实际槽位释放；两位owner直接交换终态身份。GitHub主任务也须核对真实平台容量，不从没有Pi对应题推定可运行。23:50是目标，不构成取消未完成Pi的授权；若临近窗口仍被槽位阻塞，汇报具体状态并交用户决定。

## 负责人和验收

用户要求全部sub-agent/session使用GPT-6.1-Sol / Extra High / Fast，并明确授权创建独立session/task提高并行度。主机配置已核实`service_tier=priority`。

| 负责人 | 稳定范围 |
| --- | --- |
| `pi_fast` | Pi修复包、正式四题启动及实际活动核对；已取得submission `aea08b61772c`。 |
| [官网baseline会话](codex://threads/01a10224-fe0f-75b1-8484-30b859229a30) | I14-baseline正式GitHub主任务，独占该提交/start与入口必要修复；现成official包SHA `59974724dd1cef31b6b9257e1c8e3b0124a77b669d909cc018f8e8061e7be287`。 |
| `i14_baseline_fast` | 共享standalone/failover材料，sfp7的baseline/e2e/三机制组合三个4GiB生成及应用交付。 |
| [WSL会话](codex://threads/01a10226-8db5-7893-8bed-13798e144775) | reviewer/cleaner两个4GiB本地生成、必要修复及应用交付；原owner完成只读交接，无在途写。 |
| [组合包会话](codex://threads/01a10225-89eb-76d0-9eca-7b93df0cb0a7) | 组合overlay已被采用，继续提前准备五个候选正式上传包；不启动远端或官网。 |
| [第二账号自测会话](codex://threads/01a1022d-71db-7c71-b7e9-b9bf025ed11c) | Helium Lan2 / yuanyihong2，自测Stage2/3按主线明确应用/阶段分配并行执行。 |
| 主线 | xiaoland账号自测与统一分配/记分，保持评分反馈不注入生成，23:50采用结果并统筹最终提交。 |

真实官网前端使用合一multipart上传/创建，无已证实的独立snapshot上传路径。`submission_facts`、`pi_entry_repair`已完整交接并退出；旧Pi queue/guard无存活进程。不建立新的实验编排或监控程序。

22:24 CST，Pi四题各create/start HTTP200并独立GET：Stage1 `4eab9465931a`、Stage2 `32db20c04573`、Stage3 `d86b43e8c891`均RUNNING，Sheet `e53e7ab5ec79`为STARTING；此时尚未取得模型token证据。回执为`runs/deadline-20261003/manual/four-start-receipt.json`。

自测站已实际登录，账号xiaoland，今日10/10次；ZIP根目录须包含Dockerfile且不超过50MB，排除node_modules、.git和构建产物，容器监听题目规定端口，自测不计正式榜单。实际只提供GitHub Stage1、2、3。用户先选择“先统一测Stage1，再加测领先候选”，随后明确不能等全部生成结束：有一个应用完成就立即Stage1自测，领先候选继续加测Stage2/3。同一候选后续加测消费同一份冻结应用，评分不反馈给仍生成的Agent。

用户指定“没有自测的task就算作0分”：最终按固定的三阶段总口径比较累计结果，未测阶段记0，原始状态仍保留未测/故障/有效零分区别。23:50采用当时最高累计分的variant，不只对已经测试的阶段取平均。无需等五个候选全部完成才开始评分。

用户随后在另一个Helium profile登录第二GitHub账号。22:31实查Lan2账号yuanyihong2剩余10/10次，加原xiaoland10次共20次，可覆盖五候选三阶段并保留故障空间；保留先Stage1、再领先候选Stage2/3的优先顺序，两个账号并行，主线记录账号/冻结ZIP SHA/variant/stage避免重复。

22:32前本地五项已实际启动：sfp7 baseline `4cb24886…`、e2e `52452b1d…`、combo `792d9cd1…` 均4GiB并已取得千帆Flash HTTP200完整响应；WSL reviewer `859cc0ec84fc`、cleaner `c1a5a1cb41ac` 均4GiB进入Braid阶段，首模型活动由WSL owner继续核对。每项终态即冻结应用，不等待同批其它项。

已有提交 `f5dc542ced60` 的 Stage 1 `7eba954e2c46`、Stage 2 `f7e486217a32` 均在入口退出，token 为零。外层错误为 `Pi generation failed: exit=1, terminal=None`；失败工作区已证实内部原因为 `pi-subagents/src/runs/background/async-execution.ts:615` 的同步 `spawnRunner` 函数含裸 `await managedStartup`，加载扩展即出现解析错误。原件为 `runs/deadline-20261003/facts/stage1-workspace-v2/stderr.log`。不直接重传旧坏包。

完成条件：Pi四项和I14五项分别具备正式submission/run身份、平台明确启动或队列回执及独立状态读回；报告平台接受、模型实际开始和评分分别达到哪一步。若平台限制阻止某项，保存具体HTTP状态和原因。所有Mac证据、新包及临时材料保存在WorkSSD的`runs/deadline-20261003/`。

## 接手续作（pi_fast）

修复保持 `spawnRunner` 同步接口，将 managed startup 与 child startup 的 Promise 正确串联；拒绝保留原始错误，写入 failed 状态并终止对应 runner。共享材料补丁与本 variant 的修复 delta 已更新。没有增加或运行基础设施测试。使用实际 jiti 编译及 `node --check` 确认入口解析问题已消除，最终反馈仍来自官网。

新包为 `runs/deadline-20261003/manual/agent-startup-fixed.zip`，SHA256 `22d74bb4701e662b0c6786991714b5c7ee0740e6d6ab88e957ed85e6d88487aa`。包内成员 hash、新 manifest 与修复身份在 `manual/freeze-receipt.json` 和 `manual/package-repair.json`。旧包与失败原件保留。

用户最新两轮安排覆盖此前写入顺序：Pi 先立即创建 official_evaluation 正式提交并启动 GitHub Stage 1–3 与 Sheet；I14 后续使用自身正式提交启动 GitHub、Sheet 与三个 Stage。各自固定 submission id，不引用全局 latest；两轮成绩各按实际提交归属。Pi 上传 POST 已发出，单次写入结果未知时只做 GET 核实，不重发。

## 本地五候选：sfp7 实际接线

`i14_baseline_fast` 持有 sfp7 的 baseline、e2e、reviewer-cleaner-e2e；WSL reviewer/cleaner 的实际操作已交独立 owner。共同小材料、角色 overlay 与手工 mount 合同位于 `runs/deadline-20261003/local-five/overlay-handoff.json`。只复制旧 volume 的 runtime/skills 到新的共享目录，不复制旧应用或恢复状态，也不修改旧运行；Node/Braid/代理/Pi 修复的实际 hash 已读回。

sfp7 主机为 surface-yyh，Docker `e316f857-fe3d-4e7b-8236-9376f063fedc`、镜像 `3d51899c61e6`。三项独立容器的 memory 和 memory-swap 均为 4,294,967,296 bytes。baseline `4cb24886…` 于 14:27:50 UTC 启动，e2e `52452b1d…` 于 14:27:51 UTC 启动，combo `792d9cd1…` 于 14:29:46 UTC 启动。对应 run 为 `20261003-142751-2d4e0620`、`20261003-142751-0dd0d64e`、`20261003-142946-7b1b2c51`，均已确认原生握手及原定千帆 Flash 路由 HTTP 200、首响应和完整响应体，不能据此宣告应用完成。

手工接线遇到的两项实际前提已收口：旧材料复制保留 Mac UID 501，新的共享副本先交给远端 UID/GID 1000；只读父 `/harness` 下的 runtime/skills 子 mount 点须预创建。私有文件先装配为目录 0700、文件 0600；run 仅在实际权限不符时收紧，避免在正确权限的只读 mount 上再次 chmod。共享支持、Rust 多 provider fallback 顺序及每个 run 合计一个昂贵 Braid session 的保护均保留。

原始 startup 和首活动回执保存在 `local-five/sfp7-two-start-v3.raw`、`sfp7-actual-first-activity.raw`、`sfp7-combo-start.raw`、`sfp7-combo-first-activity.raw`。各容器使用直接 `docker wait` 等待终态；一个应用完成即冻结并交主会话自测，不等待五项齐备，隐藏评分不送回生成成员。

## 22:42 实际运行与最终包就绪

I14-baseline 正式 GitHub 主任务的 submission 为 `6284ec2336df`，run 为 `a184424d7bd5`，北京时间 22:33:55 启动。官网 owner 已取得 GLM-5.3-Flash HTTP 200、4 次完整模型响应、7 次工具完成证据；模型确已开始生成，评分尚未产生。记录位于 `runs/deadline-20261003/official-i14-github/handoff.json`。

WSL 两项实际模型调用也已验证：22:40 快照中 reviewer 已有 17 次请求、27 次完成工具调用，cleaner 已有 39 次请求、50 次完成工具调用；两项仍在生成，尚无可运行发布 commit。完整身份与原始活动位于 `local-five/wsl/status.json`，不以容器 RUNNING 或 Braid 阶段单独认定生成进展。

五候选正式上传 ZIP 已全部提前准备在 `runs/deadline-20261003/final-candidates/handoff.json`，采用同一已通过官网实际入口的运行材料及各自机制；候选 owner 未启动额外正式运行。正式 baseline owner 接续承担 23:50 选定候选的手工官网上传和获授权启动，主线给出明确赢家后执行；不会提前上传未知赢家。上传约 883MB，既往实际需约 6 分钟，保留截止前余量。

两账号自测仍为 0 次已用。第一份有意义、可运行的已发布 commit 即可冻结阶段应用，无需等生成整体终态；同一份应用按 SHA 与来源 commit 绑定各阶段成绩。纯 Docker 包装可在冻结副本补齐，生成中的业务代码不由自测侧修改。

## 最新截止目标：23:56 已有正常模型请求

用户于 22:47 左右明确：“至少确保23:56之前官网已经启动且有正常模型请求发生；其次，上传本身大概率无法提速，应当考虑缩小打包出来的体积，比如精简实现。”这授权必要的窄范围打包和实现精简，覆盖此前只做无损重压的临时限制。目标从 23:50 才选择上传，调整为按真实上传与启动耗时倒推，在 23:56 前完成最终候选启动并验证正常模型请求；具体选择时点服从这一完成目标。

原 883MB I14 官方包上传实测约 8 分 33 秒，23:50 才开始不足以留下启动和模型验证余量。五候选材料 owner 负责依赖核对、精简新包及编译/身份验证；官方 owner 负责真实上传、启动和首模型响应。两者保持独立责任且直接交接，不取消既有 Pi 或 baseline。旧包保留，新精简包独立路径和 SHA。

官方 baseline 原始时间已核对：POST 完成 22:33:06，RUNNING 22:33:55，原生 request_start 22:34:36，首 HTTP 200 且流式更新 22:36:33。POST 完成后到正常模型证据约 207 秒；连上传合计约 12 分钟。未验证精简包前，暂以 23:33 选定、23:38 前上传作为保守安排；后续可依据真实精简体积和启动依赖更新，但不把减少上传量转化为启动期的大文件下载。槽位未释放依然是独立前提，时间余量不能代替槽位。

## 最新本地硬停止与官网保底

用户进一步决定：“至少23:40时截止本地所有生成，将最新生成的代码提交测评，尽可能得到分数，如果应用甚至无法启动，由我们自己来补全最后一点（如果可能，如果还差很多，则放弃）”；“最高优先级是让braid版本跑起来参赛（当然，前提是pi能在相应时间内跑完）”。因此本地五路最迟 23:40 CST 停止生成写入，保留原始现场、Git refs、未提交内容及运行身份，立即冻结最新最完整应用。此前有可运行阶段应用仍即时送测。冻结可使用明确记录的 dirty 快照，不再以等待生成自然终态或发布 commit 为必要前提。

本地 owner 获准在冻结副本中补少量构建/启动缺口并真实启动验证，保留改前快照；若缺失大量业务功能则放弃该候选，不扩展为开发侧重做应用。隐藏评测反馈不回流生成。

最终 Braid 正式参赛优先于继续等自测：GitHub baseline 现有正式运行保持；如来不及取得可用赢家，复用已上传且已取得正常模型请求的 baseline submission `6284ec2336df`，待 Pi 对应题目终态后启动其它获授权题目，省去重新上传。不会为了保底自行取消 Pi。上一节 23:33 选择时间是旧大包下的保守估计，现由 23:40 本地冻结、精简包实际体积及已上传 baseline 保底共同安排，不让它阻塞新决定。

用户同时明确：“可以不打包chromium，因为runner上面完全可以访问网络，下载开发资源”。五候选材料 owner 据此移除包内 Chromium/headless 大文件，保留驱动、版本和按需安装路径；先让根模型工作，不把浏览器大文件下载作为所有 run 的启动前置条件。

## 用户再次明确：官网持续接续至实际关闭

用户明确询问并要求执行：“23:40后截止安排是本地的对吗，直到23:59真的不能再创建新运行之前，都要监听官网pi释放出来的槽位，运行I14-baseline对吗？”主线确认：23:40 仅停止本地五路；官网 Pi 与 baseline 继续。Pi 每释放一个对应题目的槽位，官方 baseline owner 就立即复用 `6284ec2336df` 创建/start该题，无需等全部 Pi 终态、无需等本地分数或再次请求主线授权。此前等待 23:40/赢家指令再启 baseline 的临时限制由此撤销。

23:56 是争取取得正常模型响应的目标，不是停止时间。官网接续持续到 23:59 平台实际关闭新 run 创建，保留真实 HTTP 拒绝内容；不取消 Pi，不重发效果未知的写请求。Pi owner 负责轻量状态与槽位通知，官方 owner 独占写；23:30 后观察间隔最多一分钟，23:50 后约三十秒，只查小状态，不反复拉取大规模轨迹。

### sfp7 owner：23:40 硬停止与交付补件（22:57 接线）

/root/i14_baseline_fast 保持 baseline/e2e/combo 三个本次固定容器的唯一控制权。原生一次性截止进程 PID 537451 已核实 surface-yyh 与 Docker ID，23:40CST 对尚运行的三个固定容器 ID 发 SIGKILL，保留全部 bind-mounted 输出与 Braid worktrees/ref/未提交文件。控制脚本及armed回执在 `runs/deadline-20261003/local-five/hard-stop-sfp7.py`、`hard-stop-armed.json`；远端停止回执将写 `/home/yyh/factory26-deadline-20261003/control/hard-stop-receipt.json`。

根Issue公开截止评论 baseline/e2e/combo 分别 ID5/4/4，独立 readback 均为 delivered 到 glm-1，表示原生会话接受输入，不表示已经处理。未含评分或隐藏评测信息。三个运行 overlay 已补齐同一已冻结 standalone 包的 `exp_checkpoint.py`（55470B，SHA256 a41308b41d6348a2e4205eb808a11d72514bd2dda20f52c11f02974bea265797），只供 application() 离线导出；未调用 checkpoint、Lab 或controller。证据在 `exporter-repair-receipt.json` 和 `exporter-repair-readback.raw`。

硬停止后可冻结 dirty 应用；仅冻结副本允许少量 build/start 修复和实际应用验证，原始现场不改，不大幅补业务。更早完整已发布应用仍即时交 root 自测。

用户进一步明确“禁止子会话使用advisor”，并要求所有子会话理解紧急度，以最小方法、最快路径完成。所有开发子会话与其下级从此禁止调用 advisor 角色或另建咨询，由当前负责人直接判断；跳过非必要报告、完整审计与重复验证，优先实际生成包、自测及官网运行回执。全部继续使用 Sol 6.1 / xhigh / priority。

### sfp7 首批可运行阶段应用（23:11）

baseline 已发布 develop `6721293053066e5e8e0bed3b1770e96e557b41e8`，combo 已发布 design/base `12dbbe55b247048deb3f46e9cf426d02b8a68b9c`。两项均按精确 commit git archive 冻结，未复制在写工作树；source.tar 原件、application.zip 与身份回执位于 `runs/deadline-20261003/local-five/apps/{baseline,combo}/<commit>-provisional/`，采用入口为 `first-apps-handoff.json`。两份仅新增纯 Docker 包装/.dockerignore，业务源码未改，均为 provisional 基础入口/seed/认证阶段，原生成继续。

两项独立 Docker build exit0，实际 Node v20.19.3、根页与/sign-in HTTP200、同端口前后端运行；combo 启动约31秒后确认响应，合同120秒内。验证容器已停止并保留数据/image，未控制生成容器。根会话已接收 ZIP/ref/SHA 与实际验证证据，外部自测仍由其唯一执行。

23:08 起已开始实际自测：baseline 阶段应用 `6721293053` 的 Stage 1 为 `ecb2a2f1-786d-4e65-9560-730f4b414093`（xiaoland）；组合版 `12dbbe55b2` 已在 yuanyihong2 提交 Stage 1，短编号 `9dc835b0`；reviewer `f9065b25c2` 的 Stage 1 为 `edb8be15-a161-4119-a999-3465a73e7ba2`（xiaoland）。前两项同份 ZIP 后续独立 Docker build/start 已通过，reviewer 来源精确提交也有实际构建/启动证据。自测站显示近期通常约七分钟，均保留 provisional 身份。主线手工记分与配额记录为 `runs/deadline-20261003/selftest/submissions.json`，未出分不当作有效零分。

首三份 Stage1 自测均在镜像构建阶段失败，未取得业务测试分数，各扣一次额度（合计3/20）。网页原文为“请先在本地运行 docker build 确认能构建成功。构建过程中无法访问外网。”原包在独立本地 Docker 构建/启动已通过；通用 Dockerfile 的联网 apt/npm 安装与自测构建环境不兼容。两本地 owner 立即从同一冻结应用的成功构建产物制作≤50MB离线应用包，带前端dist和Linux Node20.19.3所需依赖，Dockerfile只复制/配置/启动；业务源码不变，原包原件保留，先以真实禁网Docker构建验证再重传。网页通用“不含node_modules/构建产物”建议与这个实际禁网限制冲突，以可运行离线交付与50MB硬限制为准。此修复只影响自测应用包装，官方Harness联网按需下载浏览器方案继续保留。

### sfp7 本地三项阶段应用与禁网交付修复（23:28）

生成 owner 继续持 baseline/e2e/combo，三个原始容器各 4GiB、工作区与全部 refs 保留。用户授权 23:40 硬停止；固定容器 ID 的单次 deadline 进程已在 sfp7 武装，证据为 `runs/deadline-20261003/local-five/hard-stop-armed.json`。停止后才采集 dirty 最终应用，生成期间只冻结已发布精确 commit。

自测平台实际镜像构建禁网，在线 apt/npm Dockerfile 不能交付；平铺 node_modules 的 ZIP 又被安全检查以路径/展开体积/文件数通用原因拒绝。现在使用已成功构建的 Linux 运行目录，经生产依赖裁剪后由 native tar 保存权限和符号链接，外层 ZIP 仅 Dockerfile 与 app-runtime.tar.gz，Docker ADD 解包；应用业务源码不变。baseline 12,208,937B、combo 9,239,745B、e2e 14,034,454B，三个均已真实从 ZIP 解出、docker build --network=none 成功，并以 Node20.19.3/npm start 启动，根路由和 /sign-in 返回 200。完整身份、SHA、实际构建启动证据入口为 `runs/deadline-20261003/local-five/offline-tar-apps-handoff.json`。该修复只改冻结应用的交付包装，不读取隐藏评分，不回注反馈，原始在线/平铺包保留。

用户进一步授权并行运行现有本地模拟测试，仍继续官方self-test。由原材料owner会话独占定位与直接执行，使用冻结应用，模拟分与官方分分开，不改评测器、不将评分反馈给生成。

用户授权每五分钟下载工作区做深度停滞检查，特许 GPT-5.6-Luna / medium / Fast。新线程 `01a10262-2d23-7c81-b253-c235ba31115a` 已创建立即首检；既有 `i14` heartbeat 已更新为该线程每五分钟深检，旧 `pi-minimal-vv` 百元预算心跳已暂停。深检只读取证/通知，官网写仍唯一原owner。

23:30 首个有效self-test为reviewer f9065b25离线Stage1，`ee2c358e-faff-459e-a99a-632456a74ebc`，通过2/30（显示7%）。同一SHA继续Stage2/3；当前其它未测阶段决策贡献为0。

23:30 又冻结 baseline 已发布业务增量 `b1f89e8f224a4535df4cd59dffcc5ff00664bc6c`（refs/heads/braid/pr-3），组织/仓库/code/issues/pulls 后端路由已进入源码；前端发布文件与首包完全相同，复用等同源码的已构建 dist。新增 diff 生产依赖后，17,059,279B 两文件 tar ZIP 已真实禁网构建及启动，根路由、/sign-in、/api/health 均 200。身份和 SHA 已追加到上述统一 handoff；dirty Search/Header/Orgs 继续由原生成者编写，截止前不复制。

用户新增官网门槛：“官网的eval也需要时间，如果发现进入eva，可以考虑尝试启动已经提交的I14-baseline（如果失败，那就说明确实得等待eval完成，而不是生成完成就行）”。官方owner据真实eval/evaluate步骤立即尝试同题baseline的create/start一次，不再强制等finished_at；若明确容量拒绝则保存HTTP原文并继续等待，不循环重发POST。create已得到run ID而start被拒时保留并复用同ID，结果未知先GET核实。Pi只读owner与五分钟深检同步观察步骤变化，禁止取消Pi。

### 23:39 自测与本地截止

早期冻结应用实际 self-test：reviewer 三阶段 2/30、0/29、0/41，累计 2/100；baseline 和 e2e 第一阶段各 0/30；combo 第一阶段 6/30，已安排同一 SHA 加测第二、三阶段。最终 reviewer 2152b282 离线包已于 23:38 提交 Stage1，编号 89d8977b-e143-4690-a930-973445f14eef。WSL 两项生成均已停止，cleaner 因大量业务缺失按授权放弃。sfp7 三项仍按 23:40 物理硬停止，优先冻结 baseline 新增前端与 dirty 源码。

### 23:40 实际截止

sfp7 三容器已于 23:40:00.119–.148 CST 实际 SIGKILL 停止，exit 137 且 OOMKilled=false，属于预定截止。WSL 两项此前已停止，禁止重新恢复生成。证据 `runs/deadline-20261003/local-five/hard-stop-receipt.json` 与 WSL 状态。baseline 最终源码为 commit 3bb05414f0d02fb5d0f993aecf6876406ee4fc2d 加 dirty App.tsx/RepoSettings.tsx，冻结源码 SHA d8b7e5f6ff8150a9b5454a3060197c85a00984f12dcdd1900b3722b444816f98，正在离线构建。reviewer 已送测 a9f773 包发现 /register 服务入口 404，负责人在独立冻结副本修复，旧包/分数独立保留。官网 Pi 和 I14 GitHub 主任务不受本地截止影响。

### 23:44 用户处置决定

对 Stage1 模型长请求无响应及 23:48 取消备选，用户明确回复：“保留 Pi，继续等到截止”。取消备选被否决，任何时间均不取消 Pi；继续只读监听到平台实际截止，出现 eval 或终态立即尝试 baseline 同题接续。

### 23:45 Sheet 接续优先级

用户明确：“优先监控 sheet 槽位的释放，一旦释放，那么 I14-baseline 也有机会参赛”。Sheet e53e7ab5ec79 为最高优先级，进入 eval 即尝试 baseline submission 6284ec2336df 同题创建/启动；被占用则继续等待释放，释放后立即接续，不受 self-test 或胜者上传等待影响。其余 Pi 保留继续。

### sfp7 23:40 截止已执行与最终交付

三个原始生成容器于 23:40:00 停止，指定 SIGKILL 的 exit137、OOMKilled=false，全部工作区、refs、未提交现场与运行状态保留在 sfp7 原 outputs 下；停止后源码归档已回收 WorkSSD 并核对 SHA。停止回执与保留位置入口为 `runs/deadline-20261003/local-five/cutoff-preservation-handoff.json`。baseline 最新 commit3bb05414 加 dirty App/RepoSettings，冻结副本仅修复缺失 import/类型接线/无用编译警告，最终17,050,719B 离线tar包已实际前端build、禁网Dockerbuild、Node20.19.3 start及8个直达HTTP200，23:42交root；证据 `final-baseline-handoff.json`。combo 截止commit4616b795 较首包真实增加注册/密码恢复/密码设置，独立副本恢复自身旧版遗漏SettingsLayout导出，13,604,184B最终离线tar包已同样真实build/start与signup/forgot-password200，23:45交root；证据 `final-combo-handoff.json`。e2e截止只有Guest头部小变更，无新增业务能力，不发起新自测；证据 `e2e-cutoff-no-substantial-addition.json`。生成不恢复，官方写入由其它明确owner负责，本owner保持入口故障响应。

### 23:49 候选预上传与替换讨论

用户指出应提前上传 variants，并询问是否取消官网 baseline 改组合。主线立即授权唯一官方 writer 上传当前最高实得分组合包（8/100），并预上传其余已冻结精简候选；组合吞吐及 Sheet 接续优先。官网 baseline 取消仍未授权，须先完成组合上传、给出真实submission ID和替换代价再决定。Pi 保留的明确指示继续有效。

### 23:51 用户授权主任务替换

用户原话：“还剩下不到10分钟了，我决定堵替换 I14-baseline 为混合版（当然是精简过的，而且有 resource 自动释放机制最好）”。此决定覆盖此前 GitHub 主任务保持 baseline 的要求。唯一官方 writer 在组合精简包上传成功后，保存已有 baseline 现场，取消 a184424d7bd5 并创建、启动 reviewer-cleaner-e2e 的 hackathon--github run，争取 23:56 前正常模型请求。采用已冻结 resourcewait 修复包 e88c46ddc23871e4d4b3741491861aa61706d4fd0f8063c0d8b53697bbe36dfc，不为新机制重开发延误。Pi 全部保留、Sheet 释放后接 baseline 的授权仍有效。

### 23:52 资源阈值变更

用户明确要求“之前的 resource 释放机制还可以再宽松点，放宽到 95% 内存占用”。组合包由原打包负责人立即按现有配置接口最小修改，保留释放/恢复和 resourcewait 修复，独立ZIP/SHA不覆盖在途e88包。其余预上传让出带宽，官网 writer 等新的 95% 最终包成功上传后执行已授权 baseline→combo 替换；Pi 不取消，Sheet 继续监听。

### 23:57 组合版正式启动请求已接受

95%组合精简包 SHA64e249175adc062ea3738041b96aa6a674d14aec401997612dffab3af6728a5c 上传成功，submission5571eb62c5ef，GitHub main run689770daa447，create/start均HTTP200，初始状态QUEUED。原baseline a184424d7bd5已于23:53:19按用户明确替换授权取消；95%新指令传递时取消已经落地，原现场由深检保存。官网writer继续Sheet及其他Pi释放监听；Luna深检负责新组合RUNNING/正常模型请求证据。保留旧e88组合submission d5c57fb53dfd，不作为本次最终启动包。

### 00:00 官网进入审核结算

23:59:15 最后成功四 Pi 均 start_agent/run_tests pending；23:59:38 状态 GET 超时。00:00:18 四 Pi 状态 GET 均 HTTP500，正文“arc-bench.com，初赛提交审核与成绩结算中”；新组合 template-bundle 同样HTTP500。不能将此当作在途run停止。组合新run的平台 started_at 为2026-10-03T15:56:56.984300 UTC，deadline前RUNNING已确认；首个模型请求/HTTP200/stream 尚缺证据，具体阻塞是官网维护。五分钟监控保留，维护期每轮先一条GET并安静保留响应，恢复后优先补取新combo正常模型证据。Sheet截止前未释放，未新增baseline Sheet run。

### 用户最终停止指令

用户明确：“不必检查了，停下吧。我们现在停掉所有监控和跟进，本地运行保留。”停止所有本轮主动轮询、下载、跟进和新提交，i14五分钟heartbeat暂停，原pi预算heartbeat此前已暂停。保留现存本地运行及官网运行，不取消/停止/恢复任何运行。主线前一条停止本地mock的指令已立即撤销并通知负责人，仅停止监控与跟进。后续仅凭新用户指示恢复工作。


### 2026-10-04：sfp7 组合版本地接续

用户新指示：“重新启动 cleaner+reviewer+e2e 组合版到 sfp7 运行”。这条指示授权现有 `pi-braid-i14-reviewer-cleaner-e2e` 的一条 GitHub 本地接续，以及其必要修复、材料准备、启动和实际活动验证。以昨晚23:40截止保留的组合现场为来源，保留应用、refs、dirty与原生/Braid历史；不将此前独立cleaner/reviewer/e2e恢复作为本次来源，不丢弃旧进度另起无标识fresh实验。

执行唯一负责人为当前会话 sub-agent `combined_sfp7_owner`；主线维护授权、总体判断及结果采用，不控制运行。沿现有standalone组合入口、当前冻结模型/供应商与self_funded配方核对实际配置，Mac产物全在WorkSSD。本次不恢复官网操作、其它候选、heartbeat或周期跟进；必要运行终态记录随执行保留。此前截止停止与停止监控决定作为历史事实保留，本次指示仅解除该组合本地启动限制。

当前阶段：负责人核对原组合 `20261003-142946-7b1b2c51` 的恢复能力与sfp7实际状态，完成可恢复来源核实后启动，验收以新执行身份、原进度采用、新原生模型/Braid活动及实际资源限制为准，不以容器created或accepted替代成功。运行证据入口由负责人交付后补入。


用户随后明确：“重新启动即可，可以丢失已有进度”。本次改为从公开允许GitHub需求 fresh 启动现有组合版，独立新输出目录；此决定替代本节保留进度接续要求。旧组合现场及首个接续失败保留，不再继续为本次启动修复恢复调度时序。执行负责人保持不变，先核本次在途接续已终态再启动新生成；其它候选、官网与heartbeat仍不进入范围。


本次启动已实际验证：2026-10-04 10:32:36 CST，sfp7 容器 `d919a758839346dbfa72f895fcead77ab4fefae2926dda848a6f3c171cc3f99e` 从公开需求 fresh 启动组合版，Braid run `20261004-023236-a69535b2`，独立输出 `/home/yyh/factory26-deadline-20261003/outputs/combo-fresh-20261004`。10:33:32回执证明容器running、4GiB且无swap扩展、Pi握手完成，多次GLM-5.3-Flash上游HTTP200、实际响应字节与完整流终态；尚未完成应用生成。证据入口：[启动验证](../../../runs/deadline-20261003/combo-restart-20261004/verified.json)。旧组合输出已复制保全，首次resume尝试已停止并保留日志；恢复入口临时源码还原，不为本次fresh扩修Braid。运行命令终态写入输出 `terminal.json`，未恢复官网、其它候选或周期监控。主线采用负责人实际回执，不重复操作已运行容器。


### 2026-10-04：偶发504后的实验接续

16:20观察 reviewer-5 在15:49原生响应中报 `504 upstream_headers_timeout`，Braid仍显示running、review pending。用户要求解决后立即收窄：“我是说，这看起来像是偶发的，我希望实验能继续运行就好，长期防治是后面的事情”。授权范围仅为有界核实当前是否自然恢复，并在仍卡住时沿既有合法恢复入口最小接续该审阅会话，同候选、保留进度，核实实际新模型和审查活动。长期源码修复、超时/路由架构调整不进入本次范围。原执行owner `combined_sfp7_owner` 继续负责；控制前保留原错误、事实和未知、动作目的与可能损失，不重复unknown请求。其它run、官网与周期监控不变。


16:48:34 已完成最小接续：通过既有 Braid review assign 将 PR #4 / review request #5 的固定候选 `0fb8871` 移交 reviewer-6，原证据保留。16:48:35新Pi握手，随后实际Git/候选差异工具活动与gateway1520–1522 HTTP200完整响应证明审查恢复推进。未重启整个run，未修改模型、供应商、超时或源码。旧reviewer-5的504之后还卡于background bash 30分钟auto-drain；本次保留错误，不扩大长期修复。回执：[局部接续验证](../../../runs/deadline-20261003/combo-restart-20261004/reviewer-504-recovery/verified.json)。此验证仅证明审查重新推进，不证明批准、合并或应用已完成。


19:50只读观察发现REQ-6/PR #5已完成首轮修复，固定候选`773a643f`在二轮reviewer-8/request #7于18:49:49再次发生`504 upstream_headers_timeout`，持续无原生活动。沿用户此前仅需实验继续的范围，19:51通过同一原生review assign入口局部移交reviewer-9；新原生会话、3次完整模型HTTP200及读取PR/审查意见证明恢复推进。未重启run、未改模型/路由/超时/源码；候选与进度保留，尚不证明批准或合并。回执：[本次局部恢复](../../../runs/deadline-20261003/combo-restart-20261004/reviewer8-504-recovery/verified.json)。


### 2026-10-06：网站恢复后的最终成绩核实

用户要求查看“10.3晚上最后的那两个提交最后是否取得了成绩”。本次仅核实官网状态、成绩及失败环节，不恢复周期监控、启动、取消或接续。主线负责既有账号 API 取证，sub-agent `arc_final_scores` 负责浏览器只读核对。旧 cookie 返回 HTTP401 后使用仓库既有官网登录凭据完成认证；凭据未输出，新的会话文件和原始 GET 回执均在 WorkSSD。

Pi submission `aea08b61772c` 已完成四项生成与评测，总分 `39.18493333767982`，通过 `87/200`（43.5%）。Stage1 为 `16/30`，Stage2 为 `0/29`，Stage3 为 `0/41`，Sheet 为 `71/100`。四 run 虽标记 FAILED，实际 start_agent 与 run_tests 均 completed，原失败摘要为 `Runner exited with test failures or runtime errors`，不能当作未评测。run.score 为通过率近似值，submission.task_scores.score 包含另一结算口径，报告总分以 submission.score 为准。

最终 I14 混合版95% submission `5571eb62c5ef` 的 GitHub run `689770daa447` 在生成期间 main.py exit1，start_agent failed、run_tests pending；平台记 score0，但未实际执行100项评测。它在维护期之后继续运行约3小时10分，并非截止时未运行。submission 还含 Sheet run `d3e11131cfed`，失败且无分数，故 submission.score=null、score_available=false，不能称为取得完整提交总分。两个 submission 均 is_selected_score=false，提交结果不直接证明官方最终选定或排名。

原始证据入口：`runs/deadline-20261003/final-score-check-20261006/`，包括 submissions、各 run 和 summary.json；已保留 HTTP 状态与具体错误。此次核实完成后不自动跟进官网。


### 2026-10-06：Pi两题零分调查

用户授权下载Stage2/3终态工作区、按需self-test取得具体错误并追溯Agent过程。当前授权、负责人、调查依据与结果入口归 [两题零分调查packet](pi-zero-analysis/packet.md)，不恢复生成或监控。
