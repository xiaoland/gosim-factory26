# Debian / WSL 可用环境恢复

## 目标与边界

本任务的目标是为 Factory26 后续开发和新实验恢复一个可用、可验证的 WSL 环境。历史 Factory 数据优先使用项目内已经保存的归档；Iteration 12 已经结束，仅作为历史实验保留，不恢复运行，也不以补齐其 runtime、Git objects 或最终时点全量现场作为验收条件。

用户已授权调查、只读核实和本任务 packet 整理。当前没有授权安装新发行版、启动或修复现有 Debian、挂载 VHDX、覆盖或回滚磁盘、复制并注册冷备、修改 WSL/Docker 生命周期配置，也没有授权启动模型或恢复历史运行。

## 当前事实

2026-10-01 本任务通过 Windows SSH 做了以下只读观察；这些结果来自本次工具调用，没有另造原始系统日志：

- Windows 当前账户具有管理员权限。`wsl --list --verbose` 显示 `Debian` 为 WSL2 且已停止，`docker-desktop` 正在运行。Debian 注册项仍指向 `D:\WSLDebian`，默认 UID 为 1000。
- `D:\WSLDebian\ext4.vhdx` 存在，长度为 76,422,316,032 字节，文件前 8 字节可读且为 `vhdxfile`。D: 为 NTFS，卷、分区及对应物理盘当前报告 Healthy/OK，`fsutil dirty query D:` 报告卷非 Dirty。
- `Get-VHD` 解析当前 VHDX 仍返回 `0x80070570`：`The file or directory is corrupted and unreadable`；此前 WSL 启动也在 MountDisk/HCS 层返回同一错误。当前证据只能把故障定位到 Windows 文件/VHDX 解析或其下层，不能据此认定 ext4 内容损坏。近三天有界筛选的 System 事件没有发现 D:/disk/NTFS 相关错误。
- Windows 当前 WSL 版本为 2.7.14.0；本机 `wsl --help` 明确提供带 `--name`、`--location` 和 `--no-launch` 的安装接口，以及 `--import --vhd` 和 `--import-in-place`。
- 扩容前冷备目录 `D:\WSLBackups\Debian-before-512GiB-20260926-2318` 仍存在，其中 `ext4.vhdx` 长度为 257,765,146,624 字节。历史维护记录说明该副本当时与源文件完整 SHA-256 一致且 `Test-VHD` 通过；本次没有重新读取整盘计算哈希，也没有挂载或启动它。

项目归档 [README](../../runs/wsl-retained-20260930/README.md) 纠正了最初“必须保活暂停现场”的假设：Iteration 12 后来被明确终止，WSL 干净关机，当前 VHDX 以 Full 模式从 480.62 GiB 压缩到 71.17 GiB，验证后 Debian 保持停止。项目内已保存约 37 GiB 历史主归档、约 1 GiB I12 当前捕获、约 7 GiB official-local 和约 455 MiB acceptance-workflow。

主线于 2026-10-01 只读核实 I12 捕获中的两份 online-consistent Braid 数据库可打开，9 份 Git bundle 可列出 refs，worktree 映射与 dirty patches 存在；会话 status/physical 材料也存在。该捕获约在 9 月 30 日 19:39，缺标准 native manifest，不能称为最终终止时点或全量备份。主线回执见 [`cleanup-archive-review.json`](../../runs/braid-console-control/20261001-service-start/cleanup-archive-review.json)。这些限制不构成恢复 I12 的理由。

## 决策与方案顺序

首选建立独立的干净 Debian；只有发现后续开发的具体必需材料无法从仓库、声明式依赖和项目归档重建时，才从冷备副本提取该材料。只有明确需要 2026-09-26 之后、项目归档又未覆盖的数据时，才评估现 VHDX 的专项恢复。这个顺序直接围绕“恢复工作能力”验收，避免让一个已结束历史实验扩大恢复范围。

| 路径 | 适用条件与具体做法 | 数据影响与风险 |
| --- | --- | --- |
| **C：新建干净环境（首选）** | 建议以新名称 `Debian-Factory26`、新位置 `D:\WSLDistros\Debian-Factory26` 使用本机支持的 `wsl --install Debian --name ... --location ... --no-launch`。保留旧 `Debian` 注册、当前 VHDX和冷备；不改变默认发行版。首次启动前核对 Windows 生命周期任务不会把新名称纳入旧 Debian 的自动启动规则。启动后只建立 `yyh` 用户、Factory 当前开发入口需要的基础工具和声明式依赖，再从当前源码或明确归档按需迁入材料。凭据独立配置，不复制旧 home、Docker data、服务状态或 runs 全目录。 | 新环境不会继承未声明的个人配置和工具；这正是需要在实际开发入口验收中发现的缺口。安装、首次启动、软件安装和必要文件迁入都需要用户另行授权。I12 不迁入、不启动。 |
| **B：使用冷备副本（有具体缺口时）** | 保持原冷备只读，先复制到新路径并用历史 SHA-256 `274079d50d558cdbca6150880368136fee18c9395168702bda692f98ed9cc333` 和 `Test-VHD` 验证副本。优先在已有干净发行版中把副本以只读、禁止 journal replay 的方式挂载，仅提取已确认缺失的文件；确实需要完整旧环境时，才把**副本**以新名称注册，并在首次启动前制定服务/Docker自动启动控制。 | 副本约 240 GiB，复制与完整哈希读取耗时且占空间。冷备包含 9 月 26 日的旧配置、凭据、服务和任务；注册后启动可能带起旧服务。禁止直接注册或启动唯一冷备原件，也不把它覆盖到当前 Debian。复制、挂载、注册及首次启动分别需要明确授权。 |
| **A：修复当前 VHDX（最后选择）** | 只有归档和冷备都缺少一项明确需要的数据时才进入。先制作并验证当前 VHDX 的独立副本，在副本上区分 NTFS 文件读取、VHDX 元数据和 ext4 三层。`Get-VHD` 已经在 VHDX 解析层失败；微软文档中的 `wsl --mount ... --bare` + `e2fsck` 只有在 VHD 能附加后才适用。 | `Repair-VHD`、`chkdsk /f`、`e2fsck`、覆盖/迁移及任何写修复都可能改变唯一数据或共享宿主卷，必须针对具体证据单独授权，并先有可验证副本。当前不执行这些动作，也不把卷 Healthy/非 Dirty 当作文件完整证明。 |

微软的 [WSL 基本命令](https://learn.microsoft.com/windows/wsl/basic-commands) 明确区分新发行版安装、VHD 导入和原位导入；[磁盘空间与挂载错误说明](https://learn.microsoft.com/windows/wsl/disk-space) 的 ext4 修复流程要求先附加 VHD，并会运行写修复；[WSL FAQ](https://learn.microsoft.com/windows/wsl/faq) 同样提示注销会删除原发行版文件。因此本任务不使用注销旧 Debian 作为新环境准备步骤，也不把 ext4 修复流程套用到当前无法解析的 VHDX。

## 建议实施与验收

若用户批准首选方案，实施分两段：

1. **基础环境**：再次记录旧 Debian、当前 VHDX和冷备身份；核对新名称与目录为空；以 `--no-launch` 安装新发行版；确认旧注册和三个 VHDX目标没有被替换。首次启动只完成用户、基础网络、SSH和包源核对，不安装 Docker、不接入自动启动任务。
2. **Factory 开发能力**：依据当前仓库文档安装实际需要的 Python、Node、Rust、开发 SVC及容器工具；迁入当前源码与必要的非敏感配置。Docker、模型凭据和实验 runtime 按真实新实验需要单独接入；不导入历史容器、运行状态或 I12。

完成条件是新发行版可独立启动和停止，`yyh` 用户、源码、Git及当前开发入口可用，必要依赖能按仓库声明安装，项目归档可按需读取，并且旧 Debian、当前 VHDX、冷备及历史归档身份未变。验证使用实际命令、编译和开发入口反馈；不编写或运行 Factory/Braid/SVC 测试，也不启动模型、benchmark或生成容器。

## 当前下一步

当前方案已完成，所有修复、安装、挂载和迁移动作继续停止。需要用户选择并授权“C：新建独立干净 Debian”的具体实施范围后再动手；B 和 A 仅由实际缺口触发，不能作为默认前置步骤。
