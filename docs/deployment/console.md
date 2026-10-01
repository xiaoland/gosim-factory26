# Braid Console 开发接入

[Braid Console](../../braid-console/README.md) 是独立目录中的实验基础设施，没有独立Git仓库，不进入参赛包或Harness迭代范围。
前端使用React、TypeScript、Vite、Ant Design及TanStack Query；对象HTTP桥调用配套Braid CLI，修改沿用对象事务和消息投递。物理运行控制归Docker适配层；Braid不依赖Console或实验平台。
通用构建、启动、registry与操作语义见其README，不在本页维护第二份API说明。

长期服务用README中的 `service.py prepare/serve` 放在实验目录之外，冻结程序、前端与稳定Python身份；配置、HTTP身份、轮转日志和人工journal归此服务目录。每run明确 `live/archive`：现场登记真实state、原workspace及受管理binary；归档只读浏览保存状态与manifest定位的原文，不依赖旧生成容器或Git。新制品不覆盖旧服务，不自动迁移历史或启动WSL。
实验启动时登记真实Braid state和binary，用独立运行ID区分当前现场与历史副本。同一Console可同时登记不同实验的多个run；每项独立绑定路径、配套binary、权限和可选生成容器，不要求共同实验ID。受管理Docker控制需要同宿主daemon，不能把跨实验接入解释成已支持跨宿主聚合。
从零入口在运行后创建实际state；不能为页面预建数据库或将旧state改名冒充新运行。
数据库出现后显式register并重启Console；`writable`是现场的对象修改权限，归档强制不可写及不可控制，不根据I11/I12等名称猜测。可选Docker配置单独授权该run的物理控制，并固定本宿主context、完整容器ID、实际宿主挂载及所有权标签。归档缺字段、会话目录或native manifest时保留可得数据与缺口，不能把保存状态当当前执行状态。

服务在运行所在机器监听127.0.0.1，由SSH本地转发供开发者访问。
对象轮询用于浏览器刷新，不唤醒模型；编辑草稿与服务器快照分开保留，CLI写入不自动重试。
写入回执说明实际CLI结果；确认Agent读取，需要对应消息投递和原生记录。

容器运行使用README中的独立CLI访问容器接线，保留原运行的镜像、用户及挂载路径空间。每run的访问容器以`sleep`待命，Console通过`docker exec`执行对象命令，避免5秒轮询重复创建容器。暂停原生成容器后，Console继续访问同一数据库和Git；访问容器无网络，不运行Agent或定期检查。修改registry后只重启Console服务，不恢复或重建生成容器。访问容器的创建、启动和移除由操作方明确执行，失败时保留原错误。

页面暂停当前run时冻结其全部Agent会话及Braid定期检查；访问容器、对象读取和人工草稿继续可用。恢复由用户明确操作，Console不会自动恢复、重建或启动已停止的生成容器。为避开冻结写事务，适配层在同一Linux访问容器内取得现存WAL库的写者门闩，持锁暂停并确认状态后释放；这里只协调事务排他，不修改Braid表。直接Docker暂停的既有现场可能已持写锁，遇到具体锁错误时保留暂停和journal，不通过解锁或自动恢复绕过。

部署验收实际读取各run的列表、根Issue及已有PR详情，并核对原容器`Paused`；已暂停run可请求一次pause核对`BEGIN IMMEDIATE→ROLLBACK`。读取正常、可取得写锁、实际业务修改完成，以及新暂停/恢复行为是不同证据，逐项记录。保留原始HTTP、控制及CLI回执；不为设施验收发送测试评论或恢复模型。

HTTP停止只结束它自己的进程。SSH转发由操作方独立管理；访问容器用配套 `access-start/access-stop` 显式启停且须核对service/run标签、固定context与真实最长匹配挂载。生成容器及其它消费者不归Console清理。容器缺失或daemon不明保留未确认状态，不自动补建、解除引用或清理挂载。

稳定服务的 `manifest.json` 直接进入现有GC记录域，扫描应包含稳定服务根。即使HTTP停了，可恢复配置仍保护程序、Python、现场workspace/宿主挂载和归档；旧registry和未扫描域必须显式protect。显式release接入前，HTTP须停止、转发须由操作方确认解除、Console自有访问容器须已确认停止。release移除当前恢复配置，保留ID墓碑及journal来源回执，不删除数据或容器，也不允许旧ID指向另一现场。访问日志有界轮转；journal保持证据职责，不随日志淘汰。

## 对象、会话与原生正文

工作项页面按 Braid agent → provider sessions 展示当前和历史原生关系，现场来源是登记 binary 的 `status --json.physical_sessions`，归档来源是保存的sessions/status目录；Braid、provider 和 native 身份分别保留。此目录按 physical 材料枚举，空列表不能证明从未执行，缺失正文也不抹去可得元数据。

正文通过 `GET /api/transcript` 按稳定字节游标分页读取，先核对原生 header 的 native 身份。浏览器只传 run、physical 记录 ID 与 offset，不提供任意文件路径；具体分页和数据边界归 Console README。文件缺失或身份不匹配保留错误，不从另一会话补正文。关系、工具 call/result 和原文位置帮助取证，不能从历史 provider 状态推断生成容器此刻是否暂停。

当前已经取得真实 Pi 会话的只读接口反馈，Codex 正文和页面直链、前后导航及草稿保护仍有未验边界。人工编辑成功、控制回执、模型读取消息和最终任务效果分别核实；完整证据及缺口归[会话导航记录](../../tasks/braid-console-control/session-navigation.md)。

## 运行身份与实际验收

当前I12的运行身份、部署PID、人工输入journal与停止证据见 [I12 packet](../../tasks/iteration12/packet.md)、[Console记录](../../tasks/iteration12/console.md)及[部署记录](../../tasks/iteration12/deployment.md)。
I12是人工介入研究条件；旧I11摘剪接续已停止，不再用作当前生成起点。原始记录仍保留，历史页面与旧源码位置仅供追溯。
当前Console控制与验收归 [独立任务](../../tasks/braid-console-control/packet.md)；[暂停访问历史记录](../../tasks/iteration13/console-paused-access.md)保留当时故障和接线证据，不作为I13范围。
