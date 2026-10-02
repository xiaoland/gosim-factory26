# I11 GitHub 身份、组织与团队旅程断点

2026-09-30，只读定向审查。对象是最终 replay `e68661975b53` 的冻结应用；`F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`，以下应用路径均相对 F。原始要求 `Q` = `requirements/requirements.yaml`。只写此报告；未运行应用、测试、生成或评测，未查私有评测器、Sheet，未修改应用/variant。读取根 AGENTS、run-analysis SOP，代码阅读采用 ponytail 端到端原则。本报告是候选断点而非官网逐例失败归因。

## 原需求前提与入口

| 需求层 | 必须保持的前提、入口与可观察结果 | 原文 |
|---|---|---|
| ROOT | 既有对象/权限是预置 seed；账号提供隔离浏览器会话；seed不完整也不禁用需求。写操作按当前session和目标权限校验，服务端原子持久化。角色不是自动累计梯度；带引号名称按精确英文accessible name匹配。 | Q:5–20 |
| REQ-1 / REQ-1-1 | account与当前浏览器session是不同对象。首页入口Sign up/Sign in/Forgot password，账号菜单通往设置/退出。注册直接verified、回登录；失败留非敏感输入清密码；恢复显示独立123456，不借外部邮件。 | Q:28–40,46–58 |
| REQ-1-1-1/2/3 | 注册由登录页唯一Create an account link进入；同时报告多字段错误。登录用Username or email/Password，统一Invalid credentials；刷新仍登录。恢复从Forgot password进入，known/unknown同step，错误code不改原密码。 | Q:65,152,258 |
| REQ-1-2/3 | 唯一Account menu button→Sign out link→Sign out dialog；Cancel不退出，Confirm sign out只撤当前会话；回退/刷新保护页不得恢复。Settings→Password and authentication，三个密码字段，错误当前密码/确认不写库，成功新密码立即可登录。 | Q:347,404–407 |
| REQ-2 / REQ-2-1 | Account menu→Your organizations→New organization/既有组织；组织overview有Repositories/People/Teams link。成员不默认获得私库权限；Owner/direct grant/direct team membership才获得。组织内多视图与实际仓库访问同步；创建组织初始Owner。 | Q:485–519,526,588–613 |
| REQ-2-2 | team名仅同组织唯一；组织成员关系、团队直接成员、parent树独立，parent不传播成员或授权。Owner能创建team、加/删成员和维护parent。移除组织member事务级联删本组织team-members及direct repo grants，保留账户/其它组织/团队grant，不能删最后Owner。 | Q:697–718,725–741,801–826,883–913,973–994 |
| REQ-2-2-2 seed | cycle场景要求同一个team已有parent且有可选择descendant；成员场景需现有org member尚未加入该team。Parent team是native select/combobox，拒绝后保留原选择。 | Q:801–826 |
| REQ-2-3 | repository Settings→Manage access→Add people or teams；Search实时筛选、option选team、Role/Write、Add；打开picker隐藏入口。既有grant行accessible name含主体名，行内native Role与Save；替换Read保留唯一grant。seed创建/替换是不同仓库/team初态。 | Q:1048–1084,1089–1124 |

## 按影响面排序的候选

### 1. 同名团队合法存在于不同组织，却阻断第二组织仓库授权（静态确证；评分影响未知）

**入口→前提→动作→结果：** 已登录Owner经Your organizations创建第二组织，Teams→New team创建与其它组织同名的合法team（如已seed的`frontend-team`）；打开第二组织仓库Settings→Manage access，Search能正确找到该team，选Write并Add。候选列表按当前`repo.owner_org_id`取得，但POST用全局name查询单条team，然后比较org_id。只要查到其它组织的同名team，返回422 `Team is not in this organization`，当前合法团队无法获grant；其成员也不会因此获得私库权限。

- 原要求：Q:699–705、Q:1060–1084明确team仅组织内唯一、授权当前组织team；DB也是`UNIQUE(org_id,name)`（`backend/src/db/migrations.js:48–55`）。
- 可达UI：`NewTeamPage.tsx:33–44,60–96`；`orgs/router.js:277–281`按org+name排重；`ManageAccessPage.tsx:68–86,149–169,178–198`以候选name提交subject。
- 断点：`backend/src/modules/repos/grants.js:78–80`列表正确按org过滤；`:130–136`为`SELECT * FROM teams WHERE name = ?`，缺org限定，再报team_not_in_org；事务`:139–156`不会执行。
- **反证/边界：** 单组织/全局名称恰好唯一时正常；既有grant PATCH按repo+grantId更新（`:179–188`），不受此POST断点影响。查询未ORDER BY，不能承诺每次选择哪个同名行，但静态能够确认合法输入的解析不唯一；不是所有授权均失败，也不是跨组织越权成功。
- **过程来源：** `S`=`tasks/iteration11/run-audit/github/snapshot-01/work/native-homes/`；`S/pi-glm-fast-01a0ebdc-009b-7e31-aa8b-6d2f2ec81a0c/2026-09-29T06-31-09-547Z_01a0ebdc-29eb-731e-a7b1-66cc34026ee6.jsonl` **L58 / 8308ea6f / 06:37:25**实际write已含这个全局查询，L59为成功回执。最终同样存在。F `docs/task-packets/m2-issue-4.md:45,51–52`同时记录组织内唯一及team须本组织，却未把组合转成正确查询。现有`e2e/orgs.spec.ts:316–356`只用acme-demo单一team，能在该断点存在时通过；不能由其PASS证明多组织链成立。
- 修复归属候选：grants团队主体解析层加目标org条件；下一轮判别证据是两个组织同名team、只给当前team新增grant并用其直接member开私库。此次不执行。

### 2. 启动seed把成功删除的成员关系重新加入（静态确证；需服务重启前提；评分影响未知）

**入口→前提→动作→结果：** Owner在acme-demo People通过Member menu bob-reviewer→Remove from organization→Remove；API当次原子删除org member、所有本组织team membership/direct grant。只刷新浏览器仍应正确。若使用同一个持久DB重启服务，默认seed重新插入bob的org membership与frontend-team membership，移除结果复活；若该team后来获得私库grant，bob会重新获得访问。单独从team立即Remove bob也被同一seed复活。

- 原要求：Q:16–18、Q:709–718、Q:804–809、Q:973–994；删除持久化而不是会话临时状态。
- 删除路径：`PeoplePage.tsx:78–84,151–192,218–241`，`orgs/router.js:219–248`；team立即删`:405–416`，`TeamMembersPage.tsx:68–75,137–140`。
- 启动路径：`backend/src/config.js:29–33`默认每次startup seed；`server.js:18–19`调用`runSeeds`；`seed/governance.js:41–43,75–79`无“初始化已完成”记录，按缺关系再次insert；`seed/repos.js:74,258–259`也重新保证alice/bob成员。`governance.js:67–71`还会把用户已清为空的seed parent恢复为platform-team。
- **反证/边界：** 这是restart生命周期缺陷，不是浏览器reload的即时失败；官网是否重启同DB未知。用户新创建/删除的非seed账号关系不在该固定插入中，不能外推所有删除均复活。角色update被OR IGNORE保留，密码变化也保留；“seed双跑幂等”只证明未发生用户删除时计数不增，不能证明尊重删除。
- **过程来源：** 上述M2 native **L60 / 4fba7ca3 / 06:37:45**写seed；L61成功；F packet:78–88明称幂等且只列“双跑”。该native **L31 / 21eeabb4**先认可insert-if-absent共存，**L413 / 5b1102af**交接称seed同业务键幂等。能证明把幂等当作共存依据，不能推断它明确考虑过用户删除后的restart。
- 修复归属候选：seed的首次provision生命周期；下一轮判别证据需要删除后同DB真实restart，保留既有数据及删除，不把反复运行seed视为恢复授权。

### 3. seed没有提供cycle场景要求的“已有parent且有descendant”的同一团队（静态初态缺口；评分影响未知）

**入口→前提→动作→结果：** Owner从Teams进入有existing parent的team Settings，选择其descendant后Save应报cycle且保留原parent。冻结seed只有frontend-team(parent null)、platform-team(parent null)、frontend-child(parent platform-team)。platform有descendant但无parent；frontend-child有parent但无descendant。因此该指定初态没有被预置，必须额外改造树才成立。

- Q:812–815明确这个GIVEN，ROOT Q:8–16要求预置。
- `seed/governance.js:18–22,58–73`为完整本模块树；循环判断本身`orgs/router.js:85–95,341–350`支持正确拒绝，`TeamSettingsPage.tsx:56–59`恢复原selected；不是断言cycle算法坏。
- 反证：可以经UI添加第三层再满足；不等价于题目要求的scenario前提已供应。正常parent修改成功路径可达。已有测试`e2e/orgs.spec.ts:199–207`明确检查platform原parent为空，是较弱的另一个场景。未见可得材料内额外seed配置将该团队树补齐；不据此断言官网一定用这些字面team名。
- 过程：同M2 L60写seed；F packet:82仅记录child→platform“层级/环演示”，最终验收摘要没有证明“非空原parent”反例。

### 4. grant行缺显式accessible name，自验按文字筛行而非name（运行待证；评分影响未知）

**入口→前提→动作→结果：** Admin在Manage access要定位“name含team名”的既有grant行，然后修改Role→Read→Save。`GrantRow`真实DOM是li，team名只在子span，未提供aria-label/aria-labelledby；native Role和Save本身存在，PATCH也正确，视觉上能操作。需实际浏览器AX树证明该listitem的computed name是否满足要求；此次未运行，不将“文本存在”替代名字，也不将静态DOM推论包装成运行失败。

- Q:1055–1059；`ManageAccessPage.tsx:222–267`；`:232–238`无名称属性。
- 反证：主体文本完整可见，人工能选中；需求未给此行唯一强制role，因此不能直接把缺`role=row`判为错。真正未证的是行名，而非控件缺失。
- 自验覆盖缺口：`e2e/orgs.spec.ts:335,350,354`是`getByRole('listitem').filter({hasText:'frontend-team'})`，不是accessible name判据。

## 已闭合路径、入口歧义和未升级项

身份链未找到让全部REQ-1都不可用的高影响静态断点：注册表单noValidate、关联label和提交Button，服务器聚合多字段errors、verified插入；失败前端清密码保留username/email；登录按username/email和hash、generic401、新随机session/cookie。来源`SignUpPage.tsx:36–108`、`SignInPage.tsx:32–87`、identity router:40–101、validate:20–98。恢复URL步骤、独立123456、code等值校验、密码更新和session撤销都有连线（PasswordResetPage:21–28,98–163；identity router:119–159）。改密由Settings导航，当前session保留/其它session撤销有明确原生D1解释，不能因ROOT“改变session状态”直接判保留当前session为错（SettingsLayout:20–22；identity router:164–186）。AccountMenu用自有disclosure保持link role、Radix Dialog标题形成dialog name，确认才POST sign-out；Cookie删除与DB session删除一致（AccountMenu:29–107；Menu:65–76；Dialog:21–30；session:43–75）。后端每个request attachUser而非使用客户端user推权限（app:57；middleware:12–21）。

前端实际组合是React 18.3.1 + React Router 6.28、原生input/select、Radix checkbox/dialog、自有Menu与SegmentedNav；`App.tsx:8–10`将所有路由置于AuthProvider和AppShell。checkbox关联label、SegmentedNav实际Link、team member按钮阶段隐藏、People两个Add member按原需求允许的先后顺序，都不能仅因组件名猜role不符。

首页同时有shell与body的Sign in/Sign up link（AppShell:114–119；HomePage:21–27）。REQ-1本段Q:28–33/73–77未单独要求唯一，但主线跨模块补读确认REQ-6父级 **Q:2837–2838**要求signed-in scenarios从首页**unique Sign in link**开始。因此这是**静态确证的跨模块入口契约违反**，不是仅名称歧义；仍不能确认官网定位方式或据此把所有失败归因到首页。登录页唯一Create an account link存在；登录submit仍仅一个button。首页没有Forgot password link（父级Q:32），登录页有该link（atomic Q:258），属父级入口遗漏但已有替代可达路径，未升级为全恢复失败。自验helper:57直达/login、helper:42直达/register，session.spec:17,42用Sign in.first()，无法证明首页精确名称导航无歧义。形成过程由主线已核foundation native：`S/pi-deepseek-fast-01a0eb6f-2435-7b40-8c0d-ca9ef86d9bfc/2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.jsonl` L46读父级首页Forgot password并决定Home Sign in/Sign up，L124写Home，L146创建直达/login helper；此来源为主线交接，cell未重复展开。Your repositories placeholder已交repo_content范围，不另重读。

组织创建、公开仓库筛选、People新增/删级联、团队member/parent、非Owner控件缺席的静态链都有实际UI/API/权限/事务支撑；Owner给组织所有仓库admin，普通member不默认私库授权，team只取直接membership（permissions:136–165；orgs/router:71–82,181–248,328–416）。本报告不以函数存在或已有PASS宣称运行验收。

## 覆盖与证据边界

已读ROOT/REQ-1/REQ-1-1及REQ-2/REQ-2-1/REQ-2-2父级描述、所属atomic描述及关键scenario初态；核对routes/App/AuthContext、身份4页面、安全设置、账号菜单、相关基础组件、全部org页面/client、identity/org/grants router、权限、session、中间件、schema、account/governance/repo seed及启动接线。需求长输出截断后补读遗漏的org/team/grant描述，代码大批输出截断后对关键组件/启动/schema补读；不把初始截断当完成。现有tests只静态读与候选有关的断言，未执行。已有历史m1-m2审查只作为导航/竞争解释，不重新计全读；native新读范围为M2定向L31、58–61、132、152、222、239、269、413及邻接回执。PR23终态native现已取回，见[主报告的证据状态更正](../report.md)及其新目录；机制会话正在补审，本cell未重复读取，不补造独立全量复核。

未检查真实浏览器AX树、现场用户操作、最终DB修改历史或官网逐例结果。上述1/2是代码能确定的条件性错误，3是seed初态缺口，4需要AX行为补证；首页唯一Sign in违反另由主线跨模块原文确证；均不能据汇总4/100、1/47预测具体扣分。审查实际墙钟未精确记录，无额外遥测。主线已即时收到同名team授权断点及AX/seed候选；本cell无实施任务或实验待交接。
