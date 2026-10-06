# lab.arc_bench：ARC 适配与评测证据

lab.arc_bench 是当前 `lab.run` 的 ARC 目标适配边界：每次生成或评测都是独立的 run，状态、原生会话、资源、费用和平台回执写回该 run。旧 `lab.exp` attempt 仍由历史 reader 消费，不会被新 run 隐式转换，也不再是新 run 的调度单位。

- arc_bench_adapter.py：调用官方 Runner，保存请求、响应和平台身份。
- hosted_run.py：当前 Hosted run 的 upload/create/start、只读观察、取消和 workspace 保存；未知 POST 结果只查询确认，不自动重发。
- hosted_monitor.py、local_monitor.py：旧 operation 的平台/容器采集器，保留历史生产者身份；当前 run 由 `lab.automation observe` 调用 `execution.observe/save`。
- model_facts.py：展示声明、冻结、实际配置和已观察调用，缺少材料时明确 unknown。
- arc_artifacts.py、workspace_archive.py、docker_workspace.py：处理 ARC 产物、workspace 和 Docker 证据。
- results.py、evaluate.py、arc_replay.py：解析结果、评价和重放；评分与生成 attempt 分开。
- local_job.py、score_evidence.py：历史 lowering 与保存评分依据解释；当前 Local profile 直接装配宿主 SDK `local_submit.py`、不可变 image 和显式 runtime/package。
- arc_matrix.py、official_matrix.py、package_arc_replay.py：显式组合、冻结和发布 ARC 评测材料，不自动启动下游评价。

新 run 的独立评测由 `lab.arc_bench.evaluate` 提供：

```python
from lab.arc_bench.evaluate import evaluate_run, freeze_application

snapshot = freeze_application(source_run)  # completed run 的固定 ARC 输出
evaluate_run(source_run, kind="task", snapshot=snapshot,
             configuration={"kind": "task", "task": "bookstack"})
```

`kind` 为 `simulate`、`task` 或 `official`。`simulate` 使用公开、固定的 `argv`；`task` 使用维护 registry 中的题目别名（如 `bookstack`，或已配置的 `github`）解析 requirements/tests；`official` 必须显式提供 `billing_mode`（`self_funded` 或 `competition`）。三者都创建独立 run：不可变应用保存在 `inputs/application`，供 SDK 消费的可写副本位于 `data/workspace`，requirements/tests 位于 `inputs`。评测装配只准备 no-op/replay/argv 输入，不重新构建生成 variant。不会读取可变的 `latest` 目录，也不会把隐藏评分写回生成输入。评测派发后自动注册一个 observer，不启动生成默认 automation。运行中的生成只能传显式应用路径或 `{git_repo, commit}` 快照引用。

ARC 适配器保存本地文件和官网 API 响应；同一道题在同一账户只能有一个执行中的官方 run。平台 HTTP 错误、pending、需求版本差异和终态 GET 原件必须保留，不能以“已提交”推断模型已经开始。历史 run 只能由对应冻结 executor 或只读 reader 消费，不自动翻译成新 lab.exp 执行。

官方 Git 历史通知和发布由 arc-runtime.pyz CLI 入口完成；它不修改应用或实验索引。材料存在、实际调用、采集成功和官方评测结果属于不同证据来源。

## Runner 内的 Git 历史

先用 `python3 -m lab.arc_bench runtime export --output NEW_RUNTIME.pyz` 导出当前封装，variant 的 build 也使用这个入口。以下命令在 Runner 环境执行；在 Runner 外必须显式传 `--output-dir` 指定项目目录。

```sh
python3 /absolute/arc-runtime.pyz notify-history --json
python3 /absolute/arc-runtime.pyz publish-history --source-repo REPO --ref REF --json
```

`notify-history` 用于项目目录已经有 Git 历史的情形；`publish-history` 将指定提交及祖先导入受管 Runner 仓库，只更新 `arc-delivery` 引用，不覆盖应用文件或索引。两者每次调用都尝试写入刷新信号，回执分别保留 `history_changed`、`history_updated`、`signal_written`；信号写入不证明官网已显示，也不证明应用评分完成。应用就位后可用 `--preview` 请求预览刷新。源码、完整参数及幂等操作回执见 [agent_runtime 入口](agent_runtime/__main__.py)。

需要导出过程数据时，使用同一入口的 `arc-runtime.pyz traceability export_snapshot --json`（或按 SDK 约定传 `--json-file` 与 `--output-dir`）；导出的 traceability 快照、历史通知和发布回执分别是本地记录，不替代 Runner 产物或官方评测结果。

ARC 的宿主与目标由 environment 选择，模型/费用由显式 intent/recipe 冻结，凭据由实际私有输入提供；本模块只消费已冻结选择并记录平台事实。模型、评分和平台运行的完整验收需要实际授权实验，源码或离线回执不能替代它。
