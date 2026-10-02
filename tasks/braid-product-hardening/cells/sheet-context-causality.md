# Sheet 前提丢失与 Braid Context 的因果核对

状态：只读核对完成；未改源码、未运行新模型或 benchmark。时间均为来源归档中的 UTC。对象是 `runs/e20260928-completed-replay/sheet/source-workspace.zip` 内 `template/.factory26/20260927-082825-d9c4f6ea/` 的原生 JSONL、物理 `context.md`、`braid.sqlite3`，并与 [Sheet 诊断](../../sheet-score-diagnosis/findings.md) 和 [Braid 产品审查](../../braid-architecture-audit/product-review.md) 对照。58/100 是完成快照回放的官网聚合分数，不提供逐例错误，以下不能换算失分权重。

## 结论

**已证实的直接链条是需求前提在任务分解与跨 Issue 验收中失去约束力；没有证据表明 Braid reset、通知或关闭关联 Issue 的压缩造成了这两个关键决定。** 初次 A1-only 子任务写于根负责人首次 reset 之前。REQ-5 负责人在同一条原生消息祖先链上读到 `A1:C6` 的 GIVEN，又写了通过内部 API 自建数据的浏览器检查；写检查之前该负责人没有 reset 或追加通知。Braid 的历史行为确有额外 Context 替换和广泛通知，可能增加后续整合的注意力负担，但本案只能标为未证实的放大因素，不能替代已经观察到的需求→责任→默认入口验收链条断裂。链条断裂不等于 SVC 文本本身存在缺口。

| 时点 | 存在、送达、读取的区别 | 与 Braid 的先后关系 |
| --- | --- | --- |
| 08:28–08:33，根分解 | 根 Issue 原始 Context 要求“覆盖全部需求、场景和明确指定的初始数据”，并给出 YAML 路径；物理 Context 本身没有 `A1:C6`。根 `native/000-...jsonl` 第 13 行 `grep ... | head -40` 仅返回 REQ-1 的 A1；第 25 行 29,806 字符的 ATOMIC 描述和场景**名称**摘要没有 GIVEN，也没有 `A1:C6`；第 28 行写出 Issue #2 正常启动仅 `Q3 Sales`/`Sheet1`/`A1=Region`。第 13、25 行都在第 28 行的 JSONL `parentId` 祖先链上，故是同一实际分支的输入。 | 根首次 applied reset 是 **08:38:10**（`context_resets.reset_id=01a0e203-bce7-75c3-9012-5337ba670528`），晚于 Issue #2 正文。没有此前 reset 可解释初次缩减。Issue #2 首个物理 Context 已直接收到这个窄契约，原始 YAML 路径仍在。 |
| 08:54–08:55，根二次读需求 | 根的新原生会话 `.../2026-09-27T08-54-00-976Z_01a0e212-3c10-76f4-b7b7-7473b0832357.jsonl` 第 15、17、19、21 行分段读取原始 YAML；第 21 行工具结果含 `A1:C6` **77 次**，第 22 行称“需求已全部读取完毕”并转向共享基础实现。第 21 行是第 22 行的祖先。Issue #2 当时已写窄，但之后没有把 `A1:C6` 写入 Issue #2/#6 正文或任一 `local_comments`；来源 DB 对这些正文与评论的 `A1:C6`/`Region/Sales/Status` 精确查询均无命中。 | 根此前确有 08:38、08:44、08:54 的 reset，08:54 新会话**随后主动重读**完整 YAML。因此不能说 Braid 把该事实永久藏起。大体量工具结果是否真正进入模型注意焦点无法从记录证明；“读过仍未纠偏”是观察到的行为，具体心理机制不可证。 |
| 10:01–10:29，REQ-5 实现和检查 | Issue #6 初始 Context 给出功能、原始 YAML 路径和自检方向，但未给默认 `A1:C6` 种子契约。负责人 `native/030-...jsonl` 第 12、14、16 行直接取得 REQ-5 原始 GIVEN，包含 `A1:C6`、`Region/Sales/Status`、三条销售记录；第 126 行写 `checks/dataops.spec.ts`，其中 `createWorkbook()` 使用 `POST /api/workbooks`，`seedGrid()` 再用 `PUT .../cells` 自填 A1:C4。第 12、14、16 行均是第 126 行的 `parentId` 祖先，文件内没有树切换或 `custom_message`；这比只检索同一个文件更强。 | 该原生会话从 10:01:17 到 10:35:28 只有初始 user 输入；DB 中 Issue #6 此窗口只有初始 `wake_batch`。其首次 applied reset 是 **10:35:28**（`01a0e26f-2134-75d1-a8c5-dda2f742e2c4`），晚于第 126 行的 10:29:22 检查写入。没有观察到当中通知打断或重建导致自造 setup。 |

这种自检能说明 REQ-5 操作在人工填好的工作簿上运行，却不能说明官网场景从首页打开默认 `Q3 Sales` 时存在指定数据。共享基础的 `home.spec.ts` 又只查 A1；根整合重跑 36/36 后将它解释成 REQ-1～5 全覆盖，故本案的**后续未纠偏**与**初始丢失**不是同一个“reset 抹除”机制：初次是有损摘要与责任交接，后续是已见原始前提却没有把默认入口纳入实现责任和最终判据。两者共享的是缺少可核对的跨 Issue 前提契约。

## Braid 机制能解释什么

[产品运行证据](../../braid-architecture-audit/product-evidence.json) 对整份 Sheet 归档找到 84 个可配对 applied reset，其中 39 个新 Context 仅严格追加、8 个内容相同；例如 08:44 的根 reset 只追加 Braid“请检查当前工作进展。”。这证明历史 reset 规则会制造额外重建，**不证明这些重建造成 A1-only 契约或 REQ-5 自造数据**。广泛通知、关闭后 finalization 同理是已观察到的协作成本，必须有与本案决定相交的输入/中断链才能作质量归因。最后整合的根 Context 很长（14:50 原生会话对应物理 `context.md` 为 62,134 字节）且无 `A1:C6`，可支持“重要前提未写进协作记忆”；它仍不能证明 reset 是其消失原因，因为先前 Issue/评论从未写入该前提。

历史 Braid 源码基线 `89212933c976b889f27de1b8cfe863baf8f6042e:src/context.rs` 的 `render_pull_request` 确实对 CLOSED 关联 Issue 调用 `render_issue(..., complete=false)`，省略 description 和讨论；这是**当时的机制能力**。但本案检查写于 Issue #6 关闭之前，`pr:10` 在来源 DB 没有 turn/物理 PR Context，根关联的 Issue #1 在整合期间仍 OPEN。因而没有观察到“关闭 #6 → PR #10 Context 正文被压缩 → 此缺口”的实际链条；不能将该机制列为本次失误的已发生原因。当前工作区 `sources/braid/src/context.rs` 已修改为直接 `render_issue`，应与历史运行区分。

## 决定含义与证据上限

最有依据的改进是把每个场景的初始状态从 YAML 保留到共享基础 Issue 的种子责任、REQ-5 Issue 的消费关系、以及根整合的**全新数据目录、可见首页→默认工作簿→数据操作**检查；先在不换模型的同类任务中观察这条链是否仍断。Braid 的追加评论改走 Wake、收窄通知和保留关闭关联 Issue 正文可按其自身产品证据推进，但不要宣称它们已解释或会修复 Sheet 的 58 分。若要确认 Braid 对质量的增量作用，需固定需求、模型、任务交接与验收门槛，再对比真实生成；当前只有一条轨迹，没有此反事实。

“模型实际可见”在这里指归档的初始 Context、原生 user 输入及当前祖先链中的工具结果。归档没有 provider 每次推理的完整最终请求 payload，不能排除供应商侧截断或注意力分配；同一 JSONL 的祖先关系不能升级为“模型充分理解”。相反，两处决定前无 reset/通知、而 REQ-5 GIVEN 已在祖先链上，足以否定“本案主要由 Braid 重建把前提抹掉”的直接解释。置信度：上述时间顺序、送达和写入为高；对注意力噪声的质量影响为低；官网具体失分权重未知。

## 最后验收声明前的可见证据

这里有两次“全覆盖”声明，须分开看：整合 PR 负责人 `@glm-7` 先在 `develop@8152b05` 上验收并合并，根负责人 `@glm-1` 随后发现整合回执尚未出现在自己读到的讨论中，又在同树的 `main@4023362` 独立复跑并关闭根 Issue。两人报告的测试**通过事实**有原生结果支撑；“覆盖全部需求场景”则超过了实际检查的判据。

| 负责人和时间 | 实际读到的材料 | 声明与判据差距 |
| --- | --- | --- |
| `@glm-7`，14:56–15:06 | 原生 `work/native-homes/.../2026-09-27T14-50-43-640Z_01a0e358-d037-725d-b5d2-b5a63bbeb207.jsonl` 第 16–17 行只列 `backend/test/`、`checks/` 文件名及 `run-checks.sh` 的少量行；未打开 `home.spec.ts`、`dataops.spec.ts` 或 REQ-5 GIVEN。第 28 行执行 `CHECK_PORT=4957 bash checks/run-checks.sh 2>&1 \| tail -15`；第 49 行确认后台退出 0，第 51、53 行得到**末段** #24–36 和 `36 passed (2.6m)`，并非 36 项的完整逐条输出。第 56–57 行合并，15:06 的 `local_comments` #170/#171 称 REQ-1～5 全覆盖。 | 测试计数和合并 head 均有记录；没有逐项把测试 setup 对回场景 GIVEN。单凭文件名、末段 PASS 和数量，不能知道 REQ-5 使用了自建工作簿。 |
| `@glm-1`，15:03–15:22 | 根原生 `work/native-homes/.../2026-09-27T14-59-10-437Z_01a0e360-8be5-7655-b2c9-7c946a128255.jsonl` 第 13–20 行查 `origin/main` 和评论：15:04 的 PR 列表止于 #161，15:06 的根 Issue 列表止于 #168，均早于 #170/#171 发布。根遂在 `main@4023362` 重跑。第 27–36 行核对后端 42+17+7；第 37 行执行 `CHECK_PORT=4791 bash checks/run-checks.sh 2>&1 \| tail -25`；第 44 行 `pbb tail` 只给浏览器检查 #14–36（含 #16 的“seeded workbook appears...”**名称**）和 `36 passed (1.6m)`。本次决策前没有打开需求步骤、`home.spec.ts`、`dataops.spec.ts`、`prepare-seed.mjs` 或测试结果明细文件。第 49、55 行写最终报告和关闭理由；DB 评论 #175 在 15:16 明写正常启动种子 `Q3 Sales/Sheet1/A1=Region`，又称“完整交付成立”。 | 根独立复跑确实通过，`git diff 8152b05 4023362` 为空也证明验收树与交付树相同。错误在**把已运行的检查集合扩大解释成全部需求场景**，不是虚构 36/36。评论 #175 自身把 A1-only 当作交付种子，显示漏审了 REQ-5 的默认数据前提。 |

交付检查源码可由 `official/workspace-after-generation.zip!template/checks/` 独立核对：`home.spec.ts` 第 8–39 行打开默认 `Q3 Sales`，只断言 A1=`Region`，没有 B1/C1 或销售记录；`dataops.spec.ts` 第 11–49、72–101 行通过 `POST /api/workbooks` 和 `PUT .../cells` 制造 A1:C4，再在新工作簿运行操作；`run-checks.sh` 第 28–32 行先向临时 DATA_DIR 写另一个 `Pivot Guard` 工作簿，然后启动应用并运行 Playwright。这个预备工作簿不是 `Q3 Sales`，但也表明“临时 DATA_DIR”不等于对默认种子完整性的验收。上述检查源码是本次**事后**核对的实际产物，不是负责人最终声明前读取过的内容。

对“成员报告未覆盖却未送达”的假设，来源 SQLite 的结论相反。关闭根 Issue 前，所有 `local_comments` 对 `A1:C6`、`Region/Sales/Status`、`数据缺`、`未覆盖` 精确检索均无命中；对“默认/种子/初始/Q3 Sales/A1”的有界复查找到的是 A1-only 交接、其它功能/测试说明和正向验收，没有成员明确报告默认 `Q3 Sales` 缺 B1/C1/记录。`@deepseek-4` 的 comment #169 在 15:06:34 报告首轮 35/36 的 `Target crashed`，定向复跑 1/1 后称 36/36；它的 `glm-1` 投递回执为 `delivered`，但内容不是默认种子缺口。`@glm-7` 的 #170/#171/#172 于 15:06:42–49 发布，三条对 `glm-1` 的回执均为 `delivered`；根在这之前读的列表看不到它们，其随后原生会话也没有一条新的 user 消息或显式 `comment view 170/171/172`。因此回执可证明 Braid 接受投递，不能证明根在关闭前实际读了正向交接全文；不过根自己的复跑与同类覆盖声明已独立发生，不能据此说通知未送达造成默认数据缺口。

这一步的最小证据上限是：归档没有 provider 每次模型请求的完整 payload，也没有人为对照试验，无法断言为何负责人没有把早先读过的 `A1:C6` 对回最终检查。现有原生命令、实际测试源码、结果末段、评论及投递回执已经足以区分：**真实 PASS、覆盖审计缺失、覆盖报告过宽；没有可供投递的默认数据缺口警报。**
