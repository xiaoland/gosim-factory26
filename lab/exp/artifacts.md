# 制品、遥测与恢复证据

发布 payload、manifest、域 location 和初始 producer 保留共同可见。Consumer 在装配前取得按用途保留；完成一个用途只释放相应 hold，不以 TTL 或入口退出释放其它消费者。GC 与 retain 共用 store 锁和稳定删除意图，未知位置、旧 store、未满足保全条件的载体继续保护。Artifact identity 与 manifest hash 在跨域输运中保持不变；位置不是新的 artifact identity。

成员运输保留生产者原 reference 和完整 manifest，在接收 store 中登记完整的所选 member 位置。部分成员不能冒充整个 artifact；统一 resolver 根据登记位置装配消费路径。接收字节核验与持久化完成后才公布位置，GC 依原删除意图同时回收完整 payload 和登记成员。SDK 执行使用薄入口及所选只读材料；Hosted 交付仍使用完整独立包。Controller 与 runner 各自冻结代码闭包，变更私有模型输入不重新生产公共材料。

共享 cache 中的 runtime、Harness、executor source 与 runner.pyz 跨 run 复用，run 的 artifacts/controller-source/source/runner.pyz 定位它们并持有独立保留。负载只读消费发布资产，可写 workspace 独立装配；同 UID 的 Local 存储仍在读取或接收边界核验字节，不能拿 receipt 当永久内容证明。首次生产与无变化复用的成本不同。CLI 返回 build 成功表示材料已冻结，不表示模型已启动或入口 ready。

## 发布、封口与显式运输

制品复制以接收结果为完整性边界：export/transfer 先认证源 manifest 的引用摘要、身份及路径，再对收到的字节完整计算哈希；匹配后才发布目标，不在复制前全量预读源 payload。独立 verify 与 evidence/resolve 仍核对源字节。已完成的 transfer 重入只核验目的 store，不要求源仍可读；export 重入核对已有目标与源 manifest，不重新复制。校验失败的 staging 不发布，源和半成品保留。普通发布、装配和输运在同盘 APFS 上使用隔离写入的 clone；不支持 clone 或跨文件系统时复制字节，不共享可写 hardlink。目标完整性核验仍在传输边界执行，这不等于增量传输。

新终态将 workspace 封口一次。Workspace named output 与 terminal archive 通过引用和 member 消费同一不可变快照；archive 保存日志、遥测和该关系，不再复制 workspace。Docker 在域内封口并保留位置，所选 member 的运输是显式操作，完整导出须选择 member `.`。应用交付仍独立冻结，内容快照不自动具备完整 checkpoint 能力。 `excluded_definitions` 明确列出省略目录及对应 reference/member；含这些目录的 whole output 必须声明 `workspace-snapshot` 类型。普通目录物化拒绝遗漏定义的整树视图，不受影响的具体状态成员可继续读取。显式 export 将所选封口资产成员接收到目标资产库，回执的 `sealed-asset-relations` 表示资产已接收，不表示活动 workspace 已安装。

服务 ready、入口确认、named output 封口、telemetry 封口及完整 archive 分别记录。必需 ResourceEvidence 由 runner 持有，Docker 取实际负载的 cgroup 样本，独立于 OTLP 开关。声明产物封口并保留后，同 daemon 的消费者按原位置装配；跨域或 Hosted 才请求输运。完整归档继续保全，其失败不能把已成功的 main 改成失败，也不要求重新运行入口。新 runner 对已封口的 terminal staging 使用显式同盘 handover：先耐久记录请求、来源和内容身份，再 rename 到 artifact publication staging；发布重入复用原 artifact，rename 后失响应从原 handover 接续，不再保留一份相同 terminal staging。原工作区和未确认半成品始终保留。Docker 默认在原 daemon 的资产卷保留封口快照和终态证据，宿主只保存引用及位置回执。显式完整导出的目录仍须保存内容核对和耐久安装回执后才释放下载 scratch，未归属 metadata 保留。ARC SDK 新产生的输出 tar 标明 transport scratch，只有本地输出完成核对、耐久保存并取得 verified 回执才释放；重入依据保存的本地输出与回执，旧 tar 不按新规则自动删除。

## 遥测与分析

制品用 `artifact import/verify/export/transfer` 发布、核验及装配，`evidence` 按受限 member/字节游标读取。导入历史字节不会取得新执行证明。`telemetry snapshot/batches/export/ingest` 保留 stream/epoch/源序列、原始 protobuf 与错误；摄取同源批次幂等，冲突原件保留。Analyze 固定原件摘要和采集截止点；没有调用身份时模型用量明确未知，不从原始批次数推导 token 或费用。

## 检查点与准备

新 I14 Harness 的自包含状态 checkpoint/prepared producer 使用 schema 3，受管引用快照与同域状态使用 schema 4，application 保持 schema 2。Checkpoint v3 只捕获运行状态，通过 `harness-layout.json` 的真实 artifact reference/member 保留定义依赖；prepared 在准备和执行时解析这些依赖。物理 store 是解析位置，不进入内容身份。缺少实际 artifact relation 的 Hosted package identity 不能被补造为完整恢复能力。历史 checkpoint/prepared schema 1/2 按原冻结生产者及自包含合同读取，新 producer 不猜测旧混合树中哪些目录可以省略。

受管 checkpoint schema 4 是小型元数据产物，`state_snapshot` 引用一次封口的 workspace 及其中实际 Harness state 的 member。终态输出和归档共用已封口内容；checkpoint 只有在原快照具有匹配的 managed acquisition 时复用，否则按 capture 请求另行取得恢复快照。普通终态内容不因后来取得 closure 而升级。完整 workspace 与状态子树不能互换。Docker 在原 daemon 的只读状态挂载上封口，宿主接收 checkpoint 元数据及 domain resolver；单独持有这些元数据不意味着已接收到快照字节。跨域准备只输运选中的状态及目标缺少的定义资产。旧 schema 3 和历史自包含 checkpoint 的读取合同保留。

从冻结 runtime 派生修复材料时，先克隆完整父文件树，再覆盖明确的修复文件，并保留父来源和实际差异。锁文件相同或源码编译通过不证明 runtime 完整：发布前仍须确认父负载没有遗漏、启动 wrapper 指向的程序和依赖确实进入包；失败制品保留原身份，修正后重新发布，不能覆盖已冻结字节。


定义资产包括入口、角色、技能、扩展、工具 runtime 和 Braid；每次绑定的小型 native 配置、request 和 launcher 留在可写状态。四个新 I14 入口直接读取冻结 Braid，通过小型链接树访问技能，不再将这些定义复制进运行目录。定义资产的保留独立于 attempt 生命周期。

`python3 tooling/linux/exp_checkpoint.py checkpoint --source RUN --output NEW --source-identity IDENTITY_JSON --stop-evidence STOP_JSON --acquisition ACQUISITION_JSON` 保存来源材料，获取窗口需要覆盖全部 writer 的连续关闭证明。停止原件只证明观察时点，不能排除复制期间的中途写入。没有获取窗口证明或原 Git/native 历史缺失时保留 partial；历史 schema 1 只读，不补造 complete。

Docker 导出后的保存位置与原运行逻辑根不同。对新分离布局，checkpoint 用 `--state-binding <attempt/export.json>` 消费真实导出回执；`--source` 仍明确选择本机的运行状态目录。生产者核对导出 namespace、已安装目录及成员内容，保留原执行 OS/architecture 和逻辑路径，不从 Mac 的平台或当前 `/assets` 目录猜来源。首次运行和 prepared 接续都使用这条关系；停止与获取窗口证明仍独立提供。嵌套 SDK 的 `/workspace` 若没有自己的实际导出映射，不能套用外层 `/execution/workspace`，应保留具体缺口。

同域修复前，明确选中的新 definition reference/member 在原 store 认证并保留，再安装到目标域资产位置。材料生产不持有 mutable capture；进入修复之后只处理已冻结资产和允许的状态变更。通用 `prepare` production 只派生 immutable snapshot-copy，不借 compilation/build 隐式改活动状态。恢复操作原件保存在派生目录旁的 `.recovery-operation.json`，错误另存 `.recovery-error.json`；同 request 改参数明确拒绝。

`domain-state` 在原 capture 许可内修复派生材料，保留应用、Git 和 native 状态的位置。每项修复保存实际完成事实；半失败保留许可及原始错误，不能用旧快照证明未完成的新状态。完整修复推进 generation，实际新执行通过原权威原子交接唯一写权，并重新核对当前许可后启动。交接前旧输出、归档、export 和 Console 消费者须绑定不可变快照。旧 Console 写者先关闭，新访问实例重新登记；未登记外部编辑不在完整关闭承诺内。新 resource 与 incarnation 不复用旧出生实例。`snapshot-copy` 在目标域复制状态，不能借用源 holder 的活动路径。

低层 `python3 tooling/linux/exp_checkpoint.py prepare --source CHECKPOINT --output NEW --target-layout JSON --repair REPAIR_JSON` 保留，无网络或模型请求。有限修复覆盖材料刷新、已声明 provider transport、内部路径别名、已退役 transient link、外部 node-gyp 工具物化及明确兼容 runtime 替换。每项核对原 literal/目标范围，记录实际变化与损失；Git、native 历史与应用工作不由材料刷新覆盖。结构 partial 可以离线派生以解释缺口，但结果没有完整获取/语义保证仍为 partial，不能进入完整恢复执行。

v3 的定义换版使用 repair 的 `definition_assets` 数组，每项给出已有 `name`、新 `artifact` reference、`member` 和可选解析 `store`。同一物理资产中的嵌套角色必须保持同一引用及一致成员关系，不能只改变其中一个角色。准备和验证可用 `--artifact-store STORE` 指定当前解析位置。定义换版不改变其 logical_root，保留前后关系；不以全树文本替换迁移路径。Local 的新受管角色使用 holder 私有稳定别名；换版只在实际 capture repair 许可内更换已记录别名，不修改其只读源。未受管旧逻辑位置被其它内容占用时明确阻塞，不能覆盖旧资产。Docker 在独立 namespace 中装配只读定义与可写状态。当前 hook 仅支持同 OS、architecture、logical run_root 和明确 runtime_identity。Docker 可在另一 daemon 的独立路径空间保持同根；跨 OS、架构/native 根迁移、任意 patch 及 Git 历史重建不进入完整恢复能力。Prepared 不携带停止许可；launch 重新核对同一来源 instance 的当前停止和实际目标装配。入口消费已经装配的 prepared workspace，不再解压重建整包。

`application` 独立冻结明确 commit、需求和来源，区分 stage/final，保留未提交内容政策。一个可重放应用不证明 checkpoint 完整，终态 archive 也不等同 checkpoint。

Runner 装配已验证的恢复 prepared 后，使用包内 `main.py REQUIREMENTS --output-dir OUTPUT --execute-prepared` 执行同一恢复状态；它与 `--prepare-only` 互斥。该模式核对 preparation/provenance、需求 hash、Braid binary 和 run/state 路径，复用既有运行环境、通知、执行与归档交付逻辑，不再次解包、重建 Git、刷新材料或迁移需求。当前冻结 Lab recipe 的 routes 与私有 deployment 凭据是执行权威；routes 必须等于 prepared native transport 回执，变更时重新冻结并 prepare，包内取得材料时的凭据不能覆盖当前执行。临时目录重新创建，凭据不写入公开回执。材料换版通知仍复用同一工作区的 lock/pending 与 DB comment/deliveries 读回；每来源仅启动本轮明确授权的一条生成执行。最终应用来自 `recovered-application` 与 delivery commit，不能使用尚在工作的 `work/application` 充当最终产物。

模型和供应商归新配方，四个 I14 入口与恢复通道不强制 ARC。Native per-model bindings 在新生成时拆分 provider，并同步 profile/角色。需要统一入口时，使用 `materials/model-gateway.json` 的 LiteLLM deployment 选择结果和 `routing-snapshot.json`；恢复必须保留 catalog/config SHA 及非敏感 endpoint/wire model 快照，配置漂移时重新冻结，不能从当前目录悄悄取得新路由。既有未拆分 provider 的恢复使用显式 `--override-native-transport`，保留 provider、model、profile 和历史身份，以模型级 endpoint、认证 header 与 `samplingParams.model` 指定供应商传输；不把供应商名称映射当作概念型号迁移。旧包不因源码变化取得新路由。

Prepared 装配会保留原生会话所需的一层材料路径别名，别名使用相对链接。`--execute-prepared` 消费当前 runner 已验证的 assembly 和 prepared 身份，不对运行时派生目录重跑原始 ZIP 的无链接校验。离线准备只移除已停止 PulseAudio 的 `work/home/.config/pulse/<32hex>-runtime` 临时链接，保留原链接字面值及原因回执，不读取或删除其目标，原完整来源快照保持。

保留工作树中 `better-sqlite3@11.10.0/build/node_gyp_bins/python3` 指向 `/usr/bin/python3` 的已观察链接，离线准备只在恢复副本中物化为显式目标镜像内的解释器文件，并保留权限。回执记录原链接、实际 resolved 路径、文件 SHA 和 image_id；此操作重建可再生构建工具，不迁移原生会话、修改数据库或放宽检查点外链门控。之后仍须完成现有 Git/native 独立读回。

新 Local 执行可以启动，但当前原生工具可能脱离父进程，尚无完整的登记及关闭合同，因此完整 managed capture 会明确阻塞。普通终态 named outputs 在已知执行及写者终止后仍可复制隔离并发布不可变内容，标明 terminal-content-copy，不证明未知派生写者关闭或跨文件同一切点；这些制品不进入 holder 的恢复 snapshot。内容封口失败时，archive 仅保存日志、遥测与错误，标明 terminal-evidence-only，原状态保留。两者都不能解释为完整 checkpoint。SDK child 按实际 Docker 容器取得写者关闭证据并走公共 capture，官方下载/接收不再另开旧 capture 租约；这不提供官方 SDK resume 能力。

恢复输入必须具有 `harness-manifest.json` 且 kind 为 `factory26.harness.checkpoint`。普通 workspace ZIP、application 包及 partial 平台导出不能补造 manifest 变成恢复来源。可用 `python3 tooling/linux/exp_checkpoint.py validate --source CHECKPOINT --artifact-store STORE` 读回明确来源；成功只表示相应材料合同成立，不提供停止或启动许可。缺 Git/native/链接依赖或 managed acquisition 仍保持 partial，历史 schema1/2 沿原冻结合同。完整打包、首次模型受理及热恢复耗时仍须实际获授权运行取得，离线材料反馈不替代它们。
