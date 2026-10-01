# Braid Console 前端

前端采用 React 19、TypeScript、Vite、shadcn/ui、Tailwind CSS 4、Radix primitives 和 Lucide 与 TanStack Query。Node.js 22.12+；本机使用 Node.js 24.15、pnpm 11.20。

在本目录执行 `pnpm install --frozen-lockfile`。开发时先启动仓库中的 `braid-console/server.py`（端口 8765），再执行 `pnpm dev`；Vite 将 `/api` 转发给该服务。执行 `pnpm build` 进行 TypeScript 检查并生成 `dist/`，由 Python 服务提供生产页面。`pnpm preview` 仅预览静态构建，不提供 CLI API。

对象列表、详情及已展开讨论每五秒读取 CLI 状态；未展开的隐藏正文和已解决历史只按需读取。编辑与评论草稿保存在当前页面中，不被轮询替换。所有写入均为一次明确的 `/api/action` 请求，不自动重试；HTTP 409 保留正文编辑草稿与原 revision，核对最新正文后可明确采用最新 revision。页面刷新或离开时草稿不会永久保存。

工作项、Braid agent及provider详情使用原生History API管理query链接，主动切换增加历史条目，后退/前进重新读取URL；历史切换遵守同一未提交草稿保护。会话关系每五秒读取，原生JSONL正文按需按字节位置分页，刷新已加载页不会自动加载整份日志。元数据与正文读取失败分别呈现。

UI 的本地源码位于 `src/components/ui/`，`components.json` 保留 shadcn CLI 配置，`src/theme.css` 统一主题 token，`style.css` 负责 Console 布局。`components/console-ui.tsx` 组合业务提示、按钮请求态和可访问弹窗，不保留 Ant API 兼容层。后续组件可用 `pnpm dlx shadcn@latest add <组件>` 添加。

首页提供已登记/live/archive/写入许可概览；数字来自接入登记，不推断执行状态。工作项使用 Tabs、标题/编号搜索和状态/负责人筛选，空结果可一键清除。归档范围与缺口可展开，上方导航保持可见。会话目录支持历史筛选与身份/状态搜索；provider 优先显示原生对话，身份/材料及 Turn 历史按需展开，Turn 每页50条。Home 的首屏代码独立加载，进入运行后才加载 Braid 工作项与 Markdown 阅读代码。
