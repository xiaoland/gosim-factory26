# Context 模板实施记录

## Context renderer 与直接评论读取

`sources/braid/src/context.rs` 已按 [review.md](review.md) 的获批范围简化。Issue/PR 标题合并编号、标题、状态与当前负责人；PR 在自身内容之后才以降层标题完整展示关联 Issue，包括其正文和评论。关联引用只写 Issue/PR 编号，不重复 `local/run` 或仓库身份。PR head→base 放在一行，去掉展示用的 `refs/heads/` 前缀。label、milestone、project、review/review thread、无来源的 issue type/阻塞/重复关系不再进入本地 Context；底层快照结构和数据库未改。关闭原因、父子关系、关联 PR/Issue 与评论正文仍保留。

Description 与评论正文使用动态长度的反引号围栏：围栏总比正文内最长连续反引号更长，最短三个，不靠删改正文避开围栏。Context 继续过滤 HTML 注释；CLI 直接读取评论可调用同一树渲染器并保留原始可见正文。`pub(crate) render_comments(..., heading_level, filter_html)` 和 `pub(crate) fenced_body(...)` 是两处共用入口，避免 CLI 另维护回复层级和围栏规则。

评论按真实 `reply_to` 形成父子树，兄弟按创建顺序；深度超过 Markdown 六级标题后改用缩进列表。完整树已有层级，不重复写 `reply to #parent`；直接读取单条评论且父评论不在切片中时，才在标题保留该父评论导航。深层列表的正文围栏、Read 入口和 Reactions 都缩进到所在项之下。hidden 保留作者、理由和 `comment view ID --include-hidden`，deleted 保留身份且不显示已清空正文；resolved 折叠历史给 `comment view ID`，其后的可见回复仍按自身状态展示。author 缺失不伪造 `ghost`。渲染层不显示 createdAt/updatedAt；时间仍在底层数据/结构化读取中。

验证仅限编译和归档数据库副本的实际只读调用。`cargo build -q` 成功。在临时复制的 GitHub I10 snapshot-02 数据库上，`braid --state TEMP context pr 14` 首个对象标题是 `# PR 14 ...`，后续 `## Associated Issues` 下才有 `### Issue 1 ...`；多层回复 #7 → #8 → #13 → #15 依次为六级标题及逐层缩进列表，树内不再重复父编号。深层 resolved 评论 #104/#109 的 Read 入口缩进在对应列表项内。已解决评论 #2 保留 `Read: braid comment view 2`，隐藏评论 #3 保留理由和 `--include-hidden`，没有吞掉后续评论。`braid --state TEMP comment view 8` 单条读取仍显示 `reply to #7` 及动态围栏。重新生成的完整 CLI 输出存于 [github-pr14-after-cli.txt](evidence/github-pr14-after-cli.txt)；它包含 `context` 命令额外的可指派成员目录前缀，不能与旧 Context 文件按字节直接当作 token 节省对比。

未运行测试或模拟探针，未部署、提交或恢复 I10。格式会改变新 Context 的 revision 哈希；实际 Agent 阅读与后续运行效果仍待获授权的 I11 运行观察。

## 事件、首条消息与 CLI

`group/provider.rs` 的普通消息现在只给“请处理 Issue/PR #N”与具体更新；去掉重复仓库身份和强制读取全部评论的尾句。`objects.rs` 的评论引用提供工作项、评论编号、可取得的作者和精确单条读取命令，编辑通知保留实际动作。投递对象和 thread 订阅规则不变。

旧会话预告简化为本次工作结束后重建，并保存尚未交接的进展；新会话来源保留实际作者、自编辑标记及更新后可见内容的说明。`dispatch.rs` 去掉首次 Context 的 working-memory 包裹文案；工作资料与角色指令的边界只在共用 instruction 说明一次。根定期提醒已核对，本轮保持原样。

CLI 的 `print_comments` 复用 Context 回复树；`print_item` 将标题、状态、草稿与 assignee 合并到标题，description 使用同一动态围栏。CLI JSON 与执行诊断仍保留结构化信息，未修改数据库时间或事件/重建时机。合并事实与观测已包含等事件保留原语义，不改写成笼统“已合并”。

上述主线改动已包含在最终成功的 cargo build 中。实际输出证明排版及读取路径；没有测量 token 收益，也不据此宣称模型协作效果已改善。
