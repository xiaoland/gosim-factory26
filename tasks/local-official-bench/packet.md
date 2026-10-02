# Lite/Web 本地官方运行模式隔离环境

## 目标与控制状态

目标是在当前 `factory26` 工作树旁建立独立的本地实验目录，使同一冻结参赛 ZIP 能按主办方 `local_submit.py` 的容器流程运行 `arc-bench-lite` 和 `arc-bench-web` 的公开需求与测试，并明确记录它与官网生产评分的身份差异。用户已批准开工。官方 `local_submit.py` 的生产镜像路径仍停在 `--prepare-only`；另在隔离目录建立 `platform-public-local` 诊断入口，已用无模型 fixture 在 Mac/WSL 实际部署应用并执行 Lite/Web Keep 各一例。没有启动新的真实模型生成或完整本地成绩；镜像与输入来源仍限定结论。

旧 Lite 控制器已在双比赛矩阵接管时本地退出；隔离环境不复用官网控制器、状态目录、工作区或 Docker 容器。现有其他 WSL 本地生成进程及用户未提交改动保持原样。

## 已核实的事实

- 主办方 `code-philia/hackathon-local-simulation` 固定提交 `cfbbc287ee1bbffcf1e936545e4803145693a8d8`，`local_submit.py run` 接受任意 competition/task、显式 requirements/tests、Agent ZIP、workspace 与 image；`--prepare-only` 已通过无模型 fixture。
- 该仓库的镜像只是在生产 Runner 基础镜像上加本地入口。基础镜像需来自另一仓库的 `backend/runner/Dockerfile` 或主办方发布的镜像；现有 Windows Docker daemon 镜像列表没有 `arcbench-runner:local-base` 或 `arcbench-local-submit:latest`。`third_party/arc-bench/Dockerfile` 是 ARC baseline 环境，不能替代。
- 历史宿主/WSL 对照曾使用 `factory.py` 与旧的 package runner，固定 `arc-bench` 为 `1eb018367bedd618d3b9ced406ce07fb423d4956`。旧 runner 已退役；公开上游 HEAD 为 `ddc7e40e4a715eadfd309a333b0da785192886e7`，同一应用在官网与这两版公开测试的成绩未对齐。
- 当前活动矩阵只配置 Lite 的 Keep/BookStack；公开 Web 有六题。`scripts/local_runner.py` 和 `scripts/official_matrix.py` 均硬编码 Lite，Web 须直接调用固定主办方脚本。2026-09-23 平台只读 Competition detail 列出 Web 484 项，但正确的公开测试接口发现 478 项。因此任务 ID、需求、测试哈希和版本必须逐题保存，不能仅凭题名或公开用例数宣称官网测试完全一致。
- Mac 的 `arcbox-win` Docker context 指向 `ssh://win-ws.localhost` Windows 主机，可读取其 Linux Docker daemon 镜像，但 bind mount 的源路径由该主机解释；另一个 `wsl.win-ws.localhost` 的 WSL 默认 `/var/run/docker.sock` 当前不可连接。容器执行须先在 Windows 主机可挂载的独立路径验证最小 bind mount。

## 方案

语义权威是主办方固定提交的 `local_submit.py` 和有来源的生产基础镜像；每个比赛的需求由平台 Competition task 快照持有，公开 ARC-Bench 测试仅是明确标记的本地测试快照。项目脚本只负责选择、冻结和记录输入，不复制或改写主办方的部署、Playwright、评分逻辑。每个 `{competition, task, package SHA256, input SHA256, image digest}` 使用全新 workspace；容器退出后保留 `runner-spec.json`、`local-result.json`、原始日志和输入清单。

隔离预演目录已建立在当前仓库的同级 `factory26-official-local/`：`runner/` 是干净的 `cfbbc287` checkout，`benchmark/` 是干净的公开 `ddc7e40` checkout，`platform-inputs/<competition>/<task>/` 按比赛保存平台只读返回的需求、公开测试、可取得的素材及来源记录，`fixtures/` 放无模型参赛 ZIP，`runs/` 每题独立。主办方脚本会把指定的需求与测试再复制到该次 workspace；来源 commit/API 观测时间与内容哈希须记入输入清单。实际容器执行侧要在能访问 Docker bind mount 的主机上建立同样布局；Mac 目录不能直接充当远程 daemon 的 mount 源。该目录不进入当前仓库的 `runs/`，不改变正在运行的矩阵。

最小命令形状为 `python3 runner/local_submit.py run --competition <id> --task <slug> --agent packages/<variant>.zip --requirements-dir platform-inputs/<id>/<slug>/requirements --tests-dir platform-inputs/<id>/<slug>/tests --workspace runs/<unique-id> --image <qualified-image-digest> --env-file <600-permission-file>`。`--task` 必须是 slug，不传完整平台 ID，避免脚本重复拼前缀。同一个主办方入口覆盖 Lite 两题和 Web 六题；未取得 image digest 前仅运行 `--prepare-only`，结果标为 assembled，不能标为可部署或已评分。

### 已执行的隔离预演

使用 `fixtures/standard-agent.zip` 和上述两个干净 checkout，对 Lite Keep/BookStack、Web 12306/BookStack/Ctrip/Keep/PrestaShop/Stack Overflow 各调用一次 `local_submit.py run --prepare-only`。八个 `runs/prepare-<competition>-<task>/runner-spec.json` 均标明正确的 `requirement_id` 且启用 evaluation；只装配工作区，没有启动 Agent、Docker 或测试。该公开 benchmark checkout 的 Playwright `--list` 发现 Keep 32、BookStack 34、12306 135、Ctrip 125、PrestaShop 86、Stack Overflow 66 项，即 Lite 66、Web 478。与平台此前显示的 Web 484 项不一致；发现用例数也不证明用例内容相等。`benchmark/node_modules` 仅链接到当前仓库同一 `package-lock.json` 的安装，用于只读测试发现。

随后只读查询当前平台 Competition detail 与八个需求 detail，并将需求 YAML/Markdown 逐题保存到 `platform-inputs/`。平台 Lite 两题分别列 32/34，Web 六题列 138/34/126/32/87/67；平台 Lite 的 YAML 与公开 `ddc7e40` 对应 YAML 在换行归一后相等，但 Web Keep、BookStack、12306 不相等，Web 同名题不可复用 Lite 的公开需求。平台返回的 Markdown 也不能从公开仓库直接推定。按当前页面前端代码发现正确测试接口 `/api/requirements/<task-id>/tests?catalog=competition`，保存八题公开测试到 `platform-inputs/<competition>/<task>/tests/` 并记录逐文件哈希；Playwright 实际发现 Lite 66、Web 478。Web Keep 仅 4/33、BookStack 仅 14/35 个测试文件与公开 `ddc7e40` 逐字节相等，其余四题及 Lite 对应测试文件均相等。平台列示 484 与公开 478 的差额来源未证实，不能把额外 6 项推定为某种固定隐藏测试。先前在错误 `/api/tests...` 路径上的 404 不构成“平台测试不可获取”的证据。

二进制素材的列表接口仍未知；按需求引用和公开仓库文件名，使用文件级 `/api/requirements/<task-id>/{assets|references}/<file>?catalog=competition` 下载并冻结 213 个文件，均与公开 `ddc7e40` 对应文件逐字节相等。另有 Keep 的 `label_filtered_list.png`、`search_keyword.png` 和 Ctrip 的 `index.jpg` 被需求文本引用，却在平台文件级接口与公开仓库中均不存在（对应 Lite/Web 合计 5 处 404）。它们保留为上游输入缺口，不用本地文件伪造。八题使用平台官网公开需求、测试和实际可取得的素材再次通过 `--prepare-only`，见 `runs/prepare-platform-public-*`；没有启动容器、Agent 或测试。仍不能据此推断平台未公开测试的身份或生产镜像行为。

独立 Agent 只读预演确认当前两个项目 controller 均限 Lite，固定模拟器内置输入亦不能承载 Web；直接传显式目录是共同路径。其检查还指出无模型 fixture 的实际容器 smoke 应清空继承的模型环境，避免意外访问 Meter。上述 `--prepare-only` 已由主 Agent 在隔离目录实际执行，独立 Agent 未启动容器或模型。

## 缺镜像时的可运行诊断路径

主办方模拟器的完整容器路径仍需精确生产 Runner；用公开基底拼装一个同名镜像无法证明一致性。现使用隔离目录的 `platform_public_run.py` 支持八个 `{competition, task}` 输入，读取对应平台公开需求、测试和素材哈希；可用 `--package` 运行冻结 ZIP、冻结交付应用、安装/构建/启动 frontend/backend，再用公开 Playwright 测试输出报告，也可用 `--application` 或 `--url` 复用已有应用/服务。该路径复用本项目的包校验、应用合同、进程收尾和结果完整性检查，但不是主办方生产 Runner，结果标记 `platform-public-local`，只输出公开测试通过率，不推算官网成本或综合分。使用方法见隔离目录 `README.md`。

独立 Advisor 建议在缺生产镜像时走这条明确标记的诊断链，不伪造 `run_submission.py`。无模型接线预演先对 Mac 的 Lite/Web Keep `REQ-2.1` 分别调用 Playwright，来源哈希不同、报告中的 helper 路径各自指向正确比赛；随后用确定性 `diagnostic-agent.zip` 完成 ZIP → 需求 → 应用 → build/start → Playwright 闭环，在 Mac 和 WSL 两侧均产生完整 0/1 测试报告（这是故意简单应用的有效失败，不是模型成绩）。WSL 隔离目录位于 `/home/yyh/Development/factory26-official-local`，不会改动两个既有 WSL 本地生成进程。Mac 平台公开输入的八题需求、素材、测试哈希已全部核验；WSL 复制时出现的 AppleDouble `._*` 文件已在隔离副本清理，避免 Playwright 将其当 spec 解析。完整八题真实模型运行尚未启动，不能把无模型 smoke 称为正式本地分数。

完整公开题验收：在 WSL 使用既有已交付的 `pi-team-glm` BookStack 应用，以 Node 20.19.3 和当前 Playwright 1.61.1 跑 `arc-bench-lite--bookstack` 的平台公开输入，`platform_public_run.py` 进程退出 0、测试退出 1，34 项全部发现并执行，7/34 通过，27 项为 10 秒 UI locator 超时；`state.json` 标记 `phase=completed`、`partial=false`，应用 SHA256 为 `248e27d6b62e1b398fcc5d73a0b5240be173a23f828154ce43c4062bab2d81ab`。原始证据位于 WSL `/home/yyh/Development/factory26-official-local/runs/glm-lite-bookstack-full/`。这证明诊断入口能完成整题并保留低分，不证明与官网 Runner 一致；该应用原本来自旧版公开需求，结果不作为同输入官网校准配对。

## 实施前最小预演与验收

1. 获取主办方生产基础 Runner 的不可变镜像 digest，或带 `backend/runner/Dockerfile`、`run_submission.py` 的精确源码版本；核对它与官网日志的版本身份。若只能取得近似镜像，应单独标记 compatibility，不称官方一致。
2. 在计划执行主机的同级目录完成 Docker bind mount smoke，并用固定模拟器、无模型标准 `frontend/backend` fixture 走完安装、构建、ready、Playwright 和结果收集。逐阶段检查退出码与原始日志。
3. 按 `{competition, task}` 收集 Lite 两题及 Web 六题的需求、参考资产和公开测试，保存平台 API 观测时间、逐文件哈希、发现用例身份；与平台 task 列表核对。平台列示数多于公开测试或上游素材引用缺失时，结果标为 platform-public-local；不宣称完整官网评分对齐。
4. 同一冻结 ZIP 先跑一题的容器资格；随后按选定矩阵运行，每题独立 workspace。比较官网同包同题时再核对应用源码哈希、测试身份、容器镜像和服务全程存活，差异保留为未校准而非模型分差。
5. `make test` 验证仓库入口；无模型 fixture 验证独立目录的可执行链。完整模型实验和 Web 六题评分需明确独立实验范围，不由环境预演自动启动。

## 影响与待决门槛

主办方容器路径继续复用官方脚本；新诊断入口只存在于仓库同级隔离目录，不修改当前 Factory 的生成/评测流程或 `third_party/`。用户已明确开工，实施前提交 `b65e95b` 只记录任务包；缺镜像的备选实现与验证见上节。取得镜像身份与可挂载主机路径仍是完整官方容器运行的外部前提。
