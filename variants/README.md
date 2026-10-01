# Variant 索引

I10 运行基线为 [pi-braid](pi-braid/)，I11 保留独立副本 [pi-braid-i11](pi-braid-i11/)，I12 保留 [pi-braid-i12](pi-braid-i12/)，当前 I13 在 [pi-braid-i13](pi-braid-i13/) 开发，均采用 Pi、Braid 与 SVC。每个 variant 独立维护流程、原生角色与材料；目录相似不表示它们只差一个开关。选择或创建实验先看 [实验导航](../experiments/README.md)，实际输入和运行授权归所属 task packet。

## 活动与实验实现

| 实现 | 状态 | 维护职责 |
| --- | --- | --- |
| [pi-minimal](pi-minimal/) | 独立原生 Pi 参赛实现 | GLM 主会话与 Kimi advisor，后台任务；无 Braid/SVC。授权与余额保护见 [任务包](../tasks/pi-minimal/packet.md)。 |
| [pi-braid](pi-braid/) | 保留的 I10 基线 | 原运行使用的冻结包与逐次恢复来源见 [I10 packet](../tasks/iteration10/packet.md)，目录源码不能替代旧制品身份。 |
| [pi-braid-i11](pi-braid-i11/) | 保留的 I11 实现 | 原生成、交付及评分来源见 [I11 packet](../tasks/iteration11/packet.md)。 |
| [pi-braid-i12](pi-braid-i12/) | 保留的 I12 人工介入实现 | 原冻结运行及暂停现场见 [I12 packet](../tasks/iteration12/packet.md)；Console 在开发侧，不装入制品。 |
| [pi-braid-i13](pi-braid-i13/) | 当前开发入口 | 独立维护当前生成、角色、工具与方法材料；已实现范围、待验边界和后续方案见 [I13 packet](../tasks/iteration13/packet.md)。 |
| [pi-braid-flash-team](pi-braid-flash-team/) | 实验实现 | 从最新 pi-braid 独立派生；GLM 根成员，Qwen/MiniMax 工作项成员；原生子角色保持来源模型。 |
| [pi-braid-kimi-root](pi-braid-kimi-root/) | 实验实现 | 从当前 pi-braid 独立派生；仅根成员使用 Kimi K2.7 Code，GLM/DeepSeek 工作项成员及原生角色保持基线。 |
| [pi-braid-coordinator](pi-braid-coordinator/) | 实验实现 | 根只协调，不写应用代码，也不作为后续工作项的可指派成员。 |
| [pi-braid-review](pi-braid-review/) | 实验实现 | 原生 Pi 独立最终验收角色及完成前委派流程。 |

coordinator 与 review 保留各自现有行为，没有随改名自动同步基线的新流程。模型、推理档位和技能选择以本次冻结源码与包为准，索引不维护另一份模型配置。

## 命名与更名关系

独立实现使用 `<engine>-<coordination>[-<workflow>]`。engine 表示 Pi/Codex 等客户端；coordination 表示 Braid 或原生委派；workflow 只用于值得独立维护的职责或生命周期差异。原生委派不等于单 Agent。

仅修改模型、供应商、预算、技能选择或普通提示词版本时，通常以实验 case 和冻结输入区分，不创建永久 variant。
I11–I13 是用户明确要求的迭代隔离副本，保留迭代后缀，不代表新增模型家族。Braid/SVC 共用源码仍会演进；I10 的隔离依据是冻结包和逐次热修复来源，不是声称整个依赖树已复制。由指令表达的协调或验收职责仍可能是真实工作流差异，不能仅按文件类型判断。

| 旧活动入口 | 当前入口 |
| --- | --- |
| pi-team-mixed | pi-braid |
| pi-team-k3-root-only | pi-braid-coordinator |
| pi-team-reviewer | pi-braid-review |

更名移动当前源码，保留旧 ZIP、manifest、journal 与 run 的原始名称。旧入口没有隐式执行别名；查询历史 variant 时不能把它替换成当前实现身份。Lite 配方现为 [pi-braid-lite](../experiments/pi-braid-lite/README.md)。

## 历史实现

| 原路径 | 家族与用途 |
| --- | --- |
| [pi-team-k3-root](pi-team-k3-root/) | pi-braid 家族的历史 K3 根配置及当时实现，K3 仍可用于后续指派。 |
| [pi-team-deepseek](pi-team-deepseek/)、[pi-team-glm](pi-team-glm/) | pi-braid 家族的历史单成员实现，归档停用。 |
| [pi-team-vv](pi-team-vv/) | pi-braid 家族的历史 V&V 实现，归档停用。 |
| [native-hackathon](native-hackathon/) | pi-native/codex-native 家族的 base/SVC 历史对照，使用原专用打包器。 |
| [raw](raw/) | pi-native/codex-native 家族的原始基线，保留原入口与查询。 |

家族是导航分类，不是可执行别名。历史实现的技能、分支、导出与清理流程可能不同，不代表当前基线的等价配置。

当前实验使用自带 key 的 `self_funded`；旧 pi-minimal 正式参赛记录保留历史身份，不恢复其自动接续授权。正式参赛须针对具体冻结产物取得新授权。新制品须符合按 Braid session 的预算保护，现行边界见 [AGENTS.md](../AGENTS.md#实验边界)与[预算与交付](../tasks/competition-budget/packet.md)。索引不记录某次成绩或“正在构建”等运行瞬态；历史结果与来源关系见 [官网运行总览](../tasks/competition-budget/packet.md#官网-hackathon-运行总览2026-09-26-核对)。
