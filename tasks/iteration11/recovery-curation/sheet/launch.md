# I11 Sheet 接续准备

用户已授权从暂停的 I10 Sheet 成果本地、自有 API 接续。原件保持暂停、只读；主线已进一步授权在核对摘剪数据库后直接封包启动；advisor 未证实的问题不再阻塞 Sheet，也不加入未证实的环境优先级补丁。

## 来源与空间

原容器 `f26-continue-a2ce3ac2d41459` 已通过 docker inspect 确认 `paused=true`，未 unpause、停止或修改。原目录：

`/home/yyh/Development/factory26/runs/e20260928-03-check-receipts/generation/runs/pi-braid--hackathon--sheet-3b5e3eeaa3b062/workspace/official-generation/template`

保留 Braid run `20260929-042409-811f18d4`，容器内路径仍为 `/workspace/template`。复制目标：

`/home/yyh/Development/factory26/runs/iteration11/20260930-sheet/source/template`

复制前 WSL 文件系统剩余约 21 GiB。使用 `cp -a --reflink=auto` 保留 Git、原生会话、SQLite/WAL、未提交文件、权限和符号链接；不修改应用。完整原始 tar 已另存于此前 Mac 归档目录，本轮不在 WSL 再复制一份数 GB 原始 tar。完成副本后再评估 ZIP、基础包、实验输入冻结与解压的合计空间，不擅自删除旧运行/归档。

## 待接入材料

- Sheet 摘剪以最新副本事实为准：PR #12 已 MERGED，PR #13 已 OPEN；不套用较早的未完成状态。主线/readable-cli 提供最终 curated SQLite 后，才在此独立副本应用；原暂停现场不动。
- 复用 `20260929-cold-resume/build/braid` 及对应源码 tar，不重装 runtime。
- 基包复用 `20260929-feasibility/base-agent.zip`（WSL 已在 cold-resume/prepared/base-agent.zip 留有副本）。I10→I11 使用 `--continue-generation --refresh-native-materials`。
- refresh 开关只直接替换 collector、observer、顶层 instructions；模型定义、内部角色、run.py 和技能来自基包。advisor 修正若涉及这些载荷，必须先重封相应基包文件与 manifest；不能把 refresh 开关当作任意当前源码刷新。
- advisor 调查与本次接续分开：保留冻结基包中的角色/模型配置，不把初步环境优先级假设注入恢复 main。

## 当前状态

独立复制已成功退出，原 DB/WAL 与摘剪报告提供的原件 SHA 均一致；curated SQLite SHA 为 `0550d510afbc885176de6464f87535da98eb2337f3a7aebf5f6c43c14502f183`，已应用到独立副本。旧副本 DB/WAL/SHM 移入 source/original-sqlite，防止旧 WAL 覆盖新的独立 backup；原暂停容器仍 paused=true。应用记录存于 source/copy-and-curation.json。复制后 WSL 余约 16 GiB。恢复 ZIP 与最终包均已完成，launch.py 已执行；新 run 已建立，但截至 01:06 CST 已创建并实际启动容器 `arcbench-local-cd5c76728316`；17:06:38Z 日志进入恢复包校验，尚待新原生模型响应。


## 冻结与启动身份

恢复 ZIP SHA256 为 `d310877a47d8e9b6d2db48b69689c10ae445b4f7a5f1132ce315f8b0335efcb4`；最终 `prepared/agent.zip` SHA256 为 `144bd53eb8fa74fb7f3392f34d680822589c24a7da86d8b5ff63ad6e656df723`。基包 SHA256 为 `6743f2e686fc00d73084f97622c05fa7d908fa993ca36019526cf061ddaa8d8e`，新版 Braid SHA256 为 `5c802c32e452ebe8c0de9182bfa4a5298c7cabcf1097d1dccf95ae6a031f17eb`。完整身份保留于 WSL `prepared/package-identity.json`、`prepared/workspace-identity.json` 和 `source/copy-and-curation.json`。

新 run 为 `pi-braid-i11--hackathon--sheet-db75cf2c3b82be`，位于 WSL `runs/iteration11/20260930-sheet/generation/runs/`。启动使用单 Sheet、自有供应商 API、4 GiB/2 CPU，沿用 `/workspace/template` 路径。独立后台观察沿用现有 capture.py，Mac 记录在 `runs/iteration11/20260930-sheet/observations/`；按 run 创建时间前 20 分钟每 5 分钟、之后每 8 分钟捕获，终态退出。材料展开时间包含在首段采样时间内，不误记为模型执行时间。

运行器复制 frozen agent 的 runtime 文件阶段，磁盘一度仅余 6.5 GiB。主线明确授权清理本任务已嵌入最终恢复包的 `source/template` 与 `prepared/workspace.zip`；已开始删除以释放重复中间材料。最终 agent.zip、curatedDB、manifest、旧 DB 小归档、原暂停现场及 Mac 原始 tar 均保留。没有删除其它运行材料。

截至 01:09 CST，清理已释放主要空间，WSL 余约 12 GiB；原 I10 两容器仍暂停。恢复进程有持续读取，无恢复错误。


## 首次实际响应与未闭合部分

17:11:45Z 包校验完成并开始恢复工作区；17:14:38Z 刷新原生指令/技能；17:14:45Z 开始 Braid 接续。容器 `arcbench-local-cd5c76728316` 实际运行，非 queued 状态。

Issue #4 新物理会话 `01a0ee2a-6042-7f31-89af-7ecf95c5470a` 已创建，新 Pi 身份 `01a0ee2a-7b6f-762b-a551-14df98f364c9`。原生 JSONL 位于保留 run 的 `work/native-homes/pi-glm-fast-01a0ee2a-6044-7452-9104-c3d68e55e8bf/2026-09-29T17-15-56-655Z_01a0ee2a-7b6f-762b-a551-14df98f364c9.jsonl`。17:16:21.150Z 起有 `glm-5.3-flash` assistant / toolUse，随后多轮 bash；实际动作是读取评论、PR #13 及 origin/main、origin/develop 状态。没有把 token 增长当作完成证据。

root 与 PR #13 尚未恢复成功：最新物理会话分别为 `01a0ee29-a557-77f2-a782-7a66a3bae251`、`01a0ee29-9cdd-7e63-849d-6b7a1cd54f21`，均 `status=failed` 且 `native_session_path=null`。`recovery-braid.log` 17:15:29Z / 17:15:41Z 记录 `Pi new_session RPC failed`，原错 `provider request pi_rpc timed out`，随后 `cannot replace Agent Context` / `session is unavailable`。这是 Pi 会话创建边界失败，不能声称模型已回答或整个接续完成。现场保持运行，未循环重启或直接修改 live DB；后续需主线据此安排有界诊断/恢复。

另观察到已合并 PR #9/#10/#11/#12 和已关闭 Issue #7 也获得了新原生会话，日志同时存在旧 pending reset 与本次 profile refresh reset。首批 deepseek 响应来自这些旧负责人，因此不作为正确未完成起点的证明；这里只报告已观测唤醒，不在没有触发链核实前把它归因于新 offline-resume 候选筛选。

后台 capture 进程 PID 53233 仍运行；05m/10m/15m 快照已成功，发生于材料展开阶段，尚无 native 数据。这些时间以 run 创建计，不代表 Braid 已运行同等时长。后续快照保留新原生与 SQLite 证据；观测目录和 cadence 见上文。


## 当前只读快照：2026-09-30 08:43–08:46 CST

`sheet-db75cf2c3b82be` / 容器 `arcbench-local-cd5c76728316` 仍为 running / Up，但当前 **没有 running turn**。最新原生 assistant 为 Issue #4 的 `2026-09-29T17:32:56.804Z`（北京时间 9 月 30 日 01:32:56），`glm-5.3-flash` 正常 stop、无 errorMessage；此后逾七小时未见新模型响应。本段由当前 run.json、SQLite 只读查询、最新 JSONL 和 Git refs 得出，不沿用 17:16 的初始响应当作当前进展。

初始恢复后确有新增成果：PR #14 已 MERGED，develop 从 `d07dd62` 前进到 `2dc4b9fdeefa52aea8e56f1f0d1284141089bf33`。PR #14 评论 #574 记录候选 `18cfeab` 的 SHA/干净工作树、68 E2E 通过及受 head guard 保护的合并；评论 #576/#577 说明仅 `e2e/range-undo.spec.ts` 增加 16 行等待撤销步骤记录的同步，应用树未改。上述检查数字为已有运行证据，本次没有重跑。

当前仍 OPEN 的是 root Issue #1、Issue #4 和最终整合 PR #13。Issue #4 / glm-4 为 idle，其 B 两项回归工作已有收口记录；root / glm-9 与 PR #13 / deepseek-14 仍 blocked。两条当前 reset 分别为 `01a0ed0d-4310-7952-986e-595b75ce00bc`（17:15:46Z）与 `01a0ed04-e691-7ba2-96e8-c3777dab6774`（17:15:36Z），错误仍 `session is unavailable`，原始恢复日志是 `provider request pi_rpc timed out`。它们自首次恢复后未被新成功会话取代；不能以 Issue #4 和已合并 PR 的响应推断 root/最终整合可执行。

**尚未生成交付**：`local_run.lifecycle=running`、`delivery_commit=null`；PR #13 未合并，main 仍 `2914d2ddf2a9cc5723619fd2cef53f5b21b8c3ac`。最终候选整合门与 main 交付未完成。两个暂停 I10 容器仍保持 paused，本次没有重启、改 live DB、运行测试或修改应用。当前需要有界处理 root/PR #13 会话创建阻塞，而不是继续等待容器自然取得新进展。


## 当前 Pi 超时与最小恢复边界（2026-09-30 08:50 CST，只读）

本次五个现行失败（GitHub root/Issue #10/PR #22，Sheet root/PR #13）原始日志均为 `Pi new_session RPC failed: provider request pi_rpc timed out`。冻结构建源码 `20260929-cold-resume/build/source/braid/src/provider/mod.rs` 的 `REQUEST_TIMEOUT` 是 30 秒；`provider/pi.rs` 在 spawn 子进程后立刻发送 `new_session`，等待响应后才 `get_state` 取得 native identity，之后才注入工作提示。故这是同一 **Pi 本地启动握手边界**，不是模型 API 超时，也不是已知的旧 JSONL header 格式错误。五个最新 `physical/session.json` 均 failed，session/native ID/path 全为空。stderr 没有对应故障细节；不能把 I/O/CPU 压力推断为已证根因，也不能断言延长等待必然修复。

此前 GitHub root 冷恢复成功说明同一现有身份less恢复路径可重建 Pi 并收到模型响应，但不保证后续重建不再超时。当前故障发生在该成功之后，不能沿用首次成功结论。最小方案应先修正恢复选择的具体遗漏，再在完整保留现场、确认旧进程停止后做一次冷接续；不刷新全体指令，不重新安装 runtime，不全量重跑任务，也不改 live DB 或建立无限自动重试。


Sheet 的两个现行 reset 通过冻结源码原 SELECT 即可选中，且对应 `physical` 都满足身份less失败证据，因此不需要为 Sheet 另造解封状态或手写数据库。一次受控冷接续可沿用当前 binary 的既有 offline-resume；但为了与 GitHub统一修复及保留完整可回滚现场，可在修正后的同一 binary 下顺序恢复。若再失败，应保留原始超时及新 physical/native 证据后停止重启，另查本地初始化耗时，而不是转为模型/提示词修正。本次未执行恢复。


已准备统一的新 Linux Braid：WSL `runs/iteration11/20260930-completed-turn-resume/build/braid`，SHA256 `3056feb7a599addeb82e0250d6a0cc1e055d9e8e78f0151ca12ea75582605bf4`，release 编译通过。它只补齐 GitHub 同类身份less恢复中“旧 turn 已完成但关联仍在”的筛选，不改变 Sheet 当前已满足的候选条件。构建身份和后续接续命令见 [当前 GitHub 恢复报告](../local-observation.md) 最后一节。下一次 Sheet 必须取本次 `sheet-db75cf2c3b82be` 停止现场并保留 PR #14 成果，不刷新全体原生材料。本轮没有停止或重新启动 Sheet。


## 本轮单次接续部署（2026-09-30）

原 Sheet `db75cf2c3b82be` 已受控停止，完整 Mac 归档 `runs/iteration11/20260930-completed-turn-resume/sheet/source/template.tar` 为 6,446,059,520 bytes，SHA256 `ed9165029deeade35822b231b65e2ebd2a0d005ff5e2025c01e35786b2897e92`；140,549 个成员包含 DB、physical、native 与 Git。因 WSL 空间不足，主线追加授权将该已停止原位 template 迁离 WSL，Mac 完整归档保留；映射与恢复命令见同层 migration-record.json，未碰原 I10。

新恢复包 SHA256 `4a048cc4041dab1621f6a233954a9c0e0954b57f8774bb39b4efe7bd1d160fdb`；工作区 ZIP `3ec25f5955d3c5fc96171f31ad8e0b77735e7e34af4589eb855619fb874a4536`；binary `3056feb7…`，refresh=false。新 run 为 `pi-braid-i11--hackathon--sheet-396538bc0dda96`，WSL `runs/iteration11/20260930-completed-turn-resume/sheet/generation/runs/`，单题、自有 API、4GiB/2CPU。启动只调用一次。

09:39 CST 当前仍为 runner launching，复制展开材料，尚未创建容器或新 Pi 身份。GitHub 同轮已再次握手失败并交主线调查；此处只收尾 Sheet 的单次结果，不修改源码、参数、DB 或执行重试。


### 本次 Sheet 接续成功（09:51 CST）

容器 `arcbench-local-c4e461e6ada9` 于 01:48:07 UTC 开始 Braid。root 原 reset `01a0ed0d-4310-7952-986e-595b75ce00bc` 与 PR #13 原 reset `01a0ed04-e691-7ba2-96e8-c3777dab6774` 均 applied，错误清空。新 root physical `01a0efff-7a6c-7960-9b29-78fdb04de8d5` / native `01a0efff-cf4d-7331-99aa-e020d842cac2`；新 PR #13 physical `01a0efff-7171-7460-9518-66a53c21d3b9` / native `01a0efff-cf4b-7018-9b07-4dae29085d1b`。01:49:22/24 UTC 起分别有 glm-5.3-flash / deepseek-v4-flash assistant toolUse，后续继续调用 bash，无 errorMessage。只证明恢复成功，不代表整合交付完成。

主线明确授权在首次Pi前于 budgeted-pi 加 `export PI_TIMING=1`，实际 01:46:11Z 应用；原文件和哈希已保存，未改变模型/输入/超时。原生 `Startup Timings: main` 为 root 14857ms / PR #13 14875ms；`extensions` 分项为 14069ms / 14002ms，属于分项而非应与main相加的第二套总时长。精确阶段明细保留原日志。

WSL 与 Mac 的 `runs/iteration11/20260930-completed-turn-resume/sheet/evidence/first-resume-success/` 包含只读 DB backup、两物理记录、两新JSONL、完整 recovery-braid.log、startup stdout、Pi进程生命周期记录（实际argv/cwd/环境键，凭据值不采集）及timing包装器改动身份。没有读取RPC管道干扰执行。GitHub日志亦有Subagent result-prime stderr，之前“无stderr”的口头表述不准确；应区分没有独立逐帧RPC文件与已有stderr转发。

主线已授权在长期修复binary完成后复用既有 continue-in-place.py 原位顺序部署，不再重复压缩/解压整份现场；本节截止尚未执行下一轮部署，当前Sheet仍继续运行。


2026-09-30 10:03 CST更新：Sheet成功恢复后保持当前3056feb7二进制运行，不为对齐GitHub新版本而重启。持久observer watcher PID1698834；首次输出正确指向本run实际braid.sqlite3，1 active turn、21 pending、无blocked owner。输出在WSL `runs/iteration11/runtime-stalls/watches/sheet/watch.jsonl`，stderr为空，exit-code待watch结束写入。此为运行健康快照，不代表最终应用交付。
