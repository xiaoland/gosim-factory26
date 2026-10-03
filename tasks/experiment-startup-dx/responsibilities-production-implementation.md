# 生产与域装配实施读回

本轮按已授权 responsibilities-design 实施，源码只修改隔离 worktree。主区 provider/gateway/application seed 增量经真实三方合并纳入 reviewer，原始合并材料保存在 `runs/responsibilities-implementation/source-merge/`，没有接管运行中的实验。

## 当前公共调用

`compile_intent` 只处理声明及显式政策依据；既有 runtime descriptor 与 Harness/SDK 路径保留为未解析 locator。`doctor --job` 对计划只返回所选目标的声明，不提前读取未生产材料。ARC 分数原件的解释由 `lab.arc_bench.score_evidence` 承担，是否选择候选模型仍由 intent 的明确政策决定。

`controller.build(..., job_id=ID)` 只生产所选目标依赖，不构建上游 job，也不启动执行。未选择的目标仍在原始定义中，依赖某个已发布输出的要求保留供显式 start 输入绑定。Controller 代码安装到 `controller-source`，runner 代码安装到 `source`；manifest 的 `code` 保留 controller 键，并新增 `runner_code/code_roles`。两角色使用实际导入闭包，controller-only 修改不改变 runner 内容 key。一次 build 内的 controller/runner runtime 验证共享实际内容读回窗口，不持久缓存免检结果。

材料由 `materials.json` 声明，四个 build 只传参数。组件各自有生产锁及身份，agent/runtime/skills/support 分开；私有 tool/provider 输入与公开 seed/routes 不影响公开 Harness 内容 key。SDK 只生产薄启动材料，实际子域安装所需 reference/member 并认证只读挂载。该投影只读取 agent/support 的入口材料，不先遍历 runtime/skills。Hosted 唯一自包含投影携带角色内容、公开输入及精确的私有输入，成本与 SDK 分开。位置及保留索引可引用 store，公共内容 key 不包含 store。

`execution_context.validate_assembly` 统一校验 fresh/prepared/SDK/源码开发的语义。Adapter 提供真实 namespace/placement，公共 bootstrap 创建服务与 context 并拥有入口关闭。四个 main/run 不再自行创建资源或 telemetry 服务，也不接受无 context 的直接运行。源码开发由 `scripts/experiment_entry.py --source --runtime --skills` 提供相同装配服务入口，e2e 要求显式额外 runtime；未发布的源码定义明确不声称可恢复资产。Resume 的入口代码由冻结 executor 满足，不为历史四角色 prepared 伪造 support 引用。

Generic prepare 只做不可变 snapshot-copy；mutable repair 不再进入这个生产缓存路径，归显式 recovery 操作。SDK 实际成员位置使用统一 member_payload/receive_member，原 reference 和完整清单身份保留，不能把成员换成新 artifact 身份或假称拥有整份内容。

## 取得的反馈与限制

真实现存 `example-intent.json` + `example-environment.json` 完整 metadata compile 成功：schema3、explicit-request-v1、reviewer-github，耗时 0.037060 秒；所选计划 doctor 为 unbound-plan。原件与回执在 `runs/responsibilities-implementation/production-plan-final/` 和 `production-plan-readback.json`。这是明确未绑定的编译计划，不是构建/SDK运行验收，也没有前后同条件性能对照。

修改后的 41 个 Python 源码和 SDK 中 10 段静态安装程序经过内存编译，公共生产/装配模块实际导入成功。真实角色源文件读回为 controller 62、runner 37，逐文件身份及范围在 `production-source-readback.json`。读回发现并修复了不存在的 submission 包入口、controller CLI history/analyze 闭包缺失；submission/__init__.py 由冻结生产器明确生成。

没有执行新依赖安装、完整组件生产、模型、网络、Docker 或官方 SDK。完整打包、启动至首模型和热恢复的耗时仍待具体获授权运行取得；此次小计划耗时不能外推为整体提速。Local detached writer 的完整 checkpoint 覆盖限制、Hosted 自包含限制、SDK 官方 resume=false 均保留，由实际能力回执解释。普通输出与完整恢复捕获仍分别走其公共合同，不降低 writer/身份约束。
