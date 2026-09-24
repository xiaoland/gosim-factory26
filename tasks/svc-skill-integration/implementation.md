# 实施与证据

SVC skill 的短入口位于 `harness/skills/svc/SKILL.md`。
profile 解析将 `sources/svc/corpus` 的 Markdown 作为该 skill 的相邻材料冻结，排除维护者 AGENTS；不预载正文。
主 profile、explorer、executor 和 specialist 选择该技能，browser-operator、vision 不选择。
Pi 通过显式 `--skill` 和子代理的 `skills`、`skillPath` 装载；Codex 使用 native home 的 skills 目录及角色选择。

`pi-team-vv` 使用独立 VV profile，模型、assignee、原生角色及技能与 mixed 相同，仅多一条验收设计和完成判定时读取相关方法的指引。
旧的 `svc.index/preload` 配置已删除，variant 仅保留 SVC 来源 revision。

本地生成、原生模板和官方入口均不再复制 SVC AGENTS。
Docker 不再构建 SVC wheel、安装 `svc_cli` 或生成 `svc` 启动器；本地 bootstrap 只构建 Braid，SVC 只记录和归档源码。
受控 `check_braid` 不装配 skill，已删除其旧 `--svc` 开关。
开发 analysis 保持使用 `.venv/bin/svc`。
独立 `sources/svc` checkout 的 CLI 源码仍保留，但不进入参赛构建、ZIP 或工具目录。

## 验收记录

- `runs/svc-skill-integration/make-test.log`：141 项 Python 测试及 Pi observer 通过。
- `runs/svc-skill-integration/sources/`：无 SVC 安装和构建记录时仍成功归档实际源码。
- `runs/svc-skill-integration/variant-selection.json`：四个 variant 的模型、角色入口和技能选择。
- `runs/svc-skill-integration/pi/`：真实生成的 Pi launcher 能加载模型，RPC 状态检查通过；GLM 和 DeepSeek 的模型调用均因额度不足结束，事件中的 `stopReason:error` 优先于进程退出码 0。
- `runs/svc-skill-integration/codex-20260923-195228/`：Codex 父技能筛选可见；文本模型首请求收到 429，未启动子代理。

Pi/Codex 动态读取结果不能宣称通过。
额度恢复后只需接续有界技能探针，不必重做已通过的静态和无模型检查。

打包首次误用未缓存的本地 Docker context；改为有缓存的 `arcbox-win` 后，系统临时盘在复制 runtime 时不足。
最终构建采用 `TMPDIR=$PWD/runs/svc-skill-integration/tmp`，将大临时产物放到 WorkSSD；不改变产品代码，不清理其它任务的数据。

新候选包为 `runs/packages/svc-skill-integration/pi-team-vv-skill.zip`，SHA256 `11f0c53e22a0f96de384d1cfb73d3211a508bf77ec863982d13e480af9b274e8`。
共 15985 个文件的 manifest 哈希核对通过，包内 effective profile 与当前源码解析结果一致，未发现 `svc_cli` 或 `runtime/bin/svc`。
构建成功的进程退出码为 0；`package-arcbox.log` 因前一次失败清理与重试重叠而混有临时盘不足的旧 traceback，应以 `package-check.json` 和独立 ZIP smoke 结果判断制品。

独立 Linux x86_64 / CPython 3.12 ZIP smoke 完整通过，退出码 0，日志位于 `runs/svc-skill-integration/zip-smoke-20260923-195747/`。
验收覆盖无 SVC 可执行/可导入包、获选技能冻结材料、真实工具启动、入口、冻结交付、平台文件保留、标准部署、重复交付拒绝和失败退出，模型调用为零。
原 ZIP 哈希未变，验收容器已清理。
剩余唯一接线验收缺口为受额度阻断的当前配置真实模型技能读取（包括 Codex 子代理）；评分实验未执行。
