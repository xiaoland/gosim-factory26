# 低唤醒成本的实验监控

用户明确要求监控 Agent 使用 6-luna medium/high，并指出每 60 秒返回模型等待脚本是问题；授权将可复用提示词与模型配置沉淀到项目。

旧监控复用了承担实现工作的 gpt-6-sol/high。
远端虽然每 180 秒才检查状态，子 Agent 却每 60 秒回到模型调用续等，仍制造无信息增量的采样。
旧等待连接已停止；实验 Controller 和容器未受影响。

## 当前实现

旧的监控文件曾是开发侧委派入口，现已删除；本页保留当时的配置事实，不再提供可执行的委派入口。
默认 gpt-6-luna/medium；需要复杂故障解释时可选 high，逐 run 分析仍另行委派。
主 Agent 读取该文件并加入精确主机、run 目录、等待命令及结果消费者；不增加角色配置解析器。

`scripts/wait_local_runs.py` 仅适用于 local_experiment 的 run.json，持续进程每 180 秒读取一次，每个 run 终态只输出一次。
可提供 Controller PID；Controller 已消失而记录未终态时明确报告监控故障。
脚本不以日志、token、mtime 或耗时推断语义停滞，也不修改或重启实验。

工具传输层的 write_stdin 续等由单次 functions.exec 内的 JavaScript 循环吸收，模型不在每次空返回后采样。
后台子 Agent 使用长外层 yield 窗口，主 Agent 保持可交互；若宿主提前返回外层 cell，角色要求一次报告限制，而非恢复模型轮询。

## 实际操作与当前限制

已用旧 Keep 的真实 completed 记录执行脚本，正常输出终态、退出码和结果入口并退出；没有构造模拟记录或新增测试。
新子 Agent `/root/run_monitor_luna` 已明确以 gpt-6-luna/medium 启动，仅接手 boundary-fix 两题和 Controller 895749。
等待端部署在 WSL 当前实验目录，不改变冻结 ZIP；旧监控不再并行。
长外层调用的宿主行为与两题最终结果仍以实际返回为准，不能用脚本静态结构声称已完成验收。

本次未提交；Braid 功能验收与逐 run 分析保持原任务归属。
