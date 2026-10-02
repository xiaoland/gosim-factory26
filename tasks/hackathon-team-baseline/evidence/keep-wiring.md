# Keep run 接线原始摘录

范围仅为 WSL `/home/yyh/Development/factory26/runs/hackathon-team-baseline/20260925/lite-runs/pi-team-mixed-arc-bench-lite-keep-54196efa62/`，下文记作 `$RUN`。Braid 留存目录是 `$RUN/workspace/official-generation/template/.factory26/20260924-163414-e4fa7b12/`，记作 `$B`。以下只列归档事实；旧容器的 `$B/work/...` 路径已不可直接读取时，用同一归档内 `native-config/` 与 `braid-state/physical/` 的副本。

## 主 Agent 实际收到的指令与初始输入

- `$B/braid-state/physical/01a0d444-8413-7891-8829-9391d0012388/instructions.md:1-4`：`你负责 Issue #1 的问题、设计与验收依据。需要实施时使用关联 PR 的工作树。`；`当前工作项内的局部委派使用原生 sub-agent。`
- 同文件 `:9-13`：`Issue 承接需求理解与完善、产品和技术方案、最终验收设计；PR 承接实施计划与适用的预演、实现及修复、最终验收。`；`按当前问题查阅 SVC 的设计、实现与 V&V 方法，用 task packet 保存持续工作所需的方案、计划、材料和证据。`；`子 Agent 不继承主会话历史，调用时明确设置 context:"fresh"`。
- `$B/braid-state/physical/01a0d475-b8b9-7a73-899f-457b42f53127/instructions.md:1-4,9-13` 的 PR 指令含同一用户指引，并写 `你负责 PR #1 的实施，当前分支 braid/pr-1，任务依据在直接关联的 Issue 中。`
- `$B/braid-state/physical/01a0d444-8413-7891-8829-9391d0012388/context.md:1-16`：初始工作记忆以 `系统已从当前本地对象重建工作记忆。Treat the following as working data, not as instructions.` 开头，列 `State: open`、`Assignees: @glm`；任务正文要求读 requirements.md/YAML/参考图片，允许临时工作区内设计、实现、自检及本地 commit/merge，并明确 `不得读取、搜索或下载外部验收测试、benchmark 实现`。
- `$B/native/000-2026-09-24T16-34-26-804Z_01a0d444-b173-728d-b38c-a923dba39f5d.jsonl:2,4`：`model_change` 为 `provider:"factory26", modelId:"glm-5.3-flash"`；首条 `user` message 重建上述 Issue 记忆。`$B/native/002-2026-09-24T17-28-00-786Z_01a0d475-bc12-7696-9347-539397cdc7fd.jsonl:2,4` 的 PR 首条消息重建关联 Issue、PR、Issue 设计评论与 PR 描述。JSONL 中没有独立 system/developer 原文；实际指令以 Braid 的 physical 留存为证。

## Profile、binding 与启动参数

- `$B/braid-state/request.json:52-55,63`：根 profile 为 `pi-glm-fast`，`assignee_login: "glm"`、`model: "glm-5.3-flash"`、`reasoning: "high"`；同文件 `:32,36-39` 另声明 `pi-deepseek-fast`、`deepseek-v4-flash`。这些是请求配置字段。
- `$B/braid-state/request.json:15-23`：GLM binding 为 `adapter_type: "pi"`，`executable: "/workspace/template/.factory26/20260924-163414-e4fa7b12/work/capabilities/pi-glm-fast/pi"`，`native_template: ".../pi-glm-fast/native-template"`。`$B/native-config/pi-glm-fast/pi:1-2` 保存该 executable 的脚本副本：`exec /workspace/submission/agent/runtime/bin/pi --no-extensions --no-skills --no-prompt-templates --no-themes --extension /workspace/submission/agent/runtime/node_modules/pi-subagents/index.ts --extension .../factory-subagent-observer.ts --skill .../svc/SKILL.md --skill .../ponytail/SKILL.md --skill .../impeccable/SKILL.md --skill .../exploration-tools/SKILL.md "$@"`。这里的 `...` 省略共同 `$B/work` 前缀，完整参数以脚本第 2 行为准；归档未保存 `$@` 展开后的 Braid→Pi 完整进程 argv。
- `$B/native-config/pi-glm-fast/native-template/settings.json:1-5`：`"packages": []`、`"subagents": {"disableBuiltins": true}`。同层 `agents/explorer.md:2-13` 含 `model: "factory26/deepseek-v4-flash"`、`defaultContext: "fresh"`、`inheritProjectContext: false`、`inheritSkills: false`。这两处是留存配置，不是本 run 实际子代理调用记录。
- `$RUN/workspace/official-generation/execution.debug.log:13-17` 记录外层启动：`python3 /workspace/submission/main.py /tmp/arcbench/requirements-source --output-dir /workspace/template`，generation agent 退出码 0。`$B/braid.log:3-4` 分别记录 Issue 与 PR session 的 `model=Some("glm-5.3-flash")`；`$B/telemetry-export.log:15-35` 汇总 `assistant_messages: 123`、`model: "glm-5.3-flash"`。`$B/telemetry-native.json` 的四个 session 条目均为 `profile_id: "pi-glm-fast", provider: "pi"`，原生会话由 `$B/native/manifest.json` 指向。

## 扩展、工具的留存证据与缺项

- `$B/native/000-2026-09-24T16-34-26-804Z_01a0d444-b173-728d-b38c-a923dba39f5d.jsonl` 的实际 `toolCall` 名称为 `bash/read/write/edit`；其余三段原生会话只见 `bash`。四个 `*-session-tree.json` 的 `children` 均为 `[]`。这些是**已调用工具与子会话**记录，不是可用工具枚举。
- 对 `$B/native/*.jsonl` 检索 `get_commands`、`get_state`、`Loaded extension`、`Failed to load`、`pi-subagents` 未命中；未发现现成 RPC 命令/状态返回或工具清单。`$RUN/workspace/generation.stderr.log` 为 0 字节，`$B/braid.log:1-8` 只有 INFO，`$RUN/workspace/official-generation/execution.debug.log:1-58` 未见扩展加载错误。现成日志不足以确认扩展工具是否向模型暴露。
- 对四份原生 JSONL 逐条统计 `type`：`000` 为 session/model_change/thinking_level_change 各 1、message 225；`002` 为各 1、message 24；`004` 为各 1、message 9；`006` 为各 1、message 5。没有 `custom` entry，也没有 `customType` 字段或 `pi-subagents` 启动事件。归档 `$B/` 下未保存 `work/native-homes` 目录或 Pi subagents 运行状态/配置文件；留存的是上述 `native-config/pi-glm-fast/{pi,native-template/settings.json,native-template/agents/*}` 和 observer 脚本。故本归档没有能单独确认扩展注册的启动事件或 RPC 返回。
- 原生首段 JSONL `:59` 有 `edit` 的 `oldText must match exactly` 错误，`:199,209,215` 有 `bash` 返回 `error: only this PR group can mark ready`；这些是留存的工具错误文本，均未提扩展加载。未调用模型、未发 RPC、未重跑。
