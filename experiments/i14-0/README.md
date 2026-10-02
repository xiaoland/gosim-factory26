# I14 显式实验入口

新定义使用公共 `factory26.exp.intent` schema 2，由 `python3 -m lab compile INTENT --directory COMPILED` 生成严格 recipe；随后执行 `lab doctor COMPILED/recipe.json --deployment PRIVATE_JSON`、`lab build COMPILED/recipe.json --directory EXPERIMENT`，最后在该实验实际授权内 `lab start EXPERIMENT --deployment PRIVATE_JSON`。字段及操作合同归 [Lab](../../lab/README.md)。本目录不再提供逐实验策略 launcher，旧 launch.py 原件保全于 `runs/experiment-dx-review/compiler-20261002/retired-i14-launch.py`；旧 config/recipe 只读保存，不隐式转换或恢复。

Intent.targets 逐项声明 id、variant、case、model，不固定八项矩阵。models 显式冻结实际模型、provider、endpoint 和可选凭据变量映射。只有明确选择 final-score-margin 政策才读取绑定 run ID 的历史最终分数；不默认选择模型或供应商。逐应用评价声明独立模板、from_generation 与明确费用模式，每题产物可用后按依赖派发。Compile/build 记录已有授权，不新增模型或评分许可。

当前讨论范围为四个 I14 variant 的 GitHub，Sheet 历史只读保留；本目录不自行恢复 Sheet。私有 deployment.json 引用 JSON credential_file 与必要 cookie_file。普通 Qwen、Token Plan、Kimi 可各有独立凭据变量，实际供应商是否支持冻结模型由实验负责人确认，设施不回落到其它渠道。

Controller/runner runtime 的生产依赖、authority_handoff 和资源预算继续显式冻结，维护的 environment 可解析并复用物理资产。旧 I14 SIGSTOP dispatcher、活动 Flash/GitHub、GLM 保全和旧 owner reservation 保留原身份；新 Docker 资源域接管及模型执行仍须对应实验范围授权。本次 compiler/readiness 交付没有运行 I14。
