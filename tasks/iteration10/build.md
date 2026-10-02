# 当前构建：2026-09-29

用户已明确“开始实验”。独立build-source已同步Factory `a243cbd`、Braid `1fabd11`与七个SVC技能（SVC `0cf1406`）。
调用现有`package_agent.py --variant pi-braid --output ../agent.zip`完整构建，不复用旧runtime目录。
Braid release构建已完成（3m36s），四份原生补丁已在Linux镜像中应用；随后进行浏览器依赖安装及打包。
本次日志为远端实验根`package.log`；源码身份为`source-record.json`；完成后的制品身份为`frozen-package.json`。
网关使用独立`gateway/`和端口4020，已确认健康；实际服务域名为open.bigmodel.cn、api.deepseek.com、api.moonshot.cn，不使用比赛额度。
`launch-generation.py`仅负责等待既有构建结束、核对ZIP源码身份，然后生成requirements-only两题矩阵并以每题4GiB/2CPU启动。
源脚本保存在本机`runs/iteration10/start-20260929/`，同步至远端实验根；没有新增通用设施。

以下为此前预热历史，不代表当前制品。

当前增量：FF1 observer按父身份恢复、PBB service退出不自动续轮均已完成；下文 c58d66/b9252c 是先前预热材料历史记录，不能代表最新补丁。最新补丁与生命周期证据见 [writer-followup](cells/writer-followup.md)。统一包尚未重建。

本页是既有构建/预热记录，不代表当前完整制品；是否构建或启动只依据[packet](packet.md)与[实验计划](experiments.md)。

# 迭代 10 WSL 构建输入与 runtime 预热

当前远端 build-source 仍是输入审计新增修复前的副本。完成本轮审查落地后须重新同步 variant、技能与 Braid 源码，再冻结团队制品；下列先前同步摘要不能证明它包含后加修复。已有 Docker 缓存可复用，但当前依赖变化仍需重建相应层。
2026-09-29新增pnpm 10.34.5和portless 0.15.6，npm锁和runtime命令入口已更新，因此旧预热镜像缺少这两个工具，不能作为当前完整runtime。后续构建复用缓存并更新依赖层；未启动两题。

构建输入位于 `/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/build-source`，是新建的独立目录；WSL 主 checkout 未覆盖。远端没有 `rsync`，故从 Mac 项目根目录以 `tar -chf -`（`-h` 解引用 skill 链接）通过 SSH 管道解包：

```sh
tar -chf - --exclude='node_modules' --exclude='__pycache__' --exclude='.git' --exclude='runs' --exclude='.venv' --exclude='*.pyc' --exclude='.DS_Store' \
  scripts lab submission harness/npm harness/skills variants/pi-braid \
  sources/svc/cli/pyproject.toml sources/svc/cli/README.md sources/svc/cli/pdm_build.py \
  sources/svc/cli/src sources/svc/skills \
| ssh wsl.win-ws.localhost 'tar -xf - -C /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/build-source'
```

只同步了打包和运行所需的当前源码，未同步 `sources/braid`、任何 `models.env`、密钥、旧 runs、npm node_modules、Corpus 或设施测试。同步包含的 `sources/svc/cli` 是多余的开发侧材料，不参与当前打包；本轮仅分发物化的 SVC Skills，不需要安装 SVC CLI。构建输入约 4.8 MiB；核对了 npm lock、PBB patch、runtime.py、Dockerfile、pi-braid run.py、成员文件、SVC pyproject 与物化技能文件的双端 SHA-256，均相同。WSL `harness/skills` 中没有符号链接。

另外按主线控制入口单独同步 `tasks/iteration10/scripts/monitor-generation.py` 到 build-source 的相同相对路径；双端 SHA-256 均为 `68eeccf9d798cae57cc28678d07af64c59275ade75abc7a4c67ed6664c01c16c`。未修改脚本，也未启动监控或实验。

PBB 补丁最终冻结为 `harness/npm/patches/pi-background-bash-1.0.5.patch`，SHA-256 `c58d66c3e1ba16194975a91eac4d12a86baba7875e44ecce5e436afb8df31b8f`。中途 `b0e14c…` 曾增加「主 Pi 有 subagent_wait 时跳过 PBB 自有等待」条件；该条件会在原生 auto-drain 达 30 分钟上限时让尚未结束的有限 PBB 作业失去最后的等待保障，已撤销。最终补丁在原始 PBB 1.0.5 上精确应用后的文件 SHA-256 为 `b9252c1b7f38c0bfb08121cb71449e55b83b2541584534e6bb2864b1f21186c1`，并用锁定 Pi 0.85.1 RPC 重跑了仅 PBB 的 child 与 pi-subagents+PBB 的主会话加载：`get_state` 成功、退出码零、无扩展错误。后台进程结束和 follow-up 时序尚未用模型回合验证。

WSL 构建上下文按 `scripts/runtime.py linux` 的实际布局，在 build-source 根复制了 `submission/Dockerfile` 为 `Dockerfile`、`submission/build.py` 为 `build.py`。可复用的 runtime 预热命令是：

```sh
cd /home/yyh/Development/factory26/runs/e20260928-03-check-receipts/build-source
DOCKER_BUILDKIT=1 docker build --progress=plain --platform linux/amd64 --target runtime \
  --build-arg BACKEND=pi -t factory26-iteration10-runtime-preheat:20260928 . \
  > ../runtime-preheat.log 2>&1
```

预热只建 Docker `runtime` target，没有 Braid Rust、没有导出重复 runtime 目录、没有启动模型或两题实验。第一次预热开始时输入仍为中途 `b0e14c…`，成功得到镜像 `sha256:deb49e4a5773ac94a04544d922d82af1c39bf80bfffdc31b4cb89275a78de289`，日志为 `../runtime-preheat.log`；它不是最终交付。构建输入中的 patch 随后替换为最终 `c58d66c…`，同一命令重建成功，最终日志为 `../runtime-preheat-final.log`，镜像 `factory26-iteration10-runtime-preheat:20260928` 的 ID 为 `sha256:911901ffc735ab9e2f6b3271674bf9e79028ad31afe4e955b1a1468d1f70cb52`。从该镜像内直接核得 PBB 1.0.5 源文件 SHA-256 `b9252c1b7f38c0bfb08121cb71449e55b83b2541584534e6bb2864b1f21186c1`，与最终补丁结果一致，且镜像没有 Braid 可执行文件。

主线后续把已收尾的 Braid Rust 源码单独同步为 `build-source/sources/braid`，再构建完整 `team` target 并导出唯一 Linux runtime；随后核对物化 SVC Skills 与制品摘要，最终实验仍须等用户要求的启动前完整汇报。
