# 本地运行

在仓库根目录使用 Lab 启动已配置的 variant、target 和 task。配置位置与完整参数见 [Lab](../../lab/README.md)，ARC Runner 接线见 [ARC 适配](../../lab/arc_bench/README.md)。

```sh
python3 -m lab start VARIANT TARGET TASK
python3 -m lab status RUN --json
python3 -m lab logs RUN --follow
python3 -m lab wait RUN --json
```

`start` 冻结程序和输入，派发后由 run 自己的观察程序保存状态；关闭查询命令或 Console 不会停止执行。启动受理不证明依赖安装、Harness 生成和应用部署都已完成，失败应从当前 run 的日志和原始回执定位。

target 决定执行宿主、Docker endpoint、镜像、runtime 和远端目录。Mac 的控制记录、回收数据和构建产物放在 WorkSSD；远端执行数据存于 target 声明的宿主磁盘。容器地址和遥测端点须按实际网络核对。

生成正常完成后，默认自动化按 task 的 `evaluations` 配置冻结应用并创建独立评测 run。支持 `simulate`、`task`、`self-test` 和 `official`，未配置的评测不会自动运行。官方评分必须明确费用模式；本地部署成功或公开需求验收不等于官方成绩。评测实现、身份和保存范围由 [ARC 适配](../../lab/arc_bench/README.md)维护，隐藏评分反馈不进入仍在生成的 Agent。

多阶段任务与 Python 自动化沿用 Lab 公共 API。接续前阅读[恢复说明](recovery.md)：`restart` 默认从基线重跑，`--keep-data` 才保留应用和可迁移的原生状态。
