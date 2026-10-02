# 浏览器检查：技术准备与使用路径预演

源码入口后继：本文件中的 `variants/pi-team-mixed` 现为 `variants/pi-braid`；历史冻结包与运行身份不变。

状态：源码和工具材料已修改，正在构建配套 Linux runtime，尚未取得应用检查结果。
目标：降低可靠应用检查的编写、失败定位和复跑成本，保持判据忠实于需求。

## 决定与接口依据

推荐保留 agent-browser 0.38.1 用于开发探索；为自动化应用检查补齐 `@playwright/test` 1.61.1。
现有 `harness/npm/package.json` 已固定 `playwright-core` 1.61.1，没有 test runner；npm 官方元数据确认 `@playwright/test@1.61.1` 依赖 `playwright@1.61.1`，要求 Node >=18，与运行时 Node 24 及目标应用 Node 20 相容。
具体冻结依赖由现有 package-lock 保存，不在模型运行时下载测试工具。

Playwright 原生提供语义 locator、操作自动等待、web-first assertion、独立 browser context 和失败 trace。
这些能力直接处理 A 中自制 Bash 快照检查的摩擦，不另建断言 DSL、浏览器服务或 Factory 测试框架。
agent-browser 也有语义定位和条件等待，不能把此次选择解释成它没有这些能力；它继续负责探索与短反馈。

来源：[Playwright 断言](https://playwright.dev/docs/test-assertions)、[定位](https://playwright.dev/docs/locators)、[操作等待](https://playwright.dev/docs/actionability)、[配置](https://playwright.dev/docs/test-configuration)、[agent-browser 命令](https://agent-browser.dev/commands)。
API 存在不等于新制品已经可运行，真实可用性留给开工后生成应用的检查执行。

## 环境和分发

1. 在 `harness/npm/package.json` 增加精确版本的 `@playwright/test`，更新原 lock；沿已有 Docker 分层构建一次 Linux runtime，后续生成与实验复用。
2. 统一使用该版本 Playwright 配套的完整 Chromium，安装命令使用现成 CLI 的 `install chromium --with-deps --no-shell`，固定 `PLAYWRIGHT_BROWSERS_PATH` 在 runtime 内。
3. agent-browser 通过已有 `AGENT_BROWSER_EXECUTABLE_PATH` 使用同一浏览器；Playwright config 的 `launchOptions.executablePath` 指向相同 `runtime/bin/chromium` 包装入口。
4. `submission/build.py` 保留现有动态库、字体和浏览器包装方式，改为从 Playwright 的 `chromium.executablePath()` 取得真实二进制；增加标准 `playwright` CLI 包装，确保 ZIP 删除 `.bin` 后仍可用。
5. `scripts/runtime.py::prepare` 的本机缓存与 Linux 构建取得同版本浏览器；`scripts/agent_support.py::browser_executable` 保留优先使用便携入口，并按实际缓存布局取得本机二进制。已有冻结 runtime 不原地修改。

选择配套 Chromium，是因为 Playwright 官方明确不保证任意 Chromium 版本兼容；避免把 agent-browser 当前下载的另一个 Chrome 版本直接当成已验证组合。
agent-browser 官方支持显式指定 Chromium 二进制。
来源：[Playwright 浏览器版本与 no-shell](https://playwright.dev/docs/browsers)、[agent-browser 浏览器入口](https://agent-browser.dev/engines/chrome)。
复用的是同一个浏览器文件，不共享两个工具的活动 browser context 或登录状态。
这里不增加 OS 沙箱或容器层，继续使用既有运行环境。

## 测试文件怎样取得依赖

不能只把 CLI 放进 PATH 就声称 `.spec.ts` 能 import `@playwright/test`：应用 clone 与 runtime 的 node_modules 不在同一解析路径。
采用普通 Node 模块目录解析，让检查目录拥有自己的 `node_modules` 链接，目标是包内已安装的 runtime/node_modules。
variant 提供 `BROWSER_CHECK_NODE_MODULES` 和 `BROWSER_EXECUTABLE_PATH` 两个路径环境变量；示例使用普通命令：

```sh
mkdir -p checks
# 首次建立示例目录时添加；已有忽略规则时沿用，不覆盖原文件。
printf '/node_modules/\n' >> checks/.gitignore
ln -s "$BROWSER_CHECK_NODE_MODULES" checks/node_modules
BASE_URL=http://127.0.0.1:4100 playwright test --config checks/playwright.config.ts
```

`checks` 只是工具材料中的示例目录，可按应用结构调整；依赖链接不提交，测试源码与必要配置可以随应用提交。
不在应用根或所有 worktree 的祖先目录注入 node_modules，避免生产代码偶然依赖 Harness 包而在正式部署时缺依赖。
不使用 NODE_PATH 伪装 ESM 解析，也不要求 Agent 为每次检查联网 npm install。
已有 node_modules 不覆盖；已有应用测试工程优先复用其明确依赖。

新增 `harness/skills/browser-checks/`，由 `SKILL.md` 短入口、`references/writing-checks.md` 操作指南和一份普通 Playwright config 示例组成。
config 示例采用标准配置：baseURL 取环境，headless，launchOptions 指向已打包浏览器，retries=0，trace='retain-on-failure'，screenshot='only-on-failure'，默认一个 worker；Agent 可按应用的数据独立性调整并行。
没有新 CLI 协议；执行仍是 `playwright test`，报告和退出码保持原样。
重跑时使用新的原生 output 目录保留此前失败证据，因为 Playwright 会清理所指定 outputDir。
默认不使用失败后自动重试，防止把不稳定结果隐藏为一次 PASS；条件等待和自动重试断言仍正常使用。

## 指引与消费者

`variants/pi-team-mixed/build.py` 选入新工具技能，`run.py` 分发并为主会话启用；两个 executor 的 skills 加入同一入口。
browser-operator 继续使用 agent-browser，强调它提供开发观察，不承担最终自动化验收。
executor 取得工具技能入口与现有 svc-implementation workflow，不把所有浏览器正文直接塞进系统指令。
SVC 定义需求、判据、观察、条件和结论；新工具技能定义如何用既有 API 表达这些决定，不写任何 Hackathon 题目断言。

写检查的指南覆盖：

- 按需求选择观察边界；定位用来找到目标，断言用来判断要求，二者不能混同。
- 多匹配时核对真实作用域和业务身份，再限定 locator；不能默认 `.first()` 来消除歧义。
- 等待实际结果成立，使用 locator assertion，避免固定 sleep 和“点了即成功”。
- 独立用例构造自己的条件；一段连续业务旅程可用一个 test 加 steps，使前置失败后后续步骤明确未执行。
- 页面需要登录时，登录自身的检查与把已有身份作为其它检查的前置条件分开；共享准备确有需要时采用原生 fixtures/project dependencies。
- browser context 隔开 cookies 不代表后端数据已重置；数据和服务生命周期按应用方案处理。
- 保留失败动作、期望、实际结果及必要 trace；不可捕获断言异常后继续报通过。

## 使用路径预演

| 场景 | 方案给出的路径 | 仍要取得的真实证据 |
| --- | --- | --- |
| 编写首条保存设置检查 | 原始要求→实际设置入口→填值/保存→结束旧会话并重新登录→读回与断言；从新工具技能直接取得 API 写法 | 脚本实际加载模块并驱动已打包浏览器 |
| 页面有两个同名按钮 | 按任务给定对象/区域缩小作用域，再观察结果；唯一性若是明确要求，另作相应断言 | 真实失败不是被 `.first()` 或宽泛文本掩盖 |
| 登录前置失败 | 原生测试失败，依赖步骤未执行；首先解释登录失败，不输出后续功能的假 PASS | 原始错误和 trace 能定位第一处失败 |
| 浏览器 context 全新，服务数据仍旧 | 用独立数据或已设计的重置步骤复跑，不把 context 当数据库隔离 | 第二次运行结果的有效条件明确 |
| 集成候选改动 | 复用检查源码在更新候选上执行，保存对应 commit、服务入口和结果 | 最终证据与实际导出应用对应 |

本预演是文档/API/路径层面的推演，没有运行测试或模拟；依赖和浏览器组合的真实反馈在已授权的应用验收阶段获得。
后续验收先复用已有冻结应用，避免为检查工具是否顺手而重新生成完整应用。

## 独立接口与使用路径预演补充

源码路径核对后的关键门槛如下；仍是预演，未执行包、浏览器或应用检查。

| 接续操作 | 必须看见的结果与当前断点 |
| --- | --- |
| `submission/Dockerfile` 安装配套 Chromium，`submission/build.py` 冻结 runtime，`scripts/package_agent.py` 写 ZIP | 现有 Dockerfile 只运行 `agent-browser install --with-deps`，build.py 也只找 `.agent-browser/browsers/chrome-*`。实施时须把安装和二进制发现统一切到 `playwright`/`chromium.executablePath()`；`--no-shell` 下载完整 Chromium，两个工具都显式指向 `runtime/bin/chromium`，不依赖各自默认下载目录。ZIP 排除 `node_modules/.bin`，因此 build.py 必须生成可执行的 `runtime/bin/playwright` 包装，直接调用冻结的 `node_modules/playwright/cli.js`；`runtime/bin/agent-browser` 仍保留。解包后 PATH 中这两个 bin 文件和浏览器包装都应存在。 |
| `scripts/runtime.py::prepare` 在本机缓存 lock 后，由 `scripts/agent_support.py::browser_executable` 供 variant 取路径 | 现有 prepare 只装 agent-browser Chrome，browser_executable 的 fallback 只 glob `.agent-browser/browsers`。实施时本机也按 lock 对应的 Playwright 版本安装 Chromium，并按 Playwright 实际安装结果解析路径；仅改 Docker 会使 macOS 开发运行找不到共享浏览器。显式 `BROWSER_EXECUTABLE_PATH` 与已有 `AGENT_BROWSER_EXECUTABLE_PATH` 指向同一二进制或 Linux 包装，运行测试时不需共享 browser context。 |
| Braid 成员 clone 中创建 `checks/node_modules -> $BROWSER_CHECK_NODE_MODULES`，运行 `playwright test --config checks/playwright.config.ts` | `@playwright/test` 从检查文件及 config 所在的 `checks/` 向上查找 `node_modules`，链接到已冻结的 runtime/node_modules 才能 import；PATH 中有 CLI 只解决命令发现。config 的 `launchOptions.executablePath` 必须来自 `BROWSER_EXECUTABLE_PATH`，并实际发起浏览器。`scripts/braid_runtime.py::initialize_repository` 给原始应用仓库排除 `node_modules/`，但该本地规则不随 Braid 的独立 clone 发布。工具技能示例应在创建链接前写好应用自己的 `checks/.gitignore`，其中一行 `/node_modules/`；已有应用忽略规则已覆盖时沿用。这样 `git add -A` 不会误收绝对链接，检查源码和必要配置仍可提交。无需给通用 Braid clone 加 Node 专属规则，也不让最终导出暗删已提交源码。 |
| 在已有冻结应用上取得第一次真实反馈 | 用新的冻结 runtime 和该应用的确切 commit，选择非 3000 端口启动；确认 ZIP 内 `playwright` 包装、检查文件 import、同一 Chromium 启动、失败 trace 路径和退出码，再用实际需求判据写/跑一条完整检查。记录服务入口、应用 commit、检查源码和结果；失败分清工具链加载、浏览器启动、应用行为。需要下一次生成时才比较写检查成本和最终 V&V 质量，不能把单次 API 存在或 browser-operator 报告当有效反馈。 |

已收敛的普通应用路径：`checks/.gitignore` 中 `/node_modules/` 随检查源码提交，链接在每个执行 clone 临时建立；不要依赖运行时 `copy_application`/最终导出替已提交的绝对链接清场。`runtime/bin` 的 wrapper 使用可移植相对路径，ZIP 内不保存构建容器的绝对浏览器路径。

## 实施记录

已增加 @playwright/test 1.61.1、便携 playwright 入口，统一配套 Chromium 的构建/本机定位；主会话与 executor 接入 browser-checks。
npm 锁新增三个所需包，原有版本未变；沿历史不自动解析 peer 的依赖集合，ci 和锁更新均使用 legacy-peer-deps，避免此次顺带引入另一个 Pi SDK 依赖树。
真实应用检查将在 WSL 执行，原 Windows Docker endpoint 不可用，使用现有 WSL Docker。未更改全局 context、没有新建 OS 沙箱。
