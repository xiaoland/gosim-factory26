# 参赛额度止损与交付闭环

## 当前调查：Sheet 08226 是否卡住（2026-09-26）

现场补充已确认：1217 个原有文件的 SHA256 与 18:01 快照完全相同；新增 WAL 为零字节，没有遗漏在 WAL 中的后续事务。包内 Braid 的 SHA256 与冻结 manifest 一致。已直接提取该二进制的候选 SQL（非沿用当前源码），只读查询显示 Issue #2 / PR #1 的 unassign 分别占据各自队首，target_profile 为 NULL；#3/#4 的 assign 位于其后。根任务原始 prompt 要求“根 Issue 之外同时最多指派三个 Agent”“已指派但暂时空闲的 Agent 仍占用资源”，其清理旧指派有提示依据，不能把合法 unassign 触发全局停滞归责于模型误用。冻结 ELF 静态控制流也已对应：Issue/PR 都只处理队首候选，目标 profile 为 None 时在调用取消指派收尾前直接返回。此次把队首阻塞归因从当前源码推断推进到冻结 SQL、冻结数据库和冻结二进制的相互核验；完整 dirty 源码与运行时栈仍未取得。追加诊断完成，详见原 Sheet 报告及 `user-preserved/binary-control-flow.md`。

2026-09-26 后续：用户已取消运行，并提供 `/Users/lanzhijiang/Downloads/08226c772b7a-template.zip`，要求继续分析现场。本轮仅做归档取证与报告更新，不执行包内程序或修改实现。归档 SHA256 为 `10fb5bd1056fdecf88e8452c06bbf6953225f81b16d7e958363a0303ce84bc6b`；对照 18:01 快照，原有文件内容全部相同，只增加空 WAL 和 32 KiB SHM。正在用包内精确 Braid 二进制核验候选 SQL 与取消指派处理链，证据在 `analysis-sheet/user-preserved/`。

用户要求分析 `08226c772b7a` 为何仍在运行、是否卡住。本次授权为针对该 run 的只读诊断：核对平台阶段、最近有效 Agent 动作、活动工作项和未完成工具；不因 RUNNING、耗时或 token 增长单独判定进展。用户正在修改 variant，本轮不修改实现、远端工作区或应用，不暂停/取消/重启 run，不创建新的监控或实验。持续证据保存于 `runs/competition-budget/20260926/root-only/analysis-sheet/`。

09:57 UTC 首次取证确认仍在生成、评分 pending。工作区 6 个原生会话的最后回合为根在 08:59:25 正常完成；全部已记录 toolCall 都有返回，11 个后台 Bash job 均已退出或终止。根确已收到第一批交接、PR #1 合并，并在 08:58:47 指派第二批 #3/#4；CLI 显示 deepseek-4/glm-5，但数据库只有 desired assignee 与 pending assign，未创建这两个实际 assignment/会话。此处不能把“指派命令成功”当作“Agent 已启动”。

初步定位调度队首问题：根在 08:58:27 先取消已完成 #2/PR1 的指派，两条 unassign 保持 pending；旧 assignment 已 retired。当前代码取不到这些事件的 target_profile，于是所有 profile worker 跳过它们，却仍反复取同类最早事件，后面的 #3/#4 assign 无法处理。status 的 pending_events=2 对应两条 assign（全库 pending 为20，并不是仅两个事件）；它们又阻止 quiescent。正在核对第二份快照与冻结版本边界，尚未修改或干预远端。

诊断已完成，见 [Sheet 停滞报告](results/08226c772b7a-stall.md)。10:01:29 UTC 第二份快照确认核心数据库内容与六个原生会话逐字节不变，最后回合距此约62分钟；明确是任务未继续派发，非正在评分或长 Bash 等待。当前源码能完整解释取消指派事件堵住后续 assign，但冻结包和当前代码均为 dirty，未取得冻结脏源码，保留具体二进制归因限制。建议暂停保存现场，先修调度生命周期；本轮未暂停、取消、恢复、修复或增加监控。

## 官网 Hackathon 运行总览（2026-09-26 核对）

用户要求用树状图消除原始生成、重放和失败记录的混淆。根据本地官网 journal、Playground 状态与相关 packet，已核对 15 条 run：8 条取得有效评分、4 条未进入评分的失败、3 条取消；其中 08226 的取消由用户在后续调查中确认。范围仅为已有记录覆盖的 9 月 24–26 日官网 Hackathon，不含本地验收、模型探针或其他 benchmark。

```text
官网 Hackathon
├─ codex-base 本地应用的官网重放
│  ├─ GitHub a11ce90b4611：1/100
│  └─ Sheet e263fcdbc5aa：测试枚举失败，未评分
│     └─ 同应用重试 963db7dca6c2：1/100
├─ pi-team-mixed 早期批次
│  ├─ GitHub caf2d2f23e13：生成/导出失败，未评分
│  │  └─ 用户手动重试 7207a7fe0845：1/100（重新生成）
│  └─ Sheet 17bffdd4a8b0：曾手动暂停，现已 CANCELLED
├─ pi-team-mixed 协作改造
│  ├─ 首包 GitHub 44db16c4b085：生成中断，未评分
│  ├─ 首包 Sheet 809a7fe683d4：启动被旧 run 占用阻挡，未评分
│  └─ 修正包 GitHub b77e4357a4e1：4/100
├─ K3 根 Agent 对照
│  └─ GitHub 7b533d7bd71b：11/100
│     └─ 原样重放 e45e4ae7110d：14/100（实验 A）
├─ root-only 旧包
│  └─ GitHub 48a591836974：用户取消，未评分
└─ root-only 预算与流程修正版（实验 B）
   ├─ GitHub 097402e69a15：0/100
   │  └─ 原样重放 8d751d76c2a3：0/100（实验 C，已收尾）
   └─ Sheet 08226c772b7a：用户取消，未进入评分（调度停滞现场已保存）
```

当前状态已通过只读 API 刷新：旧 Sheet `17bffdd4a8b0` 为 CANCELLED，finished_at 为 2026-09-26 04:53:43 UTC，原因 `Run cancelled because it was deleted`；因此较早文档中的 PAUSED 仅是历史观察。新 Sheet `08226c772b7a` 当时仍 RUNNING，后续用户已取消并提供现场 ZIP。证据保存在 `runs/playground/<run-id>/status.json`。其他批次对应 `tasks/hackathon-variants/packet.md`、`tasks/issue-decomposition/packet.md`、`tasks/braid-collaboration/packet.md`、`tasks/k3-root-experiment/packet.md` 与各自官网 journal。未上传的中间包和未创建 run 的 Sheet 计划不计数。

## 已完成：097402 原样官网重放（2026-09-26）

用户明确要求：“我希望你能够整理一个应用重放包，然后重新跑一个这个任务的运行。”本次授权为 GitHub 一次原样官网重放，沿用 self_funded 和自带 key，不使用参赛额度，不重新调用生成模型，不修补应用或 Harness。判断前提已澄清：本地账号场景通过不足以认定官网零分不合理，本次用于检验同一应用在干净部署下能否复现零分。

复用上轮已冻结且通过本地 Runner 回放的 `application-replay.zip`，SHA256 `8a904b9d9022bc0f223f11095ccfceda802d97aebb4cdef64df6c3bca62f5645`；36 个应用文件绑定 `0c0a7a6f0fed4aba45c48bbf7d1bfce101fec2ac`。新状态目录使用 `runs/competition-budget/20260926/replay-097402/official`，与旧实验分开。完成条件为官网生成回放、部署、评分终态与证据采集；若仍为零，不能据此证明应用功能全坏或评测错误；若分数改变，只确认重复运行差异，不将差值直接归因给某个未知失败。

重放已提交并启动：[`8d751d76c2a3`](https://arc-bench.com/runs/8d751d76c2a3)，submission `918eeef56f85`，名称 `artifact-replay-097402-clean`，首次观察 `QUEUED`，随后确认 `RUNNING`（平台 started_at 为 2026-09-26 08:43:24 UTC）。包已逐文件对照原 Git commit 核实，见 `runs/competition-budget/20260926/replay-097402/verification.json`。本次仍是原样应用，没有因诊断改变 UI、账号、数据或依赖锁文件。

既有 Sheet `08226c772b7a` 已启动。为遵守比赛写锁，原本地控制器 PID 66498 经 SIGINT 正常退出；完成新 submission/create/start 后立即用原命令与原 journal 恢复，PID 83290，900 秒间隔。没有向官网发送暂停、取消或重启 Sheet 的请求；交接记录见 `replay-097402/monitor-handoff.json`。

新重放由开发侧 `/root/monitor_replay_097402`（gpt-5.6-luna / low）负责只读终态采集，使用 `python3 -m lab.arc_bench.playground watch 8d751d76c2a3 --interval 180`；新鲜状态与日志在 `runs/playground/8d751d76c2a3/`，避免只读监控占用比赛写锁。创建 journal 保留 `official/`。

终态已采集：2026-09-26 09:01:36 UTC 结束，FAILED、0/100、0/47。前端构建成功，08:44:42 后端监听 3000，空库初始化成功；同一应用的零分在干净部署下复现，但仍没有官方逐例错误。回放入口没有生成模型调用；平台却返回 `token_count=19030172`、成本字段 `5.009885` / `CNY`，统计归属未核实，不能把整个 run 写成零 token 或据此断言生成程序调用了模型。详见 [原分析的重放补充](results/097402e69a15.md#原样官网重放结果)。

用户随后表示“算了，就这样吧”。本次 GitHub 重放到此收尾，不追加运行或诊断实验。已核实监控 Agent 为 completed，对应 watch 进程已退出；仍在运行的 PID 83290 是原 B Sheet 控制器，沿用既有授权，本次未停止或改动它。用户再次贴出的 `097402e69a15` 是此前获授权 B 实验的原始 GitHub 生成，不是新启动的另一轮；它与重放 `8d751d76c2a3` 是两个 run、同一份应用。

## 当前调查：B GitHub 0/100（2026-09-26）

用户要求分析 [`097402e69a15`](https://arc-bench.com/runs/097402e69a15) 的 0/100。本次范围为只读取证、隔离复现与记录，不修改 Harness 或生成应用，不启动新的生成或官网评测，也不干预其他任务的实验控制器。先区别部署故障、共享 UI 入口故障与功能契约缺陷，再核验 B 的交接和最终验收是否实际执行。

当前状态：调查及六项定向复验已完成，完整结论见 [0/100 分析](results/097402e69a15.md)。主要断点是子 Issue 的 `@kimi-1` 交接没有路由到根，五个后续模块未指派，Factory 导出了仅 36 文件的账号应用。原样应用通过本地注册、登录和缺少当前密码拒绝检查；官网账号全零的精确失败仍缺逐例证据。本次未修改或提交源码，六个本地 Runner 容器均已清理。下文为随调查记录的阶段证据。

已从官方 API 采集终态：`budget-root-only-20260926`、submission `02321991f315`、`self_funded`，0/100、0/47；生成耗时字段 2540 秒，开始到评分结束约 61 分钟。前端构建成功；07:49:39 UTC 后端正常监听 3000，空数据库已初始化，未见 EADDRINUSE。官方未提供逐例结果，暂不能把 100 个失败归结为同一个原因。证据入口：`runs/playground/097402e69a15/`。下一步读取冻结源码和协作记录，选择最早公共入口作隔离验证。

已下载完整工作区，SHA256 `a0ff3a463f9bd63c7d5ae7670589326684a0c89d201a4d7ba277f6a9670a3cf2`，保存在 `runs/competition-budget/20260926/root-only/analysis/`。交付 commit 为 `0c0a7a6f0fed4aba45c48bbf7d1bfce101fec2ac`。源码仅注册 auth 后端模块，前端仅有账号页面，Header 的搜索只是阻止提交的占位。Braid 终态 `quiescent`、原因为“当前没有可执行工作”；根 Issue 只有首次 turn，随后仅 Issue #2 和 PR #1 执行。当前追查交接记录与根会话为何未恢复，并验证账号入口的实际失败。

数据库确认根 #1 OPEN、#2 CLOSED、#3–#7 OPEN 且未指派、PR #1 MERGED。根 turn 为 07:06:12–07:15:36 UTC；07:44:35 的子 Issue comment #2 明确写“请 @kimi-1 验收合入”，但只生成发往 `issue:2`（origin_echo）和 `pr:1` 的事件，没有发往 `issue:1`。当前 `discussion_changed` 实现只路由到当前工作项、关联 Issue/PR 和线程参与者，不解析文本 @mention 或父子关系。根的最终输出明确等待该交接，因此应归为预期交接未路由，而非已送达后根拒绝继续。另有指引矛盾：原生指令“可指派的 Agent”包含 kimi，但 CLI 实际拒绝 `--assignee kimi`；子任务改用 deepseek 创建 PR。实际合并由 DeepSeek PR 会话执行，关闭理由却误写成 kimi 已合并。`--head` 正确保留实现，没有上一轮的代码丢失/重做。

隔离复验已开始：原样 36 文件回放，沿用已有 GitHub suite，选账号 5 项及全局搜索 1 项，WSL 每场景独立 Runner、2 workers。远端目录 `/tmp/factory26-analysis-097402/`；未调用模型或官网评测。结果用于分辨账号功能与验收定位问题，不将本地 6 项当作官方 100 项归因。

首批结果：注册、登录通过；找回密码与登出原测试失败，但检查公开契约和错误位置后确认测试存在前提错误：找回失败按需求清空密码，测试却只改验证码就再次提交；登出要求 link，原测试查 menuitem。两项不能归为应用失败。首页存在两个 Sign in 链接，原生自检曾因此改为 `.first`，本地 suite 使用 main 作用域则通过；它是官方账号入口失败的候选机制，缺少官方逐例堆栈，不能确认。分析稿见 [本轮报告](results/097402e69a15.md)。

最终复验原始结果 3 passed、1 failed、2 timedOut；按原因判读为三项通过、一项应用缺失（精确 Search 不存在且仅占位）、两项原测试缺陷。六组原始报告、trace/截图、测试快照、清理记录在 `runs/competition-budget/20260926/root-only/analysis/local-suite/`。suite SHA256 与上一轮相同，为 `105c0df7100dffc65c35fb87f047da496c275643e36e3a8f3d7faada869ec434`。建议下一步先修正交接投递目标、root-only 可指派目录和静止/完成交付边界；此处记录建议，不扩大为本轮源码修改或新实验授权。

2026-09-26 用户报告剩余参赛额度 285.86，明确撤销后续实验 variant 正式参赛授权，要求先自带 API key 在官网实验，并从 Factory 实现限制昂贵模型会话数。
用户同时要求复核 [K3 11/100 报告](../k3-root-experiment/results/7b533d7bd71b.md)，讨论下一步改进。
本次直接授权覆盖止损。用户随后认可协作交接、PR 分支和最终验收的分析及方案，修正预算边界为 Braid session，并建议在任务 prompt 明确生成阶段避开评测端口与环境。用户随后明确“同意，你可以开始了”，授权按实验设计实施、启动 A/B，并在等待期间梳理会话任务树。当前已开工；不包含源码提交或使用参赛额度。

## 已处理的止损

接续器已在新要求到达前创建 `48a591836974`，submission `2c7e143c03a4`。
只读查询发现用户已取消远端运行：`CANCELLED`，`failure_reason=Run cancelled by user`，完成于 2026-09-26 04:52:06 UTC。
本次终止本地 launcher 28209 与 controller 39521，通知原监控 Agent 停止接续，并核实进程已退出。
根-only 原状态目录保留，已通过只读 status 更新 task 为 terminal；没有新上传、重启或评测。
远端证据在 [状态记录](../../runs/k3-root-only/20260926/official/status-after-budget-stop.json)。

当前源码的 Competition `prepare` 和共同写入口 `_post` 拒绝 `official_evaluation`，包括恢复旧 journal 后继续创建或启动。
`self_funded` 保留原有自带 key 流程；API 返回的 `billing_mode=self_funded` 不能覆盖提交请求的 `credential_mode`，不据此认定没用参赛额度。

预算的有效决定：七类模型合计只允许一个 Braid session 使用，不按 Pi 原生 session ID 或 Pi sub-agent 数量计数。
七类模型为 glm-5.2、glm-5.3、qwen-3.8-max、qwen3.7-max、kimi-k3、kimi-k2.7-code-highspeed、deepseek-v4-pro。
本轮实验将昂贵模型给根 Braid session，其余 Braid 会话使用 Flash；原生 sub-agent 仍按各自角色配置，属于另一配置层面。

源码已改为用 Pi 的 CLI binding 查询 Braid 逻辑成员身份，领取本次运行唯一的昂贵模型名额。
原生上下文重建不增加名额；Pi sub-agent 按自身角色配置，不占新的 Braid 名额。
PR `--head` 已实现，真实共享源码 `cargo check` 通过；Linux release 正在复用 WSL 构建缓存。
旧 Braid 测试调用存在此前接口迁移欠账，不能将独立基线上的测试通过写成当前全库测试通过。
当前 A 已启动；B 尚未冻结或生成。未提交源码。

## 归因复核

2026-09-26 后续证据：A 的同一应用干净重放 [`e45e4ae7110d`](https://arc-bench.com/runs/e45e4ae7110d) 已完成，14/100、4/47，新后端正常监听 3000，无生成模型调用。源码 73 个文件与 `4c17843` 冻结应用完全相同。因此下述旧服务污染事实保留，但不能继续作为严重低分的主要解释。后续定向取证发现共享标题、控件角色/精确名称及默认页 Checks 等公开契约偏差；详见 [重放分析](../k3-root-experiment/results/e45e4ae7110d.md)。运行隔离和交接修复仍有必要，不能据此预期单靠这些修复就有高分。

确定：官方后端因 3000 端口占用未启动，冻结收尾只扫描 `work/`，漏掉同级 `braid-state/worktrees/`；11/100 不能用于判断最终提交或根 K3 的净收益，但仍是有效的参赛成绩记录。
高可信推断：评测请求落到了旧工作区的服务；缺少评测时的监听 PID 和请求记录，不能归因全部 89 个失败，更不能假定干净重评会得到高分。

确定：根 Issue 只在首次运行时有两条自己的讨论 comment（拆分和进展），没有来自子任务的完成交接；四个 PR 已合并，根仍 OPEN，根会话没有恢复。
当前 Braid 讨论路由发送给当前工作项、关联 Issue/PR 和线程参与者；父子 Issue 关系不等于根负责人自动收到全部子任务的更新。
因此目前能确认的是协作交接缺失，不能仅凭根没恢复就断言有调度故障。
需区分：Agent 没有发出交接、交接发出但没送达、送达后未执行；实际证据支持第一种，尚没有第二或第三种的证据。

确定：Issue #5 的实现提交未进入最终历史，PR #4 从集成分支重做了模块，约 1 小时 48 分钟。
冻结指令本来就说明在 PR 完成实现；Agent 把 PR 理解为实现后的评审交接，而 CLI 的 PR 创建语义只能从集成分支开始，二者叠加造成重复。
不能以自动搬运任意 Issue 工作区来修正；GitHub 式已有实现应由明确 head 分支/commit 创建 PR，尚未实现的 PR 才从 base 开始。

## 已认可的修复方向与实验准备

1. 先冻结 `4c17843` 的应用回放包，干净启动后用 `self_funded` 官网仅重评，不重新调用生成模型。
   验收对象是这一个提交；部署须证明新启动进程存活并绑定目标端口，不能只看 HTTP 200。
   官网没有逐例测试数据，后续仍以总分、需求和自身行为复现为依据，不把取得隐藏步骤当作前提。
2. 优先在 run.py 生成的任务 prompt 写明生成与评测共享环境：3000 留给官方评测，自检显式指定其它空闲端口；自检数据库、缓存和浏览器状态使用临时位置，不污染交付所需初始状态。
   只调整自检方式，交付应用仍须接受官方 HOST/PORT=3000；这些环境要求写入根 Issue description，不放进通用 Braid/SVC。
   现有进程清理范围修复保留为收尾保障，不扩展成新的隔离或进程管理系统。
3. 协作交接沿用 comment：根 Agent 安排完成/阻塞回报，负责人将结果送回负责整合的 Issue；Braid 负责可靠递送和恢复会话，不判断产品是否合格。
   调查是否需要通用订阅能力，不增加“子任务全部关闭→自动宣告完成”的语义规则。
4. 让 PR 支持显式采用已发布 head，保留从 base 开始实施的路径；创建反馈给出实际 head/base，消除“已实现代码自然进入 PR”的错觉。
5. 最终集成验收应针对实际交付提交、干净数据与实际部署方式，范围由设计阶段的验收方案决定。
   根协调者可以委派低成本会话执行最终验收，再依据结果整合；不要求昂贵根会话亲自操作浏览器。

实验矩阵、固定变量与判读规则见 [实验设计](experiments.md)。实验设计与开工已获用户确认，按该范围完成实现及真实运行。
参赛额度保持停用；不自动转成正式参赛。

## 当前执行

A 已从精确 commit 导出并打包，目录 `runs/competition-budget/20260926/replay/`，控制器 PID 48054，self_funded，轮询间隔 900 秒。只回放应用，不调用生成模型。Braid PR --head 的实现与任务树证据梳理由独立 Agent 并行处理；主 Agent 处理 Factory 会话预算、prompt/交接与制品整合。

Linux release 已从真实共享源码构建成功（`factory26-budget-20260926`），使用缓存耗时约 65 秒。复用已补齐后台 Bash 的 runtime，不重装依赖。会话名额的一次最小检查确认：同一 Braid owner 可再次请求，另一 owner 请求昂贵模型被拒绝，Flash 不占名额；这不替代真实运行中身份映射的验证。

B 已准备新状态目录 `runs/competition-budget/20260926/root-only/official`，尚未上传/启动；冻结 ZIP SHA256 `2ade98da55ab20fb9e00d582151ce5a3c001d98ff74cef455ecad0ccb8ec9bbe`，两题固定为 GitHub、Sheet，credential_mode=self_funded。A 完成并核查部署后接续。

A 完成干净回放 14/100（14通过、86失败），报告见 ../k3-root-experiment/results/e45e4ae7110d.md。部署正常但验收与公开需求偏离，降低端口污染的归因权重。用户要求按原定计划推进B；不改变冻结包，继续验证交接、代码承接和最终验收。B控制器PID 66498，日志 runs/competition-budget/20260926/root-only/controller.log，900秒间隔，GitHub后Sheet，self_funded。

A分析复核与后续方向已保存到 [a-review.md](a-review.md)。新证据确认PR4收到且读取精确需求，且本身为K3；偏移集中在验收判据与浏览器脚本执行，而非简单漏传或廉价模型。新方向仅供复核，B冻结输入未改。
