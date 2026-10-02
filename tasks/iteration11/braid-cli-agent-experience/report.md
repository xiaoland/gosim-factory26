# Braid Issue/PR CLI 的 Agent 使用体验分析

2026-09-30。分析与设计完成，未实施。建议保留现有对象命令体系，优先补齐**操作范围、写入回执与有界读取**。`gh` 的熟悉词汇有价值，但“与 gh 相似”不能保证 Agent 能判断实际目标、真正发生的变化和失败后怎样继续。

最有力的证据不是选项数量，而是实际恢复链：两题都把“几条回复结束”误操作为“整条 thread 折叠”；一次评论 JSON 被自行截掉 ID 后，又通过重发评论取 ID，造成 #256/#257 重复；错误被 shell 管道包装为 `isError=false`，需要读错误正文及目标状态才分辨。与此同时，按精确 head 合并、单条评论直达、带替代入口的 hide、原子 close+comment 和具体投递回执都发挥了作用。

当前代码已补 resolve 的 root/cutoff/changed 文本回执，也已改正 reset 完成时依据旧 turn 真实终态决定 continuation。**这些不是本轮待重做的功能；历史自编辑/hide 循环不应直接倒填为当前仍必现。**

## 1. 范围、身份与证据强度

依赖仓库实际在 [sources/braid](../../../sources/braid/)，HEAD `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，大量未提交改动。本轮以文件 hash 标识可见工作区：[source-manifest.json](source-manifest.json)。已读 Factory/Braid 的 AGENTS、相关 Rust skill、PRD/TDD 本地契约；不改源码、配置、真实对象，不执行 Braid/gh 对象命令、构建、测试、Agent 试跑、比赛评测、安装升级或提交。

复用 GitHub [report](../braid-context-methodology/report.md)、[runtime-semantics](../braid-context-methodology/runtime-semantics.md)、[coverage](../braid-context-methodology/coverage.md) 与 Sheet [full-lineage](../sheet-effectiveness-analysis/full-lineage.md)。没有重新逐字审完整 lineage；本轮选择8类交互，分项回读10个 native 文件的138条记录，保留原路径/hash/行/时间/toolCallId。主分析另外复核关键原件、当前语义和最终根调用：[case-evidence.json](case-evidence.json)、[primary-native-excerpts.json](primary-native-excerpts.json)。

版本原则：当前工作区、历史冻结源码、实际 binary、原生交互各自有边界。最终 GitHub binary `d76d65…83be` 对应已存 base source+启动 patch；C1/C2/C8 的09-29逐调用 binary hash 未在本轮绑定。早期交互由当时 help/返回直接作证，不以当前实现补写。完整边界见 [semantics §1](semantics.md#1-三种证据不能混在一起)。

- **A：强观察证据**——原始输入/输出与后续状态/更正能连起来。
- **B：强静态证据**——当前源码路径可直接确定，未执行验证。
- **C：条件性风险/设计假设**——存在具体失败或并发路径，但本轮没有实际事故或收益测量。

P1 表示优先纳入下一轮方案；P2 为有证据但可后置或需需求确认的候选。不列阻止当前交付的 P0：本轮没有证明终态数据损坏或业务低分由这些 CLI 问题造成。

## 2. 关键发现与归属

| 优先级 / 证据 | 发现及其实际影响 | 当前状态、归属与下一步 |
|---|---|---|
| P1 / A+B | `resolve reply-ID` 选整 root，cutoff 取执行时整串最大 ID。GitHub #318 和 Sheet #362/#370 都折叠了仍在使用的同串内容；unresolve 恢复整串，还因不支持多个参数产生额外纠错。 | **接口+业务操作单元+方法**。当前已有整串 help/文字回执；剩余是操作前范围与并发边界。D2 建议只读 preview、显式 through、批量 unresolve；不直接引入子树解决。 |
| P1 / A+B | 写回执有空输出、整篇正文、文本、JSON 多种形状。hide/unlink 不能直读 changed；merge 只给 commit，不区分新写 ref/已合并/登记既有整合。Agent 为确认效果再全量 view。 | **接口**。D1 增补简短、opt-in JSON mutation receipt，准确列本次变化、实际状态及持久效果；保留旧字段，优先已有操作。 |
| P1 / A | #256/#257 是“自行截掉 JSON ID→重发 mutation 取 ID”的真重复；JSON body 先按行截断再 parse 也失败过。 | **使用方法为主，接口可辅助**。先保存完整回包再解析；不要为读取重放创建。D5 的幂等键是可选后续，不把本例改写成网络失败。 |
| P1 / B | `view --timeline --json body` 或拼错字段被接受，却返回完整 timeline；`--comments` 同时给出也被忽略。 | **接口**。最小修复为互斥组合及明确拒绝不支持的字段，不让成功退出掩盖请求被忽略。D3。 |
| P1 / B；收益 C | `view --json body` 先加载全部讨论/详情，PR 还构造关联 Issue 讨论；单条 comment 也先读整 thread。edit 无条件回显全文。 | **接口读取实现/成本**。字段选择确实减少模型输出，不能说完全无效；剩余是后端无界工作与长回执。D3 按请求读取，D1 短写回执。未测延迟或节省量。 |
| P2 / A+B | thread 先展开再 head 截掉最新 #347；随后 `comment 347`、`comment create` 误猜子命令。comment JSON 是数组且编号字符串 `database_id`，与 item 及 create 回包不同，曾发生对象/数组误取。 | **发现性+方法**。保留通知中的单条入口，help 明确读/创建入口、JSON shape、ID类型；有界 thread 读取可后置。D3/D6。 |
| P2 / B | list 默认 open/30、倒序，无 has_more/下一页；`--state all` 仍可能只给前 N 项。 | **接口**。先说明截断，沿用 timeline 完整性模式；有遍历需求再上页外壳。当前例没有证明 list 上限造成漏项，不要求立即通用分页系统。 |
| P2 / A+B | close 前先在文字宣告关闭，另一 Agent 实际读到 OPEN；后续关闭成功。跨项 reply-to 被正确拒绝，但错误未指出实际所属 PR。mergeCommit 的 gh 风格字段猜测也失败。 | **使用时序+错误可操作性**。状态动作成功后再宣告；错误包含 requested/actual 与合法字段/读取入口。close+comment 原子性已存在，不要重造流程。D1/D6。 |
| P2 / B+C | PR create 有 request-id；Issue/comment 没有。提交后再读回执仍可能失败。整体 body 替换也没有 read→edit 的版本前置条件。 | **底层操作契约**。保住已提交 ID，区分结果未知；D4 可选 body hash guard，D5 局部幂等键。未证明实际后置读故障或并发覆盖事故。 |
| 已有改进待实际反馈 / A+B | 历史 description/hide 失效→重建/续转→无新事实也刷新有直接证据；当前 Invalidate 仍包含自修改，但 continuation 判据已改为真实终态。 | **生命周期+方法**。保持必要上下文失效，核实际部署身份与未来合法接续，不再泛加“别重复工作”长提示，也不把当前改进倒放回历史。 |

细部源码证据、参数和输出盘点在 [interface-audit.md](interface-audit.md)。当前 help 的依据是 clap 声明及代码，历史 help 有 native 原件；没有运行未经版本确认的现有 binary 来冒充当前 help。

## 3. 实际流程：哪里出错，哪里恢复有效

| 阶段 | 实际交互和恢复 | 能证明 / 不能证明 |
|---|---|---|
| 收通知后取内容 | C3 `comment view 347 --thread | head -60` 只得到根至#345；改 `comment view 347` 后拿到完整目标。C4 完整 JSON 落盘后再解析成功。 | 单条直达有用，shell 截断会损坏目标和 JSON；不是自动 context 降档导致丢失。 |
| 整理工作资料 | C1/C2 resolve 后通过 view 发现同串全部 folded；先错误批量 unresolve，后拆合法调用恢复，另一角色复核当前状态。 | 误用和恢复都真实；resolve 当时自身没有清晰回执。旧 Sheet 汇总中“返回显示整串”应理解为随后 view，不是 mutation receipt。未证短窗口导致产品遗漏。 |
| 传递结果 | C8 首个 JSON 回包前三名 queued 后 ID 被 head 截掉，第二次 mutation 得257；hide257留256与原因。 | 重复由两次客户端创建引起；不能说服务端重复投递。hide不能追回在途已发送通知。 |
| 确认合并 | C5 根使用完整 `--match-head-commit`，返回 `442dc1c…`；同调用 fetch/rev-parse 得同一 main SHA。 | 发布候选与合并目标有强身份核对；不是所有业务需求通过的证明。旁路 `DIFF_EXIT=0` 来自 tail 管道，不当 Git 独立退出码。 |
| 关闭并回复 | C6 close 返回 `issue #1: closed / comment #349`，之后 view CLOSED；跨项 reply-to 348报错，去掉 reply-to、保留导航和@得到351。 | 终态关闭成功；早先 OPEN 读数当时也真实，不是工具漏关；不能推断后来的催问导致关闭。 |
| 无新进展的维护 | C7 明知候选未变仍 hide提醒；原生明确收到“你的修改”重建通知并重复 view/fetch。 | 历史控制流开销成立；不能计算全部额外成本或声称当前一定相同。 |

八例完整命令、错误和定位在 [interaction-cases.md](interaction-cases.md)。大多数 `isError=false` 是包含 tail/head/后续命令的 shell wrapper 状态，不是 Braid 单命令退出码；保留“未知”，不据此认定 CLI 把业务错误返回了0。

## 4. 业务语义必须由 Braid 明说

CLI 对 Agent 的要求不应是“理解 Braid scheduler”，但必须说明每个动作的领域效果：

- **description** 是全文替换；同文不重新失效，可见变化会使本项及有关 PR 后续上下文失效。自写也可触发失效，必要时重建；失效、通知、续转是不同环节。当前 terminal 判据已改善后续续转，不等于可取消全部失效。
- **hide** 是指定评论可见性变更，保留正文/理由；不隐藏后续回复，不向所有参与者重新发正文，不撤销在途已经读到的信息。**delete** 清正文，不能恢复。是否增加 delete 确认不是本任务的核心；更需要 help/回执直说不可恢复。
- **resolve** 是 root 的时间前缀；新回复可见但 root仍可能 resolved。重复执行会吸收新回复，unresolve清整串cutoff。把独立关闭条件混进同串是内容方法问题，工具无法替 Agent 判断哪些业务义务已经结束。
- **关系**：parent 不递归带入完整需求；PR link只是背景。自动关闭来自正文关键词并受 origin 默认分支限制；unlink 不等于删掉正文关闭意图。当前 create/link的说明值得保留。
- **ready/merge/close**：ready只观察 published head；merge操作 origin refs，需要精确 head 条件保护已审候选，可能同时关闭正文引用的 Issue；close记录对象决定，不证明应用正确。返回结果应说明该次真实变化。

详细函数与事务边界见 [semantics.md](semantics.md)，尤其 merge 冲突会保存失败 intent/登记事件后非零退出，以及 post-commit 回执读取可能失败：不能统一宣称“非零=没有任何副作用”。

## 5. 对 gh 的取舍

应保留：对象/动作命名、文件/stdin正文、有限状态与 add/remove、明确目标、字段选择、可遍历的分页、SHA 前置条件和具体错误。Braid现有绑定 run/writer、显式工作项编号比“靠 cwd 或当前分支猜目标”更适合本业务；不需要为了相似而补 gh 全部选择器和交互能力。

不应直接继承：缺参数弹编辑器/浏览器、隐式当前PR和多重base来源、`edit-last`充当精确目标、成功退出泛指“已经合并”、`dry-run`泛指无副作用。gh 官方明确 `pr create --dry-run` 仍可能 push，附件部分失败可能在PR已经创建后非零退出；`pr merge` 在队列规则下可能先排队或启用auto-merge。这些是 gh 的业务功能，不是对 Agent 完整结果合同的替代。[gh create](https://cli.github.com/manual/gh_pr_create)、[gh merge](https://cli.github.com/manual/gh_pr_merge)

gh 的无参数 `--json` 用于字段发现，Braid 的裸 `--json` 表示全字段。保持现有含义并明确差异，不能直接搬 gh 示例；也没有证据要求新增 jq/Go-template 两种表达式语言。[gh formatting](https://cli.github.com/manual/gh_help_formatting)

少量一手工具设计材料支持名称/参数清晰、相关信息与有界结果、可操作错误；不证明 CLI 应替换成 MCP，或这些建议能带来某个节省率。具体20页官方来源及支持边界见 [gh-comparison.md](gh-comparison.md)。

## 6. 建议的最小下一轮范围

[design-candidates.md](design-candidates.md) 已给每项 before/after 命令、JSON 草案、兼容影响、失败风险和静态/离线审阅设计：

1. **D1**：短写回执，明确 changed、实际对象/状态、持久副作用与已完成部分；先覆盖 hide/edit/resolve/close/merge。
2. **D2**：在已有 resolve 回执上补操作前范围和可固定 cutoff；保留整 thread 语义，恢复参数对称。
3. **D3 最小部分 + D6**：拒绝忽略的参数组合；字段按需读取；列表截断可见；明确 comment入口/输出shape、字段和关键副作用。

完整列表/thread分页、body并发guard（D4）、Issue/comment创建重试键（D5）留作 P2 候选。尤其幂等键不能替代保存回包的方法，body guard也不能防止作者本人错误删段。先解决已观察流程，不启动通用 CLI/schema/批处理/生命周期重构。

不需要额外每次人工确认，也不需要自动为“危险”操作加交互。无交互下靠明确参数、前置条件、结果和恢复入口，让 Agent 有能力判断。产品新语义（如 through）仍须在后续实施范围中确认；本分析不授权开工。

## 7. 交付与未决

本目录同时保留主结论、细部审查、8例原生证据、当前源码身份和历史reset函数提取。只进行了已有源码/日志/官方文档阅读、定向提取及报告整理；没有基础设施测试、模拟实验、真实对象操作或收益验证。

剩余未知：当前 dirty源码的部署覆盖；早期逐调用binary身份；现有JSON消费者兼容依赖；未观察过的并发覆盖/提交后读回失败；列表实际漏页频率；净token、时延、成功率和评分效果。已知这些缺口不阻塞本分析交付，也不应被改写成实现验收通过。

若用户认可，下一步是针对选中候选细化实施范围和静态检查/已授权真实反馈入口，再按仓库复核流程进入实现；本轮止于可审查设计。
