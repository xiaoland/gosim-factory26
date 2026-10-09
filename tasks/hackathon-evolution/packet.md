# Hackathon Evolution 本地资料准备

## 目标、授权与当前状态

用户最新指示：“不要假定、建议我们后面使用哪个 variant / 基于哪个 variant 改进，没有数据之前，一切都是空话，我们大可能尝试多个 variants 做比较”；“必须尽快至少取得一次成绩”；“本会话不会开始做决赛，我们要做的是准备好资料、数据，整理好文档、指南在本地”。此指示覆盖此前的接入方案方向。本任务只整理本地资料，不选择或推荐 variant，不开展改进实现、注册、模型调用、评测、上传、删除提交或运行控制。

状态：资料准备已完成。原始包、完整离线基线、需求和参考图、来源证据及逐文件 manifest 均在 WorkSSD；规则原文、使用指南和调查已保存。当前没有待开工的决赛方案或运行计划。后续决赛执行另行建立/接续其任务包并取得具体授权，不要求用户在本资料会话选择 variant。

赛后状态（2026-10-09）：赛事已结束，平台已实际拒绝新 submission 和旧 submission 的新 run 启动。本 packet 关闭为历史资料入口；后文赛中授权、下一步和截止提醒不得用于继续执行。赛后保全与删除判断统一由[清理任务包](../post-competition-cleanup/packet.md)持有，原始 ZIP、完整基线、业务数据和 manifest 继续保留。

此前主 Agent 提出优先 minimal-vv，并采用 advisor 的路径建议，缺乏比较数据；这一选择建议已撤回。已有源码调查保留为中立兼容性事实，不能据基线生成者身份、接入成本或静态阅读对 variants 排序。

## 本地交付

长期规则与操作说明归 [决赛资料指南](../../docs/deployment/hackathon-evolution.md)，用户提供的 [通知原文](../../docs/references/hackathon-evolution-notice-20261006.md)保留为规则来源。[资料准备范围](design.md)记录本次决定，不再作为 Harness 实施方案。

数据目录为 `runs/hackathon-evolution/inquiry-20261006/`，由 Git 忽略，交接不能仅提供 Git commit：

- `requirements.zip` 和 `requirements/`：官方两题 YAML 与参考图。
- `initial-projects.zip` 和 `baseline/{github,sheet}/`：原始下载与完整离线基线，包括 SQLite/JSON 业务数据和原运行材料。
- `material-manifest.json`：3413 个成员的提取记录、逐文件哈希、两题需求身份与数据路径；原 ZIP 未修改。
- `competition.json`、`registration.json`、`preliminary-leaderboard.json`、`preliminary-submissions.json`：2026-10-06 官网只读快照。
- `github-source-comparison.json`、`sheet-source-comparison.json`：应用来源对照的具体范围与缺口。

官网任务为 `hackathon-evolution--github`、`hackathon-evolution--sheet`，各 5 修改、5 新增、30 个评测用例。基线对应初赛 submission `aea08b61772c`；GitHub 的 51 个 frontend/backend 文件与 Stage 3 `d86b43e8c891` 旧归档一致，但下载基线的数据库未由旧归档证明；Sheet 的 128 个 frontend/backend 文件与 `e53e7ab5ec79` 官方工作区一致。

2026-10-06 只读报名接口显示队长资格有效、尚未注册，初始预算 ¥200、剩余 null；页面正文为 ¥0，不能当可用余额。注册会变更队伍，未操作。该时点决赛 History 为 0，没有本会话创建的提交。

通知规定北京时间 2026-10-08 18:00 停止全部仍执行的容器，单次最长 24 小时。后续必须尽早取得成绩，不卡点提交，也不把截止停止当作可恢复暂停。最新有效正式提交仅需至少一题已有运行记录，后续提交可能替换已有成绩的提交；完整评分回执和最终采用提交须分别核对。

## 负责人及采用范围

| 负责人 | 已完成结果 | 证据入口 |
| --- | --- | --- |
| 主 Agent | 官方读取、规则原文、指南、导航、来源核对及任务整理 | 本 packet、docs/deployment/hackathon-evolution.md、数据目录 |
| evolution_harness_inquiry | 各入口的应用、交付、原生会话及工具路径只读调查 | [Harness 兼容性事实](harness-inquiry.md) |
| baseline_requirements_inquiry | 20 项演化行为的静态边界、完整基线提取与 manifest | [需求与基线调查](requirements-baseline-inquiry.md)、material-manifest.json |

源码/静态调查不证明实际 UI 已验收，不决定 variant 优劣。旧原生会话和自验记录仅保留来源，不读取隐藏评测实现，不将旧评分反馈用于定制新生成。未控制其它任务，也不改其授权和现场。

## 接续入口

后续会话先读决赛资料指南、原始需求和所属实验授权，再按实际数据比较候选。任何候选均需满足平台基线增量语义和新任务状态隔离；具体改动、矩阵、模型、费用及执行安排尚未决定。当前资料准备没有剩余执行事项，不自动进入决赛。


## 2026-10-08 基线选择核对与初赛正式补跑

用户先要求只读确认 github-evo 继承基线是否糟糕、删除初赛运行或新增参赛是否可改善；随后明确授权：“嗯...时间不多，你继续确认的同时，先将现在最新的 pi-minimal-vv 打包起来去运行 hackthon github 题和 github stage2 题（参赛）”。此指示新增两题正式参赛生成授权，不授权删除提交、重放代替参赛、其它题目或代改业务应用。

截至北京时间14:45，官网初赛 History 仍选择 `aea08b61772c`、progressive route；Stage1 `4eab9465931a` 16/30，Stage2 `32db20c04573` 0/29，Stage3 `d86b43e8c891` 0/41，Sheet `e53e7ab5ec79` 71/100。官网 Evolution 描述明确采用最新正式初赛排行榜提交选中的路线；progressive route 按Stage3→2→1取首个完整且完整性校验通过的制品，不按该stage通过率回退。Oct6基线51源码文件与d86一致，数据库没有旧归档对照。实时初赛仍标已归档，但保存/运行入口存在；实际能否受理参赛由本轮正常执行器调用核实，未用按钮可见替代授权或运行证据。

质量owner `baseline_quality` 返回 [质量核对](../../runs/hackathon-evolution/inquiry-20261006/github-baseline-quality.md)：原注册、组织及全局搜索有源码缺口；Stage2全局浏览器故障污染评分，Stage3主要导航/fixture入口失败并有一项测试脚本错误。初赛三stage曾并发启动，不能由分数序列推断正常顺序接续后退化。advisor `baseline_decision` 建议不以删除整份submission试探选择机制；这会影响Sheet且前一提交也是零分。

执行owner `hackathon_formal_launch` 负责当前最新pi-minimal-vv冻结包、正式费用模式、仅hackathon--github与hackathon--github-stage-2提交/启动及取证。主负责采用回执及基线机制核对；实时只读JSON保存在 `runs/hackathon-evolution/baseline-inquiry-20261008/`。新正式提交可能改变初赛整份排行榜身份及以后启动Evolution的两题来源；现有Evolution运行已注入的应用不追溯改变，本地Oct6副本也不会自动更新。

下一步：取得冻结包、submission及两run受理/实际启动事实，或保留具体HTTP门控原因。启动不等于完成、评分或新的完整基线。没有commit/push、删除、其它题或比赛控制授权。


本轮参赛准备与受理核实已结束，实际阻断已确认：最新包 `runs/pi-minimal/competition-20261008-formal-vv/pi-minimal-vv-latest.zip` 为180,571,670字节、SHA256 `4c0e55f08d24d786c349ebbbdc6fbb12bbff1165d3155b110ca262994a6b7b06`；执行owner只发出一次正常 `POST /submissions`，模式official_evaluation，模型glm-5.3-flash。北京时间14:51收到HTTP400，原文 `This competition is no longer accepting submissions`。未返回submission ID，因此GitHub原题及Stage2均未创建/启动；没有self-funded切换、删除或绕过门控。具体回执和制品输入见 [执行记录](../pi-minimal/competition-20261008-formal-vv/launch.md)。

当前结论：用最新包新建Hackathon正式提交改善EVO基线已被平台阻断；保留原提交，删除路径没有已证实的更好候选。没有自动启动其它题目或EVO。调查未重新下载今日完整基线ZIP，也未测试旧submission的Runremaining按钮。原始规则与Oct6基线证据保留；若后续选择改变EVO，应另行明确授权，不能把本轮两题初赛授权扩大。


用户随后明确授权：“那好吧，不接受新的提交，那么接不接受启动已经上传的提交的运行呢？让最新提交启动 github stage2 任务试试？”当前范围为核对最新已上传Hackathon submission并仅通过正常执行器尝试启动hackathon--github-stage-2；这不是上传被拒的新包，也不是应用重放。不重新上传、删除、运行其它题或绕过平台门控。由原执行owner hackathon_formal_launch续办，主不并发写官网；最新预期为aea08b61772c，实际以请求前读回为准。重复Stage2是否可启动与竞赛结束门控须取实际回执，不能由新提交HTTP400推导旧提交run请求一定被拒。结果续记原launch.md。


旧提交Stage2尝试已有实际回执：最新已上传submission仍aea08b61772c，Stage2默认来源4eab9465931a。正常POST /runs被接受，新run989c53d6deb2，创建回执official_evaluation；唯一POST /runs/989c53d6deb2/start返回HTTP409，`This competition is no longer accepting runs`。随后GET为PENDING且started_at=null；官网History仍列旧Stage2 32db20c04573。没有启动、生成或新评分，没有删除空PENDING记录。GET费用字段self_funded与创建回执不一致，保留原件，不擅自改写费用事实。来源和完整回执见原launch.md及runs/pi-minimal/competition-20261008-formal-vv/stage2-*.json。本轮新增授权已尝试到底并因明确门控结束，不再重试或绕过。
