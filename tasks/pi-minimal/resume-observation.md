# pi-minimal 恢复后 10 分钟观察

观察状态：已完成一次有界只读观察（2026-09-29）。本轮只检查 GitHub 单题、自有 BigModel/Moonshot key 的本地恢复 run；未连接官网、未启动第二题、未修改应用或输入。

## 身份与取证边界

- WSL 根目录：`/home/yyh/Development/factory26/runs/pi-minimal/20260929/native-fix/own-key-generation`
- 当前 run：`pi-minimal--hackathon--github-2c26574a6a09be`
- 接续包 SHA-256：`3998ee50feaefc55fb1e6e539027f4a5be77aeed2da98385a69b798e2c7e2aac`
- `run.json`：`venue=official-local-generation`、`phase=running`、`started_at=1790694449.3588634`
- 恢复来源：`source_run_id=pi-minimal--hackathon--github-59aaf58e7462bc`，`mode=local-pi-session-resume`
- 本轮第一次新的 provider-facing capability 观察：`2026-09-29T15:08:57.466Z`，模型 `glm-5.3-flash`。
- 归档开始：`2026-09-29T15:18:22Z`（距首个请求约9分25秒，早于严格10分钟节点约35秒）；取证使用 SSH `tar` 流到本地，没有使用 rsync，也没有读取 `.private`、`auth.json`、`models.json` 或任何凭据。
- 本地证据目录：`runs/pi-minimal/20260929/native-fix/observations/pi-minimal--hackathon--github-2c26574a6a09be/10m/`
- tar 读取仍在增长的 `events.jsonl` 时报告 `file changed as we read it`；因此该文件是有界时点副本而非原子快照。`session.jsonl`、capability JSON、身份和恢复元数据已独立保存；动态继续写入的部分以缺证处理。

## 已确认的真实能力

本轮唯一 provider-facing 能力文件为 `capabilities/e53e8e7b41541fdcbeb30aa6b0c7cc69c710e9ffc02e1548e7d6c0961c5841eb.json`，49,289 bytes，`model=glm-5.3-flash`：

- system prompt 1 条、约 13,045 字符；其中实际出现 `PONYTAIL MODE ACTIVE — level: full`、完整 Ponytail ladder/rules 以及七个技能的 available-skills 入口。由此确认官方 Ponytail full 已进入主 provider 请求，而不是只凭配置推断。
- tools 7 个：`read`、`bash`、`edit`、`write`、`subagent`、`subagent_wait`、`subagent_supervisor`。subagent 工具确实暴露，且接线的 `toolDescriptionMode=compact` 位于恢复会话的 `home/.pi/agent/extensions/subagent/config.json`。
- 该 capability 记录的 `instructions` 字段为空；本轮判断依据是 `system` 与 `tools` 的实际记录，不把空字段误报为缺少系统指令。

恢复后的 session 增量（从 `15:08:57.466Z` 起的本地副本）包含 35 条 GLM assistant 消息、28 次 bash、8 次 edit、2 次 write；没有 `subagent` tool call，也没有 Kimi model-change、advisor 子会话或子会话 provider 能力文件。因此 advisor 本轮未触发，不能把配置存在写成真实调用。

没有发现 `mcporter`、Context7 或 Exa 调用。Ponytail 官方文件没有被模型用 `read` 工具直接读取；它已通过扩展注入 system prompt，另有 Better Auth 与 organization 技能由模型用 bash `head` 实际读取。故“Ponytail full 已注入”与“Ponytail 文件被模型读取”分开记录。

## PBB、Node 20 与应用反馈

PBB 有真实 job 记录。恢复后的新实例中：

- `bg001` 后端 `app-env pnpm install`：exit 0，日志显示 `better-sqlite3 11.10.0`、`express 4.22.3` 安装完成。
- `bg002` 前端 `app-env pnpm install`：exit 0；命令使用了 `tail` 和 `echo EXIT=$?`，这个 shell 形式本身不是严格的 pipeline 退出判据，因此只把它作为安装动作记录。
- `15:14:11Z` 的直接检查用 `app-env node` 加载 `better-sqlite3`、创建内存表，结果为 `sqlite ok under v20.19.3`。这确认 Node20/app-env/native 绑定在真实应用目录中可加载。
- 前端第一次 build 暴露 `lucide-react` 没有导出 `IssueOpened`；随后模型修正图标引用，`15:15:13Z` build 输出 `dist` 和 `✓ built in 3.28s`。这属于应用修复反馈，不是 runtime/native 故障。
- 后端第一次 `app-env npm run start`（`15:15:38Z`）退出 1。PBB 日志的真实错误是 `/workspace/template/backend/src/api.js:994` 再次声明 `function reactionsFor(subjectType, subjectId)`，Node20 报 `SyntaxError: Identifier 'reactionsFor' has already been declared`。
- 随后的第二次启动在 `15:16:53Z` 成功输出 `gh-lite listening on http://0.0.0.0:4100`；该后台 job 于 `15:20:12Z` 以 SIGTERM abort，属于 Agent 后续清理/重启动作，不能把“监听成功后被终止”归为启动失败。

早期恢复现场仍有一条 `generation.stderr.log` 的 Meter baseline `HTTP 401`，但本轮 Pi 已产生 provider-facing capability、持续 assistant 消息和实际工具结果；这条记录不能解释为本轮 provider 启动失败。Pi 自身 `stderr.log` 在 10 分钟取证时为 0 bytes。

## 未触发与限制

- advisor/Kimi：未触发；本轮所有 provider-facing 主会话模型记录均为 GLM。
- subagent：工具已暴露，但没有真实调用；不能声称 advisor 结果或 compact 工具在子会话中已消费。
- Context7/Exa：未调用；没有外部文档需求触发证据。
- browser/Playwright：本 10 分钟证据中没有实际浏览器工具调用；前端 build 与后端监听不等于浏览器验收。
- 评分、测试、官网提交、余额查询和第二题：均未执行。
- 动态 events 在 tar 时仍增长，且远端当前工作区未做暂停；更晚的会话内容不属于本次 10 分钟快照，后续若需观察必须建立新的时点和增量边界。

结论分类：`needs_review`。恢复、Ponytail full、主工具面、PBB 和 Node20 SQLite 均有真实证据；advisor/Context7/Exa/浏览器仍是未触发，后端重复声明是应用代码错误，不能归因于 Pi runtime。原始 session 与应用代码保留在 WSL run，未被本次取证修改。

## 后续与停机
主线于15:30Z复查新原生记录：15:27起已读取agent-browser技能并操作页面，浏览器发现GitBranch未导入导致仓库页空白；修正重建后页面展示恢复并继续检查Issue页。advisor/Context7/Exa仍未观察到调用。用户随后批准停止本地、正式参赛；本地run已cancelled，现场保留。正式运行身份见packet.md。
