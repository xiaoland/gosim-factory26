# I13-2 Console 最小兼容部署

2026-10-01。本项在已授权 I13-2 内部署评论有效隐藏兼容，并登记主线创建的新恢复 run。独立 Console 主任务已经完成；这里不改它的 packet，不扩展界面或服务协议，不控制生成，不写业务对象，不调用模型或评分，不运行设施测试，也不 commit。

## 当前部署已完成

2026-10-01 14:54:08Z，唯一服务切换到 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-2-compatibility-release`，service `8cc80cad-d873-49ed-ab49-e958ba8852a3`，HTTP PID776190。入口仍为 [Console](http://127.0.0.1:8765/)，Mac 独立 SSH 转发 PID93554 保持同一目标，未配置自动重启。实际监听只有新 HTTP；旧 PID163346 已退出，旧两条自有访问容器已停止，旧 manifest 原子退役。

服务登记两条原 I13 保存状态 archive 和两条 r2 live：`glm-root--hackathon--github-a94a67b4b3d85b`、`glm-root--hackathon--sheet-8046cfb0695023`。新 ID 绑定新卷与原恢复 namespace，旧 ID 没有 Docker 控制或写入能力；首次失败尝试的两条 ID 从未 live register，不指向 r2 卷。完整身份和切换证据见 [最终读回](../../../runs/iteration13/i13-2-20261001/console-deployment/final-deployment-readback.json)与[单实例切换](../../../runs/iteration13/i13-2-20261001/console-deployment/single-instance-cutover.json)。

26 次实际只读 HTTP 全为200，覆盖四项运行列表、根 Issue、已有 PR、sessions、显式评论展开及两条新 runtime。普通评论视图中有效隐藏的正文均为空，隐藏祖先及后代保留追溯关系；显式读取取得原正文。Chrome 实际核对归档和 live Sheet 的 #2→#3：默认两条都隐藏，单独展开 #3 后根 #2 仍省略，后代仍显示祖先隐藏关系。已有 PR #3 正常读取，browser warn/error 为空；首页已作为结果保留。证据见 [HTTP](../../../runs/iteration13/i13-2-20261001/console-deployment/http-readback.json)与[UI](../../../runs/iteration13/i13-2-20261001/console-deployment/ui-readback.json)。这次部署不发送评论、不修改业务对象、不暂停或恢复生成，也不据 Console 可读宣称模型已经采用新材料。

## 切换前准备记录

只读核对的唯一 HTTP 是 Debian-Rebuild 的 PID163346，service `4161a417-fede-4be5-b692-162350a3d826`，稳定根 `/home/yyh/.local/share/factory26/exp-console/20261001-session-reading-release`。manifest、active、launch 与实际进程吻合，登记的 12 个程序/前端文件 SHA 全部吻合。它监听 `127.0.0.1:8765`；Mac 的独立 SSH 转发 PID93554 仍在监听 8765。Debian 首页与运行列表、Mac 转发运行列表均返回 200。

两条源生成 `glm-root--hackathon--github-f9e238c1b698a5`、`glm-root--hackathon--sheet-a45a22ec644204` 仍为 Paused，两条 Console 自有 CLI 访问容器 Running 且未暂停。访问容器保持原 named volume、`official-generation` Subpath、实际 namespace、image/user/workdir 与无网络待命；数据库、工作区和 `/console/braid` 在各自路径空间存在。本项未停止 HTTP、停止/恢复生成、创建访问容器或启动另一 HTTP。

[当前服务与容器原始回执](../../../runs/iteration13/i13-2-20261001/console-deployment/current-service-read.stdout.json)包含完整容器 ID、Mounts/HostConfig 映射、HTTP 和制品身份；[Mac 转发](../../../runs/iteration13/i13-2-20261001/console-deployment/mac-forward-process.txt)与命令另存同目录。来源 journal 原字节 SHA 和长度已记录；后续切换保存停止后的完整 journal，再记录最终身份，不把准备时的快照冒充终态。

## 冻结材料

源码仍只有 `braid-console/archives.py`、`web/src/Discussion.tsx`、`web/src/api.ts` 的原先兼容改动。当前源码冻结到 `console-deployment/release-files/`，共八个 Python 文件和四个前端文件。Python 编译通过；前端沿用已经成功的 TypeScript/Vite 实际构建，不重复编写测试。相对现服务只改变 archives.py 与包含评论组件的前端制品，其余 Python 文件及 CSS 不变。

[冻结身份](../../../runs/iteration13/i13-2-20261001/console-deployment/release-identity.json)保存完整文件 SHA、与现服务的差异及已退出引用的旧资源路径。[程序包](../../../runs/iteration13/i13-2-20261001/console-deployment/console-release-files.tar.gz) SHA 为 `da8ebee8efe63ebccc4609a7377273d914feb884997400ed0391bdf55c798ea1`。配套 Linux Braid 为 `runs/iteration13/i13-2-20261001/linux-braid/braid-linux-x86_64`，实际 SHA `bde76a5adcfa581d0d7e24c9bc9cddc32a07bca49888ee0cf8315f00bee03dc5`。没有在当前服务目录覆盖源码、前端或 binary。

## 单实例切换与登记

新 run 由主线停止源生成并创建、恢复。本项等待主线提供完整新 ID、生产者 run.json、Docker context/完整 runtime ID、实际 image/user/workdir、volume/Subpath、workspace/state namespace 和权限；不从旧 run 名推导新 namespace，也不把旧 ID 改指新 volume。

按既有 `service.py prepare` 在 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-2-compatibility-release` 准备新稳定根，先登记空列表与 Debian 的 `/usr/bin/python3.13`，再通过新根 `app/service.py binary` 冻结新 CLI。prepare 只准备材料，不运行 HTTP。旧运行的 ID、state、workspace 与原 volume 对应保留；新 run 使用各自新 ID 和实际映射。旧程序、binary、现场和 journal 保留来源，兼容 CLI 的更新不更换现场身份。

新根由 prepare 取得新 service ID，所以访问容器必须明确属于该 ID；不能让新服务直接采用带旧 service 标签的访问容器。按实际 image/user/workdir 创建新 Console 待命容器，挂载相应原或新 named volume 与精确 Subpath，以及新根受管理 binary；仅运行 sleep，无网络。通过新根 `app/service.py register --service <新根> --registry <实际列表>` 验证原路径与所有权，再只读核对新根 show。旧 HTTP 在准备和登记期间继续提供原现场阅读，第二 HTTP 不启动。

切换时再次核对 PID163346 的命令、service/锁、当前 manifest 与访问容器，并确认现有 launch 无自动重启。只向确认的旧 HTTP 发送 SIGTERM，等待进程与监听退出。在旧 manifest 仍有效时，沿旧根 `app/service.py access-stop` 显式停止旧 Console 自有访问容器，保留容器/volume 引用与回执；生成容器不归本项。保存停止后的 manifest、active、launch 和完整 journal 到新根 history，记录字节 SHA；原子将旧 manifest 改名为 retired-service.json。随后只启动新根 `app/service.py serve --service <新根> --port 8765`，保存真实 PID、launch、active 与日志。Mac 转发保持同一目标；旧 HTTP 退出不视为转发或生成停止。

旧 journal 保存在 history，不混入新活动 journal。任一步失败保留具体错误与配置，修复新服务，不自动回滚或恢复生成。

部署反馈只使用实际 HTTP/UI 阅读：运行列表、各旧/新 run 根 Issue 和现有 PR、普通隐藏分支与显式展开的追溯正文，并核对 runtime 的实际状态。新旧 ID 的 workspace/state/volume、binary SHA、唯一监听者和浏览器入口分别记录；不发送设施验收评论，不请求 pause/resume。页面读取与实际模型采用协作材料是不同验收，后者仍归主线恢复运行证据。

以上是首次切换前的准备方案；后续暂停和 r2 实际完成记录如下。

## 实际执行：新根与只读历史已准备

主线已启动新 experiment `exp-20261001-212808-5a935b`，新运行 ID 为 `glm-root--hackathon--github-346a6ae5a0e3a0` 与 `glm-root--hackathon--sheet-efba85c7cfa0f9`。旧生成由主线停止，Exit143 且 OOMKilled=false，证据在 preservation/old-execution-stop.json；本项没有执行生成生命周期操作。

核对现协议发现，live 的 writable=false 仅禁止对象修改，Docker 登记仍提供物理控制。主线明确同意旧两 ID 使用既有 archive 模式，因此上面为旧 ID 准备新访问容器的计划已收敛为派生只读归档；不登记它们的 Docker 或新 volume，不保留旧控制能力。归档来自 preservation/{case}/workspace 对应完整快照：数据库复制已有 WAL 合并的 forensics 副本，SHA 与原 receipt 一致；status 原字节复制，native 正文按原物理记录复制并核对 Pi header 身份。归档 source.json 保存原 run、namespace、volume/container、完整工作区 hash 及准确快照起止时间，不将部署时间写成来源时间。

两条归档分别保留三和六条会话，全部 native 映射有效。真实 Archive 读取得到 GitHub 两个工作项、Sheet 三个工作项；原数据库/原始 WAL/完整 workspace 保留不动。派生归档包 SHA `f174adad9d859019061ed77e19058e735da0fded8a7c99803d4617a4121a1097`，完整身份归 console-deployment/old-run-archive-identity.json。

实际新稳定根为 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-2-compatibility-release`，service `8cc80cad-d873-49ed-ab49-e958ba8852a3`。配套 prepare 已冻结十二项程序/前端文件及 Debian Python 身份，binary 已由配套管理命令保存到此根；旧两条 archive 已 register。原 HTTP 仍运行，尚未启动新 HTTP。原始回执在 console-deployment/new-service-prepare.json 与 archive-register-and-new-resource-read.json。新运行还须经过实际 Docker identity、挂载及 state 存在核对，接入后再执行唯一实例切换。

新 runtime 首次实际核对均 Running，run/image/volume/Subpath 匹配；Sheet Console 自有访问容器仅运行 sleep，GitHub 自有容器的创建命令在 40 秒后超时，终态须按实际 Docker inspect 核对，不重试创建。第一次 live 登记的前置读取发现 template 仅有 .arc/requirements，数据库尚未解包，因而在 register 前停止，未修改新 manifest 的 live 列表或旧 HTTP。原始错误保存到 new-live-registration.stderr.log、new-access-prepared.stderr.log，目录事实在 state-path-discovery.json；确认存在的访问容器按真实 ID 保留，随后接续时复用而非重复创建。

主线后续确认 13:54:57/58Z 开始恢复保留工作区。目录出现不能证明 DB/WAL 与原生材料已完整解包，因此接入的条件进一步明确为 recovery-attempt.json 的完成回执及新 recovery-braid.log 证明 Braid 已接续。旧 status 文件仅是原保存事实，不据此宣称新生成运行或恢复完成；条件未满足期间，现 HTTP 和归档准备保持不动。

GitHub 访问容器超时后实际 inspect 确认其已创建但未启动，ID `2cf9367bc84cea99d64ca34473d29553d416cac0c852241538a42af3312fece9`；Sheet 访问容器 ID `338ee82818a343b0e8d7bc8a8fc8bd04b37033cd626091c25ecce33a92307746`，Running。两者的新 service/run 标签、image/user/workdir、volume/Subpath、sleep 命令及无网络配置已核对，原始回执为 new-access-actual-readback.json。二者尚未 live register，现 manifest 只有旧两条 archive；它们仍对实际 named volume 构成消费者引用，不默认移除或重建。

21:57 主线既有采集报告两条新生成容器已不运行，要求暂停新 live 切换，由主线与 first-continuation 取证恢复入口错误。按此指示，本项没有启动已创建的 GitHub 访问容器，没有登记不完整新 live，也没有停止旧 HTTP/access 或退役旧 manifest。新 service prepare 与归档、两条访问容器及错误回执全部保留；不由 Console 任务修复生成。当前部署未完成，恢复完成条件及主线继续指示到齐后接续。

## r2 实际身份与保全

接入依据为主线生产采集 `revision2/observation/monitor/20261001T144445.120401Z`，再从 Docker 实际 inspect 核对运行身份，使用访问容器读取当前顶层 request、prepared recovery-attempt 与 WAL 数据库。GitHub runtime 为 `ae2bf1d8de9504ccf45a149f5ed68fcdfc9c1a36e405df91efa7bc738a6657f3`，访问容器 `e2af4e7a30d964043d55e514cae4ba8790f442ebad7edf7560cb394082c69a56`；Sheet runtime 为 `b2d7c7e648c1be706336e7b39e500aa9a0baee0500e92687879b244d0af296f0`，访问容器 `2158df223c6b79ebe3d0de32c6c0f01a9cc048955c8beed898b624dcdbd3dd7c`。两访问容器保持原 image、501:20 用户、/workspace 工作目录、无网络 sleep，仅挂载原 named volume 的 official-generation Subpath 和受管理 CLI。

| 现场 | named volume | 实际 Braid namespace |
| --- | --- | --- |
| GitHub r2 | factory26-attempt-103cddb843dadc54cd7814a43618f397 | 20261001-074336-af6f78cd |
| Sheet r2 | factory26-attempt-2ed9fe8619150b94136a6b51d45e56ed | 20261001-104900-3b994a70 |

配套 CLI 已更新为 r2 构建，SHA `9d322da9e3dde2d8fb065cff2f5543fdc668dd8dcd2e653a31e87fb1a34874eb`，保存到新服务 binaries 同 SHA 子目录，并在两个访问容器中核对实际字节。十二个程序/前端制品与 prepare manifest 全部相符，两个只读归档保存文件前后身份均相符。最终实际生成和访问容器均 Running、Paused=false；这是本次读取时点的事实，不代替主线监控。访问准备第一次查询误用了 local_work_items 表名，SQLite 原错误保存在 r2-access-prepared.stderr.log；改为实际 work_items 后复用既有 GitHub 容器、再创建 Sheet 容器，读回及 register 成功，未重建或改数据库。

旧服务停止后的 manifest、active、launch 和完整 console-actions.jsonl 保存到新根 history/4161a417-fede-4be5-b692-162350a3d826，再复制至本项 console-deployment/history；两处 SHA 一致。journal SHA `4f3dfae24c8541022a434a6b0e1ad2e5354ce356d4e3f031c30c7b0612ea6105`，历史不混入新活动 journal。旧 access Exit143、OOMKilled=false，容器和 volume 引用保留不删除。切换保留首次失败尝试的未登记访问容器及原错误，不冒充 r2 来源。操作与现场读取已经完成，没有后续部署阻塞；源码仍限定原三文件，未新增架构改动或提交。
