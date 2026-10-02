# SVC CLI/dev 对比赛生成 Agent 的适用性

状态：2026-09-28，已核对源码、实际 CLI 帮助和已生成应用；SVC CLI 不接入参赛 runtime。用户随后授权最小工具方案，Harness 自有 `with-service.py` 已修改并在隔离应用副本上验证；尚未构建或部署新包，也未改正在运行的应用。此前仅在本工作轮草拟的 SVC 接线已撤回，保留其他任务的工作区改动。

## 问题与结论

Agent 要解决的是一次性自检的三个实际问题：检查进程退出时保留首次真实退出码和运行前提；异常时只收尾自己启动的服务/检查；交接者判断旧结果能否用于当前候选。GitHub 已生成 E2E 在后端启动后、进入 `try/finally` 前启动浏览器，浏览器失败会漏服务；Sheet `checks/run.sh` 自建七服务并带 watchdog，最后的兜底清理仅按命令行匹配同名后端，可能越过本次所有权；PR #23 曾因缺少可交接的完整退出回执，在等价树上发生约 18.7 分和 17.2 分的两轮全套检查。第三例的成本有独立记录，不能断言每分钟都可由工具节省。当前主要场景是带临时数据和独立端口的应用自检。SVC `dev` 适合**事先声明、确实需要跨调用者长期复用**的能力，不适合作为未知比赛应用的默认服务入口。它无法单独覆盖检查退出码与收尾需求；要求生成应用额外维护 `svc.json`、身份化 probe、provision 和 stop，会增加失败面与交付认知负担。

因此本轮不把 SVC CLI 装入 `pi-braid` 的 Linux runtime，也不为 SVC 增加生成 Agent 指令或服务管理器。保留现有 SVC 技能；开发侧 `.venv/bin/svc` 继续独立使用。Harness 小工具及其指令入口是后续单独获授权的改动，见下文。若未来确有同一服务跨成员、跨多次调用复用的具体证据，再针对该应用的身份、健康探针和清理动作评估 `svc dev`，而不是让所有生成应用预先声明。

## 实际能力与边界

完整开发源码在 `/Volumes/WorkSSD/Development/svc`，HEAD 为 `80996c115ba635c6b85db47d0b14663293b95f12`，工作树有本地修改；`.bootstrap/dev-svc.json` 记录开发安装来源，当前 `.venv/bin/svc --version` 为 15.0.0。`sources/svc/` 的维护入口只承担六个 Agent 技能，不能作为参赛 CLI 安装来源。实际 `svc --help`、`svc dev --help` 列出 `status/identity/ensure/stop`；源码权威入口为完整开发树的 `cli/src/svc_cli/{cli.py,config.py,dev/runtime.py,dev/identity.py,workspace.py}`，行为说明见其 `USER_MANUAL.md` 的 Development Capabilities 节。

| 需要 | `svc dev` 的实际行为 | 对当前比赛生成的影响 |
| --- | --- | --- |
| 启动与就绪 | `ensure <target>` 只处理 `svc.json` 的 `dev.targets` 声明；执行 provision、等待 HTTP/TCP/exec probe，已健康时复用；manual provision 不代执行。`status` 观察声明，exec probe 本身可执行代码。 | 未知应用须先写配置；仅安装 CLI 不会让服务可用。就绪证明由应用 probe 决定。 |
| 所有权与并发 | 同一 capability ID 内的 ensure/stop 序列化；ID 受 namespace、scope、工作区/仓库/host 身份及 target 约束。默认 worktree probe 的解析端点须包含当前 instance（通常用 `${dev.instance}`）；host scope 要显式 `host_key`。 | Braid 成员使用独立 clone，默认 worktree/repository 身份不同，不能假设自动共享同一服务。跨 clone 共享须设计 host scope、端点身份和访问约定；健康端点被复用不等于 SVC 拥有其进程。 |
| 检查回执 | `dev` 只报告能力就绪与自身动作状态；就绪后释放启动进程句柄，后续完整进程日志不保证。另一个 `svc run` 域可对**事先声明**的有界命令留退出收据。 | `dev` 不能替代任意 E2E/构建检查的首次退出码与日志；为未知检查再声明 `run` 会加配置。 |
| 退出与权限 | `stop` 只运行 Consumer 声明的 stop 命令并复核 probe，缺 stop 时返回 `manual-action-required`；不凭历史 PID 杀进程。命令可在应用工作区执行。 | 应用必须自己提供准确、可审计的清理动作；把 stop 误写成全局 `pkill` 仍会伤及其他成员。CLI 不是进程权限沙箱。 |
| 资源与生命周期 | 开发能力可在启动 CLI 退出后继续运行，执行记录保存在本地用户 runtime 目录。 | 一次性自检通常需要在检查结束即停机、隔离数据库/端口，并把检查失败作为本次结果；持久化服务反而延长清理责任。 |

## 隔离观察与最小做法

对现有已生成应用的临时副本 `/tmp/factory26-github-3583/applications/pi-braid--hackathon--github-3d75045c72f1d6` 只读执行开发 CLI：`svc dev identity --repo <副本> --json` 返回工作区身份；`svc dev status --repo <副本> --json` 返回 `invalid-configuration`、原因 `svc.json must be a regular file`、退出码 3。该应用没有 `svc.json`。其 `e2e/req1.spec.mjs` 已自行用临时 `DATA_DIR`、非 3000 端口启动后端，轮询 `/api/health`，在正常检查路径的 `finally` 中停止服务，并通过 `process.exitCode` 报告检查失败；`e2e/README.md` 写明这些运行条件。浏览器启动发生在 `try` 之前，若该步失败，脚本的 `finally` 不能清理已启动服务；因此现有脚本也不能充当失败路径完整收尾的证明。这是应用自身的待检查边界，不是引入 SVC 的理由。没有启动应用、跑测试、改应用、建模拟服务或构建 runtime。

现有 `harness/skills/agent-browser/scripts/with-service.py` 已为**单个前台临时服务 + 一条检查命令**提供端口占用拒绝、HTTP 就绪等待、自有进程组收尾，以及保留 `service.log`、`check.log`、`result.json.check_exit`。它是 Factory 自编的可选脚本，不属于 SVC 或上游 agent-browser。能保持应用原有 E2E 自管生命周期时直接保留；需要单服务包装且首次检查收据时选它；多服务检查继续使用应用自己的明确生命周期，不为此新建通用管理器。任一方式都应按候选代码、检查入口、数据与环境前提解释结果，不能仅凭退出 0 宣称整体验收。

## 部署影响与再评估条件

SVC CLI 的 runtime 接线净改动为零；既有冻结 ZIP、运行中 Agent、应用和开发侧 CLI 均不改变。后续获授权的 Harness helper 源码改动尚未部署。若今后一个具体应用确需跨成员共享常驻服务，应先证明服务身份、端点与健康语义、成员 clone 之间的访问、应用声明的 stop 作用范围、运行结束后的资源归属；这些明确后才值得从完整开发 SVC checkout 构建并冻结 Linux CLI。`svc dev` 的真实启停与跨 clone 并发需在独立生成应用副本上验收，不能以 CLI 帮助或这次 `invalid-configuration` 观察替代。

## 已选定的小工具方案（源码已改，未部署）

已从 Sheet 候选 `cc5b876:checks/run.sh` 核实：它实际为七个 Playwright 项目各启一个独立后端（`CREATE/EDITOR/HOME/CSV/REQ3_CORE/REQ3_INTEGRATION/WORKSHEET`），每个有私有 `DATA_DIR` 和动态端口；脚本自己记录 PID、维持 watchdog、用 EXIT trap 清理。源码用普通 `node ... &` 启动七个后端、用 `watchdog &` 启动看护进程，脚本内没有 `setsid`、`nohup` 或 detached 启动，因此这些直接子进程应继承 runner 的进程组；Playwright/浏览器后代是否自行脱离，不能由该脚本保证。它的失败出口包括建服/就绪失败和 Playwright 非零，且 check 过程已负责初始化数据与环境。再让外层工具逐个配置七个服务，会复制应用逻辑、增加第二个服务管理入口。GitHub 临时副本的 `e2e/req1.spec.mjs` 则在浏览器 `launch()` 之前已经启动未脱离 session 的 Node 服务，而 `try/finally` 在 `launch()` 之后才开始；浏览器启动失败可留下该服务。

建议只扩展既有 `harness/skills/agent-browser/scripts/with-service.py`：保留当前单服务参数与行为，新增明确的 `--check-only` 模式，将应用已经拥有生命周期的 `checks/run.sh` 或 E2E 脚本当作一条前台检查命令，放进 helper 自己创建的进程组；检查退出或被中断后，仅向这个进程组发送 TERM、限时后 KILL。这样七服务脚本在启动或检查失败时仍先走其 EXIT trap，外层只收尾同组遗漏的子进程；GitHub 脚本即使在浏览器启动前后的异常路径退出，外层也能收尾它未 detached 的后端。无需新的多服务管理器或应用 `svc.json`。

首轮 `result.json` 应保存实际检查 argv、cwd、开始/结束时间、原始 `check_exit`（包括失败），以及调用者显式传入的少量 `--context KEY=VALUE`：例如候选标识、数据目录/种子、浏览器二进制、依赖版本。可自动记录 Git HEAD 与 dirty/untracked 状态供审查，但不采集完整环境变量或密钥；若源码/构建产物/数据不等价，单凭同一 commit/tree 不得复用结果。已有单服务模式继续保存服务命令、端口、就绪状态。stdout/stderr 存文件并打印证据目录。检查结束取得真实 `returncode` 后应先落首轮收据，再清理服务及写最终清理结果；检查非零、服务启动错误、信号中断必须用不同状态表达。连检查进程都未能启动时，`check_exit=null` 和明确的启动错误不能伪装为测试失败；SIGKILL 或宿主崩溃无法承诺执行 `finally` 或完整收据。外层收据只说明 runner/检查进程状态，不代替产品功能通过。

所有权边界：helper 只负责它启动的进程组，不能拦截 Agent 直接执行的 `pkill`、自行 `setsid`/daemonize 的孙进程，也不能证明任意 HTTP 响应属于本服务。Sheet 脚本的最后兜底清理按 `/proc/$listener/cmdline` 中 `backend/dist/server.js` 判断，不核对该 PID 是否属于本次进程；外层包装不能防止它误杀别的 checkout 的同名服务。因此在共享宿主复用此脚本前，Agent 应先修正其自编脚本的清理归属，再用 helper 提供的无需全局 `pkill` 的统一结束路径；不应宣称外层已解决任意误杀。

用户已授权此方案；实施只改 `harness/skills/agent-browser/scripts/with-service.py`。保留原 `--start CMD --port N` 单服务入口，增加 `--check-only` 和重复的 `--context KEY=VALUE`，不添加服务配置或多服务管理器。检查进程以独立 session/进程组启动；正常退出取得原始 returncode 后先原子写 `result.json`，再清理自有组。状态区分检查非零、检查自身信号、服务错误、检查未能启动与包装器中断；清理另有 `cleanup_status`，一个 stop 或中间回执写入报错不跳过另一自有进程组。Git 工作树自动记录 HEAD、dirty、untracked；无 `.git` 的生成应用包由调用者用 context 明示候选。不会 dump 全部环境变量。

实际验证只使用已有生成 GitHub 应用 `/tmp/factory26-github-3583/...` 的再复制副本 `/tmp/with-service-gh-validation-20260928`。该副本依赖 `better-sqlite3` 的本地二进制对应 Node 22；首次使用本机默认 Node 26 导致 ABI 失配、邻居后端未启动，随后改用现有 Node v22.22.3 完成操作。只在该副本内安装缺少的 `e2e/playwright-core` 依赖，没有改原样本或回灌应用源码。

| 隔离场景 | 实际回执与资源观察 |
| --- | --- |
| 旁边实例占用端口，helper 尝试启动同一真实后端 | `service_error`，`check_exit=null`，包装器 exit 1；旁边实例仍返回 `/api/health`。证据 `service-check-u3i6bd0i`。 |
| 真实后端以 `DATA_DIR=/dev/null` 启动 | 启动前退出 1，helper 记 `service_error`、`check_exit=null`；旁边实例仍健康。证据 `service-check-2nwv20uq`。 |
| 单服务成功就绪，实际 `/api/missing` 检查返回 HTTP 404 | `curl` 原始 exit 22，helper 记 `check_failed/check_exit=22`、`cleanup_status=passed`；被检查端口关闭，旁边实例仍健康。证据 `service-check-hudns17k`。 |
| 原 `e2e/req1.spec.mjs` 在浏览器启动时因故意不可用的 Chromium 失败 | 脚本已执行至 `chromium.launch()`，helper 的 check-only 记 exit 1；脚本未进入自身 `finally`，但外层清掉其同组后端，旁边实例仍健康。证据 `service-check-5u9o6blv`。 |
| 原 `backend/test/req1.test.mjs` | 原应用五项测试均通过；helper 记 `check_exit=0`、`passed`。证据 `service-check-r9zfzn_u`。 |

证据目录前缀在本机 Python 临时根 `/var/folders/rk/8_krr0y14p9g5plk8n77lgyr0000gn/T/`。这五次验证只证明工具的执行、回执和可观察的资源收尾；没有在 Sheet 七服务脚本上实跑，也不证明题目产品已通过整体验收。

精确依赖版本 `pi-background-bash@1.0.5`（`harness/npm/package-lock.json`）源码 `extensions/background-bash.ts` 对 PBB-owned shell 进程组先发 TERM，未 settled 时 500 ms 后发 KILL。helper 的 check/service 使用独立进程组，因此 PBB 不直接清它们。为缩短中断路径，helper 收到 TERM 后先给两个自有组发 TERM，并以短宽限收尾。使用真实后端加现有 `npm test --prefix backend`，对包装器组施加同样 500 ms 窗口的独立操作中，取得 `interrupted/check_exit=-15/cleanup_status=passed`、被检查端口关闭（证据 `service-check-igz6zsdr`）。**这不是 PBB 内部执行实测**；进程调度、磁盘故障或 SIGKILL 仍可抢在最终清理/回执前，不能承诺 `pbb kill` 一定完成 wrapper 的清理。正常完成路径有完整回执；主动中止后的 `cleanup_status` 必须实际检查，缺席不是成功。

### 评审时的真实选项

| 方案 | 覆盖与不足 | Agent负担与维护 |
| --- | --- | --- |
| 沿用PBB/原脚本，补明确操作方法 | 已有后台任务标识、退出结果、日志与停止入口；应用脚本继续建服。它不强制将首次结果与候选/数据前提一起交接，也不能替脚本处理未进入finally的异常 | 无新增工具，但每个Agent/脚本要自行拼接归属、候选和回执，容易重复已发生错误 |
| 扩展with-service的check-only及首轮收据（推荐） | 不接管七服务拓扑，只把既有runner当一次有所有权的检查执行，统一留结果并收尾同组进程；仍要求runner自身不全局误杀或脱离组 | Agent只多一层命令包装和必要前提字段；复用已有脚本，不建配置平台 |

SVC CLI/dev已因实际需求不匹配排除，不将其凑成第三个推荐选项。多服务拓扑由应用runner掌握；外层只管理这一次执行的进程组与结果。

以下是**已实现的接口示例**，`checks/run.sh` 为已存在的 Sheet 检查入口；此处仅演示包装方式，并未在正在运行的 Sheet 上执行：

```sh
python3 <skill-directory>/scripts/with-service.py \
  --check-only --cwd "$PWD" \
  --context "candidate=$(git rev-parse HEAD)" \
  --context "data=runner creates fresh per-spec directories" \
  -- bash checks/run.sh
```

`--context`只记录调用者声明，不设置环境或验证声明真实性。检查所需浏览器等变量仍按应用入口设置，结果须结合实际日志解释。
长检查可继续由现有 PBB 承载和等待；主动停止只针对该后台 job 或 helper 自己的句柄，随后核对最终收据与监听状态。PBB 的 500 ms 强制升级不保证 helper 的 `finally` 必然跑完，不能据一次 `pbb kill` 回应就宣称资源已清干净；不追加按程序名全局清理。
完成后交接证据目录，复核者先比对候选/检查/数据/环境，再决定复用或定向重验，不能为了首次没有记exit而被迫重跑。

验证还应并行保留另一份已有生成应用的独立服务，确认被检查实例异常退出时旁边实例继续可访问；只使用独立端口和临时数据，不触及冻结运行。
实际收益（例如减少多少分钟）需后续自然运行证据；隔离操作只能证明进程归属与回执机制。

## 尚未闭合的证据链

- PBB 1.0.5 的 500 ms TERM→KILL 与本 wrapper 的关系已有精确源码和独立同窗口信号验证；尚无“通过真实 PBB 作业发 `pbb kill`”的验收，也不承诺所有宿主/磁盘调度下均能写最终收据。这一边界需在下一独立运行中自然观察，不动当前冻结 Agent。
- Sheet continuation-03 的 11:57 UTC 截面见 `tasks/braid-product-reaudit/cells/sheet-progress-late03.md`：PR #26 当时仍在执行，最终交付与各项实际检查耗时尚待自然完成后的原始日志。这里的工具隔离验证不推断其后续状态。
- 生成 Agent 的环境排障耗时、通知/context 重建与共享契约冲突的原始工具日志，以及 subagent/vision 是否实际采用并消费结果，属于产品运行审计。后续在 `tasks/braid-product-reaudit/cells/open-evidence-followup.md` 从现有 packet/cells 追原始来源；不要拿 helper 的局部验证代替这些结论。
