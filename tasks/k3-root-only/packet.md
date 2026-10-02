# K3 仅作为根 Issue Agent

用户授权：先让已冻结的 `pi-team-k3-root` 官网 run 完成；同时制作正确的 K3 根 Issue variant，前者完成后紧接着运行新 variant，并在新运行中实际核验 Context7、Exa。

上一轮 [任务包](../k3-root-experiment/packet.md) 和 [工作区快照](../../runs/k3-root-experiment/20260926/official/tasks/hackathon--github/template-bundle-live.zip)表明，根 K3 指派了 K3 子 Issue，子 Issue 又指派 K3 PR；因此该轮不是根模型限定实验。新 variant 从上一轮冻结源码复制，只改以下边界：K3 Profile 带通用 `root-only` tag，Braid 用它启动根 Issue，但指派目录和后续 Issue/PR 指派均拒绝此 profile；根会话负责分派、集成与最终验收，具体应用代码交给 DeepSeek/GLM 成员。后续分工仍由 Agent 判断。

Context7 与 Exa 在官网生成容器中、Agent 启动前，各通过随包 `mcporter` 和同一 `MCPORTER_CONFIG` 做一次真实查询。原始 stdout、stderr、退出码和耗时写在 `.factory26/<run>/external-tools.json`；失败不掩盖生成结果。验收要求看到有内容的真实工具返回，不能仅凭安装或 `tools/list` 判可用。查询只用于验证能力，不进入 Agent 上下文。

实施顺序：限定 Braid 指派入口 → 新 variant 的 profile、根指引与工具查询 → Linux runtime 和 ZIP 冻结 → 核对包身份及两份输入差异 → 等上一轮官方 run 完成评分和证据采集 → 用新状态目录、`official_evaluation`、同一 Hackathon GitHub 任务启动官网 run。旧 run 和旧 ZIP 均不修改、不重复提交。新 run 生成、部署及完整评分后，报告分数、模型实际分配、K3 是否只在根 Issue、两项工具查询的真实结果、凭据字段及可比性限制，再暂停由用户决定下一轮；不自行启动 Sheet。

原准备状态（已被下方停用决定取代）：新 ZIP 已冻结，SHA256 `6a3af296cd9f6affb52a7e2bf319e2fd5a58f17bec5fa0278bba864455909afe`。相较上一轮冻结 stage，文件列表相同，仅 K3 profile、K3 指引、`run.py`、Braid 二进制及其来源记录变化。新官网状态已 `prepare`，凭据模式 `official_evaluation`；尚未上传或启动新 run。`runs/k3-root-only/20260926/launch-after-previous.py` 已以 PID 28209 脱离终端运行，只读等待上一轮 run `7b533d7bd71b` 完整评分并释放控制器锁，再使用新状态目录执行 `run-all --interval 900`。旧 run 仍在运行。

比较限制：Braid 二进制由 9 月 26 日的当前工作树重编，其来源 SHA256 已记录在包内 `runtime/runtime-source.json`；工作树同时含先前未提交的 Braid 改动，所以实验差异不能全归因于 `root-only` 指派约束。两轮共同使用的其余冻结 runtime、skills 与模型配置一致。

## 2026-09-26 额度停用

用户撤销后续实验使用参赛额度的授权。接续 run `48a591836974` 已由用户取消，本地 launcher/controller 已终止，无接续进程。此 packet 前述自动运行安排失效；旧 ZIP 不再启动。新预算限制与后续待复核方案见 [预算与交付任务](../competition-budget/packet.md)。
