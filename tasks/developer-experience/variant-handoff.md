# 来自 Variant 独立实现任务的交接

2026-09-23，用户在复核具体迁移材料后指出：“还不是时候，这背后其实是一个更巨大的问题”，要求 handoff 给 developer-experience task。
因此暂停独立 variant 的实施推进，由 DX 重新审视其上层问题与整体边界。
这不是源码开工授权，不是要求 DX 直接执行既有迁移计划。

## 已确认的需求与未确认的解法

用户已确认：每个 variant 应是可以独立演化的完整 Harness，不再通过共同配置模型生成。
动因是实验结构仍在探索；通用生成器限制实验空间，让改动相互牵连，并增加理解、调试与迭代成本。
接受有意义的重复，优先缩短 Coding Agent 从实验想法到实现、运行和解释结果的路径。
这并不禁止 Pi/Braid 的原生配置，也不要求复制这些上游的实现。

用户认可了独立 Harness 与共用实验设施的总体边界，但尚未批准具体源码迁移、旧入口退休、字段变更、依赖 lock 布局或新实验。
四份目录、build.py、支持模块提取和 mixed-first 次序都是上一任务的候选解法，应服从 DX 的整体分析，不当成固定前提。

## 可以直接复用的证据

| 事实 | 证据与影响 |
| --- | --- |
| 当前活动 variant 经两次投影进入共同执行器。 | `profiles.resolve → native_profiles.materialize → factory.generate/braid_request`；只移动 JSON 目录无法取得行为独立。 |
| 当前打包复制整个共享 harness。 | `scripts/package_agent.py:package`，并生成 `variants/factory/config.json`；构建入口参与 Harness 语义装配。 |
| 当前 local Runner 矩阵已经接受 `NAME=AGENT_ZIP`。 | `scripts/arc_matrix.py:build`；独立 Harness 不要求重写通用实验执行器。 |
| 指定诊断消费者不需要完整 effective profile 树。 | [消费者核实](../independent-variants/evidence-contract.md)：viewer/feedback/analyze 使用状态、原生会话和必要身份；历史 `official_matrix.freeze` 才直接遍历 effective profiles。 |
| 四组当前原生输入已实际物化。 | [独立预演](../independent-variants/rehearsal.md)：六份主 launcher、三十份角色文件；独立视觉 URL 与 key 环境变量分支也已核对。没有模型、Braid 或 bench 执行。 |
| 迁移不能只搬主指令。 | 预演确认 pi-subagents、observer、角色 skill roots、browser wrapper/Chromium 及运行路径都属于实际接入依赖。 |
| 诊断布局仍有既有缺口。 | 当前 viewer 默认发现范围与 local_experiment 嵌套目录不完全一致；保留证据格式不等于开发者已能自然查到新运行。 |

预演脚本与输出位于 `runs/independent-variants/rehearsal/`，不需要重新铺开原始 rollout。
四组输入基线只证明当前原生材料可生成，不能证明新的独立目录、真实协作、交付或评分已经通过。
旧 quota 错误是历史证据，不据此断言当前模型服务仍不可用。

## 与 DX 当前方案的交汇点

DX 当前 design.md 把“Factory 能力装配”和“Factory 生成”列作共同维护责任，并建议共同能力供本地与参赛入口调用。
这与用户要求各 variant 独立演化之间存在需要重新判断的边界：哪些确实是稳定基础设施，哪些是尚在探索的实验实现，不应先假定存在一个共同生成核心，再调整它的接口。

建议 DX 以具体变更来检验整体设计：Coding Agent 新增一种结构不同的 Harness，或者只改变其中一组的协作方式，需要理解和改动哪些部分、准备哪些依赖、通过什么接口获得首次可信反馈；其他组为什么能不受影响。
这只是交接方提出的问题方向，不替用户给“更大的问题”下最终结论。
进一步的边界与依赖诊断、方案讨论由 DX 承接。

## 状态、权限与材料归属

- 独立 variant 任务只增加 task packet 和无模型预演材料，没有修改产品源码、提交或启动模型实验。
- [该任务 packet](../independent-variants/packet.md)已标记暂停实施推进；其 technical/verification/plan 是参考提案，不应自动执行。
- [SVC Corpus 审查](../svc-corpus-review/packet.md)继续开放；[SVC skill 接线](../svc-skill-integration/packet.md)的剩余验收也未关闭。
- 工作区含多个任务的未提交改动；不得整包提交或回退。历史 ZIP、run、journal 保持原身份。
- DX 原有只调查/设计、无源码实施和本侧会话不使用子 Agent 的授权不变。交接来源的两个子 Agent 只提供既有证据，不替 DX 宣称完成其独立预演。

DX 维护上层问题与方案的权威说明；本文件保存交接事实和入口，不另起第三份并行架构设计。
