# 已完成工作项的联系回环与交付终止

2026-09-28 用户要求立即取消 GitHub `435b79927a47` 和 Sheet `bd7ac1b232ba`，并在修复后重新运行。官网已确认两条 run 为 `CANCELLED`；取消前原始工作区现分别保存于 `runs/e20260928-completed-replay/github/source-workspace.zip`（SHA256 `d4ca397ed629598ebe2801f75cfaf6f51d74454ae4bd831c21ccd82153af5200`）和 `runs/e20260928-completed-replay/sheet/source-workspace.zip`（SHA256 `9b981b0ee88b5b10563f4bab17d6e8ecb34a77fa803597a0cc9dfe8d21468b5c`）。

两份快照中根 Issue 和所有子 Issue 均 CLOSED，所有 PR 均 MERGED/CLOSED，`unresolved_merges=0`，交付 `main` 已形成。官网仍显示 `RUNNING`、`start_agent=running`、`run_tests=pending`。GitHub 最近 100 个物理会话有 90 个由 `terminal_contact` 触发，Sheet 最近 100 个全部如此。Sheet 的 Issue #4/#5 持续互发“main 未变、无待办”的回执，并产生新的直接联系事件；双方甚至在评论中要求停止这种重复复核，回环仍继续。当时据此判断评论投递与“必须全局静止才结束”使交付不能收敛；这只解释了终止条件，未完整解释持续唤醒。后续[独立审查](../../braid-architecture-audit/packet.md)发现 GitHub 236 次、Sheet 441 次 terminal_contact 批次完全没有关联事件，旧事件重放还存在空批次调度缺陷。全对象终态提前结束让已完成应用进入评分，但不是通知/重放根因已修复的证明。

修复边界：Braid Local 已有根 Issue 和 `delivery_ref`，当根及所有工作项均终态且无未解决 merge 时，直接结束本次 Local 运行；剩余的关闭后通知不再阻止交付。启动时先检查该条件，避免已完成快照在恢复原生 Pi 会话之前被旧通知再次唤醒。Braid 继续支持关闭后的评论与回复；Factory 决定本次交付和评分。不能用“没有新评论”代替完成判据，也不能将某个题目的固定路由或检查写入 Braid。

验收先用两份已完成快照实际恢复：保留原 Issue/PR、Git refs 与 Braid run 身份，Braid 新进程应在不调用模型的情况下 quiescent，导出同一个 `main`，官网新自费 run 进入评分；旧 run 的身份与结果保持取消。新包不宣称是从需求重新生成的 Harness 独立分数。Factory 基础设施不新增测试，使用实际运行证据验收。

修复版 Linux Braid SHA256 `f18c40fc02bfb491e8aec9b7b278ff10d40e93feda06fc27944564d1b7a97027`。可复用的已完成快照打包入口为 `scripts/package_completed_recovery.py`，包内入口为 `submission/recover_completed.py`；来源 ZIP、原包、修复二进制及源码快照的哈希写入 `recovery-source.json`。GitHub 新包 SHA256 `402c7d480b9c091682967aa84bc9122634b41804f2c34eeb6fb07b567280af37`，官网 submission `77d90e32f213`、run `595ab74c90a9`；Sheet 新包 SHA256 `93559bba727d0e39ff6ec19781e2681df9462f6147fe0a99aa0903e9057afc4c`，submission `9621a7dc59b4`、run `1efffb84ae1b`。两条均为 `self_funded`，journal 分别在 `runs/e20260928-completed-replay/{github,sheet}/official`。GitHub 已观测到 `start_agent=completed`、`run_tests=running`；Sheet 刚启动，终态与分数待收集。

两条新工作区已保存为各自 `official/workspace-after-generation.zip`。新 Braid `result.json` 都为 `quiescent`、根 Issue `CLOSED`；GitHub 交付 `main` 为 `5f64f3ccd1ddc5cf0060dbbe21c87f7c102641c1`，Sheet 为 `402336217ef1329f71b8f15560cfbf19d514e82f`。恢复前后原生 Pi JSONL 数量分别保持 GitHub 465、Sheet 682，没有新增会话；官网前端构建及后端 3000 启动成功，两条均进入 `run_tests=running`。旧快照内 `result.json` 仍记载此前被 SIGKILL 的旧状态，不是这次恢复的运行结果；以新包内同路径的 `quiescent` 结果和新工作区 provenance 为准。

两题官网评分终态均为 `FAILED`（含义是评分存在失败场景，生成/部署步骤均 completed）：GitHub `595ab74c90a9` 为 **4/100**、功能项 **1/47**；Sheet `1efffb84ae1b` 为 **58/100**、功能项 **8/24**。平台聚合状态分别保存于各自 `official/tasks/hackathon--{github,sheet}/status.json`，日志、traceability 与 commit-history 读取结果也由 `competition collect` 存在同一 journal；平台逐例 `tests` 列表为空，不能将失败项逐条归因。两条新 run `billing_mode=self_funded`，`token_count=0`、`token_cost_usd=0.0` 是本次**没有重新调用模型**的记录，不包括来源 run 的生成成本。评分反映来源应用的质量，不能单独衡量修复版 Harness 重新面对需求的通过率。本轮到此停止，不启动下一轮生成或评分。
