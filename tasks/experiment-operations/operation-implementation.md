# 实验操作入口实施与证据

2026-10-02，`lab/arc_bench/operations.py` 收敛为冻结范围的消费入口。prepare 保存 manifest 的 `experiment_id`、完整 job IDs、controller-source 实物身份与绑定文件 SHA。启动、重放、monitor targets 及完成判定共同使用 `selected_runs`，只读取这一 experiment、这些 job 与冻结 attempt 的 run；共享 runs_root 中的其它实验及随后出现的外部 retry 不参与本操作。现有 run IDs 保存为 inputs.run_ids；尚未分配的 job 只授权 attempt=1 且没有 retry_of 的首次 attempt。已有多个 attempt 时要求规格显式给出 run_ids，不能默认将所有 attempt 重放。run_ids 必须为每个已有分配的 job 至少选择一个现有 attempt。

本地恢复使用规格中的 `preparation_jobs` 对象，明确声明 job ID 到 preparation ID 的绑定。不再通过名称相同隐式替换；未使用、未知的 preparation/job 在实际离线准备前拒绝。原 recipe 先以原文件目录 normalize 输入路径，再写操作副本；已有 experiment 只能核对冻结 agent ZIP SHA 与 preparation，不能重写 inputs。未完成 prepare 重入时，已保存 recipe 与重新解析内容不同会停止并保留现场。

controller-source 按 manifest 的树身份核对实际文件。历史控制器会生成 `__pycache__`，这类解释器缓存排除于源码树身份之外；新增非缓存文件、源文件修改及缺失仍会阻止执行。operation 自身另冻结 ARC 调用源码，不用这份副本冒充实际启动的 experiment controller-source。

本地已有终态 controller、但部分 job 尚未分配时，使用 `lab.run.start` 的现行“只分配无历史 attempt 的 job”语义接续；失败 attempt 不自动重试。新 controller 尚未登记最多等待 30 秒，随后保留 launch 身份并报告未确认，不反复派出控制器。已有 running controller 身份未知/消失时要求 reconcile。

恢复启动门控消费共享 `recovery.verify_launch(package, preparation_receipt)`。只有尚未分配的本地 job、尚未实际启动全部目标任务的官网 journal 才进入启动门控；已启动执行的纯观察不重新判断来源是否可以启动。实际 ZIP 来自 experiment 冻结 input 或 journal 的 agent.zip，prepare receipt 按同一 SHA 定位；operations 不解释 caller-confirmed 等停止声明。

每个 worker 对同一 collector 最多做一次故障接续。worker 内 collector failed/interrupted 或消失时保存故障并退出；显式新的 `operation run` 才能重新接续同一 scheduler。正常 completed 后确有新增 run target 可以再启动 collector。过程身份未知始终拒绝接管。官网前若干 journal 启动成功而后续 launch 失败，仍持久保存全部 journal，并将已取得 run 的 targets 交给 collector，然后保留原启动错误及独立 handoff 错误。

operation 的完成消费公共 monitor/accepted.json：本次范围每项完整 accepted identity 相同、first_batch 非空且 run 在 done 中即可。共享 collector 仍可继续观察其它运行，不要求它整体 completed。accepted.json 同时提供 collector 身份、collector_status、started_at、finished_at、error；operations 不读取或猜测内部 scheduler 文件名。只有 accepted ID 不足以让 worker 完成。identity 包括本地 matrix/run record/created_at，官网 journal/submission/run/competition/task。

## 实际反馈

`python3 -m py_compile lab/arc_bench/operations.py` 成功。没有编写或运行 Factory 测试、fixture、smoke、自检或新收费实验。

对已有真实终态 `runs/docker-workspace-20261001/final-experiment` 执行正式 operation prepare 和 work，操作原件位于 `runs/experiment-operations/terminal-operation-20261002/operation`。源 experiment 是 `exp-20261001-183720-e96fcc`，job 是 `minimal`，唯一消费 run 是 `minimal-f9c6da7ecf0ce1`。源 active.phase 已 finished，source run.phase 已 finished；本次没有派出生成 controller、调用模型、上传官网或触碰 I13。

独立读取该操作 `observation/monitor/completion.json` 和 first_batch 的 `outcome.json`：collector completed，accepted.identity 指向原 run.json、对应 matrix 和原 created_at；first_batch 含真实终态及生成 exit_code=0，done 含原 run，model_invoked=false。worker 最终 completed。launch-gates.results 为空，表明本次只消费既有终态。历史 controller-source 的实物差异仅为 __pycache__，原源码未改。

另直接读取旧 `runs/docker-workspace-20261001/experiment` 的真实 manifest/run：作用域选择为 `exp-20261001-182207-6b8178` 的 `minimal-0b595183087b34`；与 final-experiment 分离。

本次覆盖了冻结已有实验、正确身份的终态采集、首批原件与 worker 完成链。未实际触发新生成、部分 job 补分配、官网部分成功后 launch 失败、collector 故障后显式重入及最终应用重放；这些行为需在后续对应授权真实执行中取得证据。本次没有修改冻结历史输入或活跃 I13 collector。

2026-10-02 独立复核后重新执行正式终态操作，新的证据位于 `runs/experiment-operations/terminal-scope-operation-20261002/operation`。旧目录及其冻结 source 未修改。新 inputs.run_ids 仅包含 `minimal-f9c6da7ecf0ce1`，first_attempt_jobs 为空。独立读取新的公共 accepted.json，身份、first_batch、done 均绑定同一原 run；collector 状态为 completed，worker completed。没有启动生成 controller 或收费调用。本次真实终态证明新的公开回执消费链；共享 collector 尚有其它活动 target 时本scope先完成、排除外部retry的场景仍待对应授权真实运行覆盖。
