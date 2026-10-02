# 主分析新增原文核实账

本账只列本轮主分析直接回读；既有Sheet主报告与前期全过程已读账作为复用来源单列，子审摘要不冒充主审原文阅读。B表示`../evidence/final-source/workspace/official-generation/template/.factory26/20260929-042409-811f18d4/`（相对full-lineage目录应为上级evidence）。

| 核查问题 | 实际回读范围 | 直接观察及限制 |
| --- | --- | --- |
| 整体材料与旧全读边界 | `../run-audit/sheet/packet.md`对应实际仓库路径`tasks/iteration11/run-audit/sheet/packet.md`；report.md全文；coverage.json/increment账结构；final DB表计数/字段与action分布 | 早期全读止08:24，D/E未起；本轮final DB有14对象589评论，不能据旧报告宣称全历史已读。仅索引不计语义阅读。 |
| 新根上下文怎样组织 | `B/work/native-homes/pi-glm-fast-01a0ec9d-9f09-7e02-a3c7-839bcd784e30/2026-09-29T10-02-28-840Z_01a0ec9d-a268-771a-8193-b6a47af56470.jsonl` L4 `e998256c`：程序测文本167672字符，回读首1800及末1700字符 | 开头按v1到v1.5列大量历史评论作为当前增量权威；末尾为#267及多条通知+正文修改。只量化可见输入长度，未把中间全部算主审全文读；具体正文由分区reader补齐。 |
| paste方案争议如何被分工消费 | final DB comments #218/#232/#235/#238/#267 全文（当前版本，created_at不等于所有文字均在初次创建已有） | D按原子性提paste；根吸收A/B/C对账确定事务、bounds、README归属；C自纠“尾扩张空转”的错误前提；基础更正插入证据不能证明删除。多方参与含真实增量，不可全称噪声。其具体当时版本仍由native阅读确认。 |
| 根怎样消费更正与无动作回执 | 上述root JSONL L6–44所有assistant文本/解释，逐条工具调用摘要（每个args显示前350字符；未将省略段标完整）。关键`73417ade` L6、`6613cb19` L12、`ab64b12d` L18、`d7615276` L24、`b3ced6be` L34、`279f942a` L42 | 先识别已在prompt的#265/#267，仍再查新回执/分支及他人正文；识别“旧C e2e零结构操作，不能证明paste路径”。L18发现`comment view275 --thread |head`只返回早期#1/#11，改定位。L24判断无需再催/无需发Braid回执；L34后来核实D正文修正与实现已落地，完成真实进展回复。此正负相邻链支持检查媒介/读取方式和停止条件，不支持把所有等待算浪费。 |

外部研究定向原文读取单列于[research-notes.md](research-notes.md)，不把研究理论作为本run的新增观察。

## 新增：透视复议与上下文折叠（主审直接回读）

- 只读 DB 全文读取 comments #355/#362/#375/#377/#451/#459/#470/#480 及 revision/timestamp；除 #470 revision=2 外均 revision=1。#355 已含 B 的真实 probe2、哨兵建议和 D 回放相容性来源；#362 先暂停一个分支、允许其它工作继续；#375/#377 发布新契约。故不能把 advisor 复议误报成首次发现该反例。
- 原生 `B/work/native-homes/pi-deepseek-fast-01a0ecca-0119-7532-a2c3-6b0a196170ed/subagent-artifacts/744ec1d7-fe82-4f37-b1f9-9a9ad33da3da_advisor_transcript.jsonl` L2 完整输入、L21 完整最终回答。输入已包含 B/D 的反例与推荐；advisor 独立核对代码、比较四方案、给反论据与边界。#375 接纳哨兵但明确不采纳新错误文案建议。这里只证明这次复议的消费，不把独立工具执行与问题首发现混同。
- 原生 `B/work/native-homes/pi-deepseek-fast-01a0eceb-17d3-7412-9829-7a68c18b95a5/2026-09-29T11-27-07-584Z_01a0eceb-2140-715b-a9b1-0455dd8fd4e4.jsonl` L53–69 完整逐条读取（正文/工具参数/回包）。L53 `bd1f3d9d` 写 #470 并 resolve 362/370；L56 `cdc0501f` 返回两 thread resolved；L57 的更新通知未说明折叠的整个范围。L61 发现最新 #470 也在 resolved thread；L62 `1a02d6be` 明确识别有效设计 thread 被整体折叠；L64 `f2bd639a` 尝试多参数 unresolve，L65 返回 unexpected argument；L66 `01f7b9ae` 分别 unresolve 成功（L67）；L68 `f227e4f2` 更正 #470 初版“随本条折叠”，L69 确认 open。这证明意图与操作粒度不符以及及时纠正；没有证明下游已因这几十秒窗口漏实现。
- #451/#459/#480 把旧原语、追加修订、调用方实际 head、文件 hash 和剩余 packet/PR 回执分开。它们支持“发布与消费是两步”，也支持小范围变更可复用未受影响接缝证据；不把每次复算一律判成浪费。
- 同次复议文字对照：advisor L21第4问称(a)(b)(c)三种保留pivot方案都有源表锁定，#375 §5转写为“保留文本/哨兵/删行”相同；#355旧分支实测删后pivots为空与此冲突。只读检索后续含“锁定/三种写法”评论，#377沿用三种相同；#378/#388/#389/#390/#397仍记录锁定边界但不重复三种枚举。该检索是有限导航，不是证明后来无人发现。主报告只认定这处可见论据转写偏离，不推测实现或分数后果。

一次宽关键词查询命中了大量后继上下文快照，输出被截断；该输出不计全文阅读。随即改为仅匹配 assistant 工具调用并定位上述同一 session，才完成 L53–69 的原始核验。
