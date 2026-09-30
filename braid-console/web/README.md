# Braid Console 前端

前端采用 React 19、TypeScript、Vite、Ant Design 6 与 TanStack Query。Node.js 22.12+；本机使用 Node.js 24.15、pnpm 11.20。

在本目录执行 `pnpm install --frozen-lockfile`。开发时先启动仓库中的 `braid-console/server.py`（端口 8765），再执行 `pnpm dev`；Vite 将 `/api` 转发给该服务。执行 `pnpm build` 进行 TypeScript 检查并生成 `dist/`，由 Python 服务提供生产页面。`pnpm preview` 仅预览静态构建，不提供 CLI API。

对象列表、详情及已展开讨论每五秒读取 CLI 状态；未展开的隐藏正文和已解决历史只按需读取。编辑与评论草稿保存在当前页面中，不被轮询替换。所有写入均为一次明确的 `/api/action` 请求，不自动重试；HTTP 409 保留正文编辑草稿与原 revision，核对最新正文后可明确采用最新 revision。页面刷新或离开时草稿不会永久保存。
