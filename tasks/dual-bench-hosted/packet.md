# 每个 variant 覆盖 Lite 与 Web 的官网矩阵

## 目标和当前状态

用户将本轮目标改为：四个既有冻结 variant ZIP 各在官网 ARC-Bench-Lite（Keep、BookStack）与 ARC-Bench-Web（12306、BookStack、Ctrip、Keep、PrestaShop、Stack Overflow）取得完整评分。variant 之间仍依次上传；同一 variant 的两个 Competition 尽可能同时运行。用户允许真实模型调用，但没有主办方生产 Runner 镜像或源码。本任务不把本地复现设为官网评分前提；本地公开部分按 [隔离环境 packet](../local-official-bench/packet.md) 改进并标出差异。

控制状态：用户已批准开工，设计、验收、独立预演与实现均已完成；新双比赛矩阵正在官网运行，尚未取得 32 项完整评分。旧 Lite 控制器 PID 35711 已退出，新矩阵复用其三个已有 journal。移交前 GLM/Keep `cc4afd58c444` 已收集，BookStack `23cf3569040f` 已启动且 `pending=null`；mixed 与 DeepSeek 的 Lite 两题均已收集。运行状态以当前每比赛 journal 和平台只读观测为准，不以旧 `matrix.json` 推断远端终态。

## HLD：权威与所有权

主办方的两个 Competition 分别拥有 submission 历史、最新快照与 task run；同一 ZIP 可分别作为两个比赛的 snapshot，两个 `submission_id` 和每题 `run_id` 独立。`competition.Controller` 已按 `competition_id` 锁定并持久化单比赛 journal，继续拥有 POST 的不确定结果、恢复、日志游标和终态收集。矩阵控制器只拥有跨比赛排序：当前 variant 的 Lite/Web 两侧都取得预期题目的终态评分及实际测试总数后，才允许任一比赛上传下一 variant。低分或官网 FAILED 且评分完整是有效结果；设施中断、PAUSED、未知、缺分保持当前 variant。成功一侧不因另一侧受阻而重建 submission 或 run。

同一 variant 的两场比赛各用一个 controller 并行推进；每场比赛内部可沿用 `run_all()` 的逐题执行与等待。客户端同时提交两个 Competition 不保证平台一定同时分配执行槽，报告需区分已启动、排队和实际运行区间。现有已完成 Lite 分数复用，不能把 mixed/DeepSeek 事后的 Web 补跑称为两场同步开始；GLM 当前 Lite 保留远端原 run，不从头生成。

## LLD：已有接口与关键失败合同

- `competition.prepare(directory, package, competition_id, variant, tasks, model_config)` 会复制并核验冻结 ZIP，目录已有相同身份时只读复用；同一个 `{variant, competition}` 使用唯一 journal。`Controller.__enter__` 持有该目录及该比赛的排他锁。
- `Controller.snapshot()` 只允许上一份最新快照的全部任务有终态 run 后上传新 variant；`create()` 在写入前核对本比赛最新 snapshot。任何 POST 结果不明时 `pending` 留在 journal，先调用只读恢复，不能换状态目录重发。
- `run_all()` 当前按声明顺序创建、启动和等待一场比赛的任务。矩阵可用两个 worker 调用现有方法；两侧都 complete 且 `score_status=complete`，并且各题 `total_tests` 与本次平台 detail 的预期数一致，才推进下一 variant。预期数：Lite 32/34；Web 138/34/126/32/87/67（2026-09-23 平台只读实测）。
- 旧 `official_matrix.py` 只有 Lite、硬编码四 ZIP/两题。改造应保持原冻结 ZIP SHA256、兼容读取旧 Lite manifest，并新建双比赛 manifest 与矩阵目录。新矩阵的 Lite 入口可用 `hosted/<variant>/arc-bench-lite` 符号链接引用旧 journal，Web 用新的 `hosted/<variant>/arc-bench-web` 目录；Controller 会解析真实目录与既有锁，不复制第二份可写 state。不覆盖旧 `manifest.json`、旧 `hosted/<variant>/` 或用户未提交文件。实现前先安全移交旧控制器：确认 PID/所持锁、保留远端 run、不调用取消；旧进程退出后核对 GLM journal/pending，再让新控制器成为唯一写入者。若旧进程仍推进 V&V，不能另起并发矩阵争用或抢先上传。

## 验收设计与独立预演

1. 固定四个现有 ZIP 的 SHA256、variant/model/visual model 与两个比赛八题任务清单；平台 detail 只读校验 competition/task identity、测试数及不需 template。若 Web 要求模板或额外上传字段，停在协议边界复核。
2. 用 fake Competition controller 和 barrier 验证：同 variant 的 Lite/Web 两侧能重叠启动；任一侧缺题、缺评分、测试数不符或 PAUSED 时，下一 variant 的两侧都不上传；完整低分继续；重启不重发成功侧 POST；跨比赛 journal/锁彼此独立。测试只覆盖可观察控制行为，不复制内部实现。
3. 移交旧 Lite 进程时记录旧 PID/退出状态与远端 run ID，核对旧 journal 中 mixed/DeepSeek 已完成、GLM 的 live run 不被取消且 pending 可恢复。先补 mixed、DeepSeek 的 Web；GLM 两侧收齐后再开始 V&V。若当前旧程序已自行推进，先据实际现场重新排顺序，不能盲目复用此计划。
4. 官网八题/variant 全部收分后，按比赛分别保存 task/run/submission、ZIP SHA、测试数、通过数、成本可归因性、时间及日志入口。用户本轮要求的四 variant × 八题总计 32 个 task run，其中已完成的 Lite run 计入；不自动开启后续实验。
5. 本地使用按 `{competition, task}` 从平台官网只读接口冻结的 YAML/Markdown/公开测试及素材；公开 Web 实际发现 478 项，官网列示 484 项仍是差异。Web Keep/BookStack 的公开测试内容与单一上游 Git checkout 不同，不能再用题名选同一测试目录。隔离目录中 213 个可取得素材与公开仓库对应文件逐字节相同，3 个被正文引用的素材平台亦返回 404；八题平台公开输入已通过主办方 `--prepare-only`。缺生产 Runner 镜像时，只能称为 `platform-public-local` 诊断，不取代 hosted 分数或制造补足的未公开用例。

独立 Advisor 只读审查建议保留 `competition.Controller`，仅调整矩阵为“variant 串行、两个比赛并行、八题评分齐全再推进”，并指出旧 Lite 控制器必须先移交。尚未做源码改动或平台写入。需要通过一次有界平台试运行或已存证据，区分“客户端能同时启动两个比赛”与“平台确实同时调度执行”；无证据时并发仅作请求策略，不宣称平台槽位。

独立 Agent 的隔离预演已完成：现有 `test_competition.py` 18 项、`test_official_matrix.py` 4 项均通过；临时 fake 证实不同 `competition_id` 的 controller 可同时进入、相同比赛的不同状态目录被同一比赛锁互斥、符号链接指向旧 Lite journal 时 `prepare()` 复用原输入。现有矩阵测试只覆盖本地 slots，不覆盖 hosted 双比赛屏障。实施后的最小回归须模拟两个比赛同时进入、任一侧 PAUSED、缺题、缺分或测试数不符均阻止下一 variant，以及一侧完成而另一侧 POST 不确定时重启不重发成功侧。旧 GLM journal 必须保持相同 ZIP SHA、模型配置、任务顺序和 display name；旧控制器释放锁且重读 `pending` 后方可接管。

## 已实施与运行移交（2026-09-23）

用户已明确开工，实施前提交 `b65e95b` 只包含两个任务包。旧 Lite 控制器 PID 35711 已在确认 GLM/BookStack run `23cf3569040f` 启动、journal `pending=null` 后本地停止，远端 run 未取消。新矩阵 `runs/competition/iteration-throughput-dual-bench-20260923/manifest.json` 与旧四个 ZIP 的 SHA256、模型配置、顺序完全一致；八个 task ID 与当前平台官网公开 detail 的测试数一致。三个已有 Lite journal 通过符号链接在新矩阵复用，`competition.prepare()` 已逐一核验身份。

矩阵实现复用 `competition.Controller`，每个 variant 的 Lite/Web 两侧并行，双方都完整评分后才进入下一个 variant；旧单比赛 manifest 仍可恢复。`make test` 132 项通过，本地链接与 `.venv/bin/svc status --json` 检查通过。新矩阵官网执行由长任务 Agent 持有，终态以每比赛 journal 为准；尚未取得本轮完整 32 项评分。 本轮 mixed/Web snapshot `44f172b6390b` 已保存，12306 run `46465ac9c58d` 已启动；同一次平台只读查询显示其与 Lite/GLM BookStack `23cf3569040f` 均为 `RUNNING`，证明两个比赛可实际同时执行（这两个是不同 variant，不能把该事实写成同 variant 同步开始）。

## 实施影响与开工门槛

已修改 `scripts/official_matrix.py`、其直接行为测试，以及 `docs/deployment/index.md` 的矩阵运行说明；复用现有 `competition.py`，没有新增调度服务、全站锁或第二套评分实现。官网最多为四个 ZIP 各保存 Lite/Web 两份 snapshot、创建总计 32 个 task run（扣除已有 Lite 结果），会实际使用模型额度并占用平台队列；同一 variant 两场比赛可能重叠调用共享模型 key，不能把 Meter 总量差额伪装成逐 run 精确成本。原 Lite 本地控制器已按接管方案退出，远端 run 保留；用户其他未提交改动保持原样。

项目 AGENTS.md 对非简单开发设施改动要求诊断与方案、验收、实施计划与独立 Agent 预演、具体影响和明确开工同意、实现前提交、实现验收。各门槛已依次完成；用户回复“开工”后，已执行实现前提交和上述实施。正式运行仍遵守终态评分屏障；出现不确定写入时先只读恢复，不重发 POST。
