# 更纯粹的原生 sub-agent：候选与关闭验收机制

2026-09-29：用户以“同意这个方案，开始。”批准统一关闭自动验收。锁定依赖补丁、工具界面和构建接线已完成；未替换扩展、修改角色或运行实验。

## 当前锁定 pi-subagents 0.56.0

本机runtime-faf60473273ddeed中的src/runs/shared/acceptance.ts：explicitAcceptanceCanDisable要求level=none且reason非空；formatAcceptancePrompt在none时返回空串；buildAcceptanceLedger在none时返回not-required，不执行后续判据/review。省略acceptance会自动推断，不等于关闭。
可逐次显式传 acceptance={level:"none",reason:"Acceptance is decided by the delegating agent."}。未找到现有extension config中的全局关闭项；这次结论不涵盖所有新版接口。
agentContract v1也能避开默认推断，但引入另一套contract不是当前简化目标。
逐次关闭仍保留验收参数、推断器和ledger，并不等同移除整个机制；不应把反复填写原因作为LLM长期责任。

## 外部候选（上游当前内容，尚未安装／运行）

- 官方示例：https://github.com/earendil-works/pi/tree/main/packages/coding-agent/examples/extensions/subagent 。独立Pi进程，单项/批量并行/链，流式、usage和取消，文档没有当前验收门。适合最小参照；后台启动后父继续工作、跨调用接续等不是README所承诺的现成同等能力。迁移需读实现及锁定兼容版本。
- mjakl/pi-subagent：https://github.com/mjakl/pi-subagent 。fresh默认，明确模型/工具配置、具名会话接续、并行。contract.ts的父工具接口是agent/prompt/model/thinking/cwd/initialContext/session/timeout，无acceptance/reviewer门。当前README要求Pi>=0.87.1，本项目0.85.1不能原样替换；完整技能/扩展接线、后台语义、证据保存待进一步核实。
- simple-subagents：https://pi.dev/packages/simple-subagents?name=subagent 。后台、send/status/collect/wait，但说明明确抑制stderr/error body/异常协议原文，禁子扩展，且配置面仍有写权限、会话配额等政策；不优先选，和本项目可诊断性/原生工具需求相悖。

## 建议的边界

原生扩展只提供会话、指定模型/工具/技能、输入/输出、真实错误、取消、进度与usage；LLM及SVC负责结果判定。执行终态不等于业务验收。
短期若只去掉自动验收，可统一接线关闭，不靠LLM逐次记参数；长期优先核实mjakl的实际能力，并以官方示例作为最小基准。
迁移应保持fresh角色、并行期间父继续工作（若沿用当前行为）、可找回原文/usage、合法结果交付与取消边界；不复制现有补丁以假定兼容。
调查形成下面的有限简化方案；用户随后批准实施，实验仍暂停。

## 候选核实与采用方案

用户确认保留能力判断，授权继续调查。2026-09-29检查候选源码，未安装、执行或替换候选。

| 候选与证据版本 | 已确认的能力 | 不适合直接替换的原因 |
| --- | --- | --- |
| mjakl/pi-subagent，8f12f490fb1b294bbb70a71605b0def3fc66142e | fresh默认、具名会话接续、模型/工具/思考配置、并行与usage | index.ts工具执行等待mapConcurrent整体返回，父不能后台继续；agents.ts无每角色skills/extensions配置，runner.ts继承父扩展参数；匿名fresh用--no-session，不保留等价原生会话；要求Pi>=0.87.1 |
| linearuncle/pi-cc-subagent，36b13cb3d53de15f05fc5ca9a16c25adcfa92cd2 | 后台、接续、完成通知、原生会话保存 | subagent.ts强制非简单调查/审查拆成2–5份；--no-extensions移除了子扩展能力；后台索引仅内存；stderr尾部只留2000字符 |
| 官方示例 | 独立进程、并行、流式、usage、取消 | README没有后台句柄和跨调用接续的同等承诺，只适合作为最小参考，不能声称可直接替换 |
| simple-subagents | 后台和显式查询/收取/取消 | 文档明确不提供原始stderr及异常协议内容、禁子扩展，不符合诊断与工具接线需求 |

源码只读副本在/tmp/factory26-subagent-research/mjakl及pi-cc；持久证据为上表固定commit及上游源码。临时目录丢失不影响定位。

### 决策建议

不推荐现在换依赖，也不建议为了去掉验收语义另造后台会话管理器。
先在当前锁定扩展中统一禁用自动验收，保留已使用的执行能力；这是有限简化，不等于整个扩展已变纯粹。
更换扩展的研究暂时收束：已检查候选均存在实质能力缺口，继续搜名字不足以支持迁移。

### 已实施范围

1. 在原生扩展共享acceptance解析边界统一返回none及空判据/检查/review，不再依据角色、任务关键词、async推断验收等级。前台、后台与动态子任务都调用该共享入口；不能仅改一个调用工具。
2. 同步精简LLM可见工具参数、说明和返回中的验收政策，不再要求逐次填写none/reason，不注入Acceptance Contract，不要求结构化验收报告，也不自动运行verify/reviewer。保留成功、失败、取消、退出码、原始错误和结果证据；执行成功仍不意味着任务达标。
3. 优先通过现有锁定依赖补丁交付，沿用runtime构建/缓存路径；不在Braid/SVC加入开关或新验收状态机。参数schema、运行前验证、格式化输出和恢复描述符已同步处理；显式请求旧验收策略或host gate会得到不可用说明，恢复描述符中的旧策略转为关闭状态。
4. 不删除诊断原始历史ledger，不改变既有异步/接续/取消、角色模型/技能/工具、fresh上下文语义。新执行不产生验收义务；旧结果仍可读。

方案验收：静态核对所有共享解析与格式化调用、适用的编译检查；不新增或运行设施测试。未来获授权的真实实验中核对前台/后台委派保持可用、无额外验收指令/自动review，原始错误与usage仍可追溯。实验暂停期间不宣称动态验收完成。
## 交付与反馈

采用独立的`harness/npm/patches/pi-subagents-0.56.0-acceptance-off.patch`，在已有completion-boundary补丁之后应用。
`scripts/runtime.py`的本地缓存检测、Linux源码身份记录与`submission/Dockerfile`都已接线。
缓存检测涵盖补丁的全部12个目标文件，包括内置帮助；不只记录补丁自身哈希。
当前运行缓存未直接改写，冻结制品未替换；下次依赖准备或构建才取得这些变化。

共享resolver统一none；evaluate入口也忽略旧执行描述符中的策略，既不运行verify命令也不形成review要求。
结构化结果不再附acceptanceReport字段；报告文本不再被自动剥离，子会话原文保留。
新执行的not-required不进入状态摘要；历史非空验收记录仍可查询。
模型、技能、工具、fresh历史、异步/并行、取消、会话接续及usage采集没有被重写。
Braid及SVC无修改。

静态反馈：
- 补丁dry-run对锁定依赖全部12个文件无偏移应用。
- 9个修改的TypeScript源码通过Node语法检查；runtime.py通过Python解析；非补丁文件的diff空白检查通过；补丁文件的上下文前缀属于unified diff格式，不按源码空白判断。
- TypeScript5.9.3完整类型检查不能通过：原依赖及其当前安装环境已有144条诊断（包含缺失peer类型及既有类型错误），修改后仍为144条，相同文件/诊断编号计数。唯一变化的诊断正文是既有never参数错误中打印的对象类型少了acceptance字段，不能将此记录为完整编译通过。
- 原始编译日志在`runs/iteration10/subagent-simplification/typecheck-{base,edited}.log`。
- 未新增/执行设施测试或模型实验；异步、恢复、真实错误、usage与历史读取的动态效果仍待获授权实验验证。
