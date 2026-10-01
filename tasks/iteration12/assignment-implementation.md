# 具体成员指派实现记录

用户已授权“这点不需要分析了，直接修改”，并明确要求每个配方在成功委派后递增序号，目录提供下一位虚拟候选。本文记录 Braid 指派实现，整体任务和实验授权仍以 iteration12 packet 为准。

本次只修改 `sources/braid/src/objects.rs`、`sources/braid/src/cli/mod.rs` 和 `sources/braid/docs/20-product-tdd/local.md` 的指派相关部分。保留仓库已有未提交改动；没有修改 provider、scheduler、生命周期、Factory variant、schema 或迁移，没有提交。

## 当前行为

`braid assignee list [--json]` 以一致读事务返回每个可指派配置的下一位具体成员及职责，排除 root-only。目录查询不占号、不创建会话。序号来自 `local_items.desired_member_login`、`assignments.member_login`、`local_subscriptions.member_login` 的并集，只接受精确命名前缀加 ASCII 数字的正整数。每个前缀从自身最大历史序号加一开始；尚无历史从 1 开始；旧全局计数保留 schema 字段但不再参与生成。既有成员身份不重编号。

源码和迁移检索未发现删除这三类身份记录的消费者。0012 迁移已从当时负责人及历史评论作者补齐订阅；当前取消指派、退订和改派均保留订阅行。因此尚未创建原生会话就取消指派的名字仍被保留，不会重新出现在候选目录中。历史身份仅用于确定下一候选，不使任意带数字后缀的输入变成合法成员。

Issue/PR 创建、编辑改派和内部 `set_assignee` 在既有 immediate transaction 内按最新目录精确验证名字并保存该名字；root 初始化仍由宿主 `root_profile_id` 选择配置，沿同一命名逻辑生成根成员。裸前缀、未知、过期及已占用成员被拒绝，错误提示给出最新具体候选，不默默替换输入，不输出内部 UUID 或 Profile ID。验证指派组合在编辑标题、正文和父关系之前完成；失败由事务回滚，不写入对象、revision 或语义事件。

重复 add 当前具体成员，以及 remove 当前成员后再 add 同名，统一按指派无变更处理；标题、正文和父关系仍可照常修改。此时不更换会话、不递增 assignment revision、不新增 Assign/Wake。选择其他候选仍须明确 remove 当前名；同一配方的新候选会实际换名。真实改派沿用现有停止旧 writer、fencing、独立工作区和后续 Assign/Wake 边界。

PR request-id 命中已有对象时，先返回首次创建的 PR 身份、引用及现有负责人，再考虑新建请求的候选验证；首次已消耗候选不会阻断重试，也不会额外占号或激活。创建和编辑回执读取实际负责人，只说明责任已登记；输入、输出和联系使用同一成员名，不声称模型已经开始或完成。

## 验证与交接

2026-09-30 在 Braid 仓库复用现有 target 完成 `cargo check` 和 `cargo build`，两者退出码均为 0；编译给出 13 个已有 unused/dead_code warning。`git diff --check` 通过。build 日志位于 `/tmp/factory26-assignee-build.log`，当前可操作二进制为 `sources/braid/target/debug/braid`。

未编写或运行 Braid/Factory 测试、smoke、模拟探针；未启动模型、生成或 benchmark，未接触原始运行现场、I12 暂停或 pi-minimal 官网运行。真实 CLI 核对由主 Agent 在 `runs/iteration12/assignment-cli/` 的归档副本执行，结果并入整体 packet。本记录只确认源码静态完整性与编译成功，不冒充实际 CLI 验收已经完成。

## 主线集成与实际 CLI 结果

主 Agent 已同步 `sources/braid/src/group/provider.rs`、I12 两份成员指令及 `docs/product-tdd/index.md`：指派输入、对象负责人和联系对象使用同一具体成员名，通过 `braid assignee list` 读取下一位候选，不再要求 Agent 在配方别名与实际成员之间转换。

主 Agent 使用编译后的 macOS 二进制，在 I11 真实归档数据库的独立副本上完成 CLI 操作。原始数据库不变，副本位于 `runs/iteration12/assignment-cli/braid.sqlite3`；命令、退出码、完整回执及操作前后负责人、revision、事件数量保存在 [操作回执](../../runs/iteration12/assignment-cli/receipt.json)。

初始候选为 `glm-17`、`deepseek-24`。PR #23 成功认领 `glm-17` 后，目录显示 `glm-18`、`deepseek-24`；Issue #1 随后认领 `glm-18`，目录显示 `glm-19`、`deepseek-24`。目录读取未新增事件或原生 assignment；取消 `glm-18` 的指派后仍显示 `glm-19`，不回收历史身份。

重复为 PR #23 指派当前成员 `glm-17`，revision 和事件数量均不变。裸配方名 `glm`、已被 PR #23 认领的 `glm-17` 均被明确拒绝，错误给出最新候选；失败操作没有修改 Issue #1 的负责人、revision 或事件。成功回执只说明责任登记，实际原生 assignment 数量始终保持 23，没有启动模型。

该CLI核对完成时，原生会话创建、并发竞争及 PR 创建重试尚无本次运行行为样本，不以编译替代这些结论。随后按用户从零启动授权，此修改已进入 [新I12运行](restart.md)，Linux binary为 `38c68450fa93399e7dabd3c4c912410a503e59152cb13f3d3c724ce7d9fc708d`，已见独立根成员与真实模型/工具执行。旧暂停现场及旧冻结Linux binary保持不变；尚未触发的并发和创建重试仍不写成通过。
