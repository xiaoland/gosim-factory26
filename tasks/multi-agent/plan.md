# 验收与实施顺序

## 本轮已授权范围

用户已批准 CLI 对齐、直接 PR 创建的产品调整及单一 variant/config；明确不用实验验收。本轮仅运行 Rust/Python 无模型测试、构建及文档检查。先提交方案和实施基线，再修改源码；完成后提交并汇报，不自动开始下一轮实验。

独立 advisor 已预演直接创建 PR：移除强制请求 comment；可选 request-id 提供明确重试身份，不按正文猜测去重。Git 分支不随 SQLite 回滚，因此创建分支前验证所有关联 Issue，保留残留分支与基准一致性检查；新 PR、关联与激活事件原子提交，现有 writer fencing、ready commit 与 merge journal 不变。使用新增迁移保存 nullable 唯一 request-id，不修改旧迁移。

低成本 Agent 已核对配置消费者：factory、check_braid、playground、concurrency 及文档和测试。活动配置统一到 variants/factory/config.json，backend 默认 pi，可选 codex；显式 --config 保留，旧 runs 不迁移。core probe 仍可独立关闭 SVC，不因此把 Braid 与 SVC 写成源码依赖。

实施分工：Braid worker 独占 sources/braid；主 Agent 修改 Factory 配置、脚本、文档及测试。同步 CLI 的所有生产者和消费者，检查正文/stdin、title edit、结构化输出、过期 writer 拒绝、PR 重试与失败分支、历史 run 读取。最终复核差异，运行本地测试并刷新 Braid build stamp。

## 后续多 Agent 协作（待复核，未实施）

既有完整 Keep 32 项、冻结后评测、官方 runner 不改、原生会话和应用哈希关联、每次实验后先汇报的标准继续沿用。新增验收要证明委派、上下文和实际并发，而不能只检查对象数量或 CLI 退出码。

## 新增判别场景

1. 用确定性 provider 验证熟悉的 view/edit/comment、正文/stdin 和错误用法；写入成功后读回对象和实际 Context，失效 writer 不得修改任何对象。Braid 特有动作明确显示目标和语义。
2. 根 Issue 派发两个有明确范围的实施子任务及一个研究子任务；研究仅返回材料，实施通过 PR 交付。分别证明两个 Issue group 和两个 PR group 有实际活动时间重叠，整体不超过指定容量。父 turn 结束后不会占住子任务容量，子结果能唤醒父任务；不能把“创建两个对象”当作并行验收。
3. 两个 worktree 访问同一公共 packet 材料及各自模块。验证写入所有权、发布版本和公共契约修订后的消费；重建后保留正确材料引用，历史正文不会继续充当当前任务。
4. 故意让一个子任务失败、一个会话重建，并尝试提前关闭根 Issue；核对另一任务仍可推进、错误归属正确、未满足总体交付不能成功封存。合并仍针对明确 ready commit，不复制任意 worktree。
5. Codex/Pi 适配器均做无模型会话隔离检查；首轮真实试验建议选择 Pi backend、并发 2，避免同时变更多个接入条件。接入场景通过后，下一次获授权的完整 Keep 生成和 bench 只执行一次，按结果汇报，不自动扩为两后端或并发消融矩阵。

该方案尚待用户复核，未启动模型或 bench。“实际重叠”和“材料版本生效”须由事件/输入/文件事实独立确认，不能只由负责实现的 Agent 自报。

## 实施门槛与责任

顺序：方案与新增验收边界复核 → 具体实施计划和独立 Agent 预演 → 实现前提交 → 实现及必要检查 → 单次获授权实验 → 结果汇报。

CLI 和单一配置先在本轮完成；父子生命周期、执行容量和公共材料装配留待协作方案复核。SVC 只针对发现的范式缺口调整 Corpus，并独立验证仍可用于不含 Braid 的项目。调度、材料可见性相互有依赖，不分给多个 worker 猜同一接口。

当前预研责任已分离：低成本 Agent 对照 gh CLI、另一个低成本 Agent 查询 SVC 协作范式，advisor 审视执行权威与材料边界，主 Agent 核对实际调度/对象/配置并整合方案。后续实施预演必须覆盖 worker、store claim、parent 事件、Context 投影和 provider 并发，当前方案审阅不冒充已完成的实现预演。
