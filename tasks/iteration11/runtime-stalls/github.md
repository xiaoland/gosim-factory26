# I11 GitHub：交付进度、停滞与修复实际效果

2026-09-30 只读审查。当前判断：应用已经到达「最后一个功能 PR 经实施侧和设计侧验收、等待根合并」阶段；剩余并非 M6b 开发，而是 PR #22 合入、develop→main 整合验收及交付。最新冷接续再次在 Pi 本地 `new_session` RPC 超时，根未收到候选核对完成通知。不能把运行停滞解释为模型继续思考，也不能把 `local_run.lifecycle=running` 解释为仍有有效生成。

本报告只分析 I11 接续后产生的内容，不复做 I10 全量审计、不评分、不运行模型、应用或测试，不改应用源码。时间均为 UTC；转换中国时间加八小时。

## 证据范围与读取方式

- 完整停止现场：`runs/iteration11/20260930-completed-turn-resume/github/source/template.tar`。用 Python tarfile 只读列成员，建立临时偏移索引后仅读取所需成员，未全量解包。共 230,285 个成员；历史内容保留不等于本轮活动。未读取凭据文件。
- 最新失败状态：同目录 `evidence/first-resume-failure/braid.sqlite3`，以 `mode=ro` 查询；`recovery-braid.log` 及三个 physical 目录。SQLite 的 `local_items/work_items/local_merges` 与原生 JSONL、Git refs、应用检查日志交叉核对。
- 上下文：`tasks/iteration11/recovery-curation/github/report.md`（摘剪起点），`recovery-curation/local-observation.md`（实际路径不在 github 子目录），`report-consumption.md`、`remaining.md`、`cells/native-result-handoff.md`、`context-templates/packet.md` 与实施记录。前两份源码进度表写着“未部署”属于历史时点，不能用于断言当前未部署。
- tar 内统一前缀记为 `T=template/.factory26/20260929-042409-1202e245/`；下文 DB 指最新失败态 SQLite。native 证据路径位于 `T/work/native-homes/`；Braid 工作树位于 `T/braid-state/worktrees/`。

## 现象一：代码明显前进，最终交付尚未发生

| 对象 | 独立核到的状态 | 意义 |
| --- | --- | --- |
| PR #19 / Issue #7 | MERGED / CLOSED；`local_merges.applied`，head `56f53ae`，merge `4eb2a27` | M4b 未提交成果已收敛并合入 |
| PR #21 | MERGED；head `807748c`，merge `7a3b8ea` | M4b packet 指针跟进已完成 |
| PR #20 / Issue #9 | MERGED / CLOSED；head `1ea64ab`，merge `e5110cb` | M6a 与 M4b 整合完成 |
| PR #22 / Issue #10 | OPEN / OPEN；候选 `42b2f64a2389a4d80f70c9cbded6096e766c9ce4` | M6b 已交回并核对通过，尚未合并 |
| Issue #1 | OPEN | 根未完成最终交付 |
| origin/develop | `e5110cbba3560412b5a81163aee3e100c1803c7c` | 不包含 PR #22 |
| origin/main | packed-refs 为 `2914d2ddf2a9cc5723619fd2cef53f5b21b8c3ac` | 仍为旧交付分支 |
| local_run | `delivery_commit=NULL`，`lifecycle=running` | 无最终交付提交；running 是状态记录而非活跃性证明 |

上述 Git head 分别直接读取 tar 内 `origin.git/refs/heads/develop`、`refs/heads/braid/issue-10-m6b`、`origin.git/packed-refs`；并非复制评论中的哈希。DB 没有 develop→main 整合 PR。

候选的证据链已超出“作者说完成”：

1. 16:19:29，Issue #10 #308 发布 M6b 设计；16:23:59，根 #313 完成 A/B/C 裁决。PR #22 随后落 migration v4、评审/评论/Reviewers/合并/关闭重开实现与验收。
2. 16:51:21，PR #22 #330 发布 `42b2f64` 候选；16:51:26，#331 交回 Issue #10。源码提交序列为 `1b4a932 → 28db5e5 → 6cd1d70 → 7f0a263 → 7a883fb → 42b2f64`；最后提交按评论及原生记录只增加证据与 packet。
3. tar 内 `worktrees/pr-22/pi-deepseek-fast-g1/.m6b-evidence/verify-test.txt` 实际含 `14 passed / 194 passed / TEST_EXIT=0`；`verify-e2e.txt` 为 `152 passed (3.4m) / E2E_EXIT=0`；`verify-platform-path.txt` 为 `152 passed (3.5m) / PLATFORM_EXIT=0`。这是原始日志读取，本审查未重跑。
4. 17:08:57，设计侧 Issue #10 #332 对该 head 独立核对后明确交根合并。其原生会话 `2026-09-29T16-33-47-006Z_01a0ee03-e1fe-7121-9c3f-05eb462c77ed.jsonl` 确有后续检查、对照及交接活动，最后 assistant 在 17:09:53。DB 对应 turn 于 17:09:54 completed。不能再把设计侧核对列为尚未开始。

设计側首轮失败被保留：Vitest 分别出现 193/1、192/2 timeout，E2E 151/1 页面建立 timeout。#332 用 develop 同用例也超时、交错启动耗时与后续全绿解释负载影响；这比直接抹去失败可靠，但还不是所有未来负载都不会失败的保证。设计侧 `/tmp/m6b-verify-evidence/` 和声称的 `/tmp/m6b-verify/.m6b-evidence/issue-owner-verify-42b2f64/` 不属于完整 template 的范围，本归档成员未找到镜像；可查原生工具结果及 #332，但不能宣称所有独立原始文件均已完整归档。

**判断与行动结论：** 当前功能工作接近结束，且已有可用候选，不宜重新开发 M6b 或重做全量设计。恢复后应先让根消费 #330–#332，再核对 head/base 和最终交付门；只有实际差异或新失败才能要求候选重新取证。

## 现象二：有效模型活动已经结束，通知停在恢复边界

根最后 native 文件为 `2026-09-29T16-41-37-190Z_01a0ee0b-0ea6-7553-b9d2-9fa4a95b6845.jsonl`，最后 assistant 在 **16:50:12**。其结束内容仍是等待实施者正式交回和设计侧核对。#330/#331 在其后一分钟发布，#332 在其后约十九分钟发布；因此根未把后来出现的核对完成转为合并，是有明确时间顺序的投递/恢复阻塞，不是根面对完备证据后仍主动拖延。

DB `local_comment_delivery`：#331 → deepseek-21 为 delivered，→ glm-1 为 queued；#332 → glm-1、deepseek-22 均 queued。设计侧收到候选并完成核对，根未收到完成通知，因果链在这里断开。

最新三个 reset 均 blocked、`new_session_id=NULL`、`error=session is unavailable`：

| 工作项 | reset ID | 最新 blocked 时间 |
| --- | --- | --- |
| Issue #10 | `01a0ee24-4c3d-7151-92be-1c60fdb88c78` | 09-30 01:32:16 |
| PR #22 | `01a0edf7-0a3b-7731-be53-2eaefd2a3798` | 09-30 01:32:17 |
| Issue #1 | `01a0ee12-480e-7273-a8a2-2adac39001c9` | 09-30 01:32:19 |

最新 `recovery-braid.log` 已保留真实下层错误：**`Pi new_session RPC failed: provider request pi_rpc timed out`**。三个对应 physical 为 `01a0eff0-5a4c…`、`01a0eff0-5c87…`、`01a0eff0-68b2…`；有 context/instructions，未取得 native identity。日志另有 `Subagent reload phase 'result-prime' took 695ms`，它只证明初始化经过该阶段；695ms 本身既不能解释完整超时，也不能证明 subagent 的模型任务已启动。

**判断与行动结论：** completed-turn reset 的重新入队修复实际触发了三次新物理尝试；本地 Pi 初始化超时仍挡住有效恢复。“选择条件修好”与“运行恢复成功”必须分开。后续应在已有授权范围内解决 new_session 边界、保留原始启动诊断，并在获准接续时验收新 native identity、真实 assistant、#332 送达、根合并动作四个层级。本报告不重启、不延长超时、不改 live DB。

## 原生 sub-agent 与 Braid 成员：确实用了什么

Braid 的 glm-1、deepseek-21、deepseek-22 分别是根、Issue #10、PR #22 的责任成员；它们的不同 provider sessions 是 Braid 重建产生的会话，不是 Pi 原生子代理。PR #19 的 `subagent_wait` 四次只返回 **0 async run + 1 provider item**，这里等待的是后台检查，不能算四次原生委派。

本轮存在独立的原生委派证据：

- PR #21 15:17:50 调用 `subagent(agent=advisor, async=false)`，15:18:23 返回关于“grep 命中历史说明不等于悬空引用”的具体建议。
- PR #20 15:25:45 启动原生 advisor `d340c3f1-…`，15:30:01 `subagent_wait` 报 **1 complete + 2 provider items finished**；该任务审查分支设置页、共享断言和文档引用整合。
- Issue #10 16:13:40 启动 explorer `2e49ea53-…`，16:18:08 完成；用于 M6b 设计对抗复核。此前 advisor 调用确实失败，原生 status 有 failed，不能按配置或请求参数算作成功采用该模型。#308/#311 记录限流、401 及请求的模型未被采用；本审查没有读取或验证 API key。
- Issue #10 explorer 执行中连续调用 status（16:14:54、15:19、15:29、15:59、16:16:13），存在短间隔查询成本；不能因实际使用了 subagent 就说等待行为已经最优。

## I11 修复矩阵

状态以运行证据为准。“生效”限于列出的样本；“证据不足”不等于未部署。最新冷接续 `refresh=false`，没有把新编译的 Braid 自动等同于全部原生材料又刷新一次。

| 修复 | 判定 | 运行证据与边界 |
| --- | --- | --- |
| I11-01 共享契约/权威入口消费 | **生效（样本）** | #281–#284 将 M4b 分支/词表/架构入口明确交 M6a；#313/#322 的 M6b 裁决被候选与 #332 逐条消费。PR #21 专门修正文档悬空引用。不能外推所有契约已无分散风险。 |
| I11-02 Profile 与责任成员区分、指派目录 | **证据不足** | PR #20 原成员受阻后有新责任成员接续、PR #22 指派正确，但尚无足够因果证据证明目录修复消除了“两个 profile 当两个人”的认知问题。 |
| I11-03 重建期评论可领取/精确 ack | **证据不足（端到端仍受阻）** | #331 正常送达 Issue #10并触发核对；根的 #331/#332 仍 queued，其新会话不可用。这个失败不能直接归因于评论领取算法，也不能宣称重建期全链路已通过。 |
| I11-04 重建来源、时间线与分页 | **生效（来源标识）；其余证据不足** | 真实 physical/context.md 开头列逐项变更和“你的修改”，如 `01a0ee00-f654…`；原生会话据此识别自身正文回显。分页/活动序号理解改善缺少定向样本。 |
| I11-05 RPC 有限后台收尾/结果持久化/旧 ID | **部分生效，其余证据不足** | PR #19/20 的 provider item 等待确有完成回包；Issue #10 最后后台结果消费到 17:09:53，Braid turn 17:09:54 completed，当前样本没有提前完成。正常关闭取消、强杀 unknown、跨重建旧 globalJobId 各自仍缺充分样本，不能由正常完成推定全部通过。 |
| I11-06 resolved 评论直接读 | **证据不足；thread 粒度问题仍出现** | #324–#327 错把 resolve 当局部操作，连带折叠在用裁决，随后 unresolve 恢复，终态全部可见。说明整理语义仍易误解；这不直接否定“直接读指定 resolved 正文”的实现。 |
| I11-07 失败原文、退出值和环境解释 | **生效（有明确采用）** | #330 保留首轮 10/5 E2E 失败；#332 保留 timeout、基线对照、负载和真实退出值。PR #22 verify 原始文件可读，未用最终通过抹掉历史失败。 |
| I11-08 按需求判断修复对象 | **生效（样本）** | #313 用 REQ GIVEN 排除运行时补 seed 方案，明确批准 merge-lab；#322 区分新增 seed 暴露的全库断言脆弱性与产品实现。未把已授权窄改包装成猜评测。 |
| I11-09 停止无必要复验 | **部分生效，未完全达到目的** | #286/#298 对相同树复用证据；Issue #10 16:33 明确不在未发布候选上提前全量验证。但 `42b2f64` 仅文档/证据变化仍再跑完整套件，设计侧又完整复验并因超时多轮对照。后者有真实失败辨因价值，不能一概计浪费；总体不能宣称复验成本已消失。 |
| I11-10 文件准备/全量替换帮助 | **生效（采用）；无事故复现** | 多次正文以文件写入，根/Issue #10 原生记录及 #327 显示窄改后核读，未观察到 I11 本轮正文被意外截短覆盖。无事故不是一般可靠性的证明。 |
| R1 活动序号 vs comment 身份 | **证据不足** | 本轮交接使用真实 #330–#332，尚无触发旧误读场景的定向证据。 |
| R2 vision 末尾 length 显式不完整 | **未触发（已审查后续主会话）** | 本轮定向原生证据没有 vision length 案例，不把历史修复源码当行为验收。 |
| R3 无动作通知不反复确认 | **部分生效，仍有残余** | Issue #10 16:33 无新事实时明确不发等待评论；根自身回显也结束。但后台 bg007/bg009 到达后仍输出重复已完成摘要，Issue #10 自身正文导致数次检查/重建。没有证明是同事件重复投递。 |
| Context 第二轮模板 | **生效（渲染样本）；20%预算未触发证明** | 最新失败 physical 已渲染精简上下文与逐项来源；这只证明新模板到 physical，因 native 创建失败，不代表三成员已消费最新文本。没有大上下文降档边界样本。 |
| CLI-01～05 | **证据不足（局部采用）** | 本轮有 `--body-file`、head guard、comment view/thread 与状态读取实际使用；未逐项触发五项变更的全部分支，不给整包全绿。 |
| 冷接续 blocked reset / completed-turn 筛选修复 | **生效（重新选择）；恢复目标仍失败** | 三个带 completed active_turn 的 reset 均产生新 physical；随后全部 new_session timeout，不能标成恢复成功。 |
| Pi 启动原始错误诊断 | **生效** | 最新 log 已从笼统 unavailable 进展到明确 `Pi new_session RPC failed` + `pi_rpc timed out`，但下层超时原因仍需另一份运行设施调查。 |

当前材料不足以给某项判“部署不含”；本报告不拿本仓库最新源码与运行日志不同就作此判定，也不将缺少触发样本的项目标“失效”。明确失败的是本次恢复结果；不等同 I11 所有改动失效。

## 条件化剩余时间

**在根能恢复、#332 正常送达、候选/base 不变、没有新的产品缺陷的前提下，预计还需约 20–45 分钟有效运行时间。** 这是工作量判断，不是计划完成时刻；当前基础设施未通，墙钟完成时间无法给出。停止、归档、恢复包复制、Pi 初始化超时与等待修设施均完全排除。

估计依据：PR #22 从设计提交到交回约 32 分钟、设计侧正式候选核对约 18 分钟；本轮全量 E2E 和 platform-path 单次分别约 3.4/3.5 分钟。如今开发和设计核对已完成，剩余大致为根消费与 head/base 核对、受保护合并（3–8 分钟），整合 PR/候选全范围验收与证据整理（12–25 分钟），main 交付及根闭环（5–12 分钟）。有一定工作交叉，给 20–45 分钟范围，不按测试条数外推完成比例。

若只需相同树证据适用性确认、整合没有新差异，可能接近下界；若再遇已观察到的负载 timeout 或确实需要一轮修复/复验，则约 **45–90 分钟有效时间**。若出现新的需求覆盖缺口、迁移/合并问题，现有证据不能给可靠上界。最终官网评分不在此 ETA 内，且本审查不据阶段测试数字预测分数。

最短的下一步是先恢复根的有效消费链，复用已完成的 #332，保留 head guard，完成 develop→main 交付。当前没有支持“需要再跑一轮 M6b 开发或重启所有已完成成员”的证据。

## 后续恢复事实

10:03 CST后续恢复核验：新binary d76d65f…在保留现场接续，三会话握手约123/124/129秒后均出现真实assistant。根首个工具调用成功读取#331/#332，DB确认#332 delivered。原表中“当前受阻/queued”仅描述归档截点；恢复选择、原生身份与实际交接消费现已取得端到端证据，尚不能外推所有重建竞态和重复通知均已消除。
