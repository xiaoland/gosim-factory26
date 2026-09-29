# pi-minimal 的 better-sqlite3 安装问题

结论：首轮安装后缺少原生 binding，Agent 放行 better-sqlite3 安装脚本后已成功源码编译并加载数据库。不是截至停止时仍未解决的编译依赖缺失。另一项尚未闭合的问题是应用验证实际使用 Node 24，而正式环境是 Node 20.19.3；现有成功结果不能证明正式安装/启动兼容。

本次只读已停止运行的 WSL 工作区、原生日志与安装产物；未改应用或源码，未启动模型、服务、测试或探针。I11 不受影响。

## 证据入口与因果

以下相对路径均基于 WSL 主机 `wsl.win-ws.localhost` 的目录：

`/home/yyh/Development/factory26/runs/pi-minimal/20260929/local/own-key-generation/runs/pi-minimal--hackathon--github-59aaf58e7462bc/workspace/official-generation/template`

原生会话为 `.arc/pi-minimal/session.jsonl`；后台记录目录为 `.arc/pi-minimal/home/.pi/pbb/sessions/1d41c66fa7036bdf88fe9029/instances/pbb_100_3397f4dc/`。

| 问题 | 已有证据 | 判断 |
| --- | --- | --- |
| 使用哪个版本 | backend/package.json:12 为 `^11.10.0`；backend/pnpm-lock.yaml:11–13 锁到 `11.10.0` | 本次安装实际为 better-sqlite3 11.10.0 |
| 使用哪个 Node | session.jsonl:22–23 的 `node --version; pnpm --version` 返回 `v24.10.0`、`10.34.5`；.arc/preflight.json:4 则是 `v20.19.3` | 工具 PATH 的 Node 与平台 Node 不同 |
| 初始故障是什么 | session.jsonl:42–43，重跑 install 后 import db.js 报 `Could not locate the bindings file`，搜索包含 `compiled/24.10.0/linux/x64` 与 `node-v137-linux-x64` | 是找不到 binding，不是日志已证明的 ABI mismatch 加载错误 |
| pnpm 脚本是否影响结果 | session.jsonl:28 创建的 package.json 无构建许可；:44–45 添加 `pnpm.onlyBuiltDependencies: ["better-sqlite3"]`；:46 再安装；安装日志随后出现 gyp 成功 | 放行前无 binding、放行后确实运行安装脚本且成功，是脚本策略导致首轮缺产物的强因果证据；首轮警告正文未保留，不能给出逐字警告确认 |
| 编译依赖是否缺失 | 后台 `logs/bg002.log:1–4`：`gyp info ok`、`install: Done`、`Done in 1m 39.3s using pnpm v10.34.5`、`db ok`；`jobs/bg002.json:10,11,22` 为 exitCode 0，14:08:05Z 开始、14:09:45Z 完成 | 该 Node 24 容器已有足够工具链完成源码构建；不能把慢编译归因于缺 Python/make/g++ |
| 编译目标 ABI | `backend/node_modules/.pnpm/better-sqlite3@11.10.0/node_modules/better-sqlite3/build/config.gypi:441` 为 `node_module_version: 137`，:481 为 x64 | 成功构建针对 Node 24 ABI 137，不是正式 Node 20 的验证 |
| 后续是否使用成功 | session.jsonl:53–54 读到 build/Release/better_sqlite3.node 等产物；:55–56 为 `seeded: true`；:63–64 API 返回真实仓库、提交和 PR 数据 | 原生 binding 故障已经越过，不能继续报告“SQLite 仍无法运行” |

Agent 在 :44 中考虑过 JSON/sql.js 替代，但实际选择配置 `onlyBuiltDependencies` 并保留 better-sqlite3；当前 package.json:15–16 保留该设置。没有实际换库。随后第一次启动遇到 `cookieParser` 的独立调用错误（:59–60），修正后 API 已返回（:63–64），不能把该错误归入 SQLite。

安装包的 package.json:33 明确脚本为 `prebuild-install || node-gyp rebuild --release`。第二轮 gyp 日志证明最后走了源码编译，但原始下载/回退理由被 Agent 的 `2>&1 | tail -3` 丢弃；不能据此认定是无 Node 24 预编译包、网络失败或下载被拒绝。首轮 `logs/bg001.log` 也只剩提示框尾部和完成行。管道还没有 pipefail，job exit 0 本身不能证明 install 成功；本次真正成功证据是 gyp 和 `db ok`，不是单独 exitCode。

## 最小修复方案与职责

**本次应用已有的局部修复保留。** 对确实需要 native install 的 better-sqlite3 显式允许脚本即可，不需要因首次缺 binding 重写持久化层，也不建议全局放行所有依赖脚本。尚未证实正式 Node 20 安装失败，因此不先升级、降级或换库。

**预打包环境应清楚区分工具 Node 与应用 Node。** portless 等工具需要自己的 Node 24；应用交付以 Node 20.19.3 为准。保留工具运行时，提供/说明现有 `/usr/local/bin/node` 和 `/usr/local/bin/npm` 的正式应用入口；应用安装、构建和启动应在该 Node 下完成。不要把 Node 24 编译出的 `.node` 文件视为可直接给 Node 20 使用的缓存，也不应为这一个错误预装某版本 better-sqlite3 到全局并让生成应用依赖它。现有证据不支持再添加编译工具链作为本次根因修复。

**提示词只需给必要工具知识。** 简明说明 pnpm 10 的依赖构建许可、按需配置 onlyBuiltDependencies，以及 native 包的安装与运行必须用一致的目标 Node。安装失败保留完整第一轮日志；可将完整日志写入文件再读取末尾，避免直接 tail 丢失因果。无需增加强制 advisor、MCP 或完整新验收流程来解决这一安装问题。

**应用承担可复现依赖与正式路径验证。** 依赖许可与 lockfile 属于应用；正式交付路径按平台逐目录 npm install/build/start。当前日志只证明 Node 24 下编译和 API 使用成功，没有 Node 20 下该路径的完成证据。是否能下载预编译包、是否需在 Node 20 重编译及正式安装耗时，留待后续获授权运行观察；本次不追加探针。
