# Linux 运行资源与恢复入口

本目录承担运行资源的 Linux 装配及容器内恢复材料处理。它不登记实验、不选择 variant，也不直接向官网提交。

| 文件 | 职责 | 调用入口 |
| --- | --- | --- |
| [Dockerfile](Dockerfile) | 从固定 npm lock、补丁及可选 Braid 源构建资源镜像。 | `tooling/scripts/runtime.py linux`。 |
| [build.py](build.py) | 在构建镜像内装配原生工具、Chromium 库/字体、启动器及应用 Node 环境。 | Dockerfile 的构建步骤，不在宿主机直接运行。 |
| [exp_checkpoint.py](exp_checkpoint.py) | 按调用方冻结合同捕获/准备 Harness checkpoint。 | Lab Docker backend；完整性与停止门控见[恢复手册](../../docs/deployment/recovery.md)。 |
| [recover_completed.py](recover_completed.py) | 消费已装配 prepared 或沿旧冻结合同导出完成工作区。 | 新 prepared 由公共 bootstrap 调用；旧来源通过 [package_completed_recovery.py](../scripts/package_completed_recovery.py)，沿来源 run 保留身份。 |

资源构建与 variant 封装是两个步骤，命令统一维护在 [scripts 本地说明](../scripts/README.md#构建独立运行资源与制品)。工具使用包内 Node；应用使用官方 Runner 提供的 Node，`app-env` 明确核对其版本，不用工具 Node 替代应用执行环境。

`build.py` 只收录实际 Linux 二进制、库和锁定材料，构建失败保留具体缺失依赖。更换 lock、补丁、Braid 源或构建输入会产生新的资源身份；工作树变化不更新旧 ZIP。恢复时不能只替换二进制便声称原生历史、Git 与检查点属于同一时点；制品与恢复合同归 [Lab 制品说明](../../lab/exp/artifacts.md)。
