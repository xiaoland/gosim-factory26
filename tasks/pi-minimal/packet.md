# Pi 最小参赛 Variant

目标：截止前准备原生 Pi + background tasks + subagents 的独立 variant，移除 SVC/Braid，回到直接完成产品需求的最小方式。

用户已复核精简配置，授权实现、自由提交及官网正式参赛；每10分钟检查余额，低于200停止。I10仍暂停，I11源码保留。

明确输入：GLM-5.3-flash 主会话（含视觉），Kimi 2.7 advisor；不设其它子角色；agent-browser、赛题相关技能、Context7/Exa；原生后台任务与subagents。无SVC/Braid。

分工：主线持有入口、打包、完整配置复核与提交；readable-cli构建纯Pi runtime；final_product_methods已完成初始配置；analytics_executor负责独立余额保护脚本。不得新增测试/模拟探针或调用模型试运行。

配置复核已完成，配置与授权仅适用于此新variant；其它实验仍不得使用参赛额度。当前准备冻结包与余额保护，然后提交两题。

最终配置见[config-review.md](config-review.md)。explorer/executor/browser-operator已删除；GLM官方确认视觉能力，vision也删除。Ponytail lite加入主会话和advisor。实际submission/run身份待启动后写入；不将源码完成当成已参赛。
