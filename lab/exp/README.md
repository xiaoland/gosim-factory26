# lab.exp 源码导航

本包保留旧 experiment/job/attempt 执行合同，当前 run 操作从 [Lab](../README.md)进入。下面的源码与协议只用于对应旧执行；接续时使用该执行冻结的 source 和 runtime，不用当前工作树替换其身份。本工作树的命令定义可用 `python3 -m lab.exp --help` 查阅，接口存在不代表旧运行已完成接管。

| 责任 | 实现 | 合同 |
| --- | --- | --- |
| 定义、显式政策与领域 lowering | compiler.py；ARC 的 local_job.py、score_evidence.py | [实验定义](experiments.md) |
| 物理选择、选定生产闭包与只读 readiness | environment.py、readiness.py；scripts/package_agent.py/runtime.py | [构建](experiments.md#选定目标的物理构建与只读检查) |
| 定义组件、交付投影与域装配 | definitions.py、delivery.py、assembly.py；scripts/execution_context.py/execution_bootstrap.py | [制品](artifacts.md)、[执行](execution.md#装配与域控制) |
| 显式请求与一次入口 | __main__.py、controller.py、runner.py、backends.py、hosted.py | [执行](execution.md) |
| 保存事实投影与历史读取 | projection.py、history.py | [查询](execution.md#查询保存事实) |
| 域权威、writer 与恢复事务 | admission.py、state.py；tooling/linux/exp_checkpoint.py | [恢复证据](artifacts.md#检查点与准备) |
| 引用、位置、保留与成员运输 | artifacts.py、terminal.py | [制品](artifacts.md#发布封口与显式运输) |
| 原始遥测及固定证据分析 | telemetry.py、analyze.py | [遥测](artifacts.md#遥测与分析) |

Controller code 与 runner code 分别冻结实际导入闭包。低层函数用于履行已受理操作，不作为绕过公共授权、准入和身份门控的替代 CLI；保存状态与行动建议也不授予执行许可。
