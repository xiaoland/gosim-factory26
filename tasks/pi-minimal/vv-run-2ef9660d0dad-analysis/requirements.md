# 原始需求树与新产物前置／跨层核对

本单元只读分析 `2ef9660d0dad` 新工作区，对照 `c3fea0c3488c` 的同一份公开需求与既有结论。仅本报告是持久写入；未修改应用、variant、已有工作项，未运行下载应用、测试、模型或评测，也未读取外部评测器。

## 对象与证据口径

- **R**：[公开 requirements.yaml](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1)，新旧均 292270 bytes，SHA-256 `bdc17d23265a6b1948aec150e69d0b2accfa37db4c569305c97be7ff7f3b0b8f`。以下需求行号两版通用。
- **N**：新源码／保存数据根 `runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/`。
- **M**：[新主原生 session.jsonl](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/.factory26/pi-minimal/session.jsonl:1)，551行。本单元只定向回读 M389–390、M529–532，不声称全过程覆盖。
- **O**：[旧因果结论](../github-score-analysis/causality.md)，复用其已证 Write误抽象、PR milestone漏范围；旧搜索证据复用 [旧报告](../github-score-analysis/report.md)。本单元没有重新全读旧会话。
- 两版 `requirements/prerequisites.md` 均 0 bytes，SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`，不存在一份额外前提文档能替代 ROOT／父层。
- **静态可达**指从源代码条件与参数可推导；**保存数据实证**指 ZIP 的 SQLite+WAL 快照；**历史运行实证**仅限原生会话已保存输出。未做新浏览器运行。官网总分和空逐例结果不能把这些缺口映射成具体失败数。

## 完整树与继承边界

共 **65节点 = ROOT + 17其它FOLDER + 47 ATOMIC**，共 **100 scenario**；叶子按顶层分布为 REQ-1 5、REQ-2 7、REQ-3 6、REQ-4 8、REQ-5 9、REQ-6 12。下面是完整原始树，保留父节点及显式依赖；依赖不是父层约束的替代。每个叶子还须承接其所有祖先的入口、权限、初态、唯一性、持久化和跨页一致性要求。

已读所有节点的 description/dependencies，及全部 scenario 的具体 GIVEN/WHEN/THEN；为控制重复，场景读取视图省略重复“fresh unauthenticated home”与 Seed values 后缀，重复的通用 visible-workflow/reload/rejection 模板只读一次，其余按原文读取。截图文件未检查。此表是需求覆盖账，不是47项实现通过声明。

|节点|父节点／类别|原始名称|显式依赖|场景数|保留的关键契约|
|---|---|---|---|---:|---|
|[ROOT](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1)|— / FOLDER|GitHub Collaboration Platform Core Requirements|—|—|精确英文可访问名；场景种子预供给、独立账号会话；所有叶子始终启用；服务端按当前对象/会话授权并原子持久化；角色非累积阶梯。|
|[REQ-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:24)|ROOT / FOLDER|Identity and Access|—|—|主页账号入口→统一登录页；右上账户菜单显示当前用户；后续组织/仓库/工单复用会话；退出、密码修改/恢复立即影响后续请求。|
|[REQ-1-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:42)|REQ-1 / FOLDER|Account Registration and Recovery|—|—|注册直接验证email并回登录；登录不复制账号；恢复固定123456，无邮件/外部码服务；失败保留非敏感值、清除密码回显。|
|[REQ-1-1-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:60)|REQ-1-1 / ATOMIC|Register a New GitHub Account|—|3|唯一Create an account入口；精确字段/未勾terms/可提交按钮；用户名、邮箱、密码规则；并列字段错误；成功邮箱登录与刷新。|
|[REQ-1-1-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:146)|REQ-1-1 / ATOMIC|Sign In with an Existing Account|REQ-1-1-1|4|用户名或邮箱登录；所有凭据失败统一Invalid credentials；成功唯一会话、workspace与后续保护页保持。|
|[REQ-1-1-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:252)|REQ-1-1 / ATOMIC|Recover Account Access Through a Verified Email|REQ-1-1-1|3|Forgot password→同一步骤对已知/未知邮箱；独立可见123456；错误码保留旧密码；正确更新同一账号。|
|[REQ-1-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:341)|REQ-1 / ATOMIC|Sign Out and End the Current Web Session|REQ-1-1-2|2|唯一Account menu button、Sign out link；具名dialog Confirm/Cancel；只确认失效当前浏览器会话，后退/刷新不复活。|
|[REQ-1-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:398)|REQ-1 / ATOMIC|Change Account Password|REQ-1-1-2|3|Settings→Password and authentication；三密码字段；错误不更新；各场景独立账号/候选；成功新密码可用旧密码无效。|
|[REQ-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:480)|ROOT / FOLDER|Organization and Governance|REQ-1-1-2|—|Your organizations进入；Repositories/People/Teams；Member无私库默认权；Owner/直接授权/直接team成员生效；变更各视图同步。|
|[REQ-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:499)|REQ-2 / FOLDER|Organization Identity and Discovery|REQ-1-1-2|—|组织heading与三link导航；组织标识全局唯一，display name有效；创建者Owner；后续以同一组织ID继续。|
|[REQ-2-1-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:521)|REQ-2-1 / ATOMIC|Browse Organization Repositories|—|2|Repositories link、Find a repository即时过滤、精确仓库名link；游客公开可读、私有不泄露；Back与刷新一致。|
|[REQ-2-1-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:583)|REQ-2-1 / ATOMIC|Create an Organization After Authentication|REQ-1-1-2|3|账户菜单Your organizations link→New organization；ID heading；重复ID即便display空也报重复；成功Owner+列表同步。|
|[REQ-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:692)|REQ-2 / FOLDER|Team and Member Management|REQ-2-1-2|—|team名组织内唯一；父team同组织且无环；成员关系不按层级传播；移除组织成员联删team成员和个人grant，保留team grant及至少1Owner。|
|[REQ-2-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:720)|REQ-2-2 / ATOMIC|Create an Organization Team|REQ-2-1-2|2|Owner从Teams→New team；可只填合规名；保存team及可选parent；错误不创建。|
|[REQ-2-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:796)|REQ-2-2 / ATOMIC|Manage Organization Team Members and Hierarchy|REQ-2-2-1|2|仅Owner；同一步仅一个Add member；精确member仅一次、立即Remove；Parent team原生select；拒绝环后保持原值。|
|[REQ-2-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:878)|REQ-2-2 / ATOMIC|Directly Add a User as an Organization Member|REQ-2-1-2|2|Owner直接添加已注册非member；无邀请/Pending；重复不复制；新成员看到完整组织ID但未授权私库Access denied。|
|[REQ-2-2-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:968)|REQ-2-2 / ATOMIC|Remove a Member from an Organization|REQ-2-1-2|2|Owner Member menu→Remove from organization→Remove；非Owner菜单缺席；删除组织关系、team成员、direct grants；保留个人资源/最后Owner。|
|[REQ-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1042)|REQ-2 / ATOMIC|Grant Repository Access to People and Teams|REQ-2-1-2, REQ-2-2-1|2|Settings→Manage access；即时Search选member/team；每subject/repo单grant可替换；有效role取最高，但操作仍按ROOT集合；team层级不传权。|
|[REQ-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1126)|ROOT / FOLDER|Repository Asset Management|—|—|owner/repo heading、标记和Code/Issues/Pull requests/Settings；搜索/列表/直链同一可见性；Member无默认私库权。|
|[REQ-3-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1146)|REQ-3 / ATOMIC|Search for and Locate Repositories|—|4|全局Search searchbox+Enter直接仓库结果；link恰为仓库名；无匹配No results、重复无旧结果、私库不泄露。|
|[REQ-3-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1252)|REQ-3 / FOLDER|Repository Creation and Distribution|REQ-1-1-2|—|创建入口New repository；fork独立仓库/历史与来源关系；clone仅地址复制；新建与fork进入可浏览overview。|
|[REQ-3-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1271)|REQ-3-2 / ATOMIC|Create a Repository with Owner, Visibility, and Initialization Options|REQ-1-1-2|3|默认个人Owner；Public/Private radio、README checkbox；原子repo/branch/file/commit；重复/空名无需额外输入即验证。|
|[REQ-3-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1362)|REQ-3-2 / ATOMIC|Fork a Repository into Another Namespace|REQ-3-3, REQ-1-1-2|2|Fork button→Create fork；默认个人namespace/允许visibility；复制历史且独立；私源保持私有；同名拒绝。|
|[REQ-3-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1428)|REQ-3-2 / ATOMIC|Copy a Repository Clone Value|REQ-3-3|2|Code button与Code link分工；HTTPS/SSH tabs；复制当前完整协议地址、Copied、标题保持；不修改仓库。|
|[REQ-3-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1490)|REQ-3 / ATOMIC|View a Public Repository Overview|—|1|游客打开稳定公开地址；owner/repo heading、Public、Code link和元信息；刷新不变。|
|[REQ-3-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1526)|REQ-3 / ATOMIC|Change Repository Visibility with Permission Checks|REQ-3-3, REQ-1-1-2|2|Settings→General→Danger Zone；Change visibility button、Public radio、Confirm visibility；非Admin控件缺席；原私库内容可公开读取。|
|[REQ-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1591)|ROOT / FOLDER|Code and Version Control|REQ-3-3|—|文件/目录/branch/immutable commit；页显示repo+revision；读场景游客直达；写场景独立Write账户及未保护branch；首页登录后username可见；named controls唯一。|
|[REQ-4-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1620)|REQ-4 / ATOMIC|Browse Repository Files and Directories|REQ-3-3|1|精确directory/file links；当前branch/path及完整内容；刷新保留，同步branch不写数据。|
|[REQ-4-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1656)|REQ-4 / FOLDER|Commit History and Code Search|REQ-4-1|—|commit history/diff/code search只读；history逆序、diff两revision、搜索仅当前可读repo；复用文件上下文。|
|[REQ-4-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1672)|REQ-4-2 / ATOMIC|View Repository Commit History|REQ-4-1|1|repo/file唯一Commits link；完整message/author、ago；file history只含改变该文件的commit。|
|[REQ-4-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1710)|REQ-4-2 / ATOMIC|Inspect Commit and Revision Differences|REQ-4-2-1|1|游客直接commit entry显示src/search.ts、Changed files及增删统计；不变更repo。|
|[REQ-4-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1748)|REQ-4-2 / ATOMIC|Search Code Within a Repository|REQ-4-1|4|repo Search→Enter→唯一Code link；匹配README.md/file link和query；结果页保留scope/query；无匹配No code results，重复无旧值。|
|[REQ-4-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1854)|REQ-4 / FOLDER|Branch Management|REQ-4-1|—|branch是唯一命名commit ref；创建不复制历史；默认branch只改默认入口；命名约束；已有PR源/目标引用不被改。|
|[REQ-4-3-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1874)|REQ-4-3 / ATOMIC|List and Switch Repository Branches|REQ-4-1|2|唯一Branch <name> button、Find branch textbox、精确option；即时搜索/切换；main到feature-search出现main-only.md；Escape保留。|
|[REQ-4-3-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1931)|REQ-4-3 / ATOMIC|Create a Branch from an Existing Revision|REQ-4-3-1, REQ-1-1-2|2|Write/Maintain/Admin/Owner；即时Create branch: <name> option或Invalid branch；当前head为base；一次选择创建并切换、刷新保持。|
|[REQ-4-3-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:1996)|REQ-4-3 / ATOMIC|Change the Repository Default Branch|REQ-4-3-1, REQ-1-1-2|2|仅Admin/Owner；Settings→Branches→原生Default branch select→Update→Confirm；非Admin无编辑控件；旧branch/PR不改。|
|[REQ-4-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2055)|REQ-4 / ATOMIC|Manage Repository Files Through the Web Interface|REQ-4-1, REQ-1-1-2|2|Add file→Create new file或Edit；Write+；path/content/message+commit+head原子；初始空message；非法路径/保护branch拒绝不变。|
|[REQ-5](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2125)|ROOT / FOLDER|Work Planning and Issue Management|REQ-3-3|—|issue详情侧栏Assignees/Labels/Milestone顺序；append-only活动；Write能内容但禁metadata/status；种子各mutation隔离；首页login后username可见、控件唯一、详情直达。|
|[REQ-5-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2166)|REQ-5 / FOLDER|Issue Discovery and Details|REQ-3-3|—|list过滤不写；detail聚合同一编号的正文/metadata/timeline，并为所有Issue操作共同入口。|
|[REQ-5-1-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2182)|REQ-5-1 / ATOMIC|List and Filter Repository Issues|REQ-3-3|2|Open/Closed links、唯一Search issues即时过滤，状态+关键词组合及刷新保持；title link精确。|
|[REQ-5-1-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2242)|REQ-5-1 / ATOMIC|View an Issue and Its Discussion|REQ-5-1-1|3|heading恰为title不含编号；Improve onboarding及指定完整description；允许角色才有编辑控件，持久化discussion/metadata。|
|[REQ-5-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2335)|REQ-5 / FOLDER|Issue Creation and Discussion|REQ-5-1-2|—|title/body/comment长度；repo内编号；创建activity；失败不分配空号/不写半条；内容变更保留其它字段。|
|[REQ-5-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2355)|REQ-5-2 / ATOMIC|Create a Repository Issue|REQ-3-3, REQ-1-1-2|2|Write/Maintain/Admin；New issue link→精确fields/button；空白title拒绝且无新号，成功返回精确title/detail/list。|
|[REQ-5-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2421)|REQ-5-2 / ATOMIC|Edit an Issue Title and Description|REQ-5-1-2|2|独立Edit issue title/description及Save actions；Read/Triage拒绝；错误title恢复Original issue title。|
|[REQ-5-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2494)|REQ-5-2 / ATOMIC|Comment on an Issue Discussion|REQ-5-1-2, REQ-1-1-2|2|Write+评论；任意可读登录者自己的reaction toggle唯一；article语义；空白不增加comment/activity。|
|[REQ-5-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2567)|REQ-5 / FOLDER|Issue Metadata and Classification|REQ-5-1-2|—|metadata仅关系，不赋权；milestone单选/None；不给label/milestone CRUD，seed/新repo预供给；不跨repo。|
|[REQ-5-3-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2589)|REQ-5-3 / ATOMIC|Assign or Unassign Issue Participants|REQ-5-1-2|1|仅Triage/Maintain/Admin操作者；候选至少Triage；即时Search assignees与option click保存关闭；再选取消、历史保留。|
|[REQ-5-3-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2648)|REQ-5-3 / ATOMIC|Apply Labels to an Issue|REQ-5-1-2|1|仅Triage/Maintain/Admin；Labels options当前repo；初始未应用，点击立即toggle；Read/Write无控件且server拒绝。|
|[REQ-5-3-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2696)|REQ-5-3 / ATOMIC|Assign Issues and Pull Requests to a Milestone|REQ-5-1-2|1|Issue及PR两类；Milestone button+精确option，None清除，当前repo单关联；Read/Write无写权。|
|[REQ-5-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2736)|REQ-5 / ATOMIC|Close or Reopen an Issue|REQ-5-1-2|2|仅Triage/Maintain/Admin；Open→Close issue→Closed issue activity→Reopen；Read/Write无控件/server拒绝；metadata不变。|
|[REQ-6](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2801)|ROOT / FOLDER|Change Review and Merge Control|REQ-3-3, REQ-4-3|—|PR统一状态/commit生命周期；比较前创建；新compare使review stale/inline Outdated；首页唯一Sign in、username可见、精确控件唯一；逐scenario独立restore。|
|[REQ-6-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2848)|REQ-6 / ATOMIC|Protect Branches with Review and Status-Check Requirements|REQ-4-3-1, REQ-1-1-2|3|Admin独立approval/check protection toggles；当前commit最新非作者review有效；Checks初始pending可保存setter/time；保护分支禁直写。|
|[REQ-6-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2936)|REQ-6 / FOLDER|Pull Request Discovery and Creation|REQ-4-3|—|Read不可创建、Write+可创建；临时compare不写；重复Open/Draft branch pair、无diff、同branch均拒绝。|
|[REQ-6-2-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:2956)|REQ-6-2 / ATOMIC|List and Filter Repository Pull Requests|REQ-3-3|3|公众list/Open filter/title link/heading与刷新；按status/author/review过滤；不修改PR。|
|[REQ-6-2-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3043)|REQ-6-2 / ATOMIC|Compare Branches Before Opening a Pull Request|REQ-4-3-1, REQ-1-1-2|2|仅Write+可入compare；原生base/compare；即时No changes与disabled；独立valid pair无既有Open/Draft；已知src/search.ts。|
|[REQ-6-2-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3107)|REQ-6-2 / ATOMIC|Create a Pull Request from Comparison Results|REQ-6-2-2|2|Create pull request先开form再唯一submit；title为空不创建；原子Open PR+number+branch/commit/context，刷新保持。|
|[REQ-6-2-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3192)|REQ-6-2 / ATOMIC|Create a Draft Pull Request|REQ-6-2-2|2|Create draft先开form；Draft有可见disabled Merge；独立ready seed作者操作Draft→Open，其它fields/reviews不改。|
|[REQ-6-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3268)|REQ-6 / FOLDER|Pull Request Review Workspace|REQ-6-2-3|—|同一PR的overview/commits/files；非作者Write+仅Open可review；pending隔离；每人每当前commit只有最新有效decision，历史保留。|
|[REQ-6-3-1](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3289)|REQ-6-3 / ATOMIC|View Pull Request Overview and Commits|REQ-6-2-3|3|公众PR直达；精确title heading、Conversation/Commits/Files changed links；同PR/branch/commit只读一致。|
|[REQ-6-3-2](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3390)|REQ-6-3 / ATOMIC|Inspect Changed Files and Aggregate Diff|REQ-6-3-1|1|当前base/compare diff、精确path与aggregate <n> additions, <n> deletions；只读，无跨私库泄漏。|
|[REQ-6-3-3](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3438)|REQ-6-3 / ATOMIC|Add Review Comments to Changed Code Lines|REQ-6-3-2, REQ-1-1-2|2|非作者Write+；直接Add comment在changed line；single公开、pending仅作者可见并reload保持；commit变更保留原锚点Outdated。|
|[REQ-6-3-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3517)|REQ-6-3 / ATOMIC|Submit a Pull Request Review|REQ-6-3-1, REQ-1-1-2|2|Review changes→Summary+三radio→Submit review；非作者Open；每reviewer/commit最新decision；Request changes后新Comment/Approve可解除。|
|[REQ-6-4](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3592)|REQ-6 / ATOMIC|Request or Remove Pull Request Reviewers|REQ-6-2-3, REQ-1-1-2|1|作者或Maintain/Admin/Owner在Open/Draft；Reviewers+Search即时option；request与decision分离；精确Remove <username>即时且持久。|
|[REQ-6-5](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3652)|REQ-6 / ATOMIC|Merge an Eligible Pull Request|REQ-6-3-4, REQ-6-1|2|Maintain/Admin/Owner；独立eligible/blocked seed；保护main+当前非作者approval+test success；先解释拒绝，原子双parent merge+head+终态。|
|[REQ-6-6](/Volumes/WorkSSD/Development/factory26/runs/analysis/pi-minimal-vv-2ef9660d0dad/20260930T072251Z/extracted/template/requirements/requirements.yaml:3747)|REQ-6 / ATOMIC|Close or Reopen a Pull Request Without Merging|REQ-6-2-3, REQ-1-1-2|2|作者或Maintain/Admin/Owner；立即close/reopen，Read viewer两按钮缺席；保留timeline/branch；Merged终态。|

## 高覆盖断点：先核父层，再核叶子

### 1. 首页登录入口不唯一，登录后身份显示也未承接父层

**需求及继承**：R:L2831–2839（REQ-6父层）明确“Each named action, field, and navigation link is unique on its active page”以及“unique Sign in link on the home page”“account username visible after authentication”。REQ-4父层R:L1614–1618、REQ-5父层R:L2160–2164也规定首页登录、登录后username可见与named controls唯一。ROOT R:L5–20没有允许这些父层约束被忽略。

**新产物**：`N/frontend/src/App.jsx:L44–46` 在 Layout 内渲染 Home；未登录时 `Layout.jsx:L96` 与 `pages/Home.jsx:L52` 各渲染一个同名 Sign in link。因此两个入口会同时存在。`pages/SignIn.jsx:L17–19` 登录成功回 `/`；`Layout.jsx:L65–92` 将 `me.username` 只放在 Menu 的 children 里（L72），而 `ui.jsx:L49–51` 仅在 open 时渲染 children。`Home.jsx:L21–44` 的登录 workspace没有username，闭合的账户按钮文本仅“Account menu”。所以登录成功后的默认页面不直接显示当前username；打开账户菜单才出现。

**运行证据**：M389（`403ab586`, 05:44:28Z）实际调用 `snapshot -i | grep -cE 'link "Sign in"'`；M390（`09b40972`, 05:44:29Z）返回计数 **2**。最终阶段 M530（`6ba84cd8`, 06:04:27Z）保存的登录workspace交互快照仍显示关闭的Account menu；M531–532点击后返回 `menuitem "alice-dev"`。M530是 `snapshot -i | head -20`，单独不能证明所有普通文本不存在；上述源码条件提供身份可见性结论，快照提供现场支持。

**影响与边界**：这属于多条认证后流程共享的进入条件缺口，包括REQ-4/5/6父层下的写入流程。精确角色/名称的唯一定址可能在进入业务前就无法成立。已证的是公开契约违规和历史页面输出；官网没有逐例日志，不能把它换算为“所有96个未通过场景都卡在登录”。

**对旧结论的增量修正**：旧报告 `github-score-analysis/report.md:L40` 称“需求未明确要求唯一 Sign in”，本轮完整父层阅读反证这一限定；新旧需求哈希完全相同。应保留“不能推断评分贡献”，但不应继续把唯一性仅写作未知评测器的潜在选择器偏好。未修改旧工作项。

### 2. 账户菜单的实际角色不符，影响组织与退出入口

**需求**：R:L588–590要求账户菜单中的 **link** “Your organizations”；R:L347要求恰好一个 **link** “Sign out”，再打开具名dialog；REQ-1父层R:L32–40使账户菜单成为安全设置／退出共同入口。

**新产物**：`N/frontend/src/Layout.jsx:L84–86` 的 Your profile、Your organizations、Settings 虽使用 React Link，却显式设置 `role="menuitem"`；L87–89将 Sign out 实现成 `button role="menuitem"`。标签文字正确不等于角色正确。M532（06:04:30Z，`333ecd9d`）原生快照分别记录 `menuitem "Your organizations"`、`menuitem "Settings"`、`menuitem "Sign out"`，这是已有运行实证。

**范围**：Your organizations入口不满足REQ-2-1-2；Sign out入口不满足REQ-1-2。Settings是否必须link应由其具体场景使用判断，本报告不以所有菜单项一概错误代替明确需求；它至少说明产品把不同契约统一改成了menuitem。已实现的Sign out对话框/取消/确认按钮（Layout L103–109）不能弥补前一跳的角色不符。

### 3. Owner的People页有未导入组件，组织标识也被display name替换

**需求**：REQ-2父层R:L485–497规定People是Owner增删成员入口；REQ-2-2-3/4依赖同页。R:L590–591要求新组织overview heading含组织标识；R:L892–893要求新增Member在Your organizations看到完整组织identifier。

**新产物**：`N/frontend/src/pages/OrgPage.jsx:L4` 只从ui导入 `Field, Picker, Spinner, Dialog`；完整文件没有定义或导入 `Menu`，PeopleTab却在 `data.canManage` 分支L135–150执行 `<Menu>`。Owner打开含成员的People页时会使用未绑定标识符，静态可推出该渲染分支抛ReferenceError；非Owner不渲染分支，不能用非Owner页可见反证Owner路径。这里未运行应用，未把它写成新观测异常。

同时 OrgPage L23的heading仅为 `org.displayName`，L24才以普通文本显示 `org.name`；`pages/Organizations.jsx:L19` 的列表link仅显示 `o.displayName || o.name`，不同时显示identifier。对于 `acme-demo` / `Acme Demo`、`mobile-guild` / `Mobile Guild` 这类不相同值，heading/list无法满足指定标识的可见性。不是把显示名称与标识相同的样例成功推广为所有组织通过。

## 旧问题在新版的具体终态

### 4. Write禁令：UI已改正确集合，服务端仍放行

R:L2142–2151、L2663–2664、L2702、L2741–2742明确：Issue metadata/status操作者集合为Triage/Maintain/Admin，**Write禁止**；Owner等效Admin。R:L1069–1074允许计算多个来源中的最高有效role，并不把操作授权变成累积阶梯。

|层|新证据|判断|
|---|---|---|
|有效role排序|`backend/src/perms.js:L3–4`: `read:1, triage:2, write:3, maintain:4, admin:5`，`atLeast`比较等级|用于有效role归并可成立；不自动证明操作授权成立|
|UI|`frontend/src/pages/IssuePage.jsx:L22–23`: canWrite=[write,maintain,admin]，canTriage=[triage,maintain,admin]；L65–95及L265按后者隐藏metadata/status|相较旧版，Write页面控件边界已承接正确集合|
|服务端共同守卫|`backend/src/issues.js:L116–122`: `withIssue(..., minRole)`用 `atLeast(ctx.role,minRole)`|Write>=Triage，因此不能拒绝Write提交|
|具体四类动作|issues.js L153–154 status，L165–166 assignees，L201–202 labels，L217–218 milestone，都传 `'triage'`|全部仍存在后端越权静态路径；requireAuth只保证登录，不能阻止这类已登录Write|

因此应写“**只修前端，后端旧错误保留**”，不能写“新版完全修好”，也不能忽略已有前端改进。没有执行Write请求；该结论是参数与分支推导。下一轮判别应分别核Write界面控件缺席与服务端明确拒绝，同一个Read拒绝结果不能区分正确集合与错误下限。

### 5. PR milestone仍没有数据、接口或入口

R:L2140–2141与R:L2702原文均包含“Issue or pull request”；R:L2577–2584限制每个work item一个本repo milestone，None删除关联。叶子的编号属于REQ-5不等于对象范围只能为Issue。

新 `backend/src/db.js:L99–111` 的issues有milestone_id，L147–164的pulls表没有该字段，也无PR-milestone关系表。完整 `backend/src/pulls.js:L1–346` 无milestone读取／更新；完整 `frontend/src/pages/PullPage.jsx:L1–570` 无Milestone入口，侧栏L62–97仅merge、ready、reviewers、close/reopen。Issue侧 `issues.js:L217–229` 与 `IssuePage.jsx:L75–79,L323–337` 已承接，不能证明PR侧存在。

与旧因果链O的终态一致；本单元没有从终态反推新run的遗漏起因、动机或具体决策时点，过程形成机制交由过程单元。下一轮若改通用方法，应保留并列对象集合并逐一指向数据、服务端和入口，不能仅按模块ID打勾。

### 6. 搜索：旧入口上下文问题有所改变，新接线仍断

**公开路径**：R:L1754要求“repository page Search→Enter→Code link→result file”，并在空搜索/重复搜索时保持scope/query。R:L1151的全局仓库搜索则应直接有repository results，无需额外type-filter。

**旧证据复用**：旧报告L38–40已经证明Header在Routes外使用子路由useParams取不到repo，且原生验收在Unknown ref失败后改为直接结果URL。这里不重新推定旧缺陷是新缺陷。

**新版前一跳**：Layout.jsx L21–27改为解析 `location.pathname`，在正常 `/:owner/:repo` 页面能取得repoContext；L29–35向 `/search?q=...&repo=owner/name` 导航。SearchPage L30–35在repoContext存在时显示一个Code link，搜索页本身不渲染RepoHeader；全局仓库结果默认scope=repositories，L44的结果link恰为repo名。以上源码反证了“仍是同一个useParams入口缺陷”的说法。

**新版决定性参数错误**：`SearchPage.jsx:L17–19`把repoContext拆开后发送 `owner` 与 **`name`**，而 `backend/src/search.js:L22`读取 `req.query.owner` 与 **`req.query.repo`**。正常UI调用缺repo参数，仓库名变成空串；`repo-helpers.js:L4–9`没有默认仓库回退，精确匹配不到记录，search.js L23返回 **404 `Repository not found`**。`SearchPage.jsx:L23`再把异常吞成 `{results:[],repos:[],...}`，L80显示 **No code results**。这把接口失败伪装成业务零匹配，已知query同样走这条路径；是静态可达的完整前后端错误链，不是新HTTP运行实证。

**另一个范围保留缺口**：Layout L24把`search`排除在pathname repo推导之外，L34仅复用pathname所得repoContext；所以用户在 `/search?...&repo=...&scope=code` 页面再次提交Search时丢失repo/scope，尽管searchbox仍显示旧query。应把旧结论中的“完整用户入口不能被直达结果URL替代”保留为通用方法，但这次具体实现问题位于参数接线与结果页重搜上下文。

## 初始状态与跨场景约束

R:L9–16要求场景预供给记录且seed不足不能停用叶子；REQ-5父层L2152–2159要求edit/invalid-edit/comment/invalid-comment/assignment/labels/milestone/closing使用互不污染的独立issue；REQ-6父层L2840–2845明确role accounts/branches/PRs/mutable state逐scenario独立供给和恢复，含重复与并发。

`N/backend/src/index.js:L16`启动调用seed，`db.js:L284–286`仅在users表为空时执行，已有任意用户即return。README把它说明为“created on first start”。这改善了旧版无条件重启删库的持久性风险，却不是逐场景恢复机制，不能把“每次重启会清零”的旧归因继续套用。

只读检查原ZIP的 `backend/data.sqlite` 及 `-wal`/`-shm`：将三文件复制到临时目录，以SQLite `mode=ro`查询，未导入或运行应用。保存数据与seed源码吻合：

|对象|实际保存快照／源码|需求影响及限制|
|---|---|---|
|账号/角色|3 users：alice-dev、bob-reviewer、carol-writer。alice为org Owner；bob为acme-docs Maintain；carol无组织成员身份。仅另有secret-research的team Write grant，team_members为空。源码db.js L294–337。|不存在effective Write的独立contributor/reviewer；Read可由公开库给予carol，但不应误称“Read账号完全不存在”。Write+正常动作由Maintain可走，不等于Write禁令边界被供给。|
|Issue|#1 Improve onboarding Open（bug、bob已关联）；#2 Legacy welcome text Closed；#3 Original issue title Open。db.js L393–413。|未给8类mutation各自隔离对象；默认#1与assignment/label“尚未关联”的初态相反。其它issue可能承担某个动作，故不把“默认#1已关联”写成任何选择下都无法满足；缺的是公开约定所需对象选择与恢复闭环。|
|PR|#4 Improve onboarding Open、#5 Fix search Closed、#6 Draft onboarding update Draft。db.js L415–437。|只有一个Open PR；无法同时对应明确要求独立的single/pending inline、approve/request changes、success/refusal merge及close/viewer等初态。|
|保护/review/check|`protection_rules=[]`、`reviews=[]`；只有#4当前commit的test=pending。db.js L421–428只写pending，无seed protection/review插入。|REQ-6-5 L3662–3666明确的protected main+valid non-author approval+test success之eligible merge seed不存在；独立blocked seed也未提供。REQ-6-1的“另一个已保护main上的Open PR”同样未供给。|
|有效compare pair|main←feature-search无Open/Draft PR，README也明确保留；db.js L352–358提供compare branch。|初次常规创建有条件可用，不能笼统说全部PR前提缺失；一次创建后对同pair再次创建会触发pulls.js L87–90的合法重复拒绝，需要独立pair／状态restore才能满足重复场景。|

**证据边界**：以上是交付保存快照，不自动等于官网每个scenario开始时数据库。本单元未找到可得逐例执行日志／重置调度，不声称发生了实际并发污染，也不猜测官网会或不会重启或另行供给。最小补证是明确启动制品、DB路径与场景初态配置，再依据已有公开需求核对；不需要读取隐藏评测器。需求R:L12–13也不要求私有seed API，因此建议不是“为评测器增加后门接口”。

## 紧凑跨层附录（非全面追加审查）

以下是在核对同一PR链时直接可见的具体问题，均为静态推导，不作为本次总分归因：

|需求|源码链|确定缺口／反证|
|---|---|---|
|REQ-6-3父层L3280–3282、REQ-6-3-4 L3534–3539：同reviewer/current commit只最新decision有效|pulls.js L252–259仅追加submitted reviews；perms.js L69–82用任意匹配的历史CHANGES_REQUESTED/APPROVED，没有latest筛选|先Request changes再Approve/Comment仍被历史Request changes阻止；不是review历史应该删除，而是有效决策选择错误。新commit通过repo更新可使旧commit review stale，不足以修正同commit替换。|
|REQ-6-3-3 L3456–3458：pending draft对作者立即可见并reload保留|pulls.js L127–133只读published inline；PullPage L480/L502提交后关editor并reload，完整文件没有Pending review呈现|pending保存后UI无作者可读入口。原需求scenario 2 L3512–3515“only after submitted”语句与description对作者可见的细化存在表面张力；这里以description明确区分“作者可见／不公开”为判据，未把它解释成草稿应对他人公开。|
|REQ-6-4 L3610–3615：author可request reviewers；REQ-6-3父层排除作者review|App.jsx L34/37传me=user对象；PullPage L25主页面正确比较data.me字符串；但ReviewersSection L168用`me === p.author`，FilesTab L432用`me !== p.author`|Write作者被误判非author，Reviewers操作会被隐藏；同作者inline/review按钮可能出现，再被后端L220/246拒绝。Admin/Maintain作者能经另一个角色分支继续，不能证明author条件正确。|
|REQ-6-2-4 L3199–3200：Draft要有可见disabled Merge button|PullPage L141–158仅在canMerge且status=open渲染Merge button，draft分支L159只有解释文本|Draft时控件缺席，不是可见disabled。|
|REQ-6-5 L3680–3682：成功展示result commit|pulls.js L19–24 pullJson不返回merge_commit_id；PullPage L67只有p.mergeCommitId存在才显示|后端有写merge_commit_id（L334–335），但响应/UI字段未接通；不能仅以DB有列判交付完成。|

## 收敛与缺证

- **完成覆盖**：65个需求节点、47叶子description及100场景归一阅读（具体行为条款完整、通用重复模板去重）；新旧需求字节同一性；完整读取Layout/Home/App/SearchPage/RepoHeader/ui、IssuePage/issues/perms、PullPage/pulls/db/index、RepoPage/FilePage/FileEditor、OrgPage/Organizations/ComparePage、repos及repo-helpers；只读保存数据库，及M389–390、529–532定向运行证据。部分其它文件仅索引或工具取得，未内容阅读，不计覆盖。
- **未覆盖／未声称**：截图视觉还原、其它页面全面审查、前端构建物与源码逐文件同一性、完整原生过程、官网逐scenario路径／状态／失败原因；未对全部47叶子作实现验收。前述列为“已证”不等于已证明4/100的直接评分原因。
- **适合主线收敛的机制**：需求树父层没有进入最终入口判据；UI与后端同一权限规则失配；并列对象集合遗漏；接口请求字段不一致又被空状态吞错；种子对象与恢复生命周期没有对应完整独立场景。可改变因素应先落到这些具体交接与判据，不能从这次报告推出“多读技能”“多做检查”或模型升级就保证提分。
- **后续判别证据**：父层入口须从fresh home走到username可见与准确role的菜单入口；Write须同时检查UI缺席及server拒绝；Milestone对Issue/PR各有承接；代码搜索保留真实HTTP错误并走原UI链；People Owner页须实际打开；mutable scenario的起始对象/独立性须有可追溯配置。这里仅列证据缺口，没有启动任何新运行或修改。
- **审查记录**：本单元先读旧公开原文与旧结论，再接收新产物就绪通知；早期合并长输出出现展示截断，后续按节点范围补读。高影响发现边读边回传，最终只做一次覆盖核对；没有可靠独立计时，不把被审run时间当审查耗时。一次工具transport断开后用pwd确认恢复，未因此重做已读材料。
