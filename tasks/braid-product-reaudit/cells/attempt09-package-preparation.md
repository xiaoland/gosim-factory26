# Attempt 09 普通 base 准备

授权范围：将最新 Factory 与 SVC 技能源码冻结到 WSL attempt-09，使用现有打包入口与已安装 runtime 准备普通 base。不开启 09，不停止或修改 08；最终 Braid 二进制替换、恢复包装及运行由主线程负责。

2026-09-28 07:56 UTC 已创建 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-09/code`，来源是本地 `/Volumes/WorkSSD/Development/factory26` 当前工作树。Factory HEAD 为 `ad0a627532deb792c867d54562ffaf7c28d1573a`，SVC HEAD 为 `b5a0fb8a5a4da778a8892e9893e336b57cfc7837`；两者仅表示祖先，不冒充未提交源码版本。

`source-snapshot.tar.gz` SHA-256 为 `8340d2c084a631e9a29304b7508ad24d746e22b238ea6efc20c3aaf0f673aecf`，563,620 bytes。`source-files.json` 记录 397 个源码文件，SHA-256 为 `ca1774645565ff84307c0a8419d9c9e53e6ae65049eb557638af226044ab65d6`。快照包含 Factory 的 agents、benchmarks、docs、experiments、harness、lab、scripts、submission、variants 和 SVC 的 skills，不包含 runs、凭据环境文件、Git 数据或 Braid 尚在修改的源码。打包输入未沿用旧 Factory 快照。

通过现有 `scripts/package_agent.py --variant pi-braid --runtime <attempt-07 已提取 runtime> --output ../pi-braid-base.zip` 打包；实际命令保存在远端 `build-base.sh`。Python 复用 `attempt-08/venv`。runtime 来自 `attempt-07/generation/runs/pi-braid--hackathon--github-116b6cbc63dc5c/workspace/official-generation/submission/agent/runtime`，不重新安装 runner、npm 或 Playwright；现有 assemble 的 OTLP Python 依赖安装仍执行。

保留现有模型配置；此阶段没有创建或运行新矩阵，4 GiB / 2 CPU 运行约束仍由后续恢复矩阵承接。普通 base 的 runtime 来源记录保留实际旧版本，新 Braid 不能仅靠该普通 base 声称已交付。

当前构建日志为远端 `base-build.log`、`base-timing.txt`；来源记录为 `source-provenance.json`。完成后在本页补包哈希和实际内容检查。

准备过程中的一次可恢复失败：WSL 没有 `/usr/bin/time`，第一次启动在调用 packager 前退出，没有产生包。已在 attempt-09 的 `build-base.sh` 改用 shell 时间戳，保留 `initial-launch-error.txt` 后重新启动。没有修改开发源码。

直接比较 08 和 09 的两个主角色 `settings.json`、`models.json`、`profile.json` 及 `tools/mcporter.json`，七个文件逐字节一致。包内容检查脚本仅读取已生成 ZIP 和冻结源码，检查选定材料与 manifest 哈希；不启动 Harness 或生成应用。

## 完成的普通 base

现有 packager 成功退出 0，实际构建耗时 211 秒。远端 `pi-braid-base.zip` 为 434,903,202 bytes，SHA-256：`d709087d4dbe6d274a14173903c48f95eadd3115013ebe3710b577870c2f0a43`。完整包来源与选定文件哈希写入同目录 `base-provenance.json`，manifest 有 22,871 个文件条目。

直接读取 ZIP 的结果：

- `svc-delegation/SKILL.md` 存在；原 task-packet `references/delegation.md`、browser-checks 及 `._*` / `.DS_Store` / `__MACOSX` 条目均为零。
- 六套 SVC 技能、所有打包角色材料、run.py、main.py、observer 与 OTLP support 的选定文件，对冻结源码及 manifest 的哈希差异均为零。
- run.py 包含短 `/tmp/f26-*` TMPDIR 和显式旧 `work/tmp/pi-subagents-uid-*` 状态根；observer 包含 tool_result 调用反馈；planning 含依赖只阻塞消费方的最新补充。
- agent-browser 技能存在，runtime 仍有 356 个 agent-browser 路径条目及 106 个 Playwright 路径条目；未重新安装这两套 runtime。
- ZIP 没有名为 `.env` 的文件。来源快照复制时也排除了 `.env.*`、Git、node_modules、运行产物及 macOS 元数据；没有读取或复制开发凭据。

这只是准备 base 的物料完整性检查，不证明模型行为、恢复成功、产品验收或新 Braid 修复生效。普通包内 Braid 实际 SHA-256 为 `4074f51ec262294f8acf21f6f9ae31b6457884e8ba1593b16e06a647449c2a00`；仍为复用 runtime，主线程必须在最终 recovery 包更新二进制及其对应来源记录。09 未启动，08 冻输入与运行未改动。

## 09 控制器与恢复编排准备（尚未执行）

2026-09-28 08:05:23 UTC 只读确认：08 `execution.json` 为 `generating`，PID 354115 存活；GitHub `pi-braid--hackathon--github-97914b9e3158cf` 与 Sheet `pi-braid--hackathon--sheet-d478f7dc8ff84f` 的 run.json 均为 `running`、result 为 null。08:06:21 UTC 将阶段截面保存到 09 `orchestration-preparation.json`。这不是后续热停时刻的保证，停机前必须重查。

已在 09 准备以下文件，均未执行：

- `run-experiment.py`：逐字节复用 08 控制器，基于自身 `__file__` 定位 09；SHA-256 `0731e189cc43b7ddbd40ab9b1fca836aedaf0346799ebf72aa079a2aefa0194d`。保留生成全部完成后冻结应用、执行评分的现有逻辑。
- `generation-matrix.json`：仅改 attempt 路径、恢复标签与 agent 包名。标签修为 `09-feedback-delegation-hotfix`（08 原矩阵标签仍是 07）；输入为 `github-agent.zip` / `sheet-agent.zip`。SHA-256 `2916983e83965b9b2c3eb8d2d94680b4d2f046d921b1b56b534a1069beb16052`。
- `monitor-generation.py`：复用 08 已含 cancelled 终态退出的版本；未启动 watcher。
- `package-recovery.sh`：接受两个位置参数：最终 Braid 二进制、对应源码归档。先确认两题 workspace ZIP 已存在、输出 agent ZIP 未存在，再调用现有 `package_completed_recovery.py`，来源 run ID 固定为上述 08 两题，使用 `--continue-generation --refresh-native-materials`。

直接读取矩阵确认：max_parallel=2，两题均 `--memory 4g --cpus 2`，无 attempt-08 残留路径；共享 gateway、requirements、runner、image 等其余输入不变。DS/GLM 路由仍由未改的角色配置及恢复状态保留。09 `execution.json` 不存在，没有启动。

主线程完成热停和冻结后，可在远端 09 目录执行：

```sh
sh package-recovery.sh /absolute/path/to/final-braid /absolute/path/to/final-braid-source.tar.gz
# 复核 recovery-source.json、最终 manifest、包哈希和刷新材料后，才启动：
nohup ./venv/bin/python run-experiment.py > execution.log 2>&1 < /dev/null &
# 两题 run.json 都建立后，才启动既有只读 monitor：
nohup ./venv/bin/python monitor-generation.py > monitor-generation.log 2>&1 < /dev/null &
```

启动前缺项与顺序：

1. 重查 08 状态。若已完成生成并进入 scoring，保留评分，不执行本页两题热恢复。若只有一题已完成，不能机械按本脚本给两题都继续生成；已完成题应保留原结果并调整接续安排。
2. 主线程按既有流程停下尚在生成的来源执行，确认写入者退出后，冻结各自 `workspace/official-generation/template` 为 `github-workspace.zip`、`sheet-workspace.zip`，归档条目须以 `template/` 开头，保留 Git、Braid 数据库、native 状态及符号链接语义。当前没有冻结运行中工作区，也没有新写冻结工具。
3. 最终 Braid 二进制与对应源码由其 owner 提供；此支线未改 braid-build/binary/source。会话边界调查若修改 instructions，先更新 09/code 对应源，再使用 `--refresh-native-materials` 包装；该入口会替换主 instructions、observer、OTLP support 和恢复 main，并刷新 manifest 哈希，无需重装 runtime 或重建普通 base。其它包内文件的变更不能假称由此开关覆盖。
4. 完成恢复包物料检查及新来源记录，确保两个 agent ZIP 与矩阵对应后，再由主线程启动。08 与 09 不并发延续同一冻结状态。

本次只准备编排文件和读取现有状态；未停止 08、未启动 09、未运行测试或模型调用。源码快照记录仍指初始普通 base；后续更新 09/code 的文件须另存实际恢复包刷新哈希，不能覆盖初始来源事实。

08:07:45 UTC 增量同步：主线程完成的两 variant 共五份 `agents/*/instructions.md` 已覆盖到 09/code。内容明确实施前创建并指派 PR、PR 独立成员承担执行、Issue 保留需求方案及协作交接。五文件 SHA-256 均为 `c0aef7bcdad4ced786ad7760eb5f5de8298c16e4dbdd1c49be98063bd0340ffc`，远端逐文件哈希差异为零。远端 `instructions-increment.json` 保存路径、时间、哈希及适用方式；普通 base ZIP 与原始快照哈希保持不变。后续恢复包必须经 `--refresh-native-materials` 纳入这一增量。

## 已授权的实际热恢复

主线程授权此支线在最终 CLI + provider 二进制/源码 ready 后接管 08 停止、完整本地冻结、恢复包装及 09 启动。vision_root_cause 交付最终 `braid-linux-final-v2`，SHA-256 `b9be6bc37d16187ef579380075295092cb10bcef2184d8b63bb0f93d6ed62a04`，11,149,040 bytes；源码 `braid-source-final-v2.tar.gz`，SHA-256 `bfcce2840dcf50706b7f0b958ac6c2432d9df58d95a6f1ab531865ae64df2aab`。两文件均位于 attempt-09；其构建记录为 `braid-build-provenance-final-v2.json`。不采用无 v2 后缀的早期产物。

08:12:42 UTC 的 pre-stop-state.json 再次确认 08 execution=generating、两题 running/result=null。随后通过 08 既有 `python -m lab stop ../generation` 请求停止，操作 ID 为 `5824e51aee46ecdde8c2ab57`。08:13:42 UTC 的 post-stop-state.json 显示控制器及两题均 cancelled，两题生成 PID 354320 / 354319 已消失，runner_exit_code=-15。通过既有 lab reconcile 记录两题资源，最终观察确认原生成容器不存在。中间观察仍见退出过程中的 running/owned，不把该中间状态当停机完成。

停止收据、operation 和最终资源观察均保存在 attempt-09 的 `stop08-*.json`。08 控制器保留非零退出原因并归为 cancelled，没有将人为停止冒充生成失败/完成。

完整私有恢复快照保留 .git、安装依赖、原生历史、权限及符号链接，不删历史、不修改生成应用、不对运行所需文件脱敏或设新凭据阻断。仅跳过不能持久化的特殊文件和 macOS 元数据并记路径；秘密不输出聊天。冻结脚本只用于此次本地 ZIP 操作，不是新框架或测试。

停机后状态锚点 `source-state-anchor.json`：GitHub braid_run_id=`20260928-030347-78b10c07`，21 local_items / 159 events / 49 turns / 25 native JSONL；Sheet braid_run_id=`20260928-025746-66feadac`，26 / 600 / 546 / 91。数据库原始哈希分别为 `cf568b6de624d32a2a38847a2739a93db260653c114d99bfe8cb6cdcd54e1646`、`9cef6073ac278f944f3bf4edff6496c45e285347aab78f41cfde230d296df3cd`，用于判断接续承接，不把新 run 身份混同 Braid 历史身份。

冻结 exit 0：GitHub ZIP 598,421,705 bytes，SHA-256 `f117237072c78c894e49176a079d067808efb8e4875e31309b394706b82ddd50`，47,441 entries / 185 symlinks；Sheet ZIP 1,234,419,780 bytes，SHA-256 `4dbf2130e2b06831909b1075c14a15d4f3822d66964e0f81383396813e8a7b87`，85,770 entries / 320 symlinks。分别于 08:15:12、08:17:48 UTC 完成，详细路径与跳过的非持久文件记录在 `*-workspace-provenance.json`。

恢复包装 exit 0，两题均 `--continue-generation --refresh-native-materials`：

| 包 | bytes | SHA-256 |
| --- | ---: | --- |
| github-agent.zip | 1,034,907,429 | `06691f7fe82c01d657b325398d47ec9d8f3bbc84b7a595e33bf78c1d65f3cddf` |
| sheet-agent.zip | 1,670,905,509 | `b14eaee01633fa8970fa2b7a7e5a10230f5ee18781a099f13e7436129574093b` |

`recovery-package-verification.json` 记录包内二进制、恢复 main、OTLP、observer、两份主 instructions 的实际哈希和 manifest；与 final-v2 / 刷新源码一致。包保留的两个 Braid run ID 与各自 source_run_id 正确，冻结数据库哈希与停机锚点一致。两份包内 instructions 均为最新 `c0aef7bc…` 版本，明确实施先创建并指派 PR，Issue 保留方案依据及协作。

09 于 08:20:01 UTC 启动控制器 PID 490689，180/480 秒只读 monitor PID 490754。两题运行身份分别为 `pi-braid--hackathon--github-88884da4b94a0f`、`pi-braid--hackathon--sheet-984a08e3155e3e`。此处新身份是本轮 lab 执行，恢复的 Braid 历史身份不变。启动时两题 phase=running；还需后续原生活动证明接续，不能仅凭这一状态称成功。

## 实际启动阶段、额度阻塞与停止

09 的材料准备不能计为 Agent 推进。两题 runner 于 08:25:03 UTC 才启动恢复 main（距控制器启动约 5 分钟）；GitHub 包校验至 08:26:38，展开工作区至 08:27:39，刷新材料/本地准备至 08:29:16 才 resuming Braid；Sheet 对应时间为 08:26:34、08:28:09、08:29:55。依据为各题 `workspace/official-generation/execution.debug.log` 的原始 Recovery 行。两题首次 Braid 启动分别耗约 9 分 15 秒 / 9 分 54 秒，不能用此前的 restored DB counts 宣称新调度已发生。

monitor 的本地实验脚本已作最小修正：没有本次 recovery-braid.log 时，数据库统计明确标为 `inherited_snapshot`；本次日志存在后才标 `current_recovery`，同时显示 restore phase 与最近原始 Recovery 时间。只改 attempt-09 产物脚本，不改 Factory 源码。刷新后的 monitor PID 为 492501，保持既有 180/480 秒节奏。

真实新原生活动：Sheet 在 `pi-deepseek-fast-01a0e722-96ad-7902-9d6f-b08ee5c18ae8/2026-09-28T08-30-18-959Z_01a0e722-e54f-7652-9459-90a912dc646f.jsonl` 于 08:30:24.854 产生 assistant/toolUse（bash），后续 08:33 的实际 toolResult 包含检查结果及 git grep。GitHub 08:34:43.288 有新原生响应，但 stopReason=error，不能称成功语义推进。`first-native-activity.json` 的 complete 仅表示两题观察到新原生记录，GitHub 这条明确是失败。

08 的最后 30 分钟也有不同结论。GitHub 于 07:48:56 创建 PR #12，07:49:20 指派、07:49:24 撤销，07:49:40 后这批定向尾部证据没有成功模型/工具推进；根 07:55、08:01、08:08 的 progress check 最终均遇到 provider 错误。Sheet 则有实质 Git 合并：08:03:24 PR #15→`05cffd89…`，08:05:40 PR #17→`6bb81924…`，08:09:48 PR #18→`7f4216ef…`，08:12:44 又创建 PR #19（范围移动写校验）。所以 PR15/17 不是停机时仍未合并；检查仍有重复协调和已关闭 Issue3 处理旧通知，但不能把整段归为没有成果。相关原始小摘要见 `late08-and-fresh09-activity.json`。

两题根 GLM 的原始错误相同：HTTP 429，`余额不足或无可用资源包,请充值`，`Received Model Group=glm-5.3-flash`，`Available Model Group Fallbacks=None`。08 最晚错误分别是 GitHub 08:09:22.748、Sheet 08:11:50.763；09 Sheet 根在 08:32:18/32/37 继续同错。实际 gateway PID 123829 的脱敏路由确认：GLM_BASE_URL host=`open.bigmodel.cn`，DS host=`api.deepseek.com`，不是比赛 proxy；未输出任何密钥。

09 已采样 GLM 原生记录中，GitHub 1 个 session 共 7 个 error、0 个成功；Sheet 6 个 session 共 38 个 error、0 个成功（本次新消息的定向尾部读取）。DS 有真实局部检查活动，但根整合/交付路径外部阻塞，主线程决定停止而非继续周期重试。

09 stop operation=`4280dfe493fe70837b31292f`。08:36:14 UTC `post-stop09-state.json` 确认 execution 和两题均 cancelled，生成 PID 490733 / 490734 消失，两容器 absent，exit=-15。收据、operation、两个最终 run.json 及资源观察均保存在 `stop09-*`；没有删工作区、回滚、重打包或更换模型/key。停止了睡眠 monitor，按既有脚本采集终态后退出；该脚本把 cancelled 行归为 failed 因此终态采集 exit=1，这不是新生成失败。之后没有存活模型生成进程。

`stop09-state-anchor.json` 保存最新 refs、工作项和最后原生记录。GitHub 最后响应为 08:35:37.291 的额度429；Sheet 最后工具记录为 08:35:39.459。GitHub main=`a6afc4ad…`、develop=`afee8497…`；Sheet main=`3ab688f2…`、develop=`7f4216ef…`。下一次接续应采用这个 09 停止点，保留新增原生/协作状态，不退回 08。

用户选择补充 BigModel 额度并保留配方，不能据此假定到账。主线程另授权的一次最小真实 GLM 请求于 08:37:57 UTC 经原 gateway 返回 HTTP 200，用量 15 输入 + 1 输出 token、耗时 1.265 秒；`finish_reason=length` 与 `max_tokens=1` 相符。记录为 `post-stop-glm-availability.json`。只验证该时刻路由可用，不保证未来额度，不自动接续；没有第二次请求。

## 更早恢复点初筛

实际比较的是 09 中的 08 终态 ZIP、08 中的 07 终态 ZIP、07 中的 06 终态 ZIP，避免把 archive 所在 attempt 当源状态身份。`restore-point-facts.json` 保存每个候选的 origin refs、工作项、未合并分支和最后活动。

| 源状态 | GitHub | Sheet |
| --- | --- | --- |
| 06 | 9 open Issue，1 merged PR；develop `012fb041…` | 7 open Issue，3 merged / 1 open PR；develop `61b51ee3…` |
| 07 | 6 open Issue，4 merged / 3 open PR；develop `354b198f…` | 4 open Issue，11 merged / 2 open PR；develop `3e55813b…` |
| 08 | 2 open Issue，10 merged / 1 open / 1 closed PR；develop `afee8497…` | 3 open Issue，18 merged / 1 open PR；develop `7f4216ef…` |

08 GitHub 剩 root Issue1、Issue9、PR12；Sheet 剩 root Issue1、Issue4、Issue5、PR19。回退07会失去 GitHub 六次 PR 合并和 Sheet 七次合并以及之后的检查/补丁分支状态，回退06损失更大。早期快照尚无证据可称“干净正确”；额度问题不随状态回滚解决。Issue7 关闭声明与随后 PR19 新缺陷存在矛盾，是需要澄清的运行状态污染，不能据此删除已合并产品成果；详细判断由主线程及 recovery-point-review 持有，本支线未擅改对象状态或发外部评论。

## 本地直接接续的实际失败与待确认候选

用户确认 BigModel 已补余额后，主线程批准新小 manifest 复用09已展开工作区。`continuation-01` 和 `continuation-02` 均保留独立 lab 记录，未改旧 cancelled 记录；使用 provider-error-v1 二进制 SHA `9eddeac8c66549e78f247ad380ccc04bcd0020cbadfa8911b16e6726e250abf8`、源码 SHA `ef1d463f6d42d9222db4052be1ea70f6e0779228c969301cb44f7570e0bfe758`。直接接续的原有 outer wrapper 仍负责应用发布 receipt，成功后才让既有评分入口消费；没有重新展开工作区。

本地介入交接已实际投递一次：GitHub Issue9 回复#61产生 comment67，回执仅 deepseek-9 queued；Sheet Issue7 回复#199产生 comment211，deepseek-3/7 queued。正文及回执在 `host-diagnostic-comments`，此介入不能计为纯自主收益。投递后 GitHub 草稿中的历史@提及被作者调整，但没有再次投递；实际评论内容以数据库 comment67 为准。

两次直接接续都在模型启动前失败：`git rev-parse HEAD: fatal: detected dubious ownership .../work/application`。01控制器 PID504947，02 PID505851；两者 execution=failed、两题 phase=finished。02 run ID为 GitHub `pi-braid--hackathon--github-87ab8b23798b19`、Sheet `pi-braid--hackathon--sheet-2295267a737e43`。此前只看到 stdout 的 resuming Braid 行就称“已进入且没有错误”，这个判断过早，应以随后原生/错误日志为准。

已确认是接线错误：原runner使用宿主 UID/GID（实际1000:1000），直接Docker缺少 `--user`，默认root与现存仓库所有权不符。第一次声明已补的文本替换没有实际落盘，02冻结输入仍完全相同。证据：01、02两题冻结 launcher SHA 均为 `b5ef8da5a6922d91dfd84e672281b10a82e67110a7ef613d6d29bf0a33b23933`，没有 `--user`、原runner环境变量或工作目录补充；应归为本支线实施/核对失误，不能假称第二次部署已包含修复。

用户新增“部署前逐次确认”后，没有继续部署、修改模型或发新诊断评论。按主线程允许的准备范围，仅落盘未执行的候选：`attempt-09/03-candidate/continue-container.py`，SHA-256 `a4733eedd31c84aab51490ab303b68ccde6e7ea759b87359b95b5fd0a3346b0a`；精确diff为同目录 `launcher.diff`。远端已重新读取第11行及SHA确认，旧冻结输入保持不变。

候选只改Docker argv一行：加入 `--user os.getuid():os.getgid()`，以及原runner已有的 ARC_DEBUG=1、HOME=/tmp/arcbench-home、PIP_TARGET=/tmp/arcbench-agent-deps、PYTHONPATH=/tmp/arcbench-agent-deps、npm_config_cache=/tmp/arcbench-npm-cache。继承同镜像的 WorkingDir=/workspace，不新增 safe.directory、sandbox、网络、模型路由或业务变化；资源仍4g/2CPU。没有运行候选、Docker、模型或测试来验证它，也没有创建或启动03实验。

部署仍须用户确认，并由主线程用新的 manifest 将 launcher 输入指向该确切候选文件、记录哈希后通过既有 `run-experiment.py` 启动；不能直接重跑01/02的冻结输入。另有已观察到的01/02以root写入的native归档/控制结果文件，尚未修改；若它们妨碍后续证据写入，应单列具体文件和最小处理供复核，不悄悄附加到本次参数候选。

## 用户确认后的 continuation-03 准备

用户复核09工作树后明确“可以推进”，本批含 Braid Issue/PR 职责指引归位、variant 重复段落删除和 `svc-sub-agents` 更名；工作记忆方案仍属设计，不进入本次材料。2026-09-28 本轮复用09已展开工作区，未重打包两份完整 ZIP。

新目录为远端 `attempt-09/continuation-03`。实际 launcher 从已复核03候选复制，SHA仍为 `a4733eedd31c84aab51490ab303b68ccde6e7ea759b87359b95b5fd0a3346b0a`，包含 `--user os.getuid():os.getgid()` 和五项原 runner 环境变量，4g/2CPU、网络与 gateway 不变。原控制器与归档交付/评分入口保留；monitor 对本地接续的完成条件读取新 lab result，不把父运行旧 local-result 当作本次结果。

新 entry `continue-in-place.py` SHA为 `3a36d22c96dff4d5a633600999b0cfefe1b893f1b5bd57d8b6810fb32193002f`，只在 offline-resume 前纳入现有 recover_completed 的原生刷新段：备份旧 skills/capabilities/request/materials，调用当前 variant.native_files 重建指令、原生角色、技能 flags 和 bindings，保留原有 profile 身份、model/reasoning 与 models.json 路由。保留旧原生会话、Pi状态和Braid数据库，不重建应用或对象状态。

冻结材料为 `03-candidate/native-increment.tar.gz`，SHA `ae82105c5c9421dc203ba23d484a3f797f5b270dfe1275189a7c62080659f4dd`，81个文件。清单 `native-increment-files.json` 与 `continuation-03/material-deployment.json` 保存源码哈希、父run及真实部署路径。两个活动variant材料均留源增量，但两道题实际仍用pi-braid。两题 submission/agent 的旧 run.py、agents、skills 完整保存在03目录下各自 prior-native-materials；新的六套SVC技能包含svc-sub-agents，旧svc-delegation移出当前消费路径。原ZIP与旧manifest身份不改。

已读取实际权限：两题Pi历史状态目录均为 `work/tmp/pi-subagents-uid-1000`，归yyh所有；原runner用户1000:1000接续保持这一路径。此前关于uid0的摘要不能代表这两份工作区。01/02 root产生的两份native归档目录和两份 `.arc/adapter-agent-result.json` 为755/644，不能由uid1000覆盖；已将这4个对象改名为 `continuation02-root-*` 保留。其它root日志只读留存。没有chown，也没有修改应用/Git所有权。

此截面尚未启动03，等待主线程的 roles-v1 Braid二进制和来源就绪；真实运行与新原生活动证据将在下文补记。没有运行Factory/设施测试或余额探测。

## continuation-03 已启动并确认新原生成功

主线程交付并核对 roles-v1：二进制 `braid-linux-roles-v1` SHA `74739b9d330eb5649d3d3b8624d5da8507a36ba094a2aadf4ba9a8f389f12b38`；源码 `braid-source-roles-v1.tar.gz` SHA `70e867ee3c3d1e19645c6907eb35c446e0b62ad11c7a774e1d9aa2088971c82d`；原构建来源 `braid-build-provenance-roles-v1.json`。启动前重新读取实际launcher第11行与上述四份二进制/源码/脚本哈希，未以候选意图代替冻结字节。

09:20:00.180 UTC 启动 continuation-03 控制器 PID509773；monitor PID510138 使用既有180/480秒节奏。新run为 GitHub `pi-braid--hackathon--github-3d75045c72f1d6`、Sheet `pi-braid--hackathon--sheet-22730f82778f3a`。父工作区仍为09的 GitHub `…-88884da4b94a0f` 和 Sheet `…-984a08e3155e3e`，保留 Braid run ID `20260928-030347-78b10c07` / `20260928-025746-66feadac`。

实际Docker inspect证据确认两容器均 User=1000:1000、Memory=4294967296、NanoCpus=2000000000、WorkingDir=/workspace；binary mount指向独立roles-v1文件。没有重新展开历史工作区；本次从控制器启动至Braid开始约11秒。`deployment-provenance.json` 保存实际挂载、所有增量哈希及原生动作入口。

两题 native 刷新成功。`fresh-material-verification.json` 直接读取本次 request、work/skills 与 capabilities/launcher：两个profile的model/reasoning保持原值，user_instructions和skill flags均为svc-sub-agents，旧svc-delegation目录不在当前消费路径，新skill SHA `86f67f99cc83607a9e26ea5f7cff120152b6b6565ce394948b31784bdd5905bd`。Braid日志记录按当前指令替换provider session；原生历史仍留在原工作区。

首次GLM成功动作分别为 GitHub 09:20:46.498 UTC、Sheet 09:20:46.642 UTC，均为assistant/toolUse；前者读取origin/develop、PR12与comment66，后者读取comment210、origin/develop与PR列表。后续 GitHub 09:21:06.023 assistant/toolUse→09:21:06.211 bash isError=false；Sheet 09:21:09.491 assistant/toolUse→09:21:09.548/09.888 两次bash isError=false。DS同时有新toolUse/toolResult。以上证明新版本真实接续，尚不证明应用完成或最终验收通过。

低成本监控交接：

- 控制目录/manifest：`attempt-09/continuation-03/`、`generation-matrix.json`。
- 最短状态：在该目录读取 `execution.json` 和 `tail -n 1 generation-monitor.jsonl`。monitor每条含本次start cutoff区分的新统计/原生错误；旧debug原始时间仅作历史背景。
- 两题标准运行记录：`generation/runs/<新run>/run.json`、`stdout.log`、`stderr.log`。Braid日志在父09工作区 `.factory26/<保留ID>/continuation-1790587209805388576-braid.log`（GitHub）和 `continuation-1790587209818541166-braid.log`（Sheet）。原生日志仍在对应 `work/native-homes/*/*.jsonl`，本次cutoff为09:20:00.180875 UTC。
- 终态消费：原outer wrapper发布 `.lab-artifacts`；launcher将其复制到新lab run的标准artifact位置。两题完成后既有run-experiment.py自动调用package_arc_replay、hackathon-local矩阵和本地评分，报告落到 `continuation-03/score/analysis/report`。未进入official参赛。

初次接续验证已完成，后续正常生成交给低成本monitor；没有新增模型探测、Factory测试或应用修改，没有提交。
