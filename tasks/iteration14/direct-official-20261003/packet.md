# I14 官网直连实验

2026-10-03 用户明确要求：“将 I14 reviewer 放到官网上面去运行 sheet 题……模型网关去除……仅限这次运行，可以做为一个独立的variant。”随后补充：“还用 I14 cleaner 跑 github stage1, stage2, stage3（三个 task，所以可以分开并行）；同样没有模型网关，模型配方不变。”授权独立 variant、必要接线及四项 self_funded 练习，不做正式提交。原官网 A2 不受控制，OOM 排查由其它会话负责。

本侧会话独立负责，无 sub-agent。reviewer 跑 hackathon--sheet；cleaner 分别跑 hackathon--github-stage-1、2、3。官网元数据四题 unlocked=true，stage2/3 source_run_id=blank，按用户指示独立生成，无应用 seed，不读取隐藏评测器或历史评分。

独立源码为 pi-braid-i14-reviewer-direct、pi-braid-i14-cleaner-direct；模型、推理和角色配方不变。Flash/DeepSeek0731 直连千帆个人套餐、K3 直连 ARK Coding Plan；保留每 run 昂贵模型合计一个 Braid session 的预算。仅本次去掉模型网关及其 fallback，Portless 应用代理继续保留。公开绑定和私有凭据分别装配，由 package_agent producer 生成最终清单，禁止修改已冻结 ZIP。

Mac 记录与产物全部位于 runs/iteration14/sheet-cleaner-direct-20261003。官网分题并行通过冻结 parallel_distinct_tasks=true 显式启用，仅 self_funded；同题/未知身份仍阻塞。既有实验默认门控不改变，不绕过冻结执行器。

材料已完成真实 producer 打包，reviewer/cleaner 逐文件哈希与清单一致，包内无网关激活材料。四个独立 controller 已接收；上传、创建、启动由冻结执行器在比赛写锁内依次完成，模型生成不受该写锁串行限制。完成条件分别核实首模型、应用交付、平台功能计数与原始分数；start 接收不等于模型已开始。写入意图先于调用，未知 POST 不自动重发。

Sheet 首次 run 73230b873c9e / submission aab313ccd714 启动被 HTTP 429 拒绝：全平台已有 400 active runs。独立 GET 已确认 FAILED、started_at=null、同一明确 failure_reason、score=null，保留为启动设施失败。使用同一 reviewer ZIP 创建独立 capacity-retry 定义和 controller，不修改原冻结实验，不重发未知 POST。新入口 reviewer-sheet-capacity-retry/experiment。

cleaner stage1 run 94b8e2b76455 / submission ee7dff415802 已确认平台接受启动；stage2/3 及 Sheet 重发等待原生锁与上传回执。实际状态见该目录 startup-status.json，原始 intent、响应与 execution 保留各自 experiment/attempts。

运行更新：独立 GET 确认 cleaner stage1 94b8e2b76455、stage3 db6d8361841b 为 RUNNING。stage2 首次840db796542e同样容量拒绝、FAILED且started_at=null；cleaner-stage2-capacity-retry在同一冻结包下重发一次。Sheet重发8ca071551fd4 / submission d88e97b10bdf 已获平台启动回执。容量失败不是模型实验结果；不存在未知 POST 重发。

最终启动核对：reviewer-sheet-capacity-retry = 8ca071551fd4 RUNNING; cleaner-stage1 = 94b8e2b76455 RUNNING; cleaner-stage2-capacity-retry = 9b4cc578b462 RUNNING; cleaner-stage3 = db6d8361841b RUNNING。官网独立 GET 同时核实 run、submission 身份；controller 继续按原生 900 秒间隔采集至终态。尚无评分，不将 RUNNING 解释为首模型消耗或应用完成。

2026-10-03 14:31 CST，用户在实验主线明确要求取消 cleaner stage1 `94b8e2b76455` 并分析OOM资源释放。root已在WorkSSD保存完整活体workspace诊断包，经该experiment冻结Lab stop，独立GET确认CANCELLED；原件归 `runs/iteration14/oom94-release-20261003`。主线持有运行控制和修复，oom94_analysis持有包分析；不自动重跑，也不因此控制其它三个直连run。此前RUNNING启动核对仅作为历史事实。

2026-10-03 17:13 CST，用户在主线新增授权：“9b4cc578b462、8ca071551fd4都超过100分钟无新事件，可能意味着也撞到了resource gate，建议也取消并用新版本接续旧工作”。运行控制责任转交主线direct_oom_continuations，唯一负责两run的保全、冻结stop、独立终态及各一次同题新版接续；experiment_evidence负责公共checkpoint/prepare机械修复，resource_gate_implementation交付新gate及完整support依赖。原四题生成目标、直连模型与角色、self_funded保持，最高优先级是实际资源释放或有界fail-closed。stage3 db6不受本次控制。旧controller仅采集，不并行发送控制。授权与实际源观察归`runs/iteration14/resource-recovery-20261003/direct-continuations`；两run近期无事件属实，但无当前resource_wait_groups，停滞原因尚未确定。完整workspace导出仅为来源，公共producer验证前不称完整checkpoint。

17:23 CST，两run冻结stop及独立GET均确认CANCELLED，分别于17:23:27、17:23:53；无评分。旧完整ZIP已得，取消后最终导出与包内事件、Issue/PR、native尾部和资源原件正在定向分析，以定位阻塞及公共checkpoint源完整性。RUNNING仅平台生命周期字段，无waitgroup不作为继续等待依据。
