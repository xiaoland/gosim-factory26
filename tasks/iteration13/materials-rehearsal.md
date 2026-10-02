# Braid 材料投影与提醒替换预演

2026-09-30。只读实施前预演，依据 [修复方案第四组](repair-design.md)及[上下文核心实施](context-implementation.md)。本页是最小 LLD 与反馈安排，不是源码开工授权；未修改 Braid 源码、运行对象、冻结 I12，未运行测试或模型。

## 折叠放在投影边界

当前 `sources/braid/src/context.rs` 的 `render_issue_at`、`render_pull_request`、`render_comment(filter_html=true)` 仅过滤 HTML 注释。三处分别覆盖 Issue description（含 PR 展开的 OPEN 关联 Issue）、PR description、当前讨论。模型入口汇合到 `render_budgeted`：`group/issue_agent.rs` 首次物化、`group/pr_agent.rs` 首次 PR 物化、`group/dispatch.rs` 真正新建与 reset；正常 resume 不重新发送投影。

新增一个投影正文 helper，组合现有 HTML 注释过滤与 details 折叠，以上三处采用。不要扩大 `filter_html_comments` 的语义：它还被 `objects.rs::edit` 的 description 变化比较、`edit_comment` 的通知比较、`closing_references` 的 Closes 提取共用。若直接改变该函数，折叠正文内的有效修改会被当作无变化，Closes 可能被删除，超出本批范围。隐藏区修改仍按现有 description 变化规则触发重建，生成投影仍只显示 summary。

`render_budgeted` 保持 Full → CommentIndex → References 的选择顺序和严格小于窗口 20% 的估算规则。**References 必须先折叠再截短**：当前 `reference_projection` 先截原文，若截掉 `</details>`，后续 renderer 无法识别完整容器，可能泄漏隐藏正文或浪费预算。最少改法是该函数截短 description 前调用同一投影 helper；实施时进一步收敛为：References renderer不再重复解析已投影且截短的正文。截短可能破坏代码标记，单靠helper对完整正文幂等不足以保证二次解析正确。CommentIndex 已将评论 body 设为 None，保持现状。

`cli/mod.rs::Command::Context` 调用同一 renderer，因而 `braid context ...` 显示折叠投影；`issue/pr view --json body`、`comment view ID` 及 `view --comments` 保持完整原文。CLI 文本讨论通过 `render_comments(..., false)`，该分支不可折叠。原始 SQLite snapshot 不改写；同一内容的 CLI 原文仍可保存后完整编辑。ReviewSnapshot、ReviewThreadSnapshot 当前没有进入 renderer，本批不用补 review 支持；close reason、标题与关系不是 description/comment 折叠目标。

## 使用 comrak，但不能把 HTML block 当成 details 树

现有依赖为 comrak 0.54；复用 `Arena`、`parse_document(Options::default())`、`line_offsets`、`source_range`。默认 sourcepos 使用字节列，适合现有 UTF-8 原文切片。comrak 的 HtmlInline/HtmlBlock 是原始 HTML literal，**没有 details/summary 的父子节点**。HtmlBlock 的起止按 CommonMark HTML 块规则，通常由空行结束，一个节点可能含多个标签；带空行的 details 则跨多个 HTML 和 Markdown 节点。不能仅对一个 HtmlBlock 做删除，也不能只匹配第一个 `</details>`。

最小算法是在 comrak 标识的 HTML literal 范围内提取真实标签位置，按原文位置排序，使用 details 栈配对，再生成不重叠的原文替换范围。标签识别限定 details/summary 的开闭标签，大小写不敏感，接受正常空白及属性；跳过带引号属性中的 `>`、HTML 注释、原始 script/style/pre 等字面区域，不把属性值里的 `<details>` 当作标签。不添加 HTML DOM 框架或新依赖。普通 Markdown Code/CodeBlock 不提供标签候选，因此行内代码、围栏代码与缩进代码中的示例保持原样；HTML block 本身的字面内容遵守 comrak 判定，不能声称其中反引号自动具有 Markdown code 语义。

| 输入边界 | 投影行为 |
| --- | --- |
| 同一正文多个独立 details | 每个完整容器替换为自己的 summary 内容，保留容器外全部正文及顺序。 |
| 跨空行、Markdown 段落的 details | 按原文标签区间配对，正文所在 AST 节点类型不限制其隐藏范围。 |
| 嵌套 details | 外层折叠后只留下外层直接 summary；外层隐藏区中的内层 summary 不泄漏。若 summary 自身含完整 details，对保留内容再执行相同折叠。 |
| summary 格式与中文 | 保留 summary 内原文及非 details 格式，不重新序列化整篇 Markdown。 |
| 代码中的标签示例 | comrak Code/CodeBlock 原样保留；不参与栈深度或关闭外层容器。 |
| 缺失 summary、未闭合或错误交叉嵌套 | 不折叠无法确认的容器，保留原文；不得让一个坏标签吞掉后续正常正文。已确认的独立容器仍可折叠。 |

只对完整、可确认且有直接 summary 的容器折叠；summary 出现多次时按标准容器的首个直接 summary 取标题。替换后用换行保持相邻段落边界，避免两个 summary 或外部文字粘连。不处理 HTML 修复、自动补标签或浏览器完整 DOM 容错。本算法仍有真实解析边界，应在 `context.rs` 靠近 helper 说明，不能用裸 regex 的“匹配到了”代替这些边界。

## 根提醒的可靠归属与事务

`objects.rs::root_idle_tick` 是唯一根进展提醒生产者；`local.rs` 循环在忙闲两条路径均调用它。当前 Immediate 事务检查根 OPEN、pending/executable 与连续空闲 5 分钟，然后按 `local_activity` 中 Braid 的 `commented / root progress check` 已提交数量选下一条消息，创建根评论、记录 `root_check_comment`、创建活动，再通过 `deliver_comment_to` 只向当前根负责人发送一次事件。

`system_author='Braid'` **不足以识别根提醒**：`store/mod.rs::enqueue_assignment_operational_status` 也生产 Braid 评论，活动 detail 为 `operational status`。仅隐藏最新 `root_check_comment` 也不足以清理已经积累的可见提醒，或被重新 unhide 的旧提醒。无需 schema 或新身份字段，使用已有不可变创建活动作来源凭据：目标 `issue:1`、comment 的 `system_author='Braid'`、`lifecycle='visible'`，且存在同对象、同 source_comment、`actor_login='Braid' AND action='commented' AND detail='root progress check'` 的活动。普通用户/Agent 创建评论没有 system_author；普通活动不具备该内部 detail。不要按正文、公开作者显示名或 thread_root 推断提醒身份。

推荐在同一 `root_idle_tick` Immediate 事务内，保持检查和轮换计数不变，选出此前所有符合来源条件的可见提醒，将这些**单条评论**置为 hidden，记录固定的替代理由、revision+1 和 updated_at；保留 body、reply_to、thread_root 与 resolved_through。逐条记录 Braid hide 活动，便于 timeline 找到真实作用范围，但不为这些 hide 创建事件。随后创建新提醒、更新 latest ID、插入原 `root progress check` 活动、沿用一次 `deliver_comment_to(..., "created")`，最后 commit。也可先创建再隐藏，但必须排除新 ID；先处理旧条目更简单。

不得调用现有 `hide_comments` / `change_comment`：它们自开事务且逐条 `discussion_changed`，会额外通知关注者、参与者并产生整理唤醒。不得调用 resolve：其讨论前缀语义会折叠用户/Agent 的回复。隐藏根评论后 `render_comment` 只省略该节点正文，树遍历仍展示回复；CLI 精确读取隐藏评论仍能取得原文。

对象替换、活动、根 reminder ID、deliveries 和 events 都在同一事务中。投递或提交失败保留具体错误并回滚，不能在无新提醒时先永久隐藏旧提醒。事件提交后调度器才能看到，不会观察到新通知配旧对象状态。这里只新增原提醒的一次 Wake/Mention，不新增 Invalidate，不扩大收件范围，也不清理旧历史输入：正常 resume 保留原生历史，不能宣称旧提醒已经从运行会话的历史中擦除。

`variants/pi-braid-i12/run.py::ROOT_CHECK_MESSAGES` 现有两条轮换就是隔次 packet 提醒；Braid 只使用 `sent % messages.len()`。隐藏计数不改变 `commented / root progress check` 数，root_idle_since 的复位、已有输入停止计时及连续空闲 5 分钟保持不变。不改冻结 variant 或消息文案。

## 最小实施与不可省略反馈

源码只需 `context.rs` 与 `objects.rs`，文档只更新已有 `docs/20-product-tdd/context.md` 的作者折叠、CLI 原文边界和 `local.md` 的根提醒替换规则；不新增框架、迁移、variant 配置或测试入口。顺序为投影 helper及截短顺序 → 精确来源筛选与事务内隐藏 → 权威文档 → 编译及实际操作反馈。

实施后可按已授权范围执行 cargo check/build、diff 检查及读取既有归档，但本次预演未执行。折叠的独立反馈应来自实际 binary 的 `braid context ...` 对比 `issue/pr view --json body` / `comment view --json body`，覆盖同条多容器、嵌套、代码、中文及 References 降档，确认原文往返无损和正文不会因截短泄漏。仅源码阅读或编译不能证明投影正确。

提醒必须在另获准的独立真实运行/操作环境观察至少两次自然到期：此前多个根提醒被隐藏、新提醒唯一可见、用户/Agent 回复仍可见、operational status 不被误隐藏、timeline 的来源和 hide 范围可查、单次原提醒事件和 receipt 无多余清理通知；同时观察重启或隐藏后轮换继续且 packet 隔次出现。不改写 I12 库、不缩短 5 分钟、不用 mock/probe 替代反馈。若尚无该运行授权，应明确保留为未验，不能报告模型行为或实际投递已通过。
