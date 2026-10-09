# SVC Skills 维护入口

本工作树维护八个可独立装载的 SVC Agent Skills。
开发与 analysis 使用的完整 SVC 在独立工作树中维护；不要让运行时 skill 依赖 CLI、Catalog 或 wheel。

## 文件归属

- `skills/svc-specs/`：长期项目知识的权威归属、文档准入与一致性维护；来自完整开发 SVC 的独立技能，不替代或别名映射 documentation。
- `skills/svc-documentation/`：产品目的、技术协作、内部设计、运行知识及其维护；入口、按需 references 和可选模板。
- `skills/svc-task-packet/`：外置任务工作记忆、当前判断与材料采用，按需规划、信息组织和模板。
- `skills/svc-sub-agents/`：自包含的委派判断、工作塑造、能力与反馈匹配、成果采用。
- `skills/svc-investigation/`：调查、调试和 Explorer 委派。
- `skills/svc-design/`：产品、技术和工程判断。
- `skills/svc-implementation/`：实施工作流和 Executor 委派。
- `skills/svc-verification/`：检查设计与结果解释。
- `README.md`、`CONTRIBUTING.md`、`USER_MANUAL.md`：维护和安装说明，不是运行时正文。
- `tasks/`：当前工作与历史证据，不分发给技能消费者。

`cli/`、`tools/`、PDM 和旧发布配置属于继承的历史开发工具，不是本 skill 的安装或发布路径。
历史 `docs/` 和 changelog 不能覆盖本入口说明的当前技能布局。

## 内容撰写

每个方法原则只在一个技能正文位置定义，入口负责指路。
使用稳定术语、明确的主体和动作；条件先于动作，按完整句子换行，不为固定列宽拆句。
行文参考 ASD-STE100 原则，不声称符合其受控词表。
用连贯文字解释因果，列表表达并列事项，只在确实增加信息时使用图示或模板。
保持软件工作方法通用，不引入特定比赛、Harness、模型名称或个人权限偏好。

修改正文时同步受影响的导航和模板，不保留两份竞争定义。
技能及 references 始终保留为独立文件，发现入口只提供名称、description 和路径；不得将正文内联到 system、profile、role 或 task prompt。
直接复核文本、引用与实际分发材料；不创建或运行 Corpus 内容测试或改名自检。
不将技能格式合规等同于实际方法有效，行为效果由获授权真实任务的证据判断。
