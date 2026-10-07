# 当前知识与导航审计

2026-10-07。先按 plan.md 定义的真实问题回读维护入口，再做默认 rg 查询与有限历史过滤比较。观察时 HEAD 为 f01e5fa10a6a801b486089a0542303ed39e8ada6，工作树存在其它任务并行修改；文件内容哈希、命中路径与查询条件保存在 navigation-evidence.json。以下是带上下文的有界审计，不是独立模型冷启动，也不推算 token 或耗时收益。

## 结论

当前入口自身的错误仍存在，单独屏蔽历史或移动报告无法修复。最有价值的动作是让每种实际执行合同有明确入口，撤回指向已改变语义的旧推荐；同时减少导航页重复维护实现状态。历史检索隔离应针对已识别的证据和已结束工作，不可整体隐藏 tasks。

## 实际导航路径

| 自然问题 | 从维护入口回读的路径 | 观察与判断 |
| --- | --- | --- |
| 怎样按公开要求评测已经冻结的应用？ | README → docs/deployment/index → experiments/README → hackathon-local/README | 实验索引第 16 行把该配方作为公开需求回放入口；落地页第 5、10–14、17 行仍称“新配方”“当前状态”，推荐新 lab 的 doctor/build 和旧 start 参数。实际 `python3 -m lab doctor --help` 返回 2，明确 invalid choice。入口可达，但操作答案错误。 |
| 怎样读取旧执行合同并判断恢复方式？ | docs/deployment/recovery → history/README → lab/exp/README → execution.md | 恢复页正确区分新 run 与旧 executor；历史索引第 14 行却把 lab.exp 称为“新 Lab”，lab.exp README 第 3 行把公共命令送回新 Lab，execution 第 58、60 行仍推荐 `lab checkpoint/recover`。进入历史后又被送回另一执行合同。 |
| 如何给 I14 准备输入？ | experiments/README → i14-0/README | 上游第 15 行正确标明旧合同；落地页第 7 行却称操作“统一沿 Lab 的 compile/doctor/build/start”，链接指向新的 Lab README。上游标签不能替代落地页自述和正确调用入口。 |
| 自费模型应采用哪个配方？ | docs/index → harness/model-recipes/README → self-funded.json/catalog | 配方归属和执行缺口已由 agent-doc-system-audit 当轮修正，入口明确新 Lab 的路由消费尚未闭环。当前可以识别所选配置与未验执行的区别；不把原任务尚在修复的路由缺口重复认作本轮新发现。 |
| Braid Console 与 Lab Console 分别改哪里？ | docs/index → docs/deployment/console → braid-console/README → App/RunOverview/BraidRun；再看 sources/braid/viewer | 文件名、README 标题、当前挂载和保留界面不是同一个边界。现入口默认指向通用 Lab 服务，原 Braid 界面缺少对等的当前构建导航。组件与打包问题由 audit-code.md 定向取证，不能把一个 HTTP 宿主推导为源码归属。 |

这些路径是实际链接的有界回读，操作者有本任务上下文，不是让未知 Agent 自由探索的实验。它们能证明具体错误分支及可定位的正确边界，不能证明整体阅读成本已经改善。

## 共同原因与优先处置

### 1. 旧链接落到了语义已经改变的入口

lab/README 在新架构中承载 run 控制，但 lab.exp 本地 README、旧配方与历史索引仍把它当作旧 compile/doctor/build 的公共入口。文件路径和链接都有效，所以链接检查不会发现问题。重复增加“历史不代表当前”的通用警告不能替代修正这些具体指向。

建议逐个撤回旧命令的当前推荐：新 run 从 lab/__main__.py 对应说明进入；仍维护的 lab.exp 操作使用其实际 CLI 与来源冻结执行器；只能解释旧证据的页面改成历史说明，不能留着“新配方”“当前状态”使读者自行猜版本。公开验收集是否接通新 run 需单独确认，不把命令机械替换成另一 namespace 就宣称可执行。

具体范围：experiments/hackathon-local/README.md、experiments/i14-0/README.md、lab/exp/README.md、lab/exp/execution.md、docs/deployment/history/README.md。docs/deployment/index.md 第 9 行仍沿 recipe/backend 描述通用执行，也应按当前/旧执行的适用性收窄。

### 2. 导航同时复制状态，又声明不维护状态

variants/README 第 8–16 行列出 I13/I14 基线，随后第 30–35 行再列六项相同实现及相同职责；第 41 行却说明索引不维护另一份模型配置。重复正文使同一事实至少有两处更新点，也使“其它对照”里的基线身份模糊。

docs/work-index 第 15 行把“协作现场的查看、会话与物理控制”送往旧 Console packet，当前 Console 操作说明则强调新页面不写现场工作项。其第 29 行仍把 repository-curation 这个已完成任务描述为“本轮范围”，尚未发现本次正在进行的 repository-layout。这里不能靠再增加一排平行入口解决；应由当前任务入口指出本轮职责，其它旧入口只解释已知保留用途。

建议删除重复索引行，导航只保留组件身份和其权威入口；临时运行/验收状态由所属活动 packet 承担。工作主题按当前问题指到一个主要 owner，并沿链接取得前序证据。不新建全仓状态注册表，也不把索引变成第二份配置。

### 3. 默认搜索的历史噪声不只来自 reports 或 history 目录

排除本任务后，默认 rg 可见 4,625 个文件，其中 tasks 2,873 个，约 62%；这不是“62% 无用”的结论。Console 查询命中 58 个文件，其中 44 个位于 tasks；删除指南的精确路径命中五份历史 JSON，全部位于普通 cells 子目录。它们分别是会话摘录、assignment、read-receipts 和 read-ranges，不应为消灭搜索字符串改写原件。

有界比较保持正文不变，仅通过本次命令的 glob 排除 reports 和明确的 history/source/evidence/frozen/snapshot 等目录，没有更改仓库搜索规则：

| 查询 | 同轮过滤前 → 过滤后文件数 | 能说明什么 |
| --- | --- | --- |
| 旧 Lab 命令的精确命令行 | 3 → 3 | 剩余误导入口在维护页中，过滤历史不能修复它们；其中一项是审计报告引用原错，不能全算作错误推荐。 |
| 模型 route/自费配置 | 36 → 36 | 此过滤对该使用路径几乎无效；命中数不能决定哪些配置正确。 |
| Console 名称与路径 | 58 → 57 | 只移出一份报告，大部分候选仍存在。 |
| 已删除指南路径 | 5 → 5 | 证据散落普通 cells，目录词不能完整表达生命周期。 |

因此 runs/reports 是合理归属调整，但不是主要检索优化的全部。下一步应按证据来源识别冻结 JSON、源码副本与已结束调查子树，给它们明确的证据归属和搜索边界；活动 packet、当前配置和承载未完成授权的工作单元继续可发现。对旧记录的主动追溯应从明确索引进入。具体物理处置须采用 audit-materials 的消费者证据，不能按上述查询的文件数批量删除。

## 已解决、未证明与后续反馈

显式历史追溯也取得一个成功样本：runs/reports/README → 2026-10-03-core-documentation.md → runs/developer-experience/final-cold-acceptance-20261003/report.md。实际读取到原始报告的范围和热恢复未通过限制；历史 compile/readiness 结论按当时合同理解，不作为当前 Lab 用法。过滤比较只是命令参数，没有移动文件或更改搜索规则；此样本不能代替未来迁移后的追溯验收。

此前 Makefile/scripts 的旧命令推荐及废弃指南维护引用已在本任务前轮清理，本轮不重复记成尚未完成问题。agent-doc-system-audit 同期修正了模型配方缺口和若干旧 packet 摘要；其最新证据比早期审计正文更适合作为状态入口。

收尾内容身份复核发现模型配方 README 又有并行更新，已重新读取：新增默认 target 选择自费配方和按 variant 筛选有序链的说明，仍明确网关运行接线在实现且没有真实自费验收。此变化不影响本轮建议，其初始哈希和最新回读分别保存在证据中；不把变化中的文档固定为永久状态。

尚未证明的包括：全部历史材料的可回收性、活动运行物理状态、每个旧配方可执行版本、Braid 独立界面的产品去留，以及整体 Agent token/耗时收益。本轮支持先修当前语义入口、收敛重复维护点，再按真实材料用途隔离检索；后续用同类真实问题再次回读，并至少成功追溯一个历史来源，才能评价改动收益。
