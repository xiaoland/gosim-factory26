# lab.arc_bench：ARC 适配与评测证据

lab.arc_bench 是当前 `lab.run` 的 ARC 目标适配边界：每次生成或评测都是独立的 run，状态、原生会话、资源、费用和平台回执写回该 run。旧 `lab.exp` attempt 仍由历史 reader 消费，不会被新 run 隐式转换，也不再是新 run 的调度单位。

公共参赛入口将内部生成失败与进入评测的退出码分开：安装、生成子进程普通非零退出或收尾异常保留原始诊断，入口返回 0，使 Runner 有机会评测输出中的现有应用。`.factory26/generation-entry.json` 保存入口退出码、实际生成子进程退出码和错误；返回 0 不表示需求完成、应用发布成功或获得评分。外部 SIGTERM/SIGINT、被信号终止的子进程以及 variant 的 130/143 终止出口保留非零状态，SIGKILL 无法捕获。清理和采集证据不可得不应自行终止整个生成入口；官方资源限制和外部停止仍由其实际执行方强制执行。旧冻结包不会自动取得这个出口行为。

- arc_bench_adapter.py：调用官方 Runner，保存请求、响应和平台身份。
- hosted_run.py：当前 Hosted run 的 upload/create/start、只读观察、取消和 workspace 保存；未知 POST 结果只查询确认，不自动重发。
- hosted_monitor.py、local_monitor.py：旧 operation 的平台/容器采集器，保留历史生产者身份；当前 run 由 `lab.automation observe` 调用 `execution.observe/save`。
- model_facts.py：展示声明、冻结、实际配置和已观察调用，缺少材料时明确 unknown。
- arc_artifacts.py、workspace_archive.py、docker_workspace.py：处理 ARC 产物、workspace 和 Docker 证据。
- results.py、evaluate.py、arc_replay.py：解析结果、评价和重放；评分与生成 attempt 分开。
- local_job.py、score_evidence.py：历史 lowering 与保存评分依据解释；当前 Local profile 直接装配宿主 SDK `local_submit.py`、不可变 image 和显式 runtime/package。
- arc_matrix.py、official_matrix.py、package_arc_replay.py：显式组合、冻结和发布 ARC 评测材料，不自动启动下游评价。
- package_incremental_replay.py、incremental_replay.py：为独立应用评分冻结官方基线到生成应用的文件差量；应用前核对基线哈希，保留未涉及文件。此包不调用模型，只能用于已授权的自费独立评分，不能作为正式参赛 Agent。

新 run 的独立评测由 `lab.arc_bench.evaluate` 提供：

```python
from lab.arc_bench.evaluate import evaluate_run, freeze_application

snapshot = freeze_application(source_run)  # completed run 的固定 ARC 输出
evaluate_run(source_run, kind="task", snapshot=snapshot,
             configuration={"kind": "task", "task": "bookstack"})
```

`kind` 为 `simulate`、`task`、`official` 或 `self-test`。`simulate` 使用公开、固定的 `argv`；`task` 使用维护 registry 中的题目别名解析 requirements/tests；`official` 必须显式提供 `billing_mode`（`self_funded` 或 `competition`）。`self-test` 使用 ArcBench 自测站的私有 `*-req-test` 题目，独立上传同一冻结应用的 ZIP，结果不计正式排名，也不读取模型路由。四种路径都创建独立 run：不可变应用保存在 `inputs/application`，供执行器消费的可写副本位于 `data/workspace`，requirements/tests 位于 `inputs`。评测装配不会重新构建生成 variant，不把 self-test 回退到 Hosted `/submissions`。不会读取可变的 `latest` 目录，也不会把隐藏评分写回生成输入。评测派发后自动注册一个 observer，不启动生成默认 automation。运行中的生成只能传显式应用路径或 `{git_repo, commit}` 快照引用。

`self-test` 的 adapter 复用站点公开浏览器客户端所用的三步协议：`POST /api/upload-url`、对返回的预签名 URL 做一次 `PUT`、再 `POST /api/submit`；提交和网络不确定时不自动重试。它在 `records/self-test/` 保存脱敏请求摘要、平台 submission identity、状态和结果原件，`save` 明确记录“站点没有 workspace 导出”这一缺口。执行宿主使用目标站点的 Helium 私有会话材料；不复用 ARC Hosted cookie，也不把 cookie 值写入 manifest、日志或评测输入。应用包装使用明确的 Linux/amd64 production runtime 和根 `Dockerfile`，限制为 50 MB，包装失败会留在当前 run 而不会伪造评分。

Mac 上首次准备 Helium 会话时，只对命名为 `Helium Storage Key` 的 Keychain 项目发起一次有界读取；用户若看到系统授权框，只需为本次读取选择“允许”，不需要修改 ACL。读取出的目标域、未过期 cookie 只写入 WorkSSD 上权限为 `0600` 的私有文件；同一文件仍有效时，后续请求和打包前准备直接复用，不重复唤起 Keychain。拒绝或超时会保留具体错误并停止本次提交，不会以其它浏览器凭据替代。

Chromium v10 的 AES-CBC 解密在 macOS 使用系统 CommonCrypto 的 `CCCrypt` 内存接口，派生钥匙不会出现在 `argv`、环境变量或日志中；远端执行宿主只接收过滤后的私有 Netscape 文件，不读取 Helium 数据库。

当生成运行位于 WSL/sfp7 时，远端 automation 只保存 self-test 请求，不在无浏览器会话的宿主上伪造派发；Mac relay 在源运行数据保存后创建本地 self-test child，自动 observer/save 仍由该 child 独占。若显式把 self-test 配置到远端目标，装配器会将仅含目标域 cookie 的私有文件以 0600 模式传输到远端 `.private` 目录，并从远端 manifest 中移除 Helium 发现配置。

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
