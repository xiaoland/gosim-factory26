# Sheet Issue #3 / PR #8：契约传递与实施链审查

截至 `coverage.json` 快照。只读审查；未改源码、应用或运行状态，未运行测试。`agents/run-analysis.md` 已读。本人依总账选中并按时间、逐条读完 `views_unique/S01–S39` **39 源、2545 原生 JSONL 行**，包括无头续段、子代理、推理、工具入参与反馈；别名到原文件与逐源范围见 `views_unique/index.json`、`read-ranges.json`。`S40–S49` **10 源、527 行**归主审 `cells/root/a-tail*` 与 base 子审 `cells/base/a-tail*` 独立读取并合账，本 cell 不冒称自己读过。显示层精确重复内容以 `views_unique/duplicate-lines.json` 指回首现原文；阅读工具输出截断已分块补读。原生会话本身以 `head`/`tail` 管道裁过的工具反馈仍是原生证据缺口，不能当完整命令结果。

下文 `S24:L19` 等均指上述逐行视图的**原生 JSONL 行号**。SQLite 为 `evidence/braid.sqlite3`，按 `local_comments.comment_id`、`local_comment_delivery(comment_id,recipient_login)`、关联 `events` / `wake_batch_events` / `turns` / `context_resets` 核实。评论回执的 delivered/consumed 只代表投递/队列生命周期，语义消费另由原生 user 输入、工具读取、决定与代码后果证明。

## 核心结论

1. **早期候选 `d536aa2` 的确漏了 v1.3 Y-min；最终 PR8 已修复并合入。** 根评论 #51（06:12:00）、#57（06:14:11）、#60（06:15:21）仅直接投递给 deepseek-2/deepseek-3/glm-4，`local_comment_delivery` 无 deepseek-5。PR8 在 06:17 交旧候选时没有核对当前根契约；这形成候选交接缺口（`P8a:L87/L122–L125`）。但 **PR8 在 06:31 主动拉取 Issue #1 正文，并阅读评论段（#51 后段及 #54/#57/#60），已经据此决定并开始实现**（`S24:L14–L26`，尤其 `L17–L21` 的工具读取和决定、`L181` 的提交）。根侧 #64 在 06:34:08 到来（`S24:L105–L116`），确认并精化七项/空白足迹语义，**不是全部采用的起点**。`559a0bd` 于 `S24:L181/L214–L223` 提交、推送并交接 #74；之后 PR9 helper 合入，PR8 rebase 后形成 `a23af5a`（`S29:L117–L216`）；Issue3 独立验收 #88（`S30:L87–L133`），最终 06:51:16 合入 develop `e63efc6`（`S32:L27–L32`）。合并树与受验 `a23af5a` 相同（`S33:L21–L25`）。
2. **传播机制是“权威根评论未直接定向 PR 实施者 + 交接前未强制刷新”，不是证实的消息丢失。** Issue3 收到 #51/#57/#60；#57 在旧原生会话被工具读取，#60 也作为真实 user 输入出现（`I3a:L11–L23`）。PR8 没被三条评论直接点名，但后来自行发现、主动拉取、实施。#64 对 PR8 的直接投递已进入其真实输入与工具读取（`S24:L105–L116`）。Issue3 的旧会话 06:30:57–06:31:16 `context_resets` 为 applied，可能延缓了 owner 二次交接；它不能解释全部时间，也不能被当作丢信。后期 #81/#82/#85/#88 等给 PR8 的投递在原生 user 消息和 `braid comment view` 中均可见（`S29:L117/L125`、`S31:L4/L73`）。
3. **Git 化、投递与采用必须分开。** PR2 基线README已有共享契约与类型事实源说明，但设计裁定仍指向根Issue正文/comment1；不能据此称Git中没有契约。当时最新共享v1.x的权威主要在根Issue正文/评论，v1.2 已在子项派发前成立。PR8 实际读了 Git README、packet，也主动读 Issue3 #33/#36，修正 README 三条尺寸路径并保留原端点错误语义（`P8a:L71–L99`）。这证明它会消费局部 Git/Issue 定义，不能称“从未读契约”；但 Git README/packet 当时未承载完整最新 v1.3，`d536aa2` 交接仍引用旧状态。PR8 06:31 的主动拉取又证明“未直投”不等于“永未采用”。最终 PR8 正文虽加入 v1.3 段，旧“交付范围”仍一度写 `used range=非空包围盒`，与新段的 `max(包围盒,足迹)`冲突；Issue3 owner 在 #100 指出并请求窄改（`S39:L27–L39`）。#100 后的处理由主审 S40–S49 合账，不能在本 cell 范围内断言已改好。

## 决定—动作—反馈—后果链

| 时间 UTC / 原文 | 决定与动作 | 工具反馈及可见后果 |
| --- | --- | --- |
| 06:00–06:17：Issue3 #27/#33/#36；根 #28（`P8a:L71–L99`） | A 的 D-A1…D-A10、README 三路径及显示值接缝定稿；PR8 主动读取 #33/#36，修改 README 和 packet。 | PR8 修复了 Issue3 #47 指出的两路径遗漏；该阶段的局部采用是实证，不是单凭 comment 回执。随后 06:17 交出的 `d536aa2` 仍未含 06:12 发布的 Y-min。 |
| 06:12–06:17：根 #51/#57/#60，`local_comment_delivery`；`I3a:L11–L23`；`P8a:L122–L125` | #51 定 Y-min；#57 定 state 未传字段不改与 helper 归 B；#60 允许并行临时私有校验但最终切共享 helper。Issue3 在 advisor wait / reset 前后收消息；PR8 按旧候选交 `d536aa2`。 | 根裁定不直投 deepseek-5；旧候选交接标“待根裁定”，与已发布事实不符。此为**候选版本标记/交付门槛**缺口。 |
| 06:31–06:34：`S24:L14–L26/L105–L116` | PR8 读根正文及 `issue view 1 --comments` 的相关段（`/tmp/issue1.txt` 648–841），据 #51 后段及 #54/#57/#60 决定迁移、解析补齐、快照/state 语义与导出足迹；#64 随后真实到达，精化清单。 | 主动拉取发生在 #64 之前。`S24:L181` 提交 v1.3，`L214–L223` 推送 `559a0bd`、Issue3 #74 / PR8 #75 交接；不是 #64 单独导致实现。 |
| 06:39–06:47：`S29:L36–L216`；`S30:L26–L133` | PR8 预演 rebase，发现 `store.js` 自动合并会同时保留 B helper 调用和 A 私有校验；B PR9 入 develop 后实际 rebase，删私有副本、保留 `min_rows/min_cols` 持久化；Issue3 #81/#82/#85 明确标准并独立复验。 | 候选 `a23af5a` 的 backend 96 / frontend 49 / typecheck / e2e 25 通过，Issue3 #88 接受。初轮 e2e 失败是 `better-sqlite3` Node20 ABI115 与默认 Node24 ABI137 不符，改平台 Node20 后通过（`S29:L171–L199`、`S30:L87–L120`）。不能算应用回归。 |
| 06:47–06:51：`S31:L4–L111`；`S32:L27–L32`；`S33:L21–L29` | PR8 收到 #85 后再次检查单一 helper / 足迹写入，回 #89；Issue3 owner 见 #89、#90/#91，决定自行 merge。第一次 `--match-head-commit a23af5a` 被 CLI 因短 SHA 字符串严格不等而拒绝，改完整 SHA 成功。 | develop `e63efc6`，parents `15abbf6` + `a23af5a`，树逐字节相同；PR8 #90/#91 与 Issue3 #92 记录转交。失败的短 SHA 尝试没有造成坏合并。 |
| 06:52–06:56：`S34–S39` | 根评论 #93 与关闭事件 #167 收讫并关闭 Issue3；Issue3 owner 更新正文、#95；PR8 向 C（#5）发 #96 显示值接缝与公式导出过渡断言，#97/#99 修正文指针；PR8 补 PR 正文 post-merge 状态；Issue3 #100 提醒旧 used-range 文句。 | Issue3 在 C 尚未合入时关闭，但根明确把 `cellDisplay.ts` 替换归 C、公式导出计算结果门禁归整合 PR；这是**带转交义务的收口**，不是公式结果已完成。C 当前先有 #96 交接输入；#100 后文档修正属于 S40–S49。 |

## 原因、竞争解释与修复边界

- **首个返工点在工作项交界。** 根裁定改变正在执行的 PR8 验收标准，却只投给 Issue owner / 其它依赖方；PR8 在 06:17 交候选前没有强制比较根版本。并行期先做旧候选可能是有意换速度，故不应简单判“agent 忽略指令”。真正要防的是候选被标为现行可验收而未声明版本差距。
- **根评论和 Git 指针分离造成维护负担。** README、packet、PR body 各持部分契约，权威仍在根评论；版本推进时旧句仍可能留在交付正文（#100）。此处不必复制整份契约到多个文件，宜保留单一当前版本指针/差异清单，并在 PR 交接与验收处记录所消费的根裁定号。新一轮判别证据：根裁定对 PR assignee 的直接投递记录、PR 原生输入或主动工具读取、候选 commit 中对应差异、Issue 验收引用同一版本，以及旧句是否同步改掉。
- **勿把队列状态误读为模型采纳。** `events.lifecycle=consumed` 与 `wake_batch_events` 说明事件编排，不说明模型读懂。反过来，`turns` 中 #57/#60 没有独立 turn，也不能推断丢失：Issue3 旧原生 user 消息和 PR8 后来的主动工具读取提供了更直接证据。下次若“直接投递后仍漏项”，再查消息内容是否被截断、入口是否可读、决策是否明确、候选是否真的实现；本例没有底层投递失败的确证。
- **并发合并的实质风险被局部发现并修掉。** `store.js` 自动合并本可能留双重校验或丢足迹写入；PR8 预演和 Issue3 #85 指出，最终 `a23af5a` 仅共享 helper 一处定义/调用，并保留足迹写入。`#85` 到达 PR8 时它已做了主要修正，属事后核对，不是此次修复的唯一触发。下一轮若再发生类似 rebase，应看合并后的**实际调用/写入路径**，不凭 diff 无冲突即放行。
- **当前剩余功能边界明确。** `e63efc6` 的 `cellDisplay.ts` 仍是过渡恒等实现，公式 CSV 导出原文。#96 精确交给 C 同一显示接缝（含错误值、FormulaBar/内联编辑仍读 raw）；`e2e/workbook-lifecycle.spec.ts` 的 `PRE-C TRANSITION` 须随 C 接缝替换翻转，并在整合 PR 作结果门禁。Issue3 的关闭早于该终态，不能等同 REQ-1-3-2 公式子句已满足。

## 证据与阅读限度

- 关键 SQLite 评论正文已在原生工具读取处及 `local_comments` 核过；本 cell 对 SQLite 做的是指定 comment_id / 时间窗的关系核查，**未把整库当作全文资料扫完**。`local_comment_delivery` 显示 #51/#57/#60 无 deepseek-5 收件行；#64 有 deepseek-5 行，#81/#82/#85/#88/#92/#93/#99/#100 后期投递行可逐条定位。`wake_batch_events` 的 #57/#60 部分批次无独立 turn，需与原生 user 输入并用。`context_resets` 06:30:57–06:31:16 为 applied；不能由此单因解释 06:17–06:31 的全部间隔。
- `read-ranges.json` 对每个 S01–S39 源标 `[1,N]` 全读；S40–S49 留主审账本，不混写。`views_unique/duplicate-lines.json` 记录完全相同内容的原处；未对无法从原生工具反馈还原的上游 head/tail/截断部分虚称全读。
