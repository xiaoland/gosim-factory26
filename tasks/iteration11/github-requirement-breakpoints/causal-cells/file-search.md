# 文件搜索终点：需求解释与验收替代链

2026-09-30；只读结果因果调查；对象为 I11 GitHub final replay `e68661975b53`，直接生成 lineage `20260929-042409-1202e245`。沿用[终态断点](../cells/repo-content.md)与最终184文件身份核验。本轮只补原始需求→实际输入→选择→实现→交接/验收→最终整合的形成链，不重跑应用、测试、评测或模型，不改实现/工作项，不读 Sheet。

**filename link缺失有直接代码证据，complete-text覆盖判断有直接选择证据。** M4b 的负责人和原生 advisor 直接看到了原句，却先后把“文件页存在/显示全文”当作“打开 README 后完整 query 文本值与刷新后 filename link 已覆盖”的证据。M4a 的实际验收证明了另一组属性：整个存储文本正确、分支/路径/内容保持、父目录可返回。M4b 没有重新核实它是否证明了自己新增的终点条件。其搜索自验又只打开 `src/search.ts` 并检查 substring，给这个替代判断提供了可通过的验收闭环。filename末级span使link义务不成立是强断点；`complete text value`是否要求query自身成为独立完整文本观察，保留为较谨慎的解释风险，不能单凭HTML节点形状断言官方判据失败。

这比“没读需求”“描述过长”或“仅 near-match 不滚动”更具体。near-match 的解释收窄是旁证；缺 filename link 和独立 query 文本值的主链，是**不同属性之间的证据误代和依赖组件覆盖假定**。没有逐例官网结果，不能据此断言分数影响。

## 原需求含父层，以及当时实际可见范围

`F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`；`Q` = F 内 `requirements/requirements.yaml`。`E` = `runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`。下文 native 物理行以[完整定位/原始记录摘录](file-search-evidence.json)的 `source` + `line` 为准；同 basename 的顶层压缩记录和 `sessions/` 完整记录不互换行号。DB 评论见[只读评论摘录](file-search-comments.json)，含 comment ID、Issue/PR、created_at、原文与生命周期。原 DB 连同 WAL/SHM 复制到 `/tmp/i11-file-search-db/` 后以 `mode=ro` 查询。

| 层级 | 原始义务 | 与本缺口的关系 |
|---|---|---|
| ROOT，Q:5–22 | atomic 的 role/scope/observable state 权威，seed 预先建立，原子需求保持启用 | 不能用场景摘要或既有验收名称替换 atomic 的具体状态要求。ROOT 对 quoted control 的 exact accessible name 规则与 atomic 的 filename link 同时适用。 |
| REQ-4，Q:1596–1618 | 文件只读；每个文件/commit/comparison/branch页显示仓库与branch/revision；public访客可读；默认每个named control全页唯一 | 文件搜索终点必须继续保持原内容上下文，而非只有导航成功。 |
| REQ-4-2，Q:1661–1670 | code search仅当前仓库可读内容；三视图只读，复用REQ-4-1对象且上下文变化后保持一致 | 依赖关系说明复用对象，未说明M4a已满足后来的所有搜索终点判据。 |
| REQ-4-1，Q:1626、1646–1654 | directory/file **entries**为exact name links；文件显示完整存储文本，刷新保持branch/path/content，面包屑可回父目录 | 此处未单独承诺文件页末级filename自链接；不能把“REQ-4-1已验”扩展成REQ-4-2-3终点已验。 |
| REQ-4-2-3，Q:1754 | query `search flow`；匹配文件README.md；query可见为complete text value；打开文件显示该文本；刷新保留上下文、文本及exact filename link | 两个本轮目标是成功搜索→打开README→刷新后的可观察终点，不只是结果列表filename链接或全文含substring。 |
| 场景1，Q:1765–1785 | default branch两个匹配文件，其中一个在src/；path过滤后点击结果，near match；清过滤不跨仓库、不写内容 | src/场景不能替代description中未过滤README旅程。场景2的scope/filter保留曾被真实修复，见反证。 |

**当时可见，不等于现在文件存在。** 根初始 `sessions/…04-24-34…` L9 `de1d8ff4`（04:24:54）读取 `head -c 3000 requirements.yaml`，ROOT原文进入实际返回；L12 `4d03fd07`（04:25:23）用 `if node['type']=='ATOMIC'` 生成 `/tmp/reqs_flat.md`，该平铺读视图不包含REQ-4、REQ-4-2父FOLDER正文；L19 `57699230`（04:25:35）实际读取flat offset390/limit250，**包含完整REQ-4-2-3原句**，不是只给场景摘要。不能据一个flat视图推根全程从未读父层。

M4b 初始 provider 用户消息 `sessions/…11-08-29…` L4 `d19dc484`（11:08:30）是Issue7本项正文与可见讨论，Parent只有Issue1指针；它携带root摘要、M4a branches/内容合同及已合入证据，不自动递归含父Issue/需求FOLDER全文。L16调用按wanted atomic IDs抽JSON，L17 `ebaace61`（11:08:42）返回REQ-4-1、REQ-4-2-3及branch/editor原文；这份返回没有ROOT/REQ-4/REQ-4-2 FOLDER正文，但本调查所需的两个明确终点条件都在返回中。11:14原生advisor实际读取Q原文（`ab011700` L10），同样看到这句话。没有证据能把后来的误判归于此句被截断或工具不可得。

## 形成链：第一次代码、解释、交接与验收

| 时间 / 工作项 | 当时输入 → 实际选择 → 结果 | 物理来源 |
|---|---|---|
| 04:33:51，根Issue1拆M4a/M4b，创建Issue6/7 | 已读atomic原文。M4a摘要写“完整存储内容、最近commit、文件名；刷新保持分支/路径/内容”；M4b摘要写“结果链接名=文件名、Search→Code、snippet/过滤/空态”。**没有将打开README的完整query值及刷新后filename link逐项登记在任何一边的交付摘要**，仍保留原需求入口。形成了后续依赖假定的条件；这不证明遗漏不可修复。 | root顶层 `…04-24-34…` L31 `7b7e8f87`，实际写入 `/tmp/issues/m4a.md`、`m4b.md` 并创建工作项。 |
| 05:31:34，M3 / PR11，README seed第一次明确代码引入 | 按root seed“README含search flow”与M3资产对象实施。`ACME_DOCS_TREES.searching['README.md']`写为整个markdown段落：`# acme-docs\n\nThis repository documents the **search flow** of the platform.\n`。query是段落内子串，未建立独立query文本节点；属于最早找到的代码来源，不宣称当时M3主动否定了尚归M4b的搜索终点。 | `…05-26-59…` L23 `4b3cf093`，write seed/repos.js；其当时本项输入为同session `sessions/` L4 `f055f605`，REQ-3范围与父指针。 |
| 05:38:39–42，M3 / PR11，file页filename span第一次引入 | M3为REQ-3-3“overview点filename进file页”提供只读最小内容页。L155首次write即将末级breadcrumb写为span；L157明确说末级file“render plain text”，目录末级link to itself，并以简化breadcrumb逻辑实施。全文使用单个`pre code`直接显示存储内容。**不是后期集成误删链接**。 | `…05-26-59…` L155 `992fcbed`、L157 `4c80f7ed`。同write注释明确Code/历史/diff/branch/editor交REQ-4。 |
| 05:42–07:07，M3→M4a / Issue6、PR16 | M3 #33/#35与root #42/#44/#84交接只读contents/blob/tree，登记完整Code能力归M4a；具体需修的既有近似为last-touch commit与空branch。M4a provider输入要求完整存储内容、filename显示与父目录返回。M4a设计packet将REQ-4-1/4-2-1/4-2-2列范围；PR16实际read整个旧RepositoryContentsPage，返回含filename span与全文code；后续仅接入branch/Commits等，沿用两个渲染选择。没有找到M4a对REQ-4-2-3后置filename link/query exact value的承接声明。 | `ea0c5a6a` 完整sessions L4（06:51:32）；M4a顶层packet write L29 `e6106536`（06:55:09）、L62 `3cc630e2`（07:05:45）；PR16 L24 `1f716797`（07:07:51）发read、L25返回；L162 `204c37df` / L163成功回包 `a3949bb5`（07:28:03）扩展页面；前一次L156 `dc250a91`请求失败（L157 `24291879`），不算应用成功。L164 `c51dd7ad`（07:28:08）又明确“REQ-4-1 wants file name…breadcrumb last segment. OK”，印证其只判断filename显示。DB #33/#35/#42/#44/#84/#91。 |
| 07:51–08:30，M4a / PR16，README全文自验形成 | 设计侧#125发现PR正文“README完整文本值”而实际只验guide/src，允许“补README全文”或“改措辞”。实施选择前者：直接开README，用`pre code.toHaveText(整个markdown段落)`；没有独立`search flow` exact文本判据，也没reload README后filename link判据。#150明确该新增是**REQ-4-1对齐**。 | DB #125（07:51:35）、#150（08:29:58）；PR16 L569 `b96858c7`（08:22:28）完整edit参数。 |
| 09:27–28，M4a验收/合入 | #196把README完整存储文本逐字、父目录返回、branch/path refresh列为已覆盖；#197 head `c33e8ee`→develop merge `4a8f3c9`，组合树身份核对；#198关闭Issue6。这些属性有真实检查，不是虚报；只是未提供M4b后置两个属性的证据。 | DB #196/#197/#198；最终F/e2e/content.spec.ts:49–71、83–104仍分别验全文、branch/path、唯一Commits。 |
| 11:13，M4b / Issue7设计初次near-match解释 | 主设计者看到完整file全文节点与原文，考虑分行anchor/highlight，担心改M4a渲染使“complete text value”断言受影响，并认为grader可能只看文件打开/内容可见，决定保持blob全文导航。不将这一anchor决定等同两个本轮缺口的直接修复。 | `…11-08-29…` 顶层L9 `a67442a8`（11:13:07）；记录保留整段候选/放弃理由。 |
| 11:22–25，M4b原生advisor独立复核 | advisor实际读Q、现有实现/seed；`c3e65a02`将“complete text value”判为“README contains literal search flow”；`21775e48`完整引用“refreshing…a link named exactly after the file”，紧接“blob page for README.md on main ✓ exists (M4a)”。**第一次找到明确将contains/existence当满足两个终点要求的解释记录**。它给出scope、reload query回填等有效反例，但此项使用了错误替代判据。 | `…11-08-29…/3c3e53c9-f18d-4882-86e9-3a16ee6b3715/run-0/session.jsonl` L36 `c3e65a02`（11:22:30）、L40 `21775e48`（11:25:21）；L10 `ab011700`为Q实际返回，L12 `bc0525b6`为后续材料返回。 |
| 11:29–44，Issue7→PR19实现/自验 | 设计按已发布合同交PR19实施。新`code-search.spec.ts`：结果列表确有README.md/search.ts exact links；path=src/后**点击src/search.ts**，只验URL与`pre code`包含`searchRepositories`；query则在结果snippet用`toContainText('search flow')`；刷新断言用于absent query的搜索页。原需求README成功终点两个属性未进入判据。 | PR19 `…11-29-23…` L243 `c9d32ef0`（11:44:14）完整write；后续head包含`5d7e0dc`自验提交。 |
| 11:54–55，M4b再次读原文 | `aa0542bf`真正识别结果页重搜scope/filter丢失，#264明确请求实施owner修；同轮`3e1b918e`讨论near-match，引用“shows that text”并猜测grader不检查scroll，决定“不请求change”，Issue7风险7写“若评估者要求anchor需另开M4a”。登记风险没有建立对应接手人/关闭门。 | `…11-52-26…` L43 `aa0542bf`（11:54:20）、L67 `3e1b918e`（11:55:14）、L68回包`4e2122bf`；DB #264。 |
| **11:58–59，M4b设计侧主动复查具体两句** | `f24f8ddf`明确意识到需求README query“visible as a complete text value”，也承认自验打开src；随即以“content.spec.ts already asserts README full text verbatim (M4a)…Fine”关闭疑问；刷新filename link单独写“M4a covers”。`e147aaa3`再次在REQ-4-2-3清单把此项归M4a。**此时不是未读到义务，而是主动选择以M4a的另一属性代证，未读回/实操filename link。** | `…11-57-12…` L45 `f24f8ddf`（11:58:59）、L49 `e147aaa3`（11:59:25）；前面L36 `6a677b8f`已返回真实code-search.spec自验。 |
| 12:04–15:10，PR19补齐门、独立复跑、合入 | #273要求补重搜scope/filter、唯一Search、分支无写/重名、Edit rename；没有两项README终点。#274/#276落实并独立复跑，head `56f53ae`；#278合入develop `4eb2a27`，#279关闭Issue7、#280报根。移交M6a的义务是seed/共享计数/status/migration与最终整合，没有转交filename/query终点。 | DB #273/#274/#275/#276/#278/#279/#280；`…14-47-50…` L80 `89cf1893`（15:07:26）设计侧验收发布。 |
| 15:38、16:08，后继接口维护 | M4b owner核M6a rebase，确认code-*自验及自己的准则保持不变，因main搜索seed未改而沿用证据。这是防破坏的维护，不是重新解释README旅程。 | `…15-37-55…` L21 `1cdb04ab`（15:38:33）；`…16-07-59…` L12 `44561c53`（16:08:20）。 |
| 09-30 02:03–04，PR23整合 | 当前输入要求完整需求最终验收。`fa9e3624`选择existing acceptance plan/spec已有mapping，“I don't need to re-derive each mapping”；`45506478`一度考虑读模块原文，因已确认ID引用而结束。没有针对本两项的反例反馈/承接；后续通用收口由主线审查。它延续先前未含本两项的验收主体。 | `…02-02-19…` L48 `fa9e3624`（02:03:59）、L71 `45506478`（02:04:53）；[主线完整PR23链](../../braid-context-methodology/final-pr23-flow.md)。 |

## 终态、反证与因果边界

最终F/frontend/src/features/repo/RepositoryContentsPage.tsx:96–97仍对末级filename渲染span；137–138仍以单个`code`原样显示整个存储文本；F/backend/src/seed/repos.js:54仍是含`**search flow**`的markdown段落。F/e2e/code-search.spec.ts:40–57保留结果列表链接、src点击与substring断言。README的成功搜索→打开→reload→exact filename link与完整query值都未进入自验。filename link缺失在M3最小页已有、经M4a被继承；query自身完整文本值按该句较严格解释存在呈现差距，但需求未限定DOM节点形状，运行/官方判据未证。M4b明确接到两句后都以替代证据判为覆盖，最后沿既有判据集成；不是PR23才首次创造，亦非应用/API不可读取文件。

反证需同时保留：

- code search具备repository权限、default tree、exact result links、scope、path/language filters与无结果态，文件API真实接入；不能推广为所有搜索或文件浏览失败。
- #264→#273→#274→#276真实修复并核验search结果页再次查询的scope/filter问题、唯一Search。原文阅读与跨项反馈在同一负责人处能有效工作，不能说其一概只猜grader。
- M4a设计侧曾发现候选基线不对应、私有commit diff缺自验、README全文措辞不对应，并要求补齐；这是真实审阅。错误在把其证明范围外推，不是否定M4a全部验收。
- advisor有独立原生调用、实际读材料与有效反例。重复独立执行也可能复用同一解释；“有advisor”不自动证明每项判据重新核实。
- 原需求入口并未消失，M4b实际直接读取完整atomic两次以上。root摘要丢细节是促成条件；它不能单独解释后继明文可见仍缩义。
- 没有观察到官方逐例失败或实际DOM locator执行。本轮确证的是代码结构和原生选择链；整个README显示与“query自身完整文本值可见”并非同一个已验属性；后者的严格文本观察不在现有判据中，运行行为/评分关联仍未实证。没有把near-match无anchor提升为独立评分失败。

**一般可改变因素**：交接/审阅需对依赖组件的新增消费条件逐项核实，不能以组件存在、该模块通过、全文包含代替角色/精确值/刷新终点。同样，“风险已登记”不等于义务已承接。此链优先属于需求解释与验证证据适用边界的方法，未发现工具读取/截断导致这句不可见的机制缺陷。不建议将题目README或filename需求硬编码进Harness。

## 覆盖与缺证

本cell覆盖ROOT拆分/初始读视图、M3 seed与file页首次write、M3→M4a合同、M4a文件页继承与README断言来源、M4b初始provider/直接原文返回、原生advisor相关判断、M4b设计/风险/主动复查、自验首次写入、PR19相关反馈/验收/合入、后继M6a接口维护、PR23本缺口定向承接。对已有索引全局关键词定位后只回读与本链有关的输入、选择和回包；未声明所有native整段或应用全量语义审查。长输出截断部分以定位后的对应段补读；摘录文件保存完整原始record，不意味着record内所有其它需求已审读。

未发现这两项终点的明确反馈、M4a补修请求或他人承接；该否定仅限已得终态native与DB的定向检索/回读。未取得独立provider request payload文件（E内无单独contexts目录），使用真实native用户输入/工具返回；不能量化模型注意力或证明从未考虑某句。PR23的通用覆盖/关闭不在本cell重新全面审查。无新实验/运行授权且用户要求只读，因此运行与逐例评分缺证保留，不追加试跑。
