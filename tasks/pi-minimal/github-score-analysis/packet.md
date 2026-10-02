# Pi Minimal 2026-09-30 GitHub 2 分增量诊断

## 当前增量：仅 I11 GitHub 的机制有效性（2026-09-30）

授权与范围修正：用户明确“他说的是I11，特别是GitHub，Sheet也要分析，并要求分别两个会话”；本会话只承担 `e68661975b53`，不追加 Pi Minimal 或 Sheet 调查。用户要求“利用sub-agents先整理原始资料，包括pi sessions、issue、pr等”，并要求“避免从生成应用问题反推过程缺陷，而是正向从需求出发，理解agent的运行过程，在哪里选错了、做错了，以及可能是为什么”。

状态：有界增量完成，主报告为 [I11 GitHub正向机制分析](i11-mechanisms-forward.md)，分线报告和来源索引见主报告。主线已独立核读初始输入/需求续读、M1反例裁决与合并、M5负向断言/咨询及packet重锚、M6排除/读取/替代审查关键原文。PR23终态原生session/DB在相关清单中未找到，父会话无额外已验证路径；保留证据缺口，不以产物补造决策链。分工为 `i11_requirements_svc`（需求、共享契约与 SVC 消费）、`i11_roles_forward`（原生子 Agent 输入输出与采纳）、`i11_collaboration_forward`（Braid Issue/PR 分工、审阅和交接）。主分析独立回读原始证据，按理解→规划→分工→实现→验证→交付串联；直接证据、解释假设、替代解释和缺口分开，含成功与失误。产物与4/100作为末端核对，不把分数当过程原因。

只读分析及报告写入；不修改 variant、源码或技能，不运行测试、下载内容、模型或新评测，不提交部署。历史报告保留。重要发现及最终结果按用户要求发父会话统一汇报。

## 已完成增量：原生决策链与 I11 对照

用户进一步要求“追溯 pi sessions…找到导致权限理解错误、功能范围遗漏的根本原因”，并明确建议 sub-agents 初步整理。此次授权覆盖两个有界整理 Agent，取代首轮不委派约束；主线回读原文核实。随后新增 I11 GitHub run `e68661975b53`（用户报告4分），授权一个独立有界分支核验身份、下载并复用已有分析。Pi 两条链不被替代。

当前分工：permission_trace → permission-trace.md；milestone_trace → milestone-trace.md；i11_github_trace → i11-e68661975b53.md。均不改 variant、不运行下载内容、不启动生成/评测或模型试调用，原证据不覆盖。

增量结论见 [causality.md](causality.md)；两条独立整理为 [权限](permission-trace.md)、[里程碑](milestone-trace.md)；I11身份、下载及因果见 [I11报告](i11-e68661975b53.md)。三个分支均已完成，主线已独立回读关键原文。I11为4/100、1/47，需求与Pi相同；权限错误未重现，PR里程碑遗漏源于明确知道但任务承接悬空。新binary实际接续、184冻结文件全部送达已核实。候选已按这些根因修订，均未实施。

主线已核实：主 Pi session 711行、advisor原生session 52行，均没有记录 compaction/branch-summary 事件；主错误设计最早已在01:23:59的L30出现，早于咨询advisor。两条链均完整材料可见，早期设计/复核发生错误；无法把模型内部原因进一步定为领域先验或压缩失忆。

以下保留首轮交付记录；当前结论和候选以以上增量为准。

状态：完成下载、终态核验和有界分析，结论见 [report.md](report.md)。未实施候选改动。

授权原话：“请下载这次GitHub题目的工作区文件，结合实际评分、执行记录及已有分析，解释低分原因，判断能否通过修改提示词、Agent Skill等改善。” 用户后续要求保持增量范围并尽快交付。

核实身份：GitHub c3fea0c3488c / hackathon--github 为 2/100（0/47 功能）；Sheet 6dc68bef2081 / hackathon--sheet 为 40/100（5/24 功能）。同 submission f12fdf5540a1、pi-minimal，冻结 ZIP b4196fd387909a21a39a34e8c10f2a69c621057c7ed4f0647b60db3eeaf66e6a；官网均完成生成、部署和评测。

原始证据：runs/analysis/pi-minimal-github-20260930/20260930T031746Z/。GitHub fresh ZIP 88,716,489 字节，1465 项 CRC 通过；Sheet 复用终态留存 ZIP，评分状态重新读取。证据定位见 report，不修改旧 journal。

已证：Write 权限被错误按等级放行、PR 里程碑范围遗漏；搜索工具失败后直达结果页导致验收误判。Kimi advisor 成功且读过认证/组织技能，主线未落实相关验收。登录入口重名、无条件启动删库的评分影响尚不能确定。官网逐例错误缺失，不外推到全部 98 例。

复用：tasks/github-score-diagnosis/results.md、continuation03/functional-diagnosis.md、harness-causality.md，以及 tasks/sheet-score-diagnosis/packet.md。旧结论仅作定向取证线索；新证据和原生行号见 report 与 selected-trajectory.json。

已遵守：不改 variant/skills/应用，不执行下载内容，不编写或运行 Factory/Braid 测试，不启动生成或评分、不调用模型、不额外委派、不提交或部署；保留既有 dirty 工作树（调查时 HEAD 8e6ea7f）。最初沙箱 DNS 不可用，获工具批准后只读下载成功；无审批拒绝或剩余访问阻塞。

交接：建议优先调整验收路径规则及原子需求保真；仅形成候选，是否修改由用户决定。离线人工对照可验证规则能识别现有误判，不能证明提分；任何新生成/评测仍需具体授权和费用说明。
