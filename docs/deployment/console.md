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

当前I12的运行身份、部署PID、人工输入journal与停止证据见 [I12 packet](../../tasks/iteration12/packet.md)、[Console记录](../../tasks/iteration12/console.md)及[部署记录](../../tasks/iteration12/deployment.md)。
I12是人工介入研究条件；旧I11摘剪接续已停止，不再用作当前生成起点。原始记录仍保留，历史页面与旧源码位置仅供追溯。
