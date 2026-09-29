请依据 @REQUIREMENTS@ 中的公开需求与参考图片，在 @OUTPUT@ 内独立实现完整 Web 应用。无人中途介入；常规歧义自行判断并记录重要假设。不要读取外部评测测试、参考应用或历史评分。

你可以直接读图和操作浏览器。使用 agent-browser 探索与诊断实际页面，参考图先辨别用途，再提取相关信息。可调用 advisor 获得独立建议；提供原始问题、必要材料和待决定事项，使用 fresh 上下文，不复制整段会话历史。它不是必经步骤，也不替你负责实现和最终交付。

按需使用已提供的赛题技能。Ponytail 使用 lite 程度：实现所需能力，优先采用现有成熟工具与清晰简单的办法，不因为省代码牺牲需求。Context7 用于库/API文档，Exa 用于检索外部来源；通过 mcporter 调用，参数不确定时 `mcporter list context7 --schema --no-oauth` 或 `mcporter list exa --schema --no-oauth`，不进入交互登录。

使用 pnpm 管理依赖，portless 分配开发服务端口，Vitest 做适用的局部检查；UI 使用成熟的组件库、图标库与 UnoCSS，语言和框架自行选择。预打包工具已在 PATH：agent-browser、pnpm、portless、rg、ast-grep；浏览器路径由 BROWSER_EXECUTABLE_PATH 给出，Node 检查依赖位于 BROWSER_CHECK_NODE_MODULES。最终验收自行编写可重复执行的自动化测试或脚本，判据来自原始需求；不要把实现现状当成需求。

后台任务取得完成结果与退出码后才声明完成；开发服务器使用 bash 的 service:true，工作结束后停止服务。无需用 sleep 反复轮询，使用原生完成通知。

生成与评测共用环境，3000端口留给评测。开发自检使用临时数据库、浏览器状态和缓存，不污染交付初始数据。交付目录应包含 frontend/package.json 的 build 脚本和 backend/package.json 的 start 脚本，目标环境为 Node 20；后端监听 HOST=0.0.0.0、PORT=3000 并服务前端和 API。保留 requirements/ 与 .arc/，不要写 .factory26/ 或 deploy.sh，不向外部仓库push。交付前停止自行启动的服务。
