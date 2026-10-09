# I11 GitHub 需求与产物断点调查

2026-09-30；状态：产物断点与五类因果链调查均已完成，交回父会话。对象仅为最终重放 `e68661975b53`，源生成 `pi-braid-i11--hackathon--github-0d0cb6e9982fc1`。不混入 Pi Minimal `c3fea0c3488c` 或 Sheet。

## 问题与授权

父会话转交用户语音授权：“从原始 requirement 正向构建关键用户流程/前置条件，并核对最终运行产物的入口、导航、状态建立和功能，寻找高覆盖面的需求→产物断点，再沿同期 Pi sessions/Issue/PR 实现过程找额外解释。”用户补充：“GitHub 生成应用到底如何实现，是否正确使用各组件库及开发框架。”

仅分析现有材料；允许少量有界子 Agent。只写本目录调查资料，不改生成应用、variant 或其它未提交改动；不启动应用、新评测、重新生成、模型试跑、部署或任何 Factory/Braid 测试。需要运行确认时先回报父会话。用户要求静态核查、既有日志与过程证据，不能以低分、协作数量或技术栈标签作因果；未知私有评测影响独立标明。

新增直接授权（2026-09-30，父会话转交）：用户要求“向provider sessions与Braid Issues/PRs定位根本原因，建立造成断点的因果链”，范围为首页唯一Sign in、Checks后合并资格旧状态、Your repositories占位、文件搜索文件名链接、规定初态。要求追首次解释/设计/代码引入、handoff/review/验收及最终集成，核实际上下文和选择，区分事实、解释、替代解释及缺口；产出独立`causal-chains.md`。此次授权更新了此前仅改PR23可得性状态、不补审过程的阶段范围；仍只读，不改任何运行工作项或实现。

本轮分工：三个fresh有界cell分别核首页/菜单、Checks/merge、文件搜索；主线核规定初态和跨断点最终整合，回读关键原文。复用完整lineage及索引，不重新审计全部历史会话。过程材料根为`runs/analysis/braid-context-methodology/github-final-20260930/extracted/evidence/`。

## 依据与分工

- 身份与完整性复用 [已核报告](../../pi-minimal/github-score-analysis/i11-e68661975b53.md)：184/184 冻结应用文件一致，构建及监听成功；官网仅有 4/100 汇总，无逐例失败。
- 过程入口复用 [机制分析](../../pi-minimal/github-score-analysis/i11-mechanisms-forward.md)；PR23终态native已取回，完整过程索引见[lineage报告](../braid-context-methodology/report.md)。本轮按新增授权完成五类断点及末轮收口的定向追溯，不重复全历史审计。
- 最终产物根（F）：`runs/analysis/i11-github-e68661975b53/20260930T033923Z/extracted/template/`。
- 方法：当时的运行分析说明（现已删除）。无 `.agents/` 或 `AGENTS.local.md`。
- 有界 cell：身份/组织；仓库/内容；Issue/PR。主线负责跨旅程、最终依赖与实际组件接线、seed/运行入口和反证抽查；独占写各自 cell 文件。

## 交付与下一步

已读取原始需求全层级描述及关键场景前提，沿入口→前提→动作→结果核对路由、控件、会话、权限、初始化和持久化。三个cell完成各自链路，主线回读首页组合、根ATOMIC投影、foundation页面/helper创建、Checks→merge、文件link、team作用域、M6b场景隔离解释。不是全部原生记录或全部历史验收的全量审计。

- [主报告](report.md)：首页unique Sign in被重复入口打破；Checks局部状态未刷新merge；指定初态/隔离前提；菜单占位与文件终点link缺口，附反证及最小补证。
- [因果链总报告](causal-chains.md)：五类断点的原始要求/实际上下文→解释→写入→handoff/review/验收→PR23/main，分别列事实、机制解释、替代解释与缺证；主线回读关键原文。
- 因果分线：[入口/菜单](causal-cells/entry-navigation.md)、[Checks/merge](causal-cells/checks-merge.md)、[文件搜索](causal-cells/file-search.md)、[规定初态](causal-cells/seed-state.md)，相邻JSON保存原生消息ID/时间/物理行和Braid评论全文。
- [框架/组件](framework.md)：真实package与imports、生产入口、Router/Context/Radix/UnoCSS/Express/SQLite接线、已有构建运行证据及不能证明的部分。
- [身份/组织cell](cells/identity-org.md)、[仓库/内容cell](cells/repo-content.md)、[Issue/PR cell](cells/issues-pulls.md)：局部需求/代码/过程证据与覆盖边界。
- [entry-native-excerpts](evidence/entry-native-excerpts.txt)：精确原生路径、物理行、时间、record id与定向原文；[只读DB观察](evidence/workspace-db-observation.json)仅为下载时库存旁证，不是私有评测trace。

已向父会话及时交回菜单已知残余与初态解释等重要发现，并确认短暂连接提示未造成实际阻塞。五类链完成，无继续扩查项。官方逐例trace/selector与场景隔离方式仍未知；Checks旧gate缺直接浏览器复现；complete-text严格解释未实证。PR23终态不再是缺证。不能将发现换算失分。没有运行或修改应用，没有提交。后续若需实现或运行有界验证，由父会话另定授权范围；本轮任务已交回。
