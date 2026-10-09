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

Local I15 同任务、同原生 scope 的 `restart --keep-data`，在执行宿主和远端目录不变且没有选择 snapshot 时，直接在该宿主保留来源终态 data。执行器先核对精确来源容器已停止、Docker daemon 身份和远端完整保存回执，再将全部 data 独立复制到新 run 的 staging 目录后发布；使用 copy-on-write reflink 或普通复制，不使用硬链接或共享可写来源目录。新程序和冻结输入仍正常装配，只有 SDK 的 requirements/.arc 会刷新，不以控制端空工作区或官方初始模板覆盖继承应用及原生状态。路由校验所需的小型 routing-snapshot 单独回收。

该路径的 `restart-remote-save.json` 是执行宿主保存证明，不表示 Mac 已收回完整 data；`restart-data-copy.json` 记录新远端独立副本。来源现场仍保留，后续终态保存和评测沿原消费者进行。跨宿主、不同任务或指定 snapshot 仍使用既有完整数据回收与迁移路径；不绕过停止、保存或原生身份约束。


自管 Docker 的 pause/resume 保持同一次执行，Hosted 不支持。疑似停滞先有界读回已有事实；控制前说明目标、实际生命周期、动作目的和可能损失。平台 can_resume 字段本身不证明原生进度可以恢复。

当前 CLI 没有 checkpoint、recover 或 prepare 命令。旧 schema3/4 的 writer、capture、prepared 及 legacy-terminal-export 合同归[历史恢复说明](history/recovery.md#旧-schema34-checkpoint-与-prepared-合同)，只由来源冻结执行器解释，不自动接入当前 run。Pi 重试和后台作业的原生边界见下节。

冻结应用可以独立评价，不必恢复原生成；在对应评测授权内使用 `lab evaluate RUN --kind official`，准确记录产物和非正式评分身份。阶段评分不进入仍在生成的 Agent；正式参赛须由参赛 Agent 实际生成，不能用重放替代。平台费用与提交身份见[平台与制品](competition.md)。

## Pi 原生重试与终态边界

Pi 在调用 `agent_end` 扩展前通过同一原生判定生成 `willRetry`，扩展与 RPC 监听方收到相同值。可重试错误仍沿已有次数和退避配置执行；PBB 和 subagents 此时不等待后台作业完成，也不把跳过等待记为完成。最终模型错误保留具体响应、已完成结果与 active 作业引用，不自动继续队列触发另一轮推理；最终 `agent_settled` 才由 Braid 解释为失败。成功 stop 的必要后台收口保持原行为，cleaner 工具仍须正常响应、校验通过后提交 receipt。

最终错误不会停止已经启动的作业。原生归档中的 `subagent-terminal-background` 与 `background-bash-terminal-work` 保存所属会话和作业引用；subagent 结果文件继续保留，PBB 已完成结果以不触发推理的消息保存。后续会话关闭沿原取消与持久化契约处理，接续时不能将作业引用当作已成功的检查点。代理 `upstream_headers_timeout` 仍表示未收到响应头，不能证明供应商没有执行或计费；此修复不增加跨供应商自动重放。
