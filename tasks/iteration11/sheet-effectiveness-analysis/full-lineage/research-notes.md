# 过程机制的一手研究参照

只作为构造问题、区分解释和提出可反驳预测的参照；研究对象多为人类写作/沟通或软件模块，不能据此断言LLM内部心理机制相同，也不能用理论名称代替本run的消息—动作—结果证据。以下均在2026-09-30直接打开原论文文本，未依赖二手摘要；只定向读列明段落，不宣称全文综述。

| 来源与读取位置 | 原研究提供的区分 | 本次可检验问题；不是已证因果 |
| --- | --- | --- |
| Flower & Hayes, 1981, *A Cognitive Process Theory of Writing*, pp.366–371；[作者上传原论文](https://www.researchgate.net/publication/239552089_A_Cognitive_Process_Theory_of_Writing)（网页索引日期2004不作发表日期，原扫描标Dec.1981） | 写作中的计划、表达、审阅可反复交织；已经写出的文本也会约束后续选择。按完成阶段划分不能充分描述过程。 | 查看packet/description修订究竟重新解决接收者的当前问题，还是只延续先前正文和候选引用。必须由实际改动与新会话消费区分，不能因“维护文字”便判无效。 |
| Clark & Brennan, 1991, *Grounding in Communication*, pp.128–135、140–145；[原章节扫描](https://worrydream.com/refs/Clark_H_1991_-_Grounding_in_Communication.pdf) | 发出消息与共同确认足以开展当前行动不同；相关下一步行动可提供理解证据。媒介的顺序性、可回看性和可修订性改变沟通成本。 | v1.3发布/投递/实际采用分别是否发生？hide/resolve后点读能否取得原答复？自编辑后接续者能否识别作者与已包含变化？实际使用共享函数可比再发“收到”提供更强的消费证据，但不等同于需求正确。 |
| Malone & Crowston, 1994, *The Interdisciplinary Study of Coordination*, §2.2、表1，pp.90–95；[作者上传原论文](https://www.researchgate.net/publication/5176072_The_interdisciplinary_study_of_coordination)（按原扫描ACM 26(1), March1994，不沿用页面January1993） | 协调研究区分共享资源、生产者/消费者的前置、传递和可用性等依赖；“产物产生”与“接收者可用”不是同一约束。 | 区分真实B→C接口前置、错误的“两profile=两人”容量假设、只通知Issue未通知实现PR，以及原语已发布但调用方未消费。不能由并行越多推断越好。 |
| Parnas, 1972, *On the Criteria To Be Used in Decomposing Systems into Modules*, pp.1055–1057；[原论文](https://wstomv.win.tue.nl/edu/2ip30/references/criteria_for_modularization.pdf) | 模块划分标准影响独立开发和变更传播；以隐藏设计决定组织接口，与按处理步骤切分不同。 | 分工后共享网格/公式/结构接口是否真正隔离变化？晚期E更改排序语义时，谁掌握原语、谁修改消费者？这是观察接口/责任的镜头，不是要求Braid工作项与代码模块一一对应。 |
| Shannon, 1948, *A Mathematical Theory of Communication*, introduction p.379（重印PDF p.1）；[原论文重印](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf) | 论文处理消息在信道中的传输，并明确将语义与该工程问题区分。 | 本次只量化字节、重复身份、事件可见性等可测事实；不把token数当有效知识量，不称hide/摘要具有已测“语义熵损失”，不把更多文本视作更充分理解。语义义务须按需求与消费者动作人工核对。 |

读取记录：Flower/Hayes原文的过程模型、任务环境与已写文本段落；Clark/Brennan呈现/接受、相关下一轮、共同努力与媒介约束段落；Malone/Crowston生产者消费者的前置/传递/可用性及表1；Parnas两种划分、Independent Development和The Criteria；Shannon引言。未把ResearchGate页面下的后续论文摘要当成这几篇原文。

外部研究不能证明此次分数根因。主报告仍须以同时期原始输入、可见选择、具体动作和返回来成立；缺少这些链节的类比仅保留为假设。
