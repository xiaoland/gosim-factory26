# 设计阶段验收方案

状态：Human已批准，作为后续实施与实验的固定验收方案。本页不是现有通过声明；正式隐藏测试结果只能说明应用表现，不能替代Harness运行合同的资格验证。

## 主张与证据

| 主张 | 最小可信证据 | 不足以证明 |
| --- | --- | --- |
| Agent只需GitHub式心智模型 | 真实运行输入和一个场景中，Agent只用issue/PR/comment/reply/assignee完成拆分、讨论、实现与合入，输入中不出现Braid或agent-profile | 源码中存在同名CLI |
| 内部profile正确投影为assignee | 同一内部配置支持两个独立work-item；Agent依据可见成员能力说明用GitHub式flags指派Issue，全程不查询或提及profile；指派后目标Agent实际开始工作 | profile数量、默认assignee字段或只创建idle session |
| task packet服务当前work-item | 根项与子项各能恢复自己的packet；原生sub-agent消费局部材料；跨项通过comment/ready commit交付，不依赖读取其它脏worktree | 多个worktree都有同名`tasks/`目录 |
| SVC导航既可发现又不激进 | 新会话仅凭入口能说明主要内容、task packet意义/模式、V&V触发；简单任务不全量读取Corpus，非简单任务建立/接续packet | 文案含`svc lookup`命令 |
| team-vv只增加canonical V&V装配 | 两variant的ZIP manifest除V&V装配/有效digest外一致；运行证据显示增强组实际消费canonical内容 | 目录中存在verification文档 |
| 视觉输入可用 | Pi parent→vision和browser-operator各对一张已知图片运行，归档的原生消息确认image block，返回包含可判定视觉事实与源路径 | 模型目录宣称支持图片 |
| Pi生命周期边界正确 | 同一最小场景在原生、扩展、Adapter三层的身份、停止、重建、失败恢复结果可对照；修复后的最早异常层通过且未破坏其它层 | 单元mock或进程退出码 |
| 官方ZIP符合运行合同 | 从新ZIP解压，在固定版本local simulation中以平台环境变量执行`main.py`，通过标准frontend/backend部署并保留manifest；官网同一bytes可保存snapshot | 本仓库直接执行factory.py成功，或只靠local-only deploy.sh启动 |
| 混合controller可恢复 | 用无模型替身/可控fixture模拟hosted/local成功、可恢复传输错误、终态失败和进程重启；每个矩阵项恰一次形成可追踪终态，不重复不确定写 | watch脚本能轮询一个run |
| 并行提高吞吐且不混淆证据 | 至少两项本地真实生成重叠运行，独立输出、package hash、模型身份与结果；官网遵守实际slot限制 | worker配置值大于1 |
| 实验结果可比较 | 同一冻结Harness revision及明确variant差异完成Keep/BookStack；报告通过率、官方得分/本地分数、成本可归因性、耗时和设施失败 | 不同revision的八个分数拼表 |

## 验收顺序

1. **静态资格**：解析所有内部profile/native角色及模型材料，拒绝未知字段、错误模型ID、重复原生角色名、缺失description、无消费者的MCP/skill和不被模型支持的reasoning/image配置；检查运行时指引不泄漏Braid、profile或preset。比较team/team-vv effective manifest只含预期差异。
2. **模型接口spike**：每个拟用模型只完成最小文本工具调用；视觉模型额外完成本地图片输入和浏览器截图。记录实际协议、reasoning参数、context上限观察与错误形状，不用完整应用验证接口。
3. **Pi分层spike**：原生RPC→扩展→Braid，覆盖正常turn、内部sub-agent、上下文重建、明确失败、interrupt/teardown和resume。先收敛所有权，再改实现。
4. **协作旅程**：给一个Factory task建立一个根Issue，用小型隔离仓库运行可选sub-issue和PR。Agent自主决定是否拆分，并用`--assignee`或原子`--remove-assignee/--add-assignee`把work-item交给另一个Agent；验证单active owner、旧writer fence、目标恰一次新采样、输入不暴露profile、packet恢复、comment交付、ready/merge和根完成。
5. **包与runner资格**：同一ZIP先过结构/hash/凭据/网络边界，再进固定local simulation的prepare-only、无模型deploy fixture、真实模型单题和标准frontend/backend部署检查；不以local-only deploy.sh判资格。最后用同一bytes在Competition做一项练习运行。
6. **controller故障场景**：先用fixture证明snapshot→create run→start逐写持久化、未知写核查、未知status、重启、终态与产物分离，再运行官网一槽+本地多槽的真实混合队列；不以人工轮询补完成。
7. **固定实验矩阵**：冻结package与运行配置后执行批准的全部variants×Keep/BookStack。设施问题修复会使相关资格过期，重新资格后用统一revision取得比较结果；应用低分是实验结果，不自动重采样。

## 失败分类与停止条件

- **设计不成立**：Agent需要理解内部Braid/profile状态、packet必须跨脏worktree同步、assignee能力说明无法支持有用指派，或Pi所有权模型与所需停止证明冲突。返回设计，不进入局部补丁。
- **接口不成立**：指定模型ID、图片、tools或官方API不可用。保留证据并调整配方/接口；不静默替换为Qwen Max、Kimi或Playground。
- **实现缺陷**：设计和接口成立但代码不满足。开工授权后在当前闭环修复、复验并继续。
- **外部设施问题**：官网维护、Meter服务或runner镜像不可得。完成本地独立工作并保留可恢复队列；只有确实需要Human/主办方输入时暂停。
- **实验终点**：既定矩阵每项获得标明venue的完整评分，随后汇总并停止。低分本身不触发同轮修改。

实施验收完成后仍需报告残余：官网与正式初赛环境差异、共享Meter key的成本归因限制、未纳入的Web六题、模型随机性及一次矩阵无法支持的单因素因果结论。
