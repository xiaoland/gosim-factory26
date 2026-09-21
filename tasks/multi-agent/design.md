# 方案与证据

CLI 与单一配置部分已获实施授权；多 Agent 协作及共享材料部分仍是待复核方案。

## CLI 的熟悉度与实际语义

实施前 [cli/mod.rs](../../sources/braid/src/cli/mod.rs) 的入口为 `braid object --state … --writer-turn …`，读取使用 read，comment 创建使用 `comment create issue|pr ID`，正文只支持 `--body-file`，其 `-` 会被当作文件名。Issue/PR edit 只修改正文，没有 gh edit 的 title 等可选项。这些差异是本轮 CLI 调整的原因。

建议去掉日常入口中的 object 层，对齐常用的 `issue/pr view`、`issue/pr edit`、`issue/pr comment ID`，提供 `--body/-b`、`--body-file/-F`（包括 stdin）和适用的 `--title/-t`。已明确传参时不启动编辑器、浏览器或交互确认。view 默认给精简文本，结构化输出通过显式 JSON 选项取得；未知字段或参数明确报错并给最短正确用法。writer turn 仍由每轮提供并核验，不以多个 session 共享的可变环境变量替代当前身份。

对齐依据：[gh issue comment](https://cli.github.com/manual/gh_issue_comment)、[gh issue view](https://cli.github.com/manual/gh_issue_view)、[gh pr create](https://cli.github.com/manual/gh_pr_create)。重新核对本地产品后，移除 pr ensure 强制依赖请求 comment 的约束，改为 pr create --issue ID --title TITLE --body/--body-file …，直接创建本地实施工作项并激活 PR Agent；无需 GitHub 发布或预先存在的实施分支。可选 --request-id 同键返回已有 PR，不更新内容、关系或重复激活；无键每次新建。该本地激活语义在 help 和运行协议中明确说明。保留按稳定 comment ID hide/unhide/delete 和 Context 查询，不以“最后一条 comment”推断多 Agent 写入目标。父子 Issue 关联和委派仍属后续方案。

## 协作的职责和生命周期

[local.rs](../../sources/braid/src/local.rs) 为 Issue/PR 各启动一个 worker；[group/worker.rs](../../sources/braid/src/group/worker.rs) 每 worker 仅保存一个活动 turn。对象存在多个不代表执行已经并行。[objects.rs](../../sources/braid/src/objects.rs) 的 issue_in 没有填充父子关系，create_issue 只建立独立 Issue，完成也不会沿父关系回传。

建议复用现有 group、队列、provider session、上下文重建和 PR 合并链，补齐父子 Issue 的创建/关联、环检测、状态投影及结果唤醒。根 Issue 负责总目标和最终集成，子 Issue 表示有边界的需求或调查任务；一个 Issue 仍可对应多个 PR，一个 PR 仍可关联多个 Issue。研究、设计、排障或验证工作可通过子 Issue 的 comment 和材料返回，不为了维持形式而创建空代码 PR。

委派正文给出目标、输入引用、局部 requirement、写入范围、完成条件和返回对象。父 Agent 派发后结束当前 turn，子结果通过事件唤醒父 Agent；不能让父 turn 占着执行位置等待孩子。实施 Agent 在独立 PR worktree 修改与自检，子 Issue 汇总本范围结果，根 Issue 对 delivery 分支的集成负责。完成子 Issue 不自动证明父需求满足，根提前关闭仍须被未解决的必要工作阻止。

先允许同类 group 实际并行，以 run 级活动 turn 容量控制负载，建议首次为 2。控制容量不能占用在 idle 或等待子结果的 Agent 上；取消、重建和恢复必须按 group 定位，不能误伤其它会话。修改父需求时由已声明的依赖和受影响任务传播，不把全部父子全文无差别注入每个 Agent。

## SVC 与共享任务材料

SVC `svc lookup --path task-packet/index.md` 明确 packet 保存任务局部信息，不拥有 runtime 工作图；`sub-agents/index.md` 的 Primary 持有全局任务，Child 持有有边界的 Assignment。Braid 独占执行状态、父子关系、唤醒和生命周期；SVC 定义任务分解、最小交接、信息归属和验证方法。Factory harness 组合这两者，Braid 不解析 SVC packet schema，SVC 不直接调用 Braid。

当前 svc task init/grow 按指定目录定位 packet；识别 worktree 身份不等于共享其中的文件。建议每个 run 有一个明确的任务材料根目录，位于隔离应用各 worktree 之外；所有 Agent 通过明确引用访问同一份材料。根 Agent 维护公共入口和公共契约，子 Agent 只写被指派的独立模块，同一文件只有一个写入者。Issue/PR description 保存当前委派与材料引用，详细调查、设计和验证证据放入模块；packet 不再维护第二套 running/done 状态，也不强制每个小 Issue 都生成完整目录模板。

已核对 [task_packet.py](../../sources/svc/cli/src/svc_cli/task_packet.py) 的 locate_task_packet：`--repo` 在此只要求现有目录，不强制另建 Git 仓库，因此可用 `svc task init … --repo <本次材料根目录>` 复用现有 CLI。多 Agent 共享该根目录属于 Factory 的运行装配，不需要先给 SVC 增加 registry 或同步服务。

提交材料的 comment 应指向已经写完的版本；跨 Agent 可变输入需要明确版本或内容哈希，避免在不同 worktree 里把同名但不同版本的文件当成共同事实。变更公共契约时必须发布变更并说明受影响任务。先复用现有文件、Git/哈希及对象事件，不建立双向文件同步服务。长期应用文档随 PR 进入交付 Git 树，临时 packet 与诊断产物独立归档。

根 prompt 继续引用完整 requirements 包。子 Issue 可以内联局部需求，同时保留来源标识和必要的公共约束；“不用读全部需求”不能变成“丢失交付、隔离或全局接口约束”。全局运行授权、禁止读取评测器及交付契约必须由 Factory 对所有 Agent 提供，而不只停留在根 description 中。SVC user-scope 继续保持简单导航，组合运行的具体绑定归 Factory 契约。

独立 advisor 支持单一执行权威与事件回传，建议公共材料单写入者和发布版本。主 Agent 将单写入者约束应用到各独立模块，以免所有材料变更都串行排到根 Agent；具体发布与失效行为纳入实施前预演。

## 单一 Variant 与后端

已采用的配置方案：活动配置收敛到 `variants/factory/config.json`，固定 Braid + SVC，backend 用 pi/codex 参数选择；共同 prompt 与入口继续放在 harness/，原生接入沿已有 adapter 维护。不为 backend 复制整套 variant。第一版一个 run 选一种 backend，仍使用比赛给定模型；同时混用两种 backend 不是实现多 Agent 的前提。

历史 run 和报告保留原 variant 名称及实际来源。旧配置退出活动 variant 入口，但迁移前核对旧命令和分析读取的使用者，不删除历史证据。后续消融作为新的显式实验配置加入；成绩比较仍要区分 backend、并发和实际源码，不能因 variant 名相同就混为同条件。
