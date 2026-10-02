# I13：工具接线与提示词分层方案

2026-09-30起草，2026-10-01完成审计复核后获准实施。用户最新原话：“我已经配置好了 .env.i13key。我复核了这份 tools-prompts-audit.md，没问题。你可以开工工具接线和Factory/Braid 提示词了。然后我们来讨论Braid 协作方法与 Requirements 树。”两条实现线据此明确授权，均由GPT-6.1-Sol / extra-high独立推进；主线现在恢复下一组方案讨论。此前提前开工及用户要求先补审计的纠正记录保留在packet，不再作为当前待授权状态。

## 工具接线

Context7/Exa按角色需要选择扩展入口；用户明确并非所有sub-agent都需要这两项。按已复核审计中的分配给主Agent、explorer、executor默认加载，advisor、vision、browser-operator不默认加载。fff作为本地代码搜索能力覆盖主/子会话，使用当前任务的实际cwd。沿用Pi原生扩展加载与现有runtime构建，不另建工具代理或插件管理框架。

| 工具 | 建议实现与可观察结果 |
| --- | --- |
| Context7 | 锁定官方 `@upstash/context7-pi 0.1.2`，显式加载原生扩展，提供 `resolve-library-id`、`query-docs`。它读取 `CONTEXT7_API_KEY`，直接访问官方API，无需mcporter。包内技能仍以独立文件发现和按需读取，prompt模板不自动加载。 |
| Context7必要修正 | 官方工具文案带“每问题最多3次”及强制重新resolve的条件；集中ID前提、删除次数约束及固定选择/回答流程，已取得的有效library ID可以直接沿用。现有错误解析可能丢HTTP状态和原响应，窄补丁保留具体状态及可诊断响应；不重写整套客户端。 |
| Exa | 一份薄Pi扩展注册 `exa_search` 和 `exa_contents`，直接调用官方search/contents，读取 `EXA_API_KEY`。保留必要的查询、域名/日期筛选、结果数量、来源及正文选项；长结果明确截断和原文入口，错误保留HTTP状态、request ID及响应内容。当前需要是检索与取得正文，不宣称覆盖Exa全部产品接口。 |
| pi-fff | 锁定官方 `@ff-labs/pi-fff 0.11.0`，使用 `tools-only`，默认提供 `fffind`、`ffgrep`，保留原生find/grep。补审确认 `fff-multi-grep` 需显式 `PI_FFF_MULTIGREP=1`；本组先不额外开启。整理包内description/schema/guidelines的重复，并删除固定检索次数和强制工具优先级流程。Linux构建收录对应原生依赖，主/子会话均可加载；每个工作区按插件既有生命周期索引。 |
| mcporter | I13配置中只移除迁出的Context7与Exa，保留Handsontable等仍有消费者的服务和共用依赖。更新真实工具说明及开发导航。 |

Exa现成候选已作取舍：`pi-exa-search 0.1.3`只有检索而无全文，peer仍指向旧Pi scope；`@coctostan/pi-exa-gh-web-tools`包含额外的仓库克隆、结果存储和可选模型提取。本批两个HTTP操作采用直接adapter，避免为这部分需要引入更宽的行为；使用Node原生fetch与Pi既有工具schema，不建SDK层、MCP桥或自动研究流程。

打包时从用户本地凭据来源取得两个key，写入该次非Git制品的私有配置，运行时注入对应环境变量；显式运行环境可以覆盖包内值。主/子进程沿用同一凭据环境，提示词、工具参数、日志及共享源码仅出现变量名或配置入口。此前创建了仓库根 `.env.i13-tools`，既有 `.env.*` 忽略规则已覆盖。用户最新告知已填好 `.env.i13key`；只读核对发现该文件名不存在，实际 `.env.i13-tools` 中的 `CONTEXT7_API_KEY`、`EXA_API_KEY` 均已非空，已向用户说明并采用现有文件，不复制、改名或读取其他个人配置。服务鉴权仍须通过实际调用确认。

原生加载的必要落点是 `run.py::native_files`：主Pi显式关闭自动扩展发现后加载指定扩展；child角色目前只被写入background-bash路径。安装npm包、或只改父launcher都不足以完成这组要求。沿用现有角色配置，按已选角色分配写入对应扩展入口；不恢复父profile或技能正文注入。

## 扩大的提示词审计范围

当前已证路径、重复归属、已改/拟改及未验项见[审计结果](tools-prompts-audit.md)。其中pi-fff默认工具数与其metadata自动进入system的事实是本轮补审更正，不沿用旧“插件不注入提示”的简化结论。

用户要求本组核心目标覆盖各Agent实际上下文内的提示词去重，并在最新阶段纠正中要求先补审计结果、已启动工作继续。审计单位是一次模型实际消费的组合输入，不仅比较两个源码文件。主Issue、主PR以及五种child分别核对；两个profile和前台/后台、接续路径中确实改变输入来源的差异一并覆盖。

沿调用链检查Pi基础system、工具description/promptSnippet/promptGuidelines、扩展自动注入、Braid身份/角色/通用指引、Factory profile/运行条件、角色body及目录description、技能发现信息、项目指引和任务/接续消息内的稳定指令。普通任务事实、必要身份参数及不同Agent各自需要的同一条规则分别判断，不能通过全局字符串去重误删含义。

同一稳定指令在同一次Agent输入中保留一个明确来源；重复说明在生产者处删除或收敛。需要重复存在于不同Agent上下文的规则可以保留在对应来源。保持必要义务及实际操作语义，技能正文仍独立，不用重新内联方法来替代被删提示。优先整理已有材料或修正已证重复注入，不为这项工作引入自动语义去重器、通用提示词框架或新运行政策。

每项实际修正记录重复来源、受影响消费者、保留位置及组合输入依据。通过现有真实材料生成和原生组装入口核对，不将源码搜索没有匹配当作全部运行上下文没有重复的证明；未运行模型的边界明确保留。

## 提示词分层

当前实际组合是Pi基础system → Braid角色/通用协议 → Factory profile → RUN_CONDITIONS及后台任务说明。后面三者有重复；尤其profile重复Braid的角色分工、指派/交接和讨论操作，另含比新角色description更窄的explorer/executor说明，以及会削弱文档/packet义务的“技能提供可选方法”。

| 层 | 保留的职责 | 本批整理 |
| --- | --- | --- |
| Pi基础system与工具自身说明 | 基础工具用法、原生运行能力 | 复用原生说明；Factory不再重复基础调用教程。Context7的必要窄修正属于工具组。 |
| Braid system prompt | 当前成员与Issue/PR身份、通用职责、独立clone/origin、指派与发布语义，以及关键CLI差异 | 用短段落区分身份、工作职责、协作资料与操作；合并重复叙述，普通参数查既有help。保留指派启动独立成员、已发布head与本地在途工作不同、正文edit为全量替换、root resolve/单条hide、订阅/通知及Closes的实际语义。 |
| Factory profile | 本配方的develop→main交付路线、既定advisor/vision政策、知识与任务状态义务、增量处理及结果要求 | 删除已由Braid提供的重复协议及explorer/executor等角色目录说明；统一技能入口表述，现有协作决定保持原义，不借此重写下一批方法。 |
| Factory运行条件 | 交付环境、已选开发工具、数据/服务生命周期与实验边界 | 按交付条件、开发工具与反馈、数据/服务状态三部分整理，合并重复命令说明和示例。Node版本、frontend/backend交付路径、平台启动方式、保留端口/目录、pnpm/portless/Playwright/UnoCSS等既定要求保持原义。 |
| 独立技能与下一批协作材料 | 方法、理由、成立条件和细节 | 仅提供发现/读取入口，正文不进入system/profile/role/task prompt。下一批再讨论Braid协作方法和需求树。 |

文档与task-packet入口建议改成清晰义务：

> 非简单工作开始或接续时，读取适用的svc-documentation与svc-task-packet技能，建立或接续项目知识入口和当前任务包，随决定、依据及下一步变化维护。复用已有文档与packet，关联PR接续对应任务资料；一次会话已读取的方法按需回看。

这段明确的是机制与首次读取入口，不复制技能方法，也不要求每个child另建项目文档或任务包。child继续依据自身角色、任务和独立技能入口工作，已有的父profile隔离保持；需要接续的当前材料作为任务背景传递。

advisor保留当前已选的重要判断前咨询政策，表达为事先选定的使用时机；删去重复介绍，不将其简写成“可以忽略一切成本”。vision的既定图片分工保留。本批既不降低交付/证据要求，也不新增逐步执行SOP、固定汇报栏目或其它委派条件。

## 委派和实际反馈

两条实现线分别拥有工具/构建接线和提示词内容。工具线主要涉及npm锁定、必要依赖补丁、I13扩展、build/run的加载与凭据物化、mcporter配置及工具导航；提示词线涉及Braid `group/provider.rs`及受影响产品说明、两份I13 profile和run.py中的运行条件常量。两者在run.py分别改加载函数/环境接线与提示词常量，明确小范围所有权即可，不要求父方设计逐文件执行步骤。独立仓库各自提交，共享Factory index提交时串行。

反馈采用编译、真实材料生成和工具实际操作，核对父/子实际加载入口、独立技能材料、打包后凭据读取及平台原生依赖；对Context7/Exa使用公开文档问题取得实际服务结果，保留具体错误和来源。提示词逐项核对原义务仍有唯一归属，检查实际Issue/PR最终组合材料，不用字符数当作充分性证明。不添加或运行Factory/Braid/SVC测试、smoke、模拟任务或探针；模型运行和I13实验继续独立授权，I12冻结材料保持原状。

## 来源与核对入口

- 当前实现：`variants/pi-braid-i13/run.py`、两份`agents/*/instructions.md`、`harness/npm/package-lock.json`、`scripts/runtime.py`、`submission/Dockerfile`及`sources/braid/src/group/provider.rs`。
- [Context7官方Pi说明](https://context7.com/docs/clients/pi)与[官方API指南](https://context7.com/docs/api-guide)。npm发布包已下载到 `runs/iteration13/tools-prompts-plan-20260930/context7/`，仅供源码阅读，未安装。
- [FFF官方Pi包](https://github.com/dmtrKovalenko/fff/tree/main/packages/pi-fff)。0.11.0发布包同样只保留供阅读；主/子加载和Linux平台兼容尚待实施反馈。
- [Exa search](https://exa.ai/docs/reference/search)、[contents](https://exa.ai/docs/reference/get-contents)，以及两个候选扩展的上游README。原始材料归 `runs/iteration13/tools-prompts-plan-20260930/`。
- 本轮独立advisor支持上述职责和实现选择；这属于静态方案判断，不代表已取得真实工具加载或模型使用效果。
