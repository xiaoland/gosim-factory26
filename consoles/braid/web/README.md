# Braid Console 前端

这里是 Braid 协作产品的 React/Vite 前端，负责 Braid 对象、讨论、PR 审阅、原生会话、Trace、工作区和 origin 阅读。它与 `consoles/braid/service.py` 的旧冻结服务配套，不承担 Lab run 的状态、资源或恢复入口。

依赖声明和 lock 位于上级 `consoles/`，从仓库根目录执行：

```sh
pnpm --dir consoles install --frozen-lockfile
pnpm --dir consoles build:braid
pnpm --dir consoles dev:braid
pnpm --dir consoles preview:braid
```

`build:braid` 运行 TypeScript 编译检查并生成 `web/dist/`。`dev:braid` 将 `/api` 转发到 `127.0.0.1:8765`，需要先按[历史 Console 合同](../../../docs/deployment/history/console.md#旧冻结-console-服务合同)准备对应服务；`preview:braid` 只提供静态预览，不提供旧服务 API。修改 Python 后端后必须准备新的服务制品。构建和 pnpm store/cache 必须位于 WorkSSD。

## 源码定位

| 文件 | 修改内容 |
| --- | --- |
| [src/App.tsx](src/App.tsx)、[src/navigation.ts](src/navigation.ts) | Braid 首页、运行选择、页面身份与离页草稿保护。 |
| [src/Home.tsx](src/Home.tsx)、[src/runs.ts](src/runs.ts) | Braid 运行登记摘要与生产者记录类型。 |
| [src/BraidRun.tsx](src/BraidRun.tsx)、[src/Discussion.tsx](src/Discussion.tsx) | Braid 对象、讨论和人工操作。 |
| [src/Review.tsx](src/Review.tsx) | PR 冻结审阅、责任与结论。 |
| [src/Sessions.tsx](src/Sessions.tsx)、[src/Transcript.tsx](src/Transcript.tsx)、[src/FileBrowser.tsx](src/FileBrowser.tsx) | 会话导航、原生对话与 Trace、工作区和 origin 阅读。 |
| [src/api.ts](src/api.ts)、[src/http.ts](src/http.ts) | Braid API 类型、请求、状态和响应错误。 |
| [src/components/ui/](src/components/ui/)、[src/components/console-ui.tsx](src/components/console-ui.tsx) | UI 基元、请求态与可访问弹窗。 |
| [src/theme.css](src/theme.css)、[src/style.css](src/style.css) | 主题 token 与 Braid Console 布局；配置见 [components.json](components.json)。 |

对象、会话、原文和代码读取合同见[界面与读取合同](../docs/contracts.md)。旧服务准备、登记和维护见[历史 Console 合同](../../../docs/deployment/history/console.md#旧冻结-console-服务合同)。Lab 运行页面属于 [Lab Console](../../lab/web/README.md)。
