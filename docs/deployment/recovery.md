# 工作区恢复、应用重放与监控

## 当前 checkpoint、prepare 与停止门控

新 Harness producer 使用 `python3 submission/exp_checkpoint.py checkpoint --source RUN --output NEW --source-identity IDENTITY_JSON --stop-evidence STOP_JSON`，可显式追加 materials-root。停止原件由 `python3 -m lab stop-evidence EXPERIMENT ATTEMPT --output NEW_JSON` 从实际执行身份与当前停止观察产生；它不会执行 stop。Checkpoint 保存 Git/未提交内容、Braid DB/WAL、native 和材料及语义缺口，partial 不得 prepare。

`prepare --source CHECKPOINT --output NEW --target-layout JSON` 无网络及模型请求，生产 harness-manifest.json 并独立读回。当前 hook 只支持相同 OS、architecture、logical run_root 与明确 runtime_identity；Docker 可在另一 daemon 的隔离路径空间保持同根，跨 OS/根路径迁移明确不支持。Prepared 不携带来源停止许可，启动另外核验同 instance 的停止证据和目标实际装配。终态 archive 不是 checkpoint，应用 artifact 也不是恢复材料。

模型和供应商归新配方，四个 I14 入口与恢复通道不强制 ARC。Native per-model bindings 在新生成时拆分 provider，并同步 profile/角色。既有未拆分 provider 的恢复使用显式 `--override-native-transport`，保留 provider、model、profile 和历史身份，以模型级 endpoint、认证 header 与 `samplingParams.model` 指定供应商传输；不把供应商名称映射当作概念型号迁移。旧包不因源码变化取得新路由。

官网表单只注入一个模型 key。需要多供应商时，恢复打包器通过 `--model-environment` 消费 mode 600 的私有 JSON，顶层只有 `environment`，其中只允许 `FACTORY26_MODEL_BINDINGS` 及各 route 声明的凭据变量。它随包保存到 `.private/model-env.json`；恢复入口先校验 manifest，再恢复私有目录与文件权限并装载，随后应用绑定。不要全量复制模型 env、把 key 写入公开配方，或把离线认证装配成功当作供应商实际受理。

## 历史恢复与旧冻结合同

以下旧 operation/Competition 和准备回执用于原件追溯及限定退役通道。工作树不再产生旧格式新执行；不将历史 ARC 政策当作当前新实验默认值。

本文说明已授权实验中如何保留进度、接续工作区或对冻结应用评分。改变设施与运行模型是不同授权范围；新一次执行须有明确输入、来源和完成条件。产品边界见 [PRD](../prd/index.md)，具体历史恢复与实测范围见[实验设施 packet](../../tasks/experiment-infrastructure/packet.md)。

## 实验恢复与反馈循环

### 持续执行一个已授权操作

`python3 -m lab.arc_bench operation prepare <规格.json> --directory <私有操作目录>` 冻结一次已授权操作，`operation run <同一目录>` 派出后台跟随，`operation status <同一目录>` 查询实际执行和采集记录。后台派出返回 `accepted`，不等于平台已启动或采集已接收。操作目录放在 Git 忽略的 `runs/` 或仓库外；凭据只通过私有 `credential_file` 引用。已有四项 I13 的接线不会因源码更新自动迁移。

规格必须写明 `authorization` 和 `venue`。本地操作引用 `recipe` 或已有冻结 `experiment`，两者只能选一项；可附 `run_labels`。已有多 attempt 时必须用 `run_ids` 明确选择；未分配的 job 只消费首次 attempt，后续 retry 不扩充旧操作范围。需要恢复时，`preparations` 保存恢复准备请求，`preparation_jobs` 将本地 job ID 显式绑定准备 ID；已有 experiment 仅核对实际冻结包，不改写旧输入。官网操作的 `hosted` 数组逐项指定 `id`、`package` 或 `preparation` 及原 Competition prepare 的题目、模型、费用参数。新增收费范围必须在所属 packet 获准，文本授权字段不能自行产生授权。

恢复准备请求引用已有 `package`，或提供 `recovery` 的来源 workspace/base package、允许材料变更和必要 Git 重建依据，并指定 `docker_image` 与 Docker endpoint/context。准备在独占、无网络、无模型凭据的 Linux 容器执行原包 `--prepare-only`，保留实际镜像、UID/GID、原日志和独立读回。准备成功只证明文件准备完成；恢复启动还必须核验同一来源已停止及实际执行 ZIP 与准备回执一致。缺少私有 clone Git 时需逐 clone 的明确 commit、branch 和证据，不能用数据库登记 branch 推断最后 checkout。

完整准备工作区通过容器内压缩 tar 回传，再由 `extract_output` 安全解压到原 `prepared-workspace` 路径。此输运不排除任何文件；`prepared-workspace.tar.gz`、独立 stderr 和回执中的命令、退出码、超时、字节数及 SHA 保留具体失败依据。主程序和独立读回已经成功，但最后输运失败时，原 attempt 仍记为失败，不能直接把状态改成 `prepared`。

同一已停止准备容器的完整导出和本地解压都已另行取得时，可以只接续输运。导出回执须绑定 `container_id`、`image_id`、`package_sha256` 和 `source_attempt`，记录成功退出、起止时间、归档字节数与 `sha256`，并明确 `container_restarted=false`、`models_started=false`。`source_attempt` 使用绝对路径，或相对导出回执上两级目录的路径。解压校验回执引用实际 `archive`、`archive_sha256`、`destination` 和原读回的 `preserved_files` 数量，要求 `mismatches=[]` 及相同的无重启、无模型事实。沿用实际导出及安全解压留下的回执，不补写成功观察来代替缺失原件。

```sh
python3 -m lab.arc_bench.recovery --complete-prepared-transport \
  runs/<实验>/<操作>/preparations/<准备ID> \
  runs/<实验>/<完整导出>/receipt.json \
  runs/<实验>/<完整导出>/validation.json
```

这个纯本地入口核对原失败 attempt 的规格、输入、包和 runner SHA，保存的独占断网隔离与停止身份，以及原 `--prepare-only` 和数据库、配方、Git、二进制读回。它再比较归档与解压工作区的全部目录、文件字节、执行位和链接，调用现有 `verify_launch` 后才原子发布派生准备回执。原 attempt 的失败回执和输运半成品保持，`transport-reentry-*/` 保存失败回执副本、证据哈希及派生回执。入口不访问 Docker，也不重新执行主程序。完成后重新执行同一 `operation prepare`，消费已准备回执完成冻结，再由 `operation run` 的现有启动门控接续；准备接续没有扩大模型、费用或运行范围。

本地自动官网重放须另在规格中冻结 `replay.defaults` 或 `replay.jobs` 的 Competition 参数。跟随者仅消费本次 manifest 的实验和 job，保留每个来源 run 的重放包、同一官网 journal 与结果回执；普通本地操作省略 replay 就不会评分。重入继续同一 journal，不把不确定 POST 当作未执行。collector 的确定失败保留已启动 run 和原错误，停止当前自动接续；修复前提后显式再次 `operation run`，不会每五秒自动重启。

选择执行方式时，先区分三类运行：

| 方式 | 输入与产出 | 结果归属 |
| --- | --- | --- |
| 新 Harness 实验 | 冻结 Harness、需求和模型条件，重新生成应用，再评分 | 本次冻结 Harness 的完整执行结果。 |
| 工作区断点恢复 | 保留原始 ZIP，在副本中恢复代码、会话和协作状态，完成必要的剩余工作 | 原始运行加明确恢复改动后的结果，不是原版本独立完成。 |
| 完成应用重放 | 冻结已完成的应用，用既有 replay 打包入口部署评分，不再调用生成 Harness | 指定应用版本的评分；不能冒称一次新的端到端生成成绩。 |

### 完成工作区与未完成接续

官网工作区用一条命令导出并准备恢复包：

```sh
python3 scripts/package_completed_recovery.py \
  --journal runs/<实验>/<官网journal> \
  --output runs/<实验>/recovery/recovery.zip
```

入口从 journal 的 `inputs.json` 和 `state.json` 选择旧 run，核对冻结包 SHA256、完整 manifest 和已保存终态；多题 journal 添加 `--task <题目>`。它复用 Playground 网站 Cookie，只读下载 `/api/runs/<run>/workspace/template-bundle`，默认直接使用冻结包内的 `runtime/bin/braid`。需要接续尚未完成的生成时，显式添加 `--continue-generation`。这个打包过程不启动模型或官网 run。

原始 ZIP、下载 HTTP 状态及时间、每个成员的 CRC/SHA256、冻结包和恢复包索引保存在默认的 `<新包文件名去掉.zip>-evidence/`，可用 `--evidence-dir` 指定新目录。目录和输出必须尚不存在，原件不覆盖、不改权限或内容；下载失败保留响应原文和传输错误。使用已经保存的原件时添加 `--workspace <原ZIP> --workspace-sha256 <预期SHA256>`，入口复制它到独立证据目录。此时收据明确说明 run 关联来自选定 journal，ZIP 本身未嵌入官网 run 身份；保存的终态也不会冒充新取得的状态。

显式修复版二进制仍可用 `--braid <Linux二进制>`；`--braid-source <源码tar.gz>` 是可选复现材料，不是执行依赖。默认二进制保留冻结 manifest 的源码身份。显式覆盖二进制时，新 manifest 的 Braid 来源只记录本次 binary SHA 和可选源码 tar SHA，不继承旧 revision/source_sha256；原源码身份保存在 `recovery-source.json.frozen_braid_source`，不能把源码 tar 的容器哈希当源码树哈希，或把旧 revision 当新 binary 的来源。没有 journal 的历史用法仍支持 `--source-run-id <旧run> --base-package <冻结包> --workspace <原ZIP>`，来源已停止的判断由对应 packet 负责。

新包携带原工作区与哈希；默认入口恢复原 Braid run、确认所有工作项终态，再导出旧 `main`。每个新包使用独立的 Competition journal 和当轮已冻结的费用模式，旧 run 不会原地恢复；具体来源及身份见当轮 packet。默认模式发现开放工作项会拒绝生成，防止一次重评意外调用模型。

自费迭代遇到未完成的生成中断时，保留原始 ZIP 和完整 Braid 工作区。打包命令添加 `--continue-generation` 可准备未完成工作区的接续包；它恢复原模型与工具环境、Git 索引及保留文件，调用原 `braid local` 请求，不改数据库生命周期。此模式只用于来源执行环境已经停止的快照；恢复入口显式调用 `braid local REQUEST --offline-resume`，由 Braid 撤销旧执行身份、修复输入重放并准备会话，Factory 不修改数据库。未完成接续已有平稳续进的官网实际反馈，但该 run 后由用户主动结束，没有恢复后的完整评分结论；已完成恢复模式另有生成、部署和评分证据。具体范围见 [设施 packet](../../tasks/experiment-infrastructure/packet.md#验证与限制)，已有 g03–g05 手写包不作为此入口验收。原始证据保持只读，接续时新增的通知要标明来源，不能改写成历史上已经送达。

I13 的归档回执将恢复承诺和原文保存分别记录；即使应用已交付，归档不完整也会保留 `work` 与 `recovery-workspace.json`。decision 回执不构成已核实的 resumable 检查点。当前未实现其它归档级，不得通过声明 `resumable` 推断完整停止时点已保存。

### 选择检查点并刷新材料

热恢复先确定错误首次出现及开始大规模扩散的时间，优先选择扩散前最近的可恢复检查点，避免把已受影响的上下文和协作状态原样带入修复后的运行。核对检查点内应用与 Git、Braid 数据库和原生会话的时间及相互引用；单独回退应用提交不能代表整个运行已回退。保留当前现场，记录选择依据、会丢弃的有效进度以及缺失材料。没有可确认的较早检查点时，明确记录限制，再按已授权范围接续。

需要把新的技能和原生指令应用于半成品时，使用包含新 variant 材料的 `--base-package`，并同时指定 `--continue-generation --refresh-native-materials`。恢复入口重建宿主拥有的 skills、capabilities 和成员指令，保留旧材料副本、应用工作区、协作记录和原模型配方；Braid 在离线恢复边界重建受影响的原生会话。仅替换二进制而不刷新材料，不代表新技能或提示词已生效。原执行须先停止，每次接续使用新的包和运行目录。

I13 和四个 I14 variant 的刷新使用完整冻结 base 内的 runtime、角色和独立 skills，要求同时包含 managed native 模块、资源 helper 和三项 managed process patch。入口逐项核对原 profile 的 provider、model、reasoning 和上下文参数，保留根成员选择、旧模型定义、native home 和原生 session 文件，仅刷新所属材料。旧冻结 I14 曾在刷新时强制 ARC；当前生产端已移除该供应商约束，材料刷新不代替配方显式通道绑定。两项 CLI 标志仍互斥，历史非 I14 的显式 transport 边界沿用。


接续入口从工作区 ZIP 还原 Unix 文件权限和符号链接。官网导出会把执行文件降为 `0600` 时，冻结包执行位按 manifest 恢复；保留的 `request.pi.executable`、各 binding 的 executable 和 `work/bin/pbb` 按声明恢复 `0755`，要求解析后仍在同一 Braid run 内。原生会话使用旧 `/workspace/submission/runtime` 路径、本地 ARC wrapper 把包放在 `/workspace/submission/agent` 时，入口仅为包内存在的 runtime、support、extensions、tools、agents、skills 建立兼容链接；已占用且指向不同位置的路径会拒绝恢复。修复列表写入 `recovery-launch-paths.json`，不会批量 chmod 文件或改写历史技能、指令和配置。

相反方向的本地来源恢复到官网也支持上述单层布局：旧材料引用 `/workspace/submission/agent`，官网包实际位于 `/workspace/submission` 时，仅在 `agent/` 下建立六个包目录的链接。其它重定位仍拒绝，避免把历史路径猜成当前目录。

只准备现场而不运行 Braid，可在 Linux x86_64、Python 3.12 的实际 ARC 包布局中执行：

```sh
python3 /workspace/submission/agent/main.py /workspace/template/requirements \
  --output-dir /workspace/template --prepare-only
```

准备仍核验完整包、需求和工作区，恢复 Git 索引、已声明执行位和兼容路径，写入 `recovery-preparation.json` 后退出。它不需要模型 key，不启动采集器、Braid 或模型，不改旧 `native/` 归档。可在 `--network none` 容器中按收据的 `launcher_environment` 执行实际 `pi_executable --version` 和各 `binding_executables --version`，核对启动链。这个反馈不能证明模型调用、离线会话恢复或最终评分成功；准备目录也不能再作为全新执行目录使用。

官网遗漏 private clone `.git` 时，入口仍从保留的 `origin.git` 和已发布 ref 重建索引，使用 `git read-tree` 保留未提交文件，记录 `recovery-git.json`；未发布的私有提交历史不能凭文件猜回。自动打包校验不是完整可恢复检查点认证，仍须核对应用、Braid DB/WAL 和原生会话的停止时点及对应性。

I13 本轮已授权的执行模型变更用显式选项 `--continue-generation --replace-braid-deepseek-with-glm`，不能通过替换普通冻结材料暗中应用。仅支持 `pi-braid-i13` 和 `pi-braid-i13-glm-root`：旧 `pi-deepseek-fast` 必须是 `factory26/deepseek-v4-flash`，同一 request 的目标 `pi-glm-fast` 必须是 `factory26/glm-5.3-flash`。例如对已保全本地快照：

```sh
python3 scripts/package_completed_recovery.py \
  --source-run-id <来源执行ID> --base-package <该variant原冻结ZIP> \
  --workspace <一致快照ZIP> --workspace-sha256 <原ZIP-SHA256> \
  --braid <本次Linux二进制> --braid-source <本次源码tar.gz> \
  --braid-source-identity <本次源码文件清单JSON> \
  --output runs/<实验>/model-cutover/recovery.zip \
  --continue-generation --replace-braid-deepseek-with-glm
```

打包仍先核对原工作区与原 base 材料，原 ZIP 不变；receipt 显式记录迁移选项。恢复副本中先保存 `braid-request.json` 和 `braid-state/request.json` 原文，再一致更新旧 profile 的模型、reasoning/context 参数和显示名，追加 `root-only` 使它退出新指派。原 profile ID、成员 login、assignment、worktree 和既有原生历史保留；根及其它 profile、DeepSeek sub-agent 角色、instructions 和 skills 不变，不修改普通 Braid offline guard。`root-only` 对新指派的实际行为还依赖本次 Braid binary 的成员目录实现。

同款 GLM 定义从目标 binding 的原生 template 取得，只补入受影响旧 template 和全部 `<pi-deepseek-fast>-<uuid>` native home 的 `factory26.models`，包括 sleeping/replaced home；旧 home 恢复时不会自动刷新 template。其它 provider、DeepSeek 定义与内部角色保持原样；缺文件、目标定义不唯一或 factory26 transport 不一致会拒绝迁移。`recovery-model-migration/originals/` 保存原请求和原 models.json，`recovery-model-migration.json` 保存前后哈希、profile 变更及全部 home/history 入口。执行准备或正式接续前，由主线保证旧执行已停止。

二进制覆盖时，manifest 不沿用原冻结源码的 revision 或 SHA。原身份保存在 `recovery-source.frozen_braid_source`；`--braid-source` 记录新源码 tar 的容器 SHA，`--braid-source-identity` 逐项核对 tar 中 `braid/` 文件及 `sha256-json-sorted-files` 聚合 SHA，再记录新编译源码身份。辅助源码快照没有提供时，不宣称新 binary 来自原源码。

I13 历史通道切换另用显式 `--override-native-transport`。旧冻结包曾将 I14 继续生成固定到 ARC；当前源码不再固定 endpoint 或主/视觉 key，新配方通过 FACTORY26_MODEL_BINDINGS 明确各原生 provider 的供应商与凭据变量，来源及前后哈希仍归 recovery-native-transport 回执。新生成可按模型分流并拆分 provider；旧共享 provider 的 retained 会话没有自动 provider 身份迁移保证，当前 hook 拒绝需要新增 provider 的恢复。未明确获准的旧源码/ZIP、原模型请求和通道事实保留原身份。

未完成生成接续按实际完整 runtime 能力恢复共用资源环境，不只依赖旧 recovery-source 的声明 flag；`native-managed.mjs` 与 `support/runtime_resources.py` 必须同时存在。已有明确资源声明仍按原约束校验。`recovery-resource-environment.json` 记录能力、启用结果和无 key 的路径环境；这使显式模型切换或仅更新 binary 的恢复也能继续使用资源准入保护，缺少能力的旧包不冒充已启用。

迁移的无模型反馈使用 `--prepare-only` 与断网容器中的真实 Pi RPC：对保留的 session 文件以新 profile 的 `--provider factory26 --model glm-5.3-flash --session <旧文件>` 启动，读取 `get_state` 与 `get_messages`，核对同一 sessionId/sessionFile、新 GLM 定义和历史消息内容。只发这些读取命令，不发送 prompt；原 session 文件始终留在原 ZIP 中，RPC 的新 model_change 只写到验收副本。此反馈不等于 Braid offline-resume、模型请求或最终交付已经成功。

实际接续使用包内 Pi 时间回调与 OTLP 接收器追加本次采集。Braid 结束后重新归档原生会话，原 ZIP 自带的 `native/` 先保存在 `recovery-source-native-<时间戳>/`；`recovery-diagnostics.json` 分别记录采集、归档和清理错误。清理失败仍阻断交付。旧来源和新接续的采集时间段应分开解读，不能把恢复后新增记录当作旧运行的当时状态。

本轮官网信号取证通过 `--with-official-signal-evidence` 同时冻结 collector、运行支持、归档模块及明确提供的统一 Braid binary；依赖沿用原冻结包。恢复开始即建立新 attempt UUID，旧 attempt/日志回执及整个 `process-evidence/` 导向独立来源目录，旧 `result.json` 也移出当前 Braid 状态路径。新 attempt 记录来源 run、workspace SHA、Braid run；平台没有暴露当前 run ID 时，由新 journal 与归档绑定，不能猜测。主 Braid 启动记录 request、PID 身份和实际 wait/exit，保留原 `subprocess.run` 的单进程异常清理策略。新增辅助回执写入失败保留具体 errno 并继续；缺证据不用于自动归因。复制到 `work/bin/braid` 的实际 SHA 必须与包身份一致，校验本身仍是启动边界。

应用生成完成后冻结交付版本，通过官网自费应用重放取得官方评分；本地模拟分数和启动检查不替代官网评分。工作区接续与应用重放分别记录来源，不能把重放分数冒称为一次新的端到端生成成绩。正式参赛提交从冻结 Harness 和需求重新生成，以测量完整执行；自费迭代不因此丢弃可续接的工作区。

## 官网监控

`hosted_monitor --targets <文件>` 接收动态 JSON 订阅，文件为数组或 `{"targets": [...]}`；每项指定 `journal`、`run_id` 和 `submission_id`。操作入口在锁内原子追加订阅；collector 在本地等待期间重读它，远端采样间隔保持不变。已有 run 的身份不能替换，移除订阅也不放弃仍活动的观察。scheduler 拥有接收事实，`monitor/accepted.json` 是统一公开查询回执，包含接收身份、首批原件、逐 run 终态及 collector 生命周期；消费者不猜内部 scheduler 文件名。首批采集和实际身份都成立后才证明观察已接入，操作按自身 run 集完成，不等待其它订阅。`monitor/completion.json` 区分 collector 的 completed、failed 与 interrupted，不能把 collector 的退出当作平台终态。

监控完全由脚本执行，不唤醒审查模型。程序在 run 启动后前 10 分钟每 3 分钟、随后每 8 分钟读取状态和阶段，并下载官网模板导出取得当前 provider 证据；下载保留原 ZIP，允许 10 分钟，不把耗时当成生成停滞。只选择 `template/.factory26/<id>/braid-state/status.json`，历史嵌套状态不参与当前判断。provider_sessions 与 turns 从导出的 DB/WAL 取得一致 SQLite 读取快照，原生文件以来源身份及恢复开始时间划界；导出文件集合本身是否原子仍为未知。终态保存总分、阶段及原件后退出；终态下载失败另记 evidence_errors 并告警，不无限等待缺失的失败工作区。

每批保存实际来源、观察时间、provider 身份与生命周期、native 活动元数据、阈值及未知。默认至少两次采样、30 分钟没有状态或实际活动变化才提示 suspected_stale；这是活动/存活异常提示，语义进度仍未知。已确认本轮 provider 身份后，native 证据持续不可读达到相同时间/样本门槛时报告 observation_missing 并保留原错误，不宣称 stale。sleeping、idle 与明确资源等待分别记录；idle 但 turn 仍 starting/running 不按正常闲置处理。汇总时当前会话优先于导入的历史会话，历史休眠记录不会掩盖当前活动。未配结果的历史 tool call 不证明工具仍执行，不提供无限等待豁免；仅静止一次、token 不增或导入的 running 状态不能触发 stale。状态及故障签名去重通知，原错误保持完整，通知系统接受提醒不证明人已看到。

短题暴露通用缺陷时，先保留全部现场并确定原因，再做有针对性的修复验证。在已授权的官网并行实验中，可按当轮规则取消同轮未终态的 Hackathon 运行；取消需要实际请求及远端状态确认。本地断点恢复应保留进度、受控暂停后续接，不机械沿用官网取消策略，也不在活动进程中无记录更换二进制。合理等待、外部故障与 Harness 缺陷分别处理，禁止无依据反复重生成。

每轮在 task packet 登记题目、模型、来源、费用模式、调度、告警消费者和完成条件。官网默认使用 API、`self_funded` 自带 key、非参赛，不占比赛额度；策略可复用不等于无限付费授权。

执行入口：`python3 -m lab.arc_bench.hosted_monitor <证据目录> --journal <Competition状态目录> [--journal <另一个状态目录>]`。省略 journal 时沿用该目录的 hackathon 或 arc-bench-lite 布局。`--stale-after-seconds` 与 `--minimum-samples` 可调整阈值；旧 `--review` 仅兼容为纯脚本判断，不调用模型。取消选项已经拒绝，监控不自动取消、恢复、提交或收费重跑。历史本地脚本保留原件；当前本地脚本入口见[证据查询](evidence.md#等待反馈与交接)。

## 历史本地 attempt 的恢复

恢复历史 attempt 的采样时，若该 attempt 保存了 `monitor-generation.py`，用该 attempt 的 `generation-monitor.jsonl` 查看最后采样时间，再用 `pgrep -af '[m]onitor-generation.py'` 核对**同一路径**的监控进程仍在；旧采样行不能证明程序仍活着。只在确认该 attempt 没有现存监控进程且两题仍运行时，使用 attempt 的 Python 重新启动其原脚本并保留 stdout/stderr 到 `monitor.log`。脚本从各题 `run.json.started_at` 计算前十分钟每 180 秒、之后每 480 秒的间隔，接续不会重置观察窗；这只恢复采样，不重启生成或模型，也不代替原生 Pi/数据库核对。

两题运行由一次性 `run-experiment.py` 包装时，用户取消会使 `lab run` 返回非零；包装脚本不能仅凭子进程退出码把取消记作实验失败。新 attempt 的包装脚本应在非零返回后读取两题 `run.json.phase`：均为 `cancelled` 时记录外层 `cancelled` 并跳过评分，其余故障保留原错误。旧 attempt 的 `execution.json` 和脚本保持原样，报告同时展示外层错误与逐题取消事实。

## 冻结应用与阶段提交回放

官网未公开测试时，可将已完成的本地应用封装为产物回放包，通过非榜单运行取得隐藏测试反馈。构建仍在 WSL 执行。每题生成完成后立即单独打包并提交官网，以 `self_funded` 评分，不等待同批其它题目完成。多题重放包仍可用于已全部完成的历史应用，但不能给同一需求放入多个候选应用：

```sh
python3 -m lab.arc_bench.package_arc_replay \
  --run ../factory26-official-local/runs/<matrix>/<github-run-id> \
  --output ../factory26-official-local/<variant>-artifact-replay.zip
```

打包器依据已发布的应用声明判断可复用性，即使后续 Runner 部署或评测失败也可使用已完整发布的应用；旧运行没有声明时会校验现存标准应用并标明是在打包时导入。它不携带依赖缓存、Agent 会话或环境凭据。应用的持久化数据保留生成结束时的状态，打包器不替应用重置数据或修改实现。`replay-manifest.json` 记录来源 run、需求 SHA256 和归档文件哈希。入口根据实际传入的 `requirements.yaml` 哈希选择应用，等待 3 秒后将文件交付到输出目录；不匹配时直接报告实际哈希，避免对错误版本的需求评分。官网再负责安装依赖、构建、部署和运行测试。

生成尚未完成时，获得阶段评分授权后可显式冻结已提交的分支。此模式必须同时指定 `--git-repo` 与 `--ref`，只接受一个来源 `--run`；来源 run 提供题目和原生成身份，应用内容只来自该 Git 提交：

```sh
python3 -m lab.arc_bench.package_arc_replay \
  --run runs/<experiment>/generation/runs/<run-id> \
  --git-repo /path/to/braid-state/origin.git --ref refs/heads/develop \
  --output runs/<experiment>/phase-replay/<task>-provisional.zip
```

打包器将 ref 解析一次为 commit，再用该 SHA 执行 `git archive`，在临时目录复用原有应用清单与打包流程，不读取正在写入的工作树，也不停止生成。清单的 `source_application` 保存 `provisional: true`、Git 仓库/ref/commit 和来源 run，`provenance` 为 `git-archive-provisional`；这些身份继续传入官网 journal。阶段应用不冒充已发布交付，不生成 published receipt。只有提交中的持久化文件会进入快照，未提交的数据不另行补入；缺少标准 `frontend/package.json` 或 `backend/package.json` 时直接失败，不能替生成 Agent 补代码或调整数据以取得评分。

阶段 ZIP 和官网 journal 使用独立路径，名称注明 `provisional`，仍只走 `self_funded`。已有上传或创建结果不确定时，先读取对应 journal 和官网状态，不重复上传。阶段评分与生成完成后的正式应用评分分别记录，隐藏评分反馈不传给仍在生成的 Agent。

重放沿用 [Competition 的 journal 与比赛锁边界](competition.md#参赛包与平台边界)。监控退出时先读日志并刷新原 run 状态；已经终结则 collect，仍在运行才接续同一 journal 的 watch，不重复创建 run。

提交名称使用 `artifact-replay`，关闭“使用比赛额度评测”。回放入口不调用模型。2026-09-24 实测 API 密钥表单接受 `artifact-replay-no-model-calls` 占位值，两题 API 的 `billing_mode` 均为 `self_funded`，应用均成功交付和部署；评分是否完成需继续检查测试终态与计数。官网回放耗时和模型开销不能当作原生成性能，生成成本继续取自对应本地 run。保存官方 run 链接、测试通过数、评分和具体错误，并与回放包 SHA256 关联；不要把隐藏测试反馈传入仍在生成的 Agent。
