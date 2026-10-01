# I14 reviewer 实施与反馈

本任务承接 [实施准备](reviewer-preparation.md) 的已认可接口，主线转达用户对实现、基础验收和 I14-0 启动的明确开工授权。此分支负责 Braid reviewer 源码、reviewer 专属 profile 与基础反馈；模型实验、费用、矩阵和调度归主线，不在此启动，不提交或 push。其它并行改动保持原样。

## 当前实现

`src/objects/review.rs` 持有 typed ReviewRequest、责任与终态、固定 base/head/tree、验收 Issue 原正文及 digest、不可覆写的结论和实际 checkout 事实。新 `review:ID` 内部节点复用 assignment、wake、turn、session、member 和执行状态，编号不进入公开 Issue/PR 分配。默认 IssueOwner 使用关联 Issue 当前责任；多个关联必须显式选择 Issue，没有负责人或当前责任已不可用时具体拒绝。专门委派只改变 review 节点，保留源 PR assignment。

`pr request-review` 与 `pr review list/view/assign/checkout/conclude/cancel` 已接线。list 返回最近 30 项及 has_more；view 比较当前 ref、commit 和要求 digest，保留过时结果。请求创建使用真实 origin ref 事务固定候选并保留私有 ref；checkout 从保留 ref 取得独立 clone。同一责任重复调用返回同一路径，改派按责任 revision 新建路径并保留旧文件。默认 IssueOwner 的 checkout 还绑定当前 Issue assignment_revision。conclude 只由当前具体责任写入，HEAD/tree 不匹配则拒绝，保存实际脏文件观察；宿主明确输入标为 external，不冒造 Agent 身份。默认 owner 关闭请求只写节点、activity和结果通知，不发无人消费的独立 review lifecycle；委派 review 仍沿已有生命周期收尾。

`GroupKind::Review` 和窄 review_agent materializer 取得冻结上下文、checkout 与 reviewer system prompt，复用 PR/Review 共用的 assignment session 启动以及通用 unassignment；恢复、closed contact 和 reset 均显式路由 review，核对登记路径、origin 和实际候选 SHA。reviewer-only 只进入专门目录及 Review driver，普通目录与 Issue/PR driver 排除它。Issue/PR Context 增加有界请求摘要，Review Context 的 full/index/references/minimum 路径保留按需读取入口；status公开 items只列 Issue/PR，review 请求单独展示摘要，portable对象快照保留请求与 checkout。

`merge_with_review(turn, pr, expected_head, request)` 与 `validate_review_merge_in(connection, pr, request)` 核验明确 Approved 和所有候选绑定；local_merges 保存 request ID，prepared 重试不改换请求。尚未发布时显式重试和自动恢复再次核验要求，现有 Git base/head CAS保护发布。已经实际发布的保存 merge 只补记效果，不因后来 base 或需求变化回滚或拒绝既有收据；未传 --review 的合并策略保留。

v17 迁移只在该版本事务外关闭 FK，copy/drop/rename work_items 扩展 kind，事务内 FK check 成功后写 ledger/commit，关闭/读回失败也进入统一恢复出口；恢复 ON 后核验。v18 同时注册 cleaner 的 work_item_maintenance 迁移。旧迁移原文与 checksum 不改。

权威产品事实已更新到 Braid `docs/10-prd/objects.md`、`workflow.md` 与 `docs/20-product-tdd/local.md`，保留 cleaner 已加入的维护批次小节。reviewer variant 新增 GLM-5.3-Flash 的 pi-glm-reviewer profile 和独立职责材料；其两个 Issue 主 profile 持有收到请求后委派专门 reviewer 的实验政策。通用产品动作留在 Braid system，variant 不复制这些工具契约。

## 编译与真实基础反馈

原件集中在 [runs/iteration14/reviewer](../../runs/iteration14/reviewer/)。`basic/build.log` 和 `build-final.log` 保存正常 cargo build --locked --bin braid；最终编译成功，含 11 项 dead_code 警告，git diff --check 通过。没有编写或运行 Factory/Braid 测试、smoke、mock、探针或假 session/turn。原件里的 operations 脚本只记录正常 host CLI、Git 与实际进程操作，不进入产品源码或测试入口。

最终 Mac debug binary SHA256 为 `a32729c792b5646d9e4db253b585703369c30cf3e1a879bc5b53854452fc46ad`，review.rs 为 `a64b9afc7bf37239934847d9699d6e7aec649ed99e568db73c755be22c53c483`，store/mod.rs 为 `61b9253b81b0fff9b79594a2cd2a408573071548b57e501e2965ea7c30450ee8`；`basic/source-final.json` 保存完整源码及迁移身份。基础操作使用此前保留的 binary，末次 FK失败出口/默认关闭收口后重新编译并取得 `final-default-*` 的实际对象反馈；早期二进制与原件未覆写。

| 实际操作 | 观察与证据 |
| --- | --- |
| 正常 local 初始化，provider executable 明确缺失。 | 真实 blocked，退出1；provider session 与 agent 数均0。`basic/local-initialize.*`、state/result.json。没有将它记为成功运行。 |
| ready、request 重试、view/context/checkout。 | ready 后请求数0；同 key 返回请求1；checkout重复返回同一路径；实际 HEAD/tree/origin 独立读回。`basic/operations.json`、before-request.json、facts.json、checkout-first-*。 |
| 完成宿主候选结论后分别推进 head、base，再更改要求正文。 | freshness逐项保存具体错误，三次 --review merge均退出1；旧结论仍可读，旧 checkout SHA保持。`stale-head-*`、`stale-base-*`、`stale-requirements-*`。宿主结论明确标为对象/Git验证，不冒充native或浏览器产品验收。 |
| 固定请求3后强推丢弃源head，再委派/改派reviewer。 | 通过保留ref仍取得原SHA；旧reviewer r2路径脏文件保留，新r3路径干净；PR desired_member仍builder-1。`after-review-reassignment.json`、retained-candidate-*、preserved-old-reviewer-dirty.stdout、reassigned-clean.stdout。 |
| 有效批准请求4合并与重试。 | 真实 Git ref 更新，PR MERGED，local_merges.review_request_id=4；重试无新merge，第二次conclude拒绝覆写。`protected-merge*`、immutable-conclusion.*、after-protected-merge.json。 |
| 多个/零个关联Issue及无负责人。 | 均明确退出1，未自动取根Issue或广播。`multiple-issue-request.*`、missing-owner-request.*、zero-issue-request.*。 |
| 全部公开对象关闭、显式review尚Pending，然后cancel。 | delivery_closed先false后true。最终源码默认 owner 取消请求6产生CLOSED/cancelled和activity，但无review节点事件，零native session。`status-pending-review.stdout`、status-cancelled-review.stdout、final-default-facts.json。 |
| 正常merge进程在SQLite实际prepared后SIGSTOP/SIGKILL。 | 保存真实base/head/merge/request=1，origin尚未发布；更改要求后显式重试及正常local自动恢复均拒绝，base保持；恢复原要求后自动应用同一保存merge并记MERGED。`intent/interruption.json`、operations.json、facts.json和automatic-recovery-*。 |
| 第二次真实prepared中断后，普通git update-ref发布其保存merge，再改变要求。 | 重试只记真实既有效果，git_ref_updated=false，不回滚引用，保存review ID仍1；结论view仍正确显示base已变而不适用于新合并。`intent-published/external-publish-frozen-intent.*`、explicit-retry-after-requirement-change.*、facts.json。 |

`basic/operations.json` 保存81条初始正常CLI/Git命令及真实退出值；拒绝路径分别保留stderr。最终收口又执行默认责任的真实请求/取消/状态读取，不重跑无变化的整批操作。

迁移使用真实 v16 历史库的只读 backup，来源为 `runs/iteration11/20260930-completed-turn-resume/github/evidence/first-resume-failure/braid.sqlite3`，包含22条assignment、200条provider session、1247条turn。正常新二进制 local 调用先升级至18，再因该隔离副本仍保存原origin而明确返回 stored origin differs；这只证明迁移，不声称恢复了历史运行。`migration/before.sqlite3`、after.sqlite3、前后完整inventory、comparison.json、自动backup路径及具体stderr均保留。36张旧表的原列内容、主键和FK目标完整保留，v1–16 ledger原行保留，前后FKcheck均无错误，来源文件hash未变。新增local_merges FK使PRAGMA列表中旧FK序号0变1，目标仍local_items(node_id)，该结构事实单独记录，未将序号变化误记为记录损坏。首次inventory脚本未编码SQLite BLOB而失败，随后用base64保存原字节并完成读取；没有改动来源库。

## 未证明边界与交接

编译和host实际操作证明对象事务、旧图迁移、候选保留、责任路径隔离、结论历史和Git合并/恢复。它们没有证明原生reviewer已实际启动、assignment revision阻断在途native提交，或应用服务/端口/浏览器数据和观察确实对应候选；source中的权限和生命周期接线不能替代这些运行事实。host结论和注册checkout不等于真实native agent-owned worktree已经物化。

这些边界移交主线已授权I14实验：保留实际session/assignment/turn、进程/cwd/GitSHA与错误，观察Issue默认处理、专门reviewer独立身份、源PR实施者持续存在、改派后的旧提交被拒绝，以及真实浏览器候选对应关系。实现范围已完成，源码和durable文档可冻结；此packet保留反馈与缺口，实验输入/启动/费用仍由主线packet持有。
