# 本地 Context

当前完整对象由 SQLite 物化，再由 context 模块既有 renderer 投影。Issue Context 包含当前标题、正文、生命周期、直接关联 PR 引用和 comment；PR Context 先呈现 PR 自身正文、状态、分支和 comment，再在关联需求区只呈现 OPEN 的直接关联 Issue 的 description，不展开关联讨论。关闭的关联 Issue 仅保留关联引用。隐藏分支只保留自身隐藏且没有隐藏祖先的根编号，不展示下级回复或正文；中间节点 hide 只影响该分支。同一完整隐藏理由的根编号在讨论末尾聚合为一行 `Comments 759,756,892 hidden (reason)`，没有理由的根另行聚合，理由不截短。删除评论保留标记，已解决讨论只留根标记；若又有新回复，新内容继续可见，但仍遵守 hide。隐藏/已解决标记不逐条附加读取指令。完整身份、作者、生命周期与隐藏来源仍由普通对象读取及显式追溯提供。

显示身份使用 Issue/PR/Comment 编号，不重复单仓库身份或 local 前缀。短元数据合入标题，不显示创建/更新时间；时间和内部关系仍保留在底层记录及结构化诊断中。description 与 comment 正文置于长度足以包住原文反引号的围栏中，回复按真实父子关系组织标题层级。

作者可在 description 和 comment 中用 `<details><summary>标题</summary>正文</details>` 保留按需读取的材料。模型投影只保留完整容器的首个直接 summary 内容；多个容器和嵌套容器按原文顺序处理，summary 中的 Markdown 格式保持。解析以 comrak 判定的 HTML 范围为入口，跳过 Markdown 代码及 HTML 注释、script/pre 等字面区；只接受显式平衡结构，不替作者修复缺失或交叉标签。无法确认的容器保持原文。SQLite 正文、`issue/pr view --json body`、`view --comments` 和 `comment view` 仍给出原文；`braid context` 展示模型投影。折叠区内的有效 description 修改仍触发重建，不能用折叠后的文字替代 description 变化比较。

Context 是工作数据。角色、运行授权和 CLI 协议通过独立 instructions 提供，comment 不因来源或 mention 自动成为控制指令。旧聊天、过时正文与工作区私有笔记不会被拼回替换 Context。

实际选中档位的对象投影哈希是 context_revision；重建时附加的事件来源说明不改变该哈希。
首次物化和真正 reset 才保存并发送新的 context.md；resume 保留旧原生历史及其实际 context_revision，不将未发送的新投影记为已经送达。
日常对象修改中，只有 description 的有效可见内容变化发出 Invalidate，包括自身修改；同值写入和仅 HTML 注释变化不触发重建。
关联传播只覆盖 PR 实际展开的 OPEN Issue description，标题、评论和关联关系本身均不走这条路径。

comment 的创建、编辑、hide/unhide/delete、resolve/unresolve 和 hide 理由变化按实际参与者及订阅关系增量通知，不向操作者回送自己的操作，也不替换原生会话。
标题及关系更新同样通过增量引用和 CLI 读取取得当前状态。
隐藏计算沿完整祖先链，精准单条读取也不能绕过；`minimized` 表达自身隐藏，`hidden_by` 与 `hidden_by_reason` 指向最近隐藏祖先。普通 renderer 对两者均消除正文；显式追溯可以读取保留的隐藏正文，不能恢复删除正文或改变普通投影。隐藏和折叠立即影响对象读取与后续投影，但不会从已运行会话的历史中擦除旧文字。
休眠成员的 description 变化按其具体指派与 revision 留存，不仅为刷新上下文而唤醒；真正收到联系或重新打开时才处理。
只有确实待应用的 description 变化才令恢复改为新建，不因完整对象哈希变化丢弃历史。

配置摘要变化本身不是历史失效；原生恢复时采用接口支持的当前模型和系统指令，保留旧 native home 与原生历史。
启动模板文件并不自动覆盖已有 home；其更新在真正创建新 home 时采用。
执行结果 unknown 与历史丢失分开：先确认旧执行已停止，再恢复可用的原生历史，保留原执行 unknown 并给出事实性恢复输入，不盲重放先前动作。
临时连接、启动或就绪超时保持可重试的具体错误；只有已确认原生身份或历史文件不存在才允许以明确理由新建。
新负责人拥有新的会话；这些生命周期操作不改变 description-only 的日常重建规则。

当前 SQLite 对象已经是权威，因此不再把 materialize 的旧快照反写到关联表或维护另一份可编辑 Markdown 镜像。对象和事件写入边界、跨面规则、会话清单与验收范围见 [本地运行契约](local.md)。

普通事件消息区分首次指派、后续输入和真实中断后的续接，短列工作项及具体变化；后续输入由负责人判断是否需要行动，不重复要求读取全部评论，也不附加正文读取命令。事件保留变化事实及必要关联，缺失正文、被折叠或截短的内容及后续真实变化仍按需从 CLI 取得。评论通知先定位单条正文，需要背景时再按 CLI 展开 thread。重建预告保留上下文将重建这一必要语义及变更作者、自编辑事实；新会话来源保留当前可见快照语义，不替负责人判断工作是否完成。首次上下文不附加额外 Braid working-memory 前缀，工作资料边界由 instructions 说明。消息精简不改变投递对象、事件顺序或重建时机。

模型自动重建使用分档投影：完整可见讨论、评论标题索引、引用与截短正文。按统一估算 token 数逐档选择严格小于 `context_window_tokens` 的 20% 的内容，同时保留原字节硬上限。估算并非模型精确 tokenizer；I11 adapter 从原生模型配置的 contextWindow 传入窗口，旧配置缺失时使用明确的 128000-token 兼容值。引用档先完成正文折叠，再截短投影，避免截掉闭合标签后暴露隐藏正文；截短结果直接渲染，不再次解析可能已不完整的代码标记。降档只改变投影，不写回对象，也不把省略的讨论自动标为 hidden/resolved。原始内容仍由 CLI 完整读取。运行日志记录档位、估算 token 与 bytes，CLI `context ... --window-tokens N` 可查看预算下的实际输出。

可指派目录不进入 Context 或固定 instructions。`braid assignee list [--json]` 按需返回可用于 assign 的名称与职责，属于对 GitHub repository assignees 查询的本地命令入口，并非 gh 的同名命令。根检查指引可要求负责人整理相关讨论；完成与失效的语义判断由 Agent 持有。
