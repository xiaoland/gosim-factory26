# pi-minimal 完整配置复核

状态：用户已批准正式参赛；最新修正已应用，只保留 advisor 子角色，并加入 Ponytail；本轮用户批准修正为官方Pi扩展默认full。每600秒检查参赛余额，不高于100取消本次活动run并停止后续任务。

| 配置 | 冻结目标 |
| --- | --- |
| 主会话 | glm-5.3-flash，high，支持图像输入 |
| 唯一子角色 | advisor：kimi-k2.7-code，原生thinking，fresh独立上下文，只读建议 |
| 扩展 | pi-subagents、pi-background-bash；无Braid、SVC |
| 技能 | agent-browser、hyperformula、handsontable、better-auth-best-practices、organization-best-practices、fixing-accessibility、ponytail（官方4.10.0原生Pi扩展，full） |
| MCP | Context7、Exa，通过mcporter |
| 工具环境 | pnpm、portless、rg、ast-grep、Chromium、Playwright |
| 条件 | 保留已批准通用交付条件，无Issue/PR/packet流程，无额外角色或强制委派 |
| 参赛 | 同一冻结包，hackathon--github与hackathon--sheet，official_evaluation |

GLM图像输入依据：官方模型卡 https://huggingface.co/zai-org/GLM-5.3-Flash 及 https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash 。因此不打包DS Vision，不配置独立视觉子角色。主会话自行读图与操作浏览器。

每题保留Pi原生主/子会话和工具事件；长度截断仅在同会话接续，不自动换模型。Ponytail full由官方Pi扩展注入主会话及advisor，配置PONYTAIL_DEFAULT_MODE=full。预算保护是宿主脚本，不增加模型上下文负担。
