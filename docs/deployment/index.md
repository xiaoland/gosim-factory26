# 本地运行与证据

本文维护开发者运行、恢复和检查本地 harness 所需的操作说明。[产品说明](../prd/index.md)维护实验规则和范围；可执行参数以[Factory 配置](../../variants/factory/config.json)、[运行器](../../scripts/factory.py)和 [Makefile](../../Makefile)为准。

## 参赛包与平台边界

参赛包复用本项目的 Braid + SVC 生成、Git 交付冻结和原生证据归档。每个 ZIP 固定一个 backend；根目录 `main.py` 接受平台传入的需求，不读取本地 benchmark，也不执行评测：

```sh
python3 scripts/package_agent.py --backend pi --output runs/packages/factory-pi.zip --docker-context arcbox-win
# Codex 使用 --backend codex，输出到另一份 ZIP。
# 以下命令在解压后的 ZIP 根目录执行，并由调用环境提供模型变量。
python3 main.py /path/to/requirements --output-dir /path/to/output
```

构建需要可用的 Linux x86_64 Docker daemon；`--docker-context` 可省略以使用当前 context。脚本只发送指定构建输入，不上传整个开发目录。Braid 从当前 `sources/braid` 构建；SVC 从当前 `sources/svc` 构建包含 Corpus 的 wheel，Python 依赖用 Linux CPython 3.12 安装到包内目录。Node 和所选核心也在构建时安装并随包提供；Pi 需要 Node >=22.19，不能直接使用平台原有 Node 20。精确工具版本由 [Dockerfile](../../submission/Dockerfile) 固定，实际文件哈希、源码身份和执行权限写入 `package-manifest.json`。npm lock 和 Python 依赖清单随 runtime 保留。重复构建不覆盖已有 ZIP；构建时无需模型 key，比赛运行时无需 clone 源码、Cargo 或开发者 venv。

入口要求 Linux x86_64、CPython 3.12 和 Landlock ABI >=3。它先校验所有载荷并恢复 ZIP 解压丢失的执行权限，再启动独立 Landlock launcher。规则只授权系统运行路径、只读包与需求、可写临时工作区，不开放整个 `/workspace`、`/tmp` 或 `/proc`。运行前检查子孙进程不能读取宿主标记，不能写入、删除或替换需求。内核或 seccomp 不支持时明确失败，不会无隔离回退。网络白名单仍由平台负责；该文件隔离不声称实施了网络隔离。生产 Runner 是否支持此内核能力需要在正式环境核实。

入口优先采用完整的 `VISUAL_API_KEY`、`VISUAL_BASE_URL`、`VISUAL_MODEL`；没有视觉 key 和地址时使用完整的 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`MODEL`（仅有默认 VISUAL_MODEL 不视为配置了视觉凭据）。视觉 key 或地址只提供一部分时立即失败，避免静默丢弃图像能力；选定配置不完整也立即失败，不回退到本机密钥或自选模型。只把 key 传给运行进程，配置与制品清单保存环境变量名称，不保存密钥值。原生工具输出仍可能含敏感信息，运行证据不能未经检查公开。

应用交付遵循官方标准布局：`frontend/package.json` 提供 build，`backend/package.json` 提供 start；后端在 `HOST=0.0.0.0 PORT=3000` 下提供前端产物与 API，目标应用兼容 Node 20.19.3。包内 Node 22 用于 Harness，不能推定部署环境也有 Node 22。禁止依赖本地模拟器专用的 `deploy.sh`。入口只在生成成功并冻结后复制应用，保留平台预置的 `.arc`、`.git` 和 `requirements`，拒绝覆盖同名应用文件。输入可为独立需求快照，或输出目录原有的 `requirements/`。证据保存在输出的 `.factory26/<run-id>/`；`run.json` 描述生成，`delivery.json` 单独描述交付成功或失败。

正式提交由队长使用平台的正式评测入口，并使用平台内置 key。本项目 Playground 上传仅用于自带 key 的练习，必须显式选择 `--practice`，不计正式成绩；`--offline` 仅供无模型设施探针。这里没有实现未经核实的正式提交 API。

官方契约来源是 [本地模拟环境](https://github.com/code-philia/hackathon-local-simulation/tree/cfbbc287ee1bbffcf1e936545e4803145693a8d8)。该仓库未包含生产 Runner 源码或可直接拉取的生产镜像地址。无模型验收可以证明打包、文件隔离、工具启动和入口交付，不能证明真实模型生成质量、正式评分或生产容器兼容性。当前实施与验收状态见 [task packet](../../tasks/competition-p0/packet.md)。

## 环境和启动

生成主机需要 Python 3.12+、Git、uv、Node/npm，以及对应 Pi 或 Codex 可执行文件。macOS 使用 sandbox-exec，Linux 使用 bwrap；模型接入目前在本机 macOS 验证。braid 组合另外需要 Rust 1.93+ 构建本地源码。评测可独立运行在 Linux，不需要模型密钥或 Agent 核心。

```sh
cd ~/Development/factory26
make bootstrap
make test
make run
```

`bootstrap --backend pi|codex` 从 `sources/svc`、`sources/braid` 构建安装，并准备固定评测器及 Codex 所需的 LiteLLM 1.102.0。省略 backend 使用共同配置中的 pi。首次缺少 sources 仓库时 clone 上游 main；已有源码不会被 reset、checkout 或自动 pull。后续以 HEAD、实际源文件和安装产物哈希判断是否需要重建。ARC package-lock 缓存一致时复用依赖，Chromium 存在时复用浏览器；仍执行上游静态契约检查。

本项目使用 `.venv/bin/svc`。机器全局 `svc` 可能仍是旧版；本文及 SVC 自动生成导航中的 `svc` 命令均应通过项目本地路径执行。CLI 版本、`svc.json` 配置 schema 和其中声明的 Corpus baseline 是不同维度；重装 CLI 不代表自动完成 Corpus 迁移。

比赛密钥保存在仓库外的 `~/.config/factory26/llm.env`，文件权限应为 `600`：

```dotenv
FACTORY26_API_KEY=你的比赛密钥
```

入口读取密钥后通过环境变量交给对应 Agent 或本地适配器，不写入模型配置或命令参数。网关地址和模型名称由基线配置维护，当前使用比赛视觉模型以接收需求图片。原始会话可能包含工具输出，因此 `runs/` 不纳入 Git。

## 生成和评测

生成在独立临时目录运行。两个核心均使用临时 HOME、原生配置目录和筛选后的环境变量。Pi 禁用自动发现个人扩展、技能、提示模板和主题。当前 factory 启用 Braid 和 SVC，将 [harness/AGENTS.md](../../harness/AGENTS.md) 的两行导航复制到运行时 user scope。活动配置目录、实际注入文件和公共 harness 都保存到新 run。内部只有 svc=true 才复制 SVC 安装和指导；关闭 SVC 的受控 Braid 探针不需要它们。安装在 bootstrap 时完成，生成沙箱内无需联网重装 Corpus。

文件隔离拒绝读取开发仓库、个人 Codex/Pi 配置和比赛密钥文件，需求副本只读；运行前检查评测器不可读、需求可读以及 SVC 可查询。网络用于模型调用与依赖安装，因此这不是网络隔离沙箱，也不是整个用户目录的访问隔离。主机网络及硬编码 /tmp 路径仍共享；同机并行生成可能争用端口或临时文件，受控比较应串行生成，或为每组提供独立机器/容器。远程冻结后评测使用独立应用目录和分配端口。

Codex 使用 app-server stdio，只有所请求线程和 turn 的 completed 通知表示结束。每次 Codex 生成启动一个仅监听 loopback 的 LiteLLM 适配器并在结束后停止；不回退到其他模型。Pi 单会话即使退出码为 0，也须在 Agent 阶段检查最终 stopReason；原生错误保留其正文和已报告用量，不能进入成功冻结。braid 的 Pi provider 等待 agent_settled 后判断终态，允许原生重试和压缩收尾。

braid 从 [sources/braid](../../sources/braid/) 构建，运行入口保持 `braid local <request.json>`。Factory 提供本次隔离 Git 仓库、profile、核心配置、需求、run ID、delivery ref 和状态目录，不提供 SVC 任务包。Braid 以本地 Issue/PR/comment 为权威，沿既有 Group/队列/会话链调度；Agent 使用每次 turn 提供的 CLI 身份修改对象，不手动请求 refresh。宿主调试写入必须显式指定 `--external`，Agent 写入必须携带当前 `--writer-turn`。

对象 CLI 直接使用 `braid --state STATE issue/pr view|edit|comment`，不再包含 object 层。正文使用 `--body/-b` 或 `--body-file/-F`，后者接受 stdin 的 `-`；结构化输出显式加 `--json`。`pr create --issue ID --title TITLE --body-file FILE` 直接建立本地实施工作项并激活 Agent，不再先创建请求 comment 或调用 pr ensure；可选 `--request-id` 用于不确定响应后的幂等重试。ready 与根 Issue 接受 merge 的交付边界保持不变。精确命令与上下文行为由 [Braid 本地协议](../../sources/braid/docs/20-product-tdd/local.md)维护。

`braid-state/result.json` 记录 completed/incomplete/failed 和交付 commit。只有根需求、必要 PR 和生命周期收尾收敛才可 completed。Factory 校验返回的 run/ref/仓库及 Git commit 身份，并导出指定 commit；不会按最新工作树或初始应用目录选择交付。

两个真实核心的受控检查默认关闭 SVC：

```sh
python3 scripts/check_braid.py --backend pi
python3 scripts/check_braid.py --backend codex
```

探针通过真实 Agent 创建 comment，再验证 hide/unhide/delete、自身写入不自唤醒、外部 description 修改自动重建、失效 turn 拒绝以及新的本地 PR 交付。结果位于 `runs/integration/`，包含实际输入、全部物理会话、源码快照、原生证据和对冻结 calc.py 的独立断言；没有固定阶段数，也不计入 ARC-bench 成绩。`--svc` 仅用于额外排障，不替代默认的关闭 SVC 检查。

生成结束后停止 Agent 进程组，清理工作目录仍位于本次临时工作区的独立工具进程并确认无残留，再保存应用快照并计算哈希。已退出生成进程的组清理若返回 EPERM，会保留退出码与清理异常，仍必须通过工作区清理检查；评测路径不忽略该异常。评测在另一个临时副本中安装、构建和启动应用，冻结快照保持原样。活动配置的 `deployment=arcbench` 要求上述 frontend/backend 布局；本地评测先安装并构建 frontend，再安装并启动 backend，以首页响应检查就绪。历史 run 缺少 deployment 字段时保留根 `package.json`、`npm start`、`PORT` 和 `/api/health` 返回 200 的原契约。

运行器使用官方单项测试和断言超时、单 worker、零重试；不额外设置模型输出 token 上限或流程总时限。具体值由运行器和每次评测的 `command.json`、`summary.json` 记录。服务退出时健康检查失败；arcbench 部署最多等待 120 秒，单条测试超时 10 秒。历史部署仍使用原 60 秒单测和无总上限的健康等待；查看 `application.log` 判断原因。

也可分别执行各阶段：

```sh
python3 scripts/factory.py generate
python3 scripts/factory.py eval --run runs/<run-id>
python3 scripts/factory.py analyze --run runs/<run-id>
```

`run.json` 描述生成状态，对应核心或 Braid 工作项与执行状态必须完整收敛，才允许冻结为可评测结果。每次评测有独立目录和 `summary.json`；完整执行后即使存在失败用例也保留有效分数。生成失败时查阅原生会话与 stderr；评测失败时先查对应阶段日志，不把运行错误解释成模型零分。

`factory.py run` 另存覆盖生成、评测和分析的 `outcome.json`，分析收尾后才发布 completed、failed 或 interrupted。生成失败后，只要存在原生会话清单，仍尝试 SVC analysis；分析异常独立记录，不覆盖原始错误或有效成绩。评测启动前分配 ID，即使失败也保留对应证据入口。单独的 `generate`、`eval`、`analyze` 仍各自保存阶段结果，不伪造一次完整实验的终态。

若旧运行器在成功终态后的清理环节失败，恢复前保留原始失败元数据，核验全部原生终态、最后交接动作、应用哈希及工作区无残留，另存恢复记录。未保存的退出码保持未知，不能补写成功；应用不能修改。

安装、构建或运行环境问题解决后，可对未改动的应用快照再次执行 `eval`，产生新的评测目录。新的生成或使用外部反馈的修改必须作为独立实验处理，不能覆盖旧快照。评测器版本或快照哈希不匹配时，先核对来源，不绕过检查。

## 诊断入口

先使用全流程摘要，再按具体问题打开已有诊断入口：

```sh
python3 scripts/run_feedback.py brief runs/<run-id>
python3 scripts/factory.py show <run-id>
python3 scripts/factory.py show <run-id> --case REQ-2.2
python3 scripts/factory.py show <run-id> --eval <evaluation-id> --json
```

`list/show` 只读已有运行。生成失败时，show 从哈希核实的 Pi 归档提取末条 assistant 的终止原因与记录位置；不展示完整正文，不回溯已恢复或已替代会话的旧错误，损坏或关联不唯一时明确未知。默认 show 先呈现状态、失败和相关入口；指定 --case 时优先展示该用例。全部元数据、路径、会话和 SVC evidence 映射保留在 --json，避免默认输出铺满文件列表。生成状态、所选评测和 SVC coverage 分别展示；最新本地评测失败时不回退到旧分数。用例入口展开有长度标记的错误、从官方 error-context 定向提取的页面片段及行号，以及重定位后的本地截图、视频和 trace。页面事实不自动等于因果结论。历史数据缺少阶段或退出码时显示未知；旧 variant 根据配置推导并显式标记。

新 run 在 setup、preflight、agent/braid、cleanup、frozen/failed/interrupted 时原子更新 `run.json`；新评测记录 install、build、health、tests 等阶段及日志入口。失败保留 `failed_phase`，中断明确标记。Braid 生成失败时另存 `recovery-workspace.json` 并保留原始隔离目录及 Git common repo，以免销毁工作树的恢复依据；成功后清理。此保留不表示失败应用已经冻结可评测，也不表示已有 Factory 一键恢复接口。阶段更新时间表示最后一次阶段变化，不代表进程仍存活；服务不健康时可由阶段日志定位。

远程评测以 `remote-evaluations/<evaluation-id>.json` 保存每次请求的完整观测，`remote-evaluation.json` 仅作为最近观测的兼容入口。请求在启动前分配明确 ID，区分连接、传输、远端运行和下载，每 180 秒获取该 ID 的 summary；SSH 进程退出立即返回，不额外等一个观察周期。下载后核对 run、benchmark 和冻结应用哈希，不按目录差集猜测执行。观测时间与观测失败单独保存，下载后用终态 summary 收口；断线不能被当成远程零分或停止成功。`show` 同时保留最新本地评测与远端状态，不把暂存远端状态当作已下载成绩。

## 等待、反馈与交接

一次已获授权的长实验交给较低成本子 Agent 持有运行命令和等待，主 Agent 处理其他工作或等待完成消息。交接只需本次目标、配置与证据路径、完成条件、允许操作和停止条件。子 Agent 根据程序摘要判断哪些证据值得展开，返回结果、依据、未知和需要决策的事项；不转发整段日志。每次实验结束先向用户汇报，由用户决定下一轮，不自动重跑。

`run` 的后台观察器每 180 秒读取已有事件并保存 `feedback.json`，相同类别错误不重复输出，执行退出时立即刷新终态。错误类别与重试是观测事实，可能已经恢复；不输出不能指导判断的工具完成计数。整体状态以 `outcome.json` 为准，错误片段只用于定向取证。没有完整结果的旧 run 明确标记 `scope=generation`，不能据此声称 bench 已完成。

主会话不定时读取原始流，也不通过每三分钟唤醒一次模型来模拟事件通知。当前使用子 Agent 的原生完成消息回传，验收范围限于主会话仍活跃的情况；尚未验证主会话结束或 App 关闭后的唤醒。中途恢复可读取持久结果，或由子 Agent 启动以下只读等待命令：

```sh
python3 scripts/run_feedback.py watch runs/<run-id>
python3 scripts/run_feedback.py watch runs/<run-id> --after-event <已处理的event_id>
```

独立 `watch` 没有被观测进程的句柄，因此以至少 180 秒的间隔检查文件；发现终态后立即返回。已处理的终态身份保持静默，这用于去重，不保证跨进程消息恰好投递一次。停止等待不等于停止远端实验。

## 证据与分析

`runs/<run-id>/` 保存配置、提示、输入与输出哈希、生成器源码快照、原生 session、stdout/stderr、usage，以及每次评测的源码快照、JSON、HTML、截图、视频和 trace。`native/manifest.json` 将每个物理 session 与 provider、逻辑 group、工作项、turn、归档输入及内容哈希对应；被替换会话的用量仍计入。缺失证据保留身份及错误，不能用最新文件代替。退出时清理 Agent 与应用进程组；报告中的相对产物链接依赖本机保留的 run，不会随源码自动分发。

`analyze` 为每个原生会话分别导出 `analysis/<序号>-<来源指纹>/evidence-v4.zip`，保存 overview、模型 usage 和 provenance。来源指纹包含原生内容、实际 provider 和 exporter；缓存使用前核对原生清单与产物哈希。相同来源复用已完成分析；来源变化重新导出，全部查询成功后才发布目录，失败不覆盖已有分析。历史目录保持原样。run.json 汇总整个生成的用量，Pi 包含压缩和分支摘要用量；缺失摘要 usage 会单独标记，不能声称统计完整。进一步检查可使用 `query`、`read`；请求格式通过命令帮助与 `--schema` 查询：

```sh
.venv/bin/svc analysis query --help
.venv/bin/svc analysis read --help
.venv/bin/svc status --json
.venv/bin/svc lookup --path specs/
```

svc 负责证据导航，不自动判定应用质量。标准 Pi session 缺少执行终态，可能使 overview 显示 `partial`；应结合覆盖声明、运行器退出码与最终模型停止原因判断，不能把 `partial` 一概解释成内容丢失。实际费用未知时保持 null，不用客户端估算替代比赛账单。

## 单一 Harness 与 WSL 评测

唯一活动配置为 `variants/factory/config.json`，共同使用 Braid + SVC，`--backend pi|codex` 选择核心。配置文件不因覆盖参数而改写；每次 run 保存最终生效的 config，并独立记录 variant 与 backend。旧六份配置及 configs/ 符号链接已删除，可从 Git 历史恢复；旧 runs 继续按各自归档配置和原身份读取。显式 `--config <file>` 保留为 custom 实验入口，供后续消融使用。以 Pi backend 为例：

```sh
python3 scripts/factory.py bootstrap --backend pi
python3 scripts/factory.py run --backend pi --eval-host wsl.win-ws.localhost
python3 scripts/factory.py list --variant factory --backend pi
```

wsl.win-ws.localhost 的 ~/Development/factory26 已安装固定 runner 和 Chromium，重复 bootstrap 会命中缓存。生成仍在本机完成，--eval-host 只传输冻结应用与必要元数据，在 WSL 评测后取回结果；不传比赛密钥，不在每次评测中重装 runner。应用自身依赖仍需在每次隔离评测目录中安装，以免跨实验共享可变状态。省略 --eval-host 则在本机评测。

评测主机需要同步当前 scripts/、variants/ 和必要源码后运行 bootstrap。不能只复制本机 node_modules 或 Python venv 到不同平台。单独重新评测时使用 `eval --run runs/<id> --eval-host wsl.win-ws.localhost`；已有 run 的 eval/analyze/show 使用归档配置，拒绝 backend 或配置覆盖。可用 `--evaluation-id <id>` 指定执行身份，已存在时拒绝覆盖。应用哈希必须保持不变；每次先获取官方用例发现清单，再核对实际测试身份及执行终态。

## SVC 与 braid 的共同开发

`sources/svc`、`sources/braid` 是各自有 origin 和 main 分支的独立 Git 仓库，由父仓库忽略；它们是现在的源码修改位置。`third_party/arc-bench` 只保存固定评测器。旧 `third_party/svc`、`third_party/braid` 副本为历史运行与构建缓存保留，当前生成不再读取其源码。相邻 `~/Development/svc` 和 `~/Development/braid` 的前轮通用修正已迁入 sources，原工作树保持原样。

```sh
git -C sources/svc status --short
git -C sources/braid status --short
python3 scripts/factory.py bootstrap --backend pi
make test
python3 scripts/check_braid.py --backend pi --svc
```

直接修改对应源码，运行该仓库要求的检查，再 bootstrap 和创建新 run；不再维护另一份补丁副本。更新上游时在各自仓库显式 fetch/merge，处理本地改动后重建。父仓库 status 不会列出这些独立仓库的改动，提交也应在各自仓库明确执行。

[sources.py](../../scripts/sources.py) 在构建时记录 HEAD、包括未提交和未跟踪文件的源码哈希，以及安装产物哈希。生成前验证构建仍匹配，避免修改源码后误跑旧安装。每次 run 的 `sources/` 保存实际源码 tar.gz 和构建记录，可以重建这次未提交实验；归档忽略构建目录、Git 数据和缓存。旧 runs 不补写新版本。SVC 工作方法的 runtime 注入仍由 [harness/AGENTS.md](../../harness/AGENTS.md) 维护，不加入 braid 控制协议。

默认 analyze 使用上述构建安装；分析新导出器前先 bootstrap。已有 `--svc-source <path>` 仍可使用具备 PDM 环境的源码工作树作独立诊断，它记录实际 HEAD 和 CLI 源码哈希，不替换运行时 Corpus，也不改写旧分析。SVC analysis 是开发工具，分析没有 SVC 注入的原始 core run 也完全有效。

若要追踪生成期间已经出现的工具错误，先用稳定短语 match，再用返回的 ref 做 trace：

```sh
printf '%s\n' '{"version":3,"intent":"match","predicates":{"kinds":["tool_result"],"text_terms":["稳定错误短语"]}}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
printf '%s\n' '{"version":3,"intent":"trace","event":<match返回的ref对象>}' |
  .venv/bin/svc analysis query --input <evidence-v4.zip> --request -
```

trace 提供关联的标准化调用上下文；只有需要精确内容恢复或原生审计时才用 read。外部评测在生成之后发生，其错误未必存在于生成 transcript 中，不能把用例 ID 强行关联到某次工具调用。应先从用例证据判断应用缺口，再回看当时相关实现或自检行为。

## Playground 脚本

[playground.py](../../scripts/playground.py) 使用网站 HTTP 接口完成登录、上传、运行和证据收集，日常实验不需要浏览器。首次运行 `python3 scripts/playground.py login`，交互输入网站邮箱和密码；也可以通过 `--credentials ~/.config/factory26/playground-login.json` 读取权限为 600 的 JSON 文件（email、password）。登录验证后保存权限为 600 的 `~/.config/factory26/playground.cookies.txt`。网站会话与比赛模型密钥分开保管，登录信息不进入仓库或命令参数。

```sh
python3 scripts/playground.py whoami
python3 scripts/playground.py requirements --catalog benchmark
python3 scripts/playground.py submit --practice --package /path/to/agent.zip --requirement keep --name factory-keep
python3 scripts/playground.py watch <run-id>
python3 scripts/playground.py collect <run-id>
```

上传前必须准备符合平台契约的 Python Agent ZIP，根目录包含 main.py 与 requirements.txt。`submit` 默认读取 Factory 配置中的网关和模型，也可用 `--config` 指定，并使用仓库外比赛密钥；配置不会改变 ZIP 已打包的核心或工作流。清单明确标记 configuration_scope=model-settings-only，包身份以 SHA256 为准。只有无模型探针使用 `--offline`，该选项传非凭据占位符。包哈希、已确认的 submission/run ID 与执行阶段记录在 `runs/playground/upload-*/submission.json`，便于写请求失败后查明已经完成哪一步；传输结果不明时不自动重复 POST。

续跑、启动和取消只接受本工具清单中明确记录为 practice/probe 的 ID；未知、正式和缺少分类的历史 ID 请通过平台管理。

同一包重跑使用 `python3 scripts/playground.py run --submission <submission-id> --requirement <requirement-id>`，避免重复上传。已创建但尚未启动的 run 使用 `start <run-id>`；明确结束云端执行使用 `cancel <run-id>`。中断本地 `watch` 只停止等待，不改变云端 run。401 表示需要重新登录。

`status <run-id> --saved` 可只读重放已归档状态，不联网、不改旧产物。摘要分开列出最近有效事件、心跳和采集时刻，缺少观测时间时明确未知；不使用文件 mtime 猜测。traceability 没有显式记录时显示未建立关联，不能由 SDK 自报 passed 推导外部评测成功。`status` 输出阶段摘要，`watch` 默认每 180 秒读取状态和增量日志，只在 PASSED、FAILED、CANCELLED 或 PAUSED 时收集证据、输出摘要并退出；可用 `--after-event` 跳过已处理的同一结果。运行中无变化保持静默，PAUSED 表示需介入而非完成；运行中的计数不作为完整成绩。观测超过 360 秒标为 stale，不据此推断远端已经停止。平台曾将实际耗时返回为 0，因此终态摘要用 started_at/finished_at 计算 elapsed_seconds，并汇总测试状态；原始时长字段保留在 status.json。`collect` 将状态、日志游标与分块、traceability 和 commit history 保存到 `runs/playground/<run-id>/`。JSON 的凭据字段会脱敏，但原始日志仍可能包含 Agent 工具输出，继续由 Git 忽略。

接口来自网站当前公开前端，可能随平台更新；此前实际完成网站登录、上传、启动、Demo 单项评测和证据下载。云端环境与脚本实测见[并发与 API 报告](../../reports/2026-09-20-playground-concurrency.md)，早期协议调查见[开发闭环调查](../../reports/2026-09-20-development-loop.md)。当前新增参赛包入口与标准 frontend/backend 交付；hosted runner 仍不能直接替换 `--eval-host`，也尚无新包的正式平台模型成绩。

## 并发实验

[concurrency.py](../../scripts/concurrency.py) 的 jobs 表示彼此隔离的评测任务。每份任务独立复制冻结应用、分配服务端口并保存报告；每份官方 Playwright 评测仍使用 1 个 worker、零重试。官方 runner 强制单 worker，且用例共享应用状态，不能直接增加同一应用的测试 workers。

```sh
# 在已有 runner 和浏览器缓存的 WSL 仓库执行；不需要比赛密钥。
python3 scripts/concurrency.py eval --run runs/<run-id> --jobs 2 --reference <original-evaluation-id>
python3 scripts/concurrency.py eval --run runs/<run-id> --jobs 4 --reference <original-evaluation-id>

# 在已配置比赛密钥的生成主机探测 API 并发；每组仅发对应数量的短请求。
python3 scripts/concurrency.py probe --jobs 2 4
```

通过 `python3 scripts/concurrency.py status runs/concurrency/<batch-id>` 查看当前阶段、最近完成的用例和证据入口。测试进度读取固定 list reporter 日志末尾，属于观测值；完整逐项结果仍以最终 JSON 为准。评测批次记录在 `runs/concurrency/<batch-id>/batch.json`，保留原始参考的哈希、逐项结果和各任务证据。`completed` 表示完整评测结束；`equivalent` 另外比较每个用例的身份与状态，不能用相同总分替代一致性检查。连续比较 2 路和 4 路时应显式选同一份原始参考。当前 WSL 的冻结 Keep 应用对照已验证 4 路逐项一致，类似评测可优先使用 4 路；这不代表四路完整 Agent 生成或其他任务也已验证。

冻结后 Keep 评测不调用模型；API 并发需单独测量。`probe.json` 只保存 HTTP 状态、finish_reason、usage、延迟和限流信息，不保存模型正文。探针无输出 token 上限、无自动重试，仅有单次 HTTP 连接和传输超时；这些超时不应用于完整 Agent 生成。短请求成功不能证明持续生成的并发额度。远程探针可通过 `--key-stdin` 从 SSH stdin 接收凭据，避免在远端落盘。
