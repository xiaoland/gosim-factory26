# ARC Bench 平台交付合同

平台从应用根目录的 `frontend/` 和 `backend/` 部署 Web 应用。交付 `frontend/package.json` 的 `build` 脚本和 `backend/package.json` 的 `start` 脚本；平台先在 frontend 执行 `npm install`、`npm run build`，再在 backend 执行 `npm install`、`HOST=0.0.0.0 PORT=3000 npm run start`。应用须兼容 Node.js 20.19.3，后端遵守 HOST/PORT，提供构建后的前端与 API，并在 120 秒内启动。根目录的 `npm start` 或 `deploy.sh` 不能替代这条路径。

frontend 和 backend 必须可独立安装，不能依赖工作区外的包链接。依赖选择须适配平台 Node 与 npm；开发工具的使用沿用运行环境约定，候选仍须兼容平台逐目录 npm 安装、构建和启动。正式启动不能依赖全局 pnpm 或开发代理，backend 的正式入口须能服务 frontend 构建出的产物与 API。

预打包工具使用的 Node 不代表平台部署应用的 Node。核实平台兼容性时先读取实际入口与版本：

```sh
/usr/local/bin/node --version
/usr/local/bin/npm --version
```

该入口存在且版本符合上述条件时，用应用的真实候选核实逐目录安装、构建和正式启动路径，并将 `/usr/local/bin` 放在 PATH 首位，避免默认 PATH 中的工具 Node 遮蔽应用环境。平台的命令次序如下；共享生成环境中的启动检查仍遵守下文的端口预留约定，由 portless 提供 HOST/PORT：

```sh
cd frontend
PATH=/usr/local/bin:$PATH npm install
PATH=/usr/local/bin:$PATH npm run build
cd ../backend
PATH=/usr/local/bin:$PATH npm install
HOST=0.0.0.0 PORT=3000 PATH=/usr/local/bin:$PATH npm run start
```

保留安装、构建、启动的首次输出和具体错误，并在该正式路径观察应用可用性及需求行为。入口缺失或版本不符时，明确记录尚未验证的平台条件；工具 Node 下的通过结果不能代替它。安装或启动成功说明部署前提成立，需求覆盖仍须依据实际场景和候选结果判断。

生成、自检与后续评测共用环境，3000 端口留给评测。自检服务的启动与清理沿用通用运行约定，使用所核实的应用 Node 和 backend 的正式 start 脚本检查构建产物。该检查支持相同启动路径在所分配端口上的结果，固定 3000 的实际部署由平台验证。

交付应用不包含 `requirements/`、`.arc/`、`.git/`、`.factory26/` 等平台保留目录。交付保留需求规定的初始状态；开发检查准备过的数据不能成为正常启动的隐式前提。

修改已有应用时，平台交付检查要区分两种初态。升级检查从官方提供的业务基线副本开始，保留其中的数据库、仓库文件和其它业务数据，验证应用在迁移后仍能启动并保留原有行为；空数据库启动只证明新安装/初始化路径成立。不能删除业务数据库后重新播种，再把空库通过当作存量基线升级通过。两种检查的输入副本、迁移结果和实际启动错误分别记录。

## 验收运行的资源使用

本运行的应用验收使用单个测试 worker。调用真实 runner 时显式采用该设置，不只在报告里称为串行：Vitest 使用 `--maxWorkers=1 --no-file-parallelism`；I15 同时冻结 Vitest v4 原生支持的 `VITEST_MAX_WORKERS=1`，保留该环境。先从候选实际安装版本的 CLI help 确认支持的选项，其它版本用实际支持的单 worker 配置。Playwright/e2e 保留 `workers: 1`；其它 runner 采用其实际单 worker 入口。单 worker 只限制一个 runner 内部，不会自动串行其它责任的验收，也不会释放仍在运行的后台服务或作业。保留 owned job/session 直至正常完成或明确关闭，不能用测试命令返回或 Agent turn 结束代替进程闭合。
