# 本轮数据保留清单

更新时间：2026-10-02。规模数字分两个时点：本文件的初盘记录早于开工基线；代码清单以开工基线为准（85 个已跟踪变化、2,458 个未跟踪文件），不能把初盘数字当成当前全部状态。范围是本地工作区的只读盘点；没有读取凭据正文、原生 rollout 或全量 telemetry，也没有移动、删除或运行 GC。

## 已确认规模

| 物理簇 | 规模依据 | 用途与关系 | 当前决定 | 解除保护所需事实 |
| --- | --- | --- | --- | --- |
| `third_party/` | `du -sh third_party`：约 17G | 外部源码、评测器和历史依赖；`tasks/local-official-bench/packet.md` 明确引用 `third_party/arc-bench`，`tasks/developer-experience/boundaries.md` 说明本地调用读取该 checkout；被 `.gitignore` 忽略 | 保留；不按目录名或忽略状态清理 | 逐项确认没有活动运行、冻结包或复现流程引用，并确认可从受控来源重建 |
| `.adapter/` | `du -sh .adapter`：约 470M | 本地适配器虚拟环境和工具；本轮在源码、文档和任务入口中未查到对该物理路径的直接引用，只确认它是被忽略的本地运行环境 | 保留；属于本机运行依赖候选，不是历史证据 | 从活动 controller/job/inspect/cleanup 的实际解释器回执确认是否仍使用，再决定是否可重建 |
| `.bootstrap/` | `du -sh .bootstrap`：约 5.5M | 启动、编译和探针日志及少量 ZIP/JSON 结果；被 `.gitignore` 忽略 | 先按日志/结果用途保留；不按扩展名批量删 | 对每个文件确认是否已纳入任务证据或可由已保存记录重建 |
| `tasks/` 大原件 | 初盘：tracked 1,727 files/14.4MiB、untracked 2,458 files/402.7MiB；开工基线以 2,458 个未跟踪文件为准，其中 tasks 约 2,400 files/402.5MiB。`lstat`（2026-10-02）显示 `tasks/iteration11/run-audit/sheet/increment/snapshot.tar` 为 47,554,560 bytes，`tasks/iteration11/sheet-effectiveness-analysis/full-lineage/inventory/records.jsonl` 为 34,391,986 bytes。`full-lineage/root/coverage.md`、`inventory/inventory.md` 和 `inventory/build_inventory.py` 直接引用/生成 `records.jsonl`；`snapshot.tar` 本轮未查到明确的正文引用。 | 任务证据、快照和 lineage 原件；未跟踪不代表可删 | 保留原件；可整理入口和重复派生视图，但不物理清退 | 对 snapshot 确认 packet/恢复是否仍需原件；对 records 保留其 inventory 索引消费关系，并确认是否存在完整替代物 |
| `runs/` | 总量仍未取得；但不跟随符号链接的定向 `du -shP` 已核对：`runs/iteration14` 约 85G，`runs/experiment-operations` 约 7.3G。深度限制的 `find -x runs -maxdepth 1/2/3 -type f` 分别看到 4/553/3,890 个文件，不能外推全树总量 | 原始运行现场、应用/评分、Braid/native/OTLP 与派生 viewer；I14 与 operations 已是实际大簇。活动记录中的 controller runtime 指向 `runs/iteration14/dx-launch-20261002/controller-runtime-py312/asset.json`，说明至少部分解释器资产仍被运行记录引用 | 保留；先按记录和保护关系分域，不做全树物理整理 | 完整消费记录域、运行终态、archive receipt、recovery/Console/容器依赖和真实文件身份 |

## 归档与回收边界

在 `rg --files runs` 默认可见文件范围执行 `rg --files runs | rg '(^|/)archive\.json$'` 得到 14 份 `archive.json`；这不保证隐藏项、被忽略项或符号链接目标完整。代表路径为：

- `runs/experiment-signal-diagnostics-validation-20261001/remote-evidence/official-signal-evidence-validation-20261001-attempt5/archive.json`
- `runs/iteration13/i13-2-20261001/hosted-github-self-funded-r4/hosted-own/attempts/attempt-9d0be1c6696117fccb49deac/inputs/prepared/content/run/archive.json`

14 份均为 `archive_level=decision` 且 `reclaim_state.status=blocked`；多数仍有 `recovery_capability.status=declared`，保存状态均为 `diagnostic_coverage.preservation=partial`。当前没有可证明的 `work` 回收候选。

规则依据见 [实验存储生命周期方案](../experiment-storage-lifecycle/design.md) 和 [证据说明](../../docs/deployment/evidence.md)；其中 `lab gc-plan` 明确属于历史冻结 CLI。仓库保留的 [`lab/gc.py`](../../lab/gc.py) 是对应的历史 plan 实现，不能表述为当前 CLI 可直接运行的入口。其边界是失败关闭的只读扫描，核对 archive ID、对象身份、引用和保护路径，`reclaim_authorized` 永远为 false；active、paused、cleanup、recovery、未确认外部资源和 Console 依赖必须保护。本轮不重引入旧 writer。

## 当前未知

- 远端官网、WSL、Docker/容器和 Console registry 的完整消费者关系未在本地清单中证明；不能据“全实验暂停”记录解除保护，仍需原 owner 的暂停回执和资源核对。
- `runs/` 总量、实际占块和 inode 尚未取得；本轮不再次长时间遍历，也不据此估算可回收空间。
- 记录格式之外的历史目录、无 archive receipt 的 run、以及完整 telemetry 的保留需求均保持未知，只能进入 inventory，不能进入删除候选。

## 定向消费核对

- `third_party/arc-bench` 的实际消费者已在 `tasks/local-official-bench/packet.md` 和 `tasks/developer-experience/boundaries.md` 留有路径级依据；不能把 17G 目录视为孤立缓存。
- `.adapter/` 的物理路径在仓库源码、文档和任务入口中未检索到直接消费者；这只说明缺少静态引用，不足以解除本机运行依赖，需以活动记录中的解释器回执核对。
- `records.jsonl` 被 `full-lineage/root/coverage.md`、`full-lineage/de/coverage.md`、`inventory/inventory.md` 和 `inventory/build_inventory.py` 作为逐行位置索引和报告输入；这些报告还明确保留原始 source path/line/msg_id，因此不能单独删掉索引或原始 lineage。
- `records.jsonl` 是由 `inventory/build_inventory.py` 从已有 lineage/source 记录生成的派生索引，不是维护源码或必须随仓库分发的输入；现已加入精确 `.gitignore` 规则，原文件仍保留在本地 evidence path，`inventory.md`/`coverage.md`/生成脚本继续跟踪。
- `snapshot.tar` 的 `tar -tf` 显示包含 `braid.sqlite3`、`work/native-homes/`、session JSONL 和 subagent artifacts；本轮未查到其正文 packet 直接引用，暂按恢复/审计原件保留，不能据此判定重复。
- `snapshot.tar` 是本地审计/恢复原件，不是维护源码或独立 variant 输入；现已加入精确 `.gitignore` 规则，并由 [I11 Sheet run-audit packet](../iteration11/run-audit/sheet/packet.md#快照导航) 导航。两个规则都只匹配单个大文件，不遮蔽 packet、脚本或 variant。
- I14 的 recipe/intent 记录反复引用同一 `controller-runtime-py312/asset.json`，并记录 Python 3.12.10 与解释器树身份；这是当前资产/运行的引用事实，不能按 `runs/iteration14` 内的重复 package-stage 目录直接清理。

## 文件级处置闭环

- `.bootstrap/` 已按文件名分成三类：`acceptance-*`、`feedback-*`、`*-tests.log` 是历史验收/反馈/检查日志；`braid-build.{json,log}`、`dev-svc.json`、`runtime-config-check.json` 是构建或环境回执；`probe-pi-analysis/` 下的六个 overview 与六个 ZIP 是对应探针产物；`keep-discovery.*`、`evaluator-validation.json`、`pi-failure-analysis.log` 是发现/诊断记录。当前没有证据表明这些文件可由一个单独权威副本完全替代，已采取的整理动作是保留原目录并在本清单标明用途，不复制、不改名、不删除。
- `.adapter/pyvenv.cfg` 实际显示 CPython 3.13、uv 0.12.3，解释器 home 为 `/Users/lanzhijiang/.local/share/uv/python/cpython-3.13-macos-aarch64-none/bin`；本轮源码、文档和任务入口未查到对 `.adapter` 物理路径的直接引用，因此只能确认“本机环境存在”，不能确认“无人使用”。已采取的整理动作是保留环境及其 `.lock`/`CACHEDIR.TAG`，不把它列入回收候选；删除前至少需要活动解释器回执显示已不再使用。
- `snapshot.tar` 的可用导航已补入 [I11 Sheet run-audit packet](../iteration11/run-audit/sheet/packet.md#快照导航)，记录相对链接、字节数、SHA-256 和 `tar -tf` 内容说明；这完成了索引组织，但不改变其恢复能力判断。
- 因此，本轮已完成的是“可引用入口、用途、身份和 Git 边界整理”；两个本地大文件不随源码分发但继续原位保留，没有证据充分的物理回收候选，物理清理仍未完成，不能用本清单替代归档回执或 GC plan。

## 一次只读路径核对

以下代表路径均已确认存在：两份 `archive.json`、`tasks/experiment-storage-lifecycle/packet.md`、`docs/deployment/evidence.md`、`lab/gc.py`。这只证明入口和原件存在，不证明归档完整或允许回收。

## 本次提交的原件边界

用户明确要求main整理干净后，另将两份压缩会话快照、当前runtime源码压缩包及node_modules、Sheet record-sources索引、两份大上下文派生视图、原始SQLite和下载的官网bundle加入精确Git忽略。原文件保留原位；对应任务、分析脚本、公开来源verification与维护源码仍提交。规则只匹配 `.gitignore` 列出的具体原件，不删除或遮蔽全部任务目录。
