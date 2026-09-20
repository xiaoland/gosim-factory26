# 原始 Pi / Keep 首次完整基线

2026-09-20 使用比赛网关完成一次独立生成与官方评测：**6/32 通过，26 项失败，通过率 18.75%**。没有 skipped、flaky 或全局错误。评测器退出码为 1，表示测试失败；安装、构建、服务启动和完整评测流程均已完成。

这是本地 Keep 单任务结果，不是完整 ARC-bench 六任务或线上 Lite 66 项总分。尚未验证线上提交及平台沙箱，运行记录保持 `submission_eligible=false`。

| 条件 | 实际值 |
| --- | --- |
| Run | `20260920-114308-afd49b8a` |
| 评测 | `20260920-115409-05e678` |
| Agent | 原始 Pi `0.85.1`，单会话，关闭个人扩展、技能和上下文文件 |
| 模型 | `deepseek-v4-flash-vision-exp`，thinking `high` |
| 网关 | `https://api.arc-bench.com/v1`，使用比赛提供的 key |
| ARC-bench | `1eb018367bedd618d3b9ced406ce07fb423d4956`，未经修改 |
| svc main | `4fe4c66ac4deb35209069c00b1bbdc1b22aae3af`，项目本地包版本 `15.0.0` |
| 环境 | macOS 15.4.1 arm64、Node 26.3.0、Python 3.12.10 |
| 生成耗时 | 660.526 秒，约 11 分钟 |
| 评测耗时 | Playwright 1393.982 秒；含安装、构建与启动共 1396.459 秒 |
| 模型响应 / 工具调用 | 48 / 63 |
| 累计输入 token（不含缓存命中） | 33,109 |
| 累计缓存读取 token | 3,752,320 |
| 累计输出 token | 89,864，其中 reasoning 为 53,614 |
| 累计 total token | 3,875,293；包含各次请求重复读取的上下文 |
| 实际费用 | 未知；Pi 客户端价格估算不作为比赛账单 |

生成进程正常退出，最后一条模型响应的 `stopReason=stop`。应用在评测前冻结，评测后文件哈希与冻结时一致。外部评测结果没有回传给 Pi，生成应用也没有按这些结果修改。仓库尚无提交，生成器与评测器各自的源码快照保存在 run 中。

本次生成启动时旧配置仍含 1800 秒总时限，但在 660.526 秒正常结束，没有触发该限制。之后的评测使用更新后的脚本，不设流程总时限。当前 `make run` 已移除额外的输出 token 上限及生成、安装、构建、评测总时限，采用 Pi 内置模型参数；官方的单项测试 60 秒、断言 10 秒、1 worker、0 retry 保持不变。历史配置与源码快照按实际运行条件保留。

通过的用例为 REQ-1.1 首页、REQ-2.1 笔记列表、REQ-2.4 编辑笔记、REQ-2.7.3 默认标签、REQ-3.2 关键词搜索、REQ-6.1 侧栏项目与样式。

失败中可以直接确认的共同原因：

- 创建入口是只读 `input`，评测器寻找名为 `Take a note` 的 `button`，相关创建流程无法开始。
- 笔记卡片是普通 `div`。官方 helper 优先寻找 `article`，回退时仅定位到标题文本，随后无法在其中找到删除、归档、颜色、标签或置顶按钮。
- 编辑标签、搜索建议及设置菜单还存在控件角色或名称不匹配；布局和侧栏测试检查的 `aria-pressed` / `aria-expanded` 状态也有缺失。

这些定位和可访问性契约差异足以解释多项失败；不能仅凭未能执行到后续断言，就认定对应业务功能全部缺失。完整错误、页面快照、截图、视频和 trace 保留在官方报告中。

svc 已完成 Pi 原生会话导出、overview、模型 profile、match、trace 和原生材料 read。导出包含 313 个 trajectory 事件；usage 与直接汇总原生 Pi 会话一致。通过 `read` 读回的 3,099,284 字节与原会话逐字节相同。`overview.status=partial` 的已知原因是标准 Pi session 不声明执行终态；运行器记录的退出码和最终 `stopReason` 补充这部分证据，内容和工具关联覆盖均为 complete。

固定版本需求包的 YAML 在 REQ-3.2 有缩进错误，且缺少 `search_keyword.png`、`label_filtered_list.png` 两张引用图片；按可读 Markdown 和现有图片输入生成，上游文件保持原样。

本次证据入口：

- [生成元数据与 usage](../runs/20260920-114308-afd49b8a/run.json)、[评测汇总](../runs/20260920-114308-afd49b8a/evaluation/20260920-115409-05e678/summary.json)
- [官方 JSON](../runs/20260920-114308-afd49b8a/evaluation/20260920-115409-05e678/results.json)、[官方 HTML](../runs/20260920-114308-afd49b8a/evaluation/20260920-115409-05e678/html/index.html)
- [Pi 原生会话](../runs/20260920-114308-afd49b8a/pi-session.jsonl)、[冻结应用入口](../runs/20260920-114308-afd49b8a/application/package.json)
- [svc evidence-v4](../runs/20260920-114308-afd49b8a/analysis/evidence-v4.zip)、[overview](../runs/20260920-114308-afd49b8a/analysis/overview.json)、[模型 profile](../runs/20260920-114308-afd49b8a/analysis/profile.json)、[原始材料读回验证](../runs/20260920-114308-afd49b8a/analysis/read-verification.json)

这些原始产物在本机 `runs/` 下，被 Git 忽略；本报告可随源码保存。项目的 3 项边界检查已通过，官方 benchmark 静态审计也已通过。复现入口与密钥配置见 [README](../README.md)。

初次评测的 `--reporter` 参数覆盖了配置中的 HTML 输出选项，导致 HTML 写入 benchmark 默认目录。已核对其内嵌时间、全部 32 项结果及耗时与 JSON 一致，再将原报告完整归档到上述路径，过程记录在 `html-recovery.json`。当前脚本改用 Playwright 原生 HTML 环境变量，并通过一次独立的报告路径检查；无需重跑本次评测。

此前 ChatGPT/Codex 探测在切换比赛模型时中止评测，不计入基线。另一次 Pi 探测因人为设置的 16K 输出上限而以 `stopReason=length` 结束，也不计入基线。
