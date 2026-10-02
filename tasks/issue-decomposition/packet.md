# 根 Issue 明确要求需求拆分

2026-09-25 新增定向分析：用户要求“分析 https://arc-bench.com/runs/7207a7fe0845 的 1/100 得分”。本次只读采集该手动重试 run 的完整评分、部署与执行日志、可取得的应用和过程证据，逐类定位首阻断点，再区分已证实原因与证据缺口；不修改 Harness/应用、不重跑或创建实验。证据保存在 `runs/issue-decomposition/20260925-hackathon/analysis/7207a7fe0845/`，结论回写本任务。

状态：指引已修改并冻结提交；官网原 GitHub 生成失败，用户手动重试 GitHub `7207a7fe0845` 已取得 1/100 并完成定向分析。2026-09-25 23:23（北京时间）核实 Sheet `17bffdd4a8b0` 已 PAUSED，生成未完成、评测尚未开始；暂停前长期停在生成应用的自测输出管道，定向调查已完成。
本轮依据用户提出的新实验方向，明确任务提示与验证问题。

前一轮入口修正版完整 Lite 为 49/66，两题只有根 Issue，没有 PR、子 Issue 或原生子 Agent；结果见 [前轮报告](../hackathon-team-baseline/results/interface-official-lite.md)。
用户提出在根 Issue description 明确要求拆分，可按每项需求或紧密内聚的需求组建立 Issue。
本轮允许在具体参赛任务中明确要求协作，作为对“提供能力但 Agent 没有采用”的主动干预；这不改变 Braid/SVC 的通用产品职责。

[设计](design.md)保存候选任务文字、技术落点、验收判据和实施准备顺序。
当前推荐按内聚需求组拆分；分组与负责人由 Agent 选择。
根 Issue description 由 `variants/pi-team-mixed/run.py` 的 prompt 构造，再通过 `request.prompt` 传给 Braid；落点已核实。

本次实验以现有 Linux runtime 重新打包当前 variant。用户明确要求直接在官网运行 Hackathon bench 并勾选参赛，本轮不再先跑 Lite。保留冻结 ZIP、官网两题 run、得分和原始证据，完成后报告并停止本轮实验。

用户进一步确认工作流程为产品设计 → 技术设计 → 实现计划与排障 → 生成 → 验收，并要求确认生成与验收在 PR 中完成的指引是否存在于系统提示词。
已核实最新运行归档的 physical/instructions.md：只有 GitHub 式操作、对象事实和 SVC 导航，缺少明确工作流程和 PR 实施约定。SVC 仅提供按需方法，不能代替这条参赛工作约定。
补充方案是在当前 variant 的成员 instructions.md 恢复简短工作约定，经既有 profile.user_instructions → Braid 稳定指令 → Pi --append-system-prompt 接入；Braid 通用工具说明与 SVC 方法正文保持各自职责。候选文字与具体边界见 design.md。
这意味着后续候选实验同时改变需求拆分要求和工作流程说明，结果解释须记录两项，不声称仅测量拆分的独立效果。

2026-09-25 用户指示：“同意，你可以开工；然后我们就直接在官网用这个 variant 跑 hackthon bench（勾选参加比赛）。”这授权修改当前 variant、构建并向官网以 `official_evaluation` 模式正式提交 Hackathon 的 GitHub 与 Sheet 两题。旧 Lite 49/66 只作背景参考；正式题与 Lite 不可直接比较。提交前确认包中只有本次指引差分且包含同一已用 runtime，不顺带改变模型或 Braid/SVC 源码。

已在 WSL 独立目录 `runs/issue-decomposition/20260925-hackathon/` 复用前次 build-input 和 Linux runtime 构建。包 SHA256 为 `59d8639c9566afca6ba439a64d73d5a18148408f76f7ee890fbd8d7902669e81`；包内 `run.py` 与两份成员指引均与本机当前源码哈希相同。官网 journal 位于本机同名目录的 `official/`，snapshot 为 `43b59da83877`，提交历史回读 `credential_mode=official_evaluation`。GitHub run `caf2d2f23e13` 已启动，Sheet 等控制器按顺序创建；控制器每 180 秒查询一次。

需核对平台返回字段：GitHub run 详情当前显示 `billing_mode=self_funded`，但 submission 历史显示 `credential_mode=official_evaluation`，且本次 POST 未附自带 key。先观察实际生成与比赛额度/终态记录，避免仅凭一个字段推断结算路径。

首次终态核查：GitHub run `caf2d2f23e13` 在生成阶段 `FAILED`，没有执行测试；平台记 `score=0`、`passed_count=0`、`failed_count=0`、`total_tests=0`，不能当作有效通过率。原始 stderr 指向 `support/braid_runtime.py:export_delivery` 的 `tarfile.ReadError: end of file header`，发生在导出 `delivery_commit` 时。平台 commit-history 返回 `workspace_unavailable`，现有官方证据不足以确认该 commit 的树内容和 Braid 之前的对象行为。Sheet run `17bffdd4a8b0` 已由原控制器启动，继续等待它的终态。

GitHub 终态后 `/teams/me` 中 Hackathon 比赛余额从 500 降到 493.788515 CNY，差额 6.211485 与 run 返回的 token cost 数值相同。因此实际扣用了比赛额度；run 的 `billing_mode=self_funded` 与提交和预算证据不一致，暂作为平台字段异常记录。

用户手动对同一 submission 的 GitHub 题重试，新增官网 run `7207a7fe0845`，已核实其 `submission_id=43b59da83877`、`requirement_id=hackathon--github`，当前运行中。原 journal 仍只管理最初 GitHub 和 Sheet 两条 run，不将手动 run 改写进其身份，也不重复创建。终态监控已纳入第三条 run；重点比较第一次导出错误是否复现。

本机 `competition run-all --interval 180` 持有原 journal。2026-09-25 用户要求停止使用 scheduled task，改由 `gpt-5.6-sol / low` 子 Agent 通过脚本每 15 分钟监听。
已核实 `factory26-hackathon` 为 `PAUSED`，`/root/hackathon_monitor` 已确认接管三条原 run。
等待脚本为 [monitor.py](monitor.py)，观测原文位于 `runs/issue-decomposition/20260925-hackathon/monitoring/`；首次接管看到原 GitHub FAILED、Sheet 与重试 GitHub RUNNING。
监控本身只读，不创建或重试 run；控制器恢复仍须先核对 journal pending 和远端身份。
全部终态后向主 Agent 返回结果，汇报完整实验；下一轮能力设计独立保存在 [Hackathon 能力选择](../hackathon-capabilities/packet.md)。

## 手动重试 GitHub 的定向分析

分析见 [7207a7fe0845](results/7207a7fe0845.md)。官方计数为 1 通过、99 失败，生成和部署完成；内部 Braid 实际因 Pi SIGKILL 进入 blocked，Factory 随后导出集成分支已有的 WIP commit `d9f880a`。38/38 个交付文件哈希核对相符。

本轮实际建立 6 个子 Issue、4 个 PR，并运行 GLM/DeepSeek；4 个 PR 均未合并。根 Agent 与认证 PR 重复实现框架，合并失败后 Issue #2 仍被关闭；其恢复会话又跨入根 worktree 提交在制代码。最终前端只注册首页与账号路由，其余五组功能覆盖 85 个需求场景。隔离副本浏览器确认登录可用，但新建仓库、组织列表和搜索全部进入前端 404。

已下载官网 template bundle，包括 `.factory26` 原生轨迹与 Braid 数据库；commit-history 接口不可用不代表归档不可取。官方逐例结果仍缺失，不能确定唯一通过的场景或逐项给 99 个失败定责。SIGKILL 的来源也未证实。本次未修改源码、未重跑 benchmark；后续改动方向与证据边界在分析报告中呈现。

## Sheet 长时间运行调查

用户要求“这个 run 已经运行了很久，请你看看什么情况”。当前状态与原因见 [Sheet 调查](results/17bffdd4a8b0-status.md)。平台记录暂停原因是用户请求，当前费用 ¥18.734651，尚无评分。

用户澄清“我是手动挂起的，我要你分析的是为什么这么久还没有结果”。调查重心为暂停前的耗时与无结果机制，手动暂停只作背景。补查确认第一次后端自测从 19:58:52 等到 20:51:19（52 分 27 秒），根 Agent 杀掉残留进程后立即返回持久化失败断言；根 Agent 未修复脚本清理逻辑，20:53/20:56 两个会话再次陷入同类等待。冻结 Pi Bash 默认无超时，本次调用也未设 timeout；外层 logged 无期限等待 Braid 结束，因而始终未执行后续导出交付。详细时间线与冻结源码证据已同步到现有调查报告。

根 Agent 与后端 Issue #3 分别在北京时间 20:53、20:56 停在 `api.smoke.js | tail`，到 23:15 的 RUNNING 观测至少超过两小时无新工具结果。原有应用自测最后重启后端后，finally 清理的是旧进程，新进程继承输出管道导致 tail 等不到 EOF。本地对同一脚本做 10 秒限时隔离复现，确认断言失败后测试主进程退出、后端子进程仍存活、管道不结束；复现进程已清理。

用户进一步质疑 Pi 的执行职责。核实冻结 Pi 0.85.1 已有 timeout/abort 进程组终止，以及直接子进程退出后的输出空闲保护；本次 shell 仍等待 tail，未发生 exit，且调用未传 timeout，因此这两条保护都没有触发。当前证据指向无人值守接入未落实命令期限，不能表述为 Pi 已启用的超时或退出保护失效。详细职责分析补入现有 Sheet 调查报告；未修改源码。

用户继续提出运行环境假设。已补查：普通 macOS shell 无需 Pi/Braid/官网容器即可复现管道悬挂；最后的持久化断言检查的是此前被测试自己删除的工作表内容。临时应用副本只增加观察输出，确认重启前 API、磁盘及重启后 API 均为同一空白 Sheet2；原测试在不接 tail、输出到文件时 0.678 秒返回失败，残留服务器由外部清理。平台专属故障目前证据较弱，无人值守调用方式的放大作用已有证据；不报告无对照依据的百分比。证据与局限已补入原调查报告，未改源码或远端。

本次只读调查并复现生成应用自身的脚本，没有修改代码或远端，没有恢复/取消运行。恢复前需决定如何处理自测进程清理及工具超时；最后断言的错误前提已经核实。既有只看终态的监控不会把 PAUSED 当作完成。

## Sheet 调查后的修复建议（按用户修正，待实施复核）

用户问“那应该怎样修复呢？”后，进一步明确：“我更建议超时之后通知agent而不是直接杀死进程”。当前方案据此改为达到等待阈值后通知 Agent，并保留运行中的命令；撤回自动填充 Bash 硬 timeout 的提案。上述讨论授权方案修订，尚未授权源码修改或恢复实验。

用户随后建议优先安装现有 background 插件，或补充长任务使用异步 Bash / bg task 的提示词。当前选型方向调整为优先复用合适插件；只有核实插件没有覆盖必要行为时，才考虑补项目指引，自行包装执行器也仅作为确认现成能力缺口后的备选。已询问具体仓库/包名，尚未收到标识，因此以下为候选比较，不代表用户指定了某个包或批准安装。

2026-09-26 只读查看四个候选的 README、package.json 及关键源码，冻结所查 commit 与文件在 `runs/issue-decomposition/20260925-hackathon/analysis/background-plugin-survey/`。发现同名能力不能互换：

| 候选 | 已核实能力与当前限制 |
| --- | --- |
| [Jawfish/pi-background-tasks](https://github.com/Jawfish/pi-background-tasks/tree/2db0893301130de58b099bb87fe3ec77d41273d5) | `background_task` 提供启动、状态、日志、停止、一次性输出/退出/无输出观察；`completionPolicy: wake` 才会主动推进模型，默认 notify 仅通知 UI。普通 Bash 不会自动转后台，需模型主动调用；无输出观察也不等于总运行时间阈值。 |
| [patty-io/pi-patty-bg-tasks](https://github.com/patty-io/pi-patty-bg-tasks/tree/697010eaa88ca1b861fce554a149a5f019a7439a) | 提供 Bash 自动转后台及显式 bash_bg/jobs，但 `src/tools/bash.ts:213` 在 nonInteractive 时直接跳过定时转后台；`detectNonInteractive` 将 stdin 非 TTY 判为非交互。当前 Braid 通过管道以 RPC 启动 Pi，故不能按 README 的默认 120 秒宣传推定此能力在本项目生效。 |
| [SakikoTogawa233/pi-background-tasks](https://github.com/SakikoTogawa233/pi-background-tasks/tree/24240b3f0ee001dac520fadc3c882280969eee7a) | README 将前台自动交接限定为 TUI；源码也只在非 nonInteractive 分支注册交接计时器。3.1.0 的声明兼容范围截至 Pi 0.84.x，不包含本次冻结的 0.85.1。显式 bg_run 与自动接管需分别评估。 |
| [sshkeda/pi-background-bash](https://github.com/sshkeda/pi-background-bash/tree/4948b7db3af931de1307dbcb52c48b48d3485b6c) | Bash 覆盖实现支持显式 background 和默认 30 秒自动转后台，所查自动交接路径未按 TUI/RPC 分支限制；另有三个 Git 来源依赖，完整依赖可获取性、冻结构建及 RPC 完成通知还未验收。当前不能直接承诺安装即用。 |

选型要同时覆盖“预期长任务主动后台运行”和“普通 Bash 意外变长后归还控制权”。仅添加提示词能改善前者，不能保证模型总能预判自测挂起。实际接入要把固定版本包纳入 runtime，更新显式 `--extension` 加载、Pi 内部角色的扩展及工具列表；当前 launcher 使用 `--no-extensions`，仅在开发机执行全局安装不能让官网包自动使用插件。无关的子代理编排能力不作为此次引入目标。

用户明确修正：“我们自己补提示词的前提是这些插件自己没补，我们不应该造成重复。”撤回通用后台任务提示词草案。2026-09-26 核实四个候选均已声明 `promptSnippet`、`promptGuidelines` 和工具描述：Jawfish `index.ts:1296` 覆盖主动后台、wake/notify 区分、避免轮询及增量日志；Patty `src/tools/bash.ts:70` 覆盖长任务后台和 jobs 查询；Sakiko `src/extension.ts:690` 覆盖完成后自动接续、避免等待式查询及日志读取条件；sshkeda `extensions/background-bash.ts:974` 覆盖构建/测试/服务后台执行、意外超时自动交接、不重复启动及终态处理。这些插件的等待和通知策略有差异，统一外加一段泛化指引还有可能冲突。

同时核实冻结 Pi 0.85.1 的 `dist/core/agent-session.js:_rebuildSystemPrompt` 按有效工具收集两类字段，`dist/core/system-prompt.js` 将工具指引加入默认系统提示词；当前接入使用 append 路径。因此接入审查先确认插件实际加载、角色工具列表开放对应工具、模型实际获得原生指引，再只检查交付收尾等项目约定是否仍有缺口。不能用重复提示词掩盖插件未加载或工具未开放的问题。

行为要求是：命令达到等待阈值后，工具返回“仍在运行”，附带稳定执行标识、累计耗时、最新输出及日志入口，将控制权交还模型。Agent 可以查看输出、继续等待同一执行，或明确停止它；继续等待不得重启命令。等待阈值先沿用 300 秒作为候选值，未作为用户已确认的参数。进程自然完成时记录唯一终态和退出码，交回真实结果；时间阈值本身不终止进程、不伪造失败。显式停止、用户取消整个运行或会话关闭按相应生命周期清理进程。原生显式硬 timeout 与软等待阈值保持不同语义，不自动添加硬 timeout。

冻结 Pi 0.85.1 的 Bash 原生调用会等到命令退出；它的 `timeout` 会杀进程。扩展 `sendMessage(..., {deliverAs: 'steer'})` 也要等当前工具批次结束后才进入下一次模型调用。因此单独加定时通知无法唤醒被当前 Bash 调用阻塞的模型；实现必须先让工具以“仍运行”结果返回，并保留执行、输出和取消控制。原先仅修改 `event.input.timeout` 的几行实现不满足用户的新要求。

针对用户“技术上可能吗”的追问，已静态核实冻结包的公开导出包含 `createLocalBashOperations`、`createBashToolDefinition` 与 `createBashTool`。底层 exec 接受输出回调与 AbortSignal，返回等待命令退出的 Promise；其 finally 在该执行 Promise 完成后才解除子进程跟踪。Agent 核心在外层工具返回时只停止接受该调用的增量更新，没有无条件终止 OS 进程的动作。因此可在扩展层持有一次命令执行、输出及取消控制，让外层工具只等待一个时间窗口后返回句柄；后续 wait 复用同一执行。原生 Bash 的 command/timeout 两参数不能直接表达这一行为；优先由合适的既有插件提供状态化返回/查询/续等，确认缺口后才考虑复用 Pi 底层执行能力作必要包装。

该可行性结论基于源码与公开扩展契约，尚未完成端到端运行验收。实现需将长期输出保存在执行记录中，不能继续依赖已经返回工具的 onUpdate；取消句柄归受管执行所有，普通工具返回不触发取消，同时用户取消和会话关闭仍必须清理。根成员当前通过 Pi RPC 运行，内部子 Agent 的结束路径也须纳入生命周期验收，防止执行记录被留在已结束的会话中。

加载范围包括根会话、全部 Braid 成员会话及 Pi 内部子 Agent。当前 `run.py:native_files` 可接入主会话 launcher，但内部角色 frontmatter 的 `extensions` 显式为空，因此实施时必须同时补齐内部角色接线，不能假定父扩展自动继承。被动 observer 保持观察职责。达到阈值时通知一次；后续等待由 Agent 选择，完成时再交回结果，不用定时重复消息替代执行状态管理。

当前生成应用的定向修复仍是：用当前后端进程引用清理重启后的服务器，等待退出后再删除临时数据；持久化验收以重启前的有效快照或独立保留的测试工作表为依据。直接运行测试并让 Pi 收集输出；必须使用管道时保留测试退出码，避免 tail 的成功退出掩盖断言失败。上述应用修复用于处理当前产物，不作为通用 Harness 对生成代码的改写规则。

实施后的验收需在获授权的实际运行及生成应用验收中核查：超过等待阈值时进程仍存活，模型确实收到运行状态并能调用下一工具；继续等待对应同一执行；自然完成、显式停止与整体取消都正确收尾且结果不重复；三层会话均加载策略。遵守不新增 Factory 基础设施测试的约定。新包与旧 run 身份分开，本地修复不会自动更新已暂停 run；恢复旧 run 或以新包重新实验另行确定，当前保持暂停。

## 社区日常 Pi 配置调查

用户要求查找较高赞的 Reddit、X 或技术博客日常配置，用于判断当前 Pi 能力是否过于精简。2026-09-26 只读调查取得以下一手材料；Reddit 票数是搜索索引快照，不是实时排名，个人体验也不等于 benchmark 增益。

| 公开配置 | 可借鉴内容及适用边界 |
| --- | --- |
| [Sharing my Pi setup](https://www.reddit.com/r/PiCodingAgent/comments/1u4nr9k/sharing_my_pi_setup/)，2026-06-13，快照 +354；[配置仓库](https://github.com/abhinand5/pi-setup) | 日常配置包含上下文用量分析、变更审阅、MCP、权限及界面扩展。可参考配置组织和上下文诊断；交互 UI 并非无人值守运行所需能力。 |
| [My powerful Pi agent Setup](https://www.reddit.com/r/PiCodingAgent/comments/1t41thp/my_powerful_pi_agent_setup/)，2026-05-05，快照 +192 | 以 fork 隔离探索上下文、observational memory 保留长会话信息，辅以 advisor/reviewer 和代码检索。其[后续异步配置](https://www.reddit.com/r/PiCodingAgent/comments/1w9e6zo/my_pi_agent_setup_part_2_native_async_operation/)公开 system/settings，并明确没有 benchmark 对照。可作为上下文管理候选，不据此重复添加编排器或断言提分。 |
| [Armin Ronacher：Pi: The Minimal Agent Within OpenClaw](https://lucumr.pocoo.org/2026/1/31/pi/)，2026-01-31 | 本人日常使用的 todos、独立审阅分支、浏览器技能和按需扩展；[agent-stuff](https://github.com/mitsuhiko/agent-stuff)提供实现。值得参考如何减少主上下文中的工具与探索噪声。 |
| [DeepakNess：Setting Up and Using the Pi Coding Agent](https://deepakness.com/blog/pi-agent-setup/)，2026-08-14 更新 | 日常模型搭配、pi-web-access、pi-vision-handoff 及简短项目/全局指引。可对照检索和视觉能力，不照搬模型、订阅、交互审批或界面偏好。 |

当前 variant 已有 Braid、pi-subagents、角色指令、SVC/领域技能、agent-browser、视觉角色，以及 exploration-tools 通过 mcporter 接入的 Exa、Context7 和 Handsontable 文档服务。来源为 `harness/npm/package.json`、`variants/pi-team-mixed/run.py` 和 `harness/skills/exploration-tools/`。所以“缺少日常用户的整套增强”应进一步分解：当前直接证实的缺口是普通 Bash 意外长时间运行后的受管交接；检索、浏览器、视觉与子 Agent 已有对应能力，需按有效接入和实际使用评估，不能按是否安装同名社区包判断缺失。

推荐顺序为先完成后台执行插件的 RPC 与生命周期选型；其次只在轨迹显示事实因压缩或探索噪声丢失时考虑上下文管理增强。社区整包、第二套多 Agent 编排、TUI 美化暂不作为参赛 Harness 改动。本轮仅修订调查与候选方案，没有安装插件、修改源码或运行新实验。

## pi-team-mixed 后台执行开工

2026-09-26 用户明确要求：“是的。我们来给pi-team-mixed这个variant补上后台执行的缺口吧。”授权为当前 variant 接入可在 Braid RPC 中工作的受管 Bash 后台执行，补齐主成员与 Pi 内部有 Bash 权限角色的加载、固定依赖和运行路径；继续遵守超时交还 Agent、进程不停的既定语义，不恢复旧 run、不新跑 benchmark、不提交。

实施调查发现原 sshkeda 包的 `pi-context` Git 依赖无法公开取得；Patty 与 Sakiko 的普通 Bash 自动交接都在非交互模式关闭。已发布的维护分支 [pi-background-bash 1.0.5](https://github.com/mowenroot/pi-background-bash)移除了无法取得的依赖、修复 headless 中的失效 context，并保留默认 30 秒自动转后台及终态回传；npm 锁定包和两个公开 codeload 依赖。其工具自带提示词，无需另写使用方式。项目级补充只要求交付或验收所依赖的后台命令取得终态和退出码后再宣告完成，并清理已用服务。

接入还需处理两处运行边界：`pi-subagents` 的角色 frontmatter 写 `extensions: ""` 会关闭正常扩展发现，因此有 Bash 权限角色必须显式加入插件；打包过程排除 npm `.bin` 链接，所以 `pbb` 需从真实 bin 文件建立 variant 自有启动器。插件 CLI 假定 `pi-lane` 位于插件包内，但 npm 锁将依赖提升到顶层，运行环境应显式给出 `PBB_PIL_BIN`。Braid 对 Pi 后台自然唤醒产生的后续回合是否计入当前任务尚未经过实际模型运行验收，因此不把插件作者的 headless 验证直接等同本 variant 的端到端结果。

已修改 `harness/npm/package.json` 与锁文件，固定 `pi-background-bash@1.0.5` 及带完整性摘要的 `pi-lane`、`pi-pending`；`variants/pi-team-mixed/run.py` 为两名 Braid 成员显式加载插件，为八个有 Bash 权限的内部角色写出扩展路径，保留 vision 角色无 Bash 扩展；运行时创建 `pbb` CLI 启动器并指定提升后的 `pil` 路径。项目指引只补交付所需后台任务的终态确认，不重复插件工具用法。技术边界写入产品技术说明，操作方法写入部署说明。

静态验收：`npm ls --package-lock-only --depth=0` 确认锁定依赖，锁文件相比原版本仅新增插件和两个子依赖；下载的 1.0.5 包含声明的 `index.ts` 和 `bin/pbb.js`；`py_compile` 与 `git diff --check` 通过。依照本仓库禁用 Factory 测试和包 smoke 的约定，未新建或运行基础设施测试；也未启动新的模型/benchmark 实验。RPC 下后台完成触发的自发 Pi 后续回合，Braid 当前不作为其原 Braid 工作项回合继续追踪；指引要求必要后台命令在工作项结束前取得终态，后续真实运行仍须观测这个边界。
