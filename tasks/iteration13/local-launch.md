# I13 本地批次启动回执

2026-10-01。本页记录本轮 WSL 准备、冻结和一次正式启动；实验范围与模型决定归 [experiments.md](experiments.md)，恢复来源归 [官网失败调查](hosted-github-failure.md)。主线确认用户恢复 WSL 四项运行授权后，委派准备三项干净输入与 Flash/GitHub 接续，随后明确 GO：运行已冻结的四项实验，使用 `--listen-host 0.0.0.0 --background`，不重复建 plan 或发起 run。

最终实验目录为 `/home/yyh/factory26/experiments/e20261001-01-local-20261001`，稳定资产为 `/home/yyh/factory26/assets/i13-local-20261001`。15:42:00 CST 正式启动一次，控制器为 `controller-bcfe252ace2f`，PID `3563`，process_start `465881`，boot_id `920ef16b-a457-4983-aa36-11f19693afd6`。主线后台接续入口为 [`active-matrix.json`](../../runs/iteration13/local-20261001/active-matrix.json)。

| run_name | lab run ID | 输入与接续方式 |
| --- | --- | --- |
| `e20261001-01--flash-root--github--g02` | `flash-root--hackathon--github-4afc8896760859` | 官网 `346bc3b51b09` 工作区接续；保留原生材料 |
| `e20261001-01--glm-root--github--g01` | `glm-root--hackathon--github-00bf489759b139` | 原 GLM/K3 冻结包，干净起点 |
| `e20261001-01--flash-root--sheet--g01` | `flash-root--hackathon--sheet-f893bdb3298d69` | 原 Flash/K2.7 Code 冻结包，干净起点 |
| `e20261001-01--glm-root--sheet--g01` | `glm-root--hackathon--sheet-2cf88b952f231c` | 原 GLM/K3 冻结包，干净起点 |

四项均为 ARC 模型通道、requirements-only、本地生成，不注入评测测试。并发 2，GitHub 两项先派发，每容器 4 GiB / 2 CPU；完成后逐题官网 `self_funded` 应用重放仍由主线接续程序负责。

## 实际准备与身份

宿主为 Debian 13.5 / `yyh-ws`，WSL kernel `6.18.33.2-microsoft-standard-WSL2`；12 CPU、约 15.59 GiB RAM、4 GiB swap，Docker Engine `29.8.2`、daemon ID `a76759eb-0145-45f3-be55-ed98b48ef91f`，cgroup v2/systemd。准备时没有容器。没有更改 DNS、重启 WSL 或 Docker，也未触碰旧 Debian 磁盘。

已复用发布的基础镜像 `gyataro/arcbench-runner@sha256:40e003ed470dbd4c120b9019876ba77303d38dc8b34be7f6e313fe0563dd14de`，完成官方 wrapper 构建与入口编译。实际 wrapper ID 为 `sha256:c5d3e2765a92d26093257ffa0363094f4aff502e37d5fa4dc59d1435127b3225`，容器 Python 为 3.12.3。三项干净包的真实 `main.py --prepare-only` 均退出 0；容器 ARC `/models` 返回 HTTP 200，必需精确模型均在本次返回中。模型 GET 不证明生成参数能力。准备完成事件经容器 `172.17.0.1` 路由送入宿主 OTLP，HTTP 200，2961-byte 原始 protobuf 入库摘要与发送摘要一致。

稳定 host-lab Python 为 3.12.14，环境树摘要 `4ed3436ef58534aca8a9522a501204d672eb3a98dc633f4abee68e8592ff6dfb`。最终控制源码独立复制自已核验的 159 项控制资产，树摘要 `4491002807bd420708efd0158b6414fd42dec2f7acbc8756e08b4975c5e07276`；未混入临时 `host_evidence.py`、adapter 或 controller 修改。本地 SIGKILL 归因设施不是本批前置，本批未接入该设施。原控制资产和最终 source 使用独立目录。

| 制品 | SHA256 |
| --- | --- |
| Flash 原包 | `afca9654b10544851885c748060d7d283b2d40b0890363f6acfb9a2dfe677877` |
| GLM 原包 | `6bcabc7d5e48a2f78574ee7651b5fa072a00761d80d8d3194df7f12f08d93404` |
| Flash/GitHub 恢复包，671334789 bytes，0600 | `96302a70c4df8fb65472de9b3e156fb2af944dd6eb3f3701e339c55f6b75bf06` |

恢复包单独传输至 `assets/i13-local-20261001/recovery/`。来源 Braid run 为 `20261001-052115-e45f4278`，工作区 SHA256 为 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd`，`refresh_native_materials=false`。上述来源作为字符串 labels 与独立冻结 `recovery_receipt` 输入写入 plan，Flash/GitHub 没有引用干净原包。

四项冻结输入均 ready；manifest SHA256 为 `d9d8187c9c144f718179dda19d3e76c9030c7a5b67dc472c22624cfd60b1b287`，冻结 controller-source SHA256 为 `c837795d4e160f36761623c3de16bab577688b6c8c1dbed7c9eea803b2552149`。最终容量预检可用 497405001728 bytes，高于 2 并发所需 146028888064 bytes；剩余 inode 33363878，高于保留线 3355443。预算沿用每 run 24 GiB workspace / 4 GiB telemetry / 8 GiB scratch、52 GiB host reserve、12 GiB build。承载 D: 的 WSL 9p 观测可用 1046444118016 bytes。运行仍使用已冻结的容量保护。

## 启动结果与恢复阻塞

初始两个真实容器分别为 Flash/GitHub `e3ccda4ed279c60465717e379a3094afe4d37e7bb40aea6f8e013933f459dad4` 与 GLM/GitHub `bd7cc655b8163762428c4764962ac809d2980adf9f9fad1a13e603363f9a385b`；实际 memory 为 4294967296 bytes、NanoCpus 为 2000000000，bind mount 对应各自精确 workspace。

15:44:04 CST Flash/GitHub 的 `braid local ... --offline-resume` 返回 `blocked`：`issue:pi-deepseek-fast`、`issue:pi-glm-fast`、`pr:pi-deepseek-fast`、`pr:pi-glm-fast` 四条会话均为 `session is unavailable`，并保留 `retained state can resume`。15:44:08 恢复入口因该命令 exit 1 抛出 `CalledProcessError`；本次失败没有 SIGKILL。原始恢复日志与旧官网 `braid.log` 分别保留，不能把恢复包内旧 SIGKILL 日志当作本次退出原因。Meter baseline 另有宿主 `Temporary failure in name resolution`，它不是本次 Braid 退出原因。

主线已明确要求保全失败现场，不自动重试、不为 Console 恢复容器、不停止整批；Flash 接续待主线修复与明确 GO。15:45 启动读回确认 GLM/GitHub 根 Issue 为 OPEN，Braid `20261001-074336-af6f78cd`、原生根会话 `01a0f66b-8bef-77c7-883a-8adb41c2532a` 已完成 Pi startup handshake。控制器随后按原配方派发 Flash/Sheet，Braid `20261001-074506-6e7af22b` 根 Issue 为 OPEN；GLM/Sheet当时仍 queued。这些是启动反馈，不是完整生成或评分结果。

原始回执归 [`preparation/`](../../runs/iteration13/local-20261001/preparation/)，包括宿主身份、wrapper 构建、真实 prepare-only、ARC 响应、OTLP 交付、recipe/manifest、初始与后续容器读回，以及 `flash-github-recovery-error.log` 和 `flash-github-recovery-braid.log`。失败 run 原目录原样保留，恢复状态、Git、原生会话与日志另封存至远端 `preparation/failed-flash-github/runtime-evidence.tar.gz`，266006235 bytes、0600、SHA256 `eae5dcb74312935f13746b4e64505661808afa20ac650e57d287bc1190b404d8`，其完成回执归 `failure-preservation.stdout.log`。同名本地归档已回传并独立重算摘要一致，见 `failed-flash-github/receipt.json`。后续监控、恢复修复、应用重放与最终结果由主线负责；本次未运行 Factory/Braid 测试或 smoke，未改 Harness 冻结包，仅按主线指示提交本页收据，没有 push。
