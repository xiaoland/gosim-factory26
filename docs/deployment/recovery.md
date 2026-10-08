# 工作区恢复入口

恢复操作先明确输入、来源身份、当前停止事实及本轮授权。设施修改和模型执行是两个授权范围；已有评分、目录或快照不能自行成为下一次运行请求。

本页是当前恢复入口。旧 checkpoint、prepared、ARC attempt 和官网 journal 的详细字段合同保留在[历史恢复合同](history/recovery.md)，不作为当前命令来源。

<a id="当前-checkpointprepare-与停止门控"></a>
## 当前 run 的停止与接续

当前 run 使用下列公共接口，适用源码和部署验收状态见 [Lab](../../lab/README.md)与[设施任务](../../tasks/finals-experiment-loop/packet.md)。新执行接线仍在验收中，不能用旧执行器的恢复证明代替新路径的实际反馈。

```sh
python3 -m lab status RUN --json
python3 -m lab stop RUN
python3 -m lab restart RUN --keep-data --task TASK
```

stop 只请求停止指定执行，停止结果、完整 data 回收和日志保存分别取证。`restart RUN --keep-data` 先停止并保存来源 data，再装配同 variant 程序创建新 run；相同 task/需求版本接续原生状态，新 task 保留应用与历史并创建新的原生任务状态。来源不完整时记录具体缺失和可继续范围，不把应用或 Git 备份说成完整检查点，不用静默 fresh run 替代失败接续。省略 `--keep-data` 的 `restart RUN` 明确从题目基线重跑，不继承工作区或原生进度；旧现场仍被保存。

自管 Docker 的 pause/resume 保持同一次执行，Hosted 不支持。疑似停滞先有界读回已有事实；控制前说明目标、实际生命周期、动作目的和可能损失。平台 can_resume 字段本身不证明原生进度可以恢复。

当前 CLI 没有 checkpoint、recover 或 prepare 命令。旧 schema3/4 的 writer、capture、prepared 及 legacy-terminal-export 合同归[历史恢复说明](history/recovery.md#旧-schema34-checkpoint-与-prepared-合同)，只由来源冻结执行器解释，不自动接入当前 run。

冻结应用可以独立评价，不必恢复原生成；在对应评测授权内使用 `lab evaluate RUN --kind official`，准确记录产物和非正式评分身份。阶段评分不进入仍在生成的 Agent；正式参赛须由参赛 Agent 实际生成，不能用重放替代。平台费用与提交身份见[平台与制品](competition.md)。

## 历史来源

[旧冻结恢复、应用重放与监控](history/recovery.md)保存 operation/Competition、旧 ZIP 修复、来源停止和大材料接续的完整原流程及错误。它们只适用于对应冻结执行器和原来源，不作为 schema3 新 writer 的命令推荐。新观察只有一个 owner；status/monitor 只消费其保存事实，不另建旧 collector，详见[执行状态](../../lab/exp/execution.md#查询保存事实)。
