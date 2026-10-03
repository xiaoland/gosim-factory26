# Harness 共用材料

本目录提供可供 variant 选择的工具依赖和技能文件，不决定协作流程或模型配方。开发 Agent 的项目指令归根目录 [AGENTS.md](../AGENTS.md)，参赛 Agent 的输入由I14 的 `materials.json`、`run.py` 和原生角色文件选择。

| 材料 | 权威位置 | 消费者 |
| --- | --- | --- |
| npm 工具与精确版本 | [npm/package.json](npm/package.json)、[npm/package-lock.json](npm/package-lock.json) | `scripts/runtime.py` 的本机安装和 `submission/Dockerfile` 的 Linux 构建。 |
| 原生工具补丁 | [npm/patches/](npm/patches/) | 两种 runtime 装配路径；改补丁时同时核对实际消费入口。 |
| 非 npm 依赖和技能来源 | [dependencies.lock.json](dependencies.lock.json) | 资源生产与来源追溯，不是每个 variant 的启用清单。 |
| 技能入口、许可与适配说明 | [skills/README.md](skills/README.md) | 各 variant 显式选择的独立技能。 |
| 公开模型路由 | [model-gateway.json](model-gateway.json) | 网关材料装配；私有凭据由实际 deployment 注入。 |

`skills/svc-*` 链接指向本仓库的 `sources/svc/skills/`；打包时 `copy_skill` 将入口和标准资源目录物化为普通文件，保留许可。`skills/svc` 是历史单技能快照，不能作为完整开发 SVC 安装源。开发 `.venv/bin/svc` 的安装方法归 [scripts](../scripts/README.md#准备原生工具)。

技能存在于目录或包内不代表会话已启用它。主会话和内部角色各自声明发现入口，只提供名称、description 和路径，按需读取文件；SKILL.md 和 references 正文不拼入 system、profile、role 或 task prompt。I13 的具体选择见 [I13 本地说明](../variants/pi-braid-i13/README.md#工具与技能接线)，其它 variant 按自身接线解释。

维护技能时更新已有来源/适配说明和实际消费者，避免在本页再列一份模型、技能启用或版本表。纯指令或技能变化只重新装配材料；需要新依赖才重建对应 runtime，方法见 [资源与打包](../scripts/README.md#构建独立运行资源与制品)。
