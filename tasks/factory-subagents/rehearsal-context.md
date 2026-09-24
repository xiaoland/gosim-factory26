# Factory subagents 原生接线预演：上下文与角色材料

状态：实施前调查（2026-09-24）。本文只记录已核对的原生字段、消费者和证据路径；不表示运行源码已经修改，也不表示系统提示已经生效。当前工作树以 agent-browser 原生接线（HEAD `0b49247`）为准；不恢复已删除的浏览器 wrapper。

## 结论先行

Pi 的目标语义可以由现有原生字段表达，但必须同时改角色 Markdown、隔离 home 下的 `settings.json` 和父调用参数。角色 frontmatter 只能描述默认行为，不能替父调用选择 context。Codex 0.155.0 也可以表达无父历史，但应以实际工具协议为准：V1 明确发送 `fork_context:false`，V2 明确发送 `fork_turns:"none"`；两者不能凭角色 TOML 字段互相替代。

当前 `harness/skills/svc` 通过 `../../sources/svc` 指向完整 SVC skill，`references/methods/*/index.md` 在当前工作树存在；不能把旧归档中的不完整副本当作当前材料缺口。只写 `skills: svc` 可以选择完整技能，但批准方案仍要求把角色所选章节正文直接装入角色 prompt。

## Pi 0.85.1 / pi-subagents 0.56.0

### 原生字段与消费者

每个自定义角色的 Markdown frontmatter 应至少包含：

```yaml
systemPromptMode: append
inheritProjectContext: false
inheritSkills: false
defaultContext: fresh
skills: svc                 # 只在需要 SVC 的角色中出现
skillPath: /绝对路径/work/skills
extensions: ""
```

`systemPromptMode: append` 保留 Pi 的基础系统/工具提示，再追加角色正文；默认值为 `replace`，省略它会丢掉这层语义。`inheritProjectContext:false` 只关闭 AGENTS/CLAUDE 等项目指令的继承，不能当作父会话历史开关。`inheritSkills:false` 关闭自动技能目录继承，`skills` 仍可选择列出的技能；`skillPath` 是候选目录，最终选择由 `skills` 决定。`defaultContext:fresh` 是角色的默认值，父工具调用应再次明确传 `context:"fresh"`，以覆盖调用层歧义。

`extensions:""` 表示子角色不再自动加载常规扩展；运行时需要的 `pi-subagents` 本身仍由启动器显式加载。`subagents.disableBuiltins:true` 不是 frontmatter 字段，而是 `$PI_CODING_AGENT_DIR/settings.json`（本任务的隔离 native home 下）中的 Pi 设置：

```json
{"packages":[],"subagents":{"disableBuiltins":true}}
```

它关闭内建角色发现；同名自定义角色覆盖本名并不会自动移除其它内建角色。现有 Braid profile 的 `native-template/settings.json` 已有该设置，可作为可消费的形状；Hackathon `write_roles` 目前没有生成它。

### 选定 skills 与 SVC 章节

选定技能应随 native template 一起物化到隔离工作目录，最终 `skillPath` 使用该目录的绝对路径；不要把 `@SKILLS@` 留在最终配置，也不要依赖运行者的 `~/.pi` 或仓库相对路径。当前 Braid 接线在 `variants/pi-team-glm/run.py` 中以 `native_files()` 复制模板并替换 `@SKILLS@`，`sources/braid/src/provider/factory.rs:materialize_native_home` 再复制到每个会话 home；这是可复用的消费者链。

SVC 角色按 `roles.md` 的选择只加载对应章节：Explorer → `references/methods/explore/index.md`，Executor → `references/methods/implementation/index.md`（需要时按章节导航 V&V），Advisor/Specialist → `references/methods/design/index.md`。批准的接线是装配器从当前完整 SVC skill 读取所选章节正文，并直接嵌入该角色 prompt；不采用 `defaultReads` 这种只添加读取提示的较弱路径，也不要求直接注入后出现 child `read` 事件。Base 角色应不带 SVC 章节正文和 `svc` skill。

Hackathon 的 `scripts/package_hackathon.py` 和 Braid 的通用 `scripts/package_agent.py` 都应以当前完整 `ROOT/skills/svc` / `harness/skills/svc` 为源；当前后者已通过 symlink 指向 `sources/svc`。实施时保留所选章节的源路径与生成 prompt 记录即可，不应引用旧归档声称当前 skill 缺材料。

### 当前 Pi 接线缺口与覆盖风险

`submission/hackathon_main.py:write_roles` 当前只写 `inheritProjectContext:false`、可选 `skillPath/skills` 和正文，未写 `systemPromptMode`、`inheritSkills`、`defaultContext` 或 `extensions`，也未写 `settings.json` 的 `disableBuiltins`。父启动参数包含 `--no-context-files`，这不能替代子角色的 `defaultContext`；父提示中“可以调用角色”也不能替代工具调用的 `context:"fresh"`。

Hackathon 的角色名为 `explorer`、`executor`、`browser_operator`、`advisor`；Braid 模板中常见的是 `browser-operator` 等名字。实现与采证必须使用同一配置文件名和工具参数，不能把这两个命名当作隐式别名。浏览器材料应只指向原生 `agent-browser` skill，并在 child session 证据中检查其原生调用。

## Codex 0.155.0

### 配置和调用

Codex 角色 TOML 负责 model、reasoning 和 `developer_instructions`；历史继承是 spawn 工具参数，不是可添加到角色 TOML 的字段。当前[官方自定义角色文档](https://developers.openai.com/codex/multi-agent)规定原生从隔离 `CODEX_HOME/agents/*.toml` 自动发现角色，因此不应把旧版 schema/spike 中的 `config_file` 当作 0.155.0 的强制接线。正式运行前保存生成的角色 TOML；实际 native 是否被选中，仍以原生运行记录中的角色身份、模型和 instructions 为准。

固定源码摘录 `runs/factory-subagents-research/codex-v0.155.0-spawn.rs` 显示 V1 的 `SpawnAgentArgs.fork_context: bool`：`false` 走角色覆盖和初始委派，`true` 才建立 full-history fork 且不能同时使用角色覆盖。虽然 Rust 默认值为 false，实施和证据仍应显式发送 `"fork_context":false`。若锁定运行时实际暴露 V2 工具，则发送 `"fork_turns":"none"`；省略 V2 字段的默认值是 `all`，不能省略。

`developer_instructions` 可以追加角色方法，但不能证明无父历史。Braid app-server 启动根线程时的 `developerInstructions` 也只是启动提示材料，子线程是否带历史仍由 spawn 参数决定。

### 最小原生证据路径

四个配置 Codex 使用 exec 原生路径。实施前保存隔离 `CODEX_HOME` 下的角色 TOML 和可得原生调用记录；若检查 app-server，则沿 Braid 自有记录路径核对，不为本任务另加双向遥测工程。然后在根、子线程的原生记录中核对：

1. 根事件的原生 spawn tool item 是否带目标角色以及 V1 `fork_context:false` 或 V2 `fork_turns:"none"`；
2. 子 `thread/started` 的 `source.subAgent.thread_spawn.parent_thread_id`、`depth`、`agent_role`、子 thread id；
3. 子首次 turn/items 是否从自己的初始委派开始，且没有父线程既有 turn/items；
4. 子 shell 使用 `CODEX_THREAD_ID` 作为唯一会话标识。`CODEX_SESSION_ID` 是共享 root session，不能单独证明父子隔离。

若当前固定 runtime 实际只公开 V1，就不要同时发送 V2 字段；反之亦然。必须从真实 tool schema 和原始调用帧确定协议版本。

## Pi 的最小证据路径

生成配置随制品保存，调用和会话证据在获准的真实运行中取得：

1. native template/home 中的 role Markdown、`settings.json`、绝对 `skillPath`、SVC selected chapter 源文件及其生成 prompt；
2. 父 Pi JSONL 中的原始 subagent 调用参数和返回值（含 `context:"fresh"`），而不只保存 observer 的摘要；
3. child session 的 session 起始关系、首条 user/task、实际 role 和配置；SVC 正文直接注入 prompt，不要求出现目标章节的 `read`；
4. 若能取得启动器/扩展的有效系统提示，再核对 `systemPromptMode:append`。session archive 缺少 system prompt 只能记为“未观察到”，不能倒推 append 已生效。

已有 `runs/integration/20260921-233730-pi-native-f53672/native/session-tree.json` 只提供 parent/child/session/artifact/role 关联；现有 observer 也只保存 mode、run、parentSession、childSession 等摘要，不保存 context 模式、有效 system prompt 或技能列表。因此它可用于定位原始 child session，不能单独证明 fresh 或 append；SVC 正文注入是否进入最终 prompt 仍待生成配置和正式运行记录核对。

## 线性实施顺序（本轮不执行）

1. 冻结 Pi/Codex native template 的来源和绝对路径；先把 Base 与 SVC 的技能、章节材料分开，并在生成物中检查无残留占位符。
2. 补 Pi role frontmatter、`settings.json` 的 `disableBuiltins`、父调用显式 `context:"fresh"`；SVC 角色只把选定章节正文直接装入 prompt。
3. 依据锁定工具 schema 在 Codex 调用帧中选择 V1 `fork_context:false` 或 V2 `fork_turns:"none"`；保留自动发现 `CODEX_HOME/agents/*.toml`。
4. 归档上述生成配置和可得原生事件；没有原始参数或只有缺失 system prompt 的结果仍记为未知，待正式运行核对。

## 真实未知与阻塞

- Pi observer/session-tree 没有 `context` 和有效系统提示字段；需要保留原始 parent tool call 与 child session，不能从摘要补推。
- Codex 0.155.0 的 V1/V2 实际入口必须由固定 runtime 的 tool schema 确认，不能把两个参数一起发送。
- 当前角色 TOML 自动发现来自官方自定义角色文档；本轮尚未正式运行，因此角色是否被实际选中仍需以 native 运行记录确认，不把旧 schema/spike 当作阻塞。
- 缺少官方本地测试和本轮模型运行不是上下文配置已生效的证据；本预演不启动模型、不分析分数、不写或运行基础设施测试。

证据入口：`tasks/factory-subagents/{packet,technical,roles,verification,findings}.md`、`submission/hackathon_main.py:26`、`variants/pi-team-glm/run.py:192`、`sources/braid/src/provider/factory.rs`、`runs/factory-subagents-research/codex-v0.155.0-spawn.rs`；Codex 角色发现以官方多 agent 文档为准。
