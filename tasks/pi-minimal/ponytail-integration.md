# Ponytail 原生 Pi 扩展接入核对

状态：已完成上游追踪和最小 vendor 复制（2026-09-29）。共享 `harness/skills/ponytail` 保持不变。主线已在 main.py/build.py/agents/advisor.md 完成实际接线；未运行模型验收。

## 上游来源与复制范围

上游目录：`/Users/lanzhijiang/.codex/plugins/cache/ponytail/ponytail/4.10.0`。

- npm 包：`@dietrichgebert/ponytail` `4.10.0`
- 来源：`https://github.com/DietrichGebert/ponytail.git`
- 固定 commit：`e3ba2aa6f1e6f0bc4d69eb09c9f0d0a93af56156`（`chore: release v4.10.0 (#870)`）
- 目标 vendor：`variants/pi-minimal/vendor/ponytail/`
- 来源清单：`variants/pi-minimal/vendor/ponytail/UPSTREAM.json`

已复制的最小运行文件：

```text
LICENSE
pi-extension/index.js
pi-extension/package.json       # type=module，保证 index.js 按 ESM 加载
hooks/ponytail-config.js        # CommonJS，由 index.js 的 createRequire 加载
hooks/ponytail-instructions.js  # 读取同一 vendor 下的官方 skill
skills/ponytail/SKILL.md
```

没有复制上游 tests、`pi-extension/test`、benchmarks、MCP、其他客户端 hooks、开发脚本或发布文件。复制文件的 SHA-256 与上游逐个相同；三个 JS 文件已通过 `node --check`。

## 实际 Pi 接入方式

主 Pi 的 CLI 扩展路径应指向：

```text
<staged-pi-root>/vendor/ponytail/pi-extension/index.js
```

如果 build 阶段把 variant vendor 放在 stage 根，当前源码路径对应：

```text
variants/pi-minimal/vendor/ponytail/pi-extension/index.js
```

官方 Ponytail skill 的路径应指向：

```text
<staged-pi-root>/vendor/ponytail/skills/ponytail/SKILL.md
```

Pi 原生参数分别是 `--extension <path>` 和 `--skill <path>`，可与已有 `pi-subagents`、`pi-background-bash` 扩展并列传入。vendor 内的 `pi-extension/package.json` 是必要的 ESM 边界；不需要额外 npm package。

## 默认模式与事件行为

官方配置解析顺序是：

1. `PONYTAIL_DEFAULT_MODE`，只接受 `off|lite|full|ultra`；
2. `$XDG_CONFIG_HOME/ponytail/config.json`（无该变量时 `~/.config/ponytail/config.json`）中的 `defaultMode`；
3. 内置默认 `full`。

因此正式配方可显式保留 `PONYTAIL_DEFAULT_MODE=full`，即使不设置也会得到 `full`。`review` 是 session-only，不能成为默认值。另有可选的 `PONYTAIL_QUIET_STARTUP` 与 `PONYTAIL_HIDE_STATUS`，分别控制启动提示和状态栏显示；它们不改变规则是否注入。

`index.js` 的可观察行为：

- `session_start` 从历史 `ponytail-mode` custom entry 恢复模式，否则读取默认；默认会发 `Ponytail loaded: full` 通知，除非设置 quiet。
- `before_agent_start` 在模式不是 `off` 时把官方 `SKILL.md` 内容按当前强度筛选后追加到 system prompt；读取失败才使用内置 fallback。
- `input` 只把整条消息严格等于 `stop ponytail` 或 `normal mode` 的情况切换为 `off`，并保存 custom entry；普通文本包含这些词不会误停用。
- `agent_start`/`agent_end` 只更新状态栏 active 指示。
- `/ponytail` 支持模式、`status`、`default <mode>`；review/audit/gain/debt/help 命令只是发送相应 skill 消息。

该扩展没有余额、Meter、官网提交、凭据或自建认证逻辑；它不能覆盖 `main.py` 的 `OPENAI_API_KEY`/`OPENAI_BASE_URL` 检查，也不能绕过比赛余额保护。它只影响 Pi 提示词、session custom entry、配置文件和 UI 状态。

## Advisor 边界

advisor 仍由现有 `pi-subagents` 根据 `variants/pi-minimal/agents/advisor.md` 的 frontmatter 加载：`model: factory26/kimi-k2.7-code`、`defaultContext: fresh`、`inheritProjectContext: false`，并通过 `skillPath` 查找技能。原生 Ponytail扩展的 `before_agent_start` 只作用于加载该扩展的 Pi 进程；它不会因为 advisor 被创建就自动注入子会话。

因此若希望 advisor 也消费官方全文，应让接线后的 advisor `skillPath` 包含或指向：

```text
<staged-pi-root>/vendor/ponytail/skills
```

这会让 advisor 通过已有 `skills: ... ponytail` 声明读取同一份官方 `SKILL.md`。若只给主 Pi 加 `--extension`，只能确认主会话有官方事件行为，不能声称 advisor 也加载了该扩展；本任务没有新增子会话扩展参数。

## 验证与下一步

已完成：上游 import 追踪、版本/commit 核对、目标文件复制、复制哈希比对和静态 JS 语法检查。未执行 Pi runtime，因为当前任务明确不重建 runtime、不运行模型或测试。

主线接线时需要把 vendor 目录随 stage 带入，并将主 Pi 的 `--extension`/`--skill` 改为上述路径；同时决定是否让 advisor 的 `skillPath` 使用 vendor skill 目录。其余余额 watcher、认证检查和模型配置保持现有实现。

## 已应用的主线接线

main.py显式设置PONYTAIL_DEFAULT_MODE=full，并加载vendor扩展；build.py复制vendor和官方skill到skills/ponytail，advisor的现有skillPath无需再指向另一目录。advisor显式加载同一Ponytail扩展及capability-evidence扩展；不会依赖父进程自动注入。替换@PACKAGE@为冻结包绝对路径。最终provider请求侧的记录用于下次真实运行核对full系统指令是否进入主/子会话。
