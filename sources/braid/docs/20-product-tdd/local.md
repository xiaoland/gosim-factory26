# 本地运行契约

`braid local request.json` 将一个已有本地 Git 仓库中的需求建立为根 Issue #1，沿现有 Context projector、SQLite queue、Agent Group、SessionManager 和 provider adapter 执行。它没有固定设计/实施阶段数，不调用 GitHub HTTP 服务，也不把 provider 单轮正常结束或工作项状态解释为应用完成。

面向 Agent 的稳定入口只介绍熟悉的协作对象：使用 `braid` CLI 操作 Issue / PR，常用操作沿用 GitHub CLI 的形式；Issue 和 PR 可以指派给其他 Agent，成员通过正文、评论和回复协作。创建未指派的工作项不启动独立成员；指派才建立该项的成员与工作区，创建回执应明确显示实际负责人或未指派状态。维护者所需的 queue、session、provider 和 Context 生命周期仍记录在本文后续章节，但不作为使用 CLI 前必须理解的概念，稳定指令说明 Issue 负责需求、设计和验收依据，实施前指派关联 PR，由独立 PR 负责人承担计划、排障、实现与验收；它不规定这些工作的具体方法，也不指导原生子代理使用。

Braid将当前Issue/PR身份及职责、成员名、通用对象协议与调用方profile拼成一份instructions。通用协议按工作资料、讨论整理、通知与读取、指派交接和CLI差异组织；指派即启动独立成员、published head与在途工作不同、正文edit为全量替换、root resolve与单条hide、订阅和Closes语义只在此处说明。增量评论本身不要求公开回复；成员可在持续保留的clone文件中保存私有状态，只将接手者需要的结论、依据与入口放入公开讨论。调用方profile负责自身配方政策与交付条件，避免再复制通用协议或原生工具教程；具体工作事实归Context和事件消息。已有原生历史不因指令文案去重而改写。

## 请求与启动

请求是 JSON，严格拒绝未知字段：`profiles`、`root_profile_id`、`bindings`、`codex`、`pi`、`bub`、`prompt`、`state`，以及可选的 `run_id`、`delivery_ref`。`profiles` 是成员配置列表，`root_profile_id` 选择根 Issue 的配置，`bindings` 以 Profile ID 索引原生运行材料。Braid 不接收 preset 或 variant，也不为后续 Issue/PR 设置默认成员。`delivery_ref` 默认为 `refs/heads/braid-delivery`。各 Profile 的 `workspace` 指向同一个具有初始 HEAD 的输入仓库；调用方负责初始化和运行授权。Braid 在 `state/origin.git` 建立本次运行的裸仓库，将输入 HEAD 发布到 delivery ref，并从此为每个工作项在 `state/worktrees` 建立独立 clone。PR 缺省 head 从所选 base 的当前 origin commit 建立；提交只有经 push 发布后才进入共同历史。

Profile 的 `assignee_login` 是成员命名前缀，`assignee_description` 是职责说明。前缀在配置间唯一，采用 1–39 个 ASCII 字母、数字或单连字符，不能以连字符开头或结尾；description 是最多 240 UTF-8 bytes 的非空单行说明。每个配方独立提供下一位虚拟候选成员：尚无历史时，前缀 `glm` 和 `deepseek` 对应 `glm-1` 和 `deepseek-1`；成功指派 `glm-1` 后，负责人就是 `glm-1`，下一次目录提供 `glm-2` 和 `deepseek-1`。目录读取不占号、不创建会话，序号在成功指派事务持久保存成员身份后才推进。候选不是已有空闲成员，不允许把一个成员复用到另一个工作项。

带 `root-only` tag 的 Profile 可由宿主通过 `root_profile_id` 用作根 Issue 入口，并沿同一命名前缀规则生成根成员；它不出现在普通指派目录中，也不能由后续 Issue/PR 的 assignee 操作选择。旧具体成员名保留，不重新编号；下一位取 `local_items.desired_member_login`、`assignments.member_login` 和保留的 `local_subscriptions.member_login` 中同一精确前缀加正整数的最大序号加一，不再由旧 `local_run.next_member_sequence` 全局计数决定。取消指派保留已认领名字的历史，即使尚未创建原生会话，也不回收序号。其余 provider、model、reasoning、user_instructions 和上下文限制只属于宿主诊断；binding 持有 executable、native_template、native_home.root、能力材料摘要。模型只有 Profile 一个权威，PiConfig 不再重复模型与 reasoning。local 请求必须为实际使用的 adapter 提供对应的 `codex`、`pi` 或 `bub` 配置，不能缺少或多出未使用的配置。Codex 配置保留版本/schema 身份；连接凭据只传环境变量名或凭据文件路径，不写入运行归档。每个新物理会话从模板派生独立 native home，resume 必须定位原 home。

当前候选目录、根成员命名和新指派校验只读取已冻结的 `state/request.json` profiles，其有效ID、公开前缀、职责和tags是当前配置事实。请求缺失、解析失败或配置无效时明确拒绝，不从历史profiles表回退；已移除或新增root-only的配置不再提供新候选。profiles表保留历史物化配方，revision是内容hash的前15位，不表示时间顺序，不能通过max(revision)判断当前配置。宿主隐藏诊断 `profile list/view` 的回包标记 `source=profile-history`，其中数值最大的历史revision也不代表当前有效配置；既有负责人、历史成员及序号继续保留。此读取边界不改变离线恢复的模型与配方一致性检查。

state 是输入仓库外的绝对目录。首次运行建立当前嵌入 schema 的 braid.sqlite3、请求身份记录及裸 origin；再次以相同 run_id、输入 HEAD、delivery_ref、prompt 及 profile 材料启动可恢复运行状态。运行持有独占文件锁，阻止两个 runtime 同时控制同一 state。不同请求不能覆写旧证据；origin 的已发布提交和每个 Agent clone 的本地文件在恢复时保留。旧版本已封存状态仍拒绝恢复，无需迁移。早期迁移保持不可变，其中历史远端缓存表不再是本地正文权威，也没有远端 worker 消费它们。v5 保留旧 comment 身份并加入讨论线程；v6 曾保存工作项 Profile 及旧默认指派；v7 在 Profile record 增加可空的公开 assignee 投影；v10 保存 PR base/head/draft 与合并引用；v11 保存评论定向投递回执；v12 保存工作项关注、活动历史和根 Issue 空闲检查状态；v13 为新建 PR 保存创建时的 base commit，以及 Braid 曾观察到不在目标分支中的 head commit，旧 PR 保持空值。新运行只用明确的根成员和对象 assignee；旧库已记录的非空 assignee 保留，不根据 model、provider 或内部 ID 推断新的公开身份。

## Pi 启动与失败恢复

Pi 在不带 `--session` / `--continue` 启动时已经创建新会话。
Braid 直接用 `get_state` 取得其身份，不再发送一次 `new_session` 重复销毁和建立运行时。
恢复已有会话仍传入确切 `--session` 路径，并核对返回路径。
首个身份握手包括进程冷启动及扩展加载，使用 `pi.startup_timeout_seconds`（缺省180秒）；随后控制 RPC 的时限为30秒，二者不影响模型生成时长。
日志保留进程 PID、工作目录、native home、Pi 自带启动耗时以及失败的请求名。

创建失败且未取得 native identity 时，错误原因保留在物化记录中。
只有宿主证明旧执行已停止、持有运行锁、工作项及指派仍有效、旧 turn 已终态且没有新会话时，离线恢复才重新处理同一个 reset。
恢复资格依据持久身份与生命周期，不依赖错误文案；不自动循环重试，不重新唤醒已关闭的旧工作项。

## 对象与 CLI

local_items 保存 Issue/PR 的完整标题、正文、状态原因、PR base/head ref、创建时的 base commit、曾观察到的独有 head commit、draft、最近一次 ready 时观察的 commit 和可选 request-id。local_comments 保存稳定 comment id、完整可恢复正文、生命周期及作者；删除保留墓碑并清除正文。associations 是独立的 N:M 关系表。一个 Issue 可以关联多个 PR，一个 PR 可以关联多个 Issue。`--issue` 和 `pr link` 表示提供需求与讨论背景，不是 GitHub Development 面板的自动关闭链接；创建、link 的帮助与回执明确此区别。关闭意图另由 PR 正文关键字表示，见合并契约。新建 Issue 和 PR 在同一仓库共用递增编号，根 Issue 为 #1，后续对象从两类当前最大编号之后分配。旧库可能已有 Issue #1 与 PR #1；它们继续按 kind+number 访问，不迁移编号，新对象仍从两类最大编号之后分配。

`pr create` 直接建立本地 PR 对象；显式指定 assignee 才会通知该负责人处理。它不发布 GitHub PR。`--base BRANCH` 选择本次 origin 中已发布的目标分支，缺省为 delivery ref；`--head BRANCH` 采用已发布的源分支，缺省时从所选 base 建立 `braid/pr-ID` 分支。两个参数都须是分支引用，不接受任意 commit。创建默认非 draft，可用 `--draft` 指定草稿。命令输出给出实际 head/base ref 及 commit。可选 `--request-id` 是调用方提供的精确重试键：同键只返回首次创建的 PR，不更新标题、正文或关联，也不重复激活；省略时每次新建，不按标题或正文猜测重复。创建分支前先验证全部关联 Issue。Git ref 不随 SQLite 回滚；若重试遇到同名残留分支，只在其 tip 等于本次选择的 head 时复用，否则拒绝覆盖并保留现场。PR、关联和需要的 Assign 事件在同一个 SQLite transaction 内提交。

Agent 在原生执行环境中直接运行 `braid` 对象命令。CLI 从该执行实例继承运行目录与不透明身份，在对象写事务中解析当前 session、assignment 和作者；不需要 Agent 复制运行参数。宿主传运行目录时把 `--state PATH` 放在子命令前，例如 `braid --state PATH issue list --state all`，以区分运行目录和列表状态筛选。宿主的显式控制输入仍使用 `--external`，Agent 执行环境不能使用它。身份只授权其所属工作项的当前执行，不按工作目录或 login 猜测最新 session；旧执行被替换或改派后不能借用新执行的身份。

Codex app-server 与 Pi RPC 的每次原生进程启动或实际恢复都由 runtime 接入本次执行身份及 CLI 路径，不修改宿主进程环境。身份在 provider session 登记后才可用于模型工作；恢复和上下文替换会撤销旧身份。活句柄快返不产生另一个身份。运行环境标记仍禁止 `--external`；这约束正常 Agent 调用路径，不提供针对清除环境变量、直接改数据库或不同操作系统用户的安全隔离。

```sh
braid issue edit 1 --title "Current design" --body-file design.txt
braid issue comment 1 --body-file note.txt --json
braid issue comment 1 --reply-to 8 --body "补充信息"
braid issue view 1 --timeline --after 0 --limit 30
braid issue list --state open --limit 30 --json number,title,state
braid pr list --state all --limit 100 --json number,title,state,headRefName
braid issue subscribe 1
braid assignee list
braid pr create --issue 1,2 --title "Implement design" --body-file request.txt --assignee glm-1 --json
braid pr create --issue 1 --title "Review published work" --body "Already implemented" --head refs/heads/issue-1
braid issue edit 2 --add-assignee deepseek-1
braid comment hide 8 --reason "已由后续信息替代"
braid comment resolve 8
braid pr ready 1
braid pr ready 1 --undo
braid pr merge 1 --merge --match-head-commit "$(git rev-parse HEAD)"
braid issue close 1 --reason completed --comment "当前问题已处理"
```

顶层 `issue` 和 `pr` 支持 `list`、`view`、`create`、`edit`、`comment`、`subscribe` 和 `unsubscribe`；当前负责人不能退出自己工作项的关注。list 默认按编号倒序返回最多 30 个 open 工作项；`-s/--state` 可选 `open|closed|all`，PR 还支持 `merged`，其中 PR 的 `closed` 包括已合并；`-L/--limit` 必须至少为 1。`-a/--assignee` 按当前具体成员名筛选，PR 列表还可用 `-B/--base`、`-H/--head` 筛选分支。输出说明返回数量、limit 和 `has_more`；JSON 保留原数组形状，截断提示写到 stderr，不能把 stdout 数组当成完整集合。需要更多项时显式增大 limit；本接口没有新增列表分页协议。

edit 可只改标题、只改正文或同时修改，写回执不再回显整篇正文。正文接受 `-b/--body` 或 `-F/--body-file`，`-F -` 从 stdin 读取。list/view 默认输出文本；裸 `--json` 输出全部支持字段，`--json number,title,state` 等选择只返回所选字段。`number` 是可操作编号；旧 `id` 同为本地编号，不暴露内部 UUID。PR 保留 `headRefName`、`baseRefName`、`isDraft` 及原蛇形字段；PR view 还支持 `headRefOid`、`baseRefOid`。不请求 body、execution、comments 或详细字段时，不加载对应正文、执行事实、讨论或关联讨论。原始正文完整保留，JSON 解码后的 body 可保存到文件后全文编辑。

`view -c/--comments` 以文本显示讨论；JSON 显式选择 `comments` 即可读取。`--comments` 与不含 comments 的字段选择冲突，不静默忽略。`view --timeline` 以 `--after` 和 `--limit` 读取协作活动，不自动展开全部历史；它不能与 `--comments` 同用，也只接受裸 `--json`，不接受对象字段选择。时间线文本输出评论身份或参与者与动作，分页在末尾提供续读命令；JSON 输出 `items`、`after`、`limit`、`has_more`、`next_after`。下一页以末条记录的全局活动序号作游标。评论行给出可操作的 Comment ID 和读取入口，JSON 保留 `ordinal` 与 `comment`。Issue view 的详细字段包括 `parent_issue`、`sub_issues`、`associated_prs`；PR view 包括 `associated_issues`、`closing_issues`、引用和合并 commit；二者可选 `subscriptions`、`execution_error`。未知字段或不支持的组合明确报错。

写命令默认先给目标编号、本次改变和结果，创建、编辑、close/reopen、link/unlink 及评论动作可显式 `--json`。单目标短 JSON 的 `id`、`number` 排在回包开头；Issue/PR 的编号是工作项编号，评论的编号是 Comment ID。编辑回执给 `changed_fields` 和本次事务中的负责人；创建回执保留 `id`，新增 `number`，不提交后重读对象来推断本次效果。PR 复用 request-id 时 `created=false`、`changed=false`，不冒充新建。默认评论回执只证明已创建或已编辑，详细投递通过 `braid comment view ID --json deliveries` 按需读取；queued 只表示等待投递，delivered 只表示原生会话接受了输入，均不证明已经处理。

ready/merge 保留原 `head_commit`/`draft`、`merge_commit` JSON 字段，并增加目标编号与本次效果。ready 的 `head_commit` 是本次观察到的已发布 head，`ready_commit` 是实际保存的最近 ready 观察，二者在无 draft 状态变化时可以不同；`changed` 包含实际记录的新 head 观察，不表示产品通过验收。merge 的 `outcome` 区分 `already_merged`、`recorded_existing_integration`、`applied_prepared_merge`；`git_ref_updated` 只描述本次引用更新，`closed_issues` 只列本次确实关闭的 Issue，`target_commit` 是实际应用路径观察到的目标提交，无变化早返时为 null。merge 失败保留具体错误；已保存的合并意图、已观察到的 Git 效果和对象完成尚未确认的部分分别说明，并给只读查询入口。非零退出不能统一解释为完全无副作用。

此外保留 issue close/reopen、pr link/unlink/ready/merge/close/reopen、稳定 ID 的 comment edit/hide/unhide/delete、`context issue|pr ID` 和 `status [--json]`。Issue close 可省略 `--reason`，指定时只能是 `completed`、`not planned`、`duplicate`；解释正文用 `--comment`，PR close 没有 reason 参数。close/reopen 的可选评论与状态变化同事务提交；已是目标状态时报告无变化，不再发表评论。回执中的 OPEN/CLOSED 是已提交的对象决定；先等动作成功再向协作者宣告关闭，评论创建不等于对方已收到或处理。旧状态中已经保存的自由文本 reason 保留原样，不冒充枚举。根 Issue 与其它 Issue 的 close 都只记录对象决定，reason 不作为运行状态码。PR merge 的 `--merge` 使用已有即时本地 merge，裸 merge 保持兼容；`--squash`、`--rebase`、`--auto`、`--disable-auto` 明确报尚未实现。

Issue/PR 的正文保存本项当前任务、交付与证据入口，不维护其他工作项或分支不断变化的全局状态镜像。当前集成状态由整合任务维护，并链接各项历史成果。

Agent 通过 GitHub 式 assignee 认识协作者。`braid assignee list [--json]` 只列出当前可选择的具体成员名及职责。`issue/pr create --assignee MEMBER` 与 `issue/pr edit ID --add-assignee MEMBER` 直接选择目录中的成员，成功后公开负责人和联系地址都使用输入的同一个名字；裸前缀 `glm`、`deepseek` 不是合法的新指派输入。创建时省略 assignee 保持未指派。目录可变，实际指派在 SQLite immediate transaction 内重新核对并认领候选；已占用、过期和未知名字都拒绝并返回最新具体候选，不静默换人。

`--remove-assignee MEMBER` 精确匹配当前具体成员。已有负责人时，选择另一候选必须在同一命令移除当前成员；remove 当前成员并 add 新候选是原子改派，即使两位成员来自同一配方也会更换负责人。重复 add 当前成员，或者同一命令 remove 并 add 同一当前成员，均视为指派无变更，不创建新会话、不递增 assignment revision；同一命令的标题、正文和父关系修改仍正常生效。错误 remove、不可用候选和无效组合在任何对象、revision、event 或 wake 写入前拒绝。PR request-id 重试直接返回首次实际创建结果及现有负责人，不因首次候选已被认领而失败，也不认领另一候选。

创建与改派回执给出已登记的具体负责人；Issue create 的 JSON 保留 id 并包含 assignees、assignment_note，PR create 同样返回负责人。回执只表示责任关系已登记，不表示模型已经开始或完成。工作完成或原生会话休眠不撤销指派；当前成员仍可通过明确地址收到后续消息。取消指派撤销责任，不能用于回收空闲执行资源，原成员名字不再作为新候选返回。

重新指派的单个事务核对具体候选、保存目标、递增 assignment revision、fence 旧 writer 并排队一次 Assign/Wake。runtime 在事务外关闭自己持有的旧 provider 会话；关闭完成前新 owner 不能建立 assignment，provider 关闭失败时保持 stopping/pending。完成后把原工作项的 clone 交给新成员，更新其中的本地 Git 提交身份；讨论、未提交文件和既有提交继续保留。Context 重建及恢复保留逻辑成员身份，只有明确改派才更换成员。Issue 与 PR 的 canonical object、list/view JSON 投影当前具体 `assignees`；Agent 可见的 Context 和 instructions 给出当前成员，候选目录按需查询，界面只展示具体成员名和职责，不讲内部配方或 Profile。评论、reaction 和通知按当时写入者的成员名展示；原始 UUID 映射留给宿主证据。Agent runtime 隐藏 `profile list/view`、物理 session 状态及内部 profile/model/provider/digest/generation/revision 字段；无 runtime 标记的宿主诊断仍保留这些信息。

在 Agent runtime 中，`status` 列出 Issue/PR 的编号、标题、状态、公开负责人及当前指派最近一次失败、结果未知或恢复暂不可用的执行事实；`status --json` 保留 `items` 外壳并为每项输出 `kind`、`id`、`title`、`state`、`assignees`、`execution`。`execution` 只含结果、发生时间和至多 200 字符的首条错误摘要；没有当前故障时为 null。Issue/PR view 提供同一事实，`--json execution_error` 可读取去除 UUID 的完整错误文本。原始错误持久保存在 `turns.error` 或已有恢复字段中，由宿主数据库诊断取得。失败事实查询不依赖 Profile 的通知开关；上下文压力及具体错误仍保存到既有状态记录。最近尝试是执行事实，不判断 Issue/PR 是否完成，也不自动改派或广播评论；后续成功终态或成功恢复会清除当前故障投影。无 runtime 标记时，宿主仍获得原有执行计数、物理 session 和诊断字段；内部 `local::status` 也继续为调度与结果判定生产同一摘要。

Issue 与 PR 的普通评论均支持 `comment ID --reply-to COMMENT_ID`（完整前缀是 `issue comment` 或 `pr comment`）。回复必须指向同一 work-item 中已有评论，跨项错误指出实际所属项和单条读取入口；删除只保留墓碑，不删除回复关系。`comment view ID` 直接读取指定评论时显示已解决讨论中仍可见的正文；`--thread` 浏览整段讨论时仍折叠已解决历史。独立隐藏的正文继续隐藏，输出给出 `--include-hidden` 的读取命令；该参数也可展开整串的隐藏及 resolved 历史，无法恢复已删除正文。 单条读取在 SQL 中直接限定 Comment ID，不先加载整串再筛选。`comment view ID --json` 保持数组形状，精准单条含一项，`--thread` 是整串数组；支持 `--json database_id,body`、`--json deliveries` 等字段选择，未知字段报出合法字段。全文 body 不自动截断，`--thread` 仍受原可见性规则控制。

`issue/pr comment ID --edit-last` 修改当前 Braid 成员在该工作项最后一条未隐藏、未删除的评论（已解决线程仍计入），正文仍用 `-b` 或 `-F`；`--delete-last --yes` 删除同一范围内的最后一条评论，不接受正文。宿主 `--external` 没有当前成员身份，不能使用 last 模式。没有可选目标时报错，不隐式创建新评论。按评论 ID 的 `comment edit/delete` 继续提供精确操作。

`comment resolve ROOT [ROOT...]` 与 `comment unresolve ROOT [ROOT...]` **只接受讨论根 ID**。传入回复 ID 时整批不写入，错误给出其所属根及正确命令；需要局部整理时使用 `comment hide ID --reason TEXT`。resolve 记录该根讨论当前最大 Comment ID 为折叠截止，后来的回复仍可见并送达，不自动 unresolve。重复 resolve 可把已新增的回复纳入新的前缀；unresolve 清除整串截止，仍尊重独立 hide/delete。同根平级回复不能分别 resolve，独立关闭条件应建立独立根讨论。

两条命令的批量参数和 `--json` 对称。回执给 `thread_root`、此前的 `previous_resolved_through`、现在的 `resolved_through`、`affected_comments` 和 `changed`；affected_comments 是此次前缀范围发生改变的评论记录数，包含独立 hidden/deleted 记录，不等于实际可见正文数量。文本同时说明新回复继续可见、hide/delete 保留。单次多 ID hide/resolve/unresolve 在一个 SQLite 事务中先校验全部目标，再更新及发出既有事件；重复 ID 去重，校验失败不提交部分结果。`comment hide ID [ID...] --reason TEXT` 的理由可选，保留正文与身份，不隐藏后续回复；delete 清除正文且不可恢复。hide、unhide、delete、edit 及 reaction 的短回执从本次动作返回 changed，不通过后读当前对象推断。`comment reaction add|remove ID EXPRESSION` 用当前逻辑 Agent（宿主为 external）署名，同作者同表达幂等；reaction、resolve 都不改变交付状态。

`issue create --parent ID`、`issue edit ID --parent ID` 和 `issue edit ID --remove-parent` 提供可选父关系，拒绝不存在的父项、自引用和环。上下文展示父子引用，不递归复制需求，也不自动分解、审批或关闭子项。父子状态可在对象中读取；子 Issue 关闭本身不唤醒父成员。需要交接时，子成员回到约定的父 Issue 讨论回复结果。

CLI 在同一 SQLite immediate transaction 内通过执行身份检查当前 group、session、assignment 与 reset 屏障，修改正文/关系并写入语义事件。Context 失效后，原 turn 在通知与自然收尾期间保留当前责任范围内的写入；进入 teardown 后旧身份才失效。取消指派、运行封存等独立权限边界立即生效。被拒绝的写入不留下半个正文或事件。每个事件记录实际 writer group/turn，不能以统一 Agent-origin 标签忽略所有组。

## 当前 Context 与执行

当前正文、可见 comment 和直接关联图由单一数据库物化，沿原 renderer 生成完整 Context。Issue、PR 初次启动和 Context reset 都直接把 renderer 的正文交给原生会话，不追加 working memory、canonical 或 provider history 包装。隐藏与删除 comment 只留下身份和生命周期元数据，正文不进入模型输入；PR 仅展开 OPEN 的直接关联 Issue description，不展开其评论；关闭的关联 Issue 只保留引用。

description 的实际可见内容变化使对应旧输入失效，包括自身修改；同值写入与仅 HTML 注释变化不产生重建。
comment 的创建、编辑、隐藏、恢复、删除、hide 理由、resolve/unresolve，以及标题和关联关系变化均不产生 Invalidate。
对象状态照常保存，增量通知按实际成员和参与/订阅关系送达，排除执行操作的成员本人，而不是排除评论的历史作者或同模型的所有会话。
hide/resolve 立即改变 CLI/Console 和下次投影，不能据此宣称旧原生历史已经删除那些文字。
description 自编辑仍通知原会话后替换物理会话；只有旧工作 turn 未正常完成才自动续接。
上下文替换不能撤销已发生的 shell/Git 副作用。

评论在同一事务内保存，并按当前负责人、同一讨论的历史评论作者、当次有效 @ 与显式关注整个工作项的成员合并收件。同一动作对每人只排队一次并跳过作者；跨工作项只传来源与 comment ID 引用，通过 CLI 读取原讨论。创建、参与评论或被 @ 不会隐式关注整个工作项；显式退订持续生效，当次 @ 仍可送达该条。当前负责人承担本项通知责任。关联关系只提供导航与 Context 依赖，不自动订阅或广播。

评论中的 `@具体成员` 用于邀请或特别点名，识别可见 Markdown 文字。普通回复送达未显式退订的同一讨论参与者、当前负责人及显式关注成员；即使其负责的 Issue/PR 已关闭，原会话仍可按需恢复，工作项保持关闭。未知或已改派的成员不会让评论正文回滚，投递回执说明 queued、delivered 或 unreachable；旧成员不会转投新负责人。消息不回送作者本人。

只有 OPEN 关联 Issue 的有效 description 变化向 PR 发跨面 Invalidate，因为这是 PR 投影实际展开的外部正文。
关闭 Issue 的正文不进入 PR 投影，不沿这条链传播；普通讨论不因关联自动广播给 PR 成员。
关联增删和父子关系变化向受影响对象的负责人及显式关注者发送增量引用，同次动作对成员去重并排除操作者，不为了刷新引用重建会话。
休眠指派的 Invalidate 保留实际 recipient/member revision，但不独立唤醒；联系或 reopen 时只消费该指派已捕获的 description 变化，混批的新评论输入保留自身投递义务。

description 发生 Invalidate 时，runtime 先通过同一原会话完成重建前通知，再创建新物理 session 并派发输入；不只更新数据库 revision。等待旧会话结束期间，普通评论仍可通过当前运行 turn 的原生输入通道按引用投递；同一 worker 串行发送重建通知与普通输入，真正进入 teardown 后不再向旧会话发送。每次原生输入接受后只确认这次引用的事件；发送期间追加到同一批次的评论保持待投递，未接受的输入不标已送达。引用读取遵守当前 hide/delete/resolve 可见性和当前指派，送达仅表示原生输入已接受。重建后的输入从已绑定事件读取变更引用、写入成员和是否由当前成员写入，说明下方工作项快照在这些事件提交后读取；这只说明快照读取顺序和读取时的可见状态，不保证每条历史正文仍原样存在。未记录具体成员的事件明确标为未知。普通新增评论、状态评论与根进度提醒按 Wake 或引用读取，不因完整投影哈希变化而 reset。初次物化与真正 reset 都渲染当前 Context；普通 resume 保留此前实际发送的 context_revision，不以新的完整投影哈希判定必须换会话。reset 保留 group/worktree，旧 turn 在进入 teardown 后不再能控制写入。

已提交的 description 自编辑不依赖另一条外部消息才重建活动会话的 Context。物化事务读取旧 session 最后一条非重建通知 turn 的持久终态：`completed` 不产生 continuation，`interrupted`、`failed` 或 `unknown` 保留续接；没有旧 turn 也不造工作请求。terminal 先到和 reset 先到均进入同一通知与重建流程，独立新消息仍由原 wake batch 投递。terminal 结算不得抢先休眠仍需重建的 group。重启持有独占运行锁后可接管已完成原生 teardown 的 materializing reset；遗留的 interrupting reset 若没有已验证的通知与退出证明则标为 blocked，不能建立竞争写者。

每个 profile 的 Issue 与 PR driver 各自维护按物理 session 索引的活动集合；同类 Issue 或 PR 可以同时执行，不要求父 Agent 结束当前执行让位。恢复保留仍被活动集合持有的 session；一个会话 reset、失联或关闭不移除其它会话。close/merge 不授予额外执行轮次：负责人自己关闭只记录状态，其他人的关闭作为普通输入送达负责人；当前执行自然结束。旧归档的 finalizing 状态仍能恢复，但新关闭事件不再创建该阶段。

Issue 与 PR 保存成员协作所需的问题、方案、变更和决定；成员按实际需要在讨论中协调。runtime 不从讨论状态推断阶段、批准或任务完成，也不规定角色分工、阶段目录、评论数、工作项数量或原生子代理的使用方式。V&V 方法由调用方选择，Braid 只说明对象与交付操作。维护者仍需区分 Braid 工作项会话与 provider 原生会话树：后者不建立 Braid assignment。Pi adapter 关闭自己持有的 RPC stdin，等待 Pi 主进程退出，使用 Pi 正常 shutdown 路径。原生子代理的前后台执行、清理、进程与 lease 均由 Pi 及其扩展负责；Braid 不配置原生子代理停止命令、不检查内部停止收据，也不替其管理进程树。Codex adapter 管理其独立 app-server。

Unknown 保留原执行记录，不等于成功或历史不可恢复。确认旧执行停止后，优先恢复同一原生历史并核实会话身份和空闲状态；恢复后只追加一次事实性恢复输入，不盲重放结果未知的旧动作。临时恢复失败保留具体原因并延后重试；只有 adapter 确认原生身份或历史文件不存在才以明确理由新建。配置摘要变化本身不触发换会话；模型与系统指令在实际原生 resume 时采用当前接口支持的值，旧 home 保留，新的模板文件不自动覆盖旧 home。没有额外的时间、轮数或 token 启发式终止门槛。

## 合并、收敛与恢复

处理 PR 的 Agent 在本地 commit 并 push 到 origin 的 PR head ref 后，可调用 `pr ready ID` 清除 draft；`pr ready ID --undo` 恢复 draft。ready 从共享裸 origin 读取 head，不依赖调用者持有 PR 私人 clone，保存最近观察的 commit 并通知关联 Issue。拥有有效执行身份的工作项 Agent 可按当前需要调用 merge；Braid 不限定根 Issue #1 为唯一操作者。merge 读取该 PR 记录的 base/head 当前 origin commit，拒绝 draft、未发布的分支与无新提交的源分支；可选 `--match-head-commit SHA` 用于调用者确认自己看到的源头仍未变化。不带该选项时以执行事务读取的当前 head 为准。冲突报告 PR、源分支和目标分支，合并不发生。Agent 根据事实自行决定 fetch、整合、push 或关闭 PR。

合并对象先写入 origin 的 Git object database，精确 base/head ref、输入 commit 与结果保存为该 PR 的 prepared intent，随后验证源 head，并以 CAS 更新该 PR 的 base ref，最后记录 PR merged 状态和事件。重启依据 intent 记录的引用及 origin 实际引用恢复；Git 已更新而 SQLite 尚未收据时不生成第二次合并。即使目标随后快进到包含该 prepared merge 的提交，也沿冻结 intent 结算 PR 与声明的 Issue，保留当前目标引用；目标历史不包含该 merge 时拒绝结算。显式 merge 重试若仍需发布冻结 merge，`--match-head-commit` 必须匹配 intent 保存的 head；已发布 merge 的结算不再受后来 head 变化影响。其它 PR 可选择不同 base，各自只更新自己的目标引用。这个过程不检查或改动其它 Agent clone 的 HEAD、index 或工作文件。Agent 可通过 fetch 取得合并后的分支。冲突 PR 可以明确关闭放弃；prepared 的未知合并仍必须处置。

若调用 merge 时目标分支已包含当前 head，Braid 只在曾经观察到该 PR 的 head 不在当时目标分支中、且当前 head 仍包含这个观察到的提交时，将 PR 记录为已整合；它不再次写 Git ref。显式 head 可在创建时建立该证据；`pr ready` 即使对已非 draft 的 PR 也会重新观察已发布的 head。只保存创建时 base 不足以证明整合：源分支也可能只是随后同步了目标分支。返回和保存的 `merge_commit` 是本次判定时观察到的目标分支 tip，可能晚于真正引入 head 的提交。没有上述正证时，包括旧 PR 缺少观察记录的情况，Braid 只报告当前目标已含 head，不修改状态。这个判断仅在显式 merge 请求时发生，不周期同步外部 Git 变化。

PR 正文中可用 `Closes #N`、`Fixes #N`、`Resolves #N` 声明合并后关闭的本仓库 Issue，支持 close/closed、fix/fixed、resolve/resolved 形式和大小写变化。
只解析 Markdown 正文文字，忽略代码和 HTML 注释；不解析 commit message 或跨仓库引用。
`pr view` 的 `closing_issues` 展示当前适用目标，与普通 Issue 关联分开。
仅当 PR base 是裸 origin symbolic HEAD 指向的默认分支时生效，不因 delivery ref 配置自动推断默认分支。
准备合并时把适用目标保存到 merge intent；Git 发布成功后，Issue 关闭与 PR merged 状态在同一数据库事务结算。
外部已经整合 head 的成功确认路径遵循相同规则；崩溃恢复使用保存的目标，后续正文修改不能改变该次意图。
旧 prepared intent 没有声明记录时不追溯推断，已关闭 Issue 不重复通知；普通 PR close、冲突、head/CAS 不匹配或非默认分支合并不关闭 Issue。
子 PR 合入 develop 的关闭声明不随之后 develop→main 合并自动追溯，最终 PR 可明确列出所关闭的 Issue。

Issue close 只要求原因，不检查其它工作项、已合入 PR 或交付树；close/merge 不打断当前执行，已关闭工作项的既有会话完成收尾后休眠。并行到达的评论保留在既有 batch，收尾后需要时重新激活当前成员。根 Issue 开放且其成员连续空闲五分钟时，Braid 以自己的名字发评论“请检查当前工作进展。”；调用方可通过可选 `root_check_messages` 文本列表轮换提醒，省略或空列表保持默认文字，空白成员被拒绝。每次提醒按已提交的根检查活动数选择下一条；同一事务隐藏此前所有仍可见的根检查提醒，再写入新评论、活动和一次投递。旧提醒由 issue:1 上 Braid 系统作者及对应 `commented / root progress check` 创建活动共同识别，不能只凭作者或正文判断。隐藏只改变旧提醒单条的 lifecycle、原因、revision 与更新时间，并记录 Braid 的 hide 活动；保留原正文、回复和讨论解决边界，不触发额外通知。其它 Braid 状态评论与成员回复保持原状。事务任一步失败均回滚，不能先永久隐藏旧提醒却没有新提醒。重启接续、隐藏或删除评论不会重置轮换。提醒内容由调用方决定，Braid不内置工作方法。评论留在根 Issue 历史中，仅向当前根负责人投递，不唤醒其他关注者。已有输入、执行或恢复中不提醒。根开放且可继续执行时，local 等待后续检查，不因暂时静止而退出。根与所有 Issue 均关闭、所有 PR 均合并或关闭且没有未解决合并时，local 停止派发普通讨论输入；已经开始的执行、正在物化的会话与 reset continuation 自然收尾后才返回 quiescent。末轮可以更正状态或重开工作项，此时继续正常派发。边界后的普通通知保留在数据库，明确重开工作范围后可继续处理，不再延长本次执行；应用完成仍由调用方判断。启动恢复时同时核对对象范围与遗留执行，不能仅凭 CLOSED 跳过未完成执行。其它情况下，必要物化或恢复受阻返回 blocked。状态与工作树保留，可用相同请求恢复。

Braid 不因收敛而封存运行。每次退出时从当前 delivery ref 读取确切 commit，供调用方决定如何使用；失败时也尽可能记录该提交，但不以提交是否存在覆盖原始错误。旧版本已封存的状态仍保持只读且拒绝恢复。

## 输出与证据

`state/result.json` 含 schema_version=1、run_id、status、reason、root_issue、repository、delivery_ref、delivery_commit、objects_database、sessions_manifest。`root_issue` 给出 kind/id，并在能读取时给出当前 `state`；blocked/failed 也尽量报告该已知事实。status 为 quiescent/blocked/failed；quiescent 退出码为零，blocked 和 failed 非零。delivery_commit 是退出时当前 delivery ref 的确切提交，读取失败时为 null；它不表示应用已完成。物理会话关闭之后保存结果，进程非零退出保留原因与证据。

`state/sessions.json` 持续保存所有实际创建的物理会话，包括被替换与未知的会话。每项包括 session_id、provider（codex/pi/bub）、profile_id、member_login、effective_profile_digest、group_id、work_item_kind/id、assignment_generation、context_revision、worktree、status、native_home、native_session_path，以及 instructions_path、context_path 和 turns。每个 turn 包括 braid_turn_id、provider_turn_id、status、trigger_kind、input_path。Pi session_id 与 native_session_path 是原生 session 文件路径，native_session_id 是 JSONL header 的 UUID；根记录的 parent_native_session_id 为空。Codex session_id 是 thread ID；Bub session_id 是 ACP ID，native_session_id 是由确切 cwd/ID 派生的默认 tape 文件 stem，native_session_path 指向该文件。调用方根据这些身份归档原生 parent/child，而不是按文件时间猜测归属。

`physical/<id>/instructions.md`、context.md 和 `turns/<turn>.md` 是实际交给 provider 的输入；工作项正文没有第二份可编辑 Markdown 镜像。未创建会话的启动失败保留 physical 目录的失败证据，但不冒充物理会话加入 sessions 清单。已创建但 Context 物化失败的会话仍以 unknown 列入清单；若创建已确认但身份响应丢失，也保留 unknown 与空身份，由归档明确拒绝不完整的原生映射。status.json 是最新状态快照；result.json 记录本次 local 执行的终态与 Git ref 身份，不判断应用质量。

真实 Codex/Pi 上下文替换应结合对象、讨论、原生会话和执行状态验证。应用产物与任务效果由调用方自己的验收决定，不由 Braid 的工作项数量或状态推出。

## 遥测副本

遥测不参与调度、writer 验证、对象事务或交付判定。只有长生命周期 local 进程与显式宿主 export 命令持有 exporter；Agent 的短命对象 CLI 不启动 exporter，遥测命令在 Agent runtime 标记下拒绝执行。
一次执行具有独立 service.instance.id，Braid run_id 保持不变。跨异步 worker/reader 显式携带运行 trace；物理会话与 turn 以 provider identity 和 Braid turn ID 关联，不能将 Pi 文件路径当作数据库 session UUID。

证据从 SQLite 一致读事务及已落盘原生文件取得，正文不经过有损 Context 投影。
快照保留隐藏/解决评论的现存正文、删除墓碑、reaction、关联、指派、合并与实际输入；现有数据库不保存每次历史正文版本，遥测不补造被覆盖或删除的内容。
原生消息不等于最终模型完整请求，也不包含核心未公开的内部推理。

日志中的证据格式版本为 1，包含 run、记录种类与稳定内容摘要。
原始字节分成不超过 64 KiB 的片段，artifact 记录按序引用片段并保存完整大小及摘要，snapshot 记录本次选定 artifact 和完整性缺口。
同一源文件追加或改写产生新 artifact 版本，重建只使用选定快照，不把旧尾部混进新消息列表。
消息保留原生 id/parentId、toolCallId、压缩和分支事件；并发会话不按 collector 到达时间推断因果顺序。

blocked 和 failed 也可以拥有完整诊断证据；执行终态与证据完整性是两个字段。
根会话结束后补采一次，宿主完成子代理归档后以显式 manifest 补采完整清单。
每条证据正文有界，独立队列分批 flush；网络调用不在对象事务或 provider 锁内发生。
队列/网络失败后下一次采集重新发送源证据，消费者按内容身份去重；源材料仍是恢复权威，不增加新的持久消息队列。
使用方法和输出入口见[运行说明](../40-deployment/README.md)。


### 宿主离线恢复

`braid local REQUEST --offline-resume` 是宿主对来源执行环境已经停止的明确断言。
它仅用于已有运行；请求身份与材料仍须匹配，且仍取得该状态目录的排他锁。
Braid 撤销旧 CLI 身份，将来源 provider 标识记录为本次启动已停止的执行，然后沿原有输入重放与 Context 恢复路径继续。
停止断言不适用于本次新建或已恢复的执行，不扫描或管理 Pi 内部子代理。
`offline-resumes/` 记录宿主断言和受影响的旧 provider 标识；这不冒充旧模型已处理重建通知。
没有此断言的普通启动不把“没有本进程句柄”解释为“旧执行已停止”。

普通协作输入经既有 debounce 合并为 runnable 批次后，可通过原生 steer 进入仍在工作的成员，不必等待整段执行结束。
原生拒收时保留待投递事实；接收回执只表示进入原生队列，不代表采样、理解或已处理。
CLI文本将消息投递回执与评论正文分区，`delivered`展示为“会话已接受评论输入”，不将接收状态展示成成员的任务完成声明；JSON仍在`deliveries`中保留原状态和原因。
全范围终态及待执行的正文失效继续沿既有结束与 Context reset 边界处理，不用 steer 绕过这些边界。

`status.delivery_closed` 与派发、退出共用全部对象终态及合并状态判据。
根已关闭但仍有开放对象、且当前无可执行输入时，返回 blocked 并保留现场，不把静止解释为完成。
`queued_comment_deliveries` 和结果中的 `retained_input` 说明本轮未派发的评论数量及原始回执查询入口；全范围关闭后不会为了清空普通消息继续创建执行，重新打开范围后才可继续处理。

## CLI 完整正文更新

`--body` / `--body-file` 在编辑时替换完整正文；空内容仍是合法的显式清空。
正文构造与写入分开，避免 shell 进程替换失败却向 CLI 提供空内容。
先成功取得结构化正文，再提取 body 到可编辑文件；不要从含标题、负责人等展示字段的文本中裁剪正文。

```sh
braid issue view 1 --json body > /tmp/issue-1.json && python3 -c 'import json; from pathlib import Path; Path("/tmp/issue-1.md").write_text(json.loads(Path("/tmp/issue-1.json").read_text())["body"])'
```

在 `/tmp/issue-1.md` 完成编辑并确认保留所需内容后，单独执行写入及读回：

```sh
braid issue edit 1 --body-file /tmp/issue-1.md && braid issue view 1 --json body
```

PR 使用相同的 `pr view` / `pr edit` 形式；指定评论用 `comment view ID --json body` 取得正文，解码数组首项的 body 保存到文件后，再用 `comment edit ID --body-file FILE` 更新。

创建评论先保存同一次完整回包，再解析编号及补读；不要为取得 ID 再次创建，也不要对 JSON 先 `head`/`tail` 截行：

```sh
braid issue comment 1 --body-file note.md --json > /tmp/comment-created.json
python3 -c 'import json; from pathlib import Path; print(json.loads(Path("/tmp/comment-created.json").read_text())["id"])'
# 使用上一步输出的编号读取详情：braid comment view ID --json deliveries
```
不增加空正文禁令、内容长度阈值、写前确认或 shell 解析器。

`braid assignee list [--json]` 是本地扩展，对应 GitHub repository assignees API 的用途。目录返回每个可指派配方的下一位具体候选成员及职责，排除 root-only；读取无写入，不附加到上下文或固定指令。实际输入须使用当次仍可认领的候选名字。

Bub 的独立进程、指令插件、持久化首轮 Context、Deferred 忙时输入及 Unknown 取消边界见 [原生 ACP adapter](app-server.md#bub-原生-acp-adapter)。本地入口仍只组成一个 adapter 类型；不在本次接入中改变队列调度或增加跨 adapter 混用。
