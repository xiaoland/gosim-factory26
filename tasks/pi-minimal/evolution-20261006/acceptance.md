# Sheet 冻结应用验收

本验收属于已批准阶段 3，由 variant_inquiry 负责在两次本地生成后实际执行。只验收生成应用，不编写或运行 Factory/Braid 自身测试，不进行官网重放或评分。来源为官方 Evolution Sheet requirements.yaml（SHA256 7a2ee0a9d81317bcc3f92fd627effae0c510412b891ab6c79896c4517b139962）及其 reference；没有读取隐藏测试、历史评分或 rollout。本设计是观察合同，不承诺隐藏评分。

## 隔离、身份和证据

每个模型 run 先冻结完成的 application 及源码/业务数据 inventory、来源 commit、需求和基线身份。验收使用该冻结应用的独立副本及独立 backend DATA_DIR，不让 UI 操作、seed、构建结果或日志写回冻结交付或原始 baseline。验收根必须在 WorkSSD（远端执行允许存远端盘；Mac 回执仍在 WorkSSD）。开始前核对实际 DATA_DIR、frontend dist、监听端口与来源身份，不能只信环境变量；冻结交付验收前后哈希一致。

先启动原样完整数据副本，记录应用能否自己提供 YAML 所要求的 EVO workbook。缺少公开场景 seed 时记录“原样数据不满足公开场景前置条件；供应责任未证实”。YAML规定独立EVO前置数据，未明确由生成Agent随交付提供，官网是否注入也未验证，因此不能仅因缺seed判功能失败。可在另一份独立验收副本按公开GIVEN准备数据，再原样执行WHEN/THEN，标为“公开前置数据准备后的功能验收”，同时保留原样数据事实和准备证据；不将其冒称原样数据已满足前置条件。30 个官方公开场景各用其独立 EVO workbook，不能把多个场景合并到同一 workbook 造成命名/过滤/状态污染。现成数据可通过应用 UI/API/持久文件读取，但新增属性以已冻结应用真实格式适配，不预设新字段名，更不能修改实现。

基线 Sheet backend/data 有 102 个 JSON。Workbook 持久结构为 id/name/updatedAt/activeSheetId/sheets；sheet 为 id/name/cells/validations/filter/selection/pivot；cells 键为一基坐标 r:c、值为原始字符串/公式。Q3 Sales（q3sales）保留 Sheet1（sheet1）和 A1=Region。参考图 worksheet-overview/workbook-home 仅约束表格、公式栏、工作表页签和首页的可用结构；英文可访问名称、role 和结果按 YAML，不能把参考图中文菜单当验收名称。

每个观察保存操作、实际页面可访问名称/role、刷新前后值、必要截图、具体 HTTP 状态/响应和应用错误。缺入口、缺 seed、部署失败、功能失败、未执行分别记录，不能合并为零分；未经观察不填通过。每条的刷新必须等保存请求完成，避免把正在保存误判为持久失败。冻结两个模型使用同一观察集，不把第一轮应用或反馈悄悄变成第二轮输入。

## 十项增量的最小完整观察集

下表每项对应 YAML 三个公开场景（合计 30），不推测官方测试实现。详细 GIVEN 和操作以原 YAML 为准；表格列出不能漏掉的观察。

| 需求 | 必要实际观察 |
| --- | --- |
| REQ-1-2-2 Workbook rename | RENAME-OK：经 Rename workbook/Workbook name/Save，将带空格名字保存为 FY26 Procurement Ledger，编辑标题、首页链接、刷新后预填一致，F3=unreviewed。RENAME-DUP：evo-m01-archive-reserved 触发精确 Workbook name already exists，标题和字段仍 EVO-M01-RENAME-DUP。RENAME-LIMIT：81 字符触发 Workbook name must be 80 characters or fewer，刷新后原名和 C2=limit sentinel 保留。 |
| REQ-2-1-3 Worksheet rename | SHEET-OK：Worksheet options for HarborDraft → Rename，带空格输入保存为 Dispatch Register，活动 tab、刷新后预填和 D5=dock marker 保留。SHEET-DUP：ArchiveBay 改 meridian 拒绝，精确 Worksheet name already exists，原 tab 仍活动、字段保留。SHEET-LIMIT：51 字符触发 Worksheet name must be 50 characters or fewer，原 LengthGauge 和 G4=sheet sentinel 保留。 |
| REQ-3-1-1 Delete rectangle | CLEAR-TEXT：H4 Delete 后仍选中，格值和 Formula bar 均空、刷新持久。CLEAR-FORMULA：B7=13、C7=B7*5、D7=C7+2，清 C7 后公式原文空、D7=2。CLEAR-RANGE：H4:I5 四格全空且各 aria-selected=true，刷新全空。 |
| REQ-5-1-2 Filter views | FILTER-SAVE：D3:F7 两条件 Workstream contains Atlas、Load>20 后仅 row5 Atlas/Active/31 可见，Save filter view 为 Atlas active load，刷新仍存在且条件有效。FILTER-APPLY：选择预存 Queued lanes，三个 Queued 行可见、Active 行隐藏；管理界面保持打开且视图已选。FILTER-DELETE：空格/大小写 duplicate queued lanes 触发 Filter view name already exists且保存界面不关闭；选择并删除原视图后全部原顺序行恢复、值不变、刷新视图消失。 |
| REQ-5-2-1 Validation message | VALIDATION-FORMULA：J6=37，25..75 规则，公式栏输入88显示 Capacity must be from 25 to 75，值不变且刷新仍拒绝。VALIDATION-GRID：K8=Ready，Dropdown Ready/Holding/Released，格编辑Paused显示 Choose a queue state，值不变且刷新仍拒绝。VALIDATION-EDIT：L4=42，改 Error message 为 Allocate between 25 and 75 后输入24使用新文本，刷新重开字段相同。 |
| REQ-6-1-1 Freeze | FREEZE-ROW：选B1→View→Freeze rows through 1，精确状态按钮 Frozen rows: 1; columns: 0。FREEZE-COLUMN：A8→Freeze columns through A，0/1。FREEZE-BOTH：C4→Freeze panes at C4，3/2。三者刷新状态保持；实际纵横滚动观察相应行列固定且值/选择正常，区分只显示按钮与真实冻结。 |
| REQ-6-2-1 Find/replace | FIND-NEXT：A1起，E4/E7/E11=Cobalt，Find next 两次选E7且 Match 2 of 3。REPLACE-ALL：F3/F6/F9变Indigo，F12=Copper未改，Replaced 3 cells。CASE-SENSITIVE：G3 Cobalt→Azure，G4 cobalt、G5 Cobalt-7不改，Replaced 1 cells；替换刷新持久。 |
| REQ-7-1-1 Named ranges | NAMED-CREATE：CapacityPlan=ForecastModel!J3:J5，18/24/31，在L3输入=SUM(CapacityPlan)得73；对话框列名字，刷新公式原文保留。NAMED-INVALID：1stBatch触发 Named range must start with a letter，刷新无该条目。NAMED-UPDATE：MarginBase K2:K3（5/8）扩到K4=12，M2从13即时变25，刷新编辑Range准确且值25。 |
| REQ-7-2-1 Conditional formatting | FORMAT-NUMBER：J4:J6=11/29/46，Greater than25 Red fill，仅J5/J6 rgb(254,226,226)，刷新相同。FORMAT-TEXT：K4:K6 Watch/Stable/Elevated，contains Watch Yellow fill，仅K4 rgb(254,249,195)，刷新规则列存在。FORMAT-EDIT：L3:L5=16/28/39，Edit rule 1改Green，L4/L5 rgb(220,252,231)；Delete rule 1后三格无条件背景，刷新持久。 |
| REQ-8-1-1 Notes | NOTE-CREATE：D8 Manifest R41，Add note保存公开文本，Open note for D8打开精确文本，刷新保留。NOTE-EDIT：F6 Gate Rho，通过Open note/Edit note变Controller signed at 14:20，刷新保留。NOTE-DELETE：J3 Route Zeta，Delete note后Open note按钮不存在且刷新相同。三者 cell原值均不变。 |

## 受影响旧行为和数据保留

这些补充观察针对本轮共同保存/公式/批量操作边界，不扩展成全应用回归套件。使用另外的临时诊断 workbook，结果与公开 30 场景分开。

| 边界 | 最小观察与判定 |
| --- | --- |
| 原业务数据与未知字段 | 对原基线 102 个 workbook 按 id核对均存在，name、sheet id/name、原cell/公式、validations/filter/pivot等已有字段语义未丢失；新增字段允许。原未动文档逐文件哈希差异须解释，updatedAt变更单独列出，不能盲目豁免整文档变化。启动/浏览首页后再次核对，不能重新seed覆盖。独立验收副本向一个现有 workbook/root及sheet加入 sentinel未知字段，做一项改名或note保存后确认 sentinel与原cell保留；这只验证透传，绝不写原冻结应用。 |
| 保存失败/原命名边界 | 两种rename各观察空白拒绝的旧精确文本、last successful预填；80/50字符分别成功。对一个普通cell保存人为制造一次有界网络失败，观察明确错误、原值/原公式和依赖值未改；恢复网络后能正常保存。不得在冻结交付制造故障。 |
| 原输入、公式、取消 | 在临时sheet经grid/formula bar分别提交文本/数字和=B7*5、=C7+2，Enter或移到别格提交；Escape取消未提交值；改B7使直接/间接结果重算，刷新保留公式原文；Delete矩形外一格 sentinel 保留。 |
| Validation统一入口 | 自定义消息带空格保存后使用trim文本；分别经formula bar、grid、一次包含有效及无效target的paste、一次range move触发错误，四条路径使用同一消息且整个bulk原值不变。清空消息恢复标准错误，25和75允许；删除规则不改旧值、解除限制。标准文本按原YAML（特定0..100场景用from）。 |
| Filter源数据不被变异 | 视图隐藏行后CSV导出仍有全部源行；以同一区域SUM pivot仍含隐藏行，公开数字17+31+22+9=79。Clear filter/删视图恢复原顺序和原值，公式/validation仍有效。 |
| Find/replace范围与整值 | 未勾Match case时Cobalt与cobalt均匹配，Cobalt-7不匹配；另sheet相同文字不替换。增加公式显示值匹配，确认搜索按displayed value而非公式原文；replacement后依赖公式即时重算，受validation的invalid replace不能绕过旧bulk约束。 |
| 新元数据与sheet切换 | 保存freeze/named range/conditional rule/note后切换另sheet再回来及刷新，原sheet状态不丢；note/format动作不改cell或formula原文。worksheet改名后旧cell/活动身份保留；不为未明确的跨表命名规则构造额外评分断言。 |

## 采用标准

报告每个模型的部署结果、原样交付公开seed完整性、30个场景逐条观察及上述受影响边界。原样前置数据状态与准备公开GIVEN后的功能结果分别列出，不折算官方分数；semantic问题指实际业务结果违反公开合同，mechanical问题指启动、接线、入口/role、状态落盘或数据丢失等可定位缺陷。只凭HTTP 200或截图有菜单不判通过。应用验收发现问题后保留原冻结身份和失败证据，修复是否属于当前任务授权由owner依现有授权判定，不能直接改应用答案并冒称原Harness生成成功。
