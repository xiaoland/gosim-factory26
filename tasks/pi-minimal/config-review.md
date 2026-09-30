# pi-minimal 完整配置复核

当前：用户要求改路由后从头重跑官网两题。GLM保持BigModel自有key，Kimi改为ARC自带key；不带入旧应用或会话。旧两题已取消并保留归档，原正式参赛结果保留。费用观察每600秒记录供应商消耗，不把比赛100元阈值套到个人API账户。

| 配置 | 冻结目标 |
| --- | --- |
| 主会话 | BigModel自有key：glm-5.3-flash，high，支持图像输入 |
| 唯一子角色 | ARC自带key：advisor kimi-k2.7-code，原生thinking，fresh独立上下文，只读建议 |
| 扩展 | pi-subagents、pi-background-bash；无Braid、SVC |
| 技能 | agent-browser、hyperformula、handsontable、better-auth-best-practices、organization-best-practices、fixing-accessibility、ponytail（官方4.10.0原生Pi扩展，full） |
| MCP | Context7、Exa，通过mcporter |
| 应用环境 | Node 20.19.3 + npm，保留 package-lock.json；不要求 pnpm、portless |
| 工具环境 | app-env、rg、ast-grep、Chromium、Playwright；预包现有 pnpm、portless 保留但不作为工作要求 |
| 条件 | 保留已批准通用交付条件，无Issue/PR/packet流程，无额外角色或强制委派 |
| 当前运行 | self_funded；GitHub、Sheet共用新的纯Harness冻结包从头运行，不使用参赛额度 |

GLM图像输入依据：官方模型卡 https://huggingface.co/zai-org/GLM-5.3-Flash 及 https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash 。因此不打包DS Vision，不配置独立视觉子角色。主会话自行读图与操作浏览器。

每题保留Pi原生主/子会话和工具事件；长度截断仅在同会话接续，不自动换模型。Ponytail full由官方Pi扩展注入主会话及advisor，配置PONYTAIL_DEFAULT_MODE=full。预算保护是宿主脚本，不增加模型上下文负担。
