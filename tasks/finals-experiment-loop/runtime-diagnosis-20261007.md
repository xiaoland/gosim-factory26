# 2026-10-07 晚间运行诊断

用户要求深入检查 project.zip。本轮两条验收实际是 sfp7 本地执行，没有官网 project.zip；诊断直接读取对应远端工作区、原生日志和已有截图，不新开生成、不控制运行、不修改业务应用。Mac 的 saved-sync 只镜像 records，已有 data 不保证最新，故不能以本地旧 session.jsonl 推断停滞。

## Pi BookStack：存在实质问题，不是完全停滞

运行 a3a9a5262b8b40f382883ed636758464 的当前 producer gateway.log，读回至 request 74：74个 accepted、55个 fallback，失败尝试 elapsed_ms 总和6905.179秒（约115分钟）。其中千帆53次HTTP500累计6903.040秒，ARK两次HTTP429累计2.139秒。最近千帆 qianfan-token-plan-glm-5.3-flash 多次约130秒后返回 HTTP 500，响应 body 0字节、diagnostic为空；后续 ARK 返回200，最近request72/73耗时8.203/10.353秒。这里累计的是失败attempt等待，不是额外模型费用或严格反事实可节省时间。它说明逐请求重复尝试当前失败路由持续拖慢推进；尚未定位供应商500的内部根因。

截至19:46，原生记录显示后端8项应用测试在19:29通过，前端dist存在，Agent正在浏览器验证，不是纯心跳或模型彻底无返回。19:39、19:44的snapshot均没有交互元素；19:44截图确为纯背景白屏。读取现有App.jsx发现使用UserContext.Provider但没有从context.jsx导入UserContext，而context.jsx及其它消费者导入均存在。这是明确的源码缺陷，与白屏一致；尚未取得浏览器异常栈，不宣称唯一原因，且未代替生成Agent修复。

19:33工具返回具体错误：session名task-8945cd75636e使socket路径107字节，超过工具103字节限制。Agent改成bscheck，但后续独立shell未继承AGENT_BROWSER_SESSION，也没有显式--session。docker top显示两套agent-browser daemon/Chromium，未见僵尸。该边界失败与session丢失造成额外成本，属于工具环境接线和Agent使用行为共同问题；不能把所有348个cgroup线程/进程当泄漏。

原件位于 sfp7 `/home/yyh/factory26-lab-runs/runs/a3a9a5262b8b40f382883ed636758464/`：`data/harness/f1335fc0c4d9446e90a6f6a99faaf687/session.jsonl`、`pi-timing.jsonl`、`producers/a3a9a5262b8b40f382883ed636758464/gateway.log`。应用源码在同run的data/workspace/frontend/src，截图在运行容器的`/tmp/selftest-home-guest.png`。只读HTTP首页返回200不等于渲染成功；/api/me GET会建立guest session，本次一次诊断请求产生该正常应用副作用，后续不重复请求。

## I14-dx-test：当前有语义进展，gateway 不是同类阻塞

运行 `ed426cf521bd4f46ba58629f4acbd3e3` 的最新事实来自 sfp7 远端，而不是 Mac 上较旧的 saved-sync。Braid live SQLite 显示 PR #2 的基础 PR 候选已完成一轮 review；2026-10-07 11:46:50Z 的最新事件为 `Review #1: changes_requested`，随后 root/fast 原生 turn 仍为 `running`，PR #2 与 Issue #1 仍为 OPEN。因此这是正在处理 review 修改的真实进展，不是只靠心跳伪装存活，也还不能称为完成或已有评测结果。

直接读取 producer `gateway.log`（远端同一 run）得到 325 次 attempts、311 次 HTTP 200、14 次 HTTP 429，未见 Pi 那种连续 HTTP 500/空 body。429 主要来自千帆 token-plan 路由并由 ARK fallback 成功；全部上游 header 等待平均约 3.99 秒、最大约 27.1 秒，近期 fallback 约为 0.5–4.9 秒。故 I14 没有出现 Pi 的多次约 130 秒失败等待，gateway 目前不是它的主要阻塞；状态摘要较旧（297 attempts/12 次 429），以直接日志为准。

证据原件：远端 `/home/yyh/factory26-lab-runs/runs/ed426cf521bd4f46ba58629f4acbd3e3/data/harness/782227e2db174c98a41eca4b7141289e/producers/ed426cf521bd4f46ba58629f4acbd3e3/gateway.log`；同目录 `braid-state/braid.sqlite3`；`.arc/runner-events.jsonl` 与 `.arc/runtime-reporting/operations.jsonl`。Mac `records/finish-evaluation-result.json` 仍为 `waiting-for-generation`，所以尚无应用保存、自动评测或评分闭环。此次只读取证，没有控制运行、启动新模型、读取隐藏反馈或修改业务源码。

## 最新补充与处置边界

19:48:54 Pi生成Agent自行读取浏览器console取得 `ReferenceError: UserContext is not defined`，指向dist/assets/index-D7_Qc7wV.js；19:49继续grep缺失导入。该回执确认白屏原因，并表明Agent已自行定位，主没有向它注入修复答案。此时尚未取得修复后成功页面回执。

本次请求是诊断，不改变冻结路由、停止/接续或向生成Agent注入应用修复答案。后续基础设施工作应首先处理持续失败路由的运行成本及短socket目录，保留错误和原生进度；路由变化须记录实际配方身份。最终应用仍须让生成Agent自行完成并冻结后评测。原activity=active事实不错误，但不足以支持“运行顺利”的解释，报告必须同时呈现失败/等待与语义推进。

用户随后纠正：不记住跨请求失败是正常行为，先修其它问题。上段关于失败路由是当时调查建议，不作为修改授权或已采用设计；当前不增加失败记忆、不改等待期限和在途路由。短socket公共环境与技能显式session已修；随后在现有Pi应用上独立实际浏览器操作取得首页交互元素并正常close，说明原生生成Agent已自行修好页面，不是主代修应用。

## 用户提供的进程清理中断线索

用户指出`pkill -9 -f "node src/index.js"`累计伴随16次`Command aborted`，日志显示匹配到执行shell。该命令确有自杀机制：执行shell的完整命令行也含被匹配字符串，但次数与实际来源run仍需原件确认，不能把`Command aborted`自动归责于资源监控。

主核对`lab/arc_bench/harness_services.py::ResourceSupervisor`、`scripts/runtime_resources.py`及`harness/npm/native-managed.mjs`：公共压力补救不生成pkill，回收已退出的明确child、内存reclaim，失败时停止持有的入口进程；native stop按进程身份执行。Pi当前session定向检索未发现pkill命令。I14原负责人正在只读确认来源，不执行该危险命令，也不对用户未指定的其它运行扩大控制范围。已有agent-browser技能明确禁止按程序名/端口全局pkill；若是Agent自行发出的应用清理，归工具生命周期使用问题，不能靠公共资源管理器拦截任意shell字符串解决。

I14负责人后续返回：ed426定向原生日志没有该pkill命令，没有16次对应abort；仅找到2次Command aborted，来自pi-glm-fast原生日志中的bg010/bg011，均伴随session明确执行pbb kill/portless清理。另一次pkill文本只是读取技能禁令，不是执行。故这两条验收中未证实用户描述的16次，需对应run ID或日志路径再归因，不改资源管理器来补一个未成立的缺陷。

用户澄清为pi-minimal-vv另一运行后，主找到已完成的官网原件诊断：`runs/pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/diagnosis-20261007-201100/abort-and-health-pattern.json`及同目录diagnosis.md。当前native scope为1bad241ee5cb417ab03b643991f9254e。16次从18:38:40至20:08:52，首例pgrep明确列出PID10759 bash -lc与完整清理命令，继而Command aborted；确认用户报告事实成立。之前无匹配仅限两DX验收，不能否定该报告。该命令来自原生Agent Bash调用，不来自公共压力监控；截至20:09后续有健康/交付检查，不能据历史中断断言当前卡死。只采用已有原件，不下载新官网材料、不控制该正式run、不向其注入反馈。

process_reaping_decision只基于主提供的上述事实建议：归应用服务/检查入口的接线与发现，不加公共manager拦截/gate，也不堆禁令。主采用归属判断；下一步先核实该variant实际提供的managed启动回执、停止/检查入口，再在既有入口补缺，不新增服务框架。若入口与说明已充分，则保留为Agent错误选择，不自动升级为设施缺陷。

## 自验用例的数据边界

继续读取上述官网run的本地project.zip、self-e2e-isolation-summary.json及stage-backend-database.db。三个当前e2e文件没有数据库重置hook；workers=1，服务明确使用/tmp/selfcheck/database.db。PR合并与随后文件浏览、搜索断言操作同一acme-demo/acme-docs仓库，因而独立数据库仅隔离交付应用，没有隔离用例。

交付数据库快照的main包含src/README.md，待合并feature head不包含；当前归档应用的pulls.js已经使用三方合并并注明保留main新增文件。因此存在相互影响的条件，但不能把历史失败直接归为污染，或认定最终合并实现仍然丢文件；数据库快照也不是自验数据库的最终状态。没有操作正式run、修改应用或读取隐藏评测。

主完整读取冻结e2e版本的writing-tests说明：已有fresh browser context、beforeEach/afterEach、test.extend及serial场景，但前者不恢复服务端数据。advisor仅依据提供事实建议补现有fixture发现与边界，不加通用数据库reset。主采用，更新实际打包的harness/skills/e2e/SKILL.md：独立case使用独立可变对象，有意流程保留状态，必要快照恢复须先停所属服务并覆盖相关文件/索引；区分单例初始fixture与顺序运行的反馈。该段位于variant builder替换准备段之外，VV打包会保留。未声称文档自动隔离已有测试，未改在途冻结包。

evaluation_closure实际核对冻结runtime：Bash schema已有service:true，启动回执带jobId/globalJobId和PID/PGID，pbb查询与托管停止均存在。16次pkill绕过了该链，不是缺少服务能力。另找到pbb kill未像status/tail一样识别INSTANCE:bgNNN的真实消费缺陷；修复公共pi-background-bash-1.0.5.patch，让停止也选global并沿用既有findJob接口，帮助同步说明。scripts/runtime.py将该patch用于native构建，后续公共安装消费冻结patch；未热改正式runtime。负责人报告node --check通过，但没有服务停止实际验收；主采用该边界，修正其编辑时误改的patch上下文缩进及hunk计数，git apply --numstat可解析。主只暂存本次两个hunk，保留同文件既有其它改动。长时间无回执后主中断并要求立即交回状态，负责人确认无在途操作；未把等待伪装为验收。
