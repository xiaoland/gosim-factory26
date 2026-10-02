# ARC 可追溯性与 Git 历史接入

当前源码链接已指向 `pi-braid`，它是文中历史 mixed 的维护入口后继；不表示旧 run 使用了新源码。

## 当前阶段与授权

稳定公共接口已落地到工作区，待实际 Runner/官网运行证据验收。[design.md](design.md)记录获授权的接口方案；已提交实现的基线是 `896e3a8`。用户在复核方案后明确指示“好的，你可以开始实现了”，授权本轮公共 ARC 接口、mixed 薄接线迁移及受影响文档的源码改动。模型运行、官网上传和新提交不在本次授权中。

用户最新确认的边界是：“harness薄接线可以有，但是应该让variant自己实现，相对的，ARC 公共接入组件就要提供相应的稳定的界面。”这取代此前将轮询和线程生命周期收回公共组件的建议。variant 中存在接线代码不构成边界缺陷；审查重点是公共接口是否依赖特定布局、框架和生命周期，以及调用结果是否足以支持消费者自行处理失败。

## 要解决的问题

Harness 作者应能通过已分发工具的公开接口独立接线。安装、Agent 指令、仓库选择、调用时机和恢复策略归 variant；官方协议、一次操作的写入与通知、结果及诊断归公共组件。通用 lab 的 OTLP 接收不增加 ARC 业务约束。

`896e3a8` 基线的具体缺口，本轮均已在工作区处理：

- `publish-history` 只支持内部仓库向 Runner 目录导入，拒绝源与目标相同；直接在 Runner 仓库工作的 Harness 缺少对应入口。
- Traceability 方法由 SDK 反射得出；包装层没有独立接口版本，返回值和错误形式也未统一。
- Git 更新与刷新信号分两步完成，但返回值没有表达部分完成。HEAD 相同会提前返回，可能漏掉上次失败的刷新通知；`--preview` 还会修改目标索引。
- mixed 最终发布重新解析交付分支，未直接使用已冻结的 delivery commit；stderr 只保留末尾摘要，公共 Git 失败也未统一写入操作记录。
- mixed 构建导入公共 CLI 的 `__main__` 函数并压制 stdout，让内部 Python 布局成了消费者接口。

轮询周期、线程、重试、工作区保留和提示词仍由 variant 决定。需求到实现及测试的关系必须由实际工作者提供。

## 已实现与已知限制

`896e3a8` 提供固定来源 SDK 的独立 zipapp、追溯命令及查询、官网观察记录，并在 mixed 构建和运行中接入 Git 历史发布。官网已有轮询会采集 commit history；`workspace_unavailable` 保留在观察记录中，不覆盖此前取得的列表。mixed 尚无需求、实现、测试关系的事实生产者；工具入包不等于这些关联已产生。

该提交按内容暂存，未纳入工作区其他 Braid、SVC 和实验设施改动。接续时应同时查看提交与工作区差异，不能将当前整个工作区视为该提交内容。上一轮还在工作区更新过本地 ARC 证据链接，其提交归属以 Git 差异为准。

当前只发布选定交付提交的祖先，不包含未合并分支或未提交修改。官网是否在运行中读取到这些对象、终态是否继续保留工作区，尚无真实 run 验证。辅助证据缺失不能解释为 Agent 没运行，也不自动改变应用生成或评分结果。

## 证据与验证边界

| 证据 | 支持的结论与限制 |
| --- | --- |
| [官方文档](https://arc-bench.com/api-doc)与[固定 SDK 源码](../../lab/arc_bench/agent_runtime/) | SDK 在 Runner project_dir 操作 Git，通过 runner-events 发刷新信号；信号本身不上传提交对象。 |
| `runs/official-runtime-observability/starter-20260925.zip` | 官方 starter 调查副本；SHA256 为 `efad0e6c9986aeb14c2aa75a61fa34ca6278b73767bb257076a1fe75bbbd0386`。SDK 来源及逐文件摘要另见 SOURCE.json。 |
| `runs/competition/iteration-throughput-boundary-20260923/hosted/` | 五份历史追溯响应 interfaces/tests 为空；五份 commit-history 响应为 workspace_unavailable。不能证明当前官网行为或空视图的唯一原因。 |
| [公共入口](../../lab/arc_bench/agent_runtime/__main__.py)、[mixed 接线](../../variants/pi-braid/run.py)及[构建](../../variants/pi-braid/build.py) | 支持上面列出的接口缺口；是源码证据，不是运行成功证据。 |

上一轮在 WSL 隔离目录 `/home/yyh/Development/factory26-official-local/official-runtime-observability-20260925/implementation/` 导出过追溯工具，核对源码摘要，并只读查询历史空响应。该工具 SHA256 为 `69a77b881a5ddcb8a7f5349055451c9e150336ec1a31719514cb880cef0977e3`，早于 Git 接入，不能作为当前工具身份。随后 Git 改动只做静态语法与 diff 检查；提交前解析了 14 个暂存 Python 文件。没有运行 Factory 测试、包 smoke、新模型或官网任务。

本轮继续遵守仓库不运行 Factory 自身测试或模拟探针的规则。真实行为验收须使用经授权的实际运行，先冻结包、任务、凭据模式和完成条件；静态检查不能替代官网展示验收。

## 本轮实现与下一步

2026-09-26 官网 Hackathon GitHub run `b77e4357a4e1` 的在途核查：冻结 ZIP `3440b956…` 含 `arc-runtime.pyz`，`pi-team-mixed/run.py` 启动 Git 历史发布线程；官网 `traceability?node_id=__all__` 返回空 `interfaces/tests`，与关系事实生产者尚未接线一致，不能单靠空表证明 Agent 没有自行调用。用户随后明确要求：实验追溯不能给参赛 LLM 增添工作或认知负担。因此不为填满官网页面而加入上报提示词或让 Agent 维护第二套关系表；Harness 可从原有工作过程采集提交、Issue/PR 关联和实际检查结果，只有明确来源支持的语义关系才上报，没有就保留空白。当前 `commit-history` 返回 `availability=workspace_unavailable`，不能据此判断发布成功或失败。上一条同类 run `44db16c4b085` 的 `history-publication.json` 记录公共命令 `completed`、`signal_written=true`，但只发布了空初始提交，且官网历史同样不可用。当前 run 终态后需对照本地 `history-publication.json`、Runner `.arc` 操作记录和官网 API，分别判断包内调用与平台展示；当前没有足够证据把历史空白归咎于 variant 或官网单方。

下一步方案已写入 [design.md](design.md#后续运行观测方案待复核)，待用户复核：先用当前 run 的终态证据定位 Git 历史断点；协作路径从 Braid 原生对象和 Git 离线展示，不误用 ARC 的软件接口/测试表，也不增加 Agent 提示词或动作。必要的接线修复只根据断点实施。

公共 `arc-runtime.pyz` 现在以版本化 CLI 和 JSON 结果作为跨 Harness 边界，提供固定方法列表、原地 Git 通知与内部仓库发布。发布先解析 OID，目标只改受管 Git 元数据；每次调用均尝试刷新，失败结果保留原始 Git 命令、退出码和输出。mixed 通过公开命令导出工具、读取 v1 结果，最终用已冻结 OID 和确认持有该提交的仓库发布；轮询与现场保留仍由 variant 持有。官网证据查询区分提交历史最近观察与最近可用列表。公共组件未增加 supervisor、后台轮询器或自动提示词注入。

静态验收对四份受影响 Python 文件完成 AST 解析，并核对 40 个 traceability、14 个 events 公开方法均存在于固定 SDK；目标差异通过 `git diff --check`。未运行 Factory 自身测试、包 smoke、真实模型或官网任务，因此尚无公共工具在 Runner 中执行、官网收到刷新及 Run detail 展示的证据。后续实际运行需另行冻结包、任务、凭据模式和终点；完整 Agent 语义上报也需单独确定事实生产者。用户随后指示“可以提交”，授权仅提交本轮 ARC 接口及接线改动；工作区其他任务的未提交改动继续保留。

## 授权沿革

用户先认可公共设施与事实生产者分工，随后“同意，开始落地”，授权公共上报工具、采集查询和包身份兼容。早期未经授权的 variant 追溯接线曾撤回，这项教训仍适用。Git 历史调查后，用户以“同意，应用修改”授权公共历史发布及 mixed 接线，再以“可以提交”授权提交，形成 `896e3a8`。本轮用户进一步纠正责任边界并要求技术规划，随后“好的，你可以开始实现了”授权该方案的源码实施。
