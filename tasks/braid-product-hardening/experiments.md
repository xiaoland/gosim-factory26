# e20260928-01：新 Flash Team 的 WSL Hackathon
授权：用户要求最新 variant 在 WSL 运行 Hackathon 两题，官方 API；随后指定 agent-profile 模型替换并作为新 variant。
variant 为 pi-braid-flash-team。根为 pi-glm-fast；替代原 pi-deepseek-fast 的两个 profile 为 pi-qwen-fast/qwen3.6-flash、pi-minimax/minimax-m3。
原生 sub-agent 模型未替换，不属于纯粹完全去除 DeepSeek 的模型对照；工作流和技能沿用 pi-braid。
GitHub、Sheet 各一次独立生成，workers=2。不勾选参赛、不使用 official_evaluation、不启动额外官网 run。
WSL 目录 /home/yyh/Development/factory26/runs/e20260928-01-flash-team。
官方 API /v1/models 已确认两个精确 ID；各一次两轮工具调用均正常返回，WSL 中相同 Pi 0.85.1 和 profile models.json 各完成真实 read 工具与结果续接，exit 0，无 error stop。MiniMax 将思考保留在文本 think 标签，未擅改原生 SDK；原始 session 在 WSL qualification/<profile>/。
复用 runtime 的 npm lock SHA256 与当前 harness/npm/package-lock.json 相同：960494ef698fcdeb5453296ef8de23b67cdce5f63ad9deff1d8fe0b186907992。
模型说明来源：[Qwen](https://www.alibabacloud.com/help/en/model-studio/qwen3-6-flash)、[MiniMax](https://platform.minimax.io/docs/api-reference/text-openai-api)。
模型上限与协议描述来自供应商，官方 ARC alias 的实际接线由原生调用确认；不以供应商文档等同赛事网关全部能力。
Braid 二进制待本轮修复/精简合并编译后冻结；运行身份和产物哈希随后补记。
生成与评分分离：先生成并冻结应用，再用现有本地公开需求代理测试评分；该分数不是官方隐藏测试得分。

## 用户暂缓
两题尚未启动。2026-09-28 用户要求等待产品审查并一并修复后再运行，故停止未完成打包；原生模型资格记录继续保留，但后续运行需重新冻结源码、二进制和包。Linux 暂存二进制 SHA256 83ea5057f346316fe98f5f4f2c917a00eeec05cf928d914a771f61bf859216dd；不标为最终实验输入。

## 2026-09-28 恢复启动授权
用户：“没跑的话请本地启动，开始跑。”已核实 WSL 无 generation/execution 状态或运行进程，沿用 e20260928-01；实际模型为已核实的 qwen3.6-flash/minimax-m3。使用本轮最新 Braid、方法及遥测，唯一键重复调度仍为待核实风险，保留真实证据，不因其未闭环虚报修复。两题并行，生成后自动执行公开需求代理评分。

## 启动记录
已在 WSL 启动控制器 PID 122373，execution.json=generating。两条 lab run 均已进入 running：
- GitHub：pi-braid-flash-team--hackathon--github-8585fe9975271a
- Sheet：pi-braid-flash-team--hackathon--sheet-d7d79571498155
冻结 ZIP SHA256 ca994e13be524e8a2ffc6cda03c1c26d6c88e44a5df97cb11b887b91b2b5f5af；Braid binary f544b87ec165607f928835fe369dd8297191bd9e69100f10a129dee192f2ec01。最新代码/技能经本机打包后复制 WSL，避免 WSL 大量小文件复制缓慢。包内 source provenance 已同步最新二进制和源码归档。
启动阶段 running 是控制器状态，实际模型调用待原生证据确认。监控交给 flash_team_monitor（gpt-5.6-luna / low），程序按180/480秒间隔，终态与明确故障回报。

# e20260928-02：原 DeepSeek 配方，供应商直连
用户授权同时在 WSL 跑原 DeepSeek variant 两题，并补充 GLM 使用 models.env 的 BigModel key。variant 为 pi-braid，与 e20260928-01 使用相同本轮 Braid/技能/遥测，模型配方保持 GLM 根 + DeepSeek 工作项成员。DeepSeek 文本/视觉及原生子角色均路由 api.deepseek.com；GLM 路由 open.bigmodel.cn；Kimi 保持 ARC 自带 key，不使用参赛额度。
原模型别名 deepseek-v4-flash 和 deepseek-v4-flash-vision-exp 在官方端点实际返回 deepseek-flash，均已取得 HTTP 200；这不是与 ARC 端点完全等同的纯配方对照。通过既有 LiteLLM 网关按模型路由，preserve-parameters，不添加新网关实现。
WSL 目录 /home/yyh/Development/factory26/runs/e20260928-02-deepseek-direct，两个生成 worker，随后自动冻结并本地代理评分。网关端口4018；凭据仅存私有 env，不进入 ZIP。
冻结 ZIP SHA256 ab43e59a7db44c71df13493522f0a06022bffeca057dff75bbeaed5d0b69a2e7。

## 运行时打包故障与 g02 接续
初次包复用了本机旧runtime，缺 pi-background-bash/pi-lane/pi-pending，GitHub 在原生模型启动前报 FileNotFoundError。01的Sheet与02初次尝试已通过lab stop停止；原输入和日志保留，不计评分。已从此前WSL核实的runtime取得这三个依赖及其lock，重新打包，确认包内CLI和扩展入口存在。两实验改在各自 attempt-02 下运行，不覆盖旧冻结输入。
e20260928-01 g02 ZIP SHA256 e5cf18da28ec04ba1611e5d0b26a371154a5a46d9cfb042e139d155720df93e6；本地文件 runs/e20260928-01-flash-team/agent-g02.zip。
e20260928-02 g02 ZIP SHA256 b377e0f2ae2739e55d1198e2b4b004e489d22cf4d6d1bcddaddbf60168ab8e4a；本地文件 runs/e20260928-02-deepseek-direct-agent-g01.zip。
02 g02 controller PID124546；DeepSeek/GLM供应商路由保持用户要求，网关4018已就绪。
