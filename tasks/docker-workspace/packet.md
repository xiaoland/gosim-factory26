# 远程 Docker workspace 传输

状态：实现与实际操作验收完成。用户 2026-10-01 明确要求“处理远程 Docker context 下的 workspace bind mount 适配”，本次具体修改和两台远端最小容器实际操作已授权；不运行模型或 benchmark，不 push。保留其它任务工作区修改。

Mac 持有源码、冻结输入、控制器及最终 run 记录。标准 Docker context 决定容器执行 daemon；代码不理解设备列表。attempt 启动时冻结实际 endpoint、TLS 参数和 daemon ID。Console 的 Unix socket 安全边界保持。

官方 local_submit.py 在本地装配 workspace，随后调用 docker run，再在本地写 local-run.json 和读取结果。仅改变 --workspace 会破坏装配/读取，因此采用 Factory 自有薄 Runner 接线：加载原 Runner，在其 Docker 调用边界上传本地阶段输入、替换挂载、加所有权标签和 cidfile，原 run_container 返回后回收 workspace，再让 read_result 继续。远程 attempt 使用单个 named volume、带标签的 helper 和各阶段子目录；volume Mountpoint 只进入适配器执行回执。输入与输出均保存文件清单和 SHA-256，输出校验及本地发布后才能删除 volume。

资源状态分别记录执行、回收和清理。异常/取消先停止已确认归属的容器，再回收；不可达保持 unconfirmed，回收失败保持远端副本供显式 cleanup 重试。reconcile 不做删除。完整 ID、镜像、标签、volume 和实际 Mount 类型共同核验，不使用 Mac 路径推断远端归属。

OTLP：I13 已在容器内启动 SQLite collector并归档；通用受包装 Agent 复用同一 receiver，在容器 loopback 接收并随 workspace 回收。远程默认不改写为 host.docker.internal；显式网络入口仅由调用方选择并验证。不开放 Mac collector。

实施涉及 lab 的通用 endpoint 冻结/结果收集与资源操作、ARC adapter/矩阵及薄传输模块、runtime Linux 构建入口，以及 CONTRIBUTING、技术说明、本地实验/参赛部署文档。package_agent 已委托 runtime 发送构建输入和 docker cp，无需另建源码同步工具。权威文档移除 arcbox-win 当前用法，历史 packet 原样保留。

验收以编译和实际 Docker 操作取得反馈：两远端同一冻结输入产生相同输出哈希；运行中切换当前 context 后仍操作原 daemon；正常、取消、不可达和回收失败/恢复状态正确；资源最终无残留、旁路资源不受影响。Mac 无本地 Docker socket；本地 bind 分支已用 Debian 宿主的 Unix socket 客户端和临时源码快照实际复核，快照回收到 Mac 后删除，不建立远端开发仓库。证据入口：runs/docker-workspace-20261001/。


## 实现与验收结果

使用 Docker 原生 `volume-subpath`，要求 Engine 26/API 1.45 及以上；两端实际版本为 26.1.5/API 1.45 和 29.1.2/API 1.52。官方 Runner 本身未改动，Factory wrapper 的模块局部代理只接受其已冻结的单次 docker run 形态。取消仍由 lab 控制器 TERM/KILL 驱动，stdout/stderr 和原始官方结果保留。重复指向已有 transport 的 adapter 调用没有清理权；初始 receipt 排他创建，部分分配失败只允许本次 owner token 清理。

输出核验后发布到原本地阶段目录；官方本地 local-run/local-result 额外保存到阶段资源回执旁，避免目录替换影响这两份唯一的本地元数据。cleanup 删除 volume 前再次核对本地输出；已验证后文件被移走时保持 unconfirmed，允许重新回收。当前实现拒绝不能安全归档的外部链接/特殊文件并保留远端副本。远程存储额度未纳入 Mac 文件系统预算；文档要求另外确认远端空间，并将回收 tar、解压副本和原目录计入本地峰值。

| 验收 | 实际观察与证据 |
| --- | --- |
| 两端上传、运行、回收 | `normal-results.json`：两端 requirements-only 最小文件操作经原 local_submit.py 完成，确定性输出 SHA-256 同为 `59e3a0af94e705b0b531a3861eedf822f3cd834c6d3f716a928544f0e358e980`；应用 SHA-256 同为 `38c2e9c8b518be2a3af06d65f595964e46895c7af4bfbb2903fe74bb93e2f3f4`。完整 workspace 保留各自 ID、时间与环境元数据，不将其宣称为相同文件树。 |
| 本地 bind 快速路径 | `local-bind/result.json`：Debian 宿主 Unix socket、原 Runner、非 root UID 1000 实际运行退出 0，资源回执显示 remote=false 与本宿主 bind；临时目录、执行/复制容器及 volume 已释放。Mac 本机 daemon 未创建。 |
| attempt 与 build 固定 daemon | `context-switch-result.json`：attempt 开始于 development-1，中途当前选择变为 development-2，最终仍在原 daemon completed/cleaned。`pinned-build.json`：同样切换后普通 Docker 环境和显式 build 命令均命中原 daemon，另一个 daemon 没有该构建镜像。原当前 context 已恢复。 |
| 正常结束与取消 | 正常两端 completed/verified/removed；`cancellation-result.json`：实际 lab stop 返回 requested，run.phase=cancelled、resource_state=cleaned、recovery=verified。最终 v3 完整链见 `final-run-summary.json`，包含原 run ID/attempt、输入哈希、结果和文件化遥测。 |
| 回收失败及恢复 | `faults/recovery-failure.json`、`faults/failed-cleanup.json`：不可安全回收的输出链接产生具体失败，volume 保留；修正该实际失败条件后成功回收。`faults/lost-local-output.json`：已验证本地输出被移走时拒绝删除 volume，重新回收后可继续。 |
| 连接暂时不可达 | `faults/unreachable.json`：只在本操作进程 PATH 中中断 SSH，endpoint、daemon 和其它客户端均未修改；状态 unconfirmed，保存原退出码/具体 stderr，恢复连接后 verified/removed。 |
| 所有权与重复调用 | `foreign/result.json`：挂载/标签不匹配的旁路容器清理被拒绝，仍 Running=true；其专用验证资源随后按实际创建回执独立释放。`duplicate-invocation.json`：对活动 workspace 重复调用失败，原容器仍在运行。 |
| 冷资源操作 | `reconcile-different-context.json`、`cleanup-different-context.json`：当前环境选择另一个 context 时，冻结 handler 仍按原 receipt 成功核对/清理；不启动新执行。 |
| 文件化 OTLP | 两端容器内 HTTP 200，各回收一个原始 logs 批次；v3 run 的 telemetry.status=received，数据库位于 Mac workspace。Mac collector 保持 loopback，未开放新端口。 |
| 残留与源码反馈 | `residual-resources.json`：两端本轮 container/volume 均为空；专用验证镜像 tag 已删除，基础镜像 cache 保留。修改模块 py_compile 和本任务 diff whitespace 检查通过。当前源码/权威文档的 arcbox-win 引用已清零，历史记录原样保留。 |

所有证据位于 [实际操作归档](../../runs/docker-workspace-20261001/)。本轮只运行用户指定的最小容器验收，没有模型调用、正式 benchmark、设施测试框架或包 smoke。首次直接使用开发 venv 缺少 protobuf 依赖的原始失败保留；随后通过现有 host-lab 入口构建明确稳定环境完成完整链，不修改公共依赖锁。

标准可重复执行入口为 `DOCKER_CONTEXT=<本次选择> <host-lab launcher> -m lab run <recipe.json> --experiment-root <新的目录>`。本轮 recipe、输入 SHA-256 清单、image-input 和稳定 host-lab 都在上述证据目录；若重做本轮最小操作，应先通过当前 context 从保存的 image-input 构建专用镜像，再使用新实验目录，完成后清理本轮专用 tag。重复运行已有 workspace 不作为恢复方式。

知识已整合到 [本地实验](../../docs/deployment/local-experiments.md)、[lab 入口](../../lab/README.md)、技术说明、CONTRIBUTING、参赛部署和 Makefile。Console 源码没有修改；scripts/package_agent.py 已复用 runtime，无需额外传输层。用户追加提交授权原话：“可以提交”。本次提交仅纳入远程 Docker workspace 适配及其权威说明，其它任务工作区修改保留，不 push。验收时的源码身份见 `source-identity.json`。
