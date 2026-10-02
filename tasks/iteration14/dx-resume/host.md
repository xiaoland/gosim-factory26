# I14 新执行域宿主交接调查

2026-10-02 本子任务只读调查，不停止、CONT、TERM/KILL 或重启任何 owner/container，不释放旧 registry，不发送模型请求，不建立 Console/collector。主线随后选择优先调查 development-2，WSL 原现场继续保留；baseline 的用户主动暂停保持。

原件目录为 `runs/iteration14/dx-resume-20261002/host/`，总入口 `handoff-facts.json`。SSH 连接超时 8 秒、keepalive 5 秒/2 次；远端各 subprocess 25 秒，总调用 60 秒。两宿主读取均 exit 0、stderr 空；没有无界重试。

WSL / development-1 的 boot 仍为 `0569f94d-32fc-4b45-8a89-ba4df70f94c3`，daemon `0c1d4a2e-b921-49be-a075-1e30571f0995`，Debian 13、12 CPU、Docker 内存 16,745,209,856 字节，本次 MemAvailable 12,652,416 kB，磁盘余 55,822,663,680 字节。原 runner 镜像 `sha256:a2d86e7815bcfe5d6f1da6414ad03b4c31f2cfaed070c80be2479a9027d47c8e` 仍在。Docker 32 容器，16 Running 且全部 Paused；这不是 stopped。

| 来源 | 实际生成容器 | 状态 | volume |
| --- | --- | --- | --- |
| baseline `3a4653d711c3d9` | `9a7806217deb...` | paused / Running=true，2 GiB / 2 CPU | `factory26-attempt-a2ba095e2c2bbcf01ad6096593590328` |
| reviewer `9bce3a1fd0e294` | `b32fc9ef0de3...` | paused / Running=true，2 GiB / 2 CPU | `factory26-attempt-64ad78eed69bca91e8c4183abdc004cc` |
| cleaner `51de01f10f57f3` | `72d333b81c6f...` | exited 137，非 OOM | `factory26-attempt-5c4c7cd2a753dc62eccd9ab2d9a6a279` |
| GLM GitHub `a94a67b4b3d85b` | `ae2bf1d8de95...` | exited 137，非 OOM | `factory26-attempt-103cddb843dadc54cd7814a43618f397` |
| GLM Sheet `8046cfb0695023` | `b2d7c7e648c1b...` | exited 137，非 OOM | `factory26-attempt-2ed9fe8619150b94136a6b51d45e56ed` |

WSL 旧 registry 的完整源路径记录在 `legacy-registry-source.txt`；只读副本 `legacy-registry-snapshot.json` 仍有三项 reservation。owner PID 为 baseline 53942、cleaner 54384、reviewer 54958，均 T / alive。dispatcher 53680 为 Ts / alive。三个 operation worker 53720/54127/54504、controller 53723/54133/54511、adapter 53733/54142/54525、monitor 53820/54248/54636 仍 alive。`wsl-writer-identities.json` 保存 16 份 canonical 来源路径、SHA、host/boot/PID/start 与新 core 独立 process_state 观察；`mac-processes.json` 另保存实际进程树，包括三项 docker run 子进程 57618/58895/58504。SIGSTOP 未退役、cleaner container stopped 未释放其 owner。

WSL 新 authority 至少需要受控退役全部旧派发入口、controller/adapter/owner 及其未收尾 docker run，明确关闭在途窗口，然后保全并停止相关旧生成物理资源，依据原件释放旧 reservation。当前域还保留 16 paused accessor/helper/历史资源，新 authority 的 physical 计数会占槽；不能为本轮擅自停止无关现场。尚未执行上述动作，也未发布 WSL authority-handoff。user-owned Flash/GitHub 官网 owner 不纳入本次控制范围。

已有 cleaner 完整保全继续引用 `runs/iteration14/cleaner-hidden-context-20261002/handoff.json`、`source-stop.json`、`cleaner/workspace.tar`、`source-git-identity.json`、`source-native-identity.json`，不重复导出。GLM 继续引用 `runs/iteration13/i13-2-20261001/arc-hot-recovery-20261002/` 的保全与 handoff。baseline/reviewer 的 Mac official-generation/template 无 .factory26/Git/native，不能把这些传入骨架当检查点；实际原件仍在上表 WSL volume。本次没有取得完整导出，未补造历史；公共 checkpoint 要求 stop-evidence，paused 不能满足。按主线指示暂不以大体积导出拖延新域工作。

Development-2 经 `sfp7-ws.localhost` 实读为 Fedora 43、boot `723c6424-3da1-426a-944d-e4aa9aee00b6`、daemon `e316f857-fe3d-4e7b-8236-9376f063fedc`，8 CPU、Docker 内存 16,323,756,032 字节，MemAvailable 13,639,448 kB，余盘 181,482,479,616 字节。已有 runner `sha256:3d51899c61e6464242a7545a1badb6445f368f4757828fd36f040c6954b56681` 确实在库。唯一容器为用户 Redis `db_design_service-redis-1`，无 Factory 标签；唯一 volume 为其数据，无 Factory 资源。slots=5 在现 admission 算法下将 Redis 算 foreign，首次最多可用四槽。

`dev2-facts.json` 保存宿主/daemon/容器/volume/image/process 和默认 registry 不存在观察；Mac 默认及 dev2 当前用户/root 默认 legacy registry 均不存在。`dev2-local-record-scan.json` 在 I13/I14 和 Mac 默认 admission 目录有界读取 12,058 个不大于 1 MB JSON/JSONL，排除 runtime/依赖/native/工作区/原始采集目录，只发现 dev2 候选 recipe、镜像构建及交接记录，没有 dispatch/owner/旧 registry。Mac 和 dev2 当前进程未出现 dev2 Factory writer。该范围支持当前未观察到旧 writer/在途；不能证明未知外部 controller 或自定义 registry。

现公开 `authority-handoff` 必须读取已存在且显式为空的 legacy registry，没有首次未使用域入口。没有伪造空旧 registry 或直接写新 handoff。合法下一步由主线明确首次域的公开生产合同并消费这些独立原件，或继续保存该限制；不能将 registry 不存在改写成历史已释放。主线明确方案前，本子任务不再控制现场。
