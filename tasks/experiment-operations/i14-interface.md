# I14-0 设施消费交接

2026-10-02，本任务提供接口，不代替 I14 主任务冻结或启动收费运行。`scripts/package_agent.py` 没有本任务新增改动，I14 白名单、tool-env/OTLP 和 `--e2e-runtime` 由主任务维护；制品应先按各自 build.py 冻结，ARC matrix 消费实际 ZIP，不能从 variant 名推断 addon 已包含。

矩阵生成沿用 `python3 -m lab.arc_bench.arc_matrix`，四项用重复 `--variant pi-braid-i14=/绝对路径/agent.zip` 等参数，题目重复 `--case hackathon/github --case hackathon/sheet`，本轮标签 `--experiment-key e20261002-01`。其它实际材料继续显式指定 `--inputs-root`、`--runner`、`--host-runtime`、`--image`、`--env-file`，以及既有 storage 容量参数。资源新增参数为 `--workers 5 --shared-docker-slots 5 --memory 2g --cpus 2 --separate-evaluation`；若本轮没有官方本地测试材料，显式加 `--requirements-only`，不要推断或制造测试。env-file 是运行连接，工具 key 已在各包构建时按主任务冻结，不由 matrix 改写。CLI `--output` 保存配方 JSON，仍需 plan 冻结。

共享准入已接入 adapter→docker_workspace 实际执行边界，覆盖发送、容器执行和 finally。当前同 daemon 两个老 I13 物理运行计二，五槽初始余三，旧配额不改。不同 matrix 各自 workers 不能越过共享 registry；这是同宿主、同用户的 registry 约定，跨宿主不能据此宣称全局容量保证。精确 API、实际容量和未覆盖并发情形见 [shared-admission.md](shared-admission.md)。

操作规格可在私有 `runs/iteration14/i14-0/operation-spec.json` 写入以下实际字段，路径均指已冻结材料：

```json
{
  "authorization": "引用 tasks/iteration14/packet.md 中 e20261002-01 的实际授权范围",
  "venue": "local",
  "recipe": "/绝对路径/本轮matrix配方.json",
  "monitor_output": "/Volumes/WorkSSD/Development/factory26/runs/iteration14/i14-0/observation"
}
```

`python3 -m lab.arc_bench operation prepare <规格> --directory runs/iteration14/i14-0/operation` 冻结 experiment；`operation run <同一目录>` 启动并持续跟随；`operation status <同一目录>` 读回状态。入口生成 operation/active-matrix.json 供纯脚本采集，主任务的 `runs/iteration14/i14-0/active-matrix.json` 如需对外保留，应指向该实际 experiment 和授权 run 集，不能先填未经启动确认的身份。如果先使用 lab.plan 冻结，则规格引用 `experiment` 代替 recipe；不能同时提供两者。旧 experiment 运行自己的冻结 controller-source，新 operation 不会悄悄把它升级。

此规格省略 replay，不会上传评分。若本轮已授权每题完成后官网应用重放，需另冻结 `credential_file` 与 `replay.jobs` 的逐 job Competition 参数（competition_id、tasks、model_config、variant、credential_mode 等），题目必须严格对应原来源 job；不要用模型通道推断费用模式。pending 和已启动身份继续同一 journal，不重复创建执行。

共享槽和矩阵参数已编译、真实容量已读回；operation 已完成已有真实终态的冻结、采集交接与重入验收；按单操作范围完成及 attempt 授权的最终接口已经收敛。收费执行、多 controller 满格/失联以及新I14资源实际运行反馈须来自主任务获授权运行，不能把静态接口交接当作它们已验收。

最终 operation 接口已完成按单操作范围的真实终态验收，公开 `monitor/accepted.json` 提供逐 run 接收/终态及 collector 生命周期，调用者不读取内部 scheduler 格式。已有多 attempt 使用明确 `run_ids`，外部 retry 不扩大原范围。材料消费、收费启动和实际 provider 接续仍由 I14 主任务授权与验收。

主任务后续提出只替换未开始生成项的策略。当前冻结输入不支持原地修改，替代项必须另建冻结 plan；现有 `lab stop` 只提供整个 experiment 停止，不能用它实现只撤下未启动项。单纯先读 waiting 再发送停止会与准入/启动竞态，不能宣称保护已启动项。要支持此策略，需要在 controller 取消与实际容器启动边界共同仲裁“仅未启动”的条件；这项生命周期扩展尚未实现，不要用手工 TERM 或改 manifest 替代。主任务可先保持当前冻结条件，或在单项尚未启动前通过独立实验边界选择新条件；本任务不替其决定模型变更。

主任务最后确认可采用分批独立冻结：这是现有接口下可安全执行的路径。只为当前确定要启动的项创建 recipe/operation，未来项在条件决定后另作新冻结；每一目标题目/variant的执行名在主packet登记一次，避免因批次变更重复授权或评分。现有controller里的pending没有安全的逐job条件撤销接口，不能将它当作可原地替换的配置队列。模型选择及“两题两组最终分数齐全且平均至少高10个百分点”的判断归主任务，本入口不自动更换MODEL或费用通道。
