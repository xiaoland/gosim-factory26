# I14 tester.army/e2e 接入核对

2026-10-02，I14 接入材料与实施证据。用户已授权 I14-0 实现、基础验收及冻结实验启动，要求增加独立 variant，让 tester.army/e2e 承担默认浏览器工具职责，同时保留 agent-browser。既有操作与冻结使用 ARC 运行绑定，保留其历史身份；供应商选择属于实验配方。内层 e2e 仅使用 glm-5.3-flash，不能绕过 Braid session 保护使用受限昂贵模型。本文保留正式发布包的来源核对，并记录独立 addon、接线和真实操作反馈；I13 冻结包与公共 runtime 锁文件没有修改。

本次侧会话用户明确要求“请你处理该耦合”，授权修正 e2e 配置固定 ARC 地址的限制。`tools/e2e.config.ts` 现读取实验注入的 `FACTORY26_BASE_URL` 与 `FACTORY26_API_KEY`，保留缺失配置的明确错误、末尾斜线规范化和 Flash 模型选择；技能说明同步修正。没有修改四个 variant 入口或共享恢复的 ARC-only 行为，这些仍归主线设施重构。没有修改旧冻结包、运行现场或启动实验；非 ARC 渠道的实际模型兼容性未在本次验证。

本次 `node --experimental-strip-types --check variants/pi-braid-i14-e2e/tools/e2e.config.ts` 与所改三文件的 `git diff --check` 均退出0。仅取得配置语法与补丁格式反馈，没有发模型请求或运行基础设施测试；改动留在工作区，未提交。

## 发布与实际入口

用户指定的 [tester.army/e2e](https://tester.army/e2e) 是已经发布的 TypeScript 框架，官方 Markdown 指向 [tester-army/e2e](https://github.com/tester-army/e2e)，并提供本地 CLI、SDK 和 MCP。它与 TesterArmy 云平台 `ta` 是不同入口，本 variant 不需要 `ta`、云账户或托管浏览器。[官网正文](https://tester.army/e2e.md)

| 项目 | 已观察事实 |
| --- | --- |
| 核心包 | [`e2e@0.15.1`](https://registry.npmjs.org/e2e/0.15.1)，`latest`；npm 记录发布时间为 2026-10-01 09:49:27.893 UTC。CLI bin 是 `dist/cli/bin.js`，命令名 `e2e`。 |
| Web engine | [`@e2e-dev/web@0.11.1`](https://registry.npmjs.org/@e2e-dev%2fweb/0.11.1)，peer 为 `e2e >=0.15.0 <1`、`playwright >=1.63.0 <2`。 |
| Node | 两个包要求 `>=22.12.0`；Factory 工具 Node 24 满足，官网应用 Node 20.19.3 不满足，所以 e2e 命令必须使用工具 Node。 |
| License | 两个 npm tarball 均声明 Apache-2.0，包含 LICENSE/NOTICE。分发时保留。 |
| 安装生命周期 | 两个顶层包均没有 `preinstall/install/postinstall`；不据此声称所有传递依赖已经审核或执行验证。 |
| 原生依赖 | 默认 `web()` 通过 Playwright 启动本地 Chromium，也可配置 Firefox/WebKit。移动 engine、Kernel/EAS 等托管 provider 是可选包，不属于本次 Web 接入。 |
| 发布身份 | 已下载两个正式 tarball，只解包读取，SHA-512 与 registry 的 `dist.integrity` 一致。GitHub 调查时 main 是 `1554360ba2b3d3aff5efeff443b16d8985a169ca`；接线应冻结 npm 版本与 lock，不能把随后变化的 main 当作这个发布包。 |

原始 HTTP 头、官网/文档正文、registry 元数据和发布 tarball 保存在 `runs/iteration14/tester-e2e-research/`。`retrievals.json`、`retrievals-extra.json` 保存请求 URL 与状态，`artifacts.json` 保存下载包的校验身份。`web.open` 对指定页面返回 HTTP 400 `Unsupported content-type: text/markdown`，随后使用保持 TLS 校验的系统 curl，官网 HTML 与其正式 `.md` 均返回 HTTP 200。Python 默认 CA 路径出现 `CERTIFICATE_VERIFY_FAILED`，没有关闭证书校验。

## 手动操作与 AI E2E 是两条用途

`e2e mcp --headless` 是 stdio 服务，外层固定四个工具：`open_session`、`tools`、`call`、`close_session`。打开会话取得 session id 与实际工具目录，再通过 `call` 执行 `observe`、`tap/type/press/select/check/scroll/drag/upload/navigate/back`、`locate`、`screenshot` 和按能力提供的坐标操作、录像。节点 id 属于最近观察，后续操作必须使用当前 id；每个调用显式传 session，结束关闭自己的 session。默认最多四个 session，空闲 30 分钟或总寿命四小时会关闭；客户端断开时关闭全部所属 session。[MCP 文档](https://e2e.tester.army/docs/reference/mcp.md)

发布包 `dist/mcp/session.js` 和 `dist/agent/interactive-step.js` 明确由外部 coding agent 驱动手动会话，配置模型不会参与；但 `open_session` 调用 `loadAiSdk()`，所以手动 MCP 也需要安装 `ai@^7`。MCP 操作不自动写成测试、不进入 replay cache，也不会产生与 `e2e run` 相同的测试结论；正常关闭会话不等于应用验收通过。发布包目录没有独立 console/network 调试工具，不能直接等同 agent-browser 的全部诊断接口，需要时保留 agent-browser 或使用应用/Playwright 原生反馈。

`e2e run` 执行 TypeScript 测试，`test/expect` 来自 `e2e`，Web 的 `browser` fixture 可由 `@e2e-dev/web` 提供；精确 locator/assertion 可完全不调用模型。`agent.act` 用模型完成目标，`agent.assert/waitFor/extract` 用模型判断当前观察。`e2e explore` 是无测试文件的模型探索。首版具备这些原生能力，但是否在正式实验中启用 AI step，必须随运行配方冻结。[写测试](https://e2e.tester.army/docs/writing-tests.md)、[CLI](https://e2e.tester.army/docs/reference/cli.md)

AI action 只有经后续检查验证后才有机会缓存重放；judgment 不缓存，重放失败可回到模型。因此缓存命中不代表本轮检查完全免费，也不代表应用整体通过。第一次工具因素对照建议不跨 run 共享 cache，显式记录 cache 模式及是否 replay，避免先前运行状态成为额外因素。[缓存文档](https://e2e.tester.army/docs/cache.md)

## 模型、图像与费用前提

e2e 没有默认模型或共用 API-key 环境变量，config 接收 AI SDK 的实际 model instance。官方提供 `createOpenAICompatible({ name, baseURL, apiKey }).chatModel(modelId)`，可以指向本地 Factory ARC 网关，不要求改成 TesterArmy/Vercel/OpenRouter 计费。可按发布包自身开发依赖选择冻结 `ai@7.0.107` 与 `@ai-sdk/openai-compatible@3.0.53`；这两个版本已核对 registry，接线已生成 variant 独立完整 package-lock.json，安装采用 npm ci --ignore-scripts。[模型文档](https://e2e.tester.army/docs/models.md)

手动 MCP 截图作为 MCP image 返回。当前 Pi 通过 shell/mcporter 使用 MCP；固定的 `mcporter@0.14.0` 已提供 `call --save-images <dir>`，将图像解码写入文件并打印路径，随后可由原生 read 或已配置的 vision/browser-operator 消费，无需另写图像解码器。工具返回 `isError:true` 时 mcporter 将退出值设为 1。发布包 `dist/cli/image-output.js`、`dist/cli/call-command.js` 是依据；只有实际读到落盘图片，才证明下游模型取得图像。

AI E2E 的 act 默认模型必须支持工具和图像；图像由同一个 AI SDK model route 接收，框架不会自动委派 Pi 的 vision 角色。judge 默认沿用 act model，也可另配 `judge`。`@ai-sdk/openai-compatible@3.0.53` 的实际发布代码支持 `image_url`、`reasoning_content` 和 `reasoning_effort`，能配置现有 `baseURL/key`；这证明接口存在，尚未证明 ARC 上 GLM 的多轮 tool call、结构化 judgment 与图片请求都能成功。首次收费操作只能在运行授权后验证，保留具体 HTTP 状态与 provider 内容。

建议首轮 e2e AI step 与工具对照的主/浏览器模型统一使用已选择的 `glm-5.3-flash`，judge 不另换模型；沿用本轮 ARC 费用模式。e2e 的额外模型调用会产生模型费用，`maxSteps/maxModelCalls/maxInputTokens` 是单次 agent call 的限制，不是 Braid session 名额保护，也不是总美元上限。现有 `scripts/model_budget.mjs` 只在 Pi `before_provider_request` 接缝工作；e2e 自己通过 AI SDK 发请求不会自动经过它。若未来让 e2e 使用受限昂贵模型，必须先把调用归到发起 Braid session 并共享该名额保护，不允许通过内层模型绕过限制；首轮只用 Flash 可以避免新增昂贵模型路由。

默认本地浏览器没有 TesterArmy 服务费用；启用托管 browser provider、第三方 model gateway 或订阅登录则是新费用/账户前提，不属于当前建议。手动 MCP 不新增内层模型调用，但驱动它的 Pi 会话本身仍有模型消耗。显式设置 `E2E_TELEMETRY_DISABLED=1`，避免默认遥测；不执行 `e2e feedback` 或 GitHub reporter。上游技能的自动反馈建议不取得向外发送消息的授权。

## 最小接线范围

建议新增工具因素 variant，派生 I14 共同基线：无 cleaner，review 由关联 Issue 现有负责人承担。只改变浏览器默认操作/应用 E2E 材料，保留 agent-browser 可用。它与共同基线应冻结同一 Braid/Pi、review 机制、主模型/角色、输入、根 Issue TypeScript 偏好、费用模式及重复次数。不要直接派生专门 reviewer 对照，否则独立审阅身份与工具能力同时变化；历史 I13 也不能作为严格受控基线。

以下范围已经进入获授权实现；真实操作结果另见本文末尾：

1. 在新 I14 制品依赖中冻结 `e2e@0.15.1`、`@e2e-dev/web@0.11.1`、`ai@7.0.107`，需要 AI step 时另冻 `@ai-sdk/openai-compatible@3.0.53`，保留 license。用工具 Node 24 提供 `e2e` CLI wrapper。复用现有依赖/浏览器构建路径，不增加 npm 之外的安装器。
2. 给 I14 制品提供匹配的 Playwright 1.63 与 Chromium。当前公共 lock 是 Playwright Test/core 1.61.1；新 web 包的 peer 不满足。发布包 `WebOptions` 没有 `executablePath/launchOptions`，本地 launch 也不读取 `BROWSER_EXECUTABLE_PATH`；缺浏览器会在 prepare 阶段尝试 `playwright install`。不能把旧 Chromium wrapper 环境当作已接线。主线已选定独立 addon：保留公共 runtime 的 1.61.1，仅 e2e 使用单独的 Playwright 1.63.0、匹配 Chromium 和 Linux 库。这样不迫使基线或 I13 升级；工具对照包含这套浏览器版本差异，解释结果时不能将全部差异归因于 MCP 接口。
3. 在 variant 的 build/run 技能选择、profile 及 browser-operator/executor/explorer 材料里增加独立 e2e 导航，并将默认浏览器探索改到 e2e MCP。直接读取冻结包内 `skills/e2e/` 和 `e2e guide`；发现入口只留名称、description、路径。官网称包内有 `docs/`，但此次 0.15.1 tarball 没有该目录，不把离线 docs 路径当成可用契约。技能正文不内联到任何 prompt；完整应用验收仍按允许需求设计判据。
4. 复用 mcporter 增加 e2e stdio 定义，设置 `lifecycle: 'keep-alive'`，否则每次 CLI 退出都会关闭浏览器，后续 session id 无效。按 checkout 确定 `cwd`/config，不能让所有不同工作树共享同一 e2e server：e2e 同时打开的 session 必须属于同一 config，跨 config 返回 `CONFIG_IN_USE`。mcporter 的连接身份包含真实 cwd、command args 和环境，因此每 checkout 定义可在同一 daemon 中形成独立连接；具体运行接线需真实操作确认。
5. 设置 run 专有 `MCPORTER_DAEMON_DIR` 并在收尾停止自有 daemon。mcporter 默认取 `os.userInfo().homedir()`，只修改 `HOME` 不保证 daemon 隔离。应用 URL 来自实际 portless 服务；已经由 portless 管理时 config 只给 URL，不再声明另一个 app command。输出使用每次检查的独立目录并记录候选 commit、服务及数据身份；截图用现有 `--save-images`，命令原始结果复用已有执行记录或 `with-service --check-only`。不新增通用浏览器抽象、独立检查平台或另一套服务生命周期。

显式生成 config/工具材料比运行交互式 `e2e init` 更容易固定版本与职责：`init` 会添加应用依赖、示例测试、skill 和 MCP 注册，可能扩大生成应用改动。配置文件的目录就是 e2e 的 project root，tests/output 都相对此目录；ESM import 必须能在该目录正常解析依赖，不能假设 `NODE_PATH` 或 `BROWSER_CHECK_NODE_MODULES` 自动解决。工具准备不能顺手给 Factory 自身增加测试；应用 E2E 文件属于生成应用的需求验收。

## 可采证据与实施反馈

`e2e run` 到达测试执行后写 `report.json`，可选 markdown/JUnit，保存步骤、结果、错误与 artifact 路径；`--ai-trace` 记录模型往返及用量，trace 中的图片替换为字节数。退出值区分 0 通过/显式跳过、1 应用失败或超时、2 配置/依赖/策略错误、3 服务/engine/provider/artifact/cleanup 设施失败、4 内部错误、130 中断。不能把设施失败算有效零分。[CLI 输出与退出码](https://e2e.tester.army/docs/reference/cli.md)

启动前的 config/collection/依赖失败可能没有新 report，旧文件会保留；每次调用使用独立输出目录并先以真实退出结果解释，避免读取上次报告冒充本次结果。MCP 是手动会话，不产生这个测试 report；`trace: 'on'` 可采 Playwright trace，`screenshot` 经 mcporter 落盘，录像由 start/stop_recording 保存。MCP close 会把 cleanup 问题写进返回文本，server 自身正常断开返回 0，所以关闭命令退出 0 还不能证明清理成功，必须读回 cleanup 内容与实际自有进程。录像不脱敏；设置 secret 后 MCP pixels 会受 taint 限制，浏览器仍可按语义节点操作。这些差异由真实操作验证，而不是通过阅读 reviewer 结论代替验收。

实施后的必要反馈是无模型真实操作：两个隔离 checkout 连续 open/observe/action/screenshot/close，确认 session 延续、图片能被原生读取、各自服务/数据及清理隔离，原始错误/退出值/trace 可采；再用生成应用既有验收入口确认 CLI 流程。这里不编写或运行 Factory/Braid 测试，也不把这份静态调查称作浏览器兼容验证。AI step 的实际模型兼容纳入此次已授权的最小正向操作；由主线注入 ARC 运行绑定后执行，完整矩阵仍由主线负责。

本次没有发布缺失或 license 阻碍。主线已授权并冻结共同基线的独立工具因素接线：无 cleaner、默认 IssueOwner review、手动 MCP 优先，保留按需求使用原生 AI E2E 的能力。输入、矩阵、ARC 绑定及实验启动由主线 packet 持有；本文不扩大矩阵。内层 Flash 的调用与消耗必须保留独立证据。

## 当前实现与验收进度

`variants/pi-braid-i14-e2e/tools/e2e/` 固定 e2e 0.15.1、web 0.11.1、ai 7.0.107、openai-compatible 3.0.53、Playwright 1.63.0。`tools/build-e2e.py --output <新目录> [--docker-context <context>]` 使用 Debian Bookworm 的 Linux amd64 构建，提前安装 Chromium，再导出依赖、浏览器与非 glibc 动态库。公共工具 Node 24.10.0 执行 CLI。没有执行 npm package 生命周期脚本。构建不修改公共依赖树；`addon-source.json` 保存构建输入和 Docker endpoint 身份。

`build.py` 接受 `--e2e-runtime` 或 `FACTORY26_E2E_RUNTIME`，将 addon 放入 `runtime/e2e`。`run.py` 默认使用该目录，保存 addon 来源，配置短路径的 run 专有 mcporter daemon，并在 workspace 清理前停止自己的 daemon。mcporter 的 e2e server 使用 keep-alive，真实 cwd 来自每次调用的 PWD；config 放在 checkout 的独立 `.factory-e2e/`，依赖 symlink 指向 addon，输出在其内部。

独立 `harness/skills/e2e/SKILL.md` 与各角色的技能发现入口已经接线；技能正文没有内联到 system/profile/task。默认手动 MCP；图像交给现有 mcporter 保存及原生读图，agent-browser 保留诊断用途。Linux 构建与真实操作原始记录位于 `runs/iteration14/tester-e2e/`。Python 源码编译通过；浏览器可用性另由下列实际操作证明，没有编写或运行 Factory/Braid 测试、smoke 或换名探针。

### 实际结果与边界

最终可打包 addon 是 `runs/iteration14/tester-e2e/linux-addon-final/`，解包约 795MiB；`addon-identity.json` 保存确切包版本、Chromium/Headless Shell v1243（153.0.8010.12）执行文件 SHA-256 和 87 个可移植 Linux 库的数量。`addon-source.json` 的 SHA-256 为 `831166dd47e0186bc3ff41c66dcf9a35cb74d3ba89a11552bf35b17d2a4fc6ec`。首个构建只下载 full Chromium；核对 e2e 默认 headless 路径后补齐 Shell。构建期间材料修订的两个旧目录已经标记 superseded，build.py 拒绝打包；首轮原始日志保留，不把它们冒充最终来源。最终构建冻结了 WSL Docker endpoint 与开始时的输入 hashes。

真实操作使用自有 WSL2 Linux amd64 容器，限制 2GiB 内存、2CPU，普通本地 HTML 由 Python HTTP 服务提供。现有工具 Node 为 24.10.0，mcporter 为公共 runtime 中的 managed 0.14.0。手动配置的模型地址特意为 `127.0.0.1:9` 且没有模型 key，实际 MCP 操作没有内层模型调用。两组 checkout 使用同一 run daemon、不同 cwd/config/HTTP URL；A 会话连续打开、读取 tap 参数、点击、截图，状态从“尚未保存”变为“已保存”。B 在 A 尚未关闭时成功打开，仍呈现“尚未保存”，没有 CONFIG_IN_USE；A 关闭后 B 仍能截图、点击及关闭。截图通过 --save-images 落盘，A 图像经原生 view_image 独立读取，能看到中文标题、保存按钮和已保存状态。无效节点 tap 返回具体 LOCATOR_NOT_FOUND 与退出 1，保留原始错误和未改变的屏幕；正常会话关闭均退出 0、没有 cleanup 错误。两组 Playwright trace.zip 已归档。对应操作记录为 `05` 至 `14` 的 JSON 与 `manual-artifacts-a/b/`、`screenshots-a/b/`。

操作容器最初采用 python-slim/PID1=sleep，暴露两项共用 mcporter 的系统前提：缺少 ps 时 ownedProcessTree 在工具派发前失败；没有 reaper 时 Chromium/esbuild 孤儿成为 defunct，daemon stop 的退休检查失败。首次错误、安装记录、进程列表及恢复来源均保留。只在自有操作容器安装 procps/tini；使用 tini 子树启动后的真实 e2e open/close 和 daemon stop 均退出 0，见 `18` 至 `20`。主线已收到正式生成环境应提供 ps 与 init/reaper 的前提；没有修改 lab 或其它运行。自有操作容器最后停止并移除，结束其全部进程，保留 `21` 的收尾状态。

主线另明确允许至多一次内部 Flash explore。唯一实际调用使用其私有 ARC env 经 exec stdin 注入（凭据没有进入 argv 或输出），goal 为点击保存并确认已保存，max-steps=1、timeout=180000、cache off、trace on。结果 exit 0、run.status=passed、run.errors=[]、一次 action 成功，29.91秒，结束原因为 step-limit；报告、summary、AI trace 和浏览器 trace 在 `ai-one-step/`，原始脱敏 stdout/stderr 在 `17-ai-explore.json`。不是正式 benchmark，也不能据此声称应用整体验收。

该次 explore 的结构化提取并非无异常：两次 MODEL_OUTPUT_INVALID 被框架修复，初始 planner 的提取仍 ASSERTION_INCONCLUSIVE 并回退 Survey，最终 extract 与 act 成功。stderr 保留 responseFormat/structuredOutputs 的 SDK warning，未为消除警告擅自改变已验证配置，也未追加调用。report/CLI 只记 15,757 tokens；AI trace 保留全部六次响应的 usage，总计 16,967 input + 806 output = 17,773 tokens，其中 cached input 8,128，差额 2,016 来自被拒绝的 schema 响应。`17-ai-usage-summary.json` 保存两种口径，不将 runner 报数当作 ARC 账单。该次内层请求没有 image part，所以实际验证的是语义观察及工具路由；ARC 内层多模态仍只有发布 SDK 的静态接口依据。外层 MCP 图像保存与消费已实证。

没有剩余发布/依赖阻碍或需要用户另选的常规接线事项。主线负责共同基线、packet、正式打包/矩阵与启动；独立工具对照应沿用相同输入、review、主模型与费用配方，解释时保留 Playwright/Chromium 版本差异。此资料负责人没有 commit，也没有改变 I13、共享依赖锁或其它 variant。
