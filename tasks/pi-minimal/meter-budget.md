# pi-minimal Meter 余额保护

当前实验是加入svc-verification后的单题GitHub自费运行，身份见 [verification-run.md](verification-run.md)。费用观察与比赛额度守护是不同模式；自费模式不应用比赛取消阈值，也不查询比赛余额。下面各时间点的余额、用量和进程属于对应历史运行。

2026-09-30用户新增比赛额度例外：预计扣除在途费用后的余量低于20元，不取消当前运行；仍阻止新增任务。此改动不授权新的比赛运行。

## 已核实的账户与当前余额

Meter 页面 `https://meter.arc-bench.com/user` 的现有登录会话显示个人访问密钥账户：

- 接口：`GET https://meter.arc-bench.com/api/user/balance`
- 余额字段：`balance.available_balance`
- 货币字段：`currency`（页面显示 CNY）
- 同步状态接口：`GET https://meter.arc-bench.com/api/user/freshness`
- 当前只读结果：`available_balance=23.001318`、`currency=CNY`、页面账单状态“已同步”、更新时间 `21:41:48`

该账户 `available_balance=23.001318 CNY`，但它是自带 API key 的 Meter 账户，不是 `official_evaluation` 的比赛额度，不能用它决定正式参赛是否可启动。

正式比赛额度来自官网只读接口：

- 接口：`GET https://arc-bench.com/api/competitions/hackathon/registration`
- 关键字段：`competition_type=official`、`registered=true`、`initial_budget_cny=500.0`、`remaining_budget_cny=285.862202`、`currency=CNY`

这是 2026-09-29 启动前读到的正式参赛余额。2026-09-29 16:45 UTC Sheet 运行结算后，余额变为 **281.265249 CNY**。CLI 用保存的网站会话访问该接口，保护脚本对 HTTP/身份/schema 错误 fail-closed，不猜测余额，也不输出 cookie 或 access key。Meter 的个人账户接口仍记录在上面，避免把两种余额混淆。

## 保护路径

[budget_guard.py](budget_guard.py) 只接受并解析为以下唯一 journal：

`runs/pi-minimal/20260929/official`

首次检查：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official --once
```

持续检查：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official
```

脚本启动即查询一次，此后每600秒查询。先按完整快照估计同一journal的在途未结算费用，再查询官网比赛账面余额，以两者之差决定动作。

| 预计扣费后比赛余量 | 已在运行的任务 | 新任务 |
| --- | --- | --- |
| 大于100元 | 继续运行 | 本守护不额外阻断，仍须已有实验授权 |
| 20～100元，含边界 | 核对身份后取消 | 阻断 |
| 低于20元，包括负值 | 保留运行，不发送取消请求 | 阻断 |

余量不高于100元时仍写入该journal的 `budget-stop.json`。低于20元的回执为 `status=new_runs_blocked`、`reason=balance_below_no_cancel_floor`、空取消列表，并记录 `keep_running` 事件；20～100元时只对属于该journal submission且未终态的run调用既有官方取消接口 `POST /api/runs/{run_id}/cancel`，再读取状态确认。正好20元仍属取消区间。余额查询失败写 `reason=budget_unavailable` 的停止标志，阻止继续启动，不猜测余额，也不取消未经身份核对的run。

`--check` 只查询一次且不取消，适合每次开始下一题前的闸门：

```sh
python3 tasks/pi-minimal/budget_guard.py runs/pi-minimal/20260929/official --check
```

主线 Competition controller 已检查同一 journal 的 `budget-stop.json`，存在该文件时拒绝新的远端写入，因此它会阻止下一题的 snapshot/create/start。脚本不持有 controller lock；余额事件和取消回执仅写 `budget-events.jsonl`，不写凭据。

## 限制

- watcher 使用现有 ArcBench 网站会话查询比赛额度；不能把任何 cookie 或 access key 写入仓库或命令输出。
- 保护先阻止新增远端写入，再依据余量区间决定是否取消同一submission的在途run；它不取消其它journal，也不删除或改写比赛证据。
- 本次只做了源码语法与真实只读额度核对，未上传、启动、取消任何比赛 run，未调用模型。

## 运行中预算盲区（2026-09-30 复核）

GitHub `f3424d6aa387` 仍为 RUNNING，run 接口的 `token_count`、`token_cost_usd`、`token_cost_currency` 均为 null，`settled_at` 也为 null。Sheet `ed9bb83f8e1b` 已 FAILED，终态记 `token_count=15420252`、`token_cost_usd=4.596953`、`token_cost_currency=CNY`；比赛余额从 285.862202 降至 281.265249，差额正好为 4.596953。这证明本轮可观察的比赛余额在 Sheet 终态后才纳入其费用，不能当成扣除了 GitHub 在途费用的实时余额。终态费用字段名带 `usd`，但本次货币字段明确为 `CNY`，按后者理解，不再换算。

先前下载的两个 `/runs/{id}/workspace/template-bundle` ZIP 是较早时点的包，不能用来判断当时以后的生成进展。2026-09-30 重新从该接口下载 Sheet 终态包（716,460 bytes、40 条目，SHA256 `15c73246177f8c53b33d162e10556ed86fadd6943f89a6a934cef9b6d6e0b2f8`），并保存官网文件 panel 重新 Packaging 后的 GitHub 包（3,443,438 bytes、70 条目，SHA256 `2ee19eb02bb6a57e53da4ca0983d88ca90af6036f168d2ac7fda19c740123b13`）。两个新包都含比旧包更多的生成文件，却均没有 `template/.arc/` 或 `session.jsonl`。它们保存在 `runs/pi-minimal/20260929/budget-live/*-project-new.zip`。

冻结入口 `variants/pi-minimal/main.py` 将 Pi session 写到 `output/.arc/pi-minimal/session.jsonl`，官网 generation 命令明确传 `--output-dir /workspace/template`，因此预期源位置是 `/workspace/template/.arc/pi-minimal/session.jsonl`。`cleanup_workspace` 只终止剩余工作区进程，不删除该目录。本地同入口保留的 `runs/pi-minimal/20260929/native-fix/retained-workspace.zip` 确实含该原生 session。另一方面，历史 K3/Braid 的多份官网 `template-bundle` 有隐藏 `.factory26`，没有 `.arc` 条目。这些观察支持**官网包未导出 `.arc`**，但无法单凭 ZIP 区分服务端清理与打包过滤，也不能概括为官网无法下载工作区。官网 `/runs/{id}/source` 读取 `.arc/pi-minimal/session.jsonl` 等路径返回 404，说明该单文件读取方式同样未提供原生记录。`/runs/{id}/logs` 亦无 Pi 逐条 usage。目前可以下载应用工作区代码，却不能从已核实的接口取得按消息/模型的在途费用输入。历史 Meter 单价仍需在拿到 usage 后核当前价格及计费口径。

Sheet 的失败发生在生成阶段：16:45:22 UTC `main.py` 等待 Pi stdout 时收到 SIGTERM，其 handler 抛出 `KeyboardInterrupt: terminated`；平台在 16:45:38 将 `start_agent` 记为失败，`run_tests` 仍 pending，并报告主进程 SIGINT。现有平台日志不能判断 SIGTERM 的发起者。`budget-events.jsonl` 至 16:44:42 仅有 balance 事件，没有取消或 budget stop；PID 45669 的原单一守护仍运行，故 Sheet 失败不能归因为该守护。

当前每 600 秒的守护只覆盖已结算余额。新包缺原生 JSONL，因此没有让未知费用默认为零，也没有启动第二个守护或猜测取消 GitHub。最小观测修复是让官网工作区包提供 `.arc/pi-minimal`，或另行提供在途 run 的 CNY 金额；届时按模型消息身份跨快照去重，用 ARC 当前输入、缓存命中/写入、输出单价估算，并在 run 费用进入比赛余额后排除已结算部分。即使补齐，10 分钟下载和模型持续运行仍使 100 元只是软阈值，不能保证硬保留。

## Sheet 一次重试（用户追加授权）

已重新下载终态工作区（40 条目）并核对平台日志，仍无法确定 SIGTERM 发起者。依用户“如果没有能找到原因，可以重试一次”，2026-09-29 17:00 UTC 对原 run ed9bb83f8e1b 调用官网现有 rerun，生成 d03625688de8，沿用 submission f9bd3524fe75 和原冻结 ZIP，已确认 RUNNING。旧运行和响应保存在 runs/pi-minimal/20260929/sheet-retry；未重新上传或修改制品。

控制器与同一个余额守护已顺序交接到新 PID 54251 / 54271，journal 的 Sheet 身份替换为新 run；GitHub f3424d6aa387 不变。旧 Sheet task journal 已归档。守护仍每 600 秒检查账面余额，阈值 100；原生用量不可取得的问题尚未解决，不能宣称它估算了在途费用。

2026-09-30 01:12 CST 核查：守护 PID 54271 存活，01:11 余额记录为 260.172023 CNY。GitHub f3424d6aa387 已 FAILED（部署 npm install 返回1），费用 21.093226 CNY；Sheet d03625688de8 RUNNING。rerun 已自动启动，先前控制器再 start 得409退出；现复用 Controller.recover() 只读核对后接续采集，控制器 PID55781，原守护不重启。不再重复远端 start。原生用量估算仍未实现。

## 2026-09-30 self_funded observe

用户授权的自费两题 journal 为：

`runs/pi-minimal/20260930/arc-advisor/official`

观察器读取journal中的variant/credential_mode来限定pi-minimal自费运行，不再把单个实验目录写死。旧self-funded记录保持可读取。

启动观察器的参数为：

```sh
python3 tasks/pi-minimal/budget_guard.py \
  runs/pi-minimal/20260930/arc-advisor/official \
  --self-funded-observe
```

首次检查立即执行，此后每 600 秒下载每个活动 run 的 template bundle。该模式只读取 run 身份和 `template/.factory26/pi-minimal/pi-timing.jsonl`，按 `request_id` 去重，将主会话和 advisor 按 timing 记录中的 `provider/model` 分组；它不查询 hackathon registration，不读取个人 Meter 余额，不写停止阈值，也不取消 run。快照缺少 timing 文件、provider/model、usage 或价格时记录 `usage_unknown`，不把未知费用算成零成本结论。

本模式使用 [provider-prices.json](provider-prices.json)。2026-09-30通过浏览器实际渲染 BigModel 官方价格页 `https://open.bigmodel.cn/pricing`，GLM-5.3-Flash卡片确认输入0.8、输出2.8、缓存命中0.23 CNY/百万tokens。FAQ另提限时五折，但没有本账号优惠适用证明，故使用标准价作保守估算。此前ARC目录不作为直连供应商证据。Moonshot `moonshot/kimi-k2.7-code` 的只读模型页和价格来自官方 `https://platform.kimi.com/docs/pricing/chat`：`6.50/27.00/1.30 CNY / 1M`（缓存未命中输入/输出/缓存命中输入）。两者均不使用 ARC 价格表；缓存写入单价未确认，若 timing 出现非零 `cacheWrite`，该模型成本保持未知。

已有真实 bundle `runs/pi-minimal/20260929/budget-live/f3424d6aa387-project-new.zip` 已只读核对：不含 `template/.factory26/pi-minimal/pi-timing.jsonl`，观察结果为 `usage_unknown`；这证明当前脚本不会把缺失输入误报为零费用。未启动新 run、未上传或取消任何 run。运行中的在途请求、下载间隔和供应商最终账单仍不在 timing 快照的可见范围内。

## 当前修复：脚本相对 Pi home 与费用估算

用户要求轻量定制 Pi home 并复用既有实验接线。main.py 旁的 pi-home 链接到输出 .factory26/pi-minimal/home；显式设置 HOME、PI_CODING_AGENT_DIR，主原生 session、事件、advisor 原生记录及后台任务状态均保存在 .factory26 下。恢复入口只对旧本地包搬迁 .arc/pi-minimal 并保留旧路径符号链接，以免历史中的绝对路径失效。原冻结制品与既有运行没有改动。

复用原 factory-pi-timing.ts，不增加模型提示词、工具或模型调用；主 Pi 和 advisor 都装载，统一写 pi-timing.jsonl。新增 usage_budget.py 从同一官方工作区下载入口读取该文件，以 request_id 去重，只计算 message_end 中已返回的用量；Pi input 已排除 cacheRead/cacheWrite，推理 token 已包含在 output，不重复计费。ARC 当前价格来自已认证的 /api/user/models，快照见 arc-prices.json。

既有budget_guard.py每600秒采集活动run，估计余量=采集后官网账面余额−未终态run的已知费用；当前取消区间为20～100元，低于20元保留现有运行但阻止新任务。每次从完整快照重算，不累加重复下载；下载期间终态的run由随后账面余额覆盖。费用数据缺失、未知模型、损坏或部分行明确标usage_unknown，不把差额当可信余量。正在生成但尚未返回的请求、采样和下载延迟仍不计入已知费用，因此这是软阈值。监控没有启动新实验；下一次授权运行须确认可下载timing文件并与终态官方费用比较。

最新真实采集（08:56:54 CST）：GitHub0.2219508元、Sheet0.32302944元，合计0.54498024元，脚本PID82936。Sheet的Moonshot组出现两次请求、0用量；进一步读取原生子会话确认均为供应商余额不足429，不是成功的免费调用。当前可确认费用证据采集和GLM工作，advisor受账户条件阻断。
