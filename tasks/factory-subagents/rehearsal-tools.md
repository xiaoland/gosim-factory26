# Factory subagent 工具准备预演

日期：2026-09-24。范围限定为 WSL 工具取得和真实 MCP 文档查询；没有运行模型或 benchmark，没有修改运行源码、共享 runtime、冻结 ZIP，也没有新增测试、模拟或断言。

## 环境与版本

通过 `ssh -o BatchMode=yes wsl.win-ws.localhost` 核实：

| 项目 | 结果 |
| --- | --- |
| WSL 仓库 | `/home/yyh/Development/factory26` 存在 |
| 系统 Node/npm | `/usr/bin/node` `v22.22.3`；`/usr/bin/npm` `10.9.8` |
| 运行资源 Node | `/home/yyh/Development/factory26-official-local/hackathon-runtime-pi/bin/node` `v24.10.0` |
| 运行资源依赖 | 同目录 `node_modules` 存在；同目录没有 npm 可执行文件 |
| ripgrep | `/usr/bin/rg`，`ripgrep 14.1.1` |
| 预存 ast-grep | `/home/yyh/.local/bin/ast-grep`，`0.44.1` |
| 预存 mcporter | 未发现 |

`rg` 已可用，但这是 WSL 宿主命令，不能证明最终 runtime 镜像可用。

## 独占 scratch 安装

scratch：`/home/yyh/Development/factory26/runs/factory-subagents-preparation/tool-install`。使用现有 npm 安装，没有 sudo、Docker 全量构建或修改共享 runtime：

```text
npm install --prefix /home/yyh/Development/factory26/runs/factory-subagents-preparation/tool-install \
  --no-audit --no-fund @ast-grep/cli@0.45.3 mcporter@0.14.0
```

结果：退出码 0，`@ast-grep/cli@0.45.3` 与 `mcporter@0.14.0` 均安装完成。安装由系统 Node 22/npm 执行，mcporter 给出 `EBADENGINE` 警告（要求 Node `>=24`）；随后用指定 Node 24 运行 CLI，版本和命令均正常。因此还没有证明 Docker Node 24 阶段的 `npm ci` 与锁文件可移植。

`ast-grep` 的 `.bin` 入口是原生 ELF，直接交给 `node` 会报 `SyntaxError`；按 shell CLI 直接执行才是正确入口：

```text
/.../tool-install/node_modules/.bin/ast-grep --version  # ast-grep 0.45.3
/.../tool-install/node_modules/.bin/mcporter --version  # 0.14.0
```

## 实际工具使用

### rg

实际使用 `/usr/bin/rg --version` 并定位仓库中的 Docker/build 接线。来源和版本已在上表记录。

### ast-grep

使用完整命令名，避免 `sg` 同名冲突：

```text
ast-grep run -p "import subprocess" --lang python \
  /home/yyh/Development/factory26/submission/build.py
```

查询成功，命中 `submission/build.py:5:import subprocess`。随后从该版本 CLI 帮助确认了 `run --pattern/--lang` 参数。Context7 也用同一任务问题返回了官方 CLI `--pattern`、`--lang` 与 `--rewrite` 示例。

### mcporter 配置与发现

scratch 中使用的显式配置等价于：

```json
{
  "imports": [],
  "mcpServers": {
    "context7": {"url": "https://mcp.context7.com/mcp"},
    "exa": {"url": "https://mcp.exa.ai/mcp"}
  }
}
```

以 `MCPORTER_CONFIG=/home/yyh/Development/factory26/runs/factory-subagents-preparation/tool-install/mcporter.json` 运行，并在每次调用带 `--no-oauth`：

```text
mcporter list context7 --schema --json --no-oauth  # rc 0
mcporter list exa --schema --json --no-oauth       # rc 0
```

两端均返回 `status: ok`。实际 schema 与任务包已有记录一致：Context7 为 `resolve-library-id`、`query-docs`；Exa 为 `web_search_exa`、`web_fetch_exa`。

## 真实 MCP 查询

Context7 不是只做 `tools/list`：

1. `context7.resolve-library-id`，输入 `libraryName: ast-grep` 和官方 CLI 文档问题，成功返回 `/ast-grep/ast-grep.github.io` 等候选。
2. `context7.query-docs`，使用 `/ast-grep/ast-grep.github.io` 查询 CLI pattern/language 用法，成功返回官方来源及 `ast-grep run --pattern ... --lang ...`、rewrite 示例。

Exa 也完成了真实搜索和取页：

1. `exa.web_search_exa` 查询官方 MCPorter 配置、`MCPORTER_CONFIG` 与 `--no-oauth`，成功命中 `github.com/openclaw/mcporter` 的 `docs/config.md`、`docs/cli-reference.md`。
2. `exa.web_fetch_exa` 读取这两个官方页面，确认显式 `MCPORTER_CONFIG` 独占配置文件、`imports: []` 可用，以及 `--no-oauth` 的无交互语义。

原始输出和错误日志均保留在 scratch：`context7-tools.json`、`exa-tools.json`、`context7-resolve.json`、`context7-query.json`、`exa-search.json`、`exa-fetch.json` 及对应 `.err` 文件；没有凭据写入配置或日志。

## 观察到的错误与限制

- 第一次生成 scratch 配置时结尾误写了字面量 `\\n`，mcporter 报 `Failed to parse JSON ... InvalidSymbol`；重写为合法 JSON 后两个服务均正常。这说明配置文件必须由实际 JSON 生成/校验，不应照抄带转义的 shell 示例。
- 预存 ast-grep 是 0.44.1，不能替代锁定的 0.45.3；最终接线应只使用明确的 `ast-grep` 入口。
- WSL 宿主的 Node 22/npm 只完成了 scratch 安装；Node 24 只完成了已安装包的运行。未做 Docker build，不能宣称最终 Linux 制品可移植。
- 当前 `submission/Dockerfile` 的 runtime apt 包只有 `procps sudo`，`submission/build.py` 只复制 `ps`/`kill` 及其依赖；因此最终镜像当前没有 `rg`，也没有两个 npm 包。
- 公共 MCP 查询成功只证明本次网络、服务发现和请求可用，不证明后续无凭据调用始终不受限流、网络或服务变更影响。

## 最小线性实施路线

1. 在 `harness/npm/package.json` 与锁文件加入两个锁定 npm 依赖，让现有 Docker Node 24 阶段的 `npm ci` 产出它们；在 `submission/build.py` 给 `mcporter` 复用现有 Node wrapper，`ast-grep` 直接 exec 原生 ELF，不进入 Node wrapper 循环。
2. 在 Docker runtime 阶段取得 `ripgrep`，并把 `rg` 加入 `build.py` 现有的可执行文件/动态库复制集合，最终入口保持完整命令名 `rg`。
3. 随制品提供唯一的无凭据 MCP 配置（`imports: []`，两条 HTTPS URL），角色调用前设置 `MCPORTER_CONFIG`，固定带 `--no-oauth`；随后只做一次目标 Linux 镜像内的版本、结构查询和两端真实文档调用核验。

这份预演没有替代第 3 步的目标镜像验收，也没有扩大到角色上下文、模型运行或 benchmark。
