# Factory26：09 阶段及更早历史地图

本文只保留 09 阶段及更早历史，不维护当前授权、运行或待办。接续当前迭代请读 [I13 packet](iteration13/packet.md)、[I14 packet](iteration14/packet.md) 及其 owner packet；下文日期、PID、供应商和启动安排均不得作为执行依据。


2026-09-28 历史快照。材料见 [08修复单元](braid-product-reaudit/cells/hotfix08.md)，阶段总图见 [阶段性树状报告](braid-product-reaudit/iteration-report.md)。

09 历史截面：continuation-03于09:20:00 UTC接续，09:21两题GLM与DeepSeek均有新成功工具活动；Braid角色归位和svc-sub-agents材料已核对。控制器509773、监控510138。新工作记忆整理方案已具体化、尚未部署。
该报告区分源码落地、真实运行证据、评分结果和未完成事项；具体授权与运行身份以 [当前 packet](braid-product-reaudit/packet.md) 为准。

- 上一批官网有效评分：GitHub 4/100、Sheet 58/100；均复用已生成应用，没有重新生成。
- Qwen/MiniMax 两题已按用户要求取消，不自动重启；[停止前模型用量与进展](experiment-infrastructure/cells/flash-deepseek-process-comparison.md) 是截面分析，不是完成结果。
- DeepSeek 两题已保留07半成品接续 attempt-08，4GiB/2CPU及原模型路由不变；截至2026-09-28 14:53北京时间，两题仍在生成，无新评分。
- 新版本对通知噪声、重做、验收可靠性和分数的收益仍待真实运行判断，不能由代码落地推出。

```text
目标：完整自主交付、可信验收、降低有效工作总成本
├─ 实验及结果
│  ├─ 上一批官网：GitHub 4/100、Sheet 58/100；分析与协作HTML已保存
│  ├─ 本地DeepSeek两题：08保留半成品续进，尚无本轮评分
│  ├─ Qwen/MiniMax：已取消；停止前模型用量与进展对照保留
│  └─ 热修09：上游诊断已收齐，用户批准后正在实施/打包准备；允许本地工作区有界人工修补并标注
├─ Braid产品与实现
│  ├─ 已落地：普通评论投递、收件范围、显式重建、关闭/终态/身份恢复修正
│  ├─ 待行为证据：通知回环/冗余、无效重建、旧输入消费、重复工作是否下降
│  ├─ 共享契约：历史投递缺口有证据；新运行已读后是否真正消费继续核查
│  ├─ 当前集成：外部Git合入识别修正、Issue/PR共享编号纳入09；前提就绪后派发的规划方法已补
│  └─ 保留边界：历史2.1万重复错误非全量复现；Codex reset端到端仍未验收
├─ 原生sub-agent与视觉
│  ├─ 官网+本地使用账本：成功、误拒、名字误用、取消、重复委派分开
│  ├─ 08：旧任务索引3次注入；父消费与在途终态唤醒尚待自然证据
│  ├─ 08：07:08后Issue8已正确调用vision并收到完成；父已读取报告，具体UI正确性/评分收益未证
│  ├─ 08：6次PBB等待误用仍在；就地错误反馈已完成技术预演
│  └─ 深查：具体可委派机会为何未采用，不能把零调用简单当坏结果
├─ 工具、技能与环境反馈
│  ├─ browser-checks已移除；exploration-tools已迁入explorer；MCP配置迁tools
│  ├─ agent-browser与Skill内with-service：已打包且有使用证据，适用性/采用继续查
│  ├─ Chromium长临时路径：根因明确，短路径+保留Pi状态位置为候选
│  ├─ Sheet检查wrapper：Agent自行修复并合入；旧worktree消费仍需核对
│  └─ 深查：依赖安装/构建/服务/浏览器/清理/复验的重复成本及有限资源并行
├─ Token与耗时
│  ├─ 官网生成链+本地07分类账已成；input/output/cache分列，缺口及悲观情景明确
│  ├─ 已证候选：重复executor、宽进程回显、无信息等待、被吞退出码后的重做
│  └─ 深查：长上下文来源、任务重做链、必要跨成员阅读与可避免重复的区别
├─ SVC与工作方法
│  ├─ V&V/初始条件/共享契约最小改进已落地，行为可靠性尚未证明
│  ├─ sub-agent原始讨论5条可见消息已整理，覆盖和未确认提案已标注
│  ├─ svc-delegation迁移+角色内聚+可便宜消费结果：已实施正文迁移，09打包中；真实采用待验证
│  ├─ 查询/等待/退出码/受影响复验按已有方法归属，避免同义叠加
│  └─ 深查：技能发现/选读/正文装载/具体行动的断点，区分内容与工具问题
└─ 实验设施与DX
   ├─ 半成品恢复、原始证据入口、时间窗/会话身份、静态HTML已落地
   ├─ 自包含OTLP/SQLite、token与阶段剖面已可用，完整性不由接收错误0证明
   ├─ 08 Collector计时已读回：persist慢与部分超时重合、记录重发已证；丢失及唯一瓶颈未知
   ├─ run-local监控与现有wait存在衔接缺口；不另造监控框架
   └─ 任务索引持续对账：已实施/已触发/已消费/已评分分开，旧未验收项保留
```

历史截面（15:01北京）：两题仍生成。GitHub后台作业已完成，根转向集成；PR5通过Git双亲merge进入develop后被手动关闭，不能只凭Braid MERGED数量判断代码未合入。REQ6a尚未指派，前提已具备，是可并行工作未派发；未见相关通知丢失。Sheet develop已有13条PR合入，main仍初始提交，REQ2结构恢复两项失败、REQ3范围移动、REQ5仍待汇合。

新发现：Sheet新版入口指令已接线，但仍把bg001传给subagent_wait；08其它子代理修复按自然触发证据验收。Sheet Chromium临时socket路径过长已由原生FATAL与短TMPDIR后成功定位到Harness环境候选；应用检查wrapper的lsof/set-e假失败已由Agent修复并经PR16合入；本地运行已获人工修补例外授权，但此项无需重复补丁。

定向进展：[GitHub作业与集成](braid-product-reaudit/cells/attempt08-progress.md)、[Sheet关键路径与成本](braid-product-reaudit/cells/attempt08-sheet-progress.md)。

运行分析：[子代理完整视图](factory-subagents/cells/usage-map.md)、[接口根因](factory-subagents/cells/native-discovery.md)。
Token分析：[用量、缺口和优化区间](experiment-infrastructure/cells/token-economics.md)。
设施与工具：[实时观测跟进](experiment-infrastructure/cells/live-observability-followup.md)。
共享契约：[投递与行为因果](experiment-infrastructure/cells/shared-contract-braid-causality.md)。
各支线的责任、细节和未完成项仍以 [当前 packet](braid-product-reaudit/packet.md) 的用户事项表为准。

以下仅保留历史决策脉络，不作为当前待办。当前状态统一查看上面的阶段报告及 packet。

## 2026-09-26 历史快照（不代表当前状态）


2026-09-26 按本会话决定、任务包和实际产物整理。
这里回答哪些工作仍欠结果；具体设计、授权和运行身份仍归对应 packet。
“已落地”不等于有评分证明收益；“待验证”也不自动产生一个新实验。
当前迭代以完整需求的自主交付、可信完成判断、低成本有效反馈为三个结果目标，详见 [目标与取舍依据](acceptance-integrity/packet.md#顶层目标与取舍依据)。

```text
Factory26：提高完整 Hackathon 的通过率
├─ 1. 当前主线：预算、交接和可信交付［正在实施］
│  ├─ 参赛额度停用；官网实验改 self_funded［已落地］
│  ├─ 昂贵模型限制到一个 Braid session［B GitHub仅根使用K3］
│  ├─ 生成自检避开 3000 与评测初始数据［B部署正常］
│  ├─ 子任务 comment 交接［B已写出，但@成员未投递］
│  ├─ PR --head 显式承接已发布代码［B观察到正常承接］
│  ├─ 最终验收对应最终交付提交［B根未恢复，整体未发生］
│  ├─ A：4c17843 官网干净回放［14/100，已复核］
│  └─ B：GitHub 0/100；Sheet取消指派阻塞已定位，未评分
├─ 当前：验收依据与最终整合［主体已实施，待本地验收；官网暂停］
│  ├─ GLM-Flash 根协调 + 强模型原生 advisor
│  ├─ 后续 Issue/PR 由 Agent 选择 assignee；Braid 只执行与限额
│  ├─ 子 PR → develop；根整合 PR → main并完成自动化完整验收
│  ├─ browser-operator 用于开发快反馈；最终验收是可重复测试/脚本
│  ├─ 降低可靠浏览器检查的编写成本：现成接口、工具指引、角色接线
│  ├─ 通用 PR base/head 与明确的完成交接
│  ├─ B新增：显式成员通知、统一可指派目录、静止不等于完成
│  ├─ Sheet补充：责任与执行资源解耦、取消指派收尾［已授权实施与本地验收］
│  ├─ GitHub协作差异审查：关闭后通信、ready耦合、关系/版本可见性［方向已认可］
│  └─ SVC：V&V分层框架→较系统的内容/导航方案［已认可］
├─ 2. Braid 产品主线［已落地多轮，真实协作仍在收敛］
│  ├─ Issue/PR、comment thread/reply、hide理由、resolve、reaction
│  ├─ GitHub式 CLI；profile用于派工，返回具体成员名
│  ├─ bare origin + 各工作项 clone + 真实 PR merge
│  ├─ 同 profile 的多个成员已参与运行；PR 合并与最终导出已有证据
│  └─ 剩余断点：根交接、已有代码承接、最终整合验收 → 纳入第1项
├─ 3. SVC［实现已落地，行为验收保持开放］
│  ├─ 参赛 Corpus 与开发 SVC 分开；参赛 CLI 已退场
│  ├─ 精简、行文与导航、shift-left、V&V 等内容已改
│  ├─ 单技能迁移为5项：任务包/调查/设计/实现/验证
│  └─ 尚欠：真实选读和方法采用的证据 → 从B轨迹观察，不强制调用
├─ 4. Factory 能力与角色［配置已落地，部分采用未验证］
│  ├─ 原生子角色 fresh上下文、SOP、工具知识、明确模型
│  ├─ rg / ast-grep / agent-browser / Context7 / Exa
│  ├─ Sheet与GitHub候选技能已选材并接线
│  ├─ 后台Bash及依赖已补；旧K3包未包含，不能算其验收
│  └─ 尚欠：官网MCP可达性、子角色实际采用、后台任务真实行为 → B观察
├─ 5. 实验与对照［不能合并成一个“已完成”］
│  ├─ Lite：49/66等已有基线；不是Hackathon成绩
│  ├─ 官网GitHub：1/100 → 4/100 → 11/100，各轮条件不同
│  ├─ K3根模型净收益［未证实；旧包K3也用于子Issue/PR］
│  ├─ mixed vs reviewer 本地两题对照［mixed生成终态，reviewer一题运行/一题排队］
│  └─ root-only旧参赛run已取消；后继是第1项B，不恢复旧链式运行
├─ 6. DX与工作方式［主体已落地，持续按任务使用］
│  ├─ 方案复核 → 计划/预演 → 开工确认 → 实现/实验 → 完整结果汇报
│  ├─ task packet/cell、仓库地图、文档系统、代码注释
│  ├─ variant独立实现；旧共享配置生成器与执行路径清退
│  ├─ 证据查询、原始错误入口、开发SVC安装、源码归档恢复
│  └─ 脚本等待 + 低成本Agent终态回传；取消scheduled监控
└─ 7. 明确暂缓或归档［不随本轮自动启动］
   ├─ 官网可追溯性/commit-history进一步诊断［用户暂缓］
   ├─ 更大模型/技能/reviewer消融矩阵［等有效完整基线后决定］
   ├─ 旧generalist、单模型、raw Codex/Pi配置［历史参考/归档］
   └─ playground自动实验、旧Lite-only控制器［已由新路径替代］
```

## 容易遗漏的五项

1. **SVC 任务没有关闭。** 五技能已打包不证明实际使用；从 B 的真实记录检查即可，不为证明收益另造一轮技能矩阵。
2. **独立 reviewer 是另一条尚未收尾的对照。** mixed/reviewer v2 在 WSL 的生成和模拟评分要取得结果，不能被 K3 官网实验覆盖。
3. **Context7/Exa 的官网可用性仍欠结论。** 工具已安装、开发机查询成功、Agent 是否调用和官网是否可达是不同事实。
4. **后台 Bash 的验收尚未完成。** 旧 K3 包缺插件；下一包须实际包含依赖，从新运行判断效果。
5. **官网展示追溯仍暂缓。** 公共接入和部分历史发布已有实现，页面空白原因未闭合；用户要求不增加 LLM 负担，不能靠提示词催填来补。

这些是当前未收齐的交付或证据，不意味着重新做已有实现。
本轮优先完成第1项；B 的现有轨迹可同时回答第3、4项的一部分，未发生的行为如实记为未观察到。
本地 reviewer 对照先收取已有结果，不自动重跑。

## 接续入口

| 事项 | 权威入口 |
| --- | --- |
| 当前授权与A/B | [预算与交付](competition-budget/packet.md)、[实验设计](competition-budget/experiments.md) |
| SVC内容与行为验收 | [Corpus](svc-corpus-review/packet.md)、[技能选材和拆分](hackathon-capabilities/packet.md) |
| Braid身份、Git和交接 | [协作](braid-collaboration/packet.md) |
| 原生子角色 | [子Agent](factory-subagents/packet.md) |
| mixed/reviewer本地对照 | [验收流程](acceptance-workflow/packet.md) |
| DX三项收尾 | [实际结果](developer-experience/remaining.md) |
| 暂缓的官网展示追溯 | [运行可观测性](official-runtime-observability/packet.md) |
| 详细盘点依据 | [证据清单](competition-budget/inventory-evidence.md) |

当前迭代入口：[完整需求的自主交付与可信验收](acceptance-integrity/packet.md)；[实施计划与验收](acceptance-integrity/plan.md) 已获用户“可以开工”授权，正在并行实施并准备两阶段验收。B 由用户接管监控。

当前事实纠正：continuation-02已失败，两题在模型调用前报Git dubious ownership。拟修的Docker --user并未实际进入02冻结launcher；不能把之前“参数已补齐”的报告作为证据。停止新部署，准备独立未执行候选供用户确认；保留01/02失败与原09工作区。
