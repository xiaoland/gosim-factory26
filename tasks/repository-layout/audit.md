# 仓库收敛审计

2026-10-07。按[审计计划](plan.md)先划分问题，再沿当前导航、代码消费、材料生产三个方向调查。结论是：先修正当前答案和 Console 构建边界，同时隔离明确的历史原件；再调整新产物落点与物理目录。目录收敛仍是交付目标，但仅搬路径不能解决已经观察到的错误知识。

本轮只完成审计与方案更新，没有实施新的源码迁移、删除产品代码、回收运行数据或部署。此前获准的废弃指南删除和 Makefile/scripts 入口修正已完成，见[任务包](packet.md)。工作树由多个任务并行修改，证据反映读取时的内容，实施时须核对受影响文件的最新版本。

## 四个高杠杆点

| 优先方向 | 已观察到的问题 | 建议动作与收益 |
| --- | --- | --- |
| 当前操作答案 | 从正常文档入口能走到仍称“新配方”的旧 Lab 命令；实际 `python3 -m lab doctor --help` 返回 invalid choice。历史页还把读者送回语义已改变的新 Lab README。 | 修正具体落地页和执行合同归属，撤回重复索引正文。直接消除错误操作分支，避免每个读者重新辨认版本。 |
| Console 构建边界 | 旧 `service.py prepare` 复制当前 `web/dist`，但当前 UI 源码请求的 run 路径 API 与旧 Python server 的 query-string API 不匹配。 | 先明确两个界面的构建输入和服务消费者，再收拢目录。阻止错误界面被装进旧服务，同时保留 Braid Console 的独立产品职责。 |
| 默认检索中的原件 | 默认可见 4,625 个文件，tasks 占 2,873 个；包含旧源码、技能、机器回读和会话索引。仅排除 runs/reports/history 等目录，Console 命中仅从 58 降到 57，五份含已删除指南路径的原件全部仍在。 | 精确隔离冻结快照和原始记录，保留当前 packet、结论与证据入口。减少当前源码和旧副本竞争，同时保留历史追溯。文件数不是无用程度。 |
| 材料生产与落点 | `experiments/` 同时有定义与编译输出；旧 `lab.exp` 的输出由调用者显式 `--directory` 决定。`harness/` 实际是共享输入，Console 目录名也不能代表当前构建内容。 | 先修改仍有效的生产示例与调用位置，再搬已确定用途的材料。同步落点可以防止整理后产物重新散落；准确命名和共同父目录降低职责发现成本。 |

## 具体清理范围

### 当前知识：修来源，减少重复维护

第一批建议范围是 `docs/deployment/index.md`、`docs/deployment/history/README.md`、`experiments/hackathon-local/README.md`、`experiments/i14-0/README.md`、`lab/exp/README.md`、`lab/exp/execution.md`。区分当前 run、仍可调用的旧执行器和只解释冻结证据的历史材料；不通过机械替换命令 namespace 宣称旧配方已适配新 Lab。

`variants/README.md` 重复列出六个 I13/I14 实现，应收成一份身份索引，具体模型与实现由组件本地说明负责。`docs/work-index.md` 应指出当前问题的主要任务入口，旧任务解释前序工作；不能将已完成 repository-curation 继续称为“本轮”，也不能用旧 Console 的物理控制任务代替当前界面入口。模型路由的当前说明与执行缺口由正在处理它的 agent-doc-system-audit 继续维护，本任务采用其最新结果。

### 代码：修装配关系，保留仍有用途的实现

Console 问题已有静态契约证据，尚未证明已部署实例发生故障。新源码构建的 UI 面向 `lab/serve.py`，旧服务 preparer 却不区分构建输入；现存 dist 也可能是旧构建，不能由文件名判定其身份。实施准备应固定两条入口及其制品消费者：如仍需重新准备旧服务，它必须取得匹配的 UI；如该入口已退役，应撤回其当前使用路径。具体选择需要当前服务用途证据，不能凭历史 README 推断。

可单独清理的源码是 `App.tsx` 未使用的 import/lazy 声明。未挂载不等于产品废弃，`BraidRun`、`Review`、`Discussion` 不列为可删范围。`sources/braid/viewer` 被 Lab 和离线分析实际导入，保留在 Braid 组件内；不因被嵌入 Lab 而搬入 Lab Console。

`lab.exp`、旧 Console 后端和 Linux 交付支持仍有真实 import、冻结或读取消费者，因此不整体删除。`scripts` 与 `submission` 可以收入共同 `tooling` 父目录，但继续区分宿主装配、容器内支持和包内 ABI。迁移当前源码时不重写旧包或冻结 manifest，也不预建路径注册层和永久别名。

### 原件与报告：分别处理搜索和 Git 边界

优先处置 `tasks/iteration10/instruction-audit/current/` 的旧源码/技能副本，以及 `tasks/iteration11/run-audit/` 中已识别的快照、会话原件和机器回读。`current-runtime/` 还含依赖快照，需区分已经被忽略的部分。保留 packet、结论、索引与来源关系；原件可留在原位置做精确搜索排除，或迁入 `runs/<调查>/evidence/` 并修正外部维护入口。不能整体隐藏 tasks，也不能按 JSON 扩展名批量排除当前配置。

第一批优先原位隔离已跟踪原件，不需要为搜索优化取消 Git 跟踪。后续若迁入 Git 忽略域，须明确交接载体和证据入口，不能让原先随 clone 可得的证据只剩本机路径；依赖快照不因此扩大 Git 跟踪范围。

`runs/reports/` 的 16 份报告和 README 可以整体归入 `runs/reports/`。其价值首先是清晰归属和一级目录收敛，并非最大的检索收益。继续由 Git 跟踪，给 `runs/reports/` 精确例外；其它 runs 材料保持忽略。默认当前搜索与 Git 跟踪是不同边界，可通过小范围 `.ignore` 规则处理；明确历史查询仍应可从报告索引抵达原文。快照、源码包和 node_modules 不进入报告例外。

五份含已删除指南路径的 messages/assignment/read-receipts/read-ranges JSON 保留原字节。它们是当时发生过的记录，处理的是默认搜索适用性，不是改写过去。对报告内的维护链接可以修迁移路径，对冻结 provenance 和执行身份不做全文替换。

### 产物与运行：改生产者，按具体消费者处置旧材料

`experiments/iteration14/`、`experiments/pi-minimal-vv/` 中可维护定义与一次执行的 intent/recipe/compilation 分开。后者建议收入其所属 `runs/<实验或调查>/`，保留来源和字节身份；目录名不制造单次 run 身份。旧 `lab.exp` 的 `--directory` 示例和实际调用者是纠正落点的直接位置，不需要新增通用路径配置。新 Lab 已有自己的 run 根目录，不把旧约定套给它。

`local-generations/` 没有 Git 跟踪文件，但两份 recipe 和公开需求快照有实际路径消费者及 provenance。可迁移到对应证据/输入域后收掉一级目录；先修外部可维护引用并保留来源映射，不改写原 provenance。未证明存在等价字节副本，不能当缓存删除。

`.runtime/exp-console/` 增加了 Git 未跟踪噪声，隐藏目录本来不进入默认 rg。三个 PID 对应的本地进程均已不存在，可将这三份过期控制记录列入清理范围；它不证明远端服务停止，也不支持删除日志。建议增加 `.runtime/` 忽略规则并保留明确的生产者/用途说明，不引入新的运行状态系统。

本轮读取到的 runs 一级 17 个目录都是材料分组，不能当作 17 次实际运行。当前默认 `runs/lab/runs/` 下一个 arc.run 的保存状态为 failed，也不是远端实时状态。旧容量、archive 回执和 `lab/gc.py` 不能充当当前统一回收依据；本轮没有足够证据列出可整体删除的运行簇。后续只对明确可重建的派生物和明确消费者开展回收准备，不需要先遍历全部 runs 才能做前述清理。

## 推荐分批与验收

| 批次 | 具体范围 | 完成依据 |
| --- | --- | --- |
| 1. 当前答案与有限搜索隔离 | 上述错误落地页、重复索引、当前工作入口；已确认快照/原件的精确排除；报告归属及 Git 例外。 | 正常导航取得正确执行合同；当前 packet 仍可发现；旧报告与至少一份原件仍可明确追溯。不能只看旧词消失。 |
| 2. 构建与生产落点 | Console 两条构建/服务消费链、死入口声明、仍有效的旧编译输出示例与调用位置。 | 用实际构建或装配回执确认 UI/API 配对与新产物落点，保持旧冻结制品身份；具体操作另列实施范围。 |
| 3. 物理收敛 | `harness → materials`、`scripts/submission → tooling`、两个 Console 并列归属、公开验收集聚合；已核实的机器材料迁移。 | 核对实际 import、ROOT 层级、Docker context、variant 路径、包内布局与维护链接；按组件分别取得真实反馈。 |

批次表示依赖顺序，不要求每个文件单独审批。Console 实际旧服务用途、Stage2/Stage3 对编译材料的后续消费、旧运行可重建派生物的引用关系，是尚会改变具体处置的事实；它们不阻塞第一批设计收敛。目录候选及包内边界见[布局方案](design.md)。下一阶段是据本审计确定具体实施范围，本轮审计授权不自动扩大为这些修改的开工授权。

## 证据与限制

- [导航审计](audit-navigation.md)：五条真实入口回读、错误命令反馈、有限过滤对比；[查询与内容身份](navigation-evidence.json)保留条件、路径和哈希。
- [代码审计](audit-code.md)：Console 装配与 API、新旧 Lab、公共工具链的实际消费关系。
- [材料审计](audit-materials.md)：任务快照、报告 Git 边界、编译输出生产者、本地控制记录与运行回收限制。

另从 `runs/reports/README.md` 明确进入 2026-10-03 核心文档报告，再抵达其 `runs/developer-experience/final-cold-acceptance-20261003/report.md`，成功读回历史范围和未完成的热恢复限制。这说明该样本的显式历史追溯可用，不表示其旧 compile 方法仍是当前操作方法。

本轮是有上下文的有界调查，没有进行独立冷启动或效率实验，不能报告 token/耗时改善百分比。没有运行 Factory/Braid 测试、模型、官网评测、构建、服务控制或 GC；目录迁移后的实际效果仍需实施验收。
