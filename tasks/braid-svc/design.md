# 已复核方案

状态：用户已确认本文件所述修订方向。详细验收设计见 [verification.md](verification.md)，实施顺序和变更授权见 [plan.md](plan.md)。尚未完成的源码草稿不能证明该方案已实现。

## SVC 与原生核心

Codex 使用 app-server，Pi 使用原生核心接口。两者保留纯净对照；backend、是否使用 braid、是否注入 SVC 是独立选择。SVC 不调用 braid，braid 不调用 SVC。

user-scope AGENTS.md 只保留简短导航，拟定原文如下：

```text
SVC 方法通过 svc lookup 查询；用 svc lookup --help 了解查询方式。
先阅读 svc lookup --path index.md，再按任务需要逐步读取相关条目。
```

无人值守、运行授权、比赛输入与隔离约束归 Factory26 任务契约；详细方法归 Corpus；Issue/PR、CLI 和角色规则归 braid 运行指令。不要把这些内容重新混成一份 user-scope 指南。

## braid 产品边界

保留 Issue、PR、comment、关联、生命周期、Agent Group、上下文投影、调度和本地 branch/worktree。PR 不是 implementation.md，Issue 不是 design 阶段标记。实现中发现设计问题可以修订关联 Issue，但不强制角色双向交接或固定执行若干阶段。

Agent 使用 braid CLI 读取和修改对象，覆盖 description edit、comment create/hide/unhide/delete、PR ensure 和 context/status 查询。CLI 修改对象后自动产生语义事件，不要求 Agent 再调用 refresh。comment hide 可恢复，delete 留墓碑；两者都保留身份和生命周期，但正文不得进入当前可见上下文。

当前完整对象以本地持久存储为唯一权威。CLI 写入正文和语义事件同事务完成，随后沿用投影、queue/group/session 处理链；不维护另一份可独立修改的 Markdown 镜像。不建设 GitHub 仿真 HTTP 服务或通用平台插件框架。

裁减的是 Factory26 braid 工作树里的 GitHub App/auth、webhook、远端分页/回读/写入重试、tunnel、公开 attribution/reaction/status 和远端 PR 创建补偿。原相邻上游工作树保留。现有 SQLite 元数据缓存不等于已经具备本地对象存储，需在实施中补齐完整正文权威。

## 事件与会话

当前正文、可见 comment 集合或关联图的变化，按对象依赖关系影响相关 Agent；完整上下文重建保留逻辑 group 与 worktree，替换不再适用的物理会话，并阻止失效输出继续驱动控制操作。不能只更新 revision 就声称模型已收到新正文。

自身写入沿用“不因自身回声打断当前 turn 或额外自唤醒”的规则；后续有正当唤醒时必须自动获得当前上下文。CLI 需要记录实际 writer group/turn，不能把所有 Agent-origin 写入整体忽略。其他组按目标及关联关系接收变化；跨面 description 失效和一般关联变化不能无差别打断所有 Agent。具体事件样本须进入验收。

Factory26 将需求建立为根 Issue，生成完成来自工作项、关联 PR 和明确交付分支的收敛，不能使用一次 provider turn 结束替代整个生成完成。

## 预演收束的交付条件

以下实施细化已随详细验收完成复核，尚待实现。根 Issue 的现有 Agent 判断需求是否满足；PR Agent 自检后标记 ready，相关事件经现有队列通知 Issue group。根 Issue Agent 可在已有 turn 接受并合入多个 PR，不增加固定审查轮数或新的协调角色。一个 Issue 可有多个 PR，一个 PR 可关联多个 Issue；重复请求以 comment 身份保持幂等。

Factory 在本次隔离目录初始化应用 Git 仓库和基线，运行授权允许其中的本地 commit/merge。原 prompt 的禁止提交需要同步调整；禁止 push 和修改开发源码仓库的边界仍由 Factory 保证。这与本项目实施前提交的协作门槛是两件事。

根 Issue 使用明确的 delivery branch。必要 PR 合入、未完成事项被明确处置、交付树自检结束后，根 Issue Agent 才能声明 completed；未处置引用应作为具体阻塞返回。Braid 等 close/merge 后的 finalization 与待执行、待 reset、当前未决执行全部收敛，停止后续控制写入，再返回固定交付 commit。Factory 从该 commit 导出应用并校验冻结身份，不能取初始目录、最后会话或最新 worktree。Git ref 更新和对象状态写入并非同一事务，合并中断必须按已记录输入与实际 Git 结果恢复。

无待处理事件、延迟任务或可恢复执行，但根需求仍未完成时，返回可诊断的 incomplete；不靠无限等待人类或自行重复唤醒掩盖停滞。真实应用测试失败可以形成有效成绩，运行基础设施的缺失或未知终态不能记为成功。

## 诊断是独立交付

优先复用 ARC-bench 本地报告、页面快照、截图/视频/trace，以及平台 SDK 的运行/需求事件与显式 traceability。默认展示失败层、实际与预期差异、最近有效进展、观测时间、关联证据和缺失关联，不堆叠所有元数据或原始日志。

查询顺序为失败状态 → 页面/源码事实 → 竞争解释与区分性检查；只有需要解释生成过程时，再经工作项/会话映射进入 SVC match/trace。原生 rollout 用于明确的恢复或审计。证据保留生产者与版本，不将 Agent 自报关联、平台状态或模型声明自动当作因果证明。

## 共同开发

`sources/svc` 和 `sources/braid` 是独立 Git 仓库，直接修改、检查和构建。每次运行归档实际源码，包括未提交改动；源码变更后不得误用旧安装。官方评测器和浏览器缓存继续复用。旧 runs 与旧成绩保持原样，不被新实现补写或重新解释为新版本成绩。
