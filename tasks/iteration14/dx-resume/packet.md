# I14 GitHub：DX 新基线接续

2026-10-02。用户在实验DX交付后明确：“实验DX改进完成了。现在我们继续推进。”结合已授权I14实现、实验启动与热恢复，本阶段继续配置、实际准备并接续GitHub；Sheet暂停。源码及恢复采用DX提交eef231b1的新lab.exp入口，不使用已退役旧writer，不静默覆盖原冻结记录。

## 范围与决定

四variant为baseline、cleaner、reviewer、e2e。baseline此前用户暂停，先保全与准备，不自动解除其暂停；cleaner已有完整停止快照，优先保留原进度；reviewer当前paused，须同样保全与核对；e2e尚未开始，可独立准备。原GitHub需求沿旧冻结输入，不混入新增Stage或隐藏评分反馈。每生成2GiB/2CPU，共享五槽；需要新的Docker准入权交接，不能从无running容器推导旧owner已退役。

模型配方沿最新决定：GLM-5.3-Flash的成员、cleaner、视觉及e2e走普通Qwen，Kimi K3走自有Kimi，其余走Qwen Token Plan。三组凭据由.secrets/models.env取得，不输出key、不回落ARC；默认根Flash，I13两组两题正式均分领先10pp条件尚未具备，不擅自切根或替换模型ID。新生成逐模型拆分native provider；旧retained恢复能否保持会话/profile身份需真实材料核对。

应用完成后每题独立冻结并按原self_funded/比赛额度关闭取得官网重放成绩；生成与评分费用分别保存。原Flash/GitHub运行、唯一Console与既有采集不改，新的实际接入交给原监控消费者，不另建第二服务。Factory/Braid不写或跑tests/smoke/probe，反馈来自编译、实际准备与获授权运行。

## 责任与当前事实

主线拥有配方、最终装配、实验启动、状态与监控接入。i14_recovery_routes拥有逐模型恢复接线及其有证据的必要修复；i14_host_handoff只读盘点旧writer、reservations及源保全/交接。主线保持整体集成责任，子Agent不得启动模型、停止无关旧资源或修改Console。

DX源码及离线制品发布已完成，不等于Docker接续、完整Harness恢复或供应商请求已经验收。当前正在消费公开合同和实际旧回执；真实模型catalog查询只读GET，不发生成prompt。原件归runs/iteration14/dx-resume-20261002，错误原文、版本、源停止与实际采用分别保留。

下一步是确认逐模型恢复合法路径与宿主准入，冻结新配置/私有凭据，完成实际无模型准备及逐角色读回，然后沿已授权GitHub范围启动并记录身份。若恢复需要丢进度、变更会话历史或同daemon退役无关任务，返回具体影响和最小决定，不据继续推进扩大范围。


## 优先级调整

用户新要求官网I13 Flash/GitHub 7e8ec62670df因ARC额度耗尽切换到自有API，采用I14配方。该项为当前最高优先级，独立原owner负责受控停止/完整保全和接续；I14当前仅推进无模型材料与接口准备，不启动新生成。实际catalog只读GET已取得HTTP200：普通Qwen提供ZHIPU/GLM-5.3-Flash而非裸glm-5.3-flash；Kimi包含kimi-k3/K2.7；TokenPlan提供deepseek-v4-flash-0731/4.1而非裸DS。供应商wireID与旧原生model.id不同，需要显式映射或合法迁移，不能只更换URL宣称完成。

宿主读回确认WSL旧执行权不满足新authority接管；development-2可用于独立准备，只有用户Redis，但新authority缺首次使用域消费不存在legacy registry的公开合同。已将具体原件交DXowner修接口，未编造空registry或停止无关WSL旧现场。

用户已确认本次I13 advisor“保留K2.7-Code，只切供应商”，内部DeepSeek采用Token Plan的deepseek-v4-flash-0731。这两个决定仅覆盖本次I13接续；I14 advisor仍为K3。旧官网源7e8ec62670df已单次取消并独立GET确认CANCELLED，最终ZIP为326459735字节，SHA256 de0f9bfe1af401b49756bf6abfd314fc75641b208f37afa1f70f4d41e826d43c；72条原生HTTP402错误明确为insufficient_balance，不能当作OOM。取消前ZIP、取消意图、原始响应、最终ZIP与18份native均在hosted-github-self-funded-r4保留。

最终ZIP缺clone私有.git，原来源保持partial。接续先以每个clone最后成功Git操作核实commit/branch，再用现有明确重建路径生成新Git元数据，保留全部非.git工作文件、DB/WAL和native；新index不是原index，原reflog与暂存独有状态不可声称恢复。若基准歧义或未发布对象缺失，呈现具体影响再决定。派生完整状态只属于真实离线修复后的新执行，并沿provenance保留原缺损。

实际官网表单只注入一个模型key，三路绑定不能仅靠模型配置生效。共享恢复包增加显式私有model-environment输入，只接受FACTORY26_MODEL_BINDINGS及其声明的凭据变量，入口在绑定前消费；不会全量复制models.env或建立模型网关。当前已完成源保全及共享接线的离线反馈，尚未启动替代官网运行或产生新模型请求。
