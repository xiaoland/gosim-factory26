# ARC 本地实验

本页维护 ARC run 的本地操作入口。重构实施与实际验收状态见[决赛设施 packet](../../tasks/finals-experiment-loop/packet.md)；旧 experiment schema 和 Runner 取证合同只用于对应冻结执行，见[历史本地实验合同](history/local-experiments.md)。

## 当前流程

配置好 target 和 task 后，在已有模型授权范围内用三个参数启动，复杂顺序使用普通 Python：

```sh
python3 -m lab start pi-minimal-vv-dx-test wsl TASK
python3 -m lab status RUN --json
python3 -m lab wait RUN --json
python3 -m lab restart RUN --task NEXT_TASK
```

新路径没有 compile/doctor/build 前置步骤、稳定 request-id 手工输入或容量预约。start 自动组装 program、输入需求、gateway/collector 与实际 target，保存采用的代码和配置。运行自己的 observer 保存 status；查询不会另起现场采集。CLI/Console 关闭不影响执行。

应用正常完成后，默认 Python 程序冻结应用并启动 task 配置的 evaluations；三个评测入口分别是公开需求 simulate、题目自带 task 和官网冻结应用 official。它们各有独立 run、工作区、来源、费用和结果。未配置的 simulate/official 不自动执行，官网模式必须显式 self_funded 或 competition。隐藏反馈不注入下一阶段。

## 执行位置与证据

WSL/sfp7 的执行位置、Docker、镜像、runtime、运行根目录及共享观测地址由 target 配置提供，不从 Mac 的路径或 loopback 猜测远端。Mac 控制和回收全部在 WorkSSD，远端数据允许保存在实际宿主磁盘。Hosted 使用平台身份及自包含包，不与本地容器句柄混用。

每个 run 保存整个 data/workspace 与 data/harness、日志、资源、遥测、费用和平台结果。stop 操作实际容器或平台 run，不据 Mac 控制进程退出宣称远端已停止；回收失败保留原错及远端唯一副本。pause/resume 使用 Docker pause/unpause，保留同一次执行；不保证释放内存或保住所有外部网络连接。

restart 确认来源停止并保存完整 data 后重新组装同 variant 程序。同 task/需求版本恢复原生会话，下一 task 新建原生任务状态，历史 data 与应用保留；旧 records、费用和隐藏报告不迁移。当前源码与参数见 [Lab](../../lab/README.md)，范围和允许损失见所属 packet。

## 历史入口

旧运行的 schema、`host-lab`/旧 `lab run`、ARC-Bench workspace、raw Pi/Codex 基线和浏览器验收合同保留在[历史本地实验合同](history/local-experiments.md)，只用于解释已有原件，不能创建当前实验。
