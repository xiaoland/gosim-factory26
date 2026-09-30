# I13：ARC 材料与输入目录边界实施

2026-10-01。本批开工依据为用户：“我同意你的‘现有代码也需要收回两处耦合’，而且这很关键。”对应范围是 [协作与 Requirements 方案](collaboration-requirements-plan.md) 的“泛化边界及现有内容的迁移”：迁出 I13 profile 中的 ARC 平台合同，并移除生成入口的 YAML 文件名门槛。整体 Braid 协作方法与完整需求树方法仍是后续材料工作，不纳入本批。

限定起点是 `3c7f40b9c3f2bba4d961017fcba560f480938bcf`，本批拥有的既有源码及技能索引没有起点修改。全局工作区已有大量其它任务修改，起点状态、限定源码快照、哈希及 index 差异保存在 `runs/iteration13/arc-boundary-implementation-20261001/start/`。本批只修改 `variants/pi-braid-i13/run.py`、`build.py`、`harness/skills/arc-bench/`、技能 README 及本页，不回退其它修改。

## 实际改动

`arc-bench/SKILL.md` 提供本次允许输入的理解入口、损坏或缺失材料的处理、平台合同的适用读取时点，以及产品初始状态与检查状态的区别。`references/platform-delivery.md` 保存 frontend/backend 布局、逐目录 npm 流程、Node.js 20.19.3、HOST/PORT、120 秒启动、保留目录和应用 Node 核实方法，并解释为何开发工具路径的成功不能代替平台路径。共享环境的自检沿用 portless 分配端口，3000 留给平台评测；实际检查支持对应路径与端口下的结果，不冒称固定 3000 已经部署。

I13 build 明确收录该独立技能，run 通过既有复制与 `--skill` 发现机制给主成员提供入口。root Issue description 说明本次来自 ARC Bench、输入位置及技能读取路径，不内联正文。原来读取特定文件与参考图、解释输入缺口的知识迁入技能。各 profile 不再追加平台目录、版本、npm 兼容和评测端口；pnpm、portless、应用反馈工具、角色与服务收尾规则保留。主线独立复核后，reference 对通用开发工具、资源处理和服务清理只引用运行环境约定，不复述同一做法。

`generate()` 仅确认输入路径是目录。后续继续用原有 `shutil.copytree` 复制输入、记录文件身份并传递目录，读取失败保留实际文件错误；没有增加解析器、适配接口、需求语义字段或错误包装。赛事启动参数、记录中的 `deployment='arcbench'`、应用导出、输出协议与 `delivery_ref` 保持原状。

## 实际准备与材料读取

Python 3.12 对本批 `run.py` 和 `build.py` 编译完成，编译产物和源码哈希在证据目录的 `compile.json` 与 `compiled/`。没有编写或运行 Factory/Braid/SVC 测试、smoke、probe、模拟任务或模型实验。

本次复用工具组已准备的 `runs/iteration13/tools-implementation-20261001/native-runtime`，身份为 darwin-arm64，实际工具 Node 为 v24.15.0。使用同组已经记录的 `third_party/braid/target/debug/braid` 供 prepare 复制，没有执行 Braid 会话。npm lock、运行时来源文件与实际 Braid 文件哈希记录在 `runtime-identity.json`。本批没有改依赖或 runtime，也没有重建 Linux 包；本次准备结果不代表平台 Node.js 20.19.3 或 Linux 部署已核实。

实际输入来自已有官方 compiler 浅克隆中的公开 `example/ticketbooking-demo`。原目录另含公开 tests，本批没有读取或复制它们；只将原有 `requirements.md`、`requirements.yaml` 和完整 reference 目录逐字节复制为 `allowed-example-input/`。共 9 个文件，需求中引用的图片路径均存在，来源和对应哈希保存在 `input-provenance.json`。这是真实公开示例材料的允许输入快照，没有构造 synthetic fixture，也不是参赛运行。

最终去重材料的两次准备均通过标准 `variants/pi-braid-i13/main.py --prepare-only`，exit code 为 0：

- 完整允许示例：`runs/iteration13/arc-boundary-implementation-20261001/prepared-example-final/.factory26/20261001-021933-a7a0c6ad`。
- 无 YAML 的真实 reference 图片目录：`runs/iteration13/arc-boundary-implementation-20261001/prepared-reference-no-yaml-final/.factory26/20261001-021933-d2ad8656`。该次只证明目录接入不依赖文件名，不证明完整 ARC 需求或模型能正确处理材料缺口。

最终原始命令、退出结果与日志入口归 `prepare-operations-final.json` 和 `prepare-*-final.log`；首轮 `prepared-example/`、`prepared-reference-no-yaml/` 和对应日志保留为去重前的材料，不冒称最终版本。读取最终实际 `prompt.txt`、`braid-request.json`、两份 profile、两份 launcher、十份原生角色及已复制技能后，观察到：

- root prompt 只保留 ARC 任务来源与技能路径，技能及平台 reference 正文均未内联；两份 profile 与十份角色不含迁出的 ARC 平台内容。
- 两份 launcher 都显式发现 arc-bench，全部 14 项主技能路径实际存在。复制后的两份 ARC 文件哈希与源码一致；既有工具扩展和原生角色配置未改动。
- 两次输入哈希均与真实来源一致。请求字段、profile 字段和 Pi 请求字段与工具组最终 prepare 相同，交付 ref 仍为 `refs/heads/main`，没有新增需求节点或覆盖字段。

具体最终读取结果在 `prepared-material-review-final.json`。这些反馈核实材料接线、复制与输入目录行为；没有执行模型上下文调用链、应用生成、正式启动或官网评测，因而不证明模型采用了技能或应用满足平台合同。没有重试 Exa、读取或修改凭据、push、修改 I12 或其它 variant。

主线已独立读取源码差异、两份技能及真实请求，确认迁移边界与去重材料符合范围。提交在 index 协调后仅收录本批限定文件，提交身份归同一证据目录的 `commits.json`。本批完成后，整体技能组织和知识归属由主线接续，继续扩展同一 arc-bench 技能，不创建竞争副本。
