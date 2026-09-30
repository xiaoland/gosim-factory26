# I12 实时协作 Console

目标是让开发者在 I12 的 GitHub、Sheet 两个 Braid 运行中实际操作 Issue/PR，而不是让 Agent 额外承担可观测性工作。获授权范围包括本地网页、明确的运行 registry、独立介入 journal 和使用配套 CLI 的写入。I11 如需对照，只读登记。Console 不进入参赛交付。

实现位置为 `lab/console/server.py` 和 `lab/console/index.html`；运行方法归 [部署说明](../../docs/deployment/console.md)。现有 `lab/analysis/run_viewer.py` 是归档快照；`tasks/official-collaboration-review/template.html` 的对象列表、讨论层级和状态标签供界面参考。实时操作需要 CLI 读写，因此不复用静态导出流程或引入前端框架。

实际 CLI 契约：`issue/pr list --state all --json` 返回数组；`issue/pr view ID --json` 返回正文、状态、负责人、关联、revision 和评论。隐藏或已折叠评论在对象视图中可省略正文，`comment view ID --include-hidden --json` 是取回现存正文的读接口；`--thread` 可按需展开整条历史。默认轮询不逐条读取折叠正文，新回复仍在对象视图中可见。`--external` 由宿主提供写入身份，评论作者为 `external`。编辑正文通过 `--body-file -` 从 stdin 输入，评论可加 `--reply-to`；隐藏、解决和生命周期操作经 CLI 执行。所有命令使用运行 registry 中固定 binary/state，不从浏览器接收路径或任意命令。

已按主线冻结的恢复目录与内部运行 ID 写入 `runs/iteration12/recovery/console-runs.json`，其中明确指向 WSL 的两个 I12 state 和同一配套 binary；文件属于 Git 忽略的运行材料。待恢复 workspace 和 Linux binary 落地后，先核对路径存在、CLI 只读返回，再在 WSL 启动服务。验收用语法检查、真实只读状态调用和浏览器实际操作反馈；遵守仓库禁令，不写或运行 Factory/Braid 测试、自检或 mock。人工 POST 只在运行介入确实需要时发出，不以预演随意改动实验对象。运行期间若发现写入回执不确定，先核对对象和 journal，再由操作者决定下一次明确动作。

2026-09-30 已用 I11 归档状态和本机当前 Mach-O binary 做只读预演：CLI list 字段选择返回 9 个 Issue，view #1 含 78 条评论，折叠评论 #2 的 direct view 可读取现存正文；HTTP `/api/runs`、`/api/items`、`/api/item` 均返回有效 JSON，页面在浏览器中显示 22 个 Issue/PR、负责人、状态、关联和讨论，I11 不显示写入控件。Python 与浏览器 JavaScript 语法检查通过。Linux binary 在 Mac 上报 `exec format error`，这是平台不匹配；I12 的 Linux 只读和实际写入仍待在 WSL 使用本轮 binary 核对。

随后按阅读负载修订：对象轮询不逐条补读折叠评论；浏览器在 Issue #1 初始显示 11 条已解决线程摘要和 47 条可见评论，展开一条后显示 49 条，再折叠会丢弃该线程缓存。未解决的新回复不随旧历史折叠。Mac 和 WSL 均有 `markdown_it`，页面采用禁用原始 HTML 和图片的渲染；浏览器实际显示格式化标题与列表、无图片节点。两个 WSL state 已恢复到登记路径，console 两个源文件及 registry 已小文件同步，WSL import/renderer 初始化与 registry 路径校验通过。

配套 Linux binary 冻结后已完成该核对：GitHub state 为 9 个 Issue、13 个 PR，根 Issue revision 54、78 条评论；Sheet state 为 6 个 Issue、7 个 PR，根 Issue revision 48、176 条评论。WSL 服务监听 `127.0.0.1:8765`，Mac SSH tunnel 映射同端口。HTTP 两侧列表与详情均返回 200；浏览器实际看到 GitHub 22 条、Sheet 13 条以及标题、负责人、讨论和可写控件，未见页面错误。服务 PID、日志和操作 journal 位于 `runs/iteration12/recovery/`。启动核对阶段没有发送 POST、启动模型或通过 console 写入数据库。

主线随后明确授权一次真实人工介入条件设定：在两题根 Issue 各发表同一条评论「本次为I12人工介入研究运行；用户可在这里澄清、纠正或提出工作请求，按讨论中的明确输入继续协作。」浏览器 console 实际写入 GitHub Issue #1 评论 #333、Sheet Issue #1 评论 #567；两次操作的 journal 均为 `started → completed`，无不确定回执。配套 CLI `comment view --json` 读回两条均为 `external` 作者、正文逐字一致，分别向 `glm-1`、`glm-9` 返回 `queued`。只读 SQLite 一致快照进一步核实两个评论的 writer_group/writer_turn 为空（外部作者），对应的 `local_comment_delivery` 指向 `events` 中 `origin=local`、`kind=wake`、`lifecycle=pending`、目标 `issue:1`；这是消息入队，不等于 Agent 已读取。本轮 console 未发送其它 POST，后续具体纠正由用户自己提出。
