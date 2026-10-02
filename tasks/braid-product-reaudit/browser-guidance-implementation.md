# 浏览器提示词与独立验收技能移除

2026-09-28，本页反映用户最新授权后的源码现状：删除 browser-checks 独立技能及其强制注入，浏览器操作默认使用 agent-browser；最终验收仍须依据需求选择可重复执行的测试或脚本，不绑定特定浏览器工具。此前“给 executor 引入 browser-checks”的改动已被本轮决定替代。

只修改当前 `pi-braid`、`pi-braid-flash-team` 与其共用材料和受影响文档。没有修改 SVC、其它 variant、生成应用或旧冻结包，没有运行或添加 Factory 测试，没有提交。重新打包和旧运行恢复由主线负责，本页不宣称已热更新运行中的进程。

## 已完成的源码修改

| 权威源 | 变更 |
| --- | --- |
| `harness/skills/browser-checks/` | 整体删除，包括 `SKILL.md`、`assets/playwright.config.ts`、`references/writing-checks.md`。 |
| `harness/dependencies.lock.json` | 删除独立技能来源登记；npm 依赖未改。 |
| `variants/{pi-braid,pi-braid-flash-team}/build.py` | 从打包技能选择中移除 browser-checks。 |
| 同两个 variant 的 `run.py` | 主会话 `MAIN_SKILLS` 用 agent-browser 替换 browser-checks；技能复制直接遍历 MAIN_SKILLS，避免重复复制 agent-browser；删除给 executor 强制追加 browser-checks 正文的分支。 |
| 两个 variant 下 5 份 `agents/<profile>/agents/executor.md` | skills 声明删除 browser-checks；正文默认 browser 操作使用 agent-browser，最终验收按需求选择可重复测试或脚本。 |
| 两个 variant 下 5 份 `agents/<profile>/instructions.md` | 明确 agent-browser 为默认浏览器入口，移除 browser-checks 文案；保留开发探索与最终验收的区别。 |
| `harness/skills/README.md`、`CONTRIBUTING.md`、`docs/deployment/index.md` | 同步当前技能入口与注入说明，不再描述独立 browser-checks 技能或强制配置模板。 |

受影响 profile 清单是 pi-braid 的 `pi-glm-fast`、`pi-deepseek-fast`，以及 pi-braid-flash-team 的 `pi-glm-fast`、`pi-qwen-fast`、`pi-minimax`。`scripts/package_agent.py` 默认从 `harness/skills` 取材料，各 variant 的 build.py 选择实际装包项，run.py 生成各自原生模板与 launcher；这些权威源已对齐。

`@playwright/test@1.61.1`、`playwright-core@1.61.1`、预装 Chromium、`BROWSER_CHECK_NODE_MODULES` 和 `BROWSER_EXECUTABLE_PATH` 均保留。已有应用可按自身检查方式使用它们；移除独立 skill 不等于移除工具。

## 保留的命名 session 修复

[agent-browser skill](../../harness/skills/agent-browser/SKILL.md) 继续要求按固定版本 core 手册获取 worktree 命名 session；同一旅程复用，shell 不继承环境时显式 `--session <name>`，同 worktree 并行任务使用不同名称或前缀，交接时传会话名与状态。两个活动 variant 的 5 份 browser-operator 已同步此约定，不再建议单任务使用共享默认 session。

依据为 [浏览器反馈调查](../experiment-infrastructure/cells/browser-feedback-audit.md) 及直接读取本地 agent-browser 0.38.1 的 `skill-data/core/SKILL.md`。这次删除独立验收技能没有改动该规则。

## 恢复旧 native materials 的更新清单

以下是主线准备新的恢复副本时必须处理的消费者，不是在原冻结 ZIP 或历史 rollout 上原地改写。仅替换源码或 Braid 二进制不会自动替换已有 Pi home 内的角色。

| 恢复副本位置（相对该 `.factory26/<run>/`） | 必需动作 |
| --- | --- |
| `work/skills/browser-checks/` | 删除；恢复制品顶层 `skills/browser-checks/` 也不再收录。 |
| `work/skills/agent-browser/SKILL.md` | 同步本次权威 skill，保留命名 session 修复。 |
| `work/capabilities/<profile>/pi` | 从 launcher 去掉 `--skill …/browser-checks/SKILL.md`，确保显式加载 `agent-browser/SKILL.md`。不要删除其它扩展或预算 launcher。 |
| `work/capabilities/<profile>/native-template/agents/executor.md` | 根据当前源码重新生成：删除 skills 字段中的 browser-checks，更新正文，并去掉旧文件尾部已内嵌的 browser-checks 完整正文及其来源行。不能只删除技能路径文字。保留当前 SVC 方法、exploration-tools 与运行扩展配置。 |
| `work/capabilities/<profile>/native-template/agents/browser-operator.md` | 同步当前角色和追加的 agent-browser skill，避免旧默认 session 指引残留。 |
| `work/native-homes/<实际 home>/agents/executor.md`、`agents/browser-operator.md` | 按该 home 对应的 profile 同步上述重建后的材料。旧 native home 恢复会继续读取这里的角色，只有更新 template 不足以覆盖已存在的 home。 |
| `braid-request.json` 与 `braid-state/request.json` 内 `profiles[].user_instructions` | 同步对应 `agents/<profile>/instructions.md` 及运行追加规则；若恢复入口重建请求，使用其权威生成路径，不只改一个副本。Braid 对保留 request 的一致性检查由主线恢复方案处理。 |
| 恢复制品自身的 `agents/<profile>/instructions.md`、`agents/<profile>/agents/executor.md`、`run.py` | 使用新源码，确保后续重新物化不把旧说明写回来；新制品的 build 选择不再包含删除的技能。 |

`native-config/` 若仅为历史归档，应保留原貌；若恢复流程把它当作生成模板输入，则改用新生成材料并记录来源。`materials.json`、实现/包 manifest 等哈希应由主线的新恢复制品流程重新生成，不能保留旧哈希冒充同一材料。历史 Pi JSONL、已发布 Issue/评论和应用检查文件不属于此次重写范围。

## 已有工作方法链与核对边界

两个活动 variant 的主提示词已有“需求分析 → 技术方案与验收方案共同设计 → 实施计划 → 快速反馈 → 整合候选最终验收”的链路。SVC 的设计、实施和验证技能提供按需方法；此次没有新增或修改 SVC，也没有堆叠新的 SOP。独立计划预演在 Factory 开发侧 AGENTS.md 对分阶段复核任务有条件要求，参赛侧没有统一强制步骤，保留先前调查结论。

静态文本检索确认：两个活动 variant、当前 harness 技能/来源登记及受影响开发部署文档中不再引用 browser-checks；全部 variants 当前源码检索也无该字符串，但本次没有修改其它 variant。Playwright 依赖与浏览器环境变量仍可在源码中直接确认。`git diff --check` 在改动范围无报错。未打包、未启动模型或浏览器，也未执行 Factory 测试；热修复是否实际被恢复进程消费须由主线的材料与启动证据确认。
