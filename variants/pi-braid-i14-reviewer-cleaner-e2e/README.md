# I14 Reviewer、Cleaner、E2E 组合

本 variant 将三条 I14 原生能力叠加在完整 standalone 自费基线上。独立 reviewer 只接固定候选的验收请求；普通成员通过 `braid assignee list --reviewer` 与 `braid pr review assign` 指派它。每个 Braid 成员的 Pi launcher 均加载 `braid_cleaner`，完整正常响应经 Braid 来源校验后原子维护当前工作项。成员与原生浏览器角色读取独立 e2e 技能，通过 e2e MCP 操作真实浏览器，并保留 agent-browser 的诊断能力。

默认根成员与 reviewer 使用 GLM-5.3-Flash / high；cleaner 与 e2e 使用相同模型。原生 advisor 使用 Kimi-K3 / high，executor、explorer 使用 DeepSeek-V4-Flash-0731 / high，vision、browser-operator 使用 GLM-5.3-Flash / high。私有多供应商 failover、Rust proxy、Braid session 预算保护、资源门控与 pi-subagents 修复均继承底包。

交付方式为 `build.py --base-zip <完整自费 baseline.zip> --output <WorkSSD交付目录>`。底包必须是 SHA256 `e9f7b7d2a7ad88728dcf5c589db552dd1dde1731055d10563d161baf7b8733f5` 的 `runs/deadline-20261003/i14-baseline/agent.zip`；该底包已包含 e2e addon 与技能。不要使用 `agent-official.zip` 或已转换过的 `stage/`。

执行负责人先将完整底包解压到本次独立的 Linux x86_64、CPython 3.12 包目录，再将 `overlay.tar` 解压到相同目录，保留全部继承成员与私有凭据。入口为 `python3 <包目录>/main.py <允许需求目录> --output-dir <本次输出目录> --type web`。如需只准备真实原生材料，在同一命令末尾加入 `--prepare-only`。本 variant 不预置应用，不自行提交官网；4 GiB 容器及运行启动由本轮执行负责人设置。

本地阶段接续通过 `--initial-application <上一阶段冻结应用目录>` 传入只读应用，`--output-dir` 使用本阶段独立空输出目录。入口将输入复制到隔离仓库，并在 Braid 启动前提交初始 Git 快照；源应用保留，最终交付只发布到本阶段输出。Stage 1 不传初始应用。每阶段绑定确切上阶段产物，不能用独立生成的同名阶段应用代替。

Evolution 运行添加 `--evolution`。平台已经向 output 注入基线时，入口默认从该目录复制业务应用到本次独立工作仓库；本地也可通过 `--initial-application` 指定同源完整官方基线。旧 `.factory26`、`process-evidence`、`.factory-e2e` 和 `.arc` 留在基线，不进入新成员工作树，原生会话、浏览器与工具状态重新建立。最终导出逐项更新应用成员，保留 output 中的历史证据及已有业务文件，不清空输出目录。初始文件哈希、初始 Git commit 和最终交付 commit 分别记录；增量任务要求保留既有功能、技术栈、业务数据和未知字段。

运行设施可通过 `TASK_CONTEXT_FILE` 传入独立补充任务文件。入口在模型调用前核对可读性，复制到本次 run，记录来源和 SHA256，并在任务提示中引用该文件；未配置时保持原任务入口。赛事特定的数据准备与增量约定归任务设施，该 variant 不维护 EVO 数据或赛事提示正文。

机制接线在 `run.py:native_files()`、`agents/pi-glm-reviewer/`、`extensions/factory-cleaner.ts` 与 `tools/mcporter.json`。Linux 短路径别名沿用 e2e 的原生清理流程；Mac 的实际写入位于本次 WorkSSD 输出目录。生成结束保留 maintenance 回执与 e2e daemon 清理结果。

当前 sfp7 五路对照使用 `shared-overlay.tar`：在独立空目录解压本组合的完整小材料，将 `local-five/overlays/common/` 中的 `support/`、`.private/`、`arc-runtime.pyz` 复制进去，保留空的 `runtime/` 与 `skills/` 挂载点。安装目录在宿主侧设为容器 UID/GID 1000；私有目录 700、凭据文件 600，然后整体只读挂载到 `/harness`，当前 shared runtime 与 skills 分别只读挂载到 `/harness/runtime`、`/harness/skills`。允许需求只读挂载到 `/requirements`，本次输出可写挂载到 `/output`，以 `python /harness/main.py /requirements --output-dir /output` 启动。组合 run 只在实际模式不符时调整私有文件权限；正确安装后不写只读材料。

同一未完成运行的机械恢复使用 `--resume-run-dir <output/.factory26/确切run> --resume-stopped-receipt <停止收据.json>`，同时沿用原 `--output-dir`、完整需求目录、`MODEL`、`TASK_CONTEXT_FILE` 和 `--evolution` 模式。可以通过 `--braid <独立修复的binary>` 选择已冻结身份的新二进制。入口复用原 application、input、worktrees、native homes、Braid state、预算和 request，保留原 run_id 与 started_at；不再次复制基线、初始化 Git 或创建另一 run。执行实际调用 `braid local <原request> --offline-resume`，Braid 自己完成受支持的状态恢复；入口不写其 SQLite。该参数不保证任意 blocked 状态已可恢复，具体 Braid 缺陷仍须由相应修复二进制处理。

停止收据由执行宿主核实后提供，必须含 `run_id`、64位十六进制旧 `container_id`、`stopped:true`、`owned_execution_stopped:true`、数值 UNIX 秒 `stopped_at`，以及 `container_state:{Running:false,Pid:0,ExitCode:<整数>}`。停止时间必须晚于原启动或上一恢复启动；同一收据不能用于第二次恢复。口头 flag 或仅一个 stopped 字段不足以启动模型。入口在模型调用前核对停止身份、保留官方输入和 context 字节、原根 Profile/model、冻结连接与 deployment/wire、原 seed commit 和 Braid 请求，缺失或改变明确报错。

每次恢复先将会被覆盖的 run 根控制文件与派生证据保存到 `recovery/<attempt>/`，旧 model-gateway 完整目录（含请求、HTTP错误与原私有权限）、native 归档、native-config 与 maintenance 移入该恢复归档，实际原生 home 和 Braid 原状态仍留在原位置；不复制大 worktrees。恢复收据记录停止来源、原 seed、模型、修复 binary 与入口字节哈希。旧失败 turn 和会话不能改写为成功，恢复耗时属于该 attempt，不用于宣称两模型严格同条件比较。没有新增运行停止阈值。

替换恢复二进制时，需要同时冻结它实际消费的资源协议版本。仅提供 `configure/fence/launch` 的 `support/runtime_resources.py` 不能与仍调用 `status/reclaim` 的旧 Braid 配合。已移除资源门控的版本还须配套 `runtime/native-managed.mjs`、`runtime/bin/pi` 及其真正加载的 Pi `dist/bundle/cli.js` 和同版 `dist/`；只替换未被加载的源码无法生效。可以将这些确定成员作为只读 overlay 挂载到原 runtime，并逐文件记录哈希，保留其它扩展、fd、模型路由和会话预算材料。恢复属于同一原运行，协议修复不能重新准备业务或重置原会话预算。

用户明确调整在途模型有序路由时，同 run 恢复额外传入 `--resume-routing-change-receipt <JSON>`。收据必须含原 `run_id`、`authorized_by:"user"`、非空 `reason`、原 `routing-snapshot.json` 的 `old_routing_snapshot_sha256`、新冻结 `support/model-gateway.json` 的 `new_catalog_sha256`、新 `support/gateway-routes.json` 的 `new_routes_sha256`，以及列明本次授权变化模型的 `changed_aliases` 数组（旧单模型 `changed_alias` 仍可读取）。入口要求模型集合不变、实际变化的链恰好等于列明集合，并核对这些实际字节与所有未列明模型的有序链及 deployment/wire 身份；未带收据仍要求原配方完全一致。变更身份归本次 `recovery/<attempt>/routing-change.json`，旧配置、请求和错误保留在恢复归档。该入口沿既有停止收据恢复原会话与应用，不会热重载一个正在处理请求的网关；运行宿主须先在可追溯执行边界停止旧 owned execution，再启动与新链长度及协议配套的冻结 proxy。生效以新 gateway ready/config hash 和实际请求回执为准。
