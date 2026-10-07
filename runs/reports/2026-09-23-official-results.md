# 官网实验成绩与首阻断点

数据截面：2026-09-23 13:20（北京时间）。以 arc-bench.com 的 Competition 远端 `run_id` 和平台原始 `status.json` 为准；`FAILED` 表示测试未全通过，但若分数完整，仍是一条有效实验结果。动态过程和单个 run 现场可从本地 [Run Viewer](../viewer/index.html) 查看，刷新命令是 `python3 scripts/run_viewer.py`。本报告保留结论，原始运行产物留在忽略 Git 的 `runs/`。

## 已完成的 Competition 评分

下图每格约 5 个百分点；括号内是通过数/测试数。同一个任务横向可比，跨任务的合计只用于观察覆盖面，不能当赛事最终成绩。

| 冻结 variant | Lite / Keep | Lite / BookStack | 当前已评分合计 |
| --- | --- | --- | ---: |
| pi-team-deepseek | `████████████████████` 32/32 | `████████████████░░░░` 27/34 | **59/66（89.4%）** |
| pi-team-mixed | `██████████████░░░░░░` 23/32 | `████████░░░░░░░░░░░░` 13/34 | **36/66（54.5%）** |
| pi-team-glm | `██████████████░░░░░░` 23/32 | 运行中，未计分 | 23/32（不与前两行合计比较） |
| pi-team-vv | 尚未开始 | 尚未开始 | 未计分 |

| Variant / task | 远端 run ID | 平台分数 | 原始证据 |
| --- | --- | ---: | --- |
| deepseek / Keep | `bd3c2e50b511` | 32/32，100.0 | [`status.json`](../competition/iteration-throughput-boundary-20260923/hosted/pi-team-deepseek/tasks/arc-bench-lite--keep/status.json) |
| deepseek / BookStack | `d853830ddb0a` | 27/34，79.4 | [`status.json`](../competition/iteration-throughput-boundary-20260923/hosted/pi-team-deepseek/tasks/arc-bench-lite--bookstack/status.json) |
| mixed / Keep | `007b8fc9d38b` | 23/32，71.9 | [`status.json`](../competition/iteration-throughput-boundary-20260923/hosted/pi-team-mixed/tasks/arc-bench-lite--keep/status.json) |
| mixed / BookStack | `6e786f33bc1b` | 13/34，38.2 | [`status.json`](../competition/iteration-throughput-boundary-20260923/hosted/pi-team-mixed/tasks/arc-bench-lite--bookstack/status.json) |
| glm / Keep | `cc4afd58c444` | 23/32，71.9 | [`status.json`](../competition/iteration-throughput-boundary-20260923/hosted/pi-team-glm/tasks/arc-bench-lite--keep/status.json) |

已启动但未有评分：GLM/BookStack `23cf3569040f` 和 mixed/Web/12306 `46465ac9c58d`。其他 Web 任务仍是 prepared。当前双比赛控制器因官网 API HTTP 500 暂停；运行中任务的远端状态与控制器状态不是一回事。按 [矩阵任务包](../../tasks/dual-bench-hosted/packet.md) 恢复，不从旧 Lite 控制器重新发起。Web 题目不能与 Lite 同名题目合并评分。

## 从官方日志看到什么

逐例证据和限定条件在[评分诊断](../../tasks/iteration-throughput/cells/score-diagnosis.md)。以下是按首个阻断点聚合，不把超时自动解释为模型慢、功能缺失或生成失败。

| Run | 失败集中处 | 能作出的判断 |
| --- | --- | --- |
| deepseek / Keep | 0 项 | 在当前官网 Lite/Keep 的 32 项中完整通过。 |
| deepseek / BookStack | 7 项：5 个 Tags 入口、1 个 Edit、1 个 Favorite | 同一交付应用的源码与重评 DOM 分别确认：共用 Tags 用 `<details><summary>` 而非 button；草稿列表直接进入编辑页；Book 8.2 初始已收藏，界面只有 Unfavorite。这解释了入口阻断，不能解释 Agent 的决策过程。 |
| mixed / Keep | 9 项：6 个明确要求的 button 未定位、2 个 Pinned 定位差异、1 个 Save 未定位 | 官网归档缺失败 DOM、该 run 源码和原始自验记录；不能仅凭 locator 超时独立证实实际角色或“76/76”为何漏检。 |
| mixed / BookStack | 21 项：17 个入口/导航阶段、4 个页面或提交后阶段 | 公共入口阻断会掩盖下游行为，不能把 21 项都归成同一缺陷。 |
| glm / Keep | 9 项：workspace 1、卡片控件 3、编辑器 checkbox 3、Pinned 定位 2 | 官网只提供定位超时，缺失败 DOM；这里是阻断位置而非应用缺陷的最终定责。 |

deepseek 在两项已完成 Lite 任务上比 mixed 多通过 23 项，但两个 ZIP 的模型配方、生成轨迹和潜在实现都不同。这是候选方案的实际成绩差，不是“换模型导致提升”的因果估计；当前样本也不足以给其他六个 Web 任务或 pi-team-vv 排名。

下一轮最有价值的改进假设有三项。第一，对明确的界面合同做生成前后的细粒度校验：以题目文字和可访问性角色/名称为 oracle，能让 `button`/`menuitem` 类错误早于官网评分被发现；同时用等价实现反例防止测试把 DOM 包裹结构过度固定。第二，BookStack 优先验证真实用户旅程的入口可达性、认证前置和创建/编辑路由，再评估保存后的状态；这会区分公共入口问题与下游功能问题。第三，保留冻结 ZIP，把 GLM、V&V 和 Web 的官方评分补齐后再决定 profile 配方；尤其 V&V 对照缺席，当前不能评价它是否带来收益。三项均待后续实验检验，不从已有总分推定必然增益。

从 Agent 运行过程追根因的调查已在证据边界停止。官网 run 的原生会话、Braid 对象与自验细节没有随 journal 保存，平台维护时也无法补取；同配置本地 run 不是同一执行轨迹。[过程证据缺口](../../tasks/official-results/process-evidence.md)列明已证的产物机制和最小补采文件，在补齐之前不将上述改进假设称为 Agent 行为根因。

## 不进入成绩比较的官网运行

Playground 有三个无模型诊断 run：`23a11724c9f4`、`eb84b5a05b52` 为 `__demo__` 1/1；`2041e4b58701` 为环境探针在 12306 上 0/135。它们用于验证上传、执行和环境，不是参赛 harness 的成绩。两个 `__demo__` 复用同一 submission 但 run ID 不同，应保留为两次独立诊断。早期本地/WSL 公开测试的分数见[上一轮报告](2026-09-22-multi-agent-lite.md)，测试版本、环境和生成应用不一致，本表不混入。
