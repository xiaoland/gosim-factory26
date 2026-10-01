# 迭代11：让共享决定和执行结果进入实际工作

2026-09-30。当前阶段：I11 两题已交付并完成最终应用的官网 self_funded 重放，GitHub 为4/100、功能1/47，Sheet 为59/100、功能8/24。原始生成、应用与评分证据保留；后续修正归入当前暂停的I12。
交付和恢复事实见 [恢复根治与进度审查](runtime-stalls/packet.md)，GitHub已有 [定向评分归因](../pi-minimal/github-score-analysis/i11-e68661975b53.md)，其发现与补充调查见 [I12评分问题账](../iteration12/i11-github-score/findings.md)。部署身份与历史现场见 [恢复记录](recovery-curation/packet.md)。
以下各实现记录保留当时的源码/验收范围；其中“未部署”是历史截点，当前是否进入运行包及是否生效由本轮修复矩阵核实，不能将源码完成视为行为有效。
I10 原始运行保持暂停；I11 与 pi-minimal 独立。

## 目标与授权

减少设计变更遗漏、重复工作和判据漂移，并消费迭代10全过程审查中影响完成度、耗时和token的根因。
用户已批准优先级1、2、3、5实施；本轮进一步批准：“我同意03、05的存在以及你的修复方案，你可以应用；然后看看I11还剩下什么未处理”。
用户另授权生成期间阶段性官网评分：冻结明确Git提交，原生成继续，只用self_funded，不将隐藏评测反馈注入生成会话。
不新增或运行Factory/Braid/SVC/设施测试或模拟探针；编译、语法核对和已授权实际运行取得反馈。源码完成不等于模型行为有效。

## 当前工作入口

| 工作 | 状态与负责人 | 依据和产物 |
| --- | --- | --- |
| 独立variant与分组 | 副本已建立，I10冻结输入保留 | [隔离边界](variant.md)、[分组优先级](priorities.md) |
| I11-01共享决定 | 主线源码完成，未部署 | [contract-change.md](contract-change.md) |
| I11-04/06协作可读性 | readable-cli源码完成，编译与审计副本只读CLI核对通过 | [readable-cli](cells/readable-cli.md) |
| I11-07/09及06重复确认 | GitHub审查负责人源码完成，语法核对通过 | [feedback-evidence](cells/feedback-evidence.md) |
| I11-03重建期间消息 | readable-cli已完成worker/store与ack边界，编译通过 | [共同设计](cells/reset-handoff-design.md) |
| I11-05原生结果交接 | 原生补丁完成，主线已接入构建缓存目标；修复RPC等待、关闭落盘与实际bundle入口 | [原生交接实施](cells/native-result-handoff.md) |
| 阶段官网重放 | 两题收齐：GitHub 4/100，Sheet 36/100；监控比赛锁过宽已修复 | [phase-replay](cells/phase-replay.md) |
| 未处理项与验收 | 02/08/10源码完成；CLI-01～05源码完成，主线持有行为验收与对照恢复点 | [remaining.md](remaining.md)、[问题账本](findings.md) |

## 完整证据入口

两题独立全文审查与约定增量均已完成，不再次扩张首轮截点。
- [GitHub报告](run-audit/github/report.md)：Pi原生记录、对象、成本与过程问题；审查会话 `01a0ec30-e24e-7d62-8863-bc0129ceb0f5`，现承担05实施。
- [Sheet报告](run-audit/sheet/report.md)：已纠正旧归因，PR8主动读取新版在根提醒之前，Git内已有部分契约；会话 `01a0ec30-e24e-7d62-8863-bc2128035b74`，已完成阶段评分入口与监控修复。
- [历史取证笔记](observations/initial-findings-notes.md)保留演进，不作为当前状态入口。

发现、机制原因、修复层与边界、源码状态、实际行为证据分别记录。完整报告已返回后直接消费，不把补目录当解决问题。
有界负责人自主完成并一次交付；仅真实决策阻塞或当前运行紧急故障即时升级，不逐条转发进度。

## 下一步与实验边界

03/05源码及接线核对完成；已完成CLI-01～05实现及实际只读核对，见cli-parity/implementation.md。I10当前运行故障仍独立P0处理，不等待I11。
所有进入I11包的共享Braid/SVC/原生runtime版本须明确；包构建不代表已部署或已启动新实验。
Sheet问题前尚无确认的一致早期checkpoint；现有晚期故障归档不能冒充早期状态。组织新对照前说明可恢复起点和可比性，不混用Git、数据库和原生会话的不同时间点。
阶段评分属于I10应用快照，既不验证未部署的I11修复，也不等于最终应用成绩。每题最终交付仍独立冻结并官网self_funded评分。

## 本轮02与08/10

用户授权02直接修复：指派目录/help/回执已修改并编译通过，见[cells/assignment-choice.md](cells/assignment-choice.md)。08/10已获批准并实施，详见，见[cells/decision-and-edit-proposals.md](cells/decision-and-edit-proposals.md)。10纠正-F误用归因；已证问题是失败的shell正文构造仍被写入。

本轮08/10批准并已实施，见[cells/decision-and-edit-proposals.md](cells/decision-and-edit-proposals.md)。新增[CLI对齐复核](cli-parity/packet.md)已完成两个独立清单→对比，用户现批准CLI-01～05实施。

CLI复核已完成：见[comparison.md](cli-parity/comparison.md)。优先建议关闭语义、列表查询、JSON公开字段一致性；PR创建与指派属于产品边界，不直接套用gh。用户已授权CLI-01～05实施，06/07保留产品边界。

## I10成果接续准备

用户已要求暂停I10并保留成果，以整理后的副本准备I11；当前不启动实验。详见[recovery-curation/packet.md](recovery-curation/packet.md)，两题分别委派整理，原始证据不改。

## 报告消费复核

用户要求核对其报告及两份run analysis的I11未完成项。见[report-consumption.md](report-consumption.md)：01–10/CLI已有源码，但时间线活动编号混淆仍有界面缺口，vision截断返回契约待核，无动作通知循环仅部分覆盖；remaining.md已重写，不能宣称只剩实验。

R1～R3本轮处理完成：R1活动/评论身份已修；R2原生length被误报completed的共同返回逻辑已修并接线；R3通知读取入口及无待办处理指引已修，保留原订阅/投递语义。编译/补丁应用/语法或真实只读核对完成，未启动模型/恢复I10/部署I11。详见cells/r1-timeline-identity.md、r2-truncated-result.md、r3-notification-work.md。

## 上下文模板精简（已批准实施）

用户提出上下文/事件消息排版与信息精简，已整理源码入口、I10实际样本和方案，见[context-templates/review.md](context-templates/review.md)。用户已批准简化并明确不显示createdAt/updatedAt；源码实施与编译、归档对象只读核对已完成，见[实施记录](context-templates/implementation.md)，未部署或恢复实验。PR先呈现，关联Issue完整内容保留，按需读取替代完整内容不在本轮变更。

上下文第二轮用户已批准并完成源码实施：成员按需CLI查询、PR只带OPEN关联Issue正文、resolved整树折叠、模型窗口20%估算token分档、根检查整理讨论。当前依据见[第二轮实施](context-templates/second-pass.md)。仅编译/语法与归档实际只读核对，未部署；I10保持暂停。

## 本地可行性验证（2026-09-29，已授权）

用户在pi-minimal仅跑GitHub、自有供应商key、前20分钟每5分钟取工作区检查Pi会话的范围上追加：“好的，还同样的方式启动并监控i11”。
采用最新 `pi-braid-i11` 从I10 GitHub摘剪副本接续单题；保留已有代码、Git和未提交成果，精简旧协作噪声并重建原生上下文；原I10容器与原始归档不变。本次是接续可行性验证，不是从零生成对照。无官网提交、无本地评分。
模型沿用I11配方，使用用户BigModel/Kimi/DeepSeek凭据，经已有本地网关路由，禁止ARC key或参赛额度。
构建由readable-cli从当前Braid脏源码独立快照进行，产物 `runs/iteration11/20260929-feasibility/runtime`；主线冻结ZIP、启动、记录run身份；运行前20分钟每5分钟归档下载工作区并审读会话。
观察除模型/工具/技能/原生子代理外，还关注Issue/PR协作、上下文简化与重建是否正常；未触发行为标为未验证。

供应商核对：BigModel和Moonshot models接口确认GLM/Kimi配方名存在；DeepSeek models接口只列deepseek-flash、deepseek-v4-pro。官方说明旧deepseek-v4-flash与deepseek-v4-flash-vision-exp仍接受，但实际服务已由V4.1-Flash承接（https://www.deepseek.com/en/news/deepseek-v4-1-flash/）。不改I11配置名，记录此可比性限制。

起点纠正：用户再次提醒既定I10摘剪方案，主线确认尚未启动I11。analytics_executor负责仅修改GitHub可编辑副本的对象正文/评论；final_product_methods负责现有恢复入口I11兼容与材料刷新；readable-cli构建最新runtime；主线集成并启动。原先仅完成归档与摘剪建议，实际裁剪尚待本轮落地，不能将计划当作已有成果。
