# Flash Team 与 DeepSeek Direct 的未完成运行对照

状态：只读分析；2026-09-28 03:31:40–53 UTC 为停止 Flash 前截面，03:32:32 UTC 为停止后状态。两实验均在 WSL `runs/e20260928-{01-flash-team,02-deepseek-direct}/attempt-02/generation/runs/`。Flash 两条已按用户指示取消；DeepSeek 两条仍运行。没有最终交付或评分，不能把模型 token、turn 数或分支提交直接当作需求完成量。

## 停止前的 Pi 实际用量

按 `.factory26/<run>/work/native-homes/**/*.jsonl` 中 Pi assistant message ID 去重，按消息实际 `model`/`provider` 分组；`braid-state/sessions.json` 标识 Braid 根 provider 会话，其余有原生 Pi 记录的为内部子会话。四列 token 是已结束 assistant 消息的 Pi usage，input 与 cacheRead 分列；不包含未结束请求的未知用量。成功/错误仅指 Pi 消息状态，不能判定工作有效或收费。根数/子数是观察截面内出现该模型消息的不同原生 session 数。

| 实验与题 | 实际模型/provider | 根/子会话 | 成功/错误消息 | input | output | cacheRead | cacheWrite |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Flash GitHub | glm-5.3-flash / factory26 | 4/0 | 143/0 | 140,301 | 46,115 | 4,087,232 | 0 |
| Flash GitHub | qwen3.6-flash / factory26 | 2/0 | 302/0 | 22,420,036 | 140,223 | 0 | 0 |
| Flash GitHub | minimax-m3 / factory26 | 2/0 | 174/79 | 357,593 | 49,258 | 6,906,145 | 0 |
| Flash Sheet | glm-5.3-flash / factory26 | 1/0 | 43/0 | 61,847 | 15,911 | 2,104,960 | 0 |
| Flash Sheet | qwen3.6-flash / factory26 | 2/0 | 315/0 | 23,664,848 | 141,914 | 0 | 0 |
| Flash Sheet | minimax-m3 / factory26 | 2/0 | 239/88 | 389,896 | 95,995 | 15,294,202 | 0 |
| Flash Sheet | deepseek-v4-flash / factory26 | 0/1 | 26/0 | 83,103 | 49,910 | 901,120 | 0 |
| DeepSeek GitHub | glm-5.3-flash / factory26 | 2/0 | 82/0 | 169,769 | 61,113 | 3,941,888 | 0 |
| DeepSeek Sheet | glm-5.3-flash / factory26 | 4/0 | 397/1 | 448,306 | 138,810 | 20,036,288 | 0 |
| DeepSeek Sheet | deepseek-v4-flash / factory26 | 4/0 | 170/0 | 175,926 | 148,088 | 10,132,736 | 0 |
| DeepSeek Sheet | deepseek-v4-flash-vision-exp / factory26-visual | 0/1 | 2/0 | 3,712 | 10,282 | 2,176 | 0 |

Flash 的 Qwen 两题合计 4 根会话、input 46,084,884、output 282,137，Pi cacheRead/write 0/0；MiniMax 两题合计 4 根会话、input 747,489、output 145,253、cacheRead 22,200,347、cacheWrite 0。MiniMax 的 167 条 error 消息包含此前核实的 429 RPM 错误，已结束错误消息的 Pi usage 为 0；失败请求是否计费仍须看平台账单。Qwen 的 cacheRead=0 仅是 Pi 标准化记录，本批无 ARC 原始 response usage，不能断言供应商 cache miss。Pi cost=0 也不能当真实价格。

## 同一截面的可验证进展

Flash GitHub 运行中的 Braid 起点约 02:58 UTC，至观察时约 33 分钟；8 个 Issue 全 OPEN，18 个 turn 完成、5 个失败、4 个运行，17 条评论；`develop` 与 `main` 仍为初始 1 提交，至少 Issue #6/#7 的成员分支已发布提交，但没有 PR、合并或完成的需求证据。共享基础 Issue #2、功能 Issue #3–#7 和整合 Issue #8 的依赖尚未形成可合入主干的链。

Flash Sheet 同期约 33 分钟；6 个 Issue 全 OPEN，4 个 turn 完成、5 个失败、4 个运行，9 条评论。Qwen 的 Issue #3 已发布成员分支并创建 OPEN PR #1（工作簿/工作表与 CSV）；`develop`/`main` 仍是初始 1 提交，未合并。Issue #3/#4/#5 文本依赖共享基础 Issue #2 先合入，因此 OPEN PR 不等于已完成或可在最终默认入口验证。

DeepSeek GitHub 的 Braid 约 03:04 UTC 才开始，观察时约 27 分钟；9 个 Issue 全 OPEN，只有根与共享基础两个 GLM 会话实际运行、无 DeepSeek 成员会话，`develop`/`main` 均初始 1 提交，没有成员 PR 或合并。用这一题比较 DeepSeek 模型速度没有事实基础；后续功能 Issue 仍等待共享基础/分配。

DeepSeek Sheet 与 Flash Sheet 起点相近（约 02:58 UTC），7 个 Issue 全 OPEN，7 个 turn 完成、2 个失败、1 个 interrupted、4 个运行，24 条评论。GLM 与 DeepSeek 成员已在多个 Issue 工作，Issue #4/#5 的成员分支及 `feat/shared-foundation` 有提交，但 `develop`/`main` 仍初始 1 提交、没有 PR 或合并；尚无默认入口全需求检查。其原生 vision Pi 子代理有两次响应。此例无法简单认定比 Flash Sheet 多或少完成需求：二者任务拆解、分支发布方式、依赖次序、模型分配和故障均不同。

四例的 `local_run` 在截面仍为 running，所有需求 Issue 均 OPEN，未观察到冻结应用、完整验收或评分。对比有效的是“到此刻投入多少已报告 token、哪些可见的协作/提交/PR 已发生”；需要完成需求映射、默认入口检查和合并事实才能比较有效工作。时间窗相近只限两条 Sheet；GitHub DeepSeek 晚启动约 6 分钟且尚未调用 DeepSeek 成员，不构成模型对照。

## 停止后现场与接续边界

03:32:32 UTC 读取 `Flash/attempt-02/generation/runs/*/run.json`：GitHub phase=`cancelled`、finished_at=`1790566297.4606037`；Sheet phase=`cancelled`、finished_at=`1790566294.2954664`。外层 `attempt-02/execution.json` 却为 phase=`failed`，错误为 `lab run ... returned non-zero exit status 1`，finished_at=`1790566301.8501856`；这是控制器汇总语义与每例取消状态不一致，不能把用户主动停止写成实验自身失败。Braid `local_run` 仍显示 running，是被停止后保留的现场，不表示进程仍在运行；接续须依据原始工作区和显式离线恢复流程，由主线处理。DeepSeek 外层 execution 仍 generating，两例仍 running。

来源可复查：每例包内 `braid-state/braid.sqlite3` 的 `local_run/work_items/turns/local_items/local_comments`、`braid-state/sessions.json`、`pi-timing.jsonl`、`work/native-homes/*/*.jsonl`，共享裸仓库 `braid-state/origin.git` 的 `refs/heads` 与 `develop/main`；外层及逐题 `run.json`/`execution.json`。没有读取或输出 env/key，未修改任何冻结产物或运行输入。
