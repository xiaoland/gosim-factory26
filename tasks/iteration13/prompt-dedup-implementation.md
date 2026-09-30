# I13 提示词来源审计与去重实施

2026-10-01。本批承接 [工具与提示词方案](tools-prompts-plan.md) 和用户复核的 [审计快照](tools-prompts-audit.md)。用户要求扩大审计范围，核心是检查同一 Agent 的组合输入是否重复；随后明确授权工具接线与 Factory/Braid 提示词开工。工具组单独负责 Context7、fff、Exa、凭据与加载，本页记录现有提示词生产者的审计、修正与证据。下一组 Braid 协作方法及 ARC requirements 技能尚未在本批实现。

## 起点与消费者

起点、源码和差分保存在 `runs/iteration13/prompt-dedup-20260930/`。Factory 起点 HEAD 为 `93202eaea5917d055bc6c106d2fa2f5864c9131b`，Braid 为 `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，均存在此前工作区修改。`factory-start-worktree.diff`、`braid-start-worktree.diff` 与 `start-source/` 区分起点和本轮增量；当前相对 HEAD 的全部差分不能当成本批成果。特别是 Braid `provider.rs` 的角色、CLI、事件和重建内容，以及原生 completion/model-exclusion/core/background 补丁已有先前修改。

审计单位是一次组合输入的消费者，包含 system、工具契约及消息。主 Issue/PR 各接收 Pi 基础 system；显式注册工具的 description/schema；工具 snippet/guidelines；Braid 对象角色、身份和通用协议；Factory profile 与运行条件；启用技能的名称、description、路径；原生项目指南；当前任务及接续消息。Braid Pi adapter 用 `--append-system-prompt` 传入 Braid 指引；它不是替换 Pi 基础 system。扩展的 before-agent 消息可能在后续轮次再提供恢复事实。

五种 child 采用相同的 fresh、append、关闭父项目指南及技能自动发现边界，接收本角色 body、该角色选定技能的发现信息、原生 child 边界、自己的工具和 task。父层 `subagent list` 消费角色 description，child 消费 body，两者不是同一份输入；相似职责说明不作全局删除。两 profile 的主正文相同，角色目录分别存在，模型绑定不同，也不能只为全仓少一份文本合并文件。保持技能文件独立，不内联 SKILL.md 或 references 正文。

| 消费者 | 单次输入的稳定来源与本批核对 |
| --- | --- |
| Issue 主成员 | Pi 基础能力、工具契约、Braid Issue 设计与实施交接职责、通用协议、当前成员身份、Factory recipe/profile、运行环境、主技能导航、项目指南、初始/接续消息。根 Issue 的 foundation 与需求分解由根 task 传入；普通子 Issue 没有根 task 的副本。 |
| PR 主成员 | 同一原生基础与 recipe，改为 PR 实现、预演、验收角色及当前 head 参数。分支参数与工作项编号属于身份事实。 |
| advisor child | 独立判断 body；7 个选定技能导航。主 profile 的 advisor 使用时机在主输入，child 的独立判断职责在 child 输入。 |
| browser-operator child | 页面操作 body与 agent-browser 读取入口；4 个技能导航。主 profile 的浏览器结果消费/整体验收职责属于主消费者。 |
| executor child | 明确目标内自主调查、设计、实现、反馈与交付；非简单任务首次/接续读取适用 documentation/task-packet，并复用父方资料；12 个技能导航。 |
| explorer child | 调查问题、用途、材料缺口与独立取证；同样有 documentation/task-packet 首次/接续入口；8 个技能导航。目录 description 不再限于窄型代码检索。 |
| vision child | 结合委派语境解读图片、保留可见观察与来源；1 个技能导航。必须委派参考图解读的政策由主 profile 持有。 |

表中技能数量对应本批第一次 prepare-only 的实际材料，早于工具组追加 context7-docs 的接线；它们不是最终工具整合包的数量。

## 已证重复、保留来源与修正

| 来源 → 消费者 | 重复或冲突 | 当前保留位置与理由 |
| --- | --- | --- |
| 两 profile 首段 + Braid `local_instructions` / Issue、PR role → 主成员 | CLI、通知、成员委派与设计/实施边界重复。 | Braid 持有通用操作协议与对象职责；profile 留 develop→main、候选验收与配方 advisor/vision 政策。当前成员身份、Issue/PR 编号及 head 保留作为参数。 |
| profile 评论处理/私有状态段 + Braid 协议 → 主成员 | 增量回复、无变化无需回执、私有工作状态、历史成果不镜像当前集成被多层说明。 | 移入 Braid 通用段一次，Factory profile 删除副本。CLI 的完整正文替换、单条 hide、根讨论 resolve、通知退订、指派和在途交接陷阱仍保留。 |
| profile 根基础责任 + 根 task → 根成员 | foundation 设计与关联基础 PR 在两处规定。 | 根 task 持有本次根责任；profile 不再给每个成员追加根职责。 |
| profile 原生角色教程 + subagent 工具 → 主成员 | list、执行/管理方式、后台等待与结果查询教程重复，explorer/executor 介绍过窄。 | 完整调用契约归原生工具；profile 留 Braid 名称与原生角色的跨层区别，以及恢复时使用原任务 ID、先取状态/产物的入口。实际角色职责由目录 description 和 body 各服务自己的消费者。 |
| `RUN_CONDITIONS` + 根 task / profile → 主成员 | origin 共享、pnpm/portless、后台服务、初始数据与服务停止重复。 | Braid 持有 clone/origin；运行条件一次保留平台环境、工具与服务/数据要求；根 task 删除工具/环境副本。Node 20.19.3、逐目录 npm 流程、120 秒、保留目录、3000、pnpm、portless、Vitest/Playwright/UnoCSS 与真实安装陷阱均保留。 |
| `BACKGROUND_COMPLETION_RULE` + bash description / metadata / wait description → 主成员 | background/service 自动切换、完成消息、等待与 service 停止多次注入。 | 删除 Factory 常量，原生 bash description 持有作业契约；`subagent_wait` 持有等待模式与不造 sleep 轮询作业的要求。服务名称、代理共享、端口与自检初态仍是配方环境规则。 |
| `ROOT_CHECK_MESSAGES` + Braid / documentation-task-packet 入口 → 根成员接续 | 根提醒重新给出完整整理方法和讨论处理 SOP。 | 提醒只提出本次检查与整理请求；稳定方法从原有所有者读取。提醒没有新事实不要求重复公开进度。 |
| subagent 默认 description + `SUBAGENT_TOOL_PROMPT_GUIDELINES` → 任何可委派 Agent | 单顶层 workflow/async、`runs.all` 有序数组、list、guide 等契约重复。 | 合并独有 list/model registry/未 await promise 约束到 description；snippet 只保留能力导航，删除默认 guidelines。Pi replace 模式跳过 snippet/guidelines 的 system 组装，所以不能把有效约束仅留在 metadata。inactive full/compact/custom 描述模式不额外改造。 |
| bash description + snippet + guidelines → 主/child | background/service/自动后台各重复说明；某些恢复和日志要求只在一层。 | 完整契约归 description；保留结果及退出码、不要重跑以等待、globalJobId 恢复、pbb 日志、交互 stdin 限制；snippet 只作能力导航，删除 guidelines。 |
| 原生 edit description / schema + snippet/guidelines → 主/child | exact、唯一 oldText、非重叠、禁止大段 padding 多层重复。 | schema 保留字段准确性/唯一性与非重叠契约；description 留 small oldText/不要大段不变内容；snippet 能力导航，唯一多处修改 batching 指南保留。grep/find snippet 删除再次声明的 .gitignore 行为，description 仍保留。read/write 独有工具选择指南不删。 |
| `injectOutputPathSystemPrompt` + `injectSingleOutputInstruction` → 配置 output 的 child | 同一输出路径义务被写进 system 与 task。 | 保留 system helper，删除 task helper 及前台、后台、动态并行调用。无写工具时完整返回内容、runtime 保存的分支保留；不改产物持久化或验收。 |
| observer 恢复总说明、每条 handoff 与 tool_result 补充 → 主成员后续输入 | 重复 status 教程、list/角色选择、任务归属、后台等待和 pbb SOP。 | 恢复行只含身份、状态、索引/产物入口；错误补充说明具体命名空间或 ID 不匹配事实。工具契约/profile 持有稳定操作入口。不改 watcher、事件与执行行为。 |
| 原生项目指南祖先加载 → Braid 主成员 | 独立 clone 位于 Factory 目录下时，Pi 一直向文件系统根爬祖先，会读入开发侧 Factory AGENTS。与参赛材料政策相冲突，并可能复制/引入多套开发指令。 | Pi `loadProjectContextFiles` 仅在 `BRAID_AGENT_RUNTIME=1` 时以 `findGitPaths(cwd).repoDir` 为含根目录的扫描上界；native-home 独立加载与普通 Pi 不变，无 Git 根沿用原行为。child 既有 `--no-context-files` 不受此路径影响。 |

短 snippet 与 tool description 的能力名称相同只承担工具发现；本批删除的是再次规定行为的副本。字段的合法值、默认值、身份及任务事实不是可任意删除的提示词。没有新增自动语义去重器、通用 prompt 框架、固定汇报模板或执行 SOP。

## 前台、后台与接续路径

输出义务的源码核对覆盖 `foreground/subagent-executor.ts` 单个任务、`background/async-execution.ts` 单个及顺序 step、`background/subagent-runner.ts` 动态并行 namespace。前台最终执行 `foreground/execution.ts` 仍用 system helper；后台在 outputPath 已解析后注入，namespace 在各实际路径确定后注入，不能提前用未分区路径。preflight 使用同一 system helper。新的恢复 descriptor 保存基础角色 system 与 outputPath，重新组装时仍注入一次；旧 descriptor/system 或历史 task 可能已经含有旧副本，本批不迁移既有会话历史，也不对任意用户/父方 task 做语义清洗。

主成员 fresh/reset 经同一个 Braid role/common/profile producer；正常接续消息只说明工作项和本次参考事实。observer 在 before-agent-start 增加可恢复的原任务结果事实，本批去掉其重复教程。原生 subagent 的动态 supervisor、预算和完成说明可能在运行 hook 后出现；静态组装没有声称覆盖全部运行时消息。模型路由、工具开放、fanout 深度 3、父 profile 不进 child 的边界不变。

## 构建与实际材料反馈

`compilation/braid-build.log` 记录 `cargo build --manifest-path sources/braid/Cargo.toml` 成功，13 条此前已有 dead-code warning 保留。Python 的 run.py/runtime.py 编译与 8 个改动 TS 模块的现有 TypeScript 5.9.3 语法/emit 编译成功；TS 不是完整依赖类型检查。最终 Braid 编译记录为 `compilation/braid-build-final.log`；原生 edit/grep/find/resource-loader 四模块通过 Node 语法检查，实际生产 prompt hunks 装配后字节与原生材料源一致，见 `native/core/final-prompt-assembly.json`。

`native/start-assembly.json`、`final-assembly.json` 记录固定原包与当前补丁的实际安装组装，均保持 `patch --batch --fuzz=0`。证据 runtime 复用 `runs/iteration13/subagents-20260930/runtime` 的已有 Linux 工具依赖，但 subagents 从固定原 tarball 应用最新完整补丁链重新装配，background/core 使用本批 prompt 产物。这个目录用于原生材料入口，不冒称最终 Linux 工具整合制品；原旧 runtime 没有近期删除单 writer 的提交，不能拿它的身份替代最新源码。

实际 prepare-only 使用已有需求 `tasks/iteration11/run-audit/github`，产物是 `prepared/.factory26/20261001-002539-9936377b`，技能来自 `runs/iteration13/svc-skills-20260930/stage-complete/skills`，Braid 是当前源码编译产物。命令经标准 I13 `main.py --prepare-only`，没有启动 Braid/Pi 会话、模型或评测。它发生在工具组新加载修改前，因此保存的 launcher 和技能选择代表该次实际来源。

`assemble-native-materials.mjs` 直接调用既有 Pi `loadExtensions`、`createAllToolDefinitions`、`buildSystemPrompt`，以及 subagents `discoverAgents`、skill metadata builder、`resolveSubagentLaunchContract`、`rewriteSubagentPrompt`，用这份实际 prepared 配置保存原生组装。它不构造模拟任务或执行事件。`native-preflight.json` 的十项角色结果均成功、扩展注册错误为 0；每项均为 fresh、append、关闭项目和父技能继承、fanout 开放且没有显式 allowlist。`native-input/` 保存两主层 metadata 与十 child system/tool material，child 没有 develop→main 等父 profile 文本，技能只呈现导航。主层文件名 `main-native-with-profile.md` 表示 Pi 层与 profile 的实际组合，没有伪称已经运行 Braid 的完整 role/common 注入。主准备 application 尚未初始化 Git，不能拿这份祖先列表代替真实 Braid clone 的最终项目指南结果。

最终源码另经标准 prepare-only 成功生成 `final-prepared/.factory26/20261001-010746-1d430519`，使用工具组已安装的固定 lock 本地 runtime（不是最终 Linux export），没有调用模型。`final-prepared-materials.json` 保存生成材料 hash、两 profile 的五角色配置与 task 首行；根 task 不含旧 origin 与 pnpm/portless 副本，executor/explorer 技能导航随工具接线各增加 context7-docs 到 13/9 项。native 新工具运行 hook 和服务验证仍归工具组，本页不以准备材料证明它们可用。

真实保留的独立 Braid clone 为 `runs/recovery-curation/editable/sheet/template/.factory26/20260929-042409-811f18d4/braid-state/worktrees/pr-2/pi-deepseek-fast-g1`，只读调用原生 loader 的结果在 `project-context-boundary.json`：普通 Pi 的 before/after 均返回 Factory AGENTS；Braid 标记开启时，before 返回 Factory AGENTS，after 不返回它。该 clone 及选定 native template 没有自身指南，未制造指南文件或新任务，因而 native-home/仓库内部指南的正向保留来自原生产者控制流核对，尚无该现场的非空产物证明。没有启动或改变历史 run；修复不追溯移除旧会话已消费的指南。

组装早期失败分别来自 Node 对 node_modules TS 的限制、现有 peer 入口、工具定义 API 返回对象和 preflight 返回 contract 的差异；使用包外源码及已有依赖入口后成功。保留 `native-assembly-attempt3.log`、`native-assembly-attempt4.log` 与最终日志，最终仅有 Node experimental transform 与多次加载的 listener warning。没有把失败改记为通过，也没有运行模型来掩盖装配差异。

runtime prepare 原先在每个 patch 应用后立刻记目标 hash；后续 patch 修改同一 `subagent-runner.ts` 后，早期 stamp 立即失效。改为全链 patch 完成后第二循环记录最终目标 hash，并将新增 prompt 目标纳入记录。有效身份应绑定整条组装后的文件，而不是中途文件。工具组保留了这处修正并独立负责新包接线和最终 Linux 身份。

真实 Linux 构建另发现此前 untracked model-exclusion 补丁的最后 hunk 只有两行尾 context；GNU patch 将这种不对称 hunk 按文件结尾约束，内部位置拒绝，BSD patch 此前接受。失败源码/rej 与原补丁保存在 `native/linux-model-failed.*`、`native/model-exclusion-before-platform-fix.patch`。从相同 before/after 文件重新生成标准三行 context，模型排除正文不变，fuzz 仍为 0；`native/platform-assembly.json` 记录 BSD 全链成功，Linux 最终结果由工具组实际构建记录提供。这是装配缺陷修正，不是新增模型调度行为。

## 具体未验边界与下一组入口

本批没有运行模型、动态前台/后台 child、原生 supervisor hook、完整 Braid 新会话或正式恢复。静态 source 与现有纯组装入口覆盖这些生产者的来源和调用路径，但没有证明每个动态消费者在未来任意 task/history 中都没有重复。旧会话已保存副本、任意任务文字/技能实际按需读取后可能带来的方法重叠仍需按实际材料判断；本批不篡改历史或把技能正文导入初始输入。没有运行或修改 I12 冻结实验。

Context7/fff/Exa 已由主线静态审查后交工具组实施；本页第一次材料未装载它们。新工具最终注册、服务鉴权、Linux native fff、完整 package/prepare-only 和所有 patch hash 以工具组实际产物为准，不能把审计下载包或本批旧基底 assembly 当成它们的运行证明。

下一组可承接的稳定方法目前仍在两 profile：重要决策的 advisor 时机；共享契约裁决与消费者交接；develop 集成和最终 main 候选验收；历史局部 PASS 的适用范围与 evidence 交接；跨 Braid/原生委派边界。根 task 中需求范围、初态归属、基础 PR 与任务分解方法也仍存在。后续迁移须同时改 profile/task 的读取时机与独立技能，避免新技能方法和原段落一起进同一 Agent；本批没有建立尚未存在的读取入口或迁移方法正文。

Braid 实现提交为 `49d5d5f`（`ref(prompt): 集中工作项通用协议并删除指引副本`）；Factory 实现提交以本文件和 `ref(prompt): 按消费者去重 I13 原生输入` 定位，完整身份写入证据目录的 `commit-identities.json` 并交回主线。Factory 共享文件使用 HEAD 加本轮 prompt 增量的 staged blob，保留工具组加载与其它历史 dirty；Braid 仅提交完整当前 common prompt、Issue role 的通用交接短句去重及技术说明新增段，common 中起点已有目录/CLI义务按当前契约沿用，未把它们当成新发现。其它 provider 角色/事件/重建与生命周期修改保留在工作区。
