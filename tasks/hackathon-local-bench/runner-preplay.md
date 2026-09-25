# 官方 Runner 只读实施预演

2026-09-25 核实 WSL 现有官方源码与镜像。未修改源码、未运行测试/benchmark/模型、未启动应用或改变现有服务。读取镜像文件时创建了未启动的临时容器，各次均已删除。

## 身份与最小可行接入

WSL 已存在镜像 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`，tag 为 `arcbench-local-submit:latest`；没有声明 Docker volume，默认命令为 `python3 /opt/arcbench/local_runner.py`。镜像内 `local_runner.py` 与宿主 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner/local_runner.py` 的 SHA256 相同：`80785810d4d4a256d76e35ef395b415a1e3148a9885ab0bf429f1776285b5e4d`。以下 `local_submit.py`、`local_runner.py` 行号指该宿主目录；`run_submission.py` 行号指该镜像 `/opt/arcbench/run_submission.py`。

本轮实施计划选定既有回放 ZIP 加 `arc_bench_adapter.py` 单阶段路径，每场景一个 lab job。已直接核实 WSL `/home/yyh/Development/factory26-official-local/codex-base-artifact-replay.zip` 存在，SHA256 为 `3f78afcaa8e79029bc00734b46044f08d8ea77cdf22ef93d87624e717805e6d6`。包内入口与本仓库 `lab/arc_bench/arc_replay.py` 一致：17–25 行按 requirements.yaml SHA256 选出唯一冻结应用，再复制到本次输出目录；不调用模型。两份应用来源正是计划中的 `codex-base-hackathon-github-97ad8b8eec`、`codex-base-hackathon-sheet-67ac86e938`。

`arc_bench_adapter.py:176–185` 已能将该 ZIP、tests-dir、唯一 workspace 交给官方单阶段入口，无须新增 `--application` 或直接 `--template` 分支。回放来源记在 `template/.arc/replay.json`（`arc_replay.py:26–28`）；这是包内来源清单的副本，不能将它说成运行时对目标目录重新计算的 hash。lab 冻结的 ZIP 字节身份与原清单共同保留应用身份。评测时不传模型 env-file，沿用 adapter 现有宿主模型环境清除逻辑（110–116 行）。

作为接口边界，官方 `local_submit.py` 本身也支持 `--template <冻结应用> --tests-dir <单场景输入> --workspace <唯一目录> --agent <无模型入口>`，参数在 750–781 行，装配在 389–481 行；本轮无需使用该替代路线。通用 lab 无须了解场景语义。

## 选择一个场景

`run_submission.py:869–888` 每次覆写 `tests/playwright.config.ts`：`testDir: '.'`、一个 worker、单测试及 expect 默认超时各 10 秒、JSON reporter、trace/screenshot 默认关闭；没有 `testMatch`、grep 或读取场景选择环境变量。`953–955` 的执行命令只有 `npx playwright test --workers=1`；`913–924` 的枚举命令只有 `npx playwright test --list`。自带 config 不能保留，官方 CLI 也没有透传 Playwright 参数的接口。

镜像 Playwright 1.57 的 `/opt/arcbench/node_modules/playwright/lib/common/config.js:163` 默认匹配 `**/*.@(spec|test).?(c|m)[jt]s?(x)`；`program.js:199`、361 的 grep 来自 CLI `--grep`，该官方调用未提供此参数。

实施计划选择按领域组织原生 spec 并复制完整 suite，采用 `selection.json` 加极薄 `test` 包装器：读取稳定 scenario ID，只向 Playwright 注册匹配场景，其他场景不注册、不 skip。它是测试集材料里的选择逻辑，不是修改 Runner；不需要为每场景另建源码文件。

后一方案须满足三点：选择在测试枚举期同步完成，`--list` 与运行使用同一输入；未知 ID、重复 ID 或实际枚举不等于一个场景属于设施失败；所有匹配 spec 仍会被导入，因此顶层不能做浏览器准备、写应用状态或其他副作用。可由每次适配层对最终 JSON 的稳定 ID、文件/标题与总数再核对。不要仅凭一个有效报告就接受选错或多跑场景。

## Fixture、准备阶段、附件与 trace

`local_submit.py:433–434` 复制整个 tests bundle，支持自带 TypeScript/JavaScript fixture/helper 和数据文件。`run_submission.py:891–910` 覆写 package.json，固定使用镜像预装 `@playwright/test` 1.57.0，并把 tests/node_modules 链接到 `/opt/arcbench/node_modules`；自带其他 node_modules 会被拒绝，不会安装 bundle 自定义依赖。原生 Playwright 与 Node 标准库已足够。

在每个 spec 文件顶层使用原生 `test.use({ trace: 'on', screenshot: 'only-on-failure' })`，可覆盖 Runner 的默认关闭值。不要只给扩展 fixture 设置默认 option 值后期待覆盖配置，也不要只改自带 config；若通过 support 函数复用配置，应由每个 spec 显式调用，不能依赖共享模块只执行一次的导入副作用。镜像 `playwright/lib/index.js:75–77` 定义这些原生 option；`worker/workerMain.js:297–302` 从最终 trace fixture 配置启动记录。场景的连续 UI 准备超过 10 秒时，使用原生 `test.setTimeout` 或 `test.describe.configure` 明确设置该场景的总超时；无需 Runner 超时配置框架。

准备、动作、断言可以用 `test.step` 记录，同时用 `testInfo.attach` 保存当前阶段和原始异常。JSON reporter 保留 errors、steps 和 attachments（`playwright/lib/reporters/json.js:189–209`）。阶段附件负责区分准备阻断与目标断言失败；不把准备失败转成通过。强杀可能来不及写最终附件/trace，缺失证据应随中断保留，不能保证取消后仍有完整 Playwright 报告。

设 `W` 为本场景传入的官方 `--workspace`，产物映射如下：

| 内容 | 宿主位置 |
| --- | --- |
| 官方完整 Playwright JSON | `W/template/.arc/playwright-report.json` |
| trace、失败截图、文件附件、默认错误上下文 | `W/tests/test-results/` 递归目录 |
| Runner/应用/测试原始输出 | `W/template/.arc/stdout.log` |
| Runner 调试与测试枚举原始 stdout/stderr | `W/execution.debug.log` |
| Runner 事件和回放来源记录 | `W/template/.arc/runner-events.jsonl`、`W/template/.arc/replay.json` |
| 装配与结果元数据 | `W/runner-spec.json`、`local-submission.json`、`local-run.json`、`local-result.json` |

默认 outputDir 为 package.json 所在目录下的 `test-results`（`playwright/lib/common/config.js:153`），因此真实路径是 `/workspace/tests/test-results/`，不在 `.arc`。`worker/testTracing.js:198–200` 把 `trace.zip` 存在该测试的 outputPath 并附到结果；`worker/testInfo.js:347–355` 保存文件附件。JSON 的附件 `path` 保留容器绝对路径，展示端须将 `/workspace/` 映射为 `W/`；body 附件直接以 base64 写进 JSON。保留原始 JSON，不回写路径去改原件。

`lab/run.py:113–135` 已能通过 job 的 `artifact_paths` 递归采集目录。配方至少显式加入本次官方 workspace 的 `template/.arc`、`tests/test-results`、`execution.debug.log` 与根目录元数据；不要复制 tests/node_modules 的镜像内绝对链接充当证据。`lab/arc_bench/results.py:61–63` 当前只扫描 `.arc` 顶层和根日志，不能靠它自动收齐 trace/附件。

## 隔离和构建边界

本轮回放路径先由 `local_submit.py:425` 将 ZIP 解压到本 job 的 `W/submission`，再由包内 `main.py:25` 将所选 `submission/applications/<run_id>` 复制到 `W/template`。因此回放源、应用实例与 tests 均在本 job 独有 workspace 内，没有共享的应用可写目录。ZIP 清单已排除依赖/构建目录，普通数据文件随包保存，包括 GitHub 的 `backend/data.json` 和 Sheet 的 `backend/data/*.json`；场景会从冻结包里的这些确切初始状态开始。数据是否满足需求属于种子场景验收，不能在装配时改写。

若未来改用 `--template`，`local_submit.py:292–312` 会逐个复制 baseline 普通文件；排除 `.arc`、`.git`、requirements、node_modules、`.cache`、dist、build，以及特定 `.env`/字节码文件，跳过 symlink。这是按官方契约复制的源文件副本，不是原目录的逐字节完整克隆。该替代接口同样不会自动清理已污染的普通数据文件。

`local_submit.py:406–411` 拒绝非空 workspace；`515–533` 为每次执行生成唯一容器名，只绑定 `W:/workspace`，没有其他 volume、宿主端口映射或 host network。宿主 W、容器可写层、`/tmp`、HOME 和监听 3000 端口因此按场景独立；默认每容器限制 2 GiB/1 CPU（777–778）。这覆盖容器内与应用副本内的可写状态，但不自动隔离应用代码主动访问的外部数据库/服务。Runner 没有断网或外部服务命名空间机制，不能把容器隔离声称为任意外部状态隔离。

已检查本轮 ZIP：两款应用均无 deploy.sh，因此每场景必做 frontend `npm install`、`npm run build`、backend `npm install`（`run_submission.py:1172–1190`）；安装函数还会先删除现有 node_modules（803–818）。测试工具直接复用镜像预装 Playwright，不重复 npm install。`local_runner.py:56–97` 一般允许冻结应用自带 `deploy.sh` 接管部署，此时是否重装/构建由该原有脚本决定；本轮不使用该分支，不能为了复用构建临时改冻结应用。

当前最小方案接受每场景重建，并发上限按真实主机负荷保守设定。官方 CLI 没有只读共享构建缓存的 mount 接口；跳过构建需要额外部署契约或镜像/入口改动，已超出直接复用官方 Runner 的最小接入。无需在本轮引入缓存服务或应用实例池。

## 取消与失败边界

`local_submit.py:515` 每次随机生成 `arcbench-local-<12位hex>`，不是由 workspace 推导的固定名称；521–522 将它作为 `docker run --name`。官方 parser（750–781、790 行）没有 `--name`、`--cidfile` 或 Docker 参数透传，不能从外部给此入口直接加这些选项。但 554–555 行在调用 Docker **之前**把 workspace 和容器名以 `flush=True` 写入 stdout，已经提供精确的本次容器句柄。

`local_submit.py:519–520` 使用 `docker run --rm --init`，容器退出后自动移除；557 的调用只是阻塞 `subprocess.run`，没有 signal handler 或 `finally: docker stop/rm`。生产 Runner 正常 Python 异常路径会在 `finally` 停止已登记的应用直接子进程（1313–1328；1155–1164），但没有覆盖宿主强杀/Docker CLI 失联的补偿。

`lab/run.py:155–178` 取消时 SIGTERM 宿主 job 进程组，最多等 5 秒后 SIGKILL；它不知道 Docker daemon 内的容器身份。正常 Docker 信号转发可能使容器退出，现有代码不能保证所有异常取消路径完成该转发。即使只剩容器，容器文件隔离仍在，但资源占用和状态写入会继续，不能宣布场景已经清理。

最小补偿路径留在 `arc_bench_adapter.py:110–116` 这个共享调用边界，覆盖所有调用者：

1. 在 adapter 主线程把 SIGTERM 转为能展开 Python 栈的中断，沿用 SIGINT 的异常退出；用 `try/finally` 包住官方 subprocess。只写 finally 而不处理 SIGTERM 无效，因为 lab 同时向 adapter、local_submit、Docker CLI 所在的宿主进程组发 SIGTERM。不要靠另一个后台 watcher。
2. 从这次 invoke 自己的 `<name>.stdout.log` 读取严格格式的 `Container: arcbench-local-<12位hex>`。当前单阶段是 `runner.stdout.log`，官方实际 bind source 是 `args.workspace.resolve()/official`；不是 adapter 的上层 workspace。共有路径的 generation/evaluation 调用则分别是 `generation.stdout.log` 配 `official-generation`、`evaluation.stdout.log` 配 `official-evaluation`（adapter 129–173、176–185 行）。以该次命令显式 `--workspace` 为权威，不按 task 名猜测。
3. 只对日志中的精确容器名执行 inspect，并要求 `Mounts` 中存在 `Type=bind`、`Source=本次 --workspace 的绝对路径`、`Destination=/workspace`（官方挂载在 523–524 行）。匹配才清理；名称不明、挂载不匹配或 Docker 错误均保留原始诊断并返回未确认，不能扩大到前缀批量停止。日志尚无 Container 行时，官方代码还未调用 Docker；没有理由搜索其他容器。
4. 已取消/异常退出后仍存在的本次容器可定向 `docker rm --force <精确名字>`，再 inspect 核对不存在，保存清理结果。宿主 job 已取消时，强制移除的是其可丢弃实例；最终 trace/report 可能不完整，按中断记录。若需要先给进程刷新日志的短机会，可先 `docker stop --time=1`，但整个清理须设置短的工具超时并落在 lab 现有 5 秒 SIGKILL 窗口内；不要引入默认 10 秒 stop 等待。Docker 自行 `--rm` 后的 not found 按已清理处理。

这条补偿可以改善正常 SIGTERM/异常路径，不能声称消除 SIGKILL。adapter 被直接 SIGKILL、宿主崩溃或 Docker daemon 操作超时都会阻止 finally 完成；Docker 创建请求与取消也可能交错。只对已知名字做有界的再次确认，记录最后观察时间/状态，不启动孤儿监控或扫描其他容器。若在预算内不能确认不存在，终态必须保留“容器清理未确认”和同一精确名字/挂载，供下次人工恢复定向核实。当前源码尚无上述补偿，故尚不能宣称取消时无人值守清理完整。

原始 Runner 会把 skipped、timedOut、interrupted 计未通过；本地解释层需结合阶段附件解释，不能只用 `local-result.json` 的 passed/failed。无报告、枚举异常、报告结构错误与零测试分别在 `run_submission.py:929–933`、1006–1015、1073–1075 及 `local_submit.py:653–679` 暴露；`local_submit.py:681–727` 只要有可遍历报告便标 completed，故适配层仍须核对场景身份、数量、应用身份及 Runner 是否完整结束，保留原始异常，不能把设施故障当业务零分。

## 已证边界与待实际验收

本轮直接证实了镜像和 ZIP 字节身份、包内回放入口、官方配置/命令、复制/挂载实现、报告与附件路径的实现，以及现有取消机制缺口。单场景 selector、trace 配置、artifact_paths 和 ARC 生命周期补口尚未实现，本轮没有以实际浏览器运行证明它们生效，也未测量并行构建成本或跨场景数据隔离。

开工后可沿用计划的真实应用验收：先核对一个选定场景的枚举与完整结果身份，再运行有独立观察依据的场景，打开其 trace/截图和阶段附件，观察两个独立应用实例的数据变化，核对场景完成或取消后的所属容器终态及全部日志。不增加模拟应用、Factory 自检或基础设施测试。这些未验收项不阻断上述实施路线；取消生命周期必须在宣称可无人值守并行执行之前补齐并从实际运行证据核对。
