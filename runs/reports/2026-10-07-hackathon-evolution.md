# Hackathon Evolution 阶段结果（2026-10-07）

本报告整理本任务截至正式 GitHub 于北京时间 21:02:04 完成官网评分的已完成结果，供回顾实验与选择后续方案。实时状态、授权及后续结果由[任务 packet](../../tasks/pi-minimal/evolution-20261006/packet.md)维护；本报告不是第二份运行台账。原始材料保留原位，未据本次整理删除或迁移运行数据。

## 范围与结果

`evo-sheet`、`evo-github` 分别指 `hackathon-evolution--sheet`、`hackathon-evolution--github`，与普通 `sheet`、`github` 及 GitHub stages 分开记录。本地运行通过自费模型 API 实际生成，完成冻结后独立官网 `self_funded` 应用重放评分；这些分数不用于参赛或上榜。正式运行由参赛 Agent 在官网注入基线上实际生成，不使用预制应用重放。

| Variant / 主模型 | 任务 | 官网结果 | 评分回执 |
| --- | --- | --- | --- |
| pi-minimal-vv / GLM-5.3，首轮 | evo-sheet | 0/30；缺少公开 EVO 初始数据，不能当作 30 项业务实现分别失败 | [首轮现场与诊断](../../tasks/pi-minimal/evolution-20261006/execution.md)；run `cb62eb518145` |
| pi-minimal-vv / GLM-5.3，修正输入后 | evo-sheet | 独立评分 **22/30** | [4526fbd9e2b6](../pi-minimal/evolution-20261006/rerun-20261007/glm53/official-replay/score-receipt.json) |
| pi-minimal-vv / GLM-5.3-Flash，修正输入后 | evo-sheet | 独立评分 **22/30** | [2d6b8d24f9d5](../pi-minimal/evolution-20261006/rerun-20261007/flash/official-replay/score-receipt.json) |
| pi-braid-i14-reviewer-cleaner-e2e / GLM-5.3 | evo-sheet | 独立评分 **23/30** | [72095e05a3a4](../hackathon-evolution/i14-combination-20261007/glm53/official-replay/score-receipt.json) |
| pi-braid-i14-reviewer-cleaner-e2e / GLM-5.3-Flash | evo-sheet | 独立评分 **24/30** | [2ee5fc015bfa](../hackathon-evolution/i14-combination-20261007/flash/official-replay/score-receipt.json) |
| pi-minimal-vv-tailwindcss / GLM-5.3-Flash | evo-github | 独立评分 **8/30** | [908d359c544b](../pi-minimal/evolution-20261006/tailwind-github-20261007/official-replay/score-receipt.json) |
| 官网原版 pi-minimal-vv / GLM-5.3-Flash，修复重试后 | evo-sheet | 正式运行 **23/30** | [926215fbc9f3](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-retry-1/score-receipt.json) |

| 官网原版 pi-minimal-vv / GLM-5.3-Flash，同一正式提交 | evo-github | 正式运行 **15/30** | [7746d1de4b92](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/score-receipt.json) |

首轮 vv Flash 曾按用户要求停止，不计自然完成样本。第一次正式 Sheet run `a1833bf6f972` 因供应商连接重置和原生重试漏识别退出，没有功能测试结果；它是设施失败，不计为有效业务零分。同一正式提交 `e2f81e564251` 已取得 Sheet 23/30、GitHub 15/30，原始通过数合计38/60（63.3333%）；平台惩罚后综合分49.65459981256811，不能与通过率混称。提交仍为latest，尚未选榜。新增 I15 Flash evo-github 尚未自然完成，其后续状态由原 owner 与 packet 维护。

## 可以采用的结论与比较限制

这批 evo-sheet 样本中，I14 Flash 的官网通过数最高，为 24/30；I14 GLM 为 23/30，两项 vv 为 22/30。这是单次应用的结果，不能据此证明模型或 Harness 的稳定优劣。角色配置、生成耗时、机械恢复和人工接续不完全一致，未形成控制变量的重复实验。

I14 GLM 在 16:09:49 自然退出 0，交付 commit `835a88524be447fbbbfba3db88668837b69e2609`。它和 I14 Flash 均有机械恢复及一次真实 operator 接续，不能描述为全程无人干预。I14 GLM 的新版 GLM/Kimi 路由及 Pi retry 补丁未实际部署，不把后来公共配置归算为该运行使用版本。精确运行身份和恢复历史见[I14 执行记录](../../tasks/pi-minimal/evolution-20261006/i14-execution.md)。

I14 GLM 公开 WHEN/THEN 验收 30/30，额外边界 6/7；官网独立评分 23/30，两者测量范围不同。首遍公开验收有两项点击超时，保留原件后在新独立数据副本定向重验通过，没有改冻结应用。真实滚动检查确认行、列及组合冻结均固定。剩余额外边界是保存 API 返回 503 时，数据库原值保留而 UI 不回滚。I14 Flash 的公开 30 场景通过，额外边界 5/7；vv 的后续强化检查也暴露了滚动冻结、保存失败和校验边界问题。具体条件见[GLM 验收原件](../hackathon-evolution/i14-combination-20261007/glm53/acceptance/acceptance-result.json)及各[执行入口](../../tasks/pi-minimal/evolution-20261006/execution.md)，不能从公开通过数推断隐藏失败原因。

官方 evo-github 基线已采用 Tailwind 4，并与本队初赛 Stage 3 的 51 个 frontend/backend 文件一致，另带原旧归档未能证明的数据库。Tailwind 变体此次主要测量增量实现，没有实际 UnoCSS 到 Tailwind 的迁移对照。其公开验收 12/30，15 项被搜索导航缺路由造成的 404 阻断，另有账号/校验问题；旧账号密码回归已实证。不能由被阻断的场景判定其全部内部功能失败。见[Tailwind 执行记录](../../tasks/pi-minimal/evolution-20261006/execution.md)和[验收原件](../pi-minimal/evolution-20261006/tailwind-github-20261007/public-acceptance-report.json)。

独立重放回执的 token/cost 为零，仅代表该评分不重新生成，不能代表本地模型调用免费。本地套餐实际账单不可得时保留未知。正式 Sheet 两次费用分别为 ¥2.285587、¥9.968867，GitHub 为 ¥41.341827；两题成功运行合计 ¥51.310694，含首次失败尝试合计 **¥53.596281**。GitHub 当前任务的674次Flash和13次Kimi完成响应合计169,305,628 tokens，与官方数量一致，按ARC价目核算¥41.34183628，差额仅为舍入。见[最终费用核算](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/pricing/final-recorded-consumption.json)。平台创建时 official_evaluation、启动后显示 self_funded 是用户确认的已知缺陷，原始字段不改写。

## 数据、输入与归档

任务特定补充约定由共同 bench 文件携带，冻结 SHA 为 `7f193120efffd0bf906a0875638754d0532ca3467a8b73b412bee3c1368f3644`；装配层绑定入口，官方 YAML 保持原样。Agent 负责增量创建公开 GIVEN 所需数据。I14 GLM 冻结 ZIP 静态含 102 份原业务 JSON，没有静态 EVO JSON；ZIP 内的 `seed-evo.js` 在应用启动时仅对缺失固定 ID 增量持久创建 31 份 EVO，原 102 份启动后字节不变。不能把冻结统计的 0 与启动后的 31 混作数据丢失或开发侧 fixture。官方材料来源见[资料指南](../../docs/deployment/hackathon-evolution.md)。

| 产物责任 | 原位入口 |
| --- | --- |
| vv 初始失败、修正后的两项生成、Tailwind GitHub、正式 vv 两题 | [runs/pi-minimal/evolution-20261006](../pi-minimal/evolution-20261006)；身份与分数从[主 packet](../../tasks/pi-minimal/evolution-20261006/packet.md)进入，细节由 execution.md / replay-inquiry.md 持有。 |
| I14 两项 evo-sheet 生成、公开验收和独立评分 | [runs/hackathon-evolution/i14-combination-20261007](../hackathon-evolution/i14-combination-20261007)；GLM 与 Flash 独立目录，不混用冻结或评分。 |
| I15 Flash evo-github | [runs/hackathon-evolution/i15-evo-github-20261007](../hackathon-evolution/i15-evo-github-20261007)；recipe、输入逐文件回执、新会话及终态冻结消费者独立保存。 |

已删除的 Tailwind GitHub 与 I14 GLM 临时快照均在删除前完整下载官网 project.zip 并核验 SHA256/ZIP CRC。[Tailwind 项目归档](../pi-minimal/evolution-20261006/tailwind-github-20261007/official-replay/project.zip)与[I14 GLM 项目归档](../hackathon-evolution/i14-combination-20261007/glm53/official-replay/project.zip)保留在 WorkSSD；删除后评分 task run 仍可读，原正式提交恢复为最新。自费快照也影响 latest-saved 门控，实测恢复边界和操作流程已归[运行说明](../../docs/deployment/hackathon-evolution.md)。

本次整理已补齐 vv 两项 22/30、I14 Flash 24/30、正式 Sheet 23/30 的完整官网 project.zip，均原位保存下载来源、HTTP 200、SHA256 与中央目录/全成员 CRC 核验回执；四份约 791 MB。见[补档汇总](../pi-minimal/evolution-20261006/scored-project-archive-summary.json)。下载只读取官方产物，没有创建或删除快照、改变参赛资格，也没有读取隐藏内容用于分析或回灌生成 Agent。运行目录由 Git 忽略，交接须保留这些实际文件，不能仅依赖源码 clone。

2026-10-07 用户授权进一步精简本任务七份官方项目归档。当前上述本地 project.zip 均为精简版，原下载回执和官方原 ZIP 哈希保留；新包与删除清单见[精简汇总](../pi-minimal/evolution-20261006/project-trim-summary.json)及各包旁置 project-trim-receipt.json。只移除明确的 browser-cache 和 npm 的 _cacache，保留 npm 安装日志、应用/业务数据、需求、官方评测记录、原生/Braid 过程及图像证据。保留成员逐一 SHA 与源包一致，七份新 ZIP CRC 均通过。合计由 1,085,330,143 字节降至 242,978,476 字节，释放 842,351,667 字节（77.6%）；精简版不提供完整开发环境恢复承诺。

正式 evo-github 的 20:11 运行中阶段快照另作[定向诊断](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/diagnosis-20261007-201100/diagnosis.md)：证实进程清理命令反复中止，但后续自验取得36/36、后端37项及构建成功；该自验不是官方评分。阶段归档精简至157,450,164bytes，源官方下载身份与精简身份各自保留，不混入上文已完成样本或最终归档。更近状态及动作仍以任务packet与所属消费者为准。

正式 GitHub 最终官方归档另于21:15闭环：源ZIP560,187,023字节，精简后158,042,657字节，释放402,144,366字节。保留的2681个成员逐一SHA一致，ZIP CRC通过；源包与精简包哈希分别保存在[归档闭环回执](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/archive-completion-receipt.json)，不与20:11阶段快照混用。

最新正式GitHub已进一步完成[费用、时间与质量过程剖析](../pi-minimal/evolution-20261006/formal-sheet-flash-20261007/formal-github/analysis-final/analysis.md)：687次模型响应与官方token对账，后台回执收尾47分26秒约¥6.79；自验36/36与官方15/30差异有入口、持久性及详情判据缺口。共享PBB批量通知与E2E覆盖指南已优化并核实装配/编译，尚无新运行效果实证。
