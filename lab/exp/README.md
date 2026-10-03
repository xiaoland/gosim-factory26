# lab.exp

lab.exp 是 Factory26 新实验的编译、就绪检查、执行、恢复和只读状态入口。常用命令集中在 [Lab 入口](../README.md)；本页只说明职责和源码定位。

按读者任务阅读：

- [实验定义与编译](experiments.md)：intent、environment、compile、doctor、build 和定义/运行边界。
- [执行、恢复与状态投影](execution.md)：controller、runner、hosted、start、recover、status 和物理准入。
- [制品、遥测与恢复证据](artifacts.md)：artifact、telemetry、保留、传输、checkpoint 和 prepared。

源码入口：

- __main__.py：CLI 分发
- compiler.py、readiness.py、environment.py：定义编译与只读环境事实
- controller.py、runner.py、backends.py、hosted.py：执行生命周期
- projection.py、admission.py：状态投影与物理准入
- artifacts.py、telemetry.py、analyze.py：发布、封口与分析

本地说明维护可观察合同和职责边界；具体字段与失败行为以源码为准。跨组件约束见 [产品技术说明](../../docs/product-tdd/index.md)，操作门控见 [恢复手册](../../docs/deployment/recovery.md)。
