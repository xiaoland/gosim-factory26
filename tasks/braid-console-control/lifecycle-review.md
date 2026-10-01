# Console 运行位置与生命周期核对

2026-10-01。用户希望查看Console运行位置和架构，随后明确重点是避免再次出现实验存储中的隐含依赖、证据清理及生命周期问题。本次只读核对当前主机状态、源码和已有部署回执，没有启动WSL、Console或容器，没有暂停/恢复生成、迁移或清理数据。

## 当前观察与历史部署

本机8765没有监听，HTTP连接失败。WSL SSH端口122返回连接重置；通过仍可访问的Windows SSH读取 `wsl --list --verbose`，实际为Debian Stopped、docker-desktop Running。Console登记部署在Debian，因此该部署当前未运行。Windows的Docker context为desktop-linux，查询旧registry中的四个完整容器ID均返回No such object；这只能说明这些ID不在当前查询的daemon中，不能证明Debian内其它Docker环境中的容器或文件已经删除。没有启动Debian进一步检查。

当前原始回执归 `runs/braid-console-control/20261001-lifecycle/`。最后一次成功部署为2026-09-30 21:14 CST，服务PID483894；该PID仅为历史身份，来源 `runs/braid-console-control/20260930-session-navigation/deployment.json`。服务目录为WSL `/home/yyh/Development/factory26/braid-console/`，宿主Python服务监听127.0.0.1:8765，Mac通过SSH转发访问。

## 职责与数据路径

浏览器运行React、Ant Design和TanStack Query，Python标准库HTTP服务同时提供web/dist静态资源与API，正常服务不需要启动Node。对象操作通过docker exec进入每run独立访问容器调用冻结Braid CLI；CLI仍拥有SQLite、Git与对象事务。访问容器只运行sleep infinity，与生成容器共享workspace和submission挂载，没有网络，也不运行Agent。生成容器的物理pause/resume经单独Docker适配层控制。

会话目录来自CLI status，原生正文由访问容器内Python按CLI返回的绝对路径分页读取，没有另建Console数据库或复制一套完整原生日志。用户操作追加journal；HTTP服务输出独立日志。浏览器轮询触发对象读取，不触发模型调用。

| 依赖 | 已核实的位置或行为 | 生命周期含义 |
| --- | --- | --- |
| 程序及前端 | 仓库braid-console与web/dist；启动命令使用宿主python3。 | 程序在run外，但没有冻结实际解释器身份；本轮不能确认其解释器是否来自稳定宿主安装。 |
| registry与人工操作journal | `runs/iteration12/restart-20260930/console-runs.json`、`console-actions.jsonl`。 | 长期服务配置和操作证据处在实验目录，按目录清理会同时破坏服务恢复入口及回执。 |
| 宿主binary | 同一run下的 `build/braid`。 | load_registry在Docker模式下也强制检查这份文件，虽然真正CLI在容器中执行另一条binary路径；是额外的启动依赖。 |
| 容器binary与现场 | shared-submission挂载到/workspace/submission，题目workspace挂载到/workspace；Braid state及Git保留原路径空间。 | 访问容器固定依赖镜像、完整容器ID和这些挂载，移动源目录或删除挂载内容会破坏访问。 |
| 原生正文 | native_sessions按CLI给出的绝对原路径读取。 | Console没有从归档manifest选择正文的接入，保留归档不自动使旧路径浏览继续可用。 |
| 服务退出 | server finally只关闭HTTP服务；访问容器独立sleep，restart policy为no。 | 停Console不负责停止或移除访问容器，也不表示这些外部引用已解除。 |
| 日志 | 最新部署日志位于/tmp；HTTP逐请求输出及人工journal均没有轮转实现。 | 两者应分别确定保留/轮转策略；当前没有复刻完整OTLP/native导致同等膨胀的机制。 |
| GC引用发现 | 当前lab/gc.py只扫描active/archive/manifest/recovery-workspace/run记录。 | Console registry不在已支持记录域，完整扫描标志不代表Console引用已被发现。当前只读plan及显式protect边界已反馈存储整合者。 |

源码入口为 `braid-console/server.py::load_registry/main/journal`、`docker_runtime.py::cli_command`、`native_sessions.py::read_page` 及 `lab/gc.py::plan`。挂载与容器历史身份来自 `runs/braid-console-control/20260930-control/final-container-states.json`，registry来自会话部署前保存的 `deployed-before-console-runs.json`。

此前还实际发生过Console证据目录及旧服务日志路径在整理期间消失、通过进程打开的fd补存日志的情况，来源见[会话导航部署](session-navigation.md)。这说明依赖清理后的恢复入口确实需要梳理；不能据此断言本次停止或三份缺失原生日志的具体原因。

## 建议收敛的边界

将Console自身的服务配置、版本身份、日志和运行回执放入稳定的服务归属；registry只引用受管理的binary、运行现场或归档。将活跃可写现场与归档只读浏览分别定义，使历史浏览可脱离旧生成workspace和长期sleep容器。接入现有依赖记录或在已支持范围外明确protect；只有停止相应消费者并确认引用解除，才讨论回收。具体启停要分别覆盖HTTP进程、转发和访问容器，日志与人工操作journal按其证据价值分别保留。

这些是本次调查形成的后续方案方向，不是已经完成的迁移。当前不以“Console已停”授权清理，不恢复Debian或I12。Bub/Alma新增provider能力另归[独立任务](../braid-provider-expansion/packet.md)，不与此生命周期整理或I13混合。

后续源码收敛和新制品中的只读反馈已完成，见[实施回执](lifecycle-implementation.md)。这些结果不等于旧WSL服务已迁移或恢复；本页主机状态与原部署事实仍按上述调查时点理解。
