# 系统拓扑与关键时序

以下拓扑按当前工作区实现绘制。来源快照证明了空批次回环；冷恢复与 Codex reset 的路径由源码确定，尚未用当前二进制重放。

```mermaid
flowchart TD
    H["宿主：request.json / 启停 / 归档 / 应用验收"] --> L["braid local\n运行锁、调度推进、退出与交付 ref"]
    L --> D["每 profile × Issue/PR 的 GroupDriver\n持有多个活动工作项会话"]
    D --> S["StoreActor / SQLite\nassignment、事件、batch、turn、reset"]
    D --> C["Context projector\n当前对象、可见评论、直接关系"]
    C --> O["LocalObjects / SQLite\nIssue、PR、comment、关注与成员"]
    A["LLM：理解需求、分工、讨论、验收、关闭决定"] --> CLI["braid 对象 CLI\n执行身份校验"]
    CLI --> O
    O -->|同一事务写入语义事件| S
    D --> M["SessionManager\n本进程临时句柄、已停止集合"]
    M --> P["SessionFactory / AgentProvider\nPi RPC 或 Codex app-server"]
    P --> A
    P --> N["原生会话与消息记录"]
    P --> PI["Pi 自己的扩展与原生子代理\n生命周期由 Pi 管理"]
    A --> G["每个工作项独立 Git clone"]
    G <-->|普通 fetch / push| B["本次运行的 bare origin"]
    CLI -->|PR 合并 intent + Git ref CAS| B
    L --> R["result.json + delivery_commit"]
    R --> H
```

这组边界值得保留：对象是持久工作记忆，成员责任由 assignment 表达；一次原生会话休眠不取消 assignee。Git clone 保留工作项的文件与提交，Context reset 只替换模型上下文。Git/SQLite 无法共同提交，merge intent 与原子 ref 更新有具体必要性。宿主使用 `delivery_commit` 做后续验收；Braid 不根据应用功能或 benchmark 分数调度，也不管理 SVC 或 Pi 内部子代理。

对象 CLI 直接打开 SQLite，StoreActor 在长驻进程内串行处理控制状态；因此一致性的真正边界是 SQLite 事务，并非 StoreActor 的内存消息队列。每个 profile 的 worker 是一组会话的驱动器，不是仅有一个执行名额的成员。

## 已发生的空批次回环

来源数据库与原生输入支持下列完整路径。普通评论互相唤醒也确实存在，但不是数百会话的唯一原因。

```mermaid
sequenceDiagram
    participant E as 事件 E
    participant B as 已消费批次 B1
    participant T as 旧 turn
    participant Q as SQLite 调度
    participant W as GroupDriver
    participant P as 新 Pi 会话
    E->>B: wake_batch_events 唯一绑定 E
    B->>T: 派发并标记事件 consumed
    T-->>Q: 结果 unknown
    Q->>E: 同一个事件重新置 pending
    Q->>Q: schedule_event 建立 B2
    Q->>Q: 插入 E→B2 被 UNIQUE(event_id) 忽略
    Note over Q: B2.event_count=0，E 仍属于 B1
    Q->>Q: quiet_deadline 到期，空 B2 变 runnable
    Q->>W: 关闭工作项的 pending direct_contact 可重新激活
    W->>P: 新建会话，发送“请处理 Issue”而无事件引用
    P-->>W: completed，工作项已关闭、无需处理
    W->>Q: assignment / session sleeping
    Note over E,Q: 空批次没有 E，因此没有消费 E
    loop 同一 pending direct_contact
        W->>Q: 再次 reactivation / schedule_event
        Q->>Q: 再建空批次
        W->>P: 再建物理会话
    end
```

关键代码为 `store::mark_turn_terminal` 的 unknown 分支、`schedule_event`、`advance_scheduler`、`complete_work_item_reactivation` 和 `claim_runnable_turn`。当前 `delivery_complete` 只在所有对象终态后跳出 Local 运行，不能修复根 Issue 仍开放时的这条回路。

## 冷恢复的矛盾边界

```mermaid
sequenceDiagram
    participant H as 宿主
    participant L as 新 braid local
    participant DB as 持久 SQLite
    participant W as 新 GroupDriver
    participant M as 新 SessionManager
    H->>L: 原 request.json + 原 state
    L->>L: 取得此路径的 runtime.lock
    L->>W: 启动 worker
    W->>DB: 查到旧 starting/running turn
    W->>DB: mark_turn_terminal(unknown)
    DB->>DB: 建立 materializing reset
    W->>DB: ready_context_reset
    DB-->>W: 旧 provider session ID
    W->>M: remove(old_id)
    M-->>W: 没有旧句柄，也没有本进程 stopped 记录
    W-->>L: cannot prove native teardown
    L-->>H: blocked
```

已有 `materializing/reset_pending` 也走同一空句柄 `remove(old_id)`。若旧 provider 状态为 unknown，则可能先重启同一原生会话、再关闭新句柄；这同样没有证明来源旧进程已停止。启动时遇到 `interrupting` reset，`recover_context_resets` 直接置为 blocked。这里缺少的是可恢复的“旧执行已经停止”事实，新的文件锁只能证明这一路径没有另一 Braid 主进程持锁。

## Context reset 的 adapter 边界

```mermaid
sequenceDiagram
    participant O as 对象编辑
    participant W as GroupDriver
    participant DB as reset 记录
    participant P as 旧 provider 会话
    participant N as 新 provider 会话
    O->>DB: Invalidate
    W->>DB: interrupting + 变更引用
    W->>P: steer：当前会话结束后以新 Context 继续
    P-->>W: completed
    W->>P: message_was_processed(精确通知文本)
    alt Pi 原生 JSONL 有 user 后接 assistant
        P-->>W: true
        W->>P: teardown 旧 Pi 根进程
        W->>DB: materializing / reset_pending
        W->>N: 最新完整 Context
    else Codex 没有实现消息收据接口
        P-->>W: native message receipt is unavailable
        W->>P: 补发 context_reset_notice turn
        P-->>W: completed
        W->>DB: blocked
    end
```

“RPC 已接收”与“模型有机会处理”需要区分，这个要求本身成立。问题是共享 worker 依赖一项只有 Pi 实现的收据能力，导致 Codex 的正常终结也无法进入重建。
