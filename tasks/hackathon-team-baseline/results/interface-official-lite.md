# 入口修正版：官方 API 的本地 Lite 结果

2026-09-25 使用当前 `pi-team-mixed` ZIP、比赛 API、WSL 官方本地 Runner，对 Keep 与 BookStack 各运行一次。两题均生成成功，冻结源码与评分源码哈希一致，评分阶段完成。本地 Runner 的 `score` 为 `null`；下表是官方测试的通过比例，不是官网排行榜分数。

| 任务 | 本轮 | 旧版 | 差异 | 本轮耗时 | 旧版耗时 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Keep | 23/32（71.9%） | 27/32（84.4%） | -4 项 | 36.4 分钟 | 61.4 分钟 |
| BookStack | 26/34（76.5%） | 27/34（79.4%） | -1 项 | 99.2 分钟 | 110.7 分钟 |
| 合计 | 49/66（74.2%） | 54/66（81.8%） | -5 项 | 两题并发 | 两题并发 |

本轮与旧版的 Runner、adapter、需求、测试和 noop 输入哈希分别相同；Agent ZIP 不同。两轮使用同一份比赛 API 环境文件。两次生成的随机性与 ZIP 内多个入口变化共同影响结果，因此不能将五项差异归因于单一提示词修正。

Keep 的旧五项失败全部保留：标签入口三项及置顶 DOM 两项。本轮新增 REQ-2.3.1/2/3：应用暴露 `menuitem "Delete Note"`，测试等待 `button`；新增 REQ-4.2：`Settings` 菜单项点击被 click-away 层截获。旧版 PR 曾记录将 Delete Note 改为普通按钮，本轮只经根 Issue 实施，最终 DOM 再次使用 menuitem。这说明先前的局部修正未自然保留，不能单凭这一轮确定是提示词变动导致。标签三项本轮在菜单入口处失败，旧版已打开入口后在复选框查找失败；并未改善。

BookStack 仍失败的旧项为 REQ-6.1.1、6.1.2、6.1.3、6.3.1、8.1；旧的 REQ-8.2、9.1 通过了，新失败为 REQ-5.2.2、6.3.2、7.2。八项在 Playwright 中均是等待目标 UI 元素的 10 秒 timeout；需要按生成页面与测试快照分别判断，不能把每项直接等同于产品功能缺失。

两题都实际使用根 Issue，并由根 Issue Agent 直接实现、关闭；均未创建 PR、子 Issue 或调用原生 sub-agent。Keep 无评论，BookStack 有一条评论。BookStack 读取了 SVC skill，留下 `application/NOTES.md`，未形成 task packet；Keep 也未观察到 packet。两题均有生成期自检和调整，BookStack 的自检在 fresh DB 上显示 49 pass，但官方仍有 8 项失败。自检证明有反馈循环，未证明反馈覆盖了所有官方接口契约。

原始证据在 WSL `/home/yyh/Development/factory26/runs/hackathon-team-baseline/20260925-interface-official-api/lite-runs/`，本轮 run ID 为 `pi-team-mixed-arc-bench-lite-keep-be4dde8d43`、`pi-team-mixed-arc-bench-lite-bookstack-743b6187f7`；各自的 `run.json`、`workspace/official-evaluation/template/.arc/playwright-report.json`、生成期 `.factory26` 保存评分与原生轨迹。旧 run 分别为 `54196efa62`、`ba27587982`，位于同级 `20260925/lite-runs/`。

当前判断：入口修正没有在这两题上转化为更高通过数，也没有观察到 Braid/原生多 Agent 协作。最值得下轮调查的是为什么两个有规模的任务都直接在根 Issue 实施，以及生成期自检为什么未覆盖用户可见的菜单角色与点击行为；需要基于原生会话再分辨 Agent 判断、Braid 可用性和技能入口各自的作用，避免直接强制拆 Issue/PR 或对隐藏测试做定向适配。

后续核实补充：当前运行归档的稳定指令没有产品设计→技术设计→实施计划→实现→验收的明确顺序，也没有要求实现在 PR 中完成；只介绍对象操作与 SVC 按需导航。因此“无 PR”不能用来证明 Agent 忽略了明确给出的工作流程。这个缺口已纳入 [下一轮方案](../../issue-decomposition/design.md)，尚未修改源码。
