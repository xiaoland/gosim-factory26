# 共享恢复准备实现

2026-10-02，用户授权“同意，开工，可以自有提交”。本页记录恢复打包、包内恢复和独占 Linux prepare 的实现及实际反馈；主入口、监控与 Docker 输出回收由同一任务的其它责任面持有。

`lab.arc_bench.recovery.prepare(spec, directory)` 复用恢复打包 CLI 和包内 `main.py --prepare-only`。输入选择 `package`（已有恢复 ZIP）或 `recovery`（现有打包器参数，使用下划线字段名），再声明 `docker_image`、可选 `docker_endpoint` 或 `docker_context`、`uid/gid`。`recovery` 可以引用 `workspace/workspace_sha256/base_package/journal/task/source_run_id/source_package/stop_receipt/stop_container/git_reconstruction/braid/braid_source/braid_source_identity`，材料动作沿用现有布尔参数。

结果返回 `status=prepared`、最终 `package/package_sha256`、`receipt`、`source_binding/source_binding_sha256`、`readback/readback_sha256` 和 `prepared_identity`（实际容器、镜像、endpoint、包内 attempt）。失败保存本次具体错误与原始日志后抛出原异常。操作目录必须在 Git 忽略路径或仓库外，目录权限为 0700；原件、含工具凭据的 ZIP 和解包只留在私有制品内，不进入共享文档或人类输出。

来源 journal 校验原包的 SHA/manifest 和已保存终态，目标 base 独立校验。显式更换 base 需 `refresh_native_materials`，并继续记录旧包身份和材料差异。`stop_receipt` 保留原件/hash、确切容器 ID、停止状态及观察时间；多条回执由 `stop_container` 选择。旧停止回执未嵌入 source run ID 时，如实记录为 caller-selected container，不能宣称它独立证明 run 关联，也不是新鲜 Docker 观察。

缺失 clone `.git` 时，`git_reconstruction` 为 run 内相对 clone 路径到 `{commit, branch, evidence}` 的映射，commit 必须是完整 SHA。恢复从保留 origin 对象库 fetch，显式绑定 HEAD，`read-tree` 重建 index 并保留工作文件。程序不从 DB 的登记 branch 猜实际 checkout，不宣称原 staging、reflog、未发布历史或 merge 状态已恢复。已有 `.git` 优先直接保留。

宿主 prepare 固定 Docker 原生选择的 daemon、镜像 ID 和 UID/GID，独占容器关闭网络且没有任何挂载，创建 `/workspace`、`/packages`、`/evidence` 并准备写权限。它不注入费用 key，不调用 Braid、模型或官网写接口。输入引用、最终 ZIP 和独立读回均保存 SHA。文件、native session/model/auth、DB 身份与工作项、Git HEAD/ref/dirty、授权技能/home 材料及实际 Braid binary 从源 ZIP 和目标包取得比较依据，没有固定题目文件数。显式模型/transport 变更按对应 before/after 回执核对；其余文件仍须保持。

成功重入校验 spec 与 package/readback SHA，直接复用完成回执，不再次调用包内 main。失败重入检查输入引用内容没有改变，并创建新 attempt 目录，保留旧尝试。容器最终仅停止并保存真实退出状态，不删除容器、原卷或保全副本。prepare 完成仅证明这些准备和读回事实；provider resume 仍为 `not attempted`。

## 实际操作反馈

已完成三个修改面编译：`scripts/package_completed_recovery.py`、`submission/recover_completed.py`、`lab/arc_bench/recovery.py`。没有编写或运行 Factory/Braid/SVC 测试、smoke 或改名自检。

首次正式操作使用现有 Sheet r2 恢复 ZIP，在 development-1 的独占容器 `fa61d38af245aa36aa01ac018934ed3229ae222e662f418754e68b2b998556c6` 执行 prepare。镜像 `factory26-i13-2-braid-r2-20261001` 是编译镜像，包自身明确拒绝平台：`RuntimeError: 参赛包需要 Linux x86_64、CPython 3.12`。原始 main/Docker stderr、退出码和停止状态保存在 `runs/experiment-operations/20261002/recovery-prepare/sheet-existing-package/attempt-721ac293ea6f76e6`。这是环境前提失败，不是 provider 或生成结果。

第二次改用既有官方本地 runner 镜像，从本轮 Sheet 原 workspace 和 r2 base 通过新的共享接口派生包，绑定已保全停止回执的 Sheet container，再在新独占容器执行。结果入口为 `runs/experiment-operations/20261002/recovery-prepare/sheet-derived-package/receipt.json`，具体读回与限制在本次结束后补入。

真实 GitHub 源 `377afa346c92` 的历史 `hosted-recovery-20261001/github/state.json` 仍保存 `RUNNING`。新的 journal 路径会拒绝该非终态快照；本次不改写它或用 caller-confirmed 升级终态。GitHub 缺失 application clone `.git` 的最后 HEAD 选择未在此责任面自动推断，必须提供明确证据后才可 prepare。

第二次实际操作成功：最终 ZIP SHA 为 `8eff845a758aba3b577aa0a4f581045fd6e1c427f4f231602813747a29a237a9`，包内 prepare exit0，专属容器为 `ee1fbdc63beb980fe7862fd183aa7971cc4c2f67ead4ea81e08ce1a04dbde2ba`，最后已停止并保留。完整实际 template 副本在 `sheet-derived-package/attempt-9fcb98136b366505/prepared-workspace`。宿主从原 workspace ZIP 直接逐字节比对 21764 个源清单保留文件，无差异；直接读取源及实际副本 SQLite 的七表，provider sessions、agent instances、assignments、context resets/events、work items、worktrees 全部行相同。实际 Braid SHA 为 `9d322da9e3dde2d8fb065cff2f5543fdc668dd8dcd2e653a31e87fb1a34874eb`，授权材料比较无差异。独立原件入口为同 attempt 的 `independent-host-readback.json`，完成重入沿用同一包、attempt 和容器，事实保存于 `sheet-derived-package/reentry.json`。新源码随后增加的环境持久冻结、runner 脚本冻结和 Git 读取失败门槛已通过编译；本次执行的 runner 原件及 SHA 单独保存，未用当前文件覆盖实际覆盖版本。

## 恢复执行门控

`verify_launch(package, preparation_receipt=None)` 依据实际 ZIP 成员及恢复 main 识别恢复包，普通新生成包返回 `not-required`。恢复包必须有与最终 SHA/source 匹配的成功 prepare，并核对原始 command/exit、包内准备及 attempt、容器 isolation、Braid SHA 和 SQLite before/after 原件；然后核对来源停止证据。成功返回 `verified` 与具体 stop basis；不满足时抛出带原因的 `ValueError`，由启动入口记为 Blocked。

官网来源要求恢复 ZIP 内冻结的完整终态 journal input/state 观察与 manifest/SHA、源 run/submission/原包绑定一致，冻结观察中的 pending 未确认时禁止执行。原活动 journal 路径只供追溯，后续 status/collect 改写它不影响已冻结的终态证明。本地来源要求原停止回执 SHA、确切容器及启动身份、停止状态和 source run/daemon 一致；run/daemon 可以由停止原件直接提供，也可以由冻结的 source identity 与 pre-stop identity 原件链提供。`source_stop_confirmation` 的普通字符串和 `caller-confirmed` 不构成证明。旧历史恢复 ZIP 仍可做离线 prepare；需要新执行时须另行准备有来源绑定的操作，不改写历史回执。该门槛只约束新启动，不能用于取消已经运行的实验。

对本次真实成功 Sheet prepare 直接调用门控，得到明确 Blocked：`停止观察未绑定来源 run/容器；caller-confirmed 不能作为独立停止证明`。旧停止原件确实没有嵌入 source run ID，该成功 prepare 同时未冻结额外 source identity 证明链，因此“已准备”与“可执行”保持分开。没有启动 provider、增加收费尝试或改变原实验。完整门控结果保存在 `sheet-derived-package/execution-gate.txt`。官网 journal 换 base 路径和缺 `.git` 的显式重建路径尚未在本次实际 Linux 操作中覆盖；需要具备原终态和最后 HEAD 的明确证据，不能以编译或本地成功替代这些分支的真实反馈。

独立预演收敛的证明链接口不要求历史停止文件自己新增 run ID。`recovery.source_identity` 可引用原始 preservation source identity，`recovery.stop_identity` 可引用原始 pre-stop readback；后一项仅在旧 stop 不含 daemon 时需要。两文件 SHA 冻结进入 `source_identity_binding`，沿 source run、Braid run、exact container、StartedAt、run label、source endpoint daemon、pre-stop daemon 与 stop.before 完整 state 精确连接到 stop.after。没有证明链仍 Blocked，也不按 case 名或调用方选择猜关联。

已对 Sheet 三份真实原件做只读关联：daemon 与 endpoint/pre-stop daemon 一致，source run 与容器 label/pre-stop run 一致，容器 ID 和 StartedAt 一致，pre-stop state 等于 stop.before，stop.after 为 Running=false、Pid=0。原件 SHA 及逐项事实保存在 `runs/experiment-operations/20261002/recovery-prepare/source-stop-chain-readback.json`。旧成功 prepare 的 ZIP 没有冻结新证明链，继续 Blocked 是正确语义；未改写其历史身份或原停止文件。新接口已经编译，正向 Linux prepare/执行门控尚未实际覆盖。主 Agent 明确不为本接口再次传输 699M 包或新建物理 prepare，本次只交付真实原件链的只读事实与编译反馈。


## 冻结 journal 观察

独立复核移除了对活动 journal 文件长期不变的错误要求。打包时一次读取完整 inputs/state 原字节，验证选定 run 的终态后保存私有原件，并作为 `recovery-journal-inputs.json`、`recovery-journal-state.json` 进入恢复 ZIP 的 manifest。`journal_binding.frozen_observation` 记录成员名，原字节 SHA 与原包验证 SHA/manifest identity 同时冻结。`verify_launch` 从绑定最终 ZIP 内读取这些观察并核验 manifest、run/submission、终态、pending 和原包 SHA 关联，不重新读取活动 journal/state 或原包路径；路径保留追溯用途。旧包缺冻结观察时明确 Blocked，不回退为要求旧 journal 永远不变。

真实只读反馈使用历史 GitHub run `346bc3b51b09` / submission `d0692dd35545` 的保存 FAILED 观察。调用实际 `journal_inputs` 冻结完整原字节后，独立读回 inputs/state 与原件逐字节相同，两个 SHA 与 receipt 一致；原包 SHA 与冻结 inputs 相同，原包 manifest 也相同。原件与结果保存在 `runs/experiment-operations/20261002/recovery-prepare/source-journal-freeze-readback`。相关源码已重新编译；未构造新恢复 ZIP、未新增 Linux prepare、未调用 provider 或官网写接口。冻结观察的包内正向执行门控尚未在真实新包中覆盖。
