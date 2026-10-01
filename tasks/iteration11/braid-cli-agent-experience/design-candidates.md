# 有界接口改进候选

2026-09-30。以下命令/JSON **全是未实施草案**，用于审查契约，不表示当前支持；示例 ID 沿用案例作说明，未在真实工作项执行。优先级按误操作/恢复影响与现有证据排序，尚未估算工期。各候选可独立取舍，不要求造第二套 CLI、MCP 服务或通用工作流引擎。

## D1 / P1：让写入回执回答“这次真正改变了什么”

**现状 before**

```sh
braid comment hide 339 --reason '过期提醒'   # 成功可无输出
braid issue edit 1 --body-file current.md   # 打印整篇正文，不能明确区分 no-op
braid pr merge 23 --match-head-commit <full-sha>
# {"merge_commit":"..."} 不能区分新合并、既成结果与已被目标包含
```

**候选 after**：给目前缺 JSON 的写命令增加 `--json`；沿用已有成功字段，补简短 mutation receipt。无需一开始把所有命令强制包进新 envelope。

```sh
braid comment hide 339 --reason '过期提醒' --json
```

```json
{
  "operation": "comment.hide",
  "target": {"kind": "comment", "id": 339, "work_item": {"kind": "issue", "number": 1}},
  "changed": true,
  "before": {"visibility": "visible"},
  "after": {"visibility": "hidden", "reason": "过期提醒"},
  "effects": {"context_invalidations_recorded": [{"kind": "issue", "number": 1}]}
}
```

这只报告本次事务登记的失效，不能写 `agent_woken:true` 预测异步结果。若没有活 assignment、事件被归为 Noop，数组为空；同状态/原因的重试 `changed:false`。回执不重放整条正文、全部收件人或内部 session UUID。

```sh
braid issue close 1 --reason completed --comment '验收证据见 PR #23' --json
```

```json
{"number":1,"state":"CLOSED","changed":true,"stateReason":"completed","comment_id":349}
```

重复 close 返回 `changed:false, comment_id:null`；必须明确“本次没有发表传入的新评论”，以免 Agent 误以为关闭说明已更新。

```json
{
  "merge_commit": "<full-sha>",
  "outcome": "merged",
  "changed": true,
  "head_commit": "<reviewed-sha>",
  "base_ref": "refs/heads/main",
  "ref_updated": true,
  "closed_issues": [1]
}
```

merge 其它 outcome：`already_merged`（返回已保存结果，`changed:false`）、`integration_recorded`（当前 head 已在目标历史，登记整合，`ref_updated:false`）。`closed_issues` 只列本次确实从 OPEN 转 CLOSED 的项；另有关闭候选时不混入这一数组。不要为保持统一而削弱已有 head guard、intent/ref 恢复。

**错误草案**：仅对已经识别 `--json` 的语义操作，stdout 留空，stderr 输出一个结构化错误对象，进程非零；人类模式保留原具体原因。首版允许 clap 参数解析错误仍走既有文字+退出码，不承诺所有错误都已机器化。

```json
{
  "error": {
    "code": "REPLY_TARGET_MISMATCH",
    "message": "Comment #348 belongs to PR #23; this command targets Issue #1.",
    "requested": {"kind":"issue","number":1},
    "actual": {"kind":"pr","number":23},
    "retry": "change_request",
    "next": ["braid pr comment 23 --reply-to 348 --body-file reply.md"]
  },
  "effects": {"comment_created": false}
}
```

仅在能证明时给 `comment_created:false`；merge 冲突/结果未知不复用笼统 `no_side_effects:true`。保留原错误链，而非只剩错误分类。下一步建议只给可定位目标，不替用户猜新的正文或绕过失败前提。

**兼容与风险**：保留旧字段和默认文本；新增 JSON 是 opt-in。现有 ready/merge 默认就是 JSON，添加字段前核对严格消费者；确有拒绝未知字段者则先只在显式 `--json` 扩展。结果必须由写事务内算出，不能提交后重读当前状态冒充“本次效果”（会被并发改写污染）。这是返回契约调整，宜先覆盖 hide/edit/resolve/close/merge，不做全仓错误框架重构。

## D2 / P1：resolve 可预览、可固定边界，恢复语义对称

**before**

```sh
braid comment resolve 318
braid comment unresolve 318
```

首条取整 thread 最新 ID 为 cutoff；第二条清除整条 cutoff。当前文字回执已经改善，剩余问题是读完到落笔间新增回复、重试推进 cutoff，以及误以为 unresolve 是局部 undo。

**after**

```sh
braid comment resolve 318 --preview --json
```

```json
{
  "preview": true,
  "threads": [{
    "selected_comments": [318],
    "thread_root": 308,
    "previous_resolved_through": null,
    "proposed_resolved_through": 324,
    "affected_record_count": 7,
    "affected_visible_count": 7
  }]
}
```

数字是草案说明值，不是历史当时计数。preview 必须严格只读，无事件、无新分支、无 reservation；不能照搬 gh `pr create --dry-run` 仍可能 push 的习惯。

```sh
braid comment resolve 318 --through 324 --json
```

固定在已经审过的 thread prefix；新到的325仍可见。校验 `through` 在所选 thread 中、不倒退已有 cutoff；若已有 cutoff 超过324，应返回明确冲突并提示查看，不能静默降低/扩大。多 root 使用 `--through` 易混淆，首版只允许一个 root；原有多 ID 自动最新语义保留兼容并明确警示。回执复用现有 `thread_root/resolved_through/affected_comments/changed`，补 previous cutoff；计数字段必须区分记录数和可见正文数。

`unresolve ID [ID...] --json` 可增加批量对称性，整批校验后事务提交；帮助写明“清除整串折叠，不是精确撤销上次操作”。无需新增子树解决机制。是否另加恢复旧 cutoff 的能力，等真实需求再定。

**兼容与风险**：新 flags/additive；原命令的语义不变。固定 cutoff 是业务语义的小扩展，必须先把新回复、hidden/deleted、多个输入同根、已存在更大 cutoff 的行为写清。preview 回包本身不是锁；安全性来自 apply 的明确边界与事务校验。不能用看似安全的预览替代并发约束。

## D3 / P1：读结果有边界，按字段取数据，而非先展开再截断

**before**

```sh
braid comment view 337 --thread | head -60
braid issue list --state all --limit 100 --json number,title,state
braid issue view 1 --timeline --json body
```

首条可能截掉末端目标；列表裸数组不说明超过 limit 是否还有；最后一条当前静默忽略 body 字段要求。`view --json body` 输出虽窄，后端仍先读讨论/关联详情。

**after**：保留现有单条读取优先；新增有界 thread 和 list 页模式，直接复用 timeline 的 cursor/has_more 思路。不要改变旧列表 JSON 顶层数组。

```sh
braid comment view 337 --json                         # 当前就能单条直达
braid comment view 337 --thread --after 330 --limit 20 --json
braid issue list --state all --page --limit 30 --json number,title,state
```

```json
{
  "items": [{"number":23,"title":"Integration","state":"OPEN"}],
  "page": {"order":"number_desc","limit":30,"has_more":true,"next_before":12},
  "filter": {"state":"all"}
}
```

示例 items 为缩略演示。下一页用 `--before 12`（仅 `<12`），沿既有编号倒序续读；后续新建项要在下一次从头查询时读取，状态/负责人在分页期间也可能变化，不能承诺事务级集合快照。thread 按 comment ID 升序，root/cutoff 元数据每页给一次；正文省略与 deleted 分开标记 `body_status`，`has_more` 只指未读页，不指 hidden 历史。

最小立即改法：`--timeline` 与 `--comments` 冲突时报参数错误；timeline 的 `--json FIELD` 要么真正选择受支持 timeline 字段，要么拒绝并列出字段，不能静默接受。普通 view 先校验字段再分派查询；仅 body/state 不加载 comments、每条 reaction 或 Git refs。单条 comment 直接按 ID 取，thread 才取集合。

**兼容与风险**：旧 list 数组保留；页模式新增外壳。不要默认把完整读取硬截为摘要，避免破坏 `body-file` round-trip。明确缺省30/open以及 PR closed 包含 merged；空页不能冒充“没有任何历史”。优化后端读取减少 I/O 的方向可由静态路径证明，实际延迟/token节省要等未来运行，不能在本报告给数字。优先实现参数不静默降级与字段按需读取；list 尚无真实漏页事故，最小版先增加截断提示，完整页模式属 P2 可选项。

## D4 / P2：给整体正文替换提供可选过期检测

**before**

```sh
braid issue view 9 --json body
# Agent 在本地修改全文；另一位作者可能已经更新同一正文
braid issue edit 9 --body-file design.md
```

**after**：先只覆盖正文，不引入通用 JSON Patch 或服务器语义 diff。

```sh
braid issue view 9 --json body,bodySha256
braid issue edit 9 --body-file design.md --if-body-sha256 <hash-from-read> --json
```

```json
{"error":{"code":"BODY_CHANGED","message":"Issue #9 body changed since the supplied snapshot.","expected_sha256":"<old>","current_sha256":"<new>","retry":"read_then_reapply","next":["braid issue view 9 --json body,bodySha256"]},"effects":{"body_written":false}}
```

hash 定义为原始存储 body 的 UTF-8 bytes，包含 HTML 注释/换行；同事务校验，再写入。不能用过滤后的可见文本 hash 接受旧 raw body 覆盖。它只保护 body，title/assignee/parent 各自既有前提不因此受保护。成功回执给旧/新 hash 与 changed；无须回传全文，Agent 保留本地文件即可做内容复核。

**兼容与风险**：新 guard opt-in，裸 edit 保留最后写入行为。当前文档宣称隐藏内部 revision，但 Item 的 `revision` 实际仍在 JSON 中（见 interface-audit）；其公开契约待澄清。本方案把 guard 限定为 body 内容摘要，不依赖未明确的 revision 含义，也不泄露 session/assignment revision。hash 不保存旧版，也不证明正文内容正确；历史误删两条链接是编辑方法问题，不能保证 CAS 能防止作者自己的删改错误。成本与已证真实并发覆盖损失尚未知，低于 D1–D3。

## D5 / P2：评论/Issue 创建可重试，不用重写来补读回执

**before**（真实案例形状）

```sh
braid issue comment 7 --body-file receipt.md --json | head -c 300
# 为取被截掉的 id，再运行 comment 写命令
```

**after**：使用方法首先改为保存完整 JSON 后读取；这是当前就可做的最小改法。命令失败/不确定时查 timeline 和具体对象，不能为取 ID 盲重发。

```sh
braid issue comment 7 --body-file receipt.md --json > receipt.json
# 后续只解析 receipt.json，不再次调用 mutation
```

接口候选沿用 PR create 的 request-id 概念，拓展到 comment/Issue create：

```sh
braid issue comment 7 --body-file receipt.md --request-id issue7-handoff-v1 --json
```

```json
{"id":256,"outcome":"created","replayed":false,"deliveries":[{"recipient":"glm-1","status":"queued"}]}
```

同键同请求返回原 ID、`replayed:true`，不重复通知；同键不同正文/目标明确 `REQUEST_ID_CONFLICT`，不能套用 PR create 当前“同键忽略新正文”的规则而不告知。作用域至少绑定 run + writer/member + operation + key，目标/正文/回复对象进入请求摘要；第一次写入与回执身份必须同事务保存。键是这次逻辑提交的身份，不用正文相等自动合并正常重复发言。限流、持久保留和身份过期后如何查旧回执需实现前确认，不能绕过旧 writer fence。

**兼容与风险**：有 schema/migration 成本，先把 D1 做好并采用保存回包的方法；若继续需要无人值守不确定结果恢复，再实施 D5。PR create 既有同键行为不偷偷改为 strict-match，只补 `replayed` 与说明。不能承诺全系统 exactly-once 或模型理解一次。

## D6 / P2：用帮助降低误猜，不扩大命令族

逐命令核缺补漏，缺失处的 `--help` 增加一句操作单元、一个精确案例、一条恢复入口即可。当前 BodyArgs 已明确全文替换及文件读写方法，应保留，不重复堆入另一份长指令：

- `comment resolve`：任意 ID 选整 thread；默认截至执行时最新；unresolve 不是局部 undo。
- `issue/pr edit --body-file`：整体替换；推荐先 `view --json body`；CLI 不自动合并内容。
- `comment --reply-to`：必须同工作项；ID是评论编号，不是 Issue/PR 编号。
- `pr link` 与 `Closes`：前者背景，后者默认分支合并时关闭；unlink 不移除正文关键词。
- `ready/merge`：ready 是观察；merge 读取 origin published head，完成确认用 commit/ref/state，而非本地工作区。
- 顶层提供短的只读/写入入口与运行作用域说明；Agent 环境保持不要求复制 `--state`/身份。

`--json` 无字段目前表示 all，不能照搬 gh 的“无字段列 schema”改变含义。可选 `--help` 列字段，或以后只读 `--json-fields`；不急于加入完整 schema 服务。也不导入 gh 的交互编辑器、浏览器、隐式当前分支选择、复杂模板或 jq 语言来填不相干空白。

## 静态/离线审阅设计（不是测试套件）

本轮只执行文档/源码及历史原件核对，未编写或运行 Braid/Factory 测试、mock、fixture、smoke、试跑。若以后用户批准实施，下列仍是人工契约走查与既有证据核对；编译/static checks 仅在那一实施范围执行，真实操作须另按实验授权，不能换名为探针绕过禁测。

| 候选 | 固定的现有材料与人工推演 | 通过条件 / 不能证明 |
|---|---|---|
| D1 | 原始 hide 空回包、跨项回复错误、close#349、merge#23；对照事务 commit 前后与各早返分支 | 草案能表达 changed/no-op/partial/unknown，能给出确切目标及具体原因；回包丢失时不伪造失败。不能证明运行可靠性 |
| D2 | Sheet roots314/331、GitHub root308 的真实 comment IDs/时间；手工列 cutoff 前后及新增回复 | 任意 reply 映射同 root；固定 through 不覆盖新回复；unresolve 不解 hidden；回执记录数含义无混淆。未知下游是否在短窗口读到误折叠 |
| D3 | #337/#345 的实际截断输入输出、现有 timeline envelope；逐路查字段依赖 | 精确读取到目标、缺页有下一游标、无默默忽略 flag；原始全文仍可取。无延迟基准或净token测量 |
| D4 | Issue9 原文替换与读回恢复；手工交错 A读→B写→A写及同body重试 | guard 前失败不写 body；raw hash 定义一致；作者自身错误仍需内容diff/读回。不得声称已复现并发事故 |
| D5 | #256/#257 真正重复提交链、现有 PR request-id transaction | 将“补取ID”变成复用同次请求/读取；不同payload复用键被拒绝；不重复 comment事件。未验证故障注入或 exactly-once |
| D6 | 已有帮助语法与案例中错误参数、旧binary版本表 | 新读者仅看相应帮助即可解释操作单元/副作用/恢复；历史无此提示仍按历史记录。不能替代未来真实Agent使用反馈 |

建议实施切面：先 D1/D2/D3 的最小部分及 D6 对应帮助；当前已做的 resolve 回执与 reset 终态修复只核部署身份，不重做。D4/D5 作为明确风险候选，等待接口取舍后再计划，不因本报告就获得开工授权。
