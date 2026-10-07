# I14 显式 intent 接入

本目录说明 I14 的公共 intent 接入合同。实验使用 `factory26.exp.intent` schema 2，目标、模型和评价政策由 intent 显式声明；具体冻结输入、矩阵、宿主和授权从 [I14 工作入口](../../tasks/iteration14/packet.md)的当前工作单元取得。沿该工作单元的执行记录与 compile 回执读取实际 intent/recipe 路径；当前冻结输入保存在运行材料中，不从本说明目录猜 intent 文件名。本页不复制运行状态，也不提供逐实验策略 launcher。

`targets` 逐项声明 id、variant、case 和 model，不固定八项矩阵。`models` 冻结实际模型、provider、endpoint 与可选凭据变量映射。只有明确选择 `final-score-margin` 政策才读取绑定 run ID 的历史最终分数；不默认选择模型或供应商。逐应用评价声明独立模板、`from_generation` 与费用模式，产物可用后按依赖派发。

这里的 intent 属于旧 [lab.exp](../../lab/exp/README.md) 执行合同；读取或接续已有执行时使用该执行冻结的 controller/runner runtime 与 source，不把这些字段交给当前 run 级 Lab。环境 profile、私有 deployment、authority-handoff 和资源预算按原合同解释。当前 run 的新操作从 [Lab](../../lab/README.md)进入；本页不声明旧 intent 已适配新入口，也不授予模型或评分许可。

旧 launch.py 原件保留在 `runs/experiment-dx-review/compiler-20261002/retired-i14-launch.py`，随该次证据取得；旧 config/recipe 只读保存，不隐式转换或恢复。旧 dispatcher、预约和保存现场保留原身份，退役和接管按当前执行合同核实。
