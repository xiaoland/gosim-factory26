# Factory26 Console

两个界面按产品职责分别维护，共用本目录的一份前端依赖声明和 lock。

| 界面 | 源码与操作 | 构建产物的消费者 |
| --- | --- | --- |
| Lab Console | [Lab 页面](lab/README.md)：run 状态、资源、日志、费用、评测和 Braid 投影挂载。 | `python3 -m lab serve` 的 `static_root` 指向 `consoles/lab/web/dist/`。 |
| Braid Console | [Braid 协作界面](braid/README.md)：对象、讨论、审阅与原生会话；旧冻结服务使用对应 Python 后端。 | `consoles/braid/service.py prepare` 只冻结 `consoles/braid/web/dist/`。 |

从仓库根执行 `pnpm --dir consoles install --frozen-lockfile`，再分别执行 `build:lab` 或 `build:braid`。依赖、cache 和构建产物须位于 WorkSSD；完整接入与保存状态边界见[运行说明](../docs/deployment/console.md)。

Braid 原生投影仍归 `sources/braid/viewer`，Lab HTTP 宿主仍归 `lab/serve.py`。界面挂载关系不改变这两个组件的职责，构建输出也不能互换。
