# 每个 variant 覆盖 Lite 与 Web 的官网矩阵

## 目标和当前状态

用户将本轮目标改为：四个既有冻结 variant ZIP 各在官网 ARC-Bench-Lite（Keep、BookStack）与 ARC-Bench-Web（12306、BookStack、Ctrip、Keep、PrestaShop、Stack Overflow）取得完整评分。variant 之间仍依次上传；同一 variant 的两个 Competition 尽可能同时运行。用户允许真实模型调用，但没有主办方生产 Runner 镜像或源码。本任务不把本地复现设为官网评分前提；本地公开部分按 [隔离环境 packet](../local-official-bench/packet.md) 改进并标出差异。

控制状态：只读诊断、HLD/LLD、验收设计和独立 Agent 方案预演已完成；**新范围的 impact handshake 尚未完成，不能修改调度源码或启动 Web 的新官网实验**。既有 Lite 与 WSL 本地进程不因本方案停止或改变。`scripts/official_matrix.py` PID 35711 仍持有旧矩阵；其 `matrix.json` 的 hosted 错误是旧观测，不等于当前远端停机。最近一次 journal 只读检查显示 GLM/Keep `cc4afd58c444` 已收集，BookStack `23cf3569040f` 已启动且 `pending=null`；mixed 与 DeepSeek 的 Lite 两题均已收集。Web 最近一次平台只读查询显示当前账号无 submission。实施前重新核对现场。

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

## 实施影响与开工门槛

预计修改 `scripts/official_matrix.py`、其直接行为测试，以及 `docs/deployment/index.md` 的矩阵运行说明；优先复用现有 `competition.py`，不新增调度服务、全站锁或第二套评分实现。官网最多为四个 ZIP 各保存 Lite/Web 两份 snapshot、创建总计 32 个 task run（扣除已有 Lite 结果），会实际使用模型额度并占用平台队列；同一 variant 两场比赛可能重叠调用共享模型 key，不能把 Meter 总量差额伪装成逐 run 精确成本。当前 Lite 运行和用户未提交改动保持原样。

项目 AGENTS.md 对非简单开发设施改动要求诊断与方案、验收、实施计划与独立 Agent 预演、具体影响和明确开工同意、实现前提交、实现验收。前三项和影响已在此包给出；在用户复核并明确同意新范围开工前，暂停源码修改、新 Web 上传及旧控制器移交。通用 AGENTS.md 另规定仅在用户明确指示时提交，因此实现前提交也需在握手时明确授权，不能擅自执行。
