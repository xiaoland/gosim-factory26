# Competition 与主办方 local runner 证据

调查范围：ARC-Bench Competition（非 Playground）当前公开页面/API/前端，以及主办方 `hackathon-local-simulation` 固定提交版本。调查日期为 2026-09-22。本文只记录可复核的观察、由观察支持的推断和仍未知的接口；没有发起上传、创建 run、启动或取消等写操作。

## 证据来源与可信度

| 来源 | 观察方式 | 可证明范围 |
| --- | --- | --- |
| [Competition 页面](https://arc-bench.com/competition)、[API 文档](https://arc-bench.com/api-doc) | 公开页面和当前前端行为 | Competition 的任务/快照/运行 UI 与 SDK 运行时约定；网页/API 路由仍应视为当前实现接口，不当作长期稳定公共 API |
| `GET /api/competitions`、`GET /api/competitions/{id}`、`GET /api/requirements?catalog=competition`、需求与公开 tests | 2026-09-22 只读 HTTP 请求 | 当前比赛、任务数量、测试数量、任务 ID、需求/公开测试内容；未证明需登录的写请求 |
| 网站当前 JS `assets/index-5u2DjXvG.js` | 只读下载并检索客户端 API 封装 | 当前浏览器实际构造的 Competition multipart 字段和 run/日志/产物路由；不证明后台版本兼容承诺 |
| [`reports/2026-09-20-development-loop.md`](../../reports/2026-09-20-development-loop.md)、[`reports/2026-09-20-playground-concurrency.md`](../../reports/2026-09-20-playground-concurrency.md) | 仓库已保存的请求与已完成探针 | Playground 的真实上传/创建/启动/终态/日志/traceability 形状；不能冒充 Competition 运行证据 |
| [主办方 local simulation 固定版本](https://github.com/code-philia/hackathon-local-simulation/tree/cfbbc287ee1bbffcf1e936545e4803145693a8d8) | 克隆并阅读 `README.md`、`local_submit.py`、`local_runner.py`、`test_local_submit.py` | 本地 runner 的打包、容器、部署、Playwright、结果和 Meter 逻辑；不证明生产平台隐藏 runner 的实现 |

## Observed：Competition（非 Playground）

### 比赛与任务快照

当前公开 `GET /api/competitions` 返回了以下可运行比赛：

- `arc-bench-lite`：2 tasks、66 tests；任务为 `arc-bench-lite--bookstack`（34）和 `arc-bench-lite--keep`（32）。
- `arc-bench-web`：6 tasks、484 tests；包括 `12306`、BookStack、Ctrip、Keep、PrestaShop、Stack Overflow。
- `smoke`：2 tasks、2 tests；`smoke--counter` 和 `smoke--dice`。

`GET /api/competitions/{id}` 还返回每个 task 的 `id`、`category=web`、`test_runner=playwright`、`total_tests`、`module_count`、需求资产/参考资源 URL，以及 `template_required` 和 `template_source_competition_id`。例如 `arc-bench-lite` 的 `template_required=false`；Evolution 比赛标记为需要模板来源比赛。当前 `GET /api/requirements/{id}?catalog=competition` 和 `/tests?catalog=competition` 可公开读取需求与公开测试，不能由此推断隐藏测试内容或正式测试 revision。

官方 Competition UI 文案与前端调用共同表明：一次上传先保存为 Agent submission snapshot，随后在具体 task 页面选择该 snapshot 运行；同一 Competition 的完整排名需要该 submission 的所有任务运行完成。Competition 历史数据按 submission 聚合 `task_scores`，其中每个任务可带 `task_id`、`run_id`、`score`、`test_pass_rate`、`feature_implementation_rate`、`run_duration_seconds`、`token_count`、`token_cost`。公开 leaderboard 响应还返回 `is_complete`、`passed_count`、`test_total`、`total_cost`、`score_available` 和 `score_regime`。这证明平台有跨任务聚合视图，不证明所有失败状态均可进入聚合或可重跑规则。

### 上传、快照、创建与启动

当前 Competition 前端实际使用的请求形状是：

1. `POST /api/submissions`，`multipart/form-data`，至少包含 `competition_id`、`runtime`、`catalog=competition`、`agent_source=upload`、`file`；页面还发送 `display_name`、`base_url`、`api_key`、`model`、`visual_model`，可发送 `requirement_id`、`task_type`、`template_selections`。成功后客户端消费 `submission.id`，UI 显示已保存快照并进入 task。
2. `GET /api/competitions/{competition_id}/submissions` 读取该比赛的本人 submission 历史；Competition UI 只允许最新 saved snapshot 承接尚未运行的任务，旧快照显示为 superseded。
3. `POST /api/runs`，`multipart/form-data`，发送 `submission_id` 和 `requirement_id`，得到 `run.id`。
4. `POST /api/runs/{run_id}/start` 启动该 task run。Competition UI 的“Run remaining”是在客户端逐个执行 create-run → start；没有从前端观察到一个原子性的 Competition bulk-run API。

这些 route/field 是当前站点前端观察到的接口。仓库旧的 Playground 客户端也使用相同的 `/api/submissions`、`/api/runs` 和 `/start` 路由，但其 `catalog=playground`、`competition_id=null`，不能直接当作 Competition 成功写入证据。旧教程中出现的 `model_name` 字段与当前前端的 `model` 不一致，不能静默混用。

### 运行观测、终态和并发

当前前端为单个 run 使用：

- `GET /api/runs/{run_id}`：刷新状态和聚合字段；
- `GET /api/runs/{run_id}/logs?log_offset=…&after_event_id=…`：读取 stdout/stderr 与 runner events 增量；
- `GET /api/runs/{run_id}/events?since_version=…`：SSE `submission-update` 事件；
- `GET /api/runs/{run_id}/traceability?node_id=…` 或 `node_id=__all__`；
- `GET /api/runs/{run_id}/commit-history`、`/source?...`、`/preview/status`：读取提交、源码和预览状态。

已保存的真实 Playground run 观测到 `PENDING`、`RUNNING`、`PASSED`、`FAILED`、`CANCELLED`、`PAUSED`；前端控制逻辑还识别 `PAUSE_REQUESTED`、`RESUME_REQUESTED`。这批值来自同一站点的 runner/status 形状，尚没有 Competition run 的实际终态样本，因此 Competition adapter 应保留未知枚举并将未识别值记为 `unknown`，不能把非 `PASSED` 统称为失败。

已实测 Playground 客户端的关键边界是：写请求没有自动重试；上传响应成功后会先持久化 `submission_id`，创建 run 的传输结果不明时不重复上传；日志先落盘再推进 offset；终态收集状态、日志、traceability 和 commit history。该证据可复用为 controller 的写后核查原则，但没有证明 Competition 写接口幂等。

没有 Competition 实际写入或长任务队列证据。已完成的 Playground 模型 HTTP 短请求 2 路/4 路均成功，及 WSL 独立评测 2 路/4 路约 1.98×/3.91× 吞吐；这只证明客户端请求可以重叠和本地独立评测可并行，不证明 hosted Competition slot、同一 submission 多任务并发、单 key 限额或平台队列容量。当前 Competition UI 逐任务串行发起请求，也不是平台拒绝并行的证据。

### 代码、应用和评分产物

当前前端明确暴露以下下载/查询动作：

- `GET /api/submissions/{submission_id}/archive`：Competition History 的 “Download code”，用于下载 submission ZIP；
- `GET /api/runs/{run_id}/workspace/files`：读取 run workspace 文件清单；
- `GET /api/runs/{run_id}/workspace/template-bundle`：下载该 run 的应用模板 bundle；
- run 的 `logs`、`traceability`、`commit-history`、`source`、`preview/status` 路由用于诊断和证据查看。

真实 Playground `PASSED` run 的 status 记录了 `stdout_path`、`stderr_path`、`workspace_path`、`logs_available=true`、测试明细和 `result_path=null`；其 `commit-history` 返回 `workspace_unavailable`。状态日志中出现 “Collecting test artifacts”，但没有观察到一个独立的 artifact download route，也没有证明 screenshots/traces/video 或隐藏测试报告能由 API 下载。Competition 是否允许上述 workspace/template bundle 路由、正式运行产物保留多久、评分报告是否有单独下载接口，仍需登录后只读核验。

Competition leaderboard 当前返回的是聚合后的 score/pass-rate/cost/time/token 字段。它没有公开逐 request Meter 明细；多个 run 共享一个模型 key 时，平台聚合成本是否按 run 可归因未知。

## Observed：主办方 local simulation runner

证据版本为 `cfbbc287ee1bbffcf1e936545e4803145693a8d8`。README 明确声明这是与竞赛平台核心运行阶段一致的本地模拟：运行上传 Agent、部署输出应用、可选 Playwright；它**不模拟登录、数据库、排队或排行榜**。

### 输入、打包与启动

- ZIP 根目录必须有 `main.py` 和 `requirements.txt`；额外语言可以由 `main.py` 启动。入口固定为 `python3 main.py <requirements_dir> --output-dir <output_dir>`，正常完成返回 0，异常返回非零。
- `local_submit.py` 安全解压 ZIP（拒绝绝对路径和 `..` 越界），允许去掉唯一顶层目录；把需求复制到 workspace 的 `template/requirements`，把 submission 放到 `submission/`，可选公开测试放到 `tests/`，生成 `runner-spec.json` 和 `local-submission.json`。
- 输出 workspace 必须为空或不存在；Docker bind mount 到 `/workspace`，默认以当前 UID/GID、`--cpus 1`、`--memory 2g` 运行。默认会把 `OPENAI_*`、`MODEL`、`VISUAL_*` 等白名单变量注入容器；平台 key 不应进入 ZIP。
- local image 通过 `Dockerfile` 包装生产 `run_submission.py`。基础 image 由 ARC-Bench website checkout 的 `backend/runner/Dockerfile` 构建，或由主办方提供的预构建 image 提供；固定版本仓库本身没有默认可拉取的真实 registry 地址。

### Agent 运行、部署和评测

`local_runner.py` 通过 monkey-patch 在生产 runner 外加了两项本地行为：

1. 若输出根目录有 `deploy.sh`，local runner 以 `HOST=0.0.0.0`、`PORT=3000`、`ARCBENCH_WEB_BASE_URL=http://127.0.0.1:3000` 前台启动它，并最多等待 120 秒直到 HTTP 状态小于 500。
2. 没有测试目录时跳过 Playwright 并写 `evaluation_status=skipped`。

README 明确警告：正式 `run_submission.py` 不支持 `deploy.sh`，生产路径要求输出根目录存在 `frontend/package.json` 和 `backend/package.json`，依次 `npm install`、前端 `npm run build`、后端 `HOST=0.0.0.0 PORT=3000 npm run start`。两种路径都必须让 `http://127.0.0.1:3000` 在 120 秒内可达。因而 Competition package 资格不能以 local-only `deploy.sh` 通过作为充分条件。

若提供 tests，runner 生成固定 Playwright 配置：Chromium、`workers=1`、test/expect timeout 各 10 秒、关闭 trace/screenshot；先 `npx playwright test --list`，再 `npx playwright test --workers=1`。这解释了为什么本地并发单位应是彼此隔离的 Docker run，而不是增加同一应用的 Playwright workers。

### 本地产物、终态与评分

一次 local run 的 host workspace 约定为：

```text
submission/
template/
  .arc/stdout.log
  .arc/agent-execution.json
  .arc/playwright-report.json    # 有测试且评测完成时
tests/
runner-spec.json
local-submission.json
execution.debug.log
local-run.json
local-result.json
```

`local-run.json` 记录 container exit code、结束时间、token count、token cost/currency 和 Meter 错误。`local-result.json` 在无 tests 时写 `evaluation_status=skipped`；有 tests 但无 Playwright report 时写 `evaluation_status=failed`、score 0；有报告时汇总每个 test 的 passed/failed、exact pass rate、feature coverage、run time 和 score。Meter 通过运行前/后 `/api/user/login`、`/api/user/freshness`、`/api/user/usage` 差值测量；billing 未及时 settle 或 key 不可用时 cost/score 可为空。共享 key 的并行 local runs 会让前后差值互相污染，不能据此做逐项成本归因。

local runner 的单任务 score 实现使用 `b0=1.2`、奖励指数 `0.1`、惩罚指数 `0.2`；README 同时说明正式比赛先跨任务汇总通过数、测试数和开销再评分，所以 local 单任务 score 只可作调试参考。它没有网站 snapshot、队列、重试或 leaderboard 状态。

## Inferred：可直接进入 HLD/LLD 的合同

下列合同由上面观察支持，足以写入设计；其中 Hosted route 仍应由 adapter 版本化，不把 route 字符串散落到 controller：

| 合同 | HLD/LLD 决定 |
| --- | --- |
| 不可变输入 | 每个 work item 先生成一次 ZIP，保存 `sha256`、构建/材料 manifest 和 `venue`；hosted 与 local 必须引用同一 bytes。ZIP 结构先验证 `main.py`、`requirements.txt`，再允许写入外部平台。 |
| Hosted 写链 | `snapshot_saved(submission_id)` → `run_created(run_id, requirement_id)` → `started`。每个响应先持久化再进行下一写；传输不确定时通过 GET/历史核查，禁止盲目重复 POST。Competition bulk-run 由 controller 自己编排，不假定服务端原子批量接口。 |
| Local 写链 | `workspace_prepared` → 单独 Docker run → `local-run.json` → `local-result.json`。无 tests 的 deploy-only 只能证明执行/部署，必须标为 `unscored`。 |
| 状态 | 内部最小状态应包含 `venue`、`package_sha256`、`competition_id`、`task_id`、`submission_id`、`run_id`、`phase`、`observed_at`、`error_class`、`artifact_handles`。保留未知远端 status；`terminal` 只在明确终态或本地进程终止且结果已解析时成立。 |
| 并发 | Hosted slot 上限和同 key Meter 归因都是配置/证据，不从本地 worker 数推断。Local 并发只能是独立 workspace、容器、端口和输出目录；同一 key 并行时 cost 标为不可分配，或成本 spike 串行。 |
| 评分 | 保存逐 task 的 platform score/pass/test counts/time/token/cost，并保存平台聚合原文；`local_score` 与 `hosted_score` 分开，不能拼成正式成绩。只有平台明确返回完整 Competition 聚合时才标 `complete`。 |
| 产物 | 每项保存 status、增量日志游标/事件、traceability、commit history、可下载 code/archive handle 和 local workspace 路径；“日志说 collected”不能代替下载成功证明。 |

## Unknown：必须前移的核验

1. Competition 是否接受当前 ZIP 的最大字节数、文件数量、执行时限、网络/CPU/内存上限，以及 `visual_model` 的实际注入规则。
2. `POST /api/submissions`、`POST /api/runs`、`POST /start` 是否有幂等键；超时后 GET 哪些字段足以判定请求已提交；重复 run 是否收费或被拒绝。
3. 同一 submission 是否确实只能对每个 task 建一个可计分 run，失败后 `rerun` 是否替换、追加或冻结 task score；`PENDING/RUNNING/PAUSED` 的队列含义和恢复边界。
4. hosted Competition 的并发 slot、每队/每 key 限额、同一 submission 多 task 是否可并行，以及队列排队时间和容量错误的返回形状。
5. Competition run 是否可下载 stdout/stderr、应用 ZIP、Playwright report、screenshots/traces、隐藏测试摘要；`workspace/files` 与 `template-bundle` 的权限和保留期。
6. leaderboard 聚合何时刷新，完整成绩是否要求所有 task 都有成功终态还是允许失败终态计入分母；平台 cost 是否有 request/run 级归因，币种和四舍五入规则是什么。
7. local simulation 基础 image 的真实来源、digest、生产镜像差异，以及 Apple Silicon/amd64 构建和网络依赖的可复现性。
8. local runner README 的 `deploy.sh` 分支只在本地存在；生产 runner 是否在未来同步该契约。当前应以标准 `frontend/backend` 输出为唯一 Competition 资格路径。

## 只读或无评分 spike 建议

按成本从低到高：

1. **只读 schema capture**：记录 `GET /api/competitions`、目标 Competition detail、requirements、公开 tests、leaderboard 的脱敏 JSON schema、ETag/时间和任务数量；重复一次确认稳定性。不调用任何写接口。
2. **本地包/部署资格**：用无模型替身 ZIP（根目录 `main.py`/空 `requirements.txt`，入口生成最小 `frontend/backend` 应用）执行 local simulation `--prepare-only`，再执行不带 `--tests-dir` 的 deploy-only。验收 package hash、workspace、环境变量白名单、端口 ready、`local-run.json`/`local-result.json`；不计分、不读 Meter。
3. **本地 runner contract fixture**：用两个互不共享 output 的无模型替身并行运行，记录容器 exit、应用 ready、产物路径和异常；再用受控传输错误 fixture 检查 controller 的“先 GET 核查、再决定是否重写”。不要用真实 key 测 cost。
4. **登录后 Competition 只读**：在不创建新 submission/run 的前提下读取 `/competitions/{id}/submissions`、已有 run 的 status/logs/events/traceability/source/commit-history/workspace 文件清单，确认权限和字段；把 test artifacts 是否可下载列为结果，而不是根据 UI 文案猜测。
5. **最小 hosted practice**：只有在明确授权一次外部写入后，用 smoke 的单 task、冻结 ZIP、单独 key 运行；它是接口/终态 spike，不是正式矩阵，不与正式 score 合并。先保存 upload response，再按 run 逐步验证，不自动重试。

## 会使方案失效的证据

- Competition 要求的入口、环境变量或 ZIP 结构与 local simulation 不同，且不能在同一冻结包内表达；尤其 package 只有 `deploy.sh` 而生产 runner 拒绝它。
- 上传后平台不返回可持久化的 submission identity/hash，或相同 snapshot 在不同 task 被平台隐式重写。
- 创建/启动写请求无可核查的状态、无法区分“未提交”和“已运行”，或重试会重复计费且无恢复 API。
- hosted run 不能按 task 返回稳定 terminal status、日志/错误分类或可下载产物，导致 controller 无法证明 `collected`。
- Competition 强制单槽、同 key 不能并行，或隐藏平台规则使 local 并发结果不能与 hosted 结果保持同一 evidence identity。
- 平台只给总榜分数而不提供 task/run/cost 粒度，且实验问题需要逐 variant 成本/耗时比较。
- local runner 的基础镜像、生产 runner 或公开需求 revision 无法取得/固定，导致同一 ZIP 不能在本地和 hosted 复现。

在这些证据出现前，设计可以固定“冻结同一 ZIP、hosted/local 分 venue、先快照再 task run、终态与产物分离、共享 key 成本不可归因”五项不变量；Competition 的确切 adapter 仍应等待上述最小 spike。
