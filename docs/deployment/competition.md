# ARC 平台与冻结制品

本文说明制品与 ARC 接入的操作边界。准备开发工具和修改 variant 见 [CONTRIBUTING](../../CONTRIBUTING.md)，当前实验授权见所属 task packet；查询和恢复分别见 [证据查询](evidence.md)与[恢复手册](recovery.md)。

## 赛事规则与提交模式

规则来源是用户于 2026-10-01 提供的四页[《参赛须知》原件](../references/competition-notice-20261001.pdf)，SHA256 为 `5da6b57e40cec8925b536a4535087286839b4e853df54fda37a6f169206b314e`。文件名日期表示本仓库接收日期，不是规则发布日期。以下保留原文的规则版本；比赛安排后续有变更时，记录新依据并更新受影响内容。用户同日补充了页面操作语义：不勾选“使用比赛额度评测”就不会进入排行榜。

### 练习、正式提交与模型通道

| 操作 | 凭据与本项目配置 | 成绩与资源关系 |
| --- | --- | --- |
| 官网练习提交 | 不勾选“使用比赛额度评测”；`credential_mode=self_funded`，不启用 `allow_competition_credit`，提供自己的 API key。 | 不上排行榜、不计入最终得分；须知不限制练习提交次数，但会占用队伍评测资源，有任务运行时不能另发正式评测。 |
| 官网正式提交 | 勾选“使用比赛额度评测”；`credential_mode=official_evaluation`，显式 `--allow-competition-credit`；平台注入独立比赛 key，无需上传自己的模型 key。 | 由队长账号发起，每次同时运行两题，两题全部结束后形成提交成绩。一个队伍不能并行两次正式评测，最终取历史有效正式提交的最高分。 |
| 本地练习 | 使用本地 Runner 和本次指定的模型连接；不由官网提交复选框决定。 | 用于验证运行契约、部署和基本功能；不含正式隐藏测试，本地结果不等于正式成绩。 |

自己的 key 可以来自官方 ARC API。官方服务地址、练习用个人 key、平台内置比赛 key 是不同概念；不能因为请求发到 ARC 就认定使用比赛额度，也不能把“自有 key”自动解释为直连 Bigmodel、Kimi 等供应商。`catalog=competition` 只选题库，不决定是否正式参赛；不使用比赛额度并不要求改到 Playground 或另找一份题目。以上排名语义不能从单个返回的 `billing_mode` 字段反推；保留提交时的凭据选择与平台实际返回字段，差异照实记录。[须知第 1–2 页及用户 2026-10-01 页面说明]

须知的原始初赛窗口为 9 月 24 日 00:00 至 9 月 30 日 23:59，截止后关闭提交入口，已经运行的任务继续至完成或超时。原始额度为每队练习券 100 元 × 5 次、比赛券 500 元，并明确是可按实际情况增加的暂定保底额度。它们是该版赛事安排，不是当前余额或今日入口状态，也不覆盖后续已记录的额度增加与本轮授权。实际实验范围仍查对应 packet。[第 1–2 页]

### 计分、时限与可见反馈

正式成绩按两题汇总计算。令 `p = 100 × 两题合计通过数 / 两题合计测试数`，`b` 为两题总费用（人民币元），预计合理费用为 `1.2p`。须知给出的得分为：

- `p = 0` 时，`S = 0`。
- `p > 0` 且 `b ≤ 1.2p` 时，`S = p / (b / (1.2p))^0.1`。
- `p > 0` 且 `b > 1.2p` 时，`S = p / (b / (1.2p))^0.2`。

`p` 是 0–100 的百分数，不能用 0–1 比例直接代入；综合通过率也不是两题通过率的简单平均。费用等于合理费用时得分等于 `p`，较低时有奖励，较高时有惩罚。原文未另定义 `p > 0、b = 0` 的特例，本项目不补造平台计分规则。排名依次比较得分更高、综合通过率更高、总费用更低、提交时间更早；该版规则取前 20 队进入决赛。[第 2–3 页；公式已对照 PDF 页面核读]

单个任务最长运行 48 小时，到限平台终止运行。这个规则不能单独解释某次提前退出或 SIGKILL；具体故障仍依据本次启动、退出与平台证据判断。[第 3 页]

正式测试用例及逐条通过信息不对参赛者开放，须知允许查看总体通过率、开销和得分；可下载生成的目标应用。开放日志限于智能体执行，不包含隐藏测试的具体执行过程、断言或其他泄露内容。报告只记实际取得的统计字段；逐用例资料不可得时不推测或绕过限制。[第 1、4 页]

### Harness、需求与环境约束

允许通用应用脚手架和公共组件库，但不能预置当前赛题的页面、业务逻辑、功能组件或任务答案。智能体必须实际调用大模型完成任务，不能靠不调用或极少调用模型的固定程序释放预制答案、绕过生成过程。Factory 的恢复包和冻结应用回放属于有明确来源的实验操作，不因能上传就自动成为符合正式独立参赛要求的提交。[第 3 页；最后一句为本项目实验身份边界]

参考图用于理解页面结构、布局和视觉关系；功能测试中的元素定位与交互要求以需求文档描述和场景为准，未明确要求的内容不作为功能测试目标。读取图片时应排除广告、浏览器界面和无关数据，不能把图片噪声提升为业务义务。[第 3 页]

官网网络只放行比赛所必需且明确允许的目标，例如 npm、pip、Cargo 软件源及指定 Meter/模型服务；能在本地访问或已被打入 Harness 包，不代表官网允许访问。不得绕过网络、资源或评测限制。赛事方结合自动和人工审核预制答案、泄露或绕过隐藏测试等行为；规则未明确的边缘行为由赛事工作人员确认，最终解释与裁决归主办方。[第 4 页]

本地模拟环境的来源是 [code-philia/hackathon-local-simulation](https://github.com/code-philia/hackathon-local-simulation.git)。其中 `public-exercise/arc-bench-lite` 用于了解公开需求与测试的对齐方式，不能当作 GitHub/Sheet 的正式测试或替代成绩。[第 1、4 页]

## 参赛包与平台边界

### 准备冻结包

参赛包复用本项目的 Braid + SVC 生成、Git 交付冻结和原生证据归档。
每个 ZIP 固定一个 variant 及其全部能力材料；根目录 `main.py` 接受平台传入的需求，不读取本地 benchmark，也不执行评测：

```sh
python3 scripts/package_agent.py --variant pi-braid-i13 --output runs/packages/pi-braid-i13.zip
# 以下命令在解压后的 ZIP 根目录执行，并由调用环境提供模型变量。
python3 main.py /path/to/requirements --output-dir /path/to/output
```

构建需要可用的 Linux x86_64 Docker daemon。默认尊重标准 `docker context use` 或 `DOCKER_CONTEXT`；`--docker-context` 只用于显式覆盖本次构建。runtime 在构建开始时冻结实际 endpoint，后续 build/create/cp/remove 共用该连接，不受中途 context 切换影响。源码、Git 和制品留在 Mac，远端只运行容器。
脚本只发送指定构建输入，不上传整个开发目录。
Braid 从当前 `sources/braid` 构建；团队 variant 从 `sources/svc/skills/` 冻结自己选定的独立 SVC 技能；I13 选择 documentation、task-packet、sub-agents、verification 四项，不构建或安装 CLI；raw Codex 的 LiteLLM Python 依赖用 Linux CPython 3.12 安装到包内目录。
Node、所选核心、Chrome 及其 NSS 动态模块、常用进程工具与非系统动态库均在构建时安装并随包提供。当前 Harness 使用 Node 24，应用仍须兼容平台 Node 20.19.3。
系统资源版本由 [Dockerfile](../../submission/Dockerfile)、npm 工具版本由 [lock](../../harness/npm/package-lock.json) 固定，实际文件哈希、源码身份和执行权限写入 `package-manifest.json`。
npm lock 和 Python 依赖清单随 runtime 保留。
重复构建不覆盖已有 ZIP；普通构建无需模型 key，比赛运行时无需 clone 源码、Cargo 或开发者 venv。I13 可显式传 `--tool-env` 将 Context7/Exa 凭据放入私有制品；存放、覆盖优先级及重新构建边界见 [开发说明](../../CONTRIBUTING.md#准备实际需要的依赖)。

采用当前后台 Bash 接线的团队新包包含受管后台 Bash：普通命令运行超过 30 秒时返回任务 ID，进程保持运行；预期长任务也可由插件原生 `background: true` 参数直接后台启动。当前 Pi 会话中可用 `pbb list`、`pbb status <ID>`、`pbb tail <ID>` 查看状态与日志，`pbb kill <ID>` 明确停止；记录保存在该次工作区 `work/home/.pi/pbb/`。命令显式传入的 `timeout` 仍是会终止进程的硬期限，不能与自动转后台阈值混淆。会话关闭会清理其后台进程；原已冻结 ZIP 和暂停的 run 不获得此能力。

入口要求 Linux x86_64 和 CPython 3.12。
它先校验所有载荷并恢复 ZIP 解压丢失的执行权限，再在临时工作区直接启动原生程序。
包、需求、会话配置和交付身份仍由入口分别校验并记录；文件访问限制与网络白名单由运行平台负责，入口不再装配 Landlock 或其它自建沙箱。

平台通过 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 注入文本连接；`MODEL` 若提供须与根角色一致。
可选完整 `VISUAL_API_KEY`、`VISUAL_BASE_URL`、`VISUAL_MODEL` 只供视觉角色使用，不覆盖主模型；仅有默认 VISUAL_MODEL 不视为提供了视觉凭据。
视觉地址启用时须同时提供对应 key 与模型；这只是 endpoint/key 路由分离，不代表账户 quota 已隔离或由 Harness 分配，未设置视觉地址时视觉 provider 回退到文本 endpoint/key。
冻结 variant 的主模型和视觉角色与平台模型不一致时拒绝运行，避免改变实验条件。
配置与清单保存环境变量名，不保存 key；运行时只传递实际需要的凭据。

应用交付遵循官方标准布局：`frontend/package.json` 提供 build，`backend/package.json` 提供 start；后端在 `HOST=0.0.0.0 PORT=3000` 下提供前端产物与 API，目标应用兼容 Node 20.19.3。
包内 Node 24 用于 Harness，不能推定部署环境也有 Node 22。
禁止依赖本地模拟器专用的 `deploy.sh`。
入口只在生成成功并冻结后复制应用，保留平台预置的 `.arc`、`.git` 和 `requirements`，拒绝覆盖同名应用文件。
输入可为独立需求快照，或输出目录原有的 `requirements/`。
证据保存在输出的 `.factory26/<run-id>/`；`run.json` 描述生成，`delivery.json` 单独描述交付成功或失败。

### 冻结官网 journal

以下 Competition 流程属于旧冻结 `competition.py` 入口；当前新写入见[Lab 执行合同](../../lab/exp/execution.md)。旧入口统一记录 ZIP identity、submission snapshot、task run、日志游标与终态收集。
通用参赛包只需满足平台的根入口 `main.py` 与 `requirements.txt`；Factory 包另有 `package-manifest.json` 时，Competition 会核对其中每个文件的哈希。所有包的冻结身份仍是 ZIP SHA256。
`prepare` 不写平台；其余写入按批准的实验范围执行，任何 POST 结果不确定都先保留 journal，再只读核查，不盲重试。
`prepare --credential-mode self_funded` 使用自带模型 key，也是旧 journal 缺失该字段时的历史语义。
费用来源、模型通道及是否正式参赛按本轮实验 packet 分别确定；当前 I13 范围见 [I13 packet](../../tasks/iteration13/packet.md)，不在长期手册保留易过期的全轮通道结论。页面复选框与 API 凭据模式的对应关系见[赛事规则](#练习正式提交与模型通道)。选择平台 `official_evaluation` 模式时使用 `prepare --credential-mode official_evaluation --allow-competition-credit`；源码把该显式门控冻结在 inputs 中，后续写入继续核对。模型 API 通道与官网生成场所是不同决定，不能仅从“使用 ARC”推导改成官网生成或使用比赛 key。旧 journal 仍可读取和收集证据，其存在不授权新正式提交或自动接续。
凭据模式与 ZIP、模型配置一起冻结在 inputs.json 中，重用目录时必须相同；改变模式使用新的状态目录。后续 snapshot/run-all 从该记录取值，不另传开关。
摘要的 credential_mode 是请求模式；实际运行返回的 billing_mode 另保留在 platform_result 和原始 status.json，不能混为一谈。
使用 `self_funded` 时，冻结模型配置与自带 key 对应的服务地址一致；使用平台额度时，记录实际请求模式及平台返回的计费模式。不能把旧 journal 的费用配置无条件复用到新实验。
预算决定以 Braid session 为边界，七类昂贵模型合计只允许一个 Braid session 使用；Pi 原生会话和 sub-agent 不单独占用 Braid 名额。
当前团队源码以 CLI binding 对应的 Braid 逻辑成员领取名额；上下文重建沿用同一成员，原生子会话不另占名额。旧冻结包不包含这项修正。
限制是模型使用权限，不是金额上限；一个长会话仍可能很昂贵。
实现与下一轮修复范围见 [预算与交付任务](../../tasks/competition-budget/packet.md)。

按本轮已授权的题目准备新 journal，以下只冻结本地输入，不上传或启动：

```sh
python3 -m lab.arc_bench.competition prepare \
  --state /path/to/new-journal --package /path/to/frozen-agent.zip \
  --competition <competition-id> --variant pi-braid-i13 --task <task-id> \
  --model-config /path/to/model-config.json --credential-mode self_funded
```

后续 `snapshot`、`create --task`、`start --task` 是官网写入，只有所属实验授权覆盖时执行；`run-all` 按 journal 顺序推进。写入回复未知时先用 `recover --state <同一journal>` 核对已发生的副作用。已有 run 使用 `status`、`logs`、`watch` 或 `collect`，均传同一 `--state` 和 `--task`，不因监控中断创建新 run。自动监控与间隔见[恢复手册](history/recovery.md#官网监控)。

共享操作入口通过 `Controller.launch()` 在同一比赛锁内核对 pending、snapshot、create 和 start，取得实际身份后释放锁，再交接采集；不会持锁等到比赛终态。`launch-receipt.json` 保留每次启动结果，`write-receipts/` 保存写入原响应；未确认的写请求只读核对，不自动重发。操作入口和费用范围见[恢复手册](history/recovery.md#持续执行一个已授权操作)。

Competition prepare 还可显式冻结 `--experiment-key`、`--case`、`--run-names <JSON文件>`；最后一项以 task ID 对应本次运行名。名称不替代包 SHA256、真实 run ID 或来源应用摘要；完整规则见[实验导航](../../experiments/README.md)。Playground 仍只用于显式 practice，不混入 Competition 结果。

### ARC 追溯与 Git 历史

ARC 的官网 Run detail 使用官方 SDK 写入 Runner 的 `.arc/traceability/*.json` 与 `.arc/runner-events.jsonl`。需要此能力的 Harness 可在控制器宿主导出公共工具，并在自身包构建、清单冻结之前放入 ZIP，通过自己的原生指令或工具机制将绝对路径交给 Agent：

```sh
python3 -m lab.arc_bench runtime export --output /path/to/arc-runtime.pyz
python3 /path/to/arc-runtime.pyz guide
python3 /path/to/arc-runtime.pyz version --json
python3 /path/to/arc-runtime.pyz methods --json
```

该文件包含 2026-09-25 官方 starter 的 `arcbench-agent-runtime` 0.1.0 和调用入口，运行时使用 Runner 的 `ARCBENCH_*` 路径，无需现场安装 SDK。公共 CLI 的 `traceability <方法>` 和 `events <方法>` 接受官方 SDK 的 JSON 关键字参数；`methods --json` 列出本包装器 v1 固定支持的方法与签名。操作加 `--json` 后，stdout 返回单个包含 `api_version`、`operation`、`status`、`paths`、`result` 及适用时 `error` 的结果；退出码 0 表示操作完成，1 表示失败或部分完成。旧命令默认输出仍兼容。多代理写同一个 run 时统一通过此入口调用官方高层方法；锁只保护通过该入口进行的操作。实验追溯由 Harness 从原有工作过程采集，不为填写官网页面要求参赛 Agent 额外上报；需求、接口和测试关系缺少明确事实来源时保持空白。自报的测试状态也不等于官方评分。

需要在官网展示真实 Git 提交的 Harness 可选两种命令：直接在 Runner 项目目录维护 Git 仓库时使用 `notify-history [--output-dir <Runner项目目录>] --json`；内部仓库开发时使用 `publish-history --source-repo <仓库> --ref <引用或OID> [--output-dir <Runner项目目录>] --json`。后者将选定提交及其祖先导入 Runner 项目目录的受管 Git 仓库，不改动应用文件或索引；`--preview` 在应用已就位后请求预览刷新。两种命令每次调用都尝试写入刷新信号，结果分别报告 `history_changed`、`history_updated` 和 `signal_written`；写入信号不证明官网已显示。仓库选择、轮询、重试和清理由 variant 决定。当前 Pi/Braid 团队接线从本轮运行的 `state/origin.git` 在生成中每五秒读取已发布的交付分支，交付后用冻结的交付 OID 再发布；结果写入本次 `.factory26/<run>/history-publication.json`。历史发布失败不改变应用生成结果，origin 与各 Agent 的独立 clone 留在 run state 供恢复；未合并分支和未提交文件不在发布范围内。

本地 run 与官网 task 的已保存证据可用 `python3 -m lab.arc_bench traceability <目录> [--node <需求ID>] [--json]` 查询；默认不发网络请求。它区分包内工具、实际记录与采集状态。本地保留原始表和事件，官网在既有监控轮询与显式 `collect` 时保存每次追溯及 commit history 响应或具体失败；查询分别显示提交历史的最近观察与最近可用列表的时间、来源和数量。终态若返回 `workspace_unavailable`，原始观察保留，但不会覆盖运行中已保存的提交列表。官网没有已确认的自定义文件下载能力，因此查询不会把托管工具调用日志标为已取得。通用 OTLP 仍保存 Harness 自选的 Agent 过程信号。

同一比赛只允许最新 snapshot 承接新任务。
历史接口曾在旧 Sheet run 暂停时接受新 submission，旧 run 的状态与原 journal 保持独立。该接口观测不覆盖上文正式比赛“两题全部结束后才能再次提交”的规则，也不证明任意费用模式都能并行运行。
历史双比赛矩阵由 [official_matrix.py](../../lab/arc_bench/official_matrix.py) 消费显式 manifest；它不反向解析任意 Harness 的模型配置。四组矩阵与旧日志保留其冻结条件，不能用旧配方启动新授权范围。旧冻结官网任务用 `competition.py prepare --model-config <平台模型JSON>` 显式提供 base_url、model、visual_model；POST 结果不确定时先查同一 journal，不能用新目录掩盖已有上传或 run。命名与来源关联见 [实验导航](../../experiments/README.md)。

比赛内部的 snapshot/create/start 写入有比赛锁，同一 journal 由一个 Controller 独占；已有 run 的 watch/collect 可并行。客户端并行请求不证明官网同时分配执行槽。官网评分、原生成耗时和模型用量分别记录；应用重放见[恢复手册](recovery.md)。

## 历史 Playground 操作

[playground.py](../../lab/arc_bench/playground.py) 使用网站 HTTP 接口完成登录、上传、运行和证据收集，日常实验不需要浏览器。
首次运行 `python3 -m lab.arc_bench.playground login`，交互输入网站邮箱和密码；也可以通过 `--credentials ~/.config/factory26/playground-login.json` 读取权限为 600 的 JSON 文件（email、password）。
登录验证后保存权限为 600 的 `~/.config/factory26/playground.cookies.txt`。
网站会话与比赛模型密钥分开保管，登录信息不进入仓库或命令参数。

```sh
python3 -m lab.arc_bench.playground whoami
python3 -m lab.arc_bench.playground requirements --catalog benchmark
python3 -m lab.arc_bench.playground submit --practice --package /path/to/agent.zip --config /path/to/model-config.json --requirement keep --name factory-keep
python3 -m lab.arc_bench.playground watch <run-id>
python3 -m lab.arc_bench.playground collect <run-id>
```

上传前必须准备符合平台契约的 Python Agent ZIP，根目录包含 main.py 与 requirements.txt。
`submit` 要求通过 `--config` 显式提供网关和模型，并使用仓库外比赛密钥；配置不会改变 ZIP 已打包的核心或工作流。
清单明确标记 configuration_scope=model-settings-only，包身份以 SHA256 为准。
历史 `--offline` 记录使用非凭据占位符，不代表真实模型连接。
包哈希、已确认的 submission/run ID 与执行阶段记录在 `runs/playground/upload-*/submission.json`，便于写请求失败后查明已经完成哪一步；传输结果不明时不自动重复 POST。

该历史客户端的续跑、启动和取消只接受清单中明确记录为 practice/probe 的 ID；分类不替代当前任务授权，未知或正式 ID 不由此入口启动。

同一包重跑使用 `python3 -m lab.arc_bench.playground run --submission <submission-id> --requirement <requirement-id>`，避免重复上传。
已创建但尚未启动的 run 使用 `start <run-id>`；明确结束云端执行使用 `cancel <run-id>`。
中断本地 `watch` 只停止等待，不改变云端 run。
401 表示需要重新登录。

`status <run-id> --saved` 可只读重放已归档状态，不联网、不改旧产物。
摘要分开列出最近有效事件、心跳和采集时刻，缺少观测时间时明确未知；不使用文件 mtime 猜测。
traceability 没有显式记录时显示未建立关联，不能由 SDK 自报 passed 推导外部评测成功。
`status` 输出阶段摘要，`watch` 默认每 180 秒读取状态和增量日志，只在 PASSED、FAILED、CANCELLED 或 PAUSED 时收集证据、输出摘要并退出；可用 `--after-event` 跳过已处理的同一结果。
运行中无变化保持静默，PAUSED 表示需介入而非完成；运行中的计数不作为完整成绩。
观测超过 360 秒标为 stale，不据此推断远端已经停止。
平台曾将实际耗时返回为 0，因此终态摘要用 started_at/finished_at 计算 elapsed_seconds，并汇总测试状态；原始时长字段保留在 status.json。
`collect` 将状态、日志游标与分块、traceability 和 commit history 保存到 `runs/playground/<run-id>/`。
JSON 的凭据字段会脱敏，但原始日志仍可能包含 Agent 工具输出，继续由 Git 忽略。

这些接口来自当时的网站公开前端，可能随平台更新；此前实际完成网站登录、上传、启动、Demo 单项评测和证据下载。
云端环境与脚本实测见[并发与 API 报告](../../reports/2026-09-20-playground-concurrency.md)，早期协议调查见[开发闭环调查](../../reports/2026-09-20-development-loop.md)。
Playground 与 Competition、本地评测具有不同身份，具体参赛包的成绩以其冻结身份和正式结果为准。
