# 修正后的有界导航复核

2026-10-07。本会话沿实际维护入口及源码读回下列问题，没有继承隔离的新会话、独立 reviewer、模型请求或设施测试。这份记录证明哪些入口可以得出足够具体的答案，同时保留不能证明的使用收益。

| 自然问题 | 实际读回路径与结果 |
| --- | --- |
| 指定 GLM 自费运行应选哪个供应商？ | docs/index → harness/model-recipes → self-funded.json → catalog，得到用户指定三条链；与 variant 无关，不能用默认 BigModel/Moonshot 替代。进一步查新 Lab 消费代码发现路由只被复制，已撤回启动示例；此项执行仍未通过。 |
| 当前能否开始已获明确授权的修改？ | AGENTS 协作规则明确直接修改请求即授权；分阶段复核只适用于本任务的明确约定。旧 packet 的未开工说明移入历史，不能据其撤销当前许可。 |
| 新 Console HTTP 200 是否说明真实运行已接通？ | 当前 Console 说明直链设施状态，区分服务启动与真实生产链路；旧服务 register/accessor 操作不再作为新入口。 |
| 旧 experiment 应怎样读回？ | 当前证据页先按 producer 区分；旧 lab.exp namespace 与原 executor 明确，当前 CLI 不再推荐 history/monitor/checkpoint。 |
| 中断工作能否完整恢复？ | 恢复页区分当前同 variant restart、Hosted 不支持 pause/resume 和旧 checkpoint 协议；原生状态、数据回收与新运行身份分别说明，不因 Git/应用备份存在就声称完整恢复。 |
| 取得官网评分是否等于正式参赛？ | 根术语与配方入口区分模型调用模式和提交/评测身份；自费 API、ARC API 不自动推出官方 self_funded/比赛模式，应用重放不替代参赛生成。 |
| 接续相邻设施任务应读哪个 packet？ | 工作主题索引 → finals 取得当前 run 重构；旧 DX/operations/startup packet 提供短入口及历史证据，不再把原 lab.exp 授权和静态接口作为新设施现状。 |

本轮没有缺失入口需要猜测，也没有查账户余额来推断模型配方，但操作者已参与改写，不是独立自然使用样本。它不能证明整体 Agent 判断已改善、token/耗时已经降低，或所有未来任务都会正确采用说明。实际未消费路由的问题说明只做链接/JSON检查会漏掉关键结果；该缺口保持未完成状态。
