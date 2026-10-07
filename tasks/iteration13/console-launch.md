# I13 Console 单实例接入

2026-10-01。用户解除暂停并要求四项 I13 运行自动接入，沿用 Console 可直接实施的授权。用户随后明确只需要一个实例；主线经独立 advisor 核对，授权在既有 clean/hard cutoff 范围内将两份 Mac 归档搬到 WSL、退役 Mac HTTP，原 8765 地址只转发到 WSL 唯一 HTTP。Console 迁移与接线没有修改 Console 或生成应用源码，也没有业务写入或暂停/恢复生成；后续模型运行与 Braid 修复分别按主线实验授权执行，本页只保存其实际接入事实。

当前入口为 [Console](http://127.0.0.1:8765/)，唯一服务根是 WSL `/home/yyh/.local/share/factory26/exp-console/20261001-i13-live`，service ID **`c5c21595-811d-4dde-b6b4-83a77cf1bbc8`**。17:33 CST 读取的 HTTP PID 为 **261883**，instance `de54f020-bace-43a6-ad19-38813093d3b9`，09:31:58 UTC 因登记新运行按既有命令重启，仍监听 Guest127.0.0.1:8765。Mac8765仅由独立 SSH 转发 PID **7892** 监听，目标 `factory26-i13-wsl` 的127.0.0.1:8765；不配置自启。8766方案已退役且无监听。WSL或SSH断线时归档页面也不可用，主线已向用户说明此取舍。

## 迁移与唯一权威配置

复用WSL原空服务，解释器仍为稳定 `/usr/bin/python3.13` 3.13.5。六份Python和四份前端资源共十份SHA-256与Mac当前冻结制品逐项一致，未替换app。两份归档完整复制到新服务 `archives/pi-archive-20260920/` 和 `archives/github-final-20260930/`，保留原run IDs及内容。分别有71/2325个文件或链接、12,824,438/157,679,130字节；完整相对路径树、文件hash和链接目标一致，不是只复制manifest中的投影文件。

先离线核对归档schema、冻结文件身份、根Issue、对象和会话并register成功，再核对Mac HTTP PID56220的命令、发送SIGTERM、确认进程退出和端口释放。Mac `/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-path-routing-final/manifest.json` 已原子改名为 `retired-service.json`，不存在另一份活动manifest。原配置、运行中/已结束active、journal是否存在的事实及前序history保存在新服务 `history/mac-20261001-path-routing-final/`；旧journal当时不存在，如实记录，未混入新活动journal。

Mac两份原始归档保留，未删除或修改。HTTP、SSH转发、Console自有访问容器和实验生成容器仍各自独立。新manifest是当前唯一恢复配置；retired配置只保留来源事实，不启动或自动回退旧服务。

## 首批运行与接入来源

精确实验目录为 `/home/yyh/factory26/experiments/e20261001-01-local-20261001`，只读取此矩阵四个已授权job。实际allocation的run.json、generation.resource.json、现存数据库和Docker inspect共同确定接线，不猜运行身份或预建DB。Docker default固定为 `unix:///var/run/docker.sock`。配套 `app/service.py binary` 已导入受管理binary，SHA-256 **`a78128da72e64fc604d7cd0ccde68ebc69e61d7db48af165e7b53c858e6e83dd`**，路径为新根 `binaries/<上述SHA>/braid`。

| Job | 实际 run ID | 初次接入事实 |
| --- | --- | --- |
| GLM GitHub | `glm-root--hackathon--github-00bf489759b139` | 已登记live，可写；生成running、未暂停 |
| Flash Sheet | `flash-root--hackathon--sheet-f893bdb3298d69` | 已登记live，可写；生成running、未暂停 |
| Flash GitHub | `flash-root--hackathon--github-4afc8896760859` | 未登记；原生成容器退出并移除，恢复归主线 |
| GLM Sheet | `glm-root--hackathon--sheet-2cf88b952f231c` | 未出现生成资源/数据库，后台等待实际启动 |

Flash GitHub原容器 `e3ccda4ed279c60465717e379a3094afe4d37e7bb40aea6f8e013933f459dad4` 先读到removing/Dead=true/Running=false/ExitCode=1，随后inspect返回不存在，具体事实已交主线。Console不重建生成或伪造旧身份。退出后空槽位启动Sheet，故初次成功接入的是上述两条真实运行。主线已提供修复后Flash GitHub的精确experiment `/home/yyh/factory26/experiments/e20261001-01-recovery-g03` 及job ID `flash-root--hackathon--github`，现已纳入watch白名单；未出现目录/manifest时正常等待，禁止扫描任意run。

访问容器沿用原完整image、1000:1000用户、/workspace工作目录和实际共享挂载，额外只读挂载受管理binary，具有service/run标签；只执行sleep infinity，network none、无自动重启。GLM GitHub生成/访问容器为 `bd7cc655b8163762428c4764962ac809d2980adf9f9fad1a13e603363f9a385b` / `0392f0430db3e840a7abe4a2b6673d5f8eb8b608d82b1dec3a2a2f62e2ed99db`；Flash Sheet为 `0a1723b4a8632b525888e4d3945874ff9ff7760f7239e8dc4650f4e4185b99ed` / `d321a3808ef85916e09f3207088d63ce9a3ed78e3db90e508172ffb77ab5fc6f`。容器state以实际最长匹配挂载对应同一宿主DB，没有复制或修改数据库。

后台脚本是新根 `operations/attach-live.py`，初次 g03 扩展后的 PID 为 **101386**（替换休眠中的旧PID7303），只管理本服务配置与自有访问容器。当时只读取原精确矩阵的四个job和g03精确目录的Flash GitHub单job，按每个来源同job最新attempt取得allocation；g03真实allocation出现后接替失败的Flash GitHub逻辑目标，不覆写任何旧run ID；已登记run ID跳过、保留旧身份，禁止覆写。flock阻止重复操作程序；复用访问容器前核对标签、image、用户、命令、网络和实际挂载。资源齐备后创建独立访问容器、短停已确认的本HTTP、调用冻结register、重启本HTTP，不影响生成。前十分钟每三分钟查看，之后每八分钟。此首批快照的 Flash 失败使 done=false，没有声称四项均接入；当前用户改选官网 Flash 与本地 GLM 两路后的接入完成条件见下节。

操作追加 `operations/live-attach.jsonl`，管理原始回执归 `console-actions.jsonl`；`operations/live-attach-process.json`、`live-attach-status.json`、`live-attach.stdout.log` 记录进程、接入状态和具体错误。身份或边界不匹配使脚本退出并保留unconfirmed，不自动重建。接续先读取这些记录再核对实际进程，不信任历史PID。

白名单扩展回执：watcher instance `a7ec4685-4408-4ba3-b81d-0d1124ef9c7a`，脚本SHA-256 `07b600610cc440e98359524c68be32445ab571e6db8ebc4ae65c34670153071f`。旧watcher确认处于hrtimer_nanosleep后仅终止该操作进程，再原子替换脚本并启动新watcher；HTTP仍为PID6809、原instance和service身份未变。g03目录尚不存在，recovery_allocated=false、done=false，GLM Sheet继续等待。两live和两archive的root/items复核均HTTP200，live runtime均HTTP200、未暂停。证据是runs目录中的watcher-g03-before.json、watcher-g03-after.json和watcher-g03-readonly.json；远端live-attach.jsonl有watcher-update-g03的started/completed回执。新实验尚未plan或启动，本次没有创建g03容器或DB。

## 自有 API 的两个 GLM 运行

用户后续决定 Flash 两题去官网，GLM 两题继续本地并使用自有 API。主线已确认原生成 stopconfirmed，旧登记和共享 workspace 继续保留。Console 接入只增加精确白名单 `/home/yyh/factory26/experiments/e20261001-01-local-self-funded-20261001/sheet` 的 `glm-root--hackathon--sheet` 与同批 `/github` 的 `glm-root--hackathon--github`，未扫描其它目录。由于 lab 冻结后的 manifest 不接收追加 job，两路分别冻结在同一批次根下，共享 `experiment_key=e20261001-01`、`batch=local-self-funded-20261001` 和自有 API 标签。

| 本轮任务 | 实际 run ID | 生成容器 / Console 访问容器 |
| --- | --- | --- |
| GLM Sheet 干净生成 | `glm-root--hackathon--sheet-45bf2d21de2ec4` | `f98246853f5a0bab14817b7cd17d9861b113621e2c29085519c99df9a5c6ce51` / `daabc2c64ac814d765bc482275a11ed19e6c7163e02982ca15514938d7153b38` |
| GLM GitHub 快照接续 | `glm-root--hackathon--github-e057e34c3d510a` | `6cc8d5edff36c0de3cf3976e5cefa0d1dc91360fc6ec8500c0d798d8a838743f` / `e0d3dc60635234fcf9ef246854e00076fc5f998fcc968aefaf38658fd7ba5ee6` |

两路 generation.resource.json、真实 DB 与实际容器身份均核对后才登记。访问容器仍使用完整实际挂载、1000:1000、/workspace、network none 和 sleep infinity。新受管理 binary 的 SHA-256 为 **`a8afac46d2a8268dc3e7e163e673220216caaeee892b6d3af01c743b70144414`**，包含当前 request 的指派目录修复及 Pi 子进程信号日志；旧两条登记保留原 binary。新运行的候选目录按当前 request 读取，根成员不可新指派，DeepSeek 仅保留 Pi 内部角色或兼容历史身份。

现场 watcher instance 为 `de0ade7a-bda9-4027-a66f-98fb0007de33`，PID **256287**，脚本 SHA-256 `02118ea57de50e2ceba725655386711744e8abab55cfa4b2aab63f77cfcef7e4`。旧 PID101386 身份及休眠状态核对后只终止该操作进程，替换前脚本保存在 `operations/attach-live.pre-self-funded.py`。白名单保留旧矩阵及 g03，但本批完成条件改为两个新的 GLM allocation 均已登记。17:33 CST `live-attach-status.json` 的 done/self_funded_ready 均为 true，随后核对 `/proc/256287` 已不存在；后台正常完成，不继续等待未启动的 g03。

同一 Mac8765 地址实际读取六条登记，access_error 全为 null。两份 archive、两条旧 live 和两条新 live 的根 Issue 与会话均 HTTP200；两个新 runtime 均 HTTP200、running 且未暂停。旧两条生成容器已退役，runtime 返回具体 HTTP400，旧访问容器仍能读取保留的数据，因此不把登记 mode=live 当作当前生成仍在运行。证据归 `runs/iteration13/local-self-funded-20261001/console-self-funded-final.json`、对应 summary、console-active.json、console-manifest.json 和 live-attach-status.json。

模型与费用边界由对应实验控制。Sheet 的首个真实 GLM-5.3 请求于09:13:07.993 UTC发出、09:13:14.633 UTC取得 chat.finish_reason，回执为 `sheet-first-model-readback.json`。GitHub 已实际启动并完成原根 session 握手，但17:37 CST仍未到达网关：实际 Pi URL/变量和四份 native models 配置正确，同容器只读 GET/models 返回 `Errno 113 No route to host`。Docker 配置仍是172.17.0.0/16，而此时宿主 docker0 只有172.30.0.1/24。网络恢复归主线协调；原错误和 `github-transport-readonly.json` 保留，不能把容器 running 或 Console 可读当作模型通道成功。

## 实际反馈与保护范围

经Mac8765转发独立读取两份归档的列表、根Issue、会话和原文，除归属新根的native物理路径外，正文与元数据和迁前完全一致。Pi为1个对象/1条会话、原文HTTP200；GitHub为23个对象/215条会话，缺native manifest的具体HTTP400与迁前相同。两条live的列表、根Issue、会话、runtime和已出现原文均HTTP200，初次各1个对象/1条会话，runtime均running/paused=false。Chrome实际首页显示4条登记、2 live/2 archive，两条根Issue正常加载，显示生成运行中和对应Braid session。未点击写入/控制按钮；初期无PR如实记录。主线也独立读取api/runs确认四条登记access_error全null。

Home使用明确的生产者run.json。当前lab记录提供variant，但未提供Console读取的experiment_name/status/updated_at字段，页面因此显示未保存；没有用目录名、lab phase或Issue状态冒充这些字段。实际生成状态由Docker runtime另行核实。

GC扫描必须包含新稳定服务根，manifest保护app、解释器、两份新归档、binary、已登记run整个原workspace及全部宿主挂载。首批两个workspace为精确矩阵下相应run的workspace/official-generation/；当前又加入 self-funded 根下 sheet/github 各自真实 run 的 workspace/official-generation/。旧原件、四个现场 workspace 及两代 binary 均保留引用，完整state、容器和挂载分别在single-instance-final.json及console-manifest.json。未登记现场继续由实验生产者保护；未运行GC apply或清理原始材料。

原始证据和操作脚本在Mac `runs/iteration13/console-launch-20261001/`：migration-baseline.json、migration-ready.json、mac-retired/、single-instance-cutover.json、single-instance-http.json、single-instance-http-summary.json、single-instance-final.json、forward-8765.log；远端保留operations/history。Chrome工具返回真实页面与截图，browser-single-instance.json记录观察来源。本页归当前部署身份，长期协议归[Console README](../../consoles/README.md)与[部署说明](../../docs/deployment/console.md)。限定提交本页及受影响的Console/部署状态文档，不push。

## 前序空服务与暂停来源

12:15 CST以零登记prepare取得本WSL service ID，未预建DB；12:17原HTTP PID2479、Mac8766转发PID71228提供空Home。用户12:25指示“DNS 问题交给我来，你先暂停”后保留无害空服务、停止脚本开发和接入。解除暂停后只读核对发现原PID及8766监听均失效，仅active保存旧事实。本批没有直接信任旧PID，而是按新单实例范围完成上述迁移。原prepare/source hash、空Home及Mac归档基线证据保留，不作为当前部署身份。
