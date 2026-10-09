# ARC 平台与冻结制品

本页保留当前平台规则、制品边界和费用模式。旧 Competition journal、Playground、平台追溯字段和冻结包命令迁入[历史平台合同](history/competition.md)，用于解释原件，不用于创建当前 experiment。

<a id="赛事规则与提交模式"></a>
## 赛事规则与提交模式

规则依据是用户于 2026-10-01 提供的四页[《参赛须知》原件](../references/competition-notice-20261001.pdf)，SHA256 为 `5da6b57e40cec8925b536a4535087286839b4e853df54fda37a6f169206b314e`。文件名日期是本仓库接收日期，不是规则发布日期；规则变更须记录新依据和日期。页面语义是：不勾选“使用比赛额度评测”就不会进入排行榜。

Hackathon Evolution 决赛的变化依据是 2026-10-06 接收的[决赛通知](../references/hackathon-evolution-notice-20261006.md)，本地材料与使用约定见[决赛资料指南](hackathon-evolution.md)。决赛单次容器上限为 24 小时，2026-10-08 18:00（北京时间）停止全部未结束容器；最新有效正式提交至少有一题运行记录即可成立，不能把“两题完成后取得完整成绩”误当有效提交的判定条件。后续运行须尽早取得首次成绩，不卡截止。

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

### Pi 原生补丁的生产边界

当前 Pi 0.85.1 runtime 使用 `harness/npm/patches/pi-ai-0.85.1-connection-reset.patch`，使原生有限退避重试识别供应商响应中的 `connection reset by peer`。`tooling/scripts/runtime.py prepare` 和 `tooling/linux/Dockerfile` 实际应用补丁，Linux 导出记录补丁身份并核对 SDK 文件字节。`derive-linux` 要求保留包的完整补丁集合与当前输入一致，同时核对 Pi retry SDK；旧包缺补丁时拒绝，不静默更改冻结身份。

共同 `package_agent` 的 legacy assemble、Pi material selection 和 Pi `write_zip` 装配也核对当前嵌套 `pi-ai/dist/utils/retry.js` 的完整 SHA256。SDK/锁文件升级时须同步更新该已知补丁产物身份。历史 ZIP 的直接复制不经过这些正常生产入口；已有冻结包与在途运行不会因此更新，必须另行记录实际派生或部署身份。

共享 `pi-background-bash` 补丁将同一次 flush 中积压的多个完成结果合并为一个通知，保留每个 job 的原始内容、退出详情和持久日志。单 job 通知不变，接续编号恢复读取批次全部 jobId；不更改全局 followUpMode，也不提前取消有限任务等待。Pi 连续调用工具时结果仍可能等到 agent_end 才可见，批量递送只修复收尾逐条推理，不能当作实时完成通知的保证。vv 与 Tailwind builder识别共享 error/aborted 边界；旧 runtime 的兼容装配仍使用原 guard。此补丁及 E2E 独立技能的更新须经新装配才生效，不会修改已冻结正式提交或在途运行。

### 声明 E2E 的原生 vv 包

`runtime.py linux --profile arc-core` 生产的是基础工具 runtime，不会自动安装独立的 tester.army/e2e addon。原 vv 携带 E2E 指南、wrapper 和配置，必须显式装配 addon；`build.py --e2e-runtime` 接收它，缺省只接受已经完整包含 `runtime/e2e` 的 runtime。vv builder 显式声明 `capabilities.e2e=true`；共享 ZIP 边界依据该声明核对，不因未使用的 helper 文件给其它包添加能力。模型调用前的入口也核对锁定版本、CLI、TypeScript 配置加载所需的 Linux esbuild 及浏览器动态库；缺失时报告具体路径，不将缺依赖留给 Agent 排障。dx-test 当前只声明 agent-browser，不因此增加 E2E 能力。

沿已有独立生产者构建 addon，再用 vv 的 builder 装配。所有输出和日志位于 WorkSSD，例如：

```bash
python3 variants/pi-braid-i14-e2e/tools/build-e2e.py --profile arc-core --docker-context development-2 --output runs/my-build/e2e-addon
python3 variants/pi-minimal-vv/build.py --runtime runs/my-build/runtime --e2e-runtime runs/my-build/e2e-addon --output runs/my-build/agent.zip
```

addon 的 `arc-core` 输出保留锁定 E2E npm 运行依赖及对应 Linux 浏览器动态库，不携带 Chromium 可执行文件、浏览器下载树或 npm 缓存。Docker 构建阶段使用匹配浏览器计算实际动态库闭包，导出前移除浏览器；既有 `full` profile 保持原完整用途。E2E 在实际运行的独立缓存中按锁定 Playwright 版本准备浏览器，wrapper 设置动态库搜索路径与当前 run 的缓存位置。基础 runtime 与 addon 的来源和入口 SHA 分别记录，不能因基础包名为 core 就宣称 E2E 已装配；旧已上传包不会随源码修改自动生效。现有完整版 addon 也可作为显式输入，vv 成包时仅复制必要运行依赖和动态库，移除其浏览器与缓存。

## 决赛保存快照与多题执行的顺序

2026-10-07 实测，同一 competition 后保存的 Agent snapshot（包括 `self_funded` 独立应用评测）会阻止较早 submission 再创建 task run。对较早正式 submission 调用正常 `POST /runs` 返回 HTTP 409：`Runs must use the latest saved agent submission for this competition`；官网旧快照的“Run remaining tasks”也显示 `Superseded by a newer snapshot` 并禁用。这是创建运行的 latest-saved 门控，与最终有效正式成绩或选榜规则不同，也不是仅由当前是否有活动运行决定。

同一正式 submission 要完成多题时，应在保存其它快照前完成其全部 task run 的创建/启动，或先协调独立评分顺序。不要从本地实验获授权、比赛费用模式或活动 run 列表为空推导旧 submission 仍可创建运行。已检查的官方客户端提供 create/start、rerun、delete，但未发现正常同 ID resave/reactivate/reorder 入口；不能用其它低层操作绕过已明确拒绝的门控。删除较新快照是不可逆动作，必须另有用户对具体对象的授权，不是默认的自动恢复策略。

2026-10-07 已实际验证一次恢复：非参赛 GitHub 评分快照 `f5e6af12b53c` 阻止正式提交 `e2f81e564251` 创建另一题。下载并核验评分 run `908d359c544b` 的完整 `project.zip` 后，按用户授权删除该快照，History 读回确认 `e2f81e564251` 恢复为最新；随后同提交的正式 GitHub run `7746d1de4b92` 创建、启动成功。删除后旧独立评分 run 仍可 GET 200，8/30 结果保留。证据见 [History 读回](../../runs/pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/history-after-deletion.json)、[评分保留读回](../../runs/pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/independent-run-retention-after-delete.json)及[正式启动回执](../../runs/pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/run-started.json)。这证明该次 latest-saved 门控可恢复，不等于核验过所有排行榜采用规则或所有删除场景。

需要在正式提交之后保存临时自费评分快照时，可以在用户授权覆盖该具体操作的范围内，按“评分、归档、删除临时快照、读回恢复”的顺序执行。先冻结来源应用并记录原正式 submission、已有 task runs 和最新快照顺序；独立评分明确使用 `self_funded`，不选参赛或选榜。评分到终态后，保存原始评分回执、来源应用、Agent/差量制品与完整 `project.zip`，核验 ZIP 可读取和 SHA256。随后读回该临时快照的身份及 `can_delete`，只删除授权对象，再确认原正式提交恢复为最新、原正式运行和评分记录保留。若期间另有更新快照或恢复结果与预期不同，重新协调顺序，不能据旧证据直接继续创建正式运行。

官方删除会永久移除 submission 记录及其 Agent runtime 目录，task run 的保留不代表这些材料仍可下载。因此完整项目下载和核验必须在删除前完成；删除后的运行记录不能代替本地归档。已有授权覆盖上传、评分和删除闭环时，不重复请求确认。

官网 project.zip 可能携带运行时下载的 Chromium、npm 依赖缓存等开发环境。2026-10-07 用户授权本任务下载包精简：先保存官方原 ZIP 的来源、大小、SHA256 及完整性回执，再按实际路径移除开发依赖、工具/浏览器运行环境和可重建缓存，保留应用源码、业务数据、公开需求、官方评测记录、截图及原生/Braid 过程证据。`.factory26`、`.factory-e2e` 同时含环境和证据，不能整个排除；不明确的成员保留。精简后逐成员核对保留内容字节与源包一致，并验证新 ZIP CRC，成功后才释放原 ZIP。另存删除路径/理由/大小、源与新 ZIP 哈希及核验结果；原下载回执保持不变。当前本地 project.zip 若已替换为精简版，必须结合旁置精简回执解释，不能将新哈希作为官方下载字节或完整可恢复环境的证明。
