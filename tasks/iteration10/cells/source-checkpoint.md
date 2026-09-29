# 迭代10源码检查点与实验准备

2026-09-29主线完成审查结论消费及对应修正，用户自由提交授权有效；用户随后明确“开始实验”，2026-09-29已启动新包构建。

| 仓库 | 检查点 | 覆盖与限制 |
| --- | --- | --- |
| Factory | `a243cbd`（含`8d931d2`） | 累积variant更名、独立实现、原生补丁、工具及lab接线；包含此前多轮已授权源码工作，不是本轮新写15000行，也不代表制品已构建 |
| Braid | `1fabd11` | 累积协作/恢复修正、根提醒轮换、失败事实查询、无效status_surfaces清理、已批准测试删除；提交后工作区干净 |
| SVC | `0cf1406` | 七个独立技能、V&V与规划/文档/packet方法；历史CLI、测试删除及发布配置改动仍未纳入，当前技能打包不消费它们 |

Factory仍有旧task packet、报告、模拟评分文件和临时材料未提交；不为使git status为空将它们混入源码检查点。
原生补丁是diff文件，git whitespace检查会报告其上下文前缀/原缩进；没有为了清警告修改补丁内容。

## 已核对的实验入口

`variants/pi-braid/build.py`明确装入七个SVC技能及既有工具技能；`run.py`给主成员装载技能并注入共享运行条件。
`scripts/package_agent.py`默认从当前源码构建Linux runtime；本次应走此默认新构建路径，不传旧 `--runtime`。
`submission/Dockerfile`包含Pi、pi-subagents生命周期、pi-subagents自动验收关闭、background-bash四份补丁；新包必须保留实际来源与哈希，不能用本文件的提交号替代制品记录。

生成矩阵使用 `lab.arc_bench.arc_matrix --requirements-only`，选择 `hackathon/github` 与 `hackathon/sheet`，workers=2。
此模式不放入外部tests输入，WSL只生成及执行Agent自身开发验收；`experiments/hackathon-local/matrix.py`是历史本地评分入口，本次不用。
按 experiments.md 的配方为每题明确4GiB/2CPU；当前未创建新manifest或冻结ZIP。
每题完成后独立生成应用重放包，官网self_funded评分，不等待另一题，不消耗参赛额度。

## 仍需在恢复实验时确认的事实

- 现有WSL镜像、runner与网关状态，实际输入需求目录和目标新目录是否可用；本次没有远端探测或改动。
- BigModel/DeepSeek/Kimi实际请求路由、余额及响应模型。源码GLM为glm-5.3-flash、DeepSeek为deepseek-v4-flash、advisor为kimi-k3；不静默替换旧别名，不以历史目录可见代表当前请求可用。
- 新失败事实的真实失败→查询→恢复链、原生取消及迟到结果消费、技能采用与最终效果尚未经新版运行验证。
- 正式平台Node入口存在且版本符合要求时才形成兼容性证据，工具Node通过不代替它。

用户已授权按既定输入启动；本次通过实际构建、生成取证验证上述条件，不推送仓库。
