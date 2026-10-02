# 关闭与自然收尾
用户已批准产品修正并开工。
关闭是对象状态变化，自关闭不再承诺额外 finalization；外部关闭作为普通输入通知负责人。已有执行自然结束，实际待处理消息仍可到达；关闭后的成员责任与历史身份保留。
Store 使用持久 event writer 判断作者是否为负责人，不让 LLM 新传身份参数。关闭事件转换到既有 Wake/direct_contact 接线，保留睡眠会话复用，不新增生命周期框架。旧 finalizing 数据继续可恢复，新事件不再创建此状态。
一次 Local 执行仍以所有工作项终态为边界；达到边界后不再发起普通讨论的新执行，已接受的 turn 与 reset continuation 必须自然完成。根开放时五分钟检查不变。
验证通过 Braid 编译和定向真实对象/调度边界测试；不写 Factory/Corpus 测试，不运行新的官网实验。现有旧 unit fixture 错误不无限扩大修复面。

## 实施与定向检查
移除新关闭事件的 finalizing 转移，Store 同事务区分自关闭与外部关闭。外部关闭使用 Wake/已存在的 direct_contact；关闭成员只有无真实待处理输入时休眠，晚到定向消息仍能再激活。旧归档 finalizing 可恢复，新的 claim 不再标作额外 finalization。
所有对象终态后，Store 停止领取普通输入；已有 reset continuation 例外，因为它属于已接受的执行。Local 等待 active turn、reset、continuation 与 materialization 落盘，不再直接触发 shutdown 中断末轮。开放新项或重新打开对象后，继续普通派发。
四项 Store 边界测试通过：自关闭保留正在运行的 turn 且无额外轮次；外部关闭在当前 turn 结束后仍投递；晚到定向回复可再激活且关闭范围不接受新讨论执行；已接受的 reset continuation 仍执行。原始日志 /tmp/factory26-closure-test.log，收尾复制到本 packet。

自编辑定向检查发现并修复一处原实现缺陷：complete_context_reset 把原失效事件既用于续接、又消费，导致新会话不能领取输入。现在保留原失效历史，为每次需要 continuation 的 reset 创建一条新的普通 Wake；不会再次失效或重绑旧 batch。两条真实 Store 自编辑顺序/重启测试通过，含旧写者通知前可继续、teardown 后被 fence，OPEN 续接与旧 CLOSED/finalizing 续接。

Linux release 构建完成（1 分 06 秒），源码与二进制留在 runs/e20260928-product-hardening，build log 同目录；本轮未启动新 benchmark，未提交。
源码 tar SHA256 defac89c76ee940f9c08e744ddf48ef86ba80227222cc72ad6cccaf26f3ecb23；Linux binary SHA256 f544b87ec165607f928835fe369dd8297191bd9e69100f10a129dee192f2ec01。
