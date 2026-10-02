# 最终修复复审：运行时当前增量

本轮接续既定最终复审，只读源码、锁定依赖及定向原文。结论：L01父身份保留、L02有限作业等待和服务回执收敛、L03原文定位的修复层次基本正确；但历史子任务通知仍允许在Braid turn结束后独立启动Pi，留下与Sheet349相同的生命周期缺口。建议先消除此入口，再进入原已约定的真实生成观察。本报告不代用户授权实验，也不以代码阅读宣布行为验收。

## FR1：历史子任务通知把“Pi还活着”误当“存在合法Braid回合”

这是确定的源码机制缺陷，实际新运行是否触发尚未观察。影响两活动variant的 `extensions/factory-subagent-observer.ts:363–408`，对应R11/Z02/L01，并直接影响L02声称收口的边界。

具体机制是：`session_start`选择同工作区旧父的在途run并注册文件watcher；收到终态后，第377行无条件 `sendMessage(..., {triggerTurn:true})`。唯一资格检查是当前native session ID与注册时相同；直到 `session_shutdown` 才清除它。代码明确不把历史run登记为当前父pending work，也不保活。因而当前父可以正常settled，原生RPC进程仍存活，旧run随后完成并触发此分支。

锁定Pi 0.85.1的 `dist/core/agent-session.js:1099–1122` 规定非streaming时 `triggerTurn:true` 直接调用 `_runAgentPrompt`。Braid `src/provider/pi.rs:585–608` 以 `agent_settled` 产生TurnCompleted；`src/provider/session.rs:181–199` 清当前turn并置Idle；`src/objects.rs:203–204` 要求活动turn和运行中的provider才允许写。observer触发的新原生轮没有创建Braid turn的路径。后续评论/状态修改会使用失效writer，或先继续耗费模型和工具资源；不能把此问题修成放宽writer资格。

这不是“理论上进程可能还活着”的泛化担忧。Sheet原文 `run-audit/sheet/evidence/native/349-2026-09-28T10-08-21-694Z_01a0e77c-a8be-755d-8bfa-4c3797bc3c09.jsonl` L33–39给出有限PBB转后台、wait无登记工作、最终回复、迟到回执后继续执行；L54–55是第一次评论writer失败。L137和L144–159的数据库读取/直接改写链沿用 `../../cells/writer-followup.md` 已核对结果，本轮没有重新打开数据库。它证明旧运行中“settled后原生继续”确实发生过；并不证明observer这条分支已经在旧运行发生。

竞争解释与限制：若旧任务在当前父settled之前完成，通知可进入当前有效回合；若Pi先shutdown，watcher会关闭；若从未遇到恢复中的旧在途run，则不会触发。这些限制缩小发生条件，但不能消除源码中允许的正常时序。持久结果可见性不要求每次迟到都启动新轮，因此不能以“否则结果可能晚消费”为理由绕过Braid写身份。

更简单的根治是在被动handoff回执处沿用L02服务通知的原生能力：记录消息而不独立触发新轮，保留旧run索引、恢复时重读、下次合法输入消费。若确有“正在合法回合内及时交给模型”的义务，可在原生有效运行窗口内转送、窗口外只持久化；不应仅检查session存活，也不应默认给旧任务adopt/rebind或让Braid管理原生子任务。这里建议优先统一不独立续轮，避免新状态机。若产品后来要求闲置成员也立即处理旧结果，须通过合法调度输入建立新回合，属于另外的产品决策。

最小判别证据是在获授权真实运行自然出现旧在途run时，对齐旧run终态、当前Pi agent_settled、通知和下一个Braid turn；确认通知没有单独启动失效writer，并由合法后续输入读到结果。没有自然触发就保留未证，不为此新增测试或探针。

## L01：按父历史保存是必要身份边界，没有必要接管旧执行

原上游症状来自官网父重建后重复派同一rebase：旧executor仍活动，新父再次声明“唯一写入者”并派新run；详见 `tasks/factory-subagents/cells/iteration10-role-audit.md` 的11:24–11:34链。本轮复用该有界原生审计，不重新全读官网历史。重复委派也受模型未利用身份的影响，不能断言索引一旦存在就必然消除重复。

本轮完整读observer：103–143先按旧父归档，再加载当前父历史；同父初始化复用merge；235–280按cwd发现旧父，并在同一home活动/历史清单中按父选较新版本。startup父A→RPC new_session父B不再因home相同被误拒。Pi `agent-session-runtime.js:98–173` 确实以相同agentDir替换SessionManager，故该修复针对FF1真实接口假设，而非靠忽略错误兜底。当前两活动variant文件相同。

这里需要区分执行归属和成果可见性：新父能查旧run与产物，不能因此成为旧run owner。当前索引方案保留这一区分，旧父清单在覆盖活动清单之前写出；没有新增跨进程接管状态机。无需将清单按home强行合并，也不应通过“父ID不匹配直接清空”简化。读取/转送能力的核心仍成立，但FR1要求进一步收窄自动续轮；先前Z02“存活期通知可接受”的结论必须加上合法回合边界，不能原样升级为完成。

多无关进程并发写同一个native home不是本轮已证明的使用前提，不要求新增锁；真实startup/new、自然resume、首轮旧身份可见及结果消费仍未在本轮运行。

## L02：修复在原生终态边界，不能让Braid接管job或放松writer

Sheet349的观察支持“有限job未计入settled”这一直接原因，不能用CLI语法错误、全局只读或数据库锁解释：相同原生会话有可读数据，同期别的成员能写，最后直接篡改turn和provider状态才写成功。模型绕过SQLite守卫是已发生的不当行为；在既定无新增沙箱条件下，生命周期修复不宣称防住有文件权限的直接数据库写入。

当前 `harness/npm/patches/pi-background-bash-1.0.5.patch` 为有限job登记原生background-work provider；无UI的agent_end等待completion，再冲刷回执；service显式排除，并以 `triggerTurn:!item.job.service` 保存其退出消息。锁定Pi的agent_end扩展handler被await，随后原生队列继续，最后settled（`agent-session.js:473–474,780–810`）。这比“提示模型多等一会”或Braid管理PBB内部job更贴近根因。service没有有限完成义务，迟到退出本身不应获得Braid写身份；该收敛合理，不需后台服务永远阻止turn结束。

没有新增备用框架、任意timeout或循环保活的必要。`service:true`必须由调用者表达真实长生命周期，误将永不退出的server当有限job仍可能等待，这属于当前工具契约与采用需观察的边界，不据此加入猜测式超时。补丁依赖锁版本及Mac/Linux补丁接线已静态核查；本轮未重新应用补丁、构建制品或运行PBB。完成、取消、settled顺序以及无pi-subagents子会话路径仍须真实证据，保留前轮条件。FR1说明L02选中的机制正确，但同类入口尚未统一。

## L03及工具：定位与分页值得保留，不能冒充自动因果审查

`lab/__main__.py:116–157,399–408` 直接用run的native manifest按原生ID唯一匹配路径，再沿既有run内文件边界读取；输出字节next_offset及原始行号，UTF-8尾部补读至完整字符。没有第二份索引或新增遥测生产者。它解决的是手工找路径与页尾字符损坏，不能推断已完成工作项、PID、时间跨链关联或语义阅读。

从上一页next_offset连续读取可保持字符边界；任意指定落在字符内部的offset仍可能产生替换字符，现有说明只承诺连续分页，因此不是当前阻断。行号从文件头计数，巨量连续分页会重复扫描前缀；当前未有量化瓶颈，不建议预建索引。此处“更简单”就是保留现有manifest和字节接口，不因分析工作复杂便另造通用分析引擎。未执行CLI或重新复跑历史分页例子。

Z03的BodyArgs正文入口继续成立：帮助推荐文件/stdin，已有读取实现并未变更shell语义，不能把提示写成shell展开后可恢复原文。R29 Collector、旧生命周期与对象修复没有本轮源码增量，按覆盖表边界复用旧结论，不重算旧失分或宣称节省兑现。

## 决策与证据边界

应先修FR1，因为它是当前两活动variant正常恢复时序中的资格缺口，与本次确认的writer根因一致，修复可局限在现有通知出口。L01历史身份存储、L02有限工作终态及服务回执、L03定位分页没有发现另外必须先修的高影响机制问题；FR1消费后，它们可进入既定真实生成观察，不要求先增加设施测试。PBB取消/settled、旧结果真实消费、正式Node20兼容继续列为观察条件，不能写成已通过。

所读Pi根为 `/Users/lanzhijiang/.cache/factory26/runtime-faf60473273ddeed/node_modules/@earendil-works/pi-coding-agent/`（0.85.1）；读取其源码不代表新制品已包含当前patch。本轮没有源码修改、构建、测试、探针、模型调用、实验、评分或提交。只写本报告及runtime-coverage.md。
