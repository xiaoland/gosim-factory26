# 三项高收益修正的实施与验收

2026-09-23 用户最新修正：不保留针对 Factory 实现及开发基础设施的任何测试。
已删除 tests/、check_braid.py 和对应 Makefile 测试入口，开发导航已同步；下文此前的测试结果仅为历史记录，不再构成后续工作要求。
官方 benchmark、生成应用自身的验收及历史运行证据保留，不新增替代测试。


用户已确认三项修正，并授权具体方案和计划就绪后直接推进，不再重复开工确认。
本轮不提交混合工作区、不启动评分矩阵、不修改 SVC Corpus；继续本任务原有单 Agent 工作方式。
起点文件身份和原有 diff 保存于 `runs/developer-experience/before/`。

## 具体方案和次序

1. 将工具安装/构建从 profile resolver 中取出，提供不要求 SVC Corpus、benchmark 或任何 variant 的准备入口。
   复用 npm/Docker 缓存；独立 Linux runtime 可以直接提供给团队包或 raw 包，不要求先生成团队 ZIP。
2. 把四组已预演的原生配置展开为各 variant 自有材料，建立各自 run/main/build。
   四份代码独立持有行为；公共代码只处理运行资源、文件交付和原生会话归档。
   源码入口显式接受需求、输出、工具路径与技能来源，允许先 prepare-only 核实实际配置；正式包包含选定源码和材料。
3. 新包不携带公共 resolver/materializer；切断旧活动 variant 默认生成入口。
   历史结果查询、显式单核心检查、raw 实验和官网 journal 保留；旧生成器的无消费者部分退出活动路径。
4. ARC 两阶段适配器在临时提交副本中包装标准 main.py，原样转发参数并记录进程退出状态。
   判定不再依赖 raw 私有文件；原生模型/Braid 是否完成由对应 Harness 在自身退出码中表达。
   包装不读取模型参数、不解析会话、不修改原始制品；应用冻结后评测的既有约束不变。
5. Makefile 与 CONTRIBUTING 按实际修改范围给出最短检查；默认快速检查不要求忽略的上游 checkout、模型凭据或 Docker。
   运行资源、真实原生接口和 Linux 制品检查显式进入；不为 Corpus 内容编写测试。

目录与材料归属继承 independent-variants 的调查，具体依赖 lock 不强制复制四套，普通独立变更不要求重建无关工具。
当前发布版 Runner 只输出 Agent 时长，跳过评测仍部署应用；适配器自行记录标准入口进程状态比解析日志或要求所有 Harness 写 raw 格式更直接。
真实 Docker 验证复用 `arcbox-win`，不修改 Docker 全局 context、不干预其他运行。

## 验收

- 四个 variant 在没有共同 resolver 或其他 variant 的临时目录中 prepare/执行；核对原生输入与已有基线，仅允许路径布局改变。
- 只改一个 variant 的指令/代码不会改变其他源码；每个制品只装入选定实现及其明确材料。
- 成功、生成失败和中途退出的标准 Agent 入口均保留原始输出与终态；两阶段适配器无需 raw 私有状态。
- 真实现成 Pi 的技能目录/原生配置可由无模型入口读取；Linux smoke 验证工具、官方命令、交付和失败路径。
- 默认与分组检查通过，旧查看/analysis 入口仍可使用现有会话；新增测试只验证可观察的接入边界。
- 编写和实际执行新的开发命令，记录所需条件与结果；正文链接检查不能替代命令验收。

本轮不声称无模型检查证明实际模型协作或 bench 得分；真实模型验收若需执行，先核对现有授权和服务条件，不自动开启评分矩阵。

## 实施结果

三项修正的本轮落地已完成。
四个 `variants/pi-team-*` 各自持有 main/run/build、agents、observer 和浏览器接线；没有相互 import，也不依赖共同配方生成。
删除 profiles/native_profiles/batch 及全局角色、指令和模型材料，明确退出旧活动生成入口。
通用支持仅保留文件、进程、交付与原生证据操作；旧查询和显式单核心探针保留。
安装及 Linux runtime 构建归 runtime.py；团队和 raw 包均可直接消费 runtime，源码改动不要求安装完整 benchmark 或重新构建工具。

ARC 适配器对原包的临时副本添加外层标准入口，原样转发参数和输出，单独记录入口退出状态。
官方历史 `freeze-packages` 仅恢复旧生成器元数据；新官网提交显式指定平台模型，不引入解析新 Harness 内部配置的另一套逻辑。
原 journal、冻结 ZIP 和运行数据未修改。

长期开发操作归 CONTRIBUTING，AGENTS 提供入口，Makefile 按改动范围分组。
此处记录本次证据，不作为第二份操作手册。

## 已执行验收与限制

证据根目录为 `runs/developer-experience/`；`result.json` 记录最终 ZIP 身份及主要结果入口。

| 检查 | 观察结果 | 证据 |
| --- | --- | --- |
| 四组源码 prepare 与迁移前基线比对 | defaults、Braid profiles、指令哈希、models/settings 和角色文件一致，仅路径布局变化 | `check_native_inputs.py`、`native-check/result.json` |
| 四个独立临时目录入口，修改一个不影响另一个 | 无 resolver/其他 variant 也能运行；fixture 成功、失败与原生证据归档通过 | `tests-final.log` 的 independent variants 用例 |
| 默认 Python 检查 | 129 项通过，10.474 秒；无需模型、Docker 或上游 checkout | `tests-final.log` |
| 最后增加的旧矩阵入口提示、进程终止边界 | 定向检查通过；包含正常退出、非零退出和 SIGTERM，原始包未改变 | `matrix-final.log`、`arc-entry-final.log` |
| Makefile 分组与 Pi observer | harness、experiment、observer 入口实际执行通过 | `test-harness.log`、`test-experiment.log`、`observer-final.log` |
| Linux 工具直接构建 | 有 Braid 和无 Braid 两种 runtime 均导出；无 Braid 不要求 Braid 源码 | `runtime-build.log`、`native-build.log` |
| raw 直接打包 | 从 linux-native 目录生成 raw-native.zip，无团队 ZIP 前置 | `raw-package.log`；新增 directory 分支检查 |
| 官方 Runner 公开目录装配 | local_submit.py prepare-only 接受包装目录；装配后的真实入口执行并写出独立进程结果 | `runner-entry/prepare.log`、`runner-entry/official/template/.arc/adapter-agent-result.json` |
| Linux 最终混合 variant 冻结包 | Node/Pi/Braid/browser 版本入口和实际 Pi 原生配置读取通过；fixture 交付、npm build、HTTP、拒绝覆盖和失败9通过；原 ZIP 不变 | `zip-smoke-20260923-214703/` |
| 历史证据消费者 | factory show 可以查看新源码 prepared run，无解析警告 | `show-prepared.json` |
| 文档与开发 SVC 集成 | 11 份当前文档本地链接、diff 空白检查通过；SVC status healthy | `doc-links.log`、`svc-status.json` |

四个 variant 的运行边界均在宿主临时目录检查，真实 Linux runtime 和完整制品 smoke 使用 pi-team-mixed 验证一次。
Linux smoke 中原生配置读取使用真实 Pi，生成协作由明确的 Braid fixture 替代；未调用模型，未运行官方评分，不声称实际协作质量通过。
官方 Runner 检查覆盖装配与标准入口，不覆盖完整部署评测；新适配器的评分效果仍需实验验证。
原生材料比对不是 Corpus 内容测试；本轮没有添加 Corpus 内容测试或修改 Corpus。
SVC skill 的真实读取与 Corpus 方法效果仍由原任务验收，任务保持开放。
本轮没有提交；起点已保存在 before/，避免把其他并行工作混入提交。
