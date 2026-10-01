# I13-2 本地首次接续验收

2026-10-01 21:50–22:02 CST。本次两项首次接续未通过：新容器成功部署并完成恢复准备，Braid `--offline-resume` 随后因资源准入延后而退出 1。Docker 均为 `OOMKilled=false`；不能把本次设施故障当成应用完成、有效零分或新 OOM。主线已接回修复，本次验收没有重启容器、改源码或触发模型请求。

| 项目 | GitHub | Sheet |
| --- | --- | --- |
| 新 lab run | `glm-root--hackathon--github-346a6ae5a0e3a0` | `glm-root--hackathon--sheet-efba85c7cfa0f9` |
| 原来源 run | `glm-root--hackathon--github-f9e238c1b698a5` | `glm-root--hackathon--sheet-a45a22ec644204` |
| 保留的 Braid run | `20261001-074336-af6f78cd` | `20261001-104900-3b994a70` |
| 新容器 | `4235cb71bd2581cab27a1b6991812cde82764fe6efc82d526a787a6e9635aa76` | `afde71ca1d09b336f5c3f946ad401279037561b2df57e6652b3d5b709b202693` |
| 新卷 | `factory26-attempt-e744df805fd0829597a7afffa3986cb9` | `factory26-attempt-cba9050e223b64e71d677bff16398268` |
| Docker 起止时间（UTC） | 13:49:29–13:56:29 | 13:49:43–13:56:22 |
| Docker 终态 | exited，ExitCode=1，Pid=0，OOMKilled=false | exited，ExitCode=1，Pid=0，OOMKilled=false |
| Recovery attempt | `8ca9b20b4fd748419c4879ac53ce738a`，prepared | `0ca493d5f7d1438ca19f27056d21d3b6`，prepared |

## 已取得的直接证据

真实 endpoint 是两项 `run.json`、`generation.resource.json` 和 `docker-workspace.json` 一致声明的 `ssh://wsl.win-ws.localhost`，daemon identity 为 `0c1d4a2e-b921-49be-a075-1e30571f0995`。独立 Docker inspect 确认 run/experiment/owner 标签、镜像身份和 `/workspace` 卷均匹配。两项内存上限为 4,294,967,296 字节、NanoCpus 为 2,000,000,000；MemorySwap 为 8,589,934,592 字节。上传状态已从 sending 转为 ready，21:50 两个生成容器均实际 running。

独立在生成容器内读取哈希确认 `/workspace/submission/agent/runtime/bin/braid` 为 `bde76a5adcfa581d0d7e24c9bc9cddc32a07bca49888ee0cf8315f00bee03dc5`，`runtime/native-managed.mjs` 为 `930619cd4e8fc47a3c0b38d6919c2a40bb06d436eefd4894bf49be1ef1f12107`。这是新容器内的部署证据，不仅是本地冻结包声明。

平台 stdout 按顺序记录通过 environment preflight、agent pip install、验证恢复包、解出保全工作区、刷新 native instructions and skills，最后尝试恢复 Braid。GitHub 于 13:56:10Z、Sheet 于 13:56:07Z输出 `Recovery: resuming Braid`。两项 `recovery-attempt.json` 都为 prepared、`evidence_errors=[]`，来源 lab run、原 Braid run 和派生 workspace SHA 与新 lab 的恢复标签一致。

实际资源采样和准入已接线：新 `recovery-braid.log` 中 provider factory 返回了真实 memory charge、headroom、PSI、sample identity 和 `oom_kill=0`，并拒绝物理恢复。GitHub 首次记录 `memory_current=2479677440`、`charged_headroom=1815289856`、PSI full avg10=8.11，状态 pressured。Sheet 首次记录 `memory_current=2142375936`、`charged_headroom=2152591360`、PSI full avg10=30.0，状态 critical；随后 avg10 降至24.57。由此不能把拒绝解释为已经耗尽 4 GiB，也不能仅凭这些值认定 PSI 判据不应生效。

## 首次失败的因果链

两个新 Braid 日志都先记录 `session recovery unavailable`，原始原因是 `session deferred input: resource pressure`。Context reset 随后被保留为 `Context materialization deferred; reset retained`。然而 local run 最终输出 `local run blocked: provider recovery returned an error`，将恢复组的延后结果聚合成 blocked，并返回 1；Recovery 入口再抛出 `subprocess.CalledProcessError`，平台 generation agent 和容器均退出 1。

原始错误、全部压力字段、时间和 ANSI 日志均保留在证据目录。没有以“启动失败”这一泛化分类替换原件。当前判断范围是恢复时的资源延后处理；部署解包与初始化是否造成短期 PSI，以及等待和再准入应如何恢复，由主线的独立复核决定。本次没有改变阈值或重新运行。

Docker 容器终态与控制器 lab 状态是不同事实。22:02 读回时，两项 lab `phase` 仍为 running、`runner_exit_code` 和 `finished_at` 尚为空，而 `generation.resource.json.state` 已是 exited，Docker 已明确 ExitCode=1。控制器仍可能在取回材料；历史或滞后的 running 不能作为继续生成的证明。

## 恢复来源与尚未覆盖的边界

旧执行停止由既有[停止原件](../../../runs/iteration13/i13-2-20261001/preservation/old-execution-stop.json)支持，两项旧容器都是主动维护退出143，卷与归档仍保留。原 Git、Braid DB/WAL、未提交应用工作和 native 历史的完整准备证据归[真实 Linux prepare 观察](../../../runs/iteration13/i13-2-20261001/recovery-prepare/observations.json)。本次新执行已解出相同 Braid 身份并完成 prepared，但没有把先前 prepare-only 的逐项文件结论冒充本次运行后的独立校验。

新容器解出的初始 `status.json` 含原 physical sessions、原 native IDs 和历史 running turn；这些记录属于恢复材料。新 `recovery-braid.log` 没有 `Pi process started` 或 `Pi startup handshake completed`，只取得恢复准入延后。因此 Pi resume/握手延续原 native、旧 native 字节 prefix 在新执行中的独立匹配、原私有 Git 在此次执行后的状态均未完成验收。原件 baseline 仅供后续定向核对，未标成通过。

同样没有取得新模型读取维护输入、读取独立技能、补齐并发布旧 packet 的行为证据。材料已刷新不等于方法已采用。本次也未完成对新执行共享 Portless 的 live owner/HTTP 独立核对；既有 Linux 真实操作的 run owner 结论归[native-runtime.md](native-runtime.md)，不能直接算成这两个恢复运行的通过项。

## 证据入口

证据目录为 `runs/iteration13/i13-2-20261001/first-continuation/`，只记录这次有界验收，没有建立另一个采集循环。

- [首次部署读回](../../../runs/iteration13/i13-2-20261001/first-continuation/deployment-readback-1.json)：真实 endpoint、volume、container、资源限制和running事实。
- [退出读回](../../../runs/iteration13/i13-2-20261001/first-continuation/failure-readback.json)：Docker终态、原始platform错误、Recovery attempt及定向copy回执。
- [控制器滞后状态读回](../../../runs/iteration13/i13-2-20261001/first-continuation/lab-phase-final.json)：22:02时lab仍running，resource已exited。
- [GitHub原始Braid错误](../../../runs/iteration13/i13-2-20261001/first-continuation/github/recovery-braid.log)及[平台stdout](../../../runs/iteration13/i13-2-20261001/first-continuation/github/template/.arc/stdout.log)。
- [Sheet原始Braid错误](../../../runs/iteration13/i13-2-20261001/first-continuation/sheet/recovery-braid.log)及[平台stdout](../../../runs/iteration13/i13-2-20261001/first-continuation/sheet/template/.arc/stdout.log)。
- `github-startup-log-readback.jsonl`、`sheet-startup-log-readback.jsonl` 和两项 `restore-readback.jsonl`：容器内部署哈希、平台阶段与仍为历史的初始status。

本次只写上述独占证据目录和本文件，没有读取凭据、展开完整rollout或引用隐藏思考，没有修改应用、数据库、技能或Console。
