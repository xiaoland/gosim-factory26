# 第十次迭代：标准协作与检查工具后的全新 Hackathon（用户暂停启动）

当前状态与启动授权统一以[主packet](packet.md)为准：实验暂停，统一新包未构建，两题未启动。
本页只保存恢复实验时的配方、操作安排与观察目标，不保留已经被暂停覆盖的旧启动指令。
旧Sheet自费评分58/100属于上一轮，不能归因于迭代10修改。

- variant：pi-braid；GitHub、Sheet各一次全新生成，不承接旧应用、Git或Braid状态。
- 模型/凭据：沿用e20260928-02既有配方与网关，GLM BigModel、DeepSeek官方自带key，Kimi用于原生advisor；不使用参赛额度，不增加昂贵Braid会话预算。
- 并行与资源：两题并行，每题4GiB/2CPU，复用已安装官方本地runner与现有镜像。
- 新包：实验恢复后按最终修复取舍构建完整runtime、variant与skills，冻结实际材料和模型路由。当前没有统一制品，不使用旧预热runtime或历史补丁包冒充新版。来源见[修复导航](closure.md)。
- 启动前：取得恢复实验的明确决定，消费最终修复取舍、完成必要局部修正，再统一构建冻结；本页不单独授予启动权限。
- 旧Sheet恢复只替换获批Braid局部补丁，应用树保持不变；不把其评分归到迭代10完整新版本。
- WSL只生成、运行应用开发自检及部署核对，不执行本地benchmark评分，也不从模拟测试推算官方成绩。每题生成完成后立即冻结应用重放包，上传官网以self_funded评分，不等待另一题；生成、官方评分、工具采用和耗时收益分开记录。

WSL新目录预定 `/home/yyh/Development/factory26/runs/e20260928-03-check-receipts`。
旧Sheet官网状态归原 `runs/e20260928-02-deepseek-direct/attempt-09/continuation-03/sheet-official`，新旧journal不混用。
有外部评分异常时保留原始错误并处理可恢复故障；不可解决的凭据或外部条件问题才交回用户。

构建材料使用独立目录 `build-source/`，不覆盖 WSL 主 checkout；网关显式引用 WSL 原 `.secrets/models.env`，凭据不复制进构建或制品。操作回执见 [构建记录](build.md)。

## 运行时观察与可比性

前十分钟每三分钟、之后每八分钟由脚本采集，并保留各题独立终态。
关注根基础PR是否真正承接实施、子项是否保留原始场景和前提、当前判据能否区分已知的简化错误，以及当前候选的检查结果是否在合并前被消费。
另外观察原生acceptance/review-required是否把只读结果误标成实施未完成，或诱发父追加不存在reviewer的无意义工作；该字段已确认不阻断返回，不预先加新机制。
原生角色按机会→发现/尝试→实际模型与工具→返回→父决定记录；没有机会不强迫调用，未触发不写成已验。
对provider错误保留原生stopReason/errorMessage、连续failed turn、错误首末时间、最近成功及本次恢复边界；文件活动或running不是模型调用成功。
针对重复Context、关闭联系、PBB完成、旧子任务交接和Collector重试，分别观察对应原始消息/收据，不用token下降代替正确性。

2026-09-28 只读模型目录：Kimi含kimi-k3，BigModel含glm-5.3-flash；DeepSeek目录列deepseek-flash（服务声明V4.1-Flash，支持text/image）而未列旧v4-flash别名。旧网关成功运行时仍使用旧别名，目录缺名不直接证明请求不支持；新实际请求保留请求名/路由/响应模型，不静默换模型。目录结果不证明工具流式往返或余额充足。

生成使用 `lab.arc_bench.arc_matrix --requirements-only`，不使用历史本地评分matrix。该生成入口不提供memory/cpus顶层参数；生成manifest后为每条ARC adapter命令明确追加 --memory 4g --cpus 2，再冻结manifest，避免依赖runner默认2GiB。一次性的实验配方修改不扩大成全局配置功能。
