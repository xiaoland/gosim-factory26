# 官网单题运行方案（已授权执行）

目标：以一次 Hackathon GitHub 生成与评分检验本轮协作、最终集成和自动化验收流程，避免继续等待已停止的 BookStack 调度现场。
Keep 已得27/32，工具及单题闭环有真实证据；GitHub有历史低分和集成失败证据可供比较，但本次多项变化不能解释为单变量收益。
官网2026-09-26只读GET确认 hackathon 与 arc-bench-lite 均open、template_required=false，登录Cookie可用。

| 条件 | 提议 |
| --- | --- |
| 平台 | ARC官网 Competition API，非Playground |
| 题目 | hackathon / hackathon--github，仅一次生成与完整评分 |
| 包 | runs/acceptance-integrity/20260926/schema-fix/pi-team-mixed.zip |
| SHA256 | 89452d2d9d602ef49fe3170498b5efdf4d07d724fdd09ac68e13619e4390d92f |
| 身份 | 包内旧名pi-team-mixed，当前pi-braid前身；不改写旧身份 |
| 根 | glm-5.3-flash / high |
| 其它Braid成员 | glm-5.3-flash、deepseek-v4-flash / high，由Agent指派 |
| 原生advisor | kimi-k3 / high，沿冻结配置 |
| 视觉 | deepseek-v4-flash-vision-exp |
| 凭据 | self_funded，自带既有官方API key，https://api.arc-bench.com/v1 |
| 参赛额度 | 不使用official_evaluation；不授权参加比赛 |
| 执行 | 一条run，不自动重试生成、不接Sheet、不自动开启下一轮；15分钟采集 |

比对确认当前variants/pi-braid相对stage中对应文件仅run.py身份常量改变，build.py不属于运行stage；agent_support、braid_runtime、core、model_budget对应内容一致。该比对不声称整个当前SVC/Braid源码与旧冻结包完全相同。
本地BookStack恢复专用Braid guard未进入此包；官网从新状态启动，不依赖宿主重启后的旧句柄。BookStack出现materializing和事件积压仍是未解释风险，不能声称官网必然消除。
因此建议复用明确冻结的旧包，避免维护期间重建并引入额外变量；若要求运行最新源码，需要另行冻结构建，当前尚没有可等价替换的最新pi-braid ZIP。

提交沿lab.arc_bench.competition的prepare→snapshot→create→start→collect；prepare仅本地，后三步会写官网并启动计费。
当前代码阻止official_evaluation；API写入使用catalog=competition、credential_mode=self_funded。没有独立participate字段，不应把未出现的开关说成已经核实；实际提交前应确认平台对self_funded展示/参赛语义，若会占比赛机会即停止。
现有明确授权包含凭据模式、模型配方和禁止比赛额度，当前官网执行授权曾被暂停，新的付费单题执行仍待用户确认。
没有查得本次货币上限或运行前余额，不能承诺费用上限；15分钟采集不是实时扣费硬限额。用户批准时需明确允许该一次运行按现有配置计费，或指定必须实现的金额上限。
当前未上传、未创建submission/run、未启动模型；扩容期间不占用WSL。

后续核实与授权更新：当前官方前端index-DCT-RiaL.js明确将预算/排行榜资格绑定official_evaluation勾选项，self_funded是未勾选分支；摘录与只读预算记录保存source/official-billing/verification.json。用户经协调对话批准此单题及现有配方，明确费用控制不用太在意，无需再询问金额上限。官网支持取消run，取消不可恢复、保留日志与产物；未确认金额硬上限。已登记e20260926-01，执行身份与后续结果见experiments.md。
