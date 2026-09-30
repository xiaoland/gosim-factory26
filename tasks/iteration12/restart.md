# I12 2026-09-30 从零重启

## 当前状态：已暂停

用户要求“可以暂停 I12 了，内容已经太多，我已经看到很多问题”。2026-09-30 15:59:13 CST实际确认下面两条当前容器均Running=true、Paused=true；全部容器内Agent会话及Braid定期检查一并冻结，没有取消、清理或重启，不自动恢复。
代码、Git、Issue/PR、原生会话及内存中的运行现场留在原处。暂停时的 `braid.sqlite3*` 文件复制到WSL `runs/iteration12/restart-20260930/paused-20260930/<case>/raw-db/`，原始Docker身份、状态和路径见同目录上层的 `pause-receipt.json`。
该文件副本用于复审，不单凭它宣称具有完整冷恢复检查点。以下启动和进展记录均为暂停前事实。
Console整体暂停/恢复以及暂停后的人工读写能力纳入 [I13 packet](../iteration13/packet.md)，本次紧急暂停不等同该产品能力已完成。

## 启动事实与历史过程

下面按当时顺序保留准备、受阻、启动和观察记录，其中“下一步”“尚未启动”描述对应历史时点；当前暂停状态以上节为准。

用户授权原话：“好的，现在可以启动 I12（考虑从0重启了）”。本次范围为同两份官方 GitHub/Sheet requirements、自有 BigModel/Kimi/DeepSeek 原配方，两题各 4GiB/2CPU；不执行本地评分，不使用参赛额度，不恢复旧运行。

2026-09-30 部署准备完成。旧 `f26-fresh-715fa714f396de`、`f26-fresh-8559b80ecb7f15` 经 Docker inspect 确认为 paused，持久现场仍在 WSL `runs/iteration12/fresh/<case>/workspace/official-generation/template`。先逐字复制暂停时的 `braid.sqlite3*`，记录 Docker mount、Git refs 和 native 路径，再通过既有 `lab stop`/`lab cleanup` 停止旧外层及容器、撤销旧网关绑定。两条 lab run 已 cancelled、runner exit -15，容器 absent；旧生成文件、Git、native 保留在原位置。原始回执在 `runs/iteration12/restart-20260930/stopped/`。

新现场位于 WSL `/home/yyh/Development/factory26/runs/iteration12/restart-20260930/<case>/workspace/official-generation/template`，当前只含官方 `requirements`，没有 Git、Braid DB 或 native 会话。复用 fresh container、矩阵与 3+8 watcher，并使用新目录及 `f26-restart-` 容器名。矩阵尚待主线给出新冻结 binary/shared-submission/material identity 路径后更新；尚未启动模型。

可复用运行 image 为 `arcbench-local-submit:latest`，身份 `sha256:840105914e6e166ba1eefa4bd3af1682e795d2e515497198142010c1e79eb19d`；Rust 编译 image 为 `rust:1.93-bookworm`，身份 `sha256:78a50754b62786434bc4ebfd874ef382348701b5f01b2c0d21b8e17cfad97969`。Cargo registry 与 target volumes 分别为 `/var/lib/docker/volumes/factory26-cargo-registry/_data` 和 `/var/lib/docker/volumes/factory26-braid-target/_data`，旧编译源码入口为 `runs/iteration12/build/source`。准备时 WSL 可用磁盘约 3.3GiB；不重复展开完整 runtime，不修改旧 shared-submission。

Console 原暂停 registry 只读留存为新目录 `console-runs.paused.json`，其 DB/Git 路径保持原现场。正式新 registry 必须在标准入口分配实际 Braid run 后生成，主线负责切换 bridge/UI。

下一步：收到主线冻结信号后更新矩阵 identity，以标准 main.py/run.py 启动两题，核对容器与限制、空 seed、新 DB 和首条真实模型工具行为，再交回启动证据及 watcher PID。watcher 只记录状态并终态退出，不会主动回传主会话；主线另接获授权 run-monitor。

主线随后给出新冻结信号：Linux Braid SHA256 为 `38c68450fa93399e7dabd3c4c912410a503e59152cb13f3d3c724ce7d9fc708d`，编译身份在新目录 `build/build-identity.json`。新 shared-submission 仅硬链接不可变 runtime 树，small 与 manifest 独立复制；freeze 前 unlink braid 再 copy，新 manifest SHA256 为 `2efe2ed0d09cb92b3afb03994a5fdddba5957a5e916f33a37a3754df82e7da66`。旧 binary 与 manifest 的原 SHA256 均保持不变。

冻结脚本第一次因 WSL 顶层没有 `scripts/agent_support.py` 失败；仅修改该部署脚本的 import 入口，使用新 materials/scripts 及既有 deployment/observer/lab/arc_bench 后完成冻结。首次 lab CLI 同时传 experiment-root/runs-root 被拒，未分配 attempt。随后用系统 Python 启动两个 controller，均在 OTLP receiver 初始化时原样报 `ModuleNotFoundError: No module named 'opentelemetry'`，无 run.json、无模型启动。原 controller 与 preparation 日志保留为各题 `pre-model-controller-error/`，使用既有 `/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-08/venv/bin/python` 接续标准启动。

该接续启动 SSH 在返回回执前被对端关闭，后续至少三次连接均在 SSH banner 前被关闭。当前不能证明实际新 run/container 是否已启动，也没有证据证明 Docker 内存、WSL 宿主或网络发生何种变化。禁止重复发起模型 run；连接恢复后必须先核对新目录的 generation/active.json、controller日志、run.json 和 Docker identity，再决定是否接续未执行题目。当前未生成实际 launch-receipt、首响应或新 Console registry，8765 服务尚未切换。主线已接收此具体阻塞，并负责 Mac 路由及 Windows/WSL 入口判别。

用户报告“现在应当恢复了”后，2026-09-30 已恢复 SSH。只读核对证明断连前的既有 venv 启动命令没有执行：两 template 仍只有 requirements，两 generation 无 active.json/run.json，Docker 无新容器，原日志仍是系统 Python 的 OTLP 导入错误。Gateway 4020 与 Console 8765 都无监听、对应旧进程不在。主线此前在 Windows 实际取得 `Wsl/0x80080005`；该错误只证明当时 WSL 入口异常，不推断根因。

部署使用原 `.secrets/models.env`、gateway/env/config/service identity、Python3.12 和既有官网 runtime 恢复同一 4020 网关，当前 PID 4729，已实际监听；没有新建服务身份或更换密钥。首次误读用户侧 llm.env 原样报缺 GLM_API_KEY，在模型启动前修正到原模型凭据路径。两个系统 Python controller 的错误目录实际保留为 `pre-model-controller-error/`，新 controller 使用既有 attempt-08 venv，两题标准 main.py/run.py 已启动。

| 题目 | Lab run | Braid run | 容器 / PID | Lab / watch PID |
| --- | --- | --- | --- | --- |
| GitHub | `pi-braid-i12--hackathon--github-4ad2b95fc11c89` | `20260930-071413-6b4bf7a8` | `f26-restart-4ad2b95fc11c89` / 5217 | 4991 / 5261 |
| Sheet | `pi-braid-i12--hackathon--sheet-ab453a24432a17` | `20260930-071413-6fe73efc` | `f26-restart-ab453a24432a17` / 5181 | 4990 / 5270 |

两容器实际 Running=true、Paused=false、OOMKilled=false，内存4294967296、NanoCpus2000000000，image身份保持不变。Braid从独立新DB初始化；两份 `braid-state/origin.git` 的根 seed 都为 `9e7e3cf`，`git ls-tree -r` 为空。应用根 HEAD 尚未形成交付提交，所以种子从实际 Braid origin 采集，不能把根分支 unborn 当作启动失败。标准入口首次真实 prepare 阶段约一分钟；没有运行 prepare-only、smoke 或模型探针。

两根实际模型均为 `factory26 / glm-5.3-flash`，GitHub首个已保存 assistant/toolUse 于 `2026-09-30T07:14:51.052Z` 查询需求、Git、根 Issue 与 assignee，Sheet 于 `07:14:52.228Z` 查询需求、Git及fetch。两个根均已有实际 toolResult，完整有界原始片段在 `first-model-tool-behavior.json`；不是仅以running标签声称启动。原始 native JSONL 在各自新run/work/native-homes/.../sessions/目录。

新 Console registry 为 `console-runs.json`，使用 `i12-restart-github` 与 `i12-restart-sheet` 的新对象身份。服务PID6073，监听8765，原日志和journal保留；新log/journal在restart目录。实际HTTP GET `/api/runs` 与两题 `/api/items` 均200，两题当时各有一个根 Issue，没有发送评论或改写状态/Git路径。

`launch-receipt.json` 包含真实容器/image/PID/资源和观察命令。两个既有3+8 watcher写入 WSL `runs/iteration12/restart-20260930/watches/<case>/watch.jsonl`，stderr.log当前为空；watcher仅记录状态并终态退出，不主动向主会话回传。主线按这些实际run路径接run-monitor作为结果消费者，单题完成后交官网self_funded应用重放。本部署已交回实际启动结果，不长期等待完整benchmark。

## 15:34 CST：Console看似静止的核对

用户询问是否正常推进、为何页面只有根Issue。实际DB、原生会话与Console API交叉核对表明，两题仍有新工具动作，没有已见blocked或OOM；这不是仅依据容器Running或token增长的判断。
GitHub根先完成需求、设计及原生vision/advisor：vision约122秒，advisor约651秒，后者15:29:37返回。根15:32:39更新正文，15:33:03/04保存两条报告评论，15:33:39创建并指派基础PR #2给deepseek-1；PR原生会话15:34已实际读需求及技能入口。Sheet advisor在15:32:27返回，根15:34:05仍在根据结果编辑architecture.md；该时点尚未创建新协作对象。
Console `/api/items`及`/api/item`实际显示GitHub两项、根两条评论，Sheet仍一项。浏览器实际渲染也显示GitHub PR #2与两条讨论。页面5秒刷新接线存在，本次没有发现读错DB或列表同步故障。
目前Console呈现的是持久化Issue/PR对象，不呈现原生会话的阅读、子Agent调用或未发布文档编辑。因此前期设计与审查虽然在推进，页面可以较长时间保持一个根项；这是过程可见性的缺口，不应将其解释为无工作，也不能据此声称全轮健康或完成。没有为增加界面动静向运行发送评论或改应用。
