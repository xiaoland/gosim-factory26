# continuation-03 未闭合证据追查

只读核对截至 2026-09-28 12:02 UTC 的本地/WSL 证据；后续 run 状态仍可变化。当前身份为 GitHub `pi-braid--hackathon--github-3d75045c72f1d6`、Sheet `pi-braid--hackathon--sheet-22730f82778f3a`。工作区未改、冻结应用未修、无新实验或运行干预。本页按[分析派单](analysis-dispatch.md)追此前承诺的缺证，复用既有审计，不重做 token 统计或 GitHub 产品全体验复核。

## 共享契约冲突：已读后偏离，与后续收件未到是两段不同因果

**问题。** 历史 Sheet 的 #5/#6 对 `validateEntries`、整表替换端点与旧 `validationViolation` 形状发生分叉，曾被概括成“Braid Context 噪声或通知延迟使成员没看到决定”。

**已知。** [原始投递链](../../experiment-infrastructure/cells/shared-contract-braid-causality.md)已将 2026-09-27 10:01—13:38 UTC 的 SQLite comment/event/batch 与两份 Pi JSONL 配对：旧执行时 #71/#78 未进入原生 user 输入；10:35 reset 后 11:47 的新输入含两条裁决全文，#6 随后主动读取并准确复述，却在 11:55 因 #5 分支尚未发布、旧 `develop` 已测而选择旧形状。12:36 的 #109 与 12:50 的 #118 再纠偏时，目标仍在 11:47 的长执行；两条收件 queued、事件 pending，至 13:38 无关联 turn 或新的原生 user 输入。63 条旧更新引用确实增加 Context，但关键 #71/#78 同时以全文可见。

**此次核对与缺证。** 当前 continuation-03 的新 Pi 顶层会话仍可观察到背景检查的完成通知晚于实际结果：Sheet PR #26 的 `bg012` 于 11:43:24 开始、运行 991,289 ms，原始 `/tmp/acc26-logs/n20-run-sh.out` 已写 `RUN_SH_EXIT=0`，PBB 完成消息到 12:02:13 才进入原生会话，晚于 12:01 的合并。这说明“未看到完成消息”不等于检查尚未完成；它不是历史 #109/#118 投递故障的复现。11:57 的催办 #391 发出时 PR #26 正在执行，11:57:50 的 #393 随后补进度，因此不能把该催办诊断为死锁。当前材料仍缺同一物理会话里 comment→batch claim→Pi steer ACK/拒收→原生 user 输入→terminal→重试的完整新链；[技术 T4](../technical-followup.md)已有精确核对判据。

**决定。** 不把最初旧形状选择归咎于“没读到”或 63 条引用挤掉裁决；Agent 仍须在共享契约未发布时说明依赖、PR 前核对目标分支。Braid 的责任是让普通纠偏在可接收边界进入活动成员并留下可区分收据，不能承诺模型照做。当前源码修正见[运行中输入实现](../input-delivery-implementation.md)；历史因果和新机制验收须分开，不能把实现落地当成这次运行已证明净质量收益。[token 根因报告](token-deep-03.md)另证同会话重复注入初始 Context；其成本与通知数相乘，但本页不重新估金额或把多次唤醒全部判无效。

## 原生 subagent/vision：一次明确消费，03 没有新的成功委派

**问题。** “调用少”可能是角色接线失效、成员不会用、已有负责人已覆盖工作，或子报告虽返回却未被消费；这些需要分开。

**已知。** [角色账本](../../factory-subagents/cells/usage-map.md)记录官网 GitHub 来源链三个 executor 在根会话重建前后重复承担同一 rebase，前两次终态与父消费未证，第三次 SIGKILL；官网 Sheet 所查父会话未见成功子会话。08 GitHub Issue #8 是相反的正例：[原生时间线](../../experiment-infrastructure/cells/hotfix09-cost-causes.md)显示 07:08:35 `subagent(list)`、07:08:39 委派 vision 读 PR 列表/分支比较两图、07:09:17 完成、07:09:19 查 UUID 状态、07:09:20 父 `read` 约 12k 字报告、07:11:57 随后写 PR 页面。角色发现、执行、交付及**父实际读取**已证；具体视觉事实正确入码或提高分数未证。早期 Sheet #5 也取回 vision 报告，但其方案评论早于报告完成，不能将原方案归功于子报告，见[视觉根因](vision-root-cause.md)。

**此次核对与缺证。** 对 attempt-09 两题父 `.factory26/*/work/native-homes/pi-*/2026-*.jsonl` 中 09:20—12:xx 创建的顶层会话逐条读取 assistant `toolCall`，去掉 `sessions/` 复制路径：没有新的 `subagent` 启动；GitHub 有 2 次 `subagent_wait`、Sheet 有 10 次，结果全部为无原生 async run，其中两次明确把 PBB `bg001` 当成子代理 ID。比 10:58 的[token 截面](token-deep-03.md)多出 Sheet 11:25 的一次等待，是截止时间差而非计数矛盾。03 是半成品收尾、已具 Braid owner 与现有检查环境；零新子委派本身不能判为缺陷，更不能把 `subagent_wait` 计作视觉模型调用。03 当前未见足以证明视觉报告影响最终 UI 的逐事实对照；PR #26 comment #400 自称检查了 13 张截图与 9 张参考图，但未列视觉子角色的原生委派，且该结论应按材料/需求文字另验。

**决定。** 下一独立新运行在确有图像 UI 命题时，按“相关路径与问题交给 vision → child 实收图像块 → 父读来源报告 → 决定/实现引用具体可见事实”核对，不按次数设配额。已由 Braid owner 完成的检查不再为提高子代理采用率而重复委派。历史 executor 重派的核心待证是旧 UUID 在重建父会话中能否被发现和消费，不让 Braid 接管 Pi 子任务生命周期。

## 环境排障：保留原始前提，不算成产品失败或自动可省时间

**问题。** 生成成员反复安装、启动、等待和排查可能来自真实候选变化、依赖环境不匹配、检查脚本错误或资源竞争；不能合并成“模型效率低”。

**已知与此次原始来源。** 03 Sheet Issue #3 原生 `work/native-homes/pi-deepseek-fast-01a0e799-4e92-7042-b96c-a6a3b2552582/2026-09-28T10-39-45-663Z_01a0e799-67ff-73ee-86f1-4aebeeef9e07.jsonl:26-27` 在 `/tmp/csv-verify-db23b1f` 对持久工作树 `node_modules` 做 `cp -al`，立刻得到 `Invalid cross-device link`；这是跨文件系统硬链接不成立，不是网络安装慢或产品缺陷。PR #26 的容器原始 `/tmp/acc26-logs/n20-unit-*.log` 对 Node 20.19.3 直接 `node --test *.ts` 报 `ERR_UNKNOWN_FILE_EXTENSION`，`n20-backend-test.log`/`n20-frontend-test.log` 对 glob 报找不到文件；同一候选的平台顺序 `npm install`、build/start 在 Node 20 上通过，ready 12.68 秒，开发检查改以 Node 24/`tsx` 跑通（PR #26 #393/#400）。[08 环境链](../../experiment-infrastructure/cells/hotfix09-feedback-causes.md)还追到绕开套件入口后 Chromium `Socket path too long`，短 TMPDIR 后 CSV 定向检查通过；不是 CSV 业务修复。本地 GitHub 诊断副本使用默认 Node 26 时 `better-sqlite3` ABI 失配、换 Node 22 可运行，见[冻结应用实用复现](../../github-score-diagnosis/continuation03/functional-diagnosis.md)；这只能说明本机诊断前提，不能推为官网低分原因。

**缺证与决定。** 仍无同条件串行对照、CPU throttling/OOM 或逐段安装计时，无法将七服务并行时长精确归为资源争用。区分平台 Node 20 的产品 build/start、Node 24 的开发检查、Chromium/TMPDIR 与每次 DATA_DIR 种子；只在候选、依赖、环境和断言前提相同的范围复用旧结果。`with-service.py` 的新回执可减少今后遗漏首次 exit，但不能倒推本轮节省多少分钟。下一运行自然记录运行前提即可，不为环境排障新建统一测试平台。

## Sheet 收尾与 GH 低分：分别保持证据边界

**Sheet 问题与新发现。** [11:57 截面](sheet-progress-late03.md)仍见 PR #26 检查进行。此后同一 Braid SQLite 的 `work_items` 已无 OPEN，PR #26 comment #400（12:01:16）报合并 main，根 #1 comment #401（12:01:26）交接关闭；`origin.git` 原始 `main` 为 `3fb842a46362c6c676bb2e99f92453d46f8394d9`，12:00:51 UTC merge，父提交 `3ab688f` 与实测 `cc5b876`。容器原始 `/tmp/acc26-logs/n20-run-sh.log` 为 `51 passed (15.6m)`；`n20-run-sh.out` 为 `RUN_SH_EXIT=0`，其 `accept-n20.sh` 确为 `bash checks/run.sh --skip-build ...; echo "RUN_SH_EXIT=$?"`；PBB bg012 总 991,289 ms ≈16 分 31 秒，不能与并行的其他检查简单相加。平台启动 ready 12.68 秒。最后一次读取 continuation-03 `run.json` 时 `finished_at/result` 仍为空，故“Braid 全关”与“生成归档/官网 self_funded 得分”是两道不同边界。后者交给现有接续流程，不重启或催当前运行。PR #24 关闭后遗留检查于 11:56:46 自然结束；与 #26 曾重叠，但无监测证明它拖慢 #26。

**GH 问题、已证与缺证。** 官网 `3583c4dd7e48` 的本地 `github-official/tasks/hackathon--github/status.json` 明确生成步骤完成、评分 16/100、16 通过/84 失败、功能 5/47，但 `tests=[]`，没有逐例失败位置。[独立冻结应用复现](../../github-score-diagnosis/continuation03/functional-diagnosis.md)确认组织入口要求 `link`，应用却覆写为 `menuitem`；同时注册、建私有仓库和 Issue、组织、PR 审阅合并、权限与搜索等多条真实用户路径可用且持久化。此正例反证“整体不能启动/所有写入无效”；一个可访问性违约也不能解释 84 个失败。旧来源 run 还发现注册原生邮箱校验阻断，但本次产物有 `noValidate`，不能沿用旧缺陷。这些功能差异由 GitHub 产品复核支线继续处理；本页只记录归因缺口：缺逐例身份、fixture/状态污染信息和隐藏测试权重，不从总分倒推某一 Braid 通知或工具问题的比例。

**决定。** 交付与评分分开记；继续以权威需求的角色/名称/入口作验收 oracle，失败检查变更必须回到需求判据，而非让测试适配当前 DOM。完整低分解释须有逐例证据才可量化，现阶段只保留已复现违约与可用路径。不能把 Braid 的工作项全关闭或自建套件全绿当成官网质量证明。

## 仍由其他工作流承接的事项

| 未闭合事项 | 现有证据入口与本次判断 |
| --- | --- |
| 历史 21,206 条 `assignments.member_login` 唯一键冲突 | [技术 T2](../technical-followup.md)有快照/源码因果，但没有当前版本真实修复验收；本次应用追查不重启历史生成。 |
| 根关闭绕过全对象终态、关闭后普通输入与收件说明 | [技术 T1/T3](../technical-followup.md)、[产品复审](../review.md)有产品/源码判据；需以本轮主线修复与定向验收为准，不能因这次 Sheet 正常全关便判通用边界已修。 |
| 普通消息运行中 steer 的 ACK/拒收、terminal 与 lag | [技术 T4](../technical-followup.md)明确仍缺同一会话的完整投递链；03 的“retrying 后 delivered”只证明某次收据最终变化，不等于全机制端到端验收。 |
| Collector flush 超时/重发与外部 Git 合并状态 | [09 问题树](hotfix09-synthesis.md)已列竞争解释和决策口径；本页没有新增能推翻它们的原始证据，不为本轮工具改动扩大范围。 |
| PBB 主动 kill 与 wrapper cleanup | [SVC/工具 cell](../../braid-github-minimal-review/cells/svc-cli-integration.md)按精确 PBB 1.0.5 源码说明 500 ms 升级及隔离操作；未在真实 PBB job 中调用 kill，不能承诺所有中断有最终收据。 |

本页新增的直接核对为 03 原生子代理调用扫描、Sheet 12:01 收尾的 SQLite/Git/原始检查日志与 PBB 时间、Node 20 开发检查日志、跨设备安装失败原生行，以及 GH 官网状态原始文件。其余判断按链接复用既有证据，避免把同一事实重复当多份独立验证。
