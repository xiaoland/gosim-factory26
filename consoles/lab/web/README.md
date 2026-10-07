# Lab Console 前端

这里是 Lab Console 的 React/Vite 前端，只负责运行登记、运行摘要、资源、日志、费用、评测和 Braid 原生视图挂载。对应后端是 `python3 -m lab serve --config FILE`；API 与静态页面由同一个 Lab 服务提供。

依赖声明和 lock 位于上级 `consoles/`，从仓库根目录执行：

```sh
pnpm --dir consoles install --frozen-lockfile
pnpm --dir consoles build:lab
pnpm --dir consoles dev:lab
pnpm --dir consoles preview:lab
```

`build:lab` 运行 TypeScript 编译检查并生成 `web/dist/`。`dev:lab` 将 `/api` 转发到 `127.0.0.1:8765`，需要先启动 Lab 服务；`preview:lab` 只提供静态预览，不提供 API。构建和 pnpm store/cache 必须位于 WorkSSD。

## 源码定位

| 文件 | 修改内容 |
| --- | --- |
| [src/App.tsx](src/App.tsx)、[src/navigation.ts](src/navigation.ts) | Lab 首页、运行选择、页面身份与离页草稿保护。 |
| [src/Home.tsx](src/Home.tsx)、[src/runs.ts](src/runs.ts) | 运行登记摘要与生产者记录类型。 |
| [src/RunOverview.tsx](src/RunOverview.tsx)、[src/api.ts](src/api.ts) | 运行状态、资源、日志、费用、评测和 Braid 挂载数据。 |
| [src/http.ts](src/http.ts) | HTTP 请求、状态和响应错误。 |
| [src/components/ui/](src/components/ui/)、[src/components/console-ui.tsx](src/components/console-ui.tsx) | UI 基元、请求态与可访问弹窗。 |
| [src/theme.css](src/theme.css)、[src/style.css](src/style.css) | 主题 token 与 Lab Console 布局；配置见 [components.json](components.json)。 |

Braid 协作对象、讨论、审阅、原生会话和旧冻结服务属于 [Braid Console](../../braid/web/README.md)，不在这里维护。Lab 服务的部署和登记合同见[运行说明](../../../docs/deployment/console.md)。
