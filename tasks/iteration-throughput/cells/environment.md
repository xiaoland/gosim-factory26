# 执行环境只读取证

2026-09-22（Asia/Shanghai）。本轮没有安装、上传、启动容器或实验、调用模型、修改源码或登录新的 Meter 会话。仅写入本报告。

## 已确认的路径

| 用途 | 路径与证据 | 当前边界 |
| --- | --- | --- |
| Linux 打包与无模型容器资格 | 本机 `docker --context arcbox-win`，endpoint 为 `ssh://win-ws.localhost`；Docker 28.5.2、Linux x86_64、root 为 `/var/lib/docker`。已有 `factory26-p0-runtime:pi`（4932ed6039df）、`factory26-p0-runtime:codex`（88ce5d5a8161）、`factory26-p0-acceptance:local`（9afc5a7a18c3）。 | 镜像存在不证明与当前源码相同，后续构建仍须核对 package/source identity。无须为了打包修复 WSL 默认 daemon。 |
| 已有冻结应用的 ARC 评测 | `ssh wsl.win-ws.localhost`，仓库 `/home/yyh/Development/factory26`；`third_party/arc-bench` 为 `1eb018367bedd618d3b9ced406ce07fb423d4956`，Git 工作树干净。 | 这是已有 ARC 评测路径，不等于官方 local-simulation Agent 容器已就绪；本轮未启动应用或 Playwright。 |
| ARC 依赖与浏览器 | ARC `package-lock.json` SHA256 与 `node_modules/.factory26-lock` 均为 `11958fdcff244058b3510844b426d98c71dd6be0e61009ec1622ded4e97f22bf`；Playwright 1.61.1，实际解析的 Chromium 为 `/home/yyh/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome`，文件存在且可执行。 | ARC 依赖缓存约 177 MB，Factory 缓存约 1.6 GB，浏览器缓存约 1.3 GB。无需重新安装已有匹配依赖。 |
| WSL Node 与入口 | `/home/yyh/.cache/factory26/toolchain/node-v26.3.0-linux-x64/bin/node`、同目录 npm、项目 `.venv/bin/python`、`scripts/factory.py`、`scripts/submission.py` 和 `variants/factory/config.json` 均存在。 | 非交互 SSH 的默认 PATH 未找到 node/npm，直接执行时需采用既有 toolchain PATH 装配。源码/构建是否匹配当前本机版本须由后续运行资格检查决定。 |
| 官方 local-simulation 源码 | 本机 `/tmp/factory26-local-simulation-cfbbc287`，HEAD 为 `cfbbc287ee1bbffcf1e936545e4803145693a8d8`。 | WSL 常用 checkout 和 `/tmp` 下未发现该 runner；不据此断言全盘不存在。 |

WSL 根磁盘共 251 GB、可用 209 GB（13% 使用）；`/tmp` 为 tmpfs，可用 6.6 GB（17% 使用）。大包和长期 workspace 应放仓库或磁盘目录，不把 `/tmp` 的容量当根磁盘容量。Windows 磁盘探测因 SSH 命令解释失败未得到容量；Docker `system df` 在 25 秒内未返回，未重试或清理。因此不能用 WSL 剩余空间证明 Docker Desktop 存储空间充足。

## 官方模拟器的本地限制与最小解法

WSL 默认 `unix:///var/run/docker.sock` 不可连接，`docker` 和 `docker.socket` 服务 inactive；但 Windows 的 `arcbox-win` context 可用，因此“所有远端 Docker 都不可用”不成立。可用 daemon 的镜像清单没有 `arcbench-local-submit:latest` 或 `arcbench-runner:local-base`。

2026-09-23 定向复核时，[官方 local-simulation 仓库](https://github.com/code-philia/hackathon-local-simulation)的公开 `main` 仍为 `cfbbc287ee1bbffcf1e936545e4803145693a8d8`。其 `build-image.sh` 要求独立 ARC-Bench website 仓库的 `backend/runner/Dockerfile`，或已有主办方基础镜像；仓库自身不包含该 Dockerfile，[Releases](https://github.com/code-philia/hackathon-local-simulation/releases) 没有发布项，[组织 Packages 公开页](https://github.com/orgs/code-philia/packages)也未列出可拉取容器。README 中的 `registry.example.com/arcbench/...` 是示例占位符，不是可执行镜像引用。组织公开仓库列表没有 `arc-bench-website`；`arc-bench`、`hackathon-local-simulation` 和 `agentic-requirement-compiler` 的公开 `main` 均不存在 `backend/runner/Dockerfile`。

`third_party/arc-bench` 的 Dockerfile 是 ARC benchmark reproduction 环境，基于 Playwright `v1.54.0`、使用端口 3301；固定模拟器要求网站生产 Runner 的 `run_submission.py` 环境，文档列出的基础镜像为 `mcr.microsoft.com/playwright/python:v1.57.0-noble`、Node.js `20.19.3` 和端口 3000，因此不能互换。`arcbox-win` 现有 `factory26-p0-runtime:pi`（4932ed6039df）、`factory26-p0-runtime:codex`（88ce5d5a8161）、`factory26-p0-acceptance:local`（9afc5a7a18c3）及临时 Factory 构建镜像均来自本项目的 Bookworm/Python 或 Rust 构建链；单独的 `node:20.19.3-bookworm-slim` 也没有 production Runner 和 Playwright。它们没有官方 Runner 的来源与内容身份，不能改 tag 冒充。

最小外部前提是取得以下任一不可变制品：主办方发布的 Linux amd64 完整 local-submit/基础 Runner 镜像真实 registry 引用与 digest，或与正式 Runner 对齐且含 `backend/runner/Dockerfile` 的 `arc-bench-website` 精确 revision。完整 local-submit 镜像可经 `--image` 直接使用；只有基础 Runner 时，才用冻结仓库的 Dockerfile 加入 `local_runner.py` 这一层。未取得前不自行拼装近似镜像。该限制只影响官方 local-simulation 的本地并行矩阵，不阻断官网 Competition 路径和已有 ARC 应用评测。

获得镜像后，可优先沿已有 Windows Docker daemon 路径部署。`local_submit.py:run_container` 使用 workspace bind mount，源路径必须被 daemon 所在主机访问；仅在 Mac 设置 `DOCKER_CONTEXT=arcbox-win` 不能让 Windows 自动看见 Mac 的 `/tmp` workspace。应把 wrapper 与 workspace 放到可被 Docker Desktop 挂载的执行主机目录，或验证既有 WSL 集成后在 WSL 执行。这是运行前提，本轮未传输文件或更改集成设置。

## Meter 与近期 429

既有 [capabilities.md](capabilities.md) 记录三个最小调用均为 HTTP 429、`type=insufficient_quota`、`Free allocated quota exceeded.`，没有 usage/cost。这支持“当时请求触发免费额度拒绝”，不能证明 Meter 总余额为零。

本轮复用已登录的 [Meter 页面](https://meter.arc-bench.com/user)，只读取总览与 API 说明，并点击总览刷新。页面同步时间为 2026-09-22 20:04:19，显示可用余额 **173.503704 CNY**、账单状态“已同步”。未读取或输出密钥、未创建新登录会话、未发送模型调用。

总览与 API 说明没有提供 key scope 或 free allowance 数值；错误说明仅泛称 429 可表示限流或余额不足。浏览器当前账户与仓库外 `llm.env` 中比赛 key 的绑定未验证，不能据非零余额宣布原 key 已恢复。现有 Playground Cookie 仅匹配 `arc-bench.com`，不能当作独立 `meter.arc-bench.com` 的登录凭据；本轮没有跨域复制 Cookie。

API 文档的聊天请求示例使用 `https://your-onr.example.com/v1/chat/completions` 占位地址，没有给出真实网关地址。因此本次页面证据不能确认当前实际 base URL 是 `https://api.arc-bench.com/v1`，也不能定位免费额度拒绝来自 Meter 还是前置代理。

最小解法是让 Meter 管理端核对具体比赛 key 的账户绑定、免费额度与可用余额适用范围，或提供能只读查询这些字段的接口。无需先修改模型 adapter，也不应靠换模型或反复调用消耗探测。完成额度核对后，主会话再执行已获授权的最小模型资格调用；本报告不将历史 429 视为永久阻塞，也不将余额显示视为资格通过。

### 密钥归属补查（2026-09-22）

本轮只复用已有 Meter 登录页，定向查看此前未核查的“用量详情”和“请求明细”入口。可见导航仍只有总览、用量详情、支持模型、请求明细、API 文档与退出登录；账户名称是静态文本，未暴露账户/密钥管理入口。用量详情提供模型、时间范围、粒度、时区和 Token 单位筛选；请求明细提供分页与 Token 单位，没有可见的 key ID/指纹、额度组、免费额度、练习券、失效时间或实际 base URL。没有重新读取总览/API 占位文档，也没有猜测其它路由。

`~/.config/factory26/llm.env` 的文件元数据确认修改时间为 `2026-09-20T11:32:46+08:00`、权限 `0600`。因为页面没有可比较的密钥元数据，本轮没有读取该文件内容，更没有输出或修改密钥。现有只读 UI 不能证明该 key 与当前 Meter 账户的对应关系，也不能证明免费额度已恢复；需等待用户对具体 key 的核对或管理端提供明确元数据。未登录新账户、创建 key、改设置或调用模型。

## 最新 API 实测：额度门槛已恢复

同一文件内的 key 在稍后一次最小 curl 请求中返回 HTTP 200：`deepseek-v4-flash`，prompt 86 tokens、completion 19 tokens、合计 105；`runs/qualification/quota-recheck.json` 保留时间与 usage。该证据足以撤销“当前额度仍拒绝”的运行阻塞，无需等待用户更新 key；它不证明账户归属，也不代替工具调用/视觉资格。此前 urllib 尝试在本机传输层失败，没有取得 HTTP 响应，随后用既有 curl 路径完成这一次服务端重验。
