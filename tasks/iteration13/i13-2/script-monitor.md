# I13-2 纯脚本运行监控

用户要求“让运行监控用脚本来实现，做到自动化，不继续使用模型，可以通过检查 provider sessions 的状态来判断是否 stale”。本项实现了官网和本地共用的 provider 活动判断，不改变生成、评分、费用、终态完成门槛或 Console。主线已暂停 heartbeat，旧两条采集脚本自然退出；本项未调用模型、恢复生成、执行官网提交或停止当前 HTTP。

`lab/arc_bench/hosted_monitor.py` 已移除 review 模型调用、提示词/schema 和自动取消实现。默认读取官网状态并下载模板导出取得 provider 证据，保留原 ZIP 和 HTTP 错误；旧 --review 只兼容为纯脚本观察，取消选项直接拒绝。当前状态仅选择 template/.factory26/<id>/braid-state/status.json，历史嵌套状态仍可保留原件，但不加入判断。

`lab/arc_bench/local_monitor.py` 接受显式 --matrix 与 --output，复用原有首轮立即、前十分钟3分钟、随后8分钟的采集及 terminal 回执。resource.state=sending 记 preparing；launching 时优先读取真实 cid 或核对登记 container_name，不能因运行中 container_id=null 宣称尚未启动。未绑定身份且 Docker 明确返回未创建时仍为 preparing；已绑定身份、daemon或 exec 的具体错误保持可见。容器存活但尚未生成当前顶层 Braid status/provider_sources 且没有读取错误时记 preparing；已有 status 或 DB 的读取错误仍作为缺证据保留。容器停止但 lab 仍回传时记 stopped_finalizing，停止对该容器 exec，继续等待 lab 终态。source/run 终态与 transport 回传错误分别保留，不将 finalization timeout 换成未知采集错误。

共用 `provider_liveness.py` 从 DB/WAL 的一致 SQLite 读取快照取得 provider_sessions 和 turns，每个 agent 只采用最新 session。SQLite 读取有15秒上限，原表不写入；官网导出文件集合本身是否原子仍未知。物理目录用于身份映射，native header、文件长度、完整行事件时间与原 mtime 用于活动依据；官网解包产生的本机 mtime 不作源活动时间。原生正文原件保留，判断不解释语义内容。恢复时间与新 run 开始时间划界导入历史，历史 running 不能直接被判为当前 stale。

默认至少两次采样、30分钟没有状态或可观测 native 活动变化才提示 suspected_stale，可用 --stale-after-seconds 与 --minimum-samples 调整。sleeping/idle 只有在没有 starting/running turn 时才作为正常闲置；unknown 或不一致的 idle 保留未知，当前活跃身份及可读活动证据长时间不变时才进入疑似提示。不可读 native 短期保留 activity_unknown；本轮身份已经成立且持续30分钟、至少两样本仍不可读时，报告 observation_missing 并保留具体 native.error，不据此证明静止。组级资源等待不会抹去已成立的 session 缺证据告警。未配结果的工具调用只说明存在在途记录，不证明工具仍执行，也不会被无限豁免；本轮没有新增进程管理或探针。token、一次静止和旧来源均不作为 stale 依据。

provider_health 的 key 是 kind:profile.id，保留为组级证据。组在资源等待且没有当前 session 时不会发 observation_missing；一个组的等待不会改写同组每条 session 的状态。session 资源等待只采用明确错误前缀，兼容实际的 session waiting for resources 与旧 session deferred input: resource pressure。失败、不可用、缺观察、资源等待及停止回传分别记录。所有结论都标 semantic_progress=unknown；通知按状态/故障签名去重，osascript 成功仅证明提交提醒，人是否看到未知。不自动取消、恢复、提交或收费重跑。

实际操作回执在 [operations-receipt.json](../../../runs/iteration13/i13-2-20261001/script-monitor/validation/operations-receipt.json)。直接消费旧本地两个真实终态记录，分类均 terminal，未 exec 退出容器；重复读取相同终态证据不重复通知。官网取消导出按顶层路径只选择一个当前 status，WAL 一致快照取得5条最新 provider，其中4份 native 可读，一份保持缺口，整体按真实 CANCELLED 终态收口。原暂停 Sheet 的独立副本取得3条最新 provider/native，分类为 idle、sleeping、active；保全原文件 SHA 前后相同。未构造样本或运行测试。三个 Python 源文件编译通过，疑似 stale 的长期运行告警尚未在本轮真实运行中触发。

本地 r2 采集已从仓库根实际启动，保留 stdout/stderr 和 PID。旧 collector 文件未被覆盖，成功门控的 follow-batch.py 保持原逻辑。实际入口为：

```sh
/Volumes/WorkSSD/Development/factory26/runs/iteration13/local-rebuild-20261001/host-lab/bin/python -m lab.arc_bench.local_monitor --matrix /Volumes/WorkSSD/Development/factory26/runs/iteration13/i13-2-20261001/revision2/active-matrix.json --output /Volumes/WorkSSD/Development/factory26/runs/iteration13/i13-2-20261001/revision2/observation
```

当前 r2 为 exp-20261001-223204-4b68eb，GitHub run glm-root--hackathon--github-a94a67b4b3d85b，Sheet run glm-root--hackathon--sheet-8046cfb0695023。监控目录保存 monitor/scheduler.json、每批 collection/provider-observation/liveness、alerts.jsonl 与 completion.json。源码及实际初始化读取回执身份由同目录 deployment-receipt.json 保存，生产后台身份归 revision2/background-launch.json。首批 Sheet 汇总曾为 historical_or_unknown，但直接原件显示当前 root 和 PR 3 已活动；原因是历史休眠会话在汇总排序中优先于当前会话。共享判断已将 historical_or_unknown 放在最后，失败、缺观察及疑似 stale 的优先级保持。对三个真实已保存观察重新计算后，GitHub 保持 active，本地 Sheet 和官网 Sheet 均由 historical_or_unknown 改为 active；原批次不改写，回执为 script-monitor/validation/current-priority-readback.json。

官网 r2 journal 已绑定 submission e69e9764310c / run f16834f58674，self_funded、关闭比赛额度。纯脚本入口已实际启动：

```sh
python3 -m lab.arc_bench.hosted_monitor /Volumes/WorkSSD/Development/factory26/runs/iteration13/i13-2-20261001/hosted-sheet-r2 --journal /Volumes/WorkSSD/Development/factory26/runs/iteration13/i13-2-20261001/hosted-sheet-r2
```

主实现已提交 48bb51b，官网排队/初始化分支为 dbcaa2b。汇总排序修正后，核对旧 PID 的启动时间和完整命令，依次停止旧监控并启动同一入口：本地 17338→48111，官网 27102→48187。scheduler 中的采样历史、去重状态和下次采集时间逐项保持，没有新增并行采集。准确回执为 script-monitor/monitor-restart-current-priority.json；当前 PID 与源码 SHA 分别归 revision2/background-launch.json 和 hosted-sheet-r2/monitor-launch.json。i13-wsl heartbeat 保持 PAUSED，监控聊天不再承担周期审查。Console 单实例部署另归 console-deployment.md。
