# ARC 平台与冻结制品

本页保留当前平台规则、制品边界和费用模式。旧 Competition journal、Playground、平台追溯字段和冻结包命令迁入[历史平台合同](history/competition.md)，用于解释原件，不用于创建当前 experiment。

<a id="赛事规则与提交模式"></a>
## 赛事规则与提交模式

规则依据是用户于 2026-10-01 提供的四页[《参赛须知》原件](../references/competition-notice-20261001.pdf)，SHA256 为 `5da6b57e40cec8925b536a4535087286839b4e853df54fda37a6f169206b314e`。文件名日期是本仓库接收日期，不是规则发布日期；规则变更须记录新依据和日期。页面语义是：不勾选“使用比赛额度评测”就不会进入排行榜。

| 提交身份 | 费用选择 | 结果边界 |
| --- | --- | --- |
| 官网练习 | `credential_mode=self_funded`，使用本次冻结的自费模型配方 | 不上排行榜、不计最终分，但占用队伍评测资源；有任务运行时不能另发正式评测 |
| 官网正式 | 已获本轮比赛授权的 Lab run 显式使用 `--competition`，上传请求选择 `official_evaluation` | 平台注入比赛 key；有效提交按当届规则判断，不能以启动受理代替成绩或最终采用确认 |
| 本地练习 | 本地 Runner 和指定模型连接 | 只验证运行、部署和基本功能；不含正式隐藏测试，本地结果不等于正式成绩 |

官方 ARC 地址、个人 key 和平台比赛 key 是不同概念；`catalog=competition` 只选题库，不能决定是否正式参赛，单个 `billing_mode` 也不能反推排行榜资格。原须知的 9 月 24—30 日窗口、额度和 48 小时上限属于该版规则，不能当作当前余额或运行状态；当前授权仍以所属 packet 和实际平台回执为准。隐藏测试逐条信息不公开，缺失字段保持 `unknown`。

2026-10-07 用户确认一个已知平台缺陷：创建时为 `official_evaluation` 的运行，启动回执可能显示 `self_funded`，但实际仍使用比赛费用。官网 start 不因这一字段差异拒绝成功回执、不降级为自费，也不重发启动请求。保留冻结的请求模式、创建与启动的原始回执及同一 submission/run 身份；这一已知例外不意味着任意 `self_funded` 运行都使用比赛费用，也不单独证明排行榜资格。

须知的计分分母是两题合计测试数，不是两题通过率的简单平均；`p = 100 × 合计通过数 / 合计测试数`，`b` 是两题总费用（人民币元），合理费用为 `1.2p`。`p=0` 时 `S=0`；`p>0` 且 `b≤1.2p` 时 `S=p/(b/(1.2p))^0.1`，否则指数为 `0.2`。规则未定义 `p>0,b=0` 的特例，本项目不补造。该版排名依次比较得分、综合通过率、总费用、提交时间；这些规则以 PDF 版本为准。

通用脚手架和公共组件可以预置，但不得预置赛题页面、业务逻辑或答案；Agent 必须实际调用模型。官网只允许明确放行的 npm、pip、Cargo 和模型等目标，本地能访问或已打包不等于官网允许访问；隐藏测试、逐条断言和泄露评测路径均不可推断或绕过。

<a id="参赛包与平台边界"></a>
## 参赛包与平台边界

参赛包固定 variant、输入、源码/模型环境和 ZIP SHA256；根目录 `main.py` 接收平台需求，不读取本地 benchmark、不执行评测、不预置当前赛题答案。通用包满足 `main.py` 与 `requirements.txt`，Factory 包若有 `package-manifest.json` 则还核对其中哈希。生成应用、平台评分、原生归档和 OTLP 完整性分别判断，能上传不等于取得正式资格。

当前运行位置分开理解：开发控制在 Mac；官方 ARC 本地 Runner 按冻结 recipe 使用显式的本地 backend（需要 Docker 时由该 recipe 声明），不能从 Mac 设备推断 Runner 或授权可用；Hosted 是独立的平台 backend。详细构建参数和凭据边界见 [CONTRIBUTING](../../CONTRIBUTING.md) 及对应 packet。

当前包构建、Linux runtime、CPython 和 Docker 输入见 [scripts 构建入口](../../tooling/scripts/README.md#构建独立运行资源与制品)；包运行要求 Linux x86_64/CPython 3.12，标准应用使用 `frontend/package.json` 的 build 和 `backend/package.json` 的 start。需要 Docker 时由官方 ARC local recipe 明确声明连接，不把 Docker 作为所有 Lab local backend 的全局条件。variant 专属的受管后台 Bash 由对应 variant 的运行入口冻结，不在本页复制其阈值和命令。

## 当前操作入口

当前新运行通过 `python3 -m lab start VARIANT TARGET TASK` 与 run 级 status、stop、pause/resume、restart 管理，具体入口及实际验收范围见 [Lab](../../lab/README.md)。平台身份、写入回执和终态由执行 adapter 保存；Hosted 不支持 pause/resume。写请求不确定时保留本 run 的原始响应与身份，先只读核对，不盲目重发。历史 experiment schema 2 的 compile/doctor/build/control 只用于其原冻结执行，不是新 run 的启动步骤。

官网评分、生成和独立应用重放的费用与耗时分别记录。应用回放必须消费已发布且哈希核对的制品，不能读取隐藏评测反馈来修改仍在生成的 Agent。

ARC/OTLP 追溯工具、Braid run 与外层 experiment run 的关系见 [Braid 诊断](braid-diagnostics.md)；证据选择见 [证据说明](evidence.md)；停止、来源导入和重放见 [恢复手册](recovery.md)。

当前 ARC Git history 通知与发布 CLI 见 [arc_bench 适配说明](../../lab/arc_bench/README.md)；其“材料存在、实际调用、采集成功、官方评测”仍分别记录，不把发布信号当作官网展示证明。

## 历史入口

规则 PDF、旧 Competition journal、Playground、旧平台自动化字段、ARC traceability wrapper 和历史四配置 Hackathon 条件保留在[历史平台合同](history/competition.md)。历史文件保留原始身份、时点和错误，不代表当前额度、平台状态或新授权。
