# I13-2 恢复流程与人工补齐边界

2026-10-02 只读调查。证据来自 2026-10-01 已保存的 I13-2 回执和当前共享入口；没有访问活动容器、读取私有 key、运行模型、调用官网写接口或执行测试。本文件描述调查结论和建议，不构成实施或新实验授权。

## 真实调用链

恢复入口实际是 `scripts/package_completed_recovery.py`，不是 `lab/arc_bench/package_recovery.py`。它把 `submission/recover_completed.py` 写成新包的 `main.py`，保留 variant 的 `run.py` 作为材料生成模块；因此源码版 `variants/pi-braid-i13/main.py → run.main()` 不是恢复包的执行主线。依据：[打包替换入口](../../scripts/package_completed_recovery.py)第 273–275 行、[恢复入口](../../submission/recover_completed.py)第 493–539 行。

1. **选定已停来源并保全。** 官网 journal 模式检查保存的 `PASSED/FAILED/CANCELLED`、`pending` 与原包身份；它不取得新的停止证明。显式 `--source-run-id --base-package --workspace` 模式只记录调用方确认。I13-2 本地另外核对暂停容器 birth/daemon、保全前后文件清单及 SQLite 内容，再停止来源；官网 GitHub 用已有 `FAILED` 终态与 collection 身份。来源 ZIP、Git/Braid/native 的对应关系由这层事实支撑。
2. **必要时派生输入。** 官网遗漏 clone `.git`。GitHub 的临时 `derive.py` 在副本中把 root 重建为有证据的 `base-scaffolding@828d17e`，通过 Braid CLI 追加一次维护 comment，并核对原文件、native 和身份表保留。原 ZIP 不变。
3. **冻结恢复包。** 实际命令由 [freeze.py](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/freeze.py)第 6 行保存：原/派生 workspace、Flash r2 base、明确 Braid binary/source/identity，配合 `--continue-generation --refresh-native-materials --with-official-signal-evidence`。打包器校验 ZIP 成员、manifest、唯一 Braid run、launcher request、需求及材料差异，输出 source/receipt 和完整索引。
4. **隔离实际准备。** 新建独占 Linux 容器，`network=none`、无挂载、uid/gid `501:20`，准备可写的 `/workspace`、`/packages`、`/evidence`，复制冻结输入后只执行一次 `python3 /workspace/submission/agent/main.py /workspace/requirements --output-dir /workspace/template --prepare-only`。
5. **恢复包 `main`。** 校验包/需求 → 解出保全现场并分开旧日志和新 attempt → 读取 DB 的工作树映射 → 缺失 clone `.git` 时从 origin 发布 ref 重建 HEAD/index，使用 `read-tree` 保留工作文件 → 恢复声明的执行位/六目录兼容路径 → 通过 I13 `native_files` 刷新 skills、capabilities 和 retained homes 的指令材料，保留 model 配方与 sessions → 复制并校验 Braid binary → 写 `recovery-preparation.json` 后返回。此分支不启动 telemetry、共享 proxy 或 Braid（[恢复入口](../../submission/recover_completed.py)第 357–627 行）。
6. **读回并接入正式执行。** 临时 prepare 脚本额外比较文件、DB 身份、Git、技能和 runtime，主线启动脚本核对其回执及新 journal，串行 snapshot/create/start。正式环境重新从同一冻结包恢复到新的空目录；已准备目录不能直接再次调用 `main`，第 374–375 行会拒绝已有 Braid run。
7. **原生接续。** 正式分支启动 telemetry/proxy 后执行 `work/bin/braid local braid-request.json --offline-resume`。Braid 取得 runtime lock、核对保留 request/recipe，调用 `Store::prepare_offline_resume` 撤销旧 CLI binding、处理被打断的 materialization/输入状态，记录宿主“旧执行已停”的声明，再进入 session manager/provider 的原 session resume。停止证明归宿主，DB 生命周期与原生接续归 Braid；Factory 不直接修这些生命周期。依据：[恢复调用](../../submission/recover_completed.py)第 628–654 行、[Braid local](../../sources/braid/src/local.rs)第 305–419、607–625 行、[Store](../../sources/braid/src/store/mod.rs)第 3160 行起、[session manager](../../sources/braid/src/group/session_manager.rs)第 155–179 行。

## 人工重复劳动及根因

| 根因 | I13-2 的实际补齐与证据 | 最小修正归属 |
| --- | --- | --- |
| **来源 journal 与目标 base 材料耦合，刷新材料会失去现有来源绑定。** `--journal` 同时要求 base SHA/manifest 等于旧 journal 的包；换成新 I13-2 base 后只能走显式来源模式，其停止事实只写 `caller-confirmed; not independently verified`。Braid 也只接受宿主声明，不能确认旧容器。 | [package_completed_recovery.py](../../scripts/package_completed_recovery.py)第 107–117、178–183、264 行；本轮最终 [package receipt](../../runs/iteration13/i13-2-20261001/flash-root-github-resume-r2-evidence/receipt.json)第 21 行仍是 caller-confirmed。人工另造 [pre-stop-readback.json](../../runs/iteration13/i13-2-20261001/preservation/pre-stop-readback.json) 与 [old-execution-stop.json](../../runs/iteration13/i13-2-20261001/preservation/old-execution-stop.json)，两原容器最终 `Running=false, Pid=0, ExitCode=143, OOMKilled=false`。 | 分开验证来源 journal/原包和本次目标 base，显式记录获授权材料变更；本地来源绑定已有停止回执。保存身份与 hash，不让 `prepare-only` 承担停止、收费启动或“完整检查点认证”。 |
| **平台丢失 `.git`，DB worktree branch 是登记事实，不一定是最后 checkout。** 当前自动修复按 `local_branch`，失败后才退回 `head_ref`，不验证它代表最后实际 HEAD。 | [recover_completed.py](../../submission/recover_completed.py)第 440、455–477 行。GitHub root 的 [重建回执](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/root-git-reconstruction.json)第 2–16 行显示实际证据选择 `base-scaffolding@828d17e`，DB 却仍为 `main`。人工用八文件 tree 与原 native 成功 branch/push 回执交叉确认后派生；临时脚本还出现过 [HEAD 未绑定错误](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/derive-initial-head-error.txt)及 [NameError](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/finish-derive-initial-name-error.txt)。 | 恢复入口接受显式、逐 clone 的已确认 Git 重建依据，统一执行 `init/fetch/update-ref/read-tree` 并读回。证据选择仍须判断；不能让程序猜 staging、未发布历史或 merge 状态。更完整的源快照优先于事后重建。 |
| **隔离 prepare 的实际 Linux 前置未被共享入口拥有。** `--prepare-only` 是包内动作，不负责容器、UID、工作目录与输入传输。 | 首次 Sheet 在进入 `main.py` 前因 `/workspace` 为 root 所有失败：[permission receipt](../../runs/iteration13/i13-2-20261001/recovery-prepare/sheet-prerequisite-permission-failure/receipt.json)第 9–11 行。后续 GitHub 人工准备三目录 ownership=501:20，[目录回执](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/container-directory-preparation.json)。既有 [Workspace.send](../../lab/arc_bench/docker_workspace.py)第 213–221 行已处理远端 `docker cp` 后的 UID/GID 和传输校验。 | 复用现有 Docker endpoint/ownership/传输边界，给真实 prepare 一个宿主操作入口。只管理本次独占容器及派生目录，不复用活动生成卷或 Console。 |
| **包内 prepare 回执不足以直接支撑启动决定。** 原生回执主要记录模型未启动及 launcher environment；完整保留性、材料一致性和来源绑定由每题脚本重复计算。 | [recover_completed.py](../../submission/recover_completed.py)第 615–625 行；约 300 行 [prepare-operation.py](../../runs/iteration13/i13-2-20261001/hosted-github-recovery/prepare-operation.py)第 113–149、166–290 行自行读 DB/ZIP/native/技能；[launch-hosted-github-r2.py](../../runs/iteration13/i13-2-20261001/launch-hosted-github-r2.py)第 19–30 行再硬编码 `verified_files==786` 和一组布尔条件。另一题必须复制并调整脚本。 | 将 prepare 的独立读回提升为共享操作结果，绑定 source/derived/package/attempt 身份，保留具体差异和错误；启动消费该具体回执，不硬编码本题文件数。不要把一组布尔值扩张为跨版本“可恢复认证”。 |
| **文件准备与真正 resume 是不同阶段。** 准备不调用 Braid，因此不能覆盖 resource admission、provider handshake 或既有 reset 接续。 | [首次接续](../iteration13/i13-2/first-continuation.md)第 22–40 行：准备成功后，资源 `Deferred` 被聚合成 `provider recovery returned an error`，实际 exit1 且没有 Pi 握手。r2 同文件第 64–79 行才有 resume/handshake、保留原 history prefix、读取维护输入及发布 packet 的行为证据。 | 保留“prepare 完成”和“首次接续已观察”两个阶段。r2 资源类型问题已经修复，不应再次造脚本绕过 Braid 准入或调低阈值。 |

材料选择曾有一个已经修复的接口缺陷：历史 `pi-deepseek-fast` 已迁移到 GLM/root-only，按 profile ID 选新 base 的同名 DeepSeek 模板导致 `native material refresh changes pi-deepseek-fast.model`。当前 [refresh_native_materials](../../submission/recover_completed.py)第 99–113 行显式识别该获授权历史身份并选择 GLM 材料，不能把它再列为待修问题，也不能把这条特例扩大成任意模型自动替换。

## 已有自动化应直接复用

现有打包器已覆盖原件独立保存、哈希与成员清单、需求/Braid 身份、显式模式与材料迁移开关、binary/source 区分及出处；包内入口已覆盖受控解包、文件权限/兼容路径、Git index 重建、I13 retained-home 材料更新、模型与 native 历史不变检查、attempt/原始日志隔离、实际 binary SHA、无 key prepare 返回边界，以及正式 Braid 调用与清理归档。这些逻辑应保持唯一，不另写一个恢复引擎。

GitHub r2 的实际 [prepare receipt](../../runs/iteration13/i13-2-20261001/recovery-prepare/hosted-github-r2/receipt.json)记录 exit0、786 个保留文件无差异、35 个原 native 文件保持、六表身份及工作项状态不变、68 个技能文件和 56 个 home 材料匹配。它已能作为提炼共享读回的真实样例；原私有 Git 缺口仍存在。[observations.json](../../runs/iteration13/i13-2-20261001/recovery-prepare/hosted-github-r2/observations.json)同时保留容器停止 exit137、`OOMKilled=false`，不能把 stop 命令 exit0 或模型未运行混为容器主进程 exit0。

## 最小共享接口方向

推荐先把现有“冻包 → 独占容器 prepare → 结果读回”的生产操作提炼到共用入口，继续调用当前打包器和恢复 `main`。先解耦来源 journal/原包与目标 base，分别保存并验证两种身份；输入再带本次实际必需的 source/stop 回执、workspace SHA、binary 身份、显式材料动作、可选已确认的 clone Git 重建依据和目标执行环境。输出只保留事实与原件路径。旧的一次性 `derive.py`、prepare、launch 脚本作为历史证据，不再成为新任务的模板。

正式执行仍使用现有 lab/Competition journal。共享准备结果应能被其启动门槛消费，并区分“允许提交的材料事实”和“当前授权的费用/矩阵”；未确认写入按现有 pending/read-only 恢复，不自动重发。维护 comment 的具体内容属于本次实验输入，使用现有 Braid CLI 一次追加并读回，不建立 Factory 的 DB 写入或调度旁路。

尚须人类或主 Agent 作出的决定是：采用哪个停止时点及可接受的进度损失；证据不足时是否接受 Git staging/reflog/未发布历史缺口；本次模型/材料/费用/题目矩阵以及是否启动新物理执行。这些决定不能由普通 checksum 或 `prepare-only` 推导。已获授权且证据确定的 UID 修正、路径修复和同范围重打包不应反复请求确认。

## 回收限制与无模型验收

失败后的输出回收还有独立缺陷，不能并入“准备成功”掩盖。`Workspace.recover` 先在 helper 的 `/transfer/official-generation` 做完整 inventory；[lab/records.py](../../lab/records.py)第 56–60 行按当前挂载路径解析链接，超出快照就失败。runner 正常返回、runner finally、adapter finally/finish 共三处可能重进 recover（[docker_workspace.py](../../lab/arc_bench/docker_workspace.py)第 309–310、398、416–420 行；[adapter](../../lab/arc_bench/arc_bench_adapter.py)第 528 行）。I13-2 保存的具体错误是两个 `node_modules`/pnpm 路径 `link points outside snapshot`。

原 [transport-finalization.md](../iteration13/i13-2/transport-finalization.md)第 7–18 行当时尚无 readlink 证据；主线本轮新增 [investigation.json](../../runs/experiment-operations/20261002/investigation.json)已确认**保全来源层**的真实链接：Sheet 的 `evidence/node_modules` 原文为 `/workspace/submission/agent/runtime/node_modules`，GitHub pnpm 原文为 `../../../../../../../../../tmp/sqlite-check`，且 [github/link-layout.json](../../runs/iteration13/i13-2-20261001/preservation/github/link-layout.json)当时明确目标不存在。[export-frozen-volumes.py](../../runs/iteration13/i13-2-20261001/preservation/export-frozen-volumes.py)第 6–23 行曾通过字面替换 inventory 为这两项补特例，说明保全与通用回收缺少一致的链接保留契约。主线没有重新读取远端 r1 失败卷，因此不能断言其每个目标仍与来源一致；此所有权/回收边界由主线继续持有。不要为了状态变绿调用现有 cleanup；成功分支会删除卷。

后续实施可用以下真实操作验收，不新增或运行 Factory/Braid 测试、mock、包 smoke、自检入口：

- 在新的无网络、无挂载、无模型 key 的 Linux 容器上，对已保全且已授权使用的真实冻结包执行一次共享 prepare；独立读回容器前提、命令退出码、文件/native 字节、Git HEAD/index/dirty、材料/模型身份与本次实际 Braid SHA。失败保留当前容器和原始错误。
- 用已有 `--version` 或 Pi RPC 的 `get_state/get_messages` 读取启动链和原 session 定位；不发 prompt。该反馈只能证明程序/会话读取，不证明 Braid offline-resume 或模型行为。
- 对共享操作生成的完整回执再由独立只读程序/调用方读取源 ZIP 和结果核对，而非只信同一实现产出的布尔值。来源停止和包关联必须可追溯到外部原始回执。
- 需要改变 Braid 源码时以编译反馈为底线，真正 provider resume、资源等待后接续、维护输入消费与终态交付仅在另行确认的实验范围里验收；本次调查未执行这些动作。

更省事的第一步是只共享 prepare 操作及其读回，不先建立通用恢复编排平台；Git 重建证据选择和收费启动继续走当前明确的任务决定及已有 journal。
