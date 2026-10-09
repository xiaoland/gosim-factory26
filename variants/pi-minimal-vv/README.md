# pi-minimal-vv

独立的原生 Pi Harness：主会话默认 GLM-5.3-Flash，`--model glm-5.3` 可选择本轮另一个主模型；advisor 为 Kimi-k2.7-code，AI E2E 保持 GLM-5.3-Flash。主会话与 advisor 按需读取独立的 svc-task-packet、svc-specs、svc-verification；主会话另提供 tester.army/e2e。生成、advisor 与 AI E2E 共用调用方注入的 API key 与端点；模型连接不写入源码；Context7 与 Exa 使用调用方显式选择的私有工具凭据输入。供应商次序由调用方传入的[跨 variant 模型配方](../../materials/model-recipes/README.md)选择并冻结，variant 不从 catalog 默认推断选路。费用模式和执行范围由所属任务授权；本地自费 API 不默认设置人为费用、时长或 idle 停止阈值。

在官方既有应用的 output 根增量工作，不清空或重建基线。每次启动在 `.factory26/pi-minimal-vv/runs/<随机run-id>/` 创建独立 HOME、原生会话、工具状态与证据；清理仍检查整个应用工作区的进程，但清理证据写入新 run。旧 `.factory26` 和根 `process-evidence` 不继续使用。 必要机械恢复可由执行负责人显式设置 `FACTORY26_PI_RESUME_RUN_ID`，仅复用已核实 variant、主模型与 session 文件的本轮原生会话；旧 result 和恢复身份另存，应用不回滚。正常启动仍创建新状态。该接口保留持久会话与应用，错误后的既有清理会结束本 run 服务和 E2E daemon，不能据此声称恢复了完整进程 checkpoint。构建时保证原生后台 Bash 的非交互错误终态不等待未完成任务，并将实际成员哈希记录在 runtime 身份中。

原生 settings 显式启用 `compaction.thresholdTokens=245000`，沿公共 Pi 自动压缩路径消费。实际触发线取 245000 与模型容量减默认 reserveTokens=16384 的较小值，keepRecentTokens 保持默认 20000；这是上下文压缩，不创建新会话。该配置用于之后启动的材料，不修改已经运行的冻结包。

从现有 Linux runtime 派生纯 Pi 材料，保留冻结 e2e addon，删除 Braid 可执行入口；不预置应用源码、参考答案或业务原生依赖。main.py 拒绝 macOS 执行，Linux 的短 TMPDIR alias 指向本 run 的证据目录。

生产包可从冻结 runtime 使用 `tooling/scripts/runtime.py slim-linux` 派生浏览器精简材料。存在 `bin/browser-exec` 时，main 通过该入口使用平台浏览器或按需安装的浏览器；显式非空 `PLAYWRIGHT_BROWSERS_PATH` 保持原样（含 Playwright 特殊值 `0`）；只有未提供时使用本 run 的可写缓存目录。owned E2E recipe 固定实际传入的缓存路径，后续 shell 不改变连接环境。E2E 客户端保留独立 SDK，由 SDK 安装其兼容浏览器，不再硬绑定包内 `e2e/browsers`。旧离线 runtime 仍可使用 `bin/chromium`。采用精简材料前必须同时核对主 runtime 和 E2E addon 的浏览器目录，不能只裁掉一个 Chromium 入口而保留另一整份浏览器。

原生 Pi 以 `PI_OFFLINE=1` 运行，因此 Linux runtime 必须预先包含 `bin/fd`，供原生 `find` 使用；构建缺少该依赖时直接报错。`bin/rg` 只满足原生搜索工具，不能替代 `fd`。工具二进制及上游来源随 runtime 身份冻结，不依赖运行时下载。

调用方可通过 `TASK_CONTEXT_FILE` 提供 bench 冻结的附加任务材料。配置后必须是可读 UTF-8 文件，main 在模型调用前核实并在最终 prompt 中引用其路径；未配置保留原入口。任务专属正文由 bench 持有，variant 不内置。GLM-5.3 按本轮实际后备 API 的文本能力声明，原生 Pi 会明确提示图片未发送；不能仅因 read 工具支持图片就假定模型连接支持 `image_url`。

官网装配可给 `build.py` 显式传入 `--task-context-config <bench task.json> --task <task-id>`。构建复用公共 context helper，将材料与来源回执冻结在包内 `bench/`，以薄 `main.py` 绑定 `TASK_CONTEXT_FILE` 后执行原入口 `agent-main.py`；官方需求文件保持独立，不依赖官网额外注入该环境变量。未选择 context 参数时构建保持原入口。正式采用历史已冻结版本时，应从该版本与明确机械 overlay 装配并核对成员哈希，不能用当前工作树重建来冒称历史版本。


新运行只有一个原生 Pi 实现会话；公开需求与基线 schema/data 的初态核对、增量实现和验收都由该会话负责，不生成独立准备会话或阶段交接文件。核对必要初态及必须不存在的关系，按需执行兼容迁移与一次性数据准备，不预置用户动作结果，不在启动时盲补已被删除的关系。底层初始化、数据准备与业务就绪保持单向依赖，验收使用独立副本。

当前入口只恢复同一模型的单会话原生记录，并拒绝重新生成已经自然完成的 run。旧两阶段 run 的 stages.json、子会话和归档保留原身份；当前入口明确拒绝它们的原生恢复，需要使用对应冻结 Harness。不能把阶段产物或旧子会话当作新单会话检查点。

原生 E2E 的 handle 与清理方法、其他执行器的直接 MCP 接口方法归共享 [E2E 技能](../../materials/skills/e2e/SKILL.md)及其交互参考；本 variant 仅覆盖 runtime-setup 中的独立项目路径。原生运行的独立 MCP daemon 不意味着改变环境后仍复用同一 E2E server。交付验收继续使用 TypeScript runner，MCP 用于交互探索与排障。

原生 `e2e` 工具使用共享 `materials/e2e/owned-client.mjs`，open 返回绑定固定连接 recipe 的 handle，跨 shell 的 call/discover/close 复用现有 mcporter daemon。默认配置不再暴露裸 e2e alias；TypeScript runner仍沿 e2e-cli。session状态和完整原始输出归本run，变更配置、失去服务器或已关闭handle明确失败，不自动重开。源码版本不兼容的历史handle不能接续为浏览器检查点。

主会话通过 `FACTORY26_SUBAGENT_CATALOG=1` 启用公共 pi-subagents catalog hook：在现有 system prompt 中追加当前可执行角色的名称与 description，供调用前发现；禁用角色、内置角色禁用配置和子角色能力边界沿用原生目录规则。目录不内联角色或技能正文；调用 advisor 后仍按角色文件加载独立指令和所选技能。此接线需要含 catalog-hook 补丁的当前公共 Pi runtime；旧冻结包不会因此更新，也未据此证明实际委派触发有所改善。

装配器在创建暂存目录前核对公共 Pi baseline 的锁、补丁顺序/内容、最终目标文件与 managed 模块 SHA。缺失或不匹配时直接拒绝，不再在 variant 暂存目录补写 PBB 代码；catalog 开关也不能升级旧 runtime。请使用当前公共 producer 的产物，source 保留实际 baseline 身份与 standalone 执行模式。


主会话与 advisor 加载共享锁定的 @ff-labs/pi-fff 0.11.0（tools-only）、@upstash/context7-pi 0.1.2 及从 I15 复制的原生 Exa 扩展。原生扩展由入口显式选择，不自动加载基线或 HOME 中遗留扩展。FFF 提供 `fffind`、`ffgrep`，保留原生 find/grep；Context7 提供 `resolve-library-id`、`query-docs`，Exa 提供 `exa_search`、`exa_contents`。Context7 的 `context7-docs/SKILL.md` 从已补丁 runtime 单独打包，目录仅发现名称、description 与路径，正文按需读取。mcporter 配置不再注册 Context7 或 Exa；owned E2E 的独立 daemon 接线保持原合同。

完整封包使用 `build.py --tool-env <私有双键dotenv>`，复用公共 `package_agent.write_tool_credentials` 将 CONTEXT7_API_KEY 与 EXA_API_KEY 写入 Git 忽略制品的 `.private/tool-env.json`（目录700、文件600）。凭据不进入源码、README 或身份回执；显式执行环境优先，入口在模型调用前验证两键存在。使用组件生产时沿既有 private tool input/execution_bootstrap 通道注入相同两键，不增加密钥通道。主入口显式 `--fff-mode tools-only`，并用继承的 `PI_FFF_MODE=tools-only` 保持 advisor 相同模式；子角色不传未知 CLI 旗标。FFF 原生运行库属于所选工具，必须保留；插件不会带回浏览器、开发缓存或应用依赖。


自实现 Pi 扩展的维护源归 [materials/pi-extensions](../../materials/pi-extensions/README.md)，variant 不保留源码副本。装配器将所选 canonical 文件复制到交付 extensions/ 并记录源字节身份；原生入口与相对工具引用仍使用交付路径。当前历史冻结包保持原样，新的公共组件缓存与冻结 overlay 均纳入所选扩展及选择器身份。


advisor 的目录描述与指令明确交付独立判断、推荐路径及关键不确定性；主会话负责实施，没有 implementation worker 时自行完成。职责约定不构成权限隔离：advisor 不设置角色专属工具 allowlist、capability ceiling 或额外 sandbox，保留原生工具、既有扩展与自主调查能力，模型仍为 Kimi-k2.7-code。该源码修正不会热改历史冻结包或官网运行。


官方交付入口在 bench 上下文绑定完成后包装执行，参数、准备、生成、API、清理或后处理的可捕获错误仍最终返回进程退出码 0，以允许平台进入评测。这不代表生成成功：实际 Pi 退出码和 terminal 保存在 result.json，分阶段具体错误及 traceback 保存在 execution-errors.jsonl，最外层 entry-outcome.json 分别记录 generation_succeeded、execution_succeeded 和平台退出码。早期错误尚无原生目录时写入输出目录的 entry-failures；记录失败仍输出原始 traceback。直接调用源码 main.py 及宿主 build.py 仍保留严格的参数与生成失败退出，本地消费者不能仅用官方包装入口的 0 宣称生成成功。SIGKILL、解释器无法启动及操作系统强制停止无法由 Python 兜底；返回 0 也不保证平台一定完成评测或有功能分数。

辅助遥测、日志保存和清理失败不覆盖真实生成结果，并尽力继续独立收尾。workspace 清理在 KILL 后最多等待 5 秒确认 cwd 归属退场，避免把信号已发送误当内核已经退出；仍未退场时保留具体 PID 身份错误，由官方入口记录而不阻断评测入口。
