# 参赛 Agent 的 SVC 接线改造

## 产品行为与边界

参赛 Agent 的可见工具中不再有 `svc`。当任务状态、探索、设计、实施、委派或验证需要方法指导时，它从技能目录发现 `svc`，读取该技能入口，再按需读取 Corpus 的具体文档；普通任务不自动装入 Corpus 正文。`harness/AGENTS.md` 的 SVC 索引和 user-scope AGENTS 复制一并删除。开发 Agent 的 `.venv/bin/svc telemetry|analysis` 是另一棵 SVC 安装，不改变。

`sources/svc/corpus` 仍是内容权威。Factory 在装配 profile 时把 `harness/skills/svc/SKILL.md` 和所需 Corpus Markdown 复制到同一个技能目录；技能入口只负责说明适用场景与文档路径，不再产生第二份方法正文。维护者用的 `corpus/AGENTS.md` 和 `version.json` 不进入 Agent 技能。Braid 继续只接收普通 profile、指派和工作项，不知道 SVC 或技能选择。

“删除 CLI”在本次指参赛包和 Agent 环境完全没有 SVC CLI。`sources/svc/cli` 仍留在独立上游 checkout，但不构建、不复制进 ZIP，也不进入 Agent 的工作目录；物理删除这份源码对 Agent 的命令选择没有增益，反而扩大上游同步范围。

## Profile 与变体

每个主 Agent profile 显式选择 `svc` skill；explorer、executor、specialist 角色可按职责选择，纯浏览器和读图角色不默认加载它。Pi 主会话使用显式 `--skill /.../SKILL.md`，pi-subagents 使用 `inheritSkills: false`、`skills` 和 `skillPath`；独立临时技能已在两条路径中实际读取入口和相邻文档。Codex app-server 已在隔离 home 的 `skills/<name>/` 中发现技能，主代理提示只含技能目录而不预载相邻文档。Codex 原生子代理实际可见性尚未通过模型调用验证，实施时把它作为第一项真实接线 spike；当前两份旧代理配置的本地端口均未监听，不能拿它们证明成功。profile 的可用 CLI 列表移除 `svc`。

`pi-team-vv` 当前唯一增量是把 Test Design 和 Verification 正文预载到指令。改造后它仍需与 `pi-team-mixed` 有可见区别：使用单独的 VV profile，保留相同模型和角色，仅增加一条促使 Agent 在设计验收和完成判定时打开 `svc` 技能相应文档的短指引；正文仍由 skill 按需读取。既有成绩和新接线不能当作同一配置复测。

## 运行与打包

本地 `bootstrap` 不再安装参赛 SVC wheel，生成工作区不创建 `bin/svc`，也不写入 SVC 的 user-scope AGENTS。`sources.py` 对 SVC 只记录源码快照与 run 归档；Braid 仍构建并核对二进制。官方 Docker 构建不再安装 SVC CLI 或生成 `runtime/bin/svc`；Codex 所需 LiteLLM 保持。冻结 effective profile 包含技能材料及其哈希，包内仍保留 SVC 源码快照身份，防止未提交内容与实际技能不一致。

## 验收

1. Pi 主 Agent 和子 Agent 在隔离临时目录中只看到获选技能；打开 `svc` 后能按相对路径读取一篇 Corpus 文档。Codex app-server 的技能列表与主 Agent 输入能发现 `svc`，角色级可见性以真实子代理行为验证。
2. 本地生成工作区与官方 ZIP 均无 `svc` 可执行文件、SVC CLI Python 包和 SVC user-scope AGENTS；`.venv/bin/svc` 仍可做开发分析。
3. 四个 variant 的模型、Braid assignee、角色和技能选择可从 effective profile 复核；VV variant 只有所设计的 V&V 引导差异。
4. `make test`、独立无模型官方包 smoke 和本地安装/包内材料核对通过。测试只检验技能装配与运行边界，不断言 SVC Corpus 的篇目或措辞。评分实验等用户通知设施就绪后再运行。

## 实施次序

Pi 技能装载预演已完成。开工后先以小的 Codex 原生子代理 spike 核实技能实际可见性；若当前环境无法启动该模型链，则先完成 Pi 路径，并明确保留 Codex 验收缺口，不把 schema 支持冒充运行成功。随后修改 profile 解析和原生模板；再移除本地 CLI 安装与 AGENTS 注入、移除官方 wheel 打包；最后更新使用这些边界的测试和运行文档，执行上述验收。改动源文件前按项目约定呈现影响并取得开工确认。本任务不修改通用开发 SVC，也不修改 SVC Corpus 正文。
