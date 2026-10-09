# I14 组合版 GLM-5.3 根任务完整 GitHub

用户 2026-10-06 原话：“还另外启动启动 GLM-5.3 作为 root issue agent 的 I14 组合版运行（本地跑完整 github，稍后官网重放取得测评结果）”。授权本地 fresh 完整 GitHub 生成，后续冻结应用以官网 self_funded 重放独立评分；隐藏评分不回流生成。owner `/root/i14_glm53_full_github_owner`。不控制在途 Pi/I14 Stage2。

复用 pi-braid-i14-reviewer-cleaner-e2e 派生只读远端完整包卷，直接 Docker，不调用 Lab/SDK/admission。已有 pi-glm-root profile + MODEL=glm-5.3 只选择 root/high；普通、reviewer、visual、cleaner/e2e 保持 Flash/high；advisor K3/high、executor/explorer DeepSeek 原配置。新独立 gateway-routes 加 GLM-5.3 千帆个人 TokenPlan→千问现有 API，本地凭据已有，不用 ARC。配置存在尚不证明真实模型请求成功。

原 Braid-owner v2 昂贵模型预算完整保留：GLM-5.3 和 K3 在 restricted 集合，一次运行只有一个 Braid agent_id 可永久认领；根 GLM 与根内部 K3 同 owner，其他 Braid 成员 K3 原 guard 拒绝。各 run 独立预算目录，不复制旧状态，不放宽限制。

sfp7 available 14.06GB、磁盘118.93GB，仅旧 I14 Stage2 容器运行；新增4GiB/no extra swap、2CPU、512pids、12h timeout。公开完整需求沿旧 full GitHub `/home/yyh/factory26-deadline-20261003/overlays/requirements`，无前阶段应用输入。新 output 从空目录起。Mac产物仅 WorkSSD，远端运行允许。

启动后放手，无监控/heartbeat/自动官网派发。实际生成结束后等用户进展查询，冻结 exact application commit，再独立官网重放。无测试、无 git commit/push。

## 实际启动回执

2026-10-06 20:58:49 CST 容器 `3968e53cb5cc086a89ee52edeae3b10f5fe387aae7e4e192d7b8656f8f103e3c` 运行，名字 `f26-i14-glm53-root-full-github-20261006`，Braid run `20261006-125849-7a406ace`。实际 Python/collector/Rust gateway/Braid/Pi 齐全，stderr 空。braid-request 明确 root_profile_id=pi-glm-root、root GLM-5.3/high；pi-glm-fast 与 reviewer 都仍 Flash/high。预算软链 owner `01a1114b-9c95-7cb0-b307-9d9105531b3b`。

真实 GLM-5.3 千帆 TokenPlan 请求已经 HTTP200 并收到完整响应，request7 terminal complete；配置可用已由本运行实际反馈确认。完整公开需求根为REQ1至REQ6，无旧应用。新远端 `/home/yyh/factory26-manual-glm53-full-github-20261006`；来源完整材料只读，只有 gateway-routes 配置文件的新增 route 在本 run 私有 bind 上覆盖，无公共源码修改。旧两条 run 没有操作。

证据 `runs/iteration14/glm53-root-full-github-20261006/startup-receipt.json`、`startup-gateway.log`、`input-sha256.txt`、`run.sh`、`gateway-routes.json`。现在放手，无持续监控或自动重放。

## 2026-10-06 21:56 CST 用户进度查询

仅一次有界只读，无控制或新派发。run仍running、无exit、stderr空、delivery未关闭。共享设计已发布270b3f2，PR2基础脚手架/共享契约/开发反馈设施已ready，候选48d355d，reviewer-1正独立验收；REQ1-6业务PR尚待实施。原生累计246工具调用。GLM5.3 66次HTTP200、K3 11次200、Flash145次200；千帆发生GLM3次/Flash8次429，Flash最近429均Ark接管200 complete且后来千帆也恢复200。原始gateway保留，不概括为没有HTTP错误。当前无有效最终app，不冻结、不官网重放；已停止主动跟进。证据status-20261006T2156+0800.json。

## 2026-10-07 用户进展查询

本次一次只读 Docker 精确容器核对：3968e53c...已 Exited，ExitCode137，OOMKilled=false；原控制agent.exit亦137。实际终止为2026-10-07 08:59:49北京时间，原启动20:58:49，匹配冻结run.sh的43200秒timeout+60秒强杀。delivery.json为failed/运行终止信号，没有有效最终应用或官网评分。stderr7字节，未把退出误称完成；未启动恢复、控制或模型运行。快照 runs/iteration14/glm53-root-full-github-20261006/progress-current.json。

## 2026-10-07 接续授权与实际入口

用户原话：“接续 GLM-5.3 root，继续完成（前面不是分析说有7个多小时因为上游供应商问题所以停滞吗）”。本次 owner `/root/glm53_recovery_owner`。该 7 小时停滞分析来自另一 Flash-root Stage3，不能套用于本 run。终止现场表明 PR2–7 已合入 develop，10 个历史 reviewer 请求均结束，PR8 为 draft、Flash turn 在原 12 小时截止时 running，root 为 idle；尚未完成最终交付。

采用同一 run 原生接续，保留 output、bare origin、worktrees、SQLite 和各 native home/session，不重头生成，不注入 I15 提示词或隐藏评分。原冻结 Braid binary 已支持 `local --offline-resume`，保持原 binary；旧冻结 Python entry 没有恢复参数，使用已存在的当前 I14 entry 在本 run 私有挂载覆盖。唯一兼容差异是旧 fresh run 没写 initial_application_commit：本入口硬性限定 stored seed 为 807b2d9284ad78303a4057c7c870d72778ade508，并已核实保留 input application HEAD 与 stored seed 相同，不能凭缺字段放过其它运行。不修改通用恢复实现。

原容器退出、Pid=0，已核实无其它在运行容器以可写方式挂载该 output。旧控制收据保存到远端 control/original-terminal；entry 自动保存 run/recovery 下旧控制证据。GLM 5.3 链按用户已授权调整为千帆 TokenPlan→Ark Coding Plan→Qwen TokenPlan→普通 Qwen；Flash、K3、DeepSeek 全部保持该 run 原冻结链。只向原 catalog 增补两个 GLM deployment，未替换其它模型定义。昂贵 session owner 限制仍保留。

第一次恢复容器 d963aed52fd51443cc8dc378b9c9a32c6a024782fbe16a252e0ea9a55475840e 于 15:08:21 启动，但原冻结 Python model_proxy_prepare 的三跳限制拒绝四跳链，未启动 Braid/native、未请求模型。失败现场保存在 control/failed-resume1 与 run/recovery/20261007-070821-06c97a00；已停止失败入口并重新取停止收据。采用现成四跳 prepare helper 与 Linux proxy（来源 provider-model-config-20261007 的 resource-alias-fix delivery），没有新增功能。

第二次恢复容器 b3765f7c48528c729dd9a6ab856377c695cd3a0ee3101a3edddc488347b8222a，名字 f26-i14-glm53-root-full-github-20261007-resume2，于 15:09:50 北京时间启动，同 Braid run 20261006-125849-7a406ace。4 GiB/2 CPU/512 pids 沿用原资源，无 timeout、人为费用或运行停止线。gateway 已 ready，Braid 已启动原 Pi 会话；实际模型与语义进展待下次启动回执核对。

入口和原 catalog/route、配套 binary 的 Mac 证据位于 runs/iteration14/glm53-root-full-github-20261006/recovery；全部 WorkSSD。成功启动后放手，后续用户进展查询取快照；实际生成完成后冻结 exact 应用，独立 self-funded 官网 self-test，评分不回流生成。

15:11 启动核对完成：GLM-root 与 Flash 的实际千帆 HTTP200/terminal complete 均已返回；PR8 已读取保留任务包、核实未提交实现，开始修复当前两处 TypeScript 类型错误，确认已有 5 份 e2e 文件。pending_resets 已从 1 降至 0，active_turns=1，stderr 空。原 Braid responsibility 与昂贵 owner 身份保持；offline-resume 对中断工作使用 replacement physical session，PR8 新 native session 为 01a11532-b708-73fc-92a7-0ac4acd4aa72，旧会话档案仍保留，不能声称每个 native ID 都不变。启动回执 recovery/resume2-startup-receipt.json。现在放手，不继续轮询。

## 2026-10-07 15:25 用户进展查询

一次有界只读：恢复容器仍 running，run.json=generating/braid，active_turns=1，PR8 仍 draft，PR2–7 已合入。原生最新进展为应用 Vitest 后台 job 因默认 300s 限制于 15:24:45 timeout，执行者已自行改为逐文件诊断；没有把此应用验收 timeout 当作供应商停滞。恢复后 gateway 未观察到 HTTP错误，最近 Flash 千帆仍完整响应。delivery.json 中三跳 guard failed 是第一次失败启动的旧回执，不代表当前失败；delivery_closed=false，尚无有效最终应用与评分，故不冻结/提交。未干预、未持续轮询。证据 recovery/progress-20261007T1525.json。

## 2026-10-07 16:11 用户进展查询

一次有界只读：容器仍 running，run=generating/braid，active_turns=1，PR8 仍 draft。PR8 已进入 REQ6 e2e 验收：保护规则 4/4 通过（Agent 应用自验），reviewer picker 失败为 getByLabel("Search") 匹配两个节点的 LOCATOR_AMBIGUOUS，Agent 正核 Dialog 及 locator 接口。模型曾千帆 Flash 429/token_plan_person_rate_limit_exceeded，发生 Ark fallback，最近请求234又经千帆完整返回；不能说没有HTTP错误，也不是持续供应商阻塞。delivery_closed=false，没有有效最终交付与评分；旧 delivery.json failed 三跳回执仍是历史启动错误。未控制或持续轮询。证据 recovery/progress-20261007T1611.json。

## 2026-10-07 16:28 用户进展与题目查询

本 run 是初赛完整 GitHub REQ1–REQ6 从空应用一次生成，不是决赛 evolution，也不是当前 I15 stages。一次有界只读：仍 running/generating，PR8 draft。Agent 的 REQ6 reviews e2e 5/5 通过，已重置自己的临时验收数据库并开始 merge e2e；上述是应用自验，非官网分数。千帆 Flash 间歇 429/token_plan_person_rate_limit_exceeded，最近 request284 已由 Ark 完整返回。没有最终交付、冻结应用或评分；未控制、未持续监控。证据 recovery/progress-20261007T1628.json。

## 2026-10-07 17:02 用户进展查询

容器仍 running、run=generating/braid。PR8 已 ready，固定候选 9026d47969040f849a5e3651252b3e551e3b3838，review request11/reviewer-11 正独立验收。reviewer 完成前端构建，建立独立 review-11-f2 服务及临时数据库，开始实际 API/浏览器检查；最近 curl→JSON 解析出现 JSONDecodeError，尚不能据此认定阻塞。千帆 GLM root request464 的429转 Ark 后 complete，无连续供应商阻塞。PR8尚未合入、最终交付未关闭、无评分；未干预/持续监控。证据 recovery/progress-20261007T1702.json。

## 2026-10-07 17:30 用户进展查询

恢复容器仍 running、run=generating/braid；PR8固定候选9026d479的review11尚pending，reviewer实际浏览器验收继续。reviewer报告S2权限场景（无设置链接/按钮）通过，正在S3将pending检查改为success并核刷新持久化。最近Flash请求584经Ark complete。无明确持续阻塞，PR8未合入，delivery_closed=false，没有最终冻结应用/self-test。只读查询未干预，证据recovery/progress-20261007T1730.json。

## 2026-10-07 17:51 用户进展查询

仍 running/generating/braid；PR8 review11 pending。reviewer 最近被 e2e 工具 mcporter 的 daemon_unresponsive 卡住，发现 stale daemon PID 已死而 metadata 尚存，正尝试 migrate/start。最后后台命令已退出，但本次证据尚无重新打开浏览器成功；不把工具尝试称验收进展。PR8未合入、最终交付未关闭、无冻结/官网评分。本次未干预，证据 recovery/progress-20261007T1751.json。

## 2026-10-07 18:12 用户进展查询

review11已approved/completed，PR8已合入；进入最终整合PR9（develop→main），仍draft，glm-9读取原始完整需求和覆盖范围准备全范围e2e。旧mcporter工具阻塞未再阻止该评审结论，本次未追查具体daemon恢复机制，不能据此宣称其根因修复。active_turns=2，另一个PR6 owner核对任务材料已发布并收口。run仍generating，delivery_closed=false，无有效最终交付/冻结/评分。只读未干预，证据recovery/progress-20261007T1812.json。

## 2026-10-07 19:32 用户进展查询

最终整合PR9已ready，固定候选0d3117e2，review12/reviewer-12独立验收pending。最新Agent正排查浏览器/服务环境：agent-browser返回about:blank，未找到对应browser进程，health请求无可见响应，停止自己的两个后台job；尚无结论/明确根因，不把此时宣称测试通过。run仍generating，PR9未合入、delivery_closed=false，无冻结/评分。本次未干预，证据recovery/progress-20261007T1932.json。

## 2026-10-07 20:11 用户进展查询

reviewer12已恢复实际agent-browser操作，刚以pr-reviewer登录生成应用，选择Approve、提交review并观察到Approved文本。这是生成应用功能验收，不是Braid评审Approved结论。PR9仍open/review12 pending，run仍generating，delivery_closed=false，无有效最终交付/冻结/self-test。此前about:blank工具状态已不再阻止这条旅程，恢复机制未扩展调查。本次未干预，证据recovery/progress-20261007T2011.json。

## 2026-10-07 20:39 最终合入与冻结

review12已approved/completed，最终PR9合入main5655950，delivery_closed=true。root与整合成员正在收尾packet，容器尚running且export run.json暂generating；delivery.json旧错误不能当最终发布回执。按既有独立评分授权，从原request指定refs/heads/main的5655950 Git archive冻结应用至selftest/application-source.tar（SHA6100f9f78e67421a99d2cf702e4a0eb8c53c728c3360c4ee05ef99dbbec9fc55），258 entries，来源回执selftest/application-freeze.json。尚未官网上传评分，下一步LinuxNode20正式安装构建为Dockerfile应用包并独立self-test。无生成反馈注入、无运行控制。

## 2026-10-07 21:00 终态确认与评分消费

恢复容器已于20:44:16正常exit0、非OOM；run=generated/frozen，delivery=delivered，active0，root Issue CLOSED。最终交付commit565595015d026dd9d1ac06d2d0c15eedcb4dae89，与之前精确冻结一致。独立Linux打包消费已启动（Mac PID95491，selftest/score_final.py），使用现成修复后scorer、Node20正式npm安装构建、scratch提取显式unused命令，runtime tar加入shared原代码，不改变业务应用；日志selftest/official-evaluation/build.log。

实际官网 GET /api/tasks 仅提供GitHub stage1/2/3，没有完整REQ1–6题目ID。发现记录selftest/task-discovery/records/self-test/tasks.json，当前不猜ID或将阶段分数冒称完整题结果。primary正在选择最小评分范围，打包独立推进。未上传所以暂无score。

## 2026-10-07 21:18 阶段评分开工

primary明确采用官网最终stage3一份（github-stage-3-req-test），source为完整REQ1–6生成、评分仅官网stage3范围，不称完整题总分，也不追加stage1/2矩阵。选择原件selftest/platform-task.json。Linux打包已成功，ZIP22,994,315字节，SHA92c6e17882f1c14fc2b86780eb59b4edaba9cc12e7de8770c9923d9fbbae864e。第一次消费在完成打包后因尚未确定platform-task.json退出，未上传；原error和build.log保留，没有重建/重生成。

21:18:42已启动现成API独立消费续段selftest/score_upload.py（Mac PID2092，项目.venv/bin/python），仅复用成功ZIP执行start/observe/save；程序每120秒观察终态保存，不GPT持续监控，评分不回流生成。manifest/source-receipt均在selftest/official-evaluation。

21:18:53官网已实际受理：submission a5637790-8965-45e3-9a8f-a48acf51d51c，题目github-stage-3-req-test，首状态queued、result=null；上传成功不等于评分完成。回执selftest/official-evaluation/started.json，程序observe持续保存status/saved；现在放手。

## Stage3独立官网评分终态

官网submission a5637790-8965-45e3-9a8f-a48acf51d51c于2026-10-07T21:20:57.147000+08:00完成，实际0/41。独立消费保存status.json及saved.json，非队列或设施启动错误：40项为“Could not find a visible navigation target named ...”（包括Issues、Improve onboarding、Reviewable onboarding PR等），1项为“ReferenceError: uniqueAccount is not defined”。完整错误原件和有界分类均位于selftest/official-evaluation；此分数只stage3范围，不是完整REQ1–6总分。来源最终commit5655950不变，生成早已结束，没有反馈回流。最新本地读取2026-10-07T21:31:02.889336+08:00，无额外重试/模型/评分矩阵。
