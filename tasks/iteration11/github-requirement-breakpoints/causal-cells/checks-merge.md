# Checks 保存后 merge gate 保留旧状态：因果链

对象：I11 GitHub 最终重放 `e68661975b53`，2026-09-30 定向只读调查。复用 [终态旅程断点](../cells/issues-pulls.md) 与 [完整上下文方法调查](../../braid-context-methodology/report.md) 的版本身份；不重新推测评分贡献。本次未修改应用、工作项或运行配置，未启动应用、执行测试/评测/模型试跑，未读 Sheet，未再委派。终态 Braid DB 复制到 `/tmp/f26-causal-checks.sqlite3` 后以 `mode=ro` 读取。

**结论：可改变的原因已经能定位到 M6a→M6b 的状态更新契约扩展。** M6a 将 Checks mutation 设计成只返回 `check`，母页仅局部替换 `detail.checks`；这在尚无 Open 合并区的阶段并不能单独证明错误。M6b 后来加入服务端计算、前端只读的 `detail.merge` snapshot，重写母页时保留原 Check 回调，同时将按钮/原因/确认条件绑定到 snapshot。它没有补上“Checks 成功写入必须使同页 merge snapshot 失效或更新”的消费义务。后端合并事务重读已经实现，不能替代前端点击前的资格显示更新。

当时原需求不是完全不可见。M6a 设计者与实现者分别实际收到 REQ-6 父层；实现者特地读取父层，解决了 Checks 的导航与到达可见性问题，却没有把合并资格的跨组件更新列入接口合同。M6b 接续读到了 REQ-6-5 对 REQ-6-1 的依赖和“上下文变化后保持页面与数据一致”，又实际读入旧 Check 回调；仍选择保留局部更新。审查与验收围绕独立功能、预置 eligible 初态及事务守卫收口，没有检查同一页从 pending 保存为 success 的连续旅程。

**没有证据证明 reload 是为了绕过已观察到的这个缺陷而增加。** Checks 保存后的 reload 在 M6b merge snapshot 出现之前已经写入，且直接对应 REQ-6-1 的持久化要求。真正可以确认的是它只证明了保存/刷新后仍 success，没有检验保存后当前页的 gate。M6b 合并验收另从已预置 approval+success 的 PR 入场，二者之间没有状态过渡的断言。

## 证据定位与读取边界

[证据摘录](checks-merge-evidence.json) 的 `sources` 保存完整路径、文件 hash、原 JSONL 物理行；`records` 保存对应时间、message id、角色及原记录内容；`comments` 来自终态 DB 的原评论。以下 A–G 不是仅按 basename 判身份；例如 A/B 和 D/E 同 native id 分别是早期 `sessions/` 文件与重建后根目录文件，内容、物理行与时间不同。

| 别名 | 工作项与规范文件尾部 |
| --- | --- |
| A | Issue9 早期 `sessions/…/2026-09-29T11-08-33-927Z_01a0ecda-2307-76e1-9044-d8ee02d4f010.jsonl` |
| B | Issue9 同 native id 根目录文件，始于 11:16 后的继续记录 |
| C | PR20 `2026-09-29T11-30-03-972Z_01a0eced-d244-74e4-8fc0-6cda931f6d8e.jsonl` |
| D | Issue10 早期 `sessions/…/2026-09-29T16-09-22-776Z_01a0eded-8a58-762d-bc11-f3200d8a7401.jsonl` |
| E | Issue10 同 native id 根目录文件，始于 16:12 后的继续记录 |
| F | PR22 `2026-09-29T16-19-28-010Z_01a0edf6-c68a-7397-8f67-a76528af845b.jsonl` |
| G | Issue10 核对 `2026-09-29T16-33-47-006Z_01a0ee03-e1fe-7121-9c3f-05eb462c77ed.jsonl` |

FROZEN = `runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`。下文应用路径均相对 FROZEN。父层、接口相关原文、引入状态的写操作、M6b 定向核对的输入/选择/动作已回读；全过程其它工作项与 PR23 通用收口复用既有报告。导航搜索曾显示截断，所用关键行已按精确 source/line 补读，不将搜索命中视为语义覆盖。当前 cell 没有完整审读所有原生会话或所有图像；不宣称已经穷尽缺陷。精确审查耗时未独立计量。

## 1. 原要求与实际可见输入

### 父层和原子层共同构成状态约束

- `requirements/requirements.yaml:2801–2847` REQ-6 父层区分 PR 与 branch/commit/issue，规定四视图，Checks 对应当前 compare commit；compare 前进后更新当前 commit、旧 review stale、**recalculates merge eligibility**。`:2830–2835` 的导航/精确名称不是全部父层义务。
- `:2855` REQ-6-1 规定两项保护规则、check 属于当前 commit，且“must reuse that context and keep pages and data consistent after the context changes”。保存后显示 success、setter、time，并在 reload 后保持。
- `:3658–3689` REQ-6-5 规定 eligible/blocked 的按钮和解释与条件一致；确认区显示条件，执行时重新读取；末句明确依赖 REQ-6-3-4 **与 REQ-6-1**，同样要求上下文变化后页面和数据一致。原要求没有逐字说必须返回整个 detail，也没有指定 React 缓存方案；状态一致性是上层义务，实现方式可选择。

### 父层不是靠关系自动继承，但本链存在真实 read 返回

| 时间、身份 | 当时输入 → 选择/动作 → 反馈 |
| --- | --- |
| 09-29 11:08:35，A:L4 `ad341db0`，Issue9 | 初始投影仅把 root Issue1 列为 `Parent`，正文自包含 M6a 原子范围、Checks 键控、保存/刷新验收。不能说 Parent 自动注入根全文；也不能说因此没有读到原 REQ-6。 |
| 11:09:21，A:L17 `b4a76626` | 实际工具返回从 REQ-6 父层开始，包含 current compare commit、recalculate merge eligibility，以及 REQ-6-1 的两规则与 context consistency。这是设计者收到父层的直接证据；A:L30 `f477f0cf` 还实际读到根 #231 的 Checks/merge 共享前提。 |
| 11:30:37，C:L22 `54a238f2`，PR20 | 实现者读取各原子块，REQ-6-1 的完整 description 包括 context consistency、保护规则、保存与 reload。此 read 不包含全部父层，故另看下一行的父层独立读取。 |
| 11:32:19→20，C:L70 `0b8d33f1` → L72 `c6aed31b` | 实现者主动写“REQ-6 folder description for Checks nav”，执行 YAML find REQ-6 并打印 description，工具完整返回父层。L73 `2d348c5b` 消费为四个 navigation links、单页唯一名称、Checks on arrival 的解释，决定 Conversation 和 Checks tab 互斥显示同一组件。父层读取确实改变了 UI；没有看到在此把 Check mutation 后的 merge 更新列作设计任务。 |
| 16:09:23→28，D:L4 `885c26dc` / L14 `8852969c` → L15 `7204f8ef`，Issue10 | 初始投影只列 Parent Issue1，进入后实际 read `requirements.yaml` offset3438/limit390，返回 6-3-3 至 6-6，包括 REQ-6-5 依赖 Checks/context consistency 和点击前 disabled/原因要求。本次不把 M6b 未单独读取完整 REQ-6 父层推成全部需求不可见。 |
| 16:10:28，根 #305 → 16:19:52 #310 | 根交接明确消费 M6a #235/§9.18 的 Checks 键控；实施交接把原文、M6a 实现、§9.5/§9.18 列为权威入口。交接规定了存储/当前 commit 与范围，没有定义 Check Save 应如何刷新消费者 snapshot。 |

## 2. 最早解释和局部 state 的引入：当时尚没有 Open merge UI

11:29:29，B:L17 `2d0a4df8`（设计动作，随后 L18 返回评论 #235 成功）以及 DB #235 把范围拆成：M6a 交分支保护、Checks、PR 生命周期/三视图；**Open PR 合并 UI 与 unmergeable 门控由 M6b 后续落地**，M6a 只在 Draft 显示 disabled Merge。后端 GET checks 返回 check，PUT 按当前 compare commit upsert；验收是 keying、持久化、权限、新 commit 回 pending。这说明初期“仅替换 checks”是局部交付选择，而不是已有 merge gate 被忽略的直接证据。

11:40:40，C:L164 `4e8ff866` 实现者设计独立 `PullChecks.tsx`：props 是 owner/name/number/check/canAdmin/onChange，Save 得到 CheckState 后通知父页。L165 记录文件写入成功。11:41:06，C:L172 `2e5c3271` 写入母页，L173 工具回执成功：

```ts
const onCheckChanged = (check: CheckState) =>
  setDetail((current) => current ? { ...current, checks: check } : current);
```

该时点 detail 由页面身份/用户等 effect 读取，检查与其它片段用同一个 detail 容器，但 mutation 更新只声明 check。C:L148 `93abc3ff` 引入的 `pullApi.setCheck` PUT 解包 `.check`；没有另一个 gate 请求。后来最终 `docs/task-packets/m6a-issue-9.md:88–98`、`docs/architecture.md:429–437` 持续把 merge gate 指向 M6b，并输出 `isBranchProtected` 供后续消费。共享接口的重点是数据库事实和 protected helper，未见 UI cache invalidation 的合同。

这阶段有真实失败和修复，不能以最终断点抹掉：C:L272 `b41b9ebd`（11:48:47）分析保存后 success 不显示，L273 error-context/后继反馈定位 `/pulls/undefined`；L274 `9fc908ee`（11:48:53）确认 detail 信封未解包导致 PUT 路径错，随后 edit 修 API 解包与 compare hooks。该失败不是旧 merge gate，因为此时 Open merge UI 尚未出现；局部回调本身没有因此改成完整 reload。最终 M6a packet:148 保留了这一根因/修复身份 `32826b6`。

## 3. M6b 新增 snapshot，旧 mutation 未随依赖扩展

16:18:55，E:L98 `5ef8c3ca` 写 packet 时已经选定“detail 的 merge snapshot”；16:19:29，DB #308 将其公开为设计：详情纯增量扩展 `merge` 门控快照，服务端合并事务重读 checks/reviews/current heads，前端点击前显示 disabled+原因。最终 packet:104 特别写“**详情返回，服务端计算，前端只读**”。这里需要把新派生值的刷新生命周期与既有 mutation 接起来；设计正文/API表/验收未写 Check Save 的消费契约。

| 时间、identity、Issue/PR | 输入 → 选择 → 实际动作 → 反馈/缺口 |
| --- | --- |
| 16:19:53，F:L47 `8d203222`，PR22 | 读取 M6a `PullDetailPage`，原 `onCheckChanged` 局部替换直接进入工具返回。实现者能看见旧代码；不能把它称为只读到后端接口。 |
| 16:20:19，F:L76 `5e840dd0`；16:21:02 L103 `d5cf0bed` | 选择 service detail 扩展 reviewComments/reviews.stale/**merge snapshot**/merged info；设计 `mergeGate` 与 transaction 重读，GET detail 返回 gate。L107 `399dc076` 执行 service edit。后端读时计算与合并执行重读有效，但没有扩展 checks PUT 返回值。 |
| 16:27:48，F:L270 `24b163a3` | 决定完整重写母页，“Things to keep … ready action, **PullChecks**, timeline”。同一 write 新内容 generated L477 保留 `onCheckChanged` 只替换 checks；generated L631 把 `MergeArea gate={detail.merge}` 接入 Open 区；L719/L791 将 Conversation/Checks 两处组件接回原回调；generated L297 effect 依赖仍只有 owner/name/number/repositoryState.status/user.id。L271 写入回执成功。新旧两个状态源在同一真实操作中组合，断点在此成立。 |
| 16:28:07，F:L283 `f467370f` | typecheck 发现 Ready 返回 PullSummary 与 runAction 的 PullDetail 不匹配；实现者明确选择 Ready 后 **refetch detail**，edit 为 `await readyForReview(); setDetail(await pullApi.detail(...))`，L284 成功。Reviewers 返回列表则改局部替换 reviewers。Check 仍维持局部替换。这证明更新策略实际是按 mutation 返回类型/局部数据选择，并非全站统一 mutation 后刷新。也不能据此断言 Check 缺口是有意忽略。 |
| 16:30:07，F:L327 `ff853afe` | 合并验收设计从 seed `Merge the onboarding notes` 的 approval+success 入场，确认 enabled→dialog→Confirm→Merged。没有在此前由用户 Save check 的步骤；这里实际选择了独立初态旅程。 |

其它完整 detail mutation（review、close/reopen、merge 等）会替换整个 detail，Ready 后重新 GET，也会间接刷新 gate。Reviewer 请求不创造 review 决策，局部更新不必改变 gate；不能把它与 Check 的依赖等价。**具体根因是加入新派生字段后，没有枚举既有可改变其输入的 mutation，不能概括为所有局部 state 更新都有错。**

## 4. Handoff、独立核对与自验为什么未改变这一链

M6a 候选 #299/#304 宣告 Check 键控/权限/持久化通过，M6b 依赖它是合理的；但是后续新消费者加入后，需要新的连续旅程，前期 PASS 本来就不能覆盖尚未存在的 merge UI。M6b #330（16:51:21）声称缺 check 时返回 `The test check must succeed before merging`、两规则独立判定、eligible merge 成功；#332（17:08:57）核对的是同一套条件与 #313/#314/#317/#322 的裁决。没有出现“Save 后 current gate 重算”的验收声明或错误反馈。

具体审查输入有界可证：G:L73 `62e9552f`（16:52:33）把整页落到 `/tmp/pdp.tsx`，但返回的是按 Add comment/canMerge/disabled 等关键字 grep 的行；G:L75 read offset545/limit60 是 inline 区；L125 read offset100/limit70 是 reviewer/sidebar；L132 read offset300/limit90 是权限与 effect 附近；L134/135 read1–45 是 imports。**这些相关实际读取没有覆盖 handler L497**，该核对 session 的工具返回亦未出现 `onCheckChanged`。这不是“reviewer 全读实现仍没看见”的证据；是审查选择围绕本次角色/按钮/事务表面，未走 Check producer→snapshot consumer 的链。G:L60 `dc5aa4f0` 认真核后端 transaction 重读，L123 `cd93c914` 对 Req6-5 选择确认区/Merge 名称/blocked 文案核对；这些有效核实不能支持保存后联动已验。

最终历史自验分两条：

1. `e2e/pulls.spec.ts:129–150`：Admin 在 protection-lab pending→选择 success→Save→立即断言 success 和 setter→**reload**→success 持久→API检查 compareCommitId。同样的序列在 C:L209 初写、L231 `6cc5144a`（11:46:19）实际 read 返回。保存后已有 immediate 断言，故不能说所有成功都靠 reload；没有 immediate gate 断言，故也不能说 continuous merge journey 已覆盖。
2. `e2e/reviews.spec.ts:244–277`：Maintain 打开**seed已为approval+success**的 merge-lab eligible PR→Merge enabled→确认区条件 satisfied→合并→reload 检验 Merged 持久。这是 REQ-6-5 指定的 seeded eligible 路径；Maintain 没有 Admin Checks setter，不能由此推出 Check Save 后刷新已验。

竞争解释核对：

- **故意加 reload 遮蔽失败？不支持。** reload 在11:44–46已存在，早于16:27加入 snapshot；原 REQ-6-1 明文要求 reload 持久。未找到 Save→gate stale 的历史失败原文，只有 M6a 信封解包失败被修复。
- **没看到父层才做错？不支持此强说法。** A:L17 与 C:L72 两个真实 read 返回父层；D:L15 收到相关 dependency consistency。能证选择性消费，不能证隐藏注意力或上下文压缩造成。
- **后端 checks 不持久/门控算法错误？本断点不依赖这些假设。** setCheckStatus 按当前 commit 写入；detail重新GET计算 gate；merge transaction重读。此处静态链是前端同时呈现新的 check 与旧的 gate。
- **review/Ready 等 mutation 顺便修复？可以限损，不能消除断点。** 用户只 Save 检查、甚至切 Checks/Conversation tab，并不触发 detail effect 重取；等待检查结果也不会自动改变 merge。

## 5. 末轮整合、终态与可作出的决定

PR23 的通用收口复用 [final-pr23-flow](../../braid-context-methodology/final-pr23-flow.md) 与 [final-root-flow](../../braid-context-methodology/final-root-flow.md)。本路径的末轮实质变化是 auth 测试超时余量和证据/packet，未改 Checks 保存 API、母页 Check 回调、merge snapshot 消费关系，也未增加这条连续旅程。既有全量152个检查通过的事实不否定，但它们仍消费上述分离的两个场景。最终 `f628045` 合 main `442dc1c` 树一致；本链保留到最终重放冻结源码。没有把 PR23 另一个证据文件错配问题扩进本 cell 的原因。

冻结源码的闭合静态链：

```text
PullChecks:40–49 Save
 → api.ts:350–353 PUT checks/test → 返回 CheckState
 → PullDetailPage:497 只替换 detail.checks
 → detail.merge 保留旧 snapshot
 → :651 MergeArea gate={detail.merge} / :869–886 confirmation conditions
```

`PullDetailPage:276–294` GET effect 没有 check 或 tab 依赖；`:738` 与 `:810` 两处 Checks 使用同一个回调。`backend/src/modules/pulls/service.js:863–872` GET detail 重算 gate，`:737–778` 读当前 check/review，`:797–809` merge事务前后重读。因此可静态确认 pending→success 后当前页仍用旧 blocked gate，反向 success→failure 后可能仍展示旧 enabled/确认条件；实际 merge 会被服务端拒绝，不能声称绕过保护或误合并。没有本次浏览器复现，页面渲染的实际行为证据与官方扣分对应仍未知。

修复/方法归属可决定为：**应用实现归母页/Check mutation 消费合同；通用开发方法归新增派生状态时核对跨模块 mutation 的影响与连续旅程验收**。不需要把题目的 React 或 Checks 实现硬编码进 Harness，也不需要强制每种 mutation都返回整个详情。技术修法可以是保存后重新GET detail，或原子返回完整更新后的 detail，再统一替换；选择哪一种留给已授权实现阶段。下一轮最小行为证据应在同一页、同一 current compare commit、approval已满足的受保护 Open PR 上验证 pending→success→enabled/reasons/confirm 和 success→failure→disabled/reasons，不先导航或reload；另保留服务端拒绝限损验证。无实验授权，本次止于因果与证据。

剩余缺口只影响结论边界：没有 Save→stale gate 的历史浏览器失败记录；没有逐例官方失败明细；没有对本候选的新运行复现。已有静态更新链与原生引入动作足以决定修复方向，不能从4分推算该问题的分数损失，也不能把“未见失效合同”提升为读遍所有工作项后的绝对不存在。
