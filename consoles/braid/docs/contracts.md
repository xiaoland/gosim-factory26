# Console 界面与读取合同

本页描述浏览器与 HTTP 桥的可观察行为，供修改 Console 时定位约束。服务制品、登记格式、访问资源、运行控制和解除引用统一见 [运行手册](../../../docs/deployment/console.md)。当前实现定位见 [组件入口](../README.md)；真实部署与已实测范围按运行手册链接的记录核实，不将实现支持当作实际验收。

## 首页、路径与生产者事实

根路径始终显示 Home。零登记显示空状态和登记入口，不自动选首项；未登记的运行保留原链接身份并给出返回首页操作，不改指另一现场。首页展示 live/archive、写入许可及控制接入情况；这些是登记事实，实际可用性在所选运行详情中核实。生产者记录缺失、解析失败或身份不匹配保留路径与具体错误，不从 Issue 关闭推断实验完成。

登记了 `docker.exp` 的现场从对应 attempt 的 `observation.json` 读取事实，并核对 experiment、attempt、job、dispatch 身份。其它显式现场来源为 `run_record`；归档默认使用保存的 `run.json`。页面保留来源路径、SHA-256、variant、实验名、生产者状态与观测时间；保存状态不证明当前进程或任务终态。Console 不启动实验，也不管理重试、预算或调度，目前只接入 Braid。

页面身份只来自 React Router 的路径，由 `web/src/navigation.ts` 生成和解析：

| 页面 | 路径 |
| --- | --- |
| 首页与运行 | `/`、`/runs/:run` |
| 工作项 | `/runs/:run/issues/:id`、`/runs/:run/prs/:id` |
| PR 审阅 | `/runs/:run/prs/:id/reviews/:review` |
| Agent 与 provider | 在工作项或审阅后追加 `/agents/:agent`、`/providers/:provider`。 |

旧 `?run&kind&id&agent&provider` 不解析或重定向。Python 只为有效页面结构返回前端入口；未知 API、缺失静态资源和不合法页面路径保留 404。取消离页保持原 URL 与草稿，操作中阻止切换；点击、后退/前进及页面关闭均受草稿保护。刷新或离开后草稿不永久保存。

对象列表、详情、已展开讨论和会话目录每五秒读取状态；隐藏正文、已解决历史和原文按需读取。轮询不覆盖编辑与评论草稿，不唤醒模型。Home 首屏独立加载，进入运行后才加载 Braid 对象与 Markdown 阅读代码。

## 对象修改与审阅

现场对象操作只通过登记的 Braid 公共 CLI。编辑、评论、回复、隐藏、解决、关闭与重开使用 `--external`；归档强制只读。写入只有明确的一次 `/api/action` 请求，失败或超时不自动重试。人工 journal 保存输入与实际 CLI 回执；消息已入队、Agent 已读取和业务完成分别核实，界面不根据 CLI 成功推断采用结果。

编辑提交开始编辑时的 revision。发现 revision 已变化时保留草稿并返回 409，用户查看最新正文后可明确采用最新 revision。CLI 没有原子的 revision 前提，最后提交瞬间的并发编辑仍需核对。讨论 resolve 作用于整条 thread，局部整理使用 hide 及原因；隐藏与已解决历史按需展开，后续新回复保留可见性。

PR 详情保留所有 `review_requests` 的入口，包括已完成请求及已合并 PR。审阅详情调用 `pr review view`，分别展示当前执行责任、冻结候选、checkout、实际结论作者及不可变结论。当前适用性变化展示 freshness errors，不改写历史 Approved。审阅会话按 `work_item_kind=review` 和请求编号匹配；结论或 checkout 明确指向 Issue agent 时另给原 Issue 会话入口，不将全部原对话当作本次审阅。归档尚不支持审阅详情，保留具体错误，不从评论拼造记录。

## 会话与原生正文

现场会话目录来自 `status --json.physical_sessions`。`group_id` 表示持久 Braid agent，physical 记录、provider 恢复身份与 native ID 分别呈现。明确的 `replaced/retired` 标为历史，其它状态保留 CLI 生命周期，不推断当前归属。目录按 physical 材料枚举，缺失材料的会话可能未列出；空列表不证明从未启动，历史状态不证明容器此刻运行或暂停。

归档优先读取保存的 `braid-state/sessions.json`，缺失才读取 `status.json.physical_sessions`；冲突时展示缺口，不合并。原文只通过 `native/manifest.json` 的唯一 provider/group/session、工作项和原路径身份匹配，限定归档 native 目录相对路径并核对 SHA-256 与 header。原绝对路径仅是历史事实，不能回退旧工作区或容器。缺 manifest 或正文保留元数据和具体错误。

Provider 默认显示原生输入与 Agent 正文，工具、思考及后台通知折叠为过程活动，错误直接可见。原生 user 标为“输入”，不推断来自人类。工具调用和结果只在已加载记录的唯一 call ID 上配对；父链不连续、压缩或分支摘要构成边界，停止跨边界配对，“已返回”不代表成功。正文、调用和结果均可定位同源 Trace 字节位置，切换保留阅读位置；Trace 保留全部原生事件与完整脱敏 JSON。

`native_sessions.py` 只使用 CLI 返回的精确路径，在登记的执行空间读取 JSONL；浏览器只提交 physical 记录 ID 与字节偏移。读取核对 Pi/Codex header 的 native ID，每批最多 50 条、约 1MiB，保留完整行及稳定字节游标。单行超过 8MiB 明确报错，不截断或跳过；末尾未完整行留待下次读取。历史从开头分批加载并手动刷新，当前已加载末条不代表最新进展。图片等非文本内容呈原生 JSON，凭据字段、Bearer、常见 key 格式及读取环境中的凭据值均脱敏。

只有 live provider 为 `idle`、CLI 明确返回空 `turns`、从零偏移读取且本服务此前未读过该 provider 正文时，精确路径尚不存在才返回 `availability: "not-persisted"`。页面显示等待首次轮次持久化对话；上下文替换后准备好但尚未收到新输入的 provider 可以处于这个状态，它不表示正在执行或已经交付。已有 Turn、曾读到正文、非零偏移或其它读取错误仍保留具体失败，不能都归为等待。服务不重建日志。

## 工作区与 origin 阅读

Agent/Provider 的文件入口读取 CLI 登记工作树的当前文件，包含未提交、未跟踪及 `.braid` 材料。多个不同目录须明确选择；改派可以沿用目录，历史会话路径不是历史快照，也不证明当前归属。目录和正文各保留读取时间，刷新不暂停生成或建立完整快照。

运行级 origin 入口读取本次运行 `state/origin.git` 的 `refs/heads/*`。选择分支固定完整 commit，目录、文件与缓存均绑定它；刷新分支列表保留版本，显式“更新到分支最新”才切换。origin 只包含已 push 代码，空树不能由 Agent 当前工作区替代。阅读弹窗不丢弃下面工作项草稿。

`code_files.py` 在登记 CLI 的同一空间执行固定只读 reader，浏览器不能指定绝对根路径。读取核对实际容器及最长嵌套挂载来源，拒绝 `.git`、越界和符号链接穿越；符号链接与子模块只展示目标或身份，特殊文件不读取。目录超过 2000 项、文件超过 1MiB 明确报错；二进制和非 UTF-8 内容说明不可预览。代码与 HTML 作为文本，Markdown 使用安全预览，凭据复用原生 reader 的脱敏规则。

origin 使用 `for-each-ref`、`ls-tree -z`、`cat-file`，拒绝 partial clone/promisor 配置及对象标记，并禁用 lazy fetch；不执行 checkout、fetch、clone、filters 或工作树恢复校验。代码阅读当前只接入 live 来源；归档缺少 origin 与工作区映射时直接说明，不读取旧绝对目录、重建仓库或使用最终应用代替分支历史。

## HTTP 接口定位

以下是现有路由入口；字段与类型沿用 Braid JSON 和 `web/src/api.ts`，不在此复制 schema。

| 接口 | 用途 |
| --- | --- |
| `GET /api/runs` | 登记摘要和生产者事实。 |
| `GET /api/items?run=…`、`/api/item?run=…&kind=…&id=…` | 工作项列表、详情。 |
| `GET /api/review?run=…&pr=…&id=…` | PR 的审阅详情，PR 归属由 Braid 核对。 |
| `GET /api/comment?run=…&id=…&thread=1` | 明确展开评论或整条讨论历史。 |
| `GET /api/sessions?run=…` | Physical 会话目录。 |
| `GET /api/transcript?run=…&provider=…&offset=…` | 指定记录的原生 JSONL 页。 |
| `GET /api/code/refs?run=…` | Origin 分支。 |
| `GET /api/code?run=…&source=workspace&provider=…&path=…` | 登记工作区；origin 改传 `source=origin&commit=<完整SHA>`。 |
| `POST /api/action` | 明确的对象修改。 |
| `GET /api/runtime?run=…`、`POST /api/control` | 登记执行身份的实际状态与门控请求，能力、授权和未确认处置见运行手册。 |

HTTP 状态、CLI 退出码与可诊断响应保留在错误中。服务不接受自由 `cli_command`、任意浏览器路径或容器 ID，不在读取或写入失败后偷偷切换另一现场副本。
