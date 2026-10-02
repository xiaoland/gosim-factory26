# GitHub 内容方法论：来源与覆盖账本

2026-09-30；最终归档补取后更新。本账本区分**全量结构索引、既有语义审查复用、本次主题审读、未重读字段**。下载/索引不等于全文阅读。机器入口：[coverage-index.json](coverage-index.json)、[本段阅读回执](middle-read-receipts.json)。

## 身份与纵向范围

直接通向官网 `e68661975b53` 的生成链是 `e20260928-03-check-receipts` → 源 run `pi-braid--hackathon--github-7fe42a1248f9d8` → inner `20260929-042409-1202e245`。早期生成/暂停整理称 I10，但审查目录在 `tasks/iteration11/run-audit/github/`；I11接续保留同一 inner。不能仅按目录名排除早期过程。

`tasks/iteration10/run-audit/github/` 是另一比较前史 `e20260928-02-deepseek-direct` / inner `20260928-030347-78b10c07`，不得把相同 Issue 编号、native 或旧16分产物拼入本次直接链。

最终原始资料现已取得：`runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`，receipt确认2324文件hash全部匹配；其中 native-homes 299 JSONL、native副本214 JSONL、physical context/instructions 225套、终态DB 23工作项/352评论/724活动。**此前PR23/root终态原始来源缺口已解除**；是否已审读另看各报告，不能用下载完成替代决策审查。

## 去重与覆盖

[final-message-index.json](final-message-index.json)按 `id + timestamp + type + canonical message/data hash` 去重，保留全部完整来源路径与行号，未以basename合并。513源文件得到22152唯一记录，含session元数据及派生记录，**不是22152条独立模型消息**。`prior_read`字段表示与既有审查源文件记录签名相同，仍受旧审查排除项约束。

| 时间（UTC）/阶段 | 唯一记录及旧源差分 | 结构/语义覆盖 |
|---|---:|---|
| 09-29 04:24→08:26:12 | 9868；其中9854出现在旧审查源、14新增 | 复用[首轮账本](../run-audit/github/coverage.json)：111 canonical/9035记录，后补824新记录、12native/14turn。新14条主要是ec45在旧采样边界缺的开头，现在有来源；不虚增为旧已读。定向回读根初始化、正文整理/reset、M5冻结head变更链。 |
| 08:26:13→14:45（native实际止12:05:11，14:11为人工整理） | 7207新；170源路径 | 全段活动ordinal290–548共259行均建索引；本次读116条edit/resolve/hide候选的全部thinking/text及关键原始调用/返回；读评论150–199的语义投影，另补关键全文。详见[中段报告](middle-content-evidence.md)和阅读回执。不是7207记录全文声明。 |
| 14:45→17:09:59 | 4264新；108源路径 | 全段消息/活动及来源已索引；接续分线审读，参见主线汇总。此前#324–327的DB原文及activity已读；不能因此代替整段native。 |
| 09-30 01:58:36→02:38:30交付 | 805新；28源路径；严格02:00以后772条 | 来源已齐；父Agent负责root最终流，PR23分线负责最终实施/验收。参见[final-root-flow.md](final-root-flow.md)。本子Agent不另声称已全文审阅。 |
| 无时间戳 | 8；其中5旧、3新 | 元数据/派生记录保留，不强分时间段。 |

边界说明：native段“14:45–17:09”采用`<17:10:00`，覆盖17:09整分钟。活动索引采用同一边界，保留原始时间供复核。最后一段没有连续17:10→01:58模型消息，不能用空档推断运行状态。

[final-native-file-map.json](final-native-file-map.json)将404/513文件通过**完整native-homes相对路径**或完全相同session记录映射到Braid session/工作项；其余109为未映射派生/辅助记录，不猜basename身份。[final-collaboration-objects.json](final-collaboration-objects.json)保存23工作项、352评论、关联、session终态；[final-activity-index.json](final-activity-index.json)保存724条活动及各阶段分类。DB正文是终态版本，历史决策须回原生消息/活动时间。

## 中段实际协作变化，避免把检索命中当操作数

259活动中：68次Agent正文编辑＋6次人工recovery-curation正文替换；124条评论/回复；4个新PR及8条双向关联；3次指派、3次关闭、4次合并及4次关联合并通知；2次评论编辑、4次resolve、2次hide；另27条hidden均为人工整理。Agent正文编辑按对象：root25、Issue7 20、Issue6 10、Issue8 6、Issue9 5、PR16/19各1。

308条`middle-content-operations.json`是包含匹配命令/帮助/提及的候选，**不是308次实际写入**。16份methods投影、全7207条chronology、77大块入口均可回取，未宣称全字段已读。本主题回读长段包括near-match需求解释、scope/owner判断、thread折叠、候选/证据维护，未因其包含应用推导而排除。

## 复用与剩余限制

- 比较前史复用42唯一native/5846记录核心决策、全thinking、控制流和反馈，22工作项/94评论/218活动；6删除评论已补原操作。其6provider JSONL、27原图未重新视觉核对、机械源码排除仍保留。它不是本次直接链缺口。
- 本次不重读与上下文方法无关的全部算法源码、机械工具输出/图片；原始文件完整保留。纯自报检查结果只支持“Agent当时相信/传递了什么”，不能自动当应用正确性证据。
- 原始资料齐全后，不能继续称“PR23不存在会话”；也不能称每条协作评论所有段落均经本子Agent重读。各分线应按本回执合并覆盖，保持这一边界。
- 未发现中段仍因缺文件而无法判断的本主题关键链。未测得任何候选方法的token节省或分数改善，未证明正文长度导致最终低分。
