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
