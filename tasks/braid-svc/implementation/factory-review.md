# Factory 交付与受控探针有界审查

结论：发现两个已复现的错误判定和一个验收覆盖缺口。前两个已由主 Agent 修正并经本次复核确认；受控探针对 self-write 不产生额外 Wake 的断言仍需补齐，或明确由独立确定性检查承担。没有发现需要再次调整 Braid 产品边界的理由。

范围为父仓库基线 `93a9eb3` 之后的 `scripts/factory.py`、`core.py`、新增 `braid_runtime.py`、`check_braid.py` 及对应测试。Braid 子仓库尚在施工的代码没有作为 Factory 缺陷依据。本次只新增此报告；未调用模型、线上平台、完整 bench，也未构建子仓库。

## 1. 错误分支与其正确 commit 成对返回时，会被当成当前交付

初次检查位置：`scripts/braid_runtime.py:20` 的 `load_delivery`，以及 `factory.py`、`check_braid.py` 两个调用点。

触发：Factory 请求 `refs/heads/braid-delivery`，结果却返回同一临时仓库的 `refs/heads/factory-source` 及该分支自己的有效 commit。原检查只保证结果内部 ref 与 commit 自洽，没有对照启动请求；错误 run_id 也未拒绝。

证据：在临时空 Git 仓库调用真实 `initialize_repository` 和 `load_delivery`，使用 `status=completed`、`run_id=other-run`、初始 source 分支及初始空提交，函数返回成功。原负例只改错 ref 而保留原交付 commit，因二者不一致被拒绝，没有覆盖这个成对错误。

最小建议：`load_delivery` 接收原 request，核对 run_id、delivery_ref 和本次根 Issue 身份；保留现有仓库归属、commit 类型、ref 一致性和证据目录检查，不在 Factory 重写 Braid 的业务状态机。

状态：已修正。复核看到两处调用均传入原 request，函数核对 `run_id`、`delivery_ref` 和根 Issue。新增“另一分支＋该分支正确 commit”及另一个 run_id 负例；修正后的 `test_braid_runtime.py` 两项测试通过。

## 2. hide/delete 的全文标记断言必然误伤正确投影

初次检查位置：`scripts/check_braid.py` 初始 prompt 和 comment hide/unhide/delete 后的 Context 断言。

触发：初始根 description 包含“创建正文为 HIDDEN/DELETED 标记的 comment”的任务文字。隐藏 comment 不会删除根 description；原探针对整个 Issue Context 检查标记不存在，因此正确实现也会失败。

证据：通过 Python AST 提取原 probe 的实际 prompt 表达式，用固定 markers 求值；即使 comment 已从投影移除，description 仍包含 HIDDEN 标记。这个假阴性不需要调用模型即可确定。

最小建议：comment 操作阶段只检查该稳定 comment ID 的渲染区块；替换 description 后，再检查完整新物理输入没有 OLD/HIDDEN/DELETED。这样仍保留真实 Agent 创建 comment 的动作。

状态：已修正。当前 `comment_text` 以 `#issuecomment-ID` 定位区块，hide/unhide/delete 只检查目标区块，并检查 delete 墓碑；完整新物理输入仍在 description 替换后核对。未实际执行真实模型 probe。

## 3. probe 尚不能证明自身变更没有制造额外 Wake

位置：`scripts/check_braid.py` 的 “Same-writer mutations must not interrupt or manufacture a wake” 段，以及后续仅要求存在 NEW 替换会话的断言。

触发：错误实现把自身 hide/unhide 等操作排成普通 Wake，但当前 old turn 仍在运行，因此 Wake 暂存队列。随后外部 description 修改触发 reset，这些多余 Wake 可以与外部事件合并；最终仍会存在含 NEW 的新物理会话，应用也可能完成，当前 probe 不一定失败。

证据：静态控制流中，自身变更后只核对 comment 投影，未核对其调度事件、pending/runnable Wake 或是否产生额外执行。后续 `verified` 只要求同 group 至少一个新会话，不能区分合法外部重建与夹带自身 Wake 的实现。本条是验收覆盖缺口，不表示当前 Braid 一定有此 bug。

最小建议：在 external edit 前，通过已有状态或事件证据检查这些 writer-turn 变更没有生成额外 Wake，且 old turn 仍是唯一活动执行；也可以明确由确定性 CLI/group 检查验证这一不变量，而把真实 probe 的声明限制为正文投影、外部失效、旧 turn 写入拒绝和实际物理输入。不要仅通过增加任意 sleep 来推断没有自唤醒。

状态：已反馈主 Agent，等待补齐对应断言或明确验收归属。

## 已覆盖且本次未发现阻塞的边界

`export_delivery` 使用已校验 commit 的 Git archive，而不是 Agent cwd，能排除未提交文件和另一 worktree 的内容。生成收尾若清理、归档或证据校验失败，外层会将结果记为 generation_failed；不会只因 Braid 进程零退出继续宣称成功。新增失败工作区保留提供原始 Git common repo/worktree 的恢复证据，不等于已经实现一键 resume。

Codex 原生归档按 thread ID 寻找唯一 rollout 并核对首行身份；Pi 按其物理会话路径归档。多 worktree 会话保留各自身份和归档路径，缺失证据单独记录且阻止成功。此处以 Braid 完整会话清单为生产者契约，没有把任意未声明的文件自动猜成所需会话。

远程 evaluation 使用本次明确 attempt ID，观察和下载同一目录，再核对 run_id、benchmark revision 和应用哈希；未发现原先“挑最新另一评测”的路径残留。官方发现清单与实际测试身份比较能拒绝漏例、重复身份、跳过或无终态。没有运行 SSH、模型或完整 bench 来扩大这一静态结论。

运行了 `test_core.py` 1 项、当时的 `test_factory.py` 16 项、`test_braid_runtime.py` 2 项，均通过；交付身份修正后又单独复跑 `test_braid_runtime.py`，2 项通过。所有检查均禁用 bytecode 写入。上述测试通过没有掩盖报告中的 probe 覆盖缺口，也不替代真实核心和 bench 验收。
