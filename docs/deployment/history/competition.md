# 历史平台合同（只读）

本页仅保留旧 Competition journal、ARC 追溯/历史 CLI、Playground 和已冻结现场的证据。当前规则、计分、参赛包及运行能力见 [当前平台与冻结制品](../competition.md)。

### 历史官网 journal 与原件（只读）

旧 Competition journal 的自动化入口已退役；当前 Hosted job 由 Lab experiment 的 backend/controller 保存平台身份、写入回执和终态。`lab/exp/backends.py` 与 [Lab](../../../lab/README.md) 是当前源码/合同入口，下面的 `competition.py` 命令只用于读取或解释保存该协议的历史 journal，不用于新执行。
通用参赛包只需满足平台的根入口 `main.py` 与 `requirements.txt`；Factory 包另有 `package-manifest.json` 时，Competition 会核对其中每个文件的哈希。所有包的冻结身份仍是 ZIP SHA256。
`prepare` 不写平台；其余写入按批准的实验范围执行，任何 POST 结果不确定都先保留 journal，再只读核查，不盲重试。
`prepare --credential-mode self_funded` 使用自带模型 key，也是旧 journal 缺失该字段时的历史语义。
费用来源、模型通道及是否正式参赛按本轮实验 packet 分别确定；当前 I13 范围见 [I13 packet](../../../tasks/iteration13/packet.md)，不在历史 journal 中推导新授权。页面模式与 API 凭据的当前对应关系见[当前赛事规则](../competition.md#赛事规则与提交模式)。旧 journal 只用于读取和收集证据，不授权新正式提交或自动接续。
凭据模式与 ZIP、模型配置一起冻结在 inputs.json 中，重用目录时必须相同；改变模式使用新的状态目录。后续 snapshot/run-all 从该记录取值，不另传开关。
摘要的 credential_mode 是请求模式；实际运行返回的 billing_mode 另保留在 platform_result 和原始 status.json，不能混为一谈。
使用 `self_funded` 时，冻结模型配置与自带 key 对应的服务地址一致；使用平台额度时，记录实际请求模式及平台返回的计费模式。不能把旧 journal 的费用配置无条件复用到新实验。
预算决定以 Braid session 为边界，七类昂贵模型合计只允许一个 Braid session 使用；Pi 原生会话和 sub-agent 不单独占用 Braid 名额。
当前团队源码以 CLI binding 对应的 Braid 逻辑成员领取名额；上下文重建沿用同一成员，原生子会话不另占名额。旧冻结包不包含这项修正。
限制是模型使用权限，不是金额上限；一个长会话仍可能很昂贵。
实现与下一轮修复范围见 [预算与交付任务](../../../tasks/competition-budget/packet.md)。

按本轮已授权的题目准备新 journal，以下只冻结本地输入，不上传或启动：

```sh
python3 -m lab.arc_bench.competition prepare \
  --state /path/to/new-journal --package /path/to/frozen-agent.zip \
  --competition <competition-id> --variant pi-braid-i13 --task <task-id> \
  --model-config /path/to/model-config.json --credential-mode self_funded
```

后续 `snapshot`、`create --task`、`start --task` 是官网写入，只有所属实验授权覆盖时执行；`run-all` 按 journal 顺序推进。写入回复未知时先用 `recover --state <同一journal>` 核对已发生的副作用。已有 run 使用 `status`、`logs`、`watch` 或 `collect`，均传同一 `--state` 和 `--task`，不因监控中断创建新 run。当前监控与处置边界见[恢复手册](../../../lab/exp/execution.md#查询保存事实)。

共享操作入口通过 `Controller.launch()` 在同一比赛锁内核对 pending、snapshot、create 和 start，取得实际身份后释放锁，再交接采集；不会持锁等到比赛终态。`launch-receipt.json` 保留每次启动结果，`write-receipts/` 保存写入原响应；未确认的写请求只读核对，不自动重发。当前操作范围见[恢复反馈循环](../recovery.md#当前-checkpointprepare-与停止门控)。

Competition prepare 还可显式冻结 `--experiment-key`、`--case`、`--run-names <JSON文件>`；最后一项以 task ID 对应本次运行名。名称不替代包 SHA256、真实 run ID 或来源应用摘要；完整规则见[实验导航](../../../experiments/README.md)。Playground 仍只用于显式 practice，不混入 Competition 结果。

### Git 历史（当前 CLI 指针）

Git history 通知与发布的当前 CLI 及协议见 [arc_bench 适配说明](../../../lab/arc_bench/README.md)。本页不复制当前命令合同；下面的 Playground 和 journal 记录仅用于历史现场取证。

## 历史 Playground 操作（只读）

[playground.py](../../../lab/arc_bench/playground.py) 使用网站 HTTP 接口完成登录、上传、运行和证据收集，日常实验不需要浏览器。
首次运行 `python3 -m lab.arc_bench.playground login`，交互输入网站邮箱和密码；也可以通过 `--credentials ~/.config/factory26/playground-login.json` 读取权限为 600 的 JSON 文件（email、password）。
登录验证后保存权限为 600 的 `~/.config/factory26/playground.cookies.txt`。
网站会话与比赛模型密钥分开保管，登录信息不进入仓库或命令参数。

```sh
python3 -m lab.arc_bench.playground whoami
python3 -m lab.arc_bench.playground requirements --catalog benchmark
python3 -m lab.arc_bench.playground submit --practice --package /path/to/agent.zip --config /path/to/model-config.json --requirement keep --name factory-keep
python3 -m lab.arc_bench.playground watch <run-id>
python3 -m lab.arc_bench.playground collect <run-id>
```

上传前必须准备符合平台契约的 Python Agent ZIP，根目录包含 main.py 与 requirements.txt。
`submit` 要求通过 `--config` 显式提供网关和模型，并使用仓库外比赛密钥；配置不会改变 ZIP 已打包的核心或工作流。
清单明确标记 configuration_scope=model-settings-only，包身份以 SHA256 为准。
历史 `--offline` 记录使用非凭据占位符，不代表真实模型连接。
包哈希、已确认的 submission/run ID 与执行阶段记录在 `runs/playground/upload-*/submission.json`，便于写请求失败后查明已经完成哪一步；传输结果不明时不自动重复 POST。

该历史客户端的续跑、启动和取消只接受清单中明确记录为 practice/probe 的 ID；分类不替代当前任务授权，未知或正式 ID 不由此入口启动。

同一包重跑使用 `python3 -m lab.arc_bench.playground run --submission <submission-id> --requirement <requirement-id>`，避免重复上传。
已创建但尚未启动的 run 使用 `start <run-id>`；明确结束云端执行使用 `cancel <run-id>`。
中断本地 `watch` 只停止等待，不改变云端 run。
401 表示需要重新登录。

`status <run-id> --saved` 可只读重放已归档状态，不联网、不改旧产物。
摘要分开列出最近有效事件、心跳和采集时刻，缺少观测时间时明确未知；不使用文件 mtime 猜测。
traceability 没有显式记录时显示未建立关联，不能由 SDK 自报 passed 推导外部评测成功。
`status` 输出阶段摘要，`watch` 默认每 180 秒读取状态和增量日志，只在 PASSED、FAILED、CANCELLED 或 PAUSED 时收集证据、输出摘要并退出；可用 `--after-event` 跳过已处理的同一结果。
运行中无变化保持静默，PAUSED 表示需介入而非完成；运行中的计数不作为完整成绩。
观测超过 360 秒标为 stale，不据此推断远端已经停止。
平台曾将实际耗时返回为 0，因此终态摘要用 started_at/finished_at 计算 elapsed_seconds，并汇总测试状态；原始时长字段保留在 status.json。
`collect` 将状态、日志游标与分块、traceability 和 commit history 保存到 `runs/playground/<run-id>/`。
JSON 的凭据字段会脱敏，但原始日志仍可能包含 Agent 工具输出，继续由 Git 忽略。

这些接口来自当时的网站公开前端，可能随平台更新；此前实际完成网站登录、上传、启动、Demo 单项评测和证据下载。
云端环境与脚本实测见[并发与 API 报告](../../../reports/2026-09-20-playground-concurrency.md)，早期协议调查见[开发闭环调查](../../../reports/2026-09-20-development-loop.md)。
Playground 与 Competition、本地评测具有不同身份，具体参赛包的成绩以其冻结身份和正式结果为准。
