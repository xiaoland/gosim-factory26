# Braid 协作能力实施与验收记录

实现前提交是 Factory `08f177a`，Braid 源码起点 `e0c3ca2`。正式独立预演发现 interrupting reset 重启接管和旧测试同 writer 连续编辑两个额外细节，已纳入实现。主 Agent 负责对象/CLI/projection/协议；独立实施 Agent 负责 store、worker、两个 resume 路径与 runtime 检查。SVC、新 profile 与 Factory 装配未改变。

当前新增 v5 迁移保留旧评论 ID、正文、request-id 和证据；普通 Issue/PR 讨论支持回复、按稳定 cutoff resolve、hide 理由、署名 reaction。参与者引用从持久逻辑 Agent 映射到 work-item，不依赖物理 session；根评论删除不级联回复。父关系可选且拒绝环，不广播父子任务状态。

运行时保留自身投影失效，原子 fence 后自动重建并继续；覆盖 terminal/reset 两种顺序、finalizing 自编辑和 interrupting 重启恢复。同类会话可重叠执行，单会话 reset/失联不回收同伴，busy close 保留且不阻塞其它工作。

本地验收：`cargo test --locked` 为 19 项单元/运行时检查加 1 项真实 CLI 集成，全部通过；`make test` 为 81 项，1 项 Linux 专属检查在 macOS 跳过。`cargo fmt`、生成探针脚本编译、diff whitespace、SVC status 均通过。Clippy 仍因既有 objects/store/context 风格告警失败（本次输出各 target 15 项），不作为已通过结果。日志归 `runs/verification/20260921-braid-collaboration/`。

## 本次真实实验

目的：证明 Agent 在原生 shell 用 CLI 自编辑后，无外部新消息也能由替代 Pi 会话继续，并最终交付可独立验证的 `calc.py`。固定当前比赛 provider/model `deepseek-v4-flash-vision-exp`，Pi backend，现有 profile；默认关闭 SVC，以隔离 adapter/context 行为。复用 `scripts/check_braid.py --backend pi`，不改比赛 runner 或安装 profile/扩展。

输入：旧标记 description、真实 CLI 准备脚本、两个将被隐藏/删除的 comment。脚本先验证普通自身 comment/reaction 不生成唤醒，再按 canonical state 分次 hide、delete、修改 description；每次新会话重读持久状态，旧 writer 在运行中被实际拒绝。最后新的 description 要求通过 PR 实现加法并按三个独立 Python 断言验收。

Oracle：同一 group/worktree 出现替代物理会话；原生实际模型输入包含新标记且不包含旧/隐藏/删除正文；没有宿主消息驱动；最终 delivery commit 的导出文件通过独立断言。原始材料归 `runs/integration/<id>/`。本探针不产生 ARC-bench 分数。无论成功失败，终态后先向用户汇报，不自动重跑或启动另一个 backend/完整 Keep；未执行的验收继续显式保留。

状态：2026-09-21 单次 Pi 探针通过，run `20260921-185322-pi-plain-2887cf`，耗时 122.76 秒；源码提交为 Braid `63459fc`、Factory `dda8ab1`。主 Agent 独立复核归档原生输入及逻辑身份。2 个逻辑 Agent 使用了 9 个物理会话，7 次重建均 applied；最终冻结交付通过独立断言。完整结果与证据归 [验收报告](../../runs/reports/2026-09-21-braid-collaboration-pi-probe.md)。本次终态后停止，无自动重跑或 Keep 追加。

真实 Codex、多个同类 Agent 的真实 provider 协作，以及完整 Keep 32 项均未由本轮新增实现证明；确定性测试和本次小型探针不能代替这些证据。
