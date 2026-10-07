# Factory26 Braid Console

本目录保留 Braid 协作产品和旧冻结 Console 的独立源码。它读取 Braid 对象、审阅、原生会话、工作区和归档，并按 `factory26.exp-console-service` 合同管理旧服务；不启动实验、不替代 Lab run 的状态与恢复入口。

| 要做什么 | 阅读入口 |
| --- | --- |
| 修改 Braid 页面、构建前端 | [web/README.md](web/README.md) |
| 修改对象、会话、原文或代码读取 | [界面与读取合同](docs/contracts.md) |
| 准备、登记或解除旧冻结服务 | [历史 Console 合同](../../docs/deployment/history/console.md#旧冻结-console-服务合同) |
| 服务实现 | [service.py](service.py)、[server.py](server.py) |

Braid 前端和旧 Python service 是一条独立构建链：在仓库根目录执行 `pnpm --dir consoles build:braid` 构建 Braid UI，再由 `service.py prepare` 冻结本目录的 Python 与 `web/dist/`。它不消费 `consoles/lab/web/dist/`，避免将 Lab API 页面装入旧 Braid API 服务。
