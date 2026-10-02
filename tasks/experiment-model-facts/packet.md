# 实验模型事实查询

2026-10-02，用户通过独立任务授权实现、基础验收和本任务 git commit，不 push。原话范围是“正常启动/热恢复/监控时可直接查看各运行实际生效的根Braid、其它成员、Pi sub-agent、视觉/e2e等模型、API endpoint、credential mode及配置来源/版本；区分desired/frozen/actual并暴露drift，不显示密钥”。

本任务接续 experiment-operations 的公共查询接口。原设施会话已完成提交 897f307，当前不活跃；主会话正在编辑 I14 variants/run.py、settings、e2e.config.ts、launch.py 和 I13 recover_completed.py，本任务只读这些面。持有 lab/arc_bench/model_facts.py、operations 的查询接缝、local_monitor 的既有采集接缝，以及运行文档。没有停止、恢复、启动付费实验、修改冻结输入或创建新监控。

方案是从原记录投影允许公开的字段：selection/spec 是 desired；manifest 绑定的 ZIP/env 是 frozen；运行 request、模型连接回执及 Pi 实际 native home 是 actual configuration；timing 的 model/provider 只证明 observed usage。配置可用不代表已调用，provider 别名不是供应商，认证方式不是账单费用模式。endpoint 不含用户名、查询参数或密钥；任何未取得证据的字段明确 unknown。查询默认消费已采集记录，可显式通过现有 collect 做一次只读 live 获取，不另建轮询。

验收只编译、查询已有 I14 三项运行及旧 I13材料，保存实际只读结果。无 Factory/Braid 测试、probe、smoke 或模型请求。重要范围变化交用户决定。

## 完成与验收

已实现 `python3 -B -m lab.arc_bench operation models <operation|active-matrix.json|lab-run|Competition-journal> [--live] [--json]`，status 同时返回模型投影。复用原 collect 的 Docker 身份校验和采样生命周期；单次 live 只读模型材料，不读取 rollout，不创建后台循环。新采集器在原批次保存 model-facts.json，辅助模型材料不可读只产生 unknown，不使 provider 采集整体失败。既有冻结 collector 不自动升级。

实际 I14 三项 live 查询和独立原件读回均得到根 pi-glm-fast / glm-5.3-flash，以及原生模型 endpoint 主机 api.arc-bench.com。查询还能列出其它成员、Pi role、视觉、已物化 native-home 的具体配置，timing 曾观察到 Kimi K3 和视觉 Flash；这不是每种候选模型均已调用的声明。三项已覆盖模型/连接未见漂移，frozen package/env 实际 SHA 与 manifest 相同。独立评分 policy 均为 self_funded、allow_competition_credit=false；生成运行未有账单模式回执，因此 credential_mode 坚持 unknown。旧 live 没有新 model-connection 回执，活动进程连接变量和原生模型材料仍可读。实际三份私有 model.env 中的凭据值与查询原件比对，输出匹配数量为零。

I13 两项 live 查询均读到 paused，未 exec 暂停容器，actual/drift 为 unknown。这是原件观察，任务未暂停或恢复容器；当前恢复由主任务持有。五项 I14 queued 显示尚未派发/operation 未冻结，不把批次声明冒充 actual。已有真实终态 operation 查询、status 集成、默认表格、Python 编译与 diff 检查已覆盖；无模型请求、Factory/Braid测试、probe或smoke。原件保存于 runs/experiment-model-facts/20261002/，其中 independent-readback.json 独立读取原生 request/provider，i14-live.json 保存详细投影，i13-live.json 保存暂停事实。

仍无法独立证实服务端底层模型、生成账单费用模式、未有 timing 的 e2e 实际调用。e2e 当前五个queued中的两项未派发；公开工具配置可在其冻结包/实际工具路径存在时读出静态模型，不能称已验收调用。热恢复完成后的实际模型查询反馈需来自主任务恢复结果，本任务不越界启动它。新冻结采集周期接线已经编译，当前在途collector保留自己的冻结版本，本次不重启采集器。源码和操作文档只更新本任务拥有的面，提交不包含其它工作区改动，不push。
