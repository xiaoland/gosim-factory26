# 方法分支覆盖

本轮是现有最终修复复审的增量，不是两题全量运行重审。源码阅读仅核对修复机制与边界；全部采用/质量/成本效果未做新行为验收。

| 范围 | 本轮实核 | 复用及限制 |
| --- | --- | --- |
| M01 | documentation全文；七技能互链；两build/run、harness符号链接、assemble/copy_skill；五profile/对应角色内容比较 | GitHub session03原生L23完整thinking直接回看；Sheet items c111/PR19正文直接回看。其余跨链/最终树因果复用两题报告，不冒称本轮动态复现。 |
| M02 | verification入口及四篇reference全文，金字塔/保存设置例/盲区 | 旧窄PASS、同属性反证来自既有报告；未观察新模型如何选层。 |
| M03 | 七技能入口；investigation三reference、design四reference、sub-agents全文、packet三reference、implementation三reference | task-packet模板仅实读index、plan、packet，其余旧模板不逐字复审。案例可理解性是文本判断，无采用实验。 |
| M04 | planning全文、workflow迁移导航、task-packet规划入口与模板提示 | 已核制定/保存职责不重叠；未执行预演或验证应用计划。 |
| M05 | run-analysis全文及Sheet method-retrospective全文；两题coverage来源/范围声明 | 复用旧审查的实际返工记录，未取得独立审查耗时或Luna质量对照；不重新全读原生。 |
| R02、R03、R08 | run.py公共条件/根prompt、五主指令、角色继承配置；两run除常量相同 | 当前装配链成立，fresh输入实际生成与Braid设计/实现流程采用未验。 |
| R04、R05 | product、check-design、根分工prompt；session03 L23直接证实已知冲突仍选派生权威 | 后续中央seed已修及其余遗漏复用GitHub报告；不归因隐藏评分。 |
| R06 | technical、implementation、check-design/documentation；Sheet契约/PR19原正文 | 双算法与pivot静态路径复用Sheet最终报告；本轮不再读冻结应用或重做终态判断。 |
| R07 | interpreting-results同属性反证规则；vision全文 | 旧父读取vision及错误消费链复用既有Sheet报告，未新看截图。 |
| R09、R10、R12、R13、A04 | advisor/executor/explorer/vision/browser全文及五组一致性；skill装配与workflow嵌入 | 零调用不证明阻断；工具实际往返、guard/observer纠偏由运行时线审，不以角色存在宣称可用。 |
| R11、R17 | task-packet旧任务恢复入口、主指令保留ID/先查旧结果、documentation现态/历史分开 | observer与Braid可编辑上下文机制复用旧目录并交运行时线；不把方法文字视作持久化保证。 |
| R22、R26 | 主指令接管/候选前提消费；interpreting-results按artifact/条件复用；repeatable-checks首轮退出信息 | helper行为不重跑；旧源码/运行证据复用前轮，当前技术实现交运行时线。 |
| R27、R28、A08–A11 | workflow前置成功、外写读回、归属，debugging原动作状态/空过滤，RUN_CONDITIONS浏览器与TMP条件 | 技术清理/helper/PBB保证不能由文档替代；本轮未实核helper全部实现。 |
| A06、A07 | RUN_CONDITIONS明确Node20/npm交付与工具环境分开、不指定TS/Vue；技能装配静态链 | 不重审整个依赖构建、无新制品/正式启动；保持先前兼容效果缺证。 |
| A12 | 没有方法增量，复用旧覆盖的官方类型核对 | 不重新联网/执行HyperFormula，不能当本轮独立证实。 |
| 其它R/A/Z/L | 非本分支责任 | 运行时分支/主线整合，不作未读却通过声明。 |

长合并输出曾截断；所有本文作出增量判断的方法正文均随后分段补读，角色以完整基准与无差异文件比较消费；历史两题长报告只定向读取相关章节，不将其截断部分计为本轮已读。只写methods-current.md、methods-coverage.md，未改他人文件。
