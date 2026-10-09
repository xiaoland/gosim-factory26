# 将赛事 sub-agent 经验沉淀到个人 Codex

用户于 2026-10-09 提出：比赛已经结束，executor、explorer、browser-operator/computer-operator 等 sub-agent 可以沉淀并应用到 `~/.codex`。

2026-10-09 用户在 Windows 对照建议后明确授权：“好，帮我补齐。”本轮修改范围为 Windows 原生 `C:\Users\yyh\.codex` 的 executor、explorer、browser_operator、computer_operator 四角色及全局 AGENTS 的 Sub-Agents 段；保留 Windows 环境说明、既有模型选择及授权/advisor 规则。不改 Harness、Mac 配置或 WSL 配置，不提交。项目调查、备份与记录位于 WorkSSD。

已核实 `~/.codex/agents/` 存在 executor、explorer、browser_operator、computer_operator、advisor 五个 TOML 文件；本次会话的工具角色目录也提供这五类角色。四个执行/调查角色已有完整结果责任、局部修复、授权边界与可采用证据的指引，不能把已有配置误报为本轮新增。

主 Agent 负责核对个人现状与提出沉淀范围；子 Agent `role_lessons` 负责仓库经验的定向只读调查。证据入口为 `tasks/factory-subagents/packet.md`、相关 cells、`variants/native-hackathon/agents/` 与个人角色文件。调查角色只返回结果，不创建独立任务包。

Mac 调查与建议已完成，Mac 个人配置未修改。`role_lessons` 对照仓库与个人角色后确认核心已具备；独立判断负责人 `transfer_judgment` 建议保留四角色，仅在个人 `AGENTS.md` 的委派段补充按任务选择上下文继承、由调用方提供目标与真实边界而由负责人取得执行细节的原则。主 Agent 采用这一最小范围建议。

建议正文：按任务选择上下文继承方式。需要独立判断、历史含有大量无关材料，或任务可由清晰目标和证据入口充分表达时，使用独立上下文；任务依赖已形成的需求、授权或在途工作时，保留相关上下文。调用方提供目标、必要事实、材料入口和真实边界，执行细节由负责人自行取得；接续优先沿用原负责人。

不迁移赛事模型配方、Braid 成员协议、固定角色流水线、强制 fresh/worktree 或固定浏览器工具 SOP。依据 `tasks/iteration13/executor-followup.md` 与 `tasks/factory-subagents/design.md`，这些选择应按实际任务与运行接口确定。个人 explorer 已有观察默认与有界实验要求；未发现具体误写事故，不据其 workspace-write 设置扩大本轮建议。

Mac 调查完成依据：已读取个人四角色正文与个人 AGENTS 委派段，角色目录在本次会话可用，并取得仓库定向调查与独立迁移判断。没有做四角色端到端效果或模型对比，不将配置存在等同于效率收益。Mac 修改不在本轮 Windows 授权内；没有提交或其它在途操作。

## Windows 对照（2026-10-09）

用户追问“看看 win-ws.localhost”。通过该 SSH 入口只读核实 Windows 原生用户目录 `C:\Users\yyh\.codex`，未将 WSL 配置当作 Windows 配置。当前进程未设置 CODEX_HOME；读取的是默认用户目录，未核实桌面进程是否有单独覆盖。

`agents/` 只有 advisor、executor、explorer 三份文件，没有 browser_operator 或 computer_operator。executor 仍要求父方预先提供 owned surfaces、candidate carrier、independent validator、retry budget 等项目，不完整时返回请求；这会让父方承担较多局部执行设计。explorer 的 description 为 `explore stuff`，正文只有一句限定信息问题，缺少调查收敛、来源与可采用证据的工作方法。

Windows 全局 AGENTS 的 Sub-Agents 段限定 bounded、low-coupling、isolated execution，并偏好 fork_turns=none 或少量近期历史；较 Mac 现有结果责任原则更窄。建议同步 Mac 的 executor/explorer 正文，保留 Windows 特有操作与授权要求；将上下文选择改为按任务决定。两个 operator 可增加对应角色定义，但工具实际可用性须独立核实，不能由角色文件推定。advisor 本轮只作为已有配置记录，不建议扩大改动。

Windows 对照阶段仅调查，没有修改文件或启动子 Agent 来验证远端装载与浏览器/桌面操作能力。已读角色文件、全局 AGENTS 和主配置中的模型/权限/角色相关行；未读取凭据文件。

## Windows 实施

主 Agent 负责本轮小范围配置编辑与回读核对。沿用 Mac 四角色正文，更新 Windows 的稳定负责人、可采用成果和按任务选择上下文指引；advisor 的既有调用条件及 Windows 特有说明保留。先将当前相关文件备份到 WorkSSD 的 `runs/codex-subagents-consolidation/`，写入前比较远端内容，写后回读并检查 TOML 解析与授权边界。角色配置的装载及 UI 工具实际能力只能依据实际运行证据报告，不由文件存在推定。

实施已完成。Windows 更新 `agents/executor.toml`、`agents/explorer.toml`，新增 `agents/browser_operator.toml`、`agents/computer_operator.toml`；全局 AGENTS 只替换 Sub-Agents 下 advisor 段之前的两段，保留独立证据核对原则与主方整合责任。executor/explorer 的原模型、推理强度和 sandbox 设置均未改变；新 operator 与 Mac 定义一致。advisor、主配置和 Windows 特有环境说明未改。

备份及修改证据为 [Windows 备份目录](../../runs/codex-subagents-consolidation/windows-20261009-133709/)：`before.json`、`before/` 保存原内容，`proposed/`、各 `.diff` 与 `updates.json` 保存拟写内容，`after.json` 保存远端回读。写入前逐文件核对现场未改变，写入后五份目标文件与预期逐字匹配；四份角色 TOML 通过标准库解析，advisor 回读与原内容一致。

本轮配置编辑与核对完成，没有未完成的写入或提交。未启动远端 Codex 会话或实际操作浏览器/桌面，未验证新角色装载、工具能力或热加载。需在新会话或重新加载后实际使用时确认，不把文件核对等同于端到端验收。
