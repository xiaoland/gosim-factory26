# 未闭合证据追查（二）：投递、原生子任务与成员恢复

截至 2026-09-28 13:26 UTC，本页只读核对源码、既有报告、官网 GitHub 归档和 WSL Sheet 保留运行库；没有修改生成应用、启停运行或执行 Factory 测试。**当前源码、旧冻结二进制和真实运行回执是三层证据**，以下分别标注。前轮关于共享契约、vision、环境及 GitHub 功能的已完成核对见 [第一份追查](open-evidence-followup.md)，不在此重复。

原始 Sheet 定位为 WSL `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/generation/runs/pi-braid--hackathon--sheet-984a08e3155e3e/workspace/official-generation/template/.factory26/20260928-025746-66feadac/`（下称 `R`）：`R/braid-state/braid.sqlite3`、`R/braid.log` 和 `R/work/native-homes/pi-deepseek-fast-01a0e7be-840e-71f2-8117-0285b9e203f8/2026-09-28T11-20-22-994Z_01a0e7be-98d2-7048-8fae-4bb61ef09772.jsonl`。查询均为 SQLite `mode=ro`。GitHub 旧/新父的原生材料位于 `runs/e20260928-completed-replay/github/source-workspace.zip` 中各自 `work/native-homes/pi-glm-fast-01a0e299-8037-70f0-affa-22ca36003df4/` 与 `pi-glm-fast-01a0e29d-8d70-7f43-a288-4027e9d8c829/`。

## 普通评论到原生输入：有成功同链，拒收后的同链闭环仍缺

**问题与证据。** Sheet 保留运行 `20260928-025746-66feadac` 的 SQLite `local_comments` 中，PR #26 评论 **391** 于 11:57:09.610 UTC 以 `@deepseek-24` 催办最终验收。`local_comment_delivery` 把同一评论对该成员记为 `delivered`，事件 `01a0e7e0-446a-7530-a3c7-1e97a32d8a33` 的 reference 为 `pr:26 comment 391; read \`comment view 391 --thread\``。`wake_batch_events` 连接批次 `01a0e7e0-44df-7700-b84b-66baf80e32df`，其 `urgent=0`，11:57:09.610 创建、11:57:14.326 消费。Braid 同成员的 `wake_batch` turn `01a0e7cb-c3b9-7711-8b9c-2d92bcf814eb` 已从 11:34:48.148 运行至 12:02:17.717；11:57 评论发生在其中。对应原生 Pi JSONL 第 62 行于 11:57:14.830 出现包含该 reference 的 **user** 消息，第 63 行于 11:57:16.457 出现 assistant `bash` 调用 `braid comment view 391 --thread`。这证明此普通评论实际进入了正在运行的物理会话，而且成员主动读取；不是仅看见 DB `delivered` 就推断模型消费。[运行中输入实现](../input-delivery-implementation.md)与当前 `sources/braid/src/group/dispatch.rs:410-436` 对应“收到 `Acknowledged` 后消费 batch”的路径。

**限制和因果。** 归档没有 Pi `steer` RPC 的原始请求/响应帧，不能将 DB 消费行冒称直接 ACK 抓包；也不能从一次被读取推出该催办全部执行。当前源码 `provider/session.rs:250-287` 区分运行中 steer 与空闲启动，`provider/pi.rs:419-432` 仅在 native 请求成功后返回；`dispatch.rs:520-539` 对未启动的 `Deferred` 保留普通批次。源码和定向测试说明设计边界，但这条成功链没有拒收与重试。旧同一 Sheet 运行 03:10 的另一个评论 **1** 留下两次 `urgent=0` 批次、两个 `started_at=NULL` 的 failed turn：`braid.log:15-17` 有两条 `Agent is already processing ... steer/followUp` 和随后 `channel lagged by 115`；最终对 `deepseek-3` 的回执为 `unreachable / provider did not start this message`。这证明旧拒收确实发生，并没有证明新路径已安全重试；不能把评论 1 与评论 391 拼成同一原始链，也不能仅凭已 `consumed` 的旧 batch 说投递成功。

**判定。** “普通评论在活动执行中可被看到”已有真实正例；“同一原始评论在 ACK、明确拒收、terminal 和重试之间不丢、不误记、不重复”仍缺证。下一次自然出现拒收时，只需保存该 comment/event/batch ID、Braid claim/steer 日志与原生 RPC 响应、Pi user 行、turn terminal 和后续同 ID 或派生 replay ID 的最终回执；无需专门重启或制造故障。Pi 接收成功和模型采纳契约分开判定。历史 #71/#78 已被读取但因分支未发布仍选旧实现，#109/#118 当时没有进入长执行，见[第一份追查](open-evidence-followup.md)和[原始契约链](../../experiment-infrastructure/cells/shared-contract-braid-causality.md)。

## 父会话 reset 后旧原生子任务：UUID 可从归档取回，现场没有消费

**问题与证据。** 官网 GitHub 来源链的旧父 Pi session `01a0e299-90fd-7652-8f9c-ac54e0f5e402` 于 11:24:54 启动 executor UUID `7befc0b1-e0d9-48a9-ba62-49a7be07756a`，11:26:02 arm 非阻塞等待。重建后的父 session `01a0e29d-9511-719a-9662-a40b1351d755` 于 11:27:55 对**同一 rebase 与同一工作树**再启 UUID `76d53282-1604-439f-9e94-ae8a1bf8ad97`，11:28:16 查询的仅为新 UUID。原始 `runs/e20260928-completed-replay/github/source-workspace.zip` 的旧/新 `.factory/session-tree.json` 各保存一个 UUID；新父顶层 JSONL 只出现新 UUID，没有旧 UUID 的 status、read 或结果消费。ZIP 中旧 UUID 只有 `_input.md`、`_transcript.jsonl`，无 `_meta`、`_output`，亦无 `work/tmp` 原生 `status.json`/result。因此旧任务终态与是否继续并发写不可证；“父 reset 后自动看见或消费旧结果”被这次现场反证。具体时间线和原生工具语义见[原生连续性核对](../../factory-subagents/cells/native-continuity.md)及[官网使用账本](../../factory-subagents/cells/hosted-github-usage.md)。

**已实现但未运行验收。** 锁定 `pi-subagents@0.56.0` 的无 ID `status` 只列当前物理 session；完整 UUID 的定向 `status` 可在共享临时状态尚存时解析跨 session 文件，但旧父的 `subagent_wait` 订阅不会自动继承。当前两个 variant 的 `factory-subagent-observer.ts:299-352` 已在新父 session 起点按同 cwd 收集 sibling home 的旧 UUID，写 `previous-subagents.json` 并在首次 `before_agent_start` 提示；仅在原生 queued/running 状态文件存在时被动观察其终态。这个源码接线不等于官网旧运行曾有提示，也不恢复或接管子进程；[原生连续性核对](../../factory-subagents/cells/native-continuity.md)只报告 `node --check`，下一次真实父重建的提示、UUID 查询、产物读取与是否避免重派均未验收。冷恢复若 `work/tmp` 消失，只能找回历史 UUID/transcript，不得写成仍运行或已完成。

**建议与最小缺证。** 在下一次自然发生的父重建中，保留旧/新父 JSONL、两个 `.factory` 索引、原生 `status.json`/result 与子产物；观察新父是否收到提示、是否按完整 UUID 查状态或直接读归档、是否消费结果再决定重派。同工作树的两个写任务已经是具体冲突风险，不需为了验证再发一个写任务。Braid 成员身份相同不使两次物理 Pi session 的原生订阅相同。

## 21,206 次唯一键错误与这次 materializing 孤儿是两个入口

**历史入口及已验证修复。** [旧归档原始计数](../member-conflict-evidence.json)在 2026-09-27 11:57:44—13:37:57 UTC 记录 **21,206 条日志错误**，不是 21,206 次模型调用。Issue #2 的旧 `glm-3` assignment 已 `blocked`，`desired_member_login` 仍为 `glm-3`，27 条历史 `direct_contact` pending；旧物化会重复 INSERT 同一个受全局唯一索引保护的名字。当前 Store `settle_unreachable_contacts` 在调度与物化事务入口将指向终态成员的旧事件/回执结算；`begin_agent_assignment` 还阻止 blocked 同成员创建新责任（`sources/braid/src/store/mod.rs:2560-2590, 3882-3990`）。在**真实旧 DB 的隔离副本**上推进两次后，27 条 pending→blocked，25 条 queued→0，12 条 assignment ID/login/lifecycle 不变，详见[逐项前后数据](termination-contact-evidence.json)和[修复单元](termination-contact.md)。这闭合了该快照中的历史待处理输入，不等于在原运行上重放并证明 21,206 条既有日志会被消除；新版本真实运行中也未见这类错误的证据由[迭代报告](../iteration-report.md)给出，其窗口不同。

**本次 Sheet 入口及源码状态。** [Sheet 收尾定位](sheet-closeout.md)证明 PR #19 在 attempt-08 冻结时有 `assignment/agent=materializing`，却无 `provider_sessions`；恢复后的冻结 09/03 二进制没有扫描它，导致 `materializing_groups=1`，即使所有工作项已关也不产生完成 receipt。当前源码 `prepare_offline_resume` 在持锁的离线恢复事务中只查**没有 provider session**的孤儿（`sources/braid/src/store/mod.rs:3060-3134`）：OPEN 工作项必须匹配原 desired member/profile/revision，先退休旧 assignment 并把其 `member_login` 置 NULL，再以 dedupe key `offline-materialization:<assignment>` 重排激活，使新 generation 可沿用公开成员名；CLOSED/MERGED 则退休而不重启成员。它与 blocked `glm-3` 的旧 direct_contact 结算不同，也不是取消唯一约束。当前 `sheet-closeout.md` 截至“修复与恢复获授权”段尚未给出此新源码在真实 08 数据库隔离副本上的前后结果、后续受控接续 `run.json/result` 或官网评分回执，因此此项标为**源码已修、此页未核到运行验证**；后续主 Agent/Sheet 恢复负责人持有验收与部署，不由本调查触碰活动运行。最小收据为隔离副本中 PR #19 前后 assignment、provider、事件/批次及唯一名查询，接续后的 `materializing_groups=0`、真实终态 result 与原 main tree 一致性。

**其它成员恢复边界。** [指派恢复单元](assignment-resume.md)已在 attempt-05 两题真实 DB 副本验证 applied reset + idle 新 session 的 blocked assignment 可恢复；attempt-06 又有新 assistant/tool 活动且未见重复 member_login 错误。这是另一条已实证的恢复入口，不代替本次“无 provider session 的 PR #19”验收。真正不可恢复的 provider 故障仍保留 blocked；旧地址事件要结算为 unreachable，不能悄悄换名或跨成员转发。

## 其余承诺的证据状态与承接

| 事项 | 此次状态 | 后续承接和所需证据 |
| --- | --- | --- |
| 全范围结束、关闭后联系、收件规则文案（T1/T3） | 当前 `local.rs:564` 的静止但范围未收敛返回 blocked；`Store::local_delivery_closed` 共用范围判据，`provider.rs:69` 已描述负责人/同串参与者/显式关注者。`termination-contact.md` 记录定向 Rust 验证和旧 DB 副本验证；源码与定向边界已闭合，不能把 Sheet 某次全关当通用证明。 | Braid 主线继续保留新运行中的结果/留存输入回执；无需重复本次源码调查。 |
| Codex reset 与普通/steer 回执 | Pi 的新投递源码与定向验证有记录；[架构审计](../../braid-architecture-audit/findings.md)明确 Codex **完整工作项 reset** 尚无端到端验收。 | Braid 主线在自然出现 Codex reset 时保留 native input、reset ID、terminal、continuation/result；勿拿 Pi 正例替代。 |
| 旧子任务、vision 采用和结果消费 | 08 GitHub vision 父实际 `read` 报告已有正例；旧 executor 跨父 UUID 消费缺证，本页已定位。03 未新增成功子委派，不能按调用次数判质量。 | 下一自然父重建由 variant observer/运行监测核对；vision 的具体 UI 结果因果由独立产品复核，不在本页重查。 |
| Collector flush / 外部 Git、PBB kill 与检查 wrapper、GH 16/100 | [第一份追查](open-evidence-followup.md)与相关 cell 已给可证边界；本页没有新原始回执。 | Collector/外部 Git 由主线运行收据；PBB/wrapper 由标准工具 cell；GH 逐需求与得分由独立 GitHub 任务，Astra 负责 token 和最小协作复审。无逐例官网评分时不做低分量化归因。 |

本页的新增原始核对仅为评论 391 的 SQLite→原生行、旧 03:10 拒收批次/日志、官网 ZIP 中旧/新 UUID 的各自索引及新父缺旧 UUID。其它已验证实现沿文内证据入口复用。原始路径均为只读证据，不是建议在活动应用上重试操作。
