# I14-0 实验记录

本轮为 `e20261002-01 / i14-0`。执行范围和完成判据以 [packet](packet.md) 为准；独立实现及操作反馈归 cleaner-implementation.md、reviewer-implementation.md、tester-e2e.md，配方操作与恢复归 [I14-0 README](../../experiments/i14-0/README.md)。I13 的正式结果及后续修正不阻塞这批启动，之后交 I14-1 对账。

四个 variant 各从干净起点生成 GitHub 与 Sheet 一次，共八项。普通成员与默认根为 GLM-5.3-Flash / high，原生 advisor Kimi K3；使用自有 ARC API，不使用比赛额度。每题生成完成后立即冻结最终应用，独立 `self_funded` 官网重放。生成与评分的时间、用量、费用分开记录；未执行验收或设施失败不计作应用零分。隐藏反馈不送回仍在生成的 Agent。

2026-10-02，四份制品已冻结，共同 Braid Linux binary 为 `e002edb848395698ab83d2221ec40a13bcfa8c2e379bf7ca26f90389d02260e8`。具体文件、源码清单、私有工具key来源、允许需求清单和每项模型选择保存在 `runs/iteration14/i14-0/`，不能从当前源码替代这些身份。启动源码也已独立冻结；有限 dispatcher 逐项接入已有 operation，等待真实共享准入事实后再放出下一项。

| Variant / 题目 | 当前执行身份 | 首次阶段 |
| --- | --- | --- |
| baseline / GitHub | `pi-braid-i14--hackathon--github-3a4653d711c3d9` | 已派发，取得共享准入，材料传送中 |
| cleaner / GitHub | `pi-braid-i14-cleaner--hackathon--github-51de01f10f57f3` | 已派发，取得共享准入，材料传送中 |
| reviewer / GitHub | `pi-braid-i14-reviewer--hackathon--github-9bce3a1fd0e294` | 已派发，取得共享准入，材料传送中 |
| e2e / GitHub | 待派发 | 队列 |
| baseline / Sheet | 待派发 | 队列 |
| cleaner / Sheet | 待派发 | 队列 |
| reviewer / Sheet | 待派发 | 队列 |
| e2e / Sheet | 待派发 | 队列 |

这些是首次启动时的事实截面。动态执行和后来产生的身份以唯一聚合索引 `runs/iteration14/i14-0/active-matrix.json` 为入口，各 operation 的公开 `observation/monitor/accepted.json`、原始 outcome、provider liveness、生成终态及重放 journal 为证据。记录已接收不等于模型开始生成，更不等于机制实际采用或功能完成。

新增运行配额为 2GiB / 2CPU，共享五槽计入已有 I13 两项。旧 I13 继续保持 4GiB 与原模型通道；首次三项新准入加两项旧执行占满五槽。普通生成镜像已实际核对 `ps` 与 `docker-init`，e2e 的额外 addon 不改原 I13 runtime 或镜像。

首批三容器已经实际启动，独立读取确认 memory=2147483648、NanoCpus=2000000000、init=true、MODEL/VISUAL_MODEL均为glm-5.3-flash。回执在 initial-container-readback.json；此时仍处于SDK材料准备，尚未据此声称模型开始调用或应用进展。

e2e 的最后一轮 skill 诊断指引晚于本轮包冻结：当前源码补充了默认Chromium、不重复安装、应用run显式ai-trace及失败schema用量/规划回退说明。运行代码和addon一致，冻结包保留原skill文本与摘要，不偷偷替换；原包已包含ai-trace能力说明。后续包可采用新的指引，该差异不算已在I14-0采用。

根模型判据为 I13 的两题两组正式最终分数完整，GLM 两题平均减 Flash 两题平均至少 10 个百分点。当前四个指定来源均无有效完整最终结果，首次三项均冻结 Flash。未来未派发项在各自 `selection.json` 承诺前重新消费已有结果；已经交给 operation 的项保持原选择。若后来切换，按实际根模型分层比较，不能将不同条件合并成严格机制对照。

纯脚本采集已逐项接收以上真实 run，独立监控会话 [I13 实验监控](codex://threads/01a0f613-082a-7251-a25f-e99acbc37706) 使用 GPT-5.6-Luna / low，每十分钟消费已有证据。普通进展安静，仅在明确新故障、终态或需要用户决定时通知。dispatcher 或 worker 异常时保留原 operation 并停止后续派发，按身份核查接续同一记录，不另造收费尝试。
