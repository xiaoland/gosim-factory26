# 赛后清理

状态：2026-10-09 已完成赛后深度清理。比赛期本地执行者与自动化已停止或暂停，Docker 资产清零，旧 ARC-Bench snapshot 和两个赛外旧运行目录已按保留窗口清理；保留近期包、权威回执、报告、源码和业务输入。随后用户授权将全部本地成果整理到远端 main，已随 `6edb597a` 发布；发布过程见[记录](../github-publication/packet.md)。

## 目标与边界

在不丢失比赛结果、运行证据、业务数据和未归属开发改动的前提下，结束比赛期运行与自动化，归位持续有用的项目知识，关闭已完成任务，并释放确认无复用价值的本地与远端空间。

用户原话：“比赛已经结束 ，现在我们来做清理”。这授权开展清理调查、任务包整理和后续明确属于赛后收口的非破坏性修改；批量删除运行数据、停止仍存活的执行者、撤销工作区改动、提交或推送仍须先给出具体对象与影响，按项目既有授权和破坏性操作规则处理。

## 当前事实

- 清理开始时工作区有大量源码、文档、variant 与任务修改；随后已按用户的成果发布授权整理提交，不能把这一历史状态当作当前未提交清单。
- `tasks/hackathon-evolution/packet.md`、`tasks/finals-experiment-loop/packet.md` 及比赛运行目录保存决赛材料、运行和验收状态，是本次清理的主要证据入口。
- Mac 侧任何保留、归档、临时和控制产物仍必须位于 WorkSSD。
- 开发 SVC 状态健康；本任务不新增测试，验证以 Git 状态、运行/自动化终态、文档入口和文件清单读回为准。

## 完成标准

1. 所有比赛期执行者、监控、续办和外部运行都有明确终态；需要停止的对象有停止回执，不能停止的对象有风险说明。
2. 官网结果、最终采用提交、应用包、业务数据、运行身份、费用与关键诊断证据有可追溯保留入口。
3. 持续有效的产品、技术和运行知识归入权威文档；赛事“当前阶段”陈述改为历史状态；已完成任务入口按保留规则关闭。
4. 仅删除清单中经确认可再生或无保留价值的产物，并记录路径、释放空间和恢复能力。
5. 清理后的 Git 工作区能区分本任务改动与原有改动，不覆盖或误提交其它工作。

## 当前推进

清理批次与保留边界均已执行并读回验证。本任务没有新增脚本或第二套归档机制；后续若要进一步压缩，只针对 2026-10-07 以后仍保留的具体运行包重新决策，不再按目录或文件名推断。

## 运行收口处置记录

2026-10-09 只读核对发现四个 App heartbeat 均已是 `PAUSED`，无需再次控制。Mac 仍有以下后台消费者：

- I15 正式 Sheet `d61987514b284d639abe7301e33012f0` 的 observer/default（PID 21019/21021）；最近已保存平台 `RUNNING` 状态和 441,794,802 字节 workspace 归档。
- I15 正式 GitHub `801c6afc6f074b5aaf50c49411993742` 的 observer/default（PID 80938/80940）；最近已保存平台 `RUNNING` 状态和 271,633,686 字节 workspace 归档。
- 已被官网拒绝、没有平台 run 的 `7868abfa67fa4ce096126ccc768e4bde` 残留 observer（PID 34919）；本地已保存拒绝事实和 pre-execution 现场。
- 已失败且 `result-save.saved=true` 的 `004e8a6d54f94c478bf9ce383d2c7afc` 残留 relay（PID 44445）。
- 已失败且 `result-save.saved=true` 的 `b32cdb6bef5e42cf84de7888cadd53c4` 残留 relay/rsync（PID 23529/1929）；rsync 已持续一天以上，正重复回收 `data/harness` 中的开发依赖，目的目录已有约 3.7 GiB、173,445 个文件，继续执行没有终态保全收益。

处置目的：停止上述本地观察、等待和重复同步，避免继续下载数百 MiB 快照或复制开发环境；不调用平台 stop，不把平台 `RUNNING` 改写为完成，也不删除已保存归档。预期损失是停止后不会自动取得两个正式 run 将来的新平台状态或终态包；现有最新归档和身份保留，可由后续明确操作手工查询。执行前逐个核对 host、boot ID、PID 与出生时间，只向匹配的本地进程发送 TERM，并读回退出状态。

处置结果：上述七个有身份记录的本地进程和一个已确认父子关系与完整命令的 rsync 均收到 TERM，3 秒后进程表无残留。平台 run 未受控制，已有归档与状态文件未删除。赛事入口文档和主要 packet 已加入赛后终态提示，避免后续按旧“当前动作”继续执行。

Docker 只读盘点还发现两个无 Factory run 标签的长期运行容器：`pi-evolution-vv-control-rerun-20261007`（ID `6fb1b606…`）只执行 `sleep infinity`，唯一挂载的同名控制卷继续由 Docker 保留；`serene_jones`（ID `c9670059…`）只执行无对外端口的 `node dist/index.js`，日志停在 `backend listening at http://127.0.0.1:3000`，且没有挂载。两者均无运行身份、终态采集或网络服务消费者证据。赛后收口只停止这两个容器，不删除容器、镜像或卷；预期损失仅是结束其内存态，文件系统和控制卷仍可读回。

实际结果：两个容器均停止，当前 `docker ps` 无运行容器。控制容器保留为 exited、退出码 137，同名卷未删除；`serene_jones` 配置了 Docker 自动移除，停止后容器对象随即被 Docker 删除，未挂载任何卷，镜像 `f26-stage1-offline-v4` 未删除。此前“容器文件系统仍可读回”的预期对该自动移除容器不成立，日志和进程命令已在停止前读回。

空间盘点时 WorkSSD 只余约 4.0 GiB。`runs/build-cache/` 约 1.0 GiB、`runs/runtime-cache/` 约 1.4 GiB，均为明确命名、可由当前构建/运行流程重建的缓存，不持有官网回执、业务数据或冻结应用。为恢复基本工作空间，本轮删除这两个精确目录；不删除约 17 GiB 的 `runs/material-cache/`、约 27 GiB 的 `runs/lab/`、Evolution 运行、core dump、Docker 镜像/卷或任何评分归档。删除后两个 cache 无本地恢复副本，未来使用需重新构建。

删除结果：通用 `rm -rf` 先被执行环境安全门控拒绝且没有产生文件效果；核对两个解析路径均为预期目录后，使用精确路径逐项删除成功。WorkSSD 可用空间从约 4.0 GiB 增至 6.3 GiB。此前盘点遗留的长时间 `du`/`find` 统计进程也已全部终止，不承载运行或证据状态。

## 保留与下一步

第一轮安全收口已完成：四个 App heartbeat 全部暂停，Factory 本地后台消费者和运行中 Docker 容器已清零，赛事导航已归档化，两个纯缓存目录已删除。没有 Git commit 或 push。

必须保留：`runs/hackathon-evolution/inquiry-20261006/` 的官方需求、基线、业务数据和 manifest；I15 冻结应用与用户停止回执；`runs/pi-minimal/competition-20261008-formal-vv/` 的正式上传及 HTTP 409 原件；`runs/reports/`、相关 packet 和 WSL 容器保全材料。

仍需单独决定的深度空间清理包括约 17 GiB `runs/material-cache/`、约 27 GiB 且混有运行记录的 `runs/lab/`、约 15 GiB Evolution 运行、多份 1–2.3 GiB core dump、重复 `agent.zip` / `application.tar.gz` / `project.zip`，以及 Docker exited/created 对象、镜像和卷。不能整体删除这些目录；下一步应先建立“来源—替代件—校验—可恢复性”清单，再删除具体缓存、core dump 或重复包。

用户 2026-10-09 明确授权：“是的，进行深度空间清理；特别是 runs, reports, Docker镜像, 评分归档 等都可以加入审计”。本轮据此继续审计和删除可确认无独立价值、可重建或已有权威替代件的对象；授权覆盖 runs、reports、评分归档、Docker 容器/镜像/卷，但不把目录类别本身当作删除依据。未提交源码、唯一业务数据、唯一比赛输入、当前任务记录和无法确认替代件的运行现场仍保留。

深度批次 1：删除 `runs/material-cache/`。删除前读回约 17 GiB，其中 `artifacts/` 约 11.1 GiB、`components/` 约 6.0 GiB，其余 producer cache、definitions、OTLP 和索引很小。当前源码只把该路径作为 `package_agent.py` 和 I15 builder 的默认内容寻址缓存；没有运行中的 Factory 进程或 Docker 容器消费它。整个目录删除，避免留下引用已消失 payload 的索引壳；未来打包需重新生成或下载材料，不影响已冻结在各 run/agent ZIP 中的制品。

删除后的补充审计纠正：该目录虽然是可重建的内容寻址缓存，但其中多个 artifact 带 `held` retention 记录，消费者名包括 package-material、definition、reader、delivery、hosted-delivery 和 component；因此“只作为普通缓存”的原判断过宽。删除已移除这些历史 retention/readback 链，不能从本机 cache 直接复用旧材料；已冻结 agent ZIP/run 制品未随目录删除。由于 APFS clone/共享块，WorkSSD 实际可用空间只增加约 0.3 GiB，而非表观 17 GiB。没有本地恢复副本；未来需要由源码和上游材料重新生产。

深度批次 2：删除 Tailwind 失败冻结现场的解压副本 `runs/pi-minimal/evolution-20261006/tailwind-github-20261007/frozen/application/`。该副本约 11.75 GiB，含 16,061 个成员和多份 core dump；同目录 `application.tar.gz` 为 372,044,230 字节，实际 SHA256 `b042cd4c83e2a59e54d28ee36c933d2d47bfb9113c2ac2d73c3cc44958684531`，与 `freeze-receipt.json` 完全一致，`application-manifest.json` 和失败终态回执同时保留。删除后仍可从校验过的完整归档恢复原现场，只损失免解压直接浏览能力。

深度批次 3：清理 Docker 的 86 个已停止/Created 容器、全部 BuildKit/buildx 缓存和当前全部可重建镜像。审计时没有运行容器；容器可写层约 2.519 GB、build cache 约 4.127 GB、17 个逻辑镜像约 4.815 GB。删除容器会丢失其 Docker 内部日志、元数据和未挂卷写层；关键终态、冻结应用及评分回执以 WorkSSD `runs/` 为准。镜像和构建缓存未来可重新拉取/构建。本批不删除任何命名卷，约 52 GB 卷待核对唯一数据后另批处理。

深度批次 4：删除容器清零后无任何消费者的全部 28 个 Docker 命名卷，审计总量约 52.02 GB。卷名全部属于 Factory26 的 `exp-*`、`factory26-attempt-*`、`pi-evolution-*`、`pi-manual-*`、`pi-stage*-selftest-*` 或 `pi-vv-*` 实验；没有其它项目卷。关键评分 JSON、冻结应用归档、manifest 和回执保留在 WorkSSD，用户已明确把评分归档及 Docker 资产纳入深度清理。删除后这些历史实验不能从 Docker 卷接续，未来只能使用保留的归档或重新运行。

深度批次 5：删除 I15 两个 Hosted run 的 7 个旧 workspace ZIP，保留各自最新副本。Sheet 的五份 441,794,802 字节 ZIP 均为 SHA256 `d1524dbee1a233eab77ecedbe35b07331074e734614c37a07324f49bcebbeb7e`，保留 `project-1791532457562316000.zip`、删除前四份；GitHub 的四份 271,633,686 字节 ZIP 均为 SHA256 `327841cbefa2ed914d27dd878efad28af47f82f948f96083e6554bafcef4b7fd`，保留 `project-1791531575866883000.zip`、删除前三份。预计释放 2,582,080,266 字节，只损失重复采样时间点，不损失最新 workspace 字节；平台终态仍未确认。

深度批次 6：继续删除同两个 run 中内容不同但已被最新 workspace 覆盖的历史采样 ZIP。Sheet 另删 19:52、20:32、20:54、21:16 四份；GitHub 另删 19:41、20:44、21:05、21:28、次日14:32 五份。每个 run 仍保留最新 ZIP、status、平台身份、原生摘要和日志；删除后不能逐时点重建赛中工作区演化，但主要阶段已经由 I15 packet 和进展摘要记录。

深度批次 7：再删除两份已由完整校验归档覆盖的解压应用。Tailwind `final-frozen/application/` 约 611 MiB，保留 195,267,509 字节归档，SHA256 `70290ac78a4892dfb8c2abad5649c16a69844dabdaa3568f4a7b90aa928ea8ba` 与 freeze receipt 一致；I15 EVO GitHub `final-frozen/application/` 约 1.59 GiB，保留 494,204,104 字节归档，SHA256 `4c1d879b16f4bb75eb1dae639dbb64cb005b7bee923279b5c059ae5ead779506` 与 receipt 一致。两者 manifest 和终态/停止材料保留，损失仅为免解压浏览能力。

`runs/reports/` 审计结论：17 份报告和索引均保留，本轮不删除。它们体积很小且不是逐字节重复；多数承载唯一 run/submission ID、评分身份、首阻断点或设施验收边界，并被 docs/tasks 直接链接。新增 `2026-10-07-hackathon-evolution.md` 是 Evolution 正式与非正式结果的唯一报告化入口。报告已纳入审计不等于应按运行大包处理；删除任一报告前须先把独有结论归位并修复 inbound links。

## 深度清理结果

本轮结束时 Docker 的 images、containers、local volumes、build cache 均为 0；无法从旧 Docker 卷接续任何历史实验。WorkSSD 可用空间由第一轮前约 4.0 GiB 提升到约 25 GiB，主要来自删除三个校验归档已覆盖的解压应用、两个 Hosted run 的历史 workspace ZIP，以及 build/runtime cache；material-cache 表观较大但共享块实际回收很少。保留的最新 Hosted workspace、完整 `application.tar.gz`、manifest、评分/运行回执和报告仍可读回。

当前不再继续按文件名猜测删除 `agent.zip`、`project.zip` 或 `application.tar.gz`：已审计的大包大小普遍不同，缺少证明其完全重复的哈希关系。也不整体删除 `runs/lab/`、`runs/iteration15/` 或 `runs/pi-minimal/evolution-20261006/`，避免把小型唯一回执与大包一起抹除。若以后还需继续压缩，应为具体 run 建立“保留一份 portable/final 包 + 删除展开目录与旧采样”的逐 run 清单。

用户随后明确继续清理，并补充判断：“agent.zip, project.zip 等是从 arc-bench 官网下载的运行时 snapshot，前两天内的下载确实还有价值。此外我还注意到 ../factory-i14-runs, factory26-offical-local 的存在”。本轮据此将下载时间纳入保留规则：按北京时间 2026-10-07 00:00 起的最近两天快照优先保留，更早的 `agent.zip`、`project.zip` 等进入删除候选；唯一评分回执、业务数据和无法由近两天包替代的正式结果仍需单独核对。审计范围扩展到 `/Volumes/WorkSSD/Development/` 下实际存在的 `factory-i14-runs`、`factory26-offical-local` 或相近拼写目录，Mac 产物仍只在 WorkSSD 内处理。

深度批次 8：按上述时间口径删除仓库 `runs/` 中 2026-10-07 00:00 前的 37 个旧 ARC-Bench `agent.zip` snapshot，共 23,119,017,529 字节（约 21.53 GiB）。对象只分布在 `iteration13/`、`iteration14/`、`deadline-20261003/` 和 `pi-minimal-vv/20261003/`；不删除同目录 JSON、日志、评分回执或源码。保守保留同样早于分界的 `runs/pi-minimal/evolution-20261006/preparation/agent.zip`（878,078,533 字节），因为尚未证明 10 月 7 日 rerun 包与它是同一 package identity；所有 10 月 7 日及以后的 `agent.zip`、`project.zip`、portable 包和冻结应用归档均保留。删除后无法精确重放这 37 个当时上传包，但历史身份与结论仍由 packet、report 和小型回执保存。

深度批次 9：删除实际路径 `/Volumes/WorkSSD/Development/factory26-i14-runs/` 整棵目录，表观约 3.0 GiB，全部内容最后修改于 2026-10-02，分界后没有文件，也没有进程消费。其 `reviewer-resume.zip`、`workspace.zip` 和失败/不完整 I14 现场随目录删除，历史文档中的绝对路径将不可读；I14 的结论和当前实现仍由主仓库文档、任务包与源码保存。

深度批次 10：用户所指目录实际拼写为 `/Volumes/WorkSSD/Development/factory26-official-local/`。只删除其中 2026-09-23 至 09-24 的 `runs/`（约 48 GiB）和 `fixtures/`（约 6.8 GiB），它们是旧本地实验现场、prepare/replay 产物与 raw runtime snapshot，分界后无更新且无进程消费。保留 `runner/`、`benchmark/`、`platform-inputs/`、顶层配置与 Git 元数据；主仓库 `lab/arc_bench/targets.json` 仍依赖这个 runner，并且 `runner/local_submit.py` 有未提交修改，不能整目录删除。删除后旧本地回放输入与原地接续能力消失，历史 packet/report 中指向这些运行现场的路径只剩记录用途。

批次 8–10 执行后逐项读回：37 个明确 snapshot 均不存在，Evolution preparation `agent.zip`（878,078,533 字节）和 10 月 7 日 rerun `agent.zip`（879,604,519 字节）仍存在；`factory26-i14-runs/`、`factory26-official-local/runs/`、`factory26-official-local/fixtures/` 均不存在；`factory26-official-local/runner/local_submit.py` 仍存在且保持修改状态。盘点遗留的临时 `.readonly-package-index-20261009.tsv` 和长时间 `find`/`du` 进程已清除。

用户随后明确要求：“`factory26-official-local`也完整删除吧，它似乎是另外一个仓库来着”。删除前读回剩余目录约 275 MiB，确实包含两个独立 Git 仓库：`benchmark/` 位于 ARC-Bench 提交 `ddc7e40e4a715eadfd309a333b0da785192886e7`，远端为 `https://github.com/code-philia/arc-bench.git`，另有未跟踪 `node_modules`；`runner/` 位于提交 `4e62690ef0af48601150f248e1f993a300533357`，远端只指向已不作为持久来源的 `/tmp/factory26-local-simulation-cfbbc287`，并有未提交的 `local_submit.py` 修改。按本次明确授权完整删除 `/Volumes/WorkSSD/Development/factory26-official-local/`，不另建备份；上述 runner 修改和两个仓库的本地 Git 元数据随之不可本机恢复。主仓库仍有 22 个文件保留该绝对路径作为历史或配置记录，其中 `lab/arc_bench/targets.json` 的三个 target 在重新配置 `sdk_source` 前不能再从该路径执行。

删除已执行并读回确认：`/Volumes/WorkSSD/Development/factory26-official-local` 不再存在。剩余目录仅约 275 MiB，受 APFS 计量粒度影响，WorkSSD 仍显示约 95 GiB 可用。未修改主仓库中的历史引用或 ARC target 配置，因为当前没有获知替代 SDK 路径。

最终空间读回为 WorkSSD 931 GiB 总量、832 GiB 已用、95 GiB 可用（90%）；相较最初约 4 GiB 可用，实际增加约 91 GiB，其中本次追加批次相较 25 GiB 增至 95 GiB。Docker 的 images、containers、local volumes、build cache 继续全部为 0。`git diff --check` 未通过，但错误全部位于清理前已有的 npm patch 与一份文档 EOF 空行；本任务没有改这些文件。没有运行 Factory/Braid 测试，也没有 commit 或 push。
