# 协作身份与共同仓库技术方案

2026-09-25，技术设计待用户复核；范围与授权见 [packet](packet.md)。
SVC、模型、原生子角色与 skills/MCP 选择沿用当前材料，本轮只改 Braid 的协作环境及活动 variant 的必要接线。
取证与调用路径分别见 [身份预演](identity-preflight.md)、[Git 预演](git-preflight.md)和 [Factory 预演](factory-preflight.md)。

## 指派与具体成员

沿用现有 `--assignee` / `--add-assignee` 选择能力配置的入口，不增加创建成员命令。
配置目录使用 `glm`、`deepseek` 等已有别名和能力说明；具体成员使用 `@glm-1`、`@glm-2` 等名字。
例如根 Issue 负责人是 @glm-1，创建另一个工作项并选择相同配置时：

```text
braid issue create --title "账号与认证" --body-file auth.md --assignee glm
→ 已创建 Issue #2，使用配置 glm 指派给独立 Agent @glm-2。
```

assign 返回表示指派已持久化，不表示新会话已开始或工作已完成。
当前会话的稳定指引给出“你是 @glm-2，当前处理 Issue #2”；负责人、评论作者、reaction、通知和 CLI 文本/JSON 使用同一名字。
使用者由指派结果识别新同事，不从配置名推测是否仍是自己。

名字在创建/指派的同一 SQLite 事务内预留，之后后台 worker 启动会话时沿用它。
采用每 run 单调递增的序号和配置别名组成名字；撤销尚未启动的指派也不复用该名字，不另建成员池。
`local_items` 保存待执行指派的名字，物化时复制到 `assignments`，后者保存历史作者；原生 provider session 重启或上下文重建不产生新的人。
workers 继续按内部 profile ID 和 assignment revision 接单，去掉通过公开 assignee login 猜测 profile 的旧判断。
内部会话 UUID 留在原始证据及映射中，Agent 可见的身份使用名字，不做全局日志脱敏。

| 操作 | 成员身份与工作成果 |
| --- | --- |
| 新工作项选择同一配置 | 新名字、新会话。 |
| 同一工作项重复选择当前配置 | 返回当前名字，不重复派人。 |
| 移除当前成员，重新指派配置 | 新名字；既有停止/交接机制完成后接手该工作项的本地仓库。 |
| 会话恢复、上下文重建 | 沿用名字和本地仓库，保留未提交成果。 |
| 阅读旧评论和 reaction | 根据原作者的 assignment 显示其当时的名字，不随当前负责人变化。 |

原生 explorer/executor 等子 Agent 仍属于其父会话，不因此变成新的 Braid 成员。
创建结果补充所选配置和具体 assignee；对象读取返回具体成员，移除指派也按具体成员识别。
本轮适用于新运行，历史冻结 state 不回填名字或改写作者。

## 仓库与会话边界

```text
输入 checkout：仅提供本次运行的初始 HEAD
                     ↓
state/origin.git：共同仓库（裸仓库，无 Agent 工作文件）
├─ 集成分支：请求中的 delivery_ref
└─ PR 源分支：braid/pr-N
          ↑ push          ↓ fetch
state/worktrees/...：每个工作项各有独立 clone
├─ Issue #1 的本地仓库
├─ Issue #2 的本地仓库
└─ PR #1 的本地仓库
```

保留 worktrees 目录和数据库记录作为工作目录入口；内容改为独立 clone，不再执行共享仓库的 `git worktree add`。
每个 clone 的 HEAD、本地 refs、index 和工作文件独立，共同仓库只接受实际发布的提交。
用户熟悉的本地 commit、push、fetch 和合并操作保持原义，Braid 不额外提供发布服务或网络 daemon。
[Git 官方说明](https://git-scm.com/docs/gitrepository-layout)将裸仓库定义为不含工作树、用于 push/fetch 交换历史的仓库；[worktree 文档](https://git-scm.com/docs/git-worktree#_refs)说明普通 refs 仍在关联工作树间共享，因此只换工作目录不能补齐这个边界。

首次运行在 state 建 origin，只将输入 HEAD 写到选定集成 ref，再激活根 Issue。
各 clone 从 origin 已发布分支创建；使用 `git clone --no-local`，避免本地默认文件拷贝与其他 Agent 并发 push 竞争。
clone 单独配置提交身份（`@成员名`、`成员名@braid.local`）和必要的开发文件排除规则；不依赖种子仓库的 local config 被复制。

## 工作项、发布与合并

Issue 创建后，指派建立具体成员及独立工作会话；初始 clone 来自明确的已发布关联分支，或当前集成分支。
PR create 延续现有“先建关联 PR，再指派实施 Agent”的能力：在 origin 创建源分支后持久化对象和指派，PR clone 从该分支开始。
工具结果显示源分支和基准提交；新 PR 不会隐式带入创建者尚未发布的本地文件或提交。
需要共享既有成果时，Agent 先发布分支，再让协作者取得和整合。

正常 PR 操作示例（PR Agent 已在 braid/pr-1 分支）：

```sh
git add frontend backend
git commit -m "实现账号与认证"
git push -u origin braid/pr-1
braid pr ready 1
```

`ready` 对准该 PR 的已发布 head，沿用当前调用身份和本地候选检查；本地 HEAD 与 origin head 不符时明确说明尚未发布或需要取得更新。
重复 ready 同一提交保持同一候选；发布新版本后需要重新 ready。
合并直接读取 origin 的 ready head 和目标 head，通过已有 Git 对象合并能力计算结果；实际冲突反馈到 PR，由 Agent 在自己的 clone 处理并重新发布。

准备好的合并记录仍保存 base/head/result，使 Git 更新与 SQLite 收据之间的中断可恢复。
推进分支使用 Git 自带 ref 事务，在同一操作中验证 PR 源 head 并更新目标 head；一方变化则不发布准备好的结果。[git-update-ref 文档](https://git-scm.com/docs/git-update-ref)支持这一 verify + update 方式，无需另建合并队列。
整个 merge 与恢复过程不访问任何 Agent 的 index 或工作文件，也不 reset 根 Issue 仓库。
返回结果说明实际合入的 source/merge commit，PR 保持自身状态事实；Issue close 继续由 Agent 决定。
合并成功的反馈说明共同目标分支已更新，并提示使用原生 fetch 取得更新；各客户端何时整合自己的文件由其 Agent 决定。
合并失败保留具体原因和未合并事实，不由 Braid 自动改写评论、关闭 Issue 或认证 Agent 的完成声明。

## 接续与证据

原生会话恢复、上下文重建复用该工作项的本地 clone，保留它的未提交文件和本地提交。
明确改派时，原执行结束后将该工作项的 clone 交给继任者；更新具体成员身份，不重新 clone 覆盖成果。
本轮只新建运行 state，不改写历史冻结运行的仓库或身份；旧运行仍以其冻结 runtime 和原始记录解释。

Braid 的 `result.repository` 和 `delivery_commit` 来自 origin。
Factory 的提交历史发布、最终 commit 解析和 `git archive` 导出统一改为读取这个共同仓库；输入 checkout 仅保留初始化来源的含义。
Agent 可见的身份使用具体成员名字，原始诊断保留逻辑/原生会话的内部 ID 映射；不做全局文本脱敏。

现有 variant 的“禁止 push”改为允许对本次 origin 进行正常协作，保留外部操作的原有授权范围。
Braid 指引只介绍当前成员、工作项、本地仓库与 origin、CLI 操作；原生子 Agent 的使用仍由 Pi/Codex 自身提供。
SVC 方法和当前 variant 的设计/实现工作约定不因本次技术修正扩展。

## 改动范围与实施准备

身份改动集中于 Braid 对象层、assignment 的持久化与领取、会话指引及已有证据字段；共同仓库改动集中于初始化、工作目录物化和 PR ready/merge。
Factory 仅调整活动 variant 的指引、三个 Git 仓库消费者和成员字段归档，复用现有 helper、构建与提交工具。
没有新增网络服务、调度池、合并队列或模型依赖。

技术与验收方案复核后，按“持久化与返回合同 → 独立 clone 和发布/合并 → Factory 消费者及指引 → 构建冻结与完整 benchmark”细化实施计划并做独立预演。
实施准备完成后提供具体影响和实验输入，由用户作开工确认。
