# Pi 最小参赛 Variant

目标：截止前准备原生 Pi + background tasks + subagents 的独立 variant，移除 SVC/Braid，回到直接完成产品需求的最小方式。

用户已复核精简配置，授权实现、自由提交及官网正式参赛；每10分钟检查余额，低于200停止。I10仍暂停，I11源码保留。

明确输入：GLM-5.3-flash 主会话（含视觉），Kimi 2.7 advisor；不设其它子角色；agent-browser、赛题相关技能、Context7/Exa；原生后台任务与subagents。无SVC/Braid。

分工：主线持有入口、打包、完整配置复核与提交；readable-cli构建纯Pi runtime；final_product_methods已完成初始配置；analytics_executor负责独立余额保护脚本。不得新增测试/模拟探针或调用模型试运行。

配置复核已完成，配置与授权仅适用于此新variant；其它实验仍不得使用参赛额度。冻结包与余额保护已完成；用户最新调整为先本地运行，官网提交暂缓。

最终配置见[config-review.md](config-review.md)。explorer/executor/browser-operator已删除；GLM官方确认视觉能力，vision也删除。Ponytail lite加入主会话和advisor。实际submission/run身份待启动后写入；不将源码完成当成已参赛。

## 本地先行：2026-09-29 21:47 CST

用户最新指示：“提交到官网之前，先本地运行；启动后，前20分钟先每5分钟下载一次工作区包下来检查pi会话内容”。正式 journal 仅 prepared，submission_id/run_id 均为空；不得自动启动官网控制器。

冻结 ZIP SHA256：`060bbf123e24771a4044c1a12fe0637f854c810c75af72d91279fc8691607909`。
WSL 使用相同 ZIP、官方本地 Runner、公开 Hackathon requirements 并行生成两题，每题 4GiB/2CPU，不做本地评分。
模型使用自带 ARC API key（个人 Meter 账户），不使用正式参赛额度；不能把该账户余额与285.86参赛额度混淆。

- WSL实验目录：`/home/yyh/Development/factory26/runs/pi-minimal/20260929/local/generation`
- GitHub：`pi-minimal--hackathon--github-b91ca34d0a4196`
- Sheet：`pi-minimal--hackathon--sheet-e24836ce1f57c2`
- 启动记录：`started_at=1790689645`；控制器 PID 1477715。
- 观察：第5/10/15/20分钟留存工作区及原生会话；`lite_baseline_monitor`负责定时归档下载和语义检查；输出 `local-observation.md`，原始快照在 `runs/pi-minimal/20260929/local-observations/`。
- 检查：真实进展、模型及唯一advisor角色、技能/视觉/浏览器/MCP/后台任务的调用和错误；尚未触发组件明确标未验证，不强行注入调用要求改变配方。

官网后续启动仍受每600秒参赛余额检查、低于200取消和阻断后续任务的规则约束；当前未启动官网和余额守护，避免误报本地启动为正式参赛。
