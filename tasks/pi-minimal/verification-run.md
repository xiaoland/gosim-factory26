# pi-minimal 验收方法：官网 GitHub 运行

2026-09-30。授权原话：“让pi-minimal再去官网自费运行GitHub题目（因为自费，所以不用运行比赛额度监控）”。本次从官方需求重新生成，只跑Hackathon GitHub，使用当前pi-minimal源码与完整svc-verification技能；不继承旧应用或会话，不启动Sheet，不使用比赛额度，也不启动比赛额度守护。I12两题继续暂停。

主模型沿用自有BigModel的GLM-5.3-flash；唯一advisor沿用已授权个人ARC API key的Kimi-k2.7-code。两条地址及密钥只写入上传包的private-models.json，不打印或进入Git。复用既有Linux纯Pi runtime，不重复安装工具。

源码提交为 `6cd8d2a`，实际技能材料以本次冻结包及manifest为准。实验目录为 `runs/pi-minimal/20260930/verification-github-123247/`，单题journal使用其 `official/`。snapshot、create、start均沿用competition controller与journal；不重复不确定的写请求。

完成条件是官网生成、部署与评分取得终态，保存总分、通过数和原始阶段错误。启动核对先确认self_funded与真实生成状态，再按前十分钟3分钟、之后8分钟采集。真实轨迹用于判断验收技能、advisor、浏览器与自动化验收是否采用；材料存在或RUNNING不等于采用成功。

冻结ZIP SHA256为 `4edbd960caf21a51d8a83195761a07ec8df0f06f4d8c62fea7d161dfcf0a3216`，包含完整svc-verification入口及四份references。Submission `2dbbc244c485`，GitHub run [2ef9660d0dad](https://arc-bench.com/runs/2ef9660d0dad) 已于12:42:54 CST启动。官网确认环境准备完成、生成阶段运行中，journal的credential_mode与远端billing_mode均为self_funded，任务列表仅有hackathon--github。

Controller PID `21226` 持续按3+8间隔查询状态、阶段日志和过程证据，终态后自动收集评分。启动回执为 `startup-receipt.json`，冻结与路由回执为 `freeze-identity.json`；均位于本实验目录。没有启动比赛额度监控或Sheet。当前核对只建立真实官网启动事实，技能采用、模型调用与最终应用效果仍待轨迹和评分验证。I12两题保持暂停。

旧pi-minimal自费运行已核实终态：GitHub `c3fea0c3488c` 为2/100，Sheet `6dc68bef2081` 为40/100。旧制品不含本次验收技能，分数供背景参考；仅凭分数不能判断失败原因。本次GitHub槽位可用，未取消或重建旧run。

## 新版 V&V 对照运行（2026-09-30）

用户在侧会话确认“好的，可以上传”。仅重新运行官网 GitHub、self_funded，从零生成；I12暂停状态不变。复用前次冻结ZIP的全部非V&V材料，仅替换当前svc-verification完整技能（含新增feedback-and-evolution.md），已逐文件核对与来源相同。模型继续BigModel GLM-5.3-flash主会话与个人ARC Kimi-k2.7-code advisor。

新实验目录 `runs/pi-minimal/20260930/vv-rebuilt-github-192735/`，ZIP SHA256 `1c567ad6cecd038e61591555f4b174ae7c331176a23b2fceac6716a06ff487d4`。控制器PID20283，独立journal为该目录official，按前三分钟/之后八分钟策略采集并在终态收集评分。不启动比赛额度守护。远端身份及实际状态以journal和startup-receipt.json为准；上传结果不确定时不得重复创建。

新版运行已上传并启动：submission `01d97d7a942c`，GitHub [463c50db8b06](https://arc-bench.com/runs/463c50db8b06)。启动确认状态 `RUNNING`，远端 billing_mode=`self_funded`。控制器持续采集，实际回执保存本次目录startup-receipt.json。
