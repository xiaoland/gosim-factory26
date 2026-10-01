# GitHub 官网低分诊断

目标：解释来源 run `435b79927a47` 生成的 GitHub 应用为何在恢复重评 `595ab74c90a9` 得到 4/100（47 项功能仅 1 项），区分应用行为、验收口径、部署与初始化问题。只读原始材料；仅在独立临时目录复现，不修改生成应用或 Harness，不重新评分或生成，不提交。

证据源：`runs/e20260928-completed-replay/github/source-workspace.zip`、`official/workspace-after-generation.zip`、`official/tasks/hackathon--github/status.json`；交付 `main=5f64f3ccd1ddc5cf0060dbbe21c87f7c102641c1`。官方不提供逐例失败。

工作分解：[证据索引](evidence.md)记录可复查的位置和观测；[生成流程归因](process.md)记录冻结指令、原生时间线和可改进的流程；[环境成本](environment-cost.md)细分 GitHub 生成侧的检查与排障；[共享契约成本](shared-contract-cost.md)单独分析 Sheet 续跑 #5/#6 的约 28 分钟契约重对齐，避免误归于 GitHub；[发现](findings.md)记录候选解释及反证；[结果](results.md)记录因果判断、未知项和下一步检验。调查和任务包编写已获授权；源码改动与新官网运行不在范围内。

状态：调查完成。已有两条独立的需求违约行为复现，并追到生成侧自检判据、判据改写的原生轨迹、冻结技能与指令；官网逐例缺失限制精确归因。下一轮是否修改应用或 Harness、是否重新生成或评分，均未授权。
