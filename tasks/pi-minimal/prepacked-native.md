# 应用 Node 与 better-sqlite3 预编译资源

本轮已实现源码，未构建 runtime、运行安装测试、启动模型或重启实验。生成应用及其 package.json/node_modules 未修改。

## 选择与实现

`submission/Dockerfile` 的 Node 24.10.0 服务 Pi、portless 等工具；官方 runner 已提供 `/usr/local/bin/node` 20.19.3，见此前 `.arc/preflight.json`。不再携带第二套 Node，也不全局替换工具运行时。

`submission/build.py` 新增 `runtime/bin/app-env`：校验 `/usr/local/bin/node` 为 20.19.3，将 `/usr/local/bin` 放在 PATH 首位并设置 `FACTORY26_APP_NODE`。pnpm 启动器改为 `exec "${FACTORY26_APP_NODE:-$HERE/node}" ...`，其余工具仍使用 `$HERE/node`。因此不是只改 PATH：通过 app-env 调用的打包 pnpm 进程本身就由 Node 20 执行，其普通生命周期脚本继承同一 PATH；原生扩展安装不再默认针对工具 Node 24 编译。应用若主动配置独立执行环境、硬编码另一 Node 或安装同名 node binary，仍属于应用自己的覆盖行为，不由工具偷偷重写。

主线可在依赖指南使用：

```sh
# 在相应 frontend 或 backend 目录中执行。
app-env pnpm install
app-env pnpm run build
app-env npm run start
# 开发服务工具仍使用自己的 Node 24，子应用继承 Node 20 环境。
app-env portless github-api pnpm run dev
```

app-env 还导出 `npm_config_better_sqlite3_local_prebuilds`，指向 `runtime/native-prebuilds`。`submission/Dockerfile` 通过带 checksum 的 ADD 放入官方 `better-sqlite3-v11.10.0-node-v115-linux-x64.tar.gz`，SHA-256 为 `a16b1df74f095e47b6404b4af1c237d2aca75f431d8f4d1f498419263632ed03`。该文件来自官方发布资产，下载后只计算摘要，没有加载、解压到应用或执行。官方资产 API 报大小 1,065,899 字节；该旧资产无上游 digest 字段，故冻结的是本次从 HTTPS 官方源取得的实际内容摘要。

[prebuild-install v7.1.3 的 util.js](https://github.com/prebuild/prebuild-install/blob/v7.1.3/util.js) 按包名读取这个原生 local_prebuilds 环境变量，并按版本、Node ABI、平台和架构形成文件名；[download.js](https://github.com/prebuild/prebuild-install/blob/v7.1.3/download.js) 先查该本地文件，再走缓存/下载。因此对于这一精确版本与 ABI，安装脚本可以从包内取得原生产物，省去网络下载和本地源码编译；不需要伪造 npm 缓存文件名，也不向应用复制 node_modules。资源可在[官方 v11.10.0 发布](https://github.com/WiseLibs/better-sqlite3/releases/tag/v11.10.0)查询。

## 准确边界

- 此处预缓存的是 better-sqlite3 **11.10.0 / Node ABI 115 / Linux x64 glibc** 的原生产物，不是 npm 全部依赖的离线镜像。npm 包源码和其它依赖仍按正常依赖安装取得；其它版本、Node24 ABI137、musl 或其它架构不命中此资源。
- 库选择仍由 Agent 根据应用需求决定。生成应用自行声明依赖与锁文件；使用 pnpm 10 时仍须按需允许 better-sqlite3 的构建脚本。本轮不全局放开安装脚本，也不替应用选择数据库。
- 预包不自动改变官方 runner 的独立安装/评测命令。生成期或人工正式路径检查通过 app-env 才显式启用该资源；平台未继承此环境时，npm 仍按正常上游安装路径取得原生资源。不能据此声称官方评测全程离线。
- 新入口与预编译文件要在下一次 runtime 构建、制品冻结后才存在。未向旧已冻结包、已停止 pi-minimal 或正在进行的 I11 恢复热注入。
- 已做 Python 源码语法编译、生成 app-env 的 `sh -n` 与差异格式检查；这些不等于安装或运行验证。Docker checksum ADD、平台 Node、实际 pnpm 生命周期与产物加载留给后续获授权制品构建/运行观察。

## I11 恢复全量扫描的紧急修复

已删除 `submission/recover_completed.py` 中遍历整个 run 并逐文件 open/read(4)/chmod 的旧兼容补偿。恢复 ZIP 解压处已经从 external_attr 恢复每项权限，`verify_package` 已按清单恢复新 runtime 的可执行位，新生成 Pi/PBB/Braid 启动器也分别设置可执行位。再次扫描包含 node_modules 的数 GB 工作区既无必要，还会把任意带 shebang 的普通源码提升成可执行文件。

这是针对保留完整模式的本次摘剪 ZIP 成立的删除，不声称能修复历史上已丢权限的任意归档；那类输入应依据明确丢失项修正归档或定点恢复，不重新遍历所有文件猜测。

当前已运行 Python 进程仍持有旧代码，改磁盘源码不会让它跳过扫描。安全继续方式是等待现有有限扫描完成；该扫描在启动 Braid 之前。若决定中止，应保留当前解压目录作为现场，并在新 output/新容器用修复后的包重新恢复，不能原地重新执行会拒绝已有 run 的恢复入口。没有建议调试注入、跳过栈帧或修改运行进程的方案。本轮未干预该进程。
