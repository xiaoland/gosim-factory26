# 恢复路径设计

## 产品行为

操作者给出旧 run 的原始 workspace ZIP、旧冻结 Harness ZIP、来源 run 身份，以及可选的已修复 Braid 二进制。恢复准备入口先说明哪些状态能保留、哪些 Git 历史无法证明；随后产生一个新的恢复包、明确来源清单和独立的官网 journal。新包沿用旧 Harness 其余文件、模型配置和需求；入口解开原工作区并运行 Braid `local`，从原 Issue/PR 状态继续。只有根 Issue 真正完成、Braid quiescent 且交付版本可导出时才进入评分。

官网身份始终分开：`source_run` 是原失败运行，`recovery_run` 是新自费运行；两者的费用、状态和评分不混写。重新执行准备命令若输入与已冻结包相同，直接返回已有身份；输入变化则要求新的恢复代次，不覆盖原包或 journal。上传响应不确定时，优先核对 journal pending、包哈希和远端 submission，再决定是否继续。

## 最小技术方案

维护一个恢复打包入口和一个包内恢复入口，代替 g03→g05 的手工复制与改写。打包入口复用现有 package manifest、`competition prepare/run-all` 和 `hosted_monitor.collect`；只替换恢复入口、来源 ZIP、可选 Braid 二进制，并记录这些文件及原包的哈希。包内入口复用现有 `agent_support` 与 `braid_runtime` 的校验、交付和进程清理；以来源工作区中的 Braid request、SQLite 与 bare origin 为权威，不重建根 Issue、不重新取需求、不重置已完成的子项。

恢复入口负责 ZIP 路径校验、执行位、工作树 Git 元数据重建及来源限制记录。对于需要改 Braid 状态机的故障，修正 Braid 后替换二进制；不要把针对某个 run ID 的 SQLite 更新或特殊事件逻辑做成通用恢复参数。g03 的 `context_pressure=NULL` 属于这种应清退的一次性状态手术；g04 的关闭子项候选错误应留在 Braid 查询中修复。

先不增加平台 API 逆向层、恢复调度服务或新数据库。官网目前仍需新 submission 上传完整包；这个设计减少人为操作与失败后重做的代价，不能消除平台上传时间。

## 验收与实施顺序

1. 用现有 Sheet/GitHub 终态 ZIP 只读核实恢复输入契约：来源、Braid request、manifest、bare origin、工作树与原生会话材料；明确哪些历史不可恢复。
2. 实施前沿现有运行记录走查包构成、manifest 字段和入口调用，排除已知接口/状态误解；不新增包 smoke、探针或基础设施测试。
3. 开工复核后实施打包和包内入口。用一个已保存工作区的新**自费**官网 run 验证：同一根 Issue、已有子项和 Git 成果保留；旧原生会话不被误当活动进程；新根 Pi 会话有模型回复和工具结果；最终生成与评分分开记录。只有实际发生的范围才能在报告中称为通过。
4. 形成一页操作说明，指向来源 ZIP、冻结包、恢复包、journal、终态工作区和原始错误；原始证据仍保留在各 run 目录，不复制进文档。

g05 后续已取消；两条 completed-workspace 重评验证了已完成恢复路径。未完成接续的 Braid 冷恢复边界仍待修复与真实运行验收，新入口不回填 g05 的运行身份。
