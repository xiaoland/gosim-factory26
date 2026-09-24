# 运行与迁移方案

状态：总体边界已获用户认可；本文件细化具体实现，待与验收和预演结果一起复核。
依据为当前未提交工作树，不以 Git HEAD 冒充 SVC skill 接线后的基线。

## Variant 的实际形状

以 mixed 为首个迁移对象，建议目录如下；其他三份分别持有完整文件，不 import mixed。

```text
variants/pi-team-mixed/
├── main.py             官方命令入口，调用本目录 run.py
├── run.py              需求、原生环境、Braid 调用、交付与失败收尾
├── build.py            本 variant 的材料选择及打包步骤
├── instructions/       根任务与各协作者指令
├── agents/             各 assignee 的 Pi models/settings、子代理 Markdown
├── extensions/         本 variant 使用的 Pi 扩展
└── npm/                本 variant 的 package.json 与 lock
```

原生子代理文件使用 Pi 扩展实际消费的 frontmatter，直接声明 model、thinking、tools、skills、inheritSkills 等。
models.json 使用 Pi 原生 provider/model 描述；run.py 只补充本次 URL、路径等运行值。
各 assignee 的 Braid profile/binding 由本目录 run.py 直接构造，使用现有 Braid API，不经过 Factory effective profile。
启动参数、浏览器 wrapper 和上下文行为均由本目录持有。
预演确认主 launcher 显式关闭自动发现后加载 pi-subagents、observer 和主 skills；子代理通过自己的 skillPath/skills 选择材料。
迁移必须一并重绑定这些路径与 Chromium/browser wrapper，不能只搬主指令；详细事实见 [预演](rehearsal.md)。
四份目录初期允许相同代码，不引入 base variant、继承或能力注册器。

CLI 保持官方形状：`python main.py REQUIREMENTS_DIR --output-dir OUTPUT [--type web]`。
开发运行同样消费需求目录、输出目录及明确准备的依赖，不能凭 task slug 去读评测仓库。
调用链是 `variant/main.py → variant/run.py → braid local`，模型由 Pi 原生接口访问。
生成阶段不启动 Runner、不读取测试；评分仍由外部设施在冻结后执行。

每次 invocation 创建一个根 Issue；LLM 拥有分工语义，Braid 持有 work-item/session，Pi 持有自己的 sub-agents。
本次不改变上述生命周期、不修改 Braid/Pi，不增加调度器或停止协议。
运行环境、技能发现和选用角色保持当前行为，不增加沙箱。

## 从现有实现搬什么

| 当前职责 | 新位置或处理 |
| --- | --- |
| `profiles.resolve` 的角色、指令、模型与技能选择 | 一次性展开后人工核对，保存为各 variant 直接消费的材料；不保留持续生成四份源码的程序。 |
| `native_profiles.materialize` 的 Pi 启动与角色模板构造 | 改成各 variant 的直接原生配置与局部路径填充；删除不适用于该 variant 的 Codex 分支。 |
| `factory.generate` 中 Pi+Braid 的需求 prompt、环境、Braid request、执行、交付选择 | 迁入各 variant/run.py，去掉本地/平台及 single/Codex 的条件分支。 |
| `core.archive_sessions`、Braid 状态归档和 Git commit 导出 | 继续复用现有机械性证据/文件操作；作为普通支持模块复制进制品，不经通用生成函数。 |
| `submission` 的官方 CLI 参数、应用检查、输出保留规则 | CLI 与调用顺序由 variant 入口持有；单纯的文件检查/复制可共用。公共模块不导入 factory.generate 或决定模型。 |
| `factory.py analyze/list/show/eval`、viewer、feedback | 保留开发与历史结果入口；新生成物继续产出已有消费者实际读取的文件。 |

公共支持代码不得读取 variant 名称来选择流程，也不得持有开始/设计/实施/验收等语义调度。
优先搬动已有函数，不借迁移重写会话归档或应用交付协议。
`core.py` 内的 Codex transport 与 raw-core 基线继续保留，不为四份 Pi variant 重做 Codex 接入。

生成过程保留 Braid 的 result、sessions 与原生 JSONL；非零退出保留工作现场、原始错误和退出码，不输出成功交付。
成功时从既有 delivery commit 导出应用，再按官方布局交付；不把失败现场当冻结成品。
诊断收集不拥有完成判定，不能用辅助记录缺失覆盖主失败原因。

## 打包与依赖

保留 `scripts/package_agent.py --variant ... --output ... --docker-context ...` 作为开发者选择入口；它仅派发到所选目录的 build.py。
build.py 自己选择本 variant 的材料、依赖和 SVC skill，再调用现有 Docker 构建及 ZIP 写入操作。
公共封装只接收文件与依赖输入，不读取角色或推导 skill。
ZIP 根目录包含所选 main.py/run.py、对应材料、普通支持模块和 runtime，不复制整个 harness，也不含其他 variant。

npm lock 由各 variant 持有；相同 lock 复用已有缓存/Docker layer。
Docker build context 中只放 runtime 构建真正读取的 lock、Braid 构建源码及构建脚本，纯 prompt/skill 改动不让 npm、Chromium 或 Rust 重装。
当前四份从同一个 runtime 输入起步，不在本任务升级依赖或增加依赖管理框架。
现有 `submission/build.py` 已在 Pi 制品阶段移除 Codex 二进制包；沿用这一既有打包行为，不在本任务进一步裁剪依赖。
官方格式验收沿用现有可用 Docker context；不额外搭建 Linux 隔离环境。

SVC 正文仍来自 `sources/svc/corpus`；每份 build.py 明确把所选 skill 及正文复制进本次制品。
不维护四份 Corpus 上游，也不让运行时读可变 checkout。
构建后记录实际文件及其哈希、依赖来源；继续使用现有 package-manifest 的 files/backend/sources，raw runtime 提取仍能读取。
不再生成 `variants/factory/config.json` 或整棵 effective profile。
新制品身份直接记录 variant；如需官网提交，提交 manifest 显式给出主模型和视觉模型路由，运行时不从该元数据生成 Harness。

历史 `official_matrix.execute` 使用已经冻结的 matrix manifest，因此不需要修改旧 ZIP/config 或 journal。
`official_matrix.freeze` 是旧 ZIP 格式的派生工具；本任务不增加新旧 profile 双解析，文档明确它只适用于历史格式。
新制品使用当前 ZIP 输入的 Runner 通路，新的官网上传协议并非本任务交付。

## 诊断连续性与旧入口

详见 [消费者核实](evidence-contract.md)。
本次保留 `.factory26/<run-id>/` 内的 run.json、prompt.txt、braid-state、native/manifest.json、会话文件、application-hashes 和 delivery.json。
config.json 仅保留现有 viewer 使用的身份摘要，不再作为生成输入，也不保留 effective-config.json。
model/role/skill 的实际生效状态从归档原生配置及 Braid request 查询；不能为了删 effective 而丢失定位材料。

现有 viewer 的默认发现范围与新的 local_experiment 嵌套目录并不完全一致。
本任务保证能对实际证据目录执行 `show --run`/`analyze --run`；默认聚合发现、OTLP 语义改进归 [开发设施任务](../developer-experience/packet.md)，不把旧设施缺口藏成迁移已通过。
本次不新增 OTLP exporter；现有原始会话归档继续是主要依据。

旧 `factory.py` 的显式单核心/检查配置、Playground 历史工具以及 `check_braid.py` 有独立消费者，不整体删除 factory.py 或 legacy config。
活动 variant 的旧 `generate/run/bootstrap/batch` 配方入口应停止使用 resolver，并给出新的打包与 Runner 命令，而不是偷偷继续生成另一套同名 Harness。
删除失去消费者的 profiles.py/native_profiles.py 与全局 profiles/subagents 选择层；旧单核心检查保留自己的直接 Braid request 路径。
旧 batch 文件和冻结输入不改写，历史实验仍可查询；不承诺用新实现续跑旧本地生成进程。

## 变更边界

主要触及四份 variants、打包和薄平台支持、旧活动配方入口、相应边界测试及运行文档。
不修改 SVC Corpus、Braid/Pi 源码、官方 Runner、历史制品/journal、raw-core 模型设置和实验成绩。
当前工作区有并行任务改动；实施仅操作本任务必要部分，提交需要明确授权，不能直接提交整个工作区。
