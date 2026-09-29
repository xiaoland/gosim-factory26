# 根设计与 Issue/PR 隔离：现场核查

本次只读核查了两题 local_items、sessions.json 索引中的原生工具调用、origin.git 分支内容。
时间以下为 UTC；原生记录有截断/缺头，结论限于可见材料，不宣称全量没有越界。

## 根设计

GitHub 根会话 `2026-09-29T04-24-34-972Z_01a0eb68-479c-72ef-b9ea-288545453828.jsonl`：04:28:48 写 product-plan（第7行），04:29:58 写 architecture（第14行），04:30:22写seed-data（第16行），04:30:35写acceptance-plan（第18行），04:31:39按advisor意见追加架构修订（第23行），随后创建基础PR。architecture含技术栈、目录/API/权限/内容模型/seed/UI/质量设施的共享契约；这些已出现在develop。设计不是只有标题。

Sheet 根会话 `2026-09-29T04-24-35-071Z_01a0eb68-47ff-70ef-b663-1ca63677a7a9.jsonl`：04:37:49编写根说明（第28行），04:38:40编写共享契约（第35行），04:39:27创建并指派基础PR（第41行）。正文包含需求取舍、种子、前后端与公式引擎决策、依赖分解、验收安排；评论承载数据模型/API/ARIA/持久化契约。设计存在，但PR文件树没有docs架构入口，只有tasks/pr-2-base/packet.md；项目文档系统落实弱于GitHub。

## 隔离的实际证据

- Sheet根glm-1写设计及协作材料，另在/tmp/sqlite-probe做依赖兼容调查。PR #2的deepseek-2在pr-2工作树写package、shared/types和前后端源码；04:44:40开始写脚手架、04:45:02写backend/src/config.ts。没有在可见根会话中发现产品源码实现。
- GitHub根写设计文档；PR #2的deepseek-2于04:33:57写backend/src/config.js，随后完成基础实现。基础PR已合入develop。
- GitHub Issue #5的glm-4于05:26:29发布技术/验收方案，05:26:56准备PR材料，05:27:15交接实施计划/排障/实现/验收；PR #11的deepseek-5于05:30开始写其packet和仓库模块源码。
- GitHub Issue #3的deepseek-3先写identity设计packet与视觉说明，提交的是这些文档，再于05:33:13创建PR；PR #12的glm-6于05:37:27改身份模块、05:38:04写找回密码页面。当前未见“先在Issue实现业务代码再派PR”的旧模式。

## 尚不能宣告完成的部分

分工隔离成立，不代表整个流程都完整。两题基础PR的可见packet首次写入均晚于首批源码（GitHub04:39，Sheet04:50），尚不能证明“计划及预演先于实现”已经完整发生；需要继续查前置命令/讨论，不能仅凭packet写入时间反判没有计划。后续未启动的Sheet子Issue、GitHub其余模块，以及最终整合验收都尚未取得执行证据。

Sheet自研公式引擎、默认网格规模多次调整等设计判断的质量，不在本次隔离核查结论内；“存在架构设计”不能等同“架构正确或已完整落实”。

[Sheet PR #2 完整文件树](sheet-pr2-tree.md)。原始证据位于WSL实验e20260928-03-check-receipts原generation/runs下，各题template/.factory26的braid-state和work/native-homes中。
