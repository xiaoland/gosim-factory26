# 独立问题清单（对账前）

这是初始待证问题，不是最终结论。进一步核对已确认 review-required 不阻断完成/返回，相关优先级和方案以 report.md、packet.md 为准。

1. 平台级运行约束只放根工作项正文，独立 Braid 子 Issue 与 fresh 原生子角色不会自动得到；当前仍依赖人工转述，存在真实输入缺口。
2. 原生角色只读契约与 runtime 的实现意图/验收推断分离：旧 vision 读取 UI 文案被要求 mutation tools；后续成功 run 仍被标 review-required，并要求 Implement the requested change。当前 completionGuard:false 只关闭 mutation guard，不自动改变 acceptance inference；须核对当前 runtime。
3. 当前 executor 默认异步实现任务可能自动产生 reviewer 必须复核要求，而配置仅 advisor/explorer/executor/browser-operator/vision 且 disableBuiltins；原生 acceptance 与 Braid 最终验收是不同边界，未看到权威接线说明。这是可触发缺口，不据未调用判失败。
4. profile 的整合段同时让 PR 负责人「再合并交付、关闭根 Issue」和让根负责人「判断完整交付并关闭根项」；真实职责主语漂移，建议留下根负责人唯一闭环权威。
5. 当前后台 rule 在 profile 尾部及 subagent 使用段重复 service:true 与主动停止；browser 角色再注入 skill，重复 session 规则。可局部合并，不删 fresh 子角色自包含的约束。

待排除：Pi 基础 coding assistant 不与只读角色必然冲突；SVC 无人等待/授权常规规则未见反向要求；设计/实现工作流与 role-specific application 不因词相近判冲突；技能元数据不是正文；未观察 advisor/executor 调用不能证明缺陷；旧冻结目录当前文件不能替代历史 toolResult 读到的内容。
