# 官网启动与持续监控的操作接缝

2026-10-02。此次只读调查覆盖 I13-2 两条官网 journal、启动/接线脚本、已保存监控批次及 `competition.py`、`hosted_monitor.py`、`provider_liveness.py`。没有执行这些脚本，没有访问凭据文件或发送 API 请求，没有启动、停止或替换现有运行、collector，也没有运行测试。恢复制品内部与 Docker transport 由其它子任务调查。

官网已有可用的防重复写入协议和持续采集实现。手工劳动主要发生在它们之间：任务脚本自己校验准备回执、串起有限次写入、取得独立读回，再另外启动或改接 collector；没有一个持久回执同时回答“哪个获授权运行已启动、由谁负责观察、最近已取得什么证据”。不需要重写运行框架，优先补齐这段接线。

## 已有协议和边界

| 阶段 | 实际实现 | 需要保留的边界 |
| --- | --- | --- |
| 冻结 | `competition.prepare()` 复制 ZIP、校验 manifest/载荷哈希并冻结模型、费用模式、tasks、labels；`inputs.json` 与初始 `state.json` 用 `atomic_json()` 发布。相同身份允许复用，不覆盖不同身份。 | 冻结成功只证明输入身份，不证明恢复材料可用或模型已运行。任务特有的 prepare-only 回执仍须与该包 SHA 对应。 |
| snapshot | `Controller` 独占 journal；`snapshot()` 在比赛锁内读取比赛及 history，验证 task 和凭据模式，再上传。 | 只允许已授权费用模式。新 snapshot 是有副作用的官网操作，不能把新目录当作旧 pending 的重试。 |
| create/start | `create()` 核对本 snapshot 仍为最新、该 task 没有已存在的 run；`start()` 按 journal phase 避免重复启动。 | 比赛锁解决本机 controller 的竞争，不构成服务端幂等保证，也约束不了另一个宿主或网站操作。 |
| 写请求不确定 | `_post()` 先持久化 pending，成功响应也先持久化，再应用 identity。HTTP 非 2xx 的状态和正文进入 pending；未确认 pending 阻止再次 POST。 | 程序重启可应用已保存响应。没有响应时只做 GET 核查，不能凭超时推断请求没有发生。 |
| pending 恢复 | `recover()` 对 snapshot 找 prior_ids 以外的唯一新同名 submission；create 从 history 找唯一 task run，或接受显式 run_id 后 GET 验证 submission/task；start 读取已启动时间或已启动状态。 | 无唯一候选时停止是必要保护。snapshot 恢复匹配没有验证远端 ZIP 哈希，不能声称端到端内容身份已由该路径证明。 |
| 独立读回 | 启动脚本调用 status/logs/history，保存费用字段和真实 submission/run；`Controller.status()` 保存平台阶段、统计及观察时间。 | HTTP 接受、remote RUNNING、provider 已接续、有效评分是不同结论。 |

源码入口为 [competition.py](../../lab/arc_bench/competition.py)，关键位置是 `prepare:122`、`_post:289`、`snapshot:348`、`create:375`、`start:391`、`status:399`、`recover:478`。客户端 [playground.py](../../lab/arc_bench/playground.py) 的 `Client.request:81` 不重试写请求。

现有 `run_all()` 能顺序完成一个 snapshot 的任务，但其比赛锁覆盖后续 watch，不能直接代替本轮短时提交后并行观察的入口。GitHub 启动脚本因此显式取得同一比赛锁，只包住 snapshot/create/start，并设置 Controller 的私有 `_competition_locked`；Sheet 脚本则分别调用三个受锁方法。公共接口欠缺的是有限的“提交并启动，随后释放比赛锁”，而不是再实现 HTTP 客户端。

## 监控接线和职责

`hosted_monitor.main()` 在启动时确定 journal 集合（第 163 行）。循环内重读这些 journal 的 `state.json`，能发现已登记 journal 的 run identity；不会重新发现新增 journal。`run_batch()` 只读远端状态和工作区，按当前 provider 身份、恢复边界、生命周期及 native 活动判断 liveness；默认两样本且 30 分钟不变才进入疑似 stale。每轮下载完成后再安排 180/480 秒的下次采集，所以实际启动间隔包含下载耗时。

collector 独占的是 `<输出目录>/monitor/lock`。它用独立 `scheduler-v2.json` 保存 `journals`、`next`、`liveness`、`notifications` 和 `done`；重启会加载旧 scheduler，不需要重置观察窗。锁只排斥相同输出目录的 collector，不会阻止不同输出目录重复观察同一 journal。

启动 journal 保存控制器最近一次已验证观察，monitor 保存持续采集观察，这样分工本身成立。实际 I13-2 的 Sheet journal 仍是 QUEUED、GitHub 是 STARTING，而后续 collector 已保存 RUNNING/current provider active，并不证明 journal 写错。缺口是启动回执没有登记负责它的 observer、接收状态和最新证据入口；查询者必须人工知道 GitHub 证据实际在 Sheet 的输出目录，才能正确拼接当前状态。

追加 GitHub 的 [attach 脚本](../../runs/iteration13/i13-2-20261001/attach-hosted-github-monitor.py) 为这段缺口承担了完整操作：核对 started identity、scheduler/PID/启动时间/命令，避开正在到期的批次，保存交接前状态，停止旧 collector，确认退出及锁可得，启动携带两个 `--journal` 的 collector，再逐项校验 next/liveness/notifications/done。它是一次性脚本，发现旧 attach 回执便拒绝再次执行，没有可直接接续的操作入口。

终态时 monitor 保存 score/stages/原件，加入 done，所有运行结束后保存 `finished_at` 并向被重定向的 stdout 打印结果。它不会调用 `Controller.collect()`，也没有 hosted 专用 completion 回执或持有后台进程退出的上层消费者。终态工作区下载失败会单列 evidence_errors；这不该把已知平台终态改成未知，也不该将无评测计数的生成失败解释为有效零分。

通知按分类和故障签名去重，先调用 macOS 通知再追加 alerts，并在批次结束后保存 scheduler。OS 接受通知不证明人已看到；collector 意外退出也没有独立监督者代为报告。现有实现没有证明崩溃前后恰好一次投递，不能把它当可靠消息队列。

## 支持结论的真实记录

| 记录 | 已观察事实 | 对根因的含义 |
| --- | --- | --- |
| [Sheet 首次启动 stderr](../../runs/iteration13/i13-2-20261001/hosted-sheet-r2/launch.import-error.stderr.log) | 导入第 3 行因 `ModuleNotFoundError: No module named 'lab'` 失败，未进入 API。 | 临时脚本依赖调用路径；错误发生在 launch receipt 建立之前。稳定入口及覆盖入口失败的回执可替代现场修脚本。 |
| [Sheet launch receipt](../../runs/iteration13/i13-2-20261001/hosted-sheet-r2/launch-receipt.json) 与 [GitHub launch receipt](../../runs/iteration13/i13-2-20261001/hosted-github-r2/launch-receipt.json) | Sheet snapshot/create/start 于 14:45:52–58Z 成功，run `f16834f58674`；GitHub 于 15:50:49–55Z 成功，run `e1aa595f6995`。两者独立读回 self_funded，journal pending 均为 null。 | 防重复写入已有实际成功反馈。两份脚本重复的是提交编排；不同来源身份、准备文件数量及脏工作树要求是有意义的任务验收，不能盲目删除。 |
| [GitHub 旧 run 读回错误](../../runs/iteration13/i13-2-20261001/github-launch-preparation/source-readback-error.json) | 15:17:38Z，GET `/runs/377afa346c92` 返回 HTTP 500；记录明确写着正文未保留、只有错误字符串，write_attempted=false。 | 准确 HTTP 状态保住了，但一次性调用丢失 `ApiError.detail`，后续无法判断服务端具体原因。这是已经发生的失败回执缺口。 |
| [监控修正后的重启回执](../../runs/iteration13/i13-2-20261001/script-monitor/monitor-restart-current-priority.json) | 14:59:04Z，官网 collector 27102→48187；scheduler_continuity=true。此前真实 Sheet provider 观察因历史会话优先级被汇总为 historical_or_unknown，修正后为 active。 | 修正算法后还需要人工管理进程、保存身份和验证采样连续性。修复代码与应用修复是两个动作。 |
| [GitHub attach 回执](../../runs/iteration13/i13-2-20261001/script-monitor/github-attach-receipt.json) 与 [首批 outcome](../../runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T155107.297047Z/outcome.json) | 15:51:07Z，48187→245，旧状态逐项保持。首批 GitHub 为 RUNNING、deploy_agent=running/start_agent=pending、preparing；没有把平台部署说成 Pi 已恢复。 | 单纯新增 journal 就要求停止再启动 shared collector；这是静态启动参数造成的人工接线，不是新的费用授权要求。 |
| [Sheet 16:02:40Z liveness](../../runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T160101.426749Z/f16834f58674/liveness.json) 与 [GitHub 16:00:40Z liveness](../../runs/iteration13/i13-2-20261001/hosted-sheet-r2/monitor/20261001T155834.945862Z/e1aa595f6995/liveness.json) | 分别有 2/3 条本轮 running provider，native 可读、有本轮事件时间，分类 active，errors 为空。semantic_progress 仍 unknown。 | 这是有时间边界的实际活动证据；不能只凭 PID=245 声称健康，也不能外推应用完成。 |
| [GitHub 原 FAILED 状态](../../runs/iteration13/hosted-recovery-20261001/monitor/20261001T101157.239125Z/377afa346c92/status.json) | run FAILED；`main.py` 返回 exit 1，start_agent failed、run_tests pending，score=0.0，passed_count=failed_count=0。 | 这是生成失败，未取得有效评分。回执应保留阶段和原始失败原因，而不是只呈现“零分”。 |

上述时间为 UTC。报告不是持续健康断言，较新的运行事实继续以原 collector 后续原件为准。

## 哪些应由人决定，哪些应由接口承担

用户需要决定新的付费运行范围、矩阵、费用模式、来源恢复点和是否再做一次实验。pending 恢复没有唯一远端 identity、来源一致性不能成立、或修复会改变产品行为时，也需要人提供缺失事实或决定范围。既有用户授权覆盖的唯一提交、确认同一 run、把该 run 接入已授权只读监控，不需要重复征求费用许可。

系统可以承担已批准输入的身份核验、有限提交事务、GET 读回、准确失败回执、collector 接收确认、采样/通知状态保留和终态报告。手工重写 sys.path、复制几乎同款启动脚本、为了新增 journal 停止 shared collector、跨 Sheet/GitHub 目录寻找当前事实，均源于公共入口和责任交接缺失。它们不是必要的安全门槛。

## 最小改造建议

1. 在现有 Competition 入口增加有限的 launch 操作，复用 Controller 的 pending/锁/恢复和 status/history。一次获授权的 journal 完成 snapshot/create/start 后就释放比赛锁；不要把 `run_all()` 的长期 watch 直接塞进该短事务。准备回执与冻结包 SHA 的任务验收由调用方提供明确引用，通用入口不内置 786 份文件或某个 PR 的特例。无论入口校验、POST 还是读回失败，都保存同一操作回执；保留已成功步骤及 pending，不自动创建第二个 run。
2. 让现有 shared collector 消费操作目录中的显式 targets 文件，每轮重新读取。文件由启动编排在确认 run identity 后原子追加；现有 scheduler 按 run ID 保留状态，新 target 没有 next 时立即到期。保持单 collector 和现有输出布局即可，不引入注册服务。不能静默删除仍活动的 target，也不能把同一路径的 identity 变化当原运行接续。
3. 为 target 登记接收回执和首批证据入口。targets 写入只表示期望观察；collector 实际接收、最近成功采集时间、当前采集阶段/错误要可区分。现有 sleep 最长 480 秒，下载本身也可能耗时；若要求新增后及时接收，可给 targets 的本地重读设置较短最大等待，不能宣称原采集循环天然即时。重启仍复用 scheduler；重启操作只持有 collector，不重新启动官网 run。
4. 查询及终态回执同时引用 launch journal 与 observer 最新证据，分别给出远端阶段/失败原文、是否有有效评分统计、证据缺口和通知提交结果。保持分工，不要求 collector 每次重写控制器状态。直接修复通用错误记录中丢失 detail 的路径；monitor 的 curl 已把响应写到 status.json/workspace.zip，但失败时须明确标出响应文件及传输/HTTP 结果，避免把错误正文误当有效 ZIP。

targets 相比“一 journal 一个 collector”的选择：后一种方案省去动态发现，却增加进程、启动/退出回执、日志与监督责任，并需要改变本轮 shared 输出约定。当前 shared scheduler 已有两次连续性交接回执，新增显式 targets 的成本主要是重读、身份核对和接收回执，更适合本轮。若以后完全独立的运行生命周期成为明确要求，再拆 collector；现在没有必要同时实现两种所有权模式。

## 源码候选与验证限制

以下为可定位的候选问题，不是本轮已观察到的运行事故，也未在本任务中修复：

- `provider_liveness.assess()` 第 138 行的 terminal 集合不含 `passed`，而 hosted monitor 使用的 TERMINAL 含 PASSED。成功态会进入 done，但 liveness/terminal 通知可能仍按 provider 分类。已存验证只覆盖 CANCELLED 和本地 failed，不能证明官网成功通知。
- 通知签名含完整 errors/native.error；官网每批解包路径带新时间戳。同一缺文件错误若路径改变，会形成不同签名；“同一份观察重放不重复通知”的已有回执不能证明跨批次同因故障去重。
- 通知发出、alerts 追加与 scheduler 保存不是同一持久事务。崩溃窗口可能导致重复，通知提交失败也不会因同一签名自动重试。应明示 best-effort 通知和持久事实入口，不承诺恰好一次或人已读。

无需新付费运行就能使用的证据包括：本次两份 launch 成功回执与 pending=null；两次实际 collector 交接及状态连续性；真实首批 preparing 和后续 active 的转换；HTTP 500 丢正文原件；[已有操作验收](../../runs/iteration13/i13-2-20261001/script-monitor/validation/operations-receipt.json) 的 CANCELLED/旧本地终态和相同观察通知去重；[优先级修正读回](../../runs/iteration13/i13-2-20261001/script-monitor/validation/current-priority-readback.json) 的真实前后分类。这些足以确定接口接缝，不能替代新入口实际接线成功的反馈。

未来实施可用编译与获授权的现有运行只读接线操作验证，不必新建付费 run，不新增 fixture、observer 测试或改名探针。本调查没有执行新 collector 或分类回放。服务端 exactly-once、未确认 POST 的所有崩溃窗口、自动重启监督、跨批次故障通知、PASSED 通知、导出文件集合原子性，以及 native 活动代表语义进展，均没有被现有材料证明；本轮两条官网运行也尚无最终评分结论。
