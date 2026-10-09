# I15 Stage1 reviewer验收竞态及运行约束采用

本次只读追踪run `20261007-071419-c894cc6b`、PR2候选`ea7b59b`的review1，不修改应用、Harness或在途运行。原生证据、同一失败trace与针对性源码保存在`runs/iteration15/reviewer-race-inquiry/`。2026-10-07 18:26取当前状态，随后只补取该reviewer收口生命周期。

最后一项失败可确定为“成功登录晚于页面断言采样窗口”，不能确定为密码修改业务错误，也不能把其8.75秒请求耗时直接归因CPU。reviewer将其判为偶发后Approved；我们的更窄结论是已有HTTP200、认证成功证据及3次独立复测，支持凭证未损坏，但尚未排除应用或代理的偶发延迟缺陷。

## 同一失败的因果链

测试源码`review-acceptance.e2e.ts.txt:269`先以password-change-required登录、打开密码设置；留空当前密码，填新密码后提交，要求看到`Current password is required`，然后经账户菜单登出，再以原密码登录，最后要求欢迎heading。signIn helper第12–18行只执行真实页面点击/填值，不等最终登录状态；第278行有页面重试断言，所以不能说完全没有等待。

| 北京时间2026-10-07 | 同一trace中的动作或结果 | 解释边界 |
| --- | --- | --- |
| 18:02:14.919 | change-password返回400，3.435ms | 空当前密码失败请求确已完成；测试也先等可见错误 |
| 18:02:18.407 | signout返回204，49.863ms；随后auth/me401 | 登出真实完成，没有把尚未登出当下一步前态 |
| 18:02:33.346 | 原密码signin发出 | 导航没有阻止登录请求发出 |
| trace时钟34,681→40,671ms | welcome heading重复采样5次，均未匹配；报告该断言失败等待6.2s | 最后可见性采样结束后进入失败证据采集，没有继续等到登录响应；无法由首个采样精确反推出外层计时器起点 |
| 18:02:42.094左右，trace43,026ms | signin返回200，总8748.134ms，其中wait8515.535ms | 响应迟于最后断言采样约2.35s；随后auth/me200、organizations200 |
| 失败screen.txt | URL为`/`，仍显示Sign in表单、按钮disabled，无Invalid credentials | 捕获处于导航/提交交接态；URL与DOM过渡不同步不足证明密码错误 |

上述HTTP时间取自失败trace.network，不取自Agent猜测。页面断言超时是真实失败；点击完成也没有宣称登录完成，所以没有证据证明工具虚报了业务完成条件。request已发且最终200，排除了“未发请求被导航打断”的解释。200后欢迎页是否最终稳定出现，本轮失败trace在证据采集后结束，不能从该trace补造；随后相同场景3/3复测通过提供独立佐证。

18:10:56重测命令仍用同一`e2e.config.ts`与测试文件，仅`--grep 'REQ-1-3 S3' --repeat-each 3 --no-cache`，没有提高assertion timeout参数。18:11:25记录3/3通过。因它由全量31项改为单场景重复，负载/序列条件已经变化；不能把3/3复测当成原全量运行无竞态的证明。reviewer18:17:22提交Approved，正文保留30/31与3/3而未抹掉失败。

## 其它验收编排及设施问题

首轮31项中22项因验收代码未解构browser fixture而报`browser is not defined`；其后修正。中途23/31一轮涉及menuitem角色、dialog作用域与导航定位问题，reviewer明确将它们归自己验收代码而非候选。最后30/31不再属于这些定位错误。

portless首次子进程实际用了Node24，触发better-sqlite3 ABI问题；改用绝对`/usr/local/bin/node`后启动Node20.19.3成功。另e2e MCP daemon出现`Previous daemon exited unexpectedly`，reviewer改用相同冻结运行器的CLI/Chromium验收，记录能力替代与关闭缺口。它们是独立已观察设施摩擦，不能用来解释最后一次8.75s登录请求。

## I15约束在运行中的体现

| 约束 | 实际采用证据 | 未证明或偏离 |
| --- | --- | --- |
| 同PR单当前reviewer、先收口再下一候选 | PR2只有review1，固定base65c6b4b/head ea7b59b；结论18:17:22，provider retired，turn18:17:25 interrupted且无error；后续由新实施者做PR3整合 | 本样本证明正常路径收口，未制造第二个reviewer请求以验证拒绝路径；PR3整合不是Stage2，Stage1尚未最终交付 |
| 明确svc-verification触发 | 17:14:37原生明确“before establishing acceptance criteria”，read独立SKILL；成功toolResult正文已读回 | 不能仅凭已读就证明全部验收判据可靠；仍出现fixture/定位/异步预算问题 |
| 原始requirements权威 | 17:14:53直接read run/input/requirements.yaml，测试开头及结论逐条引用原文路径，30场景映射 | Approved仍把会话立即变更语义及授权行accessible name差异列非阻断解释；直接读原文不等于所有歧义都已解决，不能按实现或“场景能跑通”自动降格原条款 |
| 独立验收环境 | 自有review1-r2-i0 portless、DB `/tmp/r2-i0-review/data/review-app.db`、`.e2e-review-N`/evidence目录；config workers1/retries0/cache off；独立浏览器上下文有报告支持 | 全量运行复用同一数据库，各场景用户名不同，重测又复用该服务；只能称与候选/其它验收隔离，不能称每次测试都从只读种子独立复制。没有cache/uploads独立路径的实际证据 |
| conclude前关闭自有执行 | 18:15:45回读0应用进程、无active portless route、HTTP404，随后conclude；provider随后retired | 清理命令用`ps ... dist/index.js ... | xargs kill`按名称匹配，并非保存PID精确关闭；本次没有证明杀掉其它服务，但方法违反“只关闭自己的进程”的可靠边界 |
| 缩短职责与默认7项技能 | 冻结I15源码及材料身份77c090...已保存；当前reviewer成功按明确触发读取verification并独立验收，没有继续扮演实施者 | 运行默认发现目录7项由材料/消费接线证明；本次不以prompt长度或read次数证明最终正确率。实际方法有效性须按需求对应oracle判断 |

相对旧I14同PR review4/5/6同时验收并在合并后补结论，I15本样本出现单专门reviewer、结论后真实retired。旧I14也有读取verification与直接原文的样本，因此不能将I15本次已读当作以前从未发生的新能力。I15改善的是默认提示、责任和生命周期约束；验收脚本/API知识、异步预算与需求解释仍有独立不确定性。

## 最小改进建议（未实施）

1. 单一登录helper保留真实点击，随后等待明确成功或错误终态，再对要求的页面状态断言；保存click→request→response→DOM时间。不要仅加sleep，也不要把HTTP200代替最终页面要求。延迟预算应与公开性能要求及本机实际服务延迟区分，当前原文未给这一步6.2s上限。
2. 对偶发失败保存同一trace，重测保持数据初态和全量前置；单场景重复可补强功能证据，但报告应保留原失败与条件变化。无需通用自动重试或掩盖失败。
3. 把Node20绝对启动路径和实际fixture/API能力写入现有工具使用说明；reviewer先采用完整文件示例，再写30场景，避免先付一整轮的编排错误成本。具体CLI/MCP崩溃独立保留，不与产品失败混称。
4. 每个服务记录PID/pgid、DB、路由、会话与证据目录；结束只关闭登记身份。现有独立命名已有效，不需新隔离框架。
5. 提示词不追加技能仪式；保留当前首次判据的明确verification指针。对影响业务承诺的原文歧义须明确替代解释和证据，不能因实现自洽或自验通过就默认非阻断。
