# Pi / pi-subagents 技能接线预演

2026-09-25。本文只核对活动 `pi-team-mixed` 的本地接线和已固定运行时源码；没有运行模型、Factory 测试或修改 Harness。

## 版本身份与观察范围

| 材料 | 版本证据 | 本地观察 |
| --- | --- | --- |
| Pi | `harness/npm/package.json:4`；lock `:161-166`，`@earendil-works/pi-coding-agent@0.85.1`，registry tarball integrity 为 `sha512-FGRN+OHb...` | `/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed/node_modules/@earendil-works/pi-coding-agent` 存在；同一 `package.json` SHA-256 为 `f1738e4b42203e5f22bcb513f13fb2fb224f1e98d1f129ff042f87048665a94c`。 |
| pi-subagents | `harness/npm/package.json:8`；lock `:3139-3148`，`pi-subagents@0.56.0`，registry tarball integrity 为 `sha512-XBmKqvrj...` | `/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed/node_modules/pi-subagents` 存在；`package.json` SHA-256 为 `e35c5acf7f2c75fcfd182b1eaa67f8485abc5ea81ac63598ef8ad637d3e788be`，`index.ts` SHA-256 为 `a2f11dbe8e200bd8c590441316a9c6ab222318d2aa738670dedcf0e72592dde3`。 |
| staged runtime / WSL | 现有 staged runtime 的两个 `package.json` SHA-256 与上述相同；WSL `/home/yyh/.cache/factory26/runtime-faf60473273ddeed` 也有这两个版本 | 这是文件存在和身份观察，不是一次模型运行的行为观察。 |

源码结论以下均来自上述固定 runtime 的源码；本次没有把“模型实际选择了哪个技能”误报为运行事实。

## 主 Pi：显式 `--skill` 只进元数据

**源码结论：显式技能不会把 SKILL.md 正文放进系统提示词。** Pi 的 `resource-loader.js:330-334` 在 `--no-skills` 时仍合并 CLI 显式路径，并调用 `updateSkillsFromPaths`。`skills.js:208-265` 的 `loadSkillFromFile` 读取并解析 frontmatter，保存 `name`、`description`、`filePath` 等字段；它没有把正文放入 prompt 字符串。`skills.js:275-297` 的 `formatSkillsForPrompt` 只输出“用 read/bash 加载文件”的提示和每项的 name/description/location。

**主提示词顺序（源码）：** `agent-session.js:752-767` 取得 loader 的技能和上下文后调用 `buildSystemPrompt`；`system-prompt.js:15-34`（custom prompt）及 `:99-116`（默认 prompt）都按“基础/追加 system prompt → project context → skills 元数据 → 当前目录”组装。Pi 文档 `docs/skills.md:24-34,42,65-72` 也明确说显式路径可重复指定，描述常驻上下文，正文按匹配任务由模型用 read/bash 渐进读取。

因此活动 launcher 的 `run.py:62-66` 中 `--no-skills` 加显式 `--skill` 的效果是：禁止自动发现，但保留四项显式技能的**可发现元数据**。它不会预读正文。

## pi-subagents 角色 frontmatter 的实际作用

角色文件先由 `frontmatter.ts:65-79,152` 分离 YAML 和 Markdown body。`agents.ts:1781-1809` 解析 `skills/skillPath`、`systemPromptMode`、`inheritProjectContext`、`inheritSkills`、`defaultContext`；最终 `agents.ts:1891-1922` 将 body 放进 `systemPrompt`，把这些字段作为独立配置保存。

### `skills` 与 `skillPath`

`execution.ts:1745-1753` 用调用参数的 skills（若无则用 agent frontmatter 的 skills）解析技能。`skills.ts:622-660` 先在 `skillPath` 指定的目录搜集，再按 cwd/全局技能路径查找；`resolveSkillsWithFallback` 在 `:663-678` 处理 runtime cwd fallback。`skillPath` 相对路径以 agent 文件目录为基准（`skills.ts:631-636`）。

解析时确实会从磁盘读完整文件并去掉 frontmatter（`skills.ts:586-620`），但这只是运行时解析和缓存；`buildSkillInjection` 在 `skills.ts:681-699` 只输出 name/description/location，并明确要求模型用 read 加载文件。`execution.ts:1765-1769` 把这段元数据接在角色 Markdown body 后。因此 `skills` 是“可发现、可按需深读”，不是正文 eager 注入。

### `systemPromptMode`

`execution.ts:1765-1774` 先形成“角色 body + 角色 skill 元数据 + 其它运行时注入”。`pi-args.ts:680-697` 把它写入临时 prompt 文件：`append` 使用 `--append-system-prompt`，`replace` 才使用 `--system-prompt`。现有四个角色均为 `systemPromptMode: "append"`（例如 explorer `:7`、executor `:7`）。所以角色 SOP 会附加在 Pi 原生系统提示词上。

### `inheritProjectContext` 与 `inheritSkills`

`pi-args.ts:673-678` 对 false 分别传 `--no-context-files`、`--no-skills`；`pi-args.ts:817-820` 同时写入 `PI_SUBAGENT_INHERIT_PROJECT_CONTEXT` 和 `PI_SUBAGENT_INHERIT_SKILLS`。子进程 runtime 的 `subagent-prompt-runtime.ts:682-703` 读取这两个环境变量，在 `:178-194` 中删除父提示词里识别到的 `# Project Context` 或标准 “The following skills provide specialized instructions...” 区段，并加入子代理边界。

这里的 `inheritSkills: false` 只阻止父 Pi 的发现/继承区段；它不取消 `execution.ts` 根据当前角色 `skills` 生成的角色自有元数据。当前角色的 `buildSkillInjection` 文案是 “The following configured skills are available to this subagent.”（`skills.ts:684-699`），与 runtime 用于剥离父 Pi 区段的标准 header（`subagent-prompt-runtime.ts:71-73`）不同。

### `defaultContext`

`defaultContext: "fresh"` 是角色在调用方省略 context 时的默认偏好，不是 prompt 加载开关。`extension/schemas.ts:319-322` 规定显式 `fresh`/`fork` 优先；省略时先用全局 `defaultSubagentContext`，再用 agent 的 defaultContext。`fork-context.ts:76-80` 和 `subagent-executor.ts:2455-2499,5626-5637` 证明 `fresh` 会在没有显式 fork 时作为 fallback。现有角色的 `defaultContext: "fresh"`（explorer `:10`、executor `:10`）因此保留 fresh 语义。

## 当前 `run.py` 是否造成正文重复

**源码结论：`skills` 声明本身不会与角色正文重复。** `run.py:47-57` 把角色 Markdown 读入后，显式把下列文件的全文追加到角色 prompt：explorer/executor/specialist 的 SVC method `index.md` 与 `exploration-tools/SKILL.md`，以及 executor/browser-operator 的 `agent-browser/SKILL.md`。同一循环的 frontmatter 只保留 `skills` 名称和 `skillPath`（角色模板例见 explorer `:11-12`、executor `:11-12`）。按 pi-subagents 的 `buildSkillInjection` 实现，后者只添加元数据，所以当前不会再添加这些 SKILL.md 的第二份正文。

当前实际 token 正文来自 `run.py:50-56` 的显式全文追加；`agent-browser`/`exploration-tools` 的 frontmatter 同时提供的是元数据入口。这是“正文一次 + 元数据一次”，不是“正文两次”。真正需要避免的是多次正文追加、角色 SOP 复制同一方法，或模型再次 read 后重复阅读；注册元数据并预装一次正文本身仍只有一份正文。

这项判断是源码推导；本次没有启动 Pi 去测量 token 或让模型报告看到的 prompt。

## 子代理是否复用 `run.py` launcher

**源码结论：不会直接复用 `run.py` 写出的 shell launcher，也不会自动继承其中的 `--skill` 参数。** `execution.ts:542-549` 对每个角色调用 `getPiSpawnCommand(args)` 后直接 `spawn`，子进程的参数就是 `buildPiArgs` 产生的 `args`。`pi-spawn.ts:139-162` 的选择顺序是：环境变量 `PI_SUBAGENT_PI_BINARY`；若当前 Node 本身就是名为 `pi` 的 standalone executable；否则从当前 Pi package root 找 CLI script 并用 Node 启动；最后才 fallback 到 PATH 的 `pi`。它没有调用父进程的 `run.py` shell 文件，也没有把父 argv 中的 `--skill` 复制到 child args。

因此活动主会话经 `run.py:61-68` 启动时，主 Pi 的 `--skill svc/...` 只属于主进程。角色 child 通过 `pi-args.ts:337-383` 生成自己的 `--no-skills`、`--append-system-prompt`、required extensions 和 task 参数；角色可见技能来自 `execution.ts:1745-1769` 的 `skills`/`skillPath` 解析和元数据注入。`buildPiArgs` 只把 Pi package root 通过环境变量传给 child（`pi-args.ts:715-719`），这用于找到同版本 Pi，不是继承 launcher 参数。

本地观察与此一致：run.py 产生的 launcher 是 run 目录下的 shell 文件，runtime 仍有独立 Pi CLI；但本次未运行子代理。若以后显式设置 `PI_SUBAGENT_PI_BINARY`，应把它视为改变 executable 选择的实验变量，并单独记录其版本和参数。

## 五个 SVC 技能的最小接线方案

目标是同时保留 fresh、角色 SOP 和按需深读，避免 generic `svc` 与五个入口长期并行。

1. 在 `build.py`/`run.py` 的现有 skill 复制与 launcher 列表中加入五个自足目录：`svc-task-packet`、`svc-investigation`、`svc-design`、`svc-implementation`、`svc-verification`。主 Pi 用五个显式 `--skill` 替代 generic `svc`，保留其它当前已启用材料；这只增加五项短元数据，完整正文仍由 read 按需取。
2. 角色 frontmatter 改为按职责暴露入口：explorer 以 `svc-investigation` 为主，specialist 以 `svc-design` 为主，executor 以 `svc-implementation` 和必要的 `svc-verification` 为主；task-packet 只在需要保留任务包/恢复点的委派入口声明。browser-operator 继续只声明 `agent-browser`，不为技能数量强行加入 SVC。保留现有 `systemPromptMode: append`、`inheritProjectContext: false`、`inheritSkills: false`、`defaultContext: fresh`、`skillPath`。
3. 角色 Markdown 中保留当前短 SOP 和职责边界。第一轮保留现有一次性 SOP 来源；三类方法正文移入对应新 skill 的 `references/workflow.md`，root `SKILL.md` 保持短而有用的入口，角色通过显式 metadata 按需深读更多内容。不要复制同一方法正文到角色 SOP 与 skill reference。`exploration-tools` 与 `agent-browser` 的现有全文追加属于既有工具 SOP，不因 SVC 拆分自动复制到五项技能。
4. 具体文件、角色映射和接线以 [`implementation.md`](implementation.md) 为准。这里的接口结论只约束“metadata 可发现、正文按需 read、单一正文来源”的边界，不另行设计接线。

这一路径只改变材料选择，不引入注册中心、preset 或通用路由器；它与 `svc-routing.md:39-47` 的“主会话短元数据、子角色保留 fresh 和 SOP、按需深读”一致。任何“技能被实际采用”的结论仍需未来授权实验独立记录。

## 证据边界

- 已观察：lock、macOS runtime、staged runtime 和 WSL runtime 的版本与文件身份；当前 `run.py` 与四个角色模板的具体接线。
- 源码证明：显式 Pi skill 的 prompt 形态、pi-subagents 角色字段语义、角色 skill 元数据生成、fresh/fork 解析以及继承区段处理。
- 未观察：本次没有模型输出、实际 token 计数、模型是否调用 read、官网行为或 Factory 得分；这些不能由本预演替代。
