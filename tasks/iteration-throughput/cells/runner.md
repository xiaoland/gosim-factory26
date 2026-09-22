# Runner Cell：Competition 与 local simulation 实施前预演

记录性质：下列 Observed/Inferred/Unknown 与实施顺序为实施前的只读/隔离预演，彼时未改源码或调用 Competition 写接口。实施后的 adapter 和检查结果记录在文末；fixture 与 schema 证据在 `/tmp/factory26-runner-fixture`。

## Observed

### Competition 登录只读 schema

本机已有 `~/.config/factory26/playground.cookies.txt`（600 权限）；`python3 scripts/playground.py whoami` 通过，返回 authenticated=true。用同一只读 Cookie 直接调用 `playground.Client.request`，没有使用任何 POST：

- `GET /api/competitions` 返回 7 项。当前可见 id 包括 `arc-bench-lite`、`arc-bench-web`、`smoke` 等；列表项字段包含 `id/status/task_count/total_tests/template_required` 等。
- `GET /api/competitions/arc-bench-lite` 返回 2 个 task、66 tests，任务是 `arc-bench-lite--bookstack`（34）和 `arc-bench-lite--keep`（32），均为 `category=web`、`test_runner=playwright`。
- `GET /api/competitions/arc-bench-lite/submissions` 成功但列表为空；当前账号没有可用于只读 run/history 核验的 Competition submission。
- `GET /api/requirements?catalog=competition` 返回 15 项；两个目标 requirement detail 都返回字符串形式 `requirements_yaml/requirements_markdown/prerequisites_markdown`、资源 URL、`module_count/total_tests` 等。
- 现有 `scripts/playground.py requirements` CLI 只允许 `benchmark|playground`，不允许 `competition`；本次用其内部通用 Client 验证了 Competition endpoint。这个 CLI 缺口不能靠把 Competition 当 benchmark 修复，否则会混淆 venue。

完整脱敏 schema 已保存为 `/tmp/factory26-runner-fixture/competition-schema.json`。没有 submission/run id，因此未调用 `/runs/{id}` 的 status/logs/events/traceability/source/commit-history/workspace 读接口；这些字段仍只能引用已有 runner-design-evidence，不能声称本轮实测。

### 现有脚本调用图与可复用边界

- `scripts/playground.py` 的 `Client.request` 是最小可复用 HTTP 层：Cookie、GET/POST、multipart、无自动重试和传输不确定错误都已有明确行为。`redact`、`save`、`run_path`、`logs` 的 cursor 先落盘后推进、`summary/saved_summary` 的终态和 freshness 计算也可复用。
- `playground.submit`/`run`/`start`/`cancel` 是面向 Playground practice 的写路径，默认只做本工具记录的 practice/probe 校验；不能直接承接 Competition，因为其 `catalog`、`competition_id`、快照历史和 task 聚合合同不同。现阶段不要从这些函数自动调用写接口。
- `scripts/batch.py` 已有 controller 的有用骨架：exclusive `controller.lock`、冻结 `inputs.json`、状态先落盘、队列暂停、进程中断转 `unknown`、generation/evaluation 分离。它硬编码 4 variants×2 tasks，并调用本地 `factory.generate/evaluate`，不能直接复用为 hosted adapter。
- `scripts/concurrency.py` 只适合彼此隔离的本地 evaluation 或模型短探针；其 `workers_per_job=1`、reference case 比较和本地 evaluation 目录不是 Competition hosted run 合同。无需删除，只禁止纳入 hosted 状态机。
- `scripts/submission.py` 是 ZIP 内 Agent runtime，负责 manifest/凭据/沙箱/`frontend/package.json`+`backend/package.json` 校验和交付；不是 controller。`scripts/package_agent.py` 用 Docker 构建 Linux x86_64 离线 ZIP，并锁定 `svc/braid` source snapshot；它是 prepared package owner，不应由 hosted adapter 重写。
- 最小新增边界应是 `scripts/competition.py`（或等价独立 adapter），复用 `playground.Client` 的只读/HTTP 基础和 `playground` 的日志 cursor/redaction helper；不要把 hosted 状态塞进 `batch.py` 的固定矩阵，也不要让 controller 调用 `playground.submit` 的隐式写链。

### local simulation 预演

- 固定提交已验证：`/tmp/factory26-local-simulation-cfbbc287` 的 `HEAD=cfbbc287ee1bbffcf1e936545e4803145693a8d8`。README 和代码确认 `local_submit.py run --prepare-only` 只组装 workspace，不启动 Docker；生产标准路径要求根目录 `frontend/package.json` 有 `build`、`backend/package.json` 有 `start`，`deploy.sh` 只由 local wrapper 支持，不能作 Competition 资格。
- 在 `/tmp/factory26-runner-fixture` 创建的无模型 `standard-agent.zip` 只含根 `main.py` 与空 `requirements.txt`。运行：

  `python3 /tmp/factory26-local-simulation-cfbbc287/local_submit.py run --competition arc-bench-lite --task keep --agent /tmp/factory26-runner-fixture/standard-agent.zip --requirements-dir /tmp/factory26-local-simulation-cfbbc287/public-exercise/keep/requirements --tests-dir /tmp/factory26-local-simulation-cfbbc287/public-exercise/keep/tests --workspace /tmp/factory26-runner-fixture/workspace-standard-keep-2 --prepare-only`

  成功生成 `runner-spec.json`、`local-submission.json`、submission、requirements 和 32 个公开测试；task identity 为 `arc-bench-lite--keep`，`evaluation_enabled=true`。fixture 直接运行后生成标准 frontend/backend，`scripts/submission.py:validate_application` 通过。
- `/tmp/factory26-local-simulation-cfbbc287/test_local_submit.py` 共 13 项通过；仓库 `python3 -m unittest tests.test_submission -v` 共 9 项通过、1 项因真实 Linux Landlock 环境缺失而 skip。脚本 `py_compile` 和 help 均通过。
- Docker 客户端存在，但 daemon 不可用：`failed to connect to the docker API ... /var/run/docker.sock`。本机无 `arcbench-local-submit:latest` 镜像；local fixed runner 需要 ARC-Bench website checkout 的 `backend/runner/Dockerfile` 或主办方预构建镜像。`third_party/arc-bench`（当前 `1eb018367b...`）只有评测源码/Dockerfile，不是 local simulation 基础镜像来源。故本次没有运行容器、npm install/build、backend ready、Playwright、Meter 或 `local-run.json/local-result.json`。

## Inferred

### Hosted 最小 adapter 状态

每一个 `{variant, task}` 绑定一次冻结 package bytes 和以下最小状态；状态记录包含 `venue=hosted`、`package_sha256`、`competition_id`、`task_id`、`submission_id`、`run_id`、`phase`、`observed_at`、`error_class`、`artifact_handles`：

```text
planned
  -> prepared
  -> snapshot-saved(submission_id)
  -> run-created(run_id)
  -> started
  -> terminal(status: known | unknown)
  -> collected
       \-> blocked/unknown
```

`prepared` 仅由本地 ZIP 结构、manifest、sha256、source/material revision、venue/task identity 和入口资格检查共同证明；不能用 package build 日志代替。Hosted 写顺序必须是 `POST /submissions` 成功响应落盘后才允许 `POST /runs`，run id 落盘后才允许 `POST /runs/{id}/start`。一次 task 一个 run 的约束在平台 schema 确认前只能作为 adapter policy，不能声称平台已保证。

### 恢复与幂等

- 所有写请求都禁止客户端自动重试。响应成功先 fsync/原子保存 identity，再进入下一写；未知传输结果先走只读 GET/history 核查。
- snapshot POST 未知时，比较请求前后的 history，接续唯一新增且名称与本次请求相符的 submission。存在歧义时保留现场；不要求平台未提供的 package hash。
- run create POST 未知时，如果平台只暴露已知 `run_id` 查询，则无法恢复未知 id；adapter 必须保留 `create-unknown` 证据并暂停该 task，不能再 POST。若登录后只读 schema证明有按 submission/task 的 run history，才实现唯一匹配并继续。
- start POST 未知但 run id 已知时，GET run status/events；`PENDING/RUNNING/PAUSED/PAUSE_REQUESTED/RESUME_REQUESTED` 归 `started`/等待，明确 `PASSED/FAILED/CANCELLED` 才归 terminal，未识别值永远保留 `unknown`。
- `logs` cursor 使用 `(log_offset, after_event_id)`；同 cursor 重放覆盖同一个 chunk，只有 chunk 已持久化才推进 cursor。status、logs、events、traceability、commit history、source/workspace/archive 各自保存 source 与 observed_at；“日志出现 collected”不等于产物下载成功。
- controller 重启时只恢复 `queued/prepared/generated` 等明确可重做本地阶段；`snapshot-saved/run-created/started` 任何写后不确定状态先读后判，不能从头提交。状态、input manifest 和 package hash 不一致立即 blocked。

### local 缓存与并发边界

- 可复用缓存只有 fixed local-simulation source checkout、已冻结 package bytes、requirements/reference snapshot、脚本/source digest 和（未来）明确 digest 的 Docker image。当前没有可用 runner image/cache；不能用 `deploy.sh` 成功或 `node v26/npm 11` 主机环境替代官方容器。
- local run 的并发单位是独立 workspace + container + port + output；Playwright 固定 worker=1。共享 Meter key 并行时 token/cost 差值不可归因，成本应标 `unattributed`，或另做串行成本 probe。Hosted slot、同 submission task 并发和 key 限额当前未知，默认 controller 串行 task，直到只读/一次明确授权的 spike 证明更高并发。
- `batch.py` 的 generation/evaluation 双池不能直接代表 hosted slot；它只可在 hosted adapter 外继续运行 local matrix。不要让一个 root scheduler 同时承担本地 process 与远端 run 的重试语义。

## Unknown

1. Competition 写请求是否支持 idempotency key；snapshot/run POST 超时后可用哪些 GET/history 字段唯一核查；重复写是否收费或拒绝。
2. 当前账号没有 submission，因此 `/runs` history、现有 run status/logs/events/traceability/source/workspace/files、archive 和 commit-history 的实际权限与字段未核验。
3. 同一 submission 是否每 task 只允许一个计分 run，失败后的 rerun 是替换、追加还是冻结；平台聚合何时刷新、失败是否进入分母。
4. hosted slot、submission task 并行度、每 key 限额、队列容量错误形状和 PAUSED 恢复合同未知。
5. Competition ZIP 最大字节/文件数、执行时限、CPU/memory/network、visual_model 注入及标准 frontend/backend 生产镜像版本未知。
6. local fixed runner 的真实基础 image/digest、ARC-Bench website checkout 来源、Docker daemon 和 Apple Silicon→amd64 构建条件未知；因此 prepare-only 是成功，deploy/score 仍 unknown。
7. local simulation 的 Meter 查询会对 `/api/user/login`/logout 产生外部会话副作用；本次未运行 container，未读取 Meter，也未做成本 spike。

## 精确拟改文件与 owner

1. **package owner**：`scripts/package_agent.py` 继续负责 Linux x86_64 ZIP、source snapshot、manifest/hash；必要改动只为把 `package_sha256`/manifest handle 暴露给 controller。`scripts/submission.py` 继续负责包内入口/标准 frontend/backend 资格，不混入 hosted API。
2. **hosted adapter owner**：新增 `scripts/competition.py`，封装 Competition-only schema、prepared identity、snapshot/run/start、GET status/logs/events/traceability/source/artifacts 和原子 state journal；复用 `scripts/playground.py` 的 `Client.request`、redaction、cursor 规则，默认只读命令不拥有写权限。
3. **practice compatibility owner**：`scripts/playground.py` 保持 Playground practice 的已有写合同；仅可加显式 `competition` 只读子命令或把只读 schema 放到 `competition.py`，不能把 `catalog=competition` 借给 Playground submit。
4. **local controller owner**：`scripts/batch.py` 保持固定 4×2 本地生成/评测；若要接 local simulation，新建 `scripts/local_runner.py` adapter，复用 `/tmp`/固定 checkout 的 `local_submit.py --prepare-only` 和独立 workspace，但不复制评分或 Docker 逻辑。`scripts/concurrency.py` 继续只做本地独立评测/短 probe。
5. **integration tests owner**：新增最小 `tests/test_competition.py`，只用 fake `Client`/fixture 验证状态 journal、未知 POST、GET recovery、cursor replay、duplicate task/package refusal；扩展现有 `tests/test_submission.py` 只覆盖 package identity，扩展 fixed runner 的 13 个测试不改其源码。

## 严格实施顺序与可运行检查

1. 固定 Competition task/package manifest schema，先跑 `package_agent.py` 的离线 fixture 或 `submission.verify_package`；检查根 `main.py`/`requirements.txt`、sha256、source digest、frontend/backend contract、禁止 `deploy.sh`。失败归 package qualification，停止 hosted/local adapter。
2. 仅实现 `competition.py` 的 GET schema capture 和脱敏保存；用当前登录 session 重跑 competitions/detail/requirements/submissions，未知字段保留，缺 submission 不伪造 run。检查 JSON schema 与 `competition-schema.json` 可重复读取。
3. 用 fake transport 证明 `prepared→snapshot-saved→run-created→started` 的逐写持久化、未知响应停机、GET 唯一核查和重复 controller lock；不触真实 POST。检查每个 task/package pair 只有一条 identity。
4. 接入只读 run collection；对 fake `PENDING/RUNNING/PAUSED/未知/PASSED/FAILED/CANCELLED` 检查状态分类、日志 cursor、terminal 与 collected 分离、重复 poll 不重复 artifact。真实账号无既有 run 时只能完成 schema capture。
5. 固定 local simulation commit，先执行 `--prepare-only`；Docker/image 可得后才执行单一无模型标准 frontend/backend deploy-only，并保存 `local-run.json/local-result.json`。失败分类为 local fixture/image/runner，不进入正式评分。
6. 用两个不同 workspace/container 的无模型 fixture 做 local 并发；验证端口、输出、package hash、source/task identity 独立。共享 key 下 cost 设不可归因；不得把 `concurrency.py` 的本地评测速度外推 hosted slot。
7. 在外部写授权前完成所有 fake/prepare/read checks；若以后批准一次 hosted smoke，只使用冻结 ZIP + 一个 smoke task，先保存 submission identity，再逐 task create/start，禁止自动重试，结果单独标 `venue=hosted-practice`，不并入正式矩阵。

## 会使方案回退的证据

- Competition 不返回可持久化 submission/run identity，且未知 POST 无 GET/history 核查：hosted adapter 不能安全实现，回退为人工单步或暂停，不写盲重试。
- 同一 snapshot 在不同 task 被平台隐式改写，或无法保存 package hash/manifest 与 run：冻结 ZIP/跨 venue 可比性失效，返回设计。
- 标准 frontend/backend 在固定 production runner 与 local simulation 入口不一致，且没有同一 ZIP 的兼容路径：不能以 local `deploy.sh` 资格替代，回退 package contract。
- terminal status、日志游标或产物下载没有稳定身份，无法区分 unknown/failed/collected：controller 不得自动推进或汇报完成。
- hosted 强制单槽/单 key，或平台只给总榜分数无 task/run/cost 粒度：停止并发/成本比较设计，保留 venue 与不可归因字段。
- Docker image/digest、固定 runner checkout 或需求 revision 无法固定：local 只能做 prepare-only，不能进入资格或 score。

## 残余

本次已证明登录只读 schema、固定 local runner checkout、prepare-only workspace、标准入口检查和现有脚本边界；未证明 Competition 写接口幂等、hosted run 终态/产物权限、Docker deploy、Meter、真实并发或正式成绩。不能以源码审阅、schema GET、prepare-only 或 fake adapter 宣称 hosted/local runner 通过。

检查摘要：`python3 -m unittest tests.test_submission -v` → 9 passed、1 skipped（需 Linux Landlock）；fixed runner `test_local_submit.py` → 13 passed；脚本 `py_compile`/help → 通过；`local_submit.py --prepare-only` → `arc-bench-lite--keep` workspace 成功；Docker → daemon unavailable。

## 已实施的 Competition adapter（2026-09-22）

[`scripts/competition.py`](../../../scripts/competition.py) 现在提供独立 CLI 与 Python API，复用 `playground.Client` 的 Cookie HTTP 与 redaction，不调用 Playground practice 写入口。本轮没有真实 POST、上传、模型请求或 Competition run；非空 history 和真实终态字段仍需主会话的获授权 smoke 核验。环境最新事实见 [environment.md](environment.md)，不能沿用前述“所有 Docker 不可用”的推断。

准备参数为一个 variant、冻结 ZIP、Competition ID、完整 task IDs 与公开模型设置。ZIP 必须含根 `main.py`、`requirements.txt` 和 `package-manifest.json`；adapter 验证无重复/越界路径或 symlink、载荷集合与哈希，然后保存自己的只读 ZIP 副本、SHA256 和原 package manifest（包括 capabilities/material/source 身份）。这只证明包结构与身份，不证明入口部署或模型资格。相同参数再次 prepare 只读复用；不同包、task、variant 或模型设置拒绝覆盖。

```sh
python3 scripts/competition.py prepare \
  --state runs/competition/pi-team-mixed \
  --package runs/packages/pi-team-mixed.zip \
  --competition arc-bench-lite --variant pi-team-mixed \
  --task arc-bench-lite--keep --task arc-bench-lite--bookstack \
  --model-config /path/to/public-model-settings.json

# 写入口；key 由既有仓库外配置读取，只在 snapshot multipart 中传递。
python3 scripts/competition.py run-all --state runs/competition/pi-team-mixed

# 下面只请求 GET 并更新本地证据；不会创建、启动或取消远端 run。
python3 scripts/competition.py status --state runs/competition/pi-team-mixed --task arc-bench-lite--keep
python3 scripts/competition.py collect --state runs/competition/pi-team-mixed --task arc-bench-lite--keep
python3 scripts/competition.py recover --state runs/competition/pi-team-mixed
```

`public-model-settings.json` 只需 `base_url`、`model` 与可选 `visual_model`；base URL 必须为不含凭据的 HTTPS URL。`--offline` 只在 `snapshot`/`run-all` 中为无模型 fixture 传非凭据占位符，不会改写包。单步接口还包括 `snapshot`、`create --task`、`start --task`、`logs --task`、`watch --task`。

CLI 默认仅显示状态、阶段、submission/run IDs、score_status、包哈希和证据目录，不输出平台结果或日志正文。显式 `--json` 才输出完整 summary；Python API 保留完整结构供矩阵消费。

Python 调用供外层矩阵复用：

```python
import competition

competition.prepare(state_dir, zip_path, competition_id="arc-bench-lite",
                    variant=variant, tasks=task_ids, model_config=model_settings)
with competition.Controller(state_dir, secret=key) as controller:
    result = controller.run_all(interval=180)
```

一个 controller 持有 state 目录锁和按 Competition 的 hosted 锁；local 评测队列不使用这些锁。`run_all` 先上传一次 snapshot，再串行完成其各 task，已有终态只补收证据。上传下一 variant 前检查上一 snapshot 的完整标志或全部 task run 的明确终态；创建 task 前检查当前 snapshot 仍是最新。history 必须提供单条记录、明确 `is_latest`，或无歧义 `created_at`；无法识别则停止写入。独立浏览器/其它主机不受本地锁约束，因此真实 smoke 仍须核验服务端 latest 规则。

`state.json` 在每次 POST 前原子保存 pending action，响应到达后先持久化 receipt，再保存确认的 identity。中断或未知响应不会自动重发。snapshot 恢复使用 history 中此前不存在、与请求 display name 相符的唯一新增记录；实际 API 没有 package hash，不再要求该字段。create 恢复只接受该 snapshot 的唯一 task-score run，或 `recover --run-id` 指定后由 GET 验证 submission/task 归属的 run。start 恢复需要已启动时间、运行态或明确终态；仅 PENDING 不视为已启动证明。缺 identity 的成功响应同样保留，不默认成功。

每题在 `tasks/<task-id>/` 保存带 source/observed_at 的 status、日志分块、traceability 和 commit history。分块落盘后才推进游标，相同游标重放覆盖同一文件。辅助 artifact endpoint 失败保留 `collection_errors`，不阻断已取得的任务终态或评分；archive 仅保存可下载 handle，明确 `archive_downloaded=false`。默认轮询间隔 180 秒，拒绝更短间隔；PAUSED 或未知状态停止本地等待，远端任务保持原状。

`summary()` 返回 `status=completed|blocked|running` 和独立 `score_status=complete|unavailable`。前者表示声明的任务均已取得明确终态；辅助诊断缺失另列；FAILED/CANCELLED 不推导零分。后者在每题真实返回有限 score 与有效 passed/failed 计数、且与实际 tests 数组长度吻合时为 complete；实际响应没有 total_tests，消费者以测试行数记录总数，并保留 token_cost_usd。不靠模型声明或退出码推算成绩。平台原始结果保留于 status 证据，不将逐题 score 合成为官方总榜。

验收：`python3 -m unittest tests.test_competition -q`，18 项通过；覆盖冻结副本与原样恢复、同一 snapshot 两题顺序、unknown snapshot/create/start、错误 identity、成功响应后本地中断、malformed response 恢复、unknown status、游标发布失败重放、旧 snapshot 拒绝、上一 variant 未完成拒绝、锁冲突、辅助诊断缺失不阻断完成，以及成绩字段不足不计实验完成。与既有 `tests.test_playground` 的联合检查也通过；这些单元检查使用 fake transport；实际官方 submission f9d8960d81a5 已上传，Keep run 007b8fc9d38b 已启动，真实结果归属 runs/competition/iteration-throughput-boundary-20260923/。

## 本轮练习与初赛提交的边界

再次核对用户提供的《参赛须知.pdf》：初赛正式提交由队长发起、使用平台内置独立 key、一次运行两题，两个任务结束后才能开始下一次；个人 key 的平台练习不计最终榜单成绩。本轮按已批准目标运行官网 ARC-Bench-Lite Competition 练习，使用个人比赛 key，不能把这里的分数称为初赛正式成绩。现有 Competition adapter 是已观察的练习 API，不假定它就是 9 月 24 日开放的正式提交 API。PDF 没有给出 ZIP 大小上限；371.72 MiB 候选已被官网接收，不能据此推断平台上限。
