# Variant：工作流程、模型与交付接线

源码入口后继：本文件中的 `variants/pi-team-mixed` 现为 `variants/pi-braid`；历史冻结包与运行身份不变。

状态：已按用户开工授权修改 variant 源码，待真实应用/完整 bench 验收。
只改当前开发基线 `variants/pi-team-mixed`；旧 variant、已冻结 ZIP 和运行输入保持原样。
本页落实 [主设计](../design.md)，Braid 接口由 [协作 cell](braid.md) 定义。

## 持续指引与普通 Git

两个 `agents/<id>/instructions.md` 使用主设计中已复核的工作流程正文。
它经 `run.py::native_files` 的 `profile.user_instructions` 进入 Pi 的 append-system-prompt；初始 user message 仍只是处理该工作项。
Issue 承载产品需求、技术方案与验收方案；PR 承载实现计划、必要排障、实现、快反馈和可重复的最终验收。
通用方法按 SVC 入口选读，浏览器 API 按 browser-checks 选读，不在每个材料中复制整个流程。

`run.py` 请求的 `delivery_ref` 改为 `refs/heads/main`。
现有 Braid 初始化已将输入 HEAD 发布为指定 delivery ref，因此不必改输入仓库的 `factory-source` 临时分支名。
根负责人开始协作时，用普通 Git 从 `origin/main` 创建并发布 `develop`；已有 develop 时 fetch 并接续，不强推覆盖。
这属于本 variant 的协作方法，不给 Braid 增加 develop 初始化钩子。
Issue 的个人 clone 可能仍从 main 建立；读取最新共享实现时 fetch 并查看 origin/develop，不能把私人 clone 的初始 HEAD 当最新集成成果。

子任务 PR 使用 `--base develop`，显式 `--head` 必须先发布相应分支。
省略 head 时由 Braid 从选定 base 创建工作分支；复用已有代码时指定其已发布分支，避免在 Issue 和 PR 重做同一份实现。
根负责人创建关联的 `--base main --head develop` 整合 PR，并自行选择负责人。
整合 PR 负责人及其原生 session tree 在最终候选上复用、补齐并运行完整需求范围的自动化检查，修复后复验。
只有对自己实际检查的发布 head 有依据时才 merge，可用 `--match-head-commit` 避免意外合入未检查的新 head；该参数不能替代对 base 变化的判断。
若 base 或候选发生会影响结论的变化，重新取得有效证据。
结果回到根 Issue，由根负责人判断整体交付并关闭根项。

流程提供责任和合作约定，不给 Braid 加入验收状态机、需求覆盖表或强制 reviewer。
协作像人类一样使用 Issue/PR 和评论；需要某位成员回应时使用返回的具体 `@成员名`，而非可指派配置别名。

根 description 保留已批准的任务拆分、需求入口与评测环境限制。
用户已确认责任关系与执行资源解耦；删除 run.py 根 description 中整个三项名额段落及“前一批完成后再推进下一批”的全批次屏障。
保留真实依赖：共享基础合入后才开展依赖它的工作，可独立部分并行，具体分工和启动时机归 LLM。
完成后的负责人和会话上下文继续保留；不要求 LLM 通过关闭工作项或取消指派释放机器资源，也不新加“禁止取消指派”的指令。
本轮不新增并发调度器，Braid 不管理 Pi 原生 sub-agent 生命周期；昂贵模型既有预算规则保持。
此补充已获“确认，开工”授权并删除根提示对应句子；取消指派的独立生命周期修正见 [指派 cell](assignment-lifecycle.md)。

## 模型与能力

| 使用者 | 配置 | 实际修改 |
| --- | --- | --- |
| 根 Issue | GLM-5.3-Flash / high | 保留当前 `ROOT_PROFILE_ID=pi-glm-fast` |
| 子 Issue 与全部 PR | Agent 从 glm / deepseek 中选择 | 保留 GLM-5.3-Flash、DeepSeek-v4-Flash 两个配置；Braid 不增加阶段选型 |
| 原生 advisor | Kimi-K3 / high / fresh | 两套原生材料将 specialist 改名 advisor，替换模型；`native_files` methods key 同步，继续消费 svc-design/workflow |
| 原生 explorer、executor | DeepSeek-v4-Flash / high / fresh | 保留模型；executor 接入 browser-checks |
| 原生 browser-operator | DeepSeek-v4-Flash-Vision-Exp / high / fresh | 保留模型，明确开发探索用途；不把一次观察报告当最终验收 |

所有原生角色继续不继承项目上下文和主会话 skills，由委派者提供必要问题、材料入口和范围。
advisor 提供有边界的判断，调用时机由 LLM 决定，不成为每项工作的固定前置步骤。
昂贵模型按 Braid session 的既有限制保留；原生 advisor 不占这个名额。
模型配置与预算保护是两件事，不通过放宽预算保护实现 advisor 接入。

`build.py` 选入 browser-checks；`run.py` 分发、为主会话启用，并提供已冻结依赖与浏览器路径。
两个 executor 取得工具 skill，按任务需要编写/运行自动化检查。
目前 executor 和 browser-operator 都直接追加 agent-browser 入口；executor 改为优先追加 browser-checks 入口，仍可按需用 agent-browser 探索，避免两个重叠工具指南同时成为默认工作法。

## 完成事实与导出

修改前 `run.py` 不论 Braid 是否 blocked、根是否 OPEN 都可能交付；本轮已加入下表状态边界，尚待完整运行验收。
修正落在此 variant 的生成结束边界，通用 `scripts/braid_runtime.py::load_delivery` 继续只解析指定 ref。
Braid 结果新增根工作项的原始 state 事实；不让 Factory 直接读 Braid 私有 SQLite 或猜测评论含义。

| 生成结束观测 | Variant 行为 |
| --- | --- |
| 进程正常结束，Braid quiescent，根 Issue CLOSED | 解析 origin/main 的确切 commit，导出、交付并记录该 commit |
| quiescent，但根 OPEN | generation_failed，明确“当前无可执行工作，根任务仍开放”；保留现场与原始结果，不调用 deliver |
| Braid blocked/failed、非零退出，或结果缺失/不可解析 | 保留原始原因及已有事实，生成失败；不把已有分支冒充完成 |
| 满足完成状态但 main 不存在或没有应用文件 | 沿现有导出错误处理，保留具体 Git/应用错误 |

根 CLOSED 只是 Agent 的工作项状态，不是产品正确性的机器证明。
最终质量仍由应用的实际验收与外部评分检验；不另造验收证明 schema 或从日志推断质量。
现场清理和会话归档继续在既有 finally 中执行，保留失败工作区；摘要不替换原始 Braid 结果。
main 与 develop 的指向、整合 PR、执行检查的候选和交付 SHA 通过现有 Git、工作项和运行证据关联，不要求 LLM 额外填写实验追踪表。

## 接线预演

1. 新任务的 seed 被发布为 origin/main，根用 Git 创建 develop；首个共享基础 PR 以 develop 为 base，后续成员读取已整合的共享基础。
2. 子任务明确点名根，原评论进入根的上下文；根自主决定继续分派、修订方案或进入整合，不由 Harness 解释“下一批”。
3. 整合 PR 持续引用 develop；完整检查取得的 head 与 merge 使用的 head 对应，main 最终指向合并结果。
4. 根关闭后导出 main；若根没有收到消息而留下 OPEN，即使进程正常退出也保留未完成。
5. 测试脚本或辅助归档失败保留各自原因；不能因没有 trace 附件推断应用失败，也不能因 API 局部通过推断整体验收完成。

这是路径推演，尚未取得实现后的运行证据。
真实验证见 [实施与验收计划](../plan.md)，不创建 Factory 自测或模拟流程。
