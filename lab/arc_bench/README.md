# lab.arc_bench：ARC 适配与评测证据

lab.arc_bench 是 ARC 官方 Runner、模型事实、官网状态、结果解释和可选过程证据的适配边界。它不改变 lab.exp 的 attempt 身份，也不从 OTLP 或 Agent 代码推断官方关系。

- arc_bench_adapter.py：调用官方 Runner，保存请求、响应和平台身份。
- hosted_monitor.py、local_monitor.py：旧 operation 的平台/容器采集器，保留历史生产者身份；新 experiment 的采集由 `lab.exp.hosted` 或 runner 负责，不另启动这些循环。
- model_facts.py：展示声明、冻结、实际配置和已观察调用，缺少材料时明确 unknown。
- arc_artifacts.py、workspace_archive.py、docker_workspace.py：处理 ARC 产物、workspace 和 Docker 证据。
- results.py、evaluate.py、arc_replay.py：解析结果、评价和重放；评分与生成 attempt 分开。
- arc_matrix.py、official_matrix.py、package_arc_replay.py：组合、冻结和发布 ARC 评测材料。

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

ARC 的宿主、凭据和费用选择由 lab.exp recipe/deployment 冻结；本模块只消费已冻结选择并记录平台事实。模型、评分和平台运行的完整验收需要实际授权实验，源码或离线回执不能替代它。
