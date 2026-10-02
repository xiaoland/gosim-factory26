# 规定初态：可见原文、降格解释与验收替代

2026-09-30，只读定向取证；对象仅 I11 GitHub 最终 replay `e68661975b53`。未运行应用、检查、评测或模型，未修改实现与 Braid 工作项。不是官方逐例失败归因。

`F` = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`，`Q` = F 的 `requirements/requirements.yaml`。原生完整路径、物理行、时间、message ID 和原文保存在 [seed-integration-native.json](seed-integration-native.json)；评论全文/时间/工作项保存在 [seed-integration-comments.json](seed-integration-comments.json)。下文 `L` 都是该 JSONL 的物理行。复用的终态评论索引来源是终态真实 `evidence/braid-state/braid.sqlite3`，不是取回目录根的零字节同名文件。

这里有三个不同强度的判断：团队树缺少原文要求的现成状态，是明确 seed 缺口；Issue 不提供逐场景隔离对象，是明确供应边界收窄；PR 是否在实际评测中互相污染，仍取决于未知的外部场景生命周期。不能把它们一律写作“官方用例互相污染已发生”。

## 原始约束与读取位置

ROOT Q:8–18 规定描述已有对象/权限时由 seed 提供，不能因缺 seed 禁用需求。REQ-2-2-2 Q:812–815 要求 cycle 场景的**同一 team 已有 parent 且有 descendant**，拒绝 descendant 后原 parent 保持。REQ-5 父层 Q:2154–2159 要求 successful edit、invalid edit、comment、comment validation、assignment、labels、milestone、closing 有隔离 issue，初態不被别的场景改变。REQ-6 父层 Q:2841–2846 要求账号、branch、PR 和可变状态逐场景独立 provision/restore，包括 repeated/parallel；REQ-6-5 再要求 eligible/blocked 各自初态与复用前恢复。

这些关键文字实际到达了负责人的工具返回，并且出现在其随后的明确解释中：

- M2 Issue4：09-29 **06:07:04 / 589ac1e9 / L26** 返回原 REQ-2-2-2 的 existing parent + descendant；**06:12:18 / 0c9834b3 / L50** 直接引用后作种子选择。
- M5 Issue8：**06:53:34 / 7ccb1825 / sessions 副本 L14** 返回 REQ-5 父层 isolated issues 整段；**06:58:32 / 58a9d136 / 根目录继续副本 L7** 直接引用隔离要求后解释。两副本同 native id、物理行不同，不能拿继续副本的 L14 代替最初 read。
- M6b Issue10：**16:10:55 / a3ff1bd7 / sessions L68** 引用 repeated/parallel 和 independently restored；实现者 PR22 **16:22:39 / ae7fd895 / L146** 再讨论，核对者 Issue10 **16:54:38 / e3dffd29 / L117** 仍能识别该原文。

因此这些链不能以“父层根本不可见”解释。Root 最早 ATOMIC 展平漏掉 FOLDER 是另一个已证事实，但后继直接读取已消除了本组三处的“未进入上下文”前提。

## A. 团队循环：把合取初态减成较弱的循环示例

| 时间、工作项、原始位置 | 输入 → 选择/动作 → 后继消费 |
| --- | --- |
| 09-29 04:30:22，Issue1，`904a0f80` L16 | Root 写共享 seed-data：`frontend-child(parent:platform-team)`“等循环层级演示按 M2 场景 seed”。这是两层示例和下放完善义务，没有写出 same team 非空 parent + descendant 的完整见证。最早共同设计可定位于此，但不能说这条简略文档禁止 M2 补第三层。 |
| 06:06:28，Issue4 评论 #58 | 交接原 REQ-2-*、共享 seed-data、7 场景与刷新验收，重点协调组织仓库 seed 共存及权限；没有另加第三层。 |
| 06:07:04–06:14:49，Issue4，`589ac1e9` L26；`0c9834b3` L50；`5123de26` L56 | 原文已有“existing parent and a descendant”。负责人仍选择 platform(parent none) 与 frontend-child(parent platform)，理由是 platform 选 child 可形成循环；稍后再次用原文论证 selector 必须保留 descendant 选项。**消费了“能选后代并拒绝”，没保留“原 parent 非空”的同一对象合取。** |
| 06:16:53，Issue4 评论 #68 | 方案把三个 team 明示登记：frontend-team/platform-team/frontend-child(parent=platform)。提出 Access denied 与 M3 的跨模块冲突、seed 共存两个裁决点；没有将 cycle 原 parent 未供应列成例外。Root 随后对已升级的两点作 #73 等裁决，这是协作有实际纠偏的反证。 |
| 06:37:45，Issue4 实施会话，`4fba7ca3` L60，L61 成功 | 写 `backend/src/seed/governance.js`，仅 child→platform；另两 team parent 为空。首次实际 seed 引入与最终 F:58–73 相同。 |
| 07:07:44，`0aba2ab0` L291 | 写/设计 cycle 自验：platform 选择 frontend-child→Save 报 cycle，原选择断言 **No parent**，reload 仍 No parent。最终 `e2e/orgs.spec.ts:199–207` 保留这个较弱反例。07:08:41 `78d23bfc` L293 检查测试间顺序时仍认为该树足够。 |
| 07:24–07:25，PR13 #113 → Issue4 #114 | 以 95 unit/51 E2E、7 场景、seed 双跑幂等报 ready，无未决；根独立复跑相同候选后合入 `e9390cc`。Root #154（08:34:48，PR15）保存其候选 `d62907d`、95/51 复验和合并事实。此处重复运行是真的；不补出未断言的非空原 parent。 |
| 09-30 PR23 → main | 共用最终整合链见主报告；最后仍是这三个 team 与 No parent 自验，无额外三层 seed。 |

**裁决：** 这不是层级环算法坏。`orgs/router.js:85–95,341–350` 会拒绝循环；`TeamSettingsPage:56–59` 可恢复原选择。断点在供应/验收把原文合取减为“任意能制造 cycle”的见证，后续复核继承该见证。原文、弱化选择、代码、弱化验收、交付之间均有直接证据。为何未注意合取的认知原因没有记录，不能由此猜模型能力或上下文压缩。

反证：用户可经 UI 新建/改造三层树后测试，普通 parent 设置功能存在；这不能替代规定初态已经供应。官方是否使用该初态未知。

## B. Issue 隔离：将应用供应要求交给假定的评测 fixture

| 时间、工作项、位置 | 输入 → 选择/动作 → 后继消费 |
| --- | --- |
| 06:53:34，Issue8，`7ccb1825` sessions L14 | 实际返回 REQ-5 父层，包括各 mutation 场景 isolated issues，不能只按9条 atomic编号声称其未可见。 |
| 06:58:32，Issue8，`58a9d136` L7 | 负责人发现 #1 已有 label/milestone/assignee，不适合作“待设置”目标；明确引用隔离段，然后推测 **“evaluator isolates via its own pw-* objects mostly”**，选择 minimal 3、不多 seed。#3 Original issue title 同时供 invalid edit 与干净 metadata；成功编辑/评论等由本地测试创建 fresh issue。它也想到成功编辑可能改掉 invalid 场景原题，最后仍依赖评测会自行建对象。记录没有提供官方支持该猜测的证据。 |
| 07:01:35，`24676441` L12；07:01:39 评论 #89；07:02:35 #90 | 方案公开成3个 issue；#3说明“也可作元数据场景的干净目标”；强调 insert-if-absent 不覆盖用户修改。PR15 交接按该设计实施。这里有明确传递的弱化设计，不是只有思考而未落地。 |
| 07:04:44，PR15，`955c4750` sessions L83，L84 成功 | 写 seed/issues.js，仅 Improve onboarding、Legacy welcome text、Original issue title 三个固定业务对象，关联只随初次创建写入。最终 F `seed/issues.js` 保留。 |
| 07:26–07:31，PR15 #115 → Issue8 #116/#117 | 报 invalid edit 在种子 Original issue title 验证、其余新建对象；review主要纠正权限显式集合并要求平台路径，未退回逐 mutation 的 seed 初态。权限问题确有纠正，不能把审查描述成完全没作用。 |
| 08:20:52–08:21:07，PR15，`2f7b1d6b` L91、`2b7c1529` L98 | 新增 triage/maintain 验收时，实施者明确识别关闭共享 #1 会污染后续场景；也否定“测试末尾恢复”因失败中断脆弱，改用独立 request context 登录并 API 创建 fresh fixture。**正确修复了自验隔离，却没有回到 REQ-5 的供应义务增加各场景独立 seed。** 原文需求与测试基础设施的隔离对象不同。 |
| 08:49–09:00，PR15 #159/#164/#167 | 整合 M2 后 `2a51605`，122 unit/75 E2E，合入 `2eed74e`；#164核冲突和候选，未追加各 mutation seed。 |
| 09:19–09:20，PR17/Issue8 #183/#187 | 两条权限前提通过新增检查闭合，`425b97c`→`41bf131`，122 unit/81 E2E。Issue8称REQ5完成。补充的是权限账户及局部行为证据，不是逐场景 seed供应；最终仍3个固定 issue。 |
| PR23 → main | 既有spec及预先准备的fresh fixture全量通过；最终保持上述供应边界。 |

**裁决：** 明确原因是未经证实的外部评测准备假设把应用的 seed 合同收窄，同时本地用例通过自行 provision 覆盖了缺少供应的前提。不是创建 issue 功能不存在，也不是所有测试共用可变对象；恰有原生记录证明团队理解测试隔离并正确实现局部 fixture。

替代解释与限制：隔离对象可以由公开 UI/API 动态建立，不必一定全是静态 seed，也不需要私有 reset 端点；但不能把“外部一定会自己建立”当作事实。若真实评测每场景确实独立建立对象，该供应缺口的评分影响可能被消除。没有官方生命周期，不能断言该3对象实际造成串扰或多少失败。

## C. PR 独立恢复：fresh DB per 本地run 被当作逐场景合同

| 时间、工作项、位置 | 输入 → 选择/动作 → 后继消费 |
| --- | --- |
| 16:10:55，Issue10，`a3ff1bd7` sessions L68 | 明确读到独立 provision/restore、repeat/parallel；也指出 insert-if-absent 合并后不会 restore。解释为本地 e2e 每 run 新DB、一次run每场景一次、成功/拒绝用不同 PR即可；进一步以 spec 排序避免相互影响。对评测本身没有观察依据。 |
| 16:18:55，Issue10，`5ef8c3ca` L98 | 复核认为隐藏套件做多次 merge 也必须自己 setup；继续推荐预置 eligible approval+check。这里是推测“外部需要setup”，不是官方承诺。 |
| 16:19:29–16:25:20，#308/#311 → root #313/#317 | **有效纠正的反证：** M6b发现现有 seed 没有protected main+非作者Write reviewer+Open eligible组合，升级裁决C。Root原生 **16:21:39 `dd4548e1` L40**、**16:23:59 `77f888b5` L59** 核原文后否定仅用e2e编排eligible初态，批准新 merge-lab 三PR、预置 approve+success，并调整旧全库计数断言。不能说所有初态都被忽略或root只维护PASS。 |
| 16:22:39，PR22，`ae7fd895` L146，L147 成功 | 实现者再看恢复要求，认为启动恢复会覆盖用户已经合并的持久数据；因此保留insert-if-absent，把“独立”解释成不同PR/本地fixture，不设计场景生命周期。实际 edit seed/pulls.js 引入 eligible、blocked、review 同仓库、共享 main的3个PR；各可变状态仅创建时写入。用户持久化与场景恢复确有张力，但原文未授权用固定测试顺序作为其解决方案。 |
| 16:28:55，PR22，`02a9f861` L289 | 编写后端review测试时采用fresh服务/DB；浏览器spec选择seed eligible直接合并。实际测试方式与上述解释一致，不能把它说成只有未采用的考虑。 |
| 16:51:21–17:08:57，PR22 #330 → Issue10 #331/#332 | 候选42b2f64经194 unit/152 E2E和平台路径；核对者 **16:54:38 `e3dffd29` L117** 把fresh DB per run当restore，**16:55:18 `059dfe36` L140** 核alphabetical顺序，认为reviews留下Request changes在pulls/content之后、后续session不依赖则可。#332通过“仅创建时写入、幂等”，没有另证逐场景/并行恢复。 |
| 09-30 02:02:33，Issue1 #337，随后PR23 | M6b merge `0e57fd0`，报告无遗留在途成果；最终整合复用相同spec形态，main `442dc1cf…` 保留固定 seed 与可变共享 main。 |

**裁决：** 这里能证的是需求恢复单位“scenario”被解释为自验运行单位“fresh database per run”，再由固定顺序使本地检查相容；产物未提供已证的逐场景恢复生命周期。它是外部前提依赖，不能静态确定官方真的复用同一DB或遭受污染。REQ6 eligible预置已成功修正，应从“初态缺失”中扣除；剩余问题是隔离/恢复合同，不能继续拿旧版本的无eligible状态冒充终态。

反证：每次独立 fresh DB确实恢复，insert-if-absent保护用户持久化也确有价值，后端merge为事务操作。设计可采用独立应用实例/公开setup等方式满足场景要求；要求不意味着每次服务启动清库或回滚用户数据。本报告不给未授权实现方案，也不运行重复/并行实验。

## 总体证据界限

原文可见、明确解释、实际写入、局部自验、正式交接、最终保留已能构成以上链条。现有材料足以决定需要复核“原始GIVEN与自验fixture是否同一合同”，不足以证明provider内在注意力、泛化能力或某一隐藏用例的执行/扣分。初始ROOT规划如何影响后继选择是有文档传播支持的解释，不能把它当唯一原因：M2/M5/M6b都获得过纠正机会，有的实际纠正了另一些前提。
