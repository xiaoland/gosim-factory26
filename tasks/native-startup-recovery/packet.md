# 原生启动取证与接续能力

## 目标与授权

2026-10-07 用户明确：“是的，创建 task packet，然后开始改进”。本任务改进 variant／Braid／Pi 适配的启动可观测性和原生接续能力，不将原生状态修复下放给 Lab。Lab 继续负责 run 生命周期、程序装配和 data 迁移。

本侧会话不调用 sub-agent，不控制主会话的在途运行，不启动付费模型、不参赛、不覆盖旧现场。源码已有大量其它任务改动，保留原样，仅添加可明确归属的局部增量。没有本侧会话的 Git 提交或部署授权。遵守项目规定，不维护或运行 Factory/Braid 测试、smoke 或换名探针；用编译、实际操作及另行授权的真实运行反馈。

## 已确认的问题

原 run `782227e2db174c98a41eca4b7141289e` 的 Pi 根会话创建在 `get_state (180s)` 超时后失败，数据库没有 provider session 或 turn。日志显示 pi-subagents 导入139,478ms，Pi内部启动149,997ms；从外部进程启动到报告握手超时约186秒，内部计时未覆盖全部区间，不能把模块导入慢当成完整根因。终态资源记录没有OOM或pids触顶证据。

接续 `1e1ff0eaf144481baccd1642c3d3b456` 的 assignment ID、generation、blocked错误及失败时间与来源相同，provider_sessions和turns仍为0。Braid恢复候选依赖已有provider_sessions，而首次创建前失败没有这一记录；原blocked assignment又阻止普通物化。第二次blocked不是第二次握手超时复现。

证据为两run的 `data/harness/782227…/braid-state/{braid.sqlite3,status.json}` 与原 `braid.log`。SQLite取证使用只读immutable连接，没有修改运行数据库。

## 实施与完成边界

先在Pi适配的原生RPC边界保存请求提交、响应收到、超时和耗时，使外部启动时间与内部加载计时可对应；复用现有tracing/OTLP，不记录提示词或认证内容、不建第二套采集系统。随后收敛创建前失败的显式重新物化路径：只处理没有会话、原执行已结束且工作仍有效的assignment，不清空数据库、不伪造恢复、不在同次启动中无限重试。

完成须能区分首次创建与既有会话恢复，保留原失败证据，并以正常原生入口证明创建前失败可重新尝试、既有会话不会重复创建。编译只证明源码完整性；旧失败现场的静态查询不证明新接续已通过。

## 当前进展与接续点

本侧会话已在 `sources/braid/src/provider/pi.rs` 添加局部观测：RPC开始、写入/flush失败、提交、完成/失败、进程启动以来耗时、首条stdout，以及迟到/无对应pending request的响应。复用tracing，无新依赖、无请求内容或凭据记录，不修改期限、重试策略或运行数据。`rustfmt --check --edition 2024` 与diff空白检查通过；在WorkSSD指定Cargo缓存/target/tmp的 `cargo check --locked --offline` 因缓存缺async-trait而失败，尚未取得类型检查或实际部署反馈。没有改用系统盘缓存。

上一轮共享store源码已出现其它负责人添加的初始物化离线恢复分支，本侧会话没有另建实现。当时它要求worktree为active、物理尝试为failed；原件却为blocked工作树和无身份unknown。用户随后明确“继续推进”，本侧会话沿该分支完成局部修正，不覆盖其它dirty改动。

当前源码增量已完成：初始物化候选接受active或blocked的保留工作树，只选当前最新代次和最近已消费的激活输入；原失败context_error保留。身份缺失unknown仅兼容错误形状为 `provider request Pi get_state (...) timed out` 的旧启动记录，沿原 `--offline-resume` 宿主停止断言和排他锁准备一次重新物化；不创建Lab重试，不清空数据库，不增加同次执行循环。对应操作解释归 `sources/braid/docs/20-product-tdd/local.md`。

WorkSSD专属Cargo缓存已通过锁文件下载依赖，专属target为 `runs/native-startup-recovery/cargo-target`；首次 `cargo check --locked` 成功35.72秒，修正后增量 `cargo check --locked --offline` 成功1.87秒，现存dead-code warnings未扩大修复。diff空白检查通过；Pi文件rustfmt检查通过，store文件rustfmt只报告其它已有格式差异，未整文件格式化。没有运行测试、mock或smoke。

对原1e1ff0数据库的只读查询实际选中assignment `01a11535-c1a4-72b1-8804-e21b26bfba26`、agent `01a11535-c1a4-72b1-8804-e228e56adf84`、activation `01a11535-a4de-78a0-ba59-46f5549718e9`；工作树为blocked，原超时context_error完整保留。这证明候选不再漏掉旧现场，不证明事务已执行或新会话成功。

剩余义务为真实Linux新字节消费和正常原生离线接续资格化。主会话在途运行不由本侧会话控制，没有部署、模型调用或Git提交。下一次正常接续须确认新增RPC事件真实出现、旧失败仍保留、只创建新物化代次而不重复已有会话；若首次启动仍超时，依据新阶段时间继续定位，不再把旧blocked立即返回当作新超时复现。
