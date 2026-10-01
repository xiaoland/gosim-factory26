# 官网工作区自动导出与恢复准备

2026-10-01，用户要求“一条脚本自动导出官网工作区、校验原 ZIP、组恢复包并处理权限”，避免每次手工组合重复排查。本任务接续 `scripts/package_completed_recovery.py` 与 `submission/recover_completed.py`，初始授权包含对应文档、真实原件组包、隔离 Linux 容器中的无模型原生启动验证，以及仅纳入本任务文件的 commit；初始阶段不启动模型或官网 POST。后续新增的兼容迁移、官网练习启动授权和实际结果见下文，活动 WSL 原包持续保留。

问题来自 I13 Flash/GitHub 官网 run `346bc3b51b09` 的终态 ZIP：27768 个文件均为 `0600`，其中 Pi/binding launcher 无法执行；原生配置引用 `/workspace/submission/runtime`，本地 wrapper 实际部署为 `/workspace/submission/agent/runtime`。失败调查及检查点限制见 [原 run 报告](../iteration13/hosted-github-failure.md)。

## 当前实现

打包命令以 hosted journal 为输入，发现 task/run 和冻结 `agent.zip`，核对 `inputs.json` 与 `state.json` 的 SHA256 和终态，再检查包 manifest 与每个实际成员。默认通过已登录 Playground Cookie 只读下载官方 template bundle，保留原始 HTTP 响应、时间、run 身份、CRC/SHA256 索引。`--workspace` 支持复制已保全原件，原路径不改；恢复输出和证据目录不覆盖。

默认二进制直接来自冻结包的 `runtime/bin/braid`；可显式覆盖二进制或提供可选源码 tar，冻结源码身份持续保留。恢复入口保留主线已批准的 `restore_launch_paths`，仅按请求中的声明恢复执行位及 wrapper 的包路径链接。`--prepare-only` 完成载荷和需求核验、现场恢复、Git 重建及执行路径恢复后退出，保留 `recovery-preparation.json`，不触发 Braid/模型或原生归档刷新。

## 验证与交接

真实输入为 `runs/iteration13/hosted-20261001/github`，冻结包 SHA256 `afca9654b10544851885c748060d7d283b2d40b0890363f6acfb9a2dfe677877`。复用的终态原件位于 `runs/iteration13/hosted-20261001/failure-investigation/20261001T070702.797343Z/workspace.zip`，预期 SHA256 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd`。新输出集中在 `runs/iteration13/local-20261001/recovery-automated/`。

本次使用以下一条命令复用原件并组包，无需手工定位 Braid 或准备源码 tar：

```sh
python3 scripts/package_completed_recovery.py \
  --journal runs/iteration13/hosted-20261001/github \
  --workspace runs/iteration13/hosted-20261001/failure-investigation/20261001T070702.797343Z/workspace.zip \
  --workspace-sha256 6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd \
  --output runs/iteration13/local-20261001/recovery-automated/recovery.zip \
  --continue-generation
```

| 原件或产物 | 验证结果 |
| --- | --- |
| 冻结包 | SHA256 与 journal 完全相同，24212 个 ZIP 文件成员的 CRC/SHA256 与 manifest 核验通过。 |
| 原工作区及证据副本 | 277814542 bytes，SHA256 `6e75992bb5146ac61092628d1488cde3b5bf329b5f4ca5ff20e3acc82ab4bbbd`；27768 个成员逐项核验通过，原路径保持不变。 |
| 默认 Braid | 自动从冻结包取出，SHA256 `a78128da72e64fc604d7cd0ccde68ebc69e61d7db48af165e7b53c858e6e83dd`；manifest 的 revision `76747f2db174237501d948c36b5321ad3ffd75ae`、源码 SHA `105e42ad20018531b7e47ce739a8df4f107b457bd1e1bb9f462b817111b8a260` 保留。 |
| 新恢复包 | 671149872 bytes，SHA256 `bcf7aea80c0a44ee2dd204133e0418f598aa613ee0ad1f564d0d094fe2050233`，24214 个成员逐项核验通过；文件当前为 `0600`，后续打包从创建开始即由 `umask(077)` 保证私有权限。 |
| 新鲜官网 GET | 08:09:42–08:12:09 UTC 返回 200，277814542 bytes，容器 SHA256 `4b7cd3755b08751bccafa9681c4f10001473a9b63f05d51c20d2d20f8b7b0e35`；成员路径和内容 SHA 与较早原件完全一致，新增、缺失或内容变化均为 0。 |

本地回执和三个索引见 [recovery-evidence](../../runs/iteration13/local-20261001/recovery-automated/recovery-evidence/receipt.json)，新鲜下载原文和收据见 [download-verification](../../runs/iteration13/local-20261001/recovery-automated/download-verification/download.json)，前后成员对照见 [comparison.json](../../runs/iteration13/local-20261001/recovery-automated/download-verification/comparison.json)。官网重新生成 ZIP 的容器 SHA 不同，未发生成员内容变化；新鲜原件单独保存，没有替换较早原件。

包已 SCP 到 `factory26-i13-wsl:/home/yyh/factory26/recovery-validation-20261001-automated/recovery.zip`，远端 SHA 与本地相同。独立现场使用实际 `/workspace/submission/agent` wrapper 布局，在 `arcbench-local-submit:i13-20261001`、Python 3.12.3、Docker `--network none` 中执行 `--prepare-only`，退出 0。随后按准备收据的环境直接执行原 `budgeted-pi --version` 和两个 binding launcher 的 `--version`，三条命令都退出 0、stdout `0.85.1`、stderr 为空。

实际回执确认四个声明的 launcher 从 `0600` 修复为 `0755`，六个旧包目录链接指向 agent payload；Git 索引按旧入口重建并保留未提交文件。反馈见 [linux-preparation.log](../../runs/iteration13/local-20261001/recovery-automated/linux-preparation.log) 和 [linux-launchers.json](../../runs/iteration13/local-20261001/recovery-automated/linux-launchers.json)。没有执行 Braid local、模型调用或 Factory/Braid 测试套件；只做 Python 编译、真实归档及实际原生工具运行。

2026-10-01 后续用户将本轮 I13 的 Braid 成员配方调整为不分派 DeepSeek、并发上限 4。这里的旧配方包仅作恢复能力验收，不直接投入新 g03；模型配方和正式恢复由主线另行冻结。该早期验收未修改配方、运行中包或旧失败现场；后续配方迁移采用新显式选项和独立包，见下文。

## 恢复边界

自动校验不把 ZIP 宣告为完整检查点。本次来源终态来自已保存 journal，失败调查曾保留 status API 500 的原始响应，本次没有获取新状态，不能把旧终态当本次新观察。无 journal 的老模式只记录调用方确认来源已停止，脚本没有独立证明。平台遗漏 clone 私有 `.git` 的限制保留；应用源码和未提交文件从原件恢复，索引按已发布 origin ref 重建，无法重建未发布私有提交。包的可启动性、原生会话实际 offline resume 和最终评分是不同反馈；早期阶段只完成无模型启动链验证；后续两个官网练习的初始部署获主线明确委派，已完成，持续监控消费者仍由主线持有。

## 本轮兼容迁移与官网练习授权

2026-10-01 后续用户明确本轮移除 DeepSeek Braid 成员并提高并发至 4；旧成员保留历史身份临时使用同 request 的 GLM 执行，DeepSeek 内部 sub-agent、根 Flash、advisor K2.7 Code 保留。这不是永久 GLM-only 策略。显式 `--replace-braid-deepseek-with-glm` 完成上述窄迁移，普通离线 guard 不变。源码快照和二进制 override 的实际新身份独立记录，原冻结身份持续保留。

用户要求官网运行的“非参赛”是关闭“使用比赛额度评测”，使用自己的 ARC API key。主线授权完成接线、真实 prepare-only 与包身份核验后，依次上传、创建并启动 Flash/GitHub 与 Flash/Sheet 官网练习，GitHub 优先且不等待 Sheet；`credential_mode=self_funded`、`allow_competition_credit=false`。比赛须知与用户确认见 [比赛运行说明](../../docs/deployment/competition.md)。不盲目重发未知 POST，不自动收费重试。新增证据位于 `runs/iteration13/hosted-recovery-20261001/`。

统一采集制品由信号与 catalog 两任务提供：binary SHA `a8afac46d2a8268dc3e7e163e673220216caaeee892b6d3af01c743b70144414`，源码文件树 SHA `088d94e5eb89bf8b1332414088fee621e2cf9879ca21f99151a1569f874e361c`，source tar SHA `5c69a5a787789741c18aae5167a47a2a070cca504e0fa75ad972572d98582248`。三个 support 模块按 commit `727c2c0` 实际内容叠加；整个旧过程证据、旧 attempt 和旧结果从当前路径隔离，当前恢复前建立新 UUID。新辅助写入缺权限保留 errno 后继续，主 Braid 的 Popen/wait 记录不改变原异常生命周期。

本地通道恢复另有显式 `--override-native-transport`，官网不启用。实际无模型迁移反馈已覆盖三个保留旧 session（含 sleeping），session ID、历史消息数及哈希前后一致，当前执行模型为 GLM；原始 RPC 回执位于 `runs/iteration13/local-20261001/recovery-model-migration/`。最终统一包的官方布局 prepare-only 与实际平台启动尚需写入本节后续结果。

本轮最终恢复源码提交 `c5f528d`。统一包 GitHub SHA `6ae8b277c367477e29aef3befbe8c57dc5e497290a79463b13b269b342cf5983`（671360810 bytes），Sheet SHA `07c8ae652038a50854dd97b25d02df468d2103fb3bab4ccff8eec73c34d6283a`（633554138 bytes）。两者均在 Linux 实际官网 `/workspace/submission` 布局、断网容器中完成 prepare-only；每包的 budgeted-pi 和两个 binding launcher 均退出 0、版本 0.85.1，复制后的 Braid SHA 正确且实际 `--version` 启动/等待记录完整。Sheet 单层反向路径链接实际通过。原件、逐项索引与 receipt 分别位于 `hosted-recovery-20261001/<题目>-package/recovery-evidence/`；实际运行回执位于该目录的 `linux-operation/`。

最终 GitHub 的三个真实旧 session RPC 仍为相同 session ID、历史消息数及哈希，当前模型均 GLM-5.3-Flash；最终 Sheet 的一个旧 session RPC 同身份、保留原 session 文件内容前缀，190 条历史消息可读、模型 GLM-5.3-Flash。全部只读 get_state/get_messages，无 prompt/模型请求；RPC 的新增 model_change 仅发生在验收副本。

GitHub 官网初始接续已按授权上传、创建并启动：submission `66774c63c885`、run [`377afa346c92`](https://arc-bench.com/runs/377afa346c92)，初始读回 STARTING、submission credential_mode 与 run billing_mode 均 self_funded，journal pending 为 null。实际 ARC key 仅从授权私有 env 注入内存，并确认与私有配置身份相同；回执仅保存一致性布尔值。独立 journal 位于 `hosted-recovery-20261001/github/`，Sheet 同级 journal 的单次上传进行中。

本地运输 opt-in 由另一执行任务在真实接续包中实际验收：4 份 declared template/retained home 的 factory26 URL 与 key 变量指向本地网关，完整 modeldefs、其它 provider 与 8 份 native JSONL 字节哈希保持。反馈见 `runs/iteration13/local-self-funded-20261001/github-prepare-readback.json`；该本地包与官网包分别冻结，官网两包未启用 transport override。

Sheet 也已完成单次上传、创建及 start：submission `5ada036f2340`、run [`691028015e69`](https://arc-bench.com/runs/691028015e69)，随后状态 RUNNING、deploy_agent completed/start_agent running；费用模式回读同为 self_funded、pending 为 null。GitHub 来源与 Sheet 的 controller stop 回读分别保存在原 journal 和 `hosted-recovery-20261001/sheet-source-stop.json`。

GitHub 首次官网现场 GET 200，原 ZIP SHA `7bc50637f8effb09b46fd88507ec39eab435cc11fee00bb9ef298c6dfe791766`，27792 成员逐项 CRC/SHA 通过；新 attempt `0fde190635764f079fc17e043328e7cc`、实际 Braid SHA 正确。`process-evidence` 原件显示 cgroup-v2 可读，2 秒采样已写入 46 次、无 capability 错误；baseline memory.max=2GiB、oom/oom_kill=0，宿主 sender 仍 unavailable。Braid log 明确 PR5 对原 native session 的握手和 compatible resume 成功。证据原件与摘要在 `hosted-recovery-20261001/github-first-workspace/`，这是一份首次运行观察，不能称为终态或完全一致的停止检查点。

两新 journal 已交给既有 `lab.arc_bench.hosted_monitor` 后台程序，PID `58107`，默认仅观察、3 分钟/8 分钟间隔、终态归档后退出；启动回执在 `hosted-recovery-20261001/monitor-start.json`。评分尚未完成，后续状态及语义判断由主线既有监控消费者接续；不要另起重复采集程序或盲目收费重试。

Sheet 首次官网现场 GET 200，ZIP SHA `78c9be45e8a91275a33f716daabfd5617a31e89dea75719d41fe7a9d8a1e1472`，6289 个实际平台导出成员的 CRC/SHA 通过。新 attempt `94058a60b1864ea9809c419cf6e55440`，实际 Braid SHA 正确；cgroup-v2 能力无错误，已完成 76 次 2 秒采样且写入成功。Braid 原始日志确认根 Issue1 与 PR2 都恢复原 session 握手；PR2 历史 profile ID 保留、当前 request 模型为 GLM-5.3-Flash、root-only 排除新指派。证据在 `hosted-recovery-20261001/sheet-first-workspace/`。两条官网 run 均已 RUNNING；本任务完成导出/准备/迁移/初次启动与采集，后续评分和故障归因由既有监控接续，宿主信号 sender 的缺口保留。
