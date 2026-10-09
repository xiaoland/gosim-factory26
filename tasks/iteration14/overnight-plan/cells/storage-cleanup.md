# Factory26 存储清理回执

时间：2026-10-02（Asia/Shanghai）。用户授权范围是：保留 I13-2 唯一完整评分、应用、冻结 package/requirements/source 和必要复现证据；删除更早及不完整运行（含 paused I14）。随后用户明确要求 Factory26 产物不得留在 WorkSSD 之外。本次没有恢复、prepare、模型请求、评分或源码修改。

## 最终保留索引

- `runs/iteration13/i13-2-20261001/`：已收缩为正向保留集。Sheet 完整评分原始记录为 `hosted-sheet-r2/monitor/20261001T174303.462955Z/f16834f58674/status.json`，其中 `score: 74.0`、`passed_count: 74`；同目录只保留 `workspace.zip`、collection/provider/liveness/archive-index。
- `hosted-sheet-r2/` 根只保留 `agent.zip`、inputs/state/launch/competition/credential 元数据；`agent.zip` SHA256 为 `7de33f7d23a910ec61e4b639275305cdd05222416ff01f2e757d55e58c1ff316`、563092136 bytes。该 ZIP 已包含完整 runtime/node/braid、构建源码与 identity、恢复脚本/manifest、native homes、Braid DB/WAL、requirements 和 template application；不再保留展开 recovery workspace。
- 另保留 `flash-sheet-score-analysis/` 顶层小型 JSON/文本/requirements 诊断文件与 `launch-hosted-sheet-r2.py`；删除其 application/origin.git 副本。其余根级 runtime、stage、base/resume ZIP、GLM/GitHub/native recovery、monitor/replay 均已删除。
- `runs/iteration13/local-rebuild-20261001/`：已删除。gateway PID `96817/96819` 已精确停止；Sheet74 提交包自带 runtime，不依赖该旧现场。
- Console PID `99106` 已精确停止，端口 8765 已释放；其外置程序根 `/Users/lanzhijiang/.local/share/factory26/exp-console/20261002-current-runs-reading` 已删除。I13-2 必要材料均已在 WorkSSD 回读，不依赖 Console。

## 已完成清理

1. 精确停止并删除 I14 baseline controller/container、dispatcher 及 cleaner/reviewer/e2e 资源；停止前 baseline 均为 paused、`OOM=false`。删除 `runs/iteration14/`，未删除 `tasks/iteration14/`。
2. 删除 `runs/` 下除 `iteration13` 外的历史运行；随后按正向保留集收缩 `i13-2-20261001`，并删除 `iteration13/local-rebuild-20261001`。删除范围包含不完整 GLM/GitHub/recovery/resume/stall/历史 hosted 目录、展开 runtime、构建 stage、重复 ZIP 与旧 gateway 现场。没有使用全局 Docker prune，也未触碰源码、文档、`.secrets`、其它项目或通用 cache。
3. 精确删除旧 I13-2 不完整 Console/container；当前 Docker 列表中已无 I13/I14 容器。先前 3 秒尝试曾超时；随后在同一 endpoint 上用 45 秒有界操作逐项删除，6 个 Factory volume 均已删除，远端 volume 清单为空，未留下删除循环。
4. 删除错误的外置 I14 根 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002`（清理前约 38 GiB），并删除空父目录 `/Users/lanzhijiang/.codex/factory26-i14-runs`。清理前已核对无 writer；其中的 I14 cleaner/reviewer/e2e 证据均属不完整运行，无 I13-2 唯一依赖。
5. 删除旧的外置 Console 快照及当前 `20261002-current-runs-reading`；删除 Factory 专属 `/Users/lanzhijiang/.cache/factory26`（约 4 GiB）及 `/Users/lanzhijiang/.local/share/factory26`。将 `~/.config/factory26` 的本项目配置、lock、运行 receipt 和凭据文件按原权限迁到 WorkSSD `.secrets/legacy-home-config/` 后，删除 home 外副本；未删除 `~/.codex` 通用内容或凭据。

## Docker 与磁盘边界

当前 Docker context 是 `development-1`，endpoint 为 `ssh://wsl.win-ws.localhost`；远端 `/` 为 125G、最后核对可用 102GiB，`DockerRootDir=/var/lib/docker`。这是远端 WSL 磁盘；本次未迁移全局 VM，也未删除其它项目资源。6 个 Factory volume 已全部删除，Factory 容器清单为空。三份 Factory 自建镜像也已按 advisor 的依赖核对删除：两份 Braid 镜像的 source/build receipt 已在 WorkSSD，第三份 `official-local-runner` 只对应不属于完整 Sheet 74 launch 链的本地 wrapper；完整 Sheet 使用的是官网 Controller snapshot/create/start。导出曾单次运行至约 1.8GiB 后中止，partial tar 已删除。未执行 buildcache 或公共 layer prune。

## 终态核对

- WorkSSD：`931GiB` 总量，约 `268GiB` 已用，约 `658GiB` 可用（29%）；由初始约 `1.2GiB` 可用提升至约 `658GiB`。System/Data 卷约 `55GiB` 可用。
- 当前本机 Factory writer：无；gateway/Console 均已停止，无 I14 writer、paused I14 container 或 I13-2 生成进程。`runs/iteration13` 当前仅有 `i13-2-20261001`，其完整证据仍可读；WorkSSD 可用约 `658GiB`，System/Data 卷约 `55GiB` 可用。
- WorkSSD 外部不再有已核实的 Factory 专属目录、volume、container 或自建镜像；`~/.config/factory26` 的生成配置也已迁回 WorkSSD 私有目录并删除 home 副本。公共 Docker base image、全局 layer/buildcache 未触碰。I13-2 完整成果所需证据入口均已在 WorkSSD 回读。
