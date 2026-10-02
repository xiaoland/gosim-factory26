# Lite 实验环境准备（2026-09-24）

本文件记录本轮独占产物目录与执行入口；源码已冻结并同步，Linux runtime 与 ZIP 已完成；Keep 生成失败，BookStack 仍在运行。

## 隔离目录与已核实输入

WSL 主机为 `wsl.win-ws.localhost`，本轮独占目录为 `/home/yyh/Development/factory26/runs/braid-usability-lite/20260924`（下文记为 `run_root`）。目录已包含从本机当前版本同步的完整 `scripts/`、`variants/pi-team-mixed/`、`harness/npm/`、六份发布 skill 资源及 `submission/`。这些副本不覆盖 WSL 的旧项目或旧实验。`source-identity.json` 记录副本树、关键脚本、Runner、输入身份文件与既有镜像的 SHA-256；其中 Runner 整树摘要为 `6131026be17be29bddabbd234384974282ebb4c11cc3d60195f0f8607e377f92`。同步时的 variant 树摘要为 `d4645693df4c855dc5feb9b34a99d7c3139f03907ed85903dcb8f1ba02a6049a`。最终 Braid 源码已经由 `scripts/sources.py export/restore` 同步到本轮 `sources/braid`；完整源包在 `braid-source/`，包括 Git bundle、工作区 patch 和新增 migration。上面的 variant 摘要是准备阶段身份；最终冻结身份以 ZIP 内 package-manifest 和 ZIP 摘要为准。

官方本地 Runner 副本在 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner`，Lite 输入在同级 `platform-inputs/arc-bench-lite/{keep,bookstack}`。两题的 `requirements/` 与 `tests/` 均存在；准备阶段没有读取公开测试正文来指导 Agent。Runner 的 `local_submit.py` 支持 `--requirements-dir`，且 `--tests-dir` 为可选参数：生成阶段只传需求目录，评测阶段再传测试目录。已有评测镜像 `arcbench-local-submit:latest` 的 ID 是 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`。Runner 副本没有 `.git`，故仅记录文件身份，不称其有 Git revision。

已复用的 WSL Pi runtime `/home/yyh/Development/factory26-official-local/hackathon-runtime-pi` 包含 Pi、浏览器工具、Chromium 与 Node，但没有 `bin/braid`，不能直接作为最终团队制品。WSL 宿主当前 `cargo`、`rustc` 不在 PATH；虽有 `/home/yyh/.cargo` 缓存，不能据此直接用宿主编译，也不能把可能依赖更新 glibc 的宿主二进制塞进 Bookworm runtime。现有 `submission/Dockerfile` 使用 `rust:1.93-bookworm` 编译 Braid，再把产物复制到 `python:3.12-slim-bookworm` 的 team runtime；`runtime.py linux --braid-source` 正是这条已有构建路径，且 Docker 保有约 5 GB 构建缓存，但特定层命中率未验证。WSL 另有 `/home/yyh/.cache/factory26/runtime-faf60473273ddeed` 和 Playwright 缓存；无需重装 Runner 或浏览器。

同步的六份 skill 仅为发布所需的 `SKILL.md`、引用、资源、脚本与许可材料，总大小约 232 KB。原有 `harness/skills/svc` 链接指向独立源码仓库，本轮已将其发布资源实体化，没有复制 SVC 的 `.git`、虚拟环境或开发文件。

独占目录的 `.private/model.env` 权限为 `0600`。它把原有 `~/.config/factory26/llm.env` 中的 `FACTORY26_API_KEY` 映射为 `FACTORY26_API_KEY` 和 `OPENAI_API_KEY`，并设 `FACTORY26_BASE_URL`、`OPENAI_BASE_URL` 为 `https://api.arc-bench.com/v1`；本文不含密钥。该 URL 来自已封存 GLM run 的 `harness-source/models.json`（`base_url`）和官方 raw-Pi 生成模板的 `.pi/agent/models.json`（`providers.raw.baseUrl`），并非推测。主 Agent 已在 WSL 对官方 `/v1/models` 执行 GET，收到 HTTP 200 且列表包含 `glm-5.3-flash`、`deepseek-v4-flash`、`deepseek-v4-flash-vision-exp`；这只验证模型列表连接，尚不证明采样成功。

## 定稿后执行命令

先把本轮**定稿** Braid 源码放入 `$run_root/sources/braid`，保留可执行 `git rev-parse HEAD` 的 `.git`；不要从旧 WSL 项目取源码。若该工作树含未提交改动，另存实际源码树摘要，不能仅以 HEAD 表示内容。`runtime.py` 需要该 Git 身份，并会用现有 Docker 构建路径生成含 `bin/braid` 的 Linux runtime。

```sh
ssh -o BatchMode=yes wsl.win-ws.localhost
run_root=/home/yyh/Development/factory26/runs/braid-usability-lite/20260924
python3 "$run_root/scripts/runtime.py" linux \
  --output "$run_root/runtime-pi-braid" --backend pi \
  --lock-dir "$run_root/harness/npm" \
  --braid-source "$run_root/sources/braid"
python3 "$run_root/scripts/package_agent.py" \
  --variant pi-team-mixed --runtime "$run_root/runtime-pi-braid" \
  --skills "$run_root/harness/skills" \
  --output "$run_root/pi-team-mixed.zip"
```

同一个冻结 ZIP 用于 Keep 与 BookStack；现有 `arc_matrix.py` 生成两项 job，`local_experiment.py` 驱动并行度 2。`arc_bench_adapter.py --separate-evaluation` 在生成调用中只向 Runner 传 `--requirements-dir`，生成结束后冻结源码摘要，再用同一生成应用和 `--tests-dir` 独立评分。

```sh
run_root=/home/yyh/Development/factory26/runs/braid-usability-lite/20260924
python3 "$run_root/scripts/arc_matrix.py" \
  --variant "pi-team-mixed=$run_root/pi-team-mixed.zip" \
  --case arc-bench-lite/keep --case arc-bench-lite/bookstack \
  --inputs-root /home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/platform-inputs \
  --runner /home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner \
  --image arcbench-local-submit:latest \
  --env-file "$run_root/.private/model.env" \
  --workers 2 --separate-evaluation --container-otlp-host 172.17.0.1 \
  --output "$run_root/lite-matrix.json"
python3 "$run_root/scripts/local_experiment.py" run "$run_root/lite-matrix.json" \
  --runs-root "$run_root/runs" --max-parallel 2 --listen-host 0.0.0.0
```

环境准备是静态核对。Docker 构建能否完成、模型实际采样、容器到 OTLP 接收器的连通性，以及两题生成与评分结果，均须在正式执行时观察。`arc_matrix.py` 会为每项运行复制 ZIP 和输入、保存证据；不能以第一题完成代替整轮 Lite bench 完成。

## 实际构建记录

本机 `cargo build --locked` 成功。WSL 首次 Docker 构建因宿主残留 `credsStore=desktop.exe`、SSH PATH 中不存在 `docker-credential-desktop.exe` 而失败；尚未产生 runtime。
本轮构建以独占空目录 `.docker-build` 作为 `DOCKER_CONFIG` 重试，使用现有 `/var/run/docker.sock`，不修改宿主 Docker 设置。失败原文在 `build.log`，重试输出在 `build-retry.log`。

Docker 重试成功，Linux `cargo build --locked --release` 与 runtime 导出完成，路径为 `runtime-pi-braid/`。随后用现有 `package_agent.py` 打包 `pi-team-mixed.zip`。

## 已启动实验

冻结 ZIP：`pi-team-mixed.zip`，391073531 bytes，SHA-256 `8b7c37b7d3097a0d12e14bb4c66170743d7f9d41e3bd443f227b3726073f6b9d`。
身份记录在远端 `frozen-artifact.json`，矩阵在 `lite-matrix.json`，同一个 ZIP 用于两题。

| Task | Run ID | 分析者 |
| --- | --- | --- |
| Keep | `pi-team-mixed-arc-bench-lite-keep-23563f65f4` | braid_usage_glm |
| BookStack | `pi-team-mixed-arc-bench-lite-bookstack-8a977ba177` | braid_usage_vv |

结果目录为本轮 `runs/<run-id>/`，Controller 的实际进程等待终态，分析者检查间隔至少三分钟。
报告归 `results/keep.md`、`results/bookstack.md`；主 Agent 负责综合和修复设施，不重复逐 run 分析。
