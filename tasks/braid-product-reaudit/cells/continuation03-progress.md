# continuation-03 当前进展与墙钟关键路径

只读截面：2026-09-28 10:38—10:41 UTC。03 从09:20:00.180 UTC启动，截至用户10:38问询为78分钟；本页不将08/09既有成果计成本轮新增，不做token归因。实际入口与部署来源见 [09准备记录](attempt09-package-preparation.md)。

## 当前结果

GitHub 已完成本地交付，不再生成。03新run `pi-braid--hackathon--github-3d75045c72f1d6` 的run.json为finished、result.status=completed、container_exit_code=0，finished_at=1790590214.498（10:10:14.498 UTC）。实际stdout输出 `Continuation delivered c3fb22d516fd9de3dcd6a554b06948ae66ae1fbd`；Braid result.json为quiescent、根Issue CLOSED，数据库没有OPEN工作项。发布应用SHA为 `7105ac6ecbdde321db117eca9aa84e963cd3de03da175d785f6e3cc7bf81c650`。main实际提交c3fb22d于10:03:47合并PR13。旧local_run仍显示running、保留8条范围关闭后的queued输入，不能覆盖成功交付结果，也不能单据此诊断死锁。

GitHub评分尚未启动，因为现有run-experiment.py同步等待两题lab generation全部结束，随后才package_arc_replay并创建统一评分矩阵。当前controller仍generating是在等待Sheet，而不是GitHub还在工作。GitHub生成从03启动到lab收尾约50分14秒；到10:38另有约27分46秒等待同批Sheet。交付完成不等同已获外部评分。

Sheet尚未完成，但有新的实质推进。10:38:58 UTC，PR20合并为 `db23b1f38baffe5da130a5076b9b30b8f18bd218`，父提交c4d5703与779c560；随后Issue4（REQ-2生命周期和结构）关闭。10:39截面仅根Issue1与Issue5（REQ-3编辑/范围/undo）仍OPEN，没有OPEN PR。REQ-3的结构undo跨表引用恢复分支有10:29:53的 `6568ded`（实现）和 `8362408`（单测），等待REQ-2合入前提现已满足；它尚未进入develop，不能把该分支已有代码等同最终交付。

当前关键路径是：REQ-3跟进分支消费db23b1f并完成受影响验证/PR交付 → 合入候选 → REQ-5/公式/CSV在变化后的前提上完成必要复验 → 根整合develop到main并交付 → 两题统一评分。没有证据显示额度或Harness P0阻断；10:36最新现有monitor为Sheet active4/pending59、native约10秒前、failed_turns_since_start=0、recent_provider_errors为空。但计数本身不证明有效推进，判断依据是下面的Git与原生动作。

## 增量成果和时间分解

| UTC | 直接锚点 | 对关键路径的意义 |
| --- | --- | --- |
| 09:20:00—09:20:46 | 控制器启动，约11秒进入Braid；两题GLM首次新toolUse | 本轮没有再次耗费约10分钟展开大包；03启动材料成本不再主导 |
| 09:27:42—09:47:04 | Sheet REQ-2结构/undo接线、API/浏览器检查提交；09:45:12 01c5c81，09:47:04 80eefdd | 实现及检查逐步收敛，并非仅后台等待 |
| 09:49:51—10:00:53 | Sheet 61c8ce8跨表复制/剪切来源绑定，PR21合并24f24a0 | 修复跨表误用当前表坐标、可能错误搬走数据的真实产品问题 |
| 09:51:10—10:03:47 | GitHub bb9bbe6种子与团队解析修正，eec19cf检查对齐；PR13合并c3fb22d | 最终整合仍发现实际需求偏差；不能把全部整合验收视作冗余 |
| 10:03:47—10:10:14 | GitHub合并后最终交接、关闭及归档发布 | 约6分27秒是合并到lab收尾的上界，未分离模型交接与归档的各自耗时 |
| 10:07:50 | Sheet PR22合并c4d5703 | 增加公式复制越界和源不变检查；属于检查成果，不冒充功能实现 |
| 10:16:29—10:16:36 | Sheet b7da76f产品收尾修正、779c560并入develop | 修复pivot源表删除守卫、越视口菜单、CSS括号；候选随后接受运行验证 |
| 10:29:36—10:38:58 | PR20 comment302报告最终head证据；303静态核对；305独立核验；合并db23b1f | 约9分22秒处于收尾核验/ready交接；其中独立worksheet浏览器复跑明确耗6.1分钟，不能全归为闲等 |
| 10:29:53—10:39:27 | REQ-3跟进分支已发布；原生git diff确认779c560与合并树db23b1f相同 | 串行依赖等待约9分钟；合并后直接复用等价树证据，已开始减少重复工作 |

## 新原生证据与重复成本

Sheet父09工作区为 `attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation/template/.factory26/20260928-025746-66feadac`。数据库为其中 `braid-state/braid.sqlite3`；Git为 `braid-state/origin.git`；以下路径均相对此根。

- 根会话 `work/native-homes/pi-glm-fast-01a0e750-a07f-71c3-8011-5811e8dc7193/2026-09-28T09-20-37-323Z_01a0e750-f3cb-7190-89fd-06143726d5b6.jsonl`，10:39:39—40实际读取comment307、fetch、查询Issue4和OPEN PR；收到Issue4 CLOSED、develop前进的工具结果。
- Issue5会话 `pi-deepseek-fast-01a0e750-992e-74a1-aad9-11e39a25a178`，10:39:23工具输出正在完成req3-core用例；10:39:26—27执行 `git diff --stat 779c560 db23b1f`，结果为空，并读取合并双亲。它在确认可消费的依赖变化，不是模型完全静止。
- REQ-2核验会话 `pi-deepseek-fast-01a0e785-5533-7420-bef0-7ce8e74cf8ec` 的原生toolResult保存了REQ5浏览器 `10 passed (1.4m)`、`REQ5_ALL_PASS`、`REQ5_ALL_EXIT=0` 和last-run passed。10:39:41也记录对不支持的 `stateReason` JSON字段查询失败后立即改用正常view并得到CLOSED；这是可恢复的接口误用，不是P0。
- 公式复验会话 `pi-glm-fast-01a0e797-fea5-7f03-9c54-a1373d4d3ae2` 在10:39:29检查新结构路由，10:39:37于 `/tmp/issue6-verify/backend` 开始npm install，准备引擎及formula-api复验。这是新的构建/验证成本；当前结构管线确有变化，不能仅因又安装就判冗余。

PR20 comment305和实际779c560/b7da76f提交对应两处浏览器才暴露的产品错误：pivot删除守卫读取存储模型不存在的字段；底部菜单Delete项落到视口外。原来的单测fixture自行带了不存在的字段而保持绿色；后续修正fixture并补浏览器验证有具体价值。CSS缺失一个闭括号导致REQ5下拉定位错误，修复后同两条用例转绿。此处评论提供因果解释，真实Git修改与原生通过输出相互支持；本支线没有重新运行应用验收。

PR22描述还记录09:33与09:42两轮全量检查期间多台per-spec server消失、watchdog重启，分别引起不同用例失败。这是环境干扰的线索，尚未在本轮独立追到kill的进程与责任源，不能直接断言由Braid清理或CPU争用造成。4g/2CPU是限制事实；这里没有CPU利用率、调度等待或OOM的直接证据，不将其当已证根因。

## 优先优化判断与边界

1. 已有交付应尽早获得评分反馈：GitHub完成后受两题批量屏障阻隔约28分钟。可独立评分会缩短“首题结果时间”，但不缩短Sheet本身的生成时间；需要另行设计/授权，不在本次改变控制器。
2. 将复核范围绑定到具体命题、候选变化和现存证据，而非每层负责人默认重跑。PR20的最终head从10:16就存在，作者/Issue owner/根经历多层核验，最新阶段有6.1分钟独立浏览器复跑。相同树的可信现存输出和必要的针对性独立核验可减少重复；不能因此省去此次真正发现产品缺陷的浏览器验收。根comment308明确779c560与db23b1f等价、无需等价性重跑，是已发生的正向收敛。
3. 尽量让后续工作先完成与未就绪依赖无关的部分，前提就绪后立即推进。REQ-3已先发布两个提交，10:39后确认同树依赖，这是有效并行；还应观察它是否快速进入PR/最终候选。单纯增加更多Agent或更多临时工作树不能保证缩短这条依赖链。
4. 环境反复建服、安装及不明清理值得单独取证，但当前不足以证明持续P0或整轮无效。不能为省时间移除必要验收，也不能把错误期望、真实产品bug和环境失败混为一种“测试慢”。

本页只读取run记录、数据库、Git提交和定向原生尾部，没有改源码、应用、运行状态或发评论。GH完整质量尚待外部评分；Sheet最终完成时间不能从当前active计数预测。token及上下文成本由另一支线分析。

## 10:54 UTC：改为每题完成即官网 self_funded 重放

用户授权每题独立应用重放，不等Sheet。主线程已处理GitHub官网run `3583c4dd7e48`，此支线不重复上传或创建。

停止旧mock评分的处置已实施：先核实实际树为外层509773→lab前台509774→lab controller509775→Sheet生成509790（独立PGID509790），读取外层与lab源码确认无父退出传播/PDEATH配置。只向509773发送SIGTERM，未杀进程组。随即观察509774由PID1接管，509775、509790、launcher509792、docker509811继续；Sheet容器仍running。10:55—10:56有后续原生响应，证明生成没有被外层停止带走。外层已经不存在，无法在Sheet完成后调用旧score()。

远端 `attempt-09/continuation-03/independent-replay-transition.json` 保存操作时间、PID和进程树；`execution-before-independent-replay.json`保留旧记录。execution.json增加orchestration_status=stopped-before-local-scoring、lab_controller_pid=509775、scoring_mode=individual-hosted-self-funded；phase=generating是外层最后截面，后续须以generation/runs各自run.json为准，不期待已停止外层再更新。

Sheet独立接续已启动：本地 `/Volumes/WorkSSD/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/sheet-hosted-on-completion.py`，PID82066（独立session，PPID1）；同目录`.log`和`.pid`记录状态。第一次shell nohup返回PID81829但没有存活或执行记录，已确认消失后用subprocess.Popen(start_new_session=True)启动唯一有效进程82066。它每480秒只读检查已知Sheet run；completed后通过现有WSL package_arc_replay单题打包，scp到本地，再使用本地现有competition prepare→snapshot --offline→create→start。任何失败退出并保留既有journal，不自动重复create/start。

固定位置：

- WSL源run：`/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/generation/runs/pi-braid--hackathon--sheet-22730f82778f3a`。
- WSL输出包：同03目录 `sheet-artifact-replay.zip`；本地包为上述本地03目录同名文件。
- 官网journal：本地03目录 `sheet-official`，task=`hackathon--sheet`，credential-mode=`self_funded`，名称`20260928-continuation03-sheet-artifact-replay`。
- model-config：本地03目录 `model-config.json`，复用主线程GH配置；无模型回放的snapshot使用现有`--offline`占位模式，不发模型请求。

此时Sheet仍生成，尚无Sheet官网run ID。后续监控不得重复提交同一题；官网容量不足或其他错误由原始journal与脚本日志判断后显式接续。没有变更Harness、模型、应用或生成控制器，没有新增测试。
