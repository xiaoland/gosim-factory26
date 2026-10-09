# 公共运行支持与构建入口

本目录处理工具资源、文件与进程、打包和模型网关；variant 自己维护生成与协作流程，Lab 持有显式实验请求。命令从仓库根执行，参数的完整定义用对应 `--help` 查询。

| 要修改什么 | 源码与说明 |
| --- | --- |
| 本机工具、Linux runtime、开发 SVC 或 host-exp runtime | [runtime.py](runtime.py)；生产 cache 与临时目录由 `production_environment` 设置。 |
| Variant 材料选择与目录/ZIP 封装 | [package_agent.py](package_agent.py)消费 I14 的 `materials.json`；`build.py` 只转交参数。 |
| 原生材料、技能链接与生成支撑 | [agent_support.py](agent_support.py)、[braid_runtime.py](braid_runtime.py)、[harness_layout.py](harness_layout.py)。 |
| 原生执行登记与实际进程管理 | [runtime_resources.py](runtime_resources.py)；跨组件约定见[资源说明](../../docs/product-tdd/runtime-resources.md)。 |
| 模型路由、兼容接口和预算 | [model_gateway_service.py](model_gateway_service.py)持有 run-owned 服务，显式选择 [Rust Chat proxy](../../sources/model-proxy/README.md)或既有 LiteLLM；[hackathon_gateway.py](hackathon_gateway.py)冻结路由，兼容及预算归 [hackathon_gateway_compat.py](hackathon_gateway_compat.py)、[responses_compat.py](responses_compat.py)、[model_budget.mjs](model_budget.mjs)。可用 deployment 归 [materials/model-gateway.json](../../materials/model-gateway.json)，显式有序链由[跨 variant 模型配方](../../materials/model-recipes/README.md)提供；凭据只由实际私有 deployment 注入。 |
| 外部独立源码的工作树交接 | [sources.py](sources.py)；本仓 `sources/` 已由父仓库跟踪，不用该命令重复导出。 |
| ARC 运行启动、状态或接续 | [Lab](../../lab/README.md)；不在公共脚本中另建调度入口。 |
| Linux runtime 镜像中的装配 | [Linux 支持](../linux/README.md)。 |

`runtime.py prepare` 和 `path` 不选择 variant 或 benchmark。`linux` 从 lock 和显式 Braid 源构建 Linux 工具；`derive-linux` 从明确的旧包和当前源码派生资源，保留来源身份。`host-exp` 为 controller/runner 冻结独立 Python runtime，它与 Agent 的 Linux runtime 不是同一制品。

## 资源归档归属分析

`python3 tooling/scripts/resource_attribution.py --harness HARNESS_ARCHIVE --samples PROCESS_EVIDENCE/resources.jsonl` 只读已保存的进程登记、native-state、Braid manifest/status与资源日志，向stdout输出逐样本归属及CPU/I/O计数速率。`--harness`须指向该执行的`data/harness/<scope>`目录，不是整个runs；也可用同目录的`resource-incidents.jsonl`或`resource-critical.jsonl`作为样本来源。历史样本缺boot ID时读取同目录resources-baseline.jsonl，缺计数不能补造速率。`cpu_ticks`单位是tick/秒，换算CPU秒须使用baseline的clock_ticks；IO字段中read_bytes/write_bytes为存储字节，rchar/wchar及syscr/syscw具有不同含义。

结果保留归属方法、具体登记路径、会话/工作项及工具作业证据；无法确定的历史活动turn仍是unknown。运行期间下载的完整project/workspace归档才能提供完整关联材料，轻量observer快照不保证覆盖所有进程记录。采样与保护职责、覆盖和存储上限见[资源说明](../../docs/product-tdd/runtime-resources.md)。

## Pi 会话用量统计

`python3 tooling/scripts/pi_usage.py <会话目录>` 只读递归统计目录内主会话和子会话的 Pi 原生 JSONL。对当前 vv，应选择 `.factory26/pi-minimal-vv/runs/<run-id>/` 根目录，使 `session.jsonl` 和 `session/<child>/...` 都在范围内；不要选择携带其它运行历史的整个应用目录。脚本只累计带 session 头的文件中的 assistant message，不累计事件流的 message_update/message_end 副本。会话镜像及 fork 继承的原消息按 entry ID、原消息时间和模型身份去重；缺失或冲突用量单列，未知不冒充零。`--since` 可排除接续继承的早期消息，必须带时区。

```sh
python3 tooling/scripts/pi_usage.py RUN_EVIDENCE --json
python3 tooling/scripts/pi_usage.py RUN_EVIDENCE --since 2026-10-07T22:59:00+08:00 --prices lab/arc_bench/arc-prices.json --json
```

JSON 提供总量、按模型和会话的 input/output/cacheRead/cacheWrite/reasoning/totalTokens、响应数、已知用量覆盖数、来源文件及读取错误。reasoning 已计入 output，不再次相加；totalTokens 沿用原生生产者字段。金额仅在显式传入价表后复用 ARC 估算，保留价格来源和时点，不读取凭据、查询余额或发模型请求。统计只覆盖已保存响应，进行中的请求、未落盘用量和输入目录以外的子会话仍是缺口；响应数不等于实际 HTTP 尝试数或供应商账单。

### Braid project 归档费用

`braid_usage.py` 对已下载的单份累计 project ZIP 或解压目录统计显式 native scope。它将该 scope 下全部带 session 头的原件保存到新证据目录，复用 `pi_usage.py` 的解析和去重，再按显式 ARC 价格表核算；不重复下载、不按根/Issue/PR/reviewer角色筛选，嵌套 Pi 子会话也包括。基线旧 scope、事件流和子会话转录副本不纳入。Braid sessions.json 身份与缺少原生文件的已分配会话列入覆盖说明。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tooling/scripts/braid_usage.py PROJECT.zip --scope NATIVE_SCOPE --prices ARC_PRICES.json --evidence-dir runs/usage/NEW_SNAPSHOT
```

每个累计快照使用新的证据目录，不将多档费用相加。接续继承早期历史时可用带时区的 `--since`；同一运行的重试应保留在范围内。错误响应返回的 usage 也计入，未返回/未落盘用量不补零。input/output/cacheRead/cacheWrite 分别定价；reasoning 不重复收费，未列缓存写入价且用量非零时保留 price-missing。结果 `usage.json` 包含价格/归档/原件 SHA256、模型与会话分布及缺项，金额是当前已保存用量的估算，不能当作供应商结算账单。

若接续保留原生逻辑 alias，却切换了实际文本模型，脚本自动读取同 scope 的 `native-model-substitution.json`，也可用 `--model-substitution RECEIPT.json` 显式指定。回执须保存 producer_run、applied_at、logical_text_alias 和 actual_text_model；仅将生效时间之后匹配文本 provider/alias 的响应按实际模型计价，旧历史与独立视觉 provider 保留原模型。当前替换合同的文本 provider 为 factory26，可由回执 logical_text_provider 显式指定。输出保留 logical_model、分段 producer 和映射响应数。订阅/token-plan 通道仍只作 ARC 价格比较，不推算实际订阅扣费；第二次不同模型替换须提供完整新时间边界，不能直接把累计历史按最终模板重估。

## 准备原生工具

裸 `make` 与 `make help` 只显示开发入口，不安装依赖。当前运行使用公共 Lab 的 start/status/logs/restart，参数与操作见 [Lab](../../lab/README.md)。旧 compiler 和 recipe 仅沿对应冻结执行器处理，入口见 [历史 lab.exp](../../lab/exp/README.md)。

原生工具准备不读取 variant、Corpus 或 benchmark：

```sh
make tools
python3 tooling/scripts/runtime.py path
```

工具版本与当前共用安装资源来自 `materials/npm/package-lock.json`。
Node/npm 必须已可用；按当前 agent-browser 版本使用 Node 24+。
相同 lock 复用仓库内 `runs/runtime-cache/runtime-<lock-hash>/`，`npm ci --prefix` 的安装结果也在这里；`prepare` 使用对应的 `runs/build-cache/runtime-<lock-hash>/` 保存 npm 下载、构建工具 cache 和临时目录。两者都在 WorkSSD 仓库内，Chromium 由 Playwright 安装器按 lock 配套版本缓存，agent-browser 与 Playwright Test 复用该二进制。
variant 可以选择其他显式 runtime；共享安装不决定其行为。

Pi 的包入口 `dist/bundle/cli.js` 与 `rpc-entry.js` 只导入已打补丁的独立模块入口，不执行上游 bundle chunk。冻结 runtime 时记录 launcher、独立 CLI、agent-session、扩展类型及 PBB/subagents 源的实际 SHA；补丁 stamp 覆盖这些执行依赖，不能仅用 npm 版本说明生命周期补丁已生效。
Linux 构建另收录 rg、ast-grep 与 MCPorter；这些二进制及 Node 工具由 [Linux 资源构建](../linux/README.md) 装入。I13 的服务、扩展和私有工具凭据选择见 [I13 本地说明](../../variants/pi-braid-i13/README.md#工具与技能接线)。

团队 Harness 另需 Braid 二进制与 SVC 技能集合。
使用本仓库的 `sources/braid`、`sources/svc` 源码目录；它们由 Factory26 Git 统一跟踪，不再是嵌套仓库。
技能来源与 variant 的选择边界见 [共享材料](../../materials/README.md)。
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

技能装配与许可边界见 [共享材料](../../materials/README.md)。

纯指令、角色与 skill 变化只重新装配文件，不重新安装 npm、Chrome 或 Runner。
更换真实运行依赖才重建对应资源。
Cargo/npm/Docker 负责增量复用，不另建通用构建系统。

模型配方使用现有 `--gateway-routes FILE` 参数传给 package_agent.py。打包按 catalog 解析各 deployment，写入 support/gateway-routes.json，执行是否消费该输入须按所属 variant/网关接线确认，不能由 ZIP 中有文件推断；`--provider-env` 提供私有凭据，凭据不进入公开配方。角色模型、选路输入与 run 冻结记录各有归属，不根据 catalog 的 factory26_default 重建本次实验选择。调用仍须在本轮模型授权内，参数说明不是启动请求。

## I14 源码装配

Variant main/run 要求 ready context，公共源码入口负责创建本地装配与服务，不让开发者填写内部 JSON：

```sh
python3 -B tooling/scripts/experiment_entry.py --source variants/pi-braid-i14 \
  --runtime "$RUNTIME" --skills materials/skills "$REQUIREMENTS" \
  --output-dir runs/source-generation --prepare-only
```

RUNTIME 和 REQUIREMENTS 必须是明确真实输入，输出、日志和临时文件均在 WorkSSD。e2e 还需 `--e2e-runtime`。去掉 prepare-only 会请求实际生成，须有当前模型授权；源码未发布定义不声称跨域 checkpoint 能力。正式执行使用[Lab](../../lab/README.md)，组件/私有输入分离归[制品合同](../../lab/exp/artifacts.md)。

当前公共 Pi baseline 的补丁顺序只维护在 `runtime.py::native_patch_specs`。Linux 构建临时 context 的 `apply-native-patches.sh` 由该清单生成；Dockerfile 不再维护第二份顺序。producer 在 patch 完成后写 `native_patch_order`、`native_target_sha256` 与既有锁/补丁/模块 SHA 到 `runtime-source.json`。`require_native_baseline` 用实际文件核这些字段和 retry 字节；旧 metadata 缺项会明确拒绝，不能仅补填字段把旧 runtime 当作新产物。原 vv 与 I15 的新装配采用此边界；旧 pi-minimal 保历史，不再扩展维护。

公共 Linux browser entry 保留非空 `PLAYWRIGHT_BROWSERS_PATH`，由 Playwright 自己解析兼容 revision 及特殊值 `0`。先复用该路径中已安装的兼容浏览器；仅未提供路径时选择并创建私有可写 fallback。`browser-install` 的显式安装仍使用所选路径，安装或权限错误原样保留，不偷偷切换命名空间。已有系统浏览器和显式 executable 入口仍可使用。不同 Playwright 版本不保证复用同一个已安装 revision。

### Rust 资源采集与 V8 归档

公共 Linux runtime 生产编译 `sources/resource-monitor` 并携带 `bin/factory26-resource-monitor`；公共装配/安装同时接线该制品。Python 的资源接口只负责生命周期连接与离线分析，缺少二进制时显示具体安装错误，不回退到第二套 Python 采样。当前已冻结的运行需其正常执行器统一采用新材料，本工具不主动重启它。

受登记的 Pi 自动记录 V8 分类/GC。需要分配证据时，在该执行启动前设置 `FACTORY_V8_PROFILE_SECONDS=30`，可用 `FACTORY_V8_PROFILE_EXECUTION` 限定执行 ID；不对整个应用工具树设置 Node Inspector 端口。读回归档：

```sh
python3 -B tooling/scripts/v8_profile.py /path/to/saved/managed-executions
```

输出只描述已有证据；缺 allocation profile 保留 missing，不能称未发生分配。`heapUsed` 与 PSS、`arrayBuffers` 与 `external` 分别有不同包含关系，解释见资源职责说明。
