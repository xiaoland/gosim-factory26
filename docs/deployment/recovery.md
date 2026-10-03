# 工作区恢复、应用重放与监控

本页是当前恢复入口。旧 checkpoint、prepared、ARC attempt 和官网 journal 的详细字段合同保留在[历史恢复合同](history/recovery.md)，不作为当前命令来源。

<a id="当前-checkpointprepare-与停止门控"></a>
## 当前 checkpoint、prepare 与停止门控

运行控制先读取该实验冻结执行器的能力，并沿 `python3 -m lab control` 操作。当前 Hosted adapter 支持终止和导出，不支持暂停、恢复或完整 checkpoint；平台的 `can_resume=true` 只是平台声明，不能证明 workspace、入口进度或检查点完整。疑似停滞先做一次有界的独立只读核对，在处置记录中写明观察事实、来源时间、证据缺口、动作目的、执行器能力、恢复路径和预期损失；不以暂停试探可恢复性。决定放弃时明确接受进度损失，再经冻结 Lab 执行器执行 `stop`，保存请求与独立终态回执。

I14 checkpoint/prepared producer 使用 schema 3，application 使用 schema 2。checkpoint v3 通过 `harness-layout.json` 的真实 artifact reference/member 保存定义依赖，物理 store 只是解析位置；缺少实际 artifact relation 的 identity 不能补造为完整恢复。保存来源时使用：

```sh
python3 submission/exp_checkpoint.py checkpoint \
  --source RUN --output NEW --source-identity IDENTITY_JSON \
  --stop-evidence STOP_JSON --acquisition ACQUISITION_JSON
```

获取窗口必须覆盖全部 writer 的连续关闭证明；只有停止原件或缺少 Git/native 历史时保留 `partial`。分离的 Docker 导出还要以 `--state-binding <attempt/export.json>` 消费真实导出回执，并由 `--source` 明确选择运行状态目录，不能从 Mac、`/assets` 或嵌套 `/workspace` 猜来源。

Hosted 来源的当前 source-stop 导入只核对和保存事实，不执行停止或授予启动许可：

```sh
python3 -m lab import-source-stop --experiment EXPERIMENT --attempt ATTEMPT \
  --birth BIRTH_GET_JSON --status TERMINAL_GET_JSON \
  --cancel-evidence CANCEL_JSON --authorization "已获授权的恢复范围" \
  --identity-output NEW_IDENTITY_JSON --output NEW_STOP_JSON
```

`experiment` 与 `attempt` 必须成对，并核对冻结合同、execution/dispatch、run/submission/competition/task 及时间身份；独立终态 GET 必须包含终态和 `finished_at`。恢复启动仍要用私有 deployment `cookie_file`，重新 GET 确认同一来源已停止。`recover` 不停止来源、不启动模型；`prepare` 只允许声明的材料刷新、transport、路径别名、兼容 runtime 等有限修复，partial 不能进入完整恢复执行，prepared 本身不携带停止许可。

这条 source-stop import 同时是当前的截断门控：取消响应只能作为证据原件，不能单独把活动来源标为可恢复；只有配对的终态观察、同一 attempt/incarnation 和后续显式 checkpoint/prepare 才能进入接续判断。

## 当前入口

恢复前确认来源执行已停止、来源身份和 checkpoint/prepared 完整，再决定派生新 run、接续明确阶段或只做应用重放。当前命令如下：

```sh
python3 -m lab recover /absolute/checkpoint \
  --intent /absolute/recovery-intent.json \
  --environment /absolute/environment.json \
  --directory /absolute/new-experiment
python3 -m lab status /absolute/new-experiment --json
python3 -m lab start /absolute/new-experiment \
  --deployment /absolute/private-deployment.json
python3 -m lab control /absolute/new-experiment ATTEMPT_ID stop \
  --request-id REQUEST_ID
```

`recover` 只派生新材料，不停止来源、不启动模型；`start` 重新核对来源、授权、runtime、预算、deployment 和物理身份。v3 定义或 runtime 换版按 [制品合同](../../lab/exp/artifacts.md)声明兼容性与引用，不重复编排 producer 已完成的输运。控制动作必须沿冻结 controller/runner/backend 合同执行，未知效果先读回，不重发原请求。需要选择检查点、丢弃进度或改变模型/费用时，决定和损失写入所属 packet。

<a id="官网监控"></a>
## 当前监控与重放

监控由实验 controller/adapter 保存平台观察、原始错误和终态；独立消费者只读取 `lab monitor EXPERIMENT --json` 或保存摘要，不创建第二采集循环，不自动暂停、恢复、重跑或修改源码。停滞告警先做有界只读核对，区分实际活动、观察失联和语义无进展；不能用 token 增长、collector 存活或 `can_resume` 代替有效进展证明。

冻结应用或阶段提交的独立评价必须声明输入制品、测试/需求身份、模型和费用模式，不能把回放分数当作原生成耗时或模型消耗。Braid 会话、原生 profile 和 OTLP 查询见 [Braid 诊断](braid-diagnostics.md)；按 producer 查询见 [证据说明](evidence.md)。

<a id="实验恢复与反馈循环"></a>
## 实验恢复与反馈循环

每轮先在 task packet 登记题目、模型、来源、费用模式、调度、告警消费者和完成条件，再按 `compile → doctor → build → start → status/control` 推进。`recover`/`prepare` 只产生有身份的新材料；`start` 重新核对来源停止、授权、runtime、预算、deployment 和物理身份；`status`、`monitor` 只读取已保存 projection 和原始回执，不另建采集循环或自动重试。疑似停滞的处置与来源导入是独立门控，不能用一个成功的 GET 或 `can_resume` 替代另一项证据。

每个阶段分别保存事实、错误和终态。应用交付与平台评分是独立结果；官网写入结果不确定时沿同一 journal 只读核对，不能盲目重发。控制、来源身份和恢复损失写入所属 packet，接续者据此选择同一来源的可恢复检查点或明确放弃现场。

<a id="冻结应用与阶段提交回放"></a>
## 冻结应用与阶段提交回放

可评分的应用必须冻结明确 commit、需求/输入 hash、来源 run 和制品 hash，并区分 `stage/provisional` 与 `final/published`。阶段回放只消费显式 Git ref 或已发布应用，不能读取正在写入的工作树；没有完整交付的工作目录不能冒充最终制品。回放使用独立费用模式和 journal，记录 ZIP SHA256、官方 run、通过数、评分与具体错误；回放耗时和模型开销不归入原生成性能，也不能把隐藏测试反馈传给仍在生成的 Agent。

当前 runner 对已验证 prepared 使用包内 `main.py ... --execute-prepared`，不再次解包、重建 Git 或刷新材料；routes 必须等于 prepared 的 native transport 回执，变化时重新冻结并 prepare。详细阶段包字段和历史评分证据见[历史恢复合同](history/recovery.md)。

## 历史入口

旧 schema 1/2 checkpoint、legacy Docker handoff、旧 Hosted journal、旧本地 attempt 和详细监控节奏保留在[历史恢复合同](history/recovery.md)，仅用于读取既有身份、错误和证据。当前 `submission/exp_checkpoint.py` producer、schema 3、Hosted source-stop 和 `recover/prepare` 仍是本页当前入口，不因历史合同存在而退役。
