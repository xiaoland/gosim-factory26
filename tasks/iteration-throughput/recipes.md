# 粗筛 Variant 与能力装配设计

状态：Human 已批准，作为技术方案的一部分。本页只定义本轮可解释的实验差异与配置所有权，不是活动配置或实验授权。

## 配置层次

`preset`不再作为独立概念。它目前只转抄profiles和defaults，没有自己的行为、生命周期或消费者；保留它只会让variant与preset形成一对一空壳。每个variant直接持有少量组合引用：内部agent-profile列表、Issue/PR默认assignee和SVC方法装配。具体模型、skills、MCP、原生sub-agents与context由各profile或角色文件持有；模型协议由共同catalog持有；实验task、venue、worker和package hash由run matrix持有。

```text
variant                  internal profile              native role
├── profile refs ───────▶ model / skills / MCP ───────▶ bounded child model/tools
├── default assignees    description / core/context
└── SVC method assembly

run matrix
├── variant ref
├── Factory task / venue
├── immutable package hash
└── concurrency limits
```

Factory展开variant并把内部profile投影为GitHub式assignee；Braid运行时只收到可指派身份、必要能力说明和provider binding，不收到variant、preset或profile术语。每个ARC-Bench task建立一个根Issue，description保存任务prompt与冻结requirement bundle入口；多个Issue可由同一内部配置形成多个独立Agent。

## 四个粗筛组合

本轮优先比较较大的能力差异，再对胜出区域做更窄消融。四组都使用Pi、Braid、同一SVC Corpus、同一skills版本、同一原生角色集合、同一browser/vision模型和同一打包入口；都不配置reviewer或contract-reviewer。

| Variant | 可见assignee / 内部模型 | Issue默认 | PR默认 | SVC装配 | 要回答的问题 |
| --- | --- | --- | --- | --- | --- |
| `pi-team-deepseek` | `deepseek` / DeepSeek V4 Flash | `deepseek` | `deepseek` | semantic index，方法按需读取 | 长上下文快速模型能否直接承担所有Braid工作项？ |
| `pi-team-glm` | `glm` / GLM 5.3 Flash | `glm` | `glm` | 同上 | 更便宜的GLM父Agent在相同原生能力下表现如何？ |
| `pi-team-mixed` | `glm` / GLM 5.3 Flash；`deepseek` / DeepSeek V4 Flash | `glm` | `deepseek` | 同上 | 两种快速模型作为可指派成员是否比同构配置更有效？Agent仍可按子目标选择任一assignee。 |
| `pi-team-vv` | 与`pi-team-mixed`完全相同 | `glm` | `deepseek` | 同一semantic index，并显式装载canonical Test Design与Verification | 相同团队中，显式V&V方法是否改善最终产品结果与诊断？ |

`pi-team-vv`是`pi-team-mixed + V&V`，不增加reviewer、模型、工具或额外审批。`pi-generalist`和`codex-generalist`退出活动variant；历史run仍作为基线证据，不改名或删除。Kimi不作为默认Braid assignee；Qwen只有在精确的`qwen-3.8-flash`出现在比赛网关并通过协议spike后才进入后续组合，不用Max替代。

## 内部profile与assignee投影

两份profile具有相同的非模型能力，使粗筛主要观察父Agent模型与异构协作差异。名称是当前设计占位；最终CLI形态由assignee投影spike冻结。

| 内部配置 | Agent可见身份与能力说明 | model / reasoning | skills | MCP | Pi原生sub-agents |
| --- | --- | --- | --- | --- | --- |
| `pi-deepseek-fast` | `deepseek`：适合长上下文、有边界的需求理解、实现与整合；可读完整任务材料与创建/承接Issue、PR | `deepseek-v4-flash`；使用网关实际支持的reasoning形态，不强写未知枚举 | Impeccable、Ponytail作为按需能力；SVC由共同导航提供 | 无 | explorer、executor、browser-operator、vision、specialist |
| `pi-glm-fast` | `glm`：适合通用需求理解、设计、实现与整合；成本较低，可创建/承接Issue、PR | `glm-5.3-flash`；使用网关实际支持的reasoning形态 | 与DeepSeek相同 | 无 | 与DeepSeek相同 |

能力说明只投影适用问题、输入/工具能力、重要限制与成本等级；不展示模型路由字段或“profile”对象。assignee不是岗位，也不拥有某类Issue。Agent对当前work-item持有责任，并通过GitHub式`--assignee`或`--remove-assignee/--add-assignee`决定谁承接另一个work-item；每项最多一个active assignee。

## 共同Pi原生角色

原生sub-agent只服务当前work-item的session tree，不创建Issue，也不出现在assignee列表。父Agent根据问题直接委派；Harness不按关键词、失败次数或阶段自动调用。

| 角色 | 模型 | tools / skills | 有界返回 |
| --- | --- | --- | --- |
| explorer | DeepSeek V4 Flash | 只读源码、搜索、必要的只读shell；无MCP | 一个事实、约束或证据问题的压缩结论、来源与残余 |
| executor | DeepSeek V4 Flash | 文件编辑、shell、git局部检查；Ponytail、Impeccable、agent-browser按需；无MCP | 一个已授权局部效果、反馈、修复和可消费commit/材料 |
| browser-operator | DeepSeek V4 Flash Vision Exp | agent-browser CLI、截图、DOM、console/network观察；无MCP | 一段明确用户旅程的观察、复现或验收证据 |
| vision | DeepSeek V4 Flash Vision Exp | 明确图片输入与只读材料；无浏览器控制 | 带源路径的视觉事实、布局关系与不确定性 |
| specialist | Kimi K3 | 只读材料与必要搜索；不直接写共享状态；无MCP | 结构性复杂且普通路径未收敛时的一次独立建议或反例 |

browser-operator直接消费截图，不经vision二次转发；vision处理requirement bundle中的参考图或已给定图片。Kimi慢且昂贵，只由父Agent针对真正复杂的有界问题显式调用，不自动升级。reasoning统一避免xhigh/max；每个模型的实际字段必须由网关spike确定，不能用一个字符串假装协议相同。

## 与ARC-Bench需求的关系

完整requirement bundle、参考图、复杂状态/实体关系、暂态交互、搜索筛选、认证会话和浏览器可观察结果要求通用应用工程、视觉读取和多边界V&V；它们没有证明应设置UI/App/Reviewer岗位，也没有要求外部系统MCP。共同能力因此提供视觉、真实浏览器、局部实现反馈与SVC方法；Braid级拆分仍由Agent根据完整子结果、独立验收、上下文和并行收益决定。

四组必须先通过模型文本tool call、图片传递、浏览器截图、原生角色加载和assignee协作的最小spike。若一个配置声明了skill/MCP/role但运行环境没有消费者或真实加载路径，静态资格直接失败；不在完整benchmark中第一次发现。
