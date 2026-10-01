# 事件与会话生命周期

本地 runtime 复用原 StoreActor、queue、GroupDriver 和 SessionManager。assignment/group 管理 materializing、idle、running、reset_pending、sleeping、retired、blocked；provider session 是可替换的物理执行绑定，每个工作项的 Git clone 和逻辑 group 保持身份。

工作项的指派记录责任关系；执行完成或休眠后仍保留当前成员和可联系地址。只有明确取消指派或改派才撤销旧责任并关闭旧执行。取消事件按工作项依次结算，旧 provider 会话确认停止后才消费；一个工作项待收尾不阻塞其它工作项的指派。

根 Issue 启动包含明确 activation 和首个 Wake；普通 assignment 不被解释为需求输入。`pr create` 用显式标题、正文和关联 Issue 直接建立本地 PR 并激活实施；可选 request-id 只为调用重试提供幂等，不从 comment 或正文推导。对象创建/修改/生命周期由 CLI 事务写入语义事件，普通 Wake 进入既有 quiet-window/count batch。

只有 Issue/PR 可见 description 的实际变化产生 Context 失效，自己编辑也保留；OPEN 关联 Issue 的 description 变化传给实际展开它的 PR。title、comment 维护和关系变化保存对象并向必要成员投递增量，排除实际操作者，不因全投影哈希不同而重建。失效事件按当前负责人及指派版本定址，旧指派的事件不阻塞新成员。具体契约见 [本地运行契约](local.md)。

Context 失效先保留待重建事件，并将变更引用告知原会话。运行中的 Pi 会话收到 steer 后继续当前工作；steer 应答只证明入队，旧会话的原生记录必须出现这条用户消息及其后的 assistant 活动。等待旧 turn 自然结束时，普通评论仍可经同一原生输入通道送达；一次 steer 只确认其实际发送的事件，批次中新追加的事件留待下一次输入。失效事件仍由 reset 消费，不作为普通评论发送。若重建通知错过当前执行的终点，或失效发生在空闲会话中，则在同一会话发送一次普通输入。旧会话自然结束、通知得到验证且原生进程确认退出后，才物化新会话。等待期间仍可按当前责任关系写回 Issue/PR；真正取消指派或运行封存仍会撤销写入权限。没有原生通知证据、执行结果不明或退出证明失败时阻断重建，不能启动第二个写者。新会话物化时按旧 session 最后一条实际工作 turn 的持久终态决定续接：自然完成只刷新 Context，中断或失败仍保留续接；独立新消息按原 batch 投递。Provider Unknown 保留上次执行结果未知的事实，按下述原生连续性恢复，不当作交付成功。

持久化 idle 只描述 Braid 已管理 turn 的状态；Pi 原生会话仍可能执行后台 follow-up。新普通输入与重置通知领取前均核对原生当前是否可接收，发送时若状态变化而返回 Deferred，则保留待投递义务。重置通知复用同一未开始 turn，记录原始延后原因、首次和最近延后时间及次数，不记为执行失败；旧会话仍须收到通知并完成原生证据验证后才能替换。

支持 managed execution 的 Pi 将原生静止与输入可接收分别报告。`get_state.data.managed_state` 包含 `status` 和当前 `execution_id`；只有身份一致的 `quiescent` 可以卸载 OPEN 的 idle 成员。服务、后台工作或未消费结果使原生仍为 busy，但服务驻留本身不禁止普通输入。卸载前在同一 Store 事务确认当前 assignment/member/version、无活动 turn、待输入或 reset，并清除旧 `cli_binding_id`；事务之后到达的新输入继续留队。停止证明通过后释放物理句柄，逻辑成员、provider session、clone 与 native history 保留，正常卸载不制造 Unknown。恢复检查仍保留有效句柄，只为真实排队输入、必要 Context 重建或未知执行接续恢复进程；无输入的普通 idle 成员不会被周期检查全部拉起。不新增持久 residency 字段，既有 binding fence 和运行内句柄集合承担这一区分。

启用运行资源控制时，所有 Pi start/resume、description reset 与重新激活均通过同一共享 launcher 准入。launcher 用运行目录的文件锁登记启动 UUID、进程 birth identity 和独立 PGID 后 exec 原 Pi，payload 在登记之前不能执行。资源拒绝必须有该启动 UUID 对应的 `resource_deferred` 原件，不能仅按退出码 75 推断。普通 turn 只检查当前压力，不再领取整个进程生命周期的启动 reservation。拒绝 start 保留原 assignment 代次、clone 和激活事件；拒绝 reset 保留 materializing reset；拒绝 sleeping activation 保留原责任与联系，各路径均可接续，不将资源不足写成永久的 assignment blocked。

各 group 复用既有两秒恢复循环；共享 factory 按 collector sample 串行执行至多一次原生 `relieve_pressure`，随后重读压力。原生运行时选择确切自有的有限作业并保存退出、部分输出与资源原因，Braid 不读取工具私有作业表。每个成员的一条连续 Unknown 链只自动恢复一次，成功 completed 或明确的新工作输入才解除限制；自动恢复通知、Braid 系统评论及自身 deferred/failed 重放不解除限制。资源准入拒绝使用独立的 `ResourceDeferred` 类型，不消耗 Unknown 恢复额度；driver 在 `provider_health` 中报告 `waiting_for_resources`，保留待执行义务并继续等待采样恢复，即使所有 group 暂时都在等待，也不封存整轮。`can_progress` 仍只报告真实活动，不把等待伪装为推进。资源等待不能掩盖同组或其它 group 的真实恢复失败、配置不兼容或恢复额度耗尽；这些错误在所有已观察 group 均不能推进时仍可返回 blocked。真正 owned execution 停止证明为 unknown 时仍沿既有 fatal 边界立即阻断整轮；本轮未建立任意未知 writer 的独立权限撤销或隔离。

close/merge 不中断当前执行，也不额外授予 finalization。自己关闭只保存对象状态；外部关闭作为普通输入投递给负责人。真实待处理输入继续执行，无输入的关闭成员自然休眠并保留责任关系；reopen 或定向评论可重新激活。旧归档的 finalizing 状态仍能沿既有恢复链收尾，新关闭不创建该状态。

关闭成员重新激活时，将同一成员、当前指派版本已排队的定向联系合入同一 wake batch，每条联系仍保留独立投递收据。原生端接受输入后才标 delivered；拒绝或 Deferred 保留待投递状态。成员仍活动时到达的联系继续排程，存在待处理批次时不先休眠；旧指派地址返回 unreachable。

重新激活同一成员时，恢复事务读取属于该真实 assignment 和指派版本的未应用 description 失效。没有描述失效且原生历史可恢复时，沿用 provider session；title、comment、关系、完整投影 hash、Profile 或指令摘要变化均不单独要求更换会话。resume 保留原会话实际收到的 context_revision，不渲染或记录尚未发送的新投影，也不被当前投影的硬上限阻止。存在 description 失效时，确认旧 writer 停止后以当前投影 start，只消费该次捕获的描述事件，混批的评论及联系仍按原规则投递；并发新增的描述失效留待下一次处理。

同一原生 adapter 的模型及指令可在实际 resume 时更新：Pi 的新进程使用 model、thinking 和 append-system-prompt，Codex 的 thread/resume 使用 model 和 developerInstructions，下一 turn 使用当前 effort。活动进程不会仅因配置摘要变化重建或即时采用全部新配置。旧 native home 的模板材料继续保留；native_template 只在真正创建新 home 时复制，不覆盖既有材料、会话文件或 Pi 内部 Agent 的记录。repository、adapter、当前责任身份和工作树约束仍须成立，不兼容时保留具体原因并阻断。

unknown 不证明原生历史丢失。活动 handle 丢失或终态未收到时，保留旧 turn 的 unknown 和原始错误，先通过已管理 provider 的 teardown，或宿主确认停止并取得 runtime lock 的 offline-resume，证明旧 writer 已停，再 resume 同一原生身份。resume 成功后将 session 恢复为 idle，并排入一次明确的恢复事实：上次终态未收到，依据原生历史、当前工作区和对象核对后接续。恢复通知按旧 turn 去重，不盲重放旧输入、不追认旧执行成功；确认停止失败时不能创建另一写者。真正 description reset 的在途恢复仍沿其独立证据约束。

Pi 的停止流程先调用原生 `stop_owned_execution` 关闭执行准入并停止自有子作业，再关闭 stdin、等待父进程，最后通过同一执行目录的离线 cleanup 核实父进程及脱离父子树的 owned execution 已全部停止。父 wait 的退出码、signal 或具体错误单独保留；非零退出不自动证明 teardown 失败，成功 wait 也不替代 owned execution 停止证明。只有离线收据为 `stopped` 才释放新代次；`unknown`、超时、权限错误或身份冲突保持原 ownership 并阻断第二 writer。新 Pi 使用独立 PGID，停止旧执行不信任或杀死历史共享 PGID。初始化或 resume 中途失败也须完成同一停止闭环，未确认停止的所有权保留在 factory，并经 stop-proof 错误交给 local。

Pi 路径可完整查找且确切原生文件已经缺失时，adapter 返回 HistoryUnavailable，才允许按当前投影 start；具体缺失原因保留在旧 session 的 last_resume_error。仅在当前配置根找不到 Codex home 不能证明原生历史已丢失，故保留该具体错误并阻断。resume 的启动错误、超时、断连或暂时不可用保留身份及原始错误，将本次休眠联系退回待投递；不会永久缓存暂时不可用。失败恢复中已启动的原生进程须确认退出后才能重试，退出失败保留其 ownership。worker 沿既有恢复检查重试，无活动时 local 可返回 blocked，保留现场供同请求恢复。

`--offline-resume` 已由宿主证明旧执行停止后，可重新物化一次此前因 Pi 新会话启动不可用而封锁的 Context reset。恢复只接受仍为 OPEN 的同一活动 assignment、相同成员/Profile/指派版本、无后续 reset 或 provider session，且物理尝试记录明确为 `failed`、没有原生会话身份的情形；已终结、改派、身份不明或后来成功接续的工作项保持原状态。恢复沿用原 reset 和失效事件，交给既有 Context 物化与续接链；若再次失败仍会封锁，不在运行中循环重试。

根及全部工作项终态且没有未解决合并时，不再派发普通讨论的新执行；已接受的执行和重建续接自然结束后，local 返回 quiescent；根仍开放时继续等待或检查，必要恢复受阻时返回 blocked。退出时读取当前 delivery ref 的提交，供调用方决定如何使用；Braid 不把工作项状态或单个 provider terminal 当成应用验收结论。Git 合并的 prepared/applied/conflict 与恢复边界见 [本地运行契约](local.md)。

Bub 沿同一物理会话与 Context 恢复契约接入；其私有 steering 不能保证同轮终态关联，因此明确 Deferred，由 queue 在下个空闲边界投递。取消核实 owned process 已停止，缺少原生 terminal 时记录 Unknown。恢复前先核对持久化 ID/cwd，首次 prompt 前仍保留待物化 Context；具体原生限制见 [Bub adapter](app-server.md#bub-原生-acp-adapter)。不把 ACP load 对未知 ID 的成功响应当作历史存在证据。
