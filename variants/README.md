# Variant 状态

当前唯一活动实现为 [pi-team-mixed](pi-team-mixed/)，使用 Pi + Braid + SVC。
[pi-team-reviewer](pi-team-reviewer/) 在现有流程上加入独立验收角色；实验见[任务包](../tasks/acceptance-workflow/packet.md)。
后续开发与新实验默认围绕它进行，具体输入、模型接入和冻结制品由当次 task packet 决定。

| 实现 | 状态 | 用途 |
| --- | --- | --- |
| pi-team-mixed | 活动 | 当前开发及正式比赛基线。 |
| pi-team-reviewer | 实验中 | 对照原生独立 reviewer 的验收增益。 |
| pi-team-deepseek | 归档／停用 | 保留单成员配方的历史实现和结果。 |
| pi-team-glm | 归档／停用 | 保留单成员配方的历史实现和结果。 |
| pi-team-vv | 归档／停用 | 保留已有 V&V 对照，重新启用须明确安排。 |
| codex-base、codex-svc、pi-base、pi-svc | 归档／停用 | [原生 Hackathon 对照](native-hackathon/)，不属于当前 Braid 基线。 |
| raw Pi/Codex | 历史参考 | [原始基线](raw/)与结果查询。 |

归档保留现有路径、包和运行证据，不移除历史结果读取能力。
旧 experiments 清单和任务记录描述当时的实验，不构成继续派发的授权。
本次新基线见 [任务包](../tasks/hackathon-team-baseline/packet.md)。
