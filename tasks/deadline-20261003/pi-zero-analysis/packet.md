# Pi Stage 2、Stage 3 零分调查

2026-10-06 用户要求：“下载 stage2, stage3 的工作区包，分析一下为什么是0分（可以使用 arc-bench self-test 来获得具体原因，因为其会直接暴露测试错误信息，根据测试错误信息我们再溯源 Agent 运行过程）”。授权下载终态工作区、只读调查、冻结原生成应用并按需提交 self-test、实际构建和启动验证生成应用；不授权修改业务源码、Harness源码、评测器或重新生成。

已有官网事实：Pi submission `aea08b61772c` 的 Stage2 `32db20c04573`、Stage3 `d86b43e8c891` 均生成完成、评测完成，但分别通过0/29、0/41。需要区分公共部署/入口/身份前置失败、接口或功能不符合需求、评测设施问题。优先消费工作区中原始评测错误；若缺具体错误再按原应用冻结身份提交同题 self-test。以测试错误定位应用契约，再沿对应 Agent 事件溯源，避免通过隐藏反馈修改应用。

| 负责人 | 可独立采用的结果 |
| --- | --- |
| `pi_stage2_zero` | Stage2原始ZIP、来源/SHA、应用边界、错误因果与原生证据。 |
| `pi_stage3_zero` | Stage3原始ZIP、来源/SHA、应用边界、错误因果与原生证据。 |
| `arc_selftest_owner` | 唯一浏览器self-test操作owner，消费上述冻结包，保留配额、提交身份和具体错误。 |
| 主线 | 授权、两题共性判断、证据采用及汇报，不重复owner操作。 |

所有Mac产物位于 `runs/deadline-20261003/pi-zero-analysis-20261006/`，已核WorkSSD剩余328GiB。下载终态原包不作为恢复检查点；此次不恢复周期监控。当前阶段：两题下载与归档调查，self-test owner只读核对站点合同和登录，等待是否有必要送测。


官网 `/runs/{id}/logs` 已于本次取证取得，两题前端 npm install/build、后端 npm install 及 Node 后端 start 均成功；启动日志分别为 `17:07:20 UTC`、`17:37:39 UTC` 的 `Backend listening at http://127.0.0.1:3000`。这排除了“根本未构建/启动”的解释，尚不能证明页面、数据或公开交互契约符合评测。原件在 `runs/deadline-20261003/pi-zero-analysis-20261006/platform-logs/{stage2,stage3}.json`。

self-test 浏览器 owner 已核对当前 xiaoland 登录、今日10/10配额、Stage2/3题目与根Dockerfile/≤50MB合同，预检原件为 `selftest/browser-preflight.md`。两题终态ZIP已下载，SHA和解包由各stage owner保存；目前正定位产物与验证缺口，是否送测由具体证据决定。


Stage2 owner 已交付原包、SHA和报告 `stage2/report.md`。主线核对 `.arc/playwright-report.json` 的29条result：全部failed、唯一错误为 `browserType.launch: Executable doesn't exist at /ms-playwright/chromium-1200/chrome-linux64/chrome`，未进入页面/业务断言。这已足够确定正式0/29的直接原因，无需重复Stage2 self-test。原包SHA `a9d0b2ff728a6dd8f227798678b86754e39c33aed15a4a537c8bef55086cacfe`，132187328 bytes。

Stage3 初步报告已核生成/部署成功，但尚缺具体断言。继续由原owner核隐藏 `.arc` 正式结果；原owner负责必要包装，浏览器owner只消费可上传冻结包，不接手分析或包装。两题共同的进一步疑问是缺失浏览器属于评测环境固有缺口，还是生成Agent改变环境导致；定向检查实际安装/浏览器路径记录，保留未知，不将Agent自验通过等同正式契约通过。


Stage3原包同样包含 `.arc/playwright-report.json`。主线核对41条正式结果：40条为找不到导航目标（Issues、Pull requests、Compare或具体fixture标题），1条为 `ReferenceError: uniqueAccount is not defined`。浏览器正常执行到了页面导航，因果与Stage2不同。仅有未等待initializeDatabase/seed的源码模式及首次测试时间，不能证明初始化竞态；同类失败持续到启动约85秒后。继续由Stage3原owner核实际seed/DB、页面导航契约、HTTP/DOM，必要时独立self-test；不得把待证实假设写为最终根因。

Stage2进一步边界：`.arc/preflight.json`声称Playwright1.57.0及chromium-ready，正式报告仍缺Chromium1200。Agent自验使用包内Chromium，e2e CLI曾写另一headless-shell1243目录，但无删除正式浏览器证据；是否平台镜像/挂载或共享目录变化导致缺失，现有工作区无法完全证明。Stage2 owner报告已写明边界。


Stage3原源码干净副本实际启动：首次立即GET /api/repos为空，约0.1秒后两个公开仓库及Issue fixture可用，故seed持续延迟不足以解释4–85秒间全部导航失败。进一步判别需要正式DOM/HTTP或独立self-test。Stage3 owner完成机械离线包装；主线要求核Linux native依赖，发现初版sqlite3为Mac arm64而弃用（未上传）。最终可用候选为 `stage3/application-selftest-upload-linux.zip`，23212932 bytes、SHA `b308457d224cd8223271584a4b3bcd419fd37834b279149a1768bcd553feadb2`，sqlite3已核Linux x86-64 ELF，原业务源码未修改。self-test owner只获准按该包向Stage3提交一次；旧包不可作为运行失败证据。


## 本次结果与接续边界

两题原始工作区已下载并保留SHA、目录及终态来源。Stage2正式29个场景均缺Chromium1200，在浏览器启动阶段失败；直接原因已证明，不能把该零分解释为业务功能全失败。Stage2报告与原件见 `stage2/report.md`、`stage2/workspace-template-bundle.zip`。浏览器缺失的来源仍需平台镜像/挂载/运行前后目录证据，未证明Agent删除浏览器。

Stage3正式40个场景找不到公共导航目标，另1个测试自身uniqueAccount未定义。独立干净启动和真实Chrome验证表明首页有公开仓库、进入仓库后Issues/PR/Compare与fixture可用，Compare有实际diff，排除了永久缺失；只凭约0.1秒seed初始化，不能解释4–85秒间正式全部失败。已证明Agent最终自验主要深链直达并共享serial浏览器状态，没有独立覆盖首页→仓库→tabs路径，36/36通过不等于正式41场景契约通过。

Stage3正式首导航时的URL/DOM/HTTP没有保存，无法精确区分页面就绪/首次渲染时序、根页与仓库页上下文、fixture预置差异等解释；报告“可能时序”只作为假设采用，不当作最终定因。原件与报告见 `stage3/workspace.zip`、`stage3/analysis.md`。

独立self-test已准备Linux机械包装包，但浏览器file chooser无可用上传接口，native Sky service启动失败；原浏览器owner和主线cua inventory均确认。上传0次、配额仍10/10，不把此工具故障算应用失败。可用包为 `stage3/application-selftest-upload-linux.zip`（SHA见上），业务源码未修改，尚未独立Dockerbuild/start；不能把Mac直接运行等同Linux容器完整验证。浏览器owner保留实际导航操作原件，之后不继续周期跟进。继续独立self-test需要上传能力恢复或用户手工提交该明确冻结包；继续正式环境精确溯源需要失败URL/DOM/HTTP或平台重评。


真实Chrome观察由Stage3原owner本人执行，工具为CUA tab110967046（不是self-test browser owner操作），应用URL为独立PORT3306。AX操作摘要在 `stage3/browser-observation.md`，主线核对证据归属后采用；该临时验证服务已停止。自测browser owner只负责self-test表单与文件chooser阻塞观察、没有上传。上述局部实际操作不是正式评测重放，不能宣称Stage3新分数或已精确定位正式环境根因。

当前已完成下载、原始逐场景错误分类、生成过程验收缺口溯源和独立实际导航核对。Stage3更深定因被正式DOM/URL/HTTP缺失及self-test上传工具故障阻塞；没有源代码修复、模型运行或周期监控待执行。用户可凭明确Linux冻结包手工self-test，工具恢复后也可在新指示下继续；不自动跟进。


### Stage2 self-test 重试授权

用户新指示：“重试 stage2 到 self-test”。本次明确授权原Stage2生成应用的机械Linux离线包装、一次Stage2 self-test提交及终态结果核实，替代此前Stage2不提交决定。原业务源码、Harness和正式运行不改。原Stage2 owner `pi_stage2_zero`负责包装、来源及结果判断，`arc_selftest_owner`继续唯一网页提交writer并重新核对当前工具能力，不沿用旧Sky错误直接停止。所有产物在WorkSSD `stage2/selftest-retry/`，先核Linux原生依赖再交包；提交身份/具体错误和配额变化必须保存，效果未知的写不自动重传。


Stage2重试包已完成：`stage2/selftest-retry/application-selftest-upload-linux.zip`，6788768 bytes，SHA `cfb199499eecfb77bc222cd7e3fef9517296a90c9d51eeafd039ff723e14d20d`。原Stage2源码机械包装、Linux x86_64生产依赖/sqlite3，实际禁网Dockerbuild成功，Node20.19.3容器health/root/login均HTTP200且0.0.0.0:3000监听。元数据为packaging-metadata.json，实际启动记录container-start-check.log。

本轮重新连接网页并新调用nativeChrome控制，仍Sky service startup失败；当前已文档浏览器接口无filechooser/setFiles。Stage2账号xiaoland配额10/10，尚无文件选中、提交0次。Cua工具规范限定“Do not use other technologies besides cua_repl for computer interactions, unless specifically requested by the user”，因此主线在完成可审阅包及验证后，请用户明确允许本次AppleScript文件选择，不能擅自用shell UI绕过这一技术限制。Stage2提交本身已授权，不再请求其提交许可。


用户就上述技术授权问题明确回复：“允许本次使用 AppleScript”。本次允许唯一browser owner用AppleScript替代故障的native服务完成Chrome文件选择，其后正常Stage2网页提交与结果读取仍沿原授权。操作只限该自测页面及明确冻结ZIP；不改系统权限、不取浏览器凭据、不控制其它运行。Stage2 owner继续持有结果判断责任，消费browser提交回执/终态。


AppleScript本轮最初按CUA通用Chrome标签寻址Google Chrome，返回application(-1728)/process(-10006)。主线只读process核对发现当前本机实际浏览器为 `/Applications/Helium.app/Contents/MacOS/Helium`（PID28589），不能据错误名称声称没有原生浏览器。已由原browser owner改为Helium应用/进程，同一self-test tab和原技术授权继续；主线告知用户该识别错误并更正。


UI责任已安全移交主线：原browser owner确认没有已知上传/提交写、无脚本在途、无filename/ID，停止新操作。主线读取当前完整selected-browser文档，发现受支持的Playwright waitForEvent(filechooser)/chooser.setFiles接口，之前仅按通用CUA文档判断无filechooser是不完整判断。主线按文档流程成功选择Stage2冻结cfb199包，不需继续原生AppleScript；已有技术许可保留为历史，不修改浏览器权限。当前主线唯一提交writer，intent先写后单次网页提交。


Stage2自测已实际提交一次，账号xiaoland，ID `5a6176dd-fe56-473c-b350-8dd1662c6ce8`，结果URL https://arcbench-selftest-web.vercel.app/submissions/5a6176dd-fe56-473c-b350-8dd1662c6ce8 ，提交时间页面显示2026-10-06 15:27 CST。已上传原应用机械Linux包cfb199...，网页明确排队中/等待评测机，预计约7分30秒。主线保存submission-receipt.json和submitted.jpg，效果明确，不重复提交。当前等本次终态，以实际测试错误/评分同原0/29对照。


Stage2本次self-test已终态：3/29（页面10%），26 failed，ID仍5a6176dd-fe56-473c-b350-8dd1662c6ce8。Chromium启动故障未复现，实际进入应用；已知错误包括重复Sign in及找不到acme-docs/Document search flow/branch-switch-demo。初版错误分组计数仅25，与页面26存在一项缺口，主线退回原Stage2 owner核全量错误、终态截图，并依据失败DOM定向追溯Agent自验及应用代码/数据，不能把locator不存在直接判为数据永久缺失。正式0/29与独立3/29分别保留，不改正式成绩，不修改业务源码，不重新提交。


Stage2终态复核完成：3 passed、26 failed；13条首页Sign in链接重复、10条acme-docs导航找不到、1条Document search flow、2条branch-switch-demo。首个失败实际截图显示首页欢迎语、两个Sign in且无仓库列表；源码Header.tsx及HomePage.tsx各渲染一个Sign in link，HomePage未提供公开仓库导航，优先解释主要失败。SignInPage的button不匹配link，已纠正原owner初始错误溯源。seed源码含fixtures；自测包元数据明确排除database.db，不采用旧库污染推论。启动未等待seed只是次要风险，未证明导致这些错误。原28/28自验没有发现上述首页契约缺口；不等同官方验收。完整26条错误在stage2/selftest-retry/selftest-result.json，报告stage2/report.md，实际首失败截图first-failure-screenshot.png。独立自测不改变原正式0/29；本次仅一次提交，无业务源码修改。
