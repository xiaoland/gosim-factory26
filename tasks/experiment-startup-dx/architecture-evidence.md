# 全生命周期架构证据

本次是架构调查，不是新实现验收。源码以独立工作区 `feat/experiment-startup-dx` 当前版本为基准；只读对照主工作区正在进行的启动修复。没有启动模型、Docker、网络操作或设施测试，没有新增耗时数字。上一轮 ARC 原错及离线 compile/material 反馈分别见 `findings.md`、`implementation.md` 与 `actual-*-readback.json`；本文不再逐项复述它们。

## 当前职责与物理布局

现有 identity/relation 模型应保留。缺口在于同一个组合定义进入不同执行域后，尚无统一设施把 artifact member、实际路径、服务与可写状态装配成可直接执行的合同。`runner._assemble` 对 fresh job 直接返回 workspace，仅 prepared 路径有完整装配（`lab/exp/runner.py:397`）。因此“有统一 runner”不等于“fresh、restore 与 child 都消费统一执行装配”。

| 执行场所 | 当前实际负责人和布局 | 不能当作共同能力的差异 |
| --- | --- | --- |
| Local | controller 冻结代码/runtime；runner 绑定 inputs 与 attempt/workspace；variant `run.py` 创建 `.factory26/<id>`、原生配置、环境与 layout。prepared 才由 runner 安装固定逻辑根。 | 没有内核只读挂载承诺；已有逻辑根不能覆盖不同内容。宿主 SDK Python 与 Harness Linux runtime 是不同资产。 |
| 自有 Docker | backend 持有 daemon asset store、attempt volume 与 RO 输入；prepared RW state 在独立 `state/run` 并挂回原逻辑根，所有 collect/export 用同一 layout binding。 | daemon 与本机物理根不同，必须输运和读回；当前 prepared 不迁移原 native logical roots，不能假设换 daemon 后路径仍成立。 |
| ARC Local + SDK child | 外层是 Local job；adapter 制作自包含 instrumented delivery；SDK 创建自己的 submission/template workspace；Workspace 处理远端 upload/download；child wrapper 再提供观测服务。 | 外层 runner PID、样本与 localhost receiver 不是 child 服务。官方 SDK 的 staging/启动 ABI 与设施可控容器不同；必须实际适配，不能把外层 Docker 配置当 SDK 自动理解。 |
| Hosted | controller 生产 ZIP；hosted adapter upload snapshot、创建 run、start，保存平台身份；平台交付 opaque export。 | `hosted.capabilities` 明确 pause/resume/checkpoint=false、telemetry=platform-export-only（`lab/exp/hosted.py:19`）。当前上传 API 是 ZIP，无可见 artifact-ref 装配接口。不能承诺可控域内热修复或完整 checkpoint。 |

定义/运行数据已经在新 I14 内部分离：`scripts/harness_layout.py:45` 记录 agent/runtime/skills/braid/extra 定义，拒绝定义与 state 重叠，派生配置留 state。variant 仍自行决定 root、工具环境、资源接入、telemetry 和 Braid 生命周期（例如 `variants/pi-braid-i14/run.py:235`）。这是记录边界，不是设施持有的装配/启动边界。

## 新启动轨迹进一步证明的边界

主 Agent 根据实验 owner 最新会话记录指出 exp19 telemetry 服务/binding 失败、exp20 fallback 引用了旧 ResourceEvidence 样本导致 freshness 失败、exp21 child layout 解析到宿主 `/Volumes` input root。实际运行错误原件由该 owner 与根任务保存；这里仅采用根 Agent 提供的有界轨迹并核对源码，不宣称自己重新执行这些失败。

隔离 wrapper 已清掉父资源/service 变量、创建 child resource sampler 并连续采样，然而 child telemetry 服务只声明 ready，未把 receiver binding 放入同一个服务描述（`lab/arc_bench/arc_bench_adapter.py:150–214`）。`scripts/agent_support.py:363` 又消费另一个环境变量的 binding；这种双入口仍需要人核对同一 attempt/stream/epoch 是否一致。

主工作区 `arc_bench_adapter.instrument_entry` 的两轮重绑循环按 root.name 或 role 猜 runtime/skills/braid 在包内的位置，候选不存在则继续传父域 root。它是正在运行的实验的具体止血，不能升级为通用 placement 合同。未装配的输入必须显式 unavailable；父路径不能成为子域候选路径。

还有独立的 member 丢失问题：`scripts/harness_layout.py:17–27` 从匹配 root 重新计算 relative member，却不组合输入 binding 已有 member。例如 ref 指向整份 agent，而 runtime placement.root 指向包内 runtime，当前计算得到 `.`，实际应是 `runtime`。`runner._input_bindings:369` 本身只有 reference/store/root，没有明确 member/domain 字段。这说明 artifact 身份与域内 placement 必须分开，且 member 组合必须由机械装配合同保留，而不能靠 root 名称恢复。

## 重复成本所在的真实生产与消费点

COW 减少本地复制的实际写入量，却不减少文件枚举、全量读取哈希、压缩与跨域发送。下面的重复不应混称“所有校验都多余”。

| 阶段及 caller | 当前成本 | 是否外部强制、建议责任 |
| --- | --- | --- |
| `package_agent.selection:255` → `plan_material:304` → `produce:308` | selection 全量 runtime/skills/support 身份；produce 再计划；完成前再次计划；cache-hit 也读整份 payload。 | 可变源码输入捕获前后检查有意义；已经冻结的 runtime/ref 应消费 producer identity，避免每个 variant 再扫相同 runtime。需要生产计划接受不可变依赖引用。 |
| `package_agent.assemble:167` | 每份 variant 材料包含完整 runtime、技能与 OTLP 支持；不同 variant 共享依赖仍进入各自 payload。 | 不是 Hosted 强制的内部存储形态。先生产组合定义；只在 ZIP/SDK 自包含交付边界展开。 |
| `environment.produce_materials:131` | producer payload → artifact publication；Hosted 另产 ZIP 再 publish。 | 发布需要封口，但生产与发布同设施可移交已封口对象，避免再次全量树和读回。ZIP 是交付形态，应按组合 identity 缓存，不能成为所有场所的内部材料。 |
| `controller.build:259–273,309` | 输入 origin contents、publish/verify 等重叠全读；`_executor:49` cache verify 后 resolve 又 verify。 | 跨消费者边界需确认实际内容，但同一操作窗口无需为同一 ref 重复全读。prepared resolver 已按 ref 分组，generic `_input_bindings:369` 尚逐输入解析。 |
| `controller.verify:417` 与 backend `preflight:216`、`local_launch:228` | runtime 全 inventory、解释器与冻结 code 读回；启动邻接调用重复读取同一资产。 | readiness 与启动防 TOCTOU 要绑定同一实际资产/窗口；不能直接建立永久信任缓存，也不应每层独立全量校验。 |
| `arc_bench_adapter.instrument_entry:61` | material → instrumented delivery，ZIP 先展开，另装 collector/support。 | 包装观测入口是设施责任；静态 support/runtime 应是复用定义组合，delivery 是明确投影。 |
| `docker_workspace.Workspace.send:252` / recover:278 / confirm_local:399 | 完整 SDK workspace inventory、远端完整传输、返回 tar、解包并核对、后来 confirm 再全 inventory。 | 原始 transport 两端需要完整性校验；重复 confirm 可消费同一安装回执而非再全扫。remote SDK 自包含树目前受接口限制，但设施可区分定义/状态，不能断言所有往返是外部要求。 |
| `local_job.job:102` → `runner._seal_outputs:586` → `_archive:663` | ARC named output workspace path='.' 先 publish 全树；generic terminal archive 又复制/发布一遍。前者未应用后者 definition capture 排除。 | 明确设施重复。完整 workspace 只应有一个 authoritative 封口；named output 关系或成员视图应引用它。应用 artifact 的独立冻结用途需保留。 |
| `backends.export_payload:610` | stage 下载、完整核对、安装与安装回执；新逻辑成功后释放匹配 stage duplicate。 | 必需 transport 的实际读回不能删；但同域执行不应为了恢复默认先导出本机再回传。 |
| checkpoint → prepare → publish → runner assemble → `execute_prepared:779` | state capture 复制/语义检查，prepare 再复制/检查，artifact publish 再复制/封口，运行装配再复制/读回，入口 inventory 再读整 state。 | 跨域搬迁或离线封存有意义；同域换定义应复用独立工作 state，必要快照与持久 lineage 不要求整套往返。入口可消费本次装配证明而不是重新全扫。 |

`package_agent.write_zip:103` 已经一边压缩一边 hash，不应改成“预 hash 后再压缩”。Git/SQLite 语义检查针对真实状态合法性，应在 capture/repair 的状态边界执行；不可变定义的内容身份检查不是同一种校验。旧冻结混合目录不能根据目录名猜测排除，新合同与旧合同必须明确分流。

## 热修复生命周期尚未闭环

公共 `lab recover` 只接受显式 checkpoint、用户提供的新 intent/target/repair，再构建全新实验目录（`lab/exp/controller.py:450`）。它不停止 source，也不取得 capture writer closure。`stop_evidence:961` 明确只提供一次物理停止观察；`submission/exp_checkpoint.py:287` 不把它当持续 writer closure，缺 acquisition 则只能 partial。这个约束正确，但“由哪个公共入口获得合法完整 checkpoint”仍需要 Agent 拼装。

prepared 的 Local/Docker 装配已经有固定 root、ref retain、RO定义与 RW state 合同（runner:397；backends:336），但只覆盖已经 prepared 的执行。ARC 高层 operation 仍生成 SDK fresh generate 入口，未声明可组合的恢复装配；不能因为 generic recipe 可以手填 `--execute-prepared` 就声称 ARC operation 能恢复。Hosted 根本不暴露 writer 控制，必须明确 unsupported 或有限应用 replay。

同域恢复所需生命周期应是：暂停/停止原 entry 与已登记 writer → 域内 state 的一致快照/保留 → 编译新定义组合或 derived inputs → readiness 验证实际 placement/新入口 → 在同一 state 位置启动新的 execution incarnation → 继续采集并封口旧 incarnation。必须保留 attempt、checkpoint、definition relation 与各原生产者身份，而不制造万能 trace ID。当前 attempt/workspace 的 ownership 与 artifact retention 不宜直接改成“同路径任意共享”；共享 state 需明确唯一 writer lease/域内持有人及新旧 incarnation 转移。

## 可采用的共享职责方案

建议先收敛两项设施合同，再迁移各场所，而非继续新增 bespoke operation：

1. **定义组合计划**持有 variant、runtime、skills、工具与 facility support 的不可变依赖引用/member。producer 输出独立可复用资产；compiler 输出定义组合与启动需求。ZIP/SDK delivery 是场所投影，缓存键来自完整组合与 delivery ABI；本机和自有 Docker 直接消费组件 refs。
2. **实际执行域装配**持有本域 placements、独立 RW state、实际 entry/runtime、子域服务 ready/binding、writer 与 close。每个 domain（含 SDK child）从冻结引用解析本地 member，永远不继承父路径/localhost/sample_path。variant 消费装配结果并只负责 Harness 行为，fresh 与 prepared 走同一入口；backend 保留真实 RO/输运/平台能力差异。

组合的通用字段可以相同，能力不能虚构相同。Hosted 的 delivery/export adapter 仍负责平台 API 与 partial 证据；ARC SDK adapter 负责 SDK workspace 与 container 生命周期；Local/Docker 负责自己的独立 state 与域内恢复。公共 projection 应解释“资源准备、装配、服务、entry、provider 首次活动、封口”分别在哪个 domain，不能将 controller running 当作模型已经启动。

验证责任按发生边界分配：可变 source → frozen producer；artifact 首次进入域 → 输运/安装读回；retained immutable 在同操作窗口复用验证；RW state capture/repair → 状态语义；entry → 消费实际装配回执。需要明确管理的 immutable 不可写承诺与 lease，否则不能将永久 hash cache 当可靠性优化。

## 如何测到验收标准

下一轮实际授权运行应复用一份真实 frozen 定义和 state，记录以下阶段的 monotonic start/end、读取哈希字节/遍数、复制写入字节、输运字节、缓存命中及域身份；零模型的生产/装配反馈与实际模型启动反馈分开报告。

| 用户验收 | 必须分段的成本 | 对比条件 |
| --- | --- | --- |
| 缩短打包 | 选择/捕获、共享依赖生产、variant 生产、发布、delivery 压缩 | 同runtime四variant；冷cache与同定义重入；更改一个variant不再重产共享runtime。 |
| 缩短启动 | compile、build/ready、域内asset传输、state装配、服务ready、entry确认、首次provider受理 | Local、自有Docker、ARC child分别计时；不把平台排队或供应商首次响应混入设施装配耗时。 |
| 缩短热修复恢复 | writer closure、state快照、修复定义生产、域内重新装配、恢复entry、跨域可选export/import | 同域小代码修复与跨域迁移分别对比；同域禁止把完整定义/state roundtrip当默认路径。 |
| 空间回归 | sharedassets、delivery、active state、checkpoint snapshots、named outputs、terminalarchive、scratch分别实际占用与逻辑大小 | COW的逻辑GiB不是实际独占GiB；测峰值和终态，防“删除scratch后看起来省空间”掩盖启动峰值。 |

以上为可验证方案，未取得新的实际耗时、模型成功或完整新checkpoint恢复结果。既有 compile 成功和真实 material 角色读回只能证明其原范围，不足以关闭生命周期或性能验收。
