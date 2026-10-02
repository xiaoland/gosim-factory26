# 浏览器反馈链路与环境成本核对

本页核对 2026-09-27 两个官网来源生成 run 的冻结材料和原生轨迹，回答 `agent-browser` 是否准备好、是否被采用，以及哪些环境耗时可由外部工具减少。GitHub 来源 run `435b79927a47`、Sheet 来源 run `bd7ac1b232ba`。时间均为 UTC。旧 run 的事实只说明旧冻结包；当前 Harness 接线单独核对。没有启动应用、模型或评测。

## 先区分两种浏览器工具

`agent-browser` 是交互探索 CLI；`browser-checks` 指导 Agent 使用预装的 Playwright Test 编写可重复的验收。两份旧 ZIP 都含 `work/skills/agent-browser/SKILL.md` 和 `browser-checks` 技能。前者 SHA-256 均为 `52feca41...b0af`，与当前 `harness/skills/agent-browser/SKILL.md` 一致；它要求执行 `agent-browser skills get core` 读取版本匹配的 CLI 手册。旧 `browser-checks` SHA-256 均为 `3371a834...f16a`，说明旧文档是同一冻结版本；当前文档已增加显式 cwd/env、PBB 完成回执、保存退出码与日志等提示，不能倒灌成旧 run 当时已有的指引。

两份官网 `official/agent.zip` 实际含 `runtime/bin/agent-browser`、`runtime/node_modules/agent-browser/package.json`、`skill-data/core/SKILL.md` 和 Linux x64 二进制；包内 `package.json` 均写明 **0.38.1**，与冻结依赖锁一致。wrapper 使用随包 Node 调用 `bin/agent-browser.js`，默认 `AGENT_BROWSER_EXECUTABLE_PATH` 指向随包 Chromium；官网 `official/inputs.json` 也列出这些文件的哈希。由此可排除“只放了导航文档、没有 CLI”这一解释，但未在原 Linux 环境执行 CLI，仍不能断言任一页面操作成功。旧原生 `browser-operator.md` 明列 `agent-browser`，原生模板也内嵌该 skill；根 Pi launcher 的 `--no-skills` 后仅显式加载 `browser-checks`，这不是丢失 `agent-browser`：浏览器角色通过自身 `skills:` 与内嵌材料取得它。当前 `pi-braid`、`pi-braid-flash-team` 的 `build.py` 都把两种技能装包；`run.py` 复制 `agent-browser`、给浏览器角色追加 skill、将 CLI 所在 `runtime/bin` 加入 PATH，并设 `AGENT_BROWSER_EXECUTABLE_PATH`、`AGENT_BROWSER_SOCKET_DIR`。两个 variant 这段接线相同。

有一处具体的 **skill 指引冲突**：Factory 薄 skill 写“单个浏览器任务使用默认 session”，但冻结 CLI 自带 `skill-data/core/SKILL.md` 的 “Always use your own session” 要求首条命令前用 `agent-browser session id --scope worktree --prefix task` 设置 `AGENT_BROWSER_SESSION`；其理由是未命名默认浏览器会被其他 Agent 共享。当前 Factory 薄 skill 保持旧文本。CLI core 是版本匹配的命令权威，这里应修改 Factory 导航为每个任务都用命名 session，再在同一旅程复用它。轨迹没有实际调用，因此这是待修的潜在并发误用，并非两题已发生的故障。

我对 GitHub ZIP 的 465 个、Sheet ZIP 的 682 个 `work/native-homes/**/*.jsonl` 会话逐条解析 assistant `toolCall.arguments`：分别有 6,668、5,601 个工具调用；`agent-browser` 字符串在两者调用参数中均为 **0**，`browser-operator` 委派参数也均为 **0**。可见 `browser-checks/SKILL.md` 的读取调用分别为 11、4 次，且两题轨迹和检查产物确实运行了 Playwright。这个搜索只证明保存的原生调用没有采用交互 CLI，不能推论 CLI 无法使用；相应也不存在可归责于 `agent-browser` 的原生失败输出或重试耗时。针对这两题的环境窗口，把“缺 skill”或“agent-browser CLI 缺陷”列为根因没有证据。

## 从命令到反馈的可证成本

时间细节与原始路径已在 [GitHub 环境成本](../../github-score-diagnosis/environment-cost.md) 和 [Sheet 环境成本](../../sheet-score-diagnosis/environment-cost.md) 定位。下表只摘取有直接时刻或计时依据的浏览器相关链路，不把重叠任务、模型消息间隔和 `sleep` 参数相加。

| 案例 | 命令执行及后台通知 | 结果消费、诊断、修正与复跑 | 归类 |
| --- | --- | --- | --- |
| GitHub 首批浏览器自检 | 13:01:57 启 runner，13:06:34 读报告，调用至消费约 4 分 37 秒；Playwright 自报 3.8 分钟。启动和结果产生的独立时刻缺失。 | runner 已处理隔离数据、health、种子登录、模块与 Chromium。多项用例失败后继续做 UI/断言诊断。整段不能算浏览器安装。 | 可重复检查已有且运行；失败在页面行为或判据层，具体分项须按需求审查。 |
| GitHub 手工复跑变量遗漏 | 13:24:18 发后台 build + `pr-basics`，13:26:34 首读 `Set BASE_URL and BROWSER_EXECUTABLE_PATH before running browser checks`；失败实际发生时刻未知。 | 13:27:00 补 `BASE_URL`，13:27:51 读 `6 passed (37.6s), 1 failed`；下一项为 `Changed files summary` 文案。2 分 16 秒是发现窗口，不是 Playwright 执行时长。 | 用错 CLI 前置环境；非 `agent-browser` 缺陷。配置报错已明确给出下一动作。 |
| Sheet 首批检查 | `bg001` 11:52:37.148–11:55:51.856，194.708 秒，含安装/构建/Playwright；Playwright 自报 2.6 分钟。PBB 11:56:10 首告知已退出。 | 11:56:36 才读 `2 passed, 19 failed`，完整结果已结束约 45 秒；11:57:16 读到三个同名旧工作簿。`\| tail -30` 导致运行中 PBB 日志为空，并使外层 `exitCode=0` 无法代表测试通过。 | 结果消费和退出码处理不当；旧 4313 端口的具体占用者未留证，不能把首批失败定为已证实端口碰撞。 |
| Sheet 4731 隔离复跑 | `bg006` 12:00:47.448–12:03:14.752，147.304 秒，含构建与 Playwright；保留内层 `EXIT=1`，外层因尾部命令为 0。 | 12:03:26 首读 `TypeError: fetch failed`（结束后约 12 秒），12:04:25 读最终 `1 passed, 20 failed`；检查脚本的 cleanup 已删除失败 `server.log`，无法判定进程失联死因。 | 应用服务生命周期/自检脚本诊断缺口；非已证实浏览器 CLI 或应用业务缺陷。 |
| Sheet 4733 手工隔离 | 12:05:37 已读到服务 health 和外置日志，12:07:33 才发浏览器命令，中间 1 分 56 秒无新的服务/浏览器命令，原因未知。`bg011` 12:07:33.948–12:09:21.164，107.216 秒；Playwright 自报 1.7 分钟、21/21 通过。 | 12:11:09 才首读结果，结束后约 108 秒；期间还查 health、发后台 `sleep`，不能叫纯空闲。21/21 只证明此轮用例与隔离服务可运行。 | 结果消费延迟与等待方法；反证浏览器安装/启动普遍不可用。 |
| Sheet 4742 故障注入与修补 | 保持外来服务后，原检查 `bg020` 运行 100.011 秒仍进入浏览器；另起 server 得到 `EADDRINUSE`。修补后的 `bg022` 运行 33.407 秒，在浏览器前报端口占用，首次读取晚约 41 秒。 | 先用 `kill -0` 的修补未挡住僵尸/旧 health；随后加入端口预检，再将预检移到构建前，12:19:32 即报 `Port 4742 is already in use...` 和 `EXIT=1`。 | 已证实自检脚本服务归属问题，以及修正有效；修补发生于生成应用的脚本，未来 Harness 不应预写该脚本。 |

Sheet 七个检查/故障注入 job 的 PBB 时长合计 735.383 秒（约 12 分 15 秒），但包含构建、浏览器用例、timeout 和并行诊断，不是净环境损失。GitHub 两次端口配置/路径误用可确认至少各 30 秒无效就绪轮询，互不重叠的下界 60 秒；cookie 探针、JSON 双重编码探针、`BASE_URL` 漏配的观察窗口都不能直接当作运行等待。可被明确标出的 Sheet 反馈滞后为约 45、108、41 秒，彼此不重叠但并非都可回收。具体时间与原生命令见上述两份记录。

## 归因和最小改进

旧材料已准备好 `agent-browser` 导航、实际 CLI 包和浏览器角色接线，但这两题在相关窗口选用的是 Playwright 可重复检查，没有发生 `agent-browser` 调用。这个选择与旧 `browser-checks` 对最终验收的定位相符，不能算 skill 未采用导致故障。Factory 薄 skill 的默认 session 说法与包内 core 手册冲突，是独立的指导错误，但没有进入本次调用链。真正可见的摩擦是服务和检查进程的边界：端口 `0`、漏 `BASE_URL`、临时脚本移到 `/tmp` 后相对路径变成 `/server.js`、错误 cookie/双重 JSON、Shell 管道吞退出码、PBB job 已结束却继续轮询、日志随隔离目录被删。前四项是命令/探针使用错误；Sheet 旧 health 命中外来服务是已复现的生成检查脚本缺陷；随后出现的 GitHub UI 不符是应用或判据问题。没有一次原生失败能证明 `agent-browser@0.38.1` 功能缺陷，也没有 CLI 调用时长可计。

优先保持 `agent-browser` 用于探索、Playwright 用于可重复验收；不换工具。先把 Factory 薄 skill 的默认 session 句子对齐包内 core 手册，这是无需新工具的小修。当前 `browser-checks` 已补足 PBB 完成、退出码和日志指引，下一步最小外部资产可放在 **Agent Skill 内**，而不写生成应用的 `package.json`、`src` 或 `scripts`：一个通用服务/检查启动辅助命令，接受调用方给出的 cwd、启动命令和必需环境，分配并保留本次独占端口与数据目录，记录服务 PID/端口归属、stdout/stderr、检查原始退出码和产物路径，检查启动前拒绝端口冲突与缺失 `BASE_URL`，服务中途退出时保留日志，结束时只清理本次进程。它不含 Sheet/GitHub API、账号或断言。先盘点现有 PBB 与 Skill 资产能否承担这些动作；可复用时只补接线/用法，不另写封装。需要验证该方案时，用不启动付费模型的两种本地情形区分：同端口外来服务应在浏览器前拒绝，服务中途退出应报告该 PID 和原始日志，而不是仅返回 `fetch failed`。本页只提出方案，不实施或运行该验证。

证据边界：旧 **source** ZIP 不含 runtime，官网 **agent** ZIP 含 Linux runtime；本页静态读取了其中 `package.json`、wrapper 和 core 手册，没有在原 Linux 环境执行 CLI。Sheet 首批端口归属、4731 服务退出原因和各观察窗口中的模型时间均未知。当前两个 variant 的静态接线不等于运行验收，后续如要证明 CLI 可用，应在获授权的隔离本地情形直接观察一次页面操作回执。
