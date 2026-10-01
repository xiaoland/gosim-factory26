# Console 会话关系导航

2026-09-30。依据[packet](packet.md)记录的用户新需求与直接应用授权实施，源码与21:14 CST部署完成，真实只读接口验收完成，浏览器UI验收受工具阻断。Console改动不属于I13 Harness；未修改Braid源码、冻结binary、数据库或原生成容器，未跑模型或提交。

工作项关联从登记CLI的 `status --json.physical_sessions` 读取。CLI用 `provider_sessions → agent_instances → assignments → work_items` 查询，将持久agent ID写入 `group_id`，因此Console按该字段聚合Braid agent session，保留同一agent下全部已发现provider记录。`session_id`是provider恢复身份（Pi为文件路径），`native_session_id`是原生会话ID，两者不替代Braid agent身份。`context_path`所在physical目录提供记录ID供URL引用，避免把长provider文件路径作为路由编号。

该接口从physical目录开始枚举，不是数据库全部agent或provider历史的独立列表。页面说明缺失physical材料的会话可能未列出；空结果表示未发现可枚举记录，不能断言工作项从未启动。只把 `replaced/retired` 明确标为历史，其他生命周期按原值显示，不通过数组顺序、最大generation或provider状态推断逻辑agent生命周期或当前引用。物理暂停独立显示，暂停后的 `running` 是冻结前的持久生命周期，不表示仍在执行。

三级只读页面继续使用 `?run&kind&id`，扩展 `agent&provider`；主动导航用History API pushState，默认选择用replaceState，popstate重新读取URL。原有未提交草稿和提交中保护适用于点击、后退与前进。三个固定层级不需要新增路由依赖；advisor独立复核了该选择及草稿边界。

用户随后明确：“还要能阅读原生对话和工具调用内容。”原生正文成为本轮必需范围。现有CLI没有定向正文读取接口，因此Console独立只读适配层从CLI已返回的原生路径读取，在登记访问容器里执行固定Python JSONL reader；浏览器只发送physical记录ID和字节偏移，不提供路径或命令。每次正文读取重新核对inventory与文件header的native ID，按稳定字节位置分页（最多50条、约1MiB；单行超过8MiB明确失败而不截断/跳过）。末尾未完成行保留原偏移等待后续读取，JSON解析失败保留偏移和原文。工具参数、结果、具体错误与完整记录可展开；图片等非文本block提供原生JSON，未实现图片渲染。reader隐藏凭据字段、Bearer和常见key格式及读取环境中实际凭据值。

真实验收使用Python编译、TypeScript/Vite build、登记运行的只读API及浏览器；不建立或运行测试、mock、probe或自检。当前两题全部provider为Pi，Codex的header读取分支未实际验收；其他provider不能当作已支持。

20:52 CST读取原运行状态：GitHub和Sheet均 `running=true/paused=true`，PID分别5217、5181，StartedAt不变。CLI发现GitHub 7个Braid agent、26条provider记录（19 replaced、4 running、2 sleeping、1 idle）；Sheet 5个Braid agent、13条provider记录（8 replaced、1 running、4 idle）。原文保存在Mac `cli-status.before.json` 与 `http.before.json`。

后续独立只读诊断以SQLite `mode=ro`核对身份数量，仅用于验收证据，不成为Console数据耦合：GitHub数据库provider26/agent7，Sheet数据库provider13/agent5，与CLI inventory逐项一致，无观察到的数据库身份漏项。原生日志文件实际缺失GitHub1条、Sheet2条；缺失ID、路径、文件数量与完整FileNotFoundError保留在 `coverage.json` 和 `native-pages.before.json`。原因未证，不自动重建用户正在清理的材料。两题历史Pi首批50条读取成功；GitHub一个保留running记录也成功，Sheet一个idle记录明确缺文件而非空对话。

## 部署及当前可行验收

Python `py_compile`、TypeScript `tsc -b`及Vite 8.3.1 build通过，未引入依赖或建立测试。构建仍有既有bundle超过500kB的提示。最终资源为 `index-BROGd5Gi.js` / `index-PdJYewCM.css`；编译回执与源码/资源hash在 `compilation.json`、`source-manifest.json`。

部署前确认WSL现有Console、registry及journal路径仍在，没有恢复此前已删除的 `runs/braid-console-control/`。旧服务journal没有未终结started动作，服务没有CLI子进程；使用SIGINT停止PID204242，再部署backend与新资源并最后原子替换index，保留旧assets。旧服务使用ThreadingHTTPServer默认daemon线程，不能声称SIGINT保证等待请求；本次通过在途动作核对安排停机，新服务显式 `daemon_threads=False` 并在finally关闭server，为以后的正常退出保留收尾顺序。

新PID **483894**，仍监听127.0.0.1:8765，registry和journal沿用 `runs/iteration12/restart-20260930/` 原文件。新服务日志在WSL `/tmp/factory26-console-session-navigation-server.log`，收尾副本保存在本机证据 `server.log`。旧日志原路径已被删除，本次从仍打开的 `/proc/204242/fd/1` 保存722461字节到本机 `deployed-before-server.log` 后才停止服务；不是重建远端历史证据。旧源码、旧index与registry也分别保存在本机 `deployed-before-*`。

实际HTTP核对两个sessions列表分别26/13条；历史Pi正文两页分别50+50、50+46条，字节offset无重复，首批刷新offset一致。已加载范围工具调用/结果分别46/46、45/45，全部结果ID能匹配已加载调用ID。缺日志读取返回HTTP400并保留具体FileNotFoundError；未知physical ID返回“CLI未发现此provider session记录”。index、JS、CSS实际HTTP200，响应字节与本机构建逐项相同。原文与摘要在 `http.after.json`、`http-summary.json`，前后容器身份和状态在 `deployment.json`；两题PID、StartedAt和 `paused=true` 一致。

主Agent随后独立读取部署API，确认两题仍暂停、原PID未变，provider列表26/13条，各一个历史会话首页50条且无读取错误；证据为同目录 `primary-readonly.json`。这提供实现者之外的真实接口反馈，不替代尚未完成的浏览器交互验收。

缺失原生日志的native ID为GitHub `01a0f237-2032-7272-bc0d-1f1558293103`，Sheet `01a0f150-e352-7323-bb16-d580b17f818c`、`01a0f151-fec7-77d2-aee8-635a96fae8d2`。完整对应physical身份在 `missing-native-files.json`；这些数据未自动重建，用户清理是背景信息而非已证根因。

浏览器验收未完成。Chrome的 `createBrowserTab` 和inventory返回 `codex app-server exited before returning initialize`；IAB创建同一授权本地URL时安全检查报告“admin-enforced policy could not be verified, access was not granted”。未绕过管理策略或改用间接控制。`browser-unverified.json`保存工具拒绝及证据来源，不能当作成功页面观察；直链重载、实际后退/前进、取消切换后的草稿保留以及视觉正文/工具呈现待浏览器能力恢复后核对。当前两题没有Codex，Codex header及展示分支尚未真实验收；图片等非文本block仅可展开原生JSON。
