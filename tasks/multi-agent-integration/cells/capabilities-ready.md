# 能力与方法装配 × 接入就绪

Track：capabilities。Phase：ready。状态：active。01 独立预演及 V&V 方案复核完成，见 [capabilities.md](../rehearsal/capabilities.md)；主 Agent 持有装配/V&V，pi_lifecycle_impl 持有薄生命周期扩展。实施起点提交后进入 02，真实兼容性仍待验明。

本 Cell 让 Braid 的每个 Agent 实际获得所选 Codex/Pi 核心、原生子代理、技能、浏览器和 SVC 指引。四份 preset 是这一责任的装配产物，不能替代整体 multi-agent 能力交付。普通 profile、原生子角色和 Factory preset 分层，LLM 保留工作组织与决策。

## 出口与依据

实际核心消费的模型/reasoning、能力材料与声明一致，个人配置隔离，原生子代理可完成有界工作并返回；浏览器按物理会话隔离，executor 保有局部实现与反馈循环。四组共享固定 V&V，其余 SVC Corpus 不变；只有 pi-verification 提供可选 reviewer，无 contract-reviewer。技能或模型不兼容须显式报告，不能静默降级后保留原名称。

选择归 [技术方案](../technical.md)、[四份 preset](../presets.md)，材料依据归 [需求映射](../requirements-fit.md)、[技能调查](../skill-candidates.md)、[Pi](../research-pi.md)和[Codex](../research-codex.md)。V&V 的方法输入是[用户原文](../../verification-system.md)，不改原文，不借适配重写其余 Corpus。

## 局部计划

1. **01：返回装配路线及风险收敛。** 独立预演实际 Pi 扩展/角色和 Codex app-server 配置入口、隔离 HOME、session ID 与模型协议；明确哪些事实已有证据、哪些必须在联合场景验明。准备 V&V 的具体删改与消费样例、外部 skill 的必要适配，避免新增强制流程。
2. **02：返回可消费的能力环境。** 共同实施前门槛通过后，按 runtime 的绑定接通配置、材料、原生子角色和浏览器；先闭合一个 work-item 到 child 的加载、工作、返回路径，再展开四份组合。dependencies/models、profiles、roles、preset、batch 各有责任，不重建 God config。
3. **03：返回固定装配与兼容证据。** 在既定 Pi/Codex 联合场景中验明 K3/K2.7 Code/GLM Flash 必需参数、工具/图像与流式终态、技能实际消费和浏览器隔离；核验 V&V 判据辨别能力及非 V&V 文件不变，交付四份可复现组合和来源摘要。

模型、核心或工具能力不足会改变配置意义时，返回具体证据和建议，不自行换模型、取消能力或扩成浏览器交叉矩阵。模板或静态配置检查只证明配置边界，不能冒充真实消费。

本 Cell 的 01/02 consumes runtime 的 01 profile/binding 合同，02 的真实执行消费 runtime 的 02 入口；自身 02 的实际配置供 runtime 的 03 联合核验，不等待完整 runtime Cell。向 feedback 随各返回提供配置/身份合同、实际配置、材料版本与能力证据。主要写入面为 Factory 装配、variants/harness 和 SVC 的 V&V owner；scripts/factory.py 的共享接缝由主 Agent 统一集成，不与 feedback 同时编辑。

## 02 当前返回（2026-09-21）

Factory 已实现 `profiles.py` 的显式引用解析、`native_profiles.py` 的 Pi/Codex 模板装配，四份 preset 各自引用普通 profiles。Pi 0.85.1 + pi-subagents 0.56.0 + agent-browser 0.38.1 的 npm 完整依赖图已固定；只安装/缓存一次。三个模型的 descriptor 取自该固定 Pi 版本内置数据，比赛网关接受情况仍待联合场景，不能把 metadata 当实测。K2.7 Code 的 high 意图映射为 always-on thinking，原生不发送 reasoning_effort；K3/GLM Flash 映射 high。

无模型 RPC 启动已收到 get_commands/get_available_models 成功响应，生命周期 command 确实加载。技能内容和适配差异在 `harness/skills/README.md`，普通 Braid profile 与 native roles 分离；前三组不提供 reviewer。配置边界测试已覆盖仅实际消费者修订失效、未知引用及路径越界。真实 child 与浏览器反馈的联合证据仍未满足 03。

V&V 两个语义 owner 已改写并升为 Corpus 15.0.1，发布元数据与对应版本断言同步；其它 Corpus 正文未改。SVC 全检查首次为 258/259，唯一失败为既有当前版本硬编码，更新后全量 259/259；catalog/release 12/12，lint/type/import contracts 通过。Factory 的 SVC baseline 已按 upgrade plan 采用 15.0.1，status healthy。

独立消费判例使用“通知开关保存后，在新的登录浏览器中仍读到已保存值”：观察新会话的用户可见设置，以要求值为 Oracle，不能拿保存响应或旧组件 state 自证。仅更新本地内存、丢失写入应失败；数据库、KV、可靠复制等满足同一用户可见性质的实现应通过。异步实现的等待边界必须来自保存完成语义或需求明确的可见性约定，不能凭测试作者偏好要求瞬时一致。该判例支持候选材料的可用性，不证明其对所有需求或 bench 成绩有效。

WSL 已安装受控 Node 26.3.0、固定 npm 核心及 Chrome 缓存、LiteLLM 1.102.0、SVC V&V 候选；runner HEAD 与清单一致。Codex `skills/list` 无模型调用确认隔离 home 能发现 agent-browser，主会话配置为 disabled，operator/executor 的 role 配置启用。Pi `session_start` 立即记录空 native tree；实际 child 通过原生 result/status 关系填入。Node 生命周期检查通过，但这仍不是活跃子进程停止的证明。

联合验收的原生能力阶段脚本在 [scripts/native-scene.py](../scripts/native-scene.py)，使用临时图像和页面，独立于 benchmark。首次 Pi 阶段为 `runs/integration/20260921-231003-pi-native-4a2f8b`：executor 和两个 browser-operator 已实际执行，父 K3 最后 Connection error，整体未通过。独立网络探针确认 WSL 默认 DNS 172.29.144.1 对 API/Rust/crates 均失败，Mac 同时可达；WSL 直接 DNS 与外网 TCP 正常，已用进程内 bwrap 的 resolv.conf 挂载恢复解析，未修改系统 DNS。真实场景还揭示 workflow children 漏归档、probe 根 session 路径身份不匹配，正在修正。原始失败不覆盖，不称已通过图像/浏览器/多 Agent 验收。

该阶段检查图像读取、原生 executor、双 operator 浏览器状态与归档；Braid 指派/协作和活跃 native tree 停止另沿同一联合验收目标完成，不能以本阶段替代。SVC V&V 源码提交为 `393b935`。
## 真实能力阶段的补充结果（2026-09-21）

Pi 第二次运行 `20260921-233730-pi-native-f53672` 在进程级 DNS 覆盖下自然完成图像、executor 和两个 browser-operator 的隔离检查。整体仍失败：父 session 路径指向无 header 的别名文件，严格归档拒绝；三个 child 的真实 session、角色和工具产物已存在。保留原失败状态，正在用原产物离线修复/重核归档，不因路径问题重复调用模型。

本机 Codex 运行 `20260921-234206-codex-native-c86aff` 已通过首个 K3 请求并执行 view_image 与 svc lookup；工具结果回传后的下一请求收到网关 400 `text content is empty`。留存 rollout 离线重放确认 Codex 插入了一个 `output_text: ""`，LiteLLM 转为 Chat 后网关拒绝。兼容 hook 只删除 Responses `input` 中精确空字符串的 text block；空白文本、图像、function call/output 均保留。本地严格网关回放由 baseline 400 变为 compat 200，尚待一次真实 Codex 场景重验。Codex 主/子配置也已消费现有模型映射的 context window，并用 TOML 实际装配检查核验。

受影响路径重验 `20260922-000743-codex-native-b27032` 已通过。Codex app-server 使用 K3/high 完成原生图像读取、executor 局部实现和两个 browser-operator；四个原生会话均有 parent/role 关系，adapter 后续 Responses 请求全部为 200。两个 operator 的 cookie、localStorage 和 native session ID 相互隔离，退出后无工作区残留进程。该场景证明 Codex generalist 的这条能力链，不替代 Braid work-item 协作场景或 ARC-bench 成绩。

Pi Braid 场景 `20260922-000737-pi-braid-5f89e9` 仍失败：前台 child 确实运行且 heartbeat 停止，但成功 stop receipt 的 children 为空，严格判据拒绝继续后台路径；多 profile Issue/PR 尚未开始。原失败证据保留。更高层根因是 Braid active reset 先 abort 父 turn、后 native teardown，使 foreground control 在 lifecycle 查询前消失；不能靠 fleet/snapshot 猜测弥补。实现已改为复用 SessionManager 的 `native teardown → close parent` 路径，失败时不 interrupt 父、不启动 replacement；extension 仅补直接 foreground-complete payload，归档使用同一 session-tree 的 canonical parent 文件。离线顺序检查和协议检查已通过，真实受影响路径仍待一次复验。

WSL 真实复验 `20260922-005345-pi-braid-58a8f8` 在上述顺序修正后仍失败。Braid 保持旧 physical session 为 `reset_pending`，没有启动 replacement，说明上层失败闭锁生效；但 foreground writer 从 teardown request 的 `1790009671` 持续写到 `1790009681`，10 秒内没有静默。此时 session-tree 却把同一 run 记为 `control_inactive:true`，且没有生成 `subagent-stop.json`；因此当前下层假设“control inactive 等价于 child process 已终止”被真实输出否定。归档还报告 session-tree 的 parent identity 与 Braid 根会话不一致。该场景是实现验收，不是 benchmark 实验结果；继续修复后复验，直到固定 Lite 批次产出评分。当前修复不再把 control inactive 当终态：hook 只给出 ready，Braid 关闭并验证自己拥有的 Pi provider 进程组后才最终写 stopped；无模型黑盒已证明忽略 TERM 的工具后代也会被清理，真实路径待复验。
