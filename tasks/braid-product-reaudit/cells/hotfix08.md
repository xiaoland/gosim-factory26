# 第08次热修复：明确缺陷一并收敛

用户授权：“都要一并解决，根本原因不明确的才延缓；还有其它支线推进如何？有没有要一起进入本次热修复的”。
保留DeepSeek两题最新半成品接续，模型路由及每题4GiB/2CPU不变；Qwen/MiniMax保持取消，不使用参赛额度。

| 改动 | 状态与负责方 | 本次运行要观察的效果 |
| --- | --- | --- |
| 只读子角色关闭错误的自然语言写入guard，保留工具范围 | 已实现并进入08首版base；主Agent | 包含编辑控件名的读图任务正常启动 |
| Pi角色/Braid成员及PBB作业ID区分 | 已实现并进入08首版base；主Agent | 真实委派使用正确角色和等待入口 |
| 重复委派、产物归属与父会话消费 | 已完成五套指令的最小修正；browser_guidance_apply | 不与已持有工作重复写入；结果有实际采用或明确失败 |
| 父会话重建后的子任务连续性 | 已实现同cwd旧任务索引及原生终态文件事件转送；语法检查通过，待运行 | 根据已查实的状态存储/发现断点修复，不让Braid管理子进程 |
| exploration-tools迁入explorer；MCP配置迁tools/ | 已实现并进入08首版base | 工具知识随角色取得，normal/recovery路径一致 |
| Issue/PR依赖交接避免同号混淆 | 已完成五套指令的最小修正 | 用对应成果、候选提交与行为判断前提，不凭编号 |
| Collector请求阶段耗时 | 已实现、Python编译完成，正在纳入恢复包 | 从真实运行区分read/decode/persist/response成本 |
| with-service、浏览器指引、Braid普通消息投递 | 已在07，不重复实施 | 保留；使用07已收集行为证据并继续观察 |

08首版base已冻结；待上述材料收齐产生新包身份，不原地修改旧ZIP。
vision_root_cause负责包更新与接续材料，主Agent负责集成与停启决策。
运行验证仅使用自然生成、原始状态和真实调用；不新增Factory/设施/Corpus测试。

暂不猜测修复：Executor SIGKILL来源、Collector超时的具体耗时阶段、冷恢复后旧任务存活与临时status文件是否保留。
其中Collector先带入计时取得证据；子任务连续性限时定向调查，明确部分即可修，不以未知部分阻塞其余热修。

本次集成已收齐：两个observer、五套instructions、collector计时、恢复来源implementation-hashes更新及现有恢复ZIP的显式替换。
打包Agent已获准在07仍生成时停止、保存最新半成品并接续08；若已交付/评分则保留该流程而非强停。
原生交接完整说明见 [native-continuity](../../factory-subagents/cells/native-continuity.md)。

## 已接续：2026-09-28 14:36起

07已人工热停并保存最新半成品；08控制器为 controller-e5aeaba7123a，执行PID 354115。
GitHub：pi-braid--hackathon--github-97914b9e3158cf；Sheet：pi-braid--hackathon--sheet-d478f7dc8ff84f。
恢复后两题均有新assistant/tool活动，逻辑Braid身份保持；截至14:53两题仍生成，无评分。
GitHub已合并4/7 PR，根在等待后台检查，需进一步核对作业是否有效推进；Sheet已合并13/14 PR，新增构建自举修复与服务收尾检查，同时仍有产品功能未集成。
该计数包含07及更早半成品，不能当作08增量效果。
原生子任务连续性与collector阶段耗时已进入恢复包，但暂不宣称已完成行为验收。

## 15:04 行为验收截面

见 [sub-agent逐项证据](../../factory-subagents/cells/attempt08-validation.md)。旧子任务索引三次在新父首个assistant前注入，证明发现与启动交接；未见父显式消费，且旧任务已完成，尚无在途终态唤醒证据。08没有新原生子代理启动，vision guard、角色选择与重复写委派均未自然触发验收。PBB与subagent_wait混淆仍出现六次，指令已接线，需优先审查调用处描述/错误反馈，不继续堆全局提示。
两题仍有实际推进；[GitHub](attempt08-progress.md)定位低效PBB轮询、手工Git合并与PR状态不同步、可并行子项未派发；[Sheet](attempt08-sheet-progress.md)定位Chromium临时目录过长，及应用自身wrapper假失败。后者留给参赛Agent处理；前者是下一次Harness环境修正候选，须保留Pi状态恢复位置。
