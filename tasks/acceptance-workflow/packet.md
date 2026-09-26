# 补齐一般工作流程与独立 reviewer 对照

状态：用户已批准开工、自由提交并启动本地实验。授权原话：“好的，开工，并且你可以自由提交和启动实验”。用户随即纠正设计验收方案应作为既有一般工作流程的一步；该修正已纳入 [设计](design.md)，实施仍按已批准的两个运行 variant、本地 Hackathon 两题范围推进。K3 根 Agent 的已冻结官网对照独立运行，不混入本轮改动。

## 问题

官方 GitHub run `b77e4357a4e1` 得到 4/100。根 Agent 在最终提交上验证了 API，却没有验证最终应用中的用户操作；局部 PR 的浏览器结果被当成整体交付依据。现有工具可用，GLM 在精简证据上也能指出缺口。不能从单次运行断言唯一根因，但当前参赛指引确实漏列了用户早已确定的一般工作流程中的“设计最终验收方案”阶段。

本轮先修复这项流程不一致，再比较独立 reviewer 是否提供额外收益。Braid 只承载 Issue/PR 协作，不判断完成或选择测试手段。

## 决定与边界

用户提出“完善一般性工作流程：设计验收方案；独立reviewer可以作为另一个variant进行尝试”，并指定下一次实验先本地跑 Hackathon，使用已经准备的模拟测试。随后明确纠正：验收方案本来就是既定一般工作流程缺失的一步，[产品说明](../../docs/prd/index.md)与开发侧 [AGENTS.md](../../AGENTS.md)已有对应边界；它不应被包装成新增的专门机制或单独的实验开关。当前 [修正后的设计与验收](design.md) 供复核，开工影响与授权尚待明确记录。

已经存在的 `svc-verification` 技能描述了实现前的检查设计和执行后的证据解释。本轮先复用它，不改 SVC Corpus，不让 Factory 指令写入 GitHub、Sheet、Web、浏览器等特定赛题的验收规则，也不要求 reviewer 只读代码。

## 方案与实验入口

见 [设计与验收](design.md)。直接补齐活动 `pi-team-mixed` 的既定流程；独立 `pi-team-reviewer` 在相同流程上增加原生 Pi reviewer。旧冻结包仅是历史参照，不维持一个故意缺少既定阶段的长期 variant。参赛 Agent 的 reviewer 是 Pi 内部 sub-agent，不是 Braid 的 Issue assignee。两个当前 variant 各自生成两题最终产物，再由同一官方本地 Runner 和本地公开需求模拟测试对冻结产物评分。

本地测试有 GitHub 47 项、Sheet 24 项；它们不是官网隐藏测试，不能当作官方百分制分数。现成 Runner、镜像和两题公开需求在 WSL 均已只读核实存在；生成与评测尚未启动。WSL 盘目前约有 37 GB 可用，完整矩阵开跑前须确认产物保留所需空间。

## 实施准备

只读预演已确认：现有 Pi 角色文件支持 `inheritProjectContext: false`、`inheritSkills: false`、`defaultContext: fresh`，当前运行入口逐个复制角色 Markdown，无需修改 Braid 或 Pi 扩展来增加 reviewer。现有 `arc_matrix.py --requirements-only` 负责本地生成，`package_arc_replay.py` 负责冻结应用，`experiments/hackathon-local/matrix.py` 负责逐场景回放；不新增实验框架。上一轮 71 场景的原始 runs 约占 3.6 GB，当前 WSL 约有 37 GB 可用；完整矩阵执行时仍需边运行边确认空间足够保留原始证据。

线性实施顺序：修正 `pi-team-mixed` 的两种可指派 profile 指引 → 基于相同源码独立建立 reviewer variant，仅增加 Pi 原生角色及整合前调用指引 → 核对两个新 ZIP 的差异和 Runner 入口 → 四次独立生成 → 每组冻结两个应用 → 用同一套 71 项本地公开需求模拟测试回放并报告。角色接口的细节以实施时冻结的 Pi 版本为准，不修改共享 SVC/Braid、官方 K3 包或旧结果。

## 运行现场

`pi-team-mixed` 与 `pi-team-reviewer` 已分别打包到 `runs/acceptance-workflow/20260926/`，SHA256 为 `cb0731983d106fc6349267a8fe50c7d9dde88d72872e794e1685e45e726028b7`、`ee1172fb7a49851b605a893c618002c71b8d15e202a99cd7485a36918dd5b551`。两包原有 22,524 个文件逐项比对，仅 `run.py`、两份成员指引不同，reviewer 包另有两份原生 reviewer 角色文件。Linux runtime 从旧冻结包复用；Runner、镜像与浏览器未重装。两包传至 WSL 后 SHA256 与本机一致。

本地执行目录为 WSL `/home/yyh/Development/factory26-acceptance-workflow-20260926/`。公开 GitHub/Sheet 需求、官方本地 Runner 和镜像已核实；模型使用官方 API 的本地受限 env 文件，测试在生成阶段不可见。生成记录分别写在 `runs/20260926-mixed-generation/` 与 `runs/20260926-reviewer-generation/`，各含两题；混合组并发 2，reviewer 组初始并发 1，避免同一 15 GiB 主机过载。

首次启动在输入冻结时暴露 `lab/plan.py` 的日志函数与同名局部变量冲突，尚未启动任何 job。改名后第二次启动发现独立 WSL 环境缺少既有 `lab/requirements.txt` 的 OTLP 协议包，也尚未启动 job；已在本次实验目录的 `.venv` 安装声明依赖。第三次启动 mixed 组，真实 Runner 的两题容器已经创建。两次失败原始日志保留在 mixed generation 目录，不算模型或应用结果。设施修正尚未单独提交：当前 `lab/plan.py` 属于父仓库先前未跟踪的 lab 文件，提交时须避免误纳入其他任务改动。

下一步：等待四次真实生成终态；对成功交付的每组两题冻结应用，运行本地 71 项模拟测试并保留原始证据。完整结果后先向用户报告。用户本轮明确授权自由提交与启动实验。
