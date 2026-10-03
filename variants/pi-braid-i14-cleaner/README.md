# I14 Cleaner 变体导航

Cleaner 是 I14 的独立实现，在共同基线的原生 Braid 成员边界内增加受控的清理/材料操作扩展。普通生成入口仍是 [`main.py`](main.py) → [`run.py`](run.py)；材料需求由 [`materials.json`](materials.json) 声明，build 只传递显式参数。

## 改什么看哪里

- 清理动作、快照和 apply 边界：[`extensions/factory-cleaner.ts`](extensions/factory-cleaner.ts)；其提示和共享约束：[`extensions/factory-cleaner.md`](extensions/factory-cleaner.md)。
- 清理扩展如何进入每个角色：[`run.py:native_files()`](run.py)。它会为能力目录写入 cleaner 扩展、说明和 `factory-cleaner.json`；不要只修改扩展源码而假定运行包已更新。
- 供应商或网关材料：[`build.py`](build.py) 的 `--provider-env`、`--gateway-routes` ；公共 producer 将它们保存为独立输入，具体运行是否消费以 run 接线为准。
- 反馈：看本次 output 目录的清理快照、Braid 回执和交付记录；清理扩展不替代 Lab 的 experiment 状态或控制入口。

Cleaner 的扩展只在其自身原生成员/运行材料中生效；它不替代 Braid 成员分派，也不自动改变其它 I14 实现的角色。不要把它推断为 Reviewer 或 E2E 的能力。源码核对：[`run.py`](run.py)、[`build.py`](build.py)、[`factory-cleaner.ts`](extensions/factory-cleaner.ts)。

入口要求设施已装配的 context；源码操作见[公共源码入口](../../scripts/README.md#i14-源码装配)。技能与额外角色需求由 [materials.json](materials.json) 声明，controller/SDK/Hosted 交付与实际服务不由本 variant 另行实现。
