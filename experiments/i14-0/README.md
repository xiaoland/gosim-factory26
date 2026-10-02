# I14 显式配方入口

`launch.py DIRECTORY --build-only` 消费该目录的 config.json 和新 schema 的 recipe.json，冻结选择回执并构建 experiment；去掉 build-only 才派发。它不创建第二套 operation/dispatcher，不按 variant 数量推导运行授权。

config.targets 逐项声明 job_id、variant、case，job_id 必须唯一且与 recipe 的 generate/prepare 主任务集合相同。评价任务在 recipe 中独立声明，引用该题的生成输出及明确费用模式；某题应用可用后立即派发其评分，不等待其它题。供应商、实际模型 ID、endpoint、凭据变量和目标集全部由配方显式冻结。只有 config.root_selection 明确选用 i13-final-two-task-margin 时，才消费历史两题最终分差政策；默认按明确配方，不自动选择模型。

当前讨论范围为四个 I14 variant 的 GitHub，Sheet 历史只读保留；本目录不自行恢复 Sheet。模型可按 native provider/model 分流，不固定 ARC 或某一 Qwen 标签。私有 deployment.json 引用 JSON credential_file 与必要 cookie_file。普通 Qwen、Token Plan、Kimi 可各有独立凭据变量；实际供应商是否支持冻结模型由实验负责人确认，设施不回落到其它渠道。

运行方法及 authority_handoff、资源预算和独立 runner 合同归[Lab](../../lab/README.md)。旧 I14 SIGSTOP dispatcher、活动 Flash/GitHub、GLM 保全和旧 owner reservation 均保留原身份；旧源码保全见实验设施 packet。新 Docker 资源域接管和新模型执行仍须对应实验范围授权，本次源码切换未运行 I14。
