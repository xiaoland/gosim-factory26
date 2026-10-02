# Cleaner 隐藏评论上下文修复

2026-10-02。用户经主会话明确授权：“独立会话立即修复隐藏评论上下文膨胀并至少热部署到I14 cleaner”。范围为模型 context 投影、真实运行读回和该 cleaner 的保全热恢复，不启动新实验矩阵或恢复暂停 dispatcher。

现有 `render_context_comments` 仅折叠 resolved 后代；hidden 分支仍逐条输出作者、祖先与重复理由。改为省略具有 hidden_by 的后代，将自身隐藏的分支根按完全相同的可选理由聚合为一行。root hidden 状态保留；中间节点 hide 只缩减其分支，保留其它可见回复。已 resolved 前缀仍按现有 cutoff 规则处理。原始数据库、正文、hide/resolve 和 CLI 追溯语义不变。

授权运行是 `pi-braid-i14-cleaner--hackathon--github-51de01f10f57f3`，具体实际身份以原 operation、run 与 Docker 读回为准。证据私有目录为 `runs/iteration14/cleaner-hidden-context-20261002/`。主会话拥有资源保护和内存采集等公共改动，本会话不改其源文件，编译时包含完成后的共同修复。

验收使用编译、同一真实 SQLite 快照的旧/新 context 读回、原始评论及线程映射，并保存停写、完整工作区与 Git/数据库/WAL/native 身份。hide 不会清除旧原生历史；不为本次显示修复制造 description 修改或改写原生历史。恢复后实际发送的新输入与历史保留分别报告。禁止测试、smoke、probe、第二采集器及隐藏评分注入。

下一步：实现 renderer 和契约，独立编译 Linux 制品；读回并保全 cleaner，使用既有恢复 operation 接续且核实无双 writer。当前没有可确认的较早完整检查点，选择最近完整停止现场，不凭 Git 或 DB 单件回滚。

## 已取得的反馈

独立 advisor 确认最外层隐藏分支代表和 resolved 截止规则，未要求对象语义变更。本机及 Linux 编译成功；Linux binary SHA256 为 `63fdabce78498bf6164df846308d05c11f640cd844c544f561507d1df82f7e8d`，源码 SHA256 为 `ee2024f9532a50fad021a8c14cb03eb1b699ed4d1b1075f6faccaceb0fe848d5`。逐文件与共同修复制品比较仅 `src/context.rs` 不同。

同一暂停现场 root Issue 1 的旧/新投影分别为 10,696 / 4,833 bytes，估算 token 为 2,892 / 1,427；77 条完整同理由隐藏评论汇成一行。Linux 新 binary 与本机投影逐字一致，77 条隐藏评论原正文仍在 SQLite。证据见私有目录 `context-readback/{before-issue-1,after-issue-1,linux-after-issue-1}.md` 和 `comparison.json`。来源没有隐藏回复，隐藏 thread、嵌套 hide 和 resolved/hidden 重叠尚无该 run 实例，不把编译或源码复核当运行验收。

Docker 实际标签、daemon、StartedAt 与原 operation/run 对齐后，来源容器已 pause；完整现场通过原 helper 导出，尚未启动接续。原生历史不删除，不人为修改 description 触发重建。ARC-only cleaner 新 base 已装配，恢复规格仍使用原模型配方、2GiB/2CPU、五槽共享准入及原 self_funded 完成后应用重放。
