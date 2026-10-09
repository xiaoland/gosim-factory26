# Evo GitHub 继承基线：功能债与输入决策

本页属于现有 Evolution 任务包，variant_inquiry 只读调查。授权范围是原始基线、公开需求及已保存生成轨迹，不修改应用、提示词或在途运行，不读取隐藏评测。原件与机器可复核差集见 `runs/hackathon-evolution/baseline-quality-inquiry-20261008/public-source-comparison.json`。

## 来源及公开契约

Oct6 官方 `initial-projects.zip` SHA256 为 `38c0457d9df5871d69604a53763b2514b9d6e1abde918364af2bc6a97fad8ba0`。本轮重新计算 GitHub frontend/backend 的52个文件（51源码/配置成员及database.db），全部与官方 material-manifest 相同。既有来源调查已证明51源码成员与本队初赛 Stage3 `d86b43e8c891` 相同；这不是所有选手共同使用的参考应用。数据库 integrity_check 为ok、foreign_key_check无错误，21张业务表226行，包含14用户、28会话、2仓库。数据库结构没有 organizations/teams，不能凭源码缺失假设另有运行时组织实现。

最新初赛普通 GitHub 公开需求的可用冻结原件是 `runs/deadline-20261003/local-five/overlays/requirements/requirements.yaml`，SHA `9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8`、172653字节，与 I13 新平台输入/I14冻结记录一致。其65节点、47 atomic、100 scenario；当前官方 Evo GitHub SHA `f1f73b4190831cef37669f9e919edde50cd0bc7ad02b888e6dab617094921754`、189231字节，70节点、52 atomic、114 scenario。

逐结构比较结果：所有旧65 ID保留；42个未修改atomic的description与scenario数组逐字相同；五个修改项 REQ-1-1-1、REQ-1-1-2、REQ-2-1-2、REQ-3-1、REQ-4-3-1 中，Original Feature Description逐字等于初赛description；所有共有folder描述也相同。新增5 ID为会话、审计、归档、release、reaction。变化是五项修改场景与新增场景，不是丢失旧契约。更早 `bdc17d…` 的292270字节版本虽然还在两份task证据中，但10/2已被平台大幅修订，不应把它当最新初赛需求带入。

## 四项影响最大的问题

### 1. 继承应用仅覆盖部分初赛能力，新增功能的前置模块也欠缺

`baseline/github/frontend/src/App.tsx:20-39`只有home/login、repo、issue、pull及branch rules。后端 `src/routes/auth.js:16-51`只有login/logout/me，`src/app.js:29-32`只挂auth/repos/issues/pulls。没有注册/恢复/密码设置、组织/团队、创建仓库、搜索、文件编辑/目录导航等入口。当前数据库也没有组织/团队表。

这不是把新增需求误称旧缺陷：初赛最新版 YAML 的 REQ-1-1-3（209行）、REQ-2-1-2（484行）、REQ-3-1（859行）、REQ-4-1（1192行）、REQ-4-4（1482行附近）已有这些功能契约，并且它们在 Evo 文件中保留。基线是按Stage3产物取回的部分实现；其功能不足不能以“沿用既有实现”合理化。会话/审计/搜索等增量分别依赖这些旧模块，局部加一个新按钮不能消除前置缺口。缺入口是源码/数据直接证据；本轮未运行完整浏览器验收，不宣称所有存在入口均可用。

### 2. 累积权限模型与公开操作权限相冲突，前后端均受影响

后端 `src/auth.js:5,77-78`以Read<Triage<Write<Maintain<Admin比较；前端 `src/auth.tsx:34`同样采用等级。`src/routes/issues.js:193,226,256,281,300`在assignee/label/milestone/close/reopen上要求至少triage；因此Write实际会通过并看到操作控件（`IssueDetailPage.tsx:38,100,125-168`）。而最新初赛及Evo REQ-5模块、REQ-5-3、REQ-5-4明确只允许Triage/Maintain/Admin，Write只能查看这些管理状态；Evo YAML 1748、2023-2033、2130行可直接核对。

这是一条确定的继承授权缺陷，而不是仅命名差异。若新增组织授予Write或归档门禁仍复用该helper，会扩散到新业务。最小方向是修正现有权限模块按操作允许角色集合判断，并核对相关UI/服务端入口；不预先要求新权限框架，也不宜在错误等级上无限追加例外。组织Owner如何映射Admin也需与实际组织关系统一，现有repoPermission只查个人collaborators后回退public read（69-74行），没有组织/team解析。

### 3. 旧初始化策略不能承担增量GIVEN与迁移，Ready也不证明准备完成

`src/database/seed_db.js:68-71`在任意users记录存在时直接返回。原始注入数据库有14用户与2仓库，因此它不会补充任何缺失seed；初赛REQ-4-4已要求的file-management-demo/file-contributor（旧YAML1482-1505行）就不在现有2仓库/14用户中。EVO账号缺失本身是增量输入前置未落实，不单独算旧bug，但沿用旧seed策略必然不能补上它。

`src/app.js:18-22`异步初始化/seed不被 `index.js:5` 的listen等待，health route25-27行无条件Ready。故干净验收副本或新增迁移可能在Ready之后仍初始化中；这是继承代码的准备竞态，实际竞态发生率尚未在本轮实测。schema使用CREATE TABLE IF NOT EXISTS，已有表不会因改create定义自动多列。需要可重复且逐记录补缺的增量准备、显式迁移与真实启动就绪边界；不能靠删库、统一改旧用户密码或重建所有seed来消除错误。保留原行、未知列、关系和历史会话，公开GIVEN只补缺状态。

### 4. 已有多步写操作不是完整原子边界，不能只沿用CRUD

`src/routes/issues.js:101-108`创建issue后另增counter、写event；修改title/description、comment、metadata也分开更新主体、活动和updated_at（153-161、179-181、267-269行）。公开原/新REQ-5-2-1要求失败不分配编号或留下部分数据。若第二步失败，可留主体而无counter/event；并发编号读取也可能冲突。原数据库当前counter与max一致，尚无证据其现有业务已损坏；此处是确定的非原子实现和可推导失败风险，不假称已经复现数据丢失。

已有 `db_runtime.js:84-105`提供事务，PR创建/merge部分采用，但单连接事务helper没有排队，普通run/get/all也不受事务作用域约束。扩大新写入模块前，应按实际互斥/连接策略核清事务边界，而不是机械地给各route包BEGIN。原数据可迁移，旧读模型、issue/PR共享对象及commit/file snapshot仍可复用，不需要全项目重写。

## 与后续Agent引入问题分开

I15实现中曾发生 RepoPage 对DirEntry不存在content调用split。原基线RepoPage.tsx:18,21声明所有返回项均是含content的文件；后端branches/files直接返回file_blobs（repos.js:91-109），原基线没有DirEntry混合树。这一崩溃是增量引入目录模型后未同步消费方，不应反推原始包已有同一崩溃。后续新Header缺React/useState等也需要新旧字节证据，不能概括为原基线质量。I15组织筛选自验失败、reviewer并发同库干扰均不是本轮原基线运行反馈。

## 已授权的最小提示及输入方案

建议不默认附加完整初赛YAML：本轮已证当前官方输入保留全部旧功能契约；再加172KB重复正文不会补缺，却增加重复上下文和旧/新场景优先级风险。旧YAML作为开发侧来源证据保留即可。正式/本地生产者仍冻结官方YAML及参考图原字节，与bench附加材料身份分开。

以下长段保留方案讨论的义务展开；用户已授权采用末段的最小表述，实际内容归 `materials/bench-contexts/hackathon-evolution/task-context.md`，不将本调查的具体缺陷注入生成Agent：

> 注入的应用是必须继承的业务与功能基线，不代表已有实现满足全部当前公开requirements。读取当前YAML中未修改功能及Original/Modified描述，确认共享入口与依赖能力；修改项以Modified描述和当前场景为准。允许为满足这些公开契约重构或替换必要模块，不要求保留原内部实现；保留已有可用功能、业务记录、身份/关系、历史与未知字段，采用增量迁移，禁止清空数据库或整体覆盖输出。先核旧能力与新增功能的前置缺口，按共享模块规划改动，在独立副本验证完整用户路径、权限拒绝与持久化；交付保持公开初态，不把自验副作用留在业务数据中。

这段处理的是“保存业务不等于冻结坏实现”的误解，不承诺仅靠新增提示能根治任务划分或验收信息转换。没有建议新角色、解释器、预置答案或付费重跑；具体模块替换边界仍由生成Agent依据现场和公开要求判断。

侧advisor仅核模块替换边界（旧YAML价值归主线advisor）：这些证据支持允许必要模块重构/替换，不支持整体重写或启动前统一修复全部旧写路径。seed补缺沿用现有bench约定，事务仅在相关业务修改处形成完整边界，不新增通用迁移/补偿设施。主线提出的最小句更合适：“先理解既有组件、接口与存储格式；为满足本次需求，可以重构或替换必要模块，不要求保留有缺陷的实现，仍须保留要求继续支持的功能与业务数据。”本页长段是供讨论的义务展开，不必全加入prompt。

本轮尚未量化基线缺陷造成的模型token/耗时贡献，不能用I15后续自验轮数推算原基线修补成本。已证事实足以说明共享错误会被复用、增量前置模块缺失、旧初始化不能补数据，以及原子边界需修正；是否显式许可能减少绕弯，仍须未来获授权运行行为验证。调查已收敛，不继续全仓审计或运行模型。

用户随后明确“同意这个改进建议，请落地。（不重启官网，但是接续本地）”。bench已落地必要模块重构/替换许可、功能与数据保留边界，以及GitHub当前YAML的未改功能与Original/Modified优先关系；官方YAML原样，不额外带入初赛YAML。实际本地GitHub接续身份和消费证据由主packet及所属执行器回执维护，官网冻结版本不改变。
