# 从上一轮官网运行到当前热修复：阶段性树状报告

整理截至 2026-09-28 12:57（北京时间）。依据 task packet/cell、官方终态材料与 attempt-06 恢复后的原生消息核实；`已实现` 与 `已运行验证` 分开，分数只保留有官方证据的运行。

```text
目标：完整交付、可信验收、缩短有效反馈周期
├─ 上一轮官网运行结束：成绩与根因
│  ├─ 有效官网评分（没有重新生成）
│  │  ├─ GitHub run 595ab74c90a9：4/100
│  │  └─ Sheet run 1efffb84ae1b：58/100
│  │     证据见文末入口
│  ├─ GitHub 根因证据
│  │  ├─ 需求已送达且曾按 link 写检查；失败后模型以当前 DOM 的 menuitem 和对官方测试的猜测改写断言
│  │  └─ 结论：判据迁就实现；发生在该成员首次 reset 前，未证实由 Braid 重建直接造成
│  ├─ Sheet 根因证据
│  │  ├─ 初始需求摘要漏掉 GIVEN/A1:C6；局部检查自行造数据，绕过交付默认状态
│  │  └─ 结论：共享契约与初始条件丢失；完整需求后来被读到，但未纠偏
│  ├─ 共享契约 / Braid 因果
│  │  ├─ 旧实现先合入 develop；成员读到新契约后仍因旧分支可测试而沿用旧形状
│  │  ├─ 后续两条纠偏消息排队未进入仍运行的成员，证明运行中普通输入投递存在缺口
│  │  └─ 未证明通知冗余挤掉关键裁决，也不能把 28 分钟排障全归给 Braid
│  └─ 环境排障
│     ├─ Sheet 检查暴露固定端口、健康检查误连、日志被清理、管道吞掉退出码等问题
│     ├─ 隔离服务下 21/21 通过，说明该窗口不能把 20 项失败都算应用缺陷
│     └─ 这是环境/工具反馈成本证据，不是模型耗时或官方评分收益证明
├─ Braid 产品与技术改进
│  ├─ 已实现并有定向验证
│  │  ├─ 普通追加走 Wake/引用，不因完整投影哈希变化重建 Context
│  │  ├─ 讨论收件按当前负责人、同 thread 作者、有效 @、显式 watch 收窄
│  │  ├─ 关闭自然收尾；仍按全部对象终态结束，已接受 turn/reset continuation 自然完成
│  │  ├─ 关闭关联 Issue 保留当前可见 description/讨论正文
│  │  ├─ 历史终态成员 direct_contact 可确定性收尾为 blocked/unreachable，不创建重复身份
│  │  ├─ 明确拒收重放保留因果；Pi 原生消息收据、状态锁与通知广播已接线
│  │  └─ `cargo check`、Linux release、针对性 Store/对象/恢复检查通过
│  ├─ 只在历史材料中验证的边界
│  │  ├─ 未完成状态冷恢复曾真实产生新 turn、非空 batch=0 个空唤醒，满足用户缩小后的“平稳续进”验收
│  │  ├─ 该官网恢复随后按授权取消，不能写成完整交付、官方评分或质量收益
│  │  ├─ 历史 21,206 条 `assignments.member_login` 唯一键错误的专项因果尚未完全复现；T2 在真实旧 DB 副本中已将 27 条 pending direct_contact 收尾，queued 回执 25→0，身份未变
│  │  ├─ 两者不等同于当前已证实的未修缺陷；专项复现与 T2 收尾需分开记录
│  │  └─ Codex 工作项 reset 尚未端到端验收；新通知量/墙钟/噪声收益未测
│  └─ 责任边界
│     ├─ Braid 保证身份、投递、Context、生命周期与可诊断收据
│     └─ LLM/SVC 仍负责语义判据、需求解释、应用完成与最终验收；不把业务契约裁决塞进 Harness
├─ SVC / 工作方法 / 工具
│  ├─ 已实现材料
│  │  ├─ 在既有 SVC Verification 入口做最小方法修正，明确“需求→观察→判据”、场景前提、结果归因；未重写 V&V Corpus
│  │  ├─ Task Packet/Design/Implementation 在需求交接与共享契约处接线
│  │  ├─ `browser-checks` 默认技能及强制注入已删除；Playwright 工具保留，按需使用
│  │  ├─ 角色材料要求失败时先区分环境、检查、应用，并禁止用实现反推判据
│  │  └─ PBB 已有后台 job、PID/PGID、日志、status/tail 能力，方法已记录其正确消费方式
│  ├─ 已观察但不能宣称收益
│  │  ├─ GitHub/Sheet 因果调查显示关键偏移早于对应首次 reset；不支持“Braid 重建直接抹掉依据”
│  │  ├─ 同一成员可正确修 UI 又错误改断言，说明不是所有失败都归为工具或模型不会浏览器
│  │  └─ 方法文本落地不等于真实成员普遍采用，需从下一次真实轨迹判断
│  └─ 预制检查脚本边界
│     ├─ 不向生成应用写题目选择器、登录脚本、业务断言；Harness 通用服务工具方向仍可评估
│     └─ “Harness 预制应用检查脚本”尚未落地；不重建已删除的 `browser-checks` 独立技能
├─ 实验设施与可观测性
│  ├─ 已实现/局部验证
│  │  ├─ 包内自包含 OTLP Collector/SQLite、原生 Pi timing、模型/成员剖面与查询/静态页面
│  │  ├─ 历史 OTLP 接收→停止→单 DB 读取通过；运行中 viewer 可读 sessions/Pi timing，并保留原始错误链接
│  │  ├─ token 按 provider usage 与 assistant message 去重，input/output/cacheRead/cacheWrite 分列
│  │  └─ 时间拆分请求、首 token/生成、工具进程、队列/消费、恢复；并行时间不求和，未知保持未知
│  ├─ 尚未完整验证
│  │  ├─ 新恢复已实际收到 logs/traces/metrics，证明 OTLP 接线可用；完整率、官网/WSL 端到端收益仍未知
│  │  ├─ capture timeout 的缺失范围未知；`receive_errors=0` 不能证明无丢批次
│  │  ├─ viewer 的运行中页面是快照，不是终态或视觉交互验收
│  │  └─ token/cache 数是原生报告值，不等于供应商账单；`cacheRead=0` 不能推出实际无 cache hit
│  └─ 官网历史 HTML
│     └─ 上一轮 Issue/PR 已重建为 GitHub-like 静态页（证据见文末入口）
├─ 模型配方与 WSL 两矩阵
│  ├─ 冻结输入与授权
│  │  ├─ 两题矩阵：GitHub + Sheet；Flash Team 配方走官方 API；不使用参赛额度
│  │  ├─ DeepSeek 配方中 DS 走用户 DeepSeek、GLM 走 BigModel，均经 4018 gateway；不笼统归为官方 API
│  │  ├─ 生成冻结后才可做本地代理评分；本地分数不能冒称官网隐藏测试分数
│  │  ├─ 原生子角色模型保持原配方；模型替换属于 agent-profile/独立 variant
│  │  └─ Qwen/MiniMax 两题已按用户要求停止/取消，保留工作区，不自动重启
│  ├─ DeepSeek 观察边界
│  │  ├─ attempt-02 停止前只完成用量/进展截面；DeepSeek GitHub 尚无 DeepSeek 成员参与，不能作为模型对照
│  │  ├─ DeepSeek Sheet 见过 vision 子代理响应；仅有一次子 Issue #5 需求整理委派
│  │  └─ 因此 DS vision“曾参与”有证据，“改善根拆分/设计/质量”没有证据
│  └─ WSL 运行语义
│     ├─ attempt-03/04/05 都是保留半成品的热修复接续，不是从需求重新生成
│     └─ 所有 session 数、旧 JSONL mtime、容器存活都不足以证明新模型活动或完成
├─ 当前热修复主线
│  ├─ attempt-03：instruction revision 不兼容导致旧 provider session blocked，随后同 member_login 物化触发唯一键冲突
│  ├─ attempt-04：刷新 native 材料时遇到 AppleDouble `._pi-deepseek-fast` 非目录，未进入新模型阶段
│  ├─ attempt-05：已清除 metadata、完成 runtime/native 刷新并进入 Braid；GitHub/Sheet 随后均 `local run blocked`
│  │  └─ 新 DB 显示 applied reset 的 provider session/agent idle，但旧 assignment 仍 blocked，另有 materializing reset 未完成
│  ├─ attempt-06：Linux 编译与真实 DB 副本/定向回归通过；两题已保留半成品和成员身份恢复，并产生新的 assistant/tool 活动
│  └─ 当前结论：热修复恢复已确认，仍在生成；不等于完整交付、评分或产品收益
└─ 未完成 / 推迟事项
   ├─ 生命周期修复已应用并真实续进；持续观察新运行是否再次出现具体缺陷
   ├─ attempt-06 已有恢复后新模型消息/工具结果；仍待两题终态、采集完整性与交付，再做本地代理评分
   ├─ 21,206 条历史问题的专项因果复现仍需单列；Codex reset 端到端验收、新版本噪声/质量收益尚无结果
   ├─ 通用预制服务/检查工具是否值得落地；先复用现有 Harness/PBB，不写生成应用内容
   ├─ 新恢复采集的完整率与 capture timeout 影响范围；不以历史 viewer 快照替代
   ├─ 官网可追溯性/commit-history 进一步诊断（用户暂缓）
   └─ 不采用：继续堆叠提示词、Braid 自动裁决业务契约、根关闭替代全部对象终态、自动重启 Qwen/MiniMax 或旧 Lite 控制器
```

## 证据入口

- [当前总图](../iteration-map.md)
- [Braid 产品/技术复审与 attempt-05/06 状态](packet.md)
- [产品加固与因果结论](../braid-product-hardening/packet.md)
- [实验设施与官网冷恢复](../experiment-infrastructure/packet.md)
- [停止前模型用量与进展](../experiment-infrastructure/cells/flash-deepseek-process-comparison.md)
- [共享契约与 Braid 投递因果](../experiment-infrastructure/cells/shared-contract-braid-causality.md)
- [运行中诊断、OTLP/token/timeout 边界](../experiment-infrastructure/cells/live-diagnostics.md)
- [GitHub 结果/判据诊断](../github-score-diagnosis/results.md)、[Sheet 诊断](../sheet-score-diagnosis/findings.md)
- [官网协作 HTML 重建](../../runs/official-collaboration-review/index.html)

## attempt-06 恢复核实

GitHub `pi-braid--hackathon--github-0fe4e541703143` 于 04:49:39 UTC 进入 Braid 恢复，新 Pi 会话于 04:50:04.164Z 产生 assistant 消息并调用 bash 查看工作树、读取评论。
Sheet `pi-braid--hackathon--sheet-e1454bb0055129` 于 04:49:53 UTC 恢复，04:49:57.782Z 创建的新 Pi 会话随后产生 assistant/tool 活动。
只读 assignments 核对保留原成员身份（GitHub glm-1/glm-2；Sheet 既有 glm/deepseek 成员），未发现本轮重复 member_login 错误。
控制器 PID199559、采集 PID199628 持续运行；采集遵循前十分钟每三分钟、之后每八分钟。两题仍在生成，没有新评分。
