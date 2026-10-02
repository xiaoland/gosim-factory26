# exploration-tools：工具知识归属 explorer

状态：2026-09-28 调查、方案与源码归属调整已完成，待下一次材料刷新进入真实运行。用户指出它应直接成为 explorer 系统/角色提示词，主 Agent 赞同；本文已据此修订，不保留与当前方向竞争的旧建议。

## 问题与决定

exploration-tools 约34行，主要告诉 Agent 何时使用 rg、ast-grep、Context7、Exa，以及可直接执行的 mcporter 命令。
这些知识是 explorer 完成专业调查所需的工作知识，不只是一个可选技能。
现有角色职责与输出边界写得清楚，却把专业知识放在独立 skill，再在 native_files 中强制拼回角色；多了一次组织和加载的间接层。
同一正文还无条件注入 executor 和 advisor，扩大了并非它们每次都需要的工具说明。

方案：删除独立 exploration-tools 技能，把通用调查工具知识直接整合进 explorer 角色提示词。
工具选择按信息缺口组织，不按固定流程依次使用所有工具。
其余角色仍可自行完成简单查询；不要求每次读文件都委派 explorer。

## 三种材料的归属

| 材料 | 归属 | 处理 |
| --- | --- | --- |
| rg 的文本定位、ast-grep 的结构查询、Context7 的已知库 API 查询、Exa 的来源发现与抓取 | explorer 角色知识 | 连同短命令例子直接进入 explorer；提升 description，使主会话知道可委派哪类问题。 |
| Handsontable/HyperFormula 的专门版本参数与 API 资料 | 既有领域技能 | 放回领域技能，explorer 根据当前库选读，不复制整个领域手册。 |
| mcporter.json 三服务地址、MCPORTER_CONFIG 环境接线 | Harness 运行资源 | 不进入角色提示词；删除技能目录时迁出配置，并同步正常启动、打包与恢复入口。 |
| 调查如何形成判据、对比假设、结束调查 | SVC Investigation | 保持既有方法来源，不吸收特定 CLI 或 MCP 命令。 |

## 最小实施范围

- 两个活动 variant 的 explorer 角色材料：直接给出通用工具知识，保持 fresh、只读范围和有出处的返回要求。
- 两个 variant 的 build.py、MAIN_SKILLS、各角色 skills 列表：移除 exploration-tools。
- native_files：移除通用技能正文拼接，保留各角色对应的 SVC 方法。
- MCP 配置迁出被删除的技能目录，同步两个正常启动入口与 recover_completed.py；服务端点和可用工具保持不变。
- Handsontable/HyperFormula 既有技能接收各自的领域查询例子。
- 更新依赖来源表、技能目录说明；不新增另一组调查技能，不预制应用源代码。

## 调查依据与限制

主线实际执行冻结 runtime 的 `mcporter list exa --schema --json --no-oauth` 成功，工具为 web_search_exa(query,numResults,objective)、web_fetch_exa(urls,maxCharacters)。
因此当前 Exa 命令例子不是未经核实的旧 API 名称，不能以“自编所以错误”删除它。
原始 schema 保存于 WSL /tmp/factory26-exa-schema.json。

DeepSeek attempt-06 主 Pi 工具记录可见大量 grep，未见 rg、ast-grep、mcporter；也未见真实 Pi explorer 委派。
Flash 对照有一次 executor，但主要执行共享基础代码。
这些观察说明尚无证据证明该材料促进专业工具使用，不能推出工具没有价值或单靠改提示词就必然增加有效委派。
角色 frontmatter 与正文都提到技能，但未核对实际加载展开，不声称正文被完整重复注入两次或给出未经测量的 token 节省。

证据入口：harness/skills/exploration-tools 全目录，两个 variant 的 run.py、build.py、agents 配置，submission/recover_completed.py，以及 [原生子代理使用](../../experiment-infrastructure/cells/subagent-usage.md)。
attempt-07 已冻结启动，包含视觉职责修正和设施热修复，不包含本项迁移。

## 实施记录

按以上边界直接改动两个活动 variant：explorer 角色持有工具知识；独立 skill、主会话/子角色技能列表和重复正文接线已移除。
每个独立 variant 的 tools/mcporter.json 保留原三个服务配置，正常启动和恢复入口同步使用包内位置。
Handsontable 与 HyperFormula 既有技能接收各自的文档查询例子。
相关消费者文本检查、Python 编译与 diff 格式检查通过，未运行 Factory 测试。
同时将真实观察到的 subagent.agent/Braid 指派名混用，以简短使用说明写在 Pi 成员指引中；不创建固定角色流水线。

