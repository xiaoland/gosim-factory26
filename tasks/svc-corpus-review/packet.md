# SVC 非 V&V Corpus 的后续清理

状态：2026-09-23 设计与验收获批，用户明确允许按方案应用；独立消费预演已通过，进入实施。官网实验仍使用冻结的 ZIP 与指引，Corpus 改动不回写当前批次。V&V 由 [multi-agent 接入](../multi-agent-integration/packet.md) 持有，本包先处理非 V&V 内容，跨包建议见[候选改稿](design.md)。

目标：按真实消费问题重新评估 Corpus 的组织与表达，优先删除、合并和清理；不预设既有“骨架”正确，也不为目录对称性增补内容。开始本任务前重读 SVC 当时版本，不能把旧观察当作永久事实。

已有线索来自 [协作模式分析](../development-loop-review/analysis.md) 和 [共同工作方法](../multi-agent/working-methods.md)：Design 总入口的抽象定义与判断路径可能错位；Implementation 的线性计划缺少通过预演收敛分支的实际指导；无具体消费价值的标签/重复声明需要清理。Sub-agent 方法的工作边界、上下文压缩和局部反馈思路当前用于 profile 设计，本轮不改其 Corpus 正文。

本次只读审计核对 `~/Development/svc` 的当前 checkout 为 `80996c1`（`ref/v15-engineering-simplification`）；Corpus 干净，但 CLI 工作树有其他未提交改动。Factory 旧文档引用的 `393b935` 在该 checkout 中不可解析，实施前先确定目标版本。审计发现 Design 总入口缺从真实旅程收敛方案的判断路径，Implementation 提到线性计划却未说如何预演高代价未知；没有足够证据支持当前修改 Task Packet 或 Sub-agent Corpus。设计、具体改稿、验收和实施门槛详见 [design.md](design.md)。

实施路径：只替换 SVC 的 Design 总入口与 Implementation 计划段落；按 SVC 发布规则同步版本、变更片段及版本断言；运行 Corpus 发布/链接检查和消费场景。Task Packet、Sub-agent 与 V&V 正文不改。预演采用两名独立读者、匿名 A/B 顺序互换：二人均在通用内容应用任务中优先选出候选 Design 的路由、状态与权限判断路径，且没有额外加载 Corpus；在过期外部 API 任务中均先要求最小真实探针、停止条件和首个 slice；在局部变量改名任务中均直接执行，不要求预演。候选文本没有造成明显的额外查阅或简单任务阻滞。

当前门槛：保留实施前基线，然后应用最小文本 diff；验证完成后记录结果与残余。不以增加文件、术语或模板作为成功标准。本任务不阻塞官网批次。
