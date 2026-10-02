# 阶段应用重放评分

## 授权与范围

2026-09-29协调任务转交用户新授权：“引入阶段性应用重放官网self_funded评分，即便生成未完成”；拥有`lab/arc_bench/package_arc_replay.py`与`docs/deployment/hackathon.md`。先增加Git repo/ref冻结入口，再对WSL iteration10 GitHub、Sheet当前develop各冻结一次并通过现有官网入口提交。只用self_funded，不使用参赛额度，不停生成、不读未提交工作树、不替Agent修应用/数据、不伪造published receipt，不把隐藏评分反馈注入运行中的Agent。无提交授权。

## 实施决定

复用原打包器、manifest、replay入口与Competition journal。Git模式要求一个来源run及成对`--git-repo/--ref`，ref一次解析成commit后只归档该SHA；临时目录内核标准布局并生成清单。source_application保存provisional与Git来源，provenance=git-archive-provisional。普通已发布/历史导入路径保留。

源码与文档在主仓库`/Volumes/WorkSSD/Development/factory26`修改；不覆盖当前其它任务改动。语法编译已通过；不新增或运行设施测试/探针。下一步使用本次实际两题冻结和官网提交取得反馈。

## 实验矩阵与完成条件

- GitHub来源：hotfix-02/generation/runs/pi-braid--hackathon--github-db0f28e3288046。
- Sheet来源：hotfix-04/generation/runs/pi-braid--hackathon--sheet-a2ce3ac2d41459。
- 共同原workspace位于`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/`，各自`.factory26/*/braid-state/origin.git`的refs/heads/develop。
- 各题仅一次阶段冻结，独立ZIP/官网journal，记下源run、commit、ZIP SHA和官网run ID；并行受限则先提交一题，另一题保留冻结。后续只按有意义的集成进展/新应用候选触发，不按每个commit或固定时间对同一应用重复评分，不新增调度器。
- 本任务完成条件为实现/文档完成、实际冻结结果与官网提交身份明确；评分终态独立收集，不把排队或应用交付当最终评分。缺标准布局直接报告；POST不确定先recover，不重复写入。

## 当前状态

实现、文档和本轮两题冻结/提交完成。2026-09-29 10:02:57–58 UTC在WSL各冻结一次，原生成未停止、未修改。两个标准应用布局都有frontend build和backend start；仅核查归档中的声明，未额外执行应用测试。源码语法编译和diff空白检查通过，实际打包与官网prepare/snapshot/create/start成功。

| 题目 | Git commit | ZIP SHA256 | 官网 submission / run |
| --- | --- | --- | --- |
| GitHub | `4a8f3c93e35f12c309ef06fec18e0addb298d6b5` | `cd71cc0e0ea8c60499bdca545294f7b91037b45f568228598700a5bad1ec86a9` | `8b7d75dc8cf5` / `c3e2c7d2d340` |
| Sheet | `a592c3ebf4e86d0ce1f82c39bea4579b98af4140` | `33000a7ba5354dae328979125ecb798c1740a7679e439ead102d6920cad576b3` | `ed44c08a794f` / `521964ebfae4` |

官网10:04:30/44 UTC接受两题，初次实际状态均QUEUED、`billing_mode=self_funded`；这不是评分完成。回放入口不调用模型，snapshot使用现有离线占位凭据模式，未取用参赛额度。阶段source_application的provisional、git.repository/ref/commit和原run/恢复链均已传入每题journal。

证据目录为本机`runs/e20260928-03-check-receipts/phase-replay-01/`，WSL同名目录保留冻结ZIP、manifest、逐题freeze.json及本次打包源码。ZIP传输后SHA一致；本机build-source.json记录工具源码SHA。GitHub 140文件、Sheet 75文件，未伪造published receipt。

## 终态采集交接

沿用现有`lab.arc_bench.competition watch`，前十分钟按原入口180秒、此后480秒采集；没有新增调度程序或按时再评分。初始watch PID为GitHub 99008、Sheet 99009（本机），`watchers.json`记录启动身份，终态/异常写入`github-watch.log`、`sheet-watch.log`和对应`*-official` journal。任务主线消费评分，不把隐藏反馈传给生成Agent。初次启动后GitHub watch实际因比赛锁冲突退出，后续修复和终态见下节。

读取当前结果用各`*-official/tasks/hackathon--<task>/status.json`及`state.json`；若watch退出，先查日志和journal，只有现存watch确实退出后才复用同一状态目录接续watch。不要再次snapshot/create/start，也不要重打当前两份快照。


## 监控互斥修复与最终结果

协调任务发现GitHub journal停在10:04 QUEUED，而其watch日志只有“另一个 Competition controller 正在使用此状态或比赛”。原PID 99008/99009均已退出。只读GET确认GitHub实际已于10:22:27 UTC结束，初始刷新保存在`github-status-refresh.json`；没有创建或重跑任何run。

根因是`Controller.__enter__`无条件取得比赛锁，Sheet的长watch因而阻塞独立GitHub journal。已在`lab/arc_bench/competition.py`将比赛锁移至`snapshot/create/start/run_all`：前三者保护当前snapshot检查及写入，run_all继续持锁覆盖整批顺序，内部调用复用该锁；所有Controller仍在with期间持有本journal状态锁。`status/logs/collect/recover/watch`只读远端操作不再争用比赛锁。已核对CLI与official_matrix调用者、通过语法编译与diff检查；没有新增或运行测试/探针，也没有Git提交。

用两个独立进程并行执行真实`collect`，两份原journal都成功更新为`collected`且`score_status=complete`。因两题已经终结，不需要再启动watch。原失败日志与watchers.json保留，完整终态汇总在本机`runs/e20260928-03-check-receipts/phase-replay-01/terminal-results.json`。

| 题目 | 官网run | 分数/通过数 | 失败数 | 终态UTC | 原始结果 |
| --- | --- | --- | --- | --- | --- |
| GitHub | `c3e2c7d2d340` | 4/100 | 96 | 2026-09-29 10:22:27 | `github-official/summary.json`及`tasks/hackathon--github/status.json` |
| Sheet | `521964ebfae4` | 36/100 | 64 | 2026-09-29 10:18:36 | `sheet-official/summary.json`及`tasks/hackathon--sheet/status.json` |

两题实际`billing_mode=self_funded`，deploy_agent/start_agent/run_tests阶段全部completed。官网总体标FAILED是这两份阶段应用未通过全部检查，完整计数仍构成有效评分；不是监控故障造成的零分。官网没有公开逐场景详情。`run_duration_seconds=3`属于无模型重放入口，不是原生成耗时；原生成成本仍归原WSL run。没有把隐藏反馈传给仍在生成的Agent。
