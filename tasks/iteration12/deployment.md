# I12 从零部署与退役接续记录

当前决定是从零生成两题。旧接续已经停止并退役，详细记录保留在后文。新运行只使用同两份官方 Hackathon requirements、当前 I12 冻结材料及自有 BigModel/Kimi/DeepSeek 网关；每题仍限制 4GiB/2CPU，以 3+8 间隔观察，不执行本地评分，不带入 I11 应用代码、Git、Braid 对象、native 会话或隐藏评分。

新现场在 WSL `runs/iteration12/fresh/<case>/workspace/official-generation/template`。准备阶段该目录只含 `requirements`。`runs/iteration12/fresh/prepare.py` 通过共享只读 submission 的标准 `/workspace/submission/agent/main.py --prepare-only` 做真实准备，输出到独立 prepared-output，模型网络禁用。标准入口每次分配新的 run ID；prepare-only 不初始化 Git/Braid DB，也不将其虚构为已启动 state。正式启动仍调用标准 main.py/run.py，由其初始化空应用仓库、Braid 与 native；不复用准备目录、恢复入口或旧 run ID。

新 lab 配方是 `runs/iteration12/fresh/github-matrix.json` 与 `sheet-matrix.json`，容器边界脚本是 `fresh/container.py`。脚本只复用既有 ARC 包装、model_environment 与资源回收，拒绝 actual template 中除 requirements 外的任何内容，并核对 official requirements 与冻结 Braid identity。完整工具/runtime 继续共享，无重复 runner/browser 安装或大 ZIP 展开。生成完成后由既有 ARC wrapper 保存应用产物；不会执行本地评分。

首个标准准备在模型启动前发现 readonly 包验证缺陷：`verify_package` 对已经正确的 755 文件无条件 chmod，报 `OSError: [Errno 30] Read-only file system: .../arc-runtime.pyz`。主线已将其改为仅缺少执行位时补权限；哈希、载荷完整性与 ZIP 权限修复语义保留。原错在 `fresh/github/first-prepare.stderr.log`。修复后的完整 manifest SHA256 是 `81d24d651780ab9ac9be14630e4a68d5d2a949ea105fd465a7372edb3cad7964`；Braid binary 仍为 `190c74bd24db7e969ae25b41ef541e322ec1775c7b445949c439f9c2e4a7398c`。退役制品的旧 support、manifest 与材料身份另留在 `deployment/stopped/materials/`。

两题标准 prepare-only 已实际成功，exit code 均为 0，网络禁用，输出独立于 generation mount。准备前现场快照、官方输入哈希、标准入口及 profile 身份见 `runs/iteration12/fresh/preparation.json` 和 `entry-identity.json`。主线确认新版 React Console 生产构建可用后，于 2026-09-30 明确授权启动；两个从零 run 当前已启动，旧接续只作为退役证据保留。

| 题目 | 实际 lab run | 实际 Braid run | 容器 / 宿主 PID | lab / watcher PID |
| --- | --- | --- | --- | --- |
| GitHub | `pi-braid-i12--hackathon--github-715fa714f396de` | `20260930-035653-f3702b83` | `f26-fresh-715fa714f396de` / `1766311` | `1765885` / `1768459` |
| Sheet | `pi-braid-i12--hackathon--sheet-8559b80ecb7f15` | `20260930-035654-b1b8ead7` | `f26-fresh-8559b80ecb7f15` / `1766366` | `1765904` / `1768480` |

实际 state 是 WSL `/home/yyh/Development/factory26/runs/iteration12/fresh/<case>/workspace/official-generation/template/.factory26/<实际Braid run>/braid-state`。两题分别由标准入口初始化，seed commit 都是 `0643b8f4738697024fbc19e2265bf5412c5376a9`，`git ls-tree -r <seed>` 均为空；这两份独立初始化的空 tree 不含 I11 对象。完整 request、input、空 seed 及来源回执见 `fresh/from-zero-identities.json`。初始 template 只含 requirements，没有 .git、Braid DB 或 native JSONL；准备输出未搬入实际 template。

两题已有真实 `factory26 / glm-5.3-flash` 响应与工具调用：GitHub 已保存根响应于 `04:01:58.468Z` 写需求与设计文档，Sheet 于 `03:59:14.105Z` 建立共享分支并查询 issue/comment 命令。这里的时间是原始根 native 文件中首条已保存 assistant 响应，不能证明是整个运行最早响应：两个原始文件开头缺 session、model_change 和 user 记录，首行已有 parentId。第一次采集器只读 model_change 导致 models 为空；现已从 assistant 自带的 provider/model 补齐，并保留原采集回执。`fresh/first-responses.json` 明确记录这个证据边界，未泛读或输出 thinking。真实 state request 与 physical instructions 均包含人工介入研究条件，prompt 指向当前 input，未继承 #333/#567 评论；配置模型仍为 DeepSeek v4 flash 与 GLM 5.3 flash，均 high。

`fresh/launch-receipt.json` 保存完整容器 ID、image ID、资源限制和 watcher 命令；`fresh/deployment-status.json` 保存当前 inspect 与观察摘要。两容器 Running=true、Paused=false，watcher 存活；当前已记录四次采样、相邻间隔 180 秒，下一阶段由同一既有 watcher 转为 480 秒。最近采样无 blocked owner。观察入口是 WSL `runs/iteration12/fresh/watches/<case>/watch.jsonl`，原 lab 入口是 `fresh/<case>/generation/runs/<实际lab run>`。主线已将独立 Console bridge 登记到 fresh registry，使用 `i12-fresh-github` / `i12-fresh-sheet` 及同一冻结 binary，通过对应容器执行真实 CLI。部署未写入验收评论或虚构任务。

当前接上的 watcher 是既有 `lab.analysis.factory watch` 状态采集进程：读取 run phase、active turn、pending event 与 blocked owner，写 JSONL；遇终态退出 0，遇确认 blocker 退出 2。它不审查模型语义，不主动通知主会话，也没有接入常驻语义审查 Agent。Lab controller 继续记录真实运行终态；主线需要通过既有终态入口或上述记录取得后续结果，不能把 detached watcher 自然退出描述为会主动反馈。

以下为已经停止的旧接续历史。

用户已授权 I12 修复、从 I11 摘剪及实时 console 人工介入；主线于 2026-09-30 明确通知“材料冻结可以启动”。本部署只接续两题本地生成，不执行正式参赛或本地评分，不提交。模型与 gateway 沿用 I11 自有 BigModel/Kimi/DeepSeek 配方，每题容器限制 4GiB/2CPU。

实际状态目录在 WSL `/home/yyh/Development/factory26/runs/iteration12/recovery/<case>/workspace/official-generation/template/.factory26/<retained-run>/braid-state`。GitHub 保留 `20260929-042409-1202e245`，Sheet 保留 `20260929-042409-811f18d4`。恢复来源与弃用进度以 [recovery.md](recovery.md) 为准；不把 I11 最终交付反向拼入此现场。

两份 Mac 摘剪副本通过 tar 流式传入，无第二份 workspace ZIP，保留 Git、Braid SQLite/WAL、physical、native、未提交文件、符号链接与权限。WSL 不具备 rsync，首次 rsync 在传输前失败，随后采用 tar；GitHub tar 的 macOS provenance 扩展属性产生警告，不影响文件内容。排除历史 node_modules、`work/cache` 和旧 `telemetry.sqlite*`；后者仍完整留在 Mac 同一 template 中，新 WSL collector 建立独立采集段。分析跨段时应分别读取 Mac 历史 DB 和 WSL 新 DB，不把新段数据缺少历史解释为会话证据丢失。

当前 OPEN 工作树中已有 node_modules 已从同一源副本传入；缺依赖的 GitHub issue-10 与 Sheet issue-4 仅在根/前端/后端 package.json 与 pnpm-lock.yaml 逐字相等后从对应 PR 工作树复制。网络安装次数为零，实际复用耗时见 `runs/iteration12/deployment/dependency-reuse.json`。其它历史 PR 依赖保留于 Mac 来源，不在 WSL 重复展开。I10/I11 原件未删除、未改动。

共享 `/home/yyh/Development/factory26/runs/iteration12/deployment/shared-submission` 以只读 bind 挂载至 `/workspace/submission`；每题独立 generation bind 至 `/workspace`。runtime 来源为 I11 `20260929-feasibility/base-agent.zip`，解压一次，替换最终 I12 全部小文件、当前选定 skills/support 和 Linux Braid。Braid SHA256 为 `190c74bd24db7e969ae25b41ef541e322ec1775c7b445949c439f9c2e4a7398c`；完整来源见 `runs/iteration12/build/build-identity.json`。材料清单见 `runs/iteration12/deployment/material-identity.json`。

`continue-in-place.py` 复用既有 I11 接续入口与 `submission/recover_completed.py` 的 native 刷新逻辑。先在无网络真实容器以 `I12_PREPARE_ONLY=1` 重建 skills/capabilities、profiles user_instructions、bindings、角色模板、pbb 与预算 launcher；保留旧材料、旧 request 和 native。Profile ID 及全部非 instruction/window 字段必须与保留配方相等。准备成功后再次启动同入口时只核对冻结 agents/skills/binary 身份，继续原 Braid run。没有引入额外配置或全局恢复状态机。刷新与配方回执在各 run 的 `i12-native-refresh.json`。

console registry、CLI、HTTP 与浏览器只读核对由独立 console 工作完成；WSL 服务 `127.0.0.1:8765` 和 Mac SSH 转发可用。本部署不覆盖其 registry 或人工操作记录。Lab 与 watcher 将记录实际 PID/container 和终态；默认前十分钟每三分钟、此后每八分钟采样。Running 标签只表示外层运行，实际接续需用新模型响应、输入消费和后续工具行为证明。

2026-09-30 11:35 左右，用户将 I12 改为从零实现；主线要求“立即暂停两条当前I12接续运行并保留workspace/native/DB/日志和runtime，不继续消耗模型”，本接续方案和输入随之退役。主线先暂停两个容器；部署侧 inspect 确认 `Paused=true`，没有 unpause。随后复制同一暂停时点的 DB/WAL/SHM，调用既有 lab stop/cleanup。两条 run 均已 `cancelled`、runner exit `-15`，容器 absent、gateway binding revoked，两个 watcher 都记录 cancelled 后自然退出。I10 两个 paused 容器仍在，I11 最终交付未动；停止操作当时尚未启动从零实验。

| 题目 | 已停止 lab run | 原容器与宿主 PID | watcher PID |
| --- | --- | --- | --- |
| GitHub | `pi-braid-i12--hackathon--github-690b8b3f871be2` | `f26-continue-690b8b3f871be2` / `1743119` | `1745047` |
| Sheet | `pi-braid-i12--hackathon--sheet-6c9d2806b4fac4` | `f26-continue-6c9d2806b4fac4` / `1743605` | `1745058` |

两题确有模型响应，不能把这次暂停解释成未启动：GitHub 根在 `03:33:15.825Z` 调用 `braid comment view 333`，工具结果 `03:33:17.455Z` 返回完整人工介入正文及 delivered 回执；Sheet 根在 `03:33:24.379Z` 调用 `braid comment view 567`，工具结果 `03:33:28.295Z` 同样返回正文及 delivered 回执。停止时两个对应 wake event 均为 consumed。两根 native 的 model_change 都是 `factory26 / glm-5.3-flash`；其他实际响应为 `deepseek-v4-flash`，与保留配方一致。未完成交付或评分，不把后续人工停止作为 Harness 失败结果。

首响应与消费回执在两端 `runs/iteration12/deployment/stopped/receipt.json`、各题 `identity-and-response.json`；停止后最终状态在 `stopped/final-state.json`，资源处理原回执在各题 `cleanup.json`。暂停时原始 DB/WAL/SHM 位于 `stopped/<case>/raw-db/`，查询工作副本在 `query-copy/`。完整原生 JSONL、physical、Git 与日志仍在上述恢复 workspace。旧 telemetry 仍留于 Mac 来源，新 WSL telemetry 段仍在本次恢复 workspace。

WSL lab 原始入口为 `runs/iteration12/deployment/<case>-generation/runs/<run-id>`；该 run 的 `workspace/official-generation` 通过显式符号链接指向对应独立恢复现场，避免再复制一次应用。`launch-receipt.json` 保存真实 Docker image/container ID、4GiB/2CPU、lab PID 与 watcher 命令。`watches/<case>/watch.jsonl` 保存按 3+8 间隔生成的记录；本次在首十分钟内由用户停止，未进入八分钟采样段。

部署错误全部保留：WSL 缺 rsync 后改 tar；lab labels 不接受 JSON boolean，首次计划在分配 attempt 前报 `ValueError: labels must be an object of string keys and values`，修正为字符串 `"true"`，runtime result 仍保留 boolean；原错见 `first-launch-error.txt`。暂停时 SQLite online backup 等待冻结进程的锁，采集进程被主动终止，改为复制暂停状态的 DB/WAL/SHM；未把不完整 online backup 当检查点，未恢复模型来解锁。冻结材料 manifest SHA256 为 `d1e3248f781fd8abf9c51a9aae168442395a5d0b51775f9fe3265f7e0f7dd11c`。

传输前后核对没有源码/native 文件内容变化，Git refs 与 profile recipe 相等；SQLite 读者清理了空 WAL/SHM。Sheet 的 DB 文件采样已包含随后由 console 写入的人工评论 #567，属于已记录的人为输入，不是传输损坏。具体差异见 `transfer-comparison.json`，console 写入原记录由主线保留在 `console-actions.jsonl`。

共享 runtime 与冻结小文件保留，可供后续从零方案明确选择复用。WSL 停止后约剩 4.7GiB；该接续现场仍完整保留，不自行删除或将旧现场当从零输入。
