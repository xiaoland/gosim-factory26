# Braid：Bub 原生 Agent 接入

2026-10-01。用户新增：“我还想添加braid对bub、alma agent的支持（不属于i13，也不阻塞）”，随后明确“alma是yetone开发的”。这是独立Braid能力方向，当前完成 Bub 原生接入及有界接口反馈，不改变I13配方、冻结运行或实验安排。

目标是让这些Agent承接Braid工作项，保持原生工具、会话与恢复能力。当前Braid的接入边界见 `sources/braid/src/provider/mod.rs` 的AgentProvider及对应session层：创建/恢复会话、传入profile与工作上下文、启动turn、增量投递、取消、终态/断连和已消费消息的证据。不能把“存在模型HTTP端点”直接等同于具备可用的Agent会话接入。

## 当前授权与下一步

用户已明确：“你也可以开始委派接入bub了。”本次授权覆盖Bub provider、必要的配置与会话生命周期接线，以及对应文档和实际接口反馈；由GPT-6.1-Sol / extra-high子Agent实施，可限定提交，不push。不改变I13默认provider或实验安排，不运行模型或启动已暂停的实验。

用户同时指出“alma实际上不开源，也没有明确的API，可能我们无法接入”。Alma暂缓，等待有文档支持的外部Agent驱动接口，不依据模型配置API猜测执行协议。本次不实现Alma适配。

先核实并固定Bub及ACP插件版本，复用Braid既有provider/session契约完成最小接入。对创建、恢复、工作目录、指令分层、取消、忙时投递、事件与完成证据作明确映射；无法由原生协议支持的能力必须显式报告。编译、真实CLI与无模型协议反馈用于验收，模型运行行为另记未验证。

## 已有调查定位

| 对象 | 已有入口 | 尚需核实 |
| --- | --- | --- |
| Bub | 暂按 [bubbuild/bub](https://github.com/bubbuild/bub) 定位；[官方ACP文档](https://bub.build/docs/tutorials/acp-server/)提供bub-acp-server、stdio、会话历史重放与稳定BUB_HOME说明。 | 目标版本及插件源码中的恢复、取消、工具事件、工作目录和指令分层能否满足Braid契约；用户若指另一个Bub则据其补充改正。 |
| Alma | 用户确认yetone；[发布仓库](https://github.com/yetone/alma-releases)指向 [官网](https://alma.now)，[插件API](https://alma.now/docs/plugins/api-reference)提供chat/events/workspace等扩展入口。yetone的magpie也列出Alma本地API，但这仅证明其模型配置入口存在。 | 可供外部宿主驱动的Agent会话协议、无界面运行条件、认证、流事件、恢复与取消；不能据配置API假定已支持完整执行。 |

先行调查仅阅读本地接入契约与官方资料。随后沿本次开工授权，在隔离目录安装固定源码的 Bub 与必要插件，完成 Braid provider 源码与权威文档；未运行模型、修改全局 Bub 安装或调用 Alma 会话。当前Console生命周期收敛归[Console任务](../braid-console-control/packet.md)，与Bub接入独立推进，不将两者并入I13的完成条件。

## 当前完成状态

Bub 已作为第三个原生 adapter 接入 Profile、local 请求和 session factory。每物理会话独占 stdio ACP process/home，官方 session-prompt 保持 system 与工作资料分层，首轮 Context 持久化，恢复先核对真实 ID/cwd。runtime 不改变 queue、调度或 I13 配方。固定源码版本、输入消费证据与退出边界见 Braid 的 `docs/20-product-tdd/app-server.md`；本次实施回执见 [implementation](implementation.md)。

发现并按现有契约处理三处原生缺口：load 会收养未知 ID；固定版 cancel 经 router quit no-op；steer 可另开没有对应 prompt terminal 的后台轮次。Braid 分别先核身份、核实 owned 进程停止并保留 Unknown、返回 Deferred 留给既有 queue。创建已得到 ID 后落盘失败仍保留 Materialization 身份；metadata 中 ID 必须唯一，不能只挑选恰好 cwd 相符的一条。

反馈已完成：任务独立 Cargo target 编译、真实 Braid/Bub help、真实 Bub hooks、无模型 stdio initialize/new、退出后 load 同一实际 ID，以及实际 native system hook 读取。原始证据在 `runs/braid-provider-expansion/bub-20261001/`。模型 prompt、工具执行、活动取消、native 消费证据及实际 usage 尚未端到端验证，prepare/握手不能替代这些证明。Alma 仍暂缓，未 push。
