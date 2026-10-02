# 首页唯一入口与个人仓库菜单：因果链

2026-09-30，只读调查。对象沿主报告已冻结的 I11 GitHub replay `e68661975b53`，不是前史的另一应用。未运行应用、测试、模型、评测，未改实现和工作项。DB 从 `runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/braid-state/braid.sqlite3` 连同存在的 WAL/SHM 复制至 `/tmp/entry-navigation.sqlite3`，以 `mode=ro` 查询。根目录 0 字节同名文件未使用。

**两条链不能合并为“没看需求”。首页重复最初是 shell/body 的组合决定，最初需求阅读还漏投影了 REQ-6 父层；晚期 M6 真正读到唯一入口要求后，既有登录 helper 仍绕开该入口。仓库菜单则在 M3 实现者已经明确发现死端时，因 Issue 范围、路由所有权及冲突顾虑选择另建 owner 列表；残余菜单没有明确转交，M1 同时把它留给“later modules”，最终结构复核还要求保留该占位路由。** 后续 PASS 真实，但覆盖的是较弱、不同入口的行为。

## 来源与定位约定

- `E` = `runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`。
- `F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`；`Q` = `F/requirements/requirements.yaml`。
- 原生行指 JSONL 的**物理行**，不是工具返回源码的行。下面的短文件名与 ID 可以在 [原生摘录](entry-navigation-native-excerpts.json) 中查到完整路径、时间、输入和返回；主要决定原文未压缩。
- `R` = root `2026-09-29T04-24-34-972Z_01a0eb68-479c-72ef-b9ea-288545453828.jsonl` 的 `sessions/--workspace-template-…-issue-1-pi-glm-fast-g1--/` 副本。`B` = foundation `2026-09-29T04-32-05-558Z_01a0eb6f-27b6-73dd-bf27-c93fdba8117b.jsonl`。`P3` = M3 `2026-09-29T05-26-59-511Z_01a0eba1-6ab7-7751-8a0a-e84a52a71f95.jsonl`；同 basename 有阶段副本，按摘录记录的完整路径与消息 ID 识别。`P1` = M1 `2026-09-29T05-33-27-670Z_01a0eba7-56f6-754f-8ecb-752e8af84bd8.jsonl`。
- DB 评论 `#n` 指 `local_comments.comment_id=n`，不是 Issue 号；工作项、时间、全文见 [评论摘录](entry-navigation-comments.json)。索引扫描仅用于找断点，不能等同全文审读；[定向检索索引](entry-navigation-search-index.json) 保留定位与匹配片段。

## 需求与 provider 实际可见性

ROOT（Q:5–20）规定英文 accessible name、角色/范围/可观察状态与原子操作的权威性；REQ-1 父层 Q:28–40 描述首页进入账号功能。REQ-6 **父层** Q:2830–2841 则明确所有 REQ-6 interaction contracts、各 named control 的唯一性，以及 signed-in scenarios 从首页 **unique Sign in link** 开始。因此只核登录表单 button 唯一不够。

REQ-3 父层 Q:1130–1144 给出 search、个人/组织 Repositories list、direct link 三类仓库入口及统一可见性；创建/fork 场景又要求新对象出现在 target owner's repository list（Q:1300 后、1400 后）。它没有规定列表必须由名为 Your repositories 的菜单入口唯一到达。因此本报告确认菜单死端和能力未接线，**不将其提升为所有 REQ-3 失败或列表功能完全缺失**。

| 阶段、provider session | 指令/context 注入与 read 返回分开核对 | 对本断点能证明什么 |
|---|---|---|
| Root 04:24，Braid session `01a0eb68-47cb-7783-8f43-883a64e5f1ec` | R L8–9 `800b156e/de1d8ff4` 用 `head -c 3000 requirements.yaml`：返回 ROOT 与开头；L12 `4d03fd07` 用 Python `if node['type']=='ATOMIC'` 才写 description/scenarios 至 `/tmp/reqs_flat.md`，仍递归 children；L13 `8ef1ff65` 回执 876 行。L14/16/18/20/22 (`7be95e70/785accbb/01761bdb/e9ae717c/e3a4b6fc`) 读该 flat 并补截断。 | 补读确实补齐了 **flat 的 ATOMIC 后半**；脚本没有输出 FOLDER description，故不能由它声称 REQ-6 父层已读。ROOT 另有真实返回，不应一概称全部父层不可见。程序读取 YAML 全树不等于模型收到所有父层正文。 |
| Foundation PR2 04:32，session `01a0eb6f-27d6-74b0-8581-8ec2d7554006` | B L4 `1807c34d` 的真实user消息与初始 `physical/01a0eb6f-2432-7a13-8aae-17647ccea592/context.md`（另有历史已提取副本 `braid-context-methodology/evidence/earliest-pr2-context.md`）实际展开 root Issue1 正文及 PR2，不嵌整份原需求。root指令要求覆盖全部需求、不得以摘要替代；PR2又限定业务只留占位。B L13 `8a1efb75` 真正返回 architecture §7 的 shell Sign in/Sign up；L25 `148046b4` 返回原始 YAML 开头60行，含ROOT/REQ1父层；L28–31读REQ1登出/改密及注册/登录区间。 | 原始 REQ-1 父层已可见；REQ-6 唯一首页入口未在这些返回中。最初错误不能定性为明知 REQ-6 唯一要求仍违背，但重复组合本身后来实际显示给模型。 |
| M3 PR11 05:27，session `01a0eba1-6adf-7eb1-8a9f-95f5c78d09c6` | `physical/01a0eba1-673c-71f3-a979-3845b2afd77b/context.md`（context_revision `898e40…`）与P3 sessions L4 `f055f605`真实user消息一致，展开 Issue5正文、#17/#20 和 PR11；Parent Issue1是关系指针，不递归展开其正文。Issue5仅列6项 atomic、交付列表和共享文档；#20路由没列个人菜单页。P3 sessions副本 L21 `a8488945` read offset1126 limit490，L22 `2a2576b5`真实返回覆盖REQ3父层及创建/fork场景；sessions L33 `30b44cea` 返回 AccountMenu源码，含 `/settings/repositories`。 | 父层原文、场景列表观察和当前菜单代码都能到达，且后续推理确实消费。这里不能归因为父层被系统完全隔绝。Issue局部清单相较原文少了个人列表入口是可核对的边界。 |
| M1 PR12 05:33，session `01a0eba7-572d-7ca0-8f4c-055c91fa3816` | `physical/01a0eba7-5173-71b0-86ef-6d2d6beb3695/context.md`（revision `21e0c2…`）与P1 L4 `1fad95aa`真实user消息一致，包含M1身份scope、设计与交付，不含M3后来的残余菜单裁决（未发现这种交接）。P1 L60/L67清楚提到现有菜单路径并自主判断organizations/repositories超M1 scope。 | 看见链接/占位存在，不等于接手仓库列表；不能由 foundation“移交/settings/*”笼统语句推得M1明示承接个人仓库功能。 |
| M6a Issue9 11:09、PR20 11:32；M6b Issue10 16:10 | Issue9 `…11-08-33…f010` sessions L16/17 `19a2c73d/b4a76626` sed2801–3060，返回 **unique Sign in**；PR20 `…11-30-03…f6d8e` L70 `0b8d33f1`明确解析REQ6.description，L72 `c6aed31b`返回完整 REQ6父层（toolCallId `call_01_NMc9LSzPSpsPD0yVcn1B2044`）。M6b `…16-09-22…a7401` sessions L65/66 `07cae554/7711770e` read2801 limit50，同样返回unique正文。 | 后期至少三个工作会话的实际工具返回使唯一入口可见；这与初始flat遗漏是不同阶段。不能继续用“父层从未进过上下文”解释晚期不纠正。 |

这些物理context保存的是一次创建时的工作项投影，native read保存的是模型收到的工具结果；二者都不等于逐个 provider HTTP 请求隐藏字段或当时注意力。正文出现能证可见，不能单凭出现证理解。

## 链 A：首页 Sign in 重复

| 时间（UTC）、原文位置、工作项 | 输入 → 选择/动作 → 结果/后继消费 |
|---|---|
| 09-29 04:33:32，B L46 `8c325b34`，PR2 | 已读REQ1父层的“首页Sign up/Sign in/Forgot password”。实施者提出找首页相关需求，但以foundation仅需AppShell+placeholder为界，决定Home显示Sign in/Sign up。不是已证完成了额外REQ6查找。 |
| 04:36:04，B L95 `5cad06b9`，PR2 | 明说 **“AppShell already renders both in the header”**，仍将HomePage的相同links视为“Fine”。这直接定位到组合解释，不能解释为独立开发两组件时完全不知道另一组件存在。 |
| 04:36:48–04:37:09，B L121 `78775a08`、L124/125 `f02e534b/47acb209`、L133 `c06e6125` | AppShell先写signed-out Sign in link；HomePage后写同名link且回执成功；App将 `<AppShell>{routes}</AppShell>` 组合，Home route仍在里面。首页两个live link的代码引入点因此可前溯到PR2。 |
| 04:37:37，B L146 `95664629`，PR2 | 同批写自验：registerAccount直达`/register`、signIn直达`/login`；session断言采用 `getByRole('link',{name:signIn}).first()`（包括登出后首页）。检查的是真实会话闭环，不检查首页唯一入口。未发现先发生locator严格失败再用first掩盖的证据；first是在初建判据时已有。 |
| 04:48:34–04:48:46，B L316–319 `43e2b1e7/815222fd/d6bdb327/b9eb1a77`，PR2 | agent-browser打开首页；**实际 snapshot** 返回link Sign in `e7`与`e4`、Sign up `e8`与`e5`。接着模型点击特定ref `@e7`进入登录页，得到表单snapshot。反馈证明重复真的渲染，点击ref又能成功；没有以name唯一选入口。此历史运行证据不能当最终版本DOM实证，但排除“重复只是死源码”的最初形成解释。 |
| 04:50–05:09，DB #6/#16/#17，PR2→M1/M3 | foundation报38/5全绿和真实浏览器控件role/name吻合，交回注册登录登出并将password-reset/settings移交；根合入`c338578`，两个模块复用AppShell/AccountMenu。未交回首页重复或唯一性风险。 |
| 05:32:55，P3 L39 `e1cdbb74`；05:37:02 L129 `3448f0b1`，PR11 | M3改shell加New repository时明确观察session用 `.first()`、判 unaffected；写repo检查时认为Home也有Sign in/Sign up“Fine”。后继不是毫无看见组合代码，仍沿既有局部判据。 |
| 11:09/11:32/16:10，上表M6 read回执，Issue9/PR20/Issue10 | REQ6父层唯一入口真正进入这些会话。终态 `F/e2e/pulls.spec.ts:46`仍调用共享signIn；`F/e2e/helpers.ts:57`直达/login。M6原文可见与终态验收未覆盖入口同时成立；本cell未发现相关纠正讨论或菜单/首页整改交接，不能断言每个成员都认真理解后故意忽略。 |
| 09-30最终整合PR23，沿已有 `final-pr23-flow.md`/`final-root-flow.md` | 既有behavior mapping及完整检查被消费，最终194/152 PASS。具体PR23收口由主线复核；本cell只确认相关helper及`.first()`仍在最终冻结源码，首页AppShell:114–119/HomePage:21–27依然组合。因此总PASS未改变此断点。 |

**因果裁决：** 最初的需求阅读转化排除FOLDER正文，令跨模块首页唯一合同没有出现在初始root/基础决策的可得返回中；foundation明确知道组件重复仍接受，且自验允许first、直接地址/ref进入，实际重复反馈不产生否定结果。晚期读到父层后，未建立“新读上层入口约束→既有共享helper/组件组合复核”的闭环，使它一直保留。前一机制是需求投影，后一机制是跨模块验收入口继承，不能简化成同一条压缩丢失。

**反证/限制：** 两个link都指/login，登录API/表单本身可用；首页ref点击成功。REQ1该段没有独立唯一性约束，决定“链接存在”在当时局部判据下能通过。官方逐例selector/错误未提供，不能由4/100断言其造成所有登录旅程评分失败或计算失分。最终实际DOM未新运行。

## 链 B：Your repositories 到占位页

| 时间、原文位置、工作项 | 输入 → 选择/动作 → 结果/后继消费 |
|---|---|
| 04:36:44，B L118 `2f0e745d`，PR2 | architecture列AccountMenu但未定个人列表路由。实施者在`/repositories`与settings路由之间权衡，猜M3 owns search/repos，最后选 `/settings/repositories`。原话称settings subpages **owned by M2/M3**，并计划在PR评论说明modules may re-point；同段又说M1 owns Settings、fills in。生成占位与业务所有权没有被分清。 |
| 04:36:44–04:37:09，B L118–119与L133 | write AccountMenu含该菜单目标，通用`/settings/*`挂placeholder；PR2只提供可导航壳。注释“后继可调整”本身不能构成后继已承接。 |
| 04:50/05:09，DB #6/#16/#17 | foundation正式交接只笼统说M1替换`/settings/*`；根转述给M1需替换SettingsPage；给M3则列复用AppShell/AccountMenu、搜索/创建/fork等，没有个人菜单后继责任。原生“计划写PR评论”与实际已发送内容需区别：未见显式Your repositories重指交接。 |
| 05:26–05:28，DB #20/#21/#23、P3初始context | Issue5负责人方案和PR实施指令以6项atomic/自身交付与路由清单为边界；个人列表、settings/repositories未列。根确认方案一致。后续问题是这个模块清单比原始父层/场景弱，不能只说根没有讨论过范围。 |
| 05:35:57–05:36:12，P3 L109–111 `f34d6d3f/baea84fe/882916d9`，PR11 | 输入：创建/fork的owner list THEN与现有菜单源码。先grep Repositories区分REQ2组织列表；实际返回同时含REQ3父层Q:1136。L111明确称菜单 **“dead-end placeholder”**，先判断个人列表不是atomic、Issue5未列、`M1 owns /settings/*`，又承认THEN明确要求owner list。潜在grader选择和M1写入冲突进入风险判断。 |
| 同L111及05:36:15–05:36:24，P3 L113–122 | 最后决定新增 `/:owner`，因为低成本、修RepoHeader已有dangling owner link、满足owner list且避免M1路由空间。添加namespace list service/API、OwnerRepositoriesPage（L119/120 `80fc68af/04f57531`成功）、路由L121/122 `7ea2740a/c67cd17d`成功。实际选择已提供列表能力，**未改 AccountMenu 的旧target**。不能概括为把全部个人列表排除不做。 |
| 05:36:51–05:38:55，P1 L60/L67/L73/L76 `6ff847ee/efdea1c4/3ab909db/2ac3277c`，PR12 | 独立并行M1也看见同一settings入口，明确将profile/organizations/repositories判 **out of M1 scope**，保留simple placeholder；写SettingsLayout的“This settings section is provided by a later module”，routes把repositories挂SettingsPlaceholder。不是M3后来合并把M1已做的列表删掉。两者的默认所有权假设不相容，却没有在可见交接中被提为待裁决。 |
| 05:37:24，P3 L134 `f1d1fdfe`，PR11；最终F/e2e/repos.spec.ts:136–137,202–203 | 自验创建/fork后用直接 `page.goto('/'+username)`检查owner列表，再用搜索验证发现；真正测到了新列表和持久化，但不从AccountMenu点击Your repositories。此判据在旧菜单死端存在时可PASS。 |
| 05:42/05:43，DB #32/#34，Issue5→root/M4 | M3主动交回visitor Code假设纠正、contents路线、双态搜索文档冲突、seed、可见性矛盾。这里有明确跨任务合同并获消费；**没有菜单残余责任/入口重指请求**。这是反证：不是所有跨任务信息都无法传达，而是本断点未进入该渠道。 |
| 05:47/06:05，DB #37/#57，M1交接/合并`a619edd` | 报“占位页已删除”实际指被删除的旧SettingsPage/PasswordResetPlaceholder文件，新SettingsPlaceholder依然存在。不能把文案当作所有业务占位均已补齐。M1关闭时列身份5旅程及已验证边界，未承接个人仓库列表。 |
| 06:08–06:50，DB #59/#65/#67/#69/#79/#82，PR11最终合入`53532a0` | #59清楚交付`/:owner`，遗留只列M4与/orgs边界；#65要求冲突解决同时保留M1 settings子路由 **repositories** 与M3 `/:owner`；#67/#69独立结构复核及#79双份76/33 PASS确认两组都保留；#82称M3闭环，仅剩Access denied小PR14。这轮会发现“路由组被删”但不会否定“菜单走保留下来的占位终点”。 |
| 09-30 PR23至最终F | 根/整合沿既有mapping并核验真实候选，具体过程复用主线。终态AccountMenu:56仍target/settings/repositories，routes:68为SettingsPlaceholder，OwnerRepositoriesPage另挂routes:103的/:owner。未见后续把该残余入口列为待承接。 |

**因果裁决：** foundation把占位导航当作modules可接管的可调壳，正式交接却笼统移交/settings给M1；M3实现者在原需求和死端都可见时，因为局部Issue范围与path所有权冲突顾虑，改为另建低风险列表；M1同时将旧菜单页留给后继。M3补了能力但没有把残余入口明确退回/转交；冲突复核按结构共存和原有检查确认通过，未覆盖菜单到列表的连接。因此该问题更准确属于**已发现的连接缺口没有责任交回及整合判据**，不是纯父层漏读。

**反证/限制：** OwnerRepositoriesPage、API和访问过滤是真实现，仓库header owner链接、search/direct地址能到达；M3不是拒绝列表全部功能。REQ3未要求一定走Your repositories菜单，因此不能单凭菜单死端认定所有创建/fork原子能力不满足。没有官方逐例结果，未预测分数。scope冲突是当时模型顾虑；证据没有证明若改菜单真的会发生不可解决冲突。

## 可改变归属、覆盖与剩余缺口

可改变的通用归属有三项：原需求投影应保留每个atomic的相关父层约束；模块对已识别残余连接作明确责任交回而不是“later modules”；整合应根据上层入口/终点观察核既有判据是否覆盖，不能只继承总PASS、编号或结构共存。应用整改位置另可由实现方处理共享首页组合、AccountMenu目标与列表接线；本调查没有开工授权，不做改动。

本轮语义回读覆盖根最初flat转换/阅读命令、PR2入口解释和写入/历史浏览器反馈/交接、M3原需求read/现有菜单read/残余解释/列表写入/交接、M1占位保留决定与写入、PR11冲突意图与多方结构/检查确认；晚期M6只定向回读父层read回执，最终PR23沿已有分线报告和主线所有权，未重复全重审。独立advisor没有针对这两个入口做已证的反例验收，不能以其身份数量代替覆盖。

仍未证：provider每个请求完整隐藏字段、注意力及其动机；是否在未匹配文本/图像里有其它未索引表达的首页整改提议；最终浏览器AX与官网逐例失败；菜单断点对评分的净贡献。原生消息检索去重复用22,152记录账本，但只把上述定位的实际回读计为本cell覆盖。早期“根补完后半需求”的旧结论应限定为atomic flat材料，不能再用于否定父层遗漏。报告及证据已交回主线；真实审查起止未设额外计时，耗时未知。
