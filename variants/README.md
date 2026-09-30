# Variant 索引

当前开发基线为 [pi-braid-i13](pi-braid-i13/)，I12冻结运行及I10运行基线保留，采用 Pi、Braid 与 SVC。每个 variant 独立维护流程、原生角色与材料；目录相似不表示它们只差一个开关。选择或创建实验先看 [实验导航](../experiments/README.md)，实际输入和运行授权归所属 task packet。

## 活动与实验实现

| 实现 | 状态 | 维护职责 |
| --- | --- | --- |
| [pi-braid](pi-braid/) | 活动基线 | 当前持续开发流程，develop/main 集成、自动化整体验收和真实完成后的交付。 |
| [pi-braid-i13](pi-braid-i13/) | 当前开发，尚未冻结实验 | 独立副本承载子Agent简化、完整工具与三层委派；其它批次按[I13 packet](../tasks/iteration13/packet.md)推进。 |
| [pi-braid-flash-team](pi-braid-flash-team/) | 实验实现 | 从最新 pi-braid 独立派生；GLM 根成员，Qwen/MiniMax 工作项成员；原生子角色保持来源模型。 |
| [pi-braid-kimi-root](pi-braid-kimi-root/) | 实验实现 | 从当前 pi-braid 独立派生；仅根成员使用 Kimi K2.7 Code，GLM/DeepSeek 工作项成员及原生角色保持基线。 |
| [pi-braid-coordinator](pi-braid-coordinator/) | 实验实现 | 根只协调，不写应用代码，也不作为后续工作项的可指派成员。 |
| [pi-braid-review](pi-braid-review/) | 实验实现 | 原生 Pi 独立最终验收角色及完成前委派流程。 |

coordinator 与 review 保留各自现有行为，没有随改名自动同步基线的新流程。模型、推理档位和技能选择以本次冻结源码与包为准，索引不维护另一份模型配置。

## 命名与更名关系

独立实现使用 `<engine>-<coordination>[-<workflow>]`。engine 表示 Pi/Codex 等客户端；coordination 表示 Braid 或原生委派；workflow 只用于值得独立维护的职责或生命周期差异。原生委派不等于单 Agent。

仅修改模型、供应商、预算、技能选择或普通提示词版本时，通常以实验 case 和冻结输入区分，不创建永久 variant。由指令表达的协调或验收职责仍可能是真实工作流差异，不能仅按文件类型判断。

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

实验均停用参赛额度，新制品须符合按 Braid session 的预算保护，见 [预算与交付](../tasks/competition-budget/packet.md)。索引不记录某次成绩或“正在构建”等运行瞬态；历史结果与来源关系见 [官网运行总览](../tasks/competition-budget/packet.md#官网-hackathon-运行总览2026-09-26-核对)。
