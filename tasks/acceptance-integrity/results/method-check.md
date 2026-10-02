# 既有应用上的浏览器检查：阶段记录

状态：原始检查因模型代理错误中断，接续已结束；完整作者报告已回收，主Agent发现其结论仍有过度声明。
本实验只检验检查方法和工具，产品源码保持旧候选 4c1784365ffe98f3a02a9639d0c083c8fb7d76d7，不生成新应用。
检查作者为 fresh DeepSeek-v4-Flash/high，获得公开需求、新 SVC/browser-checks 与运行入口，没有获得旧分析或外部验收集。

## 已确认的事实

新 runtime 的 Playwright Test、Chromium、模块导入、浏览器断言、失败截图/trace 已在24项应用检查中实际工作。
作者使用普通 TypeScript spec；仍编写了多份临时探索脚本，不能仅凭工具更换宣称反馈成本已经降低。
原生流最后一次完整执行报告16通过、8失败，源记录为 runs/acceptance-integrity/20260926/method-result/pi-output.jsonl 的150440行。
该命令使用 `playwright test ... | tail -40; echo EXIT=$?`，打印的是tail退出码，不能用EXIT=0认定用例通过。
原生模型随后遇到400 proxy_error / connection reset by peer（request id 2026092619191643468810135734），因此顶层进程exit_code=0也不代表检查工作完整完成。

8项失败包括重复关闭/审查记录触发严格匹配、已有合并状态导致按钮不存在、检查残留状态的操作错误以及待判断的行内评论失败。
这些发生在复用应用数据库的第二次执行，暂不把8项全部归因产品；原始error-context和trace保留在method-result/checks-workspace/checks/results/20260926T190427。
宿主以同一源码、新数据库和4318端口接续了原会话，旧4317现场保留；接续不回填或覆盖第一份原始结果。

## 需求到判据仍发生漂移

公开 requirements.yaml 的 REQ-5-3-1（2603行）明确要求名为Search assignees的textbox；REQ-6-4（3598行）明确要求名为Search的textbox。
作者的issues.spec.ts、pulls.spec.ts改用searchbox，后者测试名仍写“文本框”。定位能成功不证明声明的角色要求得到满足。
主Agent用独立的两项应用检查，依据原始需求保留textbox角色，在同一固定应用的4318实例执行，结果2项失败，原始命令退出码1。
两项均已经通过登录和打开相应选择器的前置，失败在所要求textbox不存在；trace显示应用提供searchbox。
独立检查源码、config、check.log、check.exit和trace在 runs/acceptance-integrity/20260926/method-independent。
这是具体产品行为的实际检查，不是Factory/Braid/工具自测，也不使用隐藏官方用例。

## 对下一步的影响

工具接线已经取得实际可执行证据，不需要为此继续扩大工具或打包设施。
现有方法没有自动防住oracle向实现漂移；该现象必须作为本轮负面结果保留，不能用16项PASS抵消。
本轮完整variant还有GLM根、独立设计、整合PR、强模型advisor等协作条件，不能由这个单独DS检查作者的表现推断整轮效果。
维持已批准配方进入本地完整实验，不临时追加题目专用规则或宣称SVC改进已经有效；观察最终交付检查是否忠实于需求，再向用户报告。

## 接续结果与主 Agent 判断

作者报告保存于 runs/acceptance-integrity/20260926/method-result/checks-workspace/report.md。新实例三轮分别报告22/25、23/25、24/25通过；最后保留了行内评论未进入Conversation的失败。
报告将textbox→searchbox归为“检查修正”、声称REQ-6-4已满足，与上面的独立需求检查相矛盾。也将修订过的不同检查和不同状态下的结果称为“连续两次稳定24/25”，而其表格中上一轮实际是23/25；该稳定性结论不成立。
再次合并检查在应用已Merged时改为观察终态，不再次执行合并；因此复跑所证明的范围不同于首次运行。统计diff只保留格式也未证明数字与内容对应。
实际可成立的阶段结论：标准Playwright接线有效，作者能修正等待和状态前置错误，并保留至少一项可复现的用户路径失败；仍存在oracle漂移和完成范围过度声明。不能把24/25当作该应用的需求通过率或SVC有效性的证明。
这些是本轮需要向用户呈现的负面证据，当前不临时增加题目专用规则或另一套强制验收系统。
