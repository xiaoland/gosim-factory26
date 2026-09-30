# I11 Sheet：交付距离与修复实效

本报告以 `pi-braid-i11--hackathon--sheet-db75cf2c3b82be` 的一致停止现场为准，时间截止 2026-09-30 08:59 CST。主线正在另行执行的单次冷接续不在这个快照内，不能拿旧现场断言新尝试成败。调查只读取归档、SQLite、Git、原生 JSONL 和已有检查产物，没有修改应用、启动模型、运行检查或评分。

## 现象：剩余主要是最终整合，关键负责人被设施挡住

Sheet 已有完整 A–E 实现集成到 develop，I11 又完成一个真实的 E2E 时序修正。当前停滞不是“还有三个大需求没做”：Issue #4 的实现及 B/E 回归已经完成，只待交付后关闭；真正持有最终验收与交付职责的 PR #13 和 root 从本轮首次恢复起就没有建立成功的 Pi 身份。main 仍是初始空树，尚未形成应用交付。

剔除设施停滞后，建议按 **45–120 分钟有效执行时间**安排剩余工作；若候选证据可复用且平台路径一次通过，可缩短到 **20–45 分钟**。若平台安装/持久化或跨域边界暴露一个真实缺陷，则约 **2–4 小时**，更大需求缺口不能凭当前检查计数封顶。这是依据剩余验收流程的条件估计，不是统计置信区间；恢复启动、握手失败、排队、无人运行的时间另计，当前不能给可靠的日历完成时刻。

## 证据与时间边界

权威原件是 `runs/iteration11/20260930-completed-turn-resume/sheet/source/template.tar`，6,446,059,520 bytes、140,549 条目；归档记录 SHA256 为 `ed9165029deeade35822b231b65e2ebd2a0d005ff5e2025c01e35786b2897e92`。本次按需读取，没有全解包；只把 SQLite、origin.git 对象和定向原生/验收记录复制到临时分析目录。原件不变。归档内共同根前缀为 `template/.factory26/20260929-042409-811f18d4/`。

| 观察面 | 直接核实结果 | 含义 |
| --- | --- | --- |
| `braid-state/braid.sqlite3` | #1/#4/#13 OPEN；#3/#5/#6/#7 CLOSED；#2/#8–#12/#14 MERGED；`local_run.delivery_commit=null` | 没有交付记录；OPEN 数不等于开发量 |
| `origin.git` | develop=`2dc4b9fdeefa52aea8e56f1f0d1284141089bf33`，main=`2914d2ddf2a9cc5723619fd2cef53f5b21b8c3ac`；`git ls-tree main` 为空 | 当前最终出口没有应用树 |
| Git 独立比较 | `d07dd62..2dc4b9f` 仅 `e2e/range-undo.spec.ts` +16；`18cfeab..2dc4b9f` **整棵树无差异** | PR14 实际合入；新 merge commit 并未改变被验候选内容 |
| `physical/01a0ee29-a557-77f2-a782-7a66a3bae251/session.json`（root）及 `01a0ee29-9cdd-7e63-849d-6b7a1cd54f21/session.json`（PR13） | failed，session ID/native ID/native path 全 null，turns 空 | 关键负责人不是模型慢，而是尚未进入可执行模型会话 |
| `recovery-braid.log` | 17:15:29Z/17:15:41Z：`Pi new_session RPC failed`，`provider request pi_rpc timed out`；随后 unavailable | 错在本地 Pi new_session 握手边界；不能定性为供应商模型 API 慢或 CPU/磁盘根因已证 |
| SQLite turns 与原生会话 | I11 17:16:03–17:32:56Z 有 28 个 completed turn；没有 root/PR13 成功 turn；最后 assistant 为 Issue4 17:32:56.804Z，正常 stop | 有约17分钟真实模型活动，之后到停止现场约7小时26分钟没有新语义进展 |

runner 在人工停止后显示 finished，不表示应用 finished；SQLite 仍保留 running 与空 delivery_commit。这两种生命周期属于不同生产者，不能互换。旧 Issue5 也有 blocked reset，但该 Issue 已 CLOSED；不应按历史错误条数一并恢复。

## 已交付到 develop 的内容，以及 I11 新增了什么

24 条 ATOMIC 需求按五个域有实现与检查：A 工作簿/CSV，B 工作表/行列，C 公式，D 范围/撤销重做，E 排序/筛选/验证/透视。上述应用实现、B 两轮回归、`d07dd62` 的四条整合 E2E 和非跳过 68 passed，均是 I10 继承成果。不能把 I11 重新读了一次报告算成新增实现或新增验收。

I11 真正新增的是 PR14：原用例看到乐观更新后的 A1=4 就按 Ctrl+Z，但撤销栈要等 PUT 返回才入栈。PR11 负责人用延长提交窗口的对照确认前序列失败、等待 Undo enabled 后通过，最终只增加 `waitForRecordedUndoStep` 及调用，未改产品行为与判据。原生 `2026-09-29T17-16-09-151Z_01a0ee2a-ac3f-71c2-9152-c2140cf9fd4d.jsonl` 保留实际操作，不只是评论自述。

`braid-state/evidence/issue-6-d/undo-shortcut-stability/` 的原始证据为：

- `probe-widened-window-result.json`：d07dd62、dirty/untracked=true，exit 1；对应日志为故意保留的旧序列 1 failed、新序列 1 passed。这个 exit 1 不是最终候选失败。
- `full-e2e-18cfeab-result.json`：精确 head=`18cfeab1a42e8b61c67676a858c9ca06c89e018c`、dirty/untracked=false、Node20.19.3、exit 0；日志末尾 **68 passed (2.0m)**，包装全过程约134秒。
- `unit-and-typecheck.log`：typecheck/backend/frontend exit 0，backend171、frontend196 passed。不能继续说 I11 完全没有新单测/typecheck 证据；尚缺的是 PR13 对最终集成候选及运行条件的明确验收接纳。
- 评论 #574 与原生 17:28:19Z 的命令显示按 `--match-head-commit 18cfeab…` 合并；SQLite local_merges/Git 真树确认 merge=`2dc4b9f`。不是只有“声称已合并”。

Issue4 的 I11 工作是消费上述变更、修正正文候选指针并维持已有 B 验收结论，不是新增一轮 B 功能开发。PR9 又追加纯文档 packet 提交至 `782770c`，不进入当前 develop 应用树。

## 剩余交付距离：需要补什么、什么不用重做

| 剩余环节 | 当前证据与缺口 | 对时间的影响 |
| --- | --- | --- |
| 最终候选证据接纳 | 18cfeab 与 2dc4b9f 整树相同，已有效覆盖新用例与单测/typecheck；PR13 正文仍滞留 d07dd62，需要负责人明确记录树相同与条件适用性 | 不应只因 merge SHA 不同机械全跑；接纳/核对约5–15分钟 |
| SKIP_FRONTEND_BUILD=1 调用 | 非跳过全量有明确新证据；未见当前候选 skip 分支完整通过记录 | 正常套件约2分钟，含启动与记录约5–15分钟 |
| 平台路径与重启持久 | 尚缺最终候选 Node20.19.3、frontend/backend 分目录 npm install/build/start、同端口服务、重启后持久化的完整证据 | 正常约10–30分钟；依赖/环境错误会拉长，但不能猜成必然缺陷 |
| 需求与跨域最终验收 | 68个本地 E2E 不是24条 ATOMIC 的独立完备性证明；PR13 明列 CSV/公式导出、验证文案、pivot三类失败等接缝，需对现有覆盖做最后核对 | 有限核对约10–25分钟；发现真实漏项才追加对应实现/检查 |
| main 合并与交付收口 | PR13 ready_commit=null，main 空树；需按实际被验 head 合并、核树/启动，关闭 Issue4 与 root，生成 delivery_commit | 正常约5–15分钟 |

上述环节有交叉，故不用逐项相加当严格工时。通常45–120分钟包括模型阅读、工具调用和一轮局部纠错；不包括另行官网排队评分。历史阶段分数不作为当前应用完成率、验收结论或预计最终分数，也不注入生成会话。

## I11 修复是否实际生效

这不是把源码完成当验收。`materials.json` 中两份顶层 instructions 摘要均为 `c2cf9e…`，与当前 I11 文件一致；advisor/explorer/executor 摘要也与当前文件一致；SVC implementation/documentation/verification 及对应 references 摘要逐项一致。因此不能笼统说“refresh只换顶层，所以其它 I11 方法没部署”：它们已在冻结基包中。相反，方法已在包内也不等于模型每次都采用。

| 修复 | 本次状态 | I11 原生/持久证据与限制 |
| --- | --- | --- |
| 01 共享契约权威与变更消费 | 证据不足 | 材料一致；本段没有新的跨模块契约决策，不能用既有v1.6交接证明新方法有效 |
| 02 profile与成员身份/指派 | 生效（局部） | PR14新建后分配 `@glm-15`，同一profile并非只有一个“人”；新Braid成员真实完成合并。尚不能推出整体排期改善 |
| 03 重建与评论领取/ack | 证据不足 | 多个reset applied且后续turn执行，评论#577被Issue4消费；未定向证明具体重建竞态及精确ack全链路 |
| 04 重建来源、分页；R1编号 | 生效（呈现与使用） | PR12原生17:16:39Z显示 `Comment 333` 与 `braid comment view 333`、页尾 `--after 741 --limit 30`，随后真实续页。不能由此证明反复翻页/推理成本已经消失 |
| 05 原生后台结果与等待 | 生效（旧结果可读）；新等待未触发 | PR9 17:19:28Z `subagent action=status` 成功读取旧run `524072e5…` complete/terminal observed；该advisor实际运行于10:50–10:54Z，是I10继承结果。本段没有新spawn/wait，不能宣称修好了全部等待时序 |
| 06 resolved单条正文 | 生效（局部） | 成员多次先thread后单条读取#562/#564/#559，单条获得正文；仍有大量 `--thread` 读取，不能说读历史成本已消除 |
| 07 原始失败与结果解释 | 生效（局部） | PR14保留probe首轮预期exit1、最终exit0、候选和环境，正确区分对照失败；不能外推所有失败都被完整保留 |
| 08 产品/检查/环境分类 | 生效（明确正例） | PR14根据可见Undo disabled与实际时序，把缺陷落在检查等待，不给应用添加无需求的在途撤销行为 |
| 09 证据适用性与停止复验 | 生效（局部），仍有过强惯性 | PR14负责人核SHA/候选后不重跑68套件；B按应用树未变复用旧证据。但#571/#574仍要求仅因merge head变更重取E2E，未利用18cfeab与2dc4b9f整树相同，仍有可避免复验风险 |
| 10 长正文文件编辑 | 生效（局部） | Issue4 17:31:13Z使用准备好的`--body-file /tmp/issue4-body.md`并回读；保留六项REQ正文，只更新候选段。此轮未见截断覆盖 |
| CLI-01～05 | 生效（本段用到的子集） | 真实使用分页、JSON、body-file、精确head合并；未触发的close/reopen等不能一并判通过 |
| R2 vision length截断 | 未触发 | 本段24个新顶层JSONL无vision调用；无新后台spawn。runtime内部补丁是否完整生效不能由材料manifest证明 |
| R3 无动作通知/同值确认 | 失效（减少重复核对目标未完整达到）；不回帖有正例 | PR9在读完无B待办的#569后仍核Git/旧advisor，最后明确不发回执；PR10 #569又复算8/8旧证据并发长“无剩余动作项”评论。Issue7多次重复翻时间线。材料含新规则，但不能认为已停止无动作复查；同时PR9/Issue4多轮不新增评论说明“无需回帖”并非完全未采用 |
| identityless offline-resume | 失效（旧现场恢复结果） | root/PR13仍无身份、blocked；这是恢复最终效果失败，不等于筛选机制没选中。新的completed-turn扩展不在该快照部署内，且Sheet两条旧active_turn_id本就为NULL，不能声称它针对Sheet补齐了遗漏 |

“生效”只表示该表限定的可观察行为出现，不是整个I11或整个修复面通过；“未触发”不等于无需继续核验。“部署不含”在此明确适用于后来的completed-turn补丁，不能把新binary的事实倒填进旧快照。

本段可见的工作者主要是 **Braid Agent**（Issue/PR负责人）；24个新顶层Pi JSONL中只见一次subagent工具调用，且只是查询I10旧advisor状态。没有观察到I11新调用advisor/explorer/executor/vision的spawn。因此不能把多成员同时醒来写成“I11 sub-agent编排成功”，更不能把旧kimi advisor结果算成本段新增高阶推理投入。

## 判断与可行动结论

先恢复 root/PR13 的真实执行能力，成功判据应是新physical绑定native身份并出现能处理当前PR13的assistant/tool行为，而非容器running、binary编译或reset短暂applied。当前单次恢复由主线操作，本报告不增加任何重试。

恢复后直接进入“补skip与平台门→接纳已适用证据→精确合并main→核交付并收口”。现有 PR14 的134秒全量检查说明数小时停滞不来自E2E本身；不要让已完成B/C/E成员继续哈希确认成为主路径。尤其18cfeab与2dc4b9f整树一致，是可复用证据的直接依据，应由最终负责人结合运行条件判断，无需为SHA字符串变化创造额外验收轮次。

还应修正认知：root/PR13正文候选仍旧并不代表没有PR14；Issue4 OPEN不代表缺B实现；main空树意味着现在还没有可称为最终交付的应用。I11已显示检查归因、证据复用、精确合并与正文编辑的正例，但恢复可靠性没有闭合，无动作核对仍然存在，sub-agent新时序和vision截断尚未取得新行为证据。

## 后续恢复事实

10:03 CST后续恢复核验：新的396538bc0dda96接续已在01:49Z取得root/PR13真实模型响应，watch显示当前仍有活动且无blocked owner。使用原binary成功恢复，没有应用本轮新启动binary，故只能证明当前恢复成功，不能将其算为新代码的验收。上述内容与效果矩阵仍以归档截点为准。
