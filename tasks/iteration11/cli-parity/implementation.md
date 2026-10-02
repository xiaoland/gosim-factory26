# I11 CLI-01～05 实施记录

本轮只修改 Braid 本地 CLI、对象存储调用和 Braid 自有帮助/文档；未部署 I10、未提交、未执行测试或写入探针。比较依据见 [comparison.md](comparison.md)，各 CLI 的独立取证见 [braid.md](braid.md) 与 [github.md](github.md)。CLI-06 的 PR 创建方式和 CLI-07 的独立成员指派边界保持原状。

| 项目 | 已实施行为与边界 |
| --- | --- |
| CLI-01 关闭语义 | Issue close 可裸用；`--reason` 限定为 `completed`、`not planned`、`duplicate`，自由解释写 `--comment`。PR close 不再要求/接受 reason；close/reopen 均可附带 `--comment`。评论与状态变更在同一 SQLite 事务内；已是目标状态时输出 `unchanged` 且不新增评论。旧库中自由文本状态原因不改写、不冒充枚举。merged PR 的 close/reopen 错误改为准确说明两者均不允许。 |
| CLI-02 列表 | Issue/PR list 默认仅 open、编号倒序、30 条；`-s/--state`、`-L/--limit`、`-a/--assignee` 可筛选，PR 另有 `-B/--base`、`-H/--head`。PR `closed` 包含 CLOSED 与 MERGED；`merged` 仅 MERGED。assignee 是当前具体成员名，不接受 `@me` 或多个负责人。完整历史需显式 `--state all --limit N`。 |
| CLI-03 JSON | list/view 保留旧 `id`、`reason`、`head_ref`、`base_ref`、`draft` 等键，并新增 `number`、`stateReason`、`headRefName`、`baseRefName`、`isDraft`；PR view 还可选 `headRefOid`、`baseRefOid`。创建回执保留 `id` 并新增同值 `number`；Agent `status --json` 也带 `number`。裸 `--json` 继续可用；没有暴露内部 UUID。 |
| CLI-04 高频参数与评论 | create 支持 `-a`，view 支持 `-c`，list 支持 `-s/-L/-a`，PR list 支持 `-B/-H`。`issue/pr comment ID --edit-last` 与 `--delete-last --yes` 只定位当前 Braid 成员在该工作项最后一条未隐藏、未删除评论；resolved 折叠历史仍计入，宿主 `--external` 没有当前成员身份不能用。无目标时报错，不隐式新建；按评论 ID 的精确命令保留。 |
| CLI-05 合并 | `pr merge ID --merge` 使用现有即时本地 merge；裸 `pr merge ID` 保持兼容。`--squash`、`--rebase`、`--auto`、`--disable-auto` 会明确报未实现，不静默当作 merge。原有 `--match-head-commit` 精确匹配与 JSON 回执保留。 |

运行目录原先也是全局 `--state`；它与新增 list `--state` 在 Clap 中不能共用一个长参数（实际解析会 panic）。现把宿主运行目录限定在根命令之前：`braid --state PATH issue list --state all`。Agent 运行环境仍自动绑定 state，不需该参数。Braid 的 telemetry export 示例和本地契约已同步；其他宿主若曾将运行目录写在子命令之后，须改为根命令前。帮助明确显示列表状态枚举，避免把两个 `--state` 混为一谈。

源码入口为 `sources/braid/src/cli/mod.rs` 与 `sources/braid/src/objects.rs`；权威用法已更新 `sources/braid/docs/20-product-tdd/local.md`，宿主 export 示例更新 `sources/braid/docs/40-deployment/README.md`，原生 Agent 指引更新 `sources/braid/src/group/provider.rs`。没有更改运行中 I10 的状态、对象或 Git 引用。

验证：最终 `cargo build -q` 成功。最终二进制的只读 help 显示 `issue list -s/--state <STATE>` 默认 open、`-L/--limit` 默认 30，`issue close --reason` 枚举及 `--comment`，`issue comment --edit-last/--delete-last/--yes`，`pr merge --merge` 与明确标记未实现的其它策略。将已归档的 `tasks/iteration11/run-audit/sheet/evidence/braid.sqlite3` **复制到临时目录**后，仅对副本运行只读 CLI：

```text
braid --state TEMP issue list --limit 2 --json number,id,title,state
→ #7 OPEN、#6 OPEN；两者 number 与旧 id 相同，按编号倒序。

braid --state TEMP pr list --state closed --limit 2 --json number,headRefName,baseRefName,isDraft,state
→ #9 MERGED、#8 MERGED；head/base 为短分支名，isDraft=false。

braid --state TEMP issue view 7 --json number,id,stateReason
→ {"id":7,"number":7,"stateReason":null}
```

这证明当前构建的解析和这些读取路径；close/reopen、评论 last 操作、创建及 merge 的实际写入效果留待后续授权的真实 I11 运行观察，本轮没有用测试或模拟状态声称端到端覆盖。

主线补齐宿主消费者：scripts/braid_runtime.py的telemetry export运行目录参数已前移到根命令；Python语法核对通过，该形式也兼容旧全局state解析。运行中冻结包不改。
