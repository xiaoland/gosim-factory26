# Issue 4 ebc5 单元补读收据

## 阅读范围

- 权威可读视图：`/Volumes/WorkSSD/Development/factory26/tasks/iteration11/run-audit/github/cells/m1-m2-rest/visible.txt`。
- 单元：`2026-09-29T06-06-09-340Z_01a0ebc5-45bc-775b-a25e-221e837eed23`（Issue 4）。
- 单元边界：`[998398, 1254720)`；下一个单元 ebdc 从字符 `1254720` 开始。
- 本次实际消费：字符 `[1240000, 1254720)`，共 `14720` 字符；输出未见截断。起点落在 ebc5 的 Record 60 中段，完整消费 Record 61–71；未读取 ebdc 的任何字符。
- 交接收据：前缀 `[0,1240000)` 已由 primary 声明实际消费；本文件只记录本次补读，不修改主 `coverage.json`。

## 补读到的事实

1. Record 60 中段继续给出 M2 设计契约：组织仓库沿用 `acme-demo/org-handbook` / `acme-demo/org-private`，seed 的组织、仓库、commit、branch 使用幂等的 insert-if-absent；Issue 4 的三个 M3 依赖（Settings 的 Manage access、仓库概览入口、登录用户的 `Access denied`）登记为 PR #11 合入后的回填项。来源：本视图文件 Record 60（本次范围起点前后的同一记录）。
2. Record 61 显示 `docs/task-packets/m2-issue-4.md` 写入成功。Record 62–63 随后提交 Issue #4 设计评论，工具返回评论 `#68`，并显示向 `@deepseek-5`、`@glm-1` 的投递状态为 `queued`。来源：本视图文件 Records 61–63。
3. Record 64–65 先按 `braid/issue-4-m2` 推送 packet 提交，提交为 `824d29a`；随后用 `--assignee glm-7` 创建 PR。Record 66–67 显示该指派名被 CLI 拒绝（可用池为 `deepseek` / `glm`），所以这次 PR 创建没有成功。来源：本视图文件 Records 64–67。
4. Record 68–69 去掉无效 assignee 后创建 PR #13，基线为 `develop`、head 为 `braid/issue-4-m2`，并明确回执为“未指派；尚未交给独立负责人处理”。这说明当时已经有实施分支和 PR 工作项，但尚无独立负责人交接事实。来源：本视图文件 Records 68–69。
5. Record 70 只显示“开始实施”的计划；Record 71 仍是读取 `frontend/src/contracts/copy.ts` 的结果，没有在本段形成实现完成、测试通过或平台验收证据。来源：本视图文件 Records 70–71。

## 解释边界

Record 62 和 Record 68 的命令正文含有 `[EXACT PARAGRAPH DUPLICATE ...]` 指针。这是可读视图对精确重复正文的表示；不能据此推断外部评论或 PR body 实际丢失正文。对本段能确证的是评论 #68 的接收回执、提交 `824d29a`、PR #13 的创建状态，以及之后尚未出现验收结果。

