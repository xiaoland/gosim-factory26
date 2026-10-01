# iteration11 GitHub 运行审查

已完成两个固定采集窗口内全部已取得原生记录的可读实质内容审查：首轮111个canonical单元、9,035条记录，以及唯一末尾增量824条记录。图片像素、原生截断与采集竞态等边界见末节；逐源回执以 `coverage.json` 为准。

## 结论

运行能通过独立审查、真实应用检查和共享契约修订纠正实现问题，但候选验收的连续性明显受上下文重建影响。最值得优先处理的是：reset之后旧后台检查没有可消费终态，新会话又仅凭当前实例的空列表重启同候选；同时 reset 期间的评论排队使基线更新迟到。另一个独立问题是检查命令先过滤错误，后续把重跑通过解释为已排除代码问题。这三条分别影响工作寿命、输入时效和结论可信度，不能用一种通知或日志补丁一起解释。

本文没有修改 Harness、生成应用或运行状态，没有运行测试、实验或提交。这里的 PASS/FAIL 都是被审查运行留下的证据。

## 运行身份与截点

审查对象为 `e20260928-03-check-receipts` 的 GitHub 应用题生成过程；文中Issue/PR均指这次Braid内部协作工作项。inner `20260929-042409-1202e245`。恢复链是 `generation → hotfix-01/generation-02 → hotfix-02/generation`。按hotfix02恢复身份，末段源码比对版本为 Braid `5c957436f5aead2c2f4d49a6a5030d8e22d9863d`；没有为每个native单独保存到进程二进制哈希的绑定证明。初版和hotfix01的错误不当作末段新故障。

首轮采集为 **2026-09-29 08:04:30.462358–08:04:36.517118 UTC**（北京时间16:04），成本口径固定在采集开始。唯一末尾增量为 **08:26:07.983932–08:26:12.309318 UTC**（北京时间16:26）。两个窗口都逐文件采集，SQLite 源只读并备份到内存；这是证据快照，不是可恢复运行检查点。末尾 Braid 日志记录08:26:07创建的 ec45 会话，但native文件未进入manifest，存在采集竞态缺口；不继续追赶运行。

固定增量中，根实际调用 `braid pr merge 13 --match-head-commit d62907d…`，回包与随后 `git fetch/rev-parse` 均为 `e9390cc5a7ad309760402db83d9c97e293abc420`。PR #13 已合并是双重证据确认，运行整体仍未完成。#7/#9/#10 尚待前置模块；不能评价最终应用分数或完整需求交付。

## 优先问题

### 1. 后台工作与 Braid turn 寿命分离，造成重复验收和交接失败（I11-05）

根对 PR #13 `d62907d` 的启动链如下；表中的“启动”不等于完整跑完，也不等于四轮全程并行。

| 原生会话 | 实际启动 UTC | PBB 身份 | 可见结果 |
| --- | --- | --- | --- |
| ec0c `01a0ec0c-a630…` | 07:27:57.947 | `pbb_44038_2d44e69d:bg001` | 07:38仍在安装；自改正文后reset；后取旧日志只到12/51、无退出行、PID已消失，metadata仍running |
| ec1b `01a0ec1b-72e5…` | 07:43:06.805 | `pbb_55555…:bg001` | 平台51PASS；额外Vitest先遇Node24 ABI错误，改Node20后94/95，restart超时；结果未完整写回接续入口 |
| ec2f `01a0ec2f-cecd…` | 08:08:20.888 | `pbb_67630_ddca7f49:bg001` | 自改正文后reset；08:10:58平台到26/51，随后新会话；末尾未采得该job终态 |
| ec38 `01a0ec38-bc87…` | 08:15:57.946 | `pbb_73745_ccda7c62:bg001` | 平台51PASS/exit0、Vitest95PASS/exit0，08:24:43合入PR13 |

**因果链。** `5c957436` 的 `worker.rs:337–345` 在 reset notice 已处理且 turn completed 时调用 `sessions.remove`；`session_manager.rs:142–164` 调 `factory.teardown`；Pi factory 调 `close_native`，通过关闭stdin让Pi执行dispose与扩展shutdown。部署PBB的 `session_shutdown` 调 `abortAllJobs`，会abort并向进程组发SIGTERM。源码与实际会话更替、旧PID消失、半成品日志相互支持：重建会结束作业所有者，并有取消其作业的代码路径。但首轮没有直接signal/exit回执，不能断言每个旧job最终都被SIGTERM取消。此版Pi适配已用 `agent_settled` 判turn结束，并非误把 `message_end` 当终态；具体后台登记/等待缺口仍需在该边界判别。另一方面，PBB `agent_end` 对无UI的finite jobs有等待分支，因此不能声称所有turn结束都杀作业。

新会话则反复把 `pbb list scope=current-instance jobs=0` 当成上一检查不存在的证据，没有先用旧globalJobId或日志定位。原生共同指令已经要求恢复先查旧任务、列表为空不能排除旧实例；问题不只是少了一句提示。正文只保存“验证运行中”，缺少可消费的job终态和已取得局部结论，使重建后重复排查。

**第四轮证据也有环境边界。** ec38 r23–24把archive解到既存 `/tmp/verify-pr13`，目录里已有 `node_modules`、`test-results`；r28看到了仍猜测可能被提交。实际 `checks/platform-path.sh` 要求调用者提供干净副本，有Playwright时跳过root install。本轮PASS成立，但不能升格为根侧干净安装证明。owner另有其自己的平台证据，必须分开记。

**最小改进方向。** 在现有reset与原生后台完成协议中明确finite work何时算完成；重建前若取消，持久化取消原因与终态；接续输入应能引用旧job和已保存结果，避免只给“运行中”。优先修复现有生命周期和证据交接，不新增通用任务平台。验收需用同候选启动检查→自改正文触发reset的实际操作，核对旧作业完成或明确取消、接续者消费对应终态，且不会凭当前实例空列表盲目重启。

**另一个具体边界：检查结束后的原生续接仍不能写 Braid。** PR14 ebf5 在同一 `9bedf84` / `53532a0` 上重新运行检查，原 Braid turn 于07:00:40完成。后台结果到达后，原生会话继续尝试交接结果，07:01:30起评论/ready写调用反复返回“当前调用已失效，本次修改未写入”；只读状态显示正确binding，但provider idle且没有对应running turn。07:13:04新notice后才成功写出#101。冻结DB和native相互支持“后台续接没有获得对应可写turn”的判断；这里没有reset kill或错误绑定证据，不能与PR13的取消路径混为一谈。PR11还有独立旁证：初始turn06:40:30完成，干净副本复验06:42:45才结束，06:42:58起写入被拒；06:47:19普通wake后#75成功发布。PR11通过普通wake恢复，PR14通过新notice恢复；本案的#75与#101最终均成功写入，不能报为永久缺失。详见 `cells/m3/pr14-lifecycle.md`、`cells/m3/pr11-lifecycle.md`。

**反证限制修复范围。** PR14前一会话ebed两次 `subagent_wait` 分别实际等待34秒、5分4秒并取得e2e/平台终态；其中平台运行前明确删除并重建archive目录。PBB等待并非普遍失效。现有有限作业等待路径应保留，重点判断reset、原生续接与Braid turn登记何时分离，而不是直接增加另一个后台框架。

基础 PR2 也有早期同类现象：仅文档改变就启动第二条平台检查，reset后再启动同a7cc9b5；之后接受docs-only等价。发生在旧版恢复背景，作为复现旁证，不混算末段新故障。详见 `cells/root/background-reset.md`、`cells/foundation/primary-notes.md`。

### 2. reset notice 长turn挡住评论投递，基线要求晚于旧基线验收（I11-03）

PR #16 #110 于07:22:55要求合并新develop后复验。给根的回执是delivered，给worker glm-12的是queued。完整native核对表明07:22:55–07:49:16间worker既没收到此评论输入，也没主动调用issue/pr/comment view读它。07:49:03先发布旧基线 `24a6ed7` 的91 Vitest、46 e2e及平台PASS；07:49:16收到正文reset摘要，07:49:22主动读Issue6正文，才看到 `develop=f6e326c` 并开始合并。

该worker的 `context_reset_notice` turn从07:06:16持续到07:49:15，约43分钟。源码 `worker.rs:522–526` 仅在reset_id为空时转发running input；`dispatch.rs:608–649` 对reset notice已有reset_id直接返回；store领取running input另排除pending invalidate。queued评论只在wake/steer被接受后转为delivered。这能解释延迟，证据不支持随机丢信。07:06:24的交接#91也晚于worker首次07:06:20读取PR，新增评论未消费；但PR正文已有设计，不能说worker没有设计输入。

**影响与边界。** worker在旧base上完成了一轮有效局部检查，随后还要处理真正的基线冲突与回归。重验本身有合理性，时机可以提前；不能把所有后续耗时都算通知延迟的损失。末尾#143/#144已经得到合并后91/47PASS，负责人又指出私有短hash直达用例和文档回填未完成；首轮46/1失败不是终态。

**改进方向。** 先确认reset期间新输入的产品语义，再收敛长reset turn与评论队列的交互，使高影响基线/验收要求在候选声明前可被消费。无需每条评论强制打断。验收用确切事件与接收记录证明顺序，不以“发送成功”或数据库有评论代替消费证据。

### 3. 首轮错误先被grep丢弃，重跑通过随后被转述成已排除代码问题（I11-07）

PR15 ebf8 在snapshot-02原生记录385（非首轮canonical编号）于08:10:26运行 `Vitest | grep 'Test Files|Tests |FAIL' && ...`，其后build/e2e接tail，没有先保存原stdout/stderr和Vitest退出值。PBB bg025完整日志只有19行：**5 failed /98 passed**，后续e2e58PASS，整个shell exit0。grep匹配FAIL仍返回0，故后续继续；PBB忠实保存了接收到的内容，扩大PBB缓存无法恢复shell输出之前已丢失的堆栈。

worker后来用PBB full tail也取不到首轮细节，明确承认过滤丢失。它在作业结束11秒后读到load33；两次同提交复跑103PASS时load仍约31→27、25→22。证据仅支持同提交随后两次通过。#138披露过滤丢失却归因为负载；Issue8 owner实际读了全文，#140进一步写成“无并发条件”“足以排除代码问题”“不进入证据链”。根ec38 r27消费了这个被加强的结论。首轮错误类型和唯一原因均未被证明。

同类问题也出现在根侧：M3/M1首次整合e2e的 `tail -3` 只留下exit1，后续33/33通过并未查明首错；PR13一轮Vitest明示75 failed/20 passed，`npm test | tail` 后却打印 `VITEST_EXIT=0`。改为Node20后94/95的重启超时虽与并行负载共存，后续95/95也只能证明那次通过，不能单凭它排除代码或时序问题。

**改进方向。** 复用已有外部 `with-service.py --check-only -- <未过滤命令>`，先保存原始结果，再单独读取摘要。该能力在agent-browser技能中确实存在，基础PR2实际使用且中止时保存 `interrupted/check_exit=-15/cleanup passed`；不能说工具缺失。PR15没有读取该入口的证据，适合把现有能力在检查/后台执行决策点直接暴露。Harness不预写生成应用的package/scripts/src，也不解析改写任意shell管道。工具只能报告实际shell结果，不能猜每个子命令状态。

验收解释应保留“首次原因未明，后两次通过”，不机械要求第三次PASS，也不把重跑成功当根因证明。应用Agent若改善自己的runner，属于生成应用实现层，不和Harness补丁混为一谈。详见 `cells/root/failure-evidence.md`。

### 4. 候选冻结与文档回写互相触发，验收重复范围缺少一致判断

PR15先在 `bab2b11` 取得平台58PASS/exit0并声明不再提交，随后仅为packet更新前移到 `6f272e7`；负责人和根要求重锚，worker重新跑整条平台，再为免争论额外跑本地检查，触发上节5FAIL问题。`--match-head-commit` 必须指向实际最终head，但仅改变任务文档不自动推翻应用行为证据。基础PR2和PR13此前已经通过diff接受代码等价，PR15对平台路径与其他检查却采取了不同口径。

另一方面，M1合入后PR11发生routes/architecture真实冲突；末尾PR13合入又使PR15/16需要整合。这些代码与基线变化确实需要重新判断，不能与docs-only一起归为无意义重跑。

PR14另有无需新head就发生的重复验收：06:59重建时候选、base、依赖和构建未变，也没有新失败，却再次执行76 Vitest和34 e2e。其thinking将重新接手本身理解为应当再做动作。这轮78.745秒的复跑与随后约12分钟写入失败排查应分别计算，不能全归因于检查运行时间。接续输入应保留已满足的完成条件；收到状态通知本身不构成重验理由。

**改进方向。** 保留现有SHA门禁；把候选、检查配方、运行条件、原始结果和后续diff关联到同一交接。文档回写尽量先完成，已启动的新job及时在同一thread说明。按变更是否影响结论决定检查范围，避免为了把PASS数字写进同一提交而不断制造新head。无需新增通用hash/缓存框架。

## 有效的纠偏机制

这些成功路径应保留，不能把所有咨询、复核和返工都视为成本问题。

- 基础advisor让共享commit、fork指针、三方merge、viewerPermission、精确文案和Checks键进入权威契约；基础PR的schema/seed/errors六项增量有根裁决并写回文档。
- M1实施者曾为防邮箱枚举而让错误验证码提前返回，违反“一次显示全部字段错误”；Issue负责人用已知/未知邮箱的相同输入反例推翻该理由，并修复实现及场景断言，最终合入候选已无该缺陷。
- M3核对原文后纠正了根此前认可的“访客不显示克隆入口”；advisor补上file-content THEN与blob/tree边界，根进一步处理带slash分支编码和登录态Access denied/访客Not found的区别。根还依据PR2已提供登录API的事实，撤销了M3必须等M1的错误依赖。
- M2从真实请求挂起追到 `requireAuth` 工厂被直接当middleware使用，同时修复测试夹具的 `.body/.data` 和缺少patch/delete方法；这些中间失败随后被最终95/51替代。它们是正常实现反馈，不应归入reset或数据库故障。
- M4 advisor用全数字短hash和fork可达性反例改变revision解析，区分只读compare与创建PR的权限流程，补Branch控件。
- M5 implementer依据原文纠正 `triage+`，改为 `{triage, maintain, admin}`；advisor区分可被指派者与操作者，根把修订传给M6。这是实际阻止Write越权的共享契约修正。
- M5 explorer发现初始全绿未覆盖的立即刷新丢q、默认列表Open+Closed、数字q查编号；实施者消费结果并修复。收益来自独立反例，而非重复背书测试名。

## 其他观察与排除项

1. 根长期写“34条原子需求”，YAML实际47。模块分工范围覆盖47个ID，错误计数不证明漏做13条。最终仍需按ID和可观察场景核对；当前未交付完整应用，不能下最终遗漏结论。
2. vision实际读取27张图，但最终回答stopReason=length，尾部跨图总结截断。根消费了逐图观察和重复图结论；图片读取完整不等于最终文本完整，更不等于应用视觉已验收。
3. Node20/24及浏览器镜像版本不一致曾造成真实安装/启动失败，后来用APP_NODE/BROWSER_EXECUTABLE_PATH修复。基础与根已读过运行约束，不能仅归因于没文档。主观“等了数分钟”多次与timestamp不符，不采用模型自报耗时估损。
4. M3 core文件曾进入历史并被清理、重写和强推。产生者/信号缺证，不把“被杀进程生成core”当根因，也不推断敏感信息泄露。改进落在应用Agent提交产物边界，不能据此让Harness预改应用文件或将任意core都自动判交付失败。
5. M2治理seed已核实不写commit/tree/branch，排除了“它另建内容导致与M3顺序冲突”的假设，不推荐为该假设新跑实验。
6. M3负责人曾把timeline事件#89当成comment ID，`comment view 89`为空便升级为评论隐藏/删除；实际目标是一直可见的comment #32，后来自行纠正。此事不构成平台丢信证据。CLI语法试错、事件ID混用和shell反引号展开均有原生记录，优先沿现有帮助与目标评论入口纠正，不据此新增命令拦截层。
7. SQLite锁与旧结果写权限已有iteration10紧急修复归属，本报告保留恢复背景，不重复立项。819个reset-notice deferred是旧版未启动turn，不能算819次模型调用。OTLP出现BrokenPipe和秒级persist；HTTP200记录不等于客户端收到响应，尚无因果证据把它等同Braid锁根因。

## 成本与计数

以下只统计首轮逻辑截点前、由native `responseId` 与timing记录交叉核对的 **3,507 个唯一响应的已记录usage**，不包含本次审计消耗，也不把重复transcript重复计费。各源usage无冲突；11个request_start尚无message_end不能直接判为失败。

| 项目 | 数量 |
| --- | ---: |
| input | 9,636,131 |
| cache read | 354,290,368 |
| cache write | 211,965 |
| output | 2,076,138 |
| reasoning（已包含在output中） | 1,092,795 |
| total tokens | 366,214,602 |

完整字段复核另发现4条明确的原生error记录：2条 `Provider finish_reason: network_error`、2条 `terminated`，均已包含在3507个响应ID中。后两条已留下部分thinking/tool参数，usage却为0；因此表格不是完整实际计费证明，不能把零值解释为没有消耗，也不能把所有HTTP200视为模型成功。固定末尾增量另有1条 `terminated`，不加入首轮成本表。具体记录见 `cells/root/error-field-receipt.json`。

累计模型请求时长32,884.97秒，并行时间并集10,831.806秒；二者不等于全部工具耗时或可节省时间。不能把3.66亿总量说成3.66亿新输入，更不能据零值cost字段宣称免费。没有本次价格和实际账单，不推算金额。细分表和算法见 `usage.json`、`cost-summary.json`、`cost.py`。

PR11记录的total约1.168亿、PR15约6,773万，含大量cache read。高用量与长反复验收相符，但需逐次判别必要实现、实际基线变化和无新信息轮询；本审查没有把所有模型用量归为浪费。Kimi内部advisor属于同一Braid session，不能按原生子会话数量误判自费模型预算规则。

## 需求分工核对

按YAML逐ID核对，47项均有模块归属。这里证明的是拆分范围，尚不是47项验收通过。

| 归属 | 原子ID | 数量 |
| --- | --- | ---: |
| Issue3 / M1 | 1-1-1、1-1-2、1-1-3、1-2、1-3 | 5 |
| Issue4 / M2 | 2-1-1、2-1-2、2-2-1、2-2-2、2-2-3、2-2-4、2-3 | 7 |
| Issue5 / M3 | 3-1、3-2-1、3-2-2、3-2-3、3-3、3-4 | 6 |
| Issue6 / M4a | 4-1、4-2-1、4-2-2 | 3 |
| Issue7 / M4b | 4-2-3、4-3-1、4-3-2、4-3-3、4-4 | 5 |
| Issue8 / M5 | 5-1-1、5-1-2、5-2-1、5-2-2、5-2-3、5-3-1、5-3-2、5-3-3、5-4 | 9 |
| Issue9 / M6a | 6-1、6-2-1、6-2-2、6-2-3、6-2-4、6-3-1、6-3-2 | 7 |
| Issue10 / M6b | 6-3-3、6-3-4、6-4、6-5、6-6 | 5 |

每个ID均省略共同前缀 `REQ-`。全模块的只读权限、可观察名称、seed关系和跨模块前提仍需要在最终应用候选上核对；不能由分工表替代结果证据。

## 截点上的模块结果

| 模块 | 可确认的结果 | 仍需保留的边界 |
| --- | --- | --- |
| 基础 PR2 | `abb6f6b` 经文档等价核对，合入 `c338578`；38 Vitest、5 e2e及平台路径 | 初始Node/浏览器错误已修复；旧session权限和reset背景不等于现版本未修复 |
| M1 PR12 | `af2d06d → a619edd`；50 Vitest、17 e2e及平台路径 | 独立候选d262e52的49/16仅旁证，不拼接计数 |
| M3 PR11 | `15c79a4 → 53532a0`；最终76 Vitest、33 e2e及平台路径 | 历史core清理、旧head结果不能当最终候选证据 |
| Access denied PR14 | `9bedf84 → d70e6ac`；登录态UI与访客UI分开、API仍404 | 该契约影响后合入分支，不能只看单模块原PASS |
| M2 PR13 | `d62907d → e9390cc`；末尾根95/51及明确退出0 | 根第四轮不是可确认的干净安装环境；owner证据另记 |
| M5 PR15 | `6f272e7` 平台58PASS、同head本地103PASS×2 | 首轮5失败原因未明；与新develop四文件冲突；Triage/Maintain小PR仍准备中 |
| M4a PR16 | `5228a3e` 合并f6e326c后91/47PASS；`9012550`补两条e2e断言 | 最新head尚无完整终态；两个文档回填缺口、与e9390cc两文件冲突；未合并 |
| M4b/M6a/M6b | 分工与依赖已建立 | 截点尚未完成，不能给最终功能/分数判断 |

M4a首轮 `Not found` 失败后来证实为合并后陈旧dist，重建后通过；这类有实际对照的原因与M5缺首轮堆栈的负载猜测应区别。`f6e326c` 是根的M5权限契约文档提交，不是PR15实现已合入。

## 覆盖及证据入口

首轮manifest有1,159份文件；121个native来源按相同记录归并为111个canonical单元、9,035条记录、27,369,023个索引字符。索引字符包含多种重复转录，不能作为实际唯一阅读量。16份Issue/PR板面、99份去重turn输入（对应1,021个源文件）、运行输入/版本/生命周期日志另行核对。结构计数和usage采用全量程序核对，异常堆栈逐段读取；这不冒充逐字阅读每个遥测事件。

首轮canonical分组如下；同一响应或实质字段的精确重复只在首次完整阅读处消费，后续保留来源引用。

| 范围 | 单元 | 记录 |
| --- | ---: | ---: |
| 根统筹 | 25 | 1,584 |
| 基础PR2 | 6 | 748 |
| M1/M2/PR14 | 25 | 2,167 |
| M3 | 28 | 2,184 |
| M4/M5 | 27 | 2,352 |
| 合计 | 111 | 9,035 |

111个单元均已完成可读实质字段审阅；字段包括正文、thinking、工具参数/回包、details和custom事件。末尾12文件新增824条记录亦完成相同范围。早期把记录顺序或投影统计当成全文的回执已撤回并补齐，最终以 `coverage.json` 及其指向的实际阅读回执为准。审计显示截断必须补读，原生运行自己grep/tail丢失的内容只能列缺证；二者分开。图片记录的路径与原生读取动作已经审查，本轮未逐像素重新评价所有截图；两段HTTP错误页内woff2字体base64保留原文但不解码。这是过程证据审查的边界，不能用“全量native文本”宣称视觉验收。

主要证据：

- `snapshot-01/manifest.json`、`snapshot-02/manifest.json`：采集身份、哈希、长度和窗口。
- `coverage.json`：唯一覆盖账本；`views/`保留canonical文本视图，原始JSONL在snapshot目录。
- `cells/root/background-reset.md`：PR13四次启动、reset和候选身份；`runtime-evidence/`保留部署PBB及固定5c957436源码。
- `cells/m3/pr14-lifecycle.md`、`cells/m3/pr11-lifecycle.md`：后台完成后的原生续接、Braid turn终态及两种恢复写入路径。
- `cells/root/failure-evidence.md`、`pbb-evidence/`：PR15过滤前后证据边界、bg025的实际日志与退出状态。
- `cells/foundation/primary-notes.md`：主审完整补读记录、实际工具采用及反证。
- `cells/m1-m2/`、`cells/root-full/`、`cells/m3/`、`cells/m3-rest/`、`cells/m4-m5/`：分工审查与逐源阅读回执；子报告的历史阶段判断由本文固定末尾增量校正。
- `increment-root.json`、`increment-comments.json`、`increment-index.json`：末尾根86条记录、评论134–149和变化范围。
- `source.git.bundle`、`source.git`：约08:09冻结的应用Git对象，只用于当时可用提交的只读核实。末尾e9390cc来自native合并回包与fetch证据，不假装已在此bundle中。

下一轮若要落地，优先把I11-05的finite work寿命与I11-03的reset输入语义放在同一生命周期设计中复核；I11-07独立收敛现有外部检查入口和证据解释。本文只提出范围与判别依据，未获得源码实施或新增实验授权。
