# Braid Console 开发接入

[Braid Console](../../braid-console/README.md) 是独立目录中的协作工具，没有独立Git仓库，不进入参赛包。
前端使用React、TypeScript、Vite、Ant Design及TanStack Query；HTTP桥仅调用配套Braid CLI，写入沿用对象事务和消息投递。
通用构建、启动、registry与操作语义见其README，不在本页维护第二份API说明。

实验启动时登记真实Braid state和binary，用独立运行ID区分当前现场与历史副本。
从零入口在运行后创建实际state；不能为页面预建数据库或将旧state改名冒充新运行。
数据库出现后登记并重启Console，旧副本如需对照仍保持只读；`writable`是明确权限，不根据I11/I12等名称猜测。

服务在运行所在机器监听127.0.0.1，由SSH本地转发供开发者访问。
对象轮询用于浏览器刷新，不唤醒模型；编辑草稿与服务器快照分开保留，CLI写入不自动重试。
写入回执说明实际CLI结果；确认Agent读取，需要对应消息投递和原生记录。

容器运行使用README中的独立CLI访问容器接线，保留原运行的镜像、用户及挂载路径空间。每run的访问容器以`sleep`待命，Console通过`docker exec`执行对象命令，避免5秒轮询重复创建容器。暂停原生成容器后，Console继续访问同一数据库和Git；访问容器无网络，不运行Agent或定期检查。修改registry后只重启Console服务，不恢复或重建生成容器。访问容器的创建、启动和移除由操作方明确执行，失败时保留原错误。

部署验收须实际读取各run的列表、根Issue及已有PR详情，并再次核对原容器的`Paused`状态；读取成功不单独证明写入可用。若原进程暂停在SQLite写事务内，按实际错误及journal处理，不通过解锁或自动恢复绕过。

## 对象、会话与原生正文

工作项页面按 Braid agent → provider sessions 展示当前和历史原生关系，来源是登记 binary 的 `status --json.physical_sessions`；Braid、provider 和 native 身份分别保留。此目录按 physical 材料枚举，空列表不能证明从未执行，缺失正文也不抹去可得元数据。

正文通过 `GET /api/transcript` 按稳定字节游标分页读取，先核对原生 header 的 native 身份。浏览器只传 run、physical 记录 ID 与 offset，不提供任意文件路径；具体分页和数据边界归 Console README。文件缺失或身份不匹配保留错误，不从另一会话补正文。关系、工具 call/result 和原文位置帮助取证，不能从历史 provider 状态推断生成容器此刻是否暂停。

当前已经取得真实 Pi 会话的只读接口反馈，Codex 正文和页面直链、前后导航及草稿保护仍有未验边界。人工编辑成功、控制回执、模型读取消息和最终任务效果分别核实；完整证据及缺口归[会话导航记录](../../tasks/braid-console-control/session-navigation.md)。

## 运行身份与实际验收

当前I12的运行身份、部署PID、人工输入journal与停止证据见 [I12 packet](../../tasks/iteration12/packet.md)、[Console记录](../../tasks/iteration12/console.md)及[部署记录](../../tasks/iteration12/deployment.md)。
I12是人工介入研究条件；旧I11摘剪接续已停止，不再用作当前生成起点。原始记录仍保留，历史页面与旧源码位置仅供追溯。
I12暂停后访问的修复及真实操作边界见 [I13 Console暂停访问记录](../../tasks/iteration13/console-paused-access.md)。
