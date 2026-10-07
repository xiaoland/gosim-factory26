# 公共运行支持与构建入口

本目录处理工具资源、文件与进程、打包和模型网关；variant 自己维护生成与协作流程，Lab 持有显式实验请求。命令从仓库根执行，参数的完整定义用对应 `--help` 查询。

| 要修改什么 | 源码与说明 |
| --- | --- |
| 本机工具、Linux runtime、开发 SVC 或 host-exp runtime | [runtime.py](runtime.py)；生产 cache 与临时目录由 `production_environment` 设置。 |
| Variant 材料选择与目录/ZIP 封装 | [package_agent.py](package_agent.py)消费 I14 的 `materials.json`；`build.py` 只转交参数。 |
| 原生材料、技能链接与生成支撑 | [agent_support.py](agent_support.py)、[braid_runtime.py](braid_runtime.py)、[harness_layout.py](harness_layout.py)。 |
| 运行资源准入与实际进程管理 | [runtime_resources.py](runtime_resources.py)；跨组件约定见[资源说明](../../docs/product-tdd/runtime-resources.md)。 |
| 模型路由、兼容接口和预算 | [hackathon_gateway.py](hackathon_gateway.py)、[hackathon_gateway_compat.py](hackathon_gateway_compat.py)、[responses_compat.py](responses_compat.py)、[model_budget.mjs](model_budget.mjs)。公开路由定义归 [materials/model-gateway.json](../../materials/model-gateway.json)，凭据只由实际私有 deployment 注入。 |
| 外部独立源码的工作树交接 | [sources.py](sources.py)；本仓 `sources/` 已由父仓库跟踪，不用该命令重复导出。 |
| ARC 实验编译、启动、状态或恢复 | [Lab](../../lab/README.md)；不在 scripts 中另建调度入口。 |
| Linux runtime 镜像中的装配 | [submission](../linux/README.md)。 |

`runtime.py prepare` 和 `path` 不选择 variant 或 benchmark。`linux` 从 lock 和显式 Braid 源构建 Linux 工具；`derive-linux` 从明确的旧包和当前源码派生资源，保留来源身份。`host-exp` 为 controller/runner 冻结独立 Python runtime，它与 Agent 的 Linux runtime 不是同一制品。

## 准备原生工具

裸 `make` 与 `make help` 只显示开发入口，不安装依赖。当前运行使用 Lab 的 start/status/logs/restart，完整操作见 [Lab](../../lab/README.md)。compile/doctor/build 属于旧 lab.exp 冻结执行合同，见 [旧执行器](../../lab/exp/README.md)，不用于当前 run。

原生工具准备不读取 variant、Corpus 或 benchmark：

```sh
make tools
python3 tooling/scripts/runtime.py path
```

工具版本与当前共用安装资源来自 `materials/npm/package-lock.json`。
Node/npm 必须已可用；按当前 agent-browser 版本使用 Node 24+。
相同 lock 复用仓库内 `runs/runtime-cache/runtime-<lock-hash>/`，`npm ci --prefix` 的安装结果也在这里；`prepare` 使用对应的 `runs/build-cache/runtime-<lock-hash>/` 保存 npm 下载、构建工具 cache 和临时目录。两者都在 WorkSSD 仓库内，Chromium 由 Playwright 安装器按 lock 配套版本缓存，agent-browser 与 Playwright Test 复用该二进制。
variant 可以选择其他显式 runtime；共享安装不决定其行为。
Linux 构建另收录 rg、ast-grep 与 MCPorter；这些二进制及 Node 工具由 [Linux 资源构建](../linux/README.md) 装入。I13 的服务、扩展和私有工具凭据选择见 [I13 本地说明](../../variants/pi-braid-i13/README.md#工具与技能接线)。

团队 Harness 另需 Braid 二进制与 SVC 技能集合。
使用本仓库的 `sources/braid`、`sources/svc` 源码目录；它们由 Factory26 Git 统一跟踪，不再是嵌套仓库。
技能来源与 variant 的选择边界见 [Harness 材料](../../materials/README.md)。
缺源码时先确认所需上游与本地修改，不让能力解析触发隐式 clone 或切换分支。

```sh
export CARGO_HOME="$PWD/runs/build-cache/braid/cargo"
export CARGO_TARGET_DIR="$PWD/sources/braid/target"
export TMPDIR="$PWD/runs/build-cache/braid/tmp"
mkdir -p "$CARGO_HOME" "$TMPDIR"
cargo build --locked --manifest-path sources/braid/Cargo.toml
```

开发侧 `.venv/bin/svc` 是独立的开发/analysis 工具；运行时 Agent 只使用技能材料，不安装 SVC CLI。
显式选择完整开发源码安装，要求本机有 uv 和 Git。先把 `DEV_SVC_SOURCE` 设为完整源码的绝对路径；本机来源记录见根目录可选的 `AGENTS.local.md`，不要从参赛技能树安装：

```sh
python3 tooling/scripts/runtime.py dev-svc --svc-source "$DEV_SVC_SOURCE"
```

该命令创建或复用 `.venv`，安装所选工作树的 `cli/`，并将来源路径、HEAD、工作区状态和版本写入 `.bootstrap/dev-svc.json`。
安装来源身份以本机 `.bootstrap/dev-svc.json` 和实际源码归档为准；只取得同一 HEAD 不包含尚未提交的本地修改，跨机器必须同时交接它们。
其安装版本与项目 Corpus baseline 可由 `.venv/bin/svc status --json` 查看，配置健康不代表开发路径或模型接线已经验收。

### 换机器时哪些内容会缺失

| 材料 | 取得边界 |
| --- | --- |
| 本仓 variant、技能入口、工具 lock | 跟随已提交源码；未提交改动需要单独交接。 |
| npm/Linux 工具 | 通过上述 runtime 入口准备，使用对应 lock 和构建输入。 |
| `sources/braid`、`sources/svc` | 随本仓库 clone/checkout 取得；源码版本归父仓库 commit，未提交改动仍需单独交接。 |
| 开发 `.venv/bin/svc` | 恢复完整开发 SVC 源码后运行 `runtime.py dev-svc --svc-source <该目录>`；不从裁减后的参赛树安装。 |
| 官方 Runner、题目、镜像与旧 runs | 按运行说明取得或交接；它们不随源码自动出现。 |

Factory26、Braid 与参赛 SVC 技能一起通过本仓库交接，不再分别 export/restore。迁入时的源码身份和独立 Git 历史恢复材料见[源码纳入记录](../../tasks/source-repository-integration/packet.md)。

开发侧完整 SVC 若仍位于外部独立仓库，可按实际源码交接，不依赖先提交或推送：

```sh
python3 tooling/scripts/sources.py export "$DEV_SVC_SOURCE" runs/handoff/dev-svc
```

将整个 handoff 目录复制到另一机器，恢复到尚不存在的目录：

```sh
python3 tooling/scripts/sources.py restore runs/handoff/dev-svc "$DEV_SVC_SOURCE"
python3 tooling/scripts/runtime.py dev-svc --svc-source "$DEV_SVC_SOURCE"
cargo build --locked --manifest-path sources/braid/Cargo.toml
```

外部独立仓库的交接包含 Git bundle、本地修改的 binary patch、未跟踪文件、浅克隆边界及来源记录。`sources.py export` 只接受仓库根目录，拒绝把本仓库中的源码子目录误导出为整个 Factory26。
恢复保留本地提交、分支、origin 和修改内容；原有暂存/未暂存划分合并成工作区修改，Git 忽略的构建产物、环境和凭据不复制。
现有目录拒绝覆盖；先选新位置，再决定是否替换旧工作树。
这不是跨仓库事务快照，export 期间不要编辑该源码树；本仓未提交改动仍须另行交接。
Cargo、uv 和 runtime 准备在目标平台重建依赖，不复制跨平台 venv/node_modules。

## 构建独立运行资源与制品

Linux runtime 可单独构建；下例团队资源包含 Braid，raw 资源省略 `--braid-source`，不会读取 Braid/SVC 或团队配方。
先通过标准 `docker context use` 或 `DOCKER_CONTEXT` 选择可用 daemon；构建入口在开始时冻结 endpoint。源码、Git 和输出仍在本地，构建输入由 Docker CLI 传输。

```sh
python3 tooling/scripts/runtime.py linux --backend pi \
  --braid-source sources/braid --output runs/runtime-team
python3 tooling/scripts/package_agent.py --variant pi-braid-i14 \
  --runtime runs/runtime-team --stage runs/staged-i14
```

新 SDK 目录是薄入口，需由 Lab 对实际子域安装并绑定只读定义组件；单独复制目录不能满足运行合同。Hosted ZIP 才是自包含交付，二者各自只采用一种满足方式。
要冻结参赛包，将上述 `--stage` 换成 `--output runs/packages/pi-braid-i14.zip`；同一源码、材料与资源参与两种封装。
已有输出不覆盖。打包器在写入 ZIP 的同一次文件读取中计算内容摘要，清单对应实际写入字节，保留原压缩策略。文件内容、权限与来源关系不变，封装方式变化会改变包的 SHA，须发布为新制品。

raw 打包可直接使用 `package_raw_core.py --runtime <runtime目录>`，不要求先创建团队 ZIP；`--source <历史ZIP>` 只保留为旧资源的读取方式。
模型和 backend 仍由 raw 命令显式选择。

技能装配与许可边界见 [Harness 材料](../../materials/README.md)。

纯指令、角色与 skill 变化只重新装配文件，不重新安装 npm、Chrome 或 Runner。
更换真实运行依赖才重建对应资源。
Cargo/npm/Docker 负责增量复用，不另建通用构建系统。

## I14 源码装配

Variant main/run 要求 ready context，公共源码入口负责创建本地装配与服务，不让开发者填写内部 JSON：

```sh
python3 -B tooling/scripts/experiment_entry.py --source variants/pi-braid-i14 \
  --runtime "$RUNTIME" --skills materials/skills "$REQUIREMENTS" \
  --output-dir runs/source-generation --prepare-only
```

RUNTIME 和 REQUIREMENTS 必须是明确真实输入，输出、日志和临时文件均在 WorkSSD。e2e 还需 `--e2e-runtime`。去掉 prepare-only 会请求实际生成，须有当前模型授权；源码未发布定义不声称跨域 checkpoint 能力。正式执行使用[Lab](../../lab/README.md)，组件/私有输入分离归[制品合同](../../lab/exp/artifacts.md)。
