# ARC 本地实验

本页是当前本地实验入口。当前实验使用 `factory26.exp.experiment` schema 2；旧 ARC schema、Runner 参数和完整历史取证合同移至[历史本地实验合同](history/local-experiments.md)。

## 当前流程

复杂矩阵先编译显式 intent，再只读检查、构建冻结执行器，最后在已有授权下启动：

```sh
python3 -m lab compile /absolute/intent.json \
  --environment /absolute/environment.json \
  --directory /absolute/bundle
python3 -m lab doctor /absolute/bundle/recipe.json \
  --environment /absolute/environment.json --json
python3 -m lab build /absolute/bundle/recipe.json \
  --environment /absolute/environment.json \
  --directory /absolute/experiment
python3 -m lab start /absolute/experiment \
  --deployment /absolute/private-deployment.json
python3 -m lab status /absolute/experiment --json
```

`compile` 冻结目标、模型选择、预算和评价关系，不安装、不请求平台、不启动模型；`doctor` 只读检查声明材料、runtime、Docker/Runner 和凭据覆盖；`build` 发布冻结执行器；`start` 才产生实际执行。`status`/`monitor` 查询保存的投影和原始观察，不以 completed 推断评分或归档完整。

ARC matrix 可直接生产 recipe，但仍须显式声明 controller/runner runtime、backend、预算、模型、评价政策和存储；不从名字展开目标，不从 ambient environment 补全费用或 endpoint。已冻结应用的独立评价使用显式 `from_job/output` 关系，生成和评价的输入、费用和耗时分别保存。

## 执行位置与证据

官方 ARC 本地 Runner 可以使用显式 Docker endpoint 或远端 Linux 环境；本地控制进程所在的 Mac 不推断 runner、daemon、容量或授权可用。WSL/sfp7 等宿主必须由 recipe 和启动前读回确认。Hosted 生成属于另一种 backend，使用平台身份和 journal，不与本地 Runner 混用。

每个 attempt 的 runner、资源、原始输出、telemetry、named output 和 archive 分别保存。Docker 资源必须按冻结 endpoint、daemon、image、labels 和 attempt 身份核对；远端复制或回收失败保持具体错误和 `unconfirmed`，不能据本机进程退出声称远端已清理。生成应用发布后，独立评价 job 才能消费已验证制品。

当前源码导航与字段解释见 [Lab](../../lab/README.md)；实验范围、授权、输入和停止条件见所属 packet。模型事实使用 `python3 -m lab status EXPERIMENT --json`，Braid/OTLP 过程使用 [Braid 诊断](braid-diagnostics.md)，不在本页复制过程分析细节。

## 历史入口

旧运行的 schema、`host-lab`/旧 `lab run`、ARC-Bench workspace、raw Pi/Codex 基线和浏览器验收合同保留在[历史本地实验合同](history/local-experiments.md)，只用于解释已有原件，不能创建当前实验。
