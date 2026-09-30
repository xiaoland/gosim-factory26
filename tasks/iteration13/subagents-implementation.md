# I13 子Agent实施记录

2026-09-30。用户开工原话：“你可以按这个方案开工『I13-sub-agent简化与改进』了；注意你一直都可以自由git commit。”实现依据[已复核方案](subagents-plan.md)，包括最后的explorer、executor与advisor用途修订，以及永久禁止内联Agent Skill。

从当前`variants/pi-braid-i12`形成独立`pi-braid-i13`。五角色开放工具、独立上下文、子层最大3；移除生成器方法/运行约定追加；原生扩展修正无工具白名单时的再委派入口和自动边界文案；两个视觉角色使用glm-5.3-flash。executor并发写策略、SVC整体改稿、Context7/Exa/pi-fff及I13实验仍在各自范围内。

主Agent持有整合责任；有界子Agent分别完成原生两处源码的可冻结补丁，以及variant、公共接线的收尾核对、真实材料生成、文档和分范围提交。不编写或运行测试、模拟任务或模型探针。

实施前快照在`runs/iteration13/subagents-20260930/before/`，`start.json`记录授权、Factory起点及I12逐文件身份。工作区有大量其它任务修改，提交只纳入本批来源明确的文件或改动；不全仓暂存。I12冻结材料、运行、Braid与SVC独立仓库均不随本批部署或提交。

当前状态：本批源码和文档完成，编译及真实材料生成核对通过；未启动模型、实验或部署。I13仍是开发中的独立目录，下一批SVC选择和父入口整体改稿尚未实施，不能将其当作最终实验制品。

五角色description与正文采用已复核短文案，不声明tools，保留fresh默认、append、inheritProjectContext:false和inheritSkills:false；两profile设置Linux基础工具默认集合。生成器只替换角色技能和后台Bash扩展路径，不追加父profile、运行条件、三类workflow或agent-browser正文。每个角色加入独立svc-sub-agents技能发现入口，子层上限由run环境的PI_SUBAGENT_MAX_DEPTH=3接线。父profile仅简化advisor咨询内容一句，MAIN_SKILLS和build打包清单保持当前I12来源，三旧技能的整体退出归下一批。

原生窄补丁保留显式tools及能力上限语义，让tools未指定且没有allowedTools上限的child取得fanout；若已有allowedTools包含subagent，原有授权路径继续有效。自动child边界文案收敛为任务归属一句，深度、结果回送、联络、等待及模型预算管线未改。补丁已进入本地runtime构建列表、Linux Docker构建与runtime-source身份清单；未重建或修改冻结runtime。另补齐package_agent.py对I13的OTLP材料选择，保留工作区已有I11选择而不纳入本批提交。

两profile的vision和browser-operator均使用factory26-visual/glm-5.3-flash，visual descriptor复用既有GLM的text/image和兼容字段。独立visual URL与凭据环境引用继续可用，VISUAL_MODEL校验同步更新。

## 实际反馈与证据

Python 3.12.10编译通过，覆盖I13的build/main/run及公共runtime/package_agent入口；编译输出与源SHA保存在`runs/iteration13/subagents-20260930/compilation/python-compile.json`。原生worker保留原始npm、补丁适用与语法编译证据；收尾从保留runtime独立复制，再以`patch --batch --fuzz=0 -p1`实际应用新补丁，使用TypeScript 5.7.2再次生成两目标文件的JavaScript，诊断为空。该步骤是语法/emit编译，不是完整类型检查。身份见`runtime-copy-identity.json`，编译见`compilation/native-compile.json`。

真实需求使用`tasks/iteration11/run-audit/github`。以下两次执行均走I13标准main.py与真实材料生成流程，到prepare-only返回为止，没有启动Braid、Pi或访问模型端点：

| 材料生成 | 实际输出 | 观察 |
| --- | --- | --- |
| 共用endpoint，`--base-url http://127.0.0.1:9/v1 --prepare-only` | `materials-default/.factory26/20260930-222152-6619c468` | visual复用主endpoint与FACTORY26_API_KEY环境引用。 |
| 另给本地不可连接visual URL、占位凭据与VISUAL_MODEL=glm-5.3-flash，仍使用prepare-only | `materials-visual/.factory26/20260930-222312-e87727fc` | visual保留独立endpoint与FACTORY26_VISUAL_API_KEY环境引用。 |

路径均位于`runs/iteration13/subagents-20260930/`。每次生成的十份角色与源码经必要路径替换后的内容逐字一致，没有自动追加正文；工具白名单均缺省，fresh/append/两项inherit:false均保持，声明技能和后台扩展文件全部存在。每个template根目录只有agents、models.json和settings.json，模板及共享native home均无SYSTEM.md。两个visual descriptor均与既有GLM descriptor相同。完整观察，包括逐角色正文、字段、路径和哈希，保存在`material-review.json`；原生buildSkillInjection只生成名称、description与location已按源码核对，未通过模拟启动宣称真实child输入验收。

实施前后I12的25个文件逐一SHA相同，没有新增文件，见`finish-review.json`。冻结runtime的两补丁目标仍与原始npm一致，新补丁仅应用在证据目录的独立复制runtime。该副本来自旧Linuxruntime并追加本批补丁，只用于真实材料生成和语法编译，不代表本批已完成全新Linuxruntime构建。

## 提交与剩余边界

提交仅含新I13、新原生补丁、本批方案/记录及共享文件的本批增量。共享文件从HEAD构造本批暂存内容，保留其它历史dirty在工作区；不纳入已有model-exclusion补丁、I11接线、其它运行/Console/实验改动或下一批SVC方案。提交身份与路径清单记录在`runs/iteration13/subagents-20260930/commit.json`，该证据在提交后写入；未push。

真实三层委派及第四层阻断、contact_supervisor请求/恢复往返、结果逐层回送、GLM视觉API与executor采用均未发生；完整类型检查、全新Linuxruntime构建与打包执行也未进行。源码和材料正确性不能代替这些行为反馈。executor写入策略继续由[独立讨论](executor-followup.md)处理；SVC Agent Skills下一批方案已由主线形成，等待对应开工授权。本批没有新增调度器、自动worktree、调用配额或测试入口。
