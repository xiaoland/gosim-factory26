# 产品职责与关键时序

图中的实线描述本轮基线行为；标为“建议”的部分尚未实现。实现缺陷的独立证据见 [技术拓扑](architecture.md)，需求判断与取舍见 [产品审查](product-review.md)。

## 职责拓扑

```mermaid
flowchart TB
    H[用户与调用方<br/>目标、执行范围、验收方式]
    L[LLM 成员<br/>分工、方案、代码、交接、完成判断]
    O[Braid 对象<br/>Issue / PR / comment<br/>描述、回复、resolve、hide、身份]
    E[Braid 投递<br/>收件范围、事件、批次、去重]
    C[Braid Context<br/>当前对象投影、失效与替换]
    R[Braid 执行边界<br/>provider 根会话、身份 fencing、恢复]
    G[Braid Git 环境<br/>每项 clone、共享 origin、merge intent]
    P[Pi 原生子代理<br/>生命周期与清理由 Pi 负责]
    X[外部验收与归档<br/>具体 commit、原生证据、应用行为]
    H --> L
    H -->|选择本次执行范围| R
    L -->|语义决定与可编辑事实| O
    O --> E
    O --> C
    E -->|实际待处理输入| R
    C -->|初始或替换输入| R
    R -->|唤醒可执行成员| L
    L -->|实现与合并决定| G
    R -->|Pi 根协议| P
    G -->|确切交付 commit| X
    R -->|原生会话身份与执行证据| X
    H --> X
```

需要审查的是 O→E 的默认收件范围、O→C 的失效条件和 O→R 的关闭规则。LLM 决策、Pi 内部生命周期和外部验收均不应被吸入这三个接口。

## 真实新增评论为何进入 reset

```mermaid
sequenceDiagram
    participant A as 评论作者
    participant O as LocalObjects
    participant Q as 事件与 batch
    participant D as prepare_dispatch
    participant S as 原 provider
    participant N as 新 provider
    A->>O: 新增评论或回复
    O->>Q: 同事务保存 comment + Wake
    Q->>D: 有真实输入的 runnable batch
    D->>O: 重新渲染完整当前 Context
    O-->>D: 比原会话初始 Context 多了评论
    D->>Q: 因 revision 不等创建 Invalidate
    Q->>S: 进入既有 reset 协议
    Note over S,N: 当前协议保留通知、自然收尾和 teardown 边界<br/>归档证明 applied reset 及实际旧新 Context 配对
    S-->>N: 旧会话替换为新会话
    D->>N: 完整 Context + 原待处理输入
```

Sheet reset `01a0e209-71fd-7700-a447-1c2c10939fe4` 的新增内容只有系统 comment #5；GitHub reset `01a0e230-b9b6-74a0-912e-9a805e63b9c1` 的新增内容只有开工提醒 #7。建议只改变是否产生 Invalidate：新增评论继续使用 Wake，真正修改既有正文仍走同一 reset 协议。

## 普通回复的收件范围

```mermaid
flowchart LR
    A[成员回复根 Issue 的 comment 180<br/>GitHub comment 203] --> O[保存 reply_to 与 thread_root]
    O --> S[取整个工作项关注者<br/>加当前 assignee、当次 @]
    S --> U[旧具体成员<br/>返回 unreachable]
    S --> W[仍负责开放工作项<br/>创建 Wake]
    S --> T[仍负责关闭工作项<br/>创建 direct_contact]
    W --> B[现有批次与调度]
    T --> B
    B --> L[LLM 自行决定是否行动或公开回复]
    L -.公开回复可能再次扩大通知.-> O
```

comment #203 有 9 个收件目标，归档中 1 delivered、3 queued、5 unreachable；不能画成 9 个已完成执行。建议收件集合改为当前 assignee、同讨论参与者、当次 @ 和显式全项关注者，不新增语义过滤或另一套消息执行机制。

## 关闭对象与执行生命周期的交叉

```mermaid
stateDiagram-v2
    [*] --> Active: 已指派
    Active --> Finalizing: close 或 merge
    Finalizing --> Resetting: 当前 Context 失效
    Resetting --> Finalizing: 替换后保留 finalization 身份
    Finalizing --> Sleeping: finalization 完成
    Sleeping --> Contact: 实际消息或关注通知
    Contact --> Resetting: 需要当前 Context
    Contact --> Sleeping: terminal_contact 完成
    Sleeping --> Active: reopen
```

此图只表达审查涉及的主要关系，不是完整数据库状态机。最小建议移除“close 必须再授予一个执行机会”的承诺，仍保留正在执行的自然结束、实际关闭通知、晚到评论和原成员身份。不能将图简化成“关闭即杀进程”，也不能取消未知执行的恢复证明。

## Local 当前的推进与结束政策

```mermaid
flowchart TD
    T[Local 检查持久状态] --> A{根与全部对象终态<br/>且没有 unresolved merge?}
    A -->|是| F[不再为关闭后的通知延长运行<br/>保存 delivery commit 并返回 quiescent]
    A -->|否| W{有输入、执行或恢复?}
    W -->|是| R[按现有调度推进]
    W -->|否| I{根开放且连续空闲五分钟?}
    I -->|是| C[Braid 写入进度检查 comment<br/>向根负责人投递]
    C --> R
    I -->|否| P[等待或报告具体阻断]
    R --> T
    P --> T
```

这一政策不是任务质量验收。根开放时五分钟检查是用户明确要求，保留。建议先明确单次执行范围及结束请求，再决定是否要求所有对象终态；不能仅靠增加退出分支把持续协作和单次交付的冲突隐藏起来。实际关闭顺序和正在执行的收尾仍需独立验证。
