# I14组合版 GitHub 三阶段顺序运行

当前（2026-10-07 19:32 CST核对）：pre403接续Stage3最终34db022c1b1002a1c9c3b24da1296bc52eb5e37d已完成、冻结并取得非正式官网self-test：0/41（41/41 failed），submission657e971b-f608-43a1-ad3c-9a3a963ea430，https://arcbench-selftest-web.vercel.app/submissions/657e971b-f608-43a1-ad3c-9a3a963ea430。ZIP SHA6c98badc...，最终应用评分而非旧timeout或阶段快照。40条首个报告错误为可见导航target缺失，另外1条REQ6-3-3 S2报评测端ReferenceError: uniqueAccount is not defined；不能据此声称41个独立下游业务功能失败；本轮只核结果未诊断。完整回执已由独立进程保存stage3-self-test-r3/{started,status,saved}.json及records/self-test。评分闭环完成，无需重提交或生成干预。

2026-10-06 用户明确：“好的，现在我们将i14组合版的github stages也重新正确接续运行（之前我们错误地在本地也分别运行各stage，而不是接续运行）”。授权本地 `pi-braid-i14-reviewer-cleaner-e2e` 正确阶段生成链及必要窄接入闭环。本轮沿既有评分15/30的 Stage 1确切 commit a11c2ca461b783bad9dc82ef096b8b4049ebdf61应用输入Stage2，再把新Stage2 application输入Stage3；不读取隐藏评测反馈，不混用此前独立阶段应用。Pi实验独立，不控制、不修改。

唯一执行 owner 为 `/root/i14_combo_sequential_owner`。旧 owner 不在当前 live tree；只读核对 sfp7 `development-2` 无运行容器，daemon `e316f857-fe3d-4e7b-8236-9376f063fedc`，镜像 `sha256:3d51899c61e6464242a7545a1badb6445f368f4757828fd36f040c6954b56681`。远端115GB可用，主机13.8GB available；本轮4GiB/no extra swap、2CPU、12h wall，原Braid session预算保护保留。Mac产物全部WorkSSD，旧运行与旧writer现场保留。

实际核最终官网 combo95 ZIP，advisor 是 `Kimi-K3/high`，不是 Pi 的 Kimi-K2.7-code。主线已决定保持 I14 官网原模型角色：根、普通、reviewer、vision/browser 为 Flash/high；advisor K3/high；executor/explorer DeepSeek-V4-Flash-0731/high。本地 I14 千帆/Ark/千问路由与私有配置沿用，不用无额度 ARC API。K3 metadata 原 maxTokens131072 保持：定向历史原gateway日志确认 K3 的 Ark request22 返回HTTP200；日志未含完整payload，不能证明具体max_tokens。没有额外synthetic模型请求，Pi的K2.7 HTTP400不机械套用K3。

必要修复由本次正确接续指令授权：`lab/arc_bench/local_job.py` 原按 backend=pi 误判 Braid 材料为根目录 rawPi，实际 build 因缺根 `agent_support.py` 失败。现按冻结 manifest 是否包含 `runtime/bin/braid` 区分真实布局，保留已有 Pi dirty。原 failed build 留在 `stage1-experiment`，未调用模型。

I14 `run.py` 原只建空 work/application，导致官方 SDK `--template` 即使传入上阶段应用，Braid 仍从空应用开始。采用 advisor 判断，直接复制 SDK 已装配 output-dir 的非保留应用成员到 work/application，在 Braid 启动前 git add/commit 初始快照；不增加新参数或 adapter 特例。真实旧 Stage1 应用仅用于隔离实际复制/clone操作验证，clone能看到 frontend/package.json 同字节；它不是新运行输入。源码variant与派生frozen bundle包含同一接线，三个阶段用同一derived身份；原no-gate bundle不修改。

当前 Stage1 已真实受理：request `i14-sequential-stage1-user-20261006`，attempt `attempt-6347bec2bfb5f1149991093c`，independent runner PID90564、PPID1，incarnation `runner-bd6df4aaa247bbb66f0cbced`。后台进程存活，当前仅确认启动受理与材料执行流程，未核实首个模型响应；不声称已生成。执行目录 `runs/iteration14/sequential-github-stages-20261006/stage1-experiment-seed`。

按用户“启动后放手，不必持续监控，我会定期确认进展”：没有collector/heartbeat/自动后续派发。用户下次询问时读保存状态；完成后读取此确切attempt的application与application_receipt，绑定实际冻结source/manifest创建独立Stage2 intent（schema3当前不支持generate from_job），不得用latest。Stage2完成后同理绑定实际application进入Stage3，再独立self-test评分，评分不注入在途生成。

证据：`runs/iteration14/sequential-github-stages-20261006/startup-receipt.json`、`seed-clone-receipt.json`、`historical-k3-gateway.log`、`intent-seed.json`、`compiled-seed/recipe.json`、`build-seed.log`、`start-stage1.log`。官方公开Stage1需求来源 `runs/iteration14/timeout-retry-20261004/execution/inputs/github-stage-1/requirements`。派生包源 `runs/iteration14/sequential-github-stages-20261006/agent-derived` 继承正式no-gate package SHA `70f134fef768d03b4c6339ac9f6b5837fec7be936cd071f88cf1c80227fd809c`。不commit/push，不运行Factory/Braid测试，不持续监控。

## 2026-10-06 19:12 CST 用户状态查询

仅有界只读，无重启、修复或新阶段启动。新Stage1 attempt6347已失败退出：generation_exit_code=2；具体错误 `copied-tree SDK Pi execution copy differs from its actual frozen source: {"backend":"pi","equal":false}`。错误发生在SDK安装一致性边界，生成容器尚未创建、未启动模型，也没有application。copy-helper已released，原workspace/terminal archive preserved。前次19时前交付只确认accepted与runner存活，不代表模型已进入；现已被此终态覆盖。Stage2/3/selftest待本轮合法Stage1应用，未启动。

同次sfp7查询无running容器；旧fullGitHub与独立Stage2/3均exited，WSL旧独立Stage1也exited。旧Ctrip r15容器已exited0于12:26CST，包装修复评分按timeout-retry权威packet为16/125、score=null，不是待生成运行。共享domain未released资源详见`runs/iteration14/sequential-github-stages-20261006/admission-query-20261006.json`；保留未知预留，不控制、不把created/terminal残留视为运行中的模型。状态摘要及确切时间见同目录`status-summary-20261006.json`。

## 2026-10-06 19:32 CST 改为手动 Docker 启动

用户明确新方案为“手动启动运行，抛弃既有实验基础设施”。本轮不再走 Lab/schema3/copied-tree/admission/reservation/build，不修失败SDKcopy框架。旧6347已终态保全且无writer，旧未知created容器与预留不控制。

直接复用sfp7已经运输的本轮完整派生材料：Docker卷`exp-assets-f5aa943bae267e5259cc675e`的`artifact-bd58625dfadf36ffa4b68be1/payload`，只读volume-subpath挂载`/harness`。没有重新跨网传几GB包。新公开需求与控制脚本小文件传入`/home/yyh/factory26-manual-sequential-20261006/stage1/`，应用output独立为空。private700/600及Braid/Node755已确认，因此入口不需写只读源包；不注入旧FACTORY26_EXP_ATTEMPT_ID/services/OTLP设施变量，入口使用原standalone collector/gateway和Braid预算。

实际容器`f26-i14-sequential-manual-stage1-20261006`、ID`5e4d14ed57d5ae91d7a8cca52dc30f59d17b7e96989bd91b12035f9a80663f62`，19:32:41 CST启动，run`20261006-113241-563d35cb`。命令`python3 -B /harness/main.py /requirements --output-dir /output`，MODEL/VISUAL_MODEL Flash，保留K3和DeepSeek原roles/routes。实际读回Python、standalone OTLP、Rustgateway、Braidlocal及Pi进程，容器running，stderr空；尚未核模型响应。4GiB memory+memory-swap、2CPU、512pid，timeout43200s/TERM+60sKILL，退出码与始终时间保存control/agent.exit、started-at、finished-at，容器与源卷保留。

启动后已放手：无监控/collector循环/自动Stage2派发。用户查进度后读取此准确run；Stage2消费本轮Stage1冻结应用，Stage3消费其Stage2，沿同一derivedseed+Git初始提交接线，再独立selftest。启动回执与inspect在`runs/iteration14/sequential-github-stages-20261006/manual-stage1/`。旧Lab失败状态仍为历史原件，不作当前执行入口。

## 2026-10-06 用户纠正：复用已有 Stage1

用户指出“i14应该之前有stage1结果啊？”。主线承认此前fresh Stage1假设过度，本轮正确接续改为已有Stage1→手动Stage2→新Stage2应用→Stage3。已有授权覆盖这项纠正。确切Stage1 run20261004-142939-bc8d926a，恢复完成commit a11c2ca461b783bad9dc82ef096b8b4049ebdf61，quiescent/根IssueClosed/scope_closed；selftest c7bc34ff-f424-4978-9baa-81e4fd6396d3为15/30，包装stage1-offline3 SHAa5cb2ea...。variant和正式no-gate parent70f134...与本轮相同；本轮派生只加seed初始化，不改变roles。

应用来源是原生成Git commit的git archive，不使用评分包装Docker层/隐藏测试反馈。Archive只包含.gitignore、README、backend、docs、e2e、frontend、tasks；未包含原运行、native/Braid、requirement/test反馈或凭据。Stage2公开requirements/prerequisites/assets/reference单独提供。

已向自家多余freshStage1 ID5e4d...发送docker stop，停止前事实/未知/目的/可能丢失已保留manual-stage1/stop-intent.txt；全部远端output/control和容器保留。新Stage2在停止确认后建立唯一容器，控制日志与应用output分开，原seed为app-only。

Stage1多余fresh容器已确认停止，after-user-correction-stop.json保留退出身份；源output/control容器不删。19:40:37 CST 手动Stage2实际启动：容器`f26-i14-sequential-manual-stage2-20261006`，ID`dba8ec94ab034c3648128d528c18f909919717800299059063d540031f4d58ad`，run`20261006-114037-ce316bc6`。实际Python/OTLP/Rustgateway/Braid/Pi进程齐全，stderr空，running；首模型响应未核实。沿同derived卷source与4GiB/no extra swap、2CPU、12h timeout合同。

实际读取新Braid origin中initial_application_commit，确认frontend/package.json在该起始commit可见，SHA与旧Stage1 a11c2ca对应文件完全一致；不是仅output目录存在而Git clone为空。证据`manual-stage2/seed-origin-receipt.json`、`baseline-receipt.json`、`startup-receipt.json`。当前正确链条已有Stage1→运行中Stage2，Stage3与selftest待用户询问进度后接续；已放手，不持续监控。

## 2026-10-06 20:03 CST 进度查询

当前手动Stage2 run20261006-114037-ce316bc6仍running，无exit文件、stderr空、无Braid交付result。HTTP实际累计Flash39次200、Ark K3四次200，其中request44已complete、45已收到流式正文。模型参数未出现Pi先前的K2.7输出上限错误。

原生主Agent49次工具调用，已读公开REQ3/REQ4及继承前提，完成14张reference截图视觉解读摘要，正在等待K3 advisor收敛仓库资产与版本控制设计；DB仍仅rootIssue1，尚未实现PR。进度为需求/设计阶段，不声称应用完成。Stage3/selftest未启动。只读有界查询，无持续监控或控制。证据`manual-stage2/status-20261006T2003+0800.json`，远端原始gateway/native保持原output。

## 2026-10-06 20:50 CST 进度查询

手动Stage2仍running，无exit、stderr或交付result。设计已提交f91c6a6，PR2正在实施REQ3仓库资产管理与REQ4代码版本控制；backend仓库路由、db、permissions、seed已修改，新增versioning/diff/repos2，frontend Header与validation正在接入。PR成员110次原生工具调用，尚无ready_commit。实际HTTP累计Flash167次200、ArkK3四次200，无模型HTTP错误。未完成阶段，不启动Stage3/selftest。只读有界查询，证据`manual-stage2/status-20261006T2050+0800.json`。

## 2026-10-06 21:55 CST 进度查询

Stage2候选实施完成commit4f5c47d，PR2工作树clean，review1/review2 pending，尚无最终delivery或退出。Agent自身packet报告E2E59/59（Stage2 29场景）及冷启动验收通过，只标自验，不冒充官方评分。模型Flash422次HTTP200、14次千帆429 rate limit；实际fallback到Ark200并complete（例request432），无终止故障。K3四次Ark200。最近21:55有新模型请求，Stage3/selftest继续等正式交付。仅只读有界查询，详情`manual-stage2/status-20261006T2155+0800.json`。

## 2026-10-06 22:25 CST 进度查询

Stage2仍running，无exit/stderr/delivery。review2于22:21提出changes_requested：Create new file路径与既有文件恰同名时未报Invalid file path而静默覆盖，违反REQ4-4；独立review已复验59场景，但发现场景之外的需求缺口。实现成员22:21已进入处理turn，开发侧不介入生成业务修复。Flash664次200/35次千帆429，K3四次200；千帆优先和现有Arkfallback未变，最近22:25模型200。无有效交付，不启动Stage3/selftest。证据`manual-stage2/status-20261006T2225+0800.json`。

## 2026-10-06 23:49 CST Stage2终态与冻结

原manualStage2于23:29:44容器exit1，无OOM。Braid已正常完整闭合，最后delivery commit1f273516；review3、review4 approved，同名路径覆盖缺陷已修复。入口`deliver(run/application, output)`的同名文件保护拒绝覆盖之前放在output的Stage1 seed，原始错误“输出目录已有同名应用文件，拒绝覆盖”已保存。source `run/application`生成出口在deliver之前已准备，不把此碰撞记为业务失败。

本次只按父任务状态查询边界freeze exact Git application，无源码修复、新Stage3或评分。实际Git archive已回收WorkSSD并解包，receipt包含源commit、tar SHA、上阶段来源与后续可绑定路径。原远端seed/output、生成run、stderr和容器保留。Flash1112次200/54次千帆429，K3四次Ark200；gateway正常stopped，千帆优先未改。证据manual-stage2/terminal-agent.stderr、terminal-braid-result.json、frozen-application-receipt.json、status-20261006T2349+0800.json。

## 2026-10-06 Stage2评分与Stage3接续授权

用户明确要求I14/Pi Stage2整理self-test取评分，并可接续Stage3。此owner只负责I14；不碰Pi或fullGitHub，不操作官方UI。root统一评分上传。

顺序发布根因完整闭环采用advisor修正：不再自动从output猜seed。入口新CLI `--initial-application`使用原copy_application复制只读上阶段应用，output保持独立空应用区；保留原seed初始Git提交。variant源码及小run.py overlay、对应package-manifest身份已更新，旧正式freeze/远端卷不改。没有其它source变化或设施测试。

23:56:38CST Stage3唯一容器ca973d5d6504f293a867066d54701d1a3df1d994efe468e68ebed1be1076c810（f26-i14-sequential-manual-stage3-20261006）真实running，run20261006-155638-60f0ce5d。Stage2 commit1f273516实际Git archive只读挂/initial-application，Stage3公开requirements/prerequisites/assets/reference单独提供，/output空。Braid origin初始commit的backend/src/routes/repos2.ts与Stage2 source同字节；Python/OTLP/Rustgateway/Braid/Pi真实进程齐全，首模型响应未核。4GiB/noextra swap、2CPU、512pid、12h timeout。启动后放手，无评分回流。证据manual-stage3/startup-receipt.json、seed-origin-receipt.json、run-stage3.py、package-manifest.json。

Stage2自测包装仅compiled frontend/backend+生产Linux依赖+根Dockerfile/runtime tar，不改业务源码。LinuxNode20.19.3前后端build完成；首次Ubuntu构建的SQLite native库在bookworm slim实启动报GLIBC_2.38缺失，原失败包与startcheck.log保留，正在bookworm Node20.19.3重建SQLite native依赖以修正ABI。此为包装兼容闭环，不是假业务零分。

## 2026-10-07 00:01 CST I14 Stage2自测包就绪

LinuxNode20.19.3前后端构建完成，SQLite native以匹配bookworm Node20.19.3重编，实际`docker build --network=none`通过；禁网容器启动后`/`、`/signin`、`/api/orgs/public`均HTTP200。首次GLIBC不匹配包和日志保留，不改业务源码。根Dockerfile与runtime.tar二成员ZIP满足50MB限制。唯一上传owner root，执行owner不操作官方UI。来源run20261006-114037-ce316bc6/finalcommit1f273516，详细ZIP绝对路径与SHA见manual-stage2/selftest/packaging-receipt.json。Stage3继续独立生成，不输入评分反馈。


## 2026-10-07 Stage2 self-test 提交

I14冻结应用已由root通过已登录的xiaoland账号提交 github-stage-2-req-test，结果页：https://arcbench-selftest-web.vercel.app/submissions/7f61a236-957d-42cf-a3f6-346ca35784d4。评测已完成：通过 6/29，未通过 23；结果页已由root实际核实。共同提交身份及包SHA记录在 runs/stage2-selftest-20261006/submission-receipts.json；两条Stage3已按各自确切Stage2应用启动，评分反馈不会进入生成。

评分原始页面、代表性错误与截图保存于 runs/stage2-selftest-20261006/。两份代表性错误均为 `Could not find a visible navigation target named "acme-docs"`；尚未据此完成根因诊断，不将该错误送入Stage3生成。既定本次提交和Stage3启动已完成；继续用户启动后放手偏好，后续生成状态待用户查询，最终Stage3冻结及评分仍待生成终态。

## Stage 2 评分开发侧溯源（2026-10-07）

完整23失败的首个暴露错误均为navigation target缺失，目标计数acme-docs12、visibility-demo2、branch-switch-demo4、default-branch-demo2、file-management-demo2、Document search flow1。官网diff失败截图停在未登录首页，现有证据未确认其下游业务断言失败或是否执行部分断言。精确评分镜像实际HTTP确认acme-docs搜索与Document search flow提交seed存在；首页不直接列仓库/commit，而自验统一Search进入，该路径符合公开需求；官方具体前置路径仍未知。另独立确认冻结应用遗漏UnoCSS虚拟样式导入，CSS请求200但内容仅823字节手写规则，非包装丢资源；该缺陷继承Stage1。59/59自验覆盖自身入口与功能文字断言，未覆盖官网前置差异及视觉样式。详见runs/iteration14/sequential-github-stages-20261006/manual-stage2/selftest/analysis.md和runtime-http-observation.json。只分析、不改业务、不控制Stage3/其他运行、不输入隐藏反馈。

## I14公开Search刷新路径复现（2026-10-07）

用户授权继续诊断后，独立确切评分镜像+Chrome真实执行未登录Home→Search acme-docs→精确结果→repooverview→reload，刷新后URL仍/orgs/1/repos/1、heading保留，公开S4通过。排除该路径必现应用刷新故障，官方实际前置动作仍未知。官网现有S4可见附件只error+PNG，无动作/URL/trace入口，未探测私有API/评测器、未另提交。每步URL/DOM、刷新后截图、镜像身份见manual-stage2/selftest/browser-replay/；详细判断更新analysis.md。未改业务或影响Stage3。

## Stage3只读进展（2026-10-07 01:14 CST）

I14手动Stage3仍running，无退出文件/agentstderr/最终交付。Stage3需求设计commit967203a已创建PR2，尚无reviewrequest或readycommit；实现工作树已有issues/pulls/merge后端与issue/pull/compare前端页面，仍未提交完成。当前Flash累计205次HTTP200、1次千帆429，K3五次200；近期模型请求与工具操作持续，模型路由未终止失败。尚未完成，因此最终冻结重放和官网Stage3评分没有发生；启动后没有自动监控/上传程序，本次只查询。原始快照manual-stage3/status-20261007T0115+0800.json，实际查询01:14:18CST。不控制、不恢复、不重评。

## Stage3只读进展（2026-10-07 10:19 CST）

容器仍running，无exit/agentstderr/最终交付；不能据此声称评审正常推进。PR2候选2a951d49cf218aef7800d50f9266464b8b4a02c4于02:29完成，Agent自验报告87/87，review1从02:31至查询时仍pending。reviewer native最后assistant02:56:53为error：HTTP403 AccessDenied.Unpurchased（Access to model denied. Please make sure you are eligible for using the model.）；对应gateway request572千帆429→Ark429→Qwen403 upstream_http_error。reviewer计划02:33、原生后续记录至02:58，此后未见新语义动作；root仍周期检查/10:19千帆200，但未形成review结论。实际累计Flash730次200/120次429/4次403，K3五次200。没有Stage3最终freeze或官网回执。只读快照status-20261007T1019+0800.json保留具体错误及角色活动，不进行恢复/控制/重评。

## Stage3恢复准备（待采用，未操作）

已核reviewer为activeassignment/idleprovider，两turn failed403、wake全部consumed；物理native/history/固定review1候选/checkout保留，非runningturn。最窄候选恢复为公开Braid PRcomment @reviewer-1生成新wake，继续原会话，不停止、不改DB或RPC、不重派或更换模型预算；同成员assign为no-op，offline-resume不适用仍活跃执行。原12h截止11:56:38CST不延长。准备事实/未知/目的/潜在损失见manual-stage3/recovery-preparation.md，尚未执行，交root采用。

## Stage3原review会话接续（2026-10-07 10:23 CST）

root采用已授权设施错误闭环后，10:22:56通过冻结Braid宿主公开--external pr comment接口创建唯一运维评论117，@reviewer-1，只说明已结束provider错误与继续既定review1，不含评分/样式反馈。初次未声明宿主--external门控拒绝且无写入，随后沿明确宿主接口成功。10:23:23一次实际receipt确认同provider session启动新runningturn01a1142b-e02e-7d52-b450-2809b60e94f4、directwake consumed，原native产生新assistant有效判断并读comment117；Flash/千帆200。固定候选、checkout、native历史/模型/预算/11:56:38期限未改，未停容器/直接改DB或RPC。证据reviewer-recovery-action.json、reviewer-recovery-receipt.json、reviewer-recovery-comment.txt，完成一次恢复回读后已放手，不循环监控。

## UnoCSS过程定向溯源（2026-10-07）

Stage1实施者22:48:58原生明确计划main.tsx含UnoCSS import，但22:54:07实际写入只有styles.css；23:09绿色构建已输出同index-BeNvGEil.css/0.82kB。首提交c589828、Stage1finala11与Stage2final1f273516保留遗漏。Stage2根/实施/reviewer实际读或改main，目的主要route/控件/行为；vision看14reference、review4唯一image为reference sign-in，不是产物截图。reviewer有真实浏览器语义走查/存截图并明确称视觉结构一致，故不能断言没人看视觉；后续验收未发现缺漏是事实，plugin自动注入误认/具体心理原因未见直接证据。analysis.md新增过程章，区分明确判断、产出证据、边界推断与未知，原生定向索引在selftest/unocss-*.json。Stage3不接收此反馈。

用户glm-5.3新增QwenTokenPlan路由指示由公共配置owner执行，root已确认四链；本Stage3实际故障/恢复alias为glm-5.3-flash，不自动扩大到Flash、不热停当前run。

## Stage3有界状态（2026-10-07 11:24 CST）

11:24:11实际读取容器仍running、exit无记录、agent.stderr为空；review1于10:56:33 approved，403后同会话恢复已产生有效评审。独立评审随后核实公开REQ-6-6 S2所需pr-viewer账户未被seed供给，既有e2e用了issue-viewer替代，文字行为验收通过但未验证逐字账户契约；reviewer1纠正先前“全种子匹配”表述。生成根成员11:12:52要求glm-3在整合PR补入该账户、直接read权限与对应e2e账户，并发布复验。最新11:19:27 turn completed无error。尚无有效终态、最终冻结或Stage3官网回执；不以先前候选或自验计数冒充最终交付。证据manual-stage3/status-20261007T1123+0800.json。此轮仅读取，不控制、不恢复、不更新冻结模型/指令、不注入外部评测反馈。

同次有限补读确认整合PR3已创建，两原生turn仍running且error为空；gateway最近request1316为glm-5.3-flash/千帆HTTP200 complete（2026-10-07T11:25:34.764000+08:00）。最新有限尾未见新的provider失败，非全程无错声明。已放手，无新监控。

## Stage3截止终态与接续准备（2026-10-07 12:04 CST）

实际137停止由12h TERM+60s强杀导致，stderr Killed，非OOM，run error为运行终止信号。尚无最终Braid result/交付应用；PR4 seed修复ce03d8e已完成，但review3未结论，最后证据提出docs合并冲突/候选基线问题，PR3仍draft。保留原Git/Braid/native/current容器现场，未把可用候选当最终交付。冻Braid公开CLI实际支持offline-resume；建议同路径、同配方、同原生会话的保留接续，必要恢复控制接线与/tmp证据保全范围见manual-stage3/timeout-recovery-proposal.md。原冻run.py无resume入口，当前源码已有retained_resume，不能顺带注入新Tailwind指令。此次只准备，root未采用前不恢复/扩大期限。

## Stage3时间profiling完成（2026-10-07）

用户授权“诊断i14 stage3运行这么久原因（时间profiling）”。现有DB/native/gateway/control定向聚合确认总12h01m，其中review失败后无新wake为7h26m08（61.88%）；自动failed-turn replay一次又失败，之后根成员84轮/168正常模型请求只检查PR表面状态，并明确误判评审进行中。10:23直接唤醒原会话→10:56 Approved验证这一阻塞路径。恢复后有head漂移处理、种子缺口、重复实施与PR4/PR3串联，deadline前PR3未完成；review3最后发现docs真实base合并冲突但未提交结论。分析、不可相加的role/tool/API时段及不确定见manual-stage3/profiling/analysis.md，机器timeline.csv/json和summary.json配套。此轮仅分析，无恢复、新运行、费用或业务/设施修改；恢复准备仍待采用。

## 一次性pre403应用接续（2026-10-07 12:26 CST）

用户原话“从模型错误前接续恢复吧（但不要做通用恢复能力）”。调查确认只有23:56初始化前4096字节空表SQLite backup，无02:56前Git/application+Braid/native共同检查点。原native在02:56:51最后前景curl已回执，但后台e2e/临时服务运行中，不能用截取JSONL与单Git提交冒称完整检查点。此前首模型504在00:58，导致长停滞的关键403在02:56；本次按后者之前的候选起点。证据manual-stage3/pre-error-recovery-evidence.json。

主线采用A：用commit2a951d49cf218aef7800d50f9266464b8b4a02c4（02:29、tree99ed07c9）的Gitarchive作为新initial-application，含原设计与业务、e2e源码；121 trackedfiles/1361920字节，SHA6390351304438fd286ea0c5786e45ebc6b4c325555129a546bac2e6ec12fb299，不含旧runtime/control/evidence。新的Braid/native从此应用继续原Stage3评审整合，不回放旧DB或截拼会话；不输入后403产生的pr-viewer修复点、旧Stage2评测或现行Tailwind指令。旧packet87pass明确只属历史，新候选/新服务必须实际验收。旧候选后产生的业务变更与评审进度留在原现场，不纳入新输入；旧临时服务也不保进程。

12:25:57CST容器277d6db72186a00179e99593fd6da8211a0348139fcd8366201871134176b791，名称f26-i14-stage3-pre403-app-20261007，run20261007-042557-61978851。遠端/home/yyh/factory26-manual-sequential-20261006/stage3-pre403-2a951d4-20261007，output和seed分离，原公开requirements只读复用。仍原4GiB/2CPU/512pid，本地自费人工12h timeout已移除；保留原Braid session预算保护。复用原镜像/RO资源volume-subpath，原冻run.py仅增加本次操作说明，overlaySHA1e848cf29c66b9e7d39205237404dd6c0e58e62a2d1849ac116cc18cd5da1df7；所有代码变动只在runs内一次性控制文件，不改共享源码或通用恢复能力，无commit/push。

12:26:15实际startup readback无exit/stderr，首三次Flash千帆HTTP200；新origin初始HEAD可见frontend/src/main.tsx且与候选source字节一致，初始Git commitf0ad0b8a26314c5d183597760a0c1d0d6355df7a。root已读原技能与新工作树Git状态。gateway相较旧运行的catalog_sha/routes_sha/deployments/limits完全相同，仅run_id不同；没有擅改Flash链。回执manual-stage3-pre403-2a951d4/startup-receipt.json、baseline-receipt.json、model-recipe-continuity.json、startup-semantic.json、docker-launch.json。

已完成最小启动核对后放手，不建立GPT轮询、collector或新监控。自然交付后由原owner freeze并非正式selftest；若同模型错误再次形成阻塞，保留具体错误后可用已有公开任务唤醒一次运维接续，不建立通用自动重试。

本次已挂一次原生docker wait（exec session31968），仅等待停止并写manual-stage3-pre403-2a951d4/native-wait-terminal.json，无周期轮询。工具等待本身不自动触发新Agent turn，也没有自动freeze/UI评分程序；评分仍需owner在完成通知/用户进展查询接续后执行，当前不宣称“自动评分在途”。先读取该持久receipt或续取session，无需重复采集运行。

## 新接续运行一次状态（2026-10-07 12:54 CST）

12:54:19实际读取的是新run20261007-042557-61978851，不用旧timeoutrun替代。容器仍running、stderr空、exit不存在。PR2候选核实已完成；Agent报告本轮e2e103/103、backend149、frontend24与平台路径验收，尚非官方评分。review1固定c875a80，但实施者packet更正移动head到631a1b8，root又向develop提交packet使base移到252c8b6，Braid标记适用性失效。生成成员12:52–12:53承认并处置纯记账时序失误，重新冻结base/head建立review2，并约定评审/合并结束前不再推记账；12:54 reviewer2 turn实际running，pending结论，无最终交付。只报告生成过程，不由开发Agent插入修复意见。

累计千帆Flash163次200/21次429，Ark19次200/2次429，Qwen2次200；fallback沿原链成功，turn_errors与model_terminal_errors均为空。最新实际HTTP千帆200。尚无Stage3冻结应用及官网self-test回执，仍待有效生成终态。证据manual-stage3-pre403-2a951d4/status-20261007T125415+0800.json和model-errors-20261007T1254+0800.json。查询结束放手，不重启/持续采样。

## 新接续运行一次状态（2026-10-07 13:33 CST）

13:33:19当前新run61978851仍running，exit不存在/stderr空，Braid delivery_commit为空，review1固定c875a80与review2固定631a1b8均pending。真实活性再核：两个reviewer原turn/provider仍running、failed_turns为空；13:33 reviewer1核验merged PR的PATCH状态与viewer负面合并权限、登录参数，reviewer2实际浏览器核组织/仓库/Issues链接，正排查自身验收脚本Open locator等待超时（独立debug能成功导航，尚无产品缺陷结论）。不能因根成员周期检查/模型token判正常，这次有具体native工具/结果证明评审活动。

模型累计千帆407×200/127×429，Ark116×200/11×429，Qwen11×200；13:08和13:11各有headers_or_total_timeout，具体gateway事件已保留，但未形成failed turn且后续继续成功，未出现本轮403。最新千帆200在13:33。未取得有效生成终态/冻结应用/Stage3selftest回执，当前不评分。证据manual-stage3-pre403-2a951d4/status-20261007T133315+0800.json与reviewer-activity-20261007T1333+0800.json。已有授权失败后运维唤醒不适用于当前active状态，因此不干预；查询结束放手。


## 新接续运行一次状态（2026-10-07 14:59 CST）

容器身份277d6db72186a00179e99593fd6da8211a0348139fcd8366201871134176b791保持，14:58:46 running/nonOOM、stderr空，run仍generating，无delivery.json。14:59:56 Braid只读快照确认review1/2已分别ChangesRequested，唯一阻断是REQ-6-6 S2命名种子账户pr-viewer缺失；生成成员提交7853c36修复，review3固定e085966于14:52:23 Approved，独立真实页面/API/seed及检查证据归候选原生记录。review3自报backend150、frontend24、e2e103全通过，不是官方评分；还如实记录并发首轮2failed/148passed后两轮干净通过且未完整定位的观察。

PR2已合入develop（420742b），14:54交接PR3 develop→main整合验收。14:59:28–36 glm-3实际继续：本轮backend150/150，平台frontend/backend npm install成功，正做正式frontend构建、backend启动合同和全量e2e；注意到一个后台pnpm命令未cd backend，开始查该执行状态，不把它归为业务失败。两个当前turn/provider running、failed_turns为空，未形成待处理review停滞；不控制或修复。宿主SQLite mode=ro曾遇attempt to write readonly database，改从当前容器namespace mode=ro成功读取真实WAL，不改DB，不以immutable旧页替代。无最终冻结应用或新Stage3官方评分，待有效完成由既有owner冻结并独立selftest。

证据为runs/iteration14/sequential-github-stages-20261006/manual-stage3-pre403-2a951d4/status-20261007T1500+0800.json（实际observed_at14:59:56，少量当前review/turn/native/comment）。查询结束放手，没有新运行、唤醒或持续采样。

2026-10-07 18:17 CST评分查询：尚未上传或获得submission/分数。初次独立包装因better-sqlite3无Node20 Linux预编译包而转node-gyp，构建镜像缺Python（Could not find any Python installation）导致失败；原日志保留stage3-self-test/build.log/error.json。此为包装设施故障，不是有效零分。按既有授权，仅为builder安装Python3/make/g++，同冻结34db022c源码不变，r2独立上下文/产物避免覆盖失败证据；score_final_r2.py由项目venv后台PID88713执行，状态归stage3-self-test-r2/和score-final-r2-process.json。尚未取得新官方回执，放手不GPT循环等待。

2026-10-07 18:24 CST评分查询：尚无官网受理或分数。r2已完成Linux前后端构建及原生依赖编译，但scratch提取容器`docker create`缺命令，报no command specified。r3仅补提取命令并复用已构建镜像，不重建/生成、不改冻结34db022c业务；后台PID91189，记录score-final-r3-process.json及stage3-self-test-r3/，r1/r2原错误保留。
