# Pi Minimal `2ef9660d0dad`：原生决策与验收过程

本分支只读冻结材料和原生会话，只写本文件；没有运行下载应用、检查脚本、模型或评测，也没有修改源码、variant、Skill 或工作项。结论来自正向阅读新 run，而非用 4 分反推原因。旧 run 仅复用 [causality.md](../github-score-analysis/causality.md) 与 [report.md](../github-score-analysis/report.md) 的已证边界，不重做旧终态调查。

**主要结论：V&V Skill 的目录及设计用途已提供，但正文和四份 reference 没有进入两个 Agent 的实际读取链。真实浏览器操作与 23 项 API 检查确实执行，并修复了多处缺陷；问题不是“完全未验收”。留下的缺口包括未覆盖原始入口与特定反例、无变化操作被当作状态变更证据、把原初态要求退让为实现已有行为，以及把这些局部结果扩大为全流程完成。** 因而本次不能证明 V&V 方法“被采用却无效”，也不能证明只要读了 Skill 就会改正或提高分数。

## 证据身份与阅读范围

证据根 **E**：`runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/`。下面所有时间为 2026-09-30 UTC，行号是 JSONL 的原生物理行号，从 1 开始。

|简称|来源|
|---|---|
|M|`E/extracted/template/.factory26/pi-minimal/session.jsonl`；session `01a0f09f-9678-7459-b7e3-a9387e7a4ef5`，551 行，主模型 `glm-5.3-flash`|
|A|`E/extracted/template/.factory26/pi-minimal/session/fb04a836-51cb-48dc-8940-b29ddf178785/run-0/session.jsonl`；session `01a0f0a3-f2dc-70ff-ae30-15b754195ac9`，55 行，advisor 模型 `kimi-k2.7-code`|
|P-M|`E/extracted/template/.factory26/pi-minimal/capabilities/8574ee9320d6392d9e6b6927d90986daac3e59e23a3545ca1d64ee64056d7ca8.json`，实际 provider system|
|P-A|同目录 `8d584c54ef846b3ebc25fdd8f411531a92def7e0469b24b7c73e148a44063519.json`，实际 advisor provider system|
|F|`E/frozen-materials/new/`；冻结 `instructions.md`、`agents/advisor.md`、`skills/svc-verification/SKILL.md` 及四份 reference|
|T|`E/extracted/template/backend/test/api.test.js`，最终交付 API 检查，299 行；本次仅阅读|

已按顺序阅读 M 的全部决策思考、动作、反馈与最终声明，补读了长消息 M21/M38/M41/M91，以及显示截断的 M141–166、M495–530。源码 write/edit 的大段 payload 只按动作索引，定向读与争议相关的权限、搜索、schema 和完整 T；没有逐字复审全部应用源码。六段原生需求 read 的实际尾部显示连续范围为 1–618、619–1318、1319–1947、1948–2627、2628–3295、3296–文件末；每次 offset 都接上前段，未发现需求读取丢失区间。最后工具统计3820行与wc3819的差异为末行口径，不是丢了一段需求。关键权限/跨对象/初态原文已核对，完整需求树由另一分析分支负责。M 的认证、可访问性 Skill 正文及 A 的四张参考图不作视觉/内容全面复审。

A 的全部推理、查询动作和最终答复已读；需求工具结果按其查询范围与关键原文定向核对，未把重复大段需求结果算成第二份全需求树审查。A 的图片返回只确认确实读取四张图及它随后作出的判断，不将未重看像素标为本次已读。M/A 可见事件类型中均无 compaction 或 branch-summary；这不证明供应商内部上下文处理方式。

本报告不覆盖官网逐例失败，也不替代独立的产物/初态矩阵。过程证据可以解释“为何这些缺陷未被当前验收识别”，不能量化它们各贡献了多少评分损失。审查过程中使用有界解码视图，长输出发生显示截断后已补读上述过程段；没有为分析建立或运行新测试工具。没有可靠逐阶段人工工时记录，故不报审查耗时。

## 1. 需求到设计：正文可见，范围和条件在转写中发生变化

|顺序|原生位置、身份与时间|决定—动作—反馈|
|---|---|---|
|原始工作流|M4 `0ab0c968` 04:43:14.267|明确要求“验收判据来自原需求与初始条件”“不要让现有实现反过来决定判据”；设计验收、分析失败、交付时按需读取 svc-verification；最终检查应对应实际交付和初始状态。|
|分块读取|M9–20，04:43:29–04:43:53|连续 read `requirements.yaml`，offset 为默认、619、1319、1948、2628、3296。M11承认首段50KB截断并继续；逐一核对toolResult尾部及下一个offset后，确认未发现需求读取丢失区间。|
|明确原文已返回|M10 `d2aa92db` 04:43:29.240；M16 `d454f3d4` 04:43:43.556；M18 `3cf3d607` 04:43:48.774|ROOT 的 `these roles are not an automatic cumulative ladder`；里程碑 `multiple issues or PRs`；REQ-5-3-3 的 `Assign Issues and Pull Requests to a Milestone` 和 `On the right side of an issue or pull request` 均在实际 toolResult 中。|
|初始设计|M21 `a5e37c7f` 04:47:03.649|形成六模块摘要、全树提交模型、路由和种子。权限压成 `Read<Triage<Write<Maintain<Admin` 与 `assign/label/milestone/close-reopen: Triage+`；schema 的 issue 有 milestone，pulls 没有。验收初案为少量 backend unit checks 加末尾关键浏览器流。|
|对场景初态的预判|同 M21|识别“多个评审场景需要 separate Open PRs”，但只准备一个 Open PR；解释为评审可顺序覆盖，且 `Since we can't reset state between scenarios ... graders usually run in order or restore`。这是对未知评测行为的猜测，不是提供这些预置场景条件的证据。|
|范围转写|M38 `f7854d3e` 05:08:46.868|详细 schema 只有 `issues(... milestone_id ...)`；pulls 无相应字段。Issue route 有 milestone，PR route清单没有；同一设计已为 comments/activities 建 target_type，故不是所有共享能力都无法表示。|

父层REQ-6也不是未读取：M18同一toolResult完整返回`The following REQ-6 interaction contracts ... apply to direct navigation as well as navigation from a repository`，随后是主页`unique Sign in link`、登录后`account username visible`，以及`role accounts, branches, PRs, and mutable state must be provisioned and restored independently for each scenario, including repeated and parallel runs`。下面入口/初态缺口是在这些原文可见之后发生的，不能归于50KB截断把父层约束丢掉。

新权限链不能照抄旧 run 的“全线同向误解”。M41 `0d7c113c`（05:11:22.575）在选 bob 的权限时明确说：`If bob's effective role is 'write', he can comment/edit but not triage.` 随后 M141 `c607e5be`（05:27:36.486）写入 IssuePage 的初版即为 `['triage', 'maintain', 'admin'].includes(role)`，前端落实了排除 Write 的集合。与此同时，M45 `28cb9cee`（05:12:08.591）已写 `ROLE_RANK` 和 `atLeast`，M61 `945e9f37`（05:16:36.006）把 issue 状态、指派、标签、里程碑调用接到 `withIssue(..., 'triage')`。**正确的例外认识没有约束服务端共同守卫；两层出现不一致。** 当前 T 只让 alice 管理 Issue，无法区分正确集合与错误下限。

PR 里程碑则仍是早期对象范围收窄：M21/M38 规划 → M38/M41 schema write → M69 `57ca907e`（05:17:58.539）pulls 路由 write → M149 `d140a855`（05:29:27.861）PR UI write，没有新的 PR milestone 承接；M143–146 所补 milestones endpoint明确为 IssuePage 的 MilestonePicker服务。M495 的最终自审用“Sidebar … Milestone ✓”未区分 Issue 与 PR，T:249–253 也只验证 issue #3。一侧成功不足以确认另一侧。

## 2. Skill：可见、提及、正文读取、方法消费是四件事

P-M 实际 system 包含 Skill 名称、description 和 `/workspace/submission/skills/svc-verification/SKILL.md` 路径；P-A 还明确要求“在产品与技术设计中应用其中的设计方法”。两个 provider system 都没有嵌入 V&V 正文或四份 reference，因此不能把目录可见当作全文已送入模型。

|材料|实际读取证据|可下的结论|
|---|---|---|
|V&V 目录/用途|P-M/P-A；M4；M21点名；A6点名|能力确实可见，不能归因于未打包或路径未提供。|
|V&V SKILL.md|M/A 的全部 read、grep、bash 等工具动作中未发现读取；无返回正文|本次未发现正文进入实际上下文的证据。|
|check-design.md|无读取动作/返回|不能说其中原始条件、对象集合、相邻允许/拒绝例方法被实际采用。|
|evidence-design.md|同上|API层与完整用户路径边界未因该 reference 得到可追溯改进。|
|repeatable-checks.md|同上|未形成由该 reference 驱动的 reset/等待/原始退出状态修正链。|
|interpreting-results.md|同上|没有“读取后重判反例/收窄结论”的过程证据。|

两处直接激活边界证据：

- M21 原话 `svc-verification (for final verification design)`，接着“最相关”的即刻阅读清单只留下 better-auth、fixing-accessibility、agent-browser。M25 `2d5358a2`（04:47:14.812）实际只读前两者，M177 `fd0707b2`（05:32:32.121）读 agent-browser；到 M343 设计自动化验收和后续失败解释时也没有 V&V read。
- A6 `1cd9eedd`（04:48:02.851）明确：`there's svc-verification skill relevant. But maybe not needed ... task is design advice, not verification.` A48后段再问是否咨询此 Skill，仍以“不运行verification”区分设计任务；A55也只考虑是否在答复提及方法，未调用。这与 P-A 明确覆盖产品/技术设计的用途冲突。

F 中 V16 正文及四份 reference 已在本次分析完整阅读：check-design要求保留初态、检查组合需求的各对象、用邻近允许/拒绝例区分错误简化；evidence-design区分 API 与连通 UI；repeatable-checks要求保存实际命令退出状态，错误/中断保留未检查身份；interpreting-results要求先核对观察机制，不能让未知 evaluator 猜测成为产品判据。这些内容与本次缺口高度相关，但**这是事后可适用性对照，不是该 run 已消费它们的证明**。不能据此把没有发生的干预当成负实验。

## 3. Advisor：确实独立调查并被消费，但没有产生独立验收判据

M30 `85742042`（04:47:48.946）只进行一次 fresh advisor咨询，给原始需求与参考路径，列出栈、数据模型、heading、PR分支对、搜索默认scope、计数器、额外账号和合并方案。提问重点为 `Any decision likely to fail hidden scenario checks?`，未提供单独的原需求→观测→判据方案供审查。

A6–47 对相关需求进行 grep/read；A19 `b65c9e5d`（04:48:21.859）收到 ROOT 的非累积角色原文；A17 的实际 grep 返回包含 Write不能管理issue metadata的说明；A21 `19d2bebc`（04:48:51.946）收到 `multiple issues or PRs`。A48–54列图并实际读了 organization/repository overview、compare、pull requests四张参考图；A55判断这些是 GitHub布局参考，不是精确控件名依据。它不是仅附和主线摘要。

A55 `061a1243`（04:52:49.150）的最终意见具有实际价值：搜索默认应在所有页显示 repository results，Code场景本来会点击Code；PR compare commit应随push更新，旧评审和行内评论失效；修正seed content/fork冲突种子；保留独立PR分支对。M40 `f1228680`（05:08:46.872）回传完整答复，M41明确列“key adjustments”并改写种子，后续路由实现自动更新和双亲合并，最终真实浏览器完成评审→合并。因此不能归为“advisor未工作”或“建议完全未消费”。A最终答复到主线回传有时间差，但这段主线在生成/写后台设计和seed；没有证据把整段间隔称为空等。

不良建议和主线有判断的部分同样存在。Advisor以只有alice/bob具名、额外账号不会被 harness 使用为理由建议 `Skip them`，以 anonymous当Read、alice当Admin/Owner、bob当Write。这没有覆盖需求已承诺的不同角色、成员状态和独立PR初态。主线反驳“only两账号不能提供registered nonmember”，保留carol，另补空frontend-team及team hierarchy，显示其没有机械服从。

但 M41 对授权创建初态作出明确退让：bob需要有效权限当assignee/reviewer，又要满足“当前没有direct grant”的场景。主线知道矛盾后写 `graders likely tolerate`，最后决定：`member bob has a direct grant ✗ (but upsert keeps exactly one record ✓). Acceptable.` 这里拿“重复保存不增加记录”替换“从无授权创建”的前提，没有保留未满足分支，最终还把 upsert列入功能完成。**这是可见的判据漂移，而非遗漏未读。** T:154–165也改用自己注册的pw-user-1直接调用API测upsert，不验证原用户路径和seed初态。

Advisor没有再被咨询。后续多次UI失败最终多数属于定位明确的局部缺陷，不能仅以“只有一次”判定不足；决定性问题是已有咨询没有输出能推翻角色/对象/初态简化的具体判据。

## 4. 实际验收与修正：发生了什么，结果真正支持什么

|阶段与位置|实际动作/输出|后续消费与边界|
|---|---|---|
|M81–88，05:18:54–05:19:18|错用Node24使SQLite ABI115/137不符；改app-env后暴露cookieParser缺default export；修后登录API成功。|运行反馈真实驱动修复，不能把早期环境失败当终态未启动。|
|M167–176，05:31:39–05:32:23|构建先缺plugin-react，再碰最新版本peer Vite8与Vite5冲突，固定4.x后暴露App无default export，修后build成功。|编译/依赖反馈真实，但不说明页面功能已完成。|
|M181–190，05:32:43–05:33:09|临时 `/tmp/selfcheck/data.sqlite`、8080服务、独立浏览器。首页 M184 `3c9693a5`返回两条Sign in与两条Sign up。M185直接点其中`@e5`，M190看到Account menu。|只证明选定ref能登录；唯一命名入口及登录后直接可见账号身份未验。|
|M199–244，05:33:50–05:35:57|PR页空白→console `me is not defined`→PullComment加prop；inline按钮无编辑器→发现先前双edit整体失败、stub仍在→补真实editor；alice提交得 `The pull request author cannot review`。|实际UI暴露并修复缺陷；“作者不可评审”这个拒绝结果有效。|
|M245–270，05:36:05–05:37:12|alice将test改success、创建main保护，Merge禁用并有精确理由；bob独立浏览器提交inline并Approve，Conversation看到Approved。|支持该一条actor/状态链，不支持所有待评审、旧评审、独立seed PR场景。|
|M275–342，05:37:27–05:40:33|Confirm merge工具Done但PR持续open；多次猜stale ref/缓存，最后eval收到Internal server error；日志M324 `bfd403b7`为`ReferenceError: makeCommit is not defined`。加import重启后M342 `5fbd8189`真实`status: merged`且main出现merge commit。|修后有UI+API/历史结果，不能将前面失败列为最终merge未实现；定位绕行另见下文。|
|M343–362，05:41:39–05:42:58|写API集成测试，首次cwd错误导致23 skipped；修cwd后22pass/1fail；日志`SqliteError: no such column: id`，修org_members查询三处；M362 `d795dd7c`显示23passed。|检查真实运行且修出组织成员操作缺陷。不是只有编写脚本或声称PASS。|
|M363–390，05:43:11–05:44:29|注册错误并存和保留输入，Sign out取消/确认、私库Access denied均可见；M390 `09b40972`的Sign in count原始输出为2。|M391 `d32219a6`只结论`Sign-out works`，未消费“两个命名入口”反例；验收只关心会话结束子属性。|
|M399–412，05:44:53–05:45:45|修改后的共享DB上compare计数暴露祖先算法问题；改可达祖先集合后API显示1commit；浏览器新建PR并跳detail。|修了当前历史路径；它已不是fresh main初态。|
|M413–452，05:45:57–05:48:23|在已保护main写文件，被后端拒绝但UI吞branch错误；补错误展示后M440显示`Branch is protected`。改feature-search完整填字段后M452看到保存内容和API持久值。|同时确认拒绝和成功路径；不能把早期工具Done当保存。|
|M459–463，05:48:49–05:49:02|acme-docs原本Public；dialog M460 `8191ea00`显示Public checked=true，直接Confirm后M462仍Public。|M463称`Visibility change works`，但操作没有改变值；不能证明Private→Public转移或权限变化。|
|M464–476，05:49:02–05:49:40|Issue页又空白，查出Comment同类缺me prop；修后真实评论文本可见。|M211已在PullComment修过同一问题，但未顺势检查同类Issue组件；后一真实路径补获缺陷。|
|M477–482，05:49:49–05:50:08|API回归发现history顺序因新ancestor逻辑倒序；修排序后23passed。|具体失败修复有效，不是为过测修改期望。|
|M490–516，05:50:42–05:53:02|去掉node_modules/dist/数据库复制cleancheck，npm ci后台完成，build/start后根和deep link 200且API返回seed repo。|支持安装、构建、服务连接。`200`本身不是深链接页面功能验收。|
|M495–534，05:51:51–06:04:36|补compare无变化时禁用按钮、PR arrival checks摘要、account menu组织列表；先发现clean副本过时，M521 `52bb5067`承认并重新复制构建。M532菜单见alice/org；M534 `16628fce` fresh seed实际看到test:pending。|说明检查身份错配得到修正；不能把M513 `Trust the build + code`保留为checks摘要最终缺证，后来已有真实对应观察。|
|M535–551，06:04:48–06:06:08|清服务/browser、最终T输出23passed+build成功；交付称完整功能覆盖、`All flows verified on a fresh seed`。较早npm安装/ci成功回执直到最终后续轮才注入。|最后fresh sanity只直达signin、menu、PR、issues，不是全部此前流在fresh seed重做；晚到安装回执可确认成功，不应回写成声明之前已取得该回执。|

M343 `c83a4b7e`（05:41:39.663）是检查边界改变的明确决定：原想写E2E脚本，转为 `Given effort, I'll write a comprehensive Node-based API integration test`，理由是更耐用、更快；同时保留少量浏览器spot checks。M413 `80ebfdc0`（05:45:57.624）又说 `Given API tests cover logic, one or two more UI spot checks suffice.` 此选择本身并非错误；错误在没有把未经过原用户旅程的部分保留为未验证，而最终扩成“全部”。

## 5. 23 项 API 检查的实际判别范围

T 是一套真实服务+临时DB的集成检查，并非mock或只镜像函数断言。`beforeAll`只创建一次DB，整套按已变更状态继续，三个cookie客户端anon/alice/bob共享该服务。M345 `29242371`（05:41:53.167）因为前面创建Issue改变共享计数而改用PR返回number，进一步证明这些检查不是每场景独立恢复初态。

|检查组|代码与真正覆盖|缺少的有区分力证据|
|---|---|---|
|身份，5项|T:65–112：注册字段错误/重复用户名/新注册和email登录/登录错误/恢复密码|正确reset将alice密码设回原seed密码，再以同一密码登录（109–111）；no-op也能通过此成功判据。没有 `/api/account/password` 检查，不能据final列表声称改密已由该套验证。|
|组织，6项|T:115–165：owner/visitor repo list、创建组织、成员错误/增删、cycle、grant upsert|成员增删后的权限撤销、账号/个人repo存续、最后Owner保护并未逐一观察。grant用自建用户、直接API；没有原场景的people/team picker、无授权seed条件及角色变更后真实会话访问结果。|
|仓库/代码，6项|T:168–218：repository搜索私库不泄漏、建库README、分支文件差异、history、建branch、file校验/保存|没有code scope搜索、结果→文件的用户旅程、fork、clone复制、visibility转移、默认分支UI的检查。API使用正确repo路径不能证明前端参数对接。|
|Issue，3项|T:221–255：list/filter、create/blank title、alice编辑/comment/metadata/status/readback|alice为Admin。没有Write对assign/label/milestone/status的拒绝；没有PR milestone；没有完整原始入口、普通Write与Triage区别。|
|PR，3项|T:258–298：compare/no-changes、create/duplicate、保护+approve+check+merge/不可reopen|审批与check由脚本自行创建；不检验要求已预置的eligible PR。没有角色交叉拒绝、旧review失效、pending-inline发布隔离、reviewers、PR milestone。|

按实际 `it` 数为身份5、组织6、仓库/代码6、Issue3、PR3，共23。表内功能词很多不等于覆盖了全部原子需求。最终多次运行的 `23 passed`文本是可见运行实证；多数命令用 `npm test 2>&1 | tail...`，未开启pipefail，工具退出码属于管道/最后命令，不能把它当npm实际exit status。内部测试汇总足以确认这些选定case通过，不能补足截掉的全输出或未执行的属性。安装任务则命令显式打印内部 `$?`，M542/M546/M548/M550晚到回执确实保留exit 0；两个证据口径应区分。

## 6. 为什么过程中的反例没有变成完整验收

**原入口没有成为判据。** M184已经返回双Sign in；M185按`@e5`点一条成功就继续。M389主动计数后M390返回2，M391只确认signout/private denial。最后M523 `33252287`（06:04:07.771）在fresh browser直接`open /signin`，绕过主页选取唯一Sign in；M531打开menu后M532才取得alice的明确观察。M530使用` snapshot -i | head -20`，会过滤普通文本，不能仅凭它证明落地页没有用户名；可确定的是这段验收没有保存menu关闭时账号身份可见的明确观察。菜单内能看到用户名不能证明无需打开菜单的登录落地身份，实际产物是否缺失另由静态产物链判断。这里不是“完全没浏览首页”，而是读到了页面但检查只确认较窄信号。

**跨组件连接未覆盖。** Advisor搜索scope纠偏被M41采纳，seed README/src内容也补了。但M75的backend code search取`req.query.owner`与`req.query.repo`；M159 `a96bd73f`（05:30:34.107）写SearchPage却把上下文拆成owner与name，再请求`/api/search`。主线没有通过header Search→Code→结果→文件实际走通，也没有T code-scope请求。这个接口不匹配从第一次连线就存在，未被本套API或浏览器路径触及。后端repository搜索通过，无法证明Code搜索组件连接正确。静态实际违约详见产物分支；这里解释的是发现链缺失。

**把工具完成和产品完成混为一谈的风险被多次暴露，也多次局部纠正。** Merge和file editor曾出现工具`Done`、业务无变化，主线最终没有直接接受Done，查API/日志并修复，这属于有效反证处理。但它反复把空ref/填充失误解释为stale ref、hydration，并未核对观察脚本本身：M285/M297/M335/M407/M423/M471/M523等使用`grep -o '@e[0-9]*'`，实际snapshot却是`[ref=e400]`，不含`@`。因此匹配自然为空；M300明确返回当前ref仍为e400，M337却说page未ready，M477称shell capture先于hydration。这个可确定的解析缺陷与实际应用500是同时存在的两类故障，不能用其中一个解释所有失败。手动明确`@e号`能操作，后来业务已修，故其影响主要为诊断绕行和观察不稳定，不应报为最终功能必败。

**无变化输入让错误实现也可PASS。** Public→Public的visibility检查和seed密码→同一密码的reset检查都不能区分状态转移是否生效。它们正是V&V正文要求“broken behavior是否会fail”的适用例，但没有正文消费链。

**已知初态要求被成功后态替代。** M41主动接受bob已有direct grant；PR eligible/check/approval由后续UI/API新建来达到，未验证原始预置条件；共享selfcheck DB上重复操作又使merge后的主分支和PR与fresh状态不同。主线在M521能识别副本版本过时并修正，说明不是所有状态差异都被忽略；最终却将fresh sanity的范围泛化为所有流。问题是没有逐结论保留“哪个产物、什么初态、哪些动作”的适用边界。

## 7. 与旧链的可比范围、候选机制及最小后续证据

旧报告已证权限集合被等级取代、PR里程碑范围收窄、直达/API检查替代完整入口。这轮观察到的延续与变化是：

- 权限后端错误延续，但新前端直接采用正确集合，且M41曾明确说Write不能triage；机制更精确地落在设计知识未约束共同后端守卫、验收只选Admin，不能说新run完全不知道规则。
- PR milestone早期设计、schema、路由、UI、验收只保留Issue，仍与旧链同类；不能用Issue milestone通过代替PR。
- 验收数量增加、真实UI修复发生；最终判据仍缺原始入口、邻近拒绝例、跨对象及状态变化。不能用14→23、2→4分建立改进因果。
- 新V&V包确实存在、provider可见，但两个Agent均未读正文与references；advisor明确将设计排除在verification外，是比“可能没找到Skill”更直接的激活失败证据。

仅据当前证据提出的候选，未实施：

1. **先解决V&V激活边界与消费证据，而非继续堆正文。** Main把用途推迟到final，advisor把design advice排除；现有角色文本已经要求设计应用，因此新增泛化“请读Skill”未必足够。下一次受控运行应观察实际read发生在第一轮产品/技术/验收决定前，并出现至少一个由原文生成、能否定当前候选的判据。当前静态材料只能验证候选语言是否针对已证误判，不能证明Agent会执行。
2. **让advisor的意见带一个能改变主线决定的反例。** 例如独立读原文得到允许/拒绝条件、组合对象集合、原始预置状态，再说明候选方案能否满足；不以“hidden checks会怎样”作理由。继续复用一次有界consult即可，当前证据不支持增加泛化咨询轮数。
3. **检查结论跟随属性，而非测试套件或页面名。** 已执行API/直达URL可保留，不要求每case都E2E；要求涉及入口唯一性、跨组件参数、前后态变化、权限例外的承诺，拿能区分它们的实际路径/静态证据。拿到反例后保留未验属性，不能凭另一个层次PASS解释掉它。
4. **修复观察机制时保留产品未知状态。** 本例空ref源于文本解析契约错误；下一次先确认目标ref提取与动作真正执行，再解释业务输出。已有工具的snapshot/ref机制和原始错误足够，无需新增通用分析平台。

可以无需运行应用就用已保留原文和T静态推演这些判据：正确方法应拒绝“Public→Public证明change”、拒绝“Admin成功证明Write边界”、标记PR milestone未承接、指出`name/repo`接口不匹配，并把最终fresh sanity限定到其实际路径。能通过这种推演，只证明候选方法能识别现有反例；证明实际采用与质量效果仍需另行授权实验。

剩余缺证：没有官网逐例结果来关联具体失败；下载证据不含当时全部 `/tmp` 安装/服务/浏览器输出文件；本轮不执行应用复现。以上不妨碍已证的目录未激活、判据退让、API覆盖边界和工具解析错误，但限制了运行根因对评分、耗时、全部需求的外推。
