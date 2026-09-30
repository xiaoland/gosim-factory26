# I12 恢复来源与实际摘剪

本方案已退役：用户随后决定I12从零实现。以下记录仅保留摘剪取舍与来源证据，不再是当前启动方案。两条短暂接续已停止，Console只读保留现场；从零准备见 [部署](deployment.md) 与 [packet](packet.md)。

已准备两份独立副本，未启动模型、未提交、未改 I10/I11 原件或最终交付。主线选择混合起点：Sheet 优先回到重复处理尚未进一步扩散的 I11 启动现场；GitHub 保留后来已完成的 M6b 软件进度，再清理讨论入口。它们都是人工整理的接续现场，不是从零生成，也不是“问题从未发生”的检查点。

## I11 实际终态

2026-09-30 只读核对外层结果、Braid result/status 与对象终态。两题均已完成应用导出；这不等于官网评分通过，Sheet 明确 evaluation skipped，score=null。

| 题目 | 最终运行 | main 交付提交 | 应用 SHA256 |
| --- | --- | --- | --- |
| GitHub | `pi-braid-i11--hackathon--github-0d0cb6e9982fc1` | `442dc1cf776f144688d8ad667a76dd026f553e27` | `ffb6501cfcc652220d57b67f91a15186cc04294557d7ddf9a492f783b4f4b16f` |
| Sheet | `pi-braid-i11--hackathon--sheet-396538bc0dda96` | `10cba2ad888fd60f283382158c1bfb00b0fad240` | `7dad14f0db9625c991f270061c8525cd3c206cc66614e6611f70a9c1d5e1af46` |

两者外层 generation completed/exit=0；Braid result=quiescent、根 #1 CLOSED，全部 PR MERGED，GitHub 含最终整合 PR #23、Sheet 含 PR #13。保留的 queued 输入分别4/12条，result 明确 scope_closed，不解释成仍在生成。旧 `.factory26/run.json` 的 generating 是陈旧状态，不能覆盖上述实际交付证据。完整受限摘要见 `runs/iteration12/recovery/i11-final-deliveries.json`。GitHub 最新 run 的实际 workspace 仍在 `5c52a331ef0d5c` 旧目录；本次按此实际指针读 result，而非假设新 run 拥有新 workspace。

## 起点选择与放弃的进度

GitHub 来源为 `runs/iteration11/20260930-completed-turn-resume/github/source/template.tar`，来自 `pi-braid-i11--hackathon--github-f402061b5bc88f` 在 2026-09-30 00:59 停止现场。归档7619962880字节，已有归档回执 SHA256=`7754fff84824fc9b27bb3f2180de8a36ce98135f0f3db6351dd264e0f085cd92`。归档工具曾报告 run 目录有变化，随后追加 telemetry sidecars；回执确认 Braid DB/WAL/SHM 与停止后身份一致，不能因此声称全目录原子快照，但 Git/DB/native 来自同一停止现场。内部 run 为 `20260929-042409-1202e245`；develop=`e5110cb`，main仍初始`2914d2d`，M6b候选`42b2f64`；根#1、Issue#10、PR#22保持OPEN。

确有更早完整 GitHub 副本 `runs/recovery-curation/editable/github/template`，但仅到评论#273、develop=`5b6c7d4`，M4b/M6a未合并，M6b尚未开发。选它会丢弃整个M6b及前置集成，因此未选。00:59现场已经发生纯文档候选重复验收和 resolve 范围误用；本次只移除循环入口，不伪造未发生。没有把后来最终 main 的代码拼入此旧数据库。后续 PR22 合并、最终整合 PR23 及最终交付进度不随本起点带入，仍完整保留在I11原运行中。

Sheet 来源为 `runs/recovery-curation/editable/sheet/template`：I10完整暂停归档展开后，仅做过有日志的I11三项正文整理，详见 `tasks/iteration11/recovery-curation/sheet/packet.md`。内部run为`20260929-042409-811f18d4`，develop=`d07dd62`，main=`2914d2d`，最后评论#566；根#1、Issue#4、PR#13保持OPEN。它保留.git、origin.git、全部worktrees、physical、native及未提交文件；此次用 APFS clone 整目录复制，不单独换数据库。早期已存在#563自编辑后无动作核对，所以只能说早于#569及后续扩散，不能称完全无症状。

Sheet 放弃的后续有效进度包括 PR14 撤销快捷键检查稳定性修正（`18cfeab`，应用树未改、`e2e/range-undo.spec.ts`增加16行等待history记录的逻辑）、整合余下验收和main交付。修正证据在后期I11 PR11 #570、PR14正文及 `braid-state/evidence/issue-6-d/undo-shortcut-stability/`；最终终态来源路径在上述JSON。它们作为后续成果保留，未反向补入早期代码或宣称早期已验收。当前已有并发flake观察#553仍可见，接续者可依据真实失败处理，未注入官网隐藏反馈。

## 已实施的副本摘剪

实际可接续根目录：

- `runs/iteration12/recovery/github/template`
- `runs/iteration12/recovery/sheet/template`

脚本 `runs/iteration12/recovery/curate.py` 已实际运行一次，拒绝同一journal重复应用。GitHub修改根#1、Issue#10、PR#22正文，消除已被#330–#332交回替代的旧待办以及“base/head变化即重取”的纪律；局部hide#318/#319/#321/#324，保留决定#313/#322、真实首轮失败和后续交付记录。没有resolve整条thread。

Sheet修改根#1、Issue#4、PR#13的证据适用边界；将已完成PR9/PR10正文收敛为模块交付/契约和整合交接入口，停止镜像全局候选。局部hide#538/#541/#556/#563/#565的重复状态与哈希核对，保留#547交接、#558验收、#566计数更正和失败记录。早期无#569/#571/#574，故未把后来消息拼入旧DB。

每题 `journal/changes.json` 列出理由及revision；各正文有完整before/after Markdown，每条hide有完整before/after JSON。原始内容未删除，原归档保留。只修改local_items正文/revision、记录external edited活动及local_comments局部可见性；未增events/wake，未调整工作项状态、负责人、Git、原生会话、验收结论。

## 接续入口与验证边界

每题 `prepared-identity.json` 保存实际Git refs、OPEN工作项与必需材料清单。两份摘剪DB均以真实SQLite `quick_check`得到ok，实际状态仍为各自三项OPEN。检查是离线数据完整性核对，未运行Factory/Braid设施测试、生成应用测试或模型。

GitHub原生历史目录此前已迁移为`recovery-source-native-1790693099179942916`，活跃homes在`work/native-homes`，physical/turns全部保留；不能以缺少旧`native/`名字判为会话丢失。Sheet保持原`native/`结构。容器内路径仍为`/workspace/template`；Git worktree和native历史带此原路径，Mac副本未尝试以宿主机路径启动。

主线下一步：使用这两份template按既有保留符号链接/权限的workspace封包流程封包，接入I12冻结基包和Braid，刷新当前native材料以重建canonical上下文，再在新容器`/workspace/template`继续。必须保留原run身份；不要用最终I11状态覆盖这两份起点，不重开已完成的最终根。主线负责I12模型session预算保护、console人工介入和实际启动，本子任务没有验证这些功能。

未采用的00:59 Sheet全量展开仍在`runs/iteration12/recovery/editable/sheet/template`，只是候选来源分析副本，不能误作选定起点；可以在主线确认选定目录已封包后删除该本次重复副本。没有再做第二轮全量压缩，也没有在仅余约9GiB的WSL创建全量副本。
