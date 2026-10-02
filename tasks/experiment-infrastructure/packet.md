# 官网恢复与监控

状态：已完成恢复、监控及未完成状态冷恢复均取得对应真实证据。用户确认冷恢复平稳续进即可，dd3bda66bcb3 已按授权取消；自包含观测性实施中。

## 目标与授权

减少中断后丢弃成果、重复打包及人工盯运行的成本，保留来源与原始错误。
用户本轮明确要求：“你来搞定断点恢复、官网运行监控的基础设施；并且对已经明确的耗时根因提出相应的解决方案。”
设施修改已授权；前一阶段未新增模型运行。随后用户明确要求官网完成验收，已启动真实未完成快照的 self_funded 接续；不提交源码。
工作方法方案已由用户复核通过并授权实施，落点见 ../braid-product-hardening/cells/working-methods.md。

## 已落实

- `competition collect` 使用通过数与失败数取得总数；隐藏逐例列表不会覆盖聚合成绩。独立记录评分阶段和逐例材料是否可用；所有任务收齐后摘要为 completed。
- `hosted_monitor` 复用已有 journal，run 启动后前 10 分钟每 3 分钟、随后每 8 分钟采集；运行中默认不下载整个工作区、不调用模型。终态下载原始证据、告警并退出；下载失败另记错误，不无限等待。语义审查显式用 `--review`；联动取消也需显式授权，低分 FAILED 不当作设施失败。
- HTTP 状态请求与上传有明确传输超时；不自动重试不确定写入，继续沿用原 journal 的 recover 核对。
- `package_completed_recovery.py` / `recover_completed.py` 保留原工作区、请求身份和 published main。默认完成模式发现开放项即拒绝生成。
- `--continue-generation` 整理原 Git 索引、文件、工具环境和原生会话的接续接线；不含逐 run SQL 手术。

## 验证与限制

已完成快照恢复的两条自费 run：GitHub `595ab74c90a9` 为 4/100；Sheet `1efffb84ae1b` 为 58/100。
生成、部署、评分均 completed，未新增模型会话；见 [交付终止记录](../acceptance-integrity/cells/terminal-contact-loop.md)。
本轮监控对这两个真实 run 完成 API 读取和 workspace 下载，done 后退出，没有调用审查模型、取消或启动运行。
[采集结果](../../runs/e20260928-completed-replay/monitor/20260928T000356.279890Z/outcome.json) 保留分数与阶段，两个 workspace 均无采集错误。

未完成接续此前的阻断已落到 Braid 修正：新增显式 `--offline-resume` 宿主断言、撤销旧身份并重放真实输入；unknown 重放改为新事件，同时修复旧快照遗留的损坏批次。
真实恢复快照显示原 Issue #6 关闭、新 PR #12 合并且无新空输入批次；达到用户确认的平稳续进验收范围。旧 BRAID_COLD_STOPPED_SESSIONS 不再使用，也未在 Factory 里改库。
Git clone 元数据在官网 ZIP 中缺失时只能依据 bare origin 重建索引并保留工作文件，无法恢复未发布提交历史。
未完成恢复 run 已由用户主动结束，没有评分结论；已完成恢复模式另有完整评分证据。

## 下一步与分工

[Braid 独立审查](../braid-architecture-audit/packet.md) 给出冷恢复、空批次和生命周期问题的根因及修正方案，使用明确的宿主停止边界，不让 Factory 接管 Provider 生命周期。
工作方法建议见 [反馈成本前移](time-cost-proposals.md)：检查环境、共享契约和验收判据的来源。
得分诊断分别由 [GitHub](../github-score-diagnosis/packet.md)、[Sheet](../sheet-score-diagnosis/packet.md) 独立 Agent 完成，主 Agent 汇总决策。

[设计](design.md) 保留恢复语义、实施顺序和验收方案；运行入口见 [运行说明](../../docs/deployment/index.md#实验恢复与反馈循环)。
历史 g03–g05 的手工恢复包、来源与逐次失败见 `runs/e20260927-03-github-resume/`；旧 GitHub g05 与 Sheet g04 均已按用户要求取消，其状态不因新恢复 run 改写。


## 当前实施单元

[离线恢复](cells/offline-resume.md)记录主 Agent 接线与真实恢复安排；[事件重放](cells/replay.md)由独立 worker 修正 Store/Actor。
使用已取消的 Sheet `3445926a1142` 在 13:38 保存的原始快照，根 Issue 与 #6、若干 PR 尚开放，包含 7 条 running turn，符合未完成恢复的验证前提。
WSL 复用现有 Rust 构建缓存产出 Linux 二进制；按用户追加要求，不启动重复本地生成，转官网自费验收。
得分原因分析已追加追踪指令、技能采用、原始需求传递和模型因素，不停在应用缺陷清单。


用户进一步限定：不采用由 Harness 写入生成应用（包括脚本）的检查入口方案。该方案已撤回；先逐命令拆解两题环境准备与排障时长，再决定外部工具/提示词的修正。不修改生成应用内容。


官网验收追加授权：“你应该启动官网运行，不然的话，验收就不完整”。本轮改为 Sheet 3445926a1142 未完成快照的官网 self_funded 接续，沿用旧模型材料；WSL 仅负责 Linux 编译。环境排障拆解继续由两个原分析 Agent 分别完成，主 Agent 负责恢复实施与官网运行。


官网 Sheet 接续已启动：submission `6a2d7c30464c`，run `dd3bda66bcb3`，当前已完成部署、正在生成；终态由专用低成本监控 Agent 回传。尚未取得恢复后的完整交付/评分结果。
环境拆解已由两个原分析 Agent 分别完成：[GitHub](../github-score-diagnosis/environment-cost.md)、[Sheet](../sheet-score-diagnosis/environment-cost.md)。下一步先盘点既有后台执行/服务管理能力，再提出外部工具或提示词修正，不制造生成应用内容。


## 细粒度耗时剖析

用户要求继续减小剖析粒度。仍由原 GitHub/Sheet 两位分析 Agent 分别进行，主 Agent 汇总判断。
粒度从“排障窗口”下沉到命令执行、后台化、结果产生、首次读取、诊断、修正和复跑。
区分直接可测时间、上下界、并行重叠与未知间隔，不把消息间隔冒称模型思考，也不求和 sleep 参数。
重点识别“什么时候已有足够证据做下一步”及其后可以省去的动作；不为了填满总时长而虚构归因。

用户要求将监控调整为 run 启动后前 10 分钟每 3 分钟、随后每 8 分钟；以官网 started_at（缺失时 created_at）计算，不以本地监控重启时间重置。共享契约合并后约 28 分钟的排障由 GitHub 原分析 Agent 单独细化，先核对原窗口，再还原冲突形成与修复链。

用户已批准全部三项 Braid 缺陷与三类清理，独立产品审查和新 WSL variant 实验归 [产品加固任务](../braid-product-hardening/packet.md)。当前官网冻结 run 不改包。

## 自包含观测性
用户已批准 Collector/SQLite/查询与 token、耗时剖析接线，参见 [实施与证据](cells/self-contained-observability.md)。
取消运行时发现 summary 将“未收齐归档”误报为 running；现已有远端终态但未完成采集的矩阵显示 terminal，并在简洁任务输出显示 remote_status。已用 dd3bda66bcb3 的实际 journal 读取确认 terminal/CANCELLED，无新增网络写入或测试。
