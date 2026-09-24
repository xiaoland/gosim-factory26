# SVC 自身作为完整 Agent Skill

2026-09-24，用户认可结构方案并明确回复“同意，可以开始”，同时要求寻找导航优化空间。
本次实施源为 `sources/svc`，开发侧完整 SVC 保持独立。
实施阶段不提交、不启动模型或 benchmark、不编写或运行 Factory/Corpus 测试，也不修改冻结制品；后续提交授权见文末。

## 具体边界与顺序

1. 把方法正文移入 `sources/svc/references/`，模板移入 `assets/templates/`，入口由同仓库根 `SKILL.md` 唯一持有。
   合并旧 corpus/index 与 Factory 包装入口的重复导航，修正方法到模板的相对链接。
   根入口直达高频方法，并提供 packet 深层指南和角色指南的可选直达路径。
2. 删除 Factory 包装文件，`harness/skills/svc` 只保留指向 `../../sources/svc` 的目录链接。
   共享文件操作增加按标准资源布局复制 skill 的机械操作，源码运行与打包使用同一操作，保留许可证。
   复制 SKILL.md、references/assets/scripts 和许可文件，不复制仓库维护者指南、CLI、Git 或环境目录。
   这是本项目所用技能的打包布局，不声称 Agent Skills 禁止其它资源布局。
3. 四个 variant 分别移除 `--svc-corpus` 与二次补装正文；build 和公共打包入口同样清退参数及 SVC 分支。
   模型、Braid 成员、角色和启用哪些 skill 不变。
4. 更新 SVC 维护者入口以及 Factory 的开发、恢复和部署说明。
   旧 CLI/tooling 是继承的历史源码，不再承担此 skill 的发布或消费；不扩大为删除全部历史开发工具的任务。
5. 通过真实 skill 分发目录的生成和直接阅读进行编辑/材料复核，不运行模型或伪装的自检。
   按既有计划等待真实 bench 与 trace 验收，不宣称文本迁移改善成绩。

## 预先核实的接口

四个 run.py 都由 skills-root 取得材料，主会话用 Pi --skill，子角色用 skills/skillPath。
公共 assemble 只被四个 build.py 消费，package CLI 为其提供显式路径。
当前其他获选 skill 只有 SKILL.md 和可选 LICENSE，不含额外自定义资源目录。
源码目录链接在复制时物化；参赛包和工作区里的 skill 不依赖仓库外的符号链接。

实施前副本：`runs/svc-skill-integration/native-skill-before/`。

## 落地结果与证据

入口现为 [SVC SKILL.md](../../sources/svc/SKILL.md)，具备 name、description 和 metadata；正文与模板全部在同一 skill 内。
`harness/skills/svc` 是指向 `../../sources/svc` 的源码目录链接，实际分发时由 `copy_skill` 物化成普通文件。
四个 variant 的 run/build 与公共打包入口已完成接线清退，当前运行代码和长期说明中不再使用 `--svc-corpus` 或旧 corpus 路径。
模型、角色和 skill 启用范围没有调整。

导航删除了旧 corpus/index 的重复入口，高频方法由 SKILL.md 直接定位正文。
现有 packet 的规划、信息组织、增长与 Explorer/Executor 指南也有可选直达链接，无需为单一问题逐层加载索引。
模板独立归入 assets/templates，入口明确仅在材料形状有帮助时复制；没有把导航变成必须执行的流程。
按原文直接复核了内部相对链接，跨到模板的两处链接已随移动修正。

实际生成的独立分发材料为 [svc.zip](../../runs/svc-skill-integration/native-skill-distribution/svc.zip)，展开目录在同级 svc/。
分发包含 27 个 Markdown 文件，顶层为 SKILL.md、references/、assets/，不携带仓库维护者指南或 CLI。
本次执行的是实际材料复制和 ZIP 分发操作，没有新增或运行测试、自检、模型或 benchmark。
这支持“材料可独立分发”的结论；真实 Agent 是否有效选读并运用方法仍需获授权运行的 trace，不能据此关闭 Corpus 行为验收。

Factory 长期开发/运行说明、源码恢复说明及 SVC 维护入口已同步。
原始操作前副本、历史实验和冻结制品保留。

## 提交进展

2026-09-24 用户明确回复“可以提交”。
SVC 源仓库已提交 `b5a0fb8`，包含 skill 正文、模板迁移及维护说明，旧 CLI 的其他改动未纳入。
提交整理时，Factory 的 run.py、build.py、agent_support.py 尚未入库，本次接线依赖未提交的独立 variant/DX 实现。
用户随后明确“确认”，允许先提交必要前序实现，再单独提交本次接线。
前序提交为 `7bb2c60`：四个独立 variant、运行支持、工具资源与打包入口；交叉文件使用迁移前副本写入 index，没有回退工作区。
本记录随完整 skill 接线提交，包含通用 skill 复制、源码链接、四组 run/build 参数清退和直接受影响的导航说明。
其他实验、诊断网站、旧执行路径清理与独立源码 CLI 改动保留在原工作区，没有纳入。
未运行测试、模型或 benchmark，也未推送。
