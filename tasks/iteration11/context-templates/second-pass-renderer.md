# 第二轮上下文渲染实施

本轮只调整 `sources/braid/src/context.rs` 的投影，不改变工作项、评论、解析或调度状态。模型注入使用 `render_budgeted(context, soft_ratio, hard_bytes, context_window_tokens)`；CLI 不带 `--window-tokens` 时继续用 `render_complete` 读取完整当前可见内容。`RenderedContext` 增加 `tier`（`full`、`comment_index`、`references`）与 `estimated_tokens` 供诊断，原有文本、修订摘要、字节数和压力字段保留。

PR 首先显示自身说明与讨论，随后只展开关联状态为 `OPEN` 的 Issue 标题和 description，不注入这些 Issue 的历史评论。`Issues:` 行仍列全部关联编号，以免丢失关系。普通上下文对已 resolve 的历史只保留 thread 根标题；cutoff 后的新回复仍显示。若新回复的直接父评论已从投影中折叠，树渲染会把它接到可见根下，同时在标题中标出原 `reply to #ID`。hidden 与 resolved 标题保留身份或隐藏理由，不产生无效的 `Read` 行。直接 `comment view ID` 仍按命令选项显示已展开的 resolved 正文，`--include-hidden` 也能显示隐藏正文；`--thread` 未请求展开时保持折叠。

预算选择依次尝试完整内容、保留 description 但只列评论标题、保留对象关系及截短 description 的引用档。评论索引开头只说明一次按编号读取；引用档给出完整工作项和讨论的 CLI 入口。截短只发生在克隆快照上，不改数据库或原始正文，也不生成摘要。估算按 ASCII 每 4 字符约 1 token、非 ASCII 每字符约 1 token；入选结果须同时满足 `bytes <= hard_bytes` 和 `estimated_tokens * 5 < context_window_tokens`。若引用档逐步缩短后仍无法满足预算，返回包含工作项编号与完整读取命令的最小入口；它仍超预算时标记 `Hard`，交由既有调用方处理。该估算是确定性的粗略预算依据，不是模型 tokenizer 的精确计数。

用 `tasks/iteration11/run-audit/github/snapshot-02/braid.sqlite3` 的临时副本执行现有 CLI 实际只读查询。样例与 CLI stderr 档位记录保存在 [evidence](evidence/)；旧版 [PR 14 样例](evidence/github-pr14-after-cli.txt)未覆盖。下表均为该归档中实际对象的输出，不代表模型运行效果或跨对象平均值：

| 对象与窗口 | 档位 | 估算 token | 样例 |
| --- | --- | ---: | --- |
| PR 14 / 128000 | full | 6121 | [完整投影](evidence/github-pr14-budget-128000.txt) |
| PR 14 / 30000 | comment_index | 4535 | [评论索引](evidence/github-pr14-budget-30000.txt) |
| PR 14 / 8192 | references | 1351 | [引用投影](evidence/github-pr14-budget-8192.txt) |
| PR 14 / 1024 | references | 199 | [最窄窗口](evidence/github-pr14-budget-1024.txt) |
| Issue 1 / 128000 | full | 6867 | [完整投影](evidence/github-issue1-budget-128000.txt) |
| Issue 1 / 30000 | comment_index | 2704 | [评论索引](evidence/github-issue1-budget-30000.txt) |
| Issue 1 / 4096 | references | 635 | [引用投影](evidence/github-issue1-budget-4096.txt) |

在归档 Issue 1 中，[完整投影](evidence/github-issue1-budget-128000.txt)只列 resolved 根评论 #2 的身份；[直接读取 #2](evidence/github-comment2-direct.txt)能看到其正文，[整串读取](evidence/github-comment2-thread.txt)仍折叠正文。[读取隐藏评论 #3](evidence/github-comment3-include-hidden.txt)在 `--include-hidden` 下显示正文和隐藏理由。这些是实际归档可验证的边界；该快照没有被用于构造额外场景。

最终 `cargo build -q` 通过；未运行测试、模拟探针、部署或提交。构建只有仓库既有的未使用代码警告。模型实际 token 使用、提示词总量和执行效果未由这些只读样例验证。
