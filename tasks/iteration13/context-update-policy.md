# I13 对象更新与上下文重建

2026-09-30。用户明确：“description重建单独保留，但是仅有description，description之外的comment、relationship、title等都不重建。”
这是对先前方案的产品行为收敛；用户随后明确“我同意你对上下文重建的这套判断，可以应用修改了”，已独立开工，实施见 [context-implementation](context-implementation.md)。不修改冻结I12。

## 行为规则

| 变更 | 发起操作的会话 | 其它受影响协作者 |
| --- | --- | --- |
| description实际可见内容变化 | 保留既有重建语义及终态续接判断 | 描述属于其上下文依赖时重建 |
| comment创建/编辑/隐藏/恢复/解决/删除 | 保存操作及回执，不自通知、不重建 | 按原参与/订阅关系发必要的增量信息，不重建 |
| title、relationship等对象元数据 | 保存实际状态及回执，不自通知、不重建 | 需要时获知变化并按CLI读取最新对象，不重建 |
| 人工Console修改 | 没有可排除的模型发起者 | 使用同样字段规则；人工修改description仍重建 |

发起者指执行这次修改的实际Braid成员会话，不是只比较评论的历史作者，也不是比较模型/profile名字；不用UUID向LLM表达这些判断。
编辑别人发表的评论也不向操作者回送自己的操作；其它协作者是否接收仍由原有关系决定。
真正新建会话时从最新对象组装上下文；恢复既有原生会话时保留其实际历史，通过增量消息及CLI读取当前状态，不把新计算的投影冒写为已发送的上下文。
hide/resolve立即改变CLI/Console和后续投影；当前原生会话已经读入的旧文本不会因此从历史中消失，下一次实际重建时生效。
新指派/取消指派、原生会话确实不可恢复等属于生命周期，保留必要的创建、停用和恢复。
同一仍可恢复的成员不能仅因休眠期间title/comment/relationship改变、完整投影hash不同，就把新建原生会话称为生命周期例外；它仍须遵守description-only。独立预演已确认provider的resume接口支持保留原生连续性。

实施先建立description-only的Invalidate分类，再复用按assignment revision归属的pending Invalidate判断休眠期间是否真的改过描述；不新增历史diff协议或数据库字段。恢复事务带出该事实，dispatch与store的完成记录同步区分resume旧上下文和start新上下文。实际description失效才改用当前投影；混批中的评论输入不被一并消费。此规则用于I13新状态，不解释或迁移I12旧混合事件。

## 开工前定位

以下保留修复前的因果依据；当前代码和反馈归[实施记录](context-implementation.md)。

`sources/braid/src/objects.rs` 的 `discussion_changed` 为可见评论修改产生Invalidate，传播到当前对象及关联PR。
它在普通评论投递处已排除作者，但Invalidate路径没有等同排除；`emit_with_id`只把自身Wake改成OriginEcho，不处理自身Invalidate。
因此“已经有自通知排除”不能证明“自编辑没有重建”。
`edit_comment`、`comment_visibility`、`hide_comments`、`resolve_comments`汇入该路径；对象 `edit_with_parent_and_assignees`、`link_in`等还需在同一实施切面核对字段/关系分类。
独立预演已排除活动会话的完整投影hash自动Invalidate旁路；但 `group::dispatch` 恢复休眠成员时会因hash不同而start新会话，须按上述产品规则一起处理，不能只改CLI发事件。

## 实施准备与反馈边界

在既有更新分类入口按实际字段区分，不为每个CLI另加例外，也不引入模型判断“这是新工作还是维护”。
title+description同一次编辑仍依description处理；description内容无实际可见变化不额外造重建。
混批中的真实描述变化、新评论以及生命周期动作分别保留，不因消除自回送而吃掉其它成员输入。
实际验收观察对象变化、事件、原生会话身份及原始CLI回执；只出现“没有新采样”不能证明没有重建。
源码实施已独立获准；运行仍保持原范围，未获准恢复I12或启动新实验。
