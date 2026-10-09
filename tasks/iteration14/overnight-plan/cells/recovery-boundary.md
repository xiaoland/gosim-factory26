# I14 材料、执行与恢复边界

更新于2026-10-03。本页保存本夜实施所需的设施接缝；实验政策归[设计](../design.md)，历史清理终态归[清理回执](storage-cleanup.md)。当前只调查和规划，没有新材料生产、prepare、模型、部署或评分。

## 当前可消费与在途

I13-2仅保留完整Flash/Sheet成果。旧GLM、GitHub、本地baseline及不完整I14现场已按用户许可删除；它们不能再成为resume、checkpoint或评分候选。过去将I14迁到系统盘违反用户规则，不能重用该路径。历史局部响应及资源记录只说明当时接线曾工作，不证明当前候选可运行。

[基建会话](codex://threads/01a0fa4f-471a-7963-a4e5-bc4a6071113e)持续持有公共定义、装配、监控、归档和恢复改动。已交付302878bc、83e723d0，当前实际入口为harness-layout v1：四I14声明只读定义及派生输入，可写state独立；checkpoint/prepared v3保留state与真实definition artifact关系；同一资产中的嵌套定义只装配一次。Hosted package identity不能冒充本地store relation。旧v2仍沿冻结producer的自包含合同，不猜目录排除或升级历史记录。

上述接口已交付main，20源码与生成入口编译、真实材料离线回执已核对；缺新I14 runtime/material，冻结前须生产本夜可消费资产。源码存在、离线生产/装配计时不等于官网启动或热恢复通过。本任务不重写这些设施，也不读取全部rollout来重复其调查。

## 新材料来源与存储

保留hosted-sheet-r2/agent.zip实际含linux-x86_64 runtime：Node、Braid、npm锁及已补丁模块、Chromium；不含e2e addon。其SHA256归清理回执。旧包只是只读基础来源，不能直接代表当前Braid通知、按Braid session预算和I14共同材料。

本机没有/var/run/docker.sock；现有Docker context为default、WSL development-1、Surface development-2。两个远端未证明WorkSSD backing，不能默认用于生产、缓存或自管生成。已安装cargo-zigbuild及其只读Zig、Rust Linux目标，可以调查在WorkSSD派生Linux资产的路径；实际交叉编译和e2e addon装配尚未执行，也未宣称可用。

本夜优先复用现有runtime/material producer，冻结基础来源与实际更新依赖后发布新身份；不要为一次官网实验建立通用远端服务。自管构建的staging、Rust/Node/Python/Zig cache、gateway、短路径socket和回传全部须物理在WorkSSD。runtime.py prepare的home cache、runtime.py linux的默认temporary及e2e入口硬编码/tmp仍是需处理的实际写入点；仅设置TMPDIR不能覆盖硬编码路径。只读公共解释器、已安装库和凭据不需迁移。

## 同一请求fallback与新生成的区别

先冻结逻辑模型、候选deployment、wire ID、endpoint、API及凭据引用；请求只在这条冻结链中切换，Braid/native和当前attempt保持。原HTTP状态、具体响应、实际落点及部分stream边界由请求层记录，429不重新打包或重建Git。未冻结的route、材料或预算变化必须派生新定义；不能把它叫同请求fallback。

恢复只能消费同切点应用/Git、Braid DB/WAL、native session及来源writer关闭证据。官网导出的package identity与workspace ZIP不自然具备checkpoint v3所需的definition store关系；缺少可恢复依据时保存原件并报告，不把ZIP可解压或Git提交当完整检查点。首轮采用干净生成，恢复不进入默认关键路径。若运行故障需要新生成，消费[设计](../design.md)的剩余机会，而非无限设施重启。

完整操作区间分别记录材料请求→可交付包、启动请求→实际入口/首个有效turn，以及明确修复输入→恢复入口。保留具体等待与原错；局部复制、读取或ZIP编码时间不替代端到端结论。应用artifact与评分独立消费，不等待所有遥测收尾，也不将辅助证据缺失自动记作应用交付失败。
