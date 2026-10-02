# I11 GitHub：从原始需求到最终用户旅程的断点

2026-09-30；本轮仅分析最终重放 [e68661975b53](https://arc-bench.com/runs/e68661975b53)。源生成是 `pi-braid-i11--hackathon--github-0d0cb6e9982fc1`，不是 Pi Minimal。用户所述历次最好14分未在本轮重新核验，也不参与本轮归因。

**找到一个覆盖面明显大于单个功能遗漏的入口缺口：需求明确要求首页唯一的 Sign in link，最终页面却同时给出两个；自有验收直接打开登录页，绕过这一跳。** 这支持优先调查“前序入口阻断后续旅程”的方向，但还不能确定它造成了哪些官方失败。另确认同页 Checks→合并资格未同步、菜单仍进占位页、部分规定初始状态未建立等不同机制；不能用一个协作问题统一解释它们。

应用确实使用React/Vite、React Router、Radix、UnoCSS及Express/SQLite，并有官网构建与监听成功证据。问题并非仅安装依赖而未使用；关键差距出现在组件组合、状态更新与业务对象/初态契约。技术栈详见[框架与组件核对](framework.md)。

## 对象与证据边界

最终应用184个文件与冻结清单逐一一致，官网汇总4/100、1/47；私有逐例结果不可见。身份、原始日志和下载清单复用[已核报告](../../pi-minimal/github-score-analysis/i11-e68661975b53.md)。下文 **F** 是 `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`，**Q** 是F内`requirements/requirements.yaml`；应用代码行号均相对F。

本轮只读原始需求、最终代码、现有自验源码/日志及定向native记录；数据库仅在临时副本上只读查询。没有启动应用、安装/构建、运行任何测试、模型、评测或部署，没有修改应用或variant，没有读取私有评测器或扩查Sheet。PR23终态native已取回；新增授权后的五类因果追溯与末轮收口见[causal-chains.md](causal-chains.md)，不以最终packet代替原生决策。

2026-09-30证据状态更正：PR23终态DB、native JSONL、context及delivery已从retained workspace取回至[新证据目录](../../../runs/analysis/braid-context-methodology/github-final-20260930/)。初次状态更正读取[receipt](../../../runs/analysis/braid-context-methodology/github-final-20260930/receipt.json)与[delivery回执](../../../runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/continuation-1790733424384681225-delivery.json)：receipt记录2324个文件、`all_manifest_hashes_match=true`；delivery为`442dc1cf776f144688d8ad667a76dd026f553e27`。此前是final发布目录与retained workspace位置不同造成的取证入口缺口，**不是记录丢失**。随后机制会话完成lineage，本任务依新增授权定向回读原生过程；新增结论归[因果链报告](causal-chains.md)，下文保留静态产物发现。

## 先从需求列前提，再看能力是否串起来

ROOT Q:5–22规定既有对象/权限必须预置、账户使用隔离浏览器session、seed不全不能关闭需求、写操作服务端权限校验及原子持久化。FOLDER还提供ATOMIC正文以外的跨场景约束。

| 关键旅程 | 原需求中的前序节点 | 最终产物的核对结果 |
|---|---|---|
| 首页→登录→所有认证动作 | Q:2837–2839明确唯一Sign in link；字段Username or email/Password、Sign in button；登录后显示用户名。REQ4/5父层也规定控件唯一及首页登录。 | 登录表单、session API、cookie、SQLite都接上；匿名首页shell/body重复入口违反前提。不能由后端登录成功证明首页路径合格。 |
| 登录→个人/组织列表→仓库 | Q:485–500要求Your organizations及Repositories/People/Teams；Q:1130–1144允许搜索、个人/组织列表、直接链接进入仓库。 | 组织链可静态贯通；Your repositories却停在基础占位。实际owner列表存在，可经搜索→repo→owner进入，故不是仓库全不可达。 |
| public仓库→代码/历史/搜索→文件 | Q:1596–1618允许访客；Q:1754要求Search→Code→filename，打开并刷新后仍有exact filename link及指定文本。 | API与分支树持久读取存在；文件页末级filename却渲染span，丢失明确要求的link。 |
| 组织/团队→grant→私库可见性 | Q:699–718规定team名组织内唯一、直接成员权限；Q:1048–1124要求选择当前组织team后授权。 | 列表按组织筛选，POST却按全局team name解析；同名team会产生合法输入拒绝，见cell。 |
| Issue/PR→修改/评论/审阅/合并 | Q:2154–2165及2841–2846规定指定初态、隔离对象和重复/并行运行；PR当前compare commit绑定Checks/reviews/merge。 | 主要后端操作有真实实现；初始化覆盖和跨动作状态同步存在缺口，不能仅由按钮/函数存在推为整条旅程可用。 |

三个cell保留各自全层级要求及更细的入口→API→权限→存储核对：[身份/组织](cells/identity-org.md)、[仓库/内容](cells/repo-content.md)、[Issue/PR](cells/issues-pulls.md)。

## 优先发现一：唯一登录入口被页面组合打破，自验从入口之后开始

**静态证据强、潜在影响面最高；实际官方阻断待证。** 前提为新匿名浏览器、首页、AuthProvider加载完成且user=null。`App.tsx:8–12`总是把首页放在AppShell中；`AppShell.tsx:114–119`渲染Sign in/Sign up links，`HomePage.tsx:21–27`再次渲染同名links，两处Sign in都指向/login且无隐藏条件。Q:2837–2839的“unique Sign in link on the home page”因此不能满足。

入口→动作→结果链是：首页→按需求唯一Sign in进入认证→实际有两个同角色同名候选→如果消费者以全页唯一role/name定位，尚未建立session就会遇到歧义，后续组织、仓库写入、Issue修改和PR审阅都可能无法开始。**条件句不等于官方实现事实**：人类可点其中任一link，知道/login地址也能绕过；没有逐例trace就不能声称官方用了该定位、跳过了后续测试或96例皆由此失败。原始100个scenario的GIVEN起句都从首页开始，但其中有访客只读路径，不能把“100个首页起点”当“100个都需要登录”。

形成过程有独立于评分的当时证据：

- 根native `R0 L12 / 04:25:23 / 4d03fd07` 使用`if node['type']=='ATOMIC'`生成`/tmp/reqs_flat.md`，输出description/scenarios却不输出FOLDER description/dependencies；L11的树只列名称。完整源路径见[定向原文](evidence/entry-native-excerpts.txt)。这证明该次摘要丢失继承约束，不证明全体成员从未在其它位置读过父层。
- foundation native `01a0eb6f…jsonl L46 / 04:33:32`已注意REQ-1父层的首页入口，却决定首页放Sign in/Sign up；`L121 / 04:36:48`实际写shell同名入口，`L124 / 04:36:54`写Home同名入口。最终代码仍保留组合。
- 同session `L146 / 04:37:37`写`registerAccount`直接goto('/register')、`signIn`直接goto('/login')。最终`e2e/helpers.ts:42,57`继续如此；session验收还有Sign in `.first()`存在性断言。因此已有通过记录无法证实首页唯一入口。

这里的新解释是**需求投影漏掉继承约束，加上验收从功能内部起步，留下组合后才出现的前置断点**；它不需要假定通知丢失或某项功能无人承接。后续[因果链](causal-chains.md)进一步确认晚期M6实际读到了父层，以及PR23沿用已有mapping的末轮保留机制。

## 优先发现二：Checks保存成功没有更新同页合并资格

**静态跨组件状态缺口确定；浏览器操作未重现；评分影响未知。** 前提是Open PR、操作者有Maintain/Admin、保护要求test、其它合并条件满足，仅test=pending。用户在Checks选择success并Save，期望新状态影响同页合并区。

`PullChecks.tsx:40–49`保存后返回单个check；`pulls/api.ts:350–353`及后端checks PUT也只返回check。`PullDetailPage.tsx:497`只覆盖`detail.checks`，没有重取/替换`detail.merge`；页面取detail的effect `:278–294`不依赖Checks或tab变化。`MergeArea :199–214`仍读旧gate，而母页`:650–652`仍传旧`detail.merge`。因此仅pending阻塞的PR变success后，前端仍显示旧禁用状态，刷新重新GET detail才按后端`service.js:737–778`重算。

反方向success→failure可能留下旧enabled按钮，**但不能据此宣称违规合并成功**：POST merge在服务端重算并拒绝无效gate。是页面观察状态与动作可用性脱节，不是服务端保护形同虚设。

现有判据说明为何局部通过不能排除它：`e2e/pulls.spec.ts:129–150`保存check后只看check并reload，`reviews.spec.ts:244–261`另行直达预置eligible PR。二者没有覆盖“在当前页改变Checks→立即使用合并区”。没有证据说某个失败断言曾被刻意删改；也不使用本轮尚未补读的PR23轨迹推测意图。细节及其它PR状态断点见[Issue/PR cell](cells/issues-pulls.md)。

## 优先发现三：已有数据不等于规定的场景初态已经供应

**数据形状缺口确定，跨场景污染/官网影响待证。** 用户提出的“缺状态节点”在此有具体实例，而不仅是功能遗漏：

- team cycle前提要求同一个team已有parent且有descendant（Q:812–815）。`seed/governance.js:18–22,58–73`仅两层树：platform有child却无parent；frontend-child有parent却无child。算法能拒绝cycle，界面也能改树，但指定初态没有预置。现有`e2e/orgs.spec.ts:199–207`验证的是原parent为空的较弱场景。
- Issue父层Q:2154–2156要求编辑、无效编辑、评论、校验、指派、标签、里程碑、关闭使用隔离issue。`seed/issues.js`只有3条固定issue，`docs/seed-data.md:105`把#3同时用作无效标题与metadata样本。PR父层Q:2841–2846明确独立provision/restore，包括重复/并行；seed为固定PR/分支组，部分merge PR共享main，插入缺省值不能恢复已改变的状态。详见Issue/PR cell的具体配对。

这些事实支持“需要额外造状态、或先前动作可能改变下一动作前提”的候选。不能据静态seed直接证明官方发生污染：官方可能隔离浏览器之外还隔离应用/DB、选择不同对象、或采用其它预置方法；当前无其执行明细。也不建议把私有reset API当成需求新增功能——ROOT明确它们不是参赛者必须暴露的额外私有接口。

这里还有明确的当时解释，不能归成单纯没看到原文。M6b `N6 L68 / a3ff1bd7 / 16:10:55`读到“每scenario独立provision/restore”，承认insert-if-absent不能恢复已合并PR，随后用“e2e每run新DB、run内merge一次、分别使用成功/拒绝PR”解释满足隔离。L71又按自验spec顺序考虑Draft已被前一spec转Open及PR复用。主线已回读原文；精确文件见[Issue/PR cell](cells/issues-pulls.md)。这是**将自己验收编排的前提用于论证应用场景供给**的直接样本；该前提是否也适用于官方仍未知。同时它后来确实补了独立eligible/blocked PR，不能把整段过程说成没有重视seed。

另一个方向也存在：默认每次服务启动seed会把已删除的预置bob组织/团队membership重新insert，甚至恢复已清空的seed parent；这是同DB重启后的持久化缺陷，**不是普通浏览器刷新即复活**。其过程把“双跑幂等”当作业务共存依据，却未覆盖用户删除；精确native与反证见[身份/组织cell](cells/identity-org.md)。官网是否重启过同DB未知，故不提升为主评分解释。

## 优先发现四：已有列表与文件功能，入口/终点仍不满足原旅程

**静态可定位，影响面低于登录入口。** `AccountMenu.tsx:56`的Your repositories→`/settings/repositories`→`routes.tsx:68`→`SettingsLayout.tsx:33–37`只显示“provided by a later module”。自然菜单不能建立个人仓库列表上下文。foundation native `L118 / 04:36:44`当时把该路由视为M2/M3后续接管的占位，最终没有完成这一跳的迁移。

反证必须保留：`/:owner`真实挂载OwnerRepositoriesPage，RepoHeader有owner link，全局搜索→仓库→owner列表仍可达。REQ-3要求个人列表但未指定Your repositories为唯一入口，所以这是实在的用户导航死端，不能推出所有仓库/后续页面不可达。

代码搜索还有一个确定的终点契约缺口：Q:1754要求打开匹配文件并刷新后仍有exact filename link；`RepositoryContentsPage.tsx:96–97`把最后一级文件名渲染span，文件内容通过API正常加载也不能补足该link。自验只在搜索结果页验证filename link，跳入文件页后检查URL/content substring。功能内部有结果不等于完成了需求指定的所有观察点。详见[仓库/内容cell](cells/repo-content.md)。

## 其它已找到的局部断点

不作为解释全部失分的主论据，但保留用于区分机制：当前组织team候选提交后被全局name查询误解析；分支名两端共同采用Git黑名单而非REQ-4-3父层ASCII白名单；Draft PR后端可close但前端只给Open显示Close；PR milestone仍缺失（沿用已有跨对象承接证据）。其中Draft原要求已在N6:15可见，N6:71却设计为“Close … when Open”，说明是可定位的状态范围缩窄；不是API不会做。这些分别属于对象作用域、共享规则误解、状态条件UI遗漏与范围承接，没有理由全部归为一个问题。各cell给出具体行号、条件和反证。

## 下载DB提供的旁证与局限

只读查询官网下载工作区的DB/WAL临时副本，得到7个seed账户、0条sessions，8仓库创建时间均为03:10:37，Issue/PR与seed数量和状态相容；没有看到新增账户或新的业务对象。查询与不含密码/会话标识的结果保存在[DB观察](evidence/workspace-db-observation.json)。它与早期入口未推进的解释相容，**不证明从未登录/从未执行**：退出会清session；缺少测试生命周期与最终快照时点保证；只读操作也可能正常发生。不可把这个DB形状当作私有评测trace。

## 可交回的判断与最小补证

本轮首先应保留“唯一入口缺口”作为高覆盖面候选，再验证状态与场景前提；不应先扩大SVC/角色/协作改造，也不应以框架品牌评判实现。根的ATOMIC摘要、自验helper直达页面、局部状态保存后reload等都有可定位的实际动作，可解释为何局部功能存在且自验通过仍遗漏用户旅程。但目前不能隔离每种机制对最终得分的贡献。

若下一轮授权实际运行，最小有价值范围是冻结应用的隔离本地副本、全新DB及独立浏览器上下文：

1. 首页等待session加载，记录Sign in的DOM/AX数量，再分别按唯一名称与指定其中一个入口进入登录。这能区分入口歧义与登录服务故障；不复刻官方评分。
2. 使用只缺test success的Open PR，保存Checks后不reload即观察合并区，再reload对照；记录请求响应与当前commit身份，确认状态快照候选。
3. 只读呈现规定team树/Issue/PR初态；若要证明重复/并行污染，先明确使用的对象和场景隔离边界，不用任意新造数据代替原GIVEN。

运行会写隔离DB并创建本地服务进程，需父会话另定范围；本轮没有执行或申请扩大授权。官方逐例日志仍不可见；PR23 native已取回，后续定向过程判断已记入[因果链报告](causal-chains.md)。报告及cell是本轮交付，后续实现/验证方向由父会话统一交用户决定。
