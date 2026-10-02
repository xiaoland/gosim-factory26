# Token 消耗截面：官网生成链与本地 DeepSeek 07

**口径先行。**Pi 0.85.1 的 OpenAI-completions 适配器把 `prompt_tokens` 中的缓存命中与写入扣除后记为 `input`，另记 `cacheRead`、`cacheWrite`；`output` 是 `completion_tokens`，已包含推理 token。因此下文四列互不重叠；`input + cacheRead + cacheWrite` 可描述送入模型的上下文量，却不能按同一单价相加成成本。这里没有可靠的实际价格记录，故只比较各类 token。`assistant_messages` 是录入原生 transcript 的 assistant 用量消息数，**不等同 LLM API 请求数**；只有本地 `pi-timing.jsonl` 可另列 `request_start`。观察值是已保存材料的下限，不把缺失记为零。

## 范围与计数方法

本次读取 `runs/e20260928-completed-replay/{github,sheet}/source-workspace.zip` 内继承的原生 Pi transcript，按原生 session ID 和 message ID 去重，再按该官网生成链各次运行的创建时间切分；评分回放不算新生成。官网 GitHub 链是初始 `38dc`→`e4e7`(g01)→`64e0`(g02)→`6b45`(g03)→`8159`(g04)→`435b`(g05)，Sheet 是初始 `20a1`→`5d3d`(g01)→`65f8`(g02)→`3445`(g03)→`bd7a`(g04)。另从 WSL `runs/e20260928-02-deepseek-direct/attempt-07/generation/runs` 的 GitHub `20260928-030347-78b10c07` 与 Sheet `20260928-025746-66feadac` 原生目录截取 **05:27:51 UTC 至 06:26:53 / 06:27:01 UTC（右开）** 的本次新增消息，排除从 06/更早恢复复制的历史。07 两题于约 06:27 由人工热修正常取消，无生成评分。身份由 Braid `sessions.json` 映射到成员工作项，剩余已确认原生子会话单列，不把子代理用量加到父会话后再算一次。可复用读取脚本为 [token_economics.py](../scripts/token_economics.py)。

单位为 **百万 token**，四舍五入至小数点后三位；精确值在脚本输出中。`—` 表示该档案没有完整 request-start 记录或该段未观察到原生消息，绝非零用量承诺。两份官网 ZIP 是后续状态的继承快照，较早失败尝试若未保存 Pi 消息无法在此复原。下表 `session` 是观察到有用量消息的物理原生会话数，不能当 Braid 成员人数；同一会话可能跨官网分段，因此分段 session 数不能相加成唯一会话总量。

| 生成链 / 时间段 | 实际模型及身份 | assistant_messages | request_start | input | output | cacheRead | cacheWrite |
|---|---|---:|---:|---:|---:|---:|---:|
| GitHub 官网初始 38dc | DeepSeek Braid 父 | 1,937 | — | 3.414 | 1.196 | 182.746 | 0 |
| 同上 | GLM Braid 父 | 1,788 | — | 1.945 | 0.486 | 80.836 | 0 |
| 同上 | DeepSeek executor 子 | 65 | — | 0.246 | 0.076 | 3.267 | 0 |
| GitHub g01 e4e7 | DeepSeek Braid 父 | 1,546 | — | 2.930 | 0.835 | 90.623 | 0 |
| 同上 | GLM Braid 父 | 524 | — | 0.551 | 0.168 | 34.141 | 0 |
| 同上 | DeepSeek executor 子 | 77 | — | 0.179 | 0.067 | 7.011 | 0 |
| GitHub g02 64e0 | DeepSeek Braid 父 | 26 | — | 0.088 | 0.013 | 0.720 | 0 |
| GitHub g03 6b45 / g04 8159 | ZIP 未见原生消息 | — | — | — | — | — | — |
| GitHub g05 435b | GLM Braid 父 | 89 | — | 0.209 | 0.022 | 6.821 | 0 |
| **GitHub 官网继承总计** | 父 2 模型 + 子 1 模型 | **6,052** | — | **9.562** | **2.863** | **406.165** | **0** |
| Sheet 官网初始 20a1 | DeepSeek Braid 父 | 582 | — | 1.052 | 0.450 | 49.291 | 0 |
| 同上 | GLM Braid 父 | 1,029 | — | 1.207 | 0.327 | 56.180 | 0 |
| Sheet g01 5d3d / g02 65f8 | ZIP 未见原生消息 | — | — | — | — | — | — |
| Sheet g03 3445 | DeepSeek Braid 父 | 519 | — | 0.899 | 0.308 | 33.701 | 0 |
| 同上 | GLM Braid 父 | 1,564 | — | 1.345 | 0.375 | 87.966 | 0 |
| Sheet g04 bd7a | DeepSeek Braid 父 | 565 | — | 1.027 | 0.232 | 14.743 | 0 |
| 同上 | GLM Braid 父 | 1,480 | — | 1.671 | 0.308 | 34.170 | 0 |
| **Sheet 官网继承总计** | 父 2 模型；无成功原生子会话 | **5,739** | — | **7.202** | **2.000** | **276.050** | **0** |
| GitHub 本地 07 新增 | DeepSeek Braid 父 | 583 | 583 | 0.404 | 0.366 | 104.909 | 0 |
| 同上 | GLM Braid 父 | 605 | 606 | 0.659 | 0.197 | 53.520 | 0 |
| 同上 | DeepSeek vision 子 | 9 | 9 | 0.017 | 0.020 | 0.036 | 0 |
| **GitHub 本地 07 新增总计** | — | **1,197** | **1,198** | **1.080** | **0.584** | **158.465** | **0** |
| Sheet 本地 07 新增 | DeepSeek Braid 父 | 1,182 | 1,185 | 0.804 | 0.600 | 166.538 | 0 |
| 同上 | GLM Braid 父 | 553 | 553 | 0.814 | 0.194 | 37.549 | 0 |
| **Sheet 本地 07 新增总计** | — | **1,735** | **1,738** | **1.617** | **0.794** | **204.087** | **0** |

官网 GitHub 源档案共有 459 个有消息的物理原生会话（456 个 Braid 父会话、三个 executor 子会话），Braid 索引 465 条；Sheet 为 682 个有消息的父会话与 686 条索引。相应的 9/4 个索引会话无可计的消息，不一定是丢档：可能从未请求、也可能未被最终 ZIP 保存，不能据此补零。本地 07 GitHub 有消息的物理会话 12 个（10 个父、两个 vision 子）、Braid 索引 19 条；Sheet 为 20 个有消息的父会话与 40 条索引。07 时间窗内无消息的旧索引不算本次缺失。08 若继续恢复，必须用原生 message ID 去重，仅把 08 新窗口作为增量，不再加一遍 07 的累计历史。

## 先行可行动发现

1. **GitHub 官网重复派同一 rebase 工作有明确可避免的上限。**初始运行在 11:24 与 11:27 对同一 rebase 任务启动两个并行 executor；其父会话没有消费到可核实的完成结果，后续 g01 12:05 又派第三次且被 SIGKILL（调用、父消费与状态证据见 [hosted-github-usage.md](../../factory-subagents/cells/hosted-github-usage.md)）。第二个重叠 executor 本身已耗 `input=111,738`、`output=29,476`、`cacheRead=1,256,704`；若第一项已足够且父会话在重派前核对在途 UUID/产物，理论上可避免 **0 至这些值**。下限为 0，因为第一项并未证明能完成、避免第二项可能损失正确性。第三次另耗 `input=178,994`、`output=66,588`、`cacheRead=7,010,816`，但其是否可避免不能从现存不完整结果断言。优先机制是把“原生 run ID、状态、产物路径、父消费”作为重派前的交接事实，避免对同一写任务盲目并行；这比降低模型档位有直接因果证据。
2. **07 的大缓存读是上下文体量信号，并非同等成本的浪费。**GitHub 07 新增 `cacheRead=158.465m`、Sheet `204.087m`，分别远大于未缓存 input；其中 GitHub issue 6 占 `79.048m`，Sheet issue 5 / issue 7 占 `52.006m / 46.921m`。这些集中段适合定向查重复读取、长工具回显和反复验收，但仅凭大缓存不能估“可省百分比”，也不能断言模型有错误。每次缩短必要上下文有潜在质量风险，只有能对应重复的原始工具/报告内容才能给节省上限。
3. **恢复与重建必须按因果区分成本。**本地 07 GitHub 的 1,197 条与 Sheet 的 1,735 条都是授权热修后的新工作，不是恢复复制带来的“重复 token”；07 `cancelled` 是人工 hotstop，无评分，不能作为模型性能结论。官网 g03/g04 等失败链无源 transcript 的段也不可当零成本。后续若要估算重建净损耗，应只量化同一任务被再次执行的读写链，而不是把重建后的全部输入或缓存读都归咎于重建。
4. **工具回显有两个可收窄的具体入口。**07 原生记录中，GitHub 父会话落盘 1,129 条工具结果、共约 1.281m 字符；Sheet 1,820 条、约 2.303m 字符。Sheet #2 的 `ls -la /tmp` 加 `ps -eo pid,etimes,cmd` 一次回显 47,683 字符，#5 的 `ps -eo pid,ppid,etime,cmd --sort=start_time` 一次回显 31,123 字符；它们是为诊断共享浏览器/检查进程而查，命令行全量回显却比所需 PID、运行时长和进程名宽。收窄 `ps -o` 字段及结果行数，保留可核查的进程身份，可避免 **0–78,806 字符**的原始输出；上限是假设两条完整回显都可替换，实际必要部分大于零。逐条文本哈希还发现 Sheet #5 与 #7/#8 的四份跨成员相同文件输出，额外完整文本约 55,981 字符；GitHub #4/#5 与 #6/#7 之间三份跨成员相同输出约 20,439 字符。这是**跨成员各自取证**，并非同一会话反复读取，也不能直接删：不同职责可能都须看原文；只有共享产物能精确标明 Git head、行段、适用范围时才宜复用。字符数不能直接折算为模型 input 或 cacheRead；同一回显进入哪个请求、是否被截断和缓存命中尚无逐片段账本，故不捏造 token 节省。

07 GitHub 的 [共享契约交接链](../../braid-product-reaudit/cells/attempt07-collaboration-evidence.md)还显示 #3/#5/#6 曾并行局部修补 `sessions.js`，后由 PR #3 归并、#3/#6 两次重基才清掉重复 diff。这一段使“共享文件先确定 owner，再给其他成员发诊断/接口事实”有依据，但诊断、复验和后续重基并非全部多余，现存用量记录不能把这些调用精确切成可避免 token。Sheet 同文档还记录两次自己修改 Issue 正文引发的中途重建；它提示 self-origin 失效通知值得收敛，但没有证据把整个重建会话当作浪费。误把 Issue #7 的功能门槛当成 PR #7 已合并是验收语义问题，不能在尚未发生重测前计入节省。

## 已知缺口与保守解释

上述官网继承 ZIP 不提供完整请求起点；`assistant_messages` 不计入可能发出但未落盘的请求，尤其失败/中断尾段，故已观察的四类 token 是下限。官网消息的四项字段在每条已保存 assistant 消息中都有数值，但这不覆盖未落盘请求。07 `pi-timing` 有 GitHub 1 条 GLM、Sheet 3 条 DeepSeek request-start 多于落盘 assistant 消息；这些请求是否完成、计费多少不能凭开始记录推断。作一个**人为悲观压力情景**：假设四个未配对起点都完成且每项分别达到同模型 07 已观察的最大单消息用量，则 GitHub 额外 `input=16,308 / output=6,881 / cacheRead=155,584`，Sheet 额外 `input=58,686 / output=19,434 / cacheRead=935,424`。这三个字段的最大值可来自不同消息，此情景有意偏大；它并非真实账单的上界，因为失败链与未落盘请求的规模在档案中没有有限上界。所有段的 `cacheWrite=0` 是 Pi 记录字段值，可能意味着 provider 未报告该项，不可解释为提供方实际没有任何缓存写入或成本。

这份表只覆盖上述两份官网最终 source ZIP 与本地 07 截面。更早 7207/e45/7b 等官网运行若有独立原始档案未纳入；取消的 Flash Qwen/MiniMax 属其他模型/条件，只宜另作对照，不能与 DeepSeek 当前增量相加。当前 08 尚未收集进表。

复算时从仓库根目录执行 `python3 tasks/experiment-infrastructure/scripts/token_economics.py runs/e20260928-completed-replay/github/source-workspace.zip`；本地窗口则把同一脚本送至 WSL 的 `python3 - <Braid .factory26 路径> --since 2026-09-28T05:27:51Z --until <该题结束 UTC>`。脚本输出 JSON 的 `known` 列可核对四字段覆盖，`maximum_message_tokens` 仅供前述缺请求压力情景，不是计费上界。
