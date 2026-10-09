# 串行 stage-B 执行器

`serial_night.py` 只读取已经保存的 stage-A experiment，自动定位唯一
`execution.json`，等待 `phase=exited`、`remote_status` 为平台终态、完整 score/counts
以及 `application_seed.status=published` 的目录；程序还核对 `application-manifest.json`
为 `factory26.harness.application` v2、`delivery_kind=final`，并用
`seed-provenance.json` 绑定同一 attempt/run/submission 与 manifest hash。然后把真实 seed 路径替换进
stage-B intent 的 `${APPLICATION_SEED}` 标记，并在 `opportunity-ledger.json` 的
文件锁内领取唯一 `audit-B`。

启动前会对 template production 去除 `producer/application_seed` 做一次
`package_agent.plan_material` baseline，A 完成后再核对同一 canonical dependency hash。
它随后固定执行当前 Lab 合同的 `python -B -m lab.exp compile → build → start`，build
消费 `compiled/recipe.json`，子进程从仓库根目录启动并显式带项目 `PYTHONPATH`；路径参数由
`--environment`、`--compiled`、`--experiment` 和 `--deployment` 明确给出；启动后
继续读取 stage-B experiment，等待同样的完整终态，并登记 monitor-contract。不会由
返回码提前宣称 B 已完成。

所有路径必须位于 `/Volumes/WorkSSD`。程序保存每次观察、每个步骤的 stdout/stderr、
退出码和最终机会状态；发现 `audit-B` 已 claimed/running/completed 时直接退出，不重复派发。
它只处理 opportunity 2，第三次机会由 root 根据终态和台账决定。
