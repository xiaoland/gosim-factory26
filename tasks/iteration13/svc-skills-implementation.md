# I13 SVC Agent Skills 实施记录

2026-09-30。本批按[已批准方案](svc-skills-plan.md)和[task-packet复审](task-packet-review.md)完成正文恢复、退出入口清理与材料核对。用户授权原话是：“我阅读了方案，没问题，你可以安排subagent开工。btw，可以考虑裁剪掉‘跨仓共同依据’的内容，因为我们的赛题不存在多repo。”本记录不替代主packet的当前任务状态。

## 实际改动

documentation入口先解释项目理解为何需要持久保存，再按问题导航到产品what/why、跨单元协作、内部设计与局部指引、部署运行恢复、Alignment五份reference。每份均包含职责、成立条件、使用维护及相邻边界。PRD、Product TDD、Unit TDD表示知识职责，不要求固定目录或文档梯子。五份可选起步模板分别服务产品、共享技术约定、运行、Alignment和局部指引；不为单元内部设计另造模板。

当前documentation中已有未提交的消费者通知与采用修订已先快照并完整整合：发布差异、通知负责人、消费者比较当前设计/计划/实现/验收、实际采用及对应版本是不同事实。编辑器/导入器例子保留，内部journal顺序与迁移恢复例子补足其它知识职责。Multi-repo专门方法、模板和导航没有恢复；多组件共享定义及版本对应仍保留。原始完整SVC仓库只读使用。

sub-agents改为自包含方法：解释完整重做和同类Agent赞同的局限，总成本同时考虑交接、等待、纠正、理解、整合、误收和过度拒绝；说明精确查询、关系检查、抽样及开放判断的成立条件与限制。短SQL和交互方案两条情境各说明调用方省去的工作、采用依据与未支持部分。实际观察与child自报分开，结果可采用、返修或保留未知。

同步本轮用户对委派价值的校正：调用方提供足以明确问题、用途与必要边界的背景和材料入口，不必先查齐局部初态、逐文件划分或执行步骤；child自主补足调查、局部设计、实现细节和协调。局部可恢复问题留在child，越过整体目标、权限或重大取舍的缺口才升级。本技能没有其它skill或方法链接，没有具体角色职责、触发或咨询豁免政策，也没有独立verifier、控制面或certificate框架；未选定原生cwd并发写策略。

task-packet入口从外置工作记忆和最小已有材料起点展开，贯穿“取得材料、形成解释、取得区分性观察、采用结果、修订当前判断”。information沿用同一共享格式问题，解释原件、当前综合和结果采用各自的用途。planning保留按需路线、负责人、依赖与Task/Track/Phase/Cell能力；`growth.md`及入口已删除，未更名迁移其形状预检或完整章节。packet模板只同步当前依据、下一步因果和在途材料入口。

保留四技能对implementation、investigation、design的链接和文字路由均已清理。verification只调整check-design、feedback-and-evolution，以及Primary确认的interpreting-results单句退出路由，保留原有判断含义。三技能源码仍在SVC。维护导航反映七技能源码与新的文档/任务材料；I13 build、main skills及两份父profile不再打包或读取退出三项。父profile其它流程、现有项目文档和packet义务保留，整体重写归后续批次。

## 来源、提交与保全

修改前身份为Factory `7f8ad6e401fd1cb96b63e077064168c0a5c553d7`、SVC `31906a599c1acda1e8c98e79e5c216c99e7bd0aa`。原始完整SVC来源为`/Users/lanzhijiang/Development/svc`的`80996c115ba635c6b85db47d0b14663293b95f12`。按需读specs总入口、PRD、Product TDD、Unit TDD、Deployment、Alignment、相关模板和Corpus/task-packet入口；sub-agent依据是[已整理来源](../factory-subagents/cells/subagent-paradox-source.md)。没有将原来源后段assistant架构提案视为用户逐项批准。

[修改前快照](../../runs/iteration13/svc-skills-20260930/before/)包含两仓binary diff、status、空index起点及本批相关文件原件，保留documentation旧改动、退出growth原文和原profile。SVC提交为`a0af6e14a9f6cd2b19e1565e5d08d82fe3672139`，仅纳入本批25个文件；CLI、旧测试删除及implementation中的历史dirty均留在工作区。Factory本批提交只纳CONTRIBUTING两段、I13 build/run/两profile、方案及本记录，最终提交身份由本批交付和Git记录给出，不暂存Primary的packet等材料。

## 实际材料反馈

使用`.venv/bin/python`编译I13 build.py、run.py和main.py，退出值0；[编译记录](../../runs/iteration13/svc-skills-20260930/compile.json)与独立pycache保存在本批目录。

标准I13 build首轮在共享assemble调用`python -m pip`时因开发venv缺pip退出。保留[原始错误](../../runs/iteration13/svc-skills-20260930/build-attempt1.log)、对应退出值及半成品`stage/`。仅通过uv将pip 26.2.1安装到本批`build-python/`，用PYTHONPATH让同一`.venv/bin/python`完成标准build；未修改共享构建源码、开发venv或旧runtime。成功制品在[stage-complete](../../runs/iteration13/svc-skills-20260930/stage-complete/)，[构建记录](../../runs/iteration13/svc-skills-20260930/build.json)退出值0。

从该制品的main.py使用真实`tasks/iteration11/run-audit/github`需求、制品内skills/runtime、`sources/braid/target/debug/braid`及`http://127.0.0.1:9/v1`执行prepare-only，退出值0。实际run是[20260930-232040-2644b0ad](../../runs/iteration13/svc-skills-20260930/prepared/.factory26/20260930-232040-2644b0ad/)，[run.json](../../runs/iteration13/svc-skills-20260930/prepared/.factory26/20260930-232040-2644b0ad/run.json)终态为prepared。未启动模型、生成应用或正式实验。

直接读取制品目录、launcher、两成员共十份原生角色、braid-request与Markdown导航：主launcher启用documentation、task-packet、sub-agents、verification四项，退出三项不在制品中；documentation、task-packet、sub-agents、verification分别有12、13、1、6个文件，reference及模板均作为普通独立文件物化，内部相对路径指向现存材料。source、stage和prepared工作目录的这32个文件身份一致，见[文件身份](../../runs/iteration13/svc-skills-20260930/skill-file-identities.json)。[实际文本查询](../../runs/iteration13/svc-skills-20260930/retired-routes-query.json)退出值1、stdout/stderr为空，三技能退出文字、growth入口和Multi-repo导航在保留材料中没有匹配；sub-agents自包含且没有角色专属政策。launcher仅传skill路径，角色frontmatter仅声明skills/skillPath；profile和task prompt没有装入技能或reference正文。

Primary另行读取三个技能入口及委派判断正文，独立比对prepare-only最终32份技能文件与sources/svc材料，差异为空，并核对四技能选择、五类文档职责、task-packet仅information/planning和退出内容。其[材料复核记录](../../runs/iteration13/svc-skills-20260930/primary-material-review.json)独立于本批实现者自报，同样只建立材料事实，不建立真实方法收益。

runtime只读复用上批`runs/iteration13/subagents-20260930/runtime`并复制进本批stage，保留其实际runtime-source及旧补丁身份，不宣称它包含Primary同期修改的原生writer说明。prepare-only显式使用的本机Braid二进制路径和哈希、SVC commit、原来源及I12起点/终点diff在[来源记录](../../runs/iteration13/svc-skills-20260930/sources.json)。I12起点已有两份profile修改，本批前后diff哈希同为`e44f4fea52eca2cd2d7fd854599cd7b58f54455c1edf01324c6c0111b064588c`，本批没有修改或运行I12。

## 判断边界与移交

编译和prepare-only建立材料来源、选择与路径事实，未证明方法在真实工作中的收益。没有编写或运行Factory、Braid、SVC测试、包smoke、模拟任务、探针、自检或模型实验。是否在决定形成前使用适合的方法、child是否独立收敛并被采用、共享知识是否影响消费者、packet是否改变当前判断，仍须获授权真实工作证据。

documentation/task-packet强制应用与profile整体分层联查尚未实施。本批清理技能选择冲突入口，没有把退出内容改为内联提示；现有profile的“按需/可选”措辞与advisor等政策留给后续统一处理。SVC和I13所有本批文件面在交付后释放，Primary继续持有packet/findings/repair-design与其它提示词批次。
