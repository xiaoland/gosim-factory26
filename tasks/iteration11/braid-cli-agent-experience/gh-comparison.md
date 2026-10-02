# gh 与 Braid Issue/PR CLI：面向 Agent 的有界比较

调查日期：2026-09-30。本文只做一手资料比较和候选分析，不构成实现或实验授权。未运行 gh/Braid 命令、模型、测试或编译，未修改真实 Issue/PR。

**结论：保留 gh 的对象/动作词汇、显式参数、文件正文、字段投影和提交前置条件；不要把 gh 的交互便利、环境推断、复合操作结果直接当作 Agent 合同。** Braid 已具备其中不少能力；优先补齐现有 CLI 的结果与发现机制，不需要为了“Agent-friendly”另造完整 CLI 或 MCP 服务。

本文使用三种证据等级：“文档事实”指官方页面明示；“源码观察”只指已读取的本地入口；“分析/候选”是迁移到 Braid 的判断，未证明改善效果。gh 网页为访问日在线手册，未绑定某个发行版本，因此不能据此断言当前安装版本也支持所有选项。Anthropic 文章发表于 2025-09-11；MCP 引用固定的 2025-11-25 规范；OpenAI 指南为访问日在线文档。

## 1. 按命令核对：哪些惯例可保留，哪些便利有代价

下表“文档事实”均来自对应官方页面；第三列是本次分析，不是 gh 官方对 Agent 效果的结论。

| 操作 | 文档事实 | 对机器调用的分析及 Braid 启示 |
| --- | --- | --- |
| Issue create | 标题、正文缺省会提示输入；支持 `--body-file`，`-` 表示 stdin；可显式选仓库。附件部分失败时仍可创建 Issue，打印 URL，同时非零退出。[官方手册](https://cli.github.com/manual/gh_issue_create) | 熟悉的命名和文件输入值得保留。必填参数缺失应给可修正错误；写入后的失败必须说明已创建对象，不能引导无条件重试。附件是 gh 的具体反例，不代表 Braid 已有同类故障。 |
| PR create | 可由当前分支推断 head；未完全 push 时会询问 push/fork；显式 `--head` 可跳过该行为。base 依次取参数、分支配置、默认分支；`--fill` 可用提交信息。`--dry-run` 仍可能 push。[官方手册](https://cli.github.com/manual/gh_pr_create) | 少打参数适合交互，但 Agent 需同时理解 Git、配置、cwd 和远端。Braid 不应为外观一致照搬这些副作用；“预览”若以后存在，应明确是否零写入。 |
| Issue edit | 可编辑同仓库多个编号/URL；正文设置与增删负责人等操作分开；支持文件正文。[官方手册](https://cli.github.com/manual/gh_issue_edit) | 明确 set/add/remove 能降低语义猜测。批量操作虽减少调用，也引入逐对象结果、部分成功和恢复需求；没有真实需求时不应仅为对齐 gh 增加。 |
| PR edit | 参数接受编号、URL、分支，省略时选当前分支 PR；可改 base、正文、负责人、reviewer。[官方手册](https://cli.github.com/manual/gh_pr_edit) | 多种选择器和隐式当前目标方便人类，但重放时目标受环境影响。Braid 已要求编号的入口值得保留；帮助必须描述其实际支持的动作。 |
| Issue comment | 无正文/附件会交互；支持文件正文，以及当前用户的 `--edit-last`、`--delete-last`；后者可用 `--yes` 跳过确认；`--create-if-none` 仅与 edit-last 配合。[官方手册](https://cli.github.com/manual/gh_issue_comment) | “最后一条”由调用时状态决定，重试时未必仍是原目标。Agent 已知评论 ID 时宜直接编辑该 ID；确认参数不是防止选错对象的机制。 |
| PR comment | 接受可选编号/URL/分支；同样支持正文文件、最后一条评论编辑/删除和编辑器/浏览器入口。[官方手册](https://cli.github.com/manual/gh_pr_comment) | 保留 comment 动作及输入形式，不必复制所有交互入口。评论写入成功、通知送达、收件 Agent 处理完成是三个不同事实。 |
| Issue list | 默认只列 open，最多 30；支持状态、负责人、搜索过滤、指定 JSON 字段。[官方手册](https://cli.github.com/manual/gh_issue_list) | 有界默认输出保护上下文，但 Agent 必须知道“这不是全量”。过滤先于拉取全部值得保留；达到 limit 不自动说明恰好只有这些记录。 |
| PR list | 同为默认 open、limit 30；另有 base/head/draft 等过滤；状态包括 merged；支持 JSON 字段。[官方手册](https://cli.github.com/manual/gh_pr_list) | 过滤应贴合对象语义，不要为表面对称强迫 Issue/PR 共享所有字段。列表摘要应给足编号和状态，让下一次读取无需猜目标。 |
| Issue view | 必须给编号或 URL；评论可单独请求；JSON 支持选字段，默认是终端展示。[官方手册](https://cli.github.com/manual/gh_issue_view) | 明确对象、正文与评论分层读取值得保留。JSON 是稳定字段访问方式；对直接阅读内容的模型，简洁文本也可能更合适，不能一律等同“JSON 更省”。 |
| PR view | 省略参数时展示当前分支 PR；可选 JSON 字段包括 head/base OID、状态和评论等。[官方手册](https://cli.github.com/manual/gh_pr_view) | 内容阅读与机器控制可共享同一领域对象。Braid 宜继续要求明确编号，并给出 merge 所需提交身份。 |
| Issue close | 关闭原因是 completed / not planned / duplicate；自由解释可用 `--comment`，另有 duplicate-of。[官方手册](https://cli.github.com/manual/gh_issue_close) | 有限状态原因与自由文本分离值得保留。关闭状态成功不能外推为应用需求通过验收。 |
| PR close | 支持关闭评论；`--delete-branch` 会删除本地及远端分支。[官方手册](https://cli.github.com/manual/gh_pr_close) | 组合清理是便利，也扩大一次操作的影响。Braid 不应仅为 gh 兼容自动加入清理；任何复合操作需明确结果边界。 |
| PR merge | 可按当前分支选择 PR；支持 `--match-head-commit`。目标分支需 merge queue 时，可能启用 auto-merge 或加入队列；支持 merge/rebase/squash、删除分支等选项。[官方手册](https://cli.github.com/manual/gh_pr_merge) | SHA 前置条件直接保护“读到的提交”与“合入的提交”一致，值得保留。命令成功可能表示请求受理，不能仅凭退出成功宣称已合并；Braid 只需返回自己实际拥有的同步/异步语义。 |

## 2. gh 的脚本能力不能与默认交互体验混为一谈

| 官方事实 | 分析：对 Agent 合同有什么意义 |
| --- | --- |
| 默认输出是逐行文本；部分命令支持 `--json FIELDS`，字段是逗号列表。不带字段的 `--json` 用于显示可选字段。`--jq` 无需安装 jq；`--template` 使用 Go 模板。[formatting](https://cli.github.com/manual/gh_help_formatting) | 有明确字段投影和字段发现是成熟惯例，但支持 JSON 的读命令不代表所有写命令都有同等结果合同。嵌入 jq/模板同时增加表达式语言和引号层次；Braid 已有简单字段选择时，没有依据再引入两套格式语言。 |
| 一般退出码为成功 0、失败 1、取消 2、需认证 4；个别命令可能有额外退出码。[exit-codes](https://cli.github.com/manual/gh_help_exit-codes) | 退出码适合过程控制，粒度不足以说明未写入、部分写入、已受理待完成或能否安全重试。错误必须保留具体原因与已发生结果；不能把所有非零都解释成“动作未发生”。 |
| `GH_REPO`/`GH_HOST` 可决定默认目标；有凭据优先级、editor/browser/pager、TTY、颜色、更新通知等环境设置；`GH_PROMPT_DISABLED` 可关闭终端交互。[environment](https://cli.github.com/manual/gh_help_environment) | gh 可以被配置成无交互脚本环境，但这依赖调用侧配置。Braid 已由宿主绑定身份/运行目录时，应保留该绑定，并在必要错误中指出实际范围；不必每次让模型复述宿主已知信息，也不应静默退到其它范围。 |
| `gh api --paginate` 逐页取完；GraphQL 需 `$endCursor` 与 `pageInfo`；默认每页是独立 JSON 对象/数组，`--slurp` 再套外层数组。加字段会默认把 GET 改成 POST，除非显式 method。[api](https://cli.github.com/manual/gh_api) | 分页终止与输出形状必须显式。API 兜底虽强，但转移了端点、方法、变量和分页结构的负担；Braid 的核心协作读取应尽量由现有领域命令完成，不把常见缺口推给通用 API 或让模型一次吞全历史。 |

可取的是 gh 已经暴露的明确控制方式，不是将其所有默认行为复制过来。上述在线手册也没有给出“gh 对某个模型更友好”的对照实验；本报告不作该推断。

## 3. 少量一手 Agent 工具材料及其支持边界

| 来源与日期 | 可据此采用的原则 | 不能由该材料推出的结论 |
| --- | --- | --- |
| Anthropic，2025-09-11，[Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) | 为重要工作流选择少数清晰工具；返回相关信息；大结果提供过滤、分页和明确截断；错误给可操作的修正信息；格式与工具划分应按实际任务观察。 | 文中内部工具结果不能迁移成 Braid 的收益百分比；没有普遍最佳的 JSON/Markdown 格式；不应为了省调用把任意读写合为一体。 |
| OpenAI，访问日在线 [Function calling：Best practices](https://developers.openai.com/api/docs/guides/function-calling#best-practices-for-defining-functions) | 名称、参数、输出含义要清楚；枚举/结构减少无效组合；已由程序掌握的参数交给程序；总是连续发生的步骤才考虑合并。 | 这些是函数工具的设计建议，不证明 CLI 必须替换为函数/MCP；结构约束也不保证目标正确、权限正确、领域前置条件成立。 |
| MCP，2025-11-25 [Tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) | 区分结构化结果与文本；若声明输出 schema，服务端结果须符合它；区分协议错误和可返回给模型修正的执行错误。 | 规范没有替 Braid 解决 Git/数据库一致性、请求去重或工作项生命周期。引入 MCP 本身不会修正这些问题，也不证明减少模型调用。 |

这些资料支持“合同要清楚、结果要够用、体积要有界”的方向。它们不替代 Braid 的 HLD，也不改变本仓库不运行基础设施测试以及实验须另行授权的规则。

## 4. Braid 当前已有什么

只读观察文件：[sources/braid/src/cli/mod.rs](../../../sources/braid/src/cli/mod.rs)。来源仓库 HEAD 为 `0712a58d0e5f7af225473d6c48c4aa740c20dfbf`，访问时该文件已有未提交修改；以下描述的是 2026-09-30 工作区读取内容，不声称它已提交或已部署。本次未深查对象层事务、调度与失败恢复，也未改动此文件。

- `BodyArgs` 已区分内联正文、文件和 stdin；帮助明确编辑是整篇替换、空内容会清空，并说明进程替换的上游失败风险。这比简单模仿 `--body-file` 名字更接近可操作合同。
- Issue/PR 的 view/edit/comment/close/merge 使用显式数字 ID；`--state`（运行目录）和 Agent 身份有宿主绑定。无需为 gh 兼容加入“省略目标即当前分支”的路径。
- `JsonFields`、`print_list`、`print_view` 已提供字段投影；create/comment 已有 JSON 回执。`ITEM_FIELDS` 同时存在 `id`/`number`、`head_ref`/`headRefName` 等内部与 gh 风格名称；view 还会增加详情字段。
- 裸 `--json` 在 Braid 表示全部字段，gh 的同写法用于字段发现。两者不是完全兼容；不能把 gh 的发现示例不加解释地交给 Braid Agent。
- `print_timeline` 已返回 `has_more`、`next_after`，文本也给出下一页命令。普通 `list` 输出数组或行，没有同等完整性元数据；因此应区分“列表上限”与“历史分页”，不把后者已解决的问题重复建设。
- `PrCommand::Create` 已有 `request_id`；merge 已有 `match_head_commit`。入口同时列出标注“尚未实现”的 squash/rebase/auto/disable-auto；当前能力应如实暴露，不应通过 gh 外观暗示已支持。
- edit/close/merge 等入口不像 create/comment 那样提供 `--json`；`print_lifecycle_result` 已能表达 unchanged。评论回执明确区分 queued/delivered/unreachable，并声明送达不是处理完成。这些现有语义可作为完善结果的一手基础。

## 5. 有边界的候选，按优先级供主方案取舍

以下为建议，不是已批准的设计。每项都落在现有 Issue/PR CLI；不新增通用 API、MCP、模板语言或工作流框架。

| 优先级与候选 | 最小范围 | 可审查的结果与限制 |
| --- | --- | --- |
| P1：补齐写操作的结果合同 | 在现有 JSON 方式上，为 edit/close/reopen/ready/merge 等实际需要机器判断的操作返回对象编号、结果状态、changed，以及确实发生的评论/提交等身份；错误保留具体原因和可确认的已完成部分。 | 调用者能区分 changed/unchanged、对象写入/通知受理/合入完成；无需靠中文成功句反推。不要只加一个 `success: true`，也不要承诺底层无法保证的回滚或 exactly-once。是否能省一次 view，取决于回执是否含下一步真正需要的事实。 |
| P1：完善帮助与字段发现 | 保留现有裸 `--json = all` 语义，说明与 gh 的差异；给 list/view 各自可发现的字段及关键嵌套字段解释；指定公开推荐拼写。尚未实现的选项应在常规发现路径中清楚区分。 | 模型不必故意输入非法字段探测能力。暂不删除已有字段别名，不引入反射/schema 服务；是否隐藏未实现选项由主方案结合兼容需求决定。 |
| P2：让普通列表也能报告“是否读完” | 复用 timeline 已有的完整性思路，先明确 list 排序、limit 的意义与截断提示；只有任务确需遍历时再确定续页参数。任何数组到 envelope 的 JSON 改动需显式处理兼容。 | 区分空结果、过滤范围和截断。不要为了返回总数做额外全量工作；不要复制一套与 timeline 冲突的游标协议。 |
| P2：把已有准确写入路径放在主示例 | 多行正文用文件；已知评论 ID 用 `comment edit ID`；合入前从 view 读取 head OID，再带现有 `--match-head-commit`；PR 重试使用已有 request_id。 | 首先改善发现和说明，保留便捷参数。SHA 冲突后须重新读取和判断，不能自动去掉条件重试。`edit-last` 只适用于确实要修改调用时最后一条的场景。 |
| 后置：按真实重试证据扩大去重/并发条件 | 如果实际记录证明 issue create/comment 重试造成重复，或正文并发修改造成覆盖，再设计对应键/版本条件；先核实对象层现有能力。 | gh 文档中的部分成功只能证明风险类型存在，不能证明 Braid 已发生。不要由此启动全局幂等框架、通用批处理或事务重构。 |

“合并调用”也应有界：关闭并留下解释是既有领域动作，返回二者身份可能足够；把读取、总结、分派、关闭串成一个高层万能命令，则会隐藏 Agent 仍需做出的判断，当前材料不足以支持。

## 6. 收益仍待实际证据，不由接口美观替代

现阶段可以审查的是：是否能明确目标、发现能力、知道结果/完整性、选择正确下一步。不能报告 token 节省、时延降低或任务成功率提升。

若后续获授权在实际任务中比较，应保持模型、初始对象状态和任务一致，观察正确终态、错误对象写入、重复写入、漏读分页、无效参数修复、工具轮次、输出 token 与用时。输出更短却导致更多往返，也可能更差。验收要核对独立对象/Git 结果和实际操作证据，不能让 reviewer 只阅读同一实现即判定成功；本次未创建或执行任何此类比较。

未决事项仅是后续设计输入：哪些写操作回执已能从现有对象层直接取得；list 的稳定排序/续页现状；旧调用方对 JSON 数组和字段别名的依赖；错误发生后哪些已完成效果能被可靠识别。它们需主调查继续核实，不能靠 gh 或 MCP 类比补全。
