# I11：恢复停滞根治与真实交付距离

当前阶段：两题生成已完成，最终交付已冻结并上传官网以self_funded重放评分；后续连续性与协作操作修正转入I12。2026-09-30，用户要求找到过去两次 I11 卡住的根本原因，做长期修复，同时分析两题 Issue/PR、估计剩余时间并核验 I11 改动。

## 问题与判断边界

已知故障发生在 Pi 原生 `new_session` RPC：30 秒后超时，尚无原生会话身份、模型响应。
上一修复仅让离线恢复接受已完成的旧 turn 引用；09:32 的新 GitHub 尝试证实三项 reset 已重新物化，但全部再次握手超时。
因此恢复筛选缺陷与原生启动缺陷分开处理，不以解封或容器 Running 代表恢复。
已确认 Braid 重复初始化 Pi、冷启动误用30秒控制请求时限，以及恢复筛选和观察接线缺陷；当前新握手实际需要123–129秒，取得身份后均有模型响应。旧失败缺少逐阶段计时，无法把其全部耗时归给扩展或磁盘中的单一因素。

## 并行分工与产物

- 主线：追踪 Braid→Pi 进程→扩展→RPC 的实际路径，修复明确根因，保留真实错误与恢复边界，更新当前状态。
- recovery 负责人：保存 Sheet 成功恢复证据并保持运行；将新 binary 部署到受阻 GitHub 的保留现场，核验实际响应及交接消费，接上两题 watcher；不循环重启、不另改源码。
- GitHub Astra：写 [github.md](github.md)，审查对象、会话、交付余量和修复有效性。
- Sheet Astra：写 [sheet.md](sheet.md)，同样口径独立审查。

审查将部署身份、实际触发、行为效果分开；继承的 I10 产物不能当 I11 的新增收益。
剩余时间基于实际剩余需求、集成和验收，运行设施故障另列，不按 OPEN 对象数机械估算。

## 证据与验收

最新 GitHub 失败：`runs/iteration11/20260930-completed-turn-resume/github/evidence/first-resume-failure/`。
两题完整停止现场：同目录 `{github,sheet}/source/template.tar`，按需读取，不重复全量解压。
历次部署与观测见 [recovery-curation](../recovery-curation/packet.md)。
修复先核对真实启动源码和原始现场，再做编译/语法与已授权实际接续观察。
原始 I10 与 pi-minimal 官网运行不受本任务影响，不改变 I11 模型路由或凭据。
不新增/运行 Factory、Braid、SVC、设施测试或模拟探针。

## 已应用的修复

1. Pi 进程启动本身已创建新会话；Braid 再请求 `new_session` 会销毁首个运行时、重复加载扩展及执行 shutdown/start hooks。改为直接 `get_state` 取得新会话身份，恢复仍用显式 `--session`，不改变模型或原生子代理所有权。
2. 首次 `get_state` 包含进程和扩展冷启动，不能套用普通控制 RPC 的 30 秒时限。单独使用 `pi.startup_timeout_seconds`（默认180秒），普通 RPC 保持30秒；有界失败且不自动无限重试。使用 Pi 自带 PI_TIMING，记录 PID/cwd/home、初始化耗时和具体请求错误。此项保证启动时间预算职责正确，是否足够由真实接续验证，不能仅以改超时宣称根治。
3. 离线恢复依据同一活动工作项、已停止环境、终态旧 turn、失败物化且无 native identity 的持久事实，不再依赖 `session is unavailable` 这一错误文案。具体错误可保留到 physical/reset，不被恢复条件迫使丢弃。
4. 已证观测断点：本次 launch 只启动 lab run，没有监控采样调用者。外层 running 只表示容器存活；观测消费者须暴露 OPEN 工作负责人全部 blocked、无 active turn、仍有待办的设施阻断，接入既有周期观察。

两题内容审查已完成，详见 [GitHub](github.md) 和 [Sheet](sheet.md)。GitHub 剩余有效时间约20–45分钟；Sheet 通常45–120分钟，均以设施恢复且没有新产品缺陷为前提，官网排队/评分另计。


## 当前验收进展

Linux Braid编译通过，binary SHA256 `d76d65f133979a9f310b39e73fc254f727b564734ee1513c4febe6fbecb083be`；基于上一冻结源码加三文件增量，未混入其它工作树改动，构建回执在 `runs/iteration11/runtime-stalls/build/`。
两题修复矩阵和剩余时间已由独立 Astra 完成；主线根因判断见 [diagnosis.md](diagnosis.md)。
新观测代码经真实GitHub受阻现场返回blocked、watch退出2；真实Sheet新运行未误报。
Sheet本次旧binary接续已在01:49Z取得根/PR13真实响应，保持有效生成；新binary先用于仍受阻GitHub。
WSL已清理本次已消费的恢复ZIP/输入重复包，未改变运行中的实际template/runtime或I10原件；回执在 `20260930-completed-turn-resume/reclaimed-*.json`。

2026-09-30 10:03 CST：GitHub 新 attempt `pi-braid-i11--hackathon--github-0d0cb6e9982fc1` 在原保留工作区接续。三个握手分别122763/124012/129190ms，01:59:43–44Z三者均产生真实assistant；根首个工具调用成功读取评论#331/#332，DB中#332对根与实现负责人的投递为delivered。容器内binary实测与新构建哈希一致；证据在 `runs/iteration11/runtime-stalls/github/evidence/first-response/`。
Sheet `396538bc0dda96` 保持旧binary继续，已成功恢复root/PR13；不将Sheet成功误算为新binary验收。
两题watch实际启动，GitHub PID1698832、Sheet PID1698834；首条分别2/1 active turn、6/21 pending event，无blocked owner。它们读取声明的真实DB，记录到WSL `runs/iteration11/runtime-stalls/watches/{github,sheet}/watch.jsonl`，退出码单独保存；文件采样与跨会话自动唤醒是不同能力，本次未验证后者。

## 验证后仍保留的改进项

| 问题 | 当前依据 | 处理边界 |
| --- | --- | --- |
| 无动作通知后仍重复核对 | 两题均有正反例；Sheet仍翻旧材料、重复确认已完成模块 | I11减少重复工作的目标只部分达到，尚未定位为同事件重复投递，不另加未经验证的调度补丁 |
| 候选SHA变化诱发重复验收 | Sheet两提交整树一致；GitHub纯文档变化仍触发全量检查 | 保留具体反例，需进一步区分有效运行条件变化与仅提交身份变化 |
| resolve作用范围误解 | GitHub #324–#327一度折叠仍在用的裁决，随后unresolve | 工具可用不等于语义理解正确；记录为协作体验残余问题，未冒称本次启动修复已解决 |
| 未触发的能力边界 | Sheet无新sub-agent spawn；两题无新vision length案例，20%上下文降档也无充分样本 | 继续记为未验证，不为补验证而打断当前收尾或制造新实验 |

本轮Braid恢复源码提交 `0712a58`；编译制品基于冻结源加本任务增量，与完整脏工作树分开记录。

## 用户补充归因的复核（方案讨论，尚未应用）

2026-09-30用户提供两题原生记录的三条进一步归因，要求主线判断。源码核对补齐以下边界：

- R3b：`begin_context_reset_connection` 以 `selected_turn_id.is_some() || self_edit` 设置 continuation；`complete_context_reset` 随后创建 `reset_continuation` wake；`render_event_references` 对该输入仍写“请处理工作项”。因此自行整理可以重新制造处理请求，不能只将反例归于Agent无视通知指引。修复设计须区分更新投影、接续尚未完成的处理和投递新输入；Braid呈现发生的事实，不判断业务是否需要重新验收。保留description编辑完整重建及真实新问题联系已完成负责人的能力。
- I11-09b：SVC interpreting-results及两份角色指令已包含证据适用性、停止复验及match-head用途；新增同义原则不足以解决旧PR正文“head变化即重验”的冲突。需要清退当前对象中冲突纪律，使交接分别携带原观察归属、当前候选适用性与合并目标。历史原始观察不改写；真实产品、检查、数据或运行条件变化仍需相应反馈，不按文件后缀豁免。
- I11-06b：resolve/unresolve参数接收评论ID，实际映射至thread根并更新resolved_through；命令成功返回单位值，未清晰返回实际范围。保持讨论级语义，帮助与回执明确thread根及折叠范围；局部整理使用hide及理由。resolved后新增回复仍可见，不新建消息过滤器。

此外，已完成工作项正文应保存其交付、约束和证据，不持续镜像其它分支/工作项的最新全局状态；集成任务拥有当前集成状态并链接历史成果。此为文档职责修正，Braid不自动分类自然语言内容或重写项目结论。
本次只读实现核对与packet整理；未修改运行、应用或上述产品机制，也未启动实验。

## 完成交付与官网评分

两题生成成功结束，根Issue关闭，最终PR合入：GitHub main `442dc1cf776f144688d8ad667a76dd026f553e27`，Sheet main `10cba2ad888fd60f283382158c1bfb00b0fad240`。
按用户要求立即冻结为应用重放包，未继续生成或修改应用。包SHA256 `bc4cab139ed9cf3c282a1b3359ed1d6a8e5f552dcf13efda30144a44fb5076fc`，来源与原始证据见 `runs/iteration11/final-replay-20260930/{replay-manifest.json,official/}`。
官网submission `87acf1919de7`；[Sheet run fe617f4f8526](https://arc-bench.com/runs/fe617f4f8526)、[GitHub run e68661975b53](https://arc-bench.com/runs/e68661975b53) 均确认billing_mode为self_funded，重放不调用模型、不占参赛额度。
官网两题完整评分已收集：Sheet为59通过/41失败，功能8/24；GitHub为4通过/96失败，功能1/47。两题部署、应用启动与评分阶段均完成，均不提供逐例错误；不根据阶段完成或分数推断具体失败根因。3+8采集脚本已按两题终态正常结束，journal中phase=collected、pending=null。
I12的工作流修正、独立恢复起点及人工介入console见 [I12 packet](../../iteration12/packet.md)。原始I11交付及评分反馈不改写，也不将隐藏评分反馈注入I12生成。
