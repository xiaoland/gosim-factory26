# Hackathon 能力改进设计复核稿

2026-09-25 用户已认可技能取舍与 SVC 拆分方案。
具体计划与预演已完成，见 [实施准备](implementation.md)；本范围已获开工授权，下一次实验待当前结果后决定。
主线是让 Agent 更容易找到适用知识、实现真实产品行为、取得可信反馈，而不是增加工具或角色数量。

## 从公开需求出发

GitHub 的 47 项原子需求包含持久账户/session、组织与团队、非简单累加的仓库权限、提交/分支、Issue、Review 与 Merge 状态。
Sheet 的 24 项原子需求包含持久 workbook、选择和键盘操作、CSV、公式依赖与引用迁移、撤销重做、排序/过滤/validation/pivot。
这些范围来自公开 requirements，具体 ID 与约束见 [需求映射](requirements-fit.md)，不来自隐藏评分器。

候选列表中最需要补充的是两题各自的状态与行为知识，而非再加通用代码审查角色。
其中一部分可由成熟库承担，一部分仍必须由 Agent 根据需求设计；技能使它能正确评估和使用库，不替它作选型决定。

## 建议范围

```text
活动 variant：pi-team-mixed
├─ 领域资料
│  ├─ Sheet：HyperFormula；Handsontable
│  └─ GitHub：Better Auth；organization 插件
├─ 两题共同的实现与观察
│  ├─ fixing-accessibility
│  ├─ 继续使用 agent-browser 与现有 browser-operator
│  └─ rg / ast-grep / Context7 / Exa；专用 Docs MCP 按需
└─ SVC 方法的发现与采用
   ├─ task-packet
   ├─ investigation
   ├─ design
   ├─ implementation
   └─ verification（含实施前的检查设计与实施后的结果判断）
```

领域技能建议进入下一轮的可发现材料，但不会预装这些应用库或要求必须使用。
主会话与实施角色可在选型或遇到该库问题时选读；不会以题目名在 Harness 中决定调用哪个技能，也不改变 Braid 的职责。
技能入口先介绍何时有用和覆盖边界，完整 API、版本迁移、长示例放按需资料。
Handsontable 当前入口过长，采用前需确认精简导航和上游版本资料的组织方式；不把 41 KB 内容加进主提示词。

两题都引入 fixing-accessibility 的具体交互知识，尤其名称、焦点、键盘和状态表达。
保留现有浏览器子角色；让它依据委派的旅程与判据观察应用，不新增固定 reviewer 或强制全量审计步骤。
agent-browser 已有配置与分发；playwright-cli 保留为出现具体能力缺口时的替代候选，当前不双重安装。

Handsontable 官方 Docs MCP 是一个有明确领域增量的候选，通过现有 MCPorter 使用即可，不建设新的 MCP 管理层。
先用本地技能与现有 Context7，遇到覆盖或版本不足时使用专用服务。
此建议不证明官网容器可联网，联网结论仍需来自实际生成环境。

SVC 拆分与来源比较见 [路由提案](svc-routing.md)、[候选调查](candidates.md)。
将 Test Design 与 V&V 放在同一个技能，是为了让“如何判断”与“证据究竟支持什么”保持联系。
把调试并入 investigation，同时复用已有 diagnosing-bugs 的有用内容；不同时保留多个互相竞争的调试 SOP。
对 verification-before-completion 主要吸收直接的触发方式和声明对应证据的表达；其核心判断多数已经存在，不为“吸收”而增加重复段落。

## 需要提前澄清的落地问题

实施准备中只解决可能改变路线的实际问题：

1. Pi 主会话和 pi-subagents 对显式 skills 的加载行为；分别保留独立历史、角色 SOP 和按需深读，避免同一正文重复注入。
2. 五个 SVC 技能的自足分发、跨资料链接与角色方法来源。使用现有 skill 文件复制，不引入注册中心、preset 或通用路由器。
3. 库技能的适用版本与依赖条件。Handsontable 的 grid 语义与精确 ARIA、HyperFormula 的错误/引用规则、Better Auth 的固定码/权限模型是选型时应检查的边界；Harness 不为每个库写适配实现。
4. 专用 MCP 使用实际 schema 和版本范围；读已知文档足够时，不以联网调用作为强制步骤。

实施顺序建议为：整理 SVC 来源和路由 → 接通当前 variant/角色 → 加入领域及可访问性资料 → 固定构建材料 → 已授权真实实验。
尽量复用现有 Linux runtime；只有实际新增工具依赖才重建资源。
具体文件计划、原生接口核实与独立预演已经完成，当前实施范围已获用户授权。

## 建议验收

本轮先等待当前冻结实验的终态，保留作为基线；源包身份、失败阶段与得分必须分开报告。
下一轮以同一 `pi-team-mixed` 的 GitHub + Sheet 完整官网评分为最终验收，运行授权单独记录。

过程证据回答四个问题：

- 遇到真实需求/失败时是否找到对应方法或领域资料，而不只是文件存在？
- 读取后的知识是否进入了具体设计、实现、观察或修复？
- 验证是否走过规定的用户路径、持久化和状态变化，而不是只看 build 成功？
- 新材料是否造成无关阅读、选型锁死、重复验证或其它可见成本？

方法没有被使用时，先区分未暴露、触发不清、任务不需要与 Agent 自行选择；不以强制调用次数制造成功。
两次整包结果只能证明组合表现变化，不独立归因于每个技能。
不新增 Factory/Corpus 测试，不以源码阅读或目录合规代替行为验收。
