# 开发 Factory26

开发者是 Coding Agent，用户参与目标、设计与授权。
常驻约定见 [AGENTS.md](AGENTS.md)；当前任务的决定、证据与恢复点放在 task packet。

## 修改对象与反馈来源

不维护针对 Factory 实现或开发基础设施的测试、fixture、mock 或 smoke，也不以其他名称重建这些测试。
官方 benchmark 和生成应用自身的验收保留；SVC Corpus 不设内容测试。

| 修改对象 | 源码入口 | 实际反馈来源 |
| --- | --- | --- |
| Harness 的指令、角色、协作或执行 | `variants/<name>/main.py`、`run.py`、`agents/` | 生成运行的原生配置、会话与应用，获授权的 bench 得分。 |
| 原生工具或打包 | `scripts/runtime.py`、variant 的 `build.py`、`scripts/package_agent.py` | 实际安装、构建与提交过程的输出。 |
| 实验执行或 ARC 接入 | [lab/README.md](lab/README.md)、`lab/plan.py`、`lab/run.py`、`lab/otlp.py`、`lab/arc_bench/arc_bench_adapter.py` | 外部命令、原始 OTLP、官方 Runner 的真实运行与错误。 |
| Pi 子代理观测 | variant 的 `extensions/` | 实际会话和原始观测记录。 |
| Braid | `sources/braid` 自身说明和公开 local 接口 | 自身构建和实际 Harness 调用结果。 |
| SVC skill 接线 | variant 的启动参数、角色 Markdown、`build.py` | 运行中实际读取的技能及上下文。 |

各团队 variant 是完整独立实现；不相互 import，也不从共同配方生成。当前活动、实验与历史状态见 [Variant 索引](variants/README.md)，新实验的 case 与运行名见 [实验导航](experiments/README.md)。
原生 models/settings/角色 Markdown 是 Pi 直接消费的材料，profile.json 是 Braid 的原生 profile 字段。
`run.py` 明确构造本次 Braid 请求。
共有支持模块只做文件、进程与证据操作。

## 从任务到实现，再回到文档

从对应 packet 确认当前问题、已批准方案、授权与未完成事项，再读 [技术说明](docs/product-tdd/index.md) 中受影响的约定。
源码描述实际行为，设计描述意图；两者冲突时先记录差异，不能用文档里的承诺代替已实现能力。
临时调查、候选方案和计划留在 packet，决定变化时改写当前答案；不要要求接手者按日期猜哪段正文仍有效。

实现中，产品行为变化更新 PRD，跨组件责任或失败语义变化更新技术说明，运行方式变化更新本文件或 Deployment。
局部实现的非显然理由、外部接口特殊行为和维护约束写在代码旁；已有完整解释时引用其归属，不重复抄写。
注释使用完整句子，按句换行，不为行宽机械折行，也不逐行翻译代码。
仅影响一个局部实现的改动不要求更新全部文档。

收尾记录实际结果与限制，将持续有用的知识提升到长期说明，原始证据留在运行目录，历史结论归 reports。
完成或转交前保留未完成验收与恢复入口；旧阶段的授权、模型资格及平台状态不能作为新阶段的实时事实。

## 修改一个成员或内部角色

下面以 `variants/pi-braid` 为例，其他 variant 独立维护自己的选择。

| 想改变什么 | 修改位置 | 需要一起理解的消费者 |
| --- | --- | --- |
| 可指派成员的能力描述、主模型或推理档位 | `agents/<id>/profile.json` | Braid 的成员与主会话配置；不要把它当作 explorer/executor 配置。 |
| 根 Issue 的启动成员 | `run.py` 的 `ROOT_PROFILE_ID` | 只选择根工作项的启动成员；后续 Issue/PR 由 Agent 通过 assignee 指派。 |
| 主会话指引 | `agents/<id>/instructions.md` | native_files 将内容传入本次 Braid profile。 |
| 内部 executor 等角色的模型、工具和技能 | `agents/<id>/agents/<role>.md` | Pi 子代理扩展消费；它不是 Braid assignee。 |
| provider 模型描述与原生设置 | `agents/<id>/models.json`、`settings.json` | Pi 消费；运行时替换实际 endpoint，不能用 descriptor 代替 API 能力事实。 |
| 主会话启用的技能与扩展 | `run.py:native_files` 的 launcher 参数 | 主会话关闭默认发现后显式启用；内部角色有自己的技能声明。 |
| 正式包提供哪些材料 | `build.py` 的选择与对应技能源 | 打包包含文件不会自动启用技能；主会话和子代理所选材料必须实际可取得。 |

例如调整 executor 模型，从该成员下的 `agents/executor.md` 开始；需要新增模型描述时再修改同成员的 models.json。
若为 executor 新增技能，同时考虑它的 skills/skillPath 与包中的材料；不因此改动其他 variant 的角色。
原生接口与精确字段以这些文件及所选原生客户端为准，不在文档另维护全套配置副本。

I13内部角色默认使用独立历史（`defaultContext:fresh`），以本次委派和按需读取取得背景；`inheritProjectContext:false`与`inheritSkills:false`关闭自动继承。角色保留自己的技能发现入口，模型按需读取独立文件。所有Agent Skill的SKILL.md及references正文均不得拼入system、profile、role或task prompt，发现信息只含名称、description和路径；这条约定同时适用于主会话与子代理。历史冻结包保留原身份，不能据当前文档推断其输入已改变。

[pi-braid-i13](variants/pi-braid-i13/)的角色description帮助调用方选择有委派价值的工作，正文说明用途；不声明角色工具白名单。`settings.json`选择默认基础工具，原生扩展提供委派、联络、等待及后台执行能力。`run.py`只替换角色的技能和扩展路径，不追加父profile、运行条件或方法正文；以`PI_SUBAGENT_MAX_DEPTH=3`限制子层深度。完整工具能力不代替委派的目标与修改范围。原生接口介绍工具使用，技能提供按需方法，不在角色中重复维护。

原生 Hackathon 四配置由 `variants/native-hackathon/hackathon_main.py` 装配：角色简介用于选角，正文在 `variants/native-hackathon/agents/`，`scripts/package_hackathon.py` 收录正文和技能。
Base/SVC 两组提供相同探索工具；只有 SVC 组装入对应方法及完整技能入口。
Codex 使用原生 `agents/*.toml`；历史由 spawn 参数控制，按实际工具协议传 `fork_context:false` 或 `fork_turns:"none"`。
Pi 明确 append 基础系统提示、选定技能并关闭内建角色发现。配置表达意图，实际生效与收益仍须从后续真实会话取证。


## 准备实际需要的依赖

原生工具准备不读取 variant、Corpus 或 benchmark：

```sh
make tools
python3 scripts/runtime.py path
```

工具版本与当前共用安装资源来自 `harness/npm/package-lock.json`。
Node/npm 必须已可用；按当前 agent-browser 版本使用 Node 24+。
相同 lock 复用 `~/.cache/factory26/`，Chromium 由 Playwright 安装器按 lock 配套版本缓存，agent-browser 与 Playwright Test 复用该二进制。
variant 可以选择其他显式 runtime；共享安装不决定其行为。
Linux 构建另收录 rg、ast-grep 与 MCPorter：前两者按原生二进制启动，MCPorter 使用 Node 24。
运行入口将 `MCPORTER_CONFIG` 指向已物化的 `exploration-tools/assets/mcporter.json`，按需通过 Context7、Exa、Handsontable Docs 服务查询；工具指引随同该 skill 分发。
本轮仅更新构建声明与接线，旧 runtime 和冻结包不会因此具备新工具；下次实验前须从当前 lock 构建新资源。

团队 Harness 另需 Braid 二进制与 SVC 技能集合。
使用现有 `sources/braid`、`sources/svc` 工作树。
当前活动 variant 使用 `harness/skills/svc-{task-packet,investigation,design,implementation,verification}` 五个目录链接，指向 `sources/svc/skills/`；`harness/skills/svc` 是归档 variant 的历史快照。需要不同技能来源时显式传入包含所选完整技能的 `--skills-root`（运行）或 `--skills`（打包）。
缺源码时先确认所需上游与本地修改，不让能力解析触发隐式 clone 或切换分支。

```sh
cargo build --locked --manifest-path sources/braid/Cargo.toml
```

开发侧 `.venv/bin/svc` 是独立的开发/analysis 工具；参赛 Agent 只使用技能材料，不安装 SVC CLI。
显式选择完整开发源码安装，要求本机有 uv 和 Git：

```sh
python3 scripts/runtime.py dev-svc --svc-source ~/Development/svc
```

该命令创建或复用 `.venv`，安装所选工作树的 `cli/`，并将来源路径、HEAD、工作区状态和版本写入 `.bootstrap/dev-svc.json`。
本次采用完整开发源码 `80996c115ba635c6b85db47d0b14663293b95f12` 加该工作树本地修改，CLI 为 15.0.0；只切到相同 HEAD 不包含本地修改，须同时交接下面的源码归档。
其安装版本与项目 Corpus baseline 可由 `.venv/bin/svc status --json` 查看，配置健康不代表开发路径或模型接线已经验收。

### 换机器时哪些内容会缺失

| 材料 | 取得边界 |
| --- | --- |
| 本仓 variant、技能入口、工具 lock | 跟随已提交源码；未提交改动需要单独交接。 |
| npm/Linux 工具 | 通过上述 runtime 入口准备，使用对应 lock 和构建输入。 |
| `sources/braid`、`sources/svc` | 独立 Git 仓库，父仓库 clone 不会带入；需取得实际采用的版本及尚未发布的本地修改。仅 clone 上游 main 不能保证等价。 |
| 开发 `.venv/bin/svc` | 恢复完整开发 SVC 源码后运行 `runtime.py dev-svc --svc-source <该目录>`；不从裁减后的参赛树安装。 |
| 官方 Runner、题目、镜像与旧 runs | 按运行说明取得或交接；它们不随源码自动出现。 |

独立仓库按实际源码交接，不依赖先提交或推送：

```sh
python3 scripts/sources.py export sources/braid /path/to/handoff/braid
python3 scripts/sources.py export sources/svc /path/to/handoff/factory-svc
python3 scripts/sources.py export ~/Development/svc /path/to/handoff/dev-svc
```

将整个 handoff 目录复制到另一机器，恢复到尚不存在的目录：

```sh
python3 scripts/sources.py restore /path/to/handoff/braid sources/braid
python3 scripts/sources.py restore /path/to/handoff/factory-svc sources/svc
python3 scripts/sources.py restore /path/to/handoff/dev-svc ~/Development/svc
python3 scripts/runtime.py dev-svc --svc-source ~/Development/svc
cargo build --locked --manifest-path sources/braid/Cargo.toml
```

交接包含 Git bundle、本地修改的 binary patch、未跟踪文件、浅克隆边界及来源记录。
恢复保留本地提交、分支、origin 和修改内容；原有暂存/未暂存划分合并成工作区修改，Git 忽略的构建产物、环境和凭据不复制。
现有目录拒绝覆盖；先选新位置，再决定是否替换旧工作树。
这不是跨仓库事务快照，export 期间不要编辑该源码树；本仓未提交改动仍须另行交接。
Cargo、uv 和 runtime 准备在目标平台重建依赖，不复制跨平台 venv/node_modules。

## 直接验证源码

以下命令写出真实原生配置、技能目录和 Braid request，不启动 Braid 或调用模型。
`REQUIREMENTS` 指向带 requirements.yaml 的小需求目录，不要求整个 benchmark。

```sh
RUNTIME=$(python3 scripts/runtime.py path)
python3 variants/pi-braid/main.py "$REQUIREMENTS" \
  --output-dir runs/dev-mixed --runtime "$RUNTIME" \
  --braid sources/braid/target/debug/braid \
  --skills-root harness/skills \
  --base-url http://127.0.0.1:9/v1 --prepare-only
```

输出路径为 `runs/dev-mixed/.factory26/<id>`。
从 braid-request.json、work/capabilities 下的原生材料开始检查，不再追踪 effective config 的两层转换。
真实运行去掉 `--prepare-only`，使用实际 base URL，并由调用环境注入 `OPENAI_API_KEY` 或 `FACTORY26_API_KEY`。
密钥不放进源码或命令参数；角色模型由各 variant 固定，MODEL 若提供则必须匹配根角色。

真实运行会产生模型费用，按当前任务的实验授权执行。
每次运行创建独立记录，成功从 Braid delivery commit 导出应用；失败保留工作现场和原始日志。
平台部署布局仍见 [运行文档](docs/deployment/index.md)。

## 构建独立运行资源与制品

Linux runtime 可单独构建；下例团队资源包含 Braid，raw 资源省略 `--braid-source`，不会读取 Braid/SVC 或团队配方。
先选择可用 Docker context，不修改全局默认。

```sh
python3 scripts/runtime.py linux --backend pi --docker-context arcbox-win \
  --braid-source sources/braid --output runs/runtime-team
python3 scripts/package_agent.py --variant pi-braid \
  --runtime runs/runtime-team --stage runs/staged-mixed
```

官方 Runner 的 `--agent` 接受已展开目录，局部验证不必压 ZIP。
要冻结参赛包，将上述 `--stage` 换成 `--output runs/packages/mixed.zip`；同一源码、材料与资源参与两种封装。
已有输出不覆盖。

raw 打包可直接使用 `package_raw_core.py --runtime <runtime目录>`，不要求先创建团队 ZIP；`--source <历史ZIP>` 只保留为旧资源的读取方式。
模型和 backend 仍由 raw 命令显式选择。

SVC 在 `sources/svc/skills/` 提供五个独立完整的 skill；各目录的 `SKILL.md`、`references/` 与 `assets/` 构成对应分发材料。
`copy_skill` 由源码运行和打包共用，复制入口、标准资源目录及许可文件，将来源链接物化为普通文件。
维护者 AGENTS、仓库文档、CLI 和开发环境不进入 skill。
每个 variant 独立选择要提供的技能及哪些会话启用它们；没有 SVC 专用正文参数或二次装配。

纯指令、角色与 skill 变化只重新装配文件，不重新安装 npm、Chrome 或 Runner。
更换真实运行依赖才重建对应资源。
Cargo/npm/Docker 负责增量复用，不另建通用构建系统。


## 运行证据与收尾

Braid 运行诊断以外层实验 run 为入口：`make braid-report RUN=<实验目录> OUTPUT=<新网站目录>`。
[诊断运行手册](docs/deployment/braid-diagnostics.md)说明 Backend 查询、补采、失败产物、组件修改位置及验收边界；`lab.analysis.run_viewer` 负责实验总览，Braid 网站负责 OTLP 内的会话和协作现场，两者不是同一数据视图。
修改导出语义时从 `sources/braid/src/telemetry.rs`、`evidence.rs` 开始，修改页面从 `lab/analysis/braid_telemetry_viewer.py`、同名 HTML 模板开始；构建本机 Braid 后用已归档真实 Backend 生成新目录核对，不以重新运行模型作为默认验证手段。

原始证据位于生成输出的 `.factory26/<id>`，可用 `python3 -m lab.analysis.factory show --run <该目录>`、`analyze --run <该目录>`。
外层实验状态先用 `python3 -m lab show <实验或run目录>`；详细 ARC/Factory 解释用 `python3 -m lab.analysis.factory show --run <run目录>`。二者描述不同进程边界，不能用其中一个的成功代替另一个。
`lab.analysis.factory show` 和 `lab.analysis.run_feedback brief` 同时接受这两种目录；外层摘要链接生成、部署、评分、应用、原生会话和原始错误。
`python3 -m lab.analysis.run_viewer --root <包含runs的根目录>` 发现嵌套实验，进入一条 run 后停止递归扫描其输入和依赖。

`lab.analysis.factory` 只保留 list/show/analyze；旧配置式 generate/run/bootstrap/eval/batch、concurrency 及 shared submission 入口已删除。
官网客户端、历史查询与诊断不再 import 旧生成器；旧结果和官网 journal 保留。
跨仓库改动记录实际依赖与运行结果；更新受影响的操作说明。
不要为了文档一致重写历史实验报告。

旧 `official_matrix.py --freeze-packages` 入口已移除。
新官网提交用 `competition.py prepare --model-config <平台模型JSON>` 显式提供 base_url、model、visual_model；矩阵执行消费显式 manifest，不能反向解析任意 Harness 的内部配置。
