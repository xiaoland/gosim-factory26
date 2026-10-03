# 显式实验执行与设施职责复核

用户在 2026-10-03 指出：attempt、run 应由使用者主动调度，不应由 controller 监听定义文件自动派发。本轮只读复核这一职责及相似功能；未批准或实施新一轮源码修改。主工作区当前有并行未提交修改，源码身份保存在 scheduling-review-readback.json。以下行号对应此次主工作区读取，不代表历史冻结执行器或实际现场已经改变。

## 已观察行为

| 行为 | 证据 | 判断 |
| --- | --- | --- |
| start 启动独立常驻 controller；它每两秒扫描所有 attempts/jobs | lab/exp/controller.py:603–761 | 定义被用作待执行队列，controller 承担实验调度策略。不是监听源 recipe 的修改，消费的是冻结 experiment manifest。 |
| 未分配 job 自动创建 attempt 并派发 | controller.py:701–747 | 创建新的执行不能只因定义存在、预算未耗尽而发生。预算是上限，不是启动请求。 |
| 生成产物可用后自动启动 evaluate，并使用上游 job 的最新 attempt | controller.py:709–733；compiler.py:231–247 | 依赖关系、结果选择和执行决策混合。应显式选定 source attempt/output 或 artifact member，不能用 latest 推导评测对象。 |
| retry 命令写文件，由 controller 以后消费 | controller.py:673–695、1032–1054 | 不是自动失败重跑，但显式动作被变成延迟队列。使用者难以分辨请求保存与执行受理；容量释放后才发生的执行缺少明确时间边界。 |
| controller 对已保存的未受理或部分 Hosted 派发状态再次 dispatch | controller.py:660–667；hosted.py:381–452 | 这是同请求延续，不一定是新 attempt 或重复模型入口。但恢复 controller 同时恢复执行权，行为边界不清晰；应由显式同请求接续决定。 |
| controller 自动导出 Hosted 终态，并把 archive pending 算进重试容量 | controller.py:655–659、681–684、751–755 | 运行监督、远端证据运输和下一次执行被耦合。这里是 controller 的逻辑并行额度，不据此断言物理预约仍占用。执行额度应随真实执行关闭释放；材料保留与导出进度独立记录。普通 job 的 active 计算没有计入 archive pending（697），与 retry 路径不一致。Hosted export 本身是部分平台 JSON 归档；整份 workspace 下载发生在此前 live observe 的另一条路径。 |
| control 先 live observe，Hosted 观察可能下载整份 workspace ZIP | controller.py:947；hosted.py:469–472 | 控制需要当前身份与物理状态，但不应先等待诊断材料采集。 |
| wait 等 controller phase，不是选定 attempt 或平台 run | lab/exp/__main__.py:153–159 | 用户关心的执行对象和等待对象错位。controller 退出不等于执行结束，导出未完也不等于模型仍运行。 |
| projection 对未执行 job 只建议等待 controller 或启动整个 controller | controller.py:808–837 | 查询界面暴露并强化了隐式调度模型，缺少单 job 的显式执行入口。 |

上一轮 feat/experiment-startup-dx 的 controller.py:735–866 同样保留常驻循环、隐式 job 派发、retry mailbox 和依赖调度。这一轮不能只批评旧实现；上一轮设计与实现也遗漏了执行决策权的边界。

## 推荐职责

实验定义描述可执行工作及其冻结材料，不表达待执行队列。compiler 可以输出可选阶段和输入契约，但编译结果存在不意味着任一阶段会运行。status/monitor 展示定义、显式请求、已发生执行和保存证据；它们无权创建、启动、恢复或重试执行。

controller 改为显式命令的处理层。每个请求选定一个 job、实际输入、部署及必要来源，至多创建一个 attempt。容量不足、缺输入或来源不确定时返回具体阻塞，不登记未来自动启动的队列。执行已受理则返回 attempt 及 backend/run 身份；后台 runner 继续该次执行。一个 request ID 重入只能解释或接续原请求，不能创建另一个 attempt。结果未知时先核对原作用，不通过更换 request ID 绕过它。

retry 是使用者明确创建下一次 attempt 的动作，与重入原请求、修复 ready 服务、热恢复同一 state 区分。它应返回直接受理或阻塞结果，而非只写入等待 controller 消费的文件。下游 evaluate 必须绑定确切的冻结应用；设施可以校验它满足输入契约，但不能自动决定选择哪轮产物。没有输入的阶段仅显示尚未满足条件。

runner 只持有单次已受理运行的执行权：装配、必要服务就绪、一次入口、进程与资源监督、限额终止、子进程关闭、输出封口及终态回执。准备成功后进入该入口是一次 start 请求的履行，不要求使用者手动驱动每个内部步骤。就绪失败后的修复仍必须来自明确操作，不把服务失败升级成自动重新运行模型。

跨实验的共享容量、独占 writer、不可重复提交和运行限额保留为准入约束；它们阻止冲突，不决定哪项实验接下来执行。max_parallel、max_attempts 若保留，应只约束当前显式请求，不再推导新的工作。只因另一个 job 为 unknown 而阻断不相关执行的全局门控，应改为具体共享资源或来源冲突的门控；无法定位冲突时保留未知事实，而不是给整个实验授予调度权限。

控制先取得动作必需的最新身份和状态，与完整诊断采集分开；Hosted 当前 control 调用 live observe 会经过 workspace 下载，不能让 stop 先等待它。

结果保存分为运行闭环所需的终态回执/声明输出封口，以及可独立请求的运输/完整归档。不要为了结束一次运行默认搬运完整 workspace；不要把证据复制完成作为释放执行槽的条件。若已冻结的执行合同明确声明必须交付特定输出，runner 应完成这些输出或记录交付失败，但不因此让入口终态消失。上一轮已经删除默认完整回收的部分代码，仍需核对功能合同，而不是另建一套归档器。

## 轮询的区别

首先删除决定新执行的常驻循环。把两秒改成事件触发，仍然是同一个错误职责。

仍在运行的单 attempt 可以需要资源采样、期限检查和远端观测；没有事件接口的 provider 也需要有界轮询。能使用本地 process wait 或平台事件的地方优先消费它们。监控可以持续更新已有对象的事实，但不能将状态变化解释成启动新对象的许可。runner 对显式控制请求的消费不同于扫描未运行 job；是否替换其文件 mailbox 应以实际请求延迟和成本判断，不为统一形态另建消息系统。

Hosted observe 当前的 _reconcile 只查询并确认原平台写入结果（hosted.py:225–260、528–561），未发现它独立 POST 新 run 的证据。ready repair 也只有明确 control 请求才执行（runner.py:774–803）。这两项不应误报为自动重试。

## 拟议验收边界

新定义 build 完成、status/monitor 查询以及剩余预算或容量变化均不创建 attempt；controller 不再有后台扫描 job/retry 的进程。显式请求未指明 job 时不隐式运行整个实验。每个执行请求有直接的受理或阻塞回执；相同请求不创建第二个 attempt。生成结束不自动启动评测，评测对象以不可变身份指定。等待绑定选定 attempt/run，执行、输出、导出分别显示。

真实执行仍在 start 命令退出后持续被 runner 监督，并能记录终态。执行真正关闭后不因完整归档未完成继续占用执行额度；writer、材料保留及运输各自遵守具体生命周期。验收使用编译、实际操作及已授权实验，不新增 Factory/Braid 测试、模拟或包 smoke。

这是设计建议，尚未实施。旧运行保持原冻结合同；不能修改历史 executor、抹掉已有 request 或清理其资源来模拟新语义。后续实施需要围绕显式调度合同集中替换 CLI、controller、compiler 输入绑定与 projection，不新增 scheduler mode/auto_start 开关来长期并存两套职责。本轮不提前搭建 batch orchestrator；将来只有明确的批处理需求才在实验设施之外讨论其策略与授权。

## Advisor 采用结论

稳定 owner storage_judgment 对主区当前源码完成独立只读复核，同意移除隐式 DAG 调度而非调整轮询间隔，补充了 control→live observe→完整 workspace 下载的职责混合，并纠正 archive pending 只在 retry 并行统计中被计入的差异。主 Agent 定点核对 control:947 与 hosted:471 后采用该结论。Advisor 没有替代实际运行验收；本轮仍只有源码证据。
