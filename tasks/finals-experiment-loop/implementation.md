# Lab 实现计划

本计划落实 [design](design.md) 已决定的命令、程序/数据路径、run 生命周期、status、观测、Console、restart 与评测合同。2026-10-06 用户已批准开工、提交和真实模型独立会话验收，授权见 [packet](packet.md)。计划只列确定代码与文档交付；调查和信息收集已在设计阶段完成，真实使用反馈单列于 [evaluation](evaluation.md)，不作为决定架构的实施阶段。路径与恢复改动优先在用户指定的 I14-dx-test、pi-minimal-vv-dx-test 派生 variant 落实，原 variant 身份与历史运行保持。

## 改动范围与顺序

### 1. 建立 run 入口、目录及 ARC 执行

将 `lab/__main__.py` 改为新的 run CLI，提供 start、stop、pause、resume、restart、status、wait、logs、evaluate、archive、serve。新增 `lab/run.py` 作为 CLI/Python 共用运行函数，使用 ARC Local SDK 与 Hosted 两个实际分支，调用启动时直接执行。

在 `lab/arc_bench/run_layout.py` 固定 manifest 与 program/inputs/data/records/snapshots/evaluations 布局。program 保存实际组装的代码、角色、技能和状态脚本；data 包含 workspace 与 harness 原生状态；records 保存每次运行新增的日志、费用、遥测、status 和实际请求/响应。task 配置消费 ARC 需求及 evaluations 列表，不导入旧 recipe/job/attempt 身份。

从 `lab/arc_bench/local_job.py`、`arc_bench_adapter.py` 和现有 runner 提取 SDK 参数、实际进程/容器句柄、终态与 workspace 收回；从 `lab/exp/hosted.py`、`lab/arc_bench/hosted_monitor.py` 提取平台 API、真实响应、同次未知 POST 查询和下载。Local 移除调用链中的 admission/slot/reservation；Hosted 保留平台原身份及实际能力。pause/resume 使用 Docker pause/unpause，Hosted 直接返回不支持。

target 配置固定提供 WSL、sfp7、Hosted 的宿主、run root、Docker/平台入口、凭据引用和观测地址；Mac 控制与回收全部放 WorkSSD。WSL/sfp7 是两个独立执行 target，共享观测服务配置指向 sfp7。start 自动保存实际展开的配置、程序版本和输入，stop 使用本 run 已保存的真实句柄。

### 2. 统一 variant 装配与原生数据入口

2026-10-07 用户已明确授权精简 runtime 及优化构建、部署。execution_owner 持续负责 runtime 构建、依赖材料与 DX builders：移出不属于 Harness 启动依赖的预装开发环境，保留实际必需依赖的消费接线；将现有 derive-linux 收敛为冻结基座及 Braid 字节的派生，避免不相关依赖重装；执行宿主独立复制已部署基座后只传变化内容，保存原始基座与新执行身份。完整导出先形成来源记录，容器/镜像清理失败另存具体错误，不阻断已导出的交付。evaluation_implementation 负责 self-test 认证、映射及评测回收，与 runtime owner 按 local_run 函数边界协调。

修改 `scripts/execution_bootstrap.py`、`scripts/experiment_entry.py`、`scripts/harness_layout.py`、`scripts/package_agent.py` 和 `submission` 的组装接线，统一传入 program、inputs、data/workspace 与 native_state_path。网关的创建、关闭、route 和采样由公共入口负责，variant 只消费路径和端点。

适配清单为 pi-minimal、pi-minimal-vv，以及 pi-braid-i14、pi-braid-i14-cleaner、pi-braid-i14-cleaner-direct、pi-braid-i14-e2e、pi-braid-i14-reviewer、pi-braid-i14-reviewer-cleaner-e2e、pi-braid-i14-reviewer-direct。保留各 variant 独立角色/技能/流程，共用路径与运行合同；Pi-only 的 main.py 将 home/session 放在 data/harness，I14 的 main.py/run.py 将 Braid DB、origin/worktree、Pi home 和 retained request 放在同一数据域。容器内路径保持稳定，私有凭据和本次服务句柄独立于可迁移 data。

同 task 调用 Pi 原 session 或 Braid `local --offline-resume`，保留原生身份；task/需求版本变化创建新的原生状态子目录和需求入口，保留历史数据并接续应用。不得因旧 Braid root 已关闭就把新 stage 当作已完成。

### 3. 实现 status、控制与同 variant restart

在各适用 variant 加入随 program 固定的 `status.py`：stdin 为采集事实和数据路径，stdout 为 activity、brief、last_activity_at 和具体依据。I14 按最近 native provider turn 判断，Pi-only 按最近 session message 判断；评测使用自己的状态脚本。观察循环原子保存 records/status.json，并输出 OTLP。

调整 `lab/status.py`、`lab/wait.py` 和新 run 控制接线，使 status 默认读取未归档且 lifecycle != completed 的摘要，RUN/--all 显式查询其它运行；显示 lifecycle 与脚本 activity、费用、时间和原错。脚本失败给 unknown，保持执行事实。archive/--undo 只改列表标记，logs/follow 读取已保存日志。

在 `lab/arc_bench/restart.py` 实现停止来源、确认实际停止、保存完整 data、重新组装同名 variant、迁移数据并启动新 run。终态来源使用确定的已保存数据；明确 snapshot 可选较早版本。新 manifest 保存 source_run、快照、原/新程序版本和 native_state_path；不接受 variant 或路径映射参数。新 run 不重复计入已迁移原生历史中的旧 usage/费用。

### 4. 交付共享 Collector、Backend 与通用 Console

复用 `lab/otlp.py` 的三信号 protobuf/gzip、SQLite 原件、分页与具体错误；补 run 归属、接收边界、查询索引和 Hosted 原件导入。共享数据库位于独立服务目录，Hosted 数据库位于 records/telemetry；运行数据 restart 时不携带接收库和旧费用。

新增 `lab/backend.py` 提供 run 列表/详情、资源、日志、费用、评测、OTLP batch 和原件读取，新增 `lab/serve.py` 用 `serve --config` 在同一常驻进程承载 Collector、API 和静态 Console。Hosted 包只调用接收落盘核心。CLI/Console 共用保存的 status 与原始来源，不增加各自观察循环。

补 `scripts/agent_support.py` 的 CPU/I/O 与实际采样范围，移除采样成功启动门禁；接通 Braid/Pi 的 native session/turn、低频持续活动与 gateway/provider/platform 费用来源。保留 actual/estimate、来源时间、采集缺口与原错。

修改 `braid-console/web` 的入口、API、列表与详情，提供 Pi-only/Braid/评测通用 run 页面，显示状态、资源、费用、日志、快照和评分。移除新链路中的 Braid live CLI 写桥、人工登记、runtime 写入及 accessor 协调；静态资源由 Lab 服务提供。

### 5. 将 Braid 视图交回 Braid

将现有 `lab/analysis/braid_telemetry_viewer.py` 的 reader、投影和页面迁入 `sources/braid/viewer/reader.py` 与 `viewer/web/`，原模块保留离线导出的薄入口。Factory Backend 显式装载其后台处理与只读路由，Console 提供入口。

在 `sources/braid/src/evidence.rs` 抽出从完整已解 records 重建的核心，现有 protobuf 入口和已解输入复用；对应 CLI 增加该输入形式。reader 只解码新增 batch，保存跨 batch 的累计证据。有新数据时每 30 秒最多按固定 cutoff 重建一次、原子发布投影，查询读已发布结果；对象和 session 目录分页，正文按 artifact 引用/offset 读取。保留更新错误与旧 cutoff，不在页面轮询中全量解码或进入 live DB。

### 6. 完成默认自动化、四个测评后端和旧入口退役

新增 `lab/automation.py` 的普通 Python 默认程序：单 task 与 stages 共用运行 API，读取采集变量，显式组织 stop/restart、同 variant stages 和自动测评。Local 在实际执行宿主运行，Hosted 的跨 run 程序在包外控制宿主运行；源码、PID 与日志记入首个 run 的 records，不设置实验级控制器或未来任务队列。

从 `lab/arc_bench/evaluate.py`、`package_arc_replay.py`、`arc_replay.py` 接通 simulate、task、official、self-test 四个独立测评后端，消费同一应用快照；task 配置决定实际执行列表、self-test 任务身份与官网费用模式。self-test 使用自己的 ZIP 包装、提交、状态和私有结果接口，不继承 Hosted 生成提交或模型配方。评测使用独立副本、身份、状态与费用，公开报告显式进入 inputs，隐藏报告保持在评测记录。自动保存成功、失败、停止的全部平台可得结果，保存范围/时点和缺项。

迁移维护中的入口、配方和调用者后，删除工作树旧 compile/doctor/build 启动流程、capacity/authority/receipt 门禁和 Console 写入协调。旧冻结运行继续由原执行器处理，历史记录保留其读取入口，不批量接管活动执行或重写旧身份。

更新 `lab/README.md`、`lab/arc_bench/README.md`、`braid-console/README.md`、产品/技术说明、运行文档与本任务 packet，使新命令、程序/数据分离、status、restart、费用/结果与历史入口只有一套当前说明。

## 交付采用

每项交付包含源码与实际受影响文档，后项消费前项已确定接口，不把“调查后再决定接口”留给实现负责人。主 Agent 负责 run 合同与整体接线，执行负责人负责 ARC/variant/状态/restart，观测负责人负责 Collector/Backend/Console/Braid view；共享文件的修改按依赖交接，不覆盖他人工作区。

代码编译、构建和实际操作反馈按仓库规则执行，不编写或运行 Factory/Braid 测试、smoke 或换名自检。新的模型/官网运行按独立 evaluation 与实验 packet 的明确范围执行；本计划不默认取得这些执行授权，也不将其结果作为未来架构选择的占位。
