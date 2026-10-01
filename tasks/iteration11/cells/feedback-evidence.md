# I11 反馈证据与停止条件

2026-09-29。优先级 5：I11-07、I11-09，以及 I11-06 中没有新增信息的重复确认。状态：有界源码实施完成，语法核验通过；尚未通过新 variant 的真实运行证明行为改善，未提交。

## 授权与范围

协调任务本轮转达：“用户本轮明确授权实施”，并指定“落地保存原输出+真实exit再摘要、按候选diff判断证据适用性/停止无必要复验”。本单元拥有 `sources/svc/skills/svc-verification/`、`harness/skills/agent-browser/`，以及必要的 `variants/pi-braid-i11` 角色指令调整。只修改两份主角色指令中的检查执行入口和交接/合并入口；其他成员负责的文档、实现技能及 Braid 改动保留。

本轮未修改 Braid、I10 运行、生成应用的 src/package/scripts，未运行测试、探针、打包或模型实验，未提交。通用原则保存在 SVC；工具用法和输出由 agent-browser 持有；variant 只接入决策入口。

## 问题、根因与修复

证据入口是 [GitHub 全量审查终稿](../run-audit/github/report.md)，重点为“首轮错误先被 grep 丢弃”和文档提交引起复验的分析。以下区分已观察事实与采用效果的推断。

### I11-07：原始失败在摘要之前丢失

PR15 的 `Vitest | grep 'Test Files|Tests |FAIL' && ...` 留下 5 failed / 98 passed，但 grep 成功令后续继续，整个 shell 返回 0。原始堆栈在 PBB 收到输出之前已经丢失。随后两次通过不能解释首轮失败，负责人却将它加强转述为足以排除代码问题。根侧也存在 `tail` 后误读退出值的同类记录。

工具并不缺失：现有 `with-service.py --check-only` 已经把传入命令的 stdout/stderr 写入 `check.log`，把该进程的真实退出值写入 `result.json`；基础 PR2 也实际使用过它。审查没有看到 PR15 读取这个入口。原指令只说“可从 agent-browser 技能取用”，工具归在浏览器技能之下；这说明入口未被采用，不能证明模型忽略它的唯一心理原因。

修复将已有能力放到首次检查之前的选择点：执行工具已经完整保留输出和检查退出值时直接复用，否则读取并使用现有包装。API、构建和自带服务的 runner 都从此入口可达。SVC 的 repeatable-checks 将原有保留结果原则改为“先选保存入口，执行后从保存结果生成摘要”，并保留首轮缺证与后续通过的解释边界。agent-browser 明确将未过滤命令交给包装，从 `check.log` 取摘要。

`with-service.py` 的最终输出现在直接显示 `status`、`check_exit`、`cleanup_status`、`check_log` 和 `receipt`，避免只看到一个 passed 字样而忽略退出值与清理结果。原日志保存、进程所有权和退出传播逻辑没有改动。传入的 runner 若自行吞掉失败，包装只能记录该 runner 的退出值；没有新增 shell 推断、拆分或拦截逻辑。

### I11-09 / I11-06：候选身份变化被当作全量证据失效

PR15 在 `bab2b11` 已取得平台 58 PASS，随后为更新 packet 产生 `6f272e7`，负责人要求重新锚定，worker 又重复本地检查。基础 PR2 和 PR13 此前已有通过 diff 接受证据继续适用的正例；问题是不同交接使用了不同判据。原有 SVC 已说明复用有效证据、负责人变化不是新条件，单纯再加一句“不要重复”不能解释这一断点。

修复把已有解释原则变成交接和复验前的具体判断：在原任务记录中连起需求、原始结果、实际检查产物与条件；检查当前候选 diff 及构建、检查代码、数据、依赖和环境变化；说明哪些结论可能失效，再决定复用或补查。只因记录结果而新增提交，不自动要求同一轮验收再次运行。文档若被构建或运行读取仍可能影响行为，不能按文件后缀一律豁免。

两份主角色指令在交接/合并点指向这一判断。`--match-head-commit` 继续保护当前已发布候选，原始运行仍标记实际验过的产物，另记证据对新候选适用的理由。证据满足当前验收义务且没有未解决矛盾后交接并停止；新确认或相同通过次数不替代新证据。真正影响集成的 base 或候选变化仍需取得相应反馈。

## 修改位置与接线

- `sources/svc/skills/svc-verification/SKILL.md`：加载描述包含保留证据与复验前适用性判断。
- 同技能 `references/repeatable-checks.md`、`references/interpreting-results.md`：替换原有相关段落，不建立另一套原则文档。
- `harness/skills/agent-browser/SKILL.md`、`scripts/with-service.py`：现有包装的调用边界和完成输出。
- `variants/pi-braid-i11/agents/{pi-glm-fast,pi-deepseek-fast}/instructions.md`：首次检查、交接与合并两个入口。

已读取 I11 的 `build.py` 和 `scripts/package_agent.py` 接线：variant 选择 svc-verification 与 agent-browser，assemble 复制角色目录和所选技能；`harness/skills/svc-verification` 链接到此次修改的独立 SVC 仓库。没有创建只存在于开发目录而不被选择的新工具，也没有移动技能树。本轮没有实际打包。

## 核验与限制

用 Python 内置 `compile()` 解析修改后的 `with-service.py`，通过；没有执行模块或检查命令。两处仓库针对本单元已跟踪修改的 `git diff --check` 通过。人工阅读了修改前后完整相关段落、工具实现、角色入口和打包材料选择；两份角色指令均已接入相同入口。

这些结果只说明语法和文本接线一致，不能证明模型行为已改善。后续获授权的新 variant 运行应从原始轨迹确认：首次检查是否在过滤前留下完整输出和真实退出值；首错缺证是否仍被如实保留；候选文档变化是否通过实际 diff 判断；缺口已满足后是否交接停止。尚未运行这轮实验，不在本单元宣称 I11-07/09 已通过行为验收。
