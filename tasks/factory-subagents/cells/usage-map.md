# 原生子代理使用视图：官网来源链与本地接续

本轮终态与 advisor 专项：见 [判断前移审计](advisor-left-shift-audit.md)。该页补齐六组保留历史、03 终态与调用/发现的区别；以下早期截面仍按原范围解释。
## 官网与本地覆盖总表

| 范围 | 实际子会话 | 启动前失败／无效等待 | 结果消费与限制 |
| --- | --- | --- | --- |
| 官网 GitHub 来源链，终态快照435b79927a47（前两次在初始run，第三次在g01） | 3个DeepSeek executor | 3次Unknown agent | 两次时间重叠的同任务委派；两次终态未知、一次SIGKILL；未证实父消费或并发写冲突 |
| 官网 Sheet 来源bd7ac1b232ba | 可见682/686父session中0个 | 38次无匹配wait，不是spawn失败 | 4份原生记录缺失；13次主会话直接读图，无可见vision委派 |
| 本地DeepSeek历史至07 | 3个vision完成 | 2次vision语义guard误拒 | 三份报告均被父消费，未证明分数净收益 |
| 本地Flash（已取消） | 1个executor启动未完成 | 2次Unknown agent | 与已有Braid工作重叠，未见完成回执 |

官网依据分别见 [GitHub调用账本](hosted-github-usage.md) 与 [Sheet调用账本](hosted-sheet-usage.md)。
官网评分回放595ab74c90a9、1efffb84ae1b没有重新生成，不追加计数。
更早独立官网运行及部分恢复窗口的独立快照尚未逐一核对，详见GitHub覆盖表；本页不声称覆盖所有历次官网运行。

最重要的新因果线索是官网根会话重建后重复派发仍在途的原生executor，说明只修角色名和vision guard还不足以验证整个委派闭环。
后续应核对Pi原生在途状态/结果在父会话重建后的发现与接续；不让Braid接管Pi子代理生命周期。

## 本地详细账本


截面：2026-09-28 05:45 UTC。DeepSeek 证据取 WSL `runs/e20260928-02-deepseek-direct/attempt-07/generation/runs/` 两题的 Braid SQLite、`work/native-homes` 原生 JSONL、`subagent-artifacts` 与此前 attempt-06 冻结证据；Flash 取已取消的 `runs/e20260928-01-flash-team/attempt-02/`，沿用已核实的[旧窗调查](../../experiment-infrastructure/cells/subagent-usage.md)。只读检查；截面之后的活动不计入。07 的 05:27:49 UTC 是控制器开始时间，约 05:32 起是本轮新 Pi 会话；旧活动随恢复资料进入 07，不把复制品当新调用。

## 层次与去重

`braid-state/braid.sqlite3` 的 `agent_instances.agent_id` 是协作成员身份；`provider_sessions` 是其物理 Pi 主会话。重启或恢复能给同一成员增加主会话，不能据此说新增了协作成员。子代理只由父 JSONL 中 `subagent` 的执行调用与独立 `subagent-artifacts/<run-id>_*` 证明；`action:list/status` 不是 spawn，顶层与 `sessions/` 下同一 session ID 的 JSONL 不能双计，`recovery-source-native` 和 06 复制记录也不能双计。`subagent_wait({id:"bg001"})` 是**Pi 子代理等待工具被模型误用于 PBB bash 作业**，不是 PBB 工具，也不代表子代理启动。

按这些材料去重后，**可证实的执行尝试为八次：三个完成的 `vision`、一个启动后取消前未完成的 `executor`、两个 `Unknown agent`、两个只读 `vision` 被 guard 启动前拒绝**。三个完成的视觉任务均有父会话消费证据；executor 无完成结果可消费。`action:list`、状态查询和 `subagent_wait` 不在八次里。这里统计的是观察到的调用，不拿调用量替代收益。Flash 的 Braid 成员总数未在本轮重新汇总，下表只写核实到的身份与任务，不把 Issue 编号上限当作全员数。

| 执行 ledger | 输入与上下文 | 实际运行成本/状态 | 消费 |
| --- | --- | --- | --- |
| DeepSeek Sheet 旧窗 #5 → `vision`, `9af6153d…` | 三张 spreadsheet 参考图；fresh 配方、视觉 DeepSeek | meta：60,829 ms；input 3,712、output 10,282、cacheRead 2,176、cacheWrite 0；exit 0 | 03:07:49 父 `read` 报告，方案已先发。 |
| DeepSeek GitHub 07 #5 → `vision`, `292edcd3…` | REQ-3 五张仓库资产图；fresh 配方、视觉 DeepSeek | 05:34:21 启动、05:35:14 通知；transcript 四条 assistant usage 合计 input 6,812、output 8,877、cacheRead 13,568、cacheWrite 0；exit 0 | 05:35:27 父明确引用报告并与需求文本核对。 |
| DeepSeek GitHub 07 #6 → `vision`, `3645ce84…` | REQ-4 八张代码/分支图；两次误拒后简化为视觉事实；fresh 配方、视觉 DeepSeek | 05:36:30 启动、05:37:46 通知；transcript 五条 assistant usage 合计 input 9,769、output 11,368、cacheRead 22,400、cacheWrite 0；exit 0 | 05:38:05 父总结截图与需求差异，在之后写 UI。 |
| Flash Sheet 根 → `executor`, `785baf8d…` | 共享基础整块开发，与 Braid 已派 Issue #2 重叠；fresh DeepSeek 配方 | 03:10:26 启动，03:31:01 状态仍 running，至少 20 分 35 秒；取消前无 final meta/可靠总 token | 无完成回执，不能算交付。 |
| Flash Sheet #3 → `qwen`、根 → `minimax` | 把 Braid 成员名填入 Pi 角色选择 | 两次 `Unknown agent`；无实际子会话、无子模型 token | 无结果。 |
| DeepSeek GitHub 07 #6 → `vision` ×2 | 长只读视觉任务包含英文 UI 文案示例 | 两次启动前 guard 拒绝；无子会话 token，父会话读角色文件并重写提示 | 无子报告，第三次才成功。 |

07 两份 meta 未记录 `durationMs` 或聚合 usage，上述约 52 秒/76 秒是父调用至通知的墙钟跨度，token 是子 transcript 各 assistant usage 相加；它们口径不同于 Sheet 的 meta 汇总，不能直接当同价成本。Flash executor 取消前没有可核实的聚合 token，不推算。父会话为重试/解释/整合所用 token 也未计入上述子成本。

| 题目/窗口 | Braid 成员与物理会话 | 原生子代理执行结果 | 父会话消费及效果 |
| --- | --- | --- | --- |
| DeepSeek GitHub 旧窗至 06 | #1–#5 五个 issue 成员，#1/#2 及 #3–#5 随 Braid 工作推进；多次主会话重建 | 06 新恢复窗未见成功 spawn；不能将 Braid 分工记成 Pi 委派 | #2 处理共享基础与合并，#3–#5 在主会话做需求、实现与检查；此前 06 报告限定此窗。 |
| DeepSeek GitHub 07 | SQLite 当前 #1–#7 七个 issue 成员。#1/#2/#3/#4/#5 的 `agent_id` 延续，07 又有 #6/#7；同一成员的重复 `provider_sessions` 是接续 | #5 REQ-3 `vision` 一次成功；#6 REQ-4 `vision` 两次启动拒绝、第三次成功。两次成功 run ID 分别 `292edcd3…`、`3645ce84…`，实际模型均 `factory26-visual/deepseek-v4-flash-vision-exp:high`，exit 0。其他四角色未见成功委派 | #5 在 05:35:14 收到 `subagent-notify`，05:35:27 明确分析报告、以需求文字压过截图差异，之后完成实现/E2E；#6 在 05:37:46 收到通知，05:38:05 总结截图差异，后续建 UI。证明回执进入判断，不单凭此证明质量增益。 |
| DeepSeek Sheet 历史与 06 | 当前 SQLite 有 #1–#7 issue 编号，其中 #2 GLM 退休后由 DeepSeek 另一个 `agent_id` 接管，另有 #4 PR 实施成员，共九个不同协作 `agent_id`；多个 provider session 是重建 | 历史 #5 03:06 一次 `vision` workflow 成功，run ID `9af6153d…`，同一视觉模型，exit 0；06 新窗未见新 spawn | 03:07:49 父会话 `read` 视觉报告并纳入中文截图/英文 accessible names 判断；初始方案评论在报告前，故初始方案收益未证。 |
| DeepSeek Sheet 07 | 上述成员接续，不能按新 `native-homes` 数当新人 | 截面内 `work/native-homes` 新 05:33+ 会话未见 `subagent` 执行；`subagent_wait` 调用几次均无可匹配原生 run，包含 `id:bg001` | Sheet 在主会话继续实现/检查。等待误用既未启动子代理，也未等到 PBB 作业。 |
| Flash GitHub 02（取消） | Braid 成员运行，旧报告核对范围内 | 未见 Pi 原生 spawn | 无法从未委派推出停滞原因；停止前无可归因的子代理结果。 |
| Flash Sheet 02（取消） | Braid #3 Qwen 与根 GLM、Braid `minimax-2` 等；Braid 名称与 Pi 角色目录分属不同命名空间 | #3 `agent:qwen` 与根 `agent:minimax` 各得到 `Unknown agent`，无子会话；根随后 `agent:executor` 一次实际启动（角色当时按配方使用 DeepSeek），取消前仍运行、未见完成回执 | 失败后 #3 主会话自己交 PR；executor 与已派给 Braid minimax 的 #2 共享基础重叠，且在根工作树写入。不能把未完成执行当交付，也不能把既定跨模型配方判为误调用。 |

这张表的“未见”仅对列明的 native-homes/observer/归档材料及截面成立；没有声称未来、丢失日志或所有外部渠道绝对零调用。07 两次 GitHub 视觉通知分别带完整报告，`subagent-artifacts` 有各自 input/output/transcript/meta；子 transcript 起始为独立 task，未把父对话正文直接复制为子任务。角色 frontmatter 声明 `defaultContext:fresh`、`inheritProjectContext:false`、`inheritSkills:false`；实际完整系统提示在 transcript 中被 `[prompt redacted]`，所以“fresh”有配置和独立会话支持，不能从该 transcript 单独证明父历史绝无隐式内容。两次 meta 确认视觉模型与 exit 0。

## 五角色实际状态与委派质量

| Pi 角色 | 配方/能力 | 已知实际委派与返回 | 判断 |
| --- | --- | --- | --- |
| `vision` | 视觉 DeepSeek；`read`；fresh；只读图 | DeepSeek Sheet #5 旧窗一成，GitHub 07 #5/#6 两成；GitHub #6 另有两次无子会话的启动拒绝。三个成功报告均由父消费 | 是清楚的职责切口。07 #6 第一/二次任务含 `Create new file` 等 UI 原文示例，被文本意图 guard 当“实施”，改成短句后通过；误报额外消耗父调查与重发。 |
| `executor` | DeepSeek；读写工具；fresh | Flash Sheet 根一次成功启动但取消前未结束；DeepSeek 这批未见 | Flash 输入给了问题、路径、工作树与范围，却和 Braid 已派 #2 重叠。下一次只在独立文件/验收切口且有单一所有者时用。 |
| `explorer` | DeepSeek；`bash`/搜索/读取；fresh；正文要求只读 | 四窗所查未见成功调用 | GitHub 07 #6 主会话自己读大段需求/现有 schema/router，若有一个会改变 API 设计的独立结构问题可委派；当主会话已靠几条读命令得到答案时，另开 agent 低 ROI。 |
| `advisor` | Kimi；`bash`/搜索/读取；fresh；独立判断 | 四窗所查未见成功调用 | Sheet 合并/权限共享 API 等有重要取舍时可给争议点、选项和反证；普通落地/编译修错由持有人更快闭环。不能以未调用计数认定缺陷。 |
| `browser-operator` | 视觉 DeepSeek；`bash`/agent-browser；fresh；操作页面旅程 | 四窗所查未见成功调用 | GitHub #5 主会话做 19 项可重复 E2E、#6 自己准备浏览器验收；独立旅程复现或跨页面观察可委派，但已成形的脚本不必重复跑。Sheet #4 自行用 Playwright 抓到 Shift+click 缺陷也是有效直接工作。 |

上述 advisor/explorer/browser-operator 的 `bash` 在 Pi capability 判定中属于可变更工具；“只读”是角色正文的工作约束，**不是硬性文件系统权限**。`vision` 的 `read` 才是硬工具边界。因此对四个非实施角色设置 `completionGuard:false` 是禁用不可靠的自然语言“必须编辑”推断，而非授予写入权；executor 应保留其实施交付 guard。其余实际权限仍由各角色工具与运行环境决定。

## 两条因果与最小动作

1. **接口与 guard。** `subagent({action:"list"})` 在 GitHub 07 两个父会话实际返回 `advisor/browser-operator/executor/explorer/vision` 五个 executable 名称、description、`context:fresh`，证明发现入口可用；Flash 的 `agent:qwen/minimax` 是模型把 Braid 协作身份误作 Pi 角色名。Pi 上游 0.56.0 的 `task-intent.ts` 却按任务全文英文动词推断修改意图，不理解被引用的 UI 文案；`completion-guard.ts::validateImplementationToolContract` 在启动前拒绝纯 `read` 的 vision。这是真实接口阻断，现有只读角色 `completionGuard:false` 能绕开启动及事后“无编辑”误判，executor 保留 guard。长期不宜继续堆 UI 关键词特例，应让明确只读角色/结构化任务契约决定是否需要编辑证据。
2. **后台概念。** PBB 扩展实际只注册 `bash`，其后台结果通过 `custom_message source=pi-background-bash`/`pbb status|tail` 消费；`subagent_wait` 是 pi-subagents 的工具，只匹配原生 async run ID。Sheet 07 `bg001` 立即返回 `No active run matched`，是模型选择失误由两种“后台等待”表述放大，不是重名覆盖。最小澄清靠近现有 Pi 子代理用法段即可；不要加新包装工具。

进一步委派应从可分离任务决定，而非固定 explorer→advisor→executor→browser 流水线。最明显的低 ROI 是 Flash 重复共享基础的 executor；GitHub #5 的 19 项 E2E 与 Sheet #4 的复现已由持有人完成，再委派同旅程只会重复工具与上下文成本。最有效的已见委派是把参考图事实交 vision，并由父会话在实现和验收判断中使用；其产品收益仍需以应用差异验证。
