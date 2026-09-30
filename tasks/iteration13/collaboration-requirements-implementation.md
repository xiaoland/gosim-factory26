# I13：Braid 协作与 ARC 需求方法实施

2026-10-01。开工依据为用户：“好的，现在可以开工该组了。然后我们看看i13树”。具体范围归 [当前方案](collaboration-requirements-plan.md)，本批直接复用先行边界提交 `1c8b9f9`。主线持有 packet、方案、推导与独立复核；本页记录两项技能、I13 接线和受影响长期说明的实施，不授权模型实验、部署或 I12 修改。

限定起点、源码哈希、工作区与 index 差异保存在 `runs/iteration13/collaboration-requirements-implementation-20261001/start/`。技术说明起点已有 assignee 段修改，本批保留它，不纳入提交。其余拥有的既有源码、技能与文档没有本批起点修改；其它任务工作区保持原样。

## 最终材料与接线

两项技能按方案形成 2 份主文件和 7 份 reference。主文件给出常见决定所需的核心判断、理由和下一步；reference 按完整问题展开，而非按字数或每条规则拆文件。材料没有固定报告模板、逐节点状态框架或新调度器。

`braid-collaboration` 解释按可消费成果和真实依赖组织责任、共同知识与任务状态的位置、交接和成果采用、变化的实际消费者、有效结果复用与结束判断。四份 reference 分别处理工作组织、交接变化、接受关闭和完整共同案例。唯一案例是编辑器与导入器共享设置；它不包含 ARC 格式、节点类型、题目答案、评分或诊断。

`arc-bench` 接续原有平台合同，补齐原树、父层与跨枝承诺、场景和初态归属、依赖解释、来源/依赖/责任/证据的区别，以及候选变化后的覆盖回查。两份新增 reference 处理需求阅读与覆盖追溯，既有 `platform-delivery.md` 继续持有平台前提。ARC 可单向引用通用协作方法和唯一案例；Braid 不反向依赖 ARC。SVC 仍持有项目知识、task packet、原生委派与 V&V 的完整方法，新材料只解释工作项之间如何连接并使用它们。

I13 build 收录 braid-collaboration，run 沿既有复制与 Pi `--skill` 发现机制装载两项技能。两份 profile 给出协作技能读取时机，同一会话已读方法按需回看；旧交接、文档连接、证据适用和关闭方法迁入技能。根基础 PR 政策从 root prompt 移到 profile，advisor/vision 分工、develop → main、应用反馈工具与通用环境保留。root description 只给本次 ARC 目标、允许输入、技能读取入口及中文输出参数，不再内联需求理解、分工和承接方法。

PRD 补入协作责任与完整承诺的产品含义；技术说明更新材料的单向依赖、读取入口和实际复制职责，替换“整组尚未实施”的旧表述。没有改 Braid/Pi 运行机制、原生角色工具权限、其它 variant、SVC 来源、凭据或实验设施。

## 实际反馈及其范围

Python 3.12 对本批 run.py 和 build.py 编译完成，源码哈希与编译产物归证据目录的 `compile.json` 和 `compiled/`。标准 `variants/pi-braid-i13/main.py --prepare-only` 使用先行批次的 `allowed-example-input`：官方 compiler 的真实 requirements 两文件和 7 张参考图片，没有读取或复制其公开 tests，也没有 synthetic fixture。

首轮实际材料路径为 `runs/iteration13/collaboration-requirements-implementation-20261001/prepared/.factory26/20261001-073443-43ea81f0`，exit code 为 0。原始命令、退出结果和日志归 `prepare-operation.json`、`prepare.log`，完整读取归 `prepared-material-review.json`。它发生在 profile 补回按需回看短句及 run/TDD 写权交接前，保留该身份，不冒称后续所有共享源码的最终版本。

读取真实 prompt/request、两份 profile、launcher、十份原生角色以及复制技能后，观察到 9 份技能文件与来源哈希一致，全部 15 项主技能路径和相对链接存在。profile/角色不含 ARC 节点与平台知识，主文件或 references 正文未内联到 prompt/profile/role。request、Pi 与 profile 字段和交付 ref 与先行边界材料一致，没有新增需求语义字段；真实输入复制哈希与来源一致。

运行时复用工具组 `native-runtime`，身份为 darwin-arm64、工具 Node v24.15.0；首轮 Braid 使用当时已有文件供 prepare 复制，没有执行 Braid 会话。本批不改依赖、不重建 Linux runtime 或大包，不用工具 Node 的材料准备证明平台 Node.js 20.19.3 已通过应用部署。

最终材料复用 storage 协作者完成的标准共同 prepare：`runs/iteration13/storage-lifecycle-integration-20261001/prepared/.factory26/20261001-074056-94828e68`，exit code 为 0；原始命令与日志归该组 `prepare-operation.json`、`prepare.log`。本组独立读取其实际产物，结果保存在本组 `prepared-material-review-final.json`。最终 profile 已包含按需回看短句，9 份技能文件、15 项路径及全部相对链接仍一致且可读，无旧方法副本或正文内联；请求字段、真实输入哈希与交付 ref 均保持本组既定边界。

共同 prepare 使用含 storage 尾部改动的当前 run.py，实施哈希与读取时源码一致；本组 `compile-final.json` 记录该实际共同源码的编译反馈。复制 Braid SHA256 为 `1f67dcea1b6309b4b505187debc8a18c168460bd5043273709735209b369b130`，编译来源身份归 storage 组。`sources/braid/target` 既有链接指向 third_party 的 target，因此材料解析后的路径不能单独辨别源码来源；使用操作中的来源身份与二进制哈希。这次准备没有进入模型或归档执行分支，不能据此声称 storage 收尾、完整 Braid 调用或应用交付已验收。

已有事实对照在 `runs/iteration13/collaboration-requirements-implementation-20261001/method-review.md`：早期漏父文与后续未采用分开判断，局部排除后整体义务继续保留，叶子 ID 和局部通过不能代表完整覆盖；同时保留实际承接、有效证据复用及合理停止的正例。对照支持“方法能表达这些决定”，不证明模型已经采用，也不把长度、reset 或检查数量当成失败原因。历史来源只在开发记录，不进入参赛技能。

## 并行集成与提交边界

完成本组接线和首轮实际准备后，run.py 与技术说明写权明确交给 storage-lifecycle 协作者。本组限定增量及交接时源码保存为证据目录的 `run-owned.diff`、`tdd-owned.diff` 和 `handoff-source/`；后续提交只应用本组增量，不收录起点 assignee 或 storage 修改。技能、profile、build、PRD、技能索引及本页继续由本组收尾；共享文件需要新改动时先重新协调。

主线已接受独立只读复核：完整读取两份主文件、七份 reference、profile/run/build 与实际材料，确认内容与单向依赖可接收，Braid system 仍持有 Issue 设计/PR 实施职责，无需实质修改。限定提交身份归本组证据目录的 `commits.json`；原始材料与失败如有发生均保留。没有编写或运行 Factory/Braid/SVC 测试、smoke、probe、模型调用、应用生成、官网评测或 Exa 重试，没有 push。材料存在、可读取和源码编译不能代替模型采用、应用正确性与部署反馈。
