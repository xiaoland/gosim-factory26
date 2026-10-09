# Harness 共用材料

本目录提供可供 variant 选择的工具依赖、技能和跨 variant 模型配方输入；不决定 Agent 的协作流程。开发 Agent 的项目指令归根目录 [AGENTS.md](../AGENTS.md)，参赛 Agent 的输入由I14 的 `materials.json`、`run.py` 和原生角色文件选择。

| 材料 | 权威位置 | 消费者 |
| --- | --- | --- |
| npm 工具与精确版本 | [npm/package.json](npm/package.json)、[npm/package-lock.json](npm/package-lock.json) | `tooling/scripts/runtime.py` 的本机安装和 `tooling/linux/Dockerfile` 的 Linux 构建。 |
| 原生工具补丁 | [npm/patches/](npm/patches) | 两种 runtime 装配路径；改补丁时同时核对实际消费入口。 |
| 非 npm 依赖和技能来源 | [dependencies.lock.json](dependencies.lock.json) | 资源生产与来源追溯，不是每个 variant 的启用清单。 |
| 技能入口、许可与适配说明 | [skills/README.md](skills/README.md) | 各 variant 显式选择的独立技能。 |
| 可用模型 deployment | [model-gateway.json](model-gateway.json) | 网关材料装配；端点、wire model 与凭据变量引用，不决定本次有序选路。 |
| 跨 variant 模型配方 | [model-recipes/README.md](model-recipes/README.md) | ARC API、自费、比赛通道的配置归属；已有自费路由由装配者显式消费。 |
| Factory26 附加任务上下文 | [bench-contexts/hackathon-evolution/task.json](bench-contexts/hackathon-evolution/task.json) | 生产者按任务显式冻结补充文件，与官方输入分别记录身份；variant通过`TASK_CONTEXT_FILE`读取。 |

共享实现以本仓库源码为唯一维护来源：技能取自 `materials/skills`，Braid 取自 `sources/braid`，Pi 取自公共 npm lock、补丁与 runtime 生产入口。新装配先取得共享材料，再应用 variant 的明确覆盖；variant 不保留一份共享实现作为默认。交付时复制和冻结材料不改变源码归属，已有冻结运行也不因共享源码更新而改变。技能库可用范围与会话启用范围分别处理，库中新增技能不会自动把其 description 加入所有会话。

角色与模型选择由 variant 和本次实验输入持有；有序供应商链由显式 gateway-routes 输入持有，ARC API、自费、比赛三种配方从[公共模型配方](model-recipes/README.md)发现，与 variant 身份独立。catalog 的 factory26_default 用于未传入路由的兼容选择，不代表用户当前配方。运行保存所消费配置与实际调用记录，不能由候选条目推断最终命中的供应商。

`skills/svc-*` 链接指向本仓库的 `sources/svc/skills/`；打包时 `copy_skill` 将入口和标准资源目录物化为普通文件，保留许可。`skills/svc` 是历史单技能快照，不能作为完整开发 SVC 安装源。开发 `.venv/bin/svc` 的安装方法归 [scripts](../tooling/scripts/README.md#准备原生工具)。

技能存在于目录或包内不代表会话已启用它。主会话和内部角色各自声明发现入口，只提供名称、description 和路径，按需读取文件；SKILL.md 和 references 正文不拼入 system、profile、role 或 task prompt。I13 的具体选择见 [I13 本地说明](../variants/pi-braid-i13/README.md#工具与技能接线)，其它 variant 按自身接线解释。

维护技能时更新已有来源/适配说明和实际消费者，避免在本页再列一份模型、技能启用或版本表。纯指令或技能变化只重新装配材料；需要新依赖才重建对应 runtime，方法见 [资源与打包](../tooling/scripts/README.md#构建独立运行资源与制品)。

附加任务上下文由 bench 持有，不能内置进 variant 或改写官方 requirements。生产者使用 `tooling/scripts/task_context.py` 的 `freeze_task_context` 将任务配置引用的文件复制到冻结 `inputs/extra`，记录来源与 SHA，并将实际容器路径设为唯一 `TASK_CONTEXT_FILE`。未提供该环境变量时保留原入口；明确提供却不可读时，variant在模型调用前报告具体文件错误。最终 prompt 只引用补充文件路径，不内联正文；实际生成是否读取该材料另由原生工具证据确认。

原生 owned E2E 客户端归 [e2e/owned-client.mjs](e2e/owned-client.mjs)，仅由显式选材与原生工具接线的 variant 使用。它固定真实子进程输入并复用 mcporter daemon，不替换公共 mcporter 的环境身份规则；技能存在或更新不表示旧冻结包已采用入口。
