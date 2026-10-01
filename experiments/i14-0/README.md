# I14-0 有限配方

本配方执行 `e20261002-01 / i14-0` 已授权的八项干净生成：`pi-braid-i14`、`pi-braid-i14-cleaner`、`pi-braid-i14-reviewer`、`pi-braid-i14-e2e` 各运行 `hackathon/github` 与 `hackathon/sheet` 一次。允许需求、完成条件和模型选择依据见 [I14 packet](../../tasks/iteration14/packet.md)，设施接口见 [I14 消费交接](../../tasks/experiment-operations/i14-interface.md)。本目录的 `launch.py` 只派发这八项，不增加题目、重复次数或恢复 attempt。

新增生成使用 `Debian-Rebuild / development-1` 的远程 Docker，每项固定 2GiB、2CPU，同 daemon 共享五槽，计入旧 I13 的实际容器及准入预留。旧 I13 的资源与模型路由保持其原冻结条件；若两个旧 I13 仍占槽，新项最多同时占三个槽，释放后才能补足五槽。单项 operation 的 worker 数为一，不能把各自 worker 配额当作宿主容量；实际准入由已有共享 registry 仲裁。

I14 使用 ARC API 的私有自有 key/额度，通道标签为 `arc-self-funded`。应用重放显式冻结 `credential_mode=self_funded` 和 `allow_competition_credit=false`，不使用比赛额度。默认根与普通 Braid 成员为 GLM-5.3-Flash / high，原生 advisor 为 Kimi K3，视觉模型为 GLM-5.3-Flash；内部 DeepSeek Flash 不成为 Braid 可指派成员。高价模型仍受每次 Factory 运行最多一个 Braid session 的既有预算保护。

## 私有冻结与启动

主线先在 `runs/iteration14/i14-0/` 冻结四个 ZIP、允许需求、Linux runtime/Braid 来源、runner、image、storage 和私有 `config.json`。配置列明八个唯一 target 的 variant/题目/包路径与 SHA256、ARC env 路径、Docker endpoint、授权及 I13 两组两题的真实评分证据绑定。凭据只留在私有 env 文件，不复制到本 README 或公开回执。不要用 variant 名推断材料已经打入包。

从仓库根目录启动，传入已有私有配置目录：

```sh
python3 experiments/i14-0/launch.py runs/iteration14/i14-0
```

dispatcher 持有目录锁，核对固定八项、配置摘要与包摘要。它逐项建立 `operations/<target-id>/`，冻结模型 env、单项 matrix、operation spec 和输入，再调用已有 operation 入口。每项 operation 持续跟随真实生成，启动既有 collector，并在成功生成和应用产物发布后立即冻结该项应用、上传官网重放、采集正式结果；不等待同批其它题，不把隐藏评分送回仍在生成的 Agent。生成失败或缺少可重放产物时记录 `skipped`，它不是有效零分；重放错误保留 `needs-review` 和具体原因。

operation 的启动回执 `accepted` 只表示已接入后台执行。dispatcher 的 `phase=dispatched` 只表示八项已派发且没有待确认准入，不代表生成、采集或评分已完成。完成判断仍需逐项读取生成结果、应用冻结身份和官网最终评分，分别记录生成与重放的耗时、费用。

## root 选择的承诺点

根模型默认使用 Flash。每次准备派发一个新 target 时，dispatcher 只消费已有 I13 journal/monitor 观察：必须同时取得 GLM 与 Flash 两组各 GitHub、Sheet 的正式最终分数，且 GLM 两题均分至少领先 10 个百分点，才选择 GLM-5.3；证据缺失或不满足判据仍选 Flash。不重新查询官网，不用阶段分数或 Agent 自报推断。

该项 `selection.json` 写入就是承诺点，保存所选 root、判据、证据入口及摘要、target 与配置摘要。尚未创建 selection 的未来项可在派发时采用后来满足判据的证据；已经创建 selection 的项沿同一选择继续，即使还在等待容器准入也不能改模型。不得原地修改 `model.env`、matrix、operation inputs、包或 manifest。若崩溃发生在 selection 写入后、dispatcher 确认前，恢复必须复用该 selection；顶层 `queued` 本身不能证明该项仍可重新选择。发生 root 切换后按根模型分层解释结果，不能合成严格同模型对照。

## 定位故障与接续

本轮入口是 `runs/iteration14/i14-0/active-matrix.json`。它索引已经存在的 operation、experiment、monitor 与实际 run 路径，并列出待派发 target；未启动项不预填 run ID。表中 `observation/` 和 `replays/` 均相对该项 operation。按以下入口定位，不另建 collector 或读取内部 scheduler 格式：

| 入口 | 要确认的事实 |
| --- | --- |
| `dispatcher.json` | 派发阶段、已确认 target、当前共享容量、进程身份及具体错误。配置或包摘要变化说明冻结前提被破坏，不能靠改状态文件绕过。 |
| 顶层 `active-matrix.json` 与该项 `selection.json` | target 对应哪个既有 operation、已经产生哪些真实 run、是否已承诺根模型。 |
| `operation status` | worker 的 phase/physical_state、已有生成 run、官网 journal、follower 回执及公开 collector 接收状态。 |
| `observation/monitor/accepted.json` | collector 身份、`collector_status`、具体 error，`accepted[run_id]` 的 `identity`、`first_batch`、`last_batch`、`last_error`，以及顶层 `done` 列表。`first_batch` 表示已采一批，需同时看错误；`done` 表示观察到终态，不表示应用通过。 |
| `observation/hosted/monitor/accepted.json` 与 `replays/<实际生成run-id>/result.json` | 官网重放是否已绑定既有 journal/run、已接入采集，或处于 skipped/needs-review。两处可能在重放开始前尚不存在。 |

把下方 operation 路径替换为索引中的已有绝对路径，先读回状态：

```sh
I14_OPERATION='/绝对路径/operations/实际目标ID'
python3 -m lab.arc_bench operation status "$I14_OPERATION"
```

worker 或 collector 失联时，先核对现有进程与 controller 回执；归属未知时保留现场。未完成生成的 controller 归属无法确认时，按既有 `lab reconcile` 契约对原 experiment 核实，不先启动新的 controller。已确认是同一 operation 的跟随或采集故障、且不存在竞争执行时，可显式重入原入口：

```sh
python3 -m lab.arc_bench operation run "$I14_OPERATION"
```

该入口消费原冻结输入、原授权 run 集和原重放 journal；它不是追加 attempt 的授权。待该项恢复回执确认后，重新运行同一个 `launch.py` 命令接续剩余派发。dispatcher 会复用已有 selection/operation，已确认项不会重新造执行。不要删掉 operation/receipt、换目录重新 prepare、手工 retry、补填 run ID 或重复上传来掩盖故障；这会丢失来源关系并可能重复收费。若确需新的生成或重放范围，先保全现有结果并交回主线决定。

持续采集由每项 operation 的既有脚本负责。独立 GPT-5.6-Luna / low 监控会话每十分钟消费已保存摘要、告警和终态回执，普通进展保持安静；不另开采集循环、重复浏览官网或反复解包。
