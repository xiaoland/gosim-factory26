# I15：结构化需求拆分与 Braid 协作改进

赛后收口（2026-10-09）：比赛已结束，`i15-github-evo` 自动跟进保持暂停。Mac 上两个正式 Hosted run 的最新平台状态仍为 `RUNNING`，但本地已各有最新 workspace 归档；赛后清理已停止其 observer/default，只停止本地消费者，未调用平台 stop，也不把平台状态改写为终态。下文赛中行动和监控指令均为历史记录；证据保全和剩余清理见[赛后清理任务包](../post-competition-cleanup/packet.md)。

## 最新授权与执行：I15 官网两题正式提交（2026-10-08）

22:05北京时间手动当前查询：两官网run均HTTP500，具体响应“arc-bench.com，维护中”；无法确认当下仍生成、已评测或已有成绩，未继续logs/大project下载/重试或控制。原件 `runs/iteration15/official-github-20261008/manual-status-current.json`。最近可信业务归档仍Github21:28（基础review1 pending/业务PR9与10实际推进/43,311,045token/冻结价估¥10.9257）、Sheet21:16（基础及重命名候选待review/24,204,436token/¥6.3187），没有归档内合并/最终评分。i15-github-evo保持用户指定PAUSED，仅手动检查，所属保存消费者保留。

用户最新要求“暂停自动任务；我会手动和你检查进展，请汇报”。已通过App工具将i15-github-evo设为PAUSED，后续主会话只响应用户手动检查；官网两题生成与所属观测/完整保存消费者保持，不据暂停自动跟进停止官网。当前已有归档Github21:28/Sheet21:16，主由runtime_owner通过正常冻结执行器一次有界读取当前平台state/logs，不重复下载在途project或新采集器。手动最新回执待返回，本地c5仍按用户取消不恢复/评分。

21:49北京时间heartbeat只消费现有观察：GitHub新归档21:28仍RUNNING/2active/blocked0，基础review1未返回、PR9/10原生尾部有实际测试/typecheck/浏览器动作，尚无合并评分；7native/459响应累计43,311,045token（cache42,435,648），冻结ARC价表已保存估¥10.92571664，不叠旧档。Sheet status仍为21:16同档（不重复核算），既有observer/default四进程仍存活；摘要ApiError: Playground HTTP500保留，workspace/logs errorNone，不能据摘要错误判生成失败，也不把滞后档当实时状态。Sheet删除101JSON候选尚无新验收/合入证据，风险与不自动干预边界保持。本地cancelled不恢复/评分。证据 `runs/iteration15/official-github-20261008/progress-20261008-1349/notes.md`，正常无可行动变化静默，继续原20min消费者。

21:25北京时间进展检查：官网Github/Sheet最新已保存归档约21:05/21:16仍RUNNING，2active/blocked0、尚无合并PR/终态评分。GitHub基础PR3交7560b41、review1 pending，5业务Issue已拆（REQ5/6合并），另有基础Issue2；Sheet基础PR11/重命名PR12交候选待review1/2，Delete PR13实现中，其余业务Issue排队。原生累计token分别30,592,748/24,204,436（含缓存29,836,800/23,447,616），冻结ARC可比估价¥7.8310644/¥6.31870368，不叠加累计档。2GiB两题均有触限max历史但oom/oom_kill0。Sheet基础候选删除101份官方基线JSON且根/冻结review依据同样认可清理，存在保留业务数据合同风险；PR未合、尚未证明最终output丢失，不自动注入/改应用或扩大早停范围。具体证据 `runs/iteration15/official-github-20261008/progress-20261008-1325/notes.md`。

本地c5状态已纠正：用户侧会话明确取消，19:33:12正常停止、远端/Mac完整saved，无后继run或评分；不接续/重头/自动评分停止产物。此前本线程“本地继续”口径撤回，20min ACTIVE自动跟进已只保留官网两题。原始data保留，portable_consistent=false不能冒称portable独立完整恢复。旧本地当前执行段仅作为历史。

Sheet真实启动采用已通过：首103MB完整project正常回收，官方output→seed→root独立工作区均102份业务JSON、Q3 Sales可读；11:52:04/09/15Z已取得Flash assistant和read/ls/bash成功工具响应，实际max_active_agents2。首切片3条assistant：input10,157/output414/cacheRead42,624/total53,195，仅首档用量，不能外推最终或重复加累计档。证据 `runs/iteration15/official-github-20261008/sheet-startup-adoption.json`（含archive路径）及sheet-startup-notes.md；同submission29e73030ac07两官网题已正常启动，成绩/终态尚待监控。本地c5继续；20min ACTIVE自动跟进已扩为三条既定运行，分别保存用量、评分和终态，不新增提交。

Sheet也已在同一submission **29e73030ac07** 复用正式包正常创建/start：官网 **75ee4879f24e**、Lab **d61987514b284d639abe7301e33012f0**，11:51:20Z（北京时间19:51）started=true/pending=null/official_evaluation，未重上传。唯一observer21019/default21021，1200秒/project留档；回执 `runs/iteration15/official-github-20261008/sheet-start-receipt.json`。同份包固定scope名称801c…，GitHub与Sheet各独立container/template，不能因scope字符串同名推断会话/业务共享。Sheet采用官方Sheet基线、fresh原生状态，GitHub a404及本地c5未控制。两题均已受理启动，但未全部完成/取得正式最终评分；首Sheet Harness/模型/基线采用待实际回执。用户20:00截止已记录。

用户追加“sheet-evo也要”：明确授权同当前正式submission29e73030ac07新增启动Sheet Evo，复用已上传当前I15正式包，fresh原生状态、官方完整Sheet基线、competition=true/official_evaluation、正式Flash/Hosted2/Vitest1。runtime_owner唯一沿正常Hosted创建/start，先核是否已有Sheet避免重复POST；优先20:00北京时间截止前取得启动回执。Github a404及本地c5继续，保全部历史，不删snapshot或取消其它run。新Sheet身份及采用待回执，20min/project归档与native费用跟进同前。

正式GitHub启动采用补充：11:40Z官网RUNNING，deploy/preflight完成，11:40:32 Pi/PBB/subagents/MCP补丁安装成功，11:40:36进入fresh scope801c6…。首完整project正常回收94MiB，output→seed→root独立工作区均有官方业务sessions28/users14/repositories2，实际braid-request max_active_agents2、1active/1reserved。11:41首档Pi session active、首模型请求在途，尚无完整assistant usage/工具响应，不能将启动当已取得评分。证据 `runs/iteration15/official-github-20261008/startup-adoption.json`；唯一observer80938/default80940继续，20min ACTIVEheartbeat已统一正式a404和本地c5两条，不重复回收首档。

正式GitHub Evo已正常受理启动：Lab **801c6afc6f074b5aaf50c49411993742**、submission **29e73030ac07**、官网run **a4049475373f**，started=true/pending=null，请求official_evaluation、competition=true；Hosted2/Vitest1、fresh scope、正式默认文本/视觉Flash，未带本地临时模型/应用。控制根 `runs/iteration15/official-github-20261008/`，唯一observer80938/default80940、1200秒观察并保留project归档。首真实Harness/模型/官方基线采用仍由runtime_owner取证，不把受理当生成成功。提交前遇execution._assemble局部import hashlib遮蔽导致UnboundLocalError，发生在官网副作用前，删除多余局部import后正常重试成功；保留原错误，未重复不确定POST。用户确认20:00截止。

用户明确“将 I15 提交正式运行吧”，随后更正“20:00 截止，总之尽快提交吧”。本次截止以用户新确认的北京时间20:00为准，覆盖此前18:00记录。立即按当前GitHub Evo题提交当前I15正式包、fresh原生会话、competition=true/official_evaluation，由官方注入完整初赛基线；本地临时GLM5.3替换仅本地，正式采用既有正式配方。runtime_owner唯一持正常Hosted生产/上传/创建/启动及回执，优先完成受理，不等待非必要核验。保留全部历史submission/run/snapshot，本地c5继续既有生成与独立评分链，不继承本地业务或隐藏反馈。20分钟跟进/project.zip/native费用方式沿既有授权，实际新身份待回执；不重复提交。

## 新授权：官网 Sheet 正式参赛（2026-10-08）

内存上游根因已确认：worker先await materialize_next_assignment，PR agent该函数内部for遍历整个新增assignment_candidates并逐个真实start Pi，循环结束之后才outer dispatch。Sheet05:53:35–49同batch连续起7PR，PR12–17已物理启动却0turn，wake runnable排除静止卸载；PR18启动约0.545s后触2GiB/OOM，尚未跑dispatch。这是启动整批先于输入投递导致累积，不是已证明claim gate拒绝或重复session计数。已采用最小修复：每次有效materialize一项即返回outer dispatch，invalid/unassigned仍扫描，不设并发cap、不改busy/fence/需求拆分。runtime_owner持实现/编译/公共材料收尾；失败run不冒充已消费新源。advisor另建议局部OOM承接与全entry终止拆开，但涉及恢复契约，当前先保留原fail-closed，不自动清历史OOM事件报健康。

费用修复已完成并采用：`tooling/scripts/braid_usage.py`对显式scope的project ZIP/目录复用pi_usage/arc_spend，纳入session原件和vision子session，排除转录/旧基线、累计归档不叠加。现场全部已保存响应12session/65assistant共1606457，ARC官方模型面板06:23:46Z价格input0.8/output2.8/cacheRead0.23 CNY/M，cacheWrite无价格且本档0；估算¥0.57938336。原件 `runs/iteration15/official-sheet-20261008/usage-cost-20261008/terminal-project/usage.json`、同目录notes/价格快照。6已分配PR成员无native/turn只列覆盖缺项，不伪造0费用；OOM在途未返回usage无法断言完整结算。Hosted费用主口径源码已始终用native+冻结价表、平台字段独立保存、缺native unknown/None；现长驻旧import未热换，后续正常新进程消费，不宣称当前已采用。AST语法/真实档核算，无测试/模型/新采集器。

内存深查在途事实：Sheet collector-start实际exit1，stderr lab_otlp.py:412导入agent_support失败；公共包agent_support位于support/而旧fallback找tooling/scripts，导致ResourceEvidence(memory.stat/peak/进程树/PSS)未采、telemetry空。runtime_owner窄修加载位置并核生产消费，同时取本地已有资源旁证。当前本地b32最新06:22:29Z lifecycle=failed、容器已不存在，consumer正保存，尚待退出原文/完整save，未控制或擅评分重放。费用完整109MB包实算：12本轮native session/65assistant，1,606,457tokens；按ARC刷新Flash价0.8(input)/2.8(output)/0.23(cacheRead) CNY/M计算¥0.57938336，不使用平台费用回执。braid_usage.py及Hosted费用消费更新在途，由metrics_owner持；另6个PR已分配但无native文件/turn，不虚造用量。

用户新开工指示（优先级覆盖）：费用不能依赖运行中官方费用回执；由project.zip全部本轮native sessions统计token，再按ARC API价目表计算，复用pi_usage.py或新增braid_usage.py。metrics_owner持实现/价格来源/实际本轮核算；此前¥0.579385只保留平台原字段，撤回为费用估算的依据。资源管理/监控/采集数据务必排查，内存是当前最高优先级：runtime_owner持官网完整project资源证据、进程/生命周期根因、必要本地现有内存旁证及明确最小设施修复；不止停在OOM直接链，不擅新实验或去掉真实2GiB边界。root持因果整合/关键判断及跟进口径。Mac产物WorkSSD、不测试Factory/Braid、不commit。

用户要求重试后的实际终态（06:13Z读回）：官网Sheet **5fe49ab17f13 FAILED/start_agent exit1**，未进入评测，不视作有效零分。05:53:53Z stderr SystemExit:-9；harness_services资源治理记resource_exhausted/memory_or_pids_limit_persisted。真实cgroup memory.current=max=2147483648，oom3/oom_kill1，memory.reclaim因只读失败，资源治理随后TERM/KILL自身entry进程组。治理按实际max/OOM事件，不是人为请求槽；不能将真实2GiB删除为“门禁”。尚只有单个Pi RSS187MB样本，不能将全部内存单因归给某worker；未擅重启。

正常terminal save完整project约109MB、saved=true。实际已拆9业务Issue3–11→glm3–11，基础PR2→glm2，根随后创建9业务PR12–20→glm12–20；全部尚未ready。DB17个Pi provider sessions，根理解旧名自动选择新成员，容量误会未复现。停止发生于多原生会话启动阶段，不能解释为没拆分或浏览器路径故障。当前scope12个有usage的session（含vision）：input194231/output38594/cacheRead1373632/cacheWrite0/total1606457，与官网token_count一致，未累计重复档或旧基线历史。平台token_cost_usd字段0.579385、token_cost_currency=CNY，按回执约¥0.579385，不按字段名说美元；创建official_evaluation身份保留，start billing self_funded属已知平台差异。全部历史提交保留，当前Sheet已终止且仅一题未评测，不满足两题完整选分。后续不自动新实验/重启；本地GitHub及其评分仍继续，heartbeat保留该未完成义务。

06:01Z用户查询进展/费用：唯一observer定期GET/status失败，原错误curl28 SSL connection timeout；未取得新project归档，不能将上次RUNNING当实时状态。可靠证据仍13:42北京时间首档：1session/4assistant，input17873/output527/cacheRead54656/cacheWrite0/total73056，仅启动切片，平台金额未知，不能外推当前累计或最终费用。首档仅需求/技能读取，业务Issue拆分尚无新证据。没有生成失败证据、不重复提交或停止；按既有20min下一轮继续消费，瞬时查询故障不自动暂停整个跟进。

05:45Z heartbeat采用：Sheet只消费刚保存首归档，尚在初期需求/技能读取，不重复下载或据此判断拆分失败。共享Hosted reader已识别当前scope native-homes/sessions真实日期文件，排除基线旧历史；原103MB档正常回读1session/4assistant=73056（cacheRead54656），旧空usage不表示零消耗。唯一observer63517替换55196，保留下一观察06:01:02Z才消费新reader，default55198不变，官网生成未重启。GitHub PR2/10/12三review仍pending、基础未合；PR9于05:29已交自验、等基础rebase复验，active3/pending0且仍有效响应，无终态/评分。PR9具体E2E BROWSER_INSTALL_FAILED已改用Playwright验收，当前非阻塞。定向原文04:29/04:36确认会话生命周期与cwd/env正确，设施原因是I15 e2e wrapper强制PLAYWRIGHT_BROWSERS_PATH=$E2E_RUNTIME/browsers，覆盖容器已有/ms-playwright；当前addon不含browsers且submission只读。最小wrapper已尊重显式路径，缺省使用FACTORY26_BROWSER_CACHE_DIR/XDG_CACHE_HOME/HOME运行cache，sh语法通过；沿当前Local执行器_sync_file/_remote_exec安装到该scope可写work/bin/e2e并读回，未改只读submission/业务或停止生成/daemon。下次新E2E进程可采用/ms-playwright；已存在MCP server仍持旧env，尚无失败消失实测，不宣称全部热换。 官网Sheet5fe4冻结包仍是修复前wrapper，Hosted不支持Local文件同步，当前未停止/重建Sheet；若后续出现同类具体失败再依冻结执行器处理，当前共享源修复不能冒充官网已采用。采用 `runs/iteration15/official-sheet-20261008/progress-0545-notes.md` 与GitHub控制根 `progress-0545.json`。

修复实际生效：05:41:42Z（北京时间13:41）新scope独立Pi session取得glm-5.3-flash完整响应，随后8项技能/需求/目录工具isError=false。正常observer已保留首project归档约103MB；官方Sheet旧业务102个JSON在output、seed及root独立worktree均存在，Q3 Sales存量可读。首归档用量input17873/output527/cacheRead54656/total73056，包含缓存、仅启动片段，不是最终费用；后续累计归档不相加。唯一supervisor55196/default55198、1200秒观察正常继续。采用入口 `runs/iteration15/official-sheet-20261008/startup-adoption.json`，内含project归档绝对路径；本次已真实生成，不再仅依平台RUNNING。

当前修复后 fresh 正式重启：Lab **2da24ede5e744805b2fd11c2ec2da074**、submission **d6ecf9b67df3**、官网 Sheet run **5fe49ab17f13**，正常 started=true/pending=null。190MB完整包携134项当前实际可执行成员清单（含node/braid），ensure预装快路径恢复执行位；首Harness/模型事实待回读，不以受理证明生成成功。target interval1200秒、retain_workspace_archives=true，复用已有每轮project下载并保留；旧失败完整97MB project正常saved=true/errors=[]，旧observer已在保存后退出。重复save派生目录symlink复制边界同时已修，未改应用/模型配方/本地冻结执行。全部历史提交保留，只启动Sheet。下面旧身份与过程按历史保留。

启动失败更新：官网22549969182e已 FAILED，start_agent阶段main.py退出1，预检通过，token_count=0、未进入评测。此前RUNNING仅启动受理，不是Harness有效生成；保留submission8e17304a3448及全部现场。runtime_owner正在下载project/stderr定位设施根因并按授权正常修复，未重新提交或删除。当前失败不是业务实现评分结果。 原始stderr根因已定位：05:31:32Z start_shared_proxy执行 `/workspace/submission/runtime/bin/node` 报 PermissionError Errno13。官网解压丢执行位，prebuilt ensure快路径跳过薄安装分支chmod。模型token0且Braid未执行。runtime_owner复用runtime-executables.json清单，在装配记录真实可执行成员并让ensure预装/marker快路径恢复权限；完整保存失败project后沿正常Lab fresh restart消费修复，不修改应用。原件 `runs/iteration15/official-sheet-20261008/startup-current-status.json`。

当前正式已启动：Lab **896c88be7c924f0297905b0154c0de1b**、submission **8e17304a3448**、官网 run **22549969182e**，正常 upload/create/start 回执 started=true、pending=None、RUNNING，competition=true/official_evaluation。控制根 `runs/iteration15/official-sheet-20261008/`；唯一 observer PID46458/default46460 已启动，target observation_interval=1200秒。首次模型及基线采用正在读回，不以 RUNNING 替代实际生成证明。新 submission 目前只创建 Sheet，GitHub 无 run，尚不满足两题完整选分条件；历史全部保留。

用户随后确认赛事组最新采用规则：“不要删除历史提交；不过，其实赛事组确认了会自动采用所有题目都完整运行的提交的里面的最高分数”。此规则覆盖旧最新有效提交上榜判断；latest-saved 创建 run 门控仍是独立机械限制。保留全部历史提交，最终核对新 I15 submission 是否两题均完整及正式最高分采用身份。当前新增执行授权为 Sheet，尚未扩大为官网 GitHub。

用户原话：“官网的 hackthon-evo 的 sheet 槽位空出来了，我建议整理一下，然后提交 I15 到官网参赛（同样持续监控，但是缩短为每20分钟；而且要下载 project.zip 来估算费用、查阅实际进展判断是否停止、绕弯）。”授权整理当前 I15 源码材料、通过正常官网执行器正式提交并启动 Evolution Sheet；不同于本地 GitHub self_funded 及其独立评分。官方注入对应初赛完整基线，fresh 原生状态，不携带本地生成应用或隐藏反馈。保留其它官网 run/submission/snapshot，不自动取消或删除。新提交可能成为最新有效正式提交，须保留原成绩与采用身份，终态核真实评分。

runtime_owner 持既有生产装配、官网正常接口提交启动与 project.zip 回收；root 持总 packet、20分钟跟进接线与业务行为判断。当前本地 GitHub b32cdb 仍继续正常运行和既有保存/独立评分，不由新增参赛指令取消。每次监控利用既有事实与 project.zip 中实际会话、Issue/PR、工具错误和有效交付；原生 token 区分缓存与累计快照，不将重复下载的累计用量相加。绕弯需回到具体决策与行为原因，不以时间/token增长单独停机。新正式身份、包与实际启动回执待 owner 返回；不测试 Factory/Braid、不 commit/push，Mac 产物仅 WorkSSD。 官网实时读回：历史正式 runs 均终态、Sheet 无活动槽；原 selected submission 92ca9811ef5e、成绩约63.137保留。Hosted 装配缺 submission-models.json，runtime_owner 按当前 Flash 主/视觉配方补官网必需模型声明，不引入私有自费路由。既有 i15-github-evo heartbeat 已统一20分钟，分别跟进两运行，正式身份待回执补齐。

官网首次装配 Lab 7e361f2beb214c1f909e46a5c2a0ea39 在上传前失败，无 submission/run/API 副作用：Hosted thin installer 未预装 Pi，但 write_zip 校验 retry.js 缺失；同路径未携 E2E addon。runtime_owner 采用公共 Hosted assemble 携当前已编译完整 runtime/E2E 的最小交付修复，复用原 write_zip 校验与 ensure 预装路径，不绕过校验、不新增安装框架。本地 b32cdb 冻结执行继续，不由本次装配改变；新正式运行身份待实际启动回执。

## 当前执行：提示收敛后的新本地 GitHub Evo（2026-10-08）

11:29Z heartbeat只读现有relay至11:30Z：c5继续running/4 active/blocked0，PR13已MERGED；review12 Approved但PR12因develop被PR13推进再次无法按冻结base合并，负责人评论105/106请求根协调合入窗口并做四轮候选，属于已观察到的重复复验热点，当前生成Agent正在协调，开发侧未插入业务反馈或更改门控。review10 ChangesRequested定位REQ4刷新文件页缺精确README.md链接，19/20其它浏览器判据通过；业务修复交生成责任人。资源current约3.42GiB、peak到4GiB，memory.events.max1333/oom0/oom_kill0，不能把触限等同OOM或停止依据。正式新提交与本地运行分别跟进，当前未自然完成/评分。

用户在侧会话明确要求“取消本地运行”。已通过正常Lab stop取消c5f67cce27364908ae06d32417797c11，2026-10-08 11:33:12Z（北京时间19:33:12）精确容器5774c918efc2 exited/Running=false/exit143，非OOM。现有消费者远端完整保存回执remote-result-save.json为stopped、saved=true、errors=[]、snapshot=false；工作区/Braid/native现场保留，Mac完整data回收状态另以保存消费回执为准。i15-github-evo自动跟进已PAUSED。该取消仅作用于本地生成，不启动接续、下一轮或本次停止产物的自动评分；正式运行与历史提交另属主线程。

11:09Z heartbeat消费现有relay至11:10Z：c5仍running，4 active、2 pending batches、1 pending reset、blocked0；原槽位修复后有持续业务推进。PR11组织治理阶段2在11:02交付aef34bf并建review14，生成Agent报告后端105/105、前端43/43、浏览器40/40；PR13基础修复对接后交bb6f0e2，根已指派review13独立验收。review10–14仍pending，PR2/10已合并，尚未自然终态/最终评分。以上应用测试为生成Agent评论回执，不替代最终评分。现有资源样本memory.current约3.75GiB、peak3.81GiB/4GiB，max/oom/oom_kill0；不因临近上限或耗时自行停止。QWEN_TOKEN_PLAN出现429后沿冻结QWEN路径取得HTTP200完整响应，未改配方。只读现有records/status.json及provider-snapshot，无新采集/控制/部署，20分钟跟进继续。

当前执行 **c5f67cce27364908ae06d32417797c11** 已实际恢复并采用槽位修复：10:54:38Z Issue5的Pi idle_unload确认quiescent，children-stop/execution-stop均stopped，逻辑会话保留而物理执行卸载；PR13随后获槽新turn，此前排队的根Issue1/review10也有新turn、成功工具及真实GLM5.3响应。当前4 active/4 reserved是有效复用，不宣称采到瞬时reserved3。source bc正常stopped/saved、原scope e4bdfc、GitHub Evo、本地自费competition=false、临时GLM5.3文本/独立Flash视觉、去ARC、Local4/Vitest1/E2E1保持。唯一supervisor308722/default321632/Macrelay43086，20min heartbeat已更新ACTIVE；自然完成完整保存后由既有独立official/self_funded非参赛消费者取得评分，不因赛事截止取消本地。原件 `runs/iteration15/slot-release-fix-20261008/{notes.md,adoption.json,root-and-reused-slot.json}`。

同host传输优化源码也已完成：正常restart/local executor核精确来源停止CID/同daemon、同task/scope及远端saved回执，new data独立staging cp/reflink完整复制后发布，program/inputs照常装配、只刷新SDK requirements/.arc，避免空Mac工作区模板覆盖继承业务，routing小元数据独立回收。省去后续约5.9GiB远端→Mac→同远端往返，不裁剪恢复数据或共享可写原件。Python语法编译通过，recovery.md同步；当前c5未为优化再次停止，下一次正常接续实际消费尚未验证。以下运输与派发段为本次过程历史。

换模费用口径已完成实际切片：braid_usage.py按scope替换回执producer/applied_at映射文本logical Flash→真实GLM5.3，保留旧Flash/独立视觉。bc保存原件49文件36去重session/4095响应，累计input15,270,872/output1,382,327/cacheRead416,758,208/cacheWrite0，total433,411,407；未把跨接续重复原件相加。ARC10:44Z价表GLM5.3 8/28/2、Flash0.8/2.8/0.23、DeepSeekFlash3/9/0.1 CNY/M，累计可比价¥181.05035624（文本旧Flash99.90008248、新GLM5.3 78.276332、视觉0.04870216、DeepSeek2.8252396），非订阅实付。新GLM5.3 native263响应/35,978,312token；gateway265usage仅作真实模型旁证，未落盘部分未知不补估、不叠加。证据 `runs/iteration15/glm53-cost-slicing-20261008/notes.md`、arc-prices.json、saved-bc9db/usage.json。暂支持本次一个替换边界，未来不同替换需新增边界，不能按最后模板改历史。

槽位修复接续当前身份已冻结为 **c5f67cce27364908ae06d32417797c11**，source bc9db于10:36:48Z正常stopped、远端saved=true/errors=[]，Mac完整保存/新data独立复制已完成。manifest已冻结native_resume=true、scope e4bdfc、GitHub Evo、自费competition=false、Local4和临时文本GLM5.3/独立Flash视觉/native substitution元数据继承。当前program/runtime装配完成、正在正常远端harness上送约5.9GiB；尚未dispatch、无新模型证明。不能将新身份创建称修复实效；实际idle unload/停止证明/queued推进由runtime_owner随后取证。

传输优化判断已收敛：保持现有业务进度，后续正常Local接续采用同执行主机的已保存data独立复制，消除远端→Mac→同远端两次5.9GiB运输；本次已在途运输继续。runtime_owner持restart.py/local_run.assemble最小分支：旧冻结执行器核精确executor/daemon/CID、stopped及saved=true/errors=[]/snapshot=false，new remote_run/data staging cp或reflink完整独立复制，禁止硬链接/直接复用旧data/旧writer复活；小routing元数据正常取得，program/inputs正常装配。不能让空Mac app触发_stage_app模板回填再覆盖继承业务，只按既有规则刷新requirements/.arc。远端saved不冒称Mac完整归档；暂不删output/worktrees/cache/历史，当前没有fresh更快的证据。不为采用运输优化另外重启本轮。

用户最新强调槽位异常需尽快修复，5+GB传输也需优化，可考虑重头但时间紧。当前bc源已正常stopped/saved；既有槽位修复接续运输继续，不抛弃保存进度或并行重启。runtime_owner持实际运输/主要体积来源和normal执行器同host复用能力；lifecycle_advisor独立判断最小远端saved-source复制边界、必须保留的恢复一致性及相比fresh重头的收益。传输优化暂为定位/决策，不绕正常saved门控、旧writer停止或冻结配方。

10:36Z后槽位修复正常接续已受理：完整Linux runtime和锁定E2E addon齐备，runtime_owner唯一执行Lab restart bc9db --keep-data，当前源停止/完整保存阶段，新继承run身份尚未生成。独立LAB_CONFIG采用slot-release runtime，来源冻结catalog/routes及本地临时替换元数据继承；在途期间不得另一消费者重复stop/restart旧bc。终态评分不针对本次主动停止源启动，接续后的自然终态责任保留。

槽位修复生产进展：Arc/Box两接口转发已完成，cargo check通过（约21秒），Linux Braid release及runtime镜像已构建成功，正在导出完整runtime并复用锁定E2E addon。源bc9db此时仍继续生成，尚未stop，避免编译阶段无谓打断。正常同scope接续同时继承已授权native_model_substitution元数据，保留文本真实GLM5.3与独立Flash视觉，不重建默认路由；实际卸载/排队推进采用待下一回执。runtime_owner是唯一运行控制者，终态保存与独立评分消费者随正常restart继承。

槽位异常根因已独立确认：sources/braid/src/provider/util.rs 的Arc/Box<dyn AgentProvider>透明包装漏转发managed_state与yield_stoppable_services，ProviderAgentSession的Arc调用落trait默认Unknown，未进入Pi真实idle_unload检查；can_accept_input有转发，解释input_readiness仍更新但卸载从不发生。advisor与runtime_owner核冻结源码同漏，SQL fence实际eligible，不能继续猜running缓存或后台子任务。runtime_owner持最小两wrapper方法转发、cargo check、当前完整Linux生产与正常stop/save/native接续，继承本轮临时本地GLM5.3文本/独立Flash视觉、原scope/应用/会话、Local4/Vitest1。保留Quiescent、SQL事务fence及物理stop-proof，不伪造DB、不盲kill。实际验收须见卸载查询、原native进程正常停止、槽位授予pending root/reviewer后的真实响应；当前尚未部署。

本次进展查询发现实际槽位释放异常：runtime_owner正常只读取pool reserved4，对应Issue4、Issue6、PR11、PR12；只有PR11有backend node子进程，另外三Pi idle无活子。Issue4/6最新10:24Z native-state明确quiescent/isStreaming=false/pendingMessageCount0，DB也idle、0running turn/0reset，仍占槽，不能解释为普通排队或有限任务阻塞。PR12旧preflight状态不当当前静止证明。runtime_owner持冻结binary卸载路径根因与必要窄修，明确设施闭环后沿正常controller/编译/stop-save-native接续，保持当前本地临时GLM5.3+独立Flash视觉、Local4/Vitest1、完整状态，禁止伪造DB或盲kill。当前根因尚在定位，未宣称修复/部署；主已向用户汇报。

18:21北京时间用户查询只读进展：bc9db仍running。DB确认基础PR2/身份PR10 MERGED，Issue3 CLOSED；组织PR11于10:04Z获依赖就绪/接口与账户菜单移交，进入行为实现。仓库资产PR12在10:07Z提交f7abbc0新候选，生成Agent报告后端90/90、前端34/34和浏览器36/36；review10/11/12分别对应PR9/8/12仍pending。现active_turns1、pending_batches4，多个group报top-level slot queued，blocked0；runtime_owner只读核具体持槽者/有限任务或结果/服务阻止释放，不以can_progress=true即判健康、不控制运行。资源memory.current约3.05GiB、peak3.55GiB/4GiB，anon约0.62GiB/file约2.33GiB，max/oom/oom_kill0，近期内存PSI0；不能将3GiB全归Pi。尚无终态/最终评分，新GLM5.3实际模型已实证采用。

本地临时换模已实际接续：**bc9db51fb77347adb5121cf6087c5cbe**，来源dfa68、同scope e4bdfc124b444524b4b13e4533a22740；旧源正常stopped/saved=true/errors=[]。10:02:29.826Z实际native homes/templates文本逻辑Flash保留但wire GLM5.3；10:02:49Z QWEN_TOKEN_PLAN/glm-5.3 HTTP200完整usage，原04:40 Pi session在10:03:31/39继续工具动作bash isError=false。vision独立ARK Flash alias已读回，未额外模型调用验证视觉。Local4/Vitest1/E2E1、自费competition=false、去ARC保持。容器98ef65bbd1c1；正常supervisor3334520/default3347964/Macrelay89543已接好，自然终态沿既有保存/独立self_funded增量评分。采用入口 `runs/iteration15/temporary-glm53-local-20261008/startup-receipt.json`、`native-adoption.json`、`notes.md`；费用从本producer/applied_at按实际GLM5.3切片，旧Flash历史不改。

最新临时本地换模已实际生效：**bc9db51fb77347adb5121cf6087c5cbe**，源dfa68正常stopped/saved，GitHub Evo、本地自费competition=false，scopee4bdfc/native_resume保留。10:02:29.826Z显式本轮映射应用；10:02:49Z QWEN_TOKEN_PLAN/glm-5.3 HTTP200完整usage；原04:40创建Pi session于10:03:31/39继续assistant和bash isError=false。文本保留原logical alias以延续会话，实际GLM5.3；native homes视觉角色已指factory26-visual/i15-local-vision-flash独立ARK Flash。正式profile和共享默认未改，去ARC/Local4/Vitest1/E2E1保持。正常supervisor3334520/Macrelay89543及default消费链已接起（default具体身份以owner回执为准），heartbeat已更新本身份20分钟ACTIVE；终态保存/独立官方自费增量评分继续。费用须按本次生效边界映射实际GLM5.3，不能照逻辑Flash名计价；视觉本次新图片调用尚未实测，不扩大宣称。详细receipt/notes由runtime_owner写入temporary-glm53-local-20261008。

用户明确视觉分工：“我们有vision sub-agent用glm-5.3-flash应该就行”。当前临时本地自费接续采用文本主生成/审查GLM5.3，vision保持glm-5.3-flash独立路由。为保留原生会话可沿既有逻辑文本alias，但必须记录真实wire模型、变更run/首次生效时间，视觉别名不得落入文本替换链。最终费用须按换模执行边界使用实际模型价表，旧Flash历史不能整体改算GLM5.3，新GLM5.3也不能因native逻辑alias名仍Flash而低估。runtime_owner继续唯一正常接续，不为费用脚本延迟恢复。

临时换模目录核实：runtime_owner正常停止dfa且远端saved=true/errors=[]，Mac运输仍在进行。一次有界models GET确认QWEN_TOKEN_PLAN有glm-5.3，QWEN有glm-5.3及ZHIPU/GLM-5.3，同时仍列ZHIPU/GLM-5.3-Flash，不能把用户怀疑直接判为目录不存在。计划本轮文本主生成/审查采用已确认GLM5.3通道；GLM5.3现native与目录未确认image能力，视觉保留已实际使用的独立路由，不虚称GLM5.3多模态。全部映射仅本地临时冻结输入，需合法route/model变更回执，正式和共享默认不改。目录证据归temporary-glm53-local-20261008/model-directory-curl.json，实际新配方/接续仍待owner回执。

新临时配方授权：用户要求“停止生成并切换到GLM-5.3替代glm-5.3-flash（临时的）”，随后限定“仅作用于本地运行，自费”。runtime_owner持dfa68正常stop/save及本轮独立临时配方/native接续，primary已读状态stopped。仅当前本地自费GitHub Evo的冻结输入生效，保留去ARC、原scope/应用/原生历史、Local4/Vitest1与旧配方恢复入口；不改共享默认或正式参赛材料、不启动其它题/下一轮。最新明确Flash替换授权覆盖旧单Braid-session GLM模型默认限制在本轮原Flash槽上的范围，不向后续轮次继承该临时例外。先核实际供应商模型标识/支持再通过正常route-change receipt接续，不将用户对QWEN Flash支持的怀疑直接写成已证根因。

内部退出/清理修复已正常原生接续采用：当前run **dfa68c905c4a4803a0a3729ef8437387**、源22a576、同scopee4bdfc，task hackathon-evolution--github，本地self_funded/competition=false，去ARC/Local4/Vitest1保持。源正常stopped且saved=true/errors=[]；首装配缺锁定e2e addon在dispatch前失败，已复用公共copy_e2e_addon并保留失败材料，同目标正常assemble/start完成。09:32:04Z实际braid恢复，原4个Pi日期session09:32–09:33有新模型响应和成功工具；远端已安装新I15/sharedcleanup/core/public wrapper/services及当前Linuxmonitor，实际supervisor已采样。唯一remote supervisor2779322/default2791539、Macrelay66550继续自然终态保存与独立official self_funded delta评分；当前running未最终评分，不声称异常路径全已实测。采用入口runs/iteration15/internal-exit-deployment-20261008/adoption-summary.json及notes.md。

最新实际接续：**dfa68c905c4a4803a0a3729ef8437387**，task明确hackathon-evolution--github、本地自费competition=false、scope仍e4bdfc/native_resume=true。来源22a576正常stop/save完整保存；首装配缺e2e addon的失败发生dispatch前，复用冻结同版addon后在同一已迁移目标正常assemble/start，无fresh/重复完整搬运，原件归internal-exit-deployment-20261008/assembly-failure-e2e-addon。新容器f6a4ac8c6f3c于09:30:36Z启动，09:32:04Z进入Braid；原4个Pi日期session于09:32–09:33有新assistant与多次bash isError=false。实际execution_limits=Local4/Vitest1/E2E1，去ARC冻结路线保持。新公共runtime/装配携entry0/sharedcleanup/core保留现场/Rust monitor不主动kill生成entry修复，材料采用回执由runtime_owner收尾；尚未自然结束，不能宣称exit0异常路径与实际评分已验收。唯一supervisor2779322/default2791539/Macrelay66550正常接起保存及独立official/self_funded评分义务；heartbeat已同步此新身份20分钟ACTIVE。Mac产物WorkSSD，无测试/业务直改/commit/push。

用户新授权将内部退出/清理修复正常接续到当前GitHub Evo。runtime_owner已核来源22a576、platform_task=hackathon-evolution--github、competition=false、自费去ARC路由及scopee4bdfc，公共Linuxruntime当前生产完成。独立LAB_CONFIG沿正常restart --keep-data已停止旧writer，正在完整save与原生状态迁移；不是fresh，不修改业务应用或路由。处置/生产/执行记录归runs/iteration15/internal-exit-deployment-20261008/。可能损失在途未落盘模型或工具结果、可能重复消耗，保留来源现场；实际新身份和模型采用待回执，不以源码或编译宣称已部署。

新部署授权：用户明确“请将刚修好的这些也接续上去（确认一下，应该是在运行github-evo这道题）”，覆盖此前本线程先不动限制。已从22a576 manifest/task_config确认platform_task=hackathon-evolution--github、competition=false，本地生成正常running，scopee4bdfc/native_resume=true。runtime_owner持当前完整Linux生产及唯一正常stop/save/keep-data原生接续，采用内部退出0/sharedcleanup/Rust资源监控和公共wrapper新合同；沿去ARC冻结路由、Local4、单测试worker，不改业务应用或fresh重头。先确认无其它在途控制、原writer停止且完整保存，再派发新身份；旧现场/执行切片保留。root持当前身份和heartbeat同步；自然完成完整保存后既有消费者独立official/self_funded取评分。接续新身份/实际模型与工具采用待回执，不把编译或受理当已生效。

09:02Z 心跳仅消费现有记录：22a576仍running，最新cgroup memory.current3115823104（约2.90GiB）/4GiB，max/oom/oom_kill0。业务评论86确认REQ5/6旧review8已Approved，但对接新develop存在seed_db.js实际冲突；负责人保留两方种子、完成合并并冻结c3=410e2d4，报告后端78/78、前端27/27与build通过后发新验收请求。已有有效冲突处理与后续验收，不据耗时/内存增长停止。当前未自然完成或取得最终评分；原保存/独立评测责任继续，无新采集/控制。内部退出0修复owner已完整交回，记录 `runs/iteration15/generation-exit-cleanup-20261008/notes.md`，仅源码/编译采用，当前冻结运行未部署。

内部退出合同源码已完成：共享cleanup_workspace不再因残留PID/信号或检查错误抛异常，保留workspace-cleanup.json具体错误及remaining身份；未证明停止不得回收恢复现场。I15内部异常、非quiescent、根未关闭不再阻断入口；尽力发布既定delivery ref，失败仅回退本run seed，或保留已注入baseline，不猜其他成员worktree。generation_result/partial与entry0分开，不冒充需求完成。公共wrapper保存generation-entry.json并将内部安装/子生成非zero/收尾异常转入口0，外部信号及130/143仍非zero。Rust资源监控已删主动TERM/KILL生成entry与resource-exhausted exit2，保留真实cgroup限额、内核事件、reclaim及失败诊断；monitor/collector/服务收尾错误不再throw阻断。Rust cargo check、6个Python源码及生成wrapper编译通过；无测试/探针/实验/commit/push。证据runs/iteration15/internal-exit-contract-20261008/notes.md。当前22a576冻结入口及二进制尚未采用新合同，遵循先不干预运行，不宣称已部署或已评分。

新开工授权：用户要求去除cleanup_workspace残留PID等内部生成阻断，除外部强制终止信号，生成入口exit0尽可能进入eval。runtime_owner持共享cleanup及I15生成/交付出口；metrics_owner持资源监督主动终止及服务start/close异常；root持公共wrapper出口和因果采用。内部失败保留具体错误及generation result，exit0不伪报业务完成；保留官方真实cgroup限制/外部信号及历史证据。当前先完成源码/编译，不抢控或部署现22a576。公共wrapper已将普通内部异常/child非zero与entry0分开并保存generation-entry.json，信号及130/143终止出口仍非zero。其余修复在途；未运行Factory/Braid测试或新实验、未commit。

08:47Z 只读核对：22a576仍running，cgroup memory.current 2512084992（约2.34GiB）/4GiB，max/oom/oom_kill0；本轮未控制、部署或修改源。runtime_owner已定位review5/7连接中断评论为误告警：两者先有效Approved，再明确closed/unassigned请求teardown，约2秒旧running turn记interrupted，worker通用分支未区分责任完成后的主动收口。验收结果未丢失，不是serviceyield故障；证据 `runs/iteration15/github-evo-prompts-20261008/review-terminal-noise-20261008-0835.md`。误告警修复尚未实施，遵循用户本线程先不动，不据此重启。业务评论83显示另一候选PR13原Approved的冻结base因PR10合入失效，负责人已要求merge最新develop、联合复验、重新冻结，属于实际候选适用性约束，不直接干预或凭此停止。review8也出现同类系统评论但尚未逐项确认原因，随后08:45已有新turn；不将它自动归为相同已证原因。尚无自然终态或评分。

08:32Z 心跳只读采用：22a576 正常 running，最新既有容器监督 memory.current 2324234240（约2.165GiB）/4GiB，memory.events max/oom/oom_kill 均0；不将 Docker 扣缓存后的1.375GiB等同cgroup占用。真实业务新进展：PR9冻结4bc25fa交验；08:30:50评论82报告身份PR10经review5 Approved合入develop（merge072bfef），生成Agent报告后端70/70、前端19/19和浏览器REQ1旅程，尚无最终官方评分。review5/7出现interrupted与连接中断系统评论，均已有后续新turn/责任动作；runtime_owner仅消费既有证据解释正常服务交接或设施错误，禁止抢控/部署。ARK出现HTTP429后正常走冻结QWEN路由HTTP200，不改配方、不以429或用量单独停止。原件当前run records/status.json及provider-snapshot；未新增采集/实验/控制。

07:52Z 心跳纠偏：用户明确“是，它在更新，你不必动先”“它正在接续”，本线程暂不控制、替换或主动部署验证，避免与 runtime-performance 的正常接续冲突。其在途新 Lab 身份为 **22a576d946f0460cb235908a74366cce**，来源 ea119、keep-data、保留原 scope；已读配置 Local4，runtime 含服务交接与 MCP 隔离修复，实际调度/单 worker/资源反馈仍未验收。接续操作与采用证据由 `tasks/runtime-performance/packet.md` 的当前负责人持有；下面 ea119 与旧 supervisor 身份属于接续前历史，不能再当当前执行目标。现心跳只读核对交接，不发起第二条恢复；最终保存与独立评分义务仍保留。

2026-10-08侧会话本次接续已完成：来源ea119正常stop/save（saved=true、errors=[]），新Lab **22a576d946f0460cb235908a74366cce**、scope仍e4bdfc/native_resume=true/competition=false，冻结去ARC路由未改。当前I15与资源采样2cca0d0f通过公共Linux生产采用；Local池实际max4/reserved4，4个原native session已有新assistant和成功工具，gateway已12个terminal complete。正常observer583161/default595003/Macrelay81898已启动，原终态保存/独立评测义务继续。资源初始41样本最多20进程，新worker/PSS覆盖/CPU-I/O/事件日志已产出，collection中位12.787ms/最大188.500ms；未验证长期轮转/OOM。接续及采用证据归tasks/runtime-performance/packet.md、runs/runtime-performance/i15-adoption；下面ea119为历史，避免发起第二条接续。

当前实际执行已切换为 **ea119b6b8a50435cbb68ae9fcda93d4d**（scope仍e4bdfc/native_resume=true）。07:31:17Z进入原scope，8保留原生session有新assistant+成功toolResult，首实际模型attempt直接ARK_CODING_PLAN/ark-coding-plan-glm-5.3-flash HTTP200 complete（request1 total69421），ARC=0新配方实际生效，不是402后fallback。唯一consumer4165669/default4179210/Macrelay57658及终态save/独立self_funded评分闭环正常；原b32/44和4b装配失败均保留。采用remove-arc-native-adoption.json及相关receipt。新Local4/Hosted2agent池、Vitest1worker及显式serviceyield仍源/公共生产在途，本次旧binary不冒充池已生效。

并行方案开工与最新容量修正：用户先明确选“两种环境均允许两Agent”，授权统一顶层Braid并行池+测试1worker，并闭合服务/槽位释放；随后表达2GiB可2~3、4GiB可4~6并希望本地实测。当前采用区间低端Hosted2/Local4，按本轮真实Github生成/应用验收和容器PSS/anon/file采样验证后再判断3/6，不做Factory/Braid测试或探针，不擅新多轮benchmark。metrics_owner持Rust run冻结max_active_agents（默认无限供其它variant）、assign显式queued/clone及Pi启动前reserve、真实cleanup后release；runtime_owner持I15新建/恢复request明确数值与共享验收runner预算、公共生产/接续。后台test/subagent/pending results阻止提前还槽；仅登记且明确可停止/下轮重启的service交接机制待实际接口判断，不按命令regex/RSS猜杀。当前ea119旧binary未消费cap，新措施不能仅source方法即宣称已生效。

去ARC正常接续已建立 **ea119b6b8a50435cbb68ae9fcda93d4d**，44已正常stopped/saved，现完整data复制/装配，尚未模型。过程中Mac openrsync delta-basis fmap_data断言，保存原失败收据；仅save传输加--whole-file并正常重收成功，不跳saved门控。新run路由变更Lab receipt和I15既有合同双层核对，ARC=0、alias/其余顺序保持，实际proxy采用待dispatch验证。

用户更正并行提议为agent并行量、不区分Issue/PR，询问更合理策略；原Issue组备选已撤回为用户早期不完整表达。当前方案评估统一顶层Braid实际执行池，logical assignment可显式排队，后台子agent/测试计父槽，静止/cleanup/stop-proof后还槽；服务等待review导致持槽死锁是必须解决边界。advisor已核PR11 backend全套Vitest5文件与PR8 seed单文件实际重叠，两config无maxWorkers/fileParallelism，v4.1.11；可考虑测试worker预算为补充，不夸为两套都大量CPU workers，不使用Node --test参数套Vitest。未授权具体并行cap实施，当前去ARC接续继续。

用户新内存线索与待评估方案：本地14:20:13PR11完整后端测试、14:20:30PR8种子Vitest、14:20:38reviewer7启动、14:20:41达4GiB、随后回3.88；两测试后台>30s重叠，PR9beforeEach超时相关未证内存因果。memory.events.max6804/oom0/oom_kill0，pids约620含线程，不能称620进程。应追本地并行验收叠加，区别Sheet整批启动0turn驻留。用户提议考虑Issue并行量：满后仍assign，agent group/session等槽再创建；这是待设计，非已授权固定cap实现。advisor持Issue执行group/PR/reviewer/多关联/根基础及等待释放边界、避免死锁与最小可验方案；runtime_owner去ARC接续继续，不恢复proxy请求gate或笼统归Pi数量。

去ARC执行决定：现冻结proxy仅启动一次config::load→Arc<App>，无reload/SIGHUP/每请求重读，单改inputs不生效。现有执行器无同host clone快速入口；不造热部署或绕停止证明。按用户明确改配方授权现在正常stop/save/native接续，保同scope应用/Git/Braid/native、alias/模型及其余通道顺序；新增显式route变更入口只持此次明确变更，不无条件放宽身份。保留旧/新配方、各slice及在途损失。此前44已恢复有效，接续需再同步约4GB及installer约90s；若公共生产可迅速组成含已编译新Linux二进制的完整runtime，则一并采用materialize修复，否则配方实际生效优先，不手工覆盖冒充公共生产。新route实际采用/新身份待回执。

最新配方变更开工授权：“可以更换配方，把 ARC API 去掉”。移除本轮I15自费有序路由的ARC API，其它已授权通道保持原优先序/模型与受限Braid会话规则。当前44c169已实际恢复：7原provider路径resume，PR8原resume_count1→2，06:57Z后review5/review7与PR8/9已有assistant和成功bash。ARC主路由HTTP402 insufficient_balance后旧冻结链正常转ARK_CODING_PLAN；新移除ARC改动待runtime_owner核正常代理/执行器后续消费能力，尽量保住当前恢复，不伪称已移除。唯一supervisor3441113/default3457438/Macrelay31306，正常监控接好；采用控制根accidental-delete-native-adoption.json。

当前误删恢复接续身份更新为 **44c16936e8494ff39327189fe6db2b89**，native_scope仍e4bdfc124b444524b4b13e4533a22740、native_resume=true；装配和同点完整data复制已完成，正远端dispatch，尚未container/模型回执。之前4b285…因共享target已被其它维护改回旧I14 runtime、producer校验retry补丁不匹配，在派发前失败，无模型/数据丢失；保留失败原件。当前采用隔离原sfp7配置和原runtime-no-slots-15m，不放宽校验/改别人target。新单项materialize Linux release已编译（约1m15s）并归档，但仅binary、不延迟恢复重组完整runtime，本次不冒充已消费此修复；采样Python公共修复由正常装配实际采用边界待原件核。

误删后正常接续已建立新Lab run **4b285eba77994d47b08f8cfabc6eba7c**，source=b32cdb、keep_data=true。来源完整正常save同步已完成，现复制已保存data并装配，尚未dispatch/实际模型恢复，native_scope待最终输入核对。原数据和所有run保留，无hidden反馈、新baseline或配方变化；Linux交错修复并行按已有缓存编译，不阻塞先用可用冻结runtime启动。

用户新确认并恢复授权：“另外一个会话跟我汇报它不小心删错了”“你尽快接续或者重头开始也可以”。b32退出不是本轮已知OOM：Docker事件06:22:18.871664889Z kill signal9→die137→destroy，删除来源以用户确认的其它会话误操作为准，不再耗时追归因。远端data/workspace、data/harness/e4bdfc和snapshots仍在，正常saved=true，容器删除不等于应用/会话删除。runtime_owner立即优先正常Lab原生接续同点Git/Braid/native，材料不足或正常入口受阻则允许同官方完整baseline fresh重头；保留全部旧现场/身份、同self_funded有序配方/模型会话约束，不继承隐藏反馈。当前新run待回执；能快速生产新Linux runtime则消费已修单项materialize/容器采样/e2e路径，若编译长阻塞则先用可用冻结恢复并明确未采用新源，不为部署重复无谓停机。

06:05Z heartbeat：基础PR2 review3于05:53:11 Approved，根comment49确认已合develop（merge a4f34de），业务开始对接。PR10旧review1于05:52 ChangesRequested针对alice-dev种子缺口，实施者已修并合基础，06:06交新head c267e47，review4 pending；PR12 review2仍pending、保持冻结后再对接。根05:59建PR13/glm13承接SPA dotfiles及busy_timeout基线修复，业务由生成Agent处理，开发侧未直接改应用。06:06:17Z active7/pending3，近期无provider error，未自然终态/保存/评分。Sheet06:01 SSL查询失败后consumer仍存活，按下一定期轮次继续，本heartbeat不重复查询/下载；首用量不当最新累计。正常继续、不控制/新采集，采用GitHub控制根progress-0605.json。

当前实际执行身份：原生接续 Lab run **b32cdb6bef5e42cf84de7888cadd53c4**，native_scope 仍 **e4bdfc124b444524b4b13e4533a22740**，native_resume=true。当前控制目录为 `runs/iteration15/github-evo-prompts-20261008/lab/runs/b32cdb6bef5e42cf84de7888cadd53c4/`。原 fresh e4bdfc 和中间4fcafcb已正常停止、完整保存；本轮未结束，不是新实验。下面启动和修复段按时间保留历史，下一次跟进消费此当前身份。

用户开工授权原话：“先这样吧，我们处理好提示词里面关于 issue 拆分、braid 使用的冲突、混杂、冗余就行，然后启动本地运行，观察情况，不再继续猜测。”本轮只收敛已确认重复与冲突，再用实际生成观察；不扩展多 Issue 验收产品方案，不改变多关联接口。共同基础先交付、业务顺序实施仍是有效安排，业务实施前需有对应子 Issue 负责人。名字机制说明自然提供下一成员，不构成名称人数/并发上限，实际模型与执行资源限制另遵守；已落地的显式自动结果继续采用。

root 持 I15 profile 和共享技能归属：root/fast 只留本配方基础/整合、业务子 Issue 政策及方法指针，删除与 RUN_CONDITIONS 重复的 reviewer 生命周期段；持续跟进缩为根责任与独立核查方法指针。reviewer-only 不加载 RUN_CONDITIONS，其独立角色约定保留。共享 braid-collaboration 持业务结果责任、PR 关联和实施顺序的组织方法；arc-bench 持原需求结构映射，不复制 Braid 机制。runtime_owner 持 provider 原生机制、run.py 公共条件/进展触发简化、生产材料与新 Linux runtime，以及新 Lab fresh 启动/observer/default/Mac relay。根材料已稳定交回，不再做根因推测或策略扩展。

新控制目录 `runs/iteration15/github-evo-prompts-20261008/`，SFP7/WSL fresh 原生 scope，从同官方完整初赛基线与允许需求启动 GitHub Evolution 自费生成；同有序模型配方与既有模型会话约束，不继承旧生成业务/会话或隐藏评分。启动后以真实模型请求、基线数据和 physical 指令确认采用，再有界读实际工作项与后续动作；不因串行或基础未完成时尚无业务 Issue 判失败。后续消费原 observer/default/relay，无新采集器，终态正常保存后沿既有独立 official/self_funded、competition=false 增量重放。保留旧 run/评分，不取消其它官网运行，不设人为费用或时长停止线，不测试 Factory/Braid、commit/push 或 overlay。新 run 身份与实际启动反馈在途；heartbeat 待冻结身份后恢复。

已完成公共 Linux runtime 实际编译及当前材料装配。首启动 `527e033…` 在 assemble 缺 runtime/e2e 组件时失败，容器与模型尚未启动；沿既有独立 e2e 组件入口补齐后正常 fresh start，新 run/native scope **e4bdfc124b444524b4b13e4533a22740**，native_resume=false、competition=false，正在 SFP7 dispatch 完整新 runtime/材料，首模型反馈在途。源与方法实际材料读回见 `material-adoption.json`，不把装配当作 Agent 采用。heartbeat `i15-github-evo` 已指向新身份恢复 10 分钟消费节奏；仅按实际业务责任缺失事实判定，不因基础尚未完成或串行停止。正常终态/独立评分消费者仍由 runtime_owner 接续。

实际启动闭环已完成：02:31:48Z 首 GLM-5.3-Flash 完整响应，read/bash 成功；真实根工作区保留 14 users、28 sessions、2 repos、25 issues、14 PR。physical 指令实际取得简化职责/子 Issue 分担、自然下一候选和当前业务子 Issue 配方政策。02:32:34Z 一次有界根观察明确计划 create sub-issues for business capabilities, create PRs，仍在调查基线/完整需求，仅初始 Issue1，不将计划视为已拆分。supervisor 1175887、default 1188005、Mac relay 7856 已实际启动；完成保存与独立官网增量评分消费者有效。启动采用证据归新目录 `startup-adoption-summary.json`、`physical-input-readback.json`、`root-current-step.json`、`operation-notes.md`。后续按已有 heartbeat 消费事实。

用户补充 pi-minimal 已定位的 e2e 会话错配：mcporter 以完整 child environment 确定连接，open 后新增 E2E_SESSION 会切换 server，旧正确 ID 因进程内 Map 不共享而 NO_SESSION；重复 open/省略 session/错误文本误读及正则又放大循环。根已确认新 run 冻结 `inputs/variant-material/skills/e2e/SKILL.md` 22–28 行及 `references/mcp-session-lifecycle.md` 已采用共用修复：同 attempt 环境/config/cwd/command 固定、ID 只在 payload、显式 session、CLI exit/isError 处理、locate 与 finally cleanup。无需再复制指令或改 mcporter 全局身份算法。runtime_owner 仅核远端实际技能消费与已有同类错误，正常继续，不为该报告停止或新增实验；“材料已包含”与“Agent 已正确使用”分别判断。

远端采用确认完成：work/skills/e2e 指向 /workspace/submission/skills/e2e，实际 program 正文含上述共用指南；mcporter 0.14.0 / E2E 0.15.1 保持原完整 env/command/cwd 连接身份，call-command 仍将原始 isError 转为 exit1。截至 02:35:35Z 根唯一会话尚未调用 E2E，无 NO_SESSION、槽满或 NoneType；这只证明当前没有错误、材料可用，不证明已经成功验收。无需新 source 修复、提示注入或停止。证据 `e2e-runtime-notes.md`、`e2e-remote-adoption.txt`、`e2e-runtime-activity.json` 归新控制目录，继续正常观察。

02:42:44Z heartbeat 有界读回：仍只有根 Issue1，唯一根 turn running；根 02:38:58 已实际读 organizing-work，02:39:56 在目录仅 glm-2 后明确说明可创建多个业务子 Issue，后续自然采用 glm-3、glm-4，容量误会此时未复现。02:41:39 成功检查 seed_db.js，正比较完整需求树与基线 schema/routes/seed，后续计划 packet/develop、业务子 Issue 和关联 PR，尚未创建实际业务项。最近工具无具体错误、全会话无 E2E 操作；已知 missing program/status.py 仅可选摘要缺口，不修造旧脚本。正常继续、不控制或注入，保持早期 10 分钟节奏至实际业务责任建立。采用证据 `root-progress-0241.json` 归新控制目录，不将计划或理解正确当作拆分已兑现。

02:52:04Z heartbeat 有界事实：仍仅初始 Issue1，尚无业务 Issue、PR 或自动指派回执；02:47:00 根成功发布 develop，02:48:29 开始形成共享需求解释、基础设计与 packet，02:50:31 成功写入六模块 requirements-interpretation，覆盖增量、存量保持及权限共同约束。属于正常设计形成，未见基础完成后绕过业务责任的事实。现 observer running、1 active，近期工具成功，无 provider error/blocked/reset 或 E2E 调用；继续运行，保持 10 分钟观察，不控制或注入。采用入口 `runs/iteration15/github-evo-prompts-20261008/progress-business-items-notes.md` 和 `progress-business-items.json`；未新增采集器，尚不能按业务责任形成恢复 30 分钟。

03:02:01Z heartbeat 实际新增基础 PR2，关联根 Issue1，负责人 glm-2（active/generation1）；03:00:18 创建成功，共同 schema/access/seed 范围明确，业务页面与流程留给业务子 Issue 关联 PR。基础独立 Pi 会话已读取设计、packet 和需求开始工作。根 03:01:20 明确准备创建 5 个业务子 Issue，使用 --parent 1、旧候选 glm-2 自动采用下一成员，已写 REQ1/REQ2 正文；此切片数据库尚无业务 Issue，自动指派结果未出现，不将计划当作责任已建立。现 observer running、gaps 空、近期工具成功，无新设施错误；正常继续早期 10 分钟观察。采用入口 `runs/iteration15/github-evo-prompts-20261008/progress-0301.json`、`progress-0301-notes.md`，没有新采集或干预。

03:11:57Z 已实际建立并指派五个业务子 Issue3–7（parent Issue1、generation1）：REQ1→glm3、REQ2→glm4、REQ3→glm5、REQ4→glm6、REQ5/6 合同核对与补齐/reactions→glm7。后者基于已有较完整基线合并承接两个模块，不是遗漏 REQ6；每项要求组织 develop 上关联 PR。当前实际 PR 仍仅基础 PR2→Issue1，业务 PR 尚未创建。03:07:27/44 真实 CLI 明确返回自动 glm2→glm3/4/5/6/7，无拒绝后重查。有效业务责任已建立，heartbeat 已恢复 30 分钟 ACTIVE。采用入口 `progress-0311.json`、`progress-0311-notes.md`（新控制目录）。

03:13:18Z 设施错误恢复边界：本切片 37 个 HTTP503 queue_timeout/model_proxy 与 2 个 terminated。基础 glm2、业务 glm3/6/7 在 03:12:18–03:13:08 有成功新模型与有效工具；根 glm1 最后 03:10:28、glm4 最后 03:09:33、glm5 最后 03:09:14 queue_timeout 后 idle、最近 turn failed，未有后续成功或持续新错误。不能把部分恢复说成故障已根治。runtime_owner 继续持有冻结生命周期正常重试/接续的有界核对，未改路由、控制或业务；已有授权仅在设施根因及范围明确时修复。原文/实际恢复边界归 `provider-errors-0311.json`、`recovery-boundary-0311.json`、`turn-recovery-0311.json`，不新增采集器。

03:15:39Z 已定位设施因果链：冻结公共 proxy 为 active=4、waiting=4、queue_ms=5000、total=600000ms；7 个实际责任同时发起模型请求时，在取得 active 前本地排队 5 秒先返回 503 queue_timeout，非上游 HTTP 错误，03:15:35 仍再次发生。Braid 同 wake batch 失败仅重放一次；根 5 分钟 idle 提醒已 03:15:30 在原 session 正常启动，业务 Issue4/5 无独立周期重试。runtime_owner 提议保留容量/配方，让已 admission 请求在既有总期限内排队，再正常 Lab 保存/原生接续消费修复。advisor 正判断此设施等待预算边界与恢复风险；runtime_owner 核实 total/queue 语义、同一保存点及 failed 责任唤醒，当前未 stop 或改冻结配置，不把根提醒触发当作所有责任恢复。

本轮设施处置决定：advisor 确认重复本地排队故障应现在修复而非等待。已授权 runtime_owner 完整执行公共唯一配置修复、正常 stop/save/native 接续与实际采用验证：active4/waiting4/模型配方保持，queue_ms 使用既有 total600000ms，排队与请求头/流读取共同消费接纳时总截止，不重新赠予上游 10 分钟。沿既有本线程设施修复授权，不新实验、不测试、不改应用/数据库伪造状态。动作可能中断正在进行的模型输出/工具，丢失尚未落盘内容或重复部分模型消耗；保存现场及版本、同一应用/Braid/native 恢复点，若不足不宣称完整原生恢复。当前 failed4/5须依执行器支持的接续/正常事件取得有效后续，不无限重试。验收分别看冻结配置实际采用、排队超过5秒后的成功响应和原失败责任有效工作；进程running或无排队请求成功不足以证明根治。具体停止保存与后继身份由 owner 记录回传，当前既定实验未结束。

用户随后明确扩大设施修复：“model-proxy 设置了请求槽这样的上限？如果是的话，请移除，还有相关不合理的限制、门禁也请移除。根的自动提醒机制也要改进了，建议增加为12~15分钟。”这条直接开工授权覆盖此前保留4 active/4 waiting的决定。runtime_owner继续持唯一owner：移除实际请求路径人为容量/准入拒绝，按相同导致无意义拒绝及重采样的机制排查相关门禁；保留权限、数据安全与供应商真实失败，不能扩成无限重试或换模型。根自动idle提醒选择15分钟，区别于本线程30分钟heartbeat；核实际唯一触发及活跃turn不重复唤醒。advisor对相关范围提供判断，不复核实现或重复请求授权。

上述旧等待预算修复已正常停止/保存 e4bdfc（saved=true/errors=[]，包含data/workspace、data/harness、records），原生接续 run **4fcafcb05a7c4f0ea860c043a26f4209** 实际启动，native_scope仍e4bdfc，真实配置仍active4/waiting4/queue600000/total600000；不是新实验或fresh业务。新supervisor2469900/default2486063/relay20156有效，Issue3/6/7原会话resume_count1，基础保存时合法reset沿其继续，Issue4/5仍待正常事件唤醒。旧4槽修复尚不按根治结案，立即转用户新授权继续修复与正常接续采用。证据 `queue-repair-notes.md` 归新控制目录，旧运行与全部现场保留。

用户新范围已落源码：删除 proxy 请求 active/admission/queue semaphore 和连接达到16直接关闭 socket 的门禁；公共 prepare 不再产生 active/waiting/connections/queue 配额字段，旧冻结字段仅兼容读取、不影响行为，不新增替代队列或重试层。保留鉴权/隔离/合法性、网络截止和真实供应商 HTTP/SSE 错误；上层 gateway/Lab 未发现另一套同类槽。根唯一 idle 触发 objects.rs 改900秒，活跃turn/pending判定不变，正常事件不延迟。新 Linux proxy release 编译已成功，公共 Braid/Pi runtime 正实际编译（git2阶段，无编译错误）；首构建入口路径错误已保留并用真实 tooling/scripts/runtime.py 接续构建。当前4fcafc仍正常工作，材料齐备后按正常执行器再次完整保存/原生接续，不将源码完成或proxy编译当作已部署。

无槽与15分钟提醒修复已实际部署：新接续 b32cdb 于03:35:08Z dispatch、正常restart exit0，同scope/native_resume。实际proxy config无active/waiting/connections/queue，保留原网络deadline；编译采用根idle900秒。新gateway切片峰值8个重叠上游attempt、20请求完整完成，未出现admission_limit/queue_timeout。原Issue4 Pi session于03:37:31Z、Issue5原session于03:36:47Z取得新模型toolUse和isError=false工具，原失败责任已有效继续。未观察超过16连接，不宣称连接高并发实测。唯一supervisor2809171/default2822768/Macrelay23529正常接起保存/独立评测闭环；heartbeat已指向b32cdb并保持30分钟ACTIVE。旧现场及两个完整save回执保留，无测试、业务直改、commit/push或新实验。采用入口 `no-slots-resume-summary.json`、`no-slots-actual-adoption.json` 与 `queue-repair-notes.md` 归新控制根。当前正常生成继续，费用需后续按三执行切片原生边界去重，尚无本轮终态或评分。

03:43Z heartbeat：全部业务实施责任已实际建立，Issue3/4/5/6/7分别关联 PR10/11/12/9/8，实施负责人glm10/11/12/9/8；原失败Issue4/5已创建PR11/12并发布方案和packet。根处理共同种子裁定和业务交接，未将业务重新吸回基础PR。当前8个活跃turn，无新failed turn或可行动设施阻塞；两条局部路径/grep命令错误原文保留，不声称均已自行修复，也不由开发侧干预业务。当前运行正常继续，维持30分钟消费已有记录，不新采集/控制。采用入口 `progress-0343-notes.md` 归当前控制根；尚无自然终态或评分。

用户新增 pi-minimal 触发性能调查：怀疑 subagents 插件不把 description 放入 system prompt，并再次要求参考 matt-skills 的触发/加载。已重读 writing-for-agents 与 SKILL-MECHANICS；此处“性能”指合适场合可靠选择角色、后续取得必要材料和行为采用，不是加载毫秒或目录大小。当前直接缺口：公共 runtime 已有受 FACTORY26_SUBAGENT_CATALOG=1 开启的共享 before_agent_start hook，仅 I15 launcher 设置；pi-minimal/pi-minimal-vv 加载同扩展却未设置，因此当前源码正常启动也无角色元数据目录。runtime_owner 复用现hook补两main.py接线，核真实父元数据及调用后角色/技能装载边界，不扩写description或复制正文，不启动模型/部署/实验，不影响当前I15生成或另一线程正式包。角色description已提供“重要决定形成前、反例或反复失败”两个分支，触发效果须留给真实决策行为判断，元数据可见不等于效果已改善。

pi-minimal catalog接线收尾：两main.py启用共享hook并同步README，Python语法通过。复用原生Pi ExtensionRunner零模型before_agent_start实际读回：两父prompt保留原文、仅追加advisor名称和当前description，errors=[]，无builtin或角色/技能正文。compact subagent工具description只指action:list及通用方法，无variant角色元数据，所以旧缺目录确实有发现断点。旧pi-minimal-vv-final.zip的launcher无flag且runtime无hook；本次源码修复只由采用当前公共runtime和新launcher的后续装配消费，未热改旧正式运行。子调用原生execution/pi-args提供角色正文和指定技能metadata，正文按需read；本次无子模型调用，不宣称角色技能实际阅读或决策触发改善。采用入口 `runs/iteration15/minimal-catalog-adoption-20261008/notes.md`、`extension-runner-readback.json`、`source-consumption.json`，无构建/部署/模型/测试/commit。

04:13Z heartbeat 正常生成：PR8已发布第一阶段，PR9前端14项生成应用测试通过（非开发侧Factory/Braid测试）；PR10正自行处理 SQLITE_ERROR: no such column: id，PR11已委派前端实现，PR12持续修改。根完成共同种子裁定，基础PR2仍实施。3次网络流超时均已有后续有效动作，无新failed责任或可行动设施阻塞；不直接修改业务或因局部错误停止。尚无reviewer请求或本轮终态评分，原保存/评分消费者正常等待。继续30分钟既有事实消费，无新采集/实验/干预；采用 `progress-0413-notes.md` 归当前控制根。

04:43Z heartbeat 首次独立验收开始：PR10冻结候选6b70712，由reviewer-1在独立工作区执行后端40项生成应用测试通过，前端验收在途，尚无结论。PR11已交付页面骨架与25项组件测试，其它业务PR和基础PR2继续实现/验收准备；根正常核查讨论，无重复回执。新增3次terminated均有后续成功工具动作，无可行动设施阻塞；当前running，保存/独立评分消费者正常等待，不控制或注入。采用 `progress-0443-notes.md` 归当前控制根；上述测试均生成应用负责人执行，开发侧未跑Factory/Braid测试，未取得终态或本轮评分。继续30分钟已有事实消费。

04:51Z用户询问进展有界采用：PR2基础正在查修 unknown user bob-reviewer 种子错误、未ready；PR8第一阶段发布、reactions等基础合入；PR9真实浏览器验收；PR10候选ready、独立review pending、后端40项通过；PR11页面骨架与25项测试交付、等基础接口；PR12持续实现/验收、子任务刚完成。根已核对验收和依赖，目前主要阻点是基础PR2与首个review未完成，无新failed turn或明确设施阻塞，正常继续；尚无终态/官网评分。采用当前控制根 `current-progress-notes.md`，含token执行切片边界，不因局部业务错误干预或停止。

05:13Z heartbeat：基础PR2已ready（8c8e77a），根安排独立review3；仓库PR12已ready（bd354962）进入review2，连同身份PR10共有3项并行独立验收，尚无结论。PR9继续真实浏览器验收，PR8/11等基础合入再推进后续阶段。部分reviewer自行纠正服务启动/E2E命令，暂无明确设施根因或新failed turn，不把使用问题猜作SDK故障、不直接干预业务。当前run及终态保存/独立评分消费者正常继续；采用 `progress-0513-notes.md` 归当前控制根，继续30分钟既有事实消费，无新实验/采集/控制。

## 当前实施：保留多关联并收敛提示（2026-10-08）

用户随后澄清：“一个 PR 关联多个 Issue 是可以的啊；不过什么叫‘验收时再选择其中一个’”。此前把工作组织关系当作每个 PR 只能关联一个 Issue，是开发侧误读，刚加的单关联 create/link/unlink/request-id 硬约束与相关文档/help/原生指令正在由 runtime_owner 完整撤回。根已同步共享技能与 I15 材料，保留多关联；不新增主次关联或归属字段。单关联实施原证据保留为已撤回路径，不再作为当前合同。

当前有效改动仍是简明 assignee 容量机制、通用 Issue/PR 职责和拆分方法去冗余，以及 I15 根承担基础/整合、按原需求能力建立业务子 Issue 的配方政策。基础先完成、业务 PR 顺序推进仍符合预期，业务开始实施前需有对应 Issue 负责人。一 Issue 可多个 PR，一 PR 可关联多个 Issue；关联不代替实际结果责任。现 review request 绑定一个 Issue 的正文/责任身份，多关联时 --issue 选择本次验收责任，不代表其它关联要求自动被验收。实际范围与权限机制继续取证说明，不自行推导新的验收产品方案。旧 request 的 Issue 失去关联时反馈不适用这项独立修复由 runtime_owner 核对保留；不移动或猜测验收责任。撤回后编译及真实多关联操作、材料读回在途，不继续生成或启动新实验。

已核实现验收机制：request_review 保存一个 issue_node_id 和该 Issue 正文 revision/body/digest；默认责任为该 Issue 当前负责人，可由其指派专门 reviewer。专门 reviewer Context 取得该 request 冻结 Issue 正文、源 PR/Issue 读取入口和请求评论，并非全部关联 Issue 的冻结快照。PR 实施 Context 则取得全部直接关联 open Issue 的上下文，closed 项仅引用。reviewer 可以沿 PR 取得其它关联义务，但现机制不自动冻结或统一验收全部关联 Issue；--issue 不是官网测试选择，也不是关联数量限制。用户本次问机制含义，不据此自行新增主次关联或多 Issue 验收合同。

澄清后的收尾已完成：Mac 编译通过，真实 create --issue 1,3、追加第二关联和移除最后关联均恢复原接口；实际 PR Context 含两项 open Issue，review Context 仅含选择 Issue 的冻结正文与相关入口。当前角色/技能装配读回完成，无测试、模型、overlay、部署或 commit。采用入口 `runs/iteration15/github-evo-fixes-20261008/multi-issue-clarification-notes.md`、`multi-issue-clarification-receipt.json` 与 `multi-issue-public-material/multi-issue-readback.json`。简化提示和成员机制保留，实际生成采用尚待后续授权运行，不宣称已保证模型会按预期创建业务 Issue。

### 已撤回的单关联解释与实施记录

用户明确：“应该一方面修好 assignee 容量误会，另一方面要简化关于 braid、issue 拆分的多个散落的提示词，而且重点是避免他们互相冲突”；“一个 PR 一个 Issue 是 braid 的根本性体验……一个 Issue 也可以有多个 PR”；“基础 PR 统一共同部分，再顺序推进业务 PR……是我们希望看到的”，担心基础完成后不建立业务 Issue。此次指示作为实施授权，不继续原模型运行或启动下一轮。

采用的职责关系是每个 PR 属于一个 Issue，一个 Issue 可组织多个 PR。根 Issue 持共同基础、跨能力约束与最终整合，基础和整合 PR 属于根；独立业务能力由业务子 Issue 承接，其实现 PR 属于该业务 Issue。基础先实施、业务顺序推进是有效安排，不等于业务责任可以省略。root 持共享协作方法、arc 来源指针与 I15 profile 简化；runtime_owner 持 Braid 原生职责/容量说明、实际接口与文档，以及编译和真实操作反馈。技能保留独立正文，profile 只保留配方政策与方法入口，不复制拆分方法。

advisor 发现实际接口仍允许 PR 多关联、验收再选 Issue，与用户归属关系矛盾。因此本轮新建 PR 只接受一个归属 Issue；重复原关联幂等，不能新增第二归属或移除最后归属。同一 Issue 多 PR 保留。复用现 association 事务边界，不加归属表、主次关联模型、历史迁移或唯一索引；历史多关联现场保留可读及明确验收选择。历史明确 unlink 收敛后，已保存 review 的 Issue 若不再关联，旧结论不能仍被认定适用；请求身份与历史结论不改，不自动移交或取消 reviewer。真实操作确认上述关系、request-id 参数一致性和验收归属，编译与材料读回；不编写/运行测试，不 commit/push、overlay、模型或评分。

## 当前诊断：六个业务 Issue 构想为何转为 PR（2026-10-08）

用户要求进一步定位，区分没有拆分意图与计划尚未执行。本次只读取停止现场的原始根会话、实际指令和材料；runtime_owner 持完整两根会话与生成文档轨迹，root 核对冻结职责/技能，advisor 持因果判断。不改源、不继续运行，不用修复后的材料推断旧 Agent 收到的指令。

新原始证据修正此前仅看最终正文的判断：首根 session 第 42 行（01:05:23Z）明确提出 Create business Issues/PRs，并按 REQ-1～6 列 Issue A～F。随后同一条完整 reasoning 引用配方“相应 Issue/PR”，担心多个 PR 修改 schema、seed、routes 冲突，转为基础 PR 提供 ALL modules 共同 schema/helper，再顺序推进 business PRs；这发生在 assignee list 查询之前。第 45 行（01:05:44Z）才误认只有 glm-2，进一步固化六业务 PR/全 glm-2 串行。后续 packet、coverage 和根正文均保留六 PR，未见创建子 Issue 的调用或明确延后创建六 Issue 的承诺。reset 后根取得完整六 PR 表，末轮仍等 foundation；没有证据支持 reset 丢失了 Issue 计划。运行在基础未完成时已停止，不能断言未来绝不会改变计划，但停止时的有效计划只有业务 PR。

因此并非没有考虑过业务子 Issue，也不是已有六 Issue 而观察遗漏。最有依据的机制解释是把共享代码冲突/实施合并安排与需求责任层次合在一起判断；协调冲突能支持共同基础和顺序整合，不能独自推出独立业务的设计与验收责任也应集中根。旧共享 Issue 指令突出“自己设计→创建 PR”，I15 允许“相应 Issue/PR”，旧协作技能未明确两种对象选择条件，允许集中设计、分拆实施这条路径。不能把容量误判作为对象选择的唯一根因，也不能把泛化职责缺口称为已证明的全部原因。

前轮在多处重复职责说明存在冗余。后续收敛建议是由共享协作方法持有业务责任与实现候选的选择条件，明确共享文件冲突影响实施/合并顺序，不决定是否保留独立业务责任；Braid 保留对象职责机制，I15 只保留根持共同基础和最终整合及方法入口。本次没有继续源改动。效果验收应看实际业务需求/技术/验收判断负责人，不能只数六个空壳 Issue。详细原始证据及时间链归同控制目录 `issue-decomposition-diagnosis.md`。

## 当前实施：停止本轮与指派、业务责任修复（2026-10-08）

用户明确要求“可以终止这次运行了”，并授权旧成员名用于新责任时直接采用同职责的新候选、审查类似额外调用，以及修正成员机制说明和业务 Issue 缺席问题。当前 run `dbe577d0710c48b895f54b362f328663` 已经正常 Lab stop；远端与 Mac result-save 均 saved=true、errors=[]，relay 已结束，未派发评分。heartbeat `i15-github-evo` 已暂停。未完成应用和独立工作区中的修改保留；portable consistent=false，不能称为完整可搬运检查点。证据归 `runs/iteration15/github-evo-fixes-20261008/stop-save-summary.json` 与 `stop-notes.md`。

已记录原生切片 00:59:41.890279Z 至 01:25:15.725528Z：3 sessions、87 assistant messages；input 155,651、output 50,434、cacheRead 4,797,824、cacheWrite 0、totalTokens 5,003,909。含缓存、仅本 run 已保存消息，非供应商账单，不与旧运行相加。main/develop 仍为基线 seed 2182a5f，已发布 foundation 3b633a1 只有设计；本轮没有完成交付或新评分。

用户进一步纠正：“不是旧名字用于新工作项，而是尽可能自动收敛/恢复/容错，而且不应该静默容错，要在 response 中说明这是自动结果。”共同目标是减少工具已有充分事实即可解决的失败、提醒与再调用往返，名称候选只是其中一例。runtime_owner 持 CLI 实际失败路径调查、共享候选解析、create/edit/review 接线、技术说明、编译与隔离现场实际操作；advisor 重新判断类似路径与自动处理边界。自动处理需要足够事实支持用户原意，并在 response 明确所做处理与实际结果；不能静默改目标、跨职责或掩盖权限与歧义。已使用名字的同职责选择、同项重复和 request-id 恢复分别核对，精确移除与联系仍依实际身份。root 持 provider 成员说明与 Issue 职责、I15 root/fast 指令、braid-collaboration 和 arc-bench 方法入口。本次授权不启动下一轮模型实验，不 commit/push，不运行 Factory/Braid 测试。

初查 PR create request-id 重试、同负责人重复 edit、已有整合事实的 merge 已自动收敛并明确返回 reused/无变化/合并结果，复用已有行为。此次补候选自动选择说明，以及 review request-id 和重复 checkout 的复用说明。另采用 advisor 的恢复判断：review request 与 conclusion 若 commit 返回结果不确定，工具按完整持久身份一次回读，确认本次预期写入成立后返回明确恢复结果并保留原错误；不重复写入，不能只看可能复用的数字 ID。未确认或回读失败仍保留具体错误。实际 commit 故障若未发生，不能用模拟或宣称实测覆盖；编译、真实正常与重复操作反馈分别记录。

同类进一步包括仅移除负责人、实际已无负责人时返回无变化（不同当前负责人仍不能误移除），以及完全相同的已保存 review 结论或取消理由返回终态回执。原 reviewer 终态后失去写入资格，回执读取沿已有 review_view 只读边界；能由现存绑定或明确 turn 唯一确认本人时说明重复操作，绑定已清除则说明已取得结果但未确认原作者，不建立历史绑定表，也不恢复写入权。Pending 操作保留原权限、责任与候选门控，不自动 cancel 活跃验收，不新建等待队列。默认文本与 JSON 均需说明自动结果；普通 view 不回放曾发生的自动动作。

最后核对首次 review 旧候选自动选择后的相同参数重试：只拒绝虽然避免重复退役，却仍需要 Agent 另查。采用 advisor 的收敛合同：有当前改派权限、Pending 且当前责任有效时，旧名字由事实唯一解析到当前 reviewer 同一 profile，自动保留现责任并明确 changed=false；不增版本、通知或 teardown，不宣称执行健康。当前名字仍幂等，显式当前新候选正常改派，不同 profile 的旧名或未知名仍报错。无需别名注册表，帮助说明主动换人使用当前新候选。

本轮修复完成。最终 Mac 编译通过，包含 provider 最新指令；没有运行测试。停止现场的隔离副本真实 CLI 确认：旧 glm-2 创建新 Issue 自动采用 glm-3，原 PR2 身份/代次不变；同项重复无变化，错误移除拒绝，已无负责人的移除明确 already_unassigned；review request-id 与 checkout 复用明确回执，同结论和同取消理由返回已记录结果，差异仍拒绝；无法确认原作者时返回 read_saved_result、未写入；并发两次 create 实际分别采用 glm-8、glm-9。review 旧 reviewer-2 首次自动采用 reviewer-3 后，再次旧名保留 reviewer-3，责任版本 2→2；显式新候选 reviewer-4 正常改派 2→3，重复当前名或再用旧名均保持 3。响应覆盖文本及 JSON。commit 异常自动回读分支已实现并编译，未在真实故障中触发，不宣称异常实测通过。

采用证据归同控制目录 `automatic-results-cli-receipt.json`，保留调查阶段错误及最终操作；public material 实际装配和 root/fast、三项技能读回见 `automatic-results-public-material/responsibility-readback.json`。共享源和 I15 职责说明已被新装配消费，没有 overlay、热部署、模型请求、新实验或评分；原 run 与旧评分保留，自动跟进保持暂停。本轮后续实验由用户决定。

业务 Issue 缺席已定位到职责表达缺口：共享 Issue system prompt 强调形成设计后创建实施 PR，I15 指令使用“相应 Issue/PR”，技能未明确能力的持续需求解释、技术取舍、验收与剩余义务由谁持有。修正为独立业务能力建立并指派业务 Issue，由其负责人组织关联实现 PR；根保留完整共同基础、跨能力约束与最终整合。已确定边界和方案的小项可直接关联 PR，不机械要求每个场景或 PR 另造 Issue。成员机制说明改为指派后自然提供下一成员，名称机制没有并发名额或总人数上限，同时保留实际模型与执行资源约束。源码修改已完成，CLI 落地与最终实际反馈在途；不宣称停止的 Agent 已采用新材料。

已直接核对保存的 `provider-snapshot-dbe577d0710c48b895f54b362f328663.sqlite3` 中 `local_items(issue:1).body`：设施原正文提供完整需求包、arc-bench 独立入口及 task-context；根后来追加的“工作边界”表明确列 PR #2 基础、PR-1 至 PR-6 六能力及整合 PR，每项业务均“待基础完成”，最后只说明每个业务 PR 独立 reviewer 验收，没有业务子 Issue 或其设计与验收负责人。因此实际 Issue description 和生成推理一致，不是投影遗漏了已创建的子 Issue。职责表达缺口能解释可成立的误读，但不能证明它是唯一原因；最新修正尚无新运行行为反馈。

## 历史早期检查：业务拆分与停止判据（2026-10-08）

用户要求深入检查进展，重点看Issue拆分，拆分有问题可尽早终止当前运行。 用户随后明确同意先不终止，并指出六个业务PR应有明确对应的六个业务Issue。当前root实际只列六业务PR，未建或明确对应Issue；开发侧此前“相应Issue/PR”表述未清楚区分业务Issue的需求/设计/验收责任与实现PR，是仍需收敛的结构要求。基础责任仍由根持有，不转整套子Issue。此次已通过现有Lab记录完成有界定向检查，没有控制运行或向生成Agent注入纠偏。实际只有根Issue1+基础PR2；PR2明确只承接共享schema/权限/seed框架/开发反馈，不含全量业务。六个业务PR仍为root计划，尚未创建，不将读取技能或文档分类认定为拆分已兑现。foundation真实clone有原14users/28sessions/2repos/25issues/14PR，近期读需求/合同，无工具错误。

已证实新的容量误读：root一次assignee list看到下一候选glm2，在01:05:44Z推导“only one other member”，把基础/六业务/整合均规划glm2串行；physical操作说明已明确这不是完整目录或并发名额，故不是系统单实施者。Braid名字认领保留，不允许不同新工作项复用已认领名，失败回执会返回当前新候选，存在首次业务PR自然纠错点。独立advisor与root判断目前继续：串行不等于边界失效，现有基础范围没有吸收业务，不仅因为误认或未创建业务项就提前终止。

下一判别点是基础交回/首业务委派：读取真实工作项范围、assignee回执及随后动作。若形成边界清楚的业务PR则继续（不以并发量评判）；若把独立业务重新塞进基础PR，或收到无法复用名字反馈后仍重复失败指派/宣称无人可用/扩大原全量委派，则按用户授权尽早正常Lab stop/save。runtime_owner持运行控制，控制前记录事实、目的与损失；不新采集器、不注入隐藏反馈、不按token/耗时阈值停，不影响其它官网run。取证归 `runs/iteration15/github-evo-fixes-20261008/issue-boundary-progress.json`、`assignee-capacity-decision.json`、`issue-boundary-reasons.json`。

## 当前实施：三项修复与新自费 GitHub Evo（2026-10-08）

用户授权原话：“好，同意。落地这三个问题的修复方案，然后自费启动新本地运行github-evo。”开工范围：完整业务基线进入Braid独立工作区；区分存量升级与空库初始化的验收；把原需求能力边界落实到业务工作项，并减少失败委派/大上下文重复处理。随后在WSL/SFP7以新native scope、新控制目录从官方完整初赛基线和允许需求启动一次自费生成，按既有配方独立增量官网评分。旧生成应用、旧会话与隐藏反馈不进入新生成；不commit/push、不测试Factory/Braid、不overlay、不设人为费用停止线、不控制其它官网运行。

runtime_owner持I15初始seed/publication/装配与实际新run；score_cost_analysis持存量验收与父方失败委派方法，root持根/fast职责与原树工作项拆分及本packet。第一项采用现有Git边界：I15 seed对已经筛除平台历史/依赖目录的完整批准业务输入force-add，工作区继承一致commit并独立clone；不新增ignored数据旁路或改Braid共享worktree合同。实际官方输入装配已见root/implementation/reviewer/export均保留14users/28sessions/2repos/25issues/14PR、独立inode，证据 `runs/iteration15/github-evo-fixes-20261008/baseline-seed-materialization/receipt.json`；新run实际成员采用仍待验证。第二项材料已区分官方存量副本升级、原数据保持和空库初始化。第三项保留根完整基础责任，明确基础PR承接共同前提而非全部业务，形成工作项前触发结构方法；父方重派方法归实际独立svc-sub-agents skill，而非未加载的executor Corpus。

三项已完成并由public真实装配读回：I15 seed完整force-add；root/fast基础与业务职责、arc主文件/reference工作项判断；platform/e2e/verif区分存量初态；父svc-sub-agents失败恢复/等待事件/必要重派上下文。新fresh Lab run `dbe577d0710c48b895f54b362f328663` 已创建，控制目录 `runs/iteration15/github-evo-fixes-20261008/`，同名新native_scope、native_resume=false、competition=false，原官方baseline/context/自费模型配方保持，隔离.e2e-evidence等旧证据。实际inputs/variant-material已消费最后父技能段，实际SFP7启动running，首GLM5.3Flash于01:01:05Z完整响应并执行read等工具；真实root issue-1工作区保留14users/28sessions/2repos/25issues/14PR，native_resume=false。唯一supervisor3602648/Macrelay95147已接终态save与official/self_funded非参赛增量评分，heartbeat i15-github-evo已恢复并指向本新run。01:03:20Z有界首次观察已读取新版reading-requirements与organizing-work，业务工作项尚未形成，仅root工作区；不把读取成功宣称拆分采用或评分改善。实施/reviewer业务数据及后续能力工作项边界由既有observer和heartbeat继续采用，不增加采集器。证据归新控制目录 startup-adoption-summary.json、first-model-and-baseline-adoption.json、initial-responsibility-readback.json。下一步自然生成/验收、完整保存后独立评分；没有取得新分数。

## 当前调查：低分、基线与用量（2026-10-08）

用户要求核实本地是否正确从初赛基线开始、官网是否确为重放，并分析失分与高token。本轮只读取证已完成，不启动新实验/评测、不修改业务或Harness源码、不commit；heartbeat保持暂停。

实际链结论：官方基线正确注入本地SDK/output，官网23:31:09实际Delivered incremental replay/no model calls及.arc回执证明增量重放已执行，原21张业务表记录未丢失或改变。但seed/final Git均无被*.db忽略的backend/database.db，Braid工作区用新建库，未消费官方已有28sessions/14users/2repos的业务初态。实施/验收库与原库不同；glm3实际删除新建库后用空库启动结果证明交付，根采用该摘要宣布完整覆盖。

官网实际第二条sessions ALTER失败（last_active_at表达式默认值），后续Evo表/seed未执行；初始化错误只打印而仍监听，health不门控。随后38次organizations缺表/API500事件：30次GET /api/repos、8次GET /api/search/repositories。不是全部连接拒绝；39应用错误事件不能一一映射29失败case，现有明细为空，不断言全部失败只有该原因。

同final slice边界的成本分解：root20,753,940；实施PR2 82,672,295；review1 53,010,320；review2 12,435,422；整合PR3 6,022,807；其它原生session29,243,547；总204,138,331（cacheRead201,345,728）。主热点为全REQ单PR后文件级8executor，首轮5/8 queue_timeout/admission_limit，kimi重派4/5再失败；父上下文215k～244k持续查询/重派。review1生成调试全量e2e、数据污染重跑，真实发现4缺陷但成本53m。根已读arc-bench/braid-collaboration主文件并列出6能力，却仍按“我的交付是设计文档+基础PR交glm2”的职责解释承接全量，未读工作边界reference，拆分改动未成为实际工作项行为。

采用入口：`runs/iteration15/github-evo-20261008/analysis-baseline-replay.md`、`analysis-baseline-database-states.json`、`analysis-official-error-events.json`、`analysis-review-acceptance.md`、`analysis/score-cost-analysis.md`、`analysis/token-breakdown.json`、`analysis/executor-fanout-evidence.md`。下一步建议优先修基线业务状态的工作区交接/验收条件，再处理拆分与高上下文重试，不靠重置DB或只减检查次数改善指标；本次未实施新修复。

## 本轮完成：GitHub Evo 权威评分（2026-10-08）

本轮生成、正常设施发布接续、完整保存及独立非参赛评分均已完成，不启动下一轮。官网 `0eef2203da5d`（Lab `574d30eee33b41b2b803464e4775342c`）真实回执：score/test_pass_rate **3.3**，passed **1**、failed **29**，feature_implementation_rate **0.0%**（0/10），billing self_funded。平台PASSED仅表示执行终态，不表示测试全通过。结果已经通过正常Lab save回收，result-save saved=true、portable_consistent=true；独立评测缺native_scope_id的共享保存缺陷已修，旧错误与旧consumer身份保留，仅替换该终态评测保存consumer，未重评、未控制其它官网run。

原5c98最终native已记录切片：input **1,852,677**、output **784,534**、cacheRead **201,345,728**、cacheWrite **155,392**、totalTokens **204,138,331**，23usage rows/1837 assistant；since19:04:36.290756Z→23:10:42.550002Z，包含缓存，非账单，未盲加其它执行片段。实际应用启动的SQLite非恒定默认值迁移错误已保留，与低分相符但不据此认定全部29失败单因。没有修改生成应用或注入隐藏反馈。

权威原件 `runs/iteration15/github-evo-20261008/lab/runs/574d30eee33b41b2b803464e4775342c/records/platform/status.json`；采用入口 `official-evo-score-summary.json`、`evaluation-save-repair-summary.json`、`generation-native-usage-final-slice.json`、`publication-recovery-success.json` 均归同控制目录。heartbeat `i15-github-evo` 随本轮完成暂停；后续改进或实验由用户决定。

## 夜间推进与新Lab原生恢复（2026-10-08，过程记录）

用户授权：“我要睡觉了；你可以继续推进，直到没有未落地修复的已知问题，然后就可以在本地（WSL/SFP7）启动自费运行了，跑github-evo task。”后续补充“可以试试用新的实验基础设施”“可以让I15支持原生恢复先”。当前顺序为完成已知修复和新Lab原生恢复，再继续github-evo自费生成；本次真实新运行同时承担一次有界停止、保存、原生接续验收。只用官方完整基线与允许需求，保留业务数据，不把旧运行应用装入新生成，不参赛、不消耗比赛额度、不commit/push。Mac产物全部WorkSSD，不编写/运行Factory或Braid测试、mock、探针，不做逐文件字节审计。

用户还要求确认自动评测不会取消阻塞重放的官网运行。已核automatic-evaluations→evaluate_run→Hosted.start：只上传本次重放、创建/start本次评分run；4xx门控保留具体拒绝，没有cancel其它run或delete快照步骤。此次授权不含停止、取消或删除其它官网run/submission/snapshot；不借旧任务专项清理许可。官网阻塞时保留具体错误等待条件变化或用户决定，不自动破障。

root持总packet、残余方法判断与结果整合；runtime_owner持续持I15 build/run、公共材料生产、Lab execution/local_run/restart接线、实际启动/设施修复/终态保存与独立评分。native_resume_advisor持恢复关键判断，已采用其结果；原评测执行者完成增量评分接线并返回，局部后续由runtime_owner接续。各owner保留他人dirty改动。

| 本次执行 | 当前事实 |
| --- | --- |
| 初始run `3d566773b0b3457b85dd8b92f1bf6319` | sfp7、新Lab正常start；ARC/arc-glm-5.3-flash实际HTTP200/terminal complete，root Pi session `01a117af-976d-737a-ad29-22b5346886b3` 已读取基线和需求。经正常restart停止并完整保存。 |
| 首次接续run `2b69078513584115b80c30eaf546a0c9` | 同scope/assignment/Pi JSONL保留，retained校验通过；Braid误判Blocked导致已恢复的新turn被shutdown。observer/save已保存失败现场。 |
| 当前run `5c98cfbdaf3b4a4299aa1ffd46ddef0e` | 修复版runtime经正常restart接续成功，保留3d566… scope、原assignment generation 1及原Pi session（resume_count=2）。新turn实际写文件、创建PR #2并指派glm-2；Braid已完成交付，应用发布因两处设施接线失败；经后续0e2e52…接续发布completed/saved，独立评分574d30…进行中。 |

本次控制与反馈归 `runs/iteration15/github-evo-20261008/`，新Lab run入口为其 `lab/runs/<id>`。`first-model-request.json`、`first-design-readback.json`保存启动事实；首执行 `initial-native-usage.json` 回读21条assistant，input=77013、output=17571、cacheRead=1124224、totalTokens=1218808，含缓存、非金额或完整交付成本。真实Pi平铺sessions文件被旧_native_log_candidates漏掉，runtime_owner已修限定work/native-homes/sessions扫描；公共reader真实回读成功，新observer消费修复。

新Lab接入已落源并完成公共材料真实装配、当前proxy Linux编译：I15采用variant-only公共producer，完整共享runtime/技能/Braid/Pi/default再variant覆盖，避免旧底包保留旧代理；当前self-funded路由ARC首道、千帆个人TokenPlan下架。Evo task冻结同一官方baseline/context，由SDK注入；终态Mac消费者复用incremental_replay/package_incremental_replay，official、self_funded、hackathon-evolution--github与hackathon-evolution competition身份明确。仅completed且保存成功后独立派发一次评分，隐藏反馈不回送生成。费用主口径token，不设人为费用或时长停止线；受限模型合计只由一个Braid Session使用。

原生恢复复用固定 `/workspace/submission`、`/workspace/template` 与同native_scope的应用、Braid DB/origin/worktrees、Pi homes/templates、原request/prompt/需求和受限模型逻辑名额，调用既有--offline-resume。Lab stop/save提供停止来源，不伪造旧manual Docker收据，不做任意历史路径替换，不调用native_files覆盖旧模板，不静默fresh。恢复默认沿原冻结route/catalog；I15显式实际不一致路由在停止源运行之前拒绝，显式相同可接受，其它variant原接口保持。same-task输入迁移包括冻结baseline/context。执行日志/进程/耗时归新producer，scope保持久状态；不承诺浏览器/PBB进程、在途工具或内存检查点恢复。

实际恢复失败根因已由runtime_owner与advisor独立定位：prepare_offline_resume后旧turn暂为unknown、worker首次health未齐，local drive过早执行root_idle_tick，以 `root Issue #1 member glm-1 has no resumable session` 返回Blocked并shutdown。远端同Pi session已resume_count=1，RPC恢复/prompt和新uncertain_continuation turn事实排除会话丢失。最小修复等待全部worker首次health后再允许根空闲/静止终止判定，fatal-stop立即收口；不放宽closed资格、不重派旧wake、不修改DB伪造连续性。Mac和最终Linux编译已通过，修复版公共runtime实际接续成功，证据见本次控制目录 `native-resume-success-summary.json`、`native-resume-fixed-actual.json`；首次失败归 `native-resume-first-failure.json`。这验证同assignment/session的有效后续执行，不扩大为所有运行中恢复边界已验证。一次有界语义核对仍见全需求单PR，未取得advisor/vision调用证明；不干预正在生成的Agent，待完整执行后分析采用差距。 已创建本线程30分钟heartbeat `i15-github-evo`，仅消费既有记录、处理可行动故障并确认终态保存与独立评分；状态未变保持安静，完成或需要用户决定的外部阻塞后暂停，不启动下一轮。

2026-10-08 03:51北京时间（19:51Z）heartbeat定位并完成实时计量修复：新原生home为700/root，宿主yyh扫描静默跳过，导致仅根会话计量。共享native reader现显式报告PermissionError，并复用宿主sudo只读读取；I15 observe入口已被当前supervisor每轮加载，生成、supervisor/default进程保持，目录权限未变。实际回读15个session、394条assistant：input=707158、output=299389、cacheRead=36930048、cacheWrite=139264、reasoning=113153、totalTokens=38075859（当前执行部分切片，含缓存，非金额，不与原生/provider双口径相加）。证据 `native-usage-observer-adoption.json`、`native-usage-private-homes-summary.json`。缺可选status.py仅使旧activity摘要unknown，现有native.braid事实正常，不新建兼容脚本。生成仍running，尚无终态或评分；没有控制其它官网运行。

2026-10-08 07:12北京时间heartbeat发现5c98cf…退出1；Braid自身已quiescent/exit0、根CLOSED并保存delivery commit `6834a44d…`，失败发生publish_application动态导入不存在的 `/workspace/tooling/linux/exp_checkpoint.py`。runtime_owner已修共享helper优先使用producer同目录support/exp_checkpoint.py；正常Lab restart创建 `2e0273ae0600472daf0afbb7790ad1ff`（保留3d566… scope），仅恢复导出同一交付、不修改业务应用。该接续无新模型turn，路径修复生效后仍因SDK注入requirements被seed误纳而发布失败；现场已完整保存。未来I15 seed排除平台requirements，当前两个导出复用显式excluded_platform_paths（默认空、只限平台保留根路径），仅在SDK目录从seed到delivery未改时排除requirements，manifest保留source commit及excluded路径，严格校验不放宽。真实保存提交应用投影已通过validate_application。再次正常发布接续run `0e2e52d5e01b439cbba281763c5ea358` 已完成发布与保存，独立评分身份及收据见下段；不修改业务代码。动作依据、目的与可能损失归 `publication-recovery-operation.json`；不伪造completed、不新开生成或控制其它官网run。

发布恢复最终已闭环：`0e2e52d5e01b439cbba281763c5ea358` completed/exit0，远端和Mac result-save均saved=true/errors=[]；未新增业务模型turn。正常Mac relay已创建独立official/self_funded、competition=false增量重放Lab run `574d30eee33b41b2b803464e4775342c`，官网run `0eef2203da5d`、submission `5dbb6bb42b3c`，评分尚未取得。原observer持续持评测事实，heartbeat已更新为跟进该身份。原5c98保存native最终切片since19:04:36.290756Z→as_of23:10:42.550002Z：23usage rows/1837 assistant，input=1852677、output=784534、cacheRead=201345728、cacheWrite=155392、reasoning=128733、totalTokens=204138331；包含缓存、仅已记录切片，不是账单，未盲加初始run/失败接续片段。应用实际启动出现SQLITE_ERROR Cannot add a column with non-constant default（evo/db/migrate.ts109，ALTER sessions ADD last_active_at DEFAULT datetime('now')）；保留业务失败，不由开发Agent修改，也不冒充设施零分。证据 `publication-recovery-success.json`、`publication-recovery-notes.md`、`generation-native-usage-final-slice.json`。没有取消其它官网运行。

advisor对其它方法已收敛：新技能可用不要求全部启用；图片已有真实视觉观察方法及root交vision入口，旧run未采用尚不足以证明多加一句强制语句有效。保留角色选择，观察本次设计交接的需求能力边界、图片依据、advisor关键判断与reviewer/e2e采用。历史评分缺失败页面证据的原因保持未知；多项改动同时采用，单次成绩变化不能归因到某一句技能。

## 当前剩余事项（2026-10-08）

用户要求列出尚未落地解决方案的问题，并提醒materials/skills有多项更新。随后明确不要把接线核对做成逐文件字节审计；后续按源码消费路径与实际修复内容判断，不继续扩大哈希或旧运行制品核对。

此前“只遗漏svc-verification”的判断不完整：七项刷新名单使其余共享技能依赖旧底包，I15整份e2e覆盖又遮住共享正文更新；新增技能还需要区分库中可用与会话启用。现已取消局部刷新名单，默认装配当前共享技能库，再应用variant明确覆盖。

| 项目 | 已落实处置 | 反馈边界 |
| --- | --- | --- |
| 共享技能更新 | 复用copy_skill发布边界装配全部有效共享技能，已声明技能缺源明确报错。 | 实际材料装配22项技能、134个资源；发现清单未扩大，实际Agent采用待运行。 |
| e2e正文覆盖 | 通用业务状态转移reference归共享e2e，删除I15整份正文和共享reference副本。 | 当前装配同时取得acceptance-contract与状态转移方法。 |
| 统一源码归属 | 技能归materials/skills，Braid归sources/braid，Pi归公共npm lock、补丁与runtime生产入口；variant只持有差异。 | 本轮修正I15技能接线，保留既有公共Braid/Pi生产链与standalone兼容交付；历史冻结运行不变。 |

PBB跨会话停止修复已接入I15源码和构建接线，不列作未处置设施。assignee名称机制、原需求结构拆分、基础/业务边界、advisor description/catalog、根跟进、245k压缩、reviewer生命周期与e2e终态/复测方法已落地；真实Agent采用及评分/token效果待后续运行，不再归为没有方案。基础责任规则保持。

评分差距仍有未定位原因：Stage2两条标题失败是检查语义差异，不据此迎合隐藏定位器；22条导航失败及3条超时缺失败页面/最后成功动作，已有材料不足以给出具体修复。根漏requirements图片属于父方材料取用，不是vision失败；现有完整材料与结构方法已有处置，上游为何漏读尚未隔离。reviewer主动放宽已有原文权威、verification、新advisor及复测方法对应，不追加重复严格口号；同步更新后观察实际判定。

共享技能消费改进自身已完成源码及真实材料装配反馈；后续新Lab运行状态见页首。详细调查入口保持下文及 `runs/iteration15/skill-consumption-inquiry-20261008/`。

## 共享源码默认与variant覆盖完成（2026-10-08）

用户指出“只遗漏svc-verification”范围不充分，并提出：“后续都是将agent skill, braid, pi等都共用一套源码，而不是在variant中分别复制，仅在variant内做覆盖”。本轮落实当前I15技能消费：共享库默认、variant明确覆盖，取消七项更新白名单；会话启用清单不扩大。Braid/Pi保持既有公共源码与producer，不新建来源注册层，不全面改造standalone兼容交付，也不追溯历史冻结包。root负责共享e2e与材料归属说明，runtime_owner负责I15 builder/README及必要真实装配反馈。

e2e业务状态转移方法为通用方法，已移至共享reference并由共享主文件按相关动作触发；移除I15整份正文及共享reference链接副本，不让旧正文继续遮住共享acceptance-contract更新。其它新增技能进入共享可用库与其是否被会话启用分别处理。“只遗漏verification”原结论仅限旧选择集，不再作为完整接线结论。所有Mac产物在WorkSSD；不做逐文件哈希审计，不编写/运行Factory或Braid测试，不启动模型、评分、overlay或在途部署，不commit/push。

实际材料装配与Python语法反馈已完成并采用，证据见 `runs/iteration15/skill-consumption-inquiry-20261008/implementation-notes.md` 与同目录 `shared-default-assembly-feedback.json`。没有扩大角色启用清单，也没有生成overlay或改变在途运行。

### advisor本轮调查与提案修正

独立advisor原件纠正了此前“第46行没有明确advisor分支”的判断：根确实记得咨询要求，并在TypeScript业务源码约束与JS基线延续的解释上自行作共享决定，却将其归为“清楚的局部决定”。这直接支持自身信心与影响范围混淆，不冒充工作拆分分支的直接心理证据。Evo未查询原生角色目录；同配方Stage2实际list可发现advisor，随后成功调用vision。description变化本身不是首要修复点。

用户随后纠正：“advisor 的触发机制应该是 advisor description 提供的，而不是 root/fast profile。”因此撤回只替换profile咨询段的方案；此前候选文字仅为历史提案，不是待实施方案。触发语义归advisor description，profile不得用窄条件重新定义或覆盖它。独立advisor完成接线核查：default/full/compact都是通用工具说明，custom也无动态角色占位符；切换mode不会展示角色description。现成action:list足够。建议三份advisor description统一定义关键性（影响范围及纠正代价）、在方案形成中独立判断、工作拆分/委派成本收益作为实例；root/fast删除窄触发段，三个profile只保留当前目录缺失时查询、有效目录复用的通用发现指针。保留advisor正文、继承设置、技能清单及完整基础责任，不建立成本表或每次delegation门控。原件结论及更正归 `runs/iteration15/advisor-cause-inquiry-20261008/findings.md`。

Stage2评分进一步定位：两条标题失败由布局标题与README标题均匹配、而自验仅匹配owner/repo解释；公开要求只有存在相应标题，没有唯一性，不能直接判产品违约。22条导航和3条超时缺失败页面与最后成功动作，现有材料不足以定位。自验包含不同入口，并非全靠直达路由。证据归 `runs/iteration15/score-cause-inquiry-20261008/stage2-score-notes.md`，不读取隐藏评测器或做针对性适配。

## sub-agent catalog hook开工（2026-10-08）

用户要求触发语义归advisor description，并建议：“做一个简单的 pi hook，把 sub-agent catalog 放到 system prompt 中”。本轮据此实现目录元数据发现接线；description是角色适用条件唯一来源，撤去root/fast重复的窄条件，不增加每次查询目录要求。root负责三份advisor description和两份profile删除，runtime_owner持续负责Pi hook、I15消费接线及真实加载反馈。保留基础责任、角色正文、模型/继承设置和技能清单。hook只投影原生当前可用角色名称及description，不内联角色或技能正文。只修改相关源码与必要文档，不启动模型/评分、overlay构建或在途部署，不commit/push，不编写或运行Factory/Braid测试。验证以当前运行时实际目录和无模型扩展加载回执为依据，不能宣称真实Agent已采用。证据归 `runs/iteration15/subagent-catalog-hook-20261008`。用户随后要求审查其它sub-agent角色description的加载性能；本轮同时审查适用性/职责重叠、目录上下文大小和真实hook加载开销。advisor_cause负责语义审查，runtime_owner在原无模型加载操作中记录开销；不把未测的性能猜测转为缓存框架，也不因description短而扩写。其它角色当前仅审查，未获具体修复结论前不修改。用户后续指出对“加载”仍理解片面；撤回仅凭职责文本、一次vision调用和字节/耗时就判定其它角色加载无问题的结论。当前已异步询问完整评价含义，角色审查等待该信息；独立的已授权catalog hook实现和接线核对继续。

### catalog hook实现与已知边界

hook已完成：公共pi-subagents补丁复用当前discoverAgentsForRuntime及可执行范围筛选，在before_agent_start追加当前角色name和description；I15三个profile的launcher启用，保留原system prompt，空目录不注入，普通不具备编排能力的子角色不注册该父扩展。三份advisor description已定义关键决策适用性；root/fast重复的窄条件已删除，基础责任及其它角色正文/配置保持。

真实Pi loadExtensions和ExtensionRunner无模型读回成功，五项角色metadata及新版advisor描述可见，两次事件无目录累积。实际目录448字符/1206 UTF8字节；整次加载约2606ms、首启动事件约236ms包括其它加载/handler，不是hook纯耗时或Agent能力加载表现。三个launcher读回启用；patch实际应用及公共目标接线完成，旧protocol-inputs缺新补丁身份会被拒绝，后续交付须重建runtime。本轮不制overlay，不改冻结材料或在途运行，不启动模型/评分。实现与回执归 `runs/iteration15/subagent-catalog-hook-20261008/notes.md`、`extension-runner-readback.json`、`native-materials-readback.json`；root角色源身份归同目录role-source-record.json。

用户进一步以matt-skills提示“触发、加载、？”。已读writing-for-agents与SKILL-MECHANICS原文，当前审查沿上下文指针的适用分支、实际取用必要材料、行为采用全链重新展开。目录可见、角色文件存在及单次vision成功均不证明可靠加载。此前仅凭静态分流与字节/耗时的结论撤回。后续用户纠正归属：Evo根没有读图片，也没有给vision任务，图片遗漏属于根的requirements材料取用，不能作为vision子角色缺陷。Stage2的具体图片委派成立，不据任务详细程度认定vision描述有缺陷；executor/explorer description中的请求补充句属加载后方法，正文已有，建议移出常驻层但尚未修改；fresh/不继承父上下文要求实际交接，技能目录存在不证明采用。root补查Evo四份完整原生父Session的toolCall元数据：76次subagent前缀调用均为subagent_wait，无角色管理/执行调用，因此该run无其它三角色实际子调用可用于判断加载链；未调用本身不等于应调用场合未采用。角色审查及行为证据边界归同目录role-description-review.md和evo-subagent-call-inventory.json。不自行新开模型实验，未改其它四类角色。

### 其它角色description修正开工与结果

用户授权：“好的，请做修正”。按刚呈现的具体修正，三套I15 profile的executor/explorer共六个角色文件仅删除description末尾请求补充句，执行方法保留正文。root负责该元数据改动，runtime_owner继续原catalog实际读回验证；不改vision/browser-operator及其它角色设置，不把未知采用问题当作已修复。源身份与正文保持回执归 `description-correction-source-record.json`；不新增测试、模型运行、overlay、部署或commit/push。三套native模板与实际Pi ExtensionRunner已读回修正后的两类描述，加载无错误；旧回执保留，新结果归description-correction-readback.json和description-correction-notes.md。目录413字符/1101字节不是采用效果证据。

## 三项改进开工与advisor当时暂缓（2026-10-08，历史授权）

用户授权原话：“对 advisor 的改动暂缓，你的理解还是有问题，所以方案也有问题，你最好问问你的 advisor。其它3个改动可以落地了。”本轮开工范围为Braid注入指令的普通assignee名称机制、braid-collaboration任务边界与执行并发的区分，以及arc-bench利用原需求结构形成和检验工作边界。CLI输出及JSON不改；advisor的description、正文、profile咨询规则和技能目录全部暂缓。不启动模型/评分、不修改在途运行、不commit/push。

root持有两项技能的主文件、organizing-work、reading-requirements、tracing-and-reviewing-coverage及本packet；runtime_owner负责Braid注入段、编译、真实已有CLI副本反馈及两项技能的必要消费接线。用户随后明确“不需要 overlay”，已取消新归档计划，只交源码、技能及验证；不启动新的打包或部署。保留侧会话执行可见性、reviewer更正及工作区其它改动。验证使用编译、实际操作、技能人工核对和归档读回，不编写或运行Factory/Braid/技能内容测试。

独立advisor已重新判断：之前双方都把通用关键决策咨询过度特化成拆分成本审核流程；Evo未调用不能证明advisor正文或技能名单造成判断失败，现有svc-sub-agents已有成本收益方法。应由advisor承担尚未完成的独立判断，不要求根先完成全套分析再请其背书。当时advisor改动暂缓；用户后续要求恢复调查，以本页首节为准。旧整套改造方案不作为下一步实施依据。

### 本轮完成与反馈

三项源码改动已完成：Braid的provider指派段与local操作说明解释下一可认领成员机制；两项协作技能主文件和references明确任务边界/并发、原树能力候选、共同前提、真实依赖、局部与跨枝完成依据，以及增量基线责任回查。I15 builder显式叠加两技能原件并拒绝缺失SKILL.md，避免以后构建仍继承旧底包正文。advisor源码、profile咨询条件及角色发现目录保持。

Mac和Linux编译通过，Linuxbinary SHA256为013255c08ecb38c37f16b88491595531b6a4e65c78773419ecee778e6256d785；真实历史CLI副本指派glm-12后重新查询取得glm-13。反馈见 `runs/iteration15/assignee-instructions-20261008/verification-notes.md`。注入正文读回是既有physical指令的源码投影，不是新原生Session或模型wire行为反馈。技能人工核对及五文件身份归 `runs/iteration15/requirements-boundaries-20261008/skill-source-record.json`；公开需求的三个静态应用案例归同目录 `manual-application.md`，显示身份与组织可分、成员撤销须承接父层原子语义、快照合同支持读写分开且分支URL一致需联合裁决。未证明真实Agent采用或评分/token改善。

“不需要overlay”消息到达时，已发出的builder调用刚完成；本轮新overlay已废弃删除，未使用或部署，旧包保持。保留操作身份记录仅用于说明时序，不是推荐制品。本轮不交overlay，不运行模型/官网评测或Factory/Braid测试，不commit/push。

## 技能编写指引（2026-10-08，侧会话）

用户要求在materials/skills增加AGENTS.md，既遵守Agent Skill规范，也总结matt-skills。已核对官方specification、matt的writing-for-agents、Skill Mechanics和Codebase Design原文，新增开发侧局部指引及README入口。指引区分标准格式、项目加载合同与上游写作方法，覆盖可靠触发、按分支披露、原则的可判断性、信息归属和实际采用证据；不将客户端专属字段当通用能力，不增加技能模板、测试或打包规则。已人工核对来源链接与本仓copy_skill只分发独立技能资源的边界；开发AGENTS不作为技能正文注入。未改其它技能或已冻结制品，未commit/push。

## 执行可见性开工（2026-10-08，侧会话）

用户授权：“从 braid-collaboration、braid CLI 的能力入手来改进难查、不能查的内容，使其至少可以查，而且知道可以查。”本侧会话仅负责工作项只读执行查询、技能发现入口及必要说明；不使用子Agent，不变更主线程的reviewer生命周期、拆分方案或在途运行，不commit/push。复用既有SQLite执行事实、物理session记录和证据路径，不增加监控器。以Mac编译和真实历史现场隔离副本的实际CLI操作核对Issue/PR/review、当前指派与旧候选区分、错误及未发布工作区入口；不编写或运行Factory/Braid测试。证据归 runs/iteration15/execution-visibility-20261008。

本侧会话已完成 `braid execution issue ID`／`pr ID`／`review PR REQUEST` 及braid-collaboration入口。查询当前最后指派代次、具体成员、最近session/turn/reset、待处理批次、完整turn/恢复错误、worktree与原生证据路径。review按最新请求级责任模型查询自身execution_node，并显示latest_request与候选checkout；不读取历史pr_review_sessions，不改变reviewer生命周期。技能说明普通view.execution只是故障投影，提供实际分支、未发布工作区及定向原生记录查询方法，不将状态当进展。Mac编译通过（14项既有未用代码警告）；真实Evo及已有历史隔离副本的宿主/Agent绑定CLI查询成功，核对停止中的旧review责任、旧/新请求、实际failed turn具体错误与缺失工作项拒绝。新二进制与操作回执在上述证据目录。未新增测试、模型/官网运行、热部署、制品替换或commit/push；Linux运行材料由其原负责人后续冻结，本侧会话不覆盖正在构建的包。 用户补充要求避免在SKILL.md堆叠内容后，已撤去新增执行核查章节与命令/字段清单，将一段判断原则和明确reference触发入口并入已有“整理支持判断”部分；查询细节及故障字段语义集中在organizing-work.md。

## Reviewer 语义更正与本次开工（2026-10-08，侧会话）

用户明确 reviewer 是具体 assignee，不是 profile；每 PR 同时只能一个 reviewer Session。用户授权：“改派既然是创建新的 reviewer Session（原有的 session 被终止）。你可以开始改造。”随后对候选A→B明确选择每次新建Session，说明两个候选的 reviewer 是不同 assignee，不能复用同一个 Session。本次仅处理这个边界，不接续其它调查、不操作在途运行、不commit/push。

此前“每 PR 持久 Session、跨候选继续使用”以及本侧会话首轮条件持久解释均撤回。已移除 PR 锚/current_request 运行消费与自动继承，恢复 request 级独立指派及 conclude/cancel Unassign；同 PR 旧 assignment 未停止退役前阻止新候选。改派当前 Pending 请求沿现有停止屏障创建新 Session，同成员重试保持幂等。schema 19 原checksum保留为历史兼容，不再承担运行职责。反馈使用编译、真实历史隔离CLI与材料读回，入口 reviewer-session.md；最终证据位于 runs/iteration15/reviewer-request-session-20261008，不启动模型/评测或测试。

Mac及Linux编译通过；真实历史隔离CLI确认候选18/19分别认领reviewer-15/16，cancel/conclude清除指派并发Unassign，实际旧assignment仍stopping时下一候选被拒。未启动provider，不能宣称物理退出或新Session已实际创建。最终overlay为 `runs/iteration15/materials/reviewer-request-session-20261008/overlay.tar`，SHA256 `38962b5fa124efa02e1ac6fcca057c46a06c22ade7ccd6925e58a986eebfc888`；manifest和指令实际读回核对完成。本次更正已交付，无模型/评测/在途部署/commit/push。

下文与此处冲突的 reviewer 解释及旧材料推荐均为历史。

## 当前修复讨论（2026-10-08，用户再次修正后）

用户明确不在CLI查询结果重复说明成员机制，改由Braid注入的现有profile操作指令简短说明；认可braid-collaboration中任务边界与并发安排分离的改进。advisor应服务关键决策，评估delegation与work-item breakdown的成本、收益；撤销前案固定首次多能力咨询入口，核对角色description、成果约定和配方触发的缺口。此前arc-bench需求结构技能方案继续推进设计，不能被局部容量修复替代。advisor当前关闭上下文/技能继承，默认技能目录也无arc-bench、braid-collaboration；方案须提供独立发现入口与相关原始材料。当前收敛方案见 `requirements-structure-inquiry.md`末节。本轮未修改这组源码或启动实验；保留侧会话reviewer与执行可见性开工及成果。

## 优先调查恢复点（2026-10-08）

用户要求优先弄清楚“根已看到需求结构，却按创建基础PR、交实施者的职责理解合并工作”的根本原因。本轮继续只读定向取证及维护现有packet，不修改技能或启动模型实验。runtime_owner持有冻结输入与成员目录语义，metrics_owner持有初始决定及跨阶段对照，lifecycle_advisor提供独立因果判断，root整合结论。

新原件纠正了此前“没有比较拆分”的判断：Evo根已考虑多PR/子Issue，随后以仅有glm-2一个实施者、协调成本高及不拆整套基础责任为依据回到单一基础PR。真实目录只展示每profile下一可认领成员，可继续取得glm-3；system也说明其它工作项从最新目录另选。根因此把目录误读为单实施者容量，又将仅约束共享基础的禁拆规则误套到全部业务。这两项错误前提是本次决定的直接机制；上游措辞、发现面与原则为何未纠正误判仍需隔离。具体证据、历史迁移反例与控制变量顺序见 `requirements-structure-inquiry.md`，不将其扩展为所有低分的统一根因。

## 当前授权与负责人（2026-10-07，用户修正后）

本轮用户修正了接续理解：一个 PR 只有一个 reviewer，对应一个 Braid Agent Session，可以改派；先前“每候选结束后新 login”的实现不能直接当作该目标已满足。改进的主要杠杆是充分利用 arc-bench requirements 自身结构形成任务拆分，以降低每个负责人的理解负担、减少幻觉和遗漏，并取得并行收益。原则型技能本身受到鼓励；需要定位当前措辞为何含糊、缺少哪些判断依据，学习 matt-skills 的信息组织与触发模式，而不是一概把原则改成操作清单。

用户补充“费用可以不是金额，本质就是 token 消耗”。本轮费用分析以 input/output/cacheRead 等实际原生用量及其采集范围为主要口径，判断重复上下文消费、无效往返与返工；不以供应商金额未知阻碍分析，也不将不同口径的 token 简单等同金额。

用户继续明确：耗时的影响优先级最低，它作为高消耗、低评分的热点定位线索。时间与token热点都回到具体Session、评论、当时材料和工具结果，解释Agent为什么选该路线或未采取其它动作；既有信息不能区分直接原因或根因时保留竞争解释，后续用消融与控制变量取得判别证据。本轮不因此停止已有实施，也不自动启动新付费实验。

用户明确授权：“上下文重置界限、根负责人跟进情况，你已经可以落地这两个修复，无需进一步讨论。”本轮同时核对 pi-minimal-vv 近期 Pi／运行时缺陷修复在 I15 中的实际接入，分析近期 I14/I15 的生成耗时、实际费用和官网评分及改进点。不启动新付费模型运行或官网评测，不热改在途运行，不 commit/push；工作区其它任务改动保留。结构拆分及技能改进先形成有证据的诊断与方案；明确授权的两项修复直接实施。

root 负责现有 packet、根负责人跟进指令、结构拆分与技能调查和整合。`/root/runtime_owner` 负责 Pi／运行时接入、原生压缩和上下文界限、I15 run/build 与新材料；`/root/reviewer_owner` 负责 reviewer Session 语义与 Braid 生命周期修复、成员指令中的该段及所属技术文档；`/root/metrics_owner` 负责近期运行耗时、费用、评分分析。各负责人保持责任，材料冻结等待源码与新二进制完成；无 Factory/Braid 测试，以编译、实际隔离操作、材料读回及现有运行证据验证。

advisor 已核实际调用链并给出可采用决定：PR 稳定 review 执行锚保持 assignment/agent_id/native Session，候选 request 保持独立冻结，current_request 是当前候选入口，旧 key 幂等读取不切换它；fixed cwd 仅验证当前成员在该 PR 注册的历史 checkout，结论另验当次显式 checkout 的 HEAD/tree；Wake 明示新 request，reset/resume 读取当前请求，改派走物理停止屏障。Pi 增加可选 compaction.thresholdTokens；I15 为245000，实际触发取该值与真实 contextWindow-reserveTokens 的较小者，reserve=16384、keepRecent=20000 保持，未配置 profile 保持原状。不能用编译或 CLI 副本宣称已证明原生历史连续与物理停止。

根负责人跟进职责已写入 root/fast 成员指令，已有 root_check_messages 入口同步由 runtime owner 实施，检查实际讨论、业务改动、失败证据、turn/provider 与有效下一步；不增加提醒频率或独立监控器。结构调查与方案见 `requirements-structure-inquiry.md`，近期运行分析见 `run-analysis.md`。后者依据新原件确认 I15 Stage2 已23:25:45自然冻结73dffb43并启动Stage3，官网非正式评分2/29；此前23:07评审中记录保留历史身份。开发侧评分分析不回送在途Agent。

Evo GitHub 指定停止后的 `final-frozen/freeze-receipt.json` 已形成，记录退出身份、54168 个归档文件及 archive SHA256 `4c1d879b16f4bb75eb1dae639dbb64cb005b7bee923279b5c059ae5ead779506`；这是冻结收据存在的事实，本轮尚未重算整个归档校验。114/114 仍仅为实施自验。

以下为既有背景与历史决定；与本节冲突的 reviewer 身份、改进目标和授权以本节为准。

### 本轮交付与后续边界

本轮已完成 PR 级持久 reviewer Session 修复、Pi／运行时已定位缺陷的接入、原生约245k压缩阈值及根负责人实际跟进指令。Mac debug、Linux release 编译通过；真实历史 CLI 副本确认跨候选同锚、不同checkout、旧key幂等不回退current、改派与旧身份停止门控、不同PR独立及无tag原行为。没有用合成session/turn补造原生连续性；后续模型压缩质量、原生实际继续及物理停止成功仍待获授权运行验证。反馈见 `reviewer-session.md`、`runtime-integration.md`。

最新可供后续采用材料为 `runs/iteration15/materials/runtime-integration-20261007/overlay.tar`，SHA256 `7fbf2347a2b235e81c7e2cee45da816171dc1188e9aa13a59b2441880c2225a3`，22466560 bytes、46 overlay成员；99个声明材料成员已按实际底包/overlay读取并核对manifest，root再次核对overlay实际哈希与identity/readback一致。新Braid SHA256 `8540ea7a07df53ff9a84d6e2c2532e5811c28e1ead9895243750217f74931c2d`；模型、角色与冻结standalone gateway配方保留，新增当前统一原生补丁目标、已有e2e状态转移/用例隔离方法。原77c090/其它历史交付保留，新材料未热入已有运行。

结构拆分调查与 matt-skills 学习已形成 `requirements-structure-inquiry.md`，技能正文未修改。原调查仅由职责自述推测合并原因；2026-10-08的决定原件进一步确认，根已比较拆分，却因误判目录容量和扩大基础政策作用域主动选择单PR。具体输入设计与模型采用的上游因果权重仍未隔离。方案以原树为初始候选，以父层规则、真实依赖、跨枝旅程、场景与图片检验边界；保留原则形式并锐化概念、适用条件与完成依据。后续方案先按本页2026-10-08根因结论收敛，再确定技能实施范围与控制变量实验输入；本轮不自行启动。

`run-analysis.md` 已按评分与token成本优先、耗时定位热点的准则完成，并返回具体Session/评论讨论当时选择及竞争解释。Evo主原生账面258997671 tokens，实施占93.75%、单次输入账面峰值537393；I14/I15 Stage2账面133.483M/131.377M，官网6/29与2/29，但继承基线和采集范围不同，不能当改动因果。没有新付费模型/官网评测、在途控制、Factory/Braid测试、smoke、commit或push。保留其它工作区与正在进行的仓库布局重组。

## 当前接续：Evo GitHub 工作拆分与上下文成本改进（2026-10-07）

用户要求：“请建立 task packet；改进后仍然称为 I15。可以停下当前 I15 evo-github 的本地运行了，显然有问题（一个巨大 PR）”。沿用本任务包与 variant `pi-braid-i15-reviewer-cleaner-e2e`，不创建 I16，不沿用历史其它任务的 commit/push 授权。本轮先记录事实、停止指定实验并形成改进方案，不启动新付费运行或官网评测。

当前重点是充分利用 arc-bench requirements 的树、父层规则、依赖、场景与图片形成可交付任务边界，降低各负责人理解负担、幻觉与遗漏，发挥 Braid 协作的主要杠杆。冻结取证确认巨大 PR 在创建时就承接全部实现，而非中途不断扩张。根负责人实际跟进与约245k上下文界限已获得直接实施授权；优先使用Pi已有原生压缩机制，不增加自定义双阈值交接器。原生摘要压缩与Braid新会话reset分开核实，不能把context_hard_bytes当token阈值或修改真实模型容量冒充操作预算。

名称核对：I13原拟arc-requirements已改名arc-bench，依据tasks/iteration13/collaboration-requirements-plan.md；当前技能包含完整需求语义、来源/依赖/责任/证据的区分、覆盖回查和平台交付。职责边界不能成为arc-bench不教授需求拆分方法的理由：arc-bench负责从ARC材料识别产品义务、形成有边界且可验收的任务候选，并解释拆分依据；braid-collaboration负责组织负责人、依赖、并行和成果采用，发现边界不合适时推动调整。

用户进一步指出，只有“完整理解YAML、场景、父层规则和图片，不能机械地按叶子拆任务”的表达，没有给出足够清楚的判断依据。原则型、why/what 型技能受到鼓励；问题是当前概念、适用条件与完成依据含糊，不能一概将原则换成操作步骤。定向证据已确认 root 实际读过技能、列过需求树与Modified段，随后仍将全部需求交给唯一基础PR。具体诊断、原文结构候选与 matt-skills 的可学习模式见 `requirements-structure-inquiry.md`；本轮尚未把该方案改入技能。

待实现的方法方向如下，不强制一节点一Issue，不新增复杂需求台账：

1. 按用户旅程提取入口、前置状态、动作、结果与例外，纳入适用父层规则和图片，并保留原文入口，减少反复重新解释整份需求。
2. 按可独立交付的成果聚合要求。默认把同一用户目标、共享关键状态的要求放在一起；每项任务应能说明交付后新增的完整能力及其可观察的验收结果。
3. 用依赖检验边界。共同业务语义尚未确定且必须同步修改时，先合并或确定共同约定；仅依赖稳定接口时可以分开。共享基础任务只承担明确的共同前提，不能不断吸收全部业务功能。
4. 用验收检验拆分。任务必须等待几乎全部其它工作才能验证，或PR包含多个可以分别交付的用户目标时，重新划分；跨任务的完整旅程仍保留集成验收责任。

当前工作为 reviewer PR级Session修复、运行时修复接入及上下文界限、根跟进改进的实施与材料核对。结构拆分先提出有依据的方案，评价需求层级是否形成清楚责任、场景与父层规则是否仍有遗漏，不能只按Issue/PR数量评价效果。本次不启动新运行或官网评测。

停运范围仅run `20261007-074221-a759c5e4`，Docker CID `7bc0232374ee3bb9b00ec217bb47f72d62c05070726925f4f7fc992c38c872c4`；不是普通Github stages，也不停止官网正式运行。动作前事实、未知与损失记录于runs/hackathon-evolution/i15-evo-github-20261007/user-stop-20261007/stop-plan.json。停止后核对Running=false/Pid0，保留原volume，等待既有归档消费者保存现场；用户停止不记为自然交付，不自动上传评分，也不把磁盘现场称为完整恢复检查点。

停止已确认：2026-10-07 23:05:38北京时间，指定容器退出，Running=false、Pid=0、ExitCode=137、OOMKilled=false；这是用户要求停止后的退出，不是自然完成。回执见 `runs/hackathon-evolution/i15-evo-github-20261007/user-stop-20261007/stop-confirmed.json`。原volume保留，既有终态消费者已记录docker-terminal.json并开始final-frozen归档，归档完整性以freeze-receipt.json为准。停止前最新 `implementation-final-e2e-observation.json` 已记录应用自验114/114，取代此前113/114的进度描述；它不是独立验收，也不消除巨大PR与根负责人监督的调查问题。

完成依据：指定执行停止与现场证据分别确认；后续设计明确任务划分、根负责人检查责任与Pi压缩真实参数，实施沿I15完成。只允许相关源码和材料改动，保留其它任务工作区，不新增Factory/Braid测试。


2026-10-07实验设施任务的补充交付：用户明确要求I15收到PBB停止修复及e2e用例隔离改进。新overlay为`runs/iteration15/materials/pbb-e2e-isolation-20261007/overlay.tar`，SHA452e3b77772a4b0453b8d494a43d2c6cd9a25e17066906ffd1a4d52385b34e1c；专属技能保留business-state-transitions，新PBB成员与技能均已实际归档读回，来源及哈希归同目录package-identity.json。构建用`--protocol-runtime`改用同目录protocol-inputs，该窄输入仅PBB更新，不替换Braid、模型或底包。旧overlay及正在运行的stages不变，后续采用新交付才收到改进；不能把材料形成说成运行热部署。

用户授权：基于 I14 reviewer/cleaner/e2e 组合版推出 I15，“每个 PR 只能指定一个 reviewer”，更新 reviewer Braid Agent 指令，隔离并行验收的数据库等状态；补充“原始 requirements 视为绝对权威”。

初次实现范围为源码与必要文档，不启动新模型实验、不改在途 I14/Pi 运行。初次实现未获提交授权；后续用户明确“可以整理一些提交”，授权整理本任务的本地 Git 提交，未授权 push。保留共享工作区其它修改。Mac 产物全部存放 WorkSSD。

基线为 variants/pi-braid-i14-reviewer-cleaner-e2e，派生独立 I15。单 PR reviewer 约束需覆盖跨候选更新，不能误做成全运行只有一个 reviewer；不同 PR 仍可并行。当前 request 已限制单个负责人，但不同 request 会创建不同 reviewer，需核实并收敛。

root 负责整体判断与采用；advisor 已核实成员投递和停止语义。采用每 PR 一个当前 reviewer 责任与执行、跨候选串行交接；不复用跨 request 的 login。旧请求取消或完成并不等于物理停止，必须复用现有停止屏障收口；冲突指出旧请求，不自动取消。Braid owner `/root/i15_braid_owner` 负责机械约束、所属技术文档和编译/真实 CLI 操作；variant owner `/root/i14_combo_sequential_owner` 负责独立 I15、提示词、打包接线和 variant 索引。reviewer 指令包含原始需求权威、进程级独立数据库/缓存/上传/浏览器/服务/证据，原始交付数据只读复制，不污染候选。反馈使用编译与实际操作，不编写或运行 Factory/Braid 测试。

当前实施边界：只在 I15 显式启用单 PR 约束；原 I14 冻结运行及模型配方保持原身份。I15 不能沿用组合版旧 ZIP overlay 继承旧 Braid 二进制，打包必须实际包含新约束。原始 requirements 的绝对权威指业务验收标准，不允许 PR 描述、设计、自验降低标准。

打包决定：I14 组合版的 frozen-base 还持有当前共用 producer 未提供的 standalone gateway，因此 I15 保留专用 frozen-base overlay，强制提供新 Linux Braid 二进制并替换旧 binary，保存实际 SHA 与编译来源。此轮不扩展 gateway/context 接口或公共交付架构；没有新 Linux binary 时不能宣称完整新包已完成。

必要配套修复：定向接口核对确认旧底包 admission 依赖缺失的 resource sample，而当前 Braid 已无旧等待闭环。仅替换 binary 不可运行；采用现成同版 process-control helper、native-managed 与实际 Pi bundle/dist，局部更新 agent_support.runtime_resource_environment，不改变网关和模型。修复归 variant owner，Braid owner提供具体已有材料与接口证据。无新设施框架或模型实验。

已完成并采用：独立 `variants/pi-braid-i15-reviewer-cleaner-e2e`；单 PR 策略在 request、assign 与实际启动边界生效，完成/取消沿已有 Unassign 收口，blocked 分支同样进入停止路径。reviewer 原始 requirements 权威、每执行状态隔离和 conclude 前关闭自有进程的指令已进入实际 profiles；原模型、角色和工具配方保留。

编译与反馈：Mac debug、Linux release 通过；真实历史 run 的隔离 SQLite/Git 副本通过公开 CLI 观察同 PR 冲突、幂等、不同 PR 独立分配、默认旧行为及 completed/sleeping 不提前释放。来源与局限见 `runs/iteration15/braid-policy/verification.md`，variant 材料接线见 `tasks/iteration15/variant-materials.md`。

最终交付为冻结完整底包加 `runs/iteration15/materials/overlay.tar`，不是重复拷贝出的 ZIP。overlay 22,128,640 bytes、35 成员，当前 SHA256 `77c090261f1a5886b7feb7afcc4879d5aca502bb637df215e854ef15f1645c33`；身份与新 Braid/协议材料记录在同目录 `package-identity.json`。builder 强制新 Linux binary、其来源 receipt 与同版 protocol runtime，实际归档身份已核对。

本轮实现收尾。没有新模型运行、官网评测、Factory/Braid 测试、包 smoke 或 commit/push；未实测新运行的原生 teardown，生命周期反馈以现有实现和隔离历史 CLI 操作为限，真实运行验证待后续运行授权。没有改动在途 I14/Pi 或将隐藏反馈注入生成。

后续调查：用户提出可能简化 reviewer instruction/skills，并怀疑 svc-verification 触发或加载性能。此轮先只读定向抽样 reviewer rollout 与技能发现/加载接口，区分未触发、失败、读后未采用；不因未出现技能名直接断言故障，不跑模型、不改在途运行。I14 稳定 owner 负责实际样本，root 负责指令/目录与加载实现；具体简化范围依据反馈确定。

用户纠正“发现、加载性能”指技能触发、摄取和实际采用的可靠性，并要求参考 matt-skills。已读 mattpocock/skills 当前 writing-for-agents 及 SKILL-MECHANICS（https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents）：context pointer 的措辞决定触发；必需材料应先强化指针而非直接删除；信息分层和消除重复服务稳定行为。前述85ms/2ms只能说明两个文件读取调用成功，不能回答用户的语义问题。四样本显示相同指令下是否读取不同，属于触发一致性线索；具体注意负担/description/skill正文采用的因果仍待运行比较。建议为reviewer缩小默认发现面，先把“按原始需求建立验收判据”设为清晰入口及一次skill触发，并以验收计划/判据/实际旅程证据评价，不以读取次数评价。本次尚未修改源码或启动模型。

reviewer 简化开工：用户明确授权“是的，按这个方向推进”。variant owner `/root/i14_combo_sequential_owner` 接续负责 I15 reviewer 专属默认技能目录（16→7）、清晰单次 svc-verification 触发、职责指令去重和实际 profile 消费、overlay 更新。root/实施者目录及文本保持；原技能文件继续打包，共享 SVC description/body 不改。原始需求权威、冻结候选、每执行隔离、完整旅程、证据与 conclude 收口边界必须保留。只做材料接线/语法/归档核对，不新增模型/官网运行或 Factory/Braid 测试。之前 overlay/identity 保留历史副本，实际行为收益仍须后续运行反馈。

reviewer 简化已完成并采用。实际 native_files 前后材料生成及 launcher/profile 读回确认：reviewer 默认目录16→7，最终职责指令+环境3146→1427字符；两实施profile指令逐字不变、目录仍16。唯一 svc-verification 触发明确为原始需求验收判据建立前读取，保留所有硬边界及三种结论。原skills文件、模型/角色/cleaner和工具配方保持。现有builder已重产overlay，旧材料保存在 materials/history/single-reviewer-protocol-f8624d31；新身份见上文及 package-identity.json。证据见 variant-materials.md 与 runs/iteration15/materials/reviewer-focused-final/readback.json。本轮无模型/官网运行，触发及验收质量的改善未实测，不把输入变短当行为收益。

提交整理已执行：`6f5b0680 feat(braid): 限制每个 PR 的当前评审责任` 仅包含 Braid 本轮 policy、blocked 收口及其 local 技术说明；`7b8f5519 feat(i15): 派生组合版并聚焦独立评审职责` 包含完整 I15 独立目录、variant 索引及唯一必要 support 初始化函数。共享混合文件按 hunk 提交，其它通知文案、运行设施与历史任务修改保留工作区。最后单独提交本 packet、材料反馈及技能调查和工作主题入口。没有推送。

提交依赖核对：HEAD 已有 Braid 相关 schema/方法/Unassign 与 SessionManager 接口；隔离 HEAD 上仅本轮补丁适用性检查通过。I15 源码没有 task_context import，不需纳入该未跟踪文件。builder 使用的 scripts/runtime_resources.py 已在 HEAD；只补充 agent_support.runtime_resource_environment 的同版配置函数。包的 gateway、Linux binary 和 protocol runtime 仍来自明确的外部冻结材料，不能把 clone 当成材料已就绪。原编译和实际 CLI 反馈属于其冻结源码现场，未启动新模型或物理 teardown 验证。

2026-10-07 运行开工：用户明确“接续 GLM-5.3 root，继续完成…可以启动 I15 对 github stages 的完整运行（可以用新的实验基础设施，其原生支持 stages 式）”。I15 实际执行负责人沿用 `/root/i14_combo_sequential_owner`；root/普通/reviewer 保留当前 I15 默认 Flash/high 与原角色配方、千帆优先，自费非参赛。Stage1→2→3必须继承确切上阶段应用和业务数据、独立原生任务；每阶段完成后冻结并独立 self-test，不将隐藏反馈带入后续生成。优先现有 Lab stages 接口，advisor 与 owner 核最小可消费方案；必要局部接线不扩展公共架构，不加人为12小时/费用阈值，启动取证后放手。细节归 stages-run.md 与 runs/iteration15/github-stages-20261007。

另一 GLM-5.3 root 原 manual run 恢复由 `/root/glm53_recovery_owner` 负责，授权和事实归原 packet。之前7小时停滞分析来源是 Flash-root I14 Stage3，不能自动套到 GLM 根运行；本次先有界核现场原因，使用冻结执行器支持的接续接口，原始输入、角色、应用和会话的可继承范围逐项记录。root不混用新Lab控制旧manualrun。

I15 执行入口决定：advisor 与执行 owner 核实新 Lab _assemble 固定公共 builder 参数，而 I15 持有 standalone frozen-base builder；Lab restart 的 data 迁移与 I15 --initial-application 接线也不同。不能仅配置 program_entry 解决。采用现有 manual Docker + 普通 Python 顺序程序，不扩展公共 gateway/context 或重构生产者。Stage1 只消费本阶段公开需求，后续显式继承上阶段冻结应用，保留允许的前阶段原需求为标注基线参考（如官方 prerequisites 已完整则直接复用），不注入隐藏评分。此决定不改变用户目标或费用/模型配方。

I15 GitHub stages 已实际启动（2026-10-07）：Stage1容器 f26-i15-github-stage1-20261007 / 87e207bafe25949d9a76af3fc6761fcb2dfcc89d6392afec979e1d782eb19246，15:14:17北京时间启动；Braid run20261007-071419-c894cc6b。15:17:01千帆TokenPlan Flash request1 HTTP200，已提交上游请求并收到首段响应体，gateway ready，stderr空；这证明实际开始，不代表生成完成。顺序程序PID2788572等待Docker实际终态，逐阶段冻结应用后新output/native接续；Mac完成事件relay PID654准备按stage.frozen独立调用self_test。尚未发生self-test提交或评分。启动后放手，不进行GPT持续轮询。身份和操作事实由执行owner记入 stages-run.md 与对应runs原件。

GLM-root恢复亦已启动：15:09:50原run20261006-125849-7a406ace在新容器b3765f7c...继续，root/Flash已取得千帆200完整响应，PR8继续未提交实现并修复TS错误。原12h timeout移除；恢复保留原应用/Git/Braid/native档案，PR8中断的physical session按现有恢复机制重建。详见其原packet与 recovery/resume2-startup-receipt.json；未混入I15提示或隐藏评分。
