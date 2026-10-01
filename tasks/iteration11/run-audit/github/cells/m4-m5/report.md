# M4/M5 跨链审查

取证范围：`snapshot-01`，截点为 2026-09-29 08:04:30–08:04:36 UTC；运行仍在继续。已按时间顺序审读 `issue:6`、`pr:16`、`issue:8`、`pr:15` 的全部 27 个原生会话/子 Agent/转录单元（2,352 records，索引约 851 万字符）及四份 board。精确重复内容回引已读原处；逐单元范围、原生截断与图像像素缺口见 `read-receipts.json`。本报告只评价该截点可见的事实，不把进行中工作判成最终交付。

## PR #16：合并基线通知滞留于队列，旧基线 PASS 先于整合

**原文与时间。** PR #16 评论 #110（07:22:55）要求先合并已前进的 `origin/develop`，再于整合后重跑验收。`snapshot-01/braid.sqlite3` 的 `local_comment_delivery` 对 `(110, glm-12)` 为 `queued`；关联事件 `01a0ec0b-8df5-7753-b72a-2b6c4e1290f8` 的 `lifecycle=pending`，引用为 `pr:16 comment 110; read comment view 110 --thread`。同一评论给根侧 `glm-1` 的状态是 `delivered`。这只是**通知投递层**状态，并不能单独证明 worker 未通过工具主动阅读。

**实际消费核对。** PR #16 worker 原生会话 `views/2026-09-29T07-06-14-819Z_01a0ebfc-49a3-754d-8636-ff1a11344c56.txt` 的 07:22:55 至 07:49:16 期间，bash/tool-call 记录没有 `braid pr view`、`braid comment view` 或 `braid issue view` 读取 #110；原生 `user` 消息亦没有评论 #110 内容。worker 在 record 321（07:49:03）把旧基线 head `24a6ed7` 的 91 Vitest、46 e2e、平台路径 exit 0 报为全部收尾。record 330（07:49:16）才收到的是 Issue #6 正文修改摘要，未列评论 #110。record 331–332（07:49:22）主动 `git fetch origin; braid issue view 6`，从**后来已更新的 Issue 正文**读到 `develop=f6e326c`、旧 head merge-base `53532a0`、须合并并重跑；record 333–336 随即确认并执行 `git merge origin/develop`，冲突于 `docs/architecture.md`。因此可确证：评论通知未注入，worker 在旧基线 PASS 前也未实际消费该要求；但 07:49 后经正文接触并开始补救，不能断言终态遗漏。

同一交接链更早已有类似情况：Issue #6 负责人 07:06:24 发 PR #16 评论 #91 交代权威依据、职责与验收，回执对 @glm-12 为 `queued`；worker 原生 record 5 的 `braid pr view 16 --comments` 发生在 07:06:20，早于 #91，随后没有再读 PR 评论。PR 创建时的正文已含共享契约且 worker 读过，因此只能说**新增的评论交接未消费**，不能说它没有设计输入。

**后果和边界。** 旧基线 PASS 不能充当合并后验收。合并后 PR #14 的 `RepositoryMissing` 和 e2e 断言相互作用，worker 被迫再处理冲突、重跑及排障，造成整合延迟。独立 clone 的相同 `--head` 属正常交接，不构成共享物理 worktree 竞争。

**最小投递因果。** 数据库中的 worker 首个 `turns` 行 `01a0ebfc-4d9a-7112-9fa0-7760c2776afc` 为 `context_reset_notice`，从 07:06:16 持续至 07:49:15 才 `completed`，长达约 43 分钟。对应 `context_resets` 行 `01a0ebfc-4cc8-7a82-b94e-5d8df3cc5a80` 自 07:06:15 为 `interrupting`；`context_reset_events` 累积五条 Issue #6 正文修改（07:06、07:12、07:22:36、07:22:51、07:48:47），恰与 record 330 的五条摘要吻合。评论 #110 则在 `wake_batch_events` 中属于 PR #16 的 runnable wake batch（截点 `event_count=21`），自身仍 `pending/queued`，没有被本次 reset 输入消费。活跃长 turn 与两类事件分轨足以解释“正文摘要先到、评论待发”，但**产品是否承诺在活跃 turn 中强制投递评论**，须核对运行版本契约；不能仅凭这个状态称 scheduler 缺陷。修复层至少应保证验收与整合候选 head 绑定，并使基线变动在验收声明前可见；是否主动打断 worker 应依据投递语义决定。

对照该时段实际热部署的 Braid `5c957436`（hotfix02；`sources/braid` HEAD 全 SHA 一致）：`src/group/worker.rs:522-526` 的循环先 `begin_active_context_reset(active)`，仅在 `active.reset_id.is_none()` 时 `forward_running_input(active)`；`src/group/dispatch.rs:416-446` 是 running input 的实际发送路径；`src/store/mod.rs:5468-5470,5764-5772` 只在 wake batch turn 开始或 steer batch 被消费时把评论 `queued` 改为 `delivered`。`claim_running_input` 另在 `src/store/mod.rs:5689-5694` 排除有 pending invalidate 的工作项。与 run 前 `1fabd11` 的关键门禁相同。本次 worker 自 07:06 即挂 reset，故评论 wake 排队是这个版本的明确调度行为，而非单次数据库状态异常。改进应评估 reset notice 在长 turn 内是否需要更早生效，以及高影响基线变动如何在提交验收结论前进入候选检查，而非默认把每条评论强制中断。
更具体地，`5c957436:src/group/dispatch.rs:608-649` 对 `context_reset_notice` turn 在设定 reset_id 后立即返回，不再转发 active reset notice；这与 `worker.rs` 的 `reset_id` 门禁合起来，使本轮 43 分钟工作期间新增评论留在 wake 队列。与“评论丢失”相比，证据支持“排队等待 reset turn 结束”。

## M4a：设计评审真正改变了共享契约，随后仍受整合时序约束

Issue #6 负责人在 advisor 返回前先写共享契约草稿，随后依审查结果修订，因此设计书写与独立评审实际并行。原始方案在 `docs/architecture.md §7.2` 采用“分支名→数字 id→短 hash”解析，并把 commit 限于本仓库 `repo_id`。原生 advisor 的 `views/01a0ebf1-0fc5-74b9-b3bc-46486e05cad7.txt` record 35 给出可判别反例：id=16 的短 hash `0000010` 会误读成十进制 id=10；fork 不复制 commit，按仓库 `repo_id` 限制会让 fork 历史/diff 全 404。它还指出 M4a 全 viewer 的 revision 比较页和 M6a Write+ 的 PR 创建比较流在权限、按钮、选项上不能共用一个页面；REQ-4-1 的切换分支缺 UI。Issue #6 负责人在原生会话后续（`views/2026-09-29T06-51-32-078Z_01a0ebee-d16e-72f4-80c5-d2fdd59e5e56.txt` 约 records 101–112）把修正写回共享文档/packet，提交 `c54e304`，PR #16 于 07:06 接手。修复层是**设计契约**，而非让下游分别猜解析规则；下一轮判别证据应核对 fork 历史、全数字短 hash、两个比较流的不同权限与控件。

设计预演也发现 M3 种子 `commit_files` 增删数与实际 tree 行 diff 不一致：Initial commit 三文件各 2/0 而实际 3/0，feature commit 的 `README.md` 与 `main-only.md` 亦低估。更正后的 feature-search→main 差异不含 `src/search.ts`，而 M6 的 PR seed 原案包含该文件。M4a 选择让 M6 自有新 commit 塑形并保留 `main-only.md` 作为 REQ-4-1 跨分支缺失文件证人；这是有具体消费者的共享种子边界。PR #16 实现 `9242b6f` 后在旧基线 `53532a0` 上得到 91 Vitest、46 e2e、平台路径 exit 0（PR #16 评论 #122 / Issue #6 评论 #123），但 `develop` 已前移至 `f6e326c`。Issue #6 负责人另于 PR #16 #125 指出私有仓库**短 hash 直开 `/commit/:rev`** 的无泄露场景尚缺直接 e2e，旧 PASS 也未覆盖完整设计判据。其后 07:49 合并 `develop` 成 `e10ebb5`，`docs/architecture.md §9` 冲突重排 14→16；合并后 91 Vitest 通过、e2e 为 46 通过/1 失败（PR #16 native records 355–376），失败处是 PR #14 的会话态 `Access denied` 场景，截图中已登录页面仍显示 `Not found`。worker 于 08:01 的定向复跑仍见同一失败（records 390–401）；截点前无最终根因和修复，不能称 M4a 完成整合验收。

实现交接还有两个可核对的契约落差。PR #16 正文把 M4b 依赖描述为“复用 transaction commit helper”，而 M4a 已约定只提供只读 diff/history helper；这类跨里程碑承诺应以权威共享文档和实际导出接口校准，不能由 PR 摘要代替。worker 的初轮验证确实抓到并修复了 seed 导入顺序、短 hash case 缺分支 head 可达性、`rootDiff` 断言与种子增删数错误（PR #16 native records 76–323），所以旧基线 PASS 对这些已覆盖行为有意义；但 `README.md`/`src/search.ts` 的 e2e 只检查了部分代表性文字，不能证明交接评论声称的“完整内容逐字”一致。只读验证中，后端有 GET 前后 `/branches`、`/commits` 响应比对，浏览器层只比 `<li>` 数量，已有的 `rowCounts` 辅助函数未用于断言。下一轮应在最终整合 head 上核对具体内容、私有短 hash 直达、以及需要证明的存储不变式；不宜用测试名概括未被断言的范围。

## M5：角色集合纠偏与独立审计消费

Issue #8 comment #89 的 `triage+` 速记与需求冲突：权限梯子 `read < triage < write < maintain < admin` 会放行 Write，而 REQ-5-3-2/5-3-3/5-4 明说 Read 与 Write 仅可查看。PR #15 implementer 在原生工作中识别并向 advisor 核对；advisor 结果 `views/01a0ec02-f4eb-701b-b7f4-5a6f8c2f5675.txt` record 21 不仅确认显式 `{triage, maintain, admin}`，还区分“可被指派目标 ≥ triage”和“可操作元数据的用户集合”，指出 M6a 的 PR 里程碑应复用**后者**、PR 关闭另有 `{author, maintain, admin, org owner}`。PR #15 把谓词上移到共享 `permissions`，Issue #8 负责人于 #117 更正 #89，根 Issue #1 评论 #112 请求并落地 `docs/architecture.md §4/§9.15`。这是设计和实现间的有效反例反馈，阻止了跨模块的 Write 越权；下一轮应用验收须在同一仓库对 Write 断言按钮不可用且服务端 403、Triage 正向可操作，并对 M6a 分别检查里程碑与关闭谓词。

PR #15 首次交接 #115（旧 head `b797e1a`）有 103 Vitest、53 e2e，实施中 e2e 已抓出并修复“关键词防抖与标签选择竞态丢 q”和“详情变更吞错误不展示字段错误”。worker 另委派只读 explorer（`views/fea4e493-37df-4d59-8db7-7bdd6e7593b5_explorer_transcript.txt`，结论在 PR #15 native 约 record 460 后），指出输入关键词后立即刷新仍丢 URL 过滤、默认列表只显示 Open 与需求初始 Open+Closed 不符、纯数字 q 找不到新编号。worker 消费该结果，改为输入立即 `replace` URL、只对请求防抖，默认两状态并列、数字 q 可匹配编号，补边界断言至 103 Vitest/58 e2e，行为修复 head `bab2b11`；Issue #8 #121 接受并窄改 #89。初始全绿不能证明这些场景，独立审计的收益来自用需求的初态和时序反例判别，而非重复阅读既有测试。

视觉子代理（`views/01a0ebf2-864f-7546-93d1-b56815de471c.txt` record 29）实读三张参考图后明确区分：Issues 列表截图是 `No results` 空态，不能证明行内排布；里程碑选择器未展开；委派书中的 issue 详情截图路径不存在。Issue #8 将这些保留为未知，并以需求文字设计数据态和交互。这是正确的证据边界，下一轮视觉复核应使用有数据的列表/详情实际页面，而不能把空态图解释成行布局验收通过。

## PR #15：候选锚点与交接反复漂移

PR #15 先后以 `b797e1a`、`12793ac`、`ed6dff7`、`bab2b11` 作为已发布 head。worker 在 #129（07:55:49）和 #131（07:56:20）声明 `bab2b11` 上 103 Vitest、58 e2e、平台路径 exit 0，且不再前移。随后它为更新同一 task packet，于 07:56:40 提交 `ab8ead5` 并尝试平台检查 `bg023`，该 job 因 owner instance stale/abort 未形成结果；07:57:15 amend 并 force push 为 docs-only `6f272e7`，07:57:19 从这个 head 的 `git archive` 启动 `bg024` 平台检查并于 07:57:21 `subagent_wait`（PR #15 native records 568–590）。Issue #8 负责人在 08:00 的 #132/#133 读到 head 前移、但尚无新 head 的讨论结果，要求重锚并暂缓整合。**因此不是“worker 未启动复验”**；快照尚看不到 `bg024` 终态。确证的问题是声明“head 冻结”后仍改 packet，且平台检查的候选、运行中的 job 和讨论证据分离，造成负责人重复要求、整合等待。修复层是候选冻结/证据发布的操作协议：文档更新在最后一次验证前完成，若 head 再变则把新提交与正在跑的检查关联并主动在同一 PR thread 更新；下一轮以最终 head 的 job exit/完整 e2e 与 `--match-head-commit` 一致判别。

对 #132 的复验要求也应分层判断。`--match-head-commit` 必须使用最终 SHA，这是合并门禁的身份条件；但 `6f272e7` 若经 diff 证实只改任务文档，先前 `bab2b11` 的应用行为反馈不会因 SHA 变化自动失效。负责人要求更新候选锚点是必要的；是否重跑完整平台路径取决于文档是否进入构建包及既有 `bg024` 的真实结果。#132 自身也留下“确认仅文档差异”的替代证据路径。下一轮同时检查最终 diff、构建输入清单和 `bg024` 结束事件，可区分必要复验与重复排障。

## 次要过程观察

PR #15 与 PR #16 worker 都多次用 `sleep` 加 `pbb status/tail` 轮询长检查（PR #15 native records 386–393、425–434、PR #16 records 359–370），还产生 bg016/bg017/bg019 等额外等待 job。任务输入已约定普通后台任务可由原生完成消息续接，且 `pbb list` 的 `current-instance` 不能否定旧实例 job 存在。这里未见验收结果因此丢失；可观察成本是重复命令和诊断噪声。下一轮需看旧实例 job ID/instance ID 和完成事件，再决定是否复跑，而非把当前实例空列表当作失败。

Issue #8 负责人在续会话 `views/2026-09-29T07-55-59-136Z_01a0ec2b-bcd3-7fea-aee8-a42985d0ef8b.txt` records 19–27 使用 `braid issue view | sed '/^## /,$p' | tail -n +2` 重写正文时，意外丢掉 `## 需求来源` 标题，随后自行发现并恢复。多次用整个 issue body 更新候选 head，也连续触发自己的正文变动通知和上下文重建。这没有证据显示最终需求损失，但说明用正文承载频繁变化的 SHA 会放大编辑与通知成本。下一轮可把稳定需求留在正文，把临时 head/job 证据放在评论或状态条目，并核对恢复后的正文与板块原件逐节一致。
