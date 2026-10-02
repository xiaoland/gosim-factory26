# pi-team-mixed 接线预演

2026-09-25 主 Agent 只读追踪当前消费者，未修改源码、构建或运行实验。
本轮 SVC 内容与已选择的 skills/MCP/原生角色配置保持当前材料，不做方法改稿。

## 共同仓库的消费者

`variants/pi-team-mixed/run.py::generate` 当前创建 `work/application`，以 `initialize_repository` 生成初始提交，再把同一路径作为各 profile 的输入 workspace。
保留这一种子仓库的职责；Braid 从其 HEAD 初始化本次 `braid-state/origin.git`，之后所有生成中的共享版本从 origin 读取。
`read_runtime_result`、Braid `result.repository` 与 Factory `delivery.repository` 应一致指向该 origin；最终确切提交仍由请求指定的 delivery ref 解析。

当前下列三个消费者都传入旧 `app` 路径，必须一起调整，否则可能合并发生在新 origin，导出仍读取旧仓库。

| 消费者 | 修改 |
| --- | --- |
| `load_delivery(app, request)` | 活动 variant 改传 origin；冻结共同分支当前确切 commit。函数已按传入 Git 仓库解析 ref，无需增加兼容解析或回退。 |
| `export_delivery(app, commit, ...)` | 改传同一 origin；已有 `git archive` 从 commit 导出，无需依赖工作目录。 |
| `publish_history` / `watch_history` | 将 ARC history publisher 的 `--source-repo` 改为 origin。已有发布器只使用 rev-parse/fetch/update-ref，无需改 SDK 或重新实现提交历史。启动时共同仓库及初始 ref 尚未就绪是等待状态，真实 Git 错误仍记录原文。 |

`scripts/braid_runtime.py` 的 load/export 接口可原样复用，归档 variant 仍显式传其旧 source；不让公共 helper 猜测不同版本的 canonical repository。
`lab/arc_bench/agent_runtime/__main__.py::publish_history` 在 Runner 输出目录维护的是用于官网展示的 Git 历史，它不是 Agent 的共同 origin；保持原用途。
不因本次改造引入按源码存在或 Issue 状态判断产品完成的新闸门。

## 身份与指令

活动成员 profile 中 `assignee_login` 的实际含义是配置选择名，需按身份 LLD 改成明确的配置别名；模型、reasoning、原生子角色不变。
Braid 负责稳定身份、配置选择、origin/分支和操作说明；variant 继续只提供参赛需求、工作约定与工具装配。
根 Issue prompt 将“使用当前工作项分配的 Git worktree”调整为准确的本地仓库表述，并授权对本次 origin 的 push/fetch；清除与正常协作冲突的笼统“禁止 push”。
保持现有按内聚需求拆分、无人中途介入、Issue/PR 工作约定；不借此次接线增加 SVC 方法或固定协作任务图。
新 clone 的 Git config 由 Braid 初始化，需要具体成员名时由 Braid 的身份映射提供，不能依靠种子仓库的本地 user.name 自动继承。

## 证据和构建

`archive_state` 的当前 state 与 `run/braid-state` 同地，origin、每个客户端目录和 SQLite 原始状态继续保留；生成结束时删除的 `work/` 不应包含唯一的共同仓库。
session manifest 新的可读成员名字应穿过现有归档，原生子 Agent 继承父 Braid Agent 身份，不冒充另一个 Braid assignee。
`scripts/core.py` 的继承字段与 `braid_runtime.py::export_telemetry` 的选字段清单需随之核对，保证 raw 证据能把公开名字、逻辑 Agent 和原生会话关联起来。
此前 run 的 physical instructions 在下载归档里有缺口；新运行在实际归档中核实，缺失时保留缺口，不据此假装已取得实际系统输入。

`scripts/package_agent.py` 继续通过本 variant 的 `build.py` 装配，SVC/领域技能沿用已完成材料。
本轮必须由当前 Braid 源码重新构建 Linux binary；复用 Docker、Cargo、npm 与浏览器缓存，不能继续使用先前技能包中的旧 Braid binary。
已有打包 manifest、源码交接包及具体文件摘要足以记录工作树差分，不添加新的测试或另起一套构建系统。
旧 ZIP、state 与官方 run 不修改；本轮制品进入新的实验目录。

## 实施顺序约束

身份的公开字段、共同仓库路径及 Braid result 合同先定稿；Factory 再一次性接上指令、三个仓库消费者和证据字段。
独立源仓库与父仓库均有前序未提交变更，实施时按任务文件归属保留，不重置工作树或将旧变更归入本轮提交。
验收沿用真实生成应用及官方 benchmark；本页静态调用追踪不是运行证明。
