# ARC 平台与制品

ARC 生成、冻结应用评测和平台状态采集由 [Lab ARC 适配](../../lab/arc_bench/README.md)提供。Hackathon Evolution 已于 2026-10-08 结束，赛事提交和运行流程只作历史解释，规则与输入见[赛事归档](hackathon-evolution.md)。

## 参赛包与平台边界

Harness 包固定 variant、源码、运行依赖和模型输入，由根目录 `main.py` 接收平台需求。构建入口及 Linux 资源要求见[打包工具](../../tooling/scripts/README.md)，variant 专属能力由各 variant 的 README 和 builder 声明。通用脚手架可以预置，具体题目的答案不能预制。

生成、独立应用重放和官方评分是不同过程。应用重放消费已冻结的应用，不调用模型重新生成；它不能冒充正式参赛生成，评分耗时也不能当作原生成耗时。阶段评分必须绑定明确 Git commit，隐藏反馈不能注入仍在生成的 Agent。

## 平台操作

Lab run 保存 upload、create、start、观察和下载的原始回执。写请求结果不确定时先按已有 submission/run 身份只读核对，不能盲目重发。平台错误保留 HTTP 状态和具体响应；上传或启动成功不代表已经评分。

Hosted 不支持 pause/resume。停止、保存和新 run 的接续沿[恢复入口](recovery.md)与实际执行器能力进行。官网下载的 workspace、原生归档和官方成绩各有保存范围，辅助证据缺失不自动等同应用失败。

## 赛事规则与提交模式

历史须知见[初赛规则 PDF](../references/competition-notice-20261001.pdf)和[决赛通知](../references/hackathon-evolution-notice-20261006.md)。`self_funded` 独立评分不计排行榜，正式提交的资格、额度和最终采用顺序由当届规则与平台回执确定，不能由 `catalog`、模型地址或单次状态字段反推。

赛事已结束，旧 packet 中的提交、重试和监控安排不能作为当前执行授权。历史平台细节和当时的具体处置可从 Git 历史查阅。
