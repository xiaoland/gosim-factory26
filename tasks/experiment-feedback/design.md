# 接点与验收

现状：factory.run 在 try/finally 外调用 generate，生成失败跳过 analysis；生成取消被写成 generation_failed，错误为空。logged 只等待进程，Codex transport 只据 turn/completed 判终态，中间 error/retry 未形成摘要。remote eval 每 15 秒读一次状态，Playground watch 默认同为 15 秒。没有覆盖生成、评测、分析的持久总结果。

修正范围：全流程保存 outcome.json（running/completed/failed/interrupted），引用现有生成、评测、analysis 证据；原始错误优先，analysis 自身错误另列。保留同步子进程退出事件，远端状态采集最小 180 秒，退出后立即返回。后台线程用 Event.wait 等待采集时机，在生命周期退出时立即收尾；不依赖主 Agent 发起下一次查询。

新增独立 run_feedback 模块：定向读取已有事件和显式关联的 Braid 会话，提取 provider 错误/重试与实际工具完成，合并重复错误；心跳、token 增长、状态文件重写不判为语义进展。brief 返回目标、阶段、错误摘要、采集时间、证据路径与明确未知，不包含 prompt 或完整会话。无变化不向 stdout 输出；终态只由运行元数据判定，语义推断交给子 Agent。通知使用稳定 run/结果身份，恢复时可带已见身份跳过重复；不声称消息跨进程投递恰好一次。

当前活动会话通过既有 sub-agent 完成消息获得结果。运行器不直接调用主模型、比赛模型或私有 Codex App 接口，也不建立每三分钟唤醒模型的 heartbeat。低成本子 Agent 获得实验目标、brief、少量定向证据和上次判断；只需在终态或确有决策需求时回传主 Agent。

独立预演：较低成本 Agent 找到了生成失败跳过分析、取消误记和 Codex/Pi 已有错误字段。其建议的“终态后额外观察180秒”不采用：180秒是轮询间隔，终态不延迟。advisor 核实持久结果加现成子 Agent 回传足够；SSH 断连只能说明本地链路失联，不能推断远端已停止。主会话结束后的唤醒仍未知，不承诺。

验收边界：

- 用 fake generate/evaluate/analyze 覆盖成功（包括有效失败用例）、生成异常、取消、分析异常，核对原结果不被遮蔽，终态在分析收尾后发布。
- 重放真实 Pi auto_retry 和 Codex stream error 形状，验证运行中已可见、计数不把同一错误的多次包装当多次请求、长日志不进入 brief、无错误不能被推导成健康。
- 用替代时钟/等待器验证至少180秒的远端观测、无变化静默、终态立即返回与已见通知身份抑制，不真实等三分钟测试每条分支。
- 用一个短假任务让低成本子 Agent 等待完成并回传当前主会话；主 Agent 在期间做独立工作，不主动轮询其状态。该结果只证明活跃会话回传。
- 文档链接、SVC status 与相关测试通过后汇报；不自动启动完整bench。
