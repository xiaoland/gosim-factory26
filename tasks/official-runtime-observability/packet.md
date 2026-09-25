# 官网 Run detail 可追溯性调查

状态：公共能力已按授权落地，真实运行验收另需确定实验范围。用户确认原话：“是的，按这个方向继续。”其复核对象是上一轮提出的通用实验设施、ARC 适配层和事实生产者的职责划分。随后用户指示“没错，继续，直到方案收敛”，授权继续设计并自主解决常规工程取舍；对已收敛的 [design.md](design.md) 又明确指示“同意，开始落地”，授权实施其中的公共 ARC 上报工具、采集与查询、包身份兼容及相应文档。具体 Harness 接线、新模型运行和官网上传不属于本次范围。

2026-09-25 用户指出官网 Run detail 看不到“可追溯性”，提供 [Runtime API 文档](https://arc-bench.com/api-doc)并建议接入。Agent 将这句话误判为授权，直接修改活动 variant；用户随后指出越权，并要求从实验基础设施的角度讨论。误改的源码、文档及 SDK 副本已撤回；未打包、提交或运行新模型。后续只调查与设计，得到明确实施授权前不再改源码。

已查官方文档：`arcbench_agent_runtime` 在参赛 Agent 的 Runner 工作区写 `.arc/traceability/*.json` 与 `.arc/runner-events.jsonl`，官网后端消费它们刷新 Run detail。旧 OTLP 上报是本地实验过程证据，不会自动填充官网这组文件。官方 Python starter 已下载至忽略的 `runs/official-runtime-observability/starter-20260925.zip`；SHA-256 为 `efad0e6c9986aeb14c2aa75a61fa34ca6278b73767bb257076a1fe75bbbd0386`。这是调查证据，不是项目依赖。

只读核查：`lab/arc_bench/competition.py:collect` 已获取 `/runs/{id}/traceability?node_id=__all__` 和增量日志、commit history；`lab/arc_bench/playground.py:collect` 也获取 traceability。`lab/arc_bench/arc_bench_adapter.py` 保存本地 Runner workspace，`lab/arc_bench/results.py` 定位其中的 runner events。历史 `runs/competition/iteration-throughput-boundary-20260923/hosted/` 下五份不同 variant/task 的 `traceability.json` 都成功取得平台值，但 `interfaces`、`tests` 均为零；这表明所查旧运行的采集链路可用，空视图至少有上游未产生关联的可能，不证明全部运行和当前官网仍如此。

已认可的方向：通用实验设施负责保存原始 OTLP 与外部命令结果；ARC 适配层负责保存和查询官方 Runner/官网的原始 traceability/events，向运行者提供平台协议材料。需求到实现和测试的真实关系由执行 Agent 或其 Harness 在工作时上报；基础设施不从 OTLP、文件名或 Git 提交推断并填充官网图。接入适用于任意 Harness，不由 `pi-team-mixed` 独占。

本轮只读核查发现，现有 `instrument_entry` 是观察标准入口的本地包装，不能直接视为适用于任意上传包的材料安装器。Competition 的 prepare 消费冻结包，并要求本项目 manifest；这也不是所有外部 Harness 已经通用的构建接口。后续设计须明确支持包如何与原包的路径、依赖安装和清单共存，避免为了接入观测而迁移原包目录造成行为差异。

上报支持采用可独立分发的 Python zipapp，内含固定来源的官方 SDK、命令入口、简短说明和来源记录。Harness 作者通过自己的原生机制将入口与说明交给 Agent，在自身打包时纳入该文件；设施不解析其 profile、不自动修改系统提示或重新布置原包目录。本地和官网消费同一个冻结 Agent 包，材料存在与实际使用分别记录。不承诺任意旧 ZIP 加入工具后即可自动产生关联。

证据采集默认工作，不以上报支持是否启用为条件：本地读取 Runner 原始文件，官网使用已有接口。查询分别呈现支持材料是否提供、实际收到哪些事件和记录、采集是否成功及截至何时，不能将空表等同于未接入或将 SDK 自报 passed 等同于官方评分。当前 `competition.collect` 只保存异常类名，会丢失 Client 已保留的 HTTP 状态和响应内容；`results.py` 枚举 `.arc` 顶层文件，尚未显式链接嵌套 traceability 表。这是已确认的设施诊断与证据入口缺口。

官方 starter 中的两个 skill 脚本实际上直接实现文件协议，并未调用 SDK。因此它们不能不经核对就当成官网文档要求的 SDK 调用入口；复用官方 SDK 本身。通用 OTLP 接收继续不要求 ARC 字段，ARC 数据保持原始文件与响应，解释归 ARC 查询/分析组件。

补充核查：SDK 0.1.0 无第三方依赖，要求 Python >=3.10；JSON 表写入使用固定临时文件且没有跨进程锁，读错误会退为空表。共享入口需要对同一数据目录的 SDK 操作加文件锁，并在调用前防止损坏的已有表被当成空表覆盖。WSL 当前 Runner 镜像声明 `/workspace/sdk` 的 PYTHONPATH，但实际没有 SDK，不能依赖环境变量推断依赖已经安装。官网已存日志只含整理后的 `stage/status/summary` 等字段，不具备原始 SDK 事件类型；采集不得依赖它们触发可靠的逐变更快照。

前一轮设计只更新本 packet 和新增设计记录，没有修改运行源码、构建包、运行模型或上传官网，也没有提交。当前按已认可方案落地公共能力；真实运行和提交仍分别遵守授权边界。

## 2026-09-25 实施与验收

公共工具保存在 `lab/arc_bench/agent_runtime/`，包含从官方 starter 原样提取的七个 SDK Python 文件、上游 README/pyproject、来源及逐文件摘要，以及调用 SDK 高层追溯和状态方法的独立命令入口。`python -m lab.arc_bench runtime export` 用标准库生成自包含 zipapp，输出 SHA256；包内的说明、方法签名和调用结果不依赖具体 Harness。入口使用 Runner 原生路径，以文件锁保护经过入口的并发 SDK 调用，在写入前拒绝损坏的既有表，并把调用结果单独记录在 `.arc/runtime-reporting/operations.jsonl`。锁不能约束绕过入口的 SDK 写入者，SDK 多文件操作也不具备事务保证。

ARC 采集入口新增只读 `traceability <run或task目录>` 查询。本地读取 Runner spec 指定或默认的追溯目录、原始事件和工具调用记录；矩阵把相关路径交给通用制品索引，结果解释器也链接嵌套表。Competition 与 Playground 在已有监控轮询时采集官网追溯；每次成功或失败都留时间、来源和 HTTP 细节，最近成功值作为兼容副本保留。Competition 的包校验改为接受官方根入口包，存在 Factory manifest 时继续严格核对。技术说明、运行说明及 lab 入口文档同步更新，没有向通用 lab 引入 ARC 语义。

WSL 隔离工作区 `/home/yyh/Development/factory26-official-local/official-runtime-observability-20260925/implementation/` 接收了本轮 lab 源码快照。38 个 Python 文件已完成 AST 语法解析；导出的 `final/arc-runtime.pyz` SHA256 为 `69a77b881a5ddcb8a7f5349055451c9e150336ec1a31719514cb880cef0977e3`，导出报告 SDK 版本 0.1.0。最终归档静态核对了入口存在及七个官方 SDK 源文件与 SOURCE.json 摘要一致；未运行包 smoke 或伪造 Agent 调用。

把历史 `pi-team-mixed/arc-bench-lite--keep` 的原始官网 `traceability.json` 放到该隔离工作区只读查询，新入口报告 `last_attempt.status=completed`、interfaces=0、tests=0、traceability.status=empty、工具使用未知，与文件中的平台事实一致。这核对了旧记录兼容和采集成功空表的展示，不证明新工具曾在 Agent、官网或多进程并发中运行。WSL 已发布 Runner 镜像的源码还核对到 `ARCBENCH_OUTPUT_DIR=/workspace/template`，默认 `.arc/traceability`，并允许 spec 指定目录；本地查询对后者做工作区内路径映射。

本轮没有运行新的模型或 benchmark、没有上传官网、没有修改活动 variant、没有提交。后续真实接入验收须先选择实际 Harness、冻结包与任务，再按实验边界记录输入、矩阵与完成条件；成功标准是 Agent 的真实上报和官网 Run detail/保存响应的对应关系，而不是本地能导出 zipapp。

## Git commit history 后续调查

用户进一步要求调查能否把 Braid 的真实提交历史接入官网 Run detail。本轮只读调查，尚未授权该接入的源码修改。官方 SDK 的 Git 操作针对 Runner `project_dir`（本地 Runner 为 `/workspace/template`），`notify_commit_history_changed` 只发刷新信号，不上传提交对象。当前活动 Harness 在 `.factory26/<run>/work/application` 内提交，最终以 `git archive` 导出应用并删除成功运行的内部 worktree，所以 Runner 项目目录没有该仓库的历史。历史官网记录中五份 `commit-history` 响应均为 `workspace_unavailable`；无法据此断言仅复制 Git 历史就能使终态页面可查。

建议保持公共能力与 Harness 分离：由 ARC 接入层提供接受源仓库和选定提交的历史发布动作，在 Runner 项目目录导入真实提交祖先并用官方 SDK 发刷新信号；Harness 只传递仓库与交付引用。先验证运行中页面能读取该仓库，再决定是否需要持续同步未交付的工作分支。设施采集应在已有官网轮询中保存 `commit-history` 响应，区分运行中可见与终态工作区不可用。不能以合成提交、单个 hash、Git bundle 文件或 OTLP 冒充官网 Git 历史。真实官网验证需要单独确定实验输入、额度和完成条件。

用户随后明确指示“同意，应用修改”，授权上述公共 Git 历史发布、活动 Harness 接线、官网运行中采集及相应文档修改。`arc-runtime.pyz publish-history` 只接受源仓库、提交引用和 Runner 项目目录；导入选定提交的真实祖先，更新受管 `arc-delivery` 引用与 HEAD，通过官方 SDK 发送刷新信号，不改动应用文件或接管已有非受管仓库。`--preview` 用于应用交付后的预览刷新。活动 `pi-team-mixed` 构建时纳入该工具，Braid 运行期间每五秒检查交付引用，交付后再发布一次；发布失败单独保留在 `history-publication.json`，不冒充生成失败，并保留源 worktree 供恢复。官网 Competition 和 Playground 沿用原有监控周期采集 commit history；`workspace_unavailable` 观察保留但不覆盖此前采到的提交列表。

本轮没有运行模型、benchmark 或官网提交；历史页面能否在运行中显示、终态能否继续访问，仍需后续经授权的真实官网 run 验证。未增加 Factory 自身测试或模拟探针。

已对本轮涉及的六个 Python 文件做 AST 语法解析，`git diff --check` 无空白错误。它们只证明源码可解析及补丁格式正常，不证明 Git 导入或官网展示在真实 Runner 中生效。
