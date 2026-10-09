# E2E 业务状态转移验收改进

用户于2026-10-07要求展开分析I15 Stage1 reviewer的验收竞态，评估设施或提示词改进，随后明确“这可以作为一个独立的 task”。用户随后授权“好的，那么开始改进（仍然是I15）”，进入实现与材料验收。本任务独立维护调查、方案与实施边界；只改变I15后续材料，不热改已冻结在途运行，不提交。root负责采用，advisor为`/root/pi_local_adapter_advisor`；实施稳定owner为`/root/i14_combo_sequential_owner`，负责I15专属技能、必要提示指针、实际消费接线、材料重产与读回，保留其它工作区修改。

目标是让验收可靠地区分业务失败、业务尚未完成和工具失败，保留慢响应与首次失败，不以重试或放宽超时掩盖应用缺陷。沿用项目禁止Factory/Braid测试的约束；后续反馈来自已有原始trace、实际工具操作及获授权的生成应用验收。Mac材料全部位于WorkSSD。

## 已知事实与证据

证据归属为[原调查](../iteration15/reviewer-race-inquiry.md)，原件位于`runs/iteration15/reviewer-race-inquiry/`，不复制完整rollout。PR2候选ea7b59b的空当前密码修改返回400，登出返回204且当前用户401，旧密码登录最终200但耗时8.748秒。欢迎页最后采样早于响应约2.35秒，断言报告等待6.2秒；该报告值不能精确反推外层计时器起点。失败截图仍在提交中，没有Invalid credentials。具体响应延迟来自应用、代理或资源竞争尚未确定。

同文件/config的单场景3次复测均通过，没有增加timeout，但移除全量前置改变了负载/序列，不能证明原全量失败已经消失。I15 reviewer正常conclude后3秒retired；原始需求读取、verification触发与独立DB/路由有证据。另观察到fixture未解构browser、locator错误、Node24/20原生依赖ABI冲突、daemon退出、按进程名称清理等独立问题；不将它们自动当作8.748秒延迟原因。

## Advisor 已咨询的建议

上一轮已咨询advisor，明确建议先检查同一次失败的动作、状态、响应和页面，而不是凭timeout认定竞态。最小默认改进应归现有e2e技能：在依赖前序结果的动作前证明所需业务状态，以有期限的可见状态、URL或账户状态断言为主。客户端校验可能不发请求，不强制HTTP屏障；click返回和HTTP200均不能代替最终页面验收。不使用固定sleep、全局network-idle或自动重复非幂等操作。

只有工具缺必要观测能力，或其完成声明被原始证据否定，才修设施。若请求拒绝或成功后页面仍错误，优先调查应用。正确等待后通过不能直接将正常快速操作暴露的问题归为测试错；功能正确性与响应时延分别报告。reviewer职责提示只引用原则，方法正文保留独立技能文件。

## 方案与下一步

advisor在最终证据后再次收敛：本任务首轮最小范围为现有e2e方法说明和完整示例中的业务完成屏障、预算解释、首次失败与复测条件记录，必要时reviewer只增加一句引用。不改全局timeout或工具重试默认。Node绝对路径和fixture/API示例先核已有说明；进程名称清理问题列独立小修候选，不作为本次登录时序原因或首轮必做项。不得新增通用平台。

workers=1的多场景共享数据库不自动违反“每验收进程/原生角色隔离”，本次也没有污染证据。是否重置数据或使用独立fixture依据场景前态，不升级为每case必须新建数据库。下一步核现有e2e技能及其版本匹配指南是否已有相应能力和说明；已有正确指引时先改发现指针。

原始需求歧义不得按实现自洽自动降格，作为验收判据边界记录；不扩展为本轮业务应用修复。本轮按上述后续用户授权实施，源文件与结果如下。完成标准为可复现地辨别提交中、明确拒绝和成功后页面不达标；首次失败及时延仍可见；重测条件变化明确；自有清理不影响其它验收。读取技能次数、变长等待或单场景通过不作为完成标准。

## 实施与交付（2026-10-07）

稳定owner为/root/i14_combo_sequential_owner，root采用方案。I15新增本地skills/e2e/SKILL.md及references/business-state-transitions.md，继承冻结底包原技能说明并加依赖动作前的可见业务终态指针；builder现有成员枚举加入skills目录，使本包同名技能和reference进入overlay/manifest。共享harness文件不改，技能正文不内联。reviewer仅增加一句方法引用，默认发现仍7项，普通成员16项。完整示例的import、getByText(RegExp)、toBeVisible({timeout})逐项对应冻结writing-tests指南；20秒只是需要说明来源的例子，不是新默认。

内容包括成功/失败终态、局部期限、请求与页面证据区分、原失败和慢响应保留，以及单场景复测不可冲销全量失败。不加全局timeout/retry、HTTP200完成替代、固定sleep或每case数据库强制要求。没有模型、官网或设施测试/smoke。

新材料为runs/iteration15/materials/e2e-state-transitions-20261007/overlay.tar（22,138,880字节），SHA256 68b13ba014cf41f28900e3ce60ff076f69fd025ffe1ad7ab0a9787a4032c62e9，material_id manual-i15-reviewer-cleaner-e2e-fad3a77d331419fbf5aa6bb99ebce5cf72b2ad97e213eec53a129769b1027d95。上一有效77c090...overlay与其receipt仍原位保留，未热更新当前I15/I14容器或stagechain卷；本次新材料须由后续明确运行采用。首次中间构建ee28da24也在新目录history保存。

实际native_files只生成材料而未启动launcher/model，读取launcher确认reviewer7/普通16、e2e指针确实指向I15本地新技能、reviewer最终profile含方法引用。归档读取确认两技能文件及角色指令与源码/manifest/receipt SHA一致；已替换技能不再错误列为retained member。Python AST及JSON解析通过。依据与结果为新材料readback/{frozen-api-evidence.json,readback.json,archive-readback.json}。初次材料读取因缺冻结standalone支持模块和显式provider绑定未进入生产，此后采用冻结支持路径与非请求地址生成成功；未将设施资格化扩为新框架。

改动文件为variant build.py、README.md、agents/pi-glm-reviewer/instructions.md与两独立skills文件；操作和材料说明更新既有tasks/iteration15/variant-materials.md。本轮只证明接线与方法API兼容，未证明新指引的模型采用或实际验收质量改善；当前运行仍用原冻结身份。
