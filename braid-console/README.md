# Factory26 Exp Console

Console 是 Factory 实验的查看与人工接入界面，提供已登记运行的首页、Braid 对象、审阅、会话和代码阅读。它属于实验基础设施，不依赖 SVC 或 ARC，不进入参赛包；源码保留在 Factory26 的 `braid-console/`，没有独立 Git 仓库。

Console 拥有服务登记与显示状态，Lab 的冻结执行器拥有实验事实和控制门控，Braid CLI 与保存归档拥有协作事实。页面上的写入许可或 Docker 状态不构成实验控制授权。当前新接入拒绝暂停生成；恢复须经过冻结执行器的能力和身份核对，不能绕过运行手册直接调用 Docker。

| 要做什么 | 阅读入口 |
| --- | --- |
| 修改页面、构建前端 | [前端开发说明](web/README.md) |
| 修改对象、会话、原文或代码阅读 | [界面与读取合同](docs/contracts.md) |
| 准备服务、登记现场、维护访问容器或解除接入 | [Console 运行手册](../docs/deployment/console.md) |
| 判断实验状态、检查点和恢复能力 | [实验恢复手册](../docs/deployment/recovery.md) |

## 源码定位

| 文件 | 职责 |
| --- | --- |
| [service.py](service.py) | 冻结程序、前端和 Python 身份，管理服务登记、访问资源及解除接入。 |
| [server.py](server.py) | HTTP 路由、静态页面、Braid CLI 桥和人工操作回执。 |
| [docker_runtime.py](docker_runtime.py) | 核对执行空间与容器出生身份，通过冻结实验执行器请求控制。 |
| [run_records.py](run_records.py) | 从明确登记的生产者记录读取运行事实，不根据目录或对象状态推断。 |
| [archives.py](archives.py) | 读取冻结 SQLite 对象和 native manifest，不启动原 CLI、worker 或 Git。 |
| [native_sessions.py](native_sessions.py)、[redaction.py](redaction.py) | 按会话身份和字节游标读取原生 JSONL，并脱敏。 |
| [code_files.py](code_files.py) | 在登记空间读取当前工作区及固定提交的 origin，不检出或拉取代码。 |
| [web/src/](web/src/) | 页面、HTTP 类型与业务组件；具体分工见前端说明。 |

## 开发入口

先按 [前端说明](web/README.md)安装依赖与构建。后端只接受 `factory26.exp-console-service` schema 1 的冻结服务，不能直接从工作树启动 `server.py`。准备独立开发制品使用 `service.py prepare --development-output`，完整参数和实际启动方法见运行手册；它不等于迁移或更新已有服务。

Mac 的依赖、构建、开发制品和长期服务均放在 WorkSSD。长期服务应位于实验 `runs/`、`prepared/`、`.factory26/` 之外，例如 `/Volumes/WorkSSD/Services/factory26/exp-console/<部署名>/`。远端 WSL/sfp7 可使用核实后的远端执行存储；Mac 回收的记录仍放 WorkSSD。真实部署身份和已实测范围以运行手册所链接的证据为准。
