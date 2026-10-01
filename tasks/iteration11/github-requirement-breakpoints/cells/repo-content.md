# REQ-3 / REQ-4 仓库与内容旅程断点

2026-09-30，只读有界调查。对象为 I11 final replay `e68661975b53`。`F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`。身份和最终184文件哈希一致沿用 `tasks/pi-minimal/github-score-analysis/i11-e68661975b53.md`；不将其它版本的行为用于解释本版。仅写本文件，没有运行应用、测试、模型或评测，没有读私有评测器或 Sheet。

## 原始需求前提

先读 ROOT:5–22，再读 REQ-3/4 全层级描述、依赖与 scenarios（requirements.yaml:1126–2124）。重复 scenarios 的相同正文只记一次，但保留其原始场景入口；atomic 指定角色/名称与可观测状态优先，不用旧 scenario 的不同操作覆盖它。

- REQ-3 FOLDER:1130–1144：overview、global search、个人/组织 Repositories list、direct link 是入口；public 可访客读；private 组织仅 Owner、直接角色或直接团队成员可读；授权/visibility变化后搜索、列表和直接访问采用同一规则。
- REQ-3-1:1151：顶部唯一 Search searchbox，Enter直接repository结果，exact repo name link；访客不能搜索private。REQ-3-2 FOLDER:1257–1269：new/fork都进入可浏览overview，fork独立且不写源。REQ-3-2-1:1277：登录后New repository link，默认个人Owner，radio Public/Private、README checkbox、Create repository button；原子初始化、重复名/空名拒绝。REQ-3-2-2:1369：有读源/建目标权限，默认个人目标和允许visibility，Fork→Create fork→源关系与历史持久化。REQ-3-2-3:1434：Code button区别于Code link，HTTPS/SSH tabs，clipboard前提，Copied。REQ-3-3:1495：public稳定地址、owner/repo heading。REQ-3-4:1533：Admin Settings→General→Change visibility→Public radio→Confirm visibility，不能强制复输repo name；non-Admin无操作button。
- REQ-4 FOLDER:1596–1618：public visitor可直接读file/history/diff/search/branch；每个内容页面显示repo与branch/revision；写场景独立登录贡献者、有权限、未保护branch；每个control默认全页唯一。REQ-4-1:1626：directory/file exact name links，存储文本完整可见、刷新保持；scenario:1634–1654还有跨branch不存在file的状态。
- REQ-4-2 FOLDER:1661–1670：branch/path历史倒序、比较readable revisions、search只读及repository权限。4-2-1:1678：overview/file各一个Commits link、完整独立message/author、ago。4-2-2:1716：访客直开commit、src/search.ts、Changed files及数字summary。4-2-3:1754：Search→唯一Code results link→exact filename result，匹配README.md包含known query `search flow`完整文本值；**打开文件并刷新后仍有exact filename link**；absent `no-such-token`显示No code results且保留query、重复操作无stale results。
- REQ-4-3 FOLDER:1859–1872：branch为named commit pointer，名字1–255且**仅ASCII letters/digits/-/_/./**，不得结尾 / 或 .，不得 .. 或 //；default变化不改既有branches/commits/PR refs。4-3-1:1880：Branch main button→Find branch textbox→exact branch name option，实时过滤及Escape。4-3-2:1938：Write/Maintain/Admin/OrgOwner才创建，实时valid-unused Create branch: name option，当前head为base，invalid..branch即时Invalid branch，创建后URL保持。4-3-3:2003：Admin Settings→Branches，native Default branch select→Update→Confirm；non-Admin完全不渲染select/update。
- REQ-4-4:2062：Write/Maintain/Admin/Owner，Add file button→Create new file menuitem，File name/File contents/空Commit message→Commit changes；单事务内容、author、parent、head更新；invalid path/empty message/protection拒绝且零改动。

## 候选，按受影响旅程范围排序

### 1. 个人仓库自然入口仍停留基础占位，替代入口可用

**静态确证；对需求的违反强度有边界；评分影响未知。** 登录→Account menu→Your repositories（F/frontend/src/components/AccountMenu.tsx:56）→`/settings/repositories`→routes.tsx:68的SettingsPlaceholder→SettingsLayout.tsx:33–37仅显示“provided by a later module”，没有repo列表，也不调用list API。它影响从首页登录后找个人repo及新建/fork后再经自然菜单重开的旅程。REQ-3 FOLDER:1135–1144和创建/fork THEN:1300、1400要求个人列表和列表持久化，但没有强制指定名为Your repositories的唯一入口，因此不能直接说所有REQ-3或下游功能不可达。

**真实形成证据：** `tasks/iteration11/run-audit/github/snapshot-01/work/native-homes/pi-deepseek-fast-01a0eb6f-2435-7b40-8c0d-ca9ef86d9bfc/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.jsonl` L118，04:36:44，foundation明确考虑Your repositories路由，决定/settings/repositories为M2/M3后续接管占位，并说这些模块可在AccountMenu重指；L124写路由（主线已核对）。本cell直接回读L118。终态占位说明迁移未落到此入口；不推测后继从未读过该决定或故意忽略。

**反证：** overview的RepoHeader.tsx:25–27 owner link→`/:owner`（routes.tsx:103）→OwnerRepositoriesPage.tsx:24–38调用repoApi.listByOwner（api.ts:209–214）→GET `/api/repos?owner=`（repos/router.js:58–61）→service.js listNamespaceRepositories按canViewRepo过滤。全局Search→repo exact name link→overview→owner list可达；direct owner address也可达。因此局部菜单死端和列表能力存在同时成立。最小补证是从登录首页沿菜单实操，再从Search进入同owner作对照；本次授权禁止执行。

### 2. code search成功后文件页丢失原需求指定的filename link / exact query值

**静态确证，运行待证，评分影响未知。** 前提public `alice-dev/acme-docs`、main、query `search flow`。AppShell.tsx:68–110将repo scope和q带到SearchPage；SearchPage.tsx:51–76只一个Code结果link，CodeResults:282–286的result link名为README.md。repoApi.searchCode→GET `/api/repos/:owner/:name/search/code`（content/router.js:73–86）有loadRepo/requireViewable。mutations.js:267–294从default tree生成README.md/blob/main/README.md地址；seed/repos.js:54供匹配内容。

点击结果→RepositoryContentsPage，branch/path来自路由，api.contents→repos/router.js:68–75→repoContents读取branch head的immutable tree；不是API缺失。**终点**RepositoryContentsPage.tsx:96–97把末级filename渲染普通span，不是link；该file状态其余links仅repo、ancestor directories、Code/Issues/Pull requests/Settings、Commits及授权Edit，没有README.md link。刷新重建相同树，故需求:1754指定的“refreshing preserves … a link named exactly after the file”不满足。影响所有匹配文件跳转后此观察，不能推广为文件加载失败。

同一终点`<code>{state.contents.content}</code>`（137–138）原样显示seed README `# acme-docs\n\nThis repository documents the **search flow** of the platform.\n`（seed/repos.js:54），没有独立完整文本值`search flow`。若按ROOT:7–8及1754的complete text value读，substring存在不足以满足exact text观察；该处是文本契约差距，不是无法看到query字样。实际DOM exact locator及评分关联仍待运行。

**过程/反证：** F/docs/task-packets/m4b-issue-7.md:38–39 D3只明确结果页filename链接、Search唯一和scope；F/e2e/code-search.spec.ts:40–57只在结果页断言exact filename link，打开src/search.ts后仅断言URL及content substring，没有打开README后刷新再断言filename link或exact `search flow`。现有判据完全可以在本缺口下仍PASS；不否定其scope/empty-state覆盖。该packet:27–30、70以后还有真实修正结果页重搜scope/filter的记录，终态AppShell对应修复已经存在，不能把旧scope bug重复列为最终问题。未取得M4b晚期原生设计轨迹，本cell只用交付packet和检查源码说明覆盖边界，不把模型意图补造成确证。

### 3. branch命名把需求白名单替换成Git禁字符黑名单，两端一致但都偏离

**静态确证；server新增reference的后果由接线推得，实际操作待证；评分影响未知。** 前提bob-reviewer或Alice有Write以上，main可读，候选名未用。REQ-4-3 FOLDER:1865–1867限定字符；BranchSelect.tsx:93–96采用branchName.ts:49–58的Git风格黑名单。输入`a$branch`或中文名时不触发任何拒绝分支，出现Create branch option（:180–193）；点击调用api.createBranch（:116）→POST content/router.js:46–59，requireAuth/requireRepoRole(write)正确→mutations.js:39–64调用backend validateBranchName后插入branches并保存created_by、当前base head。

backend http/validate.js:143–153与client同逻辑：没有ASCII whitelist，因此`a$branch`、分号、中文都会通过；DB branches schema没有替代name字符约束。反方向，`.hidden`、`a.lock`没有违反原文列出的规则，却被前后端拒绝（backend:151–152，client:56–57）。这里不会令明确例子`invalid..branch`错误通过，它仍按:149拒绝；合法常见`feature/api-v2`仍可创建，权限和事务也已接上。

**形成/判据来源：** backend validate注释:139–141明确写“git-invalid forms”；client branchName.ts:17–46 fixture把`.hidden`和`lock.lock`判false，又没列ASCII外字符，所谓parity只能证明镜像一致。F/docs/task-packets/m4b-issue-7.md:41–42 D5宣称前后端同规则，:63记录parity检查，但未记录为何用Git规则替代FOLDER白名单。没有晚期native便不推测是否漏读FOLDER、advisor接受或root有明确裁决。最小下一轮判别只需合法`.hidden`与非法`a$branch`通过selector/API/刷新两个方向，不必扩大测试系统。

## 未提升为高影响确证的观察

- code search范围固定default head（mutations.js:240以后，packet D1:36 / architecture.md:420），从feature-search页面Search仍不带branch。REQ-4-2-3:1754“currently visible branches”可被读为不限default，但scenarios:1765–1766明确default两个文件；本版default scope有显式共享决定。记为范围解释待核，不能据此直接断言此atomic失败。
- commit/history页面缺单独branch显示、diff页Commits返回default而非原branch；URL/revision标签提供部分上下文。REQ-4 FOLDER:1606要求每页branch/revision，CommitsPage仅path/count、commit hashes和父revision，满足度需要明确“显示”口径；优先级低于上面exact role/name断点。
- 创建、fork独立性、visibility与默认branch API目前有明确权限与transaction，没有发现使所有旅程必断的持久化空壳。fork共享immutable commit、分支pointer独立；history.resolveRev按branch reachability而非commit.repo_id识别fork历史，是对“fork无历史”竞争解释的反证。

## 覆盖与剩余缺证

已沿REQ-3/4入口、routes、AppShell/Search、repo页组合、BranchSelect/editor/settings、repo API、repos/content router/service/mutations/history、shared权限和seed核对；关键引用加行号回读，首轮长合并输出截断部分用后续相关范围补读，不宣称所有文件全量审计。README seed、branch creator/default operator持久化及权限可静态追踪；没有打开下载DB，没有执行应用或测试，实际运行DOM、clipboard、并发、存储失败原子性不在本cell已证范围。没有独立官网逐例失败；不能以三个候选解释96项失败或估算提分。M4b晚期native尚未由本cell补读；PR23终态原生已取回，见[主报告的证据状态更正](../report.md)及其新目录，机制会话正在补审。本cell未扩扫、未补造决策。父线继续整合跨cell判断。
