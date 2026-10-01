# I13 实验前最终检查

2026-10-01。用户要求：“现在 I13 的内容似乎做得差不多了，我们最终进行一次检查，为开始实验做好准备。”本次核对当前源码、实际装配、既有实施回执与运行前提，不启动模型、生成、评分或 I12，不修改历史归档。检查中用户先要求 GLM-5.3 使用 Qwen，并配置凭据；随后明确“情况有变化，可以回去用ARC了，因为有新增的额度”，最终确认“全部切回 ARC，包括 GLM-5.3”。最终配方因此全部使用 ARC 通道，Qwen 发现结果只保留为历史反馈，不实施其路由。

当前判断是：I13 各实现批次可以进入最终实验准备，但尚不能直接启动两组对照。剩余主要是根对照配方、ARC 完整模型供给与实验宿主，不需要把全部尚未观察的模型行为变成新的开发批次。恢复 ARC 模型通道不自动改变实验场所；沿用本地生成和 Console 人工介入，除非用户另选官网生成。

## 本轮实际核对

原始材料在 `runs/iteration13/final-readiness-20261001/`。Factory、Braid、SVC 均有历史 dirty，来源以该目录的身份记录、实际文件及构建输入为准，不能只写三个 HEAD。当时 Factory 为 `12d7f5c`、Braid 为 `76747f2`、SVC 为 `a0af6e1`；Bub 与 Console 的独立成果不因此变成 I13 的实验变量。

- 当前 Braid `cargo build --locked` 成功，保留已有编译警告；本次相关 34 份 Python 文件编译成功。没有运行 Factory/Braid/Corpus 测试或创建替代探针。
- 从项目保存的官方 GitHub、Sheet 允许需求目录分别执行当前 I13 的 `--prepare-only`，输入分别有 28、10 个文件。最终材料包含两份主 profile、十份内部角色及 15 项独立技能；68 份技能文件与当前来源一致。根仍为 `pi-glm-fast / glm-5.3-flash`。初次装配与编译重叠，取得旧 binary；身份读回发现后已保留该记录，并在编译完成后重新装配。最终两份材料的 binary 均与本轮编译产物一致。
- 工具批次旧 Linux runtime 的 npm lock 和八份补丁仍与当前源码一致，但 Braid source hash 已不同，旧工具 ZIP 不能作为最终 I13 包。本轮重建 Linux runtime 成功，源码 hash、lock 和八份补丁均与当前来源一致；无凭据候选 ZIP 为 393332274 字节，SHA256 `da960a47b96f90fc304a712e37b0b7752306ab39000a5008d9f088b32adc347c`，包含 24210 项载荷。通过网络关闭的 Linux/amd64、CPython 3.12 容器实际解包，GitHub、Sheet 的包内入口均完成载荷核验和 `prepare-only`；没有模型、应用生成或评分，操作后移除本次临时容器。完整请求、角色、技能与二进制身份在 `linux-prepared-materials.json`。
- Qwen 配置文件权限为 `0600`。使用该地址和凭据查询 `GET /models` 得到 HTTP 200，261 项模型中含精确 `glm-5.3`；没有改用 `glm-5.3-prime`。首次 Python 默认 CA 查询失败，改用系统 `/etc/ssl/cert.pem` 后成功，证书验证始终开启。模型清单不证明生成参数、流式或工具调用已通过。
- 最终改回 ARC 后，用既有官网凭据读取 `https://api.arc-bench.com/v1/models`，HTTP 200 的 16 项模型包含本配方所需 `glm-5.3`、`glm-5.3-flash`、`deepseek-v4-flash`、`kimi-k3`。现有 `base_url` 和 visual 默认共用入口可以承接 ARC，不需要新增 Qwen 网关映射。`/auth/me` 读取成功但不返回余额字段；新增额度目前是用户报告，没有将旧余额或模型清单冒称当前剩余金额。没有发起 Chat 或生成请求。
- 检查起点 `.env.i13-tools` 仍是原 key；随后用户明确已修正 Exa，本轮通过当前 Pi SDK 装载真实扩展并调用 `exa_search`、`exa_contents`，两者均 HTTP 200，检索和正文结果及 request ID 保存在 `exa/`，未调用模型。此前 401 保留为历史错误，不再是当前阻塞。Context7/FFF 的既有成功反馈仍适用。
- Windows SSH 可达，Debian 为 `Stopped`，`wsl.win-ws.localhost:122` 仍在 SSH 握手时 connection reset。`arcbox-win` 对应 Linux/amd64 Docker Desktop 28.5.2，不能等同既有 WSL 独立 Docker Engine 或已恢复的实验宿主。本次仅使用它构建和读取候选材料，不在其上运行生成或评测。

## 开跑前需要闭合的事项

| 事项 | 当前证据与下一步 |
| --- | --- |
| GLM-5.3 根模型对照 | 当前只有 `pi-braid-i13` 基线；`MODEL` 是一致性校验，不是根模型覆盖入口，模型目录也没有 `glm-5.3`。需要形成独立对照配方，保留原来的两个 Flash 可指派成员及全部原生角色，仅增设根专用 GLM-5.3 配置。不能修改共用 GLM 成员而连带改变子 Issue/PR。 |
| 全模型 ARC 路由 | 用户已明确允许恢复 ARC，并确认包括 GLM-5.3；模型发现已确认四个精确模型 ID。最终请求和 launcher 使用 ARC endpoint/凭据，视觉保持同通道；根对照需补完整 descriptor，并核对实际请求参数。Qwen key 保留但不进入本轮路由。 |
| 工具凭据装入最终包 | Exa 检索与正文现均取得成功反馈；最终私有包仍需用已修正的 `.env.i13-tools` 重新装入凭据。当前检查候选没有私有凭据，旧工具 ZIP 保留旧身份。 |
| 实验宿主 | 按独立 [Debian 环境方案](../debian-disk-recovery/packet.md)建立可用新环境，或明确选择另一实验宿主。旧 I12 已结束，无需恢复。稳定 Python asset、Runner/镜像、实际路径挂载、容器网络、OTLP 与可用空间均需针对最终宿主核实。 |
| 最终冻结与实验范围 | 根对照与 ARC 接线闭合后，再生成两份最终私有制品；比较最终请求、角色、技能和包来源。具体题目、起点、次数、并发、容量预算及逐题应用冻结/官网重放安排仍需形成实验记录并获得该范围开跑依据。恢复使用 ARC 的许可已经取得，不重复询问费用来源许可；新 journal 的 credential_mode/billing_mode 按实际平台接口选取，旧 journal 不自动接续。 |

最终私有包应记录 Factory 实际载荷、独立 Braid 源码/二进制、SVC 技能文件与 native lock/patch 身份。源码层面的实现完成，不替代这一份最终交付材料的组合核对。当前无凭据候选仅用于装配检查，不是可直接提交的私有实验包。

## 首轮实验要回答什么

两组使用相同允许需求、干净起点、共同 I13 材料和资源条件；区别限于根 Issue 的模型及其必要配置，所有模型均走 ARC。建议基线与 GLM-5.3-root 各运行 GitHub、Sheet 一次，共四次新生成，每题完成后立即冻结应用并独立官网重放，不等待其它题目。归档需求分别与自身 `source.json` 的 28、10 个文件完全一致，但这两个输入目录没有官方 `tests-source.json`，本地应明确采用 requirements-only，不产生本地分数。这是本次建议，尚不是新运行授权。用户如果选择先做小批次，应在两组间保留同题比较，而不是给两组不同题目。

过程观察集中于三条因果链：description 变化是否真正触发应有重建、普通评论是否继续增量送达；分工与交接是否保住父层及跨枝义务、最终判断是否消费对应候选证据；交付、原文保存与 work 回收是否分别产生可信结果。技能被读取、token 增长或对象关闭本身不作为行为改善的证明。

真实深层委派、executor 净收益、视觉采用、unknown 恢复和预算停止等尚未观察分支保留为实验观察项，不要求在开跑前另造模型任务。已有编译和材料反馈也不宣称这些分支已验收。辅助归档失败既不能冒充应用失败，也不能错误授权回收；首轮须读回实际归档回执及恢复承诺。

昂贵模型约束沿用 [既有明确决定](../competition-budget/packet.md)：受限模型合计只用于一个 Braid 主会话，归属使用稳定 `agent_id`；原生 sub-agent 继续各自角色配方，不另计 Braid 名额。不能仅凭摘要歧义在本轮擅自改变 Kimi advisor 或重新解释 child 豁免。

Console 已完成独立 hard cutoff 并可使用 Home，不是 I13 开跑阻塞；Bub 接入同样保持独立。I12 归档、旧服务历史和未参与本批的 dirty 均保留。
