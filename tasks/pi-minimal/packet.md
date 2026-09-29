# Pi 最小参赛 Variant

目标：截止前准备原生 Pi + background tasks + subagents 的独立 variant，移除 SVC/Braid，回到直接完成产品需求的最小方式。

用户已复核精简配置，授权实现、自由提交及官网正式参赛；每10分钟检查余额，不高于100停止。I10仍暂停，I11源码保留。

明确输入：GLM-5.3-flash 主会话（含视觉），Kimi 2.7 advisor；不设其它子角色；agent-browser、赛题相关技能、Context7/Exa；原生后台任务与subagents。无SVC/Braid。

分工：主线持有入口、打包、完整配置复核与提交；readable-cli构建纯Pi runtime；final_product_methods已完成初始配置；analytics_executor负责独立余额保护脚本。不得新增测试/模拟探针或调用模型试运行。

配置复核已完成，配置与授权仅适用于此新variant；其它实验仍不得使用参赛额度。冻结包与余额保护已完成；用户最新调整为先本地运行，官网提交暂缓。

最终配置见[config-review.md](config-review.md)。explorer/executor/browser-operator已删除；GLM官方确认视觉能力，vision也删除。Ponytail lite加入主会话和advisor。实际submission/run身份待启动后写入；不将源码完成当成已参赛。

## 本地先行：2026-09-29 21:47 CST

用户最新指示：“提交到官网之前，先本地运行；启动后，前20分钟先每5分钟下载一次工作区包下来检查pi会话内容”。正式 journal 仅 prepared，submission_id/run_id 均为空；不得自动启动官网控制器。

冻结 ZIP SHA256：`060bbf123e24771a4044c1a12fe0637f854c810c75af72d91279fc8691607909`。
WSL 使用相同 ZIP、官方本地 Runner、公开 Hackathon requirements 并行生成两题，每题 4GiB/2CPU，不做本地评分。
模型使用自带 ARC API key（个人 Meter 账户），不使用正式参赛额度；不能把该账户余额与285.86参赛额度混淆。

- WSL实验目录：`/home/yyh/Development/factory26/runs/pi-minimal/20260929/local/generation`
- GitHub：`pi-minimal--hackathon--github-b91ca34d0a4196`
- Sheet：`pi-minimal--hackathon--sheet-e24836ce1f57c2`
- 启动记录：`started_at=1790689645`；控制器 PID 1477715。
- 观察：第5/10/15/20分钟留存工作区及原生会话；`lite_baseline_monitor`负责定时归档下载和语义检查；输出 `local-observation.md`，原始快照在 `runs/pi-minimal/20260929/local-observations/`。
- 检查：真实进展、模型及唯一advisor角色、技能/视觉/浏览器/MCP/后台任务的调用和错误；尚未触发组件明确标未验证，不强行注入调用要求改变配方。

官网后续启动仍受每600秒参赛余额检查、不高于100取消和阻断后续任务的规则约束；当前未启动官网和余额守护，避免误报本地启动为正式参赛。

### 当前有效范围：仅 GitHub，自有 BigModel / Kimi key

用户随后限定“可行性验证只跑一个题目”及“我们自己的API key，而不是arc key”。已停止上述两条 ARC key 尝试，保留原始产物；原生 events 中尚无 assistant message_end，不能据此断言没有产生任何上游费用。

当前唯一有效实验：`/home/yyh/Development/factory26/runs/pi-minimal/20260929/local/own-key-generation`。
GitHub run：`pi-minimal--hackathon--github-59aaf58e7462bc`，`started_at=1790689981.3825152`。
复用现有4020网关，以 `.secrets/models.env` 中 BigModel / Moonshot 凭据路由；GLM请求发往 `open.bigmodel.cn`，Kimi发往 `api.moonshot.cn`，保留模型与推理参数。两供应商真实 models 查询确认相应模型存在。
观察窗口以新run起点重新计算；只有GitHub，Sheet不再启动。官网继续仅prepared，不自动提交。

## 能力采用修正（2026-09-29，已授权）

用户要求停止pi-minimal调查，并随后批准修正；原run已停止；用户随后授权“恢复pi-minimal，10分钟后重新观察组件使用情况”。
- 原Ponytail仅是共享改写skill，未安装原生Pi扩展。pi-minimal现vendor官方4.10.0最小依赖，主会话和advisor显式加载扩展，PONYTAIL_DEFAULT_MODE=full；不改I11共享技能。
- 根据用户 ~/.codex/AGENTS.md 提取无人值守适用的方法，合入variants/pi-minimal/instructions.md；去除人类审批/等待/确认，保留判断、设计、真实证据、文档与advisor方法，并补齐一般性流程。不修改个人原文件，不引入SVC/Braid。
- 增加advisor的决策时机、按问题路由skill、依赖文档查证条件；subagents采用原生compact工具说明。auth技能description仅在此variant打包副本改写。
- 新capability-evidence扩展从实际before_provider_request记录system/developer、tools和model，按内容摘要去重，不保存会话正文/header或发探针，主/子会话均加载。
- better-sqlite3首次binding问题已由原Agent修复；预包新增app-env选目标Node20与11.10.0/ABI115原生缓存，不预置生成应用源码/依赖树。详情prepacked-native.md。
- I11恢复的全量文件权限扫描已删除；本轮正在运行的旧代码未被热改。I11于14:45:02Z真正进入Braid，14:46起已有context replacement；原I10现场保持暂停。
源码语法检查完成；更新纯Pi runtime正在构建，新制品尚未通过模型运行验收。

## 修正后接续（2026-09-29）

保留原 GitHub 应用与 Pi session，剔除依赖/浏览器缓存后在相同容器路径恢复；不重新生成需求、不启动 Sheet、不提交官网。
原始归档 8,709 个文件，无跳过的符号链接，SHA256 `2186d32aaede8de0867e106ba42d0279a2aaed33ac75733d2eac486cec611667`。
新冻结包 SHA256 `3998ee50feaefc55fb1e6e539027f4a5be77aeed2da98385a69b798e2c7e2aac`。
接续脚本位于 `resume/`；新运行使用 BigModel/Moonshot 自有凭据、4GiB/2CPU；实际恢复后第10分钟检查新会话增量和 provider-facing 能力证据。
原运行归档保留；依赖由 Agent 使用 app-env 在目标 Node20 下重新安装。
新实验目录：WSL `runs/pi-minimal/20260929/native-fix/own-key-generation`，身份与观察结果记录到 [resume-observation.md](resume-observation.md)。

本轮实际 run 已确定为 `pi-minimal--hackathon--github-2c26574a6a09be`，恢复源为 `pi-minimal--hackathon--github-59aaf58e7462bc`；首次新的 provider-facing capability 记录时间为 `2026-09-29T15:08:57.466Z`，10 分钟取证节点为 `2026-09-29T15:18:22Z`。观察报告已完成：主请求真实注入 Ponytail full，主工具面含 compact subagent 工具，PBB 与 Node20/native SQLite 有真实证据；advisor、Context7/Exa 和浏览器尚未触发，后端首次启动的 `reactionsFor` 重复声明已单独记录。详见 [resume-observation.md](resume-observation.md)。

## 正式参赛授权更新
用户明确授权停止本地 pi-minimal、提交官网参赛；余额每600秒检查，≤100元立即取消并禁止后续题启动。提交当前修正版纯Harness（native-fix/base-agent.zip），不包含本地生成应用或保留session；两题沿先前批准矩阵。原未上传 prepared journal 保存为 official-pre-native-fix，新 official journal 冻结新版。I11恢复修复继续，原I10保持暂停。

正式提交已创建：submission `f9bd3524fe75`，GitHub run `f3424d6aa387` 已进入RUNNING；Sheet由同一控制器顺序创建。冻结纯Harness SHA256 `c727b9aa9d0948dd1a5ac2d8c39bad45fe99a8c3fcf5bc4ac171d1ae535dec27`。提交前参赛余额285.862202元；余额守护PID42828、控制器PID42814，完整身份记录于official/processes.json。网站run仍返回billing_mode=self_funded，需与submission credential_mode独立记录，不把此字段当成未参赛。
本地接续run `pi-minimal--hackathon--github-2c26574a6a09be` 已按用户要求cancelled，finished_at=1790696261.6131678；工作区保留。
