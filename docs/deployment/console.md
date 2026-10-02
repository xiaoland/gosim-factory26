# Factory26 Exp Console 开发接入

## 新执行合同接入

新 Docker 登记除访问容器、binary/state/mounts 外，还要求 docker.exp 的 experiment 绝对路径和 attempt_id。登记和物理控制通过该实验冻结 runtime/source 查询实际资源，核对完整容器 ID、StartedAt 和 labels，避免显示一个现场却控制另一个。Console 服务制品不依赖工作树 import lab。resume/stop 返回执行器的实际效果；尚无 Harness 公共静止协调合同时拒绝 Console pause，避免冻结持有写事务的 Agent。对象读写仍通过 Braid 公共 CLI，归档只读。

本轮只修改接入代码，没有部署、重启唯一 WSL Console 或迁移其旧登记。旧现场继续使用已冻结服务及限定退役控制。当前受管理访问仅支持可核实同宿主 Unix context；跨宿主访问空间不能冒充已支持。

## 已有服务与历史操作说明

以下描述既有冻结 Console，包括其旧暂停门闩；它不是新接入保证。新登记以本节合同为准。

[Factory26 Exp Console](../../braid-console/README.md)是独立目录中的实验基础设施，没有独立Git仓库，不进入参赛包或Harness迭代范围。
前端使用React、TypeScript、Vite、shadcn/ui、Tailwind CSS、Radix和Lucide及TanStack Query和React Router；对象HTTP桥调用配套Braid CLI，修改沿用对象事务和消息投递。物理运行控制归Docker适配层；Braid不依赖Console或实验平台。
通用构建、启动、registry与操作语义见其README，不在本页维护第二份API说明。

Home始终可访问，空登记有明确登记方法；Braid详情保持专用对象、会话与物理控制。页面展示权限配置与保存事实，当前现场可用性由实际详情读取核实；生产者记录缺失保持未知。

长期服务用README中的service.py prepare/serve放在实验目录之外，固定app/并冻结程序、前端与稳定Python身份；配置、HTTP身份、轮转日志和人工journal归此服务目录。每run明确 `live/archive`：现场登记真实state、原workspace及受管理binary；归档只读浏览保存状态与manifest定位的原文，不依赖旧生成容器或Git。本轮hard cutoff旧服务格式与自由registry启动入口；新制品有独立服务身份，不自动迁移历史或启动WSL。切换先prepare有效新根，再核实停止旧HTTP、保存配置和journal到history、原子退役旧manifest，最终只有新manifest表达恢复配置；不建立兼容或自动回退平台。
实验启动时登记真实Braid state和binary，用独立运行ID区分当前现场与历史副本。同一Console可同时登记不同实验的多个run；每项独立绑定路径、配套binary、权限和可选生成容器，不要求共同实验ID。受管理Docker控制需要同宿主daemon，不能把跨实验接入解释成已支持跨宿主聚合。
从零入口在运行后创建实际state；不能为页面预建数据库或将旧state改名冒充新运行。
数据库出现后显式register并重启Console；`writable`是现场的对象修改权限，归档强制不可写及不可控制，不根据I11/I12等名称猜测。可选Docker配置单独授权该run的物理控制，并固定本宿主context、完整容器ID、实际宿主挂载及所有权标签。归档缺字段、会话目录或native manifest时保留可得数据与缺口，不能把保存状态当当前执行状态。

服务在所在机器监听127.0.0.1；本机直接访问，远端由操作方独立设置SSH本地转发。
对象轮询用于浏览器刷新，不唤醒模型；编辑草稿与服务器快照分开保留，CLI写入不自动重试。
写入回执说明实际CLI结果；确认Agent读取，需要对应消息投递和原生记录。

容器运行使用README中的独立CLI访问容器接线，保留原运行的镜像、用户及挂载路径空间。每run的访问容器以`sleep`待命，Console通过`docker exec`执行对象命令，避免5秒轮询重复创建容器。暂停原生成容器后，Console继续访问同一数据库和Git；访问容器无网络，不运行Agent或定期检查。修改registry后只重启Console服务，不恢复或重建生成容器。访问容器的创建、启动和移除由操作方明确执行，失败时保留原错误。

页面暂停当前run时冻结其全部Agent会话及Braid定期检查；访问容器、对象读取和人工草稿继续可用。恢复由用户明确操作，Console不会自动恢复、重建或启动已停止的生成容器。为避开冻结写事务，适配层在同一Linux访问容器内取得现存WAL库的写者门闩，持锁暂停并确认状态后释放；这里只协调事务排他，不修改Braid表。直接Docker暂停的既有现场可能已持写锁，遇到具体锁错误时保留暂停和journal，不通过解锁或自动恢复绕过。

部署验收实际读取各run的列表、根Issue及已有PR详情，并核对原容器`Paused`；已暂停run可请求一次pause核对`BEGIN IMMEDIATE→ROLLBACK`。读取正常、可取得写锁、实际业务修改完成，以及新暂停/恢复行为是不同证据，逐项记录。保留原始HTTP、控制及CLI回执；不为设施验收发送测试评论或恢复模型。

HTTP停止只结束它自己的进程。SSH转发由操作方独立管理；访问容器用配套 `access-start/access-stop` 显式启停且须核对service/run标签、固定context与真实最长匹配挂载。生成容器及其它消费者不归Console清理。容器缺失或daemon不明保留未确认状态，不自动补建、解除引用或清理挂载。

稳定服务的 `manifest.json` 直接进入现有GC记录域，扫描应包含稳定服务根。即使HTTP停了，可恢复配置仍保护程序、Python、现场workspace/宿主挂载和归档；尚未退役的旧manifest格式使GC失败关闭；未扫描域必须显式protect。显式release接入前，HTTP须停止、转发须由操作方确认解除、Console自有访问容器须已确认停止。release移除当前恢复配置，保留ID墓碑及journal来源回执，不删除数据或容器，也不允许旧ID指向另一现场。访问日志有界轮转；journal保持证据职责，不随日志淘汰。

## 对象、会话与原生正文

工作项页面按 Braid agent → provider sessions 展示当前和历史原生关系，现场来源是登记 binary 的 `status --json.physical_sessions`，归档来源是保存的sessions/status目录；Braid、provider 和 native 身份分别保留。此目录按 physical 材料枚举，空列表不能证明从未执行，缺失正文也不抹去可得元数据。

正文通过 `GET /api/transcript` 按稳定字节游标分页读取，先核对原生 header 的 native 身份。浏览器只传 run、physical 记录 ID 与 offset，不提供任意文件路径；具体分页和数据边界归 Console README。文件缺失或身份不匹配保留错误，不从另一会话补正文。关系、工具 call/result 和原文位置帮助取证，不能从历史 provider 状态推断生成容器此刻是否暂停。

Provider默认对话与Trace共用分页原文，调用和结果有独立来源定位。Agent/Provider文件入口读取登记worktree当前文件，运行级origin入口固定分支提交；历史登记不等于文件快照，未push代码不在origin。读取不修改Git、切换工作区或暂停生成；缺失的归档来源直接报错。代码接口与读取边界归Console README，当前实现及新增验收结果归[Agent Session阅读记录](../../tasks/braid-console-control/provider-session-reading.md)。

当前已经取得真实 Pi 会话的只读接口及页面反馈，归档深链和前后导航已在 shadcn/ui 制品核对；Codex 正文和可写现场的草稿保护仍未实测。人工编辑成功、控制回执、模型读取消息和最终任务效果分别核实；前序接口证据归[会话导航记录](../../tasks/braid-console-control/session-navigation.md)，当前路由与 UI 结果归[路径路由回执](../../tasks/braid-console-control/path-routing.md)。

## 运行身份与实际验收

I12已在独立磁盘清理中终止，归档在runs/wsl-retained-20260930/；不以恢复其暂停现场为Console目标。历史运行身份、部署PID、人工输入journal与停止证据见 [I12 packet](../../tasks/iteration12/packet.md)、[Console记录](../../tasks/iteration12/console.md)及[部署记录](../../tasks/iteration12/deployment.md)。
I12是人工介入研究条件；旧I11摘剪接续已停止，不再用作当前生成起点。原始记录仍保留，历史页面与旧源码位置仅供追溯。
当前Console控制与验收归 [独立任务](../../tasks/braid-console-control/packet.md)；[暂停访问历史记录](../../tasks/iteration13/console-paused-access.md)保留当时故障和接线证据，不作为I13范围。

I13-2首次部署直接运行在Debian-Rebuild，入口为 [Console](http://127.0.0.1:8765/)。该次切换后的稳定根为 `/home/yyh/.local/share/factory26/exp-console/20261001-i13-2-compatibility-release`，service ID `8cc80cad-d873-49ed-ab49-e958ba8852a3`，HTTP PID776190。Mac8765仍为原独立SSH转发；HTTP与转发均不配置自动重启。旧HTTP PID163346已退出，旧自有访问容器已停止，原manifest已退役；完整配置与journal保存到新根history并校验，旧服务不再表示当前恢复配置。

当前登记四项：原`glm-root--hackathon--github-f9e238c1b698a5`与`glm-root--hackathon--sheet-a45a22ec644204`为只读archive，没有Docker控制；r2的`glm-root--hackathon--github-a94a67b4b3d85b`与`glm-root--hackathon--sheet-8046cfb0695023`为live，分别绑定各自新卷及原Braid namespace。首次失败尝试未登记到新卷。真实HTTP/UI已覆盖四项Issue、PR与sessions、两新runtime，以及隐藏祖先下后代的默认省略和单条显式展开；本次没有业务写入或生成控制。准确身份、制品和限制归[I13-2部署记录](../../tasks/iteration13/i13-2/console-deployment.md)。较早的实际Pi对话、Trace、工作区和origin读取结果仍归[阅读记录](../../tasks/braid-console-control/provider-session-reading.md)，其中旧PID和接入身份只作历史证据。

每项访问容器使用原named volume及同一`volume-subpath`，保留实际消费者引用；宿主路径供GC保护，存在性在固定访问容器内核实。最终清理须关闭转发与HTTP、停止访问容器、release接入、明确移除访问容器，然后执行实验资源清理。仅停止访问容器仍占用volume；原生成runtime被移除后，材料读取可继续，物理控制单独报告不可用。创建与核对步骤归[Console README](../../braid-console/README.md)，最新部署回执归[I13-2部署记录](../../tasks/iteration13/i13-2/console-deployment.md)。

2026-10-02 的审阅阅读修复已切换到 Debian-Rebuild 稳定根 `/home/yyh/.local/share/factory26/exp-console/20261002-review-sessions`，保持原 service ID `8cc80cad-d873-49ed-ab49-e958ba8852a3`、七条登记、原 binary 和访问容器绑定；当前 HTTP PID1676167，instance `8ccaaf92-02f0-4a60-904e-5564ba6957c3`。旧 HTTP 已退出，旧 manifest 已退役，配置及 journal 原字节保存在对应后继根 history，不新增访问容器、模型运行或自动启动。Mac8765仍使用原转发。PR2 → review1 → reviewer agent → provider → 原生对话/Trace、provider 深链刷新及返回审阅已实际操作；七项 Issue 与 sessions 均返回200，真实 reviewer 正文返回200。部署与边界归 [审阅阅读任务](../../tasks/console-reviewer/packet.md)。


## 读取当前远端生成容器

当当前 `lab exp` 的 Braid 数据库和原生会话仍在生成容器 overlay 中，独立访问容器不能共享该现场。应在持有原 experiment 和冻结 controller launcher 的宿主准备 Console，显式登记 Docker `access_mode: "runtime-readonly"`。此方式的 `runtime_container` 和 `cli_container` 必须是同一个原容器完整 ID，并声明实际 SSH `endpoint`、`daemon_id`、`started_at`、owner `labels`、容器内 `binary` 及其 `binary_sha256`、容器内 `state` 和 `workspace`，以及 `exp.experiment/attempt_id`。顶层 `state/workspace` 与容器路径一致；不声明 `mounts` 或 `access_owner`，也不把远端 overlay 路径伪装为本地目录。顶层 `binary` 仍是准备时可核对的同字节可执行制品。

准备时通过冻结 exp controller 核对实际资源与出生身份，读取时再次核对 daemon、容器身份、状态、数据库和 binary。注册必须 `writable: false`；此方式没有物理控制权限，所有写入、暂停/恢复和 `access-start/access-stop` 均拒绝。`release` 仅解除登记，不操作原生成容器。既有独立访问容器的 Unix context、共享挂载及显式控制合同不受影响。

按生产者发布的有效 active bindings 选择实际 attempt 和 Braid run ID，只有数据库已存在才登记。Console 首页刷新对应 attempt 的 `observation.json`，核对 experiment/attempt/job/dispatch 身份，显示实际生产者状态和观测时点；没有登记的运行不会自动发现。生成容器结束后，此只读接入报告具体不可读边界，应将保全后的实际终态材料另行登记 archive，不能把旧 ID 改指另一次生成。切换宿主时保留原服务历史入口和材料。


当前 live provider 若为 `idle`、CLI 明确返回空 `turns`、读取从偏移零开始且该服务此前未读到该 provider 正文，精确登记的 JSONL 路径尚不存在时，原文接口返回 `availability: "not-persisted"`，页面显示文件目前不存在、等待首次轮次持久化对话。它不表示模型正在执行或已经交付应用；上下文替换后准备好但尚未收到新输入的 provider 可以处于这个状态。已有 Turn、该服务此前读到过正文、其它文件错误或非零偏移的缺失仍保留具体读取错误，不能都当作等待。
