# 产物与运行材料审计

审计范围：Git 可见的报告/实验定义、当前工作区的 `experiments/`、`local-generations/`、`.runtime/`，以及既有存储生命周期证据。未遍历 `runs/` 全树、未读私有凭据、未移动或删除文件，也未启动运行、服务或 GC。结论针对“如何减少默认检索误命中和错误归属”，不是对每个历史文件给出回收判定。

## 结论

优先级最高的杠杆是把维护输入与历史原件的检索边界分开，并让新产物进入明确的证据域：`experiments/` 保留可复用、可维护的实验定义；编译出的 intent/recipe/compilation 和阶段生成材料进入所属 `runs/<实验或调查>/`；报告可迁入 Git 跟踪例外 `runs/reports/`。`local-generations/` 当前没有 Git 跟踪文件，完成具体消费者和交接处理后可迁出并收掉一级目录；`.runtime/` 是本机 Console 隧道状态，应加入本地运行时忽略边界。

## 关键发现

### 0. `tasks/` 是默认检索的主要噪声源，优先隔离原件和源码快照，而不是删除任务正文

观察：本次 `tasks/repository-layout/navigation-evidence.json` 记录的默认可见文件为 4,625 个，其中 `tasks` 占 2,873 个（约 62%）；当前只读复核得到 `rg --files tasks` 2,880 个、`git ls-files tasks` 2,788 个，差异来自本地未跟踪材料。按路径分布，`tasks/iteration11` 为 1,159 个，`tasks/iteration10` 为 862 个；按扩展名，`.json` 536、`.jsonl` 186、`.txt` 697，说明默认候选大量是机器回读和原生会话索引，而非维护正文。

高收益隔离范围一：`tasks/iteration10/instruction-audit/current/` 与 `current-runtime/` 是冻结源码/技能和 Node runtime 快照。`current/` 当前约 55 个文件，包含 `sources/braid`、`sources/svc`、`harness/skills`；`current-runtime/` 还含 `node_modules`。`tasks/iteration10/instruction-audit/packet.md` 把它们定义为本次调查输入，`tasks/repository-curation/code.md` 也明确称其为调查快照。它们会让一次针对当前源码的 `rg` 同时命中旧 Braid/SVC/skill 实现，形成“历史快照像现行代码”的误导。建议保留 packet、sources.json、结论和必要索引，将原件移到 `runs/<对应调查>/evidence/`，或留在原位并为检索设置精确排除；不应放入 `runs/reports/`，也不删除字节、不重写其中路径。

高收益隔离范围二：`tasks/iteration11/run-audit/` 内的 `snapshot-*`、`source.git`、`evidence/`、`work/native-homes/` 等原件和派生回读。现有 `.gitignore` 已覆盖若干未跟踪路径，但 tracked 的任务正文仍大量引用这些路径，且任务树中同时存在 `session-*.json`、`read-receipts.json`、`read-ranges.json` 等机器索引。这里应把原始快照/源码包/会话日志与可读 packet、cells、coverage/index 脱钩：默认检索只保留索引和结论，原件从专用 evidence 入口按需读取。不能依据文件未跟踪或旧日期直接删除；`snapshot.tar`、lineage records 和 native home 的保留关系仍按既有 packet 证据核实。

这两个范围比清理 17 份 reports 更能降低错误检索，因为它们同时覆盖“当前源码查询”和“运行事实查询”两条常见路径；处置目标是隔离默认候选，原始证据仍可从明确入口回找。

### 1. `reports/` 可合并到 `runs/reports/`，但必须建立“Git 跟踪的报告子域”

观察：当前 16 份 Markdown 报告及 `README.md` 都是 Git 跟踪文件（`git ls-files reports`）；根 `.gitignore` 却把整个 `runs/` 忽略（`.gitignore:1`）。现有报告内容是带日期、实验条件和历史结论的证据，不是 `docs/` 的长期操作合同；`reports/README.md` 也把它定义为历史报告入口。

判断：物理上迁入 `runs/reports/` 能表达“带时点的证据集合”。已跟踪文件可以用 `git mv` 继续跟踪；风险在于整个 `runs/` 的忽略规则会使普通迁移、未来新增报告和交接漏纳，因此仍需增加精确例外，例如 `runs/*`、`!runs/reports/`、`!runs/reports/**`，并给 `runs/reports/README.md` 一个稳定入口。该例外只覆盖报告，不解除其它运行现场的忽略边界。

建议：保留报告原文件名与日期身份，整体迁入 `runs/reports/`；更新 `docs/index`、任务入口和报告内部相对链接；报告仍可被明确搜索，但不进入 durable docs 默认入口。迁移前先检查报告内对 `reports/` 的相对链接，避免静默断链。

边界：报告来源未必是一条实际 run，因此目录名表达的是证据/运行域，不应要求每份报告绑定一个 `runs/<run-id>`。报告迁移不等于允许删除其引用的原始运行材料。

### 2. `experiments/` 已同时承载定义和编译产物，造成“可复用入口”与“历史快照”的检索竞争

观察：`experiments/README.md:3,7` 明确区分 experiment、run，并说明旧 intent/recipe/bundle 只解释对应冻结执行，不是新入口；但工作树中 `experiments/iteration14/` 有 47 个文件、`experiments/pi-minimal-vv/` 有 59 个文件，主要是 `intent.json`、`recipe.json`、`compilation.json` 等编译结果。可跟踪的实验目录目前只有 README/脚本等少量定义（`git ls-files experiments`），这些编译结果多为未跟踪材料。

观察：`tasks/pi-minimal/sequential-stage2-stage3-20261006/packet.md:65` 将 `experiments/pi-minimal-vv/sequential-stage2-stage3-20261006/` 作为本轮正式定义，并在同一段说明 K3 已 superseded；因此不能把该目录整体当作可删除缓存。这个 packet 是路径消费者证据，但不证明 Stage2/Stage3 当前仍在运行或仍会读取该目录；实时活动状态本轮未核实。`rg` 未发现源码或维护文档把这些具体目录作为新的自动入口，主要消费者是对应 task packet 和历史执行回读。

判断：这里适合做“定义/执行快照”分流，而不是把所有 `experiments/` 迁进 `runs/`。可维护的 README、matrix、archive registration 留在 `experiments/`；已经编译且只服务一次执行的 intent/recipe/compilation 随所属实验保存到 `runs/<experiment>/...`，在外部维护入口记录来源和 SHA。它们不必人为绑定一个新的单 run 身份；仍被后续 Stage3 或恢复流程读取的定义，在迁移前必须由 owner 标出具体消费者。

建议：先建立文件级分类清单，再迁移已终态、无后续输入消费者的编译结果；在 owner 提供终态/消费者回执前，Stage2/Stage3 目录暂保留。不要用“未跟踪”作为删除条件，也不要用目录存在作为运行授权或活动状态证明。

### 2a. 编译产物落点由调用者的 `--directory` 决定，当前没有集中默认生产目录

观察：`lab/exp/__main__.py:16-33` 要求 `compile`、`build`、`recover` 显式传入 `--directory`；`lab/exp/compiler.py:129-145,265-274` 直接把 `intent.json`、`recipe.json`、`compilation.json` 写入该目录；`lab/exp/controller.py:234-269` 在 build 时再向调用者给定目录写 `build-intent.json`/运行材料。`experiments/hackathon-local/README.md:5,11` 的示例也将 bundle/experiment 目录作为命令参数，没有隐含 `experiments/` 默认值。

判断：现有“实验目录里出现编译结果”的生产原因是任务/操作者手工把旧 `lab.exp` 命令族的 `--directory` 指向 `experiments/...`，不是当前所有 Lab 入口都自动把产物写回该一级目录。改变后续落点的最小杠杆是更新这组旧命令的实验登记模板和命令示例，约定定义输入留在 `experiments/`、该命令族的输出使用 `runs/<experiment>/definition|program|...`；不要新增一层路径配置或运行时猜测，也不要把跨 run 编译产物人为绑定到单个 run。迁移旧文件时保留 compiler 生成的绝对路径、SHA 与原执行身份，映射写进外部维护入口，不改写原 provenance。

### 3. `local-generations/` 是历史兼容材料区，当前最适合“移出默认入口后再判定回收”

观察：目录没有 Git 跟踪文件，当前有两份 `experiment27-*.recipe.json` 和一份 `public-requirements/github-a2-8a282da5502e/`，其中需求 YAML/Markdown 约 320KB，`provenance.json` 绑定了来源 run、submission、attempt 及需求 SHA。任务 `experiment-startup-dx/example-intent.json:45`、`actual-material-readback.json:7` 仍直接引用该绝对/仓库相对路径；因此它不是孤立副本。

判断：公开需求快照属于可复现输入，recipe 属于历史执行材料。它们不应继续作为一级目录的“当前生成入口”，但在对应 run 或任务 packet 完成来源重绑定前，不能直接删除。可将需求快照纳入 `runs/<来源 run>/inputs/` 或明确的共享输入区，保持原 provenance 和字节身份；迁移映射写在外部维护入口，只更新可维护引用，不重写历史 readback。完成交接与引用收敛后可移除 `local-generations/` 一级目录。

边界：需求快照是否可由官方材料重新取得尚未证明；在没有等价字节和 provenance 替代物之前，属于“可移/可隔离”而非“可回收”。

### 4. `.runtime/` 是 Console 隧道的本机状态，应该被忽略和清理，但不能按实验材料处理

观察：`.runtime/exp-console/` 当前只含 PID、隧道日志和 `tunnels.ps`。全仓维护源码、任务入口和运行文档没有引用该仓库相对路径；Console 的正式说明要求服务根位于 WorkSSD 的独立服务目录（`braid-console/README.md:35,37`），历史部署也使用 `/.../exp-console/<deployment>`，不是仓库 `.runtime/`。源码检索未发现 Console 或 Lab 写入 `.runtime/` 的默认路径；因此当前目录更像启动者/操作者用显式目录或 shell 重定向创建的本地运行状态，而非源码默认产物。`.gitignore` 当前没有 `.runtime/` 规则，目录因此出现在未跟踪工作区；由于它是隐藏目录，主 `rg --files` 默认并不纳入这批文件。

判断：这些文件是可重建的本机连接控制状态，不是运行证据或维护源码。它们主要污染 Git 未跟踪视图，并有陈旧 PID 误导接续的风险；不能把它们描述成已观测的默认 `rg` 语料。主 Agent 已对 `mac-sfp7=75328`、`wsl-bridge=83405`、`wsl-sfp7=75341` 执行 `ps -p PID -o pid=,comm=,etime=`，三个本地 PID 均无进程，这只证明本地 PID 记录已过期，不证明远端隧道/服务已停止，也不授权删除日志。应加入 `.runtime/` 忽略规则；后续脚本若需要状态目录，应显式接受 WorkSSD 下的 runtime directory，并在 README 中标明生产者。

边界：本次审计不控制隧道、不读私有 token、不删除 `.runtime/`；外部 Console 服务根和远端服务状态需要其 owner 的实时回执。

### 5. 不宜把大 `runs/` 簇直接做 GC；现有生命周期代码要求以记录和引用为准

观察：既有数据清单记录 `runs/iteration14` 约 85G、`runs/experiment-operations` 约 7.3G，但明确未取得全树规模和远端消费者；14 份可见 `archive.json` 均为 `decision` 且 `reclaim_state.status=blocked`。历史 `lab/gc.py` 代码能说明曾有一套保护字段和只读规划逻辑，但它不是当前 run 的通用 GC 入口；本审计不据此执行或推导回收授权。

判断：可以优化 `runs/` 的索引和默认检索，例如报告子域、按 run 的输入/结果边界、明确的 archive 入口；当前证据不足以支持物理删除或把历史现场压进一个扁平 archive。目录大小、`completed`、旧日期和“暂停”均不是回收授权；实际回收必须以当前运行合同、owner 回执和明确授权为准。

建议：先按 archive 回执生成有界 inventory，再将明确可重建的 viewer/decoded/cache 投影列为候选；原始 workspace、Braid/native/OTLP 和 runtime 依赖继续依其 record 保护。这个顺序能减少导航噪声而不破坏恢复链。

## 建议实施顺序

1. 先隔离 `tasks/iteration10`、`tasks/iteration11` 中的源码快照、会话/运行原件与可读 packet；已跟踪原件优先原位精确排除。随后可迁移并继续跟踪 `runs/reports/`，它是边界清楚的物理收敛，不代替任务材料隔离。
2. 对 `experiments/iteration14` 和 `experiments/pi-minimal-vv` 建立文件级 owner/消费者表，终态编译结果迁入对应 `runs/<experiment>/`，活动定义保留在 `experiments/`。
3. 为 `local-generations/` 的需求快照和 recipe 建立外部迁移映射；区分 `tasks/experiment-startup-dx` 的可维护输入与历史 readback 后再迁移，原 provenance 和 readback 不改写。
4. 把 `.runtime/` 纳入忽略规则，三份已确认过期的本地 PID 可列为清理对象；日志的保留价值另行判断，远端状态不由本地 PID 推断。
5. 最后才按当前运行合同、archive/recovery/consumer 记录审计 `runs/` 内可重建派生物；不以“运行目录很大”作为删除条件。当前 `runs/` 一级 17 个目录均未见顶层 `manifest/run/experiment/archive/status/runtime.json`，应先视为材料分组，不能当作 17 次 run；默认 `runs/lab/runs` 仅见一个 `arc.run`，其 `records/status.json` 为保存状态 `failed`，不等同实时平台确认。

## 尚未解决且会改变决定的事实

- `runs/` 中哪些目录仍被远端 Console、WSL/Docker、恢复控制器或官网重放引用，尚未完成全量路径级核对。
- `experiments/pi-minimal-vv` 当前 Stage2/Stage3 是否仍会继续读取同一编译材料，需要 owner 给出终态回执后才能迁移。
- `local-generations/public-requirements` 是否存在官方等价快照及其字节身份，尚未核实；没有替代 provenance 前不能回收。
- `.runtime/exp-console` 的三个本地 PID 已核实不存在；远端服务状态和日志保留用途仍未知，不影响对过期本地 PID 的判断。
