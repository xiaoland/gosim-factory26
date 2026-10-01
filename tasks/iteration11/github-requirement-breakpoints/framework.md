# 最终应用的框架、组件与数据接线

2026-09-30。仅核最终 `e68661975b53` 下载工作区；下文 **F** = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`。未执行源码、安装依赖或重新构建。

**这是实际接线的 React 单页应用及 Express/SQLite 服务，不是只有静态画面或只装了组件包。没有发现能归咎于“框架没装对”的全局启动断点；已确认的高影响问题位于页面组合、导航终点、前端状态更新和业务对象解析。** 这不等于证明每个组件的全部交互正确。

## 真实实现

| 层 | 最终声明与实际使用 | 能证明的范围 |
|---|---|---|
| 前端 | `frontend/package.json:12–27`：React/React DOM 18.3.1、React Router DOM 6.28.0、Vite 5.4.11、TypeScript 5.7.2 | `main.tsx:1–15` 的 `createRoot`/StrictMode → `App.tsx:8–12` 的 BrowserRouter → AuthProvider → AppShell → routes。不是安装后未使用。 |
| 路由 | `routes.tsx:49–153` 挂载身份、组织、仓库、内容、Issue/PR 页面 | `Link`/`useNavigate` 真正驱动路由；`backend/src/app.js:62–71` 对非 API GET 返回 SPA，支持直接地址与刷新。缺陷在某些路由指向占位组件，非 Router 未挂载。 |
| 会话与状态 | `auth/AuthContext.tsx:43–70` 查询 `/api/auth/session`，登录/退出更新 context；`api/client.ts:46–66` 同源 fetch 携带cookie | 无 localStorage 假登录。页面局部使用 React state；后端是持久状态来源，但跨组件衍生状态仍需显式重取，Checks→merge 的缺口见 cell。 |
| Radix | 只声明 Dialog 1.1.4 与 Checkbox 1.1.3 | `components/Dialog.tsx:19–33` 实际组合 Root/Portal/Overlay/Content/Title/Description；`CheckboxField.tsx:30–47` 实际使用 Root/Indicator、受控checked与label关联。账户退出由 AccountMenu:80–107 打开 Dialog 并调用 API；注册页消费 CheckboxField。 |
| 其它基础控件 | `Button.tsx`、`TextField.tsx`、`RadioGroup.tsx` 是原生HTML的React封装；`Menu.tsx` 是手写disclosure | 不是所有控件都声称来自Radix。Button转发真实button属性，TextField关联label，Menu含真实links、Escape和外部点击处理。手写本身不构成缺陷；需要核对各控件的业务名称、唯一性与动作。 |
| 图标与样式 | lucide-react 0.468.0；UnoCSS 0.65.4、reset及少量全局CSS | `AppShell.tsx:4,60` 等实际渲染图标；Vite config:1–14注册React与UnoCSS插件；main:3–5导入reset、`virtual:uno.css`、styles；uno.config定义theme和shared shortcuts，styles.css提供focus ring。不是只列依赖。 |
| 后端 | Express 4.21.2、cookie-parser 1.4.7、better-sqlite3 11.10.0 | `app.js:28–45,52–60` 真正挂载六领域router、JSON、cookie及attachUser；`server.js:18–22` 先开DB/migrate/seed再监听。API与前端为同源。 |
| 数据 | SQLite WAL、foreign_keys、迁移和同步事务 | `db/index.js:15–46,53–54`，具体实体在migrations与各service/router；提交存tree_json、branch存head指针，构成简化版本控制域模型。需求ROOT排除了外部Git remote协议，未要求后端必须使用真实Git服务器。 |
| 生产启动 | frontend独立npm install/build；backend独立npm install/start | root package主要是开发工具，生产backend为plain ESM JS，`backend/package.json:13`直接node src/server.js，不依赖平台不存在的backend编译步骤。 |

`requirements/prerequisites.md` 是0 bytes；requirements.yaml未规定必须采用某个前端框架/组件品牌。因此不能以“没用某库”或“不是全套Radix”判定违反需求。

## 已有运行证据

原始 [官网日志](../../../runs/analysis/i11-github-e68661975b53/20260930T033923Z/logs-readable.json) 记录：frontend安装203包；Vite转换1714 modules，产出21.01kB CSS与355.75kB JS，03:10:16构建完成；backend安装154包，03:10:37在`0.0.0.0:3000`监听。这排除了本次“完全无法安装/编译/启动”的解释，不能证明浏览器中每条业务路径都可用。旧生成过程中有Node24/Node20的better-sqlite3 ABI故障，已有修复和后续成功证据，不能拿旧错误替代本次最终状态。

最终应用历史验收152 E2E与194 backend/typecheck结果沿用[身份报告](../../pi-minimal/github-score-analysis/i11-e68661975b53.md)引用的原始日志；本轮只检查其中与候选有关的路径和断言，未运行它们。

## 具体组合错误与反证

1. **Link正确、组合后的页面错误。** AppShell:114–119与HomePage:21–27均渲染同名Sign in/Sign up；App:10把两者组合。REQ-6父层:2837–2839要求首页唯一Sign in link。单看Link组件或单页面片段不会发现跨shell/body重名。它可能阻断所有使用唯一入口的登录旅程；人类可点其中任一链接，所以不能称登录API坏了。
2. **菜单正确、路由终点错误。** AccountMenu:56把Your repositories指向/settings/repositories；routes:68渲染SettingsPlaceholder，实际OwnerRepositoriesPage另挂/:owner。用户从菜单进入不能获得预期仓库列表；搜索与owner链接仍有替代入口，不能扩成所有仓库不可达。
3. **局部状态正确、衍生状态未同步。** PR Checks更新detail.checks，而同页merge资格依赖另一份detail.merge；既有检查把更新和读取之间加reload，所以局部PASS不足以验证原页面动作链。详见[Issue/PR cell](cells/issues-pulls.md)。
4. **选择器显示正确、后端对象作用域错误。** Manage access按当前组织列团队，但提交的name在后端先跨组织解析；同名团队可被解析成另一组织并422。详见[身份/组织cell](cells/identity-org.md)。

反证也具体：Menu未使用Radix DropdownMenu是有意识保留需求link角色，而非不会使用组件库。foundation原生 `2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.jsonl L49 / 04:33:54` 明确分析menuitem与link区别并选择真实anchor；最终Menu:25–28与AccountMenu保持该策略。该选择没有造成上述首页重复，不能误把“手写组件”作为统一原因。

同份native L37明确因官网只构建frontend而选择无需编译的backend JS。两项选择都有需求/交付约束依据。精确源路径与定向原文见[entry-native-excerpts](evidence/entry-native-excerpts.txt)。

## 未证部分

本轮没有最终浏览器DOM/accessibility快照、像素对照或新的运行操作。构建日志不能证明每条UnoCSS utility都达到预期，也不能证明各弹窗焦点/全部键盘路径正确；未发现具体反例就不把这些一般可能性列为低分原因。当前有证据支持先修用户旅程连接处的契约，而非更换技术栈或强制所有控件套用组件库。
