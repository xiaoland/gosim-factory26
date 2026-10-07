# 边界与依赖专项调查

2026-09-23，沿用户认可的“项目变更如何独立理解、验证和集成”主线继续检查。当前工作树有其他任务的变更，本记录描述本轮所读实现。只读产品源码；有界复现使用 `python3 -B` 和进程内 mock，没有修改来源仓库、启动模型、构建制品或运行 benchmark。

## 判断依据

对每条依赖检查：消费者需要什么事实或能力、谁决定这些事实、消费者实际读取哪些输入、输入如何取得及冻结、检查是否覆盖双方真实可观察的约定。用具体变更判断影响是否合理，不能从 import 数量、文件长度或目录名称直接判断架构好坏。

开发设施需要回答的仍是：改什么组件，应该牵动哪些消费者，最小验证需要什么条件。下面的实验设施问题只是这一检查方法在某类组件上的结果。

## 实际依赖图

```text
任务/批次入口
  └─ profiles.configuration
       ├─ profiles.resolve → 选定 profile、角色、技能、模型、npm 锁、SVC Corpus
       └─ experiments/multi-agent-lite.json → 允许任务、部署方式、benchmark 版本

package_agent → profiles.configuration → 上述特定批次
package_agent → Braid 源码 + npm runtime → Factory ZIP
package_raw_core → 已存在的 Factory ZIP/runtime → raw Pi/Codex ZIP

Factory.generate ↔ submission（环境、平台配置、应用交付验证）
Factory.generate → Braid 请求/交付 + native_profiles → 当前工作树选择的 runtime

local_experiment → argv / 结果文件 + otlp_store
arc_matrix → arc_bench_adapter → 官方 local Runner
arc_bench_adapter 的两阶段生成判定 → raw 壳私有 entry-result.json

部分 Factory 测试 → sources/svc/corpus
跨 Braid defaults 的测试 → sources/braid/src/config.rs 的 Rust 文本
```

这张图混合代码调用和文件读取，旨在显示真实边界。问题在下列具体边中，并非所有依赖都应删除。

## 发现及开发影响

### BD-01：一次实验的选择反向约束 Harness 配置和打包

[profiles.configuration](../../scripts/profiles.py) 第 152–162 行始终读取 `experiments/multi-agent-lite.json`，用其 tasks 验证任务，再取 deployment、benchmark URL/revision。[package_agent.package](../../tooling/scripts/package_agent.py) 第 112 行也走此路径，默认 task 为 keep；构建参赛 Agent 本来不需要选中某道题。[batch.execute](../../scripts/batch.py) 虽接受 manifest 参数，却仍调用读取固定 manifest 的 configuration，且硬编码 4 variants × 2 tasks、generation_workers ≤ 2。

内存复现：只把固定 manifest 返回的 tasks 改成 `['bookstack']`，默认 configuration 即报 `task not selected for this batch: keep`。因此调整某轮实验，会阻断共享配置乃至打包路径。固定批次脚本本身可以有固定范围；不合理的是其选择成为其他消费者的隐藏前提。

候选纠正：能力装配只处理 Harness 输入；实验入口组合题目、benchmark 和运行选择。保留固定批次时明确其专用身份，不把它作为通用配置来源。

### BD-02：应用生成与宿主/参赛接入的组合责任交叉

[factory.generate](../../scripts/factory.py) 第 327–342 行只在 `runtime=submission` 时允许外部 requirements；普通本地调用必须读取固定 `third_party/arc-bench`，并检查整个 benchmark checkout。Factory 的环境与 adapter 分支又反向 import [submission](../../scripts/submission.py)，submission.main 同时调用 factory.generate、load_config 等。

因此验证“给一份小需求生成应用”也会牵涉 benchmark 或伪装成参赛包；改变宿主入口容易波及生成核心。循环 import 是症状，实际问题是生成能力内部决定调用方的输入来源和平台环境。

候选纠正：本地命令和参赛入口各自准备明确需求、运行资源与交付约束，再调用共同生成能力。先移动现有责任和参数；当前证据不支持增加插件框架或通用依赖注入系统。

### BD-03：证据快照被同时用作过宽的构建依赖

[sources.snapshot](../../tooling/scripts/sources.py) 第 18–26 行记录整个独立仓库的 tracked/untracked 非忽略文件；require_build 第 68 行比较整份 snapshot，相同源码、不同文档也拒绝运行。完整来源快照有证据价值，但不能据此认定每个文件都影响二进制。

内存复现：记录与现状只有 `docs/notes.md` 的摘要不同，源码和 artifact 摘要相同，require_build 仍报 `braid source changed; run bootstrap before generation`。这里证明的是生成被阻断并要求 bootstrap；没有测量 Cargo 是否实际重新编译或耗时。

另一处是 [profiles.resolve](../../scripts/profiles.py) 第 78–81、135–140 行把完整 npm lock 放入每个 Pi profile 的有效摘要；[native_profiles.runtime_cache](../../scripts/native_profiles.py) 第 19–24 行也用它选整套缓存。内存中只改 Codex lock 条目的 version，两个 Pi profile 的摘要和缓存路径均改变，Pi core_version 不变。共享锁本身可以合理，但能力身份、实际打包内容和缓存失效范围现在没有清楚区分。Pi 包构建后又删除 Codex，见 [submission/build.py](../../tooling/linux/build.py) 第 16–22 行。

候选纠正：区分来源证据、真实构建输入和运行制品身份；首先缩小明显无关的失效范围。是否拆 npm 包或缓存要依据安装成本与实际消费关系决定，不预先建设通用构建图。

### BD-04：冻结声明与实际资源选择没有沿同一条路径传递

resolve 保存 `common.npm_sha256` 和 core_version，但 materialize 不使用这些值选择 runtime，而在 [native_profiles.py](../../scripts/native_profiles.py) 第 82–85、148 行重新从当前 ROOT 的 lock 和缓存定位可执行文件。全仓搜索未发现 npm_sha256 在解析之外的执行校验消费者。已解析配置与工作树锁发生变化时，声明身份与实际资源可以分离；本轮没有声称现存实验已发生这种错配。

SVC 也存在两种合同：variant 声明 source_revision，resolve 只检验格式并读取当前 sources/svc/corpus；本地 generate 另外归档实际来源而不比较声明 revision；package_agent.capability_manifest 则强制比较两者。内存复现中把声明改成 40 个零，本地 configuration 接受，而包能力校验拒绝。

候选纠正：先明确声明表示必须使用的 revision，还是开发工作树的基线；本地与打包遵守同一解释。允许未提交源码开发时记录实际材料，不用强制提交代替身份。运行资源由一次解析所得的输入传到消费者，避免执行中另读工作树默认值。

### BD-05：运行时基础依赖要经过完整产品和历史制品才能取得

[package_raw_core](../../tooling/scripts/package_raw_core.py) 第 15–29、41–43 行要求已存在的 Factory ZIP，复制其全部 runtime；当前 package_agent 又依赖 profile resolver，而 resolver 第 88 行只接受 Pi。由此 raw Codex 有消费历史 ZIP 的路径，却没有通过当前受维护打包入口从声明源码重建该来源的闭合路径。不能从这一事实推断历史 ZIP 已不可用，也不否认手工 Docker 构建的可能性。

开发环境也有未闭合的取得边：开发 SVC `.venv/bin/svc` 的准备未由项目 bootstrap 承担；sources 被父仓库忽略；当前 bootstrap 只会补 Braid，而解析所需 SVC Corpus 要事先存在。Braid 缺失时 clone main，尚无相应固定来源选择。不能用本机目录已存在来证明重建路径完整。

候选纠正：原生 runtime 有独立的受维护构建入口，Factory 和 raw 包消费它；开发依赖准备直接说明来源、版本和必要步骤。复用已有 Docker 构建能力，不引入制品服务作为前提。

### BD-06：有些检查依赖上游的源码写法，且检查条件与开发问题不匹配

[test_profiles](../../tests/test_profiles.py) 第 54–59 行用正则从 Braid 的 `src/config.rs` 提取 Rust struct 字段，作为 JSON 请求合同检查。上游移动类型或改变布局会影响 Factory 检查；仅比较 Rust 字段名也不能验证 serde 映射和实际请求接受行为。这个测试还要求忽略目录中的上游源码存在。

部分装配测试直接 resolve 仓库真实 profiles，因而需要 sources/svc/corpus；同一文件已经有 synthetic Corpus fixture，说明纯装配逻辑可以用较少条件验证。Makefile 只提供聚合入口，没有把纯本仓逻辑检查、上游合同检查、打包检查与真实模型探针的适用边界说清楚。

`check_braid.py`（现已删除） 使用无 effective 的旧 config 和宿主 PATH 的 native CLI，而默认生成使用 mixed effective 配置和锁定缓存。内存读取证实两者 model/variant/effective 均不同。不过文档已明确该检查是“不装载技能”的受控上下文探针，因此差异本身不是 bug，更不能要求它承担完整 Harness 验收；需要显式说明它支持什么结论，以及修改装配时另需哪项检查。`submission_smoke.py`（现已删除） 已覆盖部分包内 materialize，后续应复用而非宣称没有集成检查。

候选纠正：普通逻辑检查使用其真实最小输入；跨仓库检查验证公开请求/输出；现有探针保留其有价值的受控范围。检查入口和开发说明将变更类型映射到必要检查，不按所有改动一律跑全矩阵。

### BD-07：替换 Harness 时，bench 适配和证据消费仍会牵连具体实现

[arc_bench_adapter](../../scripts/arc_bench_adapter.py) 第 90–110 行的两阶段模式只接受 `.arc/raw/entry-result.json`。符合平台入口、但采用 Factory 自有交付证据的包会被该路径判为未完成；这属于两阶段适配器的 raw 依赖，不是整个 local_experiment 都依赖 Factory。后者目前只消费 argv、结果和 OTLP，是应保留的合理边界。

旧 run_feedback、inspect_runs、viewer 与新 local_experiment 的发现路径和状态形状不一致，见 [首轮调查 DX-07](inquiry.md)。运行记录的生产者、读者和代际没有明确选择路径，Agent 需要先知道历史实现才能查询结果。

候选纠正：平台适配器依据其公开生成结果合同判断；确需 native 终态时由对应 Harness 适配边界提供，而不是在通用路径猜私有文件。历史证据读取与当前执行分别明确支持范围，保留需要的读者不等于继续维护旧执行器。

### BD-08：旧实现仍提供活动默认，信息与代码都缺少退出边界

默认 load_config 选择 pi-team-mixed；`variants/factory/config.json` 仍被受控 Braid 探针、concurrency 默认探针和旧接入路径读取。README 仍推荐已不存在的四 variants；运行文档第 214 行仍称 factory/config 是唯一活动配置；PRD 的持续验收又链接某个任务方案。这些描述会使 Coding Agent 将一次实验或兼容入口解释为长期权威。

[native_profiles.materialize](../../scripts/native_profiles.py) 第 149–168 行还保留 Codex 分支，但当前唯一生产调用链的 resolver 不接受 Codex profile；materialize 自身先要求 Pi 可执行文件，并给 pi/codex 填同一个 core_version。这是目前不可由正常配置抵达的能力形状，不应让它暗示已经支持 Codex profiles。旧显式单核心运行与 raw Codex 是另外的消费者，不能因此一并删除。

候选纠正：对每项旧入口确认活动消费者，再选择明确受限用途、迁移或退出。长期文档撤下旧默认，历史报告保持其原有条件。当前未授权删除实现或数据。

## 应保留的边界与未下结论的部分

local_experiment 与 otlp_store 没有导入具体 Factory Harness，继续保留通用执行和原始数据存储边界。Braid 交付检查验证请求身份、所属仓库和不可变 commit，再从该 commit 导出应用；这是正确的跨组件校验。运行时 Agent 与开发侧 SVC 已在当前源码改为 skill/CLI 分工，不再把之前的 runtime CLI 情况当作现状。

两个 model catalog 服务 Factory 和 raw，推理选择不同可以是实验设计；不能仅因字段重复就认定参数应完全合并。多处短小 JSON/hash helper 也不是本轮优先问题。网站相关入口仅搜索了本地消费者，未访问或操作网站。未深查 Braid/SVC 内部架构、全部 upstream API、真实平台协议或全量历史运行；本轮结论限于 Factory 消费这些边界的方式。

## 设计讨论的下一步

### 主会话接手后的定向核实

2026-09-23，当前主 Agent 读取现有调查并对照当前入口，没有重新运行以上内存复现，也未启动 Runner 或模型。
Makefile 仍只有 `bootstrap/test/run` 三个聚合入口，其中 bootstrap/run 指向共同 factory 入口；没有 CONTRIBUTING 开发说明。
这支持“开发路径仍需理解共同生成链”的判断，但不能仅由入口数量推导需要增加多少命令。

本地发布版 Runner 位于 `../factory26-official-local/runner`。
其 `local_submit.py` 的 `--agent` 明确接受 ZIP 或已展开目录，`validate_agent_entrypoint` 只检查 main.py 与 requirements.txt 两个入口文件。
因此开发验证无需先压缩 ZIP，不需要另写一个 Runner 来获得目录输入能力；依赖与真实执行条件仍需分别准备。

同一文件的 `read_result` 在 `evaluation_enabled=false` 时读取公开的 local-run.json 和 `.arc/agent-execution.json`，输出 `evaluation_status=skipped` 与 container_exit_code。
但 `local_runner.py:install_optional_evaluation_contract` 跳过的是评测，仍有应用部署阶段。
因此 container_exit_code 不能不加区分地当作 Agent 生成是否完成；还需核实生产执行层对 Agent 终态的记录，才能替换 adapter 当前的 raw 私有结果依赖。
本轮不据文件名猜字段，也没有据这项静态阅读宣称接口验收通过。

上述发现已纳入 design：目录运行是现有平台能力，公开生成终态仍是具体待核实边界；二者不应混成重新建设通用 Harness 框架的理由。

优先明确 Harness 装配、原生 runtime 构建与实验选择三者的输入归属，然后才能决定开发入口准备哪些依赖、运行哪些检查。用四个反例检验边界：改变一轮题目选择不影响 Agent 打包；修改 Braid 文档不要求生成重建；已解析的运行选择不随工作树锁改变；调整上游内部源码布局不影响稳定公开请求的检查。

这些是设计候选和调查判据，尚非实施方案或已通过的系统验收。无需先搬目录、拆仓库、添加服务或给所有模块创建接口。
