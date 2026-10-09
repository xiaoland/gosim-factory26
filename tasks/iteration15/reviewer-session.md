# I15：每 PR 一个 reviewer Braid Agent Session

## 当前更正（2026-10-08）

用户澄清 reviewer 是具体 assignee，不是 Profile；同 PR 同时两个 reviewer Session 验收被禁止。用户授权：“改派既然是创建新的 reviewer Session（原有的 session 被终止）。你可以开始改造。”随后针对候选A→B明确选择每次新建Session，解释“两个都是不同的assignee，怎么能复用一个agent session”。因此之前同成员跨候选持续负责的理解和本侧会话首轮条件持久方案都已撤回。

本次撤掉 PR 执行锚及 current_request 的消费、自动继承 reviewer、跨请求 canonical/resume/reset、历史 checkout 放宽校验和 conclude/cancel 保留 Session 的逻辑。新候选重新指派独立 assignee/Session；结束候选沿 Unassign 终止原 Session。冲突检查不再豁免旧锚上的 assignment，直到物理停止并退役才允许下一候选。当前 Pending 请求改派保留共享 replace_assignee 停止屏障，旧身份被 fence，停止后新建 assignment/agent/native Session；同成员重试仍幂等。

保留已冻结 schema 19 的原 SQL/checksum 与归档支持，运行代码不读写 pr_review_sessions；不降级或改写已存在数据库。Braid system、I15三个成员指令/run说明及现有技术说明同步更正。此前条件持久首轮产物 runs/iteration15/reviewer-session-correction-20261008 仅为撤回方案的历史，不作为交付；最终源码与反馈位于 runs/iteration15/reviewer-request-session-20261008。不热改在途运行，不启动模型或官网评测，不新增测试/smoke，不commit/push。

实际隔离 CLI 反馈：历史候选 A/B 对应 request 18/19，分别指派 reviewer-15/reviewer-16；新请求默认为 issue_owner，不能重新指派已用过的 reviewer-13。取消候选A和对候选B提交明确未验收的 Inconclusive 结论，均清除 current_member 并保存 Unassign；后续请求再次由 Issue 负责人承接。同request-id重试幂等，同PR第二个Pending候选被拒。另一个直接复制 Evo 原冻结现场的副本保留真实 assignment/agent：同成员重试身份不变，改派后旧身份进入 stopping，cancel后仍为 stopping，新候选依然被拒。没有运行provider或合成assignment/agent/session/turn，不能宣称已实际验证原生物理退出、新Session启动或评分收益。

Mac编译通过（14条既有unused警告）。首次snapshot按旧文件清单遗漏并行新增的execution.rs，保留具体编译错误；修正为冻结完整src与migrations，并调整该新查询对旧锚的消费后，重新编译通过。Linux release编译通过（14条既有unused警告）。最终overlay为 runs/iteration15/materials/reviewer-request-session-20261008/overlay.tar，SHA256 38962b5fa124efa02e1ac6fcca057c46a06c22ade7ccd6925e58a986eebfc888，22517760 bytes；新binary SHA256 17c3aa5d51ac4a4ea4c59f3bda7df26b37ed9bc6ac4a3c08bb0d8937a4357962。实际manifest/底包/overlay成员哈希与三个成员指令、run说明逐字读回核对完成，见该目录readback.json。

## 2026-10-07 实施历史（其中无条件持久复用的需求解释已撤回）

用户本轮纠正：“一个 PR 只能有一个 reviewer（对应一个 Braid Agent Session）（可以改派）”。原实现将“当前无并发 reviewer”作为约束，conclude/cancel 之后清除责任并强制原生 teardown，下一候选重新认领 login 和创建 assignment。该实现并不满足用户要求。

本轮由 reviewer_owner 接续负责 Braid review 生命周期、对应技术说明、I15 reviewer 职责段与 Linux 二进制。允许必要源码改动，不 commit/push，不新增或运行 Factory/Braid 测试、smoke、模型或官网实验，不修改正在运行的冻结交付。运行反馈采用编译和真实历史 CLI 隔离副本。

修复前接口事实：每 review request 都有唯一 work_item；assignment、agent_id、原生 session、worktree、消息和 reset 都依赖该 work_item。只复用 login 会绕过真正的 Braid Agent Session 生命周期。replace_assignee_in 已有停止旧执行、等待物理停止后 materialize 新负责人的屏障；request 的冻结候选、需求快照、结论和 checkout 必须继续独立保留。

实施准备方向：为 PR 保留稳定 review 执行锚和当前 request；每候选仍有独立冻结 request，后续投递复用锚、assignment 和 agent_id。结束候选不自动退役 reviewer；改派显式切换锚负责人并沿现有物理停止屏障。advisor 已确认此职责分离方向。实现已完成，源码和新 Linux 二进制均已冻结；旧运行未热改。

修复前调用链核对：`request_review` 建立冻结 request 和独立 review work_item；`assign_review` 调用 `replace_assignee_in`，后者派生具体成员并发 Assign/Wake；`materialize_review_assignment` 在 review work_item 上创建 Braid assignment/agent_instance，并用冻结 checkout 作为原生 cwd；`close_review_in` 当时在 I15 强制 Unassign，最终通过 SessionManager 停止原生会话。`review_writer_for` 以 work_item 和 assignment revision 限定写者；`review_context` 与 reset、resume、reactivation 都按 review work_item 编号读取候选。本轮稳定锚实现同时修正了这些边界，未仅删除 Unassign。

既有 `pr review checkout` 合同是取得独立固定候选而不切换当前工作区。复用 session 时保留原 cwd 可以沿此合同工作，但 system prompt 不能继续把锚编号当作最新 request；验收操作必须使用当次 request 的显式 checkout 路径。每次 request 的结论仍校验对应 checkout commit/tree/责任，旧 request-id 重试只读返回已保存结果。

验收准备：Mac 和 x86_64 Linux 编译；从真实历史 run 的 SQLite/Git 来源复制至 `runs/iteration15/reviewer-session/cli-history`，使用公开 CLI 检查同 PR 跨候选保留绑定、幂等、改派与不同 PR 独立。副本保留来源回执，不启动 provider，不合成 assignment/session。CLI 反馈只覆盖实际请求、责任、冻结候选与事件投递，不能宣称验证了原生 session 历史连续或物理停止。

## 实施结果与反馈

PR 首次 assign 建立 `pr_review_sessions` 稳定锚；显式对当前 Pending 历史 request 重复 assign 同成员，也可建立锚并保留已存在的 assignment/agent_id。每次新 request 保留独立冻结候选和 checkout，切换 current_request 与明确的 view/checkout Wake 同事务提交；旧 request-id 幂等返回不能回退 current_request。conclude/cancel 保留 reviewer 责任与原生历史，结束候选前关闭自有验收进程和工具会话，以 conclude 结束当前 turn，等待下一明确候选。固定 cwd 只验证该 PR 当前成员的已登记 checkout，明确候选的 conclude 独立校验 request、责任和 HEAD/tree。resume/reset canonical 使用当前请求，system 不固化首个候选编号。改派复用现有停止屏障，补齐 blocked assignment，当前责任 revision 立即使旧写者失效，新执行等旧物理停止后才启动。

Mac debug 和 x86_64 Linux release 编译通过，保留 15 条 unused-code 警告。Linux 首次失败是 PATH 缺 zig，找到已有 WorkSSD zig 后离线失败缺 cpufeatures；仅联网取得构建依赖后成功，具体错误日志保留，不泛化为设施失败。源码 snapshot、完整文件哈希、命令、缓存路径及 binary 身份归 `runs/iteration15/reviewer-session/linux-build-receipt.json`。新 binary 为 `runs/iteration15/reviewer-session/linux/braid`，SHA256 `8540ea7a07df53ff9a84d6e2c2532e5811c28e1ead9895243750217f74931c2d`，已交 runtime_owner 进入最终 overlay。

隔离真实历史 CLI 反馈位于 `runs/iteration15/reviewer-session/cli-history/`：两候选分别为 review 14、15，同属 PR 11 和执行锚 review:14；新候选自动继承 reviewer-12，两个 checkout 路径独立，旧 request-id 返回 review 14 后 current_request 仍为 15。显式改派 reviewer-13 仍使用锚 review:14，并按责任 revision 取得第三个独立 checkout；锚 context 返回当前 review 15。PR 12 独立建立另一个锚和成员；去掉 tag 后仍可建立同 PR 第二 Pending request。没有启动 provider，所以该新 PR 的 assignment 不存在，不能把这些操作说成原生连续性反馈。

另一个隔离副本来自停止后 Evo GitHub 的真实最终 archive，位于 `runs/iteration15/reviewer-session/actual-reviewer-history/`。来源已有 reviewer-1 的真实 assignment `01a116cf-cedc-7820-b05b-dbdb4b04f66f` 和 agent_id `01a116cf-cedc-7820-b05b-dbe885eea32e`。对同成员显式 assign 建立锚后，两身份和 active/idle 状态保持；显式改派后同一旧 assignment/agent 进入 stopping，取消候选不伪称物理停止，新候选因仍在收口的真实 turn/assignment 被拒。副本仅应用实际 schema 19 和重定位复制的 Git origin，未合成或改写 assignment、agent、session 或 turn。

未启动新模型/官网实验，没有 Factory/Braid 测试、smoke、commit/push；原生跨候选实际继续、物理 teardown 成功与行为收益仍需后续获授权运行反馈。以上 CLI 证明请求、锚、候选隔离、幂等和真实旧身份的停止门控，不能替代该反馈。
