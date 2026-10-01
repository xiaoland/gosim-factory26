# 同宿主 Docker 执行准入

2026-10-02，按主任务转交的 I14-0 设施范围实现。本项不启动 I14，不修改原两项 I13 容器或监控，不提交代码。共享上限为同一冻结 Docker daemon 的五个本地执行容器；当前老 I13 各占 4GiB/2CPU，新 I14 所需的 2GiB/2CPU 由调用配方显式冻结，本准入不改写资源限制。

矩阵实际接口为 `arc_matrix.build(..., shared_docker_slots=5, memory="2g", cpus="2")`；CLI 为 `--shared-docker-slots 5 --memory 2g --cpus 2`。三项参数在每个 job 的 adapter argv 中冻结，CLI 的 CPU 数值可能写成等价 `2.0`。默认值均为 None，原矩阵不自动采用新政策或资源值。内存格式沿用 Docker 原生解析，CPU 需要有限正数；内存、CPU 与文件系统 storage 配额是不同限制。已有 I13 的 4GiB 无需改动；可运行 I14 数量由五格减去当前真实物理占用决定，老执行结束后余量自动增加。

I14 主会话可直接消费本接口，先在配方引用 Debian-Rebuild 的 development-1 冻结 endpoint（daemon ID 见下文），显式给所有新本地 job 设置上述三参数，再通过既有 lab.plan 冻结。不同新矩阵即使各自 workers=5，实际仍由同一准入 registry 共享五格，不是各有五格。文件系统共享目录不得为每条run单独设置；若使用 FACTORY26_DOCKER_ADMISSION_ROOT，所有controller保持同值。不要把现行两个I13的旧frozen controller-source换成新代码，也不更改其原矩阵。

执行边界使用 `from lab.arc_bench.docker_admission import admit`，在 Runner 的整个 `run_container` 生命周期外层使用 `with admit(endpoint, resource):`。这层须覆盖输入传输、启动、执行，以及原有 finally 的停止和保全动作；异常同样退出 lease。资源字典须包含 `shared_docker_slots: 5` 和完整 `labels`，四项身份为 `io.factory26.run/attempt/stage/owner`。`resource_path` 可填写原 resource JSON 的绝对路径，以在其旁同步 `<stage>.resource.admission.json`。lease 返回 `id`、`receipt`、`identity` 等字典；未设置 slots 时不启用准入并返回 None。Root 负责 adapter 参数、资源登记和 Docker workspace 调用接入。

准入按冻结 `daemon_id` 哈希，在 `~/.config/factory26/docker-admission/<hash>/` 保存 registry 和 flock 锁。遵从 XDG_CONFIG_HOME，可用 `FACTORY26_DOCKER_ADMISSION_ROOT` 指定统一目录；同 daemon 的所有参与 controller 必须使用同一稳定目录。已有 registry 的 slots 与请求不一致时明确失败，不由后来的 controller 改上限。这是同宿主同用户、同 registry 的协调边界；不同宿主或独立用户的锁不共享。未接入准入的执行者仍可能在准入之后增加容器，不能声称该实现可阻止跨宿主启动或未参与的外部启动。

每轮在锁内先核对当前 daemon ID，再读取带 `io.factory26.stage` 标签的全部容器及原生状态。running、paused 和 restarting 容器均计入，每个物理容器占一格；原 I13 不需要改记录。传输 helper 没有 stage 标签，不计执行格。尚未绑定活动物理容器的 reservation 另占一格；与同 run/attempt/stage/owner 物理执行匹配时只计物理容器。reservation 保存真实宿主、boot UUID、PID 和出生身份，以及资源、来源和 attempt/stage/owner labels；当前查询 unreadable 或身份未知不会释放容量。确认 owner lost 后，只有同 daemon 完整物理读回同时确认该身份无活动执行，才可在实际准入时清除。相同四项身份已有 reservation 或活动容器时拒绝再次启动。

容量满时由程序每五秒读回并等待，不唤醒模型。等待、准入、退出会在 `receipts/<lease-id>.json` 保留最新事实，并在同名 `.jsonl` 追加状态变化；不每次轮询重复写相同等待状态。`admitted` 的 capacity 是登记该 lease 前的观察。退出 lease 仅删除本次 reservation；实际仍运行的容器在下一轮独立 Docker 读回中继续占格。失联 owner 的回收依据在 capacity 的 `reclaimable_lost` 列表中，registry 落盘后才实际移除；`snapshot(endpoint, 5)` 只读观察，不改写 registry，返回可回收事实不等于已回收。

Docker 读取失败时保留 subprocess 的返回码、stdout/stderr，由调用层现有错误回执呈现；物理状态没有确认时不执行准入或失联回收。当前实现不覆盖收费执行授权，只负责已授权执行的机械容量门禁。

实际容量读回在 [readback.json](../../runs/experiment-operations/20261002/shared-admission/readback.json)，保存直接 Docker 命令、独立计算、API snapshot 和原 resource 的 SHA。冻结 daemon `0c1d4a2e-b921-49be-a075-1e30571f0995` 的 info 返回 16745209856 字节内存与 12 CPU；两个带 stage 标签的真实 I13 容器均为 running，各 4294967296 字节内存、2000000000 NanoCPUs，当前五格中占二、余三。registry 原本不存在，本次只读 snapshot 没有生成 reservation 或 registry 内容。

两模块编译及 diff 检查通过。没有构造 lease、并发样本或运行测试、smoke、自检和探针，没有改变容器状态。实际多 controller 并发准入、满格等待、崩溃后失联回收、finally 释放和 I14 新资源限制，仍须在下一次获授权真实运行中验收；当前真实容量观察不能替代这些反馈。
