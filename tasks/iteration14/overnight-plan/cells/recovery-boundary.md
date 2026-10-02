# 今晚无人值守：恢复边界与耗时诊断

更新时间：2026-10-02（Asia/Shanghai）。本单元只做只读诊断；没有模型请求、prepare、部署、恢复、启动、测试或源码修改。

## 结论

过去一天只有 `I13-flash-sheet` 完整评分，说明当前最紧的未知不是“再加多少并发”，而是每个候选能否在低额度条件下完成一次可追溯的生成→冻结→评分闭环。旧设施的几项根因已经被真实反馈修正，但“variant 定义、运行定义、运行数据、Braid/native 会话和应用身份”仍由不同入口分别写入；这正是热修复长、恢复时容易重新准备或错接身份的主要剩余风险。

`experiments/<name>` 与 `runs/<name>/<execution>` 的目标边界已写清：前者保存 intent/recipe/编译结果，后者保存定义消费快照、attempt、artifact、telemetry 和回执；改变定义必须新 run，恢复同一 run 沿原记录接续（[experiments/README.md](../../../experiments/README.md)）。最新 `6f40e88a` 已把 production plan、共享 cache、冻结 executor/runtime 和 `from_production` 接入 `lab.exp`，不能再笼统断言“运行定义与运行数据混在一起”。

仍有一个需要今晚明确的边界：I13/I14 的旧/variant `run.py` 仍各自复制输入、runtime、skills、profiles、Braid request 和本地 telemetry；它们是否仍是今晚入口，必须由启动命令确认。若走 `lab.exp`，这些是生产资产而不是独立 run 状态；若仍直接走 variant `run.py`，则应把它视为 legacy runner，不能把其私有 `.factory26/<timestamp>/`、`braid-state/` 或 `pi-timing.jsonl` 当作公共 `experiment/attempt` 记录。当前源码没有证据证明二者已经在同一执行中互相覆盖，因此“数据混合导致耗时”只能列为假设。普通 429 仍没有统一的客户端/网关 fallback 合同。

## 耗时与根因证据

可比较的端到端指标仍应是：完整打包请求→可交付包、启动请求→入口确认、明确热修复输入→恢复入口确认；不能用减少哈希、doctor 或一次复制代替。已有真实数字：旧/新 semantic readback 约 `56.84s→15.41s`，但缓存未控制；transport 的真实 prepared transfer 约 `103.45s`，目的 store 重入约 `27.03s`；首次大包约 `720,307,829` bytes、manifest 约 `82,086` 条目。已有 ZIP 编码局部基线 `62.45s→57.49s` 不能代表完整打包。证据入口：`tasks/experiment-dx-review/technical.md:110-116`、`tasks/experiment-dx-review/preparation.md:78-83`、`tasks/experiment-dx-review/packet.md:165-203`。

I14 启动复盘把旧设施问题与真实运行问题分开：Python 3.9 依赖失败已通过 Python 3.12 修正；e2e 首次包登记 `__pycache__` 已修正；新 runner 接管 OTLP 时遗漏 `ResourceEvidence` 曾造成 `resource-latest.json` 缺失、Braid 等待资源，后来在真实 e2e run 读到约 `0.93s` 新鲜采样、2 GiB cgroup、Pi AS unlimited 和 10 条成功 assistant。WorkSSD 约 11 GiB 不满足 12 GiB reserve，路径解析后仍落 WorkSSD，迁移到 `/Users/lanzhijiang/.codex/factory26-i14-runs/20261002` 才取得真实 e2e 模型响应。证据入口：`tasks/iteration14/dx-resume/startup-blockers.md:13-31`、`...:33` 及其中链接的原始回执。

仍会拖长恢复的边界是可消费产物和运行现场的分离：cleaner named prepared 已成功输运/verify，但旧入口会再次解压、创建 submission；reviewer 曾有完整 `/attempt/.` `docker cp` 300 秒超时，另有全量 physical inspect 30/60 秒超时；来源容器、accessor、writer volume 和僵尸 worker 必须逐项核对，不能用 `unknown` 或容器 stopped 代替停止证明。`--execute-prepared`、同 attempt export 和 legacy-source 导入虽已补入恢复材料，实际 Linux 接续和模型响应仍不能由“编译成功”推出。参见 `tasks/iteration14/dx-resume/startup-blockers.md:16-22,28-33` 以及 `tasks/experiment-dx-review/packet.md:221-233`。

## variant / run 边界判断

I13 `run.py` 在生成前直接复制 requirements、skills、runtime、Braid binary，写 `config.json`、hash、materials 和 `braid-request.json`，然后再启动 telemetry；I14 结构相同，但增加 `model-connection.json`、显式 route 和按模型拆分 provider。两者都把 `run.json` 先标为 prepared，再在同一私有流程中进入 generating。I14-e2e 对工具供应商另行读取 `E2E_MODEL/E2E_BASE_URL/E2E_API_KEY`，这是必要隔离，但没有形成跨 variant 的统一 attempt 身份投影。

因此当前最可信的身份链必须由外向内核对：`experiment definition sha → run/experiment.json → attempt_id/incarnation → frozen variant/source/runtime/material hashes → Braid run/provider_session/native session → application artifact → independent evaluation attempt`。任一段缺失，只能报告“准备/运行/应用/评分的某一阶段”，不能称完整恢复。Braid/native 会话恢复还必须满足同一 variant 冻结包、同一 provider/model/credential mode、同一 Braid session/CLI binding、同一工作树交付身份；改变供应商或模型应新 attempt/run，不能把旧 session 续接到新路由。

对“边界违反”的源码核对结果如下，当前只能确认重复装配，不能确认运行数据已经混入公共定义：

* `lab.exp.controller.build()`（`lab/exp/controller.py:208-380`）现在先发布 definition snapshot，再把 `from_production` 输入解析为共享 artifact，并通过 `environment.produce_runtimes()`/`produce_materials()` 复用 runtime 和材料；`environment.produce_materials()`（`lab/exp/environment.py:117-184`）按 dependency key 和 production-index 做跨 run 复用。这部分没有找到把 attempt 状态写回 definition 的路径。
* 仍可见的重复工作在 legacy variant 入口：I14 `native_files()`（`variants/pi-braid-i14/run.py:54-118`）每次都复制 agent template、重写 models/settings/roles、生成 launcher；I14 `generate()`（`run.py:136-205`）每次都复制 requirements/skills/Braid、写私有 `.factory26/<timestamp>/`、`braid-state` 和 `pi-timing`。I13 有同形的 `native_files()`/`generate()`，但用固定 `FACTORY26_API_KEY` 路由。这些是旧入口的重复装配/哈希/复制触发点，不等于定义与运行数据混写。
* 精确的违反只有在启动仍调用这些 legacy `run.py`、而不是 `lab.exp build/start` 时才成立：它们的私有状态没有 `lab.exp` 的 `experiment.json`/`attempt.json`/`execution.json` 合同，且 I13/I14 的模型绑定字段不同。当前提交与静态源码没有证明今晚实际命令会同时消费两套状态；这点保持“待启动命令核实”的假设。若今晚走 `lab.exp`，上述 legacy 路径不应参与；若走 legacy variant，则必须把它标记为 legacy run，不能把其私有目录当新实验 attempt。

## 429 与 fallback 判定

普通 429 是请求层故障，优先在客户端/网关边界处理：保留原始 HTTP 状态、响应正文、provider/deployment、attempt/incarnation 和 request id；如果 run 的冻结配置一开始就声明了多个允许 route，切换到其中下一条是同一 attempt 内的请求 route 事实，且客户端的逻辑 model、Braid/native session 和费用模式不变。它不应触发重新打包、重新 prepare 或热修复，前提是 runner、输入、会话和预算仍有效。

要严格区分两种情况：

* 已冻结的 fallback：recipe/production plan 已列出 route 顺序和每条 route 的 provider、wire model、endpoint、credential 引用；429 后只选择其中一条并记录 `route_attempt`，不改 attempt 的逻辑模型或材料身份。
* 未冻结的路由改动：运行中临时把 endpoint、provider、wire model、credential mode、模型预算或材料改成定义中没有的值。这不是 fallback，应保留 429 原件、封口旧 attempt，并建立新的定义/run/attempt；native session 或 CLI binding 已死亡、请求副作用未知、原预算耗尽时同样不能在原 attempt 盲切。

当前 `scripts/hackathon_gateway.py:200-253` 只按 attempt 绑定临时 token，`hackathon_gateway_compat.py` 记录 requested/normalized/failure/response；catalog 仍只选一个 deployment，没有 fallback policy、429 分类或 route 接续实现。故今晚只有在 production plan 的 route 列表已实际冻结并被启动入口消费时才能启用同-attempt fallback，否则按新 attempt 处理，不假设 gateway 自动完成。

## 今晚启动前最小必做项

1. 每个候选只冻结一份可读 recipe/run manifest：显式 case、variant commit、requirements/skills/runtime/Braid 摘要、provider/model/base URL、credential mode、fallback 顺序、预算和停止条件。把运行数据写入独立 `runs/.../attempts/<id>`，不回写定义目录。
2. 启动前做一次廉价 readback：确认 `experiment sha`、attempt/incarnation、container/host、Braid run、root provider session、Pi native session/CLI binding、模型 wire identity 和 `FACTORY26_EXP_ATTEMPT_*` 全部一致；没有完整链条则不启动。
3. fallback 只在请求层实现并保存原错；首个 429 后切到下一冻结 deployment，重试次数和总 wall budget 有界。不要在 429 后重新打包、重建 Git/native 或重启 Braid。若没有可消费的统一 fallback 接线，就宁可让该候选停在明确 blocked，避免伪造“热修复已恢复”。
4. 每题生成完成立即封口应用 artifact，再独立创建 evaluation attempt；评分失败只重试评价层。记录生成、冻结、上传、平台排队、首次请求、fallback 和评分耗时，避免把设施失败记成应用零分。
5. 运行完成后保留原始响应、退出码、provider liveness、stop/source identity 和 artifact manifest；monitor 只消费已保存摘要，不另建第二 collector。

## 两个 paused fresh baseline 的最短安全路径

这两个 baseline 有比 cleaner/reviewer 更好的接续条件：`runs/iteration14/baseline-roots-20261002/active-bindings.json` 给出了原 `experiment-live`/`experiment-flash`、`attempt_id`、container、Braid run、只读 monitor source 和 pause receipt；两项均是 `actual-model-success`，不是只有排队记录。实验定义还明确记录了 Qwen endpoint、`self_funded`、逻辑模型、视觉模型和 `FACTORY26_MODEL_BINDINGS`。因此，如果今晚使用的 route 仍是这些冻结值，且物理读回确认 paused 容器、attempt/incarnation、Braid/native CLI binding 和控制器属于同一现场，可以顺序 `resume` 原 attempt；不应重打包、重做 prepare 或创建新生成 attempt。

推荐先逐项只读 observe/readback，再顺序续 GLM、Flash（顺序只是减少同时占槽；以实际 execution 状态和输出进度决定先后，不能由模型名推断进度）。每项达到 generation terminal 后立即消费既有独立 evaluate job；不要等另一项完成。

这两个现场当前冻结的 route 是普通 Qwen：`qwen / https://maas.qianwenaiapi.com/compatible-mode/v1`，GLM/Flash 的 `model_id` 各在 `experiment-live/experiment-flash/experiment.json` 中；并非 ARC。若“接入 gateway fallback”只是给原 recipe 增加 ARK/Coding Plan/普通 DeepSeek 等未列 route，或者改变 provider、wire model、credential mode、费用或逻辑模型，不能直接 resume：先封存原 attempt 的 pause/响应原件，依据今天 production plan 重新解析并建立新 definition/run/attempt；原源若仍有写入口，先取得 source-stop/ownership 证明，再从 checkpoint/prepared artifact 恢复。

DX 交付可直接省掉的重复路径是：`lab.exp.controller.build()` 的 `_executor()` 通过 dependency key 复用 frozen executor，`environment.produce_runtimes()` 复用 controller/runner runtime，`environment.produce_materials()` 通过 `production-index` 复用 prepared/harness artifact。对已成功发布的 named prepared，恢复应消费 artifact 引用和同 attempt 的 execute-prepared/接续尾段；不要再走旧的整包解压、Git/native 重建、重新 prepare。历史上 cleaner named prepared 输运 `660.924s` 已通过公共 verify，reviewer 的 `/attempt` 复制曾有 `300s` 超时；这些是输运/归档边界，不能作为重新生成的理由。若现有 baseline 的 public runner 只支持 resume 控制而没有 execute-prepared，必须报告具体缺口，不能拿 legacy variant `run.py` 重新生成来“修复”。

## 可暂缓

可暂缓完整 controller/runner 重写、统一中心运行数据库、自动 Console 发现登记、跨宿主接管、全量 legacy 检查点修复，以及按历史分数自动选模型。这些会改变长期架构或引入新授权，今晚不能代替上面的身份/数据边界核对。variant 内部重复装配仍是长期维护问题；今晚只要把其产物显式写入 run manifest，并让 fallback/恢复消费同一 attempt 合同即可。

## 验收边界

最低真实验收不是静态编译：至少取得一个候选的启动入口确认、一个成功或原始 429 fallback 回执，以及生成→应用冻结→独立评价的完整身份链。若发生 429，证据必须能回答“是否同一 Braid/native session、是否同一 attempt、何时切换 provider、是否产生未知副作用”；回答不了就按需要新 attempt 处理。I13/I14 当前真实 e2e 与 baseline 成功回执只证明各自 run 的局部采用，不证明所有 variant 或 fallback 已验收。
