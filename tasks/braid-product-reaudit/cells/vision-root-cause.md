# 参考图与 vision 使用断点

2026-09-28 05:08 UTC 的只读截面。分析对象为 WSL `e20260928-02-deepseek-direct/attempt-06` 下继续运行的 Sheet/GitHub 两个 case；原生日志随运行增长，下面的计数只对应此截面。没有操作运行、调用模型或读取凭据。此前 attempt02 的调用事实见 [vision-requirements-evidence.md](../vision-requirements-evidence.md)。

## 判断

**“DeepSeek vision 只调用一次”的核心问题是视觉解读没有交给专门角色，不是接线或模型调用失败。** `pi-braid` 的根与若干成员使用 `glm-5.3-flash`，本次注入的 `models.json` 声明其接受 `image`；Sheet 根、共享基础和行列负责人直接用原生 `read` 读取参考图并自行解读。原生 `toolResult` 含 `image/png` 图像块，后续回答描述了图中的云盘主页、Google Sheets 风格编辑器和中文界面。这支持“原生会话有图像输入并作出相关判断”，但日志不能独立证明网关实际传入了每个像素，也不能证明所有视觉判断正确。即使 GLM 能看图，也没有履行所需的 vision sub-agent 职责分工。

真正的断点有三处。第一，根任务只要求“阅读参考图片”，没有说明视觉解读归 vision：GLM 主会话因此直接读图；GitHub 根会话更将列出 27 个文件名当成已通读图片，未观察到该根会话对任一图片 `read`。第二，`deepseek-v4-flash` 配置为只接受 `text`；`read` 对 PNG 明确提示 `Current model does not support images. The image will be omitted from this request.`。部分成员把这视为材料不可用，直接依据详细文字需求继续，而没有走已存在的 vision 角色。唯一一次 vision 委派恰由读图失败触发，说明成员把它视为能力补救，而非图像职责。第三，子 Issue 基本没有把关联截图作为具体材料入口传递：Sheet #2 明列了 `workbook-home.png`、`create-workbook.png`、`worksheet-overview.png`，其余子 Issue 无具体图片路径；GitHub #2 只有 `input/reference/` 目录入口，其余子 Issue 无具体路径。虽然成员仍能从 `requirements.yaml` 的 `![image](reference/...)` 自行发现图片，责任没有落实到相关工作项。

需要修正的是**需求参考图的视觉解读交给 vision，主会话提供关联路径与问题，读取带来源的报告后形成方案**。可按任务批量委派并复用已有有效观察，不须每张图各建一次会话。主模型是否支持图片不改变分工；文件存在、目录列表或读图工具返回都不能冒充 vision 观察。

## 运行证据

本次生成提示在 `variants/pi-braid/run.py` 的 `prompt` 里已写“阅读 requirements.md、requirements.yaml 和参考图片”，而实际输入里没有 `requirements.md`，有 `requirements.yaml`、空的 `prerequisites.md` 与 `reference/`。Sheet 有 9 张 PNG、GitHub 有 27 张。两个 `requirements.yaml` 各含 `![image](reference/...)` 引用（Sheet 10 处、GitHub 27 处），所以不是图片未进入需求包或完全没有路径索引。注入后的两个 profile 均有原生 `vision.md`，模型指向 `factory26-visual/deepseek-v4-flash-vision-exp`，声明 `input: [text, image]`；DeepSeek 主模型只声明 `input: [text]`。`run.py:native_files` 拷贝角色并装载 `pi-subagents`；Sheet #5 的 `subagent({action: "list"})` 实际列出了 `vision`，随后的委派返回成功报告。现有证据不支持角色未注册、视觉模型不可用、图片路径失效或配额硬限制这些解释。

| 环节 | Sheet | GitHub |
| --- | --- | --- |
| 文件发现 | 根会话 `ls reference/`，9 张均存在 | 根会话 `ls reference/`，27 张均存在 |
| 原生读图 | 截面共 12 次对输入参考图的 `read`，涉及 7 个不同文件；其中 GLM 成功读取 6 个不同文件并收到图像块 | 根会话无图片 `read`；05:07 新恢复的 #5 DeepSeek 成员尝试读 2 张 |
| 文本模型失败 | #5、#7、接手 #2 的 DeepSeek 分别读图后收到不支持图片提示 | #5 读 `github-create-repository.png` 和 `github-fork-repository.png` 均收到不支持图片提示 |
| vision | #5 在失败后列出原生角色，委派 vision 读 3 张图并取回报告；这是唯一已见 vision 会话 | 截面尚无 vision 委派 |
| 结果消费 | #5 已读回报告，但其方案评论早于报告完成；没有证据证明方案根据报告修订。#7 与接手 #2 没有委派 | #5 下一轮明确说不能读图，将依据文字描述继续；根分析称已通读 27 张，工具记录只支持列名 |

Sheet 6 张有 GLM 直接读图证据：`workbook-home.png`、`worksheet-overview.png`、`sort-range.png`、`worksheet-lifecycle.png`、`create-workbook.png`、`manage-rows.png`。vision 的 3 张为 `copy-paste-range.png`、`worksheet-overview.png`、`basic-formulas.png`；与 GLM 重叠 `worksheet-overview.png`。合并看，9 张中只有 `manage-columns.png` 在截面尚未见成功读图，但**直接读图的覆盖不算 vision 分工已落实**。#7 的 `sort-range.png` 虽在其 DeepSeek 会话失败，根 GLM 曾直接读过；仍没有向 #7 交接可消费的视觉结论。接手 #2 的 DeepSeek 再读 `worksheet-overview.png` 失败后转而猜测网格规模，同样说明缺少 vision 报告或明确交接。

GitHub 根会话 03:05:20–03:05:40 列图并阅读大段 YAML，后续根分析称“已通读 27 张参考截图”；该会话没有图片 `read` 或 vision 委派。这是**已发现路径被误写成已审图**的直接例子。05:07:30 新恢复的 #5 成员又暴露第二种断点：主动 `read` 两张图片，工具在 05:07:31 告知图像会被省略，05:07:32 它决定仅依赖文字需求。相同失败在 Sheet #5 导向成功委派，在 Sheet #7 和 GitHub #5 则没有；这是模型决策与指令/交接约束不足，而非统一的调用限制。

## 最小通用修复与核实

在现有需求处理说明中补上一个短规则即可，无须硬编码“每图一次 vision”或新增编排层：**划分/负责 UI 需求时，把相关 `reference/` 路径交给负责人；形成方案前，由主会话将相关图、需求背景和具体问题一并委派原生 vision，读取其带来源的报告再形成判断。主模型能直接看图也遵守这项职责分工。记录哪些图实际由 vision 查看、哪些仅列出/无法看，以及可见事实与文字需求的差异；不要声称仅列名的图已读。** 根负责人可只分配关联路径，避免自己先读完 27 张；子任务按所负责需求判断哪些图影响决策。视觉模型返回的事实仍须与文字需求核对，不能从截图推断不可见交互。

核实应在下一次**已获授权**的生成中读原生记录，而非新增 Factory 测试：抽查一项由 GLM 承担的有图 UI 需求和一项由 DeepSeek 承担的有图 UI 需求。检查 YAML 引用与 Issue 材料入口、原生 vision 委派是否包含关联路径和问题、child 是否实际获得图像块、主会话是否读取带来源的报告，以及方案/实现记录是否引用具体可见事实。若仍由 GLM 主会话直接读图代替 vision，或 DeepSeek 失败后直接写“无法看图/仅靠文本”，说明分工尚未落实；若只出现大量 vision 调用而没有结果消费，也未解决问题。当前 run 仍在进行，后续追加行为须重新取截面，不把本次计数当终态。

## 可复查定位

WSL 根：`/home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct/attempt-06/generation/runs/`。两个 case 的内层 `.factory26` ID 分别为 Sheet `20260928-025746-66feadac`、GitHub `20260928-030347-78b10c07`。以下均相对各自内层根：

- Sheet 根 GLM：`work/native-homes/pi-glm-fast-01a0e5f3-3b57-7d32-b2f7-3014d624bad1/2026-09-28T02-58-55-469Z_01a0e5f3-7f6c-7001-b229-04dc2a2d2d57.jsonl` 第 29–35 行，`read`、图像块与后续视觉描述。
- Sheet #2 GLM：`work/native-homes/pi-glm-fast-01a0e5f7-39bb-7712-8f13-351fa805a7ce/2026-09-28T03-03-12-551Z_01a0e5f7-6ba7-739e-aaf3-3e8d230c17ef.jsonl` 第 13–22 行；Sheet #4 GLM 为 `pi-glm-fast-01a0e5f7-d021-75f1-9882-171dca66a678` 会话第 27–30 行。
- Sheet #5 DeepSeek 的拆分早期会话：`work/native-homes/pi-deepseek-fast-01a0e5f8-89f5-7b72-be0f-86f933413e0a/sessions/--workspace-template-.factory26-20260928-025746-66feadac-braid-state-worktrees-issue-5-pi-deepseek-fast-g1--/2026-09-28T03-04-28-625Z_01a0e5f8-94d0-72dc-b764-f0d1b81360e7.jsonl` 第 28–34 行；同 home 顶层同名会话第 19–26 行为报告取回。Sheet #7 同样位于 `work/native-homes/pi-deepseek-fast-01a0e5f8-ff9f-72b0-83ef-79822e63d630/sessions/`，早期会话第 70–72 行；接手 #2 位于 `work/native-homes/pi-deepseek-fast-01a0e611-0688-7632-b098-a2f2eaf26a96/`，会话第 100–102 行。
- GitHub 根 GLM：`work/native-homes/pi-glm-fast-01a0e5f8-df4b-7c72-8a7a-d109d950bc43/2026-09-28T03-05-01-537Z_01a0e5f9-1560-710f-8acf-11f497871768.jsonl` 第 7–13 行列图与需求分析，第 36、60 行写出截图已读主张。GitHub #5 DeepSeek：`work/native-homes/pi-deepseek-fast-01a0e668-ddc4-7653-a592-a93660c1ceda/2026-09-28T05-07-08-406Z_01a0e668-e1f6-7594-8f9b-5a9afc8b1ed0.jsonl` 第 34–37 行。
- 角色与模型接线：各 case `work/capabilities/pi-{glm,deepseek}-fast/native-template/{agents/vision.md,models.json}`；输入图和 YAML 位于 `input/`；Issue 路径传递可用 `braid-state/braid.sqlite3` 的 `local_items.body` 只读核对。
