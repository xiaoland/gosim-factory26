# Braid Issue/PR CLI 的 Agent 使用体验

## 当前状态

2026-09-30，独立分析与设计完成，等待用户选择下一轮范围。接续来源会话 `01a0f01b-c0bb-719d-af64-671b0563103f`；不进入实现准备或开工。

## 问题与授权

用户要求：“从实际Agent使用流程与错误恢复出发，审查Braid当前CLI实现/帮助/输出/运行记录，对照gh官方文档与必要一手agent tool设计材料”，且“严格分析与设计，不修改源码/实际IssuePR/配置，不启动测试、Agent试跑、比赛评测，不安装升级”。允许少量有界子 Agent、只读源码/日志和无副作用帮助。报告保存本目录，保留现有未提交改动；不提交。

范围为 Issue/PR/comment/relationship/hide/resolve/merge/close 等 CLI 交互；区分接口、底层语义和使用方法。gh 是比较对象，不是规范权威。必须确认操作实际影响及恢复边界，不能把历史二进制当当前工作区。

## 方法与分工

- 主分析：核实 description 自编辑、hide 唤醒、resolve thread/cutoff、写入与事件/调度边界；汇总候选、风险和静态/离线核查设计。
- `cli_surface`：当前接口及帮助/返回契约，写 `interface-audit.md`。
- `cli_cases`：复用已有 lineage，定向回读少量原始命令交互，写 `interaction-cases.md` 与 `case-evidence.json`。
- `gh_primary`：gh 官方与少量一手工具设计材料，写 `gh-comparison.md`。

子任务均仅可写本目录的专属报告；不运行测试、构建或真实对象命令。源码位于独立仓库 `sources/braid`；起始 HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf` 且已有未提交修改。根无 `.agents/` 或 `AGENTS.local.md`；已读 Braid 的 `AGENTS.md`、`.agents/skills/rust-code/SKILL.md`；应用 ponytail 技能的小改动原则，服从本任务禁止测试的要求。

## 证据入口

- `../braid-context-methodology/report.md`、`runtime-semantics.md`、`coverage.md` 及其原始引用。
- `../sheet-effectiveness-analysis/full-lineage.md` 及其原始引用。
- 当前源码：`sources/braid/src/cli/mod.rs`、`objects.rs`、`context.rs`、`group/`、`queue/`。
- 已读职责契约：Braid `docs/20-product-tdd/{README,local}.md`，Factory PRD/TDD 与 CONTRIBUTING。

## 结果与核对

主入口为 [report.md](report.md)，候选命令/JSON、兼容风险与静态离线审阅设计在 [design-candidates.md](design-candidates.md)。[semantics.md](semantics.md) 区分历史 binary 与当前源码，核实自编辑/hide/resolve/merge 的事件、事务和恢复边界。接口、8例交互及 gh 一手资料分别保留在三份分项报告中；原始引用未挪动或覆盖。

8例引用10个 native 文件、138条选定记录，不声称完整 lineage 重审。主分析回读两题 resolve、重复评论、hide 重建、merge/close/跨项回复的关键原件；单命令退出码未保存处保持未知。发现旧 Sheet 汇总的 resolve“返回显示整串”实际来自随后 view，以及 DIFF_EXIT=0 来自 tail 管道，已在本报告中澄清，没有改写旧报告。

当前已有 resolve 文本回执与 reset 完成时按 durable terminal 决定 continuation；不将其重复列为未实现。本轮建议先完善写回执、resolve可预见性、字段读取/参数组合；完整分页、正文并发guard和创建幂等键为后续候选。

报告所有本地链接目标已核对存在；源码清单收尾重读hash与开始一致，历史提取的归档/member/hash已记录 [source-manifest.json](source-manifest.json)。Braid工作区仍为原17个已修改文件，本轮只新增本任务目录；未改源码/配置/真实对象，未编译、测试、运行模型或评测、安装升级、提交推送。草案没有提升为已批准长期产品契约。

## 下一步与验收边界

用户决定选中哪些候选后，再细化实施范围与复核。只设计静态审阅/离线证据核对，不新写或运行 Factory/Braid 自身测试。当前源码部署覆盖、早期逐调用binary身份、兼容消费者和收益测量仍未知；这些不阻塞本分析交付，也不表示实现或实验已获授权。
