# pi-minimal GitHub 本地运行观察

观察对象为 `pi-minimal--hackathon--github-59aaf58e7462bc`，`started_at=1790689981.3825152`（2026-09-29 13:53:01 UTC）。run 在第 20 分钟截点仍为 `running`；当前状态文件见归档 `run.json`。

计划中的 5/10/15/20 分钟事件检查已执行。每个时点的模型与工具计数由原生 `session.jsonl` 按 UTC 时间戳回切重建。四份源码快照没有成功落盘：本机 rsync 在传输前因不支持 `--info=stats2` 退出。随后仅用 SSH tar 保存了一份约第 27 分钟的当前快照，因此不能把它当作四个历史源码状态。

| 从启动计时 | GLM assistant 消息 | 累计工具调用 | 当时可见证据 |
|---|---:|---|---|
| 5 分钟 | 7 | bash 7 | 新 Pi session 已有连续模型返回。两次读取 GitHub PNG 发生在截点后约 1 秒。 |
| 10 分钟 | 12 | bash 10、read 2、write 2 | 两次 PNG `read` 的返回都含 `image`，确认有视觉输入。 |
| 15 分钟 | 19 | bash 12、read 2、write 6、edit 2 | 14:07:13 UTC 一次 Bash 执行失败，详情见下文；之后仍有模型调用及文件修改。 |
| 20 分钟 | 20 | bash 13、read 2、write 6、edit 2 | 截点前最后一次工作区工具结果为 14:08:35 UTC；到 20 分钟时已有约 4 分 26 秒没有新 session 消息。 |

原生 session 在 13:55:01 UTC 创建，工作目录为 `/workspace/template`；首次 assistant 返回于 13:55:25 UTC。session 中唯一的实际主模型标记是 `factory26/glm-5.3-flash`，且在四个截点均有 assistant 消息。`home/.pi/agent/agents/advisor.md` 将 advisor 配为 `factory26/kimi-k2.7-code`、`defaultContext: fresh`、`inheritProjectContext: false`；`models.json` 列出 GLM 和 Kimi。但主 session 没有 advisor/subagent 调用、Kimi model-change 或子 session 文件，所以只能确认配置，不能确认实际调用。主 session 的单一新 session 起点支持 fresh run 的判断；advisor 自身上下文因未启动而不可验证。

到 20 分钟为止，没有观察到直接读取 `SKILL.md` 的工具调用。出现过的工具只有 bash、read、write、edit。read 了两张 PNG，确有图像返回；agent 自身没有实际浏览器/Playwright 操作，较早的 `BROWSER_EXECUTABLE_PATH` 检查只是环境探测。没有 Context7 或 Exa 调用。PBB 在 20 分钟窗口内也未观察到；最终归档中有一条 14:15:02 UTC 的 `pbb status bg002` 命令，已超出观察窗口，且命令把 stderr 丢弃并经 `head` 管道，结果不能证明调用成功。

错误证据分属不同路径：

- `session.jsonl` 在 14:07:13 UTC 记录一次 Bash 错误：`better-sqlite3` 找不到 native bindings。后面仍有新的 GLM 消息及文件写入，未见重复同一错误形成的循环。
- `evidence/generation.stderr.log` 记录 `Meter baseline unavailable: meter request failed with HTTP 401`。这是启动基线 meter 错误；原生 session 同时持续收到 GLM 返回，因此现有证据不支持把它当成模型请求失败。
- `pi-minimal/otlp-errors.log` 有 RemoteDisconnected 与 ConnectionResetError，指向 telemetry 导出连接；`pi-minimal/stderr.log` 为空。未在原生 session 看到模型 API 错误。
- 14:08:35 至 14:14:34 UTC 约 359 秒没有新 session 消息，之后 agent 恢复文件写入。观察到长间隔，但没有证据将其定性为死循环或终止。

当前归档位于 `/Volumes/WorkSSD/Development/factory26/runs/pi-minimal/20260929/local-observations/pi-minimal--hackathon--github-59aaf58e7462bc/snapshot-final/`。其中 `workspace/official-generation/submission/` 保留生成代码，`workspace/observed-agent/agent/` 保留 agent 源与配置，`workspace/official-generation/template/.arc/pi-minimal/` 保留原生 session、事件和 home 配置；另有 `run.json` 与 `evidence/generation.{stdout,stderr}.log`。`session.jsonl`、`events.jsonl`、`identity.json` 和 advisor 配置可用于核对上面的观察。

为缩小归档并避免复制凭据，排除了 `node_modules`、`.playwright` 浏览器缓存、`.cache`、`Cache`、`auth.json` 与 `models-store.json`；归档副本 `home/.pi/agent/models.json` 中的 `apiKey` 字段已替换为 `[redacted]`。运行源文件没有改动。
