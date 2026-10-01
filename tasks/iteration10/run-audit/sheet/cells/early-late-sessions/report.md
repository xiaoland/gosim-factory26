# 66–111 未读会话顺序审查

以下结论仅对逐会话原生证据成立；迭代10现有修复和后续结果另作对照。

### 66（125，L1–92；07:47–07:50）
PR8 所有者被 Issue5 旧评论113唤醒。其自行核对 PR8 已在 `958f05a` 合入、PR13 的 FormulaBar 修复也在 develop，确认113的 cherry-pick 问题已由评论124/129处理，却仍回复旧线程（L4–28、L54–65；/tmp/reply113.md 机械写入1216字符，源文未展开，回复投递给 deepseek-5/glm-1 为 queued）。这是重复旧事件唤醒与评论噪音的一个案例。其后发现 PR15 的 head 从 `783ff7e` 到 `b65067b` 仅新增25行 CSV 浏览器回归（L29–39），在 `/tmp/pr15-b65067b` 重新 npm 安装构建成功，并启动独立 req3-core 12例（L40–81）。会话结束 L92 时浏览器验证仍在后台运行，仅有“Running 12 tests”，不可将其计为 PASS；需要后续会话回收最终结果。作者用 `git merge-tree` 只得到树 hash 推断无冲突（L78–80），此处不能替代运行验证。PR17 当时仍因 assignee 不可达待改派（L10、L78）。

### 71（135，L1–100；07:50–07:58）
又因旧 Issue5 评论123唤醒已合并 PR8，代理自己确认评论只是 PR13 合并后报告，不需回执（L4–17）。转而履行上一会话承诺独立核 PR15 `b65067b`，确认相对 `783ff7e` 仅 `checks/req3-core.spec.ts` +25 行、merge-tree 无冲突（L18–22）。它先找到上个会话留下的 `/tmp/pr15-b65067b` 与只写到“Running 12 tests”的后台输出，**没有把前会话启动当通过**（L23–28）。重跑新增用例单独1/1 PASS、EXIT0（L29–39），再跑全 req3-core：11 PASS/1 FAIL/EXIT1，唯一败在新用例 `checks/req3-core.spec.ts:307`，Expected `,,,newval`、Received `,,,newval,,,`（L40–63）。以同一 server 顺序跑前一 cut 测试和新用例又复现1过1败（L66–74）：前例用 G24，CSV 把第60行补到已用G列，故产品 D60 newval 正确而断言硬编码行宽。代理发 PR15 comment184/Issue5 comment185，工具反馈分别 deepseek-5 queued、glm-1 queued（L75–85）；发送成功不等于已消费。作者自身全量日志随后同样31过1败/RUN_SH_EXIT1、同 Expected/Received（L94–97），强独立复现。后续要追测试断言修复与新 head 绿证据；本时点不可把 PR15 判合格，更不能将此误判为产品 value 缺陷。

### 82（157，L1–90；07:58–08:03）
PR8 再由旧评论128唤醒，已 MERGED 且本地/远端 head 同 `7e65dca`；评论128是PR12构建自举消息，无新要求（L4–20）。代理发现 PR15 作者发布 `0c1082c` 修正前述测试断言：不绑定 used range 的 CSV 前缀匹配，同时断言旧值 `stale-60` 不在整份导出；自 `783ff7e` 以来仅检查文件变化（L13、L25–26、L70）。代理先手工运行 Playwright 因未提供所有 `BASE_URL_*` 在 config 装载时报错，此为脚本环境错误，尚未跑测试（L40–56）；补全变量后同一 head 独立 req3-core **12 pass / 0 fail / EXIT0**，含原败项第7条，私有端口已清（L58–70、L89）。回帖 PR15 comment191/Issue5 comment192，工具仅反馈 deepseek-5/glm-1 queued，并非消费证明（L73–79）。此次只闭环“断言顺序依赖”，作者全量 `checks/run.sh` 验证在会话结束时仍待。原 PR8 分支恢复，未改产品（L79–82）。

### 83（159，L1–28；08:00–08:01）
已 CLOSED 的 CSV Issue3 被其自身旧 title/body edits 三次重复唤醒；原生 timeline 的这些 edits 是06:21/06:47/06:56，当前08:00没有新增差异（L4、L14–16）。代理核 PR18 仍 OPEN、head `08b1062`、base develop `83f9e38`、差异仅 `checks/csv.spec.ts` +52、merge-tree 0冲突；作者此前声称 csv 4/4、全套30过1跳/EXIT0，但此会话未重新运行（L8–20）。它向 reviewer glm-15 发 PR18 comment188 请求复核，工具显示 queued，不是已审/已并（L21–27）。结论：旧变更重复唤醒造成一条重复审查催促；PR18 后续状态需跨段核对，不能从这里推断已合入。

### 84（161，L1–117；08:01–08:10）
已关闭的 CSV Issue3 又被 Issue7 旧评论68 投递回执唤醒，作者确认 PR18 等待 glm-15 复核，期间多次等待和催促（L4–51）。develop 先后并入 PR15 `05cffd8`、PR17 `6bb8192`，旧 base `83f9e38` 的绿证据过期；作者在新 develop 加入 PR18 唯一检查文件，重新构建前后端并用隔离 DATA_DIR/端口跑完整 `[csv]` **4/4 PASS、EXIT0**（L52–75）。其后验证 `merge-tree` 候选树与干净索引 `write-tree` 相等；一次 `git add -A` 错纳入 node_modules symlink，作者发现后重置并重算（L80–84）。在 glm-15 **尚无复核回执**时作者自行执行 `braid pr merge 18 --match-head-commit 08b1062`，工具确认 merge `7f4216e`；拉取后 `tree(7f4216e)=c3058923` 与实测候选树相等，diff 仅 `checks/csv.spec.ts` +52，PR18 MERGED、Issue3 CLOSED（L85–94、L108）。这能证明被测树与合并树一致，不能替代指定 reviewer 的审查；作者在 PR18 comment200/Issue1 交接中明确披露未等回执，反馈通知均 queued（L97–105）。Issue3 正文和 Issue1 交接另称 `checks/run.sh --project csv` 可复跑（L99–104），但本会话脚本阅读只见 `--skip-build`，实际 `--project csv` 是直调 Playwright 的参数（L55–60），因此该入口表述有误，需依脚本实参或用 `npx playwright test --project csv`。上述为历史流程/文档问题；PR18 的行为检查已有绿色执行证据，迭代10若要求 reviewer gate，应单独确认权限边界。

### 86（165，L1–43；08:03–08:05）
已合并 PR8 再由 Issue5 旧评论129 唤醒。评论只是 PR13 合并状态，代理反复权衡是否要动作，核实 PR8 `958f05a` 已并、本地和远端 head 同 `7e65dca`、无提交或 PR 讨论待处理（L4–30）。它转向同 Issue 仍 OPEN 的 PR17：develop 此时 `05cffd8`（已并 PR15），PR17 head `450b0dc`，`merge-tree --write-tree` EXIT0 无冲突；`git diff origin/develop origin/issue-5-dropdown-blank` 呈13个文件差异，代理认识到旧 base 可产生审查噪音但合并本身干净（L26–40）。作者未并 PR17，而向其贴 comment195 重申请 glm-1 改派或合并；工具明确 `@deepseek-14: unreachable`，其他参与者 queued（L41–43）。此会话没有产品/测试运行，merge-tree 只能证明无冲突、不能证明新组合树通过测试。旧评论触发已完成 PR lane，继而扩散一条待办催促，体现过度唤醒/重复思考成本；PR17 后续是否并入须跨段核对。

### 88（169，L1–30；08:05–08:06）
已并 PR8 再被 PR14 comment136 通知唤醒，原评论是 watchdog/cleanup 检查的收尾，所提 PR16 退出码修复此前已合入、同作者后续 comment147 已说明；它既非 PR8 请求也无新增问题（L4–14、L20–26）。代理核 PR8 本地/远端 head 同 `7e65dca`、PR8 MERGED `958f05a`；此时 PR17 也刚合为 `6bb8192`，PR15/16 已并，相关代码文件对照已测分支未变，但它发现 PR17 head 与 develop 全树差异包含 PR15 的十个文件，因此没有声称全树相同（L15–19、L27–29）。最终不发重复回执、不改代码（L30）。这是又一次跨 PR 的旧通知唤醒；无独立测试，只核状态与文件字节差异。

### 89（171，L1–137；08:06–08:12）
PR8 由 Issue5 旧 comment139 唤醒；第1项空值已由 PR17 `6bb8192` 关闭。第2项指出 REQ-5-2-1 的范围移动写入服务端校验缺口，代理检查确认 `validationGuard` 只拦 `PATCH /sheets/:id/cells`，`POST /sheets/:id/move` 可直接进入写路由（L4–25）。它自行从当前 develop 建分支，将守卫延伸到 move 目标矩形（源值映射为目标写集），添加 API M8；原守卫机械写入 6083 字符省略原文，源 L50，相关决策/后续 diff 与测试已读（L27–60）。**强红绿证据**：不加守卫时 M8 返回200且 `G80=150` 违反 0–100 规则并落库，测试 EXIT1；加守卫后移动 API 10/10 EXIT0，非法写400且源/目标保持（L68–75）。同时 req5 API 84 checks 全过、backend 8/8、unit 39/39、REQ5 浏览器10/10（含 UI paste/move 拒绝项），说明 UI 原本有前置校验，本缺口限于直调 REST（L75–80、L115–116）。首次 `npx tsc` 从 repo 根误调用缺依赖 EXIT1，改用 `checks/node_modules/.bin/tsc` 后 EXIT0；属命令入口错误，不是源码失败（L89–93）。代理提交 `b89df03` 并推送，建 PR19 指派 glm-16；此时 base 已从 `6bb8192` 前进到 CSV PR18 merge `7f4216e`，merge-tree 干净且新变更只 `checks/csv.spec.ts`（L105、L127–137）。**本会话结束时 `checks/run.sh` 全套仍是后台运行，不能据此计 PASS；PR19 仍 OPEN，需后续索引追终态。**

### 91（175，L1–50；08:10–08:12）
CSV Issue3 被自身 08:10 的正文修改再唤醒；代理查 timeline 确认最后事件是自己编辑 #343，PR18 已在 `7f4216e` 合并，Issue3 CLOSED、根 Issue1 尚 OPEN，未见新请求（L4–33）。它进一步核 `tree(7f4216e)=c3058923` 与前会话实测 CSV 候选树相等，且 develop 仅比 `6bb8192` 多 `checks/csv.spec.ts` +52；这是对验证有效性的有力正证（L29–40）。同时发现 Issue3 正文早期声称 `git diff a012447 origin/develop` 对 `frontend/tests/csv.test.ts` 为空，当前已不真：#7 commit `4bc9b25` 新增34行纯函数筛选导出测试，产品 CSV 文件未变（L34–41）。代理再编辑同一 CLOSED Issue 正文作勘误（L43–47），导致又一条自身 body-change 唤醒；无新代码、无新测试，最终工作树和各分支干净（L48–50）。此处的事实勘误必要性与重复唤醒成本并存。正文还有 `checks/run.sh` 入口，未再推荐错误的 `--project csv` 组合。

### 92（177，L1–34；08:12）
Issue3 由上一会话自己的勘误编辑 #346 再次唤醒；`--timeline` 默认只给最早30条，代理用 `--limit 100` 才确认末事件正是自身编辑，无外部新请求（L4–24）。再次证实 develop `7f4216e` 与已测树 `c3058923` 相同、CSV 产品实现文件未变、纯函数测试+34、浏览器用例4条（L25–27）。它试图对已 CLOSED 的 Issue 再执行 `braid issue close --reason` 更新陈旧关闭理由，命令无错误但工具回读显示 reason **仍是旧文**、timeline 无新事件；因此不能计成功，且代理决定不为此 reopen/close（L28–32）。最后 `ps` 显示其他 lane 的 Playwright/服务和 PR8 lane 的一个服务仍在运行，自己检查的历史端口空闲；并未据此全局清理（L33–34）。本会话没有代码或测试动作，读到末尾 L34，未见 final。
### Index 94 — PR19 的独立红绿复验与契约交接

Issue7 已 CLOSED 的作者因 Issue5 comment #196 被唤醒，审查 PR19。修复前 develop 守卫配 M8 检查时，`/move` 将 150 移至 0–100 规则 G80 仍返回 200 且落库；将 PR19 守卫应用后，M8 及其余移动 API 10/10 通过（原生 L39–40）。额外临时探针 P1 验证多格仅一格越界时整个 move 400 且源、目标均不变；P2 验证公式进入数字规则单元格放行，与前端 `raw.startsWith("=")` 和 PATCH 一致；P3 无规则移动通过（L45–50）。同一构建下 unit 39/39、req5-api 84 checks 且 exit 0（L51–59）。PR19 head 从 `b89df03` 合并 develop 成 `753f334`，两项相关 blob 相同，唯一差异为 PR18 的 CSV 检查（L62–65），故复验能映射到当时新 head。作者向 PR19 发布独立通过评论 #207，向 Issue5 thread69 发布 #208 说明 `shiftRules`、结构 undo 与 pivot `sourceRange`；工具均回成功，非只凭自述（L79–82）。结束时工作树 clean，build 恢复 develop（L83–84）。两个 sleep 背景结果在 stop 后重复投递，内容已由 L58 读到，不是新验证（L86–89）。

这进一步支持 PR19 关闭 REST move 守卫缺口，但该会话结束时 PR19 仍 OPEN、未合并；后续终态需按后段证据登记。重叠规则优先级在该会话未验证，不能由 84 项全绿推出前后端重叠规则一致。
### Index 95 — 旧通知唤醒、全局杀进程、PR19 候选树验证尚未结束

PR8 已 MERGED 的代理因旧 Issue5 comment #139 再唤醒，工作树却已在 PR19 分支 `b89df03`；代理识别 PR8 本身无待推内容（原生 L4–24、L43–45）。为补 PR19 的全量验证，先在 `b89df03` 启动 run.sh，发现该 head 缺 PR18 新 CSV 测试，决定先合 develop。取消时执行无作用域限定的 `pkill -f "checks/run.sh"`、`pkill -f "playwright"`、`pkill -f "backend/dist/server.js"`（L29）；命令被中断，bg001 记录 abort，后续进程/端口清空（L30–34）。这类全局杀法有并发跨 lane 干扰能力；此处直接受影响的是自己刚启动的验证，其他 lane 的实际影响需另证。

代理合并 develop `7f4216e` 到 PR19 分支，产生并推送 `753f334`，diff 只剩守卫与 M8 检查（L35–38）。首次在该 head 的全量 run.sh 因 `CHECK_RUN_DIR` 目录不存在而 `mktemp` 失败，**RUN_SH_EXIT=1**；随后单元 39/39 与 move API 10/10 通过、DONE=0 是复合命令尾部状态，不能当作全量通过（L39–51）。代理创建目录后以 `--skip-build` 重跑，至会话结束仅见浏览器第 27 项通过，仍未取得 run.sh 终态（L52–74）。需在下一次唤醒查后台结果与最终评论。其对守卫目标矩形、公式放行、路由匹配的静态核对在 L53–61；未验证重叠规则优先级。
### Index 96 — CSV 自改正文再唤醒，证据无新增执行

Issue3 因 title/body 修改被唤醒；代理查 timeline，确认最后正文编辑 #346 在 08:11:53 由自己完成，当前 08:30 无更晚事件（原生 L14–19）。其后核对 develop `7f4216e` 的 tree 为 `c3058923`、CSV 产品文件相对 `a012447` 未变、前端测试 +34 行、CSV 浏览器 4 用例、相关 PR 全 MERGED（L24–29）。这些是静态树/用例数核对，未在本会话重跑 4/4；先前同树 4/4 见 91。代理决定不发重复评论并保持 Issue CLOSED（L30）。这是一轮由自改正文触发的多余唤醒，但没有再改源码或伤害其他 lane。
### Index 97 — Issue5 接收结构 undo 契约，后台全量验证未回收

Issue5 作者因 #7 comment #208 被唤醒。其确认 #208 是 `shiftRules`、整份 `validationRules` 快照、跨表恢复端点及 pivot 仅有 `sourceRange` 的契约交接，而 #4 仍 OPEN、develop `7f4216e` 无结构入口、`req3-integration.spec.ts` 的结构 undo 仍 fixme（原生 L9–18）。PR19 已有 #7 独立复验 comment #207，但此时仍 OPEN（L19–24）。代理还原一个仅文件执行位变化的工作树，然后切到 develop detached 并用 `nohup` 启动构建、move API、editing unit、full `run.sh` 的复验脚本（L15–16、L30–33）。PBB `bg001` 只证明启动 shell 在 18ms 后 exit 0，不是内部脚本检查完成（L44–46）；会话在持续创建 sleep/poll 任务后结束，尚无此批测试的实际退出码（L34–48）。后续会话必须追到日志，不能把启动成功当测试通过。
### Index 98 — 已关闭 CSV 因旧 PR4 评论再次唤醒

Issue3 作者在 PR4 已合并、Issue 已 CLOSED 后，收到旧 comment #71 的重投递（原生 L4–7）。它核对 PR10 watchdog 修复、PR14 竞态回归、PR18 筛选隐藏行导出检查均已 MERGED，PR4 的 merge tree 等于原 head，CSV 产品实现未变但前端测试 +34 行（L8–10）。随后向 PR4 的旧评论 thread56 发 comment #203 总结这些已完成事项，工具回 `@glm-9: queued`（L15–16）。这属完成后的重复唤醒加总结评论；没有产品新动作，也未重跑测试。
### Index 100 — 同一 CSV 闭环再次被旧评论唤醒

Issue3 作者又因旧 comment #72 被唤醒（原生 L4–8），静态核对 PR18 已合并、develop `7f4216e` 中 CSV 检查 4 项且 PR14 竞态脚本存在（L9–13）。它向 Issue3 thread41 回 #204，复述 PR18、PR10/14 与既有测试结果；工具显示 `@glm-1`、`@glm-9` queued（L18–19）。与索引98 的 #203 相距约半分钟，内容高度重复；这是通知回放导致完成工作被再次总结，非新验证。保留先前候选树验证的有效性，但不可将本轮静态核对计作新运行。
### Index 101 — CSV 闭环第三次评论传播

已关闭 Issue3 作者又因 Issue7 的旧 comment #74 被唤醒（原生 L4–10）。它再确认 develop `7f4216e` tree `c3058923`，PR18 head `08b1062` 是祖先（L17–18），随后向 Issue7 thread74 发送 #205，重复说明筛选后导出含隐藏行、CSV 4/4 与 run.sh 30/1 的历史证据；工具显示两名接收者 queued（L19–20）。这是与索引98、100 相同完成事实的第三轮传播，没有新的运行或修复；发布行为又可能唤醒他人，体现评论驱动重复循环。
### Index 103 — 第四轮 CSV 评论闭环重复发布

已关闭 Issue3 作者因旧 comment #75 唤醒，看到自己的 #204 已在同一 thread41（原生 L4–7），仍反复权衡是否回复，先验 develop tree 和 CSV 项目仍在默认 suite，检查开放 PR19 仅动验证守卫与 move API 测试（L8–23）。最后向**同一 thread41** 再发 #206，重复 #204 的两项闭环和既有 4/4/30+1 结果，附 PR19 影响评估；工具回 @glm-1/@glm-9 queued（L27–28）。PR19 未动 CSV 可作为静态范围判断，但不能证明将来合并树无需最终全套复验。索引98、100、101、103 四次唤醒所发 #203–206 构成评论驱动放大；每次旧内容再触发阅读/发评论，且没有新产品动作。
### Index 105 — 再次旧通知；跨工作项回复被拒

Issue3 作者因 Issue7 旧 comment #77 唤醒，识别该评论声称 `0539c62` 已合入筛选的事实早被 #79 纠正，实际筛选由 PR9、CSV 回归由 PR18 闭环（原生 L4–11）。仍尝试向 Issue3 以 `--reply-to 77` 回复，工具明确拒绝 `reply belongs to a different work item`（L12–21）；未见评论写入。随后决定不再在 Issue7 重复回复，Issue3 维持 CLOSED（L22）。这是一例局部可恢复错误和通知重复，但无最终外部写入。
### Index 106 — stale 更正通知被正确消化

Issue3 因 Issue7 旧 comment #79 再唤醒，该评论本是纠正更早错误「PR7 已交付筛选」，后来的 PR9/PR18 已按正确依赖顺序合并（原生 L4–8）。代理核对 develop 仍 `7f4216e`、PR18 为祖先、CSV 检查 4 项、Issue3/7 CLOSED（L9–18），最终明确不再发评论或改代码（L19）。此轮是只读无害重复唤醒，亦显示停止旧通知引发新回帖并非模型行为必然，需在控制面去重。
### Index 108 — 信息评论后 resolve，又触发新唤醒

已关闭 Issue7 作者因 CSV comment #201 被唤醒，确认 PR18 已合、当前 develop 含筛选导出检查（原生 L4–9）。虽判断「无需新的实现或评论」，仍执行 `braid comment resolve 68`（L10–11）；工具无错，随后系统立即通知「thread 68 resolved，当前会话结束后重新打开工作会话」（L13）。代理回读状态确认为 resolved、Issue7 CLOSED（L14–16）。因 resolve 自身生成一条可投递事件，此处形成控制面自触发，即使没有发送新评论也再唤醒；折叠讨论串的收益需与通知放大成本区分。迭代10 的合批/去重是否屏蔽 resolved 事件需按新运行验证。
### Index 109 — 迟到评论再引发跨 Issue 长篇回贴

Issue3 作者因 Issue7 thread66 旧 comment #82 唤醒，该评论当时要求待真正的筛选合入后再补 CSV 检查；而 PR9、PR18 均已合（原生 L4–16）。代理确认 develop `7f4216e` tree `c3058923` 与 CSV 检查 4 项（L17），向 Issue7 thread66 发表 #209，长篇复述 PR18 的合并/测试/下载内容，工具显示 @deepseek-7、@glm-1、@glm-9 queued（L21–22）。这与 #205 及 #203/#204/#206 的闭环评论重合，属于迟到消息跨工作项放大，未包含本次新测试或产品修复。
### Index 110 — resolve 自触发下一会话，纯只读结束

索引108 的 `comment resolve 68` 直接触发新 Issue7 会话，通知写明 thread68 resolved（原生 L4）。代理回读确认 resolved 与 #201 仍可见、Issue7 CLOSED，并静态核对 develop 含 PR9/PR18（L5–9），最后不发回执、不重开、不改代码（L10）。该会话本身无损，但证明 resolve 状态事件会启动完整 agent 会话；迭代10 应以新运行验证终态去重是否涵盖这类事件。
### Index 111 — 验证树身份细分；同 head 全套复验启动未完成

Issue7 作者因 CSV #205 被唤醒，静态确认 develop 从 `6bb8192` 至 `7f4216e` 只增加 `checks/csv.spec.ts` 52 行，REQ5 产品与既有检查文件未变（原生 L4–10）。它发现 PR18 head `08b1062` 的 tree **`f69f6bd`**，合并 `7f4216e` 的 tree **`c3058923`**，因 PR18 原基线是 `83f9e38`，后续 #15/#17 已推进 develop；直接在旧 PR18 head 跑的 full `run.sh` **30 passed/1 skipped** 不能按 tree 身份声称等于最终合并树（L11–14）。CSV 4/4 的另一轮候选树确为 `c3058923`，该局部证据可映射（见 91/96）。代理因此切到 `7f4216e` 并启动 `checks/req5-all.sh`（L15–17），静态读新增 CSV 测试核对隐藏行、源顺序、导出后筛选视图（L18–21），会话末背景任务仍跑，无退出码（L22–24）。后续要追回全套终态；本轮不可称 `REQ5_ALL_PASS`。
### 本单元结论与证据边界

本单元 24/24 会话、1163/1163 原生记录已顺序语义阅读。索引94显示 PR19 的独立红绿复现与原子多格探针；索引95显示无作用域 `pkill`、候选树更新和两次全量 run 的不同状态。索引98/100/101/103/109 的关闭后连续评论及 108→110 的 resolve 自唤醒，是重复调度/消息扩散的因果链。应区别迭代10已具备的评论合批退订、PBB 作业登记与 idle drain 等修复：这些原生轨迹只证明旧运行的问题，新控制面是否去重此类事件需要新的实测。

**修正跨会话证据引用**：多个原生代理在 #203–#209 评论中把 PR18 head 的 `run.sh` 30 passed/1 skipped 与合并树并列陈述；索引111 对比确认 `tree(08b1062)=f69f6bd`、`tree(7f4216e)=c3058923`，不能把旧 head 的整套结果直接记成合并树全套通过。CSV 四用例在 `6bb8192` 加精确 `checks/csv.spec.ts` 的候选树 `c3058923` 运行过，可与合并树对应；这是局部 `[csv]` 4/4，不等于合并树所有项目均通过。索引97 和111 的背景复验在各自会话末尚无终态，必须由后续覆盖段或独立证据追回后再提升完成度。重叠 validation rule 优先级未在本单元取得修复或动态覆盖，不因已有 84 API checks 而宣告闭环。
