# I11 GitHub 五类需求断点的形成与保留链

2026-09-30；已完成，有界只读调查。对象仅最终重放 **e68661975b53**，源生成 `20260929-042409-1202e245`，最终 main `442dc1cf776f144688d8ad667a76dd026f553e27`。不混入 Pi Minimal 或 Sheet。

**五类断点已经能追到不同的具体形成机制，不能统一归为“没看需求”“协作过多”或框架使用错误。** 首页最初漏掉跨模块父层约束，组合重复已被浏览器返回却被允许的验证入口绕过；Checks 是新增派生状态后没补旧 mutation 的刷新合同；个人仓库菜单是被发现的残余连接没有责任交回；文件搜索是把依赖模块的另一种验收属性误当本需求已覆盖；规定初态则多次在原文已可见时被弱化或交给假定的外部 fixture。最终整合真实验证了候选身份、构建和既有检查，继承了这些检查未覆盖的路径与前提。

这解释了**断点怎样进入并保留在应用**，不是对官网 4/100 的完整归因。官方逐例 selector、失败记录、场景隔离和运行轨迹仍不可见，不能换算失分、声称测试被跳过或质疑官方评分。

## 证据范围与结论强度

最终产物 `F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`；原始需求 `Q` = F 的 `requirements/requirements.yaml`。应用身份及 184/184 文件匹配复用[产物报告](report.md)。终态过程 `E` = `runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`，包括真实 `braid-state/braid.sqlite3`、native、初始 context、delivery。**PR23 原生终态已取回且本轮已定向回读，不再是记录缺口。** 先前缺失表述来自发布目录/retained workspace位置不同，不能继续作为解释。

本轮回读 provider native 的真实 user 输入、tool 返回、选择与写入回执，再连接 Braid 评论/合并事实；原生消息 ID和物理行见各 cell 的原始摘录，不能只按同名 JSONL判断身份。没有独立的每次 provider HTTP 请求快照；这里的“可见”指实际 native 输入/工具返回，不代表注意力或隐藏推理。未把当前已更新 packet 反充为早期看到的内容。原始 lineage/投影语义复用[完整方法报告](../braid-context-methodology/report.md)及[runtime semantics](../braid-context-methodology/runtime-semantics.md)，不重复全历史审计。

| 断点及影响面 | 确证与限度 | 已定位的可改变原因 |
| --- | --- | --- |
| 首页唯一 Sign in；可能影响多个登录前置旅程 | 终态静态违反 REQ-6 父层；PR2既有浏览器 snapshot 确实有两个 link。最终严格 locator/评分影响未证 | 最初 ATOMIC 投影漏父层；共享壳与首页重复被认可；直达地址、ref及`.first()`自验未否定重复，晚期读到父层后未回核共享入口 |
| Checks Save→当前页 merge资格 | 静态新check/旧gate链与实际引入操作确证；无本次运行或历史直接 stale gate 失败。服务端事务重读限损 | M6b扩展detail.merge snapshot时保留M6a check-only回调；未将新消费者加入旧mutation更新义务 |
| 文件搜索→README打开/刷新后filename link | 终态末级span、首次引入与后继误判确证；complete query文本值另有解释边界 | “文件页存在/全文已验”替代“此终点的角色、精确值、刷新状态已验” |
| 规定初态/隔离；跨多个场景 | 团队合取初态缺失、Issue供应收窄确证；PR实际污染取决于未知外部生命周期 | 合取条件减成弱示例；应用供应与本地fresh fixture混同；fresh DB per run/固定顺序替代逐scenario合同 |
| Your repositories菜单→占位 | 死端、已发现后另建列表、未交接残余确证；原需求不规定一定由此菜单进列表 | 相互不一致的模块/路径所有权假设；补了能力，未闭合原导航连接；结构共存复核没有走用户路径 |

表格按潜在影响面与证据强度组织，不是官方失败概率排序。没有运行应用、测试、评测、生成或模型试跑；没有修改实现、variant、工作项或其它既有改动。只新增本目录文档/证据。

## 1. 首页唯一入口：初期漏投影，晚期仍未对账

**要求/路径：** ROOT Q:5–20为名称与状态规则；REQ-1父层给首页账户入口；REQ-6父层 Q:2837–2839要求 signed-in scenarios 从首页 **unique Sign in link** 开始。最终 AppShell 与 HomePage 同时渲染 Sign in，两个均指向 `/login`。入口→登录本身可用，入口的唯一性合同不成立。

| UTC时间、工作项 | 原文身份与动作 | 对断点的因果含义 |
| --- | --- | --- |
| 09-29 04:25:23，Issue1 | `4d03fd07`，root sessions L12：仅 `type==ATOMIC` 输出description/scenarios；ROOT另由head实际读取 | 补读flat后半不等于补读FOLDER。REQ-6父层没有在这份早期投影视图出现；这是可证促成条件，不是永久不可得 |
| 04:33:32–04:36:04，PR2 | `8c325b34` L46读REQ1后选Home Sign in/up；`5cad06b9` L95明确“AppShell already renders both in the header”，仍认为Fine | 不是两个组件互不知情地写出重复；最初验收标准允许重复 |
| 04:36:48–04:37:37，PR2 | `78775a08` L121写shell，`f02e534b` L124写home，`c06e6125` L133组合；`95664629` L146写直达`/login`、`/register` helper与`.first()` | 产物形成与自验入口同时确定；没有证据是先发生严格locator失败再改first掩盖 |
| 04:48:40，PR2 | `815222fd` L317真实snapshot有Sign in e7/e4；后继`d6bdb327`点击特定ref e7成功 | 重复反馈确实被返回，但ref点击不要求名称唯一；既有浏览器证据排除最初只是死源码 |
| 04:50–05:09，PR2→M1/M3 | 评论#6/#16/#17报本地检查/浏览器通过并交接shared shell；未交回重复风险 | 后继继承已验基础；M3 `e1cdbb74` L39还看到`.first()`并判不受影响 |
| 11:09、11:32、16:10，Issue9/PR20/Issue10 | `b4a76626` sessions L17；PR20 `0b8d33f1` L70→`c6aed31b` L72；M6b `7711770e` sessions L66，均真实返回REQ6父层unique要求 | **晚期不能再说父层从未可见。** 没有找到据该新可见约束回核首页组合/helper的纠正链 |
| 09-30 PR23→main | 沿第6节同一整合门；终态 AppShell:114–119 + HomePage:21–27，helpers:57仍直达登录 | 现有检查通过未改变入口合同 |

**机制判断：** 初期漏父层和后期未核共享入口是连续但不同的机制。实际重复被看到、实际父层后来被读到，排除“一直看不到所以没法改”的解释。也不能由“可见”推断负责人充分理解后故意忽略。

**替代解释/边界：** 两个链接功能相同，ref点击可成功，认证和持久化并未因此失效。没有官方locator，不能声称这一条解释了全部登录相关扣分。完整输入/交接/反证见[入口分线](causal-cells/entry-navigation.md)，原始[48条摘录](causal-cells/entry-navigation-native-excerpts.json)及[评论](causal-cells/entry-navigation-comments.json)。

## 2. Checks→merge：新snapshot没有接入旧mutation更新

**要求/路径：** Q:2801–2847的PR/current commit/门控一致性，REQ-6-1 Q:2855的context变化后页面与数据一致，REQ-6-5 Q:3658–3689对Checks的依赖及点击前资格/原因，共同要求当前条件改变后页面保持一致。Admin在受保护Open PR当前compare commit将check pending改success→Save，UI check更新，`detail.merge`保持旧blocked值；反向失败也可显示旧enabled，但后端merge重新读库会拒绝错误合并。

| 时间、工作项 | 可见输入 → 选择/实际动作 → 反馈 |
| --- | --- |
| 09-29 11:09–11:32，Issue9/PR20 | `b4a76626`及`c6aed31b`实际返回REQ6父层；PR20明确用父层纠正Checks导航/唯一性。父层读取有实际作用，不是全部忽略 |
| 11:29:29，Issue9 #235；11:40–11:41，PR20 | #235把Open合并区交M6b；`4e8ff866` L164写PullChecks，`2e5c3271` L172写check-only回调，回执成功。此时尚无Open merge snapshot，局部更新本身还不足以构成本缺陷 |
| 11:44–11:49，PR20 | 自验Save→success/setter→reload持久；11:48 `b41b9ebd`/`9fc908ee`真实修过`/pulls/undefined`信封解包故障。reload已存在且对应持久化原文，早于新snapshot |
| 16:18–16:21，Issue10 #308→PR22 | `5ef8c3ca` L98设计detail.merge；PR22 `8d203222` L47实际读入旧回调；`5e840dd0` L76、`d5cf0bed` L103/`399dc076` L107扩展GET detail gate和事务重读。PUT checks仍只返回CheckState |
| **16:27:48，PR22** | **`24b163a3` L270**完整重写母页，明确保留PullChecks；同一写入保留check-only回调，又接上`MergeArea gate={detail.merge}`；L271成功。**新消费者与旧更新机制组合的引入点** |
| 16:28:07，PR22 | `f467370f` L283因Ready返回类型不合修为refetch detail；reviewer局部替换。Check维持原状，说明刷新按各mutation局部选择，不是全站统一重取 |
| 16:30–17:08，PR22/Issue10 | `ff853afe` L327合并验收从seed approval+success入场；#330→#331/#332核两规则、blocked/eligible及事务。核对者相关工具返回围绕按钮、角色、其它片段，没有读到Check handler497；没有Save→当前gate断言 |
| 09-30 PR23→main | 第6节既有152用例再验；没有新增连续状态过渡。终态静态链不变 |

最终 `PullChecks:40–49 → api.ts:350–353 → PullDetailPage:497`只替换checks；`:651`消费旧merge，`:276–294`取detail的effect没有check/tab依赖。后端 service:863–872在GET detail才重算，:797–809执行merge时再读。Ready/review等其它action或整页刷新可以更新gate，单纯保存check或切tab不会。

**机制判断：** 新派生字段增加后，没有回查哪些既有mutation改变它的输入；按模块独立场景验收没有覆盖新组合。父层/原子一致性要求实际可见，不能把根因写成缺父层；reload为主动遮错也没有证据，时间先后反而排除该强说法。

**缺口：** 无旧gate历史浏览器失败记录，未新运行；因果引入与静态更新链闭合，实际渲染表现和评分关联未证。[完整链与替代解释](causal-cells/checks-merge.md)、[原文/评论](causal-cells/checks-merge-evidence.json)。

## 3. Your repositories：能力补上，原导航残余没有交回

**要求/路径：** REQ-3父层 Q:1130–1144和创建/fork场景要求owner列表及新对象可观察。应用自己提供Account menu→Your repositories→`/settings/repositories`，终点却是SettingsPlaceholder。另有真的`/:owner`列表，经repo header owner、搜索/直接地址可达。原文未指定一定走Your repositories这个菜单，故该死端不能等同REQ3全部能力缺失。

| 时间、工作项 | 可见输入 → 选择/实际动作 → 后继验收 |
| --- | --- |
| 09-29 04:36:44，PR2 | `2f0e745d` L118选择settings路径，认为M2/M3可重指；正式#6却笼统将`/settings/*`移交M1。可调壳与具体业务责任没分清 |
| 05:26–05:28，Issue5/PR11 #20/#21/#23 | 局部方案列6项atomic及路由，没列个人菜单页；真实初始context以本项为主、Parent为指针；但后续`2a2576b5` sessions L22实际读到REQ3父层与owner-list场景 |
| **05:36:12，PR11** | **`882916d9` L111**明确发现菜单“dead-end placeholder”，承认THEN要求owner list；因Issue5没列、M1拥有settings的判断及冲突顾虑，选择另建`/:owner`修自己RepoHeader链接，未重指旧菜单 |
| 05:36–05:39，PR11与PR12并行 | PR11 `80fc68af`/`7ea2740a`写真实owner列表/路由；M1 `6ff847ee` L60、`efdea1c4` L67同时将repositories判out of M1 scope，`3ab909db`/`2ac3277c`保留“later module”占位。不是后期合并误删完成品 |
| 05:37–06:08，PR11 | `f1d1fdfe` L134自验直接goto`/:owner`；#32/#34主动传其他跨模块问题，#59交回owner列表却未交回菜单残余或承接人。不存在“跨任务渠道完全不可用”的证据 |
| 06:12–06:50，#65/#67/#69/#79/#82 | 路由冲突复核要求同时保留M1 settings/repositories和M3`/:owner`；结构共存/76 unit/33 E2E通过，`53532a0`合入。验证结构完整并不验证菜单连到正确终点 |
| PR23→main | AccountMenu:56仍走routes:68 SettingsPlaceholder；真列表挂routes:103。最终检查沿同一替代入口 |

**机制判断：** 已发现的连接问题被一个不冲突的替代入口部分解决，未解决的原入口没有明确退回/接手，双方所有权假设不一致未被升级裁决。根因不是组件库不支持menu，也不是后端列表没写。

**限制：** 冲突顾虑是当时选择理由，不证明重指menu真的不可行；搜索、直接链接和owner header可限损；无官方路径/评分贡献。[完整链、初始context对照与评论](causal-cells/entry-navigation.md)。

## 4. 文件搜索：把已有组件通过扩大为新增终点通过

**要求/路径：** REQ-4/4-2父层要求内容上下文与只读一致；REQ-4-1验完整存储文本/目录入口/父目录返回；REQ-4-2-3 Q:1754额外要求打开README显示query，刷新后仍有exact filename link。最终末级filename是span，搜索结果页filename link存在不能补上终点link。query在整段markdown中，`complete text value`是否要求query本身是独立完整文本观察，保留谨慎解释。

| 时间、工作项 | 输入 → 选择/动作 → 后继消费 |
| --- | --- |
| 09-29 04:25/04:33，Issue1 | root flat `57699230` L19实际已有完整REQ-4-2-3；`7b7e8f87` L31拆M4a为完整全文/filename显示、M4b为结果link，不登记打开后两项。父FOLDER没在flat，但本断点原句已可见，不能仅归压缩丢失 |
| 05:38:39–42，PR11 | `992fcbed` L155初写file页末级span；`4c80f7ed` L157明确“file plain text”。这是首次找到的引入，不是最终集成删link |
| 07:07–07:28，PR16/M4a | 实际读旧页，`204c37df` L162修改并获`a3949bb5`成功回执；`c51dd7ad` L164判断REQ4-1要filename，breadcrumb末级满足。M4a承担的是显示/父目录返回，未明确承接REQ4-2-3终点 |
| 07:51–09:28，#125/#150/#196/#197 | 补README `pre code.toHaveText(整个markdown)`，核完整存储文本、branch/path/parent，合入`4a8f3c9`。真实验证另一属性，不是虚报所有东西都验过 |
| **11:22–11:25，M4b原生advisor** | 原需求实际读取；**`c3e65a02` L36**以“README contains literal search flow”判complete text；**`21775e48` L40**完整引用refresh filename link后以“blob page…exists (M4a)”打勾。独立review也使用了替代判据 |
| 11:44，PR19 | `c9d32ef0` L243自验写结果exact filename links，path=src后开search.ts，URL+substring；未走README打开刷新后的link。结果页scope/filter后来确实被#264→#273/#274修复，是有效纠偏反证 |
| **11:58–11:59，Issue7** | **`f24f8ddf` L45**重新意识到README complete query和自验其实打开src，最后认为M4a已逐字验全文，所以Fine；filename link写“M4a covers”；**`e147aaa3` L49**再次如此归属。这里是已读原文后的明确证据外推 |
| 15:07–15:10，#276/#278/#279/#280 | 按scope/filter、唯一Search、分支/editor补齐门复验，`56f53ae`→`4eb2a27`，Issue7关闭；没有把两项README终点交回M4a |
| PR23→main | 第6节继承既有mapping；终态RepositoryContentsPage:96–97仍span，:137–138仍全文code |

**机制判断：** 依赖组件的新增消费条件没被重新验证，证明“存在/全文包含”被扩大为证明“精确link/文本观察”。不是原句没读到；有advisor也没有消除共享解释偏差。near-match不滚动的已登记风险是旁证，不能替代这条链或被升级成确定官方失败。

**边界：** 文件API、权限、结果链接、scope、filter是真实可用实现；filename link为强静态断点，complete-text为解释和运行待证。详情与49条原文见[文件分线](causal-cells/file-search.md)、[证据](causal-cells/file-search-evidence.json)、[评论](causal-cells/file-search-comments.json)。

## 5. 规定初态：三种收窄，不能笼统称seed全坏

本组完整逐项链、真正read返回、代码回执与正式交接见[seed-state.md](causal-cells/seed-state.md)，原文见[seed/integration native](causal-cells/seed-integration-native.json)、[评论](causal-cells/seed-integration-comments.json)。

| 初态 | 原始要求实际可见 → 解释 → 代码/自验 → review/集成 | 事实与解释边界 |
| --- | --- | --- |
| 团队cycle的同一对象既有parent又有descendant，Q:812–815 | root `904a0f80`04:30:22 L16先给两层示例，允许M2补齐；M2 `589ac1e9`06:07:04 L26返回完整原文，`0c9834b3`06:12:18 L50、`5123de26` L56引用后仍选platform(parent空)→child；#68公开此方案；`4fba7ca3`06:37:45 L60实际seed；`0aba2ab0`07:07:44 L291自验原值 **No parent**；#113/#114报95/51通过、根复跑合`e9390cc`（#154）；最后仍三team | 可证把合取初态弱化为任意cycle例子。拒cycle算法可用；指定初态没有。用户可自行补树，但不是预置已供应；官方是否依赖此初态未知 |
| REQ5父层逐mutation isolated issues，Q:2154–2159 | `7ccb1825`06:53:34 sessions L14完整返回父层；`58a9d136`06:58:32 L7引用后猜evaluator自建pw-*，选择仅3issue；#89/#90正式交接#3复用invalid+metadata；`955c4750`07:04:44 sessions L83实际seed；#115/#116/#117验收；08:20 `2f7b1d6b`/`2b7c1529`识别自验共享污染并改fresh API fixture；PR15 `2eed74e`、PR17 `41bf131`补权限后#187关闭；最终仍3个seed | 可证应用供应被外部fixture假设收窄，且测试隔离与应用供应被混同。不是不会隔离测试。若实际外部每场景自行provision，则评分影响可能消失；无官方证据不能认定实际串扰 |
| REQ6父层逐scenario provision/restore、repeat/parallel，Q:2841–2846 | `a3ff1bd7`16:10:55 sessions L68明确见原文且承认insert-if-absent不恢复；解释fresh DB per本地run、每场景一次/不同PR；`ae7fd895`16:22:39 L146考虑持久化后保留此方式并seed；核对者`e3dffd29`16:54:38 L117、`059dfe36`16:55:18 L140以freshDB+spec排序解释；#332通过，#337交回无遗留；PR23复用同套检查 | 可证解释把scenario恢复单位换成run/顺序；没有已证应用场景生命周期。实际评测是否共享DB、是否受污染未知。不能要求每次服务启动回滚用户数据，原文没有指定这种机制 |

**必要反证：** M6b不是一律用测试setup替代seed。#308/#311发现eligible缺protected main/非作者reviewer/approval/check，root `dd4548e1`16:21:39 L40、`77f888b5`16:23:59 L59回读原文，#313批准新增merge-lab并调整旧计数断言；#317/#322与#332真实闭合。终态eligible初态已存在，不能把早期缺失继续当终态问题。剩余是隔离/恢复合同。

本组不需要假定所有缺口同源：团队是合取遗漏；Issue有明确无依据的外部准备猜测；PR有真实持久化与恢复张力，但通过本地执行条件替代解决。无证据能量化模型“内在根因”；这里只定位可追溯、可改变的决策与验收边界。

## 6. 共同末轮：候选身份被验证，既有判据没有从原文重新推出

PR23是所有五条链共同的终点；以下为本轮主线回读，未用最终packet假造过程。详见[PR23完整lineage](../braid-context-methodology/final-pr23-flow.md)与[根收口](../braid-context-methodology/final-root-flow.md)。

| UTC时间、原生消息/评论 | 实际动作与能证明的范围 |
| --- | --- |
| 09-30 02:02:03，root `37da0043` L26 | 创建PR23，要求全模块最终候选全量E2E、平台启动、unit/typecheck，说明局部PASS不替代整合。原始需求入口保留；并未授权只核编号就算功能覆盖 |
| 02:03:56–59，PR23 `09835fd1` L45→`5aa2c470` L46；`fa9e3624` L48 | 读取原需求head40，ROOT seed等实际返回；取ID清单后明确“acceptance plan and existing specs already establish”mapping，“I don't need to re-derive each mapping” |
| 02:04:53，`45506478` L71 | 一度考虑回读模块requirements核coverage，继而以已确认34叶子引用转去安装/平台事项。后续ID核对更正为47叶子，不等于审读父层/前置/终点 |
| 02:35:19–29，#345/#346 | 最终code head `0c73f4a`：194 unit+typecheck、152 E2E；clean平台路径在`0e57fd0`通过，后续实现增量仅测试超时配置。`f628045`仅附证据/packet。覆盖声明基于47叶子ID引用和已有acceptance-plan；没有为五条断点新增否定判据 |
| 02:35:34–57，root `310c4705` L14；`1f8ec4d5` L18；L19–22 `a8477457/1c7d4663/9801442c/551e1ada` | 核候选亲缘、差异/配置、日志tails与194/152真实通过。确实验证了证据适用的版本，不是根没读日志或未核merge身份；没有重新推导这五条用户旅程 |
| 02:36:05–06，`8586d62f` L23→`8f9e4d6b` L24；#347 | `--match-head-commit f628045…`合入main `442dc1cf…`，后续关闭Issue1。最终冻结184文件相符，排除这五条只是旧工作树未交付的解释 |

**因果裁决：** 末轮的identity/reproducibility门有效，但“沿原需求连续旅程重新评价已有检查是否足够”的门没有在这些断点上发生。编号覆盖和重复运行不证明父层前提、入口、状态过渡、终点角色也被覆盖。也不能反过来写“47中13条全漏”：47是实际全部叶子，34来自层级/旧口径，13较浅叶子仍有spec引用；当前发现不是简单数量缺13。

这是一条**保留链**，不是全部缺陷的首次创造原因。不同局部曾有效修复权限、scope/filter、API信封、eligible初态等，说明不能只用“自测不可信”概括。需要区分真实PASS的证明范围与原合同的剩余要求。

## 可交付判断与未闭合部分

当前证据支持五个方法归属：需求展开保留相关父层；已发现的残余入口明确退回责任；依赖组件新增条件不沿用旧通过结论；新增派生状态回查所有影响它的mutation；验收fixture/隔离单位与需求GIVEN一致。应用中的具体定位均已保存，下一轮可以据此讨论修正，不需要把GitHub题目字段硬编码进Harness。

此前[框架核查](framework.md)确认React/Router、实际Radix/UnoCSS、Express/SQLite都有真实使用和构建证据；本轮找到的是组合、合同和验收路径问题，没有证据指向“依赖只安装未使用”或整体框架配置错误导致这些五条链。Checks局部更新的具体设计有缺口，也不意味着使用React局部state本身错误。

仍不能确定：官方逐例失败/selector、真实场景初始化与隔离、这些断点的评分贡献；Checks保存后页面的直接运行复现；complete-text严格语义的实际观察；所有provider请求隐藏字段及注意力。缺口已划清，本轮不再扩大调查，也不运行应用或新实验。父会话可直接使用本报告与四份分线证据统一汇报。
