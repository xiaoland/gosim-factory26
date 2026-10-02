# 本轮实施与验收状态

范围是 Factory 使用的 `sources/svc` Corpus、Factory 本地运行时 SVC 的接线，以及对应文档和非 bench 检查。
开发 SVC 保持完整；官方参赛包仍从 `sources/svc` 构建，不改冻结 ZIP。

独立只读预演核对了 `bootstrap → sources.build → generate → runtime_environment`、`batch.complete → analyze` 和官方 Docker 包装三条路径。
其结论是只需把本地参赛 SVC 安装移到 `.bootstrap/svc-runtime`，继续以源码快照和安装产物哈希判断缓存，开发 analysis 保持使用 `.venv`。
共享安装在已有 run 执行期间不应被重建；本轮不增加内容寻址安装或新的状态层。

本地运行代码已将参赛 SVC 安装移到 `.bootstrap/svc-runtime`，每个生成工作区仅建立一个指向已验证安装的 `svc` 链接。
开发 `.venv` 不再复制进生成工作区，`analyze` 的默认入口仍是 `.venv/bin/svc`。
SVC Corpus 已删除参赛任务不消费的 `specs/`、`migrations/`、`taste/` 和顶层 `templates/`，保留 `svc task init/grow` 的任务包模板；版本升为 `16.0.0` 并在旧 baseline 处明确截止升级链。
运行时 Corpus 不提及 Factory、Braid、Issue 分配、Web 应用或赛题素材，只界定当前 Agent 内的子代理；场景耦合审查见 [记录](overfit-audit.md)。

SVC 的 `pdm run check` 为 260 项通过；Factory 的 `make test` 为 139 项 Python 测试与 Pi observer 检查通过。
开发 `.venv/bin/svc lookup --list` 仍列出完整目录与 Corpus `15.0.1`；参赛 `.bootstrap/svc-runtime/bin/svc lookup --list` 只列出 `methods/`、`sub-agents/`、`task-packet/`、`verification/` 与入口，版本为 `16.0.0`。
参赛 SVC 在临时项目中完成 `task init` 与 `task grow`；本机 wheel 的 42 个 `svc_cli/data` 文件与参赛安装逐文件一致。
真实 `runtime_environment` 装配出的临时 Agent 环境通过 `PATH` 调用 `svc lookup --list`，读到 Corpus `16.0.0` 和预期的五个顶层入口。
源码快照和安装产物哈希校验、重复构建缓存命中均通过。
独立 Agent 只通过参赛安装的 `svc lookup` 预演简单单页和多角色视觉任务：前者停在短入口，后者按需找到 Task Packet、Planning、Design、Test Design、Verification 和物理 Sub-agent 路由。
预演指出根入口的 Task Packet 触发比正文窄，这一点已修正；先前为使 `screenshot` 检索命中而新增的句子已按用户要求撤回。
本地参赛安装的 `svc lookup --keyword screenshot` 现在无结果，`lookup --list` 仍可按方法目录导航。
最终 Linux x86_64 候选参赛 ZIP 为 `runs/packages/svc-corpus-review/pi-team-vv-generic-corpus-candidate.zip`，SHA256 为 `2de02e56b2f7df2db1c47ebdcf35e346fdefe8a920ae879829a063a60577979c`。
包内 manifest 的 16,360 个文件哈希全部核对通过；SVC 与 Braid 源码快照匹配当前工作树，包内 Catalog 与本地参赛安装一致，27 篇 Corpus 文档在源码、本地安装与 ZIP 中逐文件一致，V&V 预载两篇的哈希匹配。
上一份过期候选 ZIP 已删除，避免误用。
`sources/svc` 尚未提交，variant 的 `source_revision` 因此仍是旧 HEAD `393b935`；候选包 manifest 的逐文件哈希记录了实际改稿。
正式评分前要在获准提交后更新该 revision，并重新构建参赛包，避免把旧 HEAD 误认作本轮 Corpus 的提交身份。
用户已明确将 bench 评分验收延后，待实验基础设施准备好后另行通知；本轮不能把非 bench smoke 宣称为实验成绩。

此处记录的是 CLI 裁减前的验收快照；删除 `task grow` 后，该 ZIP 不再代表当前源码。最新状态见 [CLI 裁减任务](../svc-cli-simplification/packet.md)。

后续接线已改为 skill，以上安装与 ZIP 均为历史快照；当前状态见 [SVC skill 接入](../svc-skill-integration/packet.md)。
