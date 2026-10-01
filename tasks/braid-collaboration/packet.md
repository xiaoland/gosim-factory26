# Braid 协作身份与共同 Git 仓库

2026-09-25 本轮目标：补齐具体 Agent 身份与共同 Git 仓库语义，使指派、发布、PR 合并及完成声明有清晰一致的依据。
用户已确认产品方向，并要求梳理本轮事项。2026-09-25 用户在技术与验收方案呈现后明确回复“可以开工”；本轮已进入实现与验收，源码提交仍待单独指示。
最新授权为用户原话：“‘SVC：打磨通用反馈闭环’先不做；其它的没问题，你可以继续推进了。”
技术设计及只读预演已完成；SVC 改稿移出本轮，沿用现有已实现的 skills 内容。
前序原始调查继续保留在 [身份方案](../braid-usability/agent-identity.md)与[合并反馈](../braid-usability/merge-feedback.md)，本页负责本轮范围、顺序与授权。

## 本轮工作

| 工作 | 已明确的方向 | 下一阶段需收敛 |
| --- | --- | --- |
| 指派与成员身份 | 只有指派工作；选择 profile 后返回具体 Agent 名。负责人、当前会话、评论与通知统一身份，Agent 接口不用 UUID。 | 名字何时分配；重复指派、改派、恢复和上下文重建的身份；配置目录与具体成员的区别。 |
| 共同 Git 仓库与 PR 合并 | 共同仓库存放已发布分支/提交；Agent 拥有自己的本地工作状态。合并推进共同目标分支，不检查或 reset 他人的工作区。 | 核实 bare origin + 独立 clone 候选；根/子 Issue 与 PR 的初始化、发布、ready、合并、取得更新、恢复；明确 PR 所引用的版本。 |
| Braid 操作反馈 | 返回真实指派/合并结果、相关成员与对象事实，帮助 Agent 使用已有工作方法。 | 与前两项同步收敛指引和 CLI 返回文案；不改 SVC，不向 Braid 转移关单、验收或协作方法。 |
| pi-team-mixed 接线与验收 | 串通请求、成员启动、本地 origin、最终集成提交、冻结包和原始证据。沿用真实 benchmark 与生成应用验收。 | 修改与本地协作冲突的“禁止 push”文案；交付读取共同仓库指定 ref；冻结输入与本轮具体实验安排在开工复核中明确。 |

身份与 Git 仓库设计可以独立调查，随后共同落实到 Agent 可见接口。
不要求预设任务图、由 Braid 判断 Issue 是否完成，或通过增加成员命令扩大操作模型。
权限、沙箱、原生子代理生命周期及模型配方不因本次诊断扩展。
SIGKILL 原因保留为未解决的独立证据问题；不能用猜测的 OOM 或自动重试替代诊断，也不阻塞已证实问题的设计。

## 已有成果与本轮关系

[Hackathon 能力任务](../hackathon-capabilities/packet.md)已完成五个 SVC skills、题目候选技能与 MCP 接线和材料验收，真实采用与得分尚未验证。
本轮复用这些成果，在 Braid 变更完成后重新构建匹配的 runtime 和冻结包；已有技能包不包含尚未实现的身份/合并修正。
技能收益与协作修正若在同一实验中验证，结论应报告组合效果，不声称测出了各改动的独立贡献。
[SVC Corpus](../svc-corpus-review/packet.md)仍开放，后续真实运行需辨别材料提供、实际选读、影响行动三个层次。
原冻结实验由原监控继续负责，新的设计和包不改变其输入与记录。

## 验收要回答的问题

1. 同配置的多个工作项是否返回并使用不同成员名，Agent 能否正确识别自己和协作者；恢复/上下文重建是否沿用该成员身份。
2. PR 是否引用实际发布的提交，合并是否只更新共同仓库与对象结果；其他 Agent 的本地修改能否继续保留并由本人同步。
3. 实际遇到失败时，Braid 是否准确反馈未发生的操作与对象现状；Agent 对失败的处理作为过程观察，不把本轮描述为已实现 SVC 方法修正。没有发生失败的运行不能声称验证了失败恢复行为。
4. 最终应用验收与官网评分是否针对实际导出的集成提交，完整 bench 的得分与可取得的逐例证据是什么。

不新增 Factory/开发设施/Corpus 测试或换名探针；验收以已授权的真实操作、模型运行、生成应用反馈及官方评分为依据。
与旧 GitHub 1/100 比较时同时报告过程差异、评分及证据限制，不把工作项数量当作协作成功。

## 推进顺序与下一步

已形成且交用户复核的[技术方案](design.md)与[验收方案](verification.md)。用户以“可以开工”授权按此范围推进 Braid 身份、共同仓库/合并、Factory 接线、Linux 打包及完整正式 Hackathon 验收；保持现有模型/技能材料。
只读调查分工：identity_design（gpt-5.6-luna / high）负责[身份分配与展示](identity-preflight.md)；git_design（gpt-6-sol / medium）负责[Braid 共同仓库与 Git 路径](git-preflight.md)；主 Agent 收敛 [Factory 导出、打包与指引](factory-preflight.md)及整体方案。
已收敛的关键接缝是：assign 同步预留公开成员名；worker 继续按内部配置匹配；共同仓库与每工作项 clone 分离；Factory 的历史发布、提交解析和归档统一读取 origin。
当前实施分工：identity_impl（gpt-5.6-luna / high）负责 Braid 具体成员身份；factory_origin（gpt-5.6-luna / high）负责活动 variant 三个交付消费者、指引和证据接线；主 Agent 负责 Braid origin/clone/合并与最终集成。两位工作者不提交，主 Agent 核实接口与构建结果。
实现顺序：成员身份与 origin/clone/merge 并行落地 → 接合 root 初始化、恢复、ready 和最终导出 → 编译 Linux runtime 与打包 → 同一冻结包正式 Hackathon GitHub、Sheet 两题 → 整理原始证据和结果后报告。
范围内可修复的问题持续处理；若平台或凭据等外部条件真正阻断，保留原始错误并向用户报告。
源码提交单独以用户明确指令为依据。

## 本轮执行现场

2026-09-25 已完成 Braid 成员身份、共同 bare Git origin、独立工作项 clone、PR 发布/合并与 Factory 交付接线。`cargo check`、Linux runtime 编译、`pi-team-mixed` 打包、Python 语法检查及 diff 检查通过；真实协作与得分仍待本轮官方运行验证。
冻结包为 `runs/braid-collaboration/20260925-pi-team-mixed-origin.zip`，SHA256 `b17b73633ae72ab933d9a1eec223444cd70cc00c466379702800f1b845f3a8fd`。
官方 journal 位于 `runs/braid-collaboration/20260925-hackathon/official`；submission `c947d09ca69e`，`official_evaluation`，GitHub run `44db16c4b085` 已启动，Sheet 尚待同一控制器按顺序创建。
旧 submission `43b59da83877` 的 Sheet run `17bffdd4a8b0` 仍为 `PAUSED`，平台原文 `Execution paused by user request`；本轮没有恢复、取消或修改它。原 Competition 控制器额外要求前一 snapshot 的两题全部完成，这阻断了本轮已授权实验；已移除该跨快照限制，保留本快照内逐题执行及远端写入防重。官网接受了新 snapshot。
独立监控每 900 秒只读观察终态或明确故障；完整两题评分后按验收方案报告并停止，不启动下一轮。

2026-09-26 更新：上述首次官网运行在生成阶段中断，没有进入 GitHub 测试；Sheet 因旧暂停 run 占用而启动失败。原始过程、评分边界和修复依据见 [首次运行结果](results/44db16c4b085.md)。已从官网取回原生 bundle，确认共同 origin 只有空初始提交；8 个 Issue Agent 同时活跃，编译进程和一个 Pi 会话先后被系统杀死，确切 kill 来源仍未证实。已把 Factory 根任务改成按依赖分批指派、共享基础单一负责人、根 Agent 之外最多三个同时指派的 Agent；空交付现在给出明确错误。随后又确认一个 Agent 曾把已分配的成员名 `deepseek-4` 填入 `--assignee`，收到含糊错误后让 PR 保持未指派；Braid Agent 指引和错误现改为列出可指派 Agent 名称并解释成员名的用途。
仅含 Factory 修正的中间包 SHA256 `d1b206b16ca270e4f5b8ff7deea5fc7f655fce9fca755677ebf0f864bb94f470`，journal `runs/braid-collaboration/20260926-hackathon/official` 已 prepare，**均未向官网上传**。最终候选包 `runs/braid-collaboration/20260926-pi-team-mixed-collaboration.zip` 的 SHA256 为 `3440b95605ba7b5a3df606438becff3d2b2f0741673d6f32f5b5d4d29b527609`；官网 submission `59bc17b44cb1`，journal `runs/braid-collaboration/20260926-hackathon-v2/official`，GitHub run `b77e4357a4e1` 已启动。
用户明确同意正式关闭旧 Sheet run `17bffdd4a8b0`，但官网在 `PAUSED` 状态报告 `can_cancel=false`，`/cancel` 返回 HTTP 409；报告 `can_resume=true`，但 `/resume` 返回 HTTP 404 `Submission workspace is not available`。操作现场在 `runs/issue-decomposition/20260925-hackathon/official/manual-actions/stop-old-sheet-20260926/`。旧 run 未改变，且占用该题启动槽；新 Sheet 的执行需要平台修复旧 run 状态。GitHub 独立运行与监控继续。

2026-09-26 GitHub run `b77e4357a4e1` 已完成生成、构建与评分，官方为 4/100（4 通过、96 失败）；[结果与证据边界](results/b77e4357a4e1.md)。五个 PR 全部合并，Factory 导出最终集成提交，说明旧 WIP 交付问题已消失；但 Agent 自验收与官方浏览器场景严重不一致。官网没有逐例失败结果，暂不能确定主要失分缺陷。按用户指示，暂停可追溯性方案及下一轮实验；Sheet 外部阻塞仍在。

用户拒绝把 Web 题型专属验收规则写入通用 Factory 指引，要求评估更强的根 Agent 模型。[三模型同输入探针](results/model-validation-probe-20260926.md)显示 GLM、Kimi K2.7 Code、Kimi K3 在简短事实摘要上都选择补齐最终提交的浏览器验收；这不能取代长时完整运行。

随后用户明确批准新增 K3 根 Issue Agent 的独立 variant 并重跑试题；该项是模型对照实验。用户同时要求提出不同于题型专属规则的通用解决方案；[新上下文结果验收提案](acceptance-design.md)待复核，尚未批准实施，不与 K3 对照混入同一冻结包。
