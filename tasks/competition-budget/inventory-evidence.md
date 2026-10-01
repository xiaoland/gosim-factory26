# Factory26 迭代与遗漏证据树

盘点时间：2026-09-26。本文只整理已有文件、结果目录和 Git 历史；“packet 写成完成”不等于真实实验已验证。

状态标记：

- `[已实现]` 有源码/制品或提交证据；`[已验证]` 有真实运行、模型调用或评分证据。
- `[待验证]` 有设计、静态检查或冻结包，但缺少目标行为的真实证据。
- `[暂停]` 明确停止、取消或外部阻塞；`[被替代]` 当前入口已迁移；`[状态不明]` 当前材料不足以判断。

## 当前接续点

```text
Factory26
├─ 竞赛预算与最新实验
│  ├─ A：4c17843 清洁应用回放（自购 key、self_funded、0 次生成）
│  │  ├─ [已开工/待验证] 已有冻结回放包和官网 run
│  │  └─ 尚无分数或干净部署终态
│  ├─ B：修复后的 pi-team-k3-root-only 完整 Hackathon
│  │  ├─ [已获开工] 当前授权禁止使用参赛额度
│  │  └─ 新冻结包、生成和评分证据尚未出现
│  └─ 旧 K3 root-only 接续
│     └─ [暂停] 参赛额度停用后已取消；旧包和状态只作历史证据
└─ 主线结论
   ├─ 代码和静态材料已经多轮演化
   ├─ 行为验证仍是零散探针、Lite 评分和有污染/混杂因素的官网运行
   └─ 当前工作树大量未提交；包、commit、运行目录不能默认代表同一版本
```

证据：`tasks/competition-budget/packet.md`、`tasks/competition-budget/experiments.md`；A 的 `runs/competition-budget/20260926/replay/replay-provenance.json`、`official/state.json`、`official/tasks/hackathon--github/status.json`（当前 `STARTING`、`score=null`）；旧 B 的 `runs/k3-root-only/20260926/official/status-after-budget-stop.json`。用户本轮已明确 A 自费回放、B 修复版全 Hackathon、禁止参赛额度；packet 中“待用户复核”的旧表述与此授权冲突，应以本授权为准。

## 1. SVC CLI、Corpus 与 skill 化

```text
SVC
├─ CLI 裁减
│  ├─ [已实现/已验证静态] 删除参赛运行时 task init/grow 和专用 Corpus 测试，保留 lookup
│  └─ [被替代] 后续不恢复参赛 CLI，入口转到 skill 接线
├─ 完整 skill 接线
│  ├─ [已实现] sources/svc/SKILL.md、references、assets；四 variant 去掉 --svc-corpus 和二次装配
│  └─ [待验证] 尚无新材料驱动的真实模型读取、采用和评分
├─ Corpus 增强
│  ├─ [已实现] 正文改稿和编辑复核
│  └─ [待验证] 材料提供、实际选读、影响行动三层尚未在新入口闭环
└─ Hackathon 技能路由
   ├─ [已实现/待验证] 五个 SVC skill、领域候选 skill、MCP 接线和材料打包完成
   └─ [待验证] 不能用 ZIP 内存在 14 个入口证明模型选读、MCP 返回或技能收益
```

证据：`tasks/svc-cli-simplification/packet.md`（241 项 SVC check、Factory 139 项静态检查，无评分）；`tasks/svc-skill-integration/packet.md`、提交 `4ab6165`（SVC 源仓库提交 `b5a0fb8`）；`tasks/svc-corpus-review/packet.md`、`implementation.md`、`overfit-audit.md`；`tasks/hackathon-capabilities/packet.md`、制品 `runs/hackathon-capabilities/20260925-pi-team-mixed-skills.zip`（SHA `ad47f4…`）。

关键遗漏：没有同一需求、同一模型、同一 runtime 下旧 CLI/单 skill/五 skill/完整 skill 的行为对照；没有稳定记录“读了哪一份、用于哪一个决定、结果被谁采用”；SVC 的真实行为验收未因 Lite 分数自动关闭。

## 2. 独立 variant、DX 与可交接性

```text
开发体验与装配
├─ 四个独立 variant
│  ├─ [已实现] 每个 variant 拥有自己的 Harness、指令和运行资源
│  ├─ [已验证静态] 四组物化接口预演、输入基线与包差分
│  └─ [待验证] 未证明真实生成时相互隔离且改变只影响目标 variant
├─ DX 第二轮
│  ├─ [已实现/已验证操作] 记录查询、local_experiment 归档、开发 SVC 显式安装、bundle/补丁恢复
│  └─ [待验证] 尚无跨机器恢复和后续新实验的端到端证据
└─ 当前交接
   ├─ [已实现] 来源、工作区补丁、浅克隆信息分别归档
   └─ [状态不明] 恢复产物与当前冻结包、远端 run、未提交 index 的对应关系不具原子性
```

证据：提交 `7bb2c60`；`tasks/independent-variants/{packet,verification,rehearsal}.md`；`tasks/developer-experience/{packet,remaining}.md`；`runs/developer-experience/recovery*`。DX 已明确不以旧 ZIP 或模型额度错误冒充当前验收。

关键遗漏：变体独立性的真实模型证明、依赖/runtime 在 WSL 和官网的一致性证明、从运行身份到恢复目录的可重放关系；工作树当前 dirty，必须把“源码 HEAD、未提交差异、制品 SHA、run journal”作为四个独立字段记录。

## 3. Braid 协作、共同 Git、assignee 与交付

```text
Braid
├─ 早期协作对象
│  ├─ [已实现/局部已验证] thread/reply、resolve/hide、reaction、父子 Issue、参与者路由、上下文重建
│  └─ [待验证] 多个同类 Agent 的真实协作和完整 bench 未形成证据
├─ 身份与 assignee
│  ├─ [已实现] profile 与具体成员名分离，指派返回成员身份
│  ├─ [已验证失败现场] 旧运行中 Agent 曾把成员名当 profile/assignee 使用，错误反馈含糊
│  └─ [待验证] 重复指派、改派、恢复、上下文重建和失败反馈的全链路
├─ 共同 Git
│  ├─ [已实现/静态验证] bare origin、工作项 clone、发布 head/base、PR 合并和 Factory 从 origin 导出
│  ├─ [已验证局部] 4/100 运行中五个 PR 合并、最终集成提交导出，旧 WIP 交付问题消失
│  └─ [待验证] Issue→PR 是否一直承接真实 head、根是否取得子任务交接、合并后是否按正确 commit 验收
└─ Factory 交付
   ├─ [已实现] 分批指派、共享基础负责人、并发上限、空交付错误
   └─ [已验证缺口] 根 Issue 未收到子任务完成交接；最终应用自验与官方浏览器结果严重不一致
```

证据：`tasks/braid-collaboration/packet.md`、`design.md`、`verification.md`、`identity-preflight.md`、`git-preflight.md`、`factory-preflight.md`；`tasks/braid-usability/packet.md` 及 `results/`；`tasks/multi-agent/packet.md`；旧运行 `runs/braid-collaboration/20260926-hackathon-v2/`（GitHub `b77e4357a4e1`，4/100）；提交 `16cdfb3`、`727c3c0`。

关键遗漏：没有“交接已发出/已送达/已被根采用”的三段证据；没有同一实际实现的 PR head/base/祖先关系与最终导出 commit 的统一报告；Sheet 旧 PAUSED run 外部阻塞，不能以 GitHub 4/100 代替完整 bench。Braid 不应被描述为替代 V&V 或自动判断完成。

## 4. V&V、最终验收与可追溯性

```text
验收闭环
├─ 一般工作流程
│  ├─ [已实现] 将“设计最终验收方案”补回既有流程；reviewer 作为独立 variant 维度
│  ├─ [已验证设施] 两个 variant、71 项公开场景入口、修复 runtime 依赖后重新冻结
│  └─ [待验证/状态不明] v2 生成与 71 项回放在当前仓库没有最终评分报告
├─ 子 Agent 能力
│  ├─ [已实现/静态预演] fresh context、SOP、工具和角色装配、Context7/Exa 接线
│  └─ [待验证] 实际 spawn 参数、子会话上下文、真实工具返回、局部产出被父 Agent 采用
├─ 端到端追溯
│  ├─ [已实现公共接口] ARC history/traceability CLI、固定 SDK、mixed 薄接线，提交 `896e3a8`
│  ├─ [已验证限制] 官网 traceability 的 interfaces/tests 为空，commit-history 为 workspace_unavailable
│  └─ [待实现/待验证] 实际事实生产者、重试 lineage、测试/应用/提交关系和接收失败状态
└─ 实验基础设施
   ├─ [已发现] 取消/失联后 queued 不收敛、retry_of 缺失、OTLP 拒收不持久化、环境/镜像未完全绑定 run
   └─ [暂停] 用户要求先停止可追溯性方案和下一轮实验，待新决策
```

证据：`tasks/acceptance-workflow/packet.md`、`design.md`、`verification.md`、`runs/acceptance-workflow/20260926/`；`tasks/factory-subagents/{packet,verification}.md`；`tasks/experiment-traceability/packet.md`、`preplay.md`、`technical.md`；`tasks/official-runtime-observability/packet.md`；`runs/braid-collaboration/20260926-hackathon-v2/` 的 `traceability`/`history-publication` 记录。

关键遗漏：自编浏览器断言不能代替官方用户场景；没有把“最终提交、干净数据库、实际部署、最后一次验收”绑定为单一可追溯链；没有可靠区分未配置 OTLP、发送失败、接收失败、尚未结束和数据丢失；没有把 retry、controller、job、run、report 关系写入统一身份。

## 5. 独立 reviewer、能力材料与模型实验

```text
实验演化
├─ Lite 基线
│  ├─ [已验证] 官方 API Lite：Keep 23/32、BookStack 26/34，合计 49/66
│  └─ [已验证限制] 真实轨迹只有 GLM 根客户端；SVC 只在 Keep 被读取，未证实 V&V 正文采用
├─ 公开本地矩阵
│  ├─ [已验证局部] 历史本地场景、独立分析、环境/评分差异记录完整
│  └─ [待验证] 本地公开测试不是官网隐藏测试，不能转写为官网百分制
├─ 根模型对照
│  ├─ [已验证结果但不可归因] mixed 4/100，K3 root 11/100
│  ├─ [已发现混杂] 3000 端口冲突、旧服务污染、K3 实际参与子 Issue/PR、两次 runtime/提交差异
│  └─ [暂停] root-only 接续因额度政策取消；不能以 11/100 证明根模型净收益
├─ 三模型短探针
│  └─ [已验证有限事实] GLM、Kimi K2.7 Code、Kimi K3 均选择补最终浏览器验收；短摘要探针不能替代长运行
└─ 自购模型 API
   ├─ [已验证有限] Kimi/GLM/DeepSeek 各一次 Chat 请求 200、答案 391
   └─ [待验证] 流式、工具、视觉、统一网关和完整 Hackathon 仍无证据
```

证据：`tasks/hackathon-team-baseline/packet.md`、`results/interface-official-lite.md`；`tasks/local-run-analysis/packet.md`、`reports/2026-09-23-local-agent-process.md`；`tasks/k3-root-experiment/packet.md`、`results/7b533d7bd71b.md`；`tasks/braid-collaboration/results/model-validation-probe-20260926.md`；`tasks/external-model-providers/packet.md` 与 `runs/external-api-check/20260924T041240Z/`。

关键遗漏：没有在同一干净基线隔离 root 模型、skill、runtime、部署、协作和最终验收的单变量对照；没有把“模型实际请求成功”与“模型完成产品任务”分开统计；模型额度/计费字段曾与请求 credential_mode 不一致，必须保留请求模式和平台返回模式两列。

## 6. 后台执行与生命周期（近期迭代）

```text
长任务能力
├─ [已实现静态] pi-background-bash 1.0.5、pi-lane、pi-pending 接入 pi-team-mixed 主成员和有 Bash 权限的内部角色
├─ [已验证静态] 锁文件、包内容、启动器、扩展显式加载和 diff 检查
└─ [待验证] RPC 下超时交还但进程继续、同一执行句柄续等、自然完成/显式停止/整体取消，以及三层会话收尾
```

证据：`tasks/issue-decomposition/packet.md` 的后台插件调查与实施记录；`tasks/iteration-throughput/packet.md`、`cells/vv-local-failure.md`；`runs/acceptance-workflow/20260926/npm-archives/` 和修复后 runtime ZIP。

关键遗漏：插件作者的 headless 证明不等于本 variant 的 Braid RPC 端到端证明；内部角色 `extensions: ""`、提升依赖路径和自发后续回合的归属都需要真实轨迹。旧长任务失败显示，普通 Bash 管道悬挂、残留服务和持久化断言错误仍可能让 Agent 自验收失真。

## 7. 最关键的待补证据（按影响排序）

1. **最终交付 V&V**：对同一最终集成 commit，在干净初始数据、无旧 3000 端口服务的环境启动，记录部署身份、用户可见浏览器流程、应用自验、导出 commit 和官方评分。A 回放只回答已有应用质量，不替 B 的生成过程。
2. **交接与 Git 关系**：每个 Issue/PR 记录 profile、具体成员、head/base/OID、交接 comment、送达结果、根采用结果；把“未发出、未送达、送达未执行”分开。
3. **能力消费证据**：对 SVC、领域 skill、原生 sub-agent、MCP、后台 Bash 记录提供、读取、调用、产出、采用五个事实；未调用要区分未暴露与模型未选择。
4. **实验身份**：为 matrix/controller/job/retry/run/report 统一保存 `retry_of`、输入包 SHA、源码 HEAD+dirty diff、runtime/镜像、模型/credential_mode、测试快照和环境标签。
5. **遥测完整性**：持久化 OTLP 发送/接收拒绝、批次缺失、collector 生命周期和补采边界；不得用“有批次”推断“会话完整”。
6. **预算与可比性**：A、B 均使用 self_funded，保留官方返回的 billing_mode 但不将其单独视为授权依据；任何新分数不得与旧 4/100、11/100 做无条件因果比较。
7. **工作树与制品一致性**：当前大量源码、文档、skill、variant 和任务包未提交；新实验前必须明确冻结 commit、允许的工作树差异和 ZIP 内容，避免把未提交修复误归因于 variant。

## 8. Git 迭代锚点

主要演化节点：`4ab6165`（SVC skill 迁移）、`7bb2c60`（独立 variant）、`a6d5276`/`b15570f`（子 Agent 方法与工具）、`08f177a`/`e0c3ca2`（Braid 协作）、`e229e6b`/`f8228df`（multi-agent 接入规划）、`896e3a8`/`10f3665`（ARC 公共追溯接口）、`727c3c0`（验收流程与 reviewer variant）、`ad0a627`（修复后本地矩阵现场）。这些提交证明历史演化和部分实现边界，不自动证明当前 dirty 工作树或新冻结包已通过行为验收。
