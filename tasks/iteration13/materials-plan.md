# I13：正文投影与根提醒整理

2026-09-30。用户明确授权：“‘正文折叠与根提醒整理’可以开工”。本批源码与文档已完成，编译及已有归档只读读取通过，新增行为的实际反馈边界见末节。范围沿用下面的具体LLD与独立预演；不启动I13实验或修改冻结I12。
依据[修复方案第四组](repair-design.md)及[独立预演](materials-rehearsal.md)。CLI和description-only核心已有独立实施结果，不重复开工。

## 要消除的负担

原始材料可以保留完整，却不需要在每次重建时全文进入当前输入。作者用标准details表达哪些材料按需展开，Braid只做投影，不判断其内容是否无用。
同时，周期提醒是Braid自己生产的同类材料；持续保留旧提醒没有新增信息，应在新提醒提交时替代旧条目，同时保留参与者回复。
正常原生resume仍保留历史，本批不把隐藏/折叠误称为删除已经送进会话的文字。

| 问题 | 具体改法 | 保持的边界 |
| --- | --- | --- |
| description/comment中的长原件常驻重建输入 | 在模型投影正文入口识别完整details，只保留其summary。多容器与嵌套按原文结构处理，代码示例不折叠；无法确认完整结构就保留原文。 | SQLite原文与CLI body不改；不摘要、不修复任意HTML、不自动插入details。 |
| 预算降档可能先截断闭合标签，让折叠失效 | References档先投影折叠，再截短，renderer不再解析已截短正文；沿用既有20%估算与硬上限。 | 不添加新档位、预算参数或自动重建。 |
| 系统根提醒重复堆积 | 按根进度提醒的创建活动及system_author识别此前可见提醒，同一事务逐条hide，再创建并投递新提醒。 | 不处理其它Braid状态评论、不隐藏成员回复、不resolve整串；仅原本的一次新提醒通知。 |

## 最小技术范围与顺序

1. `sources/braid/src/context.rs` 增加投影正文helper，接Issue/PR description和模型comment路径；CLI原文路径保持。复用comrak提供的HTML来源范围，匹配完整details/summary结构，不增加依赖或HTML修复框架。
2. `reference_projection`在description截短前调用同一helper。References renderer直接使用已投影且截短的正文，避免不完整代码标记被二次解释。不得改 `filter_html_comments` 的语义，因为它还参与正文有效变化比较与Closes提取。折叠区正文实际变化仍属于description变化。
3. `sources/braid/src/objects.rs::root_idle_tick`沿用原Immediate事务、空闲条件与提醒轮换计数。只处理具备 `commented / root progress check` 创建活动、issue:1来源和Braid系统作者的可见旧提醒，保存hide原因和活动；不调用会额外发通知的通用hide入口。
4. 更新Braid现有context/local技术说明并编译。不得扩至角色、SVC、variant配方、Console部署、冻结I12或新的实验。

## 反馈安排

沿用已批准的反馈边界，不增加测试、mock或专用run。编译确认接线，实际 `braid context` 与CLI原文读取对比确认已有材料的投影；不足以覆盖的输入明确未验，不补写I12对象来凑反馈。
提醒的实际采用需要后续获授权运行经过自然周期，观察旧提醒hidden、回复保留、新提醒唯一可见、一次投递及隔次packet节奏。当前I12已由用户再次暂停，本批不以编译或阅读实现声称这部分已实际验收。

独立预演已经指出两个必须保留的设计约束：投影与描述比较分开；根提醒与其它Braid系统评论分开。没有新增数据库字段、调度模式或通用整理策略。

## 实现与反馈（2026-09-30）

改动限于 Braid 的 `src/context.rs`、`src/objects.rs` 与现有 context/local 技术说明。正文投影使用 comrak 的 HTML 源码范围和显式标签栈，保留首个直接 summary；注释、属性引号及 raw 区跨空行延续，坏配对不借后续闭合标签补齐。嵌套容器通过省略区间合并处理，不递归重解析或增加依赖。References 先投影再截短，并直接渲染结果；实际完整正文读取入口明确指向 `view --json body`。

根提醒在现有 Immediate 事务中精确筛选全部可见旧提醒，逐条记录 hidden、替代理由和 hide 活动，然后沿用一次新提醒投递。创建活动计数、五分钟空闲条件和轮换配方保持，成员回复与其它系统评论不在更新范围。

`cargo check --locked`、`cargo build --locked` 和差异空白检查通过，保留原有13条 dead_code 警告。真实 I11 归档只读操作覆盖 Issue #1、PR #23 的 Full 与 References 输出，及 Issue/PR/comment 原文读取；三份 CLI body 与现存数据库原文一致。所有命令成功，没有写入归档或运行对象。

定向查询了78份本地 Braid SQLite 归档的现存 description/comment，没有 `<details>` 材料。因此上述读取只证明普通投影、预算档位及原文路径可用，不能证明多容器、嵌套、畸形标签或字面区的实际折叠效果。实现前预演与实施中静态边界审视分别收敛了直接 summary、跨节点字面区及非法属性处理，也不能代替实际运行反馈。

新增折叠边界、根提醒自然到期替换、回复保留和单次通知仍待后续获授权运行验收。未增加或运行测试、mock、probe/selfcheck，未启动模型，未部署到冻结 I12，未提交。当前 I12 已由用户再次暂停；20:52 CST两题实际API确认 paused=true。

最终开发 binary SHA-256：`b6cbd4e4b4c2ad7123c3fa2b42961c4a6c3f89118516e8247c99cee0acf60eaf`。

本批原始证据及源码开工前副本在 `runs/iteration13/materials-20260930/`：`start.json`、`before/`、`check.log`、`build.log`、`existing-details-inventory.json` 和 `cli-readonly.json`；CLI完整stdout分别保存，binary身份以最终回执为准。
