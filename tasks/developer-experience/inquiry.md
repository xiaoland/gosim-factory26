# 开发路径调查

## 范围与证据边界

2026-09-23 在 `/Volumes/WorkSSD/Development/factory26` 当前工作树进行只读审查。工作树有其他任务的未提交变更；本文描述当时观察，实施前应重核受影响代码。未修改产品源码、运行正式 benchmark、调用真实模型、操作主线程进程或启动子 Agent。

检查覆盖 README、AGENTS、长期产品与运行文档、SVC 配置、Makefile、配置解析、环境构建、打包、实验控制、ARC 适配、OTLP、反馈/viewer 和相关测试。未穷尽每个模块，未执行全套测试或完整新机安装。调查中的内存模拟和静态推导不得写成真实部署验收。

首轮按理解项目、准备环境、修改、验证、运行、诊断、交接与维护等场景寻找断点。这些是调查用例，不构成相同层次的架构分类。2026-09-23 用户明确本项目开发者只有 Coding Agent，README 面向项目用户，开发入口以 AGENTS.md 为主、开发说明归 CONTRIBUTING 等开发文档。后续设计以此为前提。

主要判断维度为理解成本、首次有效反馈时间、反馈可信度、环境可复现性、变更影响范围及历史知识生命周期。此前以 README 命令失效发现的文档漂移仍是事实，但不能据此推导应让 README 承担开发入口。

## 边界与依赖的扩展调查

用户认可按项目变更梳理工程边界，要求沿边界与依赖扩大排查。本轮的调用/文件读取图、八组问题、内存复现与候选纠正归 [边界调查](boundaries.md)。它补充首轮症状，重点区分事实归属、真实依赖、冻结资源的传递和验证边界，不将组件目录或 import 数量作为判断标准。

主线程同期已将参赛 SVC 改为 skill 材料，当前不安装 runtime SVC CLI。下表保留首轮观察；DX-02/03 中关于旧 bootstrap 构建 SVC 的描述不再代表当前实现。当前路径要求事先存在 sources/svc/corpus，bootstrap 只会补 Braid，开发 `.venv/bin/svc` 的准备仍未闭合。

## 已确认的问题

| 编号 | 观察与证据 | 对开发者的影响 | 证据等级 |
| --- | --- | --- | --- |
| DX-01 | [README](../../README.md) 推荐 pi-generalist、codex-generalist、pi-team、pi-verification；当前只有另外四个团队 variants。直接调用 `factory.load_config(variant=...)`，上述四项均 FileNotFoundError。运行文档“单一 Harness 与 WSL 评测”又把共同配置称为唯一活动配置。 | 当前入口和实际默认不一致，用户必须读源码与历史判断。 | 实际解析复现、文档对照。 |
| DX-02 | [factory.py](../../scripts/factory.py) 在 bootstrap 前调用 load_config；[profiles.py](../../scripts/profiles.py) 必须先读取 sources/svc/corpus；[sources.py](../../scripts/sources.py) 的 clone 在后续 bootstrap 才发生。内存模拟缺少该来源时退出 2，bootstrap 未被调用。 | 首次安装存在依赖顺序闭环，已有机器会掩盖问题。 | 缺失条件的内存模拟；未做新机器安装。 |
| DX-03 | 文档指定开发 `.venv/bin/svc`；bootstrap 创建的是 `.bootstrap/svc-runtime` 或 `.adapter`，未提供开发 SVC 的装配步骤。sources 缺失时 clone main，variant 又声明固定 SVC revision。 | 机器现状与受维护的重建路径脱节。 | 已读入口和构建实现；未量化跨机器差异。 |
| DX-04 | [concurrency.py](../../scripts/concurrency.py) 把所有 429 设为 rate_limited，读取后不保存错误响应正文。请求只带 model/messages/stream，不带所配置的 reasoning 参数，只允许并发 2 或 4。 | 原因被丢失且分类误导；普通请求成功不能证明实际推理配置或持续吞吐。 | 代码路径确认；本专项未发送真实请求。 |
| DX-05 | [raw_otlp.py](../../submission/raw_otlp.py) 的 ScopeLogs.scope 写入裸字符串；捕获当前编码输出并按官方 schema 做内存解码，发现长度越界。 | 字节持久化成功无法保证下游标准工具可消费。 | 当前生产函数输出的独立结构检查。 |
| DX-06 | [test_raw_baseline.py](../../tests/test_raw_baseline.py) 只断言批次数、字节包含 tool_call，不解码 OTLP。Makefile 未运行文档命令或冷启动检查；本轮本地文件链接检查无断链，README 命令仍失败。 | 检查通过与开发者承诺之间缺乏对应关系。 | 测试边界和入口复核；未据测试数量评价质量。 |
| DX-07 | [local_experiment.py](../../scripts/local_experiment.py) 用 phase 存终态；[run_feedback.py](../../scripts/run_feedback.py) 主要按旧 status/outcome 解析。新 completed 状态输入返回 status=unknown。viewer 只扫描仓库 runs 根下的旧生产者布局，未接入同级新设施结果。 | 用户需先知道设施代际，才能选对查询入口。 | 解析函数内存复现、发现路径静态检查。 |
| DX-08 | profiles.configuration 用特定 [multi-agent-lite.json](../../experiments/multi-agent-lite.json) 决定允许任务；ARC 两阶段适配硬编码 `.arc/raw/entry-result.json`。 | 实验选择与通用配置耦合；生成结果判定依赖具体 raw 壳。 | 调用路径确认。 |
| DX-09 | [package_raw_core.py](../../scripts/package_raw_core.py) 必须从已有 Factory ZIP 提取 runtime；当前 package_agent 走只接受 Pi core 的 profile resolver。raw Codex 依赖历史 ZIP，当前入口未闭合其源码重建路径。 | 制品即使有哈希，也不等于能够从当前声明的输入重建。 | 当前构建入口检查；未断言历史 ZIP 已损坏或不可用。 |
| DX-10 | local_experiment 先为全矩阵串行 copytree/copy2 和哈希，再打印 queued 并启动 pool。四个 api-v4 ZIP 约 91.6/91.6/331.8/331.8 MiB，八题副本约 6.61 GiB。 | 首次反馈前存在重复准备成本，workers 只作用于后续执行。 | 文件大小与控制流确认；尚未测量时间瓶颈。 |
| DX-11 | PRD 保存某轮活动矩阵及 task 验收链接；同级 factory26-official-local README 仍宣称生产 Runner 未公开，并指向旧模拟器。 | 长期行为、当前实验与历史材料具有相互矛盾的“当前”表述。 | 本地文档对照；不从 packet 数量推断每个任务都已过期。 |

### 有界复现记录

README 解析检查：使用 `python3 -B` 导入 scripts/factory.py，依次调用四个 README variant 的 load_config，全部因不存在的 variant.json 失败。实际 `profiles.DEFAULT_VARIANT` 为 pi-team-mixed。

冷启动检查：仅在当前 Python 进程中包装 `Path.read_bytes`，对包含 `/sources/` 的路径抛出 FileNotFoundError，并 mock `factory.bootstrap`；调用 argv 为 `factory.py bootstrap` 的 main。输出指向缺失的 `sources/svc/corpus/index.md`，SystemExit.code=2，bootstrap.called=False。没有删除或移动真实 sources。

反馈检查：对不存在的只读路径调用 `run_feedback._outcome`，传入 `schema_version=1, phase=completed, result.status=completed`。返回 `status=unknown, stage=completed, scope=generation`。

OTLP 检查：在内存中 mock raw_otlp.urlopen，调用 LogExporter.add 和 flush 捕获 Request.data，沿 resource_logs=1 → scope_logs=2 → scope=1 解码 length-delimited 字段。147 字节样本中的 scope 内容是 `b'raw-core-wrapper'`；把它按 message 解析得到 `field 14 needs 97 bytes, only 14 remain`。规范要求 scope 为 InstrumentationScope，其中 name 才是字符串，见 [官方 logs.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/logs/v1/logs.proto) 与 [common.proto](https://github.com/open-telemetry/opentelemetry-proto/blob/main/opentelemetry/proto/common/v1/common.proto)。未逐一解码历史已存批次，原始 events.jsonl 仍可另行分析。

入口链接检查：扫描 README.md、AGENTS.md 和 docs 下 Markdown 的本地文件链接，不检查外网可用性和页内锚点；未发现缺失目标。这个结果不能用来判定文档语义一致。

## 根因判断与待区分因素

目前最有解释力的判断是：组件存在，但跨组件的开发者路径没有明确维护者、版本边界和可执行验收；历史任务中的选择逐渐进入默认入口，用户或 Agent 负责临时组合。此判断解释多处断点，但不是对所有模块质量的判定。

需要保留并复用的能力包括输入与产物身份、冻结后评测、独立 run 目录、并发执行、原始日志、通用 OTLP 批次保存及若干故障边界测试。具体错误优先在所属边界修复，不据此推导必须重写整个平台。

后续设计仍需核对：开发者是否需要跨主机运行的当前支持范围；官方输入与原生 runtime 的可重新获取方式；新旧运行读取最小兼容面；哪些准备开销确实影响首次反馈；冷启动基线应固定哪些外部工具。上述问题先通过仓库与环境事实缩小，再向用户提出必要的产品选择。
