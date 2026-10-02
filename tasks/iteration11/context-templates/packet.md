# Braid上下文与事件模板精简

用户提出去除单仓库重复身份、无实际能力的metadata、合并短元数据到heading、thread用层级呈现、正文使用代码围栏，并要求提供现有模板共同审查。
用户已批准方案、review findings及修复，另明确createdAt/updatedAt无需显示。源码实施与编译、归档对象只读核对已完成，见 implementation.md。尚未部署或运行模型：不显示时间、不改变存储时间和投递/重建时机；第一轮曾完整保留关联Issue；第二轮已改为仅展开OPEN关联Issue正文，以下第二轮记录为当前行为。I10保持暂停。

- [实施与核对记录](implementation.md)：源码改动与实际归档输出。
- [现状与方案](review.md)：真实入口、观察、建议与待复核边界。
- evidence/context-renderer.rs.txt：改动前renderer完整源码快照。
- evidence/instructions-events.rs.txt：改动前系统指令与事件模板源码快照。
- evidence/github-actual-context.md、sheet-actual-context.md：I10归档中的实际context.md全文；是已运行旧版，不冒充当前I11源码输出。

实施范围：context.rs物化输出，group/provider.rs事件/重建消息，dispatch.rs首次包裹文案，objects.rs事件引用和CLI同源正文呈现。根提醒已核对并保持原样。系统提示中的完整CLI导航另列，不以本次模板精简擅自改变工作方法。

## 第二轮复审（源码完成，未部署）

用户要求成员目录转CLI按需读取；PR只展开OPEN关联Issue正文、不带comments（用户已澄清）；hidden/resolved去Read提示，resolved整树只留根；按模型窗口20%分档降级；考虑根负责人跨工作项整理讨论。上一轮源码完成不代表本轮要求已实施。
调查确认目录有CLI context前缀和provider固定instruction两个入口；现有阈值是bytes而非model token window，不能直接复用为20%。共用instruction已经介绍hide/resolve，故不能将未使用直接归因为提示词缺位。需核查实际会话收到的版本与使用时点；先以当前工作流中的整理责任收敛，而非自动判定讨论已解决。
建议分档：完整可见讨论→讨论标题索引→工作项/关联引用最小入口，逐档计量；正文超预算时也须按需读取，不能承诺保留全部正文仍必然低于20%。降档仅影响投影，不改hide/resolve真实状态。具体token计量与resolved后新回复行为须在实施前明确。

用户已明确“其它的我也同意，你可以开始落地了”。范围包括统一token估算、20%预算分档（允许截短description）、按需成员查询、resolved树折叠与后续回复可见、根检查时整理相关讨论。源码及接线已完成；Rust编译、Python语法、归档对象只读核对通过，不启动模型/实验。见 [第二轮实施](second-pass.md)、[渲染记录与新样例](second-pass-renderer.md)。旧 github-pr14-after-cli.txt 保留为第一轮历史证据，当前输出以第二轮样例为准。
