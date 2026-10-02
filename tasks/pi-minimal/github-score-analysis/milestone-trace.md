# GitHub c3fea0c3488c：Issue / PR 里程碑范围的丢失链

结论：公开需求明确覆盖 Issue 和 PR，且主 Agent、fresh advisor 都实际收到了这一范围。最早可见收窄发生在主 Agent 的初始模块设计；随后 advisor brief、数据库、接口和 UI 沿用 Issue 专属范围，后续检查没有纠正。证据支持“已送达的跨对象要求在需求转述与设计时丢失”，不支持将本例归因于未读取、工具截断或已发生的上下文压缩。无法从轨迹证明模型内部为何忽略该限定，也不能据此量化其对总分 2/100 的贡献。

## 证据约定与边界

- `T`：`runs/analysis/pi-minimal-github-20260930/20260930T031746Z/c3fea0c3488c/extracted/template`。
- `M:Lx`：`T/.factory26/pi-minimal/session.jsonl` 的 1-based 原生行号，共 711 行。
- `A:Lx`：`T/.factory26/pi-minimal/session/dc12f443-1021-4428-9573-e360a0e6112f/run-0/session.jsonl` 的 1-based 原生行号，共 52 行。
- 表中 ID 是原生行的 `id`；时间均为 2026-09-30 UTC。代码行号另标为交付源码位置。
- 只读取上述本地证据、相关交付源码、需求和 system/Skill 定向片段；不执行下载内容，不联网、调用模型、运行测试或评分，不改源码。本报告是唯一写入文件。既有 report 仅作定位线索。

## 一条可追溯链

| 环节 | 原生位置、ID、UTC | 短引文与可观察事实 |
| --- | --- | --- |
| 完整范围第一次实际可见 | M:L18，`a8a06e90`，01:19:29.422 | `read` 的实际返回含需求 L2140–2141：milestone “may be associated with multiple issues or PRs”。不是仅凭发出读取命令推断读到。 |
| 原子需求与场景完整送达 | M:L19–20；请求 `cb5b19f7` 01:19:34.061，返回 `c0eaa9e7` 01:19:34.063 | 请求 offset=2357、limit=560；实际返回覆盖 L2357–2916，含完整 REQ-5-3-3（需求 L2696 起）。“Assign Issues and Pull Requests to a Milestone”；description 开头 “On the right side of an issue or pull request”；场景也写 “opens an issue or pull-request detail page”。实际返回与交付 YAML 的该 description 完全相同。 |
| 最早可见的设计收窄 | M:L30，`af8a7b56`，01:23:59.084 | 数据清单中 `issues (... milestone_id ...)`，紧邻 `pulls (...)` 没有该字段；UI 清单把 “Milestone” 放在 Issue detail；路由清单为 “issues CRUD, … milestones, close/reopen”，下一项 pulls 清单没有 milestone。同条记录明确引用 REQ-5-3-3 的 `v1.0`，证明并非完全未注意到该需求。 |
| 最早对外 toolCall 转述收窄 | M:L36，`adf80123`，01:24:49.095 | `subagent` 参数 `task` 把 “assignees, labels, milestones” 放在 `issues (...)` 内，而 `pull requests (...)` 罗列评审、检查、合并、状态操作，没有 milestone。验收提议只是 “main user paths (register→sign in→create repo→commit→issue→PR→review→merge)”；五项咨询问题聚焦重播种、组件库、快照提交、版本及 accessible-name 风险。 |
| 首次落成数据库边界 | M:L46，`219a38f0`，01:26:04.421 | `write` 的 `backend/src/db.js` 内容创建 issues 的 `milestone_id INTEGER REFERENCES milestones(id)`；相邻 pulls 表没有该列，也没有独立 PR–milestone 关联表。这是首次实现 toolCall 中可见的遗漏。 |
| advisor 有第二次发现机会 | A:L11，`cb501b13`，01:25:01.958；A:L21，`5a9ac217`，01:25:13.067 | A:L11 grep 的 REQ 原文 L2702 虽按 500 字符截断，开头 “On the right side of an issue or pull request” 完整保留；A:L21 的实际 read 返回又完整出现 “may be associated with multiple issues or PRs”。advisor 不是只收到主线缩写。 |
| advisor 没有纠正这一范围 | A:L52，`c2f56d72`，01:29:01.845；M:L62–63，通知 `6967ec7e` 01:29:22.166、主线处理 `7480c445` 01:30:22.166 | advisor 结论为 “The plan is basically sound”，突出 accessible-name、ARIA widgets、合并内容问题；报告无 milestone。主线处理将 milestone 提到 picker 的 role 设计，但没有补充 PR 支持，随后继续实现。数据库在 advisor 完成前已经写入；后续仍有纠正机会。 |
| 后端沿用 Issue 专属关系 | M:L73，`140a5de1`，01:34:15.777；M:L85，`b6b8b406`，01:36:44.252 | issues 路由写入 `router.put('/:owner/:name/issues/:number/milestone', ...)`，更新 `issues SET milestone_id`，活动 target_type 固定为 `'issue'`。同轮 pulls 路由 write 内容共 18 个路由定义，全文没有 milestone。 |
| 前端再次沿用收窄后的设计 | M:L111，`134e2019`，01:40:57.792；M:L157，`ff222dc5`，01:51:12.752；M:L164，`87cc07cf`，01:53:32.948 | L111 页面设计仍把 “Milestone” picker 列在 `/issues/:number`。L157 IssueDetail 写入 picker 和 `/issues/${number}/milestone` 调用；L164 PullDetail 的 aside 只有 `ReviewersBox`、`ReviewSummary`、`MergeBox`，全文无 milestone。 |
| 真实浏览器已到过两种详情页，未触发范围纠正 | M:L220，`3930d308`，01:57:55.426；M:L226–227，快照 `09ea4ed6` 01:58:13.258、主线处理 `ccbcafef` 01:58:20.268 | Issue 快照列出 `button "Milestone" [ref=e72]`。随后 PR 详情快照列出 Reviewers、Review summary、Merge，没有 Milestone；主线反馈 “PR detail renders”，转去检查 Merge 和 Files changed。PR 快照来自 `head -40`，不能单独作为完整页面缺失证明；前述 PullDetail 源码为独立支持。 |
| 后期验证仍以 Issue 元数据为范围 | M:L630，`7df791ac`，02:41:58.907；M:L638–639，请求 `59d430a6` 02:42:50.040、返回 `ab11d0cd` 02:42:51.116 | 主线审查 “issue detail page: metadata pickers (Assignees/Labels/Milestone…)”。浏览器打开 `/issues/1`，对 Read 账户统计这些按钮数量，返回 0。它验证了 Issue 的控制不可见性，没有验证 PR 里程碑可用、保存、None 移除和刷新持久化。 |
| 收尾继续宣称完整 | M:L685，`4e7938bd`，02:48:51.921；M:L699，`8588a1d1`，02:50:57.999 | 收尾说 “re-check a couple of potentially graded details”，随后检查 clone popover。最终声称满足“全部约 30 条原子需求”，将“指派/标签/里程碑”列在 issue 验证项内，PR 列表仍没有里程碑。公开 YAML 实有 47 个 `type: ATOMIC`；这里的约数不能充当逐条闭环证据。 |

交付源码与上述初始 toolCall 一致：`backend/src/db.js:127` 只有 issues 的 milestone_id；`backend/src/routes/issues.js:354` 为 Issue 里程碑路由；`frontend/src/pages/repo/IssueDetail.tsx:85` 调用该路由。`backend/src/routes/pulls.js`（629 行）与 `frontend/src/pages/repo/PullDetail.tsx`（616 行）全文均无 milestone；后者 L76–80 的侧栏仍只有三个评审/合并组件。没有发现随后实现 PR 里程碑的变更。

## 原因判别、反证与未知

**可支持的原因层级。** 这不是“先设计正确、编码时漏一个控件”：数据库、接口与 UI 都一致执行了较早收窄的范围。更精确地说，主线按 Issue / PR 分模块时未保留这一条跨对象要求，advisor 的风险复核和后续实现导向检查又没有发现差异。依据是 M:L30 → L36 → L46 / L73 / L85 → L157 / L164 的连续一致性，而非由最终缺陷反推全部过程。

**不可升级为确定因果的解释。** 需求确实位于 Issue 模块下，依赖 REQ-5-1-2，且种子描述偏向 Issue；这使“沿模块分类时忽略跨对象限定”成为合理假说，但没有原生记录说 Agent 因该分组而主动排除 PR。反证是 M:L30 同时把 comments / activities 建模为带 `target_type` 的 Issue / PR 共用对象，不能称其完全不懂两者共享能力。也没有明确决定“为省事删去 PR milestone”的记录。

**读入与截断。** 主线初读确实碰到 50KB 输出限制，但后续按实际断点接读：M:L10（`b0f41d25`，01:19:05.574）尾部为 1–618；M:L16（`6b74224a`，01:19:24.949）为 1159–1796；M:L22（`1b7259ab`，01:19:38.707）为 2917–3618。跨对象里程碑原文位于未被截断的 M:L18 / L20。advisor 的 grep 单行截断也未遮住跨对象限定，且另有 A:L21 的完整表述。因此不能把可见截断直接当作本例原因。

**上下文与 compaction 边界。** 两份原生 JSONL 均没有 compaction / branch-summary 事件。M 从 L1（session `01a0efe4-7d83-7106-aa8f-3ee6679cb85c`，01:18:44.100）至 L711（`288f6a35`，02:51:46.956）；A 从 L1（session `01a0efea-1822-77f0-94ca-1fafda39f0ed`，01:24:51.363）至 L52（上述 advisor 最终答复）。M 的其余非消息事件只有模型/思考级别变更、advisor 通知和后台任务返回；A 另有 session_info。可见记录不支持“压缩后忘记”，但不能用 JSONL 事件缺席证明模型内部注意力或所有不可见传输行为。

**相关指令与 Skill。** M:L4（`a6c91f6d`，01:18:50.405）明确要求“验收判据来自原需求与初始条件”及“不以最少行数牺牲完整需求”。两份 capability snapshot 的 `system` 均含 Ponytail 的 “Never simplify away … anything explicitly requested”；advisor 实际读取返回 A:L7（`c3377eec`，01:24:58.115）也包含该句及 “Trace the whole thing first”。advisor system 要求挑战验收判据、找反例；A:L52 没有完成这条需求的对照。M:L202（`6eb7f2ee`，01:56:48.898）的 agent-browser Skill 还写明 “A successful click is not proof that the application persisted or applied the change”。这些规则提供了纠错要求，不能被解释成删减里程碑范围的直接指令。此次没有证据能将 Ponytail 判定为直接根因。

**验证证据的界限。** 定向检查里程碑关键词、相关页面往返与已观察到的 `@e72` 调用，未找到可定位的正向“选择 milestone → None → 刷新”检查，更未找到 PR 对应检查；不能仅凭最终交付声称“issue … 里程碑”已走查就补出操作证据。本调查没有遍历所有浏览器操作来证明绝对不存在其它验证，亦未重跑页面。最终缺少 PR 数据关系/路由/UI 可由静态交付证据确定；官方逐例错误缺失，不能把其余失分归给该缺口。

## 两项针对性改进候选

1. 在需求转述与 advisor 输入中保留“ID + 动作 + 适用对象集合”的最小清单。此例应明确 `REQ-5-3-3: {Issue, PR} × {选择, None移除, 刷新后保留}`，让 reviewer 从原文核对跨模块对象，而不是只复核按页面整理过的功能摘要。这是补足保真步骤，不需要泛读更多 Skill。
2. 收尾将每个对象分别关联已观察结果；仅验证 Issue 时，PR 项保持未验收，不允许汇总成需求已完成。对本例只需实际应用验收中的两条同型路径与保存/移除/刷新观察；这不是新增 Factory/Braid 测试。以上仅为候选，未修改提示词或实现，也未证明提分。
