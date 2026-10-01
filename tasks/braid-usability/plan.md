# 实施计划与开工影响

## 已授权的边界补正

2026-09-24 用户明确“你可以应用这些修正了”，并限定自主工作流程仅用于 Braid Factory、“像人类一样协作”只保留一句。
当前增量按 [职责边界](run-boundary.md) 实施：独立 Agent 处理 Braid local/objects/evidence 和 Braid 规范；主 Agent 同时处理 Factory 导出、Braid 原生提示、成员指令及 Factory 规范。
接口提前收敛为 quiescent/blocked/failed 与本次 ref 的 commit；Factory 自己冻结请求指定的 ref，不消费协作状态作为交付许可。
实现之后使用既有编译和 Linux 构建，再以一个新冻结 mixed ZIP 完成 Lite 两题，沿用逐 run 独立分析；旧运行保持原样，无需新测试设施或协议模拟。

以下保留此前易用性改造的实施准备，当前增量以本段和边界文档为准。


状态：设计及验收方案已复核，三份独立预演完成；主 Agent 曾在缺少独立开工确认时错误推进。用户现明确不必停止或撤回，继续依据与纠正记录见 [packet](packet.md)。
用户进一步明确：V&V 方法归 SVC Corpus，Braid 不承载 V&V 方法指引。

## 预演后的决定

| 项目 | 收敛决定 | 依据 |
| --- | --- | --- |
| 调用身份 | 在 `provider_sessions` 增可空唯一 `cli_binding_id`；内部 CliContext 经环境传递 state 与 binding。进程创建前生成，provider ID 返回后在原注册事务绑定 | [身份预演](rehearsal-identity.md) |
| 恢复与替换 | 真正恢复前清除旧 binding，成功登记新 binding；活句柄快返不轮换。reset/reassign 沿既有生命周期拒绝旧执行 | 同上 |
| 正常写入 | 在对象写事务中解析 binding 和当前执行，保留作者与工作项归属；评论的 writer_turn 取解析结果，不再取 CLI 参数 | 同上 |
| 明确分工 | 新请求只含 `root_profile_id`；移除对象默认补人和 store NULL 自动认领；未指派显示为未指派 | [指派预演](rehearsal-assignment.md) |
| 重开工作项 | sleeping 组也参与取消/改派清退；reopen 仅恢复匹配当前 assignee 与 assignment_revision 的组，否则按明确指派新建执行 | 同上 |
| 评论整理 | hide/resolve 多 ID，一次事务先校验，再更新并发出现有事件；同 ID、同 resolve thread 去重 | [上下文预演](rehearsal-context.md) |

binding 是执行实例身份，不加哈希层、服务或新的令牌系统。
Pi `start_turn` 里缺进程时自行 spawn 的回退应收敛到既有 unavailable/恢复路径，保证新执行实例经过唯一的 binding 注册入口；不接管 Pi 内部子代理。
旧请求的 `defaults` 格式不作为新二进制的运行兼容范围，旧封存记录继续可读，旧未完成实验继续使用原冻结二进制与状态目录。
旧库已记录的非 NULL assignee 保留；不试图区分它过去来自明确指派还是旧默认，也不重写历史数据。

## 线性实施顺序

1. **记录开始点。** 取得开工同意后先仅提交本任务包，记录 Factory/Braid/SVC 源码与工作区基线。
   Braid 当前 `src/config.rs`、`src/provider/codex.rs`、`docs/20-product-tdd/app-server.md` 有其它任务未提交修改，必须保留；同文件只提交本任务新增部分，不夹带供应商接线改动。
2. **贯通隐式身份。** 先落 schema、CliContext、SessionFactory/CreatedSession 和四类 session 创建/两类恢复入口，再接 Pi/Codex 进程环境与 PATH，最后切 CLI 对象事务和删除 dispatch 身份前缀。
   注册失败沿既有清退路径结束新 handle；不得留下无身份的新执行。
3. **贯通显式指派。** 根初始化原子写 root assignee，之后改 create、assignment candidate/begin、claim/resume、unassign/reopen，消费遗留的 NULL 激活事件，保持最终 incomplete/交付规则。
   同步四个独立 variant 的 ROOT_PROFILE_ID 与请求字段。
4. **评论整理和工作指引。** 完成多 ID 事务与 CLI 参数，再精简 Braid 工作项指引及六份 variant instructions 的重复协议。
   保留原生委派和无人值守指引；V&V variant 仅保留提示查阅 SVC 的入口，不在 Braid 复制 V&V 方法。不改 SVC skill、模型、工具或角色配方。
5. **构建、冻结和真实实验。** 用现有 WSL Docker 构建路径编译 Braid、打包一个 pi-team-mixed ZIP；两个 Lite task 共用该冻结 ZIP，并行度 2。
   跑完 Keep 与 BookStack 的完整生成和评分，保留失败原文与对象、原生会话、评测证据，再由一 run 一分析 Agent 诊断；完整 bench 后报告。

实施时共享的 `objects.rs`、`store/mod.rs`、CLI 和生命周期接口由一个执行者按顺序修改，避免多个 Agent 同时改这些文件。
主 Agent 持有接口决定与整合；可并行委派六份 instructions 和对应文档的改稿，以及 WSL 既有资源准备，给定明确文件所有权。
不得让多个 worker 各自增加一套身份或默认分派兼容层。
预演是前置排障，不以“独立 Agent 看过代码”替代验收。

## 已核实的实验入口

2026-09-24 从 macOS 通过 SSH 只读检查 WSL：

- 主机 `wsl.win-ws.localhost`，工作树 `/home/yyh/Development/factory26`。
- 官方本地 Runner 副本实际在 `/home/yyh/Development/factory26-official-local/raw-baseline-20260923-wsl/runner/`，包含 `local_submit.py`；旧文档的同级 `runner/` 不存在。
- 输入在 `/home/yyh/Development/factory26-official-local/platform-inputs/arc-bench-lite/{keep,bookstack}/`，各有 requirements/tests/source 记录。
- 已有镜像 `arcbench-local-submit:latest`，当前 image ID 为 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`；不重装 Runner/浏览器、不重建该评测镜像，Harness 自身正常构建仍需进行。
- WSL `~/.config/factory26/llm.env` 已存在；只检查存在性，未输出密钥、未作模型请求。沿用比赛连接与既有 pi-team-mixed 配方，不切换其它任务的自购网关。

Runner 副本不含 `.git`，冻结时记录实际输入与 Runner 文件身份，不伪造 Git revision，也不声称本地分数与官网已校准一致。
使用现有 `arc_matrix.py` + `local_experiment.py` + `arc_bench_adapter.py`，启用生成/评测分离；新矩阵与结果目录为 `runs/braid-usability-lite/<本次时间>/`，不覆写已有 ZIP 或 journal。
Lite 是两题一 bench；此轮一个 variant、两个 task run，不将一题完成称为整个实验完成。
实际配置、网络/API可用性和容器可达性在正式运行中观察；本次只读资源检查不能代替这些运行事实。

## 验收边界与停止条件

不增加或运行 Factory、基础设施或 Corpus 测试，也不以 smoke/fixture/模拟探针替代。
正常编译与制品构建服务于真实交付；应用自身验证和官方本地 Runner 评分沿用已批准方法。
Pi 内置 bash 的环境继承已从本机安装的 0.85.1 源码核实，原生子代理仍以实际会话证据为准。
Codex 官方 [配置参考](https://developers.openai.com/codex/config-reference/) 提供 `shell_environment_policy.inherit` 与 `set`；这支持存在原生环境接线能力，但没有证明本机二进制与 Braid 组合已实际通过。
本轮 pi-team-mixed 完整 bench 验收 Pi 路径；Codex 分支同步接线与构建，实际工具继承仍标为未运行验证，不扩展成额外 Codex variant 或模拟测试。

模型/工具配置之外的并行任务不得悄悄进入本次冻结输入；若必须改变实验配方、重写调度架构或更换验收题目，回到用户复核。
已授权实验中的可修复代码/运行问题继续解决；只有实质范围变化、外部阻塞或证据缺失且无法补齐时暂停。
合法低分不是停止修复设施的借口；完整低分要如实报告，不追加下一轮优化或重跑掩盖。
首次完整评分后再总结：参数负担是否消除、分工是否由 Agent 选择、工作项是否承接了必要的信息变化，以及哪些能力仍未观察。
