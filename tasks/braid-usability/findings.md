# 调查与产品方向

## 实施前的源码观察

| 观察 | 实现入口 | 含义 |
| --- | --- | --- |
| 每轮输入附带 state 和 writer-turn，命令默认不自动取得它们 | `sources/braid/src/group/dispatch.rs:451`；`sources/braid/src/cli/mod.rs:12`、`:500` | LLM 承担运行身份搬运和更新成本。 |
| writer 查询关联 turn、session、assignment、agent，检查失效与重建状态 | `sources/braid/src/objects.rs:145` | 参数不是单纯的作者名称；不能只删校验，也不能把初始 turn 固定放入长期进程环境。 |
| 协作提示词解释 writer 失效、中断、finalization，并预载完整 CLI 清单 | `sources/braid/src/group/provider.rs:63` | 用户可见工作项操作与内部调度机制混在一起，说明负担可以直接确认；它是否造成某次失败尚需 run 证据。 |
| variant 同时设置 issue/pr 默认 profile | `variants/pi-team-mixed/run.py:20`；其它三个 variant 同构 | 配方预设了后续工作项的默认分工。 |
| 创建对象省略 assignee 时选择全局默认 profile | `sources/braid/src/objects.rs:266`–`:285` | 子 Issue 同样会继承全局默认，并非由父 Issue 明确选人。 |
| create 支持 assignee；edit 支持 remove/add assignee，CLI 路径允许跨工作项修改 | `sources/braid/src/objects.rs:459`–`:553`、`:940` | 能力已有，不应重新建一套派工系统；注意不要把只允许自身修改的另一个内部 set_assignee 路径误认成 CLI 限制。 |

## 已有实验的证据边界与本轮纠偏

用户指出“没有发挥作用”指退化成一次性设计交接、实施、复验流水线，不是声称没有执行任何 Issue/PR 命令。
上一答用“存在设计评论和验收”回应这一点，判断标准错位。
应判断 Braid 在任务中承担了什么仅靠一次性交接难以承接的上下文或协作需求，而不是是否完成对象流程。

本轮一 run 一分析者的定向观察见 [旧 team BookStack](run-team-bookstack.md)、[GLM BookStack](run-glm-bookstack.md)、[V&V BookStack](run-vv-bookstack.md)。
这些观察不把“一 Issue + 一 PR”本身判为错误，也不把更多评论或拆分当作修复目标。

三个 run 都是一个 Issue、一个 PR、三条顶层评论。
旧 team 一次交接约 10 KB 方案，V&V 一次交接约 4 KB 方案，随后是完成通知与验收合并。
GLM 根 Issue Agent 已经实现，才建 PR 让另一个 Agent 复验，说明设计/实施的产品职责也未实际落到对象使用中。
三例未观察到评论推动的设计澄清或修订；不据此推断更多协商必然提高分数。

两个值得带入设计的问题：旧 team 的受检提交 `d74c507` 与最终合并 head `7e579034` 不同，工作已有变化但协作结论没有绑定更新；GLM 收尾先 resolve 成功，接着另一次 resolve 遭 stale writer，说明维护上下文的正常操作暴露了运行协议负担。
后者既不能称“没有使用上下文编辑”，也不能由它推断整个 run 未协作的唯一原因。
这些证据提示从“当前设计、待解决问题、变化和验收依据如何成为可持续更新的共享工作上下文”重新设计使用方式，避免仅将一篇设计稿转交另一会话。

[本地逐 run 过程报告](../../reports/2026-09-23-local-agent-process.md)记载设计评论、PR 实施、自验、合并，也记载错误 seed 决定被写入 PR、API 检查被上升为 UI 通过、验收较早提交等问题。
它支持“流程完成不代表有效设计与验收”，不支持“Braid 完全没被使用”，也不构成 Braid 对成绩的消融因果证据。
现有报告没有系统统计 comment 回复如何改变决策、hide/resolve/正文更新如何改变后续会话，不能据此声称这些机制完全未使用。
官网早期报告另有原生会话缺失，不用应用得分补造协作过程。
本轮选择上述本地批次中的三个明确 run 定向核对，不声称它们就是用户亲自查看的全部 run。

## 调查后形成的方向

1. Agent 直接使用 `braid issue/pr/comment …`。
   宿主自动提供运行位置与调用身份，作者、工作项归属、失效会话判断留在运行时。
   优先考察 provider session 绑定的环境或启动包装，避免 Agent 手写参数。
   长期进程不会随每轮 dispatch 自动更新环境，不能简单把 writer-turn 改成启动环境变量便宣布完成。
   会话替换、迟到工具调用和继承环境的原生子代理需在接口设计时厘清，不让 Braid 接管 Pi 子代理生命周期。
2. variant 只选择根 Issue 的启动成员，并提供成员目录。
   后续 Issue/PR 由 Agent 使用 assignee 选择成员；省略时建议保存为未指派，不自动激活默认成员。
   同一成员可承接多个工作项，不要求制造角色差异，也不强制拆子 Issue。
3. 初始上下文提供当前工作项、成员能力与少量协作入口，完整命令语法按需从 help 取得。
   保留 Issue 设计、PR 实施、comment 异步讨论与上下文编辑的产品行为，移除需要 Agent 理解运行器内部状态的说明。
   正文更新和 hide/resolve 导致会话重建是否存在实际摩擦，应凭对应命令和续接证据判断；当前不据此改变既定产品语义。
4. 验收关注一次真实任务中信息是否被消费、决定是否影响执行、交付判断是否依据有效证据。
   评论数、Issue 数和上下文编辑次数不是成功指标，低使用量本身也不是缺陷。
   接口改善可以直接观察参数误用是否消失；分数收益仍需经过授权的 benchmark，不能靠代码审查宣称。

上述方向已形成获批设计并实施，具体变化和真实验收进度以 [packet](packet.md) 为准。
调查中的源码行号指实施前位置，不代表改动后的现状。
上述前三项接口改进可降低负担，但不能单独证明解决了 Braid 的价值问题。
保留既定设计与实现职责分离，不将其机械等同于新建两个阶段目录，也不建立强制协商轮数或额外审批状态机。
