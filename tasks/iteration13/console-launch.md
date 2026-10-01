# I13 Console 单实例接入

2026-10-01。用户解除暂停并要求四项 I13 运行自动接入，沿用 Console 可直接实施的授权。用户随后明确只需要一个实例；主线经独立 advisor 核对，授权在既有 clean/hard cutoff 范围内将两份 Mac 归档搬到 WSL、退役 Mac HTTP，原 8765 地址只转发到 WSL 唯一 HTTP。本批没有修改 Console、Braid、Harness 或生成应用源码，没有业务写入、暂停/恢复生成或模型启动。

当前入口为 [Console](http://127.0.0.1:8765/)，唯一服务根是 WSL `/home/yyh/.local/share/factory26/exp-console/20261001-i13-live`，service ID **`c5c21595-811d-4dde-b6b4-83a77cf1bbc8`**。15:50 CST 实测 HTTP PID **6809**，instance `a7a140cd-a17a-43d7-bd33-553f95ef5dbb`，监听 Guest127.0.0.1:8765。Mac8765仅由独立 SSH 转发 PID **7892** 监听，目标 `factory26-i13-wsl` 的127.0.0.1:8765；不配置自启。8766方案已退役且无监听。WSL或SSH断线时归档页面也不可用，主线已向用户说明此取舍。

## 迁移与唯一权威配置

复用WSL原空服务，解释器仍为稳定 `/usr/bin/python3.13` 3.13.5。六份Python和四份前端资源共十份SHA-256与Mac当前冻结制品逐项一致，未替换app。两份归档完整复制到新服务 `archives/pi-archive-20260920/` 和 `archives/github-final-20260930/`，保留原run IDs及内容。分别有71/2325个文件或链接、12,824,438/157,679,130字节；完整相对路径树、文件hash和链接目标一致，不是只复制manifest中的投影文件。

先离线核对归档schema、冻结文件身份、根Issue、对象和会话并register成功，再核对Mac HTTP PID56220的命令、发送SIGTERM、确认进程退出和端口释放。Mac `/Users/lanzhijiang/.local/share/factory26/exp-console/20261001-path-routing-final/manifest.json` 已原子改名为 `retired-service.json`，不存在另一份活动manifest。原配置、运行中/已结束active、journal是否存在的事实及前序history保存在新服务 `history/mac-20261001-path-routing-final/`；旧journal当时不存在，如实记录，未混入新活动journal。

Mac两份原始归档保留，未删除或修改。HTTP、SSH转发、Console自有访问容器和实验生成容器仍各自独立。新manifest是当前唯一恢复配置；retired配置只保留来源事实，不启动或自动回退旧服务。

## 真实运行与后台接入

精确实验目录为 `/home/yyh/factory26/experiments/e20261001-01-local-20261001`，只读取此矩阵四个已授权job。实际allocation的run.json、generation.resource.json、现存数据库和Docker inspect共同确定接线，不猜运行身份或预建DB。Docker default固定为 `unix:///var/run/docker.sock`。配套 `app/service.py binary` 已导入受管理binary，SHA-256 **`a78128da72e64fc604d7cd0ccde68ebc69e61d7db48af165e7b53c858e6e83dd`**，路径为新根 `binaries/<上述SHA>/braid`。

| Job | 实际 run ID | 初次接入事实 |
| --- | --- | --- |
| GLM GitHub | `glm-root--hackathon--github-00bf489759b139` | 已登记live，可写；生成running、未暂停 |
| Flash Sheet | `flash-root--hackathon--sheet-f893bdb3298d69` | 已登记live，可写；生成running、未暂停 |
| Flash GitHub | `flash-root--hackathon--github-4afc8896760859` | 未登记；原生成容器退出并移除，恢复归主线 |
| GLM Sheet | `glm-root--hackathon--sheet-2cf88b952f231c` | 未出现生成资源/数据库，后台等待实际启动 |

Flash GitHub原容器 `e3ccda4ed279c60465717e379a3094afe4d37e7bb40aea6f8e013933f459dad4` 先读到removing/Dead=true/Running=false/ExitCode=1，随后inspect返回不存在，具体事实已交主线。Console不重建生成或伪造旧身份。退出后空槽位启动Sheet，故初次成功接入的是上述两条真实运行。主线后续计划将修复后的Flash GitHub放入独立一项experiment；新目录不在当前watch范围，须由主线提供精确配置后扩展，禁止扫描任意run。

访问容器沿用原完整image、1000:1000用户、/workspace工作目录和实际共享挂载，额外只读挂载受管理binary，具有service/run标签；只执行sleep infinity，network none、无自动重启。GLM GitHub生成/访问容器为 `bd7cc655b8163762428c4764962ac809d2980adf9f9fad1a13e603363f9a385b` / `0392f0430db3e840a7abe4a2b6673d5f8eb8b608d82b1dec3a2a2f62e2ed99db`；Flash Sheet为 `0a1723b4a8632b525888e4d3945874ff9ff7760f7239e8dc4650f4e4185b99ed` / `d321a3808ef85916e09f3207088d63ce9a3ed78e3db90e508172ffb77ab5fc6f`。容器state以实际最长匹配挂载对应同一宿主DB，没有复制或修改数据库。

后台脚本是新根 `operations/attach-live.py`，PID **7303**，只管理本服务配置与自有访问容器。它读取精确矩阵，按同job最新attempt取得allocation；已登记run ID跳过、保留旧身份，禁止覆写。flock阻止重复操作程序；复用访问容器前核对标签、image、用户、命令、网络和实际挂载。资源齐备后创建独立访问容器、短停已确认的本HTTP、调用冻结register、重启本HTTP，不影响生成。前十分钟每三分钟查看，之后每八分钟；四组当前allocation都登记后退出，等待不唤醒模型。本轮Flash失败使done仍为false，不能声称四项均接入。

操作追加 `operations/live-attach.jsonl`，管理原始回执归 `console-actions.jsonl`；`operations/live-attach-process.json`、`live-attach-status.json`、`live-attach.stdout.log` 记录进程、接入状态和具体错误。身份或边界不匹配使脚本退出并保留unconfirmed，不自动重建。接续先读取这些记录再核对实际进程，不信任历史PID。

## 实际反馈与保护范围

经Mac8765转发独立读取两份归档的列表、根Issue、会话和原文，除归属新根的native物理路径外，正文与元数据和迁前完全一致。Pi为1个对象/1条会话、原文HTTP200；GitHub为23个对象/215条会话，缺native manifest的具体HTTP400与迁前相同。两条live的列表、根Issue、会话、runtime和已出现原文均HTTP200，初次各1个对象/1条会话，runtime均running/paused=false。Chrome实际首页显示4条登记、2 live/2 archive，两条根Issue正常加载，显示生成运行中和对应Braid session。未点击写入/控制按钮；初期无PR如实记录。主线也独立读取api/runs确认四条登记access_error全null。

Home使用明确的生产者run.json。当前lab记录提供variant，但未提供Console读取的experiment_name/status/updated_at字段，页面因此显示未保存；没有用目录名、lab phase或Issue状态冒充这些字段。实际生成状态由Docker runtime另行核实。

GC扫描必须包含新稳定服务根，manifest保护app、解释器、两份新归档、binary、已登记run整个原workspace及全部宿主挂载。当前两个workspace为精确矩阵下相应run的workspace/official-generation/；完整state、容器和挂载保存在single-instance-final.json。未登记现场继续由实验生产者保护；未运行GC apply或清理原始材料。

原始证据和操作脚本在Mac `runs/iteration13/console-launch-20261001/`：migration-baseline.json、migration-ready.json、mac-retired/、single-instance-cutover.json、single-instance-http.json、single-instance-http-summary.json、single-instance-final.json、forward-8765.log；远端保留operations/history。Chrome工具返回真实页面与截图，browser-single-instance.json记录观察来源。本页归当前部署身份，长期协议归[Console README](../../braid-console/README.md)与[部署说明](../../docs/deployment/console.md)。限定提交本页及受影响的Console/部署状态文档，不push。

## 前序空服务与暂停来源

12:15 CST以零登记prepare取得本WSL service ID，未预建DB；12:17原HTTP PID2479、Mac8766转发PID71228提供空Home。用户12:25指示“DNS 问题交给我来，你先暂停”后保留无害空服务、停止脚本开发和接入。解除暂停后只读核对发现原PID及8766监听均失效，仅active保存旧事实。本批没有直接信任旧PID，而是按新单实例范围完成上述迁移。原prepare/source hash、空Home及Mac归档基线证据保留，不作为当前部署身份。
