# attempt02 的视觉子 Agent 与需求整理证据

2026-09-28 03:39:18 UTC 只读截面。**确实调用了 DeepSeek vision，但只在 DeepSeek Direct Sheet 的 Issue #5 中调用一次，用于局部需求/UI 参考图分析。根任务最初整理需求和拆分 Issue 时未观察到 vision 委派；Flash 两题和 DeepSeek GitHub 均未观察到 vision 调用。** Flash 保持 cancelled，DeepSeek 两题在读取时仍 running；本次没有重启、修改运行或调用模型。

## 按 case 的实际计数

| case / 内层 run ID | vision 委派 | 实际子会话 | 实际模型响应 | 图像用途 |
| --- | ---: | ---: | ---: | --- |
| Flash GitHub / `20260928-025803-8d9418d2` | 0 | 0 | 0 | 未观察到 |
| Flash Sheet / `20260928-025750-fb85c109` | 0 | 0 | 0 | 未观察到 |
| DeepSeek GitHub / `20260928-030347-78b10c07` | 0 | 0 | 0 | 未观察到 |
| DeepSeek Sheet / `20260928-025746-66feadac` | 1 | 1 | 2 | 3 张 `input/reference/` 需求参考图，非生成应用截图 |

本次分别扫描四例 `work/native-homes/**/*.jsonl` 的 8、8、2、13 个文件，解析 assistant 的 subagent toolCall 参数（直接 `agent: vision` 或 workflowScript 内指定 vision），并核对实际 assistant `provider`/`model`。DeepSeek Sheet 的 transcript 与 child session 保存了同一两次响应，不能加总成四次调用：两份记录中 message.timestamp 分别为 `1790564767950`、`1790564774526`；以下以 child `session.jsonl` 为主。其它 subagent status/wait/list 不计作 vision 委派，配置文件声明 vision 也不算使用证据。

## 唯一一次 vision 委派的链路

父 Braid 工作项为 **Issue #5「单元格编辑、范围操作与撤销重做 (REQ-3-*)」**，负责人 `deepseek-5`，原生父会话 `01a0e5f8-94d0-72dc-b764-f0d1b81360e7`，实际父模型为 `deepseek-v4-flash`。该 Issue 已于 03:03 左右拆出，调用时尚在等待共享基础 Issue #2。

| UTC 时间 | 直接观察 |
| --- | --- |
| 03:05:29–03:05:59 | 父会话尝试 read `copy-paste-range.png`。工具明确返回当前模型不支持图片，图像将从请求中省略。 |
| 03:06:01 | 父会话查询原生 subagent 列表，获得 vision 角色。 |
| 03:06:04.365 | 父会话发出异步 workflowScript，`runs.all` 中只有一个 `agent: "vision"`。toolCall ID 为 `call_00_KfUpmm4ygC3GSSCNlvCD0909`。 |
| 03:06:06.140 | child session 创建，ID `01a0e5fa-11ba-76b0-8e0a-f27a21f75b69`；subagent run ID `9af6153d-e030-4eca-8237-ca26493a4e1e`。 |
| 03:06:07.833 | child model_change 实际选择 `factory26-visual / deepseek-v4-flash-vision-exp`，thinking 为 high。 |
| 03:06:08.991 | 第一条 assistant 响应发出 3 个 read 调用，分别读取所给参考图。 |
| 03:06:14.430–.516 | 3 个 toolResult 均含 `image/png` 图像内容；总览图返回原图 3840×1924、显示 2000×1002。 |
| 03:07:05.829 | 第二条 assistant 响应返回「参考图视觉事实报告」，stopReason=stop；原生 status 后续显示 completed、exit 0。 |
| 03:07:47.770 | 父会话查询该 run status，看到完成状态与报告路径。 |
| 03:07:49.709–.872 | 父会话显式 read `subagent-artifacts/9af6153d-…_vision_0_output.md`，收到包含跨图汇总和疑点的报告正文。 |

委派只要求读取 `copy-paste-range.png`、`worksheet-overview.png`、`basic-formulas.png`，逐项描述文字标签、工具栏、公式栏、网格表头、矩形选区、上下文菜单、编辑态与 Sheet 标签栏；明确要求不可见处不要猜测，不操作浏览器。三张图片均来自该次任务的 `input/reference/`。

视觉返回覆盖 Google Sheets 风格界面结构、公式栏和底部标签；指出复制源 `A3:C5` 的蓝色虚线、目标选区 `E3:G5` 的浅蓝填充与活动格白底深蓝边框，以及编辑态函数下拉。它也明确说明三图没有可见右键菜单、不能确认精确色值/像素，参考图 UI 主要是中文。这些是 **child 的观察报告内容**，本次调查没有独立审图证明其每项视觉判断正确。

## 是否用于需求或设计

可以确认这是局部需求与 UI 分析：父会话先读取 REQ-3 文本，因自身不能读取图像而委派 vision，并在 03:07:49 实际取回报告。父会话随后明确区分“参考图是中文”与“需求要求英文可访问名称”，选择以需求文本确定名称。这说明视觉结果进入了其判断上下文。

但不能把它说成已依据视觉结果重做需求或技术设计：Issue #5 的技术与验收方案 comment #9 在 **03:06:36.389** 已发布，早于 vision 的 **03:07:05.829** 最终报告。该方案开头明确依据 `requirements.yaml` 的 REQ-3 descriptions。后续已读取的 Issue #5 评论讨论校验规则、文案、公式契约，没有明确引用视觉报告或据此修订方案；父会话后续工作主要是编辑/选区/历史纯逻辑与检查脚本。到本截面，尚未建立某项截图观察 → 方案修改 → 实现界面 → 浏览器验证的证据链。

因此准确表述是：**局部任务整理实现所需 UI 信息时用过 DS vision，报告已被父会话读取；没有证据证明根级需求拆分使用过 vision，也不能声称视觉建议已落地或通过验收。**

## 可复查路径

WSL 共同根为 `/home/yyh/Development/factory26/runs/`。四例外层路径如下，之后均接 `workspace/official-generation/template/.factory26/<上表内层 run ID>/`：

- `e20260928-01-flash-team/attempt-02/generation/runs/pi-braid-flash-team--hackathon--github-356dab3a5fe6a6/`
- `e20260928-01-flash-team/attempt-02/generation/runs/pi-braid-flash-team--hackathon--sheet-739b90d54f05db/`
- `e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--github-87616ca3ee80f1/`
- `e20260928-02-deepseek-direct/attempt-02/generation/runs/pi-braid--hackathon--sheet-6533a6edafdd94/`

DeepSeek Sheet 的具体材料都位于该内层根，令 `H=work/native-homes/pi-deepseek-fast-01a0e5f8-89f5-7b72-be0f-86f933413e0a`：

- 父会话前半段：`H/sessions/--workspace-template-.factory26-20260928-025746-66feadac-braid-state-worktrees-issue-5-pi-deepseek-fast-g1--/2026-09-28T03-04-28-625Z_01a0e5f8-94d0-72dc-b764-f0d1b81360e7.jsonl`，第 29–35 行记录读图失败、列表与委派。
- 父会话后半段：`H/2026-09-28T03-04-28-625Z_01a0e5f8-94d0-72dc-b764-f0d1b81360e7.jsonl`，第 5–7 行为方案发布，第 22–27 行为 status 与读取报告。拆分存放的原生记录不能只读其中一份。
- 子会话：`H/2026-09-28T03-04-28-625Z_01a0e5f8-94d0-72dc-b764-f0d1b81360e7/9af6153d-e030-4eca-8237-ca26493a4e1e/run-0/session.jsonl`，第 1–4 行为身份和实际模型，第 5–10 行为任务、读图与两次响应。
- 返回报告：`H/subagent-artifacts/9af6153d-e030-4eca-8237-ca26493a4e1e_vision_0_output.md`；对应 `_transcript.jsonl` 是重复证据，不另计模型响应。
- `braid-state/braid.sqlite3` 以只读连接查询 `local_items` 的 `issue:5`、`local_comments` 的 comment #9，交叉验证工作项归属、方案正文和发布时间。

这是运行中的有界观察，不排除 DeepSeek 后续新增 vision 调用；Flash 结论对应已取消后保留的现场。没有读取凭据、输出图像 base64、修改运行输入或调用外部 benchmark。
