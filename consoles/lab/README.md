# Factory26 Lab Console

当前 run 的只读页面和保存状态由 `python3 -m lab serve --config FILE` 提供；本目录只包含 Lab Console 的 React/Vite 前端。后端入口在 [lab/serve.py](../../lab/serve.py)，页面主体在 [RunOverview.tsx](web/src/RunOverview.tsx)，接入合同见[Console 运行说明](../../docs/deployment/console.md)。

在仓库根目录安装共享依赖并构建 Lab 前端：

```sh
pnpm --dir consoles install --frozen-lockfile
pnpm --dir consoles build:lab
```

构建输出 `web/dist/` 由 Lab service 的 `static_root` 配置消费。Braid 协作对象、讨论、会话和旧冻结服务的独立前端与 Python 入口归 [consoles/braid](../braid/README.md)，不在本目录复制或冻结。
