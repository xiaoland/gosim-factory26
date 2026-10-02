# 技术栈与预打包环境约定

状态：2026-09-29 用户批准共用部分及预打包环境改进，明确排除两题专属建议。已应用到两个活动 variant 的 adapter；统一制品尚未重建，实验等待两位审查 Agent 的结果及完整修复树复核。
用户已要求 pnpm、portless、Vitest、成熟组件库、图标库与 UnoCSS；没有指定 TypeScript、Vue 或其它应用框架。
本页只补工程默认值和按需选型依据，不预制应用业务源码或验收判据。

## 两题共用

- Agent 选择框架后使用其官方脚手架；SPA 可优先评估 Vite。按平台 Node 20.19.3 选择并固定兼容版本，不机械拉取 latest；不引入 monorepo 工具来破坏 frontend/backend 独立 npm 安装。
- 持久化优先评估 SQLite，利用事务完成相关写入；迁移与需求种子数据须可重复执行。自检使用临时数据库，正式应用启动准备自己的初始数据。数据库驱动与构建过程由 Agent 按实际运行环境核实。
- 前端优先使用同源相对 API，开发代理转发后端，减少 Cookie、CORS 与端口切换的差异。浏览器访问 portless 输出的 URL；最终验收仍验证构建产物与正式启动路径。
- 共享接口只在真实跨模块边界集中定义请求、响应和错误格式；有需要时选运行时 schema 库，不强制 TypeScript 或另加代码生成系统。
- Vitest 用于逻辑/API等适合的检查；复杂交互可按需使用 Browser Mode。完整应用验收保留 Playwright 自动化；agent-browser 用于开发探索与诊断。失败留下 trace、控制台和请求错误，复用已有浏览器与 with-service 工具，不另建检查框架。
- 成熟组件须核对实际 role、name、状态、键盘与焦点行为；统一少量视觉变量。图标打入产物，不依赖运行时远程取图。UnoCSS 动态类使用可静态提取的映射、safelist或适当的CSS变量。

## 边界与优先级

已落实同源开发/交付、持久化与初始状态、稳定的自动化反馈、UnoCSS 和组件语义接线。两题专属新增建议未采用，既有领域技能不因此删除。
variant adapter 表达工程要求，预打包环境提供外部命令、浏览器与按需积累的运行内包缓存，技能提供按需知识，生成 Agent 自己选择和创建应用实现；通用 ARC adapter 只承接平台协议。

## 核实来源

- https://vite.dev/guide/
- https://sqlite.org/whentouse.html
- https://vitest.dev/guide/browser/
- https://playwright.dev/docs/trace-viewer-intro
- https://unocss.dev/guide/extracting
- https://unocss.dev/presets/icons

缓存按 pnpm 10 的 npm 配置格式设置 `npm_config_cache` 与 `npm_config_store_dir`，与锁定版本一致；不套用新主版本的配置方式。来源：https://pnpm.io/10.x/configuring 。
