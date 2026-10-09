> **当前：两组 baseline 均已按用户要求暂停，不自动恢复。** 用户原话：“立即暂停目前现有所有实验，API额度即将耗尽”。冻结 Lab 公开 pause 回执已确认两个原容器 Paused=true；两个准确出生身份的 controller 以 SIGSTOP 保持 T 状态，后续生成和评价自动派发冻结。现场、原始产物和模型成功原件保留。详见本文末尾暂停回执，历史“正在生成”说明仅为暂停前状态。

# I14 baseline GitHub 两组根模型实验

用户直接开工原话：“所以请你直接使用I14-baseline运行GitHub题，有两个variant：glm-5.3-flash和glm-5.3（因为之前I13的glm-5.3 variant没有结果）”。

用户最新决定由主线转达：停止 I13 热恢复，直接从干净起点运行 I14 baseline GitHub 两组，根模型分别为 GLM-5.3-Flash 和 GLM-5.3。两组使用普通 Qwen，Kimi K3 使用普通 Qwen，内部 DeepSeek v4 Flash 使用 Token Plan 的 deepseek-v4-flash-0731。Sheet 不运行。此授权覆盖必要窄修复、冻结、lab.exp 编译与启动、实际模型反馈，以及每题完成后立即独立 self_funded 官网应用重放，allow_competition_credit=false。

执行负责人为当前 hosted_stop owner，主线持有整体范围及旧运行在途协调。旧 baseline 暂停现场不修改，c5a3674c42c4 已取消，I13 r5 不再启动。两组不用旧 source/prepared/stop 恢复合同。

两组均为 2 GiB 内存、2 CPU、development-2 同一五槽 admission 域；每个 run 的高价模型合计只允许一个 Braid session。冻结源码为 variants/pi-braid-i14，当前脚本的 Braid owner 预算保护随包提供，原生子会话不新增 Braid 名额。GLM 根组使用 root-only profile，K3 是 Pi 内部 advisor，按现行合同不另计 Braid session；GLM 根组的唯一高价 Braid 名额归根 owner。

允许需求使用 I13 已确认的完整新版包 revised-requirements，requirements.yaml SHA256=9480921cb3b7ffdc5f32cb76011ecc1d5bf9bfbf2cba38e3a092355ac88a54f8；两组完全相同。旧 I14 冻结需求不进入本轮。生成独立于外部评测，隐藏评测反馈不传回生成 Agent。

当前两组均已从干净起点取得真实模型成功响应，正在生成。GLM-5.3 的 Braid run 是 `20261002-110120-f5e81834`，来源为 `experiment-live/attempt-d43144ff7dcff8ea8659d863`；Flash 的 Braid run 是 `20261002-110738-65a19bd7`，来源为 `experiment-flash/attempt-e0ef27e350f030621a65eb03`。最终包 `pi-braid-i14-final.zip` 的 SHA256 为 `f725e9345fdd19274cdf08a0038a9eb993d375043f0d5282eb445385751dce00`，包含当前预算保护和资源采样路径接线；Braid 为 Linux OOM 修复 binary `e209d754d89fe1d972ab0acbda020356e56121501b0756183d88857be7e03d22`，冻结 runner 仅对 local 设置地址空间上限，Docker 维持 2GiB cgroup。证据根为 `runs/iteration14/baseline-roots-20261002`，当前事实以 `actual-startup-success.json` 和 `active-bindings.json` 为入口。

下一步由既有 runner/controller 保存真实终态，在每组完成并发布冻结应用后独立官网自费重放；尚未取得生成终态或分数。唯一十分钟 heartbeat 使用 `active-bindings.json` 两个 target 的 `monitor_binding`：其中直接给出 frozen launcher、source、cwd、argv、只读环境和精确 attempt_scope。监控仅消费这些真实两组，不为历史无实例失败再开采集循环。GLM 如被原未启动 Flash 依赖阻断重放，只从实际冻结应用补独立 evaluate，绝不再次 generate。当前 owner 继续持有必要修复、终态及重放闭环；以下记录保留已废弃尝试和原始失败史。

编排冻结 intent.json 为两 generate 加两 evaluate，共四个 attempt 上限、max_parallel=2。官网评测使用 Flash 表单，自费且不占比赛额度；同一 competition 的评测由既有 controller 串行派发。当前 private driver 也在非零退出时保存 generation-state，原始错误保持 runner 日志。

实际 start 已接受，controller PID19016 / birth1790937397.751278，实验为 runs/iteration14/baseline-roots-20261002/experiment。同包 SHA256=643c04930a07940b8d45bd6aa48dbca04a7d86d9682351afa9cca090005097ca；编译、build 和 start 原件均在证据根。首个真实 attempt=attempt-4fa4c581aa385bc06c10e091，Docker container=3421dc058515527721726dc28f9cb322548e5668ec0d25a9c394f066d4fd56ab，创建于2026-10-02T10:36:49Z，目前在共享 runner 输运阶段；accepted 不等于模型成功。

首轮 Flash 实际已启动，但预算复核发现 Pi child 被 guard 整体跳过，会让不同 Braid 成员分别使用高价模型。源码已移除 child return，孩子继承 BRAID_STATE/CLI_BINDING_ID 按父 agent_id 认领同一名额，不另计 Pi child。公开 control stop 已取得 applied 和精确 exited 读回，Flash 原运行20261002-103747-ce163a6c及原始日志保留；不得把其计为成功 baseline。GLM 首轮在 authority reserve 的前置只读 inspect 超时，未出现匹配容器或 reservation，原 launch_pending/error 保持不变，证据 glm-unlaunched-physical-evidence.json。

下一次干净启动使用 budget-fixed 包和独立 experiment，不覆写原冻结实验。admission.physical 仅对前置只读 inspect 的 timeout 增加一次有界重试（30 秒后重试60 秒），不重试 reserve/launch 或任何写操作。主线 runner owner 正接线缺失的 resource-latest 生产，收到真实交付后冻结同版本 runner。

第二次冻结在主线 virtual-address 修复到达前已派发；其首组同样在前置只读 inspect 超时，第二组在本机存储预留拒绝。旧 controller 已 blocked/lost，原件保留，并独立确认两个来源没有对应容器/reservation/create intent；没有把 launch_pending 改成虚构终态。最终有效候选定义为 intent-live.json、compiled-live、experiment-live，冻结 runner 已限定 RLIMIT_AS 只用于 local，Docker 仍使用 2GiB cgroup。

本机 SSD 曾仅剩6.5GiB。按既有接口将 generation storage_reserve_bytes 显式冻结为1GiB，与 execution.storage.host_reserve_bytes一致；远端 storage_bytes=12GiB 保持。仅整理本任务已消费的 runtime/package-stage scratch，它们的完整字节仍在 final ZIP；对10份同字节同权限不可变包建立 hardlink，原路径、manifest与哈希不变。实际余量回升到12122554368字节，证据 scratch-retirement.json。

卡住 admission inspect 的明确对象是主线 reviewer prepare attempt-e77cba903ba6029d7969d2eb 的 terminal export 窗口，由原稳定owner处理，本任务不操作其资源、不跳过未知或释放lease。最终两组模型成功仍待确认，不能把 compile/build/accepted 当作已达结果。

最终 runtime 已取得首组供应商成功：GLM来源 experiment-live / attempt-d43144ff7dcff8ea8659d863 / Docker9faab12abf7b2abc8e8880474475803911741c0927815fe6be7db746f727128e，Braid run20261002-110120-f5e81834。第一条真实glm-5.3 assistant时间2026-10-02T11:01:36.627Z，input12598/output79/total12677，没有error。原件 glm-live-readback.json 同时确认memory.max=2147483648、oom/oom_kill=0、Pi地址空间unlimited、采样policy绑定/attempt/process-evidence/resource-latest.json，以及高价budget owner为根agent01a0fc46-9ecc-7ea3-b890-9a7d2d14728a。

保留已运行GLM，不能整体重启。experiment-live先前Flash在pre-reserve超时未产生实例，补组只含Flash generate及独立evaluate，定义为 intent-flash/compiled-flash/experiment-flash，budget2/max_parallel1，同冻结ZIP与新版需求。原GLM controller如果被旧Flash未成功输出依赖阻断，则仅从实际冻结应用追加独立公开evaluate，不再生成GLM。正常运行和终态由既有controller/runner采集，主线将此GLM binding及新Flash binding纳入唯一heartbeat；不将无模型的失败尝试纳入有效矩阵。

两组实际模型成功已确认，完整入口为 actual-startup-success.json 与 active-bindings.json。Flash补组 experiment-flash / attempt-e0ef27e350f030621a65eb03 / Docker d9962d24bf401d262d63e43984f5eb993e573b80e712be82166b15e97162ae2c，Braid run20261002-110738-65a19bd7，首条真实ZHIPU/GLM-5.3-Flash成功时间2026-10-02T11:08:03.007Z，totalTokens=12733，没有provider error。GLM组同期也已取得kimi-k3内部advisor成功响应，预算owner仍为原根Braid agent。两组memory.max均2147483648，当前oom/oom_kill均0，采样年龄约1.2–1.4秒；GLM第二次sample_started明显前进，实际持续采样成立。

当前两组仍在生成；不宣称生成完成或已取得官网分数。既有runner保留真实退出、采样与终态archive，现有controller的per-application job按各生成输出发布后启动self_funded重放。Flash具有独立generate/evaluate controller；GLM来源controller仍running且evaluate定义保持，首个无实例Flash错误原件留在旧实验，监控有效binding不包括它。如果后续依赖阻断GLM重放，owner仅从已冻结GLM应用补公开evaluate，不再generate。主线已获准将这两个准确binding交唯一十分钟监控consumer，正常状态变化不重复通知。


## 2026-10-02：子代理 modelScope 原地修复

Console 阅读真实 Flash Issue 后定向核对根 Pi 原生 toolResult，确认视觉两次和 advisor 两次委派均被本地 scope 拒绝。具体 resolved models 是 `factory26-visual-route-9637aca15b5b/ZHIPU/GLM-5.3-Flash`、`factory26-route-4e83d0961055/kimi-k3` 等；原 allow 只有 `factory26/*` 与 `factory26-visual/*`。`native_model_route` 为冻结的逐模型传输生成别名，model 和角色 frontmatter 已同步，而 settings 的 scope 未同步，因此错误发生于供应商调用前，不是额度或模型拒绝。

已在 `scripts/agent_support.py` 增加同一映射的 `bind_native_model_scope`，I14 native_files 在写出路由 models 后同步写 settings。仅把原 allow 已允许、且本次冻结 bindings 明确存在的模型映射成准确 `alias/model_id` 条目；原限制仍开启，不增加 `factory26-route-*` 通配，Braid session 预算保护保持。Python 编译通过，不运行设施测试。

现有 pi-subagents `discoverAgents` 每次委派读取 user/project settings，故直接更新两实际 run 的 native-template 与已创建 native-homes settings，无需重启生成或会话。GLM 10 文件、Flash 6 文件于下列真实回执时点应用，原字节保留在各自 run 的 `recovery/model-scope-20261002/originals/`；每文件原 SHA、新 SHA、具体 allow 和准确应用时间归 `runs/iteration14/baseline-roots-20261002/model-scope-hotfix/{glm-apply,flash-apply}.json`，总入口 `application-index.json`。原始拒绝 toolResult 归 Console 证据目录的 `flash-model-scope-errors.json`。

应用后通过公开 Console runtime 只读核对，两原容器保持原 StartedAt、running、未暂停，Braid run/attempt 身份保持。回执 `model-scope-hotfix/runtime-after-application.json`。自然下一次授权的子代理委派成功仍待验；不人为创建探针或追加模型调用，由既有唯一监控消费实际事件。旧冻结 ZIP 不改字节，本次运行材料改动有原件与 receipt。


## 2026-10-02：Flash PR2 的新 provider 0 Turn

用户观察的 provider `01a0fc6f-8244-7991-a2f4-cc8cd7140fdb` 属于 PR2 成员 `01a0fc57-8cf1-71a0-bf72-3ca3db17fbcd`。旧 provider 的 Braid Turn 已在 11:46:01Z 正常 completed；随后待执行的 context reset 在 11:46:04Z applied，continuation 实际为 0，准备了新的 idle provider。新 provider 没有 Braid Turn、resume_count 0，原生 JSONL 尚未首次持久化；Pi 活进程及 fresh quiescent/input_readiness 状态证明它等待新输入、没有模型请求。PR2 wake/event 均 consumed，没有待投递批次；advisor 按现 reset 合同裁定不恢复调度、不发 wake。零 Turn 是新 provider 的计数，不代表此前 PR2 没有工作，旧 Turn 完成也不代表应用验收完成。

Console 已把这个严格限定的首次未持久化状态改为 HTTP200/not-persisted，明确保留文件尚不存在事实；已有轮次、读过正文或其它错误仍报具体原因。当前 provider 实际读回等待状态，旧 provider 实际 50 条正文可读，主 Agent 独立 IAB 验收通过。新 8765 服务根 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261002-current-runs-reading`，service `5c80fa07-731a-4539-811b-1d8ca0f149d6`，PID99106；旧服务身份/history 保全，未修改生成或 Braid 调度。因果、原错、部署及原始证据归 `tasks/braid-console-control/current-runs.md` 和 `runs/braid-console-control/20261002-current-runs/flash-zero-turns/`。

modelScope 修复仍待自然委派成功；此新 provider 没收到首轮输入，不能拿它当作该修复的成功调用证据。沿当时的唯一监控入口继续消费；该说明现已删除，不人为造调用。


## 2026-10-02 20:48 CST：立即暂停全部现有实验

用户明确要求“立即暂停目前现有所有实验，API额度即将耗尽”，撤销继续生成/评测/热恢复的执行安排；不自动恢复。先按准确 host、boot_id、PID、process_start 和命令核对两个实验 controller，再 SIGSTOP 原 controller（GLM PID33164，Flash PID90428，均 T），阻止后续收费阶段派发。通过每个实验冻结 launcher/source 的公开 `lab.exp control EXPERIMENT ATTEMPT pause` 执行实际暂停，固定 request IDs 为 `user-pause-20261002-glm`、`user-pause-20261002-flash`。没有以 stop、取消或 Console 控制代替 pause。

GLM attempt `attempt-d43144ff7dcff8ea8659d863` / 容器 `9faab12abf7b2abc8e8880474475803911741c0927815fe6be7db746f727128e` 与 Flash attempt `attempt-e0ef27e350f030621a65eb03` / 容器 `d9962d24bf401d262d63e43984f5eb993e573b80e712be82166b15e97162ae2c` 的冻结控制均 exit0/status applied，独立物理读回 Status=paused、Paused=true，StartedAt及owner labels保持，OOMKilled=false。效果时点分别1790945290.647706、1790945290.168428。controller暂停后再次核对出生身份和 T 状态，当前两experiment没有已创建的 evaluate attempt；GLM原设施失败Flash attempt保留，不重试。

原始回执统一保存 `runs/iteration14/baseline-roots-20261002/user-pause-20261002/`：controller原身份/命令/暂停时点、公开control argv、stdout effect/stderr/tool returncode、各variant pause-confirmed及attempt清单；总入口 `pause-confirmed-index.json`。`active-bindings.json` 当前明确 paused-by-user/auto_resume=false，暂停前原件另存。原 execution/observation 的历史 running 字段不伪改，不作为暂停后的实际状态；当前以真实 pause effect 为准。没有删除、改写应用工作树、原会话或冻结ZIP。其它主线实验及共享heartbeat由协调方统一暂停；不操作Redis/无关资源。已取消I13 hosted c5及未派发r5不会重新创建，模型scope自然调用验收与e2e接入均不触发生成。


协调方另已读回 development-1 / development-2 全局 active Factory inventory，两机存活 Factory 容器均 Paused；共享十分钟 heartbeat 已工具更新 PAUSED。当前用户“全实验暂停”覆盖原生成、收费模型调用、评分和热恢复授权；只有用户新的明确指令可以 resume，不能因旧 completed、进程退出、额度重置或历史 automatic evaluation 配方自动恢复。协调方已收齐主线暂停回执：11 个 controller 确认不存活，没有新增 e2e 恢复、prepare 或评价 attempt，也无在途操作；cleaner Paused，e2e/reviewer Exited，现场保留。全局暂停范围已完整覆盖，本 owner 不操作其它 owner 资源。
