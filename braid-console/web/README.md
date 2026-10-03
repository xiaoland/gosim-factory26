# Console 前端开发

前端使用 React、TypeScript、Vite、shadcn/ui、Tailwind CSS、Radix、Lucide、TanStack Query 和 React Router。Node 与 pnpm 要求以 [package.json](package.json) 的 `engines`、`packageManager` 为准，不在文档登记开发者本机版本。

在本目录安装和构建；Mac 的 pnpm store/cache 与生成文件须位于 WorkSSD，按 [开发工具准备](../../CONTRIBUTING.md)选择项目环境。

```sh
pnpm install --frozen-lockfile
pnpm build
```

`pnpm build` 执行 TypeScript 编译检查并生成 `dist/`。开发时先按 [Console 运行手册](../../docs/deployment/console.md)准备并启动独立冻结服务，再执行 `pnpm dev`；Vite 将 `/api` 转发到 `127.0.0.1:8765`，页面变化由 Vite 加载。仓库中的 `server.py` 不能直接启动；修改 Python 后端需要重新准备新服务制品。`pnpm preview` 只预览静态构建，不提供 CLI API。

## 源码定位

| 文件 | 修改内容 |
| --- | --- |
| [src/App.tsx](src/App.tsx)、[src/navigation.ts](src/navigation.ts) | 首页、运行选择、页面身份与离页草稿保护。 |
| [src/Home.tsx](src/Home.tsx)、[src/runs.ts](src/runs.ts) | 通用运行登记摘要与生产者记录类型。 |
| [src/BraidRun.tsx](src/BraidRun.tsx)、[src/Discussion.tsx](src/Discussion.tsx)、[src/api.ts](src/api.ts) | Braid 对象、讨论、人工操作和运行状态。 |
| [src/Review.tsx](src/Review.tsx) | PR 的冻结审阅、责任与结论。 |
| [src/Sessions.tsx](src/Sessions.tsx)、[src/Transcript.tsx](src/Transcript.tsx)、[src/FileBrowser.tsx](src/FileBrowser.tsx) | 会话导航、原生对话与 Trace、工作区和 origin 阅读。 |
| [src/http.ts](src/http.ts) | HTTP 请求、状态和响应错误。 |
| [src/components/ui/](src/components/ui/)、[src/components/console-ui.tsx](src/components/console-ui.tsx) | UI 基元、业务请求态与可访问弹窗。 |
| [src/theme.css](src/theme.css)、[src/style.css](src/style.css) | 主题 token 与 Console 布局；shadcn 配置见 [components.json](components.json)。 |

路由、轮询、草稿、原文分页与读取边界统一维护在 [界面与读取合同](../docs/contracts.md)，服务启动、登记和维护统一维护在运行手册。新增页面时同步前端路由与 Python 的有效页面匹配；API 和缺失静态文件须保留实际错误响应。
