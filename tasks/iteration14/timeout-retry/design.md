# Pi瞬态错误的退避与终态边界

本方案针对已完成组合实验中两次504后审阅会话长期保持running的问题。根因、版本字节及原始时间线归[诊断报告](../../../runs/deadline-20261003/combo-restart-20261004/timeout-retry-diagnosis/diagnosis.md)。本轮不改变代理超时和供应商fallback；目标是使已有Pi重试走到正确位置，并使耗尽后的原生失败可靠结束。

## 已观察行为

代理向当前主路由发出请求后90秒未收到响应头，返回本地504。Pi识别该错误为可重试，默认退避预算为3次、2/4/8秒。然而Pi在准备退避前等待agent_end扩展。subagents与background-bash拿不到原生willRetry，执行终态后台等待，导致退避没有开始。Braid等待agent_settled才完成turn是正确边界，不能改成见到message_end/error就中止合法重试。

实际bin/pi加载bundle，而旧补丁修改dist/core，形成修复代码未执行的制品差异。因此修复包括生命周期与生产接线，不能只改一个扩展或只改未加载文件。

## 采用的合同

Pi在等待agent_end钩子前用唯一原生判定计算willRetry，同一个元数据同时传给extension和RPC，不在扩展重写HTTP分类或重试预算。subagents与background-bash遇到willRetry不等待active后台工作自然结束，保留完成结果及所有权，不把跳过等待标为成功。实际退避仍由Pi负责，保留既有次数、取消与预算。

重试耗尽或不可重试error应保留模型原错误、已经完成的后台结果与尚active的作业引用，不靠自动follow-up绕过预算；原生逻辑有界settle为failed。active作业按既有session所有权与shutdown合同处理，不任意杀服务，也不等待常驻服务自然退出才报告模型失败。正常stop路径仍执行必要的有限任务收尾。cleaner工具事务仍只在正常完整响应与来源校验成立时提交，失败与重试不会变成committed receipt。

运行入口统一到实际可用、已打补丁的非bundle dist/cli.js及依赖；若该发布版本不提供兼容入口，则从固定源码构建同一补丁bundle。只采用一条运行路径，不维护两份生命周期实现，不运行时替换压缩bundle字符串。冻结记录包括入口与依赖字节、两个插件补丁及运行制品身份。

代理不自行重放header timeout的未知请求；客户端原生退避是现有行为，保留请求身份和具体错误。未收到headers不证明供应商未生成或未计费；修复不声称消除供应商504，只避免瞬态错误卡死会话。

## 实施与验收

`combined_sfp7_owner`持续持有源补丁、生产接线、编译、完整组合制品与版本证据。`evaluation_preparation`持GitHub三阶段及12306、携程共5个job及逐题评分，直接消费修复owner冻结交付。用户完整指示授权修正后执行这批benchmark；矩阵不改变模型/供应商，实际容量、公开需求、预算及制品身份在启动前冻结。用户已明确采用sfp7与WSL两机，让五题全部并发；每run4GiB无额外swap，现有sfp7两题不重启，剩余题按两机实际余量分配。

不运行Factory/Braid设施测试、探针或smoke，不用固定错误响应伪装真实故障验收。编译与真实授权benchmark取得反馈。出现自然瞬态故障时，读取有界原生证据确认retry metadata、退避、新完整响应、最终settled与Braid状态一致。没有自然故障时，只报告正常路径验证及编译/字节合同核对，故障分支运行验证仍缺失。

GitHub三阶段采用确切公开输入独立生成并送自测站；12306与携程两题Web生成后冻结应用，再以各自官方本地快照评分。生成Agent不见测试正文及隐藏评分反馈，生成与评分耗时、费用、版本和应用哈希分别记录。完成本轮结果后汇报，不自动增加下一轮。
