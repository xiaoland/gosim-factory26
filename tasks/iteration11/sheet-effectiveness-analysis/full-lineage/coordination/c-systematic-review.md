# C（Issue5 / PR10）后段系统语义复核账

## 复核口径

主线生成的 `full-lineage/semantic-streams/C.jsonl` 是按 inventory `needs_new_read` 提取的 assistant prose/thinking 与工具导航流；它保留原始 path/line/msgID，但工具参数只截取导航前缀，工具结果仍以原 JSONL 为准。该流本身不是全文语义阅读。

本轮按 **103 个 native/session 文件、3,270 条 assistant 流记录**浏览各会话最后答复，按时序批次回到下列关键原文；C 流约 5.30M 字符，未把全文灌入上下文。实际补读了 A 早期追加 `:35–93` 与 B 早期 content-diff 78 行，见 `semantic-excerpts.md` A3/B5。

## 时序决定、纠正和责任转移

下表时间用于导航session/处理阶段，不是所引用最终答复内每个事实的发生时间；长session的最后答复可能回顾后续事实。尤其`ed72f89`发布在11:25–11:26附近，不能据11:12开始的载体把发布提前。严格事件顺序以原JSONL消息timestamp及comment created_at为准。

| 时间 | 原始 path:line / msgID | 语义结论与责任变化 |
| --- | --- | --- |
| 08:12–08:36 | `work/native-homes/pi-deepseek-fast-01a0ec4c-81ff-70b2-bc23-9da9c3560624/2026-09-29T08-33-53-040Z_01a0ec4c-8590-7193-8683-7427aec61aab.jsonl:68`, `db1a4484` | C/PR10 已在 `a592c3e` 合入，Issue5 只等 D 的两条端到端回归；恢复通知和 merge 状态重复唤醒，不能补造缺失原生判断。 |
| 08:49–09:00 | `work/native-homes/pi-deepseek-fast-01a0ec61-832f-7312-b888-dda83bdcc9b3/2026-09-29T08-56-49-452Z_01a0ec61-862b-76e3-a9dc-8972c95dd8a0.jsonl:70`, `aaa55c7b` | C owner 用 Node v20 探针固定 D 消费的四值/接口入口，Issue5 正文把 D 负责人、关闭前提和 cut/move 解释疑问写入导航；D 仍负责裁定。 |
| 09:36–09:41 | `...01a0ec85-f80c.../2026-09-29T09-36-37-900Z_01a0ec85-f80c-74d1-b0ae-86026421d7e9.jsonl:96`, `ce3e95a4` | 根 #216 裁定采用读法②：move raw 文本原样写入、仅重算；copy 才执行整式 `=#REF!` 塌缩。C 在 `a592c3e` 上确认悬空显示 `0`，发 #217，剩余责任交 D。 |
| 09:48–09:52 | `...01a0ec89-c80c...jsonl:100`, `cfaa3389`; `...01a0ec91-dcf7...jsonl:85`, `d70da1e6` | D #11 交接绑定 post-expansion bounds；C #222/#227 说明 paste 对 C 无接口改动，但纠正 `rewriteRefsOnInsertDelete` 的尾扩张前提：尾索引引用并非一概空转。#232/#235 将裸 `UPDATE row_count/col_count` 设为硬约束，D 需消费。 |
| 10:00 | `...01a0ec99-450d.../2026-09-29T09-57-42-797Z_01a0ec99-450d-706d-851a-0d99718b5a93.jsonl:77`, `63ce4c8b` | C 识别 #260 纠正：`formula-engine.spec.ts:276` 是零结构操作的无变更基线，不能当 tail-expansion 覆盖；就地窄改 #256/#PR10，保留 #247 结构路径缺口给 D/E。 |
| 10:01–10:08 | `...01a0ec9b-cc6f...jsonl:56`, `43e70325`; `...01a0ec9c-6f26...jsonl:119`, `a8bd027d` | C 继续收窄正文措辞，将“持久原文损坏但当前套件不检测”写入 #259/#271 证据链；D PR11 尚 packet-only，C 端两条 e2e 仍是明确阻塞。 |
| 10:23 | `...01a0eca3-97b1.../2026-09-29T10-08-59-313Z_01a0eca3-97b1-72eb-9b4e-5d0325041583.jsonl:196`, `07922d7b` | D 候选 `bdb457a` 层面 C 复核：自写 e2e 5 passed、完整套件 45 passed、四个 C 探针 exit 0；#247 §1 仍缺，回交 #293 明确由 D 补 e2e/README，C 等 develop 树等价。 |
| 11:12–11:18 | C stream 最终答复 `...01a0ecdd...jsonl:72`, `ae5989e8`；`...01a0ecdf...jsonl:95`, `2823289c` | E/row-permutation 原语出现 RT 口径和 `ed72f89` 修订；C 独立复核区分“提议端点混合绝对引用”与已提交 position-self 行为，并保留唯一退化构型，后续由 E/整合消费。 |
| 11:41–11:54 | `...01a0ecf3...jsonl:104`, `de01da3b`; `...01a0ed03...jsonl:46`, `c1f3862b` | PR12 `ca69b7b` 合入后，C 7 目录重取/第二来源复核完成；7×4 sha256、rerun-postmerge 和接口冻结均记录，责任从 C 交给 PR13 最终整合。 |
| 11:56–12:05 | `...01a0ed03...jsonl:71`, `d113d9f0`; `...01a0ed0b...jsonl:72`, `326915bc` | C 清理已结束 thread，只保留 #107/#306/#325 等权威入口；PR10/Issue5 正文按 `d07dd62` 当前树收窄，未将历史候选当终态。 |
| 17:18–17:20 | `...01a0ee2a...jsonl:66`, `b4689456`; `...01a0ee2c...jsonl:48`, `30f24cb2`; `...01a0ee2d...jsonl:21`, `36286e93` | PR13 门禁接手最终覆盖；C 仅核对合入树增量不触四个冻结接口，Issue5 已关闭，C 无在途动作。 |

## 实际新增评论/载体的责任链

从最终答复与 source native 回包中核对到的 C 侧写入/纠正标题包括：#205（归属更正）、#212/#213（D 消费入口与探针）、#217（读法②确认）、#221/#226/#227（D seam/bounds）、#232/#235（尾扩张硬约束）、#249（请求 D 维护正文）、#256/#263（#260 测试覆盖范围纠正）、#271/#274（#259 原语证据）、#293（候选层回交）、#524/#528（PR12 触发协议及就地更正）、#532/#534/#536/#537/#538/#541（7 目录重取和耐久性）、#547/#549/#568/#569（PR13 交接、终态窄改）。这些标题和责任变化用于补足 report 的行动流；不把评论已写入等同所有 recipient 已消费。

## 未细读边界

- C semantic-stream 的 3,270 条 assistant 记录中，本账系统浏览了每会话最终答复和上表关键时段；没有把全部 5.30M 字符逐字放入上下文。
- 4,017 条 C toolResult、3,263 条 read-like bash 及约 577 条 mutation-like bash 候选仍以导航/最终答复筛选；精确命令输出、未形成决定的重复查询和纯日志没有逐条语义复述。需要核验具体 mutation 时，必须按表中原始 path:line 回原件。
- 因此本账支持“C 侧后段新增决定/纠正/责任去向”的有界结论，不宣称穷尽所有 assistant 中间思考，也不将 D/E/整合 owner 的原生消费升级为已读证明。
