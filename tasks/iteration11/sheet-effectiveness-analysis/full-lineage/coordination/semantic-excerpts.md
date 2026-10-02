# 语义抽查批次与未读边界

这份账记录本轮实际进入模型上下文并被语义判读的原始片段。其余记录只由脚本解析、计数、保留 `source_file/line/msg_id/fingerprint`，不能写成已全文阅读。原始材料根和只读 DB 边界见 `coverage.md`。

## 已判读片段

| 批次 | 原始 path:line | msgID / role | 判读内容 | 可支持的结论 |
| --- | --- | --- | --- | --- |
| C1 | `work/native-homes/pi-deepseek-fast-01a0ec51-3250-77f3-90a6-7cd3ecdf056a/2026-09-29T08-39-00-259Z_01a0ec51-35a3-7211-b870-967923ee0dc2.jsonl:4` | `54490a0f` / user | Issue5 刷新正文：PR10 已合入 `a592c3e`，Issue 仍等待 D 回归 | 当前正文把实现完成与跨 Issue 依赖分开表达 |
| C2 | 同上 `:6` | `0f1dbb0d` / toolResult | PR10 状态与证据入口回包 | 负责人可由对象状态追到冻结候选与证据入口 |
| C3 | 同上 `:7` | `1eca9726` / toolResult | PR10 交付/消费基线和验收事实 | 该片段支持“C 已交付”的局部判断，不支持全链消费结论 |
| C4 | `work/native-homes/pi-deepseek-fast-01a0ec4c-81ff-70b2-bc23-9da9c3560624/2026-09-29T08-33-53-040Z_01a0ec4c-8590-7193-8683-7427aec61aab.jsonl:6` | `19878cdf` / assistant | C owner 先核验 PR10、当前评论与 merge 状态 | 体现续段先读取当前对象再决定动作 |
| B1 | `work/native-homes/pi-deepseek-fast-01a0ec60-3a2c-7152-ad47-4e868032fa2e/2026-09-29T08-55-25-259Z_01a0ec60-3d4b-71b6-a647-c9c35f3c4663.jsonl:6` | `6304d1f5` / toolResult | PR9 状态、权威入口、依赖边界 | B 的判据和依赖被集中到 Issue/PR 入口 |
| B2 | 同上 `:10` | `cea78a2a` / toolResult | C/E/D 依赖与验收边界，记录首轮失败需保留原始输出 | 支持“机制门与用户路径仍需分开核对”的局部判断 |
| B3 | 同上 `:11` | `ba711b37` / assistant | 收到 PR10 通知后，B 判断 Issue5 正文与持久证据已一致、PR9 无动作 | 这是具体“无动作”消费样本，不推广为所有通知都被消费 |
| B4 | 同上 `:15` | `bd0c6071` / toolResult | 根 Issue 当前契约与负责人/版本入口 | 支持续段可从当前契约回看共享版本 |
| base1 | `work/native-homes/pi-deepseek-fast-01a0ec8e-a3de-7dc0-a89b-d5ed448caf45/2026-09-29T09-46-08-652Z_01a0ec8e-ad8c-75ef-8bca-d590b119a323.jsonl:4` | `8e9864f4` / user | 根 Issue 刷新：当前负责人已为 `glm-9`，并带入恢复/契约上下文 | 支持负责人迁移改变后继者看到的当前入口 |
| base2 | 同上 `:8` | `d11d0e9b` / toolResult | 共享契约 v1 正文片段 | 支持契约正文作为共同版本入口 |
| base3 | 同上 `:12` | `7668355e` / assistant | 基础层核对 `parseCellChanges`、state endpoint 与 paste 新端点边界 | 支持基础层对新实现边界作出具体“需动作/无动作”判断 |
| root1 | `work/native-homes/pi-deepseek-fast-01a0ec90-aec6-7ed2-9308-a2f58732b9f0/2026-09-29T09-48-22-852Z_01a0ec90-b9c4-70f5-aa17-62e14cd05e2a.jsonl:6` | `ff3d11f3` / assistant | A owner 识别 C 已合入，A-3 前置接缝消失，需窄化当前任务 | 支持“新版本/新合入改变后续责任”的局部判断 |
| A1 | 同上 `:7` | `ae0b46c5` / toolResult | A 设计 comment #27 的权威入口和判据 | 支持角色责任与验收判据绑定到设计评论 |
| A2 | `work/native-homes/pi-deepseek-fast-01a0ec4c-85d1-7f02-9bf2-e15cb4f81b4d/2026-09-29T08-33-53-878Z_01a0ec4c-88d6-7286-903c-7d4a806c14b5.jsonl:14` | `b2d14c67` / assistant | A/B/C 合入树、冷跑和证据路径核对；临时证据已清理的局部限制 | 支持“持久评论证据与临时文件存续是两种可见性” |
| A3（早期追加） | `work/native-homes/pi-deepseek-fast-01a0ec10-47cb-7063-b87c-3091a9ce6d5d/2026-09-29T07-28-06-207Z_01a0ec10-4c3f-7130-bbce-c852c0d29a59.jsonl:35–93` | `b9067705`–`30fbb243` / mixed | 早期已读前缀之后的追加段：#218 paste 契约增量、A-3 README 三/四入口冲突、A/C/B 对“无影响/无动作”的具体回执，以及 #223/#224 投递回执 | 补齐 append 不应被文件名时间切割漏掉的 A 责任转交与共享文档后果；delivery receipt 仍不等于消费 |
| B5（早期 content-diff） | `work/native-homes/pi-glm-fast-01a0ec18-dd01-7710-8628-056a21a12e7a/2026-09-29T07-37-31-051Z_01a0ec18-eaab-742f-beef-c670a8c6bc1c.jsonl:1–78` | `01a0ec18-eaab-742f-beef-c670a8c6bc1c`–`8daa0f68` / mixed | 独立 canonical 文件的 78 行 content-diff 段：B 侧先登记 C 合入后回归点、树等价/非 docs 差异的结案判据、第二来源 e2e 证据与正文/packet 窄改 | 补齐 B 的责任关闭判据、证据可取性更正和三载体同步；不把 35 passed 外推为协作机制评分 |

DB 结构和状态为独立只读查询，不把上表片段扩大为完整原生行为结论。评论/事件的时间和身份仍以 `evidence/comments.md`、`comment-anchors.json` 及 SQLite 的 `comment_id/event_id` 为准；A3/B5 是针对早期 ledger 的追加/内容差异补读，不改变后段索引计数。除表内片段外，例如 #220、#228、#230、#237、#245、#262、#286、#289、#304、#307、#338、#366、#396、#406、#411、#413、#421、#442、#455、#473、#503、#516、#524、#536、#578–#589 的正文未因本表而宣称逐字重读。

## 未读范围

- 当前 inventory revision 中 ABC/base 的 `needs_new_read` 完整集合为 **19,399 条记录**（PR2 1,487；Issue3 2,212；PR8 1,903；Issue4 972；PR9 4,484；Issue5 4,217；PR10 4,124）。本表只判读上述 13 个原始文件中的有限片段，剩余记录未在本轮模型上下文逐条判读。
- Coordination / Issue1 另有 **1,083 条** `needs_new_read` 记录；本表只用一段根刷新片段作抽查，不能称 Issue1 后段全文已读。
- 按 `timestamp >= 2026-09-29T08:24:23` 的筛选规模是 20,433 条；这是时间筛选统计，不改变 inventory 的完整 `needs_new_read` 计数，也不能掩盖同一文件更早记录或追加记录的边界问题。
- 当前全局 inventory 有 389 个文件、27,053 条记录标为 `needs_new_read`，其中 D、D-stability、E、integration 由其他 cell/主线负责；本交付不代称其语义覆盖。
- 早期 04:24–08:24 的 176 源/11,203 行全文阅读账仍可复用；本轮补读了 A 的早期追加 `:35–93` 与 B 的 78 行 content-diff 文件。两份 08:12 canonical 路径在 final-source 缺失，但对应 early increment 原件在旧 audit 目录且已全读；缺失的是 final-source 身份/追加边界，见 `post-0824-reading.md`。

因此本报告中的“全 DB”只指 SQLite 表和事件状态已完整枚举；对原生 JSONL 的后段语义结论只适用于上表抽查片段与既有早期全读账。后段其余结论应由主线按需要补读后再升级证据等级。
