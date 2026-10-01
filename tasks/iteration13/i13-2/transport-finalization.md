# I13-2 失败运行的回收终态诊断

2026-10-01 本次工作限于现有记录、Mac 进程表与一次有界 Docker 只读请求。没有修改生产源码或冻结输入，没有停止、删除或重启任何生成、访问、复制 helper 或操作容器。原 volumes、preservation 和失败 raw 日志继续留在原处；新增证据在 `runs/iteration13/i13-2-20261001/transport-finalization/observation.json`。

主线交接时两份 `run.json` 仍是 `running`。实际诊断期间它们已自行结束：GitHub 于北京时间 22:11:52、Sheet 于 22:11:59 变为 `finished`，结果均为生成失败、`generation_exit_code=1`。原 PID 15727/15728 已不在 Mac 进程表，也未发现仍运行的 `arc_bench_adapter.py` 或实验 controller。较早观察过的旧 controller PID 98966/98997/98999 亦已消失；仍存活的 96817 是共享 `hackathon_gateway.py` 服务，不是待终结的回收控制器。

最新回收记录已经从交接时报告的 600 秒 inventory 超时变为具体失败。两份 `workspace-cleanup.json` 均为 `status=unconfirmed`、`recovery=failed`，对应 `docker-workspace.json` 也是 `state=unconfirmed`、`recovery=failed`。最终异常是远端 inventory 的 `ValueError: link points outside snapshot`，分别指向以下链接：

- Sheet：`template/.factory26/20261001-104900-3b994a70/work/tasks/pr-2/evidence/node_modules`。
- GitHub：`template/.factory26/20261001-074336-af6f78cd/work/cache/pnpm/v10/projects/f569a376d44e3fffc64abc0d4e3e571e`。

`lab/arc_bench/docker_workspace.py` 的 `Workspace.recover` 在复制输出之前，对 helper 中 `/transfer/official-generation` 执行完整 inventory。inventory 会排序遍历并逐个读取文件 SHA；对链接则调用 `resolve()`，要求解析结果位于该 snapshot 根下。链接失败并非 volume 因引用而等待删除：`Workspace.finish` 的次序是在成功 recover/confirm 后才删除 helper 和 volume，所以失败直接进入保留记录。绝对原生路径在 `/workspace` 下有效、在 helper `/transfer` 挂载视角下却落出 snapshot，是可解释该错误的候选原因；本次没有读取链接目标，尚不能把候选当作已确认根因。

同一退出路径存在重复回收：runner `run_container` 正常返回前调用一次；它的 `finally` 在 recovery 尚未 verified 时再调用；adapter `run` 的 `finally` 又调用 `Workspace.finish(cleanup=True)`，后者对未 verified 的 stage 继续 recover。该控制流可把原生成已经退出后的终态记录推迟，也会用后一次错误更新回收错误；本次没有取得每次尝试的完整时间线，不能声称最初的超时由哪种 I/O 或目录遍历行为造成。

唯一远端读取 `docker ps -a` 在 30 秒内无输出并超时，后续 helper `top` 未执行，也没有重试。因此不能确认当前 helper 的 Python inventory 进程是否残留、CPU/I/O 状态或目录图规模。停止 Mac 的 Docker 读取进程不会证明远端 exec 进程停止，不能据此写停止回执。

当前最小动作是不再手工终结元数据：两项已自然 finished，保留失败 volumes、helper、原错误和原始日志即可。不要为了让 cleanup 状态变绿重复调用既有 `cleanup`，因为它会重跑同一 inventory，而且成功后有删除原 volume 的行为。新的 I13-2 尝试使用新的 run/volume，不以旧卷回收成功为前置。若以后要恢复回收，只需补充这两个实际链接的 readlink 目标与 helper 挂载路径映射，再决定如何在保留原始链接身份的前提下做输出归档；本次授权不包含实施该变化。
